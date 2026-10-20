"""
Build layerdock STLs and preview renders with Blender (headless).

This mirrors the geometry in scad/layerdock.scad so that STLs can be produced
on a machine without OpenSCAD.  All numbers come from the .scad file: the
parameter block at its top is parsed, so there is a single source of truth.

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/build_stl.py -- [--no-render]

Outputs:
    stl/base.stl, stl/layer.stl, stl/top.stl, stl/pin.stl, stl/test-coupon.stl
    docs/images/assembly.png, docs/images/exploded.png, docs/images/parts.png
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
socket = D("pin") + D("socket_clear")
socket_depth = D("pin_len") / 2 + D("socket_extra")
xbox_x = (D("frame_w") - D("xbox_w")) / 2
xbox_y = -D("xbox_front_overhang")
inner_h = D("base_boss_h") + int(D("layers")) * D("layer_h")
plug_zone = (D("frame_d") - D("rear_rail_t")) - (xbox_y + D("xbox_d"))
post = D("post")
frame_w, frame_d = D("frame_w"), D("frame_d")
corners = [(0, 0), (frame_w - post, 0), (0, frame_d - post), (frame_w - post, frame_d - post)]


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


def box(x, y, z, sx, sy, sz, name="box"):
    v = [(x, y, z), (x + sx, y, z), (x + sx, y + sy, z), (x, y + sy, z),
         (x, y, z + sz), (x + sx, y, z + sz), (x + sx, y + sy, z + sz), (x, y + sy, z + sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_obj(name, v, f)


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


def union(objs, name):
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


# --------------------------------------------------------------------- sockets
def socket_cutter(x, y, z_open, up):
    off = (post - socket) / 2
    if up > 0:
        return box(x + off, y + off, z_open - socket_depth, socket, socket, socket_depth + EPS)
    return box(x + off, y + off, z_open - EPS, socket, socket, socket_depth + EPS)


def sockets(z_open, up):
    return [socket_cutter(x, y, z_open, up) for x, y in corners]


# --------------------------------------------------------------------- parts
def build_base():
    base_t, boss_h = D("base_t"), D("base_boss_h")
    solids = [box(0, 0, 0, frame_w, frame_d, base_t, "plate")]
    for x, y in corners:
        solids.append(box(x, y, 0, post, post, base_t + boss_h))
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
    difference(ob, sockets(base_t + boss_h, 1))
    clean(ob)
    return ob


def build_layer():
    lh = D("layer_h")
    srt, srh, rrt, rrh = D("side_rail_t"), D("side_rail_h"), D("rear_rail_t"), D("rear_rail_h")
    solids = [box(x, y, 0, post, post, lh) for x, y in corners]
    for x in (0, frame_w - srt):
        solids.append(box(x, post - EPS, lh - srh, srt, frame_d - 2 * post + 2 * EPS, srh))
    solids.append(box(post - EPS, frame_d - rrt, lh - rrh, frame_w - 2 * post + 2 * EPS, rrt, rrh))
    ob = union(solids, "layer")
    difference(ob, sockets(0, -1) + sockets(lh, 1))
    clean(ob)
    return ob


def build_top():
    tt, bh, rh, rt = D("top_t"), D("top_boss_h"), D("rim_h"), D("rim_t")
    mac_w, mac_d, gap = D("mac_w"), D("mac_d"), D("mac_gap")
    mac_x, mac_y = (frame_w - mac_w) / 2, (frame_d - mac_d) / 2
    solids = [box(0, 0, 0, frame_w, frame_d, tt, "plate")]
    for x, y in corners:
        solids.append(box(x, y, 0, post, post, tt + bh))
    # outer rim as four bars (overlapping at the corners is fine for the union)
    solids.append(box(0, 0, tt - EPS, frame_w, rt, rh + EPS))
    solids.append(box(0, frame_d - rt, tt - EPS, frame_w, rt, rh + EPS))
    solids.append(box(0, 0, tt - EPS, rt, frame_d, rh + EPS))
    solids.append(box(frame_w - rt, 0, tt - EPS, rt, frame_d, rh + EPS))
    if D("stops"):
        st, sl, sh = D("stop_t"), D("stop_len"), D("stop_h")
        solids.append(box(mac_x - gap - st, frame_d / 2 - sl / 2, tt - EPS, st, sl, sh + EPS))
        solids.append(box(mac_x + mac_w + gap, frame_d / 2 - sl / 2, tt - EPS, st, sl, sh + EPS))
        solids.append(box(frame_w / 2 - sl / 2, mac_y - gap - st, tt - EPS, sl, st, sh + EPS))
        solids.append(box(frame_w / 2 - sl / 2, mac_y + mac_d + gap, tt - EPS, sl, st, sh + EPS))
    ob = union(solids, "top")
    cutters = sockets(0, -1)
    if D("vents"):
        vi, vw, vp = D("vent_inset"), D("vent_w"), D("vent_pitch")
        vx0, vx1 = mac_x + vi, mac_x + mac_w - vi
        vy0, vy1 = mac_y + vi, mac_y + mac_d - vi
        n = int(math.floor((vx1 - vx0 - vw) / vp)) + 1
        x_start = (vx0 + vx1) / 2 - ((n - 1) * vp + vw) / 2
        for i in range(n):
            cutters.append(box(x_start + i * vp, vy0, -EPS, vw, vy1 - vy0, tt + 2 * EPS))
    difference(ob, cutters)
    clean(ob)
    return ob


def pin_points(ox=0, oy=0, oz=0):
    p, L, c = D("pin"), D("pin_len"), D("pin_chamfer")
    pts = []
    for (x0, x1, y0, y1, z) in ((c, p - c, c, p - c, 0), (0, p, 0, p, c), (0, p, 0, p, L - c), (c, p - c, c, p - c, L)):
        for x in (x0, x1):
            for y in (y0, y1):
                pts.append((ox + x, oy + y, oz + z))
    return pts


def build_pin():
    return hull_obj("pin", pin_points())


def build_test():
    clearances = D("test_clearances")
    pitch = post
    h = socket_depth + 3
    block = box(0, 0, 0, pitch * len(clearances), post, h, "test-coupon")
    cutters = []
    for i, cl in enumerate(clearances):
        s = D("pin") + cl
        cutters.append(box(i * pitch + (pitch - s) / 2, (post - s) / 2, 3, s, s, socket_depth + EPS))
    difference(block, cutters)
    clean(block)
    pin = build_pin()
    to_print_orientation_pin(pin)
    transform_verts(pin, lambda v: (v.x, v.y + post + 8, v.z))
    return join([block, pin], "test-coupon")


# --------------------------------------------------------------------- print orientation
def to_print_orientation_layer(ob):
    lh = D("layer_h")
    transform_verts(ob, lambda v: (v.x, frame_d - v.y, lh - v.z))


def to_print_orientation_pin(ob):
    p = D("pin")
    transform_verts(ob, lambda v: (v.x, v.z, p - v.y))


# --------------------------------------------------------------------- export
def export_stl(ob, filename):
    os.makedirs(STL_DIR, exist_ok=True)
    path = os.path.join(STL_DIR, filename)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, ascii_format=False)
    else:  # Blender < 4.2
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True)
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
    bpy.context.view_layer.update()
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
    bpy.context.view_layer.update()  # new objects need this before matrix_world is valid
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
    sc = bpy.context.scene
    lo, hi = scene_bounds(objs)
    center = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    radius = (Vector(hi) - Vector(lo)).length / 2
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "PERSP"
    cam_data.lens = lens
    cam_data.sensor_fit = "AUTO"
    cam_data.clip_end = 20000
    w, h = sc.render.resolution_x, sc.render.resolution_y
    sensor = 36.0
    fov_w = 2 * math.atan(sensor / (2 * lens))
    fov_h = 2 * math.atan(sensor * (h / w) / (2 * lens)) if w >= h else 2 * math.atan(sensor / (2 * lens))
    fov = min(fov_w, fov_h)
    dist = radius / math.sin(fov / 2) * margin
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    # tighten: project the bbox corners and shrink the distance until they fill the frame
    from bpy_extras.object_utils import world_to_camera_view
    corners8 = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    for _ in range(4):
        cam.location = center + d * dist
        bpy.context.view_layer.update()
        dev = 0.0
        for c in corners8:
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


def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


GREY = (0.45, 0.48, 0.52, 1)
BLUE_A = (0.69, 0.77, 0.87, 1)
BLUE_B = (0.27, 0.51, 0.71, 1)
ORANGE = (0.95, 0.60, 0.20, 1)
GHOST_X = (0.15, 0.65, 0.25, 1)
GHOST_M = (0.75, 0.25, 0.25, 1)


def place_stack(parts, gap=0.0, with_pins=False, ghosts=True):
    """Lay out base + layers + top (+ pins) along z; gap>0 gives an exploded view."""
    base_t, boss_h, lh, tt = D("base_t"), D("base_boss_h"), D("layer_h"), D("top_t")
    n = int(D("layers"))
    objs = []
    z_joint = base_t + boss_h  # plane where base meets layer 1
    objs.append(copy_obj(parts["base"], "a_base", 0, 0, 0, GREY))
    for i in range(n):
        z = base_t + boss_h + i * lh
        objs.append(copy_obj(parts["layer"], f"a_layer{i}", 0, 0, z + (i + 1) * gap, BLUE_A if i % 2 == 0 else BLUE_B))
    z_top = base_t + inner_h
    objs.append(copy_obj(parts["top"], "a_top", 0, 0, z_top + (n + 1) * gap, GREY))
    if with_pins:
        L = D("pin_len")
        for j in range(n + 1):
            zj = z_joint + j * lh + j * gap + gap / 2 - L / 2
            for x, y in corners:
                objs.append(copy_obj(parts["pin"], f"a_pin{j}", x + (post - D("pin")) / 2, y + (post - D("pin")) / 2, zj, ORANGE))
    if ghosts:
        objs.append(ghost_box("xbox", xbox_x, xbox_y, base_t, D("xbox_w"), D("xbox_d"), D("xbox_h"), GHOST_X))
        objs.append(ghost_box("mac", (frame_w - D("mac_w")) / 2, (frame_d - D("mac_d")) / 2,
                              z_top + (n + 1) * gap + tt, D("mac_w"), D("mac_d"), D("mac_h"), GHOST_M))
    return objs


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    do_render = "--no-render" not in args

    bpy.ops.wm.read_factory_settings(use_empty=True)
    clear_scene()
    print(f"layerdock: boolean solver {SOLVER}; inner height {inner_h} mm; plug zone {plug_zone} mm")

    parts = {
        "base": build_base(),
        "layer": build_layer(),
        "top": build_top(),
        "pin": build_pin(),
    }
    test = build_test()

    # --- STL in print orientation
    export_stl(parts["base"], "base.stl")
    export_stl(parts["top"], "top.stl")
    layer_p = copy_obj(parts["layer"], "layer_print")
    to_print_orientation_layer(layer_p)
    export_stl(layer_p, "layer.stl")
    pin_p = copy_obj(parts["pin"], "pin_print")
    to_print_orientation_pin(pin_p)
    export_stl(pin_p, "pin.stl")
    export_stl(test, "test-coupon.stl")

    for name, ob in list(parts.items()) + [("layer.stl", layer_p), ("pin.stl", pin_p), ("test", test)]:
        lo, hi = bbox(ob)
        print(f"  {name:10s} bbox {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm")

    if not do_render:
        return

    setup_render()
    # hide the masters; renders use copies
    for ob in list(parts.values()) + [layer_p, pin_p, test]:
        ob.hide_render = True

    # --- assembled view
    tot_h = D("base_t") + inner_h + D("top_t") + D("top_boss_h")
    objs = place_stack(parts, gap=0, with_pins=False, ghosts=True)
    camera_look(objs, (-1.0, -1.6, 0.7))
    render(os.path.join(IMG_DIR, "assembly.png"))
    for ob in list(bpy.data.objects):
        if ob.name.startswith(("a_", "xbox", "mac", "cam")):
            delete(ob)

    # --- exploded view with pins
    gap = 45
    n = int(D("layers"))
    objs = place_stack(parts, gap=gap, with_pins=True, ghosts=False)
    camera_look(objs, (-1.0, -1.6, 0.55))
    render(os.path.join(IMG_DIR, "exploded.png"))
    for ob in objs + [bpy.context.scene.camera]:
        delete(ob)

    # --- parts in print orientation, side by side
    row = [("base", parts["base"], GREY), ("layer", layer_p, BLUE_B), ("top", parts["top"], GREY),
           ("pin", pin_p, ORANGE), ("test", test, ORANGE)]
    x = 0
    objs = []
    for name, ob, col in row:
        lo, hi = bbox(ob)
        objs.append(copy_obj(ob, f"p_{name}", x - lo[0], -lo[1], -lo[2], col))
        x += (hi[0] - lo[0]) + 30
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 750
    camera_look(objs, (-0.25, -1.0, 1.0), lens=60)
    render(os.path.join(IMG_DIR, "parts.png"))


if __name__ == "__main__":
    main()
