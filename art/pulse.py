"""pulse.py - one hour per minute: the automation heartbeat wheel.

A radial chart with 24 hours on the clock face, one hand-length per scheduled
workflow run, and a colour per workflow. The schedule is read out of
.github/workflows/*.yml at build time, so the drawing cannot drift from the
cron lines it claims to describe. Later workflows are drawn on a wider ring so
colliding hours stay readable.
"""

from __future__ import annotations

import glob
import json
import os
import re

from kit import (
    MONO,
    W,
    alpha,
    circle,
    defs_common,
    f,
    label,
    line,
    path,
    polar,
    rect,
    svg_open,
    text,
    PALETTES,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Workflow file -> (display name, accent, ring index). Rings are wider the
# busier the workflow is, so simultaneous hours never overlap.
ORDER = {
    "daily-update.yml": ("daily self-update", "cyan"),
    "live-stats.yml": ("live telemetry", "violet"),
    "sheet.yml": ("blueprint sheets", "mint"),
    "guestbook.yml": ("signature margin", "amber"),
    "snake.yml": ("snake", "rose"),
    "pacman.yml": ("pac-man", "cyan"),
    "profile-3d.yml": ("3d graph", "violet"),
    "pulse.yml": ("pulse (this chart)", "mint"),
    "skyline.yml": ("skyline", "amber"),
    "ledger.yml": ("ledger", "rose"),
    "badges.yml": ("badges", "cyan"),
    "stamp.yml": ("commit stamp", "violet"),
    "dispatch.yml": ("dispatch desk", "mint"),
    "daybreak.yml": ("daybreak digest", "rose"),
}

WEEKDAY = {"MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6, "SUN": 0}


def parse_cron(expr: str, hours: set, count: dict) -> None:
    """Expand a 5-field cron into the hour-of-day it fires at (UTC)."""
    fields = expr.split()
    if len(fields) != 5:
        return
    minute_f, hour_f, dom_f, mon_f, dow_f = fields
    if dom_f != "*" or mon_f != "*":
        return
    if dow_f not in ("*", "*/*"):
        return
    hours.add(hour_f)
    count["n"] += 1


def read_schedule() -> list:
    workflows = []
    for path in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        base = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        exprs = re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", src)
        if not exprs:
            continue
        name, accent = ORDER.get(base, (base.rsplit(".", 1)[0], "cyan"))
        runs = []
        for expr in exprs:
            parts = expr.split()
            if len(parts) != 5:
                continue
            minute_f, hour_f, dom_f, mon_f, dow_f = parts
            if dom_f != "*" or mon_f != "*" or dow_f not in ("*", "*/*"):
                continue
            if hour_f == "*":
                hrs = list(range(24))
            elif hour_f.startswith("*/"):
                step = int(hour_f[2:])
                hrs = list(range(0, 24, step))
            elif "," in hour_f:
                hrs = [int(h) for h in hour_f.split(",")]
            else:
                hrs = [int(hour_f)]
            if minute_f == "*":
                n = 60
            elif minute_f.startswith("*/"):
                n = 60 // int(minute_f[2:])
            elif "," in minute_f:
                n = len(minute_f.split(","))
            else:
                n = 1
            for h in hrs:
                runs.append({"hour": h, "minute": int(minute_f.split(",")[0]) if minute_f[0].isdigit() else 0,
                             "per_hour": n})
        workflows.append({"file": base, "name": name, "accent": accent,
                          "cron": exprs, "runs": runs})
    return workflows


def build(theme: str, workflows: list) -> tuple[str, dict]:
    p = PALETTES[theme]
    height = 560
    cx, cy = 330.0, 300.0
    o = [svg_open(p, W, height, "Automation heartbeat",
                  "A 24-hour clock where every hand is one scheduled workflow run, read from the workflow "
                  "files at build time; ring width grows with run frequency so overlapping hours stay apart.")]
    o.append(defs_common(p, "pul"))
    o.append(rect(0, 0, W, height, "url(#bgGrad)"))
    o.append(circle(330, 190, 260, "url(#haloGrad)"))
    o.append(rect(1, 1, W - 2, height - 2, "none", 20, p["line"], 1))

    o.append(label(p, 40, 44, "THE HEARTBEAT  \u00b7  24H UTC", "rose"))
    o.append(text(40, 74, "Every scheduled run, as a clock hand", p["ink"], 21, 700))

    # --- the ring of hours -----------------------------------------------------
    for h in range(4):
        a0 = h * 90.0
        x1, y1 = polar(cx, cy, 244, a0)
        x2, y2 = polar(cx, cy, 244, a0 + 90)
        o.append(path(f"M{f(x1)} {f(y1)} A244 244 0 0 1 {f(x2)} {f(y2)}",
                      stroke=alpha(p["line"], 0.9), sw=1.2))
    for h in range(0, 24, 3):
        x, y = polar(cx, cy, 262, h * 15)
        ticker = h % 6
        o.append(text(x, y + 4, f"{h:02d}", p["ink_soft"] if ticker == 0 else p["ink_mute"],
                      11 if ticker == 0 else 9.5, 700 if ticker == 0 else 400,
                      anchor="middle", family=MONO))

    # --- one hand per workflow, one tick per hour it fires ---------------------
    rings = sorted(workflows, key=lambda w: len({r["hour"] for r in w["runs"]}), reverse=True)
    max_ticks = max(1, len(rings))
    legend = []
    for i, wf in enumerate(rings):
        accent = wf["accent"]
        col = p[accent]
        radius = 100 + (i / max(1, max_ticks - 1)) * 132 if max_ticks > 1 else 160
        hours = sorted({r["hour"] for r in wf["runs"]})
        o.append(circle(cx, cy, radius, "none", alpha(col, 0.18), 1, extra='stroke-dasharray="2 4"'))
        for h in hours:
            x1, y1 = polar(cx, cy, radius - 7, h * 15 + 7.5)
            x2, y2 = polar(cx, cy, radius + 7, h * 15 + 7.5)
            o.append(line(x1, y1, x2, y2, col, 3.6, extra='stroke-linecap="round"'))
            # a faint second tick shows the hour the run lands on even at 1:1
            xa, ya = polar(cx, cy, radius + 12, h * 15 + 7.5)
            xb, yb = polar(cx, cy, radius + 16, h * 15 + 7.5)
            o.append(line(xa, ya, xb, yb, col, 1.2, extra='opacity="0.5"'))
        legend.append((wf["name"], col, hours, len(wf["runs"])))

    o.append(circle(cx, cy, 58, p["card"], extra=f'stroke="{p["line"]}"'))
    total_runs = sum(len(w["runs"]) for w in workflows)
    o.append(text(cx, cy + 8, str(total_runs), p["ink"], 28, 700, anchor="middle", family=MONO))
    o.append(text(cx, cy + 13, "RUNS / DAY", p["ink_mute"], 8.6, 700, anchor="middle", spacing=0.8))
    o.append(text(cx, cy + 27, f"{len(workflows)} workflows", p["ink_mute"], 8.6, 400, anchor="middle"))

    # --- legend table ----------------------------------------------------------
    x0 = 640
    o.append(label(p, x0, 44, "SCHEDULE LEDGER", "mint"))
    o.append(text(x0, 74, "workflow", p["ink_mute"], 9, 700, spacing=1.6))
    o.append(text(x0 + 210, 74, "cron (utc)", p["ink_mute"], 9, 700, spacing=1.6))
    o.append(text(W - 40, 74, "runs", p["ink_mute"], 9, 700, anchor="end", spacing=1.6))
    o.append(line(x0, 84, W - 40, 84, p["line"]))
    rows = sorted(legend, key=lambda r: -r[3])
    for i, (name, col, hours, n) in enumerate(rows):
        y = 110 + i * 31
        o.append(circle(x0 + 4, y - 4, 4, col))
        o.append(text(x0 + 16, y, name[:24], p["ink"], 11.5, 600))
        hrs = ",".join(f"{h:02d}" for h in hours)
        if len(hrs) > 20:
            hrs = hrs[:18] + "\u2026"
        o.append(text(x0 + 210, y, hrs, p["ink_soft"], 10.5, 400, family=MONO))
        o.append(text(W - 40, y, f"{n}\u00d7", p[("cyan", "violet", "mint", "amber", "rose")[i % 5]],
                      11.5, 700, anchor="end", family=MONO))
    o.append(line(x0, 110 + len(rows) * 31 - 12, W - 40, 110 + len(rows) * 31 - 12, p["line_soft"]))
    o.append(text(x0, 110 + len(rows) * 31 + 8,
                  "cron expanded from .github/workflows/*.yml at build time \u2014 no numbers typed by hand",
                  p["ink_mute"], 9.4, 400, family=MONO))

    o.append("</svg>")
    return "".join(o), {"workflows": len(workflows), "runs": total_runs,
                        "names": [r[0] for r in rows]}
