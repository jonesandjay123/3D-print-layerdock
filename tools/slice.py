#!/usr/bin/env python3
"""
Slice every STL in <project>/stl/ with the locally installed Bambu Studio (CLI mode) using
the stock "Bambu Lab A1 mini 0.4 nozzle" + "0.20mm Standard @BBL A1M" +
"Bambu PLA Basic" profiles, then write docs/print-report.md with print time,
filament, brim, and the real footprint of everything the nozzle touches.

Nothing is printed and nothing is sent to a printer; this is a dry run of the
slicer.  Bambu's profile JSONs inherit from each other, so they are flattened
into build/profiles/ first (that folder is git-ignored).

Shared by every project in projects/: <project> is --project DIR (default: the
current directory).  Output goes to <project>/build/slice/<part>/ (git-ignored)
and the summary to <project>/docs/print-report.md.

Process-profile values can be overridden with --set key=value (repeatable), e.g.
--set wall_loops=3 --set elefant_foot_compensation=0.15; the overrides are listed
in the report so the 3MF in build/slice/ is reproducible.

Usage: tools/slice.py [--project DIR] [--only part[,part]] [--set key=value]... [--app /Applications/BambuStudio.app]
                      [--plate "Textured PEI Plate"] [--filament "Bambu PETG Basic @BBL A1M 0.4 nozzle"]
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.getcwd()  # overridden by --project
BUILD = os.path.join(ROOT, "build")
APP = "/Applications/BambuStudio.app"
MACHINE = "Bambu Lab A1 mini 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL A1M"
FILAMENT = "Bambu PLA Basic @BBL A1M"  # Jones prints PLA; --filament overrides
BED = 180.0


def flatten(profiles_dir, kind, name):
    path = os.path.join(profiles_dir, kind, name + ".json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    parent = d.pop("inherits", None)
    if parent:
        base = flatten(profiles_dir, kind, parent)
        base.update(d)
        return base
    return d


def gcode_stats(path):
    """Header estimates plus the XY extents of the OBJECT toolpaths only (the purge
    line in the machine start g-code runs past the bed on purpose and is skipped)."""
    stats = {"brim": False}
    xs, ys = [], []
    in_object = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("; MACHINE_START_GCODE_END"):
                in_object = True
            elif line.startswith("; MACHINE_END_GCODE_START"):
                in_object = False
            if line.startswith("; model printing time:"):
                stats["time"] = line.split(":", 1)[1].split(";")[0].strip()
            elif line.startswith("; total filament weight"):
                stats["grams"] = float(line.split(":")[1])
            elif line.startswith("; total filament length"):
                stats["length_m"] = float(line.split(":")[1]) / 1000
            elif line.startswith("; total layer number"):
                stats["layers"] = int(line.split(":")[1])
            elif line.startswith("; FEATURE: Brim"):
                stats["brim"] = True
            elif line.startswith("; brim_type ="):
                stats["brim_type"] = line.split("=")[1].strip()
            elif line.startswith("; wall_loops ="):
                stats["walls"] = line.split("=")[1].strip()
            elif line.startswith("; sparse_infill_density ="):
                stats["infill"] = line.split("=")[1].strip()
            elif line.startswith("; support_"):
                pass
            elif in_object and line.startswith("G1 ") and " E" in line and "X" in line and "Y" in line:
                m = re.search(r"X(-?[\d.]+) Y(-?[\d.]+)", line)
                if m:
                    xs.append(float(m.group(1)))
                    ys.append(float(m.group(2)))
    if xs:
        stats["extents"] = (min(xs), max(xs), min(ys), max(ys))
    return stats


def main():
    global ROOT, BUILD
    args = sys.argv[1:]
    if "--project" in args:
        ROOT = os.path.abspath(args[args.index("--project") + 1])
        BUILD = os.path.join(ROOT, "build")
    only = args[args.index("--only") + 1].split(",") if "--only" in args else None
    overrides = {}
    for i, a in enumerate(args):
        if a == "--set":
            k, v = args[i + 1].split("=", 1)
            overrides[k] = v
    app = APP
    plate = "Textured PEI Plate"
    if "--app" in args:
        app = args[args.index("--app") + 1]
    if "--plate" in args:
        plate = args[args.index("--plate") + 1]
    global FILAMENT
    if "--filament" in args:
        FILAMENT = args[args.index("--filament") + 1]
    exe = os.path.join(app, "Contents", "MacOS", "BambuStudio")
    profiles_dir = os.path.join(app, "Contents", "Resources", "profiles", "BBL")
    if not os.path.exists(exe):
        print(f"Bambu Studio not found at {app}; skipping slice test")
        sys.exit(2)

    pdir = os.path.join(BUILD, "profiles")
    os.makedirs(pdir, exist_ok=True)
    machine = flatten(profiles_dir, "machine", MACHINE)
    process = flatten(profiles_dir, "process", PROCESS)
    process["curr_bed_type"] = plate
    for k, v in overrides.items():
        if k not in process:
            print(f"WARNING: {k} is not a key of the process profile; setting it anyway")
        process[k] = v
    filament = flatten(profiles_dir, "filament", FILAMENT)
    for name, d in (("machine", machine), ("process", process), ("filament", filament)):
        with open(os.path.join(pdir, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)

    stls = sorted(f for f in os.listdir(os.path.join(ROOT, "stl")) if f.endswith(".stl"))
    if only:
        stls = [f for f in stls if f[:-4] in only]
    rows = []
    for stl in stls:
        name = stl[:-4]
        out = os.path.join(BUILD, "slice", name)
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        cmd = [exe, "--debug", "1",
               "--load-settings", f"{pdir}/machine.json;{pdir}/process.json",
               "--load-filaments", f"{pdir}/filament.json",
               "--slice", "0", "--export-3mf", name + ".3mf",  # relative: an absolute path makes the .tmp write fail
               "--outputdir", out, os.path.join(ROOT, "stl", stl)]
        print(f"slicing {stl} ...", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=out)  # Bambu writes result.json to cwd
        gcode = os.path.join(out, "plate_1.gcode")
        if not os.path.exists(gcode):
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-5:])
            print(f"  FAILED (exit {r.returncode}):\n{tail}")
            rows.append((name, None))
            continue
        st = gcode_stats(gcode)
        rows.append((name, st))
        ext = st.get("extents")
        fp = f"{ext[0]:.1f}..{ext[1]:.1f} x {ext[2]:.1f}..{ext[3]:.1f}" if ext else "?"
        print(f"  {st.get('time')}  {st.get('grams')} g  brim={'yes' if st['brim'] else 'no'}  toolpath XY {fp}")

    report = os.path.join(ROOT, "docs", "print-report.md")
    if only:  # a partial run must not overwrite the full report
        report = os.path.join(BUILD, "print-report-partial.md")
    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Slicing dry run (Bambu Studio CLI)\n\n")
        f.write(f"Printer profile `{MACHINE}`, process `{PROCESS}`, filament `{FILAMENT}`, plate `{plate}`.\n")
        if overrides:
            f.write("Process overrides: " + ", ".join(f"`{k}={v}`" for k, v in overrides.items()) + ". ")
        else:
            f.write("Stock profile values (walls, infill, brim) — nothing hand-tuned. ")
        f.write("Generated by `tools/slice.py`; the g-code itself is in `build/slice/` (git-ignored).\n\n")
        f.write("| part | print time | filament | layers | brim generated | toolpath footprint on bed (mm) | fits 180 × 180 |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for name, st in rows:
            if not st:
                f.write(f"| {name} | slice failed | | | | | |\n")
                continue
            ext = st.get("extents")
            if ext:
                w, d = ext[1] - ext[0], ext[3] - ext[2]
                fits = "yes" if (ext[0] >= 0 and ext[2] >= 0 and ext[1] <= BED and ext[3] <= BED) else "**NO**"
                fp = f"{w:.1f} × {d:.1f}"
            else:
                fits, fp = "?", "?"
            f.write(f"| {name} | {st.get('time')} | {st.get('grams')} g ({st.get('length_m', 0):.1f} m) | {st.get('layers')} | "
                    f"{'yes' if st['brim'] else 'no'} ({st.get('brim_type')}) | {fp} | {fits} |\n")
        f.write(f"\nProfile values used: walls {rows[0][1].get('walls') if rows and rows[0][1] else '?'}, "
                f"infill {rows[0][1].get('infill') if rows and rows[0][1] else '?'}, supports off.\n")
    print(f"wrote {os.path.relpath(report, ROOT)}")
    sys.exit(0 if all(st for _, st in rows) else 1)


if __name__ == "__main__":
    main()
