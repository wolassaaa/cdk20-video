"""HKBU SCIE1007 coursework science video. manual: the same printed surface as T4, done in an EEVEE shader so a turning surface can be rendered at 4K on the GPU. Dots are computed from screen position so they stay pinned to the paper; runes come from a UV baked at the rest pose so they stay pinned to the surface. Real mesh, real pLDDT. Prints the seconds for each frame."""
import math
import os
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "_work")
D = np.load(os.path.abspath(os.path.join(HERE, "..", "..", "..", "S2plus", "_work", "cdk20_surface.npz")))
v, q, conf = D["verts"].astype(np.float32), D["quads"], D["conf"].astype(np.float32)
v -= (v.min(0) + v.max(0)) / 2
z = np.array([0.15, -0.25, 1.0])
z /= np.linalg.norm(z)
x = np.cross([0, 1, 0], z)
x /= np.linalg.norm(x)
y = np.cross(z, x)
B = np.stack([x, y, z]).astype(np.float32)
v = v @ B.T

bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE"
s.eevee.taa_render_samples = 8
s.render.resolution_x, s.render.resolution_y = 3840, 2160
s.render.film_transparent = True
s.view_settings.view_transform, s.view_settings.look = "Standard", "None"
s.render.image_settings.file_format = "PNG"

me = bpy.data.meshes.new("cdk20")
me.vertices.add(len(v))
me.vertices.foreach_set("co", v.ravel())
me.loops.add(q.size)
me.loops.foreach_set("vertex_index", q.ravel().astype(np.int32))
me.polygons.add(len(q))
me.polygons.foreach_set("loop_start", (np.arange(len(q)) * 4).astype(np.int32))
me.update(calc_edges=True)
me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
a = me.attributes.new("conf", "FLOAT", "POINT")
a.data.foreach_set("value", conf)
uv = me.uv_layers.new(name="rest")
SCX, SW_, SH_ = 36.3, 4080.0, 2464.0
luv = (v[q.ravel(), :2] * SCX / 2 + np.array([SW_ / 2, SH_ / 2], np.float32)) / np.array([SW_, SH_], np.float32)
uv.data.foreach_set("uv", luv.ravel())
o = bpy.data.objects.new("cdk20", me)
s.collection.objects.link(o)

m = bpy.data.materials.new("print")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
N, L = nt.nodes.new, nt.links.new


def mth(op, a_, b_=None, clamp=False):
    n = N("ShaderNodeMath")
    n.operation, n.use_clamp = op, clamp
    for i, val in enumerate((a_, b_)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            n.inputs[i].default_value = val
        else:
            L(val, n.inputs[i])
    return n.outputs[0]


dif = N("ShaderNodeBsdfDiffuse")
aon = N("ShaderNodeAmbientOcclusion")
aon.inputs["Distance"].default_value = 9.0
s2r = N("ShaderNodeShaderToRGB")
L(dif.outputs[0], s2r.inputs[0])
bw = N("ShaderNodeRGBToBW")
L(s2r.outputs[0], bw.inputs[0])
bw2 = N("ShaderNodeRGBToBW")
L(aon.outputs[0], bw2.inputs[0])
tone = mth("MULTIPLY", bw.outputs[0], mth("ADD", 0.25, mth("MULTIPLY", bw2.outputs[0], 0.75)))
tc = N("ShaderNodeTexCoord")
sep = N("ShaderNodeSeparateXYZ")
L(tc.outputs["Window"], sep.inputs[0])
X_, Y_ = mth("MULTIPLY", sep.outputs[0], 3840.0), mth("MULTIPLY", sep.outputs[1], 2160.0)


def screen(deg, cell=14.0):
    c_, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    k = 2 * math.pi / cell
    u = mth("COSINE", mth("MULTIPLY", mth("ADD", mth("MULTIPLY", X_, c_), mth("MULTIPLY", Y_, s_)), k))
    w = mth("COSINE", mth("MULTIPLY", mth("ADD", mth("MULTIPLY", X_, -s_), mth("MULTIPLY", Y_, c_)), k))
    return mth("ADD", 0.5, mth("MULTIPLY", mth("ADD", u, w), 0.25))


def plate(top, width, scr, sharp=6.0):
    g = mth("DIVIDE", mth("SUBTRACT", top, tone), width, True)
    return mth("ADD", mth("MULTIPLY", mth("SUBTRACT", g, mth("SUBTRACT", 1.0, scr)), sharp), 0.5, True)


def over(base, cov, rgb):
    n = N("ShaderNodeMix")
    n.data_type = "RGBA"
    L(cov, n.inputs[0])
    if isinstance(base, tuple):
        n.inputs[6].default_value = base + (1,)
    else:
        L(base, n.inputs[6])
    n.inputs[7].default_value = rgb + (1,)
    return n.outputs[2]


def h(c):
    c = c.lstrip("#")
    return tuple(((int(c[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))


att = N("ShaderNodeAttribute")
att.attribute_name = "conf"
tail = mth("DIVIDE", mth("SUBTRACT", 0.72, att.outputs["Fac"]), 0.05, True)
notail = mth("SUBTRACT", 1.0, tail)
S1, S2 = screen(15), screen(75)
col = over(h("#fbf1d4"), mth("MULTIPLY", plate(0.66, 0.34, S1), notail), h("#f0a81e"))
col = over(col, mth("MULTIPLY", plate(0.86, 0.44, S1), tail), h("#d9361c"))
col = over(col, mth("MULTIPLY", plate(0.36, 0.22, S2), notail), h("#141f66"))
col = over(col, mth("MULTIPLY", plate(0.34, 0.20, S2), tail), h("#3a0a22"))
uvn = N("ShaderNodeUVMap")
uvn.uv_map = "rest"
ti = N("ShaderNodeTexImage")
ti.image = bpy.data.images.load(os.path.join(WORK, "rune_sheet.png"))
ti.image.colorspace_settings.name = "Non-Color"
ti.interpolation = "Cubic"
L(uvn.outputs[0], ti.inputs[0])
fine = mth("DIVIDE", mth("SUBTRACT", 0.78, tone), 0.10, True)
col = over(col, mth("MULTIPLY", mth("MULTIPLY", ti.outputs[0], fine), notail), h("#141f66"))
col = over(col, mth("MULTIPLY", mth("MULTIPLY", ti.outputs[0], fine), tail), h("#3a0a22"))
em = N("ShaderNodeEmission")
L(col, em.inputs[0])
out = N("ShaderNodeOutputMaterial")
L(em.outputs[0], out.inputs[0])
me.materials.append(m)

cam = bpy.data.cameras.new("c")
cam.type = "ORTHO"
cam.ortho_scale = 3840 / SCX
co = bpy.data.objects.new("c", cam)
s.collection.objects.link(co)
co.location = (0, 0, 120)
s.camera = co
sun = bpy.data.lights.new("s", "SUN")
sun.energy = 3.4
so = bpy.data.objects.new("s", sun)
s.collection.objects.link(so)
so.rotation_euler = (math.radians(-38), math.radians(-35), 0)

o.rotation_mode = "XYZ"
times = []
for i, (rx, ry) in enumerate(((-14, 12), (-13, 11), (-12, 10), (-11, 9))):
    o.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(-5))
    s.render.filepath = os.path.join(WORK, "eevee_4k_%d.png" % i)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    times.append(time.time() - t)
    print("FRAME", i, "%.2f s" % times[-1], flush=True)
