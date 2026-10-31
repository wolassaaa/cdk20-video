"""HKBU SCIE1007 coursework science video. Style scout g4: a confocal figure. One protein crosses four channel strips, the way a real figure lays out channels and merge. Every channel is a real part of the model: surface, thin sections through the surface, backbone, and the residues under 0.7 confidence."""
from glib import *

A = atoms()
S = surface()
c = S["center"]
R = rot(-90, 0, -8)
SC = 18.4; cx, cy = 590, 346
V = (S["v"] - c) @ R.T
px = cx + V[:, 0] * SC; py = cy - V[:, 1] * SC
SS = 2


def splat(x, y, w=None):
    ix = (x * SS).astype(np.int32); iy = (y * SS).astype(np.int32)
    g = (ix >= 0) & (ix < W * SS) & (iy >= 0) & (iy < H * SS)
    b = np.bincount(iy[g] * W * SS + ix[g], weights=None if w is None else w[g], minlength=W * H * SS * SS).astype(np.float32)
    return b.reshape(H * SS, W * SS)


def dn(a): return a.reshape(H, SS, W, SS).mean((1, 3))


# channel 1, surface mass with a mottled chromatin grain
mass = dn(splat(px, py))
mass = gblur(mass, 3.2)
mott = fbm(beta=1.5, seed=2)
c1 = np.clip(mass / np.percentile(mass[mass > 0], 96), 0, 1) ** .75 * (.25 + 1.25 * mott ** 1.2)

# channel 2, optical sections: the pinhole keeps one thin plane at a time
sec = np.zeros((H, W), np.float32)
zs = np.linspace(V[:, 2].min() + 3, V[:, 2].max() - 3, 15)
for i, z in enumerate(zs):
    g = np.abs(V[:, 2] - z) < .42
    b = dn(splat(px[g], py[g]))
    sec += gblur(b, 1.5)
c2 = np.clip(sec * 5.5, 0, 1) ** .62

# channel 3, the real backbone as one filament with puncta on each residue
ca = A["xyz"][A["name"] == "CA"] - c
Vc = ca @ R.T
P2 = np.stack([cx + Vc[:, 0] * SC, cy - Vc[:, 1] * SC], -1)
im = Image.new("L", (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
def catmull(p, sub=10):
    Q = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    t = np.linspace(0, 1, sub, endpoint=False, dtype=np.float32)[None, :, None]
    p0, p1, p2, p3 = Q[:-3, None], Q[1:-2, None], Q[2:-1, None], Q[3:, None]
    return (.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)).reshape(-1, 2)


d.line([tuple(p * SS) for p in catmull(P2)], fill=190, width=9, joint="curve")
fil = dn(np.asarray(im, np.float32) / 255)
fil = gblur(fil, 1.3)
pun = np.zeros((H * SS, W * SS), np.float32)
rng = np.random.default_rng(5)
for i, p in enumerate(P2):
    pun[np.clip(int(p[1] * SS), 0, H * SS - 1), np.clip(int(p[0] * SS), 0, W * SS - 1)] += rng.uniform(.5, 2.2)
pun = gblur(dn(pun), 2.6) * 130
c3 = np.clip(fil * 1.15 + pun, 0, 1)

# channel 4, the low-confidence residues as a soft haze
low = A["conf"] < .7
Vt = (A["xyz"][low] - c) @ R.T
tl = dn(splat(cx + Vt[:, 0] * SC, cy - Vt[:, 1] * SC))
c4 = np.clip(gblur(tl, 7) * 40, 0, 1) ** .7 * (.5 + 1.0 * fbm(beta=2, seed=8))


def photons(a, k, seed):
    r = np.random.default_rng(seed)
    return r.poisson(np.clip(a, 0, 1.4) * k + .15).astype(np.float32) / k


n1 = photons(gblur(c1, .7), 28, 1); n2 = photons(c2, 46, 2); n3 = photons(c3, 60, 3); n4 = photons(c4, 26, 4)
CY = np.array([.05, .50, 1.0], np.float32)
MG = np.array([1.0, .05, .86], np.float32)
GR = np.array([.12, 1.0, .25], np.float32)
RD = np.array([1.0, .28, .02], np.float32)
ch1 = n1[..., None] * CY
ch2 = n2[..., None] * MG
ch3 = n3[..., None] * GR
ch4 = n4[..., None] * RD
merge = ch1 * .42 + ch2 * .95 + ch3 * .95 + ch4 * 1.15
merge = merge + gblur(np.clip(merge - .75, 0, 2), 5) * .5

# four strips, one protein crossing them
edges = [0, 214, 428, 642, W]
rgb = np.zeros((H, W, 3), np.float32)
for i, ch in enumerate([ch1, ch2, ch3, merge]):
    a, b = edges[i], edges[i + 1]
    rgb[:, a:b] = ch[:, a:b]
rgb[:, :edges[3]] = np.clip(rgb[:, :edges[3]] * 1.15, 0, 1)
for e in edges[1:-1]:
    rgb[:, e - 2:e + 2] = .95

# figure furniture: plain sans, the way lab figures look
sm = font("arialbd.ttf", 22)
for i, n_ in enumerate(["surface", "z-sections", "backbone", "merge"]):
    t = text_mask(n_, sm, (edges[i] + 16, 34), "ls")
    rgb = over(rgb, (.96, .96, .96), t)
big = font("arialbd.ttf", 136)
t = text_mask("CDK20", big, (14, 704), "ls", spacing=-3)
rgb = rgb * (1 - gblur(t, 3)[..., None] * .55)
rgb = over(rgb, (1, 1, 1), t)
tag = text_mask(LABEL, font("arialbd.ttf", 25), (W - 24, 662), "rs")
rgb = rgb * (1 - gblur(tag, 2.5)[..., None] * .6)
rgb = over(rgb, (1, 1, 1), tag)
L = 10 * SC
rgb[688:696, int(W - 24 - L):W - 24] = 1
t2 = text_mask("10 Å", font("arialbd.ttf", 22), (int(W - 34 - L), 700), "rs")
rgb = over(rgb, (1, 1, 1), t2)
save(rgb, "g4_confocal.png")
