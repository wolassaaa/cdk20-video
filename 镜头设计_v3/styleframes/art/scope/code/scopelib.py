"""HKBU SCIE1007 coursework science video. Scope direction: shared drawing kit. Round field, evidence rings, labels, scale bars.

The ring of each field says what kind of evidence is inside, by line type, not colour:
  measured  solid ring     predicted  dotted ring     our docking  double ring     schematic  dashed ring
Colours stay on the brief's palette. Red and blue never add: where they would overlap, the front one replaces the other, so purple cannot appear.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
SCOPE = Path(__file__).resolve().parent.parent
WORK = SCOPE / "_work"
STILLS = SCOPE / "stills"
S1F = SCOPE.parent.parent / "S1/v2/_code/s110/fonts"


def c(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


RED, DARKRED, KLEIN, BLUE, BONE = c("#E8190F"), c("#9A0E08"), c("#002FA7"), c("#1F3BFF"), c("#EDEBE4")
SS = 3


def sans(size, weight=500):
    f = ImageFont.truetype(str(S1F / "InterTight.ttf"), size)
    f.set_variation_by_axes([weight])
    return f


def mono(size, weight=400):
    f = ImageFont.truetype(str(S1F / "MartianMono.ttf"), size)
    ax = f.get_variation_axes()
    v = []
    for a in ax:
        nm = a["name"].decode() if isinstance(a["name"], bytes) else str(a["name"])
        v.append(weight if "eight" in nm else a["default"])
    f.set_variation_by_axes(v)
    return f


def gblur(a, s):
    p = int(3 * s) + 2
    pad = ((p, p), (p, p)) + ((0, 0),) * (a.ndim - 2)
    A = np.pad(a, pad, mode="constant")
    fy = np.fft.fftfreq(A.shape[0])[:, None]
    fx = np.fft.rfftfreq(A.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    if a.ndim == 3:
        g = g[..., None]
    r = np.fft.irfft2(np.fft.rfft2(A, axes=(0, 1)) * g, s=A.shape[:2], axes=(0, 1))
    return r[p:-p, p:-p].astype(np.float32)


def blank():
    return np.zeros((H, W, 3), np.float32)


def over(rgb, col, a):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def layer():
    im = Image.new("L", (W * SS, H * SS), 0)
    return im, ImageDraw.Draw(im)


def done(im):
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def text(rgb, s, xy, font, col=BONE, anchor="ls", halo=True):
    """Draws at 3x and shrinks, so edges stay clean. A dark halo keeps text legible over a field."""
    f = font if isinstance(font, tuple) else (sans, font, 500)
    fn, size, wt = f
    big = fn(size * SS, wt)
    im, d = layer()
    d.text((xy[0] * SS, xy[1] * SS), s, font=big, fill=255, anchor=anchor)
    a = done(im)
    if halo:
        rgb = rgb * (1 - np.clip(gblur(a, 5) * 2.4, 0, 1)[..., None] * .9)
    return over(rgb, col, a)


def width(s, font):
    fn, size, wt = font if isinstance(font, tuple) else (sans, font, 500)
    return fn(size * SS, wt).getlength(s) / SS


def ring(rgb, cx, cy, r, kind, col=BONE, w=3.0, alpha=1.0):
    """Evidence ring: solid, dotted, dashed, double, or faint for nothing to show."""
    im, d = layer()
    k = SS
    if kind == "solid":
        d.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), outline=255, width=int(w * k))
    elif kind == "double":
        for q in (0, 11):
            rr = r + q
            d.ellipse(((cx - rr) * k, (cy - rr) * k, (cx + rr) * k, (cy + rr) * k), outline=255, width=int(w * .8 * k))
    elif kind == "dotted":
        n = int(2 * np.pi * r / 16)
        for i in range(n):
            t = 2 * np.pi * i / n
            x, y = cx + (r + 1) * np.cos(t), cy + (r + 1) * np.sin(t)
            q = w * .95
            d.ellipse(((x - q) * k, (y - q) * k, (x + q) * k, (y + q) * k), fill=255)
    elif kind == "dashed":
        n = int(2 * np.pi * r / 44)
        for i in range(n):
            a0 = 360 * i / n
            d.arc(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), a0, a0 + 360 / n * .58, fill=255, width=int(w * k))
    elif kind == "faint":
        d.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), outline=255, width=int(max(1, w * .6) * k))
    return over(rgb, col, done(im) * alpha)


def disc(cx, cy, r, soft=1.2):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.clip((r - np.hypot(xx - cx, yy - cy)) / soft + .5, 0, 1)


def illum(cx, cy, r):
    """Even round illumination that falls off gently to the stop. Smooth, so it cannot shimmer."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    q = np.hypot(xx - cx, yy - cy) / r
    return (1 - .34 * np.clip(q, 0, 1) ** 4) * disc(cx, cy, r)


def line(rgb, pts, col=BONE, w=2.0, alpha=1.0):
    im, d = layer()
    d.line([(x * SS, y * SS) for x, y in pts], fill=255, width=int(w * SS), joint="curve")
    return over(rgb, col, done(im) * alpha)


def dot(rgb, x, y, r, col=BONE):
    return over(rgb, col, disc(x, y, r, 1.0))


def small_ring(rgb, cx, cy, r, kind, col=BONE):
    im, d = layer()
    k = SS
    box = lambda q: ((cx - q) * k, (cy - q) * k, (cx + q) * k, (cy + q) * k)
    if kind == "solid":
        d.ellipse(box(r), outline=255, width=int(2.6 * k))
    elif kind == "double":
        d.ellipse(box(r), outline=255, width=int(2 * k))
        d.ellipse(box(r - 7), outline=255, width=int(2 * k))
    elif kind == "dotted":
        for i in range(10):
            t = 2 * np.pi * i / 10
            x, y = cx + r * np.cos(t), cy + r * np.sin(t)
            d.ellipse(((x - 2.2) * k, (y - 2.2) * k, (x + 2.2) * k, (y + 2.2) * k), fill=255)
    elif kind == "dashed":
        for i in range(6):
            d.arc(box(r), 60 * i, 60 * i + 34, fill=255, width=int(2.4 * k))
    return over(rgb, col, done(im))


def tag(rgb, x, y, kind, s, anchor="l", col=BONE, size=25):
    """Evidence tag: a small sample of the ring, then its word. y is the text baseline."""
    f = (mono, size, 400)
    tw = width(s, f)
    x0 = x if anchor == "l" else x - tw - 58
    rgb = small_ring(rgb, x0 + 20, y - 10, 18, kind, col)
    return text(rgb, s, (x0 + 58, y), f, col, halo=False)


def scalebar(rgb, x, y, px, s, col=BONE):
    """px comes from the orthographic render: real length times the render's px per unit. Nothing is eyeballed."""
    im, d = layer()
    k = SS
    d.rectangle((x * k, (y - 3) * k, (x + px) * k, (y + 3) * k), fill=255)
    rgb = over(rgb, col, done(im))
    return text(rgb, s, (x + px / 2, y - 16), (sans, 36, 500), col, anchor="ms", halo=True)


def clean(rgb, name):
    """Keeps the picture before labels go on, for the colour script."""
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(WORK / ("clean_" + name + ".png"))


def save(rgb, name):
    STILLS.mkdir(exist_ok=True)
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(STILLS / name)
    print("saved", name)


def smooth_norm(n, a):
    """Undo edge premultiply on a pass."""
    return n / np.maximum(a, 1e-3)[..., None]


def purple_check(rgb):
    """Share of pixels that drift to purple or green. Should stay near zero."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    p = (r > .25) & (b > .25) & (g < .45 * np.minimum(r, b))
    gr = (g > .2) & (g > r * 1.15) & (g > b * 1.15)
    print("purple px", int(p.sum()), "green px", int(gr.sum()))


STATIONS = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"]


def minimap(rgb, x, y, lit, before=False, gap=46):
    """The road map at thumbnail size: six stops, no words. lit = stops already reached. before = the red stops just short of the next stop."""
    n = 6
    rgb = line(rgb, [(x, y), (x + gap * (n - 1), y)], BONE, 2, .45)
    end = x + gap * (lit - 1) if lit else x
    if lit or before:
        x0 = x - gap * .7
        x1 = end + (gap * .62 if before and lit else 0) - (gap * .3 if before and not lit else 0)
        rgb = line(rgb, [(x0, y), (x1, y)], RED, 4)
    for i in range(n):
        cx = x + gap * i
        rgb = over(rgb, (0, 0, 0), disc(cx, y, 11))
        rgb = small_ring(rgb, cx, y, 9, "solid", BONE)
        if i < lit:
            rgb = over(rgb, RED, disc(cx, y, 9.5))
    return rgb


def ruler(rgb, x, y, px_step, n, label, col=BONE):
    """Measuring scale: n divisions, each px_step long, label says what one whole ruler or one division is. Steps come straight from the orthographic render."""
    pts = [(x, y), (x + px_step * n, y)]
    rgb = line(rgb, pts, col, 3)
    for i in range(n + 1):
        h = 14 if i in (0, n) else 8
        rgb = line(rgb, [(x + px_step * i, y - h), (x + px_step * i, y)], col, 2.4)
    return text(rgb, label, (x + px_step * n / 2, y - 24), (sans, 36, 500), col, anchor="ms")


def fluor(mask, lo, hi, rim_px=7, fill=.42):
    """Flat shape shown the same way as the real models: bright at the wall, dim inside. Returns (colour, alpha)."""
    inner = gblur(mask, rim_px)
    rim = np.clip((1 - inner) * 2.2, 0, 1) * mask
    t = np.clip(fill + (1 - fill) * rim, 0, 1)[..., None]
    return lo + (hi - lo) * t, mask


def poly(pts):
    im, d = layer()
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return done(im)


def tick(rgb, x, y, s=44, col=BONE, w=7):
    return line(rgb, [(x - s, y), (x - s * .25, y + s * .72), (x + s, y - s * .75)], col, w)


def cross(rgb, x, y, s=38, col=BONE, w=7):
    rgb = line(rgb, [(x - s, y - s), (x + s, y + s)], col, w)
    return line(rgb, [(x - s, y + s), (x + s, y - s)], col, w)
