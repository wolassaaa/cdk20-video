"""HKBU SCIE1007 coursework science video, dawn art direction. T4 comp: colours the white-light layers. Low pLDDT goes into the mist, so what is uncertain is not sharply seen.
python comp_t4.py <prefix> <out.png> [scale]   prefix e.g. ../_work/T4/T4
"""
import sys
import numpy as np
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
sun, skl, dat = load(pre + "_sun.npy"), load(pre + "_sky.npy"), load(pre + "_data.npy")
h, w = sun.shape[:2]
al = np.clip(dat[..., 3], 0, 1)
safe = np.maximum(al, 1e-4)[..., None]
dist, z, conf = (dat[..., :3] / safe).transpose(2, 0, 1)
dist = dist * 20; z = z * 20
hy = int(HY * h / H)

bg = sky("S4", w, h, hy, seed=5, clouds=.3, stars=.12)
SUN = hex2lin("4FA2FF") * 5.2
FILL = hex2lin("0E2A6E") * .42
raw = sun[..., :3] / np.maximum(sun[..., 3:], 1e-4)
crisp = sm(.04, .34, raw) ** 1.2 * .62 + raw * .38      # the light lands on rock, not on cotton: a hard terminator, then a falloff
surf = crisp * SUN + skl[..., :3] / np.maximum(skl[..., 3:], 1e-4) * FILL

# aerial perspective: the far ridges take a little of the sky behind them, near rock stays darker than the sky
valid = al > .5
d0, d1 = np.percentile(dist[valid], 3), np.percentile(dist[valid], 97)
fog = (1 - np.exp(-np.clip((dist - d0) / (d1 - d0), 0, 2) * 1.2))[..., None]
yy = np.arange(h, dtype=np.float32)[:, None]
fogcol = hex2lin("15408F")
surf = surf * (1 - fog * .6) + fogcol * fog * .6

# real pLDDT: where the model is unsure, it is out of focus. Same surface, same place, only soft, so doubt is never drawn sharp
unsure = (1 - sm(.46, .68, conf))
pad = 40
def soft(a, s):
    return blur(np.pad(a, ((pad, pad), (pad, pad), (0, 0))), s)[pad:-pad, pad:-pad]
A_s = (al * unsure)[..., None]
A_c = (al * (1 - unsure))
sharp = surf * A_c[..., None]
ghost, ghost_a = soft(surf * A_s, 9) * .5, soft(A_s, 9)
lit = bloom(sharp, sig=(3, 12, 50), wt=(.34, .22, .14), thr=.25) - sharp
img = bg * (1 - ghost_a * .7) + ghost * .7
img = sharp + img * (1 - A_c[..., None])

# mist at camera height: the body rises out of it. Brighter than the land, as real valley fog is
n = fbm(21, 300, 10, 5, w, h)
top = hy + n * 7 * h / 1080
below = sm(-10, 12, yy - top)
tex = sm(-1.6, 1.6, fbm(22, 240, 9, 5, w, h))
fall = sm(hy, hy + 300 * h / 1080, yy)
sea = (hex2lin("2257AE") * (1 - fall[..., None]) + hex2lin("061440") * fall[..., None]) * (.6 + .55 * tex[..., None])
k = below[..., None]
img = img * (1 - k) + sea * k
lit = lit * (1 - k)

# black near ridge along the bottom, the ground we stand on
rn = fbm(33, 260, 1, 4, w, 1)[0]
ridge = h - (64 + 26 * rn + 110 * np.linspace(1, 0, w) ** 3) * h / 1080
land = np.clip((yy - ridge[None, :]) / 2.0, 0, 1)[..., None]
img = img * (1 - land) + hex2lin(SKY["S4"]["land"]) * land
lit = lit * (1 - land)

save(img + lit, out)
