"""Shared Blender helpers for the W0 / 1-01 options (Blender 5.1, Cycles GPU OPTIX).
Run one Blender at a time:  blender.exe -b --factory-startup -t 4 -P optX.py -- --shot hit1 --out X.png
"""
import bpy, bmesh, sys, math, argparse
from mathutils import Vector

ANAT = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
LIVER_C = Vector((-10.35, -122.87, 1105.54))


def args(extra=None):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="hit1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--exposure", type=float, default=0.0)
    if extra: extra(ap)
    return ap.parse_args(argv)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def gpu(scn, samples, pct=100, transparent=False, view="AgX", look="AgX - Base Contrast", exposure=0.0):
    scn.render.engine = "CYCLES"
    pref = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            pref.compute_device_type = dev; pref.get_devices(); ok = False
            for d in pref.devices:
                d.use = (d.type == dev); ok |= d.use
            if ok: break
        except Exception as e: print("device", dev, e)
    scn.cycles.device = "GPU"
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = "OPENIMAGEDENOISE"
    try: scn.cycles.denoising_use_gpu = True
    except Exception: pass
    scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16; scn.cycles.glossy_bounces = 6
    scn.cycles.transparent_max_bounces = 32; scn.cycles.volume_bounces = 1
    scn.cycles.blur_glossy = 0.5
    scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = pct
    scn.render.film_transparent = transparent
    vs = scn.view_settings
    vs.view_transform = view
    try: vs.look = look
    except Exception as e: print("look", e)
    vs.exposure = exposure
    st = scn.render.image_settings
    st.file_format = "PNG"; st.color_mode = "RGBA" if transparent else "RGB"; st.color_depth = "16"


def render(scn, out):
    import time
    scn.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("RENDER %.1fs -> %s" % (time.time() - t, out))


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out


def emission(name, rgb, strength):
    m, nt, out = mat(name)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def principled(name, rgb, rough=0.5, **kw):
    m, nt, out = mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, nt, b


def volume(name, rgb, density, aniso=0.0, absorb=None):
    m, nt, out = mat(name)
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*rgb, 1); v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = aniso
    if absorb: v.inputs["Absorption Color"].default_value = (*absorb, 1)
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    return m


def camera(scn, pos, tgt, lens=50, fstop=None, focus=None):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens
    c = bpy.data.objects.new("cam", cd); scn.collection.objects.link(c); scn.camera = c
    c.location = Vector(pos)
    c.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    if fstop:
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus if focus else (Vector(tgt) - Vector(pos)).length
    return c


def area(scn, name, power, size, pos, tgt, rgb=(1, 1, 1), size_y=None, cam_vis=False, spread=None):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.color = rgb
    ld.shape = "RECTANGLE"; ld.size = size; ld.size_y = size_y or size
    if spread: ld.spread = math.radians(spread)
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    o.location = Vector(pos); o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = cam_vis
    return o


def spot(scn, name, power, pos, tgt, rgb=(1, 1, 1), angle=30, blend=0.3, radius=0.05):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = power; ld.color = rgb
    ld.spot_size = math.radians(angle); ld.spot_blend = blend; ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    o.location = Vector(pos); o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def point(scn, name, power, pos, rgb=(1, 1, 1), radius=0.05):
    ld = bpy.data.lights.new(name, "POINT"); ld.energy = power; ld.color = rgb; ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    o.location = Vector(pos)
    return o


def world(scn, rgb=(0, 0, 0), strength=1.0, vol=None):
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (*rgb, 1); bg.inputs["Strength"].default_value = strength
    return w


def box(scn, name, size, loc, m=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if m: o.data.materials.append(m)
    return o


def load_stl(name, scale=0.01, keep=None, smooth=True):
    bpy.ops.wm.stl_import(filepath=ANAT + name + ".stl")
    o = bpy.context.selected_objects[0]; o.name = name
    me = o.data
    for v in me.vertices: v.co = (v.co - LIVER_C) * scale
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    if keep:
        bad = [v for v in bm.verts if not keep(v.co / scale + LIVER_C)]
        bmesh.ops.delete(bm, geom=bad, context="VERTS")
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return o


# palette (linear-ish values for Blender; sRGB hex -> linear)
def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


RED = lin("FF2A14"); VERM = lin("E8190F"); IKB = lin("002FA7"); BLUE = lin("1F3BFF"); BONE = lin("EDEBE4")
