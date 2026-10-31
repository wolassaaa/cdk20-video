"""HKBU SCIE1007 coursework science video. Style scout f7: line light. Two layers on a black mirror: real CDK20 surface as contour rings of light, and the real CA chain as one continuous tube of light.
Blue is pLDDT 0.7 and above, orange is below, both from AlphaFold DB v6. Writes scouts/f/_work/tron.npz."""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import SC, VIEW, build

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/f/_work"
PDB = r"D:/。hkbu/molecular science/镜头设计_v3/assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
W, H = 1280, 720
SPP = 96
sc, ob, cam = build(W, H, samples=SPP)
sc.render.film_transparent = False
sc.cycles.max_bounces = 3
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"

vs = np.empty(len(ob.data.vertices) * 3, np.float32)
ob.data.vertices.foreach_get("co", vs)
vs = vs.reshape(-1, 3)
lo, hi = vs.min(0), vs.max(0)
cen = Vector(((lo + hi) / 2).tolist())
ob.data.transform(Matrix.Translation(-cen))
q = Matrix.Rotation(math.radians(-14), 4, "X").to_quaternion() @ Matrix.Rotation(math.radians(24), 4, "Z").to_quaternion() @ VIEW.rotation_difference(Vector((0, -1, 0)))
ob.rotation_mode = "QUATERNION"
ob.rotation_quaternion = q
FLOOR = -3.15

# chain: real CA trace, Catmull-Rom smoothed, split into confident and low-confidence runs
xyz, bf = [], []
for ln in open(PDB):
    if ln.startswith("ATOM") and ln[12:16].strip() == "CA":
        xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
        bf.append(float(ln[60:66]) / 100)
xyz, bf = np.array(xyz), np.array(bf)
# the surface mesh lives in the camera frame of S2plus/code/make_surface.py, so the chain takes the same transform
VIEW_M = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
u, _, vt = np.linalg.svd(np.array(VIEW_M))
R = u @ vt
xyz = (xyz - xyz[:302].mean(0)) @ R.T * SC
print("chain bbox", xyz.min(0), xyz.max(0), "mesh bbox", lo, hi)


def catmull(p, n=6):
    out = []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, len(p) - 1)]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(p[-1])
    return np.array(out)


def tube(name, pts_list, col, strength, radius):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", radius, 2
    for pts in pts_list:
        s = cu.splines.new("POLY")
        s.points.add(len(pts) - 1)
        for pt, v in zip(s.points, pts):
            pt.co = (float(v[0]), float(v[1]), float(v[2]), 1)
    o = bpy.data.objects.new(name, cu)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em, ou = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], ou.inputs["Surface"])
    cu.materials.append(m)
    sc.collection.objects.link(o)
    o.matrix_world = ob.matrix_world.copy()
    return o


smooth = catmull(xyz - np.array(cen))
n_sub = (len(smooth) - 1) / (len(xyz) - 1)
sub_b = np.interp(np.arange(len(smooth)), np.arange(len(xyz)) * n_sub, bf)
runs_a, runs_b = [], []
i = 0
while i < len(smooth) - 1:
    j = i
    lowc = sub_b[i] < 0.7
    while j < len(smooth) - 1 and (sub_b[j] < 0.7) == lowc:
        j += 1
    (runs_b if lowc else runs_a).append(smooth[i:j + 1])
    i = j
bpy.context.view_layer.update()
CYAN, ORANGE = (0.03, 0.72, 1.0), (1.0, 0.27, 0.02)
t_a = tube("chainA", runs_a, CYAN, 9.0, 0.026)
t_b = tube("chainB", runs_b, ORANGE, 9.0, 0.026)
# re-link so the tubes follow the same rotation
t_a.rotation_mode = t_b.rotation_mode = "QUATERNION"
t_a.rotation_quaternion = t_b.rotation_quaternion = q

# surface shell: matte black with contour rings
m = bpy.data.materials.new("shell")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
N = nt.nodes.new
L = nt.links.new
geo, sep, mul, fr, sub, ab, ramp = N("ShaderNodeNewGeometry"), N("ShaderNodeSeparateXYZ"), N("ShaderNodeMath"), N("ShaderNodeMath"), N("ShaderNodeMath"), N("ShaderNodeMath"), N("ShaderNodeMapRange")
mul.operation, fr.operation, sub.operation, ab.operation = "MULTIPLY", "FRACT", "SUBTRACT", "ABSOLUTE"
mul.inputs[1].default_value, sub.inputs[1].default_value = 4.6, 0.5
ramp.interpolation_type = "SMOOTHSTEP"
ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = 0.035, 0.0
L(geo.outputs["Position"], sep.inputs[0])
L(sep.outputs["Z"], mul.inputs[0])
L(mul.outputs[0], fr.inputs[0])
L(fr.outputs[0], sub.inputs[0])
L(sub.outputs[0], ab.inputs[0])
L(ab.outputs[0], ramp.inputs["Value"])
# silhouette line
lw, edge = N("ShaderNodeLayerWeight"), N("ShaderNodeMapRange")
lw.inputs["Blend"].default_value = 0.5
edge.interpolation_type = "SMOOTHSTEP"
edge.inputs["From Min"].default_value, edge.inputs["From Max"].default_value = 0.93, 0.985
L(lw.outputs["Facing"], edge.inputs["Value"])
add = N("ShaderNodeMath")
add.operation = "MAXIMUM"
L(ramp.outputs[0], add.inputs[0])
L(edge.outputs[0], add.inputs[1])
attr, cr = N("ShaderNodeAttribute"), N("ShaderNodeMapRange")
attr.attribute_name, attr.attribute_type = "conf", "GEOMETRY"
cr.data_type = "RGBA" if False else "FLOAT"
mixc = N("ShaderNodeMix")
mixc.data_type = "RGBA"
th = N("ShaderNodeMath")
th.operation = "GREATER_THAN"
th.inputs[1].default_value = 0.7
L(attr.outputs["Fac"], th.inputs[0])
L(th.outputs[0], mixc.inputs["Factor"])
mixc.inputs["A"].default_value = (*ORANGE, 1)
mixc.inputs["B"].default_value = (*CYAN, 1)
em, gl, ms, ou = N("ShaderNodeEmission"), N("ShaderNodeBsdfDiffuse"), N("ShaderNodeAddShader"), N("ShaderNodeOutputMaterial")
sm = N("ShaderNodeMath")
sm.operation = "MULTIPLY"
sm.inputs[1].default_value = 4.0
L(add.outputs[0], sm.inputs[0])
L(sm.outputs[0], em.inputs["Strength"])
L(mixc.outputs["Result"], em.inputs["Color"])
gl.inputs["Color"].default_value = (0.002, 0.003, 0.004, 1)
L(gl.outputs[0], ms.inputs[0])
L(em.outputs[0], ms.inputs[1])
L(ms.outputs[0], ou.inputs["Surface"])
ob.data.materials.append(m)

# black mirror
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, FLOOR))
fl = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
nt = fm.node_tree
b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.42, 0.45, 0.48, 1)
b.inputs["Metallic"].default_value = 1.0
b.inputs["Roughness"].default_value = 0.035
g2, cd, sx, sy, fxx, fyy, sbx, sby, abx, aby, mn, rmp, fade, mult, em2, add2 = (nt.nodes.new(x) for x in ("ShaderNodeNewGeometry", "ShaderNodeCameraData", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMapRange", "ShaderNodeMapRange", "ShaderNodeMath", "ShaderNodeEmission", "ShaderNodeAddShader"))
sp = nt.nodes.new("ShaderNodeSeparateXYZ")
for n_, op in ((sx, "MULTIPLY"), (sy, "MULTIPLY"), (fxx, "FRACT"), (fyy, "FRACT"), (sbx, "SUBTRACT"), (sby, "SUBTRACT"), (abx, "ABSOLUTE"), (aby, "ABSOLUTE"), (mn, "MINIMUM"), (mult, "MULTIPLY")):
    n_.operation = op
sx.inputs[1].default_value = sy.inputs[1].default_value = 0.5
sbx.inputs[1].default_value = sby.inputs[1].default_value = 0.5
rmp.inputs["From Min"].default_value, rmp.inputs["From Max"].default_value = 0.494, 0.5
rmp.inputs["To Min"].default_value, rmp.inputs["To Max"].default_value = 0.0, 1.0
fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = 6.0, 34.0
fade.inputs["To Min"].default_value, fade.inputs["To Max"].default_value = 1.0, 0.0
LK = nt.links.new
LK(g2.outputs["Position"], sp.inputs[0])
LK(sp.outputs["X"], sx.inputs[0])
LK(sp.outputs["Y"], sy.inputs[0])
LK(sx.outputs[0], fxx.inputs[0])
LK(sy.outputs[0], fyy.inputs[0])
LK(fxx.outputs[0], sbx.inputs[0])
LK(fyy.outputs[0], sby.inputs[0])
LK(sbx.outputs[0], abx.inputs[0])
LK(sby.outputs[0], aby.inputs[0])
mx_ = nt.nodes.new("ShaderNodeMath")
mx_.operation = "MAXIMUM"
LK(abx.outputs[0], mx_.inputs[0])
LK(aby.outputs[0], mx_.inputs[1])
LK(mx_.outputs[0], rmp.inputs["Value"])
LK(cd.outputs["View Distance"], fade.inputs["Value"])
LK(rmp.outputs[0], mult.inputs[0])
LK(fade.outputs[0], mult.inputs[1])
em2.inputs["Color"].default_value = (0.03, 0.55, 1.0, 1)
gs = nt.nodes.new("ShaderNodeMath")
gs.operation = "MULTIPLY"
gs.inputs[1].default_value = 0.12
LK(mult.outputs[0], gs.inputs[0])
LK(gs.outputs[0], em2.inputs["Strength"])
ou2 = nt.nodes["Material Output"]
LK(b.outputs[0], add2.inputs[0])
LK(em2.outputs[0], add2.inputs[1])
LK(add2.outputs[0], ou2.inputs["Surface"])
fl.data.materials.append(fm)

w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
sc.world = w
cam.data.lens, cam.data.clip_start, cam.data.clip_end = 22, 0.05, 500
cam.location = Vector((0.0, -8.4, FLOOR + 0.30))
look = (Vector((0.15, 0, -0.75)) - cam.location).normalized()
cam.rotation_mode = "QUATERNION"
cam.rotation_quaternion = look.to_track_quat("-Z", "Y")


def grab(path):
    im = bpy.data.images.load(path)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    os.remove(path)
    return px.reshape(H, W, 4)[::-1][..., :3].astype(np.float32)


# layer A: shell only
t_a.hide_render = t_b.hide_render = True
sc.render.filepath = os.path.join(OUT, "_tron_a.exr")
bpy.ops.render.render(write_still=True)
A = grab(sc.render.filepath)
# layer B: chain only
t_a.hide_render = t_b.hide_render = False
ob.hide_render = True
sc.render.filepath = os.path.join(OUT, "_tron_b.exr")
bpy.ops.render.render(write_still=True)
B = grab(sc.render.filepath)
np.savez(os.path.join(OUT, "tron.npz"), shell=A, chain=B)
print("done")
