"""HKBU SCIE1007 coursework science video. shanshui direction, shot T5 (W4): the key turns. The real pocket is a ravine in brush ink, our docked 048 is a thin pencil drawing, the measured number carries the only cinnabar seal on the page. Solid red block against open pencil line, so the two evidence levels differ by shape."""
from PIL import ImageFilter
from sbrush import *

yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
D = np.load(SCR / "pocket.npz")
v = D["verts"].astype(np.float32); q = D["quads"]; hid = D["hidden"]
cx0, cy0 = float(D["cx"]), float(D["cy"])
K = float(D["ppa"]); OX, OY = 1490, 500     # px per Angstrom and where the camera centre lands


def to(p):
    return OX + (p[..., 0] - cx0) * K, OY - (p[..., 1] - cy0) * K


# normals and a real-only render of what the S2plus code marks visible
n = np.zeros_like(v)
fn = np.cross(v[q[:, 2]] - v[q[:, 0]], v[q[:, 3]] - v[q[:, 1]]).astype(np.float32)
for i in range(4):
    np.add.at(n, q[:, i], fn)
n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
vis = np.zeros(len(v), bool); vis[np.unique(q[~hid])] = True
if (n[vis, 2] > 0).mean() < .5:
    n = -n
print("facing", (n[vis, 2] > 0).mean())
cell = (np.floor(v / 2.6).astype(np.int64) * np.array([73, 179, 283])).sum(1) % 400
nc = np.zeros((400, 3), np.float32); np.add.at(nc, cell, n); nc /= np.maximum(np.linalg.norm(nc, axis=1, keepdims=True), 1e-6)
nf = .45 * n + .55 * nc[cell]; nf /= np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-6)
ss = 2
px, py = to(v); px = px * ss; py = py * ss
idx = np.where(vis)[0]; idx = idx[np.argsort(v[idx, 2])]
I = -np.ones((SH * ss, SW * ss), np.int32)
r = int(np.ceil(.14 * K * ss))
dy, dx = np.mgrid[-r:r + 1, -r:r + 1]; k = dx * dx + dy * dy <= (r + .5) ** 2; dx, dy = dx[k], dy[k]
for s_ in range(0, len(idx), 20000):
    id_ = idx[s_:s_ + 20000]
    x = (np.round(px[id_]).astype(np.int32)[:, None] + dx[None]).ravel(); y = (np.round(py[id_]).astype(np.int32)[:, None] + dy[None]).ravel()
    ii = np.repeat(id_, len(dx)); g = (x >= 0) & (x < SW * ss) & (y >= 0) & (y < SH * ss)
    I[y[g], x[g]] = ii[g]
m_ = I >= 0; J = np.maximum(I, 0)


def dn(a):
    return a.reshape(SH, ss, SW, ss, *a.shape[2:]).mean((1, 3))


mk = dn(m_.astype(np.float32)); dv = np.maximum(mk, 1e-3)
Pn = dn(np.where(m_[..., None], n[J], 0)) / dv[..., None]; Pn = gblur(Pn, 1.8); Pn /= np.maximum(np.linalg.norm(Pn, axis=-1, keepdims=True), 1e-4)
Pf = dn(np.where(m_[..., None], nf[J], 0)) / dv[..., None]; Pf /= np.maximum(np.linalg.norm(Pf, axis=-1, keepdims=True), 1e-4)
Pz = dn(np.where(m_, v[J, 2], 0)) / dv
Ph = dn(np.where(m_, v[J, 1], 0)) / dv
P = dict(mask=mk.astype(np.float32), n=Pn.astype(np.float32), nf=Pf.astype(np.float32), z=Pz.astype(np.float32), hw=Ph.astype(np.float32), conf=np.ones_like(mk, np.float32), res=np.where(m_, cell[J], 0)[::ss, ::ss])
print("pocket covered", (mk > .5).mean())
Ik = ink_rock(P, seed=9, density=.9, strata_d=2.1, strata_k=.3)
print("tone", Ik["tone"][P["mask"] > .5].mean(), "wash", Ik["wash"][P["mask"] > .5].mean())
m = P["mask"]

# ligand, real coordinates, heavy atoms and real bonds only
lig = D["lig"]; heavy = D["heavy"]; el = D["el"]; bonds = D["bonds"]
lx, ly = to(lig)
hv = np.where(heavy)[0]
lcx, lcy = lx[hv].mean(), ly[hv].mean()

# the clearing: ink thins toward the drawn key, the blank paper is where the eye goes
d2 = np.full((SH, SW), 1e6, np.float32)
for i in hv:
    d2 = np.minimum(d2, (xx - lx[i]) ** 2 + (yy - ly[i]) ** 2)
clear = smooth01(46, 112, gblur(np.sqrt(d2), 6) + (fbm(SH, SW, 2.6, 61) - .5) * 60)
n1 = fbm(SH, SW, 3.0, 62)
edge = smooth01(.08, .62, gblur(m, 26) + (n1 - .5) * .35)     # crop walls of the pocket run out into mist
frame = clear * edge
kw = frame; ks = dissolve(np.clip(frame * 1.1, 0, 1), 63)

tone = np.array([.945, .905, .800], np.float32)   # the page warms here: dawn in the colour script
rgb = paper(seed=7, tone=tone)
rgb = far_hills(rgb, 1100, 130, .11, 51, 60)
rgb = lay(rgb, Ik, kw, ks)

# pencil: graphite is grey, thin, and doubles its line. Never wash, never ink
G = Image.new("L", (SW * 3, SH * 3), 0); dr = ImageDraw.Draw(G)
rngp = np.random.default_rng(3)
def pencil(a, b, width=3):
    for _ in range(2):
        j = rngp.normal(0, 1.1, 4)
        dr.line(((a[0] + j[0]) * 3, (a[1] + j[1]) * 3, (b[0] + j[2]) * 3, (b[1] + j[3]) * 3), fill=int(rngp.uniform(170, 235)), width=width)
for b in bonds:
    i, j = int(b[0]), int(b[1])
    if heavy[i] and heavy[j]:
        pencil((lx[i], ly[i]), (lx[j], ly[j]))
for i in hv:
    R_ = 6 if el[i] == "C" else 8.5
    for _ in range(2):
        o = rngp.normal(0, .9, 2)
        dr.ellipse(((lx[i] - R_ + o[0]) * 3, (ly[i] - R_ + o[1]) * 3, (lx[i] + R_ + o[0]) * 3, (ly[i] + R_ + o[1]) * 3), outline=int(rngp.uniform(180, 235)), width=3)
# label box: an open pencil rectangle, corners overshoot, as a hand ruled it
bx0, by0, bx1, by1 = 1290, 942, 1666, 1016
for a, b in (((bx0 - 8, by0), (bx1 + 10, by0 + 1)), ((bx0 - 6, by1), (bx1 + 8, by1 - 1)), ((bx0, by0 - 9), (bx0 + 1, by1 + 8)), ((bx1, by0 - 7), (bx1 - 1, by1 + 9))):
    pencil(a, b)
lead_a = (lcx - 26, ly[hv].max() + 20); lead_b = ((bx0 + bx1) / 2 - 40, by0 - 8)
pencil(lead_a, lead_b)
G = l2a(G, 3)
grain = np.clip(fbm(SH, SW, .4, 64) * 2.6 - .35, 0, 1)
GR = np.array([.20, .20, .215], np.float32)
a_ = np.clip(gblur(G, .5) * 1.6, 0, 1) * (.58 + .42 * grain)
rgb = rgb * (1 - a_[..., None]) + GR * a_[..., None]
tp = text_mask("OUR RE-DOCKING", vf(SANS, 38, 300), ((bx0 + bx1) / 2, (by0 + by1) / 2), "mm", w=SW, h=SH)
rgb = rgb * (1 - (tp * (.8 + .2 * grain))[..., None]) + GR * (tp * (.8 + .2 * grain))[..., None]

# text column
tx = 86
t1 = text_mask("Enzyme IC50", vf(SERIF, 52, 500), (tx, 318), "ls", w=SW, h=SH)
rgb = over(rgb, INK, t1)
t2 = text_mask("048 = 33.4 ± 22.6 nM", vf(SERIF, 92, 800), (tx - 4, 462), "ls", w=SW, h=SH)
rgb = over(rgb, INK, t2 * .985)
ff = vf(SERIF, 42, 450)
t3 = text_mask("Just this much cuts the", ff, (tx, 556), "ls", w=SW, h=SH) + text_mask("enzyme's activity in half.", ff, (tx, 614), "ls", w=SW, h=SH)
rgb = over(rgb, INK, np.clip(t3, 0, 1))

# the seal: white-letter cinnabar block, hand pressed, the only red on the page
sw_, sh_ = 420, 250
sc = Image.new("L", (sw_ * 3, sh_ * 3), 255); d = ImageDraw.Draw(sc)
fs = vf(SANS, 3 * 46, 800); fs2 = vf(SANS, 3 * 42, 700)
d.text((sw_ * 3 / 2, 70 * 3), "MEASURED ·", 0, font=fs, anchor="mm")
d.text((sw_ * 3 / 2, 128 * 3), "Ren 2023,", 0, font=fs2, anchor="mm")
d.text((sw_ * 3 / 2, 184 * 3), "Fig. 9A", 0, font=fs2, anchor="mm")
sc = sc.filter(ImageFilter.GaussianBlur(1.4)).point(lambda p: 255 if p > 128 else 0).rotate(-2.2, resample=Image.BICUBIC, expand=False, fillcolor=0)
sa = np.zeros((SH, SW), np.float32)
pat = np.asarray(sc.resize((sw_, sh_), Image.LANCZOS), np.float32) / 255
sx, sy = 86, 680
sa[sy:sy + sh_, sx:sx + sw_] = pat
ragged = (fbm(SH, SW, 2.2, 66) - .5) * 9
outer = ((xx + ragged > sx + 10) & (xx - ragged < sx + sw_ - 10) & (yy + ragged > sy + 10) & (yy - ragged < sy + sh_ - 10)).astype(np.float32)
sa = gblur(sa * outer, .6)
wear = np.clip(fbm(SH, SW, 1.1, 67) * 3.0 - .35, 0, 1) * np.clip(fbm(SH, SW, .3, 68) * 5 - .6, 0, 1)
press = sa * (.70 + .30 * wear)
rgb = rgb * (1 - press[..., None]) + CIN * press[..., None]
save_still(rgb, "T5.png")
