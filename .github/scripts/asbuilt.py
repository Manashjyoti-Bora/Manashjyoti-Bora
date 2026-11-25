"""asbuilt.py - the build log and the weekly rhythm, both drawn from git.

The profile is a small codebase with a commit history; this prints the last
commits of the actual repository (never re-typed) into the README between

    <!-- ASBUILT:START --> ... <!-- ASBUILT:END -->   last commits, as a log
    <!-- WEEKLY:START -->  ... <!-- WEEKLY:END -->    commits per ISO week, as a table + mermaid xychart

Run:  python3 .github/scripts/asbuilt.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections import Counter
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, "README.md")
LOG_START, LOG_END = "<!-- ASBUILT:START -->", "<!-- ASBUILT:END -->"
WK_START, WK_END = "<!-- WEEKLY:START -->", "<!-- WEEKLY:END -->"


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def log_block(n: int = 8) -> str:
    raw = git("log", f"-{n}", "--date=short", "--pretty=format:%ad|%an|%s")
    lines = ["```diff"]
    for row in raw.splitlines():
        parts = row.split("|", 2)
        if len(parts) != 3:
            continue
        day, who, subject = parts
        tag = "+" if who.endswith("[bot]") else " "
        lines.append(f"{tag} {day}  {subject[:64]}")
    lines.append("```")
    return f"{LOG_START}\n" + "\n".join(lines) + f"\n{LOG_END}"


def weekly_block(weeks: int = 8) -> str:
    raw = git("log", "--date=short", "--pretty=format:%ad")
    counts = Counter()
    for day in raw.splitlines():
        try:
            d = date.fromisoformat(day)
        except ValueError:
            continue
        monday = d - timedelta(days=d.weekday())
        counts[monday] += 1
    if not counts:
        return f"{WK_START}\n_no commit history available in this clone_\n{WK_END}"
    ordered = sorted(counts)[-weeks:]
    top = max(counts[w] for w in ordered)
    rows = ["| week of | commits | |", "| --- | :--: | --- |"]
    for w in ordered:
        bar = "\u2588" * max(1, round(6 * counts[w] / top))
        rows.append(f"| {w.isoformat()} | {counts[w]} | `{bar}` |")
    chart = ["```mermaid", "xychart-beta", "    title \"commits per week\"", "    x-axis [" +
             ", ".join(f'"{w.strftime("%d %b")}"' for w in ordered) + "]", f"    y-axis 0 --> {top}",
             "    bar [" + ", ".join(str(counts[w]) for w in ordered) + "]", "```"]
    return f"{WK_START}\n" + "\n".join(rows) + "\n\n" + "\n".join(chart) + f"\n{WK_END}"


def patch(text: str, start: str, end: str, block: str) -> str:
    if start not in text or end not in text:
        return text
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return head + block + tail


def main() -> int:
    if not os.path.isfile(README):
        print("asbuilt: no README; nothing to do")
        return 0
    text = open(README, encoding="utf-8").read()
    new = patch(text, LOG_START, LOG_END, log_block())
    new = patch(new, WK_START, WK_END, weekly_block())
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("asbuilt: README build log refreshed")
    else:
        print("asbuilt: no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
