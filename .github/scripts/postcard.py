r"""[sign] postcard - visitors sign by opening an issue titled "[sign] <name>".

The workflow reads every open issue that matches `^\[sign\]`, keeps the ones
whose author has not signed before (one postcard per person, first one wins),
and redraws assets/postcard-{aurora,daylight}.svg. Each postcard shows the name
in the author's own initials-block, the note they typed, and the date - clocked
as a stamp in the top-right corner, because a postcard without a stamp is just
a photo.

Markers in README.md (the only part this script ever writes):

    <!-- POSTCARD:START -->
    <!-- POSTCARD:END -->

Nothing else is touched; the script exits 0 and leaves the README alone when
the markers are absent, so it can run on a fork without editing it.

Run:  python3 .github/scripts/postcard.py
Env:  POSTCARD_MOCK=1 draws three sample postcards locally.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

import ghub

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "assets", "data", "postcards.json")
README_PATH = os.path.join(ROOT, "README.md")
START, END = "<!-- POSTCARD:START -->", "<!-- POSTCARD:END -->"
MAX = 9

PALETTES = {
    "aurora": dict(bg="#05070F", line="#1B2740", ink="#EAF1FF", soft="#93A6C4", mute="#5B6E8E",
                   a="#4DE1FF", b="#9B8CFF", c="#5BF2B8", d="#FFD260", e="#FF6E9C"),
    "daylight": dict(bg="#FFFFFF", line="#D6E0F0", ink="#0B1326", soft="#41516F", mute="#7A8AA8",
                     a="#0A7E9E", b="#5A46E0", c="#0E8F62", d="#A96B00", e="#C3114F"),
}
ACCENTS = ("a", "b", "c", "d", "e")


def esc(s: object) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def clean_login(login: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "", login or "visitor")[:39]


def clean_note(body: str) -> str:
    body = re.sub(r"<!--.*?-->", " ", body or "", flags=re.S)
    body = re.sub(r"^#+.*$", " ", body, flags=re.M)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:140]


def initials(name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9\u0980-\u09FF]+", name)
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def collect() -> list:
    if os.environ.get("POSTCARD_MOCK"):
        return [
            {"login": "pixel-pilot", "name": "Aditi Sen", "note": "the heartbeat wheel made me rebuild my own profile. wild.", "date": "2026-11-22", "number": 1},
            {"login": "ru-aayush", "name": "Aayush Das", "note": "second time here, still copying the divider.", "date": "2026-11-23", "number": 2},
            {"login": "mi-juno", "name": "Juno", "note": "\u09a8\u09ae\u09b8\u09cd\u09a4\u09c7 from Bengaluru \u2014 keep shipping from the phone.", "date": "2026-11-24", "number": 3},
        ]
    issues = ghub.paged(f"/repos/{ghub.USER}/Manashjyoti-Bora/issues?state=all&labels=sign", cap=200)
    seen = set()
    out = []
    for issue in issues:
        title = issue.get("title") or ""
        if not re.match(r"^\s*\[?sign\]?", title, re.I):
            continue
        login = clean_login((issue.get("user") or {}).get("login", ""))
        if login.lower() in seen or login.endswith("[bot]"):
            continue
        seen.add(login.lower())
        name = re.sub(r"^\s*\[?sign\]?[:\s-]*", "", title, flags=re.I).strip() or login
        out.append({
            "login": login,
            "name": name[:40],
            "note": clean_note(issue.get("body") or ""),
            "date": (issue.get("created_at") or "")[:10],
            "number": issue.get("number", 0),
        })
    out.sort(key=lambda c: (c["date"], c["number"]))
    return out[-MAX:]


def stamp(p: dict, x: float, y: float, date: str) -> str:
    """Perforated postage stamp with the postcard's serial and date."""
    o = [f'<g transform="translate({x},{y})">',
         f'<rect x="0" y="0" width="64" height="46" rx="3" fill="{p["bg"]}" stroke="{p["soft"]}" stroke-dasharray="3 2.4"/>',
         f'<rect x="4" y="4" width="56" height="38" rx="2" fill="{p["a"]}" opacity="0.10"/>',
         f'<text x="32" y="19" fill="{p["soft"]}" font-size="7" text-anchor="middle" letter-spacing="1" '
         f'font-family="DejaVu Sans Mono">POSTED</text>',
         f'<text x="32" y="32" fill="{p["ink"]}" font-size="9.5" text-anchor="middle" font-weight="700" '
         f'font-family="DejaVu Sans Mono">{esc(date or "----")}</text>',
         f'<text x="32" y="42" fill="{p["soft"]}" font-size="5.6" text-anchor="middle" letter-spacing="1.6" '
         f'font-family="DejaVu Sans Mono">MJB POST</text>',
         "</g>"]
    return "".join(o)


def render(theme: str, cards: list) -> str:
    p = PALETTES[theme]
    cols = 3
    rows = max(1, (len(cards) + cols - 1) // cols)
    cw, ch, gap = 356, 150, 16
    W = cols * cw + (cols - 1) * gap + 48
    H = rows * (ch + gap) + 96
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         "<title>Visitor postcards</title>",
         "<desc>Postcards signed by visitors through GitHub issues, one per person, newest last.</desc>",
         f'<rect width="{W}" height="{H}" rx="18" fill="{p["bg"]}" stroke="{p["line"]}"/>',
         f'<circle cx="40" cy="30" r="3" fill="{p["d"]}"/>',
         f'<text x="52" y="34" fill="{p["soft"]}" font-size="10" font-weight="700" letter-spacing="2.4" '
         f'font-family="Helvetica">POSTCARD WALL \u00b7 SIGN BY OPENING AN ISSUE</text>',
         f'<text x="{W - 24}" y="34" fill="{p["mute"]}" font-size="10" text-anchor="end" '
         f'font-family="DejaVu Sans Mono">{len(cards)} card{"s" if len(cards) != 1 else ""}</text>']
    if not cards:
        o.append(f'<rect x="24" y="56" width="{W - 48}" height="110" rx="14" fill="none" stroke="{p["line"]}" '
                 f'stroke-dasharray="6 5"/>')
        o.append(f'<text x="{W / 2}" y="106" fill="{p["ink"]}" font-size="14" text-anchor="middle" '
                 f'font-family="Helvetica">No postcards yet \u2014 yours would be the first.</text>')
        o.append(f'<text x="{W / 2}" y="130" fill="{p["mute"]}" font-size="11" text-anchor="middle" '
                 f'font-family="DejaVu Sans Mono">issues/new?template=sign.yml \u00b7 title: [sign] your name</text>')
        o.append("</svg>")
        return "".join(o)
    for i, card in enumerate(cards):
        col = ACCENTS[i % 5]
        colr = p[col]
        x = 24 + (i % cols) * (cw + gap)
        y = 56 + (i // cols) * (ch + gap)
        tilt = (-1.2, 0.9, -0.6, 1.3, -1.0, 0.6)[i % 6]
        o.append(f'<g transform="rotate({tilt} {x + cw / 2} {y + ch / 2})">')
        o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="{p["bg"]}" stroke="{p["line"]}"/>')
        o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="4" rx="2" fill="{colr}"/>')
        # initials block
        o.append(f'<rect x="{x + 16}" y="{y + 20}" width="46" height="46" rx="12" fill="{colr}" opacity="0.14"/>')
        o.append(f'<text x="{x + 39}" y="{y + 49}" fill="{colr}" font-size="17" font-weight="800" '
                 f'text-anchor="middle" font-family="DejaVu Sans Mono">{esc(initials(card["name"]))}</text>')
        o.append(f'<text x="{x + 74}" y="{y + 40}" fill="{p["ink"]}" font-size="13.5" font-weight="700" '
                 f'font-family="Helvetica">{esc(card["name"][:26])}</text>')
        o.append(f'<text x="{x + 74}" y="{y + 57}" fill="{p["mute"]}" font-size="10" '
                 f'font-family="DejaVu Sans Mono">@{esc(card["login"])}</text>')
        # ruled note area
        for r in range(3):
            ly = y + 92 + r * 17
            o.append(f'<line x1="{x + 16}" y1="{ly}" x2="{x + cw - 16}" y2="{ly}" stroke="{p["line"]}" '
                     f'stroke-width="0.8" opacity="0.8"/>')
        note = card["note"] or "signed the drawing."
        words = note.split()
        lines, cur = [], ""
        for wd in words:
            if len((cur + " " + wd).strip()) > 46:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        for r, ln in enumerate(lines[:3]):
            o.append(f'<text x="{x + 16}" y="{y + 96 + r * 17}" fill="{p["soft"]}" font-size="10.5" '
                     f'font-family="Helvetica">{esc(ln)}</text>')
        o.append(stamp(p, x + cw - 84, y + 14, card["date"]))
        o.append("</g>")
    o.append(f'<text x="24" y="{H - 18}" fill="{p["mute"]}" font-size="9.5" '
             f'font-family="DejaVu Sans Mono">one card per GitHub account \u00b7 drawn from real issues by '
             f'.github/scripts/postcard.py</text>')
    o.append("</svg>")
    return "".join(o)


def readme_block(cards: list) -> str:
    if not cards:
        return (f"{START}\n"
                "**[Be the first postcard \u2192](https://github.com/Manashjyoti-Bora/Manashjyoti-Bora/issues/new?template=sign.yml)** "
                "&nbsp;·&nbsp; the wall redraws itself every 12 hours.\n"
                f"{END}")
    names = ", ".join(f"[{c['name'][:24]}](https://github.com/{c['login']})" for c in cards[:6])
    return (f"{START}\n"
            f"**{len(cards)} postcard{'s' if len(cards) != 1 else ''} on the wall** &nbsp;·&nbsp; {names}"
            f" &nbsp;·&nbsp; [add yours](https://github.com/Manashjyoti-Bora/Manashjyoti-Bora/issues/new?template=sign.yml)\n"
            f"{END}")


def main() -> int:
    cards = collect()
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    previous = {}
    if os.path.isfile(DATA):
        try:
            with open(DATA, encoding="utf-8") as fh:
                previous = json.load(fh)
        except Exception:
            previous = {}
    if previous.get("cards") != cards:
        with open(DATA, "w", encoding="utf-8") as fh:
            json.dump({"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "count": len(cards), "cards": cards}, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    for theme in PALETTES:
        with open(os.path.join(ROOT, "assets", f"postcard-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(render(theme, cards))
    if os.path.isfile(README_PATH):
        with open(README_PATH, encoding="utf-8") as fh:
            text = fh.read()
        if START in text and END in text:
            head, rest = text.split(START, 1)
            _, tail = rest.split(END, 1)
            with open(README_PATH, "w", encoding="utf-8") as fh:
                fh.write(head + readme_block(cards) + tail)
            print(f"postcard: {len(cards)} card(s); README block refreshed")
        else:
            print("postcard: markers absent; README left alone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
