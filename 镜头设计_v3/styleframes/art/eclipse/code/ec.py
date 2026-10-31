"""HKBU SCIE1007 coursework science video. Shared helpers for the eclipse direction: one colour band, one text face, four evidence glyphs. Every frame is built as band position 0..1 and only coloured at the very end."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art")
sys.path.insert(0, str(ART / "scouts/a/code"))
import kit  # noqa: E402  read-only use of the real mesh projector

W, H = 1920, 1080
STILLS = ART / "eclipse/stills"
WORK = ART / "eclipse/_work"
WORK.mkdir(exist_ok=True)
SANS = "C:/Windows/Fonts/NotoSansSC-VF.ttf"  # Noto Sans SC, SIL OFL

BAND = [(0.00, "#000000"), (0.10, "#1c0203"), (0.22, "#4c0508"), (0.36, "#9e0b0e"), (0.48, "#de1a10"),
        (0.60, "#f8520a"), (0.72, "#ff9400"), (0.84, "#ffc81e"), (0.93, "#ffee8c"), (1.00, "#fffcea")]


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def band(t):
    """The only colour map in the film."""
    t = np.clip(t, 0, 1)
    pos = [p for p, _ in BAND]
    c = np.stack([hexc(s) for _, s in BAND])
    return np.stack([np.interp(t, pos, c[:, i]) for i in range(3)], -1).astype(np.float32)


# second rail. Pearl, the corona's own colour, belongs to the machine and to nothing else
COLD = [(0.00, "#000000"), (0.10, "#0a0e12"), (0.25, "#1d2730"), (0.45, "#4a5c6a"), (0.65, "#8fa3b0"),
        (0.82, "#c8d6dd"), (0.93, "#e8eff2"), (1.00, "#f8fbfc")]
RED_TOP = 0.50      # the world stops at red. Above this on the warm rail is people's light, nothing else may go there


def cold(t):
    t = np.clip(t, 0, 1)
    pos = [p for p, _ in COLD]
    c = np.stack([hexc(s) for _, s in COLD])
    return np.stack([np.interp(t, pos, c[:, i]) for i in range(3)], -1).astype(np.float32)


def rails(t, ai=None):
    """Warm rail where ai is 0, pearl rail where ai is 1."""
    rgb = band(t)
    if ai is None:
        return rgb
    return rgb * (1 - ai[..., None]) + cold(t) * ai[..., None]


def expose(L, k=1.0):
    return 1 - np.exp(-np.maximum(L, 0) * k)


def grid(w=W, h=H):
    return np.mgrid[0:h, 0:w].astype(np.float32)


def blur(a, s):
    return kit.fft_blur(a, s) if s > 0 else a


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(seed, scale, shape=(H, W), slope=2.0):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(shape)
    fy, fx = np.fft.fftfreq(shape[0])[:, None], np.fft.rfftfreq(shape[1])[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    amp = 1 / np.maximum(f, 1 / scale) ** (slope / 2 + 0.5)
    r = np.fft.irfft2(np.fft.rfft2(n) * amp, s=shape)
    return ((r - r.min()) / (r.max() - r.min())).astype(np.float32)


def sample(a, sx, sy):
    h, w = a.shape[:2]
    ok = (sx >= 0) & (sx <= w - 1) & (sy >= 0) & (sy <= h - 1)
    x, y = np.clip(sx, 0, w - 1.001), np.clip(sy, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - x0, y - y0
    v = (a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy) + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy
    return v * ok


def face(size, weight=700):
    f = ImageFont.truetype(SANS, size)
    f.set_variation_by_axes([weight])
    return f


def text(s, size, xy, weight=700, anchor="lm", tracking=0):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    f = face(size, weight)
    if not tracking:
        d.text(xy, s, 255, font=f, anchor=anchor)
    else:
        adv = [d.textlength(c, font=f) + tracking for c in s]
        x = xy[0] - (sum(adv) - tracking if anchor[0] == "r" else (sum(adv) - tracking) / 2 if anchor[0] == "m" else 0)
        for c, a in zip(s, adv):
            d.text((x, xy[1]), c, 255, font=f, anchor="l" + anchor[1])
            x += a
    return np.asarray(im, np.float32) / 255


def width(s, size, weight=700):
    return ImageDraw.Draw(Image.new("L", (8, 8))).textlength(s, font=face(size, weight))


def put(t, a, val):
    """Write a band value into the frame through coverage a."""
    return t * (1 - a) + val * a


def ring(x, y, cx, cy, r, w):
    return sstep(w / 2 + 0.8, w / 2 - 0.8, np.abs(np.hypot(x - cx, y - cy) - r))


def dashed_ring(x, y, cx, cy, r, w, n):
    a = np.arctan2(y - cy, x - cx)
    return ring(x, y, cx, cy, r, w) * ((np.floor((a + np.pi) / (2 * np.pi) * n * 2) % 2) == 0)


def box(x, y, x0, y0, x1, y1):
    return sstep(-0.8, 0.8, x - x0) * sstep(0.8, -0.8, x - x1) * sstep(-0.8, 0.8, y - y0) * sstep(0.8, -0.8, y - y1)


def frame_line(x, y, x0, y0, x1, y1, w, dash=0):
    """Rectangle outline. dash > 0 makes it a dashed line, the mark of our own work."""
    o = box(x, y, x0, y0, x1, y1) * (1 - box(x, y, x0 + w, y0 + w, x1 - w, y1 - w))
    if dash:
        o = o * (((x + y) // dash) % 2 == 0)
    return o


def glyph(kind, x, y, cx, cy, r):
    """Evidence marks, one eclipse phase each, told apart by shape alone.
    measured: solid disc. predicted: thin full ring, only an outline. docked: dashed ring. schematic: hatched half disc."""
    d = np.hypot(x - cx, y - cy)
    if kind == "measured":
        return sstep(r + 0.8, r - 0.8, d)
    if kind == "predicted":
        return ring(x, y, cx, cy, r - 2, 4)
    if kind == "docked":
        return dashed_ring(x, y, cx, cy, r - 2, 5, 7)
    h = ((np.floor((x + y) / 6) % 2) == 0) * sstep(r + 0.8, r - 0.8, d) * (x < cx)
    return np.maximum(h, ring(x, y, cx, cy, r - 2, 4))


def tag(t, x, y, kind, s, x0, cy, size=38, weight=700, ink=1.0, ground=None):
    """Evidence tag: shape of the plate and the glyph both carry the kind, colour is not needed."""
    tw = width(s, size, weight)
    pad, r = 24, size * 0.46
    x1 = x0 + pad * 2 + r * 2 + 18 + tw
    y0, y1 = cy - size * 0.95, cy + size * 0.95
    if kind == "measured":      # solid slab
        t = put(t, box(x, y, x0, y0, x1, y1), ink)
        fg = ground if ground is not None else 0.0
        t = put(t, glyph(kind, x, y, x0 + pad + r, cy, r), fg)
        t = put(t, text(s, size, (x0 + pad + 2 * r + 18, cy), weight), fg)
        return t
    if ground is not None:
        t = put(t, box(x, y, x0, y0, x1, y1), ground)
    t = put(t, frame_line(x, y, x0, y0, x1, y1, 4 if kind == "docked" else 2, dash=12 if kind == "docked" else 0), ink)
    t = put(t, glyph(kind, x, y, x0 + pad + r, cy, r), ink)
    t = put(t, text(s, size, (x0 + pad + 2 * r + 18, cy), weight), ink)
    return t


def tag_box(x, y, s, x0, cy, size=38, weight=700):
    """Coverage of a tag plate, for marking it on the pearl rail."""
    r = size * 0.46
    return box(x, y, x0, cy - size * 0.95, x0 + 48 + r * 2 + 18 + width(s, size, weight), cy + size * 0.95)


def person(x, y, cx, base, h):
    """Tiny standing figure, coverage mask. Head, shoulders, two legs, no detail."""
    hr = h * 0.075
    top = base - h
    head = sstep(0.8, -0.8, np.hypot(x - cx, y - (top + hr)) - hr)
    u = (y - (top + hr * 2.1)) / (h - hr * 2.1)
    torso = np.where(u < 0.46, h * (0.13 - 0.06 * np.clip(u / 0.46, 0, 1) ** 2), h * 0.1)
    legs_gap = sstep(0.46, 0.62, u) * h * 0.022
    a = sstep(0.8, -0.8, np.abs(x - cx) - torso) * (u > 0) * (u < 1)
    a = a * (1 - sstep(0.8, -0.8, np.abs(x - cx) - legs_gap) * (u > 0.5))
    return np.maximum(head, a)


def save(t, name, ai=None):
    rgb = rails(t, ai)
    n = np.random.default_rng(3).random(t.shape + (1,), dtype=np.float32) - 0.5  # one static LSB so the long gradients do not band
    Image.fromarray((np.clip(rgb + n / 255, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILLS / name)
    print("saved", name)
