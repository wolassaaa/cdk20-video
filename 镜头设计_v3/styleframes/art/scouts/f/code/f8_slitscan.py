"""HKBU SCIE1007 coursework science video. Style scout f8: real slit scan. The two walls of the corridor are the CDK20 render itself, read one slit at a time and stretched toward the camera."""
from fx import *

P = load(1.0)
mask, key, rim, ao, conf, nrm = P["mask"], P["key"], P["rim"], P["ao"], P["conf"], P["normal"]
h, w = mask.shape
yy0, xx0 = np.nonzero(mask > 0.5)
x0, x1, y0, y1 = xx0.min(), xx0.max(), yy0.min(), yy0.max()

# source artwork: the surface solarized through a cycling gel palette, each tone flips like a colour negative
L = np.clip(0.95 * key * ao + 0.62 * rim * ao + 0.06, 0, 1)
STOPS = [rgb(c) for c in ("#05010F", "#3D00B8", "#FF0A54", "#FF8A00", "#FFF0A8", "#18E2FF", "#3D00B8")]


def gel(t):
    t = (t % 1.0) * (len(STOPS) - 1)
    i = np.floor(t).astype(np.int32)
    f = (t - i)[..., None]
    arr = np.stack(STOPS)
    return arr[i] * (1 - f) + arr[np.minimum(i + 1, len(STOPS) - 1)] * f


src = gel(L * 0.86) * mask[..., None]
cx, cy = W / 2, 338.0
yy, xx = np.mgrid[:H, :W].astype(np.float32)
dx, dy = (xx - cx), (yy - cy)
gap = 16.0  # half height of the black slit the camera flies through
wall = np.abs(dy) - gap
z = 1 / np.maximum(wall, 0.5)  # perspective depth on a flat wall
zn = z * 150

# along the wall the slit sweeps over the protein; across the wall it reads the slit top to bottom
u = dx * zn / 150  # lateral position on the wall in slit units
S = 900.0
sweep_x = x0 + (x1 - x0) * (0.5 + 0.5 * np.sin(zn * 0.17 + np.sign(dy) * 1.2 + 0.0))  # which slit is exposed at this depth
slit_y = y0 + (y1 - y0) * ((u * 0.36 + 0.5) % 1.0)
wallc = sample(src, sweep_x, slit_y)
# streaks: integrate along depth, the long exposure of the slit. Thousands of fine lines, one per point on the slit
acc = np.zeros((H, W, 3), np.float32)
N = 40
u2 = dx / np.maximum(wall, 4.0)
top = dy < 0
for i in range(N):
    zz = zn * (1 + 0.02 * i)
    sx = x0 + (x1 - x0) * (0.5 + 0.5 * np.sin(zz * 0.09 + top * 1.9))
    sy = y0 + (y1 - y0) * (0.5 + 0.5 * np.sin(u2 * 3.3 + 0.7 * np.sin(u2 * 0.41) + top * 2.0))
    acc += sample(src, sx, sy)
wallc = acc / N * 2.0
wallc = np.where(top[..., None], wallc, wallc[..., [2, 0, 1]])  # lower wall through a different gel
fade = smooth(10.0, 150.0, wall) * (0.85 + 0.15 * smooth(100, 360, wall))
img = np.clip(wallc, 0, 1) * fade[..., None]

# black slit keeps the middle clean, and a hot line sits on each lip
lip = np.exp(-(wall / 2.2) ** 2) * smooth(30, 620, np.abs(dx) * -1 + 640)
img += lip[..., None] * rgb("#FFE9C8") * 0.75

# the protein itself at the vanishing point, big, sharp, printed in negative colour
sc = 0.56
pw, ph = 1920, 1080
px = (xx - cx) / sc + (x0 + x1) / 2
py = (yy - cy) / sc + (y0 + y1) / 2
pm = sample(mask, px, py)
pk = sample(key, px, py)
pr = sample(rim, px, py)
pa = sample(ao, px, py)
core = gel(np.clip(0.95 * pk * pa + 0.62 * pr * pa + 0.06, 0, 1) * 0.86)
halo = gauss(pm, 22)
img = img * (1 - 0.97 * smooth(0.02, 0.42, halo))[..., None]
img = mix(img, core, pm)

# title: extruded down the corridor by the same streak method, sharp face on top
f = font("bahnschrift.ttf", 164)
try:
    f.set_variation_by_name("Bold Condensed")
except Exception:
    pass
tr = 56
tw = text_width("CDK20", f, tr)
tx, ty = cx - tw / 2, 668
tm = text_mask("CDK20", f, (tx, ty), tr)
ex = np.zeros((H, W), np.float32)
for i in range(1, 240):
    s = 1 - i * 0.0034
    mx = (xx - cx) / s + cx
    my = (yy - cy) / s + cy
    ex = np.maximum(ex, sample(tm, mx, my) * (1 - i / 240) ** 1.4)
ext = ex[..., None] * mix(rgb("#3D00B8"), rgb("#FF0A54"), smooth(0.05, 0.7, ex))
keep = 1 - smooth(0.0, 0.25, ex + gauss(tm, 12) * 1.5)
img = img * (0.1 + 0.9 * keep)[..., None] + ext
img = mix(img, rgb("#FFF6E5"), tm)

lab = font("bahnschrift.ttf", 22)
lw = text_width(LABEL, lab, 1.2)
lm = text_mask(LABEL, lab, (cx - lw / 2, 703), 1.2)
back = gauss(lm, 5) * 6
img = img * (1 - np.clip(back, 0, 1) * 0.92)[..., None]
img = mix(img, rgb("#FFFFFF"), lm)

bloom = gauss(np.clip(img - 0.75, 0, 2), 7) * 0.45
img = img + bloom
save(img, OUT / "f8_slitscan.png")
print("ok")
