"""HKBU SCIE1007 coursework science video. Arena direction: the lighting desk and the finishing pass.

python grade.py T4 [tag] writes ../stills/T4.png (or ../_work/<shot><tag>_preview.png when a tag is given).
Each still comes out of Blender with one light group per channel. Here each channel gets the real colour of that lighting section, then bloom, a film curve and the type layer.
No grain, nothing frame-random, so the same code run over a sequence cannot flicker.
"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, "..", "_work"))
STILLS = os.path.normpath(os.path.join(HERE, "..", "stills"))


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def gauss_fft(shape, sigma):
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    return np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy)).astype(np.float32)


def blur(img, sigma):
    """Gaussian blur with mirrored edges, by FFT. No scipy on this machine."""
    h, w = img.shape[:2]
    pad = int(sigma * 3) + 1
    pad = min(pad, h - 1, w - 1)
    p = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
    G_ = gauss_fft(p.shape[:2], sigma)
    out = np.stack([np.fft.irfft2(np.fft.rfft2(p[..., i]) * G_, s=p.shape[:2]) for i in range(3)], -1)
    return out[pad:-pad, pad:-pad].astype(np.float32)


def bloom(img, amount=0.08, thresh=0.55):
    x = np.maximum(img - thresh, 0)
    x = np.minimum(x, 30)
    s = img.shape[1] / 1920
    return img + amount * (0.5 * blur(x, 7 * s) + 0.3 * blur(x, 26 * s) + 0.2 * blur(x, 80 * s))


def film(x, exposure=1.0):
    """ACES-style fit, per channel, so a saturated beam runs to white at its core as in stage photographs."""
    x = np.maximum(x * exposure, 0)
    y = np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)
    return np.where(y <= 0.0031308, y * 12.92, 1.055 * y ** (1 / 2.4) - 0.055)


def over(rgb8, layer_path, opacity=1.0):
    """Lays a straight-alpha type layer over the display-referred frame."""
    if not os.path.exists(layer_path):
        print("no layer", layer_path)
        return rgb8
    im = Image.open(layer_path).convert("RGBA").resize((rgb8.shape[1], rgb8.shape[0]), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    al = a[..., 3:] * opacity
    return rgb8 * (1 - al) + a[..., :3] * al


def led_grid(pic, pitch):
    """Sample and hold onto a grid locked to whole output pixels, each cell one round lamp. Whole pixels, integer pitch, no resampling of the grid: no moire, on any frame."""
    h, w = pic.shape[:2]
    ny, nx = h // pitch, w // pitch
    small = pic[:ny * pitch, :nx * pitch].reshape(ny, pitch, nx, pitch, 3).mean((1, 3))
    tile_ss = 8
    n = pitch * tile_ss
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    r = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2)
    t = np.clip((0.96 - r) / 0.2, 0, 1)
    tile = t.reshape(pitch, tile_ss, pitch, tile_ss).mean((1, 3)).astype(np.float32)
    tile = 0.5 + 0.5 * tile / tile.mean()    # the dark gaps stay part lit, as on a real wall seen through haze, so a player scaling the picture finds little to beat against
    tile /= tile.mean()
    out = np.zeros_like(pic)
    big = np.repeat(np.repeat(small, pitch, 0), pitch, 1)
    out[:ny * pitch, :nx * pitch] = big * np.tile(tile, (ny, nx))[..., None]
    return out


def load(tag):
    return np.load(os.path.join(WORK, tag + ".npy"))


def desk(d, a, b, c):
    """a, b, c are (colour, gain) per channel."""
    return sum(d[..., i:i + 1] * lin(col) * g for i, (col, g) in enumerate((a, b, c)))


PITCH = {"T2": 3, "T5": 3}     # px at 1080p, doubled at 4K, always whole pixels
DESK = {
    # shot: R fader, G fader, B fader, exposure, bloom
    "T1": (("C9CFD6", 0.6), ("C4122A", 1.2), ("E3172D", 0.8), 1.0, 0.07),
    "T2": (("7F6BFF", 0.9), ("9A3FD0", 1.0), ("FFB27A", 0.6), 1.0, 0.08),
    "T3": (("C8D4FF", 1.0), ("1F2BFF", 1.0), ("A8B8FF", 1.0), 1.0, 0.10),
    "T4": (("DCF3FF", 0.42), ("1E6BFF", 1.4), ("7FB4FF", 0.8), 1.0, 0.09),
    "T5": (("F2FFFB", 0.62), ("00C4AE", 1.0), ("7FF5DC", 0.7), 1.0, 0.09),
    "T6": (("3BC9A5", 1.5), ("3BC9A5", 0.35), ("FFC85A", 1.0), 1.0, 0.09),
}


def finish(shot, tag=""):
    name = shot + tag
    d = load(name)
    a, b, c, ex, bl = DESK[shot]
    img = desk(d, a, b, c)
    mp = os.path.join(WORK, name + "_mask.npy")
    if os.path.exists(mp):
        m = np.load(mp)[..., :1]
        m = np.clip(m, 0, 1)
        pic_path = os.path.join(WORK, shot + "led.npy")
        if os.path.exists(pic_path) and d.shape[1] == 1920:
            pic = np.load(pic_path)
            beams = d[..., 0:1] * lin(a[0]) * a[1] + d[..., 1:2] * lin(b[0]) * b[1]
            img = img * (1 - m) + (led_grid(pic, PITCH[shot]) + beams) * m
    img = bloom(img, bl)
    out = film(img, ex)
    out = over(out, os.path.join(WORK, "text", shot + "over.png"))
    im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    path = os.path.join(STILLS, shot + ".png") if not tag else os.path.join(WORK, name + "_preview.png")
    if not tag:
        im = im.resize((1920, 1080), Image.LANCZOS)
    im.save(path)
    print("wrote", path, "levels p50 %.3f p99 %.3f" % (np.percentile(out, 50), np.percentile(out, 99)))


if __name__ == "__main__":
    os.makedirs(STILLS, exist_ok=True)
    finish(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
