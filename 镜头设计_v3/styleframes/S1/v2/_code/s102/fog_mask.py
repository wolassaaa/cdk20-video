"""Wipe mask for the 1-02 'fog' option: 1,412 tally marks (283 groups) drawn with a fingertip on a fogged pane,
plus the number '1,412' written the same way. White = wiped (clear glass), black = fog. Small drips run down
from some strokes. 3840x2160 (UV of the pane in fog_glass.py).

python fog_mask.py <out.png> [drips=1.0]
"""
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = sys.argv[1]
DRIPS = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0   # v2 uses ~3: more and longer runs
COUNT = 1412
W, H = 3840, 2160
rnd = random.Random(1412)
m = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(m)


def finger(p0, p1, w):
    """A fingertip stroke: wider at the press, tapering a little toward the lift, wobbly."""
    n = 14
    pts = []
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t + rnd.uniform(-1.5, 1.5)
        y = p0[1] + (p1[1] - p0[1]) * t + rnd.uniform(-1.5, 1.5)
        pts.append((x, y, w * (1.08 - 0.28 * t)))
    for (x0, y0, w0), (x1, y1, w1) in zip(pts, pts[1:]):
        d.line([(x0, y0), (x1, y1)], fill=255, width=int(w0))
        d.ellipse([x1 - w1 / 2, y1 - w1 / 2, x1 + w1 / 2, y1 + w1 / 2], fill=255)
    x, y, w0 = pts[0]
    d.ellipse([x - w0 * 0.6, y - w0 * 0.6, x + w0 * 0.6, y + w0 * 0.6], fill=255)  # the press
    return pts[-1] if p1[1] > p0[1] else pts[0]


def drip(x, y, w):
    L = rnd.uniform(40, 220) * (1 + 0.6 * (DRIPS - 1))
    xs = x
    for k in range(int(L)):
        xs += rnd.uniform(-0.5, 0.5)
        d.ellipse([xs - w / 2, y + k - w / 2, xs + w / 2, y + k + w / 2], fill=255)
    r = w * 1.15
    d.ellipse([xs - r, y + L - r, xs + r, y + L + r], fill=255)


# ---- tally field: 31 columns x 10 rows (283 groups = 9 full rows + 4), upper ~70% of the pane
COLS, PX, PY, X0, Y0 = 31, 112, 124, 200, 110
GW, GH, FW = 64, 92, 10
groups = math.ceil(COUNT / 5)
for g in range(groups):
    r, c = divmod(g, COLS)
    x, y = X0 + c * PX + rnd.uniform(-6, 6), Y0 + r * PY + rnd.uniform(-5, 5)
    sk = rnd.uniform(-0.12, 0.12)   # each group leans its own way
    n = min(5, COUNT - g * 5)
    for k in range(n):
        if k < 4:
            bx = x + k * GW / 3.3
            p0 = (bx + rnd.uniform(-3, 3), y + rnd.uniform(-6, 6))
            p1 = (bx + sk * GH + rnd.uniform(-4, 4), y + GH + rnd.uniform(-6, 6))
            end = finger(p0, p1, FW * rnd.uniform(0.85, 1.15))
            if rnd.random() < 0.06 * DRIPS: drip(end[0], end[1], FW * 0.35 * (1.3 if DRIPS > 1 else 1))
        else:
            finger((x - 14, y + GH * 0.8 + rnd.uniform(-8, 8)), (x + GW + 12, y + GH * 0.2 + rnd.uniform(-8, 8)), FW * 0.95)

# ---- the number, written with the same finger, lower left, under the last (unfinished) group
font = ImageFont.truetype("C:/Windows/Fonts/segoepr.ttf", 400)
t = Image.new("L", (W, H), 0)
ImageDraw.Draw(t).text((560, 1930), "1,412", font=font, fill=255, anchor="ls")
t = t.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 90 else 0)
m = ImageChops.lighter(m, t)
d = ImageDraw.Draw(m)
for _ in range(int(7 * DRIPS)):   # drips off the numerals
    bbox = t.getbbox()
    for _try in range(200):
        x = rnd.uniform(bbox[0], bbox[2]); y = rnd.uniform(bbox[1] + 200, bbox[3])
        if t.getpixel((int(x), int(y))) > 0 and t.getpixel((int(x), int(y) + 12)) == 0:
            drip(x, y + 6, 6); break

# soft wet edge: slight blur, then a ragged threshold with fine noise
m = m.filter(ImageFilter.GaussianBlur(2.2))
noise = Image.effect_noise((W, H), 40).filter(ImageFilter.GaussianBlur(1))
m = ImageChops.add(m, ImageChops.subtract(noise, Image.new("L", (W, H), 128)))
m = m.point(lambda v: 0 if v < 70 else (255 if v > 170 else int((v - 70) * 2.55)))
m.save(OUT)
print("groups", groups, "->", OUT)
