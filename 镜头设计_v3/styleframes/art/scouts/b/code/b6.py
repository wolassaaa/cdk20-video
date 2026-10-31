"""HKBU SCIE1007 coursework science video. Style scout b6: the real CDK20 surface points stay sharp on the left and are carried off into a liquid flow on the right. Colour is the real confidence score."""
import numpy as np

from common import *

D = np.load(SURFACE)
vt, cf = D["verts"] * 0.1, D["conf"]
rng = np.random.default_rng(1)

# same camera as the shared scene
VIEW = np.array([0.15, -0.25, 1.0])
VIEW /= np.linalg.norm(VIEW)
c = (vt.min(0) + vt.max(0)) / 2
fwd = -VIEW
right = np.cross(fwd, [0, 1, 0])
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
rel = vt - (c + VIEW * 26)
zc = rel @ fwd
ZOOM = 1.34
f = 70 / 36 * W * ZOOM
px = (rel @ right) / zc * f + 470
py = -(rel @ up) / zc * f + 322

# front-facing points only, lit once from the upper left so the form survives in the point cloud
L = np.array([-0.6, 0.55, 0.58])
L /= np.linalg.norm(L)
# per-point normals from quads
q = D["quads"]
a, b, d = vt[q[:, 0]], vt[q[:, 1]], vt[q[:, 3]]
fn = np.cross(b - a, d - a)
n = np.zeros_like(vt)
for j in range(4):
    np.add.at(n, q[:, j], fn)
n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
sign = np.sign(np.median((n * (vt - c)).sum(1)))
n = n * sign
face = -(n @ fwd)
keep = face > 0.0
lam = np.clip(n @ L, 0, 1) ** 1.2 * 0.9 + 0.1
ids = rng.choice(np.where(keep)[0], 900_000, p=None)
x0 = px[ids] + rng.normal(0, 0.5, ids.size)
y0 = py[ids] + rng.normal(0, 0.5, ids.size)
conf = cf[ids]
light = lam[ids] * (0.3 + 0.7 * face[ids] ** 0.5)
zz = zc[ids]


def psi_vel(x, y, t):
    """Velocity from a stream function, three octaves with domain warp, so the flow folds like poured paint."""
    wx = x + 60 * np.sin(y * 0.0071 + 1.3) + 26 * np.sin(y * 0.021 + x * 0.006)
    wy = y + 60 * np.sin(x * 0.0059 - 0.7) + 26 * np.sin(x * 0.019 - y * 0.008)
    e = 1.5
    def s(a, b):
        return (np.sin(a * 0.0052 + 0.8 * np.sin(b * 0.0031)) * np.cos(b * 0.0067) * 170
                + np.sin(a * 0.0131 + b * 0.0071 + 2.0) * 62
                + np.sin(a * 0.031 - b * 0.023 + 0.4) * 19)
    dy = (s(wx, wy + e) - s(wx, wy - e)) / (2 * e)
    dx = (s(wx + e, wy) - s(wx - e, wy)) / (2 * e)
    return dy, -dx


STEPS = 56
acc = np.zeros((H, W, 3), np.float64)
lo = sstep(0.45, 0.9, conf)
# confidence ramp: cold machine blue when confident, hot in the tail
stops = [(0.0, "#ff2a00"), (0.34, "#ff7a00"), (0.62, "#e8007a"), (0.8, "#2030ff"), (1.0, "#21d4ff")]
col = lin(np.stack([np.interp(conf, [p for p, _ in stops], hexc_ch) for hexc_ch in np.stack([hexc(s) for _, s in stops], 1)], 1)).astype(np.float32)
x, y = x0.copy(), y0.copy()
wave = (x0 - 300) / 820 + 0.22 * (y0 / 720 - 0.5)
gate = sstep(0.34, 0.78, wave + 0.26 * ((1 - conf) * 2 - 0.3))
STEPS = 150
for s in range(STEPS):
    k = s / (STEPS - 1)
    vx, vy = psi_vel(x, y, k)
    sp = gate * (0.25 + 1.5 * k)
    x = x + (vx * 2.7 + 2.1) * sp
    y = y + (vy * 2.7 + 0.2) * sp
    if s == 0 or s >= STEPS - 7:  # draw the sheet where it ends up, not its trail, so the folds stay crisp
        ix, iy = x.astype(np.int32), y.astype(np.int32)
        ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
        idx = iy[ok] * W + ix[ok]
        late = 1.0 if s else 0.0
        w = light[ok] * (gate[ok] * late * 0.55 + (1 - gate[ok]) * (1 if s == 0 else 0) * 3.4 + (1 - late) * gate[ok] * 0.18)
        for ch in range(3):
            acc[..., ch] += np.bincount(idx, weights=w * col[ok, ch], minlength=W * H).reshape(H, W)

# log tone map keeps the filaments, then one soft bloom
acc = acc.astype(np.float32)
lum = acc.sum(-1, keepdims=True)
img = acc / np.maximum(lum, 1e-3) * (1 - np.exp(-lum * 0.16)) ** 0.8 * 1.3
img = img + blur(img, 9) * 0.28 + blur(img, 40) * 0.16
base = np.stack([hexc("#03040e")] * 1)[0]
rgb = lin(base) + img
rgb = to_srgb(rgb)
rgb = np.clip(rgb, 0, 1)

t = text("CDK20", "bahnschrift.ttf", 142, (46, 618), "lm", tracking=10)
glow = blur(t, 12)
rgb = np.clip(rgb * (1 - 0.7 * glow[..., None]) * (1 - 0.8 * blur(text(LABEL, "bahnschrift.ttf", 21, (52, 690), "lm", tracking=1.5), 7)[..., None] * 2).clip(0, 1), 0, 1)
rgb = over(rgb, hexc("#ffffff"), t)
lab = text(LABEL, "bahnschrift.ttf", 21, (52, 690), "lm", tracking=1.5)
rgb = over(rgb, hexc("#ffffff"), lab)
finish(rgb, "b6_data_sculpture.png")
