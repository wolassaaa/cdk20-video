"""1-04 opt1 'glass-row': ten glass test tubes on a black glossy stage; three hold lit vermilion, seven are empty
glass lit only by a cold blue rim. Cycles.

blender -b --factory-startup -P vials.py -- --out X.png [--shot row|low] [--samples 256] [--pct 100]
  row : frontal, slightly above; the whole row reads as one count (survival frame)
  low : low macro along the row, shallow focus on a lit tube (unmet-need frame)
"""
import bpy, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--shot", default="row")
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--lit", default="1,4,8")
A = ap.parse_args(argv)
LIT = {int(i) for i in A.lit.split(",") if i != ""}

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    scn.cycles.device = "GPU"
except Exception as e:
    print("GPU fallback", e)
scn.cycles.samples = A.samples
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16; scn.cycles.glossy_bounces = 8
scn.cycles.caustics_refractive = False
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = A.pct
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"
scn.view_settings.exposure = 0.0
scn.render.image_settings.file_format = "PNG"
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1)


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def glass():
    m, nt, out = mat("glass")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.92, 0.95, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.47
    b.inputs["Transmission Weight"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def liquid():
    m, nt, out = mat("liquid")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (1.0, 0.06, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Transmission Weight"].default_value = 0.6
    b.inputs["Emission Color"].default_value = (1.0, 0.018, 0.006, 1)
    b.inputs["Emission Strength"].default_value = 1.5
    # seen through the neighbouring glass (transmission rays) the liquid is dark, so empty tubes stay blue
    lp = nt.nodes.new("ShaderNodeLightPath"); dk = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dk.inputs["Color"].default_value = (0.02, 0.0, 0.0, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 2.5
    nt.links.new(lp.outputs["Transmission Depth"], gt.inputs[0])
    nt.links.new(gt.outputs[0], mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(dk.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def floor():
    m, nt, out = mat("floor")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
    b.inputs["Roughness"].default_value = 0.16
    b.inputs["Specular IOR Level"].default_value = 0.6
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


G, L, F = glass(), liquid(), floor()
R, H, N, GAP = 0.11, 1.55, 10, 0.40


def tube(x, lit):
    # glass: cylinder + hemisphere, hollow via solidify
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=R, depth=H, location=(x, 0, R + H / 2), end_fill_type="NOTHING")
    cyl = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=R, location=(x, 0, R))
    sph = bpy.context.object
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    for v in sph.data.vertices: v.select = v.co.z > 1e-4
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="VERT"); bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT"); cyl.select_set(True); sph.select_set(True)
    bpy.context.view_layer.objects.active = cyl; bpy.ops.object.join()
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.remove_doubles(threshold=0.002)
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode="OBJECT")
    t = bpy.context.object
    s = t.modifiers.new("sol", "SOLIDIFY"); s.thickness = 0.012; s.offset = -1
    t.modifiers.new("sub", "SUBSURF").levels = 1
    for p in t.data.polygons: p.use_smooth = True
    t.data.materials.append(G)
    # lip ring at the top
    bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.002, minor_radius=0.012, location=(x, 0, R + H), major_segments=64, minor_segments=16)
    bpy.context.object.data.materials.append(G)
    for p in bpy.context.object.data.polygons: p.use_smooth = True
    if lit:
        r2, lh = R - 0.016, H * 0.62
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r2, depth=lh, location=(x, 0, R + lh / 2))
        c = bpy.context.object
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r2, location=(x, 0, R))
        s2 = bpy.context.object
        bpy.ops.object.select_all(action="DESELECT"); c.select_set(True); s2.select_set(True)
        bpy.context.view_layer.objects.active = c; bpy.ops.object.join()
        for p in bpy.context.object.data.polygons: p.use_smooth = True
        bpy.context.object.data.materials.append(L)


x0 = -GAP * (N - 1) / 2
for i in range(N):
    tube(x0 + i * GAP, i in LIT)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
bpy.context.object.data.materials.append(F)


def area(name, loc, rot, size, energy, rgb, shape="RECTANGLE", sy=None):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.color = rgb; d.shape = shape
    d.size = size; d.size_y = sy if sy else size
    o = bpy.data.objects.new(name, d); scn.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o


BLUE = (0.10, 0.20, 1.0)
# cold blue strip lights behind-left and behind-right: rim every tube's edges
area("rimL", (-6.5, 3.5, 2.2), (math.radians(80), 0, math.radians(-120)), 0.25, 2200, BLUE, sy=4)
area("rimR", (6.5, 3.5, 2.2), (math.radians(80), 0, math.radians(120)), 0.25, 2200, BLUE, sy=4)
# very soft top fill, slightly blue, to give the glass a body
area("top", (0, -0.5, 4.5), (0, 0, 0), 4.0, 70, (0.55, 0.62, 1.0))
# a thin white hairline from front-top for one crisp highlight on each tube
area("spec", (0.6, -4, 3.2), (math.radians(55), 0, math.radians(8)), 0.08, 160, (1, 1, 1), sy=3)

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam); scn.camera = cam
if A.shot == "row":
    cam_d.lens = 50
    cam.location = (0, -7.6, 1.55)
    tgt = Vector((0, 0, 0.82))
else:  # low macro along the row
    cam_d.lens = 55
    cam.location = (x0 - 2.4, -3.0, 0.95)
    tgt = Vector((x0 + 4 * GAP, 0, 0.85))
    cam_d.dof.use_dof = True
    cam_d.dof.focus_distance = (Vector((x0 + 4 * GAP, 0, 0.7)) - cam.location).length
    cam_d.dof.aperture_fstop = 2.0
d = tgt - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
if A.shot == "row":
    cam_d.shift_y = -0.06

scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("WROTE", A.out)
