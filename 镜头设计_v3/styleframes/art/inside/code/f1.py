"""HKBU SCIE1007 coursework science video. Direction inside, F1 (script 1-02): the liver, and how many people it costs.
Outline, form and veins are the real BodyParts3D meshes. The fill is a packing of plain round cells, the same flat disc and ink line as the crowd, so the macro shot already belongs to the world inside. Cell size is not to scale, and the frame says schematic."""
from ilib import *

SHX, SHY = 372, 8     # where the liver sits, offset from frame centre


def part(k):
    a = np.load(WORK / f"liver_{k}.npy").astype(np.float32)
    a = np.roll(a, (SHY, SHX), (0, 1))
    al = a[..., 3]
    s = np.maximum(al, 1e-3)
    return al, a[..., 0] / s, a[..., 1] / s, a[..., 2] / s


rgb = np.broadcast_to(NIGHT * .7, (H, W, 3)).copy()
la, nx, nz, dep = part("liver")
pa, pnx, pnz, pdep = part("portal")
ha, hnx, hnz, hdep = part("hepatic")

L = np.array([-.5, -.72, .48])   # world light: from upper left, on the camera side
ny = -np.sqrt(np.clip(1 - nx ** 2 - nz ** 2, 0, 1))
lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)

ss = 2
r = np.random.default_rng(5)
cell = Image.new("RGB", (W * ss, H * ss), (4, 2, 4))
d = ImageDraw.Draw(cell)
GAP = 19
ys = np.where(la.max(1) > 0)[0]
xs = np.where(la.max(0) > 0)[0]
pts = []
for j, y in enumerate(np.arange(ys.min() - GAP, ys.max() + GAP, GAP * .87)):
    for x in np.arange(xs.min() - GAP + (j % 2) * GAP / 2, xs.max() + GAP, GAP):
        px, py = x + r.normal(0, 1.8), y + r.normal(0, 1.8)
        ix, iy = int(np.clip(px, 0, W - 1)), int(np.clip(py, 0, H - 1))
        if la[iy, ix] > .02:
            pts.append((px, py, lam[iy, ix]))
print("cells", len(pts))
for px, py, l in pts:
    t = float(np.clip((l - .05) / .85, 0, 1))
    col = DEEP * (.40 + .60 * t / .62) if t < .62 else DEEP * (1 - (t - .62) / .38) + RED * ((t - .62) / .38)
    rr = (GAP * .5 + r.uniform(-.9, .5)) * ss
    d.ellipse((px * ss - rr, py * ss - rr, px * ss + rr, py * ss + rr), fill=rgb8(col), outline=(4, 2, 4), width=2 * ss)
cell = np.asarray(cell.resize((W, H), Image.LANCZOS), np.float32) / 255
rgb = rgb * (1 - la[..., None]) + cell * la[..., None]
rim = np.clip(gblur(la, 2.5) * 2.4, 0, 1) * (1 - la)
rgb = rgb * (1 - rim[..., None]) + BONE * .85 * rim[..., None] * (rim > .25)[..., None] + rgb * 0 * rim[..., None]


def tree(rgb, a, nx_, nz_, col):
    ny_ = -np.sqrt(np.clip(1 - nx_ ** 2 - nz_ ** 2, 0, 1))
    l = np.clip(nx_ * L[0] + ny_ * L[1] + nz_ * L[2], 0, 1)
    c = col[None, None] * (.66 + .40 * l[..., None])
    halo = np.clip(gblur(a, 1.6) * 4, 0, 1)
    rgb = rgb * (1 - halo[..., None])
    return rgb + np.minimum(c, 1) * a[..., None]


rgb = tree(rgb, ha, hnx, hnz, BLUE)
rgb = tree(rgb, pa, pnx, pnz, BONE)
im = to_pil(rgb)

for name, a in (("liver", la), ("portal", pa), ("hepatic", ha)):
    ys_, xs_ = np.where(a > .5)
    print(name, xs_.min(), xs_.max(), ys_.min(), ys_.max())

# one big number, one line of what it counts
text(im, (96, 300), "1,412", sans(232, 600), fill=BONE, anchor="ls")
text(im, (96, 408), "deaths in Hong Kong, 2022", sans(58, 500), anchor="ls")

text(im, (610, 640), "liver", sans(56, 600), anchor="lm")
leader(im, (735, 640), (884, 640), case=BLACK)
text(im, (1440, 790), "portal vein", sans(56, 600), anchor="lm")
leader(im, (1428, 790), (1332, 742), case=BLACK)
text(im, (1450, 92), "hepatic veins", sans(56, 600), anchor="lm")
leader(im, (1440, 104), (1300, 232), case=BLACK)
text(im, (96, 984), "HKCaR 2022 · BodyParts3D, DBCLS, CC BY 4.0", mono(26), min_px=24)
x0, y0, x1, y1 = tag(im, (1340, 900), "schematic", "schematic", size=30)
leader(im, (x0 + 4, y0 + 26), (1130, 770), case=BLACK)
save(im, "F1.png")
