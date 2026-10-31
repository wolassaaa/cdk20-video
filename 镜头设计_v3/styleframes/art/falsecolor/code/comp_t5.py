"""HKBU SCIE1007 coursework science video. falsecolor art direction: T5 picture layer.

python comp_t5.py [out.png]   needs t5_*.png from bl_pocket_pass.py

Each pocket pixel is its distance to the nearest heavy atom of 048 in our re-docked pose, in Å, on the s5 map: the walls that touch the key are the hottest thing in the film.
048 itself carries no colour. It is bone with a dark edge, because it is the thing placed, not a thing measured by this scale.
"""
import os
import sys

import numpy as np
from PIL import Image

from fc_common import PUB, WORK, apply, blur, l2s, s2l, smooth, to_u8, lut

NEAR, FAR = 2.0, 6.5     # Å at the top and the bottom of the bar
BONE = "F4EFE0"


def g(n):
    return np.asarray(Image.open(os.path.join(WORK, f"t5_{n}.png"))).astype(np.float64) / 65535


def compose(name="s5_contact", field_v=0.0):
    m = g("mask")
    inv = lambda a, c: (s2l(a) / np.maximum(c, 1e-3)).clip(0, 1) ** (1 / 2.2)
    d = inv(g("dist"), m) * 8
    ao = inv(g("ao"), m)
    lc = g("lig")
    ls = inv(g("ligshade"), lc)
    v = 1 - np.clip((d - NEAR) / (FAR - NEAR), 0, 1)
    v = np.where(m > 1e-3, v, 0)
    col = apply(v, name)
    t = 0.30 + 0.70 * np.clip((ao - 0.1) / 0.75, 0, 1)
    lin = s2l(col) * np.stack([t ** 0.7, t ** 1.2, t ** 1.8], -1)
    field = s2l(lut(name)[0])
    lin = lin * m[..., None] + field * (1 - m[..., None])
    # 048: bone, with a soft dark edge so it stands clear of the hot wall behind it
    halo = np.clip(blur(lc, 5) * 2.2, 0, 1)[..., None]
    lin = lin * (1 - 0.86 * halo)
    bone = s2l(np.array([int(BONE[i:i + 2], 16) / 255 for i in (0, 2, 4)]))
    sh = (0.42 + 0.58 * ls ** 1.2)[..., None]
    lin = lin * (1 - lc[..., None]) + bone * sh * lc[..., None]
    return l2s(lin), m, lc


if __name__ == "__main__":
    rgb, m, lc = compose()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PUB, "t5_bg.png")
    Image.fromarray(to_u8(rgb)).save(out)
    print("wrote", out)
