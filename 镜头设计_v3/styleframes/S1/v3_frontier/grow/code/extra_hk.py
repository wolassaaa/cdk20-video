"""GROW / extra still: 1-11 "part of it starts right here, in Hong Kong".

The same organism on another silhouette: Hong Kong's land (OSM coastline, (c) OpenStreetMap contributors, ODbL) is the
allowed domain, the Sha Tin -> Pak Shek Kok route is the trunk, space colonisation sprouts from it across the
territory and Physarum agents lay the capillary mesh.  Tero et al. 2010 grew Physarum over a map of the Tokyo region;
this borrows only the idea of a network finding its way across a real geography.
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from physarum import Physarum

ROOT = "D:/。hkbu/molecular science/镜头设计_v3"
FONT = ROOT + "/styleframes/S1/v2/_code/s110/fonts/"
D = json.load(open(ROOT + "/styleframes/S1/v2/_code/s110/hk_land.json", encoding="utf-8"))
OUT = os.path.join(HERE, "..", "still_extra.jpg")
W, H = 1920, 1080
RED = np.array([232, 25, 15], np.float32); BG = np.array([6, 6, 6], np.float32); BONE = np.array([237, 235, 228], np.float32)
BLUE = np.array([31, 59, 255], np.float32)
S = 21.0 / 1000      # px per metre
CX, CY = 800.0, 590.0
rng = np.random.default_rng(5)


def pj(p):
    p = np.asarray(p, np.float64)
    return np.stack([CX + p[..., 0] * S, CY - p[..., 1] * S], -1)


SS = 3
im = Image.new("L", (W * SS, H * SS), 0)
dr = ImageDraw.Draw(im)
for r in D["rings"]:
    q = pj(r["p"]) * SS
    if len(q) > 2 and r["a"] > 2e4:
        dr.polygon([tuple(x) for x in q.tolist()], fill=255)
sz = pj(D["sz"]) * SS
dr.polygon([tuple(x) for x in sz.tolist()], fill=0)     # mainland north of the boundary stays black
dr.rectangle([0, 0, 335 * SS, 372 * SS], fill=0)        # Shekou peninsula (mainland, west of Deep Bay)
dr.rectangle([0, 372 * SS, 60 * SS, H * SS], fill=0)    # mainland islands at the left edge
dr.rectangle([0, 1035 * SS, 120 * SS, H * SS], fill=0)
mask = np.asarray(im, np.float32).reshape(H, SS, W, SS).mean((1, 3)) / 255
inside = mask > 0.5
print("land px", inside.sum())

# ---- trunk along the route, then space colonisation across the land
route = pj(D["route"])
P = [route[0]]
for a, b in zip(route[:-1], route[1:]):
    n = int(np.ceil(np.linalg.norm(b - a) / 4))
    for k in range(1, n + 1):
        P.append(a + (b - a) * k / n)
n0 = len(P)
par = [-1] + list(range(n0 - 1)); lev = [0] * n0; nch = [1] * (n0 - 1) + [0]; born = [0] * n0


def sample(sp, keep):
    gy, gx = np.mgrid[0:H:sp, 0:W:sp]
    ax = (gx + rng.random(gx.shape) * sp).ravel(); ay = (gy + rng.random(gy.shape) * sp).ravel()
    ix, iy = np.clip(ax.astype(int), 0, W - 1), np.clip(ay.astype(int), 0, H - 1)
    k = keep[iy, ix]
    return np.stack([ax[k], ay[k]], 1)


def erode(m, k):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(k)), np.uint8) > 0


def grow(A, Dd, KILL, R_INF, AGE, sprout, maxold, maxnew, level, max_it=320):
    global P, par, lev, nch, born
    n_old = len(P)
    live = np.ones(len(A), bool)
    Pa = np.asarray(P)
    for c in range(0, len(A), 1024):
        dd = ((A[c:c + 1024, None, :] - Pa[None, :, :]) ** 2).sum(-1)
        live[c:c + 1024] &= np.sqrt(dd.min(1)) >= KILL
    it = 0
    while it < max_it:
        it += 1
        Pa = np.asarray(P); bA = np.asarray(born); nA = np.asarray(nch)
        spr = np.zeros(len(Pa), bool); spr[:n_old] = sprout
        activ = np.nonzero(np.where(np.arange(len(Pa)) < n_old, spr & (nA < maxold), (it - bA <= AGE) & (nA < maxnew)))[0]
        li = np.nonzero(live)[0]
        if not len(li) or not len(activ):
            break
        nd = np.full(len(li), 1e18); ni = np.zeros(len(li), np.int64)
        Q = Pa[activ]
        for c in range(0, len(li), 512):
            dd = ((A[li[c:c + 512], None, :] - Q[None, :, :]) ** 2).sum(-1)
            k = dd.argmin(1)
            nd[c:c + 512] = dd[np.arange(len(k)), k]; ni[c:c + 512] = activ[k]
        sel = nd < R_INF ** 2
        if not sel.any():
            break
        act, tgt = li[sel], ni[sel]
        v = A[act] - Pa[tgt]
        v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
        acc = np.zeros((len(Pa), 2)); np.add.at(acc, tgt, v)
        nodes = np.unique(tgt)
        dirs = acc[nodes]
        bad = np.linalg.norm(dirs, axis=1) < 0.3
        dirs[bad] += rng.normal(0, 0.5, (bad.sum(), 2))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-9
        newp = Pa[nodes] + dirs * Dd
        xi, yi = np.clip(newp[:, 0].astype(int), 0, W - 1), np.clip(newp[:, 1].astype(int), 0, H - 1)
        ok = mask[yi, xi] > 0.4
        nodes, newp = nodes[ok], newp[ok]
        if not len(newp):
            continue
        P.extend(list(newp)); par.extend(nodes.tolist()); born.extend([it] * len(newp))
        lev.extend([level] * len(newp)); nch.extend([0] * len(newp))
        for q in nodes:
            nch[q] += 1
        li = np.nonzero(live)[0]
        dd = ((A[li, None, :] - newp[None, :, :]) ** 2).sum(-1)
        live[li[np.sqrt(dd.min(1)) < KILL]] = False
    print(f"level {level}: +{len(P) - n_old} nodes, {it} it, {live.sum()} left")


t0 = time.time()
A1 = sample(62, erode(inside, 25))
sp = np.zeros(len(P), bool); sp[-1] = True; sp[len(P) // 2] = True; sp[0] = True
grow(A1, 5.0, 22, 260, 6, sp, 3, 2, 1)
A2 = sample(24, erode(inside, 11))
sp = (np.asarray(lev) <= 1) & (rng.random(len(P)) < 0.55)
grow(A2, 4.0, 13, 60, 7, sp, 3, 2, 2)
A3 = sample(9, erode(inside, 5))
sp = (np.asarray(lev) >= 1) & (rng.random(len(P)) < 0.2)
grow(A3, 3.0, 6.5, 40, 9, sp, 3, 2, 3)
print("sca", time.time() - t0)
P = np.asarray(P, np.float32); par = np.asarray(par, np.int32); lev = np.asarray(lev, np.int8)
n = len(P)
for _ in range(6):
    acc = np.zeros_like(P); cnt = np.zeros(n, np.float32)
    acc[1:] += P[par[1:]]; cnt[1:] += 1
    np.add.at(acc, par[1:], P[1:]); np.add.at(cnt, par[1:], 1)
    avg = acc / np.maximum(cnt, 1)[:, None]
    ch = np.bincount(par[1:], minlength=n)
    mv = (np.arange(n) >= n0) & (ch > 0)
    P[mv] = 0.5 * P[mv] + 0.5 * avg[mv]
ch = np.bincount(par[1:], minlength=n)
lv = (ch == 0).astype(np.float32)
for i in range(n - 1, 0, -1):
    lv[par[i]] += lv[i]
wid = 0.40 * lv ** (1 / 2.2)
wid[:n0] = np.maximum(wid[:n0], 5.0)
print("nodes", n, "tips", int((ch == 0).sum()))

# ---- physarum mesh on land, fed by the tree + coastline band
food_im = Image.new("F", (W, H), 0.0)
fd = ImageDraw.Draw(food_im)
for i in range(1, n):
    fd.line([tuple(P[par[i]].tolist()), tuple(P[i].tolist())], fill=float(min(1, 0.32 + wid[i] / 3)), width=max(1, int(round(wid[i]))))
food = np.asarray(food_im, np.float32) + (erode(inside, 3) & ~erode(inside, 7)) * 0.9
ph = Physarum(inside, seed=31, SA=45, RA=30, SO=6.0, SS=1.0, DEP=1.0, DECAY=0.30, DIFF=0.35)
ys, xs = np.nonzero(inside)
N = int(inside.sum() * 0.42)
k = rng.integers(0, len(xs), N)
ph.spawn(xs[k] + rng.random(N), ys[k] + rng.random(N))
for i in range(90):
    ph.step(food, 0.6)
    if i == 0:
        disp = ph.T.copy()
    disp = disp * 0.72 + ph.T * 0.28
print("physarum agents", N, time.time() - t0)

# ---- compose
order = np.argsort(lv)
im = Image.new("F", (W * SS, H * SS), 0.0)
dr = ImageDraw.Draw(im)
inten = np.where(lev == 0, 1.2, 0.66 + 0.3 * np.clip(lv / lv.max() * 6, 0, 1)).astype(np.float32)
for i in order:
    if i == 0:
        continue
    a, b = P[par[i]] * SS, P[i] * SS
    w = wid[i] * SS
    if w < 1.2:
        dr.line([tuple(a.tolist()), tuple(b.tolist())], fill=float(inten[i] * max(w, 0.3)), width=1)
    else:
        wa = wid[par[i]] * SS * 0.5; wb = w * 0.5
        dv = b - a; nor = np.array([-dv[1], dv[0]]) / (np.linalg.norm(dv) + 1e-6)
        q = [a + nor * wa, b + nor * wb, b - nor * wb, a - nor * wa]
        dr.polygon([tuple(x.tolist()) for x in q], fill=float(inten[i]))
        dr.ellipse([b[0] - wb, b[1] - wb, b[0] + wb, b[1] + wb], fill=float(inten[i]))
tree = np.asarray(im, np.float32).reshape(H, SS, W, SS).mean((1, 3))
v = (1 - np.exp(-(disp / 3.5) ** 1.5)) * 0.62
m = mask
caps = np.zeros_like(m)
caps[1:-1, 1:-1] = np.maximum(np.abs(m[1:-1, 2:] - m[1:-1, :-2]), np.abs(m[2:, 1:-1] - m[:-2, 1:-1]))
caps = np.clip(caps * 1.1, 0, 1) * 0.55
glow = np.asarray(Image.fromarray((np.clip(tree, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
vv = 1 - (1 - np.clip(tree, 0, 1)) * (1 - v) * (1 - caps) * (1 - glow * 0.3)
rgb = BG + vv[..., None] * (RED - BG)

# ---- labels
tl = Image.new("L", (W, H), 0)
d2 = ImageDraw.Draw(tl)
f = ImageFont.truetype(FONT + "InterTight.ttf", 30); f.set_variation_by_axes([300])
mono = ImageFont.truetype(FONT + "MartianMono.ttf", 13); mono.set_variation_by_axes([300, 100])
a = pj(D["poi"]["pwh"]); b = pj(D["poi"]["hkstp"])
d2.text((b[0] + 22, b[1] - 40), "Pak Shek Kok", font=f, fill=255)
d2.text((a[0] + 24, a[1] + 2), "Sha Tin", font=f, fill=255)
d2.text((70, 1012), "\u00a9 OpenStreetMap contributors", font=mono, fill=120)
L = np.asarray(tl, np.float32) / 255
halo = np.asarray(tl.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
rgb = BG + (rgb - BG) * (1 - 0.8 * np.clip(halo * 1.4, 0, 1))[..., None]    # clear the network behind the labels
rgb = rgb + L[..., None] * (BONE - rgb)
for p in (a, b):
    yy, xx = np.ogrid[0:H, 0:W]
    dd = np.sqrt((xx - p[0]) ** 2 + (yy - p[1]) ** 2)
    c = np.clip(7.5 - dd, 0, 1) - np.clip(5.5 - dd, 0, 1)
    rgb = rgb + c[..., None] * (BONE - rgb)
Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8)).save(OUT, quality=95, subsampling=0)
print("saved", time.time() - t0)
