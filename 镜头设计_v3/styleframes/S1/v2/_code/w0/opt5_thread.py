"""Option 5 · red-thread room (Blender), after Chiharu Shiota's thread installations: red threads stretched through a dark room,
anchored to an empty chair. Blue window light from behind; a little haze.
hit1 one thread pulls taut across the dark; hit2 a few dozen; hit3 the web, and the empty chair it holds.
1-01: four empty chairs held in one web, beside A's card. (Absence, not figures.)
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
scn = reset()
world(scn, (0, 0, 0))
random.seed(11)
shot = A.shot

RW, RD, RH = 7.0, 7.0, 3.6
wallm, _, _ = principled("wall", (0.02, 0.02, 0.022), rough=0.95)
floorm, _, _ = principled("floor", (0.015, 0.015, 0.017), rough=0.6)
box(scn, "floor", (RW, RD, 0.1), (0, 0, -0.05), floorm)
box(scn, "ceil", (RW, RD, 0.1), (0, 0, RH + 0.05), wallm)
box(scn, "wl", (0.1, RD, RH), (-RW / 2, 0, RH / 2), wallm)
box(scn, "wr", (0.1, RD, RH), (RW / 2, 0, RH / 2), wallm)
# back wall with a tall window: blue night light comes through it
WX, WZ, WW, WH = 1.2, 1.9, 1.6, 2.4
yb = RD / 2
box(scn, "bw_l", (WX - WW / 2 + RW / 2, 0.1, RH), ((WX - WW / 2 - RW / 2) / 2, yb, RH / 2), wallm)
box(scn, "bw_r", (RW / 2 - WX - WW / 2, 0.1, RH), ((WX + WW / 2 + RW / 2) / 2, yb, RH / 2), wallm)
box(scn, "bw_b", (WW, 0.1, WZ - WH / 2), (WX, yb, (WZ - WH / 2) / 2), wallm)
box(scn, "bw_t", (WW, 0.1, RH - WZ - WH / 2), (WX, yb, (RH + WZ + WH / 2) / 2), wallm)
bpy.ops.mesh.primitive_plane_add(size=1, location=(WX, yb + 1.0, WZ), rotation=(math.radians(90), 0, 0))
pw = bpy.context.active_object; pw.scale = (WW * 3, WH * 3, 1)
pw.data.materials.append(emission("night", (0.0, 0.05, 1.0), 2.2))
area(scn, "window", 140, WW, (WX, yb + 0.1, WZ), (WX - 0.6, -3, 0.6), (0.0, 0.07, 1.0), size_y=WH, spread=80)

# haze so the window light has a body
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, RH / 2))
hz = bpy.context.active_object; hz.scale = (RW - 0.2, RD - 0.2, RH - 0.05)
hz.data.materials.append(volume("haze", (0.9, 0.92, 1.0), 0.009, aniso=0.5))

# soft white key from front-left, low, so threads read red, chairs bone
area(scn, "key", 200, 2.5, (-2.5, -3.2, 2.6), (0, 0, 0.6), (0.94, 0.96, 1.0))

# ---------------------------------------------------------------- chairs
chairm, _, _ = principled("chair", BONE, rough=0.55)


def chair(cx, cy, rot=0.0):
    parts = []
    c, s = math.cos(rot), math.sin(rot)
    def P(x, y): return (cx + c * x - s * y, cy + s * x + c * y)
    def add(name, size, loc):
        x, y = P(loc[0], loc[1])
        o = box(scn, name, size, (x, y, loc[2]), chairm); o.rotation_euler = (0, 0, rot); parts.append(o)
    add("seat", (0.44, 0.42, 0.035), (0, 0, 0.46))
    for i, (lx, ly) in enumerate([(-0.19, -0.18), (0.19, -0.18), (-0.19, 0.18), (0.19, 0.18)]):
        add("leg%d" % i, (0.03, 0.03, 0.46), (lx, ly, 0.23))
    for i, lx in enumerate((-0.19, 0.19)):
        add("post%d" % i, (0.03, 0.03, 0.48), (lx, 0.19, 0.72))
    add("back", (0.42, 0.025, 0.16), (0, 0.19, 0.86))
    # anchor points for threads: seat edges, back rail, legs
    pts = []
    for _ in range(40):
        t = random.random()
        k = random.random()
        if k < 0.35: lx, ly, lz = random.uniform(-0.22, 0.22), random.choice((-0.21, 0.21)), 0.46
        elif k < 0.6: lx, ly, lz = random.uniform(-0.21, 0.21), 0.19, random.uniform(0.8, 0.94)
        elif k < 0.8: lx, ly, lz = random.choice((-0.19, 0.19)), random.choice((-0.18, 0.18)), random.uniform(0.05, 0.44)
        else: lx, ly, lz = random.choice((-0.19, 0.19)), 0.19, random.uniform(0.5, 0.95)
        x, y = P(lx, ly); pts.append(Vector((x, y, lz)))
    return pts


def wall_point():
    k = random.random()
    if k < 0.3: return Vector((random.choice((-RW / 2 + 0.06, RW / 2 - 0.06)), random.uniform(-0.8, RD / 2), random.uniform(0.2, RH)))
    if k < 0.65: return Vector((random.uniform(-RW / 2, RW / 2), random.uniform(-0.8, RD / 2), RH - 0.06))
    if k < 0.85: return Vector((random.uniform(-RW / 2, RW / 2), RD / 2 - 0.06, random.uniform(0.2, RH)))
    return Vector((random.uniform(-RW / 2, RW / 2), random.uniform(-0.5, RD / 2), 0.02))


anchors = []
if shot == "hit3": anchors = chair(0.0, 0.6, 0.25)
if shot == "1-01":
    for (cx, cy, r) in [(-0.45, 0.2, 0.3), (0.45, 1.0, -0.2), (1.3, 0.1, 0.5), (2.05, 1.0, 0.1)]:
        anchors += chair(cx, cy, r)

# ---------------------------------------------------------------- threads (one curve object, many splines)
cu = bpy.data.curves.new("threads", "CURVE"); cu.dimensions = "3D"
cu.bevel_depth = 0.0016; cu.bevel_resolution = 2


def thread(a, b, sag=0.02):
    sp = cu.splines.new("POLY"); n = 8
    sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1)
        p = a.lerp(b, t); p.z -= sag * 4 * t * (1 - t) * (a - b).length
        sp.points[i].co = (p.x, p.y, p.z, 1)


if shot == "hit1":
    cu.bevel_depth = 0.0022
    thread(Vector((-RW / 2, -2.2, 2.3)), Vector((RW / 2, -1.9, 0.9)), sag=0.003)
elif shot == "hit2":
    cu.bevel_depth = 0.0022
    for _ in range(110):
        thread(wall_point(), wall_point(), sag=0.01)
else:
    n_anchor = 1800 if shot == "hit3" else 1900
    for _ in range(n_anchor):
        thread(random.choice(anchors), wall_point(), sag=0.008)
    for _ in range(500 if shot == "hit3" else 600):
        thread(wall_point(), wall_point(), sag=0.01)
th = bpy.data.objects.new("threads", cu); scn.collection.objects.link(th)
tm, tnt, tb = principled("redwool", (0.5, 0.0, 0.035), rough=0.75)
tb.inputs["Sheen Weight"].default_value = 0.4; tb.inputs["Sheen Tint"].default_value = (1.0, 0.0, 0.1, 1)
th.data.materials.append(tm)

if shot == "hit1":
    camera(scn, (-0.3, -2.9, 1.5), (0.3, 1.0, 1.6), lens=40, fstop=2.0, focus=0.85)
elif shot == "hit2":
    camera(scn, (0.0, -3.3, 1.5), (0.4, 1.5, 1.6), lens=30, fstop=4.0, focus=3.5)
elif shot == "hit3":
    camera(scn, (-0.6, -3.3, 1.35), (0.3, 1.5, 0.9), lens=30, fstop=4.0, focus=4.0)
else:
    camera(scn, (-2.3, -3.6, 1.35), (-0.55, 1.5, 0.9), lens=30, fstop=5.6, focus=4.6)

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
scn.cycles.volume_step_rate = 2.0
render(scn, A.out)
