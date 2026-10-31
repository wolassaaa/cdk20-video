"""HKBU SCIE1007 coursework science video. Eclipse direction, T2: a team member seated and talking, phone footage, interview framing.
No footage of a seated person exists yet, so the figure is a plain capsule mannequin standing in for a phone frame. grade() is the actual treatment and takes any phone frame plus its matte.
During a partial eclipse every gap in the leaves throws a small crescent sun: that layer stays, but the face is kept clear."""
from ec import *

y, x = grid()
OC = np.load(WORK / "t6_mask.npy")


# ---------- the treatment, used unchanged on real footage ----------
def crescents(seed, keep):
    """Crescent light layer. keep(px, py) is True where crescents are allowed. Each bite is the same outline used in the roadmap."""
    Rc = 62

    def sprite(r, soft):
        n = int(r * 2 + 30)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        c = n / 2
        disc = sstep(r + 1, r - 1, np.hypot(xx - c, yy - c))
        k = 0.62 * r / 112
        sh = sample(OC, (xx - c - r * 1.34) / k + 480, (yy - c - r * 0.1) / k + 480)
        return kit.fft_blur(disc * (1 - sh), soft)

    rng = np.random.default_rng(seed)
    sprites = [sprite(Rc * sc, b) for sc in (0.72, 0.86, 1.0, 1.16) for b in (2.0, 3.5, 6.5)]
    D = np.zeros((H, W), np.float32)
    pts = []
    tries = 0
    while len(pts) < 200 and tries < 20000:
        tries += 1
        px, py = rng.uniform(-40, W + 40), rng.uniform(-40, H + 40)
        if not keep(px, py) or any((px - a) ** 2 + (py - b) ** 2 < (Rc * 1.4) ** 2 for a, b in pts):
            continue
        pts.append((px, py))
    for px, py in pts:
        s_ = sprites[rng.integers(0, len(sprites))]
        h_, w_ = s_.shape
        x0, y0 = int(px - w_ / 2), int(py - h_ / 2)
        x1, y1 = min(x0 + w_, W), min(y0 + h_, H)
        ax, ay = max(x0, 0), max(y0, 0)
        if x1 > ax and y1 > ay:
            D[ay:y1, ax:x1] += s_[ay - y0:y1 - y0, ax - x0:x1 - x0] * rng.uniform(0.5, 1.0)
    canopy = blur(noise(seed + 33, 520, slope=3.0), 46)
    canopy = sstep(0.42, 0.6, (canopy - canopy.min()) / (canopy.max() - canopy.min()))
    return D * (0.06 + 0.94 * canopy)


def grade(Y, matte, D, faces):
    """Y: luminance of the phone frame, 0..1. matte: person, from Roto Brush. D: crescent layer. faces: list of (cx, cy, rx, ry), tracked.
    Returns band positions. The person takes the whole warm range up to gold, the room is pushed down to black and deep red."""
    # edge: pull in 2 px so the old background does not fringe, then feather 3 px
    m = sstep(0.5, 1.0, blur(matte, 2.0))
    m = blur(m, 3.0)
    # person: levels so the skin midtone lands in the gold, then the warm rail does the rest
    lo, hi = np.percentile(Y[m > 0.9], [2, 99.5])
    p = np.clip((Y - lo) / (hi - lo), 0, 1) ** 0.8
    tp = 0.07 + 0.80 * p
    # room: one stop of crushed contrast, nothing may leave the red
    tb = np.minimum(0.03 + 0.22 * np.clip(Y, 0, 1) ** 1.3, RED_TOP - 0.2)
    # the room's red wraps a few pixels round the person, so the cut sits in the space
    wrap = blur(tb * (1 - m), 9) / (blur(1 - m, 9) + 1e-3)
    tp = tp * (1 - 0.28 * (1 - blur(m, 9)) * m) + wrap * 0.28 * (1 - blur(m, 9)) * m
    # crescents: last. On the room they stay red. On the body gold. Never on a face
    clear = np.ones_like(Y)
    for cx, cy, rx, ry in faces:
        clear = clear * sstep(0.85, 1.25, np.hypot((x - cx) / rx, (y - cy) / ry))
    f = 1 - np.exp(-D * 1.8)
    tb = np.minimum(tb + 0.12 * f, RED_TOP - 0.02)
    tp = np.minimum(tp + 0.55 * f * clear * (1 - 0.4 * sstep(0.3, 0.7, tp)), 0.9)
    return tb * (1 - m) + tp * m, m


if __name__ == "__main__":
    # ---------- placeholder phone frame. Drawn: a seated person in dark clothes, side-on, medium shot, turned toward the question ----------
    def spline(pts, n=24):
        p = np.array(pts, float)
        p = np.vstack([p[-1], p, p[0], p[1]])
        out = []
        for i in range(1, len(p) - 2):
            a, b, c, d = p[i - 1:i + 3]
            for u in np.linspace(0, 1, n, endpoint=False):
                out.append(0.5 * (2 * b + (c - a) * u + (2 * a - 5 * b + 4 * c - d) * u ** 2 + (3 * b - a - 3 * c + d) * u ** 3))
        return [tuple(q) for q in out]

    def poly(pts, ss=2, smooth=True):
        im = Image.new("L", (W * ss, H * ss), 0)
        ImageDraw.Draw(im).polygon([(a * ss, b * ss) for a, b in (spline(pts) if smooth else pts)], fill=255)
        return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255

    S_, X0, Y0_ = 0.74, 1716, 112

    def M(pts):
        return [(X0 - (u - 60) * S_, Y0_ + (v - 196) * S_) for u, v in pts]

    FIG = [(470, 196), (540, 204), (592, 238), (616, 286), (610, 318), (628, 350), (648, 386), (634, 398), (620, 404), (630, 424), (618, 438), (628, 456),
           (612, 474), (618, 502), (590, 530), (540, 540), (526, 590), (548, 640), (640, 690), (740, 760), (800, 900), (850, 1200), (880, 1500), (0, 1500), (30, 1200), (70, 880), (130, 750),
           (280, 668), (362, 610), (372, 548), (330, 452), (316, 366), (338, 278), (398, 216)]
    HAIR = [(470, 186), (548, 196), (604, 240), (590, 262), (540, 262), (492, 290), (452, 340), (432, 410), (424, 480), (412, 548), (362, 604), (368, 540),
            (318, 450), (304, 362), (328, 268), (392, 206)]
    COLLAR = [(526, 600), (548, 640), (640, 690), (760, 770), (850, 1200), (880, 1500), (0, 1500), (30, 1200), (50, 880), (120, 740), (280, 660), (372, 610), (430, 650), (490, 650)]
    SLEEVE = [(250, 760), (330, 900), (390, 1100), (460, 1270), (640, 1310), (700, 1400), (420, 1420), (300, 1300), (190, 1060)]
    fig = poly(M(FIG))
    hair = poly(M(HAIR)) * fig
    shirt = poly(M(COLLAR)) * fig
    sleeve = poly(M(SLEEVE)) * fig
    ear = sstep(1.2, -1.2, np.hypot((x - (X0 - (448 - 60) * S_)) / (24 * S_), (y - (Y0_ + (410 - 196) * S_)) / (38 * S_)) - 1) * fig
    skin = fig * (1 - hair) * (1 - shirt)

    # round the flat shape so the side light has something to fall on
    hgt = blur(fig, 26) + 0.5 * blur(fig, 9) + 0.5 * blur(fig * (1 - shirt), 14)
    gy, gx = np.gradient(hgt)
    nx, ny = -gx * 30, -gy * 30
    nz = 1 / np.sqrt(1 + nx ** 2 + ny ** 2)
    nx, ny = nx * nz, ny * nz
    key = np.clip(-0.78 * nx - 0.30 * ny + 0.32 * nz, 0, 1)
    edge = np.clip(nx, 0, 1) ** 2.5
    folds = blur(noise(44, 260, slope=2.4), 6)
    Ys = 0.26 + 0.52 * key
    Yh = 0.07 + 0.09 * key + 0.05 * blur(noise(45, 30, slope=1.3), 1.5)
    Yc = 0.06 + 0.15 * key + 0.05 * (folds - 0.5)
    Y0 = Ys * skin + Yh * hair + Yc * shirt
    Y0 = put(Y0, ear * (1 - blur(ear, 7) * 0.7), 0.36)
    Y0 = Y0 + 0.0 * edge

    # room behind: plain wall in late light, chair back, a door edge. Enough to read as a room shot on a phone
    wall = 0.44 + 0.22 * sstep(1900, 100, x) - 0.10 * sstep(200, 1000, y) + 0.05 * (noise(42, 700, slope=2.4) - 0.5)
    door = box(x, y, 1856, 0, 1920, 1080)
    Yb = wall * (1 - door) + 0.24 * door
    Yb = put(Yb, box(x, y, 1838, 0, 1856, 1080), 0.60)
    Yb = Yb - 0.2 * blur(fig, 70)
    Yall = Y0 * fig + Yb * (1 - fig)

    FACE = [(X0 - (500 - 60) * S_, Y0_ + (370 - 196) * S_, 170, 200)]

    def keep(px, py):
        """No crescents where the question sits, none on the face."""
        return not (40 < px < 1090 and 700 < py < 1040) and not (1200 < px < 1660 and 80 < py < 470)

    D = crescents(8, keep)
    t, m = grade(Yall, fig, D, FACE)

    # the question, two lines would also fit: it sits low on the wall where the crescents stop
    LN = ["How can computer-aided methods", "help scientists find and assess", "potential cancer drug candidates?"]
    for i, ln in enumerate(LN):
        t = put(t, text(ln, 54, (84, 790 + i * 76), 700), 1.0)
    np.save(WORK / "t2_ref.npy", Yall)
    save(t, "T2.png")
