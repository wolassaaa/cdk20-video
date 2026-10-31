"""HKBU SCIE1007 coursework science video. shanshui direction, shot T6 (6-10): the road map as one stretch of a handscroll with six ferry stops. The scroll is painted up to the gate of stop four; past that it is still blank paper. This is a schematic, so it uses pale ink and blank paper, and no seal."""
from sbrush import *

yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
rng = np.random.default_rng(16)
base = paper(seed=22)
XS = [170, 480, 790, 1090, 1400, 1715]
NAMES = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"]


def yc(x):
    return 600 + 62 * np.sin(np.asarray(x, np.float32) / 1920 * 2 * np.pi * 1.1 + .4)


HW = 74
n1 = fbm(SH, SW, 3.0, 81); n2 = fbm(SH, SW, 2.2, 82)
paint = 1 - smooth01(925, 1045, xx + (n1 - .5) * 170)              # where the painter has stopped
yr = yc(xx[0])[None]
above = yr - HW + (n2 - .5) * 34 - yy                              # distance up the far bank
below = yy - (yr + HW) + (n2 - .5) * 34                            # distance down the near bank

# far bank: real CDK20 twice over, small, in the same ink as T4. Painted scroll only
S = surface2()
rgb = far_hills(base, 500, 150, .12, 83, 90)
hide0 = smooth01(0, 20, -above)
rgb = rgb * (1 - hide0[..., None]) + base * hide0[..., None]
rgb = base * (1 - paint[..., None]) + rgb * paint[..., None]
for cx, cy, sc, ry, sd in ((285, 560, 13.5, 205, 31), (800, 515, 9.5, 165, 37)):
    R = rot(0, ry, 0) @ rot(0, 0, 90)
    P = persp(R, 40, 66, 66 * sc, cx, cy, S=S)
    I = ink_rock(P, seed=sd, density=.8)
    foot = 1 - smooth01(cy - 120, cy - 30, yy + (n2 - .5) * 90)
    top = smooth01(30, 210, yy + (n1 - .5) * 170)
    fr = foot * top * paint
    h_ = np.clip(gblur(P["mask"], 2) * fr * 1.3, 0, 1)[..., None]
    rgb = rgb * (1 - h_) + base * h_
    rgb = lay(rgb, I, fr, dissolve(np.clip(fr * 1.2, 0, 1), sd + 1))

# banks: a wash that starts dark at the water and pales away from it
for dist, a_, seed in ((above, .42, 84), (below, .50, 85)):
    w_ = smooth01(-2, 7, dist) * np.exp(-np.maximum(dist, 0) / 46) * (.62 + .76 * fbm(SH, SW, 1.5, seed))
    w_ = w_ * paint * a_
    rgb = over(rgb, INK, np.clip(w_, 0, 1))
Br = Image.new("L", (SW * 2, SH * 2), 0); db = ImageDraw.Draw(Br)
for side in (-1, 1):
    x = 0.0
    while x < 1010:
        L = rng.uniform(70, 210)
        ts = np.linspace(0, 1, 18); xp = x + ts * L
        yp = yc(xp) + side * HW + np.sin(ts * 5 + x) * 3
        wd = (1.4 + 4.6 * np.sin(ts * np.pi) ** .7)
        for i in range(17):
            db.line((xp[i] * 2, yp[i] * 2, xp[i + 1] * 2, yp[i + 1] * 2), fill=255, width=max(1, int(wd[i] * 2)))
        x += L + rng.uniform(-6, 24)
Ba = np.asarray(Br, np.float32).reshape(SH, 2, SW, 2).mean((1, 3)) / 255
rgb = over(rgb, INK, Ba * dissolve(paint, 86) * .9)
rgb = ripples(rgb, 545, 660, rng, 26, strength=.20) * paint[..., None] + rgb * (1 - paint[..., None])
# low near hills under the labels stay pale so the type always wins
rgb2 = far_hills(rgb, 1085, 120, .10, 87, 40)
rgb = rgb2 * paint[..., None] + rgb * (1 - paint[..., None])

# unpainted road: a single pale dashed brush line, drawn with nothing behind it
D = Image.new("L", (SW * 3, SH * 3), 0); dd = ImageDraw.Draw(D)
x = 1034.0
while x < 1880:
    ts = np.linspace(0, 1, 6); xp = x + ts * 30; yp = yc(xp)
    for i in range(5):
        dd.line((xp[i] * 3, yp[i] * 3, xp[i + 1] * 3, yp[i + 1] * 3), fill=255, width=6)
    x += 56


def pavilion(x, y, s_=1.15):
    """A ferry shelter in plan outline, one for each stop."""
    p = [(-38, -33), (-16, -44), (0, -56), (16, -44), (38, -33), (24, -28), (-24, -28)]
    return [(x + a * s_, y + b * s_) for a, b in p], [((x - 17 * s_, y - 28 * s_), (x - 17 * s_, y)), ((x + 17 * s_, y - 28 * s_), (x + 17 * s_, y))]


def dash(dr, a, b, on=9, off=7, width=5):
    L = np.hypot(b[0] - a[0], b[1] - a[1]); t = 0.0
    while t < L:
        e = min(t + on, L)
        dr.line(((a[0] + (b[0] - a[0]) * t / L) * 3, (a[1] + (b[1] - a[1]) * t / L) * 3, (a[0] + (b[0] - a[0]) * e / L) * 3, (a[1] + (b[1] - a[1]) * e / L) * 3), fill=255, width=width)
        t += on + off


BANK = {k: float(yc(XS[k])) + (-HW if k == 4 else HW) for k in range(6)}
for k in (3, 4, 5):                                                        # stops nobody has reached: the shelter is only a dashed outline
    roof, posts = pavilion(XS[k], BANK[k])
    for i in range(len(roof)):
        dash(dd, roof[i], roof[(i + 1) % len(roof)])
    for a_, b_ in posts:
        dash(dd, a_, b_)
Da = np.asarray(D, np.float32).reshape(SH, 3, SW, 3).mean((1, 3)) / 255
rgb = over(rgb, INK, gblur(Da, .5) * .60)

# reached stops: the same shelter, painted solid on the near bank
Jt = Image.new("L", (SW * 3, SH * 3), 0); dj = ImageDraw.Draw(Jt)
for k in range(3):
    roof, posts = pavilion(XS[k], BANK[k])
    dj.polygon([(a_ * 3, b_ * 3) for a_, b_ in roof], fill=255)
    for a_, b_ in posts:
        dj.line((a_[0] * 3, a_[1] * 3, b_[0] * 3, b_[1] * 3), fill=255, width=11)
Ja = np.asarray(Jt, np.float32).reshape(SH, 3, SW, 3).mean((1, 3)) / 255
Ja = smooth01(.30, .62, gblur(Ja, 1.1) + (fbm(SH, SW, 1.8, 88) - .5) * .22)
rgb = over(rgb, INK, Ja * .97)

# type
f1 = vf(SERIF, 46, 600); f2 = vf(SERIF, 42, 500); fn = vf(SANS, 34, 400)
for k, (x_, nm) in enumerate(zip(XS, NAMES)):
    b_ = BANK[k]
    if k < 3:
        rgb = over(rgb, INK, text_mask(nm, f1, (x_, b_ + 58), "mm", w=SW, h=SH))
    else:
        ty = b_ - 170 if k == 4 else b_ + 58                                  # stop five sits on the far bank so the long label clears its neighbours
        rgb = over(rgb, INK, text_mask(nm, f2, (x_, ty), "mm", w=SW, h=SH) * .78)
        rgb = over(rgb, INK, text_mask("not reported", fn, (x_, ty + 54), "mm", w=SW, h=SH) * .66)

# the boat waits at the gate of stop four
bx, by = 975, float(yc(975)) + 8
rgb = boat(rgb, bx, by, 1.5)
rgb = over(rgb, INK, text_mask("048", vf(SERIF, 56, 800), (bx + 4, by - 66), "mm", w=SW, h=SH))
save_still(rgb, "T6.png")
