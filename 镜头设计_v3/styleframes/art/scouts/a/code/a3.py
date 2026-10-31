"""HKBU SCIE1007 coursework science video. Style scout a3, photogram: the real CDK20 surface treated as a thin glass shell laid on photo paper, with a plain key beside it. Height above the paper sets the blur."""
from kit import *

S = surface()
R = rot(0, -22, 18) @ base_view()
SC, CX, CY = 11.3, 898, 345
v = S["v"] @ R.T
z = v[:, 2]
zn = (z - z.min()) / (z.max() - z.min())


def expose(shift=(0, 0), N=7):
    """shift is the parallax in px at full height, from moving the lamp between exposures."""
    D = np.zeros((H, W), np.float32)
    for i in range(N):
        sel = (zn >= i / N) & (zn < (i + 1) / N + 1e-6)
        t = (i + 0.5) / N
        px = v[sel, 0] * SC + CX + shift[0] * t
        py = -v[sel, 1] * SC + CY + shift[1] * t
        h, _, _ = np.histogram2d(py, px, bins=[H, W], range=[[0, H], [0, W]])
        D += fft_blur(h.astype(np.float32), 0.8 + 9 * t**2.2)
    return D


V = view(R, scale=SC, cx=CX, cy=CY, ss=0.6)
body = fft_blur(V["mask"], 1.2)
D1 = expose()
D2 = expose((-120, 70))
D1 = D1 / np.percentile(D1[body > 0.5], 97)
D2 = D2 / np.percentile(D2[body > 0.5], 97)
halo = fft_blur(V["mask"], 22)
nz = np.clip(V["normal"][..., 2], 0, 1)
shell = (1 - nz) ** 1.9 * V["mask"]  # a glass bead prints dark in the middle, bright round its edge
crease = (1 - V["ao"]) * V["mask"]
L = 0.10 * body + 1.25 * shell + 0.12 * D1 + 0.26 * crease + 0.17 * D2 * (1 - 0.5 * body) + 0.10 * halo

# ---- objects on the paper: a plain key, two positions, the type as cut metal ----
def key(cx, cy, deg, s=1.0):
    """A generic door key silhouette, rotated about the bow."""
    a = np.radians(deg)
    c, sn = np.cos(a), np.sin(a)
    T = lambda x, y: (cx + (x * c - y * sn) * s, cy + (x * sn + y * c) * s)
    lay = Layer(ss=2)
    r0, r1 = 52, 26
    th = np.linspace(0, 2 * np.pi, 64)
    lay.poly([T(r0 * np.cos(t), r0 * np.sin(t)) for t in th])
    lay.poly([T(r1 * np.cos(t), r1 * np.sin(t)) for t in th], 0)
    lay.poly([T(46, -10), T(300, -10), T(300, 10), T(46, 10)])
    lay.poly([T(262, 10), T(300, 10), T(300, 44), T(262, 44)])
    lay.poly([T(226, 10), T(246, 10), T(246, 34), T(226, 34)])
    return lay.a()


k1 = key(150, 290, 6, 1.12)
k2 = key(150, 290, 38, 1.12)
K = np.maximum(fft_blur(k1, 0.7), 0)
L = L + 1.1 * K + 0.30 * fft_blur(k2, 3.0) + 0.16 * fft_blur(k1, 16)

T = Layer(ss=2)
block_word(T, "CDK20", lambda i: affine(66 + i * 100, 538, 84, 118))
tm = T.a()
tt = fft_blur(tm, 0.9)
L = L + 1.15 * tt + 0.22 * np.roll(np.roll(fft_blur(tm, 7), 14, 0), 16, 1)

# a strip of paper slid across mid exposure: a hard straight burn of light
strip = Layer(ss=1).poly([(-40, 120), (760, -90), (800, -30), (-20, 190)]).a()
sg = fft_blur(strip, 2.5) * np.clip(np.linspace(1, 0.0, W)[None, :] ** 1.3, 0, 1)
L = L + 0.11 * sg
disc = Layer(ss=1).ell(420, 170, 860, 610).a()
ds = fft_blur(disc, 1.5) - fft_blur(Layer(ss=1).ell(430, 180, 850, 600).a(), 12)
L = L + 0.08 * np.clip(ds, 0, 1)

# label: typed on a strip of acetate
lab = Layer(ss=2).text((66, 690), "AlphaFold DB v6 · predicted", "consolab.ttf", 22, track=0.4).a()
L = L + 1.1 * fft_blur(lab, 0.35)

tone = 1 - np.exp(-2.1 * np.clip(L, 0, 4))
fog = 0.022 + 0.012 * smooth(noise(s=90, seed=2), -1, 2)
tone = fog + (1 - fog) * tone

# warm silver print with brushed emulsion edge, bare paper showing round it
e = smooth(tone, 0, 1)[..., None]
lo, mi, hi = np.array((0.035, 0.028, 0.024)), np.array((0.53, 0.46, 0.38)), np.array((0.985, 0.955, 0.875))
rgb = np.where(e < 0.5, lo + (mi - lo) * e * 2, mi + (hi - mi) * (e - 0.5) * 2)
nx, ny = np.meshgrid(np.arange(W), np.arange(H))
edge = np.minimum.reduce([nx, W - 1 - nx, ny, H - 1 - ny]).astype(np.float32)
brush = edge + 2.2 * noise(s=22, seed=21) + 0.9 * noise(s=1.6, seed=22)
print_a = smooth(brush, 13, 15.5)[..., None]
bare = paper((238, 230, 210), 5, mott=0.012, fibre=0.012)
rgb = bare * (1 - print_a) + rgb * print_a
save(rgb, "a3_photogram.png")
