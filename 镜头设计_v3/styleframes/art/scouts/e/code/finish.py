"""HKBU SCIE1007 coursework science video. Group E style scouts: last pass that adds the small label to each Blender frame.

Keeps a clean copy in _work/raw so it can run again without stacking type. System Python.
Usage: python finish.py e2 e3 ...   (no arguments: all Blender frames)
"""
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from common import FONTS, LABEL, OUT, WORK

RAW = WORK / "raw"
RAW.mkdir(exist_ok=True)
NAMES = {"e2": "e2_voxel", "e3": "e3_chrome", "e4": "e4_clay", "e5": "e5_glass", "e6": "e6_tiltshift",
         "e8": "e8_inflate", "e9": "e9_viscous", "e10": "e10_cliff"}


def font(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}", size)


def plate(im, xy, text, fnt, fg, bg, pad=(10, 6), radius=0):
    d = ImageDraw.Draw(im, "RGBA")
    l, t, r, b = d.textbbox(xy, text, font=fnt)
    d.rounded_rectangle((l - pad[0], t - pad[1], r + pad[0], b + pad[1]), radius, fill=bg)
    d.text(xy, text, font=fnt, fill=fg)


def star(im, x, y, r, col=(255, 255, 255)):
    """Four point sparkle, drawn from two thin diamonds."""
    a = np.zeros((im.height, im.width), np.float32)
    yy, xx = np.mgrid[0:im.height, 0:im.width].astype(np.float32)
    dx, dy = np.abs(xx - x), np.abs(yy - y)
    a = np.clip(1 - (np.sqrt(dx) + np.sqrt(dy)) / np.sqrt(r), 0, 1) ** 0.6
    arr = np.asarray(im, np.float32)
    arr = arr + a[..., None] * (np.array(col, np.float32) - arr * 0.4)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def e2(im):
    im = ImageEnhance.Contrast(im).enhance(1.12)
    plate(im, (28, 668), LABEL, font("consolab.ttf", 22), (255, 240, 200), (16, 12, 20, 205))
    return im


def e3(im):
    for x, y, r in ((238, 104, 62), (1192, 470, 40), (96, 420, 26), (1086, 636, 20)):
        im = star(im, x, y, r)
    plate(im, (1000, 682), LABEL, font("bahnschrift.ttf", 22), (10, 12, 60), (255, 255, 255, 0), pad=(0, 0))
    return im


def e4(im):
    # a hand-cut paper tag leaning on the mat
    plate(im, (34, 672), LABEL, font("georgiab.ttf", 21), (40, 30, 20), (250, 240, 215, 240), pad=(12, 7))
    return im


def e5(im):
    a = np.asarray(im, np.float32) / 255
    yy, xx = np.mgrid[0:im.height, 0:im.width].astype(np.float32)
    a = a * np.clip(xx / 300, 0.12, 1)[..., None]            # settle the stray reflection on the left
    a = a ** 0.8
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    plate(im, (34, 668), LABEL, font("segoeuil.ttf", 24), (235, 240, 255), (0, 0, 0, 0), pad=(0, 0))
    return im


def e6(im):
    im = ImageEnhance.Color(im).enhance(1.35)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    plate(im, (34, 670), LABEL, font("arialbd.ttf", 21), (20, 20, 20), (255, 225, 60, 235), pad=(12, 7))
    return im


def e8(im):
    plate(im, (34, 672), LABEL, font("seguibl.ttf", 20), (255, 255, 255), (230, 10, 90, 230), pad=(14, 6), radius=16)
    return im


def e9(im):
    plate(im, (34, 26), LABEL, font("segoeuib.ttf", 22), (255, 236, 200), (0, 0, 0, 0), pad=(0, 0))
    return im


def e10(im):
    im = ImageEnhance.Contrast(im).enhance(1.22)
    im = ImageEnhance.Color(im).enhance(1.12)
    d = ImageDraw.Draw(im, "RGBA")
    d.text((58, 74), "CDK20", font=font("bahnschrift.ttf", 86), fill=(255, 255, 255, 245))
    d.rectangle((60, 178, 340, 180), fill=(255, 255, 255, 200))
    d.text((60, 192), LABEL, font=font("bahnschrift.ttf", 23), fill=(255, 255, 255, 240))
    return im


todo = sys.argv[1:] or list(NAMES)
for k in todo:
    p = OUT / f"{NAMES[k]}.png"
    raw = RAW / p.name
    if not p.exists():
        print("missing", k)
        continue
    if not raw.exists() or raw.stat().st_mtime < p.stat().st_mtime - 2 and "--keep" not in sys.argv:
        shutil.copy2(p, raw)
    im = Image.open(raw).convert("RGB")
    im = globals()[k](im)
    im.save(p)
    print("done", k, im.size)
