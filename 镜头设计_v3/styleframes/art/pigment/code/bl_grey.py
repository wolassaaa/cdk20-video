"""HKBU SCIE1007 coursework science video. Pigment direction: grey light passes for the printed stills, no colour here, the inks are added in comp.py.

Run: bash gpu_slot.sh blender -b -t 4 -P bl_grey.py -- --shot cdk20|liver|cdk20turn --out <dir> [--pct 100] [--samples 64] [--ppa 17] [--xc 960] [--yc 540]
cdk20: real AlphaFold surface. Writes cdk20_shade (sun + sky), cdk20_sky (sky only, reads as occlusion), cdk20_conf (real pLDDT per vertex, raw 0-1).
liver: BodyParts3D meshes. Writes liver_shade, liver_sky, vess_shade (vessels alone), vess_id (R veins, G artery, B bile ducts).
Standard view with film transparent, so a grey value here is the tone the screen in comp.py receives.
"""
import argparse, json, math, os, sys, time
import bpy
import numpy as np
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--ppa", type=float, default=17)     # px per Angstrom at 1080p for cdk20, px per mm for the liver
ap.add_argument("--xc", type=float, default=960)
ap.add_argument("--yc", type=float, default=540)
ap.add_argument("--az", type=float, default=0)       # liver: turn about the body axis, degrees
ap.add_argument("--el", type=float, default=0)       # liver: tilt, degrees, negative looks up from below
ap.add_argument("--roll", type=float, default=0)
ap.add_argument("--frames", type=int, default=0)     # cdk20turn
ap.add_argument("--deg", type=float, default=14)     # cdk20turn: total turn
A = ap.parse_args(argv)
OUT = A.out.rstrip("/\\")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples = "GPU", A.samples
c_.use_adaptive_sampling = False
c_.use_denoising, c_.denoiser = True, "OPTIX"
c_.max_bounces, c_.diffuse_bounces, c_.glossy_bounces, c_.transmission_bounces, c_.volume_bounces = 4, 4, 0, 0, 0
c_.caustics_reflective, c_.caustics_refractive = False, False
c_.seed, c_.use_animated_seed = 0, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 3840, 2160, A.pct
sc.render.film_transparent = True
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.view_settings.exposure, sc.view_settings.gamma = 0, 1
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth, st.compression = "PNG", "RGBA", "8", 30

w = bpy.data.worlds.new("w")
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
sc.world = w


def diffuse(name, grey=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    d, o = nt.nodes.new("ShaderNodeBsdfDiffuse"), nt.nodes.new("ShaderNodeOutputMaterial")
    d.inputs["Color"].default_value = (grey, grey, grey, 1)
    nt.links.new(d.outputs[0], o.inputs["Surface"])
    return m


def emit(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    d, o = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    d.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(d.outputs[0], o.inputs["Surface"])
    return m


def sun(vec, energy, angle=5):
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy, ld.angle = energy * math.pi, math.radians(angle)
    o = bpy.data.objects.new("sun", ld)
    o.rotation_euler = Vector(vec).normalized().to_track_quat("Z", "Y").to_euler()
    sc.collection.objects.link(o)
    return o


def shot(path, raw=False):
    sc.view_settings.view_transform = "Raw" if raw else "Standard"
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"wrote {path} in {time.time() - t:.1f} s", flush=True)


if A.shot.startswith("cdk20"):
    SC = 0.1
    D = np.load(os.path.join(V3, "styleframes", "S2plus", "_work", "cdk20_surface.npz"))
    verts, quads, conf = D["verts"] * SC, D["quads"], D["conf"]
    print("cdk20 extent, A:", (verts.min(0) / SC).round(1), (verts.max(0) / SC).round(1), len(verts), len(quads), flush=True)
    me = bpy.data.meshes.new("cdk20")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
    me.update()
    ob = bpy.data.objects.new("cdk20", me)
    sc.collection.objects.link(ob)
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
    cam_d.ortho_scale = 1080 / A.ppa * SC
    cam_d.clip_start, cam_d.clip_end = 0.01, 60
    cam = bpy.data.objects.new("cam", cam_d)
    cam.location = ((960 - A.xc) / A.ppa * SC, (A.yc - 540) / A.ppa * SC, 25)
    sc.collection.objects.link(cam)
    sc.camera = cam

    grey = diffuse("grey")
    me.materials.append(grey)
    key = sun((-0.80, 0.52, 0.30), 1.05, 6)

    if A.shot == "cdk20turn":
        pivot = bpy.data.objects.new("pivot", None)
        sc.collection.objects.link(pivot)
        ob.parent = pivot
        bg.inputs[1].default_value = 0.22
        cm = bpy.data.materials.new("conf")
        cm.use_nodes = True
        nt = cm.node_tree
        nt.nodes.clear()
        a, e, o = nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
        a.attribute_name, a.attribute_type = "conf", "GEOMETRY"
        nt.links.new(a.outputs["Fac"], e.inputs["Color"])
        nt.links.new(e.outputs[0], o.inputs["Surface"])
        for i in range(A.frames):
            pivot.rotation_euler = (0, math.radians(-A.deg / 2 + A.deg * i / max(A.frames - 1, 1)), 0)
            me.materials[0] = grey
            key.hide_render = False
            bg.inputs[1].default_value = 0.22
            c_.samples, c_.use_denoising = A.samples, True
            shot(f"{OUT}/turn_{i:04d}.png")
            me.materials[0] = cm
            key.hide_render = True
            bg.inputs[1].default_value = 0.0
            c_.samples, c_.use_denoising = 8, False
            shot(f"{OUT}/tconf_{i:04d}.png", raw=True)
        sys.exit(0)

    bg.inputs[1].default_value = 0.22
    shot(f"{OUT}/cdk20_shade.png")
    key.hide_render = True
    bg.inputs[1].default_value = 1.0
    shot(f"{OUT}/cdk20_sky.png")
    m = bpy.data.materials.new("conf")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    a, e, o = nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    a.attribute_name, a.attribute_type = "conf", "GEOMETRY"
    nt.links.new(a.outputs["Fac"], e.inputs["Color"])
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    me.materials[0] = m
    bg.inputs[1].default_value = 0.0
    c_.samples, c_.use_denoising = 16, False
    shot(f"{OUT}/cdk20_conf.png", raw=True)

elif A.shot == "liver":
    ST = os.path.join(V3, "assets", "anatomy", "bp3d_v4_groups_stl")
    SC = 0.01  # 1 mm -> 0.01 m
    groups = dict(liver=["liver_parenchyma_segments"], veins=["hepatic_veins", "portal_vein_hepatic"], art=["hepatic_artery"], bile=["intrahepatic_bile_ducts"], gall=["gallbladder"])
    objs = {}
    for g, names in groups.items():
        objs[g] = []
        for n in names:
            bpy.ops.wm.stl_import(filepath=os.path.join(ST, n + ".stl"), global_scale=SC)
            o = bpy.context.selected_objects[0]
            bpy.ops.object.shade_smooth()
            objs[g].append(o)
    pts = np.array([list(o.matrix_world @ Vector(c)) for o in objs["liver"] for c in o.bound_box])
    lo, hi = pts.min(0), pts.max(0)
    mid = (lo + hi) / 2
    print("liver box, mm:", (lo / SC).round(1), (hi / SC).round(1), flush=True)
    # camera in front of the body (-Y looks to +Y in BodyParts3D), turned about the body axis by az, tilted by el
    az, el, roll = math.radians(A.az), math.radians(A.el), math.radians(A.roll)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
    cam_d.ortho_scale = 1080 / A.ppa * SC
    cam_d.clip_start, cam_d.clip_end = 0.01, 40
    cam = bpy.data.objects.new("cam", cam_d)
    q = (-d).to_track_quat("-Z", "Y") @ Euler((0, 0, roll)).to_quaternion()
    cam.rotation_euler = q.to_euler()
    right, up = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    cam.location = Vector(mid) + d * 8 + right * ((960 - A.xc) / A.ppa * SC) + up * ((A.yc - 540) / A.ppa * SC)
    sc.collection.objects.link(cam)
    sc.camera = cam

    grey, vgrey = diffuse("grey"), diffuse("vgrey", 0.65)
    for g, L in objs.items():
        for o in L:
            o.data.materials.append(grey if g in ("liver", "gall") else vgrey)
    vess = objs["veins"] + objs["art"] + objs["bile"]
    key = sun((d.x * 0.3 + right.x * 0.62 + up.x * 0.72, d.y * 0.3 + right.y * 0.62 + up.y * 0.72, d.z * 0.3 + right.z * 0.62 + up.z * 0.72), 1.0, 7)
    bg.inputs[1].default_value = 0.16
    for o in vess:
        o.hide_render = True
    shot(f"{OUT}/liver_shade.png")
    key.hide_render = True
    bg.inputs[1].default_value = 1.0
    shot(f"{OUT}/liver_sky.png")
    # vessels alone, the parenchyma gone, for the x-ray overlay
    for o in objs["liver"] + objs["gall"]:
        o.hide_render = True
    for o in vess:
        o.hide_render = False
    key.hide_render = False
    bg.inputs[1].default_value = 0.3
    shot(f"{OUT}/vess_shade.png")
    key.hide_render = True
    bg.inputs[1].default_value = 0.0
    ids = dict(veins=emit("r", (1, 0, 0)), art=emit("g", (0, 1, 0)), bile=emit("b", (0, 0, 1)))
    for g in ("veins", "art", "bile"):
        for o in objs[g]:
            o.data.materials[0] = ids[g]
    c_.samples, c_.use_denoising = 16, False
    shot(f"{OUT}/vess_id.png", raw=True)
    # bile ducts alone, so the yellow tree is whole and not cut by the veins in front of it
    for o in objs["veins"] + objs["art"]:
        o.hide_render = True
    shot(f"{OUT}/bile_id.png", raw=True)
print("DONE", flush=True)
