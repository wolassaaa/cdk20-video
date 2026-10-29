"""1-04 opt2 'pigment-field': a low rectangular bed of loose dry pigment on a black gallery floor, split 3:7,
vermilion and International Klein Blue (after Yves Klein's IKB, Wolfgang Laib's pollen fields, Anish Kapoor's pigment works).
One hard top light. Cycles, GPU.

blender -b --factory-startup -t 4 -P pigment.py -- --out X.png [--shot oblique|edge|top] [--samples 512] [--pct 100] [--redfrac 0.3]
"""
import bpy, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--shot", default="oblique")
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--redfrac", type=float, default=0.3)
ap.add_argument("--groove", type=int, default=0, help="1 = a finger-drawn groove across the bed (switch frame)")
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices: d.use = d.type == "OPTIX"
scn.cycles.device = "GPU"
scn.cycles.samples = A.samples
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"  # keep IKB and vermilion saturated (AgX would wash them)
scn.view_settings.look = "None"
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def pigment(name, rgb):
    """matte powder: rough diffuse + sheen, fine grain bump, tiny value noise in the colour."""
    m, nt, out = mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.15
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Tint"].default_value = (*rgb, 1)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 2
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (rgb[0] * 0.55, rgb[1] * 0.55, rgb[2] * 0.55, 1)
    ramp.color_ramp.elements[1].color = (*rgb, 1)
    nt.links.new(nz.outputs[0], ramp.inputs[0]); nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs[0], bump.inputs["Height"])
    # mid-scale powder relief: sifted lumps and drag marks
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 26; n2.inputs["Detail"].default_value = 6; n2.inputs["Roughness"].default_value = 0.65
    b2 = nt.nodes.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.9; b2.inputs["Distance"].default_value = 0.03
    nt.links.new(n2.outputs[0], b2.inputs["Height"]); nt.links.new(b2.outputs[0], bump.inputs["Normal"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


KLEIN = (0.0, 0.028, 0.39)   # #002FA7 in linear
VERM = (0.75, 0.004, 0.022)   # crimson ~#E0102A in linear (v2 red pass; was #FF3B1F, read orange)

# floor
m, nt, out = mat("floor")
b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Base Color"].default_value = (0.0012, 0.0012, 0.0012, 1); b.inputs["Roughness"].default_value = 0.9; b.inputs["Specular IOR Level"].default_value = 0.0
nt.links.new(b.outputs[0], out.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=60); bpy.context.object.data.materials.append(m)

# the bed: one grid, displaced into a soft-edged slab of powder (sifted edges fall off), split by x
LX, LY = 6.0, 3.0
split = -LX / 2 + LX * A.redfrac


def bed(name, x0, x1, material, seed):
    nx = max(8, int((x1 - x0) * 90)); ny = int(LY * 90)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1, location=((x0 + x1) / 2, 0, 0))
    o = bpy.context.object; o.name = name
    o.scale = (x1 - x0 + 0.16, LY + 0.16, 1); bpy.ops.object.transform_apply(scale=True)
    import random
    rnd = random.Random(seed)
    for v in o.data.vertices:
        x, y = v.co.x, v.co.y
        # distance inside the rectangle edge -> soft shoulder, slightly irregular
        dx = min(x - (x0 - 0.08), (x1 + 0.08) - x); dy = min(y + LY / 2 + 0.08, LY / 2 + 0.08 - y)
        d = min(dx, dy) + 0.025 * math.sin(x * 9 + seed) * math.sin(y * 7)
        h = 0.028 * max(0.0, min(1.0, d / 0.12)) ** 0.7
        if A.groove:  # a finger dragged once across the powder: trough with two soft ridges
            gy = y - (0.38 * math.sin(x * 0.62 + 0.3) - 0.05)
            h = h - 0.026 * math.exp(-(gy / 0.045) ** 2) + 0.008 * math.exp(-((abs(gy) - 0.075) / 0.03) ** 2)
            h = max(h, 0.0005)
        v.co.z = h + 0.0015 * rnd.random()
    tx = bpy.data.textures.new(name + "tx", "CLOUDS"); tx.noise_scale = 0.35; tx.noise_depth = 3
    dm = o.modifiers.new("disp", "DISPLACE"); dm.texture = tx; dm.strength = 0.06; dm.mid_level = 0.5
    dm.texture_coords = "GLOBAL"
    vg = o.vertex_groups.new(name="in")
    for v in o.data.vertices: vg.add([v.index], min(1.0, v.co.z / 0.028) * (0.25 if A.groove else 1.0), "REPLACE")
    dm.vertex_group = "in"
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(material)
    return o


if A.redfrac >= 0.999:
    bed("verm", -LX / 2, LX / 2, pigment("pv", VERM), 1)
else:
    bed("verm", -LX / 2, split - 0.004, pigment("pv", VERM), 1)
    bed("klein", split + 0.004, LX / 2, pigment("pk", KLEIN), 2)

# one hard museum spot from above + a faint fill
d = bpy.data.lights.new("spot", "SPOT"); d.energy = 4200; d.spot_size = math.radians(75); d.spot_blend = 0.6; d.shadow_soft_size = 0.05
o = bpy.data.objects.new("spot", d); scn.collection.objects.link(o); o.location = (-1.6, -0.6, 6.8)
o.rotation_euler = (Vector((0, 0, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()
d = bpy.data.lights.new("rake", "AREA"); d.energy = 120; d.size = 3; d.color = (0.9, 0.92, 1.0)
o = bpy.data.objects.new("rake", d); scn.collection.objects.link(o); o.location = (-7, -3, 0.9)
o.rotation_euler = (Vector((0, 0, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()
if A.groove:  # raking light from behind, low, across the groove; key spot nearly off
    scn.objects["spot"].data.energy = 600
    d = bpy.data.lights.new("rake2", "AREA"); d.energy = 900; d.size = 0.6; d.size_y = 6; d.shape = "RECTANGLE"; d.color = (0.95, 0.96, 1.0)
    o = bpy.data.objects.new("rake2", d); scn.collection.objects.link(o); o.location = (0.0, 5.0, 0.45)
    o.rotation_euler = (Vector((0, 0, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam); scn.camera = cam
cam_d.dof.use_dof = True
if A.shot == "oblique":
    cam_d.lens = 42; cam.location = (-0.2, -7.4, 4.6); tgt = Vector((0.0, 0.25, 0)); cam_d.dof.focus_distance = 8.4; cam_d.dof.aperture_fstop = 2.8
elif A.shot == "edge":  # eye almost at the powder, looking along the seam
    cam_d.lens = 85; cam.location = (split - 0.9, -LY / 2 - 1.5, 0.55); tgt = Vector((split + 0.3, 0.0, 0.0))
    cam_d.dof.focus_distance = (Vector((split, -LY / 2 + 0.4, 0)) - cam.location).length; cam_d.dof.aperture_fstop = 1.8
elif A.shot == "groove":  # low raking view across the groove
    cam_d.lens = 38; cam.location = (2.2, -3.4, 2.0); tgt = Vector((-0.5, 0.25, 0.0))
    cam_d.dof.focus_distance = 3.9; cam_d.dof.aperture_fstop = 2.2
else:  # top: the bed as a flat colour field
    cam_d.lens = 50; cam.location = (0, 0, 13.6); tgt = Vector((0, 0.001, 0)); cam_d.dof.use_dof = False
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("WROTE", A.out)
