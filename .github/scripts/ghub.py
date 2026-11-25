"""ghub.py - one tiny GitHub REST client shared by every automation script.

No third-party dependencies: the standard library plus an optional token.
A token is never required for reading public data, but it lifts the anonymous
rate limit from 60 to 5,000 requests/hr, so every workflow passes one in.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

USER = "Manashjyoti-Bora"
API = "https://api.github.com"
UA = "mjb-profile-bot (+https://github.com/Manashjyoti-Bora)"


class GhError(RuntimeError):
    pass


def token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def get(path: str, retries: int = 3, allow_404: bool = False):
    """GET an API path. Retries on 5xx / secondary rate limits, returns None on 404."""
    url = path if path.startswith("http") else API + path
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
            **({"Authorization": "Bearer " + token()} if token() else {}),
        })
        try:
            with urllib.request.urlopen(req, timeout=25) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_404:
                return None
            if exc.code == 403 and "rate limit" in (exc.headers.get("x-ratelimit-remaining", "") or ""):
                pass
            last = exc
            if exc.code in (403, 429, 500, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            raise GhError(f"GET {url} -> {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise GhError(f"GET {url} failed: {last}")


def paged(path: str, cap: int = 500, per_page: int = 100) -> list:
    """Concatenate pages until short/empty or `cap` items."""
    out: list = []
    page = 1
    sep = "&" if "?" in path else "?"
    while len(out) < cap:
        batch = get(f"{path}{sep}per_page={per_page}&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return out[:cap]


def user() -> dict:
    return get(f"/users/{USER}")


def repos() -> list:
    """Owned, non-fork repositories, freshest push first."""
    data = paged(f"/users/{USER}/repos?sort=pushed&type=owner", cap=200)
    return [r for r in data if not r.get("fork")]


def commit_count(name: str) -> int:
    """Count commits without downloading the history: walk the last page."""
    path = f"/repos/{USER}/{name}/commits?per_page=1"
    url = API + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
        **({"Authorization": "Bearer " + token()} if token() else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            link = res.headers.get("Link", "")
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 409):
            return 0
        raise GhError(f"commits {name} -> {exc.code}") from exc
    # Rel pages: <...&page=12>; rel="last"}
    tail = link.rsplit("page=", 1)[-1].split(">")[0] if "page=" in link else ""
    if tail.isdigit():
        return int(tail)
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            return 1 if json.loads(res.read().decode("utf-8")) else 0
    except Exception:
        return 0


def contributions_by_day() -> dict:
    """Public contribution calendar (includes bot commits).

    GitHub has no plain REST endpoint for this; the HTML calendar is parsed
    with a fixed, conservative regex. If the markup ever changes the caller
    gets {} and falls back to counting commits itself.
    """
    import re
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            html = res.read().decode("utf-8", "replace")
    except Exception:
        return {}
    days = {}
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', html):
        days[m.group(1)] = int(m.group(2))
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"', html):
        days.setdefault(m.group(1), 0)
    # the tooltip carries the exact count: "12 contributions on November 2nd."
    for m in re.finditer(r'(\d+) contributions? on (\w+ \d+\w*, \d{4})', html):
        try:
            from datetime import datetime
            d = datetime.strptime(m.group(2).replace("st,", ",").replace("nd,", ",")
                                  .replace("rd,", ",").replace("th,", ","), "%B %d, %Y")
            days[d.strftime("%Y-%m-%d")] = int(m.group(1))
        except Exception:
            continue
    return days


def streak(dates: list) -> int:
    """Consecutive days ending today (or yesterday, before the first commit)."""
    if not dates:
        return 0
    from datetime import date, timedelta
    have = set(dates)
    today = date.today()
    cursor = today if today.isoformat() in have else today - timedelta(days=1)
    n = 0
    while cursor.isoformat() in have:
        n += 1
        cursor -= timedelta(days=1)
    return n
