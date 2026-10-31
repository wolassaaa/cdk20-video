"""HKBU SCIE1007 coursework science video. Style scout g6: shan shui. The protein stands as one mountain, its real low-confidence tail dissolves into the mist at the foot, one warm figure gives the scale. Brush strokes follow the real surface."""
from glib import *

S = surface()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def silk(seed=1):
    a = fbm(beta=1.0, seed=seed); b = fbm(beta=2.8, seed=seed + 1)
    weave = (np.sin(xx * 1.9) * .5 + np.sin(yy * 2.1) * .5) * .006
    base = np.array([.91, .855, .735], np.float32)[None, None] * (.93 + .1 * b[..., None] + .05 * (a[..., None] - .5))
    return base + weave[..., None]


def peak(R, sc, cx, cy, ink_gain, mist_floor, seed):
    P = smooth_pass(render(R, sc, cx, cy, S=S), 1.0)
    m = P["mask"]; n = P["n"]; z = P["z"] * sc
    # brush direction: across the slope, the way texture strokes follow a rock face
    gx = n[..., 0]; gy = -n[..., 1]
    tx, ty = -gy, gx
    # axe-cut strokes tilt down the slope, stir with noise so they are not mechanical
    ang = .9 * (fbm(beta=3, seed=seed) - .5)
    vx = tx * np.cos(ang) - ty * np.sin(ang); vy = tx * np.sin(ang) + ty * np.cos(ang)
    vy = vy + 1.5   # strokes run down the rock, not round it
    l = np.maximum(np.sqrt(vx * vx + vy * vy), 1e-3); vx, vy = vx / l, vy / l
    st = lic(fbm(beta=.5, seed=seed + 1) ** 2, vx, vy, 16, 1.3)
    st = (st - st.mean()) / st.std()
    dry = np.clip(.5 + st * .55, 0, 1)
    cav = cavity(z, m, (3, 7, 16, 36))
    shade = np.clip(1.15 - (n @ np.array([.55, .55, .63], np.float32)), 0, 1.6)   # light from upper right, ink gathers lower left
    ink = (.18 * shade ** 2.2 + 1.5 * cav ** .9) * (.42 + 1.05 * dry)
    # dark contour with broken brush pressure
    edge = np.clip(1 - n[..., 2] * 2.4, 0, 1) ** 1.6
    press = np.clip(fbm(beta=2.2, seed=seed + 2) * 2.2 - .55, 0, 1)
    ink = (ink + edge * (.25 + .95 * press)) * gblur(m, .9)
    # the foot sinks into a low band of mist above the river. the real low-confidence residues thin out first
    conf = gblur(np.where(m > .5, P["conf"], 1), 7)
    low = np.clip((.74 - conf) / .14, 0, 1)
    n_ = fbm(beta=3, seed=seed + 3) - .5
    mist = np.clip((yy + n_ * 150 - mist_floor) / 92, 0, 1)
    keep = np.clip((1 - mist) * (1 - low * .82), 0, 1)
    return m, np.clip(ink * ink_gain, 0, 1.3) * keep, keep


rgb = silk()
INK = np.array([.055, .062, .075], np.float32)
# far range: the same protein again, pale, standing on the same river
for R, sc, cx, cy, gain, seed, fl in ((rot(0, 110, -8), 6.4, 170, 408, .26, 20, 500), (rot(0, 200, 6), 7.2, 1060, 392, .3, 30, 505)):
    m, ink, keep = peak(R, sc, cx, cy, gain, fl, seed)
    a = gblur(m, 2) * .5 * keep
    rgb = rgb * (1 - a[..., None]) + (rgb * .84 + INK * .16) * a[..., None]
    rgb = rgb * (1 - ink[..., None]) + INK * ink[..., None]

# the mountain
R = rot(0, 0, -90) @ rot(0, 28, 0)
SC = 11.2
cx0, cy0 = 610, 392
m, ink, keep = peak(R, SC, cx0, cy0, 1.0, 520, 2)
P0 = smooth_pass(render(R, SC, cx0, cy0, S=S), 1.0)
lit = np.clip(P0["n"] @ np.array([.5, .62, .6], np.float32), 0, 1)
wash = gblur(m, 1.4) * keep
wash = wash * np.clip((.74 + .34 * fbm(beta=2.4, seed=40)) * (1 - .92 * lit ** 2.2), 0, 1)
rgb = rgb * (1 - wash[..., None]) + INK * wash[..., None]
bleed = gblur(ink, 2.2) * .35 + ink * .85
rgb = rgb * (1 - np.clip(bleed, 0, 1)[..., None]) + INK * np.clip(bleed, 0, 1)[..., None]
# stone green laid thin in the shadow, the way blue-green landscapes carry colour
tint = np.clip(gblur(ink, 8) * 1.1, 0, 1) * wash
rgb = rgb + tint[..., None] * np.array([.0, .05, .05], np.float32)

# near foothills press in from both sides, so the peak has ground to stand on
for R2, sc, cx, cy, seed, fl in ((rot(0, 300, 20), 8.8, 78, 590, 50, 556), (rot(0, 60, -30), 8.0, 900, 628, 55, 566)):
    m2, ink2, keep2 = peak(R2, sc, cx, cy, 1.0, fl, seed)
    P2 = smooth_pass(render(R2, sc, cx, cy, S=S), 1.0)
    lit2 = np.clip(P2["n"] @ np.array([.5, .62, .6], np.float32), 0, 1)
    w2 = gblur(m2, 1.2) * keep2 * np.clip(.92 * (1 - .78 * lit2 ** 2), 0, 1)
    rgb = rgb * (1 - w2[..., None]) + INK * w2[..., None]
    rgb = rgb * (1 - np.clip(ink2, 0, 1)[..., None]) + INK * np.clip(ink2, 0, 1)[..., None]

# trees and moss dots along the ridges: the one cue that turns a mass into a mountain
masks = [m, m2]
rt = np.random.default_rng(21)
tr = Image.new("L", (W * 3, H * 3), 0); dr = ImageDraw.Draw(tr)
for mm in masks:
    up = (mm > .5) & (np.roll(mm, 7, axis=0) < .5) & (yy < 575) & (xx < 1120)
    ys_, xs_ = np.where(up)
    pick = rt.choice(len(ys_), min(len(ys_), 150), replace=False)
    for k in pick:
        x, y = float(xs_[k]), float(ys_[k]) + 4
        h_ = rt.uniform(7, 19) * (.62 + .5 * y / 560)
        lean = rt.uniform(-1.6, 1.6)
        dr.line(((x * 3, y * 3), ((x + lean) * 3, (y - h_) * 3)), fill=255, width=3)
        for j in range(5):
            f_ = rt.uniform(.45, 1.05)
            cxx = x + lean * f_ + rt.uniform(-h_ * .32, h_ * .32); cyy = y - h_ * f_
            rx_ = rt.uniform(1.5, 4.2) * (h_ / 12); ry_ = rx_ * .62
            dr.ellipse(((cxx - rx_) * 3, (cyy - ry_) * 3, (cxx + rx_) * 3, (cyy + ry_) * 3), fill=255)
tr = np.asarray(tr, np.float32).reshape(H, 3, W, 3).mean((1, 3)) / 255
rgb = rgb * (1 - tr[..., None] * .96) + INK * tr[..., None] * .96

# river at the foot: blank silk, a boat, one warm figure with a lamp
foot = 642
rgb = rgb * (1 - .05 * np.exp(-((yy - foot) / 4) ** 2)[..., None])
for yr, x0, x1, a in ((612, 300, 480, .22), (664, 760, 1040, .24), (655, 470, 640, .20), (684, 620, 880, .14)):
    w_ = fbm(beta=2.6, seed=yr) * 2.6
    d = np.exp(-((yy - yr - w_ * 3) / 1.0) ** 2) * np.clip((xx - x0) / 20, 0, 1) * np.clip((x1 - xx) / 20, 0, 1) * a
    rgb = rgb * (1 - d[..., None]) + INK * d[..., None]
bx, by = 586, 640
boat = Image.new("L", (W * 4, H * 4), 0); dr = ImageDraw.Draw(boat)
dr.polygon([(q[0] * 4, q[1] * 4) for q in [(bx - 46, by), (bx + 46, by - 3), (bx + 34, by + 9), (bx - 34, by + 9)]], fill=255)
dr.line([((bx - 40) * 4, (by + 2) * 4), ((bx - 96) * 4, (by + 26) * 4)], fill=255, width=7)
boat = np.asarray(boat, np.float32).reshape(H, 4, W, 4).mean((1, 3)) / 255
rgb = rgb * (1 - boat[..., None] * .92) + INK * boat[..., None] * .92
fig = Image.new("L", (W * 4, H * 4), 0); dr = ImageDraw.Draw(fig)
dr.ellipse(((bx - 9) * 4, (by - 25) * 4, (bx - 1) * 4, (by - 17) * 4), fill=255)
dr.polygon([(q[0] * 4, q[1] * 4) for q in [(bx - 12, by - 1), (bx - 8, by - 17), (bx - 2, by - 17), (bx + 3, by - 1)]], fill=255)
fig = np.asarray(fig, np.float32).reshape(H, 4, W, 4).mean((1, 3)) / 255
rgb = rgb * (1 - fig[..., None]) + np.array([.80, .16, .08], np.float32) * fig[..., None]
glow = gblur(((np.abs(xx - bx - 12) < 3) & (np.abs(yy - by + 16) < 3)).astype(np.float32), 9) * 3
rgb = rgb + glow[..., None] * np.array([.45, .20, .02], np.float32)
dot = ((xx - bx - 12) ** 2 + (yy - by + 16) ** 2 < 8).astype(np.float32)
rgb = over(rgb, (1, .78, .28), gblur(dot, .6))

# title, as a scholar would hang it: down the right, brushed, with a red seal under
f = font("STXINGKA.TTF", 158)
ty = 16
for i, ch in enumerate("CDK20"):
    t = text_mask(ch, f, (1176, ty + i * 118), "mt")
    rough = np.clip(fbm(beta=1.2, seed=60 + i) * 2.6 - .15, 0, 1)
    rgb = rgb * (1 - (t * rough)[..., None]) + INK * .8 * (t * rough)[..., None]

# seal: cinnabar block, label cut out in reverse so it stays small and legible
sx0, sy0, sx1, sy1 = 34, 626, 460, 688
sq = ((xx > sx0) & (xx < sx1) & (yy > sy0) & (yy < sy1)).astype(np.float32)
sq = gblur(sq, .9) * (.88 + .2 * fbm(beta=1.2, seed=70))
cin = np.array([.70, .10, .07], np.float32)
rgb = rgb * (1 - np.clip(sq, 0, 1)[..., None]) + cin * np.clip(sq, 0, 1)[..., None]
tag = text_mask(LABEL, font("georgiab.ttf", 26), ((sx0 + sx1) / 2, (sy0 + sy1) / 2), "mm")
rgb = over(rgb, (.97, .92, .80), tag)
save(rgb, "g6_shanshui.png")
