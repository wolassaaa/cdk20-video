"""HKBU SCIE1007 coursework science video. Style scout g2: a scanning electron micrograph. Grey only, tilted walls emit more so every edge burns bright, one detector side. Where the model's real confidence falls below 0.7 the scan tears and charges: the image of not being sure."""
from glib import *

S = surface()
R = rot(-90, 0, 12) @ rot(0, 0, 0)
SC = 16.0
cx, cy = 800, 306
P = smooth_pass(render(R, SC, cx, cy, S=S), 1.6)
m = P["mask"]; n = P["n"]; z = P["z"] * SC
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def hblur(a, s):
    p = int(3 * s) + 2
    A = np.pad(a, ((0, 0), (p, p)), mode="edge")
    fx = np.fft.rfftfreq(A.shape[1])[None, :]
    return np.fft.irfft(np.fft.rfft(A, axis=1) * np.exp(-2 * (np.pi * s * fx) ** 2), n=A.shape[1], axis=1)[:, p:-p].astype(np.float32)


# sputter coat: a very fine bump on every surface, the look of a gold-coated sample
A = atoms()
c_ = S["center"]
At = spheres(A["xyz"] - c_, np.full(len(A["xyz"]), 1.72, np.float32), R, SC, cx, cy)
nat = gblur(At["n"] * At["mask"][..., None], .9)
n = n * .5 + nat * .8
n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-4)
bx = fbm(beta=1.5, seed=1); by = fbm(beta=1.5, seed=2)
nn = n + np.stack([(bx - .5) * .5, (by - .5) * .5, np.zeros_like(bx)], -1)
nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
nz = np.clip(nn[..., 2], .07, 1)
edge = np.clip((1 / nz - 1) * .30, 0, 1.25)            # tilted walls emit more electrons
det = np.clip(nn @ np.array([-.62, .62, .48], np.float32), -1, 1)   # one side detector
cav = cavity(z, m, (3, 8, 20, 44))
I = (.05 + .40 * np.clip(.5 + .5 * det, 0, 1) ** 1.7 + .92 * edge) * (1 - .72 * np.clip(cav * 1.1, 0, 1))
I = I * m

# floor: a tilted stub, falling away to black at the horizon
y0 = 210
s_ = np.clip((yy - y0) / (H - y0), 0, 1)
u = (xx - 640) / (s_ + .10); v = 90 / (s_ + .10)
noise = fbm(beta=1.1, seed=4)
pit = sample(noise, (u * .55) % (W - 2), (v * 2.2) % (H - 2))
floor = (.012 + .30 * s_ ** 1.5) * (.55 + .9 * pit)
# specks of debris, the first thing anyone notices on a real stub
rng = np.random.default_rng(3)
deb = np.zeros((H, W), np.float32)
for i in range(240):
    sy = rng.uniform(.05, 1) ** 1.2
    y = y0 + sy * (H - y0); x = rng.uniform(0, W); r = rng.uniform(.6, 3.2) * (.3 + sy)
    y1, y2, x1, x2 = int(max(0, y - r - 2)), int(min(H, y + r + 3)), int(max(0, x - r - 2)), int(min(W, x + r + 3))
    if y2 <= y1 or x2 <= x1: continue
    d = np.sqrt((yy[y1:y2, x1:x2] - y) ** 2 + (xx[y1:y2, x1:x2] - x) ** 2) / r
    deb[y1:y2, x1:x2] = np.maximum(deb[y1:y2, x1:x2], np.clip(1 - d, 0, 1) ** .4 * (d < 1))

# contact shadow: the object blocks the path to the detector, so the floor behind it goes black
sh = sample(m, xx - 46, yy - 74)
shadow = gblur(sh, 16) * .92
floor = floor * (1 - shadow) + deb * .6 * (1 - shadow) * (.3 + s_)

# title: blocks milled out of the stub, standing up, same physics as the sample
f = font("ariblk.ttf", 188)
face = text_mask("CDK20", f, (34, 672), "ls", spacing=-2)
side = np.zeros((H, W), np.float32)
for i in range(1, 19):
    side = np.maximum(side, sample(face, xx - i * 1.25, yy + i * .9) * (1 - i / 60))
side = side * (1 - face)
fe = np.abs(gblur(face, 1.2) - gblur(face, 4)) * 4  # bright rim
shl = gblur(sample(face, xx + 40, yy + 16), 8)

floor = floor * (1 - shl * .45)
I2 = floor * (1 - m) + I
mt = fbm(beta=1.6, seed=7)
facecol = (.20 + .16 * mt)
sidecol = .56 + .3 * mt
I2 = I2 * (1 - side) + sidecol * side
I2 = I2 * (1 - face) + facecol * face
I2 = I2 + np.clip(fe, 0, 1) * face * .86

# depth cue: the far side of the floor falls off, the protein keeps its own light
# charging: where confidence is low the raster tears sideways and streaks
tail = gblur(((P["conf"] < .7) & (m > .5)).astype(np.float32), 6)
tail = np.clip(tail * 1.8, 0, 1)
r1 = np.random.default_rng(11)
rowj = np.cumsum(r1.standard_normal(H)) * .9
rowj = rowj - gblur(rowj[None, :], 30)[0]
rowk = (r1.random(H) ** 5) * 72
J = (rowj + rowk * np.sign(r1.standard_normal(H)))[:, None]
torn = sample(I2, xx + J * tail, yy)
streak = hblur(np.clip(tail * I2 - .1, 0, 1), 46) * 2.5 * (0.35 + 1.3 * r1.random((H, 1)) ** 3)
Fin = torn + streak * (.6 + .4 * (m > .5))

# lines of the raster itself, static
scan = 1 + .035 * np.sin(yy * np.pi / 1.0)
rowgain = 1 + .022 * (r1.standard_normal((H, 1)))
Fin = Fin * scan * rowgain
Fin = Fin + (fbm(beta=.2, seed=8) - .5) * .05
Fin = np.clip(gblur(Fin, .55), 0, 1) ** .80
rgb = np.repeat(Fin[..., None], 3, -1)

# the instrument's data bar
bar = 44
rgb[H - bar:] = .02
rgb[H - bar - 1:H - bar + 1] = .85
tag = text_mask(LABEL, font("arialbd.ttf", 25), (26, H - 13), "ls")
rgb = over(rgb, (.97, .97, .97), tag)
L = 10 * SC  # ten Angstrom at this scale, real
bx0 = W - 268
rgb[H - 20:H - 15, bx0:int(bx0 + L)] = .97
rgb[H - 28:H - 8, bx0:bx0 + 3] = .97; rgb[H - 28:H - 8, int(bx0 + L) - 3:int(bx0 + L)] = .97
t2 = text_mask("10 Å", font("arialbd.ttf", 25), (W - 26, H - 13), "rs")
rgb = over(rgb, (.97, .97, .97), t2)
save(rgb, "g2_sem.png")
