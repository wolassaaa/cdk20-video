"""HKBU SCIE1007 coursework science video. Style scout g1: a watercolour molecular landscape, method only. The protein is sliced open on real atoms. Colour follows the real sequence: oily, polar, plus and minus side chains. The only other thing drawn is water, the one molecule that is safely real, at true size, packed the way a crowd is packed."""
from glib import *

A = atoms()
S = surface()
xyz0 = A["xyz"] - S["center"]
R = rot(-90, 0, 12)
V = xyz0 @ R.T
SC = 13.8; cx, cy = 690, 366
zcut = 3.0
rng = np.random.default_rng(6)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

KD = {"ALA": 0, "VAL": 0, "ILE": 0, "LEU": 0, "MET": 0, "PHE": 0, "TRP": 0, "CYS": 0, "PRO": 0,
      "SER": 1, "THR": 1, "ASN": 1, "GLN": 1, "GLY": 1, "TYR": 1, "HIS": 1,
      "LYS": 2, "ARG": 2,
      "ASP": 3, "GLU": 3}
PAL = np.array([[.96, .66, .10], [.93, .40, .22], [.84, .12, .36], [.46, .20, .68]], np.float32)
cls = np.array([KD[r] for r in A["resn"]])
pcol = PAL[cls]
back = np.isin(A["name"], ["N", "CA", "C", "O"])
pcol = np.where(back[:, None], pcol * .78 + np.array([.97, .90, .72], np.float32) * .22, pcol)

# water: true geometry, a fair packing, only where no atom of the protein sits
xs = np.arange(-cx / SC - 3, (W - cx) / SC + 3, 3.05)
ys = np.arange(-(H - cy) / SC - 3, cy / SC + 3, 2.64)
pos = []
for k, z in enumerate((zcut - .6, zcut - 3.6, zcut - 6.6)):
    for j, y in enumerate(ys):
        for x in xs:
            pos.append((x + (j % 2) * 1.52 + (k % 2) * 1.2, y + (k % 3) * .9, z))
pos = np.array(pos, np.float32) + rng.normal(0, .42, (len(pos), 3)).astype(np.float32)
keep = np.ones(len(pos), bool)
for s in range(0, len(pos), 800):
    d2 = ((pos[s:s + 800, None] - V[None]) ** 2).sum(-1)
    keep[s:s + 800] = d2.min(1) > 2.9 ** 2
pos = pos[keep]
th = 104.5 / 2 * np.pi / 180
XYZ = [V]; RAD = [np.full(len(V), 1.72, np.float32)]; COL = [pcol]
MOL = [A["resi"].astype(np.int32)]
Wlight = np.array([.33, .76, .80], np.float32); Wdeep = np.array([.10, .50, .70], np.float32)
wx, wr, wc, wm = [], [], [], []
for i, p in enumerate(pos):
    a = rng.uniform(0, 6.28); b = rng.uniform(-.8, .8)
    u = np.array([np.cos(a), np.sin(a), b * .4], np.float32); u /= np.linalg.norm(u)
    v = np.array([-np.sin(a), np.cos(a), -b * .3], np.float32); v -= u * (v @ u); v /= np.linalg.norm(v)
    h1 = p + .96 * (np.cos(th) * u + np.sin(th) * v); h2 = p + .96 * (np.cos(th) * u - np.sin(th) * v)
    tint = rng.uniform(0, 1)
    co = Wlight * (1 - tint) + Wdeep * tint
    wx += [p, h1, h2]; wr += [1.50, 1.12, 1.12]
    wc += [co, co * .86 + .14, co * .86 + .14]; wm += [1000 + i] * 3
XYZ.append(np.array(wx, np.float32)); RAD.append(np.array(wr, np.float32)); COL.append(np.array(wc, np.float32)); MOL.append(np.array(wm, np.int32))
XYZ = np.vstack(XYZ); RAD = np.concatenate(RAD); COL = np.vstack(COL); MOL = np.concatenate(MOL)
P = spheres(XYZ, RAD, np.eye(3, dtype=np.float32), SC, cx, cy, clip=zcut)
I = P["id"]; m = I >= 0; J = np.maximum(I, 0)
col = np.where(m[..., None], COL[J], np.array([.86, .94, .92], np.float32))
mol = np.where(m, MOL[J], -1)
isp = np.where(m, MOL[J] < 1000, False)
n = P["n"]; z = P["z"]
cutface = m & (z >= zcut - .01)

# the cut plane sits full strength, things behind it thin toward paper, the way a wash is layered
dep = np.clip((zcut - z) / 9, 0, 1) * m
paper = np.array([.985, .965, .91], np.float32)
col = col * (1 - .46 * dep[..., None]) + paper * .46 * dep[..., None]
# soft roundness on spheres, none on the cut
lamb = np.clip(n @ np.array([-.4, .55, .73], np.float32), 0, 1)
col = col * (.80 + .30 * lamb[..., None])

# edges: dark pooled line round each molecule, faint between atoms of one molecule
def edges(a):
    e = np.zeros(a.shape, bool)
    e[:-1] |= a[:-1] != a[1:]
    e[:, :-1] |= a[:, :-1] != a[:, 1:]
    return e.astype(np.float32)


wob = (fbm(beta=2.6, seed=12) - .5) * 6
ex = np.clip(xx + wob, 0, W - 1).astype(np.int32); ey = np.clip(yy + wob, 0, H - 1).astype(np.int32)
molw = mol[ey, ex]; colw = col[ey, ex]; idw = I[ey, ex]
e_m = edges(molw); e_a = edges(idw)
line = np.clip(gblur(e_m, .95) * 3.1, 0, 1)
line2 = np.clip(gblur(e_a, .8) * 1.5, 0, 1)
pool = gblur(e_m, 4.5) * 2.6

# pigment: granulation, uneven flood, back-runs
gran = fbm(beta=.9, seed=13); flood = fbm(beta=2.7, seed=14)
rgb = colw * (1 - .34 * np.clip(pool, 0, 1)[..., None])
rgb = rgb * (.84 + .28 * flood[..., None]) * (.93 + .14 * gran[..., None])
LINE = np.array([.10, .06, .13], np.float32)
rgb = rgb * (1 - line2[..., None] * .30) + LINE * line2[..., None] * .30
rgb = rgb * (1 - line[..., None] * .84) + LINE * line[..., None] * .84
# a stronger contour round the protein so the big shape survives at thumbnail size
pm = gblur(isp[ey, ex].astype(np.float32), 2.4)
pl = np.clip(1 - np.abs(pm - .5) * 3.4, 0, 1)
rgb = rgb * (1 - pl[..., None] * .92) + LINE * pl[..., None] * .92
rgb = rgb + (isp[ey, ex].astype(np.float32) * (flood - .5))[..., None] * .05

# cold-press paper tooth over everything
tooth = fbm(beta=.7, seed=15)
rgb = rgb * (.965 + .07 * tooth[..., None])

# title: masking fluid. The letters were never painted, the wash pools hard against them
f = font("segoeprb.ttf", 150)
t = text_mask("CDK20", f, (20, 180), "ls")
tr = np.clip(gblur(t, 1.1) + (fbm(beta=1.7, seed=16) - .5) * .5, 0, 1)
tr = (tr > .5).astype(np.float32); tr = gblur(tr, .6)
ring = gblur(tr, 5.5) * (1 - tr)
rgb = rgb * (1 - np.clip(ring * 3.0, 0, 1)[..., None] * .92) + np.array([.04, .10, .22], np.float32) * np.clip(ring * 3.0, 0, 1)[..., None] * .92
rgb = rgb * (1 - tr[..., None]) + paper * tr[..., None]

# the label sits on a reserved strip of bare paper
lx0, ly0, lx1, ly1 = 840, 656, 1262, 704
lw = (fbm(beta=2.2, seed=18) - .5) * 9
lb = ((xx + lw > lx0) & (xx - lw < lx1) & (yy + lw > ly0) & (yy - lw < ly1)).astype(np.float32)
lb = gblur(lb, .7)
rgb = rgb * (1 - lb[..., None]) + paper * lb[..., None]
tg = text_mask(LABEL, font("georgiab.ttf", 25), ((lx0 + lx1) / 2, (ly0 + ly1) / 2), "mm")
rgb = over(rgb, (.08, .06, .12), tg)
save(rgb, "g1_goodsell.png")
print("waters", len(pos), "protein atoms", len(V))
