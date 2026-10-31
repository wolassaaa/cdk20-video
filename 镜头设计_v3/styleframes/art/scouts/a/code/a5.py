"""HKBU SCIE1007 coursework science video. Style scout a5, futurism and chronophotography: the real CDK20 surface turns and rushes at the lens, ten exposures on one plate. Force lines and the flat colour bands all follow the paths of real CA atoms."""
from kit import *

A = atoms()
N = 10


def pose(t):
    e = t**1.5
    R = rot(0, -120 + 120 * t, -30 + 30 * t) @ rot(-18 + 18 * t, 0, 0) @ base_view()
    x = 92 + (925 - 92) * e
    y = 250 + (322 - 250) * e - 118 * np.sin(np.pi * e)
    s = 2.7 + (9.6 - 2.7) * t**1.7
    return R, s, x, y


acc = np.zeros((H, W, 3), np.float32)
cold, hot = np.array((0.20, 0.42, 1.0)), np.array((1.0, 0.36, 0.08))
for i in range(N):
    t = i / (N - 1)
    R, s, x, y = pose(t)
    V = view(R, scale=s, cx=x, cy=y, ss=min(0.6, 0.28 + 0.035 * s))
    m = V["mask"]
    nz = np.clip(V["normal"][..., 2], 0, 1)
    E = ((1 - nz) ** 1.5 + 0.10 * V["key"]) * m
    col = cold * (1 - t) ** 1.1 + hot * t**0.8 + 0.34 * t**5
    acc = acc * (1 - m[..., None] * 0.62) + E[..., None] * col * (0.62 + 0.75 * t)
    if i == N - 1:
        last = V

ts = np.linspace(0.0, 1, 110)
Pts = np.stack([project(A["ca"], *pose(t)) for t in ts], 1)  # residue, time, xyz

lines = Layer(ss=2)
for a_ in Pts[3::4]:
    lines.line(a_[:, :2].tolist(), 1.2)
acc += lines.a()[..., None] * np.array((1.0, 0.86, 0.6)) * 0.30

# Balla's divisionism: the whole plate becomes separate dabs of pure colour laid along the direction of travel
lum = fft_blur(acc.sum(2) / 1.6, 1.0)
warm = fft_blur(acc[..., 0], 2.0) / (fft_blur(acc[..., 0] + acc[..., 2], 2.0) + 1e-3)
rng = np.random.default_rng(4)
C = lambda *c: np.array(c, np.float32)
DARK = [C(14, 16, 44), C(20, 26, 70), C(12, 12, 28), C(30, 40, 104)]
COLD = [C(24, 40, 132), C(36, 84, 200), C(112, 168, 236), C(236, 240, 244)]
HOT = [C(120, 26, 22), C(216, 54, 24), C(244, 150, 30), C(250, 216, 96), C(252, 244, 224)]
ss = 2
im = Image.new("RGB", (W * ss, H * ss), (8, 8, 18))
dr = ImageDraw.Draw(im)
cw, ch = 12.0, 7.0
rows = int(H / ch) + 2
for r in range(rows):
    for c in range(int(W / cw) + 2):
        x = c * cw + (r % 2) * cw / 2 + rng.uniform(-1.5, 1.5)
        y = r * ch + rng.uniform(-1.0, 1.0)
        ix, iy = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
        l = np.clip(1 - np.exp(-1.7 * lum[iy, ix]) + rng.normal(0, 0.035), 0, 0.999)
        w_ = warm[iy, ix]
        if l < 0.10:
            col = DARK[rng.integers(0, len(DARK))]
        else:
            ramp = HOT if w_ > 0.56 + rng.normal(0, 0.05) else COLD
            col = ramp[int(((l - 0.10) / 0.9) ** 0.8 * len(ramp))]
        col = col * rng.uniform(0.93, 1.05)
        ang = np.radians(-17 + 27 * x / W)
        L_ = rng.uniform(6.2, 8.2)
        T_ = rng.uniform(2.4, 3.2)
        ca_, sa_ = np.cos(ang), np.sin(ang)
        pts = [(x + i * L_ * ca_ - j * T_ * sa_, y + i * L_ * sa_ + j * T_ * ca_) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        dr.polygon([(a0 * ss, b0 * ss) for a0, b0 in pts], fill=tuple(int(v) for v in np.clip(col, 0, 255)))
rgb = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255

# type: strobe outlines arrive from the left, then the hit
tw, th, gapx, ty = 86, 128, 100, 536
for j in range(6, -1, -1):
    x0 = 58 + (6 - j) * 25.0 - 0
    Tl = Layer(ss=2)
    block_word(Tl, "CDK20", lambda i: affine(x0 + i * gapx, ty, tw, th, shear=0.3))
    a = Tl.a()
    if j > 0:
        ed = np.clip(a - np.clip(fft_blur(a, 1.3) * 1.9 - 0.9, 0, 1), 0, 1)
        rgb = ink(rgb, ed * (0.92 - 0.1 * j), (232, 76, 28))
    else:
        rgb = ink(rgb, a * np.clip(fft_blur(a, 1.0) * 2, 0, 1), (250, 240, 222))

Rl = Layer(ss=2).rect(0, 703, W, 704.4)
for i in range(N):
    px = 92 + (925 - 92) * (i / (N - 1)) ** 1.5
    Rl.rect(px - 0.7, 690, px + 0.7, 703)
rgb = ink(rgb, Rl.a() * 0.85, (232, 226, 212))
rgb = ink(rgb, Layer().text((914, 682), "AlphaFold DB v6 · predicted", "arialbd.ttf", 23, track=0.4).a(), (250, 240, 222))
save(rgb, "a5_chronophotography.png")
