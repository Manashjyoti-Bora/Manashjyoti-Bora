#!/usr/bin/env bash
# commit.sh - serialise every bot write into one rebased, retried push.
#
# The old setup had each workflow committing and pushing on its own schedule.
# On a shared crontab some runs land in the same minute, so one push loses the
# race and its commit simply never happens ("Updates were rejected"). This
# wrapper makes a loss impossible *and* makes a collision harmless:
#
#   1. stage everything the run produced; nothing to commit -> exit 0,
#   2. fetch the newest origin state,
#   3. if origin already lists a path we touched, that path is GENERATED, so
#      it is recomputed from source instead of merged (a merge of a generated
#      SVG is a corrupt SVG) - see `rebuild` in art/universe.py - and the last
#      local commit is replaced,
#   4. rebase the rest onto origin, commit, push,
#   5. on rejection, go back to step 2 with exponential backoff.
#
# Before anything is pushed, doctor.py must pass: a bot never publishes a
# broken tree.
#
# Usage:  bash .github/scripts/commit.sh "chore: message"
# Env:    MAX_TRIES (default 5), REBUILD (default: python3 art/universe.py --refresh)
set -uo pipefail

msg="${1:-chore: automated profile refresh}"
tries="${MAX_TRIES:-5}"
branch="$(git rev-parse --abbrev-ref HEAD)"
rebuild="${REBUILD:-python3 art/universe.py --refresh}"

# something to stage maybe? untracked/modified files, or a commit waiting to go
if [ -z "$(git status --porcelain)" ]; then
  echo "commit.sh: nothing to commit"
  exit 0
fi

git config user.name  "mjb-profile-bot"
git config user.email "github-actions[bot]@users.noreply.github.com"

for i in $(seq 1 "$tries"); do
  git add -A

  # newest origin, without touching the working tree yet
  if ! git fetch --quiet origin "$branch"; then
    echo "commit.sh: fetch failed on attempt $i, retrying"
    sleep $((i * 2))
    continue
  fi

  # paths this run produced, plus anything in a commit we have not pushed yet
  touched="$(git diff --cached --name-only; git diff --name-only "origin/$branch"...HEAD 2>/dev/null)"
  collided=""
  for path in $touched; do
    if git cat-file -e "origin/$branch:$path" 2>/dev/null; then
      case "$path" in
        assets/*|README.md) collided="$collided $path" ;;
      esac
    fi
  done

  if [ -n "$collided" ]; then
    # Generated content moved under us. Never merge it: reset to origin, put
    # the script changes back from our own commit (if any), and recompute every
    # generated file from source.
    echo "commit.sh: origin also changed$collided - recomputing generated files"
    mapfile -t scripts < <(git diff --name-only "origin/$branch"...HEAD -- .github art 2>/dev/null)
    git reset --quiet --soft "origin/$branch" || true
    git reset --quiet
    if [ "${#scripts[@]}" -gt 0 ]; then
      git checkout "origin/$branch" -- "${scripts[@]}" 2>/dev/null || true
    fi
    if ! bash -c "$rebuild" >/dev/null 2>&1; then
      echo "commit.sh: rebuild reported a problem; doctor will decide"
    fi
    git add -A
  fi

  # drop our own local commits and replay them on the fresh origin state
  if ! git rebase --quiet "origin/$branch" >/dev/null 2>&1; then
    echo "commit.sh: conflict while rebasing on origin - rebuilding from source"
    git rebase --abort >/dev/null 2>&1 || true
    git reset --quiet --soft "origin/$branch" || true
    bash -c "$rebuild" >/dev/null 2>&1 || true
    git add -A
  fi

  git add -A
  if git diff --cached --quiet; then
    if [ -n "$(git log --oneline "origin/$branch"..HEAD 2>/dev/null)" ]; then
      :
    else
      echo "commit.sh: nothing left to commit after sync"
      exit 0
    fi
  else
    git commit --quiet -m "$msg" --no-verify
  fi

  # never publish a broken tree
  if ! python3 .github/scripts/doctor.py --strict >/tmp/doctor.log 2>&1; then
    echo "commit.sh: doctor rejected the tree, not pushing"
    sed -n '1,20p' /tmp/doctor.log
    exit 1
  fi

  if git push --quiet origin "HEAD:$branch" 2>/dev/null; then
    echo "commit.sh: pushed «$msg»"
    exit 0
  fi

  echo "commit.sh: push attempt $i rejected, rebuilding on top of origin"
  sleep $((i * 2))
done

echo "commit.sh: gave up after $tries tries; the change will be retried on the next schedule"
exit 1
