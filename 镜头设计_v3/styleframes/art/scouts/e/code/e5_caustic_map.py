"""HKBU SCIE1007 coursework science video. Style scout e5: forward photon trace through the real CDK20 field.

Light travels straight down through glass shaped by the real atoms, bends twice with a different IOR per colour, and
lands on the table. Saved as a floor texture for Blender. Numpy only, system Python.
"""
import numpy as np
from PIL import Image, ImageFilter

from common import WORK, rot
from sdf import HALF, build, trilinear

g, conf, _ = build()
R = rot(-70, 0, 200)        # same pose as the Blender scene
SCALE = 0.1                 # scene units per Angstrom
Z_CENTER = 3.4 / SCALE      # molecule centre above the table, Angstrom
LIGHT = np.array([0.62, 0.42, -0.66], np.float32)
LIGHT /= np.linalg.norm(LIGHT)
TEX, SPAN = 2048, 34.0      # texture size, scene units covered


def grad(p):
    e = 0.5
    n = np.stack([
        trilinear(g, (p + [e, 0, 0]) @ R) - trilinear(g, (p - [e, 0, 0]) @ R),
        trilinear(g, (p + [0, e, 0]) @ R) - trilinear(g, (p - [0, e, 0]) @ R),
        trilinear(g, (p + [0, 0, e]) @ R) - trilinear(g, (p - [0, 0, e]) @ R),
    ], 1)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)


def refract(i, n, eta):
    c = -(i * n).sum(1, keepdims=True)
    k = 1 - eta * eta * (1 - c * c)
    ok = k[:, 0] > 0
    return eta * i + (eta * c - np.sqrt(np.maximum(k, 0))) * n, ok


def shoot(ior, N, seed):
    rng = np.random.default_rng(seed)
    # disc of photons perpendicular to the light
    a = np.cross(LIGHT, [0, 1, 0]); a /= np.linalg.norm(a)
    b = np.cross(LIGHT, a)
    u, v = rng.uniform(-44, 44, N), rng.uniform(-44, 44, N)
    o = (a[None] * u[:, None] + b[None] * v[:, None] - LIGHT * 75).astype(np.float32)
    d = np.tile(LIGHT, (N, 1))
    t = np.zeros(N, np.float32)
    alive = np.arange(N)
    hit = np.zeros(N, bool)
    for _ in range(55):
        p = o[alive] + d[alive] * t[alive, None]
        s = trilinear(g, p @ R)
        h = s < 0.03
        hit[alive[h]] = True
        t[alive] += np.maximum(s, 0.05)
        alive = alive[(~h) & (t[alive] < 170)]
        if not len(alive):
            break
    # photons that miss cast plain light later; keep them with weight 1
    miss = ~hit
    idx = np.nonzero(hit)[0]
    p = o[idx] + d[idx] * t[idx, None]
    n = grad(p)
    d1, ok = refract(d[idx], n, 1 / ior)
    idx, p, d1 = idx[ok], p[ok], d1[ok]
    # inside the glass, march on the negative field until out
    s_t = np.full(len(idx), 0.8, np.float32)
    live = np.arange(len(idx))
    for _ in range(60):
        q = p[live] + d1[live] * s_t[live, None]
        s = -trilinear(g, q @ R)
        h = s < 0.03
        s_t[live] += np.maximum(s, 0.08)
        live = live[(~h) & (s_t[live] < 80)]
        if not len(live):
            break
    p2 = p + d1 * s_t[:, None]
    n2 = -grad(p2)
    d2, ok2 = refract(d1, n2, ior)
    return p2[ok2], d2[ok2], o[miss], d[miss]


floor = -Z_CENTER
img = np.zeros((TEX, TEX, 3), np.float32)


def splat(ch, p, d, w):
    tt = (floor - p[:, 2]) / np.minimum(d[:, 2], -1e-3)
    q = p + d * tt[:, None]
    ok = d[:, 2] < -1e-3
    xs = (q[ok, 0] * SCALE / SPAN + 0.5) * TEX
    ys = (q[ok, 1] * SCALE / SPAN + 0.5) * TEX
    i, j = xs.astype(int), ys.astype(int)
    m = (i >= 0) & (i < TEX) & (j >= 0) & (j < TEX)
    np.add.at(img[..., ch], (j[m], i[m]), w)


for ch, ior in enumerate((1.46, 1.50, 1.56)):       # strong dispersion on purpose: a rainbow is the point of this frame
    for rnd in range(2):
        p, d, po, dm = shoot(ior, 1300000, 100 * ch + rnd)
        splat(ch, p, d, 1.0)
        print(ch, rnd, len(p))
area_px = (96 / (SPAN / SCALE) * TEX) ** 2
base = 2 * 1300000 / area_px
img /= base
for _ in range(2):
    img = (img + np.roll(img, 1, 0) + np.roll(img, -1, 0) + np.roll(img, 1, 1) + np.roll(img, -1, 1)) / 5
print("mean", img.mean(), "max", img.max())
np.save(WORK / "e5_caustic.npy", img.astype(np.float16))
tone = np.clip(img / 2.0, 0, 1) ** 0.5
Image.fromarray((tone * 255).astype(np.uint8)).save(WORK / "e5_caustic.png")
