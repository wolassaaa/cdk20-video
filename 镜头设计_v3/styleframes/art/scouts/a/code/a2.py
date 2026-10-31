"""HKBU SCIE1007 coursework science video. Style scout a2, suprematism: every real helix, strand and loop of CDK20 becomes one flat bar on a white field, pulled apart like an exploded view. Colour is real pLDDT."""
from kit import *

A = atoms()
ca, conf = A["ca"], A["ca_conf"]
n = len(ca)
d = lambda k: np.r_[np.linalg.norm(ca[k:] - ca[:-k], axis=1), np.full(k, 99)]
d3, d4, d2 = d(3), d(4), d(2)
hel = np.zeros(n, bool)
for i in range(n - 4):
    if 4.5 < d3[i] < 5.8 and 5.3 < d4[i] < 7.0:
        hel[i:i + 4] = True
stn = (d2 > 6.0) & ~hel
segs, i = [], 0
while i < n:
    if hel[i]:
        j = i
        while j + 1 < n and hel[j + 1]:
            j += 1
        if j - i >= 4:
            segs.append(("h", i, j + 1))
            i = j + 1
            continue
    if stn[i]:
        j = i
        while j + 1 < n and stn[j + 1]:
            j += 1
        if j - i >= 3:
            segs.append(("e", i, j + 1))
            i = j + 1
            continue
    i += 1
used = np.zeros(n, bool)
for t, a, b in segs:
    used[a:b] = True
# loops become straight sticks too, a few residues each, so nothing curves
i = 0
while i < n:
    if not used[i]:
        j = i
        while j + 1 < n and not used[j + 1] and j - i < 5:
            j += 1
        if j > i:
            segs.append(("c", i, j + 1))
        i = j + 1
    else:
        i += 1
print(len(segs), "bars; pLDDT by bar", np.round(np.percentile([conf[a:b].mean() for _, a, b in segs], [10, 30, 50, 70, 90]), 2))

BG = (244, 239, 226)
PAL = dict(k=(15, 14, 15), b=(26, 48, 150), y=(240, 190, 26), r=(208, 32, 22))


def col(c):
    return PAL["k"] if c >= 0.93 else PAL["b"] if c >= 0.82 else PAL["y"] if c >= 0.62 else PAL["r"]


W3, H3, s3 = 1280, 720, 3
im = Image.new("RGB", (W3 * s3, H3 * s3), BG)
R = rot(64, 0, 0) @ base_view()
R = rot(0, 0, 31) @ R
SCALE, CX, CY, PERSP, EXPL = 8.9, 505, 372, 0.95, 1.30
P = project(ca * EXPL, R, SCALE, CX, CY, PERSP * 0.72)
G = view(R, scale=SCALE * EXPL * 1.04, cx=CX, cy=CY, ss=0.6, persp=PERSP * 0.72 * 0.8)
gm = (G["mask"] > 0.5).astype(np.float32)
ghost = (np.array(BG, np.float32) * (1 - gm[..., None]) + np.array((226, 219, 200), np.float32) * gm[..., None]).astype(np.uint8)
im = Image.fromarray(ghost).resize((W3 * s3, H3 * s3), Image.BICUBIC)
dr = ImageDraw.Draw(im)
items = []
for t, a, b in segs:
    p = P[a:b]
    c0 = p[:, :2].mean(0)
    q = p[:, :2] - c0
    ux = np.linalg.svd(q, full_matrices=False)[2][0]
    L = (q @ ux).max() - (q @ ux).min()
    z = p[:, 2].mean()
    k = 1 + PERSP * z / (25 * EXPL)
    k = max(k, 0.22)
    wd = dict(h=8.2, e=4.6, c=1.25)[t] * SCALE * k
    L = L + (wd * 0.4 if t != "c" else 0)
    items.append((z, c0, ux, L, wd, col(conf[a:b].mean())))
items.sort(key=lambda t: t[0])


def bar(dr, c0, ux, L, wd, cl):
    vy = np.array([-ux[1], ux[0]])
    pts = [c0 + ux * L / 2 + vy * wd / 2, c0 + ux * L / 2 - vy * wd / 2, c0 - ux * L / 2 - vy * wd / 2, c0 - ux * L / 2 + vy * wd / 2]
    dr.polygon([(float(x) * s3, float(y) * s3) for x, y in pts], fill=cl)


for z, c0, ux, L, wd, cl in items:
    bar(dr, c0, ux, L, wd, cl)

ANG = -31.0
Tf = lambda i: affine(808 + i * 88, 598 - i * 52.8, 72, 116, ANG)
for i, ch in enumerate("CDK20"):
    for s, pl in glyph_pts(ch, Tf(i)):
        dr.polygon([(x * s3, y * s3) for x, y in pl], fill=PAL["k"] if s > 0 else BG)
rgb = np.asarray(im.resize((W3, H3), Image.LANCZOS), np.float32) / 255
lab = text_rot("AlphaFold DB v6 · predicted", "arialbd.ttf", 22, 31, 1096, 580, track=0.6)
rgb = ink(rgb, lab, PAL["k"])

# hand-laid paint: edges wander a little, brush drag inside shapes, canvas tooth in the white
dx, dy = 0.55 * noise(s=16, seed=11), 0.55 * noise(s=16, seed=12)
rgb = warp(rgb, dx, dy)
fg = np.linalg.norm(rgb - np.array(BG, np.float32) / 255, axis=2)
fg = smooth(fg, 0.05, 0.25)
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
st = fft_blur(np.random.default_rng(3).standard_normal((H, W)).astype(np.float32), 0.8)
st = np.asarray(Image.fromarray(st, "F").resize((W // 8, H), Image.BILINEAR).resize((W, H), Image.BICUBIC))
st = st / st.std()
tex = 1 + 0.035 * st * fg + 0.012 * noise(s=0.7, seed=9) * (1 - fg)
rgb = np.clip(rgb * tex[..., None] + 0.018 * fg[..., None] * st[..., None], 0, 1)
save(rgb, "a2_suprematism.png")
