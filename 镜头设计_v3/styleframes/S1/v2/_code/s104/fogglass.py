"""1-04 opt4 'fog-glass': a fogged window pane with finger-wiped strokes; neon light behind it.
Fogged = frosted glass + condensation beads; wiped = clear glass (mask PNG from Remotion, masks/fog_<part>.png).
Behind: ten vertical neon tubes (3 vermilion, 7 blue) aligned with the ten strokes; far city bokeh. Cycles, GPU.

blender -b --factory-startup -t 4 -P fogglass.py -- --part a|b|c --mask masks/fog_b.png --out X.png [--samples 512] [--pct 100]
"""
import bpy, sys, math, argparse, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--mask", required=True)
ap.add_argument("--part", default="b")
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--lit", default="1,4,8")
ap.add_argument("--fogdark", type=float, default=-1, help="share of dark matte in the fog film (default 0.9 for a, 0.45 for b/c)")
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
scn.cycles.max_bounces = 12; scn.cycles.transmission_bounces = 12
scn.cycles.blur_glossy = 1.0
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"  # v2: keep #1F3BFF pure (AgX pushed it lavender)
scn.view_settings.look = "Medium High Contrast"
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

PW, PH, PZ = 3.2, 1.8, 1.0
DIST = (PW / 2) / math.tan(math.atan(18 / 50)) * 0.97


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def emit(name, rgb, strength):
    m, nt, out = mat(name)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*rgb, 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- the pane
m, nt, out = mat("pane")
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(A.mask); tex.image.colorspace_settings.name = "Non-Color"
uv = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(uv.outputs["UV"], tex.inputs[0])
clear = nt.nodes.new("ShaderNodeBsdfGlass"); clear.inputs["Roughness"].default_value = 0.0; clear.inputs["IOR"].default_value = 1.5
frost = nt.nodes.new("ShaderNodeBsdfGlass"); frost.inputs["Roughness"].default_value = 0.42; frost.inputs["IOR"].default_value = 1.5
# v2: fog is mostly a dark matte film (near-black ground), only ~35% of the light scatters through
milk = nt.nodes.new("ShaderNodeBsdfDiffuse"); milk.inputs[0].default_value = (0.012, 0.012, 0.013, 1)
fm = nt.nodes.new("ShaderNodeMixShader"); fm.inputs[0].default_value = A.fogdark if A.fogdark >= 0 else (0.9 if A.part == "a" else 0.45)
nt.links.new(frost.outputs[0], fm.inputs[1]); nt.links.new(milk.outputs[0], fm.inputs[2])
# condensation beads on the fogged part: voronoi bumps (droplets refract the light behind)
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "F1"; vor.inputs["Scale"].default_value = 260; vor.inputs["Randomness"].default_value = 1
nt.links.new(uv.outputs["Object"], vor.inputs[0])
inv = nt.nodes.new("ShaderNodeMapRange"); inv.inputs[1].default_value = 0.0; inv.inputs[2].default_value = 0.45; inv.inputs[3].default_value = 1; inv.inputs[4].default_value = 0
nt.links.new(vor.outputs["Distance"], inv.inputs[0])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 0.006
# beads only where fogged: height *= (1 - mask)
one = nt.nodes.new("ShaderNodeMath"); one.operation = "SUBTRACT"; one.inputs[0].default_value = 1
nt.links.new(tex.outputs["Color"], one.inputs[1])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(inv.outputs[0], mul.inputs[0]); nt.links.new(one.outputs[0], mul.inputs[1])
nt.links.new(mul.outputs[0], bump.inputs["Height"])
nt.links.new(bump.outputs[0], frost.inputs["Normal"])
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(tex.outputs["Color"], mix.inputs[0])
nt.links.new(fm.outputs[0], mix.inputs[1]); nt.links.new(clear.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, PZ), rotation=(math.radians(90), 0, 0))
pane = bpy.context.object; pane.scale = (PW, PH, 1)
bpy.ops.object.transform_apply(scale=True)
pane.data.materials.append(m)
s = pane.modifiers.new("sol", "SOLIDIFY"); s.thickness = 0.006
# frame bars just outside the view so the edges never show

# ---------------------------------------------------------------- behind the glass
RED, BLUE, BONE = (1.0, 0.02, 0.005), (0.015, 0.05, 1.0), (0.85, 0.85, 0.8)
mRed, mBlue = emit("neonR", (1.0, 0.010, 0.027), 2.6), emit("neonB", (0.0137, 0.0433, 1.0), 2.6)


DEPTH = 0.55
K_PAR = (DIST + DEPTH) / DIST  # parallax: objects behind the pane must sit wider to line up with the strokes
def px2x(px): return (px / 1920 - 0.5) * PW * K_PAR
def py2z(py): return PZ + (0.5 - py / 1080) * PH * K_PAR


if A.part in ("b", "c"):
    for i in range(10):
        x = px2x(420 + i * 120)
        z0, z1 = py2z(820), py2z(250)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.011, depth=z1 - z0, location=(x, DEPTH, (z0 + z1) / 2))
        bpy.context.object.data.materials.append(mRed if i in LIT else mBlue)
else:
    # v2: no neon behind the words; a soft pure-blue field far back, so the wiped letters read blue
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2.5, PZ), rotation=(math.radians(90), 0, 0))
    bpy.context.object.scale = (8, 4, 1); bpy.context.object.data.materials.append(emit("field", (0.0137, 0.0433, 1.0), 0.55))

# far city bokeh (few objects, small RAM)
rnd = random.Random(7)
mats = [emit("pB", (0.0137, 0.0433, 1.0), 5), emit("pW", BONE, 3), emit("pB2", (0.0137, 0.0433, 1.0), 3)]
for k in range(140):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.012 + rnd.random() * 0.022,
                                         location=(rnd.uniform(-4.5, 4.5), rnd.uniform(5, 9), rnd.uniform(-0.6, 2.8)))
    bpy.context.object.data.materials.append(mats[0 if rnd.random() < 0.6 else (1 if rnd.random() < 0.5 else 2)])
# faint skyglow so the fog has something to scatter
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 12, 1), rotation=(math.radians(90), 0, 0))
bpy.context.object.scale = (30, 12, 1); bpy.context.object.data.materials.append(emit("sky", (0, 0, 0), 0.0))

# a little light on our side, to catch the beads
d = bpy.data.lights.new("key", "AREA"); d.energy = 22; d.size = 1.5; d.color = (0.93, 0.92, 0.89)
o = bpy.data.objects.new("key", d); scn.collection.objects.link(o); o.location = (1.5, -1.6, 2.6)
o.rotation_euler = (Vector((0, 0, PZ)) - o.location).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- camera: pane fills the frame
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam); scn.camera = cam
cam_d.lens = 50; cam_d.sensor_fit = "HORIZONTAL"; cam_d.sensor_width = 36
dist = DIST
cam.location = (0, -dist, PZ); cam.rotation_euler = (math.radians(90), 0, 0)
cam_d.dof.use_dof = True; cam_d.dof.focus_distance = dist; cam_d.dof.aperture_fstop = 2.2

scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("WROTE", A.out)
