"""HKBU SCIE1007 coursework science video. Ink direction, F1 art layer: the real liver cut as an engraving, portal vein and hepatic veins inked solid.

python f1_liver.py -> ../_work/f1_art.npy (linear-free display RGB at 1920x1080) and ../_work/f1_anchor.json (pixel points for the leader lines).
"""
import json
import os

import numpy as np

import engrave as E

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
D = np.load(HERE + "../_work/liver.npz")
M = D["world_to_cam"]
L = E.world_per_px(D)   # world size of a 4K pixel


def layer(name):
    m = D[name + "_mask"].astype(np.float32)
    return m, D[name + "_pos"].astype(np.float32), D[name + "_nrm"].astype(np.float32), D[name + "_light"].astype(np.float32)


h, w = D["liver_mask"].shape
img = np.zeros((h, w, 3), np.float32)

# ---- liver surface: two cut directions, lines swell with light, deep shade goes black
m, P, N, li = layer("liver")
P = P * m[..., None]
tone = E.smooth(0.03, 1.0, np.clip(E.mblur(li, m, 2), 0, 1))
pitch_px = 19.0                                   # 9.5 px at 1080p
d1 = np.array([0.45, -0.55, -0.70]); d1 /= np.linalg.norm(d1)
d2 = np.array([-0.70, -0.45, -0.55]); d2 /= np.linalg.norm(d2)
Ps = np.stack([E.mblur(P[..., i], m, 5) for i in range(3)], -1)  # lightly smoothed so remesh facets do not nick the lines
s1 = (Ps @ d1.astype(np.float32)) / (pitch_px * L) + E.wob((h, w), 90, 3, 0.35)
s2 = (Ps @ d2.astype(np.float32)) / (pitch_px * L * 1.15) + E.wob((h, w), 90, 5, 0.35)
ph = E.wob((h, w), 40, 7, 0.08)
w1 = np.clip(0.06 + 0.62 * tone + ph, 0, 0.92)
w2 = np.clip((tone - 0.45) * 0.75 + ph, 0, 0.7)
ink = np.maximum(E.stripes(s1, w1, 7.0) * (tone > 0.012), E.stripes(s2, w2, 7.0) * (tone > 0.45))
rim = E.contour(N, m, tone, base=0.20, gain=0.10)
ink = np.maximum(ink * m, rim * 0.0)
liver_ink = ink * m
edge = E.calligraphic_edge(D["liver_mask"], 22, nib=(-0.85, 0.5), thin=0.22)

img = E.over(img, liver_ink, E.BONE)
del s1, s2, w1, w2, Ps

# ---- vessels: seen through the liver. Solid ink with a dark engraved side, black trap so white lines stop short of them
def vessel(name, hi, lo, dirv, seed):
    m, P, N, li = layer(name)
    li = E.mblur(li, m, 2)
    t = E.smooth(0.05, 0.75, li)
    s = (P @ dirv.astype(np.float32)) / (13.0 * L) + E.wob((h, w), 60, seed, 0.25)
    cut = E.stripes(s, np.clip(0.75 - t * 1.0, 0, 0.9), 5.0) * m
    edgeN = E.contour(N, m, t, base=0.34, gain=0.18)
    return m, cut, edgeN, E.cam_depth(P, M)


dv = np.array([0.7, -0.2, 0.68]); dv /= np.linalg.norm(dv)
mp, cp, ep, zp = vessel("portal", E.RED, E.DARKRED, dv, 11)
mh, ch, eh, zh = vessel("hepatic", E.BLUE, E.KLEIN, dv, 13)
front_p = mp * (1 - mh * (zh < zp))
front_h = mh * (1 - mp * (zp <= zh))
trap = np.clip(E.blur(np.maximum(mp, mh), 7) * 3.2, 0, 1)
img = E.over(img, trap, np.zeros(3))
img = E.over(img, front_h, E.BLUE)
img = E.over(img, front_h * ch, E.KLEIN)
img = E.over(img, front_h * eh, np.zeros(3))
img = E.over(img, front_p, E.RED)
img = E.over(img, front_p * cp, E.DARKRED)
img = E.over(img, front_p * ep, np.zeros(3))

# ---- the outline last, on top of everything, as the pen would close the drawing
img = E.over(img, edge * (1 - D["liver_mask"]), E.BONE)
out = E.down2(img)


def anchor(mask, x0, x1, y0, y1):
    """Pick a real pixel of a structure inside a window, in 1080p coordinates."""
    ys, xs = np.nonzero(mask[y0 * 2:y1 * 2, x0 * 2:x1 * 2])
    if len(xs) == 0:
        return None
    i = len(xs) // 2
    return [float(xs[i] / 2 + x0), float(ys[i] / 2 + y0)]


Xs = np.nonzero(D["liver_mask"].any(0))[0] / 2
Ys = np.nonzero(D["liver_mask"].any(1))[0] / 2
print("liver bbox x", Xs.min(), Xs.max(), "y", Ys.min(), Ys.max())
xp = np.nonzero(D["portal_mask"].any(0))[0] / 2
yp = np.nonzero(D["portal_mask"].any(1))[0] / 2
xh = np.nonzero(D["hepatic_mask"].any(0))[0] / 2
yh = np.nonzero(D["hepatic_mask"].any(1))[0] / 2
print("portal", xp.min(), xp.max(), yp.min(), yp.max(), "hepatic", xh.min(), xh.max(), yh.min(), yh.max())
np.save(HERE + "../_work/f1_art.npy", out.astype(np.float32))
E.save(out, HERE + "../_work/f1_art.png")
