"""HKBU SCIE1007 coursework science video. Finds the way the cut tail (residues 303-346) can be lifted out of CDK20 in shot u (the new S4 opening) without passing through the part that is kept (1-302). The tail is moved as one rigid piece along a straight line; a direction passes if, all the way out to 70 Angstrom, no tail atom comes closer to a kept atom than the closest pair already is (the 302-303 bond aside). Of the passing directions the one nearest straight up on the table is kept. Writes frames/tail_cut.json. Run: python tail_cut_dir.py"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
P_UP = math.radians(16)             # as in bl_inserts.py
pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[76:78].strip() != "H"]
res = np.array([int(l[22:26]) for l in pdb])
xyz = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb])
keep, tail = xyz[res <= 302], xyz[res >= 303]
skip = np.outer(res[res >= 303] == 303, res[res <= 302] == 302)        # the bond that is cut


def turn(a, b):
    """The shortest turn taking a onto b, as Blender's rotation_difference does."""
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a @ b)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


mouth = np.load(HERE + "frames/cdk20.npz")["mouth"]
R = turn(mouth, np.array([0, -math.cos(P_UP), math.sin(P_UP)]))
a = -(math.pi / 2 - P_UP)
Qs = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])        # S3's small model: pocket looking up
up = R.T @ Qs.T @ np.array([0, 0, 1.0])     # straight up on the table, in the model's own frame


def least(shift):
    d = np.linalg.norm((tail + shift)[:, None] - keep[None], axis=2)
    d[skip] = 99
    return float(d.min())


start = least(np.zeros(3))
n = 600
i = np.arange(n) + 0.5
z, ph = 1 - i / n, math.pi * (1 + 5 ** 0.5) * i          # a spiral over the upper half, around "up"
local = np.c_[np.sqrt(1 - z * z) * np.cos(ph), np.sqrt(1 - z * z) * np.sin(ph), z]
e1 = np.cross(up, [1, 0, 0])
e1 /= np.linalg.norm(e1)
e2 = np.cross(up, e1)
dirs = local[:, :1] * e1 + local[:, 1:2] * e2 + local[:, 2:] * up
best = None
for d in sorted(dirs, key=lambda d: -float(d @ up)):         # nearest to straight up first; the first that passes wins
    if all(least(d * s) >= start - 0.05 for s in np.arange(0.5, 70.01, 0.5)):
        best = d
        break
assert best is not None, "no clear way out"
print("closest pair before the lift %.2f A; way out %.0f degrees from straight up" % (start, math.degrees(math.acos(float(best @ up)))))
json.dump(dict(dir=best.tolist(), reach=70.0, closest=start), open(HERE + "frames/tail_cut.json", "w"))
