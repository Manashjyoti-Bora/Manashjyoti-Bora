#!/usr/bin/env python3
"""
MJB.OS — cinematic boot hero.
Hand-coded SVG + SMIL. One 18s looping timeline, three acts.
Emits assets/boot-dark.svg and assets/boot-light.svg
"""
import os, math

W, H = 1200, 500
T = 18.0  # master loop

DARK = dict(
    bg="#05070d", bg2="#0a0f1a", panel="#0b1220", panelEdge="#17293d",
    grid="#0e1a2b", text="#cbd5e1", dim="#5b6b80", bright="#f1f5f9",
    em="#10b981", cy="#22d3ee", vi="#8b5cf6", am="#f59e0b", rd="#f43f5e",
    scrim="#05070d", chrome="#0a121e", glow=".22", sheen=".18",
)
LIGHT = dict(
    bg="#f6f8fb", bg2="#eef2f7", panel="#ffffff", panelEdge="#d7e0ea",
    grid="#e4ebf3", text="#243040", dim="#7b8798", bright="#0b1220",
    em="#059669", cy="#0891b2", vi="#7c3aed", am="#b45309", rd="#e11d48",
    scrim="#f6f8fb", chrome="#e9eef5", glow=".09", sheen=".06",
)

MONO = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"


def kt(*pairs):
    """pairs of (seconds, value) -> (keyTimes, values) on the T timeline"""
    ks = ";".join(f"{round(s/T,4)}" for s, _ in pairs)
    vs = ";".join(str(v) for _, v in pairs)
    return ks, vs


def anim(attr, pairs, extra=""):
    k, v = kt(*pairs)
    return (f'<animate attributeName="{attr}" dur="{T}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="{k}" values="{v}" {extra}/>')


def act_gate(start, end, fade=0.35, base=0):
    """opacity animation making a group visible in [start,end]"""
    pts = [(0, 1 if base else 0)]
    if start > 0:
        pts += [(max(0.001, start - fade), 0), (start, 1)]
    pts += [(end, 1), (min(T - 0.001, end + fade), 0)]
    if base:
        pts += [(T - fade, 0), (T, 1)]
    else:
        pts += [(T, 0)]
    # dedupe / sort
    clean = []
    for s, v in pts:
        if clean and abs(clean[-1][0] - s) < 1e-6:
            clean[-1] = (s, v)
        else:
            clean.append((s, v))
    return anim("opacity", clean)


# ───────────────────────────── ACT 1 · boot log ─────────────────────────────
LOG = [
    ("cmd", "$ ./boot --profile manashjyoti --device android"),
    ("ok", "mount /dev/curiosity", "0.4 GB/s"),
    ("ok", "load kernel   · html · css · javascript", "core"),
    ("ok", "link runtime  · react 19 · next 15 · node", "esm"),
    ("ok", "attach store  · mongodb atlas (persistent)", "tls"),
    ("ok", "verify auth   · jwt + bcrypt + httpOnly", "sealed"),
    ("ok", "probe deploys · vercel x2", "live"),
    ("warn", "no laptop detected -> falling back to phone", "notice"),
    ("ok", "6.1-inch display accepted as workstation", "forced"),
    ("ok", "2 production apps shipped from that screen", "verified"),
]


def act1(c):
    x0, y0 = 46, 96
    out = [f'<g opacity="1">{act_gate(0, 5.5, base=1)}']
    # frame
    out.append(f'<rect x="{x0-18}" y="{y0-34}" width="{W-2*(x0-18)}" height="330" rx="14" '
               f'fill="{c["panel"]}" fill-opacity=".55" stroke="{c["panelEdge"]}"/>')
    out.append(f'<text x="{x0}" y="{y0-12}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
               f'letter-spacing="2.4">BOOT SEQUENCE · POST</text>')
    out.append(f'<text x="{W-x0}" y="{y0-12}" text-anchor="end" font-family="{MONO}" font-size="11.5" '
               f'fill="{c["em"]}" letter-spacing="2.4">STATE: WAKING</text>')

    ly = y0 + 22
    for i, row in enumerate(LOG):
        t = 0.35 + i * 0.44
        y = ly + i * 24
        g = [f'<g opacity="0">{anim("opacity", [(0,0),(t,0),(t+0.12,1),(5.5,1),(T,0)])}']
        if row[0] == "cmd":
            # typewriter via clip
            txt = row[1]
            g.append(f'<clipPath id="c1t"><rect x="{x0}" y="{y-14}" height="20" width="0">'
                     f'{anim("width", [(0,0),(0.35,0),(1.9,len(txt)*8.42),(T,len(txt)*8.42)])}</rect></clipPath>')
            g.append(f'<g clip-path="url(#c1t)"><text x="{x0}" y="{y}" font-family="{MONO}" font-size="14" '
                     f'fill="{c["cy"]}">{txt}</text></g>')
            g.append(f'<rect x="{x0}" y="{y-11}" width="8" height="15" fill="{c["cy"]}" opacity=".9">'
                     f'{anim("x", [(0,x0),(0.35,x0),(1.9,x0+len(txt)*8.42),(T,x0+len(txt)*8.42)])}'
                     f'<animate attributeName="opacity" values="1;0;1" dur=".9s" repeatCount="indefinite"/></rect>')
        else:
            tag, label, note = row
            col = c["em"] if tag == "ok" else c["am"]
            word = " OK " if tag == "ok" else "WARN"
            g.append(f'<rect x="{x0}" y="{y-13}" width="46" height="19" rx="4" fill="{col}" fill-opacity=".13" '
                     f'stroke="{col}" stroke-opacity=".45"/>')
            g.append(f'<text x="{x0+23}" y="{y+1}" text-anchor="middle" font-family="{MONO}" font-size="11.5" '
                     f'font-weight="700" fill="{col}" letter-spacing="1">{word}</text>')
            g.append(f'<text x="{x0+62}" y="{y}" font-family="{MONO}" font-size="14" '
                     f'fill="{c["text"] if tag=="ok" else c["am"]}">{label}</text>')
            g.append(f'<text x="{W-x0}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12" '
                     f'fill="{c["dim"]}">{note}</text>')
        g.append("</g>")
        out.append("".join(g))

    # progress bar
    by = ly + len(LOG) * 24 - 8
    bw = W - 2 * x0
    out.append(f'<rect x="{x0}" y="{by}" width="{bw}" height="7" rx="3.5" fill="{c["grid"]}"/>')
    out.append(f'<rect x="{x0}" y="{by}" width="0" height="7" rx="3.5" fill="url(#gSweep)">'
               f'{anim("width", [(0,0),(0.3,0),(4.9,bw),(T,bw)])}</rect>')
    out.append(f'<text x="{x0}" y="{by+26}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
               f'letter-spacing="1.6">initialising identity module<tspan fill="{c["em"]}">'
               f'<animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/> ...</tspan></text>')
    out.append("</g>")
    return "".join(out)


# ───────────────────────────── ACT 2 · identity ─────────────────────────────
CHIPS = ["React", "Next.js", "TypeScript", "Node", "MongoDB", "Tailwind", "Git", "Vercel"]


def act2(c):
    cx, cy = W / 2, 250
    out = [f'<g opacity="0">{act_gate(5.85, 11.0)}']
    # orbit rings
    for i, (rx, ry, dur, op) in enumerate([(430, 150, 26, .30), (330, 112, 20, .22), (232, 78, 15, .16)]):
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{c["cy"]}" '
                   f'stroke-opacity="{op}" stroke-dasharray="3 7"/>')
    # orbiting chips on the outer + mid ring
    for i, name in enumerate(CHIPS):
        ring = 0 if i % 2 == 0 else 1
        rx, ry = (430, 150) if ring == 0 else (330, 112)
        dur = 26 if ring == 0 else 20
        off = (i / len(CHIPS)) * dur
        path = (f'M {cx-rx} {cy} a {rx} {ry} 0 1 0 {2*rx} 0 a {rx} {ry} 0 1 0 {-2*rx} 0')
        w = 13 + len(name) * 8.4
        col = [c["cy"], c["vi"], c["em"], c["am"]][i % 4]
        out.append(
            f'<g><animateMotion dur="{dur}s" repeatCount="indefinite" begin="-{off:.2f}s" '
            f'path="{path}" rotate="0"/>'
            f'<rect x="{-w/2}" y="-13" width="{w}" height="26" rx="13" fill="{c["panel"]}" '
            f'stroke="{col}" stroke-opacity=".65"/>'
            f'<text x="0" y="5" text-anchor="middle" font-family="{MONO}" font-size="12" '
            f'fill="{col}" letter-spacing=".6">{name}</text></g>')
    # name
    out.append(f'<rect x="{cx-352}" y="{cy-84}" width="704" height="168" rx="18" fill="{c["bg"]}" '
               f'fill-opacity=".82" stroke="{c["panelEdge"]}"/>')
    out.append(f'<text x="{cx}" y="{cy-46}" text-anchor="middle" font-family="{MONO}" font-size="12" '
               f'fill="{c["dim"]}" letter-spacing="5.5">IDENTITY RESOLVED</text>')
    out.append(f'<g filter="url(#soft)"><text x="{cx}" y="{cy+10}" text-anchor="middle" '
               f'font-family="{MONO}" font-size="48" font-weight="700" fill="url(#gName)" '
               f'letter-spacing="1.5">MANASHJYOTI BORA</text></g>')
    out.append(f'<text x="{cx}" y="{cy+10}" text-anchor="middle" font-family="{MONO}" font-size="48" '
               f'font-weight="700" fill="url(#gName)" letter-spacing="1.5">MANASHJYOTI BORA</text>')
    # shimmer bar under name
    out.append(f'<rect x="{cx-260}" y="{cy+26}" width="520" height="2" fill="url(#gSweep)" opacity=".8"/>')
    out.append(f'<text x="{cx}" y="{cy+56}" text-anchor="middle" font-family="{MONO}" font-size="13.5" '
               f'fill="{c["text"]}" letter-spacing="2.2">FULL-STACK DEVELOPER'
               f'<tspan fill="{c["dim"]}"> · </tspan>NAGAON, ASSAM, INDIA</text>')
    out.append("</g>")
    return "".join(out)


# ───────────────────────────── ACT 3 · telemetry ────────────────────────────
SPARK = [12, 18, 15, 26, 22, 34, 30, 44, 39, 52, 61, 55, 70, 66, 82, 92, 86, 100]
BARS = [("shipped apps", "2 live", .92, "em"), ("stack depth", "12 tools", .74, "cy"),
        ("device", "1 phone", 1.0, "vi"), ("laptops used", "zero", .06, "am")]


def act3(c):
    out = [f'<g opacity="0">{act_gate(11.35, 17.3)}']
    px, py, pw, ph = 46, 96, 640, 330
    out.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{c["panel"]}" '
               f'fill-opacity=".55" stroke="{c["panelEdge"]}"/>')
    out.append(f'<text x="{px+22}" y="{py+30}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
               f'letter-spacing="2.6">TELEMETRY · LEARNING CURVE</text>')
    out.append(f'<text x="{px+pw-22}" y="{py+30}" text-anchor="end" font-family="{MONO}" font-size="11.5" '
               f'fill="{c["em"]}" letter-spacing="1.6">TREND +</text>')
    # sparkline
    gx0, gy0, gw, gh = px + 26, py + 54, pw - 52, 152
    for i in range(5):
        gy = gy0 + i * (gh / 4)
        out.append(f'<line x1="{gx0}" y1="{gy:.1f}" x2="{gx0+gw}" y2="{gy:.1f}" stroke="{c["grid"]}"/>')
    pts = []
    for i, v in enumerate(SPARK):
        x = gx0 + i * (gw / (len(SPARK) - 1))
        y = gy0 + gh - (v / 100) * gh
        pts.append((x, y))
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    out.append(f'<path d="{d} L {pts[-1][0]:.1f} {gy0+gh} L {gx0} {gy0+gh} Z" fill="url(#gFill)" opacity="0">'
               f'{anim("opacity", [(0,0),(12.6,0),(13.6,.75),(17.3,.75),(T,0)])}</path>')
    out.append(f'<path d="{d}" fill="none" stroke="url(#gSweep)" stroke-width="2.6" stroke-linecap="round" '
               f'stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">'
               f'{anim("stroke-dashoffset", [(0,length),(11.5,length),(13.4,0),(T,0)])}</path>')
    out.append(f'<circle r="5" fill="{c["em"]}" opacity="0">'
               f'{anim("opacity", [(0,0),(13.3,0),(13.5,1),(17.3,1),(T,0)])}'
               f'<animateMotion dur="{T}s" repeatCount="indefinite" keyPoints="0;0;1;1" '
               f'keyTimes="0;{11.5/T:.4f};{13.4/T:.4f};1" calcMode="linear" path="{d}"/></circle>')
    # bars
    for i, (label, val, frac, ck) in enumerate(BARS):
        by = py + 208 + i * 0  # single row layout
        bx = px + 26 + i * ((pw - 52) / 4)
        bwd = (pw - 52) / 4 - 16
        out.append(f'<text x="{bx}" y="{py+250}" font-family="{MONO}" font-size="10.5" fill="{c["dim"]}" '
                   f'letter-spacing="1.2">{label.upper()}</text>')
        out.append(f'<text x="{bx}" y="{py+276}" font-family="{MONO}" font-size="17" font-weight="700" '
                   f'fill="{c[ck]}">{val}</text>')
        out.append(f'<rect x="{bx}" y="{py+290}" width="{bwd:.0f}" height="5" rx="2.5" fill="{c["grid"]}"/>')
        out.append(f'<rect x="{bx}" y="{py+290}" width="0" height="5" rx="2.5" fill="{c[ck]}">'
                   f'{anim("width", [(0,0),(12.2+i*0.18,0),(13.6+i*0.18,round(bwd*frac)),(T,round(bwd*frac))])}</rect>')
    # device panel
    dx, dy, dw = 716, 96, 438
    out.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="330" rx="14" fill="{c["panel"]}" '
               f'fill-opacity=".55" stroke="{c["panelEdge"]}"/>')
    out.append(f'<text x="{dx+22}" y="{dy+30}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
               f'letter-spacing="2.6">WORKSTATION</text>')
    # phone
    fx, fy, fw, fh = dx + 30, dy + 52, 122, 250
    out.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="16" fill="{c["bg2"]}" '
               f'stroke="{c["cy"]}" stroke-opacity=".5"/>')
    out.append(f'<rect x="{fx+fw/2-14}" y="{fy+7}" width="28" height="4" rx="2" fill="{c["panelEdge"]}"/>')
    out.append(f'<clipPath id="scr"><rect x="{fx+7}" y="{fy+18}" width="{fw-14}" height="{fh-30}" rx="8"/></clipPath>')
    out.append(f'<g clip-path="url(#scr)">')
    import random
    random.seed(7)
    rows = 26
    # Proper SMIL transform animation (type= belongs to <animateTransform>,
    # not <animate>) -- built outside the f-string so no backslashes are
    # needed inside the expression part.
    scroll = (f'<animateTransform attributeName="transform" type="translate" '
              f'additive="sum" dur="{T}s" repeatCount="indefinite" '
              f'calcMode="linear" keyTimes="0;{11.35/T:.4f};{17.3/T:.4f};1" '
              f'values="0 0;0 0;0 -150;0 -150"/>')
    out.append(f'<g>{scroll}')
    for i in range(rows):
        ry = fy + 26 + i * 13
        wdt = random.choice([30, 46, 58, 70, 84, 40])
        indent = random.choice([0, 8, 16])
        col = random.choice([c["cy"], c["em"], c["vi"], c["dim"], c["text"]])
        out.append(f'<rect x="{fx+12+indent}" y="{ry}" width="{wdt}" height="4" rx="2" fill="{col}" opacity=".65"/>')
    out.append('</g></g>')
    # readouts beside phone
    rx0 = fx + fw + 30
    facts = [("MACHINE", "Android phone"), ("SHELL", "Termux · node · git"),
             ("EDITOR", "github.dev web editor"), ("DEPLOYS", "git push -> vercel")]
    for i, (k, v) in enumerate(facts):
        y = dy + 80 + i * 60
        out.append(f'<text x="{rx0}" y="{y}" font-family="{MONO}" font-size="10.5" fill="{c["dim"]}" '
                   f'letter-spacing="1.6">{k}</text>')
        out.append(f'<text x="{rx0}" y="{y+20}" font-family="{MONO}" font-size="13" fill="{c["text"]}">{v}</text>')
        out.append(f'<rect x="{rx0}" y="{y+30}" width="196" height="1" fill="{c["panelEdge"]}"/>')
    out.append("</g>")
    return "".join(out)


# ───────────────────────────── chrome + shell ───────────────────────────────
def build(c):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="MJB.OS boot sequence: animated terminal boot log, identity reveal for Manashjyoti Bora, and telemetry dashboard.">']
    s.append('<defs>')
    s.append(f'<linearGradient id="gSweep" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{c["cy"]}"/><stop offset=".5" stop-color="{c["em"]}"/>'
             f'<stop offset="1" stop-color="{c["vi"]}"/></linearGradient>')
    s.append(f'<linearGradient id="gName" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{c["cy"]}"><animate attributeName="stop-color" '
             f'values="{c["cy"]};{c["em"]};{c["vi"]};{c["cy"]}" dur="8s" repeatCount="indefinite"/></stop>'
             f'<stop offset=".55" stop-color="{c["bright"]}"/>'
             f'<stop offset="1" stop-color="{c["vi"]}"><animate attributeName="stop-color" '
             f'values="{c["vi"]};{c["cy"]};{c["em"]};{c["vi"]}" dur="8s" repeatCount="indefinite"/></stop>'
             f'</linearGradient>')
    s.append(f'<linearGradient id="gFill" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{c["em"]}" stop-opacity=".38"/>'
             f'<stop offset="1" stop-color="{c["em"]}" stop-opacity="0"/></linearGradient>')
    s.append(f'<radialGradient id="gHalo" cx=".5" cy=".1" r=".9">'
             f'<stop offset="0" stop-color="{c["cy"]}" stop-opacity="{c["glow"]}"/>'
             f'<stop offset="1" stop-color="{c["cy"]}" stop-opacity="0"/></radialGradient>')
    s.append('<filter id="soft" x="-30%" y="-60%" width="160%" height="240%">'
             '<feGaussianBlur stdDeviation="9"/></filter>')
    s.append(f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
             f'<circle cx="1.2" cy="1.2" r="1.2" fill="{c["grid"]}"/></pattern>')
    s.append('</defs>')

    # background
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="{c["bg"]}"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#gHalo)"/>')

    # title bar
    s.append(f'<rect x="0" y="0" width="{W}" height="40" fill="{c["chrome"]}"/>')
    for i, col in enumerate([c["rd"], c["am"], c["em"]]):
        s.append(f'<circle cx="{26+i*20}" cy="20" r="5.5" fill="{col}" opacity=".9"/>')
    s.append(f'<text x="{W/2}" y="25" text-anchor="middle" font-family="{MONO}" font-size="12.5" '
             f'fill="{c["dim"]}" letter-spacing="1.4">mjb.os — /boot/manashjyoti.init</text>')
    s.append(f'<circle cx="{W-142}" cy="20" r="4" fill="{c["em"]}">'
             f'<animate attributeName="opacity" values="1;.2;1" dur="1.8s" repeatCount="indefinite"/></circle>'
             f'<text x="{W-130}" y="24.5" font-family="{MONO}" font-size="12" fill="{c["dim"]}" '
             f'letter-spacing=".8">open to work</text>')
    s.append(f'<line x1="0" y1="40" x2="{W}" y2="40" stroke="{c["panelEdge"]}"/>')

    # acts
    s.append(act1(c))
    s.append(act2(c))
    s.append(act3(c))

    # status strip
    sy = H - 30
    s.append(f'<line x1="0" y1="{sy-14}" x2="{W}" y2="{sy-14}" stroke="{c["panelEdge"]}"/>')
    s.append(f'<circle cx="26" cy="{sy+1}" r="4" fill="{c["em"]}">'
             f'<animate attributeName="opacity" values="1;.15;1" dur="2s" repeatCount="indefinite"/></circle>')
    s.append(f'<text x="40" y="{sy+5}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
             f'letter-spacing="1.5">hand-coded SMIL · zero badge services · theme-aware</text>')
    s.append(f'<text x="{W-466}" y="{sy+5}" font-family="{MONO}" font-size="11.5" '
             f'fill="{c["dim"]}" letter-spacing="1.5">'
             f'<tspan fill="{c["cy"]}">ACT 1</tspan> boot <tspan fill="{c["dim"]}">·</tspan> '
             f'<tspan fill="{c["vi"]}">ACT 2</tspan> identity <tspan fill="{c["dim"]}">·</tspan> '
             f'<tspan fill="{c["em"]}">ACT 3</tspan> telemetry</text>')

    # scanline sheen
    sheen = c["sheen"]
    s.append(f'<rect x="0" y="-120" width="{W}" height="120" fill="url(#gFill)" opacity="{sheen}">'
             f'<animate attributeName="y" values="-120;{H}" dur="{T}s" repeatCount="indefinite"/></rect>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="{c["panelEdge"]}"/>')
    s.append('</svg>')
    return "".join(s)


ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)
for name, pal in (("boot-dark", DARK), ("boot-light", LIGHT)):
    p = os.path.join(ASSETS, f"{name}.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(build(pal))
    print(name, os.path.getsize(p), "bytes")
