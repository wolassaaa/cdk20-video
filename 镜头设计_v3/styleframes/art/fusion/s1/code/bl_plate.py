"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: the static table. Rendered once as two versions; base.py wipes from one to the other, so the liquid can run without a render per frame.

Run: bash gpu_slot.sh blender.exe -b -t 4 -P bl_plate.py -- <strip|map|s2|drugs> <e|l|f> <out.png> [samples] [size]
size 1 is for 1080p, 2 for 4K. drugs renders only the medicines station, for checking the models. Plates too big for the denoiser go tile by tile and stitch.py joins them.
e: bare glass, pale figures, no drops. l: e with liquid in the glass. f: l with red figures, drops, the lens.
"""
import math
import os
import subprocess
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
sys.path[:0] = [HERE, HERE + "../../code/"]
import world as W      # noqa: E402
import bl_shots as B   # noqa: E402

P, gk = B.P, B.gk
argv = sys.argv[sys.argv.index("--") + 1:]
WHAT, STATE, OUT = argv[0], argv[1], argv[2]
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
SIZE = int(argv[4]) if len(argv) > 4 else 1
FULL = STATE == "f"
LIQUID = STATE in "lf"


def u(xy, z=0.0):
    return (xy[0] / W.PPU, -xy[1] / W.PPU, z)


def pipe(pts, r_px, mat, name, z=W.SURFACE_Z / W.PPU, taper=None):
    """A bevelled line through the table points. taper gives a radius factor per point."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r_px / W.PPU, 8
    cu.use_fill_caps = True
    s = cu.splines.new("POLY")
    s.points.add(len(pts) - 1)
    for i, (q, xy) in enumerate(zip(s.points, pts)):
        q.co = (*u(xy, z), 1)
        if taper:
            q.radius = taper[i]
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o


def glass_pipe(pts, taper=None):
    o = pipe(pts, W.TUBE_R, B.clear_glass(), "glass", taper=taper)
    o.visible_shadow = False
    o.visible_diffuse = False


def figure(cx, cy, h, mat):
    """The same plain person shape as the stand-in in F2, flat on the table. Schematic."""
    half = [(0, 435), (60, 420), (98, 360), (104, 300), (92, 235), (62, 185), (52, 150), (56, 120), (100, 92), (210, 62), (270, 30), (300, -30), (315, -120), (330, -300), (340, -420)]
    ctrl = half + [(-x, y) for x, y in reversed(half[1:])]
    n, pts = len(ctrl), []
    for i in range(n):
        a, b_, c, d = [Vector(ctrl[(i + k) % n]) for k in (-1, 0, 1, 2)]
        for t in (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            pts.append(0.5 * ((2 * b_) + (c - a) * t + (2 * a - 5 * b_ + 4 * c - d) * t * t + (3 * b_ - a - 3 * c + d) * t ** 3))
    k = h / 855.0
    poly = [((cx + q.x * k) / W.PPU, -(cy - (q.y - 7.5) * k) / W.PPU) for q in pts]
    B.extrude([poly], 0.05, 0.02, name="figure", mat=mat)


def bead(xy, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r / W.PPU, location=u(xy, W.SURFACE_Z / W.PPU), scale=(1, 1, 0.8), segments=64, ring_count=32)
    o = bpy.context.object
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()


def revolve(profile, cx, cy, mat, name, rest=None):
    """Turns a (radius, along) profile in table px about a line lying on the table and pointing up the screen. rest is the line's height."""
    n, rest = 96, rest or W.VIAL_R
    verts, faces = [], []
    for r, a in profile:
        for j in range(n):
            q = 2 * math.pi * j / n
            verts.append(((cx + r * math.cos(q)) / W.PPU, -(cy - a) / W.PPU, (rest + r * math.sin(q)) / W.PPU))
    for i in range(len(profile) - 1):
        for j in range(n):
            k = (j + 1) % n
            faces.append((i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    B.smooth(o)
    return o


def vial(cx, cy, glass, liquid, cap, label, seal):
    """A generic injection vial lying on the table. Schematic, no maker's marks."""
    o = revolve([(0, -125), (54, -125), (62, -117), (62, 52), (55, 68), (41, 84), (38, 96), (0, 96)], cx, cy, glass, "vial")
    o.visible_shadow = False
    revolve([(0, -116), (52, -116), (56, -110), (56, 46), (0, 46)], cx, cy, liquid, "dose")
    revolve([(0, -84), (63.5, -84), (63.5, 16), (0, 16)], cx, cy, label, "label")
    revolve([(0, 92), (44, 92), (46, 96), (46, 112), (0, 112)], cx, cy, seal, "seal")
    revolve([(0, 112), (40, 112), (40, 126), (36, 130), (0, 130)], cx, cy, cap, "cap")


def sample_tube(cx, cy, glass, liquid, cap):
    """A generic sample tube lying on the map, with a blue cap. Schematic."""
    k = 0.22
    o = revolve([(r * k, a * k) for r, a in [(0, -190), (34, -176), (42, -150), (42, 150), (0, 150)]], cx, cy, glass, "sample", 10)
    o.visible_shadow = False
    revolve([(r * k, a * k) for r, a in [(0, -178), (30, -166), (36, -146), (36, 30), (0, 30)]], cx, cy, liquid, "sample_dose", 10)
    revolve([(r * k, a * k) for r, a in [(0, 150), (46, 150), (46, 205), (0, 205)]], cx, cy, cap, "sample_cap", 10)


def blister(cx, cy):
    """A generic foil strip of round tablets. Schematic, no maker's marks."""
    foil, nt, out = gk._mat("foil")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.78, 0.78, 0.80, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.34
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    w, h = 200, 112
    corners = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
    B.extrude([B.round_poly([(x / W.PPU, -y / W.PPU) for x, y in corners], 0.09)], 0.03, 0.01, name="foil", mat=foil)
    tablet = P.gloss((0.32, 0.012, 0.008), 0.25, 0.6)
    dome = B.clear_glass()
    for row in (-1, 1):
        for col in (-1.5, -0.5, 0.5, 1.5):
            xy = (cx + col * 92, cy + row * 50)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=30 / W.PPU, location=(xy[0] / W.PPU, -xy[1] / W.PPU, 0.09), scale=(1, 1, 0.4), segments=64, ring_count=32)
            o = bpy.context.object
            o.data.materials.append(tablet)
            bpy.ops.object.shade_smooth()
            bpy.ops.mesh.primitive_uv_sphere_add(radius=38 / W.PPU, location=(xy[0] / W.PPU, -xy[1] / W.PPU, 0.04), scale=(1, 1, 0.55), segments=64, ring_count=32)
            o = bpy.context.object
            o.data.materials.append(dome)
            o.visible_shadow = False
            bpy.ops.object.shade_smooth()


def medicines():
    glass, ink_paper = B.clear_glass(), gk.surface((0.86, 0.85, 0.81), 0.5, 0.2)
    liquid = B.fluid((0.72, 0.78, 0.92), (0.9, 0.92, 0.96))
    cap = P.gloss(P.KLEIN, 0.25, 0.6)
    seal = gk.surface((0.62, 0.62, 0.64), 0.35, 0.5)
    blister(*W.BLISTER)
    for xy in W.VIALS:
        vial(*xy, glass, liquid, cap, ink_paper, seal)


def strip():
    red_fluid = B.fluid(P.RED, (0.9, 0.05, 0.03))
    pale = gk.surface((0.70, 0.69, 0.655), 0.55, 0.15)
    red = P.gloss(P.RED, 0.2, 0.6)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    for k in ("main_a", "main_b", "liver", "prot"):
        glass_pipe(W.PATHS[k])
        if LIQUID:
            o = pipe(W.PATHS[k], W.FLUID_R, red_fluid, "liquid")
            o.visible_diffuse = False
    glass_pipe(W.ROAD_TUBE)
    for xy in W.FOUR:
        figure(*xy, 62, red if FULL else pale)
    for xy in W.TEN:
        figure(*xy, 170, red if FULL else pale)
    for xy in W.STUDENTS:
        figure(*xy, 100, red if FULL else pale)
    for xy in W.BEADS:
        bead(xy, 34, red if FULL else pale)
    if FULL:
        for xy in W.DROPS:
            bead(xy, 34, red)
        x, y, r = W.LENS
        bpy.ops.mesh.primitive_cylinder_add(vertices=256, radius=r / W.PPU, depth=0.1, location=u((x, y), 0.05))
        bpy.context.object.data.materials.append(gk.surface((0.93, 0.925, 0.89), 0.6, 0.15))
        bpy.ops.mesh.primitive_torus_add(major_radius=r / W.PPU, minor_radius=3.5 / W.PPU, location=u((x, y), 0.1), major_segments=256, minor_segments=20)
        bpy.context.object.data.materials.append(ink)
        B.smooth(bpy.context.object)
    if FULL:
        medicines()
    for i, xy in enumerate(W.STATIONS):
        B.bulb(xy[0] / W.PPU, -xy[1] / W.PPU, W.SURFACE_Z / W.PPU, 0.31, ink, red_fluid if FULL and i == 0 else None, width=0.022)


def hk():
    land = gk.surface((0.74, 0.725, 0.67), 0.7, 0.1)
    n = 0
    for r in W.HK["rings_simple"]:
        pts = [W.m2w(*p) for p in r["p"]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) < W.MAP[0] or min(xs) > W.MAP[2] or max(ys) < W.MAP[1] or min(ys) > W.MAP[3]:
            continue
        poly = [(x / W.PPU, -y / W.PPU) for x, y in pts]
        if poly[0] == poly[-1]:
            poly = poly[:-1]
        B.extrude([poly], 0.02, 0.006, name="land", mat=land)
        n += 1
    print("LAND", n)
    pts, n = W.PATHS["map"] + W.PATHS["exit"][1:], len(W.PATHS["map"])
    k = [min(1, max(0.3, 1 - 0.7 * i / (n * 0.45)) + max(0, i - len(pts) + 90) / 90 * 0.7) for i in range(len(pts))]    # the line thins as it comes ashore, and widens again just before the map's edge
    glass_pipe(pts, taper=k)
    if LIQUID:
        o = pipe(pts, W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid", taper=k)
        o.visible_diffuse = False
    if FULL:
        glass, liquid, cap = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03)), P.gloss(P.KLEIN, 0.25, 0.6)
        for xy in W.SAMPLES:
            sample_tube(*xy, glass, liquid, cap)


def s2():
    glass_pipe(W.PATHS["s2"])
    if LIQUID:
        o = pipe(W.PATHS["s2"], W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid")
        o.visible_diffuse = False


def render_tiles(w, h):
    """The denoiser runs out of memory on a whole 4K plate, so big plates go in overlapping tiles."""
    cols, rows = math.ceil(w / 5000), math.ceil(h / 4400)
    if cols * rows == 1:
        gk.render(OUT)
        return
    r, lap = sc.render, 64
    r.use_border, r.use_crop_to_border = True, True
    sc.render.use_persistent_data = True
    for j in range(rows):
        for i in range(cols):
            a, b = max(0, i * w // cols - lap), min(w, (i + 1) * w // cols + lap)
            c, d = max(0, j * h // rows - lap), min(h, (j + 1) * h // rows + lap)
            r.border_min_x, r.border_max_x = (a + 0.25) / w, (b + 0.25) / w
            r.border_min_y, r.border_max_y = (h - d + 0.25) / h, (h - c + 0.25) / h
            gk.render("%s_%d_%d.png" % (OUT[:-4], i, j))
    subprocess.run(["python", HERE + "stitch.py", OUT, str(w), str(h), str(cols), str(rows), str(lap)], check=True)


x0, y0, x1, y1 = {"strip": W.STRIP, "map": W.MAP, "s2": W.S2_STRIP, "drugs": (3840, 0, 5760, 1080)}[WHAT]
k = (W.MAP_SCALE if WHAT == "map" else 1) * SIZE
sc = P.scene(samples=SAMPLES, w=(x1 - x0) * k, h=(y1 - y0) * k)
sc.cycles.denoising_use_gpu = True
P.floor()
bpy.data.objects["floor"].scale = (5, 5, 1)    # the S2 table runs past the floor's usual edge
P.sun()
c = P.camera(W.PPU)
c.data.ortho_scale = (x1 - x0) / W.PPU
c.location = ((x0 + x1) / 2 / W.PPU, -(y0 + y1) / 2 / W.PPU, 20)
if WHAT == "drugs":
    medicines()
else:
    {"strip": strip, "map": hk, "s2": s2}[WHAT]()
sc.cycles.caustics_refractive = False
render_tiles((x1 - x0) * k, (y1 - y0) * k)
