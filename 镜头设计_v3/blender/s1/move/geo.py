"""Mesh analysis helpers (run inside Blender's python: numpy + mathutils only).

geodesic(): Dijkstra over mesh edges + proximity "bridge" edges between the
separate BodyParts3D element shells, so the dye front can run from the bottom of
the SMV, through the portal trunk, into every intrahepatic branch.
"""
import heapq
import numpy as np
from mathutils import kdtree


def islands(nv, edges):
    parent = np.arange(nv)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    lab = np.array([find(i) for i in range(nv)])
    _, lab = np.unique(lab, return_inverse=True)
    return lab


def bridge_edges(co, lab, link_r=2.5):
    """Connect shells: (1) every vertex to verts of other shells within link_r,
    (2) a minimum spanning tree over shells using their closest vertex pair so
    the whole tree is guaranteed connected."""
    n = len(co)
    kd = kdtree.KDTree(n)
    for i, p in enumerate(co):
        kd.insert(p, i)
    kd.balance()
    extra = []
    for i, p in enumerate(co):
        for (_, j, dist) in kd.find_range(p, link_r):
            if lab[j] != lab[i] and j > i:
                extra.append((i, j, dist))
    # shell MST on closest pairs
    nl = lab.max() + 1
    best = {}
    trees = []
    for k in range(nl):
        idx = np.where(lab == k)[0]
        t = kdtree.KDTree(len(idx))
        for m, i in enumerate(idx):
            t.insert(co[i], m)
        t.balance()
        trees.append((idx, t))
    for a in range(nl):
        ia, _ = trees[a]
        for b in range(nl):
            if b <= a:
                continue
            ib, tb = trees[b]
            bd = (1e9, -1, -1)
            for i in ia[:: max(1, len(ia) // 400)]:
                _, m, dist = tb.find(co[i])
                if dist < bd[0]:
                    bd = (dist, i, ib[m])
            best[(a, b)] = bd
    # Prim
    inT = {0}
    while len(inT) < nl:
        cand = None
        for (a, b), (dist, i, j) in best.items():
            if (a in inT) != (b in inT):
                if cand is None or dist < cand[0]:
                    cand = (dist, i, j, a, b)
        dist, i, j, a, b = cand
        extra.append((i, j, dist))
        inT.add(a); inT.add(b)
    return extra


def geodesic(co, edges, extra, seed):
    n = len(co)
    adj = [[] for _ in range(n)]
    for a, b in edges:
        w = float(np.linalg.norm(co[a] - co[b]))
        adj[a].append((b, w)); adj[b].append((a, w))
    for a, b, w in extra:
        adj[a].append((b, float(w))); adj[b].append((a, float(w)))
    dist = np.full(n, np.inf)
    pred = np.full(n, -1)
    dist[seed] = 0.0
    h = [(0.0, seed)]
    while h:
        d, u = heapq.heappop(h)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd; pred[v] = u
                heapq.heappush(h, (nd, v))
    return dist, pred
