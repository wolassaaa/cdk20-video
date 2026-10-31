"""HKBU SCIE1007 coursework science video. Renders the CDK20 data passes once, so a style can be tried in numpy in a minute without touching Blender.

blender -b -t 4 -P bl_passes.py
Writes ../_passes/cdk20_passes.npz (float16, 1080x1920) and a preview sheet. Raw view, so values are data, not display colour.
key, rim: diffuse light from two low directions. ao: ambient occlusion. normal: camera space, -1..1. depth: 0 near, 1 far.
conf: pLDDT / 100, real data. pos: model position, 0..1 in the bounding box. mask: coverage.
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scene_cdk20 import DIST, build, emit_material

OUT = os.path.join(HERE, "..", "_passes")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
sc, ob, cam = build(W, H, samples=32)
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
sc.cycles.max_bounces = 2
ob.data.materials.append(bpy.data.materials.new("x"))

bb = np.array(ob.bound_box)
lo, hi = bb.min(0), bb.max(0)


def geo(n):
    return n.new("ShaderNodeNewGeometry")


def lit(direction):
    def f(n, l):
        dot = n.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        l.new(geo(n).outputs["Normal"], dot.inputs[0])
        dot.inputs[1].default_value = tuple(Vector(direction).normalized())
        return dot.outputs["Value"]
    return f


def ao(n, l):
    a = n.new("ShaderNodeAmbientOcclusion")
    a.samples, a.inputs["Distance"].default_value = 16, 1.6
    a.inputs["Color"].default_value = (1, 1, 1, 1)
    return a.outputs["AO"]


def normal(n, l):
    t = n.new("ShaderNodeVectorTransform")
    t.vector_type, t.convert_from, t.convert_to = "NORMAL", "WORLD", "CAMERA"
    l.new(geo(n).outputs["Normal"], t.inputs[0])
    return t.outputs[0]


def depth(n, l):
    c, m = n.new("ShaderNodeCameraData"), n.new("ShaderNodeMapRange")
    m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = DIST - 7, DIST + 7
    l.new(c.outputs["View Z Depth"], m.inputs["Value"])
    return m.outputs["Result"]


def conf(n, l):
    a = n.new("ShaderNodeAttribute")
    a.attribute_name, a.attribute_type = "conf", "GEOMETRY"
    return a.outputs["Fac"]


def pos(n, l):
    m = n.new("ShaderNodeMapRange")
    m.data_type = "FLOAT_VECTOR"
    m.inputs[7].default_value, m.inputs[8].default_value = tuple(lo), tuple(hi)  # From Min, From Max of the vector socket set
    l.new(geo(n).outputs["Position"], m.inputs[6])
    return m.outputs[1]


PASSES = dict(key=lit((-0.75, 0.55, 0.30)), rim=lit((0.9, -0.2, 0.12)), ao=ao, normal=normal, depth=depth, conf=conf, pos=pos)
out = {}
for name, fn in PASSES.items():
    ob.data.materials[0] = emit_material(fn, name)
    sc.render.filepath = os.path.join(OUT, f"_{name}.exr")
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(sc.render.filepath)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)[::-1]
    out[name] = (px[..., :3] if name in ("normal", "pos") else px[..., 0]).astype(np.float16)
    out["mask"] = px[..., 3].astype(np.float16)
    bpy.data.images.remove(im)
    os.remove(sc.render.filepath)
    print("pass", name, float(px[..., 0].min()), float(px[..., 0].max()))
out["key"] = np.clip(out["key"], 0, 1)
out["rim"] = np.clip(out["rim"], 0, 1)
np.savez_compressed(os.path.join(OUT, "cdk20_passes.npz"), **out)
print("done")
