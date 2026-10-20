// =====================================================================
//  layerdock — modular, 3D-printable device stand
//  Base + Layer × N + Top, joined with separately printed square pins.
//
//  Default use case: a Mac mini (M4) on top, an Xbox Series S standing
//  vertically inside the frame, removable straight out of the front.
//
//  Units: mm.  Printer: Bambu Lab A1 mini (180 × 180 mm bed).
//  Every part prints as a single piece with no supports.
//
//  Coordinate convention (assembly):
//    x = left → right (frame width)      y = front → back (frame depth)
//    z = up.   The front of the stand is y = 0 (the open side).
//
//  Render one part:   openscad -D 'part="layer"' -D print_orientation=true \
//                              -o stl/layer.stl scad/layerdock.scad
//  The same parameters are read by tools/build_stl.py (Blender mirror).
// =====================================================================

/* [Output] */
// Which part to render
part = "assembly"; // [assembly, base, layer, top, pin, test]
// Rotate the part into its print orientation (rails of the Layer down, pin lying flat)
print_orientation = false;
// Number of Layer pieces stacked in the assembly preview
layers = 5;

/* [Device A: Xbox Series S (standing vertically, power button facing front)] */
// Width across the front (the thin 63.5 mm face faces you)
xbox_w = 63.5;
// Depth front→back (the 151 mm face runs along the sides)
xbox_d = 151;
// Height when standing vertically
xbox_h = 275;
// How far the Xbox's front face sticks out past the front of the frame (easy to grab)
xbox_front_overhang = 6;
// Free space required behind the Xbox for HDMI / power plugs (only checked, not modelled)
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
// Outer width of every part (must fit the 180 mm bed)
frame_w = 170;
// Outer depth of every part (must fit the 180 mm bed)
frame_d = 175;
// Corner post cross-section (square)
post = 18;
// Height of one Layer piece
layer_h = 60;
// Left/right rails of a Layer: thickness (x) and height (z)
side_rail_t = 8;
side_rail_h = 20;
// Rear rail of a Layer: thickness (y) and height (z).  Keep thin: it eats the plug zone.
rear_rail_t = 6;
rear_rail_h = 20;

/* [Base] */
// Base plate thickness
base_t = 5;
// Height of the four corner bosses that carry the sockets
base_boss_h = 12;
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
// Corner bosses on the Top (project upward, sockets open downward)
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

/* [Pins] */
// Square pin side
pin = 8;
// Total pin length (half goes into each part)
pin_len = 30;
// Socket = pin + socket_clear.  0.4 is the PETG starting point; print the test coupon first.
socket_clear = 0.4;
// Extra socket depth so the pin never bottoms out before the parts meet
socket_extra = 0.5;
// Chamfer on the pin ends
pin_chamfer = 1;
// Socket clearances on the test coupon (front -> back)
test_clearances = [0.2, 0.4, 0.6];

/* [Hidden] */
socket = pin + socket_clear;
socket_depth = pin_len / 2 + socket_extra;
eps = 0.01;
xbox_x = (frame_w - xbox_w) / 2;
xbox_y = -xbox_front_overhang;
plug_zone = (frame_d - rear_rail_t) - (xbox_y + xbox_d);
inner_w = frame_w - 2 * post;
inner_h = base_boss_h + layers * layer_h; // from base plate top to Top plate underside
total_h = base_t + inner_h + top_t + top_boss_h;

// ---------------------------------------------------------------- checks
echo(str("layerdock: inner width ", inner_w, " mm, inner height ", inner_h,
         " mm, plug zone behind Xbox ", plug_zone, " mm, total height ", total_h, " mm"));
if (max(frame_w, frame_d) > 180)
    echo("WARNING: frame exceeds the 180 mm A1 mini bed");
if (inner_h < xbox_h + xbox_headroom)
    echo(str("WARNING: inner height ", inner_h, " < Xbox ", xbox_h, " + headroom ", xbox_headroom,
             " — add a Layer (layers=", layers, ")"));
if (plug_zone < xbox_min_plug_zone)
    echo(str("WARNING: only ", plug_zone, " mm behind the Xbox for plugs (want ", xbox_min_plug_zone, ")"));
if (inner_w < xbox_w + 2 * guide_gap + 2 * guide_w + 10)
    echo("WARNING: Xbox + guides do not fit between the posts");
if (mac_w + 2 * mac_gap + 2 * stop_t > frame_w - 2 * post ||
    mac_d + 2 * mac_gap + 2 * stop_t > frame_d - 2 * post)
    echo("WARNING: Mac mini stops collide with the Top corner bosses");

// ---------------------------------------------------------------- helpers
function corners() = [[0, 0], [frame_w - post, 0], [0, frame_d - post], [frame_w - post, frame_d - post]];

// One square socket, open at z = z_open, going `up` (+1) or down (-1).
module socket_at(x, y, z_open, up = 1) {
    translate([x + (post - socket) / 2, y + (post - socket) / 2,
               up > 0 ? z_open - eps : z_open - socket_depth])
        cube([socket, socket, socket_depth + eps]);
}

module sockets(z_open, up = 1) {
    for (c = corners()) socket_at(c[0], c[1], z_open, up);
}

// ---------------------------------------------------------------- BASE
module base() {
    difference() {
        union() {
            cube([frame_w, frame_d, base_t]);
            for (c = corners())
                translate([c[0], c[1], 0]) cube([post, post, base_t + base_boss_h]);
            if (guides)
                for (sx = [-1, 1])
                    translate([frame_w / 2 + sx * (xbox_w / 2 + guide_gap + guide_w / 2) - guide_w / 2,
                               guide_setback, base_t - eps])
                        cube([guide_w, guide_len, guide_h + eps]);
            if (rear_stop)
                translate([xbox_x - guide_gap, xbox_y + xbox_d + 1, base_t - eps])
                    cube([xbox_w + 2 * guide_gap, 3, guide_h + eps]);
        }
        sockets(base_t + base_boss_h, 1);
    }
}

// ---------------------------------------------------------------- LAYER
// Four posts + left/right rails + rear rail, all at the top of the piece.
// The front is completely open; nothing crosses the Xbox space.
module layer() {
    difference() {
        union() {
            for (c = corners())
                translate([c[0], c[1], 0]) cube([post, post, layer_h]);
            // side rails, flush with the outer faces
            for (x = [0, frame_w - side_rail_t])
                translate([x, post - eps, layer_h - side_rail_h])
                    cube([side_rail_t, frame_d - 2 * post + 2 * eps, side_rail_h]);
            // rear rail, flush with the back
            translate([post - eps, frame_d - rear_rail_t, layer_h - rear_rail_h])
                cube([frame_w - 2 * post + 2 * eps, rear_rail_t, rear_rail_h]);
        }
        sockets(0, -1);          // bottom sockets open downward
        sockets(layer_h, 1);     // top sockets open upward
    }
}

// ---------------------------------------------------------------- TOP
module top() {
    mac_x = (frame_w - mac_w) / 2;
    mac_y = (frame_d - mac_d) / 2;
    difference() {
        union() {
            cube([frame_w, frame_d, top_t]);
            // corner bosses (upward), they double as corner stops
            for (c = corners())
                translate([c[0], c[1], 0]) cube([post, post, top_t + top_boss_h]);
            // outer rim
            translate([0, 0, top_t - eps]) difference() {
                cube([frame_w, frame_d, rim_h + eps]);
                translate([rim_t, rim_t, -eps]) cube([frame_w - 2 * rim_t, frame_d - 2 * rim_t, rim_h + 3 * eps]);
            }
            // Mac mini stops: one centred on each side of its footprint
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
        sockets(0, -1);          // sockets open downward, into the bosses
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

// ---------------------------------------------------------------- PIN
module pin_part() {
    c = pin_chamfer;
    hull() {
        translate([c, c, 0]) cube([pin - 2 * c, pin - 2 * c, eps]);
        translate([0, 0, c]) cube([pin, pin, pin_len - 2 * c]);
        translate([c, c, pin_len - eps]) cube([pin - 2 * c, pin - 2 * c, eps]);
    }
}

// ---------------------------------------------------------------- TEST COUPON
// Three sockets with test_clearances (front → back) plus one pin.
module test_part() {
    pitch = post;
    difference() {
        cube([pitch * len(test_clearances), post, socket_depth + 3]);
        for (i = [0 : len(test_clearances) - 1]) {
            s = pin + test_clearances[i];
            translate([i * pitch + (pitch - s) / 2, (post - s) / 2, 3]) cube([s, s, socket_depth + eps]);
        }
    }
    translate([0, post + 8, 0]) rotate([-90, 0, 0]) translate([0, -pin, 0]) pin_part();
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
    %translate([(frame_w - mac_w) / 2, (frame_d - mac_d) / 2, base_t + inner_h + top_t])
        cube([mac_w, mac_d, mac_h]);
}

// ---------------------------------------------------------------- OUTPUT
if (part == "assembly") assembly();
else if (part == "base") base();
else if (part == "layer") {
    // print with the rails on the bed: rotate 180° about x
    if (print_orientation) translate([0, frame_d, layer_h]) rotate([180, 0, 0]) layer();
    else layer();
}
else if (part == "top") top();
else if (part == "pin") {
    if (print_orientation) rotate([-90, 0, 0]) translate([0, -pin, 0]) pin_part();
    else pin_part();
}
else if (part == "test") test_part();
