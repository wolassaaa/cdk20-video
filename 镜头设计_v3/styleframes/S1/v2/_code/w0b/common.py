"""Shared Blender helpers for the w0b options (opt7 angiogram, opt8 glass-vessels, opt9 endoscope).

Opens blender/s1/move/s1_move.blend (real BodyParts3D anatomy, CC BY 4.0, re-centred on the liver, mm units):
  portal_system  - SMV + splenic + portal trunk + intrahepatic portal tree, with point attrs
                   'd' (geodesic dye distance from the SMV tip, mm; hilum 219, farthest tip 338) and 'm' (main path mask)
  hepatic_veins, liver_parenchyma_segments
Camera arrays (follow-cam along the portal vein) come from timeline_debug.npz of the same build.
"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOVE = os.path.normpath(os.path.join(HERE, "../../../../../blender/s1/move"))
META = json.load(open(os.path.join(MOVE, "scene_meta.json")))
TL = np.load(os.path.join(MOVE, "timeline_debug.npz"))
D_HILUM, D_MAX = META["D_HILUM"], META["D_MAX"]
SPOTS = [Vector(p) for p in META["SPOTS"]]

def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    d = {}
    i = 0
    while i < len(a):
        if a[i].startswith("--"):
            k = a[i][2:]
            if i + 1 < len(a) and not a[i + 1].startswith("--"):
                d[k] = a[i + 1]; i += 2
            else:
                d[k] = "1"; i += 1
        else: i += 1
    return d

def hexc(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]   # sRGB -> linear
    return (*c, a)

CRIMSON = hexc("E0102A"); BONE = hexc("EDEBE4"); BLUE = hexc("1F3BFF"); IKB = hexc("002FA7")

def load():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(MOVE, "s1_move.blend"))
    for o in list(bpy.data.objects):
        if o.name.startswith("spot_halo"): bpy.data.objects.remove(o)
    for o in bpy.data.objects:
        o.animation_data_clear()
        if o.type == 'CAMERA': o.data.animation_data_clear()
    for m in list(bpy.data.materials): m.animation_data_clear()
    for ng in bpy.data.node_groups: ng.animation_data_clear()
    for o in bpy.data.objects:
        if o.type == 'MESH': o.data.materials.clear()
    return {o.name: o for o in bpy.data.objects}

def cycles(samples=256, w=1920, h=1080, denoise=True, bounces=None, transp=64):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices: d.use = (d.type == 'OPTIX')
    s.cycles.device = 'GPU'
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.01
    s.cycles.use_denoising = denoise
    if denoise: s.cycles.denoiser = 'OPTIX'
    s.cycles.transparent_max_bounces = transp
    if bounces:
        s.cycles.max_bounces = bounces
        s.cycles.glossy_bounces = bounces; s.cycles.transmission_bounces = bounces
        s.cycles.diffuse_bounces = 2; s.cycles.volume_bounces = 2
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = w, h, 100
    s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
    s.view_settings.exposure = 0; s.view_settings.gamma = 1
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_depth = '16'
    s.render.image_settings.color_mode = 'RGB'
    s.render.film_transparent = False
    w_ = bpy.data.worlds.new("w") if not s.world else s.world
    s.world = w_; w_.use_nodes = True
    bg = w_.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0, 0, 0, 1); bg.inputs[1].default_value = 0
    s.frame_set(1)

def camera(loc, target, lens=40, shift_x=0.0, shift_y=0.0, roll=0.0, dof=None, fstop=4.0):
    cam = bpy.data.objects["cam"]; cd = cam.data
    cd.lens = lens; cd.shift_x = shift_x; cd.shift_y = shift_y
    cd.clip_start = 0.2; cd.clip_end = 5000
    cam.rotation_mode = 'QUATERNION'
    loc, target = Vector(loc), Vector(target)
    q = (target - loc).to_track_quat('-Z', 'Y')
    if roll:
        from mathutils import Quaternion
        q = q @ Quaternion((0, 0, 1), roll)
    cam.location = loc; cam.rotation_quaternion = q
    cd.dof.use_dof = dof is not None
    if dof is not None: cd.dof.focus_distance = dof; cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = cam
    return cam

def tl_cam(frame):
    return TL["cam"][frame], TL["target"][frame]

def centreline(o, step=2.0, smax=None):
    """Ring centroids of the single SMV -> portal trunk path at geodesic distance s (mm).
    Also writes point attr 'p' = 1 on that path + the intrahepatic tree, 0 on splenic vein / side tributaries / bottom hook."""
    sys.path.insert(0, MOVE); import geo
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    d = np.empty(n, np.float32); me.attributes["d"].data.foreach_get("value", d)
    m = np.empty(n, np.float32); me.attributes["m"].data.foreach_get("value", m)
    ev = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", ev)
    lab = geo.islands(n, ev.reshape(-1, 2).tolist())
    spl = lab == lab[int(co[:, 0].argmax())]
    ok = (m > 0.5) & ~spl
    S = np.arange(50.0, smax or D_HILUM, step)
    pts, prev = [], None
    for s in S:
        sel = ok & (np.abs(d - s) < 1.6)
        if prev is not None: sel &= np.linalg.norm(co - prev, axis=1) < 14
        if sel.sum() < 4:
            pts.append(prev); continue
        p = co[sel].mean(0); pts.append(p); prev = p
    P = np.array(pts)
    k = np.ones(5) / 5
    P = np.stack([np.convolve(np.pad(P[:, i], 2, mode='edge'), k, 'valid') for i in range(3)], 1)
    # smooth 'd' over the mesh (the build carried it from the base mesh by nearest vertex, so it is stepped)
    e = ev.reshape(-1, 2)
    deg = np.bincount(e.ravel(), minlength=n).astype(np.float32)
    ds = d.copy()
    for _ in range(25):
        acc = np.bincount(e[:, 0], weights=ds[e[:, 1]], minlength=n) + np.bincount(e[:, 1], weights=ds[e[:, 0]], minlength=n)
        ds = np.where(deg > 0, 0.5 * ds + 0.5 * acc / np.maximum(deg, 1), ds).astype(np.float32)
    me.attributes["d"].data.foreach_set("value", ds)
    pm = ok.astype(np.float32)
    at = me.attributes.get("p") or me.attributes.new("p", 'FLOAT', 'POINT')
    at.data.foreach_set("value", pm)
    return S, P, co, d

def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out

def attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = name; a.attribute_type = 'GEOMETRY'
    return a.outputs["Factor"] if "Factor" in a.outputs else a.outputs[2]

def math_(nt, op, a, b=0.0, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if hasattr(v, "links") or hasattr(v, "node"): nt.links.new(v, n.inputs[i])
        else: n.inputs[i].default_value = v
    return n.outputs[0]

def render(out):
    s = bpy.context.scene
    s.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out)

def path_mask(o, S, P, co, d):
    return np.array([v.value for v in o.data.attributes["p"].data])
