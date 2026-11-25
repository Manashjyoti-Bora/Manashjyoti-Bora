"""findings.py - self-review every repo and publish what it found.

Walks the root of each owned repository through the Git trees API (one call
per repo, plus the last commit's date from the repo metadata), and checks for
the boring things that actually break projects:

  readme      a README in the root
  env-in-git  a tracked file named .env / .env.local (a real leak)
  license     any licence file
  ci          .github/workflows or a pipeline file
  tests       a tests folder or *.test.* / *_test.py near the root
  gitignore   a .gitignore
  manifest    package.json / pyproject.toml / requirement*.txt / Cargo.toml / go.mod

Result: assets/data/findings.json (the full list) and the "self-review" number
the README quotes. It is a hygiene score of the profile, not a grade of the work:
an empty learning repo is allowed to miss tests.

Run:  python3 .github/scripts/findings.py
"""

from __future__ import annotations

import json
import os

import ghub

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "data", "findings.json")

CHECKS = ["readme", "gitignore", "license", "ci", "tests", "manifest"]


def classify(names: list) -> dict:
    low = [n.lower() for n in names]
    joined = " ".join(low)
    return {
        "readme": any(n.startswith("readme") for n in low),
        "gitignore": ".gitignore" in low,
        "license": any(n.startswith(("license", "licence", "copying")) for n in low),
        "ci": any(n.startswith(".github/workflows") or n in ("vercel.json", "netlify.toml", "dockerfile")
                  or n.endswith((".gitea", ".gitlab-ci.yml", "jenkinsfile")) for n in low),
        "tests": any(n.startswith(("tests/", "test/", "__tests__/", "spec/"))
                     or n.split("/")[-1].startswith(("test_", "conftest", "vitest", "jest"))
                     or n.split("/")[-1].endswith((".test.ts", ".test.js", ".test.tsx", ".spec.ts", ".spec.js"))
                     for n in low),
        "manifest": any(n in ("package.json", "pyproject.toml", "setup.py", "cargo.toml", "go.mod", "composer.json")
                        or n.startswith(("requirements", "pipfile")) for n in low),
        "env_in_git": any(n in (".env", ".env.local", ".env.production") for n in low),
        "_names": joined[:0],
    }


def mock() -> dict:
    return {
        "generated_at": "mock",
        "source": "mock",
        "repos": [
            {"name": "Manashjyoti-Bora", "score": 6, "passed": CHECKS, "env_in_git": False,
             "pushed_at": "2026-11-25", "size_kb": 412},
            {"name": "aurevyn-store", "score": 6, "passed": CHECKS, "env_in_git": False,
             "pushed_at": "2026-11-24", "size_kb": 2680},
        ],
        "summary": {"repos": 2, "checks_passed": 12, "checks_possible": 12, "env_leaks": 0,
                    "dirty_repos": []},
    }


def live() -> dict:
    repos_out = []
    for repo in ghub.repos():
        name = repo["name"]
        try:
            branch = repo.get("default_branch") or "main"
            tree = ghub.get(f"/repos/{ghub.USER}/{name}/git/trees/{branch}?recursive=0", allow_404=True) or {}
            names = [t.get("path", "") for t in tree.get("tree", [])]
            try:
                gh_dir = ghub.get(f"/repos/{ghub.USER}/{name}/contents/.github/workflows", allow_404=True) or []
                names += [".github/workflows/" + c.get("name", "") for c in gh_dir if isinstance(c, dict)]
            except Exception:
                pass
        except Exception:
            names = []
        found = classify(names)
        passed = [c for c in CHECKS if found.get(c)]
        repos_out.append({
            "name": name,
            "score": len(passed),
            "passed": passed,
            "env_in_git": bool(found.get("env_in_git")),
            "pushed_at": (repo.get("pushed_at") or "")[:10],
            "size_kb": repo.get("size", 0),
        })
    possible = len(repos_out) * len(CHECKS)
    passed = sum(r["score"] for r in repos_out)
    dirty = [r["name"] for r in repos_out if r["env_in_git"]]
    return {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "live",
        "repos": repos_out,
        "summary": {"repos": len(repos_out), "checks_passed": passed, "checks_possible": possible,
                    "env_leaks": len(dirty), "dirty_repos": dirty},
    }


def main() -> int:
    data = mock() if os.environ.get("FINDINGS_MOCK") else live()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    s = data["summary"]
    pct = 0 if not s["checks_possible"] else round(100 * s["checks_passed"] / s["checks_possible"])
    print(f"findings: {s['checks_passed']}/{s['checks_possible']} checks passed ({pct}%), "
          f"{s['env_leaks']} env leak(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
