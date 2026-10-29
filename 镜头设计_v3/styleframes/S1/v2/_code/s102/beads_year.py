"""1-02 option 'year' in 3D: 2022 laid out as a calendar on a black glossy table, one red glass bead per death.
1,412 beads = 365 days x 3 + 317 extra: 317 days hold four beads, 48 hold three (spread evenly). Schematic.
Low oblique camera, shallow focus: the year recedes like a field. Cobalt light from behind rims every bead.
Refs: Felix Gonzalez-Torres (one object per person, the count made physical); Boltanski (the archive of the dead).

blender -b --factory-startup -t 4 -P beads_year.py -- --out X.png [--samples 512] [--pct 100]
"""
import bpy, sys, math, argparse, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DX, DY, R, S = 0.15, 0.27, 0.02, 0.046   # day pitch, month pitch, bead radius, bead spacing in a 2x2 cell


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


# red lacquer bead (glass read as dark on black; a glossy coated red keeps the vermilion and takes a cobalt rim)
bead_m, nt, out = mat("bead")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.86, 0.006, 0.03, 1); b.inputs["Roughness"].default_value = 0.25
b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Radius"].default_value = (1.0, 0.02, 0.06)
nt.links.new(b.outputs[0], out.inputs["Surface"])
# empty slot: a tiny bone-white pinprick on the table (where a bead could have been)
dot_m, nt, out = mat("slot")
e = nt.nodes.new("ShaderNodeBsdfDiffuse"); e.inputs["Color"].default_value = (0.5, 0.49, 0.46, 1)
nt.links.new(e.outputs[0], out.inputs["Surface"])
# table: black lacquer, soft reflections
tab_m, nt, out = mat("table")
p = nt.nodes.new("ShaderNodeBsdfPrincipled")
p.inputs["Base Color"].default_value = (0.006, 0.006, 0.007, 1); p.inputs["Roughness"].default_value = 0.18
p.inputs["Coat Weight"].default_value = 0.5; p.inputs["Coat Roughness"].default_value = 0.06
nt.links.new(p.outputs[0], out.inputs["Surface"])
lab_m, nt, out = mat("label")
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (0.93, 0.92, 0.89, 1); e.inputs["Strength"].default_value = 0.35
nt.links.new(e.outputs[0], out.inputs["Surface"])

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=R)
proto = bpy.context.active_object; proto.data.materials.append(bead_m)
for f in proto.data.polygons: f.use_smooth = True
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0035, depth=0.001)
slot = bpy.context.active_object; slot.data.materials.append(dot_m)

# which 48 days hold three: rank days by a fixed hash, take the lowest 48 (deterministic, spread across the year)
rank = sorted(range(365), key=lambda i: hashlib.md5(f"2022-{i}".encode()).hexdigest())
three = set(rank[:48])
total = 0; doy = 0
for m_i, n in enumerate(DAYS):
    for d in range(n):
        cx, cy = d * DX, m_i * DY
        lit = 3 if doy in three else 4
        for k in range(4):
            x, y = cx + (k % 2) * S, cy + (k // 2) * S
            if k < lit:
                o = proto.copy(); o.location = (x, y, R); scn.collection.objects.link(o); total += 1
            else:
                o = slot.copy(); o.location = (x, y, 0.0005); scn.collection.objects.link(o)
        doy += 1
bpy.data.objects.remove(proto); bpy.data.objects.remove(slot)
assert total == 1412, total
print("beads", total)

bpy.ops.mesh.primitive_plane_add(size=40, location=(2, 1, 0)); bpy.context.active_object.data.materials.append(tab_m)

# month labels set flat on the table, left of each row
font = None
try: font = bpy.data.fonts.load("C:/Windows/Fonts/consola.ttf")
except Exception as ex: print("font", ex)
for i, mname in enumerate(MON):
    cu = bpy.data.curves.new(mname, "FONT"); cu.body = mname; cu.size = 0.07; cu.align_x = "RIGHT"
    if font: cu.font = font
    o = bpy.data.objects.new(mname, cu); scn.collection.objects.link(o)
    o.location = (-0.07, i * DY + 0.008, 0.0006); o.data.materials.append(lab_m)

# ---------------------------------------------------------------- light
def panel(name, strength, w, h, loc, color, aim=(2.0, 1.0, 0.0), cam_vis=False, no_gloss=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = (w, h, 1)
    if no_gloss: o.visible_glossy = False
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("Z", "Y").to_euler(); o.visible_camera = cam_vis
    m, nt, out = mat(name); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


panel("blue_back", 26, 12.0, 0.12, (2.4, 6.5, 0.7), (0.0, 0.02, 1.0))              # cobalt bar behind the year: rims + floor streak
panel("top", 4.0, 5.0, 3.0, (2.3, 2.4, 3.4), (1.0, 1.0, 1.0), no_gloss=True)                   # soft top fill so beads glow red
panel("spec", 18, 0.4, 3.0, (-1.4, 0.4, 1.0), (1.0, 1.0, 1.0))                   # thin strip: one crisp highlight per bead

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

# ---------------------------------------------------------------- camera: from the front-left, January nearest, December receding
cd = bpy.data.cameras.new("cam"); cd.lens = 27
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
tgt = Vector((2.25, 1.75, 0.0))
cam.location = Vector((1.9, -2.2, 1.25))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.shift_y = 0.06
cd.dof.use_dof = True; cd.dof.focus_distance = (Vector((1.6, 0.35, 0)) - cam.location).length; cd.dof.aperture_fstop = 2.0

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
scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16; scn.cycles.volume_bounces = 1
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"; scn.view_settings.exposure = 0.0
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
