"""HKBU SCIE1007 coursework science video. falsecolor art direction: turns the public BodyParts3D liver mesh into a volume, for the T1 still.

python liver_field.py   writes ../_work/liver_field.npz

The liver and its vessels are voxelised from the real mesh, then every voxel gets its exact distance to the nearest vessel, in mm.
This is a picture made from a public anatomy model, not patient data. The still says so on screen.
"""
import json
import os
import struct
import time

import numpy as np

from fc_common import V3, WORK

STL = os.path.join(V3, "assets", "anatomy", "bp3d_v4_groups_stl")
H = 0.5        # voxel size, mm
PAD = 8.0


def read_stl(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    if 84 + 50 * n == len(b):
        a = np.frombuffer(b, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), offset=84, count=n)
        return a["v"].reshape(-1, 3, 3).astype(np.float64)
    vals = [list(map(float, ln.split()[1:4])) for ln in b.decode("ascii", "ignore").splitlines() if ln.strip().startswith("vertex")]
    return np.array(vals).reshape(-1, 3, 3)


def voxelise(tri, lo, shape):
    """Signed crossing count along +z per column: a mesh made of closed pieces fills correctly even where pieces touch."""
    g = (tri - lo) / H
    D = np.zeros(shape, np.int16)
    a, b, c = g[:, 0], g[:, 1], g[:, 2]
    nz = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    x0 = np.ceil(g[:, :, 0].min(1)).astype(int)
    x1 = np.floor(g[:, :, 0].max(1)).astype(int)
    y0 = np.ceil(g[:, :, 1].min(1)).astype(int)
    y1 = np.floor(g[:, :, 1].max(1)).astype(int)
    for t in np.nonzero((x1 >= x0) & (y1 >= y0) & (np.abs(nz) > 1e-12))[0]:
        xs, ys = np.meshgrid(np.arange(x0[t], x1[t] + 1), np.arange(y0[t], y1[t] + 1), indexing="ij")
        ax, ay, az = a[t]
        bx, by, bz = b[t]
        cx, cy, cz = c[t]
        d = nz[t]
        w1 = ((xs - ax) * (cy - ay) - (ys - ay) * (cx - ax)) / d
        w2 = ((bx - ax) * (ys - ay) - (by - ay) * (xs - ax)) / d
        ok = (w1 >= 0) & (w2 >= 0) & (w1 + w2 <= 1)
        if not ok.any():
            continue
        z = az + w1[ok] * (bz - az) + w2[ok] * (cz - az)
        iz = np.clip(np.ceil(z).astype(int), 0, shape[2] - 1)
        np.add.at(D, (xs[ok], ys[ok], iz), -1 if d > 0 else 1)
    return np.cumsum(D, axis=2) != 0


def morph(m, r, grow):
    """Box dilate or erode by r voxels, one axis at a time."""
    op = np.logical_or if grow else np.logical_and
    for ax in range(3):
        src = m
        out = src.copy()
        for k in range(1, r + 1):
            sl_a = [slice(None)] * 3
            sl_b = [slice(None)] * 3
            sl_a[ax], sl_b[ax] = slice(k, None), slice(None, -k)
            out[tuple(sl_a)] = op(out[tuple(sl_a)], src[tuple(sl_b)])
            out[tuple(sl_b)] = op(out[tuple(sl_b)], src[tuple(sl_a)])
        m = out
    return m


def edt(mask, radius_vox):
    """Exact squared distance transform, one axis at a time, out to radius_vox. Numpy only."""
    big = float(radius_vox ** 2 * 3 + 1)
    d = np.where(mask, 0.0, big).astype(np.float32)
    for ax in range(3):
        src = d.copy()
        for k in range(1, radius_vox + 1):
            c = float(k * k)
            sl_a = [slice(None)] * 3
            sl_b = [slice(None)] * 3
            sl_a[ax], sl_b[ax] = slice(k, None), slice(None, -k)
            np.minimum(d[tuple(sl_a)], src[tuple(sl_b)] + c, out=d[tuple(sl_a)])
            np.minimum(d[tuple(sl_b)], src[tuple(sl_a)] + c, out=d[tuple(sl_b)])
    return d


if __name__ == "__main__":
    t0 = time.time()
    liver = read_stl(os.path.join(STL, "liver_parenchyma_segments.stl"))
    parts = {k: read_stl(os.path.join(STL, k + ".stl")) for k in ("portal_vein_hepatic", "hepatic_veins", "hepatic_artery", "intrahepatic_bile_ducts")}
    lo = liver.reshape(-1, 3).min(0) - PAD
    hi = liver.reshape(-1, 3).max(0) + PAD
    shape = tuple(np.ceil((hi - lo) / H).astype(int) + 1)
    print("liver tris", len(liver), "bbox", lo.round(1), hi.round(1), "grid", shape, flush=True)
    inside = voxelise(liver, lo, shape)
    inside = morph(morph(inside, 3, True), 3, False)      # closes the seams between the liver's segments
    inside = morph(morph(inside, 2, False), 2, True)     # drops one-voxel column streaks from face-on triangles
    print("liver voxels", inside.sum(), "volume cm3", round(inside.sum() * H ** 3 / 1000), f"{time.time() - t0:.0f}s", flush=True)
    vs = np.zeros(shape, bool)
    blood = np.zeros(shape, bool)
    for k, tri in parts.items():
        m = voxelise(tri[np.all((tri > lo) & (tri < hi), axis=(1, 2))], lo, shape)
        # column fill can streak if a mesh is cut by the box: keep only what the mesh actually bounds, at most 40 mm deep
        print(k, "tris", len(tri), "voxels", m.sum(), flush=True)
        vs |= m
        if k != "intrahepatic_bile_ducts":
            blood |= m
    d2 = edt(blood, int(45 / H))
    dist = np.sqrt(d2) * H
    print("edt done", f"{time.time() - t0:.0f}s", "dist in liver: p50 %.1f p95 %.1f max %.1f mm" % tuple(np.percentile(dist[inside], [50, 95, 100])), flush=True)
    np.savez_compressed(os.path.join(WORK, "liver_field.npz"), inside=inside, blood=blood, dist=dist.astype(np.float32), lo=lo, h=H)
    print("saved", f"{time.time() - t0:.0f}s")
