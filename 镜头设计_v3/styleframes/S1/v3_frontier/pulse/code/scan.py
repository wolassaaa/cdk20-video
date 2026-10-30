"""Scan every consecutive frame pair with the brief's metric and report spikes.
scan.py FRAMES_DIR OUT.npy  (frames named p_0000.png ...)"""
import sys, os
import numpy as np
from PIL import Image


def blur3(a, s=3.0):
    h, w = a.shape; pad = 16
    fy = np.fft.fftfreq(h + 2 * pad)[:, None]; fx = np.fft.rfftfreq(w + 2 * pad)[None, :]
    k = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(np.pad(a, pad, mode="edge")) * k, s=(h + 2 * pad, w + 2 * pad))[pad:-pad, pad:-pad]


fdir, out = sys.argv[1], sys.argv[2]
prev = None; v = []
for fr in range(300):
    a = np.asarray(Image.open(os.path.join(fdir, "p_%04d.png" % fr)).convert("L")).astype(np.float32)
    if prev is not None:
        d = (a - prev).astype(np.float64); v.append(float(np.abs(d - blur3(d)).mean()))
    prev = a
v = np.array(v); np.save(out, v)
med = np.array([np.median(v[max(0, i - 6):i + 7]) for i in range(len(v))])
print("pairs %d  whole-film mean %.3f  max %.3f at %d->%d" % (len(v), v.mean(), v.max(), v.argmax(), v.argmax() + 1))
for a, b, n in ((15, 92, "opening"), (93, 164, "the four"), (165, 240, "pull-back"), (241, 294, "landing"), (295, 298, "hold")):
    print("  %-10s frames %3d-%3d  mean %.3f  max %.3f" % (n, a, b, v[a:b + 1].mean(), v[a:b + 1].max()))
sp = np.where(v > 1.8 * med + 0.15)[0]
print("spikes (more than 1.8x local median):", [(int(i), round(float(v[i]), 2)) for i in sp] or "none")
print("seam 92->93: %.3f  (neighbours %.3f, %.3f)" % (v[92], v[91], v[93]))
