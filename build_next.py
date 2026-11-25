#!/usr/bin/env python3
"""Build the 2026 profile art set — a single deterministic source of truth.

Emits six theme-aware SVG sections (dark + light) used by README.md:

    assets/next-hero-{dark,light}.svg        the opening frame
    assets/next-about-{dark,light}.svg       capabilities + autoplay carousel
    assets/next-stack-{dark,light}.svg       three tilted tech orbits
    assets/next-id-{dark,light}.svg          the hanging lanyard badge
    assets/next-ops-{dark,light}.svg         the 24h automation schedule
    assets/next-connect-{dark,light}.svg     social cards

Rules the output follows (GitHub renders these inside <img>):

  * self-contained — portrait is inlined base64, no external assets, no JS
  * CSS only for motion, so `prefers-reduced-motion` actually disables it
  * every theme colour is resolved here, never at runtime

The repo's automation owns README marker blocks and the .github/ workflows;
this builder touches neither.

Run:  python3 build_next.py
"""

from __future__ import annotations

import base64
import math
import random
from html import escape as esc
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
PORTRAIT = ASSETS / "next-portrait.jpg"

SANS = "'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',ui-monospace,'SFMono-Regular',Consolas,'Liberation Mono',monospace"

PALETTES: Dict[str, Dict[str, object]] = {
    "dark": {
        "bg0": "#05080f",
        "bg1": "#080d1a",
        "card": "#0b1220",
        "card2": "#0e1729",
        "text": "#f4f7ff",
        "text2": "#c9d6ec",
        "muted": "#8b9dc2",
        "line": "#f4f7ff",
        "lineo": 0.10,
        "blue": "#247bff",
        "blue2": "#7fb2ff",
        "crimson": "#ff354f",
        "mint": "#34e5a1",
        "glow": 0.30,
        "dots": 0.20,
        "grid": 0.10,
        "photo_ring": "#1b2a45",
        "chip": "#0d1728",
        "metal0": "#dbe4f2",
        "metal1": "#7d8ca6",
        "foil": 0.16,
    },
    "light": {
        "bg0": "#f7f9ff",
        "bg1": "#eef3fd",
        "card": "#ffffff",
        "card2": "#f4f7ff",
        "text": "#070b16",
        "text2": "#24314a",
        "muted": "#5a6b8c",
        "line": "#070b16",
        "lineo": 0.12,
        "blue": "#0f62e6",
        "blue2": "#247bff",
        "crimson": "#d81f3a",
        "mint": "#0b9e6c",
        "glow": 0.16,
        "dots": 0.16,
        "grid": 0.07,
        "photo_ring": "#c9d6ec",
        "chip": "#eef3fd",
        "metal0": "#ffffff",
        "metal1": "#a9b6cc",
        "foil": 0.10,
    },
}

CSS = """
text{font-family:%(sans)s}
.mono{font-family:%(mono)s}
.e{opacity:0;animation:rise .9s cubic-bezier(.22,1,.36,1) forwards}
.b1{animation-delay:.06s}.b2{animation-delay:.16s}.b3{animation-delay:.26s}
.b4{animation-delay:.36s}.b5{animation-delay:.46s}.b6{animation-delay:.56s}
.b7{animation-delay:.68s}.b8{animation-delay:.80s}.b9{animation-delay:.92s}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes faded{from{opacity:0}to{opacity:1}}
@keyframes blink{0%%,48%%{opacity:1}50%%,100%%{opacity:0}}
@keyframes roles{0%%{opacity:0;transform:translateY(7px)}3%%{opacity:1;transform:none}22%%{opacity:1;transform:none}25%%{opacity:0;transform:translateY(-7px)}100%%{opacity:0}}
@keyframes slide{0%%{opacity:0;transform:translateY(10px)}3%%{opacity:1;transform:none}30%%{opacity:1;transform:none}33.3%%{opacity:0;transform:translateY(-9px)}100%%{opacity:0}}
@keyframes barA{0%%{transform:scaleX(0)}33%%{transform:scaleX(1)}100%%{transform:scaleX(1)}}
@keyframes barB{0%%{transform:scaleX(0)}33%%{transform:scaleX(0)}66%%{transform:scaleX(1)}100%%{transform:scaleX(1)}}
@keyframes barC{0%%{transform:scaleX(0)}66%%{transform:scaleX(0)}99%%{transform:scaleX(1)}100%%{transform:scaleX(1)}}
@keyframes dashes{to{stroke-dashoffset:-420}}
@keyframes float{0%%,100%%{transform:translateY(0)}50%%{transform:translateY(-7px)}}
@keyframes pulse{0%%,100%%{opacity:.35;transform:scale(.85)}50%%{opacity:1;transform:scale(1)}}
@keyframes sway{0%%,100%%{transform:rotate(-1.7deg)}50%%{transform:rotate(1.7deg)}}
@keyframes foil{0%%{transform:translateX(-160px)}55%%,100%%{transform:translateX(520px)}}
@keyframes nudge{0%%,100%%{transform:translateX(0)}50%%{transform:translateX(5px)}}
.barA{transform-box:fill-box;transform-origin:left center;animation:barA 12s linear infinite}
.barB{transform-box:fill-box;transform-origin:left center;animation:barB 12s linear infinite}
.barC{transform-box:fill-box;transform-origin:left center;animation:barC 12s linear infinite}
.slide{opacity:0;animation:slide 12s linear infinite}
.role{opacity:0;animation:roles 12s linear infinite}
.dash{animation:dashes 26s linear infinite}
.dash.fast{animation-duration:17s;animation-direction:reverse}
.fl{animation:float 7s ease-in-out infinite}
.fl.f2{animation-delay:-2.2s}.fl.f3{animation-delay:-4.1s}.fl.f4{animation-delay:-5.6s}
.dotp{animation:pulse 2.8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.swing{transform-origin:380px 118px;animation:sway 7.5s ease-in-out infinite}
.foil{animation:foil 7s ease-in-out infinite}
.arrow{animation:nudge 2.4s ease-in-out infinite}
@media (prefers-reduced-motion: reduce){
      .e,.slide,.role,.dash,.fl,.dotp,.swing,.foil,.arrow{animation:none!important}
  .e,.slide,.role{opacity:1!important;transform:none!important}
  .barA,.barB,.barC{animation:none!important;transform:scaleX(1)}
}
""" % {"sans": SANS, "mono": MONO}


# ---------------------------------------------------------------------------
# tiny element helpers
# ---------------------------------------------------------------------------

def txt(
    x: float,
    y: float,
    s: str,
    size: float = 13,
    fill: Optional[str] = None,
    weight: int = 400,
    anchor: str = "start",
    ls: float = 0,
    mono: bool = False,
    cls: str = "",
    opacity: Optional[float] = None,
    italic: bool = False,
    style: str = "",
) -> str:
    a = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight != 400:
        a.append(f'font-weight="{weight}"')
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls}"')
    if mono:
        a.append(f'font-family="{MONO}"')
    if italic:
        a.append('font-style="italic"')
    if opacity is not None:
        a.append(f'opacity="{opacity}"')
    if cls:
        a.append(f'class="{cls}"')
    if style:
        a.append(f'style="{style}"')
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def rect(x, y, w, h, fill="none", stroke=None, op=1.0, rx=0, sw=1, cls="", extra=""):
    a = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
    if rx:
        a.append(f'rx="{rx}"')
    a.append(f'fill="{fill}"')
    if stroke:
        a.append(f'stroke="{stroke}"')
        a.append(f'stroke-width="{sw}"')
    if op != 1.0:
        a.append(f'fill-opacity="{op}"')
    if cls:
        a.append(f'class="{cls}"')
    if extra:
        a.append(extra)
    return f'<rect {" ".join(a)}/>'


def rule(x1, x2, y, p, op=None):
    o = p["lineo"] if op is None else op
    return (
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
        f'stroke="{p["line"]}" stroke-opacity="{o}" stroke-width="1"/>'
    )


def pill(x, y, w, h, label, p, fg=None, bg=None, border=None, size=10.5, ls=1.3, cls=""):
    fg = fg or p["text2"]
    bg = bg or p["chip"]
    border = border or p["line"]
    return (
        f'<g class="{cls}">'
        + rect(x, y, w, h, fill=bg, stroke=border, sw=1, op=1, rx=h / 2, extra=f'stroke-opacity="{p["lineo"]}"')
        + txt(x + w / 2, y + h / 2 + size * 0.36, label, size, fg, 700, "middle", ls, mono=True)
        + "</g>"
    )


def corner(x, y, p, s=7, op=0.35):
    return (
        f'<path d="M{x - s} {y}H{x + s}M{x} {y - s}V{y + s}" stroke="{p["muted"]}" '
        f'stroke-opacity="{op}" stroke-width="1"/>'
    )


def barcode(x, y, w, h, p, seed=11):
    rnd = random.Random(seed)
    bars: List[str] = []
    cx = x
    while cx < x + w - 2:
        bw = rnd.choice([1, 1, 2, 3])
        gap = rnd.choice([2, 3, 4])
        if cx + bw > x + w:
            break
        bars.append(f'<rect x="{cx}" y="{y}" width="{bw}" height="{h}"/>')
        cx += bw + gap
    return f'<g fill="{p["text"]}" opacity=".78">{"".join(bars)}</g>'


def photo_data_uri() -> str:
    raw = PORTRAIT.read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


# ---------------------------------------------------------------------------
# shared chrome
# ---------------------------------------------------------------------------

def shell(p, w, h, defs: str = "", body: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<title>Manashjyoti Bora — profile artwork</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{p['bg0']}"/>
  <stop offset="1" stop-color="{p['bg1']}"/>
</linearGradient>
<radialGradient id="glowA" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="{p['blue']}" stop-opacity="{p['glow']}"/>
  <stop offset="1" stop-color="{p['blue']}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowB" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="{p['crimson']}" stop-opacity="{float(p['glow']) * 0.8}"/>
  <stop offset="1" stop-color="{p['crimson']}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="hair" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['blue']}" stop-opacity="0"/>
  <stop offset=".25" stop-color="{p['blue']}" stop-opacity=".9"/>
  <stop offset=".72" stop-color="{p['crimson']}" stop-opacity=".9"/>
  <stop offset="1" stop-color="{p['crimson']}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['text']}"/>
  <stop offset=".55" stop-color="{p['text']}"/>
  <stop offset="1" stop-color="{p['blue2']}"/>
</linearGradient>
<linearGradient id="crimGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['crimson']}"/>
  <stop offset="1" stop-color="{p['blue']}"/>
</linearGradient>
<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
  <circle cx="1.4" cy="1.4" r="1.3" fill="{p['muted']}" opacity="{p['dots']}"/>
</pattern>
<pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse">
  <path d="M22 0H0V22" fill="none" stroke="{p['line']}" stroke-opacity="{p['grid']}" stroke-width=".8"/>
</pattern>
{defs}
</defs>
<style>{CSS}</style>
<rect width="{w}" height="{h}" rx="28" fill="url(#bg)"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="27.5" fill="none" stroke="{p['line']}" stroke-opacity="{float(p['lineo']) + .04}"/>
{body}
</svg>
"""


def section_head(p, kicker: str, right: str, y=72, right_fill=None):
    return "".join(
        [
            txt(64, y, kicker, 11, p["blue"], 700, ls=2.6, mono=True, cls="e b1"),
            txt(1116, y, right, 10.5, right_fill or p["muted"], 500, "end", ls=2.2, mono=True, cls="e b1"),
            rule(64, 1116, y + 20, p),
        ]
    )


# ---------------------------------------------------------------------------
# 1 · HERO
# ---------------------------------------------------------------------------

def build_hero(p) -> str:
    w, h = 1180, 620
    roles = [
        "FULL-STACK DEVELOPER",
        "SVG + SMIL CRAFT",
        "AUTOMATION TINKERER",
        "IT STUDENT · B.VOC",
    ]
    role_svg = []
    for i, r in enumerate(roles):
        role_svg.append(
            txt(132, 422, r, 19, p["blue2"], 700, ls=0.8, mono=True,
                cls="role", style=f"animation-delay:{i * 3}s")
        )

    chips = [
        ("ANDROID-FIRST DEV", 136),
        ("2 APPS IN PRODUCTION", 160),
        ("7 PIPELINES · 24/7", 148),
    ]
    cx = 64
    chip_svg = []
    for label, cw in chips:
        chip_svg.append(pill(cx, 470, cw, 34, label, p, size=10, ls=1.1))
        cx += cw + 10

    defs = f"""
<clipPath id="hclip"><rect x="0" y="0" width="{w}" height="{h}" rx="28"/></clipPath>
<clipPath id="roleclip"><rect x="120" y="396" width="520" height="34"/></clipPath>
"""
    body = f"""
<g clip-path="url(#hclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".9"/>
  <ellipse cx="120" cy="640" rx="620" ry="360" fill="url(#glowA)"/>
  <ellipse cx="1060" cy="20" rx="380" ry="300" fill="url(#glowB)"/>
</g>

{txt(64, 88, "NAGAON, ASSAM — 26.35°N · 92.68°E", 11, p["muted"], 600, ls=2.4, mono=True, cls="e b1")}
<g class="e b1"><circle cx="655" cy="84" r="3.5" fill="{p["mint"]}" class="dotp"/><circle cx="655" cy="84" r="8" fill="none" stroke="{p["mint"]}" stroke-opacity=".35"/></g>
{txt(1116, 88, "PROFILE / 2026", 10.5, p["muted"], 500, "end", ls=2.4, mono=True, cls="e b1")}
{rule(64, 1116, 110, p)}

<g class="e b2">{txt(62, 222, "MANASHJYOTI", 92, "url(#nameGrad)", 800, ls=-3.2)}</g>
<g class="e b3">{txt(62, 314, "BORA", 92, p["text"], 800, ls=-1)}</g>
<g class="e b4">
  {rect(368, 296, 46, 2, fill="url(#crimGrad)")}
  {txt(432, 288, "BUILDING", 10.5, p["muted"], 600, ls=2.4, mono=True)}
  {txt(432, 306, "IN PUBLIC", 10.5, p["blue2"], 600, ls=2.4, mono=True)}
</g>

<g class="e b4">
  {txt(64, 372, ">", 15, p["crimson"], 700, mono=True)}
  {txt(86, 372, "shipping full-stack products from an Android phone", 15, p["text2"], 500, mono=True)}
  {rect(582, 358, 9, 17, fill=p["blue"])}
</g>

<g class="e b5" clip-path="url(#roleclip)">
  {txt(64, 422, "ROLE", 10, p["muted"], 600, ls=2.4, mono=True)}
  {rule(112, 112, 396, p, .18)}
  {''.join(role_svg)}
</g>

<g class="e b6">{''.join(chip_svg)}</g>

{rule(64, 1116, 536, p)}
<g class="e b7">
  {txt(64, 574, "SCROLL · THE BUILD LOG", 10, p["muted"], 600, ls=2.6, mono=True)}
  {txt(1116, 574, "/ MANASHJYOTI-BORA", 10, p["muted"], 600, "end", 2.6, mono=True)}
</g>

<g class="e b3">
  <line x1="792" y1="150" x2="792" y2="500" stroke="{p["line"]}" stroke-opacity="{p['lineo']}"/>
  {corner(792, 150, p)} {corner(792, 500, p)}
</g>

<g class="e b4">
  <ellipse class="dash" cx="944" cy="316" rx="196" ry="86" transform="rotate(-20 944 316)"
    fill="none" stroke="{p['blue']}" stroke-opacity=".45" stroke-width="1.2" stroke-dasharray="3 9"/>
  <ellipse class="dash fast" cx="944" cy="316" rx="168" ry="168"
    fill="none" stroke="{p['line']}" stroke-opacity="{float(p['lineo']) + .06}" stroke-width="1" stroke-dasharray="2 10"/>
  <ellipse class="dash" cx="944" cy="316" rx="226" ry="104" transform="rotate(26 944 316)"
    fill="none" stroke="{p['crimson']}" stroke-opacity=".34" stroke-width="1" stroke-dasharray="14 12"/>
  <circle cx="944" cy="316" r="104" fill="url(#glowA)" opacity=".6"/>
  <rect x="874" y="246" width="140" height="140" rx="40" fill="{p['card']}" stroke="url(#hair)" stroke-width="1.4"/>
  <rect x="886" y="258" width="116" height="116" rx="32" fill="none" stroke="{p['line']}" stroke-opacity="{p['lineo']}"/>
  {txt(944, 320, "MB", 54, p["text"], 800, "middle", ls=-1.5)}
  {txt(944, 348, "EST. 2025", 8.5, p["muted"], 600, "middle", 2.4, mono=True)}
</g>

<g class="e b6 fl">
  {pill(806, 138, 104, 30, "NEXT.JS", p, fg=p["blue2"], bg=p["card"], size=10)}
</g>
<g class="e b6 fl f2">
  {pill(1060, 196, 84, 30, "NODE", p, fg=p["text2"], bg=p["card"], size=10)}
</g>
<g class="e b7 fl f3">
  {pill(806, 452, 96, 30, "MONGO", p, fg=p["text2"], bg=p["card"], size=10)}
</g>
<g class="e b7 fl f4">
  {pill(1052, 430, 100, 30, "SVG+SMIL", p, fg=p["crimson"], bg=p["card"], size=10)}
</g>

<g class="e b8">
  {txt(944, 486, "CORE / 01", 8.5, p["muted"], 600, "middle", 2.4, mono=True)}
  {corner(1116, 138, p, 6, .4)}
</g>
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# 2 · ABOUT / OPERATOR
# ---------------------------------------------------------------------------

def build_about(p) -> str:
    w, h = 1180, 480
    rows = [
        ("01", "FRONTEND SYSTEMS", "React 19 · Next.js · Vite · responsive UI"),
        ("02", "BACKEND & DATA", "Node · REST · JWT · Zod · MongoDB Atlas"),
        ("03", "CRAFT & OPS", "Hand-typed SVG/SMIL · GitHub Actions · Vercel"),
    ]
    row_svg = []
    for i, (n, title, desc) in enumerate(rows):
        y = 292 + i * 56
        row_svg.append(
            rule(64, 636, y, p, .08)
            + txt(64, y + 24, n, 10.5, p["blue"], 700, ls=1.8, mono=True)
            + txt(112, y + 24, title, 14.5, p["text"], 700, ls=1.1)
            + txt(112, y + 43, desc, 11.5, p["muted"], 400, ls=.2)
        )

    slides = [
        ("CRAFT / 01", ["Zero-JS", "animation."],
         "Fourteen SVG files, hand-typed.", "CSS + SMIL only — GitHub renders", "every frame, no libraries."),
        ("SHIP / 02", ["Production,", "from a phone."],
         "Termux → GitHub → Vercel.", "Auth, cart and checkout are live", "in the wild right now."),
        ("HABIT / 03", ["Seven robots", "work here."],
         "Daily snapshot, telemetry, sheets,", "snake, Pac-Man, 3D city, signatures.", "All conflict-safe, all automatic."),
    ]
    slide_svg = []
    for i, (kicker, head, l1, l2, l3) in enumerate(slides):
        slide_svg.append(
            f'<g class="slide" style="animation-delay:{i * 4}s">'
            + txt(1010, 214, f"0{i + 1}", 92, p["text"], 800, "end", -2, opacity=.055)
            + txt(712, 152, kicker, 9.5, p["blue"], 700, ls=2.4, mono=True)
            + txt(712, 202, head[0], 27, p["text"], 800, ls=-.6)
            + txt(712, 234, head[1], 27, p["text"], 800, ls=-.6)
            + txt(712, 268, l1, 11.5, p["text2"], 400)
            + txt(712, 286, l2, 11.5, p["muted"], 400)
            + txt(712, 304, l3, 11.5, p["muted"], 400)
            + "</g>"
        )

    defs = '<clipPath id="aclip"><rect x="0" y="0" width="1180" height="480" rx="28"/></clipPath>'
    body = f"""
<g clip-path="url(#aclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".5"/>
  <ellipse cx="1120" cy="470" rx="420" ry="300" fill="url(#glowA)" opacity=".55"/>
</g>
{section_head(p, "01 / THE OPERATOR", "WHAT I ACTUALLY DO")}

<g class="e b2">{txt(64, 166, "One phone.", 44, p["text"], 800, ls=-1.4)}</g>
<g class="e b3">{txt(64, 214, "Two production apps.", 44, "url(#nameGrad)", 800, ls=-1.4)}</g>
<g class="e b4">{txt(64, 252, "The laptop was never the point. The constraint became the brand.", 12.5, p["muted"], 400, mono=True)}</g>

{''.join(row_svg)}

<g class="e b3">
  <rect x="676" y="104" width="440" height="330" rx="22" fill="{p['card']}" stroke="{p['line']}" stroke-opacity="{float(p['lineo']) + .03}"/>
  <rect x="676" y="104" width="440" height="330" rx="22" fill="url(#grid)" opacity=".5"/>
  <path d="M676 104H760" stroke="url(#hair)" stroke-width="2"/>
</g>

{''.join(slide_svg)}

<g class="e b6">
  {rule(712, 1080, 340, p, .10)}
  {rect(712, 366, 118, 3, fill=p["line"], op=.10, rx=1.5)}
  {rect(840, 366, 118, 3, fill=p["line"], op=.10, rx=1.5)}
  {rect(968, 366, 118, 3, fill=p["line"], op=.10, rx=1.5)}
  {rect(712, 366, 118, 3, fill=p["blue"], rx=1.5, cls="barA")}
  {rect(840, 366, 118, 3, fill=p["blue"], rx=1.5, cls="barB")}
  {rect(968, 366, 118, 3, fill=p["blue"], rx=1.5, cls="barC")}
  {txt(712, 400, "AUTOPLAY · 4S PER SLIDE · CSS ONLY", 8.5, p["muted"], 600, ls=2, mono=True)}
  {txt(1080, 400, "01 — 03", 8.5, p["muted"], 600, "end", 2, mono=True)}
</g>

<g class="e b8">
  {txt(676, 462, "ANDROID-BUILT · ZERO JS", 8.5, p["muted"], 600, ls=2, mono=True)}
  {txt(1116, 462, "BUILD_NEXT.PY", 8.5, p["muted"], 600, "end", 2, mono=True)}
</g>
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# 3 · STACK ORBITS
# ---------------------------------------------------------------------------

def _on_ellipse(cx, cy, rx, ry, tilt_deg, angle_deg) -> Tuple[float, float]:
    t = math.radians(tilt_deg)
    a = math.radians(angle_deg)
    x = rx * math.cos(a)
    y = ry * math.sin(a)
    return (cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t))


def build_stack(p) -> str:
    w, h = 1180, 520
    cx, cy = 720, 250
    rings = [
        dict(rx=150, ry=64, tilt=-24, color=p["blue"], op=.40, dash="3 8"),
        dict(rx=212, ry=88, tilt=16, color=p["crimson"], op=.32, dash="12 10"),
        dict(rx=290, ry=118, tilt=0, color=p["muted"], op=.24, dash="2 9"),
    ]
    # Satellites sit exactly on the outer orbit, spaced so none of them can
    # collide with the monogram, the headline or the group cards.
    labels = [
        (0, "NODE.JS", 86, p["blue"]),
        (40, "MONGODB", 94, p["crimson"]),
        (90, "GITHUB ACTIONS", 118, p["mint"]),
        (140, "REACT", 74, p["blue"]),
        (220, "NEXT.JS", 86, p["blue"]),
        (270, "TYPESCRIPT", 106, p["crimson"]),
        (320, "PYTHON", 78, p["mint"]),
    ]
    edge = 'stroke-opacity=".45"'
    ring_svg, label_svg = [], []
    for ring in rings:
        ring_svg.append(
            f'<ellipse class="dash{" fast" if ring["tilt"] > 0 else ""}" cx="{cx}" cy="{cy}" '
            f'rx="{ring["rx"]}" ry="{ring["ry"]}" transform="rotate({ring["tilt"]} {cx} {cy})" '
            f'fill="none" stroke="{ring["color"]}" stroke-opacity="{ring["op"]}" '
            f'stroke-width="1.1" stroke-dasharray="{ring["dash"]}"/>'
        )
    for angle, label, pw, accent in labels:
        x, y = _on_ellipse(cx, cy, 290, 118, 0, angle)
        label_svg.append(
            f'<g class="e b6">'
            f'{rect(x - pw / 2, y - 12, pw, 24, fill=p["card"], stroke=accent, sw=1, rx=12, extra=edge)}'
            f'{txt(x, y + 4, label, 10.5, p["text2"], 600, "middle", .4)}'
            f'</g>'
        )

    groups = [
        ("FRONTEND", "HTML · CSS · JS · React · Next.js · Tailwind · Vite", p["blue"]),
        ("BACKEND & DATA", "Node · Express · REST · JWT · Zod · MongoDB", p["crimson"]),
        ("CRAFT & OPS", "SVG + SMIL · Actions · Git · Linux · Vercel · npm", p["mint"]),
    ]
    card_svg = []
    for i, (title, list_, accent) in enumerate(groups):
        x = 64 + i * 360
        card_svg.append(
            rect(x, 392, 332, 92, fill=p["card"], stroke=p["line"], sw=1, rx=18,
                 extra=f'stroke-opacity="{p["lineo"]}"')
            + rect(x, 392, 44, 3, fill=accent, rx=1.5)
            + txt(x + 24, 424, title, 9.5, accent, 700, ls=2.2, mono=True)
            + txt(x + 24, 448, list_, 10.2, p["text2"], 500, ls=.1, mono=True)
        )

    defs = '<clipPath id="sclip"><rect width="1180" height="520" rx="28"/></clipPath>'
    body = f"""
<g clip-path="url(#sclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".45"/>
  <ellipse cx="720" cy="250" rx="420" ry="280" fill="url(#glowA)" opacity=".45"/>
</g>
{section_head(p, "02 / THE STACK", "WHAT I REACH FOR")}

<g class="e b2">{txt(64, 178, "Tools are", 38, p["text"], 800, ls=-1.2)}</g>
<g class="e b2">{txt(64, 220, "borrowed.", 38, "url(#nameGrad)", 800, ls=-1.2)}</g>
<g class="e b3">{txt(64, 258, "Habits compound.", 38, p["text"], 800, ls=-1.2)}</g>
<g class="e b4">{txt(64, 296, "No bootcamp. No laptop. Six months", 11.5, p["muted"], 400, mono=True)}</g>
<g class="e b4">{txt(64, 314, "of shipping, one commit at a time.", 11.5, p["muted"], 400, mono=True)}</g>

<circle cx="{cx}" cy="{cy}" r="120" fill="url(#glowB)" opacity=".7"/>
{''.join(ring_svg)}
<g class="e b4">
  <rect x="{cx - 58}" y="{cy - 58}" width="116" height="116" rx="34" fill="{p['card']}" stroke="url(#hair)" stroke-width="1.3"/>
  {txt(cx, cy - 4, "MB", 34, p["text"], 800, "middle", -1)}
  {txt(cx, cy + 22, "CORE", 8, p["muted"], 600, "middle", 2.2, mono=True)}
  <circle cx="{cx}" cy="{cy - 58}" r="3.2" fill="{p['blue']}"/>
</g>
{''.join(label_svg)}
{''.join(card_svg)}
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# 4 · IDENTITY LANYARD
# ---------------------------------------------------------------------------

def build_identity(p) -> str:
    w, h = 1180, 700
    data = [
        ("NAME", "Manashjyoti Bora"),
        ("ROLE", "Full-stack developer · IT student"),
        ("BASE", "Nagaon, Assam · 26.35°N 92.68°E"),
        ("SINCE", "2025 · first line of code"),
        ("STATUS", "Building, daily"),
        ("VERIFIED", "GitHub API · auto-refreshed"),
    ]
    rows = []
    for i, (k, v) in enumerate(data):
        y = 286 + i * 52
        rows.append(
            rule(660, 1116, y - 20, p, .08)
            + txt(660, y, k, 9.5, p["muted"], 700, ls=2.2, mono=True)
            + txt(820, y, v, 14, p["text"] if i in (0, 1) else p["text2"], 600 if i in (0, 1) else 400)
        )

    stripe = "".join(
        f'<path d="M{300 + i * 18} 0 L{318 + i * 18} 0 L{300 + i * 18} 118 L{282 + i * 18} 118Z" '
        f'fill="{p["crimson"] if i % 3 == 1 else "none"}" fill-opacity=".18"/>'
        for i in range(7)
    )

    defs = f"""
<clipPath id="piclip"><rect width="1180" height="700" rx="28"/></clipPath>
<clipPath id="cardclip"><rect x="200" y="160" width="360" height="500" rx="26"/></clipPath>
<clipPath id="photoclip"><rect x="224" y="184" width="312" height="300" rx="18"/></clipPath>
<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{p['metal0']}"/>
  <stop offset=".5" stop-color="{p['metal1']}"/>
  <stop offset="1" stop-color="{p['metal0']}"/>
</linearGradient>
<linearGradient id="strape" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['card2']}"/>
  <stop offset=".5" stop-color="{p['photo_ring']}"/>
  <stop offset="1" stop-color="{p['card2']}"/>
</linearGradient>
<linearGradient id="foilgrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['text']}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{p['text']}" stop-opacity="{p['foil']}"/>
  <stop offset="1" stop-color="{p['text']}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{p['bg0']}" stop-opacity="1"/>
  <stop offset="1" stop-color="{p['bg0']}" stop-opacity="0"/>
</linearGradient>
<mask id="strapmask"><rect width="1180" height="150" fill="url(#fadeTop)"/></mask>
"""
    photo = photo_data_uri()
    body = f"""
<g clip-path="url(#piclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".4"/>
  <ellipse cx="380" cy="700" rx="480" ry="360" fill="url(#glowA)" opacity=".5"/>
  <ellipse cx="1050" cy="60" rx="360" ry="260" fill="url(#glowB)" opacity=".55"/>
</g>
{section_head(p, "03 / IDENTITY", "BADGE NO. MJB-2026", right_fill=p["muted"])}

<g mask="url(#strapmask)">{stripe}
  <rect x="336" y="0" width="88" height="150" fill="url(#strape)" opacity=".9"/>
  <rect x="348" y="0" width="2" height="150" fill="{p['text']}" opacity=".10"/>
  <rect x="410" y="0" width="2" height="150" fill="{p['text']}" opacity=".10"/>
</g>

<g class="swing">
  <rect x="352" y="112" width="56" height="46" rx="10" fill="url(#metal)" stroke="{p['line']}" stroke-opacity=".25"/>
  <rect x="366" y="132" width="28" height="12" rx="6" fill="{p['bg0']}" opacity=".65"/>
  <circle cx="380" cy="158" r="5" fill="{p['bg0']}" opacity=".55"/>

  <rect x="200" y="160" width="360" height="500" rx="26" fill="{p['card']}" stroke="{p['line']}" stroke-opacity="{float(p['lineo']) + .05}"/>
  <rect x="200" y="160" width="360" height="500" rx="26" fill="url(#grid)" opacity=".35"/>
  <image x="224" y="184" width="312" height="300" preserveAspectRatio="xMidYMid slice"
    clip-path="url(#photoclip)" href="{photo}" xlink:href="{photo}"/>
  <rect x="224" y="184" width="312" height="300" rx="18" fill="none" stroke="{p['line']}" stroke-opacity=".18"/>
  <rect x="224" y="440" width="312" height="44" fill="url(#fadeTop)" opacity=".0"/>

  <g clip-path="url(#cardclip)">
    <g class="foil"><rect x="-160" y="120" width="90" height="560" fill="url(#foilgrad)" transform="rotate(16 380 400)"/></g>
  </g>

  {txt(224, 522, "MANASHJYOTI", 21, p["text"], 800, ls=-.4)}
  {txt(224, 548, "BORA", 21, p["text"], 800, ls=-.4)}
  {txt(556, 522, "FULL-STACK", 8.5, p["blue"], 700, "end", 1.8, mono=True)}
  {txt(556, 538, "DEVELOPER", 8.5, p["muted"], 600, "end", 1.8, mono=True)}
  {txt(556, 554, "IT · B.VOC", 8.5, p["muted"], 600, "end", 1.8, mono=True)}
  {rule(224, 556, 566, p, .12)}
  {barcode(224, 582, 240, 34, p)}
  {txt(556, 616, "MJB-2026-INF", 8.5, p["muted"], 600, "end", 1.6, mono=True)}
  {txt(224, 640, "NAGAON · ASSAM · IN", 8.5, p["muted"], 600, ls=1.6, mono=True)}
</g>

<g class="e b2">{txt(660, 172, "The badge", 40, p["text"], 800, ls=-1.2)}</g>
<g class="e b2">{txt(660, 216, "is the proof.", 40, "url(#nameGrad)", 800, ls=-1.2)}</g>
<g class="e b3">{txt(660, 250, "No titles I haven't earned. Every line points at live work.", 11.5, p["muted"], 400, mono=True)}</g>
{''.join(f'<g class="e b4">{r}</g>' for r in rows)}
<g class="e b8">
  {rect(660, 616, 46, 2, fill="url(#crimGrad)")}
  {txt(660, 652, "The constraint was never a wall —", 13, p["muted"], 500, italic=True)}
  {txt(660, 674, "it became the brand.", 13, p["text2"], 600, italic=True)}
</g>
{corner(1116, 286, p, 6, .35)}
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# 5 · THE MACHINE / OPS TIMELINE
# ---------------------------------------------------------------------------

def build_ops(p) -> str:
    """A 24-hour map of the real cron schedule, read from .github/workflows.

    Nothing here is invented: the seven rows are the seven workflows, the
    strip below counts how many scheduled runs land in each UTC hour
    (00:05, 00:10, 00:17, 00:41, 02:30, 03:00, 06:17, 06:41, 12:17, 12:41,
    18:17, 18:41 — 14 runs a day).
    """
    w, h = 1180, 520
    rows = [
        ("00:05", "SNAKE", "daily · output branch", p["mint"]),
        ("00:10", "PAC-MAN", "daily · output branch", p["crimson"]),
        ("00:17", "LIVE TELEMETRY", "every 6h · terminal card", p["blue2"]),
        ("00:41", "BLUEPRINT SHEETS", "every 6h · drawing sheet", p["blue"]),
        ("02:30", "DAILY SELF-UPDATE", "daily · README markers", p["blue"]),
        ("03:00", "3D CITY", "daily · skyline SVG", p["mint"]),
        ("12:17", "SIGNATURE MARGIN", "every 12h · plus issues", p["crimson"]),
    ]
    row_svg = []
    for i, (t, name, cad, accent) in enumerate(rows):
        y = 152 + i * 33
        row_svg.append(
            rule(600, 1116, y - 20, p, .07)
            + f'<circle cx="600" cy="{y - 4}" r="3" fill="{accent}" class="dotp" style="animation-delay:-{i * 0.42:.2f}s"/>'
            + txt(616, y, t, 11, accent, 700, mono=True)
            + txt(676, y, name, 12.5, p["text2"], 600, ls=.9)
            + txt(1116, y, cad, 9.5, p["muted"], 500, "end", ls=.7, mono=True)
        )

    # Runs per UTC hour, straight from the cron lines in .github/workflows.
    hours = [5, 0, 1, 1, 0, 0, 2, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
    step = 1052 / 24
    cell_svg, axis_svg = [], []
    for i, n in enumerate(hours):
        x = 64 + i * step
        cell_svg.append(
            rect(x, 434, step - 5.5, 30, fill=p["blue"] if n else p["line"],
                 op=0.06 + min(n, 5) * 0.11, rx=4)
        )
        if n:
            cell_svg.append(txt(x + (step - 5.5) / 2, 428, str(n), 8, p["muted"], 600, "middle", mono=True))
    for hr in (0, 6, 12, 18, 24):
        x = 64 + hr * step
        anchor = "start" if hr == 0 else ("end" if hr == 24 else "middle")
        axis_svg.append(txt(x, 484, f"{hr:02d}", 8.5, p["muted"], 600, anchor, 1.4, mono=True))

    defs = '<clipPath id="oclip"><rect width="1180" height="520" rx="28"/></clipPath>'
    body = f"""
<g clip-path="url(#oclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".45"/>
  <ellipse cx="1110" cy="490" rx="420" ry="300" fill="url(#glowA)" opacity=".5"/>
  <ellipse cx="70" cy="10" rx="320" ry="240" fill="url(#glowB)" opacity=".45"/>
</g>
{section_head(p, "04 / THE MACHINE", "SCHEDULED IN UTC")}

<g class="e b2">{txt(64, 170, "While I sleep,", 40, p["text"], 800, ls=-1.3)}</g>
<g class="e b2">{txt(64, 214, "seven robots ship.", 40, "url(#nameGrad)", 800, ls=-1.3)}</g>
<g class="e b3">
  {txt(64, 252, "Fourteen scheduled runs a day — every one", 11.5, p["muted"], 400, mono=True)}
  {txt(64, 270, "of them writes real data. None need me.", 11.5, p["muted"], 400, mono=True)}
</g>
<g class="e b5">{pill(64, 296, 176, 30, "CONFLICT-SAFE BY DESIGN", p, size=9, ls=1.2)}</g>

<g class="e b4">
  {txt(64, 366, "07", 30, p["text"], 800, ls=-1)}
  {txt(64, 386, "PIPELINES", 8.5, p["muted"], 600, ls=2, mono=True)}
  {txt(212, 366, "14", 30, p["blue2"], 800, ls=-1)}
  {txt(212, 386, "RUNS / DAY", 8.5, p["muted"], 600, ls=2, mono=True)}
  {txt(360, 366, "00", 30, p["crimson"], 800, ls=-1)}
  {txt(360, 386, "HANDS", 8.5, p["muted"], 600, ls=2, mono=True)}
</g>

{''.join(row_svg)}

<g class="e b6">
  {txt(64, 412, "SCHEDULE MAP · RUNS PER HOUR", 8.5, p["muted"], 600, ls=2, mono=True)}
  {txt(1116, 412, "UTC · 24H", 8.5, p["muted"], 600, "end", ls=2, mono=True)}
</g>
{''.join(cell_svg)}
<g class="e b7">{''.join(axis_svg)}</g>
<g class="e b8">
  {txt(64, 506, "CRON IN UTC · CONCURRENCY GROUPS SERIALISE EACH FAMILY · PUSH-SAFE.SH RETRIES ×5", 8, p["muted"], 600, ls=1.3, mono=True)}
</g>
{corner(1116, 152, p, 6, .35)}
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# 6 · CONNECT
# ---------------------------------------------------------------------------

def build_connect(p) -> str:
    w, h = 1180, 450
    cards = [
        ("GITHUB", "@Manashjyoti-Bora", "code"),
        ("LINKEDIN", "manashjyoti-bora", "linkedin"),
        ("PORTFOLIO", "portfolio-manashjyoti-bora", "globe"),
        ("EMAIL", "manashjyotibora122", "mail"),
        ("RESUME", "PDF · one page, always fresh", "doc"),
        ("OPEN TO", "internships · freelance", "status"),
    ]

    def icon(kind, x, y):
        c = p["blue2"]
        if kind == "code":
            return (f'<path d="M{x + 10} {y + 4}L{x + 3} {y + 11}L{x + 10} {y + 18}M{x + 18} {y + 4}'
                    f'L{x + 25} {y + 11}L{x + 18} {y + 18}" fill="none" stroke="{c}" stroke-width="1.8" '
                    f'stroke-linecap="round" stroke-linejoin="round"/>')
        if kind == "linkedin":
            return (f'<rect x="{x + 3}" y="{y + 3}" width="22" height="22" rx="5" fill="none" stroke="{c}" stroke-width="1.6"/>'
                    f'{txt(x + 14, y + 21, "in", 10, c, 700, "middle", mono=True)}')
        if kind == "globe":
            return (f'<circle cx="{x + 14}" cy="{y + 13}" r="10" fill="none" stroke="{c}" stroke-width="1.5"/>'
                    f'<path d="M{x + 4} {y + 13}H{x + 24}M{x + 14} {y + 3}C{x + 22} {y + 11} {x + 22} {y + 15} {x + 14} {y + 23}'
                    f'M{x + 14} {y + 3}C{x + 6} {y + 11} {x + 6} {y + 15} {x + 14} {y + 23}" '
                    f'fill="none" stroke="{c}" stroke-width="1.2" opacity=".8"/>')
        if kind == "mail":
            return (f'<rect x="{x + 3}" y="{y + 6}" width="22" height="16" rx="3" fill="none" stroke="{c}" stroke-width="1.6"/>'
                    f'<path d="M{x + 4} {y + 8}L{x + 14} {y + 16}L{x + 24} {y + 8}" fill="none" stroke="{c}" stroke-width="1.6"/>')
        if kind == "doc":
            return (f'<path d="M{x + 7} {y + 3}H{x + 18}L{x + 23} {y + 8}V{y + 23}H{x + 7}Z" fill="none" stroke="{c}" stroke-width="1.5"/>'
                    f'<path d="M{x + 18} {y + 3}V{y + 8}H{x + 23}M{x + 11} {y + 13}H{x + 19}M{x + 11} {y + 17}H{x + 17}" '
                    f'fill="none" stroke="{c}" stroke-width="1.3"/>')
        return (f'<circle cx="{x + 14}" cy="{y + 13}" r="5" fill="{p["mint"]}" class="dotp"/>'
                f'<circle cx="{x + 14}" cy="{y + 13}" r="10" fill="none" stroke="{p["mint"]}" stroke-opacity=".35"/>')

    tiles = []
    for i, (label, handle, kind) in enumerate(cards):
        col, row = i % 2, i // 2
        x = 600 + col * 260
        y = 120 + row * 90
        tiles.append(
            f'<g class="e b{4 + row}">'
            + rect(x, y, 246, 78, fill=p["card"], stroke=p["line"], sw=1, rx=16,
                   extra=f'stroke-opacity="{p["lineo"]}"')
            + icon(kind, x + 18, y + 24)
            + txt(x + 56, y + 34, label, 9.5, p["blue"], 700, ls=2.2, mono=True)
            + txt(x + 56, y + 55, handle, 10.5, p["text2"], 500, ls=.1, mono=True)
            + f'<g class="arrow">{txt(x + 220, y + 46, "→", 15, p["muted"], 400, "middle")}</g>'
            + "</g>"
        )

    defs = '<clipPath id="cclip"><rect width="1180" height="450" rx="28"/></clipPath>'
    body = f"""
<g clip-path="url(#cclip)">
  <rect width="{w}" height="{h}" fill="url(#dots)" opacity=".45"/>
  <ellipse cx="120" cy="450" rx="440" ry="300" fill="url(#glowA)" opacity=".55"/>
  <ellipse cx="1100" cy="30" rx="320" ry="220" fill="url(#glowB)" opacity=".5"/>
</g>
{section_head(p, "05 / CONNECT", "REPLIES WITHIN 24H")}

<g class="e b2">{txt(64, 190, "Let's build", 52, p["text"], 800, ls=-2)}</g>
<g class="e b3"><text x="64" y="248" font-size="52" font-weight="800" letter-spacing="-2" fill="{p['text']}">something <tspan fill="url(#crimGrad)">loud.</tspan></text></g>
<g class="e b4">
  {txt(64, 292, "Open to internships, freelance builds", 12, p["muted"], 400, mono=True)}
  {txt(64, 310, "and open-source with a real deadline.", 12, p["muted"], 400, mono=True)}
</g>
<g class="e b5">
  {rect(64, 344, 3, 22, fill=p["crimson"], rx=1.5)}
  {txt(80, 360, "manashjyotibora122@gmail.com", 12.5, p["text2"], 600, mono=True)}
</g>
<g class="e b6">
  {txt(64, 406, "THE WORK WILL DECIDE — BUT SAY HI FIRST.", 8.5, p["muted"], 600, ls=2, mono=True)}
</g>

{''.join(tiles)}
"""
    return shell(p, w, h, defs, body)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    builders = {
        "next-hero": build_hero,
        "next-about": build_about,
        "next-stack": build_stack,
        "next-id": build_identity,
        "next-ops": build_ops,
        "next-connect": build_connect,
    }
    total = 0
    for name, fn in builders.items():
        for theme, palette in PALETTES.items():
            svg = fn(palette)
            path = ASSETS / f"{name}-{theme}.svg"
            path.write_text(svg, encoding="utf-8")
            total += len(svg.encode("utf-8"))
            print(f"wrote {path.relative_to(ROOT)}  {len(svg.encode('utf-8')) // 1024} KB")
    print(f"total {total // 1024} KB across {len(builders) * 2} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
