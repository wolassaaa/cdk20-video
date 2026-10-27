"""Export chosen docked poses + receptor context as JSON for the Blender render.

Usage: python export_poses.py <work_dir> <out_json>
Chosen poses: 001 mode 3 (two hinge H-bonds to Met84), 048 mode 2 (hinge + pyrazole to Lys33 + pyrrole NH to Ile10).
"""
import sys, json
import numpy as np
from rdkit import Chem

W, OUT = sys.argv[1].rstrip("/\\"), sys.argv[2]
CHOSEN = {"001": 3, "048": 2}
KEY_RES = {84: "Met84", 33: "Lys33", 10: "Ile10", 81: "Phe81", 85: "Leu85"}
PARTNERS = {"Met84 N": (84, "N"), "Met84 O": (84, "O"), "Lys33 NZ": (33, "NZ"), "Ile10 O": (10, "O")}

rec = []
for l in open(f"{W}/rec_1-302.pdb"):
    if l.startswith("ATOM"):
        rec.append({"res": int(l[22:26]), "resn": l[17:20], "name": l[12:16].strip(), "el": l[76:78].strip() or l[12:14].strip()[0],
                    "xyz": [float(l[30:38]), float(l[38:46]), float(l[46:54])]})
pos = {(a["res"], a["name"]): np.array(a["xyz"]) for a in rec}

out = {"ca": [[a["res"], *a["xyz"]] for a in rec if a["name"] == "CA"], "residues": {}, "poses": {}}
for r, label in KEY_RES.items():
    ats = [a for a in rec if a["res"] == r]
    out["residues"][label] = {"atoms": [[a["name"], a["el"], *a["xyz"]] for a in ats]}

for name, mode in CHOSEN.items():
    m = Chem.SDMolSupplier(f"{W}/dock_{name}.sdf", removeHs=False)[mode - 1]
    x = m.GetConformer().GetPositions()
    keep = [a.GetIdx() for a in m.GetAtoms() if a.GetSymbol() != "H" or a.GetNeighbors()[0].GetSymbol() in ("N", "O")]
    idx = {i: k for k, i in enumerate(keep)}
    atoms = [[m.GetAtomWithIdx(i).GetSymbol(), *x[i].round(3).tolist()] for i in keep]
    bonds = [[idx[b.GetBeginAtomIdx()], idx[b.GetEndAtomIdx()], b.GetBondTypeAsDouble()] for b in m.GetBonds()
             if b.GetBeginAtomIdx() in idx and b.GetEndAtomIdx() in idx]
    contacts = []
    for label, key in PARTNERS.items():
        best = min(((float(np.linalg.norm(x[i] - pos[key])), i) for i in keep if m.GetAtomWithIdx(i).GetSymbol() in ("N", "O")))
        if best[0] <= 3.6:
            contacts.append({"partner": label, "dist": round(best[0], 2), "lig": x[best[1]].round(3).tolist(), "rec": pos[key].round(3).tolist()})
    score = float(m.GetProp("_Name").split("(")[1].split()[0])
    out["poses"][name] = {"mode": mode, "vina": score, "atoms": atoms, "bonds": bonds, "contacts": contacts}
    print(name, mode, score, [(c["partner"], c["dist"]) for c in contacts])
json.dump(out, open(OUT, "w"))
