"""Grow a vessel tree inside the REAL liver shape (BodyParts3D FMA7197) for the TouchDesigner flow shot.

The liver outline is real anatomy; the branching inside is generated (space colonisation toward points filling the
liver volume) and must be labelled as a schematic. Outputs, in a TD-friendly normalised frame (liver ~100 units wide):
  paths.npy   (P, S, 4) float32  - P root-to-leaf paths, S samples each: xyz + vessel radius
  surface.npy (N, 4)    float32  - points on the liver surface (xyz + 1) for the faint real silhouette
usage: python grow_tree.py <liver.stl> <out_dir> [n_paths] [samples]
"""
import sys, os
import numpy as np
import trimesh
from scipy.spatial import cKDTree

STL, OUT = sys.argv[1], sys.argv[2]
P = int(sys.argv[3]) if len(sys.argv) > 3 else 256
S = int(sys.argv[4]) if len(sys.argv) > 4 else 128
rng = np.random.default_rng(11)
os.makedirs(OUT, exist_ok=True)

with open(STL, "rb") as f:
    liver = trimesh.load(f, file_type="stl")
centre = liver.bounds.mean(axis=0)
scale = 100.0 / (liver.bounds[1] - liver.bounds[0]).max()
to_td = lambda p: (p - centre) * scale
# BodyParts3D: x = patient left/right, y = front/back, z = up. TD: x right, y up, z toward camera (anterior view: the patient's right lobe on screen left)
axes = lambda p: np.stack([p[:, 0], p[:, 2], -p[:, 1]], axis=1)

# attractors: points filling the liver volume
vox = liver.voxelized(pitch=3.0).fill()
inside = vox.points
attr = axes(to_td(inside[rng.choice(len(inside), min(4000, len(inside)), replace=False)]))
surf = axes(to_td(liver.sample(40000)))

# root: the hilum, approximated as the inferior-medial edge of the liver; the trunk enters from below
lo = attr[:, 1].min()
hil = attr[(attr[:, 1] < lo + 25)]
root = hil[np.argmin(np.abs(hil[:, 0] - np.median(hil[:, 0])))].copy()
root[1] -= 6
trunk = [root + np.array([0, -40 + 4 * k, 0]) for k in range(10)]

# space colonisation
nodes = [n.copy() for n in trunk]
parent = [-1] + list(range(len(trunk) - 1))
STEP, INFLUENCE, KILL = 2.2, 14.0, 3.5
alive = np.ones(len(attr), bool)
for it in range(400):
    tree = cKDTree(np.array(nodes))
    d, idx = tree.query(attr, distance_upper_bound=INFLUENCE)
    grow = {}
    for a in np.where(alive & np.isfinite(d))[0]:
        grow.setdefault(idx[a], []).append(attr[a])
    if not grow:
        break
    for n, targets in grow.items():
        v = (np.array(targets) - nodes[n])
        v = (v / np.linalg.norm(v, axis=1, keepdims=True)).mean(axis=0)
        v += rng.normal(0, 0.12, 3)
        nodes.append(nodes[n] + STEP * v / (np.linalg.norm(v) + 1e-9))
        parent.append(n)
    tree = cKDTree(np.array(nodes))
    alive &= tree.query(attr)[0] > KILL
    if alive.sum() < 40:
        break
nodes = np.array(nodes)
parent = np.array(parent)
print(f"nodes {len(nodes)} after {it + 1} iterations, attractors left {alive.sum()}")

# pipe model radii: leaves thin, r^2 of a parent = sum of children's r^2
children = [[] for _ in nodes]
for i, p in enumerate(parent):
    if p >= 0:
        children[p].append(i)
r = np.zeros(len(nodes))
for i in range(len(nodes) - 1, -1, -1):
    r[i] = 0.35 if not children[i] else np.sqrt(sum(r[c] ** 2 for c in children[i]))
r = r / r.max() * 4.5

# root-to-leaf paths, resampled to S points each; pick P leaves spread across the liver
leaves = np.array([i for i in range(len(nodes)) if not children[i]])
pick = leaves[rng.choice(len(leaves), min(P, len(leaves)), replace=False)]
out = np.zeros((P, S, 4), np.float32)
for k in range(P):
    leaf = pick[k % len(pick)]
    chain = [leaf]
    while parent[chain[-1]] >= 0:
        chain.append(parent[chain[-1]])
    chain = chain[::-1]
    pts, rad = nodes[chain], r[chain]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, seg[-1], S)
    for c in range(3):
        out[k, :, c] = np.interp(t, seg, pts[:, c])
    out[k, :, 3] = np.interp(t, seg, rad)
np.save(os.path.join(OUT, "paths.npy"), out)
np.save(os.path.join(OUT, "surface.npy"), np.c_[surf, np.ones(len(surf))].astype(np.float32))
print("paths", out.shape, "x", out[..., 0].min().round(1), out[..., 0].max().round(1), "y", out[..., 1].min().round(1), out[..., 1].max().round(1),
      "leaves", len(leaves))
