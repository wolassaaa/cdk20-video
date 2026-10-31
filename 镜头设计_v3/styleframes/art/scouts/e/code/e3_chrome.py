"""HKBU SCIE1007 coursework science video. Style scout e3: Y2K liquid chrome.

The real CDK20 surface, melted slightly and mirrored; a hard banded environment makes the liquid chrome read.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import load_surface, rot, smooth_field

sc = reset(1280, 720, samples=64, bounces=8)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.1
v = v @ rot(-80, 10, 200).T
v = smooth_field(v, q, it=6)                         # liquid: keeps every lump, drops the tiny ones

prot = add_mesh("prot", v, q)
prot.scale = (1.32, 1.32, 1.32)
prot.location = (0.9, 0, 0.75)
bpy.context.view_layer.objects.active = prot

# Environment: banded studio, black horizon, a hot acid sky. Liquid chrome is only ever a picture of its surroundings.
w = bpy.data.worlds.new("w")
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
stops = [
    (0.00, (0.00, 0.01, 0.06)), (0.32, (0.01, 0.03, 0.30)), (0.47, (0.45, 0.72, 1.00)),
    (0.495, (1.00, 1.00, 1.00)), (0.502, (0.00, 0.00, 0.00)), (0.56, (0.02, 0.01, 0.03)),
    (0.60, (0.95, 0.02, 0.55)), (0.66, (0.03, 0.02, 0.10)), (0.74, (0.75, 0.98, 1.00)),
    (0.80, (0.10, 0.30, 0.85)), (1.00, (0.98, 0.98, 1.00)),
]
cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
cr.elements[1].position = stops[1][0]; cr.elements[1].color = (*stops[1][1], 1)
for pos, col in stops[2:]:
    e = cr.elements.new(pos); e.color = (*col, 1)
mp = nt.nodes.new("ShaderNodeMapRange")
mp.inputs[1].default_value = -1; mp.inputs[2].default_value = 1
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 1.6
noise.inputs["Detail"].default_value = 2
nt.links.new(tc.outputs["Generated"], noise.inputs["Vector"])
mix = nt.nodes.new("ShaderNodeMath")
mix.operation = "MULTIPLY_ADD"
mix.inputs[1].default_value = 0.34
mix.inputs[2].default_value = -0.17
nt.links.new(noise.outputs[0], mix.inputs[0])
add = nt.nodes.new("ShaderNodeMath")
add.operation = "ADD"
nt.links.new(sep.outputs["Z"], add.inputs[0])
nt.links.new(mix.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], mp.inputs[0])
nt.links.new(mp.outputs[0], ramp.inputs[0])
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs[1].default_value = 1.25
nt.links.new(ramp.outputs[0], bg.inputs[0])
o = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(bg.outputs[0], o.inputs[0])
sc.world = w

chrome, pc = principled("chrome", (0.98, 0.985, 1.0), 0.035, 1.0)
prot.data.materials.append(chrome)

# Title: fat letters, remeshed and smoothed until they read as poured mercury, sunk into the molecule
t = text3d("CDK20", "ariblk.ttf", size=1.72, extrude=0.14, bevel=0.085, bevel_res=4)
t.rotation_euler = (np.radians(82), 0, np.radians(-5))
t.location = (-0.3, -3.6, -1.32)
remesh_smooth(t, voxel=0.018, smooth=20, factor=0.7)
t.data.materials.append(chrome)
t.data.polygons.foreach_set("use_smooth", np.ones(len(t.data.polygons), bool))
t.data.update()

# Mercury beads breaking from the surface
rng = np.random.default_rng(4)
for i in range(46):
    r = 0.03 + 0.32 * rng.random() ** 3
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r,
                                         location=(rng.uniform(-6.5, 6.5), rng.uniform(-3.5, 1.0), rng.uniform(-3.4, 3.5)))
    so = bpy.context.object
    bpy.ops.object.shade_smooth()
    so.scale = (1, 1, 1.0 + rng.random() * 0.5)
    so.data.materials.append(chrome)

sc.render.film_transparent = False
camera((0, -12.5, 0.1), (0.0, 0, 0.0), lens=42)
print(render(sc, "e3_chrome"))
