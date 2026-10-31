"""HKBU SCIE1007 coursework science video. Hands direction, numpy kit: an ash plain with real relief, pressed prints, carved and gold-filled type, evidence tags.
The world is neutral grey and black. The only warm colours are skin and the gold hands leave behind. Everything is 1920 x 1080 and static, no per-frame grain."""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
HERE = ROOT / "styleframes/art/hands"
STILL = HERE / "stills"
RAW = HERE / "code/_raw"
sys.path.insert(0, str(ROOT / "styleframes/art/_shared"))
W, H = 1920, 1080
FX = str(ROOT / "styleframes/S1/v2/_code/s110/fonts") + "/"
SERIF, SERIFI, BLACK, MONO, SANS = FX + "InstrumentSerif-Regular.ttf", FX + "InstrumentSerif-Italic.ttf", FX + "ArchivoBlack-Regular.ttf", FX + "MartianMono.ttf", FX + "InterTight.ttf"
GOLD, GOLD_D, GOLD_L = np.array([0.93, 0.66, 0.20], np.float32), np.array([0.46, 0.27, 0.05], np.float32), np.array([1.0, 0.86, 0.50], np.float32)
SKIN = [np.array(c, np.float32) for c in ((0.85, 0.58, 0.44), (0.76, 0.48, 0.33), (0.64, 0.38, 0.25), (0.52, 0.29, 0.18), (0.90, 0.67, 0.53), (0.40, 0.22, 0.14))]
LX, LY = -0.72, -0.69   # sun, image space: from the upper left, as in bl_kit.SUN


def font(p, s):
    return ImageFont.truetype(p, s)


def gblur(a, s):
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gblur(a[..., i], s) for i in range(a.shape[2])], -1)
    h, w = a.shape
    pad = int(s * 3) + 1
    b = np.pad(a, pad, mode="edge")
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    r = np.fft.irfft2(np.fft.rfft2(b) * g, s=b.shape)
    return r[pad:pad + h, pad:pad + w].astype(np.float32)


def vnoise(w, h, cell, seed=0, oct=4, gain=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, c = 1.0, 0.0, float(cell)
    for _ in range(oct):
        gw, gh = max(2, int(w / c) + 3), max(2, int(h / c) + 3)
        g = rng.random((gh, gw), dtype=np.float32)
        a = np.asarray(Image.fromarray(g).resize((int(gw * c), int(gh * c)), Image.BICUBIC))[:h, :w]
        out += amp * a
        tot += amp
        amp *= gain
        c = max(1.0, c / 2)
    return out / tot


def comp(rgb, a, col):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def press(mask, depth=1.0, soft=2.0):
    """Relief of something pressed into ash: a soft-walled dent with a low lip pushed up around it."""
    return -gblur(mask, soft) * depth + gblur(mask, soft * 5) * depth * 0.30


def ash(relief=None, tone=0.62, seed=3, light=1.0):
    """Top-down ash. Neutral grey by construction. relief is added to the height, so every dent gets real light and shadow."""
    h = vnoise(W, H, 520, seed, 3, 0.45) * 3.0 + vnoise(W, H, 34, seed + 1, 3, 0.5) * 0.16 + vnoise(W, H, 5, seed + 2, 2, 0.6) * 0.075
    if relief is not None:
        h = h + relief
    gy, gx = np.gradient(h)
    sl = gx * LX + gy * LY
    v = tone * (1 + np.clip(sl * 13 * light, -0.95, 1.2))
    v = np.clip(v, 0, 1.3)
    rng = np.random.default_rng(seed + 7)
    fine = rng.random((H, W), dtype=np.float32)
    fine = gblur(fine, 0.55)
    fine = (fine - fine.mean()) / fine.std()
    v = v * (1 + fine * 0.075)
    v = v * (0.90 + 0.20 * vnoise(W, H, 260, seed + 3, 3))
    return np.stack([v, v, v * 1.012], -1).astype(np.float32), h


def vignette(rgb, k=0.42):
    xx, yy = np.meshgrid(np.linspace(-1, 1, W, dtype=np.float32), np.linspace(-1, 1, H, dtype=np.float32))
    return rgb * (1 - k * np.clip(xx ** 2 * 0.8 + yy ** 2 * 0.8, 0, 1.4) ** 1.3)[..., None]


def over_rgba(rgb, im):
    """Straight-alpha render over the plate. Shadow-catcher pixels are black with partial alpha."""
    a = np.asarray(im.convert("RGBA"), np.float32) / 255
    al = a[..., 3:4]
    return rgb * (1 - al) + a[..., :3] * al


def sprite_text(txt, fnt, pad=6, track=0):
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    if track:
        w = int(sum(d.textlength(c, font=fnt) + track for c in txt)) + pad * 2
        b = d.textbbox((0, 0), txt, font=fnt)
        im = Image.new("L", (w, b[3] - b[1] + pad * 2), 0)
        dd = ImageDraw.Draw(im)
        x = pad
        for c in txt:
            dd.text((x, pad - b[1]), c, 255, font=fnt)
            x += d.textlength(c, font=fnt) + track
        return im
    b = d.textbbox((0, 0), txt, font=fnt)
    im = Image.new("L", (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), 0)
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, 255, font=fnt)
    return im


def layer(spr, x, y, anchor="lt", w=W, h=H, rot=0):
    """Place an L sprite on a blank float layer."""
    s = spr.rotate(rot, Image.BICUBIC, expand=True) if rot else spr
    im = Image.new("L", (w, h), 0)
    if anchor == "c":
        x, y = x - s.width / 2, y - s.height / 2
    im.paste(s, (int(x), int(y)))
    return np.asarray(im, np.float32) / 255


def poly(pts, ss=3):
    im = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def strokes(segs, width=2.0, ss=2):
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for s in segs:
        d.line([(s[0] * ss, s[1] * ss), (s[2] * ss, s[3] * ss)], fill=255, width=max(1, int(width * ss)))
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def path_pts(pts, step):
    """Even points along a polyline."""
    pts = np.array(pts, np.float32)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    t = np.r_[0, np.cumsum(seg)]
    q = np.arange(0, t[-1], step)
    return np.c_[np.interp(q, t, pts[:, 0]), np.interp(q, t, pts[:, 1])]


def print_sprite(seed=0, s=420):
    """One real-looking handprint: palm pad and separate finger pads, not a silhouette. Fingers up."""
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    k = s / 420
    r = np.random.default_rng(seed)

    def ell(cx, cy, rx, ry, ang=0):
        t = Image.new("L", (s, s), 0)
        ImageDraw.Draw(t).ellipse(((cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k), fill=255)
        if ang:
            t = t.rotate(ang, Image.BICUBIC, center=(cx * k, cy * k))
        im.paste(255, (0, 0), t)

    ell(210, 300, 86, 78)                      # palm
    ell(160, 262, 52, 40, 10)
    ell(262, 262, 46, 38, -8)
    ell(144, 322, 40, 58, 12)                  # heel of thumb
    for (x, ang, ln) in ((138, 10, 1.0), (186, 3, 1.12), (232, -4, 1.05), (278, -13, 0.84)):
        for j, (dist, rx, ry) in enumerate(((60, 19, 24), (112, 18, 22), (160, 17, 24))):
            cx = x + (dist * ln + 150) * math.sin(math.radians(-ang)) * -1 * 0 + dist * ln * math.sin(math.radians(ang)) * -1
            cy = 205 - dist * ln
            ell(cx, cy, rx * (0.95 if ln < 0.9 else 1), ry * ln, ang)
    ell(86, 248, 22, 30, 38)                   # thumb
    ell(52, 204, 21, 30, 34)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(3.0 * k)), np.float32) / 255
    n = vnoise(s, s, 20 * k + 2, seed, 3)
    a = np.clip((a + (n - 0.5) * 0.42 - 0.46) * 8, 0, 1)
    return a


def print_sil(seed=0, s=300):
    """Handprint for small sizes: one continuous shape with long splayed fingers, so it still reads as a hand at 35 px."""
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    k = s / 300
    d.rounded_rectangle((92 * k, 150 * k, 214 * k, 268 * k), 46 * k, fill=255)
    for (bx, by, tx, ty, wd) in ((104, 166, 62, 62, 25), (136, 156, 118, 26, 26), (168, 156, 178, 24, 26), (198, 166, 232, 60, 24)):
        d.line([(bx * k, by * k), (tx * k, ty * k)], fill=255, width=int(wd * k))
        d.ellipse(((tx - wd / 2) * k, (ty - wd / 2) * k, (tx + wd / 2) * k, (ty + wd / 2) * k), fill=255)
    d.line([(112 * k, 236 * k), (36 * k, 158 * k)], fill=255, width=int(30 * k))
    d.ellipse((21 * k, 143 * k, 51 * k, 173 * k), fill=255)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(2.5 * k)), np.float32) / 255
    n = vnoise(s, s, 16 * k + 2, seed, 3)
    return np.clip((a + (n - 0.5) * 0.30 - 0.46) * 8, 0, 1)


def rot_sprite(a, ang, size):
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS).rotate(ang, Image.BICUBIC, expand=True)
    return np.asarray(im, np.float32) / 255


def stamp(canvas, a, x, y, mode="max"):
    h, w = a.shape
    x0, y0 = int(x - w / 2), int(y - h / 2)
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(canvas.shape[1], x0 + w), min(canvas.shape[0], y0 + h)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    sub = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    canvas[cy0:cy1, cx0:cx1] = np.maximum(canvas[cy0:cy1, cx0:cx1], sub)


def save(rgb, name):
    p = STILL / name
    Image.fromarray((np.clip(np.nan_to_num(rgb), 0, 1) * 255 + 0.5).astype(np.uint8)).save(str(p))
    print("wrote", name)
