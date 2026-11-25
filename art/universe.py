"""universe.py - the one command that rebuilds everything that is generated.

    python3 art/universe.py            # data, then sheets, then README regions
    python3 art/universe.py --refresh  # same, but quietly and from a clean tree
                                       # (used by .github/scripts/commit.sh after
                                       #  it has reset to origin)

Order matters, and it is the same order every workflow uses, so any sheet can be
regenerated on its own without leaving the next one stale:

    1  data      skyline    GitHub API -> assets/data/snapshot.json
                 live       HTTPS probes -> assets/data/live.json
                 findings   repo trees -> assets/data/findings.json
                 postcard   issues -> assets/data/postcards.json
                 daybreak   events -> assets/data/daybreak.json
    2  sheets    art/*.py, ledger, state  (pure drawing over step 1)
    3  text      README regions, build log
    4  verify    doctor.py --strict (nothing is published unless it passes)

Every step is optional at runtime: if the network is down the step prints why
and the rest continues with the last good data, because a stale number with a
timestamp beats a blank page.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

DATA_STEPS = [
    ("skyline", ".github/scripts/skyline.py"),
    ("live", ".github/scripts/live_stats.py"),
    ("findings", ".github/scripts/findings.py"),
    ("postcard", ".github/scripts/postcard.py"),
    ("daybreak", ".github/scripts/daybreak.py"),
]
SHEET_STEPS = [
    ("art", "art/build_all.py"),
    ("ledger", ".github/scripts/ledger.py"),
    ("state", ".github/scripts/state.py"),
]
TEXT_STEPS = [
    ("build log", ".github/scripts/asbuilt.py"),
]
VERIFY_STEPS = [
    ("doctor", ".github/scripts/doctor.py --strict"),
]


def run(label: str, cmd: str, quiet: bool) -> bool:
    args = [PY] + cmd.split()
    result = subprocess.run(args, cwd=ROOT, text=True,
                            stdout=subprocess.DEVNULL if quiet else None,
                            stderr=subprocess.DEVNULL if quiet else None)
    if result.returncode != 0:
        print(f"  ! {label} exited {result.returncode}")
    return result.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="rebuild every generated file")
    ap.add_argument("--refresh", action="store_true", help="quiet, tolerate failures")
    ap.add_argument("--skip-network", action="store_true", help="data steps read local files only")
    args = ap.parse_args()

    steps = ([] if args.skip_network else DATA_STEPS) + SHEET_STEPS + TEXT_STEPS + VERIFY_STEPS
    failed = []
    for label, cmd in steps:
        ok = run(label, cmd, quiet=args.refresh)
        if not ok:
            failed.append(label)
        elif not args.refresh:
            print(f"  {label}: ok")

    if args.refresh:
        return 0
    if failed:
        print(f"universe: {len(failed)} step(s) reported a problem: {', '.join(failed)}")
        return 1
    print(f"universe: {len(steps)} steps, everything regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
