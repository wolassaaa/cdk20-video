"""brief's clean-check: mean |diff - gauss3(diff)| between consecutive frames, 8-bit. flicker.py a.png b.png [more...]"""
import sys
import numpy as np
from PIL import Image
def blur3(a, s=3.0):
    h, w = a.shape; pad = 16
    fy = np.fft.fftfreq(h + 2 * pad)[:, None]; fx = np.fft.rfftfreq(w + 2 * pad)[None, :]
    k = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(np.pad(a, pad, mode="edge")) * k, s=(h + 2 * pad, w + 2 * pad))[pad:-pad, pad:-pad]
fs = sys.argv[1:]
vals = []
for a, b in zip(fs, fs[1:]):
    A = np.asarray(Image.open(a).convert("RGB")).astype(float); B = np.asarray(Image.open(b).convert("RGB")).astype(float)
    d = (B - A).mean(2)
    hf = d - blur3(d)
    vals.append(np.abs(hf).mean())
print("hf diff: mean %.3f  max %.3f  (n=%d)" % (np.mean(vals), np.max(vals), len(vals)))
