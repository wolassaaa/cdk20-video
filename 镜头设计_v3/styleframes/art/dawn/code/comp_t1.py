"""HKBU SCIE1007 coursework science video, dawn art direction. T1 comp: the real liver as a dusk hill under the last ember light.
On its dark face stand exactly 1,412 small lit windows, one for each death in the on-screen figure, because in this film a person is a lit window. They are placed by noise, the positions mean nothing.
python comp_t1.py <prefix> <out.png>
"""
import sys
import numpy as np
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
sun, skl, dat = load(pre + "_sun.npy"), load(pre + "_sky.npy"), load(pre + "_data.npy")
h, w = sun.shape[:2]
al = np.clip(dat[..., 3], 0, 1)
safe = np.maximum(al, 1e-4)[..., None]
dist, z, _ = (dat[..., :3] / safe).transpose(2, 0, 1)
hy = int(HY * h / H)
yy = np.arange(h, dtype=np.float32)[:, None]

bg = sky("S1", w, h, hy, seed=8, clouds=.5, stars=.05)
SUN = hex2lin("FF4E1E") * 4.0
FILL = hex2lin("3C2238") * .3
surf = sun[..., :3] / np.maximum(sun[..., 3:], 1e-4) * SUN + skl[..., :3] / np.maximum(skl[..., 3:], 1e-4) * FILL

# land under the horizon: a low dark foreground the hill stands behind
rn = fbm(41, 240, 1, 4, w, 1)[0]
crest = hy + (-6 + 12 * rn + 34 * np.linspace(0, 1, w) ** 2) * h / 1080
land = np.clip((yy - crest[None, :]) / 1.5, 0, 1)
gnd = hex2lin(SKY["S1"]["land"])[None, None] * (1 + 1.6 * (1 - sm(hy, hy + 110, yy)))[..., None]

img = surf * al[..., None] + bg * (1 - al[..., None])

# low haze where the hill meets the ground, picks up the ember from the horizon
haze = sm(hy - 130, hy + 6, yy)[..., None] * .55
img = img * (1 - haze * al[..., None]) + hex2lin("7A3236") * haze * al[..., None]

# exactly 1,412 windows: dark face of the hill only, clustered like settlements, never two in one spot
r = np.random.default_rng(1412)
dark = (al > .98) & (sun[..., 0] / safe[..., 0] < .004) & ((yy - crest[None, :]) < -4)
dens = .22 + sm(-.6, 1.6, fbm(77, 70, 40, 4, w, h)) ** 2
ys, xs = np.nonzero(dark)
p = dens[ys, xs] + 1e-3
p /= p.sum()
pick = r.choice(len(ys), 16000, replace=False, p=p)
mind = 2.4
grid, kept = {}, []
for i in pick:
    x, y = xs[i], ys[i]
    cx, cy = int(x // mind), int(y // mind)
    if any((cx + a, cy + b) in grid for a in (-1, 0, 1) for b in (-1, 0, 1)):
        continue
    grid[(cx, cy)] = 1
    kept.append((x, y))
    if len(kept) == 1412:
        break
assert len(kept) == 1412, len(kept)
glow = np.zeros((h, w, 3), np.float32)
warm = [hex2lin("FFC070"), hex2lin("FFD9A0"), hex2lin("FF9A4A")]
for x, y in kept:
    c = warm[r.integers(0, 3)] * (0.5 + r.random() * .9)
    glow[y, x] += c
    if r.random() < .5:
        glow[y, min(x + 1, w - 1)] += c * .7
img = img * (1 - land[..., None]) + gnd * land[..., None]
img += glow * (1 - land[..., None])
img += blur(np.pad(glow, ((30, 30), (30, 30), (0, 0))), 1.6)[30:-30, 30:-30] * 2.2 * (1 - land[..., None])

img = bloom(img, sig=(3, 14, 60), wt=(.12, .1, .08), thr=.5)
save(img, out)
print("windows", len(kept))
