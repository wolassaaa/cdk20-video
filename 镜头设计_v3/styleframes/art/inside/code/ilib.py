"""HKBU SCIE1007 coursework science video. Direction inside: shared painter for the F frames.
Molecular-illustration method, in numpy and PIL only: flat colour, ink outline, depth fades into the dark, real atoms stay detailed and schematic shapes stay plain.
Fonts (SIL OFL, Google Fonts): Inter Tight, Instrument Serif, Martian Mono."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
OUT = ROOT / "styleframes/art/inside/stills"
WORK = ROOT / "styleframes/art/inside/_work"
FONTS = ROOT / "styleframes/S1/v2/_code/s110/fonts"
PDB = ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
CONF = ROOT / "assets/alphafold/AF-Q8IZL9-F1-confidence_v6.json"
SURF = ROOT / "styleframes/S2plus/_work/cdk20_surface.npz"
W, H = 1920, 1080


def hx(s):
    return np.array([int(s[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


RED, DEEP, KLEIN, BLUE, BONE, BLACK, WHITE = hx("#E8190F"), hx("#9A0E08"), hx("#002FA7"), hx("#1F3BFF"), hx("#EDEBE4"), np.zeros(3, np.float32), np.ones(3, np.float32)
NIGHT = KLEIN * .16      # the deep ground: Klein blue on its way to black


def rgb8(c):
    return tuple(int(round(float(x) * 255)) for x in c)


# ---------- type ----------
def sans(size, wght=500):
    f = ImageFont.truetype(str(FONTS / "InterTight.ttf"), size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def serif(size):
    return ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), size)


def mono(size, wght=500):
    f = ImageFont.truetype(str(FONTS / "MartianMono.ttf"), size)
    try:
        ax = f.get_variation_axes()
        f.set_variation_by_axes([wght if b"eight" in (a.get("name") or b"") else a["default"] for a in ax])
    except Exception:
        pass
    return f


def text(im, xy, s, font, fill=BONE, anchor="la", min_px=36, **kw):
    assert font.size >= min_px, (s, font.size)
    ImageDraw.Draw(im).text(xy, s, fill=rgb8(fill), font=font, anchor=anchor, **kw)


def to_pil(rgb):
    return Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8))


def from_pil(im):
    return np.asarray(im.convert("RGB"), np.float32) / 255


def save(im, name):
    OUT.mkdir(exist_ok=True)
    p = OUT / name
    (im if isinstance(im, Image.Image) else to_pil(im)).save(p)
    print("saved", p, Image.open(p).size)


# ---------- evidence tags: four kinds told apart by line, never by colour alone ----------
def _dash(d, a, b, on, off, fill, width):
    a, b = np.array(a, float), np.array(b, float)
    L = np.linalg.norm(b - a)
    u = (b - a) / L
    t = 0
    while t < L:
        p = a + u * t
        q = a + u * min(t + on, L)
        d.line([tuple(p), tuple(q)], fill=fill, width=width)
        t += on + off


def tag(im, xy, s, kind, size=30, fg=BONE, bg=None, anchor="l", font=None):
    """kind: measured = solid filled block. predicted = dashed outline. ours = hollow single line. schematic = dotted outline, round ends.
    bg, when given, fills the plate first so the words hold over the crowd."""
    d = ImageDraw.Draw(im)
    f = font or mono(size)
    tw = d.textlength(s, font=f)
    px, py = round(size * .75), round(size * .55)
    w, h = tw + 2 * px, size * 1.05 + 2 * py
    x, y = xy
    if anchor == "r":
        x -= w
    elif anchor == "m":
        x -= w / 2
    x0, y0, x1, y1 = x, y, x + w, y + h
    c = rgb8(fg)
    if bg is not None:
        d.rounded_rectangle((x0, y0, x1, y1), radius=h / 2 if kind == "schematic" else 2, fill=rgb8(bg))
    if kind == "measured":
        d.rectangle((x0, y0, x1, y1), fill=c)
        c2 = rgb8(BLACK)
    else:
        c2 = c
        if kind == "ours":
            d.rectangle((x0, y0, x1, y1), outline=c, width=3)
        elif kind == "predicted":
            for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                _dash(d, a, b, 16, 10, c, 3)
        elif kind == "schematic":
            r = h / 2
            pts = []
            per = 2 * (w - 2 * r) + 2 * np.pi * r
            n = int(per / 11)
            for i in range(n):
                t = i / n * per
                if t < w - 2 * r:
                    pts.append((x0 + r + t, y0))
                elif t < w - 2 * r + np.pi * r:
                    a = (t - (w - 2 * r)) / r
                    pts.append((x1 - r + r * np.sin(a), y0 + r - r * np.cos(a)))
                elif t < 2 * (w - 2 * r) + np.pi * r:
                    pts.append((x1 - r - (t - (w - 2 * r) - np.pi * r), y1))
                else:
                    a = (t - 2 * (w - 2 * r) - np.pi * r) / r
                    pts.append((x0 + r - r * np.sin(a), y0 + r + r * np.cos(a)))
            for p in pts:
                d.ellipse((p[0] - 2.2, p[1] - 2.2, p[0] + 2.2, p[1] + 2.2), fill=c)
    d.text((x + px, y + py), s, fill=c2, font=f, anchor="la")
    return (x0, y0, x1, y1)


def leader(im, a, b, col=BONE, width=3, dot=True, case=None):
    """Thin line and an end dot. case draws a dark underlay first, so it holds across light shapes."""
    d = ImageDraw.Draw(im)
    if case is not None:
        d.line([tuple(a), tuple(b)], fill=rgb8(case), width=width + 6)
        d.ellipse((b[0] - 11, b[1] - 11, b[0] + 11, b[1] + 11), fill=rgb8(case))
    d.line([tuple(a), tuple(b)], fill=rgb8(col), width=width)
    if dot:
        d.ellipse((b[0] - 7, b[1] - 7, b[0] + 7, b[1] + 7), fill=rgb8(col))


# ---------- blur ----------
def gblur(a, s):
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gblur(a[..., i], s) for i in range(a.shape[2])], -1)
    p = int(3 * s) + 2
    A = np.pad(a, p, mode="edge")
    fy = np.fft.fftfreq(A.shape[0])[:, None]
    fx = np.fft.rfftfreq(A.shape[1])[None, :]
    G = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(A) * G, s=A.shape)[p:-p, p:-p].astype(np.float32)


def box(x0, y0, x1, y1, soft=60):
    m = np.zeros((H, W), np.float32)
    m[int(y0):int(y1), int(x0):int(x1)] = 1
    return gblur(m, soft)


def disc(cx, cy, r, soft=60):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return gblur(((xx - cx) ** 2 + (yy - cy) ** 2 < r * r).astype(np.float32), soft)


# ---------- the crowd: plain flat shapes, nothing here is a real structure ----------
def _shape(d, x, y, kind, s, ang, fill, line, lw, ss):
    """Circle, capsule or bent bean. Flat colour, round ends, no atoms, so nobody takes it for a structure."""
    ca, sa = np.cos(ang), np.sin(ang)
    if kind == 0:
        segs = [((x, y), (x, y))]
        r = s
    elif kind == 1:
        segs = [((x - ca * s, y - sa * s), (x + ca * s, y + sa * s))]
        r = s * .62
    else:
        mx, my = x - sa * s * .5, y + ca * s * .5
        segs = [((x - ca * s, y - sa * s), (mx, my)), ((mx, my), (x + ca * s, y + sa * s))]
        r = s * .56
    for pad, col in ((lw, line), (0, fill)):
        if col is None:
            continue
        rr = (r + pad) * ss
        for a, b in segs:
            ax, ay, bx, by = a[0] * ss, a[1] * ss, b[0] * ss, b[1] * ss
            d.ellipse((ax - rr, ay - rr, ax + rr, ay + rr), fill=col)
            d.ellipse((bx - rr, by - rr, bx + rr, by + rr), fill=col)
            if (ax, ay) != (bx, by):
                d.line([(ax, ay), (bx, by)], fill=col, width=int(2 * rr))


LAYERS = (  # size, spacing, colour, outline
    (34, 62, KLEIN * .34, None),
    (42, 74, KLEIN * .55, BLACK),
    (54, 102, KLEIN * .72, BLACK),
)


def crowd(seed=1, layers=LAYERS, ground=NIGHT, w=W, h=H, ss=2, keep=None):
    """Packed scene of plain shapes, far to near. keep(x, y) -> False leaves a hole in the crowd."""
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (w * ss, h * ss), rgb8(ground))
    d = ImageDraw.Draw(im)
    for (size, gap, col, line) in layers:
        for j, y in enumerate(np.arange(-size, h + size, gap * .87)):
            for x in np.arange(-size + (j % 2) * gap / 2, w + size, gap):
                px, py = x + r.normal(0, gap * .26), y + r.normal(0, gap * .26)
                if keep is not None and not keep(px, py):
                    continue
                tint = r.uniform(.82, 1.12)
                c = rgb8(np.clip(col * tint, 0, 1))
                _shape(d, px, py, r.integers(0, 3), size * r.uniform(.55, 1.05), r.uniform(0, 6.28), c, rgb8(line) if line is not None else None, 3.2, ss)
    im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def dim(rgb, mask, amt=.8, col=NIGHT):
    m = (mask * amt)[..., None]
    return rgb * (1 - m) + col * m


# ---------- real atoms ----------
def read_pdb(path=PDB):
    xyz, name, resi = [], [], []
    for l in open(path):
        if l.startswith("ATOM"):
            xyz.append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
            name.append(l[12:16].strip())
            resi.append(int(l[22:26]))
    return np.array(xyz, np.float32), np.array(name), np.array(resi)


def rotm(ax, ay, az):
    a, b, c = np.radians([ax, ay, az])
    X = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Z = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return (Z @ X @ Y).astype(np.float32)


def spheres(V, rad, scale, cx, cy, w=W, h=H, ss=2, clip=None, Z=None, Nn=None, I=None, id0=0):
    """Sphere impostors with a z-buffer. V is camera space in Angstrom, x right, y up, z to the viewer. clip keeps z below the cut plane and leaves a flat face."""
    if Z is None:
        Z = np.full((h * ss, w * ss), -1e6, np.float32)
        Nn = np.zeros((h * ss, w * ss, 3), np.float32)
        I = -np.ones((h * ss, w * ss), np.int32)
    for i in range(len(V)):
        r = rad[i] * scale * ss
        x, y = (cx + V[i, 0] * scale) * ss, (cy - V[i, 1] * scale) * ss
        x0, x1, y0, y1 = int(max(0, x - r)), int(min(w * ss, x + r + 2)), int(max(0, y - r)), int(min(h * ss, y + r + 2))
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = (xx - x) / r, (yy - y) / r
        q = 1 - dx * dx - dy * dy
        g = q > 0
        nz = np.sqrt(np.clip(q, 0, 1))
        zz = V[i, 2] + nz * rad[i]
        if clip is not None:
            g = g & (V[i, 2] - nz * rad[i] < clip)
            cut = zz > clip
            zz = np.where(cut, clip, zz)
            nn = np.stack([np.where(cut, 0, dx), np.where(cut, 0, -dy), np.where(cut, 1, nz)], -1)
        else:
            nn = np.stack([dx, -dy, nz], -1)
        zs = Z[y0:y1, x0:x1]
        m = g & (zz > zs)
        zs[m] = zz[m]
        Nn[y0:y1, x0:x1][m] = nn[m]
        I[y0:y1, x0:x1][m] = i + id0
    return Z, Nn, I


def edges(Z, I, group, ss=2, jump=1.0, grow=2):
    """Ink line where the depth jumps or the group changes. group[id] is the molecule or chain piece."""
    G = np.where(I >= 0, group[np.maximum(I, 0)], -1)
    e = np.zeros(Z.shape, bool)
    e[:-1] |= (G[:-1] != G[1:]) | (np.abs(Z[:-1] - Z[1:]) > jump)
    e[:, :-1] |= (G[:, :-1] != G[:, 1:]) | (np.abs(Z[:, :-1] - Z[:, 1:]) > jump)
    for _ in range(grow):
        f = e.copy()
        f[1:] |= e[:-1]
        f[:-1] |= e[1:]
        f[:, 1:] |= e[:, :-1]
        f[:, :-1] |= e[:, 1:]
        e = f
    return e


def down(a, ss=2):
    h, w = a.shape[0] // ss, a.shape[1] // ss
    return a.reshape(h, ss, w, ss, *a.shape[2:]).mean((1, 3))


def spline(P, n=8):
    """Catmull-Rom through points, n samples per span. Returns points and the source index as a float."""
    P = np.vstack([P[0], P, P[-1]])
    out, idx = [], []
    for i in range(1, len(P) - 2):
        for t in np.arange(n) / n:
            a, b, c, d = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
            idx.append(i - 1 + t)
    out.append(P[-2])
    idx.append(len(P) - 3)
    return np.array(out, np.float32), np.array(idx, np.float32)


# ---------- the road: the film's map, drawn as a chain of beads so it lives in this world ----------
def road(rgb, xs, y, state, flow_to, r_st=34, r_b=9, gap=26, wave=10, x_start=None, x_end=None):
    """xs station centres. state per station: done, half, todo. flow_to is the x where the red stops. Returns a float image."""
    ss = 3
    x_start = xs[0] - 120 if x_start is None else x_start
    x_end = xs[-1] + 60 if x_end is None else x_end
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).resize((W * ss, H * ss), Image.BICUBIC)
    d = ImageDraw.Draw(im)
    yw = lambda x: y + wave * np.sin((x - xs[0]) / 140)
    for x in np.arange(x_start, x_end, gap):
        yy_ = yw(x)
        if min(abs(x - s) for s in xs) < r_st + gap * .5:
            continue
        lit = x < flow_to
        o = (r_b + 3) * ss
        d.ellipse(((x * ss) - o, yy_ * ss - o, x * ss + o, yy_ * ss + o), fill=(0, 0, 0))
        q = r_b * ss
        if lit:
            d.ellipse((x * ss - q, yy_ * ss - q, x * ss + q, yy_ * ss + q), fill=rgb8(RED))
        else:
            d.ellipse((x * ss - q, yy_ * ss - q, x * ss + q, yy_ * ss + q), fill=rgb8(NIGHT), outline=rgb8(BONE), width=2 * ss)
    for x, st in zip(xs, state):
        yy_ = yw(x)
        o = (r_st + 5) * ss
        d.ellipse((x * ss - o, yy_ * ss - o, x * ss + o, yy_ * ss + o), fill=(0, 0, 0))
        q = r_st * ss
        box_ = (x * ss - q, yy_ * ss - q, x * ss + q, yy_ * ss + q)
        d.ellipse(box_, fill=rgb8(NIGHT))
        if st == "todo":                      # not reached: dashed ring, the script's own line for "not reported"
            for k in range(14):
                d.arc(box_, k * 360 / 14, k * 360 / 14 + 15, fill=rgb8(BONE), width=3 * ss)
        else:
            d.ellipse(box_, outline=rgb8(BONE), width=3 * ss)
        if st == "done":
            d.ellipse(box_, fill=rgb8(RED), outline=rgb8(BONE), width=3 * ss)
        elif st == "half":
            d.pieslice(box_, 90, 270, fill=rgb8(RED))
            d.ellipse(box_, outline=rgb8(BONE), width=3 * ss)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
