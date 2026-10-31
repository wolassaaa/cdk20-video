"""HKBU SCIE1007 coursework science video. Small helpers shared by the group D style scouts (no scipy or cv2 on this machine)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art")
ROOT = Path(r"D:/。hkbu/molecular science")
sys.path.insert(0, str(ART / "_shared"))
from passes import load, save  # noqa: E402

OUT = ART / "scouts" / "d"
FD = "C:/Windows/Fonts/"
LABEL = "AlphaFold DB v6 \u00b7 predicted"
_cache = {}


def passes():
    if "P" not in _cache:
        _cache["P"] = load(scale=1.0)
    return _cache["P"]


def sample(a, x, y):
    """Bilinear lookup of a 2D or 3D array at float pixel coordinates; outside reads 0."""
    h, w = a.shape[:2]
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < w - 1) & (y0 < h - 1)
    x0c, y0c = np.clip(x0, 0, w - 2), np.clip(y0, 0, h - 2)
    if a.ndim == 3:
        fx, fy, ok = fx[..., None], fy[..., None], ok[..., None]
    r = (a[y0c, x0c] * (1 - fx) * (1 - fy) + a[y0c, x0c + 1] * fx * (1 - fy)
         + a[y0c + 1, x0c] * (1 - fx) * fy + a[y0c + 1, x0c + 1] * fx * fy)
    return r * ok


def view(W=1280, H=720, zoom=1.0, rot=0.0, at=(0.5, 0.5), c=(0.5, 0.5), flipx=False):
    """Crop and rotate the passes into a W x H frame.
    zoom 1 = protein as large as the delivered 1280 frame. rot in degrees. c = which point of the source (0..1) lands at `at` (0..1 of the frame)."""
    P = passes()
    sh, sw = P["mask"].shape
    k = (W / sw) * zoom
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - at[0] * W, yy - at[1] * H
    if flipx:
        dx = -dx
    t = np.deg2rad(rot)
    ct, st = np.cos(t), np.sin(t)
    sx = (ct * dx + st * dy) / k + c[0] * sw
    sy = (-st * dx + ct * dy) / k + c[1] * sh
    out = {}
    m = sample(P["mask"], sx, sy)
    for name, a in P.items():
        out[name] = sample(a, sx, sy)
    n = out["normal"].copy()
    nx, ny = n[..., 0].copy(), n[..., 1].copy()
    if flipx:
        nx = -nx
    # image y runs down, normal y runs up: rotating the picture by +rot clockwise rotates the xy normal the same way on screen
    n[..., 0] = ct * nx + st * ny
    n[..., 1] = -st * nx + ct * ny
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-4)
    out["normal"] = n
    out["mask"] = m
    return out


def lit(Q, L, wrap=0.0):
    """Diffuse relight from a camera space direction: x right, y up, z into the screen (use negative z for light from the viewer side)."""
    L = np.array(L, np.float32)
    L /= np.linalg.norm(L)
    return np.clip(((Q["normal"] * L).sum(2) + wrap) / (1 + wrap), 0, 1)


def gauss(a, s):
    """Gaussian blur of any float array through the FFT, edge padded."""
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gauss(a[..., i], s) for i in range(a.shape[2])], -1)
    p = int(min(3 * s + 2, 256))
    b = np.pad(a, p, mode="edge")
    h, w = b.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    F = np.fft.rfft2(b) * np.exp(-2 * np.pi ** 2 * s ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(F, s=b.shape)[p:-p, p:-p].astype(np.float32)


def noise(h, w, cell, seed=0):
    r = np.random.default_rng(seed)
    gh, gw = max(2, int(h / cell) + 3), max(2, int(w / cell) + 3)
    g = r.random((gh, gw), dtype=np.float32)
    big = Image.fromarray(g).resize((int(gw * cell), int(gh * cell)), Image.BICUBIC)
    return np.asarray(big, dtype=np.float32)[:h, :w]


def fbm(h, w, cell, oct=4, seed=0, gain=0.5):
    a, s, t = 1.0, 0.0, 0.0
    out = np.zeros((h, w), np.float32)
    for i in range(oct):
        out += a * noise(h, w, max(1.0, cell / 2 ** i), seed + i * 7)
        s += a
        a *= gain
    return np.clip(out / s, 0, 1)


def edges(Q, dz=0.006, dn=0.35):
    """Boolean silhouette and crease lines from depth steps and normal turns."""
    d = Q["depth"]
    m = Q["mask"] > 0.5
    gz = np.zeros_like(d)
    gz[:, 1:] = np.abs(d[:, 1:] - d[:, :-1])
    gz[1:, :] = np.maximum(gz[1:, :], np.abs(d[1:, :] - d[:-1, :]))
    n = Q["normal"]
    gn = np.zeros_like(d)
    gn[:, 1:] = np.abs(n[:, 1:] - n[:, :-1]).sum(2)
    gn[1:, :] = np.maximum(gn[1:, :], np.abs(n[1:, :] - n[:-1, :]).sum(2))
    sil = np.zeros_like(m)
    sil[:, 1:] |= m[:, 1:] ^ m[:, :-1]
    sil[1:, :] |= m[1:, :] ^ m[:-1, :]
    return sil | ((gz > dz) & m) | ((gn > dn) & m), gz, gn


def bayer(n):
    b = np.array([[0.0]], np.float32)
    while b.shape[0] < n:
        b = np.block([[4 * b, 4 * b + 2], [4 * b + 3, 4 * b + 1]])
    return (b + 0.5) / b.size


def tile(p, h, w):
    return np.tile(p, (h // p.shape[0] + 1, w // p.shape[1] + 1))[:h, :w]


def bluenoise(h, w, seed=0, s=1.1):
    r = np.random.default_rng(seed).random((h, w), dtype=np.float32)
    hp = r - gauss(r, s)
    o = np.argsort(hp.ravel())
    out = np.empty(h * w, np.float32)
    out[o] = (np.arange(h * w) + 0.5) / (h * w)
    return out.reshape(h, w)


def font(name, size):
    p = name if ":" in name else FD + name
    return ImageFont.truetype(p, size)


def text(W, H, s, f, xy, anchor="la", track=0, aa=True):
    """Float 0..1 mask of a text line; track = extra pixels between letters."""
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    if not aa:
        d.fontmode = "1"
    if track == 0:
        d.text(xy, s, fill=255, font=f, anchor=anchor)
    else:
        total = sum(d.textlength(c, font=f) + track for c in s) - track
        x, y = xy
        if anchor[0] == "m":
            x -= total / 2
        elif anchor[0] == "r":
            x -= total
        for c in s:
            d.text((x, y), c, fill=255, font=f, anchor="l" + anchor[1])
            x += d.textlength(c, font=f) + track
    return np.asarray(im, np.float32) / 255


def nearest(a, k):
    return np.repeat(np.repeat(a, k, 0), k, 1)


def over(rgb, col, a):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.array(col, np.float32) * a


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def ramp(t, stops):
    """Colour ramp. stops = [(pos, '#rrggbb'), ...]."""
    xs = [p for p, _ in stops]
    cs = np.stack([hexc(c) for _, c in stops])
    return np.stack([np.interp(t, xs, cs[:, i]) for i in range(3)], -1).astype(np.float32)


def mesh():
    D = np.load(ART.parent / "S2plus" / "_work" / "cdk20_surface.npz")
    return D["verts"].astype(np.float32), D["quads"], D["conf"].astype(np.float32)


def ca():
    """C-alpha coordinates and pLDDT (0..1) from the AlphaFold DB model."""
    xyz, b = [], []
    for l in open(ROOT / "镜头设计_v3" / "assets" / "alphafold" / "AF-Q8IZL9-F1-model_v6.pdb", encoding="utf-8", errors="ignore"):
        if l.startswith("ATOM") and l[12:16].strip() == "CA":
            xyz.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
            b.append(float(l[60:66]) / 100)
    return np.array(xyz, np.float32), np.array(b, np.float32)


def sequence():
    p = ROOT / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data" / "sequence.json"
    d = json.load(open(p, encoding="utf-8"))
    return d
