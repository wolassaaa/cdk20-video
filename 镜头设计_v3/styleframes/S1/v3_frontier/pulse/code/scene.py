"""PULSE, 1,412 lights. Blender 5.1 Cycles scene + render.

1,412 small hanging globe bulbs (one per person who died of liver cancer in Hong Kong in 2022, HKCaR)
fill the volume of a BodyParts3D liver at installation scale (x30, ~6.3 m wide), each on its own black
cable up into the dark. Every bulb beats at its own deterministic heart rate (per-bulb brightness is a
float texture: column = bulb index, row = frame, R = white drive, G = red ember).
The camera starts inside the cloud, close on a few lights; four of them stop (the beat slows, the next
beat never comes, the filament cools through blood red to dark). Then one dolly back out through the
cloud until the whole liver is seen.

blender -b --factory-startup -t 3 -P scene.py -- --out FRAMES/f_ [--stills 0,120,299 | --frames 0-299]
        [--samples 1024] [--thresh 0.01] [--pct 100] [--plan_only 1]
Outputs EXR (linear, half float); post.py does glow + Standard sRGB + PNG.
"""
import bpy, bmesh, sys, math, argparse, time, json, os, itertools
import numpy as np
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="")
ap.add_argument("--frames", default="")
ap.add_argument("--stills", default="")
ap.add_argument("--samples", type=int, default=1024)
ap.add_argument("--thresh", type=float, default=0.01)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--plan_only", type=int, default=0)
ap.add_argument("--floor", type=int, default=1)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--extra", type=int, default=0, help="1: the ten-bulb still for 1-04 instead of the liver")
A = ap.parse_args(argv)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
t0 = time.time()
FPS, NF = 30, 300
W_, H_ = 1920, 1080

# ------------------------------------------------------------------ palette (linear)
def srgb2lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
BONE = srgb2lin("#EDEBE4")      # (0.846, 0.831, 0.776)
RED = srgb2lin("#E8190F")       # (0.807, 0.0097, 0.0048)

# ------------------------------------------------------------------ bulbs
d = np.load(os.path.join(DATA, "points.npz"))
P = d["P"].copy()
N = len(P)
assert N == 1412, N
CEIL = 14.0
RG = 0.024          # globe radius (a G48 globe)
CAP_H = 0.026       # E14 cap height above the globe
CEN = np.array([0.0, 0.0, (P[:, 2].min() + P[:, 2].max()) / 2])

_t = np.load(os.path.join(DATA, "threads.npz"))
THR, THR_PAR, THR_RAD = _t["pts"], _t["par"], _t["rad"]

_d = np.linalg.norm(THR[:, None] - P[None], axis=2).min(1)
_keep = _d < 0.42
_map = -np.ones(len(THR), int); _map[_keep] = np.arange(_keep.sum())
THR_PAR = np.array([_map[p] if p >= 0 and _keep[p] else -1 for p in THR_PAR[_keep]])
THR, THR_RAD = THR[_keep], THR_RAD[_keep]
# arrival: path length from the root of each piece, normalised, so red can run out along the branches
_arr = np.full(len(THR), -1.0)
def _arrival(i):
    chain = []
    while _arr[i] < 0:
        if THR_PAR[i] < 0: _arr[i] = 0.0; break
        chain.append(i); i = THR_PAR[i]
    for c in reversed(chain):
        _arr[c] = _arr[THR_PAR[c]] + float(np.linalg.norm(THR[c] - THR[THR_PAR[c]]))
for _i in range(len(THR)): _arrival(_i)
THR_ARR = _arr / _arr.max()
print("threads kept %d / %d, longest run %.1f m" % (_keep.sum(), len(_keep), _arr.max()))

LENS = 40.0
TX = 18.0 / LENS                 # tan(half hfov)
TY = TX * H_ / W_


# ------------------------------------------------------------------ camera plan (numpy only)
def basis(fwd):
    f = fwd / np.linalg.norm(fwd)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return f, r, u


def plan():
    """The liver hangs above head height (lowest bulb 2.4 m), so the camera can stand below its underside with no
    cable in its way (a cable only runs UP from its bulb). Start: tucked under the cloud, tilted up, close on a few
    lights. End: 13.5 m back. Picks the start that gives 4-7 near lights, well spread on screen."""
    az = math.radians(14.0)                       # camera swung toward the patient's left: the classic liver wedge
    dh = np.array([math.sin(az), -math.cos(az), 0.0])
    rh = np.array([math.cos(az), math.sin(az), 0.0])
    tgt = CEN + rh * 0.45 + np.array([0, 0, -0.30])
    D_END, Z_END = 12.6, 3.0
    E = tgt + dh * D_END; E[2] = Z_END
    best = None
    ntest = 0
    for along, ox, zs, pitch in itertools.product(np.arange(-2.4, 3.01, 0.15), np.arange(-3.0, 3.01, 0.15),
                                                  np.arange(1.7, 4.61, 0.2), (10, 18, 26, 34, 42)):
        S = np.array([CEN[0], CEN[1], zs]) + dh * along + rh * ox
        p = math.radians(pitch)
        f, r, u = basis(-dh * math.cos(p) + np.array([0, 0, math.sin(p)]))
        rel = P - S
        z = rel @ f; x = rel @ r; y = rel @ u
        sx = x / np.maximum(z, 1e-3) / TX; sy = y / np.maximum(z, 1e-3) / TY
        vis = (z > 0.05) & (np.abs(sx) < 1.05) & (np.abs(sy) < 1.05)
        if (vis & (z < 0.55)).any(): continue
        nearall = vis & (z < 1.7)
        if nearall.sum() > 9: continue
        if (vis & (z > 2.0)).sum() < 140: continue
        cand = np.where((z > 0.6) & (z < 1.6) & (np.abs(sx) < 0.72) & (np.abs(sy) < 0.68))[0]
        if not (4 <= len(cand) <= 7): continue
        # nothing right against the lens, even outside the frame
        if np.linalg.norm(rel, axis=1).min() < 0.35: continue
        bestc = None
        for c4 in itertools.combinations(cand, 4):
            pts = np.stack([sx[list(c4)], sy[list(c4)] * TY / TX], 1)
            m = min(np.linalg.norm(pts[i] - pts[j]) for i in range(4) for j in range(i + 1, 4))
            bal = np.linalg.norm(pts.mean(0))
            s_ = m - 0.5 * bal
            if bestc is None or s_ > bestc[0]: bestc = (s_, c4, m)
        if bestc[2] < 0.36: continue
        occl = False
        for i in bestc[1]:
            front = (z < z[i] - 0.05) & (z > 0.05) & (np.hypot((sx - sx[i]) * TX * z[i], (sy - sy[i]) * TY * z[i]) < 0.09)
            if front.any(): occl = True
        if occl: continue
        # path clearance S -> E: bulbs 0.30 m, cables (only above their bulb) 0.14 m
        ts = np.linspace(0, 1, 90)[:, None]
        path = S + (E - S) * ts
        if np.linalg.norm(path[:, None, :] - P[None], axis=2).min() < 0.30: continue
        hz = np.linalg.norm(path[:, None, :2] - P[None, :, :2], axis=2)
        if np.any((path[:, None, 2] > P[None, :, 2] - 0.05) & (hz < 0.14)): continue
        if np.linalg.norm(path[:, None, :] - THR[None, ::4], axis=2).min() < 0.30: continue
        ntest += 1
        score = bestc[0] - 0.12 * abs(len(cand) - 5) - 0.25 * z[list(bestc[1])].mean()
        if best is None or score > best[0]:
            best = (score, dict(S=S.tolist(), E=E.tolist(), f=f.tolist(), r=r.tolist(), u=u.tolist(),
                                dying=[int(i) for i in bestc[1]], near=[int(i) for i in cand], sep=float(bestc[2]),
                                along=float(along), ox=float(ox), zs=float(zs), pitch=float(pitch), tgt=tgt.tolist(),
                                depths=[float(z[i]) for i in bestc[1]]))
    print("valid starts:", ntest)
    return best


plan_path = os.path.join(DATA, "plan.json")
if os.path.exists(plan_path):
    PL = json.load(open(plan_path))
else:
    sc, PL = plan()
    S, f, r, u = map(np.array, (PL["S"], PL["f"], PL["r"], PL["u"]))
    rel = P[PL["dying"]] - S
    sx = (rel @ r) / (rel @ f) / TX
    sy = (rel @ u) / (rel @ f) / TY
    # order of going out: start near the centre of the frame, then move across it
    order = np.argsort(np.hypot(sx, sy * 0.8))
    first = order[0]
    rest = sorted([i for i in range(4) if i != first], key=lambda i: math.atan2(sy[i] - sy[first], sx[i] - sx[first]))
    PL["dying"] = [PL["dying"][first]] + [PL["dying"][i] for i in rest]
    PL["score"] = float(sc)
    json.dump(PL, open(plan_path, "w"), indent=1)
print("plan:", {k: PL[k] for k in ("dying", "near", "sep", "along", "ox", "zs", "pitch", "depths")}, "(%.1fs)" % (time.time() - t0))

# ------------------------------------------------------------------ heartbeats -> texture (N x NF)
T_DIE = [3.10, 4.10, 5.10, 6.10]       # seconds: four lives, one after another
rng = np.random.default_rng(2022)
bpm = np.clip(rng.normal(72, 8, N), 54, 96)
phase0 = rng.random(N)
gain = 0.85 + 0.3 * rng.random(N)      # bulbs are hand-made; a little spread in brightness
SUB = 8                                 # sub-samples per frame (box filter over the frame)
ts = (np.arange(NF * SUB) + 0.5) / (FPS * SUB)
dt = 1.0 / (FPS * SUB)


def beat_shape(tau):
    """drive for time-since-beat-onset tau (s): soft lub, smaller dub."""
    a1, a2 = 0.07, 0.09
    u1 = np.maximum(tau, 0) / a1
    u2 = np.maximum(tau - 0.30, 0) / a2
    return u1 * np.exp(1 - u1) + 0.42 * u2 * np.exp(1 - u2)


REST = 0.42
white = np.zeros((N, NF * SUB))
ember = np.zeros((N, NF * SUB))
tr_r = np.full((N, NF * SUB), 0.97)     # glass transmission, red
tr_g = np.full((N, NF * SUB), 0.97)     # glass transmission, green and blue
death_t = {}
for i in range(N):
    rate = np.full(len(ts), bpm[i] / 60.0)
    dk = PL["dying"].index(i) if i in PL["dying"] else -1
    if dk >= 0:
        # the last beats slow down (rate falls ~35% over the final 2.2 s) and weaken a little
        td_target = T_DIE[dk]
        slow = np.clip((ts - (td_target - 2.2)) / 2.2, 0, 1)
        rate = rate * (1 - 0.35 * slow ** 1.5)
    cum = np.cumsum(rate) * dt
    if dk >= 0:                                        # align so a beat is due exactly at the death time
        cj = cum[np.searchsorted(ts, T_DIE[dk])]
        phase0[i] = np.ceil(cj) - cj
    ph = phase0[i] + cum
    k = np.floor(ph); frac = ph - k
    tau = frac / rate                                  # seconds since this beat's onset
    drive = REST + (1 - REST) * beat_shape(tau)
    if dk >= 0:
        # death = the onset of the first beat after the target time that never comes
        onset = np.where(np.diff(k) > 0)[0] + 1
        j = onset[np.searchsorted(ts[onset], T_DIE[dk])]
        td = ts[j]; death_t[i] = float(td)
        weak = 1 - 0.25 * np.clip((ts - (td - 2.2)) / 2.2, 0, 1)
        drive = drive * weak
        after = ts >= td
        dlev = drive[j - 1]
        x = ts[after] - td
        drive[after] = dlev * np.exp(-x / 0.05)                     # the white goes almost at once
        xe = np.maximum(x - 0.13, 0)
        ember[i, after] = (1 - np.exp(-xe / 0.10)) * np.exp(-xe / 0.60)  # then a dull red that cools away
        sk = np.clip(x / 0.18, 0, 1); dk_ = sk * sk * (3 - 2 * sk)
        sat = np.minimum(1.0, ember[i, after] / 0.25)
        tr_r[i, after] = 0.97 + (0.06 + 0.22 * sat - 0.97) * dk_
        tr_g[i, after] = 0.97 + (0.02 * sat + 0.06 * (1 - sat) ** 2 - 0.97) * dk_
    # filament thermal lag (incandescent softness): first-order low-pass, tau 40 ms
    lag = np.empty_like(drive); acc = drive[0]; al = dt / 0.040
    for n_ in range(len(drive)):
        acc += (drive[n_] - acc) * al; lag[n_] = acc
    white[i] = lag * gain[i]
# box filter to frames
white_f = white.reshape(N, NF, SUB).mean(2)
ember_f = ember.reshape(N, NF, SUB).mean(2)
tr_r_f = tr_r.reshape(N, NF, SUB).mean(2)
tr_g_f = tr_g.reshape(N, NF, SUB).mean(2)
np.savez(os.path.join(DATA, "pulse.npz"), white=white_f, ember=ember_f, bpm=bpm, phase0=phase0, gain=gain,
         dying=np.array(PL["dying"]), death_t=np.array([death_t.get(i, -1) for i in PL["dying"]]))
print("death times:", {i: round(t, 3) for i, t in death_t.items()}, "(%.1fs)" % (time.time() - t0))
if A.plan_only:
    sys.exit(0)

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = FPS
scn.frame_start, scn.frame_end = 0, NF - 1

img = bpy.data.images.new("pulse_tex", N, NF, alpha=True, float_buffer=True)
px = np.zeros((NF, N, 4), np.float32)
px[..., 0] = white_f.T; px[..., 1] = ember_f.T; px[..., 3] = 1
img.pixels.foreach_set(px.ravel())
img.pack()
img.colorspace_settings.name = "Non-Color"
img_tr = bpy.data.images.new("glass_tex", N, NF, alpha=True, float_buffer=True)
px = np.zeros((NF, N, 4), np.float32)
px[..., 0] = tr_r_f.T; px[..., 1] = tr_g_f.T; px[..., 2] = tr_g_f.T; px[..., 3] = 1
img_tr.pixels.foreach_set(px.ravel())
img_tr.pack()
img_tr.colorspace_settings.name = "Non-Color"


def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


FRAME_KEYS = []   # value nodes that carry (frame + 0.5) / NF
LOOK = {}         # node tree -> the lookup vector, for the glass transmission texture


def pulse_lookup(nt):
    """returns (white, ember) sockets for this bulb at the current frame."""
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "idx"
    fr = nt.nodes.new("ShaderNodeValue"); FRAME_KEYS.append(fr)
    cx = nt.nodes.new("ShaderNodeCombineXYZ")
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY_ADD"
    mu.inputs[1].default_value = 1.0 / N; mu.inputs[2].default_value = 0.5 / N
    nt.links.new(at.outputs["Fac"], mu.inputs[0]); nt.links.new(mu.outputs[0], cx.inputs[0])
    nt.links.new(fr.outputs[0], cx.inputs[1])
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Closest"; tx.extension = "EXTEND"
    nt.links.new(cx.outputs[0], tx.inputs["Vector"])
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tx.outputs["Color"], sp.inputs[0])
    LOOK[nt.name_full] = cx.outputs[0]
    return sp.outputs[0], sp.outputs[1]


def emis_color(nt, w, e, sw, se):
    """bone * w * sw + red * e * se  -> color socket"""
    def scaled(sock, col, s):
        m = nt.nodes.new("ShaderNodeVectorMath"); m.operation = "SCALE"
        m.inputs[0].default_value = tuple(c * s for c in col)
        nt.links.new(sock, m.inputs["Scale"]); return m.outputs[0]
    ad = nt.nodes.new("ShaderNodeVectorMath"); ad.operation = "ADD"
    nt.links.new(scaled(w, BONE, sw), ad.inputs[0]); nt.links.new(scaled(e, RED, se), ad.inputs[1])
    return ad.outputs[0]


# filament: bright, small
FIL_W, FIL_E = 9.0, 1.35
m_fil, nt, out = nodes_mat("filament")
w, e = pulse_lookup(nt)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
nt.links.new(emis_color(nt, w, e, FIL_W, FIL_E), em.inputs["Color"])
nt.links.new(em.outputs[0], out.inputs["Surface"])

# glass: thin clear shell = transparent + fresnel gloss, plus a soft centre-weighted glow (satin glass)
GLOW_W, GLOW_E = 0.55, 0.05
m_gl, nt, out = nodes_mat("glass")
w, e = pulse_lookup(nt)
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
ttx = nt.nodes.new("ShaderNodeTexImage"); ttx.image = img_tr; ttx.interpolation = "Closest"; ttx.extension = "EXTEND"
nt.links.new(LOOK[nt.name_full], ttx.inputs["Vector"]); nt.links.new(ttx.outputs["Color"], tr.inputs["Color"])
gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.0
fr_ = nt.nodes.new("ShaderNodeFresnel"); fr_.inputs["IOR"].default_value = 1.5
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(fr_.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
nt.links.new(lw.outputs["Facing"], inv.inputs[1])
pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
nt.links.new(inv.outputs[0], pw.inputs[0])
emg = nt.nodes.new("ShaderNodeEmission")
nt.links.new(emis_color(nt, w, e, GLOW_W, GLOW_E), emg.inputs["Color"]); nt.links.new(pw.outputs[0], emg.inputs["Strength"])
ad = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(mx.outputs[0], ad.inputs[0]); nt.links.new(emg.outputs[0], ad.inputs[1])
nt.links.new(ad.outputs[0], out.inputs["Surface"])
m_gl.cycles.emission_sampling = "NONE"      # glow reaches the camera directly; not a light for other surfaces

# cap and cable: black, a little gloss so they catch their neighbours
def dark(name, rough, base=0.012, spec=0.5):
    m, nt, out = nodes_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (base, base, base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m
m_cap = dark("cap", 0.32, 0.02, 0.6)
# cables: black, with a faint even sheen that dies away above the cloud (no sampled light, so nothing to converge)
CAB_L = 0.042
m_cab, nt, out = nodes_mat("cable")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.010, 0.010, 0.010, 1)
b.inputs["Roughness"].default_value = 0.22; b.inputs["Specular IOR Level"].default_value = 0.45
geo = nt.nodes.new("ShaderNodeNewGeometry")
sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sz.inputs[0])
ztop = float(P[:, 2].max())
mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
mr.inputs["From Min"].default_value = ztop - 0.5; mr.inputs["From Max"].default_value = ztop + 3.2
mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
nt.links.new(sz.outputs["Z"], mr.inputs["Value"])
CAB_VAL = nt.nodes.new("ShaderNodeValue")
cm_ = nt.nodes.new("ShaderNodeMath"); cm_.operation = "MULTIPLY"
nt.links.new(mr.outputs[0], cm_.inputs[0]); nt.links.new(CAB_VAL.outputs[0], cm_.inputs[1])
emc = nt.nodes.new("ShaderNodeEmission"); emc.inputs["Color"].default_value = (*BONE, 1)
nt.links.new(cm_.outputs[0], emc.inputs["Strength"])
adc = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(b.outputs[0], adc.inputs[0]); nt.links.new(emc.outputs[0], adc.inputs[1]); nt.links.new(adc.outputs[0], out.inputs["Surface"])
m_cab.cycles.emission_sampling = "NONE"

# threads: dark in the close-up, rise to blood red as the whole liver is seen
m_thr, nt, out = nodes_mat("thread")
emt = nt.nodes.new("ShaderNodeEmission"); emt.inputs["Color"].default_value = (*RED, 1)
THR_VAL = nt.nodes.new("ShaderNodeValue")                        # the blood front, 0-1 along the tree
aa = nt.nodes.new("ShaderNodeAttribute"); aa.attribute_type = "GEOMETRY"; aa.attribute_name = "arr"
sb = nt.nodes.new("ShaderNodeMath"); sb.operation = "SUBTRACT"
nt.links.new(THR_VAL.outputs[0], sb.inputs[0]); nt.links.new(aa.outputs["Fac"], sb.inputs[1])
gt = nt.nodes.new("ShaderNodeMapRange"); gt.interpolation_type = "SMOOTHSTEP"
gt.inputs["From Min"].default_value = 0.0; gt.inputs["From Max"].default_value = 0.14
gt.inputs["To Min"].default_value = 0.0; gt.inputs["To Max"].default_value = 0.85
nt.links.new(sb.outputs[0], gt.inputs["Value"])
nt.links.new(gt.outputs[0], emt.inputs["Strength"]); nt.links.new(emt.outputs[0], out.inputs["Surface"])
m_thr.cycles.emission_sampling = "NONE"


def build_bulb():
    bm = bmesh.new()
    # globe
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=RG)
    for f_ in bm.faces: f_.material_index = 0; f_.smooth = True
    # cap (E14) + short neck
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0085, radius2=0.0085, depth=CAP_H)
    for v in geom["verts"]: v.co.z += RG + CAP_H / 2 - 0.004
    for f_ in {f_ for v in geom["verts"] for f_ in v.link_faces}: f_.material_index = 2; f_.smooth = True
    # filament: a short vertical helix + two leads to the neck
    pts = []
    turns, hh, rr = 3.5, 0.020, 0.0055
    for k in range(141):
        t = k / 140
        a = t * turns * 2 * math.pi
        pts.append(Vector((rr * math.cos(a), rr * math.sin(a), -hh / 2 + hh * t)))
    leads = [[Vector((rr, 0, -hh / 2)), Vector((0.0025, 0, RG - 0.006))],
             [pts[-1].copy(), Vector((-0.0025, 0, RG - 0.006))]]

    def tube(path, rad, segs=6):
        rings = []
        for k, p in enumerate(path):
            tng = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
            n0 = tng.cross(Vector((0, 0, 1)))
            if n0.length < 1e-4: n0 = tng.cross(Vector((1, 0, 0)))
            n0.normalize(); b0 = tng.cross(n0)
            ring = [bm.verts.new(p + (n0 * math.cos(2 * math.pi * s / segs) + b0 * math.sin(2 * math.pi * s / segs)) * rad) for s in range(segs)]
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for s in range(segs):
                f_ = bm.faces.new((r0[s], r0[(s + 1) % segs], r1[(s + 1) % segs], r1[s])); f_.material_index = 1; f_.smooth = True
    tube(pts, 0.00075)
    for a_, b_ in leads:
        tube([a_.lerp(b_, t / 8) for t in range(9)], 0.00035, 5)
    me = bpy.data.meshes.new("bulb")
    bm.to_mesh(me); bm.free()
    for m in (m_gl, m_fil, m_cap): me.materials.append(m)
    return me


bulb_me = build_bulb()
col = bpy.data.collections.new("bulbs"); scn.collection.children.link(col)
rngr = np.random.default_rng(7)
for i in range(N):
    o = bpy.data.objects.new("b%04d" % i, bulb_me)
    o.location = P[i].tolist(); o.rotation_euler = (0, 0, float(rngr.random() * 2 * math.pi))
    o["idx"] = float(i)
    col.objects.link(o)

# cables: one mesh, a thin 6-sided tube from each cap up into the dark
cv, cf = [], []
for i in range(N):
    z0 = P[i, 2] + RG + CAP_H - 0.005
    base = len(cv)
    for s in range(6):
        a = 2 * math.pi * s / 6
        dx, dy = 0.0018 * math.cos(a), 0.0018 * math.sin(a)
        cv.append((P[i, 0] + dx, P[i, 1] + dy, z0)); cv.append((P[i, 0] + dx, P[i, 1] + dy, CEIL))
    for s in range(6):
        a0, a1 = base + 2 * s, base + 2 * ((s + 1) % 6)
        cf.append((a0, a1, a1 + 1, a0 + 1))
cme = bpy.data.meshes.new("cables"); cme.from_pydata(cv, [], cf)
for p_ in cme.polygons: p_.use_smooth = True
cme.materials.append(m_cab)
cab = bpy.data.objects.new("cables", cme); scn.collection.objects.link(cab)

# threads: a 6-sided tube per tree edge; thicker on the trunks
tv, tf, ta = [], [], []
for i, p_ in enumerate(THR_PAR):
    if p_ < 0: continue
    a_, b_ = THR[i], THR[p_]
    rt = float(np.clip(0.0030 + 0.013 * THR_RAD[i], 0.0030, 0.0072))
    ax = b_ - a_; L_ = np.linalg.norm(ax)
    if L_ < 1e-6: continue
    ax = ax / L_
    n0 = np.cross(ax, [0, 0, 1.0])
    if np.linalg.norm(n0) < 1e-3: n0 = np.cross(ax, [1.0, 0, 0])
    n0 /= np.linalg.norm(n0); b0 = np.cross(ax, n0)
    base = len(tv)
    for s in range(6):
        an = 2 * math.pi * s / 6
        o_ = (n0 * math.cos(an) + b0 * math.sin(an)) * rt
        tv.append(tuple(a_ - ax * 0.004 + o_)); tv.append(tuple(b_ + ax * 0.004 + o_))
        ta += [THR_ARR[i], THR_ARR[p_]]
    for s in range(6):
        a0, a1 = base + 2 * s, base + 2 * ((s + 1) % 6)
        tf.append((a0, a1, a1 + 1, a0 + 1))
tme = bpy.data.meshes.new("threads"); tme.from_pydata(tv, [], tf)
for p_ in tme.polygons: p_.use_smooth = True
_at = tme.attributes.new("arr", "FLOAT", "POINT"); _at.data.foreach_set("value", np.array(ta, np.float32))
tme.materials.append(m_thr)
thr = bpy.data.objects.new("threads", tme); scn.collection.objects.link(thr)

# floor: polished black resin, a dim mirror
if A.floor:
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "floor"
    m, nt, out = nodes_mat("floor")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    b.inputs["Roughness"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.35
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    fl.data.materials.append(m)

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
print("scene built (%.1fs)" % (time.time() - t0))

# ------------------------------------------------------------------ camera (baked per frame)
S, E, f, r, u = (np.array(PL[k]) for k in ("S", "E", "f", "r", "u"))
TGT = np.array(PL["tgt"])
DY = [P[i] for i in PL["dying"]]             # the four, in the order they go out
f_end = (TGT - E) / np.linalg.norm(TGT - E)
Q0 = Vector(f.tolist()).to_track_quat("-Z", "Y")
Q1 = Vector(f_end.tolist()).to_track_quat("-Z", "Y")


def smoother(x):
    x = min(1.0, max(0.0, x)); return x * x * x * (x * (x * 6 - 15) + 10)


F_PB = (165, 294)                            # pull-back frames (5.5 -> 9.8 s), slower = quieter
# focus: settles on the first light, then racks to the next light as each one goes
RACKS = [(int(FPS * (T_DIE[k] + 0.42)), int(FPS * (T_DIE[k] + 0.82)), k + 1) for k in range(3)]


def focus_point(fr):
    pt = DY[0]
    for a_, b_, k in RACKS:
        pt = pt * (1 - smoother((fr - a_) / (b_ - a_))) + DY[k] * smoother((fr - a_) / (b_ - a_))
    return pt


def cam_state(fr):
    drift_in = 0.06 * min(1.0, fr / F_PB[0])                       # a slow drift in during the first 5.7 s
    pb = smoother((fr - F_PB[0]) / (F_PB[1] - F_PB[0]))
    pos = S + f * drift_in * (1 - pb) + (E - S) * pb                # lands at E on frame 294 and holds
    q = Q0.slerp(Q1, smoother((fr - F_PB[0] - 6) / (F_PB[1] - F_PB[0] - 6)))
    fw = np.array((q @ Vector((0, 0, -1)))[:])
    rk = smoother((fr - (F_PB[0] + 26)) / (F_PB[1] - F_PB[0] - 20))
    fpt = focus_point(fr) * (1 - rk) + TGT * rk
    fdist = max(0.3, float(np.dot(fpt - pos, fw)))
    fdist += 0.35 * (1 - smoother(fr / 50))                        # opening: focus settles onto the first light
    fstop = 1.8 + 1.6 * rk
    return pos, q, fdist, fstop


camd = bpy.data.cameras.new("cam"); camd.lens = LENS; camd.sensor_width = 36; camd.sensor_fit = "HORIZONTAL"
camd.clip_start = 0.02; camd.clip_end = 200
cam = bpy.data.objects.new("cam", camd); scn.collection.objects.link(cam); scn.camera = cam
cam.rotation_mode = "QUATERNION"
camd.dof.use_dof = True; camd.dof.aperture_blades = 0
for fr in range(NF):
    pos, q, fdist, fstop = cam_state(fr)
    cam.location = pos.tolist(); cam.rotation_quaternion = q
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_quaternion", frame=fr)
    camd.dof.focus_distance = fdist; camd.dof.aperture_fstop = fstop
    camd.dof.keyframe_insert("focus_distance", frame=fr); camd.dof.keyframe_insert("aperture_fstop", frame=fr)
    for vn in FRAME_KEYS:
        vn.outputs[0].default_value = (fr + 0.5) / NF
        vn.outputs[0].keyframe_insert("default_value", frame=fr)
    THR_VAL.outputs[0].default_value = -0.2 + 1.45 * smoother((fr - 226) / 60)
    THR_VAL.outputs[0].keyframe_insert("default_value", frame=fr)
    CAB_VAL.outputs[0].default_value = CAB_L * smoother((fr - 212) / 60)
    CAB_VAL.outputs[0].keyframe_insert("default_value", frame=fr)


def set_interp(idb, kind):
    ad = idb.animation_data
    if not ad or not ad.action: return
    act = ad.action
    curves = []
    if hasattr(act, "fcurves"):
        try: curves = list(act.fcurves)
        except Exception: curves = []
    if not curves and hasattr(act, "layers"):
        for L in act.layers:
            for st in L.strips:
                for cb in st.channelbags: curves += list(cb.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points: kp.interpolation = kind


set_interp(cam, "LINEAR"); set_interp(camd, "LINEAR")
for m in (m_fil, m_gl): set_interp(m.node_tree, "CONSTANT")
set_interp(m_thr.node_tree, "LINEAR"); set_interp(m_cab.node_tree, "LINEAR")

# ------------------------------------------------------------------ render settings
scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
pref.compute_device_type = "OPTIX"; pref.get_devices()
for dv in pref.devices: dv.use = (dv.type == "OPTIX")
scn.cycles.device = "GPU"
scn.cycles.samples = A.samples
scn.cycles.use_adaptive_sampling = True; scn.cycles.adaptive_threshold = A.thresh
scn.cycles.use_denoising = True; scn.cycles.denoiser = "OPTIX"
scn.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scn.cycles.max_bounces = 8; scn.cycles.diffuse_bounces = 1; scn.cycles.glossy_bounces = 3
scn.cycles.transmission_bounces = 4; scn.cycles.transparent_max_bounces = 24; scn.cycles.volume_bounces = 0
scn.cycles.caustics_refractive = False; scn.cycles.caustics_reflective = False
scn.cycles.blur_glossy = 0.0
scn.cycles.sample_clamp_direct = 6.0
scn.cycles.sample_clamp_indirect = 4.0
scn.cycles.seed = 1412; scn.cycles.use_animated_seed = False
scn.render.use_motion_blur = True; scn.render.motion_blur_shutter = 0.5
scn.render.use_persistent_data = True
scn.render.resolution_x = W_; scn.render.resolution_y = H_; scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"; scn.view_settings.exposure = 0.0
ims = scn.render.image_settings
ims.file_format = "OPEN_EXR"; ims.color_mode = "RGB"; ims.color_depth = "16"; ims.exr_codec = "ZIP"

# camera-space data for post / overlays: projected bulb positions per frame (only for the four)
from bpy_extras.object_utils import world_to_camera_view
proj = {}
for fr in range(0, NF, 1):
    scn.frame_set(fr)
    proj[fr] = [list(world_to_camera_view(scn, cam, Vector(P[i].tolist()))[:]) for i in PL["dying"]]
json.dump(proj, open(os.path.join(DATA, "dying_proj.json"), "w"))
print("setup done (%.1fs)" % (time.time() - t0))

if A.stills:
    for fr in [int(x) for x in A.stills.split(",")]:
        scn.frame_set(fr); scn.render.filepath = A.out + "%04d.exr" % fr
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print("RENDER_TIME %.1fs -> %s" % (time.time() - t1, scn.render.filepath), flush=True)
elif A.frames:
    a, b = [int(x) for x in A.frames.split("-")]
    for fr in range(a, b + 1, A.step):
        fp = A.out + "%04d.exr" % fr
        if os.path.exists(fp): continue
        scn.frame_set(fr); scn.render.filepath = fp
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print("RENDER_TIME %.1fs -> %s" % (time.time() - t1, fp), flush=True)
