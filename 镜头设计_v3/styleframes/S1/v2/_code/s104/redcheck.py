"""Red-drift check (director bans orange): over reddish pixels (R > 0.35, R > 2B), report median and p90 of G/R.
Pass if p90 G/R < 0.35.   python redcheck.py file.png [...]"""
import sys
import numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGB"), float) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 0.35) & (r > 2 * b) & (r > 1.2 * g)
    if m.sum() < 200: print(f"{'-':5} {'':>5} {'':>5} n={m.sum():7d} {f.split('/')[-1]}"); continue
    q = g[m] / r[m]
    p90 = np.percentile(q, 90)
    print(f"{'OK' if p90 < 0.35 else 'FAIL':5} {np.median(q):.2f} {p90:.2f} n={m.sum():7d} {f.split('/')[-1]}")
