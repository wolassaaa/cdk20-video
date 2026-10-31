"""HKBU SCIE1007 coursework science video. Lantern motion film: camera path and renderer core.
view2 is kit.view with early culling, a near cut and back-face removal, so the camera can move from the T4 view of the real surface down into the pocket of the T5 frame without leaving the mesh.
The camera at the end of the path is the one the pocket layers were rendered with, so 048's pixels drop into place unchanged."""
import json
import sys

from lk import *

sys.path.insert(0, str(kit.ROOT / "styleframes/S2plus/code"))
import pocket048 as pk  # noqa: E402

S = kit.surface()
VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
u_, _, vt_ = np.linalg.svd(np.array(VIEW))
Q = u_ @ vt_


def af_ca_mean():
    xyz, name, res = [], [], []
    for ln in open(kit.ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"):
        if ln.startswith("ATOM"):
            xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            name.append(ln[12:16].strip())
            res.append(int(ln[22:26]))
    xyz, name, res = np.array(xyz), np.array(name), np.array(res)
    return xyz[(name == "CA") & (res <= 302)].mean(0)


def t5_camera():
    """R, translation d (Angstrom, camera space) and the clip plane of the pocket render, in the mesh frame."""
    pose = json.load(open(pk.POSES))["poses"]["048"]
    xyz = np.array([a[1:] for a in pose["atoms"]], float)
    heavy = np.array([a[0] != "H" for a in pose["atoms"]])
    c = xyz[heavy].mean(0)
    _, _, vt = np.linalg.svd(xyz - xyz.mean(0))
    n = vt[2] * (1 if vt[2][2] >= 0 else -1)
    B = pk.basis(n + np.array([0.15, -0.25, 0.35]), pk.ROLL)
    R = B @ Q.T
    d = B @ Q.T @ S["cen"].astype(float) + B @ (af_ca_mean() - c)
    lig = (xyz - c) @ B.T
    return R.astype(np.float64), d, lig, heavy


def fit_screen(lig):
    """Scale and offset of the 2D ligand layer against the real atoms, from their bounding boxes in the T5 frame."""
    a = np.asarray(Image.open(kit.ROOT / "styleframes/S2plus/public/pose_048_lig.png"))[..., 3]
    sx = np.where(a.max(0) > 30)[0][[0, -1]] * 0.25 + (W - 960 + 20)
    sy = np.where(a.max(1) > 30)[0][[0, -1]] * 0.25
    x0, x1 = lig[:, 0].min(), lig[:, 0].max()
    y0, y1 = lig[:, 1].min(), lig[:, 1].max()
    s = 0.5 * ((sx[1] - sx[0]) / (x1 - x0 + 0.76) + (sy[1] - sy[0]) / (y1 - y0 + 0.76))
    ax = 0.5 * (sx[0] + sx[1]) - s * 0.5 * (x0 + x1)
    ay = 0.5 * (sy[0] + sy[1]) + s * 0.5 * (y0 + y1)
    return float(s), float(ax), float(ay)


def slerp(R0, R1, t):
    """Rotation between two camera frames, the short way."""
    Rd = R1 @ R0.T
    ang = np.arccos(np.clip((np.trace(Rd) - 1) / 2, -1, 1))
    if ang < 1e-5:
        return R0
    ax = np.array([Rd[2, 1] - Rd[1, 2], Rd[0, 2] - Rd[2, 0], Rd[1, 0] - Rd[0, 1]]) / (2 * np.sin(ang))
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    a = ang * t
    return (np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K) @ R0


SP = 0.25  # mesh spacing in Angstrom


def view2(R, scale, cx, cy, zcut=None, cull_back=False, extra=None, w=W, h=H, ss=0.5, L=(0.60, 0.58, 0.55)):
    """Passes of the real surface. zcut removes everything nearer than it. cull_back drops faces turned away, so the hollow inside of the mesh stays black."""
    v, n = S["v"] @ R.T.astype(np.float32), S["n"] @ R.T.astype(np.float32)
    px, py = v[:, 0] * scale + cx, -v[:, 1] * scale + cy
    keep = (px > -40) & (px < w + 40) & (py > -40) & (py < h + 40)
    if zcut is not None:
        keep &= v[:, 2] < zcut
    if cull_back:
        keep &= n[:, 2] > 0.02
    if extra is not None:
        keep &= extra
    v, n, px, py, cf = v[keep], n[keep], px[keep] * ss, py[keep] * ss, S["c"][keep]
    W2, H2 = int(w * ss), int(h * ss)
    fp = max(1, int(np.ceil(SP * scale * ss * 0.8)))
    off = [(i, j) for i in range(-fp, fp + 1) for j in range(-fp, fp + 1) if i * i + j * j <= fp * fp + 1]
    ix = np.concatenate([px.astype(np.int32) + i for i, j in off])
    iy = np.concatenate([py.astype(np.int32) + j for i, j in off])
    id0 = np.tile(np.arange(len(px)), len(off))
    ok = (ix >= 0) & (ix < W2) & (iy >= 0) & (iy < H2)
    ix, iy, id0 = ix[ok], iy[ok], id0[ok]
    o = np.argsort(v[id0, 2], kind="stable")
    buf = -np.ones((H2, W2), np.int32)
    buf[iy[o], ix[o]] = id0[o]
    m = buf >= 0
    z = np.where(m, v[buf.clip(0), 2], 0).astype(np.float32)
    nn = np.where(m[..., None], n[buf.clip(0)], 0).astype(np.float32)
    c = np.where(m, cf[buf.clip(0)], 0).astype(np.float32)
    sig = max(1.2, fp * 0.7)
    wt = fft_blur(m.astype(np.float32), sig) + 1e-4
    sm = lambda a: fft_blur(a * m, sig) / wt
    mask_s = fft_blur(m.astype(np.float32), max(0.9, sig * 0.8))
    z, c = sm(z), sm(c)
    nn = np.stack([sm(nn[..., i]) for i in range(3)], -1)
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-5)
    up = lambda a: resize(a, w, h)
    mask = smooth(up(mask_s), 0.40, 0.60)
    z, c = up(z), up(c)
    nn = np.stack([up(nn[..., i]) for i in range(3)], -1)
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-5)
    Lv = np.array(L, np.float32) / np.linalg.norm(L)
    key = np.clip(nn @ Lv, 0, 1) * mask
    wm = fft_blur(mask, 2.5 * scale) + 1e-3
    ao = np.clip(1 - np.clip(fft_blur(z * mask, 2.5 * scale) / wm - z, 0, 8) / 6, 0, 1) * mask
    return dict(mask=mask, z=z * (mask > 0), normal=nn, key=key, ao=ao, conf=c)
