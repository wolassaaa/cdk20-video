"""HKBU SCIE1007 coursework science video. polar direction: shared tools. The interference colour here is a look, not data."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art")
sys.path.insert(0, str(ART / "scouts/g/code"))
import glib as G
from glib import gblur, cavity, smooth_pass, rot, render, surface, atoms

HERE = Path(__file__).resolve().parent
STILLS = HERE.parent / "stills"
WORK = HERE.parent / "_work"
W, H = 1920, 1080
FD = r"C:/Users/woola/AppData/Local/Microsoft/Windows/Fonts/"
PX, PY = -100.0, 3400.0        # hidden pivot of the sheet edge: the same line swings through the whole film
INK = (.075, .075, .08)
PAPER = (.80, .795, .775)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def sans(size, wght=500):
    f = ImageFont.truetype(FD + "NotoSansSC-VF.ttf", size); f.set_variation_by_axes([wght]); return f


def serif(size, wght=900):
    f = ImageFont.truetype(FD + "NotoSerifSC-VF.ttf", size); f.set_variation_by_axes([wght]); return f


def mask_text(s, f, xy, anchor="ls"):
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).text(xy, s, 255, font=f, anchor=anchor)
    return np.asarray(im, np.float32) / 255


def over(rgb, col, a):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def put(rgb, s, xy, f, col=INK, anchor="ls"):
    return over(rgb, col, mask_text(s, f, xy, anchor))


def poly(pts, ss=3):
    im = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def seg(p0, p1, wid, dash=None, gap=None, ss=3):
    """A line, solid or dashed. Line type carries the evidence level, so dashes are real geometry."""
    im = Image.new("L", (W * ss, H * ss), 0); d = ImageDraw.Draw(im)
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0); u = (p1 - p0) / max(L, 1e-6)
    if dash is None:
        d.line([*(p0 * ss), *(p1 * ss)], fill=255, width=int(wid * ss))
    else:
        s = 0
        while s < L:
            a = p0 + u * s; b = p0 + u * min(s + dash, L)
            d.line([*(a * ss), *(b * ss)], fill=255, width=int(wid * ss))
            s += dash + gap
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def box(x0, y0, x1, y1, wid=4, dash=None, gap=None):
    out = np.zeros((H, W), np.float32)
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        out = np.maximum(out, seg(a, b, wid, dash, gap))
    return out


def line_d(t):
    """Signed distance to the sheet edge. Negative is the coloured side."""
    return (xx - (PX + (PY - yy) * t)) / np.sqrt(1 + t * t)


def line_x(t, y):
    return PX + (PY - y) * t


def sheet(colour, grey, t):
    d = line_d(t)
    a = np.clip(-d / 1.3 + .5, 0, 1)[..., None]
    g = grey * (1 - .34 * np.exp(-np.maximum(d, 0) / 42))[..., None]       # the sheet sits above the grey world and casts a soft shadow
    rgb = colour * a + g * (1 - a)
    return rgb + (np.exp(-(d / 1.7) ** 2) * .85)[..., None] * np.array([1, .99, .96], np.float32)


# ---- colour: the Michel-Levy idea, used as a palette ----
def _g(l, m, s1, s2):
    return np.exp(-.5 * ((l - m) / np.where(l < m, s1, s2)) ** 2)


def _lut(n=3000, gmax=3000, push=1.35):
    lam = np.arange(400, 701, 5, dtype=np.float32)
    x = 1.056 * _g(lam, 599.8, 37.9, 31.0) + .362 * _g(lam, 442, 16, 26.7) - .065 * _g(lam, 501.1, 20.4, 26.2)
    y = .821 * _g(lam, 568.8, 46.9, 40.5) + .286 * _g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * _g(lam, 437, 11.8, 36) + .681 * _g(lam, 459, 26, 13.8)
    Gm = np.linspace(0, gmax, n, dtype=np.float32)
    T = np.sin(np.pi * Gm[:, None] / lam[None]) ** 2
    XYZ = np.stack([(T * x).sum(1), (T * y).sum(1), (T * z).sum(1)], -1) / y.sum() * 2
    M = np.array([[3.2406, -1.5372, -.4986], [-.9689, 1.8758, .0415], [.0557, -.2040, 1.0570]], dtype=np.float32)
    rgb = np.clip(XYZ @ M.T, 0, None) ** (1 / 2.2)
    l = rgb.mean(1, keepdims=True)
    return np.clip(l + (rgb - l) * push, 0, 1)


LUT = _lut()


def lookup(g):
    return LUT[np.clip((g / 3000 * (len(LUT) - 1)).astype(np.int32), 0, len(LUT) - 1)]


def limit(rgb, peak=.74):
    """Hold the colour side down: luminance rolls off toward peak, hue stays."""
    Y = (rgb * [.2126, .7152, .0722]).sum(-1, keepdims=True)
    k = peak * (1 - np.exp(-Y / peak)) / np.maximum(Y, 1e-4)
    return rgb * k


def thickness(P, R, scale, cx, cy, S):
    """Front minus back of the real surface along the view, in Angstrom. A clear cast of the model would be this thick at each pixel."""
    V = (S["v"] - S["center"]) @ R.T
    st = 3
    gw, gh = W // st + 1, H // st + 1
    ix = np.clip(((cx + V[:, 0] * scale) / st).astype(np.int32), 0, gw - 1); iy = np.clip(((cy - V[:, 1] * scale) / st).astype(np.int32), 0, gh - 1)
    ok = (cx + V[:, 0] * scale > 0) & (cx + V[:, 0] * scale < W) & (cy - V[:, 1] * scale > 0) & (cy - V[:, 1] * scale < H)
    zb = np.full((gh, gw), 1e6, np.float32); zf = np.full((gh, gw), -1e6, np.float32)
    np.minimum.at(zb, (iy[ok], ix[ok]), V[ok, 2]); np.maximum.at(zf, (iy[ok], ix[ok]), V[ok, 2])
    hit = (zb < 1e5).astype(np.float32)
    T = np.where(hit > 0, zf - zb, 0).astype(np.float32)
    T = gblur(T * hit, 2.2) / np.maximum(gblur(hit, 2.2), 1e-3)
    T = np.asarray(Image.fromarray(T).resize((W, H), Image.BICUBIC), np.float32)
    return T * P["mask"]


STOPS = ["f4c13a", "ee6a2c", "cf1f6e", "5a22c4", "1468dc", "10b4a6", "86cc3c", "f4c13a"]


def _pal(n=2048):
    c = np.array([[int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] for h in STOPS], np.float32) ** 2.2
    u = np.linspace(0, len(STOPS) - 1, n)
    i = np.minimum(u.astype(int), len(STOPS) - 2); f = (u - i)[..., None]; f = f * f * (3 - 2 * f)
    return (c[i] * (1 - f) + c[i + 1] * f) ** (1 / 2.2)


PAL = _pal()


def pal(p):
    return PAL[((p % 1) * (len(PAL) - 1)).astype(np.int32)]


def photo(P, T, scale, k=.016, height=.034, floor=.10, seed=1, shift=0., turn=0.):
    """Clear plastic between two crossed sheets: colour bands follow height and thickness, each bump carries a dark cross. A look, never a measurement.
    turn is the sheet angle in radians: it swings the crosses without changing the bands, so nothing flashes."""
    z = P["z"]; n = P["n"]; m = P["mask"]
    Ts = gblur(T, 10)
    zs = gblur(z * m, 3) / np.maximum(gblur(m, 3), 1e-3)
    wob = G.fbm(H, W, beta=3.9, seed=seed)
    c = pal(k * Ts + height * (zs - P["zmin"]) + .42 * (wob - .5) + shift)
    th = np.arctan2(n[..., 1], n[..., 0]) + .55 * (wob - .5) + turn
    ext = floor + (1 - floor) * (np.sin(2 * th) ** 2) ** .5
    thin = np.clip(gblur(T, 3) / 7, 0, 1)[..., None]
    c = (c.mean(-1, keepdims=True) * (1 - thin) + c * thin)
    L = np.clip((n * np.array([-.34, .5, .8])).sum(-1), 0, 1)
    cav = gblur(cavity(gblur(z, 1.5) * scale, m, (5, 14, 30)), 2)
    shade = (.80 + .38 * L) * (1 - .86 * np.clip(cav * 1.4, 0, 1))
    return c * (ext * shade * m)[..., None]


def field(seed=3, size=1.0):
    """A shapeless clear sheet of soft bumps for frames with no protein in them, so colour never shows CDK20 before its label does."""
    r = np.random.default_rng(seed)
    z = np.zeros((H, W), np.float32)
    for sig, n_, amp in ((95, 60, 1.0), (48, 150, .5)):
        p = np.zeros((H, W), np.float32)
        p[r.integers(0, H, n_), r.integers(0, W, n_)] = r.uniform(.5, 1.5, n_)
        q = gblur(p, sig * size); z += amp * q / q.max()
    z = 34 * z / z.max()
    gy, gx = np.gradient(z)
    n = np.stack([-gx * 3.2, gy * 3.2, np.ones_like(z)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return dict(z=z, n=n.astype(np.float32), mask=np.ones_like(z), zmin=float(z.min()), zmax=float(z.max())), z - z.min() + 8


def plaster(P, scale, bg):
    """The same surface with the sheet out of the way: plain, pale, almost nothing."""
    n = P["n"]; m = P["mask"]
    L = np.clip((n * np.array([-.34, .5, .8])).sum(-1), 0, 1)
    cav = gblur(cavity(gblur(P["z"], 2) * scale, m, (5, 14, 30)), 3)
    v = .70 + .17 * L - .30 * np.clip(cav * 1.3, 0, 1)
    p = v[..., None] * np.array([1, .993, .972], np.float32)
    return bg * (1 - m[..., None]) + p * m[..., None]


def grey_world(v=.80, warm=.0):
    """Bright field. Static, smooth, no grain."""
    r = ((xx - W * .56) / W) ** 2 + ((yy - H * .46) / H) ** 2
    g = v * (1.03 - .22 * r)
    return g[..., None] * np.array([1, .995 - warm * .03, .975 - warm * .08], np.float32)


def save(rgb, name):
    p = STILLS / name
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
    return p
