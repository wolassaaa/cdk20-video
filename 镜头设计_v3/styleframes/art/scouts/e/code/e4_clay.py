"""HKBU SCIE1007 coursework science video. Style scout e4: clay stop motion.

One hand-rolled plasticine ball for each of the 346 real residues, placed at the real C-alpha positions, shoved
together on a tabletop set. Colour follows the real pLDDT: the low confidence tail is the unmixed white clay.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import load_ca, rot

sc = reset(1280, 720, samples=160, bounces=6)
ca, pl = load_ca()
c = (ca.min(0) + ca.max(0)) / 2
ca = (ca - c) * 0.1 @ rot(-72, 0, 200).T
rng = np.random.default_rng(11)

# icosphere template by subdividing
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1)
tmp = bpy.context.object
n = len(tmp.data.vertices)
tv = np.zeros(n * 3, np.float32)
tmp.data.vertices.foreach_get("co", tv)
tv = tv.reshape(-1, 3)
m = len(tmp.data.polygons)
tf = np.zeros(m * 3, np.int32)
tmp.data.polygons.foreach_get("vertices", tf)
tf = tf.reshape(-1, 3)
bpy.data.objects.remove(tmp)


def lump(pos, r, seed):
    g = np.random.default_rng(seed)
    a = g.normal(size=(6, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
    d = np.zeros(n, np.float32)
    for dirn in a:
        d += g.uniform(0.03, 0.10) * np.sin(g.uniform(2, 5) * (tv @ dirn) + g.uniform(0, 6))
    # a thumb press: flat dimple on one side
    th = g.normal(size=3); th /= np.linalg.norm(th)
    d -= 0.22 * np.clip((tv @ th - 0.72) / 0.28, 0, 1) ** 1.5
    s = g.uniform(0.92, 1.08, 3)
    return tv * (1 + d[:, None]) * s * r + pos


pal = np.array([
    [0.95, 0.27, 0.05],  # tomato
    [0.98, 0.56, 0.05],  # orange
    [0.98, 0.78, 0.12],  # yolk
    [0.05, 0.42, 0.42],  # teal
    [0.04, 0.20, 0.50],  # blue
    [0.72, 0.08, 0.20],  # crimson
], np.float32)
vs, fs, cols = [], [], []
hi = pl >= 0.70
v_min_z = ca[:, 2].min() - 0.55
for i, (p, b) in enumerate(zip(ca, pl)):
    r = rng.uniform(0.40, 0.56) if hi[i] else rng.uniform(0.30, 0.44)
    vs.append(lump(p, r, i))
    fs.append(tf + i * n)
    # runs of the same colour along the chain, like one rolled sausage being used up
    col = pal[(i // 23) % len(pal)] if hi[i] else np.array([0.92, 0.88, 0.80], np.float32)
    cols.append(np.tile(col * rng.uniform(0.92, 1.06), (n, 1)))
# scraps left on the mat by the person who made it
gs = np.random.default_rng(21)
for k in range(26):
    p0 = np.array([gs.uniform(-7, 6), gs.uniform(-6.5, 0), 0.0], np.float32)
    r0 = gs.uniform(0.05, 0.17)
    p0[2] = r0 * 0.7 - 2.9 - 0.0
    i0 = len(vs)
    p_local = p0 - np.array([1.4, 0.9, 0], np.float32)
    p_local[2] = v_min_z + r0 * 0.7
    vs.append(lump(p_local, r0, 900 + k))
    fs.append(tf + i0 * n)
    cols.append(np.tile(pal[gs.integers(0, len(pal))], (n, 1)))
v = np.concatenate(vs)
f = np.concatenate(fs)
col = np.concatenate(cols)
ob = add_mesh("clay", v, f, tris=True)
a = ob.data.color_attributes.new("col", "BYTE_COLOR", "POINT")
a.data.foreach_set("color", np.c_[col, np.ones(len(col))].ravel())
ob.location = (1.4, 0.9, -v_min_z - 0.08)

# Clay material: soft subsurface, fingerprints as curved ridges that come and go in patches
M = bpy.data.materials.new("clay")
M.use_nodes = True
nt = M.node_tree
P = nt.nodes["Principled BSDF"]
P.inputs["Roughness"].default_value = 0.46
P.inputs["Subsurface Weight"].default_value = 0.45
P.inputs["Subsurface Radius"].default_value = (0.25, 0.09, 0.05)
P.inputs["Subsurface Scale"].default_value = 0.18
P.inputs["Specular IOR Level"].default_value = 0.45
vc = nt.nodes.new("ShaderNodeVertexColor")
vc.layer_name = "col"
nt.links.new(vc.outputs[0], P.inputs["Base Color"])
tc = nt.nodes.new("ShaderNodeTexCoord")
wave = nt.nodes.new("ShaderNodeTexWave")
wave.wave_type = "RINGS"
wave.rings_direction = "SPHERICAL"
wave.inputs["Scale"].default_value = 6.5
wave.inputs["Distortion"].default_value = 5.0
wave.inputs["Detail"].default_value = 1.5
wave.inputs["Detail Scale"].default_value = 1.2
nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
patch = nt.nodes.new("ShaderNodeTexNoise")
patch.inputs["Scale"].default_value = 1.3
nt.links.new(tc.outputs["Object"], patch.inputs["Vector"])
rmp = nt.nodes.new("ShaderNodeMapRange")
rmp.inputs[1].default_value = 0.47; rmp.inputs[2].default_value = 0.58
nt.links.new(patch.outputs[0], rmp.inputs[0])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(wave.outputs[1], mul.inputs[0])
nt.links.new(rmp.outputs[0], mul.inputs[1])
fine = nt.nodes.new("ShaderNodeTexNoise")
fine.inputs["Scale"].default_value = 22
fine.inputs["Detail"].default_value = 6
nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
nt.links.new(mul.outputs[0], add.inputs[0])
nt.links.new(fine.outputs[0], add.inputs[1])
bp = nt.nodes.new("ShaderNodeBump")
bp.inputs["Strength"].default_value = 0.9
bp.inputs["Distance"].default_value = 0.022
nt.links.new(add.outputs[0], bp.inputs["Height"])
nt.links.new(bp.outputs[0], P.inputs["Normal"])
ob.data.materials.append(M)

# Letters: thick cut clay, lumpy, leaning on the pile. Same material through a solid colour.
tm, tp = principled("cream", (0.95, 0.90, 0.78), 0.5)
tp.inputs["Subsurface Weight"].default_value = 0.4
tp.inputs["Subsurface Radius"].default_value = (0.2, 0.1, 0.06)
tp.inputs["Subsurface Scale"].default_value = 0.15
# reuse the bump network
def bump_copy(mat, p):
    tree = mat.node_tree
    t = tree.nodes.new("ShaderNodeTexCoord")
    w = tree.nodes.new("ShaderNodeTexWave")
    w.wave_type = "RINGS"; w.rings_direction = "SPHERICAL"
    w.inputs["Scale"].default_value = 6.5
    w.inputs["Distortion"].default_value = 6
    tree.links.new(t.outputs["Object"], w.inputs["Vector"])
    nz = tree.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6
    tree.links.new(t.outputs["Object"], nz.inputs["Vector"])
    a2 = tree.nodes.new("ShaderNodeMath"); a2.operation = "ADD"
    tree.links.new(w.outputs[1], a2.inputs[0]); tree.links.new(nz.outputs[0], a2.inputs[1])
    b = tree.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.7; b.inputs["Distance"].default_value = 0.01
    tree.links.new(a2.outputs[0], b.inputs["Height"])
    tree.links.new(b.outputs[0], p.inputs["Normal"])


bump_copy(tm, tp)
xoff = -5.3
palt = [(0.95, 0.90, 0.78), (0.96, 0.30, 0.05), (0.97, 0.78, 0.10), (0.04, 0.42, 0.46), (0.95, 0.90, 0.78)]
for li, (ch, ang, dy, h) in enumerate(zip("CDK20", (6, -5, 4, -7, 5), (0.1, -0.05, 0.02, -0.1, 0.08), (1.95, 1.85, 2.0, 1.9, 1.95))):
    t = text3d(ch, "ariblk.ttf", size=h, extrude=0.26, bevel=0.07, bevel_res=2)
    t.rotation_euler = (np.radians(82), np.radians(ang), 0)
    t.location = (xoff + 0.55, -4.1 + dy, 0.60)
    xoff += 1.62
    tt = bpy.data.textures.new("n", "CLOUDS")
    tt.noise_scale = 0.32
    tt.noise_depth = 2
    remesh_smooth(t, voxel=0.018, smooth=6, factor=0.7)
    d = t.modifiers.new("d", "DISPLACE")
    d.texture, d.strength = tt, 0.05
    apply_mods(t)
    tl = tm.copy()
    tl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*palt[li], 1)
    t.data.materials.append(tl)
    t.data.polygons.foreach_set("use_smooth", np.ones(len(t.data.polygons), bool))
    t.data.update()

# Set: a seamless card swept up the wall, painted gouache sky, visibly hand made
sv = []
sq = []
res = 80
for i in range(res + 1):
    a = i / res
    y = -14 + a * 26
    z = 0.0 if y < 5 else ((y - 5) / 2.2) ** 2 * 2.2 * 0.7
    if y >= 7:
        z = (y - 6.1) * 2.1
    sv += [[-30, min(y, 8.5), z], [30, min(y, 8.5), z]]
for i in range(res):
    sq.append([i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2])
card = add_mesh("card", np.array(sv, np.float32), np.array(sq), smooth=True)
cm, cp = principled("card", (0.03, 0.17, 0.33), 0.62)
ctree = cm.node_tree
n1 = ctree.nodes.new("ShaderNodeTexNoise")
n1.inputs["Scale"].default_value = 2.4; n1.inputs["Detail"].default_value = 8; n1.inputs["Roughness"].default_value = 0.6
rmp2 = ctree.nodes.new("ShaderNodeValToRGB")
rmp2.color_ramp.elements[0].position = 0.35; rmp2.color_ramp.elements[0].color = (0.80, 0.36, 0.03, 1)
rmp2.color_ramp.elements[1].position = 0.68; rmp2.color_ramp.elements[1].color = (0.98, 0.58, 0.06, 1)
ctree.links.new(n1.outputs[0], rmp2.inputs[0])
# cutting mat on the table: green with a printed yellow grid, ends where the card sweeps up
geo = ctree.nodes.new("ShaderNodeNewGeometry")
sepz = ctree.nodes.new("ShaderNodeSeparateXYZ")
ctree.links.new(geo.outputs["Position"], sepz.inputs[0])
grid = ctree.nodes.new("ShaderNodeTexBrick")
grid.inputs["Color1"].default_value = (0.006, 0.20, 0.13, 1)
grid.inputs["Color2"].default_value = (0.008, 0.24, 0.15, 1)
grid.inputs["Mortar"].default_value = (0.95, 0.72, 0.12, 1)
grid.inputs["Scale"].default_value = 1.0
grid.inputs["Mortar Size"].default_value = 0.012
grid.inputs["Brick Width"].default_value = 0.6
grid.inputs["Row Height"].default_value = 0.6
grid.offset = 0.0
grid.squash = 1.0
ctree.links.new(geo.outputs["Position"], grid.inputs["Vector"])
st = ctree.nodes.new("ShaderNodeMath"); st.operation = "LESS_THAN"; st.inputs[1].default_value = 0.02
ctree.links.new(sepz.outputs["Z"], st.inputs[0])
mx = ctree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
ctree.links.new(st.outputs[0], mx.inputs[0])
ctree.links.new(rmp2.outputs[0], mx.inputs["A"])
ctree.links.new(grid.outputs[0], mx.inputs["B"])
ctree.links.new(mx.outputs["Result"], cp.inputs["Base Color"])
card.data.materials.append(cm)

# Hard stage key from high left, small warm kicker, a cold fill: a stop-motion stage is lit with little tungsten units
key = area((-7, -6.5, 10), (0, 0, 2.2), 2600, 3.0, (1.0, 0.90, 0.74))
kick = area((8, 3, 4.5), (0, 0, 2.5), 700, 1.6, (1.0, 0.55, 0.30))
fill = area((3, -11, 3), (0, 0, 2), 420, 7, (0.72, 0.82, 1.0))
world_rgb((0.10, 0.10, 0.12), 1.0)
camera((-1.2, -15.8, 3.3), (-0.4, 0, 2.15), lens=38, dof=12.0, fstop=11.0)
print(render(sc, "e4_clay"))
