"""live_stats.py - probe every live deployment twice, then draw the results.

For each URL: two HTTPS requests, keep the better latency, record status codes,
Content-Type, response size and a SHA-256 of the first 8 KiB. On the next run
the previous fingerprint is compared, so the sheet can say "html unchanged in
N runs" instead of guessing. Everything lands in assets/live-{aurora,daylight}.svg
and assets/data/live.json.

Run:  python3 .github/scripts/live_stats.py
Env:  LIVE_MOCK=1 draws from a synthetic record (for local checks).
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

TARGETS = [
    ("portfolio", "https://portfolio-manashjyoti-bora.vercel.app"),
    ("nexusmart", "https://nexusmart-dusky.vercel.app"),
]

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "assets", "data", "live.json")

PALETTES = {
    "aurora": dict(bg="#05070F", card="#0B1220", line="#1B2740", ink="#EAF1FF", soft="#93A6C4",
                   mute="#5B6E8E", ok="#4DF2B4", warn="#FFD260", bad="#FF6E9C", accent="#4DE1FF"),
    "daylight": dict(bg="#FFFFFF", card="#F6F9FF", line="#D6E0F0", ink="#0B1326", soft="#41516F",
                     mute="#7A8AA8", ok="#0E8F62", warn="#A96B00", bad="#C3114F", accent="#0A7E9E"),
}


def probe(url: str) -> dict:
    best = None
    codes = []
    meta = {}
    for _ in range(2):
        started = time.perf_counter()
        req = urllib.request.Request(url, headers={"User-Agent": "mjb-live-probe/2.0", "Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=12) as res:
                body = res.read(8192)
                ms = int((time.perf_counter() - started) * 1000)
                codes.append(res.status)
                meta = {
                    "content_type": res.headers.get("Content-Type", ""),
                    "bytes": res.headers.get("Content-Length") or len(body),
                    "server": (res.headers.get("Server") or "").split("/")[0],
                }
        except urllib.error.HTTPError as exc:
            ms = int((time.perf_counter() - started) * 1000)
            codes.append(exc.code)
            body = b""
        except (urllib.error.URLError, socket.timeout, ssl.SSLError, TimeoutError):
            ms = int((time.perf_counter() - started) * 1000)
            codes.append(0)
            body = b""
        if body:
            best = {"ms": ms, "fingerprint": hashlib.sha256(body).hexdigest()[:12], **meta}
        elif best is None:
            best = {"ms": ms, "fingerprint": "", **meta}
        else:
            best["ms"] = min(best["ms"], ms)
    return {"status": codes[-1] if codes else 0, "codes": codes, **best, "url": url}


def mock() -> list:
    return [
        {"label": "portfolio", "url": TARGETS[0][1], "status": 200, "codes": [200, 200], "ms": 84,
         "fingerprint": "a1b2c3d4e5f6", "content_type": "text/html; charset=utf-8", "bytes": 48211, "server": "Vercel"},
        {"label": "nexusmart", "url": TARGETS[1][1], "status": 200, "codes": [200, 200], "ms": 57,
         "fingerprint": "0f9e8d7c6b5a", "content_type": "text/html; charset=utf-8", "bytes": 39876, "server": "Vercel"},
    ]


def badge(p: dict, x: float, y: float, label: str, value: str, colour: str, w: float = 132) -> str:
    return (
        f'<g><rect x="{x}" y="{y}" width="{w}" height="26" rx="13" fill="{p["card"]}" stroke="{p["line"]}"/>'
        f'<text x="{x + 12}" y="{y + 17}" fill="{p["mute"]}" font-size="9" font-weight="700" '
        f'font-family="DejaVu Sans Mono">{label}</text>'
        f'<text x="{x + w - 12}" y="{y + 17}" fill="{colour}" font-size="10.5" font-weight="700" '
        f'text-anchor="end" font-family="DejaVu Sans Mono">{value}</text></g>'
    )


def render(theme: str, rows: list, when: str, repeat: dict) -> str:
    p = PALETTES[theme]
    W, H = 1160, 150 + len(rows) * 96
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         f'<title>Live deployment checks</title><desc>HTTP status, latency and content fingerprint for each live app.</desc>',
         f'<rect width="{W}" height="{H}" rx="18" fill="{p["bg"]}" stroke="{p["line"]}"/>',
         f'<rect x="24" y="24" width="10" height="10" rx="2" fill="{p["accent"]}"/>',
         f'<text x="44" y="34" fill="{p["soft"]}" font-size="10" font-weight="700" letter-spacing="2.4" '
         f'font-family="Helvetica">LIVE PROBE \u00b7 TWO REQUESTS PER APP</text>',
         f'<text x="{W - 24}" y="34" fill="{p["mute"]}" font-size="10" text-anchor="end" '
         f'font-family="DejaVu Sans Mono">{when}</text>']
    for i, row in enumerate(rows):
        y = 62 + i * 96
        ok = row["status"] == 200
        col = p["ok"] if ok else p["bad"]
        o.append(f'<rect x="24" y="{y}" width="{W - 48}" height="80" rx="14" fill="{p["card"]}" stroke="{p["line"]}"/>')
        o.append(f'<circle cx="50" cy="{y + 40}" r="9" fill="{col}" opacity="0.18"/>')
        o.append(f'<circle cx="50" cy="{y + 40}" r="4.5" fill="{col}"/>')
        o.append(f'<text x="74" y="{y + 28}" fill="{p["ink"]}" font-size="15" font-weight="700" '
                 f'font-family="Helvetica">{row["label"]}</text>')
        o.append(f'<text x="74" y="{y + 46}" fill="{p["mute"]}" font-size="10" '
                 f'font-family="DejaVu Sans Mono">{row["url"].replace("https://", "")}</text>')
        # latency bar scaled to 400 ms
        bar_x, bar_w = 74, 300
        filled = max(4, min(bar_w, row["ms"] / 400 * bar_w))
        o.append(f'<rect x="{bar_x}" y="{y + 58}" width="{bar_w}" height="6" rx="3" fill="{p["line"]}"/>')
        o.append(f'<rect x="{bar_x}" y="{y + 58}" width="{filled:.0f}" height="6" rx="3" fill="{col}"/>')
        o.append(f'<text x="{bar_x + bar_w + 10}" y="{y + 64}" fill="{p["soft"]}" font-size="10" '
                 f'font-family="DejaVu Sans Mono">{row["ms"]} ms</text>')
        bx = W - 24 - 4 * 138 + 6
        o.append(badge(p, bx, y + 14, "STATUS", f"{row['status']} / {row['codes'][0]}", col))
        o.append(badge(p, bx + 138, y + 14, "REPEAT", f"{row['repeat_n']}x same", p["accent"]))
        o.append(badge(p, bx + 276, y + 14, "SERVER", (row.get("server") or "?")[:8], p["soft"]))
        o.append(badge(p, bx + 414, y + 14, "SHAPE", row["fingerprint"] or "none", p["soft"], 128))
    o.append(f'<text x="24" y="{H - 18}" fill="{p["mute"]}" font-size="9.5" font-family="DejaVu Sans Mono">'
             f'a fingerprint is the sha-256 of the first 8 KiB; a changed shape means the page itself changed</text>')
    o.append("</svg>")
    return "".join(o)


def main() -> int:
    repeat_prev = {}
    live_probe = not os.environ.get("LIVE_MOCK")
    if os.path.isfile(DATA):
        try:
            with open(DATA, encoding="utf-8") as fh:
                prev = json.load(fh)
            repeat_prev = {r["label"]: (r.get("fingerprint"), r.get("repeat_n", 1)) for r in prev.get("rows", [])}
        except Exception:
            pass
    if not live_probe:
        rows = mock()
    else:
        rows = []
        for name, url in TARGETS:
            r = probe(url)
            r["label"] = name
            rows.append(r)
    for r in rows:
        fp, n = repeat_prev.get(r["label"], (None, 1))
        r["repeat_n"] = n + 1 if fp and fp == r["fingerprint"] else 1
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump({"generated_at": when, "rows": rows}, fh, indent=2)
        fh.write("\n")
    for theme in PALETTES:
        with open(os.path.join(ROOT, "assets", f"live-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(render(theme, rows, when, repeat_prev))
    print("live_stats: " + ", ".join(f"{r['label']}={r['status']}/{r['ms']}ms" for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
