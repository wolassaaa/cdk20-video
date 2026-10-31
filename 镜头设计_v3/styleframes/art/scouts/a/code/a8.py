"""HKBU SCIE1007 coursework science video. Style scout a8, Dada photo collage: the real CDK20 surface as newspaper halftone, cut into strips and pasted out of register among machine parts, the real 346 letter sequence as newsprint, and ransom-note type. All scraps are made here, nothing is scanned from anywhere."""
import json

from PIL import ImageFilter

from kit import *

SS = 2
CW, CH = W * SS, H * SS
rng = np.random.default_rng(23)
seq = json.load(open(ROOT.parent / "镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/sequence.json", encoding="utf8"))
if isinstance(seq, dict):
    seq = seq.get("sequence", seq.get("seq", ""))
if not isinstance(seq, str):
    seq = "".join(seq)
assert len(seq) == 346, len(seq)

TAN = (216, 198, 160)
CREAM = (232, 220, 192)
RED = (172, 44, 30)
MUST = (208, 160, 50)
TEAL = (58, 108, 112)
PINK = (214, 156, 142)
BLK = (20, 18, 16)


def to_im(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def ht_rgb(g, paper_c=CREAM, ink_c=BLK, cell=6.0, ang=45):
    h, w = g.shape
    c = paper(paper_c, int(rng.integers(0, 999)), mott=0.02, fibre=0.02, h=h, w=w)
    return ink(c, halftone(np.clip(g, 0, 1), cell=cell, ang=ang), ink_c)


def protein(w, h, R, s, cx, cy, gamma=1.0, L=(-0.6, 0.6, 0.5), p=CREAM, inkc=BLK, cell=6.0):
    V = view(R, scale=s, cx=cx, cy=cy, w=w, h=h, ss=0.5, L=L)
    t = np.clip(0.04 + 1.25 * V["key"], 0, 1) * (0.25 + 0.75 * V["ao"])
    g = (1 - t**gamma) * V["mask"]
    return ht_rgb(g, p, inkc, cell), V["mask"]


def news(w, h, size=None, cols=None):
    size = size or int(rng.integers(13, 22))
    fnt = str(rng.choice(["times.ttf", "georgia.ttf", "timesbd.ttf"]))
    im = to_im(paper(TAN if rng.random() < 0.6 else CREAM, int(rng.integers(0, 999)), mott=0.025, fibre=0.03, h=h, w=w))
    d = ImageDraw.Draw(im)
    f = font(fnt, size)
    cols = cols or int(rng.integers(2, 4))
    cw = w // cols
    for c in range(cols):
        y = 4
        o = int(rng.integers(0, 346))
        while y < h:
            n = max(6, int((cw - 12) / (size * 0.56)))
            line = "".join(seq[(o + i) % 346] for i in range(n))
            o += n
            d.text((c * cw + 5, y), line, font=f, fill=(30, 26, 22))
            y += int(size * 1.22)
        if c:
            d.line([(c * cw, 0), (c * cw, h)], fill=(30, 26, 22), width=1)
    return np.asarray(im, np.float32) / 255


def gear(w, h, teeth=14, p=TAN, ic=BLK):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    R_ = min(w, h) * 0.46
    r = np.hypot(x - cx, y - cy)
    th = np.arctan2(y - cy, x - cx)
    prof = R_ * (0.84 + 0.16 * smooth(np.cos(th * teeth), -0.15, 0.15))
    m = (r < prof).astype(np.float32)
    bore = r < R_ * 0.20
    web = (r < R_ * 0.68) & (r > R_ * 0.36)
    tone = 0.25 + 0.45 * (0.5 + 0.5 * np.cos(th - 0.8))
    tone = tone + 0.5 * web * smooth(np.cos(th * 5), 0.2, 0.3)
    c = paper(p, int(rng.integers(0, 999)), h=h, w=w)
    c = ink(c, halftone(np.clip(tone, 0, 1) * m, cell=5.0, ang=30) * (~bore), ic)
    return c, np.clip(fft_blur(m, 0.6), 0, 1)


def eye(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
    lid = 0.86 * (1 - np.abs(u) ** 2.0)
    open_ = (np.abs(v) < lid) & (np.abs(u) < 0.98)
    r = np.hypot(u * w, v * h) / h
    th = np.arctan2(v * h, u * w)
    iris = r < 0.46
    pupil = r < 0.20
    streak = 0.46 + 0.28 * np.sin(th * 34 + 3 * np.sin(th * 7))
    g = np.where(iris, streak * (0.55 + 0.9 * r), 0.10 + 0.32 * np.abs(u) ** 2 + 0.14 * np.abs(v))
    g = np.where(pupil, 1.0, g)
    hi = np.hypot(u * w / h + 0.16, v + 0.20) < 0.09
    g = np.where(hi, 0, g)
    skin = 0.34 + 0.34 * np.clip(np.abs(v) - lid, 0, 1)
    fold = np.abs(v + lid * 1.28 + 0.06) < 0.024
    g = np.where(open_, g, skin)
    g = np.where(np.abs(np.abs(v) - lid) < 0.05, 0.96, g)
    g = np.where(fold & ~open_, 0.9, g)
    return ht_rgb(fft_blur(g.astype(np.float32), 0.8), PINK, BLK, cell=4.6, ang=45)


def flat(w, h, c, stripes=False):
    a = paper(c, int(rng.integers(0, 999)), mott=0.03, fibre=0.03, h=h, w=w)
    if stripes:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        a = ink(a, ((x + y) % 26 < 11).astype(np.float32) * 0.92, BLK)
    return a


def key_img(w, h):
    L_ = Layer(w=w, h=h, ss=2)
    cy = h / 2
    L_.ell(6, cy - 62, 130, cy + 62)
    L_.ell(44, cy - 26, 92, cy + 26, 0)
    L_.rect(120, cy - 12, w - 8, cy + 12)
    L_.rect(w - 58, cy + 12, w - 8, cy + 48)
    L_.rect(w - 100, cy + 12, w - 78, cy + 36)
    a = L_.a()
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = 0.78 + 0.20 * np.sin((x + y * 2) / 16)
    c = paper(CREAM, 77, h=h, w=w)
    c = ink(c, halftone(t, cell=4.4) * a, BLK)
    return c, a


canvas = Image.fromarray((paper(TAN, 2, mott=0.03, fibre=0.03, h=CH, w=CW) * 255).astype(np.uint8)).convert("RGB")


def jag(pts, amt=2.5):
    return [(x + rng.normal(0, amt), y + rng.normal(0, amt)) for x, y in pts]


def paste(rgb, cx, cy, deg=0.0, m=None, poly=None, rim=4, shadow=0.42):
    """Glue one scrap: cut along poly (or its own mask), leave a paper rim, rotate, drop a small shadow."""
    h, w = rgb.shape[:2]
    im = to_im(rgb).convert("RGBA")
    if poly is None and m is None:
        poly = jag([(0, 0), (w, 0), (w, h), (0, h)], 3.0)
        poly = [(float(np.clip(x, 2, w - 2)), float(np.clip(y, 2, h - 2))) for x, y in poly]
    if poly is not None:
        a = Image.new("L", (w, h), 0)
        ImageDraw.Draw(a).polygon(poly, fill=255)
    else:
        a = to_im(m)
    if rim:
        a2 = a.filter(ImageFilter.MaxFilter(rim * 2 + 1))
        base = Image.new("RGBA", (w, h), (240, 234, 216, 255))
        base.putalpha(a2)
        im.putalpha(a)
        base.alpha_composite(im)
        im = base
    else:
        im.putalpha(a)
    im = im.rotate(deg, Image.BICUBIC, expand=True)
    x0, y0 = int(cx - im.width / 2), int(cy - im.height / 2)
    if shadow:
        sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(3.0))
        dark = Image.new("RGB", im.size, (10, 8, 6))
        sh = sh.point(lambda v: int(v * shadow))
        canvas.paste(dark, (x0 + 4, y0 + 5), sh)
    canvas.paste(im.convert("RGB"), (x0, y0), im.getchannel("A"))


def rd(a, b):
    return float(rng.uniform(a, b))


Rb = base_view()
# ---- under-layer: dense newsprint, colour paper, little protein crops ----
for i in range(96):
    w, h = int(rd(150, 520)), int(rd(110, 400))
    k = rng.random()
    if k < 0.46:
        s = news(w, h)
    elif k < 0.68:
        s, _ = protein(w, h, rot(rd(-80, 80), rd(-170, 170), rd(0, 90)) @ Rb, rd(7, 26), w * rd(0.3, 0.7), h * rd(0.3, 0.7), gamma=0.8, cell=float(rng.choice([4.4, 5.6, 7.0])), p=TAN if rng.random() < 0.5 else CREAM)
    else:
        c = [RED, MUST, TEAL, PINK, CREAM, BLK][int(rng.integers(0, 6))]
        s = flat(w, h, c, stripes=rng.random() < 0.3)
    paste(s, rd(0, CW), rd(0, CH), rd(-34, 34), rim=int(rng.choice([0, 3])))

# ---- machine parts ----
for cx, cy, sz, t, deg in [(1980, 1190, 620, 16, 12), (2420, 240, 500, 12, 0), (300, 330, 360, 11, 0), (1290, 1220, 300, 9, 0)]:
    c, m = gear(sz, sz, t, p=CREAM if t % 2 else TAN)
    paste(c, cx, cy, deg, m=m, rim=3)

# ---- the main figure: protein cut into strips, glued out of register ----
fw, fh = 1560, 1560
PR = rot(0, -24, 12) @ Rb
fig, fm = protein(fw, fh, PR, 25.5, fw / 2, fh / 2, gamma=0.72, L=(-0.72, 0.5, 0.48), cell=8.0)
edges = [0, 400, 640, 930, 1160, fh]
shifts = [(1464, 660, -1.5), (1610, 650, 3.5), (1380, 650, -4), (1530, 668, 2.5), (1440, 650, -2.5)]
for (y0, y1), (cx, cy, deg) in zip(zip(edges[:-1], edges[1:]), shifts):
    band_m = np.zeros((fh, fw), np.float32)
    band_m[y0:y1] = 1
    bm = np.clip(fm * band_m, 0, 1)
    paste(fig, cx, cy, deg, m=bm, rim=6, shadow=0.55)

# the eye sits in the lump where a face would have one, a plain key is shoved at the side
paste(eye(640, 340), 1560, 650, 7, poly=jag([(14, 40), (620, 12), (632, 300), (40, 334), (6, 180)], 4), rim=5, shadow=0.5)
k, km = key_img(620, 190)
paste(k, 690, 690, -14, m=km, rim=7, shadow=0.6)

# ---- ransom type, every letter from a different paper ----
letters = [
    ("C", "impact.ttf", 330, BLK, MUST, 250, 318, 196, 1050, -7),
    ("D", "timesbd.ttf", 360, (238, 230, 210), BLK, 270, 340, 470, 1120, 5),
    ("K", "georgiab.ttf", 310, RED, CREAM, 262, 330, 742, 1060, -4),
    ("2", "ariblk.ttf", 310, BLK, PINK, 262, 330, 1014, 1136, 6),
    ("0", "courbd.ttf", 400, (240, 232, 214), RED, 262, 330, 1274, 1056, -8),
]
for ch, fnt, fs, fg, bg, w, h, cx, cy, deg in letters:
    im = to_im(paper(bg, int(rng.integers(0, 999)), mott=0.02, fibre=0.03, h=h, w=w))
    d = ImageDraw.Draw(im)
    f = font(fnt, fs)
    bb = d.textbbox((0, 0), ch, font=f)
    d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), ch, font=f, fill=fg)
    paste(np.asarray(im, np.float32) / 255, cx, cy, deg, rim=4, shadow=0.55)

# ---- label typed on a clean slip, the only tidy thing in the picture ----
w, h = 800, 84
im = to_im(paper((244, 238, 222), 9, mott=0.01, fibre=0.012, h=h, w=w))
ImageDraw.Draw(im).text((22, 18), "AlphaFold DB v6 · predicted", font=font("consolab.ttf", 50), fill=(14, 12, 10))
paste(np.asarray(im, np.float32) / 255, 2060, 1320, 1.8, rim=0, shadow=0.55)

rgb = np.asarray(canvas.resize((W, H), Image.LANCZOS), np.float32) / 255
rgb = np.clip(rgb * (0.985 + 0.015 * noise(s=40, seed=4)[..., None]), 0, 1)
save(rgb, "a8_dada_collage.png")
