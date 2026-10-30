"""Build the static splat set for the liver (numpy only).
python build_splats.py MESHES.npz OUT.npz [--scale 1.0]

Every splat = centre, rotation, three hull half-sizes (4 sigma), base colour (linear), opacity, view-dependent gains,
plus the data the animation needs: a cloud start position, a formation delay, and (for the four lives) a life index
and weight. Groups: 0 skin, 1 volume haze, 2 red vessels, 3 blue vessels, 4 bile ducts (white), 5 life, 6 coarse blob, 7 dust.
"""
import sys, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("meshes"); ap.add_argument("out")
ap.add_argument("--scale", type=float, default=1.0, help="multiplies splat counts")
A = ap.parse_args()
M = np.load(A.meshes)
rng = np.random.default_rng(20261030)


def s2l(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


BONE, RED, RED_D, BLUE, KLEIN = s2l("#EDEBE4"), s2l("#E8190F"), s2l("#9A0E08"), s2l("#1F3BFF"), s2l("#002FA7")


# ------------------------------------------------------------------ smooth deterministic noise (sum of sinusoids)
class Noise:
    def __init__(self, seed, n=7, freq=1.0):
        r = np.random.default_rng(seed)
        self.k = r.normal(size=(n, 3)) * freq
        self.ph = r.random(n) * 2 * np.pi
        self.a = 1.0 / np.sqrt(n) * np.sqrt(2)

    def __call__(self, p):
        return (np.sin(p @ self.k.T + self.ph) * self.a).sum(1)


def vnoise(seed, freq):
    ns = [Noise(seed + i, freq=freq) for i in range(3)]
    return lambda p: np.stack([n(p) for n in ns], 1)


# ------------------------------------------------------------------ sampling helpers
def tri_area(v, t):
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)


def sample(v, t, vn, n, blue=True):
    """area-weighted samples; blue=True: oversample 3x and keep one per hash cell for an even, clump-free spread."""
    ar = tri_area(v, t)
    m = n * 3 if blue else n
    fi = rng.choice(len(t), m, p=ar / ar.sum())
    r1, r2 = rng.random(m), rng.random(m)
    s = np.sqrt(r1); u, w, x = 1 - s, s * (1 - r2), s * r2
    p = u[:, None] * v[t[fi, 0]] + w[:, None] * v[t[fi, 1]] + x[:, None] * v[t[fi, 2]]
    nn = u[:, None] * vn[t[fi, 0]] + w[:, None] * vn[t[fi, 1]] + x[:, None] * vn[t[fi, 2]]
    nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    if blue:
        h = np.sqrt(ar.sum() / n) * 0.62
        key = np.floor(p / h).astype(np.int64)
        key = key[:, 0] * 73856093 ^ key[:, 1] * 19349663 ^ key[:, 2] * 83492791
        _, first = np.unique(key, return_index=True)
        first = rng.permutation(first)[:n]
        p, nn, fi = p[first], nn[first], fi[first]
    return p, nn, fi


def frame_from(nrm, tdir):
    """rotation matrices with columns (t1, t2, n); t1 = tdir projected to the tangent plane."""
    t1 = tdir - (tdir * nrm).sum(1, keepdims=True) * nrm
    bad = np.linalg.norm(t1, axis=1) < 1e-4
    if bad.any():
        alt = np.cross(nrm[bad], [0.0, 0.0, 1.0]); alt[np.linalg.norm(alt, axis=1) < 1e-4] = [1.0, 0, 0]
        t1[bad] = alt
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    t2 = np.cross(nrm, t1)
    return np.stack([t1, t2, nrm], 2)


def euler(R):
    y = np.arcsin(np.clip(-R[:, 2, 0], -1, 1))
    x = np.arctan2(R[:, 2, 1], R[:, 2, 2])
    z = np.arctan2(R[:, 1, 0], R[:, 0, 0])
    return np.stack([x, y, z], 1)


def curvature(v, t, vn):
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    k = np.linalg.norm(vn[e[:, 0]] - vn[e[:, 1]], axis=1) / (np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1) + 1e-6)
    kv = np.zeros(len(v)); cnt = np.zeros(len(v))
    np.add.at(kv, e[:, 0], k); np.add.at(cnt, e[:, 0], 1)
    np.add.at(kv, e[:, 1], k); np.add.at(cnt, e[:, 1], 1)
    return kv / np.maximum(cnt, 1)


OUT = {k: [] for k in ("T", "R", "S", "COL", "NRM", "A", "RIM", "SPEC", "GLOW", "DIF", "G")}


def add(T, R, S, col, nrm, a, rim, spec, glow, dif, g):
    n = len(T)
    OUT["T"].append(T); OUT["R"].append(R); OUT["S"].append(S)
    OUT["COL"].append(np.broadcast_to(col, (n, 3)).astype(np.float64)); OUT["NRM"].append(nrm)
    for k, x in (("A", a), ("RIM", rim), ("SPEC", spec), ("GLOW", glow), ("DIF", dif)):
        OUT[k].append(np.broadcast_to(np.asarray(x, np.float64), (n,)).copy())
    OUT["G"].append(np.full(n, g, np.int32))


K = A.scale
swirl = vnoise(11, 1.3)

# ------------------------------------------------------------------ 0 skin (bone glass)
sv, st, sn = M["skin_v"], M["skin_t"], M["skin_n"]
kv = curvature(sv, st, sn)
n_skin = int(135000 * K)
P, N_, fi = sample(sv, st, sn, n_skin)
kap = kv[st[fi]].mean(1)
tdir = swirl(P * 1.0) + np.array([1.0, 0.2, 0.35])
R = frame_from(N_, tdir)
ang = rng.normal(0, 0.35, n_skin)  # +-20 deg jitter of the stroke direction
c, s_ = np.cos(ang), np.sin(ang)
t1 = R[:, :, 0] * c[:, None] + R[:, :, 1] * s_[:, None]
R = frame_from(N_, t1)
area = tri_area(sv, st).sum()
h0 = np.sqrt(area / n_skin)                       # mean spacing
size = h0 * 2.6 * np.exp(rng.normal(0, 0.30, n_skin)) / (1 + 0.05 * kap)
size = np.clip(size, h0 * 0.7, h0 * 6.0)
asp = 1.0 + 1.6 * rng.random(n_skin) ** 2
S = np.stack([size * np.sqrt(asp), size / np.sqrt(asp), size * (0.12 + 0.12 * rng.random(n_skin))], 1)
# a few big flat splats (the large anisotropic gaussians 3DGS grows on smooth regions)
big = rng.random(n_skin) < 0.035
S[big] *= np.array([3.2, 2.2, 1.0])
aS = np.clip(0.085 * np.exp(rng.normal(0, 0.25, n_skin)), 0.02, 0.25)
aS[big] *= 0.35
P = P + N_ * rng.normal(0, 0.0012, (n_skin, 1))
tone = Noise(41, freq=2.2)(P)   # slow tonal drift across the surface instead of per-splat speckle
lum = 0.026 * (1 + 0.25 * tone)
add(P, R, S * 0.8, BONE * lum[:, None], N_, aS, 24.0, 26.0, 1.0, 0.75, 0)
# fringe: thin long splats just off the surface, the fuzzy edge a radiance field has at silhouettes
n_f = int(9000 * K)
Pf, Nf, _ = sample(sv, st, sn, n_f, blue=False)
off = 0.004 + 0.030 * rng.random(n_f) ** 2.2
Rf = frame_from(Nf, swirl(Pf) + rng.normal(0, 0.4, (n_f, 3)))
sz = 0.016 * np.exp(rng.normal(0, 0.35, n_f))
add(Pf + Nf * off[:, None], Rf, np.stack([sz * 2.0, sz * 0.5, sz * 0.25], 1), BONE * 0.10, Nf, 0.10, 2.0, 0.0, 1.0, 0.0, 0)
print("skin", n_skin, "area %.2f  spacing %.4f" % (area, h0))

# ------------------------------------------------------------------ 1 interior haze
vp, vd = M["vol_p"], M["vol_d"]
n_vol = min(int(3000 * K), len(vp))
pick = rng.permutation(len(vp))[:n_vol]
P = vp[pick].astype(np.float64); d = vd[pick]
P += rng.normal(0, 0.006, P.shape)
R = frame_from(np.tile([0, 0, 1.0], (n_vol, 1)), rng.normal(size=(n_vol, 3)))
size = 0.075 * np.exp(rng.normal(0, 0.3, n_vol))
S = np.stack([size * 1.4, size, size * 0.8], 1)
a = 0.022 * np.clip(1 - d / 0.4, 0.25, 1)
add(P, R, S, BONE * 0.10, R[:, :, 2], a, 0.0, 0.0, 1.0, 0.0, 1)
print("volume", n_vol)


# ------------------------------------------------------------------ 2/3 vessels
def vessel(names, n, col, g, alpha=0.72, rim=1.5, spec=0.5, clip=None, zhi=None, zlo=None, span=0.3):
    vs, ts, ns = [], [], []
    off = 0
    for nm in names:
        v, t, vn = M[nm + "_v"], M[nm + "_t"], M[nm + "_n"]
        vs.append(v); ts.append(t + off); ns.append(vn); off += len(v)
    v, t, vn = np.concatenate(vs), np.concatenate(ts), np.concatenate(ns)
    if clip is not None:
        keep = clip(v[t].mean(1)); t = t[keep]
    P, N_, _ = sample(v, t, vn, n)
    # local vessel axis: smallest-eigenvalue eigenvector of the normals' covariance per 3 mm cell
    cell = 0.03
    key = np.floor(P / cell).astype(np.int64)
    _, inv = np.unique(key[:, 0] * 73856093 ^ key[:, 1] * 19349663 ^ key[:, 2] * 83492791, return_inverse=True)
    nc = inv.max() + 1
    cov = np.zeros((nc, 3, 3)); cen = np.zeros((nc, 3)); cnt = np.zeros(nc)
    np.add.at(cov, inv, N_[:, :, None] * N_[:, None, :]); np.add.at(cen, inv, P); np.add.at(cnt, inv, 1)
    w, V = np.linalg.eigh(cov + np.eye(3) * 1e-6)
    axis = V[:, :, 0][inv]
    cen = (cen / cnt[:, None])[inv]
    d = P - cen; d -= (d * axis).sum(1, keepdims=True) * axis
    rad = np.sqrt(np.maximum((d * d).sum(1), 1e-8))
    radc = np.zeros(nc); np.add.at(radc, inv, rad); radc = (radc / cnt)[inv]
    R = frame_from(N_, axis)
    across = np.clip(radc * 0.46, 0.0036, 0.016) * np.exp(rng.normal(0, 0.22, n))
    along = np.minimum(across * (3.0 + 2.5 * rng.random(n)), 0.055)
    S = np.stack([along, across, across * 0.35], 1)
    lum = np.exp(rng.normal(0, 0.24, n))
    # outside the organ the trees thin out and dissolve instead of ending in a cut
    zhi = sv[:, 2].max() - 0.18 if zhi is None else zhi
    zlo = sv[:, 2].min() + 0.30 if zlo is None else zlo
    over = np.maximum(np.maximum(P[:, 2] - zhi, zlo - P[:, 2]), 0.0)
    fade = 1 - np.clip(over / span, 0, 1)
    keep = rng.random(n) < fade ** 1.5
    add(P[keep], R[keep], S[keep], (col * lum[:, None])[keep], N_[keep], (alpha * np.exp(rng.normal(0, 0.15, n)) * fade)[keep], rim, spec, 1.0, 0.40, g)
    print("vessel", names, n)


vessel(["portal", "portal_x", "artery"], int(70000 * K), RED * 0.62, 2)
vessel(["hveins"], int(38000 * K), BLUE * 0.62, 3)
vessel(["ivc"], int(6000 * K), BLUE * 0.45, 3, alpha=0.7, zhi=0.46, zlo=-0.02, span=0.26)

# ------------------------------------------------------------------ 4 bile ducts: faint white filaments
bv, bt, bn = M["bile_v"], M["bile_t"], M["bile_n"]
n_b = int(9000 * K)
P, N_, _ = sample(bv, bt, bn, n_b)
R = frame_from(N_, rng.normal(size=(n_b, 3)))
size = 0.006 * np.exp(rng.normal(0, 0.2, n_b))
add(P, R, np.stack([size * 1.8, size, size * 0.4], 1), BONE * 0.22, N_, 0.22, 1.0, 0.3, 1.0, 0.5, 4)

# ------------------------------------------------------------------ 5 four lives: knots of light under the anterior skin
lives = []
ant = np.array([0, -1.0, 0.18]); ant /= np.linalg.norm(ant)
for xt, zt in ((-0.66, 0.10), (-0.24, 0.24), (0.18, 0.12), (0.56, 0.20)):
    cand = (np.abs(sv[:, 0] - xt) < 0.06) & (sn @ ant > 0.55)
    idx = np.where(cand)[0]
    j = idx[np.argmin(np.abs(sv[idx, 2] - zt) - 0.4 * (sn[idx] @ ant))]
    lives.append((sv[j] - sn[j] * 0.075, sn[j].copy()))
lives_p = np.array([l[0] for l in lives]); lives_n = np.array([l[1] for l in lives])
print("lives", np.round(lives_p, 3))
for k, (c, nn) in enumerate(lives):
    n_l = int(1300 * K)
    g = rng.normal(size=(n_l, 3)) * 0.024
    g -= (g @ nn)[:, None] * nn * 0.45
    r = np.linalg.norm(g, axis=1)
    P = c + g
    R = frame_from(np.tile(nn, (n_l, 1)), rng.normal(size=(n_l, 3)))
    size = 0.015 * np.exp(rng.normal(0, 0.25, n_l))
    S = np.stack([size * 1.5, size, size * 0.7], 1)
    a = 0.018 * np.exp(-r * r / (2 * 0.034 ** 2))
    add(P, R, S, BONE * (2.4 + 7.0 * np.exp(-r * r / (2 * 0.013 ** 2)))[:, None], R[:, :, 2], a, 0.0, 0.0, 1.0, 0.0, 5)
    # soft halo
    n_h = 36
    P = c + rng.normal(size=(n_h, 3)) * 0.02
    R = frame_from(np.tile(nn, (n_h, 1)), rng.normal(size=(n_h, 3)))
    size = 0.13 * np.exp(rng.normal(0, 0.2, n_h))
    add(P, R, np.stack([size, size, size * 0.8], 1), BONE * 1.3, R[:, :, 2], 0.005, 0.0, 0.0, 1.0, 0.0, 5)

# ------------------------------------------------------------------ 6 coarse blobs (early-training gaussians)
skinP = np.concatenate(OUT["T"][:1])
for cell, amp, g_alpha in ((0.30, 1.0, 0.10), (0.14, 0.62, 0.09)):
    key = np.floor(skinP / cell).astype(np.int64)
    _, inv = np.unique(key[:, 0] * 73856093 ^ key[:, 1] * 19349663 ^ key[:, 2] * 83492791, return_inverse=True)
    nc = inv.max() + 1
    cen = np.zeros((nc, 3)); cnt = np.zeros(nc)
    np.add.at(cen, inv, skinP); np.add.at(cnt, inv, 1)
    cen /= cnt[:, None]
    keep = cnt > 40
    cen = cen[keep]; nb = len(cen)
    R = frame_from(np.tile([0, 0, 1.0], (nb, 1)), rng.normal(size=(nb, 3)))
    size = cell * 0.85 * np.exp(rng.normal(0, 0.15, nb))
    S = np.stack([size * 1.2, size, size * 0.85], 1)
    add(cen, R, S, BONE * 0.30, R[:, :, 2], g_alpha, 0.0, 0.0, amp, 0.0, 6)
    print("blobs", cell, nb)

# ------------------------------------------------------------------ 7 floaters: the stray gaussians every real capture leaves hanging
#   near the subject; they are few, soft and long, and they are what makes the space around the organ read as a field
n_d = int(70 * K)
Pf, Nf, _ = sample(sv, st, sn, n_d, blue=False)
P = Pf + Nf * (0.03 + 0.42 * rng.random(n_d) ** 1.6)[:, None]
Nr = rng.normal(size=(n_d, 3)); Nr /= np.linalg.norm(Nr, axis=1, keepdims=True)
R = frame_from(Nr, rng.normal(size=(n_d, 3)))
size = 0.045 * np.exp(rng.normal(0, 0.4, n_d))
add(P, R, np.stack([size * 1.7, size, size * 0.6], 1), BONE * 0.14, R[:, :, 2], 0.03 + 0.04 * rng.random(n_d) ** 2, 0.0, 0.0, 1.0, 0.0, 7)
print("floaters", n_d)

# ------------------------------------------------------------------ 9 hollows: black, opaque-ish splats that fade in where a life was.
#   A radiance field can hold darkness as well as light: these occlude the far wall and the vessels behind.
for k in range(4):
    n_v = 70
    g_ = rng.normal(size=(n_v, 3)) * np.array([0.050, 0.042, 0.050])
    P = lives_p[k] + g_
    R = frame_from(np.tile(lives_n[k], (n_v, 1)), rng.normal(size=(n_v, 3)))
    size = 0.135 * np.exp(rng.normal(0, 0.12, n_v))
    add(P, R, np.stack([size, size, size], 1), np.zeros(3), R[:, :, 2], 0.19, 0.0, 0.0, float(k), 0.0, 9)

# ------------------------------------------------------------------ 8 threads: hidden until the life goes; then they unspool upward
for k in range(4):
    n_t = int(3600 * K)
    P = np.tile(lives_p[k], (n_t, 1))
    Rm = np.tile(np.eye(3), (n_t, 1, 1))     # axis aligned: the ellipsoids hang along the plume
    add(P, Rm, np.ones((n_t, 3)), BONE, Rm[:, :, 2], 0.0, 0.0, 0.0, float(k), 0.0, 8)

# ------------------------------------------------------------------ assemble
D = {k: np.concatenate(v).astype(np.float32 if k != "G" else np.int32) for k, v in OUT.items()}
N = len(D["T"])
D["E"] = euler(D["R"].astype(np.float64)).astype(np.float32); del D["R"]
G = D["G"]; T = D["T"].astype(np.float64)

# cloud start: the liver dissolved -- expanded, swirled, lifted
warp = vnoise(23, 0.75)
rc = np.random.default_rng(8)
neb = rc.normal(size=(N, 3)) * np.array([0.58, 0.42, 0.36])     # a volume, not a warped surface
wp = warp(T); wp -= wp.mean(0)
C = T * 0.50 + 0.36 * wp + neb + np.array([0.0, 0.45, -0.20])
b6 = G == 6
C[b6] = T[b6] * 1.20 + 0.40 * (warp(T[b6]) - wp.mean(0)) + np.array([0.1, 0.25, 0.0])
C[G == 7] = T[G == 7]; C[G == 9] = T[G == 9]
# the mist is not even: a slow density field gives it lobes and voids
dens = Noise(57, freq=1.5)(C) + 0.6 * Noise(58, freq=3.1)(C)
D["CM"] = np.clip((dens + 0.45) / 1.4, 0, 1).astype(np.float32) ** 1.5
D["C"] = C.astype(np.float32)

# formation delay (frames): a smooth front from the core out, vessels later, lives last
dn = Noise(31, freq=1.6)
r = np.linalg.norm(T / np.array([1.0, 0.8, 0.75]), axis=1)
delay = 26 * np.clip(r / 1.1, 0, 1) + 9 * dn(T)
delay[(G == 2) | (G == 3) | (G == 4)] += 15
delay[G == 5] = 34 + 3 * dn(T[G == 5])
delay[G == 1] += 8
D["DEL"] = delay.astype(np.float32)

# life membership: each life owns its knot + the skin / haze / vessel splats around it (the hollow)
LIFE = np.full(N, -1, np.int32); LW = np.zeros(N, np.float32)
off = 0
for k in range(4):
    d = np.linalg.norm(T - lives_p[k], axis=1)
    w = np.clip(1 - d / 0.165, 0, 1) ** 1.1
    m = (w > LW) & (G != 7) & (G != 6) & (G != 9) & (G != 8)
    LIFE[m] = k; LW[m] = w[m]
# the knots are fully owned
gl = np.where(G == 5)[0]
d = np.linalg.norm(T[gl][:, None] - lives_p[None], axis=2)
LIFE[gl] = d.argmin(1); LW[gl] = 1.0
gv = np.where((G == 9) | (G == 8))[0]
LIFE[gv] = D["GLOW"][gv].astype(np.int32); LW[gv] = 1.0
D["GLOW"][gv] = 0.0
D["LIFE"] = LIFE; D["LW"] = LW
D["lives_p"] = lives_p.astype(np.float32); D["lives_n"] = lives_n.astype(np.float32)
np.savez(A.out, **D)
print("total splats", N, {int(g): int((G == g).sum()) for g in np.unique(G)})
