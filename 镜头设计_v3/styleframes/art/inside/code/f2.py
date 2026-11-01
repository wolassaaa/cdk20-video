"""HKBU SCIE1007 coursework science video. Direction inside, F2 (script 2-02): a person asks the question, and the road map shows the film has not left the start.
The figure is a flat stand-in, not a fake close-up. Real phone footage replaces the whole porthole, see 方向说明.md."""
from ilib import *

CX, CY, R = 1590, 540, 770     # the porthole: a very big circle, so its edge reads as a wall

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d_ = np.hypot(xx - CX, yy - CY) - R
inside = np.clip(.5 - d_, 0, 1)

rgb = crowd(seed=9, keep=lambda x, y: np.hypot(x - CX, y - CY) > R - 60)
rgb = dim(rgb, box(0, 0, 900, H, 80), .62)

# stand-in plate. Footage goes here at full frame. A dashed outline, so nobody takes it for a person
plate = np.broadcast_to(KLEIN * .34, (H, W, 3)).copy()


def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def rbox(cx, cy, hw, hh, r):
    qx, qy = np.abs(xx - cx) - hw + r, np.abs(yy - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


PX = 1400
head = np.hypot(xx - PX, (yy - 400) * .84) - 92
neck = rbox(PX, 540, 40, 60, 10)
body = rbox(PX, 900, 240, 310, 110)
fig = smin(smin(head, neck, 16), body, 34)
a = np.clip(.5 - fig, 0, 1)[..., None]
plate = plate * (1 - a) + KLEIN * .62 * a
th = np.arctan2(yy - 640, xx - PX)
dash = np.clip((np.sin(th * 90) + .1) * 5, 0, 1)
ln = (np.clip(2.5 - np.abs(fig), 0, 1) * dash)[..., None]
plate = plate * (1 - ln) + BONE * ln
rgb = rgb * (1 - inside[..., None]) + plate * inside[..., None]

# wall of the porthole: a double row of plain beads
ss = 3
im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).resize((W * ss, H * ss), Image.BICUBIC)
d = ImageDraw.Draw(im)
for rr, off, c in ((R + 15, 0, BONE), (R - 15, .5, BONE)):
    n = int(2 * np.pi * rr / 25)
    for i in range(n):
        th = (i + off) / n * 2 * np.pi
        x, y = CX + rr * np.cos(th), CY + rr * np.sin(th)
        if -30 < x < W + 30 and -30 < y < H + 30:
            q = 11 * ss
            d.ellipse((x * ss - q - 6, y * ss - q - 6, x * ss + q + 6, y * ss + q + 6), fill=(0, 0, 0))
            d.ellipse((x * ss - q, y * ss - q, x * ss + q, y * ss + q), fill=rgb8(c))
rgb = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255

# small road: flow stops before the first station
xs = [190, 300, 410, 520, 630, 740]
rgb = road(rgb, xs, 944, ["todo"] * 6, flow_to=150, r_st=20, r_b=5, gap=15, wave=3, x_start=96, x_end=790)

im = to_pil(rgb)
f = serif(74)
lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
for i, l in enumerate(lines):
    text(im, (96, 290 + i * 90), l, f, anchor="ls")
tag(im, (96, 72), "schematic", "schematic", size=30, bg=NIGHT)
save(im, "F2.png")
