"""Flicker metric from the brief: mean |d - gauss3(d)| where d = frame[t+1] - frame[t] (8-bit, all channels)."""
import numpy as np, sys, glob
from PIL import Image, ImageFilter


def gblur(a, sigma=3.0):
    """separable gaussian (sigma px, radius 3 sigma), edge-replicate, numpy only"""
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a.astype(np.float32), ((0, 0), (r, r)), mode="edge")
    o = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
    p = np.pad(o, ((r, r), (0, 0)), mode="edge")
    return sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))


def hf(a, b):
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32)
    d = b - a
    if d.ndim == 3:
        return float(np.mean([np.abs(d[..., c] - gblur(d[..., c])).mean() for c in range(d.shape[2])]))
    return float(np.abs(d - gblur(d)).mean())


if __name__ == "__main__":
    files = sorted(glob.glob(sys.argv[1]))
    a0, a1 = int(sys.argv[2]), int(sys.argv[3])
    vals = []
    for i in range(a0, a1):
        v = hf(Image.open(files[i]).convert("RGB"), Image.open(files[i + 1]).convert("RGB"))
        vals.append(v)
        print(files[i].split("/")[-1].split("\\")[-1], f"{v:.3f}")
    print(f"mean {np.mean(vals):.3f}  max {np.max(vals):.3f}")
