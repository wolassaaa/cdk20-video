"""HKBU SCIE1007 coursework science video. Style scout a7, German Expressionism: a crooked painted room, a wedge of door light, and the real CDK20 silhouette thrown up the wall as a giant shadow. Everything is painted light and painted dark."""
from kit import *

rng = np.random.default_rng(7)
VP = np.array((770.0, 236.0))
y, x = np.mgrid[0:H, 0:W].astype(np.float32)


def tri(a):
    return 2 * np.abs(a - np.floor(a + 0.5)) * 2 - 1


def polar_streaks(seed=1, k=380, rs=26.0):
    th = np.arctan2(y - VP[1], x - VP[0])
    r = np.hypot(x - VP[0], y - VP[1])
    t = np.random.default_rng(seed).standard_normal((64, k)).astype(np.float32)
    a = ((th + np.pi) / (2 * np.pi) * k).astype(int) % k
    b = np.clip((r / rs).astype(int), 0, 63)
    return fft_blur(t[b, a], 0.8)


G = np.full((H, W), 0.76, np.float32)  # wall wash


def lay(G, cov, v):
    return G * (1 - cov) + v * cov


# radiating painted shards on the walls
def shard(a0, da, r0, r1, bend=0.0):
    a0, da = np.radians(a0), np.radians(da)
    p0 = VP + r0 * np.array((np.cos(a0), np.sin(a0)))
    p1 = VP + r1 * np.array((np.cos(a0 - da), np.sin(a0 - da)))
    p2 = VP + r1 * np.array((np.cos(a0 + da), np.sin(a0 + da)))
    return [p0, p1, p2]


Wall_k = Layer(ss=2)
Wall_p = Layer(ss=2)
for i in range(22):
    a = rng.uniform(0, 360)
    Wall_k.poly(shard(a, rng.uniform(1.0, 4.2), rng.uniform(60, 300), 1500))
for i in range(30):
    a = rng.uniform(0, 360)
    Wall_p.poly(shard(a, rng.uniform(0.8, 3.2), rng.uniform(60, 300), 1500))
G = lay(G, Wall_k.a() * 0.82, 0.30)
G = lay(G, Wall_p.a() * 0.86, 0.90)

# the giant shadow: the true silhouette, sheared and stretched up and over the wall
R = rot(0, -8, -6) @ base_view()
V = view(R, scale=9.0, cx=742, cy=408, ss=0.6, L=(-0.72, -0.18, 0.66), L2=(0.5, 0.8, 0.2))
m = V["mask"]
X0, Y0, tx, ty, sx, sy, sh = 742.0, 600.0, 196.0, -36.0, 1.32, 1.34, 0.70
ys = Y0 + (y - Y0 - ty) / sy
xs = X0 + (x - X0 - tx - sh * (Y0 - ys)) / sx
tooth = 7 * tri(ys / 31 + 0.3 * noise(s=30, seed=3)) + 3 * tri(xs / 17)
msh = warp(m, xs - x + tooth, ys - y + 5 * tri(xs / 23))
msh = smooth(msh, 0.42, 0.58)

# crooked floor, slats that all run at the vanishing point
fl = Layer(ss=2).poly([(-10, 500), (1290, 438), (1290, 730), (-10, 730)]).a()
slats = Layer(ss=2)
for i in range(13):
    a = 8 + i * 13.2 + rng.uniform(-2, 2)
    slats.poly(shard(a, rng.uniform(1.6, 3.1), 200, 1800))
G = lay(G, msh * 0.985, 0.025)
G = lay(G, fl, 0.42)
G = lay(G, slats.a() * fl * 0.95, 0.06)

# door, tilted, burning white, and its wedge of light on the floor
door = Layer(ss=2).poly([(78, 196), (206, 96), (250, 500), (112, 572)]).a()
fr = Layer(ss=2).poly([(48, 214), (214, 56), (272, 512), (92, 610)]).a()
G = lay(G, fr, 0.03)
G = lay(G, door, 1.0)
wedge = Layer(ss=2).poly([(112, 572), (250, 500), (1290, 470), (1290, 730), (700, 730)]).a()
G = lay(G, wedge * fl * (0.97 - 0.32 * x / W), 0.97)
slat2 = slats.a() * wedge * fl
G = lay(G, slat2 * 0.55, 0.16)

# a small figure in the doorway, its shadow thrown along the wedge at the thing
fig = Layer(ss=2)
fig.poly([(164, 534), (152, 372), (140, 340), (164, 318), (168, 296), (182, 292), (190, 318), (214, 338), (202, 372), (196, 526)])
fig.poly([(186, 524), (172, 534), (574, 600), (566, 584)])
G = lay(G, fig.a(), 0.02)

# protein, hard door light, sawtooth edges
ton = np.clip(1.1 * V["key"] ** 0.8, 0, 1) * (0.30 + 0.70 * V["ao"])
dxx = 2.6 * tri(y / 15 + 0.5 * noise(s=26, seed=4)) + 1.0 * tri(y / 6)
dyy = 2.6 * tri(x / 18 + 0.5 * noise(s=26, seed=5)) + 1.0 * tri(x / 7)
mj = warp(m, dxx, dyy)
tj = warp(ton, dxx, dyy) + 0.05 * polar_streaks(9, 900, 12)
lv = (tj > 0.14).astype(np.float32) * 0.30 + (tj > 0.34).astype(np.float32) * 0.28 + (tj > 0.58).astype(np.float32) * 0.37
lv = fft_blur(lv, 0.7)
mj = smooth(mj, 0.40, 0.60)
G = lay(G, shadow_of(mj, 26, 16, 2) * fl * 0.86, 0.03)
G = lay(G, mj, 0.015 + lv)

# hand-cut title on the wall, leaning into the room
WEDGE = {
    "C": [[(0.10, 0.20), (1.08, -0.08), (0.90, 0.20), (0.34, 0.30)], [(-0.02, 0.26), (0.34, 0.12), (0.30, 0.86), (0.10, 1.0)], [(0.08, 0.76), (0.30, 0.70), (1.02, 0.90), (0.26, 1.08)]],
    "D": [[(0.00, -0.08), (0.34, 0.02), (0.28, 1.08), (0.04, 0.98)], [(0.10, 0.00), (0.74, 0.10), (1.06, 0.52), (0.70, 0.36), (0.12, 0.22)], [(1.02, 0.44), (0.74, 0.94), (0.06, 1.04), (0.12, 0.82), (0.62, 0.74)]],
    "K": [[(0.00, -0.08), (0.34, 0.02), (0.28, 1.08), (0.04, 0.98)], [(0.20, 0.54), (1.04, -0.12), (0.72, 0.40)], [(0.26, 0.46), (0.60, 0.46), (1.10, 1.12), (0.58, 0.84)]],
    "2": [[(0.00, 0.24), (0.40, -0.06), (1.02, 0.04), (0.86, 0.36), (0.40, 0.20)], [(1.00, 0.02), (0.86, 0.46), (-0.02, 1.08), (0.22, 0.70)], [(-0.02, 0.92), (1.12, 0.80), (0.88, 1.08), (0.00, 1.06)]],
    "0": [[(0.46, -0.08), (0.00, 0.42), (0.40, 1.08), (0.24, 0.46)], [(0.44, -0.08), (1.04, 0.50), (0.40, 1.08), (0.76, 0.48)]],
}
pan = Layer(ss=2).poly([(322, 44), (742, 8), (706, 176), (344, 206)]).a()
G = lay(G, pan * 0.96, 0.03)
T_ = Layer(ss=2)
for i, ch in enumerate("CDK20"):
    h_ = 124 - i * 9
    Tf = affine(346 + i * 76 + i * i * 0.4, 64 - i * 6, 62, h_, -5, shear=0.10)
    for pl in WEDGE[ch]:
        T_.poly([Tf(u, v) for u, v in pl])
G = lay(G, T_.a(), 0.97)

# placard
pc = Layer(ss=2).poly([(322, 644), (690, 612), (696, 664), (328, 698)]).a()
G = lay(G, pc, 0.93)
G = lay(G, text_rot("AlphaFold DB v6 · predicted", "georgiab.ttf", 25, 5.0, 509, 656, track=0.2), 0.02)

# paint, then the projected print
paintk = polar_streaks(2)
G = np.clip(G + 0.045 * paintk * (0.3 + 0.7 * G) + 0.012 * noise(s=2, seed=8), 0, 1)
G = warp(G, 0.8 * noise(s=2.5, seed=31), 0.8 * noise(s=2.5, seed=32))
d = np.hypot((x - 640) / 690, (y - 360) / 400)
G = G * (1 - 0.92 * smooth(d, 0.80, 1.14))
# a few static scratches
S = Layer(ss=1)
for i in range(7):
    xx = rng.uniform(0, W)
    S.line([(xx, rng.uniform(0, 300)), (xx + rng.uniform(-3, 3), rng.uniform(320, 720))], 1)
G = lay(G, S.a() * 0.22, 0.95)
t = np.clip(G, 0, 1)[..., None]
lo, mi, hi = np.array((0.035, 0.02, 0.012)), np.array((0.70, 0.36, 0.09)), np.array((1.0, 0.86, 0.56))
rgb = np.where(t < 0.5, lo + (mi - lo) * t * 2, mi + (hi - mi) * (t - 0.5) * 2)
save(rgb, "a7_expressionism.png")
