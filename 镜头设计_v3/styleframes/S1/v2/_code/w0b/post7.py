"""opt7 angiogram post: radiograph film on a lightbox.
python post7.py RAW.png OUT.png [--card] [--tag] [--marker]
Neutral tissue -> bone white on deep blue-black; dye stays crimson with halation; heavy clumped film grain + dust.
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "w0"))
import numpy as np
from PIL import Image
from sf import *

ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("out")
ap.add_argument("--card", action="store_true"); ap.add_argument("--tag", action="store_true")
ap.add_argument("--marker", action="store_true"); ap.add_argument("--tissue", type=float, default=0.9)
ap.add_argument("--norm", type=float, default=0); ap.add_argument("--gamma", type=float, default=1.7); ap.add_argument("--halo", type=float, default=1.0); ap.add_argument("--seed", type=int, default=3)
A = ap.parse_args()
a = np.asarray(Image.open(A.raw), np.float32); a = a / (65535.0 if a.max() > 255 else 255.0); a = a[..., :3]
R, G, B = a[..., 0], a[..., 1], a[..., 2]
neu = np.minimum(G, B) * 1.0                     # bone part (grey)
dye = np.clip(R - neu, 0, None)                  # crimson part
CRIM = hexc("E0102A")
# tissue: soft film response
p99 = A.norm if A.norm else (np.percentile(neu[neu > 0.02], 99.5) if (neu > 0.02).sum() > 100 else 1.0)
t = np.clip(neu / p99, 0, 1) ** A.gamma * A.tissue
x, y = grid()
r = np.sqrt(((x - W * 0.62) / W) ** 2 + ((y - H * 0.45) / H) ** 2)
ground = hexc("05070D") + IKB * 0.10 * np.clip(1 - 1.6 * r, 0, 1)[..., None]
# fine mottle in the film base (quantum noise feel)
mott = value_noise(W, H, 3, seed=A.seed, octaves=3)
ground = ground * (0.75 + 0.5 * mott[..., None])
img = ground * (1 - t[..., None]) + BONE * t[..., None]
# dye on top: crimson, saturates to a hotter crimson, never orange
d = np.clip(dye, 0, None)
al = np.clip(d / 0.22, 0, 1)[..., None]
dn = np.clip(d / max(np.percentile(d[d > 0.03], 98) if (d > 0.03).sum() > 50 else 1, 1e-3), 0, 1.3)[..., None]
img = img * (1 - al) + CRIM * al * (0.35 + 0.8 * dn ** 1.3)
# halation around the dye (red only)
h = fast_blur(d, 14) * 0.55 + fast_blur(d, 50) * 0.35 + fast_blur(d, 140) * 0.25
hh = np.clip(h * A.halo, 0, None)[..., None]
img[..., 1:] *= 1 - np.clip(hh, 0, 0.85)          # halation eats the cool channels: bone under the glow turns crimson, not pink
img += CRIM * hh * 0.8
# clumped grain (two scales) + dust specks
g1 = grain(np.zeros_like(img), 1.0, seed=A.seed + 10)[..., 0:1]
rng = np.random.default_rng(A.seed)
n2 = rng.standard_normal((H // 2 + 1, W // 2 + 1)).astype(np.float32)
n2 = np.asarray(Image.fromarray(n2).resize((W + 2, H + 2), Image.BILINEAR))[:H, :W][..., None]
lum = img.mean(-1, keepdims=True)
img = img + (g1 * 0.035 + n2 * 0.03) * (0.4 + 0.9 * np.sqrt(np.clip(lum, 0, 1)))
dust = (rng.random((H, W)) > 0.99996).astype(np.float32)
dust = blur(dust, 0.8) * 3.0
img = img + BONE * dust[..., None] * 0.6
if A.marker:  # radiograph lead marker
    img = ink(img, text_mask("R", 46, "Bold", xy=(1830 if not A.card else 1830, 70), anchor="ra"), BONE, 0.55)
finish(img, A.out, 40 if A.card else None, grain_amt=0.0, vig=0.35, tag=A.tag, tm=True)
