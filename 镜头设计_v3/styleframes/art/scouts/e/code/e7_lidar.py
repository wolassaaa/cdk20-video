"""HKBU SCIE1007 coursework science video. Style scout e7: LiDAR point cloud.

A simulated spinning scanner fires real discrete beams at the real CDK20 field plus a floor and the title block, so
the returns wrap the form in scan lines and leave true scan shadows. Then the cloud is viewed from a different spot.
Usage: python e7_lidar.py [scale]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common import FONTS, LABEL, OUT, rot
from sdf import HALF, bilinear2, build, text_sdf, trilinear

S = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
W, H = int(1280 * S), int(720 * S)
g, conf, _ = build()
tsd, down = text_sdf("CDK20", "bahnschrift.ttf", size=220)
th, tw = tsd.shape
R = rot(-72, 0, 28)     # stand the molecule up on the floor
FLOOR = -44.0
TSC = 1.5
ro = np.array([-30, -92, -38], np.float32)
ta = np.array([58, 40, 8], np.float32)
ww = (ta - ro) / np.linalg.norm(ta - ro)
up = np.array([0.05, 0, 1], np.float32)
uu = np.cross(ww, up); uu /= np.linalg.norm(uu)
vv = np.cross(uu, ww)
TPOS = ro + ww * 318 + uu * 162 + vv * 78


def map_scene(p):
    d = trilinear(g, p @ R)                                       # protein
    d = np.minimum(d, p[:, 2] - FLOOR)                            # floor
    tp = p - TPOS                                                 # upright title wall behind the molecule
    u = tp[:, 0] / TSC + tw / 2
    v = -tp[:, 2] / TSC + th / 2
    d2 = bilinear2(tsd, u, v) * TSC / down
    out = np.maximum(np.maximum(-u, u - tw), np.maximum(-v, v - th)) * TSC
    d2 = np.where(out > 0, np.maximum(d2, 0) + out, d2)
    dz = np.abs(tp[:, 1]) - 5.0
    dt = np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2)
    return np.minimum(d, dt)


def scan(origin, n_beams, n_az, el0, el1, seed=0):
    rng = np.random.default_rng(seed)
    el = np.radians(np.linspace(el0, el1, n_beams))
    az = np.radians(np.linspace(0, 360, n_az, endpoint=False)) + rng.normal(0, 3e-4, n_az)
    E, A = np.meshgrid(el, az, indexing="ij")
    rd = np.stack([np.cos(E) * np.cos(A), np.cos(E) * np.sin(A), np.sin(E)], -1).reshape(-1, 3).astype(np.float32)
    beam = np.repeat(np.arange(n_beams), n_az)
    N = len(rd)
    t = np.ones(N, np.float32) * 2
    alive = np.arange(N)
    hit = np.zeros(N, bool)
    for _ in range(120):
        if not len(alive):
            break
        p = origin + rd[alive] * t[alive, None]
        d = map_scene(p)
        h = d < 0.06
        hit[alive[h]] = True
        t[alive] += d * 0.9
        alive = alive[(~h) & (t[alive] < 640)]
    pts = origin + rd[hit] * t[hit, None]
    return pts, rd[hit], t[hit], beam[hit]


# two scanner stops, the way a real survey is stitched
sets = []
for o, seed in [((-60, -74, -10), 1), ((70, -66, 18), 2)]:
    o = np.array(o, np.float32)
    pts, r, tt, bm = scan(o, 240, 7000, -62, 52, seed)
    sets.append((pts, r, tt, bm))
    print("scan", len(pts))
pts = np.concatenate([s[0] for s in sets])
rays = np.concatenate([s[1] for s in sets])
rng_t = np.concatenate([s[2] for s in sets])
beam = np.concatenate([s[3] for s in sets])

# return intensity: incidence angle, like a real sensor
e = 0.5
nrm = np.stack([
    map_scene(pts + [e, 0, 0]) - map_scene(pts - [e, 0, 0]),
    map_scene(pts + [0, e, 0]) - map_scene(pts - [0, e, 0]),
    map_scene(pts + [0, 0, e]) - map_scene(pts - [0, 0, e]),
], 1)
nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
inc = np.abs((nrm * rays).sum(1))
cf = trilinear(conf, pts @ R)
d_prot = trilinear(g, pts @ R)
on_prot = d_prot < 0.6
on_floor = pts[:, 2] < FLOOR + 0.3

# The low confidence tail lifts off as a data storm: real pLDDT decides which returns drift
rng = np.random.default_rng(5)
drift = np.clip((0.72 - cf) / 0.25, 0, 1) * on_prot
wind = np.array([1.0, 0.25, 0.30], np.float32)
amt = (rng.random(len(pts)) ** 2.2) * drift * 300
pos = pts + wind * amt[:, None] + rng.normal(0, 1, pts.shape) * (amt[:, None] * 0.14)
# scan slices slipping sideways: a data fault, not a flicker
band = ((pts[:, 2] + 80) // 7).astype(int)
glitch = np.where((np.sin(band * 12.9898) * 43758.5) % 1 > 0.91, 1.0, 0.0)
pos[:, 0] += glitch * on_prot * ((np.sin(band * 78.2) * 9000) % 1 - 0.5) * 34

rel = pos - ro
zc = rel @ ww
ok = zc > 4
f = 1.62 * H / 2
xs = (rel[ok] @ uu) / zc[ok] * f + W / 2
ys = -(rel[ok] @ vv) / zc[ok] * f + H / 2

val = (0.20 + 0.95 * inc[ok] ** 1.3) * np.where(on_floor[ok], 0.42, 1.0)
val *= np.where(on_prot[ok], 1.25, 1.0)
val *= np.where(amt[ok] > 4, 4.0, 1.0)
val *= np.clip(120 / zc[ok], 0.42, 1.25) ** 1.3
val *= np.where(zc[ok] > 230, 2.4, 1.0)
# house lights colour: cold cyan white, amber only on what is about to leave
c0 = np.array([0.72, 0.92, 1.0], np.float32)
c1 = np.array([1.0, 0.38, 0.12], np.float32)
mix = drift[ok][:, None]
cc = c0 * (1 - mix) + c1 * mix
out = np.zeros((H, W, 3), np.float32)
ix = np.clip(xs, 0, W - 1.001)
iy = np.clip(ys, 0, H - 1.001)
inside = (xs >= 0) & (xs < W - 1) & (ys >= 0) & (ys < H - 1)
i, j = ix.astype(int), iy.astype(int)
fx, fy = ix - i, iy - j
for dx, dy, wt in [(0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)]:
    for ch in range(3):
        np.add.at(out[..., ch], (j[inside] + dy, i[inside] + dx), (val * wt * cc[:, ch])[inside] * 0.62)
print("splat")
# small sensor bloom
b = Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255))
from PIL import ImageFilter

bloom = np.asarray(b.filter(ImageFilter.GaussianBlur(5 * S)), np.float32) / 255
img = out + bloom * 0.8
img = 1 - np.exp(-img * 1.35)
img = np.clip(img, 0, 1) ** 0.86
im = Image.fromarray((img * 255).astype(np.uint8))
if S > 1:
    im = im.resize((1280, 720), Image.LANCZOS)
d = ImageDraw.Draw(im)
fnt = ImageFont.truetype(FONTS + "/consola.ttf", 22)
d.text((34, 668), LABEL, font=fnt, fill=(215, 240, 255))
im.save(OUT / ("e7_lidar.png" if S >= 1 else "_e7_test.png"))
print("saved")
