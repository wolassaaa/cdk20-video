"""HKBU SCIE1007 coursework science video. Style scout c2: the real CDK20 surface as a concrete mass in a brutalist hall, red portal behind it. Method only."""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import build

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/c/_code/_raw"
os.makedirs(OUT, exist_ok=True)
random.seed(7)
sc, ob, cam = build(1280, 720, samples=220)
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.cycles.max_bounces = 5

# centre the mesh, face it to the camera
bb = [Vector(v) for v in ob.bound_box]
c = sum(bb, Vector()) / 8
ob.data.transform(Matrix.Translation(-c))
ob.data.update()
ob.scale = (4.5, 4.5, 4.5)
ob.rotation_euler = (math.radians(90), math.radians(-14), 0)
ob.location = (0.5, 4, 21)


def concrete(name, base=0.42, scale=1.0, rough=0.85, boards=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n1 = N.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value, n1.inputs["Detail"].default_value = 0.5 * scale, 10
    n2 = N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value, n2.inputs["Detail"].default_value = 7 * scale, 8
    L.new(tc.outputs["Object"], n1.inputs["Vector"])
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    ramp = N.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = 0.3, 0.7
    ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = base * 0.55, base * 1.25
    L.new(n1.outputs[0], ramp.inputs["Value"])
    L.new(ramp.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.6, 0.12
    if boards:
        w = N.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = "Z"
        w.inputs["Scale"].default_value = 0.28 * scale
        w.inputs["Distortion"].default_value = 0.6
        w.inputs["Detail"].default_value = 2
        L.new(tc.outputs["Object"], w.inputs["Vector"])
        mx = N.new("ShaderNodeMath")
        mx.operation = "ADD"
        L.new(w.outputs[1], mx.inputs[0])
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 0.6
        L.new(n2.outputs[0], mul.inputs[0])
        L.new(mul.outputs[0], mx.inputs[1])
        L.new(mx.outputs[0], bump.inputs["Height"])
    else:
        L.new(n2.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs[0], bs.inputs["Normal"])
    return m


def emit(name, col, s):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N = m.node_tree.nodes
    N.clear()
    e, o = N.new("ShaderNodeEmission"), N.new("ShaderNodeOutputMaterial")
    e.inputs[0].default_value, e.inputs[1].default_value = (*col, 1), s
    m.node_tree.links.new(e.outputs[0], o.inputs[0])
    return m


def box(name, loc, size, mat, rot=None):
    me = bpy.data.meshes.new(name)
    x, y, z = size[0] / 2, size[1] / 2, size[2] / 2
    v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.update()
    o = bpy.data.objects.new(name, me)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    sc.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


con = concrete("con", 0.46)
con_d = concrete("con_d", 0.26)
floor = concrete("floor", 0.10, rough=0.22, boards=False)
ob.data.materials.append(concrete("prot", 0.62, scale=2.2, rough=0.8, boards=False))
red = emit("red", (1.0, 0.0, 0.004), 3.2)

HX, TOP, BACK = 40, 62, 34
box("floor", (0, 0, -0.5), (240, 240, 1), floor)
box("ceil", (0, 0, TOP + 0.5), (240, 240, 1), con)
box("lw", (-HX - 1, 0, TOP / 2), (2, 240, TOP), con)
box("rw", (HX + 1, 0, TOP / 2), (2, 240, TOP), con)
box("bwL", (-26, BACK, TOP / 2), (28, 2, TOP), con_d)
box("bwR", (26, BACK, TOP / 2), (28, 2, TOP), con_d)
box("bwT", (0, BACK, 49), (24, 2, 26), con_d)
box("portal", (0, BACK + 1.2, 18), (24, 0.5, 36), red)

# columns and coffers, repeated blocks stepping into the distance
for i in range(6):
    y = -30 + i * 12.5
    for sx in (-1, 1):
        box(f"col{i}{sx}", (sx * 29, y, TOP / 2), (5, 6, TOP), con)
for i in range(46):
    x = random.uniform(-36, 36)
    y = random.uniform(-26, 32)
    h = random.uniform(5, 26)
    box(f"h{i}", (x, y, TOP - h / 2 + random.uniform(-3, 0)), (random.uniform(3, 11), random.uniform(3, 11), h), con_d if i % 3 else con)
# slabs that hang in the air, off the ceiling, slightly tilted: the room has stopped behaving
for i, (x, y, z, sx, sy, sz, t) in enumerate([(-21, -6, 27, 12, 7, 1.5, .10), (22, -3, 23, 9, 10, 1.2, -.14), (-17, 17, 9, 6, 6, 1.1, .2), (20, 15, 8, 5, 8, 1, -.1), (-27, 9, 15, 7, 5, 6, .06), (26, 7, 17, 5, 5, 9, -.07)]):
    box(f"f{i}", (x, y, z), (sx, sy, sz), con, (t, -t * 1.5, t))

# monumental letters standing on the floor, a person next to them for scale
cu = bpy.data.curves.new("t", "FONT")
cu.body = "CDK20"
cu.font = bpy.data.fonts.load(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/fonts/ArchivoBlack-Regular.ttf")
cu.size, cu.extrude, cu.align_x = 7.4, 0.5, "CENTER"
to = bpy.data.objects.new("t", cu)
to.location, to.rotation_euler = (-1, -14, 0), (math.radians(90), 0, 0)
sc.collection.objects.link(to)
to.data.materials.append(concrete("letters", 0.015, scale=2.0, boards=False))

fig = emit("fig", (0.0, 0.0, 0.0), 0)
fx, fy = 0.35, -14.3
fz = 4.13
for loc, r1, r2, d in [((fx - 0.11, fy, fz + 0.42), 0.075, 0.11, 0.84), ((fx + 0.11, fy, fz + 0.42), 0.075, 0.11, 0.84), ((fx, fy, fz + 1.16), 0.17, 0.25, 0.66)]:
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=d, location=loc)
    bpy.context.object.data.materials.append(fig)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.115, location=(fx, fy, fz + 1.64))
bpy.context.object.data.materials.append(fig)

# light: the portal does the work, a thin cold sun finds the concrete
sun = bpy.data.lights.new("sun", "SUN")
sun.energy, sun.angle, sun.color = 0.0, math.radians(1), (0.9, 0.95, 1.0)
so = bpy.data.objects.new("sun", sun)
so.rotation_euler = (math.radians(38), math.radians(-48), 0)
sc.collection.objects.link(so)
back = bpy.data.lights.new("back", "AREA")
back.energy, back.size, back.color = 30000, 26, (1, 0.0, 0.01)
bo = bpy.data.objects.new("back", back)
bo.location, bo.rotation_euler = (0, 26, 12), (math.radians(90), 0, 0)
sc.collection.objects.link(bo)
fill = bpy.data.lights.new("fill", "AREA")
fill.energy, fill.size, fill.color = 520, 14, (0.75, 0.85, 1.0)
fo = bpy.data.objects.new("fill", fill)
fo.location = (-22, -42, 30)
fo.rotation_euler = (Vector((0, 0, 15)) - fo.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(fo)
sp = bpy.data.lights.new("spot", "SPOT")
sp.energy, sp.spot_size, sp.spot_blend, sp.shadow_soft_size, sp.color = 150000, math.radians(38), 0.08, 0.15, (0.82, 0.9, 1.0)
spo = bpy.data.objects.new("spot", sp)
spo.location = (-27, -22, 50)
spo.rotation_euler = (Vector((0, 4, 21)) - spo.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(spo)
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
sc.world = w

cam.data.lens, cam.data.clip_end, cam.data.clip_start = 28, 400, 0.5
cam.data.shift_y = 0.17
cam.rotation_mode = "XYZ"
cam.location, cam.rotation_euler = (0, -44, 2.4), (math.radians(90), 0, 0)
for o in sc.collection.objects:
    if o.name[0] == "h" or o.name == "ceil":
        o.visible_shadow = False
rc = bpy.data.collections.new("recv")
rc.objects.link(ob)
spo.light_linking.receiver_collection = rc
sc.render.filepath = os.path.join(OUT, "c2.png")
bpy.ops.render.render(write_still=True)
print("c2 done")
