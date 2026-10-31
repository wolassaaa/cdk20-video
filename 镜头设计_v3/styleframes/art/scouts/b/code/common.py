"""HKBU SCIE1007 coursework science video. Small numpy helpers for the group B style scouts (light and installation looks)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from passes import load, save  # noqa: E402

W, H = 1280, 720
OUT = Path(__file__).resolve().parent.parent
FONTS = Path("C:/Windows/Fonts")
LABEL = "AlphaFold DB v6 · predicted"
SEQ = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/sequence.json"
PLDDT = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/plddt.json"
SURFACE = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/_work/cdk20_surface.npz"
PDB = r"D:/。hkbu/molecular science/镜头设计_v3/assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"


def grid():
    return np.mgrid[0:H, 0:W].astype(np.float32)


def sample(a, sx, sy):
    """Bilinear lookup of a at float pixel coords, zero outside."""
    h, w = a.shape[:2]
    ok = (sx >= 0) & (sx <= w - 1) & (sy >= 0) & (sy <= h - 1)
    x, y = np.clip(sx, 0, w - 1.001), np.clip(sy, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - x0, y - y0
    if a.ndim == 3:
        fx, fy, ok = fx[..., None], fy[..., None], ok[..., None]
    v = (a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy) + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy
    return v * ok


def view(P, zoom=1.0, at=(640, 360), src=(960, 545), rot=0.0):
    """Resample the 1920x1080 passes into 1280x720. zoom 1 matches load(scale=0.667); src is the point of the 1080p pass placed at frame pixel at."""
    y, x = grid()
    s = zoom * 0.667
    c, n = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    dx, dy = (x - at[0]) / s, (y - at[1]) / s
    sx, sy = src[0] + c * dx + n * dy, src[1] - n * dx + c * dy
    out = {k: sample(v, sx, sy) for k, v in P.items()}
    nn = out["normal"]
    if rot:  # keep camera-space normals consistent with the turned image
        nx, ny = nn[..., 0].copy(), nn[..., 1].copy()
        nn[..., 0], nn[..., 1] = c * nx - n * ny, n * nx + c * ny
    return out


def blur(a, sigma):
    """Gaussian blur through the FFT, wrap-padded so edges stay clean."""
    if a.ndim == 3:
        return np.stack([blur(a[..., i], sigma) for i in range(a.shape[2])], -1)
    pad = int(sigma * 3) + 2
    b = np.pad(a, pad, mode="edge")
    fy, fx = np.fft.fftfreq(b.shape[0])[:, None], np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    r = np.fft.irfft2(np.fft.rfft2(b) * g, s=b.shape)
    return r[pad:-pad, pad:-pad].astype(np.float32)


def noise(seed, scale, shape=(H, W), slope=2.0):
    """Static fractal noise, 0..1. scale is the largest feature in pixels."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(shape)
    fy, fx = np.fft.fftfreq(shape[0])[:, None], np.fft.rfftfreq(shape[1])[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    amp = 1 / np.maximum(f, 1 / scale) ** (slope / 2 + 0.5)
    r = np.fft.irfft2(np.fft.rfft2(n) * amp, s=shape)
    r = (r - r.min()) / (r.max() - r.min())
    return r.astype(np.float32)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.maximum(c, 1e-6), 1 / 2.4) - 0.055)


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def ramp(t, stops):
    """stops: [(pos, hex), ...] mapped in order, returns H x W x 3 in display space."""
    t = np.asarray(t)
    pos = [p for p, _ in stops]
    cols = np.stack([hexc(c) for _, c in stops])
    return np.stack([np.interp(t, pos, cols[:, i]) for i in range(3)], -1).astype(np.float32)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def text(s, name, size, xy, anchor="lm", tracking=0, variation=None, shape=(H, W)):
    """Anti-aliased text mask 0..1. tracking is extra pixels between letters."""
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    f = font(name, size)
    if variation:
        f.set_variation_by_name(variation)
    if tracking == 0:
        d.text(xy, s, 255, font=f, anchor=anchor)
    else:
        widths = [d.textlength(ch, font=f) + tracking for ch in s]
        total = sum(widths) - tracking
        x = xy[0] - (total if anchor[0] == "r" else total / 2 if anchor[0] == "m" else 0)
        for ch, w in zip(s, widths):
            d.text((x, xy[1]), ch, 255, font=f, anchor="l" + anchor[1])
            x += w
    return np.asarray(im, np.float32) / 255


def over(rgb, col, a):
    return rgb * (1 - a[..., None]) + np.asarray(col, np.float32) * a[..., None]


def dither(rgb, seed=7):
    """One static LSB of noise so the long gradients do not band."""
    n = np.random.default_rng(seed).random(rgb.shape[:2] + (1,), dtype=np.float32) - 0.5
    return rgb + n / 255


def finish(rgb, name):
    p = OUT / name
    save(dither(rgb), str(p))
    print("saved", p.name, rgb.shape)
