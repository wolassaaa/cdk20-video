"""Post for the SPLAT test (numpy + PIL only; deterministic, nothing varies per frame except the picture).
  - bloom (three Gaussian scales of the highlights)
  - palette guard for red-dominant pixels: G < 0.35 R, B <= 1.3 G (red may not drift to pink), blue-over-red never reads purple
  - stage black #060606, type layers composited at the end (layers that are not the frame's size are resampled to it)
python post.py --src FRAMES_DIR --dst OUT_DIR --work WORKDIR [--frames a-b] [--stills 10,20]
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True); ap.add_argument("--dst", required=True); ap.add_argument("--work", required=True)
ap.add_argument("--frames", default="0-299"); ap.add_argument("--stills", default=""); ap.add_argument("--step", type=int, default=1)
ap.add_argument("--no_type", type=int, default=0); ap.add_argument("--jpg", type=int, default=0)
A = ap.parse_args()
os.makedirs(A.dst, exist_ok=True)


def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2s(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 1e-9), 1 / 2.4) - 0.055)


def load_layer(name):
    a = np.asarray(Image.open(os.path.join(A.work, name))).astype(np.float32) / 255
    return a


NUM, SUB, SRC = None, None, None
if not A.no_type:
    NUM = load_layer("type_num.png"); SUB = load_layer("type_sub.png"); SRC = load_layer("type_src.png")
FIT = {}


def fit(layer, h, w):
    """type layers come from Remotion at 1920x1080 (or --scale=2): resample once per frame size, PIL premultiplies RGBA for this."""
    if layer.shape[:2] == (h, w): return layer
    key = (id(layer), h, w)
    if key not in FIT:
        im = Image.fromarray(np.uint8(np.clip(layer, 0, 1) * 255 + 0.5)).resize((w, h), Image.LANCZOS)
        FIT[key] = np.asarray(im).astype(np.float32) / 255
    return FIT[key]


def sstep(a, b, x):
    x = min(1.0, max(0.0, (x - a) / (b - a))); return x * x * (3 - 2 * x)


def box1(a, r, axis):
    pad = [(0, 0)] * a.ndim; pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = 2 * r + 1
    hi = np.take(c, np.arange(n, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - n), axis=axis)
    return ((hi - lo) / n).astype(np.float32)


def blur(lin, sigma):
    """three box passes = a good gaussian, float precision (PIL's blur has no float mode)"""
    r = max(1, int(round((np.sqrt(4 * sigma * sigma + 1) - 1) / 2)))
    x = lin
    for _ in range(3):
        x = box1(box1(x, r, 0), r, 1)
    return x


def grade(rgb8):
    h, w, _ = rgb8.shape
    lin = s2l(rgb8.astype(np.float32) / (65535.0 if rgb8.dtype == np.uint16 else 255.0)).astype(np.float32)
    # bloom works at half size (faster, smoother)
    small = lin[::2, ::2]
    # bloom from bright *neutral* light only (luma keeps the reds from turning neon)
    luma = (0.2126 * small[..., 0] + 0.7152 * small[..., 1] + 0.0722 * small[..., 2])[..., None]
    hi = small * np.clip((luma - 0.28) / 0.5, 0, 1)
    b = blur(hi, 3) * 0.30 + blur(hi, 10) * 0.26 + blur(hi, 30) * 0.16
    bl = np.repeat(np.repeat(b, 2, axis=0), 2, axis=1)[:h, :w]
    bl = blur(bl, 1.5)
    x = lin + np.maximum(bl, 0.0)
    # --- palette guard, in display space, where the rule is written
    s = l2s(np.clip(x, 0, 1)).astype(np.float32)
    R, G, B = s[..., 0], s[..., 1], s[..., 2]
    # bluish-red overlaps first: if R and B both beat G, the pixel is purple; send it to whichever is stronger
    pur = np.clip((np.minimum(R, B) - G * 1.25) / np.maximum(np.maximum(R, B), 1e-4) * 2.5, 0, 1)
    tored = R > B
    R = np.where(tored, R, R * (1 - pur) + (0.22 * B) * pur)
    B = np.where(tored, B * (1 - pur) + (1.25 * G) * pur, B)
    # stage: lift to #060606 by screen so the blacks match the rest of the film
    bg = 6 / 255
    s = 1 - (1 - np.stack([R, G, B], -1)) * (1 - bg)
    R, G, B = s[..., 0], s[..., 1], s[..., 2]
    # red rule last, so the delivered pixel obeys it: G < 0.35 R, B <= 1.3 G. Bone seen through red must not go pink.
    t = np.clip((R / np.maximum(np.maximum(G, B), 1e-4) - 1.18) / (1.60 - 1.18), 0, 1)
    red = t * t * (3 - 2 * t) * np.clip((R - bg) / 0.06, 0, 1)
    G2 = np.minimum(G, 0.33 * R); B2 = np.minimum(B, 1.20 * G2)
    s = np.stack([R, G * (1 - red) + G2 * red, B * (1 - red) + B2 * red], -1)
    return s


def over(s, layer, op):
    if op <= 0: return s
    a = layer[..., 3:] * op
    return s * (1 - a) + layer[..., :3] * a


def process(f):
    fp = os.path.join(A.src, "f_%04d.png" % f)
    if not os.path.exists(fp): return False
    im = Image.open(fp)
    arr = np.asarray(im)
    if arr.ndim == 3 and arr.shape[2] == 4: arr = arr[..., :3]
    s = grade(arr)
    if not A.no_type:
        h, w = s.shape[:2]
        s = over(s, fit(NUM, h, w), sstep(236, 262, f))
        s = over(s, fit(SUB, h, w), sstep(250, 272, f))
        s = over(s, fit(SRC, h, w), sstep(262, 284, f))
    out = np.uint8(np.clip(s, 0, 1) * 255 + 0.5)
    Image.fromarray(out).save(os.path.join(A.dst, "f_%04d.%s" % (f, "jpg" if A.jpg else "png")), quality=93)
    return True


if A.stills:
    frames = [int(x) for x in A.stills.split(",")]
else:
    a, b = A.frames.split("-"); frames = range(int(a), int(b) + 1, A.step)
n = 0
for f in frames:
    n += process(f)
print("processed", n)
