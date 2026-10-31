"""HKBU SCIE1007 coursework science video, dawn art direction. T5: inside the real pocket (AlphaFold 1-302 surface) behind 048 in our re-docked pose, looking out through the mouth at the horizon.
Same geometry as the docking input and our pose; nothing moved. The wall behind the lens is simply not drawn.
blender -b -t 4 -P bl_t5.py -- <outdir> [--test] [--back 10 --roll 0 --focal 18 --sx 0]
"""
import argparse, json, math, os, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_core as B
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--test", action="store_true")
ap.add_argument("--back", type=float, default=11)
ap.add_argument("--roll", type=float, default=0)
ap.add_argument("--pitch", type=float, default=0)
ap.add_argument("--yawo", type=float, default=0)
ap.add_argument("--focal", type=float, default=20)
ap.add_argument("--sx", type=float, default=0)
ap.add_argument("--sunel", type=float, default=3)
ap.add_argument("--sunaz", type=float, default=-10)
ap.add_argument("--samples", type=int, default=200)
A = ap.parse_args(argv)

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work")
D = np.load(WORK + "/rock_302.npz")
V, Q = D["verts"].astype(np.float64), D["quads"]
P = np.load(WORK + "/pose048.npz")
M = json.load(open(WORK + "/mouth.json"))
d0, c = np.array(M["open"]), np.array(M["centre"])

sc = B.setup(samples=A.samples, pct=50 if A.test else 100)
sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.transparent_max_bounces = 4, 3, 16

rock = B.diffuse("rock", (0.8, 0.8, 0.8))
nt = rock.node_tree
geo, mix, tr = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
out = nt.nodes["Material Output"]
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
nt.links.new(nt.nodes["Principled BSDF"].outputs[0], mix.inputs[1])
nt.links.new(tr.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
bone = B.diffuse("bone", (0.82, 0.78, 0.7), rough=.5)
SC = .1


def frame(roll, pitch=0.0, yaw=0.0):
    d = d0.copy()
    up0 = np.array([0, 0, 1.0]) - d * d[2]
    up0 /= np.linalg.norm(up0)
    r0 = np.cross(d, up0)
    a, p, y = math.radians(roll), math.radians(pitch), math.radians(yaw)
    d2 = d * math.cos(p) * math.cos(y) + up0 * math.sin(p) + r0 * math.sin(y) * math.cos(p)
    d2 /= np.linalg.norm(d2)
    u = up0 - d2 * np.dot(up0, d2); u /= np.linalg.norm(u)
    r = np.cross(d2, u)
    up = u * math.cos(a) + r * math.sin(a)
    right = np.cross(d2, up)
    return np.stack([right, d2, up], 0)


def sphere(loc, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=tuple(loc), segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    return bpy.context.object


def cyl(a, b, r):
    a, b = Vector(a), Vector(b)
    dv = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=dv.length, location=(a + b) / 2, vertices=20)
    o = bpy.context.object
    o.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.shade_smooth()
    return o


def ligand(R, origin):
    T = lambda q: (np.asarray(q, float) - origin) @ R.T * SC
    objs = []
    el, xyz = P["el"], P["xyz"]
    AT = dict(C=.42, N=.40, O=.40, S=.5, H=.22)
    for e, q in zip(el, xyz):
        objs.append(sphere(T(q), AT.get(str(e), .4) * SC))
    for i, j, order in P["bonds"]:
        i, j = int(i), int(j)
        a, b = T(xyz[i]), T(xyz[j])
        if order < 1.9:
            objs.append(cyl(a, b, .15 * SC))
        else:
            off = np.cross(b - a, [0, 0, 1.0]); off = off / (np.linalg.norm(off) + 1e-9) * .12 * SC
            objs += [cyl(a + off, b + off, .1 * SC), cyl(a - off, b - off, .1 * SC)]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = "lig"
    o.data.materials.clear()
    o.data.materials.append(bone)
    return o


def shot(name, roll, back, pitch, yaw):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    R = frame(roll, pitch, yaw)
    camw = c - R[1] * back         # camera behind the ligand, along the view axis
    pv = (V - camw) @ R.T * SC
    r = B.mesh("rock", pv, Q, rock)
    lig = ligand(R, camw)
    B.camera((0, 0, 0), A.focal, shift_x=A.sx, clip=(.05, 400))
    s = B.sun("sun", A.sunaz, A.sunel, angle=2.0)
    ld = bpy.data.lights.new("fill", "POINT")
    ld.energy, ld.shadow_soft_size = 3.2, .15
    f = bpy.data.objects.new("fill", ld)
    f.location = (0.3, .35, .25)
    sc.collection.objects.link(f)
    plan = {"sun": (0.0, ["sun", "rock", "lig"]), "sky": (1.0, ["rock", "lig"]), "fill": (0.0, ["fill", "lig"])}
    B.layers(A.out, name, plan, [s, f, r, lig], data_scale=None)


if A.test:
    sc.cycles.samples = 48
    var = [(60, 9, 14, 0), (240, 9, 14, 0), (60, 8, 12, 0), (240, 10, 16, 0), (60, 9, 14, 12), (240, 9, 14, -12), (30, 9, 14, 0), (270, 9, 14, 0)]
    for k, (roll, back, foc, pit) in enumerate(var):
        A.focal = foc
        shot(f"t{k:02d}", roll, back, pit, 0)
        print("VAR", k, roll, back, foc, pit, flush=True)
else:
    shot("T5", A.roll, A.back, A.pitch, A.yawo)
    R = frame(A.roll, A.pitch, A.yawo)
    camw = c - R[1] * A.back
    f = A.focal / 36 * 1920
    lc = (c - camw) @ R.T
    print("LIG_PX", 960 + f * lc[0] / lc[1] - A.sx * 1920, 720 - f * lc[2] / lc[1], flush=True)
    json.dump(dict(lig_px=[960 + f * lc[0] / lc[1] - A.sx * 1920, 720 - f * lc[2] / lc[1]]), open(os.path.join(A.out, "T5_px.json"), "w"))
