"""HKBU SCIE1007 coursework science video. Tools for the neon street direction: glass tube signs, lightboxes, bulb signs, the far street and the wet road. Stills only, nothing here flickers."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
sys.path.insert(0, str(ROOT / "styleframes/art/scouts/f/code"))
sys.path.insert(0, str(ROOT / "styleframes/art/scouts/g/code"))
from fx import ADV, STROKES, box_x, contours, gauss, mix, noise, noise_raw, rgb, sample, screen, smooth  # noqa: E402,F401
from glib import atoms, render, rot, smooth_pass, surface  # noqa: E402,F401

W, H = 1920, 1080
OUT = ROOT / "styleframes/art/neon/stills"
OUT.mkdir(parents=True, exist_ok=True)
WORK = ROOT / "styleframes/art/neon/_work"
WORK.mkdir(exist_ok=True)
LABEL = "AlphaFold DB v6 \u00b7 predicted"
yy, xx = np.mgrid[:H, :W].astype(np.float32)

HOT = np.array([1.0, 0.97, 0.94], np.float32)
PINK = np.array([1.0, 0.06, 0.40], np.float32)
RED = np.array([1.0, 0.09, 0.05], np.float32)
AMB = np.array([1.0, 0.46, 0.04], np.float32)
GRN = np.array([0.08, 1.0, 0.44], np.float32)
CYN = np.array([0.08, 0.70, 1.0], np.float32)
YEL = np.array([1.0, 0.82, 0.12], np.float32)
PAL = [PINK, GRN, CYN, YEL, RED, AMB]
ORD = ["\u8336\u9910\u5ef3", "\u91d1\u884c", "\u62bc", "\u7ca5\u9eb5", "\u6dbc\u8336", "\u9152\u5bb6", "\u65c5\u9928", "\u71d2\u81d8", "\u8a3a\u6240", "\u58eb\u591a", "\u51b0\u5ba4", "\u7406\u9aee", "\u914d\u5319", "\u958b\u9396", "\u85e5\u623f", "\u5316\u9a57"]


def nfont(size, weight="Black", serif=False):
    """Noto Sans SC and Noto Serif SC, both SIL OFL."""
    f = ImageFont.truetype("C:/Windows/Fonts/" + ("NotoSerifSC-VF.ttf" if serif else "NotoSansSC-VF.ttf"), int(size))
    f.set_variation_by_name(weight)
    return f


def text(txt, size, xy, weight="Black", anchor="ls", tracking=0, serif=False, wh=(W, H), ss=2):
    """Antialiased text mask, supersampled, manual tracking."""
    w, h = wh
    f = nfont(size * ss, weight, serif)
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    x, y = xy[0] * ss, xy[1] * ss
    if tracking == 0:
        d.text((x, y), txt, 255, font=f, anchor=anchor)
    else:
        tot = sum(d.textlength(c, font=f) + tracking * ss for c in txt) - tracking * ss
        if anchor[0] == "m":
            x -= tot / 2
        elif anchor[0] == "r":
            x -= tot
        for c in txt:
            d.text((x, y), c, 255, font=f, anchor="l" + anchor[1])
            x += d.textlength(c, font=f) + tracking * ss
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def text_w(txt, size, weight="Black", tracking=0):
    f = nfont(size, weight)
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    return sum(d.textlength(c, font=f) + tracking for c in txt) - tracking


def neon(t, col, gain=1.0, haze=1.0):
    """One lit tube: white hot core, tight gas colour, wide haze."""
    t = np.clip(t, 0, 1.5)
    col = np.asarray(col, np.float32)
    g = gauss(t, 1.9)[..., None] * 1.15 + gauss(t, 6)[..., None] * 0.9 + (gauss(t, 24)[..., None] * 0.8 + gauss(t, 75)[..., None] * 0.55) * haze
    core = np.clip(gauss(t, 0.8) * 1.3 - 0.15, 0, 1)[..., None]
    return (col * g + (HOT * 0.6 + col * 0.4) * core * 1.2) * gain


def cold_tube(t):
    """An unlit glass tube: only a thin grey highlight, picks up a little of the street."""
    return gauss(t, 0.8)[..., None] * np.array([0.11, 0.115, 0.13], np.float32)


def homog(src, dst):
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    return np.append(np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64)), 1).reshape(3, 3)


def warp(img, quad, sw, sh):
    """Hang a flat sw x sh sign on the quad tl tr br bl in the frame."""
    M = homog(quad, [(0, 0), (sw, 0), (sw, sh), (0, sh)])
    d = M[2, 0] * xx + M[2, 1] * yy + M[2, 2]
    sx = ((M[0, 0] * xx + M[0, 1] * yy + M[0, 2]) / d).astype(np.float32)
    sy = ((M[1, 0] * xx + M[1, 1] * yy + M[1, 2]) / d).astype(np.float32)
    ins = ((sx >= 0) & (sx < sw - 1) & (sy >= 0) & (sy < sh - 1)).astype(np.float32)
    out = sample(img, sx, sy)
    return out * (ins[..., None] if img.ndim == 3 else ins), ins


def smooth_loop(p, s):
    n = len(p)
    r = int(3 * s)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    idx = (np.arange(n)[:, None] + np.arange(-r, r + 1)[None]) % n
    return (p[idx] * k[None, :, None]).sum(1)


def tube_loops(mask_bool, s=9.0, minlen=70):
    """Real glass cannot bend tighter than a few cm: outlines are traced then relaxed."""
    out = []
    for lp in contours(mask_bool):
        if len(lp) < minlen:
            continue
        out.append(smooth_loop(lp[::2].astype(np.float32), s / 2))
    return out


def draw_tube(wh, loops, width=4, dash=None, ss=2, closed=True, value=None):
    """Polylines to a tube mask. dash=(on, off) in pixels gives the broken low-confidence tube. value(point) can switch segments off."""
    w, h = wh
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    for lp in loops:
        p = np.vstack([lp, lp[:1]]) if closed else lp
        if value is not None:
            keep = value(p)
        else:
            keep = np.ones(len(p), bool)
        seg = np.hypot(*(p[1:] - p[:-1]).T)
        t = np.r_[0, np.cumsum(seg)]
        if dash:
            on = (t % (dash[0] + dash[1])) < dash[0]
            keep = keep & on
        run = []
        for i in range(len(p)):
            if keep[i]:
                run.append((float(p[i, 0]) * ss, float(p[i, 1]) * ss))
            else:
                if len(run) > 1:
                    d.line(run, fill=255, width=width * ss, joint="curve")
                run = []
        if len(run) > 1:
            d.line(run, fill=255, width=width * ss, joint="curve")
    return np.asarray(im.resize((w, h), Image.BILINEAR), np.float32) / 255


def step_print(a, n, step, blur, decay, seed=0):
    """Discrete repeats of one frame, each with its own blur. Frozen into the plate so nothing strobes."""
    r = np.random.default_rng(seed)
    out = np.zeros_like(a)
    tot = 0.0
    for i in range(n):
        b = np.roll(box_x(a, blur), int(i * step), axis=1)
        b = np.roll(b, int(r.normal(0, 2.0)), axis=0)
        wt = decay ** i
        out += b * wt
        tot += wt
    return out / tot * (1 + 0.5 * (n - 1) ** 0.5)


def street(vp, seed=12, n=90, pal=None, gain=1.0, smear=True, sky=(0.012, 0.012, 0.03), words=None):
    """The far street: a crowd of signs converging on vp, out of focus and step printed. Common words only, no shop names."""
    r = np.random.default_rng(seed)
    words = words or ORD
    pal = pal if pal is not None else PAL
    lay = np.zeros((len(pal), H, W), np.float32)
    fnt = {}
    for i in range(n):
        d = r.uniform(0.13, 1.0) ** 1.25
        side = r.choice([-1, 1])
        x = vp[0] + side * (r.uniform(0.16, 1.15)) * 1500 * d
        y = vp[1] + r.uniform(-1.15, 0.72) * 720 * d
        hh = r.uniform(0.5, 1.0) * 400 * d
        ww = hh * r.uniform(0.3, 0.6)
        wd = words[r.integers(len(words))]
        ci = r.integers(len(pal))
        im = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(im)
        dr.rectangle((x, y, x + ww, y + hh), outline=255, width=max(1, int(5 * d)))
        sz = max(12, int(min(ww * 0.72, hh * 0.86 / len(wd))))
        f = fnt.setdefault(sz, nfont(sz, "Bold"))
        for j, ch in enumerate(wd):
            dr.text((x + ww / 2, y + (j + 0.5) * hh / len(wd)), ch, 255, font=f, anchor="mm")
        lay[ci] += np.asarray(im, np.float32) / 255 * (0.5 + 0.5 * d)
    far = np.zeros((H, W, 3), np.float32)
    for ci in range(len(pal)):
        if lay[ci].max() > 0:
            far += neon(gauss(lay[ci], 3.0), pal[ci], 0.55 * gain, 0.12)
    grad = (yy / H)[..., None]
    base = np.asarray(sky, np.float32) * (0.55 + 1.4 * grad)
    if smear:
        far = step_print(far, 5, 46, 34, 0.72, seed)
        far = np.clip(far * 0.7, 0, 4) ** 1.2
    return base + far


def street_cached(vp, seed=12, **kw):
    key = f"street_{vp[0]}_{vp[1]}_{seed}_{kw.get('n', 90)}_{kw.get('tag', '')}"
    p = WORK / (key + ".npy")
    if p.exists():
        return np.load(p)
    kw.pop("tag", None)
    a = street(vp, seed=seed, **kw).astype(np.float32)
    np.save(p, a)
    return a


def person(d, x, base, h, ss=3, phone=False, flip=1):
    """A small passer-by, polygon silhouette. Placeholder for phone footage at this scale."""
    def T(pts):
        return [((x + flip * a * h) * ss, (base - b * h) * ss) for a, b in pts]
    d.polygon(T([(-0.075, 0), (-0.03, 0), (-0.005, 0.44), (0.02, 0), (0.08, 0), (0.09, 0.47), (0.105, 0.8), (0.07, 0.855), (0.022, 0.87), (-0.022, 0.87), (-0.075, 0.85), (-0.105, 0.78), (-0.09, 0.47)]), fill=255)
    d.polygon(T([(-0.105, 0.8), (-0.145, 0.5), (-0.115, 0.49), (-0.07, 0.72)]), fill=255)
    if phone:
        d.polygon(T([(0.09, 0.83), (0.2, 0.86), (0.19, 1.04), (0.16, 1.04), (0.16, 0.9), (0.08, 0.77)]), fill=255)
        d.rectangle(sorted_box(T([(0.13, 1.03), (0.23, 1.15)])), fill=255)
    else:
        d.polygon(T([(0.105, 0.8), (0.145, 0.5), (0.115, 0.49), (0.07, 0.72)]), fill=255)
    a, b = T([(-0.066, 1.0)])[0], T([(0.066, 0.865)])[0]
    d.ellipse(sorted_box([a, b]), fill=255)


def sorted_box(p):
    (a, b), (c, e) = p
    return [min(a, c), min(b, e), max(a, c), max(b, e)]


def building_mass(rgbf, vp, left=True, right=True):
    """Dark walls that make the street a canyon."""
    if left:
        edge = vp[0] - (yy - vp[1]) * 0.0 - np.abs(yy - vp[1]) * 0.9 - 60
        rgbf = rgbf * (1 - 0.55 * smooth(edge + 30, edge - 120, xx))[..., None]
    if right:
        edge = vp[0] + np.abs(yy - vp[1]) * 1.1 + 60
        rgbf = rgbf * (1 - 0.55 * smooth(edge - 30, edge + 160, xx))[..., None]
    return rgbf


def wet_road(rgbf, wy, strength=0.9, seed=31, fall=240):
    """Everything above, smeared down into a wet road."""
    rip = (noise((H, W), 2.0, seed) - 0.5) * 38
    rx = xx + rip * np.clip(yy - wy, 0, None) / 90
    ry = np.clip(2 * wy - yy + rip * 0.3, 0, H - 1)
    refl = gauss(sample(rgbf, rx, ry), 3.0)
    vb = np.zeros_like(refl)
    for k in range(1, 9):
        vb += sample(refl, xx, np.clip(yy - k * 9, 0, H - 1))
    refl = (refl + vb) / 9
    amt = np.clip(1 - (yy - wy) / fall, 0.2, 1) * strength
    out = np.where((yy > wy)[..., None], refl * amt[..., None] + np.array([0.008, 0.009, 0.014], np.float32), rgbf)
    return out * (1 - np.exp(-((yy - wy) / 4) ** 2) * 0.8)[..., None]


def finish(rgbf, name, halation=0.7, soft=True):
    """Same print for every still: highlights bleed warm, blacks lean green, a soft shoulder keeps colour in the neon."""
    hl = np.clip(rgbf - 0.75, 0, 4)
    rgbf = rgbf + gauss(hl, 7) * [1.0, 0.45, 0.4] * halation * 0.6 + gauss(hl, 26) * [0.9, 0.3, 0.3] * halation * 0.35
    rgbf = rgbf + gauss(np.clip(rgbf - 0.5, 0, 3), 44) * 0.10
    x = np.clip(rgbf, 0, None)
    out = np.where(x < 0.8, x, 0.8 + 0.2 * (1 - np.exp(-(x - 0.8) / 0.2)))
    lum = out.mean(-1)
    out = out + (1 - smooth(0.0, 0.16, lum))[..., None] * np.array([0.0, 0.012, 0.010], np.float32)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / name)
    return out


def subtitle(rgbf, lines, y_last, size=44, x=None, col="#FFF08A"):
    """The words a person says are burned in like a Hong Kong print. Molecules and data get signs, people get subtitles."""
    lh = size * 1.32
    for i, ln in enumerate(lines):
        yl = y_last - (len(lines) - 1 - i) * lh
        m = text(ln, size, (W / 2 if x is None else x, yl), "Medium", "ms" if x is None else "ls")
        o = np.clip(gauss(m, 2.2) * 6, 0, 1)
        rgbf = rgbf * (1 - 0.93 * o)[..., None]
        rgbf = rgbf * (1 - m)[..., None] + rgb(col) * m[..., None]
    return rgbf
