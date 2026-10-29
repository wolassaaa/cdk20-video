"""Post for option 3: adds the condensation sparkle the render cannot resolve at 1080p (beads 1-4 px),
gated by the same fog mask the glass used; then grain, bloom and (1-01) A's card.
python fog_post.py SHOT OUT.png
"""
import sys
import numpy as np
from PIL import Image
from sf import *

x, y = grid()
RAW = SCRATCH + "raw/"


def droplets(density, rmin, rmax, seed, mask):
    r = np.random.default_rng(seed)
    hi = np.zeros((H, W), np.float32); dk = np.zeros((H, W), np.float32)
    n = int(W * H * density)
    xs = r.uniform(0, W, n); ys = r.uniform(0, H, n); rs = r.uniform(rmin, rmax, n)
    for cx, cy, rad in zip(xs, ys, rs):
        if mask[int(cy), int(cx)] < r.random(): continue
        R = int(rad + 3)
        x0, x1 = int(max(0, cx - R)), int(min(W, cx + R)); y0, y1 = int(max(0, cy - R)), int(min(H, cy + R))
        if x1 <= x0 or y1 <= y0: continue
        dx = x[y0:y1, x0:x1] - cx; dy = y[y0:y1, x0:x1] - cy
        d = np.sqrt(dx * dx + dy * dy)
        body = np.clip(rad - d, 0, 1)
        dk[y0:y1, x0:x1] = np.maximum(dk[y0:y1, x0:x1], body * np.clip(d / rad, 0, 1) ** 2)
        hd = np.sqrt((dx + rad * 0.35) ** 2 + (dy + rad * 0.35) ** 2)
        hi[y0:y1, x0:x1] += np.clip(1 - hd / (rad * 0.32 + 0.6), 0, 1) * body
    return hi, dk


shot, out = sys.argv[1], sys.argv[2]
img = np.asarray(Image.open(RAW + f"fog_{shot}_render.png"), np.float32)
img = img[..., :3] / (65535.0 if img.max() > 255 else 255.0)
# fog mask back to frame coordinates (texture has a 3% margin and is 2x)
F = np.asarray(Image.open(RAW + f"fog_{shot}.png"), np.float32) / 65535
th, tw = F.shape
m0x, m0y = int(round(tw * 0.03 / 1.06)), int(round(th * 0.03 / 1.06))
F = np.asarray(Image.fromarray(F[m0y: th - m0y, m0x: tw - m0x]).resize((W, H), Image.BILINEAR))
hi, dk = droplets(0.012, 0.6, 1.9, 3, np.clip(F * 1.1, 0, 1))
img = img * (1 - 0.28 * dk[..., None]) + hi[..., None] * 0.30 * np.array([0.86, 0.9, 1.0], np.float32)
# the water the finger pushed aside: a brighter, beaded rim along each clear line
S = np.clip(1 - F / np.maximum(blur(F, 10), 1e-3), 0, 1) * (blur(F, 10) > 0.3)
rim = np.clip(blur(1 - np.clip(F * 3, 0, 1), 3) - (1 - np.clip(F * 3, 0, 1)), 0, 1) * (blur(F, 20) > 0.4)
hi2, dk2 = droplets(0.02, 1.2, 3.4, 5, np.clip(rim * 5, 0, 1))
img = img * (1 - 0.5 * dk2[..., None]) + hi2[..., None] * 0.8 * BONE
img = bloom(img, sig=(4, 18, 60), gain=(0.25, 0.2, 0.18), thresh=0.5)
finish(img, out, 40 if shot == "1-01" else None, grain_amt=0.045, vig=0.35, tag=False)
