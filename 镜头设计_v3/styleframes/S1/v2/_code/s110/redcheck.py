"""Orange check: among red pixels (R>110, R>1.6*B, R>1.6*G... loosely: R dominant), share whose G > 0.35 R."""
import sys, numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGB")).astype(float)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    red = (R > 110) & (R > 1.5 * B) & (R > 1.3 * G)
    n = red.sum()
    if n < 200: print(f"{f.split('/')[-1]:28s} red px {n:7d}  (n/a)"); continue
    org = red & (G > 0.35 * R) & (G > 1.25 * B)  # G well above B = orange; G≈B = pink/white highlight
    print(f"{f.split('/')[-1]:28s} red px {n:7d}  orange {100*org.sum()/n:5.1f}%  median G/R {np.median(G[red]/R[red]):.2f}")
