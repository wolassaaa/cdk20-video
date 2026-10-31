"""HKBU SCIE1007 coursework science video, dawn art direction. Turns the real CDK20 surface into terrain.

A protein seen whole reads as a cloud, because it has overhangs. Terrain has none. So the surface is read from directly above the pocket, keeping the highest point of the real mesh in each cell.
What the low camera then sees is the true relief of that side, in true proportion (1:1, nothing invented), with the pocket as a real canyon. pLDDT comes along per cell.
python make_relief.py [tilt_deg]    writes _work/relief.npz
"""
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "_work"
ROOT = HERE.parents[2] / "S2plus"
tilt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
yaw = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0

D = np.load(WORK / "rock_full.npz")
V, C = D["verts"].astype(np.float64), D["conf"]
res = json.load(open(ROOT / "code" / "cdk20_backbone_view.json"))["res"]
ca = {r["i"]: np.array(r["ca"]) for r in res}
cen = np.mean([ca[i] for i in range(1, 303)], 0)
pocket = (ca[33] + ca[84]) / 2
nl, cl = np.mean([ca[i] for i in range(5, 85)], 0), np.mean([ca[i] for i in range(100, 290)], 0)
op = pocket - cen; op /= np.linalg.norm(op)
lobe = nl - cl; lobe -= op * np.dot(lobe, op); lobe /= np.linalg.norm(lobe)
side = np.cross(op, lobe)

t, a = math.radians(tilt), math.radians(yaw)
z = op * math.cos(t) + side * math.sin(t)
x = lobe
y = np.cross(z, x)
R = np.stack([x, y, z], 0)
R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]]) @ R
P = (V - cen) @ R.T
DX = 0.2
lo = P[:, :2].min(0) - 6
n = np.ceil((P[:, :2].max(0) + 6 - lo) / DX).astype(int) + 1
ij = np.floor((P[:, :2] - lo) / DX).astype(int)
Z = np.full((n[1], n[0]), -1e9, np.float32)
order = np.argsort(P[:, 2])
Z[ij[order, 1], ij[order, 0]] = P[order, 2]        # last write wins, and the order is by height, so each cell keeps the top of the surface
K = np.zeros_like(Z)
K[ij[order, 1], ij[order, 0]] = C[order]
base = float(P[:, 2].min())
filled = Z > -1e8
for _ in range(3):      # close single-cell gaps in the raster, never grow the footprint by more than that
    m = filled.astype(np.float32)
    s = np.zeros_like(Z); w = np.zeros_like(Z); sk = np.zeros_like(Z)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        s += np.roll(np.roll(np.where(filled, Z, 0), dy, 0), dx, 1)
        sk += np.roll(np.roll(np.where(filled, K, 0), dy, 0), dx, 1)
        w += np.roll(np.roll(m, dy, 0), dx, 1)
    hole = (~filled) & (w >= 3)
    Z = np.where(hole, s / np.maximum(w, 1), Z); K = np.where(hole, sk / np.maximum(w, 1), K)
    filled = Z > -1e8
Z = np.where(filled, Z, base)
K = np.where(filled, K, 0.0)


def smooth(a, k=1):
    for _ in range(k):
        a = (a * 4 + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 8
    return a


# Cliffs where the footprint ends are not surface, they are the raster falling to the base. Under them goes a talus: a slope no steeper than SLOPE that only ever fills, never cuts, so every real crest stays where it was.
SLOPE = 1.7
real = Z.copy()
for _ in range(420):
    d = Z - SLOPE * DX
    e = np.maximum.reduce([np.roll(d, 1, 0), np.roll(d, -1, 0), np.roll(d, 1, 1), np.roll(d, -1, 1)])
    Z = np.maximum(Z, e)
print("talus fills", round(float((Z - real > .05).mean() * 100)), "% of cells; real surface kept on the rest")
Z, K = smooth(Z, 2), smooth(K, 2)
pk = ((pocket - cen) @ R.T)
np.savez(WORK / "relief.npz", Z=Z.astype(np.float32), K=K.astype(np.float32), lo=lo, DX=DX, base=base, pocket=pk, R=R, cen=cen)
print("relief", Z.shape, "height", round(float(Z.max() - base), 1), "A, footprint", np.round((n * DX), 1), "A, pocket at", pk.round(1), "cells kept", int(filled.sum()))
