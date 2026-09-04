#!/usr/bin/env python3
"""MJB.OS — footer shell session. Typewriter SMIL, theme-aware."""
import os

W, H = 1200, 330
T = 16.0
MONO = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"

DARK = dict(bg="#05070d", panel="#0b1220", chrome="#0a121e", edge="#17293d", grid="#0e1a2b",
            text="#cbd5e1", dim="#5b6b80", bright="#f1f5f9", em="#10b981", cy="#22d3ee",
            vi="#8b5cf6", am="#f59e0b", rd="#f43f5e", glow=".07")
LIGHT = dict(bg="#f6f8fb", panel="#ffffff", chrome="#e9eef5", edge="#d7e0ea", grid="#e4ebf3",
             text="#243040", dim="#7b8798", bright="#0b1220", em="#059669", cy="#0891b2",
             vi="#7c3aed", am="#b45309", rd="#e11d48", glow=".04")

# (kind, text)  kind: cmd | out
LINES = [
    ("cmd", "whoami"),
    ("out", "first-year IT student · shipping full-stack apps in public · Nagaon, Assam, India"),
    ("cmd", "availability --check"),
    ("out", "internships and junior roles · remote or relocate · replies inside 24 hours"),
    ("cmd", "contact --list"),
    ("out", "mail manashjyotibora122@gmail.com   ·   linkedin /in/manashjyoti-bora-323b97405"),
]

CW = 8.42  # advance width at font-size 14


def build(c):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-label="Terminal footer: Manashjyoti Bora is a first-year IT student from '
         f'Nagaon, Assam, open to internships and junior roles, reachable at '
         f'manashjyotibora122 at gmail dot com and on LinkedIn.">']
    s.append('<defs>')
    s.append(f'<linearGradient id="fSweep" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{c["cy"]}"/><stop offset=".5" stop-color="{c["em"]}"/>'
             f'<stop offset="1" stop-color="{c["vi"]}"/></linearGradient>')
    s.append(f'<radialGradient id="fHalo" cx=".12" cy="1" r=".55">'
             f'<stop offset="0" stop-color="{c["vi"]}" stop-opacity="{c["glow"]}"/>'
             f'<stop offset="1" stop-color="{c["vi"]}" stop-opacity="0"/></radialGradient>')
    s.append(f'<pattern id="fdots" width="22" height="22" patternUnits="userSpaceOnUse">'
             f'<circle cx="1.2" cy="1.2" r="1.2" fill="{c["grid"]}"/></pattern>')
    for i, (kind, txt) in enumerate(LINES):
        start = 0.5 + i * 2.15
        dur_type = min(1.55, 0.045 * len(txt))
        wpx = len(txt) * CW + (0 if kind == "out" else 0)
        s.append(f'<clipPath id="fc{i}"><rect x="0" y="0" height="24" width="0">'
                 f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" '
                 f'keyTimes="0;{start/T:.4f};{(start+dur_type)/T:.4f};{14.6/T:.4f};1" '
                 f'values="0;0;{wpx:.0f};{wpx:.0f};0"/></rect></clipPath>')
    s.append('</defs>')

    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="{c["bg"]}"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#fdots)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#fHalo)"/>')

    # chrome
    s.append(f'<rect x="0" y="0" width="{W}" height="40" fill="{c["chrome"]}"/>')
    for i, col in enumerate([c["rd"], c["am"], c["em"]]):
        s.append(f'<circle cx="{26+i*20}" cy="20" r="5.5" fill="{col}" opacity=".9"/>')
    s.append(f'<text x="{W/2}" y="25" text-anchor="middle" font-family="{MONO}" font-size="12.5" '
             f'fill="{c["dim"]}" letter-spacing="1.4">mjb.os — bash · session/hire-me</text>')
    s.append(f'<text x="{W-176}" y="24.5" font-family="{MONO}" font-size="12" fill="{c["dim"]}" '
             f'letter-spacing=".8">shell ready</text>')
    s.append(f'<line x1="0" y1="40" x2="{W}" y2="40" stroke="{c["edge"]}"/>')

    x0, y0 = 40, 84
    for i, (kind, txt) in enumerate(LINES):
        y = y0 + i * 27
        start = 0.5 + i * 2.15
        dur_type = min(1.55, 0.045 * len(txt))
        px = x0
        if kind == "cmd":
            prompt = "mjb@os:~$ "
            s.append(f'<text x="{px}" y="{y}" font-family="{MONO}" font-size="14" fill="{c["em"]}" '
                     f'opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
                     f'keyTimes="0;{max(0.0001,(start-0.1))/T:.4f};{start/T:.4f};{14.6/T:.4f};'
                     f'{14.9/T:.4f};1" values="0;0;1;1;0;0"/>{prompt}</text>')
            tx = px + len(prompt) * CW
            col = c["bright"]
        else:
            s.append(f'<text x="{px}" y="{y}" font-family="{MONO}" font-size="14" fill="{c["cy"]}" '
                     f'opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
                     f'keyTimes="0;{max(0.0001,(start-0.1))/T:.4f};{start/T:.4f};{14.6/T:.4f};'
                     f'{14.9/T:.4f};1" values="0;0;1;1;0;0"/>&gt;</text>')
            tx = px + 2 * CW
            col = c["text"]
        s.append(f'<g transform="translate({tx:.0f} {y-16})" clip-path="url(#fc{i})">'
                 f'<text x="0" y="16" font-family="{MONO}" font-size="14" fill="{col}">{txt}</text></g>')
        # caret riding the typed text
        s.append(f'<rect x="{tx:.0f}" y="{y-12}" width="8" height="15" fill="{c["em"]}" opacity="0">'
                 f'<animate attributeName="x" dur="{T}s" repeatCount="indefinite" '
                 f'keyTimes="0;{start/T:.4f};{(start+dur_type)/T:.4f};1" '
                 f'values="{tx:.0f};{tx:.0f};{tx+len(txt)*CW:.0f};{tx+len(txt)*CW:.0f}"/>'
                 f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
                 f'keyTimes="0;{(start-0.05)/T:.4f};{start/T:.4f};{(start+dur_type)/T:.4f};'
                 f'{(start+dur_type+0.15)/T:.4f};1" values="0;0;.85;.85;0;0"/></rect>')

    # final prompt with blinking cursor
    fy = y0 + len(LINES) * 27 + 6
    s.append(f'<text x="{x0}" y="{fy}" font-family="{MONO}" font-size="14" fill="{c["em"]}" opacity="0">'
             f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
             f'keyTimes="0;{13.4/T:.4f};{13.6/T:.4f};{14.6/T:.4f};{14.9/T:.4f};1" '
             f'values="0;0;1;1;0;0"/>mjb@os:~$</text>')
    s.append(f'<rect x="{x0+10*CW:.0f}" y="{fy-12}" width="8" height="15" fill="{c["em"]}" opacity="0">'
             f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
             f'keyTimes="0;{13.45/T:.4f};{13.6/T:.4f};{14.6/T:.4f};{14.75/T:.4f};1" '
             f'values="0;0;.9;.9;0;0"/>'
             f'<animate attributeName="fill-opacity" values="1;.1;1" dur=".9s" repeatCount="indefinite"/></rect>')

    # divider + signature
    dy = H - 50
    s.append(f'<rect x="40" y="{dy}" width="{W-80}" height="1.5" fill="url(#fSweep)" opacity=".55"/>')
    s.append(f'<text x="40" y="{dy+28}" font-family="{MONO}" font-size="11.5" fill="{c["dim"]}" '
             f'letter-spacing="1.6">built on a 6.1-inch screen · every animation on this page is '
             f'hand-written SVG · no badge services</text>')
    s.append(f'<circle cx="{W-52}" cy="{dy+23}" r="4.5" fill="{c["em"]}">'
             f'<animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite"/></circle>')
    s.append(f'<text x="{W-176}" y="{dy+28}" font-family="{MONO}" font-size="11.5" fill="{c["em"]}" '
             f'letter-spacing="1.4">OPEN TO WORK</text>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="{c["edge"]}"/>')
    s.append('</svg>')
    return "".join(s)


os.makedirs("/home/user/workspace/mjbos/assets", exist_ok=True)
for n, pal in (("footer-dark", DARK), ("footer-light", LIGHT)):
    p = f"/home/user/workspace/mjbos/assets/{n}.svg"
    open(p, "w").write(build(pal))
    print(n, os.path.getsize(p))
