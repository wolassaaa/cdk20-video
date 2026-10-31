"""HKBU SCIE1007 coursework science video. Style scout b4: dots repeat until the room is gone. No shading anywhere, the real CDK20 form comes only from how dots sit on its surface."""
import numpy as np

from common import *

P = load()
V = view(P, zoom=1.2, at=(860, 346), src=(945, 545), rot=10)
y, x = grid()
m = V["mask"]
RED, WHITE, BLACK = hexc("#e8102a"), hexc("#fff8ec"), hexc("#0a0a0a")

# background: a dot lattice in log-polar space, so the wall falls into an endless tunnel behind the protein
cx, cy = 860, 346
dx, dy = x - cx, y - cy
rr = np.maximum(np.hypot(dx, dy), 1)
ang = np.arctan2(dy, dx) + 0.22 * np.log(rr)
N = 58
u = np.log(rr) * N / (2 * np.pi)
v = (ang / (2 * np.pi) + 0.5) * N
row = np.floor(u)
v = v + 0.5 * (row % 2)
du, dv = u - row - 0.5, v - np.floor(v) - 0.5
bg = sstep(0.285, 0.26, np.hypot(du, dv))

# surface dots: real mesh points thinned on a voxel grid, then each pixel asks for its nearest point in 3D
D = np.load(SURFACE)
vt, cf = D["verts"], D["conf"]
lo, hi = vt.min(0), vt.max(0)
S = 2.35
cell = np.floor((vt - lo) / S).astype(np.int32)
dims = cell.max(0) + 3
key = (cell[:, 0] + 1) + dims[0] * ((cell[:, 1] + 1) + dims[1] * (cell[:, 2] + 1))
rng = np.random.default_rng(4)
order = rng.permutation(len(key))
_, first = np.unique(key[order], return_index=True)
pts = vt[order[first]]
pc = cf[order[first]]
# greedy thinning so neighbouring dots keep a gap
keep = []
occ = {}
for i, p in enumerate(pts):
    c = tuple(np.floor(p / (S * 0.8)).astype(int))
    ok = True
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            for e in (-1, 0, 1):
                for j in occ.get((c[0] + a, c[1] + b, c[2] + e), ()):
                    if np.sum((pts[j] - p) ** 2) < (S * 0.92) ** 2:
                        ok = False
    if ok:
        keep.append(i)
        occ.setdefault(c, []).append(i)
pts, pc = pts[keep], pc[keep]
print("dots on surface", len(pts))
lut = -np.ones(dims.prod(), np.int32)
cc = np.floor((pts - lo) / S).astype(np.int32)
for i, c in enumerate(cc):
    lut[(c[0] + 1) + dims[0] * ((c[1] + 1) + dims[1] * (c[2] + 1))] = i

pp = lo + V["pos"] * (hi - lo)
pc0 = np.floor((pp - lo) / S).astype(np.int32)
best = np.full((H, W), 1e9, np.float32)
idx = np.zeros((H, W), np.int32)
mk = m > 0.02
for a in (-1, 0, 1):
    for b in (-1, 0, 1):
        for e in (-1, 0, 1):
            q = pc0 + np.array([a, b, e])
            k = np.clip(q[..., 0] + 1, 0, dims[0] - 1) + dims[0] * (np.clip(q[..., 1] + 1, 0, dims[1] - 1) + dims[1] * np.clip(q[..., 2] + 1, 0, dims[2] - 1))
            j = lut[k]
            d = np.sum((pp - pts[np.maximum(j, 0)]) ** 2, -1)
            d = np.where(j >= 0, d, 1e9)
            sel = (d < best) & mk
            best[sel] = d[sel]
            idx[sel] = j[sel]
dist = np.sqrt(best)
sz = 0.72 + 0.46 * ((np.sin(pts[:, 0] * 0.37) * np.cos(pts[:, 2] * 0.31) + 1) / 2)  # hand-made size drift
dots = sstep(0.06, -0.06, dist - sz[idx])

# low confidence tail: dots keep their true place but turn black
tail = (pc[idx] < 0.7).astype(np.float32)
surface = np.ones((H, W, 3), np.float32) * WHITE
surface = surface * (1 - dots[..., None]) + dots[..., None] * (RED * (1 - tail[..., None]) + BLACK * tail[..., None])

bgc = RED * (1 - bg[..., None]) + WHITE * bg[..., None]
hard = sstep(0.4, 0.6, m)
rgb = bgc * (1 - hard[..., None]) + surface * hard[..., None]

# creases and occluding edges are hard red line, no shading
ao = blur(V["ao"] * hard, 0.7) / np.maximum(blur(hard, 0.7), 0.05)
crease = sstep(0.27, 0.25, ao) * hard
dp = V["depth"]
gy, gx = np.gradient(dp)
edge = sstep(0.006, 0.012, np.hypot(gx, gy)) * sstep(0.9, 1.0, blur(hard, 1.6))
rgb = over(rgb, RED, np.maximum(crease, edge))

# name built from dots: solid black letters punched with the same pattern
t = np.maximum(text("CDK", "ariblk.ttf", 196, (24, 450), "lm", tracking=-6), text("20", "ariblk.ttf", 196, (24, 606), "lm", tracking=-6))
hole = sstep(6.6, 5.8, np.hypot(((x + 16 * (np.floor(y / 28) % 2)) % 32) - 16, (y % 28) - 14))
rgb = over(rgb, BLACK, t)
rgb = over(rgb, WHITE, t * hole)

lab = text(LABEL, "bahnschrift.ttf", 22, (46, 56), "lm", tracking=1)
plate = sstep(1, 0, np.abs(x - 192) - 172) * sstep(1, 0, np.abs(y - 56) - 24)
rgb = over(rgb, BLACK, plate)
rgb = over(rgb, WHITE, lab)
finish(rgb, "b4_infinity_dots.png")
