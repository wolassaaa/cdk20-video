"""HKBU SCIE1007 coursework science video. Style scout g7: a Kowloon neon street. The protein is bent in glass tube: silhouette and real height contours, tail tubes in a different gas where confidence is low. One sign is left dark on purpose: the medicine sign, because the compound is not a medicine yet."""
from glib import *

S = surface()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
WHITE = np.array([1, .97, .94], np.float32)
PINK = np.array([1.0, .07, .42], np.float32)
RED = np.array([1.0, .10, .04], np.float32)
AMB = np.array([1.0, .50, .05], np.float32)
GRN = np.array([.10, 1.0, .46], np.float32)
CYN = np.array([.10, .72, 1.0], np.float32)
YEL = np.array([1.0, .84, .14], np.float32)
FJ = "C:/Windows/Fonts/msjhbd.ttc"


def neon(t, col, gain=1.0, hz=1.0):
    """One lit tube: white hot core, tight gas colour, wide haze."""
    t = np.clip(t, 0, 1.5)
    col = np.asarray(col, np.float32)
    g = gblur(t, 1.6)[..., None] * 1.15 + gblur(t, 5)[..., None] * .95 + (gblur(t, 18)[..., None] * .85 + gblur(t, 55)[..., None] * .6) * hz
    core = np.clip(gblur(t, .6) * 1.25 - .15, 0, 1)[..., None]
    return (col * g + (WHITE * .55 + col * .45) * core * 1.2) * gain


def iso(f, level, width):
    gy, gx = np.gradient(f)
    g = np.sqrt(gx ** 2 + gy ** 2) + 1e-4
    return np.exp(-(((f - level) / (g * width)) ** 2))


def outline(mask, s=2.2, level=.5, sharp=.15):
    f = gblur(mask, s)
    return np.exp(-(((f - level) / sharp) ** 2))


def homog(src, dst):
    A = []; b = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    h = np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64))
    return np.append(h, 1).reshape(3, 3)


def warp(img, quad, sw=W, sh=H):
    M = homog(quad, [(0, 0), (sw, 0), (sw, sh), (0, sh)])
    d = M[2, 0] * xx + M[2, 1] * yy + M[2, 2]
    sx = ((M[0, 0] * xx + M[0, 1] * yy + M[0, 2]) / d).astype(np.float32)
    sy = ((M[1, 0] * xx + M[1, 1] * yy + M[1, 2]) / d).astype(np.float32)
    ins = ((sx >= 0) & (sx < sw - 1) & (sy >= 0) & (sy < sh - 1)).astype(np.float32)
    out = sample(img, sx, sy)
    return out * (ins[..., None] if img.ndim == 3 else ins), ins


# ---- night sky and the far street: crowded, out of focus, nothing readable as a brand
rgb = np.stack([.012 + .05 * (yy / H), .008 + .012 * (yy / H), .03 + .06 * (yy / H)], -1).astype(np.float32)
rng = np.random.default_rng(12)
far = np.zeros((H, W, 3), np.float32)
PAL = [PINK, GRN, CYN, YEL, RED, AMB]
lay = np.zeros((2, 6, H, W), np.float32)
WORDS = ["\u8336\u9910\u5ef3", "\u91d1\u884c", "\u62bc", "\u7ca5\u9eb5", "\u6dbc\u8336", "\u9152\u5bb6", "\u65c5\u9928", "\u71d2\u81d8", "\u5f8b\u5e2b\u6a13", "\u627e\u63db"]
vp = (1120, 330)
for i in range(84):
    d_ = rng.uniform(.14, 1) ** 1.3
    x = vp[0] + (rng.uniform(-1.5, 1.1)) * 900 * d_ * .62
    y = vp[1] + rng.uniform(-1.05, .85) * 560 * d_
    hh = rng.uniform(.45, 1) * 280 * d_; ww = hh * rng.uniform(.3, .62)
    w_ = WORDS[rng.integers(len(WORDS))]
    ci_ = rng.integers(6)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    dr.rectangle((x, y, x + ww, y + hh), outline=255, width=max(1, int(4 * d_)))
    sz = max(10, int(ww * .72))
    ft = ImageFont.truetype(FJ, sz)
    for j, ch in enumerate(w_):
        dr.text((x + ww / 2, y + (j + .5) * hh / len(w_)), ch, 255, font=ft, anchor="mm")
    t = np.asarray(im, np.float32) / 255
    lay[int(d_ > .45), ci_] += t * (.5 + .5 * d_)
for dp in (0, 1):
    for ci_ in range(6):
        far += neon(gblur(lay[dp, ci_], 2.1 - dp * 1.3), PAL[ci_], .52, .10)
rgb = rgb + far

# nearer signs, sharp, crowding every edge of the frame
for x, y, ww, hh, w_, col, vert in ((6, 6, 112, 318, "茶餐廳", GRN, 1), (128, -6, 156, 150, "押", RED, 1), (296, 2, 262, 96, "金行", YEL, 0),
                                    (578, 0, 112, 178, "粥麵", CYN, 1), (4, 338, 138, 280, "涼茶", PINK, 1), (150, 500, 132, 122, "酒家", AMB, 0),
                                    (812, 410, 120, 214, "旅館", GRN, 1)):
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    dr.rectangle((x, y, x + ww, y + hh), outline=255, width=4)
    dr.rectangle((x + 8, y + 8, x + ww - 8, y + hh - 8), outline=120, width=2)
    if vert:
        sz = int(min(ww * .74, hh * .9 / len(w_))); ft = ImageFont.truetype(FJ, sz)
        for j, ch in enumerate(w_):
            dr.text((x + ww / 2, y + (j + .5) * hh / len(w_)), ch, 255, font=ft, anchor="mm")
    else:
        sz = int(min(hh * .74, ww * .9 / len(w_))); ft = ImageFont.truetype(FJ, sz)
        for j, ch in enumerate(w_):
            dr.text((x + (j + .5) * ww / len(w_), y + hh / 2), ch, 255, font=ft, anchor="mm")
    t = np.asarray(im, np.float32) / 255
    box_ = ((xx > x) & (xx < x + ww) & (yy > y) & (yy < y + hh)).astype(np.float32)
    rgb = rgb * (1 - box_[..., None] * .86) + box_[..., None] * np.asarray(col, np.float32) * .05
    rgb = rgb + neon(gblur(t, .7), col, .62, .14)

# ---- hero sign, built flat then hung in perspective
SC = 16.0
R = rot(-90, 0, 12)
P = smooth_pass(render(R, SC, 640, 372, S=S), 2.2)
m = P["mask"]
mS = gblur(m, 7)  # glass cannot bend tight, so the outline is simplified
ms = (mS > .5).astype(np.float32)
f = gblur(P["z"] * m, 6.5) + 40 * (1 - mS)
inner = np.zeros((H, W), np.float32)
ins_ = gblur(ms, 6)
for lv in np.arange(P["zmin"] + 8, P["zmax"], 3.1):
    inner = np.maximum(inner, iso(f, lv, 1.5))
inner = inner * (ins_ > .92)
tail = np.clip(gblur((P["conf"] < .7).astype(np.float32) * m, 7) * 1.9, 0, 1)
sil1 = outline(ms, 2.0, .5, .14)
sil2 = outline(ms, 9.0, .78, .05) * (ins_ > .55)

em = neon(sil1 * (1 - tail), PINK, 1.1) + neon(sil1 * tail, AMB, 1.1)
em = em + neon(sil2 * (1 - tail), CYN, .85) + neon(sil2 * tail, RED, .85)
em = em + neon(inner * (1 - tail), GRN, .72) + neon(inner * tail, RED, .72)

# sheet metal behind the tubes, cut to the protein's shape: the crowd stays visible round it
panel = ms[..., None] * np.array([.075, .008, .04], np.float32)
gr = (((xx % 92) < 2.4) | ((yy % 92) < 2.4)).astype(np.float32)
panel = panel + (gr * ms)[..., None] * np.array([.05, .03, .05], np.float32)
panel = panel + gblur(em, 9) * .20 * ms[..., None]
q1 = [(-40, -32), (934, 30), (934, 610), (-40, 690)]
wp, _ = warp(panel, q1)
wem, _ = warp(em, q1)
wms, _ = warp(ms, q1)
rgb = rgb * (1 - gblur(wms, .8)[..., None] * .97) + wp + wem

# steel stays run to the wall
st = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(st)
for a_, b_ in (((0, 96), (300, 142)), ((0, 300), (168, 300)), ((0, 508), (216, 478)), ((470, 0), (470, 78))):
    dr.line((a_, b_), fill=255, width=5)
st = np.asarray(st, np.float32) / 255 * (1 - gblur(wms, 1))
rgb = rgb * (1 - st[..., None] * .9) + st[..., None] * np.array([.05, .04, .05], np.float32)

# ---- the dark sign, standing in the crowd with its tubes cold
dk = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(dk)
dx0, dy0, dx1, dy1 = 662, 448, 802, 622
dr.rectangle((dx0, dy0, dx1, dy1), outline=255, width=4)
dr.text(((dx0 + dx1) / 2, (dy0 + dy1) / 2), "\u85e5", 255, font=ImageFont.truetype(FJ, 118), anchor="mm")
dk = np.asarray(dk, np.float32) / 255
box = ((xx > dx0) & (xx < dx1) & (yy > dy0) & (yy < dy1)).astype(np.float32)
rgb = rgb * (1 - box[..., None] * .985) + np.array([.018, .016, .02], np.float32) * box[..., None]
rgb = rgb + gblur(dk, .7)[..., None] * np.array([.34, .32, .33], np.float32)

# ---- title sign, vertical, hard against the hero
f_big = font("impact.ttf", 138)
tt = np.zeros((H, W), np.float32)
t_in = np.zeros((H, W), np.float32)
sw2, sh2 = 300, 900
blank = Image.new("L", (sw2, sh2), 0); dr = ImageDraw.Draw(blank)
for i, ch in enumerate("CDK20"):
    dr.text((sw2 / 2, 96 + i * 172), ch, 255, font=f_big, anchor="mm")
tm = np.asarray(blank, np.float32) / 255


def neon_small(t, col, gain):
    return neon(t, col, gain)


o1 = outline(tm, 1.3, .5, .19)
fill = gblur(tm, 1)
em2 = fill[..., None] * np.array([1.0, .16, .10], np.float32) * .72 + neon_small(o1, YEL, .9)
pn = np.array([.05, .012, .02], np.float32) + 0 * em2
br = np.zeros((sh2, sw2), np.float32); br[6:12, 6:-6] = 1; br[-12:-6, 6:-6] = 1; br[6:-6, 6:12] = 1; br[6:-6, -12:-6] = 1
em2 = em2 + neon_small(br, CYN, .85)
fl2 = pn + em2
q2 = [(944, 50), (1262, 92), (1262, 640), (944, 628)]
wt, ins2 = warp(fl2, q2, sw2, sh2)
wte, _ = warp(em2, q2, sw2, sh2)
rgb = rgb * (1 - ins2[..., None]) + wt
rgb = rgb + gblur(wte, 22) * .30 * (1 - ins2[..., None])

# ---- wet street: everything above, smeared down
wy = 628
street = yy > wy
ry = (2 * wy - yy)
rip = (fbm(beta=2.0, seed=31) - .5) * 26
rx = xx + rip * (yy - wy) / 60
refl = sample(rgb, rx, np.clip(ry + rip * .3, 0, H - 1))
refl = gblur(refl, 2.2)
vb = np.zeros_like(refl)
for k in range(1, 7):
    vb += sample(refl, xx, np.clip(yy - k * 6, 0, H - 1))
refl = (refl + vb) / 7
fall = np.clip(1 - (yy - wy) / 150, .18, 1) * .85
rgb = np.where(street[..., None], refl * fall[..., None] + np.array([.01, .01, .016], np.float32), rgb)
rgb = rgb * (1 - np.exp(-((yy - wy) / 3) ** 2) * .85)[..., None]

# ---- rain haze over all, and a lightbox with the label
rgb = rgb + gblur(np.clip(rgb - .5, 0, 3), 30) * .16
rgb = rgb / (1 + .16 * rgb.mean(-1, keepdims=True))
lx0, ly0, lx1, ly1 = 26, 652, 442, 700
lb = ((xx > lx0) & (xx < lx1) & (yy > ly0) & (yy < ly1)).astype(np.float32)
rgb = rgb * (1 - gblur(lb, 2)[..., None]) + np.array([1.0, .96, .84], np.float32) * gblur(lb, .7)[..., None]
rgb = rgb + gblur(lb, 16)[..., None] * np.array([.28, .24, .15], np.float32)
tag = text_mask(LABEL, font("arialbd.ttf", 26), ((lx0 + lx1) / 2, (ly0 + ly1) / 2), "mm")
rgb = over(rgb, (.04, .02, .03), tag)
save(rgb, "g7_hk_neon.png")
