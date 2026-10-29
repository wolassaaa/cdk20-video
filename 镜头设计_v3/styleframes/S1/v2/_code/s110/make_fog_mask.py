"""Finger-on-condensation mask for W1 opt fog: white = wiped (clear glass), black = fogged.
Monoline rounded strokes (thin Inter Tight dilated + blurred + thresholded), per-letter wobble, drips running down.
Also writes a drip-bead list (uv positions) for Blender droplets.
"""
import json, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

CODE = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/"
W, H = 3840, 2160
random.seed(4)
img = Image.new("L", (W, H), 0)


def word(text, y, size, x0=None):
    f = ImageFont.truetype(CODE + "fonts/InterTight.ttf", size)
    try: f.set_variation_by_axes([250])
    except Exception as e: print("var", e)
    widths = [f.getlength(c) for c in text]
    tw = sum(widths) + 0.04 * size * (len(text) - 1)
    x = (W - tw) / 2 if x0 is None else x0
    boxes = []
    for c, w in zip(text, widths):
        L = Image.new("L", (int(size * 1.6), int(size * 1.6)), 0)
        ImageDraw.Draw(L).text((size * 0.3, size * 0.1), c, font=f, fill=255)
        L = L.rotate(random.uniform(-7, 7), resample=Image.BICUBIC)
        dy = random.uniform(-0.03, 0.03) * size
        img.paste(255, (int(x - size * 0.3), int(y + dy - size * 0.1)), L)
        boxes.append((x, y + dy, w))
        x += w + 0.04 * size
    return boxes


b1 = word("WORTH", 330, 640)
b2 = word("TESTING?", 1010, 640)
a = np.array(img)
# dilate thin strokes into a finger-wide monoline
m = Image.fromarray(a).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.MaxFilter(11))
m = m.filter(ImageFilter.GaussianBlur(9))
a = (np.array(m) > 110).astype(np.float32)

# drips: from the bottom of strokes, thin trails that run down and end in a bead
dr = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(dr)
beads = []
cols = np.where(a.any(0))[0]
for k in range(15):
    x = int(random.choice(cols))
    ys = np.where(a[:, x] > 0)[0]
    if not len(ys): continue
    # choose the lower edge of a stroke
    y0 = int(ys[ys < 1400].max() if (ys < 1400).any() and random.random() < 0.45 else ys.max())
    L = random.uniform(80, 520) if y0 < 1400 else random.uniform(150, 700)
    w = random.uniform(7, 13)
    pts = []
    xx = x
    for s in range(int(L / 8)):
        xx += random.uniform(-1.2, 1.2); pts.append((xx, y0 + s * 8))
    dd.line(pts, fill=255, width=int(w))
    ex, ey = pts[-1]; r = w * 1.25
    dd.ellipse([ex - r, ey - r, ex + r, ey + r], fill=255)
    beads.append([ex / W, ey / H, r / W])
d = (np.array(dr.filter(ImageFilter.GaussianBlur(2))) > 100).astype(np.float32)
a = np.maximum(a, d)
# soft fog-edge: wiped edge re-fogs slightly (blur) and a hairline of beaded water on the stroke rims
edge = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))) / 255.0
Image.fromarray((edge * 255).astype(np.uint8)).save(CODE + "public/fog_mask.png")
json.dump(beads, open(CODE + "fog_beads.json", "w"))
print("beads", len(beads))
