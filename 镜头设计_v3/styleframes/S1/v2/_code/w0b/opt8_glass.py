"""opt8 glass-vessels: the real portal tree as clear borosilicate lab glass on black, blue rim light;
crimson liquid rises inside it (after Charlie Murphy's 'Blood Vessels').
blender -b --factory-startup -t 4 -P opt8_glass.py -- --shot hit1|hit2|hit3|1-01 --out RAW.png [--samples 512]
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import numpy as np
from mathutils import Vector

A = args(); shot = A.get("shot", "hit3")
ob = load()
cycles(int(A.get("samples", 256)), bounces=24, transp=32)
bpy.context.scene.cycles.caustics_refractive = True
bpy.context.scene.cycles.caustics_reflective = True
bpy.context.scene.cycles.blur_glossy = 0.5
pv, hv, lv = ob["portal_system"], ob["hepatic_veins"], ob["liver_parenchyma_segments"]
bpy.data.objects.remove(lv)
if A.get("hv", "1") == "0": bpy.data.objects.remove(hv); hv = None
S, P, co, dd = centreline(pv, 2.0)
def cl(s): return Vector([float(np.interp(s, S, P[:, k])) for k in range(3)])

FRONT = {"hit1": 0.0, "hit2": 140.0, "hit3": 285.0, "1-01": 999.0}[shot]
LO = 44.0   # the straight part of the SMV: the root of the sculpture

# ---- materials
def glass(name):
    m, nt, out = mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.97, 0.98, 1.0, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = 1.47
    nt.links.new(b.outputs[0], out.inputs[0])
    return m
mg = glass("borosilicate")
if hv: hv.data.materials.append(mg)
# portal glass: only the single SMV -> portal path + intrahepatic tree (splenic vein and SMV side branches left out)
mp = glass("borosilicate_portal"); ntp = mp.node_tree
op = [n for n in ntp.nodes if n.type == "OUTPUT_MATERIAL"][0]; gb = op.inputs[0].links[0].from_socket
trp = ntp.nodes.new("ShaderNodeBsdfTransparent"); mxp = ntp.nodes.new("ShaderNodeMixShader")
ntp.links.new(attr(ntp, "p"), mxp.inputs[0]); ntp.links.new(trp.outputs[0], mxp.inputs[1]); ntp.links.new(gb, mxp.inputs[2])
ntp.links.new(mxp.outputs[0], op.inputs[0])
pv.data.materials.append(mp)

# liquid: inner skin of the portal mesh pushed 0.5 mm inward
liq = pv.copy(); liq.data = pv.data.copy(); liq.name = "liquid"
bpy.context.scene.collection.objects.link(liq)
liq.data.materials.clear()
dm = liq.modifiers.new("in", 'DISPLACE'); dm.mid_level = 0.0; dm.strength = -float(A.get("wall", 0.55)); dm.direction = 'NORMAL'
m, nt, out = mat("liquid")
d = attr(nt, "d")
fill = math_(nt, 'SUBTRACT', FRONT, d); fill = math_(nt, 'MULTIPLY', fill, 1.5); fill = math_(nt, 'MINIMUM', fill, 1.0); fill = math_(nt, 'MAXIMUM', fill, 0.0)
lo = math_(nt, 'SUBTRACT', d, LO); lo = math_(nt, 'MULTIPLY', lo, 1.5); lo = math_(nt, 'MINIMUM', lo, 1.0); lo = math_(nt, 'MAXIMUM', lo, 0.0)
fill = math_(nt, 'MULTIPLY', fill, lo)
if shot == "hit2":   # a level meniscus: cut the fill by a plane across the trunk at the front
    pf = cl(FRONT); tg = (cl(FRONT + 4) - cl(FRONT - 4)).normalized()
    g2 = nt.nodes.new("ShaderNodeNewGeometry")
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = pf[:]
    nt.links.new(g2.outputs["Position"], sub.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = tg[:]
    nt.links.new(sub.outputs[0], dot.inputs[0])
    below = math_(nt, 'LESS_THAN', dot.outputs["Value"], 0.0)
    near = math_(nt, 'LESS_THAN', d, FRONT + 25)
    fill = math_(nt, 'MULTIPLY', lo, math_(nt, 'MULTIPLY', below, near))
fill = math_(nt, 'MULTIPLY', fill, attr(nt, "p"))
if shot == "1-01":   # four branch tips left empty: four distal branch ends, spread apart, facing the camera
    pmv = np.array([v.value for v in pv.data.attributes["p"].data]) > 0.5
    cand = np.where(pmv & (dd > D_HILUM + 70) & (co[:, 1] < 15))[0]
    tips = [cand[np.argmin(co[cand, 0])]]
    for _ in range(3):
        dmin = np.min([np.linalg.norm(co[cand] - co[t], axis=1) for t in tips], 0)
        tips.append(cand[np.argmax(dmin)])
    # walk each pick to the true end of its branch: the max-d vertex within 18 mm
    T = []
    for t in tips:
        near = np.where(pmv & (np.linalg.norm(co - co[t], axis=1) < 18))[0]
        T.append(near[np.argmax(dd[near])])
    print("tips", [(np.round(co[t]).tolist(), round(float(dd[t]))) for t in T])
    geo_ = nt.nodes.new("ShaderNodeNewGeometry")
    R = float(A.get("tipr", 34.0))
    EMPTY = None
    for t in T:
        vd = nt.nodes.new("ShaderNodeVectorMath"); vd.operation = 'DISTANCE'; vd.inputs[1].default_value = co[t].tolist()
        nt.links.new(geo_.outputs["Position"], vd.inputs[0])
        inR = math_(nt, 'LESS_THAN', vd.outputs["Value"], R)
        far = math_(nt, 'GREATER_THAN', d, float(dd[t]) - R * 1.1)
        empty = math_(nt, 'MULTIPLY', inR, far)
        fill = math_(nt, 'MULTIPLY', fill, math_(nt, 'SUBTRACT', 1.0, empty))
        EMPTY = empty if EMPTY is None else math_(nt, 'MAXIMUM', EMPTY, empty)
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = CRIMSON
b.inputs["Transmission Weight"].default_value = float(A.get("ltrans", 0.4))
b.inputs["Roughness"].default_value = 0.04
b.inputs["IOR"].default_value = 1.33
b.inputs["Subsurface Weight"].default_value = float(A.get("lsss", 0.0))
em = float(A.get("glow", 0.0))
if em:
    b.inputs["Emission Color"].default_value = CRIMSON; b.inputs["Emission Strength"].default_value = em
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
if shot == "1-01":   # the four drained branches turn cold: a faint cobalt tint in the empty glass
    trc = nt.nodes.new("ShaderNodeBsdfTransparent"); trc.inputs[0].default_value = (0.35, 0.45, 1.0, 1)
    emc = nt.nodes.new("ShaderNodeEmission"); emc.inputs[0].default_value = BLUE; emc.inputs[1].default_value = float(A.get("coldglow", 0.6))
    adc = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(trc.outputs[0], adc.inputs[0]); nt.links.new(emc.outputs[0], adc.inputs[1])
    mxc = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(EMPTY, mxc.inputs[0]); nt.links.new(tr.outputs[0], mxc.inputs[1]); nt.links.new(adc.outputs[0], mxc.inputs[2])
    tr = mxc
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(fill, mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
liq.data.materials.append(m)

# ---- light: blue rims from behind, one long white strip overhead-front for the glass highlights
def area(name, loc, target, size, col, power, shape='RECTANGLE', sy=None):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = shape; L.size = size; L.size_y = sy or size
    L.color = col[:3]; L.energy = power
    o = bpy.data.objects.new(name, L); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    o.visible_camera = False
    return o
blue = BLUE
k = float(A.get("light", 1.0))
rb = float(A.get("rim", 0.35))
area("rimL", (-320, 260, 60), (0, 0, -40), 220, blue, 9.0e6 * k * rb, sy=500)
area("rimR", (320, 260, 0), (0, 0, -40), 220, blue, 9.0e6 * k * rb, sy=500)
area("strip", (-60, -260, 330), (0, 0, -20), 30, (1, 1, 1), 4.5e6 * k * float(A.get("strip", 1.0)), sy=600)
area("back", (0, 420, -40), (0, 0, -40), 260, (1, 1, 1), 4.0e6 * k * float(A.get("back", 1.0)), sy=520)
if float(A.get("under", 1.0)) > 0: area("under", (0, 120, -420), (0, 0, -60), 160, (1, 1, 1), 1.0e6 * k * float(A.get("under", 1.0)))
# a dark gallery wall far behind catches a soft blue wash
if A.get("wall_on"):
  wall = bpy.data.meshes.new("wall");   wo = bpy.data.objects.new("wall", wall); bpy.context.scene.collection.objects.link(wo)
  import bmesh
  bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2000); bm.to_mesh(wall); bm.free()
  wo.location = (0, 700, 0); wo.rotation_euler = (math.radians(90), 0, 0)
  mw, ntw, outw = mat("wall")
  bw = ntw.nodes.new("ShaderNodeBsdfDiffuse"); bw.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
  ntw.links.new(bw.outputs[0], outw.inputs[0]); wall.materials.append(mw)

# hit1: one drop of the liquid, falling inside the empty glass root
if shot == "hit1":
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32)
    dr = bpy.context.active_object; dr.name = "drop"
    for p_ in dr.data.polygons: p_.use_smooth = True
    pc = cl(LO + 14); t_ = (cl(LO + 18) - cl(LO + 10)).normalized()
    dr.location = pc; dr.rotation_mode = 'QUATERNION'; dr.rotation_quaternion = t_.to_track_quat('Z', 'Y')
    dr.scale = (0.85, 0.85, 1.25)
    md, ntd, outd = mat("drop")
    bd = ntd.nodes.new("ShaderNodeBsdfPrincipled")
    bd.inputs["Base Color"].default_value = CRIMSON; bd.inputs["Transmission Weight"].default_value = 1.0
    bd.inputs["Roughness"].default_value = 0.02; bd.inputs["IOR"].default_value = 1.33
    bd.inputs["Emission Color"].default_value = CRIMSON; bd.inputs["Emission Strength"].default_value = float(A.get("dropglow", 0.5))
    ntd.links.new(bd.outputs[0], outd.inputs[0]); dr.data.materials.append(md)

# ---- cameras
if shot == "hit1":
    p = cl(LO + 14)
    camera(p + Vector((-10, -55, -4)), p, lens=85, dof=56, fstop=2.0)
elif shot == "hit2":
    p = cl(FRONT - 35)
    camera(p + Vector((-22, -55, -10)), cl(FRONT + 12), lens=28, dof=62, fstop=2.8)
elif shot == "hit3":
    camera(Vector((-120, -400, -95)), Vector((-5, 0, -25)), lens=40, dof=420, fstop=11)
else:
    camera(Vector((-120, -470, -10)), Vector((-5, 0, -10)), lens=40, shift_x=float(A.get('sx', -0.2)), shift_y=-0.02, dof=480, fstop=11)
render(A["out"])
