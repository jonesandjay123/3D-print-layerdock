"""
Build layerdock STLs and preview renders with Blender (headless).

This is a 1:1 mirror of the geometry in scad/layerdock.scad so that STLs can be
produced on a machine without OpenSCAD.  Every number comes from the parameter
block at the top of the .scad file (parsed below) — one source of truth for
dimensions.  Each `module` in the .scad has a `build_*` / `*_at` twin here with
the same name and the same box list, in the same order.  If you change one,
change the other; tools/check_consistency.py compares the two when OpenSCAD
is installed.

Usage:
    blender -b --python-exit-code 1 -P tools/build_stl.py -- [--no-render]

Outputs:
    stl/base.stl, stl/layer.stl, stl/top.stl, stl/test-coupon.stl
    docs/images/assembly.png, exploded.png, parts.png, joint.png
"""
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAD = os.path.join(ROOT, "scad", "layerdock.scad")
STL_DIR = os.path.join(ROOT, "stl")
IMG_DIR = os.path.join(ROOT, "docs", "images")
EPS = 0.5  # overlap used to avoid coplanar boolean faces (always inside solid or outside the part)


# --------------------------------------------------------------------- params
def parse_params(path):
    """Read `name = literal;` lines from the top of the .scad file (up to [Hidden])."""
    params = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "[Hidden]" in line:
                break
            m = re.match(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+?);", line)
            if not m:
                continue
            name, raw = m.group(1), m.group(2).strip()
            if raw in ("true", "false"):
                params[name] = raw == "true"
            elif raw.startswith('"'):
                params[name] = raw.strip('"')
            elif raw.startswith("["):
                params[name] = [float(v) for v in raw.strip("[]").split(",")]
            else:
                params[name] = float(raw)
    return params


P = parse_params(SCAD)


def D(name):
    return P[name]


# derived, same as the [Hidden] block in the .scad
peg, peg_h = D("peg"), D("peg_h")
socket = peg + 2 * D("socket_fit")
socket_depth = peg_h + D("socket_extra")
post = D("post")
frame_w, frame_d = D("frame_w"), D("frame_d")
layer_h = D("layer_h")
base_t, base_boss_h = D("base_t"), D("base_boss_h")
top_t, top_boss, top_boss_h = D("top_t"), D("top_boss"), D("top_boss_h")
xbox_x = (frame_w - D("xbox_w")) / 2
xbox_y = -D("xbox_front_overhang")
plug_zone = (frame_d - D("rear_rail_t")) - (xbox_y + D("xbox_d"))
N_LAYERS = int(D("layers"))
inner_h = base_boss_h + N_LAYERS * layer_h
total_h = base_t + inner_h + top_t + top_boss_h
wall = (post - peg) / 2 - D("socket_fit")
mac_x = (frame_w - D("mac_w")) / 2
mac_y = (frame_d - D("mac_d")) / 2
test_bar_h = socket_depth + 3
test_stub_h = 8


def corners(size):
    return [(0, 0), (frame_w - size, 0), (0, frame_d - size), (frame_w - size, frame_d - size)]


# --------------------------------------------------------------------- CSG helpers
def _solver_id():
    ids = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    for want in ("EXACT", "MANIFOLD"):
        if want in ids:
            return want
    return ids[0]


SOLVER = _solver_id()


def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box_pts(x, y, z, sx, sy, sz):
    return [(x, y, z), (x + sx, y, z), (x + sx, y + sy, z), (x, y + sy, z),
            (x, y, z + sz), (x + sx, y, z + sz), (x + sx, y + sy, z + sz), (x, y + sy, z + sz)]


def box(x, y, z, sx, sy, sz, name="box"):
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_obj(name, box_pts(x, y, z, sx, sy, sz), f)


def delete(ob):
    bpy.data.objects.remove(ob, do_unlink=True)


def boolean(target, other, op):
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.object = other
    mod.solver = SOLVER
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    delete(other)


def join(objs, name):
    """Join several non-overlapping objects into one mesh (no boolean needed)."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def union(objs, name="union"):
    base = objs[0]
    for o in objs[1:]:
        boolean(base, o, "UNION")
    base.name = name
    return base


def difference(target, cutters):
    if cutters:
        cutter = join(cutters, "cutter") if len(cutters) > 1 else cutters[0]
        boolean(target, cutter, "DIFFERENCE")
    return target


def intersection(target, other):
    boolean(target, other, "INTERSECT")
    return target


def hull_obj(name, points):
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bm.verts.ensure_lookup_table()
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def transform_verts(ob, fn):
    for v in ob.data.vertices:
        v.co = Vector(fn(v.co))
    ob.data.update()


def clean(ob):
    """Merge duplicate vertices and recalc normals after booleans."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=True)
    bm.free()
    return v


# --------------------------------------------------------------------- joint features (twins of the .scad modules)
def peg_at(x, y, z0):
    """Integrated peg growing upward from z0, centred on a post-sized square at corner (x, y)."""
    c = D("peg_chamfer")
    ox, oy, oz = x + (post - peg) / 2, y + (post - peg) / 2, z0 - EPS
    pts = box_pts(ox, oy, oz, peg, peg, peg_h - c + EPS) + \
        box_pts(ox + c, oy + c, oz, peg - 2 * c, peg - 2 * c, peg_h + EPS)
    return hull_obj("peg", pts)


def socket_cutter_at(x, y, size, fit=None):
    """Socket cutter opening at z=0 going up, centred on a size-sized square at corner (x, y).
    Includes the mouth chamfer; crush ribs are subtracted from the cutter so they remain."""
    if fit is None:
        fit = D("socket_fit")
    cx, cy = x + size / 2, y + size / 2
    s = peg + 2 * fit
    mc = D("socket_mouth_chamfer")
    body = box(cx - s / 2, cy - s / 2, -EPS, s, s, socket_depth + EPS, "socket")
    mouth = hull_obj("mouth", box_pts(cx - s / 2 - mc, cy - s / 2 - mc, -EPS, s + 2 * mc, s + 2 * mc, EPS) +
                     box_pts(cx - s / 2, cy - s / 2, mc, s, s, EPS))
    cutter = union([body, mouth], "socket")
    if D("crush_ribs"):
        rw, rh = D("rib_w"), D("rib_h")
        z0 = mc + 1
        zl = socket_depth + 1 - z0
        ribs = [box(cx + s / 2 - rh, cy - rw / 2, z0, rh + 1, rw, zl),
                box(cx - s / 2 - 1, cy - rw / 2, z0, rh + 1, rw, zl),
                box(cx - rw / 2, cy + s / 2 - rh, z0, rw, rh + 1, zl),
                box(cx - rw / 2, cy - s / 2 - 1, z0, rw, rh + 1, zl)]
        difference(cutter, ribs)
    return cutter


# --------------------------------------------------------------------- parts
def build_base():
    solids = [box(0, 0, 0, frame_w, frame_d, base_t, "plate")]
    for x, y in corners(post):
        solids.append(box(x, y, 0, post, post, base_t + base_boss_h))
        solids.append(peg_at(x, y, base_t + base_boss_h))
    if D("guides"):
        gw, gg, gl, gs, gh = D("guide_w"), D("guide_gap"), D("guide_len"), D("guide_setback"), D("guide_h")
        for sx in (-1, 1):
            cx = frame_w / 2 + sx * (D("xbox_w") / 2 + gg + gw / 2) - gw / 2
            solids.append(box(cx, gs, base_t - EPS, gw, gl, gh + EPS))
    if D("rear_stop"):
        gg = D("guide_gap")
        solids.append(box(xbox_x - gg, xbox_y + D("xbox_d") + 1, base_t - EPS,
                          D("xbox_w") + 2 * gg, 3, D("guide_h") + EPS))
    ob = union(solids, "base")
    clean(ob)
    return ob


def build_layer():
    srt, srh, rrt, rrh = D("side_rail_t"), D("side_rail_h"), D("rear_rail_t"), D("rear_rail_h")
    solids = []
    for x, y in corners(post):
        solids.append(box(x, y, 0, post, post, layer_h))
        solids.append(peg_at(x, y, layer_h))
    for x in (0, frame_w - srt):
        solids.append(box(x, post - EPS, 0, srt, frame_d - 2 * post + 2 * EPS, srh))
    solids.append(box(post - EPS, frame_d - rrt, 0, frame_w - 2 * post + 2 * EPS, rrt, rrh))
    ob = union(solids, "layer")
    difference(ob, [socket_cutter_at(x, y, post) for x, y in corners(post)])
    clean(ob)
    return ob


def build_top():
    rh, rt = D("rim_h"), D("rim_t")
    mac_w, mac_d, gap = D("mac_w"), D("mac_d"), D("mac_gap")
    solids = [box(0, 0, 0, frame_w, frame_d, top_t, "plate")]
    for x, y in corners(top_boss):
        solids.append(box(x, y, 0, top_boss, top_boss, top_t + top_boss_h))
    # outer rim as four bars (overlapping at the corners is fine for the union)
    solids.append(box(0, 0, top_t - EPS, frame_w, rt, rh + EPS))
    solids.append(box(0, frame_d - rt, top_t - EPS, frame_w, rt, rh + EPS))
    solids.append(box(0, 0, top_t - EPS, rt, frame_d, rh + EPS))
    solids.append(box(frame_w - rt, 0, top_t - EPS, rt, frame_d, rh + EPS))
    if D("stops"):
        st, sl, sh = D("stop_t"), D("stop_len"), D("stop_h")
        solids.append(box(mac_x - gap - st, frame_d / 2 - sl / 2, top_t - EPS, st, sl, sh + EPS))
        solids.append(box(mac_x + mac_w + gap, frame_d / 2 - sl / 2, top_t - EPS, st, sl, sh + EPS))
        solids.append(box(frame_w / 2 - sl / 2, mac_y - gap - st, top_t - EPS, sl, st, sh + EPS))
        solids.append(box(frame_w / 2 - sl / 2, mac_y + mac_d + gap, top_t - EPS, sl, st, sh + EPS))
    ob = union(solids, "top")
    cutters = [socket_cutter_at(x, y, post) for x, y in corners(post)]  # on the post grid
    if D("vents"):
        vi, vw, vp = D("vent_inset"), D("vent_w"), D("vent_pitch")
        vx0, vx1 = mac_x + vi, mac_x + mac_w - vi
        vy0, vy1 = mac_y + vi, mac_y + mac_d - vi
        n = int(math.floor((vx1 - vx0 - vw) / vp)) + 1
        x_start = (vx0 + vx1) / 2 - ((n - 1) * vp + vw) / 2
        for i in range(n):
            cutters.append(box(x_start + i * vp, vy0, -EPS, vw, vy1 - vy0, top_t + 2 * EPS))
    difference(ob, cutters)
    clean(ob)
    return ob


def build_test():
    fits = D("test_fits")
    pitch = post
    bar = box(0, 0, 0, pitch * len(fits), post, test_bar_h, "test-bar")
    difference(bar, [socket_cutter_at(i * pitch, 0, post, f) for i, f in enumerate(fits)])
    stub = union([box(0, post + 10, 0, post, post, test_stub_h), peg_at(0, post + 10, test_stub_h)], "stub")
    ob = join([bar, stub], "test-coupon")
    clean(ob)
    return ob


def build_joint(gap=10):
    """One corner of the Base + bottom 30 mm of one Layer post, sectioned at y = post/2."""
    b = build_base()
    intersection(b, box(0, 0, 0, post + 10, post + 10, 100))
    l = build_layer()
    intersection(l, box(0, 0, 0, post + 10, post + 10, 30))
    transform_verts(l, lambda v: (v.x, v.y, v.z + base_t + base_boss_h + gap))
    ob = union([b, l], "joint")
    difference(ob, [box(-1, -100, -1, post + 20, 100 + post / 2, 200)])  # remove the front half
    clean(ob)
    return ob


# --------------------------------------------------------------------- export
def export_stl(ob, filename):
    os.makedirs(STL_DIR, exist_ok=True)
    path = os.path.join(STL_DIR, filename)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, ascii_format=False)
    print(f"wrote {os.path.relpath(path, ROOT)}")


def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# --------------------------------------------------------------------- render
def copy_obj(ob, name, dx=0, dy=0, dz=0, color=(0.8, 0.8, 0.8, 1)):
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    new.location = (dx, dy, dz)
    new.color = color
    new.hide_render = False
    bpy.context.scene.collection.objects.link(new)
    return new


def ghost_box(name, x, y, z, sx, sy, sz, color):
    ob = box(x, y, z, sx, sy, sz, name)
    mod = ob.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 2.5
    mod.use_even_offset = True
    ob.color = color
    return ob


def setup_render(width=1400, height=1100):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x = width
    sc.render.resolution_y = height
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_object_outline = True
    sh.show_cavity = True
    sh.show_shadows = False
    sh.background_type = "WORLD"
    world = bpy.data.worlds.new("world")
    world.color = (0.96, 0.96, 0.95)
    sc.world = world
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.display.render_aa = "8"


def scene_bounds(objs):
    bpy.context.view_layer.update()
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for ob in objs:
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def camera_look(objs, direction, lens=50, margin=1.06):
    """Perspective camera looking along -direction, framed on the objects' bounding box."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    lo, hi = scene_bounds(objs)
    center = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    radius = (Vector(hi) - Vector(lo)).length / 2
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "PERSP"
    cam_data.lens = lens
    cam_data.clip_end = 20000
    w, h = sc.render.resolution_x, sc.render.resolution_y
    fov = 2 * math.atan(36.0 * min(1.0, h / w) / (2 * lens))
    dist = radius / math.sin(fov / 2) * margin
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    pts = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    for _ in range(4):
        cam.location = center + d * dist
        bpy.context.view_layer.update()
        dev = 0.0
        for c in pts:
            u, v, _ = world_to_camera_view(sc, cam, c)
            dev = max(dev, abs(u - 0.5), abs(v - 0.5))
        dist *= (dev / 0.5) * margin
    cam.location = center + d * dist
    return cam


def render(path):
    os.makedirs(IMG_DIR, exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"wrote {os.path.relpath(path, ROOT)}")


def clear_render_objects():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(("a_", "p_", "j_", "xbox", "mac", "cam")):
            delete(ob)


GREY = (0.45, 0.48, 0.52, 1)
BLUE_A = (0.69, 0.77, 0.87, 1)
BLUE_B = (0.27, 0.51, 0.71, 1)
ORANGE = (0.95, 0.60, 0.20, 1)
GHOST_X = (0.15, 0.65, 0.25, 1)
GHOST_M = (0.75, 0.25, 0.25, 1)


def place_stack(parts, gap=0.0, ghosts=True):
    objs = [copy_obj(parts["base"], "a_base", 0, 0, 0, GREY)]
    for i in range(N_LAYERS):
        z = base_t + base_boss_h + i * layer_h + (i + 1) * gap
        objs.append(copy_obj(parts["layer"], f"a_layer{i}", 0, 0, z, BLUE_A if i % 2 == 0 else BLUE_B))
    z_top = base_t + inner_h + (N_LAYERS + 1) * gap
    objs.append(copy_obj(parts["top"], "a_top", 0, 0, z_top, GREY))
    if ghosts:
        objs.append(ghost_box("xbox", xbox_x, xbox_y, base_t, D("xbox_w"), D("xbox_d"), D("xbox_h"), GHOST_X))
        objs.append(ghost_box("mac", mac_x, mac_y, z_top + top_t, D("mac_w"), D("mac_d"), D("mac_h"), GHOST_M))
    return objs


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    do_render = "--no-render" not in args

    bpy.ops.wm.read_factory_settings(use_empty=True)
    for ob in list(bpy.data.objects):
        delete(ob)
    print(f"layerdock v0.1.1: solver {SOLVER}; inner width {frame_w - 2 * post:.1f} mm; inner height {inner_h:.1f} mm; "
          f"plug zone {plug_zone:.1f} mm; total height {total_h:.1f} mm; socket wall {wall:.2f} mm")
    if inner_h < D("xbox_h") + D("xbox_headroom"):
        print("WARNING: not enough height for the Xbox")
    if plug_zone < D("xbox_min_plug_zone"):
        print("WARNING: plug zone too small")

    parts = {"base": build_base(), "layer": build_layer(), "top": build_top(), "test": build_test()}
    for name, ob in parts.items():
        export_stl(ob, {"test": "test-coupon"}.get(name, name) + ".stl")
        lo, hi = bbox(ob)
        print(f"  {name:6s} bbox {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
              f"volume {volume(ob)/1000:.1f} cm3")

    if not do_render:
        return

    setup_render()
    for ob in parts.values():
        ob.hide_render = True

    # assembled view
    objs = place_stack(parts, gap=0, ghosts=True)
    camera_look(objs, (-1.0, -1.6, 0.7))
    render(os.path.join(IMG_DIR, "assembly.png"))
    clear_render_objects()

    # exploded view
    objs = place_stack(parts, gap=40, ghosts=False)
    camera_look(objs, (-1.0, -1.6, 0.55))
    render(os.path.join(IMG_DIR, "exploded.png"))
    clear_render_objects()

    # parts in print orientation, side by side
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 750
    x = 0
    objs = []
    for name, col in (("base", GREY), ("layer", BLUE_B), ("top", GREY), ("test", ORANGE)):
        ob = parts[name]
        lo, hi = bbox(ob)
        objs.append(copy_obj(ob, f"p_{name}", x - lo[0], -lo[1], -lo[2], col))
        x += (hi[0] - lo[0]) + 30
    camera_look(objs, (-0.25, -1.0, 1.0), lens=60)
    render(os.path.join(IMG_DIR, "parts.png"))
    clear_render_objects()

    # joint close-up: sectioned, exploded (left) and engaged (right)
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 900
    j_open = build_joint(gap=10)
    j_closed = build_joint(gap=0)
    objs = [copy_obj(j_open, "j_open", 0, 0, 0, BLUE_B), copy_obj(j_closed, "j_closed", post + 30, 0, 0, BLUE_B)]
    j_open.hide_render = True
    j_closed.hide_render = True
    camera_look(objs, (0.25, -1.0, 0.45), lens=70)
    render(os.path.join(IMG_DIR, "joint.png"))


if __name__ == "__main__":
    main()
