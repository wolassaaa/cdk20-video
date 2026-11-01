"""HKBU SCIE1007 coursework science video. Ink direction, F4 art layer: CDK20 from AlphaFold DB v6, drawn from its real backbone, with real per-residue confidence.

python f4_protein.py -> ../_work/f4_art.npy
Drawn the way ribbon diagrams were first inked by hand: one face of the ribbon bright, the other dark with lines along the chain, so the chain's path reads.
Confidence (pLDDT, the 346 values in the AlphaFold file) sets how whole the ribbon is. At 70 and up it is unbroken; below that it breaks into dashes, more gaps the lower the value.
So the tail, residues 303 to 346, falls apart on screen because of its own numbers.
"""
import os

import numpy as np

import engrave as E

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
D = np.load(HERE + "../_work/protein.npz")
h, w = D["prot_mask"].shape
M = D["world_to_cam"]
m = D["prot_mask"].astype(np.float32)
P, N = D["prot_pos"], D["prot_nrm"].astype(np.float32)
A, B = D["prot_attr"], D["prot_attr2"]
pl, u = A[..., 0], A[..., 1]
side, cross = B[..., 0], B[..., 1]
res = u * 345 + 1                         # residue number along the chain, 1 to 346
li = E.mblur(D["prot_light"].astype(np.float32), m, 2)
z = E.cam_depth(P, M)
zm = z[m > 0]
zn = np.clip((z - np.percentile(zm, 4)) / (np.percentile(zm, 96) - np.percentile(zm, 4)), 0, 1)
tone = E.smooth(0.02, 0.8, li)

tail = (res >= 303) * m
core = m * (res < 303)

# depth: near parts bone, far parts sink to the brighter blue, then towards the ground
far = E.smooth(0.15, 0.85, zn)[..., None]
bone = E.BONE[None, None] * (1 - far) + E.BLUE[None, None] * far

lit_face = E.smooth(0.46, 0.54, side)      # one face of each ribbon
# lines along the chain, across the ribbon width. Predicted = hatched, on every part of the model
s = cross * 7.0
flow = E.stripes(s, np.clip(0.22 + 0.45 * tone, 0, 0.8), 6.0)
s2 = res * 3.0
hatch = E.stripes(s2, np.clip(0.66 + 0.40 * tone, 0, 0.92), 6.0)

img = np.zeros((h, w, 3), np.float32)
img[:] = E.KLEIN
# a black trap lifts the whole model off the blue
trap = np.clip(E.blur(core, 7) * 3.4, 0, 1)
img = E.over(img, trap, np.zeros(3))
face = np.where(lit_face > 0.5, hatch, flow)
ink = core * face
img = img * (1 - ink[..., None]) + ink[..., None] * bone
edge = E.contour(N, m, tone, base=0.16, gain=0.05) * core
img = E.over(img, edge, np.zeros(3))

# breaks by real confidence: full ribbon at pLDDT 70 and above
c = np.clip((pl - 40) / (70 - 40), 0, 1)
duty = 0.30 + 0.70 * c
dash = np.abs((res / 1.5) - np.round(res / 1.5)) * 2
keep = np.where(duty >= 0.999, 1.0, E.smooth(duty + 0.03, duty - 0.03, dash))
gap = core * (1 - keep)
img = E.over(img, gap, E.KLEIN)

# tail in blood red with a bone edge, so the dashes hold on the blue
t = tail * keep
tt = 0.62 + 0.38 * tone
img = img * (1 - t[..., None]) + t[..., None] * (E.RED[None, None] * tt[..., None] + E.DARKRED[None, None] * (1 - tt[..., None]))
out = E.down2(img)

ys, xs = np.nonzero(tail)
print("tail bbox", xs.min() / 2, xs.max() / 2, ys.min() / 2, ys.max() / 2)
ys, xs = np.nonzero(core)
print("core bbox", xs.min() / 2, xs.max() / 2, ys.min() / 2, ys.max() / 2)
for r in (303, 310, 315, 320, 325, 330, 335, 340, 346):
    b = (np.abs(res - r) < 0.6) * m > 0
    if b.any():
        yy, xx = np.nonzero(b)
        print("res", r, round(xx.mean() / 2), round(yy.mean() / 2))
np.save(HERE + "../_work/f4_art.npy", out.astype(np.float32))
E.save(out, HERE + "../_work/f4_art.png")
