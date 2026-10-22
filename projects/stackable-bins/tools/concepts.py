"""
Concept mock-ups for the top module (hood + deeper tray + a dust shade), rendered for
Jones to choose from.  Mock-up only: geometry is approximate and nothing here is exported
as STL.  Builds on tools/build_stl.py with the hood covering 2/3 of the depth.

    blender -b --python-exit-code 1 -P tools/concepts.py
Outputs docs/concepts/concept-A.png ... concept-D.png (3/4 view + side section each).
"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stl as bs  # noqa: E402

ROOT = bs.ROOT
OUT = os.path.join(ROOT, "docs", "concepts")
W, D, R, wall, sc = bs.bin_w, bs.bin_d, bs.corner_r, bs.wall, bs.sc
BIN_H, N = bs.bin_h, bs.N_BINS

# shared changes vs v0.1.1: hood covers 2/3 of the depth, tray 25 mm deep
COVER = 115.0
HOOD_H = 72.0
TRAY_H = 27.0
bs.cover_depth, bs.hood_h, bs.tray_h = COVER, HOOD_H, TRAY_H
bs.ledge_z = HOOD_H - TRAY_H
bs.tray_d = COVER - wall - bs.tray_fit
Y_FRONT = D - COVER          # y of the hood's open front edge
Z_TOP = N * BIN_H            # top of the top bin = bottom of the hood

IVORY, DARK, SHADE = bs.IVORY, bs.IVORY_B, (0.55, 0.62, 0.72, 1)


def yz_prism(name, pts, x0, x1):
    """Prism along x of a polygon given in the (y, z) plane."""
    n = len(pts)
    verts = [(x0, y, z) for y, z in pts] + [(x1, y, z) for y, z in pts]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    ob = bs.mesh_obj(name, verts, faces)
    bs.clean(ob)
    if bs.volume(ob) < 0:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    return ob


def ring(name, h, cover, t=wall):
    """Three rounded walls (no groove), open at the front, z from 0 to h."""
    prof = [(sc, 0), (0, sc), (0, h - sc), (sc, h), (t, h), (t, 0)]
    ob = bs.sweep(name, W, D, R, prof, closed=True)
    bs.difference(ob, [bs.box(-1, -1, -1, W + 2, D - cover + 1, h + 2)])
    return ob


def slab(name, w, d, radii, t, hole=2.5):
    prof = [(hole, 0), (0, 0), (0, t), (hole, t)]
    return bs.sweep(name, w, d, radii, prof)


def base_module():
    hood = bs.build_hood()
    tray = bs.build_tray()
    bs.transform_verts(hood, lambda v: (v.x, v.y, v.z + Z_TOP))
    bs.transform_verts(tray, lambda v: (v.x + wall + bs.tray_fit, v.y + Y_FRONT, v.z + Z_TOP + bs.ledge_z))
    return [hood, tray]


# ---- the four shades ---------------------------------------------------------------
def shade_A():
    """Slanted awning: hood side walls rise as wedges, a flat roof plate slopes from 36 mm at the
    back down to 12 mm above the hood at its front edge; the front 22 mm of the tray stay open."""
    yF, zF, zB, t = Y_FRONT + 22, 12.0, 36.0, 2.4
    slope = (zB - zF) / (D - wall - yF)
    z_line = lambda y: zF + (y - yF) * slope  # noqa: E731
    ext = ring("A_ext", zB, COVER)
    bs.difference(ext, [yz_prism("cut", [(-10, z_line(-10)), (D + 10, z_line(D + 10)), (D + 10, 400), (-10, 400)], -1, W + 1)])
    roof = yz_prism("A_roof", [(yF, zF), (D - wall + 0.01, zB), (D - wall + 0.01, zB - t), (yF, zF - t)], wall - 0.01, W - wall + 0.01)
    for ob in (ext, roof):
        bs.transform_verts(ob, lambda v: (v.x, v.y, v.z + Z_TOP + HOOD_H))
    return [ext, roof]


def shade_B():
    """Flat half lid: a plate flush with the tray rim covers the back 2/3 of the tray; the front
    third of the tray is an open slot.  The top stays flat for putting things on."""
    tw, td = bs.tray_wall, bs.tray_fit
    w = bs.tray_w - 2 * tw - 0.6
    d = bs.tray_d - tw - 0.3
    rb = bs.tray_back_r - tw - 0.3
    plate = slab("B_plate", w, d + 5, (rb, rb, 3.0, 3.0), 2.4)
    open_d = bs.tray_d / 3
    bs.difference(plate, [bs.box(-1, -10, -1, w + 2, open_d + 10, 5)])
    bs.transform_verts(plate, lambda v: (v.x + wall + td + tw + 0.3, v.y + Y_FRONT - 5, v.z + Z_TOP + HOOD_H - 2.4))
    return [plate]


def shade_C():
    """Second cubby: a 40 mm three-wall hood on top covers the back 2/3 of the tray with a flat
    roof (a drop-in plate), open at the front; the roof is another shelf."""
    h, cover = 40.0, COVER * 2 / 3
    up = ring("C_ring", h, cover)
    inset = wall + 0.3
    roof = slab("C_roof", W - 2 * inset, D - 2 * inset, R - inset, 2.4)
    bs.difference(roof, [bs.box(-1, -1, -1, W + 2, D - cover - inset + 1, 5)])
    bs.transform_verts(roof, lambda v: (v.x + inset, v.y + inset, v.z + h - 2.4))
    for ob in (up, roof):
        bs.transform_verts(ob, lambda v: (v.x, v.y, v.z + Z_TOP + HOOD_H))
    return [up, roof]


def shade_D():
    """Curved canopy: the side walls rise under a quarter-ellipse roof that starts vertical at the
    front edge (12 mm above the hood) and sweeps up to 36 mm at the back wall."""
    yF, zF, zB, t = Y_FRONT + 22, 12.0, 36.0, 2.4
    a, b = (D - wall) - yF, zB - zF
    cx, cz = D - wall, zF
    outer = [(cx - a * math.cos(math.radians(k * 3)), cz + b * math.sin(math.radians(k * 3))) for k in range(31)]
    inner = [(y, z - t) for y, z in outer][::-1]
    ext = ring("D_ext", zB, COVER)
    cutter = [(-10, -1), (yF, -1)] + outer + [(D + 10, zB), (D + 10, 400), (-10, 400)]
    bs.difference(ext, [yz_prism("cut", cutter, -1, W + 1)])
    roof = yz_prism("D_roof", outer + [(cx + 0.01, zB), (cx + 0.01, zB - t)] + inner[:-1] + [(yF, zF - t)], wall - 0.01, W - wall + 0.01)
    for ob in (ext, roof):
        bs.transform_verts(ob, lambda v: (v.x, v.y, v.z + Z_TOP + HOOD_H))
    return [ext, roof]


SHADES = {"A": ("A  斜遮簷", shade_A), "B": ("B  平頂半蓋", shade_B), "C": ("C  上層小罩", shade_C), "D": ("D  弧形遮簷", shade_D)}


# ---- rendering ---------------------------------------------------------------------
def render_to_array(path):
    bs.render(path)
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return arr


def save_array(path, arr):
    h, w, _ = arr.shape
    img = bpy.data.images.new("out", width=w, height=h, alpha=True)
    img.pixels[:] = arr.ravel().tolist()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def label_image(text, width, height=90):
    """Render a label strip with a Chinese-capable font."""
    sc_ = bpy.context.scene
    sc_.render.resolution_x, sc_.render.resolution_y = width, height
    font = bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    cu = bpy.data.curves.new("label", type="FONT")
    cu.body = text
    cu.font = font
    cu.size = 1.0
    cu.align_x = "LEFT"
    ob = bpy.data.objects.new("cam_label", cu)
    ob.color = (0.12, 0.12, 0.12, 1)
    sc_.collection.objects.link(ob)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = width / height * 1.6
    cam = bpy.data.objects.new("cam", cam_data)
    sc_.collection.objects.link(cam)
    cam.location = (cam_data.ortho_scale / 2 - 0.4, 0.45, 10)
    sc_.camera = cam
    arr = render_to_array(os.path.join(OUT, "_label.png"))
    bs.delete(ob)
    bs.delete(cam)
    return arr


def hstack(a, b):
    h = max(a.shape[0], b.shape[0])

    def pad(x):
        if x.shape[0] == h:
            return x
        bg = np.ones((h - x.shape[0], x.shape[1], 4), dtype=np.float32) * np.array([0.96, 0.96, 0.95, 1], dtype=np.float32)
        return np.vstack([x, bg])  # image rows are bottom-up in Blender: pad on top
    return np.hstack([pad(a), pad(b)])


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for ob in list(bpy.data.objects):
        bs.delete(ob)
    os.makedirs(OUT, exist_ok=True)
    bs.IMG_DIR = OUT
    bs.setup_render()
    bins = [bs.build_bin()]
    bins[0].hide_render = True

    for key, (title, fn) in SHADES.items():
        module = base_module()
        shade = fn()
        for ob in module + shade:
            ob.hide_render = True
        objs = []
        for i in range(N):
            objs.append(bs.copy_obj(bins[0], f"a_bin{i}", 0, 0, i * BIN_H, IVORY))
        objs.append(bs.copy_obj(module[0], "a_hood", 0, 0, 0, IVORY))
        objs.append(bs.copy_obj(module[1], "a_tray", 0, 0, 0, DARK))
        for k, ob in enumerate(shade):
            objs.append(bs.copy_obj(ob, f"a_shade{k}", 0, 0, 0, SHADE))
        sc_ = bpy.context.scene
        sc_.render.resolution_x, sc_.render.resolution_y = 1100, 1000
        bs.camera_look(objs, (0.9, -1.3, 0.9), margin=1.04)
        view = render_to_array(os.path.join(OUT, f"_{key}_view.png"))
        bs.clear_render_objects()

        # side section through the middle, top bin + module only
        sec_objs = []
        top_bin = bs.copy_obj(bins[0], "s_bin", 0, 0, (N - 1) * BIN_H, IVORY)
        parts = [top_bin, bs.copy_obj(module[0], "s_hood", 0, 0, 0, IVORY), bs.copy_obj(module[1], "s_tray", 0, 0, 0, DARK)] + \
            [bs.copy_obj(ob, f"s_shade{k}", 0, 0, 0, SHADE) for k, ob in enumerate(shade)]
        for ob in parts:
            bs.intersection(ob, bs.box(W / 2, -5, (N - 1) * BIN_H - 1, W, D + 10, 400))
            sec_objs.append(ob)
        sc_.render.resolution_x, sc_.render.resolution_y = 1000, 1000
        bs.camera_look(sec_objs, (-1.0, 0.0, 0.0), ortho=True, margin=1.06)
        section = render_to_array(os.path.join(OUT, f"_{key}_section.png"))
        bs.clear_render_objects()

        sheet = hstack(view, section)
        label = label_image(title + "   （左：外觀   右：中央側剖面，前方在左）", sheet.shape[1])
        sheet = np.vstack([sheet, label])  # rows are bottom-up: label ends up on top
        save_array(os.path.join(OUT, f"concept-{key}.png"), sheet)
        print(f"wrote docs/concepts/concept-{key}.png")
        for ob in module + shade:
            bs.delete(ob)
    for f in os.listdir(OUT):
        if f.startswith("_"):
            os.remove(os.path.join(OUT, f))


if __name__ == "__main__":
    main()
