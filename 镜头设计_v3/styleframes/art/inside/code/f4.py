"""HKBU SCIE1007 coursework science video. Direction inside, F4 (script 4-03): the AI-predicted CDK20 with a tail it is unsure of.
Every position is the real AlphaFold DB v6 model. Colour and bead spacing follow the real per-residue confidence. The crowd is schematic."""
from ilib import *

SC, CX, CY = 15.5, 760, 560
xyz, name, resi = read_pdb()
conf = np.array(json.load(open(CONF))["confidenceScore"], np.float32)
ca_all = xyz[name == "CA"]
R = rotm(308.05, 46.04, 289.90)
cen = ca_all[:302].mean(0)
A = (xyz - cen) @ R.T
ca = (ca_all - cen) @ R.T

# crowd, opened up around the protein
rgb = crowd(seed=4)
rgb = dim(rgb, disc(CX + 60, CY - 20, 500, 120), .9)
rgb = dim(rgb, box(1330, 340, W, 590, 60), .85)
rgb = dim(rgb, box(0, 0, W, 170, 60), .55)
rgb = dim(rgb, box(1250, 620, W, H, 70), .8)

# real heavy atoms of the body
body = resi <= 302
Z, N, I = spheres(A[body], np.full(body.sum(), 1.7, np.float32), SC, CX, CY)
g = np.arange(body.sum())
m = I >= 0
L = np.array([-.45, .55, .70], np.float32)
lam = np.clip(N @ L, 0, 1)
z0, z1 = A[body, 2].min(), A[body, 2].max()
dep = np.clip((Z - z0) / (z1 - z0), 0, 1)
shade = .10 + .34 * dep * (.55 + .45 * lam)
acol = (BONE[None, None] * shade[..., None]) + (KLEIN[None, None] * (.42 * (1 - dep))[..., None])
e = edges(Z, I, np.ones(body.sum() + 1, np.int32), jump=.9, grow=1)
acol = np.where(e[..., None], acol * .25, acol)
a = down(m.astype(np.float32))
rgb = rgb * (1 - a[..., None]) + down(np.where(m[..., None], acol, 0)) * 1

# chain: the real backbone ribbon (AlphaFold DB v6, secondary structure from the model) where the model is confident. Residues under 70 lose the ribbon and become separate beads on a thread
G_ = np.load(WORK / "ribbon_geo.npy")
A_ = np.load(WORK / "ribbon_attr.npy")
cov = G_[..., 3]
s_ = np.maximum(cov, 1e-3)
rn = np.stack([G_[..., 0] / s_, G_[..., 1] / s_], -1)
rz = G_[..., 2] / s_ * 10          # Blender units back to Angstrom
rp = A_[..., 0] / s_
sure_r = conf >= 70                # a lone residue over 70 inside an unsure run is too short to draw as ribbon, so it stays with its neighbours
for i in range(1, 345):
    if sure_r[i] and not sure_r[i - 1] and not sure_r[i + 1]:
        sure_r[i] = False
ru = np.clip(np.round(A_[..., 2] / s_ * 345).astype(int), 0, 345)
keep = (cov > .5) & sure_r[ru]
Z2 = np.where(keep, rz.astype(np.float32), -1e6).astype(np.float32)
nzz = np.sqrt(np.clip(1 - (rn ** 2).sum(-1), 0, 1))
N2 = np.dstack([rn[..., 0] * keep, rn[..., 1] * keep, nzz * keep]).astype(np.float32)
I2 = np.where(keep, 0, -1).astype(np.int32)
P, idx = spline(ca, 16)
th = P[~sure_r[np.clip(np.round(idx).astype(int), 0, 345)]]
Z2, N2, I2 = spheres(th, np.full(len(th), .30, np.float32), SC, CX, CY, Z=Z2, Nn=N2, I=I2, id0=1)
n0 = 1 + len(th)
low = np.where(~sure_r)[0]
Z2, N2, I2 = spheres(ca[low], np.full(len(low), 1.5, np.float32), SC, CX, CY, Z=Z2, Nn=N2, I=I2, id0=n0)
col = np.zeros((n0 + len(low), 3), np.float32)
col[0] = BONE
col[1:n0] = BONE * .8
col[n0:] = BLUE
grp = np.concatenate([[1], np.full(len(th), 2), 3 + np.arange(len(low))]).astype(np.int32)
m2 = I2 >= 0
lam2 = np.clip(N2 @ L, 0, 1)
zr = Z2[keep]
zmin, zmax = np.percentile(zr, 1), np.percentile(zr, 99)
dep2 = np.clip((Z2 - zmin) / (zmax - zmin), 0, 1)[..., None]
isbead = I2 >= n0
c = col[np.maximum(I2, 0)] * (.66 + .42 * lam2[..., None]) * (.60 + .40 * dep2)
c = np.where(isbead[..., None], np.minimum(col[np.maximum(I2, 0)] * (.86 + .30 * lam2[..., None]), 1), c)
ed = edges(Z2, I2, grp, jump=.8, grow=2)
c = np.where(ed[..., None] & ~isbead[..., None], BLACK, c)
c = np.where(ed[..., None] & isbead[..., None], BONE, c)
c = np.where(m2[..., None], c, 0)
a2 = down(m2.astype(np.float32))
rgb = rgb * (1 - a2[..., None]) + down(c)

im = to_pil(rgb)
tail_pts = ca[302:]
tx = CX + tail_pts[:, 0] * SC
ty = CY - tail_pts[:, 1] * SC
print("tail px", tx.min(), tx.max(), ty.min(), ty.max())

# one reading at a time: what it is, then the doubt
tag(im, (96, 72), "AlphaFold DB v6 · predicted", "predicted", size=36, bg=NIGHT)
text(im, (96, 190), "CDK20", sans(84, 600))
k = 320 + np.argmin(np.abs(conf[302:] - conf[302:].min()))
tipx, tipy = CX + ca[325, 0] * SC, CY - ca[325, 1] * SC
leader(im, (1400, 470), (tipx, tipy))
text(im, (1416, 400), "floppy tail", sans(88, 600))
text(im, (1420, 500), "low confidence", sans(52, 500))

# legend, words only, no numbers
d = ImageDraw.Draw(im)
lx, ly = 1400, 800
d.rounded_rectangle((lx, ly - 12, lx + 110, ly + 12), 12, fill=rgb8(BONE), outline=(0, 0, 0), width=3)
text(im, (lx + 134, ly), "more confident", sans(40), anchor="lm")
for i in range(4):
    x = lx + 12 + i * 29
    d.ellipse((x - 12, ly + 72 - 12, x + 12, ly + 72 + 12), fill=rgb8(BLUE), outline=rgb8(BONE), width=3)
text(im, (lx + 134, ly + 72), "less confident", sans(40), anchor="lm")

# scale bar from PDB coordinates: 1 nm = 10 Angstrom = 10 x SC px
bx, by = 1400, 960
d.rectangle((bx, by, bx + 10 * SC, by + 8), fill=rgb8(BONE))
text(im, (bx + 10 * SC + 20, by + 4), "1 nm", sans(36), anchor="lm")
x0, y0, x1, y1 = tag(im, (96, 968), "schematic", "schematic", size=30, bg=NIGHT)
leader(im, ((x0 + x1) / 2, y0), (160, 842), case=BLACK)
save(im, "F4.png")
