"""Pack the real AlphaFold CDK20 model (AF-Q8IZL9, CC BY 4.0) and our re-docked 048 pose into textures for TouchDesigner.

atoms.npy (H, 64, 4): x y z (Å, centred on the docked ligand = the ATP pocket) + pLDDT (AlphaFold confidence 0-100)
meta.npy  (H, 64, 4): residue number, kind (0 protein, 1 ligand, -1 padding), element code (C1 N2 O3 S4 other0), is-CA
ca.npy    (n, 4):     CA trace in residue order (xyz + pLDDT) for the backbone ink line
usage: python prep_protein.py <model.pdb> <poses.json> <out_dir>
"""
import sys, os, json
import numpy as np

PDB, POSES, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
EL = {"C": 1, "N": 2, "O": 3, "S": 4}

atoms, meta, ca = [], [], []
for line in open(PDB):
    if not line.startswith("ATOM"):
        continue
    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
    res, b = int(line[22:26]), float(line[60:66])
    el = line[76:78].strip() or line[12:16].strip()[0]
    is_ca = line[12:16] == " CA "
    atoms.append([x, y, z, b])
    meta.append([res, 0, EL.get(el, 0), 1.0 if is_ca else 0.0])
    if is_ca:
        ca.append([x, y, z, b])

lig = json.load(open(POSES))["poses"]["048"]["atoms"]
for el, x, y, z in lig:
    if el == "H":
        continue
    atoms.append([x, y, z, 100.0])
    meta.append([0, 1, EL.get(el, 0), 0.0])

atoms, meta, ca = np.array(atoms, np.float32), np.array(meta, np.float32), np.array(ca, np.float32)
pocket = atoms[meta[:, 1] == 1, :3].mean(axis=0)
atoms[:, :3] -= pocket
ca[:, :3] -= pocket
W = 64
H = -(-len(atoms) // W)
pad = H * W - len(atoms)
atoms = np.vstack([atoms, np.zeros((pad, 4), np.float32)]).reshape(H, W, 4)
meta = np.vstack([meta, np.tile(np.array([[0, -1, 0, 0]], np.float32), (pad, 1))]).reshape(H, W, 4)
np.save(os.path.join(OUT, "atoms.npy"), atoms)
np.save(os.path.join(OUT, "meta.npy"), meta)
np.save(os.path.join(OUT, "ca.npy"), ca)
low = (ca[:, 3] < 50).sum()
print(f"atoms {H}x{W} (+{pad} pad), ligand atoms {(meta[..., 1] == 1).sum()}, CA {len(ca)}, low-confidence residues {low}, pocket centre {pocket.round(2)}")
