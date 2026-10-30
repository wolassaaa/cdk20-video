"""SCAN extra still (1-02 "top 3 deadliest in HK"): lung, colon + rectum, liver as hairline section stacks,
same spacing, same camera, true relative scale.

python prep_trio.py -> public/trio.bin + public/trio.json
Lung: BodyParts3D v3 lobes + bronchial tree + trachea. Colon: v3 colon + rectum. Liver: v4 segments + vessels.
"""
import json, os, time
import numpy as np
from slicer import ANAT, load_obj, load_stl, slice_mesh, shoelace, simplify_loop

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public")
V3 = ANAT + "bp3d_v3_stl/"
V4 = ANAT + "bp3d_v4_obj/"
DZ = 0.25
Q = 10
G = json.load(open(ANAT + "bp3d_v4_groups_stl/groups_report.json"))
ORG = {
    "lung": dict(skin=[V3 + f"FMA{k}.stl" for k in (7333, 7383, 7337, 7370, 7371)],
                 inner=[V3 + "FMA7409.stl", V3 + "FMA7394.stl"]),
    "colorectal": dict(skin=[V3 + "FMA14543nsn.stl", V3 + "FMA14544.stl"], inner=[]),
    "liver": dict(skin=[V4 + k + ".obj" for k in ("FJ2816", "FJ2818", "FJ2819", "FJ2820", "FJ2821", "FJ2822", "FJ2823", "FJ2824")],
                  inner=[V4 + e + ".obj" for g in ("portal_vein_hepatic", "hepatic_veins", "hepatic_artery", "intrahepatic_bile_ducts")
                         for e in G[g]["elements"]]),
}


def load(p):
    return load_stl(p) if p.endswith(".stl") else load_obj(p)


def main():
    t0 = time.time()
    buf = []
    pos = 0
    out = {}
    for name, o in ORG.items():
        skin = [load(p) for p in o["skin"]]
        inner = [load(p) for p in o["inner"]]
        A = np.vstack([v for v, f in skin])
        lo, hi = A.min(0), A.max(0)
        zs = np.arange(hi[2] - DZ / 2, lo[2], -DZ)
        secs = []
        vol = 0.0
        for z in zs:
            rec = dict(z=round(float(z), 2), s=[], i=[])
            area = 0.0
            for V, F in skin:
                for P, closed in slice_mesh(V, F, float(z)):
                    if closed and len(P) >= 3:
                        area += shoelace(P)
                    S = simplify_loop(P, 0.25, closed) if closed else P
                    if closed:
                        S = np.vstack([S, S[:1]])
                    I = np.round(S * Q).astype(np.int16).ravel()
                    buf.append(I); rec["s"].append([pos, len(S)]); pos += len(I)
            for V, F in inner:
                for P, closed in slice_mesh(V, F, float(z)):
                    if not closed or len(P) < 3 or abs(shoelace(P)) < 0.15:
                        continue
                    S = np.vstack([simplify_loop(P, 0.15), P[:1]])
                    I = np.round(S * Q).astype(np.int16).ravel()
                    buf.append(I); rec["i"].append([pos, len(S)]); pos += len(I)
            rec["a"] = round(area, 1)
            vol += area * DZ
            secs.append(rec)
        out[name] = dict(bmin=lo.tolist(), bmax=hi.tolist(), n=len(zs), vol_cm3=round(vol / 1000, 1), sec=secs)
        print(name, "bbox", lo.round(1), hi.round(1), "sections", len(zs), "vol cm3", round(vol / 1000, 1), "max area", max(s["a"] for s in secs), "t", round(time.time() - t0, 1), flush=True)
    data = np.concatenate(buf).astype("<i2")
    data.tofile(os.path.join(PUB, "trio.bin"))
    json.dump(dict(dz=DZ, q=Q, org=out), open(os.path.join(PUB, "trio.json"), "w"), separators=(",", ":"))
    print("points", pos // 2, "MB", round(pos * 2 / 1e6, 1))


main()
