#!/usr/bin/env bash
# Build the Stackable Bins STLs + preview images with Blender (headless), then
# check the STLs with the repo's shared tools.  No OpenSCAD needed.
#
# Usage: tools/build.sh [--no-render] [--slice]
#   --no-render   skip the preview PNGs
#   --slice       also run ../../tools/slice.py (needs Bambu Studio installed)
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$(cd ../.. && pwd)"   # shared tools live in <repo>/tools
mkdir -p build

BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
if [ ! -x "$BLENDER" ]; then
  BLENDER="$(command -v blender || true)"
fi
if [ -z "$BLENDER" ]; then
  echo "Blender not found. Set BLENDER=/path/to/blender" >&2
  exit 1
fi

SLICE=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --slice) SLICE=1 ;;
    *) ARGS+=("$a") ;;
  esac
done

echo "== Blender build"
"$BLENDER" -b --python-exit-code 1 -P tools/build_stl.py -- "${ARGS[@]+"${ARGS[@]}"}" > build/blender.log 2>&1 || {
  echo "Blender build FAILED; last lines of build/blender.log:" >&2
  tail -n 30 build/blender.log >&2
  exit 1
}
grep -E 'stackable|wrote|bbox|WARNING' build/blender.log

echo "== STL check"
python3 "$REPO/tools/check_stl.py" --project .

if [ "$SLICE" = 1 ]; then
  echo "== Bambu Studio slice dry run (3 walls, 0.15 mm elephant-foot compensation; everything else stock)"
  python3 "$REPO/tools/slice.py" --project . --set wall_loops=3 --set elefant_foot_compensation=0.15
  echo "== copying the sliced 3MF project files to print/"
  for p in bin lid test-coupon; do cp "build/slice/$p/$p.3mf" "print/$p.3mf"; done
fi
