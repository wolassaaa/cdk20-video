"""HKBU SCIE1007 coursework science video. Shared kit for the lantern direction: only what the light touches exists.

Four kinds of light carry the four evidence levels, by shape first and colour second.
solid() warm flat light, people and measured results. stripes() cold structured light, AI prediction.
dot_screen() light through a punched plate, our own re-docking. dash() no light at all, chalk, schematic.
Reuses the real-mesh projection in scouts/a/code/kit.py (read only).
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/scouts/a/code")
import kit  # noqa: E402
from kit import Layer, atoms, base_view, fft_blur, noise, project, resize, rot, smooth, view, warp  # noqa: E402,F401

W, H = 1920, 1080
OUT = kit.ROOT / "styleframes/art/lantern/stills"
OUT.mkdir(parents=True, exist_ok=True)
NOTO = "C:/Windows/Fonts/NotoSansSC-VF.ttf"  # SIL OFL

BLACK = np.array((5, 5, 6), np.float32) / 255
AMBER = np.array((255, 168, 66), np.float32) / 255
AMBER_HI = np.array((255, 226, 170), np.float32) / 255
COLD = np.array((214, 240, 255), np.float32) / 255
CHALK = np.array((168, 168, 160), np.float32) / 255

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def noto(size, wt=700):
    f = ImageFont.truetype(NOTO, size)
    f.set_variation_by_axes([wt])
    return f


def blank():
    return np.ones((H, W, 3), np.float32) * BLACK


def lay(c, cov, col):
    return c * (1 - cov[..., None]) + np.asarray(col, np.float32) * cov[..., None]


def add(c, cov, col):
    return c + cov[..., None] * np.asarray(col, np.float32)


def save(rgb, name):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / name)
    print("saved", name)


def tx(s, size, wt, x, y, anchor="ls", track=0.0, w=W, h=H, ss=3):
    """Coverage of a line of text. Plain antialiased, no blur."""
    f = noto(int(size * ss), wt)
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    if track == 0:
        d.text((x * ss, y * ss), s, font=f, fill=255, anchor=anchor)
    else:
        tot = sum(f.getlength(c) for c in s) + track * ss * (len(s) - 1)
        px = x * ss - (tot / 2 if anchor[0] == "m" else tot if anchor[0] == "r" else 0)
        for c in s:
            d.text((px, y * ss), c, font=f, fill=255, anchor="l" + anchor[1])
            px += f.getlength(c) + track * ss
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def tw(s, size, wt):
    return noto(int(size * 3), wt).getlength(s) / 3


def stencil_glyph(ch, size, wt, bridge):
    """One glyph as a real hole in a wall: every enclosed island gets bridges, or it would fall out."""
    f = noto(size, wt)
    pad = int(size * 0.15)
    bb = f.getbbox(ch)
    gw, gh = bb[2] + pad * 2, bb[3] + pad * 2
    im = Image.new("L", (gw, gh), 0)
    ImageDraw.Draw(im).text((pad, pad), ch, font=f, fill=255)
    a = np.asarray(im) > 127
    k = 4
    sm = ~a[::k, ::k]
    h_, w_ = sm.shape
    lab = np.zeros((h_, w_), np.int32)

    def grow(y, x, v):
        st = [(y, x)]
        lab[y, x] = v
        pts = []
        while st:
            cy, cx = st.pop()
            pts.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < h_ and 0 <= nx < w_ and sm[ny, nx] and lab[ny, nx] == 0:
                    lab[ny, nx] = v
                    st.append((ny, nx))
        return np.array(pts)

    grow(0, 0, 1)
    out = a.copy()
    v = 2
    b = bridge // 2
    for y in range(h_):
        for x in range(w_):
            if sm[y, x] and lab[y, x] == 0:
                pts = grow(y, x, v)
                v += 1
                if len(pts) < 6:
                    continue
                cx = int(pts[:, 1].mean() * k)
                for sign, start in ((-1, pts[:, 0].min() * k), (1, pts[:, 0].max() * k)):
                    r = int(start)
                    while 0 <= r < gh and (r == start or abs(r - start) < k * 2 or a[r, cx]):
                        out[r, cx - b:cx + b + 1] = False
                        r += sign
    return out, pad


def stencil(s, size, wt, x, y, bridge=None, gap=0.0, ss=2, w=W, h=H):
    """Stencil word, baseline at y. Returns coverage. Bridges are thick enough to read as metal."""
    bridge = bridge or max(4, int(size * ss * 0.035))
    im = Image.new("L", (w * ss, h * ss), 0)
    f = noto(int(size * ss), wt)
    px = x * ss
    for c in s:
        if c == " ":
            px += f.getlength(" ")
            continue
        g, pad = stencil_glyph(c, int(size * ss), wt, bridge)
        asc = f.getmetrics()[0]
        gim = Image.fromarray((g * 255).astype(np.uint8))
        im.paste(255, (int(px - pad), int(y * ss - asc - pad)), gim)
        px += f.getlength(c) + gap * ss
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def extrude(m, dx, dy, step=2):
    """Hard shafts of light leaving a hole in the wall. Max over shifted copies, no blur."""
    n = int(max(abs(dx), abs(dy)) / step)
    e = m.copy()
    for i in range(1, n + 1):
        sx, sy = int(dx * i / n), int(dy * i / n)
        p = np.zeros_like(m)
        y0, y1 = max(sy, 0), min(H + sy, H)
        x0, x1 = max(sx, 0), min(W + sx, W)
        p[y0:y1, x0:x1] = m[y0 - sy:y1 - sy, x0 - sx:x1 - sx]
        e = np.maximum(e, p)
    return e


def beam(ax, ay, a0, a1, reach=4000):
    """Hard wedge from an apex. Angles in degrees, screen space, y down."""
    p = [(ax, ay)]
    for t in np.linspace(a0, a1, 24):
        p.append((ax + reach * np.cos(np.radians(t)), ay + reach * np.sin(np.radians(t))))
    return Layer(W, H, 2).poly(p).a()


def stripes(phase, width, aa=0.10):
    """Cold structured light: bright rays with black between. phase in periods, width 0..1 of a period."""
    v = np.abs(phase - np.floor(phase) - 0.5) * 2
    return smooth(width - (1 - v), -aa, aa)


def dot_screen(tone, cell=13.0, ang=30.0):
    """Punched-plate light: a fixed grid of round holes. tone 0..1 sets the hole size."""
    a = np.radians(ang)
    u = (xx * np.cos(a) + yy * np.sin(a)) / cell
    v = (-xx * np.sin(a) + yy * np.cos(a)) / cell
    d = np.hypot(u - np.floor(u) - 0.5, v - np.floor(v) - 0.5)
    r = 0.48 * np.sqrt(np.clip(tone, 0, 1))
    return smooth(r - d, -0.05, 0.05) * (tone > 0.01)


def dash(pts, on=16, off=12, width=3, closed=False):
    """Chalk: a dashed path. No light involved."""
    L_ = Layer(W, H, 2)
    pts = [np.array(p, np.float64) for p in pts] + ([np.array(pts[0], np.float64)] if closed else [])
    left, draw = on, True
    for a, b in zip(pts[:-1], pts[1:]):
        seg = np.linalg.norm(b - a)
        u = (b - a) / max(seg, 1e-6)
        s = 0.0
        while s < seg:
            d_ = min(left, seg - s)
            if draw:
                L_.line([a + u * s, a + u * (s + d_)], width)
            s += d_
            left -= d_
            if left <= 1e-6:
                draw = not draw
                left = on if draw else off
    return L_.a()


def walker(px, py, sc=1.0, reach=(1.0, 1.0)):
    """Small standing figure with one arm raised. Returns coverage and the lamp position."""
    L_ = Layer(W, H, 3)
    s = sc
    S = lambda *p: [(px + a * s, py + b * s) for a, b in p]
    L_.ell(px - 3.8 * s, py - 50 * s, px + 3.8 * s, py - 41.5 * s)
    L_.poly(S((-4.8, -41), (4.8, -41), (6.2, -20), (3.6, 0), (0.8, 0), (0, -18), (-2, 0), (-5.2, 0), (-5.6, -21)))
    lx, ly = 18 * reach[0], -54 * reach[1]
    L_.poly(S((3, -39.5), (7, -38.5), (lx + 1, ly + 3), (lx - 1.5, ly + 0.5)))
    return L_.a(), (px + lx * s, py + ly * s)
