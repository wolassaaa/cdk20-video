"""HKBU SCIE1007 coursework science video. Puts the real CDK20 surface in a desert at colossal scale for the group F style scouts.

blender -b -t 4 -P bl_world.py -- tag samples scale cam_dist cam_h lens aim_z sun_az sun_el spin_deg people
Writes scouts/f/_work/world_<tag>.npz: beauty (linear RGB), z (distance), id (0 sky, 1 sand, 2 protein, 3 people), conf.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import VIEW, build

a = sys.argv[sys.argv.index("--") + 1:]
tag, spp, scale, dist, cam_h, lens, aim_z, az, el, spin, n_people = a[0], int(a[1]), float(a[2]), float(a[3]), float(a[4]), float(a[5]), float(a[6]), float(a[7]), float(a[8]), float(a[9]), int(a[10])
OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/f/_work"
W, H = 1280, 720
sc, ob, cam = build(W, H, samples=spp)
sc.render.film_transparent = False
sc.cycles.max_bounces = 3
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"

# centre the mesh, turn the M04 side to face the camera, then scale and bury the lower part
vs = np.empty(len(ob.data.vertices) * 3, np.float32)
ob.data.vertices.foreach_get("co", vs)
vs = vs.reshape(-1, 3)
cen = Vector(((vs.min(0) + vs.max(0)) / 2).tolist())
ob.data.transform(Matrix.Translation(-cen))
ob.rotation_mode = "QUATERNION"
ob.rotation_quaternion = Matrix.Rotation(math.radians(spin), 4, "Y").to_quaternion() @ VIEW.rotation_difference(Vector((0, -1, 0)))
ob.scale = (scale,) * 3
ob.location = (0, 0, 0)

# dunes: real terrain would be overkill, a warped fractal with one ridge direction reads as sand
N = 700
L = 90.0
fy = np.fft.fftfreq(N)[:, None]
fx = np.fft.rfftfreq(N)[None, :]
f = np.sqrt(fx ** 2 + fy ** 2)
f[0, 0] = 1
rng = np.random.default_rng(4)
ns = np.fft.irfft2((rng.normal(size=f.shape) + 1j * rng.normal(size=f.shape)) * f ** -1.9, s=(N, N))
ns = (ns - ns.mean()) / ns.std()
xs = np.linspace(-L / 2, L / 2, N)
X, Y = np.meshgrid(xs, xs)
ridge = 1 - np.abs(np.sin((X * 0.55 + Y * 0.22 + ns * 2.4) * 0.42))
GROUND = -1.15 * scale
Z = GROUND + 0.9 * ridge ** 1.6 * np.clip((np.hypot(X, Y) - 7) / 14, 0, 1) + 0.34 * ns * np.clip((np.hypot(X, Y) - 2) / 10, 0, 1)
Z += 0.55 * scale * np.exp(-((X / (3.4 * scale)) ** 2 + (Y / (3.0 * scale)) ** 2))  # sand banked against the object
idx = np.arange(N * N).reshape(N, N)
quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
me = bpy.data.meshes.new("sand")
me.vertices.add(N * N)
me.vertices.foreach_set("co", np.stack([X, Y, Z], -1).ravel().astype(np.float32))
me.loops.add(quads.size)
me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
me.polygons.add(len(quads))
me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
me.update(calc_edges=True)
me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
me.update()
sand = bpy.data.objects.new("sand", me)
sc.collection.objects.link(sand)


def height(x, y):
    i = int(np.clip((y + L / 2) / L * (N - 1), 0, N - 1))
    j = int(np.clip((x + L / 2) / L * (N - 1), 0, N - 1))
    return float(Z[i, j])


def pbr(name, col, rough, spec=0.3):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m


m_sand = pbr("sand", (0.62, 0.42, 0.24), 0.95, 0.15)
nt = m_sand.node_tree
tc, ns_t, bump = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexWave"), nt.nodes.new("ShaderNodeBump")
ns_t.inputs["Scale"].default_value, ns_t.inputs["Distortion"].default_value, ns_t.inputs["Detail"].default_value = 3.0, 9.0, 3.0
bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.1, 0.02
nt.links.new(tc.outputs["Object"], ns_t.inputs["Vector"])
nt.links.new(ns_t.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
sand.data.materials.append(m_sand)
rock = pbr("rock", (0.20, 0.19, 0.175), 0.62, 0.35)
ob.data.materials.append(rock)
# strata: board-marked concrete cut into the surface. Fine lines on a huge mass are what sell the scale
nt = rock.node_tree
tcr, wv, nz, mx, bp = (nt.nodes.new(x) for x in ("ShaderNodeTexCoord", "ShaderNodeTexWave", "ShaderNodeTexNoise", "ShaderNodeMath", "ShaderNodeBump"))
wv.bands_direction = "Z"
wv.inputs["Scale"].default_value, wv.inputs["Distortion"].default_value, wv.inputs["Detail"].default_value, wv.inputs["Detail Scale"].default_value = 13.0, 2.6, 4.0, 3.0
nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 9.0, 6.0
mx.operation = "MULTIPLY"
nt.links.new(tcr.outputs["Object"], wv.inputs["Vector"])
nt.links.new(tcr.outputs["Object"], nz.inputs["Vector"])
nt.links.new(wv.outputs["Fac"], mx.inputs[0])
nt.links.new(nz.outputs["Fac"], mx.inputs[1])
bp.inputs["Strength"].default_value, bp.inputs["Distance"].default_value = 0.8, 0.045
nt.links.new(mx.outputs[0], bp.inputs["Height"])
nt.links.new(bp.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])

# people: small capsules along a curve, height about one ~100th of the object
peop = []
if n_people:
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.013, radius2=0.012, depth=0.13, location=(0, 0, 0))
    body = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.015, location=(0, 0, 0.08))
    head = bpy.context.object
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    head.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.data.materials.append(pbr("p", (0.02, 0.015, 0.012), 0.8))
    r = np.random.default_rng(9)
    for i in range(n_people):
        t = (i + 0.9 * r.uniform(-1, 1)) / max(1, n_people - 1)
        if r.uniform() < 0.25:
            t += 0.05
        x = -7.5 + 12.0 * (t // 0.14) * 0.14 + r.normal(0, 0.16) + 1.2 * ((t % 0.14) / 0.14) * 0.3
        y = -dist * 0.46 - 1.6 * np.sin(t * 2.6) + r.normal(0, 0.14)
        o = body.copy()
        sc.collection.objects.link(o)
        o.location = (x, y, height(x, y) + 0.06)
        o.pass_index = 3
        peop.append(o)
    bpy.data.objects.remove(body)
ob.pass_index, sand.pass_index = 2, 1

sun = bpy.data.lights.new("sun", "SUN")
sun.energy, sun.angle, sun.color = 6.0, math.radians(0.8), (1.0, 0.86, 0.68)
so = bpy.data.objects.new("sun", sun)
sc.collection.objects.link(so)
d = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
so.rotation_mode = "QUATERNION"
so.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.72, 0.5, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
sc.world = w

cam.data.lens, cam.data.clip_start, cam.data.clip_end = lens, 0.05, 400
cam.location = Vector((0, -dist, height(0, -dist) + cam_h))
look = (Vector((0, 0, aim_z)) - cam.location).normalized()
cam.rotation_mode = "QUATERNION"
cam.rotation_quaternion = look.to_track_quat("-Z", "Y")


def grab(path):
    im = bpy.data.images.load(path)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    os.remove(path)
    return px.reshape(H, W, 4)[::-1]


sc.render.filepath = os.path.join(OUT, f"_{tag}_b.exr")
bpy.ops.render.render(write_still=True)
beauty = grab(sc.render.filepath)

# data pass: emission override holding distance, object id and pLDDT
m = bpy.data.materials.new("data")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
camd, info, attr, comb, em, out = (nt.nodes.new(x) for x in ("ShaderNodeCameraData", "ShaderNodeObjectInfo", "ShaderNodeAttribute", "ShaderNodeCombineColor", "ShaderNodeEmission", "ShaderNodeOutputMaterial"))
attr.attribute_name, attr.attribute_type = "conf", "GEOMETRY"
nt.links.new(camd.outputs["View Z Depth"], comb.inputs[0])
nt.links.new(info.outputs["Object Index"], comb.inputs[1])
nt.links.new(attr.outputs["Fac"], comb.inputs[2])
nt.links.new(comb.outputs[0], em.inputs["Color"])
nt.links.new(em.outputs[0], out.inputs["Surface"])
sc.view_layers[0].material_override = m
sc.cycles.samples = 1
sc.cycles.pixel_filter_type = "BOX"
w.node_tree.nodes["Background"].inputs[1].default_value = 0
sc.render.filepath = os.path.join(OUT, f"_{tag}_d.exr")
bpy.ops.render.render(write_still=True)
data = grab(sc.render.filepath)
np.savez(os.path.join(OUT, f"world_{tag}.npz"), beauty=beauty[..., :3].astype(np.float32), z=data[..., 0].astype(np.float32), id=data[..., 1].astype(np.float32), conf=data[..., 2].astype(np.float32))
print("done", tag)
