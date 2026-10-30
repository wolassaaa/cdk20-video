"""Batch version of _code/reel/py/recolor.py: pull every red-dominant pixel of the sequence to blood red #E8190F
(hue 2 deg, saturation pulled fully to 0.935 so the grain overlay cannot lift it to pink, full weight from s=0.2), so salmon/pink highlights on the red glass read as blood red, blues untouched.
python recolor_seq.py SRC_DIR DST_DIR"""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bench"))
from png16 import read_png16

HUE, PULL, VAL = 2.0, 1.0, 0.93


def ramp(x, a0, a1): return np.clip((x - a0) / (a1 - a0), 0, 1)


def recolor(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    wh = np.where(h >= 330, 1, np.where(h >= 300, ramp(h, 300, 330), np.where(h <= 12, 1, 1 - ramp(h, 12, 25))))
    w = wh * ramp(s, 0.08, 0.2)
    s2 = s + (0.935 - s) * PULL * (s < 0.935)
    v = mx * VAL; lo = v * (1 - s2)
    new = np.stack([v, lo + (v - lo) * HUE / 60, lo], -1)
    return a * (1 - w[..., None]) + new * w[..., None]


src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
fs = sorted(f for f in os.listdir(src) if f.endswith(".png"))
for i, f in enumerate(fs):
    p = os.path.join(src, f); a = read_png16(p)   # organs.py writes 8-bit today; a 16-bit source keeps its bits up to the recolour
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255 if a is None else a[..., :3]
    Image.fromarray(np.clip(recolor(a) * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(dst, f), compress_level=1)
    if i % 50 == 0: print(i, f, flush=True)
print("done", len(fs))
