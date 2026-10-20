// =====================================================================
//  layerdock — modular, 3D-printable device stand   (v0.1.1)
//  Base + Layer × N + Top.  Every joint is an integrated square peg
//  (on top of each post) pressed into a square socket (in the bottom of
//  the next part).  No separate pins, screws or glue.
//
//  Default use case: Mac mini (M4) on top, Xbox Series S standing
//  vertically inside the frame, removable straight out of the front.
//
//  Units: mm.  Printer: Bambu Lab A1 mini (180 × 180 mm bed).
//  Every part prints as ONE piece, in the orientation it is modelled
//  (z up = print up), with no supports.
//
//  Coordinate convention:
//    x = left → right (frame width)      y = front → back (frame depth)
//    z = up.   The front of the stand is y = 0 (the open side).
//
//  Render one part:   openscad -D 'part="layer"' -o stl/layer.stl scad/layerdock.scad
//  tools/build_stl.py (Blender) reads the SAME parameter block below and
//  rebuilds identical geometry, so STLs can be made without OpenSCAD.
//  Keep the two in sync: every module here has a build_*() twin there.
// =====================================================================

/* [Output] */
// Which part to render
part = "assembly"; // [assembly, base, layer, top, test, joint]
// Number of Layer pieces stacked in the assembly preview
layers = 5;

/* [Device A: Xbox Series S, standing vertically, power button facing front] */
// Width across the front (the thin 63.5 mm face faces you)
xbox_w = 63.5;
// Depth front→back (the 151 mm face runs along the sides)
xbox_d = 151;
// Height when standing vertically
xbox_h = 275;
// How far the Xbox's front face sticks out past the front of the frame (easy to grab)
xbox_front_overhang = 8;
// Free space required behind the Xbox for HDMI / power plugs (checked, not modelled)
xbox_min_plug_zone = 22;
// Headroom required above the Xbox before the Top plate
xbox_headroom = 10;

/* [Device B: Mac mini (M4 = 127 × 127 × 50)] */
mac_w = 127;
mac_d = 127;
mac_h = 50;
// Clearance between Mac mini and the positioning stops on the Top tray (per side)
mac_gap = 1.5;

/* [Frame] */
// Outer width of every part.  166 leaves 7 mm per side on the 180 mm bed for a brim.
frame_w = 166;
// Outer depth of every part.  172 leaves 4 mm per side for a brim.
frame_d = 172;
// Corner post cross-section (square)
post = 20;
// Height of one Layer piece
layer_h = 60;
// Left/right rails of a Layer: thickness (x) and height (z).  Rails sit at the BOTTOM of the Layer.
side_rail_t = 8;
side_rail_h = 20;
// Rear rail of a Layer: thickness (y) and height (z).  Keep thin: it eats the plug zone.
rear_rail_t = 6;
rear_rail_h = 20;

/* [Joint: integrated square peg + socket] */
// Peg side (square).  Post wall around the socket = (post - peg) / 2 - socket_fit
peg = 11;
// Peg height = engagement depth
peg_h = 12;
// Chamfer on the top edges of the peg (lead-in)
peg_chamfer = 1.5;
// Socket clearance per side.  Printed holes come out ~0.1 mm small; crush ribs absorb the rest.
socket_fit = 0.15;
// Extra socket depth so the peg never bottoms out before the post faces meet
socket_extra = 0.5;
// 45° chamfer at the socket mouth (kills elephant foot, guides the peg)
socket_mouth_chamfer = 0.8;
// Four thin ribs inside each socket that get crushed by the peg → zero-play friction fit
crush_ribs = true;
// Rib width along the wall
rib_w = 1.2;
// Rib protrusion into the socket
rib_h = 0.35;
// Socket clearances on the test coupon (front → back)
test_fits = [0.05, 0.15, 0.25];

/* [Base] */
// Base plate thickness
base_t = 5;
// Height of the four corner bosses the pegs grow from
base_boss_h = 6;
// Two low ribs that centre the Xbox when sliding it in
guides = true;
guide_h = 3;
guide_w = 4;
// Gap between Xbox side and guide rib
guide_gap = 2;
guide_len = 110;
// Distance of the guide ribs from the front edge
guide_setback = 15;
// Low rib behind the Xbox so it always stops with the plug zone free
rear_stop = true;

/* [Top] */
// Top plate thickness
top_t = 4;
// Corner bosses on the Top (project upward, sockets open downward).  Sockets always sit on
// the post grid, so keep this >= socket + 2 × wall; 20 = same as the posts.
top_boss = 20;
top_boss_h = 14;
// Low rim around the tray edge
rim_h = 3;
rim_t = 2.4;
// Four positioning stops around the Mac mini footprint
stops = true;
stop_h = 3;
stop_t = 3;
stop_len = 36;
// Ventilation slots under the Mac mini (it breathes through its bottom)
vents = true;
vent_w = 5;
vent_pitch = 10;
// Solid border kept around the vent field, measured from the Mac mini footprint
vent_inset = 8;

/* [Hidden] */
socket = peg + 2 * socket_fit;
socket_depth = peg_h + socket_extra;
eps = 0.01;
xbox_x = (frame_w - xbox_w) / 2;
xbox_y = -xbox_front_overhang;
plug_zone = (frame_d - rear_rail_t) - (xbox_y + xbox_d);
inner_w = frame_w - 2 * post;
inner_h = base_boss_h + layers * layer_h; // base plate top → Top plate underside
total_h = base_t + inner_h + top_t + top_boss_h;
wall = (post - peg) / 2 - socket_fit;
mac_x = (frame_w - mac_w) / 2;
mac_y = (frame_d - mac_d) / 2;

// ---------------------------------------------------------------- checks
echo(str("layerdock: inner width ", inner_w, " mm, inner height ", inner_h,
         " mm, plug zone behind Xbox ", plug_zone, " mm, total height ", total_h,
         " mm, socket wall ", wall, " mm"));
if (max(frame_w, frame_d) > 180)
    echo("WARNING: frame exceeds the 180 mm A1 mini bed");
if (inner_h < xbox_h + xbox_headroom)
    echo(str("WARNING: inner height ", inner_h, " < Xbox ", xbox_h, " + headroom ", xbox_headroom,
             " — add a Layer (layers=", layers, ")"));
if (plug_zone < xbox_min_plug_zone)
    echo(str("WARNING: only ", plug_zone, " mm behind the Xbox for plugs (want ", xbox_min_plug_zone, ")"));
if (inner_w < xbox_w + 2 * guide_gap + 2 * guide_w + 10)
    echo("WARNING: Xbox + guides do not fit between the posts");
if (wall < 3)
    echo(str("WARNING: socket wall only ", wall, " mm; enlarge post or shrink peg"));
if (top_boss < post || socket_depth + 2 > top_t + top_boss_h)
    echo("WARNING: Top boss too small for the socket");
if (mac_x < top_boss && mac_y < top_boss)
    echo("WARNING: Mac mini footprint overlaps the Top corner bosses");
if (frame_w / 2 - stop_len / 2 < top_boss || frame_d / 2 - stop_len / 2 < top_boss)
    echo("WARNING: Mac mini stops collide with the Top corner bosses");

// ---------------------------------------------------------------- helpers
function corners(size) = [[0, 0], [frame_w - size, 0], [0, frame_d - size], [frame_w - size, frame_d - size]];

// Integrated peg growing upward from z0, centred on a `post`-sized square whose corner is (x, y).
module peg_at(x, y, z0) {
    c = peg_chamfer;
    translate([x + (post - peg) / 2, y + (post - peg) / 2, z0 - eps])
        hull() {
            cube([peg, peg, peg_h - c + eps]);
            translate([c, c, 0]) cube([peg - 2 * c, peg - 2 * c, peg_h + eps]);
        }
}

// Socket cutter: opens at z = 0 (the part's bottom face) and goes up.  Centred on a
// `size`-sized square whose corner is (x, y).  Includes the mouth chamfer; the crush
// ribs are subtracted from the cutter so they remain as material in the part.
module socket_cutter_at(x, y, size, fit = socket_fit) {
    cx = x + size / 2;
    cy = y + size / 2;
    s = peg + 2 * fit;
    mc = socket_mouth_chamfer;
    difference() {
        union() {
            translate([cx - s / 2, cy - s / 2, -eps]) cube([s, s, socket_depth + eps]);
            hull() {
                translate([cx - s / 2 - mc, cy - s / 2 - mc, -eps]) cube([s + 2 * mc, s + 2 * mc, eps]);
                translate([cx - s / 2, cy - s / 2, mc]) cube([s, s, eps]);
            }
        }
        if (crush_ribs) {
            z0 = mc + 1;
            zl = socket_depth + 1 - z0;
            translate([cx + s / 2 - rib_h, cy - rib_w / 2, z0]) cube([rib_h + 1, rib_w, zl]);
            translate([cx - s / 2 - 1, cy - rib_w / 2, z0]) cube([rib_h + 1, rib_w, zl]);
            translate([cx - rib_w / 2, cy + s / 2 - rib_h, z0]) cube([rib_w, rib_h + 1, zl]);
            translate([cx - rib_w / 2, cy - s / 2 - 1, z0]) cube([rib_w, rib_h + 1, zl]);
        }
    }
}

// ---------------------------------------------------------------- BASE
module base() {
    union() {
        cube([frame_w, frame_d, base_t]);
        for (c = corners(post)) {
            translate([c[0], c[1], 0]) cube([post, post, base_t + base_boss_h]);
            peg_at(c[0], c[1], base_t + base_boss_h);
        }
        if (guides)
            for (sx = [-1, 1])
                translate([frame_w / 2 + sx * (xbox_w / 2 + guide_gap + guide_w / 2) - guide_w / 2,
                           guide_setback, base_t - eps])
                    cube([guide_w, guide_len, guide_h + eps]);
        if (rear_stop)
            translate([xbox_x - guide_gap, xbox_y + xbox_d + 1, base_t - eps])
                cube([xbox_w + 2 * guide_gap, 3, guide_h + eps]);
    }
}

// ---------------------------------------------------------------- LAYER
// Four posts, left/right rails and a rear rail at the BOTTOM of the piece (so it prints
// flat with the sockets on the bed), pegs on top.  The front is completely open and
// nothing crosses the Xbox space.
module layer() {
    difference() {
        union() {
            for (c = corners(post)) {
                translate([c[0], c[1], 0]) cube([post, post, layer_h]);
                peg_at(c[0], c[1], layer_h);
            }
            for (x = [0, frame_w - side_rail_t])
                translate([x, post - eps, 0]) cube([side_rail_t, frame_d - 2 * post + 2 * eps, side_rail_h]);
            translate([post - eps, frame_d - rear_rail_t, 0])
                cube([frame_w - 2 * post + 2 * eps, rear_rail_t, rear_rail_h]);
        }
        for (c = corners(post)) socket_cutter_at(c[0], c[1], post);
    }
}

// ---------------------------------------------------------------- TOP
module top() {
    difference() {
        union() {
            cube([frame_w, frame_d, top_t]);
            for (c = corners(top_boss))
                translate([c[0], c[1], 0]) cube([top_boss, top_boss, top_t + top_boss_h]);
            // outer rim
            translate([0, 0, top_t - eps]) difference() {
                cube([frame_w, frame_d, rim_h + eps]);
                translate([rim_t, rim_t, -eps]) cube([frame_w - 2 * rim_t, frame_d - 2 * rim_t, rim_h + 3 * eps]);
            }
            if (stops) {
                translate([mac_x - mac_gap - stop_t, frame_d / 2 - stop_len / 2, top_t - eps])
                    cube([stop_t, stop_len, stop_h + eps]);
                translate([mac_x + mac_w + mac_gap, frame_d / 2 - stop_len / 2, top_t - eps])
                    cube([stop_t, stop_len, stop_h + eps]);
                translate([frame_w / 2 - stop_len / 2, mac_y - mac_gap - stop_t, top_t - eps])
                    cube([stop_len, stop_t, stop_h + eps]);
                translate([frame_w / 2 - stop_len / 2, mac_y + mac_d + mac_gap, top_t - eps])
                    cube([stop_len, stop_t, stop_h + eps]);
            }
        }
        for (c = corners(post)) socket_cutter_at(c[0], c[1], post); // on the post grid
        if (vents) {
            vx0 = mac_x + vent_inset;
            vx1 = mac_x + mac_w - vent_inset;
            vy0 = mac_y + vent_inset;
            vy1 = mac_y + mac_d - vent_inset;
            n = floor((vx1 - vx0 - vent_w) / vent_pitch) + 1;
            x_start = (vx0 + vx1) / 2 - ((n - 1) * vent_pitch + vent_w) / 2;
            for (i = [0 : n - 1])
                translate([x_start + i * vent_pitch, vy0, -eps])
                    cube([vent_w, vy1 - vy0, top_t + 2 * eps]);
        }
    }
}

// ---------------------------------------------------------------- TEST COUPON
// A bar with len(test_fits) sockets (different clearances, front → back) and a short post
// stub with one peg.  Print both, push the peg into each socket, pick the fit you like.
test_bar_h = socket_depth + 3;
test_stub_h = 8;
module test_part() {
    pitch = post;
    difference() {
        cube([pitch * len(test_fits), post, test_bar_h]);
        // sockets open at z = 0, i.e. mouth on the bed, exactly like the Layer and Top
        for (i = [0 : len(test_fits) - 1]) {
            socket_cutter_at(i * pitch, 0, post, test_fits[i]);
            // i+1 grooves on the front face next to socket i: 1 groove = test_fits[0], 2 = [1], ...
            for (k = [0 : i])
                translate([i * pitch + pitch / 2 + (k - i / 2) * 3 - 0.6, -eps, 2])
                    cube([1.2, 0.8 + eps, test_bar_h]);
        }
    }
    translate([0, post + 10, 0]) {
        cube([post, post, test_stub_h]);
        peg_at(0, 0, test_stub_h);
    }
}

// ---------------------------------------------------------------- JOINT close-up (section)
// One corner of the Base and the bottom 30 mm of one Layer post, cut in half, pulled apart.
module joint() {
    gap = 10;
    difference() {
        union() {
            intersection() { base(); cube([post + 10, post + 10, 100]); }
            translate([0, 0, base_t + base_boss_h + gap])
                intersection() { layer(); cube([post + 10, post + 10, 30]); }
        }
        translate([-1, -100, -1]) cube([post + 20, 100 + post / 2, 200]); // remove the front half
    }
}

// ---------------------------------------------------------------- ASSEMBLY
module assembly() {
    color("SlateGray") base();
    for (i = [0 : layers - 1])
        color(i % 2 == 0 ? "LightSteelBlue" : "SteelBlue")
            translate([0, 0, base_t + base_boss_h + i * layer_h]) layer();
    color("SlateGray") translate([0, 0, base_t + inner_h]) top();
    // ghost devices
    %translate([xbox_x, xbox_y, base_t]) cube([xbox_w, xbox_d, xbox_h]);
    %translate([mac_x, mac_y, base_t + inner_h + top_t]) cube([mac_w, mac_d, mac_h]);
}

// ---------------------------------------------------------------- OUTPUT
if (part == "assembly") assembly();
else if (part == "base") base();
else if (part == "layer") layer();
else if (part == "top") top();
else if (part == "test") test_part();
else if (part == "joint") joint();
