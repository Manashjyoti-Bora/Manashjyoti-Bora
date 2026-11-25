"""kit.py - shared palette, geometry and escaping helpers for the profile sheets.

Every SVG on this profile is produced by the files in this folder, so the whole
art set can be rebuilt (`python3 art/build_all.py`), diffed and audited. No
JavaScript, no external fonts, no bitmaps except the one portrait.

Units are SVG user units (px at 1:1). Fonts are asked for by generic family so
GitHub's own font stack decides the final letterforms.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

# Sheet width shared by every artboard, so stacked sections never jump width.
W = 1160

# Two palettes, one sheet. `aurora` is the dark grade, `daylight` the light one.
PALETTES = {
    "aurora": {
        "bg_a": "#04060D",
        "bg_b": "#0A1122",
        "bg_c": "#0B1D2E",
        "card": "#0C1424",
        "card_2": "#101A2E",
        "line": "#1C2A44",
        "line_soft": "#16233A",
        "ink": "#EAF1FF",
        "ink_soft": "#9DB0CE",
        "ink_mute": "#5F7395",
        "cyan": "#4DE1FF",
        "violet": "#9B8CFF",
        "mint": "#5BF2B8",
        "amber": "#FFD260",
        "rose": "#FF6E9C",
        "glow": 0.55,
        "grid": "#132038",
    },
    "daylight": {
        "bg_a": "#FBFCFF",
        "bg_b": "#F1F5FD",
        "bg_c": "#EAF1FC",
        "card": "#FFFFFF",
        "card_2": "#F6F9FF",
        "line": "#D5DFF0",
        "line_soft": "#E4EBF7",
        "ink": "#0B1326",
        "ink_soft": "#40506E",
        "ink_mute": "#7787A6",
        "cyan": "#0A7E9E",
        "violet": "#5A46E0",
        "mint": "#0E8F62",
        "amber": "#A96B00",
        "rose": "#C3114F",
        "glow": 0.0,
        "grid": "#DCE5F4",
    },
}

ACCENTS = ("cyan", "violet", "mint", "amber", "rose")


def esc(text: object) -> str:
    """XML-escape a value for text or attribute content."""
    s = str(text)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def f(v: float) -> str:
    """Compact number formatting: no trailing zeros, no '-0'."""
    if abs(v) < 0.005:
        return "0"
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    """Blend two hex colours, t=0 -> a, t=1 -> b."""
    ra, ga, ba = rgb(a)
    rb, gb, bb = rgb(b)
    return "#%02X%02X%02X" % (
        round(ra + (rb - ra) * t),
        round(ga + (gb - ga) * t),
        round(ba + (bb - ba) * t),
    )


def alpha(hex_color: str, a: float) -> str:
    """Hex-with-alpha. SVG 1.1 (what GitHub sanitises against) has no rgba()."""
    r, g, b = rgb(hex_color)
    return f"#{r:02X}{g:02X}{b:02X}{max(0, min(255, round(a * 255))):02X}"


# Two explicit families instead of the generic ones. GitHub has no Inter, so
# on github.com these resolve to the platform sans/mono; resvg has no generic
# fallback, so "sans-serif" would render as an invisible blank there. Same
# fallback behaviour, but it also works offline (see art/preview.py).
# Exactly one family name per text element: resvg ignores any font-family
# containing a comma, so stacks silently disappear offline. "Helvetica" exists
# (or aliases) on every preview host; browsers that lack it fall back to their
# default sans, which is the same behaviour a stack would give.
FONT = "Helvetica"
MONO = "DejaVu Sans Mono"
MONO = "monospace"


def text(
    x: float,
    y: float,
    s: object,
    fill: str,
    size: float = 13,
    weight: int = 400,
    anchor: str = "start",
    family: str = FONT,
    spacing: float | None = None,
    opacity: float | None = None,
    extra: str = "",
) -> str:
    """One <text> element. Keep the markup terse; the file is read by humans."""
    attrs = [
        f'x="{f(x)}"',
        f'y="{f(y)}"',
        f'fill="{fill}"',
        f'font-size="{f(size)}"',
        f'font-weight="{weight}"',
        # A bare family name (never a stack) - see the note on FONT below.
        f'font-family="{family}"',
    ]
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{f(spacing)}"')
    if opacity is not None:
        attrs.append(f'opacity="{f(opacity)}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)}>{esc(s)}</text>'


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = "none",
    rx: float = 0,
    stroke: str | None = None,
    sw: float = 1,
    extra: str = "",
) -> str:
    attrs = [f'x="{f(x)}"', f'y="{f(y)}"', f'width="{f(w)}"', f'height="{f(h)}"', f'fill="{fill}"']
    if rx:
        attrs.append(f'rx="{f(rx)}"')
    if stroke:
        attrs += [f'stroke="{stroke}"', f'stroke-width="{f(sw)}"']
    if extra:
        attrs.append(extra)
    return f'<rect {" ".join(attrs)}/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, sw: float = 1, extra: str = "") -> str:
    attrs = [f'x1="{f(x1)}"', f'y1="{f(y1)}"', f'x2="{f(x2)}"', f'y2="{f(y2)}"']
    attrs += [f'stroke="{stroke}"', f'stroke-width="{f(sw)}"']
    if extra:
        attrs.append(extra)
    return f'<line {" ".join(attrs)}/>'


def circle(cx: float, cy: float, r: float, fill: str = "none", stroke: str | None = None, sw: float = 1, extra: str = "") -> str:
    attrs = [f'cx="{f(cx)}"', f'cy="{f(cy)}"', f'r="{f(r)}"', f'fill="{fill}"']
    if stroke:
        attrs += [f'stroke="{stroke}"', f'stroke-width="{f(sw)}"']
    if extra:
        attrs.append(extra)
    return f'<circle {" ".join(attrs)}/>'


def poly(points: Sequence[Tuple[float, float]], fill: str = "none", stroke: str | None = None, sw: float = 1, closed: bool = False, extra: str = "") -> str:
    pts = " ".join(f"{f(x)},{f(y)}" for x, y in points)
    attrs = [f'points="{pts}"', f'fill="{fill}"']
    if stroke:
        attrs += [f'stroke="{stroke}"', f'stroke-width="{f(sw)}"', 'stroke-linejoin="round"', 'stroke-linecap="round"']
    if closed:
        attrs.append('stroke-linejoin="round"')
    if extra:
        attrs.append(extra)
    return f'<polyline {" ".join(attrs)}/>'


def path(d: str, fill: str = "none", stroke: str | None = None, sw: float = 1, extra: str = "") -> str:
    attrs = [f'd="{d}"', f'fill="{fill}"']
    if stroke:
        attrs += [f'stroke="{stroke}"', f'stroke-width="{f(sw)}"', 'stroke-linejoin="round"', 'stroke-linecap="round"']
    if extra:
        attrs.append(extra)
    return f'<path {" ".join(attrs)}/>'


def sparkline(values: Sequence[float], x: float, y: float, w: float, h: float, stroke: str, sw: float = 2.2) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = w / max(1, len(values) - 1)
    pts = [(x + i * step, y + h - (v - lo) / span * h) for i, v in enumerate(values)]
    d = "M" + " L".join(f"{f(px)} {f(py)}" for px, py in pts)
    area = d + f" L{f(x + w)} {f(y + h)} L{f(x)} {f(y + h)} Z"
    return (
        f'<path d="{area}" fill="{stroke}" opacity="0.10"/>'
        + path(d, stroke=stroke, sw=sw, extra='stroke-linejoin="round"')
    )


def wrap(s: str, width: int) -> List[str]:
    """Greedy word wrap for captions; no font metrics, so width is in chars."""
    out: List[str] = []
    cur = ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if len(cand) > width and cur:
            out.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def stars(n: int = 3) -> str:
    return "\u2726 " * n


def polar(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    a = math.radians(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def donut_slice(cx: float, cy: float, r_out: float, r_in: float, a0: float, a1: float) -> str:
    """Path for one annular slice, from a0 to a1 degrees clockwise from 12 o'clock."""
    large = 1 if (a1 - a0) % 360 > 180 else 0
    x0, y0 = polar(cx, cy, r_out, a0)
    x1, y1 = polar(cx, cy, r_out, a1)
    x2, y2 = polar(cx, cy, r_in, a1)
    x3, y3 = polar(cx, cy, r_in, a0)
    return (
        f"M{f(x0)} {f(y0)} A{f(r_out)} {f(r_out)} 0 {large} 1 {f(x1)} {f(y1)} "
        f"L{f(x2)} {f(y2)} A{f(r_in)} {f(r_in)} 0 {large} 0 {f(x3)} {f(y3)} Z"
    )


def svg_open(p: dict, width: int, height: int, title: str, desc: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d" '
        f'style="background:{p["bg_a"]}">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
    )


def defs_common(p: dict, seed: str = "g") -> str:
    """Gradients and filters shared by every sheet: backdrop, glow, fades."""
    glow = p["glow"]
    return (
        "<defs>"
        '<linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{p["bg_a"]}"/>'
        f'<stop offset="0.55" stop-color="{p["bg_b"]}"/>'
        f'<stop offset="1" stop-color="{p["bg_c"]}"/>'
        "</linearGradient>"
        '<linearGradient id="sweepGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{p["cyan"]}"/>'
        f'<stop offset="0.5" stop-color="{p["violet"]}"/>'
        f'<stop offset="1" stop-color="{p["mint"]}"/>'
        "</linearGradient>"
        '<radialGradient id="haloGrad" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{p["cyan"]}" stop-opacity="{f(0.30 if glow else 0.10)}"/>'
        f'<stop offset="1" stop-color="{p["cyan"]}" stop-opacity="0"/>'
        "</radialGradient>"
        '<radialGradient id="haloViolet" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{p["violet"]}" stop-opacity="{f(0.26 if glow else 0.08)}"/>'
        f'<stop offset="1" stop-color="{p["violet"]}" stop-opacity="0"/>'
        "</radialGradient>"
        f'<linearGradient id="{seed}Fade" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{p["ink"]}" stop-opacity="0"/>'
        f'<stop offset="0.35" stop-color="{p["ink"]}" stop-opacity="0.9"/>'
        "</linearGradient>"
        f'<filter id="{seed}Glow" x="-40%" y="-40%" width="180%" height="180%">'
        f'<feGaussianBlur stdDeviation="{f(6 if glow else 1)}" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        "</defs>"
    )


def static_wave(cycles: float, width: float, base: float, amp: float, step: float = 4.0) -> str:
    """A deterministic sine polyline - the only 'motion' here is opacity, not time."""
    pts = []
    x = 0.0
    while x <= width:
        y = base + math.sin((x / width) * cycles * 2 * math.pi) * amp
        pts.append((x, y))
        x += step
    return poly(pts, stroke="url(#sweepGrad)", sw=1.6, extra='opacity="0.55"')


def label(p: dict, x: float, y: float, s: str, accent: str = "cyan") -> str:
    """Small uppercase section label with a leading dot."""
    return (
        circle(x + 3, y - 4, 3, p[accent])
        + text(x + 12, y, s, p["ink_soft"], 10.5, 700, spacing=2.4)
    )


def ruler(p: dict, x0: float, x1: float, y: float, ticks: int, label_fn=None) -> str:
    out = [line(x0, y, x1, y, p["line"], 1)]
    for i in range(ticks + 1):
        x = x0 + (x1 - x0) * i / ticks
        tall = i % 5 == 0
        out.append(line(x, y, x, y - (7 if tall else 3), p["line"], 1))
        if tall and label_fn:
            out.append(text(x, y + 14, label_fn(i), p["ink_mute"], 9, 500, anchor="middle", family=MONO))
    return "".join(out)


def stars_dots(seed: int, w: int, h: int, count: int, colors: Iterable[str]) -> str:
    """Deterministic star field: a plain LCG so rebuilds are byte-identical."""
    state = seed
    colors = list(colors)
    out = []
    for i in range(count):
        state = (1103515245 * state + 12345) % (2**31)
        x = state % w
        state = (1103515245 * state + 12345) % (2**31)
        y = state % h
        state = (1103515245 * state + 12345) % (2**31)
        r = 0.4 + (state % 100) / 140.0
        state = (1103515245 * state + 12345) % (2**31)
        c = colors[state % len(colors)]
        op = 0.10 + (state % 100) / 260.0
        out.append(circle(x, y, r, c, extra=f'opacity="{f(op)}"'))
    return "".join(out)
