"""Parse the AlphaFold DB CDK20 model (AF-Q8IZL9-F1 v6, CC BY 4.0) into a compact JSON:
per residue: CA, C, O (Angstrom, centred on CA centroid, principal axes aligned), pLDDT, secondary structure (H/E/C).
Run: python -I prep_protein.py
"""
import json, os
import numpy as np

ROOT = "D:/。hkbu/molecular science/镜头设计_v3"
PDB = ROOT + "/assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
CIF = ROOT + "/assets/alphafold/AF-Q8IZL9-F1-model_v6.cif"
OUT = ROOT + "/styleframes/S1/v2/_code/s110/cdk20_backbone.json"

res = {}
for ln in open(PDB):
    if not ln.startswith("ATOM"):
        continue
    name = ln[12:16].strip(); seq = int(ln[22:26]); aa = ln[17:20]
    xyz = [float(ln[30:38]), float(ln[38:46]), float(ln[46:54])]
    b = float(ln[60:66])
    r = res.setdefault(seq, {"aa": aa, "plddt": b})
    if name in ("CA", "C", "O", "N"):
        r[name] = xyz

ss = {k: "C" for k in res}
lines = open(CIF).read().split("\n")
for ln in lines:
    p = ln.split()
    if len(p) > 10 and p[0] == "A" and p[6].startswith(("STRN", "HELX")):
        b, e, t = int(p[2]), int(p[9]), p[6]
        code = "E" if t == "STRN" else ("H" if t.startswith("HELX_RH_AL") else "C")
        for k in range(b, e + 1):
            if code != "C":
                ss[k] = code

keys = sorted(res)
CA = np.array([res[k]["CA"] for k in keys])
cen = CA.mean(0)
X = CA - cen
# principal axes: longest along x
w, V = np.linalg.eigh(np.cov(X.T))
V = V[:, ::-1]
if np.linalg.det(V) < 0:
    V[:, 2] *= -1
R = lambda p: ((np.array(p) - cen) @ V).round(3).tolist()
out = [{"i": k, "aa": res[k]["aa"], "plddt": res[k]["plddt"], "ss": ss[k],
        "ca": R(res[k]["CA"]), "c": R(res[k]["C"]), "o": R(res[k]["O"])} for k in keys]
json.dump({"source": "AlphaFold DB AF-Q8IZL9-F1 model v6 (CC BY 4.0), predicted", "res": out}, open(OUT, "w"))
s = "".join(ss[k] for k in keys)
print(len(out), "residues;", s.count("H"), "H", s.count("E"), "E")
print(s)
pl = np.array([r["plddt"] for r in out]); print("plddt min/mean/max", pl.min(), pl.mean().round(1), pl.max())
print("extent", (CA - cen).__matmul__(V).min(0).round(1), (CA - cen).__matmul__(V).max(0).round(1))
