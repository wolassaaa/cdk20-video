"""opt7 angiogram: the real portal tree as a radiograph; crimson contrast dye runs up one vessel.
blender -b --factory-startup -t 4 -P opt7_angio.py -- --shot hit1|hit2|hit3|1-01 --out RAW.png [--samples 64]
Every surface is additive (transparent + emission), so overlapping tissue builds density like film.
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import numpy as np
from mathutils import Vector

A = args(); shot = A.get("shot", "hit3")
ob = load()
cycles(int(A.get("samples", 96)), bounces=4, transp=256)
pv, hv, lv = ob["portal_system"], ob["hepatic_veins"], ob["liver_parenchyma_segments"]

FRONT = {"hit1": 52.0, "hit2": 175.0, "hit3": 292.0, "1-01": 400.0}[shot]
TAIL = {"hit1": 1000.0, "hit2": 40.0, "hit3": 30.0, "1-01": 30.0}[shot]

def xray(name, k_flat, k_edge, col=BONE, p=2.5):
    m, nt, out = mat(name)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    f = math_(nt, 'POWER', lw.outputs["Facing"], p)
    s = math_(nt, 'MULTIPLY_ADD', f, k_edge)
    nt.links.new(f, s.node.inputs[0]); s.node.inputs[2].default_value = k_flat
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = col
    nt.links.new(s, em.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    return m, nt, em, s

# parenchyma: soft grey mass; hepatic veins: faint bone tubes
# liver: voxel-remesh the 8 segment shells into one body (drops the internal segment walls),
# then shade it as an emitting volume: brightness grows with path length = a real radiograph's density.
rm = lv.modifiers.new("rm", 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = float(A.get("voxel", 2.2)); rm.use_smooth_shade = True
ml, ntl, outl = mat("X_liver")
vol = ntl.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.0
vol.inputs["Emission Color"].default_value = BONE
tex = ntl.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = 0.09; tex.inputs["Detail"].default_value = 10; tex.inputs["Roughness"].default_value = 0.65
em_s = math_(ntl, 'MULTIPLY_ADD', tex.outputs[0], float(A.get("tissue", 0.0035)))
em_s.node.inputs[2].default_value = -0.4 * float(A.get("tissue", 0.0035))
em_s = math_(ntl, 'MAXIMUM', em_s, 0.0)
ntl.links.new(em_s, vol.inputs["Emission Strength"])
ntl.links.new(vol.outputs[0], outl.inputs["Volume"])
# a faint skin on the surface so the silhouette reads
lwl = ntl.nodes.new("ShaderNodeLayerWeight"); lwl.inputs[0].default_value = 0.5
fl = math_(ntl, 'POWER', lwl.outputs["Facing"], 4.0); fl = math_(ntl, "MULTIPLY", fl, float(A.get("skin", 0.03)))
eml = ntl.nodes.new("ShaderNodeEmission"); eml.inputs[0].default_value = BONE; ntl.links.new(fl, eml.inputs[1])
trl = ntl.nodes.new("ShaderNodeBsdfTransparent"); addl = ntl.nodes.new("ShaderNodeAddShader")
ntl.links.new(trl.outputs[0], addl.inputs[0]); ntl.links.new(eml.outputs[0], addl.inputs[1]); ntl.links.new(addl.outputs[0], outl.inputs[0])
mh, *_ = xray("X_hv", 0.003, 0.05, p=2.5)
lv.data.materials.append(ml); hv.data.materials.append(mh)

S, P, co, dd = centreline(pv, 2.0)
pm = path_mask(pv, S, P, co, dd)
print("path verts", int(pm.sum()), "of", len(pm))
# portal: bone X-ray + dye where d < FRONT
m, nt, em, s = xray("X_portal", 0.010, 0.12, p=2.0)
out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
d = attr(nt, "d")
behind = math_(nt, 'SUBTRACT', FRONT, d)                     # >0 where dye has arrived
dye = math_(nt, 'DIVIDE', behind, float(A.get('soft', 4.0))); dye = math_(nt, 'MINIMUM', dye, 1.0); dye = math_(nt, 'MAXIMUM', dye, 0.0)
dye = math_(nt, 'MULTIPLY', dye, attr(nt, "p"))
if shot == "hit1":   # a single bolus: a soft bead of dye around one point on the trunk
    S0, P0, *_ = centreline(pv, 2.0)
    bp = [float(np.interp(FRONT, S0, P0[:, k])) for k in range(3)]
    geo_ = nt.nodes.new("ShaderNodeNewGeometry")
    vd = nt.nodes.new("ShaderNodeVectorMath"); vd.operation = 'DISTANCE'; vd.inputs[1].default_value = bp
    nt.links.new(geo_.outputs["Position"], vd.inputs[0])
    bol = math_(nt, "SUBTRACT", 7.0, vd.outputs["Value"]); bol = math_(nt, "DIVIDE", bol, 5.0); bol = math_(nt, 'MINIMUM', bol, 1.0); bol = math_(nt, 'MAXIMUM', bol, 0.0)
    dye = bol

# head: brighter within TAIL mm of the front
head = math_(nt, 'DIVIDE', behind, TAIL); head = math_(nt, 'SUBTRACT', 1.0, head); head = math_(nt, 'MAXIMUM', head, 0.0)
head = math_(nt, 'POWER', head, 2.0)
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.4
core = math_(nt, 'SUBTRACT', 1.0, lw.outputs["Facing"]); core = math_(nt, 'MULTIPLY_ADD', core, 0.6)
core.node.inputs[2].default_value = 0.4
strength = math_(nt, 'MULTIPLY_ADD', head, float(A.get("headgain", 3.0)))
strength.node.inputs[2].default_value = float(A.get("dye", 0.55))
strength = math_(nt, 'MULTIPLY', strength, dye)
strength = math_(nt, 'MULTIPLY', strength, core)
nodye = math_(nt, 'SUBTRACT', 1.0, dye)
nt.links.new(math_(nt, 'MULTIPLY', s, nodye), em.inputs[1])
emd = nt.nodes.new("ShaderNodeEmission"); emd.inputs[0].default_value = CRIMSON
nt.links.new(strength, emd.inputs[1])
add2 = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(out.inputs[0].links[0].from_socket, add2.inputs[0]); nt.links.new(emd.outputs[0], add2.inputs[1])
nt.links.new(add2.outputs[0], out.inputs[0])
pv.data.materials.append(m)

# ---- cameras
def cl(s): return Vector([float(np.interp(s, S, P[:, k])) for k in range(3)])
if shot == "hit1":
    p = cl(FRONT)
    camera(p + Vector((-25, -190, 15)), p, lens=60, shift_x=0.0, dof=193, fstop=1.4)
elif shot == "hit2":
    p = cl(FRONT - 70); t = cl(FRONT)
    camera(p + Vector((-40, -170, -95)), t + Vector((0, 0, 5)), lens=30)
else:
    # AP projection, like a film: orthographic, straight from the front
    cam = camera(Vector((0, -800, -40)), Vector((0, 0, -40)), lens=50)
    cam.data.type = 'ORTHO'
    if shot == "hit3": cam.data.ortho_scale = 400; cam.location.z = -45; cam.data.shift_x = 0.0
    else: cam.data.ortho_scale = 470; cam.location.z = -40; cam.location.x = -10; cam.data.shift_x = -0.24
render(A["out"])
