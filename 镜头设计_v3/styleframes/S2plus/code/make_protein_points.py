# Bakes CDK20 (AF-Q8IZL9-F1 v6) into flat stipple dots for stills 4, 5 (fallback) and 13. numpy and the AlphaFold files only; no GPU.
# Geometry is the real model: a ribbon surface built on the N/CA/C/O atoms, same recipe as S1 prot_geo.ribbon, sampled as points.
# Confidence is the real per-residue pLDDT: >= 70 stays on the ribbon, < 70 scatters by SIGMA * (70 - score) Angstrom.
# That scatter is a picture of low confidence, not a measured motion: pLDDT is not a distance error.
# Dots are baked in screen space for one camera, so a moving shot needs a re-bake per frame or a real 3D pass.
# Output:
#   styleframes/S2plus/public/protein_points.bin   Float32 x[n], Float32 y[n], Uint16 residue[n]; design px, 1920x1080
#   src/v3/s2plus/data/protein_points.json         n, counts, camera, ghost outline path, bboxes
#   styleframes/S2plus/code/cdk20_backbone_view.json   prot_geo schema in the camera frame, read by bl_ribbon302.py
import json, sys
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
V3 = Path(__file__).resolve().parents[3]
AF = V3 / "assets" / "alphafold"
PUB = V3 / "styleframes" / "S2plus" / "public"
DATA = V3.parent / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data"
CODE = Path(__file__).resolve().parent

N_RES, KEEP_TO = 346, 302          # R23 kept Met1-Ile302
CUTOFF = 70.0                      # same split as BAR_MODES.splat in kit.jsx
SOFT = 0.02                        # Angstrom of scatter per pLDDT point below 90, for residues above CUTOFF
SIGMA = 0.075                      # Angstrom of scatter per pLDDT point below CUTOFF
VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
CAM = 260.0                        # camera distance, Angstrom: nearly flat, a little depth
BOX = dict(top=130.0, bottom=800.0, right=1760.0, width=1010.0)   # frame area for the chain. Scatter may pass it, up to the 96 px margin and the barcode
BAR_TOP = 900.0                    # top of the barcode in still 4
DENSITY = 0.006                    # square Angstrom of ribbon surface per sample
DOTS_PER_RES = 100                 # loose dots per low-confidence residue, before spacing
HALO = 3                           # black edge beside nearer ribbons, in 3 px depth-buffer cells
R_TIGHT, R_LOOSE = 1.25, 3.4       # smallest gap between dots, design px
M = 96.0                           # frame margin
SEED = 20261031

# ---------- read the model ----------
atoms = {}
for l in (AF / "AF-Q8IZL9-F1-model_v6.pdb").read_text(encoding="utf8").splitlines():
    if l.startswith("ATOM") and l[12:16].strip() in ("N", "CA", "C", "O"):
        r = atoms.setdefault(int(l[22:26]), dict(aa=l[17:20], plddt=float(l[60:66])))
        r[l[12:16].strip()] = [float(l[30:38]), float(l[38:46]), float(l[46:54])]
assert sorted(atoms) == list(range(1, N_RES + 1))
conf = json.loads((AF / "AF-Q8IZL9-F1-confidence_v6.json").read_text(encoding="utf8"))["confidenceScore"]
PL = np.array([atoms[i + 1]["plddt"] for i in range(N_RES)])
assert np.allclose(PL, conf), "PDB B-factors disagree with the confidence JSON"

ss = ["C"] * N_RES                  # secondary structure from the CIF, as S1 prep_protein.py reads it
for ln in (AF / "AF-Q8IZL9-F1-model_v6.cif").read_text(encoding="utf8").splitlines():
    p = ln.split()
    if len(p) > 10 and p[0] == "A" and p[6].startswith(("STRN", "HELX")):
        code = "E" if p[6] == "STRN" else "H" if p[6].startswith("HELX_RH_AL") else None
        if code: ss[int(p[2]) - 1: int(p[9])] = [code] * (int(p[9]) - int(p[2]) + 1)

xyz = lambda k: np.array([atoms[i + 1][k] for i in range(N_RES)], float)
CA, CC, OO = xyz("CA"), xyz("C"), xyz("O")
cen = CA[:KEEP_TO].mean(0)
CA, CC, OO = CA - cen, CC - cen, OO - cen


# ---------- camera: x right, y up, z towards the lens ----------
# Best of 6000 random rotations for a tail clear of the fold, lower right, over its own bars at the end of the barcode. Orthonormalised after rounding.
u, _, vt = np.linalg.svd(np.array(VIEW))
R = u @ vt
assert abs(np.linalg.det(R) - 1) < 1e-9
CAv, CCv, OOv = CA @ R.T, CC @ R.T, OO @ R.T
nrm = lambda v: v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


# ---------- ribbon samples: port of prot_geo.ribbon, widths from its plddt look ----------
def ribbon(helix_w=1.9, sheet_w=1.7, thick=0.42, coil=0.42, arrow=1.7):
    P = CAv.copy()
    for i in range(1, N_RES - 1):
        if ss[i - 1] == ss[i] == ss[i + 1] == "E": P[i] = 0.25 * CAv[i - 1] + 0.5 * CAv[i] + 0.25 * CAv[i + 1]
    T = np.gradient(P, axis=0); T = nrm(T)
    D = OOv - CCv; D = nrm(D - T * (D * T).sum(1, keepdims=True))
    for i in range(1, N_RES):
        if D[i] @ D[i - 1] < 0: D[i] = -D[i]
    for _ in range(2):
        D = np.array([nrm(D[max(0, i - 1)] + 2 * D[i] + D[min(N_RES - 1, i + 1)]) if ss[i] != "E" else D[i] for i in range(N_RES)])
    size = lambda s: (helix_w, thick) if s == "H" else (sheet_w, thick) if s == "E" else (coil, coil)
    rng = np.random.default_rng(SEED)
    out_p, out_n, out_r = [], [], []
    for i in range(N_RES - 1):
        a, b, c, d = P[max(0, i - 1)], P[i], P[i + 1], P[min(N_RES - 1, i + 2)]
        (w0, t0), (w1, t1) = size(ss[i]), size(ss[i + 1])
        arrowhead = ss[i] == "E" and ss[i + 1] != "E"
        n = int(np.linalg.norm(c - b) * 1.1 * (4 * max(w0, w1, sheet_w * arrow if arrowhead else 0) + 2) / DENSITY)
        u, th = rng.random(n), rng.random(n) * 2 * np.pi                # every sample is independent, so the dots fall in no rows
        t = u[:, None]
        C = 0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3)
        tg = nrm(0.5 * ((c - a) + 2 * (2 * a - 5 * b + 4 * c - d) * t + 3 * (3 * b - a - 3 * c + d) * t ** 2))
        Sd = nrm(D[i] * (1 - t) + D[i + 1] * t); Sd = nrm(Sd - tg * (Sd * tg).sum(1, keepdims=True))
        Nm = np.cross(tg, Sd)
        sm = u * u * (3 - 2 * u)
        if arrowhead: w, h = sheet_w * arrow * (1 - u) + coil * u, thick * (1 - u) + coil * u
        elif ss[i] == ss[i + 1] == "E": w, h = np.full(n, w0), np.full(n, t0)
        else: w, h = w0 + (w1 - w0) * sm, t0 + (t1 - t0) * sm
        e = np.where(w > h * 1.5, 0.45, 1.0)                            # superellipse, flat ribbon faces
        cx, sx = np.cos(th), np.sin(th)
        x, y = np.sign(cx) * np.abs(cx) ** e * w, np.sign(sx) * np.abs(sx) ** e * h
        nx, ny = np.sign(cx) * np.abs(cx) ** (2 - e) / np.maximum(w, 1e-3), np.sign(sx) * np.abs(sx) ** (2 - e) / np.maximum(h, 1e-3)
        out_p.append(C + Sd * x[:, None] + Nm * y[:, None])
        out_n.append(nrm(Sd * nx[:, None] + Nm * ny[:, None]))
        out_r.append(np.where(u < 0.5, i + 1, i + 2).astype(np.uint16))  # each sample belongs to the nearer residue
    return np.concatenate(out_p), np.concatenate(out_n), np.concatenate(out_r)


S, NV, RS = ribbon()
print(f"ribbon samples: {len(S):,}")


# ---------- fit to the frame ----------
def fit():
    k = CAM / (CAM - S[:, 2])
    x, y = S[:, 0] * k, S[:, 1] * k
    sc = min((BOX["bottom"] - BOX["top"]) / (y.max() - y.min()), BOX["width"] / (x.max() - x.min()))
    return sc, BOX["right"] - sc * x.max(), BOX["top"] + sc * y.max()


SC, OX, OY = fit()
project = lambda p: (OX + SC * p[:, 0] * (CAM / (CAM - p[:, 2])), OY - SC * p[:, 1] * (CAM / (CAM - p[:, 2])))
PX, PY = project(S)


# ---------- depth buffer from the samples, so the far side of the chain drops out ----------
def zbuffer(x, y, z, cell=3):
    bw, bh = 1920 // cell, 1080 // cell
    zb = np.full((bh, bw), -1e9)
    ix, iy = np.clip((x / cell).astype(int), 0, bw - 1), np.clip((y / cell).astype(int), 0, bh - 1)
    np.maximum.at(zb, (iy, ix), z)
    z2 = zb.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)): z2 = np.maximum(z2, np.roll(np.roll(zb, dy, 0), dx, 1))
    return z2, ix, iy


ZB, IX, IY = zbuffer(PX, PY, S[:, 2])
front = (S[:, 2] > ZB[IY, IX] - 1.0) & (NV[:, 2] > -0.1)


# ---------- stipple: tone becomes spacing, every dot the same flat colour ----------
def poisson(x, y, gap, order):
    """Greedy variable-radius dart throwing on a grid. Even spacing, no clumps, so density reads as tone."""
    cell, cells, kept = gap.min(), {}, []
    for i in order:
        cx, cy, g = int(x[i] / cell), int(y[i] / cell), gap[i]
        reach, ok = int(np.ceil(g / cell)), True
        for b in range(cy - reach, cy + reach + 1):
            for a in range(cx - reach, cx + reach + 1):
                for j in cells.get((a, b), ()):
                    if (x[j] - x[i]) ** 2 + (y[j] - y[i]) ** 2 < g * g: ok = False; break
                if not ok: break
            if not ok: break
        if ok: cells.setdefault((cx, cy), []).append(i); kept.append(i)
    return np.array(kept)


rng = np.random.default_rng(SEED + 1)
L = np.array([-0.5, 0.6, 0.62]); L /= np.linalg.norm(L)
lam = np.clip(NV @ L, 0, 1)
far = np.clip((S[:, 2] + 28) / 56, 0, 1)
tone = (0.12 + 0.88 * lam ** 1.3) * (0.3 + 0.7 * far)
# a surface passing behind a nearer one drops out beside it: the black edge that keeps overlapping ribbons apart
near = ZB.copy()
for _ in range(HALO):
    near = np.maximum.reduce([near, np.roll(near, 1, 0), np.roll(near, -1, 0), np.roll(near, 1, 1), np.roll(near, -1, 1)])
tone[near[IY, IX] - S[:, 2] > 3.0] *= 0.06

tight = np.where(front & (PL[RS - 1] >= CUTOFF))[0]
fuzz = rng.normal(size=(len(tight), 3)) * (SOFT * np.clip(90 - PL[RS[tight] - 1], 0, None))[:, None]   # sharpness keeps falling from 90 to 70
fx, fy = project(S[tight] + fuzz)
gap = R_TIGHT / np.sqrt(np.clip(tone[tight] * 2.0, 0.05, 1))
pick = poisson(fx, fy, gap, rng.permutation(len(tight)))
tx, ty, tr = fx[pick], fy[pick], RS[tight][pick]


# ---------- below the cutoff the dots leave the ribbon ----------
def loose():
    idx = np.where(PL[RS - 1] < CUTOFF)[0]
    sig = SIGMA * (CUTOFF - PL[RS[idx] - 1])
    p = S[idx] + rng.normal(size=(len(idx), 3)) * sig[:, None]
    x, y = project(p)
    ix, iy = np.clip((x / 3).astype(int), 0, ZB.shape[1] - 1), np.clip((y / 3).astype(int), 0, ZB.shape[0] - 1)
    on = (p[:, 2] > ZB[iy, ix] - 1.5) & (x > M) & (x < 1920 - M) & (y > M) & (y < BAR_TOP - 36)   # behind the fold, or past the margin: gone
    idx, x, y = idx[on], x[on], y[on]
    per = DOTS_PER_RES / np.maximum(np.bincount(RS[idx], minlength=N_RES + 2)[RS[idx]], 1)   # same dots per residue, so more scatter means thinner
    q = rng.random(len(idx)) < per
    idx, x, y = idx[q], x[q], y[q]
    pick = poisson(x, y, np.full(len(x), R_LOOSE), rng.permutation(len(x)))
    return x[pick], y[pick], RS[idx][pick]


lx, ly, lr = loose()
xs, ys, rs = np.concatenate([tx, lx]).astype(np.float32), np.concatenate([ty, ly]).astype(np.float32), np.concatenate([tr, lr]).astype(np.uint16)


# ---------- ghost for still 13: the model's own outline, thickened evenly, tail included. It is no measurement ----------
def blur(f, k):
    """Box blur, same size, by summed-area table."""
    w = 2 * k + 1
    ii = np.pad(np.pad(f, k).astype(float), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    return (ii[w:, w:] - ii[:-w, w:] - ii[w:, :-w] + ii[:-w, :-w]) / w ** 2


def outline(reach=3.4, cell=4):
    """Boundary of every ribbon sample dilated by reach Angstrom. No offset and no body/tail split, so it implies no result."""
    bw, bh = 1920 // cell, 1080 // cell
    m = np.zeros((bh, bw))
    m[np.clip((PY / cell).astype(int), 0, bh - 1), np.clip((PX / cell).astype(int), 0, bw - 1)] = 1
    m = blur(m, int(reach * SC / cell)) > 0
    for _ in range(3): m = blur(m, 4) > 0.5                        # round off the square dilation
    # Moore boundary trace from the first set cell, which is on the outer edge
    y0, x0 = np.argwhere(m)[0]
    ring = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
    path, cx, cy, back = [(x0, y0)], x0, y0, 6
    for _ in range(200000):
        for s in range(8):
            d = (back + s) % 8
            nx, ny = cx + ring[d][0], cy + ring[d][1]
            if 0 <= nx < m.shape[1] and 0 <= ny < m.shape[0] and m[ny, nx]:
                cx, cy, back = nx, ny, (d + 5) % 8
                break
        if (cx, cy) == (x0, y0): break
        path.append((cx, cy))
    p = np.array(path, float) * cell + cell / 2
    w = 11                                                         # smooth the pixel staircase, then every 4th point
    for _ in range(2):
        p = np.stack([np.convolve(np.r_[p[-w:, i], p[:, i], p[:w, i]], np.ones(w) / w, "same")[w:-w] for i in (0, 1)], 1)
    p = p[::4]
    return "M" + "L".join(f"{a:.1f} {b:.1f}" for a, b in p) + "Z", len(p)


GHOST, ghost_n = outline()


# ---------- write and check ----------
PUB.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
with open(PUB / "protein_points.bin", "wb") as f:
    f.write(xs.tobytes()); f.write(ys.tobytes()); f.write(rs.tobytes())
hidden = sorted(set(range(1, N_RES + 1)) - set(np.unique(rs).tolist()))
counts = dict(n=len(xs), tight=len(tx), loose=len(lx))
bx = lambda a, b: [round(float(v), 1) for v in (a.min(), b.min(), a.max(), b.max())]
body = RS <= KEEP_TO
meta = dict(source="AlphaFold DB AF-Q8IZL9-F1 model v6, CC BY 4.0, predicted", file="protein_points.bin", **counts,
            cutoff=CUTOFF, sigma_per_point=SIGMA, px_per_angstrom=round(float(SC), 3), origin=[round(float(OX), 2), round(float(OY), 2)], cam_angstrom=CAM,
            chain_bbox=bx(PX, PY), body_bbox=bx(PX[body], PY[body]), dot_bbox=bx(xs, ys), ghost=GHOST)
(DATA / "protein_points.json").write_text(json.dumps(meta, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf8")
view = [dict(i=i + 1, aa=atoms[i + 1]["aa"], plddt=float(PL[i]), ss=ss[i], ca=CAv[i].round(3).tolist(), c=CCv[i].round(3).tolist(), o=OOv[i].round(3).tolist()) for i in range(N_RES)]
b = meta["body_bbox"]
frame = dict(cam=CAM, body_centre=[round(((b[0] + b[2]) / 2 - float(OX)) / float(SC), 3), round((float(OY) - (b[1] + b[3]) / 2) / float(SC), 3)])   # Angstrom, camera frame
(CODE / "cdk20_backbone_view.json").write_text(json.dumps(dict(source=meta["source"] + "; camera frame of make_protein_points.py", frame=frame, res=view), separators=(",", ":")), encoding="utf8")

print(f"dots {counts['n']:,}: tight {counts['tight']:,}, loose {counts['loose']:,}; {SC:.2f} px/A; origin {OX:.1f}, {OY:.1f}")
print(f"chain bbox {meta['chain_bbox']}, body bbox {meta['body_bbox']}, dot bbox {meta['dot_bbox']}, ghost points {ghost_n}")
print(f"binary {(PUB / 'protein_points.bin').stat().st_size / 1024:.0f} KB; {len(hidden)} residues sit behind the fold in this view and draw no dot")
checks = (("binary size", (PUB / "protein_points.bin").stat().st_size == 10 * len(xs)),
          ("dots inside the side and top margins", xs.min() > M and xs.max() < 1920 - M and ys.min() > M),
          ("dots clear of the barcode", ys.max() < BAR_TOP - 20),
          ("tight dots all >= cutoff", (PL[tr - 1] >= CUTOFF).all()), ("loose dots all < cutoff", (PL[lr - 1] < CUTOFF).all()))
for name, ok in checks: print(("ok  " if ok else "FAIL"), name)
sys.exit(0 if all(ok for _, ok in checks) else 1)
