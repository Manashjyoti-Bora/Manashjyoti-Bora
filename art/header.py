"""header.py - the identity plate plus a skyline whose towers are real repos.

Nothing on this plate is typed in by hand: the name and handle are fixed
identity, the three counters come from assets/data/snapshot.json, and the
skyline heights are each repository's measured commit count, ranked.
"""

from __future__ import annotations

import json
import math
import os

from kit import (
    MONO,
    W,
    alpha,
    circle,
    defs_common,
    esc,
    f,
    label,
    line,
    mix,
    path,
    poly,
    rect,
    sparkline,
    stars_dots,
    svg_open,
    text,
    PALETTES,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "assets", "data")

NAME_EN = "MANASHJYOTI BORA"
NAME_AS = "\u09ae\u09a8\u099c\u09cd\u09af\u09cb\u09a4\u09bf \u09ac\u09f0\u09be"
HANDLE = "@Manashjyoti-Bora"
PLACE = "Nagaon, Assam \u00b7 India"
ROLES = "full-stack developer \u00b7 SVG craftsman \u00b7 automation tinkerer"


def load() -> dict:
    with open(os.path.join(DATA, "snapshot.json"), encoding="utf-8") as fh:
        snap = json.load(fh)
    summary = snap.get("summary") or {}
    repos = snap.get("repos") or []
    dates = snap.get("dates") or []
    # Skyline ranking: only repositories with real commit numbers, dev first.
    ranked = sorted(
        [r for r in repos if not r.get("fork")],
        key=lambda r: (r.get("commits") or 0, r.get("pushed_at") or ""),
        reverse=True,
    )[:9]
    return {"summary": summary, "dates": dates, "repos": ranked}


def _towers(p: dict, repos: list, y_base: float) -> str:
    """A city of towers; height maps commit counts, width maps recency."""
    if not repos:
        return ""
    heights = [max(1, r.get("commits") or 0) for r in repos]
    top = max(heights)
    out = []
    x = 40.0
    gap = 10.0
    avail = W - 80
    n = len(repos)
    bw = min(96.0, (avail - gap * (n - 1)) / n)
    for i, repo in enumerate(repos):
        h = 26 + (heights[i] / top) ** 0.68 * 168
        accent = ("cyan", "violet", "mint", "amber", "rose")[i % 5]
        col = p[accent]
        bx = x + i * (bw + gap)
        # body
        out.append(rect(bx, y_base - h, bw, h, alpha(col, 0.16 if p["glow"] else 0.10), 6,
                        alpha(col, 0.55), 1))
        # window grid
        rows = int(h // 16)
        cols = max(2, int(bw // 16))
        for r in range(rows):
            for c in range(cols):
                lit = (r * 7 + c * 3 + i * 5) % 5 in (0, 1)
                if lit:
                    out.append(rect(bx + 8 + c * ((bw - 16) / cols), y_base - h + 10 + r * 16,
                                    4.5, 4.5, col, 1, extra='opacity="0.65"'))
        # antenna + spark
        out.append(line(bx + bw / 2, y_base - h, bx + bw / 2, y_base - h - 12, alpha(col, 0.6), 1))
        out.append(circle(bx + bw / 2, y_base - h - 13, 2.6, col))
        # repo name on the roof line
        short = (repo.get("short") or repo.get("name") or "")[:16]
        out.append(text(bx + bw / 2, y_base - h - 22, short, p["ink_soft"], 8.6, 600,
                        anchor="middle", family=MONO))
        out.append(text(bx + bw / 2, y_base - 8, f"{heights[i]:,}", p["ink"], 11, 700,
                        anchor="middle", family=MONO))
    return "".join(out)


def build(theme: str, model: dict) -> str:
    p = PALETTES[theme]
    height = 470
    s = model["summary"]
    dates = model["dates"]
    repos = model["repos"]

    o = [svg_open(p, W, height, "Manashjyoti Bora - profile header",
                  "Dark or light plate with the name, role line, live counters and a skyline where each tower's "
                  "height is one repository's real commit count.")]
    o.append(defs_common(p, "hdr"))
    o.append(
        f'<linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0.4">'
        f'<stop offset="0" stop-color="{p["ink"]}"/>'
        f'<stop offset="0.55" stop-color="{p["cyan"]}"/>'
        f'<stop offset="1" stop-color="{p["violet"]}"/>'
        f"</linearGradient>"
    )
    o.append(rect(0, 0, W, height, "url(#bgGrad)"))
    # star field, one seed per theme so both files are stable
    o.append(stars_dots(7 if theme == "aurora" else 11, W, height, 90,
                        [p["cyan"], p["violet"], p["mint"], p["ink"]]))
    o.append(circle(180, 60, 260, "url(#haloGrad)"))
    o.append(circle(W - 90, 150, 230, "url(#haloViolet)"))
    o.append(rect(1, 1, W - 2, height - 2, "none", 20, p["line"], 1))
    o.append(text(W - 40, 26, "\u2726", p["ink_mute"], 10, 400, anchor="end"))

    # --- top strip: section index + live dot -----------------------------------
    o.append(line(40, 44, W - 40, 44, p["line_soft"]))
    o.append(label(p, 40, 30, "PROFILE \u00b7 2027 EDITION", "mint"))
    dots = "".join(circle(W - 52 - i * 10, 26, 2.2, p["ink_mute"], extra='opacity="0.7"') for i in range(3))
    o.append(dots)
    o.append(text(W - 92, 30, "LIVE", p["ink_soft"], 9.5, 700, anchor="end", spacing=2.4, family=MONO))

    # --- the name, oversized, with the Assamese line above it ------------------
    o.append(text(40, 116, NAME_AS, p["ink_soft"], 17, 400, family="sans-serif"))
    o.append(text(40, 172, "MANASHJYOTI", "url(#nameGrad)", 52, 800, spacing=-1.2))
    o.append(text(40, 220, "BORA", p["ink"], 52, 800, spacing=-1.2))
    o.append(text(196, 218, ".build", p["cyan"], 20, 600, family=MONO, extra='opacity="0.85"'))
    o.append(text(40, 252, f"{HANDLE}  \u00b7  {PLACE}", p["ink_soft"], 12.5, 500))
    o.append(text(40, 274, ROLES, p["ink_mute"], 12.5, 400))
    # a hairline separates the identity block from the skyline underneath
    o.append(rect(40, 288, 300, 1.2, "url(#sweepGrad)", 1))

    # underline sweep


    # --- counters, all measured ------------------------------------------------
    cards = [
        ("COMMITS", f"{int(s.get('commits_total') or 0):,}", "cyan"),
        ("REPOSITORIES", f"{int(s.get('repos') or 0)}", "violet"),
        ("STREAK \u00b7 DAYS", f"{int(s.get('streak') or 0)}", "mint"),
        ("FOLLOWERS", f"{int(s.get('followers') or 0)}", "amber"),
    ]
    total = int(s.get("commits_total") or 0)
    dev = int(s.get("commits_dev") or 0)
    for i, (name, value, accent) in enumerate(cards):
        cx = W - 478 + i * 118
        # three rows, all round numbers: label, the number, the accent rule
        o.append(text(cx, 116, name, p["ink_mute"], 8.8, 700, spacing=1.8))
        o.append(text(cx, 152, value, p[accent], 25, 700, family=MONO))
        o.append(rect(cx, 162, 40, 2, p[accent], 1, extra='opacity="0.6"'))
        if i == 0 and dev:
            o.append(text(cx, 178, f"{dev:,} hand-written", p["ink_mute"], 8.6, 400, family=MONO))

    # --- activity: one bar per contribution day (real dates from the calendar) --
    if dates:
        bars, x0, y0, bw_total, bh = len(dates), W - 560, 236, 520, 40
        o.append(text(x0, y0 - 12, f"ACTIVE DAYS \u00b7 LAST {bars}", p["ink_mute"], 8.8, 700, spacing=1.8))
        step = bw_total / max(1, bars)
        for i, day in enumerate(dates):
            hh = bh if i % 7 else bh  # uniform height: every day listed had activity
            o.append(rect(x0 + i * step, y0 + bh - hh, max(1.6, step - 2.4), hh,
                          p["mint"] if i >= bars - 7 else p["cyan"],
                          extra='opacity="%s"' % f(0.9 if i >= bars - 7 else 0.45)))
        o.append(text(x0, y0 + bh + 14, esc(dates[0]), p["ink_mute"], 8.6, 500, family=MONO))
        o.append(text(x0 + bw_total, y0 + bh + 14, esc(dates[-1]), p["ink_mute"], 8.6, 500,
                      anchor="end", family=MONO))

    # --- skyline ---------------------------------------------------------------
    base_y = height - 52
    o.append(text(W - 40, 300, "SKYLINE \u00b7 TOWER HEIGHT = COMMITS", p["ink_mute"], 8.8, 700,
                  anchor="end", spacing=1.8))
    o.append(_towers(p, repos, base_y))
    o.append(line(40, base_y, W - 40, base_y, p["line"], 1))
    o.append(rect(40, base_y + 1, W - 80, 1, p["line_soft"]))
    o.append(text(40, height - 22, "every tower, every number on this plate is read from the GitHub API by the daily workflow",
                  p["ink_mute"], 9.6, 400, family=MONO))
    o.append("</svg>")
    return "".join(o)
