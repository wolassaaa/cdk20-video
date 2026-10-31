"""HKBU SCIE1007 coursework science video. Small numpy and PIL helpers for the group F style scouts (film and title sequence methods)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
sys.path.insert(0, str(ROOT / "styleframes/art/_shared"))
from passes import load, save  # noqa: E402,F401

OUT = ROOT / "styleframes/art/scouts/f"
WORK = OUT / "_work"
WORK.mkdir(exist_ok=True)
W, H = 1280, 720
FONTS = "C:/Windows/Fonts/"
LABEL = "AlphaFold DB v6 · predicted"


def load_view(name):
    """Load a custom camera pass set rendered by bl_view.py, same keys as passes.load."""
    d = np.load(WORK / f"view_{name}.npz")
    out = {k: d[k].astype(np.float32) for k in d.files}
    mk = out["mask"]
    for k in ("key", "rim", "ao", "depth", "conf", "normal", "pos"):
        a = out[k]
        den = np.maximum(mk, 1e-3) if a.ndim == 2 else np.maximum(mk, 1e-3)[..., None]
        out[k] = np.where((mk > 1e-3) if a.ndim == 2 else (mk > 1e-3)[..., None], a / den, 0)
    return out


def gauss(a, s):
    """FFT gaussian blur with mirrored edges, H x W or H x W x C."""
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gauss(a[..., i], s) for i in range(a.shape[2])], -1)
    h, w = a.shape
    pad = int(min(3 * s, min(h, w) // 2))
    b = np.pad(a, pad, mode="reflect")
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    r = np.fft.irfft2(np.fft.rfft2(b) * g, s=b.shape).astype(np.float32)
    return r[pad:pad + h, pad:pad + w]


def box_x(a, n):
    """Horizontal box blur of width n, the motion blur inside one step-printed frame."""
    n = max(1, int(n))
    p = np.pad(a, [(0, 0), (n, n)] + [(0, 0)] * (a.ndim - 2), mode="edge")
    c = np.cumsum(p, axis=1, dtype=np.float64)
    r = (c[:, n:] - c[:, :-n]) / n
    return r[:, n // 2 + 1: n // 2 + 1 + a.shape[1]].astype(np.float32)


def noise(shape, beta=2.0, seed=0, lo=0.0):
    """Spectral noise, 1/f^beta. Returns 0..1, roughly uniform."""
    rng = np.random.default_rng(seed)
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[f < lo] = 0
    amp[0, 0] = 0
    z = rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape)
    r = np.fft.irfft2(z * amp, s=(h, w))
    o = np.argsort(np.argsort(r.ravel())).reshape(r.shape) / r.size
    return o.astype(np.float32)


def noise_raw(shape, beta=2.0, seed=0):
    rng = np.random.default_rng(seed)
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[0, 0] = 0
    z = rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape)
    r = np.fft.irfft2(z * amp, s=(h, w))
    return ((r - r.mean()) / r.std()).astype(np.float32)


def sample(img, x, y):
    """Bilinear lookup with clamped coordinates."""
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - x0, y - y0
    if img.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def screen(a, b):
    return 1 - (1 - np.clip(a, 0, 1)) * (1 - np.clip(b, 0, 1))


def rgb(hexs):
    s = hexs.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def mix(a, b, t):
    colour = np.ndim(a) in (1, 3) or np.ndim(b) in (1, 3)
    if np.ndim(t) == 2 and colour:
        t = t[..., None]
    return a * (1 - t) + b * t


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def font(name, size, index=0):
    return ImageFont.truetype(FONTS + name, size, index=index)


def text_mask(txt, fnt, xy, tracking=0, wh=(W, H), ss=3, anchor="ls"):
    """Antialiased text mask with manual tracking. xy is the baseline start in output pixels."""
    w, h = wh
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    big = fnt.font_variant(size=fnt.size * ss)
    x = xy[0] * ss
    y = xy[1] * ss
    for ch in txt:
        d.text((x, y), ch, fill=255, font=big, anchor=anchor)
        x += d.textlength(ch, font=big) + tracking * ss
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def text_width(txt, fnt, tracking=0):
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    return sum(d.textlength(c, font=fnt) + tracking for c in txt) - tracking


def contours(mask):
    """Trace the pixel-crack outlines of a boolean mask into closed loops. Returns list of N x 2 float arrays (x, y)."""
    m = np.pad(mask.astype(bool), 1)
    nxt = {}
    # directed cracks with the inside kept on the right hand
    ys, xs = np.nonzero(m[1:, 1:-1] != m[:-1, 1:-1])
    for y, x in zip(ys.tolist(), xs.tolist()):
        a, b = (x + 1, y + 1), (x + 2, y + 1)
        if m[y + 1, x + 1]:
            nxt.setdefault(a, []).append(b)
        else:
            nxt.setdefault(b, []).append(a)
    ys, xs = np.nonzero(m[1:-1, 1:] != m[1:-1, :-1])
    for y, x in zip(ys.tolist(), xs.tolist()):
        a, b = (x + 1, y + 1), (x + 1, y + 2)
        if m[y + 1, x + 1]:
            nxt.setdefault(b, []).append(a)
        else:
            nxt.setdefault(a, []).append(b)
    loops = []
    while nxt:
        start = next(iter(nxt))
        p = start
        loop = [p]
        while True:
            q = nxt[p].pop()
            if not nxt[p]:
                del nxt[p]
            if q == start:
                break
            loop.append(q)
            p = q
            if p not in nxt:
                break
        if len(loop) > 8:
            loops.append(np.array(loop, np.float32) - 1)
    return loops


def simplify(pts, eps):
    """Douglas-Peucker on a closed loop, the scissors: long straight cuts."""
    pts = np.asarray(pts)
    n = len(pts)
    if n < 4:
        return pts
    far = int(np.argmax(((pts - pts[0]) ** 2).sum(1)))

    def dp(a, b):
        if b <= a + 1:
            return []
        p, q = a_pts[a], a_pts[b]
        seg = q - p
        l2 = float((seg ** 2).sum()) + 1e-9
        rel = a_pts[a + 1:b] - p
        t = np.clip((rel @ seg) / l2, 0, 1)
        d = ((rel - t[:, None] * seg) ** 2).sum(1)
        i = int(np.argmax(d))
        if d[i] <= eps * eps:
            return []
        k = a + 1 + i
        return dp(a, k) + [k] + dp(k, b)

    a_pts = np.concatenate([pts, pts[:1]])
    sys.setrecursionlimit(20000)
    idx = [0] + dp(0, far) + [far] + dp(far, n)
    return a_pts[idx]


def ca_trace():
    """Real CA coordinates (Angstrom) and pLDDT/100 from the AlphaFold DB v6 model."""
    xyz, b = [], []
    for ln in open(ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"):
        if ln.startswith("ATOM") and ln[12:16].strip() == "CA":
            xyz.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            b.append(float(ln[60:66]) / 100)
    return np.array(xyz), np.array(b)


def arc(cx, cy, rx, ry, a0, a1, n=24):
    t = np.radians(np.linspace(a0, a1, n))
    return [(cx + rx * np.cos(v), cy + ry * np.sin(v)) for v in t]


# Monoline skeletons of the five characters, unit box, y down. Drawn here, so no font is copied.
STROKES = {
    "C": [arc(0.5, 0.5, 0.46, 0.5, -48, -312, 40)],
    "D": [[(0.08, 0.0), (0.08, 1.0)], [(0.08, 0.0), (0.34, 0.0)] + arc(0.36, 0.5, 0.52, 0.5, -90, 90, 30) + [(0.08, 1.0)]],
    "K": [[(0.08, 0.0), (0.08, 1.0)], [(0.82, 0.0), (0.08, 0.6)], [(0.33, 0.4), (0.88, 1.0)]],
    "2": [arc(0.48, 0.3, 0.4, 0.3, -170, 40, 26) + [(0.05, 1.0), (0.92, 1.0)]],
    "0": [arc(0.48, 0.5, 0.42, 0.5, 0, 360, 48)],
}
ADV = {"C": 1.02, "D": 1.04, "K": 0.98, "2": 1.0, "0": 1.0}
