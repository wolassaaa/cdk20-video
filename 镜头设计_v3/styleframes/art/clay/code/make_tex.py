"""HKBU SCIE1007 coursework science video. Clay direction: flat textures for the work table (system Python, PIL + numpy).

Cutting mat, glazed tiles with painted type, the pencil sheet, paper flags, the person plate that stands in for phone footage.
All on-screen words are copied letter for letter from the master brief.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import FONTS, ROOT, WORK

WORK.mkdir(exist_ok=True)
rng = np.random.default_rng(1)
BOLD = FONTS + "/bahnschrift.ttf"
SEMI = FONTS + "/segoeuib.ttf"
HAND = FONTS + "/segoeprb.ttf"


def fnt(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght and "bahnschrift" in path:
        f.set_variation_by_axes([wght, 100])
    return f


def mat(dark=False):
    """60 x 40 units, 1 unit = 2 cm, so the grid is 1 cm = 0.5 unit."""
    S = 136
    W, H = 60 * S, 40 * S
    im = Image.new("RGB", (W, H), (20, 84, 66))
    d = ImageDraw.Draw(im)
    line = (150, 190, 120)
    for i in range(0, 121):
        x = i * S // 2
        d.line((x, 0, x, H), fill=line, width=6 if i % 10 == 0 else 2)
    for j in range(0, 81):
        y = j * S // 2
        d.line((0, y, W, y), fill=line, width=6 if j % 10 == 0 else 2)
    f = fnt(BOLD, 44)
    for i in range(0, 121, 10):
        for j in (0, 40, 80):
            d.text((i * S // 2 + 12, j * S // 2 + 8), str(i // 2 if i else 0), font=f, fill=line)
    # years of knife cuts
    for _ in range(900):
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
        a = rng.choice([0, np.pi / 2, rng.uniform(0, 3.14)], p=[0.35, 0.35, 0.3])
        L = rng.uniform(200, 2400)
        d.line((x0, y0, x0 + np.cos(a) * L, y0 + np.sin(a) * L), fill=(60, 128, 104), width=int(rng.integers(1, 3)))
    a = np.asarray(im, np.float32)
    n = np.asarray(Image.fromarray((rng.random((H // 16, W // 16)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    n2 = np.asarray(Image.fromarray((rng.random((H // 200, W // 200)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    a = a * (0.86 + 0.22 * n[..., None]) * (0.8 + 0.38 * n2[..., None])
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W // 2, H // 2), Image.LANCZOS).save(WORK / "mat.jpg", quality=92)


def wobble(mask, amp=1.2, seed=0):
    """Brush edge: a small low frequency warp so painted type looks painted without getting harder to read."""
    g = np.random.default_rng(seed)
    h, w = mask.shape
    nx = np.asarray(Image.fromarray((g.random((h // 30, w // 30)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
    ny = np.asarray(Image.fromarray((g.random((h // 30, w // 30)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
    yy, xx = np.mgrid[0:h, 0:w]
    xi = np.clip(xx + nx * amp * 2, 0, w - 1).astype(int)
    yi = np.clip(yy + ny * amp * 2, 0, h - 1).astype(int)
    return mask[yi, xi]


def tile(name, w, h, rows, glaze, ink, seed=3):
    """rows: (text, font path, size, y, x or None for centred). Colour map plus a bump map for pooled glaze."""
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for r in rows:
        txt, path, size, y, x = r[:5]
        f = fnt(path, size, r[5] if len(r) > 5 else None)
        tw = d.textlength(txt, font=f)
        d.text(((w - tw) / 2 if x is None else x, y), txt, font=f, fill=255)
    m = np.asarray(im, np.float32) / 255
    m = wobble(m, 1.0, seed)
    g = np.random.default_rng(seed)
    base = np.array(glaze, np.float32)
    kin = np.array(ink, np.float32)
    mott = np.asarray(Image.fromarray((g.random((h // 40, w // 40)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    col = base * (0.985 + 0.03 * mott[..., None])
    col = col * (1 - m[..., None]) + kin * m[..., None] * (0.9 + 0.2 * mott[..., None])
    # glaze thins at the edge and shows the body
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.minimum(np.minimum(xx, w - xx), np.minimum(yy, h - yy)) / (0.012 * w)
    t = np.clip(e, 0, 1)[..., None]
    col = col * t + np.array([150, 110, 78], np.float32) * (1 - t)
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(WORK / f"{name}.png")
    Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)).save(WORK / f"{name}_h.png")


def paper_base(w, h, seed=2, tint=(240, 233, 216)):
    g = np.random.default_rng(seed)
    fib = np.asarray(Image.fromarray((g.random((h // 3, w // 3)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    blot = np.asarray(Image.fromarray((g.random((h // 90, w // 90)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    return np.array(tint, np.float32) * (0.95 + 0.06 * fib[..., None]) * (0.96 + 0.05 * blot[..., None])


def pencil_sheet():
    """The re-docking, drawn in graphite from the project's own render. Only redrawn, the structure is not touched."""
    W, H = 1500, 1800
    src = Image.open(ROOT / "styleframes/S2plus/public/pose_048_lines.png").convert("RGBA")
    # crop to the drawing and keep aspect
    box = (965, 417, 3248, 3527)
    src = src.crop(box)
    tw = 1330
    th = int(src.height * tw / src.width)
    if th > 1380:
        th = 1380
        tw = int(src.width * th / src.height)
    src = src.resize((tw, th), Image.LANCZOS)
    lig_src = Image.open(ROOT / "styleframes/S2plus/public/pose_048_lig.png").convert("RGBA").crop(box).resize((tw, th), Image.LANCZOS)
    a = np.asarray(src, np.float32) / 255
    alpha = a[..., 3]
    b = np.asarray(lig_src, np.float32) / 255
    lig_a = b[..., 3]
    lig_lum = (b[..., :3] * [0.3, 0.6, 0.1]).sum(-1)
    lig = lig_a > 0.5
    li = Image.fromarray((lig * 255).astype(np.uint8))
    edge = np.asarray(li.filter(ImageFilter.MaxFilter(5)), np.float32) / 255 - np.asarray(li.filter(ImageFilter.MinFilter(3)), np.float32) / 255
    # pocket: the project's own contour lines, in graphite, kept lighter so the ligand stays on top
    ink = alpha * 0.62
    ink = np.where(lig, (1 - np.clip(lig_lum, 0, 1)) * 1.6, ink)      # shaded balls, heavier than the pocket
    ink = np.maximum(ink, edge * 1.0)
    p = paper_base(W, H)
    cv = np.zeros((H, W), np.float32)
    x0, y0 = (W - tw) // 2, 150
    cv[y0:y0 + th, x0:x0 + tw] = ink
    g = np.random.default_rng(9)
    # pencil only catches the tooth of the paper
    tooth = np.asarray(Image.fromarray((g.random((H // 2, W // 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    cv = cv * np.clip(0.62 + 0.75 * tooth, 0, 1)
    ligfill = np.zeros((H, W), np.float32)
    ligfill[y0:y0 + th, x0:x0 + tw] = lig
    col = p * (1 - np.clip(cv * 1.1, 0, 0.92)[..., None]) + np.array([42, 42, 46], np.float32) * np.clip(cv * 1.1, 0, 0.92)[..., None]
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = fnt(HAND, 74)
    txt = "OUR RE-DOCKING"
    tw2 = d.textlength(txt, font=f)
    x = (W - tw2) / 2
    y = H - 170
    # a dashed box, ruled by hand
    pad = 34
    bb = (x - pad, y - 16, x + tw2 + pad, y + 112)
    pts = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3]), (bb[0], bb[1])]
    for a0, b0 in zip(pts, pts[1:]):
        L = np.hypot(b0[0] - a0[0], b0[1] - a0[1])
        n = int(L / 42)
        for i in range(n):
            t0, t1 = i / n, (i + 0.62) / n
            d.line((a0[0] + (b0[0] - a0[0]) * t0, a0[1] + (b0[1] - a0[1]) * t0 + g.normal(0, 0.8),
                    a0[0] + (b0[0] - a0[0]) * t1, a0[1] + (b0[1] - a0[1]) * t1 + g.normal(0, 0.8)), fill=(46, 46, 50), width=5)
    d.text((x, y), txt, font=f, fill=(38, 38, 42))
    im.save(WORK / "pencil.png")


def flag(name, lines, w=620, h=250, size=None):
    p = paper_base(w, h, seed=abs(hash(name)) % 1000)
    im = Image.fromarray(np.clip(p, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    s = size or 84
    f = fnt(SEMI, s)
    tot = len(lines) * s * 1.14
    y = (h - tot) / 2 - 8
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((w - tw) / 2, y), ln, font=f, fill=(30, 26, 22))
        y += s * 1.14
    im.save(WORK / f"flag_{name}.png")


def text_card():
    W, H = 1600, 1200
    p = paper_base(W, H, seed=5, tint=(244, 236, 216))
    im = Image.fromarray(np.clip(p, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = fnt(SEMI, 118)
    lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
    # measured width guard
    mx = max(d.textlength(l, font=f) for l in lines)
    if mx > W - 170:
        f = fnt(SEMI, int(118 * (W - 170) / mx))
    y = 170
    for l in lines:
        d.text((85, y), l, font=f, fill=(28, 24, 20))
        y += 232
    im.save(WORK / "card.png")


def catmull(pts, n=26):
    P = np.array(pts, np.float32)
    P = np.r_[P[[-1]], P, P[:2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    return [tuple(p) for p in out]


def person():
    """Stand-in for the phone footage: a flat warm cut-out plate, side-on, because that is literally how the footage arrives."""
    W, H = 1400, 1700
    S = 2
    head = [(600, 170), (705, 165), (790, 215), (830, 300), (838, 365), (875, 425), (842, 450), (850, 490), (838, 520), (842, 556),
            (815, 600), (745, 612), (700, 640), (700, 720), (760, 770), (900, 830), (1010, 930), (1060, 1150), (1090, 1700),
            (120, 1700), (150, 1200), (210, 960), (330, 840), (455, 760), (495, 660), (470, 560), (445, 440), (470, 290), (525, 205)]
    im = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(im).polygon([(x * S, y * S) for x, y in catmull(head)], fill=255)
    m = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    blur = lambda r: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    # cut out with scissors: straight facets, a cream paper border, then the warm-graded picture inside
    pts = catmull(head)
    cuts = pts[::11] + [pts[-1]]
    out = Image.new("L", (W * S, H * S), 0)
    dc = ImageDraw.Draw(out)
    dc.polygon([(x * S, y * S) for x, y in cuts], fill=255)
    dc.line([(x * S, y * S) for x, y in cuts + cuts[:1]], fill=255, width=52, joint="curve")
    outer = np.asarray(out.resize((W, H), Image.LANCZOS), np.float32) / 255
    # form: lit from the right, the plate darkens to the left and towards the table, as the graded footage would
    lit = np.clip((m - np.roll(blur(30), -34, 1)) * 1.8, 0, 1)
    g = np.random.default_rng(5)
    grain = g.normal(0, 5, (H, W, 1)).astype(np.float32)
    body = np.array([104, 66, 52], np.float32) * (0.9 + 0.35 * np.clip((1500 - yy) / 1500, 0, 1))[..., None]
    body = body + np.array([196, 118, 70], np.float32) * lit[..., None] * 0.55 + grain
    paper = np.array([238, 228, 206], np.float32)
    col = paper * (1 - m[..., None]) + body * m[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), outer * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(1.2)).save(WORK / "person.png")


which = sys.argv[1:] or ["mat", "tiles", "pencil", "flags", "card", "person"]
if "mat" in which:
    mat()
if "tiles" in which:
    # T5: the measured value, in cobalt on a white glazed tile
    tile("tile_t5", 2000, 1160, [
        ("Enzyme IC50", SEMI, 120, 86, 120),
        ("048 = 33.4 ± 22.6 nM", SEMI, 182, 350, None),
        ("MEASURED · Ren 2023, Fig. 9A", SEMI, 96, 870, 120),
    ], (250, 249, 245), (14, 44, 134))
    tile("tile_t1", 2000, 1000, [
        ("1,412", SEMI, 460, 70, None),
        ("deaths in Hong Kong, 2022", SEMI, 126, 700, None),
    ], (22, 20, 20), (226, 214, 194), seed=7)
if "pencil" in which:
    pencil_sheet()
if "flags" in which:
    flag("target", ["Target"])
    flag("hit", ["Hit"])
    flag("improve", ["Improve"])
    flag("cells", ["Cells &", "animals"], size=80)
    flag("trials", ["Clinical trials", "1-2-3"], size=80)
    flag("approval", ["Approval"])
    flag("nr", ["not reported"], h=150, w=620, size=78)
    flag("048", ["048"], w=300, h=170, size=104)
    flag("label", ["AlphaFold DB v6 · predicted"], w=1240, h=170, size=84)
    flag("sch", ["no one had measured CDK20's shape"], w=1500, h=210, size=84)
    flag("sch2", ["schematic"], w=520, h=170, size=80)
    flag("caption", ["Just this much cuts the", "enzyme's activity in half."], w=1500, h=340, size=112)
if "card" in which:
    text_card()
if "person" in which:
    person()
print("ok")
