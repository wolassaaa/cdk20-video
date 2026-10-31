"""HKBU SCIE1007 coursework science video. Lantern motion film: one continuous shot of 18 s at 1080p30.
A small warm lamp feels about in the dark. The cold AI light opens over the real CDK20 surface that was there all along. The camera goes down to the pocket while the light closes round it. 048 arrives along a beam of punched-plate light, turns once, and the measured number lights up behind the wall.
Run: python film.py <offset> <stride> <out_dir>. frame(539) is also T5, so the film stops exactly on the still."""
import sys
from pathlib import Path

from lk import *
from mv import S, fit_screen, pk, slerp, t5_camera, view2
from t3 import FLOOR, keyhole

F_OPEN, F_HOLD, F_P0, F_P1 = 105, 135, 225, 330
F_DOT, F_KEY0, F_KEY1, F_TURN, F_CLICK = 330, 345, 395, 401, 413
F_WALL0, F_WALL1, F_END = 415, 455, 540
PERIOD = 16.0
AX, AY = 2520.0, -760.0
dx_, dy_ = xx - AX, yy - AY
th, r = np.arctan2(dy_, dx_), np.hypot(dx_, dy_)
NB = 30000


def shifted(a, dx, dy):
    """Move a layer without wrapping it round the frame edge."""
    o = np.zeros_like(a)
    y0, y1 = max(dy, 0), min(H + dy, H)
    x0, x1 = max(dx, 0), min(W + dx, W)
    o[y0:y1, x0:x1] = a[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return o


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def out3(t):
    t = np.clip(t, 0, 1)
    return 1 - (1 - t) ** 3


R1, d1, lig_cam, heavy = t5_camera()
s1, ax1, ay1 = fit_screen(lig_cam)
P = (R1.T @ (-d1)).astype(np.float32)  # the ligand's centre, in the mesh frame
lig_mesh = ((lig_cam[heavy] - d1) @ R1).astype(np.float32)
_d = np.full(len(S["v"]), 1e9, np.float32)
for a_ in lig_mesh:
    _d = np.minimum(_d, np.sum((S["v"] - a_) ** 2, 1))
DIST = np.sqrt(_d)
_Rh1 = None


def R_hold(f):
    return (rot(0, -6 + 0.10 * np.clip(f - F_HOLD, 0, F_P0 - F_HOLD), -14) @ base_view()).astype(np.float64)


def camera(f):
    p = ease((f - F_P0) / (F_P1 - F_P0))
    Rh = R_hold(f)
    if p <= 0:
        return Rh, 16.0, 1130.0, 462.0, None, None, 0.0
    R0 = R_hold(F_P0)
    SP0 = np.array(((R0 @ P)[0] * 16 + 1130, -(R0 @ P)[1] * 16 + 462))
    R_ = slerp(R0, R1, p)
    sc = 16.0 * (s1 / 16.0) ** p
    tgt = SP0 + (np.array((ax1, ay1)) - SP0) * p
    Pc = R_ @ P
    cx, cy = tgt[0] - sc * Pc[0], tgt[1] + sc * Pc[1]
    pc = ease((p - 0.30) / 0.70)
    zc = float(Pc[2]) + pk.CUT + 44.0 * (1 - pc)
    sh = ease((p - 0.35) / 0.65)
    shell = 6.5 + 70.0 * (1 - sh) ** 2
    return R_, sc, cx, cy, zc, DIST < shell, p


def passes(f):
    R_, sc, cx, cy, zc, ex, p = camera(f)
    return view2(R_, sc, cx, cy, zcut=zc, cull_back=True, extra=ex), p


def cold(V, p):
    """Rays from the huge lamp. Hard edges, black between. The width of a line follows real pLDDT."""
    return lit_rays(V), None


def lit_rays(V):
    phase = th * 1900.0 / PERIOD + V["z"] * 0.34 * 10.5 / PERIOD
    tone = np.clip(V["key"] ** 0.75, 0, 1) * (0.25 + 0.75 * V["ao"] ** 1.2)
    conf = smooth(V["conf"], 0.5, 0.86)
    width = np.clip(0.10 + 0.72 * tone, 0, 0.86) * (0.42 + 0.58 * conf)
    return stripes(phase, width, aa=0.11) * V["mask"] * smooth(V["key"], 0.0, 0.05)


# ---------- things that never change ----------
fig0, (lx0, ly0) = walker(322.0, FLOOR + 2, 1.9)
pool0 = fft_blur((((xx - 322) / 104) ** 2 + ((yy - FLOOR - 8) / 9) ** 2 < 1).astype(np.float32), 0.8)
txt3 = tx("no one had measured CDK20's shape", 44, 500, 1860, 932, anchor="rs")
bw = tw("schematic", 36, 500)
fr3 = dash([(1860 - bw - 48, 960), (1860, 960), (1860, 1028), (1860 - bw - 48, 1028)], on=12, off=9, width=3, closed=True)
txt3 = np.maximum(np.maximum(txt3, fr3), tx("schematic", 36, 500, 1836, 1007, anchor="rs"))
lab4 = tx("AlphaFold DB v6 · predicted", 42, 700, 96, 1042)
for i in range(3):
    lab4 = np.maximum(lab4, Layer(W, H, 2).rect(60 + i * 10, 1006, 65 + i * 10, 1050).a())
KH = keyhole()
fr_all = dash(KH, on=20, off=15, width=3.6, closed=True)

# left wall of T5
x0 = 84
big = stencil("33.4", 330, 900, x0, 490)
line2 = stencil("± 22.6 nM", 150, 900, x0 + 6, 668)
pre = tx("048 =", 92, 800, x0 + 4, 176)
holes = np.maximum(big, line2)
shaft = extrude(holes, 150, 92, step=3)
ic50 = tx("Enzyme IC50", 46, 700, x0 + 4, 92)
plate = Layer(W, H, 2).rect(x0 + 4, 716, x0 + 4 + 720, 788).a()
ptxt = tx("MEASURED · Ren 2023, Fig. 9A", 44, 800, x0 + 26, 768)
sent = np.maximum(tx("Just this much cuts the", 54, 700, x0 + 4, 880), tx("enzyme's activity in half.", 54, 700, x0 + 4, 950))
rtag = tx("OUR RE-DOCKING", 42, 800, 1500, 1010, anchor="ms")
rw = tw("OUR RE-DOCKING", 42, 800)
fx0, fx1, fy0, fy1 = 1500 - rw / 2 - 26, 1500 + rw / 2 + 26, 958, 1032
_fr = Layer(W, H, 2)
_n = int((fx1 - fx0) / 20)
for i in range(_n + 1):
    px = fx0 + (fx1 - fx0) * i / _n
    for py in (fy0, fy1):
        _fr.ell(px - 5, py - 5, px + 5, py + 5)
_m = int((fy1 - fy0) / 20)
for j in range(_m + 1):
    py = fy0 + (fy1 - fy0) * j / _m
    for px in (fx0, fx1):
        _fr.ell(px - 5, py - 5, px + 5, py + 5)
rframe = _fr.a()
rplate = Layer(W, H, 2).rect(fx0 - 10, fy0 - 10, fx1 + 10, fy1 + 10).a()

# 048: the same render as the still, only moved and turned as one rigid piece
_lig = Image.open(kit.ROOT / "styleframes/S2plus/public/pose_048_lig.png").convert("RGBA").resize((960, 1080), Image.LANCZOS)
LIG = Image.new("RGBA", (W, H), (0, 0, 0, 0))
LIG.paste(_lig, (W - 960 + 20, 0))
_la = np.asarray(LIG, np.float32)[..., 3] / 255
yl, xl = np.where(_la > 0.3)
LCX, LCY = float(xl.mean()), float(yl.mean())
CNX, CNY = W + 60.0, H + 40.0

_cache = {}


def static_final():
    if "V" not in _cache:
        V, _ = passes(F_P1)
        _cache["V"] = V
        _cache["lit"] = lit_rays(V)
        pm = fft_blur((V["mask"] > 0.5).astype(np.float32), 0.8)
        _cache["pm"] = pm
        ang = np.degrees(np.arctan2(LCY - CNY, LCX - CNX))
        cone = beam(CNX, CNY, ang - 10.5, ang + 10.5)
        th_ = np.arctan2(yy - CNY, xx - CNX)
        r_ = np.hypot(xx - CNX, yy - CNY)
        b_ = ((th_ + np.pi) / (2 * np.pi) * 7200).astype(np.int64) % 7200
        rm_ = np.full(7200, 1e9, np.float32)
        hit = pm > 0.5
        np.minimum.at(rm_, b_[hit], r_[hit])
        rm_ = np.minimum.reduce([np.roll(rm_, i) for i in range(-3, 4)])
        _cache["stop"] = (r_ < rm_[b_] + 2).astype(np.float32)
        _cache["r_"] = r_
        _cache["coneb"] = cone
        pool = (np.clip(fft_blur((_la > 0.4).astype(np.float32), 26.0) * 5.5, 0, 1) > 0.5).astype(np.float32)
        _cache["pool"] = pool
    return _cache


def ligand(f):
    """Position and angle of 048 at frame f, or None. It flies in along the dot beam, stops at the mouth a quarter turn short, then turns home."""
    if f < F_KEY0:
        return None
    t = out3((f - F_KEY0) / (F_KEY1 - F_KEY0))
    x_, y_ = CNX + 140 + (LCX - CNX - 140) * t, CNY + 110 + (LCY - CNY - 110) * t
    a_ = -210.0 + (210.0 - 42.0) * t
    if f >= F_TURN:
        a_ = -42.0 * (1 - ease((f - F_TURN) / (F_CLICK - F_TURN)))
    return x_, y_, a_


def keyhole_left(n):
    return fr_all if n >= len(KH) else dash(KH[:max(2, n)], on=20, off=15, width=3.6)


def frame(f):
    c = blank()
    o = out3((f - F_OPEN) / 18) if f >= F_OPEN else 0.0
    V, p = (None, 0.0)
    final = f >= F_P1
    if f >= F_OPEN:
        if final:
            st = static_final()
            V, p = st["V"], 1.0
        else:
            V, p = passes(f)
    # ---------- the cold light ----------
    if V is not None:
        m = V["mask"]
        mid = 128.75
        hw = 16.75 * o + 0.06
        a0, a1 = mid - hw - 7 * p, mid + hw + 14.5 * p
        bm = beam(AX, AY, a0, a1)
        A0, A1 = np.radians(90.0), np.radians(190.0)
        bins = ((th - A0) / (A1 - A0) * NB).astype(np.int64)
        ok = (bins >= 0) & (bins < NB)
        sel = ok & (m > 0.5)
        rmin = np.full(NB, 1e9, np.float32)
        np.minimum.at(rmin, bins[sel], r[sel])
        rmin = np.minimum.reduce([np.roll(rmin, i) for i in range(-30, 31, 5)])  # no hairlines of light through pinholes in the mask
        fl_y = FLOOR + 420 * p
        free = bm * (r < rmin[np.clip(bins, 0, NB - 1)])
        air = free * (yy < fl_y)
        k_air = (1 - p) ** 2
        ph_air = th * 1900.0 / PERIOD
        c = add(c, air * (1 - m) * 0.26 * k_air, COLD)
        c = add(c, stripes(ph_air, 0.30, 0.2) * air * (1 - m) * 0.30 * k_air, COLD)
        c = add(c, stripes(ph_air, 0.34, 0.18) * free * (yy >= fl_y) * 0.62 * k_air, COLD)
        c = lay(c, m, BLACK)
        lit = st["lit"] if final else lit_rays(V)
        lit = lit * bm
    # ---------- chalk, until the light replaces it ----------
    if f < F_HOLD:
        k = 1.0 if f < F_OPEN else 1 - ease((f - F_OPEN) / 26)
        c = lay(c, keyhole_left(int(len(KH) * k)), CHALK * 0.6)
        if f < F_OPEN + 12:
            wipe = 0.0 if f < F_OPEN else ease((f - F_OPEN) / 12)
            c = lay(c, txt3 * (xx < 1960 - 1400 * wipe) * (xx > 700 + 0 * wipe), CHALK)
    # ---------- the person and the warm lamp, who leave as the camera goes in ----------
    if p < 0.62:
        q = ease(p / 0.62)
        ox, oy = int(-760 * q), int(300 * q)
        fig = shifted(fig0, ox, oy)
        lx, ly = lx0 + ox, ly0 + oy
        # the search: the axis wanders and the lamp is pushed further and further, then settles on the first patch of surface
        g = np.clip(f / F_OPEN, 0, 1)
        ax_d = -90 + 31 * ease(g) + 26 * np.sin(g * 7.4) * (1 - g) ** 0.8
        half = 15 - 6 * ease(g)
        reach = 250 + 550 * ease((g - 0.25) / 0.75)
        ang = np.arctan2(yy - ly, xx - lx)
        da = np.abs(np.angle(np.exp(1j * (ang - np.radians(ax_d)))))
        dist = np.hypot(xx - lx, yy - ly)
        cone = fft_blur(((da < np.radians(half)) & (dist < reach)).astype(np.float32), 0.7)
        if V is None:
            if "V0" not in _cache:
                _cache["V0"], _ = passes(F_HOLD)
            Vw = _cache["V0"]
            air_w = 0.0
            bmw = 0.0
        else:
            Vw, air_w, bmw = V, air, bm
        mw = Vw["mask"]
        warm = np.clip(Vw["normal"] @ np.array((-0.55, -0.62, 0.56), np.float32), 0, 1) * (0.3 + 0.7 * Vw["ao"])
        wt = fft_blur(((warm > 0.16) * 0.34 + (warm > 0.38) * 0.33 + (warm > 0.60) * 0.33).astype(np.float32), 0.8)
        c = add(c, cone * (1 - mw) * (1 - air_w) * (yy < FLOOR + oy) * (0.30 - 0.13 * ease(g)), AMBER)
        if V is not None:
            c = lay(c, lit * (1 - np.clip(cone * mw * wt * (1 - bmw), 0, 1)), COLD)
        c = lay(c, np.clip(cone * mw * wt * (1 - bmw), 0, 1), AMBER)
        c = lay(c, fig, AMBER)
        c = add(c, (np.hypot(xx - lx, yy - ly) < 6.5).astype(np.float32), AMBER_HI)
        c = add(c, shifted(pool0, ox, oy) * 0.42, AMBER)
    elif V is not None:
        c = lay(c, lit, COLD)
    # ---------- the label of the AI light ----------
    if F_HOLD <= f < F_P0 + 30:
        wipe = out3((f - F_HOLD) / 14)
        leave = ease((f - F_P0) / 30)
        c = lay(c, lab4 * (xx < 60 + 660 * wipe) * (xx > 60 + 660 * leave), COLD)
    # ---------- 048 on a punched-plate beam ----------
    if f >= F_DOT:
        st = static_final()
        pm = st["pm"]
        pool = st["pool"]
        t = ease((f - F_DOT) / 22)
        Rg = 300 + 1500 * t
        d_ = dot_screen(np.clip(0.8 * st["coneb"] * (1 - pm) * st["stop"] * (st["r_"] < Rg), 0, 1), cell=15.0)
        c = lay(c, d_, AMBER)
        lg = ligand(f)
        if f >= F_CLICK:
            c = lay(c, pool * pm * (st["lit"] * 0 + 1), BLACK)
            c = lay(c, dot_screen(0.8 * pool * pm, cell=15.0), AMBER)
        if lg is not None:
            x_, y_, a_ = lg
            im = LIG.rotate(a_, resample=Image.BICUBIC, center=(LCX, LCY), translate=(x_ - LCX, y_ - LCY))
            arr = np.asarray(im, np.float32) / 255
            al = arr[..., 3]
            halo = np.clip(fft_blur((al > 0.4).astype(np.float32), 5.0) * 6, 0, 1)
            c = lay(c, halo, BLACK)
            lt = arr[..., :3].mean(2)
            c = lay(c, al, AMBER_HI * 0.25)
            c = c + (al * np.clip(lt, 0, 1))[..., None] * (AMBER_HI * 0.85)
        if f >= F_DOT + 16:
            w_ = ease((f - F_DOT - 16) / 12)
            cut = (xx < fx0 - 12 + (fx1 - fx0 + 24) * w_)
            c = lay(c, rplate * cut, BLACK)
            c = lay(c, rframe * cut, AMBER)
            c = lay(c, rtag * cut, AMBER)
    # ---------- the wall: a hard edge of solid light slides in behind it, right to left ----------
    if f >= F_WALL0:
        st = static_final()
        w_ = ease((f - F_WALL0) / (F_WALL1 - F_WALL0))
        edge = 1020 - 1040 * w_
        rev = (xx > edge).astype(np.float32)
        c = add(c, shaft * (1 - holes) * (1 - st["pm"]) * 0.17 * rev, AMBER)
        c = lay(c, holes * rev, AMBER_HI * 0.45 + AMBER * 0.55)
        c = lay(c, pre * rev, AMBER_HI)
        c = lay(c, ic50 * rev, AMBER)
        c = lay(c, plate * rev, AMBER)
        c = lay(c, ptxt * rev, BLACK)
    if f >= F_WALL1 - 6:
        w_ = ease((f - F_WALL1 + 6) / 16)
        c = lay(c, sent * (xx < x0 + 720 * w_), AMBER_HI)
    return c


if __name__ == "__main__":
    off, stride, out = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    only = [int(a) for a in sys.argv[4:]]
    for f in only or range(off, F_END, stride):
        p_ = out / f"{f:04d}.png"
        if p_.exists():
            continue
        Image.fromarray((np.clip(frame(f), 0, 1) * 255 + 0.5).astype(np.uint8)).save(p_, compress_level=1)
    print("done", off, stride)
