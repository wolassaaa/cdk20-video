"""HKBU SCIE1007 coursework science video. Group E style scouts: a distance field of the real CDK20 atoms for numpy ray marching.

Field units are Angstrom, the molecule is centred on its bounding box. Cached in _work so every frame reuses it.
"""
import numpy as np

from common import WORK, load_atoms, text_mask

H = 0.8      # voxel size
HALF = 52.0  # half width of the cube the grid covers


def build(k=0.95, r=2.7):
    p = WORK / "sdf_cdk20.npz"
    if p.exists():
        d = np.load(p)
        return d["g"], d["conf"], d["c"]
    WORK.mkdir(parents=True, exist_ok=True)
    xyz, b = load_atoms()
    c = (xyz.min(0) + xyz.max(0)) / 2
    xyz = xyz - c
    n = int(2 * HALF / H) + 1
    acc = np.zeros((n, n, n), np.float32)
    wsum = np.zeros((n, n, n), np.float32)
    cf = np.zeros((n, n, n), np.float32)
    ax = -HALF + H * np.arange(n, dtype=np.float32)
    W = int(11 / H)
    for a, bf in zip(xyz, b):
        i = np.round((a + HALF) / H).astype(int)
        lo, hi = np.maximum(i - W, 0), np.minimum(i + W + 1, n)
        X = (ax[lo[0]:hi[0]] - a[0])[:, None, None]
        Y = (ax[lo[1]:hi[1]] - a[1])[None, :, None]
        Z = (ax[lo[2]:hi[2]] - a[2])[None, None, :]
        e = np.exp(-k * (np.sqrt(X * X + Y * Y + Z * Z) - r))
        s = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        acc[s] += e
        cf[s] += e * bf
        wsum[s] += e
    g = -np.log(np.maximum(acc, 1e-5)) / k
    conf = cf / np.maximum(wsum, 1e-6)
    g = np.minimum(g, 9.0)
    # far field: chamfer sweeps, scaled to stay conservative
    far = np.where(g < 8.5, g, 1e3).astype(np.float32)
    for axis in range(3):
        far = np.moveaxis(far, axis, 0)
        for i in range(1, n):
            far[i] = np.minimum(far[i], far[i - 1] + H)
        for i in range(n - 2, -1, -1):
            far[i] = np.minimum(far[i], far[i + 1] + H)
        far = np.moveaxis(far, 0, axis)
    g = np.where(g < 8.5, g, np.maximum(g, far / 1.74))
    np.savez_compressed(p, g=g.astype(np.float32), conf=conf.astype(np.float32), c=c)
    return g, conf, c


def trilinear(g, p):
    """p N x 3 in Angstrom (clamped to the grid), returns N."""
    u = np.clip((p + HALF) / H, 0, g.shape[0] - 1.001)
    i = u.astype(np.int32)
    f = (u - i).astype(np.float32)
    x, y, z = i[:, 0], i[:, 1], i[:, 2]
    fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
    c00 = g[x, y, z] * (1 - fx) + g[x + 1, y, z] * fx
    c10 = g[x, y + 1, z] * (1 - fx) + g[x + 1, y + 1, z] * fx
    c01 = g[x, y, z + 1] * (1 - fx) + g[x + 1, y, z + 1] * fx
    c11 = g[x, y + 1, z + 1] * (1 - fx) + g[x + 1, y + 1, z + 1] * fx
    return (c00 * (1 - fy) + c10 * fy) * (1 - fz) + (c01 * (1 - fy) + c11 * fy) * fz


def text_sdf(txt, font, size=150, down=3):
    """2D signed distance (in mask pixels at full res) to glyphs, brute force on a coarse grid."""
    m = text_mask(txt, font, size, pad=size // 2)
    h, w = m.shape
    ys = np.arange(0, h, down)
    xs = np.arange(0, w, down)
    mc = m[ys][:, xs] > 0.5
    # boundary points
    e = mc ^ (np.roll(mc, 1, 0) & np.roll(mc, -1, 0) & np.roll(mc, 1, 1) & np.roll(mc, -1, 1) & mc)
    by, bx = np.nonzero(mc & e)
    yy, xx = np.mgrid[0:len(ys), 0:len(xs)].astype(np.float32)
    out = np.zeros(mc.shape, np.float32)
    for r0 in range(0, len(ys), 8):
        r1 = min(r0 + 8, len(ys))
        dy = yy[r0:r1, :, None] - by[None, None, :]
        dx = xx[r0:r1, :, None] - bx[None, None, :]
        out[r0:r1] = np.sqrt((dx * dx + dy * dy).min(-1))
    out = np.where(mc, -out, out) * down
    return out, down


def bilinear2(g, u, v):
    """Sample 2D array at float pixel coords (u=x, v=y)."""
    h, w = g.shape
    u = np.clip(u, 0, w - 1.001)
    v = np.clip(v, 0, h - 1.001)
    i, j = u.astype(np.int32), v.astype(np.int32)
    fu, fv = u - i, v - j
    return (g[j, i] * (1 - fu) + g[j, i + 1] * fu) * (1 - fv) + (g[j + 1, i] * (1 - fu) + g[j + 1, i + 1] * fu) * fv
