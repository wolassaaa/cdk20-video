"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: the static table. Rendered once as two versions; base.py wipes from one to the other, so the liquid can run without a render per frame.

Run: bash gpu_slot.sh blender.exe -b -t 4 -P bl_plate.py -- <strip|map> <e|f> <out.png> [samples]
e: bare glass, pale figures, no drops. l: e with liquid in the glass. f: l with red figures, drops, the lens.
"""
import os
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
    pts = W.PATHS["map"]
    k = [max(0.3, 1 - 0.7 * i / (len(pts) * 0.45)) for i in range(len(pts))]    # the line thins as it comes ashore
    glass_pipe(pts, taper=k)
    if LIQUID:
        o = pipe(pts, W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid", taper=k)
        o.visible_diffuse = False


x0, y0, x1, y1 = W.STRIP if WHAT == "strip" else W.MAP
k = 1 if WHAT == "strip" else W.MAP_SCALE
sc = P.scene(samples=SAMPLES, w=(x1 - x0) * k, h=(y1 - y0) * k)
sc.cycles.denoising_use_gpu = True
P.floor()
P.sun()
c = P.camera(W.PPU)
c.data.ortho_scale = (x1 - x0) / W.PPU
c.location = ((x0 + x1) / 2 / W.PPU, -(y0 + y1) / 2 / W.PPU, 20)
(strip if WHAT == "strip" else hk)()
sc.cycles.caustics_refractive = False
gk.render(OUT)
