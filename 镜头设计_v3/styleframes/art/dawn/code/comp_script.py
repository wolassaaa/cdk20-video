"""HKBU SCIE1007 coursework science video, dawn art direction. Colour script: one sky, left to right over 17:43, each segment as wide as its running time. Same stops as the stills.
python comp_script.py <out.png>
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from comp_lib import *

W_, H_ = 1920, 480
SEC = [("S1", 141), ("S2", 142), ("S3", 129), ("S4", 213), ("S5", 139), ("S6", 151), ("S7", 49), ("S8", 99)]
T = sum(s for _, s in SEC)
assert T == 1063
hy = int(H_ * 2 / 3)
# S5 opens as indigo; the horizon only burns from W4 (12:10) on. W4 is the first colour red has had since S1
SKY["S5a"] = dict(stops=[(0, "4A2C7A"), (.05, "3A2670"), (.2, "262060"), (.5, "131650"), (1, "070A2A")], land="04040F")
edges = np.cumsum([0] + [s for _, s in SEC]).astype(float)
ts = (np.arange(W_) + .5) / W_ * T
t_h = np.clip((hy - (np.arange(H_) + .5)) / hy, 0, 1)
ramps = {k: ramp(k, t_h) for k in list(SKY)}


def col_at(t):
    i = int(np.searchsorted(edges, t, "right") - 1)
    i = min(i, len(SEC) - 1)
    name = SEC[i][0]
    if name == "S5":
        base = ramps["S5a"] ** (1 / 2.2)
    else:
        base = ramps[name] ** (1 / 2.2)
    return base


img = np.zeros((H_, W_, 3), np.float32)
FADE = 14.0  # seconds either side of a join: neighbouring hours run into each other
step = T / W_
cols = np.stack([col_at(t) for t in ts], 1)
SIG = 30.0 / step        # about half a minute either side: one sky, no seams
kern = int(SIG * 6) | 1
g = np.exp(-.5 * (np.arange(kern) - kern // 2) ** 2 / SIG ** 2); g /= g.sum()
pad = kern // 2
c2 = np.pad(cols, ((0, 0), (pad, pad), (0, 0)), mode="edge")
out = np.zeros_like(cols)
for yy in range(H_):
    for ch in range(3):
        out[yy, :, ch] = np.convolve(c2[yy, :, ch], g, "valid")
img = out ** 2.2

# W4 at 12:10: the burn is the one hard edge in the film, so it stays out of the smoothing. It opens on the beat, then eases into S6
bw = (sm(726, 734, ts) * (1 - sm(790, 850, ts)))[None, :, None]
img = img * (1 - bw) + ramps["S5"][:, None, :] * bw

# land: one ridge running through the whole night, in each hour's own land colour
rn = fbm(5, 120, 1, 5, W_, 1)[0]
crest = hy - 4 - 7 * sm(-1, 1.6, rn)
yi = np.arange(H_, dtype=np.float32)[:, None]
land_col = np.stack([hex2lin(SKY[SEC[min(int(np.searchsorted(edges, t, "right") - 1), 7)][0]]["land"]) ** (1 / 2.2) for t in ts], 0)
lc = np.stack([np.convolve(np.pad(land_col[:, c], pad, mode="edge"), g, "valid") for c in range(3)], 1) ** 2.2
m = np.clip((yi - crest[None, :]) / 1.2, 0, 1)[..., None]
img = img * (1 - m) + lc[None, :, :] * m

# the moments that hold the colour: where the first blue body rises, the first burn, the lamps, the amber
xof = lambda t: t / T * W_
d = Image.new("L", (W_, H_), 0)
dd = ImageDraw.Draw(d)
def stamp(pre, width, cx, sink, ink, rim=None, side=-2):
    """Drop a real silhouette from the stills onto the ridge, so the strip carries the same shapes."""
    a = np.load(pre + "_data.npy")[..., 3].astype(np.float32)
    ys, xs = np.nonzero(a[:721] > .5)
    crop = a[ys.min():721, xs.min():xs.max() + 1]
    wh = max(int(crop.shape[0] * width / crop.shape[1]), 2)
    t = np.asarray(Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((width, wh), Image.LANCZOS), np.float32)[..., None] / 255
    x0, y0 = int(cx - width / 2), hy - wh + sink
    global img
    img[y0:y0 + wh, x0:x0 + width] = img[y0:y0 + wh, x0:x0 + width] * (1 - t) + hex2lin(ink) * t
    if rim:
        r = np.clip(t - np.roll(t, side, 1), 0, 1)
        img[y0:y0 + wh, x0:x0 + width] += r * hex2lin(rim) * 1.2


stamp("../_work/T1/T1", 170, xof(62), 8, "120A10", "FF5A24", side=2)   # the ember sits on the right lobe, frame left, as in T1
stamp("../_work/T4/T4", 120, xof(450), 6, "0A1636", "6AB4FF")
# S2: one lit window in a dark block
x = int(xof(212)); img[hy - 56:hy + 2, x:x + 86] = hex2lin("120E20"); img[hy - 44:hy - 16, x + 12:x + 60] = hex2lin("F2B070")
# S3: the keyhole, barely there
x = int(xof(348)); yy_, xx_ = np.mgrid[0:H_, 0:W_]
kh = (((xx_ - x) ** 2 + (yy_ - (hy - 38)) ** 2) < 8 ** 2) | ((np.abs(xx_ - x) < 3.2 + (yy_ - (hy - 38)) * .16) & (yy_ > hy - 38) & (yy_ < hy - 2))
img[kh] = hex2lin("2A3040")
# S8: four windows of the same building, the road's end
x = int(xof(1000)); img[hy - 60:hy + 2, x:x + 120] = hex2lin("15121A")
for i, (dx, dy) in enumerate(((12, 12), (66, 12), (12, 36), (66, 36))):
    img[hy - 60 + dy:hy - 60 + dy + 16, x + dx:x + dx + 42] = hex2lin("FFC070")
# six lamps in S6, three lit
for k in range(6):
    t = edges[5] + (k + 1) / 7 * SEC[5][1]
    x = int(xof(t))
    img[hy - 22:hy, x:x + 1] = hex2lin("1C1A24")
    if k < 3:
        img += (np.exp(-((xx_ - x) ** 2 + (yy_ - (hy - 23)) ** 2) / (2 * 2.2 ** 2)) * 1.6 + np.exp(-((xx_ - x) ** 2 + (yy_ - (hy - 23)) ** 2) / (2 * 9.0 ** 2)) * .16)[..., None] * hex2lin("FFD29A")

img = img * 1.0
save(img, sys.argv[1])

# hard joins as hairlines, so the eye can measure each hour; labels live in the Remotion layer
np.save(sys.argv[1].replace(".png", ".edges.npy"), edges / T * W_)
