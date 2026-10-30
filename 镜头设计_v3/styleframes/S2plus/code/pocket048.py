"""Still 9 (W4) geometry: 048 in our re-docked pose and the real pocket around it, in camera space. numpy only, so Blender and plain python share it.

python pocket048.py                 prints the framing, writes s2plus/data/pose048_2d.json (vector fallback for s09.jsx)
python pocket048.py preview X.png   flat numpy shading of the same geometry and camera, to judge framing without the GPU
python pocket048.py check X.png     after the Blender run: colours on palette, blue clear of the centre line and the plate

Pocket: the AlphaFold 1-302 model in rec_1-302.pdb (T6_molecules), a Gaussian surface over its heavy atoms, kept within SHELL of the ligand and cut flat at CUT in front of it.
The camera frame is a pure rotation, so 048 is not mirrored. The surface is ours and only shows where the walls are. The pose is our AutoDock Vina run (dock_048.sdf mode 2 through export_poses.py), never a measured structure.
"""
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
T6 = ROOT / "镜头设计_v2" / "tests" / "T6_molecules"
POSES, PDB = T6 / "poses.json", T6 / "rec_1-302.pdb"
OUT2D = ROOT / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data" / "pose048_2d.json"

VDW = dict(C=1.7, N=1.55, O=1.52, S=1.8)
ATOM_R = dict(C=0.38, N=0.36, O=0.36, H=0.20)    # ball radii, Å. render_poses.py sizes, a little heavier for a half-frame
STICK_R, H_STEP = 0.13, 0.15                     # bond radius; voxel size, Å (5 px at 1080p, smooth-shaded)
SHELL, CUT = 6.5, 0.8                            # keep the protein within SHELL of the ligand; flat cut CUT in front of its mid-plane, Å
CROP_SKIN = 0.3                                  # faces this close to the SHELL crop count as crop walls, Å
EDGE_ON, OPEN_RINGS, MIN_PIECE = 0.2, 4, 1500    # hide faces steeper than this z-normal, ribbons under 8 faces wide, pieces under this many faces
K_BLOB, SHRINK = 1.1, 0.92                       # Gaussian sharpness; VdW scale. Lower = smoother walls
ROLL = 0.0                                       # view roll, radians
LIGHT = np.array([-0.32, 0.42, 0.85]); LIGHT /= np.linalg.norm(LIGHT)   # toward the sun, camera space
AMBIENT, SUN = 0.14, 0.86                        # radiance over albedo: they add to 1, so nothing passes its palette colour

# screen box for the pocket, CSS px in the 1920x1080 frame: 96 off the centre line and every edge, and clear of the OUR RE-DOCKING plate at y 930
SAFE = dict(x0=1056, x1=1824, y0=96, y1=882)


def basis(w, roll=0.0):
    """Rows are camera x, y, z (z toward the camera)."""
    w = np.asarray(w, float) / np.linalg.norm(w)
    up = np.array([0, 0, 1.0]) if abs(w[2]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(up, w); u /= np.linalg.norm(u)
    v = np.cross(w, u)
    c, s = np.cos(roll), np.sin(roll)
    return np.array([c * u + s * v, -s * u + c * v, w])


def load(poses=POSES, pdb=PDB, roll=ROLL):
    """Ligand, contacts and receptor heavy atoms in camera space. Same view as render_poses.py: ligand plane face-on, then the same tilt."""
    pose = json.load(open(poses))["poses"]["048"]
    el = [a[0] for a in pose["atoms"]]
    xyz = np.array([a[1:] for a in pose["atoms"]], float)
    heavy = np.array([e != "H" for e in el])
    c = xyz[heavy].mean(0)
    _, _, vt = np.linalg.svd(xyz - xyz.mean(0))
    n = vt[2] * (1 if vt[2][2] >= 0 else -1)
    B = basis(n + np.array([0.15, -0.25, 0.35]), roll)
    cam = lambda p: (np.asarray(p, float) - c) @ B.T
    rec, rel = [], []
    for l in open(pdb):
        if l.startswith("ATOM"):
            rec.append([float(l[30:38]), float(l[38:46]), float(l[46:54])]); rel.append(l[76:78].strip())
    return dict(el=el, lig=cam(xyz), heavy=heavy, bonds=pose["bonds"], rec=cam(rec), rad=np.array([VDW[e] for e in rel]),
                contacts=[dict(partner=x["partner"], dist=x["dist"], lig=cam(x["lig"]), rec=cam(x["rec"])) for x in pose["contacts"]], vina=pose["vina"], mode=pose["mode"])


def cut_z(S):
    return float(S["lig"][S["heavy"], 2].mean() + CUT)


def field(S, h=H_STEP):
    """Implicit solid on a camera-aligned grid: > 0 inside, roughly Å. Returns f, the grid origin and the distance to the ligand."""
    L = S["lig"][S["heavy"]]
    lo, hi = L.min(0) - SHELL - 1.5, L.max(0) + SHELL + 1.5
    n = np.ceil((hi - lo) / h).astype(int) + 1
    ax = [(lo[i] + h * np.arange(n[i])).astype(np.float32) for i in range(3)]
    F = np.zeros(n, np.float32)
    for p, vr in zip(S["rec"], S["rad"]):
        r = vr * SHRINK
        rad = r * 2.6
        i0, i1 = np.maximum(np.floor((p - rad - lo) / h).astype(int), 0), np.minimum(np.floor((p + rad - lo) / h).astype(int) + 2, n)
        if (i1 <= i0).any():
            continue
        d2 = (ax[0][i0[0]:i1[0], None, None] - p[0]) ** 2 + (ax[1][None, i0[1]:i1[1], None] - p[1]) ** 2 + (ax[2][None, None, i0[2]:i1[2]] - p[2]) ** 2
        F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] += np.exp(-K_BLOB * (d2 / r ** 2 - 1))
    d2 = np.full(n, 1e9, np.float32)
    for p in L:
        d2 = np.minimum(d2, (ax[0][:, None, None] - p[0]) ** 2 + (ax[1][None, :, None] - p[1]) ** 2 + (ax[2][None, None, :] - p[2]) ** 2)
    d = np.sqrt(d2)
    return np.minimum(np.minimum((F - 1) / 1.3, cut_z(S) - ax[2][None, None, :]), SHELL - d), lo, d


def surface_nets(f, lo, h=H_STEP, relax=2):
    """Naive surface nets with outward quads: one vertex per sign-changing cell, a quad per sign-changing grid edge. Smoother than marching cubes for a smooth-shaded mesh."""
    s = f > 0
    corners = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)])
    m = np.zeros(np.array(f.shape) - 1, np.uint8)
    for c in corners:
        m += s[c[0]:f.shape[0] - 1 + c[0], c[1]:f.shape[1] - 1 + c[1], c[2]:f.shape[2] - 1 + c[2]]
    cells = np.argwhere((m > 0) & (m < 8))
    vid = -np.ones(m.shape, np.int32)
    vid[tuple(cells.T)] = np.arange(len(cells))
    fv = np.stack([f[tuple((cells + c).T)] for c in corners], 1)
    acc, cnt = np.zeros((len(cells), 3), np.float32), np.zeros(len(cells), np.float32)
    for a in range(8):
        for ax in range(3):
            if corners[a][ax] == 0:
                b = a + (1 << ax)
                fa, fb = fv[:, a], fv[:, b]
                hit = (fa > 0) != (fb > 0)
                t = np.where(hit, fa / np.where(hit, fa - fb, 1), 0)
                pos = np.broadcast_to(corners[a], acc.shape).astype(np.float32).copy()
                pos[:, ax] += t
                acc += pos * hit[:, None]; cnt += hit
    verts = lo + (cells + acc / cnt[:, None]) * h
    quads = []
    for ax in range(3):
        o = [(ax + 1) % 3, (ax + 2) % 3]
        lead = [slice(None)] * 3; next_ = [slice(None)] * 3
        lead[ax] = slice(0, -1); next_[ax] = slice(1, None)
        for sign, e in ((1, s[tuple(lead)] & ~s[tuple(next_)]), (-1, ~s[tuple(lead)] & s[tuple(next_)])):
            idx = np.argwhere(e)
            idx = idx[(idx[:, o[0]] > 0) & (idx[:, o[1]] > 0) & (idx[:, o[0]] < m.shape[o[0]]) & (idx[:, o[1]] < m.shape[o[1]]) & (idx[:, ax] < m.shape[ax])]
            q = []
            for da, db in ((1, 1), (0, 1), (0, 0), (1, 0)):
                c = idx.copy()
                c[:, o[0]] -= da; c[:, o[1]] -= db
                q.append(vid[tuple(c.T)])
            q = np.stack(q, 1)
            quads.append(q if sign > 0 else q[:, ::-1])
    quads = np.concatenate(quads)
    assert (quads >= 0).all(), "surface reaches the grid edge: raise the padding in field()"
    for _ in range(relax):      # light averaging takes the voxel grain off the curved walls; flat cut stays flat, its neighbours share its z
        acc = np.zeros_like(verts, dtype=np.float64); cnt = np.zeros(len(verts))
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
            np.add.at(acc, quads[:, a], verts[quads[:, b]]); np.add.at(cnt, quads[:, a], 1)
            np.add.at(acc, quads[:, b], verts[quads[:, a]]); np.add.at(cnt, quads[:, b], 1)
        verts = 0.5 * verts + 0.5 * acc / cnt[:, None]
    return verts, quads


def pieces(quads, on, n):
    """Face count of the connected piece each face belongs to, over the faces marked on."""
    label = np.arange(n)
    seen = quads[on]
    while True:
        new = label.copy()
        np.minimum.at(new, seen.ravel(), np.repeat(label[seen].min(1), 4))
        new = new[new]
        if (new == label).all():
            break
        label = new
    size = np.bincount(label[seen[:, 0]], minlength=n)
    return np.where(on, size[label[quads[:, 0]]], 0)


def hidden_faces(S, verts, quads, h=H_STEP):
    """True for the flat cut and the crop walls. render_048.py makes these holdout, so the black stage itself is the cut face and only real pocket surface shows.
    Walls seen edge-on, thin ribbons and loose flecks read as dirt on the black and go too. A side chain poking through the cut stays visible, or it would punch a black hole beside the ligand."""
    L = S["lig"][S["heavy"]]
    d = np.sqrt(((verts[:, None, :] - L[None, :, :]) ** 2).sum(2)).min(1)
    cap = (verts[quads, 2] >= cut_z(S) - 0.5 * h).all(1)
    cap &= pieces(quads, cap, len(verts)) >= MIN_PIECE
    e1, e2 = verts[quads[:, 2]] - verts[quads[:, 0]], verts[quads[:, 3]] - verts[quads[:, 1]]
    n = np.cross(e1, e2)
    edge_on = n[:, 2] < EDGE_ON * np.linalg.norm(n, axis=1)
    keep = ~(cap | edge_on | (d[quads] >= SHELL - CROP_SKIN).any(1))
    blocked = ~keep
    for _ in range(OPEN_RINGS):
        bad = np.zeros(len(verts), bool); bad[quads[~keep].ravel()] = True
        keep &= ~bad[quads].any(1)
    for _ in range(OPEN_RINGS):
        good = np.zeros(len(verts), bool); good[quads[keep].ravel()] = True
        keep = (keep | good[quads].any(1)) & ~blocked
    return pieces(quads, keep, len(verts)) < MIN_PIECE


def show_mask(quads, hidden, n, passes=3):
    """Per-vertex 0..1: share of visible faces around it, blurred. render_048.py thresholds this at 0.5 in the shader, so the blue edge is a smooth contour, not stair-stepped faces."""
    c = np.zeros(n); np.add.at(c, quads.ravel(), 1)
    v = np.zeros(n); np.add.at(v, quads.ravel(), np.repeat((~hidden).astype(float), 4))
    v /= np.maximum(c, 1)
    for _ in range(passes):
        a = np.zeros(n); np.add.at(a, quads.ravel(), np.repeat(v[quads].mean(1), 4))
        v = a / np.maximum(c, 1)
    return v


def fit(verts, quads, hidden):
    """Scale and centre that put the visible pocket inside SAFE. Returns px per Å and the camera x, y in Å (frame half is 960 CSS px wide, x from 960)."""
    seen = verts[np.unique(quads[~hidden])]
    lo, hi = seen[:, :2].min(0), seen[:, :2].max(0)
    ppa = float(min((SAFE["x1"] - SAFE["x0"]) / (hi[0] - lo[0]), (SAFE["y1"] - SAFE["y0"]) / (hi[1] - lo[1])))
    mid = (lo + hi) / 2
    sx, sy = (SAFE["x0"] + SAFE["x1"]) / 2, (SAFE["y0"] + SAFE["y1"]) / 2
    return ppa, float(mid[0] - (sx - 1440) / ppa), float(mid[1] + (sy - 540) / ppa)


def to_px(p, ppa, cx, cy):
    """Camera-space Å to CSS px in the full 1920x1080 frame."""
    return 1440 + (p[..., 0] - cx) * ppa, 540 - (p[..., 1] - cy) * ppa


def write_2d(S, ppa, cx, cy, out=OUT2D):
    """The same pose as plain coordinates, so s09.jsx can draw a vector stand-in if pose_048.png is not there yet."""
    L = S["lig"]
    x, y = to_px(L, ppa, cx, cy)
    rnd = lambda v: round(float(v), 1)
    d = dict(note="generated by pocket048.py. Vector stand-in only: real image is pose_048.png. OUR RE-DOCKING, AutoDock Vina, not a measured structure.",
             atoms=[[rnd(x[i]), rnd(y[i]), rnd(ATOM_R.get(S["el"][i], 0.36) * ppa)] for i in np.argsort(L[:, 2])],
             bonds=[[rnd(x[i]), rnd(y[i]), rnd(x[j]), rnd(y[j])] for i, j, _ in S["bonds"]],
             hbonds=[[rnd(v) for v in (*to_px(c["lig"], ppa, cx, cy), *to_px(c["rec"], ppa, cx, cy))] for c in S["contacts"] if c["rec"][2] < cut_z(S)])
    out.write_text(json.dumps(d, separators=(",", ":")) + "\n", encoding="utf8")


def preview(path, S, f, lo, d, verts, quads, hidden, ppa, cx, cy, W=960, H=1080, scale=1):
    """Orthographic depth-map shading of the implicit, no Cycles. Sun, ambient and palette as in render_048.py, without bounce light or soft shadows."""
    from PIL import Image
    h = H_STEP
    ins = f > 0
    has = ins.any(2)
    top = f.shape[2] - 1 - np.argmax(ins[:, :, ::-1], axis=2)
    depth = lo[2] + h * top
    gx, gy = np.gradient(np.where(has, depth, depth.min() - 4), h)
    depth = np.where(has, depth, -1e9)      # empty columns must not shadow anything
    nrm = np.sqrt(gx ** 2 + gy ** 2 + 1)
    lam = np.clip((-gx * LIGHT[0] - gy * LIGHT[1] + LIGHT[2]) / nrm, 0, 1)
    wpx, hpx = W * scale, H * scale
    px = (np.arange(wpx) + 0.5) / scale - 480
    py = (np.arange(hpx) + 0.5) / scale
    ax = np.clip(np.round((cx + px / ppa - lo[0]) / h).astype(int), 0, f.shape[0] - 1)
    ay = np.clip(np.round((cy + (540 - py) / ppa - lo[1]) / h).astype(int), 0, f.shape[1] - 1)
    sel = np.ix_(ax, ay)
    mask, dep, sh = has[sel].T, depth[sel].T, lam[sel].T
    seen = np.zeros((hpx, wpx), bool)                   # only what hidden_faces leaves visible
    vx, vy = to_px(verts[quads[~hidden]].mean(1), ppa, cx, cy)
    seen[np.clip((vy * scale).astype(int), 0, hpx - 1), np.clip(((vx - 960) * scale).astype(int), 0, wpx - 1)] = True
    for _ in range(int(h * ppa * scale * 0.6) + 1):
        seen = seen | np.roll(seen, 1, 0) | np.roll(seen, -1, 0) | np.roll(seen, 1, 1) | np.roll(seen, -1, 1)
    for t in np.arange(0.4, 10, 0.4):       # hard shadow, marched across the depth map
        xx = np.clip((np.arange(wpx) + LIGHT[0] / LIGHT[2] * t * ppa * scale).astype(int), 0, wpx - 1)
        yy = np.clip((np.arange(hpx) - LIGHT[1] / LIGHT[2] * t * ppa * scale).astype(int), 0, hpx - 1)
        sh = np.where(dep[np.ix_(yy, xx)] > dep + t + 0.25, 0, sh)
    img = np.zeros((hpx, wpx, 3)); zb = np.full((hpx, wpx), -1e9)
    blue, bone, cap = srgb2lin("1F3BFF"), srgb2lin("EDEBE4"), ~seen
    img[:] = srgb2lin("060606")
    img[mask & ~cap] = ((SUN * sh + AMBIENT)[..., None] * blue)[mask & ~cap]; zb[mask] = dep[mask]

    def disc(p, r, col):
        x0, y0 = (p[0] - cx) * ppa * scale + wpx / 2, -(p[1] - cy) * ppa * scale + hpx / 2
        rp = r * ppa * scale
        y1, x1 = max(0, int(y0 - rp)), max(0, int(x0 - rp))
        ys, xs = np.mgrid[y1:min(hpx, int(y0 + rp) + 2), x1:min(wpx, int(x0 + rp) + 2)]
        d2 = ((xs + 0.5 - x0) ** 2 + (ys + 0.5 - y0) ** 2) / rp ** 2
        nz = np.sqrt(np.clip(1 - d2, 0, 1)); zz = p[2] + r * nz
        v = (d2 < 1) & (zz > zb[ys, xs])
        lm = np.clip((xs + 0.5 - x0) / rp * LIGHT[0] - (ys + 0.5 - y0) / rp * LIGHT[1] + nz * LIGHT[2], 0, 1)
        img[ys[v], xs[v]] = (SUN * lm + AMBIENT)[v, None] * col; zb[ys[v], xs[v]] = zz[v]
    L = S["lig"]
    for i, j, _ in S["bonds"]:
        for t in np.linspace(0, 1, int(np.linalg.norm(L[j] - L[i]) * ppa * scale / 2) + 2):
            disc(L[i] + (L[j] - L[i]) * t, STICK_R, bone)
    for c in S["contacts"]:
        if c["rec"][2] < cut_z(S):
            for k in range(7):
                for t in np.linspace(k / 7, (k + 0.5) / 7, 6):
                    disc(c["lig"] + (c["rec"] - c["lig"]) * t, 0.05, bone)
    for e, p in zip(S["el"], L):
        disc(p, ATOM_R.get(e, 0.36), bone)
    a = np.clip(img, 0, 1)
    a = np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(path)


def srgb2lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def check(path):
    """pose_048.png must be 1920x2160 with alpha; no ink near the centre line or the plate, no hue outside blue and bone. Exits 1 on any failure."""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGBA"), float) / 255
    fails = []
    if im.shape[:2] != (2160, 1920): fails.append(f"size {im.shape[1]}x{im.shape[0]}, want 1920x2160: the half frame must not be upscaled")
    a = im[..., 3] > 0.5
    k = im.shape[1] / 960
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min() / k + 960, xs.max() / k + 960, ys.min() / k, ys.max() / k
    print("ink box in CSS px: x %.0f-%.0f, y %.0f-%.0f" % (x0, x1, y0, y1))
    slack = 6       # the soft mask moves the edge by a few px; this still keeps ink clear of the plate and 90 off the line
    if x0 < SAFE["x0"] - slack or y0 < SAFE["y0"] - slack or x1 > SAFE["x1"] + slack or y1 > SAFE["y1"] + slack: fails.append("ink leaves the safe box")
    r, g, b = (im[..., i][a] for i in range(3))
    cyan = ((g > 0.55 * b) & (r < 0.6 * g) & (b > 0.2)).mean()          # blue pushed over into cyan by overexposure
    warm = ((r > 1.25 * b) & (r > 0.2)).mean()                           # anything red or orange on the computed side
    print("cyan share %.5f, warm share %.5f, max rgb %.3f %.3f %.3f" % (cyan, warm, r.max(), g.max(), b.max()))
    if cyan > 0.001: fails.append("cyan drift: lower the sun in render_048.py")
    if warm > 0.001: fails.append("warm pixels on the computed side")
    print("FAIL: " + "; ".join(fails) if fails else "ok")
    sys.exit(1 if fails else 0)


def build():
    S = load()
    f, lo, d = field(S)
    verts, quads = surface_nets(f, lo)
    hidden = hidden_faces(S, verts, quads)
    ppa, cx, cy = fit(verts, quads, hidden)
    return S, f, lo, d, verts, quads, hidden, ppa, cx, cy


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:2] == ["check"]:
        check(sys.argv[2])
    S, f, lo, d, verts, quads, hidden, ppa, cx, cy = build()
    x, y = to_px(verts[np.unique(quads[~hidden])], ppa, cx, cy)
    print(f"{len(verts)} verts, {len(quads)} quads, {(~hidden).sum()} visible; {ppa:.2f} px/Å at 1080p; camera centre {cx:.2f}, {cy:.2f} Å")
    print(f"visible pocket in the frame: x {x.min():.0f}-{x.max():.0f}, y {y.min():.0f}-{y.max():.0f} (safe {SAFE})")
    L = S["lig"]
    lx, ly = to_px(L, ppa, cx, cy)
    print(f"ligand in the frame: x {lx.min():.0f}-{lx.max():.0f}, y {ly.min():.0f}-{ly.max():.0f}; Vina {S['vina']} (mode {S['mode']})")
    print("contacts:", [(c["partner"], c["dist"], "behind cut" if c["rec"][2] < cut_z(S) else "in front, dash dropped") for c in S["contacts"]])
    if sys.argv[1:2] == ["preview"]:
        preview(sys.argv[2], S, f, lo, d, verts, quads, hidden, ppa, cx, cy, scale=int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    else:
        write_2d(S, ppa, cx, cy)
        print("wrote", OUT2D)
