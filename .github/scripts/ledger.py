"""ledger.py - the commit ledger, drawn as a feathered "nightingale" fan.

Each repository is given a wedge whose thickness is its share of all commits;
the wedge is split into a solid part (hand-written) and a hatch part
(bot-written, estimated from the most recent 100 commits). Numbers come from
assets/data/snapshot.json, written by skyline.py, so the fan can never disagree
with the table printed beside it.

Run:  python3 .github/scripts/ledger.py
"""

from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAP = os.path.join(ROOT, "assets", "data", "snapshot.json")
SIDECAR = os.path.join(ROOT, "assets", "data", "ledger.json")

PALETTES = {
    "aurora": dict(bg="#05070F", card="#0B1220", line="#1B2740", ink="#EAF1FF", soft="#93A6C4", mute="#5B6E8E",
                   a="#4DE1FF", b="#9B8CFF", c="#5BF2B8", d="#FFD260", e="#FF6E9C"),
    "daylight": dict(bg="#FFFFFF", card="#F6F9FF", line="#D6E0F0", ink="#0B1326", soft="#41516F", mute="#7A8AA8",
                     a="#0A7E9E", b="#5A46E0", c="#0E8F62", d="#A96B00", e="#C3114F"),
}
ACCENTS = ("a", "b", "c", "d", "e")


def build(theme: str, model: dict, bot_share: float) -> tuple[str, dict]:
    p = PALETTES[theme]
    W, H = 1160, 440
    repos = model["repos"][:7]
    total = max(1, sum(max(1, r["commits"]) for r in repos))
    cx, cy = 330.0, 210.0
    r_out = 150.0
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         "<title>Commit ledger fan</title>",
         "<desc>A feathered fan where each wedge is one repository and the split between solid and hatched "
         "inside it is hand-written versus automated commits.</desc>",
         '<defs>',
         f'<pattern id="hatch" width="6" height="6" patternTransform="rotate(35)" patternUnits="userSpaceOnUse">'
         f'<line x1="0" y1="0" x2="0" y2="6" stroke="{p["soft"]}" stroke-width="1.6" opacity="0.55"/></pattern>',
         "</defs>",
         f'<rect width="{W}" height="{H}" rx="18" fill="{p["bg"]}" stroke="{p["line"]}"/>',
         f'<circle cx="44" cy="29" r="3" fill="{p["b"]}"/>',
         f'<text x="56" y="33" fill="{p["soft"]}" font-size="10" font-weight="700" letter-spacing="2.4" '
         f'font-family="Helvetica">COMMIT LEDGER \u00b7 FEATHER FAN</text>',
         f'<text x="24" y="70" fill="{p["ink"]}" font-size="20" font-weight="700" '
         f'font-family="Helvetica">Where the work actually lives</text>']

    for i, repo in enumerate(repos):
        value = max(1, repo["commits"])
        frac = value / total
        col = p[ACCENTS[i % 5]]
        y0 = cy - r_out + i * (2 * r_out / len(repos)) + 4
        thickness = max(6.0, 2 * r_out / len(repos) - 7)
        # the band's own share of the total is its length, its bot share is hatched
        x_start = cx - r_out
        x_end = x_start + 2 * r_out * frac
        solid = thickness * (1 - bot_share)
        # wedge band: a horizontal strip, feathered at both ends by a sine profile
        pts_top, pts_bot = [], []
        steps = 40
        for s in range(steps + 1):
            t = s / steps
            x = x_start + t * (x_end - x_start)
            feather = math.sin(t * math.pi) ** 0.35
            pts_top.append((x, y0 + (thickness - solid) / 2 * (1 - feather)))
            pts_bot.append((x, y0 + thickness - (thickness - solid) / 2 * (1 - feather)))
        d_solid = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts_top) + " L" + " L".join(
            f"{px:.1f} {py:.1f}" for px, py in reversed(pts_bot)) + " Z"
        o.append(f'<path d="{d_solid}" fill="{col}" opacity="0.85"/>')
        # hatch layer over the whole band shows the automated part
        d_all = (f"M{x_start:.1f} {y0:.1f} L{x_end:.1f} {y0:.1f} "
                 f"L{x_end:.1f} {y0 + thickness:.1f} L{x_start:.1f} {y0 + thickness:.1f} Z")
        o.append(f'<path d="{d_all}" fill="url(#hatch)"/>')
        o.append(f'<line x1="{x_start}" y1="{y0}" x2="{x_end}" y2="{y0}" stroke="{col}" '
                 f'stroke-width="1" opacity="0.35"/>')
        o.append(f'<text x="{x_start - 12}" y="{y0 + thickness / 2 + 4}" fill="{p["ink"]}" font-size="11.5" '
                 f'font-weight="600" text-anchor="end" font-family="Helvetica">'
                 f'{repo["short"][:14]}</text>')

    o.append(f'<text x="{cx}" y="{cy + r_out + 34}" fill="{p["ink"]}" font-size="22" font-weight="700" '
             f'text-anchor="middle" font-family="DejaVu Sans Mono">{total:,} commits</text>')
    o.append(f'<text x="{cx}" y="{cy + r_out + 52}" fill="{p["mute"]}" font-size="9" font-weight="700" '
             f'letter-spacing="1.8" text-anchor="middle" font-family="Helvetica">'
             f'FEATHERED: LENGTH = SHARE, HATCH = AUTOMATION</text>')

    # table on the right
    tx = 560
    o.append(f'<text x="{tx}" y="122" fill="{p["mute"]}" font-size="9" font-weight="700" letter-spacing="1.6" '
             f'font-family="Helvetica">REPOSITORY</text>')
    o.append(f'<text x="{W - 40}" y="122" fill="{p["mute"]}" font-size="9" font-weight="700" letter-spacing="1.6" '
             f'text-anchor="end" font-family="Helvetica">COMMITS / SHARE</text>')
    o.append(f'<line x1="{tx}" y1="132" x2="{W - 40}" y2="132" stroke="{p["line"]}"/>')
    rows = []
    for i, repo in enumerate(repos):
        value = max(1, repo["commits"])
        share = value / total
        y = 156 + i * 30
        col = p[ACCENTS[i % 5]]
        o.append(f'<rect x="{tx}" y="{y - 10}" width="4" height="14" rx="2" fill="{col}"/>')
        o.append(f'<text x="{tx + 14}" y="{y}" fill="{p["ink"]}" font-size="12" '
                 f'font-family="Helvetica">{repo["name"][:30]}</text>')
        o.append(f'<rect x="{tx + 250}" y="{y - 7}" width="150" height="5" rx="2.5" fill="{p["line"]}"/>')
        o.append(f'<rect x="{tx + 250}" y="{y - 7}" width="{max(3, share * 150):.1f}" height="5" rx="2.5" fill="{col}"/>')
        o.append(f'<text x="{W - 40}" y="{y}" fill="{p["soft"]}" font-size="11" text-anchor="end" '
                 f'font-family="DejaVu Sans Mono">{value:,} \u00b7 {share * 100:.1f}%</text>')
        rows.append({"name": repo["name"], "commits": value, "share": round(share, 4)})
    o.append(f'<text x="{tx}" y="{H - 22}" fill="{p["mute"]}" font-size="9.5" '
             f'font-family="DejaVu Sans Mono">solid = hand-written \u00b7 hatch = automation \u00b7 '
             f'commit counts read from the GitHub API</text>')
    o.append("</svg>")
    return "".join(o), {"total": total, "rows": rows}


def main() -> int:
    with open(SNAP, encoding="utf-8") as fh:
        model = json.load(fh)
    summary = model.get("summary") or {}
    total = summary.get("commits_total") or 0
    dev = summary.get("commits_dev") or 0
    bot_share = 0.0 if not total else max(0.0, min(0.9, 1 - dev / total))
    side = {}
    for theme in PALETTES:
        svg, side = build(theme, model, bot_share)
        with open(os.path.join(ROOT, "assets", f"ledger-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
    side["bot_share"] = round(bot_share, 4)
    with open(SIDECAR, "w", encoding="utf-8") as fh:
        json.dump(side, fh, indent=2)
        fh.write("\n")
    print(f"ledger: {side['total']:,} commits, bot share {bot_share * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
