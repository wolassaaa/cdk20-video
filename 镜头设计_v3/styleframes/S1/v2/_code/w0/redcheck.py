"""Orange check: among clearly red pixels (R>120, R>1.6B), share with G > 0.35 R (reads orange). Card region (1-01) excluded."""
import sys, glob
import numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGB"), np.float32)
    if "1-01" in f.replace("\\", "/").split("/")[-2]: a = a[:, 980:]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    red = (R > 120) & (R > 1.6 * B) & (R > 1.3 * G)
    n = red.sum()
    bad = (red & (G > 0.35 * R)).sum()
    print(f"{f.split('/')[-1]:40s} red px {n:7d}  orange share {bad / max(n, 1):.3f}  medianG/R {np.median(G[red] / R[red]) if n else 0:.2f}")
