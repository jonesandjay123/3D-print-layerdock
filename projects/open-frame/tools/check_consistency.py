#!/usr/bin/env python3
"""
Compare the OpenSCAD and Blender versions of every part.

If OpenSCAD is installed, each part is rendered from scad/layerdock.scad into
build/scad/<part>.stl and compared with stl/<part>.stl (made by Blender) on
volume, surface area and bounding box.  Agreement within 0.5 % means the two
descriptions are the same solid (two different meshes of the same CSG tree
have identical volume/area; a missing socket, rib or chamfer changes both).

If OpenSCAD is NOT installed the script says so and exits 2: the .scad file
has then not been executed on this machine and only the Blender STLs are
verified geometry.

Usage: tools/check_consistency.py [--openscad /path/to/openscad]
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "..", "tools"))  # shared tools in <repo>/tools
from check_stl import analyse, read_stl  # noqa: E402
PARTS = {"base": "base", "layer": "layer", "top": "top", "test": "test-coupon"}
CANDIDATES = ["/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD", "openscad", "openscad-nightly"]


def find_openscad(explicit=None):
    for c in ([explicit] if explicit else []) + CANDIDATES:
        if c and (os.path.exists(c) or shutil.which(c)):
            return c if os.path.exists(c) else shutil.which(c)
    return None


def main():
    args = sys.argv[1:]
    explicit = args[args.index("--openscad") + 1] if "--openscad" in args else None
    exe = find_openscad(explicit)
    if not exe:
        print("OpenSCAD not found: the .scad file has NOT been executed here; only the Blender STLs are verified.")
        print("Install with:  brew install --cask openscad   and re-run this script.")
        sys.exit(2)
    out = os.path.join(ROOT, "build", "scad")
    os.makedirs(out, exist_ok=True)
    ok = True
    print(f"{'part':8s} {'volume scad/blender':>22s} {'area scad/blender':>22s}  bbox")
    for part, stl in PARTS.items():
        target = os.path.join(out, part + ".stl")
        r = subprocess.run([exe, "-D", f'part="{part}"', "--export-format", "binstl", "-o", target,
                            os.path.join(ROOT, "scad", "layerdock.scad")], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(target):
            print(f"{part:8s} OpenSCAD failed:\n{r.stderr[-800:]}")
            ok = False
            continue
        a = analyse(read_stl(target))
        b = analyse(read_stl(os.path.join(ROOT, "stl", stl + ".stl")))
        dv = abs(a["volume_cm3"] - b["volume_cm3"]) / max(b["volume_cm3"], 1e-9)
        da = abs(a["area_cm2"] - b["area_cm2"]) / max(b["area_cm2"], 1e-9)
        db = max(abs(a["size"][i] - b["size"][i]) for i in range(3))
        good = dv < 0.005 and da < 0.005 and db < 0.05 and a["bad_edges"] == 0
        ok = ok and good
        print(f"{part:8s} {a['volume_cm3']:10.3f}/{b['volume_cm3']:<10.3f} {a['area_cm2']:10.2f}/{b['area_cm2']:<10.2f}  "
              f"Δ{db:.3f} mm  {'OK' if good else 'MISMATCH'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
