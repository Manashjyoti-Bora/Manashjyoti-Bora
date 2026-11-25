"""preview.py - render every sheet to PNG so a human can look at it.

Kept out of the pipeline: this is the local review aid, not a workflow step.
The sheets themselves stay pure SVG; this only rasterises them.

    python3 -m venv .venv-preview && .venv-preview/bin/pip install resvg-py
    .venv-preview/bin/python art/preview.py             # -> artifacts/*.png
    .venv-preview/bin/python art/preview.py --scale 2

resvg loads no system fonts on a bare Linux box, so pass a font directory that
contains Inter and JetBrains Mono (the two families the drawings ask for).
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "artifacts")


def main() -> int:
    ap = argparse.ArgumentParser(description="rasterise the generated sheets")
    ap.add_argument("--fonts", default="/tmp/fonts", help="directory of .ttf files")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--only", default="", help="comma-separated substring filter")
    args = ap.parse_args()

    try:
        import resvg_py
    except ImportError:
        print("preview: install resvg-py first (see the docstring)", file=sys.stderr)
        return 2

    wanted = [w.strip() for w in args.only.split(",") if w.strip()]
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(ROOT, "assets", "*.svg")))
    if wanted:
        files = [f for f in files if any(w in os.path.basename(f) for w in wanted)]
    for path in files:
        with open(path, encoding="utf-8") as fh:
            svg = fh.read()
        png = resvg_py.svg_to_bytes(
            svg_string=svg,
            font_dirs=[args.fonts] if os.path.isdir(args.fonts) else [],
            skip_system_fonts=os.path.isdir(args.fonts),
            zoom=args.scale,
        )
        name = os.path.splitext(os.path.basename(path))[0] + ".png"
        with open(os.path.join(OUT, name), "wb") as fh:
            fh.write(bytes(png))
        print("  " + name)
    print(f"preview: {len(files)} sheets in {os.path.relpath(OUT, ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
