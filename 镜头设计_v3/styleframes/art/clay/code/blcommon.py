"""HKBU SCIE1007 coursework science video. Group E style scouts: Blender helpers (fast mesh building, text to mesh, cycles setup)."""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FONTS, OUT, load_surface  # noqa: E402


def reset(w=1280, h=720, samples=128, engine="CYCLES", denoise=True, transparent=False, bounces=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.refresh_devices()
        for dv in prefs.devices:
            dv.use = dv.type == "OPTIX"
        c = sc.cycles
        c.device, c.samples = "GPU", samples
        c.use_adaptive_sampling = False
        c.use_denoising = denoise
        if denoise:
            c.denoiser = "OPENIMAGEDENOISE"
        if bounces:
            c.max_bounces = bounces
            c.transmission_bounces = bounces
            c.glossy_bounces = bounces
            c.transparent_max_bounces = bounces
    return sc


def add_mesh(name, v, q, smooth=True, tris=False):
    """Build a mesh quickly from numpy arrays; q is N x 4 (or N x 3 with tris=True)."""
    me = bpy.data.meshes.new(name)
    n = 3 if tris else 4
    me.vertices.add(len(v))
    me.vertices.foreach_set("co", np.asarray(v, np.float32).ravel())
    me.loops.add(len(q) * n)
    me.loops.foreach_set("vertex_index", np.asarray(q, np.int32).ravel())
    me.polygons.add(len(q))
    me.polygons.foreach_set("loop_start", np.arange(0, len(q) * n, n, dtype=np.int32))
    me.update(calc_edges=True)
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
        me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def add_attr(ob, name, values, kind="FLOAT", domain="POINT"):
    a = ob.data.attributes.new(name, kind, domain)
    key = "value" if kind == "FLOAT" else "vector" if kind == "FLOAT_VECTOR" else "color"
    a.data.foreach_set(key, np.asarray(values, np.float32).ravel())


def camera(loc, look, lens=50, dof=None, fstop=2.8, sensor=36):
    d = bpy.data.cameras.new("cam")
    d.lens, d.clip_start, d.clip_end, d.sensor_width = lens, 0.05, 2000, sensor
    cam = bpy.data.objects.new("cam", d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(loc)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y")
    if dof is not None:
        d.dof.use_dof, d.dof.focus_distance, d.dof.aperture_fstop = True, dof, fstop
    bpy.context.scene.camera = cam
    return cam


def sun(rot, energy, color=(1, 1, 1), angle=1.0):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy, d.color, d.angle = energy, color, np.radians(angle)
    ob = bpy.data.objects.new("sun", d)
    ob.rotation_euler = np.radians(rot)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def area(loc, look, energy, size=5, color=(1, 1, 1), shape="SQUARE"):
    d = bpy.data.lights.new("area", "AREA")
    d.energy, d.size, d.color, d.shape = energy, size, color, shape
    ob = bpy.data.objects.new("area", d)
    ob.location = Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y")
    bpy.context.scene.collection.objects.link(ob)
    return ob


def world_rgb(color, strength=1.0):
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    bpy.context.scene.world = w
    return w


def principled(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for k, val in kw.items():
        p.inputs[k.replace("_", " ")].default_value = val
    return m, p


def text3d(txt, font="ariblk.ttf", size=1.0, extrude=0.1, bevel=0.0, bevel_res=3, align="CENTER", resolution=6, space=1.0):
    """Text object converted to a mesh object lying in XY (reads from +Z)."""
    cu = bpy.data.curves.new("t", "FONT")
    cu.body = txt
    cu.font = bpy.data.fonts.load(os.path.join(FONTS, font))
    cu.size, cu.extrude, cu.bevel_depth, cu.bevel_resolution = size, extrude, bevel, bevel_res
    cu.align_x, cu.align_y, cu.resolution_u = align, "CENTER", resolution
    cu.space_character = space
    ob = bpy.data.objects.new("t", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    out = bpy.data.objects.new("text", me)
    bpy.context.scene.collection.objects.link(out)
    return out


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = me
    return ob


def remesh_smooth(ob, voxel=0.02, smooth=0, factor=0.5):
    r = ob.modifiers.new("r", "REMESH")
    r.mode, r.voxel_size, r.use_smooth_shade = "VOXEL", voxel, True
    if smooth:
        s = ob.modifiers.new("s", "SMOOTH")
        s.factor, s.iterations = factor, smooth
    return apply_mods(ob)


def rot_mesh(v, R, c=None):
    return (v - (0 if c is None else c)) @ np.asarray(R).T


def render(sc, name):
    os.makedirs(OUT, exist_ok=True)
    path = str(OUT / name)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
