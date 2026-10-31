"""HKBU SCIE1007 coursework science video. Shared kit for the `manual` direction: one printed booklet, eight chapters, invented rune script that spells the real CDK20 sequence.

Everything is laid out flat on a spread of SW x SH, then wrap() puts it in the book on the desk at 1920 x 1080.
Fonts: Noto Serif SC and Noto Sans SC (SIL OFL), the variable files already on this machine.
"""
from t import *

ST = ART / "manual" / "stills"
FW, FH = 1920, 1080
SW, SH = 1800, 992
SEQ = sequence()["seq"]
assert len(SEQ) == 346

# Chapter papers and inks, used in the frames and the page edges
CH = {
    1: dict(paper="#c8c4b8", ink="#2a2422", spot="#7a1c1e", len=141),
    2: dict(paper="#ecca92", ink="#3a1c14", spot="#b23c22", len=142),
    3: dict(paper="#141417", ink="#b8bcc4", spot="#5a5e68", len=129),
    4: dict(paper="#f1e5c6", ink="#141f66", spot="#f0ae22", len=213),
    5: dict(paper="#f6b414", ink="#14100c", spot="#d62c1a", len=139),
    6: dict(paper="#d0dcc8", ink="#163c30", spot="#3f8a6a", len=151),
    7: dict(paper="#efc6b8", ink="#4e1c42", spot="#c04a7a", len=49),
    8: dict(paper="#f5f0e4", ink="#1a2030", spot="#c8a23c", len=99),
}
T_ALL = sum(c["len"] for c in CH.values())


def serif(size, wght=700):
    f = ImageFont.truetype(FD + "NotoSerifSC-VF.ttf", int(size))
    f.set_variation_by_axes([wght])
    return f


def sans(size, wght=700):
    f = ImageFont.truetype(FD + "NotoSansSC-VF.ttf", int(size))
    f.set_variation_by_axes([wght])
    return f


# ---- runes: bar on top, stem, six optional strokes. Our own invention; one glyph for each of the 20 amino acid letters ----
ALPHA = "ACDEFGHIKLMNPQRSTVWY"
_seen, RUNE = set(), {}
_r = np.random.default_rng(346)
for a in ALPHA:
    while True:
        b = tuple(int(v) for v in _r.integers(0, 2, 7))
        if b not in _seen and 2 <= sum(b) <= 5:
            _seen.add(b)
            RUNE[a] = b
            break
_SEG = [((0.5, 0), (0.5, 1)), ((0, 0), (0.5, 0.5)), ((1, 0), (0.5, 0.5)), ((0, 1), (0.5, 0.5)), ((1, 1), (0.5, 0.5)), ((0, 1), (1, 1)), ((0, 0.5), (1, 0.5))]


class Mask:
    """Antialiased ink coverage, drawn at ss times the size and reduced on a()."""

    def __init__(self, w=SW, h=SH, ss=2):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, f, anchor="ls", track=0, v=255):
        """f must be built at size * ss."""
        x, y = xy[0] * self.ss, xy[1] * self.ss
        if track == 0:
            self.d.text((x, y), s, fill=v, font=f, anchor=anchor)
            return x / self.ss + f.getlength(s) / self.ss
        for c in s:
            self.d.text((x, y), c, fill=v, font=f, anchor="l" + anchor[1])
            x += f.getlength(c) + track * self.ss
        return x / self.ss

    def rect(self, x0, y0, x1, y1, v=255):
        s = self.ss
        self.d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=v)

    def poly(self, pts, v=255):
        self.d.polygon([(a * self.ss, b * self.ss) for a, b in pts], fill=v)

    def ell(self, x0, y0, x1, y1, v=255, w=0):
        s = self.ss
        if w:
            self.d.ellipse([x0 * s, y0 * s, x1 * s, y1 * s], outline=v, width=int(w * s))
        else:
            self.d.ellipse([x0 * s, y0 * s, x1 * s, y1 * s], fill=v)

    def line(self, pts, w=2.0, v=255):
        self.d.line([(a * self.ss, b * self.ss) for a, b in pts], fill=v, width=max(1, int(w * self.ss)), joint="curve")

    def pen(self, pts, w=2.0, amp=0.7, seed=0, v=255):
        self.line(wobble(pts, amp, seed), w, v)

    def dash(self, pts, w=2.4, on=16, off=11, amp=0.6, seed=0, v=255):
        """Dashed pencil line along a polyline."""
        p = np.array(wobble(pts, amp, seed), np.float32)
        seg = np.hypot(*(p[1:] - p[:-1]).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        t = 0.0
        while t < cum[-1]:
            ts = np.linspace(t, min(t + on, cum[-1]), 8)
            xs = np.interp(ts, cum, p[:, 0])
            ys = np.interp(ts, cum, p[:, 1])
            self.line(list(zip(xs, ys)), w, v)
            t += on + off

    def rune(self, x, y, ch, w=9.0, h=13.0, lw=1.6, v=255):
        b = RUNE[ch]
        X = lambda u: (x + u * w) * self.ss
        Y = lambda t: (y + t * h) * self.ss
        L = max(1, int(lw * self.ss))
        self.d.line([X(0), Y(0), X(1), Y(0)], fill=v, width=L)
        for k, (p, q) in enumerate(_SEG):
            if b[k]:
                self.d.line([X(p[0]), Y(p[1]), X(q[0]), Y(q[1])], fill=v, width=L)

    def runes(self, x, y, wd, lines, start=0, w=9.0, h=13.0, gap=4.0, lh=24.0, lw=1.6, skip=None, v=255):
        """Set the real sequence in order as text. Returns the next index. skip(x, y) leaves a cell empty and does not consume a letter."""
        i = start
        for l in range(lines):
            cx = x
            yy_ = y + l * lh
            while cx + w <= x + wd:
                if skip is not None and skip(cx, yy_):
                    cx += w + gap
                    continue
                self.rune(cx, yy_, SEQ[i % 346], w, h, lw, v)
                brk = (i * 7 + 3) % 6 == 0  # word gaps
                cx += w + gap + (w if brk else 0)
                i += 1
        return i

    def a(self):
        return np.asarray(self.im.resize((self.w, self.h), Image.LANCZOS), np.float32) / 255

    def hi(self):
        return np.asarray(self.im, np.float32) / 255


def wobble(pts, amp=0.7, seed=0):
    r = np.random.default_rng(seed)
    p = np.array(pts, np.float32)
    seg = np.hypot(*(p[1:] - p[:-1]).T)
    n = np.maximum((seg / 7).astype(int), 1)
    out = []
    for i in range(len(p) - 1):
        for k in range(n[i]):
            out.append(p[i] + (p[i + 1] - p[i]) * k / n[i])
    out.append(p[-1])
    out = np.array(out)
    nz = np.cumsum(r.normal(0, 1, out.shape), 0)
    nz -= np.linspace(0, 1, len(nz))[:, None] * nz[-1]
    nz = nz / max(np.abs(nz).max(), 1e-3)
    return [tuple(q) for q in out + nz * amp]


# ---- print ----
def paper(hexcol, seed=1, w=SW, h=SH, mott=0.05):
    b = hexc(hexcol)
    f = fbm(h, w, 3, 3, seed) - 0.5
    m = fbm(h, w, 120, 4, seed + 5) - 0.5
    out = np.ones((h, w, 3), np.float32) * b
    out *= (1 + (f * 0.10 + m * mott * 2))[..., None]
    return out


def halftone(g, cell=8.0, ang=45.0):
    """g 0..1 ink wanted; returns coverage."""
    h, w = g.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(ang)
    u = (x * np.cos(a) + y * np.sin(a)) / cell
    v = (-x * np.sin(a) + y * np.cos(a)) / cell
    s = 0.5 + 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
    return np.clip((g - (1 - s)) * cell * 0.45 + 0.5, 0, 1)


def ink(rgb, cov, col, breakup=0.0, seed=3):
    """Lay a flat ink, optionally starved by the paper grain."""
    col = hexc(col) if isinstance(col, str) else col
    if breakup:
        g = fbm(rgb.shape[0], rgb.shape[1], 2.5, 2, seed)
        cov = cov * np.clip(1 - breakup * (g > 0.62), 0, 1)
    return rgb * (1 - cov[..., None]) + col * cov[..., None]


def tape(w, h, ang, seed=0):
    """Coverage of a strip of masking tape, rough cut ends."""
    s = 2
    pad = int(max(w, h))
    a = np.zeros((h * s, w * s), np.float32)
    im = Image.new("L", (pad * 3, pad * 3), 0)
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    x0, y0 = pad + 0, pad + 0
    d.polygon([(x0 + r.uniform(-3, 3), y0), (x0 + w + r.uniform(-3, 3), y0), (x0 + w + r.uniform(-3, 3), y0 + h), (x0 + r.uniform(-3, 3), y0 + h)], fill=255)
    return im.rotate(ang, Image.BICUBIC, center=(x0 + w / 2, y0 + h / 2)), pad


def paste_tape(rgb, cx, cy, w, h, ang, col="#e7dab0", alpha=0.82, seed=0):
    im, pad = tape(w, h, ang, seed)
    H_, W_ = rgb.shape[:2]
    big = Image.new("L", (W_, H_), 0)
    big.paste(im, (int(cx - pad - w / 2), int(cy - pad - h / 2)))
    m = np.asarray(big, np.float32) / 255
    shadow = np.roll(np.roll(gauss(m, 2.5), 3, 0), 2, 1)
    rgb = rgb * (1 - 0.22 * shadow[..., None])
    return rgb * (1 - m[..., None] * alpha) + hexc(col) * m[..., None] * alpha


# ---- book on the desk ----
def chapter_at(frac):
    """Which chapter a fraction 0..1 through the book belongs to."""
    t = frac * T_ALL
    for k, c in CH.items():
        t -= c["len"]
        if t <= 0:
            return k
    return 8


def wrap(spread, pos, tilt=-1.6, zoom=1.0, cover="#1a1a22", lamp=(380, 170), desk="#141216", warm=1.0, dark=0.0, fall=1500.0, pan=(0, 0), floor=0.40):
    """Curl a flat spread into an open book. pos 0..1 is how far through the book we are: page stacks left and right, each sheet in its chapter's paper."""
    H_, W_ = spread.shape[:2]
    S = 2  # the page edges are thin, build at 2x
    OW, OH = FW * S, FH * S
    Y, X = np.mgrid[0:OH, 0:OW].astype(np.float32)
    cx, cy = OW / 2 + pan[0] * S, OH / 2 - 8 + pan[1] * S
    t = np.deg2rad(tilt)
    c_, s_ = np.cos(t), np.sin(t)
    x = (c_ * (X - cx) + s_ * (Y - cy)) / zoom / S
    y = (-s_ * (X - cx) + c_ * (Y - cy)) / zoom / S
    # open book profile: edges pinched at the gutter
    u = x / (W_ / 2)
    pinch = 26 * np.exp(-np.abs(x) / 66) + 10 * (1 - u ** 2)
    v = y * (1 + (pinch - 10) / (H_ / 2) * 0.9)
    # page surface: pulled into the gutter, so the print stretches a touch away from it
    px = x + 16 * np.tanh(x / 90) * np.exp(-np.abs(x) / 180)
    sx, sy = px + W_ / 2, v + H_ / 2
    inside = (np.abs(px) < W_ / 2) & (np.abs(v) < H_ / 2)
    pg = sample(spread, np.clip(sx, 0, W_ - 2.01), np.clip(sy, 0, H_ - 2.01))
    out = np.ones((OH, OW, 3), np.float32) * hexc(desk)
    wood = fbm(OH // 2, OW // 2, 200, 3, 2)
    wood = np.asarray(Image.fromarray(wood).resize((OW, OH), Image.BICUBIC), np.float32)
    out *= (0.8 + 0.5 * wood[..., None])
    out = np.array(out, np.float32)
    # stacks: thin sheets fanning out on both sides, chapter colours in order
    N = 34
    nL, nR = max(3, int(pos * N)), max(3, int((1 - pos) * N))
    pad = np.maximum(np.abs(px) - W_ / 2, 0)
    dv = np.abs(v) - H_ / 2
    # hard board under everything
    board = (np.abs(px) < W_ / 2 + N * 2.0 + 16) & (v > -H_ / 2 - 8) & (v < H_ / 2 + N * 1.7 + 16)
    shadow = gauss(board.astype(np.float32), 26)
    shadow = np.roll(np.roll(shadow, 36, 0), 24, 1)
    out *= (1 - 0.7 * shadow[..., None])
    out = np.where(board[..., None], hexc(cover), out)
    for side, n, base in ((-1, nL, 0.0), (1, nR, pos)):
        for i in range(n, 0, -1):
            f = (i / N) * (1 if side > 0 else 1)
            # sheet i sits i steps below the visible page
            fr = pos - (i / N) * pos * 1.0 if side < 0 else pos + (i / N) * (1 - pos)
            k = chapter_at(np.clip(fr, 0, 1))
            sheet = ((side * px) > 0) & ((side * px) < W_ / 2 + i * 2.0) & (v > -H_ / 2) & (v < H_ / 2 + i * 1.7)
            col = hexc(CH[k]["paper"]) * (1 - 0.018 * (i % 2)) * (0.86 if i % 3 == 0 else 1)
            out[sheet] = col
    sc = np.exp(-np.abs(x) / 44) * 0.55 + np.exp(-np.abs(x) / 8) * 0.40 + np.exp(-np.abs(x) / 180) * 0.18
    hi = np.exp(-((np.abs(x) - 150) / 90) ** 2) * 0.06
    page = pg * (1 - sc[..., None]) + hi[..., None]
    out = np.where(inside[..., None], page, out)
    # fine edge between the top page and the stack
    edge = inside ^ np.roll(inside, 2, 0)
    out[edge] *= 0.7
    # lamp from upper left, warm
    d = np.hypot(X / S - lamp[0], (Y / S - lamp[1]) * 1.2)
    L = np.clip(1.22 - d / fall, floor, 1.22)
    if dark:
        L = L * (1 - dark) + np.clip(1.1 - d / 900, 0.1, 1.1) * dark
    out = out * L[..., None] * (hexc("#fff4e4") * warm + (1 - warm))
    out = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((FW, FH), Image.LANCZOS), np.float32) / 255
    return out


def hand_thumb(w, h, base, tip, r, seed=0):
    """Coverage and shading of one finger drawn as a tapered capsule: shading rounds it so it survives a halftone."""
    yy_, xx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    ax, ay, bx, by = base[0], base[1], tip[0], tip[1]
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t_ = np.clip(((xx_ - ax) * vx + (yy_ - ay) * vy) / L2, 0, 1)
    d = np.hypot(xx_ - ax - t_ * vx, yy_ - ay - t_ * vy)
    rr = r * (1 - 0.14 * t_ ** 2)
    cov = np.clip((rr - d) + 0.5, 0, 1)
    round_ = np.sqrt(np.clip(1 - (d / rr) ** 2, 0, 1))
    return cov, round_
