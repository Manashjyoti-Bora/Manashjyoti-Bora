# Install — new README + photo banner

You do this **once**. After that everything is automatic.

## 1. Add the photo (original size)

Upload `assets/photo.jpg` (this folder) into your repo at `assets/photo.jpg`.
It is your original photo, **720 × 718, untouched** — the README shows it at exactly
that size as the banner. Do not rename it.

## 2. Replace the README

Replace the repo's `README.md` with the new `README.md` from this folder.
(The old `assets/hero-dark.svg` / `hero-light.svg` banner files can stay or be deleted —
the new README no longer references them.)

## 3. (Recommended) Clean the junk

The repo currently has committed `__pycache__/` folders and `*.pyc` files.
Copy this folder's `.gitignore` into the repo root, then:

```bash
git rm -r --cached __pycache__ .github/scripts/__pycache__ 2>/dev/null
git commit -m "chore: stop tracking pycache"
```

## What runs automatically (nothing to do daily)

| Workflow | File | Schedule | What it updates |
|----------|------|----------|-----------------|
| Daily self-update | `.github/workflows/daily-update.yml` | 02:30 UTC daily | `README.md` snapshot block (repos, followers, stars, commits, top language) |
| Live telemetry | `.github/workflows/live-stats.yml` | every 6 h | `assets/live-dark.svg` / `live-light.svg` card |
| Snake | `.github/workflows/snake.yml` | 00:00 UTC daily | snake contribution animation |
| Pac-Man | `.github/workflows/pacman.yml` | daily | pac-man contribution animation |
| 3D city | `.github/workflows/profile-3d.yml` | daily | `profile-3d-contrib/*.svg` |

⚠ The README keeps the `<!--AUTO-UPDATE:START-->` / `<!--AUTO-UPDATE:END-->` markers,
so `scripts/update_readme.py` keeps working unchanged. Never hand-edit between them.

## Verified

- All 10 external asset URLs used in the README return HTTP 200.
- `scripts/update_readme.py` was run against this exact `README.md` and replaced the
  snapshot block successfully (live GitHub API data).
