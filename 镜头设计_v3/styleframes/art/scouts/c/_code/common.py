"""HKBU SCIE1007 coursework science video. Shared helpers for the C group style scouts (game art, method only)."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
sys.path.insert(0, str(ROOT / "styleframes/art/_shared"))
from passes import load, save  # noqa: E402

OUT = ROOT / "styleframes/art/scouts/c"
PDB = ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
SURF = ROOT / "styleframes/S2plus/_work/cdk20_surface.npz"
SEQ = Path(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/sequence.json")
W, H = 1280, 720
F = r"C:/Windows/Fonts/"
FX = str(ROOT / "styleframes/S1/v2/_code/s110/fonts") + "/"
LABEL = "AlphaFold DB v6 · predicted"


def font(name, size):
    return ImageFont.truetype(name, size)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def gblur(a, s):
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gblur(a[..., i], s) for i in range(a.shape[2])], -1)
    h, w = a.shape
    pad = int(s * 3) + 1
    b = np.pad(a, pad, mode="edge")
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    r = np.fft.irfft2(np.fft.rfft2(b) * g, s=b.shape)
    return r[pad:pad + h, pad:pad + w].astype(np.float32)


def vnoise(w, h, cell, seed=0, oct=4, gain=0.5):
    """Smooth value noise, 0..1."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    c = float(cell)
    for _ in range(oct):
        gw, gh = max(2, int(w / c) + 3), max(2, int(h / c) + 3)
        g = rng.random((gh, gw), dtype=np.float32)
        im = Image.fromarray(g).resize((int(gw * c), int(gh * c)), Image.BICUBIC)
        a = np.asarray(im)[:h, :w]
        out += amp * a
        tot += amp
        amp *= gain
        c = max(1.0, c / 2)
    return out / tot


def warp(P, zoom=1.0, cx=None, cy=None, rot=0.0, flip=False, w=W, h=H, ox=None, oy=None):
    """Zoom and rotate the passes. (cx, cy) is the source point in the 1920x1080 frame placed at output (ox, oy)."""
    sh, sw = P["mask"].shape
    cx = sw / 2 if cx is None else cx
    cy = sh / 2 if cy is None else cy
    ox = w / 2 if ox is None else ox
    oy = h / 2 if oy is None else oy
    ca, sa = math.cos(rot), math.sin(rot)
    fx = -1.0 if flip else 1.0
    # output (x, y) -> source
    a, b = fx * ca / zoom, fx * sa / zoom
    d, e = -sa / zoom, ca / zoom
    c = cx - a * ox - b * oy
    f = cy - d * ox - e * oy
    co = (a, b, c, d, e, f)
    out = {}

    def tr(arr):
        return np.asarray(Image.fromarray(arr).transform((w, h), Image.AFFINE, co, resample=Image.BICUBIC))

    for k, v in P.items():
        if v.ndim == 2:
            out[k] = tr(v)
        else:
            out[k] = np.stack([tr(v[..., i]) for i in range(3)], -1)
    n = out["normal"].copy()
    n[..., 2] = -n[..., 2]  # Blender camera space has -Z towards the lens; flip so +Z faces the viewer
    nx, ny = n[..., 0].copy() * fx, n[..., 1].copy()
    # image y is down, camera y is up. Rotate the in-plane part with the picture.
    n[..., 0] = ca * nx + sa * ny
    n[..., 1] = -sa * nx + ca * ny
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-4)
    out["normal"] = n
    out["mask"] = np.clip(out["mask"], 0, 1)
    out["_co"] = np.array([[a, b, c], [d, e, f]], np.float32)
    return out


def unwarp_pts(Q, xy):
    """Map source pixel coordinates to the output of warp()."""
    M = np.vstack([Q["_co"], [0, 0, 1]])
    inv = np.linalg.inv(M)
    p = np.c_[xy, np.ones(len(xy))]
    return (p @ inv.T)[:, :2]


def read_pdb():
    """Real Calpha trace and all heavy atoms from the AlphaFold DB model."""
    ca, conf, atoms = [], [], []
    for ln in open(PDB):
        if not ln.startswith("ATOM"):
            continue
        xyz = [float(ln[30:38]), float(ln[38:46]), float(ln[46:54])]
        atoms.append(xyz)
        if ln[12:16].strip() == "CA":
            ca.append(xyz)
            conf.append(float(ln[60:66]) / 100)
    ca, conf, atoms = np.array(ca, np.float64), np.array(conf, np.float32), np.array(atoms, np.float64)
    VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]  # same frame as make_surface.py
    u, _, vt = np.linalg.svd(np.array(VIEW))
    R = u @ vt
    o = ca[:302].mean(0)
    return ((ca - o) @ R.T).astype(np.float32), conf, ((atoms - o) @ R.T).astype(np.float32)


_V = np.array([0.15, -0.25, 1.0])
_V = _V / np.linalg.norm(_V)


def surf_center():
    D = np.load(SURF)
    v = D["verts"]
    return (v.min(0) + v.max(0)) / 2


def project(xyz, res=(1920, 1080), offset=(0, 0, 0)):
    """Project model Angstrom coordinates through the shared camera into the 1920x1080 pass frame."""
    SC = 0.1
    v = (np.asarray(xyz, np.float64) + np.asarray(offset)) * SC
    c = surf_center() * SC
    cam = c + _V * 26.0
    f = -_V
    up0 = np.array([0, 0, 1.0])
    up = up0 - up0.dot(_V) * _V
    up /= np.linalg.norm(up)
    r = np.cross(f, up)
    d = v - cam
    zc = d @ f
    xc = d @ r
    yc = d @ up
    w, h = res
    fpx = 70.0 / 36.0 * w
    return np.c_[w / 2 + fpx * xc / zc, h / 2 - fpx * yc / zc], zc


# ---- type on a raster


def text_mask(txt, fnt, w=W, h=H, xy=(0, 0), anchor="la", spacing=0):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    if spacing:
        x, y = xy
        for ch in txt:
            d.text((x, y), ch, 255, font=fnt, anchor=anchor)
            x += d.textlength(ch, font=fnt) + spacing
    else:
        d.text(xy, txt, 255, font=fnt, anchor=anchor)
    return np.asarray(im, np.float32) / 255


def type_sprite(txt, fnt, sx=1.0, sy=1.0, pad=8):
    """Tight L-mode sprite of a text line, optionally stretched."""
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    b = d.textbbox((0, 0), txt, font=fnt)
    im = Image.new("L", (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), 0)
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, 255, font=fnt)
    if sx != 1 or sy != 1:
        im = im.resize((int(im.width * sx), int(im.height * sy)), Image.LANCZOS)
    return im


def paste_sprite(rgb, spr, x, y, col, rot=0, alpha=1.0):
    """Composite an L sprite on a float rgb array. (x, y) is the sprite centre."""
    s = spr.rotate(rot, Image.BICUBIC, expand=True) if rot else spr
    a = np.asarray(s, np.float32) / 255 * alpha
    x0, y0 = int(x - a.shape[1] / 2), int(y - a.shape[0] / 2)
    x1, y1 = x0 + a.shape[1], y0 + a.shape[0]
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(rgb.shape[1], x1), min(rgb.shape[0], y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return rgb
    a = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0, None]
    rgb[cy0:cy1, cx0:cx1] = rgb[cy0:cy1, cx0:cx1] * (1 - a) + np.asarray(col, np.float32) * a
    return rgb


def comp(rgb, a, col):
    """Composite a colour (or image) through a float mask."""
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def poly_mask(pts, w=W, h=H, ss=3):
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def lines_mask(segs, width=1.0, w=W, h=H, ss=3):
    """segs: list of (x0, y0, x1, y1)."""
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    wd = max(1, int(round(width * ss)))
    for s in segs:
        d.line([(s[0] * ss, s[1] * ss), (s[2] * ss, s[3] * ss)], fill=255, width=wd)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def finish(rgb, name):
    p = OUT / name
    assert rgb.shape[:2] == (H, W), rgb.shape
    save(rgb, str(p))
    print("wrote", p)
