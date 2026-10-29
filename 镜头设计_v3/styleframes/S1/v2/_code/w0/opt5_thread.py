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

# ---------------------------------------------------------------- chairs: an old bentwood chair (the Thonet No. 14 type), modelled from round bent rods
# bone paint over wood, worn: paint thins where hands and feet rubbed it, grime sits in the joints (AO)
chairm, cnt, cb = principled("chair", BONE, rough=0.6)
nzw = cnt.nodes.new("ShaderNodeTexNoise"); nzw.inputs["Scale"].default_value = 38.0; nzw.inputs["Detail"].default_value = 8
ao = cnt.nodes.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.04
wear = cnt.nodes.new("ShaderNodeMapRange"); wear.inputs["From Min"].default_value = 0.64; wear.inputs["From Max"].default_value = 0.76
cnt.links.new(nzw.outputs["Fac"], wear.inputs["Value"])
c1 = cnt.nodes.new("ShaderNodeMix"); c1.data_type = "RGBA"
c1.inputs["A"].default_value = (*BONE, 1); c1.inputs["B"].default_value = (0.05, 0.045, 0.042, 1)   # worn through to dark old wood
cnt.links.new(wear.outputs[0], c1.inputs["Factor"])
c2 = cnt.nodes.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MULTIPLY"
cnt.links.new(c1.outputs["Result"], c2.inputs["A"]); cnt.links.new(ao.outputs["AO"], c2.inputs["B"])
c2.inputs["Factor"].default_value = 0.7
cnt.links.new(c2.outputs["Result"], cb.inputs["Base Color"])
bmp = cnt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.15
cnt.links.new(nzw.outputs["Fac"], bmp.inputs["Height"]); cnt.links.new(bmp.outputs["Normal"], cb.inputs["Normal"])


def crom(pts, n_per=10):
    """Catmull-Rom through control points -> dense list (smooth bends for the bent-wood rods)."""
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n_per):
            t = k / n_per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def chair(cx, cy, rot=0.0):
    c, s_ = math.cos(rot), math.sin(rot)
    def W(p): return Vector((cx + c * p.x - s_ * p.y, cy + s_ * p.x + c * p.y, p.z))
    cu_ = bpy.data.curves.new("chairrods", "CURVE"); cu_.dimensions = "3D"; cu_.bevel_depth = 0.01; cu_.bevel_resolution = 4
    cu_.use_fill_caps = True
    pts_all = []
    def rod(pts, r0, r1=None, cyclic=False):
        r1 = r0 if r1 is None else r1
        sp = cu_.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = cyclic
        for i, p in enumerate(pts):
            w = W(p); sp.points[i].co = (w.x, w.y, w.z, 1)
            sp.points[i].radius = (r0 + (r1 - r0) * i / max(1, len(pts) - 1)) / 0.01
            pts_all.append(w)
    V = Vector
    # rear legs + outer back loop: one continuous bent piece, foot to foot
    half = [V((-0.175, 0.27, 0.0)), V((-0.168, 0.2, 0.3)), V((-0.165, 0.17, 0.45)), V((-0.158, 0.2, 0.66)), V((-0.12, 0.235, 0.84)), V((-0.05, 0.25, 0.91))]
    mirror = [V((-p.x, p.y, p.z)) for p in reversed(half)]
    rod(crom(half + [V((0.0, 0.252, 0.92))] + mirror, 8), 0.0125)
    # inner back loop
    il = [V((-0.075, 0.185, 0.47)), V((-0.085, 0.205, 0.6)), V((-0.06, 0.225, 0.7)), V((0.0, 0.232, 0.725))]
    rod(crom(il + [V((-p.x, p.y, p.z)) for p in reversed(il[:-1])], 8), 0.0085)
    # front legs: tapered, splayed
    for sx in (-1, 1):
        rod([V((sx * 0.145, -0.115, 0.45)), V((sx * 0.162, -0.142, 0.22)), V((sx * 0.18, -0.17, 0.0))], 0.0165, 0.012)
    # leg ring at knee height
    ring = [V((0.165 * math.cos(t), 0.035 + 0.185 * math.sin(t), 0.19)) for t in [2 * math.pi * k / 48 for k in range(48)]]
    rod(ring, 0.0085, cyclic=True)
    # seat rim (bent ring under the seat edge)
    rim = [V((0.2 * math.cos(t), 0.2 * math.sin(t), 0.445)) for t in [2 * math.pi * k / 64 for k in range(64)]]
    rod(rim, 0.013, cyclic=True)
    ob = bpy.data.objects.new("chair", cu_); scn.collection.objects.link(ob); ob.data.materials.append(chairm)
    # round seat (a cane seat, read as a slightly dished disc)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.198, depth=0.018, vertices=64, location=W(V((0, 0, 0.455))))
    st = bpy.context.active_object; st.data.materials.append(chairm)
    bv = st.modifiers.new("b", "BEVEL"); bv.width = 0.006; bv.segments = 3
    for p in st.data.polygons: p.use_smooth = True
    # thread anchors: anywhere on the rods, more on the back loop and seat rim
    return random.sample(pts_all, min(60, len(pts_all)))


def wall_point():
    if shot == "1-01":  # keep the web behind and above the chairs so all four stay readable
        k = random.random()
        if k < 0.3: return Vector((RW / 2 - 0.06, random.uniform(-0.5, RD / 2), random.uniform(0.6, RH)))
        if k < 0.65: return Vector((random.uniform(-0.6, RW / 2), random.uniform(-0.2, RD / 2), RH - 0.06))
        return Vector((random.uniform(-0.6, RW / 2), RD / 2 - 0.06, random.uniform(0.4, RH)))
    k = random.random()
    if k < 0.3: return Vector((random.choice((-RW / 2 + 0.06, RW / 2 - 0.06)), random.uniform(-0.8, RD / 2), random.uniform(0.2, RH)))
    if k < 0.65: return Vector((random.uniform(-RW / 2, RW / 2), random.uniform(-0.8, RD / 2), RH - 0.06))
    if k < 0.85: return Vector((random.uniform(-RW / 2, RW / 2), RD / 2 - 0.06, random.uniform(0.2, RH)))
    return Vector((random.uniform(-RW / 2, RW / 2), random.uniform(-0.5, RD / 2), 0.02))


anchors = []
if shot == "hit3": anchors = chair(0.0, 0.6, 0.25)
if shot == "1-01":
    # four chairs, all in the right half (A's card covers the left), staggered in depth so none hides another
    for (cx, cy, r) in [(0.71, 0.0, 0.35), (1.44, 1.2, -0.25), (1.71, 0.2, 0.6), (2.75, 1.6, 0.05)]:
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
    n_anchor = 1800 if shot == "hit3" else 1100
    for _ in range(n_anchor):
        thread(random.choice(anchors), wall_point(), sag=0.008)
    for _ in range(500 if shot == "hit3" else 250):
        thread(wall_point(), wall_point(), sag=0.01)
    if shot == "1-01":  # a canopy: the web hangs above the four chairs, clear of the seats
        for _ in range(450):
            a_, b_ = wall_point(), wall_point()
            if min(a_.z, b_.z) > 1.5: thread(a_, b_, sag=0.012)
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
    camera(scn, (0.2, -3.4, 1.3), (0.2, 1.5, 0.75), lens=26, fstop=5.6, focus=4.0)

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
scn.cycles.volume_step_rate = 2.0
render(scn, A.out)
