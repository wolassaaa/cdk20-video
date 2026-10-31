"""HKBU SCIE1007 coursework science video. Group E style scouts: shared helpers for the Blender and numpy frames.

Real CDK20 data only: the AlphaFold DB v6 surface mesh and PDB atoms. Nothing here invents a molecule.
"""
import os
from pathlib import Path

import numpy as np

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
OUT = ROOT / "styleframes/art/scouts/e"
WORK = OUT / "_work"
PDB = ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
SURFACE = ROOT / "styleframes/S2plus/_work/cdk20_surface.npz"
FONTS = r"C:/Windows/Fonts"
LABEL = "AlphaFold DB v6 \u00b7 predicted"
TITLE = "CDK20"


def load_ca():
    """C-alpha positions (Angstrom) and pLDDT (0..1), one per residue, from the real PDB."""
    xyz, b = [], []
    for ln in open(PDB, encoding="ascii", errors="ignore"):
        if ln.startswith("ATOM") and ln[12:16].strip() == "CA":
            xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            b.append(float(ln[60:66]) / 100)
    return np.array(xyz, np.float32), np.array(b, np.float32)


def load_atoms():
    xyz, b = [], []
    for ln in open(PDB, encoding="ascii", errors="ignore"):
        if ln.startswith("ATOM"):
            xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            b.append(float(ln[60:66]) / 100)
    return np.array(xyz, np.float32), np.array(b, np.float32)


def load_surface():
    D = np.load(SURFACE)
    return D["verts"].astype(np.float32), D["quads"].astype(np.int32), D["conf"].astype(np.float32)


def rot(ax, ay, az):
    """Rotation matrix from Euler angles in degrees."""
    x, y, z = np.radians([ax, ay, az])
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return (Rz @ Ry @ Rx).astype(np.float32)


def vertex_normals(v, q):
    a, b, c, d = (v[q[:, i]] for i in range(4))
    n = np.cross(c - a, d - b)
    out = np.zeros_like(v)
    for i in range(4):
        np.add.at(out, q[:, i], n)
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-8)


def smooth_field(v_field, q, it=4):
    """Laplacian smoothing of any per-vertex field over the quad mesh."""
    f = v_field.copy().astype(np.float32)
    nv = len(f)
    cnt = np.zeros(nv, np.float32)
    for k in range(4):
        np.add.at(cnt, q[:, k], 2)
    for _ in range(it):
        acc = np.zeros_like(f)
        for k in range(4):
            np.add.at(acc, q[:, k], f[q[:, (k + 1) % 4]] + f[q[:, (k + 3) % 4]])
        den = cnt if f.ndim == 1 else cnt[:, None]
        f = 0.5 * f + 0.5 * acc / np.maximum(den, 1)
    return f


def text_mask(txt, font, size, pad=20):
    """White-on-black glyph mask as float array."""
    from PIL import Image, ImageDraw, ImageFont

    fnt = ImageFont.truetype(os.path.join(FONTS, font), size)
    l, t, r, b = fnt.getbbox(txt)
    im = Image.new("L", (r - l + pad * 2, b - t + pad * 2), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, fill=255, font=fnt)
    return np.asarray(im, np.float32) / 255


def overlay(path, drawfn):
    """Open a rendered PNG, let drawfn(ImageDraw, Image) add type, save over it as flat RGB."""
    from PIL import Image, ImageDraw

    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    drawfn(ImageDraw.Draw(im), im)
    im.save(path)
