#!/usr/bin/env bash
# push-safe.sh — conflict-proof auto-commit & push for GitHub Actions.
#
# Every auto-workflow in this repo pushes to `main` on its own schedule, so
# two of them can start from the same commit and the second push gets
# "non-fast-forward". This helper fixes that: commit, rebase onto the latest
# main, then push with retries. No manual work, ever.
#
# IMPORTANT: commits are authored as the account owner (linked email),
# so they count on the contribution graph. Bot-authored commits do NOT.
#
# Usage:  bash .github/scripts/push-safe.sh "commit message"
set -euo pipefail

MSG="${1:-chore: automated update [skip ci]}"
ATTEMPTS="${PUSH_ATTEMPTS:-5}"
BRANCH="${PUSH_BRANCH:-main}"
REMOTE="${PUSH_REMOTE:-origin}"

git config user.name "${PUSH_USER:-Manashjyoti-Bora}"
git config user.email "${PUSH_EMAIL:-manashjyotibora122@gmail.com}"

git add -A
if git diff --cached --quiet; then
  echo "push-safe: nothing to commit — clean."
  exit 0
fi

git commit -m "$MSG"

for i in $(seq 1 "$ATTEMPTS"); do
  # Bring in anything a sibling workflow pushed while we were working.
  if git pull --rebase --autostash "$REMOTE" "$BRANCH"; then
    if git push "$REMOTE" "HEAD:$BRANCH"; then
      echo "push-safe: pushed to $BRANCH (attempt $i)."
      exit 0
    fi
  fi
  echo "push-safe: attempt $i failed — rebasing & retrying in 15s..."
  sleep 15
done

echo "push-safe: ERROR — could not push after $ATTEMPTS attempts." >&2
exit 1
