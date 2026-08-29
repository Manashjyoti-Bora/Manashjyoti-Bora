#!/usr/bin/env python3
"""DRAWING No. MJB-001 - an engineering drawing sheet of a developer.

Hand-written SVG. No design tool, no icon set, no third-party service.
Dark theme is a cyanotype blueprint, light theme is ink on vellum.
Run:  python build_sheet.py   ->  assets/sheet-dark.svg, assets/sheet-light.svg
"""
import json
import os
import code39

W, H = 1240, 860
T = 24.0                      # animation cycle, seconds
FONT = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"
ADV = 0.6                     # monospace advance width / font-size
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

DARK = dict(
    bg="#071426", bg2="#0a1b30", gridMinor="#0d2338", gridMajor="#13314c",
    ink="#dceafc", dim="#5f89ad", accent="#4cc9f0", ok="#52d1a4",
    warn="#ffb703", red="#ff6b6b", band="#0c2136",
    faceTop="#0f2a44", faceL="#0b2038", faceR="#081a2e", screen="#4cc9f0",
    paper="#ffffff", stampInk="#52d1a4",
)
LIGHT = dict(
    bg="#f5f2e9", bg2="#efebdf", gridMinor="#e0dacb", gridMajor="#cfc7b4",
    ink="#1b2a3a", dim="#7d7565", accent="#0b6fa4", ok="#0f7a5a",
    warn="#a86400", red="#b3261e", band="#e8e3d5",
    faceTop="#ffffff", faceL="#e6e1d3", faceR="#d6d0be", screen="#0b6fa4",
    paper="#ffffff", stampInk="#0f7a5a",
)

# ------------------------------------------------------------------ content
PARTS = [
    ("01", "SURFACE  ·  HTML + CSS", "hand-written, no framework"),
    ("02", "BEHAVIOUR  ·  JAVASCRIPT", "events, state, motion"),
    ("03", "COMPONENTS  ·  REACT 19", "one job per component"),
    ("04", "ROUTING  ·  NEXT.JS APP ROUTER", "server and client split"),
    ("05", "CONTRACTS  ·  ZOD SCHEMAS", "validated on every mutation"),
    ("06", "ACCESS  ·  JWT + BCRYPT", "httpOnly cookies, role gates"),
    ("07", "STORAGE  ·  MONGODB ATLAS", "indexed, typed access layer"),
    ("08", "DELIVERY  ·  ACTIONS + VERCEL", "typecheck, build, deploy"),
]
NOTES = [
    "NOTES",
    "1. ALL FIGURES MEASURED 2026-08-23, NOT ESTIMATED.",
    "2. COMMIT TOTALS FROM git rev-list --count HEAD.",
    "3. LATENCIES FROM REAL HTTPS GET REQUESTS.",
    "4. 4 PROJECTS BUILT, 3 REACHABLE IN PRODUCTION.",
    "5. taskflow-enterprise IS SOURCE ONLY, NO DEMO.",
    "6. NO THIRD-PARTY BADGE OR STAT SERVICE ON THIS",
    "   SHEET. EVERY MARK IS GENERATED IN THIS REPO.",
    "7. EXPERIENCE: 1 YEAR OF SELF-DIRECTED BUILDING,",
    "   0 YEARS EMPLOYED. STATED PLAINLY ON PURPOSE.",
    "8. TOLERANCE ON CLAIMS: +/- 0.",
]
TITLE_ROWS = [
    ("TITLE", "MANASHJYOTI BORA · CREATIVE DEVELOPER"),
    ("DWG No", "MJB-001            REV  E"),
    ("DRAWN BY", "M. BORA            DATE  2026-08-23"),
    ("SCALE", "1:1                SHEET  1 OF 1"),
    ("MEDIUM", "ONE 6.1-INCH ANDROID PHONE, TERMUX"),
    ("STATUS", "OPEN TO WORK  ·  REPLIES WITHIN 24 h"),
]
BARCODE_TEXT = "MANASHBORA.VERCEL.APP"

# assembly geometry
CX = 400.0
HX, HY, TH = 150.0, 75.0, 9.0        # plate half-width, half-depth, thickness
PLATE_Y = [130 + 41 * i for i in range(8)]
BASE_Y = 508.0
BAND_Y = 690.0


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(s, fs):
    """rendered width of a monospace string"""
    return len(s) * fs * ADV


def fit(s, fs, limit):
    n = int(limit / (fs * ADV))
    return s if len(s) <= n else s[:max(0, n - 1)] + "."


def txt(x, y, s, fill, fs=10, anchor="start", weight="400", op=None,
        extra="", ls=None):
    a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
    o = ' opacity="%s"' % op if op is not None else ""
    l = ' letter-spacing="%s"' % ls if ls else ""
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" '
            'font-weight="%s" fill="%s" xml:space="preserve"%s%s%s%s>%s</text>'
            % (x, y, FONT, fs, weight, fill, a, o, l, extra, esc(s)))


def draw(d, stroke, sw=1.0, begin=0.0, dur=0.8, dash=None, fill="none",
         extra="", op=1.0):
    """a path that draws itself once, then stays"""
    if dash:
        # dashed line: reveal with a growing clip instead of dashoffset
        return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" '
                'stroke-dasharray="%s" opacity="0"%s>'
                '<animate attributeName="opacity" values="0;%.2f" dur="%.2fs" '
                'begin="%.2fs" fill="freeze"/></path>'
                % (d, fill, stroke, sw, dash, extra, op, dur, begin))
    return ('<path d="%s" pathLength="1" fill="%s" stroke="%s" '
            'stroke-width="%.2f" stroke-dasharray="1" stroke-dashoffset="1" '
            'stroke-linecap="round" opacity="%.2f"%s>'
            '<animate attributeName="stroke-dashoffset" values="1;0" '
            'dur="%.2fs" begin="%.2fs" fill="freeze" '
            'calcMode="spline" keySplines="0.4 0 0.2 1"/></path>'
            % (d, fill, stroke, sw, op, extra, dur, begin))


def fade(inner, begin, dur=0.5, to=1.0):
    return ('<g opacity="0">%s<animate attributeName="opacity" values="0;%.2f" '
            'dur="%.2fs" begin="%.2fs" fill="freeze"/></g>'
            % (inner, to, dur, begin))


def wipe(inner, cid, x, y, w, h, begin, dur=0.7):
    return ('<clipPath id="%s"><rect x="%.1f" y="%.1f" height="%.1f" width="0">'
            '<animate attributeName="width" values="0;%.1f" dur="%.2fs" '
            'begin="%.2fs" fill="freeze" calcMode="spline" '
            'keySplines="0.3 0 0.1 1"/></rect></clipPath>'
            '<g clip-path="url(#%s)">%s</g>'
            % (cid, x, y, h, w, dur, begin, cid, inner))


# ------------------------------------------------------------------ pieces
def grid(c):
    o = []
    o.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, c["bg"]))
    minor = []
    for x in range(0, W + 1, 10):
        minor.append("M%d 0V%d" % (x, H))
    for y in range(0, H + 1, 10):
        minor.append("M0 %dH%d" % (y, W))
    o.append('<path d="%s" stroke="%s" stroke-width="0.5" fill="none" '
             'opacity="0"><animate attributeName="opacity" values="0;1" '
             'dur="1.2s" fill="freeze"/></path>' % ("".join(minor), c["gridMinor"]))
    major = []
    for x in range(0, W + 1, 50):
        major.append("M%d 0V%d" % (x, H))
    for y in range(0, H + 1, 50):
        major.append("M0 %dH%d" % (y, W))
    o.append('<path d="%s" stroke="%s" stroke-width="0.7" fill="none" '
             'opacity="0"><animate attributeName="opacity" values="0;1" '
             'dur="1.4s" begin="0.2s" fill="freeze"/></path>'
             % ("".join(major), c["gridMajor"]))
    return "".join(o)


def frame(c):
    o = []
    o.append(draw("M12 12H1228V848H12Z", c["dim"], 1.0, 0.7, 1.1))
    o.append(draw("M30 30H1210V830H30Z", c["ink"], 1.6, 0.9, 1.3))
    # zone marks: numbers across the top, letters down the left
    zones = []
    for i in range(6):
        x = 30 + (1180 / 6.0) * i
        zones.append('<path d="M%.1f 12V30" stroke="%s" stroke-width="1"/>'
                     % (x, c["dim"]))
        zones.append(txt(x + (1180 / 12.0), 26, str(i + 1), c["dim"], 9,
                         "middle"))
    for j in range(4):
        y = 30 + (800 / 4.0) * j
        zones.append('<path d="M12 %.1fH30" stroke="%s" stroke-width="1"/>'
                     % (y, c["dim"]))
        zones.append(txt(21, y + (800 / 8.0) + 3, "ABCD"[j], c["dim"], 9,
                         "middle"))
    o.append(fade("".join(zones), 1.6, 0.6))
    return "".join(o)


def plate(c, i, y, begin):
    """one exploded slab of the stack, drawn as a 2:1 isometric plate"""
    top = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX, y - HY, CX + HX, y, CX, y + HY, CX - HX, y)
    left = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX - HX, y, CX, y + HY, CX, y + HY + TH, CX - HX, y + TH)
    right = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX + HX, y, CX, y + HY, CX, y + HY + TH, CX + HX, y + TH)
    o = [fade('<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
              '<path d="%s" fill="%s"/>' % (left, c["faceL"], right, c["faceR"],
                                            top, c["faceTop"]),
              begin + 0.25, 0.55, 1.0)]
    o.append(draw(top, c["accent"] if i in (0, 7) else c["ink"], 1.3, begin, 0.62))
    o.append(draw(left + right, c["dim"], 1.0, begin + 0.2, 0.5))
    return "".join(o)


def phone(c, begin):
    """the workbench: the 6.1-inch phone everything is built on"""
    y = BASE_Y
    hx, hy, th = HX + 26, HY + 13, 14.0
    top = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX, y - hy, CX + hx, y, CX, y + hy, CX - hx, y)
    left = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX - hx, y, CX, y + hy, CX, y + hy + th, CX - hx, y + th)
    right = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX + hx, y, CX, y + hy, CX, y + hy + th, CX + hx, y + th)
    o = [fade('<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
              '<path d="%s" fill="%s"/>' % (left, c["faceL"], right, c["faceR"],
                                            top, c["faceTop"]), begin, 0.5)]
    o.append(draw(top, c["ink"], 1.5, begin, 0.7))
    o.append(draw(left + right, c["dim"], 1.1, begin + 0.2, 0.5))
    # screen: a smaller diamond with a moving code line
    s = 0.62
    scr = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
        CX, y - hy * s, CX + hx * s, y, CX, y + hy * s, CX - hx * s, y)
    o.append(fade('<path d="%s" fill="%s" opacity="0.16"/>'
                  '<path d="%s" fill="none" stroke="%s" stroke-width="1" '
                  'stroke-dasharray="5 4"/>' % (scr, c["screen"], scr,
                                                c["screen"]), begin + 0.4, 0.5))
    # a caret blinking on the screen
    o.append(fade('<rect x="%.1f" y="%.1f" width="7" height="12" fill="%s">'
                  '<animate attributeName="opacity" values="1;1;0;0;1" '
                  'keyTimes="0;0.45;0.5;0.95;1" dur="1.1s" '
                  'repeatCount="indefinite"/></rect>'
                  % (CX - 3, y - 6, c["screen"]), begin + 0.7, 0.4))
    lab = "6.1-INCH ANDROID  ·  TERMUX  ·  NO LAPTOP"
    o.append(fade(txt(CX, y + hy + th + 17, lab, c["accent"], 11, "middle",
                      "600", ls="0.6"), begin + 0.8, 0.6))
    return "".join(o)


def centerline(c, begin):
    d = "M%.1f 66V626" % CX
    return ('<path d="%s" stroke="%s" stroke-width="0.9" fill="none" '
            'stroke-dasharray="20 4 4 4" opacity="0">'
            '<animate attributeName="opacity" values="0;0.9" dur="0.7s" '
            'begin="%.2fs" fill="freeze"/></path>' % (d, c["accent"], begin))


def balloons(c, begin):
    """numbered callouts, one per plate, leader line then label"""
    o = []
    bx = 600.0
    for i, y in enumerate(PLATE_Y):
        b = begin + i * 0.42
        num, name, sub = PARTS[i]
        # leader: from the plate's right vertex, dogleg to the balloon
        d = "M%.1f %.1fL%.1f %.1fL%.1f %.1f" % (
            CX + HX - 4, y + 1, bx - 46, y + 1, bx - 15, y + 1)
        o.append(draw(d, c["dim"], 0.9, b, 0.42))
        o.append('<circle cx="%.1f" cy="%.1f" r="0" fill="none" stroke="%s" '
                 'stroke-width="1.2"><animate attributeName="r" '
                 'values="0;15.5;13" keyTimes="0;0.68;1" dur="0.4s" '
                 'begin="%.2fs" fill="freeze"/></circle>'
                 % (bx, y + 1, c["accent"], b + 0.3))
        o.append(fade(txt(bx, y + 5, num, c["accent"], 11, "middle", "700"),
                      b + 0.44, 0.3))
        name = fit(name, 11, 250)
        sub = fit(sub, 9.5, 250)
        inner = (txt(bx + 22, y - 1, name, c["ink"], 11, "start", "600")
                 + txt(bx + 22, y + 12, sub, c["dim"], 9.5))
        o.append(wipe(inner, "bl%d" % i, bx + 20, y - 12, 258, 28, b + 0.5, 0.5))
    return "".join(o)


def arrow(x, y, ang, c, size=7.0):
    """solid filled arrowhead, ang in degrees"""
    return ('<path d="M0 0L%.1f %.1fL%.1f %.1fZ" fill="%s" '
            'transform="translate(%.1f %.1f) rotate(%.1f)"/>'
            % (size, -size * 0.3, size, size * 0.3, c, x, y, ang))


def dims(c, begin):
    """real measured dimensions, drawn the way a machinist expects"""
    o = []
    y0, y1 = PLATE_Y[0] - HY, BASE_Y + HY + 14
    # extension lines
    o.append(draw("M%.1f %.1fH%.1f M%.1f %.1fH%.1f"
                  % (CX - HX - 6, y0, 150, CX - HX - 32, y1, 150),
                  c["dim"], 0.8, begin, 0.5))
    # dimension line 1: overall stack
    o.append(draw("M170 %.1fV%.1f" % (y0, y1), c["warn"], 1.1, begin + 0.3, 0.7))
    o.append(fade(arrow(170, y0, 90, c["warn"]) + arrow(170, y1, -90, c["warn"]),
                  begin + 0.9, 0.3))
    o.append(fade('<g transform="translate(164 %.1f) rotate(-90)">%s</g>'
                  % ((y0 + y1) / 2.0,
                     txt(0, 0, "81 COMMITS", c["warn"], 12, "middle", "700",
                         ls="1")), begin + 1.0, 0.4))
    # dimension line 2: chained outside the first
    o.append(draw("M120 %.1fV%.1f" % (y0, y1), c["dim"], 1.0, begin + 0.5, 0.7))
    o.append(fade(arrow(120, y0, 90, c["dim"]) + arrow(120, y1, -90, c["dim"]),
                  begin + 1.0, 0.3))
    o.append(fade('<g transform="translate(114 %.1f) rotate(-90)">%s</g>'
                  % ((y0 + y1) / 2.0,
                     txt(0, 0, "52 DAYS  (2026-07-02 -> 2026-08-23)", c["dim"],
                         9.5, "middle")), begin + 1.1, 0.4))
    # horizontal dimension under the phone
    hx = HX + 26
    yb = BASE_Y + HY + 14 + 60
    o.append(draw("M%.1f %.1fV%.1f M%.1f %.1fV%.1f"
                  % (CX - hx, BASE_Y + 6, yb + 6, CX + hx, BASE_Y + 6, yb + 6),
                  c["dim"], 0.8, begin + 0.6, 0.5))
    o.append(draw("M%.1f %.1fH%.1f" % (CX - hx, yb, CX + hx), c["accent"], 1.1,
                  begin + 0.9, 0.7))
    o.append(fade(arrow(CX - hx, yb, 0, c["accent"])
                  + arrow(CX + hx, yb, 180, c["accent"]), begin + 1.4, 0.3))
    o.append(fade('<rect x="%.1f" y="%.1f" width="122" height="17" fill="%s"/>'
                  % (CX - 61, yb - 8.5, c["bg"])
                  + txt(CX, yb + 4, "ONE DEVELOPER", c["accent"], 11, "middle",
                        "700"), begin + 1.5, 0.4))
    # leader callout to the stack
    o.append(draw("M%.1f %.1fL%.1f %.1fH%.1f"
                  % (CX + 96, PLATE_Y[7] + 34, CX + 176, 506, 604),
                  c["ok"], 1.0, begin + 1.2, 0.6))
    o.append(fade('<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s"/>'
                  % (CX + 96, PLATE_Y[7] + 34, c["ok"])
                  + txt(612, 510, "5 REPOSITORIES  ·  4 PROJECTS  ·  3 LIVE",
                        c["ok"], 10.5, "start", "600")
                  + txt(612, 524, "one of them has no demo, and the sheet says so",
                        c["dim"], 9), begin + 1.7, 0.4))
    # section marker A-A
    o.append(fade('<path d="M612 664H700" stroke="%s" stroke-width="2.2" '
                  'stroke-dasharray="16 5"/>' % c["red"]
                  + arrow(706, 664, 0, c["red"], 9)
                  + txt(612, 656, "A", c["red"], 11, "middle", "700")
                  + txt(718, 668, "SECTION A-A  ·  THE README BELOW", c["red"],
                        9.5), begin + 1.9, 0.5))
    return "".join(o)


def detail(c, begin):
    """DETAIL A (2:1): the magnified edge of plate 05, with a tolerance note"""
    ox, oy, r = 1040.0, 178.0, 96.0
    o = [draw("M%.1f %.1fA%.1f %.1f 0 1 1 %.1f %.1f A%.1f %.1f 0 1 1 %.1f %.1f"
              % (ox - r, oy, r, r, ox + r, oy, r, r, ox - r, oy),
              c["ink"], 1.4, begin, 1.0)]
    o.append('<clipPath id="dtl"><circle cx="%.1f" cy="%.1f" r="%.1f"/>'
             '</clipPath>' % (ox, oy, r - 2))

    def slab(cy, hx=58.0, hy=29.0, th=15.0):
        top = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (
            ox, cy - hy, ox + hx, cy, ox, cy + hy, ox - hx, cy)
        side = ("M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ"
                % (ox - hx, cy, ox, cy + hy, ox, cy + hy + th, ox - hx, cy + th)
                + "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ"
                % (ox + hx, cy, ox, cy + hy, ox, cy + hy + th, ox + hx, cy + th))
        hatch = []
        for k in range(11):
            x = ox - hx + 6 + k * 10
            hatch.append("M%.1f %.1fl9 -5" % (x, cy + th + (hy - abs(x - ox)
                                                            * hy / hx) - 3))
        return ('<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
                '<path d="%s" stroke="%s" stroke-width="0.7" fill="none" '
                'opacity="0.85"/>'
                '<path d="%s" fill="none" stroke="%s" stroke-width="1.5"/>'
                '<path d="%s" fill="none" stroke="%s" stroke-width="1"/>'
                % (side, c["faceL"], top, c["faceTop"], "".join(hatch),
                   c["dim"], top, c["ink"], side, c["dim"]))

    inner = [slab(oy - 52), slab(oy + 52)]
    # the honest gap between two layers
    g0, g1 = oy - 52 + 29 + 15, oy + 52 - 29
    inner.append('<path d="M%.1f %.1fV%.1f" stroke="%s" stroke-width="1"/>'
                 % (ox - 44, g0, g1, c["warn"]))
    inner.append(arrow(ox - 44, g0, 90, c["warn"], 6))
    inner.append(arrow(ox - 44, g1, -90, c["warn"], 6))
    inner.append(txt(ox - 36, (g0 + g1) / 2.0 + 4, "GAP", c["warn"], 10,
                     "start", "700"))
    o.append(fade('<g clip-path="url(#dtl)">%s</g>' % "".join(inner),
                  begin + 0.7, 0.6))
    o.append(fade(txt(ox, oy + r + 20, "DETAIL A  (2:1)  ·  TOL +/- 0", c["ink"],
                      11, "middle", "700", ls="0.8")
                  + txt(ox, oy + r + 36, "GAP = WHAT I HAVE NOT LEARNED YET",
                        c["dim"], 9.5, "middle"), begin + 1.1, 0.4))
    # the marker back on the assembly
    o.append(fade('<circle cx="%.1f" cy="%.1f" r="17" fill="none" stroke="%s" '
                  'stroke-width="1.2" stroke-dasharray="4 3"/>'
                  % (CX + 96, PLATE_Y[4] + 4, c["ink"])
                  + txt(CX + 96, PLATE_Y[4] + 8, "A", c["ink"], 11, "middle",
                        "700"), begin + 0.3, 0.4))
    return "".join(o)


def notes(c, begin):
    o = []
    x, y = 880.0, 344.0
    o.append(draw("M%.1f %.1fH1200V%.1fH%.1fZ" % (x, y, y + 190, x), c["dim"],
                  1.0, begin, 0.7))
    for i, line in enumerate(NOTES):
        b = begin + 0.5 + i * 0.13
        fs = 11 if i == 0 else 9.5
        col = c["ink"] if i == 0 else c["dim"]
        s = fit(line, fs, 300)
        o.append(wipe(txt(x + 12, y + 22 + i * 15.4, s, col, fs, "start",
                          "700" if i == 0 else "400"),
                      "nt%d" % i, x + 10, y + 8 + i * 15.4, 304, 16, b, 0.4))
    return "".join(o)


def stamp(c, begin):
    """an ink stamp that lands on the sheet"""
    ox, oy = 1032.0, 604.0
    inner = ['<g stroke="%s" fill="none">'
             '<rect x="-118" y="-40" width="236" height="80" stroke-width="2.4"/>'
             '<rect x="-110" y="-32" width="220" height="64" stroke-width="1"/>'
             '</g>' % c["stampInk"],
             txt(0, -6, "BUILT IN PUBLIC", c["stampInk"], 17, "middle", "800",
                 ls="1.6"),
             txt(0, 14, "SHIPPED · NOT SIMULATED", c["stampInk"], 10, "middle",
                 "600", ls="0.8"),
             txt(0, 30, "2026-08-23", c["stampInk"], 9, "middle", "400")]
    g = ("".join(inner))
    return ('<g opacity="0" transform="translate(%.1f %.1f) rotate(-7) '
            'scale(1)">%s'
            '<animateTransform attributeName="transform" type="scale" '
            'values="1.5;0.94;1" keyTimes="0;0.72;1" dur="0.5s" begin="%.2fs" '
            'fill="freeze" additive="sum"/>'
            '<animate attributeName="opacity" values="0;0.35;0.9" '
            'keyTimes="0;0.4;1" dur="0.5s" begin="%.2fs" fill="freeze"/>'
            '</g>' % (ox, oy, g, begin, begin))


SIG_A = ("M14 52C16 22 21 12 28 12C35 12 34 30 31 42C28 54 27 30 38 17"
         "C45 8 53 12 53 25C53 34 49 44 46 48C52 40 62 24 74 22"
         "C82 21 84 30 76 34C86 34 88 46 76 49C69 50 64 46 64 41")
SIG_B = ("M70 47C84 56 108 58 132 52C158 45 176 28 194 30C208 31 212 44 201 48"
         "C192 51 188 44 193 39")
SIG_C = "M8 64C64 76 152 72 214 58"


def signature(c, begin):
    """a signature that writes itself, then the printed name under the rule"""
    ox, oy = 660.0, 712.0
    o = ['<g transform="translate(%.1f %.1f)">' % (ox, oy)]
    for i, d in enumerate((SIG_A, SIG_B, SIG_C)):
        o.append(draw(d, c["ink"], 2.5 if i < 2 else 1.6, begin + i * 0.95,
                      1.15 if i < 2 else 0.8, extra=' stroke-linejoin="round"'))
    o.append("</g>")
    o.append(fade('<path d="M%.1f %.1fH%.1f" stroke="%s" stroke-width="1"/>'
                  % (ox + 4, oy + 78, ox + 226, c["dim"]), begin, 0.4))
    o.append(fade(txt(ox + 4, oy + 94, "SIGNED  ·  MANASHJYOTI BORA", c["ink"],
                      10.5, "start", "700", ls="0.5")
                  + txt(ox + 4, oy + 108, "NAGAON, ASSAM, INDIA  ·  IST (UTC+5:30)",
                        c["dim"], 9), begin + 2.6, 0.6))
    return "".join(o)


def band(c, begin):
    """bottom band: barcode cell, signature cell, title block"""
    o = []
    o.append(draw("M30 %.1fH1210" % BAND_Y, c["ink"], 1.6, begin, 0.8))
    o.append(fade('<rect x="30" y="%.1f" width="1180" height="%.1f" fill="%s" '
                  'opacity="0.55"/>' % (BAND_Y, 830 - BAND_Y, c["band"]),
                  begin, 0.5))
    o.append(fade('<path d="M640 %.1fV830 M900 %.1fV830" stroke="%s" '
                  'stroke-width="1"/>' % (BAND_Y, BAND_Y, c["dim"]),
                  begin + 0.3, 0.5))
    # ---- barcode cell
    narrow, wide = 1.8, 4.5
    bw = code39.width(BARCODE_TEXT, narrow, wide)
    bx = 40 + (600 - bw) / 2.0
    label = ('<rect x="%.1f" y="%.1f" width="%.1f" height="66" rx="2" '
             'fill="%s" stroke="%s" stroke-width="0.8"/>'
             % (bx - 12, BAND_Y + 26, bw + 24, "#ffffff", c["dim"]))
    bars = code39.svg_bars(BARCODE_TEXT, bx, BAND_Y + 36, 46, narrow, wide,
                           "#101820")
    o.append(wipe(label + bars, "bc", bx - 14, BAND_Y + 24, bw + 28, 70,
                  begin + 1.0, 0.9))
    o.append(fade(txt(40 + 300, BAND_Y + 18, "CODE 39  ·  ENCODED BY HAND IN THIS REPO",
                      c["dim"], 9, "middle")
                  + txt(40 + 300, BAND_Y + 108, BARCODE_TEXT, c["ink"], 12,
                        "middle", "700", ls="2.2")
                  + txt(40 + 300, BAND_Y + 124, "scan it  ·  it opens the live site",
                        c["accent"], 9, "middle"), begin + 1.6, 0.6))
    # ---- title block
    tx = 912.0
    for i, (k, v) in enumerate(TITLE_ROWS):
        y = BAND_Y + 20 + i * 21
        b = begin + 0.5 + i * 0.1
        o.append(fade('<path d="M900 %.1fH1210" stroke="%s" stroke-width="0.6" '
                      'opacity="0.6"/>' % (y + 6, c["dim"]), b, 0.3))
        o.append(fade(txt(tx, y, k, c["dim"], 8.5, "start", "600", ls="0.4"), b,
                      0.3))
        val = fit(v, 9.5, 222)
        o.append(fade(txt(tx + 74, y, val, c["ink"], 9.5, "start",
                          "700" if i == 0 else "400"), b + 0.05, 0.3))
    return "".join(o)


def header(c, begin):
    o = []
    o.append(fade(txt(44, 94, "DRAWING No. MJB-001", c["accent"], 13, "start",
                      "800", ls="1.4")
                  + txt(44, 110, "A DEVELOPER, DRAWN TO SCALE",
                        c["dim"], 10), begin, 0.6))
    o.append(fade(txt(1196, 58, "REV E", c["ink"], 13, "end", "800", ls="1.2")
                  + txt(1196, 74, "SUPERSEDES REV A-D", c["dim"], 9.5, "end"),
                  begin + 0.2, 0.6))
    return "".join(o)


def build(theme, c):
    body = [grid(c), frame(c), header(c, 1.8), centerline(c, 2.2)]
    for i, y in enumerate(PLATE_Y):
        body.append(plate(c, i, y, 2.6 + i * 0.62))
    body.append(phone(c, 7.9))
    body.append(balloons(c, 9.0))
    body.append(dims(c, 12.2))
    body.append(detail(c, 14.4))
    body.append(notes(c, 15.6))
    body.append(stamp(c, 17.6))
    body.append(band(c, 18.2))
    body.append(signature(c, 19.4))
    inner = "".join(body)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img" '
            'aria-label="Engineering drawing MJB-001: an exploded assembly '
            'view of Manashjyoti Bora as a developer, with measured '
            'dimensions, notes, a stamp, a hand-encoded Code 39 barcode and a '
            'signature.">'
            '<g opacity="1"><animate attributeName="opacity" '
            'values="1;1;0;1" keyTimes="0;0.965;0.995;1" dur="%.1fs" '
            'repeatCount="indefinite"/>%s</g></svg>'
            % (W, H, W, H, T, inner))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, c in (("dark", DARK), ("light", LIGHT)):
        p = os.path.join(OUT, "sheet-%s.svg" % name)
        with open(p, "w") as f:
            f.write(build(name, c))
        print("sheet-%s %d bytes" % (name, os.path.getsize(p)))
    meta = dict(drawing="MJB-001", cycle_seconds=T, barcode=BARCODE_TEXT,
                barcode_symbology="Code 39", parts=[p[1] for p in PARTS])
    with open(os.path.join(OUT, "data", "sheet.json"), "w") as f:
        json.dump(meta, f, indent=1)


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    main()
