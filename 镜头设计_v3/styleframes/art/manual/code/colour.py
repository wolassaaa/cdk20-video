"""HKBU SCIE1007 coursework science video. manual colour script: eight chapters of the booklet, widths by real running time. Crops of the delivered stills where they exist, small pages in the same inks for the others. The strip at the foot is the rune row turning into letters: real sequence, read left to right."""
from mk import *

W, H = 1920, 480
TOP = 368
DUR = {k: CH[k]["len"] for k in CH}
xs = [0]
for k in range(1, 9):
    xs.append(xs[-1] + DUR[k] / T_ALL * W)
xs = [int(round(v)) for v in xs]
xs[-1] = W
img = np.zeros((H, W, 3), np.float32)


def crop(name, cx, cy, ww, hh, scale):
    a = np.asarray(Image.open(ST / name).convert("RGB"), np.float32) / 255
    h, w = a.shape[:2]
    cw, ch = ww / scale, hh / scale
    x0 = int(np.clip(cx - cw / 2, 0, w - cw))
    y0 = int(np.clip(cy - ch / 2, 0, h - ch))
    im = Image.fromarray((a[y0:int(y0 + ch), x0:int(x0 + cw)] * 255).astype(np.uint8)).resize((ww, hh), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def keyhole(M, cx, cy, r, solid=True, seed=0):
    t = np.linspace(np.pi / 2 + 0.72, 2.5 * np.pi - 0.72, 60)
    pts = [(cx + r * 1.1, cy + r * 2.6), (cx - r * 1.1, cy + r * 2.6)] + [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in t]
    pts.append(pts[0])
    if solid:
        M.poly(pts)
    else:
        M.dash(pts, 2.4, 10, 8, 0.4, seed)


def s1(ww, hh):
    p = paper(CH[1]["paper"], 71, ww, hh)
    M = Mask(ww, hh, 2)
    M.text((12, 214), "1,412", serif(96 * 2, 900), "ls")
    p = ink(p, M.a(), CH[1]["ink"])
    B = Mask(ww, hh, 2)
    B.rect(0, 240, ww, hh)
    p = ink(p, B.a(), CH[1]["spot"])
    R = Mask(ww, hh, 2)
    R.runes(12, 262, ww - 20, 5, 0, 7.0, 10.0, 3.0, 22.0, 1.2)
    return ink(p, R.a() * 0.7, "#c8c4b8")


def s3(ww, hh):
    p = paper(CH[3]["paper"], 73, ww, hh)
    M = Mask(ww, hh, 2)
    keyhole(M, ww / 2, 150, 46, True)
    a = M.a()
    # the emptiest page of the book: the hole shows nothing at all, only its cut edge catches light
    lip = np.clip(gauss(a, 1.4) - np.roll(np.roll(gauss(a, 1.4), 3, 0), 3, 1), 0, 1)
    p = p * (1 - a[..., None]) + hexc("#000000") * a[..., None]
    return ink(p, lip * 2, CH[3]["ink"])


def s7(ww, hh):
    p = paper(CH[7]["paper"], 77, ww, hh)
    D = Mask(ww, hh, 2)
    for i in range(3):
        keyhole(D, ww / 2, 58 + i * 122, 20, False, i)
    return ink(p, D.a(), CH[7]["ink"])


def s8(ww, hh):
    p = paper(CH[8]["paper"], 78, ww, hh)
    R = Mask(ww, hh, 2)
    R.runes(14, 200, ww - 26, 8, 0, 7.0, 10.0, 3.0, 22.0, 1.2)
    p = ink(p, R.a() * 0.75, CH[8]["ink"])
    L = Mask(ww, hh, 2)
    L.rect(14, 60, ww - 14, 66)
    L.rect(14, 80, ww - 44, 86)
    L.rect(14, 100, ww - 24, 106)
    L.rect(14, 120, ww - 70, 126)
    L.rect(14, 140, ww - 34, 146)
    p = ink(p, L.a(), CH[8]["ink"])
    G = Mask(ww, hh, 2)
    G.rect(ww - 30, 0, ww - 16, 170)
    return ink(p, G.a(), CH[8]["spot"])


P = {
    1: lambda w_, h_: crop("T1.png", 1400, 540, w_, h_, 0.346),
    2: lambda w_, h_: crop("T2.png", 530, 500, w_, h_, 0.40),
    3: lambda w_, h_: crop("T3.png", 960, 520, w_, h_, 0.36),
    4: lambda w_, h_: crop("T4.png", 960, 470, w_, h_, 0.46),
    5: lambda w_, h_: crop("T5.png", 1400, 600, w_, h_, 0.46),
    6: lambda w_, h_: crop("T6.png", 1028, 470, w_, h_, 0.48),
    7: lambda w_, h_: s7(w_, h_),
    8: lambda w_, h_: s8(w_, h_),
}
for k in range(1, 9):
    x0, x1 = xs[k - 1], xs[k]
    img[0:TOP, x0:x1] = P[k](x1 - x0, TOP)

# Foot of the sheet: the running rune row. Chapter 4 is where the reading jumps. It never reaches the end.
READ = {1: 0.0, 2: 0.10, 3: 0.10, 4: 0.55, 5: 0.72, 6: 0.80, 7: 0.80, 8: 0.86}  # share of each chapter's foot row already in letters
foot = np.zeros((H - TOP, W, 3), np.float32)
for k in range(1, 9):
    x0, x1 = xs[k - 1], xs[k]
    foot[:, x0:x1] = paper(CH[k]["paper"], 90 + k, x1 - x0, H - TOP)
img[TOP:] = foot
Mr = Mask(W, H, 2)
Lt = Mask(W, H, 2)
Lb = Mask(W, H, 2)
n_cells = int(W / 12.5)
fl = sans(15 * 2, 700)
for i in range(n_cells):
    x = i * 12.5 + 2
    fr = i / n_cells
    k = next(q for q in range(1, 9) if x < xs[q])
    ch = SEQ[int(fr * 346)]
    if (x - xs[k - 1]) / (xs[k] - xs[k - 1]) < READ[k]:
        Lt.text((x + 5, 400), ch, fl, "ms")
    else:
        Mr.rune(x, 388, ch, 8.0, 13.0, 1.5)
tiny = sans(17 * 2, 700)
hx_ = sans(15 * 2, 600)
PAPER = {1: "grey, inked out", 2: "manila", 3: "black", 4: "cream, inked blue", 5: "saffron", 6: "sage", 7: "blush", 8: "ivory"}
for k in range(1, 9):
    Lb.text((xs[k - 1] + 7, 436), "S%d" % k, tiny, "ls")
    m_, s_ = divmod(CH[k]["len"], 60)
    Lb.text((xs[k] - 6, 436), "%d:%02d" % (m_, s_), hx_, "rs")
    Lb.text((xs[k - 1] + 7, 464), CH[k]["paper"], hx_, "ls")
    if xs[k] - xs[k - 1] > 200:
        Lb.text((xs[k] - 6, 464), PAPER[k], hx_, "rs")
A, B, C_ = Mr.a(), Lt.a(), Lb.a()
for k in range(1, 9):
    x0, x1 = xs[k - 1], xs[k]
    c = hexc(CH[k]["ink"])
    img[:, x0:x1] = img[:, x0:x1] * (1 - A[:, x0:x1, None] * 0.75) + c * A[:, x0:x1, None] * 0.75
    img[:, x0:x1] = img[:, x0:x1] * (1 - B[:, x0:x1, None]) + c * B[:, x0:x1, None]
    img[:, x0:x1] = img[:, x0:x1] * (1 - C_[:, x0:x1, None]) + c * C_[:, x0:x1, None]
# Thin paper gap between chapters
for x in xs[1:-1]:
    img[:, x - 1:x + 1] = hexc("#0e0d10")
save(img, ST / "colour_script.png")
