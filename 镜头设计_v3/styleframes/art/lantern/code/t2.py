"""HKBU SCIE1007 coursework science video. Lantern T2 (2-02): a speaker whose only light is the phone in their own hand. The question is cut out of the wedge the phone throws.
No clip of a member exists yet. The hand is a real frame of our own phone test clip (tests/T1_hand/hand_raw.mp4 at 7 s). The head is a labelled stand-in that goes through the same grade, phone_grade() in pg.py, the one every member clip would go through."""
from lk import *
from pg import load_hand, phone_grade


def spline(p, n=14, closed=True):
    p = np.array(p, np.float64)
    N = len(p)
    out = []
    rng_ = range(N) if closed else range(N - 1)
    for i in rng_:
        p0, p1, p2, p3 = p[(i - 1) % N], p[i], p[(i + 1) % N], p[(i + 2) % N]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3))
    return np.array(out)


HEAD = 392.0
OX, OY = 1236.0, 118.0
P = lambda pts: [(OX + x * HEAD, OY + y * HEAD) for x, y in pts]

head = [(0.52, 0.00), (0.30, 0.06), (0.205, 0.17), (0.178, 0.30), (0.205, 0.36), (0.155, 0.44), (0.095, 0.515), (0.115, 0.545), (0.17, 0.56), (0.15, 0.60), (0.142, 0.625), (0.18, 0.64), (0.155, 0.675), (0.165, 0.70), (0.195, 0.725), (0.165, 0.80), (0.20, 0.875), (0.30, 0.895), (0.36, 0.90), (0.37, 1.02), (0.34, 1.12), (0.24, 1.24), (0.17, 1.42), (0.14, 1.78), (0.14, 2.2), (1.56, 2.2), (1.50, 1.66), (1.32, 1.38), (1.04, 1.20), (0.88, 1.10), (0.86, 0.94), (0.97, 0.70), (0.99, 0.46), (0.92, 0.24), (0.76, 0.07)]
hair = [(0.52, -0.02), (0.30, 0.05), (0.205, 0.16), (0.235, 0.20), (0.36, 0.19), (0.45, 0.25), (0.50, 0.40), (0.60, 0.38), (0.66, 0.46), (0.70, 0.66), (0.78, 0.82), (0.90, 1.08), (0.96, 0.70), (1.0, 0.46), (0.93, 0.24), (0.76, 0.06)]


def mask(pts, n=14):
    return Layer(W, H, 2).poly(spline(P(pts), n).tolist()).a()


m_body, m_hair = mask(head), mask(hair)


def relief(m):
    h = 0.0
    for s, w_ in ((6, 0.34), (16, 0.40), (48, 0.26)):
        h = h + w_ * fft_blur(m, s) * s
    return h


def blob(cx, cy, sx, sy, a):
    x_, y_ = OX + cx * HEAD, OY + cy * HEAD
    return a * np.exp(-(((xx - x_) / (sx * HEAD)) ** 2 + ((yy - y_) / (sy * HEAD)) ** 2))


LX, LY = 1096.0, 640.0


def shade(hf, m, lamp_z=60.0, k=1.2):
    gy, gx = np.gradient(fft_blur(hf, 1.2))
    n = np.stack([-gx * k, -gy * k, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    lx, ly = LX - xx, LY - yy
    lz = lamp_z - hf * 0.45
    d = np.sqrt(lx * lx + ly * ly + lz * lz)
    ndl = np.clip((n[..., 0] * lx + n[..., 1] * ly + n[..., 2] * lz) / d, 0, 1)
    return ndl * (520.0 / (d + 160)) ** 1.9 * m


# ---------- the stand-in head: only a tone source for the grade, not a drawing to keep ----------
h = relief(m_body)
h = h + blob(0.30, 0.345, 0.09, 0.03, 3) + blob(0.335, 0.405, 0.04, 0.02, -3.5) + blob(0.68, 0.50, 0.05, 0.085, 5)
h = h + blob(0.20, 0.735, 0.05, 0.007, -2.5) + blob(0.16, 0.565, 0.016, 0.012, -4)
body = shade(h, m_body, 90.0, 1.5)
rng = np.random.default_rng(3)
n_ = np.asarray(Image.fromarray((rng.random((H // 2, W // 8)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
hair_tex = 0.62 + 0.7 * (n_ - 0.5)
shirt = smooth(yy, OY + 1.14 * HEAD, OY + 1.30 * HEAD)
alb = (1 - m_hair * (1 - 0.34 * hair_tex)) * (1 - 0.86 * shirt)
tone = fft_blur(body * alb, 1.3)
tone = tone + rng.normal(0, 1, (H, W)).astype(np.float32) * 0.012 * (tone > 0.01)  # the sensor noise of a dark room
tone_rgb = np.repeat(tone[..., None], 3, 2)

c = blank()
# the wedge leaves the long edge of the phone and fills the frame to the left, flat and hard
PH_ = 84.0
wedge = Layer(W, H, 2).poly([(LX, LY - PH_), (LX, LY + PH_), (LX - 1500, LY + 1500), (LX - 1500, LY - 1500)]).a()
c = lay(c, wedge, AMBER)
lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
tcov = np.zeros((H, W), np.float32)
for i, l in enumerate(lines):
    tcov = np.maximum(tcov, tx(l, 66, 800, 64, 540 + i * 94))
c = lay(c, tcov, BLACK)

REACH = 660.0  # the phone's hard limit. Past this nothing exists, background included
fig = phone_grade(tone_rgb, (LX, LY), REACH, d0=560.0, black=0.015, white=0.8, gamma=0.60)
cov = m_body[..., None]
c = c * (1 - cov) + fig * cov

# real hand, real pixels, same grade. Mirrored and turned so the thumb and finger hold the phone
hand_rgb, hand_a = load_hand(angle=-13.0, scale=0.86, tx_=1104.0, ty_=640.0)
hand_a = hand_a * (1 - smooth((xx - 1104) * 0.974 + (yy - 640) * 0.225, 130, 228))  # the wrist falls off into the dark, as it would with one lamp
hg = phone_grade(hand_rgb, (LX, LY), REACH, d0=420.0, black=0.05, white=0.92, gamma=0.8)
c = lay(c, np.clip(fft_blur(hand_a, 3.0) * 2.2, 0, 1) * (1 - hand_a) * 0.8 * m_body, BLACK)
# the phone seen edge on, behind the fingers
c = lay(c, Layer(W, H, 3).rect(LX, LY - PH_, LX + 20, LY + PH_).a(), np.array((14, 11, 9), np.float32) / 255)
c = lay(c, Layer(W, H, 3).rect(LX, LY - PH_, LX + 5, LY + PH_).a(), AMBER_HI)
c = c * (1 - hand_a[..., None]) + hg * hand_a[..., None]

c = lay(c, tx("placeholder: member's phone clip goes here", 36, 500, 1880, 1046, anchor="rs"), CHALK)
save(c, "T2.png")
