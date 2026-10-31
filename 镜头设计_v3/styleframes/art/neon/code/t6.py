"""HKBU SCIE1007 coursework science video. T6 of the neon street direction: the roadmap used twelve times in the film. Six signs in a row down one wall of one street, one power line runs along their tops.
The first three are lit. The line stops at the door of the fourth, which has caught at one end only. The last three carry not reported. Nothing blinks: the fourth stays steady and half lit."""
import time

from nk import *

t0 = time.time()
vp = (1700, 480)
plate = street_cached(vp, seed=33, n=120, gain=0.9, tag="t6b", pal=[GRN, CYN, PINK, AMB, RED, YEL])
# the street is dark where nobody has walked: the far end is the unlit future
img = plate * (0.1 + 0.9 * smooth(1700, 800, xx))[..., None]

#       x    y    w    h, all feet on one line so the row reads like a sentence
BOX = [(30, 165, 400, 271), (452, 208, 300, 228), (774, 245, 290, 191), (1086, 270, 260, 166), (1368, 286, 270, 150), (1660, 310, 232, 126)]
ST = ["Target", "Hit", "Improve", None, None, "Approval"]
COL = [PINK, YEL, GRN]
wh = (W, H)
AMBL = rgb("#FFC24A")
UNLIT = np.array([0.42, 0.43, 0.47], np.float32)
wy = 524

# the wall under the row, with the shopfronts of the stations that have been reached
img = img * (1 - 0.92 * smooth(430, 440, yy))[..., None]
for i, (x, y, ww, hh) in enumerate(BOX[:3]):
    m = gauss(((xx > x + 14) & (xx < x + ww - 14) & (yy > 452) & (yy < wy)).astype(np.float32), 1.0)
    shutter = 0.72 + 0.28 * np.cos(xx * 2 * np.pi / 9) ** 2
    img = img + (m * shutter)[..., None] * (rgb("#FFC890") * 0.3 + COL[i] * 0.16)
# the door of the fourth: one warm doorway, open
dm = gauss(((xx > 1090) & (xx < 1118) & (yy > 446) & (yy < wy)).astype(np.float32), 0.8)
img = img + dm[..., None] * rgb("#FFC890") * 1.1 + gauss(dm, 18)[..., None] * rgb("#FFB25A") * 0.5


def line(v):
    return 118 + 0.095 * v


def polyline(a, b):
    v = np.arange(a, b, 6, dtype=np.float32)
    return np.stack([v, line(v)], 1)


lit = [polyline(-10, 1104)]
for x, y, ww, hh in BOX[:3]:
    c = x + ww * 0.5
    lit.append(np.array([(c, line(c)), (c, y)], np.float32))
lit.append(np.array([(1104, line(1104)), (1104, 270)], np.float32))
img = img + neon(gauss(draw_tube(wh, lit, 6, closed=False), 0.6), AMBL, 0.85, 0.42)
dead = [polyline(1104, 1930)] + [np.array([(x + ww * 0.5, line(x + ww * 0.5)), (x + ww * 0.5, y)], np.float32) for x, y, ww, hh in BOX[4:]]
img = img + draw_tube(wh, dead, 3, dash=(16, 12), closed=False)[..., None] * UNLIT


def fit(txt, size, width):
    while text_w(txt, size, "Bold") > width:
        size -= 1
    return size


def signface(img, i):
    x, y, ww, hh = BOX[i]
    box = gauss(((xx > x) & (xx < x + ww) & (yy > y) & (yy < y + hh)).astype(np.float32), 0.8)
    fr = Image.new("L", wh, 0)
    ImageDraw.Draw(fr).rounded_rectangle((x + 8, y + 8, x + ww - 8, y + hh - 8), radius=14, outline=255, width=5 if i < 3 else 4)
    fr = np.asarray(fr, np.float32) / 255
    cx = x + ww / 2
    if i == 3:
        t = text("Cells &", 44, (cx, y + 70), "Bold", "ms") + text("animals", 44, (cx, y + 124), "Bold", "ms")
    elif i == 4:
        s_ = fit("Clinical trials", 40, ww - 28)
        print("clinical", s_)
        t = text("Clinical trials", s_, (cx, y + 64), "Bold", "ms") + text("1-2-3", s_, (cx, y + 112), "Bold", "ms")
    else:
        sz = fit(ST[i], {0: 104, 1: 104, 2: 76, 5: 48}[i], ww - 44)
        print(ST[i], sz)
        t = text(ST[i], sz, (cx, y + hh * 0.5 + sz * 0.34), "Bold", "ms")
    img = img * (1 - box * 0.96)[..., None] + box[..., None] * np.array([0.012, 0.01, 0.016], np.float32)
    if i < 3:
        img = img + neon(gauss(fr, 0.6), COL[i], 0.88, 0.75) + neon(gauss(t, 0.5), COL[i], 0.92, 0.75)
    elif i == 3:
        # just powered: caught at the end the line comes in on, the rest still cold. Steady, never flickering
        ramp = smooth(x + ww * 0.66, x + ww * 0.16, xx)
        img = img + neon(gauss(fr * ramp, 0.6), AMB, 0.9, 0.55) + neon(gauss(t * ramp, 0.5), AMB, 0.85, 0.5)
        img = img + (gauss(fr * (1 - ramp), 0.6) + gauss(t * (1 - ramp), 0.5))[..., None] * UNLIT
    else:
        img = img + (gauss(fr, 0.6) + gauss(t, 0.5))[..., None] * UNLIT
    if i >= 3:
        # not reported: a painted plate bolted under the sign. Paint, not light
        px, pw = (1122, 224) if i == 3 else (x, ww)
        py, ph = y + hh + 8, 50
        pl = gauss(((xx > px) & (xx < px + pw) & (yy > py) & (yy < py + ph)).astype(np.float32), 0.7)
        img = img * (1 - pl)[..., None] + pl[..., None] * np.array([0.11, 0.115, 0.13], np.float32)
        tx = text("not reported", 37, (px + pw / 2, py + 38), "Medium", "ms")
        img = img * (1 - tx)[..., None] + tx[..., None] * np.array([0.72, 0.74, 0.78], np.float32)
    return img


for i in range(6):
    img = signface(img, i)

# 048: a small measured lightbox on the line, exactly where the power stops
bw, bh = 112, 56
hx = 1060
by0 = 146
hang = Image.new("L", wh, 0)
ImageDraw.Draw(hang).line((hx, by0 + bh, hx, line(hx)), fill=255, width=4)
img = img + neon(gauss(np.asarray(hang, np.float32) / 255, 0.5), AMBL, 0.5, 0.1)
lb = gauss(((xx > hx - bw / 2) & (xx < hx + bw / 2) & (yy > by0) & (yy < by0 + bh)).astype(np.float32), 0.7)
img = img + gauss(lb, 16)[..., None] * rgb("#FFE6C4") * 0.5 + gauss(lb, 54)[..., None] * rgb("#FFD6B0") * 0.28
img = img * (1 - lb)[..., None] + lb[..., None] * rgb("#FFF7E6")
tn = text("048", 46, (hx, by0 + 44), "Black", "ms")
img = img * (1 - tn)[..., None] + tn[..., None] * rgb("#120C0A")

# people go in black against the shopfronts, so the wet road reflects them too. Nobody past the fourth door
pm = Image.new("L", (W * 3, H * 3), 0)
pd = ImageDraw.Draw(pm)
for px, hh, ph, fl in ((1062, 118, False, 1), (640, 124, True, 1), (690, 112, False, -1), (232, 132, False, 1), (300, 120, False, -1)):
    person(pd, px, wy + 2, hh, 3, ph, fl)
pm = np.asarray(pm.resize(wh, Image.LANCZOS), np.float32) / 255
img = img * (1 - 0.97 * pm)[..., None]

img = wet_road(img, wy, 0.98, seed=44, fall=640)
finish(img, "T6.png", 0.6)
print("done", time.time() - t0)
