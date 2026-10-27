"""T6: dock the real ISM042-2-001 and -048 into the AlphaFold CDK20 model with AutoDock Vina.

Structures were read off Ren et al. 2023 Fig. 5 / Fig. 7 and checked against the SI LCMS masses
(001: C14H13N5O, [M+H]+ 268; 048: C17H15N7O, [M+H]+ 334). The receptor is the AlphaFold model trimmed to
residues 1-302, as in the paper. This is our own re-docking for visualisation, not the authors' poses.

Usage: python dock.py <af_pdb> <vina.exe> <out_dir>
"""
import sys, json, subprocess
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from meeko import MoleculePreparation, PDBQTWriterLegacy, PDBQTMolecule, RDKitMolCreate
from openbabel import pybel

AF, VINA, OUT = sys.argv[1], sys.argv[2], sys.argv[3].rstrip("/\\")
LIGANDS = {
    "001": "CNC(=O)c1cc(Nc2ncc3ccccc3n2)c[nH]1",
    "048": "CNC(=O)c1cc(Nc2ncc3ccc(-c4cn[nH]c4)cc3n2)c[nH]1",
}
POCKET_RES = [10, 33, 81, 84, 85, 87, 90, 146]  # P-loop Ile10, Lys33, gatekeeper Phe81, hinge Met84/Leu85, Asp87, Glu90, DFG Phe146
SEED, EXH, BOX = 20261025, 32, 22.0

# ---- receptor: residues 1-302, hydrogens at pH 7.4, rigid PDBQT
atoms = []
with open(AF, encoding="utf-8") as f:
    lines = [l for l in f if l.startswith("ATOM") and int(l[22:26]) <= 302]
open(f"{OUT}/rec_1-302.pdb", "w").write("".join(lines) + "END\n")
for l in lines:
    atoms.append((int(l[22:26]), l[17:20], l[12:16].strip(), np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])])))
rec = next(pybel.readfile("pdb", f"{OUT}/rec_1-302.pdb"))
rec.OBMol.AddHydrogens(False, True, 7.4)
rec.write("pdbqt", f"{OUT}/rec.pdbqt", overwrite=True, opt={"r": None})

pocket = np.array([a[3] for a in atoms if a[0] in POCKET_RES and a[2] not in ("N", "C", "O")])
center = pocket.mean(axis=0)
get = lambda res, name: next(a[3] for a in atoms if a[0] == res and a[2] == name)
MET84_N, MET84_O, LEU85_N = get(84, "N"), get(84, "O"), get(85, "N")
LYS33_NZ = get(33, "NZ")

report = {"box_center": center.round(2).tolist(), "box_size": BOX, "exhaustiveness": EXH, "seed": SEED, "ligands": {}}
for name, smi in LIGANDS.items():
    mol = Chem.AddHs(Chem.MolFromSmiles(smi))
    AllChem.EmbedMolecule(mol, randomSeed=SEED)
    AllChem.MMFFOptimizeMolecule(mol)
    setup = MoleculePreparation().prepare(mol)[0]
    pdbqt, ok, err = PDBQTWriterLegacy.write_string(setup)
    open(f"{OUT}/lig_{name}.pdbqt", "w").write(pdbqt)
    subprocess.run([VINA, "--receptor", f"{OUT}/rec.pdbqt", "--ligand", f"{OUT}/lig_{name}.pdbqt",
                    "--center_x", str(center[0]), "--center_y", str(center[1]), "--center_z", str(center[2]),
                    "--size_x", str(BOX), "--size_y", str(BOX), "--size_z", str(BOX),
                    "--exhaustiveness", str(EXH), "--num_modes", "9", "--seed", str(SEED),
                    "--out", f"{OUT}/dock_{name}.pdbqt"], check=True, capture_output=True)
    poses = RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(open(f"{OUT}/dock_{name}.pdbqt").read(), skip_typing=True))[0]
    scores = [float(l.split()[3]) for l in open(f"{OUT}/dock_{name}.pdbqt") if l.startswith("REMARK VINA RESULT")]
    w = Chem.SDWriter(f"{OUT}/dock_{name}.sdf")
    modes = []
    for cid, conf in enumerate(poses.GetConformers()):
        xyz = conf.GetPositions()
        polar = [i for i, a in enumerate(poses.GetAtoms()) if a.GetSymbol() in ("N", "O")]
        d = lambda p: round(float(min(np.linalg.norm(xyz[i] - p) for i in polar)), 2)
        mode = {"mode": cid + 1, "vina_kcal_mol": scores[cid], "hinge_Met84_N": d(MET84_N), "hinge_Met84_O": d(MET84_O),
                "Leu85_N": d(LEU85_N), "Lys33_NZ": d(LYS33_NZ)}
        mode["hinge_contact"] = min(mode["hinge_Met84_N"], mode["hinge_Met84_O"]) <= 3.5
        modes.append(mode)
        poses.SetProp("_Name", f"ISM042-2-{name} mode {cid + 1} ({scores[cid]} kcal/mol)")
        w.write(poses, confId=conf.GetId())
    w.close()
    heavy = Chem.RemoveHs(mol)
    report["ligands"][name] = {"smiles": smi, "formula": rdMolDescriptors.CalcMolFormula(heavy),
                               "mw": round(Descriptors.MolWt(heavy), 2), "mh_plus_mono": round(Descriptors.ExactMolWt(heavy) + 1.00728, 2),
                               "modes": modes}
    print(name, json.dumps(modes[:3]))
json.dump(report, open(f"{OUT}/dock_report.json", "w"), indent=2)
