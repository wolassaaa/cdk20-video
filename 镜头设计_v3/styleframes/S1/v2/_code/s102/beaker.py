"""1-03 option 'beaker': a real lab beaker, vermilion liquid filled to about a third, graduations running far above it.
"We already have medicines. Just not good enough ones." Rendered on black; composited beside A's card with screen.

blender -b --factory-startup -t 4 -P beaker.py -- --out X.png [--samples 512] [--pct 100] [--fill 0.32]
"""
import bpy, bmesh, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--fill", type=float, default=0.32)
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
RAD, HGT, WALL = 0.5, 1.5, 0.018


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


glass, nt, out = mat("glass")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.0
b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.47
nt.links.new(b.outputs[0], out.inputs["Surface"])

liquid, nt, out = mat("liquid")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.0
b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.34
nt.links.new(b.outputs[0], out.inputs["Surface"])
va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (1.0, 0.01, 0.06, 1); va.inputs["Density"].default_value = 5
vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (1.0, 0.02, 0.07, 1); vs.inputs["Density"].default_value = 5.0
ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
# a faint glow from within (the backlight can't reach the volume through glass when it is hidden from transmission)
ve = nt.nodes.new("ShaderNodeEmission"); ve.inputs["Color"].default_value = (1.0, 0.004, 0.04, 1); ve.inputs["Strength"].default_value = 0.45
ad2 = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(ad.outputs[0], ad2.inputs[0]); nt.links.new(ve.outputs[0], ad2.inputs[1])
nt.links.new(ad2.outputs[0], out.inputs["Volume"])

ink, nt, out = mat("ink")
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (0.93, 0.92, 0.89, 1); e.inputs["Strength"].default_value = 0.9
nt.links.new(e.outputs[0], out.inputs["Surface"])

# beaker: open cylinder + bottom, made thick, with a little pouring lip
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAD, depth=HGT, location=(0, 0, HGT / 2))
bk = bpy.context.active_object
bm = bmesh.new(); bm.from_mesh(bk.data)
top = [f for f in bm.faces if f.normal.z > 0.9]
bmesh.ops.delete(bm, geom=top, context="FACES")
for v in bm.verts:   # lip: pull the rim out a touch, and the spout further at +X
    if v.co.z > HGT - 1e-4:
        a = math.atan2(v.co.y, v.co.x)
        k = 1.0 + 0.035 + 0.09 * math.exp(-(a / 0.22) ** 2)
        v.co.x *= k; v.co.y *= k
bm.to_mesh(bk.data); bm.free()
for f in bk.data.polygons: f.use_smooth = True
s = bk.modifiers.new("solid", "SOLIDIFY"); s.thickness = WALL; s.offset = -1
bv = bk.modifiers.new("bevel", "BEVEL"); bv.width = 0.006; bv.segments = 3; bv.limit_method = "ANGLE"
bk.data.materials.append(glass)

# liquid: a cylinder just inside the wall, to the fill line
lh = (HGT - WALL) * A.fill
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAD - WALL - 0.002, depth=lh, location=(0, 0, WALL + lh / 2 + 0.001))
lq = bpy.context.active_object
bv = lq.modifiers.new("bevel", "BEVEL"); bv.width = 0.01; bv.segments = 4
for f in lq.data.polygons: f.use_smooth = True
lq.data.materials.append(liquid)

# graduations on the camera side: short ticks every 1/6, longer every third, all far above the liquid
for i in range(1, 6):
    z = WALL + (HGT - WALL) * i / 6
    w = 0.16 if i % 2 == 0 else 0.09
    a0 = math.radians(-90 - 40)
    bpy.ops.mesh.primitive_cube_add(size=1)
    t = bpy.context.active_object; t.scale = (w, 0.006, 0.011)
    ang = a0 + (w / 2) / RAD
    t.location = (RAD * 1.002 * math.cos(ang), RAD * 1.002 * math.sin(ang), z)
    t.rotation_euler = (0, 0, ang + math.pi / 2)
    t.data.materials.append(ink)

bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
fl = bpy.context.active_object
fm, nt, out = mat("floor"); p = nt.nodes.new("ShaderNodeBsdfPrincipled")
p.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1); p.inputs["Roughness"].default_value = 0.35
nt.links.new(p.outputs[0], out.inputs["Surface"]); fl.data.materials.append(fm)
fl.is_shadow_catcher = True   # transparent film: only the beaker's own reflection/shadow survive

tgt = Vector((0, 0, 0.7))


def panel(name, strength, w, h, loc, color, aim=None, hidden=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = (w, h, 1)
    if hidden: o.visible_transmission = False; o.visible_glossy = False   # light the liquid's volume, never seen in the glass
    o.rotation_euler = ((aim or tgt) - Vector(loc)).to_track_quat("Z", "Y").to_euler(); o.visible_camera = False
    m, nt, out = mat(name); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


panel("back", 90, 1.4, 0.6, (0.0, 2.5, 0.3), (1, 1, 1), aim=Vector((0, 0, 0.25)), hidden=True)  # low white strip behind: lights the liquid only
panel("blue_l", 45, 0.18, 3.0, (-2.6, 0.9, 1.0), (0.0, 0.01, 1.0))     # cobalt rim, left
panel("strip_r", 22, 0.15, 3.0, (2.4, -0.4, 1.1), (1, 1, 1))           # white rim, right

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

cd = bpy.data.cameras.new("cam"); cd.lens = 70
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
cam.location = Vector((0.0, -5.6, 1.55))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

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
scn.cycles.max_bounces = 24; scn.cycles.transmission_bounces = 24; scn.cycles.volume_bounces = 2
scn.cycles.caustics_refractive = True
scn.render.resolution_x = 1000; scn.render.resolution_y = 1000; scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"; scn.view_settings.exposure = 0.0
scn.render.film_transparent = True; scn.cycles.film_transparent_glass = True
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGBA"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
