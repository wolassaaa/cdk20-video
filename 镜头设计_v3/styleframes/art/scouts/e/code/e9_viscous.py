"""HKBU SCIE1007 coursework science video. Style scout e9: viscous fluid, drip and coil.

The real CDK20 surface hangs in mid air, sagging under its own weight as thick honey. Ropes run off its underside and
coil into stacks on the floor. Real surface plus hand-placed drip paths, all fused by a voxel remesh, no fluid solver.
"""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/e/code")
from blcommon import *  # noqa
from common import load_surface, rot, smooth_field, vertex_normals

sc = reset(1280, 720, samples=128, bounces=14)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.095 @ rot(-74, 6, 200).T
v = smooth_field(v, q, it=10)
nrm = vertex_normals(v, q)
# gravity: undersides sag, a soft low-frequency pull so the real lobes hang like drops
v[:, 2] -= 0.62 * np.clip(-nrm[:, 2], 0, 1) ** 2
ZC = 5.0
v[:, 2] += ZC
rng = np.random.default_rng(6)
vs, fs = [], []
nvert = [0]


def push(vv, ff):
    vs.append(vv.astype(np.float32))
    fs.append(ff + nvert[0])
    nvert[0] += len(vv)


q_t = np.concatenate([q[:, [0, 1, 2]], q[:, [0, 2, 3]]])
push(v, q_t)


def tube(path, rad, sides=10):
    path = np.asarray(path, np.float32)
    rad = np.asarray(rad, np.float32)
    n = len(path)
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
    a = np.cross(t, [0.31, 0.77, 0.55]); a /= np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-6)
    b = np.cross(t, a)
    th = np.linspace(0, 6.28318, sides, endpoint=False)
    ring = (a[:, None, :] * np.cos(th)[None, :, None] + b[:, None, :] * np.sin(th)[None, :, None]) * rad[:, None, None]
    vv = (path[:, None, :] + ring).reshape(-1, 3)
    vv = np.concatenate([vv, path[[0]], path[[-1]]])
    f = []
    for i in range(n - 1):
        for k in range(sides):
            a0, b0 = i * sides + k, i * sides + (k + 1) % sides
            a1, b1 = a0 + sides, b0 + sides
            f += [[a0, a1, b1], [a0, b1, b0]]
    s0, s1 = len(vv) - 2, len(vv) - 1
    for k in range(sides):
        f += [[s0, k, (k + 1) % sides], [s1, (n - 1) * sides + (k + 1) % sides, (n - 1) * sides + k]]
    push(vv, np.array(f, np.int64))


def coil(x, y, z0, r0=0.42, r1=0.12, turns=7, tr=0.12, h=0.11):
    """A rope folding on itself as it lands: a slightly precessing helix."""
    t = np.linspace(0, 1, int(turns * 26))
    ang = t * turns * 6.283
    rr = r0 * (1 - t) + r1 * t + 0.05 * np.sin(ang * 0.37)
    px = x + rr * np.cos(ang) + 0.09 * np.sin(ang * 0.21)
    py = y + rr * np.sin(ang) + 0.09 * np.cos(ang * 0.17)
    pz = z0 + t * turns * h
    tube(np.c_[px, py, pz], np.full(len(t), tr), sides=9)
    return px[-1], py[-1], pz[-1]


# Drips: underside points spread apart, so the ropes fall where the real lobes hang lowest
under = np.nonzero(nrm[:, 2] < -0.55)[0]
picks = []
order = rng.permutation(under)
for i in order:
    p = v[i]
    if all(np.linalg.norm(p - v[j]) > 0.85 for j in picks):
        picks.append(i)
    if len(picks) >= 26:
        break
picks = sorted(picks, key=lambda i: v[i, 2])
for n, i in enumerate(picks):
    p = v[i]
    if n < 7:        # long ropes reach the floor
        fx, fy = p[0] + rng.normal(0, 0.1), p[1] + rng.normal(0, 0.1)
        top = coil(fx, fy, 0.08, r0=rng.uniform(0.34, 0.55), turns=int(rng.integers(5, 9)), tr=rng.uniform(0.09, 0.13))
        nt_ = 44
        s = np.linspace(0, 1, nt_)
        path = np.c_[p[0] + (top[0] - p[0]) * s ** 3, p[1] + (top[1] - p[1]) * s ** 3, p[2] + 0.2 + (top[2] - p[2] - 0.2) * s]
        rad = 0.05 + 0.22 * (1 - s) ** 6 + 0.04 * s ** 8
        tube(path, rad)
        # puddle spreading under the stack
        th = np.linspace(0, 6.283, 40, endpoint=False)
        for rr, zz in ((0.95, 0.0), (0.85, 0.05), (0.5, 0.075)):
            pass
        bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=16, radius=1)
        o = bpy.context.object
        nv = len(o.data.vertices)
        arr = np.zeros(nv * 3, np.float32); o.data.vertices.foreach_get("co", arr); arr = arr.reshape(-1, 3)
        t_ = np.zeros(len(o.data.loop_triangles) * 3, np.int32) if False else None
        o.data.calc_loop_triangles()
        lt = np.zeros(len(o.data.loop_triangles) * 3, np.int32)
        o.data.loop_triangles.foreach_get("vertices", lt)
        bpy.data.objects.remove(o)
        pu = arr * np.array([rng.uniform(0.9, 1.5), rng.uniform(0.8, 1.2), 0.1]) + np.array([fx, fy, 0.03])
        push(pu, lt.reshape(-1, 3).astype(np.int64))
    else:            # short drips with a bead hanging
        L = rng.uniform(0.5, 2.1)
        s = np.linspace(0, 1, 26)
        path = np.c_[np.full(26, p[0]), np.full(26, p[1]), p[2] + 0.18 - L * s]
        bead = 0.15 * np.exp(-((s - 0.93) / 0.075) ** 2)
        rad = 0.05 + 0.25 * (1 - s) ** 5 + bead
        tube(path, rad)

# The pour feeding it from above, folding on the top lobe
top_i = np.argmax(v[:, 2])
tp = v[top_i]
end = coil(tp[0], tp[1], tp[2] - 0.1, r0=0.55, r1=0.1, turns=5, tr=0.15, h=0.14)
s = np.linspace(0, 1, 30)
tube(np.c_[np.full(30, end[0]), np.full(30, end[1]), end[2] + (16 - end[2]) * s], 0.075 + 0.07 * (1 - s) ** 8)

me = None
V = np.concatenate(vs)
F = np.concatenate(fs).astype(np.int32)
print("pre", len(V), len(F))
ob = add_mesh("fluid", V, F, tris=True)
remesh_smooth(ob, voxel=0.034, smooth=14, factor=0.6)
print("post", len(ob.data.vertices))
ob.data.polygons.foreach_set("use_smooth", np.ones(len(ob.data.polygons), bool))
ob.data.update()

# Title: poured letters that have slumped and pooled at the foot
T = text3d("CDK20", "ariblk.ttf", size=1.85, extrude=0.24, bevel=0.07, bevel_res=2, space=1.16)
T.rotation_euler = (np.radians(90), 0, 0)
T.location = (-0.1, -4.2, 0.74)
apply_mods(T)
tv = np.zeros(len(T.data.vertices) * 3, np.float32)
T.data.vertices.foreach_get("co", tv)
tv = tv.reshape(-1, 3)
m_w = np.array(T.matrix_world)[:3]
tv = tv @ m_w[:3, :3].T + m_w[:3, 3]
T.data.vertices.foreach_set("co", tv.ravel())
T.rotation_euler = (0, 0, 0); T.location = (0, 0, 0)
T.data.update()
remesh_smooth(T, voxel=0.03, smooth=10, factor=0.6)
# slump: lower part spreads
tv = np.zeros(len(T.data.vertices) * 3, np.float32)
T.data.vertices.foreach_get("co", tv)
tv = tv.reshape(-1, 3)
base = np.clip(1 - tv[:, 2] / 0.5, 0, 1) ** 2
tv[:, 1] -= base * 0.25
T.data.vertices.foreach_set("co", tv.ravel())
T.data.polygons.foreach_set("use_smooth", np.ones(len(T.data.polygons), bool))
T.data.update()

M = bpy.data.materials.new("honey")
M.use_nodes = True
nt = M.node_tree
P = nt.nodes["Principled BSDF"]
P.inputs["Base Color"].default_value = (1, 0.93, 0.8, 1)
P.inputs["Transmission Weight"].default_value = 1.0
P.inputs["Roughness"].default_value = 0.03
P.inputs["IOR"].default_value = 1.49
ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
ab.inputs["Color"].default_value = (0.98, 0.42, 0.03, 1)
ab.inputs["Density"].default_value = 0.9
nt.links.new(ab.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
ob.data.materials.append(M)
T.data.materials.append(M)

# Set: seamless cobalt sweep, the complement of amber
sv, sq = [], []
for i in range(61):
    a = i / 60
    y = -24 + a * 40
    z = 0 if y < 7 else ((y - 7) ** 2) * 0.35
    sv += [[-40, y, z], [40, y, z]]
for i in range(60):
    sq.append([i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2])
card = add_mesh("card", np.array(sv, np.float32), np.array(sq))
cm, cp = principled("card", (0.015, 0.05, 0.42), 0.32)
card.data.materials.append(cm)

area((0, 7, 12), (0, 0, 4), 2800, 12, (1.0, 0.95, 0.85))          # big back top: amber glows through the fluid
area((-11, -7, 7), (0, 0, 4), 900, 3, (1.0, 0.98, 0.95))
a = area((10, -5, 4), (0, 0, 4), 600, 1, (0.8, 0.9, 1.0)); a.data.shape = "RECTANGLE"; a.data.size = 0.6; a.data.size_y = 10
world_rgb((0.55, 0.62, 0.8), 0.45)
camera((1.2, -18.5, 3.6), (0.2, 0, 3.55), lens=38)
print(render(sc, "e9_viscous"))
