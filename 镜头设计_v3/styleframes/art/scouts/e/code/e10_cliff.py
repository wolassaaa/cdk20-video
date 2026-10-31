"""HKBU SCIE1007 coursework science video. Style scout e10: photoreal cliff, engine tech demo.

The real CDK20 surface is the mountain. Its big forms are untouched; strata, cracks and scree are added on top only.
A human figure at the foot gives the scale. Real displacement, sun and sky, depth fog added from the Z pass.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import load_surface, rot, vertex_normals

sc = reset(1280, 720, samples=80, bounces=4)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.1 @ rot(-90, 0, 196).T          # long axis stood up, the face with the deep cleft to the camera
v[:, 2] -= v[:, 2].min()
v *= np.array([1.5, 1.0, 1.7], np.float32)
v[:, 2] -= 1.6
v *= 10                                         # 1 unit is about 2 metres of cliff now
ob = add_mesh("cliff", v, q)
print("z", v[:, 2].min(), v[:, 2].max(), v[:, 0].min(), v[:, 0].max())
sub = ob.modifiers.new("s", "SUBSURF")
sub.subdivision_type = "SIMPLE"
sub.levels = sub.render_levels = 1

M = bpy.data.materials.new("rock")
M.use_nodes = True
M.displacement_method = "BOTH"
nt = M.node_tree
P = nt.nodes["Principled BSDF"]
O = nt.nodes["Material Output"]
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])


def N(cls):
    return nt.nodes.new(cls)


def math(op, a=None, b=None):
    m = N("ShaderNodeMath"); m.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            nt.links.new(x, m.inputs[i])
    return m.outputs[0]


# Strata: horizontal bands warped by low noise
warp = N("ShaderNodeTexNoise")
warp.inputs["Scale"].default_value = 0.022; warp.inputs["Detail"].default_value = 3
nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
zw = math("ADD", sep.outputs["Z"], math("MULTIPLY", warp.outputs[0], 30.0))
strata = math("ABSOLUTE", math("SINE", math("MULTIPLY", zw, 0.33)))
strata2 = math("ABSOLUTE", math("SINE", math("MULTIPLY", zw, 1.4)))
bands = math("ADD", math("MULTIPLY", math("POWER", strata, 0.35), 2.6), math("MULTIPLY", strata2, 0.8))

# Blocky fracture
vor = N("ShaderNodeTexVoronoi")
vor.feature = "DISTANCE_TO_EDGE"
vor.inputs["Scale"].default_value = 0.30
mp_v = N("ShaderNodeMapping")
mp_v.inputs["Scale"].default_value = (0.55, 0.55, 2.1)
nt.links.new(tc.outputs["Object"], mp_v.inputs[0])
nt.links.new(mp_v.outputs[0], vor.inputs["Vector"])
crack = math("MULTIPLY", math("MINIMUM", math("MULTIPLY", vor.outputs["Distance"], 7.0), 1.0), 2.0)
vor2 = N("ShaderNodeTexVoronoi")
vor2.feature = "DISTANCE_TO_EDGE"
vor2.inputs["Scale"].default_value = 1.2
nt.links.new(mp_v.outputs[0], vor2.inputs["Vector"])
crack2 = math("MULTIPLY", math("MINIMUM", math("MULTIPLY", vor2.outputs["Distance"], 6.0), 1.0), 0.9)

# Fine fbm
fb = N("ShaderNodeTexNoise")
fb.inputs["Scale"].default_value = 0.8; fb.inputs["Detail"].default_value = 11; fb.inputs["Roughness"].default_value = 0.62
nt.links.new(tc.outputs["Object"], fb.inputs["Vector"])
fine = math("MULTIPLY", fb.outputs[0], 3.0)
h = math("ADD", math("ADD", bands, crack), math("ADD", crack2, fine))

dsp = N("ShaderNodeDisplacement")
dsp.inputs["Scale"].default_value = 0.30
dsp.inputs["Midlevel"].default_value = 5.6
nt.links.new(h, dsp.inputs["Height"])
nt.links.new(dsp.outputs[0], O.inputs["Displacement"])

# Colour: warm limestone, darker in cracks, thin blue-grey in strata, moss only on ledges facing up
col = N("ShaderNodeValToRGB")
e = col.color_ramp.elements
e[0].position = 0.34; e[0].color = (0.10, 0.075, 0.06, 1)
e[1].position = 0.70; e[1].color = (0.62, 0.50, 0.38, 1)
ee = col.color_ramp.elements.new(0.52); ee.color = (0.30, 0.235, 0.18, 1)
hh = math("DIVIDE", h, 8.0)
nt.links.new(hh, col.inputs[0])
geo = N("ShaderNodeNewGeometry")
sn = N("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], sn.inputs[0])
up = math("GREATER_THAN", math("ADD", sn.outputs["Z"], math("MULTIPLY", fb.outputs[0], 0.4)), 0.86)
mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
mix.inputs["B"].default_value = (0.07, 0.12, 0.035, 1)
nt.links.new(up, mix.inputs[0])
nt.links.new(col.outputs[0], mix.inputs["A"])
nt.links.new(mix.outputs["Result"], P.inputs["Base Color"])
P.inputs["Roughness"].default_value = 0.82
ob.data.materials.append(M)

# Terrain and scree: a big displaced plane and thousands of real boulders
gr = 400
xs = np.linspace(-500, 500, gr)
ys = np.linspace(-500, 600, gr)
X, Y = np.meshgrid(xs, ys)
rng = np.random.default_rng(2)
WAVES = [(f, a, *rng.uniform(0, 7, 2)) for f, a in ((0.008, 4.0), (0.021, 1.6), (0.06, 0.5))]


def height(x, y):
    z = -3.0
    for f, a, px, py in WAVES:
        z = z + a * np.sin(x * f + px + np.sin(y * f * 0.7) * 1.3) * np.sin(y * f * 0.8 + py + np.sin(x * f * 0.6))
    return z


Z = height(X, Y)
Vt = np.c_[X.ravel(), Y.ravel(), Z.ravel()].astype(np.float32)
ii = np.arange(gr * gr).reshape(gr, gr)
Qt = np.c_[ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()]
ter = add_mesh("terrain", Vt, Qt)
M2 = M.copy()
M2.displacement_method = "BUMP"
ter.data.materials.append(M2)

# Boulders: squashed noisy spheres at the foot of the wall
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
ic = bpy.context.object
nv = len(ic.data.vertices)
iv = np.zeros(nv * 3, np.float32); ic.data.vertices.foreach_get("co", iv); iv = iv.reshape(-1, 3)
nf = len(ic.data.polygons)
ifc = np.zeros(nf * 3, np.int32); ic.data.polygons.foreach_get("vertices", ifc); ifc = ifc.reshape(-1, 3)
bpy.data.objects.remove(ic)
NB = 5000
th = rng.uniform(0, 6.283, NB)
rr = rng.normal(0, 1, NB)
bx = rng.uniform(-260, 260, NB)
by = -40 + np.abs(rr) * -26 + rng.uniform(-5, 10, NB)
bz = height(bx, by) - 0.5
sz = np.minimum(np.exp(rng.normal(0.0, 0.75, NB)) * 1.2, 5.0)
FX, FY = -7.0, -47.0
bx[0], by[0], sz[0] = FX, FY, 5.0
bz[0] = height(FX, FY) + 0.5
far = (np.hypot(bx + 16, by + 70) > 16) & ((by > -54) | (sz < 1.5))
sz = np.where(far | (np.arange(NB) == 0), sz, 0.05)
d = 1 + 0.26 * np.sin(iv[:, 0:1] * 4 + 1) * np.cos(iv[:, 1:2] * 5)
base = iv * d
ax = rng.normal(size=(NB, 3)); ax /= np.linalg.norm(ax, axis=1, keepdims=True)
scl = rng.uniform(0.55, 1.1, (NB, 1, 3)); scl[0] = 1.0
vv = base[None] * (sz[:, None, None] * scl)
ca, sa = np.cos(th)[:, None], np.sin(th)[:, None]
xx = vv[..., 0] * ca - vv[..., 1] * sa
yy = vv[..., 0] * sa + vv[..., 1] * ca
pos = np.stack([xx + bx[:, None], yy + by[:, None], vv[..., 2] + bz[:, None]], -1)
ff = (ifc[None] + nv * np.arange(NB)[:, None, None]).reshape(-1, 3)
bo = add_mesh("boulders", pos.reshape(-1, 3), ff, tris=True)
bo.data.materials.append(M2)

# A person, for scale only: a plain dark standing silhouette on a boulder
pv = []
pf = []
fig, _ = principled("figure", (0.8, 0.02, 0.015), 0.6)
_tip = pos[0][np.argmax(pos[0][:, 2])]
FX, FY, FZ = float(_tip[0]), float(_tip[1]), float(_tip[2]) - 0.08
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.12, depth=0.75, location=(FX, FY, FZ + 0.38))
body = bpy.context.object
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.1, location=(FX, FY, FZ + 0.84))
head = bpy.context.object
body.data.materials.append(fig); head.data.materials.append(fig)

# Sky, sun, Z pass for aerial perspective
w = bpy.data.worlds.new("w")
w.use_nodes = True
tn = w.node_tree
sky = tn.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "MULTIPLE_SCATTERING"
except Exception:
    pass
try:
    sky.sun_disc = False
except Exception:
    pass
sky.sun_elevation = np.radians(8)
sky.sun_rotation = np.radians(95)
tn.links.new(sky.outputs[0], tn.nodes["Background"].inputs[0])
tn.nodes["Background"].inputs[1].default_value = 0.24
sc.world = w
sun((80, 0, -60), 6.5, (1.0, 0.62, 0.34), 1.0)

hv = bpy.data.materials.new("haze")
hv.use_nodes = True
nt2 = hv.node_tree
nt2.nodes.clear()
pv = nt2.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.0014
pv.inputs["Color"].default_value = (0.85, 0.72, 0.62, 1)
pv.inputs["Anisotropy"].default_value = 0.6
o2 = nt2.nodes.new("ShaderNodeOutputMaterial")
nt2.links.new(pv.outputs[0], o2.inputs["Volume"])
bv = np.array([[x, y, z] for z in (-40, 260) for x, y in ((-700, -300), (700, -300), (700, 900), (-700, 900))], np.float32)
bq = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
hb = add_mesh("hazebox", bv, bq, smooth=False)
hb.data.materials.append(hv)
sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 5
camera((-16.0, -70.0, float(height(-16.0, -70.0)) + 5.0), (3.0, 0.0, 37.0), lens=16, sensor=36)
print(render(sc, "e10_cliff"))
