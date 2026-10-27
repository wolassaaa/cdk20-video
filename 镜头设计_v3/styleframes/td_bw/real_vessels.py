"""Centrelines of the REAL liver vessels (BodyParts3D v4, CC BY 4.0) as flow paths for TouchDesigner.

Each vessel group is voxelised, skeletonised to a 1-voxel centreline, turned into a graph, and walked from its root
(where blood enters or leaves the liver) to every branch tip. Radii come from the distance transform.
Output (same TD frame as grow_tree.py: liver ~100 units wide, x right, y up, z toward the viewer):
  real_paths.npy   (P, S, 4) xyz + radius, rows grouped by vessel: see real_paths.json for row ranges
  real_surface.npy (200, 200, 4) points on the v4 liver surface (the silhouette)
usage: python real_vessels.py <groups_stl_dir> <out_dir> [samples]
"""
import sys, os, json
import numpy as np
import trimesh
import networkx as nx
from scipy import ndimage
from skimage.morphology import skeletonize

SRC, OUT = sys.argv[1], sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 128
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(5)


def load(name):
    with open(os.path.join(SRC, name + ".stl"), "rb") as f:
        return trimesh.load(f, file_type="stl")


liver = load("liver_parenchyma_segments")
centre = liver.bounds.mean(axis=0)
scale = 100.0 / (liver.bounds[1] - liver.bounds[0]).max()
to_td = lambda p: np.stack([p[:, 0], p[:, 2], -p[:, 1]], axis=1) * 0 + np.stack(
    [(p[:, 0] - centre[0]), (p[:, 2] - centre[2]), -(p[:, 1] - centre[1])], axis=1) * scale

# groups: (file, root rule, max paths). Portal vein and hepatic artery enter from below; hepatic veins drain upward.
GROUPS = [("portal_vein_hepatic", "low", 140), ("hepatic_veins", "high", 80), ("hepatic_artery", "low", 36)]
PITCH = 0.8
rows, meta = [], {}
for name, rule, maxp in GROUPS:
    mesh = load(name)
    vg = mesh.voxelized(pitch=PITCH).fill()
    solid = vg.matrix.astype(bool)
    dist = ndimage.distance_transform_edt(solid) * PITCH
    skel = skeletonize(solid)
    idx = np.argwhere(skel)
    pts = vg.indices_to_points(idx) if hasattr(vg, "indices_to_points") else trimesh.transform_points(idx.astype(float), vg.transform)
    key = {tuple(v): i for i, v in enumerate(idx)}
    G = nx.Graph()
    offs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    for i, v in enumerate(idx):
        for o in offs:
            j = key.get((v[0] + o[0], v[1] + o[1], v[2] + o[2]))
            if j is not None and j > i:
                G.add_edge(i, j, weight=float(np.linalg.norm(o)))
    comp = max(nx.connected_components(G), key=len)
    G = G.subgraph(comp).copy()
    nodes = np.array(sorted(G.nodes))
    z = pts[nodes, 2]
    root = int(nodes[np.argmin(z)] if rule == "low" else nodes[np.argmax(z)])
    lengths, paths = nx.single_source_dijkstra(G, root)
    leaves = [n for n in G.nodes if G.degree(n) == 1 and n != root and lengths[n] > 15]
    leaves.sort(key=lambda n: -lengths[n])
    pick = leaves[:maxp] if len(leaves) <= maxp else [leaves[i] for i in np.linspace(0, len(leaves) - 1, maxp).astype(int)]
    start = len(rows)
    for leaf in pick:
        chain = paths[leaf]
        p = to_td(pts[chain])
        r = dist[tuple(idx[chain].T)] * scale
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        t = np.linspace(0, seg[-1], S)
        row = np.zeros((S, 4), np.float32)
        for c in range(3):
            row[:, c] = np.interp(t, seg, p[:, c])
        row[:, 3] = np.interp(t, seg, ndimage.uniform_filter1d(r, 5))
        rows.append(row)
    meta[name] = {"rows": [start, len(rows)], "skeleton_voxels": int(len(nodes)), "leaves": len(leaves), "root_rule": rule}
    print(f"{name}: skeleton {len(nodes)} voxels, {len(leaves)} tips, kept {len(pick)} paths")

paths = np.stack(rows)
np.save(os.path.join(OUT, "real_paths.npy"), paths)
surf = to_td(liver.sample(40000))
np.save(os.path.join(OUT, "real_surface.npy"), np.c_[surf, np.ones(len(surf))].astype(np.float32).reshape(200, 200, 4))
json.dump({"groups": meta, "shape": list(paths.shape), "source": "BodyParts3D v4 (CC BY 4.0), centrelines by skeletonisation"},
          open(os.path.join(OUT, "real_paths.json"), "w"), indent=1)
print("paths", paths.shape, "x", paths[..., 0].min().round(1), paths[..., 0].max().round(1), "y", paths[..., 1].min().round(1), paths[..., 1].max().round(1))
