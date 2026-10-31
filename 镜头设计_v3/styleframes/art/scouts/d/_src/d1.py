"""HKBU SCIE1007 coursework science video. d1 style test: 1-bit dither method, strictly two tones at 640x360, a light shaft cutting the real CDK20 surface out of black."""
from t import *

W, H = 640, 360
INK, PAPER = hexc("#0c0f10"), hexc("#e9f2dc")
Q = view(W, H, zoom=1.62, rot=16, at=(0.685, 0.50), c=(0.5, 0.47))
m = Q["mask"] > 0.5
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# the shaft: a wedge from above left, soft inside, hard edged
ox, oy = 700.0, -130.0
ang = np.arctan2(yy - oy, xx - ox)
axis, half = np.deg2rad(125.0), np.deg2rad(24.0)
sh = np.clip((half - np.abs(ang - axis)) / np.deg2rad(1.2), 0, 1)
dist = np.hypot(xx - ox, yy - oy)

dif = lit(Q, (0.70, 0.62, -0.36), 0.08)
tone = (dif ** 1.15) * (0.18 + 0.82 * np.clip(Q["ao"] * 1.1, 0, 1) ** 1.6)
tone = tone * (0.03 + 1.25 * sh)
tone = np.clip(tone + 0.16 * lit(Q, (-0.8, -0.2, -0.3)) ** 3 * sh, 0, 0.94)

# air: fine dust glow inside the shaft, dying with distance. The sea at the bottom keeps it from floating in a void.
air = sh * np.clip(0.40 - dist / 1500, 0, 1) * (0.72 + 0.56 * fbm(H, W, 60, 3, 3))
air += 0.05 * np.exp(-((yy - 40) / 60) ** 2) * sh
horizon = 306
sea = yy > horizon
rows = (yy - horizon).clip(0, None)
wob = (fbm(H, W, 22, 3, 8) - 0.5) * (6 + rows * 1.1)
ry = np.clip(2 * horizon - yy + wob * 0.6, 0, H - 1).astype(int)
rx = np.clip(xx + wob * 2.2, 0, W - 1).astype(int)
refl = (tone * m)[ry, rx] * 0.8
glint = np.clip(np.sin(yy ** 1.32 * 1.9 + (fbm(H, W, 34, 2, 5) * 14)) * 0.5 + 0.5, 0, 1) ** 2
refl = refl * glint + sh * 0.08 * glint

ground = np.where(sea, refl, air)
v = np.where(m & ~sea, tone, ground)

bl = bluenoise(H, W, 11)
by = tile(bayer(8), H, W)
th = np.where(m, bl * 0.72 + by * 0.28, by)
bit = v > th

# Lines: white where the form sits in the dark, black where it is lit. Outside the shaft the protein exists only as these lines.
e, gz, gn = edges(Q, dz=0.005, dn=0.30)
e &= ~sea
fine = np.exp(-(fbm(H, W, 9, 2, 21) - 0.5) ** 2 / 0.012)  # dropouts so the line reads drawn, not plotted
dark = gauss(tone * m.astype(np.float32), 1.0) < 0.28
linew = e & dark & (fine > 0.06)
lineb = e & ~dark
bit = (bit | linew) & ~lineb
bit[sea & (np.abs(yy - horizon) < 0.6)] = True

# Type: a heavy slab, hard one-bit, white above the shaft. Scratched by the same dither at its foot.
tx = font("BOOKOSB.TTF", 132)
big = (text(W, H, "CDK", tx, (10, 2), "lt", track=-2, aa=False) > 0.5) | (text(W, H, "20", tx, (10, 124), "lt", track=-2, aa=False) > 0.5)
hole = (yy > 150) & (yy < 286) & (by * 0.5 + 0.5 < (yy - 150) / 150)
big &= ~hole
halo = gauss(big.astype(np.float32), 2.2) > 0.03
bit &= ~halo
bit |= big
pad = np.zeros((H, W), bool)
pad[331:352, 14:224] = True
lab = text(W, H, LABEL, font("verdanab.ttf", 11), (22, 335), "lt", aa=False) > 0.5
bit[pad] = True
bit[lab] = False

rgb = np.where(bit[..., None], PAPER, INK)
save(nearest(rgb, 2), OUT / "d1_obra_dither.png")
print("ok", bit.mean())
