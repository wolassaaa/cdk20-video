"""HKBU SCIE1007 coursework science video. F4 plate: CDK20 as predicted by AlphaFold DB v6 (AF-Q8IZL9-F1, CC BY 4.0). A thin glass outer surface holds the real backbone. Ribbon colour is a hard step on the real per-residue pLDDT at 70. Orthographic, 1 unit = 10 Angstrom, so the scale bar is true."""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/specimen/code")
import sp
from sp import gk

S1 = sp.ROOT + "styleframes/S1/v2/_code/"
sys.path.append(S1 + "s110")
import prot_geo as G
G.JSON = sp.ROOT + "styleframes/S2plus/code/cdk20_backbone_view.json"  # same frame as the surface mesh: x right, y up, z to the lens

A = sp.args()
argv = sys.argv[sys.argv.index("--") + 1:]
AZ = float(argv[2]) if len(argv) > 2 else 0.0
EL = float(argv[3]) if len(argv) > 3 else 0.0
OUT = argv[4] if len(argv) > 4 else "f4"
WIDTH = 12.8                          # units: 150 px per nm, 15 px per Angstrom
sc = sp.scene(A["samples"], A["pct"])

ob = gk.cdk20(sp.shell(blend=0.20, edge=0.52, rough=0.16, rgb=(0.8, 0.85, 1.0), fill=0.03), centre=False)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
ob.data.remesh_voxel_size = 0.42        # the molecular surface is lumpy and fights the ribbon: remesh and smooth it into one clean case around the same volume
ob.data.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
m_ = ob.modifiers.new("smooth", "SMOOTH")
m_.factor, m_.iterations = 1.0, 30
d_ = ob.modifiers.new("inflate", "DISPLACE")   # smoothing shrinks; push back out so the case still clears the chain
d_.strength, d_.mid_level = 0.30, 0.0
for p in ob.data.polygons:
    p.use_smooth = True
res = G.load(scale=0.1)
rib = G.ribbon(res, scale=0.1, coil_r=0.5, helix_w=1.9, sheet_w=1.7, thick=0.42, arrow=2.2)


def ribbon_mat():
    m = sp.tissue((1, 1, 1), rough=0.42, coat=0.3)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name, at.attribute_type = "plddt", "GEOMETRY"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value, mr.inputs[2].default_value = 0, 100
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    e = cr.color_ramp.elements
    e[0].position, e[0].color = 0.0, (*sp.RED, 1)
    e[1].position, e[1].color = 0.7, (*sp.BONE, 1)
    nt.links.new(at.outputs["Fac"], mr.inputs[0])
    nt.links.new(mr.outputs[0], cr.inputs[0])
    cd = nt.nodes.new("ShaderNodeCameraData")               # chain at the back goes darker, so the front of the fold reads first and the path can be followed
    dr = nt.nodes.new("ShaderNodeMapRange")
    dr.inputs[1].default_value, dr.inputs[2].default_value = 17.5, 23.0
    dr.inputs[3].default_value, dr.inputs[4].default_value = 1.0, 0.22
    nt.links.new(cd.outputs["View Z Depth"], dr.inputs[0])
    mu = nt.nodes.new("ShaderNodeVectorMath")
    mu.operation = "SCALE"
    nt.links.new(cr.outputs[0], mu.inputs[0])
    nt.links.new(dr.outputs[0], mu.inputs["Scale"])
    nt.links.new(mu.outputs[0], b.inputs["Base Color"])
    nt.links.new(mu.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.30
    return m


rib.data.materials.append(ribbon_mat())

bb = [Vector(r["ca"]) for r in res]
c0 = sum(bb, Vector()) / len(bb)
TARGET = c0 + Vector((2.05, 0.0, 0))     # protein sits left of centre, labels on the right
a, e = math.radians(AZ), math.radians(EL)
d = Vector((math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)))
pos = TARGET + 20 * d
cam = sp.ortho(pos, TARGET, WIDTH)
fwd = -d
right = fwd.cross(Vector((0, 1, 0))).normalized()
up = right.cross(fwd)
rel = lambda x, y, z: tuple(c0 + right * x + up * y + fwd * z)
sp.softbox("key", rel(-5, 6, -8), tuple(c0), 4.6, 10, 8)
sp.softbox("fill", rel(7, -2, -7), tuple(c0), 0.7, 8, 8)
sp.softbox("rim", rel(-6, 1, 6), tuple(c0), 22, 0.8, 14, (0.8, 0.85, 1.0))
sp.softbox("rim2", rel(7, 3, 5), tuple(c0), 12, 0.8, 12, (0.8, 0.85, 1.0))
gk.render(sp.PLATES + OUT + ".png")

# where residues land on screen, for label placement
from bpy_extras.object_utils import world_to_camera_view as w2c
sc2 = bpy.context.scene
pts = {}
for i in (1, 200, 303, 310, 320, 330, 340, 346):
    p = w2c(sc2, cam, Vector(res[i - 1]["ca"]))
    pts[i] = (round(p.x * 1920), round((1 - p.y) * 1080))
json.dump({"px_per_nm": 1920 / WIDTH, "res": pts}, open(sp.PLATES + OUT + ".json", "w"))
print("POINTS", pts)
