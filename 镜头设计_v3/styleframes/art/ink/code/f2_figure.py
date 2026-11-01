"""HKBU SCIE1007 coursework science video. Ink direction, F2 art layer: a stand-in for the speaker until real footage exists.

python f2_figure.py -> ../_work/f2_art.npy
The stand-in is the BodyParts3D skin mesh at medium distance, engraved like everything else, kept dim so nobody takes it for the final person.
"""
import os

import numpy as np

import engrave as E

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
D = np.load(HERE + "../_work/figure.npz")
h, w = D["body_mask"].shape
L = E.world_per_px(D)
m = D["body_mask"].astype(np.float32)
P, N = D["body_pos"].astype(np.float32), D["body_nrm"].astype(np.float32)
li = E.mblur(D["body_light"].astype(np.float32), m, 3)
tone = E.smooth(0.03, 1.0, li)
Ps = np.stack([E.mblur(P[..., i] * m, m, 26) for i in range(3)], -1)
d1 = np.array([0.30, -0.35, 0.89], np.float32)
d1 /= np.linalg.norm(d1)
s = (Ps @ d1) / (14.0 * L) + E.wob((h, w), 90, 21, 0.3)
ink = E.stripes(s, np.clip(0.05 + 0.40 * tone, 0, 0.8), 7.0) * m
edge = E.calligraphic_edge(D["body_mask"], 12, nib=(-0.85, 0.5), thin=0.25) * (1 - m)
img = np.zeros((h, w, 3), np.float32)
img = E.over(img, ink, E.BONE)
img = E.over(img, edge, E.BONE)
out = E.down2(img)
ys, xs = np.nonzero(D["body_mask"])
print("body bbox", xs.min() / 2, xs.max() / 2, ys.min() / 2, ys.max() / 2)
np.save(HERE + "../_work/f2_art.npy", out.astype(np.float32))
E.save(out, HERE + "../_work/f2_art.png")
