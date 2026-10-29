"""1-02 option 'chain': three glossy vermilion links (lung · colorectal · liver, the three deadliest in HK)
on an International-Klein-blue field. Ref: Red Knot Chain (glossy tubes, flat colour field).
Equal links on purpose: no values are encoded (ILLUSTRATIVE).

blender -b --factory-startup -P chain3.py -- --out X.png [--samples 256] [--pct 100]
"""
import bpy, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--bg", default="0.0,0.028,0.386")   # #002FA7 in linear
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


# glossy lacquer red
red, nt, out = mat("lacquer")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.75, 0.018, 0.006, 1)
b.inputs["Roughness"].default_value = 0.22
b.inputs["Coat Weight"].default_value = 1.0
b.inputs["Coat Roughness"].default_value = 0.03
b.inputs["Subsurface Weight"].default_value = 0.15
b.inputs["Subsurface Radius"].default_value = (1.0, 0.1, 0.05)
nt.links.new(b.outputs[0], out.inputs["Surface"])

# blue field: emissive backdrop (flat colour, like a screen-printed ground) + a matte floor of the same blue
bg = [float(x) for x in A.bg.split(",")]
blue, nt, out = mat("blue")
d = nt.nodes.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = (*bg, 1)
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*bg, 1); e.inputs["Strength"].default_value = 0.4
add = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(d.outputs[0], add.inputs[0]); nt.links.new(e.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs["Surface"])

R, r, D = 1.0, 0.2, 1.42
YAW = math.radians(-34)
links = []
for i in range(3):
    x = (i - 1) * D
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=200, minor_segments=56,
                                     location=(x * math.cos(YAW), x * math.sin(YAW), 0.0))
    o = bpy.context.active_object
    # a real chain: links alternate between two perpendicular planes that both contain the chain axis
    o.rotation_euler = (math.radians(90), 0, YAW) if i % 2 == 0 else (0, 0, YAW)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(red)
    links.append(o)

# infinite cove: big plane behind + floor, both blue
# (no floor: the links float on a flat colour field)
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 14, 0), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.data.materials.append(blue)

# camera
cd = bpy.data.cameras.new("cam"); cd.lens = 55
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
tgt = Vector((-0.75, 0.0, -0.1))
cam.location = Vector((1.6, -8.6, 2.1))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.dof.use_dof = True; cd.dof.focus_distance = (Vector((D * math.cos(YAW), D * math.sin(YAW), 0)) - cam.location).length; cd.dof.aperture_fstop = 2.8


def softbox(name, strength, w, h, loc, color=(1, 1, 1)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    o.rotation_euler = (tgt - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = False
    m, nt, out = mat(name)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


softbox("key", 14, 5, 2.2, (-4.5, -6, 6))          # broad top-left key: long glossy streaks
softbox("strip", 40, 0.35, 6, (6, -3, 2.5), (0.9, 0.95, 1.0))  # thin right strip: crisp rim line
softbox("fill", 0.8, 8, 3, (0, -9, -0.5))          # low front fill so the undersides aren't dead

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*bg, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3

scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        pref.compute_device_type = dev; pref.get_devices(); ok = False
        for dv in pref.devices:
            dv.use = (dv.type == dev); ok |= dv.use
        if ok: break
    except Exception as ex:
        print("device", dev, ex)
scn.cycles.device = "GPU"; scn.cycles.samples = A.samples; scn.cycles.use_denoising = True
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"; scn.view_settings.exposure = 0.0
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
