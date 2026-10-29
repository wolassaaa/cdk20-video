"""S1 'move' animatic -- scene builder.

blender -b --factory-startup -P build.py -- [--save path.blend]

Builds a heat-pass scene from real BodyParts3D anatomy (mm units, re-centred on
the liver). Every surface is pure emission whose strength = heat (0..~1.3);
grade.py maps the grayscale render to the false-colour heat ramp.

All timing lives in timeline() below (frames @30fps, 240 total).
"""
import bpy, bmesh, os, sys, math, json, time
import numpy as np
from mathutils import Vector, Matrix, Quaternion, kdtree

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo

STL = os.path.normpath(os.path.join(HERE, "..", "..", "..", "assets", "anatomy", "bp3d_v4_groups_stl"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = argv[argv.index("--save") + 1] if "--save" in argv else os.path.join(HERE, "s1_move.blend")

FPS, NF = 30, 240
HITS = (4, 24, 46)
LOSSES = (150, 170, 190, 210)

# ----------------------------------------------------------------------------- utils
def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def smootherstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * t * (t * (6 * t - 15) + 10)

def gsmooth(arr, sigma):
    """Gaussian smoothing along axis 0 with edge padding."""
    if sigma <= 0: return arr
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    pad = np.concatenate([np.repeat(arr[:1], r, 0), arr, np.repeat(arr[-1:], r, 0)], 0)
    out = np.zeros_like(arr, dtype=float)
    for i, w in enumerate(k):
        out += w * pad[i:i + len(arr)]
    return out

def import_stl(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(STL, name + ".stl"))
    o = bpy.context.selected_objects[0]; o.name = name
    return o

def clean_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)

# ----------------------------------------------------------------------------- anatomy
clean_scene()
t0 = time.time()
liver = import_stl("liver_parenchyma_segments")
lco = np.array([v.co[:] for v in liver.data.vertices])
C0 = (lco.min(0) + lco.max(0)) / 2.0                         # liver bbox centre (mm)

trib = import_stl("portal_tributaries_splenic_SMV")
pv = import_stl("portal_vein_hepatic")
hv = import_stl("hepatic_veins")
ivc = import_stl("inferior_vena_cava")
for o in (liver, trib, pv, hv, ivc):
    o.data.transform(Matrix.Translation(-Vector(C0)))
    o.data.update()

# join portal system (SMV + splenic + portal trunk + intrahepatic branches)
bpy.ops.object.select_all(action='DESELECT')
trib.select_set(True); pv.select_set(True); bpy.context.view_layer.objects.active = trib
bpy.ops.object.join(); pv = bpy.context.active_object; pv.name = "portal_system"

def merged_bm(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(o.data); bm.free(); o.data.update()

for o in (pv, hv, ivc, liver): merged_bm(o)

me = pv.data
co = np.array([v.co[:] for v in me.vertices])
edges = [tuple(e.vertices) for e in me.edges]
lab = geo.islands(len(co), edges)
extra = geo.bridge_edges(co, lab)
seed = int(co[:, 2].argmin())                                  # bottom tip of the SMV
dist, pred = geo.geodesic(co, edges, extra, seed)

# splenic vein: real flow runs *toward* the confluence, so re-time it as an
# inflow that arrives at the confluence together with the SMV front.
spl_lab = lab[int(co[:, 0].argmax())]
spl = lab == spl_lab
d_conf = dist[spl].min()
g = dist[spl] - d_conf
dist[spl] = d_conf - g * (d_conf - 12.0) / g.max()

# trunk centreline: follow the Dijkstra path toward the far right-lobe tip and
# take ring centroids (verts at the same geodesic distance, near the path).
def path_to(t):
    p = []
    while t != -1: p.append(t); t = pred[t]
    return np.array(p[::-1])
intra = (co[:, 2] > -10) & ~spl
iR = np.where(intra)[0][co[intra, 0].argmin()]
iL = np.where(intra)[0][co[intra, 0].argmax()]
pR, pL = path_to(iR), path_to(iL)
# hilum = where the right- and left-lobe paths separate by > 14 mm
D_HILUM = None
for s in np.arange(100, dist[iR], 1.0):
    a = pR[np.searchsorted(dist[pR], s)]; b = pL[np.searchsorted(dist[pL], s)]
    if np.linalg.norm(co[a] - co[b]) > 14.0: D_HILUM = s - 6; break
D_MAX = float(dist[~spl].max())
S = np.arange(0.0, D_HILUM + 1.0, 1.0)
cl = []
for s in S:
    a = pR[min(np.searchsorted(dist[pR], s), len(pR) - 1)]
    m = (np.abs(dist - s) < 3.0) & (np.linalg.norm(co - co[a], axis=1) < 13.0) & ~spl
    cl.append(co[m].mean(0) if m.sum() > 3 else co[a])
cl = gsmooth(gsmooth(np.array(cl), 5.0), 5.0)
HILUM = cl[-1]
print("D_HILUM %.1f D_MAX %.1f d_conf %.1f hilum %s" % (D_HILUM, D_MAX, d_conf, np.round(HILUM, 1)))

# heart-beat spots: 4 well-separated points on distal portal branches
cand = np.where((dist > D_HILUM + 45) & (dist < D_MAX - 15) & ~spl)[0]
spots = [cand[np.argmin(co[cand, 0])]]
for _ in range(3):
    dmin = np.min([np.linalg.norm(co[cand] - co[s], axis=1) for s in spots], 0)
    spots.append(cand[np.argmax(dmin)])
SPOTS = [co[s] for s in spots]
print("spots", [np.round(p) for p in SPOTS])

# ---- subdivide for smooth close-ups, then carry 'd' over by nearest base vertex
def subdivide_with_attr(o, levels, base_co=None, base_val=None, name=None):
    mod = o.modifiers.new("sub", 'SUBSURF'); mod.levels = mod.render_levels = levels
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="sub")
    for p in o.data.polygons: p.use_smooth = True
    if base_co is not None:
        kd = kdtree.KDTree(len(base_co))
        for i, p in enumerate(base_co): kd.insert(p, i)
        kd.balance()
        idx = np.array([kd.find(v.co)[1] for v in o.data.vertices])
        for nm, bv in base_val.items():
            at = o.data.attributes.new(nm, 'FLOAT', 'POINT')
            at.data.foreach_set("value", np.asarray(bv, np.float32)[idx])

# main-path mask: 1 on the SMV->portal trunk and everything past the hilum; 0 on the
# SMV's own side tributaries and the bottom hook (blood flows *into* the trunk there,
# so the dye front must not run down them; they only warm up with the whole organ).
D0, D1 = 50.0, 72.0     # the point appears on the straight part of the SMV, creeps to D1 by hit 2
ci = np.clip(dist.astype(int), 0, len(cl) - 1)
off = np.linalg.norm(co - cl[ci], axis=1)
side = ((dist < D_HILUM - 4) & (off > np.where(dist < 150, 8.5, 13.0))) | (dist < D0 - 6)
side &= ~spl
MAIN = (~side).astype(np.float32)
print("side verts", int(side.sum()))
subdivide_with_attr(pv, 1, co, {"d": dist, "m": MAIN})
bpy.data.objects.remove(ivc)   # IVC read as a vertical stripe behind the liver: dropped
for o in (hv,):
    subdivide_with_attr(o, 1)
for p in liver.data.polygons: p.use_smooth = True
# parenchyma: distance from hilum (for the fill-out reveal)
lv = np.array([v.co[:] for v in liver.data.vertices])
at = liver.data.attributes.new("dp", 'FLOAT', 'POINT')
at.data.foreach_set("value", np.linalg.norm(lv - HILUM, axis=1).astype(np.float32))
print("geometry %.1fs" % (time.time() - t0))

# ----------------------------------------------------------------------------- timeline
f = np.arange(NF, dtype=float)


def front_curve():
    """Dye front position (mm of geodesic distance) per frame."""
    fr = np.full(NF, -8.0)
    # 4..24: the point appears at the SMV tip and creeps
    a = (f >= 4) & (f < 24)
    fr[a] = D0 + (D1 - D0) * ((f[a] - 4) / 20.0) ** 1.3
    # 24..46: rush up the SMV/portal trunk; integrate a smooth speed bump
    tt = np.linspace(24, 46, 400)
    v = 1.0 + 14.0 * np.sin(np.pi * np.clip((tt - 24) / 24.0, 0, 1)) ** 1.6
    cum = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(tt))])
    cum = cum / cum[-1] * (D_HILUM - D1) + D1
    b = (f >= 24) & (f <= 46)
    fr[b] = np.interp(f[b], tt, cum)
    # 46..~104: flood the intrahepatic tree level by level (three surges)
    c = f > 46
    x = f[c]
    surge = (0.45 * smootherstep(46, 62, x) + 0.33 * smootherstep(58, 80, x) + 0.22 * smootherstep(76, 104, x))
    fr[c] = D_HILUM + surge * (D_MAX + 8 - D_HILUM) + 3.0 * smoothstep(46, 50, x)
    return fr

FRONT = front_curve()

# hit accents (head gain) and "life" level
gain = np.ones(NF)
for h, amp in zip(HITS, (0.5, 0.6, 0.8)):
    gain += amp * np.where(f >= h, np.exp(-(f - h) / 5.0), 0) * smoothstep(h - 1, h, f)
head_vis = smoothstep(3, 4.5, f)                                # nothing before hit 1

# losses: count 0..4 (+ a final drift), each loss = one step down the heat ramp.
# Step tables are in heat units (see grade.py: <0.415 cold half, 0.415-0.445 acid, >0.445 hot half)
lossc = np.zeros(NF)
for L in LOSSES:
    lossc += smootherstep(L, L + 9, f)
lossc += 0.4 * smoothstep(212, 240, f)
V_STEPS = [0.80, 0.68, 0.575, 0.48, 0.37, 0.34]     # portal veins (direct view)
F_STEPS = [0.555, 0.475, 0.36, 0.27, 0.18, 0.15]    # parenchyma field
life = 1 - lossc / 4.0
xs = [0, 1, 2, 3, 4, 5]
warm = smoothstep(52, 104, f)                                    # trail -> whole-liver warmth
trail = 0.52 * (1 - warm) + V_STEPS[0] * warm                   # cooling tail behind the hot point
paren_level = F_STEPS[0] * smoothstep(48, 64, f)
drift = smoothstep(212, 240, f)
DV, DF = (V_STEPS[0] - V_STEPS[4]) / 4, (F_STEPS[0] - F_STEPS[4]) / 4   # one step per loss
COOL_SPEED, COOL_LEN = 13.0, 7.0      # mm/frame wave speed, frames to settle locally
paren_front = 210 * smootherstep(48, 108, f)                     # mm from hilum
ghost = 0.12 + (V_STEPS[0] - 0.10 - 0.12) * warm                 # hepatic veins (warm level)

# heart-beat spots
RATES_BPM = (64, 78, 92, 112)
def beat(t, bpm, phase):
    p = ((t * bpm / 60.0 / FPS) + phase) % 1.0
    # lub-dub: two soft bumps per cycle (wide enough to read at 30fps)
    return np.exp(-((p - 0.10) / 0.075) ** 2) + 0.6 * np.exp(-((p - 0.36) / 0.09) ** 2)
spot = []
for i, (bpm, L) in enumerate(zip(RATES_BPM, LOSSES)):
    on = smoothstep(96 + 4 * i, 112 + 4 * i, f)
    b = beat(f, bpm, 0.17 * i)
    # freeze the pulse at the loss frame then cool exponentially
    alive = f < L
    last = 0.5 + 0.6 * b[L - 1] if L - 1 < NF else 0
    val = np.where(alive, on * (0.5 + 0.6 * b), on * last * np.exp(-(f - L) / 7.0))
    val = val + np.where(f >= L, 0.9 * np.exp(-(f - L) / 2.5), 0)     # brief death flash
    if i == 3:   # the last one leaves a faint trace
        val = np.where(f >= L, np.maximum(val, 0.44 - 0.08 * smoothstep(L + 5, 240, f)), val)
    spot.append(val)
spot = np.array(spot)

# ----------------------------------------------------------------------------- camera
def norm(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)

lead = -3.0
s_cam = np.where(f < 4, D0, FRONT) + lead
s_cam = D_HILUM - 10.0 * np.log1p(np.exp((D_HILUM - s_cam) / 10.0))   # soft clamp at the hilum
P = np.array([np.array([np.interp(s, S, cl[:, k]) for k in range(3)]) for s in s_cam])
P = gsmooth(P, 2.5)

LIV_T = np.array([0.0, 0.0, 0.0])                               # liver centre (re-centred)
w = smootherstep(32, 106, f)                                     # follow -> organ blend
wz = smootherstep(28, 102, f) ** 0.6                                  # zoom blend (log distance)
# follow direction: in front (-y), a little patient-right (-x) and below; slow orbit
az0 = np.radians(-28 + 14 * smoothstep(0, 46, f))
el0 = np.radians(-20 + 4 * smoothstep(0, 46, f))   # from below: the vessel climbs away
az1 = np.radians(-22 + 9 * smoothstep(104, 240, f))              # final slow drift
el1 = np.radians(-9 - 3 * smoothstep(104, 240, f))
az = az0 * (1 - w) + az1 * w
el = el0 * (1 - w) + el1 * w
dirv = np.stack([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)], 1)
r0 = 62.0 - 10.0 * smoothstep(0, 30, f)                          # tiny push-in at the start
r1 = 505.0 * (1 - 0.05 * smoothstep(108, 240, f))
r = np.exp(np.log(r0) * (1 - wz) + np.log(r1) * wz)
T = P * (1 - w)[:, None] + LIV_T * w[:, None]
CAM = T + dirv * r[:, None]
SHIFT_X = -0.25 * smootherstep(40, 108, f)
_allv = np.concatenate([co, np.array([v.co[:] for v in hv.data.vertices])])
_kd = kdtree.KDTree(len(_allv))
for _i, _p in enumerate(_allv): _kd.insert(_p, _i)
_kd.balance()
CLEAR = np.array([_kd.find(CAM[i])[2] for i in range(NF)])
print("camera clearance (mm) min %.1f @ %d; f30-70:" % (CLEAR.min(), CLEAR.argmin()), np.round(CLEAR[30:70:4], 0))
SHIFT_Y = 0.0

# ----------------------------------------------------------------------------- materials
def mk_group():
    """Shared node group holding every animated scalar (one keyed datablock)."""
    ng = bpy.data.node_groups.new("Clock", 'ShaderNodeTree')
    names = ["front", "gain", "headvis", "trail", "paren", "pfront", "ghost", "drift", "warm"] + \
            ["spot%d" % i for i in range(4)] + ["age%d" % i for i in range(4)]
    out = ng.nodes.new("NodeGroupOutput")
    for i, n in enumerate(names):
        ng.interface.new_socket(n, in_out='OUTPUT', socket_type='NodeSocketFloat')
        v = ng.nodes.new("ShaderNodeValue"); v.name = v.label = n; v.location = (0, -80 * i)
        ng.links.new(v.outputs[0], out.inputs[n])
    return ng, names

CLOCK, CNAMES = mk_group()

class NB:
    """Tiny node-building helper."""
    def __init__(s, mat):
        mat.use_nodes = True
        s.nt = mat.node_tree; s.nt.nodes.clear(); s.x = 0
    def node(s, t, **kw):
        n = s.nt.nodes.new(t); n.location = (s.x, 0); s.x += 160
        for k, v in kw.items(): setattr(n, k, v)
        return n
    def link(s, a, b): s.nt.links.new(a, b)
    def _in(s, sock, v):
        if isinstance(v, (int, float)): sock.default_value = v
        else: s.link(v, sock)
    def m(s, op, a, b=0.0, c=None, clamp=False):
        n = s.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        s._in(n.inputs[0], a); s._in(n.inputs[1], b)
        if c is not None: s._in(n.inputs[2], c)
        return n.outputs[0]
    def attr(s, name):
        return s.node("ShaderNodeAttribute", attribute_name=name, attribute_type='GEOMETRY').outputs["Fac"]
    def clock(s):
        g = s.node("ShaderNodeGroup"); g.node_tree = CLOCK
        return {n: g.outputs[n] for n in CNAMES}

def shading(nb):
    """Fake 'glossy tube' term in 0..1: bright facing core, dark limb, a key light."""
    lw = nb.node("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    facing = lw.outputs["Facing"]                                   # 0 facing .. 1 grazing
    core = nb.m('SUBTRACT', 1.0, nb.m('POWER', facing, 1.6))
    geom = nb.node("ShaderNodeNewGeometry")
    dot = nb.node("ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nb.link(geom.outputs["Normal"], dot.inputs[0]); dot.inputs[1].default_value = (-0.35, -0.55, 0.76)
    lam = nb.m('MULTIPLY', nb.m('ADD', dot.outputs["Value"], 1.0), 0.5)
    spec = nb.m('POWER', nb.m('MAXIMUM', nb.m('SUBTRACT', lam, 0.78), 0.0), 1.0)
    sh = nb.m('ADD', nb.m('MULTIPLY', core, 0.72), nb.m('MULTIPLY', lam, 0.28))
    return sh, nb.m('MULTIPLY', spec, 2.2)

def cooling(nb, ck):
    """Number of losses that have reached this point (0..4): each spot's death sends
    a cooling wave outward at COOL_SPEED; locally it settles over COOL_LEN frames."""
    geom = nb.node("ShaderNodeNewGeometry")
    acc = None
    for i, p in enumerate(SPOTS):
        dv = nb.node("ShaderNodeVectorMath", operation='DISTANCE')
        nb.link(geom.outputs["Position"], dv.inputs[0]); dv.inputs[1].default_value = tuple(p)
        t = nb.m('DIVIDE', nb.m('SUBTRACT', ck["age%d" % i], nb.m('DIVIDE', dv.outputs["Value"], COOL_SPEED)), COOL_LEN)
        t = nb.m('MINIMUM', nb.m('MAXIMUM', t, 0.0), 1.0)
        t = nb.m('MULTIPLY', nb.m('MULTIPLY', t, t), nb.m('SUBTRACT', 3.0, nb.m('MULTIPLY', t, 2.0)))  # smoothstep
        acc = t if acc is None else nb.m('ADD', acc, t)
    return acc

def spot_heat(nb, ck, radius):
    """Sum of gaussian heat blobs around the 4 beating spots (world position)."""
    geom = nb.node("ShaderNodeNewGeometry")
    acc = None
    for i, p in enumerate(SPOTS):
        dv = nb.node("ShaderNodeVectorMath", operation='DISTANCE')
        nb.link(geom.outputs["Position"], dv.inputs[0]); dv.inputs[1].default_value = tuple(p)
        g = nb.m('EXPONENT', nb.m('MULTIPLY', nb.m('POWER', nb.m('DIVIDE', dv.outputs["Value"], radius), 2.0), -1.0))
        g = nb.m('MULTIPLY', g, ck["spot%d" % i])
        acc = g if acc is None else nb.m('ADD', acc, g)
    return acc

def out_emission(nb, strength, alpha=None):
    em = nb.node("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1)
    nb._in(em.inputs["Strength"], strength)
    out = nb.node("ShaderNodeOutputMaterial")
    if alpha is None:
        nb.link(em.outputs[0], out.inputs["Surface"])
    else:
        tr = nb.node("ShaderNodeBsdfTransparent")
        mix = nb.node("ShaderNodeMixShader")
        nb._in(mix.inputs[0], alpha)
        nb.link(tr.outputs[0], mix.inputs[1]); nb.link(em.outputs[0], mix.inputs[2])
        nb.link(mix.outputs[0], out.inputs["Surface"])

def mat_portal():
    mat = bpy.data.materials.new("M_portal_dye"); nb = NB(mat); ck = nb.clock()
    d = nb.attr("d")
    x = nb.m('SUBTRACT', ck["front"], d)                           # >0 behind the front
    behind = nb.m('GREATER_THAN', x, 0.0)
    xb = nb.m('MAXIMUM', x, 0.0)
    head = nb.m('MULTIPLY', nb.m('EXPONENT', nb.m('DIVIDE', xb, -7.0)), ck["gain"])
    tr = nb.m('SUBTRACT', ck["trail"], nb.m('ADD', nb.m('MULTIPLY', cooling(nb, ck), DV), nb.m('MULTIPLY', ck["drift"], 0.03)))
    hot = nb.m('ADD', tr, nb.m('MULTIPLY', head, nb.m('SUBTRACT', 1.15, tr)))
    pre = nb.m('MULTIPLY', nb.m('EXPONENT', nb.m('DIVIDE', nb.m('MINIMUM', x, 0.0), 2.5)), 0.85)
    pre = nb.m('MULTIPLY', nb.m('MULTIPLY', pre, ck["gain"]), ck["headvis"])
    pre = nb.m('MULTIPLY', pre, nb.m('SUBTRACT', 1.0, behind))      # glow only ahead of the front
    cold = nb.m('ADD', 0.115, pre)
    m = nb.attr("m")
    behind = nb.m('MULTIPLY', behind, m)                            # side tributaries: no front
    cold = nb.m('ADD', cold, nb.m('MULTIPLY', nb.m('MULTIPLY', nb.m('SUBTRACT', 1.0, m), ck["warm"]),
                                  nb.m('SUBTRACT', tr, 0.115)))   # ...they just warm with the organ
    H = nb.m('ADD', nb.m('MULTIPLY', behind, hot), nb.m('MULTIPLY', nb.m('SUBTRACT', 1.0, behind), cold))
    H = nb.m('ADD', H, spot_heat(nb, ck, 9.0))
    sh, spec = shading(nb)
    # glossy tube: heat * shading, a little subtractive darkening at the limb, plus spec
    val = nb.m('ADD', nb.m('MULTIPLY', H, nb.m('ADD', 0.55, nb.m('MULTIPLY', sh, 0.45))),
               nb.m('MULTIPLY', nb.m('MULTIPLY', spec, H), 0.22))
    out_emission(nb, val)
    return mat

def mat_ghost():
    mat = bpy.data.materials.new("M_ghost_veins"); nb = NB(mat); ck = nb.clock()
    g = nb.m('SUBTRACT', ck["ghost"], nb.m('MULTIPLY', cooling(nb, ck), DV * 0.85))
    H = nb.m('ADD', g, spot_heat(nb, ck, 9.0))
    sh, spec = shading(nb)
    val = nb.m('ADD', nb.m('MULTIPLY', H, nb.m('ADD', 0.5, nb.m('MULTIPLY', sh, 0.5))), nb.m('MULTIPLY', spec, 0.05))
    # fade in with the organ so the opening close-up stays about the one vessel
    vis = nb.m('ADD', 0.12, nb.m('MULTIPLY', ck["paren"], 2.0), clamp=True)
    out_emission(nb, nb.m('MULTIPLY', val, vis))
    return mat

def mat_paren():
    mat = bpy.data.materials.new("M_parenchyma"); nb = NB(mat); ck = nb.clock()
    mat.surface_render_method = 'BLENDED'; mat.use_backface_culling = True
    dp = nb.attr("dp")
    rev = nb.m('MINIMUM', nb.m('MAXIMUM', nb.m('DIVIDE', nb.m('SUBTRACT', ck["pfront"], dp), 35.0), 0.0), 1.0)
    lw = nb.node("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
    rim = nb.m('POWER', lw.outputs["Facing"], 2.2)
    base = nb.m('SUBTRACT', ck["paren"], nb.m('ADD', nb.m('MULTIPLY', cooling(nb, ck), DF), nb.m('MULTIPLY', ck["drift"], 0.03)))
    base = nb.m('MULTIPLY', base, nb.m('MINIMUM', nb.m('MULTIPLY', ck["paren"], 20.0), 1.0))   # keep 0 before reveal
    lvl = nb.m('ADD', base, nb.m('MULTIPLY', spot_heat(nb, ck, 22.0), 0.35))
    geom = nb.node("ShaderNodeNewGeometry")
    dot = nb.node("ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nb.link(geom.outputs["Normal"], dot.inputs[0]); dot.inputs[1].default_value = (-0.35, -0.55, 0.76)
    lam = nb.m('MULTIPLY', nb.m('ADD', dot.outputs["Value"], 1.0), 0.5)
    # own pass (max-composited with the vessel pass in grade.py), so it can be opaque:
    # a soft form term + brighter rim; banding turns it into contour lines.
    core = nb.m('POWER', nb.m('SUBTRACT', 1.0, lw.outputs["Facing"]), 0.7)
    val = nb.m('MULTIPLY', lvl, nb.m('ADD', 0.66, nb.m('ADD', nb.m('MULTIPLY', core, 0.30), nb.m('MULTIPLY', lam, 0.12))))
    out_emission(nb, val, rev)
    return mat

def mat_halo(i):
    mat = bpy.data.materials.new("M_halo%d" % i); nb = NB(mat); ck = nb.clock()
    # own pass (max-composited), so plain opaque emission; soft falloff from the facing term
    lw = nb.node("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    core = nb.m('POWER', nb.m('SUBTRACT', 1.0, lw.outputs["Facing"]), 3.0)
    out_emission(nb, nb.m('MULTIPLY', nb.m('MULTIPLY', core, ck["spot%d" % i]), 1.5))
    return mat

def assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m)

assign(pv, mat_portal())
gm = mat_ghost(); assign(hv, gm)
assign(liver, mat_paren())
for i, p in enumerate(SPOTS):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=9.5, location=tuple(p), segments=48, ring_count=24)
    h = bpy.context.active_object; h.name = "spot_halo%d" % i
    for pg in h.data.polygons: pg.use_smooth = True
    assign(h, mat_halo(i))

# ----------------------------------------------------------------------------- keys
def key_value(name, arr):
    node = CLOCK.nodes[name]
    for fr in range(NF):
        node.outputs[0].default_value = float(arr[fr])
        node.outputs[0].keyframe_insert("default_value", frame=fr)

for i, L in enumerate(LOSSES): key_value("age%d" % i, f - L)
for n, arr in (("front", FRONT), ("gain", gain), ("headvis", head_vis), ("trail", trail),
               ("paren", paren_level), ("pfront", paren_front), ("ghost", ghost), ("drift", drift), ("warm", warm)):
    key_value(n, arr)
for i in range(4): key_value("spot%d" % i, spot[i])

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d)
bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
cam_d.lens = 40.0; cam_d.sensor_width = 36.0; cam_d.clip_start = 0.5; cam_d.clip_end = 5000
cam_d.dof.use_dof = True
cam.rotation_mode = 'QUATERNION'
prevq = None
FSTOP = np.exp(np.log(2.2) * (1 - wz) + np.log(9.0) * wz)
for fr in range(NF):
    loc = Vector(CAM[fr]); look = Vector(T[fr]) - loc
    q = look.to_track_quat('-Z', 'Y')
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = loc; cam.rotation_quaternion = q
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_quaternion", frame=fr)
    cam_d.shift_x = float(SHIFT_X[fr]); cam_d.keyframe_insert("shift_x", frame=fr)
    cam_d.dof.focus_distance = float(look.length); cam_d.dof.keyframe_insert("focus_distance", frame=fr)
    cam_d.dof.aperture_fstop = float(FSTOP[fr]); cam_d.dof.keyframe_insert("aperture_fstop", frame=fr)

for a in [CLOCK.animation_data, cam.animation_data, cam_d.animation_data]:
    if a and a.action:
        try:
            for fc in a.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        except AttributeError:  # 5.x layered actions
            for layer in a.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# two passes, max-composited in grade.py (MIP / angiogram logic): V = vessels, P = parenchyma
scn = bpy.context.scene
cV = bpy.data.collections.new("VES"); cP = bpy.data.collections.new("PAR")
cS = bpy.data.collections.new("SPOT")
scn.collection.children.link(cV); scn.collection.children.link(cP); scn.collection.children.link(cS)
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    for c in list(o.users_collection): c.objects.unlink(o)
    (cP if o is liver else cS if o.name.startswith("spot_halo") else cV).objects.link(o)
vlV = scn.view_layers[0]; vlV.name = "V"



# ----------------------------------------------------------------------------- render setup
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.001   # 1 BU = 1 mm (for DOF)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = NF - 1
sc.eevee.taa_render_samples = 48
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.film_transparent = False
w_ = bpy.data.worlds.new("W"); sc.world = w_; w_.use_nodes = True
w_.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'BW'; sc.render.image_settings.color_depth = '16'
sc.render.resolution_x, sc.render.resolution_y = 960, 540

meta = dict(C0=C0.tolist(), D_HILUM=float(D_HILUM), D_MAX=D_MAX, HILUM=HILUM.tolist(),
            SPOTS=[p.tolist() for p in SPOTS], hits=HITS, losses=LOSSES, bpm=RATES_BPM)
json.dump(meta, open(os.path.join(HERE, "scene_meta.json"), "w"), indent=1)
np.savez(os.path.join(HERE, "timeline_debug.npz"), front=FRONT, gain=gain, life=life, trail=trail,
         paren=paren_level, spot=spot, cam=CAM, target=T, r=r, w=w)
bpy.ops.wm.save_as_mainfile(filepath=SAVE)
print("saved", SAVE, "%.1fs" % (time.time() - t0))
