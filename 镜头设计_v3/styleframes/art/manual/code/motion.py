"""HKBU SCIE1007 coursework science video. manual motion test, one unbroken shot in the booklet, 19.5 s at 1080p30, no sound.
A page folds over to the black page and its keyhole. The 346 runes on the left page turn into the real sequence letter by letter. Blue ink soaks out from what has been read. The real CDK20 surface comes up through the page; runes are pinned to the surface, the dot screen stays pinned to the paper. The page folds over to chapter five, 048 turns in the keyhole (our re-docking), the page reads itself, and the shot stops on the number.
Run: python motion.py <first> <last> <step> <out_dir>"""
import sys
import time
from functools import lru_cache

from mk import *
import T3 as T3m

sys.path.insert(0, str(ART / "scouts/a/code"))
import kit

WK = ART / "manual" / "_work"
N = 585
FLIP = 7
GRID = np.mgrid[0:FH, 0:FW].astype(np.float32)
YF, XF = np.mgrid[0:SH, 0:SW].astype(np.float32)
TILT = -1.2
clamp = lambda t: float(np.clip(t, 0, 1))
ease = lambda t: (lambda c: c * c * (3 - 2 * c))(clamp(t))

# ---- timeline, in frames ----
FA = (0, 34)        # fold to the black page
R0, R1 = 128, 262   # reading
FL0, FL1 = 150, 296  # ink soaks across
RS0, RS1 = 270, 372  # surface rises
LB0 = 352           # label
FC = (405, 441)     # fold to chapter five
KI = (443, 469)     # 048 goes in
KT = (469, 488)     # and turns
TAG = 478
TX = dict(enz=490, num=500, pm=512, s1=524, s2=536)
STAMP = 552
PUSH = (500, 575)


# ---- book ----
@lru_cache(maxsize=4)
def bg(pos):
    p = WK / ("bg_%03d.npy" % int(pos * 100))
    if p.exists():
        return np.load(p)
    S0, Bw, Bh = 1.5, 4200, 2400
    Y, X = np.mgrid[0:Bh, 0:Bw].astype(np.float32)
    x, y = (X - Bw / 2) / S0, (Y - Bh / 2) / S0
    u = x / (SW / 2)
    pinch = 26 * np.exp(-np.abs(x) / 66) + 10 * (1 - u ** 2)
    v = y * (1 + (pinch - 10) / (SH / 2) * 0.9)
    px = x + 16 * np.tanh(x / 90) * np.exp(-np.abs(x) / 180)
    out = np.ones((Bh, Bw, 3), np.float32) * hexc("#141216")
    wood = np.asarray(Image.fromarray(fbm(Bh // 2, Bw // 2, 200, 3, 2)).resize((Bw, Bh), Image.BICUBIC), np.float32)
    out = out * (0.8 + 0.5 * wood[..., None])
    n_ = 34
    nL, nR = max(3, int(pos * n_)), max(3, int((1 - pos) * n_))
    board = (np.abs(px) < SW / 2 + n_ * 2.0 + 16) & (v > -SH / 2 - 8) & (v < SH / 2 + n_ * 1.7 + 16)
    sh = np.roll(np.roll(gauss(board.astype(np.float32), 26), 27, 0), 18, 1)
    out *= 1 - 0.7 * sh[..., None]
    out = np.where(board[..., None], hexc("#1a1a22"), out)
    for side, n in ((-1, nL), (1, nR)):
        for i in range(n, 0, -1):
            fr = pos - (i / n_) * pos if side < 0 else pos + (i / n_) * (1 - pos)
            k = chapter_at(np.clip(fr, 0, 1))
            sheet = ((side * px) > 0) & ((side * px) < SW / 2 + i * 2.0) & (v > -SH / 2) & (v < SH / 2 + i * 1.7)
            out[sheet] = hexc(CH[k]["paper"]) * (1 - 0.018 * (i % 2)) * (0.86 if i % 3 == 0 else 1)
    out = out.astype(np.float32)
    np.save(p, out)
    return out


def gutter_x(y, cx=960.0, cy=532.0):
    t = np.deg2rad(TILT)
    return cx - np.tan(t) * (y - cy)


def book(spread, pos, cam):
    z, pnx, pny, lamp, fall, floor, warm, vig = cam
    Y, X = GRID
    cx, cy = 960 + pnx, 532 + pny
    t = np.deg2rad(TILT)
    c_, s_ = np.cos(t), np.sin(t)
    x = (c_ * (X - cx) + s_ * (Y - cy)) / z
    y = (-s_ * (X - cx) + c_ * (Y - cy)) / z
    u = x / (SW / 2)
    pinch = 26 * np.exp(-np.abs(x) / 66) + 10 * (1 - u ** 2)
    v = y * (1 + (pinch - 10) / (SH / 2) * 0.9)
    px = x + 16 * np.tanh(x / 90) * np.exp(-np.abs(x) / 180)
    a = np.clip((SW / 2 - np.abs(px)) * z + 0.5, 0, 1) * np.clip((SH / 2 - np.abs(v)) * z + 0.5, 0, 1)
    pg = sample(spread, np.clip(px + SW / 2, 0, SW - 2.01), np.clip(v + SH / 2, 0, SH - 2.01))
    B = sample(bg(pos), np.clip(x * 1.5 + 2100, 0, 4197), np.clip(y * 1.5 + 1200, 0, 2397))
    sc = np.exp(-np.abs(x) / 44) * 0.55 + np.exp(-np.abs(x) / 8) * 0.40 + np.exp(-np.abs(x) / 180) * 0.18
    hi = np.exp(-((np.abs(x) - 150) / 90) ** 2) * 0.06
    page = pg * (1 - sc[..., None]) + hi[..., None]
    out = B * (1 - a[..., None]) + page * a[..., None]
    d = np.hypot(X - lamp[0], (Y - lamp[1]) * 1.2)
    L = np.clip(1.22 - d / fall, floor, 1.22)
    out = out * L[..., None] * (hexc("#fff4e4") * warm + (1 - warm))
    if vig > 0:
        dv = np.hypot(X - 960, Y - 540)
        out = out * (1 - vig * (1 - np.clip(1 - (dv - 330) / 300, 0.05, 1)))[..., None]
    return np.clip(out, 0, 1), a


def fold(Fa, Aa, Fb, Ab, th, k=0.22, Wp=900.0):
    """A simple flat fold about the spine. Fa, Fb are finished frames of the two spreads, so everything printed comes along with the page."""
    Y, X = GRID
    gx = gutter_x(Y)
    u0 = X - gx
    base = np.where((u0 >= 0)[..., None], Fb, Fa)
    s, c = np.sin(th), np.cos(th)
    if th < np.pi / 2:
        a = u0 / Wp
        src, al, sign = Fa, Aa, 1.0
    else:
        a = -u0 / Wp
        src, al, sign = Fb, Ab, -1.0
        c = -c
    u = a / np.maximum(c + k * a * s, 1e-3)
    ok = (a >= 0) & (u >= 0) & (u <= 1)
    y0 = 532 + (Y - 532) * (1 - k * u * s)
    xs = gutter_x(y0) + sign * u * Wp
    tex = sample(src, np.clip(xs, 0, FW - 2.01), np.clip(y0, 0, FH - 2.01))
    A = sample(al, np.clip(xs, 0, FW - 2.01), np.clip(y0, 0, FH - 2.01)) * ok
    # the page casts a soft shadow on the side it is falling toward
    side = u0 if th < np.pi / 2 else -u0
    reach = Wp * abs(c) + 60
    near = 0.62 * s * np.exp(-np.maximum(side - reach, 0) / 170)
    # the far side only darkens as the page stands up; the two sides meet at exactly 90 degrees, so nothing jumps when the page crosses over
    far = 0.62 * s ** 3 * np.exp(-np.maximum(-side - 60, 0) / 170)
    sh = 1 - np.where(side >= 0, near, far)
    base = base * sh[..., None]
    return base * (1 - A[..., None]) + tex * (1 - 0.42 * s) * A[..., None]


# ---- letters that turn over ----
def paste(A, m, x, y):
    h, w = m.shape
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, A.shape[1]), min(y + h, A.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    A[y0:y1, x0:x1] = np.maximum(A[y0:y1, x0:x1], m[y0 - y:y1 - y, x0 - x:x1 - x])


def squish(m, s):
    h = m.shape[0]
    idx = ((np.arange(h) - h / 2) / max(s, 0.05) + h / 2).astype(int)
    ok = (idx >= 0) & (idx < h)
    out = m[np.clip(idx, 0, h - 1)].copy()
    out[~ok] = 0
    return out


class Flip:
    """One line of real text set first in runes; each cell turns over on its own beat."""

    def __init__(self, text, px, wght, x, y, t0, per, fam=None, seq=0, track=0):
        fam = fam or serif
        ss = 2
        f = fam(px * ss, wght)
        self.cells = []
        k = 0
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            ad = f.getlength(ch) / ss
            pos = f.getlength(text[:i]) / ss + track * i
            cw, chh = int(ad) + 14, int(px * 1.6)
            G = Mask(cw, chh, ss)
            G.text((7, px * 1.2), ch, f, "ls")
            R = Mask(cw, chh, ss)
            R.rune(7 + ad * 0.12, px * 1.2 - px * 0.72, SEQ[(seq + k) % 346], ad * 0.76, px * 0.72, max(1.4, px * 0.075))
            self.cells.append((x + pos - 7, y - px * 1.2, G.a(), R.a(), t0 + k * per))
            k += 1

    def draw(self, Ag, Ar, f):
        for x, y, g, r, t in self.cells:
            st = (f - t) / FLIP
            if st <= 0:
                paste(Ar, r, x, y)
            elif st >= 1:
                paste(Ag, g, x, y)
            elif st < 0.5:
                paste(Ar, squish(r, 1 - 2 * st), x, y)
            else:
                paste(Ag, squish(g, 2 * st - 1), x, y)


# ---- black page and the reading ----
CW_, CH_, COLS, GX0, GY0 = 30, 61, 25, 96, 72
TR = R0 + (R1 - R0) * (np.arange(346) / 345) ** 0.58


@lru_cache(maxsize=1)
def cells():
    Rm, Lm = {}, {}
    f = serif(38 * 3, 700)
    for a in ALPHA:
        M = Mask(CW_ + 6, CH_, 3)
        M.rune(6, 12, a, 21, 33, 2.4)
        Rm[a] = M.a()
        L_ = Mask(CW_ + 6, CH_, 3)
        L_.text(((CW_ + 6) / 2, 44), a, f, "ms")
        Lm[a] = L_.a()
    return Rm, Lm


@lru_cache(maxsize=1)
def black():
    return T3m.black_spread()


@lru_cache(maxsize=1)
def hole_s3():
    return T3m.keyhole_mask()


@lru_cache(maxsize=1)
def navy():
    n = paper("#10195c", 41, mott=0.06)
    M = Mask(SW, SH, 2)
    M.runes(930, 30, SW - 960, 25, 40, 15.0, 22.0, 6.0, 37.5, 1.5)
    a = M.a()
    n = n * (1 - a[..., None] * 0.92) + hexc("#3f55b0") * a[..., None] * 0.92
    h = hole_s3()[..., None]
    lit_ = np.clip(hole_s3() - np.roll(np.roll(hole_s3(), -4, 0), -4, 1), 0, 1)
    n = n * (1 - h) + hexc("#020203") * h
    return ink(n, lit_ * 0.9, "#7f96e6")


@lru_cache(maxsize=1)
def soak():
    return (XF / SW) * 0.86 + (YF / SH) * 0.06 + (fbm(SH, SW, 150, 4, 7) - 0.5) * 0.30


def read_spread(f):
    fr = (f - FL0) / (FL1 - FL0)
    front = -0.20 + 1.36 * np.clip(fr, 0, 1)
    c = np.clip((front - soak()) / 0.04, 0, 1)
    out = black() * (1 - c[..., None]) + navy() * c[..., None]
    # a dark wet edge at the front of the ink
    seam = np.clip(1 - np.abs(front - soak()) / 0.018, 0, 1) * (0 < fr < 1)
    out = out * (1 - 0.35 * seam[..., None])
    Rm, Lm = cells()
    Ar, Ag, Ah = np.zeros((SH, SW), np.float32), np.zeros((SH, SW), np.float32), np.zeros((SH, SW), np.float32)
    for i, a in enumerate(SEQ):
        r_, c_ = divmod(i, COLS)
        x, y = GX0 + c_ * CW_, GY0 + r_ * CH_
        st = (f - TR[i]) / FLIP
        if st <= 0:
            paste(Ar, Rm[a], x, y)
        elif st >= 1:
            paste(Ah if f - TR[i] < 26 else Ag, Lm[a], x, y)
        elif st < 0.5:
            paste(Ar, squish(Rm[a], 1 - 2 * st), x, y)
        else:
            paste(Ah, squish(Lm[a], 2 * st - 1), x, y)
    out = ink(out, Ar * 0.9, "#6c7180")
    out = ink(out, Ag, "#dfe6ff")
    return ink(out, Ah, "#f0ae22")


# ---- the surface comes up through the page ----
B_ = kit.base_view()
R_END = kit.rot(0, 0, -5) @ B_
SC, CX, CY = 18.16, 985.5, 484.5
Lv = np.array((-0.60, 0.62, 0.50), np.float32)
Lv /= np.linalg.norm(Lv)


@lru_cache(maxsize=1)
def screens():
    a15, a75 = np.deg2rad(15), np.deg2rad(75)
    f = lambda a: 0.5 + 0.25 * (np.cos(2 * np.pi * (XF * np.cos(a) + YF * np.sin(a)) / 7.0) + np.cos(2 * np.pi * (-XF * np.sin(a) + YF * np.cos(a)) / 7.0))
    return f(a15).astype(np.float32), f(a75).astype(np.float32)


@lru_cache(maxsize=1)
def rune_sheet():
    M = Mask(SW + 240, SH + 240, 2)
    M.runes(10, 14, SW + 200, int((SH + 200) / 36), 0, 15.0, 22.0, 6.0, 36.0, 3.0)
    return M.hi()


ht = lambda g, S: np.clip((g - (1 - S)) * 3.15 + 0.5, 0, 1)


def small_gauss_normal(n):
    h, w = n.shape[:2]
    sm = np.stack([np.asarray(Image.fromarray(n[..., i]).resize((w // 4, h // 4), Image.BILINEAR), np.float32) for i in range(3)], -1)
    sm = gauss(sm, 4.5)
    up = np.stack([np.asarray(Image.fromarray(sm[..., i]).resize((w, h), Image.BILINEAR), np.float32) for i in range(3)], -1)
    return up / np.maximum(np.linalg.norm(up, axis=2, keepdims=True), 1e-4)


@lru_cache(maxsize=1)
def paper_form():
    return paper("#fbf1d4", 43, mott=0.03)


_held = {}


def form(f):
    """Coverage and colour of the printed surface for this frame, and how far it has risen. Once it has stopped, the same print is reused."""
    if f >= RS1:
        if "f" not in _held:
            _held["f"] = form_at(RS1)
        return _held["f"]
    return form_at(f)


def form_at(f):
    t = clamp((f - RS0) / (RS1 - RS0))
    e = ease(t)
    R = kit.rot((1 - e) * -30, (1 - e) * 24, -5) @ B_
    s_ = SC * (0.93 + 0.07 * e)
    V = kit.view(R=R, scale=s_, cx=CX, cy=CY, w=SW, h=SH, ss=0.34, L=tuple(Lv))
    m, z, n = V["mask"], V["z"], V["normal"]
    # every pixel back to where it sits on the finished pose, so the runes stay stuck to the surface as it turns
    Rd = (R @ R_END.T).astype(np.float32)
    px, py = (XF - CX) / s_, -(YF - CY) / s_
    p = np.stack([px, py, z], -1) @ Rd   # row vectors: same as Rd.T @ p for each pixel
    ZL, ZH = -19.0, 30.0
    hr = np.clip((p[..., 2] - ZL) / (ZH - ZL), 0, 1) * (m > 0.02)
    xr = p[..., 0] * SC + CX
    yr = -p[..., 1] * SC + CY
    xr = xr + (xr - 930) * (-0.085 * hr)
    yr = yr + (yr - 500) * (-0.085 * hr)
    sheet = sample(rune_sheet(), np.clip((xr + 120) * 2, 0, 2 * (SW + 240) - 2.01), np.clip((yr + 120) * 2, 0, 2 * (SH + 240) - 2.01))
    # the plane of the page drops past the form, so only what is above it shows
    lev = ZH + 2 - ease(t * 1.18) * (ZH - ZL + 10)
    rv = np.clip((z - lev) / 1.4 + 0.5, 0, 1) * m
    key = np.clip(((n * Lv).sum(2) + 0.05) / 1.05, 0, 1)
    big = np.clip(((small_gauss_normal(n) * Lv).sum(2) + 0.1) / 1.1, 0, 1)
    ao = np.clip(V["ao"], 0, 1)
    s = np.clip((0.62 * key + 0.5 * big) * (0.25 + 0.75 * ao ** 1.3), 0, 1)
    tail = np.clip((0.72 - gauss(V["conf"], 1.5)) / 0.05, 0, 1) * (m > 0.5)
    S15, S75 = screens()
    gold = ht(np.clip((0.66 - s) / 0.34, 0, 1) * 0.98, S15)
    blue = ht(np.clip((0.36 - s) / 0.22, 0, 1) ** 0.8, S75)
    red = ht(np.clip((0.86 - s) / 0.44, 0, 1), S15)
    dk = ht(np.clip((0.34 - s) / 0.20, 0, 1) ** 0.8, S75)
    col = paper_form()
    col = ink(col, gold * (1 - tail), "#f0a81e")
    col = ink(col, red * tail, "#d9361c")
    col = ink(col, blue * (1 - tail), "#141f66")
    col = ink(col, dk * tail, "#3a0a22")
    fine = np.clip((0.78 - s) / 0.10, 0, 1)
    cov = sheet * fine * 0.92
    col = ink(col, cov * (1 - tail), "#141f66")
    col = ink(col, cov * tail, "#3a0a22")
    return rv, col, e


@lru_cache(maxsize=1)
def paper_slip():
    return paper("#fbf3dc", 9)


@lru_cache(maxsize=1)
def flip_label():
    return Flip(LABEL, 40, 800, 94, 925, LB0 + 12, 0.75)


def label(page, f):
    if f < LB0:
        return page
    x0, y0, x1, y1 = 70, 874, 716, 948
    p = clamp((f - LB0) / 12)
    xe = int(x0 + (x1 - x0) * ease(p))
    slip = np.zeros((SH, SW), np.float32)
    slip[y0:y1, x0:xe] = 1
    page = page * (1 - 0.5 * gauss(np.roll(np.roll(slip, 7, 0), 6, 1), 6)[..., None])
    page = np.where(slip[..., None] > 0, paper_slip(), page)
    if f >= LB0 + 10:
        A, B = np.zeros((SH, SW), np.float32), np.zeros((SH, SW), np.float32)
        flip_label().draw(A, B, f)
        A, B = A * slip, B * slip
        page = ink(page, B, "#7f96e6")
        page = ink(page, A, "#141f66")
    if f >= LB0 + 12:
        page = paste_tape(page, x0 + 2, y0 - 2, 84, 26, 40, seed=2)
        page = paste_tape(page, x1 + 2, y0 + 2, 84, 26, -42, seed=3)
    return page


def t4_spread(f):
    page = read_spread(f)
    rv, col, e = form(f)
    sh = gauss(np.roll(np.roll(rv, int(46 * e), 0), int(62 * e), 1), 20) * 0.78 * e
    page = page * (1 - sh[..., None])
    out = page * (1 - rv[..., None]) + col * rv[..., None]
    o = np.clip(rv - gauss(rv, 2.0), 0, 1)
    out = ink(out, np.clip(o * 3.0, 0, 0.9), "#fbf1d4")
    return label(out, f)


# ---- chapter five, built from T5.py so the page is the same page ----
@lru_cache(maxsize=1)
def t5():
    src = open(Path(__file__).with_name("T5.py"), encoding="utf-8").read()
    ns = {}
    exec(src[:src.index("# 048: warm bone")], ns)
    exec(src[src.index("# shadow of the page"):src.index("Tt = Mask")], ns)
    ns["pag"] = paper(CH[5]["paper"], 51, mott=0.04)
    # the stamp block
    exec(src[src.index("st = Mask(860"):src.index("rgb = wrap(")], ns)
    Rn = Mask(SW, SH, 2)
    Rn.runes(72, 862, 790, 3, 212, 11.0, 16.0, 4.5, 28.0, 2.0)
    ns["rn"] = Rn.a()
    L = ns["L"]
    ys, xs = np.where(L[..., 3] > 0.02)
    ns["lb"] = (max(xs.min() - 60, 0), max(ys.min() - 60, 0), min(xs.max() + 60, SW), min(ys.max() + 60, SH))
    ns["fl"] = [
        Flip("Enzyme IC50", 70, 900, 70, 112, TX["enz"], 1.1),
        Flip("048 = 33.4", 138, 900, 64, 286, TX["num"], 1.4, track=-1),
        Flip("± 22.6 nM", 138, 900, 64, 452, TX["pm"], 1.4, track=-1),
        Flip("Just this much cuts the", 50, 700, 70, 556, TX["s1"], 0.5),
        Flip("enzyme's activity in half.", 50, 700, 70, 618, TX["s2"], 0.5),
    ]
    ns["tagf"] = Flip("OUR RE-DOCKING", 36, 500, 941, 60, TAG, 1.2, fam=sans)
    return ns


@lru_cache(maxsize=1)
def grain():
    """Paper starving the ink a little. One pattern for the whole shot, never redrawn."""
    return np.clip(1 - 0.06 * (fbm(SH, SW, 2.5, 2, 4) > 0.62), 0, 1).astype(np.float32)


def t5_spread(f):
    T = t5()
    p = clamp((f - KI[0]) / (KI[1] - KI[0]))
    q = clamp((f - KT[0]) / (KT[1] - KT[0]))
    behind = T["behind"]
    if p > 0:
        L = T["L"]
        x0, y0, x1, y1 = T["lb"]
        ang = -52 * (1 - ease(q))
        dy = -(1 - ease(p)) * 620
        dx = (1 - ease(p)) * 150
        # 048 is only moved and turned in the plane, its shape is untouched
        crop = Image.fromarray((np.clip(L[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8), "RGBA").rotate(ang, Image.BICUBIC)
        c_ = np.asarray(crop, np.float32) / 255
        la = np.zeros((SH, SW), np.float32)
        lc = np.zeros((SH, SW), np.float32)
        h, w = c_.shape[:2]
        xp, yp = x0 + int(dx), y0 + int(dy)
        xa, ya, xb, yb = max(xp, 0), max(yp, 0), min(xp + w, SW), min(yp + h, SH)
        if xb > xa and yb > ya:
            la[ya:yb, xa:xb] = c_[ya - yp:yb - yp, xa - xp:xb - xp, 3]
            lc[ya:yb, xa:xb] = c_[ya - yp:yb - yp, xa - xp:xb - xp, :3].mean(2)
        behind = ink(behind, np.clip(gauss(la, 3.2) * 2.4, 0, 1), "#100d0c")
        col = ramp(np.clip(lc / np.maximum(la, 1e-3), 0, 1), [(0.3, "#e4661e"), (0.62, "#ffb732"), (0.9, "#fff6da"), (1, "#ffffff")])
        behind = behind * (1 - la[..., None]) + col * la[..., None]
    behind = behind * (1 - 0.72 * T["inner"][..., None])
    hole = T["hole"][..., None]
    out = T["pag"] * (1 - hole) + behind * hole
    out = ink(out, T["lip"], "#ffe08a")
    out = ink(out, T["Dd"].a(), "#1c1a22")
    out = ink(out, T["rn"] * 0.9, CH[5]["ink"])
    Ag, Ar = np.zeros((SH, SW), np.float32), np.zeros((SH, SW), np.float32)
    for fl_ in T["fl"]:
        fl_.draw(Ag, Ar, f)
    out = ink(out, Ar * 0.82, "#9a6a10")
    out = ink(out, Ag * grain(), CH[5]["ink"])
    if f >= TAG - 8:
        out = ink(out, T["Tg"].a(), "#1c1a22")
        A2, A3 = np.zeros((SH, SW), np.float32), np.zeros((SH, SW), np.float32)
        T["tagf"].draw(A2, A3, f)
        out = ink(out, A3 * 0.8, "#9a6a10")
        out = ink(out, A2, "#14100c")
    if f >= STAMP:
        sc = 1 + 0.12 * (1 - ease((f - STAMP) / 4))
        sm, kn = T["smask"], T["kn"]
        if sc > 1.001:
            x0, y0, x1, y1 = 50, 640, 930, 860
            cw, chh = x1 - x0, y1 - y0
            mat = (1 / sc, 0, cw / 2 * (1 - 1 / sc), 0, 1 / sc, chh / 2 * (1 - 1 / sc))
            zoomed = lambda a: np.pad(np.asarray(Image.fromarray(a[y0:y1, x0:x1]).transform((cw, chh), Image.AFFINE, mat, Image.BILINEAR), np.float32), ((y0, SH - y1), (x0, SW - x1)))
            sm, kn = zoomed(sm), zoomed(kn)
        out = ink(out, sm, "#a81a0e")
        out = ink(out, kn, "#fff0c4")
    return out


# ---- camera and lamp ----
C_WIDE = (1.0, 0.0, 0.0, (420.0, 160.0), 1800.0, 0.40, 1.0, 0.0)
C_T3 = (1.25, -562.0, -17.0, (960.0, 540.0), 720.0, 0.28, 0.2, 1.0)
C_READ = (1.0, 0.0, 0.0, (640.0, 320.0), 1500.0, 0.34, 0.6, 0.0)
C_T5 = (1.0, 0.0, 0.0, (900.0, 140.0), 2600.0, 0.40, 0.5, 0.0)
C_NUM = (1.16, 330.0, 118.0, (900.0, 140.0), 2600.0, 0.40, 0.5, 0.0)


def mixc(a, b, t):
    return tuple(mixc(x, y, t) if isinstance(x, tuple) else x + (y - x) * t for x, y in zip(a, b))


def camera(f):
    if f < 34:
        return C_T5
    if f < 92:
        return mixc(C_T5, C_T3, ease((f - 34) / 58))
    if f < 118:
        c = list(C_T3)
        c[0] += 0.012 * (f - 92) / 26
        return tuple(c)
    if f < 156:
        c = list(C_T3)
        c[0] += 0.012
        return mixc(tuple(c), C_READ, ease((f - 118) / 38))
    if f < 296:
        return mixc(C_READ, C_WIDE, ease((f - 156) / 140))
    if f < FC[1]:
        return C_WIDE
    if f < PUSH[0]:
        return C_T5
    return mixc(C_T5, C_NUM, ease((f - PUSH[0]) / (PUSH[1] - PUSH[0])))


@lru_cache(maxsize=2)
def frozen(name):
    if name == "T2":
        return book(np.load(WK / "T2_flat.npy"), 0.25, C_T5)
    if name == "S3":
        return book(read_spread(0), 0.25, C_T5)
    if name == "T4":
        return book(t4_spread(FC[0]), 0.45, C_WIDE)
    if name == "T5":
        return book(t5_spread(FC[1]), 0.70, C_T5)


def frame(f):
    if f < FA[1]:
        th = np.pi * ease(f / (FA[1] - 1))
        if th <= 0:
            return frozen("T2")[0]
        if th >= np.pi:
            return frozen("S3")[0]
        return fold(*frozen("T2"), *frozen("S3"), th)
    if f < RS0:
        return book(read_spread(f), 0.25, camera(f))[0]
    if f < FC[0]:
        return book(t4_spread(f), 0.45, camera(f))[0]
    if f < FC[1]:
        th = np.pi * ease((f - FC[0]) / (FC[1] - FC[0] - 1))
        if th <= 0:
            return frozen("T4")[0]
        if th >= np.pi:
            return frozen("T5")[0]
        return fold(*frozen("T4"), *frozen("T5"), th)
    return book(t5_spread(f), 0.70, camera(f))[0]


if __name__ == "__main__":
    a, b, st, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(exist_ok=True, parents=True)
    for f in range(a, min(b, N), st):
        if (out / ("%04d.jpg" % f)).exists():
            continue
        t0 = time.time()
        fr = frame(f)
        Image.fromarray((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out / ("%04d.jpg" % f), quality=96, subsampling=0)
        print(f, "%.2f s" % (time.time() - t0), flush=True)
