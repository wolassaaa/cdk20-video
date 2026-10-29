"""Shared Blender helpers for the s110 style frames (1-10 / 1-11 / W1). Blender 5.1, Cycles GPU (OPTIX)."""
import bpy, math, sys, argparse
from mathutils import Vector

CODE = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/"
FONTS = CODE + "fonts/"


def args(spec):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    for k, v in spec.items():
        ap.add_argument("--" + k, type=type(v), default=v)
    return ap.parse_args(argv)


def hex2lin(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (*[f(x) for x in c], a)


# reds are biased to crimson in 3D so AgX/Filmic never pushes them to orange (renders read as #FF3B1F or deeper)
VERM, BLUE, KLEIN, INK, BG, CYAN = "#E8102A", "#1F3BFF", "#002FA7", "#EDEBE4", "#060606", "#29F0FF"
VERM_S = "#FF1A2E"  # crimson-leaning red for lit surfaces (gloss, ink, thread)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def render_setup(scn, samples=256, w=1920, h=1080, pct=100, look="AgX - Punchy", exposure=0.0, bounces=12,
                 caustics=False, denoise=True, view="AgX"):
    scn.render.engine = "CYCLES"
    pref = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            pref.compute_device_type = dev; pref.get_devices(); ok = False
            for d in pref.devices:
                d.use = (d.type == dev); ok |= d.use
            if ok: break
        except Exception as e:
            print("device", dev, e)
    scn.cycles.device = "GPU"
    scn.cycles.samples = samples
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.use_denoising = denoise
    try: scn.cycles.denoiser = "OPTIX"   # keep denoising on the GPU (CPU is shared)
    except Exception: scn.cycles.denoiser = "OPENIMAGEDENOISE"
    scn.cycles.max_bounces = bounces; scn.cycles.transmission_bounces = bounces; scn.cycles.glossy_bounces = 6
    scn.cycles.transparent_max_bounces = 24; scn.cycles.volume_bounces = 1
    scn.cycles.caustics_refractive = caustics; scn.cycles.caustics_reflective = caustics
    scn.cycles.blur_glossy = 0.6
    scn.render.threads_mode = "FIXED"; scn.render.threads = 4
    scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = w, h, pct
    scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_depth = "16"
    vs = scn.view_settings
    vs.view_transform = view
    try: vs.look = look if view == "AgX" else "None"
    except Exception as e: print("look", e)
    vs.exposure = exposure
    w_ = bpy.data.worlds.new("W"); scn.world = w_; w_.use_nodes = True
    bg = w_.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0, 0, 0, 1); bg.inputs[1].default_value = 0
    return w_


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def principled(name, color=INK, rough=0.4, metal=0.0, transmission=0.0, ior=1.45, coat=0.0, sss=0.0, emission=None, estrength=0.0,
               dispersion=0.0, alpha=1.0):
    m, nt, out = mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = hex2lin(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.6, 0.4, 0.3)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if emission:
        b.inputs["Emission Color"].default_value = hex2lin(emission)
        b.inputs["Emission Strength"].default_value = estrength
    if dispersion and "Dispersion" in b.inputs:
        b.inputs["Dispersion"].default_value = dispersion
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, nt, b, out


def emissive(name, color, strength):
    m, nt, out = mat(name)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = hex2lin(color) if isinstance(color, str) else color
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m)


def plane(name, size, loc, rot=(0, 0, 0), m=None, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    if m: assign(o, m)
    return o


def light_panel(name, color, strength, loc, size, look_at=(0, 0, 0), shape="RECTANGLE", size_y=None, visible=False, spread=180):
    d = bpy.data.lights.new(name, "AREA"); d.color = hex2lin(color)[:3] if isinstance(color, str) else color
    d.energy = strength; d.shape = shape; d.size = size
    if size_y: d.size_y = size_y
    d.spread = math.radians(spread)
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = loc; aim(o, look_at)
    o.visible_camera = visible
    return o


def spot(name, color, energy, loc, look_at, size_deg=30, blend=0.3, radius=0.05):
    d = bpy.data.lights.new(name, "SPOT"); d.color = hex2lin(color)[:3]; d.energy = energy
    d.spot_size = math.radians(size_deg); d.spot_blend = blend; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = loc; aim(o, look_at); return o


def aim(o, target):
    d = Vector(target) - Vector(o.location)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(loc, target, lens=50, fstop=0.0, focus=None, sensor=36, shift=(0, 0)):
    c = bpy.data.cameras.new("Cam"); c.lens = lens; c.sensor_width = sensor
    c.shift_x, c.shift_y = shift
    o = bpy.data.objects.new("Cam", c); bpy.context.scene.collection.objects.link(o)
    o.location = loc; aim(o, target)
    if fstop > 0:
        c.dof.use_dof = True; c.dof.aperture_fstop = fstop
        c.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = o
    return o


def text3d(body, font, size=1.0, extrude=0.0, bevel=0.0, loc=(0, 0, 0), rot=(math.pi / 2, 0, 0), align="CENTER", spacing=1.0, m=None,
           res=12, valign="CENTER"):
    cu = bpy.data.curves.new("T", "FONT"); cu.body = body
    cu.font = bpy.data.fonts.load(FONTS + font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    cu.align_x = align; cu.align_y = valign; cu.space_character = spacing; cu.resolution_u = res
    o = bpy.data.objects.new("T_" + body[:10], cu); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if m: cu.materials.append(m)
    return o


def save(scn, path):
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("SAVED", path)
