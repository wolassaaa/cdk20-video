"""HKBU SCIE1007 coursework science video. Scope direction, frame F6 (script 6-10): how far 048 has got, and what has not happened.
Six fields in a row. Real content where a real file exists: the CDK20 model, 001 and 048 from our docking files. Where nothing has been reported the field stays dark, on purpose.
Each ring keeps its meaning: dotted predicted, double our docking, solid measured. A hairline ring with a stroke through it means nothing to show."""
import json

from scopelib import *
from F4 import cdk_layers

R = 128
xs = [176 + 313.6 * i for i in range(6)]
y = 500
rgb = blank()

# road behind the fields
rgb = line(rgb, [(xs[3], y), (xs[5], y)], BONE, 2.4, .35)
rgb = line(rgb, [(0, y), (xs[3] - 2, y)], RED, 6)


def fit(a, xc, r, zoom=1.0):
    """Places a full-frame layer into a small field."""
    global rgb
    h = int(1080 * .92 / zoom)
    box = (W // 2 - h // 2, H // 2 - h // 2, W // 2 + h // 2, H // 2 + h // 2)
    t = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).crop(box).resize((2 * r, 2 * r), Image.LANCZOS)
    im = np.zeros((H, W, 3), np.uint8)
    x0 = int(xc - r)
    im[y - r:y + r, x0:x0 + 2 * r] = np.asarray(t)
    m = disc(x0 + r, y, r)[..., None]
    rgb = rgb * (1 - m) + im.astype(np.float32) / 255 * m


def field_black(xc, r=None):
    global rgb
    rgb = over(rgb, (0, 0, 0), disc(xc, y, r or R))


def ball_stick(name):
    """Ball and stick from the real docking file, seen face-on to the molecule's plane. Hydrogens dropped."""
    P = json.load(open(SCOPE.parents[3] / "镜头设计_v2/tests/T6_molecules/poses.json", encoding="utf8"))["poses"][name]
    el = [a[0] for a in P["atoms"]]
    xyz = np.array([a[1:] for a in P["atoms"]], float)
    heavy = np.array([e != "H" for e in el])
    c0 = xyz[heavy].mean(0)
    u, s, vt = np.linalg.svd(xyz[heavy] - c0)
    q = (xyz - c0) @ vt.T
    sc = 1.0 / np.abs(q[heavy, :2]).max()
    im, d = layer()
    cx0, cy0 = W / 2, H / 2
    pos = lambda i: ((cx0 + q[i, 0] * sc * 400) * SS, (cy0 - q[i, 1] * sc * 400) * SS)
    for b in P["bonds"]:
        i, j = b[0], b[1]
        if heavy[i] and heavy[j]:
            d.line(pos(i) + pos(j), fill=255, width=int(16 * SS))
    for i in np.where(heavy)[0]:
        x, y_ = pos(i)
        r = 25 * SS
        d.ellipse((x - r, y_ - r, x + r, y_ + r), fill=255)
    a = done(im)[..., None]
    return np.zeros((H, W, 3), np.float32) + a * RED


both, _, _, _ = cdk_layers(0)   # the composited model, red over blue, so no purple
for x, r in zip(xs[:3], (R, R + 11, R + 11)):
    field_black(x, r)
fit(both, xs[0], R, 1.42)
fit(ball_stick("001"), xs[1], R)
fit(ball_stick("048"), xs[2], R)
rgb = ring(rgb, xs[0], y, R, "dotted", w=2.4)
rgb = ring(rgb, xs[1], y, R, "double", w=2.6)
rgb = ring(rgb, xs[2], y, R, "double", w=2.6)

# station 4: only the left half has anything in it
x = xs[3]
field_black(x)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
half = disc(x, y, R) * np.clip((x - xx) / 1.2 + .5, 0, 1)
rgb = over(rgb, BLUE, half)
im, d = layer()
k = SS
d.arc(((x - R) * k, (y - R) * k, (x + R) * k, (y + R) * k), 90, 270, fill=255, width=int(3 * k))
rgb = over(rgb, BONE, done(im))
rgb = ring(rgb, x, y, R, "faint", BONE, 3, .5)
rgb = line(rgb, [(x, y - R), (x, y + R)], BONE, 2.4)


def empty(x):
    global rgb
    field_black(x)
    rgb = ring(rgb, x, y, R, "faint", BONE, 3, .5)
    a = R * .707
    rgb = line(rgb, [(x - a, y + a), (x + a, y - a)], BONE, 2, .5)


empty(xs[4])
empty(xs[5])

# station names above
names = [["Target"], ["Hit"], ["Improve"], ["Cells &", "animals"], ["Clinical trials", "1-2-3"], ["Approval"]]
for x, n in zip(xs, names):
    for i, l in enumerate(reversed(n)):
        rgb = text(rgb, l, (x, 336 - i * 50), (sans, 42, 600), BONE, anchor="ms", halo=False)

# what happened, below
rgb = text(rgb, "cells:", (xs[3], 672), 36, BONE, anchor="ms", halo=False)
rgb = text(rgb, "first tests", (xs[3], 718), 36, BONE, anchor="ms", halo=False)
rgb = text(rgb, "animals:", (xs[3], 782), 36, BONE, anchor="ms", halo=False)
rgb = text(rgb, "not reported", (xs[3], 828), 36, BONE, anchor="ms", halo=False)
rgb = text(rgb, "not reported", (xs[4], 672), 36, BONE, anchor="ms", halo=False)
rgb = text(rgb, "not reported", (xs[5], 672), 36, BONE, anchor="ms", halo=False)

# 048 stands at the lit half of station 4
bx = xs[3] - R * .5
rgb = over(rgb, (0, 0, 0), disc(bx, y, 58))
rgb = over(rgb, RED, disc(bx, y, 52))
rgb = text(rgb, "048", (bx, y + 16), (sans, 46, 600), BONE, anchor="ms", halo=False)
clean(rgb, "F6")
purple_check(rgb)
save(rgb, "F6.png")
