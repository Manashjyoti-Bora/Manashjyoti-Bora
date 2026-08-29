#!/usr/bin/env python3
"""Build a genuine cross-repository as-built commit log using git only."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "assets" / "data" / "asbuilt.json"
README_PATH = ROOT / "README.md"
OWNER = "Manashjyoti-Bora"
REPOSITORIES = (
    "portfolio",
    "taskflow-enterprise",
    "devhire-pro-ats",
    "nexusmart",
    "Manashjyoti-Bora",
)
REPO_WIDTH = 20


def utc_now() -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def run(command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, cwd=str(cwd) if cwd else None, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def subject_text(value: str) -> str:
    """Keep one log commit per physical output line."""
    return " ".join(value.split()).strip()[:52]


def collect_repo(
    repository: str, directory: Path
) -> Tuple[List[Tuple[dt.datetime, str, str]], Optional[str]]:
    """Clone a bare remote and return all its commits with author datetimes."""
    target = directory / (repository + ".git")
    url = "https://github.com/%s/%s.git" % (OWNER, repository)
    clone = run([
        "git", "clone", "--bare", "--filter=blob:none", "--quiet", url, str(target),
    ])
    if clone.returncode != 0:
        reason = (clone.stderr or clone.stdout or "git clone failed").strip()
        return [], "%s: %s" % (repository, reason[:400])
    log = run([
        "git", "-C", str(target), "log", "HEAD", "--format=%aI%x1f%s",
    ])
    if log.returncode != 0:
        reason = (log.stderr or log.stdout or "git log failed").strip()
        return [], "%s: %s" % (repository, reason[:400])
    commits = []
    for line in log.stdout.splitlines():
        if "\x1f" not in line:
            continue
        authored, subject = line.split("\x1f", 1)
        try:
            date = dt.datetime.fromisoformat(authored.replace("Z", "+00:00"))
        except ValueError:
            continue
        commits.append((date, repository, subject_text(subject)))
    return commits, None


def line_for_commit(commit: Tuple[dt.datetime, str, str]) -> str:
    date, repository, subject = commit
    return "%s  %-*s  %s" % (
        date.date().isoformat(), REPO_WIDTH, repository, subject,
    )


def weekly_counts(commits: List[Tuple[dt.datetime, str, str]]) -> List[Dict[str, object]]:
    counts: Dict[str, int] = {}
    for authored, unused_repo, unused_subject in commits:
        local_date = authored.date()
        monday = local_date - dt.timedelta(days=local_date.isoweekday() - 1)
        key = monday.isoformat()
        counts[key] = counts.get(key, 0) + 1
    return [
        {"week_start": week, "count": counts[week]}
        for week in sorted(counts)
    ]


def fenced_log(lines: List[str]) -> str:
    return "```text\n%s\n```" % "\n".join(lines)


def weekly_mermaid(weekly: List[Dict[str, object]]) -> str:
    labels = ", ".join(
        '"%s"' % str(item["week_start"]) for item in weekly
    )
    values = ", ".join(str(int(item["count"])) for item in weekly)
    maximum = max([int(item["count"]) for item in weekly] or [1])
    return (
        "```mermaid\nxychart-beta\n"
        '    x-axis [%s]\n'
        '    y-axis "commits" 0 --> %d\n'
        "    bar [%s]\n"
        "```"
    ) % (labels, maximum, values)


def replace_between(
    text: str, start: str, end: str, replacement: str
) -> Optional[str]:
    first = text.find(start)
    second = text.find(end)
    if first < 0 or second < 0 or second < first:
        return None
    before = text[:first + len(start)]
    after = text[second:]
    return before + "\n" + replacement + "\n" + after


def update_readme(lines: List[str], weekly: List[Dict[str, object]]) -> bool:
    """Update both marker sections only when both are present."""
    if not README_PATH.is_file():
        print("asbuilt: README.md markers absent; README left unchanged")
        return False
    original = README_PATH.read_text(encoding="utf-8")
    with_log = replace_between(
        original, "<!-- ASBUILT:START -->", "<!-- ASBUILT:END -->", fenced_log(lines)
    )
    if with_log is None:
        print("asbuilt: README.md markers absent; README left unchanged")
        return False
    completed = replace_between(
        with_log, "<!-- WEEKLY:START -->", "<!-- WEEKLY:END -->", weekly_mermaid(weekly)
    )
    if completed is None:
        print("asbuilt: README.md markers absent; README left unchanged")
        return False
    README_PATH.write_text(completed, encoding="utf-8")
    print("asbuilt: README.md marker sections updated")
    return True


def main() -> int:
    all_commits: List[Tuple[dt.datetime, str, str]] = []
    errors: List[str] = []
    with tempfile.TemporaryDirectory(prefix="blueprint-asbuilt-") as temporary:
        directory = Path(temporary)
        for repository in REPOSITORIES:
            commits, error = collect_repo(repository, directory)
            all_commits.extend(commits)
            if error:
                errors.append(error)

    all_commits.sort(key=lambda item: item[0], reverse=True)
    log_lines = [line_for_commit(item) for item in all_commits[:18]]
    weekly = weekly_counts(all_commits)
    record = {
        "generated_at": utc_now(),
        "log_lines": log_lines,
        "weekly": weekly,
        "total": len(all_commits),
        "errors": errors,
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    update_readme(log_lines, weekly)
    print("asbuilt: %d commits collected; %d log lines written" % (
        len(all_commits), len(log_lines),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
