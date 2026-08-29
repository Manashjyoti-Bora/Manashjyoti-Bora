#!/usr/bin/env python3
"""Collect deployment checks and GitHub commit counts for the blueprint sheet.

The script deliberately uses only the Python standard library.  REPORT_MOCK=1
is an offline mode which uses the measurements verified in SPEC-shared.md.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "assets" / "data" / "report.json"
DARK_PATH = ROOT / "assets" / "testreport-dark.svg"
LIGHT_PATH = ROOT / "assets" / "testreport-light.svg"
OWNER = "Manashjyoti-Bora"
FONT = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"

SITES = (
    ("portfolio", "https://manashbora.vercel.app", 78),
    ("nexusmart", "https://nexusmart-dusky.vercel.app", 80),
    ("devhire-pro-ats", "https://devhire-pro-ats.vercel.app", 74),
)
REPOSITORIES = (
    ("portfolio", 27),
    ("taskflow-enterprise", 17),
    ("devhire-pro-ats", 16),
    ("nexusmart", 13),
    ("Manashjyoti-Bora", 8),
)

PALETTES = {
    "dark": {
        "bg": "#071426", "bg2": "#0a1b30", "gridMinor": "#0d2338",
        "gridMajor": "#13314c", "ink": "#dceafc", "dim": "#5f89ad",
        "accent": "#4cc9f0", "ok": "#52d1a4", "warn": "#ffb703",
        "red": "#ff6b6b", "band": "#0c2136",
    },
    "light": {
        "bg": "#f5f2e9", "bg2": "#efebdf", "gridMinor": "#e0dacb",
        "gridMajor": "#cfc7b4", "ink": "#1b2a3a", "dim": "#7d7565",
        "accent": "#0b6fa4", "ok": "#0f7a5a", "warn": "#a86400",
        "red": "#b3261e", "band": "#e8e3d5",
    },
}


def timestamp() -> str:
    """Return a stable, UTC JSON timestamp with whole-second precision."""
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def ascii_text(value: object) -> str:
    """Keep SVG labels compliant with the shared drawing-sheet character rules."""
    text = str("" if value is None else value)
    return "".join(
        char if 32 <= ord(char) <= 126 or char in "·—" else "?"
        for char in text
    )


def escape_xml(value: object) -> str:
    return (ascii_text(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def measure(text: str, size: float) -> float:
    """Required monospace advance-width estimate."""
    return len(text) * 0.6 * size


def fit(text: object, maximum: float, size: float) -> str:
    """Truncate before a measured label can leave its assigned drawing area."""
    shown = ascii_text(text)
    if measure(shown, size) <= maximum:
        return shown
    suffix = "..."
    allowed = max(0, int(maximum / (0.6 * size)) - len(suffix))
    return shown[:allowed] + suffix if allowed else ""


def svg_text(
    x: float, y: float, text: object, size: float, fill: str, maximum: float,
    anchor: str = "start", weight: Optional[int] = None, preserve: bool = False,
) -> str:
    """Make a clipped, mono-spaced SVG label."""
    weight_attr = (' font-weight="%d"' % weight) if weight else ""
    preserve_attr = ' xml:space="preserve"' if preserve else ""
    return (
        '<text x="%.1f" y="%.1f" fill="%s" font-family="%s" font-size="%g" '
        'text-anchor="%s"%s%s>%s</text>' % (
            x, y, fill, FONT, size, anchor, weight_attr, preserve_attr,
            escape_xml(fit(text, maximum, size)),
        )
    )


def github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "blueprint-testreport",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    return headers


def github_commit_count(repository: str, headers: Dict[str, str]) -> Optional[int]:
    """Get a default-branch count using GitHub's Link pagination header."""
    quoted = urllib.parse.quote(repository, safe="")
    url = (
        "https://api.github.com/repos/%s/%s/commits?per_page=1"
        % (OWNER, quoted)
    )
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(
            request, timeout=20, context=ssl.create_default_context()
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
            link = response.headers.get("Link", "") or ""
        match = re.search(r"[?&]page=(\d+)>;\s*rel=\"last\"", link)
        if match:
            return int(match.group(1))
        if isinstance(payload, list):
            return 1 if payload else 0
    except Exception:
        return None
    return None


def collect_repositories(mock: bool) -> List[Dict[str, object]]:
    """Return exact commit counts or an explicitly identified verified fallback."""
    records = []
    headers = github_headers()
    for name, fallback in REPOSITORIES:
        count = None if mock else github_commit_count(name, headers)
        if count is None:
            records.append({
                "name": name, "commits": fallback, "source": "fallback",
            })
        else:
            records.append({"name": name, "commits": count, "source": "api"})
    return records


def one_request(url: str) -> Tuple[Optional[int], int]:
    """Make one full HTTPS GET and measure elapsed wall time in milliseconds."""
    started = time.perf_counter()
    status = None
    try:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "blueprint-testreport",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(
            request, timeout=20, context=ssl.create_default_context()
        ) as response:
            status = int(response.getcode())
            # Read a bounded amount so this remains an actual completed GET.
            response.read(1)
    except urllib.error.HTTPError as error:
        status = int(error.code)
    except Exception:
        status = None
    elapsed = max(0, int(round((time.perf_counter() - started) * 1000)))
    return status, elapsed


def check_site(label: str, url: str, known_ms: int, mock: bool) -> Dict[str, object]:
    """Run exactly two status-and-latency samples for a deployment."""
    if mock:
        samples = [
            {"status_code": 200, "latency_ms": known_ms},
            {"status_code": 200, "latency_ms": known_ms},
        ]
    else:
        samples = []
        for unused in range(2):
            status, latency = one_request(url)
            samples.append({"status_code": status, "latency_ms": latency})
    latest = samples[-1]
    status = latest["status_code"]
    return {
        "label": label,
        "url": url,
        "samples": samples,
        "status_code": status,
        "latency_ms": int(latest["latency_ms"]),
        "ok": bool(status is not None and 200 <= int(status) <= 399),
    }


def load_history() -> Dict[str, List[Dict[str, object]]]:
    """Read old URL history while treating a missing or invalid record as empty."""
    try:
        with DATA_PATH.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
        raw = record.get("history", {}) if isinstance(record, dict) else {}
        if isinstance(raw, dict):
            cleaned = {}
            for label, entries in raw.items():
                if not isinstance(entries, list):
                    continue
                # A sparkline is an instrument history: only retain samples
                # whose provenance is explicitly a live network measurement.
                cleaned[str(label)] = [
                    entry for entry in entries
                    if isinstance(entry, dict) and entry.get("source") == "real"
                ][-24:]
            return cleaned
    except Exception:
        pass
    return {}


def update_history(
    history: Dict[str, List[Dict[str, object]]],
    checks: List[Dict[str, object]],
    generated_at: str,
) -> Dict[str, List[Dict[str, object]]]:
    """Append one latest measurement per URL and retain the latest 24 only."""
    for check in checks:
        label = str(check["label"])
        samples = check.get("samples", [])
        entries = list(history.get(label, []))
        if isinstance(samples, list):
            for sample in samples:
                if not isinstance(sample, dict):
                    continue
                entries.append({
                    "t": generated_at,
                    "ms": int(sample.get("latency_ms") or 0),
                    "status_code": sample.get("status_code"),
                    "ok": bool(
                        sample.get("status_code") is not None
                        and 200 <= int(sample.get("status_code")) <= 399
                    ),
                    "source": "real",
                })
        history[label] = entries[-24:]
    return history


def latency_colour(latency: int, known: bool, palette: Dict[str, str]) -> str:
    if not known:
        return palette["dim"]
    if latency < 150:
        return palette["ok"]
    if latency <= 400:
        return palette["warn"]
    return palette["red"]


def sparkline(
    entries: object, x: float, y: float, width: float, height: float,
) -> Tuple[str, int, int, int]:
    """Return only real-recorded points, with the required adaptive ceiling."""
    points_data = []
    if isinstance(entries, list):
        for entry in entries[-24:]:
            if isinstance(entry, dict):
                try:
                    points_data.append((
                        max(0, int(entry.get("ms") or 0)),
                        bool(entry.get("ok")),
                    ))
                except (TypeError, ValueError):
                    pass
    if not points_data:
        return "", 0, 0, 0
    values = [value for value, unused in points_data]
    ceiling = max(120, int(max(values) * 1.3))
    span = max(1, len(points_data) - 1)
    points = []
    for index, (value, is_ok) in enumerate(points_data):
        point_x = x + (width * index / span) if len(points_data) > 1 else x + width / 2
        normalized = min(value, ceiling) / float(ceiling) if is_ok else 1.0
        point_y = y + height - (height * normalized)
        points.append("%.1f,%.1f" % (point_x, point_y))
    return " ".join(points), len(points_data), min(values), max(values)


def number_animation(x: float, y: float, latency: int, palette: Dict[str, str]) -> str:
    """Draw a visible, discrete SMIL count-up without relying on textContent."""
    values = [0, int(latency * 0.25), int(latency * 0.55), latency]
    windows = (
        ("1;1;0;0", "0;0.07;0.071;1"),
        ("0;0;1;1;0;0", "0;0.07;0.071;0.12;0.121;1"),
        ("0;0;1;1;0;0", "0;0.12;0.121;0.18;0.181;1"),
        ("0;0;1;1", "0;0.18;0.181;1"),
    )
    output = []
    for value, (opacity_values, key_times) in zip(values, windows):
        output.extend([
            '<text x="%.1f" y="%.1f" fill="%s" font-family="%s" font-size="13" text-anchor="end" font-weight="700" opacity="0">%s' % (
                x, y, palette["ink"], FONT,
                escape_xml(fit("%d ms" % value, 54, 13)),
            ),
            '<animate attributeName="opacity" values="%s" keyTimes="%s" dur="12s" repeatCount="indefinite"/>' % (
                opacity_values, key_times,
            ),
            "</text>",
        ])
    return "".join(output)


def render_svg(theme: str, record: Dict[str, object]) -> str:
    """Render a 1200 by 300 instrument test report on a blueprint sheet."""
    palette = PALETTES[theme]
    generated_at = ascii_text(str(record.get("generated_at") or "UNKNOWN"))
    checks = record.get("checks", [])
    checks_by_label = {
        str(item.get("label")): item
        for item in checks if isinstance(item, dict)
    } if isinstance(checks, list) else {}
    history = record.get("history", {})
    history = history if isinstance(history, dict) else {}

    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="Instrument test report showing deployment availability and latency">',
        "<defs>",
        '<pattern id="minor-grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="%s" stroke-width="1"/></pattern>' % palette["gridMinor"],
        '<pattern id="major-grid" width="50" height="50" patternUnits="userSpaceOnUse"><rect width="50" height="50" fill="url(#minor-grid)"/><path d="M 50 0 L 0 0 0 50" fill="none" stroke="%s" stroke-width="1"/></pattern>' % palette["gridMajor"],
        '<clipPath id="chart-clip"><rect x="320" y="86" width="846" height="162"/></clipPath>',
        "</defs>",
        '<rect width="1200" height="300" fill="%s"/>' % palette["bg"],
        '<rect width="1200" height="300" fill="url(#major-grid)"/>',
        '<rect x="10" y="10" width="1180" height="280" fill="none" stroke="%s" stroke-width="1.5"/>' % palette["accent"],
        '<path d="M10 70H1190M10 258H1190M306 70V258" stroke="%s" stroke-width="1"/>' % palette["gridMajor"],
        '<rect x="28" y="20" width="455" height="35" fill="%s" stroke="%s"/>' % (palette["bg2"], palette["accent"]),
        svg_text(42, 42, "TEST REPORT · AVAILABILITY & LATENCY", 14, palette["ink"], 405, weight=700),
        svg_text(1172, 42, "UTC " + generated_at, 12, palette["ink"], 275, anchor="end", weight=700),
        svg_text(28, 84, "TARGET", 12, palette["dim"], 160, weight=700),
        svg_text(205, 84, "HTTP", 12, palette["dim"], 60, anchor="middle", weight=700),
        svg_text(294, 84, "LATEST", 12, palette["dim"], 54, anchor="end", weight=700),
        svg_text(320, 84, "LATENCY SCALE / 0-400 MS", 12, palette["dim"], 250, weight=700),
        svg_text(1166, 84, "RECORDED HISTORY", 12, palette["dim"], 215, anchor="end", weight=700),
        '<path d="M320 92V246M425 92V246M530 92V246M635 92V246" stroke="%s" stroke-dasharray="2 4"/>' % palette["gridMajor"],
        svg_text(320, 258, "0", 12, palette["dim"], 20),
        svg_text(425, 258, "150", 12, palette["dim"], 28, anchor="middle"),
        svg_text(530, 258, "300", 12, palette["dim"], 28, anchor="middle"),
        svg_text(635, 258, "400", 12, palette["dim"], 28, anchor="middle"),
    ]

    for row, (label, unused_url, unused_ms) in enumerate(SITES):
        check = checks_by_label.get(label, {})
        status_code = check.get("status_code") if isinstance(check, dict) else None
        latency = max(0, int(check.get("latency_ms") or 0)) if isinstance(check, dict) else 0
        known = status_code is not None
        is_ok = bool(check.get("ok")) if isinstance(check, dict) else False
        row_y = 108 + row * 48
        status_label = ("%s OK" % status_code) if is_ok else (
            "NO RESP" if status_code is None else "%s FAIL" % status_code
        )
        status_colour = palette["ok"] if is_ok else palette["red"]
        bar_colour = latency_colour(latency, known, palette)
        bar_width = min(315.0, latency / 400.0 * 315.0) if known else 0.0
        points, count, low, high = sparkline(
            history.get(label, []), 700, row_y + 2, 300, 24,
        )
        caption = (
            "%d checks recorded · %d-%d ms" % (count, low, high)
            if count else "0 checks recorded · n/a"
        )
        body.extend([
            '<rect x="20" y="%d" width="1150" height="38" fill="%s"/>' % (
                row_y - 11, palette["band"] if row % 2 == 0 else palette["bg2"],
            ),
            '<path d="M20 %dH1170" stroke="%s"/>' % (row_y + 28, palette["gridMajor"]),
            svg_text(28, row_y + 6, label, 13, palette["ink"], 137, weight=700),
            '<rect x="175" y="%d" width="60" height="18" fill="%s"/>' % (
                row_y - 9, status_colour,
            ),
            svg_text(205, row_y + 4, status_label, 12, palette["bg"], 52, anchor="middle", weight=700),
            number_animation(294, row_y + 5, latency, palette) if known else
            svg_text(294, row_y + 5, "n/a", 13, palette["ink"], 54, anchor="end", weight=700),
            '<rect x="320" y="%d" width="315" height="14" fill="%s" stroke="%s"/>' % (
                row_y - 11, palette["bg"], palette["gridMajor"],
            ),
            '<rect x="320" y="%d" width="0" height="14" fill="%s">' % (row_y - 11, bar_colour),
            '<animate attributeName="width" values="0;0;%.1f;%.1f" keyTimes="0;0.08;0.22;1" dur="12s" repeatCount="indefinite"/>' % (bar_width, bar_width),
            "</rect>",
            '<path d="M700 %dH1000" stroke="%s" stroke-dasharray="2 4"/>' % (row_y + 14, palette["gridMajor"]),
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1000" stroke-dashoffset="1000">' % (
                points, bar_colour,
            ),
            '<animate attributeName="stroke-dashoffset" values="1000;1000;0;0" keyTimes="0;0.10;0.30;1" dur="12s" repeatCount="indefinite"/>',
            "</polyline>",
            svg_text(1166, row_y + 6, caption, 11, palette["dim"], 200, anchor="end"),
        ])
        if count == 1 and points:
            point_x, point_y = points.split(" ")[0].split(",")
            body.append('<circle cx="%s" cy="%s" r="3" fill="%s"/>' % (
                point_x, point_y, bar_colour,
            ))

    body.extend([
        '<g clip-path="url(#chart-clip)" opacity="0.65">',
        '<line x1="320" y1="88" x2="320" y2="244" stroke="%s" stroke-width="1.5" stroke-dasharray="4 4">' % palette["accent"],
        '<animate attributeName="x1" values="320;320;1166;1166;320;320" keyTimes="0;0.08;0.62;0.86;0.97;1" dur="12s" repeatCount="indefinite"/>',
        '<animate attributeName="x2" values="320;320;1166;1166;320;320" keyTimes="0;0.08;0.62;0.86;0.97;1" dur="12s" repeatCount="indefinite"/>',
        "</line>",
        "</g>",
        '<path d="M10 270H1190" stroke="%s"/>' % palette["gridMajor"],
        svg_text(28, 283, "METHOD: TWO HTTPS GET SAMPLES PER TARGET · BAR SCALE 0-400 MS", 12, palette["dim"], 695, weight=700),
        svg_text(1172, 283, "INSTRUMENT SHEET / REV 01", 12, palette["accent"], 250, anchor="end", weight=700),
        "</svg>",
    ])
    return "\n".join(body) + "\n"


def write_outputs(record: Dict[str, object]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    DARK_PATH.write_text(render_svg("dark", record), encoding="utf-8")
    LIGHT_PATH.write_text(render_svg("light", record), encoding="utf-8")


def main() -> int:
    mock = os.environ.get("REPORT_MOCK") == "1"
    generated_at = timestamp()
    checks = [
        check_site(label, url, known_ms, mock)
        for label, url, known_ms in SITES
    ]
    history = load_history()
    if not mock:
        history = update_history(history, checks, generated_at)
    record = {
        "generated_at": generated_at,
        "mode": "mock" if mock else "live",
        "repositories": collect_repositories(mock),
        "checks": checks,
        "history": history,
    }
    write_outputs(record)
    print("testreport: wrote %s and two SVG sheets" % DATA_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
