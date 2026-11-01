"""HKBU SCIE1007 coursework science video. Ink direction: renders real geometry into numpy data passes, no picture yet.

blender -b -t 4 -P bl_ink_passes.py -- <liver|protein|figure> [--scale 2] [--yaw 0 --pitch 0 --roll 0]
Writes ../_work/<scene>.npz. For each layer: pos (world xyz), nrm (camera-space normal), attr (scene data), light (shadowed key light), mask.
pos and nrm are unfiltered single samples, so each pixel holds exact geometry. The line pattern is computed from them in engrave.py.
Liver and body come from BodyParts3D, the protein from AlphaFold DB v6. Nothing here is drawn by hand.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
ROOT = HERE + "../../../"
sys.path.insert(0, ROOT + "art/_shared")
sys.path.insert(0, ROOT + "S1/v2/_code/s110")
import glass_kit as gk

argv = sys.argv[sys.argv.index("--") + 1:]
NAME = argv[0]


def opt(k, d):
    return float(argv[argv.index("--" + k) + 1]) if "--" + k in argv else d


SCALE = opt("scale", 2)
W, H = int(1920 * SCALE), int(1080 * SCALE)
OUT = HERE + "../_work/"
TAG = argv[argv.index("--tag") + 1] if "--tag" in argv else NAME


def mat_emit(fn, name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    e, o = n.new("ShaderNodeEmission"), n.new("ShaderNodeOutputMaterial")
    l.new(fn(n, l), e.inputs["Color"])
    l.new(e.outputs[0], o.inputs["Surface"])
    return m


def f_pos(n, l):
    return n.new("ShaderNodeNewGeometry").outputs["Position"]


def f_nrm(n, l):
    t = n.new("ShaderNodeVectorTransform")
    t.vector_type, t.convert_from, t.convert_to = "NORMAL", "WORLD", "CAMERA"
    l.new(n.new("ShaderNodeNewGeometry").outputs["Normal"], t.inputs[0])
    return t.outputs[0]


def f_attr(n, l):
    c = n.new("ShaderNodeCombineXYZ")
    for i, k in enumerate(("plddt", "u", "ss")):
        a = n.new("ShaderNodeAttribute")
        a.attribute_name, a.attribute_type = k, "GEOMETRY"
        l.new(a.outputs["Fac"], c.inputs[i])
    return c.outputs[0]


def f_attr2(n, l):
    c = n.new("ShaderNodeCombineXYZ")
    for i, k in enumerate(("side", "cross", "ss")):
        a = n.new("ShaderNodeAttribute")
        a.attribute_name, a.attribute_type = k, "GEOMETRY"
        l.new(a.outputs["Fac"], c.inputs[i])
    return c.outputs[0]


def m_light():
    m = bpy.data.materials.new("light")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    b, o = n.new("ShaderNodeBsdfDiffuse"), n.new("ShaderNodeOutputMaterial")
    b.inputs["Color"].default_value = (1, 1, 1, 1)
    l.new(b.outputs[0], o.inputs["Surface"])
    return m


def grab(path, sc):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    os.remove(path)
    return px.reshape(H, W, 4)[::-1]


def passes(sc, layers):
    out = {}
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
    sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
    sc.render.film_transparent = True
    c = sc.cycles
    c.use_adaptive_sampling = False
    allobs = [o for ob in layers.values() for o in ob]
    for name, obs in layers.items():
        for o in allobs:
            o.hide_render = o not in obs
        c.samples, c.use_denoising, c.filter_width, c.max_bounces = 1, False, 0.01, 0
        for tag, fn, typ in (("pos", f_pos, np.float32), ("nrm", f_nrm, np.float16), ("attr", f_attr, np.float32), ("attr2", f_attr2, np.float32)):
            if tag.startswith("attr") and "plddt" not in obs[0].data.attributes:
                continue
            m = mat_emit(fn, tag)
            for o in obs:
                o.data.materials.clear()
                o.data.materials.append(m)
            a = grab(OUT + f"_{TAG}_{tag}.exr", sc)
            out[f"{name}_{tag}"] = a[..., :3].astype(typ)
            out[f"{name}_mask"] = a[..., 3] > 0.5
        m = m_light()
        for o in obs:
            o.data.materials.clear()
            o.data.materials.append(m)
        c.samples, c.use_denoising, c.filter_width, c.max_bounces = 24, True, 1.5, 1
        c.denoiser = "OPENIMAGEDENOISE"
        a = grab(OUT + f"_{TAG}_light.exr", sc)
        out[f"{name}_light"] = a[..., 0].astype(np.float16)
        print("LAYER", name, "done")
    return out


def add_sun(direction, energy=3.14):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy, d.angle = energy, math.radians(6)
    o = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = Vector(direction).normalized().to_track_quat("Z", "Y").to_euler()
    return o


sc = gk.scene(w=W, h=H, samples=1, look="None")
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0

if NAME == "liver":
    skin = gk.liver_skin(voxel=0.015)
    portal, hep = gk.stl("portal_vein_hepatic"), gk.stl("hepatic_veins")
    cam = gk.camera((1.1, -14.0, -0.3), (0, 0, 0.0), lens=124, shift=(-0.170, 0.012))
    add_sun((-0.62, -0.55, 0.62))
    layers = {"liver": [skin], "portal": [portal], "hepatic": [hep]}
    if "--orbit" in argv:                 # motion test only: liver alone, camera turned about the body axis by this many degrees
        a = math.radians(opt("orbit", 0))
        loc = Matrix.Rotation(a, 3, "Z") @ Vector((1.1, -14.0, -0.3))
        cam = gk.camera(loc, (0, 0, 0.0), lens=124, shift=(-0.170, 0.012))
        layers = {"liver": [skin]}
        portal.hide_render = hep.hide_render = True
elif NAME == "protein":
    import prot_geo as G
    res = G.load()
    rib = G.ribbon(res, coil_r=0.34, helix_w=1.7, sheet_w=1.5, thick=0.42, arrow=1.7, seg=14, ring=16)
    # which face of the ribbon a vertex is on, and where across its width: read back from the ring order of prot_geo.ribbon
    me, ring = rib.data, 16
    nv = len(me.vertices)
    side, cross = [0.5] * nv, [0.5] * nv
    for i in range(nv - 2):
        th = 2 * math.pi * (i % ring) / ring
        side[i], cross[i] = (math.sin(th) + 1) / 2, (math.cos(th) + 1) / 2
    me.attributes.new("side", "FLOAT", "POINT").data.foreach_set("value", side)
    me.attributes.new("cross", "FLOAT", "POINT").data.foreach_set("value", cross)
    ctr = sum((r["ca"] for r in res[:302]), Vector()) / 302
    R = Euler((math.radians(opt("pitch", 0)), 0, math.radians(opt("yaw", 0))), "ZYX").to_matrix().to_4x4()
    rib.matrix_world = R @ Matrix.Translation(-ctr)
    bpy.context.view_layer.update()
    cam = gk.camera((0, -30, 0), (0, 0, 0), lens=opt("lens", 185), shift=(opt("sx", -0.206), opt("sy", -0.008)))
    add_sun((-0.6, -0.6, 0.6))
    layers = {"prot": [rib]}
elif NAME == "figure":
    bpy.ops.wm.stl_import(filepath=ROOT + "blender_lineart/_cache/skin_dec08_outer.stl")
    body = bpy.context.selected_objects[0]
    bb = np.array([body.matrix_world @ Vector(c) for c in body.bound_box])
    print("BODY", bb.min(0), bb.max(0))
    size = (bb.max(0) - bb.min(0)).max()
    k = 17.0 / size
    body.matrix_world = Matrix.Scale(k, 4) @ body.matrix_world
    bpy.context.view_layer.update()
    for p in body.data.polygons:
        p.use_smooth = True
    body.data.update()
    bb = bb * k
    ztop = bb[:, 2].max()
    cxb, cyb = (bb[:, 0].max() + bb[:, 0].min()) / 2, (bb[:, 1].max() + bb[:, 1].min()) / 2
    cam = gk.camera((cxb + 6.0, cyb - 26, ztop - 2.0), (cxb, cyb, ztop - 3.0), lens=85, shift=(-0.20, 0.0))
    add_sun((-0.7, -0.55, 0.55))
    layers = {"body": [body]}
else:
    raise SystemExit("unknown scene")

bpy.context.view_layer.update()
data = passes(sc, layers)
data["world_to_cam"] = np.array(cam.matrix_world.inverted(), np.float64)
data["cam_loc"] = np.array(cam.location, np.float64)
data["lens"] = cam.data.lens
data["sensor"] = cam.data.sensor_width
data["shift"] = np.array([cam.data.shift_x, cam.data.shift_y], np.float64)
data["wh"] = np.array([W, H])
np.savez(OUT + TAG + ".npz", **data)
print("SAVED", OUT + TAG + ".npz")
