#!/usr/bin/env python3
"""Daily README self-updater — the heart of the hands-free profile.

Pulls REAL data from the GitHub API and refreshes three marker blocks in
README.md without ever touching the hand-written parts:

    <!--AUTO-UPDATE:START-->   daily snapshot (ASCII terminal box)
    <!--REPO-INDEX:START-->    live repository table
    <!--LANG-PIE:START-->      Mermaid pie with real language bytes

It also appends each successful run to assets/data/snapshot-history.json so
the profile can truthfully show an "auto-update streak" — if the pipeline
ever stops, the streak stops too.  If the GitHub API is unreachable it falls
back to the last cached snapshot instead of failing, keeping the daily
heartbeat alive.  Standard library only.  Run with MJB_MOCK=1 to test offline.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "assets" / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.json"
HISTORY_PATH = DATA_DIR / "snapshot-history.json"
README_PATH = ROOT / "README.md"

USER = "Manashjyoti-Bora"
API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
MOCK = os.environ.get("MJB_MOCK") == "1"

IST = timezone(timedelta(hours=5, minutes=30))


# --------------------------------------------------------------------------
# GitHub API (small, retryable, token-aware if present)
# --------------------------------------------------------------------------

def _headers() -> Dict[str, str]:
    h = {
        "User-Agent": USER,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def gh_response(path: str, retries: int = 3) -> Any:
    """GET a GitHub API path, returning (payload, response headers)."""
    url = path if path.startswith("http") else API + path
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            last = exc
            # 403/429 are rate limits; retrying is the right move.
            if exc.code == 404:
                raise
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GitHub API failed after {retries} tries: {last}")


def gh(path: str, retries: int = 3) -> Any:
    return gh_response(path, retries)[0]


def repo_commit_count(name: str) -> int:
    """Total commits on a repo's default branch — via Link-header pagination."""
    data, headers = gh_response(f"/repos/{USER}/{name}/commits?per_page=1", retries=2)
    link = headers.get("Link", "")
    m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
    if m:
        return int(m.group(1))
    return len(data)


# --------------------------------------------------------------------------
# Data collection
# --------------------------------------------------------------------------

def iso_utc(dt: Optional[datetime]) -> str:
    if not dt:
        return "n/a"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect() -> Dict[str, Any]:
    """Fetch everything the README needs from the live API."""
    user = gh("/users/" + USER)
    repos = gh(f"/users/{USER}/repos?per_page=100&sort=pushed")
    events = gh(f"/users/{USER}/events?per_page=100")

    # Language bytes across every repo (best effort — never fatal).
    lang_bytes: Dict[str, int] = {}
    for repo in repos:
        try:
            langs = gh(f"/repos/{USER}/{repo['name']}/languages", retries=2)
        except Exception:
            continue
        for name, size in langs.items():
            lang_bytes[name] = lang_bytes.get(name, 0) + size

    pushes = [e for e in events if e.get("type") == "PushEvent"]
    commits_from_events = sum(len(e.get("payload", {}).get("commits", [])) for e in pushes)

    # True total commit count across every repo, via Link-header pagination.
    # (The events API ignores bot-authored commits, so we count the real
    # history instead — best effort, never fatal.)
    commits_total = 0
    for repo in repos:
        try:
            commits_total += repo_commit_count(repo["name"])
        except Exception:
            continue

    return {
        "user": user,
        "repos": [
            {
                "name": r["name"],
                "description": r.get("description") or "",
                "language": r.get("language") or "—",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "pushed_at": (r.get("pushed_at") or "")[:10],
                "fork": r.get("fork", False),
            }
            for r in repos
        ],
        "events": {
            "commits_total": commits_total or commits_from_events,
            "last_push": max((r.get("pushed_at", "")[:10] for r in repos), default="n/a"),
        },
        "lang_bytes": lang_bytes,
        "source": "live",
    }


def cache_snapshot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fall back to the last cached snapshot when the API is unreachable."""
    if SNAPSHOT_PATH.exists():
        try:
            cached = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            cached["source"] = "cache"
            return cached
        except Exception:
            pass
    raise RuntimeError("no live data and no cached snapshot available")


# --------------------------------------------------------------------------
# History / streak
# --------------------------------------------------------------------------

def load_history() -> List[str]:
    if HISTORY_PATH.exists():
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            return list(data.get("dates", []))
        except Exception:
            pass
    return []


def update_history(dates: List[str], today: str) -> List[str]:
    if today not in dates:
        dates.append(today)
    # Keep the newest 400 days — plenty for a streak years long.
    return sorted(set(dates))[-400:]


def streak(dates: List[str], today: str) -> int:
    """Consecutive daily auto-updates ending today (honest: 0 if broken)."""
    wanted = datetime.fromisoformat(today).date()
    days = {datetime.fromisoformat(d).date() for d in dates}
    count = 0
    while wanted in days:
        count += 1
        wanted -= timedelta(days=1)
    return count


# --------------------------------------------------------------------------
# Text rendering (pure functions — easy to verify)
# --------------------------------------------------------------------------

W = 47  # interior width of the ASCII box


def box_line(text: str = "") -> str:
    return "│" + str(text)[:W].ljust(W) + "│"


def render_snapshot(summary: Dict[str, Any], updated: datetime) -> str:
    ist = updated.astimezone(IST)
    title = " DAILY SNAPSHOT · LIVE DATA "
    # Interior width is W; the leading ─ plus the title occupy 1 + len(title),
    # so the trailing run of ─ must fill the remainder.
    top = "┌─" + title + "─" * (W - 1 - len(title)) + "┐"
    mid = "├" + "─" * W + "┤"
    bot = "└" + "─" * W + "┘"
    streak_text = f"{summary['streak']}d"
    lines = [
        "```text",
        top,
        box_line(f" {ist.strftime('%d %b %Y')} · {ist.strftime('%H:%M')} IST"),
        box_line(f" {updated.strftime('%d %b %Y')} · {updated.strftime('%H:%M')} UTC"),
        box_line(f" Public repos ..... {summary['repos']}"),
        box_line(f" Followers ........ {summary['followers']}"),
        box_line(f" Total stars ...... {summary['stars']}"),
        box_line(f" Commits (all) ... {summary['commits_total']}"),
        box_line(f" Top language ..... {summary['top_lang']}"),
        box_line(f" Last push ........ {summary['last_push']}"),
        box_line(f" Auto-update ...... {streak_text}"),
        mid,
        box_line(" Generated by GitHub Actions — no hands"),
        box_line(" were involved."),
        bot,
        "```",
    ]
    return "\n".join(lines)


def render_repo_index(summary: Dict[str, Any], updated: datetime) -> str:
    rows = []
    for r in summary["repo_rows"]:
        rows.append(
            f"| [{r['name']}](https://github.com/{USER}/{r['name']}) "
            f"| {r['language']} | {r['stars']} ⭐ | {r['pushed_at']} |"
        )
    block = "\n".join(
        [
            "<!--REPO-INDEX:START-->",
            f"**{summary['repos']} public repos · {summary['followers']} followers — "
            "table rebuilt from the live GitHub API.**",
            "",
            "| Repository | Language | Stars | Last push |",
            "|------------|----------|-------|-----------|",
            *rows,
            "",
            f"<sub>🤖 Auto-updated {updated.strftime('%d %b %Y %H:%M')} UTC — "
            f"[workflow](https://github.com/{USER}/{USER}/blob/main/.github/workflows/daily-update.yml)</sub>",
            "<!--REPO-INDEX:END-->",
        ]
    )
    return block


def render_lang_pie(lang_bytes: Dict[str, int], updated: datetime) -> str:
    total = sum(lang_bytes.values()) or 1
    ordered = sorted(
        ((k, v) for k, v in lang_bytes.items() if v / total >= 0.005),
        key=lambda kv: kv[1],
        reverse=True,
    )
    rows = [f'    "{name}" : {round(size / 1024, 1)}' for name, size in ordered]
    if not rows:
        rows = ['    "—" : 1']
    lines = [
        "<!--LANG-PIE:START-->",
        "```mermaid",
        "pie showData",
        "    title Code by language (KB, all repos) — auto-updated",
        *rows,
        "```",
        f"<sub>🤖 Regenerated from the live language API, {updated.strftime('%d %b %Y')}.</sub>",
        "<!--LANG-PIE:END-->",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# README patching
# --------------------------------------------------------------------------

def patch(readme: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.S)
    if not pattern.search(readme):
        raise SystemExit(f"missing marker block {start} in README.md — add it first")
    return pattern.sub(lambda _: block, readme, count=1)


def main() -> int:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    try:
        raw = collect() if not MOCK else {
            "user": {"public_repos": 5, "followers": 12},
            "repos": [],
            "events": {"commits_total": 42, "last_push": today},
            "lang_bytes": {"JavaScript": 1000, "CSS": 500},
            "source": "mock",
        }
    except Exception as exc:
        print(f"[warning] live fetch failed ({exc}); using cached snapshot")
        raw = cache_snapshot()

    if raw["source"] == "live":
        dates = update_history(load_history(), today)
    else:
        dates = load_history()
        today = None  # cached runs never extend the streak

    summary: Dict[str, Any] = {
        "repos": raw["user"].get("public_repos", 0),
        "followers": raw["user"].get("followers", 0),
        "stars": sum(r["stars"] for r in raw["repos"]),
        "commits_total": raw["events"]["commits_total"],
        "last_push": raw["events"]["last_push"],
        "top_lang": max(raw.get("lang_bytes", {}), key=raw["lang_bytes"].get)
        if raw.get("lang_bytes") else "n/a",
        "streak": streak(dates, today) if today else (raw.get("streak") or 0),
        "repo_rows": [r for r in raw["repos"] if not r.get("fork")],
        "source": raw["source"],
        "generated_at": iso_utc(now),
    }

    # Persist a machine-readable snapshot + history (they are also committed).
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_record = {
        "generated_at": summary["generated_at"],
        "source": summary["source"],
        "dates": dates,
        "summary": {k: v for k, v in summary.items() if k != "repo_rows"},
        "repos": summary["repo_rows"],
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot_record, indent=2) + "\n", encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps({"dates": dates}, indent=2) + "\n", encoding="utf-8")

    # Patch README, writing only when something actually changed.
    readme = README_PATH.read_text(encoding="utf-8")
    readme = patch(readme, "<!--AUTO-UPDATE:START-->", "<!--AUTO-UPDATE:END-->",
                   f"<!--AUTO-UPDATE:START-->\n{render_snapshot(summary, now)}\n<!--AUTO-UPDATE:END-->")
    readme = patch(readme, "<!--REPO-INDEX:START-->", "<!--REPO-INDEX:END-->",
                   render_repo_index(summary, now))
    readme = patch(readme, "<!--LANG-PIE:START-->", "<!--LANG-PIE:END-->",
                   render_lang_pie(raw.get("lang_bytes", {}), now))

    if readme != README_PATH.read_text(encoding="utf-8"):
        README_PATH.write_text(readme, encoding="utf-8")
        print(f"README updated ({summary['source']}) — streak {summary['streak']}d")
    else:
        print(f"README unchanged ({summary['source']}) — streak {summary['streak']}d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
