"""Orange check: among red-dominant pixels (R>60, R>1.4G, R>1.4B), report median G/R, 95th pct G/R, and % with G>0.35R.
python red_check.py a.png b.png ..."""
import sys
import numpy as np
from PIL import Image
crop = 0
args = sys.argv[1:]
if args and args[0].startswith("--x0="): crop = int(args[0][5:]); args = args[1:]   # skip the card (1-03 frames): only x >= x0
for p in args:
    a = np.asarray(Image.open(p).convert("RGB")).astype(float)[:, crop:]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 60) & (R > 1.4 * G) & (R > 1.4 * B)
    if m.sum() < 50: print(f"{p}: few red px"); continue
    gr = G[m] / R[m]
    strict = (G[m] > 0.35 * R[m]).mean() * 100
    # orange = G over 0.35R AND G above B (hue toward yellow). G>0.35R with B>=G is a desaturated pink (haze, highlight), not orange.
    org = ((G[m] > 0.35 * R[m]) & (G[m] > B[m] * 1.05)).mean() * 100
    hue = np.median((G[m] - B[m]) / R[m])
    print(f"{'FAIL' if org > 1 else 'ok  '} {p.split('/')[-1]:30s} n={m.sum():7d} medG/R={np.median(gr):.3f} med(G-B)/R={hue:+.3f} G>0.35R={strict:5.1f}% orange={org:5.2f}%")
