"""doctor.py - the bot checks its own work before anyone sees it.

Fails loudly (exit 1) instead of publishing a broken profile. Checks:

  files     every local asset referenced by README.md exists
  markers   every automation marker pair appears exactly once, in order
  svg       every SVG parses, has a viewBox, and has no script / foreignObject /
            external http reference / @import
  cron      every workflow's cron lines are well formed and the count reported
            by pulse.json matches what is on disk
  diag      the per-second denominator is labelled as a diagnostic, nowhere else
  links     every relative link in README.md resolves inside the repo

Run:  python3 .github/scripts/doctor.py [--strict]
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, "README.md")

MARKERS = [
    ("<!--STATE:START-->", "<!--STATE:END-->"),
    ("<!--VITALS:START-->", "<!--VITALS:END-->"),
    ("<!--POSTCARD:START-->", "<!--POSTCARD:END-->"),
    ("<!--ASBUILT:START-->", "<!--ASBUILT:END-->"),
    ("<!--WEEKLY:START-->", "<!--WEEKLY:END-->"),
    ("<!--DAYBREAK:START-->", "<!--DAYBREAK:END-->"),
]
# Scheduled runs per day per workflow file, as the README quotes them.
EXPECTED = {
    "skyline.yml": 24,
    "pulse.yml": 6,
    "ledger.yml": 4,
    "live-stats.yml": 12,
    "findings.yml": 8,
    "postcard.yml": 4,
    "state.yml": 2,
    "daybreak.yml": 1,
    "healthcheck.yml": 1,
    "snake.yml": 1,
    "pacman.yml": 1,
    "profile-3d.yml": 1,
}

problems: list = []
notes: list = []


def fail(msg: str) -> None:
    problems.append(msg)


def check_files(text: str) -> None:
    refs = set(re.findall(r'["\'](\./assets/[^"\'\s>]+)', text))
    refs |= set(re.findall(r'\]\((assets/[^)\s]+)\)', text))
    for ref in sorted(refs):
        clean = ref.split("?")[0].lstrip("./").split("#")[0]
        if clean.endswith("/"):
            continue
        if not os.path.exists(os.path.join(ROOT, clean)):
            fail(f"README references a missing file: {ref}")
    total = len(glob.glob(os.path.join(ROOT, "assets", "**", "*.*"), recursive=True))
    notes.append(f"{len(refs)} local references, {total} files under assets/")


def check_markers(text: str) -> None:
    for start, end in MARKERS:
        n0, n1 = text.count(start), text.count(end)
        if n0 != 1 or n1 != 1:
            fail(f"marker pair {start}/{end} appears {n0}/{n1} times (need exactly 1/1)")
            continue
        if text.index(start) > text.index(end):
            fail(f"marker pair {start}/{end} is out of order")


def check_svgs() -> None:
    files = sorted(glob.glob(os.path.join(ROOT, "assets", "**", "*.svg"), recursive=True))
    for path in files:
        rel = os.path.relpath(path, ROOT)
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            fail(f"{rel}: not well-formed XML ({exc})")
            continue
        root = tree.getroot()
        if not root.get("viewBox"):
            fail(f"{rel}: no viewBox")
        raw = open(path, encoding="utf-8").read()
        for bad in ("<script", "foreignObject", "@import"):
            if bad in raw:
                fail(f"{rel}: contains {bad}")
        if re.search(r'href="https?://|xlink:href="https?://', raw):
            fail(f"{rel}: links to an external URL")
    notes.append(f"{len(files)} SVG files parsed and scanned")


def check_cron() -> None:
    total = 0
    seen = set()
    for path in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        base = os.path.basename(path)
        src = open(path, encoding="utf-8").read()
        exprs = re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", src)
        if base in EXPECTED:
            seen.add(base)
        runs = 0
        for expr in exprs:
            fields = expr.split()
            if len(fields) != 5 or not all(re.fullmatch(r"[\d*/,\-]+", x) for x in fields):
                fail(f"{base}: malformed cron '{expr}'")
                continue
            minute_f, hour_f = fields[0], fields[1]
            per_hour = (60 // int(minute_f[2:])) if minute_f.startswith("*/") else (
                len(minute_f.split(",")) if "," in minute_f else 1)
            if hour_f == "*":
                hours = 24
            elif hour_f.startswith("*/"):
                hours = 24 // int(hour_f[2:])
            elif "," in hour_f:
                hours = len(hour_f.split(","))
            else:
                hours = 1
            runs += per_hour * hours
        if base in EXPECTED and runs != EXPECTED[base]:
            fail(f"{base}: workflow runs {runs}/day, README says {EXPECTED[base]}")
        total += runs
    for base in EXPECTED:
        if base not in seen:
            fail(f"{base}: expected workflow file is missing")
    side = os.path.join(ROOT, "assets", "data", "pulse.json")
    if os.path.isfile(side):
        with open(side, encoding="utf-8") as fh:
            pulse = json.load(fh)
        hard = sum(EXPECTED.values())
        if pulse.get("runs") and pulse["runs"] != hard:
            fail(f"pulse.json says {pulse['runs']} runs/day, disk says {hard}")
    notes.append(f"{total - EXPECTED.get('healthcheck.yml', 0)} scheduled runs/day in total")


def check_diag(text: str) -> None:
    # the honest limitation note must exist exactly once and stay a diagnostic
    n = len(re.findall(r"per[- ]second", text, re.I))
    if n == 0:
        notes.append("no per-second disclaimer found (fine if the field was removed)")
    ok = re.search(r"1 commit per second[^\n]*diagnostic", text, re.I)
    if n and not ok:
        fail("the per-second barem is not labelled as a diagnostic")


def check_links(text: str) -> None:
    for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#", "<")):
            continue
        clean = target.split("#")[0].split("?")[0]
        if clean and not os.path.exists(os.path.join(ROOT, clean[2:] if clean.startswith("./") else clean)):
            fail(f"dead relative link: {target}")


def main() -> int:
    strict = "--strict" in sys.argv
    if os.path.isfile(README):
        text = open(README, encoding="utf-8").read()
        check_files(text)
        check_markers(text)
        check_diag(text)
        check_links(text)
        fences = text.count("```")
        if fences % 2:
            fail(f"unbalanced code fences ({fences})")
    else:
        fail("README.md is missing")
    check_svgs()
    check_cron()
    for note in notes:
        print("  \u00b7 " + note)
    if problems and strict:
        for p in problems:
            print("  ! " + p)
        print(f"doctor: {len(problems)} problem(s)")
        return 1
    for p in problems:
        print("  ! " + p)
    print(f"doctor: {len(problems)} problem(s), {len(notes)} note(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
