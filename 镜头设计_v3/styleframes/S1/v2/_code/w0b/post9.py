"""opt9 endoscope post: optional radial zoom blur (the rush), bloom, grain, card.
python post9.py RAW.png OUT.png [--zoom 0.08] [--card] [--tag] [--crush 0.0]
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "w0"))
import numpy as np
from PIL import Image
from sf import *
ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("out")
ap.add_argument("--zoom", type=float, default=0.0); ap.add_argument("--card", action="store_true"); ap.add_argument("--tag", action="store_true")
ap.add_argument("--crush", type=float, default=0.0); ap.add_argument("--bloom", type=float, default=0.6); ap.add_argument("--grain", type=float, default=0.04)
ap.add_argument("--iris", type=float, default=0.0); ap.add_argument("--cx", type=float, default=W / 2); ap.add_argument("--ring", type=float, default=0.0); ap.add_argument("--gain", type=float, default=1.0)
A = ap.parse_args()
im = Image.open(A.raw).convert("RGB")
img = from_pil(im) * A.gain
x, y = grid(); rr = np.sqrt((x - W / 2) ** 2 + (y - H / 2) ** 2)
lit = img.max(-1) > 0.004
R = np.percentile(rr[lit], 99.7) if lit.sum() > 1000 else 9999
circ = np.clip((R - 1.5 - rr) / 3.0, 0, 1)[..., None]      # the scope's hard image circle
if A.zoom:
    acc = np.zeros_like(img); n = 24
    for i in range(n):
        s = 1 + A.zoom * i / (n - 1)
        w2, h2 = int(W * s), int(H * s)
        z = from_pil(to_pil(img).resize((w2, h2), Image.BILINEAR))
        x0, y0 = (w2 - W) // 2, (h2 - H) // 2
        acc += z[y0:y0 + H, x0:x0 + W] * (1.0 - 0.5 * i / n)
    img = acc / sum(1.0 - 0.5 * i / n for i in range(n))
if A.iris:
    R = A.iris; rr = np.sqrt((x - A.cx) ** 2 + (y - H / 2) ** 2); circ = np.clip((R - 1.5 - rr) / 3.0, 0, 1)[..., None]
if R < 1500: img = img * circ
if A.ring:   # the scope's image circle drawn as a thin bone hairline
    img = ink(img, np.clip(1 - np.abs(rr - R) / 1.2, 0, 1), BONE, A.ring)
if A.crush: img = np.clip((img - A.crush) / (1 - A.crush), 0, None)
img = bloom(img, sig=(4, 18, 60), gain=(0.3 * A.bloom, 0.25 * A.bloom, 0.2 * A.bloom), thresh=0.5)
finish(img, A.out, 40 if A.card else None, grain_amt=A.grain, vig=0.2, tag=A.tag, tm=True)
