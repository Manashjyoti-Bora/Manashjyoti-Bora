# Install — one-time setup, then fully automatic

You do this **once**. After that the profile updates itself every single day.
No laptop, no manual merge, no remembering anything — GitHub Actions is the
only worker, and it never sleeps.

## 1. Make sure the repo is on `main`

The workflows only run on `main`. Push this commit there (a normal PR merge
is fine — everything below is already wired).

## 2. Grant the workflow write permission

Nothing to do manually: `.github/workflows/daily-update.yml` declares
`permissions: contents: write`, so GitHub automatically grants it a token
that can commit and push. Other workflows do the same.

## 3. (Recommended) Clean the junk

The repo previously tracked `__pycache__` build artifacts. This repo's
`.gitignore` already excludes them; the `.pyc` files have been removed.

## What runs automatically (nothing to do daily)

| Workflow | File | Schedule | What it updates |
|----------|------|----------|-----------------|
| **Daily self-update** | `.github/workflows/daily-update.yml` | 02:30 UTC daily | README snapshot, repo index, language pie, `assets/data/snapshot*.json` |
| Live telemetry | `.github/workflows/live-stats.yml` | every 6 h | `assets/live-dark.svg` / `live-light.svg` terminal card |
| Blueprint sheets | `.github/workflows/sheet.yml` | every 6 h | `assets/data/asbuilt.json`, report, sheet SVGs |
| Signature margin | `.github/workflows/guestbook.yml` | every 12 h + on issues | visitor signatures in the sheet |
| Snake | `.github/workflows/snake.yml` | 00:05 UTC daily | snake contribution animation (`output` branch) |
| Pac-Man | `.github/workflows/pacman.yml` | 00:10 UTC daily | pac-man contribution animation (`output` branch) |
| 3D city | `.github/workflows/profile-3d.yml` | 03:00 UTC daily | `profile-3d-contrib/*.svg` |

## Why it never breaks (even when bots race)

- Every push goes through `.github/scripts/push-safe.sh`, which commits,
  **fetches the latest `main`, rebases on top of it and retries up to 8
  times** (aborting any half-finished rebase between attempts). Concurrency
  groups serialize same-family workflows, so even when all seven pipelines
  fire on the same push, no push stays rejected as "non-fast-forward".
- `scripts/update_readme.py` falls back to the last cached snapshot if the
  GitHub API is unreachable — the daily heartbeat still beats.
- The README keeps the marker blocks (`AUTO-UPDATE`, `REPO-INDEX`, `LANG-PIE`).
  **Never hand-edit between the markers** — the bot owns those regions and
  regenerates them from live data.

## The honest streak

`assets/data/snapshot-history.json` records one entry per successful daily
run. If the pipeline ever stops, the `Auto-update` counter stops too. That is
intentional: the profile only claims what its own automation proves.

## Verify

1. `Actions → Daily README Self-Update → Run workflow` (or just wait a day).
2. Open the profile: the DAILY SNAPSHOT box, repository table and language
   pie are now all real, generated numbers.
3. Check `https://github.com/<user>?tab=contributions` — the bot's own
   commits keep the graph green every day.
