"""Option 1 · fontana-cut (Blender): an ultramarine canvas (Klein's blue) is slashed on each hit (Lucio Fontana, Concetto spaziale);
red light lives behind it. Real geometry: the lips curl back into the cut, a raking light catches them.
--shot hit1|hit2|hit3|1-01|hit3_alt
hit3_alt: same three cuts, but deeper lips, one hard grazing light and almost no fill, so the canvas reads as a physical object in deep shadow.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *
import numpy as np

A = args()
ALT = A.shot == "hit3_alt"
if ALT: A.shot = "hit3"
scn = reset()
world(scn, (0, 0, 0))

PX = 400.0  # canvas pixels per metre (canvas = 4.8 x 2.7 m, matches a 1920x1080 frame head-on)
CW, CH = 6.0, 3.4

# cuts in frame pixels: x, y0, y1, lean (dx/dy), bow px, max open width px
C1 = (960, 170, 900, 0.10, 18, 40)
C2 = (700, 260, 860, -0.07, -12, 30)
C3 = (1240, 230, 820, 0.16, 10, 34)
CUTS = {"hit1": [C1], "hit2": [C1, C2], "hit3": [C1, C2, C3],
        "1-01": [(1180, 200, 880, 0.08, 14, 34), (1400, 280, 840, -0.05, -10, 28), (1620, 240, 860, 0.12, 8, 32),
                 (1800, 380, 720, 0.05, -5, 18)]}[A.shot]

# ---------------------------------------------------------------- canvas mesh (numpy grid -> bmesh)
NX, NZ = 1400, 800
xs = np.linspace(-CW / 2, CW / 2, NX); zs = np.linspace(-CH / 2, CH / 2, NZ)
X, Z = np.meshgrid(xs, zs)
px = X * PX + 960; py = 540 - Z * PX
SP = CW / (NX - 1) * PX  # grid spacing in frame px
Xsnap = np.zeros(X.shape)
Dmin = np.full(X.shape, 1e9); Ymove = np.zeros(X.shape); Xmove = np.zeros(X.shape); inside = np.zeros(X.shape, bool)
for (cx, y0, y1, lean, bow, wid) in CUTS:
    t = (py - y0) / (y1 - y0); tc = np.clip(t, 0, 1)
    xc = cx + lean * (py - y0) + bow * np.sin(np.pi * tc)
    prof = np.abs(np.sin(np.pi * tc)) ** 0.7
    half = wid * 0.5 * prof * (1.35 if ALT else 1.0)
    dx = px - xc
    d = np.abs(dx) - half
    tipy = np.where(t <= 0, y0, y1); tipx = cx + lean * (tipy - y0)
    dt = np.sqrt((px - tipx) ** 2 + (py - tipy) ** 2)
    within = (t > 0) & (t < 1)
    d = np.where(within, d, dt + 2)
    inside |= within & (np.abs(dx) < half)
    # snap the first ring of outside vertices onto the true cut contour (no staircase edges)
    # (hit3_alt: the raking light shows the stair where a leaning cut steps a column between rows, so the second ring snaps too)
    near = within & (d > 0) & (d < (2.05 if ALT else 1.5) * SP)
    Xsnap = np.where(near, -np.sign(dx) * d / PX, Xsnap)
    # lips: the cloth is pushed back (into the canvas) and slightly rolled, strongest mid-cut
    lipr = 9 + 16 * prof
    fall = np.exp(-np.clip(d, 0, None) / lipr) * (0.25 + 0.75 * prof)
    Ymove = np.maximum(Ymove, fall * (0.03 + 0.05 * prof) * (1.5 if ALT else 1.0))
    # a little bunching just outside the lip (the canvas was stretched and gave way)
    Ymove -= np.exp(-((np.clip(d, 0, None) - lipr * 2.2) / (lipr * 1.2)) ** 2) * 0.006 * prof
    Dmin = np.minimum(Dmin, d)
# fabric sag: very slight overall
Ymove += 0.004 * np.sin(np.pi * (X / CW + 0.5)) * np.sin(np.pi * (Z / CH + 0.5))

me = bpy.data.meshes.new("canvas")
verts = np.stack([X + Xsnap, Ymove, Z], -1).reshape(-1, 3)
idx = np.arange(NX * NZ).reshape(NZ, NX)
q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
keep = ~(inside[:-1, :-1] | inside[:-1, 1:] | inside[1:, 1:] | inside[1:, :-1]).reshape(-1)
q = q[keep]
me.from_pydata(verts.tolist(), [], q.tolist())
me.update()
uv = me.uv_layers.new(name="uv")
loops_v = np.zeros(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", loops_v)
uvs = np.stack([(verts[loops_v, 0] + CW / 2) / CW, (verts[loops_v, 2] + CH / 2) / CH], -1)
uv.data.foreach_set("uv", uvs.reshape(-1))
for p in me.polygons: p.use_smooth = True
canvas = bpy.data.objects.new("canvas", me); scn.collection.objects.link(canvas)
sol = canvas.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.004; sol.offset = 1.0

# canvas material: pigment-saturated ultramarine, dry and velvety, linen weave in the bump
m, nt, b = principled("ikb", (0.0, 0.035, 0.42), rough=0.92)
b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Tint"].default_value = (0.0, 0.25, 1.0, 1)
b.inputs["Sheen Roughness"].default_value = 0.4
tc = nt.nodes.new("ShaderNodeTexCoord")
wv1 = nt.nodes.new("ShaderNodeTexWave"); wv1.wave_type = "BANDS"; wv1.bands_direction = "X"; wv1.inputs["Scale"].default_value = 900
wv2 = nt.nodes.new("ShaderNodeTexWave"); wv2.wave_type = "BANDS"; wv2.bands_direction = "Y"; wv2.inputs["Scale"].default_value = 520
for w_ in (wv1, wv2):
    w_.inputs["Distortion"].default_value = 2.0; w_.inputs["Detail"].default_value = 1.0
    nt.links.new(tc.outputs["UV"], w_.inputs["Vector"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(wv1.outputs["Fac"], mul.inputs[0]); nt.links.new(wv2.outputs["Fac"], mul.inputs[1])
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 10
add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
nt.links.new(mul.outputs[0], add.inputs[0]); nt.links.new(nz.outputs["Fac"], add.inputs[1])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12; bump.inputs["Distance"].default_value = 0.0006
nt.links.new(add.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
# pigment load varies a little
nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 2.5; nz2.inputs["Detail"].default_value = 6
cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.0, 0.02, 0.42, 1); cr.color_ramp.elements[1].color = (0.0, 0.045, 0.62, 1)
nt.links.new(nz2.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
canvas.data.materials.append(m)

# ---------------------------------------------------------------- behind the canvas: black gauze (as Fontana backed his cuts), lit red from inside
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.32, 0), rotation=(math.radians(90), 0, 0))
g = bpy.context.active_object; g.scale = (CW * 1.4, CH * 1.4, 1)
gm, gnt, gb = principled("gauze", (0.35, 0.02, 0.02), rough=0.8)
g.data.materials.append(gm)
for (cx, y0, y1, lean, bow, wid) in CUTS:
    ym = (y0 + y1) / 2
    xm = cx + lean * (ym - y0) + bow
    X0 = (xm - 960) / PX; Z0 = (540 - ym) / PX
    L = (y1 - y0) / PX
    # a strip light behind each cut: a hot core seen through the slit, falling off toward its ends
    ld = bpy.data.lights.new("rc", "AREA"); ld.shape = "ELLIPSE"; ld.size = 0.06; ld.size_y = L * 0.8
    ld.energy = 1.6 * L * (0.4 if ALT else 1.0); ld.color = (1.0, 0.006, 0.003)
    o = bpy.data.objects.new("rc", ld); scn.collection.objects.link(o)
    o.location = (X0, 0.16, Z0); o.rotation_euler = (math.radians(90), math.atan(lean), 0)  # faces -y (toward canvas)
    o.visible_camera = False

# haze in the space behind the canvas: the light has depth when seen through a cut
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.36, 0))
hz = bpy.context.active_object; hz.scale = (CW * 1.3, 0.66, CH * 1.3)
hz.data.materials.append(volume("backhaze", (1, 1, 1), 0.35, aniso=0.5))

# ---------------------------------------------------------------- front: one raking key from upper left, very low fill
if ALT:
    # one hard light from the far right, almost parallel to the canvas: every lip throws a long shadow, the field falls off into black
    # a low sun from the upper left, ~9 deg off the canvas plane: hard, parallel, long shadows off every lip
    sd = bpy.data.lights.new("rake", "SUN"); sd.energy = 3.5; sd.angle = math.radians(0.8); sd.color = (0.92, 0.95, 1.0)
    so = bpy.data.objects.new("rake", sd); scn.collection.objects.link(so)
    so.rotation_euler = Vector((-1.0, -0.16, 0.42)).to_track_quat("Z", "Y").to_euler()   # lamp +Z points back at the source (upper-left-front); light travels along -Z
    b.inputs["Sheen Weight"].default_value = 0.15
    area(scn, "fill", 4, 4, (1.5, -5, 0.5), (0, 0, 0), (0.6, 0.75, 1.0))
else:
    area(scn, "key", 420, 0.6, (-3.4, -1.2, 2.6), (0.4, 0, -0.3), (0.9, 0.95, 1.0), size_y=3.0)
    area(scn, "fill", 30, 4, (1.5, -5, 0.5), (0, 0, 0), (0.6, 0.75, 1.0))

cam_y = -5.2
if A.shot == "1-01":
    camera(scn, (0.0, cam_y, 0.0), (0.0, 0, 0.0), lens=39, fstop=5.6, focus=5.2)  # 4.8 m wide = frame px mapping
elif ALT:
    camera(scn, (-2.2, cam_y + 0.9, -0.6), (0.15, 0, 0.05), lens=55, fstop=4.0, focus=4.9)
else:
    camera(scn, (-1.6, cam_y + 0.25, -0.35), (0.05, 0, 0.0), lens=48, fstop=5.6, focus=5.4)

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
render(scn, A.out)
