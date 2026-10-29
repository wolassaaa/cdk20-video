"""1-02 option 'globe' in 3D: a black glass sphere carrying the land as cobalt lacquer beads (Natural Earth 110m land),
turned to Hong Kong, which is one vermilion bead. Close, low, f/1.4: only Hong Kong's coast is sharp.
All land dots are merged into ONE mesh (low RAM), not thousands of objects.

blender -b --factory-startup -t 4 -P globe3d.py -- --land land.json --out X.png [--samples 512] [--pct 100]
"""
import bpy, bmesh, sys, math, argparse, json
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--land", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
R = 1.0
LAT0, LON0 = math.radians(22.3), math.radians(114.17)


def xyz(lat, lon, r=R):
    """Globe coords rotated so Hong Kong faces -Y (the camera)."""
    p, l = math.radians(lat), math.radians(lon) - LON0
    # standard: x east, y north-pole... build in a frame where HK is at (0,-1,0)
    x = math.cos(p) * math.sin(l)
    y = -(math.cos(p) * math.cos(l))
    z = math.sin(p)
    v = Vector((x, y, z))
    v = Matrix.Rotation(LAT0, 3, "X") @ v      # tilt so HK's latitude comes to the equator of view
    return v * r


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


# land dots: one merged mesh of small hemispherical bumps
land = json.load(open(A.land))
bm = bmesh.new()
proto = bmesh.new(); bmesh.ops.create_icosphere(proto, subdivisions=1, radius=1.0)
pv = [v.co.copy() for v in proto.verts]; pf = [[v.index for v in f.verts] for f in proto.faces]; proto.free()
r_dot = 0.0072
for lat, lon in land:
    c = xyz(lat, lon, R * 1.004)
    base = len(bm.verts)
    vs = [bm.verts.new(c + p * r_dot) for p in pv]
    for f in pf:
        bm.faces.new([vs[i] for i in f])
me = bpy.data.meshes.new("land"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
dots = bpy.data.objects.new("land", me); scn.collection.objects.link(dots)
dm, nt, out = mat("dots")   # cobalt lacquer beads: lit, tactile, not neon
bb = nt.nodes.new("ShaderNodeBsdfPrincipled")
bb.inputs["Base Color"].default_value = (0.0, 0.035, 0.75, 1); bb.inputs["Roughness"].default_value = 0.3
bb.inputs["Coat Weight"].default_value = 1.0; bb.inputs["Coat Roughness"].default_value = 0.03
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (0.0, 0.03, 1.0, 1); e.inputs["Strength"].default_value = 0.25
ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(bb.outputs[0], ad.inputs[0]); nt.links.new(e.outputs[0], ad.inputs[1])
nt.links.new(ad.outputs[0], out.inputs["Surface"]); dots.data.materials.append(dm)

# the body: black glass, glossy, so the room's light curves across it
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=R)
sph = bpy.context.active_object
for p in sph.data.polygons: p.use_smooth = True
sm, nt, out = mat("body"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.004, 0.004, 0.006, 1); b.inputs["Roughness"].default_value = 0.12
b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
nt.links.new(b.outputs[0], out.inputs["Surface"]); sph.data.materials.append(sm)

# Hong Kong: a vermilion bead of light with a soft volume halo
hk = xyz(22.3, 114.17, R * 1.006)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.022, location=xyz(22.3, 114.17, R * 1.014))
h = bpy.context.active_object
hm, nt, out = mat("hk"); hb = nt.nodes.new("ShaderNodeBsdfPrincipled")
hb.inputs["Base Color"].default_value = (0.9, 0.015, 0.005, 1); hb.inputs["Roughness"].default_value = 0.25
hb.inputs["Coat Weight"].default_value = 1.0; hb.inputs["Coat Roughness"].default_value = 0.02
hb.inputs["Emission Color"].default_value = (1.0, 0.01, 0.004, 1); hb.inputs["Emission Strength"].default_value = 2.5
nt.links.new(hb.outputs[0], out.inputs["Surface"]); h.data.materials.append(hm)
# (no point light / volume halo: they bloomed into an orange core; the bead's own emission is enough)

tgt = Vector((0, 0, 0))
aim = xyz(22.3, 114.17) * 0.85


def panel(name, strength, w, h, loc, color, no_gloss=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = (w, h, 1)
    if no_gloss: o.visible_glossy = False   # lights the beads, leaves no grey patch on the black body
    o.rotation_euler = (tgt - Vector(loc)).to_track_quat("Z", "Y").to_euler(); o.visible_camera = False
    m, nt, out = mat(name); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


panel("key", 3.5, 6.0, 4.0, (-2.5, -1.0, 5.0), (1, 1, 1), no_gloss=True)
# (a sheen strip was tried: it read as a grey scratch across the globe, dropped)
panel("rim", 14, 0.2, 4.0, (2.8, 1.6, 0.4), (0.0, 0.03, 1.0))  # cobalt rim, right/back

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

cd = bpy.data.cameras.new("cam"); cd.lens = 85
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
cam.location = Vector((-1.6, -6.4, -0.9))
cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.shift_x = -0.22  # globe sits right of centre, room for type on the left
cd.dof.use_dof = True; cd.dof.focus_distance = (hk - cam.location).length; cd.dof.aperture_fstop = 1.2

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
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
