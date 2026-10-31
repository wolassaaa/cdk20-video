"""HKBU SCIE1007 coursework science video. Style scout e1: demoscene ray marching.

A true sphere-traced distance field in numpy. The field is the real CDK20 atoms, mirrored into an endless lattice.
Usage: python e1_raymarch.py [scale]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common import FONTS, LABEL, OUT, rot
from sdf import HALF, bilinear2, build, text_sdf, trilinear

S = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
W, H = int(1280 * S), int(720 * S)
g, conf, _ = build()
tsd, down = text_sdf("CDK20", "impact.ttf", size=220)
th, tw = tsd.shape

L = 66.0                 # half lattice period
R = rot(18, 34, -8)      # how the molecule sits inside each cell
RT = R.T


def map_scene(p, want_id=False):
    """p N x 3. Returns distance. Mirrored lattice of the molecule, thin struts along cell edges, the title block."""
    q = np.abs(np.mod(p + L, 2 * L) - L)                      # mirrored repeat: q in 0..L
    s = np.sign(np.mod(p + L, 4 * L) - 2 * L)                 # flips so neighbours are not all the same pose
    mq = (p + L) % (2 * L) - L
    d = trilinear(g, (mq @ R) * 1.0)
    # strut grid along the edges of the cell
    e = L - q
    dx = np.sqrt(e[:, 1] ** 2 + e[:, 2] ** 2)
    dy = np.sqrt(e[:, 0] ** 2 + e[:, 2] ** 2)
    dz = np.sqrt(e[:, 0] ** 2 + e[:, 1] ** 2)
    st = np.minimum(np.minimum(dx, dy), dz) - 0.9
    global LAST_ST, LAST_P
    LAST_ST, LAST_P = st, d
    # title: extruded 2D field, only at the origin cell front
    tp = p - TPOS
    tp = tp @ TR
    sc = 0.215
    u = (tp[:, 0] / sc + tw / 2)
    v = (-tp[:, 1] / sc + th / 2)
    d2 = bilinear2(tsd, u, v) * sc / down
    outside = np.maximum(np.maximum(-u, u - tw), np.maximum(-v, v - th)) * sc
    d2 = np.maximum(d2, 0) * (d2 > 0) + d2 * (d2 <= 0) + np.maximum(outside, 0)
    dz2 = np.abs(tp[:, 2]) - 1.1
    dt = np.minimum(np.maximum(d2, dz2), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz2, 0) ** 2) - 0.08
    d3 = np.minimum(d, st)
    d3 = np.minimum(d3, dt)
    if want_id:
        ids = np.where(dt <= d3 + 1e-3, 2, np.where(st <= d3 + 1e-3, 1, 0))
        return d3, ids, mq
    return d3


ro = np.array([24.0, -10.0, 64.0], np.float32)
ta = np.array([-10.0, 2.0, -40.0], np.float32)
TPOS = None
TR = None

ww = (ta - ro) / np.linalg.norm(ta - ro)
roll = np.radians(-9)
up = np.array([np.sin(roll), np.cos(roll), 0], np.float32)
uu = np.cross(ww, up); uu /= np.linalg.norm(uu)
vv = np.cross(uu, ww)
TPOS = ro + ww * 25 - uu * 17 - vv * 12.5
TR = np.stack([uu, vv, -ww], 1) @ rot(4, -16, 4)
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
px = (x + 0.5 - W / 2) / (H / 2)
py = -(y + 0.5 - H / 2) / (H / 2)
fov = 1.05
rd = (px[..., None] * uu + py[..., None] * vv + fov * ww[None, None, :]).reshape(-1, 3)
rd /= np.linalg.norm(rd, axis=1, keepdims=True)
N = len(rd)

t = np.zeros(N, np.float32) + 1.0
glow = np.zeros(N, np.float32)
glow2 = np.zeros(N, np.float32)
steps = np.zeros(N, np.float32)
hit = np.zeros(N, bool)
alive = np.arange(N)
TMAX = 1400.0
for i in range(170):
    if len(alive) == 0:
        break
    p = ro + rd[alive] * t[alive, None]
    d = map_scene(p)
    glow[alive] += np.exp(-np.maximum(LAST_ST, 0) * 0.42) * 0.11
    glow2[alive] += np.exp(-np.maximum(LAST_P, 0) * 0.5) * 0.035
    steps[alive] += 1
    h = d < 0.0009 * t[alive] + 0.02
    hit[alive[h]] = True
    t[alive] += d * 0.82
    alive = alive[(~h) & (t[alive] < TMAX)]
print("march done", hit.mean())

pos = ro + rd * t[:, None]
col = np.zeros((N, 3), np.float32)
idx = np.nonzero(hit)[0]
hp = pos[idx]
e = 0.45
ds = np.stack([
    map_scene(hp + [e, 0, 0]) - map_scene(hp - [e, 0, 0]),
    map_scene(hp + [0, e, 0]) - map_scene(hp - [0, e, 0]),
    map_scene(hp + [0, 0, e]) - map_scene(hp - [0, 0, e]),
], 1)
nor = ds / np.maximum(np.linalg.norm(ds, axis=1, keepdims=True), 1e-6)
_, ids, mq = map_scene(hp, True)
lig = np.array([0.55, 0.62, 0.56], np.float32); lig /= np.linalg.norm(lig)

# soft shadow
sh = np.ones(len(idx), np.float32)
st = np.full(len(idx), 1.5, np.float32)
live = np.arange(len(idx))
for i in range(36):
    if len(live) == 0:
        break
    q = hp[live] + nor[live] * 0.6 + lig * st[live, None]
    d = map_scene(q)
    sh[live] = np.minimum(sh[live], np.clip(9 * d / st[live], 0, 1))
    st[live] += np.clip(d, 0.8, 16)
    live = live[(sh[live] > 0.01) & (st[live] < 160)]

# ambient occlusion, iq style
ao = np.zeros(len(idx), np.float32)
for i, h in enumerate([1.5, 3.5, 7, 12, 20]):
    ao += (h - map_scene(hp + nor * h)) / h * (0.6 ** i)
ao = np.clip(1 - 0.42 * ao, 0, 1)

conf_v = trilinear(conf, mq @ R)
dif = np.clip((nor * lig).sum(1), 0, 1) * sh
fre = np.clip(1 + (nor * rd[idx]).sum(1), 0, 1) ** 3
rf = rd[idx] - 2 * (rd[idx] * nor).sum(1, keepdims=True) * nor
spe = np.clip((rf * lig).sum(1), 0, 1) ** 40 * sh


def pal(tt, a, b, c, d):
    return a + b * np.cos(6.28318 * (c * tt[..., None] + d))


# iq cosine palette running with depth and the real pLDDT, so the far lattice burns through a colour cycle
tt = 0.08 + t[idx] * 0.0009 + 0.34 * (1 - conf_v)
alb = pal(tt, np.array([.62, .38, .30]), np.array([.55, .42, .50]), np.array([1, 1, 1.0]), np.array([.02, .12, .30]))
alb = np.clip(alb, 0, 1.4)
alb = np.where((ids == 1)[:, None], np.array([3.0, 6.0, 8.0]), alb)
alb = np.where((ids == 2)[:, None], np.array([2.6, 2.4, 2.0]), alb)
sky = np.array([0.32, 0.55, 1.0], np.float32)
amb = (0.5 + 0.5 * nor[:, 1:2]) * ao[:, None] * sky * 0.55
c = alb * (dif[:, None] * np.array([1.9, 1.55, 1.1]) + amb)
c += fre[:, None] * ao[:, None] * np.array([1.2, 0.5, 1.6]) * 0.7
c += spe[:, None] * 1.3
# the title is a gradient logo: hard cyan to white to hot pink across its height
gy = np.clip(((hp - TPOS) @ TR)[:, 1] / 9.0 * 0.5 + 0.5, 0, 1)[:, None]
grad = (np.array([1.0, 0.1, 0.45]) * (1 - gy) ** 1.4 * 1.9 + np.array([1.5, 1.45, 1.3]) * np.exp(-((gy - 0.52) / 0.12) ** 2) * 1.4 + np.array([0.1, 0.8, 1.0]) * gy ** 1.2 * 1.6)
faceon = np.clip((-nor * rd[idx]).sum(1, keepdims=True), 0, 1)
c = np.where((ids == 2)[:, None], grad * (0.35 + 0.8 * faceon ** 3), c)

col[idx] = c
# distance fog into a hot two colour sky
bgv = np.clip(0.5 + 0.5 * rd[:, 1], 0, 1)
bg = (1 - bgv[:, None]) * np.array([0.26, 0.04, 0.16]) + bgv[:, None] * np.array([0.01, 0.01, 0.07])
sun = np.clip((rd * lig).sum(1), 0, 1)
bg = bg + (sun[:, None] ** 24) * np.array([1.0, 0.45, 0.2]) * 0.25
fog = 1 - np.exp(-(t / 430) ** 1.5)
col = col * (1 - fog[:, None]) + bg * fog[:, None]
col = np.where(hit[:, None], col, bg)
# step-count glow, the signature of these shaders
col += glow[:, None] * np.array([0.18, 0.75, 1.0]) * 0.6
col += glow2[:, None] * np.array([1.0, 0.22, 0.55]) * 0.8
col += (steps / 170)[:, None] ** 2 * np.array([0.25, 0.1, 0.5]) * 0.5

img = col.reshape(H, W, 3)
img = img / (1 + 0.25 * img)
img = np.clip(img, 0, 1) ** (1 / 2.2)
img = img * img * (3 - 2 * img) * 0.35 + img * 0.65
vig = 1 - 0.34 * ((px / 1.78) ** 2 + py ** 2)
img = img * vig[..., None]
im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
if S != 1.0 and S > 1.0:
    im = im.resize((1280, 720), Image.LANCZOS)
d = ImageDraw.Draw(im)
s = im.size[0] / 1280
f = ImageFont.truetype(FONTS + "/consolab.ttf", int(21 * s))
d.text((int(30 * s), int(672 * s)), LABEL, font=f, fill=(255, 245, 225))
im.save(OUT / ("e1_raymarch.png" if S >= 1 else "_e1_test.png"))
print("saved")
