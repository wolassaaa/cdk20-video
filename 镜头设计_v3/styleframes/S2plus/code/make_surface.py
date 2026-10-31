# HKBU SCIE1007 coursework science video. Builds the CDK20 surface used by the engraved stills, numpy only, no GPU.
# Geometry: every heavy atom of AlphaFold AF-Q8IZL9-F1 v6, residues 1-346, in the camera frame of make_protein_points.py, as a Gaussian surface.
# Confidence: the real per-residue pLDDT, carried on to each vertex, so line width in bl_lines.py is data and not decoration.
# Output: S2plus/_work/cdk20_surface.npz (verts in Angstrom, quads, conf 0-1, x right, y up, z to the lens). _work is not in the repo.
import sys
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pocket048 as G

V3 = HERE.parents[2]
PDB = V3 / "assets" / "alphafold" / "AF-Q8IZL9-F1-model_v6.pdb"
OUT = HERE.parent / "_work" / "cdk20_surface.npz"
OUT.parent.mkdir(exist_ok=True)

VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]  # same as make_protein_points.py
KEEP_TO, H, PAD = 302, 0.3, 6.0   # the camera centre uses residues 1-302, as make_protein_points.py does; grid step and padding, Angstrom
K_BLOB, SHRINK = 0.9, 1.0         # softer than the pocket: this surface is seen whole, so it should read as one mass

xyz, el, res, pl = [], [], [], []
ca = []
for l in PDB.read_text(encoding="utf8").splitlines():
    if not l.startswith("ATOM"):
        continue
    e = l[76:78].strip()
    if e == "H":
        continue
    p = [float(l[30:38]), float(l[38:46]), float(l[46:54])]
    xyz.append(p); el.append(e); res.append(int(l[22:26])); pl.append(float(l[60:66]))
    if l[12:16].strip() == "CA" and int(l[22:26]) <= KEEP_TO:
        ca.append(p)
xyz, ca = np.array(xyz), np.array(ca)
pl, res = np.array(pl, np.float32), np.array(res)
assert res.max() == 346 and res.min() == 1

u, _, vt = np.linalg.svd(np.array(VIEW))
R = u @ vt
assert abs(np.linalg.det(R) - 1) < 1e-9
P = (xyz - ca.mean(0)) @ R.T
rad = np.array([G.VDW.get(e, 1.7) * SHRINK for e in el])

lo, hi = P.min(0) - PAD, P.max(0) + PAD
n = np.ceil((hi - lo) / H).astype(int) + 1
ax = [(lo[i] + H * np.arange(n[i])).astype(np.float32) for i in range(3)]
print(f"{len(P)} heavy atoms, grid {n.tolist()}, {np.prod(n) / 1e6:.1f} M cells")
F, WP = np.zeros(n, np.float32), np.zeros(n, np.float32)
for p, r, s in zip(P, rad, pl):
    reach = r * 2.6
    i0 = np.maximum(np.floor((p - reach - lo) / H).astype(int), 0)
    i1 = np.minimum(np.floor((p + reach - lo) / H).astype(int) + 2, n)
    d2 = (ax[0][i0[0]:i1[0], None, None] - p[0]) ** 2 + (ax[1][None, i0[1]:i1[1], None] - p[1]) ** 2 + (ax[2][None, None, i0[2]:i1[2]] - p[2]) ** 2
    w = np.exp(-K_BLOB * (d2 / r ** 2 - 1))
    F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += w
    WP[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += w * s

verts, quads = G.surface_nets((F - 1) / 1.3, lo, H, relax=3)
cells = np.clip(np.round((verts - lo) / H).astype(int), 0, n - 1)
conf = WP[tuple(cells.T)] / np.maximum(F[tuple(cells.T)], 1e-6) / 100.0
assert 0 < conf.min() and conf.max() <= 1.0
np.savez_compressed(OUT, verts=verts.astype(np.float32), quads=quads.astype(np.int32), conf=conf.astype(np.float32))
print(f"{len(verts)} verts, {len(quads)} quads; x {verts[:, 0].min():.1f}..{verts[:, 0].max():.1f}, y {verts[:, 1].min():.1f}..{verts[:, 1].max():.1f}, z {verts[:, 2].min():.1f}..{verts[:, 2].max():.1f} A")
print(f"confidence on the surface {conf.min():.2f}..{conf.max():.2f}, wrote {OUT}")
