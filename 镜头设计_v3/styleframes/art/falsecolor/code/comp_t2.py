"""HKBU SCIE1007 coursework science video. falsecolor art direction: T2 picture layer, and the recipe for phone footage.

python comp_t2.py [map] [out.png]

The recipe, the same on any phone clip: take the luminance of the room behind the speaker, blur it hard, look it up on the map. The speaker stays in natural colour.
The bar says room brightness, not temperature. So the colour is a real measurement of the shot, every member's room lands in one palette, and a messy room turns into a soft field.
Here the room is a stand-in and the person is the grey placeholder from the brief, pushed warm to show the grade. Real footage needs a soft matte, nothing tighter.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from fc_common import PUB, apply, blur, l2s, s2l, smooth, to_u8

W, H = 1920, 1080


def person(cx=1262):
    """Soft bust, the placeholder from the brief. Warm head, dark clothes: the eye goes to the face. Returns coverage and a shaded layer."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float64)
    dx = x - cx
    head = (dx / 126) ** 2 + ((y - 372) / 160) ** 2 < 1
    neck = (np.abs(dx) < 80) & (y > 470) & (y < 660)
    # shoulder line: a smooth slope from the neck out, then the arms falling away
    top = 596 + 118 * smooth(70, 330, np.abs(dx)) + 430 * smooth(300, 570, np.abs(dx)) ** 1.5
    body = y > top
    m = (head | neck | body).astype(np.float64)
    m = smooth(0.38, 0.62, blur(m, 8))
    h = 1.0 * blur(m, 40) + 0.7 * blur(m, 14)
    gy, gx = np.gradient(h)
    n = np.stack([-gx * 24, -gy * 24, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.52, -0.40, 0.75])
    t = smooth(0.15, 0.98, np.clip((n * L).sum(-1), 0, 1))[..., None]
    skin = s2l(np.array([0.40, 0.25, 0.20])) * (1 - t) + s2l(np.array([0.93, 0.76, 0.62])) * t
    cloth = s2l(np.array([0.085, 0.065, 0.075])) * (1 - t) + s2l(np.array([0.30, 0.24, 0.24])) * t
    c = smooth(-7, 7, y - (668 - 0.0034 * dx ** 2))[..., None]    # round neckline, rising to the shoulder so the clothes cover it
    return m, l2s(skin * (1 - c) + cloth * c)


def room():
    """Stand-in for the luminance of a phone shot of an ordinary room: lit wall, window behind the speaker, shelf, floor. Only its blurred brightness is ever seen."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float64)
    L = 0.08 + 0.30 * smooth(300, 1400, x) + 0.04 * (1 - y / H)
    L += 0.44 * ((x > 1040) & (x < 1480) & (y > 70) & (y < 640))        # window behind the head
    L += -0.12 * ((x > 880) & (x < 1040) & (y > 130) & (y < 800))       # dark shelf
    L += 0.10 * ((x > 900) & (x < 1020) & (y > 340) & (y < 372))
    L += -0.06 * (y > 900)                                               # floor
    return np.clip(L, 0, 1)


def compose(map_name="s2_iron", cx=1262, gain=1.0):
    m, skin = person(cx)
    v = blur(room(), 88) * gain
    # the lens glow of a bright subject: only adds, and stays soft
    v = v + 0.10 * blur(m, 70)
    bg = apply(np.clip(v, 0, 1), map_name)
    rim = np.clip(blur(m, 9) - m, 0, 1)[..., None]                       # room light wrapping the edge of the speaker, so they sit in the picture
    lin = s2l(bg) * (1 + 0.8 * rim)
    a = m[..., None]
    p = s2l(skin) * (1 + 0.5 * (1 - blur(m, 6)[..., None]) * np.array([1.0, 0.6, 0.35]))
    return l2s(lin * (1 - a) + p * a)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "s2_iron"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PUB, "t2_bg.png")
    Image.fromarray(to_u8(compose(name))).save(out)
    print("wrote", out)
