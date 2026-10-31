"""HKBU SCIE1007 coursework science video. Small numpy/PIL kit for the group A style scouts.

Reprojects the real CDK20 surface mesh (AlphaFold DB v6, cdk20_surface.npz) from any angle in about a second,
and supplies paper, halftone, hand-built block lettering and polygon helpers. W x H is 1280 x 720.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
OUT = ROOT / "styleframes/art/scouts/a"
W, H = 1280, 720
F = "C:/Windows/Fonts/"


def font(name, size):
    return ImageFont.truetype(F + name, size)


# ---------- real data ----------
_S = None


def surface():
    global _S
    if _S is None:
        D = np.load(ROOT / "styleframes/S2plus/_work/cdk20_surface.npz")
        v, q, c = D["verts"].astype(np.float32), D["quads"], D["conf"].astype(np.float32)
        a, b, d = v[q[:, 0]], v[q[:, 1]], v[q[:, 3]]
        fn = np.cross(b - a, d - a)
        n = np.zeros_like(v)
        for i in range(4):
            np.add.at(n, q[:, i], fn)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
        cen = (v.min(0) + v.max(0)) / 2
        if np.mean(np.sum((v - cen) * n, 1)) < 0:
            n = -n
        _S = dict(v=v - cen, n=n, c=c, cen=cen)
    return _S


def atoms():
    """Backbone CA trace: xyz (centred like the surface), residue confidence, and all heavy atoms."""
    S = surface()
    xyz, conf, name, res = [], [], [], []
    for ln in open(ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"):
        if ln.startswith("ATOM"):
            xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            conf.append(float(ln[60:66]) / 100)
            name.append(ln[12:16].strip())
            res.append(int(ln[22:26]))
    conf, name, res = np.array(conf, np.float32), np.array(name), np.array(res)
    ca = name == "CA"
    # the mesh lives in the camera frame of make_surface.py, so the atoms must go through the same transform
    VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
    u, _, vt = np.linalg.svd(np.array(VIEW))
    xyz = np.array(xyz, np.float64)
    xyz = (xyz - xyz[ca & (res <= 302)].mean(0)) @ (u @ vt).T
    xyz = (xyz - S["cen"]).astype(np.float32)
    return dict(ca=xyz[ca], ca_conf=conf[ca], xyz=xyz, conf=conf, name=name, res=res)


def rot(rx=0, ry=0, rz=0):
    """Rotation in degrees, applied in x, y, z order. Base orientation matches the shared M04 side view."""
    a, b, c = np.radians([rx, ry, rz])
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def base_view():
    """The same side the shared passes use: VIEW = (0.15, -0.25, 1) with +Y up."""
    z = np.array([0.15, -0.25, 1.0])
    z /= np.linalg.norm(z)
    x = np.cross([0, 1, 0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z])


def fft_blur(a, s):
    if s <= 0:
        return a
    h, w = a.shape
    pad = int(s * 3) + 2
    p = np.pad(a, pad, mode="edge")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx**2 + fy**2))
    o = np.fft.irfft2(np.fft.rfft2(p) * g, s=p.shape)
    return o[pad:pad + h, pad:pad + w].astype(np.float32)


def resize(a, w, h, how=Image.BICUBIC):
    return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w, h), how))


def view(R=None, scale=4.0, cx=W / 2, cy=H / 2, w=W, h=H, ss=0.5, L=(-0.55, 0.65, 0.55), L2=(0.8, -0.3, 0.2), persp=0.0):
    """Project the real surface. scale is px per Angstrom at output size. Returns float passes at w x h.

    z: larger is nearer, in Angstrom, undefined outside the mask. key, rim: lambert light. ao: cheap screen space cavity shade.
    persp > 0 adds a wide-angle feel: points nearer the camera get bigger.
    """
    S = surface()
    R = base_view() if R is None else R
    v, n = S["v"] @ R.T, S["n"] @ R.T
    W2, H2 = int(w * ss), int(h * ss)
    k = 1 + persp * v[:, 2] / 25.0
    px = (v[:, 0] * k * scale + cx) * ss
    py = (-v[:, 1] * k * scale + cy) * ss
    fp = max(1, int(np.ceil(0.9 * ss * scale / 2.0)))
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
    c = np.where(m, S["c"][buf.clip(0)], 0).astype(np.float32)
    # close the small pinholes the splat leaves
    wt = fft_blur(m.astype(np.float32), 1.2) + 1e-4
    sm = lambda a: fft_blur(a * m, 1.2) / wt
    mask_s = fft_blur(m.astype(np.float32), 0.7)
    z, c = sm(z), sm(c)
    nn = np.stack([sm(nn[..., i]) for i in range(3)], -1)
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-5)
    up = lambda a: resize(a, w, h)
    mask = np.clip(up(mask_s) * 1.6 - 0.3, 0, 1)
    z, c = up(z), up(c)
    nn = np.stack([up(nn[..., i]) for i in range(3)], -1)
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-5)
    Lv = np.array(L, np.float32) / np.linalg.norm(L)
    Lb = np.array(L2, np.float32) / np.linalg.norm(L2)
    key = np.clip(nn @ Lv, 0, 1) * mask
    rim = np.clip(nn @ Lb, 0, 1) * mask
    wm = fft_blur(mask, 10 * scale / 4) + 1e-3
    ao = np.clip(1 - np.clip(fft_blur(z * mask, 10 * scale / 4) / wm - z, 0, 8) / 6, 0, 1) * mask
    return dict(mask=mask, z=z * (mask > 0), normal=nn, key=key, rim=rim, ao=ao, conf=c, w=w, h=h)


def project(p, R=None, scale=4.0, cx=W / 2, cy=H / 2, persp=0.0):
    R = base_view() if R is None else R
    v = p @ R.T
    k = 1 + persp * v[:, 2] / 25.0
    return np.stack([v[:, 0] * k * scale + cx, -v[:, 1] * k * scale + cy, v[:, 2]], 1)


# ---------- print helpers ----------
def noise(h=H, w=W, s=8, seed=0):
    p = int(s * 4) + 4
    r = np.random.default_rng(seed).standard_normal((h + 2 * p, w + 2 * p)).astype(np.float32)
    n = fft_blur(r, s)[p:p + h, p:p + w]
    return (n - n.mean()) / (n.std() + 1e-6)


def paper(base, seed=1, mott=0.035, fibre=0.012, h=H, w=W):
    c = np.array(base, np.float32) / 255
    n = mott * (0.6 * noise(h, w, 60, seed) + 0.4 * noise(h, w, 9, seed + 1)) + fibre * noise(h, w, 0.8, seed + 2)
    return np.clip(c[None, None, :] * (1 + n[..., None]), 0, 1)


def ink(canvas, cov, col):
    """Lay flat ink of colour col (0..255) with coverage cov (0..1) over the canvas, multiply-free."""
    col = np.array(col, np.float32) / 255
    return canvas * (1 - cov[..., None]) + col * cov[..., None]


def mul(canvas, cov, col):
    col = np.array(col, np.float32) / 255
    return canvas * (1 - cov[..., None] * (1 - col))


def halftone(g, cell=9.0, ang=45.0, soft=0.9, h=None, w=None):
    """g 0..1 is ink wanted. Returns a hard dot screen of coverage 0..1."""
    h, w = g.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.radians(ang)
    u = (x * np.cos(a) + y * np.sin(a)) / cell
    v = (-x * np.sin(a) + y * np.cos(a)) / cell
    s = 0.5 + 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
    return np.clip((g - (1 - s)) * cell * soft * 0.45 + 0.5, 0, 1)


def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def shadow_of(m, dx, dy, s):
    return np.roll(np.roll(fft_blur(m, s), dy, 0), dx, 1)


# ---------- vector shapes, drawn at 3x and reduced ----------
class Layer:
    """Antialiased coverage mask built from polygons and text."""

    def __init__(self, w=W, h=H, ss=3):
        self.ss, self.w, self.h = ss, w, h
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def poly(self, pts, v=255):
        self.d.polygon([(float(x) * self.ss, float(y) * self.ss) for x, y in pts], fill=v)
        return self

    def rect(self, x0, y0, x1, y1, v=255):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], v)

    def line(self, pts, width, v=255):
        self.d.line([(float(x) * self.ss, float(y) * self.ss) for x, y in pts], fill=v, width=int(width * self.ss), joint="curve")
        return self

    def ell(self, x0, y0, x1, y1, v=255):
        self.d.ellipse([x0 * self.ss, y0 * self.ss, x1 * self.ss, y1 * self.ss], fill=v)
        return self

    def text(self, xy, s, fnt, fs, v=255, track=0, anchor="ls"):
        f = font(fnt, int(fs * self.ss))
        x, y = xy[0] * self.ss, xy[1] * self.ss
        for ch in s:
            self.d.text((x, y), ch, font=f, fill=v, anchor=anchor)
            x += f.getlength(ch) + track * self.ss
        return self

    def a(self):
        im = self.im.resize((self.w, self.h), Image.LANCZOS)
        return np.asarray(im, np.float32) / 255


def text_rot(s, fnt, fs, ang, cx, cy, track=0, w=W, h=H, ss=3):
    """Coverage of a string rotated about its centre, placed with centre at cx, cy."""
    f = font(fnt, int(fs * ss))
    tw = int(sum(f.getlength(c) + track * ss for c in s)) + 40
    th = int(fs * ss * 1.8)
    im = Image.new("L", (tw, th), 0)
    d = ImageDraw.Draw(im)
    x = 20
    for ch in s:
        d.text((x, th * 0.72), ch, font=f, fill=255, anchor="ls")
        x += f.getlength(ch) + track * ss
    im = im.rotate(ang, Image.BICUBIC, expand=True)
    big = Image.new("L", (w * ss, h * ss), 0)
    big.paste(im, (int(cx * ss - im.width / 2), int(cy * ss - im.height / 2)))
    return np.asarray(big.resize((w, h), Image.LANCZOS), np.float32) / 255


# Block letters in a unit box (y down). Each glyph is a list of (+1 or -1, polygon).
def _r(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


BLOCK = {
    "C": [(1, _r(0, 0, 1, 1)), (-1, _r(0.34, 0.24, 1.02, 0.76))],
    "D": [
        (1, [(0, 0), (0.70, 0), (1, 0.24), (1, 0.76), (0.70, 1), (0, 1)]),
        (-1, [(0.34, 0.24), (0.58, 0.24), (0.66, 0.34), (0.66, 0.66), (0.58, 0.76), (0.34, 0.76)]),
    ],
    "K": [
        (1, _r(0, 0, 0.34, 1)),
        (1, [(0.34, 0.36), (0.64, 0), (1.0, 0), (0.60, 0.48), (0.34, 0.74)]),
        (1, [(0.42, 0.56), (0.62, 0.38), (1.0, 1), (0.64, 1)]),
    ],
    "2": [
        (1, _r(0, 0, 1, 0.24)),
        (1, _r(0.66, 0, 1, 0.60)),
        (1, _r(0, 0.38, 1, 0.60)),
        (1, _r(0, 0.38, 0.34, 1)),
        (1, _r(0, 0.76, 1, 1)),
    ],
    "0": [
        (1, [(0.22, 0), (0.78, 0), (1, 0.18), (1, 0.82), (0.78, 1), (0.22, 1), (0, 0.82), (0, 0.18)]),
        (-1, _r(0.34, 0.24, 0.66, 0.76)),
    ],
}


def glyph_pts(ch, T):
    """Yield (sign, transformed polygon). T maps a unit-box (u, v) to screen."""
    for s, pl in BLOCK[ch]:
        yield s, [T(u, v) for u, v in pl]


def block_word(layer, word, T_for_index):
    for i, ch in enumerate(word):
        T = T_for_index(i)
        for s, pl in glyph_pts(ch, T):
            layer.poly(pl, 255 if s > 0 else 0)
    return layer


def affine(x, y, w, h, deg=0, shear=0):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)

    def T(u, v):
        px, py = (u + shear * (1 - v)) * w, v * h
        return x + px * c - py * s, y + px * s + py * c

    return T


def warp(a, dx, dy):
    """Bilinear resample of H x W (x C) image at x + dx, y + dy."""
    h, w = a.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    X, Y = np.clip(x + dx, 0, w - 1.001), np.clip(y + dy, 0, h - 1.001)
    x0, y0 = X.astype(np.int32), Y.astype(np.int32)
    fx, fy = X - x0, Y - y0
    if a.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    return (a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy) + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy


def save(rgb, name):
    p = OUT / name
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)
    print("saved", p)
