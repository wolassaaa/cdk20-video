"""1-03 option 'capsule': one clear glass capsule, only partly filled with vermilion granules ("we already have
medicines... just not good enough ones"). Transparent film, composited beside A's photo card in Remotion.

blender -b --factory-startup -P capsule.py -- --out X.png [--samples 256] [--pct 100] [--fill 0.38]
"""
import bpy, bmesh, sys, math, argparse, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--fill", type=float, default=0.38)
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
RAD, HALF = 0.5, 0.75          # capsule radius, half-length of the straight part (lies along X)


def capsule_mesh(name, rad, half, nu=96, nv=48):
    """Capsule as rings: profile = cap / cylinder / cap, revolved about X."""
    prof = []
    for i in range(nv + 1):            # left cap: -90..0 deg
        a = -math.pi / 2 + (math.pi / 2) * i / nv
        prof.append((-half - rad * math.cos(a + math.pi / 2) * 1.0 if False else -half + rad * math.sin(a), rad * math.cos(a)))
    for i in range(1, 12):
        prof.append((-half + 2 * half * i / 12, rad))
    for i in range(nv + 1):            # right cap: 0..90 deg
        a = (math.pi / 2) * i / nv
        prof.append((half + rad * math.sin(a), rad * math.cos(a)))
    verts, faces = [], []
    for (x, r) in prof:
        for j in range(nu):
            t = 2 * math.pi * j / nu
            verts.append((x, r * math.cos(t), r * math.sin(t)))
    for i in range(len(prof) - 1):
        for j in range(nu):
            a, b = i * nu + j, i * nu + (j + 1) % nu
            faces.append((a, b, b + nu, a + nu))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scn.collection.objects.link(o)
    return o


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


glass, nt, out = mat("glass")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.02
b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.45
nt.links.new(b.outputs[0], out.inputs["Surface"])

red, nt, out = mat("granule")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (1.0, 0.05, 0.015, 1); b.inputs["Roughness"].default_value = 0.3
b.inputs["Coat Weight"].default_value = 0.6
nt.links.new(b.outputs[0], out.inputs["Surface"])

shell = capsule_mesh("shell", RAD, HALF)
shell.data.materials.append(glass)
sol = shell.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.03; sol.offset = -1

# granules: random packing in the lower part of the capsule interior (simple rejection sampling, small overlap ok)
random.seed(7)
inner = RAD - 0.05
zmax = -inner + 2 * inner * A.fill
pts = []
tries = 0
while len(pts) < 900 and tries < 200000:
    tries += 1
    x = random.uniform(-HALF - inner, HALF + inner); y = random.uniform(-inner, inner); z = random.uniform(-inner, zmax)
    cx = max(-HALF, min(HALF, x))
    rr = random.uniform(0.035, 0.06)
    if (x - cx) ** 2 + y * y + z * z > (inner - rr) ** 2: continue
    if any((x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 < (rr + p[3]) ** 2 * 0.8 for p in pts[-200:]): continue
    pts.append((x, y, z, rr))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
proto = bpy.context.active_object; proto.data.materials.append(red)
for p in proto.data.polygons: p.use_smooth = True
coll = []
for (x, y, z, rr) in pts:
    o = proto.copy(); o.location = (x, y, z); o.scale = (rr, rr, rr); scn.collection.objects.link(o)
bpy.data.objects.remove(proto)
print("granules", len(pts))

# tilt the whole capsule a little, like it was set down
root = bpy.data.objects.new("root", None); scn.collection.objects.link(root)
for o in list(scn.objects):
    if o.type == "MESH": o.parent = root
root.rotation_euler = (math.radians(-8), math.radians(-14), math.radians(18))

cd = bpy.data.cameras.new("cam"); cd.lens = 85
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
tgt = Vector((0, 0, 0))
cam.location = Vector((0.4, -7.5, 2.4))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()


def softbox(name, strength, w, h, loc, color=(1, 1, 1)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = (w, h, 1)
    o.rotation_euler = (tgt - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = False
    m, nt, out = mat(name)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


softbox("key", 30, 3, 0.4, (-3, -2.5, 4))
softbox("rim", 45, 0.25, 4, (3.5, 1.5, 1.5), (0.95, 0.97, 1.0))
softbox("back", 6, 6, 4, (0, 6, 1))
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.004, 1)

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
scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16
scn.render.resolution_x = 1200; scn.render.resolution_y = 900; scn.render.resolution_percentage = A.pct
scn.render.film_transparent = True
scn.cycles.film_transparent_glass = True
scn.view_settings.view_transform = "AgX"; scn.view_settings.exposure = 0.9
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGBA"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
