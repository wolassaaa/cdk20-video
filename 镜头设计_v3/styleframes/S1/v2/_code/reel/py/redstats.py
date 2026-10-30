"""Red check for reel plates: among red-dominant pixels (R > 0.25, R > 1.6*max(G,B)), report hue spread.
pink = hue in 300..355 deg (B > G); orange = G > 0.35 R. Usage: python redstats.py a.png b.png ..."""
import sys, numpy as np
from PIL import Image
def stats(p):
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 0.25) & (r > 1.6 * np.maximum(g, b))
    n = int(m.sum())
    if n == 0: return f"{p}: no red"
    R, G, B = r[m], g[m], b[m]
    pink = float(((B > G * 1.15) & (B > 0.04 * R)).mean())  # visibly B-heavy
    orange = float((G > 0.35 * R).mean())
    return f"{p.split('/')[-1]:32s} n={n:8d} medG/R={np.median(G/R):.3f} medB/R={np.median(B/R):.3f} pinkfrac={pink:.3f} orangefrac={orange:.4f}"
for p in sys.argv[1:]: print(stats(p))
