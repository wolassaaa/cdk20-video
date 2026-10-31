"""HKBU SCIE1007 coursework science video. manual: greys for two stills, nothing else. T1: the real BodyParts3D liver, front view, so the big right lobe lands on the left of the frame. T2: a stand-in sitter from the BodyParts3D skin mesh, used only until the team films. Raw light passes go to _work; the print look is made in T1.py and T2.py."""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "_work")
ASSET = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "assets", "anatomy"))
which = sys.argv[sys.argv.index("--") + 1]


def setup(w, h, spp=64):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"
    pr.refresh_devices()
    for d in pr.devices:
        d.use = d.type == "OPTIX"
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device, s.cycles.samples = "GPU", spp
    s.cycles.use_denoising, s.cycles.denoiser = True, "OPTIX"
    s.cycles.max_bounces, s.cycles.diffuse_bounces = 4, 3
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.film_transparent = True
    s.view_settings.view_transform, s.view_settings.look = "Standard", "None"
    i = s.render.image_settings
    i.file_format, i.color_mode, i.color_depth = "PNG", "RGBA", "8"
    wd = bpy.data.worlds.new("w")
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    s.world = wd
    return s


def clay(me, v=0.6):
    m = bpy.data.materials.new("c")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (v, v, v, 1)
    b.inputs["Roughness"].default_value = 0.42
    me.materials.append(m)


def cam(pos, tgt, lens):
    c = bpy.data.cameras.new("c")
    c.lens = lens
    o = bpy.data.objects.new("c", c)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o


def area(name, pos, tgt, size, power):
    l = bpy.data.lights.new(name, "AREA")
    l.size, l.energy = size, power
    o = bpy.data.objects.new(name, l)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def shot(s, lights, on, name):
    for k, o in lights.items():
        o.hide_render = k != on
    s.render.filepath = os.path.join(WORK, name)
    bpy.ops.render.render(write_still=True)


if which == "liver":
    s = setup(1800, 1300)
    bpy.ops.wm.stl_import(filepath=os.path.join(ASSET, "bp3d_v4_groups_stl", "liver_parenchyma_segments.stl").replace("\\", "/"))
    o = bpy.context.selected_objects[0]
    me = o.data
    C = Vector((-10.35, -122.87, 1105.54))
    for v in me.vertices:
        v.co = (v.co - C) * 0.01
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0015)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    r = o.modifiers.new("fuse", "REMESH")  # the source is cut into segments; fuse them so the seams do not read as stitching
    r.mode, r.voxel_size, r.use_smooth_shade = "VOXEL", 0.016, True
    q = o.modifiers.new("sm", "SMOOTH")
    q.iterations, q.factor = 24, 0.7
    clay(me)
    # BodyParts3D: patient's right is -x, front is -y. Camera on -y keeps +x on screen right, so the right lobe falls on the left of the frame
    az, el, d = math.radians(-8), math.radians(4), 6.6
    t = Vector((0, 0, -0.05))
    cam(tuple(t + d * Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))), tuple(t), 62)
    L = dict(key=area("key", (-5.2, -2.8, 3.8), (0, 0, 0), 2.0, 380), low=area("low", (4.2, -3.2, -2.4), (0, 0, 0), 3, 150))
    shot(s, L, "key", "liver_key.png")
    shot(s, L, "low", "liver_low.png")
else:
    s = setup(1000, 1100)
    bpy.ops.wm.stl_import(filepath=os.path.join(ASSET, "..", "..", "..", "镜头设计_v2", "tests", "T5_body", "assets", "FMA7163_skin.stl").replace("\\", "/"))
    o = bpy.context.selected_objects[0]
    me = o.data
    zs = [v.co.z for v in me.vertices]
    zt = max(zs)
    hd = [v.co for v in me.vertices if v.co.z > zt - 180]
    C = sum(hd, Vector()) / len(hd)
    print("head centre", C, "top", zt)
    for v in me.vertices:
        v.co = (v.co - C) * 0.01
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    q = o.modifiers.new("sm", "SMOOTH")
    q.iterations, q.factor = 6, 0.6
    clay(me, 0.7)
    a = math.radians(30)
    t = Vector((0.04, 0, -2.3))
    cam(tuple(t + 8.2 * Vector((-math.sin(a), -math.cos(a), 0.08))), tuple(t), 42)
    L = dict(key=area("key", (3.4, -3.6, 1.2), (0, 0, -0.8), 5.0, 300), fill=area("fill", (-4.5, -3.2, -0.2), (0, 0, -1.2), 6, 190))
    shot(s, L, "key", "sit_key.png")
    shot(s, L, "fill", "sit_fill.png")
