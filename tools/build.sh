#!/usr/bin/env bash
# Build all STLs + preview images with Blender (headless). No OpenSCAD needed.
# Usage: tools/build.sh [--no-render]
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
if [ ! -x "$BLENDER" ]; then
  BLENDER="$(command -v blender || true)"
fi
if [ -z "$BLENDER" ]; then
  echo "Blender not found. Set BLENDER=/path/to/blender" >&2
  exit 1
fi
"$BLENDER" -b -P tools/build_stl.py -- "$@" 2>&1 | grep -E 'wrote|layerdock|bbox|WARN|Error|Traceback|line [0-9]+' || true
