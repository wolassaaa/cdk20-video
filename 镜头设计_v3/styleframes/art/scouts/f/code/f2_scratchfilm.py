"""HKBU SCIE1007 coursework science video. Style scout f2: scratched film stock. A macro of the real CDK20 surface optically printed too hard, then attacked by hand on the emulsion.
The title is scratched with a needle, three passes, because a hand can never repeat itself. All damage is fixed to the image; in motion it must hold still or crawl slowly, never flicker per frame."""
from fx import *

rng = np.random.default_rng(7)
P = load_view("hero")
key, rim, ao, mask, nrm, conf = P["key"], P["rim"], P["ao"], P["mask"], P["normal"], P["conf"]
ss = 0.84
sz = (int(key.shape[1] * ss), int(key.shape[0] * ss))


def rs(a):
    return np.asarray(Image.fromarray(a).resize(sz, Image.BILINEAR))


key, rim, ao, mask = rs(key), rs(rim), rs(ao), rs(mask)
nx, ny = rs(nrm[..., 0]), rs(nrm[..., 1])
ch, cw = key.shape
x_off, y_off = (cw - W) // 2, (ch - H) // 2
crop = lambda a: a[y_off:y_off + H, x_off:x_off + W]
key, rim, ao, mask, nx, ny = map(crop, (key, rim, ao, mask, nx, ny))

# print it too hard: bleach bypass curve, cold silver over crushed black
L = 0.9 * key ** 1.25 * ao + 0.6 * rim ** 2 * ao + 0.14 * ao ** 2
L = np.clip(L * mask, 0, 1)
L = smooth(0.03, 0.82, L)
# double exposure: the same plate printed again, sliding and larger, as a dirty ghost
yy, xx = np.mgrid[:H, :W].astype(np.float32)
gh = sample(L, (xx - 640) * 0.86 + 640 + 38, (yy - 360) * 0.86 + 360 - 14)
Lf = np.maximum(L, gh * 0.42)

# emulsion rot: large stains eaten out of the image
st = noise((H, W), 2.7, 2)
st2 = noise((H, W), 2.2, 9)
burn = smooth(0.76, 0.95, st) * smooth(0.25, 0.8, st2)
Lf = Lf * (1 - 0.9 * burn)
Lf = Lf + smooth(0.93, 0.99, st) * 0.3  # burnt-through patches go clear
grain_static = noise_raw((H, W), 0.6, 5) * 0.022
Lf = Lf + grain_static * (0.4 + Lf)

# needle hatching: scratches that follow the form across the bright planes
SS = 2
hatch = Image.new("L", (W * SS, H * SS), 0)
dh = ImageDraw.Draw(hatch)
prob = np.clip(gauss(L, 1.0), 0, 1) ** 2.0 + 0.004
prob = prob / prob.sum()
idx = rng.choice(H * W, 3200, p=prob.ravel())
ys, xs = np.unravel_index(idx, (H, W))
gy, gx = np.gradient(gauss(L, 2.2))
for x0, y0 in zip(xs.tolist(), ys.tolist()):
    x, y = float(x0), float(y0)
    n = int(rng.integers(8, 30))
    pts = [(x * SS, y * SS)]
    for _ in range(n):
        i, j = int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))
        tx, ty = -gy[i, j], gx[i, j]  # along the iso-tone line, so the strokes wrap round each lobe
        l = np.hypot(tx, ty) + 1e-4
        x += tx / l * 2.2 + rng.normal(0, 0.28)
        y += ty / l * 2.2 + rng.normal(0, 0.28)
        pts.append((x * SS, y * SS))
    v = int(rng.uniform(40, 190))
    dh.line(pts, fill=v, width=1)
hatch = np.asarray(hatch.resize((W, H), Image.LANCZOS), np.float32) / 255

# frame-length scratches: the print dragged through a dirty gate
drag = np.zeros((H, W), np.float32)
dd = Image.new("L", (W * SS, H * SS), 0)
dg = ImageDraw.Draw(dd)
for i in range(46):
    x = rng.uniform(0, W)
    wob = rng.uniform(0.3, 6)
    y0 = rng.uniform(-100, 400)
    y1 = y0 + rng.uniform(160, 900)
    pts = [((x + wob * np.sin(t * 0.012 + i) + 0.002 * (t - y0) * rng.normal(0, 3)) * SS, t * SS) for t in np.arange(y0, y1, 12)]
    dg.line(pts, fill=int(rng.uniform(40, 255)), width=int(rng.integers(1, 3)))
drag = np.asarray(dd.resize((W, H), Image.LANCZOS), np.float32) / 255
# dust and hairs
dust = Image.new("L", (W * SS, H * SS), 0)
dd2 = ImageDraw.Draw(dust)
for i in range(260):
    x, y = rng.uniform(0, W * SS), rng.uniform(0, H * SS)
    r = rng.uniform(0.6, 3.2)
    dd2.ellipse([x - r, y - r, x + r, y + r], fill=255)
for i in range(14):
    x, y = rng.uniform(0, W * SS), rng.uniform(0, H * SS)
    a = rng.uniform(0, 6.28)
    pts = []
    for t in range(40):
        pts.append((x, y))
        a += rng.normal(0, 0.2)
        x += np.cos(a) * 4
        y += np.sin(a) * 4
    dd2.line(pts, fill=255, width=2)
dust = np.asarray(dust.resize((W, H), Image.LANCZOS), np.float32) / 255

# title: scratched with a needle. Each letter is cut several times, never in the same place twice
tt = Image.new("L", (W * 3, H * 3), 0)
dt = ImageDraw.Draw(tt)
LX, LY, LH, LW = 92, 196, 296, 172
x = LX
for n, ch in enumerate("CDK20"):
    for stroke in STROKES[ch]:
        arr = np.array(stroke, np.float32)
        # resample each stroke
        seg = np.hypot(*(arr[1:] - arr[:-1]).T)
        t = np.r_[0, np.cumsum(seg)]
        ts = np.linspace(0, t[-1], max(24, int(t[-1] * 60)))
        q = np.stack([np.interp(ts, t, arr[:, 0]), np.interp(ts, t, arr[:, 1])], -1)
        for rep in range(9):
            jx = rng.normal(0, 0.016)
            jy = rng.normal(0, 0.012)
            wob = np.cumsum(rng.normal(0, 0.0032, q.shape), 0)
            wob -= wob.mean(0)
            over = rng.uniform(-0.04, 0.09)  # strokes overshoot their ends
            r = q + wob + [jx, jy]
            r = r + (r - r.mean(0)) * over
            a = rng.uniform(0, 0.05)
            b = 1 - rng.uniform(0, 0.05)
            r = r[int(len(r) * a): max(int(len(r) * b), int(len(r) * a) + 3)]
            pts = [((x + px * LW + (py - 0.5) * 22) * 3, (LY + py * LH) * 3) for px, py in r]
            dt.line(pts, fill=int(rng.uniform(150, 255)), width=int(rng.choice([2, 3, 3, 4, 6, 9])), joint="curve")
    x += LW * ADV[ch] + 50
title = np.asarray(tt.resize((W, H), Image.LANCZOS), np.float32) / 255
# scratched emulsion lifts off in flakes along the strokes
flake = gauss(title, 2.2) * smooth(0.4, 0.7, noise((H, W), 0.8, 3))
title = np.clip(title + 0.5 * flake, 0, 1)

# plate gets pushed down behind the title so the scratches stay white
under = gauss(title, 16)
Lf = Lf * (1 - np.clip(under * 2.0, 0, 0.72))

out = Lf + hatch * (0.5 + 0.5 * mask) * 0.95
out = np.maximum(out, drag * 0.55)
out = np.maximum(out, dust * 0.9)
out = out * (1 - dust * 0)

# hair-thin black scratches: on the print, not the negative
blk = Image.new("L", (W * SS, H * SS), 0)
db = ImageDraw.Draw(blk)
for i in range(30):
    x = rng.uniform(0, W * SS)
    db.line([(x, 0), (x + rng.normal(0, 30), H * SS)], fill=int(rng.uniform(60, 220)), width=1)
blk = np.asarray(blk.resize((W, H), Image.LANCZOS), np.float32) / 255
out = out * (1 - blk * 0.8)

# stock: cold grey in the highlights, sick yellow-brown in the mids, ink black
cols = np.stack([rgb(c) for c in ("#050403", "#2A2010", "#8C8058", "#D8D8C4", "#F4F6EE")])
stops = np.array([0, 0.18, 0.5, 0.82, 1.0], np.float32)
t = np.clip(out, 0, 1)
img = np.stack([np.interp(t.ravel(), stops, cols[:, i]).reshape(t.shape) for i in range(3)], -1).astype(np.float32)
# one wound of red, on the emulsion that lifted first, a fixed stain
stain = smooth(0.86, 0.97, noise((H, W), 3.0, 27))
img = img * (1 - 0.86 * stain[..., None] * (1 - rgb("#C81E12")))

# title sits on top as pure scratched-through clear
img = mix(img, rgb("#FBFBF0"), title)
# ragged gate: uneven black frame edge, hand-filed
edge = noise_raw((H, W), 2.0, 44)
tp = smooth(16 + edge * 10, 4 + edge * 10, yy) + smooth(H - 16 + edge * 9, H - 4 + edge * 9, yy)
lf = smooth(26 + edge * 12, 10 + edge * 12, xx) + smooth(W - 26 + edge * 12, W - 10 + edge * 12, xx)
frame = np.clip(tp + lf, 0, 1)
img = img * (1 - frame)[..., None]

# label: typewriter, printed twice and a little out of register
lab = font("consolab.ttf", 24)
lm = text_mask(LABEL, lab, (66, 672), 0.6)
lm2 = text_mask(LABEL, lab, (68, 670), 0.6)
back = gauss(lm, 7) * 7
img = img * (1 - np.clip(back, 0, 1) * 0.86)[..., None]
img = mix(img, rgb("#BDBBA8"), lm2 * 0.45)
img = mix(img, rgb("#FAF8EA"), lm)
save(img, OUT / "f2_scratchfilm.png")
print("ok")
