"""Shared Blender helpers for the W0 / 1-01 options (Blender 5.1, Cycles GPU OPTIX).
Run one Blender at a time:  blender.exe -b --factory-startup -t 4 -P optX.py -- --shot hit1 --out X.png
"""
import bpy, bmesh, sys, math, argparse, os, shutil, time
from mathutils import Vector

# the 镜头设计_v3 folder: found from this file, or set HKBU_V3 if the assets live elsewhere (a rented machine)
V3 = (os.environ.get("HKBU_V3") or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".."))).replace("\\", "/")
ANAT = V3 + "/assets/anatomy/bp3d_v4_groups_stl/"
LIVER_C = Vector((-10.35, -122.87, 1105.54))

# 4K batch flags, shared by every Cycles script. Each default leaves the script as it is, so a run without them renders what it always did.
RENDER_FLAGS = {
    "seed": -1,        # >=0: fixed Cycles seed, use_animated_seed off
    "denoiser": "",    # OPTIX | OIDN (OIDN: on the GPU, Accurate prefilter, High quality)
    "tile": 0,         # tile_size. 4096 keeps a 4K frame in one tile; the 2048 default splits it and caches tiles to disk
    "thresh": 0.0,     # >0: adaptive sampling threshold
    "caustics": -1,    # 0/1: refractive caustics. Reflective stays as the script set it.
    "out-format": "",  # png | jpg. Blender's JPEG is 4:2:0, so for 4:4:4 write png and convert with PIL.
    "resume": 0,       # 1: skip frames already on disk and whole. It cannot see settings, so give each setting its own --out.
    "vram-log": "",    # path: append nvidia-smi samples (csv) once a second
}
SEQ_FLAGS = {          # scripts with a timeline only
    "step": 1,         # render every Nth frame (drafts)
    "hold": 0,         # 1: copy each rendered frame over the skipped ones, so the sequence has no gaps
}
_flags = None          # the parsed flags: args() and apply_flags() set them, gpu() and render() read them


def add_render_flags(ap, seq=False):
    """A flag the script already has stays the script's own (organs --thresh)."""
    for k, v in {**RENDER_FLAGS, **(SEQ_FLAGS if seq else {})}.items():
        if "--" + k not in ap._option_string_actions: ap.add_argument("--" + k, type=type(v), default=v)


def vram_log(path, every=1.0, cmd=("nvidia-smi", "--query-gpu=timestamp,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits")):
    """Sample the card from a daemon thread: it dies with Blender, so an out-of-memory crash leaves no nvidia-smi running."""
    import subprocess, threading

    def loop():
        with open(path, "a") as f:
            while True:
                try: f.write(subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout)
                except Exception as e: print("vram-log stopped:", e); return
                f.flush(); time.sleep(every)
    threading.Thread(target=loop, daemon=True).start()


def apply_flags(scn, A, seed=None):
    """Lay the flags over a script's own Cycles setup. Call it last, just before rendering. seed: a script whose --seed means something else passes its own."""
    global _flags
    _flags = A
    c, st, r = scn.cycles, scn.render.image_settings, scn.render
    seed = A.seed if seed is None else seed
    if seed >= 0: c.seed = seed; c.use_animated_seed = False
    if A.denoiser == "OIDN":
        c.denoiser = "OPENIMAGEDENOISE"; c.denoising_use_gpu = True
        c.denoising_prefilter = "ACCURATE"; c.denoising_quality = "HIGH"
    elif A.denoiser: c.denoiser = A.denoiser
    if A.tile > 0: c.tile_size = A.tile
    if A.thresh > 0: c.use_adaptive_sampling = True; c.adaptive_threshold = A.thresh
    if A.caustics >= 0: c.caustics_refractive = bool(A.caustics)
    if A.out_format not in ("", "png", "jpg"): raise ValueError("--out-format png|jpg, got " + A.out_format)
    if A.out_format == "jpg" and st.file_format != "JPEG":
        st.file_format = "JPEG"; st.color_mode = "RGB"; st.quality = 95
    elif A.out_format == "png" and st.file_format != "PNG":
        st.file_format = "PNG"; st.color_mode = "RGB"; st.color_depth = "8"
    if A.vram_log: vram_log(A.vram_log)
    w, h = r.resolution_x * r.resolution_percentage // 100, r.resolution_y * r.resolution_percentage // 100
    print("SETTINGS %dx%d tiles=%s(%d) spp=%d thresh=%g seed=%d animated=%s denoiser=%s gpu=%s refr_caustics=%s %s devices=%s" % (
        w, h, "many" if w * h > c.tile_size ** 2 else "one", c.tile_size, c.samples, c.adaptive_threshold, c.seed, c.use_animated_seed, c.denoiser,
        c.denoising_use_gpu, c.caustics_refractive, st.file_format, [d.name for d in bpy.context.preferences.addons["cycles"].preferences.devices if d.use]))


def out_file(path, fmt=""):
    """path with the extension Blender will give it; fmt = --out-format, "" keeps what the path says."""
    b, e = os.path.splitext(path)
    if e.lower() not in (".png", ".jpg", ".jpeg"): b, e = path, ".png"
    return b + ("." + fmt if fmt else e)


def frame_done(path):
    """True if path is a whole PNG or JPEG. Blender writes straight to the final name, so a crash mid-write leaves a cut-off file that must not count."""
    try:
        with open(path, "rb") as f:
            f.seek(-12, 2); tail = f.read()
    except OSError:
        return False
    return tail == b"\x00\x00\x00\x00IEND\xaeB`\x82" or tail[-2:] == b"\xff\xd9"


def render_seq(scn, a, b, A):
    """Animation render of frames a..b to scn.render.filepath, honouring --step, --hold and --resume."""
    step = max(1, A.step); r = scn.render
    scn.frame_start, scn.frame_end, scn.frame_step = a, b, step
    if A.resume:
        r.use_overwrite = False                     # Blender skips every file that exists, so take away the ones a crash cut off
        for f in range(a, b + 1, step):
            p = r.frame_path(frame=f)
            if os.path.exists(p) and not frame_done(p):
                print("CUT OFF, rendering again:", p); os.remove(p)
    bpy.ops.render.render(animation=True)
    if A.hold:
        for f in range(a, b + 1, step):
            for g in range(f + 1, min(f + step, b + 1)): shutil.copyfile(r.frame_path(frame=f), r.frame_path(frame=g))


def args(extra=None):
    global _flags
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="hit1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--exposure", type=float, default=0.0)
    if extra: extra(ap)
    add_render_flags(ap)
    _flags = ap.parse_args(argv)
    return _flags


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def gpu(scn, samples, pct=100, transparent=False, view="AgX", look="AgX - Base Contrast", exposure=0.0, flags=None):
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
    if flags or _flags: apply_flags(scn, flags or _flags)


def render(scn, out):
    """Write one image and return its path. With --resume a whole file is left alone."""
    if _flags:
        out = out_file(out, _flags.out_format)
        if _flags.resume and frame_done(out):
            print("SKIP", out); return out
    scn.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("RENDER %.1fs -> %s" % (time.time() - t, out))
    return out


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
