"""HKBU SCIE1007 coursework science video. Style scout b8: the real CDK20 spread across a wall of mismatched CRT sets. Every set shows a different real data layer, a neon tube traces the outline, each letter of the name has its own set."""
import json

import numpy as np

from common import *

P = load()
Vv = view(P, zoom=1.08, at=(650, 268), src=(950, 545))
y, x = grid()
rng = np.random.default_rng(31)
m = Vv["mask"]
plddt = np.array(json.load(open(PLDDT, encoding="utf8"))["score"], float) / 100
seq = json.load(open(SEQ, encoding="utf8"))["seq"]

lum = np.clip(0.22 + 1.1 * Vv["key"] + 0.9 * Vv["rim"], 0, 1) * (0.42 + 0.58 * Vv["ao"])
nrm = np.clip(Vv["normal"] * 0.62 + 0.5, 0, 1) ** 1.3
dep = 1 - np.clip((Vv["depth"] - 0.22) / 0.34, 0, 1)
cf = Vv["conf"]
heat = ramp(np.clip((cf - 0.3) / 0.68, 0, 1), [(0, "#ff2a00"), (0.5, "#ffd000"), (0.72, "#10f070"), (1, "#0a70ff")])
PHOS = ["#39ff8a", "#ff3a2a", None, None, "#ffa030", "#40a8ff", "#ffffff", "#ff40e0"]


def lay(kind):
    if kind == 2:
        return nrm
    if kind == 3:
        return heat * (0.45 + 0.9 * lum[..., None])
    if kind == 4:
        return (dep ** 1.3)[..., None] * hexc(PHOS[4])
    if kind == 7:
        return (Vv["ao"] ** 1.6)[..., None] * hexc(PHOS[7])
    return lum[..., None] * hexc(PHOS[kind])


def seq_card(sw, sh):
    """Screen off the protein: real sequence text."""
    im = Image.new("L", (max(int(sw), 8), max(int(sh), 8)), 0)
    d = ImageDraw.Draw(im)
    f = font("consolab.ttf", 13)
    s = int(rng.integers(0, 300))
    for r in range(int(sh // 15) + 1):
        d.text((3, 1 + r * 15), seq[s + r * 12:s + r * 12 + int(sw // 7) + 1], 255, font=f)
    return np.asarray(im, np.float32) / 255


def curve_card(sw, sh):
    """Screen off the protein: the real pLDDT curve, residue 1 to 346, as a trace."""
    im = Image.new("L", (max(int(sw), 8), max(int(sh), 8)), 0)
    d = ImageDraw.Draw(im)
    pts = [(i / 345 * sw, sh * 0.92 - plddt[i] * sh * 0.82) for i in range(346)]
    d.line(pts, fill=255, width=2)
    for k in range(1, 4):
        d.line([(0, k * sh / 4), (sw, k * sh / 4)], fill=46)
    return np.asarray(im, np.float32) / 255


def tube(bx0, by0, bx1, by1, paint, frame=None, bez=None, panel=0):
    """One CRT set: cabinet, bulged glass, shadow mask. paint(smpx, smpy, cx, cy, sw, sh) returns screen colour."""
    if bx1 <= 2 or bx0 >= W - 2:
        return
    frame = frame or str(rng.choice(["#2a2420", "#16161a", "#3a3028", "#c8c0ae", "#54483a", "#0e0e10", "#7a6a50"]))
    ax0, ay0, ax1, ay1 = max(bx0, 0), max(by0, 0), min(bx1, W), min(by1, H)
    rgb[ay0:ay1, ax0:ax1] = hexc(frame)
    bez = bez or int(rng.integers(7, 12))
    sx0, sy0, sx1, sy1 = bx0 + bez, by0 + bez, bx1 - bez - panel, by1 - bez
    sw, sh = max(sx1 - sx0, 8), max(sy1 - sy0, 8)
    cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    yy, xx = np.mgrid[ay0:ay1, ax0:ax1].astype(np.float32)
    u, v = (xx - cx) / (sw / 2), (yy - cy) / (sh / 2)
    r2 = u * u + v * v
    bu, bv = u * (1 + 0.06 * r2), v * (1 + 0.06 * r2)
    inside = sstep(1.11, 1.05, (np.abs(bu) ** 5 + np.abs(bv) ** 5) ** 0.2)
    pic = paint(cx + bu * sw / 2, cy + bv * sh / 2, cx, cy, sw, sh)
    scan = 0.7 + 0.3 * np.cos(yy * 2 * np.pi / 3.0)
    tri = np.stack([(xx % 3) == k for k in range(3)], -1).astype(np.float32)
    pic = pic * scan[..., None] * (0.72 + 0.84 * tri) * 1.3
    pic = pic * (1.08 - 0.3 * r2[..., None].clip(0, 1.6))
    pic = pic + blur(pic, 2.4) * 0.45
    glass = hexc("#040505")
    res = glass * (1 - inside[..., None]) + pic * inside[..., None]
    region = rgb[ay0:ay1, ax0:ax1]
    keep = np.maximum(np.abs(u), np.abs(v)) < 1.04
    region[keep] = res[keep]
    if panel:
        for kk in range(3):
            ky, kx = sy0 + 12 + kk * 19, bx1 - bez - panel // 2 - 1
            if 6 <= ky < H - 6 and 6 <= kx < W - 6:
                d2 = np.hypot(np.arange(-5, 6)[None, :], np.arange(-5, 6)[:, None])
                rgb[ky - 5:ky + 6, kx - 5:kx + 6][d2 < 5] = hexc("#b0a890")


def picture(kind):
    """Shared image with each set's own hold and size error."""
    skew = rng.uniform(-9, 9) * (rng.random() < 0.55)
    roll = rng.uniform(-3, 3)
    gz = rng.uniform(0.985, 1.02)
    shift = rng.uniform(-4, 4)
    src = lay(kind)

    def paint(sx, sy, cx, cy, sw, sh):
        px_ = cx + (sx - cx) / gz + skew * (sy - cy) / (sh / 2) + shift
        py_ = cy + (sy - cy) / gz + roll
        pic = sample(src, px_, py_)
        al = sample(m, px_, py_)
        idle = hexc(str(rng.choice(["#061033", "#1c0628", "#04201c", "#260c06", "#08080c"])))
        return idle * (1 - al[..., None]) + pic * al[..., None]

    return paint


def card(kind):
    col = hexc(str(rng.choice(["#39ff8a", "#ffa030", "#40a8ff", "#ff40e0"])))
    fn = seq_card if kind else curve_card

    def paint(sx, sy, cx, cy, sw, sh):
        a = fn(sw, sh)
        return sample(a, sx - cx + sw / 2, sy - cy + sh / 2)[..., None] * col

    return paint


rgb = np.tile(hexc("#060509"), (H, W, 1))

# upper wall, the protein's mosaic
rows = [0, 108, 216, 330, 436, 544]
for r in range(len(rows) - 1):
    cx_ = -int(rng.integers(0, 60))
    while cx_ < W:
        w_ = int(rng.integers(118, 196))
        b0x, b1x = cx_ + 2, cx_ + w_ - 2
        cy_ = (b0x + b1x) / 2, (rows[r] + rows[r + 1]) / 2
        on = sample(m, np.array([cy_[0]], np.float32), np.array([cy_[1]], np.float32))[0] > 0.3
        near = sample(m, np.linspace(b0x + 10, b1x - 10, 5, dtype=np.float32), np.full(5, cy_[1], np.float32)).max() > 0.3
        if on or near:
            p = picture(int(rng.integers(0, 8)))
        else:
            p = card(int(rng.integers(0, 2))) if rng.random() < 0.6 else picture(0)
        tube(b0x, rows[r] + 2, b1x, rows[r + 1] - 2, p, panel=int(rng.integers(0, 2)) * 14)
        cx_ += w_

# neon tube round the real silhouette: smoothed, thick, burned over the wall
hard = (m > 0.5).astype(np.float32)
s = blur(hard, 5)
band = sstep(0.12, 0.05, np.abs(s - 0.5))
pink = hexc("#ff1a8a")
rgb = rgb * (1 - 0.3 * blur(band, 16)[..., None])
rgb = rgb + blur(band, 3)[..., None] * pink * 1.2 + blur(band, 12)[..., None] * pink * 1.0 + blur(band, 34)[..., None] * pink * 0.7
rgb = over(rgb, hexc("#fff0f8"), band)


# last row: every letter has its own set
def glyph(ch):
    im = Image.new("L", (64, 64), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((32, 32), ch, 255, font=font("tahomabd.ttf", 24), anchor="mm")
    a = np.asarray(im, np.float32) / 255
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


LET = list(zip("CDK20", ["#fff6e0", "#39ff8a", "#ffb030", "#ff4a3a", "#50c0ff"]))
rx0, rw = 20, 248
for i, (ch, c) in enumerate(LET):
    g = glyph(ch)
    col = hexc(c)

    def paint(sx, sy, cx, cy, sw, sh, g=g, col=col):
        gh, gw = g.shape
        sc = sh * 0.86 / gh
        gx_ = (sx - cx) / (sc * 0.92) + gw / 2 - 0.5
        gy_ = (sy - cy) / sc + gh / 2 - 0.5
        ok = (gx_ >= -0.5) & (gx_ < gw - 0.5) & (gy_ >= -0.5) & (gy_ < gh - 0.5)
        a = g[np.clip(np.round(gy_).astype(np.int32), 0, gh - 1), np.clip(np.round(gx_).astype(np.int32), 0, gw - 1)] * ok
        return hexc("#04060e") * (1 - a[..., None]) + col * a[..., None] * 1.1

    tube(rx0 + i * rw + 2, 546, rx0 + (i + 1) * rw - 2, 716, paint, frame=["#c8c0ae", "#2a2420", "#7a6a50", "#16161a", "#c8c0ae"][i], bez=12)

lab = text(LABEL, "consolab.ttf", 22, (34, 30), "lm")
plate = sstep(1, 0, np.abs(x - 188) - 172) * sstep(1, 0, np.abs(y - 30) - 20)
rgb = over(rgb, hexc("#040406"), plate)
rgb = over(rgb, hexc("#fffbe8"), lab)
finish(np.clip(rgb, 0, 1), "b8_crt_wall.png")
