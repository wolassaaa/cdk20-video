"""HKBU SCIE1007 coursework science video. Style scout e2: destructible voxel world.

The real CDK20 surface voxelised at 0.1 nm-ish steps into a building-sized block world. Low pLDDT voxels (the real
tail) are the ones that have been blown loose: pLDDT alone picks what falls. Real exposed faces only, ray traced.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import WORK
from common import load_surface, rot

sc = reset(1280, 720, samples=96)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) @ rot(-68, 0, 24).T
vox = 0.72  # Angstrom per voxel: big enough to read as blocks, small enough to keep every lump of the surface

# Voxelise by marking shell cells from the dense surface, then flood the outside to get solid
mn = v.min(0) - 4
ijk = ((v - mn) / vox).astype(np.int32)
dims = ijk.max(0) + 4
shell = np.zeros(dims, bool)
cf = np.zeros(dims, np.float32)
cnt = np.zeros(dims, np.float32)
shell[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
np.add.at(cf, (ijk[:, 0], ijk[:, 1], ijk[:, 2]), conf)
np.add.at(cnt, (ijk[:, 0], ijk[:, 1], ijk[:, 2]), 1)
cf = cf / np.maximum(cnt, 1)
out = np.zeros(dims, bool)
out[0, :, :] = True
for _ in range(240):
    grown = out.copy()
    grown[1:] |= out[:-1]; grown[:-1] |= out[1:]
    grown[:, 1:] |= out[:, :-1]; grown[:, :-1] |= out[:, 1:]
    grown[:, :, 1:] |= out[:, :, :-1]; grown[:, :, :-1] |= out[:, :, 1:]
    grown &= ~shell
    if grown.sum() == out.sum():
        break
    out = grown
solid = ~out
print("voxels", solid.sum())

# carry pLDDT to interior voxels by a few blur passes
cfs = cf.copy()
wt = (cnt > 0).astype(np.float32)
for _ in range(8):
    a = cfs * wt
    a2 = a.copy(); w2 = wt.copy()
    for ax in range(3):
        a2 += np.roll(a, 1, ax) + np.roll(a, -1, ax)
        w2 += np.roll(wt, 1, ax) + np.roll(wt, -1, ax)
    m = wt == 0
    cfs = np.where(m, a2 / np.maximum(w2, 1e-5), cfs)
    wt = np.where(m & (w2 > 0), 1.0, wt)

rng = np.random.default_rng(3)
idx = np.argwhere(solid)
cc = cfs[idx[:, 0], idx[:, 1], idx[:, 2]]

# Blast sphere: a crater in the low confidence side, only voxels with pLDDT < 0.70 may leave
low = cc < 0.70
pos = (idx + 0.5) * vox + mn
blast = pos[low].mean(0) if low.any() else pos.mean(0)
drop = low & (rng.random(len(idx)) < 0.86)
keep = ~drop

GROUND = pos[:, 2].min() - 1.0


def faces_for(cells, colors, name, size=vox):
    """Merged cube mesh from cell centres."""
    n = len(cells)
    corners = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], np.float32) - 0.5
    fa = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    verts = (cells[:, None, :] + corners[None] * size).reshape(-1, 3)
    quads = (fa[None] + 8 * np.arange(n)[:, None, None]).reshape(-1, 4)
    ob = add_mesh(name, verts, quads, smooth=False)
    a = ob.data.color_attributes.new("col", "BYTE_COLOR", "POINT")
    al = np.ones(n) if colors.shape[1] == 3 else colors[:, 3]
    a.data.foreach_set("color", np.repeat(np.c_[colors[:, :3], al], 8, 0).ravel())
    return ob


# surface only: skip fully buried voxels to save geometry
sg = np.zeros(dims, bool)
sg[idx[keep, 0], idx[keep, 1], idx[keep, 2]] = True
buried = sg.copy()
for ax in range(3):
    buried &= np.roll(sg, 1, ax) & np.roll(sg, -1, ax)
show = keep & ~buried[idx[:, 0], idx[:, 1], idx[:, 2]]

# colour: concrete brick and rust palette with per voxel noise; pLDDT sets the band
base_hi = np.array([0.50, 0.50, 0.52], np.float32)
base_mid = np.array([0.46, 0.09, 0.05], np.float32)
base_low = np.array([0.95, 0.55, 0.10], np.float32)
t = np.clip((cc - 0.70) / 0.2, 0, 1)[:, None]
col = base_mid * (1 - t) + base_hi * t
col = np.where((cc < 0.72)[:, None], base_low, col)
col *= (0.55 + 0.75 * rng.random((len(idx), 1)))
# interior cut faces glow like heated metal around the crater
dist = np.linalg.norm(pos - blast, axis=1)
heat = np.clip(1 - dist / 12, 0, 1)[:, None] ** 2
col = col * (1 - heat) + np.array([1.0, 0.25, 0.03]) * heat

col = np.c_[col, 1 - heat[:, 0]]
ob = faces_for(pos[show], col[show], "world")

# debris: dropped voxels thrown out on ballistic arcs, clumped in small chunks, plus a rubble heap at the foot
dp = pos[drop]
n = len(dp)
print("debris", n)
take = rng.random(n) < 0.34
air = dp[take].copy()
dirn = air - blast
dirn /= np.maximum(np.linalg.norm(dirn, axis=1, keepdims=True), 1e-5)
sp = rng.random(len(air))[:, None] ** 1.6
air = air + dirn * sp * 70 + np.array([26, -6, 8], np.float32) * sp
air[:, 2] -= (sp[:, 0] ** 2) * 34
air[:, 2] = np.maximum(air[:, 2], GROUND + 0.5)
air_col = col[drop][take]
rub = dp[~take].copy()
rub[:, :2] += rng.normal(0, 1, (len(rub), 2)) * np.array([26, 18]) + np.array([8, -14])
rub[:, 2] = GROUND + vox * (0.5 + np.floor(np.abs(rng.normal(0, 1, len(rub))) * 2.4))
rub = np.round(rub / vox) * vox
faces_for(air, air_col, "air", size=vox * 0.92)
faces_for(rub, col[drop][~take], "rubble", size=vox)

# title: voxel letters big as a block of flats, standing in the rubble, one corner shot off
mask = np.load(WORK / "mask_ariblk_26.npy")
my, mx = np.nonzero(mask[::-1] > 0.5)
lv = vox
cells = []
cols = []
for k in range(10):
    drop_k = rng.random(len(mx)) < (0.012 + 0.02 * (k > 6) + 0.3 * (k > 8))
    xx = mx[~drop_k] * lv - mask.shape[1] * lv / 2 - 18
    zz = my[~drop_k] * lv + GROUND + lv * 0.5
    yy = np.full(len(xx), -46.0 - k * lv)
    cells.append(np.c_[xx, yy, zz]); cols.append(np.tile([0.98, 0.93, 0.74], (len(xx), 1)))
cells = np.concatenate(cells); cols = np.concatenate(cols) * (0.8 + 0.3 * rng.random((len(cells), 1)))
faces_for(cells, cols, "title", size=lv)

m, p = principled("vox", rough=0.85)
at = m.node_tree.nodes.new("ShaderNodeVertexColor")
at.layer_name = "col"
m.node_tree.links.new(at.outputs[0], p.inputs["Base Color"])
m.node_tree.links.new(at.outputs[0], p.inputs["Emission Color"])
inv = m.node_tree.nodes.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"
inv.inputs[1].default_value = -22.0; inv.inputs[2].default_value = 22.0
m.node_tree.links.new(at.outputs["Alpha"], inv.inputs[0])
m.node_tree.links.new(inv.outputs[0], p.inputs["Emission Strength"])
p.inputs["Specular IOR Level"].default_value = 0.15
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.materials.append(m)

# dirt ground
gv = np.array([[-900, -900, GROUND], [900, -900, GROUND], [900, 900, GROUND], [-900, 900, GROUND]], np.float32)
g = add_mesh("ground", gv, np.array([[0, 1, 2, 3]]), smooth=False)
gm, gp = principled("dirt", (0.16, 0.13, 0.11), 0.95)
g.data.materials.append(gm)

# golden hour with thick ground haze, the world's only light
w = world_rgb((0.05, 0.10, 0.34), 1.0)
s = sun((76, 0, -70), 9.0, (1.0, 0.52, 0.22), 1.0)
# hazy volume cube
hv = bpy.data.materials.new("haze")
hv.use_nodes = True
nt = hv.node_tree
nt.nodes.clear()
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.0003
pv.inputs["Color"].default_value = (1.0, 0.72, 0.5, 1)
pv.inputs["Anisotropy"].default_value = 0.55
o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(pv.outputs[0], o.inputs["Volume"])
bv = np.array([[x, y, z] for z in (GROUND - 1, 220) for x, y in ((-500, -400), (500, -400), (500, 700), (-500, 700))], np.float32)
bq = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
b = add_mesh("hazebox", bv, bq, smooth=False)
b.data.materials.append(hv)
sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 4

camera((-44, -176, GROUND + 7), (-3, 0, GROUND + 31), lens=46)
# a heavier camera exposure for the sunset
sc.view_settings.exposure = 0.0
print(render(sc, "e2_voxel"))
