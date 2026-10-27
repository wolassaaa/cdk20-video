"""T3 feasibility test: an 8-second animated 3D shot rendered on the RTX 5080.

The camera pushes from a wide view of the AlphaFold CDK20 hologram into the ATP pocket; the low-confidence tail
(303-346) is pulled out of the pocket and fades, and the pocket rings light up. Measures render cost per finished second.

Run:  blender -b -P T3_keyhole_anim.py -- <pdb> <outdir>
"""
import bpy, sys, math, time, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PDB, OUT = argv[0], argv[1].rstrip("/\\")
FPS, SECONDS = 30, 8

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "GPU"
sc.cycles.samples = 256
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, FPS * SECONDS
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = f"{OUT}/T3_frames/f"

CYAN, ORANGE, ICE = (0.25, 0.85, 1.0), (1.0, 0.38, 0.10), (0.75, 0.95, 1.0)

def holo(name, color, strength, edge):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = edge
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY_ADD"
    k.inputs[1].default_value, k.inputs[2].default_value = 0.8, 0.2
    k.use_clamp = True
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], k.inputs[0])
    nt.links.new(k.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m, em

def glow(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m, em

def tube(points, mat, radius, name):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth, cd.bevel_resolution, cd.resolution_u = radius, 4, 8
    sp = cd.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for j, p in enumerate(points):
        sp.points[j].co = (*p, 1)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(points))
    ob = bpy.data.objects.new(name, cd)
    ob.data.materials.append(mat)
    sc.collection.objects.link(ob)
    return ob

def ring(loc, radius, thick, mat, rot):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=radius, minor_radius=thick,
                                     major_segments=160, minor_segments=8, rotation=rot)
    bpy.context.object.data.materials.append(mat)
    return bpy.context.object

def ease(owner, path, f0, v0, f1, v1):
    """Two keyframes; Blender's default bezier interpolation gives the ease in/out."""
    setattr(owner, path, v0)
    owner.keyframe_insert(path, frame=f0)
    setattr(owner, path, v1)
    owner.keyframe_insert(path, frame=f1)

w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.001, 0.002, 0.004, 1)
sc.world = w

ca = []
for line in open(PDB, encoding="utf-8"):
    if line.startswith("ATOM") and line[12:16].strip() == "CA":
        ca.append((int(line[22:26]), Vector((float(line[30:38]), float(line[38:46]), float(line[46:54])))))
c = sum((p for _, p in ca), Vector()) / len(ca)
ca = [(r, (p - c) * 0.1) for r, p in ca]

core_m, _ = holo("core", CYAN, 1.6, 0.55)
tail_m, tail_em = holo("tail", ORANGE, 3.0, 0.5)
tube([p for r, p in ca if r <= 303], core_m, 0.028, "core")
arg = next(p for r, p in ca if r == 305)
met = next(p for r, p in ca if r == 84)
pocket = (arg + met) / 2

# the tail and Arg305 are parented to one empty so they can be pulled out of the pocket together
pull = bpy.data.objects.new("pull", None)
sc.collection.objects.link(pull)
tail = tube([p for r, p in ca if r >= 302], tail_m, 0.04, "tail")
tail.parent = pull
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=arg, segments=48, ring_count=24)
argob = bpy.context.object
arg_m, arg_em = glow("Arg305", (1.0, 0.6, 0.3), 10)
argob.data.materials.append(arg_m)
argob.parent = pull

r1_m, r1_em = glow("pocket", ICE, 4)
r2_m, r2_em = glow("pocket2", ICE, 2)
ring(pocket, 0.55, 0.004, r1_m, (math.radians(70), 0, math.radians(20)))
ring(pocket, 0.66, 0.002, r2_m, (math.radians(65), 0, math.radians(25)))
ui_m, _ = glow("ui", CYAN, 0.5)
for i, (rx, rz) in enumerate([(80, 0), (75, 40), (88, -30)]):
    ring((0, 0, 0), 3.0 + i * 0.35, 0.003, ui_m, (math.radians(rx), 0, math.radians(rz)))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=30, location=(0, 0, min(p.z for _, p in ca) - 0.8))
g = bpy.context.object
g.modifiers.new("wire", "WIREFRAME").thickness = 0.008
g.data.materials.append(glow("grid", CYAN, 0.12)[0])

# camera: wide three-quarter view -> close on the pocket; a target empty keeps it aimed
cd = bpy.data.cameras.new("cam")
cd.lens = 50
cd.dof.use_dof, cd.dof.aperture_fstop = True, 2.0
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
aim = bpy.data.objects.new("aim", None)
sc.collection.objects.link(aim)
tc = cam.constraints.new("TRACK_TO")
tc.target, tc.track_axis, tc.up_axis = aim, "TRACK_NEGATIVE_Z", "UP_Y"
cd.dof.focus_object = aim

F = lambda s: int(s * FPS) + 1
wide, close = Vector((5.5, -11.0, 3.2)), pocket + Vector((2.6, -6.2, 1.5))
ease(cam, "location", F(0), wide, F(4.5), close)
ease(aim, "location", F(0), Vector((0, 0, 0)), F(4.5), pocket)
# beat 2 (4.8-7.0 s): the tail is pulled out along the view-right/up direction and fades
away = (Vector((1.0, 0.2, 0.9))).normalized() * 3.5
ease(pull, "location", F(4.8), Vector((0, 0, 0)), F(7.0), away)
ease(tail_em.inputs["Strength"], "default_value", F(5.6), 3.0, F(7.2), 0.0)
ease(arg_em.inputs["Strength"], "default_value", F(5.6), 10.0, F(7.0), 0.0)
# beat 3 (6.4-8.0 s): the freed pocket lights up
ease(r1_em.inputs["Strength"], "default_value", F(6.4), 4.0, F(7.6), 14.0)
ease(r2_em.inputs["Strength"], "default_value", F(6.4), 2.0, F(7.6), 8.0)

# screen positions of the points the 2D labels point at, for every frame (0..1 from top-left)
from bpy_extras.object_utils import world_to_camera_view
anchors = {"pocket": lambda: pocket, "arg305": lambda: argob.matrix_world.translation.copy(),
           "met84": lambda: met, "tail_mid": lambda: pull.matrix_world @ tail_mid}
tail_mid = [p for r, p in ca if r == 325][0]
track = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    row = {}
    for k, fn in anchors.items():
        v = world_to_camera_view(sc, cam, fn())
        row[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
    track.append(row)
json.dump(track, open(f"{OUT}/T3_anchors.json", "w"))
print("ANCHORS", len(track))
if "--anchors-only" in argv:
    sys.exit(0)

t = time.perf_counter()
bpy.ops.render.render(animation=True)
dt = time.perf_counter() - t
res = {"frames": FPS * SECONDS, "seconds_of_film": SECONDS, "render_s": round(dt, 1),
       "render_s_per_film_s": round(dt / SECONDS, 1), "samples": sc.cycles.samples}
json.dump(res, open(f"{OUT}/T3_result.json", "w"), indent=2)
print("RESULT", json.dumps(res))
