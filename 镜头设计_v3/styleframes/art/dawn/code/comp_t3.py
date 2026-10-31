"""HKBU SCIE1007 coursework science video, dawn art direction. T3: the darkest frame of the film. The lock cannot be seen; it only blots out the stars. The mass is the same outline the audience meets lit in T4, so the cut from here to there is one continuous reveal.
The keyhole is a hole through it, on the fixed horizon: there is sky behind it. Schematic, so its outline is dashed. It is drawn, not measured.
python comp_t3.py <T4 prefix> <out.png>
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from comp_lib import *

pre, out = sys.argv[1], sys.argv[2]
w, h, hy = W, H, HY
dat = load(pre + "_data.npy")
mass = np.clip(dat[..., 3], 0, 1)
yy = np.arange(h, dtype=np.float32)[:, None]

bg = sky("S3", w, h, hy, seed=9, clouds=0, stars=0)
r = np.random.default_rng(308)
n = 1500
xs, ys = r.integers(0, w, n), r.integers(0, hy, n)
v = np.power(r.random(n), 6) * .34 + .008
s = np.zeros((h, w), np.float32)
np.add.at(s, (ys, xs), v)
stars = (s + blur(s, 1.0) * 3)[..., None] * np.array([.86, .9, 1.0], np.float32)
stars = stars * sm(.015, .25, (hy - yy) / hy)[..., None]

# the keyhole, upright, standing on the horizon so the fixed line runs through it
KX, HT, RAD = 960, 400, 92
SS = 2
key = Image.new("L", (w * SS, h * SS), 0)
d = ImageDraw.Draw(key)
base = hy + 92
cy = base - HT + RAD
d.ellipse([(KX - RAD) * SS, (cy - RAD) * SS, (KX + RAD) * SS, (cy + RAD) * SS], fill=255)
d.polygon([((KX - 40) * SS, (cy + RAD * .55) * SS), ((KX + 40) * SS, (cy + RAD * .55) * SS), ((KX + 78) * SS, base * SS), ((KX - 78) * SS, base * SS)], fill=255)
keym = np.asarray(key.resize((w, h), Image.LANCZOS), np.float32) / 255

# dashed outline along the edge of the hole
outline = np.zeros((h, w), np.float32)
edge = keym - np.asarray(Image.fromarray((keym * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)), np.float32) / 255
ys_, xs_ = np.nonzero(edge > .4)
ang = np.arctan2(ys_ - cy, xs_ - KX)
# a dash pattern by arc length round the shape: walk it as angle round the centre of the shape
cx0, cy0 = KX, cy + 90
ang = np.arctan2(ys_ - cy0, xs_ - cx0)
order = np.argsort(ang)
pts = np.stack([xs_[order], ys_[order]], 1).astype(np.float32)
seg = np.r_[0, np.cumsum(np.minimum(np.linalg.norm(np.diff(pts, axis=0), axis=1), 6))]
on = (seg % 22) < 13
outline[ys_[order][on], xs_[order][on]] = 1
outline = blur(np.pad(outline, 8), .7)[8:-8, 8:-8] * 1.9

# everything but the hole hides the stars where the mass stands
behind = bg + stars
lock = hex2lin("020203") + hex2lin("05060A") * blur(np.pad(mass, 40), 26)[40:-40, 40:-40][..., None] * .4
img = behind * (1 - mass[..., None]) + lock * mass[..., None]
land = np.clip((yy - hy) / 1.2, 0, 1)[..., None]
img = img * (1 - land) + hex2lin(SKY["S3"]["land"]) * land

# through the hole: a little more sky than anywhere else in the frame. Barely any colour. The line of the horizon is visible only here
inner = sky("S3", w, h, hy, seed=9, clouds=0, stars=0) * 3.2 + stars * 2.2
low = sm(.1, 0, (hy - yy) / hy)[..., None] * hex2lin("1B2230") * 1.2
inner = inner + low
land2 = np.clip((yy - hy) / 1.2, 0, 1)[..., None]
inner = inner * (1 - land2) + hex2lin("030305") * land2
k = keym[..., None]
img = img * (1 - k) + inner * k
img += outline[..., None] * hex2lin("B9BDC6") * .62
img += (blur(np.pad(keym, 60), 40)[60:-60, 60:-60])[..., None] * hex2lin("0A0D14") * .32
save(img, out, dither=True)
json.dump(dict(kx=KX, cy=cy, base=base, rad=RAD), open(pre.rsplit("/", 2)[0] + "/plates/T3.json", "w"))
