"""HKBU SCIE1007 coursework science video. Style scout c5: time stopped. The real surface cut to low poly red facets, breaking apart in a white room, a black key held up in first person. Method only."""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import build

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/c/_code/_raw"
os.makedirs(OUT, exist_ok=True)
random.seed(3)
sc, ob, cam = build(1280, 720, samples=128)
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.cycles.max_bounces = 6

bb = [Vector(v) for v in ob.bound_box]
c = sum(bb, Vector()) / 8
ob.data.transform(Matrix.Translation(-c))
ob.data.update()
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
d = ob.modifiers.new("d", "DECIMATE")
d.ratio = 0.011
bpy.ops.object.modifier_apply(modifier="d")
me = ob.data
print("tris", len(me.polygons))

# pull every triangle out as its own piece so a share of them can leave the body
V = np.array([v.co[:] for v in me.vertices], np.float64)
T = [list(p.vertices) for p in me.polygons]
impact = np.array([4.1, 0.9, 1.4])
verts, faces, red_ids = [], [], []
for t in T:
    if len(t) != 3:
        t = t[:3]
    p = V[t]
    ctr = p.mean(0)
    dv = ctr - impact
    r = np.linalg.norm(dv)
    keep = r > 2.5 + random.uniform(-0.7, 0.7)
    if not keep:
        if random.random() < 0.42:
            continue
        k = (1 - r / 4.2)
        s = random.uniform(0.75, 1.15)
        dir_ = dv / max(r, 1e-3) * 0.2 + np.array([0.95, -0.10, 0.25]) + np.random.default_rng(len(verts)).normal(0, .19, 3)
        off = dir_ * (0.8 + random.expovariate(0.5)) * (0.5 + k)
        R = np.array(Euler((random.uniform(-3, 3), random.uniform(-3, 3), random.uniform(-3, 3))).to_matrix())
        p = (p - ctr) @ R.T * s * 1.55 + ctr + off
    b = len(verts)
    verts += [tuple(x) for x in p]
    faces.append((b, b + 1, b + 2))
mesh = bpy.data.meshes.new("low")
mesh.from_pydata(verts, [], faces)
mesh.update()
ob.data = mesh


def mat(name, col, em=0.0, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = em
    return m


RED = mat("red", (0.66, 0.006, 0.006), 0.0, 0.6)
RED.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
WHITE = mat("white", (0.98, 0.99, 0.99))
BLACK = mat("black", (0.0, 0.0, 0.0), 0, 1.0)
BLACK.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0
ob.data.materials.append(RED)
ob.location = (-2.5, 3.2, 2.72)
ob.visible_diffuse = False
ob.rotation_euler = (math.radians(90), math.radians(-6), 0)
ob.scale = (0.84, 0.84, 0.84)


def box(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    o.data.materials.append(m)
    return o


box((0, 8, -0.5), (60, 80, 1), WHITE)
box((0, 18, 8), (60, 1, 18), WHITE)
box((-13, 8, 8), (1, 40, 18), WHITE)
box((13, 8, 8), (1, 40, 18), WHITE)
box((0, 8, 14.5), (60, 80, 1), WHITE)
for x, y, s in [(-10.5, 7, 2.4), (10.5, 7, 2.4), (-9, 13, 2.4), (9, 13, 2.4)]:
    box((x, y, 7), (s, s, 14), WHITE)
for x, y, z, sx, sy, sz in [(-7, 1, 0.6, 3, 2, 1.2), (7.6, 2, 1, 2.4, 4, 2), (-4.5, 13, 1.4, 6, 2, 2.8), (6, 15, 2, 3, 3, 4)]:
    box((x, y, z), (sx, sy, sz), WHITE)

# the word sits on the wall, big, over the room
cu = bpy.data.curves.new("t", "FONT")
cu.body = "CDK20"
cu.font = bpy.data.fonts.load(r"C:/Windows/Fonts/seguibli.ttf")
cu.size, cu.extrude, cu.align_x, cu.align_y = 8.8, 0.08, "CENTER", "CENTER"
to = bpy.data.objects.new("t", cu)
to.location, to.rotation_euler = (0.2, 17.4, 10.3), (math.radians(90), 0, 0)
sc.collection.objects.link(to)
to.data.materials.append(BLACK)

# a black low poly key, first person, big in the lower right. Not a molecule, the film's own metaphor.
kk = bpy.data.objects.new("key", None)
sc.collection.objects.link(kk)
parts = []
bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.105, major_segments=7, minor_segments=3, location=(0, -0.9, 0), rotation=(0, 0, 0))
parts.append(bpy.context.object)
parts.append(box((0, 0.1, 0), (0.15, 1.45, 0.12), BLACK))
parts.append(box((0.14, 0.65, 0), (0.2, 0.13, 0.12), BLACK))
parts.append(box((0.17, 0.42, 0), (0.26, 0.13, 0.12), BLACK))
parts[0].data.materials.append(BLACK)
for p in parts:
    p.data.polygons.foreach_set("use_smooth", [False] * len(p.data.polygons))
    p.parent = kk
kk.location = (1.72, -4.6, 1.56)
kk.rotation_euler = (math.radians(30), math.radians(-30), math.radians(30))
kk.scale = (0.86, 0.86, 0.86)

w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.97, 1.0, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.1
sc.world = w
for n, loc, e, sz in [("a", (0, 2, 13.6), 900, 12), ("b", (-6, -6, 12), 420, 9)]:
    l = bpy.data.lights.new(n, "AREA")
    l.energy, l.size, l.color = e, sz, (0.93, 0.99, 1.0)
    o = bpy.data.objects.new(n, l)
    o.location = loc
    sc.collection.objects.link(o)

cam.data.lens, cam.data.clip_end, cam.data.clip_start = 22, 200, 0.05
cam.rotation_mode = "QUATERNION"
cam.location = (0, -7, 2.3)
cam.rotation_quaternion = (Vector((0.5, 6, 4.0)) - cam.location).to_track_quat("-Z", "Y")
sc.render.filepath = os.path.join(OUT, "c5.png")
bpy.ops.render.render(write_still=True)
print("c5 done")
