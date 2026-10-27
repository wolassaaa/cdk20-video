"""GPU test for the RTX 5080: builds the AlphaFold CDK20 model in Blender and renders it with Cycles.

Run:  blender -b -P cdk20_gpu_test.py -- <pdb> <outdir>
Renders a CPU vs GPU benchmark frame, a look-test frame (low-confidence C-terminal tail highlighted)
and a 150-frame turntable to measure video throughput.
"""
import bpy, sys, time, math, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PDB, OUT = argv[0], argv[1].rstrip("/\\")
log = {}

# ---------- devices ----------
prefs = bpy.context.preferences.addons["cycles"].preferences
devices = {}
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.refresh_devices()
        devices[kind] = [(d.name, d.type) for d in prefs.devices if d.type == kind]
    except TypeError:
        devices[kind] = []
log["devices"] = devices
prefs.compute_device_type = "OPTIX" if devices.get("OPTIX") else "CUDA"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == prefs.compute_device_type
print("DEVICES", devices)

# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences  # re-fetch after reset
prefs.compute_device_type = "OPTIX" if devices.get("OPTIX") else "CUDA"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == prefs.compute_device_type

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

# Cα trace with pLDDT from the B-factor column
ca = []
for line in open(PDB, encoding="utf-8"):
    if line.startswith("ATOM") and line[12:16].strip() == "CA":
        ca.append((int(line[22:26]), Vector((float(line[30:38]), float(line[38:46]), float(line[46:54]))), float(line[60:66])))
center = sum((p for _, p, _ in ca), Vector()) / len(ca)
ca = [(r, (p - center) * 0.1, b) for r, p, b in ca]  # 1 Å -> 0.1 m

def mat(name, base, emit=None, strength=0.0, rough=0.35, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*base, 1)
    bs.inputs["Roughness"].default_value = rough
    if coat:
        bs.inputs["Coat Weight"].default_value = coat
    if emit:
        bs.inputs["Emission Color"].default_value = (*emit, 1)
        bs.inputs["Emission Strength"].default_value = strength
    return m

# confidence bands (AlphaFold DB colour convention) + the removed tail 303–346
M = {
    "vhigh": mat("pLDDT>=90", (0.05, 0.23, 0.62), rough=0.3, coat=0.4),
    "high": mat("pLDDT70-90", (0.25, 0.62, 0.95), rough=0.3, coat=0.4),
    "low": mat("pLDDT50-70", (0.95, 0.80, 0.25), rough=0.4),
    "vlow": mat("pLDDT<50", (0.95, 0.45, 0.20), rough=0.4),
    "tail": mat("tail_303_346", (1.0, 0.35, 0.12), emit=(1.0, 0.32, 0.08), strength=1.2, rough=0.4),
}
def band(res, b):
    if res >= 303:
        return "tail"
    return "vhigh" if b >= 90 else "high" if b >= 70 else "low" if b >= 50 else "vlow"

# one smooth tube per run of equal band; runs share an end point so the trace is continuous
runs, cur = [], None
for i, (r, p, b) in enumerate(ca):
    k = band(r, b)
    if cur is None or cur[0] != k:
        if cur is not None:
            cur[1].append(p)
        cur = (k, [ca[i - 1][1]] if i else [])
        runs.append(cur)
    cur[1].append(p)
for k, pts in runs:
    cd = bpy.data.curves.new("trace", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.055 if k != "tail" else 0.07
    cd.bevel_resolution = 6
    cd.resolution_u = 10
    sp = cd.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for j, p in enumerate(pts):
        sp.points[j].co = (*p, 1)
    sp.use_endpoint_u = True
    sp.order_u = 4 if len(pts) >= 4 else len(pts)
    ob = bpy.data.objects.new("trace_" + k, cd)
    ob.data.materials.append(M[k])
    sc.collection.objects.link(ob)

# Arg305 marker: the residue that sits in the ATP pocket in the predicted model
arg = next(p for r, p, _ in ca if r == 305)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=arg, segments=48, ring_count=24)
bpy.context.object.data.materials.append(mat("Arg305", (1, 0.9, 0.7), emit=(1.0, 0.55, 0.2), strength=4))
bpy.ops.object.shade_smooth()

# floor + studio lights
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, min(p.z for _, p, _ in ca) - 0.6))
bpy.context.object.data.materials.append(mat("floor", (0.035, 0.04, 0.05), rough=0.55))
def light(kind, loc, energy, color, size=4.0):
    ld = bpy.data.lights.new(kind, "AREA")
    ld.energy, ld.color, ld.size = energy, color, size
    ob = bpy.data.objects.new(kind, ld)
    ob.location = loc
    ob.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
light("key", (5, -6, 6), 1800, (1.0, 0.95, 0.9), 5)
light("rim", (-6, 5, 3), 1400, (0.55, 0.75, 1.0), 3)
light("fill", (-5, -6, -1), 300, (1.0, 0.85, 0.75), 6)
w = bpy.data.worlds.new("world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.006, 0.008, 0.012, 1)
sc.world = w

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 50
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new("cam", cam_d)
radius = max(p.length for _, p, _ in ca)
dist = radius / math.tan(cam_d.angle_y / 2) * 1.15  # whole model fits the frame height
cam_dir = Vector((0.3, -0.9, 0.25)).normalized()
cam_d.dof.focus_distance = dist
sc.collection.objects.link(cam)
sc.camera = cam

def place_camera(angle):
    """Orbit the camera around the model's centre; angle in radians."""
    d = Vector((cam_dir.x * math.cos(angle) - cam_dir.y * math.sin(angle),
                cam_dir.x * math.sin(angle) + cam_dir.y * math.cos(angle), cam_dir.z))
    cam.location = d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
place_camera(0.0)

def render(device, samples, name, denoise):
    sc.cycles.device = device
    sc.cycles.samples = samples
    sc.cycles.use_denoising = denoise
    if denoise:
        sc.cycles.denoiser = "OPTIX" if device == "GPU" else "OPENIMAGEDENOISE"
    sc.render.filepath = f"{OUT}/{name}.png"
    t = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    dt = round(time.perf_counter() - t, 2)
    print(f"RENDER {name} {device} {samples}spp {dt}s")
    return dt

# warm-up (kernel load), then like-for-like benchmark at 128 spp, then the look frame
render("GPU", 8, "warmup", False)
log["gpu_128spp_s"] = render("GPU", 128, "bench_gpu_128", False)
log["cpu_128spp_s"] = render("CPU", 128, "bench_cpu_128", False)
log["look_gpu_1024spp_s"] = render("GPU", 1024, "look_cdk20_tail", True)
log["residues"] = len(ca)

# 5 s turntable (150 frames, 30 fps, 128 spp + OptiX denoise) to measure video throughput
sc.cycles.device, sc.cycles.samples = "GPU", 128
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
t = time.perf_counter()
for f in range(150):
    place_camera(math.radians(40) * f / 149 - math.radians(20))
    sc.render.filepath = f"{OUT}/turntable/f{f:04d}.png"
    bpy.ops.render.render(write_still=True)
log["turntable_150f_s"] = round(time.perf_counter() - t, 1)
json.dump(log, open(f"{OUT}/result.json", "w"), indent=2)
print("RESULT", json.dumps(log))
