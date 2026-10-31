"""HKBU SCIE1007 coursework science video. Style scout e8: inflatable soft body.

The real CDK20 surface blown up inside a room far too small for it: real lumps become puffed foil panels pinched at
seams, squashed flat against ceiling and wall. The panels are one per residue group along the real chain.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import WORK, load_ca, load_surface, rot, smooth_field, vertex_normals

sc = reset(1280, 720, samples=96, bounces=8)
v, q, conf = load_surface()
ca, pl = load_ca()
c = (v.min(0) + v.max(0)) / 2
R = rot(-76, 8, 196)
v = (v - c) * 0.1 @ R.T
ca = (ca - c) * 0.1 @ R.T
v = smooth_field(v, q, it=14)
nrm = vertex_normals(v, q)

# Panels: nearest of a thinned set of real C-alpha positions, so seams come from the real chain
seeds = ca[::7]
# chunked nearest two seeds
d1 = np.full(len(v), 1e9, np.float32)
d2 = np.full(len(v), 1e9, np.float32)
lab = np.zeros(len(v), np.int32)
for i, s in enumerate(seeds):
    d = np.linalg.norm(v - s, axis=1)
    upd = d < d1
    d2 = np.where(upd, d1, np.minimum(d2, d))
    d1 = np.where(upd, d, d1)
    lab = np.where(upd, i, lab)
gap = d2 - d1                         # 0 on a seam
pill = np.sqrt(np.clip(gap / 0.55, 0, 1))
# puckers: fine wrinkles running across the seam, dying out away from it
ang = np.arctan2(v[:, 1], v[:, 0]) * 30 + v[:, 2] * 14 + lab * 1.7
pucker = np.sin(ang) * np.exp(-gap / 0.16) * 0.022
disp = (pill - 0.55) * 0.38 + pucker
v2 = v + nrm * disp[:, None] * 1.0
v2 = smooth_field(v2, q, it=2)
v2 = v2 * 1.85 + np.array([1.2, 0.6, 0.0], np.float32)

# Squash flat against the room. Soft clamp so contact patches spread like a real pressed balloon.
CEIL, FLOOR_Z, WALL_R, WALL_L = 2.95, -3.15, 5.05, -9.0


def squash(x, lim, soft=0.28):
    over = x - (lim - soft)
    return np.where(over > 0, (lim - soft) + soft * (1 - np.exp(-over / soft)), x)


v2[:, 2] = squash(v2[:, 2], CEIL)
v2[:, 2] = -squash(-v2[:, 2], -FLOOR_Z)
v2[:, 0] = squash(v2[:, 0], WALL_R)
ob = add_mesh("foil", v2, q)
add_attr(ob, "conf", conf)

foil = bpy.data.materials.new("foil")
foil.use_nodes = True
nt = foil.node_tree
P = nt.nodes["Principled BSDF"]
P.inputs["Metallic"].default_value = 0.92
P.inputs["Roughness"].default_value = 0.11
P.inputs["Coat Weight"].default_value = 1.0
P.inputs["Coat Roughness"].default_value = 0.04
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "conf"
r = nt.nodes.new("ShaderNodeValToRGB")
e = r.color_ramp.elements
e[0].position = 0.60; e[0].color = (0.98, 0.72, 0.05, 1)    # real tail: gold
e[1].position = 0.72; e[1].color = (1.00, 0.06, 0.34, 1)    # confident core: hot pink foil
nt.links.new(at.outputs["Fac"], r.inputs[0])
nt.links.new(r.outputs[0], P.inputs["Base Color"])
# micro crinkle
n1 = nt.nodes.new("ShaderNodeTexNoise")
n1.inputs["Scale"].default_value = 26; n1.inputs["Detail"].default_value = 3
b = nt.nodes.new("ShaderNodeBump")
b.inputs["Strength"].default_value = 0.12; b.inputs["Distance"].default_value = 0.02
nt.links.new(n1.outputs[0], b.inputs["Height"])
nt.links.new(b.outputs[0], P.inputs["Normal"])
ob.data.materials.append(foil)

# Foil letters from the pre-built pillow field
D = np.load(WORK / "e8_letters.npz")
lv, lq = D["v"], D["q"]
L = add_mesh("letters", lv, lq)
L.rotation_euler = (np.radians(84), np.radians(-3), 0)
L.scale = (0.72, 0.72, 0.72)
L.location = (-4.45, -7.2, -2.15)
sm, sp = principled("silver", (0.93, 0.95, 1.0), 0.12, 1.0)
sp.inputs["Coat Weight"].default_value = 0.6
L.data.materials.append(sm)

# Room: white gallery with a skirting line, wet looking floor, doorway light
def quad(name, pts, mat):
    o = add_mesh(name, np.array(pts, np.float32), np.array([[0, 1, 2, 3]]), smooth=False)
    o.data.materials.append(mat)


wm, wp = principled("wall", (0.015, 0.06, 0.48), 0.5)
fm, fp = principled("floor", (0.55, 0.57, 0.62), 0.12)
cm, cp = principled("ceil", (0.75, 0.75, 0.76), 0.7)
B = 7.5
quad("floor", [(-20, -20, FLOOR_Z), (20, -20, FLOOR_Z), (20, B, FLOOR_Z), (-20, B, FLOOR_Z)], fm)
quad("ceil", [(-20, -20, CEIL), (-20, B, CEIL), (20, B, CEIL), (20, -20, CEIL)], cm)
quad("back", [(-20, B, FLOOR_Z), (20, B, FLOOR_Z), (20, B, CEIL), (-20, B, CEIL)], wm)
quad("right", [(WALL_R, -20, FLOOR_Z), (WALL_R, B, FLOOR_Z), (WALL_R, B, CEIL), (WALL_R, -20, CEIL)], wm)
quad("left", [(-13, B, FLOOR_Z), (-13, -20, FLOOR_Z), (-13, -20, CEIL), (-13, B, CEIL)], wm)

# Fluorescent ceiling strips and a soft big front light; strips reflect as long streaks in the foil
for x in (-9.5, -5, 3):
    a = area((x, -1.5, CEIL - 0.02), (x, -1.5, 0), 170, 1, (1.0, 0.98, 0.95))
    a.data.shape = "RECTANGLE"; a.data.size = 0.3; a.data.size_y = 12
area((-6, -16, 0), (0, 0, 0), 700, 8, (1.0, 0.95, 0.9))
world_rgb((0.10, 0.11, 0.14), 1.0)
camera((-7.2, -15.5, -1.2), (-2.0, 0, -0.2), lens=30)
print(render(sc, "e8_inflate"))
