"""HKBU SCIE1007 coursework science video. Style scout g5: an X-ray plate. The surface is summed as a thin shell, front and back, so edges pile up exactly as they do on film. Bonds and backbone are real, the white sparks are the model's ten real sulphur atoms."""
from glib import *

A = atoms()
Sf = surface()
D0 = np.load(SURF)
q = D0["quads"]
center = Sf["center"]
R = rot(12, 200, -8)
SC = 15.5; cx, cy = 700, 356
SS = 2
w2, h2 = W * SS, H * SS
Vs = (Sf["v"] - center) @ R.T
xs = (cx + Vs[:, 0] * SC) * SS; ys = (cy - Vs[:, 1] * SC) * SS

# thin shell: sample every quad, count hits per pixel. Tangent walls collect more hits by geometry alone
u = np.linspace(.08, .92, 6, dtype=np.float32)
uu, vv = np.meshgrid(u, u); uu = uu.ravel(); vv = vv.ravel()
buf = np.zeros(w2 * h2, np.float64)
for s in range(0, len(q), 40000):
    Q = q[s:s + 40000]
    x = np.outer(xs[Q[:, 0]], (1 - uu) * (1 - vv)) + np.outer(xs[Q[:, 1]], uu * (1 - vv)) + np.outer(xs[Q[:, 2]], uu * vv) + np.outer(xs[Q[:, 3]], (1 - uu) * vv)
    y = np.outer(ys[Q[:, 0]], (1 - uu) * (1 - vv)) + np.outer(ys[Q[:, 1]], uu * (1 - vv)) + np.outer(ys[Q[:, 2]], uu * vv) + np.outer(ys[Q[:, 3]], (1 - uu) * vv)
    ix = x.ravel().astype(np.int32); iy = y.ravel().astype(np.int32)
    g = (ix >= 0) & (ix < w2) & (iy >= 0) & (iy < h2)
    buf += np.bincount(iy[g] * w2 + ix[g], minlength=w2 * h2)
shell = buf.reshape(h2, w2).astype(np.float32)

# skeleton: real bonds from real distances, backbone heavier
V = (A["xyz"] - center) @ R.T
px = (cx + V[:, 0] * SC) * SS; py = (cy - V[:, 1] * SC) * SS
sk = Image.new("L", (w2, h2), 0); dr = ImageDraw.Draw(sk)
xyz = A["xyz"]
d2 = ((xyz[:, None] - xyz[None]) ** 2).sum(-1)
ii, jj = np.where((d2 < 1.95 ** 2) & (d2 > .1))
for i, j in zip(ii[ii < jj], jj[ii < jj]):
    dr.line((px[i], py[i], px[j], py[j]), fill=120, width=3)
bb = np.isin(A["name"], ["N", "CA", "C"])
idx = np.where(bb)[0]
for a, b in zip(idx[:-1], idx[1:]):
    if d2[a, b] < 1.95 ** 2:
        dr.line((px[a], py[a], px[b], py[b]), fill=255, width=9)
for i in np.where(A["el"] != "C")[0]:
    r = 3.2; dr.ellipse((px[i] - r, py[i] - r, px[i] + r, py[i] + r), fill=200)
sk = np.asarray(sk, np.float32) / 255

# sulphur at true proportion: a small dense point
sul = Image.new("L", (w2, h2), 0); dr = ImageDraw.Draw(sul)
for i in np.where(A["el"] == "S")[0]:
    r = .62 * SC * SS; dr.ellipse((px[i] - r, py[i] - r, px[i] + r, py[i] + r), fill=255)
sul = np.asarray(sul, np.float32) / 255


def dn(a): return a.reshape(H, SS, W, SS).mean((1, 3))


shell = dn(shell); sk = dn(sk); sul = dn(sul)
shell = gblur(shell, .55)
# film curve
dens = shell * .062 + sk * 1.5
T = np.clip(1 - np.exp(-np.clip(dens, 0, None)), 0, 1)
T = T ** 1.15
L = gblur(text_mask("CDK20", font("ariblk.ttf", 172), (30, 704), "ls", spacing=-3), .6)

base = np.array([.006, .022, .046], np.float32)
col_mid = np.array([.16, .48, .70], np.float32)
col_hi = np.array([.90, .97, 1.0], np.float32)
t = T[..., None]
rgb = base * (1 - t) ** 2 + col_mid * 2 * t * (1 - t) + col_hi * t ** 2
rgb = rgb + gblur(rgb, 22) * .08
s = sul[..., None]
rgb = rgb * (1 - s) + 1.15 * s
rgb = rgb + gblur(s, 7) * np.array([.35, .7, 1.0], np.float32) * .55

# light box falloff
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
v = 1 - .45 * (((xx - 700) / 900) ** 2 + ((yy - 360) / 560) ** 2)
rgb = rgb * np.clip(v, .4, 1)[..., None]

# lead markers sit on the plate: no ray passes, the flattest white in the frame
rgb = rgb * (1 - L[..., None]) + np.array([.96, .99, 1.0], np.float32) * L[..., None]

tag = text_mask(LABEL, font("consolab.ttf", 25), (W - 26, 702), "rs")
rgb = rgb * (1 - np.clip(gblur(tag, 5) * 2.2, 0, 1)[..., None] * .86)
rgb = over(rgb, (.90, .97, 1), tag)
save(rgb, "g5_xray.png")
