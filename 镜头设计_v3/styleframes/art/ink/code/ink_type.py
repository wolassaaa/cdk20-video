"""HKBU SCIE1007 coursework science video. Ink direction: type, leader lines, evidence tags and the road, shared by all six test frames.

Coordinates are 1080p pixels. Text goes through a 2x mask so small sizes stay crisp. Fonts are SIL OFL, from Google Fonts: Archivo Black, Instrument Serif, Martian Mono.
Four kinds of evidence are told apart by mark, never by colour alone:
  measured = solid block, predicted = hatched, our re-docking = dotted outline, schematic = double outline.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import engrave as E

F = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/fonts/"
ARCHIVO, SERIF, ITALIC, MONO = F + "ArchivoBlack-Regular.ttf", F + "InstrumentSerif-Regular.ttf", F + "InstrumentSerif-Italic.ttf", F + "MartianMono.ttf"


def _font(path, size):
    return ImageFont.truetype(path, int(round(size * 2)))


def width(s, path, size):
    return _font(path, size).getlength(s) / 2


def text(img, x, y, s, path=SERIF, size=44, col=E.BONE, anchor="ls", halo=0):
    """Draw s with its baseline at y. anchor as in PIL: ls left, ms middle, rs right."""
    f = _font(path, size)
    l, t, r, b = f.getbbox(s, anchor="ls")
    pad = 8 + int(halo) * 2
    W, H = r - l + 2 * pad, b - t + 2 * pad
    W += W % 2
    H += H % 2
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((pad - l, pad - t), s, font=f, fill=255, anchor="ls")
    m = m.resize((W // 2, H // 2), Image.BOX)
    a = np.asarray(m, np.float32) / 255
    dx = {"l": 0, "m": -(r - l) / 4, "r": -(r - l) / 2}[anchor[0]]
    px, py = int(round(x + dx + l / 2 - pad / 2)), int(round(y + t / 2 - pad / 2))
    _paste(img, a, px, py, col, halo)
    return (r - l) / 2


def _paste(img, a, px, py, col, halo=0):
    h, w = a.shape
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(px, 0), max(py, 0), min(px + w, W), min(py + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    sub = a[y0 - py:y1 - py, x0 - px:x1 - px]
    if halo:
        g = np.clip(E.blur(sub, halo) * 6, 0, 1)
        img[y0:y1, x0:x1] = E.over(img[y0:y1, x0:x1], g, np.zeros(3))
    img[y0:y1, x0:x1] = E.over(img[y0:y1, x0:x1], sub, np.asarray(col))


def draw(img, fn, col=E.BONE):
    """fn(d) draws on a 2x mask with PIL calls in 2x coordinates; the mask is laid over img in one colour."""
    H, W = img.shape[:2]
    m = Image.new("L", (W * 2, H * 2), 0)
    fn(ImageDraw.Draw(m))
    a = np.asarray(m.resize((W, H), Image.BOX), np.float32) / 255
    img[:] = E.over(img, a, np.asarray(col))


def leader(img, pts, col=E.BONE, w=2.5, dot=6, halo=True):
    """Thin atlas leader with a dot on the structure it names. pts run from the label to the structure."""
    p = [(a * 2, b * 2) for a, b in pts]
    if halo:
        def k(d):
            d.line(p, fill=255, width=int((w + 5) * 2), joint="curve")
            x, y = p[-1]
            d.ellipse((x - dot * 2 - 6, y - dot * 2 - 6, x + dot * 2 + 6, y + dot * 2 + 6), fill=255)
        draw(img, k, np.zeros(3))
    def f(d):
        d.line(p, fill=255, width=int(w * 2), joint="curve")
        x, y = p[-1]
        d.ellipse((x - dot * 2, y - dot * 2, x + dot * 2, y + dot * 2), fill=255)
    draw(img, f, col)


def evidence_mark(img, x, y, kind, s=30, col=E.BONE):
    """A square swatch of the line type, sitting on baseline y."""
    x0, y0, x1, y1 = x * 2, (y - s) * 2, (x + s) * 2, y * 2
    def f(d):
        if kind == "measured":
            d.rectangle((x0, y0, x1, y1), fill=255)
        elif kind == "predicted":
            d.rectangle((x0, y0, x1, y1), outline=255, width=3)
            for k in range(-s * 2, s * 2, 10):
                a = max(x0, x0 + k)
                b = min(x1, x0 + k + s * 2)
                d.line((a, y1 - (a - x0 - k), b, y1 - (b - x0 - k)), fill=255, width=4)
        elif kind == "redocking":
            n = 5
            for i in range(n + 1):
                for px, py in ((x0 + (x1 - x0) * i / n, y0), (x0 + (x1 - x0) * i / n, y1), (x0, y0 + (y1 - y0) * i / n), (x1, y0 + (y1 - y0) * i / n)):
                    d.ellipse((px - 3.5, py - 3.5, px + 3.5, py + 3.5), fill=255)
        elif kind == "schematic":
            d.rectangle((x0, y0, x1, y1), outline=255, width=5)
            d.rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), outline=255, width=3)
    draw(img, f, col)


def tag(img, x, y, kind, s, size=26, col=E.BONE, anchor="l"):
    """Evidence mark plus its words."""
    w = width(s, MONO, size)
    if anchor == "r":
        x = x - w - 44
    evidence_mark(img, x, y + 2, kind, col=col)
    text(img, x + 44, y, s, MONO, size, col)


def road_mini(img, x0, y, gap=66, r=12, lit=0, pre=True, col=E.BONE, ground=None):
    """The six-station road, small. lit is how many stations are done; pre lights the stub before station one."""
    xs = [x0 + 60 + gap * i for i in range(6)]
    def base(d):
        for i in range(5):
            a, b = xs[i], xs[i + 1]
            n = 6
            if i < lit - 1:
                d.line((a * 2, y * 2, b * 2, y * 2), fill=255, width=7)
            else:
                for k in range(n):
                    t0, t1 = (k + 0.2) / n, (k + 0.65) / n
                    d.line(((a + (b - a) * t0) * 2, y * 2, (a + (b - a) * t1) * 2, y * 2), fill=255, width=5)
    draw(img, base, col)
    draw(img, lambda d: [d.ellipse(((x - r - 5) * 2, (y - r - 5) * 2, (x + r + 5) * 2, (y + r + 5) * 2), fill=255) for x in xs], np.zeros(3) if ground is None else ground)
    def rings(d):
        for i, x in enumerate(xs):
            if i < lit:
                d.ellipse(((x - r) * 2, (y - r) * 2, (x + r) * 2, (y + r) * 2), fill=255)
            else:
                d.ellipse(((x - r) * 2, (y - r) * 2, (x + r) * 2, (y + r) * 2), outline=255, width=5)
    draw(img, rings, col)
    def red(d):
        if pre and lit == 0:
            d.line((x0 * 2, y * 2, (xs[0] - r - 8) * 2, y * 2), fill=255, width=12)
            d.ellipse(((x0 - 12) * 2, (y - 12) * 2, (x0 + 12) * 2, (y + 12) * 2), fill=255)
        elif lit:
            x = xs[lit - 1]
            d.ellipse(((x - r - 7) * 2, (y - r - 7) * 2, (x + r + 7) * 2, (y + r + 7) * 2), outline=255, width=6)
    draw(img, red, E.RED)
