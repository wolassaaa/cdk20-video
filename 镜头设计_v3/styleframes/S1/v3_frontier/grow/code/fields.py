"""GROW / fields: per-pixel maps derived from the grown tree, plus the four territories that will starve.

Jump flooding gives each crop pixel its nearest tree node; from that come
  Lmap  path length from the root to here (pulse phase for the capillary bed)
  hmap  height of the nearest node (how far the tissue here is from the branch tip -> retraction order)
Territories: a subtree whose area is near the target and whose centroid is near the target point.
Writes work/fields.npz and work/regions.png (check picture).
"""
import numpy as np, os, sys, time
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
X0, Y0, CW, CH = 280, 0, 1100, 1080

d = np.load(os.path.join(WORK, "liver_proj.npz")); t = np.load(os.path.join(WORK, "tree.npz"))
P = t["P"] - np.array([X0, Y0], np.float32)
par, L, height, seg = t["parent"], t["L"], t["height"], t["seg"]
n = len(P)
mask = d["mask"][Y0:Y0 + CH, X0:X0 + CW]
inside = mask > 0.5

# ---- jump flooding
t0 = time.time()
seed = np.full((CH, CW), -1, np.int32)
xi, yi = np.clip(P[:, 0].astype(int), 0, CW - 1), np.clip(P[:, 1].astype(int), 0, CH - 1)
seed[yi, xi] = np.arange(n)
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
best = np.full((CH, CW), 1e12, np.float32)
has = seed >= 0
best[has] = (xx[has] - P[seed[has], 0]) ** 2 + (yy[has] - P[seed[has], 1]) ** 2
k = 512
while k >= 1:
    for dy in (-k, 0, k):
        for dx in (-k, 0, k):
            if dx == 0 and dy == 0:
                continue
            sy0, sy1 = max(0, dy), CH + min(0, dy)
            sx0, sx1 = max(0, dx), CW + min(0, dx)
            src = seed[sy0:sy1, sx0:sx1]
            ty0, ty1 = max(0, -dy), CH + min(0, -dy)
            tx0, tx1 = max(0, -dx), CW + min(0, -dx)
            v = src >= 0
            dd = (xx[ty0:ty1, tx0:tx1] - P[np.maximum(src, 0), 0]) ** 2 + (yy[ty0:ty1, tx0:tx1] - P[np.maximum(src, 0), 1]) ** 2
            upd = v & (dd < best[ty0:ty1, tx0:tx1])
            best[ty0:ty1, tx0:tx1][upd] = dd[upd]
            seed[ty0:ty1, tx0:tx1][upd] = src[upd]
    k //= 2
dist = np.sqrt(best)
print(f"JFA {time.time() - t0:.1f}s, max dist {dist[inside].max():.1f}")

Lmap = L[seed] + dist
hmap = height[seed] + 0.0

# ---- subtree area / centroid
area = np.bincount(seed[inside], minlength=n).astype(np.float64)
sx = np.bincount(seed[inside], weights=xx[inside], minlength=n)
sy = np.bincount(seed[inside], weights=yy[inside], minlength=n)
A, X, Y = area.copy(), sx.copy(), sy.copy()
for i in range(n - 1, 0, -1):
    p = par[i]
    A[p] += A[i]; X[p] += X[i]; Y[p] += Y[i]
tot = area.sum()
cx, cy = X / np.maximum(A, 1), Y / np.maximum(A, 1)
print("liver px", tot)

# targets in full-frame px: (x, y, area fraction)
targets = [(1215, 262, 0.075),   # left lobe, towards the tip
           (445, 700, 0.08),     # right lobe, inferior tip
           (560, 170, 0.085),    # right lobe, superior
           (970, 470, 0.06)]     # left lobe, inferior edge
regions = []
taken = np.zeros(n, bool)
level = t["level"]
for (tx, ty, frac) in targets:
    tx -= X0; ty -= Y0
    ok = (A > tot * frac * 0.7) & (A < tot * frac * 1.4) & (level >= 1) & ~taken
    score = np.hypot(cx - tx, cy - ty) + 600 * np.abs(A / tot - frac)
    score[~ok] = 1e9
    b = int(np.argmin(score))
    # subtree membership
    sub = np.zeros(n, bool); sub[b] = True
    for i in range(b + 1, n):
        sub[i] = sub[par[i]]
    taken |= sub
    # also forbid ancestors (a later pick must not contain an earlier one)
    a = b
    while a >= 0:
        taken[a] = True; a = par[a]
    regions.append((b, sub))
    print(f"region base {b} lvl {level[b]} L {L[b]:.0f} height {height[b]:.0f} area {A[b] / tot:.3f} "
          f"centroid {cx[b] + X0:.0f},{cy[b] + Y0:.0f} nodes {sub.sum()}")

reg_of = np.full(n, -1, np.int8)
for k, (b, sub) in enumerate(regions):
    reg_of[sub] = k
terr = reg_of[seed]
terr[~inside] = -1
np.savez_compressed(os.path.join(WORK, "fields.npz"), seed=seed, dist=dist.astype(np.float32), Lmap=Lmap.astype(np.float32),
                    hmap=hmap.astype(np.float32), terr=terr, reg_of=reg_of, bases=np.array([r[0] for r in regions]),
                    crop=np.array([X0, Y0, CW, CH]))

pal = np.array([[60, 60, 60], [231, 25, 15], [31, 59, 255], [237, 235, 228], [0, 160, 90]], np.uint8)
img = pal[terr + 1].copy()
img[~inside] = 0
for i in range(1, n):
    img[yi[i], xi[i]] = (255, 255, 255) if t["level"][i] == 1 else img[yi[i], xi[i]]
Image.fromarray(img).save(os.path.join(WORK, "regions.png"))
