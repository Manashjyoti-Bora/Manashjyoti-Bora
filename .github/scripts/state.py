"""state.py - the facts sheet in one place: clock, streak, counts, sources.

Renders assets/state-{aurora,daylight}.svg and fills the README regions:

    <!--STATE:START-->  ... <!--STATE:END-->     three headline numbers
    <!--VITALS:START--> ... <!--VITALS:END-->    one compact table row set

Both are optional: if a marker is missing the README is left untouched. The
sheet reads ONLY files that other scripts already wrote, so it is cheap and it
can never invent a number that the sources do not contain.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, "assets")
D = os.path.join(A, "data")
README_PATH = os.path.join(ROOT, "README.md")
START, END = "<!--STATE:START-->", "<!--STATE:END-->"
VSTART, VEND = "<!--VITALS:START-->", "<!--VITALS:END-->"

PALETTES = {
    "aurora": dict(bg="#05070F", card="#0B1220", line="#1B2740", ink="#EAF1FF", soft="#93A6C4",
                   mute="#5B6E8E", a="#4DE1FF", b="#9B8CFF", c="#5BF2B8", d="#FFD260", e="#FF6E9C"),
    "daylight": dict(bg="#FFFFFF", card="#F6F9FF", line="#D6E0F0", ink="#0B1326", soft="#41516F",
                     mute="#7A8AA8", a="#0A7E9E", b="#5A46E0", c="#0E8F62", d="#A96B00", e="#C3114F"),
}


def load(name: str) -> dict:
    path = os.path.join(D, name)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def esc(s: object) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def facts() -> dict:
    snap = load("snapshot.json")
    live = load("live.json")
    find = load("findings.json")
    cards = load("postcards.json")
    ledger = load("ledger.json")
    s = snap.get("summary") or {}
    checks = (find.get("summary") or {})
    rows = live.get("rows") or []
    up = sum(1 for r in rows if r.get("status") == 200)
    dev = int(s.get("commits_dev") or 0)
    total = int(s.get("commits_total") or 0)
    return {
        "commits": total,
        "dev": dev,
        "bot_share": round(0 if not total else 1 - dev / total, 4),
        "repos": int(s.get("repos") or 0),
        "streak": int(s.get("streak") or 0),
        "followers": int(s.get("followers") or 0),
        "stars": int(s.get("stars") or 0),
        "top_lang": s.get("top_lang") or "",
        "live_up": up,
        "live_total": len(rows),
        "hygiene": 0 if not checks.get("checks_possible") else round(
            100 * checks.get("checks_passed", 0) / checks["checks_possible"]),
        "cards": int(cards.get("count") or 0),
        "source": snap.get("source") or "none",
        "generated_at": snap.get("generated_at") or "",
        "ledger_bot": ledger.get("bot_share"),
    }


def render(theme: str, m: dict) -> str:
    p = PALETTES[theme]
    W, H = 1160, 190
    when = m["generated_at"].replace("T", " ").replace("Z", " UTC") if m["generated_at"] else "waiting for first run"
    tiles = [
        ("COMMITS", f"{m['commits']:,}", f"{100 - m['bot_share'] * 100:.0f}% hand-written", "a"),
        ("STREAK", f"{m['streak']}", "consecutive days", "c"),
        ("LIVE APPS", f"{m['live_up']}/{m['live_total']}", "answering right now", "d"),
        ("HYGIENE", f"{m['hygiene']}%", "self-review checks passed", "b"),
        ("POSTCARDS", f"{m['cards']}", "signed by visitors", "e"),
    ]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         "<title>Facts sheet</title><desc>Five headline numbers, each read from a data file written by a workflow.</desc>",
         f'<rect width="{W}" height="{H}" rx="18" fill="{p["bg"]}" stroke="{p["line"]}"/>',
         f'<circle cx="40" cy="30" r="3" fill="{p["c"]}"/>',
         f'<text x="52" y="34" fill="{p["soft"]}" font-size="10" font-weight="700" letter-spacing="2.4" '
         f'font-family="Helvetica">MEASURED, NOT REMEMBERED</text>',
         f'<text x="{W - 24}" y="34" fill="{p["mute"]}" font-size="9.5" text-anchor="end" '
         f'font-family="DejaVu Sans Mono">source: {esc(m["source"])} \u00b7 {esc(when)}</text>']
    tw = (W - 48 - 4 * 12) / 5
    for i, (label, value, note, accent) in enumerate(tiles):
        x = 24 + i * (tw + 12)
        o.append(f'<rect x="{x:.1f}" y="56" width="{tw:.1f}" height="90" rx="14" fill="{p["card"]}" stroke="{p["line"]}"/>')
        o.append(f'<text x="{x + 16:.1f}" y="80" fill="{p["mute"]}" font-size="8.8" font-weight="700" '
                 f'letter-spacing="1.8" font-family="Helvetica">{esc(label)}</text>')
        o.append(f'<text x="{x + 16:.1f}" y="114" fill="{p[accent]}" font-size="28" font-weight="700" '
                 f'font-family="DejaVu Sans Mono">{esc(value)}</text>')
        o.append(f'<text x="{x + 16:.1f}" y="134" fill="{p["soft"]}" font-size="9.5" '
                 f'font-family="Helvetica">{esc(note)}</text>')
    o.append("</svg>")
    return "".join(o)


def state_block(m: dict) -> str:
    return (f"{START}\n"
            f"| {m['commits']:,} commits | {m['streak']}-day streak | {m['live_up']}/{m['live_total']} apps live | "
            f"{m['hygiene']}% hygiene | {m['cards']} postcards |\n"
            f"| :--: | :--: | :--: | :--: | :--: |\n"
            f"{END}")


def vitals_block(m: dict) -> str:
    return (f"{VSTART}\n"
            f"| metric | value | how it is measured |\n"
            f"| --- | --- | --- |\n"
            f"| commits, all repos | {m['commits']:,} | the GitHub commits API, walked once per repo |\n"
            f"| hand-written | {m['dev']:,} ({100 - m['bot_share'] * 100:.0f}%) | commits whose author is not `github-actions[bot]` |\n"
            f"| public repositories | {m['repos']} | `/users/…/repos?type=owner` |\n"
            f"| streak | {m['streak']} days | public contribution calendar |\n"
            f"| followers / stars | {m['followers']} / {m['stars']} | user + repo objects |\n"
            f"| live apps answering | {m['live_up']} of {m['live_total']} | two HTTPS probes per URL, 12 h |\n"
            f"| self-review | {m['hygiene']}% | six checks \u00d7 every repo, 12 h |\n"
            f"{VEND}")


def patch(readme: str, start: str, end: str, block: str) -> str:
    if start not in readme or end not in readme:
        return readme
    head, rest = readme.split(start, 1)
    _, tail = rest.split(end, 1)
    return head + block + tail


def main() -> int:
    m = facts()
    for theme in PALETTES:
        with open(os.path.join(A, f"state-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(render(theme, m))
    if os.path.isfile(README_PATH):
        with open(README_PATH, encoding="utf-8") as fh:
            text = fh.read()
        text = patch(text, START, END, state_block(m))
        text = patch(text, VSTART, VEND, vitals_block(m))
        with open(README_PATH, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(f"state: {m['commits']:,} commits, streak {m['streak']}, {m['live_up']}/{m['live_total']} live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
