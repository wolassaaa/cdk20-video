"""HKBU SCIE1007 coursework science video. Ink direction: motion check for the engraved lines.

python turn_test.py turn0 turn1 turn2  (npz tags in ../_work, made with bl_ink_passes.py liver --orbit <deg> --tag <tag>)
Prints how much the frame's average brightness moves between frames and how long one frame takes. A flash shows up as a brightness jump; a line that stays on the surface does not.
"""
import os
import sys
import time

import numpy as np

import engrave as E

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"


def ink(tag):
    D = np.load(HERE + "../_work/" + tag + ".npz")
    L = E.world_per_px(D)
    m = D["liver_mask"].astype(np.float32)
    P = D["liver_pos"].astype(np.float32) * m[..., None]
    li = D["liver_light"].astype(np.float32)
    tone = E.smooth(0.03, 1.0, np.clip(E.mblur(li, m, 2), 0, 1))
    h, w = m.shape
    d1 = np.array([0.45, -0.55, -0.70], np.float32)
    d1 /= np.linalg.norm(d1)
    Ps = np.stack([E.mblur(P[..., i], m, 5) for i in range(3)], -1)
    s1 = (Ps @ d1) / (19.0 * L) + E.wob((h, w), 90, 3, 0.35)
    out = E.stripes(s1, np.clip(0.06 + 0.62 * tone, 0, 0.92), 7.0) * m
    return out, m


frames = []
for t in sys.argv[1:]:
    t0 = time.time()
    a, m = ink(t)
    frames.append(a)
    print(t, "line pass %.1f s" % (time.time() - t0), "mean level %.5f" % a.mean())
for a, b in zip(frames, frames[1:]):
    print("mean level change %.3f %%" % (abs(a.mean() - b.mean()) / a.mean() * 100), "pixels changed over 0.25: %.1f %%" % ((np.abs(a - b) > 0.25).mean() * 100))
for i, a in enumerate(frames):
    E.save(np.repeat(E.down2(np.repeat(a[..., None], 3, 2))[..., :1], 3, 2), HERE + f"../_work/turn{i}.png")
