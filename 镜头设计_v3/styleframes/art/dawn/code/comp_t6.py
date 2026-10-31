"""HKBU SCIE1007 coursework science video, dawn art direction. T6 comp: the night road. Lamp layers are white light, so any number can be on and the film can switch them one by one without a render.
python comp_t6.py <prefix> <out.png> [lit: float 0..3]   lit = how many lamps are on, fractions fade the next one up
"""
import json, sys
import numpy as np
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
LIT = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
L = {k: load(f"{pre}_{k}.npy") for k in ("sky", "lamp0", "lamp1", "lamp2", "solid", "dash", "bulb", "data")}
px = json.load(open(pre + "_px.json"))
h, w = L["sky"].shape[:2]
hy = int(HY * h / H)
yy = np.arange(h, dtype=np.float32)[:, None]
al = np.clip(L["data"][..., 3], 0, 1)

bg = sky("S6", w, h, hy, seed=14, clouds=.5, stars=0)

# low far ridges, each a little closer to the sky colour, so the horizon stays a line and not a seam
for sd, amp, col in ((51, 26, "6E6880"), (52, 13, "57526A")):
    n = fbm(sd, 170, 1, 5, w, 1)[0]
    top = hy - (amp * (.6 + .4 * n)).clip(2) * h / 1080
    m = np.clip((yy - top[None, :]) / 1.2, 0, 1)[..., None]
    bg = bg * (1 - m) + hex2lin(col) * m

WARM = hex2lin("FFC27A") * 1.0
FILL = hex2lin("5E5A72") * 1.15
k = [np.clip(LIT - i, 0, 1) for i in range(3)]
surf = L["sky"][..., :3] * FILL * .85
for i in range(3):
    surf += L[f"lamp{i}"][..., :3] * WARM * 1.1 * k[i]

# aerial haze: the far ground melts into the band of sky over the horizon
dat = L["data"]
safe = np.maximum(al, 1e-4)
dist = dat[..., 0] / safe * 500
fog = (1 - np.exp(-np.clip(dist - 60, 0, None) / 300))[..., None] * .9
surf = surf * (1 - fog) + hex2lin("7E7690") * fog
surf = surf * al[..., None]
img = surf + bg * (1 - al[..., None])

# the line: solid and warm under the lit lamps, dashed and pale where nothing has been lit
img += L["solid"][..., :3] * hex2lin("FFD9A6") * .9 * min(1, LIT)
dm = np.clip(L["dash"][..., :1], 0, 1)
img = img * (1 - dm) + dm * hex2lin("C9C3D4") * .8

# bulbs
g = np.zeros((h, w), np.float32)
for i in range(3):
    t = px["st"][i]["top"]
    x, y = t[0] * w / 1920, t[1] * h / 1080
    sc = {0: 1.0, 1: .6, 2: .4}[i] * k[i]
    yi, xi = np.mgrid[0:h, 0:w]
    d2 = (xi - x) ** 2 + (yi - y) ** 2
    g += sc * (np.exp(-d2 / (2 * (9 * sc + 1e-3) ** 2)) * 3 + np.exp(-d2 / (2 * (60 * sc + 1e-3) ** 2)) * .34)
img += g[..., None] * hex2lin("FFD6A0")

# the 048 lantern, on the road at the door of the fourth station
dx, dy = px["door"]
yi, xi = np.mgrid[0:h, 0:w]
d2 = (xi - dx * w / 1920) ** 2 + (yi - dy * h / 1080) ** 2
img += (np.exp(-d2 / (2 * 5.0 ** 2)) * 2.4 + np.exp(-d2 / (2 * 30.0 ** 2)) * .22)[..., None] * hex2lin("FFB45E")

save(img, out)
