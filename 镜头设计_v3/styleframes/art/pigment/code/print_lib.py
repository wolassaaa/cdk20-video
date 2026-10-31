"""HKBU SCIE1007 coursework science video. Pigment direction: a small printing press in numpy.

Every picture is plates of ink density on paper. Paper times, for each plate, 1 - density x (1 - ink colour): that is a plain sRGB multiply, the same sum as
mix-blend-mode: multiply in Remotion, so a layout found here can be rebuilt there. Worked at 3840x2160, box-reduced to 1920x1080 at the end.
Screens are locked to the page and every noise field is fixed, so nothing here can flicker. No per-frame grain, by the director's rule.
Two screens, because they mean different things:
  am() regular round dots on an exact grid: AI prediction.
  fm() irregular litho grain, no grid: the real body (BodyParts3D liver).
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
O = HERE.parent
WORK, STILLS = O / "_work", O / "stills"
W, H = 3840, 2160


def hx(s):
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


INK = dict(
    haem=hx("B01622"), bili=hx("F0B323"), eosin=hx("EC5A86"), melanin=hx("3D2518"), hema=hx("3E2F93"),
    carbon=hx("181716"), prussian=hx("0E5AA7"), indigo=hx("283A8E"), ochre=hx("B9592E"), graphite=hx("4B4946"),
)
PAPER = hx("F4EDDE")
X, Y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))


def band(seed, f0, bw):
    """Band-pass noise, made uniform 0-1. Cached, so every shot and every run sees the same grain."""
    p = WORK / f"n_{seed}_{f0}_{bw}.npy"
    if p.exists():
        return np.load(p)
    n = np.random.default_rng(seed).standard_normal((H, W), dtype=np.float32)
    F = np.fft.rfft2(n)
    r = np.sqrt(np.fft.fftfreq(H)[:, None] ** 2 + np.fft.rfftfreq(W)[None, :] ** 2)
    b = np.fft.irfft2(F * np.exp(-((r - f0) / bw) ** 2), s=(H, W)).astype(np.float32)
    q = np.quantile(b[::7, ::7].ravel(), np.linspace(0, 1, 2049))
    u = np.interp(b, q, np.linspace(0, 1, 2049)).astype(np.float32)
    np.save(p, u)
    return u


FINE, CRAYON, CLOUD, RIPPLE, SWELL = band(1, 0.22, 0.10), band(2, 0.075, 0.04), band(3, 0.0025, 0.002), band(4, 0.012, 0.008), band(5, 0.0035, 0.0025)
_mix = 0.45 * FINE + 0.55 * CRAYON
_q = np.quantile(_mix[::7, ::7].ravel(), np.linspace(0, 1, 1025))
GRAIN = np.interp(_mix, _q, np.linspace(0, 1, 1025)).astype(np.float32)
del _mix
SPECK = (FINE > 0.9975).astype(np.float32)   # the little paper flecks in a solid
_s = np.linspace(0, 1, 4097)
_u, _v = np.meshgrid(np.linspace(0, 2 * np.pi, 512, endpoint=False), np.linspace(0, 2 * np.pi, 512, endpoint=False))
_q2 = np.quantile(0.5 + 0.25 * (np.cos(_u) + np.cos(_v)), _s)


def thr(tone, field, soft):
    return np.clip((tone * (1 + soft) - soft / 2 - (1 - field)) / soft + 0.5, 0, 1).astype(np.float32)


def am(tone, pitch, deg, ox=0.0, oy=0.0, gain=0.03):
    """Regular dots. tone is ink coverage 0-1, pitch in 4K px. A little fixed ink spread keeps the dots from looking computed."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    u = (X * c + Y * s + ox) * (2 * math.pi / pitch)
    v = (-X * s + Y * c + oy) * (2 * math.pi / pitch)
    t = np.interp(0.5 + 0.25 * (np.cos(u) + np.cos(v)), _q2, _s).astype(np.float32)
    return thr(tone, t + gain * (CRAYON - 0.5), 2.6 / pitch)


def fm(tone, soft=0.10):
    """Irregular grain, the litho crayon: heavy tone closes up to solid ink, light tone breaks into specks."""
    return thr(tone, GRAIN, soft)


def blur(a, r):
    if r <= 0:
        return a
    b = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r))
    return np.asarray(b, np.float32) / 255


def blur_f(a, sigma):
    """Gaussian on floats, for smooth tone and depth."""
    F = np.fft.rfft2(a)
    r2 = np.fft.fftfreq(a.shape[0])[:, None] ** 2 + np.fft.rfftfreq(a.shape[1])[None, :] ** 2
    return np.fft.irfft2(F * np.exp(-2 * (math.pi * sigma) ** 2 * r2), s=a.shape).astype(np.float32)


def rough(mask, r=3.0, amp=0.5):
    """Ink edge instead of a vector edge."""
    b = blur(mask, r)
    return np.clip((b - 0.5 + amp * (FINE * 0.4 + CRAYON * 0.6 - 0.5) * (b > 0.02) * (b < 0.98)) / 0.12 + 0.5, 0, 1).astype(np.float32)


def rect(x0, y0, x1, y1):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle([x0 * 2, y0 * 2, x1 * 2, y1 * 2], fill=255)
    return np.asarray(m, np.float32) / 255


def shift(d, dx, dy):
    """Fixed misregistration of a plate, in 1080p px. Ink pushed off the sheet is gone, it does not wrap."""
    o = np.roll(np.roll(d, dy * 2, 0), dx * 2, 1)
    if dy > 0: o[:dy * 2] = 0
    if dy < 0: o[dy * 2:] = 0
    if dx > 0: o[:, :dx * 2] = 0
    if dx < 0: o[:, dx * 2:] = 0
    return o


def levels(a, lo, hi, g=1.0):
    return (np.clip((a - lo) / (hi - lo), 0, 1) ** g).astype(np.float32)


def smooth(a, lo, hi):
    u = np.clip((a - lo) / (hi - lo), 0, 1)
    return (u * u * (3 - 2 * u)).astype(np.float32)


def rgba(rel):
    im = Image.open(WORK / rel).convert("RGBA")
    if im.size != (W, H):
        im = im.resize((W, H), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255


def paper():
    p = PAPER * (1 + 0.016 * (CLOUD[..., None] - 0.5) + 0.014 * (FINE[..., None] - 0.5))
    return p.astype(np.float32)


def lay(img, d, ink, solid=True):
    """One plate, multiplied. solid adds the slight unevenness and flecks of a real flat of ink. Fixed, so it never moves."""
    c = INK[ink] if isinstance(ink, str) else ink
    if solid:
        d = d * (0.965 + 0.035 * CRAYON) * (1 - 0.8 * SPECK)
    img *= 1 - d[..., None] * (1 - c)
    return img


def text(id_):
    t = np.asarray(Image.open(WORK / "text" / f"{id_}.png").convert("RGB"), np.float32) / 255
    return t[..., 0], t[..., 1], t[..., 2]


def patches(img, a, b=None, y=2000):
    S, x0 = 80, 96
    cell = lambda i: rect((x0 + i * S) / 2, y / 2, (x0 + (i + 1) * S) / 2 - 0.5, (y + S) / 2 - 0.5)
    if b is None:
        for i, t in enumerate((1.0, 0.72, 0.5, 0.28, 0.0)):
            lay(img, cell(i) * (am(np.full((H, W), t, np.float32), 16, 45) if t < 1 else 1), a, solid=False)
    else:
        lay(img, cell(0) + cell(4), a, solid=False)
        lay(img, cell(1) * am(np.full((H, W), 0.5, np.float32), 16, 45), a, solid=False)
        lay(img, cell(2) + cell(4), b, solid=False)
        lay(img, cell(3) * am(np.full((H, W), 0.5, np.float32), 16, 75), b, solid=False)
    return img


def swatch(kind, x, y, s=36):
    """Evidence key beside a tag, 1080p px, shape only: solid, dots, outline, pencil. Returns a density mask."""
    x, y, s = x * 2, y * 2, s * 2
    box = [x, y, x + s, y + s]
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    if kind == "solid":
        d.rectangle(box, fill=255)
    elif kind == "dots":
        d.rectangle(box, fill=255)
        return np.asarray(m, np.float32) / 255 * am(np.full((H, W), 0.45, np.float32), 16, 45)
    elif kind == "outline":
        d.rectangle(box, outline=255, width=5)
    else:
        return pencil([[(x, y), (x + s, y), (x + s, y + s), (x, y + s), (x, y)]], w=4, dash=(12, 9), wobble=1.2)
    return np.asarray(m, np.float32) / 255


def regmark(cx, cy, r=20):
    """Registration target, 4K px. Printed on every plate, so the fixed offset between plates is visible, as on a real sheet."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=3)
    d.line([cx - r - 10, cy, cx + r + 10, cy], fill=255, width=3)
    d.line([cx, cy - r - 10, cx, cy + r + 10], fill=255, width=3)
    return np.asarray(m, np.float32) / 255


def pencil(segs, w=5, seed=1, dash=(34, 20), wobble=2.2):
    """Graphite: hand-wobbled dashes, broken by the paper tooth. segs is a list of polylines in 4K px. dash None draws a continuous line."""
    rng = np.random.default_rng(seed)
    m = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(m)
    for pts in segs:
        p = np.array(pts, float)
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        s = 0.0
        while s < L[-1]:
            e = min(s + (dash[0] if dash else 1e9), L[-1])
            ts = np.linspace(s, e, max(int((e - s) / 6) + 2, 2))
            q = np.c_[np.interp(ts, L, p[:, 0]), np.interp(ts, L, p[:, 1])] + np.cumsum(rng.normal(0, wobble / 3, (len(ts), 2)), 0) * 0.5 + rng.normal(0, wobble / 2, 2)
            dr.line([tuple(a) for a in q], fill=255, width=w, joint="curve")
            s = e + (dash[1] if dash else 0)
    a = np.asarray(m, np.float32) / 255
    return blur(a, 0.8) * (0.55 + 0.45 * thr(np.full((H, W), 0.8, np.float32), FINE, 0.3))


def save(img, name, rows=None):
    a = np.clip(img if rows is None else img[:rows], 0, 1)
    a = 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])
    STILLS.mkdir(exist_ok=True)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(STILLS / f"{name}.png", optimize=False)
    print("wrote", STILLS / f"{name}.png", flush=True)
