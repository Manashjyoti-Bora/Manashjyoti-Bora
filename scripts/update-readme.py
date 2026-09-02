#!/usr/bin/env python3
"""Auto-updates the LIVE REPO INDEX section of README.md.
Runs daily + on every push via GitHub Actions. No fake data —
everything is pulled from the GitHub API at run time."""
import json, re, urllib.request, datetime

USER = "Manashjyoti-Bora"

def gh(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER, "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

repos = gh(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
user = gh(f"https://api.github.com/users/{USER}")

rows = []
for r in repos:
    if r["fork"]:
        continue
    name = r["name"]
    desc = (r["description"] or "—")[:60]
    lang = r["language"] or "—"
    pushed = r["pushed_at"][:10]
    stars = r["stargazers_count"]
    rows.append(f"| [{name}](https://github.com/{USER}/{name}) | {lang} | {stars} ⭐ | {pushed} |")

now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
block = "\n".join([
    "<!-- REPO-INDEX:START -->",
    f"**{user['public_repos']} public repos · {user['followers']} followers** — table refreshed automatically by GitHub Actions.",
    "",
    "| Repository | Language | Stars | Last push |",
    "|------------|----------|-------|-----------|",
    *rows,
    "",
    f"<sub>🤖 Auto-updated: {now} — [see the workflow](https://github.com/{USER}/{USER}/blob/main/.github/workflows/update-readme.yml)</sub>",
    "<!-- REPO-INDEX:END -->",
])

readme = open("README.md", encoding="utf-8").read()
new = re.sub(r"<!-- REPO-INDEX:START -->.*?<!-- REPO-INDEX:END -->", block, readme, flags=re.S)
if new != readme:
    open("README.md", "w", encoding="utf-8").write(new)
    print("README updated")
else:
    print("No changes")
