"""SCAN: 1,412 axial sections of the liver, one per person in the 2022 registry count.

Spacing is whatever divides the organ into exactly 1,412 equal sections:
(1183.14 - 1027.94) mm / 1412 = 0.1099 mm.

python prep_dense.py [N]  ->  public/liver1412.bin + public/liver1412.json
Binary layout (little-endian Int16, units 0.1 mm, x then y):
  per section: all closed fill loops, then all outline polylines. The JSON holds the offsets and counts.
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from slicer import ANAT, load_obj, slice_mesh, shoelace, simplify_loop

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public")
SEGS = ["FJ2816", "FJ2818", "FJ2819", "FJ2820", "FJ2821", "FJ2822", "FJ2823", "FJ2824"]   # FJ2409 duplicates FJ2822
RES = 0.4
Q = 10


def main(N=1412):
    t0 = time.time()
    segs = [load_obj(ANAT + "bp3d_v4_obj/" + k + ".obj") for k in SEGS]
    G = json.load(open(ANAT + "bp3d_v4_groups_stl/groups_report.json"))
    VV = [[load_obj(ANAT + "bp3d_v4_obj/" + e + ".obj") for e in G[g]["elements"]]
          for g in ("portal_vein_hepatic", "hepatic_veins", "hepatic_artery", "intrahepatic_bile_ducts")]
    allV = np.vstack([v for v, f in segs])
    lo, hi = allV.min(0), allV.max(0)
    zT, zB = float(hi[2]), float(lo[2])
    dz = (zT - zB) / N
    ox, oy = lo[0] - 3, lo[1] - 3
    Wm, Hm = int((hi[0] - lo[0] + 6) / RES) + 1, int((hi[1] - lo[1] + 6) / RES) + 1

    # first pass: loops and a union mask per section (packed, 0.4 mm/px)
    all_loops, areas, packed = [], [], []
    for i in range(N):
        z = zT - dz * (i + 0.5)
        loops = []
        for si, (V, F) in enumerate(segs):
            for P, closed in slice_mesh(V, F, z):
                if closed and len(P) >= 3:
                    loops.append((si, P))
        areas.append(sum(shoelace(P) for _, P in loops))
        mask = np.zeros((Hm, Wm), bool)
        for si in range(len(segs)):
            arr = None
            for sj, P in loops:
                if sj != si:
                    continue
                tmp = Image.new("1", (Wm, Hm), 0)
                ImageDraw.Draw(tmp).polygon([((x - ox) / RES, (y - oy) / RES) for x, y in P], fill=1)
                t = np.asarray(tmp)
                arr = t.copy() if arr is None else arr ^ t
            if arr is not None:
                mask |= arr
        all_loops.append(loops)
        packed.append(np.packbits(mask))
    packed = np.stack(packed)
    print("pass 1", round(time.time() - t0, 1), flush=True)
    W_Z = int(round(1.5 / dz))     # +-1.5 mm: closes the hairline voids between neighbouring segment meshes

    buf = []
    pos = 0
    index = []
    for i in range(N):
        z = zT - dz * (i + 0.5)
        loops = all_loops[i]
        area = areas[i]
        mask = np.unpackbits(packed[i], count=Hm * Wm).reshape(Hm, Wm).astype(bool)
        up = np.bitwise_or.reduce(packed[max(0, i - W_Z):i], axis=0) if i else np.zeros_like(packed[0])
        dn = np.bitwise_or.reduce(packed[i + 1:i + 1 + W_Z], axis=0) if i < N - 1 else np.zeros_like(packed[0])
        sandwich = np.unpackbits(up & dn, count=Hm * Wm).reshape(Hm, Wm).astype(bool)
        tissue = mask | sandwich
        fills, outs = [], []
        for si, P in loops:
            S = simplify_loop(P, 0.2)
            fills.append(S)
            Q2 = np.vstack([S, S[:1]])
            d = np.diff(Q2, axis=0)
            L = np.hypot(*d.T) + 1e-9
            m = (Q2[:-1] + Q2[1:]) / 2
            right = np.stack([d[:, 1], -d[:, 0]], 1) / L[:, None]
            flags = []
            for off in (0.8, 1.2):
                s = m + right * off
                ix = np.clip(((s[:, 0] - ox) / RES).astype(int), 0, Wm - 1)
                iy = np.clip(((s[:, 1] - oy) / RES).astype(int), 0, Hm - 1)
                flags.append(tissue[iy, ix])
            inside = flags[0] & flags[1]
            n = len(inside)
            if inside.all():
                continue
            if (~inside).all():
                outs.append(Q2)
                continue
            st = int(np.argmax(inside != np.roll(inside, 1)))
            run = [Q2[st]]
            cur = inside[st]
            for j in range(n):
                e = (st + j) % n
                if inside[e] != cur:
                    if not cur:
                        outs.append(np.array(run))
                    run = [Q2[e]]
                    cur = inside[e]
                run.append(Q2[e + 1])
            if not cur:
                outs.append(np.array(run))
        ves = []
        for items in VV:
            for V, F in items:
                for P, closed in slice_mesh(V, F, z):
                    if closed and len(P) >= 3 and abs(shoelace(P)) > 0.08:
                        ves.append(np.vstack([simplify_loop(P, 0.12), P[:1]]))
        rec = dict(z=round(z, 3), a=round(area, 1), f=[], o=[], v=[])
        for key, arrs in (("f", fills), ("o", outs), ("v", ves)):
            for A in arrs:
                I = np.round(A * Q).astype(np.int16).ravel()
                buf.append(I)
                rec[key].append([pos, len(A)])
                pos += len(I)
        index.append(rec)
        if i % 100 == 0:
            print(i, round(z, 2), round(area), len(fills), len(outs), round(time.time() - t0, 1), flush=True)
    os.makedirs(PUB, exist_ok=True)
    data = np.concatenate(buf).astype("<i2")
    data.tofile(os.path.join(PUB, f"liver{N}.bin"))
    json.dump(dict(N=N, dz=dz, zTop=zT, zBot=zB, q=Q, bmin=lo.tolist(), bmax=hi.tolist(), sec=index),
              open(os.path.join(PUB, f"liver{N}.json"), "w"), separators=(",", ":"))
    print("points", pos // 2, "bin MB", round(pos * 2 / 1e6, 2), "time", round(time.time() - t0, 1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1412)
