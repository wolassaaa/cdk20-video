"""Post for Blender renders: bloom, grain, optional A card (1-01), optional W0 word, optional ILLUSTRATIVE tag.
python post.py RAW.png OUT.png [--card] [--word WHICH] [--tag] [--bloom 0.6] [--grain 0.04]
"""
import argparse
import numpy as np
from PIL import Image
from sf import *

ap = argparse.ArgumentParser()
ap.add_argument("raw"); ap.add_argument("out")
ap.add_argument("--card", action="store_true")
ap.add_argument("--word", default="")
ap.add_argument("--wordpos", default="150,960")
ap.add_argument("--tag", action="store_true")
ap.add_argument("--bloom", type=float, default=0.6)
ap.add_argument("--thresh", type=float, default=0.55)
ap.add_argument("--grain", type=float, default=0.04)
ap.add_argument("--vig", type=float, default=0.25)
ap.add_argument("--lift", type=float, default=0.0, help="add BLACK*lift so pure black reads as the stage colour")
ap.add_argument("--crush", type=float, default=0.0, help="black point: subtract and rescale")
ap.add_argument("--band", type=float, default=0.0, help="print-like banding amount")
A = ap.parse_args()

im = Image.open(A.raw)
a = np.asarray(im, np.float32)
a = a / (65535.0 if a.max() > 255 else 255.0)
img = a[..., :3]
if img.shape[1] != W: img = from_pil(to_pil(img).resize((W, H), Image.LANCZOS))
if A.crush: img = np.clip((img - A.crush) / (1 - A.crush), 0, None) ** 1.08
img = np.maximum(img, BLACK * A.lift) if A.lift else img
if A.bloom:
    img = bloom(img, sig=(4, 18, 60), gain=(0.30 * A.bloom, 0.25 * A.bloom, 0.22 * A.bloom), thresh=A.thresh)
if A.band: img = posterize_band(img, 36, A.band)
if A.word:
    x, y = [int(v) for v in A.wordpos.split(",")]
    img = ink(img, text_mask(A.word, 64, "Light", tracking=12, xy=(x, y), anchor="ls", ss=2), BONE, 0.95)
finish(img, A.out, 40 if A.card else None, grain_amt=A.grain, vig=A.vig, tag=A.tag, tm=True)
