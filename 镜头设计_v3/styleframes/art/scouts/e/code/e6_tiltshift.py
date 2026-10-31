"""HKBU SCIE1007 coursework science video. Style scout e6: tilt-shift miniature.

The real CDK20 surface is a mountain in a model-railway town: forest where pLDDT is high, bare rock on the real
low-confidence tail. Thousands of tiny houses, trees, cars. Real depth of field from a steep macro view.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import WORK, load_surface, rot, vertex_normals

sc = reset(1280, 720, samples=96, bounces=5)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.1 @ rot(-74, 0, 18).T
v *= 1.8
v[:, 2] *= 0.86
v[:, 2] -= v[:, 2].min() + 0.9        # sink the foot into the ground so it reads as a hill
nrm = vertex_normals(v, q)
hill = add_mesh("hill", v, q)
add_attr(hill, "conf", conf)

hm, hp = principled("hill", (0.2, 0.35, 0.1), 0.9)
t = hm.node_tree
at = t.nodes.new("ShaderNodeAttribute"); at.attribute_name = "conf"
r = t.nodes.new("ShaderNodeValToRGB")
e = r.color_ramp.elements
e[0].position = 0.60; e[0].color = (0.46, 0.31, 0.21, 1)
e[1].position = 0.74; e[1].color = (0.10, 0.28, 0.05, 1)
t.links.new(at.outputs["Fac"], r.inputs[0])
t.links.new(r.outputs[0], hp.inputs["Base Color"])
hill.data.materials.append(hm)

rng = np.random.default_rng(8)
GZ = 0.0


def boxes(cent, size, rotz, col, name):
    """Merged boxes: cent N x 3 (base centre), size N x 3, rotz N."""
    n = len(cent)
    cn = np.array([[-.5, -.5, 0], [.5, -.5, 0], [.5, .5, 0], [-.5, .5, 0], [-.5, -.5, 1], [.5, -.5, 1], [.5, .5, 1], [-.5, .5, 1]], np.float32)
    fa = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    p = cn[None] * size[:, None, :]
    cs, sn = np.cos(rotz)[:, None], np.sin(rotz)[:, None]
    x = p[..., 0] * cs - p[..., 1] * sn
    y = p[..., 0] * sn + p[..., 1] * cs
    vv = np.stack([x, y, p[..., 2]], -1) + cent[:, None, :]
    qq = (fa[None] + 8 * np.arange(n)[:, None, None]).reshape(-1, 4)
    ob = add_mesh(name, vv.reshape(-1, 3), qq, smooth=False)
    a = ob.data.color_attributes.new("col", "BYTE_COLOR", "POINT")
    a.data.foreach_set("color", np.repeat(np.c_[col, np.ones(n)], 8, 0).ravel())
    return ob


def roofs(cent, size, rotz, col, name):
    n = len(cent)
    cn = np.array([[-.55, -.55, 0], [.55, -.55, 0], [.55, .55, 0], [-.55, .55, 0], [-.55, 0, .55], [.55, 0, .55]], np.float32)
    fa = np.array([[0, 1, 5, 4], [2, 3, 4, 5], [3, 0, 4, 4], [1, 2, 5, 5]])
    p = cn[None] * size[:, None, :]
    cs, sn = np.cos(rotz)[:, None], np.sin(rotz)[:, None]
    x = p[..., 0] * cs - p[..., 1] * sn
    y = p[..., 0] * sn + p[..., 1] * cs
    vv = np.stack([x, y, p[..., 2]], -1) + cent[:, None, :]
    qq = (fa[None] + 6 * np.arange(n)[:, None, None]).reshape(-1, 4)
    ob = add_mesh(name, vv.reshape(-1, 3), qq, smooth=False)
    a = ob.data.color_attributes.new("col", "BYTE_COLOR", "POINT")
    a.data.foreach_set("color", np.repeat(np.c_[col, np.ones(n)], 6, 0).ravel())
    return ob


# ground footprint of the hill from the surface
hx, hy = v[:, 0], v[:, 1]
mn, mx = np.array([-26.0, -19.0]), np.array([26.0, 22.0])
fp_res = 0.2
gi = ((v[:, :2] - mn) / fp_res).astype(int)
dims = ((mx - mn) / fp_res).astype(int) + 1
keep = (gi >= 0).all(1) & (gi < dims).all(1)
foot = np.zeros(dims, bool)
foot[gi[keep, 0], gi[keep, 1]] = True
for _ in range(1):
    foot = foot | np.roll(foot, 1, 0) | np.roll(foot, -1, 0) | np.roll(foot, 1, 1) | np.roll(foot, -1, 1)


def on_foot(p):
    i = ((p[:, :2] - mn) / fp_res).astype(int)
    i = np.clip(i, 0, dims - 1)
    return foot[i[:, 0], i[:, 1]]


# Street grid: blocks of houses in tidy rows, roads between, a ring road hugging the foot
cols_wall = np.array([[.93, .88, .78], [.85, .55, .35], [.95, .80, .55], [.75, .80, .85], [.90, .35, .25], [.97, .95, .90]], np.float32)
cols_roof = np.array([[.70, .15, .08], [.25, .25, .30], [.55, .22, .10], [.15, .30, .50]], np.float32)
BX, BY = 2.6, 2.0
cents, sizes, rots, walls, rf = [], [], [], [], []
for gx in np.arange(-26, 26, BX):
    for gy in np.arange(-19, 22, BY):
        n = 8
        lx = np.linspace(-1.0, 1.0, n)
        for row in (-0.42, 0.42):
            pp = np.c_[gx + lx + 0.0, np.full(n, gy + row), np.zeros(n)]
            cents.append(pp)
            sizes.append(np.c_[rng.uniform(.17, .25, n), rng.uniform(.27, .34, n), rng.uniform(.14, .34, n)])
            rots.append(np.zeros(n))
            walls.append(cols_wall[rng.integers(0, len(cols_wall), n)])
            rf.append(cols_roof[rng.integers(0, len(cols_roof), n)])
cents = np.concatenate(cents).astype(np.float32); sizes = np.concatenate(sizes).astype(np.float32)
rots = np.concatenate(rots).astype(np.float32); walls = np.concatenate(walls); rf = np.concatenate(rf)
m_ok = ~on_foot(cents)
cents, sizes, rots, walls, rf = cents[m_ok], sizes[m_ok], rots[m_ok], walls[m_ok], rf[m_ok]
print("houses", len(cents))
boxes(cents, sizes, rots, walls, "houses")
top = cents.copy(); top[:, 2] += sizes[:, 2]
roofs(top, sizes * np.array([1, 1, 0.7]), rots, rf, "roofs")

# trees: clusters of small balls on the hill where pLDDT is high and the slope faces up, and along streets
sel = (conf > 0.70) & (nrm[:, 2] > -0.1) & (v[:, 2] > 0.02)
idx = rng.choice(np.nonzero(sel)[0], 60000, replace=False)
tp = v[idx] + nrm[idx] * 0.03
s = rng.uniform(.05, .10, len(tp))
g_col = np.array([[.05, .27, .05], [.10, .36, .06], [.20, .42, .07], [.04, .20, .07], [.32, .46, .10]], np.float32)
tc = g_col[rng.integers(0, 5, len(tp))]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
ic = bpy.context.object
nv = len(ic.data.vertices)
iv = np.zeros(nv * 3, np.float32); ic.data.vertices.foreach_get("co", iv); iv = iv.reshape(-1, 3)
nf = len(ic.data.polygons)
ifc = np.zeros(nf * 3, np.int32); ic.data.polygons.foreach_get("vertices", ifc); ifc = ifc.reshape(-1, 3)
bpy.data.objects.remove(ic)
vv = (iv[None] * (s[:, None, None] * np.array([1, 1, 1.45]))) + tp[:, None, :] + np.array([0, 0, 0.03])
ff = (ifc[None] + nv * np.arange(len(tp))[:, None, None]).reshape(-1, 3)
tree = add_mesh("trees", vv.reshape(-1, 3), ff, tris=True, smooth=True)
a = tree.data.color_attributes.new("col", "BYTE_COLOR", "POINT")
a.data.foreach_set("color", np.repeat(np.c_[tc, np.ones(len(tc))], nv, 0).ravel())

# Cars: yellow and red dots along the roads
xr = np.arange(-26, 26, BX) + BX / 2
nc = 620
cx = rng.choice(xr, nc) + rng.choice([-.06, .06], nc)
cy = rng.uniform(-19, 22, nc)
cp = np.c_[cx, cy, np.zeros(nc)].astype(np.float32)
cp = cp[~on_foot(cp)]
n2 = len(cp)
cc = np.array([[.95, .75, .05], [.85, .10, .08], [.95, .95, .95], [.10, .25, .55]], np.float32)[rng.integers(0, 4, n2)]
boxes(cp, np.tile([.075, .17, .075], (n2, 1)).astype(np.float32), np.zeros(n2, np.float32), cc, "cars")

vm, vp = principled("vc", rough=0.6)
vc = vm.node_tree.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "col"
vm.node_tree.links.new(vc.outputs[0], vp.inputs["Base Color"])
for o in bpy.data.objects:
    if o.type == "MESH" and o.name != "hill":
        o.data.materials.append(vm)

# Ground: asphalt with a grass grid drawn by a brick texture, each block a green with road lines
gv = np.array([[-120, -120, 0], [120, -120, 0], [120, 120, 0], [-120, 120, 0]], np.float32)
g = add_mesh("ground", gv, np.array([[0, 1, 2, 3]]), smooth=False)
gm, gp = principled("g", (0.2, 0.2, 0.2), 0.9)
gt = gm.node_tree
geo = gt.nodes.new("ShaderNodeNewGeometry")
br = gt.nodes.new("ShaderNodeTexBrick")
br.inputs["Color1"].default_value = (0.25, 0.38, 0.12, 1)
br.inputs["Color2"].default_value = (0.32, 0.42, 0.14, 1)
br.inputs["Mortar"].default_value = (0.10, 0.10, 0.11, 1)
br.inputs["Scale"].default_value = 1.0
br.inputs["Mortar Size"].default_value = 0.11
br.inputs["Mortar Smooth"].default_value = 0.0
br.inputs["Brick Width"].default_value = BX
br.inputs["Row Height"].default_value = BY
br.offset = 0.0
br.squash = 1.0
gt.links.new(geo.outputs["Position"], br.inputs["Vector"])
gt.links.new(br.outputs[0], gp.inputs["Base Color"])
g.data.materials.append(gm)

# Hillside sign: white letters planted on the slope, a billboard you would see from every street in town
for i, ch in enumerate("CDK20"):
    tx = text3d(ch, "ariblk.ttf", size=2.9, extrude=0.18)
    wm, wp = principled("w", (0.97, 0.96, 0.92), 0.45)
    tx.data.materials.append(wm)
    x = -6.3 + i * 2.65
    tx.location = (x, -8.7 - 0.25 * (i - 2) ** 2 * 0.2, 1.05)
    tx.rotation_euler = (np.radians(90 - 22), 0, np.radians((2 - i) * -3))

world_rgb((0.75, 0.86, 1.0), 1.0)
sun((58, 0, -52), 3.6, (1.0, 0.93, 0.82), 2.0)
cam_loc = np.array([-9.0, -50.0, 34.0]); tgt = np.array([0.2, -3.2, 2.0]); foc = np.array([0.0, -8.7, 2.0])
camera(tuple(cam_loc), tuple(tgt), lens=85, dof=float(np.linalg.norm(cam_loc - foc)), fstop=0.028)
sc.view_settings.look = "None"
print(render(sc, "e6_tiltshift"))
