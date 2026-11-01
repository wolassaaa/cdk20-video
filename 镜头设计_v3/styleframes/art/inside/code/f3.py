"""HKBU SCIE1007 coursework science video. Direction inside, F3 (script 3-02, 3-03): lock and key. Everything here is schematic on purpose: plain flat shapes, a dotted line inside each protein, no atoms."""
from ilib import *

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def circ(cx, cy, r):
    return np.hypot(xx - cx, yy - cy) - r


def rbox(cx, cy, hw, hh, r=10):
    qx, qy = np.abs(xx - cx) - hw + r, np.abs(yy - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def key(cx, top):
    """Bow at the top, shaft down, two teeth on the right. top is the y of the bow centre."""
    bow = np.maximum(circ(cx, top, 92), -circ(cx, top, 34))
    tip = top + 300
    shaft = rbox(cx, (top + tip) / 2 + 30, 27, (tip - top) / 2 - 30, 12)
    t1 = rbox(cx + 44, tip - 96, 42, 21, 8)
    t2 = rbox(cx + 34, tip - 26, 32, 21, 8)
    return np.minimum(np.minimum(bow, shaft), np.minimum(t1, t2))


def blob(cx, cy, pts):
    d = circ(cx + pts[0][0], cy + pts[0][1], pts[0][2])
    for p in pts[1:]:
        d = smin(d, circ(cx + p[0], cy + p[1], p[2]), 70)
    return d


def ramp(d):
    return np.clip(.5 - d, 0, 1)


AX, BX, CY = 470, 1450, 700
A = blob(AX, CY, [(-90, 40, 170), (110, 70, 170), (0, -70, 180), (-150, -60, 110), (160, -50, 120)])
B = blob(BX, CY, [(100, 30, 170), (-110, 80, 160), (10, -70, 180), (170, -80, 100), (-160, -40, 120)])
ka, kb = key(AX, 362), key(BX, 142)
slotA = key(AX, 362) - 9
slotB = np.minimum(rbox(BX + 6, CY - 100, 22, 190, 10), np.minimum(rbox(BX - 50, CY - 10, 52, 24, 8), rbox(BX - 34, CY + 62, 36, 24, 8))) - 6
A2 = np.maximum(A, -slotA)
B2 = np.maximum(B, -slotB)

rgb = crowd(seed=7)
rgb = dim(rgb, box(0, 0, W, H, 10), .55)
rgb = dim(rgb, gblur(((A < 90) | (B < 90)).astype(np.float32), 50), .55)


def fill(rgb, d, col, line=BLACK, lw=7):
    rgb = rgb * (1 - ramp(d - lw)[..., None]) + line * ramp(d - lw)[..., None]
    return rgb * (1 - ramp(d)[..., None]) + col * ramp(d)[..., None]


rgb = fill(rgb, A2, BONE)
rgb = fill(rgb, B2, BLUE, line=BLACK)


def dotted(rgb, d, slot, cx, cy, col, n=64):
    th = np.arctan2(yy - cy, xx - cx)
    band = np.clip(4 - np.abs(d + 22), 0, 1)
    dots = np.clip((np.sin(th * n) - .1) * 4, 0, 1)
    keep = np.clip((slot - 26) / 3, 0, 1)
    a = (band * dots * keep)[..., None]
    return rgb * (1 - a) + col * a


rgb = dotted(rgb, A, slotA, AX, CY, KLEIN)
rgb = dotted(rgb, B, slotB, BX, CY, BONE)
rgb = fill(rgb, ka, RED, line=BLACK)
rgb = fill(rgb, kb, RED, line=BLACK)
im = to_pil(rgb)
d = ImageDraw.Draw(im)

# yes and no are marks, so they read without English
x0, y0 = BX + 150, 396
for w_, c in ((30, (0, 0, 0)), (16, (255, 255, 255))):
    d.line([(x0 - 44, y0 - 44), (x0 + 44, y0 + 44)], fill=c, width=w_)
    d.line([(x0 - 44, y0 + 44), (x0 + 44, y0 - 44)], fill=c, width=w_)
x0, y0 = AX + 170, 396
for w_, c in ((30, (0, 0, 0)), (16, (255, 255, 255))):
    d.line([(x0 - 44, y0 + 2), (x0 - 10, y0 + 40), (x0 + 54, y0 - 46)], fill=c, width=w_, joint="curve")

text(im, (AX, 1000), "target (a protein)", sans(46, 600), anchor="ma")
text(im, (AX + 120, 196), "candidate (a small molecule)", sans(46, 600), anchor="la")
leader(im, (AX + 112, 222), (AX + 40, 290))
text(im, (960, 640), "selectivity", sans(70, 600), anchor="mm")
tag(im, (96, 72), "schematic", "schematic", size=32, bg=NIGHT)
save(im, "F3.png")
