"""build_all.py - rebuild every hand-coded SVG on this profile.

    python3 art/build_all.py              # everything, both themes
    python3 art/build_all.py --only header,pulse
    python3 art/build_all.py --out /tmp/x # write elsewhere (used by checks)

Every sheet is deterministic: same inputs, same bytes. That is what lets
.github/workflows/healthcheck.yml fail the moment a drawing drifts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import divider  # noqa: E402
import header  # noqa: E402
import pulse  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(ROOT, "assets")
THEMES = ("aurora", "daylight")

PARTS = {
    "header": lambda theme, out: header.build(theme, header.load()),
    "pulse": lambda theme, out: pulse.build(theme, pulse.read_schedule()),
    "divider": lambda theme, out: divider.build(theme),
}


def write(out_dir: str, name: str, svg: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return len(svg.encode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="rebuild the profile art set")
    ap.add_argument("--only", default="", help="comma list: " + ", ".join(PARTS))
    ap.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    ap.add_argument("--theme", default="", help="aurora or daylight (default: both)")
    args = ap.parse_args()

    wanted = [p.strip() for p in args.only.split(",") if p.strip()] or list(PARTS)
    unknown = [p for p in wanted if p not in PARTS]
    if unknown:
        print(f"build_all: unknown part(s) {unknown}", file=sys.stderr)
        return 2
    themes = (args.theme,) if args.theme else THEMES

    sidecars: dict = {}
    total = 0
    for part in wanted:
        for theme in themes:
            result = PARTS[part](theme, args.out)
            svg, side = result if isinstance(result, tuple) else (result, None)
            if side is not None:
                sidecars.setdefault(part, side)
            size = write(args.out, f"art-{part}-{theme}.svg", svg)
            total += size
            print(f"  art-{part}-{theme}.svg  {size / 1024:6.1f} KB", flush=True)
    if sidecars:
        data_dir = os.path.join(args.out, "data")
        os.makedirs(data_dir, exist_ok=True)
        for part, side in sidecars.items():
            with open(os.path.join(data_dir, f"{part}.json"), "w", encoding="utf-8") as fh:
                json.dump(side, fh, indent=2)
                fh.write("\n")
    print(f"build_all: {len(wanted) * len(themes)} sheets, {total / 1024:.1f} KB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
