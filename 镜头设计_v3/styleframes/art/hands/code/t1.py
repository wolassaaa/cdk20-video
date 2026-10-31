"""HKBU SCIE1007 coursework science video. Hands T1: the real liver outline (BodyParts3D) filled with exactly 1,412 hands, one for each death in the on-screen figure.
How they are counted: the script places 1,412 points, stamps one hand at each and writes its number into an id buffer, pixel by pixel. It then counts the numbers left in the buffer and measures how much of each hand can still be seen. The run stops with an error unless the count is 1,412 and every hand keeps at least MIN_VIS of its own area. The result goes to code/_raw/t1_count.txt."""
import struct

from hk import *

N = 1412
MIN_VIS = 0.30
STL = ROOT / "assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
b = open(STL, "rb").read()
n = struct.unpack("<I", b[80:84])[0]
tri = np.frombuffer(b, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), count=n, offset=84)["v"].reshape(-1, 3, 3)
# anterior view: viewer left is the body right, BodyParts3D x already runs that way
px = tri[..., 0]
py = -tri[..., 2]
sc = 0.95 * min(W / (px.max() - px.min()), H / (py.max() - py.min()))
ox = W * 0.46 - sc * (px.max() + px.min()) / 2
oy = H * 0.5 - sc * (py.max() + py.min()) / 2
SS = 2
im = Image.new("L", (W * SS, H * SS), 0)
d = ImageDraw.Draw(im)
qx, qy = (px * sc + ox) * SS, (py * sc + oy) * SS
for i in range(0, n):
    d.polygon([(qx[i, 0], qy[i, 0]), (qx[i, 1], qy[i, 1]), (qx[i, 2], qy[i, 2])], fill=255)
mask = np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255
mask = gblur(mask, 2) > 0.5
print("liver area px", int(mask.sum()))

# k-means on the mask gives exactly N evenly spaced points
rng = np.random.default_rng(1412)
ys, xs = np.where(mask)
idx = rng.choice(len(xs), 70000, replace=False)
P = np.c_[xs[idx], ys[idx]].astype(np.float32)
C = P[rng.choice(len(P), N, replace=False)].copy()
for it in range(24):
    lab = np.zeros(len(P), np.int32)
    for i in range(0, len(P), 4000):
        lab[i:i + 4000] = ((P[i:i + 4000, None] - C[None]) ** 2).sum(-1).argmin(1)
    sx = np.bincount(lab, P[:, 0], N)
    sy = np.bincount(lab, P[:, 1], N)
    ct = np.bincount(lab, minlength=N)
    ok = ct > 0
    C[ok, 0], C[ok, 1] = sx[ok] / ct[ok], sy[ok] / ct[ok]
assert len(C) == N
cell = math.sqrt(mask.sum() / N)
size = 36
print("cell", cell, "hand box", size)

base = [print_sil(s, 300) for s in range(6)]
flow = vnoise(W, H, 500, 9, 2)
tones = [SKIN[int(rng.integers(len(SKIN)))] * rng.uniform(0.86, 1.08) for _ in range(N)]


def lay(order):
    """Hands placed earlier keep their pixels, so a later hand only takes what is free. Each tries a few angles and small shifts and keeps the one that hides least of itself."""
    ids = np.zeros((H, W), np.int32)
    own = np.zeros(N + 1, np.int64)
    pm = np.zeros((H, W), np.float32)
    col = np.zeros((H, W, 3), np.float32)
    for i in order:
        x, y = C[i]
        best = None
        a0 = float(flow[int(y), int(x)]) * 540
        for k in range(24):
            ang = a0 + rng.normal(0, 80)
            jx, jy = rng.normal(0, 3.0, 2)
            a = rot_sprite(base[(i + k) % 6], ang, size)
            h, w = a.shape
            x0, y0 = int(x + jx - w / 2), int(y + jy - h / 2)
            cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
            sub = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
            on = sub > 0.5
            r = ids[cy0:cy1, cx0:cx1]
            cover = int((on & (r != 0)).sum()) / max(int(on.sum()), 1)
            if best is None or cover < best[0]:
                best = (cover, sub, on, (cy0, cy1, cx0, cx1))
                if cover == 0:
                    break
        _, sub, on, (cy0, cy1, cx0, cx1) = best
        own[i + 1] = int(on.sum())
        r = ids[cy0:cy1, cx0:cx1]
        r[on & (r == 0)] = i + 1
        sub2 = sub * (r == i + 1)
        col[cy0:cy1, cx0:cx1] = col[cy0:cy1, cx0:cx1] * (1 - sub2[..., None]) + tones[i] * sub2[..., None]
        pm[cy0:cy1, cx0:cx1] = np.maximum(pm[cy0:cy1, cx0:cx1], sub2)
    vis = np.bincount(ids.ravel(), minlength=N + 1)[1:]
    return ids, own, pm, col, vis / own[1:]


order = np.arange(N)
for rnd in range(6):
    ids, own, pm, col, ratio = lay(order)
    print("round", rnd, "min", round(float(ratio.min()), 3), "under", int((ratio < MIN_VIS).sum()), flush=True)
    if ratio.min() >= MIN_VIS:
        break
    order = np.argsort(ratio)      # the most hidden go first next round

vis = np.bincount(ids.ravel(), minlength=N + 1)[1:]
ratio = vis / own[1:]
count = int((vis > 0).sum())
report = f"placed {N}\nids found in the buffer {count}\nvisible share of each hand: min {ratio.min():.3f}, median {np.median(ratio):.3f}\nhands under {MIN_VIS:.0%} visible: {int((ratio < MIN_VIS).sum())}\nhand box {size} px at 1080p\n"
print(report)
(RAW / "t1_count.txt").write_text(report, encoding="utf8")
assert count == N, count
assert ratio.min() >= MIN_VIS, ratio.min()
np.savez_compressed(RAW / "t1_ids.npz", ids=ids.astype(np.int16), mask=mask)

tf = font(SERIF, 74)
t1 = layer(sprite_text("1,412 deaths in", tf), 1330, 842)
t2 = layer(sprite_text("Hong Kong, 2022", tf), 1330, 928)
txt = np.maximum(t1, t2)
relief = press(pm, 0.55, 1.0) + press(txt, 0.16, 1.1) + press(gblur(mask.astype(np.float32), 18), 0.45, 8)
rgb, _ = ash(relief, tone=0.27, seed=11, light=1.0)
floor = col * (0.72 + 0.28 * np.clip(rgb.mean(-1, keepdims=True) / 0.3, 0, 1.6))
rgb = comp(rgb, pm * 0.97, floor * 1.12)
rgb = comp(rgb, gblur(txt, 0.5), np.array([0.92, 0.92, 0.92], np.float32))
rgb = vignette(rgb, 0.5)
save(rgb, "T1.png")
