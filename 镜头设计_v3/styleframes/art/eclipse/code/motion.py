"""HKBU SCIE1007 coursework science video. Eclipse direction, the one-take motion test.
One world, one camera, no cuts: the shadow slides over the sun, full black, light breaks through the real gaps in the CDK20 surface, the camera rolls like a key turning, the number stands on a red wall.
The eclipse is a metaphor: the sun, its corona and the way it is hidden are staging. Only the surface shape, 048's pose and the numbers are real.
Everything rigid is pre-rendered once in the surface's own frame and resampled per frame, so one frame costs seconds, not a render."""
import os
import sys
import time

from ec import *

K4 = os.environ.get("EC4K") == "1"
MS, MW = (56.0, 5200) if K4 else (30.0, 2800)      # fine canvas: px per Angstrom, size
CS, CW = (30.0, 4800) if K4 else (15.0, 2400)      # canvas for soft light
FPS = 30
DUR = 18.8
HOLD = 0.8           # extra seconds of totality, so the one line in the dark can be read
SUN = np.array([0.34, -0.57])          # sun in world Angstrom, same as T4
RS = 385 / 17.6
G1, G2 = np.array([9.4, -11.5]), np.array([0.0, -20.9])    # the two real gaps in the outline, seen in T4
POCKET = np.array([0.73, -0.19])       # real pocket in view coordinates, from the docked pose
L = WORK / ("m4k" if K4 else "m")
L.mkdir(exist_ok=True)


def lp(a, b, u):
    return a + (b - a) * u


def ease(a, b, s):
    u = np.clip((s - a) / (b - a), 0, 1)
    return float(u * u * u * (u * (6 * u - 15) + 10))


def build():
    print("master view")
    V = kit.view(R=kit.base_view(), scale=MS, cx=MW / 2, cy=MW / 2, w=MW, h=MW, ss=0.45)
    my, mx = np.mgrid[0:MW, 0:MW].astype(np.float32)
    bx, by = (mx - MW / 2) / MS, -(my - MW / 2) / MS
    mask = V["mask"]
    hard = sstep(0.42, 0.58, mask)
    n3 = V["normal"]
    ao = V["ao"]
    # T4 surface light
    nz = np.clip(n3[..., 2], 0, 1)
    fres = (1 - nz) ** 3.2
    dx_, dy_ = bx - SUN[0], by - SUN[1]
    r = np.maximum(np.hypot(dx_, dy_), 1e-3)
    out = np.clip(n3[..., 0] * dx_ / r + n3[..., 1] * dy_ / r, 0, 1)
    rim = fres * (0.25 + 0.75 * out) * (0.3 + 0.7 * ao)
    fill = ao ** 1.6 * (0.2 + 0.8 * np.clip(0.5 * V["key"] + 0.7 * V["rim"], 0, 1))
    surf = 0.075 * fill + 0.62 * rim ** 1.2
    # T5 surface light: the wall's light from frame left, written in the surface's own frame
    ld = np.array([-0.75, 0.35, 0.56], np.float32)
    ld /= np.linalg.norm(ld)
    c, s_ = np.cos(np.radians(-96)), np.sin(np.radians(-96))
    lds = np.array([c * ld[0] - s_ * ld[1], s_ * ld[0] + c * ld[1], ld[2]], np.float32)
    lam = np.clip((n3 * lds).sum(-1), 0, 1) ** 1.5
    hs = sstep(0.4, 0.6, blur(mask, 3.5 * MS / 26))
    lip = blur(hs, 70 * MS / 26)
    reach = 1 - sstep(0.60, 0.97, lip)
    limb = np.clip(0.03 + 0.46 * lam * (0.3 + 0.7 * ao), 0, 0.56) * reach ** 1.1
    vall = (1 - hs) * sstep(0.56, 0.66, blur(hs, 30 * MS / 26))
    for k, a in dict(hard=hard, surf=surf, limb=limb, vall=vall).items():
        np.save(L / f"{k}.npy", a.astype(np.float32))

    print("corona")
    cy_, cx_ = np.mgrid[0:CW, 0:CW].astype(np.float32)
    ax, ay = (cx_ - CW / 2) / CS, -(cy_ - CW / 2) / CS
    h2 = sample(hard, ax * MS + MW / 2, -ay * MS + MW / 2)
    limb2 = h2 * (1 - blur(h2, 16 * CS / 17.6)) * 2
    th = np.arctan2(ay - SUN[1], ax - SUN[0])
    n = 2048
    s1 = noise(11, 340, (8, n), 1.4)[3]
    s2 = noise(12, 90, (8, n), 1.1)[5]
    idx = ((-th + np.pi) / (2 * np.pi) * n).astype(np.int32) % n
    st = (0.72 * s1 + 0.28 * s2)[idx]
    st = sstep(0.25, 0.8, (st - st.min()) / (st.max() - st.min()))
    sx0, sy0 = SUN[0] * CS + CW / 2, -SUN[1] * CS + CW / 2
    STEPS = 240
    lay = [np.zeros_like(limb2) for _ in range(3)]
    for i in range(STEPS):
        k = 1 - (i + 0.5) / STEPS * 0.62
        a = sample(limb2, sx0 + (cx_ - sx0) * k, sy0 + (cy_ - sy0) * k) * (1 - i / STEPS) ** 2.6
        lay[0 if i < STEPS * 0.22 else 1 if i < STEPS * 0.5 else 2] += a
    for j, a in enumerate(lay):
        a = blur(a, 1.2) / STEPS * 26 * (0.1 + 1.3 * st ** 1.4) * 0.55
        np.save(L / f"cor{j}.npy", a.astype(np.float32))
    b = lambda sg: blur(h2, sg * CS / 17.6)
    halo = (b(14) * 0.9 + b(46) * 0.8 + b(130) * 0.55 + b(300) * 0.3) * 0.2 * (0.5 + 0.9 * st)
    np.save(L / "halo.npy", halo.astype(np.float32))
    np.save(L / "red.npy", (b(10) * (1 - h2)).astype(np.float32))
    print("layers done")


def screen_layers():
    """Everything fixed to the frame at the end: the wall with its type, the pocket and 048, the ground."""
    y, x = grid()
    S2 = ART.parent / "S2plus/public"
    grain = noise(5, 8, slope=0.6)
    drift = noise(6, 420, slope=2.2)
    wall = 0.475 + 0.03 * (drift - 0.5) + 0.012 * (grain - 0.5) - 0.05 * (x / W)
    ink = np.zeros_like(wall)
    w2 = wall.copy()
    for s, sz, pos, wg in (("Enzyme IC50", 58, (84, 176), 700), ("048 =", 112, (80, 300), 900), ("33.4 ± 22.6 nM", 122, (78, 462), 900),
                           ("Just this much cuts the enzyme's", 46, (84, 610), 500), ("activity in half.", 46, (84, 672), 500)):
        w2 = put(w2, text(s, sz, pos, wg), 0.0)
    w2 = tag(w2, x, y, "measured", "MEASURED · Ren 2023, Fig. 9A", 84, 800, size=40, weight=700, ink=0.0, ground=0.47)
    tagd = tag(np.zeros_like(wall), x, y, "docked", "OUR RE-DOCKING", 1270, 980, size=40, weight=700, ink=0.93, ground=0.0)
    tagd_a = tag_box(x, y, "OUR RE-DOCKING", 1270, 980, 40, 700)
    tag4 = tag(np.zeros_like(wall), x, y, "predicted", "AlphaFold DB v6 · predicted", 72, 1006, size=38, weight=500, ink=0.94, ground=0.0)
    tag4_a = tag_box(x, y, "AlphaFold DB v6 · predicted", 72, 1006, 38, 500)
    # crowd
    rng = np.random.default_rng(14)
    ppl = np.zeros((H, W), np.float32)
    for cxx, nn in ((300, 5), (520, 2), (1390, 3), (1560, 6)):
        for i in range(nn):
            ppl = np.maximum(ppl, person(x, y, cxx + rng.normal(0, 30), 930 + 2 + rng.random() * 8, rng.uniform(34, 42)))
    grey = np.asarray(Image.open(S2 / "pose_048_grey.png").convert("RGBA"), np.float32) / 255
    lig = np.asarray(Image.open(S2 / "pose_048_lig.png").convert("RGBA").resize((1920, 2160), Image.LANCZOS), np.float32) / 255
    return dict(t3=np.load(L / "t3.npy"), wall=wall, wtxt=w2, tagd=tagd, tagd_a=tagd_a, tag4=tag4, tag4_a=tag4_a, ppl=ppl, ga=grey[..., 3], gl=grey[..., 0], la=lig[..., 3], ll=lig[..., 0])


def fb(a, sg):
    """Soft blur at reduced size: the per-frame blurs are all wide, and this keeps a frame in seconds."""
    f = min(8, max(1, int(round(sg / 1.5))))
    if f == 1:
        return blur(a, sg)
    h_, w_ = a.shape
    sm = np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w_ // f, h_ // f), Image.BOX), np.float32)
    sm = blur(sm, sg / f)
    return np.asarray(Image.fromarray(sm, "F").resize((w_, h_), Image.BILINEAR), np.float32)


class World:
    def __init__(self, k=1.0):
        self.k = k
        self.w, self.h = int(W * k), int(H * k)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.x, self.y = (xx + 0.5) / k - 0.5, (yy + 0.5) / k - 0.5
        self.A = {n: np.load(L / f"{n}.npy", mmap_mode="r" if K4 else None) for n in ("hard", "surf", "limb", "vall", "cor0", "cor1", "cor2", "halo")}
        if K4:
            self.S = {n: np.load(L / f"s_{n}.npy", mmap_mode="r") for n in ("t3", "wtxt", "tagd", "tagd_a", "tag4", "tag4_a", "ppl", "ga", "gl", "la", "ll")}
        else:
            self.S = screen_layers()
        self.u = {n: (1 if n in ("ga", "gl") or not K4 else 2) for n in self.S}
        lv = np.linspace(0, 1, 4096, dtype=np.float32)
        self.lw, self.lc = band(lv), cold(lv)
        self.dith = np.random.default_rng(3).random((self.h, self.w, 1), dtype=np.float32) - 0.5
        sky = 0.33 + 0.12 * np.exp(-np.hypot(self.x - 966, self.y - 462) / 520) + 0.05 * np.exp(-np.hypot(self.x - 966, self.y - 462) / 260)
        self.sky = sky.astype(np.float32)

    def scr(self, n, X, Y):
        """Sample a frame-fixed layer, given 1080p coordinates, at whatever size it was built."""
        u = self.u[n]
        return sample(self.S[n], u * X + (u - 1) / 2, u * Y + (u - 1) / 2)

    def camera(self, s):
        u = ease(9.2, 13.8, s)
        Sc = lp(17.0, 17.6, ease(0, 8.0, s)) if s < 9.2 else lp(17.6, 26.0, u)
        return Sc, 96.0 * u, lp(960, 1730, u), lp(452, 540, u)

    def offset(self, s):
        """Where the surface sits relative to the sun, in Angstrom. It stops just short so the disc is fully hidden, then creeps until the real gaps pass over the sun's edge."""
        a = ease(0, 3.2, s)
        xo = lp(52.0, OFF_B[0], a)
        yo = lp(0.0, OFF_B[1], a)
        c = ease(4.6, 7.6, s)
        return np.array([lp(xo, 0, c), lp(yo, 0, c)])

    def frame(self, real):
        s = real if real < 4.0 else 4.0 if real < 4.0 + HOLD else real - HOLD
        x, y, k = self.x, self.y, self.k
        A, S_ = self.A, self.S
        Sc, th, cx, cy = self.camera(s)
        c, sn = np.cos(np.radians(-th)), np.sin(np.radians(-th))
        ux, uy = (x - cx) / Sc, -(y - cy) / Sc
        wx, wy = c * ux - sn * uy, sn * ux + c * uy        # world Angstrom
        off = self.offset(s)
        bx, by = wx - off[0], wy - off[1]                  # surface Angstrom
        mx, my = bx * MS + MW / 2, -by * MS + MW / 2
        qx, qy = bx * CS + CW / 2, -by * CS + CW / 2
        h = sample(A["hard"], mx, my)

        # the sun, and what the surface lets through
        sd = np.hypot(wx - SUN[0], wy - SUN[1])
        disc = sstep(RS + 1.5 / Sc, RS - 1.5 / Sc, sd)
        leak = disc * (1 - h) * (1 - ease(12.0, 13.2, s))
        # no offset hides the disc outright, the real gaps are too deep, so the sun itself goes out through totality and comes back at the first gap, then the second
        dg1 = np.hypot(bx - G1[0], by - G1[1])
        rl = lp(0, 42, ease(4.9, 6.8, s))
        gate = (1 - ease(2.5, 3.1, s)) + (sstep(rl, rl - 7, dg1) if rl > 0 else 0)
        leak = leak * gate
        vis = float((disc * (1 - h)).sum() / max(disc.sum(), 1)) * (1 - ease(2.5, 3.1, s))
        night = 1 - ease(0.2, 3.0, s)                      # the red drains as the sun goes; nothing to do with the leak later
        t = self.sky * night ** 1.3
        ai = np.zeros_like(t)

        # bare sun early on: pearl
        if s < 3.8:
            sg = np.clip(np.exp(-np.maximum(sd - RS, 0) * Sc / 70), 0, 1) * (1 - disc) * vis
            t = np.clip(t + sg * 0.22, 0, 1)
            ai = np.maximum(ai, np.clip(sg * 1.5, 0, 1))
            t = put(t, leak, 1.0)
            ai = np.maximum(ai, sstep(0.0, 0.05, leak))

        # the burst: a front runs out from the two real gaps along the surface, the corona follows it
        rho = lp(0, 95, ease(5.5, 8.0, s))
        dg = np.minimum(np.hypot(bx - G1[0], by - G1[1]), np.hypot(bx - G2[0], by - G2[1]))
        rev = sstep(rho, rho - 14, dg) if rho > 0 else np.zeros_like(dg)
        cg = 1 - ease(10.6, 13.0, s)
        pulse = 1 + 0.5 * ease(5.8, 6.8, s) * (1 - ease(6.8, 8.2, s))
        if rho > 0 and cg > 0:
            a0, a1, a2 = ease(5.5, 6.6, s), ease(5.9, 7.3, s), ease(6.4, 8.0, s)
            Lc = (sample(A["cor0"], qx, qy) * a0 + sample(A["cor1"], qx, qy) * a1 + sample(A["cor2"], qx, qy) * a2 + sample(A["halo"], qx, qy) * a1) * rev * cg * pulse
            tc = expose(Lc, 2.6)
            t = np.clip(t + tc, 0, 1)
            ai = np.maximum(ai, sstep(0.0, 0.03, tc))

        # wall: a soft light front crosses the frame from the left, red comes up behind the type that was already there
        f = lp(-420, 1900, ease(11.0, 13.9, s))
        Fx = sstep(f + 260, f - 260, x)
        wv = Fx * sstep(1440, 1380, x)
        if wv.max() > 0:
            dr = 70 * (1 - ease(10.9, 14.6, s))
            wa = self.scr("wtxt", x + dr, y)
            t = t * (1 - wv) + wa * wv
            ai = ai * (1 - wv)

        # the mass
        Ls = sample(A["surf"], mx, my)
        pu2 = 1 + 0.25 * (pulse - 1)
        ts = expose((0.012 + Ls) * rev * pu2, 2.6)       # before the front arrives the surface is pure black: its shape is not known yet
        if wv.max() > 0:
            ts = ts * (1 - Fx) + sample(A["limb"], mx, my) * Fx
        t = t * (1 - h) + ts * h
        ai = ai * (1 - h) + h

        # beads in the gaps
        if s >= 3.0 and leak.max() > 0:
            # the true surface is a little tighter than the 1080p splat, so the real gaps let more through: the bloom is held down to match
            b = (fb(leak, 3 * k) * 2.5 + fb(leak, 12 * k) * 7 + fb(leak, 40 * k) * 12) * (0.45 if K4 else 1.0)
            Lb = leak * 40 + b * (1 - 0.5 * h)
            tb = expose(Lb, 2.6)
            t = np.clip(t + tb, 0, 1)
            ai = np.maximum(ai, sstep(0.0, 0.04, tb))

        # as the wall arrives the light stays only in the valleys of the outline
        vg = ease(12.2, 13.6, s)
        if vg > 0:
            v = sample(A["vall"], mx, my) * sstep(120, 200, y) * sstep(1040, 960, y) * vg
            gv = np.clip(fb(v, 3 * k) + fb(v, 14 * k) * 1.4 + fb(v, 46 * k) * 1.1, 0, 1) * (1 - h * 0.5)
            t = np.clip(t + v * 0.6 + gv * 0.42, 0, 1)
            ai = np.maximum(ai, np.clip(v + gv * 1.6, 0, 1))

        # 048 and the pocket: rigid, turning into place, the only thing with its own small rotation
        lg = ease(10.4, 12.0, s)
        if lg > 0:
            cc, ss_ = np.cos(np.radians(th)), np.sin(np.radians(th))
            px_ = cx + Sc * (cc * POCKET[0] - ss_ * POCKET[1])
            py_ = cy - Sc * (ss_ * POCKET[0] + cc * POCKET[1])
            land = ease(10.6, 13.6, s)
            ph = np.radians(-74 * (1 - land))
            ox_, oy_ = -260 * (1 - land), 40 * (1 - land)
            PS = 0.46 * Sc / 26
            dx_, dy_ = x - px_ - ox_, y - py_ - oy_
            cp, sp = np.cos(ph), np.sin(ph)
            sx = (cp * dx_ + sp * dy_) / PS + 1037
            sy = (-sp * dx_ + cp * dy_) / PS + 850
            la = self.scr("la", sx, sy)
            ll = self.scr("ll", sx, sy)
            pr = lp(0, 760, ease(13.0, 14.8, s))
            if pr > 0:
                g2 = self.scr("ga", (x - px_) / PS + 1037, (y - py_) / PS + 850) * sstep(pr, pr - 200, np.hypot(x - px_, y - py_)) * sstep(0.05, 0.5, h)
                gl2 = self.scr("gl", (x - px_) / PS + 1037, (y - py_) / PS + 850)
                t = t * (1 - g2) + (0.04 + 0.46 * gl2 ** 1.1) * g2
            hot = np.clip(fb(la, 4 * k) * 0.6 + fb(la, 18 * k) * 0.8 + fb(la, 55 * k) * 0.6, 0, 1)
            t = np.clip(t + hot * 0.30 * h * lg, 0, 1)
            t = put(t, la * lg, 0.78 + 0.22 * ll)
            ai = np.maximum(ai, la)
        wd = ease(14.0, 15.0, s)
        if wd > 0:
            wipe = sstep(1270 + 480 * wd, 1270 + 480 * wd - 60, x)
            a_ = self.scr("tagd_a", x, y) * wipe
            t = put(t, a_, self.scr("tagd", x, y))
            ai = np.maximum(ai, a_)

        # ground: leaves the frame as the camera lifts before it rolls
        gd = 340 * ease(9.2, 10.6, s)
        hz = 930 + gd
        if hz < H + 2:
            g = sstep(hz - 1, hz + 1, y)
            fl = 2 * hz - y
            ms = sstep(1080 + gd, hz, y) ** 1.2 * 0.5
            mt = fb(sample(t, fl * k, x * k) if False else sample(t, x * k, fl * k), 3 * k) * ms
            mi = sample(ai, x * k, fl * k)
            t = t * (1 - g) + g * mt
            ai = ai * (1 - g) + g * mi
            pp = self.scr("ppl", x, y - gd)
            pp = pp * (1 - ease(2.6, 3.4, s) * (1 - ease(5.6, 6.8, s)))     # at totality even the crowd is gone; the warm comes back with the first light
            t = put(t, pp, 0.66)
            ai = ai * (1 - pp)
            tv = ease(7.6, 8.5, s)
            if tv > 0:
                wipe = sstep(72 + 640 * tv, 72 + 640 * tv - 40, x)
                a_ = self.scr("tag4_a", x, y - gd) * wipe
                t = put(t, a_, self.scr("tag4", x, y - gd))
                ai = np.maximum(ai, a_)
        # totality: T3 itself, over everything. The surface is black on black, so nothing of its shape shows yet. Its one ring goes out when the first light arrives
        g3 = ease(2.7, 3.7, real) * (1 - ease(4.9 + HOLD, 5.8 + HOLD, real))
        if g3 > 0:
            a3 = self.scr("t3", x, y) * g3
            ai = ai * (1 - np.clip(a3 * 8, 0, 1) * (a3 > t))
            t = np.maximum(t, a3)
        idx = (np.clip(t, 0, 1) * 4095 + 0.5).astype(np.int32)
        a3_ = ai[..., None]
        rgb = self.lw[idx] * (1 - a3_) + self.lc[idx] * a3_
        return np.clip(rgb + self.dith / 255, 0, 1)


def find_hidden():
    """Smallest offset of the surface at which the sun's disc is completely hidden."""
    h = np.load(L / "hard.npy")
    n = 900
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    wx, wy = (xx - n / 2) * 0.1 + SUN[0], -(yy - n / 2) * 0.1 + SUN[1]
    d = np.hypot(wx - SUN[0], wy - SUN[1]) < RS
    best = None
    for r_ in np.arange(0, 12, 0.5):
        for an in np.arange(0, 360, 15):
            o = r_ * np.array([np.cos(np.radians(an)), np.sin(np.radians(an))])
            v = sample(h, (wx - o[0]) * MS + MW / 2, -(wy - o[1]) * MS + MW / 2)
            lk = float((d * (1 - v)).sum())
            if lk < 1:
                return o, r_
    return None, None


OFF_B = np.array([4.0, 3.0])
_o = L / "off_b.npy"
if _o.exists():
    OFF_B = np.load(_o)


def master(i):
    """Index of the frame this 60 fps frame repeats: nothing moves through the held totality, or after the last settle."""
    if 240 <= i <= 288:
        return 240
    return min(i, 954)


def to8(rgb):
    return Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
        o, r_ = find_hidden()
        print("hidden offset", o, r_)
        if o is not None:
            np.save(_o, o)
    if cmd == "sheet":                    # contact sheet to check the motion, one row of stops
        k = float(sys.argv[2])
        wd = World(k)
        ss = [float(v) for v in sys.argv[3].split(",")]
        ims = []
        t0 = time.time()
        for s in ss:
            ims.append(to8(wd.frame(s)))
        print("frame s", (time.time() - t0) / len(ss))
        cols = 4
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (ims[0].width * cols, ims[0].height * rows))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * im.width, (i // cols) * im.height))
        sh.save(WORK / "sheet.png")
    if cmd == "render":                   # render <k> <fps> <part> <parts> <outdir>
        k, fps, part, parts = float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        out = WORK / sys.argv[6]
        out.mkdir(exist_ok=True)
        wd = World(k)
        n = int(DUR * fps)
        for i in range(part, n, parts):
            f = out / f"{i:04d}.png"
            if f.exists():
                continue
            to8(wd.frame(i / fps)).save(f, compress_level=1)
        print("part done", part)
    if cmd == "render60":                 # render60 <part> <parts> [first last]: 4K60. Frames that repeat an earlier one are linked afterwards, not rendered
        part, parts = int(sys.argv[2]), int(sys.argv[3])
        out = WORK / "f4k"
        out.mkdir(exist_ok=True)
        n = int(round(DUR * 60))
        a, b = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 4 else (0, n)
        todo = [i for i in range(a, b) if i == master(i)]
        wd = World(2.0)
        t0 = time.time()
        done = 0
        for i in todo[part::parts]:
            f = out / f"{i:04d}.png"
            if f.exists():
                continue
            to8(wd.frame(i / 60)).save(f, compress_level=1)
            done += 1
        print("part done", part, "frames", done, "s per frame", (time.time() - t0) / max(done, 1), flush=True)
    if cmd == "link60":
        out = WORK / "f4k"
        n = int(round(DUR * 60))
        for i in range(n):
            m_ = master(i)
            if m_ != i and not (out / f"{i:04d}.png").exists():
                os.link(out / f"{m_:04d}.png", out / f"{i:04d}.png")
        print("frames", len(list(out.glob("*.png"))))
    if cmd == "still":                    # still <s> <name>
        wd = World(1.0)
        to8(wd.frame(float(sys.argv[2]))).save(STILLS / sys.argv[3])
