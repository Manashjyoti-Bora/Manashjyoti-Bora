#!/usr/bin/env python3
"""SIGNATURE MARGIN - visitors sign the drawing.

A visitor opens an issue titled `sign: ...` on this repository. This script
reads those issues through the GitHub API, sanitises them hard, writes the
signature table into README.md between the SIGN markers, and draws the
signature margin of the drawing sheet as SVG.

Standard library only. No third-party service. Run with GUESTBOOK_MOCK=1 to
test offline. Override the README path with GUESTBOOK_README=<path>.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ASSETS, "data", "guestbook.json")
README = os.environ.get("GUESTBOOK_README") or os.path.join(ROOT, "README.md")
REPO = os.environ.get("GITHUB_REPOSITORY") or "Manashjyoti-Bora/Manashjyoti-Bora"
TOKEN = os.environ.get("GITHUB_TOKEN") or ""
MOCK = os.environ.get("GUESTBOOK_MOCK") == "1"
KEEP = 8

FONT = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"
W, H, T = 1200, 330, 14.0
DARK = dict(bg="#071426", bg2="#0a1b30", gridMinor="#0d2338",
            gridMajor="#13314c", ink="#dceafc", dim="#5f89ad",
            accent="#4cc9f0", band="#0c2136")
LIGHT = dict(bg="#f5f2e9", bg2="#efebdf", gridMinor="#e0dacb",
             gridMajor="#cfc7b4", ink="#1b2a3a", dim="#7d7565",
             accent="#0b6fa4", band="#e8e3d5")

MOCK_ENTRIES = [
    dict(login="octocat", date="2026-08-22", note="clean work, following along"),
    dict(login="torvalds", date="2026-08-21", note="the notes section is honest"),
    dict(login="sindresorhus", date="2026-08-20", note="built on a phone, respect"),
    dict(login="gaearon", date="2026-08-19", note="nice drawing"),
]


# ------------------------------------------------------------- sanitisation
def clean_login(s):
    s = re.sub(r"[^A-Za-z0-9-]", "", str(s or ""))
    return s[:39]


def clean_note(s):
    s = "".join(ch for ch in str(s or "") if 32 <= ord(ch) < 127)
    s = re.sub(r"[<>&|`\[\]\(\)\{\}\*_#@\\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:34]


def api(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "mjb-drawing-guestbook")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def collect():
    if MOCK:
        return list(MOCK_ENTRIES), len(MOCK_ENTRIES), True
    try:
        items = api("/repos/%s/issues?state=all&per_page=100" % REPO)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as e:
        print("guestbook: API unavailable (%s), keeping existing data" % e)
        return None, 0, False
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict) or "pull_request" in it:
            continue
        title = str(it.get("title") or "")
        labels = [str(l.get("name", "")).lower()
                  for l in it.get("labels") or [] if isinstance(l, dict)]
        is_sig = "sign" in labels or title.strip().lower().startswith("sign:")
        if not is_sig:
            continue
        login = clean_login((it.get("user") or {}).get("login"))
        if not login:
            continue
        note = clean_note(title.split(":", 1)[1] if ":" in title else title)
        if not note:
            body = str(it.get("body") or "")
            for line in body.splitlines():
                if line.strip():
                    note = clean_note(line)
                    break
        out.append(dict(login=login,
                        date=str(it.get("created_at") or "")[:10],
                        note=note))
    seen, uniq = set(), []
    for e in sorted(out, key=lambda x: x["date"], reverse=True):
        if e["login"] in seen:
            continue
        seen.add(e["login"])
        uniq.append(e)
    return uniq[:KEEP], len(uniq), True


# ------------------------------------------------------------------ drawing
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, fill, fs=10, anchor="start", weight="400", extra=""):
    a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" '
            'font-weight="%s" fill="%s" xml:space="preserve"%s%s>%s</text>'
            % (x, y, FONT, fs, weight, fill, a, extra, esc(s)))


def render(theme, c, entries):
    rows, x0, x1 = KEEP, 40.0, 1160.0
    col_w = (x1 - x0) / 2.0
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" role="img" aria-label="Signature margin of '
         'drawing MJB-001: visitors who signed by opening an issue.">'
         % (W, H, W, H)]
    o.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, c["bg"]))
    g = []
    for x in range(0, W + 1, 10):
        g.append("M%d 0V%d" % (x, H))
    for y in range(0, H + 1, 10):
        g.append("M0 %dH%d" % (y, W))
    o.append('<path d="%s" stroke="%s" stroke-width="0.5" fill="none"/>'
             % ("".join(g), c["gridMinor"]))
    g = []
    for x in range(0, W + 1, 50):
        g.append("M%d 0V%d" % (x, H))
    for y in range(0, H + 1, 50):
        g.append("M0 %dH%d" % (y, W))
    o.append('<path d="%s" stroke="%s" stroke-width="0.7" fill="none"/>'
             % ("".join(g), c["gridMajor"]))
    o.append('<rect x="12" y="12" width="%d" height="%d" fill="none" '
             'stroke="%s" stroke-width="1.5"/>' % (W - 24, H - 24, c["ink"]))
    o.append('<rect x="28" y="24" width="392" height="30" fill="%s" '
             'stroke="%s"/>' % (c["bg2"], c["accent"]))
    o.append(txt(40, 44, "SIGNATURE MARGIN  ·  SHEET 1  ·  DWG MJB-001",
                 c["ink"], 13, "start", "700"))
    o.append(txt(1160, 44, "OPEN AN ISSUE TITLED  sign:  TO ADD YOURS",
                 c["dim"], 11, "end", "600"))
    for i in range(rows):
        col, row = i // 4, i % 4
        bx = x0 + col * col_w
        by = 100.0 + row * 50.0
        o.append('<path d="M%.1f %.1fh%.1f" stroke="%s" stroke-width="0.9" '
                 'opacity="0.75"/>' % (bx, by + 12, col_w - 40, c["dim"]))
        o.append(txt(bx, by + 9, "x", c["dim"], 11))
        e = entries[i] if i < len(entries) else None
        if not e:
            o.append(txt(bx + 16, by + 8, "_" * 26, c["gridMajor"], 10))
            continue
        cid = "sg%d" % i
        inner = ('<g transform="translate(%.1f %.1f) skewX(-9)">%s</g>'
                 % (bx + 16, by + 6,
                    txt(0, 0, e["login"], c["accent"], 15, "start", "700"))
                 + txt(bx + 16, by + 27, e.get("note") or "signed the drawing",
                       c["dim"], 9.5)
                 + txt(bx + col_w - 44, by + 27, e.get("date") or "", c["dim"],
                       9.5, "end"))
        o.append('<clipPath id="%s"><rect x="%.1f" y="%.1f" height="42" '
                 'width="0"><animate attributeName="width" values="0;0;%.1f;%.1f" '
                 'keyTimes="0;%.3f;%.3f;1" dur="%.1fs" repeatCount="indefinite" '
                 'calcMode="spline" keySplines="0 0 1 1;0.3 0 0.1 1;0 0 1 1"/>'
                 '</rect></clipPath><g clip-path="url(#%s)">%s</g>'
                 % (cid, bx + 12, by - 12, col_w - 50, col_w - 50,
                    0.04 + i * 0.055, 0.12 + i * 0.055, T, cid, inner))
    o.append('<path d="M12 %d H%d" stroke="%s"/>' % (H - 44, W - 12,
                                                     c["gridMajor"]))
    o.append(txt(40, H - 24, "SIGNATURES ARE READ FROM REAL GITHUB ISSUES  ·  "
                             "LOGINS AND NOTES ARE SANITISED BEFORE DRAWING",
                 c["dim"], 10, "start", "600"))
    o.append(txt(1160, H - 24, "%d OF %d LINES USED" % (min(len(entries), KEEP),
                                                        KEEP), c["accent"], 10,
                 "end", "700"))
    o.append("</svg>")
    return "".join(o)


# ------------------------------------------------------------------ readme
def update_readme(entries, total):
    if not os.path.exists(README):
        print("guestbook: no README at %s, skipping" % README)
        return
    src = open(README, encoding="utf-8").read()
    a, b = "<!-- SIGN:START -->", "<!-- SIGN:END -->"
    if a not in src or b not in src:
        print("guestbook: markers absent, README untouched")
        return
    if entries:
        lines = ["| date | signed by | note |", "|:--|:--|:--|"]
        for e in entries:
            lines.append("| `%s` | [%s](https://github.com/%s) | %s |"
                         % (e.get("date", ""), e["login"], e["login"],
                            e.get("note") or "signed the drawing"))
        lines.append("")
        lines.append("Total signatures: **%d**" % total)
        block = "\n".join(lines)
    else:
        block = ("No signatures yet. The margin is blank and waiting.\n\n"
                 "Total signatures: **0**")
    head, rest = src.split(a, 1)
    _, tail = rest.split(b, 1)
    open(README, "w", encoding="utf-8").write(
        head + a + "\n\n" + block + "\n\n" + b + tail)
    print("guestbook: README updated with %d signature(s)" % len(entries))


def main():
    entries, total, ok = collect()
    if entries is None:
        if os.path.exists(DATA):
            old = json.load(open(DATA))
            entries = old.get("entries", [])
            total = old.get("count_total", len(entries))
        else:
            entries, total = [], 0
    os.makedirs(os.path.join(ASSETS, "data"), exist_ok=True)
    with open(DATA, "w") as f:
        json.dump(dict(generated_at=datetime.now(timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
                       mode="mock" if MOCK else ("live" if ok else "cached"),
                       repository=REPO, count_total=total, lines=KEEP,
                       entries=entries), f, indent=1)
    for name, c in (("dark", DARK), ("light", LIGHT)):
        p = os.path.join(ASSETS, "signatures-%s.svg" % name)
        with open(p, "w") as f:
            f.write(render(name, c, entries))
        print("guestbook: wrote %s (%d bytes)" % (p, os.path.getsize(p)))
    update_readme(entries, total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
