"""orthographic check of the thread tree over the light points."""
import numpy as np, sys
from PIL import Image, ImageDraw
d = np.load("data/points.npz"); P = d["P"]; t = np.load("data/threads.npz"); Q, par = t["pts"], t["par"]
W, H = 960, 720
a = np.radians(14); R = np.array([[np.cos(a), np.sin(a), 0], [-np.sin(a), np.cos(a), 0], [0, 0, 1]])
def pr(X):
    Y = X @ R.T; return (Y[:, 0] + 4) / 8 * W, (7.6 - Y[:, 2]) / 6 * H
im = Image.new("RGB", (W, H)); dr = ImageDraw.Draw(im)
x, y = pr(P)
for a_, b_ in zip(x, y): dr.ellipse((a_ - 1.2, b_ - 1.2, a_ + 1.2, b_ + 1.2), fill=(130, 130, 125))
x, y = pr(Q)
for i, p in enumerate(par):
    if p >= 0: dr.line((x[i], y[i], x[p], y[p]), fill=(232, 25, 15), width=1)
im.save("scratch/threads.png")
