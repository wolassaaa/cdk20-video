"""HKBU SCIE1007 coursework science video, dawn art direction. Builds the CDK20 surfaces used as terrain, numpy only.

Same atoms, same frame and same per-residue pLDDT as S2plus/code/make_surface.py, but a sharper Gaussian surface, so the atom-scale relief reads as crags under a low light.
Writes _work/rock_full.npz (residues 1-346, for T4) and _work/rock_302.npz (residues 1-302, the receptor the docking used, for T5), plus the 048 pose in the same frame.
"""
import json, sys
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
S2 = HERE.parents[2] / "S2plus" / "code"
sys.path.insert(0, str(S2))
import pocket048 as G

V3 = HERE.parents[3]
PDB = V3 / "assets" / "alphafold" / "AF-Q8IZL9-F1-model_v6.pdb"
OUT = HERE.parent / "_work"
OUT.mkdir(exist_ok=True)
VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]  # same frame as make_surface.py
H, PAD, K_BLOB = 0.2, 5.0, 3.6

xyz, el, res, pl, ca, ca_i = [], [], [], [], [], []
for l in PDB.read_text(encoding="utf8").splitlines():
    if not l.startswith("ATOM"):
        continue
    e = l[76:78].strip()
    if e == "H":
        continue
    p = [float(l[30:38]), float(l[38:46]), float(l[46:54])]
    xyz.append(p); el.append(e); res.append(int(l[22:26])); pl.append(float(l[60:66]))
    if l[12:16].strip() == "CA" and int(l[22:26]) <= 302:
        ca.append(p); ca_i.append(int(l[22:26]))
xyz, ca = np.array(xyz), np.array(ca)
pl, res = np.array(pl, np.float32), np.array(res)
u, _, vt = np.linalg.svd(np.array(VIEW))
R = u @ vt
T = lambda q: (np.asarray(q, float) - ca.mean(0)) @ R.T
P = T(xyz)

# the docked pose lives in the receptor file's coordinates: check they are the AlphaFold ones before reusing them
rec = {}
for l in open(G.PDB):
    if l.startswith("ATOM") and l[12:16].strip() == "CA":
        rec[int(l[22:26])] = [float(l[30:38]), float(l[38:46]), float(l[46:54])]
same = np.mean([np.linalg.norm(np.array(rec[i]) - ca[ca_i.index(i)]) for i in ca_i if i in rec])
print("mean CA offset, rec_1-302 vs AF v6:", round(float(same), 3), "A")

pose = json.load(open(G.POSES))["poses"]["048"]
pe = [a[0] for a in pose["atoms"]]
px = T([a[1:] for a in pose["atoms"]])
np.savez(OUT / "pose048.npz", el=np.array(pe), xyz=px.astype(np.float32), bonds=np.array(pose["bonds"], np.float32),
         lys=T([c["rec"] for c in pose["contacts"] if c["partner"].startswith("Lys33")][0]).astype(np.float32),
         lys_lig=T([c["lig"] for c in pose["contacts"] if c["partner"].startswith("Lys33")][0]).astype(np.float32))
print("ligand centre", px.mean(0).round(1), "bonds", len(pose["bonds"]), "contacts", [c["partner"] for c in pose["contacts"]])


def build(keep, name):
    Q, rad, s = P[res <= keep], np.array([G.VDW.get(e, 1.7) for e in np.array(el)[res <= keep]]), pl[res <= keep]
    lo, hi = Q.min(0) - PAD, Q.max(0) + PAD
    n = np.ceil((hi - lo) / H).astype(int) + 1
    ax = [(lo[i] + H * np.arange(n[i])).astype(np.float32) for i in range(3)]
    F, WP = np.zeros(n, np.float32), np.zeros(n, np.float32)
    for p, r, c in zip(Q, rad, s):
        reach = r * 2.2
        i0 = np.maximum(np.floor((p - reach - lo) / H).astype(int), 0)
        i1 = np.minimum(np.floor((p + reach - lo) / H).astype(int) + 2, n)
        d2 = (ax[0][i0[0]:i1[0], None, None] - p[0]) ** 2 + (ax[1][None, i0[1]:i1[1], None] - p[1]) ** 2 + (ax[2][None, None, i0[2]:i1[2]] - p[2]) ** 2
        w = np.exp(-K_BLOB * (d2 / r ** 2 - 1))
        F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += w
        WP[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += w * c
    v, q = G.surface_nets((F - 1) / 1.3, lo, H, relax=1)
    cells = np.clip(np.round((v - lo) / H).astype(int), 0, n - 1)
    conf = WP[tuple(cells.T)] / np.maximum(F[tuple(cells.T)], 1e-6) / 100.0
    np.savez(OUT / f"{name}.npz", verts=v.astype(np.float32), quads=q.astype(np.int32), conf=conf.astype(np.float32), lo=lo, H=H)
    np.save(OUT / f"{name}_field.npy", F.astype(np.float16))
    print(name, len(v), "verts", "conf", conf.min().round(2), conf.max().round(2), flush=True)


build(346, "rock_full")
build(302, "rock_302")
