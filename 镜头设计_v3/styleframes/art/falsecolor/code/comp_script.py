"""HKBU SCIE1007 coursework science video. falsecolor art direction: picture layer for colour_script.png.

python comp_script.py   needs the T1, T2, T4, T5, T6 picture layers and t4 passes

Eight sections, widths by running time. Top: one picture per section on that section's map. Bottom strip: the map itself, low to high.
S7 and S8 are not among the six stills, so they reuse T4 and T2 on their own maps.
"""
import os

import numpy as np
from PIL import Image

import comp_t2
import comp_t4
from fc_common import PUB, SECTIONS, apply, to_u8

W, H, STRIP = 1920, 480, 44
PIC = H - STRIP


def load(n):
    return np.asarray(Image.open(os.path.join(PUB, n)).convert("RGB")).astype(np.float64) / 255


def crop(a, w, cx):
    """Scale a 1920x1080 picture to PIC high, take a slice w wide centred on cx (in 1920 px)."""
    s = PIC / a.shape[0]
    im = Image.fromarray(to_u8(a)).resize((int(a.shape[1] * s), PIC), Image.LANCZOS)
    b = np.asarray(im).astype(np.float64) / 255
    x0 = int(np.clip(cx * s - w / 2, 0, b.shape[1] - w))
    return b[:, x0:x0 + w]


def s3_slice(w):
    """Signal dying away to nothing: the empty keyhole outline in the last of the dusk map."""
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, PIC)
    xx, yy = np.meshgrid(x, y)
    v = 0.55 * np.clip(1 - x * 1.5, 0, 1)[None, :] ** 1.5 * np.exp(-((yy - 0.5) / 0.55) ** 2)
    return apply(v, "s3_dusk")


pics = {
    "S1": lambda w: crop(load("t1_bg.png"), w, 640),
    "S2": lambda w: crop(load("t2_bg.png"), w, 1262),
    "S3": s3_slice,
    "S4": lambda w: crop(load("t4_bg.png"), w, 880),
    "S5": lambda w: crop(load("t5_bg.png"), w, 1290),
    "S6": lambda w: crop(load("t6_bg.png"), w, 800),
    "S7": lambda w: crop(comp_t4.compose("t4", "s7_ash", lines=False) * 0.62, w, 1120),
    "S8": lambda w: crop(comp_t2.compose("s8_dawn", gain=0.8), w, 1262),
}

total = sum(s[1] for s in SECTIONS)
out = np.zeros((H, W, 3))
x = 0
for i, (n, sec, name) in enumerate(SECTIONS):
    x1 = W if i == len(SECTIONS) - 1 else x + round(sec / total * W)
    w = x1 - x
    out[:PIC, x:x1] = pics[n](w)
    out[PIC:, x:x1] = apply(np.linspace(0, 1, w)[None, :].repeat(STRIP, 0), name)
    out[:, x1 - 2:x1] = 0
    x = x1
Image.fromarray(to_u8(out)).save(os.path.join(PUB, "colour_script_bg.png"))
print("wrote colour_script_bg.png")
