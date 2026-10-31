"""HKBU SCIE1007 coursework science video. Style scout g9: stained glass. Each pane of the protein is one real residue, its glass colour is its real confidence band. The window is dark until light reaches it: the sun line is the AI."""
from glib import *

S = surface()
R = rot(-90, 0, 12)
SC = 11.2
P = smooth_pass(render(R, SC, 640, 350, S=S), 1.2)
m = (P["mask"] > .5); res = P["res"].copy(); conf = P["conf"]; n = P["n"]
rng = np.random.default_rng(4)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# confidence bands, the same four AlphaFold publishes, as pot-metal glass
COB = np.array([.035, .10, .62], np.float32)
SKY = np.array([.10, .42, .88], np.float32)
GLD = np.array([.98, .66, .07], np.float32)
RUB = np.array([.78, .035, .05], np.float32)
A = atoms()
pl = np.zeros(400, np.float32)
pl[A["resi"]] = A["conf"]
band = np.stack([COB, SKY, GLD, RUB])
bi = np.where(pl >= .9, 0, np.where(pl >= .7, 1, np.where(pl >= .5, 2, 3)))
tint = rng.uniform(.74, 1.18, (400, 1)).astype(np.float32)
paneRGB = band[bi] * tint
# every pane gets a little wobble of its own so no two match
paneRGB = paneRGB + rng.uniform(-.03, .03, (400, 3)).astype(np.float32)

# break large panes on the outline with the wobble a hand cut would give
wx = (fbm(beta=3.2, seed=1) - .5) * 9; wy = (fbm(beta=3.2, seed=2) - .5) * 9
ix = np.clip(xx + wx, 0, W - 1).astype(np.int32); iy = np.clip(yy + wy, 0, H - 1).astype(np.int32)
res = res[iy, ix]; m = m[iy, ix]

# ground: Chartres style diamond mosaic in blue and ruby, cut by iron bars
gs = 46
u = (xx + yy) / gs; v = (xx - yy) / gs
ci = np.floor(u).astype(np.int32); cj = np.floor(v).astype(np.int32)
gid = (ci * 73 + cj * 19) % 1024 + 1024
h = np.random.default_rng(9).random(2048)
gcol = np.where((h[gid] < .72)[..., None], np.array([.03, .08, .46], np.float32), np.array([.55, .02, .05], np.float32))
gcol = gcol * (.30 + .34 * h[(gid * 7) % 2048])[..., None]
dot = (((u - ci - .5) ** 2 + (v - cj - .5) ** 2) < .03) & (ci % 3 == 0) & (cj % 3 == 0)
gcol = np.where(dot[..., None], np.array([.70, .46, .12], np.float32), gcol)
gridlead = (np.minimum(np.minimum(u - ci, 1 - (u - ci)), np.minimum(v - cj, 1 - (v - cj))) < .035)

# composite pane ids. Residue pane ids are 1..346, ground ids 1024..2047
ids = np.where(m, res, gid)
base = np.where(m[..., None], paneRGB[np.minimum(res, 399)], gcol)

# lead lines wherever the pane id changes
e = np.zeros((H, W), bool)
e[:-1, :] |= ids[:-1, :] != ids[1:, :]
e[:, :-1] |= ids[:, :-1] != ids[:, 1:]
lead = gblur(e.astype(np.float32), 1.05) * 3.2
lead = np.clip(np.maximum(lead, gridlead * (~m) * 1.0), 0, 1)
# a heavier lead around the whole protein silhouette
sil = gblur(m.astype(np.float32), 2.2); sil = np.clip(1 - np.abs(sil - .5) * 4.5, 0, 1)
lead = np.maximum(lead, sil)

# glass body: streaks, seeds, and the painter's grisaille laid over each pane from real relief
streak = lic(fbm(beta=.8, seed=5), np.ones((H, W), np.float32) * .8, np.ones((H, W), np.float32) * .6, 18, 2.2)
streak = (streak - streak.mean()) / streak.std()
cav = cavity(P["z"] * SC, P["mask"], (3, 7, 16))
gris = np.clip(.25 + .75 * (n @ np.array([-.45, .5, .74], np.float32)), 0, 1)
gris = np.where(m, gris, 1.0)
lum = (1 + .10 * streak) * (.72 + .40 * gris) * (1 - .72 * np.clip(cav * 1.4, 0, 1) * m)
seed = (fbm(beta=.4, seed=6) > .78).astype(np.float32); seed = gblur(seed, .7) * .55
glass = base * lum[..., None] * (1 + seed[..., None] * .6)

# dead state: seen from inside with no sun, glass is grey-brown soot and only the lead shows
dead = (base.mean(-1, keepdims=True) * .18 + .025) * np.array([1, .96, .9], np.float32) * lum[..., None] * .75

# the sun line. Everything right of it transmits, a little past it the glass overexposes
d = (xx - 505 + .55 * (yy - 360)) / 1.0
lit = np.clip(d / 90 + .5, 0, 1)
lit = lit * lit * (3 - 2 * lit)
hot = np.exp(-(np.maximum(d - 20, 0) / 240) ** 2) * .55 + .95
rgb = dead * (1 - lit[..., None]) + glass * (hot * lit)[..., None] * 1.12

# light spills from bright panes across the lead, as it does on a real camera
b = rgb * (1 - lead[..., None])
g1 = gblur(np.clip(b - .28, 0, 2), 9); g2 = gblur(np.clip(b - .2, 0, 2), 34)
rgb = b + g1 * .55 + g2 * .34
rgb = rgb * (1 - .78 * lead[..., None])

# iron armature bars cross the window, the only things that stay black
bars = np.zeros((H, W), bool)
for bx in (230, 628, 1040):
    bars |= np.abs(xx - bx) < 7
for by in (242, 482):
    bars |= np.abs(yy - by) < 7
barsf = gblur(bars.astype(np.float32), .8)
rgb = rgb * (1 - barsf[..., None] * .96)

# title: letters are pale glass set straight into the window, each one its own pane in heavy lead
f = font("ariblk.ttf", 172)
t = text_mask("CDK20", f, (24, 700), "ls", spacing=-2)
halo = np.clip(gblur(t, 6.5) * 3.4, 0, 1)
rgb = rgb * (1 - halo[..., None] * .96)
leadt = np.clip(gblur(t, 2.4) * 4, 0, 1)
ribbon = np.clip(gblur(t, 14) * 3, 0, 1) * (1 - leadt)
pale = np.array([1.0, .86, .55], np.float32)[None, None] * (.97 + .025 * streak[..., None]) * (.94 + .2 * lit[..., None])
rgb = rgb * (1 - t[..., None]) + pale * t[..., None]
rgb = rgb + gblur(pale * t[..., None], 16) * .24

# label on a small pale quarry, plain enough to read
qx0, qy0, qx1, qy1 = 846, 648, 1254, 696
q = ((xx > qx0) & (xx < qx1) & (yy > qy0) & (yy < qy1)).astype(np.float32)
q = gblur(q, .7)
rgb = rgb * (1 - q[..., None]) + np.array([.97, .93, .78], np.float32) * q[..., None]
fr2 = np.clip(gblur(((xx > qx0 - 5) & (xx < qx1 + 5) & (yy > qy0 - 5) & (yy < qy1 + 5)).astype(np.float32), .7) - q, 0, 1)
rgb = rgb * (1 - fr2[..., None])
tag = text_mask(LABEL, font("georgiab.ttf", 24), ((qx0 + qx1) / 2, (qy0 + qy1) / 2), "mm")
rgb = over(rgb, (.08, .03, .02), tag)
save(rgb, "g9_stained_glass.png")
