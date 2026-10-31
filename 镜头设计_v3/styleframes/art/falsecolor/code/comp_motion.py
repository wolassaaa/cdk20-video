"""HKBU SCIE1007 coursework science video. falsecolor art direction: frames for the 6 s motion test, W2 lit by the data.

python comp_motion.py   needs ../_work/mo/m_NNN_<pass>.png from bl_data_pass.py --seq, writes ../public/mo/fNNN.jpg and adds the bar curve to luts.json

Black, an empty bar. The map then lights from the most certain residues down, the bar fills in step, and the tail arrives last and cold. A 10 degree turn runs under it.
The 61 rendered keys are about 0.17 degrees apart, under 1.5 px at the edge, so the 180 frames blend neighbouring data passes, not finished pictures. Nothing here changes from frame to frame except the data: no grain, no flicker.
"""
import json
import os

import numpy as np
from PIL import Image

from comp_t4 import PLDDT_GAMMA, contour
from fc_common import PUB, WORK, apply, blur, bloom, l2s, lut, s2l, smooth

N, KEYS = 180, 61
MO = os.path.join(WORK, "mo")
OUT = os.path.join(PUB, "mo")
os.makedirs(OUT, exist_ok=True)
NAME = "s4_signal"


def key(k, n):
    return np.asarray(Image.open(os.path.join(MO, f"m_{k:03d}_{n}.png"))).astype(np.float32) / 65535


def passes(u):
    k0 = min(int(u), KEYS - 2)
    t = u - k0
    return {n: key(k0, n) * (1 - t) + key(k0 + 1, n) * t for n in ("mask", "plddt", "smooth", "ao", "facing")}


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def cut_at(f):
    return float(1.0 if f < 24 else 0.995 - (0.995 - 0.24) * ease((f - 24) / 116))


def frame(f):
    P = passes(f / (N - 1) * (KEYS - 1))
    m = P["mask"].astype(np.float64)
    inv = lambda a: (s2l(a) / np.maximum(m, 1e-3)).clip(0, 1) ** (1 / 2.2)
    conf, cs, ao, fc = inv(P["plddt"]), inv(P["smooth"]), inv(P["ao"]), inv(P["facing"])
    ao = blur(ao, 1.0)
    conf = np.where(m > 1e-3, conf, 0)
    cut = cut_at(f)
    col = apply(conf ** PLDDT_GAMMA, NAME)
    occ = np.clip((ao - 0.12) / 0.7, 0, 1)
    rim = np.clip(fc / 0.75, 0, 1) ** 0.8
    t = 0.30 + 0.70 * occ * (0.62 + 0.38 * rim)
    lin = s2l(col) * np.stack([t ** 0.75, t ** 1.25, t ** 1.9], -1)
    k = 0
    for lv in (0.5, 0.7, 0.9):
        k = np.maximum(k, contour(blur(cs, 1.0), lv, m))
    lin = lin * (1 - 0.8 * k[..., None])
    a = (smooth(cut - 0.014, cut + 0.014, conf) * m)[..., None]
    floor = s2l(lut(NAME)[0]) * ease((f - 24) / 60)     # black until the first signal arrives, then the bar's floor
    return bloom(l2s(lin * a + floor * (1 - a)), amount=0.20, s=(4, 14, 48)), l2s(floor)


if __name__ == "__main__":
    L = json.load(open(os.path.join(PUB, "luts.json")))
    L["reveal"], L["floorSeq"] = [], []
    for f in range(N):
        rgb, fl = frame(f)
        L["reveal"].append(round(cut_at(f), 4))
        L["floorSeq"].append("#%02X%02X%02X" % tuple(int(c * 255 + 0.5) for c in fl))
        Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f"f{f:03d}.jpg"), quality=94, subsampling=0)
        if f % 30 == 0:
            print(f, flush=True)
    json.dump(L, open(os.path.join(PUB, "luts.json"), "w"))
    print("done")
