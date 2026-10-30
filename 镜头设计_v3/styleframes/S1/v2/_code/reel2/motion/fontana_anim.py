"""reel2/motion: the Fontana canvas actually gets cut (W0 + 1-01 background), one Blender process renders the whole frame plan.
Built from reel/blender/fontana_reel.py (blood-red copy): same canvas material, gauze, back lights, haze, key/fill, Standard view.
Changes: the canvas is wider (the 1-01 camera sits further left and further back), every cut has an opening state
(s = how far the slash has run along its length, w = how wide it has opened, flash = extra light while it tears),
and the camera can move. The mesh is rebuilt per frame from the numpy grid (foreach_set, ~1 s).

  blender -b --factory-startup -t 4 -P fontana_anim.py -- --seq w0|101|all --out DIR [--only 0,5,40] [--samples 384]
Frame plan (unique frames only; Remotion maps every timeline frame to one of these):  plan() below, also written to DIR/plan.json.
"""
import os, sys, json
sys.path.insert(0, "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/w0")
from bl_common import *
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--seq", default="all"); ap.add_argument("--out", required=True)
ap.add_argument("--only", default=""); ap.add_argument("--samples", type=int, default=384); ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--planonly", action="store_true")
A = ap.parse_args(argv)

PX = 400.0
X0C, X1C = -4.7, 3.1          # canvas extent in x (m): wide enough for the 1-01 framing
CH = 3.7
XC, CW = (X0C + X1C) / 2, X1C - X0C

# cuts in canvas px (x = X*400 + 960, y = 540 - Z*400): x, y0, y1, lean, bow, open width
C1 = (960, 170, 900, 0.10, 18, 40)
C2 = (700, 260, 860, -0.07, -12, 30)
C3 = (1240, 230, 820, 0.16, 10, 34)
C4 = (1456, 345, 760, 0.05, -5, 24)   # the fourth cut, on "four people": sits right of C3 in the 1-01 framing
CUTS = [C1, C2, C3, C4]

# cameras: hit = v1 W0 camera (oblique), c101 = head-on, pulled back so the three W0 cuts land where v1's 1-01 had its cuts
CAM_HIT = dict(pos=(-1.6, -4.95, -0.35), tgt=(0.05, 0, 0.0), lens=48.0, focus=5.4)
CAM_101 = dict(pos=(-1.32, -6.34, 0.0), tgt=(-1.32, 0, 0.0), lens=39.0, focus=6.34)

# opening curves (frames after the hit): slash length s, width w (overshoot), light flash
S_CURVE = [0.45, 0.85, 1.0]
W_CURVE = [0.25, 0.65, 1.0, 1.14, 1.09, 1.04, 1.015, 1.0]
F_CURVE = [2.0, 2.4, 2.0, 1.55, 1.3, 1.15, 1.06, 1.0]
OPEN_N = len(W_CURVE)


def cut_state(k):
    """state of a cut k frames after its hit (k<0: closed)."""
    if k < 0: return (0.0, 0.0, 0.0)
    s = S_CURVE[k] if k < len(S_CURVE) else 1.0
    w = W_CURVE[k] if k < OPEN_N else 1.0
    fl = F_CURVE[k] if k < OPEN_N else 1.0
    return (s, w, fl)


def ease(x):
    x = min(1, max(0, x)); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def lerp(a, b, t): return tuple(p + (q - p) * t for p, q in zip(a, b))


def plan():
    """unique frames. W0: hits at 0, 20, 40 (60 frames). 1-01 (180 frames): truck 0..TR, fourth cut at H4."""
    P = []
    hits = [0, 20, 40]
    order = [0, 1, 2]           # C1 first (centre), then C2 (left), then C3 (right) -- as v1 hit1/hit2/hit3
    for i, h in enumerate(hits):
        for k in range(OPEN_N):
            cs = [cut_state(h + k - hits[j]) for j in range(3)] + [(0, 0, 0)]
            P.append(dict(name="w0_%02d" % (h + k), seq="w0", t=h + k, cam=CAM_HIT, cuts=cs))
    TR0, TR1, H4 = 0, 40, 72
    full3 = [cut_state(99)] * 3
    for t in range(TR0, TR1 + 1):
        u = ease((t - TR0) / (TR1 - TR0))
        cam = dict(pos=lerp(CAM_HIT["pos"], CAM_101["pos"], u), tgt=lerp(CAM_HIT["tgt"], CAM_101["tgt"], u),
                   lens=CAM_HIT["lens"] + (CAM_101["lens"] - CAM_HIT["lens"]) * u, focus=CAM_HIT["focus"] + (CAM_101["focus"] - CAM_HIT["focus"]) * u)
        P.append(dict(name="c101_%03d" % t, seq="101", t=t, cam=cam, cuts=full3 + [(0, 0, 0)]))
    for k in range(OPEN_N):
        P.append(dict(name="c101_%03d" % (H4 + k), seq="101", t=H4 + k, cam=CAM_101, cuts=full3 + [cut_state(k)]))
    return P


PLAN = [p for p in plan() if A.seq == "all" or p["seq"] == A.seq]
if A.only: PLAN = [p for p in PLAN if p["name"] in A.only.split(",") or str(p["t"]) in A.only.split(",")]
os.makedirs(A.out, exist_ok=True)
json.dump([{k: v for k, v in p.items() if k in ("name", "seq", "t")} for p in plan()], open(os.path.join(A.out, "plan.json"), "w"))
if A.planonly: sys.exit(0)

scn = reset()
world(scn, (0, 0, 0))

# ---------------------------------------------------------------- canvas grid (same density as v1: 1400 verts over 6 m)
NX = int(round(CW / 6.0 * 1400)); NZ = int(round(CH / 3.4 * 800))
xs = np.linspace(X0C, X1C, NX); zs = np.linspace(-CH / 2, CH / 2, NZ)
X, Z = np.meshgrid(xs, zs)
px = X * PX + 960; py = 540 - Z * PX
SP = (xs[1] - xs[0]) * PX
IDX = np.arange(NX * NZ).reshape(NZ, NX)
QALL = np.stack([IDX[:-1, :-1], IDX[:-1, 1:], IDX[1:, 1:], IDX[1:, :-1]], -1).reshape(-1, 4)
SAG = 0.004 * np.sin(np.pi * ((X - X0C) / CW)) * np.sin(np.pi * (Z / CH + 0.5))


def geometry(states):
    Xsnap = np.zeros(X.shape); Ymove = np.zeros(X.shape); inside = np.zeros(X.shape, bool)
    for (cx, y0, y1, lean, bow, wid), (s, w, fl) in zip(CUTS, states):
        if s <= 0 or w <= 0: continue
        L = (y1 - y0) * s
        tf = np.clip((py - y0) / (y1 - y0), 0, 1)              # position along the full cut: the slash runs along its final path
        t = (py - y0) / L; tc = np.clip(t, 0, 1)
        xc = cx + lean * (py - y0) + bow * np.sin(np.pi * tf)
        prof = np.abs(np.sin(np.pi * tc)) ** 0.7
        half = wid * 0.5 * prof * w
        dx = px - xc
        d = np.abs(dx) - half
        tipy = np.where(t <= 0, y0, y0 + L)
        tipx = cx + lean * (tipy - y0) + bow * np.sin(np.pi * np.clip((tipy - y0) / (y1 - y0), 0, 1))
        dt = np.sqrt((px - tipx) ** 2 + (py - tipy) ** 2)
        within = (t > 0) & (t < 1)
        d = np.where(within, d, dt + 2)
        inside |= within & (np.abs(dx) < half)
        near = within & (d > 0) & (d < 1.5 * SP)
        Xsnap = np.where(near, -np.sign(dx) * d / PX, Xsnap)
        lipr = (9 + 16 * prof) * (0.6 + 0.4 * min(w, 1.0))
        curl = min(w, 1.25)                                   # the overshoot rolls the lips a little further back
        fall = np.exp(-np.clip(d, 0, None) / lipr) * (0.25 + 0.75 * prof)
        Ymove = np.maximum(Ymove, fall * (0.03 + 0.05 * prof) * curl)
        Ymove -= np.exp(-((np.clip(d, 0, None) - lipr * 2.2) / (lipr * 1.2)) ** 2) * 0.006 * prof * min(w, 1.0)
    Ymove += SAG
    verts = np.stack([X + Xsnap, Ymove, Z], -1).reshape(-1, 3)
    keep = ~(inside[:-1, :-1] | inside[:-1, 1:] | inside[1:, 1:] | inside[1:, :-1]).reshape(-1)
    return verts, QALL[keep]


me = bpy.data.meshes.new("canvas")
canvas = bpy.data.objects.new("canvas", me); scn.collection.objects.link(canvas)


def set_mesh(verts, q):
    me.clear_geometry()
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    nl = q.size
    me.loops.add(nl); me.loops.foreach_set("vertex_index", q.astype(np.int32).ravel())
    me.polygons.add(len(q)); me.polygons.foreach_set("loop_start", (np.arange(len(q)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    uv = me.uv_layers.new(name="uv") if not me.uv_layers else me.uv_layers[0]
    lv = q.ravel()
    uvs = np.stack([(verts[lv, 0] - X0C) / CW * (CW / 6.0), (verts[lv, 2] + CH / 2) / CH * (CH / 3.4)], -1)  # same texel scale as v1
    uv.data.foreach_set("uv", uvs.astype(np.float32).ravel())
    me.shade_smooth()


set_mesh(*geometry([(0, 0, 0)] * 4))
sol = canvas.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.004; sol.offset = 1.0

# canvas material (as v1)
m, nt, b = principled("ikb", (0.0, 0.035, 0.42), rough=0.92)
b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Tint"].default_value = (0.0, 0.25, 1.0, 1)
b.inputs["Sheen Roughness"].default_value = 0.4
tcn = nt.nodes.new("ShaderNodeTexCoord")
wv1 = nt.nodes.new("ShaderNodeTexWave"); wv1.wave_type = "BANDS"; wv1.bands_direction = "X"; wv1.inputs["Scale"].default_value = 900
wv2 = nt.nodes.new("ShaderNodeTexWave"); wv2.wave_type = "BANDS"; wv2.bands_direction = "Y"; wv2.inputs["Scale"].default_value = 520
for w_ in (wv1, wv2):
    w_.inputs["Distortion"].default_value = 2.0; w_.inputs["Detail"].default_value = 1.0
    nt.links.new(tcn.outputs["UV"], w_.inputs["Vector"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(wv1.outputs["Fac"], mul.inputs[0]); nt.links.new(wv2.outputs["Fac"], mul.inputs[1])
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 10
add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
nt.links.new(mul.outputs[0], add.inputs[0]); nt.links.new(nz.outputs["Fac"], add.inputs[1])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12; bump.inputs["Distance"].default_value = 0.0006
nt.links.new(add.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 2.5; nz2.inputs["Detail"].default_value = 6
cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.0, 0.02, 0.42, 1); cr.color_ramp.elements[1].color = (0.0, 0.045, 0.62, 1)
nt.links.new(nz2.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
canvas.data.materials.append(m)

# gauze + per-cut back lights + haze (as v1, sized to the wider canvas)
bpy.ops.mesh.primitive_plane_add(size=1, location=(XC, 0.32, 0), rotation=(math.radians(90), 0, 0))
g = bpy.context.active_object; g.scale = (CW * 1.4, CH * 1.4, 1)
gm, gnt, gb = principled("gauze", tuple(0.35 * c / max(VERM) for c in VERM), rough=0.8)
g.data.materials.append(gm)
LIGHTS = []
for (cx, y0, y1, lean, bow, wid) in CUTS:
    ym = (y0 + y1) / 2; xm = cx + lean * (ym - y0) + bow
    L = (y1 - y0) / PX
    ld = bpy.data.lights.new("rc", "AREA"); ld.shape = "ELLIPSE"; ld.size = 0.06; ld.size_y = L * 0.8
    ld.energy = 0; ld.color = tuple(c / max(VERM) for c in VERM)
    o = bpy.data.objects.new("rc", ld); scn.collection.objects.link(o)
    o.location = ((xm - 960) / PX, 0.16, (540 - ym) / PX); o.rotation_euler = (math.radians(90), math.atan(lean), 0)
    o.visible_camera = False
    LIGHTS.append((ld, o, 1.6 * L, cx, y0, y1, lean, bow))
bpy.ops.mesh.primitive_cube_add(size=1, location=(XC, 0.36, 0))
hz = bpy.context.active_object; hz.scale = (CW * 1.3, 0.66, CH * 1.3)
hz.data.materials.append(volume("backhaze", (1, 1, 1), 0.35, aniso=0.5))

area(scn, "key", 420, 0.6, (-3.4, -1.2, 2.6), (0.4, 0, -0.3), (0.9, 0.95, 1.0), size_y=3.0)
area(scn, "fill", 30, 4, (1.5, -5, 0.5), (0, 0, 0), (0.6, 0.75, 1.0))

cam = camera(scn, CAM_HIT["pos"], CAM_HIT["tgt"], lens=CAM_HIT["lens"], fstop=5.6, focus=CAM_HIT["focus"])
gpu(scn, A.samples, A.pct, view="Standard", look="None")


def set_cam(c):
    cam.location = Vector(c["pos"])
    cam.rotation_euler = (Vector(c["tgt"]) - Vector(c["pos"])).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = c["lens"]; cam.data.dof.focus_distance = c["focus"]


for p in PLAN:
    set_mesh(*geometry(p["cuts"]))
    for (ld, o, e0, cx, y0, y1, lean, bow), (s, w, fl) in zip(LIGHTS, p["cuts"]):
        ld.energy = e0 * min(w, 1.0) * fl * min(1.0, s * 1.2)
        # while the slash is still running the light sits on the part that is open
        ye = y0 + (y1 - y0) * max(s, 0.05); ym = (y0 + ye) / 2
        o.location = ((cx + lean * (ym - y0) + bow * math.sin(math.pi * (ym - y0) / (y1 - y0)) - 960) / PX, 0.16, (540 - ym) / PX)
        ld.size_y = max(0.02, (ye - y0) / PX * 0.8)
    set_cam(p["cam"])
    render(scn, os.path.join(A.out, p["name"] + ".png"))
print("ALLDONE", len(PLAN))
