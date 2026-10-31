"""HKBU SCIE1007 coursework science video. T2 of the neon street direction: a person talks, half the screen. Placeholder only, the real footage is a teammate on a night street, filmed on a phone.
The placeholder sits under one warm bulb, seen from behind, so what is tested is the treatment: warm on the skin, a smeared street behind, red and green only on the edges."""
import time

from nk import *

t0 = time.time()
vp = (620, 470)
plate = street_cached(vp, seed=51, n=120, gain=1.15, tag="t2", pal=[RED, GRN, PINK, CYN, RED, AMB])
plate = gauss(plate, 6.0) * 1.05
wh = (W, H)
BULB = rgb("#FFAE5E")


def closed(pts):
    p = np.array(pts, np.float32)
    t = np.linspace(0, len(p), len(p) * 24, endpoint=False)
    i = np.floor(t).astype(int) % len(p)
    f = (t - np.floor(t))[:, None]
    p0, p1, p2, p3 = p[(i - 1) % len(p)], p[i], p[(i + 1) % len(p)], p[(i + 2) % len(p)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


def fillp(pts):
    im = Image.new("L", (W * 2, H * 2), 0)
    ImageDraw.Draw(im).polygon([(float(a) * 2, float(b) * 2) for a, b in closed(pts)], fill=255)
    return np.asarray(im.resize(wh, Image.LANCZOS), np.float32) / 255


# seen from behind, half body: a dark figure against the street, the bulb only reaches the edge of the cheek and one shoulder
head = fillp([(1286, 372), (1296, 280), (1344, 226), (1414, 208), (1490, 232), (1530, 300), (1528, 392), (1496, 462), (1440, 508), (1370, 506), (1318, 456)])
neck = fillp([(1346, 470), (1344, 530), (1330, 570), (1480, 570), (1466, 530), (1466, 470)])
# a hood down on the shoulders: the neck is never seen as a post
hood = fillp([(1262, 500), (1226, 566), (1252, 636), (1340, 672), (1470, 676), (1572, 640), (1604, 566), (1560, 492), (1490, 524), (1410, 540), (1330, 526)])
torso = fillp([(1010, 1130), (1040, 860), (1086, 730), (1170, 650), (1270, 612), (1340, 590), (1490, 590), (1560, 612), (1660, 650), (1750, 730), (1800, 860), (1840, 1130)])
arm = fillp([(1086, 730), (1010, 810), (930, 880), (880, 905), (880, 955), (960, 960), (1060, 930), (1150, 860)])
# loose hair breaks the outline, so the head does not read as a shape
tuft = noise((H, W), 1.1, 7) - 0.5
head = smooth(0.42, 0.58, gauss(head, 4) + tuft * 0.5 * smooth(470, 340, yy))
all_m = np.clip(head + neck + hood + torso + arm, 0, 1)


def edge(m, r, d):
    # light that wraps in from one side: how far in from the edge, and whether that edge faces the light
    g = gauss(m, r)
    gy, gx = np.gradient(g)
    nrm = np.hypot(gx, gy) + 1e-5
    d = np.array(d, np.float32)
    d /= np.linalg.norm(d)
    return np.clip(m * (1 - smooth(0.5, 0.98, g)) * ((-gx / nrm) * d[0] + (-gy / nrm) * d[1]), 0, 1)


hairline = smooth(250, 360, yy)
skinm = head * (1 - hood)
tex = gauss(noise_raw((H, W), 3.0, 5), 3)
fill = all_m[..., None] * (np.array([0.016, 0.013, 0.012], np.float32) + (tex * 0.02)[..., None])
cheek = edge(skinm, 42, (-0.9, -0.15)) * hairline
lit = fill + (cheek ** 1.3)[..., None] * rgb("#E8A67C") * BULB * 3.4
lit = lit + edge(all_m, 7, (-0.7, -0.7))[..., None] * BULB * 0.95
lit = lit + edge(all_m, 5, (0.1, -1.0))[..., None] * RED * 0.5
lit = lit + edge(all_m, 6, (0.95, -0.3))[..., None] * GRN * 0.8
lit = lit + edge(np.clip(torso + arm + hood, 0, 1), 22, (-0.6, -0.8))[..., None] * BULB * 0.3
seam = edge(hood, 4, (-0.2, 1.0)) + edge(hood, 5, (-0.5, -0.8)) * (1 - smooth(0, 1, head))
lit = lit + seam[..., None] * BULB * 0.34

img = plate * (1 - 0.45 * gauss(all_m, 40))[..., None]
# one bare lamp on a flex, a warm pool in a cold street
bx, by = 925, 262
flex = Image.new("L", wh, 0)
ImageDraw.Draw(flex).line((bx, -10, bx, by - 34), fill=255, width=3)
img = img * (1 - 0.8 * np.asarray(flex, np.float32) / 255)[..., None]
d2 = (xx - bx) ** 2 + (yy - by) ** 2
pool = np.exp(-d2 / (2 * 430 ** 2)) * 0.36 + np.exp(-d2 / (2 * 130 ** 2)) * 0.5
img = img + pool[..., None] * BULB * 0.8
core = np.clip(1.4 - np.sqrt(((xx - bx) / 26) ** 2 + ((yy - by) / 34) ** 2), 0, 1)
img = img + gauss(core, 2)[..., None] * rgb("#FFF0D0") * 2.2
# table edge, catching the bulb
tb = gauss(((yy > 930 + xx * 0.02) & (xx < 1040)).astype(np.float32), 1.0)
tbc = np.array([0.05, 0.035, 0.025], np.float32) + (np.exp(-(((xx - 640) / 420) ** 2)) * np.exp(-((yy - 950) / 70) ** 2))[..., None] * BULB * 0.55
img = img * (1 - tb)[..., None] + tb[..., None] * tbc

a = gauss(all_m, 1.0)
lit = gauss(lit, 0.8)
img = img * (1 - a)[..., None] + lit * a[..., None]
img = subtitle(img, ["How can computer-aided methods help scientists find", "and assess potential cancer drug candidates?"], 1040, 46)
finish(img, "T2.png", 0.6)
print("done", time.time() - t0)
