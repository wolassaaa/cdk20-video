"""HKBU SCIE1007 coursework science video. Style scout g10: Chinese shadow theatre. The protein is cut from one sheet of dyed hide and hung on rods. The real low-confidence tail is a separate limb on a pivot, because it is the part the model is least sure of. Holes are punched where real residues sit."""
from glib import *

S = surface()
A = atoms()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
c = S["center"]
R = rot(-90, 0, -32)
SC = 11.8
cx, cy = 640, 322
P = smooth_pass(render(R, SC, cx, cy, S=S), 1.4)
m = (gblur(P["mask"], 2.6) > .5).astype(np.float32)   # a knife outline, a little simplified
tail_ = gblur(((P["conf"] < .7) & (P["mask"] > .5)).astype(np.float32), 6) > .42
tail = tail_.astype(np.float32) * m
body = m * (1 - tail)

# the screen: paper lit from behind by one warm lamp, hottest a little left of centre
d = np.sqrt(((xx - 520) / 900) ** 2 + ((yy - 420) / 620) ** 2)
lamp = np.clip(1.12 - d ** 1.7, 0, 1.2)
SC_HOT = np.array([1.0, .78, .40], np.float32); SC_MID = np.array([.86, .32, .07], np.float32); SC_LOW = np.array([.16, .025, .012], np.float32)
t = lamp[..., None]
screen = SC_LOW * (1 - t) ** 2 + SC_MID * 2 * t * (1 - t) + SC_HOT * t ** 2
paper = fbm(beta=1.1, seed=2)
fib = lic(fbm(beta=.5, seed=3), np.ones((H, W), np.float32) * .9, np.ones((H, W), np.float32) * .3, 9, 1.6)
screen = screen * (.93 + .12 * paper[..., None]) * (1 + .06 * (fib[..., None] - .5))

# the fretwork: a fine punch on every real heavy atom, a ring cut on every real alpha carbon. The lace is the structure itself
Vall = (A["xyz"] - c) @ R.T
xa = cx + Vall[:, 0] * SC; ya = cy - Vall[:, 1] * SC
front = Vall[:, 2] > np.percentile(Vall[:, 2], 30)
holes = Image.new("L", (W * 3, H * 3), 0); dr = ImageDraw.Draw(holes)
for x, y, e in zip(xa[front], ya[front], A["el"][front]):
    r = 2.0 if e == "C" else 2.9
    dr.ellipse(((x - r) * 3, (y - r) * 3, (x + r) * 3, (y + r) * 3), fill=255)
ca = A["xyz"][A["name"] == "CA"] - c
V = ca @ R.T
pts = np.stack([cx + V[:, 0] * SC, cy - V[:, 1] * SC], -1)
for p in pts[V[:, 2] > np.percentile(V[:, 2], 22)]:
    dr.ellipse(((p[0] - 7.5) * 3, (p[1] - 7.5) * 3, (p[0] + 7.5) * 3, (p[1] + 7.5) * 3), outline=255, width=5)
holes = np.asarray(holes, np.float32).reshape(H, 3, W, 3).mean((1, 3)) / 255
er = (gblur(m, 6) > .93)
er = er & (gblur(tail, 3) < .3) | (er & (gblur(tail, 6) > .9))


def iso(f, level, width):
    gy, gx = np.gradient(f)
    g = np.sqrt(gx ** 2 + gy ** 2) + 1e-4
    return np.exp(-(((f - level) / (g * width)) ** 2))


zs = gblur(P["z"] * P["mask"], 3.0)
slits = np.zeros((H, W), np.float32); inks = np.zeros((H, W), np.float32)
for i, lv in enumerate(np.arange(P["zmin"] + 6, P["zmax"], 2.6)):
    if i % 2:
        slits = np.maximum(slits, iso(zs, lv, 1.7))
    else:
        inks = np.maximum(inks, iso(zs, lv, 1.5))
slitbreak = np.clip(fbm(beta=2.6, seed=8) * 3 - .9, 0, 1)   # slits break into crescents, the sheet must hold
cut = np.clip(holes + (slits > .5) * slitbreak, 0, 1) * er.astype(np.float32)
cut = cut * (1 - np.clip(inks * 1.5, 0, 1))

# hide: translucent, dye sits unevenly, the lamp shows through it
DY_RED = np.array([.72, .17, .06], np.float32)
DY_GRN = np.array([.16, .40, .17], np.float32)
hide_tex = .52 + .62 * fbm(beta=1.9, seed=5) ** 1.3
grain = lic(fbm(beta=.6, seed=9), np.ones((H, W), np.float32) * .2, np.ones((H, W), np.float32) * .9, 10, 1.4)
dye = (body[..., None] * DY_RED + tail[..., None] * DY_GRN) * hide_tex[..., None] * (.82 + .38 * grain[..., None])
puppet = screen * dye * 1.55
ink = np.clip(gblur(m, 1.1), 0, 1) * (1 - (gblur(m, 3.2) > .84).astype(np.float32))
ink = np.clip(ink + np.clip(inks * 1.2, 0, 1) * er, 0, 1)
tseam = np.clip(gblur(tail, 1.8) - tail, 0, 1) * 3 * m

# compose: hide sits against the paper so edge is crisp; a soft second shadow where it leans off the screen
off = sample(gblur(m, 7), xx - 13, yy - 11)
rgb = screen * (1 - .55 * off[..., None] * (1 - m[..., None]))
alpha = m * (1 - cut)
alpha = gblur(alpha, .55)
rgb = rgb * (1 - alpha[..., None]) + puppet * alpha[..., None]
inkm = np.clip(ink + tseam, 0, 1) * alpha
rgb = rgb * (1 - inkm[..., None] * .95) + np.array([.03, .012, .01], np.float32) * inkm[..., None] * .95

# rods: bamboo, held from below the frame, soft because they stand off the screen
rods = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(rods)
tailpts = np.stack([xx[tail_], yy[tail_]], -1)
tc = tailpts.mean(0)
piv = (int(tc[0] * .55 + 640 * .45), int(tc[1] * .55 + 322 * .45))
for a_, b_, w_ in (((520, 196), (432, 760), 5), ((760, 330), (832, 760), 5), ((int(tc[0]), int(tc[1])), (1080, 760), 5)):
    dr.line((a_, b_), fill=255, width=w_)
rods = gblur(np.asarray(rods, np.float32) / 255, 1.8)
rgb = rgb * (1 - rods[..., None] * .86)

# pivot rivets
for p_ in ((520, 196), (760, 330), (int(tc[0]), int(tc[1]))):
    q = ((xx - p_[0]) ** 2 + (yy - p_[1]) ** 2)
    rv = np.clip(1 - np.abs(np.sqrt(q) - 8) / 2.6, 0, 1)
    rgb = rgb * (1 - rv[..., None]) + np.array([.02, .01, .01], np.float32) * rv[..., None]

# title: cut from the same hide with the same pierced dots, standing on the stage rail
f = font("impact.ttf", 150)
tm = text_mask("CDK20", f, (40, 702), "ls", spacing=4)
tmH = (tm > .5).astype(np.float32)
dots = ((np.sin(xx * .34) * np.sin(yy * .34)) > .62).astype(np.float32) * (gblur(tmH, 3.2) > .9)
ta = gblur(tmH * (1 - dots), .55)
rgb = rgb * (1 - ta[..., None]) + np.array([.022, .010, .008], np.float32) * ta[..., None]

# stage rail: a band of shadow, the label pasted on a paper slip like a playbill
rail = np.clip((yy - 712) / 3, 0, 1)
rgb = rgb * (1 - rail[..., None] * .9)
lx0, ly0, lx1, ly1 = 852, 658, 1256, 704
lb = ((xx > lx0) & (xx < lx1) & (yy > ly0) & (yy < ly1)).astype(np.float32)
lb = gblur(lb, .7)
rgb = rgb * (1 - lb[..., None]) + np.array([.96, .84, .58], np.float32) * lb[..., None]
tg = text_mask(LABEL, font("georgiab.ttf", 25), ((lx0 + lx1) / 2, (ly0 + ly1) / 2), "mm")
rgb = over(rgb, (.14, .03, .01), tg)
save(rgb, "g10_shadow_puppet.png")
