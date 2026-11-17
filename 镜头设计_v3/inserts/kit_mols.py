"""HKBU SCIE1007 课程作业的科普视频：给零件库准备三个小分子件和香港轮廓的数据（写到 kit_data.json，kit_parts.py 读它）。

- 001、048：论文里的两个化合物。结构是之前从 Ren et al. 2023 的图 5、图 7 读出来、用 SI 里的质谱分子量核过的，
  三维坐标用我们自己重对接的姿态（镜头设计_v2/tests/T6_molecules/poses.json）。只留非氢原子。
- ATP：公开的常见分子，用 RDKit 从 SMILES 生成三维坐标。
- 香港轮廓、地球仪的陆地栅格：Natural Earth 1:10m admin-0（公有领域）。
- credits：片尾要写的来源（器官网格是 BodyParts3D, © The Database Center for Life Science, CC BY 4.0）。
每个分子转到自己的主平面上（最长的方向放横、最薄的方向朝上），零件就能平躺在板里。

    PYTHONPATH=G:/cdk20/work/kit/pydeps python kit_mols.py NE_GEOJSON
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

HERE = Path(__file__).parent
POSES = HERE / "../../镜头设计_v2/tests/T6_molecules/poses.json"
ATP = "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O"


def flat(el, xyz, bonds):
    xyz = np.array(xyz, float); xyz -= xyz.mean(0)
    w, v = np.linalg.eigh(np.cov(xyz.T))
    R = v[:, ::-1]                                   # 最长、次长、最薄
    if np.linalg.det(R) < 0:
        R[:, 2] *= -1
    q = xyz @ R
    return {"atoms": [[e, round(float(a), 3), round(float(b), 3), round(float(c), 3)] for e, (a, b, c) in zip(el, q)], "bonds": bonds}


out = {}
P = json.loads(POSES.read_text(encoding="utf-8"))["poses"]
for k in ("001", "048"):
    A, B = P[k]["atoms"], P[k]["bonds"]
    keep = [i for i, a in enumerate(A) if a[0] != "H"]
    idx = {i: n for n, i in enumerate(keep)}
    out[k] = flat([A[i][0] for i in keep], [A[i][1:4] for i in keep], [[idx[b[0]], idx[b[1]]] for b in B if b[0] in idx and b[1] in idx])
m = Chem.AddHs(Chem.MolFromSmiles(ATP))
AllChem.EmbedMolecule(m, randomSeed=20261117); AllChem.MMFFOptimizeMolecule(m)
m = Chem.RemoveHs(m); c = m.GetConformer()
out["ATP"] = flat([a.GetSymbol() for a in m.GetAtoms()], [list(c.GetAtomPosition(i)) for i in range(m.GetNumAtoms())],
                  [[b.GetBeginAtomIdx(), b.GetEndAtomIdx()] for b in m.GetBonds()])
if len(sys.argv) > 1:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    g = next(f for f in d["features"] if f["properties"].get("NAME") == "Hong Kong")["geometry"]["coordinates"]
    k = math.cos(math.radians(22.35))
    out["HK"] = [[[round(x * k, 5), round(y, 5)] for x, y in poly[0][:-1]] for poly in g]
if len(sys.argv) > 1:                                 # 地球仪用的陆地栅格：720 × 360，一格半度，陆地 1、海 0
    import base64
    from PIL import Image, ImageDraw
    Wd, Hd = 720, 360
    im = Image.new("1", (Wd, Hd), 0); dr = ImageDraw.Draw(im)
    for f in d["features"]:
        g2 = f["geometry"]
        for poly in (g2["coordinates"] if g2["type"] == "MultiPolygon" else [g2["coordinates"]]):
            dr.polygon([((x + 180) / 360 * Wd, (90 - y) / 180 * Hd) for x, y in poly[0]], fill=1)
    out["LAND"] = {"w": Wd, "h": Hd, "bits": base64.b64encode(np.packbits(np.array(im, dtype=np.uint8)).tobytes()).decode()}
out["credits"] = ["BodyParts3D, © The Database Center for Life Science, CC BY 4.0 (liver, liver vessels, lungs, airways, colon, rectum meshes)",
                  "Made with Natural Earth (Hong Kong outline, land mask on the globe), public domain",
                  "CDK20 shape: AlphaFold Protein Structure Database, AF-Q8IZL9-F1, CC BY 4.0",
                  "Compounds 001 and 048: structures from Ren et al., Chem. Sci. 2023; poses are our own re-docking"]
(HERE / "kit_data.json").write_text(json.dumps(out), encoding="utf-8")
for k, v in out.items():
    if k in ("LAND", "credits"):
        continue
    if k == "HK":
        a = np.concatenate([np.array(p) for p in v]); print(k, len(v), a.min(0), a.max(0))
    else:
        a = np.array([x[1:] for x in v["atoms"]]); print(k, len(v["atoms"]), len(v["bonds"]), a.min(0).round(1), a.max(0).round(1))
