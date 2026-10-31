"""HKBU SCIE1007 coursework science video. d5 style test: watercolour and sand. Transparent pigment washes with pooled edges on paper; the real low confidence tail blows away as sand across the page."""
from t import *

W, H = 1280, 720
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
Q = view(W, H, zoom=1.16, rot=11, at=(0.665, 0.475), c=(0.5, 0.49))
m = gauss(Q["mask"], 1.2)
rng = np.random.default_rng(7)

PAPER = hexc("#f6efe0")
tooth = gauss(noise(H, W, 1, 1), 0.8)
tooth = (tooth - tooth.mean()) / tooth.std()
fibre = fbm(H, W, 5, 3, 2) - 0.5
dens = np.zeros((H, W, 3), np.float32)  # optical density, Beer-Lambert: colour = paper * exp(-dens)


def absorb(hexcol):
    """A pigment as the density that takes paper to this colour."""
    return -np.log(np.clip(hexc(hexcol) / PAPER, 0.02, 1))


def wash(mask, pig, amt=1.0, wob=26, edge=0.9, seed=0, flow=None):
    """One wet layer: wobble the shape, pool the pigment at its edge, granulate into paper tooth."""
    wn = (fbm(H, W, 46, 4, seed) - 0.5) * wob
    wm = (fbm(H, W, 46, 4, seed + 3) - 0.5) * wob
    sh = sample(mask, np.clip(xx + wn, 1, W - 3), np.clip(yy + wm, 1, H - 3))
    sh = np.clip((gauss(sh, 1.5) - 0.45) / 0.10, 0, 1)
    pool = np.clip(sh - gauss(sh, 11), 0, 1)
    thick = 0.68 + 0.7 * fbm(H, W, 150, 4, seed + 9) ** 1.4
    bloom = np.clip(fbm(H, W, 80, 5, seed + 21) - 0.54, 0, 1) * 5
    bloomE = np.exp(-((bloom - 0.3) / 0.05) ** 2) * 0.22
    d = sh * thick * amt * (1 + 0.20 * tooth + 0.12 * fibre) + pool * edge * amt + bloomE * sh * amt
    if flow is not None:
        d = d * flow
    global dens
    dens = dens + d[..., None] * pig


# Sky: broad graded wash, rose coming up into pale gold from the horizon
sky = np.clip(1.08 - yy / 430, 0, 1) ** 1.3
wash(np.ones((H, W), np.float32), absorb("#e9a79a"), 0.95, 0, 0, 3, sky * (0.82 + 0.3 * fbm(H, W, 220, 3, 2)))
wash(np.ones((H, W), np.float32), absorb("#f3c477"), 0.55, 0, 0, 4, np.clip((yy - 200) / 340, 0, 1) * np.clip((590 - yy) / 90, 0, 1))

# The mass in stacked transparent bands of depth, near ones on top, ramp from ultramarine shade to vermilion lit
dif = lit(Q, (0.62, 0.62, -0.45), 0.25)
ao = np.clip(Q["ao"], 0, 1)
d0 = Q["depth"]
near = np.clip((d0 - 0.29) / 0.355, 0, 1)
msk = (m > 0.5).astype(np.float32)
pal = ["#1f55c0", "#5a4fd0", "#d9308a", "#f2402a", "#f79a2a"]
qs = np.quantile(near[m > 0.5], [0.18, 0.38, 0.60, 0.80])
bands = [(qs[3], 9.0, "#2f55c8"), (qs[2], qs[3], "#7a45cf"), (qs[1], qs[2], "#e0308a"), (qs[0], qs[1], "#f0483a"), (-9.0, qs[0], "#f79a2a")]
shm = gauss(np.clip(1 - ao, 0, 1) * msk, 1.5) > 0.36  # cavities keep clean pigment: no glaze over orange, that makes mud
wash(msk, absorb("#f6c8b0"), 0.8, 6, 1.0, 11)
for i, (lo, hi, c) in enumerate(bands):
    band = ((near >= lo) & (near < hi) & (m > 0.5) & ~shm).astype(np.float32)
    wash(band, absorb(c), 0.86, 3, 0.55, 12 + i * 5, 0.70 + 0.42 * (1 - dif))
wash(shm.astype(np.float32), absorb("#27278c"), 0.95, 3, 0.7, 41)
sh2 = np.clip(1 - dif * 1.6, 0, 1) * msk * ~shm
wash((gauss(sh2, 2.5) > 0.62).astype(np.float32), absorb("#a03a9c"), 0.20, 5, 1.0, 43)
# Lifted lights: wet pigment blotted off the crests
crest = (dif > 0.80) * (ao > 0.72)
lift = np.clip(gauss(crest.astype(np.float32), 2.2) * 1.5, 0, 1)
dens = dens * (1 - lift[..., None] * 0.86)

# Dunes: two curved flat washes, gold into burnt sienna
def dune(y0, a, f, ph, sk):
    return y0 + a * np.sin(xx * f + ph) + a * 0.5 * np.sin(xx * f * 2.3 + ph * 1.7) + sk * (xx - 640) / 640


d1 = yy > dune(560, 26, 0.0058, 1.2, -14)
d2 = yy > dune(610, 18, 0.0047, 3.4, 26)
d3 = yy > dune(662, 10, 0.0062, 0.2, -6)
wash(d1.astype(np.float32), absorb("#f0ae56"), 1.1, 4, 1.25, 60)
wash(d2.astype(np.float32), absorb("#e8703c"), 0.95, 4, 1.25, 61)
wash(d3.astype(np.float32), absorb("#a83a3e"), 1.05, 4, 1.25, 62)
# Wind ripples on the sand
rip = np.sin((yy + (fbm(H, W, 90, 3, 8) - 0.5) * 70 + xx * 0.10) * 0.72)
rip = (rip > 0.72) * d1
dens += gauss(rip.astype(np.float32), 0.7)[..., None] * absorb("#a84a2c") * 0.32

rgb = PAPER * np.exp(-dens)
# granulation specks settle in the paper grooves where pigment is heavy
gr = (tooth < -1.5) * np.clip(dens.mean(2) * 1.6, 0, 1)
rgb *= (1 - 0.22 * gr[..., None])
rgb *= (1 + 0.012 * tooth[..., None])

# Sand: grains lifted from the real low confidence region, carried on a curl field to the left and up
conf = Q["conf"]
ty, tx = np.where((conf < 0.70) & (Q["mask"] > 0.6))
pot = fbm(H, W, 130, 3, 90) * 240
py, px = np.gradient(gauss(pot, 3))
N = 190000
idx = rng.integers(len(ty), size=N)
x = tx[idx].astype(np.float32) + rng.normal(0, 3, N)
y = ty[idx].astype(np.float32) + rng.normal(0, 5, N)
steps = 230
life = rng.uniform(0.08, 1, N) ** 1.35
n = (life * steps).astype(int)
gold = np.zeros((H, W), np.float32)
dark = np.zeros((H, W), np.float32)
glint = np.zeros((H, W), np.float32)
for s in range(steps):
    live = n > s
    ix = np.clip(x, 0, W - 1).astype(int)
    iy = np.clip(y, 0, H - 1).astype(int)
    u = -5.4 + py[iy, ix] * 0.8 + 0.5 * np.sin(y * 0.012)
    v = -1.55 - px[iy, ix] * 0.8 + 1.1 * np.sin(x * 0.0065 + 2)
    x = x + u * live
    y = y + v * live
ix, iy = x.astype(int), y.astype(int)
ok = (ix >= 0) & (iy >= 0) & (ix < W) & (iy < H)
which = rng.random(N)
np.add.at(dark, (iy[ok & (which < 0.5)], ix[ok & (which < 0.5)]), 1)
np.add.at(gold, (iy[ok & (which >= 0.5)], ix[ok & (which >= 0.5)]), 1)
sp = ok & (which > 0.9975)
np.add.at(glint, (iy[sp], ix[sp]), 1)
rgb *= np.exp(-np.minimum(gauss(dark, 0.55) * 0.75, 3))[..., None] ** np.array([0.35, 0.8, 1.05], np.float32)
rgb = over(rgb, hexc("#ffcf6a"), np.clip(gauss(gold, 0.55) * 0.75, 0, 0.95))
star = gauss(glint, 0.9) * 7
rgb += star[..., None] * hexc("#fff4d0")

# Traveller on the crest, a stroke of dark wash and a line of steps
tx0 = 330
ty0 = dune(610, 18, 0.0047, 3.4, 26)[0, tx0]
cl = Image.new("L", (W * 4, H * 4), 0)
d = ImageDraw.Draw(cl)
def S(*p):
    return [(a * 4, b * 4) for a, b in p]


d.polygon(S((tx0 - 1.4, ty0 - 31), (tx0 + 1.8, ty0 - 31), (tx0 + 5, ty0 + 3), (tx0 - 6, ty0 + 3)), fill=255)
d.ellipse(S((tx0 - 2.2, ty0 - 36), (tx0 + 2.4, ty0 - 30)), fill=255)
for k in range(1, 15):
    a = tx0 + 22 + k * 34
    b = dune(610, 18, 0.0047, 3.4, 26)[0, int(a)] + 5 + np.sin(k) * 1.2
    d.ellipse(S((a - 4, b - 1), (a + 4, b + 1.6)), fill=120)
figm = np.asarray(cl.resize((W, H), Image.LANCZOS), np.float32) / 255
rgb = over(rgb, hexc("#3a1426"), figm)
sc = Image.new("L", (W * 4, H * 4), 0)
ds = ImageDraw.Draw(sc)
pts = [(tx0 + i * 4.2, ty0 - 27 - i * 0.7 + np.sin(i * 0.6) * (1 + i * 0.28)) for i in range(26)]
ds.line(S(*pts), fill=255, width=9, joint="curve")
scm = np.asarray(sc.resize((W, H), Image.LANCZOS), np.float32) / 255
rgb = over(rgb, hexc("#c81e24"), scm)

# Type: brushed hairline serif, sitting in the sky, soaked at its foot
T = text(W, H, "CDK20", font("pala.ttf", 132), (40, 28), "lt", track=7)
tb = sample(T, xx + (fbm(H, W, 30, 3, 5) - 0.5) * 4, yy + (fbm(H, W, 30, 3, 6) - 0.5) * 4)
pool = np.clip(tb - gauss(tb, 4), 0, 1)
blead = np.clip(gauss(T, 6) * 0.6 * np.clip((yy - 100) / 80, 0, 1), 0, 1)
td = (tb * (0.98 + 0.4 * fbm(H, W, 40, 3, 7)) + pool * 0.9 + blead * 0.25)
rgb *= np.exp(-td[..., None] * 2.0 * absorb("#26308a"))

lab = text(W, H, LABEL, font("constanb.ttf", 26), (46, 186), "lm", track=0.6)
rgb = over(rgb, hexc("#23286e"), lab)
save(rgb, OUT / "d5_journey_watercolor.png")
