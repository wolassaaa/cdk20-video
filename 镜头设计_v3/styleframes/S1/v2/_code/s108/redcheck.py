"""Red drift check: among reddish pixels (R>0.35, R>1.6B, R>1.6G), report median G/R and share with G>0.35R."""
import sys, numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) / 255
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 0.35) & (R > 1.6 * B) & (R > 1.6 * G)
    # also catch salmon/orange: hue between red and yellow with R high
    m2 = (R > 0.35) & (G > 0.35 * R) & (B < 0.75 * G) & (R > G * 1.15)
    n = m.sum()
    gr = np.median(G[m] / R[m]) if n else 0
    print(f"{f.split('/')[-1]:34s} red px {n:7d}  median G/R {gr:.2f}  orange-ish px {m2.sum():6d}")
