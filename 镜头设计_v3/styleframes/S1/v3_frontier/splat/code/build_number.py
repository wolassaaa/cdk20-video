"""Sample the glyph mask of "1,412" into splat target pixels.  python build_number.py type_num.png number.npz"""
import sys
import numpy as np
from PIL import Image

mask, out = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(mask))[..., 3].astype(np.float32) / 255
rng = np.random.default_rng(1412)
SP = 1.15
ys, xs = np.mgrid[360:620:SP, 120:740:SP]
px = xs.ravel() + rng.uniform(-0.3, 0.3, xs.size)
py = ys.ravel() + rng.uniform(-0.3, 0.3, xs.size)
v = a[np.clip(py.astype(int), 0, 1079), np.clip(px.astype(int), 0, 1919)]
keep = v > 0.5
px, py = px[keep], py[keep]
print("glyph px", int((a > 0.5).sum()), "splats", len(px))
np.savez(out, px=px.astype(np.float32), py=py.astype(np.float32))
