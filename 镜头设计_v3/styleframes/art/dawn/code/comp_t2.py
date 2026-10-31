"""HKBU SCIE1007 coursework science video, dawn art direction. T2 comp: a lit window at dusk with a phone-footage stand-in behind the glass.
grade() is the whole treatment a real clip gets: no keying, no relighting, the footage only has to sit in a warm room behind a frame.
python comp_t2.py <prefix> <out.png>
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
L = {k: load(f"{pre}_{k}.npy") for k in ("sky", "spill", "mask", "data")}
px = json.load(open(pre + "_px.json"))
h, w = L["sky"].shape[:2]
hy = int(HY * h / H)
yy = np.arange(h, dtype=np.float32)[:, None]
al = np.clip(L["data"][..., 3], 0, 1)[..., None]


def phone_plate(W_=1280, H_=720):
    """Stand-in for an ordinary phone clip: flat exposure, cream wall, a door edge, a shelf, a grey seated figure. Deliberately dull, so the grade has to do the work."""
    im = Image.new("RGB", (W_, H_), (178, 174, 166))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 300, H_], fill=(160, 156, 150))
    d.rectangle([980, 0, 1010, H_], fill=(205, 200, 190))
    d.rectangle([1010, 0, W_, H_], fill=(120, 112, 100))
    d.rectangle([90, 120, 330, 142], fill=(96, 84, 72))
    d.rectangle([110, 60, 150, 120], fill=(70, 74, 90)); d.rectangle([160, 74, 196, 120], fill=(110, 80, 70)); d.rectangle([205, 50, 240, 120], fill=(84, 92, 80))
    d.rectangle([0, 640, W_, H_], fill=(112, 102, 92))
    im = im.filter(ImageFilter.GaussianBlur(5))
    # figure, seated, left of centre, facing us: only a grey shape, this is a placeholder
    f = Image.new("L", (W_, H_), 0)
    g = ImageDraw.Draw(f)
    cx = 560
    g.ellipse([cx - 92, 138, cx + 92, 356], fill=255)
    g.rectangle([cx - 46, 330, cx + 46, 420], fill=255)
    g.polygon([(cx - 70, 386), (cx + 70, 386), (cx + 230, 470), (cx + 280, 720), (cx - 280, 720), (cx - 230, 470)], fill=255)
    f = f.filter(ImageFilter.GaussianBlur(3))
    grey = Image.new("RGB", (W_, H_), (86, 84, 84))
    im.paste(grey, (0, 0), f)
    a = np.asarray(im, np.float32) / 255
    # the ceiling light every phone clip has, and a soft light on the figure
    y, x = np.mgrid[0:H_, 0:W_]
    a += (np.exp(-(((x - 640) / 420) ** 2 + ((y + 60) / 240) ** 2)) * .32)[..., None]
    fig = (np.asarray(f, np.float32) / 255)[..., None]
    a = a * (1 - fig * .0) + fig * (np.exp(-(((x - cx + 60) / 240) ** 2 + ((y - 240) / 220) ** 2)) * .16)[..., None]
    return np.clip(a, 0, 1)


def grade(srgb):
    """Phone clip to lit room: keeps skin warm whatever the white balance was. Every number here is one slider in the edit."""
    x = np.power(srgb, 2.2)
    lum = (x * [.3, .6, .1]).sum(-1, keepdims=True)
    x = lum * .35 + x * .65                         # most of the phone's own colour goes
    x = x * np.array([1.7, .9, .36], np.float32) # tungsten
    x = x + np.array([.018, .007, .002], np.float32)     # shadows stay brown, never blue
    x = np.power(x, 1.22) * 1.3 / (1 + x * .3)         # a little contrast back, highlights roll off, the ceiling light cannot clip
    yy_, xx_ = np.mgrid[0:x.shape[0], 0:x.shape[1]]
    v = 1 - .55 * (((xx_ / x.shape[1] - .5) * 1.6) ** 2 + ((yy_ / x.shape[0] - .5) * 1.5) ** 2)
    return x * np.clip(v, .25, 1)[..., None]


def pin(a, c, w, h):
    """Corner pin a float image to quad c (tl, tr, br, bl) in px."""
    H_, W_ = a.shape[:2]
    src = [(0, 0), (W_, 0), (W_, H_), (0, H_)]
    A_, B_ = [], []
    for (x, y), (u, v) in zip([tuple(p) for p in c], src):
        A_ += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        B_ += [u, v]
    co = np.linalg.solve(np.array(A_, float), np.array(B_, float))
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = co[6] * x + co[7] * y + 1
    u = np.clip((co[0] * x + co[1] * y + co[2]) / d, 0, W_ - 1.001)
    v = np.clip((co[3] * x + co[4] * y + co[5]) / d, 0, H_ - 1.001)
    u0, v0 = u.astype(int), v.astype(int)
    fu, fv = (u - u0)[..., None], (v - v0)[..., None]
    return a[v0, u0] * (1 - fu) * (1 - fv) + a[v0, u0 + 1] * fu * (1 - fv) + a[v0 + 1, u0] * (1 - fu) * fv + a[v0 + 1, u0 + 1] * fu * fv


bg = sky("S2", w, h, hy, seed=31, clouds=.6, stars=.09)
for sd, amp, col in ((71, 34, "4A3560"), (72, 16, "2C2240")):
    n = fbm(sd, 150, 1, 5, w, 1)[0]
    top = hy - (amp * (.65 + .4 * n)).clip(2) * h / 1080
    m = np.clip((yy - top[None, :]) / 1.2, 0, 1)[..., None]
    bg = bg * (1 - m) + hex2lin(col) * m

FILL = hex2lin("3D3268") * 1.15
WARM = hex2lin("FFB877") * 1.0
surf = L["sky"][..., :3] * FILL + L["spill"][..., :3] * WARM * .7

# the ground goes to the dusk land with distance, so the building stands on the same horizon as every other shot
dat = L["data"]
safe = np.maximum(al[..., 0], 1e-4)
dist = dat[..., 0] / safe * 500
fog = (1 - np.exp(-np.clip(dist - 16, 0, None) / 90))[..., None]
surf = surf * (1 - fog) + hex2lin(SKY["S2"]["land"]) * fog
# plaster: a slow, static unevenness on the wall, so it reads as a wall and not as a card
pl = 1 + .10 * fbm(83, 70, 90, 5, w, h)[..., None] + .05 * fbm(84, 6, 9, 3, w, h)[..., None]
surf = surf * np.clip(pl, .6, 1.4)
img = surf * al + bg * (1 - al)

plate = phone_plate()
g = grade(plate)
c = [px["tl"], px["tr"], px["br"], px["bl"]]
foot = pin(g, c, w, h)
m = np.clip(L["mask"][..., :1], 0, 1)
# cold sky on the glass, top corner only: the window stays a window, not a screen
yi, xi = np.mgrid[0:h, 0:w].astype(np.float32)
rx = (xi - c[0][0]) / (c[1][0] - c[0][0]); ry = (yi - c[0][1]) / (c[3][1] - c[0][1])
refl = np.clip(.55 - rx * .9 - ry * .7, 0, 1)[..., None]
room = foot + refl * hex2lin("5A4E9C") * .35
img = img * (1 - m) + room * m

img = bloom(img, sig=(4, 20, 80), wt=(.12, .12, .12), thr=.55)
save(img, out)
