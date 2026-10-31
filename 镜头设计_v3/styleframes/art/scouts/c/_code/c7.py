"""HKBU SCIE1007 coursework science video. Style scout c7: a yellow field, the real protein tearing sideways through a broken HUD, real pLDDT as the signal trace. Method only."""
from common import *

rng = np.random.default_rng(77)
Y, K, C, R = hexrgb("#FCEE0A"), hexrgb("#07070D"), hexrgb("#00F0FF"), hexrgb("#FF003C")
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

Q = warp(load(), zoom=0.86, cx=950, cy=525, rot=0.0, ox=560, oy=372)
n, m, ao, conf = Q["normal"], Q["mask"], Q["ao"], Q["conf"]
hard = gblur((m > 0.5).astype(np.float32), 0.6)
L = np.array([-0.55, 0.62, 0.56], np.float32)
tone = np.clip((n * L).sum(-1) * 0.55 + 0.52, 0, 1) * (0.3 + 0.7 * np.clip(ao * 1.5 - 0.3, 0, 1))
rimv = (n * np.array([0.85, -0.25, 0.2], np.float32)).sum(-1)

rgb = np.ones((H, W, 3), np.float32) * Y
# faint diagonal hazard weave, stops it being a flat colour
weave = ((xx * 0.7 + yy) % 40 < 1.6).astype(np.float32) * 0.06
rgb = comp(rgb, weave, K)


def chamfer(x0, y0, x1, y1, c=26):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


# black chamfered panel behind the right third, the HUD lives here
rgb = comp(rgb, poly_mask(chamfer(842, 78, 1262, 702, 36)), K)
rgb = comp(rgb, poly_mask([(842, 78), (878, 78), (842, 114)]), R)

# protein: scanlined black on yellow, red on black panel, cyan edge, real tail stays red
pitch = 5
scan = ((yy % pitch) / pitch)
ink = (scan < np.clip(1.62 - tone * 1.75, 0.0, 1.0)).astype(np.float32)
ink = gblur(ink, 0.45)
tx = np.ones((H, W, 3), np.float32) * Y
tx = comp(tx, ink, K)
on_panel = gblur(poly_mask(chamfer(842, 78, 1262, 702, 36)), 0.5)
tx2 = np.ones((H, W, 3), np.float32) * K
tx2 = comp(tx2, 1 - ink, R)
tx = comp(tx, on_panel, tx2)
tail = gblur(((conf < 0.7) & (m > 0.5)).astype(np.float32), 0.8)
txt = np.ones((H, W, 3), np.float32) * R
tx = comp(tx, tail, comp(txt, ink, K))
cy = np.clip((rimv - 0.52) * 14, 0, 1)
tx = comp(tx, cy * ((yy % pitch) < 3), C)
rgb = comp(rgb, hard, tx)

# type, heavy condensed and sloped
f = font(F + "bahnschrift.ttf", 300)
f.set_variation_by_name("Bold Condensed")
spr = type_sprite("CDK20", f, pad=4)
sk = 0.20
ttl = spr.transform((int(spr.width + spr.height * sk), spr.height), Image.AFFINE, (1, sk, -spr.height * sk * 0.9, 0, 1, 0), Image.BICUBIC)
ta = np.zeros((H, W), np.float32)
t_arr = np.asarray(ttl, np.float32) / 255
tw, th_ = ttl.size
x0, y0 = 34, 6
ta[y0:y0 + min(th_, H - y0), x0:x0 + min(tw, W - x0)] = t_arr[:min(th_, H - y0), :min(tw, W - x0)]
rgb = comp(rgb, np.roll(ta, 9, 1) * 0.95, C)
rgb = comp(rgb, np.roll(ta, -9, 1) * 0.95, R)
rgb = comp(rgb, ta, K)

# ---- HUD
ca, conf_r, _ = read_pdb()
seq = json.load(open(SEQ, encoding="utf8"))["seq"]
mono = F + "consolab.ttf"
mf = font(mono, 15)
xy, _ = project(ca)
pts = unwarp_pts(Q, xy)

# real pLDDT as a signal trace
X0, X1, Y0, Y1 = 872, 1236, 386, 520
tr = np.zeros((H, W), np.float32)
for i, c_ in enumerate(conf_r):
    x = int(X0 + (X1 - X0) * i / 345)
    h = int((c_ - 0.2) / 0.8 * (Y1 - Y0))
    tr[Y1 - h:Y1, x:x + 1] = 1
col = np.ones((H, W, 3), np.float32) * C
col[Y0:Y1, :] = C
lowx = np.array([1 if c_ < 0.7 else 0 for c_ in conf_r])
for i, l_ in enumerate(lowx):
    if l_:
        x = int(X0 + (X1 - X0) * i / 345)
        col[Y0:Y1, x:x + 2] = R
rgb = comp(rgb, tr, col)
yth = int(Y1 - (0.7 - 0.2) / 0.8 * (Y1 - Y0))
rgb[yth:yth + 1, X0:X1] = Y
d = Image.new("L", (W, H), 0)
ds = ImageDraw.Draw(d)
ds.text((X0, Y0 - 22), "pLDDT / RES 001-346", 255, font=mf)
ds.text((X1 - 34, yth - 18), "0.70", 255, font=font(mono, 13))
rows = [seq[i:i + 34] for i in range(0, 34 * 8, 34)]
for k, row in enumerate(rows):
    ds.text((872, 546 + k * 17), row, 255, font=font(mono, 14))
ds.text((872, 100), "SCAN//Q8IZL9", 255, font=font(mono, 20))
ds.text((872, 128), "LOCK: UNSEEN", 255, font=font(mono, 20))
hudtxt = np.asarray(d, np.float32) / 255
rgb = comp(rgb, hudtxt, Y)

# label tag, on the yellow, chamfered
rgb = comp(rgb, poly_mask(chamfer(34, 646, 438, 692, 14)), K)
rgb = paste_sprite(rgb, type_sprite(LABEL, font(F + "consolab.ttf", 26), pad=2), 236, 668, Y)

# ---- break it. Whole bands of the finished picture slide sideways and split channels.
src = rgb.copy()
out = src.copy()
bands = []
y = 0
while y < H:
    h = int(rng.choice([3, 5, 8, 12, 18, 30, 54]))
    bands.append((y, h))
    y += h
for y, h in bands:
    near = np.exp(-((y - 400) / 170) ** 2)
    if y + h < 215:          # the word keeps only hairline tears
        if h > 8 or rng.random() > 0.6:
            continue
        dx = int(rng.normal(0, 16))
    elif rng.random() > 0.12 + 0.34 * near:
        continue
    else:
        dx = int(rng.normal(0, 95) * (0.3 + near))
    if dx == 0:
        continue
    b = np.roll(src[y:y + h], dx, 1)
    if h <= 30:
        b[..., 0] = np.roll(b[..., 0], 12, 1)
        b[..., 2] = np.roll(b[..., 2], -12, 1)
    # the right third stays closer to readable
    keep = np.clip((xx[y:y + h] - 860) / 20, 0, 1)[..., None] * (1 if rng.random() < 0.72 else 0)
    out[y:y + h] = b * (1 - keep) + src[y:y + h] * keep

# smear: rows of the protein pull out to the left in solid streaks, like a stuck buffer
col_l = np.argmax(hard > 0.5, 1)
for y0_ in range(150, 600, 6):
    if rng.random() > 0.5 or not (hard[y0_] > 0.5).any():
        continue
    x = int(col_l[y0_])
    Ln = int(rng.gamma(1.6, 120))
    x1 = max(0, x - Ln)
    v = K if rng.random() < .7 else (R if rng.random() < .5 else C)
    h = int(rng.choice([2, 4, 6]))
    out[y0_:y0_ + h, x1:x + 8] = v

# blocks knocked out of place
for i in range(26):
    bw, bh = int(rng.choice([24, 40, 64, 96])), int(rng.choice([8, 12, 16, 24]))
    sx, sy = int(rng.integers(120, 760)), int(rng.integers(150, 620))
    dx, dy = int(rng.integers(-180, 180)), int(rng.integers(-40, 40))
    tx_, ty_ = np.clip(sx + dx, 0, 830 - bw), np.clip(sy + dy, 0, H - bh)
    patch = src[sy:sy + bh, sx:sx + bw].copy()
    if i % 3 == 0:
        patch = 1 - patch * np.array([1, 1, 0.2], np.float32)
    out[ty_:ty_ + bh, tx_:tx_ + bw] = patch

# restore the label so the glitch never eats the evidence tag
lm = poly_mask(chamfer(30, 640, 442, 698, 14))
out = comp(out, lm, src)
# channel slip lands on the palette: stray green goes cyan, stray blue goes red
o = np.clip(out, 0, 1)
gr = (o[..., 1] > 0.5) & (o[..., 0] < 0.45) & (o[..., 2] < 0.5)
bl = (o[..., 2] > 0.5) & (o[..., 0] < 0.45) & (o[..., 1] < 0.5)
o[gr] = C
o[bl] = R
finish(o, "c7_cyberpunk_glitch_hud.png")
