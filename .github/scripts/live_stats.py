#!/usr/bin/env python3
"""Generate a compact, self-updating GitHub telemetry SVG.

Set MJB_MOCK=1 to generate deterministic-looking local preview data without
making network requests.  The production path uses only Python's standard
library and intentionally degrades to empty values if an API request fails.
"""

import urllib.request
import json
import os
import datetime
import math


OWNER = "Manashjyoti-Bora"
API = "https://api.github.com"
FONT = "ui-monospace,SFMono-Regular,Menlo,DejaVu Sans Mono,Consolas,monospace"
REPO_NAMES = [
    "Manashjyoti-Bora",
    "portfolio",
    "taskflow-enterprise",
    "devhire-pro-ats",
    "nexusmart",
]


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def iso_z(value):
    return value.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ascii_text(value):
    """Keep arbitrary GitHub input safe for XML and the requested glyph set."""
    text = str(value or "").encode("ascii", "replace").decode("ascii")
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&apos;"))


def shorten(value, limit):
    value = ascii_text(value)
    if len(value) <= limit:
        return value
    if limit <= 3:
        return value[:limit]
    return value[:limit - 3] + "..."


def parse_timestamp(value):
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def safe_int(value):
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


def relative_age(value, now):
    then = parse_timestamp(value)
    if not then:
        return "unknown"
    seconds = max(0, int((now - then).total_seconds()))
    if seconds < 60:
        return "now"
    if seconds < 3600:
        return str(seconds // 60) + "m ago"
    if seconds < 86400:
        return str(seconds // 3600) + "h ago"
    if seconds < 2592000:
        return str(seconds // 86400) + "d ago"
    return str(seconds // 2592000) + "mo ago"


def mock_commits():
    now = utc_now()
    messages = [
        "refine telemetry layout and panel spacing",
        "add language aggregation for profile widget",
        "fix workflow update guard",
        "ship initial project dashboard",
        "document local preview mode",
    ]
    result = {}
    for repo_index, repo in enumerate(REPO_NAMES):
        entries = []
        for item in range(1 + (repo_index % 3), 32, 5 + (repo_index % 3)):
            moment = now - datetime.timedelta(days=item, hours=repo_index + 1)
            entries.append({
                "sha": ("%x" % (0x1A2B3C0 + repo_index * 0x110 + item))[:7].ljust(7, "0"),
                "commit": {
                    "message": messages[(repo_index + item) % len(messages)],
                    "author": {"date": iso_z(moment)},
                },
                "author": {"login": OWNER},
            })
        result[repo] = entries
    return result


MOCK_COMMITS = mock_commits()
MOCK_LANGUAGES = {
    "Manashjyoti-Bora": {"Python": 285000, "Jupyter Notebook": 98000, "Shell": 12000},
    "portfolio": {"TypeScript": 164000, "CSS": 62000, "JavaScript": 19000},
    "taskflow-enterprise": {"TypeScript": 410000, "Python": 128000, "CSS": 47000},
    "devhire-pro-ats": {"TypeScript": 338000, "HTML": 84000, "CSS": 59000},
    "nexusmart": {"JavaScript": 301000, "CSS": 96000, "Python": 24000},
}


def mock_response(path):
    """A small offline API fixture used by MJB_MOCK=1."""
    bare = path.split("?", 1)[0]
    if bare == "/users/" + OWNER:
        return {"public_repos": 5}
    if bare == "/users/" + OWNER + "/repos":
        if "page=2" in path:
            return []
        return [
            {
                "name": name,
                "stargazers_count": [4, 13, 7, 5, 9][index],
                "forks_count": [1, 3, 2, 1, 2][index],
                "pushed_at": iso_z(utc_now() - datetime.timedelta(days=index + 1)),
            }
            for index, name in enumerate(REPO_NAMES)
        ]
    parts = bare.strip("/").split("/")
    if len(parts) >= 4 and parts[0] == "repos":
        repo = parts[2]
        if parts[3] == "languages":
            return MOCK_LANGUAGES.get(repo, {})
        if parts[3] == "commits":
            entries = MOCK_COMMITS.get(repo, [])
            if "page=2" in path:
                return []
            if "per_page=1&" in path:
                return entries[:1]
            return entries
    return None


def api_get(path):
    """Return decoded JSON, or None. Every HTTP request is independently safe."""
    if os.environ.get("MJB_MOCK") == "1":
        try:
            return mock_response(path)
        except Exception:
            return None
    token = os.environ.get("GITHUB_TOKEN", "")
    request = urllib.request.Request(
        API + path,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "mjb-live-telemetry-generator",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def paged_repos():
    repos = []
    for page in range(1, 11):
        data = api_get("/users/" + OWNER + "/repos?per_page=100&page=" + str(page))
        if not isinstance(data, list):
            break
        repos.extend(item for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return repos


def repo_commits(repo, since):
    commits = []
    encoded_since = since.replace(":", "%3A")
    for page in range(1, 21):
        path = ("/repos/" + OWNER + "/" + repo + "/commits?since=" + encoded_since
                + "&author=" + OWNER + "&per_page=100&page=" + str(page))
        data = api_get(path)
        if not isinstance(data, list):
            break
        commits.extend(item for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return commits


def latest_commit(repo):
    data = api_get("/repos/" + OWNER + "/" + repo + "/commits?per_page=1&page=1")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return None


def commit_date(commit):
    try:
        return commit["commit"]["author"]["date"]
    except Exception:
        return ""


def collect():
    now = utc_now()
    since_day = (now - datetime.timedelta(days=29)).date()
    since = iso_z(datetime.datetime.combine(
        since_day, datetime.time.min, tzinfo=datetime.timezone.utc
    ))
    user = api_get("/users/" + OWNER)
    repos = paged_repos()
    public_repos = len(repos)
    if isinstance(user, dict) and isinstance(user.get("public_repos"), int):
        public_repos = user["public_repos"]

    language_totals = {}
    daily = {str(since_day + datetime.timedelta(days=index)): 0 for index in range(30)}
    pushed_at = {}
    total_stars = 0
    total_forks = 0
    candidates = []

    for repo_data in repos:
        name = str(repo_data.get("name", ""))
        if not name:
            continue
        pushed_at[name] = str(repo_data.get("pushed_at") or "")
        total_stars += safe_int(repo_data.get("stargazers_count"))
        total_forks += safe_int(repo_data.get("forks_count"))

        languages = api_get("/repos/" + OWNER + "/" + name + "/languages")
        if isinstance(languages, dict):
            for language, byte_count in languages.items():
                try:
                    language_totals[str(language)] = language_totals.get(str(language), 0) + safe_int(byte_count)
                except Exception:
                    pass

        for commit in repo_commits(name, since):
            stamp = parse_timestamp(commit_date(commit))
            if stamp:
                key = str(stamp.astimezone(datetime.timezone.utc).date())
                if key in daily:
                    daily[key] += 1

        current_latest = latest_commit(name)
        if current_latest:
            candidates.append((commit_date(current_latest), name, current_latest))

    candidates.sort(key=lambda item: item[0] or "", reverse=True)
    latest = {"repo": "no commits", "sha": "-------", "message": "awaiting activity", "age": "unknown"}
    if candidates:
        _, repo_name, item = candidates[0]
        try:
            message = str(item["commit"]["message"]).splitlines()[0]
        except Exception:
            message = ""
        latest = {
            "repo": repo_name,
            "sha": str(item.get("sha", "-------"))[:7],
            "message": shorten(message or "no commit message", 52),
            "age": relative_age(commit_date(item), now),
        }

    ordered_daily = [daily[str(since_day + datetime.timedelta(days=index))] for index in range(30)]
    return {
        "repos": max(0, public_repos),
        "stars": max(0, total_stars),
        "forks": max(0, total_forks),
        "daily": ordered_daily,
        "languages": language_totals,
        "pushed_at": pushed_at,
        "latest": latest,
        "synced": now.strftime("%Y-%m-%d %H:%MZ"),
    }


def bar_chart(data, colors):
    values = data["daily"]
    maximum = max(values) if values else 0
    total = sum(values)
    baseline = 246
    chart_top = 119
    chart_height = baseline - chart_top
    left = 43
    step = 11
    bar_width = 7
    parts = []
    for grid_y in (119, 151, 183, 215, 246):
        parts.append('<line x1="43" y1="{0}" x2="373" y2="{0}" stroke="{1}" stroke-width="1"/>'.format(grid_y, colors["grid"]))
    for index, value in enumerate(values):
        height = 0 if value <= 0 or maximum == 0 else max(2, int(math.ceil(chart_height * value / maximum)))
        y = baseline - height
        delay = "{:.2f}s".format(index * 0.03)
        x = left + index * step
        parts.append(
            '<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{emerald}">'
            '<animate attributeName="height" from="0" to="{h}" begin="{delay}" dur="1.4s" fill="freeze"/>'
            '<animate attributeName="y" from="{base}" to="{y}" begin="{delay}" dur="1.4s" fill="freeze"/>'
            '</rect>'.format(x=x, base=baseline, w=bar_width, emerald=colors["emerald"],
                            h=height, y=y, delay=delay)
        )
    return "\n".join(parts), maximum, total


def language_block(data, colors, uid):
    items = sorted(data["languages"].items(), key=lambda item: item[1], reverse=True)[:5]
    total = sum(max(0, count) for _, count in items)
    if not items or total <= 0:
        return (
            '<rect x="434" y="100" width="332" height="14" rx="7" fill="{grid}"/>'
            '<text x="434" y="143" fill="{dim}" font-size="12">no language data</text>'
        ).format(**colors)
    palette = [colors["cyan"], colors["emerald"], colors["violet"], colors["amber"], colors["dim"]]
    segments = [
        '<defs><clipPath id="lang-clip-{0}"><rect x="434" y="100" width="332" height="14" rx="7"/></clipPath></defs>'.format(uid),
        '<rect x="434" y="100" width="332" height="14" rx="7" fill="{grid}"/>'.format(**colors),
        '<g clip-path="url(#lang-clip-{0})">'.format(uid),
    ]
    cursor = 434.0
    for index, (_, byte_count) in enumerate(items):
        width = 332.0 * byte_count / total
        delay = "{:.2f}s".format(index * 0.12)
        segments.append(
            '<rect x="{x:.2f}" y="100" width="{width:.2f}" height="14" fill="{color}">'
            '<animate attributeName="width" from="0" to="{width:.2f}" begin="{delay}" dur="1.1s" fill="freeze"/>'
            '</rect>'.format(x=cursor, width=width, color=palette[index], delay=delay)
        )
        cursor += width
    segments.append("</g>")
    for index, (language, byte_count) in enumerate(items):
        y = 143 + index * 20
        label = shorten(language, 24)
        percent = 100.0 * byte_count / total
        segments.extend([
            '<circle cx="439" cy="{0}" r="4" fill="{1}"/>'.format(y - 4, palette[index]),
            '<text x="450" y="{0}" fill="{1}" font-size="12">{2}</text>'.format(y, colors["text"], label),
            '<text x="766" y="{0}" text-anchor="end" fill="{1}" font-size="12">{2:.1f}%</text>'.format(y, colors["dim"], percent),
        ])
    return "\n".join(segments)


def svg(data, theme):
    dark = {
        "bg": "#05070d", "panel": "#0b1220", "edge": "#17293d", "grid": "#0e1a2b",
        "text": "#cbd5e1", "dim": "#5b6b80", "bright": "#f1f5f9", "emerald": "#10b981",
        "cyan": "#22d3ee", "violet": "#8b5cf6", "amber": "#f59e0b", "chrome": "#0a121e",
    }
    light = {
        "bg": "#f6f8fb", "panel": "#ffffff", "edge": "#d7e0ea", "grid": "#e4ebf3",
        "text": "#243040", "dim": "#7b8798", "bright": "#0b1220", "emerald": "#059669",
        "cyan": "#0891b2", "violet": "#7c3aed", "amber": "#b45309", "chrome": "#e9eef5",
    }
    colors = dark if theme == "dark" else light
    chart, maximum, total = bar_chart(data, colors)
    languages = language_block(data, colors, theme)
    latest = data["latest"]
    latest_line = (
        shorten(latest["repo"], 11) + " · " + shorten(latest["sha"], 7) + " · "
        + shorten(latest["message"], 19) + " · " + shorten(latest["age"], 8)
    )
    title = "mjb.os — /var/live/telemetry.json"
    timestamp = "synced " + data["synced"]
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="Live GitHub telemetry for Manashjyoti-Bora">
<rect width="1200" height="300" rx="16" fill="{bg}"/>
<path d="M16 0h1168a16 16 0 0 1 16 16v24H0V16A16 16 0 0 1 16 0Z" fill="{chrome}"/>
<circle cx="26" cy="20" r="5.5" fill="#f43f5e"/><circle cx="46" cy="20" r="5.5" fill="#f59e0b"/><circle cx="66" cy="20" r="5.5" fill="{emerald}"/>
<text x="600" y="24" text-anchor="middle" fill="{dim}" font-family="{font}" font-size="12">{title}</text>
<text x="976" y="24" fill="{dim}" font-family="{font}" font-size="12">{timestamp}</text>
<g font-family="{font}">
  <rect x="24" y="56" width="370" height="212" rx="12" fill="{panel}" fill-opacity=".55" stroke="{edge}"/>
  <rect x="415" y="56" width="370" height="212" rx="12" fill="{panel}" fill-opacity=".55" stroke="{edge}"/>
  <rect x="806" y="56" width="370" height="212" rx="12" fill="{panel}" fill-opacity=".55" stroke="{edge}"/>

  <text x="43" y="80" fill="{bright}" font-size="12">COMMITS · LAST 30 DAYS</text>
  <text x="43" y="100" fill="{dim}" font-size="11">MAX {maximum:02d} · TOTAL {total:02d}</text>
  {chart}

  <text x="434" y="80" fill="{bright}" font-size="12">LANGUAGE MIX</text>
  {languages}

  <text x="825" y="80" fill="{bright}" font-size="12">SIGNAL</text>
  <text x="825" y="108" fill="{text}" font-size="12">repos</text>
  <text x="1157" y="108" text-anchor="end" fill="{bright}" font-size="14">{repos}</text>
  <line x1="825" y1="119" x2="1157" y2="119" stroke="{grid}"/>
  <text x="825" y="139" fill="{text}" font-size="12">stars</text>
  <text x="1157" y="139" text-anchor="end" fill="{bright}" font-size="14">{stars}</text>
  <line x1="825" y1="150" x2="1157" y2="150" stroke="{grid}"/>
  <text x="825" y="170" fill="{text}" font-size="12">forks</text>
  <text x="1157" y="170" text-anchor="end" fill="{bright}" font-size="14">{forks}</text>
  <line x1="825" y1="182" x2="1157" y2="182" stroke="{grid}"/>
  <text x="825" y="202" fill="{dim}" font-size="11">LATEST COMMIT</text>
  <circle cx="830" cy="217" r="4" fill="{emerald}"><animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite"/></circle>
  <text x="842" y="221" fill="{text}" font-size="9.5">{latest_line}</text>
</g>
</svg>
""".format(font=FONT, title=title, timestamp=timestamp, chart=chart, languages=languages,
           maximum=maximum, total=total, repos=data["repos"], stars=data["stars"], forks=data["forks"],
           latest_line=latest_line, **colors)


def main():
    try:
        data = collect()
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        assets = os.path.join(root, "assets")
        os.makedirs(assets, exist_ok=True)
        for theme in ("dark", "light"):
            path = os.path.join(assets, "live-" + theme + ".svg")
            with open(path, "w", encoding="utf-8") as output:
                output.write(svg(data, theme))
        print("live-stats: wrote live-dark.svg and live-light.svg "
              "(repos=%s stars=%s forks=%s)"
              % (data["repos"], data["stars"], data["forks"]))
    except Exception as exc:
        # A telemetry failure must never make the scheduled GitHub workflow
        # fail — but say so in the log instead of vanishing silently.
        print("live-stats: generation failed (%s) — keeping previous widgets" % exc)


if __name__ == "__main__":
    main()
