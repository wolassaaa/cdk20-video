"""HKBU SCIE1007 coursework science video. Shared Blender scene for the art direction scouts: the real CDK20 surface from one fixed camera.

Inside a Blender script:
    import sys; sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
    from scene_cdk20 import build
    sc, ob, cam = build(1280, 720, samples=64)
    ob.data.materials.append(my_material); sc.render.filepath = "out.png"; bpy.ops.render.render(write_still=True)

The mesh carries the point attribute "conf" (pLDDT / 100), real per-residue confidence from AlphaFold DB v6. Scale is 1 unit = 10 Angstrom.
"""
import os

import bpy
import numpy as np
from mathutils import Vector

SURFACE = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/_work/cdk20_surface.npz"
SC = 0.1
VIEW = Vector((0.15, -0.25, 1.0)).normalized()  # same side as the M04 still, a little from below so the form has mass
DIST, LENS = 26.0, 70.0


def build(w=1920, h=1080, samples=32, engine="CYCLES"):
    D = np.load(SURFACE)
    verts, quads, conf = D["verts"] * SC, D["quads"], D["conf"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = engine
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.refresh_devices()
        for dv in prefs.devices:
            dv.use = dv.type == "OPTIX"
        sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "GPU", samples, False
        sc.cycles.use_adaptive_sampling = False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.film_transparent = True
    me = bpy.data.meshes.new("cdk20")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
    me.update()
    ob = bpy.data.objects.new("cdk20", me)
    sc.collection.objects.link(ob)
    c = Vector(((verts.min(0) + verts.max(0)) / 2).tolist())
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens, cam_d.clip_start, cam_d.clip_end = LENS, 1, 80
    cam = bpy.data.objects.new("cam", cam_d)
    cam.location = c + VIEW * DIST
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-VIEW).to_track_quat("-Z", "Y")
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, ob, cam


def emit_material(nt_builder, name="pass"):
    """Emission-only material; nt_builder(nodes, links) returns the socket to emit."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(nt_builder(nt.nodes, nt.links), em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m
