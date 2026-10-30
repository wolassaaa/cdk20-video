"""PULSE: place exactly 1,412 light points in the BodyParts3D liver volume (blue-noise spacing).

Installation scale: liver x K (=30), so the real ~21 cm liver becomes a ~6.3 m cloud hung in a hall.
Coordinates: metres, BodyParts3D axes (anterior = -y, patient right = -x), liver centred in x/y, lowest point at z = Z0.

blender -b --factory-startup -t 3 -P points.py -- --out ../data/points.npz
Writes: positions (1412,3), surf (distance to skin, m), plus the remeshed skin (verts, tris) for checks.
Blue noise = farthest-point sampling over a dense candidate pool (surface + interior), which gives
an exact count with a near-uniform minimum spacing (Poisson-disk-like).
"""
import bpy, bmesh, sys, argparse, time
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=1412)
ap.add_argument("--K", type=float, default=30.0)
ap.add_argument("--z0", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=1412)
A = ap.parse_args(argv)

LIVER = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=LIVER)
o = bpy.context.selected_objects[0]
me = o.data
co = np.array([v.co[:] for v in me.vertices]) * 0.001 * A.K   # mm -> m, x K
mn, mx = co.min(0), co.max(0)
SHIFT = np.array([-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, A.z0 - mn[2]])
for v, c in zip(me.vertices, co + SHIFT): v.co = c
print("liver bbox (m):", (mx - mn).round(3), "shift", SHIFT.round(3))

# clean closed skin: voxel remesh (2 mm in liver scale) + light smoothing
me.remesh_voxel_size = 0.002 * A.K
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.voxel_remesh()
lap = o.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = 4; lap.lambda_factor = 0.7
bpy.ops.object.modifier_apply(modifier="lap")
me = o.data
me.calc_loop_triangles()
V = np.array([v.co[:] for v in me.vertices])
T = np.array([t.vertices[:] for t in me.loop_triangles])
bvh = BVHTree.FromPolygons([Vector(v) for v in V], [tuple(t) for t in T])
print("skin: %d verts %d tris (%.1fs)" % (len(V), len(T), time.time() - t0))

rng = np.random.default_rng(A.seed)
# --- surface pool: area-weighted samples on the skin, pulled 4 cm inside so a bulb sits just under the skin
a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
k = rng.choice(len(T), 30000, p=area / area.sum())
r1, r2 = rng.random(30000), rng.random(30000)
s = np.sqrt(r1)
P_s = a[k] * (1 - s)[:, None] + b[k] * (s * (1 - r2))[:, None] + c[k] * (s * r2)[:, None]
nrm = np.cross(b - a, c - a)[k]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
P_s = P_s - nrm * 0.04

# --- interior pool: uniform in the bbox, keep points inside the skin (nearest-face normal test)
lo, hi = V.min(0), V.max(0)
cand = lo + (hi - lo) * rng.random((160000, 3))
inside = np.zeros(len(cand), bool)
dist = np.zeros(len(cand))


def parity(p, dv):
    """odd number of skin crossings along a ray = inside (robust, unlike the nearest-face normal test)."""
    o = Vector(p); n = 0
    for _ in range(40):
        hit = bvh.ray_cast(o, dv, 40.0)
        if hit[0] is None: break
        n += 1; o = hit[0] + dv * 1e-4
    return n % 2 == 1


DX, DZ = Vector((1, 0, 0)), Vector((0.0, 0.0, 1.0))
for i, p in enumerate(cand):
    if parity(p, DZ) and parity(p, DX):
        inside[i] = True
        dist[i] = bvh.find_nearest(Vector(p))[3]
P_v = cand[inside & (dist > 0.04)]
print("pool: surface %d interior %d (%.1fs)" % (len(P_s), len(P_v), time.time() - t0))

# --- farthest-point sampling -> exactly N points
pool = np.concatenate([P_s, P_v])
N = A.n
sel = np.empty(N, int)
sel[0] = int(np.argmin(pool[:, 2]))           # start at the lowest point
dmin = np.linalg.norm(pool - pool[sel[0]], axis=1)
for i in range(1, N):
    j = int(np.argmax(dmin)); sel[i] = j
    dmin = np.minimum(dmin, np.linalg.norm(pool - pool[j], axis=1))
P = pool[sel]
assert len(P) == N == len(np.unique(sel))

# spacing stats
D = np.linalg.norm(P[:, None] - P[None], axis=2); np.fill_diagonal(D, 1e9)
nn = D.min(1)
print("N=%d  nearest-neighbour spacing: min %.3f  mean %.3f  max %.3f m" % (N, nn.min(), nn.mean(), nn.max()))
# distance to skin for each point
surf = np.array([bvh.find_nearest(Vector(p))[3] for p in P])
print("on-skin (<6 cm): %d   interior: %d" % ((surf < 0.06).sum(), (surf >= 0.06).sum()))
np.savez(A.out, P=P, surf=surf, nn=nn, V=V, T=T, shift=SHIFT, K=A.K)
print("saved", A.out, "%.1fs" % (time.time() - t0))
