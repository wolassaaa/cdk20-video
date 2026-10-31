"""HKBU SCIE1007 coursework science video. Renders the same data passes as _shared/bl_passes.py from a custom camera, for the group F style scouts.

blender -b -t 4 -P bl_view.py -- name width height lens vx vy vz roll_deg tx ty tz
Writes scouts/f/_work/view_<name>.npz. tx ty tz shift the aim point in Blender units.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import DIST, build, emit_material

a = sys.argv[sys.argv.index("--") + 1:]
name, W, H, lens = a[0], int(a[1]), int(a[2]), float(a[3])
view = Vector((float(a[4]), float(a[5]), float(a[6]))).normalized()
roll, aim = float(a[7]), Vector((float(a[8]), float(a[9]), float(a[10])))
OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/f/_work"
sc, ob, cam = build(W, H, samples=24)
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
sc.cycles.max_bounces = 2
ob.data.materials.append(bpy.data.materials.new("x"))
bb = np.array(ob.bound_box)
lo, hi = bb.min(0), bb.max(0)
c = Vector(((lo + hi) / 2).tolist()) + aim
cam.data.lens = lens
cam.location = c + view * DIST
cam.rotation_mode = "QUATERNION"
cam.rotation_quaternion = (-view).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(roll))


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
    s = n.new("ShaderNodeAmbientOcclusion")
    s.samples, s.inputs["Distance"].default_value = 16, 1.6
    s.inputs["Color"].default_value = (1, 1, 1, 1)
    return s.outputs["AO"]


def normal(n, l):
    t = n.new("ShaderNodeVectorTransform")
    t.vector_type, t.convert_from, t.convert_to = "NORMAL", "WORLD", "CAMERA"
    l.new(geo(n).outputs["Normal"], t.inputs[0])
    return t.outputs[0]


def depth(n, l):
    d, m = n.new("ShaderNodeCameraData"), n.new("ShaderNodeMapRange")
    m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = DIST - 7, DIST + 7
    l.new(d.outputs["View Z Depth"], m.inputs["Value"])
    return m.outputs["Result"]


def conf(n, l):
    s = n.new("ShaderNodeAttribute")
    s.attribute_name, s.attribute_type = "conf", "GEOMETRY"
    return s.outputs["Fac"]


def pos(n, l):
    m = n.new("ShaderNodeMapRange")
    m.data_type = "FLOAT_VECTOR"
    m.inputs[7].default_value, m.inputs[8].default_value = tuple(lo), tuple(hi)
    l.new(geo(n).outputs["Position"], m.inputs[6])
    return m.outputs[1]


PASSES = dict(key=lit((-0.75, 0.55, 0.30)), rim=lit((0.9, -0.2, 0.12)), ao=ao, normal=normal, depth=depth, conf=conf, pos=pos)
out = {}
for nm, fn in PASSES.items():
    ob.data.materials[0] = emit_material(fn, nm)
    sc.render.filepath = os.path.join(OUT, f"_{name}_{nm}.exr")
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(sc.render.filepath)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)[::-1]
    out[nm] = (px[..., :3] if nm in ("normal", "pos") else px[..., 0]).astype(np.float16)
    out["mask"] = px[..., 3].astype(np.float16)
    bpy.data.images.remove(im)
    os.remove(sc.render.filepath)
out["key"] = np.clip(out["key"], 0, 1)
out["rim"] = np.clip(out["rim"], 0, 1)
np.savez(os.path.join(OUT, f"view_{name}.npz"), **out)
print("done", name)
