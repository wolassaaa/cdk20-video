"""HKBU SCIE1007 coursework science video. Style scout c4: the real surface as white architecture seen from high up, one red. Red is the real low-confidence tail. Method only."""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import build

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/c/_code/_raw"
os.makedirs(OUT, exist_ok=True)
sc, ob, cam = build(1280, 720, samples=128)
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.cycles.max_bounces = 6

bb = [Vector(v) for v in ob.bound_box]
c = sum(bb, Vector()) / 8
ob.data.transform(Matrix.Translation(-c))
ob.data.update()

m = bpy.data.materials.new("white")
m.use_nodes = True
nt = m.node_tree
N, L = nt.nodes, nt.links
bs = N["Principled BSDF"]
attr = N.new("ShaderNodeAttribute")
attr.attribute_name, attr.attribute_type = "conf", "GEOMETRY"
ramp = N.new("ShaderNodeValToRGB")
ramp.color_ramp.interpolation = "CONSTANT"
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (1, 0.0, 0.015, 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.7, (0.9, 0.9, 0.9, 1)   # pLDDT 0.7 is the real cut
L.new(attr.outputs["Fac"], ramp.inputs["Fac"])
L.new(ramp.outputs[0], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.55
ob.data.materials.append(m)


def plane(z, col, s=400):
    bpy.ops.mesh.primitive_plane_add(size=s, location=(0, 0, z))
    p = bpy.context.object
    mm = bpy.data.materials.new("p")
    mm.use_nodes = True
    mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*col, 1)
    p.data.materials.append(mm)
    return p


# white rooftops far below the protein, so the eye falls
ob.rotation_euler = (math.radians(-18), math.radians(12), math.radians(-24))
import random
random.seed(5)
wm = bpy.data.materials.new("w")
wm.use_nodes = True
wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.97, 0.97, 0.97, 1)
for i in range(240):
    x, y = random.uniform(-70, 70), random.uniform(-60, 90)
    w, d, h = random.uniform(3, 12), random.uniform(3, 12), random.uniform(10, 46)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, -70 + h / 2))
    o = bpy.context.object
    o.scale = (w, d, h)
    o.data.materials.append(wm)
plane(-70, (0.95, 0.95, 0.95))

# sun: hard, cool shadow comes from the sky colour
sun = bpy.data.lights.new("sun", "SUN")
sun.energy, sun.angle, sun.color = 1.7, math.radians(0.6), (1.0, 0.99, 0.97)
so = bpy.data.objects.new("sun", sun)
so.rotation_mode = "QUATERNION"
so.rotation_quaternion = Vector((-0.80, 0.30, 0.52)).to_track_quat("Z", "Y")
sc.collection.objects.link(so)
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.84, 0.90, 1.0, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.62
sc.world = w

cam.data.lens, cam.data.clip_end, cam.data.clip_start = 15, 800, 0.2
cam.rotation_mode = "QUATERNION"
cam.location = (-2.0, -4.0, 4.9)
tg = Vector((1.2, 1.6, -5))
cam.rotation_quaternion = (tg - cam.location).to_track_quat("-Z", "Y")
bpy.context.view_layer.update()
RQ = cam.rotation_quaternion
fpx = 15 / 36 * 1280


def ray(px, py, z):
    d = RQ @ Vector(((px - 640) / fpx, -(py - 360) / fpx, -1))
    return cam.location + d * ((z - cam.location.z) / d.z)


ROOF = -13.0
pc = ray(835, 575, ROOF)
right = (ray(1100, 590, ROOF) - ray(500, 530, ROOF)).normalized()     # type runs a little downhill on screen
ang = math.atan2(right.y, right.x)
dist = (pc - cam.location).length
bpy.ops.mesh.primitive_cube_add(size=1, location=(pc.x, pc.y, ROOF - 30))
b = bpy.context.object
b.scale = (31, 13, 60)
b.rotation_euler = (0, 0, ang)
b.data.materials.append(wm)
red = bpy.data.materials.new("red")
red.use_nodes = True
rb = red.node_tree.nodes["Principled BSDF"]
rb.inputs["Base Color"].default_value = (1, 0.0, 0.015, 1)
cu = bpy.data.curves.new("t", "FONT")
cu.body = "CDK20"
cu.font = bpy.data.fonts.load(r"C:/Windows/Fonts/seguibl.ttf")
cu.size, cu.extrude, cu.align_x, cu.align_y = 9.4, 0.02, "CENTER", "CENTER"
to = bpy.data.objects.new("t", cu)
to.location, to.rotation_euler = (pc.x, pc.y, ROOF + 0.03), (0, 0, ang)
sc.collection.objects.link(to)
to.data.materials.append(red)
sc.render.filepath = os.path.join(OUT, "c4.png")
bpy.ops.render.render(write_still=True)
print("c4 done")
