"""GROW / sca: hierarchical space-colonisation growth of the portal tree inside the projected liver silhouette.

Runions et al. 2005 (open venation) run at three scales, each level sprouting from the one before:
  L1 trunks       sparse attractors laid mostly along the projected BodyParts3D portal vein, grown from the hilum
  L2 branches     medium attractors over the whole silhouette, sprouting from L1
  L3 twigs        dense attractors, sprouting from L1+L2
Each attractor pulls its nearest *active* node (young enough, not too many children); nodes step D toward the
mean pull; attractors die within KILL of any node.  Deterministic (seed 7).

Writes work/tree.npz: P (n,2) px, parent, level, L (path length from root), leaves, height, seg.
"""
import numpy as np, os, sys, time
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
d = np.load(os.path.join(WORK, "liver_proj.npz"))
mask = d["mask"]
H, W = mask.shape
rng = np.random.default_rng(7)


def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)),
                      np.float32) / 255


def erode(m, k):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(k)), np.uint8) > 0


inside = mask > 0.6
portal = d["portal"].astype(np.float32) / 255
ves = np.maximum.reduce([d["portal"], d["hepv"], d["art"]]).astype(np.float32) / 255
pb = blur(portal, 6); pb /= pb.max()
vb = blur(ves, 14); vb /= vb.max()


def sample(spacing, dens, region):
    gy, gx = np.mgrid[0:H:spacing, 0:W:spacing]
    ax = (gx + rng.random(gx.shape) * spacing).ravel()
    ay = (gy + rng.random(gy.shape) * spacing).ravel()
    ix, iy = np.clip(ax.astype(int), 0, W - 1), np.clip(ay.astype(int), 0, H - 1)
    keep = region[iy, ix] & (rng.random(ax.size) < dens[iy, ix])
    return np.stack([ax[keep], ay[keep]], 1)


# ---- root path: extra-hepatic portal vein trunk (mm -> px)
s, (CX, CY) = float(d["px_per_mm"]), d["center"]
mx, mz = -10.35, 1105.53
mm = np.array([(-6.0, 982.0), (-8.5, 1015.0), (-10.5, 1045.0), (-11.2, 1062.9), (-13.5, 1080), (-16.5, 1097), (-19.2, 1110)])
path = np.stack([CX + (mm[:, 0] - mx) * s, CY - (mm[:, 1] - mz) * s], 1)
pts = [path[0]]
for a, b in zip(path[:-1], path[1:]):
    n = int(np.ceil(np.linalg.norm(b - a) / 4))
    for k in range(1, n + 1):
        pts.append(a + (b - a) * k / n)
pts = np.array(pts)
for _ in range(60):
    pts[1:-1] = 0.5 * pts[1:-1] + 0.25 * (pts[:-2] + pts[2:])
HILUM = pts[-1].copy()

P = list(pts)
par = [-1] + list(range(len(pts) - 1))
born = [0] * len(pts)
lev = [0] * len(pts)
nch = [1] * (len(pts) - 1) + [0]


def grow(A, D, KILL, R_INF, AGE, can_sprout, maxch_old, maxch_new, level, max_it=400):
    """grow new nodes (level) from nodes where can_sprout (bool over existing nodes) is True."""
    global P, par, born, lev, nch
    n_old = len(P)
    sprout = np.zeros(n_old, bool); sprout[:] = can_sprout
    Pa = np.asarray(P)
    live = np.ones(len(A), bool)
    for c in range(0, len(A), 1024):
        dd = ((A[c:c + 1024, None, :] - Pa[None, :, :]) ** 2).sum(-1)
        live[c:c + 1024] &= np.sqrt(dd.min(1)) >= KILL
    it = 0
    t0 = time.time()
    while it < max_it:
        it += 1
        Pa = np.asarray(P)
        bornA, nchA = np.asarray(born), np.asarray(nch)
        idx = np.arange(len(Pa))
        old = idx < n_old
        spr = np.zeros(len(Pa), bool); spr[:n_old] = sprout
        activ = np.nonzero(np.where(old, spr & (nchA < maxch_old),
                                    (it - bornA <= AGE) & (nchA < maxch_new)))[0]
        li = np.nonzero(live)[0]
        if len(li) == 0 or len(activ) == 0:
            break
        nd = np.full(len(li), 1e18); ni = np.zeros(len(li), np.int64)
        Q = Pa[activ]
        for c in range(0, len(li), 1024):
            dd = ((A[li[c:c + 1024], None, :] - Q[None, :, :]) ** 2).sum(-1)
            k = dd.argmin(1)
            nd[c:c + 1024] = dd[np.arange(len(k)), k]; ni[c:c + 1024] = activ[k]
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
        newp = Pa[nodes] + dirs * D
        xi, yi = np.clip(newp[:, 0].astype(int), 0, W - 1), np.clip(newp[:, 1].astype(int), 0, H - 1)
        ok = mask[yi, xi] > 0.4
        nodes, newp = nodes[ok], newp[ok]
        if len(newp) == 0:
            continue
        P.extend(list(newp)); par.extend(nodes.tolist()); born.extend([it] * len(newp))  # born: iteration within level
        lev.extend([level] * len(newp)); nch.extend([0] * len(newp))
        for q in nodes:
            nch[q] += 1
        li = np.nonzero(live)[0]
        dd = ((A[li, None, :] - newp[None, :, :]) ** 2).sum(-1)
        live[li[np.sqrt(dd.min(1)) < KILL]] = False
    print(f"level {level}: +{len(P) - n_old} nodes in {it} it, {live.sum()} attractors left, {time.time() - t0:.1f}s")


yy, xx = np.mgrid[0:H, 0:W]
near_hilum = (xx - HILUM[0]) ** 2 + (yy - HILUM[1]) ** 2 < 55 ** 2
# L1 trunks: along the portal projection, plus sparse cover so every lobe gets a trunk
A1 = np.concatenate([sample(30, np.clip(pb * 2.0, 0, 1), erode(inside, 15) & (pb > 0.15) & ~near_hilum),
                     sample(70, np.ones_like(mask), erode(inside, 41) & ~near_hilum)])
print("L1 attractors", len(A1))
sp = np.zeros(len(P), bool); sp[-1] = True
grow(A1, D=5.0, KILL=22, R_INF=260, AGE=6, can_sprout=sp, maxch_old=2, maxch_new=2, level=1)

n1 = len(P)
A2 = sample(22, 0.55 + 0.45 * vb, erode(inside, 13))
print("L2 attractors", len(A2))
sp = (np.asarray(lev) == 1) & (rng.random(len(P)) < 0.6)
grow(A2, D=4.0, KILL=13, R_INF=70, AGE=7, can_sprout=sp, maxch_old=3, maxch_new=2, level=2)

A3 = sample(8.5, 0.6 + 0.4 * vb, erode(inside, 5))
print("L3 attractors", len(A3))
sp = (np.asarray(lev) >= 1) & (rng.random(len(P)) < 0.2)
grow(A3, D=3.0, KILL=6.5, R_INF=44, AGE=9, can_sprout=sp, maxch_old=3, maxch_new=2, level=3)

P = np.asarray(P, np.float32)
par = np.asarray(par, np.int32)
lev = np.asarray(lev, np.int8)
n = len(P)
NR = len(pts)
for _ in range(6):
    acc = np.zeros_like(P); cnt = np.zeros(n, np.float32)
    acc[1:] += P[par[1:]]; cnt[1:] += 1
    np.add.at(acc, par[1:], P[1:]); np.add.at(cnt, par[1:], 1)
    avg = acc / np.maximum(cnt, 1)[:, None]
    nchk = np.bincount(par[1:], minlength=n)
    mv = (np.arange(n) >= NR) & (nchk > 0)          # keep tips and the root path fixed
    P[mv] = 0.5 * P[mv] + 0.5 * avg[mv]
seg = np.zeros(n, np.float32)
seg[1:] = np.linalg.norm(P[1:] - P[par[1:]], axis=1)
# re-order so that parent < child holds (it does: nodes are only appended with existing parents)
assert (par[1:] < np.arange(1, n)).all()
L = np.zeros(n, np.float32)
for i in range(1, n):
    L[i] = L[par[i]] + seg[i]
nchild = np.bincount(par[1:], minlength=n)
leaves = (nchild == 0).astype(np.float32)
height = np.zeros(n, np.float32)
for i in range(n - 1, 0, -1):
    p = par[i]
    leaves[p] += leaves[i]
    height[p] = max(height[p], height[i] + seg[i])
print("nodes", n, "tips", int((nchild == 0).sum()), "max L", L.max())
red_par = par.copy()
np.savez_compressed(os.path.join(WORK, "tree.npz"), P=P, parent=par, level=lev, L=L, leaves=leaves,
                    height=height, seg=seg, nchild=nchild, hilum=HILUM, nroot=len(pts))

# ---- second tree: hepatic veins (drain upward into the IVC), interleaved with the portal tree
red_P = P.copy(); red_lev = lev.copy(); red_w = 0.42 * leaves ** (1 / 2.2)
prox = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(prox)
for i in np.nonzero(red_lev <= 2)[0]:
    if i:
        dr.line([tuple(red_P[par[i]]), tuple(red_P[i])], fill=255, width=int(max(1, red_w[i]) + 20))
near_red = np.asarray(prox) > 0
hepv = d["hepv"].astype(np.float32) / 255
hb = blur(hepv, 6); hb /= hb.max()
top = np.array([(847.0, -8.0), (845.0, 30.0), (832.0, 70.0), (812.0, 105.0), (798.0, 134.0)])
pts_b = [top[0]]
for a, b in zip(top[:-1], top[1:]):
    m = int(np.ceil(np.linalg.norm(b - a) / 4))
    for k in range(1, m + 1):
        pts_b.append(a + (b - a) * k / m)
pts_b = np.array(pts_b)
for _ in range(40):
    pts_b[1:-1] = 0.5 * pts_b[1:-1] + 0.25 * (pts_b[:-2] + pts_b[2:])
P = list(pts_b); par = [-1] + list(range(len(pts_b) - 1)); born = [0] * len(pts_b); lev = [0] * len(pts_b)
nch = [1] * (len(pts_b) - 1) + [0]
HV = pts_b[-1]
near_c = (xx - HV[0]) ** 2 + (yy - HV[1]) ** 2 < 45 ** 2
B1 = np.concatenate([sample(30, np.clip(hb * 2, 0, 1), erode(inside, 13) & (hb > 0.15) & ~near_c),
                     sample(84, np.ones_like(mask), erode(inside, 41) & ~near_c & ~near_red)])
sp = np.zeros(len(P), bool); sp[-1] = True
grow(B1, D=5.0, KILL=22, R_INF=240, AGE=6, can_sprout=sp, maxch_old=2, maxch_new=2, level=1)
B2 = sample(30, np.ones_like(mask), erode(inside, 13) & ~near_red)
sp = (np.asarray(lev) == 1) & (rng.random(len(P)) < 0.5)
grow(B2, D=4.0, KILL=16, R_INF=64, AGE=7, can_sprout=sp, maxch_old=3, maxch_new=2, level=2)
Pb = np.asarray(P, np.float32); parb = np.asarray(par, np.int32); levb = np.asarray(lev, np.int8)
nb = len(Pb)
for _ in range(6):
    acc = np.zeros_like(Pb); cnt = np.zeros(nb, np.float32)
    acc[1:] += Pb[parb[1:]]; cnt[1:] += 1
    np.add.at(acc, parb[1:], Pb[1:]); np.add.at(cnt, parb[1:], 1)
    avg = acc / np.maximum(cnt, 1)[:, None]
    ch = np.bincount(parb[1:], minlength=nb)
    mv = (np.arange(nb) >= len(pts_b)) & (ch > 0)
    Pb[mv] = 0.5 * Pb[mv] + 0.5 * avg[mv]
segb = np.zeros(nb, np.float32); segb[1:] = np.linalg.norm(Pb[1:] - Pb[parb[1:]], axis=1)
Lb = np.zeros(nb, np.float32)
for i in range(1, nb):
    Lb[i] = Lb[parb[i]] + segb[i]
chb = np.bincount(parb[1:], minlength=nb)
lvb = (chb == 0).astype(np.float32)
for i in range(nb - 1, 0, -1):
    lvb[parb[i]] += lvb[i]
print("blue nodes", nb, "tips", int((chb == 0).sum()))
np.savez_compressed(os.path.join(WORK, "tree_b.npz"), P=Pb, parent=parb, level=levb, L=Lb, leaves=lvb, seg=segb,
                    nchild=chb, nroot=len(pts_b))
# ---- quick look
SS = 2
im = Image.new("L", (W * SS, H * SS), 0)
dr = ImageDraw.Draw(im)
P = red_P; par = red_par
wpx = 0.42 * leaves ** (1 / 2.2)
for i in np.argsort(wpx):
    if i == 0:
        continue
    a, b = P[par[i]] * SS, P[i] * SS
    w = wpx[i] * SS
    if w < 1.0:
        dr.line([tuple(a), tuple(b)], fill=int(255 * max(w, 0.4)), width=1)
    else:
        dr.line([tuple(a), tuple(b)], fill=255, width=int(round(w)))
        r = w / 2
        dr.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=255)
a = np.asarray(im, np.float32).reshape(H, SS, W, SS).mean((1, 3)) / 255
rgb = np.stack([a * 232, a * 25, a * 15], -1) + 6
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(WORK, "tree_look.png"))
