# Vessel tubes as one mesh with UVs: u = distance downstream (world units), v = angle around / 2pi.
# Each path only adds the part not already covered by an earlier path (trunks are shared), plus a short overlap.
import numpy as np, sys
from scipy.spatial import cKDTree
OUT = sys.argv[1]
P = np.load(r"D:/。hkbu/molecular science/镜头设计_v3/assets/vessel_paths/real_paths.npy")
NP, NS = P.shape[:2]
SEG = 20
V, UV, NRM, F = [], [], [], []
done = set()   # centreline points already covered
for i in range(NP):
    s = np.linspace(0, NS - 1, NS * 3)
    p = np.stack([np.interp(s, np.arange(NS), P[i, :, c]) for c in range(3)], 1)
    r = np.interp(s, np.arange(NS), P[i, :, 3]) * (0.93 + 0.1 * np.sin(s * 0.3 + i) ** 8)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    t = np.gradient(p, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    # skip the part of this path that runs inside a tube already built (shared trunk)
    start = 0
    if done:
        tree = cKDTree(np.array(list(done)))
        d, _ = tree.query(p)
        inside = d < np.maximum(0.6, r * 0.6)
        while start < len(p) and inside[start]: start += 1
    done.update(map(tuple, p[start:]))
    start = max(0, start - 3)
    if len(p) - start < 3: continue
    # parallel-transport frame so the ring does not twist
    u = np.cross(t[start], [0, 1, 0] if abs(t[start][1]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u)
    base = sum(len(x) for x in V)
    for j in range(start, len(p)):
        u = u - np.dot(u, t[j]) * t[j]; u /= np.linalg.norm(u); w = np.cross(t[j], u)
        a = np.linspace(0, 2 * np.pi, SEG + 1)
        n = np.cos(a)[:, None] * u + np.sin(a)[:, None] * w
        V.append(p[j] + n * r[j]); NRM.append(n)
        UV.append(np.c_[np.full(SEG + 1, L[j]), a / (2 * np.pi)])
    rows = len(p) - start
    for j in range(rows - 1):
        for k in range(SEG):
            a0 = base + j * (SEG + 1) + k; b0 = a0 + SEG + 1
            F.append((a0, b0, b0 + 1, a0 + 1))
V, UV, NRM = np.concatenate(V), np.concatenate(UV), np.concatenate(NRM)
with open(f"{OUT}/tubes_td.obj", "w") as f:
    f.write("".join(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in V))
    f.write("".join(f"vt {a:.4f} {b:.5f}\n" for a, b in UV))
    f.write("".join(f"vn {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in NRM))
    f.write("".join("f %d/%d/%d %d/%d/%d %d/%d/%d %d/%d/%d\n" % tuple(x for q in face for x in (q + 1,) * 3) for face in F))
print("verts", len(V), "quads", len(F))
