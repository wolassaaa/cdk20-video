"""HKBU SCIE1007 coursework science video. Builds the solid CDK20 shape for S3's second piece: a soft surface over the heavy atoms of the AlphaFold DB v6 model, with the mouth of the ATP pocket found from our re-docked 048. numpy only. Run: python make_cdk20_mesh.py <out.npz> [last residue] [first residue]"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
V3 = HERE.parents[4]
sys.path.insert(0, str(V3 / "styleframes" / "S2plus" / "code"))
import pocket048 as G

OUT = sys.argv[1]
LAST = int(sys.argv[2]) if len(sys.argv) > 2 else 346
FIRST = int(sys.argv[3]) if len(sys.argv) > 3 else 1      # 303 with last 346: the tail on its own, for S4
PDB = V3 / "assets" / "alphafold" / "AF-Q8IZL9-F1-model_v6.pdb"
H, PAD, K_BLOB = 0.6, 6.0, 0.55     # grid step and padding in Angstrom; low K_BLOB keeps it one soft mass, a silhouette and not a pile of atoms

xyz, el = [], []
for l in PDB.read_text(encoding="utf8").splitlines():
    if l.startswith("ATOM") and l[76:78].strip() != "H" and FIRST <= int(l[22:26]) <= LAST:
        xyz.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
        el.append(l[76:78].strip())
xyz = np.array(xyz)
lig = np.array([a[1:] for a in json.load(open(G.POSES))["poses"]["048"]["atoms"] if a[0] != "H"], float)
pocket = lig.mean(0)
print("nearest atom to the 048 centre %.1f A" % np.linalg.norm(xyz - pocket, axis=1).min())

# the mouth: from the pocket, the direction with the most room around the ray
n = 800
i = np.arange(n) + 0.5
z, a = 1 - 2 * i / n, np.pi * (1 + 5 ** 0.5) * i
dirs = np.c_[np.sqrt(1 - z * z) * np.cos(a), np.sqrt(1 - z * z) * np.sin(a), z]
rel = xyz - pocket
along = rel @ dirs.T
clear = []
for k in range(n):
    s = along[:, k]
    off = np.linalg.norm(rel - s[:, None] * dirs[k], axis=1)
    clear.append(off[s > 2].min())
clear = np.array(clear)
best = dirs[np.argsort(-clear)[:12]]
mouth = best.mean(0) / np.linalg.norm(best.mean(0))
print("widest way out %.1f A" % clear.max())

centre = xyz.mean(0)
P = xyz - centre
rad = np.array([G.VDW.get(e, 1.7) for e in el])
lo, hi = P.min(0) - PAD, P.max(0) + PAD
c = np.ceil((hi - lo) / H).astype(int) + 1
ax = [(lo[j] + H * np.arange(c[j])).astype(np.float32) for j in range(3)]
F = np.zeros(c, np.float32)
for p, r in zip(P, rad):
    reach = r * 3.0
    i0 = np.maximum(np.floor((p - reach - lo) / H).astype(int), 0)
    i1 = np.minimum(np.floor((p + reach - lo) / H).astype(int) + 2, c)
    d2 = (ax[0][i0[0]:i1[0], None, None] - p[0]) ** 2 + (ax[1][None, i0[1]:i1[1], None] - p[1]) ** 2 + (ax[2][None, None, i0[2]:i1[2]] - p[2]) ** 2
    F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += np.exp(-K_BLOB * (d2 / r ** 2 - 1))
verts, quads = G.surface_nets((F - 1) / 1.3, lo, H, relax=6)
np.savez_compressed(OUT, verts=verts.astype(np.float32), quads=quads.astype(np.int32), pocket=pocket - centre, mouth=mouth)
print(len(verts), "verts", len(quads), "quads; size", (verts.max(0) - verts.min(0)).round(1), "pocket", (pocket - centre).round(1), "mouth", mouth.round(2))
