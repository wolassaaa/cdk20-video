"""HKBU SCIE1007 coursework science video. manual T4: the real CDK20 surface pushes up through the page. Rune rows spell the real sequence, swell over the form, and thicken in its shade, so the text itself draws the protein."""
from mk import *

C = CH[4]
Q = view(SW, SH, zoom=1.40, rot=-5, at=(0.535, 0.485), c=(0.5, 0.49))
m = Q["mask"]
mb = m > 0.5
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
cx, cy = 930, 500

d = Q["depth"]
lo, hi_ = d[mb].min(), d[mb].max()
hgt = np.where(mb, 1 - (d - lo) / (hi_ - lo), 0).astype(np.float32)
hs = gauss(hgt * m, 5) + gauss(m, 42) * 0.34
tent = gauss(m, 14)

# Rune sheet at 2x, three weights of the same text
GW, GH, GAP, LH = 15.0, 22.0, 6.0, 36.0
sheets = []
for lw in (1.5, 3.0, 5.2):
    M = Mask(SW + 240, SH + 240, 2)
    M.runes(10, 14, SW + 200, int((SH + 200) / LH), 0, GW, GH, GAP, LH, lw)
    sheets.append(M.hi())

n = Q["normal"]
A = 11.0
bx = (xx - cx) * (-0.085 * hs) + n[..., 0] * A * tent * -1
by = (yy - cy) * (-0.085 * hs) + n[..., 1] * A * tent
sx = (xx + bx + 120) * 2
sy = (yy + by + 120) * 2
layers = [sample(s, sx, sy) for s in sheets]

# Light on the real surface. The lamp is what the AI switched on.
key = lit(Q, (-0.60, 0.62, -0.50), 0.05)
NN = dict(Q)
NN["normal"] = gauss(n, 18)
big = lit(NN, (-0.60, 0.62, -0.50), 0.1)
ao = np.clip(Q["ao"], 0, 1)
s = np.clip((0.62 * key + 0.5 * big) * (0.25 + 0.75 * ao ** 1.3), 0, 1)

tail = np.clip((0.72 - gauss(Q["conf"], 1.5)) / 0.05, 0, 1) * (m > 0.5)  # real low confidence region

# Page outside the form: full dark flood, runes reversed out in a paler blue
FLOOD, ICE = hexc("#10195c"), hexc("#3f55b0")
page = paper("#10195c", 41, mott=0.06)
outside = 1 - m
page = page * (1 - layers[0][..., None] * 0.92) + ICE * layers[0][..., None] * 0.92
# fall off: the lines nearest the form are heavier, as if the sheet were stretched
near_f = np.clip(gauss(m, 60) * 2.4, 0, 1)
page = page * (1 - (layers[1] * near_f)[..., None] * 0.9) + hexc("#7f96e6") * (layers[1] * near_f)[..., None] * 0.9
# cast shadow of the form on the page, long, away from the lamp
sh = gauss(np.roll(np.roll(m, 46, 0), 62, 1), 20) * 0.78
page *= (1 - sh[..., None])

# The form is printed, not rendered: bare paper, a gold plate, a blue plate, both screened
gold = halftone(np.clip((0.66 - s) / 0.34, 0, 1) * 0.98, 7.0, 15)
blue = halftone(np.clip((0.36 - s) / 0.22, 0, 1) ** 0.8, 7.0, 75)
red = halftone(np.clip((0.86 - s) / 0.44, 0, 1), 7.0, 15)
dk = halftone(np.clip((0.34 - s) / 0.20, 0, 1) ** 0.8, 7.0, 75)
col = paper("#fbf1d4", 43, mott=0.03)
col = ink(col, np.maximum(gold * (1 - tail), 0), "#f0a81e")
col = ink(col, red * tail, "#d9361c")
col = col * (1 - tail[..., None] * 0.0)
col = ink(col, blue * (1 - tail), "#141f66")
col = ink(col, dk * tail, "#3a0a22")
fine = np.clip((0.78 - s) / 0.10, 0, 1)
cov = layers[1] * fine * 0.92
col = ink(col, cov * (1 - tail), "#141f66")
col = ink(col, cov * tail, "#3a0a22")
# ink keyline around the whole form so it sits on the flood like a printed figure
kl = np.clip(gauss((m > 0.5).astype(np.float32), 1.6) * 2.2 - 0.2, 0, 1) * (1 - np.clip(gauss((m > 0.8).astype(np.float32), 1.4) * 2 - 0.9, 0, 1))
out = page * (1 - m[..., None]) + col * m[..., None]
out = ink(out, np.clip(kl, 0, 1) * 0.9, "#fbf1d4")

# Label slip, pasted on the flood. The only words on this spread.
sl = Mask(SW, SH, 2)
x0, y0, x1, y1 = 70, 874, 716, 948
slip = np.zeros((SH, SW), np.float32)
slip[y0:y1, x0:x1] = 1
sh2 = gauss(np.roll(np.roll(slip, 7, 0), 6, 1), 6)
out *= 1 - 0.5 * sh2[..., None]
out = np.where(slip[..., None] > 0, paper("#fbf3dc", 9), out)
sl.text((x0 + 24, (y0 + y1) / 2 + 14), LABEL, serif(40 * 2, 800), "ls")
out = ink(out, sl.a(), "#141f66")
out = paste_tape(out, x0 + 2, y0 - 2, 84, 26, 40, seed=2)
out = paste_tape(out, x1 + 2, y0 + 2, 84, 26, -42, seed=3)

rgb = wrap(out, 0.52, tilt=-1.3, zoom=1.0, lamp=(420, 160), fall=1800)
save(rgb, ST / "T4.png")
