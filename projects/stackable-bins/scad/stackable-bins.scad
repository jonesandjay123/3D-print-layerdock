// =====================================================================
//  LayerDock Stackable Bins   (v0.1)
//  Independent storage bins that stack into one clean, rounded column,
//  plus one flat lid.  Two STLs: bin.stl and lid.stl.
//
//  Stacking joint ("hidden lip + groove"):
//    * the top of every bin has a thin LIP rising from the inner side of
//      the rim;  the outer part of the rim stays flat.
//    * the underside of every bin (and of the lid) has a matching GROOVE
//      just inside its outer edge.  The lip of the bin below enters that
//      groove, so the stack cannot slide sideways, and the outer walls end
//      up flush with only a fine seam between them.
//    * weight is carried by the flat outer rim of the lower bin and the
//      flat outer skirt of the upper bin (face to face), never by the lip.
//    * everything prints upright, floor on the bed, with no supports: the
//      only overhang is the groove ceiling, a bridge of groove_w (1.5 mm).
//
//  Units: mm.  Printer: Bambu Lab A1 mini (180 × 180 × 180 mm).
//  Coordinate convention: x = width, y = depth, z = up (= print up).
//  The lid is modelled in its PRINT orientation (top face on the bed,
//  groove opening upward); the assembly preview flips it.
//
//  Render one part:  openscad -D 'part="bin"' -o stl/bin.stl scad/stackable-bins.scad
//  tools/build_stl.py (Blender) reads the SAME parameter block below and
//  builds identical geometry, so STLs can be made without OpenSCAD.
// =====================================================================

/* [Output] */
// Which part to render
part = "assembly"; // [assembly, bin, lid, test, joint]
// Number of bins in the assembly preview
bins = 3;

/* [Bin outer shape] */
// Outer width (x).  166 leaves 7 mm per side on the 180 mm bed.
bin_w = 166;
// Outer depth (y).  172 leaves 4 mm per side.
bin_d = 172;
// Radius of the four vertical corners
corner_r = 12;
// Height of the outer wall (the lip adds lip_h on top; printed height = bin_h + lip_h <= 180)
bin_h = 120;
// Main wall thickness (4–5 perimeters with a 0.4 nozzle)
wall = 2.0;
// Floor thickness (solid, continuous)
floor_t = 2.0;
// Chamfer on the outer top and bottom edges: the two chamfers meet at every seam as a fine V line
seam_chamfer = 0.3;

/* [Stacking joint] */
// Height of the lip above the rim
lip_h = 5;
// Lip thickness
lip_t = 1.0;
// Chamfer on the lip's top edges (lead-in)
lip_chamfer = 0.4;
// Horizontal clearance between lip and groove, per side.  Coupon test 2026-10-21 (PLA): 0.20 was the tightest of 0.20/0.25/0.30 and still felt a little loose; Jones chose to go one step tighter (0.15, untested on the coupon).
fit = 0.15;
// Vertical clearance between lip top and groove ceiling
groove_extra = 0.25;
// Thickness of the outer skirt below the groove (this ring carries the stack)
skirt_t = 1.5;
// Chamfer on the groove mouth edges (counters elephant foot on the first layer)
groove_mouth_chamfer = 0.3;
// Thickness of the inner skirt (foot) on the inner side of the groove
foot_t = 1.2;
// Solid height above the groove ceiling before the foot ledge
foot_extra = 0.8;
// Height of the thickened rim zone at the top of the wall that carries the lip
rim_zone = 6;

/* [Lid] */
// Solid plate thickness above the groove
lid_t = 3.0;
// Chamfer on the lid's top outer edge
lid_edge_chamfer = 1.0;

/* [Fit test coupon: a mini bin + three mini lids with different fits] */
test_w = 50;
test_d = 42;
test_r = 8;
test_h = 14;
test_fits = [0.20, 0.25, 0.30];
// Engraved labels: text height and depth ("0.20" etc. on the groove side of each mini lid, "BIN" on the mini bin's floor)
test_text_size = 7;
test_text_depth = 0.6;

/* [Preview only] */
// Tissue box drawn as a wireframe on the lid in the assembly preview
tissue_w = 230;
tissue_d = 115;
tissue_h = 80;

/* [Hidden] */
groove_w = lip_t + 2 * fit;                 // 1.5
groove_depth = lip_h + groove_extra;        // 5.25
rim_t = skirt_t + fit + lip_t;              // 2.75: wall thickness in the rim zone; lip inner face is flush with it
bottom_t = skirt_t + groove_w + foot_t;     // 4.2: wall thickness at the very bottom (skirt + groove + foot)
foot_h = groove_depth + foot_extra;         // 6.05
lid_h = groove_depth + lid_t;               // 8.25
hole_off = 6;                               // where the swept wall profile stops and the flat floor begins (< corner_r)
tiny = 0.01;
$fn = 64;

// ---- checks (printed to the console)
echo(str("inner cavity ", bin_w - 2 * wall, " x ", bin_d - 2 * wall, " x ", bin_h - floor_t, " mm"));
echo(str("printed bin height ", bin_h + lip_h, " mm; lid ", lid_h, " mm; stack of ", bins, " = ", bins * bin_h + lid_h, " mm"));
echo(str("rim bearing ring: ", skirt_t - seam_chamfer - groove_mouth_chamfer, " mm wide on a ", skirt_t + fit - seam_chamfer, " mm rim flat"));
if (rim_t < wall) echo("WARNING: rim_t < wall: the lip would stick out past the inner wall");
if (hole_off >= corner_r || hole_off <= bottom_t) echo("WARNING: hole_off must be between bottom_t and corner_r");
if (bin_h + lip_h > 180) echo("WARNING: bin taller than the A1 mini's 180 mm");

// ---- 2D rounded rectangle, offset inward by `off`, for a w × d box with corner radius r
module rrect(w, d, r, off) {
    offset(r = r - off) offset(delta = -r) square([w, d]);
}
module prism(w, d, r, off, z0, z1) {
    translate([0, 0, z0]) linear_extrude(height = z1 - z0) rrect(w, d, r, off);
}
// Loft between two offsets: a 45° chamfer when |off1 - off0| == z1 - z0
module loft(w, d, r, off0, z0, off1, z1) {
    hull() {
        prism(w, d, r, off0, z0, z0 + tiny);
        prism(w, d, r, off1, z1 - tiny, z1);
    }
}

// ---- Bin ------------------------------------------------------------
module bin_body(w, d, r, h) {
    sc = seam_chamfer;
    difference() {
        union() {
            loft(w, d, r, sc, 0, 0, sc);                                   // bottom seam chamfer
            prism(w, d, r, 0, sc, h - sc);                                 // outer wall
            loft(w, d, r, 0, h - sc, sc, h);                               // top seam chamfer
            prism(w, d, r, skirt_t + fit, h, h + lip_h - lip_chamfer);     // lip
            loft(w, d, r, skirt_t + fit, h + lip_h - lip_chamfer, skirt_t + fit + lip_chamfer, h + lip_h);
        }
        // interior
        prism(w, d, r, rim_t, h - rim_zone, h + lip_h + 1);                            // rim zone + inside of the lip
        hull() {  // lip inner chamfer prism(w, d, r, rim_t - lip_chamfer, h + lip_h, h + lip_h + 1); prism(w, d, r, rim_t, h + lip_h - lip_chamfer, h + lip_h - lip_chamfer + tiny); }
        if (rim_t > wall)
            loft(w, d, r, wall, h - rim_zone - (rim_t - wall), rim_t, h - rim_zone + tiny);  // 45° step out to the main wall
        prism(w, d, r, wall, foot_h, h - rim_zone - (rim_t - wall) + tiny);                 // main cavity
        prism(w, d, r, bottom_t, floor_t, foot_h + tiny);                                  // cavity between the feet
        groove(w, d, r);
    }
}
// Groove cut into the underside, open at z = 0, with chamfered mouth
module groove(w, d, r) {
    gmc = groove_mouth_chamfer;
    difference() {
        union() {
            prism(w, d, r, skirt_t, -1, groove_depth);
            hull() { prism(w, d, r, skirt_t - gmc, -1, 0); prism(w, d, r, skirt_t, gmc, gmc + tiny); }
        }
        prism(w, d, r, skirt_t + groove_w, -2, groove_depth + 1);
        hull() { prism(w, d, r, skirt_t + groove_w + gmc, -2, 0); prism(w, d, r, skirt_t + groove_w, gmc, groove_depth + 1); }
    }
}
module bin() { bin_body(bin_w, bin_d, corner_r, bin_h); }

// ---- Lid (print orientation: top face at z = 0, groove opens upward) --
module lid_body(w, d, r, f) {
    sc = seam_chamfer;
    lec = lid_edge_chamfer;
    difference() {
        union() {
            loft(w, d, r, lec, 0, 0, lec);                 // top edge chamfer (on the bed)
            prism(w, d, r, 0, lec, lid_h - sc);
            loft(w, d, r, 0, lid_h - sc, sc, lid_h);       // seam chamfer at the rim side
        }
        // groove, flipped: opens at z = lid_h
        translate([0, 0, lid_h]) mirror([0, 0, 1]) groove_fit(w, d, r, f);
    }
}
module groove_fit(w, d, r, f) {
    gw = lip_t + 2 * f;
    gmc = groove_mouth_chamfer;
    difference() {
        union() {
            prism(w, d, r, skirt_t, -1, groove_depth);
            hull() { prism(w, d, r, skirt_t - gmc, -1, 0); prism(w, d, r, skirt_t, gmc, gmc + tiny); }
        }
        prism(w, d, r, skirt_t + gw, -2, groove_depth + 1);
        hull() { prism(w, d, r, skirt_t + gw + gmc, -2, 0); prism(w, d, r, skirt_t + gw, gmc, groove_depth + 1); }
    }
}
module lid() { lid_body(bin_w, bin_d, corner_r, fit); }

// ---- Fit test coupon: one mini bin + a mini lid per fit, 1/2/3 notches on the front face
module engrave(txt, cx, cy, z_top) {  // text readable from +z, cut test_text_depth down from z_top
    translate([cx, cy, z_top - test_text_depth]) linear_extrude(test_text_depth + 1)
        text(txt, size = test_text_size, halign = "center", valign = "center");
}
module test() {
    difference() { bin_body(test_w, test_d, test_r, test_h); engrave("BIN", test_w / 2, test_d / 2, floor_t); }
    for (i = [0 : len(test_fits) - 1])   // 2 × 2 grid: bin front-left, lids 1 / 2 / 3 clockwise
        translate([(i + 1) % 2 * (test_w + 8), floor((i + 1) / 2) * (test_d + 8), 0]) difference() {
            lid_body(test_w, test_d, test_r, test_fits[i]);
            for (k = [0 : i])
                translate([test_w / 2 + (k - i / 2) * 3 - 0.5, -1, -1]) cube([1.0, 0.5 + 1, lid_h + 2]);
            engrave(str(test_fits[i]), test_w / 2, test_d / 2, lid_h);
        }
}

// ---- Previews --------------------------------------------------------
module lid_in_use(z) {  // flipped from print orientation onto the top of the stack
    translate([0, bin_d, z + lid_h]) rotate([180, 0, 0]) lid();
}
module assembly(gap = 0) {
    for (i = [0 : bins - 1]) translate([0, 0, i * (bin_h + gap)]) bin();
    lid_in_use(bins * bin_h + bins * gap);
    %translate([(bin_w - tissue_w) / 2, (bin_d - tissue_d) / 2, bins * bin_h + lid_h + bins * gap]) cube([tissue_w, tissue_d, tissue_h]);
}
// One corner of two stacked bins, cut open through the joint
module joint(gap = 0) {
    intersection() {
        union() { bin(); translate([0, 0, bin_h + gap]) bin(); }
        translate([-1, -1, bin_h - 25]) cube([40, 40, 50 + gap]);
    }
}

if (part == "assembly") assembly();
else if (part == "bin") bin();
else if (part == "lid") lid();
else if (part == "test") test();
else if (part == "joint") joint(10);
