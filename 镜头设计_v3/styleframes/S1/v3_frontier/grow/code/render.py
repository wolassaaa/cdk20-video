"""GROW / render: the 10 s test.  numpy + PIL, one process, deterministic.

Layers (all at native 1:1 pixels, nothing upscaled):
  tree     space-colonisation vessels, drawn as tapered vector quads at 3x and box-reduced (crisp)
  phys     Jones/Physarum agents feeding on the tree: anastomoses + capillary body + capsule rim
  scars    bone-grey skeleton of each starved subtree
  type     PIL/FreeType at 1x

python render.py --out DIR [--only 30,90,...] [--end 300]
"""
import numpy as np, os, sys, time, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from physarum import Physarum

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--only", default="")
ap.add_argument("--end", type=int, default=300)
ap.add_argument("--start", type=int, default=0)
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)
ONLY = set(int(x) for x in A.only.split(",") if x) or None

WORK = os.path.join(HERE, "..", "work")
FONT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/fonts/"
W, H, FPS = 1920, 1080, 30
RED = np.array([232, 25, 15], np.float32)
BG = np.array([6, 6, 6], np.float32)
BONE = np.array([237, 235, 228], np.float32)

d = np.load(os.path.join(WORK, "liver_proj.npz"))
t_ = np.load(os.path.join(WORK, "tree.npz"))
f_ = np.load(os.path.join(WORK, "fields.npz"))
X0, Y0, CW, CH = [int(v) for v in f_["crop"]]
OFF = np.array([X0, Y0], np.float32)
P = t_["P"] - OFF
par, lev, Ln, leaves, height, seg = t_["parent"], t_["level"], t_["L"], t_["leaves"], t_["height"], t_["seg"]
nchild = t_["nchild"]
n = len(P)
mask = d["mask"][Y0:Y0 + CH, X0:X0 + CW]
inside = mask > 0.5
seedm, distm, Lmap, hmap, terr = f_["seed"], f_["dist"], f_["Lmap"], f_["hmap"], f_["terr"]
reg_of, bases = f_["reg_of"], f_["bases"]
rng = np.random.default_rng(23)

# ----------------------------------------------------------------- clock
BEAT = 0.80
BEATS = 7.0 + BEAT * np.arange(-8, 4)           # 0.6 ... 7.0 ... 9.4
DEATH_BEAT = [3, 4, 5, 6]                       # index into BEATS: 3.0, 3.8, 4.6, 5.4
T_NUM, T_SUB, T_SRC = 7.0, 7.4, 7.8
C_PULSE = 1400.0                                # px/s, wave speed along the tree


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# growth time of each node: the front runs along the tree, slower at finer levels
vel = {0: 1150.0, 1: 640.0, 2: 300.0, 3: 210.0}
delay = {2: 0.07, 3: 0.05}
bv = rng.uniform(0.82, 1.18, n).astype(np.float32)   # per-sprout speed factor, inherited
tb = np.zeros(n, np.float32)
tb[0] = 0.13
f = np.ones(n, np.float32)
for i in range(1, n):
    p = par[i]
    new = lev[i] != lev[p]
    f[i] = bv[i] if new else f[p]
    tb[i] = tb[p] + seg[i] / (vel[int(lev[i])] * f[i]) + (delay.get(int(lev[i]), 0) if new else 0)
print("growth ends", tb.max())
tbp = tb[par]; tbp[0] = 0
order = np.argsort(leaves)                      # thin first, trunks last
kids_order = np.arange(n - 1, 0, -1)
par_l = par.tolist()

NR = int(t_["nroot"])
stem = np.ones(n, np.float32)
stem[:NR] = 0.34 + 0.66 * smooth((Ln[:NR] / Ln[NR - 1] - 0.15) / 0.85) ** 1.3
stem_i = np.ones(n, np.float32)
stem_i[:NR] = 0.50 + 0.50 * smooth((Ln[:NR] / Ln[NR - 1] - 0.0) / 0.9)
# pulse table
TAB_DT = 1 / 240.0
tau = np.arange(-2, 12, TAB_DT, dtype=np.float32)


def bump(x):
    return np.where(x < 0, np.exp(-(x / 0.030) ** 2), np.exp(-(x / 0.135) ** 2))


def wave(beats, amps):
    w = np.zeros_like(tau)
    for b, a in zip(beats, amps):
        w = np.maximum(w, a * bump(tau - b))
    return w.astype(np.float32)


amp_all = np.array([1, 1, 1, 1, 0.96, 0.92, 0.88, 0.84, 1.0, 0.74, 0.72, 0.70], np.float32)
WAVE = wave(BEATS, amp_all)
WAVE_K = []
for k, bi in enumerate(DEATH_BEAT):
    a = amp_all.copy(); a[bi] = 1.5                 # the last pulse into a region is its brightest
    WAVE_K.append(wave(BEATS[:bi + 1], a[:bi + 1]))
nreg = len(bases)
T0 = np.array([BEATS[bi] + Ln[bases[k]] / C_PULSE + 0.13 for k, bi in enumerate(DEATH_BEAT)])
RET = 1.05                                       # retraction seconds
Hk = height[bases]
print("deaths start", T0.round(2), "heights", Hk.round(0))
reg_nodes = [np.nonzero(reg_of == k)[0] for k in range(nreg)]
reg_px = [terr == k for k in range(nreg)]


def wlook(table, phase):
    idx = np.clip(((phase + 2) / TAB_DT).astype(np.int32), 0, len(table) - 1)
    return table[idx]


# ----------------------------------------------------------------- static maps
def erode(m, k):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(k)), np.uint8) > 0


rim_in = erode(inside, 3)
rim_food = (rim_in & ~erode(inside, 7)).astype(np.float32)
edge_line = (inside & ~erode(inside, 3)).astype(np.float32)
tbmap = tb[seedm] + distm / 180.0
_m = mask.copy()
caps = np.zeros_like(_m)
caps[1:-1, 1:-1] = np.maximum(np.abs(_m[1:-1, 2:] - _m[1:-1, :-2]), np.abs(_m[2:, 1:-1] - _m[:-2, 1:-1]))
caps = np.clip(caps * 1.1, 0, 1)

SS = 3
WIDTH0, GAMMA = 0.40, 2.2


def draw_tree(wid, fac, inten, sel=None, ss=SS):
    """vector quads + round joints at ss x; returns crop-sized float32 (premultiplied intensity)."""
    im = Image.new("F", (CW * ss, CH * ss), 0.0)
    dr = ImageDraw.Draw(im)
    idx = order[(fac[order] > 0.003)]
    if sel is not None:
        idx = idx[sel[idx]]
    idx = idx[idx > 0]
    a = P[par[idx]] * ss
    b = a + (P[idx] - P[par[idx]]) * fac[idx][:, None] * ss
    dv = b - a
    ln = np.sqrt((dv ** 2).sum(1)) + 1e-6
    nor = np.stack([-dv[:, 1], dv[:, 0]], 1) / ln[:, None]
    wa = wid[par[idx]] * ss * 0.5
    wb = wid[idx] * ss * 0.5
    q = np.stack([a + nor * wa[:, None], b + nor * wb[:, None], b - nor * wb[:, None], a - nor * wa[:, None]], 1)
    ql, al, bl = q.tolist(), a.tolist(), b.tolist()
    wbl = wb.tolist(); inl = inten[idx].tolist()
    poly, line, ell = dr.polygon, dr.line, dr.ellipse
    for j in range(len(idx)):
        w = wbl[j] * 2
        v = inl[j]
        if w < 1.2:
            line([tuple(al[j]), tuple(bl[j])], fill=v * max(w, 0.25), width=1)
        else:
            qq = ql[j]
            poly([tuple(qq[0]), tuple(qq[1]), tuple(qq[2]), tuple(qq[3])], fill=v)
            r = wbl[j]
            x, y = bl[j]
            ell([x - r, y - r, x + r, y + r], fill=v)
    arr = np.asarray(im, np.float32)
    return arr.reshape(CH, ss, CW, ss).mean((1, 3))


w_final = WIDTH0 * leaves ** (1 / GAMMA)
w_final[0] = w_final[1]
SCARS = []
for k in range(nreg):
    sel = reg_of == k
    wsc = np.clip(w_final * 0.42, 0.55, 1.7)
    arr = draw_tree(wsc, np.ones(n, np.float32), np.ones(n, np.float32), sel)
    SCARS.append(arr)
print("scars ready")

# ----------------------------------------------------------------- hepatic veins (second tree, stays quiet)
b_ = np.load(os.path.join(WORK, "tree_b.npz"))
Pb, parb, levb, Lb, lvb, segb, chb = b_["P"] - OFF, b_["parent"], b_["level"], b_["L"], b_["leaves"], b_["seg"], b_["nchild"]
nb = len(Pb)
tb_b = np.zeros(nb, np.float32); tb_b[0] = 0.55
velb = {0: 900.0, 1: 560.0, 2: 260.0}
fb = rng.uniform(0.85, 1.15, nb).astype(np.float32)
for i in range(1, nb):
    p = parb[i]
    if levb[i] != levb[p]:
        tb_b[i] = tb_b[p] + segb[i] / (velb[int(levb[i])] * fb[i]) + 0.06
    else:
        fb[i] = fb[p]
        tb_b[i] = tb_b[p] + segb[i] / (velb[int(levb[i])] * fb[i])
print("blue growth ends", tb_b.max())
tbp_b = tb_b[parb]; tbp_b[0] = 0
wb_final = 0.40 * lvb ** (1 / 2.3)
order_b = np.argsort(lvb)
bx = np.clip(Pb[:, 0].astype(int), 0, CW - 1); by = np.clip(Pb[:, 1].astype(int), 0, CH - 1)
reg_b = terr[by, bx]
hm_b = hmap[by, bx]
BLUE = np.array([31, 59, 255], np.float32)


def draw_blue(fac, inten, ss=SS):
    im = Image.new("F", (CW * ss, CH * ss), 0.0)
    dr = ImageDraw.Draw(im)
    idx = order_b[(fac[order_b] > 0.003) & (order_b > 0)]
    a = Pb[parb[idx]] * ss
    b = a + (Pb[idx] - Pb[parb[idx]]) * fac[idx][:, None] * ss
    dv = b - a
    ln = np.sqrt((dv ** 2).sum(1)) + 1e-6
    nor = np.stack([-dv[:, 1], dv[:, 0]], 1) / ln[:, None]
    wa = wb_final[parb[idx]] * ss * 0.5
    wb = wb_final[idx] * ss * 0.5
    q = np.stack([a + nor * wa[:, None], b + nor * wb[:, None], b - nor * wb[:, None], a - nor * wa[:, None]], 1)
    ql, al, bl, wbl, inl = q.tolist(), a.tolist(), b.tolist(), wb.tolist(), inten[idx].tolist()
    for j in range(len(idx)):
        w = wbl[j] * 2
        v = inl[j]
        if w < 1.2:
            dr.line([tuple(al[j]), tuple(bl[j])], fill=v * max(w, 0.3), width=1)
        else:
            qq = ql[j]
            dr.polygon([tuple(qq[0]), tuple(qq[1]), tuple(qq[2]), tuple(qq[3])], fill=v)
            r = wbl[j]; x, y = bl[j]
            dr.ellipse([x - r, y - r, x + r, y + r], fill=v)
    return np.asarray(im, np.float32).reshape(CH, ss, CW, ss).mean((1, 3))


# ----------------------------------------------------------------- type
tx = Image.new("L", (W, H), 0)
tx2 = Image.new("L", (W, H), 0)
tx3 = Image.new("L", (W, H), 0)
big = ImageFont.truetype(FONT + "InterTight.ttf", 268); big.set_variation_by_axes([140])
mid = ImageFont.truetype(FONT + "InterTight.ttf", 45); mid.set_variation_by_axes([300])
mono = ImageFont.truetype(FONT + "MartianMono.ttf", 17); mono.set_variation_by_axes([300, 100])
TX = 1058
ImageDraw.Draw(tx).text((TX, 548), "1,412", font=big, fill=255)
ImageDraw.Draw(tx2).text((TX + 9, 872), "deaths in Hong Kong, 2022", font=mid, fill=255)
ImageDraw.Draw(tx3).text((TX + 10, 985), "Hong Kong Cancer Registry, Hospital Authority", font=mono, fill=255)
TYPE = [np.asarray(x, np.float32) / 255 for x in (tx, tx2, tx3)]

# ----------------------------------------------------------------- threads: the scars let down four lines to the four digits
NUM = "1,412"
TH_BOX = (980, 240, 1700, 640)     # x0, y0, x1, y1 full-frame
TH_T0, TH_T1 = 6.55, 7.0
threads = []
for ci, reg in zip((0, 2, 3, 4), (3, 3, 0, 0)):
    x0 = TX + big.getlength(NUM[:ci])
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).text((x0, 548), NUM[ci], font=big, fill=255)
    a = np.asarray(g) > 128
    ys_ = np.nonzero(a.any(1))[0][0]
    xs_ = np.nonzero(a[ys_ + 1])[0]
    tgt = np.array([xs_.mean(), ys_ + 1.0])
    nd = reg_nodes[reg]
    pp = P[nd] + OFF
    src = pp[np.argmin(np.abs(pp[:, 0] - tgt[0]) * 1.0 - pp[:, 1] * 0.75)]
    u = np.linspace(0, 1, 64)[:, None]
    th_r = np.random.default_rng(100 + ci)
    wob = sum(th_r.uniform(-1, 1) * np.sin(np.pi * u * (m + 1)) / (m + 1) for m in range(3)) * 9.0
    path = src + (tgt - src) * u + np.hstack([wob, wob * 0])
    threads.append(path)
print("thread lengths", [round(float(np.linalg.norm(p[-1] - p[0]))) for p in threads])


def draw_threads(u):
    ss = 3
    bw, bh = TH_BOX[2] - TH_BOX[0], TH_BOX[3] - TH_BOX[1]
    im = Image.new("L", (bw * ss, bh * ss), 0)
    dr = ImageDraw.Draw(im)
    for k, p in enumerate(threads):
        m = int(np.clip(u, 0, 1) * (len(p) - 1)) + 1
        q = ((p[:m + 1] - np.array(TH_BOX[:2])) * ss).tolist()
        if len(q) > 1:
            dr.line([tuple(x) for x in q], fill=255, width=3, joint="curve")
    arr = np.asarray(im, np.float32) / 255
    return arr.reshape(bh, ss, bw, ss).mean((1, 3))


# ----------------------------------------------------------------- simulation
E = os.environ.get
ph = Physarum(inside, seed=11, SA=float(E("SA", 45)), RA=float(E("RA", 30)), SO=float(E("SO", 6)), SS=1.0, DEP=1.0,
              DECAY=float(E("DEC", 0.30)), DIFF=float(E("DIFF", 0.25)))
keep_map = inside.astype(np.float32)
disp = np.zeros((CH, CW), np.float32)
K_TONE = float(os.environ.get("K_TONE", 3.5))
AG_PER_NODE = 22
spawned = np.zeros(n, bool)
NF = A.end
t_run = time.time()
for fr in range(0, NF):
    t = fr / FPS
    # --- tree state
    grow = np.clip((t - tbp) / (tb - tbp + 1e-6), 0, 1).astype(np.float32)
    fac = grow.copy()
    life = np.ones(n, np.float32)
    closed_cut = np.zeros(nreg, np.float32)
    rk = np.zeros(nreg, np.float32)
    for k in range(nreg):
        nodes = reg_nodes[k]
        r = float(smooth((t - T0[k]) / RET))
        rk[k] = r
        c = r * Hk[k]
        closed_cut[k] = c
        if t > T0[k]:
            hp = height[par[nodes]]; hi = height[nodes]
            fac[nodes] *= np.clip((hp - c) / (hp - hi + 1e-6), 0, 1)
            life[nodes] = 1 - 0.32 * smooth((t - T0[k]) / 0.4)
    # visible leaf count -> pipe-model width
    c = (fac * (nchild == 0)).tolist()
    for i in kids_order.tolist():
        c[par_l[i]] += c[i]
    cnt = np.maximum(np.asarray(c, np.float32), np.minimum(fac * 3, 1))
    wid = WIDTH0 * cnt ** (1 / GAMMA) * stem
    wid[:NR] = np.maximum(wid[:NR], 2.4 * (grow[:NR] > 0))
    # --- pulse on nodes
    ph_n = t - Ln / C_PULSE
    wn = wlook(WAVE, ph_n)
    for k in range(nreg):
        nodes = reg_nodes[k]
        wn[nodes] = wlook(WAVE_K[k], ph_n[nodes])
    tip = np.exp(-np.clip(t - tb, 0, None) / 0.10) * (t >= tbp)
    inten = (0.74 + 0.40 * wn + 0.9 * tip) * life * stem_i
    # --- food + agents
    fim = Image.new("F", (CW, CH), 0.0)
    dr = ImageDraw.Draw(fim)
    vis = np.nonzero(fac[1:] > 0.5)[0] + 1
    aa, bb = P[par[vis]].tolist(), P[vis].tolist()
    fv = np.clip(0.32 + wid[vis] / 3.0, 0, 1) * life[vis]
    ww = np.maximum(1, np.round(wid[vis])).astype(int).tolist()
    fvl = fv.tolist()
    for j in range(len(vis)):
        dr.line([tuple(aa[j]), tuple(bb[j])], fill=fvl[j], width=ww[j])
    food = np.asarray(fim, np.float32) + rim_food * (tbmap < t) * 0.9
    new = (~spawned) & (tb <= t)
    new_i = np.nonzero(new)[0]
    spawned |= new
    if len(new_i):
        px = P[new_i]
        xi, yi = np.clip(px[:, 0].astype(int), 0, CW - 1), np.clip(px[:, 1].astype(int), 0, CH - 1)
        ok = inside[yi, xi]
        px = px[ok]
        if len(px):
            m = len(px) * AG_PER_NODE
            sx = np.repeat(px[:, 0], AG_PER_NODE) + rng.normal(0, 1.5, m)
            sy = np.repeat(px[:, 1], AG_PER_NODE) + rng.normal(0, 1.5, m)
            ph.spawn(np.clip(sx, 0, CW - 1), np.clip(sy, 0, CH - 1))
    # --- starving territories: closed behind the retraction front
    closed = np.zeros((CH, CW), bool)
    for k in range(nreg):
        if t > T0[k]:
            closed |= reg_px[k] & (hmap < closed_cut[k])
    allowed = inside & ~closed
    ph.allowed = allowed
    keep = inside.astype(np.float32)
    keep[closed] = 0.91
    ph.keep_map = keep
    if len(ph.x):
        xi = np.clip(ph.x.astype(np.int32), 0, CW - 1); yi = np.clip(ph.y.astype(np.int32), 0, CH - 1)
        ph.keep(allowed[yi, xi])
    if t < 2.7:
        for _ in range(3):
            ph.step(food, 0.6, ss=1.0)
    else:
        ph.step(food, 0.6, ss=0.45)
    disp = disp * 0.72 + ph.T * 0.28

    if fr < A.start or (ONLY is not None and fr not in ONLY):
        continue
    # --- compose
    tree = draw_tree(wid, fac, inten)
    v = 1 - np.exp(-(disp / K_TONE) ** 1.5)
    v = smooth((v - 0.16) / 0.66)
    pm = wlook(WAVE, t - Lmap / C_PULSE)
    for k in range(nreg):
        pm[reg_px[k]] = wlook(WAVE_K[k], t - Lmap[reg_px[k]] / C_PULSE)
    vp = v * (0.46 + 0.54 * pm) * 0.92
    rimv = caps * smooth((t - tbmap) / 0.25) * (0.34 + 0.42 * pm)
    for k in range(nreg):
        if t > T0[k]:
            rimv[reg_px[k]] *= 1 - smooth((closed_cut[k] - hmap[reg_px[k]]) / 28.0)
    vp = 1 - (1 - vp) * (1 - rimv)
    glow = np.asarray(Image.fromarray((np.clip(tree, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)),
                      np.float32) / 255
    vp = vp * (1 - 0.8 * np.clip(glow * 3.5, 0, 1))      # no soft halo around the crisp trunks
    vv = 1 - (1 - np.clip(tree, 0, 1)) * (1 - vp) * (1 - glow * 0.30)
    dim = 1 - 0.14 * float(smooth((t - 7.0) / 1.0))
    for k in range(nreg):
        if t > T0[k]:
            x_ = (t - T0[k]) / 0.16
            dim *= 1 - 0.18 * float(x_ * np.exp(1 - x_))     # soft onset: a flinch, not a flicker
    vv *= dim
    full = np.broadcast_to(BG, (H, W, 3)).copy()
    # hepatic veins underneath, red lies over them (no additive mix -> no purple)
    fb_ = np.clip((t - tbp_b) / (tb_b - tbp_b + 1e-6), 0, 1).astype(np.float32)
    ib = np.full(nb, 0.62, np.float32)
    for k in range(nreg):
        if t > T0[k]:
            sel = reg_b == k
            ib[sel] *= 1 - smooth((closed_cut[k] - hm_b[sel]) / 40.0)
    vb_ = np.clip(draw_blue(fb_, ib), 0, 1) * dim
    crop_b = BG + vb_[..., None] * (BLUE - BG)
    crop_r = BG + vv[..., None] * (RED - BG)
    crop = np.where((vv >= vb_ * 0.9)[..., None], crop_r, crop_b)   # either red or blue, never a mix (no purple)
    # scars
    sc = np.zeros((CH, CW), np.float32)
    for k in range(nreg):
        if t > T0[k]:
            front = smooth((closed_cut[k] - hmap) / 28.0)
            s = SCARS[k] * front * 0.36 * float(smooth((t - T0[k] - 0.2) / 1.0))
            s = np.maximum(s, edge_line * reg_px[k] * front * 0.12 * float(smooth((t - T0[k] - 0.2) / 1.0)))
            sc = np.maximum(sc, s)
    crop = np.maximum(crop, BG + sc[..., None] * (BONE - BG))
    full[Y0:Y0 + CH, X0:X0 + CW] = crop
    if t > TH_T0:
        u_ = float(smooth((t - TH_T0) / (TH_T1 - TH_T0))) ** 1.6
        thr = draw_threads(u_) * 0.40
        reg_ = full[TH_BOX[1]:TH_BOX[3], TH_BOX[0]:TH_BOX[2]]
        full[TH_BOX[1]:TH_BOX[3], TH_BOX[0]:TH_BOX[2]] = reg_ + thr[..., None] * (BONE - reg_)
    for L_, t0 in zip(TYPE, (T_NUM, T_SUB, T_SRC)):
        al = float(smooth((t - t0) / (5 / FPS)))
        if al > 0:
            am = L_ * al * (1.0 if t0 != T_SRC else 0.55)
            full = full + am[..., None] * (BONE - full)
    Image.fromarray(np.clip(full + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(A.out, f"f_{fr:04d}.png"), compress_level=1)
    print(f"f{fr} agents {len(ph.x)} T p99 {np.percentile(ph.T[inside], 99):.1f} {time.time() - t_run:.0f}s", flush=True)
print("total", time.time() - t_run)
