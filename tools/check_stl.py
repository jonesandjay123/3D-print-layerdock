#!/usr/bin/env python3
"""
Check every STL in stl/: binary format, watertight (every edge shared by exactly
two triangles with opposite winding), positive volume, bounding box within the
printer bed.  Pure Python, no dependencies.

Usage: tools/check_stl.py [--bed 180] [files...]
Exit code 1 if any file fails.
"""
import glob
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:5] == b"solid" and b"facet" in data[:300]:
        raise ValueError("ASCII STL — expected binary")
    n = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + n * 50:
        raise ValueError(f"size mismatch: {len(data)} bytes for {n} triangles")
    tris = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack_from("<12f", data, off)
        tris.append(((v[3], v[4], v[5]), (v[6], v[7], v[8]), (v[9], v[10], v[11])))
    return tris


def key(p):
    return tuple(round(c, 4) for c in p)


def analyse(tris):
    edges = {}
    vol6 = 0.0
    area = 0.0
    lo = [1e18] * 3
    hi = [-1e18] * 3
    degenerate = 0
    for a, b, c in tris:
        ka, kb, kc = key(a), key(b), key(c)
        if ka == kb or kb == kc or ka == kc:
            degenerate += 1
            continue
        for e in ((ka, kb), (kb, kc), (kc, ka)):
            edges[e] = edges.get(e, 0) + 1
        # signed volume of tetrahedron (origin, a, b, c)
        vol6 += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        cr = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        area += 0.5 * (cr[0] ** 2 + cr[1] ** 2 + cr[2] ** 2) ** 0.5
        for p in (a, b, c):
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    unmatched = 0
    for (u, v), cnt in edges.items():
        if cnt != 1 or edges.get((v, u), 0) != 1:
            unmatched += 1
    return {
        "triangles": len(tris),
        "degenerate": degenerate,
        "bad_edges": unmatched,
        "volume_cm3": vol6 / 6.0 / 1000.0,
        "area_cm2": area / 100.0,
        "size": [hi[i] - lo[i] for i in range(3)],
        "min": lo,
    }


def main():
    args = sys.argv[1:]
    bed = 180.0
    if "--bed" in args:
        i = args.index("--bed")
        bed = float(args[i + 1])
        del args[i:i + 2]
    files = args or sorted(glob.glob(os.path.join(ROOT, "stl", "*.stl")))
    ok = True
    print(f"{'file':18s} {'tris':>6s} {'bad edges':>9s} {'volume cm3':>10s} {'area cm2':>9s}  size (mm)")
    for path in files:
        try:
            r = analyse(read_stl(path))
        except Exception as e:  # noqa: BLE001
            print(f"{os.path.basename(path):18s} ERROR {e}")
            ok = False
            continue
        problems = []
        if r["bad_edges"]:
            problems.append("not watertight")
        if r["degenerate"]:
            problems.append(f"{r['degenerate']} degenerate")
        if r["volume_cm3"] <= 0:
            problems.append("negative volume (inverted normals)")
        if max(r["size"][0], r["size"][1]) > bed:
            problems.append(f"footprint exceeds {bed:g} mm bed")
        if r["size"][2] > bed:
            problems.append("too tall")
        if min(r["min"]) < -1e-3:
            problems.append("below z=0 / negative origin")
        sz = " x ".join(f"{s:.1f}" for s in r["size"])
        status = "FAIL: " + ", ".join(problems) if problems else "OK"
        print(f"{os.path.basename(path):18s} {r['triangles']:6d} {r['bad_edges']:9d} {r['volume_cm3']:10.2f} {r['area_cm2']:9.1f}  {sz}  {status}")
        ok = ok and not problems
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
