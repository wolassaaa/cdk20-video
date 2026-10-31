"""HKBU SCIE1007 coursework science video, dawn art direction. Picks the T5 camera: which way out of the pocket is open, from the real 1-302 surface and the 048 pose in our re-docking.
Marches rays out from the ligand through the same Gaussian field the mesh came from. Prints the open direction and writes _work/mouth.json.
"""
import json
from pathlib import Path
import numpy as np

WORK = Path(__file__).resolve().parent.parent / "_work"
F = np.load(WORK / "rock_302_field.npy").astype(np.float32)
meta = np.load(WORK / "rock_302.npz")
lo, H = meta["lo"], float(meta["H"])
P = np.load(WORK / "pose048.npz")
heavy = P["el"] != "H"
L = P["xyz"][heavy]
c = L.mean(0)
print("ligand heavy atoms", int(heavy.sum()), "span", (L.max(0) - L.min(0)).round(1), "centre", c.round(1))
r = np.random.default_rng(0)
D = r.standard_normal((6000, 3)); D /= np.linalg.norm(D, axis=1, keepdims=True)
steps = np.arange(0, 42, .4)
free = np.zeros(len(D))
sh = np.array(F.shape)
for i, d in enumerate(D):
    p = c + d[None] * steps[:, None]
    q = np.round((p - lo) / H).astype(int)
    ok = ((q >= 0) & (q < sh)).all(1)
    v = np.zeros(len(p)); v[ok] = F[tuple(q[ok].T)]
    # start outside the ligand's own space; hitting solid means blocked
    hit = np.nonzero(v > 1.0)[0]
    free[i] = steps[hit[0]] if len(hit) else 99
open_dirs = D[free > 60]
print("open fraction", round(len(open_dirs) / len(D), 3))
m = open_dirs.mean(0); m /= np.linalg.norm(m)
best = D[free > 60]
# widest cone of clear sky around the mean
cos = open_dirs @ m
print("mean open dir", m.round(3), "spread deg", round(float(np.degrees(np.arccos(np.percentile(cos, 20)))), 1))
json.dump(dict(open=m.tolist(), centre=c.tolist()), open(WORK / "mouth.json", "w"))
