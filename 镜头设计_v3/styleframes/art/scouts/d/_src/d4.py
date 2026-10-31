"""HKBU SCIE1007 coursework science video. d4 style test: silhouette and fog. The real CDK20 outline hangs as a colossal mass, the type stands as far architecture in the same fog, one small warm lamp reveals a patch of real surface."""
from t import *

W, H = 1280, 720
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
Q = view(W, H, zoom=1.17, rot=-8, at=(0.725, 0.425), c=(0.5, 0.50))
m = Q["mask"]
mb = m > 0.5
GROUND = 628

# Air: cold grey green, a low sun behind the mass
lx, ly = 930, 310
r = np.hypot((xx - lx) / 1.25, yy - ly)
glow = np.exp(-(r / 500) ** 2) * 0.74 + np.exp(-(r / 170) ** 2) * 0.32
base = 0.17 + 0.12 * (yy / H) ** 2
air = base + glow

# Far architecture: columns and a gantry, fading in steps of fog. The type belongs to this layer.
layer = np.zeros((H, W), np.float32)
ink = np.zeros((H, W), np.float32)
rng = np.random.default_rng(4)


def rect(a, x0, y0, x1, y1, v):
    a[int(max(y0, 0)):int(min(y1, H)), int(max(x0, 0)):int(min(x1, W))] = v


far = np.zeros((H, W), np.float32)
for i in range(16):
    x = rng.uniform(-40, W)
    w = rng.uniform(16, 60)
    rect(far, x, rng.uniform(40, 240), x + w, GROUND + 20, 1)
rect(far, 0, 92, W, 112, 1)
rect(far, 0, 462, W, 476, 1)
mid = np.zeros((H, W), np.float32)
for x in (30, 500, 1180):
    rect(mid, x, 0, x + 46, GROUND + 20, 1)
rect(mid, 0, 26, W, 52, 1)
far_fog = 0.62
air = air * (1 - far * (1 - far_fog * 0.9)) + 0.0
air = air * (1 - 0.0 * mid)

# The far wall, near black, with CDK20 cut clean through it. The light behind the wall comes through the letters.
tf = font("bahnschrift.ttf", 272)
T = np.maximum(text(W, H, "CDK", tf, (34, 8), "lt", track=-4), text(W, H, "20", tf, (34, 262), "lt", track=-4))
T = (T > 0.5).astype(np.float32)
wall = xx < 572 + 0 * yy
wall |= (xx < 610) & (yy < 70)
wall |= (xx < 596) & (yy > 560)
rivet = ((xx % 86) < 3) & (yy > 0)
pic = air.copy()
pic = np.where(mid > 0, 0.20 + 0.13 * glow, pic)
pic = np.where(wall, 0.030 + 0.012 * (yy / H), pic)
pic = np.where(wall & rivet, 0.042, pic)
through = T * wall
pic = np.where(through > 0.5, 0.95 - 0.28 * (yy / H), pic)
# light spilling out of the letters into the fog in front of the wall, leaning down and to the right
sp = np.zeros((H, W), np.float32)
Tb = gauss(through, 1.6)
for i in range(46):
    k = i / 46
    sx = xx - 150 * k
    sy = yy - 90 * k
    sp += sample(Tb, sx, sy) * (1 - k) ** 1.6
sp /= 22
pic = pic + np.clip(sp, 0, 1) * 0.26 * (1 - through)
pic += gauss(through, 16) * 0.22

# Shafts: radial march of the real outline away from the light, so the actual gaps in the protein throw rays
occ = gauss(np.clip(m, 0, 1), 1.0)
L = 1 - occ
acc = np.zeros((H, W), np.float32)
N = 48
for i in range(N):
    t = 1 - i / N * 0.72
    sx = lx + (xx - lx) * t
    sy = ly + (yy - ly) * t
    acc += sample(L, sx, sy) * (0.5 + 0.5 * (i / N))
acc /= N
ray = np.clip(acc * 1.45 - 0.45, 0, 1)
fall = np.exp(-np.hypot(xx - lx, yy - ly) / 650)
ray = ray * ~wall + (~wall == 0) * 1.0
pic = pic * (0.66 + 0.60 * ray) + 0.22 * ray ** 2 * fall * (~wall)

# The mass: near black, slightly lifted by fog at its far lobes, a thin cold edge where the sun wraps it
depthfog = np.clip((Q["depth"] - 0.30) / 0.34, 0, 1)
rimlight = np.clip(1 - gauss(Q["mask"], 5), 0, 1) * 2.2 * mb
body = 0.018 + 0.05 * depthfog ** 2 + 0.33 * np.clip(rimlight, 0, 1) ** 2 * np.exp(-np.hypot(xx - lx, yy - ly) / 420)
pic = pic * (1 - m) + body * m

# Ground plane, and the far haze that eats its horizon
gnd = yy > GROUND + (fbm(H, W, 200, 2, 3) - 0.5) * 6
pic = np.where(gnd, 0.012, pic)

# Slow drifting fog bank at the foot of everything
bank = np.clip(1 - np.abs(yy - 600) / 90, 0, 1) ** 1.5 * fbm(H, W, 170, 4, 12)
pic = pic + bank * 0.30 * (~gnd)

col = pic[..., None] * hexc("#c8dcd6")[None, None] * 1.25 + 0.012
col = np.clip(col, 0, 1)

# A person with a lamp under it. Warm against everything cold.
px, py = 688, GROUND + 1
fig = Image.new("L", (W * 4, H * 4), 0)
d = ImageDraw.Draw(fig)


def S(*p):
    return [(a * 4, b * 4) for a, b in p]


d.ellipse(S((px - 3.6, py - 49), (px + 3.6, py - 41)), fill=255)
d.polygon(S((px - 4.8, py - 41), (px + 4.8, py - 41), (px + 6.2, py - 20), (px + 3.4, py), (px + 0.8, py), (px, py - 18), (px - 2, py), (px - 5, py), (px - 5.4, py - 21)), fill=255)
d.polygon(S((px + 3, py - 39), (px + 7, py - 39), (px + 17, py - 50), (px + 16, py - 53)), fill=255)
fg = np.asarray(fig.resize((W, H), Image.LANCZOS), np.float32) / 255
lamp = (px + 17.0, py - 53.0)

# Warm cone rising from the lamp, and the real surface it uncovers
ax = np.deg2rad(-63)
ang = np.arctan2(yy - lamp[1], xx - lamp[0])
da = np.abs(np.angle(np.exp(1j * (ang - ax))))
dist = np.hypot(xx - lamp[0], yy - lamp[1])
cone = np.clip((np.deg2rad(20) - da) / np.deg2rad(5), 0, 1)
warm = hexc("#ffb060")
reach = np.exp(-dist / 300)
air_warm = cone * reach * 0.55 * (0.7 + 0.5 * fbm(H, W, 40, 3, 6)) * (~gnd) * (1 - m)
col += air_warm[..., None] * warm * 0.55

dif = lit(Q, (-0.42, -0.84, -0.34), 0.0)
surf = (dif ** 0.9) * (0.15 + 0.85 * np.clip(Q["ao"], 0, 1) ** 1.5)
spot = cone * np.exp(-dist / 300) * m
col += (surf * spot * 3.6)[..., None] * hexc("#ffa95e")
e = edges(Q, dz=0.003, dn=0.2)[0]
g = np.exp(-(((xx - lamp[0]) / 3) ** 2 + ((yy - lamp[1]) / 3) ** 2))
g2 = np.exp(-(((xx - lamp[0]) / 26) ** 2 + ((yy - lamp[1]) / 26) ** 2))
col = col * (1 - fg[..., None]) + hexc("#040505") * fg[..., None]
col += g[..., None] * hexc("#fff0c8") * 1.7 + g2[..., None] * hexc("#ffa24a") * 0.55
pool = np.exp(-(((xx - px) / 110) ** 2 + ((yy - GROUND - 8) / 9) ** 2)) * gnd
col += pool[..., None] * hexc("#ff9a4a") * 0.20

# Fine film grain, static
col += (noise(H, W, 1, 3) - 0.5)[..., None] * 0.018
col *= (0.72 + 0.28 * np.clip(1.25 - np.hypot((xx - 640) / 800, (yy - 360) / 460), 0, 1))[..., None]

lab = text(W, H, LABEL, font("bahnschrift.ttf", 24), (42, 676), "lm", track=1.2)
col = over(col, hexc("#c8dcd6"), lab * 0.95)
save(col, OUT / "d4_inside_fog.png")
