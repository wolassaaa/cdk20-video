"""Shared helpers for the W0 / 1-01 style frames (numpy + PIL only).

Colours follow S1_visual_brief_v2.md: black stage, bone ink, vermilion, electric cyan, plus the pure-blue family.
All images are float32 linear-ish RGB in 0..1 (we treat them as display values; good enough for style frames).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
ROOT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/"
SCRATCH = "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/"


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


BLACK = hexc("060606"); BONE = hexc("EDEBE4"); VERM = hexc("FF3B1F"); CYAN = hexc("29F0FF")
IKB = hexc("002FA7"); BLUE = hexc("1F3BFF"); DEEPBLUE = hexc("0A1AFF")

RNG = np.random.default_rng(7)


def canvas(c=BLACK, w=W, h=H):
    return np.ones((h, w, 3), np.float32) * c


def grid(w=W, h=H):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


# ---------------------------------------------------------------- blur (3 box passes ~ gaussian), any channels
def _box1d(a, r, axis):
    if r < 1: return a
    pad = [(0, 0)] * a.ndim; pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, sigma):
    if sigma <= 0.3: return a
    r = max(1, int(round(np.sqrt(12 * sigma * sigma / 3 + 1) / 2)))
    for _ in range(3):
        a = _box1d(_box1d(a, r, 0), r, 1)
    return a


def fast_blur(a, sigma):
    """Large blur: downsample, blur, upsample."""
    if sigma < 12: return blur(a, sigma)
    k = int(sigma // 6)
    h, w = a.shape[:2]
    im = a[: h - h % k, : w - w % k]
    sm = im.reshape(h // k, k, w // k, k, *a.shape[2:]).mean(axis=(1, 3))
    sm = blur(sm, sigma / k)
    up = np.repeat(np.repeat(sm, k, 0), k, 1)
    pad = [(0, h - up.shape[0]), (0, w - up.shape[1])] + [(0, 0)] * (a.ndim - 2)
    out = np.pad(up, pad, mode="edge")
    return blur(out, k * 0.8)


def bloom(img, sig=(6, 24, 70), gain=(0.35, 0.25, 0.2), thresh=0.6):
    hi = np.clip(img - thresh, 0, None)
    out = img.copy()
    for s, g in zip(sig, gain):
        out += fast_blur(hi, s) * g
    return out


# ---------------------------------------------------------------- noise
def value_noise(w, h, scale, seed=0, octaves=1):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gw, gh = int(w / scale) + 3, int(h / scale) + 3
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(g).resize((int(gw * scale), int(gh * scale)), Image.BICUBIC)
        a = np.asarray(im)[:h, :w]
        out += a * amp; tot += amp; amp *= 0.5; scale /= 2
        if scale < 1.5: break
    return out / tot


def grain(img, amt=0.06, seed=1, mono=True, size=1.0):
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    if size > 1:
        n = rng.standard_normal((int(h / size) + 1, int(w / size) + 1)).astype(np.float32)
        n = np.asarray(Image.fromarray(n).resize((int(n.shape[1] * size), int(n.shape[0] * size)), Image.BILINEAR))[:h, :w]
    else:
        n = rng.standard_normal((h, w)).astype(np.float32)
    n = n[..., None] if mono else rng.standard_normal((h, w, 3)).astype(np.float32)
    # film-like: more grain in the mids
    lum = img.mean(-1, keepdims=True)
    k = 0.45 + 0.55 * np.clip(4 * lum * (1 - lum), 0, 1)
    return img + n * amt * k


def posterize_band(img, levels=48, amt=0.5):
    """Print-like banding: quantise softly."""
    q = np.round(img * levels) / levels
    return img * (1 - amt) + q * amt


def vignette(img, strength=0.35, power=2.2):
    x, y = grid(img.shape[1], img.shape[0])
    d = np.sqrt(((x - img.shape[1] / 2) / (img.shape[1] / 2)) ** 2 + ((y - img.shape[0] / 2) / (img.shape[0] / 2)) ** 2) / 1.414
    return img * (1 - strength * d[..., None] ** power)


def tonemap(img, white=1.25):
    """Soft shoulder so glows roll off instead of clipping."""
    x = np.clip(img, 0, None)
    return x * (1 + x / (white * white)) / (1 + x)


def save(img, path, tm=False):
    if tm: img = tonemap(img)
    a = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(a).save(path)
    print("saved", path)


def to_pil(img):
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def from_pil(im):
    return np.asarray(im.convert("RGB"), np.float32) / 255


# ---------------------------------------------------------------- type
BAHN = "C:/Windows/Fonts/bahnschrift.ttf"
CONS = "C:/Windows/Fonts/consola.ttf"


def font(size, style="Regular", path=BAHN):
    f = ImageFont.truetype(path, size)
    if path == BAHN:
        try: f.set_variation_by_name(style)
        except Exception: pass
    return f


def text_mask(txt, size, style="Regular", path=BAHN, tracking=0, w=W, h=H, xy=(0, 0), anchor="la", ss=1):
    """Return a float mask (h, w) with text drawn; tracking in px between glyphs."""
    m = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(m)
    f = font(size * ss, style, path)
    x, y = xy[0] * ss, xy[1] * ss
    if tracking == 0:
        d.text((x, y), txt, fill=255, font=f, anchor=anchor)
    else:
        widths = [d.textlength(ch, font=f) + tracking * ss for ch in txt]
        tot = sum(widths) - tracking * ss
        if anchor[0] == "m": x -= tot / 2
        elif anchor[0] == "r": x -= tot
        for ch, wd in zip(txt, widths):
            d.text((x, y), ch, fill=255, font=f, anchor="l" + anchor[1])
            x += wd
    if ss > 1: m = m.resize((w, h), Image.LANCZOS)
    return np.asarray(m, np.float32) / 255


def ink(img, mask, color, alpha=1.0):
    m = mask[..., None] * alpha
    return img * (1 - m) + color * m


def label(img, txt, xy, size=17, color=None, anchor="la", tracking=2, alpha=0.75):
    color = BONE if color is None else color
    return ink(img, text_mask(txt, size, path=CONS, tracking=tracking, xy=xy, anchor=anchor), color, alpha)


def illustrative(img, xy=(1880, 1046), anchor="rs", alpha=0.55):
    return label(img, "ILLUSTRATIVE", xy, size=15, anchor=anchor, tracking=3, alpha=alpha)


# ---------------------------------------------------------------- A's on-cam card (rendered by Remotion, src/v3/s1v2/w0/entry.jsx)
def card(frame=40):
    im = np.asarray(Image.open(SCRATCH + f"cardA_{frame}.png").convert("RGBA"), np.float32) / 255
    rgb, a = im[..., :3], im[..., 3:4]
    # the card's own drop shadow is warm brown; on coloured grounds use a neutral dark shadow instead
    paper = (a > 0.97).astype(np.float32)
    paper = blur(paper, 0.7)
    return rgb, a, paper


def comp_card(img, frame=40, shadow=0.75):
    rgb, a, paper = card(frame)
    sh = np.clip(a - paper, 0, 1) * shadow
    out = img * (1 - sh)
    return out * (1 - paper) + rgb * paper


def finish(img, out, card_frame=None, grain_amt=0.05, vig=0.4, seed=5, tag=True, tm=True, post=None):
    """Grade the world, then lay A's card on top (the card keeps its own warm print look), unify with light grain."""
    img = vignette(img, vig) if vig else img
    img = grain(img, grain_amt, seed=seed)
    if tm: img = tonemap(img)
    if card_frame is not None:
        img = comp_card(img, card_frame)
        img = grain(img, 0.018, seed=seed + 1)
    if post: img = post(img)
    if tag: img = illustrative(img)
    save(img, out)
