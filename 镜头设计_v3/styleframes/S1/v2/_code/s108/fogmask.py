"""Masks for the fogged-glass pane (white = wiped clear). 3200x1800 maps to the 16x9 pane; camera sees ~px 650..2550 x 365..1435.
python fogmask.py out_dir"""
import sys, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out = sys.argv[1]
Wm, Hm = 3200, 1800
rnd = random.Random(3)


def finish(img, seed):
    r = random.Random(seed)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
    # drips: from the lower edge of wiped strokes, thin clear runs downward
    ys, xs = np.nonzero(a > 0.8)
    d = ImageDraw.Draw(img)
    for _ in range(38):
        k = r.randrange(len(xs)); x, y = int(xs[k]), int(ys[k])
        L = r.randint(60, 320); w = r.randint(4, 9)
        pts = [(x + math.sin(t / 40 + seed) * 3, y + t) for t in range(0, L, 6)]
        d.line(pts, fill=255, width=w)
        d.ellipse([x - w, y + L - w, x + w, y + L + w], fill=255)
    img = img.filter(ImageFilter.GaussianBlur(2.2))
    a = np.asarray(img, dtype=np.float32) / 255
    # condensation droplets: tiny clear dots in the fog
    rng = np.random.default_rng(seed)
    dots = Image.new("L", (Wm, Hm), 0); dd = ImageDraw.Draw(dots)
    for _ in range(9000):
        x, y = rng.uniform(0, Wm), rng.uniform(0, Hm); rr = rng.uniform(1, 4.5) ** 1.3
        dd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(rng.uniform(120, 255)))
    b = np.asarray(dots.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
    # low-frequency unevenness of the fog
    n = rng.random((18, 32)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((Wm, Hm), Image.BICUBIC), dtype=np.float32) / 255
    m = np.clip(np.maximum(a, b * 0.55) + n * 0.12, 0, 1)
    return Image.fromarray((m * 255).astype(np.uint8))


# --- time: "2006 -> 2026" written with a finger
img = Image.new("L", (Wm, Hm), 0); d = ImageDraw.Draw(img)
f = ImageFont.truetype("C:/Windows/Fonts/segoeprb.ttf", 205)
txt = "2006 \u2192 2026"
bb = d.textbbox((0, 0), txt, font=f)
x0 = (Wm - (bb[2] - bb[0])) // 2; y0 = 640
for k in range(3):  # finger is fat: stroke the text a bit
    d.text((x0 + rnd.uniform(-2, 2), y0 + rnd.uniform(-2, 2)), txt, font=f, fill=255, stroke_width=9, stroke_fill=255)
f2 = ImageFont.truetype("C:/Windows/Fonts/segoeprb.ttf", 120)
d.text((x0 + 40, y0 + 330), "US$2.8B", font=f2, fill=255, stroke_width=6, stroke_fill=255)
finish(img, 11).save(f"{out}/fog_time.png")

# --- tally: ten finger strokes; the 7th lines up with the red light behind the glass
img = Image.new("L", (Wm, Hm), 0); d = ImageDraw.Draw(img)
for i in range(10):
    x = 1730 + (i - 6) * 112 + rnd.uniform(-8, 8)
    y0, y1 = 760 + rnd.uniform(-20, 20), 1040 + rnd.uniform(-20, 20)
    tilt = rnd.uniform(-22, 10)
    pts = [(x + tilt * (t / 20) + math.sin(t / 3) * 2, y0 + (y1 - y0) * t / 20) for t in range(21)]
    d.line(pts, fill=255, width=46, joint="curve")
    d.ellipse([pts[0][0] - 23, pts[0][1] - 23, pts[0][0] + 23, pts[0][1] + 23], fill=255)
    d.ellipse([pts[-1][0] - 23, pts[-1][1] - 23, pts[-1][0] + 23, pts[-1][1] + 23], fill=255)
finish(img, 12).save(f"{out}/fog_tally.png")
print("ok")
