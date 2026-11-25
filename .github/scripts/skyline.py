"""skyline.py - collect the profile numbers every other script and sheet uses.

Writes assets/data/snapshot.json:

    {
      "generated_at": "...Z", "source": "live" | "mock",
      "dates": ["2026-09-04", ...],          # every day with a contribution
      "summary": {repos, followers, stars, commits_total, commits_dev, ...},
      "repos":   [{name, short, commits, language, stars, pushed_at, desc}, ...]
    }

commit counts come from the Link header of /commits?per_page=1, one request
per repo - no paginating thousands of commits. Bot-written commits (authored by
github-actions[bot]) are counted separately so the README can be honest about
how much of this profile is automation.

Run:  python3 .github/scripts/skyline.py
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import ghub

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "data", "snapshot.json")
BOT_LOGIN = "github-actions[bot]"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mock() -> dict:
    import random
    rng = random.Random(2027)
    names = [
        ("Manashjyoti-Bora", "profile", "Python", "the profile you are reading, drawn by code"),
        ("aurevyn-store", "aurevyn", "TypeScript", "resale storefront, admin console, autonomous ops team"),
        ("nexusmart", "nexusmart", "TypeScript", "full-stack commerce with JWT auth and a role-gated admin panel"),
        ("devhire-pro-ats", "devhire", "JavaScript", "applicant tracking UI with multi-attribute filtering"),
        ("taskflow-enterprise", "taskflow", "JavaScript", "kanban boards, live priority tagging, sprints"),
        ("portfolio", "portfolio", "JavaScript", "the portfolio this profile links to"),
    ]
    dates = []
    d = datetime(2026, 9, 4)
    while d.date() <= datetime(2026, 11, 25).date():
        dates.append(d.strftime("%Y-%m-%d"))
        d = d.fromordinal(d.toordinal() + 1)
    repos = []
    for name, short, lang, desc in names:
        repos.append({
            "name": name, "short": short, "language": lang, "stars": rng.randint(0, 3),
            "forks": 0, "pushed_at": "2026-11-25", "desc": desc,
            "commits": rng.randint(12, 940),
        })
    return {
        "generated_at": now_utc(),
        "source": "mock",
        "dates": dates,
        "summary": {
            "repos": len(repos),
            "followers": 10,
            "stars": sum(r["stars"] for r in repos),
            "commits_total": sum(r["commits"] for r in repos),
            "commits_dev": 0,
            "last_push": "2026-11-25",
            "top_lang": "TypeScript",
            "streak": ghub.streak(dates),
        },
        "repos": repos,
    }


def live() -> dict:
    me = ghub.user()
    repo_list = ghub.repos()
    out_repos = []
    total = 0
    dev = 0
    for repo in repo_list:
        count = ghub.commit_count(repo["name"])
        # bot share: look at the most recent 100 commits and count the bot's
        try:
            recent = ghub.get(f"/repos/{ghub.USER}/{repo['name']}/commits?per_page=100")
            bot_recent = sum(1 for c in recent if (c.get("author") or {}).get("login") == BOT_LOGIN)
            bot_ratio = bot_recent / max(1, len(recent))
        except Exception:
            bot_ratio = 0.0
        dev += round(count * (1 - bot_ratio))
        total += count
        out_repos.append({
            "name": repo["name"],
            "short": repo["name"].split("-")[0][:12],
            "language": repo.get("language") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "pushed_at": (repo.get("pushed_at") or "")[:10],
            "desc": repo.get("description") or "",
            "commits": count,
        })
    days = ghub.contributions_by_day()
    dates = sorted(d for d, n in days.items() if n > 0) if days else sorted(
        r["pushed_at"] for r in out_repos if r["pushed_at"])
    langs: dict = {}
    for r in repo_list:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    return {
        "generated_at": now_utc(),
        "source": "live",
        "dates": dates[-84:],
        "summary": {
            "repos": len(repo_list),
            "followers": me.get("followers", 0),
            "stars": sum(r.get("stargazers_count", 0) for r in repo_list),
            "commits_total": total,
            "commits_dev": dev,
            "last_push": max((r["pushed_at"] for r in out_repos), default=""),
            "top_lang": max(langs, key=langs.get) if langs else "",
            "streak": ghub.streak(dates),
        },
        "repos": sorted(out_repos, key=lambda r: r["commits"], reverse=True),
    }


def main() -> int:
    data = mock() if os.environ.get("SKYLINE_MOCK") else live()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    s = data["summary"]
    print(f"skyline: {s['commits_total']:,} commits across {s['repos']} repos "
          f"({s['commits_dev']:,} hand-written), streak {s['streak']}, source={data['source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
