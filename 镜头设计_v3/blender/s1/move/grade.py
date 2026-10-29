"""Heat pass -> false-colour print look (numpy + PIL only).

python grade.py IN_DIR OUT_DIR [--scale 0.5] [--frames a,b,c]
Reads heatV_/heatP_####.png (16-bit gray), writes f_####.png (RGB).

Pipeline per frame: linearise -> soft bloom of the hot range (turns into
isotherm rings once banded) -> grain (dithers the band edges, new seed every
frame) -> quantise to 26 bands -> band LUT built from the heat ramp with a
single acid fringe band between the cold (cyan) and hot (vermilion) halves ->
fine colour grain.
"""
import sys, os, glob
import numpy as np
from PIL import Image

NB = 26
COLD = [(0.00, "#060606"), (0.07, "#03171A"), (0.17, "#08454A"), (0.28, "#11949A"), (0.40, "#29F0FF")]
ACID = (0.415, 0.445, "#E8FF3A")       # one band only
HOT = [(0.445, "#FF3B1F"), (0.58, "#FF6A1A"), (0.72, "#FFB21F"), (0.86, "#FFF04A"), (1.00, "#FFFFFF")]

def hx(c): return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)

def ramp(stops, x):
    xs = [s[0] for s in stops]; cs = np.array([hx(s[1]) for s in stops])
    return np.stack([np.interp(x, xs, cs[:, k]) for k in range(3)], -1)

def build_lut():
    lut = np.zeros((NB, 3))
    for i in range(NB):
        c = (i + 0.5) / NB
        if ACID[0] <= c < ACID[1]: lut[i] = hx(ACID[2])
        elif c < ACID[0]: lut[i] = ramp(COLD, c)
        else: lut[i] = ramp(HOT, c)
    lut[0] = hx("#060606")
    return lut.astype(np.uint8)

LUT = build_lut()

def box(a, r, axis):
    if r < 1: return a
    c = np.cumsum(np.pad(a, [(r + 1, r) if ax == axis else (0, 0) for ax in range(a.ndim)], mode='edge'), axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return (hi - lo) / (2 * r + 1)

def blur(a, r):
    for _ in range(3):
        a = box(box(a, r, 0), r, 1)
    return a

def load(p):
    g = np.asarray(Image.open(p)).astype(np.float64) / 65535.0
    return np.where(g <= 0.04045, g / 12.92, ((g + 0.055) / 1.055) ** 2.4)   # sRGB -> linear heat

def grade(src, dst, seed, scale=1.0):
    # max-intensity composite of vessel and parenchyma passes
    h = np.maximum(np.maximum(load(src), load(src.replace("heatV_", "heatP_"))), load(src.replace("heatV_", "heatS_")))
    if scale != 1.0:
        H, W = h.shape
        h = np.asarray(Image.fromarray(h.astype(np.float32), 'F').resize((int(W * scale), int(H * scale)), Image.LANCZOS)).astype(np.float64)
    H, W = h.shape
    k = W / 1920.0
    # bloom: wide + tight, from the warm half only
    src_b = np.maximum(h - 0.42, 0)
    small = src_b[::4, ::4]
    wide = blur(small, max(1, int(10 * k)))
    wide = np.asarray(Image.fromarray(wide.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))
    tight = blur(src_b, max(1, int(5 * k)))
    h = h + 0.16 * wide + 0.07 * tight
    # cold glow so dark-teal veins read on black
    cg = blur(np.minimum(h, 0.42)[::4, ::4], max(1, int(6 * k)))
    h = h + 0.10 * np.asarray(Image.fromarray(cg.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))
    # grain (changes every frame): fine + clumpy
    rng = np.random.default_rng(seed)
    fine = rng.normal(0, 1, (H, W))
    clump = rng.normal(0, 1, (H // 3 + 1, W // 3 + 1))
    clump = np.asarray(Image.fromarray(clump.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))
    h = h + (0.011 * fine + 0.008 * clump) * (0.35 + np.clip(h * 2.5, 0, 1))
    b = np.clip((h * NB).astype(int), 0, NB - 1)
    rgb = LUT[b].astype(np.float64)
    rgb += rng.normal(0, 4.0, (H, W, 1))
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(dst)

if __name__ == "__main__":
    a = sys.argv[1:]
    ind, outd = a[0], a[1]
    os.makedirs(outd, exist_ok=True)
    scale = float(a[a.index("--scale") + 1]) if "--scale" in a else 1.0
    files = sorted(glob.glob(os.path.join(ind, "heatV_*.png")))
    if "--frames" in a:
        want = set(int(x) for x in a[a.index("--frames") + 1].split(","))
        files = [p for p in files if int(p[-8:-4]) in want]
    for p in files:
        n = int(p[-8:-4])
        grade(p, os.path.join(outd, "f_%04d.png" % n), seed=1000 + n, scale=scale)
    print("graded", len(files))
