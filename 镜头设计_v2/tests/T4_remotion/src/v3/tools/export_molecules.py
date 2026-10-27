import json, sys, math
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdDepictor
from rdkit.Chem import rdFMCS

out = sys.argv[1]
S001 = "CNC(=O)c1cc(Nc2ncc3ccccc3n2)c[nH]1"
S048 = "CNC(=O)c1cc(Nc2ncc3ccc(-c4cn[nH]c4)cc3n2)c[nH]1"

rdDepictor.SetPreferCoordGen(True)
m48 = Chem.MolFromSmiles(S048)
m01 = Chem.MolFromSmiles(S001)
rdDepictor.Compute2DCoords(m48)

# orient 048: principal axis horizontal
conf = m48.GetConformer()
P = np.array([[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y] for i in range(m48.GetNumAtoms())])
c = P.mean(0); Q = P - c
w, v = np.linalg.eigh(Q.T @ Q)
ax = v[:, np.argmax(w)]
ang = math.atan2(ax[1], ax[0])
R = np.array([[math.cos(-ang), -math.sin(-ang)], [math.sin(-ang), math.cos(-ang)]])
Q = Q @ R.T
# put the pyrazole on the right side
match = m48.GetSubstructMatch(m01)
new_atoms = [i for i in range(m48.GetNumAtoms()) if i not in match]
if Q[new_atoms, 0].mean() < 0:
    Q[:, 0] *= -1
from rdkit.Geometry import Point3D
for i in range(m48.GetNumAtoms()):
    conf.SetAtomPosition(i, Point3D(float(Q[i, 0]), float(Q[i, 1]), 0.0))

# 001 drawn with identical coords for the shared atoms
m01_match_in_48 = m48.GetSubstructMatch(m01)  # m01 atom k -> m48 atom match[k]
conf01 = Chem.Conformer(m01.GetNumAtoms())
for k, j in enumerate(m01_match_in_48):
    conf01.SetAtomPosition(k, conf.GetAtomPosition(j))
m01.AddConformer(conf01, assignId=True)

def export(m, extra=None):
    mk = Chem.Mol(m)
    Chem.Kekulize(mk, clearAromaticFlags=False)
    conf = m.GetConformer()
    atoms = []
    for a in m.GetAtoms():
        p = conf.GetAtomPosition(a.GetIdx())
        atoms.append(dict(i=a.GetIdx(), el=a.GetSymbol(), x=round(p.x, 4), y=round(-p.y, 4),  # y flipped for screen
                          h=a.GetTotalNumHs(), arom=a.GetIsAromatic()))
    bonds = []
    for b in mk.GetBonds():
        bonds.append(dict(a=b.GetBeginAtomIdx(), b=b.GetEndAtomIdx(), order=int(round(b.GetBondTypeAsDouble())),
                          ring=b.IsInRing()))
    rings = [list(r) for r in m.GetRingInfo().AtomRings()]
    d = dict(smiles=Chem.MolToSmiles(m), atoms=atoms, bonds=bonds, rings=rings)
    if extra: d.update(extra)
    return d

d48 = export(m48, dict(newAtoms=new_atoms))
d01 = export(m01, dict(mapTo048=list(m01_match_in_48)))
# check shared coords agree
err = max(abs(d01["atoms"][k]["x"] - d48["atoms"][j]["x"]) + abs(d01["atoms"][k]["y"] - d48["atoms"][j]["y"]) for k, j in enumerate(m01_match_in_48))
print("coord mismatch", err)
print("bond length", np.mean([np.linalg.norm(Q[b.GetBeginAtomIdx()] - Q[b.GetEndAtomIdx()]) for b in m48.GetBonds()]))
print("bbox 048", Q.min(0), Q.max(0))
json.dump({"m001": d01, "m048": d48, "source": "RDKit " + Chem.rdBase.rdkitVersion + " CoordGen 2D depiction; y flipped for screen; units = RDKit (bond ~1.0-1.5)"}, open(out, "w"), indent=1)
print("new atoms", new_atoms, [m48.GetAtomWithIdx(i).GetSymbol() for i in new_atoms])
