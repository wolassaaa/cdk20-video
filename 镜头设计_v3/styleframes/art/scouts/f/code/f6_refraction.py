"""HKBU SCIE1007 coursework science video. Style scout f6: prismatic refraction, high key. The frame is a pale pearl wall of thin film; the real CDK20 is a dark prism hanging in it, bending the veils and splitting light at its edge.
Where pLDDT is high the surface is hard glass. Where it is low, real data, the glass gives way and melts into the wall."""
from fx import *

P = load(0.667)
mask, key, rim, ao, conf, nrm = (P[k][:H, :W] for k in ("mask", "key", "rim", "ao", "conf", "normal"))
yy, xx = np.mgrid[:H, :W].astype(np.float32)
cx, cy = 642.0, 330.0
sc_up = 1.14
sx = (xx - cx) / sc_up + cx
sy = (yy - 352.0) / sc_up + 352.0
mask = sample(mask, sx, sy)
key, rim, ao, conf = (sample(a, sx, sy) for a in (key, rim, ao, conf))
nrm = sample(nrm, sx, sy)
rad = np.hypot((xx - cx) * 0.8, yy - cy)


def film_c(t, order=1.0):
    r = 0.5 + 0.5 * np.cos(2 * np.pi * t / 0.65)
    g = 0.5 + 0.5 * np.cos(2 * np.pi * t / 0.53)
    b = 0.5 + 0.5 * np.cos(2 * np.pi * t / 0.45)
    return np.stack([r, g, b], -1) ** order


# the wall: curtains of film, tall and slow, like oil running down a pane. Noise is stretched vertically then warped
n = noise_raw((H, W), 3.0, 41)
n = np.swapaxes(box_x(np.swapaxes(n, 0, 1), 260), 0, 1)
n = (n - n.mean()) / n.std()
wx = noise_raw((H, W), 3.6, 42)
wy = noise_raw((H, W), 3.6, 43)
fine = noise_raw((H, W), 2.2, 44)
fine = np.swapaxes(box_x(np.swapaxes(fine, 0, 1), 120), 0, 1)
fine = (fine - fine.mean()) / fine.std()


def wall(x, y):
    u = x + 62 * sample(wx, x, y)
    v = y + 62 * sample(wy, x, y)
    t = 1.08 + 0.17 * sample(n, u, v) + 0.03 * sample(fine, u, v) + 0.00018 * (x - 640)
    c = film_c(t, 1.1)
    return c


# the object lenses the wall around it: everything near it is pushed along the gradient of its soft shadow
soft = gauss(mask, 34)
gy, gx = np.gradient(soft)
lens = 460.0
base = wall(xx - gx * lens, yy - gy * lens)
pearl = rgb("#F4EFE9")
bg = pearl * 0.74 + base * 0.34
# prismatic halo: a spectrum wrapped round the silhouette, strongest just outside the edge
halo_t = 0.92 + 1.1 * gauss(mask, 15) + 0.35 * soft
halo = film_c(halo_t, 1.5)
hw = smooth(0.0, 0.42, gauss(mask, 26)) * (1 - mask)
bg = mix(bg, halo, hw * 0.88)

# refraction with dispersion through the object
BANDS = 11
lam = np.linspace(0, 1, BANDS)
spec = np.stack([np.clip(1.5 - np.abs(lam - 0.05) * 3.6, 0, 1), np.clip(1.5 - np.abs(lam - 0.5) * 3.6, 0, 1), np.clip(1.5 - np.abs(lam - 0.95) * 3.6, 0, 1)], -1)
spec = spec / spec.sum(0, keepdims=True)
acc = np.zeros((H, W, 3), np.float32)
nx, ny = nrm[..., 0], nrm[..., 1]
ndv = np.clip(-nrm[..., 2], 0, 1)  # in the shared pass, surfaces facing the lens have negative z
for i in range(BANDS):
    k = 70 + 130 * lam[i]
    acc += sample(bg, xx - nx * k, yy + ny * k) * spec[i]

# Beer-Lambert: light dies crossing the thick middle, survives at the thin edges
absorb = np.exp(-3.3 * ndv ** 1.4)[..., None] * (rgb("#D8C8FF") ** 0.6)
fres = (1 - ndv) ** 3
oil = film_c(0.98 + 0.75 * ndv + 0.3 * nx + 0.22 * ny, 2.2)
glass = acc * absorb * 1.0
glass = glass + oil * (0.05 + 0.8 * (0.16 + key) * ao ** 1.3)[..., None] * 1.25
glass = glass + film_c(1.05 + 1.1 * fres, 1.3) * (fres ** 1.1)[..., None] * 1.05
glass = glass + (key ** 30 * ao)[..., None] * 1.3 + (rim ** 26 * ao)[..., None] * rgb("#FFEFFF") * 0.8
glass = glass * (0.2 + 0.8 * ao ** 1.3)[..., None]

# low confidence: the prism stops being a prism and the wall comes through
solid = smooth(0.48, 0.74, conf + 0.05 * sample(wx, xx, yy))
alpha = mask * (0.14 + 0.86 * solid)
img = bg * (1 - alpha)[..., None] + glass * alpha[..., None]
# thin rainbow line traced where the melt begins
melt = np.exp(-((conf - 0.61) / 0.03) ** 2) * mask
img = mix(img, film_c(1.2 + 3 * conf, 1.2), melt * 0.5)

# the whole frame is printed through a weak prism
out = np.zeros_like(img)
for c, k in enumerate((-1.0, 0.0, 1.0)):
    f_ = 1 + k * 0.007 * smooth(150, 780, rad)
    out[..., c] = sample(img[..., c], (xx - cx) * f_ + cx, (yy - cy) * f_ + cy)
img = out

# title: ink on pearl. Each colour plate lands in a different place, so the black splits into a spectrum at its edges
f = font("segoeuil.ttf", 170)
t = "CDK20"
tr = 42
tw = text_width(t, f, tr)
tx, ty = (W - tw) / 2, 672
plate = pearl * 0
OFF = 10
for c, k in enumerate((-1.0, 0.0, 1.0)):
    m = text_mask(t, f, (tx + k * OFF, ty + k * OFF * 0.2), tr)
    img[..., c] = img[..., c] * (1 - 0.97 * m)
lab = font("segoeui.ttf", 23)
lw = text_width(LABEL, lab, 1.0)
lm = text_mask(LABEL, lab, ((W - lw) / 2, 708), 1.0)
img = mix(img, rgb("#17121F"), lm)
img = img + gauss(np.clip(img - 0.85, 0, 2), 8) * 0.3
save(img, OUT / "f6_refraction.png")
print("ok")
