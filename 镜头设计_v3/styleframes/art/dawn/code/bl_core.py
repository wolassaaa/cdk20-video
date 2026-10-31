"""HKBU SCIE1007 coursework science video, dawn art direction. Shared Blender helpers for the concept stills.

Every shot is rendered as white-light layers (one light on at a time) and saved as float .npy, so colour and exposure are chosen afterwards in comp.py without another GPU run.
The horizon is held at y = 720 of 1080 by a level camera with lens shift, whatever the focal length, so all shots share one line.
"""
import math, os, time
import bpy
import numpy as np
from mathutils import Vector

H_Y = 720
W, H = 1920, 1080


def setup(samples=128, pct=100):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.refresh_devices()
    for dv in prefs.devices:
        dv.use = dv.type == "OPTIX"
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    c = sc.cycles
    c.device, c.samples = "GPU", samples
    c.use_adaptive_sampling, c.adaptive_threshold = True, 0.02
    c.use_denoising, c.denoiser, c.denoising_input_passes = True, "OPTIX", "RGB_ALBEDO_NORMAL"
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.volume_bounces = 4, 3, 2, 2, 0
    c.caustics_reflective, c.caustics_refractive = False, False
    c.seed, c.use_animated_seed = 0, False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, pct
    sc.render.film_transparent = True
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    sc.world = w
    return sc


def set_world(strength, rgb=(1, 1, 1)):
    w = bpy.context.scene.world
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*rgb, 1)
    bg.inputs[1].default_value = strength


def camera(loc, focal, yaw_deg=0.0, shift_x=0.0, sensor=36.0, clip=(0.02, 4000)):
    """Level camera looking along +Y turned by yaw. shift_y puts the horizon at H_Y."""
    d = bpy.data.cameras.new("cam")
    d.lens, d.sensor_width, d.sensor_fit = focal, sensor, "HORIZONTAL"
    d.shift_y = (H_Y - H / 2) / W
    d.shift_x = shift_x
    d.clip_start, d.clip_end = clip
    o = bpy.data.objects.new("cam", d)
    o.location = loc
    o.rotation_euler = (math.pi / 2, 0, math.radians(-yaw_deg))
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o


def sun(name, az_deg, el_deg, angle=1.5, energy=math.pi):
    """az 0 = straight ahead of an unturned camera (+Y), positive to the right. energy pi = radiance 1 on a white face square to it."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    v = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.angle = energy, math.radians(angle)
    o = bpy.data.objects.new(name, d)
    o.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)
    return o


def mesh(name, verts, faces, mat=None, smooth=True, attrs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(verts).tolist(), [], np.asarray(faces).tolist())
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    for k, v in (attrs or {}).items():
        me.attributes.new(k, "FLOAT", "POINT").data.foreach_set("value", np.asarray(v, float).tolist())
    me.update()
    if mat:
        me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def diffuse(name, rgb=(0.8, 0.8, 0.8), rough=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.2
    return m


def emission(name, rgb=(1, 1, 1), strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e, o = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs[0].default_value = (*rgb, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def data_material(scale):
    """Debug-free data pass: R camera distance / scale, G world z / scale, B the conf attribute (0 where a mesh has none). Emission, so one sample is exact."""
    m = bpy.data.materials.new("data")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    cam, geo, at = nt.nodes.new("ShaderNodeCameraData"), nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name, at.attribute_type = "conf", "GEOMETRY"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    com = nt.nodes.new("ShaderNodeCombineXYZ")

    def div(sock, k):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = "DIVIDE"
        L(sock, n.inputs[0])
        n.inputs[1].default_value = k
        return n.outputs[0]

    L(div(cam.outputs["View Distance"], scale), com.inputs[0])
    L(div(sep.outputs["Z"], scale), com.inputs[1])
    L(at.outputs["Fac"], com.inputs[2])
    e, o = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    L(com.outputs[0], e.inputs[0])
    L(e.outputs[0], o.inputs[0])
    return m


def _grab(path):
    sc = bpy.context.scene
    tmp = path + ".exr"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    a = a.reshape(h, w, 4)[::-1].astype(np.float16)
    np.save(path + ".npy", a)
    os.remove(tmp)


def layers(out, shot, plan, lights, data_scale=None):
    """plan: {layer name: (world strength, [light names on])}. Everything off except what the layer names."""
    sc = bpy.context.scene
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    for name, (ws, on) in plan.items():
        set_world(ws)
        for o in lights:
            o.hide_render = o.name not in on
        t = time.time()
        _grab(os.path.join(out, f"{shot}_{name}"))
        print(f"LAYER {shot}_{name} {time.time() - t:.1f}s", flush=True)
    if data_scale:
        c = sc.cycles
        keep = c.samples, c.use_denoising, c.use_adaptive_sampling
        c.samples, c.use_denoising, c.use_adaptive_sampling = 8, False, False
        for o in lights:
            o.hide_render = True
        set_world(0)
        sc.view_layers[0].material_override = data_material(data_scale)
        _grab(os.path.join(out, f"{shot}_data"))
        sc.view_layers[0].material_override = None
        c.samples, c.use_denoising, c.use_adaptive_sampling = keep
    print(f"DONE {shot} {time.time() - t0:.1f}s", flush=True)
