"""HKBU SCIE1007 coursework science video. falsecolor art direction: T4 picture layer. The colour of every surface pixel is the real pLDDT of that residue, looked up on the bar.

python comp_t4.py [tag] [out.png]   needs <tag>_mask/plddt/ao/facing.png from bl_data_pass.py

Colour = pLDDT through PLDDT_GAMMA, so the crowded band above 90 opens up; the bar prints its ticks at the same positions, so it stays a true scale.
Crevices lean warm and dark so the form survives at the pale top of the map. Thin lines are the 50, 70 and 90 contours of the same number.
"""
import os
import sys

import numpy as np
from PIL import Image

from fc_common import PUB, WORK, apply, bloom, blur, s2l, l2s, to_u8, lut

PLDDT_GAMMA = 2.0


def g(tag, n):
    return np.asarray(Image.open(os.path.join(WORK, f"{tag}_{n}.png"))).astype(np.float64) / 65535


def contour(c, level, m, width=1.1):
    """Soft line where c crosses level, about width px either side whatever the slope."""
    gy, gx = np.gradient(c)
    d = np.abs(c - level) / np.maximum(np.hypot(gx, gy), 1.5e-3)
    edge = blur((m > 0.98).astype(float), 1.5) > 0.97
    return np.clip(1.6 - d / width, 0, 1) * edge


def compose(tag="t4", name="s4_signal", reveal=None, lines=True):
    m = g(tag, "mask")
    inv = lambda a: (s2l(a) / np.maximum(m, 1e-3)).clip(0, 1) ** (1 / 2.2)   # undoes the display curve and the edge coverage: this is the stored number
    conf, cs, ao, f = inv(g(tag, "plddt")), inv(g(tag, "smooth")), inv(g(tag, "ao")), inv(g(tag, "facing"))
    conf = np.where(m > 1e-3, conf, 0)
    if reveal is not None:
        conf = np.where(conf >= reveal, conf, 0)   # map lights up from the most certain residues down
    col = apply(conf ** PLDDT_GAMMA, name)
    occ = np.clip((ao - 0.12) / 0.7, 0, 1)
    rim = np.clip(f / 0.75, 0, 1) ** 0.8
    t = 0.30 + 0.70 * occ * (0.62 + 0.38 * rim)
    lin = s2l(col) * np.stack([t ** 0.75, t ** 1.25, t ** 1.9], -1)
    if lines:
        k = 0
        for lv in (0.5, 0.7, 0.9):
            k = np.maximum(k, contour(blur(cs, 1.0), lv, m))
        lin = lin * (1 - 0.8 * k[..., None])
    field = s2l(lut(name)[0])
    lin = lin * m[..., None] + field * (1 - m[..., None])
    return bloom(l2s(lin), amount=0.20, s=(4, 14, 48))


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "t4"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PUB, "t4_bg.png")
    Image.fromarray(to_u8(compose(tag))).save(out)
    print("wrote", out)
