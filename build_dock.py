#!/usr/bin/env python3
"""MJB.OS — dock tiles. Five clickable animated app icons, hand-coded SMIL."""
import os

C = dict(bg="#0b1220", bg2="#070d17", edge="#17293d", text="#e2e8f0", dim="#64748b",
         em="#10b981", cy="#22d3ee", vi="#8b5cf6", am="#f59e0b", rd="#f43f5e")
MONO = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"
W, H = 236, 132


def shell(title, meta, accent, viz, aria):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-label="{aria}">']
    s.append('<defs>')
    s.append(f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{accent}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{accent}"/>'
             f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient>')
    s.append(f'<linearGradient id="cardbg" x1="0" y1="0" x2=".7" y2="1">'
             f'<stop offset="0" stop-color="{C["bg"]}"/><stop offset="1" stop-color="{C["bg2"]}"/>'
             f'</linearGradient>')
    s.append(f'<radialGradient id="acch" cx=".85" cy="0" r="1">'
             f'<stop offset="0" stop-color="{accent}" stop-opacity=".22"/>'
             f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')
    s.append(f'<clipPath id="cvz"><rect x="14" y="58" width="{W-28}" height="46" rx="6"/></clipPath>')
    s.append('</defs>')
    s.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13" fill="url(#cardbg)" stroke="{C["edge"]}"/>')
    s.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13" fill="url(#acch)"/>')
    s.append(f'<rect x="14" y="0" width="{W-28}" height="2" fill="url(#acc)">'
             f'<animate attributeName="opacity" values=".35;1;.35" dur="3.4s" repeatCount="indefinite"/></rect>')
    s.append(f'<text x="16" y="28" font-family="{MONO}" font-size="13" font-weight="700" '
             f'fill="{C["text"]}" letter-spacing=".3">{title}</text>')
    s.append(f'<text x="16" y="46" font-family="{MONO}" font-size="9.5" fill="{C["dim"]}" '
             f'letter-spacing=".7">{meta}</text>')
    s.append(f'<g clip-path="url(#cvz)">{viz}</g>')
    s.append(f'<circle cx="20" cy="118" r="3" fill="{accent}">'
             f'<animate attributeName="opacity" values="1;.25;1" dur="2.2s" repeatCount="indefinite"/></circle>')
    s.append(f'<text x="30" y="121.5" font-family="{MONO}" font-size="9" fill="{C["dim"]}" '
             f'letter-spacing="1.1">LIVE</text>')
    s.append(f'<text x="{W-16}" y="121.5" text-anchor="end" font-family="{MONO}" font-size="9" '
             f'fill="{accent}" letter-spacing="1.1">OPEN -&gt;</text>')
    s.append('</svg>')
    return "".join(s)


# ── viz 1: portfolio — reveal bars + custom cursor ──────────────────────────
def viz_portfolio(a):
    o = [f'<rect x="14" y="58" width="{W-28}" height="46" fill="{a}" fill-opacity=".05"/>']
    for i in range(7):
        x = 24 + i * 26
        h = [10, 18, 26, 14, 30, 20, 12][i]
        o.append(f'<rect x="{x}" y="{100-h}" width="14" height="{h}" rx="3" fill="{a}" fill-opacity=".55">'
                 f'<animate attributeName="height" values="0;{h};{h};0" keyTimes="0;{0.1+i*0.03};0.86;1" '
                 f'dur="4s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="100;{100-h};{100-h};100" '
                 f'keyTimes="0;{0.1+i*0.03};0.86;1" dur="4s" repeatCount="indefinite"/></rect>')
    o.append(f'<g><animateMotion dur="4s" repeatCount="indefinite" '
             f'path="M 24 96 L 90 72 L 160 88 L 206 66 L 24 96"/>'
             f'<circle r="4.5" fill="none" stroke="#e2e8f0" stroke-width="1.4"/>'
             f'<circle r="1.5" fill="#e2e8f0"/></g>')
    return "".join(o)


# ── viz 2: nexusmart — items flow into cart ────────────────────────────────
def viz_nexusmart(a):
    o = []
    for i in range(4):
        d = i * 0.55
        o.append(f'<rect x="0" y="{68+ (i%2)*14}" width="13" height="13" rx="3" fill="{a}" fill-opacity=".7">'
                 f'<animate attributeName="x" values="18;18;170;170" keyTimes="0;{0.05+i*0.09:.2f};'
                 f'{0.45+i*0.09:.2f};1" dur="4.4s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;{0.06+i*0.09:.2f};'
                 f'{0.44+i*0.09:.2f};{0.5+i*0.09:.2f}" dur="4.4s" repeatCount="indefinite"/></rect>')
    # cart
    o.append(f'<path d="M176 72 h6 l5 20 h18 l4 -13" fill="none" stroke="{a}" stroke-width="1.8" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<circle cx="190" cy="98" r="2.6" fill="{a}"/><circle cx="203" cy="98" r="2.6" fill="{a}"/>')
    o.append(f'<text x="14" y="66" font-family="{MONO}" font-size="8.5" fill="#64748b">cart</text>')
    o.append(f'<text x="212" y="78" text-anchor="end" font-family="{MONO}" font-size="10" fill="{a}" '
             f'font-weight="700">4<animate attributeName="opacity" values=".3;1;.3" dur="1.1s" '
             f'repeatCount="indefinite"/></text>')
    return "".join(o)


# ── viz 3: devhire — filter sweep dims non-matching rows ───────────────────
def viz_devhire(a):
    o = []
    keep = {0, 2, 3, 5}
    for i in range(6):
        y = 62 + i * 7
        w = [138, 110, 148, 122, 90, 132][i]
        op = ".85" if i in keep else ".2"
        o.append(f'<rect x="20" y="{y}" width="{w}" height="4" rx="2" fill="{a}" fill-opacity="{op}">'
                 f'<animate attributeName="fill-opacity" values=".55;.55;{op};{op};.55" '
                 f'keyTimes="0;0.28;0.42;0.9;1" dur="4.6s" repeatCount="indefinite"/>'
                 f'<animate attributeName="width" values="{w};{w};{w if i in keep else w*0.5};'
                 f'{w if i in keep else w*0.5};{w}" keyTimes="0;0.28;0.42;0.9;1" dur="4.6s" '
                 f'repeatCount="indefinite"/></rect>')
    o.append(f'<rect x="20" y="58" width="2" height="46" fill="#e2e8f0" opacity=".8">'
             f'<animate attributeName="x" values="20;20;208;208;20" keyTimes="0;0.1;0.4;0.95;1" '
             f'dur="4.6s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;.9;.9;0;0" keyTimes="0;0.1;0.4;0.44;1" '
             f'dur="4.6s" repeatCount="indefinite"/></rect>')
    o.append(f'<rect x="176" y="60" width="40" height="13" rx="6.5" fill="#070d17" fill-opacity=".9"/>'
             f'<text x="196" y="69.5" text-anchor="middle" font-family="{MONO}" font-size="8.5" '
             f'fill="{a}">4 / 6</text>')
    return "".join(o)


# ── viz 4: taskflow — card travels across kanban columns ───────────────────
def viz_taskflow(a):
    o = []
    labels = ["todo", "doing", "done"]
    for i in range(3):
        x = 20 + i * 68
        o.append(f'<rect x="{x}" y="60" width="60" height="42" rx="5" fill="{a}" fill-opacity=".07" '
                 f'stroke="{a}" stroke-opacity=".28"/>')
        o.append(f'<text x="{x+5}" y="70" font-family="{MONO}" font-size="7.5" fill="#64748b" '
                 f'letter-spacing=".6">{labels[i]}</text>')
        for j in range(2):
            o.append(f'<rect x="{x+5}" y="{75+j*9}" width="{[40,28][j]}" height="5" rx="2.5" '
                     f'fill="{a}" fill-opacity=".28"/>')
    o.append(f'<g><animateMotion dur="4.2s" repeatCount="indefinite" keyPoints="0;0;.5;.5;1;1" '
             f'keyTimes="0;.12;.42;.6;.9;1" calcMode="linear" path="M 25 92 L 93 92 L 161 92"/>'
             f'<rect width="44" height="10" rx="3" fill="{a}" fill-opacity=".95"/>'
             f'<rect x="4" y="3.5" width="24" height="3" rx="1.5" fill="#0b1220" fill-opacity=".6"/></g>')
    return "".join(o)


# ── viz 5: resume / contact — signal wave + envelope ───────────────────────
def viz_contact(a):
    o = []
    for i in range(20):
        x = 20 + i * 8
        h = [6, 12, 20, 14, 26, 18, 30, 22, 34, 26, 30, 20, 24, 14, 18, 10, 14, 8, 10, 6][i]
        o.append(f'<rect x="{x}" y="{82-h/2:.0f}" width="4" height="{h}" rx="2" fill="{a}" '
                 f'fill-opacity=".6"><animate attributeName="height" values="{h};{max(3,h*0.35):.0f};{h}" '
                 f'dur="{1.6+ (i%5)*0.22:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{82-h/2:.0f};{82-max(3,h*0.35)/2:.0f};{82-h/2:.0f}" '
                 f'dur="{1.6+ (i%5)*0.22:.2f}s" repeatCount="indefinite"/></rect>')
    o.append(f'<text x="{W-18}" y="102" text-anchor="end" font-family="{MONO}" font-size="8.5" '
             f'fill="#64748b">replies within 24h</text>')
    return "".join(o)


TILES = [
    ("portfolio", "PORTFOLIO", "GSAP · AOS · SEO · Vercel", C["cy"], viz_portfolio,
     "Portfolio app tile with animated reveal bars and a custom cursor path."),
    ("nexusmart", "NEXUSMART", "Next.js · TS · Mongo · JWT", C["em"], viz_nexusmart,
     "NexusMart e-commerce tile: product items flowing into an animated cart."),
    ("devhire", "DEVHIRE PRO", "React 19 · Vite · ATS UI", C["vi"], viz_devhire,
     "DevHire Pro tile: a filter sweep narrowing candidate rows from six to four."),
    ("taskflow", "TASKFLOW", "React · Kanban · State", C["am"], viz_taskflow,
     "TaskFlow tile: a task card moving across todo, doing and done columns."),
    ("contact", "CONTACT / CV", "email · linkedin · resume", C["rd"], viz_contact,
     "Contact tile: an animated signal waveform indicating replies within 24 hours."),
]

os.makedirs("/home/user/workspace/mjbos/assets", exist_ok=True)
for slug, title, meta, accent, vf, aria in TILES:
    svg = shell(title, meta, accent, vf(accent), aria)
    p = f"/home/user/workspace/mjbos/assets/dock-{slug}.svg"
    open(p, "w").write(svg)
    print("dock-" + slug, os.path.getsize(p))
