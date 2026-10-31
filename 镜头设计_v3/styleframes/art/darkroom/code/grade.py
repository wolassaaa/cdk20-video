"""HKBU SCIE1007 coursework science video. One grade for the darkroom direction: takes linear float dumps from Blender, adds lens halation, a film-style shoulder per channel, and a fixed dither. Nothing here varies by frame."""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
WORK = os.path.join(ROOT, "_work")
STILLS = os.path.join(ROOT, "stills")


def gauss(a, sigma):
    h, w = a.shape[:2]
    fy, fx = np.fft.fftfreq(h)[:, None], np.fft.rfftfreq(w)[None, :]
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    return np.stack([np.fft.irfft2(np.fft.rfft2(a[..., c]) * k, s=(h, w)) for c in range(a.shape[2])], -1)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def shoulder(x, ev=1.0):
    """Exposure then a soft shoulder per channel, so a red lamp burns through orange before it reaches white, the way paper and film do."""
    return 1 - np.exp(-np.maximum(x, 0) * ev)


def halation(a, thr=0.55, tint=(1.0, 0.55, 0.45), amt=(0.16, 0.10)):
    hi = np.maximum(a - thr, 0)
    return a + (gauss(hi, 5) * amt[0] + gauss(hi, 26) * amt[1]) * np.array(tint)


def vignette(h, w, amt=0.28):
    y, x = np.mgrid[0:h, 0:w]
    r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
    return 1 - amt * np.clip(r - 0.35, 0, 1) ** 2


def dither(h, w, amp=1.1):
    rng = np.random.default_rng(1007)
    return rng.uniform(-amp, amp, (h, w, 3)) / 255


def finish(lin, ev=1.0, tint=(1.0, 0.55, 0.45), thr=0.55, vig=0.28):
    h, w = lin.shape[:2]
    a = halation(lin * vignette(h, w, vig)[..., None], thr=thr, tint=tint)
    out = srgb(shoulder(a, ev)) + dither(h, w)
    return np.clip(out, 0, 1)


def save(arr, name, size=(1920, 1080)):
    im = Image.fromarray((arr * 255 + 0.5).astype(np.uint8))
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    p = os.path.join(STILLS, name + ".png")
    im.save(p)
    print("wrote", p, im.size)


if __name__ == "__main__":
    name = sys.argv[1]
    ev = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    lin = np.load(os.path.join(WORK, name + ".npy")).astype(np.float64)
    tint = (0.5, 0.65, 1.0) if name.startswith("t4") else (1.0, 0.55, 0.45)
    save(finish(lin, ev, tint), name + ("_test" if len(sys.argv) > 3 else ""), (lin.shape[1], lin.shape[0]))
