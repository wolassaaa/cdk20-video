"""HKBU SCIE1007 coursework science video. Style scout b7: a wall of falling light lines. Water runs over the real CDK20 surface and around the name, so both exist only because the flow parts for them."""
import numpy as np

from common import *

P = load()
V = view(P, zoom=1.38, at=(640, 300), src=(950, 545))
y, x = grid()
m = V["mask"]
hard = m > 0.5
n = V["normal"].copy()
n = n * np.array([1, 1, 0.5], np.float32)
n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-4)

# the name is an obstacle too: a rounded height field cut from the letters
t = text("CDK20", "ariblk.ttf", 232, (640, 574), "mm", tracking=18)
tb = blur(t, 5)
gy, gx = np.gradient(tb)
tn = np.stack([-gx * 16, gy * 16, np.ones_like(gx)], -1)
tn = tn / np.linalg.norm(tn, axis=-1, keepdims=True)

# slope field: gravity projected on to the surface, in image space y grows downward
g = np.array([0, -1, 0], np.float32)
N = n
dot = (N * g).sum(-1, keepdims=True)
tang = g - dot * N
vx0, vy0 = tang[..., 0], -tang[..., 1]
outside = ~hard
# in free air lines fall nearly straight, with a slow wander
wander = (noise(11, 260, slope=2.2) - 0.5) * 0.9
vx = np.where(outside, wander, vx0)
vy = np.where(outside, 1.0, np.maximum(vy0, 0.04))
vx = blur(vx.astype(np.float32), 1.4)
vy = blur(vy.astype(np.float32), 1.4)
speed = np.maximum(np.hypot(vx, vy), 0.05)
vx, vy = vx / speed, vy / speed
shade = np.clip(0.2 + 0.95 * V["key"] + 0.85 * V["rim"], 0, 1.3) * (0.3 + 0.7 * V["ao"])
shade = np.where(hard, shade, 0.85)
confv = np.where(hard, V["conf"], 1.0)

rng = np.random.default_rng(2)
NL, STEPS = 3400, 1300
px = rng.uniform(-40, W + 40, NL).astype(np.float32)
py = rng.uniform(-30, 0, NL).astype(np.float32)
# a second population starts on the protein, so its surface is drawn densely and the free curtain stays thin
extra = 9000
ys, xs = np.where(hard)
pick = rng.integers(0, ys.size, extra)
px = np.concatenate([px, xs[pick].astype(np.float32)])
py = np.concatenate([py, ys[pick].astype(np.float32)])
life = np.concatenate([np.full(NL, STEPS), rng.integers(40, 160, extra)])
name = 3600
ty, tx = np.where(t > 0.5)
pk = rng.integers(0, ty.size, name)
base = px.size
px = np.concatenate([px, tx[pk].astype(np.float32)])
py = np.concatenate([py, ty[pk].astype(np.float32)])
life = np.concatenate([life, rng.integers(60, 200, name)])
u = rng.random(px.size).astype(np.float32)
gain = 0.05 + 0.95 * u ** 7                # most lines are haze, a few burn
gain[NL:base] = 0.16 + 0.84 * u[NL:base] ** 3
gain[base:] = 0.5 + 0.5 * u[base:]
cool = np.zeros((H, W), np.float64)
nm = np.zeros((H, W), np.float64)
warm = np.zeros((H, W), np.float64)
air = np.where(hard, 1.0, 0.34)
for s in range(STEPS):
    live = s < life
    ix = np.clip(px.astype(np.int32), 0, W - 1)
    iy = np.clip(py.astype(np.int32), 0, H - 1)
    ok = live & (px >= 0) & (px < W) & (py >= 0) & (py < H)
    if ok.any():
        idx = iy[ok] * W + ix[ok]
        w = gain[ok] * shade[iy[ok], ix[ok]] * air[iy[ok], ix[ok]]
        lowc = confv[iy[ok], ix[ok]] < 0.7
        isname = np.arange(px.size)[ok] >= base
        inl = t[iy[ok], ix[ok]] > 0.5
        keepn = isname & inl
        nm += np.bincount(idx[keepn], weights=gain[ok][keepn], minlength=W * H).reshape(H, W)
        w = w * ~isname
        cool += np.bincount(idx[~lowc], weights=w[~lowc], minlength=W * H).reshape(H, W)
        warm += np.bincount(idx[lowc], weights=w[lowc], minlength=W * H).reshape(H, W)
    sx, sy = vx[iy, ix], vy[iy, ix]
    px = px + sx * 0.92
    py = py + sy * 0.92

cool, warm = cool.astype(np.float32), warm.astype(np.float32)


def tone(a, gain_):
    return 1 - np.exp(-a * gain_)


bgc = ramp(y / H, [(0, "#000a2a"), (0.6, "#010a24"), (1, "#000614")])
c1 = tone(blur(cool, 0.5), 0.75)
c2 = tone(blur(cool, 3.2), 0.42)
w1 = tone(blur(warm, 0.5), 0.8)
w2 = tone(blur(warm, 3.2), 0.5)
rgb = lin(bgc)
rgb = rgb + c2[..., None] * lin(hexc("#0a3cff")) * 0.9 + c1[..., None] * lin(hexc("#7ed8ff")) * 1.1 + c1[..., None] ** 3 * 0.9
rgb = rgb + w2[..., None] * lin(hexc("#ff1a50")) * 0.8 + w1[..., None] * lin(hexc("#ff9a50")) * 1.1 + w1[..., None] ** 3 * 0.5
rgb = rgb * (1 - 0.82 * blur(t, 2.2)[..., None])
n1 = tone(blur(nm.astype(np.float32), 0.5), 1.1)
rgb = rgb + (n1 * t)[..., None] * lin(hexc("#ffffff")) * 1.4 + blur(n1 * t, 5)[..., None] * lin(hexc("#3a8cff")) * 0.9
rgb = to_srgb(rgb)
lab = text(LABEL, "bahnschrift.ttf", 21, (640, 698), "mm", tracking=2)
halo = blur(lab, 6)
rgb = np.clip(rgb * (1 - np.clip(halo * 2.4, 0, 0.92))[..., None], 0, 1)
rgb = over(rgb, hexc("#ffffff"), lab)
finish(rgb, "b7_flowing_light.png")
