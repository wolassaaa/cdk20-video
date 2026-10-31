"""HKBU SCIE1007 coursework science video. Style scout a6, cubism: five real views of the CDK20 surface share one picture, cut into planes that each keep their own light."""
from kit import *

SS = 2
w, h = W * SS, H * SS
rng = np.random.default_rng(12)
VIEWS = [  # rotation, centre x, centre y, scale
    (rot(0, 0, 0), 650, 372, 12.4),      # front
    (rot(0, 74, 0), 610, 362, 12.4),     # one profile
    (rot(0, -74, 0), 700, 376, 12.4),    # other profile
    (rot(78, 0, 0), 640, 352, 12.4),     # from above
    (rot(-66, 20, 0), 650, 390, 12.4),   # from below
]
T, M, E = [], [], []
for Rk, cx, cy, s in VIEWS:
    V = view(Rk @ base_view(), scale=s * SS, cx=cx * SS, cy=cy * SS, w=w, h=h, ss=0.35, L=(-0.75, 0.55, 0.4))
    t = np.clip(0.05 + 1.15 * V["key"] ** 1.0, 0, 1) * (0.32 + 0.68 * V["ao"] ** 1.3)
    T.append(np.clip(t + 0.12 * V["rim"], 0, 1))
    M.append(V["mask"])
    edge = np.abs(fft_blur(V["mask"], 1.5 * SS) - 0.5) < 0.16
    E.append(edge.astype(np.float32) * (fft_blur(V["mask"], 1.5 * SS) > 0.2))


def clip(poly, px, py, nx, ny):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da = (a[0] - px) * nx + (a[1] - py) * ny
        db = (b[0] - px) * nx + (b[1] - py) * ny
        if da >= 0:
            out.append(a)
        if da * db < 0:
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def area(p):
    x, y = np.array(p).T
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


shards = []
ANGS = [14, 62, 76, 104, 118, 166, 90, 38]


def split(p):
    c = np.mean(p, 0)
    r = np.hypot((c[0] - 640) / 640, (c[1] - 360) / 360)
    lim = 11000 + 46000 * smooth(np.array(r), 0.3, 1.0)
    if area(p) < lim * rng.uniform(0.7, 1.5):
        shards.append(p)
        return
    th = np.radians(rng.choice(ANGS) + rng.normal(0, 5))
    nx, ny = np.sin(th), -np.cos(th)
    px, py = c + rng.normal(0, 24, 2)
    a = clip(p, px, py, nx, ny)
    b = clip(p, px, py, -nx, -ny)
    if len(a) >= 3 and len(b) >= 3 and min(area(a), area(b)) > 400:
        split(a)
        split(b)
    else:
        shards.append(p)


split([(-30, -30), (W + 30, -30), (W + 30, H + 30), (-30, H + 30)])
print(len(shards), "planes")

ids = Image.new("I", (w, h), 0)
d = ImageDraw.Draw(ids)
for i, p in enumerate(shards):
    d.polygon([(x * SS, y * SS) for x, y in p], fill=i + 1)
ids = np.asarray(ids)

STOPS = {
    "ochre": np.array([(26, 20, 15), (82, 58, 36), (156, 116, 66), (208, 174, 116), (236, 220, 180)], np.float32),
    "grey": np.array([(24, 24, 24), (70, 70, 66), (128, 124, 110), (186, 178, 156), (226, 218, 196)], np.float32),
    "dark": np.array([(14, 12, 12), (44, 32, 24), (88, 62, 40), (132, 96, 60), (182, 146, 98)], np.float32),
    "blue": np.array([(18, 22, 26), (46, 56, 62), (88, 102, 106), (142, 150, 142), (204, 204, 182)], np.float32),
}


def pal(name, v):
    st = STOPS[name]
    v = np.clip(v, 0, 1) * 4
    return np.stack([np.interp(v, np.arange(5), st[:, i]) for i in range(3)], -1)


yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
xx /= SS
yy /= SS
canvas = np.zeros((h, w, 3), np.float32)
Ledge = Layer(ss=2)
Lpale = Layer(ss=2)
for i, p in enumerate(shards):
    c = np.mean(p, 0)
    sel = ids == i + 1
    if not sel.any():
        continue
    # which view this plane looks through depends on where it sits, with some planes crossing over
    zone = [abs(c[0] - 640) / 150 + abs(c[1] - 366) / 110, abs(c[0] - 400) / 150 + abs(c[1] - 370) / 240, abs(c[0] - 880) / 150 + abs(c[1] - 370) / 240, abs(c[1] - 170) / 90 + abs(c[0] - 640) / 300, abs(c[1] - 570) / 90 + abs(c[0] - 640) / 300]
    k = int(np.argmin(np.array(zone) + rng.uniform(0, 0.55, 5)))
    dx, dy = (rng.normal(0, 3, 2) * SS).astype(int)
    t = np.roll(np.roll(T[k], dy, 0), dx, 1)[sel]
    m = np.roll(np.roll(M[k], dy, 0), dx, 1)[sel]
    th = rng.uniform(0, 2 * np.pi)
    ext = np.sqrt(area(p)) * 0.9
    g = ((xx[sel] - c[0]) * np.cos(th) + (yy[sel] - c[1]) * np.sin(th)) / ext
    r_ = np.hypot((c[0] - 640) / 640, (c[1] - 360) / 360)
    inside = m.mean() > 0.35
    name = rng.choice(["ochre", "grey", "blue"], p=[0.68, 0.2, 0.12]) if inside else rng.choice(["dark", "grey", "ochre"], p=[0.72, 0.14, 0.14])
    fig = 0.10 + 0.98 * t
    bg = 0.20 + 0.09 * rng.uniform(-1, 1)
    val = m * fig + (1 - m) * bg + g * (0.22 * m + 0.42 * (1 - m))
    canvas[sel] = pal(name, val)
    n = len(p)
    for e in range(n):
        a, b = p[e], p[(e + 1) % n]
        u = rng.random()
        if u < 0.42:
            Ledge.line([a, b], rng.uniform(1.6, 3.6))
        elif u < 0.56:
            Lpale.line([a, b], rng.uniform(1.0, 2.2))

rgb = np.asarray(Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS), np.float32) / 255
# the brush: small tilted dabs over everything, the pale edge lines scumbled
y1, x1 = np.mgrid[0:H, 0:W].astype(np.float32)
u = (x1 * 0.8 + y1 * 0.6) / 7
v = (-x1 * 0.6 + y1 * 0.8) / 3.2
cell = np.random.default_rng(3).random((512, 512)).astype(np.float32)
dab = cell[np.floor(v).astype(int) % 512, (np.floor(u + 0.5 * np.floor(v)).astype(int)) % 512] - 0.5
dab = fft_blur(dab, 0.6)
rgb = np.clip(rgb * (1 + 0.14 * dab[..., None]), 0, 1)
rgb = ink(rgb, Lpale.a() * 0.5, (226, 208, 166))
outline = resize(np.maximum.reduce(E), W, H)
rgb = ink(rgb, np.clip(outline * 0.75, 0, 1), (16, 12, 10))
rgb = ink(rgb, Ledge.a() * 0.86, (18, 13, 10))

# stencil letters, the bridges left unpainted, on a dark plane that sits flat on the picture
plane = Layer().poly([(40, 96), (486, 34), (500, 176), (54, 226)]).a()
rgb = ink(rgb, plane * 0.94, (28, 22, 18))
St = Layer()
a0 = np.degrees(np.arctan2(-62, 446))
for i, ch in enumerate("CDK20"):
    T_ = affine(62 + i * 84.5, 104 - i * 11.8, 72, 104, a0)
    for s, pl in glyph_pts(ch, T_):
        St.poly(pl, 255 if s > 0 else 0)
    b0, b1 = T_(0.40, -0.05), T_(0.60, -0.05)
    b2, b3 = T_(0.60, 1.05), T_(0.40, 1.05)
    if ch in "D20":
        St.poly([T_(-0.05, 0.47), T_(1.05, 0.47), T_(1.05, 0.53), T_(-0.05, 0.53)], 0)
    if ch == "C":
        St.poly([T_(-0.05, 0.47), T_(0.40, 0.47), T_(0.40, 0.53), T_(-0.05, 0.53)], 0)
    if ch == "K":
        St.poly([T_(-0.05, 0.47), T_(0.34, 0.47), T_(0.34, 0.53), T_(-0.05, 0.53)], 0)
st = St.a()
rgb = ink(rgb, st * (0.94 + 0.06 * np.clip(noise(s=1.2, seed=8), -1, 1)), (232, 212, 168))

# pasted paper for the label
pp = Layer().poly([(836, 628), (1236, 604), (1242, 664), (842, 688)]).a()
rgb = rgb * (1 - 0.5 * np.clip(shadow_of(pp, 3, 4, 2.5), 0, 1)[..., None])
newsprint = paper((226, 214, 186), 15, mott=0.012, fibre=0.02)
rgb = rgb * (1 - pp[..., None]) + newsprint * pp[..., None]
rgb = ink(rgb, text_rot("AlphaFold DB v6 · predicted", "timesbd.ttf", 28, 3.4, 1039, 648, track=0.4), (20, 16, 14))
save(rgb, "a6_cubism.png")
