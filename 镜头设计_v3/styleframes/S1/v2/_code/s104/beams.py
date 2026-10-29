"""1-04 opt3 'ten-beams': ten shafts of light falling through haze in a dark room (after Anthony McCall's solid-light works).
Three beams vermilion, seven blue. Cycles volumetrics, GPU.

blender -b --factory-startup -t 4 -P beams.py -- --out X.png [--shot wide|low|top] [--samples 512] [--pct 100] [--lit 1,4,8] [--blue 1.0]
  wide : three-quarter view into the row, beams read as ten columns, floor pools
  low  : low camera between beams looking up the row (unmet-need frame)
  --blue scales the seven blue beams (0 = they are switched off)
"""
import bpy, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--shot", default="wide")
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--lit", default="1,4,8")
ap.add_argument("--blue", type=float, default=1.0)
ap.add_argument("--red", type=float, default=1.0)
ap.add_argument("--haze", type=float, default=0.06)
A = ap.parse_args(argv)
LIT = {int(i) for i in A.lit.split(",") if i != ""}

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices: d.use = d.type == "OPTIX"
scn.cycles.device = "GPU"
scn.cycles.samples = A.samples
scn.cycles.use_denoising = True
scn.cycles.volume_bounces = 1
scn.cycles.max_bounces = 6
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"
scn.view_settings.exposure = 0.6
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


# floor: black polished concrete
m, nt, out = mat("floor")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.04, 0.04, 0.042, 1)
b.inputs["Roughness"].default_value = 0.32
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.22; mr.inputs[4].default_value = 0.5
nt.links.new(nz.outputs[0], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
nt.links.new(b.outputs[0], out.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); bpy.context.object.data.materials.append(m)

# haze: a big box of homogeneous scattering volume
m, nt, out = mat("haze")
v = nt.nodes.new("ShaderNodeVolumePrincipled")
v.inputs["Density"].default_value = A.haze
v.inputs["Color"].default_value = (1, 1, 1, 1)
v.inputs["Anisotropy"].default_value = 0.25
# slight uneven haze so beams are not perfect
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 3
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = A.haze * 0.55; mr.inputs[4].default_value = A.haze * 1.45
nt.links.new(nz.outputs[0], mr.inputs[0]); nt.links.new(mr.outputs[0], v.inputs["Density"])
nt.links.new(v.outputs[0], out.inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3)); hz = bpy.context.object
hz.scale = (24, 24, 6); hz.data.materials.append(m)

RED = (1.0, 0.003, 0.014)  # crimson (v2 red pass)
BLUE = (0.012, 0.035, 1.0)
N, GAP, TOP = 10, 0.9, 5.6
x0 = -GAP * (N - 1) / 2
for i in range(N):
    lit = i in LIT
    d = bpy.data.lights.new(f"beam{i}", "SPOT")
    d.color = RED if lit else BLUE
    d.energy = (90000 * A.red) if lit else (45000 * A.blue)
    d.spot_size = math.radians(4.2); d.spot_blend = 0.08
    d.shadow_soft_size = 0.01
    o = bpy.data.objects.new(f"beam{i}", d); scn.collection.objects.link(o)
    o.location = (x0 + i * GAP, 0, TOP)
    o.rotation_euler = (0, 0, 0)  # spots point down -Z
    if d.energy <= 0: o.hide_render = True

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam); scn.camera = cam
cam_d.dof.use_dof = True
if A.shot == "wide":
    cam_d.lens = 30
    cam.location = (-0.6, -10.5, 1.5)
    tgt = Vector((0.3, 0, 2.5))
    cam_d.dof.focus_distance = 9.5; cam_d.dof.aperture_fstop = 5.6
elif A.shot == "low":
    cam_d.lens = 24
    cam.location = (x0 - 1.0, -1.6, 0.35)
    tgt = Vector((x0 + 5 * GAP, 0.4, 2.6))
    cam_d.dof.focus_distance = 2.4; cam_d.dof.aperture_fstop = 2.8
else:  # top: looking straight down on the ten pools of light
    cam_d.lens = 35
    cam.location = (0, -0.01, 11.5)
    tgt = Vector((0, 0, 0))
    cam_d.dof.use_dof = False
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("WROTE", A.out)
