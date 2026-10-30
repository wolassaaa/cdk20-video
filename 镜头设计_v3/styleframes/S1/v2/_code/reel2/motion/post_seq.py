"""Post for the fontana frame sequence: exactly w0/post.py defaults (bloom 0.6 @ 0.55, vignette 0.25, grain 0.04, tonemap),
except the grain seed follows the frame so the print grain lives instead of sitting still on a moving canvas,
then the reel's blood-red recolour (reel/py/recolor.py, --hue 2.5, as reel/py/recolor_all.sh does for the v1 fontana stills).
python post_seq.py RAWDIR OUTDIR [--jpg 93] [--sheet sheet.jpg]
"""
import os, sys, glob, argparse, zlib
sys.path.insert(0, "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/w0")
import numpy as np
from PIL import Image
from sf import bloom, vignette, grain, tonemap, W, H


def recolor(a, hue=2.5, pull=0.6, val=0.93):
    """same maths as reel/py/recolor.py: red-dominant pixels move to blood red #E8190F, keep value/saturation shape."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    rp = lambda x, a0, a1: np.clip((x - a0) / (a1 - a0), 0, 1)
    wh = np.where(h >= 330, 1, np.where(h >= 300, rp(h, 300, 330), np.where(h <= 12, 1, 1 - rp(h, 12, 25))))
    w = wh * rp(s, 0.12, 0.3)
    s2 = s + (0.935 - s) * pull * (s < 0.935)
    v = mx * val; lo = v * (1 - s2); f = hue / 60
    new = np.stack([v, lo + (v - lo) * f, lo], -1)
    return a * (1 - w[..., None]) + new * w[..., None]

ap = argparse.ArgumentParser()
ap.add_argument("raw"); ap.add_argument("out"); ap.add_argument("--jpg", type=int, default=93); ap.add_argument("--sheet", default="")
ap.add_argument("--grain", type=float, default=0.04)  # 0 since 10-30: the director found moving grain flickery
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)
files = sorted(glob.glob(os.path.join(A.raw, "*.png")))
thumbs = []
for i, f in enumerate(files):
    a = np.asarray(Image.open(f), np.float32)
    a = a / (65535.0 if a.max() > 255 else 255.0)
    img = a[..., :3]
    if img.shape[1] != W: img = np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS), np.float32) / 255
    img = bloom(img, sig=(4, 18, 60), gain=(0.18, 0.15, 0.132), thresh=0.55)
    img = vignette(img, 0.25)
    name = os.path.splitext(os.path.basename(f))[0]
    if A.grain: img = grain(img, A.grain, seed=1000 + (zlib.crc32(name.encode()) % 100000))
    img = tonemap(img)
    img = recolor(np.round(np.clip(img, 0, 1) * 255) / 255)
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    im.save(os.path.join(A.out, name + ".jpg"), quality=A.jpg, subsampling=0)
    thumbs.append((name, im.resize((480, 270))))
    print("post", name)
if A.sheet:
    from PIL import ImageDraw
    n = len(thumbs); cols = 4; rows = (n + cols - 1) // cols
    sh = Image.new("RGB", (cols * 480, rows * 290), (20, 20, 20)); d = ImageDraw.Draw(sh)
    for k, (nm, t) in enumerate(thumbs):
        x, y = (k % cols) * 480, (k // cols) * 290
        sh.paste(t, (x, y + 20)); d.text((x + 4, y + 4), nm, fill=(220, 220, 220))
    sh.save(A.sheet, quality=88)
