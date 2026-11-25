"""daybreak.py - one line a day, written from what actually happened.

Reads the GitHub events feed for the owner plus the live/telemetry files the
other sheets already produced, and writes assets/data/daybreak.json:

    {"date": "2026-11-25", "commits": 6, "repos_touched": 2,
     "live_up": "2/2", "cards": 0, "headline": "...", "fired_at": "..."}

The README prints this line verbatim, so it says only what the data says.
Run:  python3 .github/scripts/daybreak.py
Env:  DAYBREAK_MOCK=1 writes a deterministic sample (used by healthcheck.yml).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import ghub

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "data", "daybreak.json")
DATA = os.path.join(ROOT, "assets", "data")
START, END = "<!-- DAYBREAK:START -->", "<!-- DAYBREAK:END -->"


def load(name: str) -> dict:
    path = os.path.join(DATA, name)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def counted(events: list) -> tuple:
    """Commits and distinct repos from the last day of PushEvents."""
    commits = {}
    for ev in events:
        if ev.get("type") != "PushEvent":
            continue
        repo = (ev.get("repo") or {}).get("name", "")
        payload = ev.get("payload") or {}
        n = len(payload.get("commits") or [])
        commits[repo] = commits.get(repo, 0) + n
    return sum(commits.values()), len(commits), commits


def build() -> dict:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    if os.environ.get("DAYBREAK_MOCK"):
        commits, repos = 6, 2
        headline = "mock day: 6 commits landed across 2 repositories."
        waypoints = []
    else:
        events = ghub.paged(f"/users/{ghub.USER}/events/public", cap=100)
        since = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent = [e for e in events if (e.get("created_at") or "") >= since]
        commits, repos, per_repo = counted(recent)
        if commits:
            top = sorted(per_repo.items(), key=lambda kv: -kv[1])[:2]
            headline = (f"{commits} commit{'s' if commits != 1 else ''} landed across "
                        f"{repos} repositor{'ies' if repos != 1 else 'y'} \u2014 "
                        + ", ".join(f"{k.split('/')[-1]} ({v})" for k, v in top) + ".")
        else:
            headline = "no commits in the last 24 hours \u2014 the automation still ran."
        seen = set()
        waypoints = []
        for ev in recent:
            name = (ev.get("repo") or {}).get("name")
            if name and name not in seen:
                seen.add(name)
                waypoints.append(name)
    live = load("live.json")
    rows = live.get("rows") or []
    up = sum(1 for r in rows if r.get("status") == 200)
    cards = int((load("postcards.json") or {}).get("count") or 0)
    return {
        "date": today,
        "commits": commits,
        "repos_touched": repos,
        "live_up": f"{up}/{len(rows)}" if rows else "\u2014",
        "cards": cards,
        "headline": headline,
        "repos": waypoints[:5],
        "fired_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def readme_block(data: dict) -> str:
    """The README line - regenerated on every run, never typed by hand."""
    tail = f" \u00b7 live {data['live_up']} \u00b7 {data['cards']} postcard(s)" if data["live_up"] != "\u2014" else ""
    body = f"{data['date']} \u2014 {data['headline']}{tail}"
    return f"{START}\n> :sunrise: {body}\n{END}"


def main() -> int:
    data = build()
    os.makedirs(DATA, exist_ok=True)
    previous = load("daybreak.json")
    unchanged = all(previous.get(k) == data.get(k) for k in
                    ("date", "commits", "repos_touched", "live_up", "cards", "headline"))
    if unchanged:
        print("daybreak: nothing changed since the last digest")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    text_path = os.path.join(ROOT, "README.md")
    if os.path.isfile(text_path):
        text = open(text_path, encoding="utf-8").read()
        if START in text and END in text:
            head, rest = text.split(START, 1)
            _, tail = rest.split(END, 1)
            open(text_path, "w", encoding="utf-8").write(head + readme_block(data) + tail)
    print("daybreak: " + data["headline"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
