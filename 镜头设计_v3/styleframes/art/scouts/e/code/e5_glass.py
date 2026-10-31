"""HKBU SCIE1007 coursework science video. Style scout e5: glass and caustics.

A solid glass casting of the real CDK20 surface on a black table. The rainbow on the table is a real photon trace
through the atom field (e5_caustic_map.py), three IORs, used as the floor texture. Letters are glass too.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import WORK, load_surface, rot, smooth_field

sc = reset(1280, 720, samples=200, bounces=14)
sc.cycles.caustics_refractive = True
sc.cycles.caustics_reflective = True
sc.cycles.blur_glossy = 0.0
sc.cycles.sample_clamp_indirect = 40

v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.1 @ rot(-70, 0, 200).T
v = smooth_field(v, q, it=2)
Z0 = 3.4
v[:, 2] += Z0
print("zmin", v[:, 2].min())
prot = add_mesh("prot", v, q)

# Dispersive glass: three lobes, one IOR per colour, added
G = bpy.data.materials.new("glass")
G.use_nodes = True
nt = G.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
a1 = nt.nodes.new("ShaderNodeAddShader")
a2 = nt.nodes.new("ShaderNodeAddShader")
for i, (ior, col) in enumerate(((1.46, (1, 0, 0)), (1.50, (0, 1, 0)), (1.56, (0, 0, 1)))):
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = ior
    g.inputs["Roughness"].default_value = 0.0
    g.inputs["Color"].default_value = (*col, 1)
    if i == 0:
        nt.links.new(g.outputs[0], a1.inputs[0])
    elif i == 1:
        nt.links.new(g.outputs[0], a1.inputs[1])
    else:
        nt.links.new(a1.outputs[0], a2.inputs[0])
        nt.links.new(g.outputs[0], a2.inputs[1])
nt.links.new(a2.outputs[0], out.inputs["Surface"])
prot.data.materials.append(G)

# Floor: dark gloss with the photon map laid in as light
SPAN = 34.0
im = bpy.data.images.load(str(WORK / "e5_caustic.png"))
im.colorspace_settings.name = "Non-Color"
fm, fp = principled("floor", (0.0, 0.0, 0.0), 0.5)
t = fm.node_tree
fp.inputs["Specular IOR Level"].default_value = 0.02
tc = t.nodes.new("ShaderNodeTexCoord")
mp = t.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / SPAN, 1 / SPAN, 1)
mp.inputs["Location"].default_value = (0.5, 0.5, 0)
t.links.new(tc.outputs["Object"], mp.inputs[0])
ti = t.nodes.new("ShaderNodeTexImage")
ti.image = im
ti.interpolation = "Linear"
ti.extension = "CLIP"
t.links.new(mp.outputs[0], ti.inputs[0])
gam = t.nodes.new("ShaderNodeGamma")
gam.inputs["Gamma"].default_value = 2.0
t.links.new(ti.outputs[0], gam.inputs[0])
t.links.new(gam.outputs[0], fp.inputs["Emission Color"])
fp.inputs["Emission Strength"].default_value = 1.7
fv = np.array([[-90, -90, 0], [90, -90, 0], [90, 90, 0], [-90, 90, 0]], np.float32)
fl = add_mesh("floor", fv, np.array([[0, 1, 2, 3]]), smooth=False)
fl.data.materials.append(fm)

# Glass title lying upright on the table, lit from behind by the rainbow
tx = text3d("CDK20", "ariblk.ttf", size=2.2, extrude=0.28, bevel=0.03, bevel_res=2)
tx.rotation_euler = (np.radians(90), 0, np.radians(-14))
tx.location = (1.0, -3.2, 0.79)
cm, cp = principled("cglass", (1, 1, 1), 0.02)
cp.inputs["Transmission Weight"].default_value = 1.0
cp.inputs["IOR"].default_value = 1.5
tx.data.materials.append(G)

# One hard distant light, and a strip softbox that cuts bright edges into the glass
l = (0.62, 0.42, -0.66)
s = sun((0, 0, 0), 3.0, (1, 1, 1), 0.3)
from mathutils import Vector

s.rotation_mode = "QUATERNION"
s.rotation_quaternion = Vector(l).to_track_quat("-Z", "Y")
area((10, 8, 10), (0, 0, 3), 700, 4, (0.8, 0.9, 1.0))
area((-9, 7, 5), (0, 0, 3), 500, 2.5, (1.0, 0.75, 0.9))
area((-3, -15, 8), (-2, -6, 1), 1500, 7, (1.0, 1.0, 1.0))
world_rgb((0.003, 0.0035, 0.005), 1.0)
camera((-6.5, -21.0, 7.6), (1.2, 0.6, 1.9), lens=40)
print(render(sc, "e5_glass"))
