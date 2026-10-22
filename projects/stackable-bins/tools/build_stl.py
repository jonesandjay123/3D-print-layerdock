"""
Build the Stackable Bins STLs and preview renders with Blender (headless).

Geometry twin of scad/stackable-bins.scad: every number comes from the
parameter block at the top of the .scad (parsed below), so the .scad is the
single source of truth for dimensions.  The bin and lid are built as ONE
closed mesh each by sweeping a 2-D wall profile (inward offset, z) around the
rounded-rectangle outline and capping the floor — no booleans are needed, so
the result is watertight by construction.  Booleans are only used for the
coupon's notches and for the sectioned preview renders.

Usage:
    blender -b --python-exit-code 1 -P tools/build_stl.py -- [--no-render]

Outputs:
    stl/bin.stl, stl/lid.stl, stl/test-coupon.stl
    docs/images/assembly.png, exploded.png, parts.png, joint.png, section.png
"""
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAD = os.path.join(ROOT, "scad", "stackable-bins.scad")
STL_DIR = os.path.join(ROOT, "stl")
IMG_DIR = os.path.join(ROOT, "docs", "images")
N_ARC = 16  # segments per 90° corner arc


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
bin_w, bin_d, corner_r, bin_h = D("bin_w"), D("bin_d"), D("corner_r"), D("bin_h")
wall, floor_t, sc = D("wall"), D("floor_t"), D("seam_chamfer")
lip_h, lip_t, lc, fit = D("lip_h"), D("lip_t"), D("lip_chamfer"), D("fit")
skirt_t, gmc, foot_t = D("skirt_t"), D("groove_mouth_chamfer"), D("foot_t")
groove_w = lip_t + 2 * fit
groove_depth = lip_h + D("groove_extra")
rim_t = skirt_t + fit + lip_t
bottom_t = skirt_t + groove_w + foot_t
foot_h = groove_depth + D("foot_extra")
lid_h = groove_depth + D("lid_t")
hole_off = 6.0
rim_zone = D("rim_zone")
hood_h, cover_depth, tray_h = D("hood_h"), D("cover_depth"), D("tray_h")
tray_wall, tray_floor, tray_fit = D("tray_wall"), D("tray_floor"), D("tray_fit")
ledge_w, ledge_h, tray_front_r = D("ledge_w"), D("ledge_h"), D("tray_front_r")
ledge_z = hood_h - tray_h
tray_w = bin_w - 2 * wall - 2 * tray_fit
tray_d = cover_depth - wall - tray_fit
tray_back_r = corner_r - wall - tray_fit
roof_front_h, roof_back_h, roof_setback = D("roof_front_h"), D("roof_back_h"), D("roof_setback")
roof_t, roof_lip, roof_fit = D("roof_t"), D("roof_lip"), D("roof_fit")
roof_y0 = bin_d - cover_depth + roof_setback
roof_yc = bin_d - roof_lip - roof_fit          # back end of the roof (inside the back wall's lip)
roof_a = roof_yc - roof_y0
roof_b = roof_back_h - roof_front_h


def roof_curve(dz=0.0):
    """Outer curve of the roof, front (vertical tangent) to back (horizontal tangent), z relative to the hood rim."""
    return [(roof_yc - roof_a * math.cos(math.radians(k * 3)), roof_front_h + dz + roof_b * math.sin(math.radians(k * 3)))
            for k in range(31)]
N_BINS = int(D("bins"))


# --------------------------------------------------------------------- mesh helpers
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


def transform_verts(ob, fn):
    for v in ob.data.vertices:
        v.co = Vector(fn(v.co))
    ob.data.update()


def clean(ob):
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


# --------------------------------------------------------------------- rounded-rectangle sweep (twin of rrect/prism/loft in the .scad)
def rounded_loop(w, d, r, off, z):
    """Counter-clockwise outline of a w × d rounded rectangle offset inward by `off`, at height z.
    `r` is one corner radius or four (back-right, back-left, front-left, front-right; y = 0 is
    the front).  The arc centres never move; only the radius shrinks, exactly like OpenSCAD's
    offset()."""
    radii = list(r) if isinstance(r, (list, tuple)) else [r] * 4
    centres = [(w - radii[0], d - radii[0], 0.0), (radii[1], d - radii[1], 90.0),
               (radii[2], radii[2], 180.0), (w - radii[3], radii[3], 270.0)]
    pts = []
    for (cx, cy, a0), ri in zip(centres, radii):
        rr = ri - off
        assert rr > 1e-6, f"offset {off} >= corner radius {ri}"
        for k in range(N_ARC + 1):
            a = math.radians(a0 + 90.0 * k / N_ARC)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
    return pts


def sweep(name, w, d, r, profile, closed=False):
    """Sweep a wall profile [(off, z), ...] around the outline.  Open profile (default): its two
    ends must have the same offset (the floor hole boundary) and each end loop is capped with one
    n-gon.  Closed profile: the last loop connects back to the first (a ring with no floor).
    Returns a watertight object."""
    loops = [rounded_loop(w, d, r, off, z) for off, z in profile]
    n = len(loops[0])
    verts = [p for loop in loops for p in loop]
    faces = []
    m = len(loops) if closed else len(loops) - 1
    for i in range(m):
        a, b = i * n, ((i + 1) % len(loops)) * n
        for j in range(n):
            k = (j + 1) % n
            faces.append((a + j, a + k, b + k, b + j))
    if not closed:
        faces.append(tuple(range(0, n)))                               # cap at the first loop
        faces.append(tuple(range((len(loops) - 1) * n, len(loops) * n)))  # cap at the last loop
    ob = mesh_obj(name, verts, faces)
    clean(ob)
    if volume(ob) < 0:  # make normals point outward
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    return ob


def yz_prism(name, pts, x0, x1):
    """Prism along x of a simple polygon given in the (y, z) plane."""
    n = len(pts)
    verts = [(x0, y, z) for y, z in pts] + [(x1, y, z) for y, z in pts]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    ob = mesh_obj(name, verts, faces)
    clean(ob)
    if volume(ob) < 0:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    return ob


def groove_profile(f):
    """Profile of the underside groove (open at z = 0), outward from the floor to the outer skirt."""
    gw = lip_t + 2 * f
    return [(skirt_t + gw + gmc, 0), (skirt_t + gw, gmc), (skirt_t + gw, groove_depth),
            (skirt_t, groove_depth), (skirt_t, gmc), (skirt_t - gmc, 0)]


# --------------------------------------------------------------------- parts (twins of the .scad modules)
def bin_body(w, d, r, h, name="bin"):
    prof = [(hole_off, 0)] + groove_profile(fit) + [
        (sc, 0), (0, sc), (0, h - sc), (sc, h),                      # outer face with seam chamfers
        (skirt_t + fit, h), (skirt_t + fit, h + lip_h - lc),          # rim flat, lip outer face
        (skirt_t + fit + lc, h + lip_h), (rim_t - lc, h + lip_h),     # lip top with lead-in chamfers
        (rim_t, h + lip_h - lc), (rim_t, h - rim_zone)]              # lip inner face = rim zone inner face
    if rim_t > wall:
        prof.append((wall, h - rim_zone - (rim_t - wall)))           # 45° step out to the main wall
    prof += [(wall, foot_h), (bottom_t, foot_h),                      # main cavity, foot ledge
             (bottom_t, floor_t), (hole_off, floor_t)]                # foot inner face, floor top
    return sweep(name, w, d, r, prof)


def lid_body(w, d, r, f, name="lid"):
    lec = D("lid_edge_chamfer")
    g = [(off, lid_h - z) for off, z in reversed(groove_profile(f))]  # flipped: opens at z = lid_h
    prof = [(hole_off, 0), (lec, 0), (0, lec), (0, lid_h - sc), (sc, lid_h)] + g + [(hole_off, lid_h)]
    return sweep(name, w, d, r, prof)


def build_bin():
    return bin_body(bin_w, bin_d, corner_r, bin_h)


def build_hood():
    """Three walls + the bottom groove ring, open at the front above the ring, inner ledge for the
    tray; side and back walls rise above the rim under the roof curve."""
    h = hood_h + roof_back_h
    prof = [(sc, 0), (0, sc), (0, h), (wall, h),
            (wall, ledge_z), (wall + ledge_w, ledge_z), (wall + ledge_w, ledge_z - ledge_h),
            (wall, ledge_z - ledge_h - ledge_w),                          # 45° under the ledge
            (wall, foot_h), (bottom_t, foot_h), (bottom_t, 0)] + groove_profile(fit)
    ob = sweep("hood", bin_w, bin_d, corner_r, prof, closed=True)
    above = [(-10, hood_h), (roof_y0, hood_h)] + [(y, z + hood_h) for y, z in roof_curve()] + \
        [(bin_d + 10, hood_h + roof_back_h), (bin_d + 10, 400), (-10, 400)]
    difference(ob, [box(-1, -1, foot_h, bin_w + 2, bin_d - cover_depth + 1, h + 2)])   # open front
    clean(ob)
    difference(ob, [yz_prism("above_roof", above, -1, bin_w + 1)])                     # walls stop at the roof curve
    clean(ob)
    # rebate for the roof: inside the outer lip (offset >= roof_lip) the wall top is roof_t lower
    y0 = roof_y0 - roof_fit
    rebate = [(y0, hood_h + roof_front_h - roof_t)] + [(y, z + hood_h) for y, z in roof_curve(-roof_t)] + \
        [(bin_d + 10, hood_h + roof_back_h - roof_t), (bin_d + 10, 400), (y0, 400)]
    cutter = yz_prism("rebate", rebate, -1, bin_w + 1)
    inside = sweep("inside", bin_w, bin_d, corner_r, [(hole_off, hood_h), (roof_lip, hood_h), (roof_lip, 500), (hole_off, 500)])
    intersection(cutter, inside)
    difference(ob, [cutter])
    clean(ob)
    assert len(ob.data.vertices) > 0, "hood boolean produced an empty mesh"
    return ob


def build_roof(in_use=False):
    """Curved roof plate that drops into the rebate along the hood's side and back walls.  Modelled
    in use orientation (z relative to the hood rim); exported lying on its side for printing."""
    outer = roof_curve()
    inner = roof_curve(-roof_t)
    x0 = roof_lip + roof_fit
    ob = yz_prism("roof", outer + inner[::-1], x0, bin_w - x0)
    clean(ob)
    if not in_use:  # rotate onto its side: x -> z, keep everything at >= 0
        transform_verts(ob, lambda v: (v.z, v.y, v.x))  # a mirror: re-orient the faces
        clean(ob)
        if volume(ob) < 0:
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            bm.to_mesh(ob.data)
            bm.free()
        lo, _ = bbox(ob)
        transform_verts(ob, lambda v: (v.x - lo[0], v.y - lo[1], v.z - lo[2]))
    return ob


def build_tray():
    radii = (tray_back_r, tray_back_r, tray_front_r, tray_front_r)
    ho = tray_wall + 0.3
    prof = [(ho, 0), (0, 0), (0, tray_h), (tray_wall, tray_h), (tray_wall, tray_floor), (ho, tray_floor)]
    return sweep("tray", tray_w, tray_d, radii, prof)


def build_lid():
    return lid_body(bin_w, bin_d, corner_r, fit)


def text_cutter(text, cx, cy, z_top, size, depth):
    """Extruded text (readable from +z) whose top is at z_top, going `depth` down: subtract it to engrave."""
    cu = bpy.data.curves.new("txt", type="FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = depth / 2 + 0.5
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    e = depth / 2 + 0.5                     # converted mesh spans z in [-e, e]
    transform_verts(ob, lambda v: (v.x + cx, v.y + cy, v.z + z_top - depth + e))  # -> [z_top - depth, z_top + 1]
    clean(ob)
    if volume(ob) < 0:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    return ob


def build_test():
    tw, td, tr, th = D("test_w"), D("test_d"), D("test_r"), D("test_h")
    ts, tdp = D("test_text_size"), D("test_text_depth")
    mini = bin_body(tw, td, tr, th, "test-bin")
    difference(mini, [text_cutter("BIN", tw / 2, td / 2, floor_t, ts, tdp)])  # on the floor, read from above
    parts = [mini]
    for i, f in enumerate(D("test_fits")):
        cap = lid_body(tw, td, tr, f, f"test-lid{i}")
        x0, y0 = (i + 1) % 2 * (tw + 8), ((i + 1) // 2) * (td + 8)   # 2 × 2 grid, same as the .scad
        transform_verts(cap, lambda v, x0=x0, y0=y0: (v.x + x0, v.y + y0, v.z))
        notches = [box(x0 + tw / 2 + (k - i / 2) * 3 - 0.5, y0 - 1, -1, 1.0, 1.5, lid_h + 2) for k in range(i + 1)]
        # the fit value engraved on the groove side (printed top surface), read from above
        label = text_cutter(f"{f:.2f}", x0 + tw / 2, y0 + td / 2, lid_h, ts, tdp)
        difference(cap, notches + [label])
        parts.append(cap)
    ob = join(parts, "test-coupon")
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
def copy_obj(ob, name, dx=0, dy=0, dz=0, color=(0.8, 0.8, 0.8, 1), flip=False):
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    if flip:  # rotate 180° about x: print orientation -> in-use orientation (lid)
        transform_verts(new, lambda v: (v.x, bin_d - v.y, lid_h - v.z))
    new.location = (dx, dy, dz)
    new.color = color
    new.hide_render = False
    bpy.context.scene.collection.objects.link(new)
    return new


def ghost_box(name, x, y, z, sx, sy, sz, color):
    ob = box(x, y, z, sx, sy, sz, name)
    mod = ob.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 2.0
    mod.use_even_offset = True
    ob.color = color
    return ob


def setup_render(width=1400, height=1100):
    sc_ = bpy.context.scene
    sc_.render.engine = "BLENDER_WORKBENCH"
    sc_.render.resolution_x = width
    sc_.render.resolution_y = height
    sc_.render.resolution_percentage = 100
    sc_.render.image_settings.file_format = "PNG"
    sh = sc_.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_object_outline = True
    sh.show_cavity = True
    sh.show_shadows = False
    sh.background_type = "WORLD"
    world = bpy.data.worlds.new("world")
    world.color = (0.96, 0.96, 0.95)
    sc_.world = world
    sc_.render.film_transparent = False
    sc_.view_settings.view_transform = "Standard"
    sc_.display.render_aa = "8"


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


def camera_look(objs, direction, lens=50, margin=1.06, ortho=False):
    from bpy_extras.object_utils import world_to_camera_view
    sc_ = bpy.context.scene
    lo, hi = scene_bounds(objs)
    center = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    radius = (Vector(hi) - Vector(lo)).length / 2
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO" if ortho else "PERSP"
    cam_data.lens = lens
    cam_data.clip_end = 20000
    w, h = sc_.render.resolution_x, sc_.render.resolution_y
    fov = 2 * math.atan(36.0 * min(1.0, h / w) / (2 * lens))
    dist = radius / math.sin(fov / 2) * margin
    cam = bpy.data.objects.new("cam", cam_data)
    sc_.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc_.camera = cam
    pts = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    if ortho:
        cam.location = center + d * (radius * 4)
        cam_data.ortho_scale = 2 * radius * margin
        for _ in range(4):
            bpy.context.view_layer.update()
            dev = max(max(abs(u - 0.5), abs(v - 0.5)) for u, v, _ in (world_to_camera_view(sc_, cam, c) for c in pts))
            cam_data.ortho_scale *= (dev / 0.5) * margin
        return cam
    for _ in range(4):
        cam.location = center + d * dist
        bpy.context.view_layer.update()
        dev = 0.0
        for c in pts:
            u, v, _ = world_to_camera_view(sc_, cam, c)
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
        if ob.name.startswith(("a_", "p_", "j_", "s_", "tissue", "cam")):
            delete(ob)


IVORY = (0.86, 0.84, 0.80, 1)
IVORY_B = (0.74, 0.72, 0.68, 1)
BLUE_B = (0.27, 0.51, 0.71, 1)
ORANGE = (0.95, 0.60, 0.20, 1)
GHOST = (0.25, 0.55, 0.30, 1)


def place_stack(parts, gap=0.0, ghost=True, alternate=False, top="hood"):
    objs = []
    for i in range(N_BINS):
        col = IVORY_B if (alternate and i % 2) else IVORY
        objs.append(copy_obj(parts["bin"], f"a_bin{i}", 0, 0, i * (bin_h + gap), col))
    z_lid = N_BINS * bin_h + N_BINS * gap
    if top == "hood":
        objs.append(copy_obj(parts["hood"], "a_hood", 0, 0, z_lid, IVORY))
        objs.append(copy_obj(parts["tray"], "a_tray", wall + tray_fit, bin_d - cover_depth, z_lid + ledge_z + gap,
                             IVORY_B if alternate else IVORY))
        objs.append(copy_obj(parts["roof_use"], "a_roof", 0, 0, z_lid + hood_h + 2 * gap, IVORY_B if alternate else IVORY))
        return objs
    objs.append(copy_obj(parts["lid"], "a_lid", 0, 0, z_lid, IVORY, flip=True))
    if ghost:
        tw, td, th = D("tissue_w"), D("tissue_d"), D("tissue_h")
        objs.append(ghost_box("tissue", (bin_w - tw) / 2, (bin_d - td) / 2, z_lid + lid_h, tw, td, th, GHOST))
    return objs


def build_joint(gap):
    """One corner of two stacked bins, 40 × 40 mm, cut open at y = 20 to show the joint."""
    lower = build_bin()
    upper = build_bin()
    transform_verts(upper, lambda v: (v.x, v.y, v.z + bin_h + gap))
    ob = union([lower, upper], "joint")
    intersection(ob, box(-1, -1, bin_h - 22, 41, 21, 44 + gap))
    clean(ob)
    return ob


def build_section():
    """Top bin + hood + tray + roof cut in half at x = bin_w / 2, one half kept (side section)."""
    z0 = (N_BINS - 1) * bin_h
    top = build_bin()
    transform_verts(top, lambda v: (v.x, v.y, v.z + z0))
    hood = build_hood()
    transform_verts(hood, lambda v: (v.x, v.y, v.z + N_BINS * bin_h))
    tray = build_tray()
    transform_verts(tray, lambda v: (v.x + wall + tray_fit, v.y + bin_d - cover_depth, v.z + N_BINS * bin_h + ledge_z))
    roof = build_roof(in_use=True)
    transform_verts(roof, lambda v: (v.x, v.y, v.z + N_BINS * bin_h + hood_h))
    parts = [top, hood, tray, roof]
    for ob in parts:
        intersection(ob, box(bin_w / 2, -5, z0 - 1, bin_w, bin_d + 10, 400))
    ob = join(parts, "section")
    clean(ob)
    return ob


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    do_render = "--no-render" not in args

    bpy.ops.wm.read_factory_settings(use_empty=True)
    for ob in list(bpy.data.objects):
        delete(ob)
    iw, idp, ih = bin_w - 2 * wall, bin_d - 2 * wall, bin_h - floor_t
    ir = corner_r - wall
    cavity_l = (iw * idp - (4 - math.pi) * ir * ir) * ih / 1e6
    print(f"stackable-bins v0.1: solver {SOLVER}; inner cavity {iw:.1f} x {idp:.1f} x {ih:.1f} mm "
          f"(~{cavity_l:.2f} L); printed bin height {bin_h + lip_h:.2f} mm; lid {lid_h:.2f} mm; "
          f"stack of {N_BINS} = {N_BINS * bin_h + lid_h:.1f} mm; rim_t {rim_t:.2f}; bottom_t {bottom_t:.2f}; "
          f"groove {groove_w:.2f} x {groove_depth:.2f}; bearing ring {skirt_t - sc - gmc:.2f} mm")
    if rim_t < wall:
        print("WARNING: rim_t < wall")
    if bin_h + lip_h > 180:
        print("WARNING: bin taller than 180 mm")

    parts = {"bin": build_bin(), "lid": build_lid(), "hood": build_hood(), "tray": build_tray(), "roof": build_roof(),
             "test": build_test()}
    for name, ob in parts.items():
        export_stl(ob, {"test": "test-coupon"}.get(name, name) + ".stl")
        lo, hi = bbox(ob)
        print(f"  {name:5s} bbox {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
              f"volume {volume(ob)/1000:.1f} cm3")

    if not do_render:
        return

    setup_render()
    parts["roof_use"] = build_roof(in_use=True)
    for ob in parts.values():
        ob.hide_render = True

    objs = place_stack(parts, gap=0, top="hood")
    camera_look(objs, (-1.0, -1.5, 0.55))
    render(os.path.join(IMG_DIR, "assembly.png"))
    clear_render_objects()

    objs = place_stack(parts, gap=0, top="hood")
    camera_look(objs, (0.9, -1.3, 0.9))
    render(os.path.join(IMG_DIR, "assembly-top.png"))
    clear_render_objects()

    objs = place_stack(parts, gap=0, ghost=True, top="lid")
    camera_look(objs, (-1.0, -1.5, 0.55))
    render(os.path.join(IMG_DIR, "assembly-lid.png"))
    clear_render_objects()

    objs = place_stack(parts, gap=45, alternate=True, top="hood")
    camera_look(objs, (-1.0, -1.5, 0.5))
    render(os.path.join(IMG_DIR, "exploded.png"))
    clear_render_objects()

    bpy.context.scene.render.resolution_x = 2200
    bpy.context.scene.render.resolution_y = 800
    x = 0
    objs = []
    for name, col in (("bin", IVORY), ("lid", IVORY), ("hood", IVORY), ("tray", IVORY), ("roof", IVORY), ("test", ORANGE)):
        ob = parts[name]
        lo, hi = bbox(ob)
        objs.append(copy_obj(ob, f"p_{name}", x - lo[0], -lo[1], -lo[2], col))
        x += (hi[0] - lo[0]) + 30
    camera_look(objs, (-0.3, -1.0, 0.8), lens=60)
    render(os.path.join(IMG_DIR, "parts.png"))
    clear_render_objects()

    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 900
    j_open = build_joint(gap=10)
    j_closed = build_joint(gap=0)
    objs = [copy_obj(j_open, "j_open", 0, 0, 0, BLUE_B), copy_obj(j_closed, "j_closed", 60, 0, 0, BLUE_B)]
    j_open.hide_render = True
    j_closed.hide_render = True
    camera_look(objs, (0.35, 1.0, 0.4), lens=70)
    render(os.path.join(IMG_DIR, "joint.png"))
    clear_render_objects()

    # joint section detail: a 2-D cut through one wall of the engaged joint, viewed square on
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1000
    jd = build_joint(gap=0)
    intersection(jd, box(-1, 10, bin_h - 14, 14, 20, 28))  # the straight wall at x 0..13, between the cut and the corner
    objs = [copy_obj(jd, "j_detail", 0, 0, 0, BLUE_B)]
    jd.hide_render = True
    camera_look(objs, (0.0, -1.0, 0.0), ortho=True, margin=1.15)
    render(os.path.join(IMG_DIR, "joint-section.png"))
    clear_render_objects()

    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1200
    s = build_section()
    objs = [copy_obj(s, "s_section", 0, 0, 0, BLUE_B)]
    s.hide_render = True
    camera_look(objs, (-1.0, 0.0, 0.0), ortho=True, margin=1.04)
    render(os.path.join(IMG_DIR, "section.png"))


if __name__ == "__main__":
    main()
