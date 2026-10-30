"""Fig. 5 (Ren 2023) first-round compounds -> 2D coordinates for still 07.

The seven IDs are traceable: the ESI synthesis section (SC-014-D2SC05709C-s001.pdf)
runs 001 (p2), 004 (p3), 007 (p4), 009 (p5), 015 (p6), 019 (p8), 025 (p9) and only
then starts the round-2 block at 048 (p11). That is exactly the "7 compounds selected
for synthesis" of the Results text, so the IDs below are sourced, not guessed.

The STRUCTURES are a different matter. Ren 2023 gives the seven structures only as
the Fig. 5 bitmap; neither the article text nor the ESI prints a SMILES, and the ESI
names intermediates as "ISM042-2-004-1" rather than chemically. So only 001 has a
SMILES we can trace, and only 001 gets coordinates here. The other six stay unsourced
and still 07 draws them as pending slots.

Do NOT fill a `smiles` in below from the figure by eye. A structure read off a bitmap
is an invented structure, which is what research/marathon_refs_20261031.md section 5
rule 5 forbids. It needs someone who can read Fig. 5, and 025 additionally needs the
stereocentre call recorded in STEREO_NOTE.

Run: <repo>/镜头设计_v2/tests/T1_hand/.venv/Scripts/python.exe make_fig5.py
Out: 镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/fig5_seven.json
Exits non-zero on any check failure; it never adjusts a value to make a check pass.
"""
import json
import pathlib
import sys

from rdkit import Chem
from rdkit.Chem import Descriptors, rdCoordGen

ROOT = pathlib.Path(__file__).resolve().parents[4]  # code -> S2plus -> styleframes -> 镜头设计_v3 -> repo
OUT = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/fig5_seven.json"
MOLECULES = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/molecules.json"

# Kd labels are verbatim from marathon_refs_20261031.md section 4 still 7.
# 001 = 9.2 µM (E14); the other six are "> 30 µM" (script flag F12: beyond the
# reported range, so "barely held on", never "no binding").
SIX = "> 30 µM"
COMPOUNDS = [
    # id,     ESI page, Kd label (screen text),  SMILES or None
    ("001", 2, "001: 9.2 µM", "CNC(=O)c1cc(Nc2ncc3ccccc3n2)c[nH]1"),
    ("004", 3, SIX, None),
    ("007", 4, SIX, None),
    ("009", 5, SIX, None),
    ("015", 6, SIX, None),
    ("019", 8, SIX, None),
    ("025", 9, SIX, None),
]

UNSOURCED = "no SMILES in Ren 2023 text or ESI; Fig. 5 is a bitmap. Needs a figure read."
STEREO_NOTE = (
    "025 carries a stereocentre that this source does not define: the ESI entry (p9-p10) "
    "gives no (R)/(S) descriptor, no chiral reagent and no resolution step, and its final "
    "1H NMR shows a single CH multiplet at 4.60-4.72 ppm with diastereotopic CH2 signals. "
    "If 025 is ever drawn, draw that centre flat (no wedge, no hash) unless a chemist "
    "confirms the configuration. Do not pick one to make the drawing look finished."
)
# 001's structure is cross-checked twice over, so it is safe to draw:
#   ESI p2 final step couples CH3NH2 -> the N-methyl amide of the SMILES, and its
#   1H NMR 3.01 (d, J = 4.80 Hz, 3H) is that N-CH3;
#   ESI p2 reports LCMS [M+H]+ 268.0 against 268.1 computed below.
MH_PLUS_EXPECTED = 268.0
MH_PLUS_TOLERANCE = 0.3


def depict(smiles):
    """2D coordinates in molecules.json's convention: CoordGen, y flipped for screen."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None
    Chem.Kekulize(mol, clearAromaticFlags=False)  # orders become 1/2 so bonds draw skeletally
    rdCoordGen.AddCoords(mol)
    conf = mol.GetConformer()
    atoms = [{"i": a.GetIdx(), "el": a.GetSymbol(),
              "x": round(conf.GetAtomPosition(a.GetIdx()).x, 4),
              "y": round(-conf.GetAtomPosition(a.GetIdx()).y, 4),  # flip: SVG y grows downward
              "h": a.GetTotalNumHs(), "arom": a.GetIsAromatic()} for a in mol.GetAtoms()]
    bonds = [{"a": b.GetBeginAtomIdx(), "b": b.GetEndAtomIdx(),
              "order": 2 if b.GetBondType() == Chem.BondType.DOUBLE else
                       3 if b.GetBondType() == Chem.BondType.TRIPLE else 1,
              "ring": b.IsInRing()} for b in mol.GetBonds()]
    rings = [list(r) for r in mol.GetRingInfo().AtomRings()]
    return mol, {"atoms": atoms, "bonds": bonds, "rings": rings}


def main():
    fails = []
    out = []
    for cid, page, kd, smiles in COMPOUNDS:
        row = {"id": cid, "esi_page": page, "kd": kd, "sourced": smiles is not None,
               "smiles": smiles, "note": None if smiles else UNSOURCED}
        if smiles:
            mol, geom = depict(smiles)
            if mol is None:
                fails.append(f"{cid}: SMILES does not parse: {smiles}")
            else:
                row.update(geom)
                row["formula"] = Chem.rdMolDescriptors.CalcMolFormula(mol)
                row["mh_plus"] = round(Descriptors.ExactMolWt(mol) + 1.00728, 2)
        if cid == "025":
            row["stereo_note"] = STEREO_NOTE
        out.append(row)

    # --- checks: the script reports, it does not repair ---
    if len(out) != 7:
        fails.append(f"expected the 7 first-round compounds, built {len(out)}")

    one = next(r for r in out if r["id"] == "001")
    if one["sourced"]:
        if abs(one["mh_plus"] - MH_PLUS_EXPECTED) > MH_PLUS_TOLERANCE:
            fails.append(f"001 [M+H]+ {one['mh_plus']} != ESI p2 {MH_PLUS_EXPECTED}")
        # the repo already holds a vetted depiction of 001; counts must agree with it
        if MOLECULES.exists():
            m001 = json.loads(MOLECULES.read_text(encoding="utf8"))["m001"]
            if m001["smiles"] != one["smiles"]:
                fails.append("001 SMILES disagrees with molecules.json")
            if len(m001["atoms"]) != len(one["atoms"]) or len(m001["bonds"]) != len(one["bonds"]):
                fails.append("001 atom/bond counts disagree with molecules.json")
        else:
            fails.append(f"molecules.json not found at {MOLECULES}")

    for r in out:
        if r["sourced"] and not r.get("atoms"):
            fails.append(f"{r['id']} is marked sourced but has no coordinates")
        if not r["sourced"] and r.get("atoms"):
            fails.append(f"{r['id']} is marked unsourced but carries coordinates")

    payload = {
        "source": "RDKit %s CoordGen 2D depiction; y flipped for screen; units = RDKit (bond ~1.0-1.5)"
                  % Chem.rdBase.rdkitVersion,
        "compounds": out,
        "sourced": [r["id"] for r in out if r["sourced"]],
        "unsourced": [r["id"] for r in out if not r["sourced"]],
    }

    n_src = len(payload["sourced"])
    print(f"Fig. 5 first-round compounds: {len(out)} IDs, {n_src} drawable, "
          f"{len(out) - n_src} pending a figure read ({', '.join(payload['unsourced'])})")
    if one["sourced"]:
        print(f"001  {one['formula']}  [M+H]+ {one['mh_plus']} vs ESI p2 {MH_PLUS_EXPECTED}  "
              f"{len(one['atoms'])} atoms  {len(one['bonds'])} bonds")

    if fails:
        for f in fails:
            print("FAIL", f)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf8")
    print("ok ->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
