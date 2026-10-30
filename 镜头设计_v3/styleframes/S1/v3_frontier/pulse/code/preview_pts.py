"""quick orthographic splat preview of the point set from a few azimuths (numpy + PIL)."""
import numpy as np, sys
from PIL import Image
d = np.load(sys.argv[1]); P = d["P"]
out = []
for az in (0, 20, -25):
    a = np.radians(az)
    R = np.array([[np.cos(a), np.sin(a), 0], [-np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Q = P @ R.T
    W, H = 640, 480; img = np.zeros((H, W))
    x = (Q[:, 0] + 4) / 8 * W; y = (P[:, 2].max() + 0.4 - Q[:, 2]) / 6.0 * H * 0.9 + 20
    yy, xx = np.mgrid[-4:5, -4:5]; k = np.exp(-(xx**2 + yy**2) / 3.0)
    for xi, yi in zip(x.astype(int), y.astype(int)):
        img[yi - 4:yi + 5, xi - 4:xi + 5] += k
    out.append(np.clip(img / 1.5, 0, 1))
Image.fromarray((np.concatenate(out, 1) * 255).astype(np.uint8)).save(sys.argv[2])
