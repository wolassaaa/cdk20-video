"""1-03 vitrine pass: the medicine object lit like a museum piece. A pool of light on a glossy black plinth, a cobalt
rim, darkness everywhere else, shallow focus. Full 1920x1080 opaque frame with the object in the right half, so A's
photo card can be laid over the left half and sit in the same dark room (the plinth runs behind it).

  --obj beaker   lab beaker, vermilion liquid a third full, graduations far above it
  --obj capsule  one clear capsule lying on the plinth, partly filled with vermilion granules
  --obj row      nine clear capsules standing in a receding row; only two are filled red

blender -b --factory-startup -t 4 -P vitrine.py -- --obj beaker --out X.png [--samples 768] [--pct 100]
Refs: Damien Hirst, Pharmacy (1992) and the pill cabinets: medicine shown as a cool, lit specimen.
"""
import bpy, bmesh, sys, math, argparse, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--obj", default="beaker")
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=768)
ap.add_argument("--pct", type=int, default=100)
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def principled(name, base, rough, trans=0.0, ior=1.45, coat=0.0, emit=None):
    m, nt, out = mat(name); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.03
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, nt, out


glass = principled("glass", (1, 1, 1), 0.0, trans=1.0, ior=1.47)[0]
red_lacquer = principled("granule", (0.85, 0.02, 0.006), 0.28, coat=0.8)[0]
ink = principled("ink", (0.9, 0.89, 0.86), 0.5, emit=((0.93, 0.92, 0.89), 0.6))[0]


def red_liquid():
    m, nt, out = principled("liquid", (1, 1, 1), 0.0, trans=1.0, ior=1.34)
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (1.0, 0.03, 0.01, 1); va.inputs["Density"].default_value = 5
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (1.0, 0.05, 0.02, 1); vs.inputs["Density"].default_value = 5
    ve = nt.nodes.new("ShaderNodeEmission"); ve.inputs["Color"].default_value = (1.0, 0.01, 0.004, 1); ve.inputs["Strength"].default_value = 0.35
    a1 = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], a1.inputs[0]); nt.links.new(vs.outputs[0], a1.inputs[1])
    a2 = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(ve.outputs[0], a2.inputs[1])
    nt.links.new(a2.outputs[0], out.inputs["Volume"])
    return m


def capsule_mesh(name, rad, half, nu=96, nv=32):
    """Capsule along X: cap / cylinder / cap, revolved."""
    prof = []
    for i in range(nv + 1):
        a = -math.pi / 2 + (math.pi / 2) * i / nv
        prof.append((-half + rad * math.sin(a), rad * math.cos(a)))
    for i in range(1, 12):
        prof.append((-half + 2 * half * i / 12, rad))
    for i in range(nv + 1):
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


def glass_capsule(name, rad, half):
    o = capsule_mesh(name, rad, half); o.data.materials.append(glass)
    s = o.modifiers.new("solid", "SOLIDIFY"); s.thickness = rad * 0.06; s.offset = -1
    return o


# ---------------------------------------------------------------- the plinth: glossy black top, a soft front edge
pl, nt, out = principled("plinth", (0.004, 0.004, 0.005), 0.06, coat=1.0)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.0, -0.5))
plinth = bpy.context.active_object; plinth.scale = (9.0, 5.0, 1.0)
bv = plinth.modifiers.new("bevel", "BEVEL"); bv.width = 0.02; bv.segments = 4
plinth.data.materials.append(pl)

objs = []
if A.obj == "beaker":
    RAD, HGT, WALL, FILL = 0.5, 1.5, 0.018, 0.32
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAD, depth=HGT, location=(0, 0, HGT / 2))
    bk = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(bk.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES")
    for v in bm.verts:
        if v.co.z > HGT - 1e-4:
            a = math.atan2(v.co.y, v.co.x); k = 1.035 + 0.09 * math.exp(-(a / 0.22) ** 2)
            v.co.x *= k; v.co.y *= k
    bm.to_mesh(bk.data); bm.free()
    for f in bk.data.polygons: f.use_smooth = True
    s = bk.modifiers.new("solid", "SOLIDIFY"); s.thickness = WALL; s.offset = -1
    bk.data.materials.append(glass)
    lh = (HGT - WALL) * FILL
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAD - WALL - 0.002, depth=lh, location=(0, 0, WALL + lh / 2 + 0.001))
    lq = bpy.context.active_object; b2 = lq.modifiers.new("bevel", "BEVEL"); b2.width = 0.01; b2.segments = 4
    for f in lq.data.polygons: f.use_smooth = True
    lq.data.materials.append(red_liquid())
    for i in range(1, 6):
        z = WALL + (HGT - WALL) * i / 6; w = 0.16 if i % 2 == 0 else 0.09
        ang = math.radians(-90 - 40) + (w / 2) / RAD
        bpy.ops.mesh.primitive_cube_add(size=1); t = bpy.context.active_object; t.scale = (w, 0.006, 0.011)
        t.location = (RAD * 1.002 * math.cos(ang), RAD * 1.002 * math.sin(ang), z); t.rotation_euler = (0, 0, ang + math.pi / 2)
        t.data.materials.append(ink)
    focus = Vector((0, -0.45, 0.55)); aim = Vector((0, 0, 0.72)); dist, lens, height = 5.2, 85, 1.05
elif A.obj == "capsule":
    RAD, HALF = 0.42, 0.62
    root = bpy.data.objects.new("root", None); scn.collection.objects.link(root)
    sh = glass_capsule("shell", RAD, HALF); sh.parent = root
    random.seed(7); inner = RAD - RAD * 0.08; zmax = -inner + 2 * inner * 0.38; pts = []
    tries = 0
    while len(pts) < 700 and tries < 200000:
        tries += 1
        x = random.uniform(-HALF - inner, HALF + inner); y = random.uniform(-inner, inner); z = random.uniform(-inner, zmax)
        cx = max(-HALF, min(HALF, x)); rr = random.uniform(0.03, 0.05)
        if (x - cx) ** 2 + y * y + z * z > (inner - rr) ** 2: continue
        if any((x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 < (rr + p[3]) ** 2 * 0.8 for p in pts[-200:]): continue
        pts.append((x, y, z, rr))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1); proto = bpy.context.active_object
    proto.data.materials.append(red_lacquer)
    for p in proto.data.polygons: p.use_smooth = True
    for (x, y, z, rr) in pts:
        o = proto.copy(); o.location = (x, y, z); o.scale = (rr, rr, rr); o.parent = root; scn.collection.objects.link(o)
    bpy.data.objects.remove(proto)
    root.location = (0, 0, RAD); root.rotation_euler = (0, 0, math.radians(-28))
    focus = Vector((0.2, -0.2, RAD)); aim = Vector((0, 0, RAD * 0.9)); dist, lens, height = 4.6, 85, 0.95
else:  # row
    RAD, HALF, N = 0.17, 0.26, 9
    filled = {2, 6}
    liq = red_lacquer
    for i in range(N):
        x, y = -1.6 + i * 0.42, 0.9 - i * 0.38   # a diagonal row receding toward the back-left... toward the back-right
        o = glass_capsule(f"cap{i}", RAD, HALF); o.rotation_euler = (0, math.radians(90), 0); o.location = (x, y, HALF + RAD)
        if i in filled:
            fi = capsule_mesh(f"fill{i}", RAD * 0.86, HALF * 0.97); fi.data.materials.append(liq)
            fi.rotation_euler = (0, math.radians(90), 0); fi.location = (x, y, HALF + RAD)
    focus = Vector((-1.6 + 2 * 0.42, 0.9 - 2 * 0.38, 0.4)); aim = Vector((0.1, -0.3, 0.42)); dist, lens, height = 5.0, 70, 0.75

# ---------------------------------------------------------------- light: a pool from above, a cobalt rim, nothing else
sp = bpy.data.lights.new("pool", "SPOT"); sp.energy = 900; sp.spot_size = math.radians(30); sp.spot_blend = 0.55
sp.shadow_soft_size = 0.25; sp.color = (1.0, 0.99, 0.97)
so = bpy.data.objects.new("pool", sp); scn.collection.objects.link(so)
so.location = aim + Vector((0.4, 0.3, 4.2)); so.rotation_euler = (aim - so.location).to_track_quat("-Z", "Y").to_euler()


def panel(name, strength, w, h, loc, color, tgt):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = (w, h, 1)
    o.rotation_euler = (tgt - Vector(loc)).to_track_quat("Z", "Y").to_euler(); o.visible_camera = False
    m, nt, out = mat(name); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)


panel("rim", 40, 0.15, 2.6, tuple(aim + Vector((-2.3, 1.6, 0.6))), (0.0, 0.012, 1.0), aim)    # cobalt rim, back-left
panel("rim2", 22, 0.12, 2.4, tuple(aim + Vector((2.4, 1.2, 0.5))), (1, 1, 1), aim)             # white edge line, back-right

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

# ---------------------------------------------------------------- camera: object in the right half; the card covers the left
cd = bpy.data.cameras.new("cam"); cd.lens = lens
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
cam.location = aim + Vector((-0.35, -dist, height))
cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.shift_x = -0.24
cd.dof.use_dof = True; cd.dof.focus_distance = (focus - cam.location).length; cd.dof.aperture_fstop = 2.0

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
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
