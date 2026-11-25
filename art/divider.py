"""divider.py - gilded hairline used between README chapters.

Static SVG (no SMIL): a rule with a diamond at the centre and tick marks that
fade out toward the edges, so long pages get a clean chapter break.
"""

from __future__ import annotations

from kit import W, alpha, circle, defs_common, f, line, path, poly, rect, svg_open, text, PALETTES


def build(theme: str) -> str:
    p = PALETTES[theme]
    w, h = W, 44
    o = [svg_open(p, w, h, "chapter divider", "A gilded hairline with a central diamond.")]
    o.append(
        f'<defs><linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{p["line"]}" stop-opacity="0"/>'
        f'<stop offset="0.28" stop-color="{p["cyan"]}" stop-opacity="0.85"/>'
        f'<stop offset="0.5" stop-color="{p["violet"]}" stop-opacity="1"/>'
        f'<stop offset="0.72" stop-color="{p["mint"]}" stop-opacity="0.85"/>'
        f'<stop offset="1" stop-color="{p["line"]}" stop-opacity="0"/>'
        "</linearGradient></defs>"
    )
    # No plate: the rule sits on whatever background the page has, so the
    # chapter break works in both themes without a visible band.
    o = o[:1]
    o.append(rect(120, 21, w - 240, 1.4, "url(#fadeL)"))
    for i in range(3):
        o.append(circle(90 - i * 14, 22, 1.4, p["cyan"], extra=f'opacity="{f(0.55 - i * 0.15)}"'))
        o.append(circle(w - 90 + i * 14, 22, 1.4, p["mint"], extra=f'opacity="{f(0.55 - i * 0.15)}"'))
    # diamond
    cx, cy, r = w / 2, 21.5, 7
    o.append(
        path(f"M{f(cx)} {f(cy - r)} L{f(cx + r)} {f(cy)} L{f(cx)} {f(cy + r)} L{f(cx - r)} {f(cy)} Z",
             fill=p["violet"])
    )
    o.append(
        path(f"M{f(cx)} {f(cy - r - 4)} L{f(cx + r + 4)} {f(cy)} L{f(cx)} {f(cy + r + 4)} L{f(cx - r - 4)} {f(cy)} Z",
             stroke=alpha(p["cyan"], 0.6), sw=1)
    )
    o.append("</svg>")
    return "".join(o)
