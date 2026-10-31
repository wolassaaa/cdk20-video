"""HKBU SCIE1007 coursework science video. Style scout g8: an oscilloscope in X-Y mode. One beam, one line: the real backbone, residue 1 to 346, drawn once and left to fade on the phosphor while it turns. Beam brightness follows speed, as on real tube. The strip below is the real per-residue confidence."""
from glib import *

A = atoms()
ca = A["xyz"][A["name"] == "CA"]
cf = A["conf"][A["name"] == "CA"]
ca = ca - ca.mean(0)
SS = 2
w2, h2 = W * SS, H * SS


def catmull(p, sub=14):
    """Smooth path through the real C-alpha positions."""
    P = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    t = np.linspace(0, 1, sub, endpoint=False, dtype=np.float32)[None, :, None]
    p0, p1, p2, p3 = P[:-3, None], P[1:-2, None], P[2:-1, None], P[3:, None]
    q = .5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    return q.reshape(-1, p.shape[1])


PATH = catmull(ca, 16)
CF = np.repeat(cf[:-1], 16)


def beam(buf, x, y, gain):
    """Deposit energy along the path. Slow beam burns brighter, fast beam thins out."""
    dx = np.diff(x, append=x[-1]); dy = np.diff(y, append=y[-1])
    sp = np.sqrt(dx * dx + dy * dy) + 1.2
    e = gain / sp
    n = np.clip(sp.astype(np.int32) + 1, 1, 40)
    i = np.repeat(np.arange(len(x)), n)
    fr = np.concatenate([np.arange(k) / k for k in n]).astype(np.float32)
    px = x[i] + dx[i] * fr; py = y[i] + dy[i] * fr
    w = e[i] / n[i] * sp[i]
    ix = px.astype(np.int32); iy = py.astype(np.int32)
    g = (ix >= 0) & (ix < w2) & (iy >= 0) & (iy < h2)
    buf += np.bincount(iy[g] * w2 + ix[g], weights=w[g], minlength=w2 * h2).reshape(h2, w2)


SC = 12.6; cx, cy = 868, 302
scr = np.zeros((h2, w2), np.float64)
fresh = np.zeros((h2, w2), np.float64)
N = 120
for k in range(N):  # the phosphor still holds the last turns: older sweeps are dimmer
    ang = -1.5 * (N - 1 - k)
    R = rot(10 + 8 * np.sin(k * .05), ang, 0) @ rot(-70, 20, 0)
    V = PATH @ R.T
    persp = 1 + V[:, 2] / 240
    x = (cx + V[:, 0] * SC * persp) * SS; y = (cy - V[:, 1] * SC * persp) * SS
    dim = .05 + .34 * (k / (N - 1)) ** 6
    beam(scr, x, y, 3.2 * dim * (.5 + V[:, 2] / 90).clip(.12, 1.3))
    if k == N - 1:
        beam(fresh, x, y, 8.5)

# the time base: real pLDDT, residue 1 at left. Below 0.7 is the tail
tb = np.zeros((h2, w2), np.float64)
x0, x1 = 64, 1216
xs = np.linspace(x0, x1, len(cf) * 8, dtype=np.float32) * SS
vals = np.interp(np.linspace(0, len(cf) - 1, len(cf) * 8), np.arange(len(cf)), cf)
ys = (706 - (vals - .2) * 118).astype(np.float32) * SS
beam(tb, xs, ys, 4.0)


def dn(a): return a.reshape(H, SS, W, SS).mean((1, 3)).astype(np.float32)


scr, fresh, tb = dn(scr), dn(fresh), dn(tb)

# graticule etched on the faceplate, it does not glow itself, edge lit only
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
gx, gy = 128, 72
grid = ((np.abs((xx + gx / 2) % gx - gx / 2) < .7) | (np.abs((yy + gy / 2) % gy - gy / 2) < .7)).astype(np.float32)
tick = ((np.abs(xx - 640) < 5) & (np.abs((yy + 7.2) % 14.4 - 7.2) < .6)) | ((np.abs(yy - 360) < 5) & (np.abs((xx + 12.8) % 25.6 - 12.8) < .6))
grid = np.maximum(grid, tick.astype(np.float32))

e = scr * 1.0 + fresh * 1.0 + tb
core = np.clip(gblur(e, .75) * 1.6, 0, 1.6)
halo1 = gblur(e, 3.2) * 2.2
halo2 = gblur(e, 16) * 2.4
# phosphor: P31 green, the core clips to near white the way a hot trace does
G = np.array([.13, 1.0, .36], np.float32)
W_ = np.array([.86, 1.0, .9], np.float32)
rgb = G * (core[..., None] * .75 + halo1[..., None] * .62 + halo2[..., None] * .26)
hot = np.clip(gblur(fresh + tb, .7) * 2.2 - .35, 0, 1)
rgb = rgb * (1 - hot[..., None]) + W_ * hot[..., None]

# title in the beam's own hand: single stroke, one continuous pass with the retrace left in


def stroke(pts, scale, ox, oy):
    a = np.array(pts, np.float32)
    return a * scale + np.array([ox, oy], np.float32)


GLY = {
    "C": [(1, .18), (.8, .04), (.5, 0), (.2, .05), (.03, .3), (0, .5), (.03, .7), (.2, .95), (.5, 1), (.8, .96), (1, .82)],
    "D": [(0, 1), (0, 0), (.42, 0), (.75, .08), (.95, .3), (1, .5), (.95, .7), (.75, .92), (.42, 1), (0, 1)],
    "K": [(0, 0), (0, 1), (0, .58), (.95, 0), (.3, .4), (1, 1)],
    "2": [(.03, .25), (.15, .07), (.45, 0), (.78, .05), (.93, .25), (.85, .48), (.5, .7), (0, 1), (1, 1)],
    "0": [(.5, 0), (.15, .1), (0, .5), (.15, .9), (.5, 1), (.85, .9), (1, .5), (.85, .1), (.5, 0)],
}
title = np.zeros((h2, w2), np.float64); retr = np.zeros((h2, w2), np.float64)
ox = 54; oy = 44; sz = 126; adv = 110
last = None
for i, ch in enumerate("CDK20"):
    p = stroke(GLY[ch], 1, 0, 0) * np.array([sz * .72, sz], np.float32) + np.array([ox + i * adv * 1.0, oy], np.float32)
    # densify and round the corners a little, deflection plates cannot stop dead
    q = catmull(p, 10)
    q = np.vstack([p[0], q])
    if last is not None:
        beam(retr, np.linspace(last[0], q[0, 0], 40, dtype=np.float32) * SS, np.linspace(last[1], q[0, 1], 40, dtype=np.float32) * SS, 1.0)
    for rep in range(5):
        beam(title, (q[:, 0] + (rep - 2) * .9) * SS, (q[:, 1] + (rep - 2) * .9) * SS, 7.0)
    last = q[-1]
title = dn(title); retr = dn(retr)
te = gblur(title, 1.0)
rgb = rgb + G * (gblur(title, 3.5)[..., None] * 5 + gblur(title, 20)[..., None] * 3.4)
rgb = rgb + G * gblur(retr, .8)[..., None] * .7
hot = np.clip(te * 2.6 - .1, 0, 1)
rgb = rgb * (1 - hot[..., None]) + W_ * hot[..., None]

# graticule lit from the edge, a little brighter near the trace
gl = gblur(e, 40) * 2.2 + .045
rgb = rgb + grid[..., None] * gl[..., None] * np.array([.5, .8, .6], np.float32) * .9

tag = text_mask(LABEL, font("consola.ttf", 25), (64, 572), "ls")
rgb = rgb + gblur(tag, 3)[..., None] * G * .5
rgb = over(rgb, W_, tag)
small = text_mask("pLDDT, residue 1 → 346", font("consola.ttf", 19), (64, 600), "ls")
rgb = over(rgb, (.45, .95, .58), small * .85)

# tube glass: dark tint, rounded corners cut by the bezel, gentle barrel falloff
u = (xx - 640) / 640; v = (yy - 360) / 360
r = (np.abs(u) ** 5 + np.abs(v) ** 5) ** (1 / 5)
vig = np.clip(1.16 - r ** 3 * .62, 0, 1)
rgb = rgb * vig[..., None] + np.array([.012, .03, .02], np.float32)
bezel = np.clip((r - 1.005) * 40, 0, 1)
rgb = rgb * (1 - bezel[..., None])
save(rgb, "g8_oscilloscope.png")
