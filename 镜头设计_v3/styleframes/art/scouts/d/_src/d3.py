"""HKBU SCIE1007 coursework science video. d3 style test: oil paint method. Stroke based painting with real relief from a height map, the real CDK20 surface as a portrait falling apart where confidence is low."""
from t import *

W, H = 1280, 720
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
Q = view(W, H, zoom=1.44, rot=9, at=(0.715, 0.655), c=(0.5, 0.48))
m = Q["mask"]
mb = m > 0.5
rng = np.random.default_rng(3)

# Target picture: bruised acid complementary light, no greys
key = lit(Q, (-0.66, 0.60, -0.44), 0.05)
cool = lit(Q, (0.80, -0.30, -0.25), 0.0)
ao = np.clip(Q["ao"], 0, 1)
NN = dict(Q)
NN["normal"] = gauss(Q["normal"], 12)
big = lit(NN, (-0.66, 0.60, -0.44), 0.1)
s = np.clip((0.6 * key + 0.5 * big) * (0.30 + 0.70 * ao ** 1.2), 0, 1)
PAL = [(0, "#120a1a"), (0.20, "#120a1a"), (0.21, "#3a1228"), (0.34, "#3a1228"), (0.35, "#8e2418"), (0.47, "#8e2418"), (0.48, "#d9561a"), (0.62, "#d9561a"), (0.63, "#f2a52a"), (0.76, "#f2a52a"), (0.77, "#f7dc86"), (0.90, "#f7dc86"), (0.91, "#fff6dc")]
tone = ramp(s, PAL)
cc = (cool > 0.52) & (s < 0.34)
tone[cc] = hexc("#1f7a8c")
tone[(cool > 0.80) & (s < 0.30)] = hexc("#7fd0c8")
sky = ramp(np.clip((yy / H) * 0.95 + (fbm(H, W, 300, 2, 2) - 0.5) * 0.8 + (xx / W - 0.5) * 0.55, 0, 1),
           [(0, "#0a1020"), (0.40, "#0a1020"), (0.41, "#1c3244"), (0.52, "#1c3244"), (0.53, "#3f5a5c"), (0.60, "#3f5a5c"), (0.61, "#b8641e"), (0.71, "#b8641e"), (0.72, "#eeb63c"), (0.80, "#eeb63c"), (0.81, "#c23a1a"), (1, "#2a0e1e")])
target = np.where(mb[..., None], tone, sky)
tail = np.clip((0.74 - gauss(Q["conf"], 2)) / 0.14, 0, 1) * mb  # real low confidence region
target = target * (1 - 0.7 * tail[..., None]) + ramp(s, [(0, "#2a1a5c"), (0.5, "#6a3aa8"), (1, "#c48ae0")]) * 0.7 * tail[..., None]

# Stroke direction: along the form (perpendicular to the luminance gradient), noise outside the protein
lum = target.mean(2)
blur = gauss(s * mb, 11)
gy, gx = np.gradient(blur)
ang = np.arctan2(gx, -gy)  # along the iso line of the big light shape
wild = fbm(H, W, 150, 3, 9) * 2 * np.pi * 1.6 - 0.4
ang = np.where(mb, ang, 1.15 + (wild - 3) * 0.32)

CAN = hexc("#b89a6a")
paint = np.ones((H, W, 3), np.float32) * CAN
canvas_tex = (np.sin(xx * 1.6) * np.sin(yy * 1.6)) * 0.5
paint *= (1 + 0.05 * canvas_tex[..., None])
hgt = np.zeros((H, W), np.float32)


def brush(L, W_, seed, dk=0.0):
    """Bristle stamp: length L, width W_. Streaks run along x, tips broken."""
    r = np.random.default_rng(seed)
    bris = r.random(W_) ** 1.5
    bris = np.convolve(bris, np.ones(3) / 3, "same")
    x = np.linspace(0, 1, L)[None, :]
    y = np.abs(np.linspace(-1, 1, W_))[:, None]
    tip = np.clip((1 - x) * 8, 0, 1) * np.clip(x * 12, 0, 1)
    edge = np.clip((1 - y) * 3.2, 0, 1)
    dry = np.clip(1.25 - x * 0.9 - r.random((W_, 1)) * 0.5 + bris[:, None] * 0.7, 0, 1)
    h = (0.45 + 0.55 * bris[:, None]) * tip * edge
    a = np.clip(tip * edge * (dry * (2.2 + dk) - 0.4 - dk * (0.35 + 0.9 * x)), 0, 1)
    return a.astype(np.float32), h.astype(np.float32)


def stamp(cx, cy, th, L, Wd, col, wet, seed):
    """Lay one straight bristle stroke by rotated lookup."""
    a0, h0 = BR[(L, Wd, seed % 6)]
    R = int(np.hypot(L, Wd) / 2 + 2)
    x0, y0 = int(cx) - R, int(cy) - R
    x1, y1 = x0 + 2 * R, y0 + 2 * R
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    xs = np.arange(max(x0, 0), min(x1, W))
    ys = np.arange(max(y0, 0), min(y1, H))
    gxx, gyy = np.meshgrid(xs - cx, ys - cy)
    c, s_ = np.cos(th), np.sin(th)
    u = (c * gxx + s_ * gyy + L / 2).astype(int)
    v = (-s_ * gxx + c * gyy + Wd / 2).astype(int)
    ok = (u >= 0) & (v >= 0) & (u < L) & (v < Wd)
    if not ok.any():
        return
    al = np.zeros(u.shape, np.float32)
    he = np.zeros(u.shape, np.float32)
    al[ok] = a0[v[ok], u[ok]]
    he[ok] = h0[v[ok], u[ok]]
    sl = (slice(ys[0], ys[-1] + 1), slice(xs[0], xs[-1] + 1))
    mix = col * (1 - wet) + paint[sl].reshape(-1, 3).mean(0) * wet
    paint[sl] = paint[sl] * (1 - al[..., None]) + mix * al[..., None]
    hgt[sl] = hgt[sl] * (1 - al * 0.8) + he * al * 1.0


LAY = [(240, 84, 520, 0.20, 0.20), (150, 50, 1300, 0.16, 0.10), (84, 26, 3000, 0.12, 0.04), (46, 14, 5200, 0.08, 0.02), (26, 8, 5200, 0.06, 0.0)]
BR = {}
for L, Wd, *_ in LAY:
    for k in range(6):
        BR[(L, Wd, k)] = brush(L, Wd, 100 + L * 7 + k)

for li, (L, Wd, N, jit, wet) in enumerate(LAY):
    smooth = gauss(target, [11, 6, 3, 1.6, 0.8][li])
    # Only paint where the canvas is still wrong: this is what keeps the form while the strokes stay huge
    err = None
    placed = 0
    tries = 0
    while placed < N and tries < N * 14:
        if tries % 400 == 0:
            err = np.abs(paint - smooth).sum(2)
        tries += 1
        x = rng.uniform(-30, W + 30)
        y = rng.uniform(-30, H + 30)
        ix, iy = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
        if li >= 3 and not mb[iy, ix]:
            continue
        if li >= 1 and err[iy, ix] < [0, 0.12, 0.16, 0.20, 0.24][li]:
            continue
        t = tail[iy, ix]
        if li >= 3 and t > 0.4:  # uncertain tail never gets the fine layers
            continue
        th = ang[iy, ix] + rng.normal(0, 0.20)
        col = smooth[iy, ix] * (1 + rng.normal(0, jit * 0.30, 3))
        if li == 1 and rng.random() < 0.03 and mb[iy, ix]:  # a loaded wrong colour now and then, never as confetti
            col = hexc(["#e6352a", "#16a3a0", "#e6352a", "#f2d12c"][rng.integers(4)]) * 0.8 + col * 0.2
        stamp(x, y, th, L, Wd, np.clip(col, 0, 1), wet, placed)
        placed += 1

# Long dragged strokes pulling the real low confidence tail off the form, loaded at the start and running dry
BR[(620, 40, 0)] = brush(620, 40, 901, 3.0)
BR[(460, 64, 0)] = brush(460, 64, 902, 3.0)
tys, txs = np.where(tail > 0.5)
low = tys > 400
tys, txs = tys[low], txs[low]
for i in range(13):
    k = rng.integers(len(tys))
    y0, x0 = tys[k], txs[k]
    L, Wd = ((620, 40), (460, 64))[i % 2]
    th = rng.normal(0.05, 0.05) + np.pi
    cx = x0 + np.cos(th) * L * 0.42
    cy = y0 + np.sin(th) * L * 0.42
    col = paint[max(y0 - 3, 0):y0 + 3, max(x0 - 3, 0):x0 + 3].reshape(-1, 3).mean(0)
    stamp(cx, cy, th, L, Wd, hexc(["#4f2f86", "#8a66b8", "#2c2160", "#5a3a8a"][i % 4]), 0.0, 0)

# Letters painted, not typed: a loaded ivory block with broken edges, then bristle strokes along each glyph
S = text(W, H, "CDK20", font("ariblk.ttf", 158), (24, 2), "lt", track=-1)
Sw = gauss(S, 2)
rough = (Sw + (fbm(H, W, 24, 3, 44) - 0.5) * 0.55) > 0.5
paint = np.where(rough[..., None], hexc("#f1e6ca"), paint)
hgt = np.where(rough, 0.45, hgt)
Sb = gauss(S, 6)
gy2, gx2 = np.gradient(Sb)
ang2 = np.arctan2(gx2, -gy2)
tys, txs = np.where(gauss(S, 3) > 0.8)
BR[(52, 14, 0)] = brush(52, 14, 903)
for i in range(1500):
    k = rng.integers(len(tys))
    y0, x0 = tys[k], txs[k]
    th = ang2[y0, x0] + rng.normal(0, 0.10)
    col = hexc("#f4ead0") * (1 + rng.normal(0, 0.03))
    if rng.random() < 0.05:
        col = hexc("#e8a23c")
    stamp(x0, y0, th, 52, 14, np.clip(col, 0, 1), 0.0, 0)
bare = ramp(fbm(H, W, 16, 3, 77), [(0.3, "#f4e7c6"), (0.7, "#e8d5a8")])

# Relief: the height field lit from the upper left, the only reason this reads as paint
hb = gauss(hgt, 0.75)
hy, hx = np.gradient(hb)
nrm = np.stack([-hx * 3.6, -hy * 3.6, np.ones_like(hx)], -1)
nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
lv = np.array([-0.55, -0.55, 0.63], np.float32)
sh = (nrm * lv).sum(2)
spec = np.clip(sh, 0, 1) ** 22 * 0.20
rgb = paint * (0.62 + 0.62 * sh[..., None]) + spec[..., None]
rgb = np.clip(rgb, 0, 1) ** 0.96
rgb *= (1 + 0.012 * canvas_tex[..., None])

# Label on a torn strip of raw primed canvas stuck at the bottom
strip = (yy > 648 + (xx - 40) * 0.012 + (fbm(H, W, 6, 2, 3) - 0.5) * 7) & (yy < 696 + (fbm(H, W, 6, 2, 5) - 0.5) * 7 + (xx - 40) * 0.012) & (xx > 36 + (fbm(H, W, 6, 2, 6) - 0.5) * 9) & (xx < 462 + (fbm(H, W, 6, 2, 7) - 0.5) * 9)
rgb[strip] = (bare * 1.02)[strip]
rgb = over(rgb, hexc("#1a0f18"), text(W, H, LABEL, font("georgiab.ttf", 25), (56, 673), "lm"))
save(rgb, OUT / "d3_disco_oil.png")
