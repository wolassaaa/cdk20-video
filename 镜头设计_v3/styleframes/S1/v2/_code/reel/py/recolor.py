"""Move the crimson/pink reds of the earlier Blender plates to blood red (#E8190F, hue ~3 deg) for the reel.
Only red-dominant pixels move: hue weight 1 in [330, 360) U [0, 12], fading to 0 at 300 and 25 deg; saturation weight
fades in from s=0.12 to s=0.3, so greys, bone, skin-free highlights and every blue stay as they were. Value and saturation are kept.
python recolor.py SRC DST [--sat 1.0]"""
import sys, argparse, numpy as np
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--sat", type=float, default=1.0)
ap.add_argument("--hue", type=float, default=3.0)
ap.add_argument("--pull", type=float, default=0.6, help="pull saturation toward blood red s=0.935 (0 = keep)")
ap.add_argument("--val", type=float, default=0.93, help="value scale on moved pixels (blood red is not full-value)")
A = ap.parse_args()
im = Image.open(A.src); mode = im.mode
a = np.asarray(im.convert("RGB"), np.float32) / 255
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-6
h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
def ramp(x, a0, a1): return np.clip((x - a0) / (a1 - a0), 0, 1)
wh = np.where(h >= 330, 1, np.where(h >= 300, ramp(h, 300, 330), np.where(h <= 12, 1, 1 - ramp(h, 12, 25))))
w = wh * ramp(s, 0.12, 0.3)
s2 = np.clip(s * A.sat, 0, 1); s2 = s2 + (0.935 - s2) * A.pull * (s2 < 0.935)
v = mx * A.val; lo = v * (1 - s2); f = A.hue / 60
new = np.stack([v, lo + (v - lo) * f, lo], -1)
out = a * (1 - w[..., None]) + new * w[..., None]
Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(A.dst)
print(f"{A.src.split('/')[-1]}: moved {(w > 0.5).mean() * 100:.1f}% of pixels")
