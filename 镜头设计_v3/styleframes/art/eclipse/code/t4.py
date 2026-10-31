"""HKBU SCIE1007 coursework science video. Eclipse direction, T4: CDK20 seen for the first time. The real surface is the moon: only its edge burns, and the light that gets through comes through its real valleys."""
from ec import *

y, x = grid()
SCALE = 17.6
CX, CY = 960, 452
cache = WORK / "t4_view.npz"
if cache.exists():
    V = dict(np.load(cache))
else:
    V = kit.view(R=kit.base_view() @ np.eye(3), scale=SCALE, cx=CX, cy=CY, w=W, h=H, ss=0.55)
    np.savez(cache, **{k: v for k, v in V.items() if isinstance(v, np.ndarray)})
m = V["mask"]
hard = sstep(0.42, 0.58, m)

# the sun sits fully behind the real outline. The one real gap in the silhouette is the only place it gets through
SX, SY, R = 966, 462, 385
r = np.hypot(x - SX, y - SY)
disc = sstep(R + 1.5, R - 1.5, r)
leak = disc * (1 - hard)
print("leak px", float(leak.sum()))

# corona: starts on the real outline and is drawn out along the radii, wispy, never hard speed lines
th = np.arctan2(y - SY, x - SX)
n = 2048
s1 = noise(11, 340, (8, n), 1.4)[3]
s2 = noise(12, 90, (8, n), 1.1)[5]
idx = ((th + np.pi) / (2 * np.pi) * n).astype(np.int32) % n
st = (0.72 * s1 + 0.28 * s2)[idx]
st = sstep(0.25, 0.8, (st - st.min()) / (st.max() - st.min()))
limb = hard * (1 - blur(hard, 16)) * 2
cor = np.zeros_like(limb)
STEPS = 260
for i in range(STEPS):
    k = 1 - (i + 0.5) / STEPS * 0.62
    cor += sample(limb, SX + (x - SX) * k, SY + (y - SY) * k) * (1 - i / STEPS) ** 2.6
cor = blur(cor, 1.6) / STEPS * 26
halo = blur(hard, 14) * 0.9 + blur(hard, 46) * 0.8 + blur(hard, 130) * 0.55 + blur(hard, 300) * 0.3
L = 0.0 + cor * (0.1 + 1.3 * st ** 1.4) * 0.55 + halo * 0.2 * (0.5 + 0.9 * st)

# the leak: blown out, tight bloom only
bead = blur(leak, 3) * 2.5 + blur(leak, 12) * 7 + blur(leak, 40) * 12
L = L + leak * 40 + bead

# surface: nearly black. A sliver of back light on every edge, a low red fill so the real relief still reads
n3 = V["normal"]
nz = np.clip(n3[..., 2], 0, 1)
fres = (1 - nz) ** 3.2
toSun = np.clip((n3[..., 0] * (x - SX) * -0 + 0), 0, 1)
dirx, diry = (x - SX) / np.maximum(r, 1), -(y - SY) / np.maximum(r, 1)
out = np.clip(n3[..., 0] * dirx + n3[..., 1] * diry, 0, 1)   # does this facet point away from the sun's centre, toward the limb glow
rim = fres * (0.25 + 0.75 * out) * (0.3 + 0.7 * V["ao"])
fill = V["ao"] ** 1.6 * (0.2 + 0.8 * np.clip(0.5 * V["key"] + 0.7 * V["rim"], 0, 1))
surf = 0.012 + 0.075 * fill + 0.62 * rim ** 1.2
L = L * (1 - hard) + surf * hard + bead * hard * 0.5

t = expose(L, 2.6)

ai = np.ones_like(tt := t)
# ground: far horizon, wet black, a crowd for scale
hz = 930
g = sstep(hz - 1, hz + 1, y)
fl = 2 * hz - y
mir = blur(sample(t, x, fl), 3) * sstep(1080, hz, y) ** 1.2 * 0.5
tt = t * (1 - g) + g * mir
rng = np.random.default_rng(14)
ppl = np.zeros((H, W), np.float32)
for cxx, nn in ((300, 5), (520, 2), (1390, 3), (1560, 6)):
    for i in range(nn):
        ppl = np.maximum(ppl, person(x, y, cxx + rng.normal(0, 30), hz + 2 + rng.random() * 8, rng.uniform(34, 42)))
tt = put(tt, ppl, 0.66)      # people are the only orange-gold in the frame: the crowd is warm against a cold machine
ai = ai * (1 - ppl)

tt = tag(tt, x, y, "predicted", "AlphaFold DB v6 · predicted", 72, 1006, size=38, weight=500, ink=0.94, ground=0.0)
save(tt, "T4.png", ai)
