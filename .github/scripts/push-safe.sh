#!/usr/bin/env bash
# push-safe.sh — conflict-proof auto-commit & push for GitHub Actions.
#
# Every auto-workflow in this repo pushes to `main` on its own schedule, and
# all of them fire TOGETHER on every push to main. So two (or seven) of them
# can start from the same commit, and the later pushes get
# "non-fast-forward". This helper is built for exactly that storm:
#
#   1. commit the generated changes
#   2. fetch the latest main and rebase our one commit on top
#   3. push; if it lost the race, clean up and retry (up to 8 times)
#
# A previous failed attempt can leave the worktree mid-rebase, which would
# poison every later retry — so a stale rebase is always aborted first.
# No manual work, ever.
#
# Usage:  bash .github/scripts/push-safe.sh "commit message"
set -euo pipefail

MSG="${1:-chore: automated update [skip ci]}"
ATTEMPTS="${PUSH_ATTEMPTS:-8}"
BRANCH="${PUSH_BRANCH:-main}"
REMOTE="${PUSH_REMOTE:-origin}"

git config user.name "${PUSH_USER:-github-actions[bot]}"
git config user.email "${PUSH_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

# A previous failed run can leave this worktree mid-rebase, which would make
# even `git commit` below impossible — always start from a clean state.
abort_stale_rebase() {
  # Clear a half-finished rebase left over from a failed attempt.
  git rebase --abort 2>/dev/null || git rebase --quit 2>/dev/null || true
}
abort_stale_rebase

git add -A
if git diff --cached --quiet; then
  echo "push-safe: nothing to commit — clean."
  exit 0
fi

git commit -m "$MSG"

for i in $(seq 1 "$ATTEMPTS"); do
  abort_stale_rebase
  # Bring in anything a sibling workflow pushed while we were working,
  # then replay our single commit on top of the fresh tip.
  if git fetch "$REMOTE" "$BRANCH" && git rebase "FETCH_HEAD"; then
    if git push "$REMOTE" "HEAD:$BRANCH"; then
      echo "push-safe: pushed to $BRANCH (attempt $i)."
      exit 0
    fi
    echo "push-safe: push rejected (sibling pushed first) — will retry."
  else
    echo "push-safe: rebase onto $BRANCH failed — will retry."
  fi
  abort_stale_rebase
  if [ "$i" -lt "$ATTEMPTS" ]; then
    echo "push-safe: attempt $i/$ATTEMPTS failed — retrying in 15s..."
    sleep 15
  fi
done

echo "push-safe: ERROR — could not push after $ATTEMPTS attempts." >&2
exit 1
