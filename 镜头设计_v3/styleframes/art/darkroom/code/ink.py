"""HKBU SCIE1007 coursework science video. Helpers for the darkroom papers: load an ink layer, crop it, paste it onto a paper texture in any colour."""
import os
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, "..", "_work"))
_cache = {}

def ink(name):
    if name not in _cache:
        im = Image.open(os.path.join(WORK, "type", name + ".png")).convert("RGBA")
        _cache[name] = im.crop(im.split()[3].getbbox())
    return _cache[name]

def fit(name, height=None, width=None):
    """height is the pixel height of the cropped ink, so it scales with the paper texture."""
    im = ink(name)
    s = (height / im.height) if height else (width / im.width)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

def paste(paper, name, xy, height=None, width=None, color=(0, 0, 0), opacity=1.0, rotate=0, soft=0):
    im = fit(name, height, width)
    if rotate:
        im = im.rotate(rotate, Image.BICUBIC, expand=True)
    a = im.split()[3]
    if soft:
        a = a.filter(ImageFilter.GaussianBlur(soft))
    if opacity < 1:
        a = a.point(lambda v: int(v * opacity))
    paper.paste(Image.new("RGB", im.size, color), (int(xy[0]), int(xy[1])), a)
    return im.size

def lf(W, H, sig, seed, down=8):
    r = np.random.default_rng(seed).random((H // down + 2, W // down + 2))
    im = Image.fromarray((r * 255).astype("uint8")).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(sig))
    a = np.asarray(im, float) / 255
    return (a - a.min()) / (a.max() - a.min() + 1e-9)
