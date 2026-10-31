"""HKBU SCIE1007 coursework science video, dawn art direction. T5 comp: looking out of the pocket at the first burn on the horizon, with 048 between us and it.
python comp_t5.py <prefix> <out.png> [burn 0..1]
"""
import sys
import numpy as np
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
BURN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
sun, skl, fil = load(pre + "_sun.npy"), load(pre + "_sky.npy"), load(pre + "_fill.npy")
h, w = sun.shape[:2]
hy = int(HY * h / H)
yy = np.arange(h, dtype=np.float32)[:, None]
al = np.clip(sun[..., 3], 0, 1)[..., None]
lig_a = np.clip(fil[..., 3], 0, 1)[..., None]
safe = np.maximum(al, 1e-4)

bg = sky("S5", w, h, hy, seed=23, clouds=.4, stars=.22)
rn = fbm(61, 200, 1, 4, w, 1)[0]
crest = hy + (2 + 5 * rn) * h / 1080
land = np.clip((yy - crest[None, :]) / 1.2, 0, 1)[..., None]
bg = bg * (1 - land) + hex2lin(SKY["S5"]["land"]) * land

SUN = hex2lin("FF3A14") * 1.0
FILL = hex2lin("1A1652") * .62
s1 = np.clip(sun[..., :3] / safe, 0, None)
rock = sm(.26, 1.0, s1) ** 1.3 * SUN * 2.2 + skl[..., :3] / safe * FILL
# the walls fall to black away from the opening, and the ground under the horizon stays clear for the words
rock = rock * (.16 + .84 * (1 - sm(hy + 10, hy + 170, yy))[..., None])
xi = np.arange(w, dtype=np.float32)[None, :]
vig = np.clip(1.25 - np.hypot((xi - 930) / 980, (yy - 660) / 620), 0, 1)
rock = rock * sm(.0, .5, vig)[..., None]
rock_a = al.copy()
rock_a[:, 1560:] = 1.0      # a second gap in the wall at the frame edge read as a glitch; it stays closed, the opening is the only sky
rock[:, 1560:] = rock[:, 1560:] * al[:, 1560:]
img = rock * rock_a + bg * (1 - rock_a)

# 048: bone, the only warm pale thing in the frame, lit from our side so its atoms read against the burn
lig = fil[..., :3] / np.maximum(lig_a, 1e-4) * hex2lin("F3EFE6") * 2.3 + s1 * SUN * .55 + skl[..., :3] / safe * FILL * .35
img = img * (1 - lig_a) + lig * lig_a

img = bloom(img, sig=(4, 18, 70), wt=(.2, .16, .14), thr=.4)
save(img, out)
