"""HKBU SCIE1007 coursework science video. d8 style test: a printed hand-drawn game manual found in a box. Open spread, ink line art of the real CDK20 surface, offset colour with halftone dots, and text in a made-up rune script that spells the real 346-letter sequence."""
from t import *

W, H = 1280, 720
S = 2
rng = np.random.default_rng(8)
seq = sequence()["seq"]
assert len(seq) == 346

PW, PH = W * S, H * S
INK = (28, 26, 34)
PAPER = (240, 229, 203)
# The spread is drawn flat, then the paper, print and scan damage go on top
im = Image.new("RGB", (PW, PH), PAPER)
d = ImageDraw.Draw(im)
MID = 620 * S  # spine
yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)


def W_(x):
    return int(x * S)


def wobble(pts, amp=0.7, seed=0):
    r = np.random.default_rng(seed)
    p = np.array(pts, np.float32)
    # resample then jitter with slow noise so the pen feels drawn
    seg = np.hypot(*(p[1:] - p[:-1]).T)
    n = np.maximum((seg / 6).astype(int), 1)
    out = []
    for i in range(len(p) - 1):
        for k in range(n[i]):
            out.append(p[i] + (p[i + 1] - p[i]) * k / n[i])
    out.append(p[-1])
    out = np.array(out)
    nz = np.cumsum(r.normal(0, 1, out.shape), 0)
    nz -= np.linspace(nz[0], nz[-1], len(nz))
    nz = np.clip(nz / max(np.abs(nz).max(), 1e-3), -1, 1)
    return [tuple(q) for q in out + nz * amp * S]


def pen(pts, w=2.0, fill=INK, seed=0, amp=0.8):
    d.line(wobble(pts, amp, seed), fill=fill, width=W_(w), joint="curve")


def box(x0, y0, x1, y1, w=2.0, seed=0, fill=None):
    if fill is not None:
        d.rectangle([W_(x0), W_(y0), W_(x1), W_(y1)], fill=fill)
    pen([(W_(x0), W_(y0)), (W_(x1), W_(y0)), (W_(x1), W_(y1)), (W_(x0), W_(y1)), (W_(x0), W_(y0))], w, seed=seed)


# ---- rune script: 20 amino acid letters, each a stem with a fixed tick pattern on a shared top bar ----
ALPHA = "ACDEFGHIKLMNPQRSTVWY"
R = {}
for i, a in enumerate(ALPHA):
    r = np.random.default_rng(1000 + i)
    R[a] = r.integers(0, 2, 7)


def rune(x, y, ch, h=13.0, w=9.0, col=INK, lw=1.6):
    """Bar on top, centre stem, six optional strokes. Own invention."""
    b = R[ch]
    L = W_(lw)
    X = lambda v: x + v * w * S
    Y = lambda v: y + v * h * S
    d.line([X(0), Y(0), X(1), Y(0)], fill=col, width=L)
    segs = [((0.5, 0), (0.5, 1)), ((0, 0), (0.5, 0.5)), ((1, 0), (0.5, 0.5)), ((0, 1), (0.5, 0.5)), ((1, 1), (0.5, 0.5)), ((0, 1), (1, 1)), ((0, 0.5), (1, 0.5))]
    for k, (p, q) in enumerate(segs):
        if b[k]:
            d.line([X(p[0]), Y(p[1]), X(q[0]), Y(q[1])], fill=col, width=L)


def rune_block(x, y, wchars, lines, start, h=13.0, w=9.0, gap=4.0, lh=24.0, col=INK):
    i = start
    for l in range(lines):
        cx = x
        n = 0
        while n < wchars:
            brk = (i * 7 + 3) % 6 == 0  # word gaps
            rune(W_(cx), W_(y + l * lh), seq[i % len(seq)], h, w, col)
            cx += w + gap + (8 if brk else 0)
            n += 2 if brk else 1
            i += 1
    return i


# ---- left page is a full flood of one dark blue ink, with a coarse screen so it still looks printed ----
d.rectangle([0, 0, MID, PH], fill=(32, 58, 118))
for j in range(0, PH, 12):
    for i in range(0, MID, 12):
        o = 6 if j % 24 else 0
        d.ellipse([i + o - 3, j - 3, i + o + 3, j + 3], fill=(44, 76, 142))

# ---- main illustration: real surface as ink over flat offset colour ----
ax, ay, aw, ah = 0, 90, 618, 630
Q = view(aw * S, ah * S, zoom=1.86, rot=-6, at=(0.515, 0.50), c=(0.5, 0.49))
Q2 = Q
m = Q["mask"]
mb = m > 0.5
key = lit(Q, (-0.55, 0.70, -0.45), 0.0)
ao = np.clip(Q["ao"], 0, 1)
tn = np.clip(key * 0.8 + 0.25, 0, 1) * (0.35 + 0.65 * ao)
e, gz, gn = edges(Q, dz=0.0032, dn=0.38)
# colour plates: three flat inks, each a halftone screen at its own angle, slightly off register
H_, W2 = m.shape
gy, gx = np.mgrid[0:H_, 0:W2].astype(np.float32)


def screen(val, ang, pitch):
    t = np.deg2rad(ang)
    u = gx * np.cos(t) + gy * np.sin(t)
    v = -gx * np.sin(t) + gy * np.cos(t)
    c = np.cos(u * 2 * np.pi / pitch) * np.cos(v * 2 * np.pi / pitch) * 0.5 + 0.5
    return c < val ** 0.75


ink_cyan = screen(np.clip(1.05 - tn * 1.25, 0, 0.92), 15, 8.0) & mb
tail = np.clip(0.70 - gauss(Q["conf"], 2), 0, 1) > 0.0  # real low confidence region
ink_mag = (screen(np.clip(1.1 - tn * 1.5, 0, 0.8), 75, 8.0) | tail) & mb & (tail | (tn < 0.46))
ink_yel = mb & (tail | True) & (tn > 0.20)
arr = np.asarray(im).astype(np.float32).copy()
ox, oy = W_(ax), W_(ay)
sl = arr[oy:oy + H_, ox:ox + W2]
key_line = gauss((m > 0.5).astype(np.float32), 5) > 0.06  # paper keyline, the old print trick that pops a figure off a flood
sl[key_line] = PAPER


def plate(mask, col, dx, dy, a=0.92):
    mk = np.roll(np.roll(mask, dy, 0), dx, 1)
    sl = arr[oy:oy + H_, ox:ox + W2]
    sl[mk] = sl[mk] * (1 - a) + (sl[mk] * np.array(col, np.float32) / 255) * a


plate(ink_yel, (255, 214, 92), 3, 2)
plate(ink_cyan, (64, 164, 196), -2, 1)
plate(ink_mag, (232, 84, 96), 2, -2)
# Line plate: thick outline, thinner creases
sil = gauss((m > 0.5).astype(np.float32), 2.4)
outline = (sil > 0.12) & (sil < 0.88)
inner = gauss(e.astype(np.float32), 0.9) > 0.32
sl = arr[oy:oy + H_, ox:ox + W2]
sl[(outline | (inner & mb))] = INK
# Hatch in deep shade, in pen
hatch = (((gx + gy * 0.8) % 11) < 2.4) & (tn < 0.19) & mb
sl[hatch] = INK
im = Image.fromarray(arr.astype(np.uint8))
d = ImageDraw.Draw(im)

# ---- left page furniture ----
tf = font("BOOKOSB.TTF", 112 * S)
d.text((W_(38) + 8, W_(2) + 7), "CDK20", font=tf, fill=(232, 84, 96))
d.text((W_(38), W_(2)), "CDK20", font=tf, fill=PAPER)
rune_block(494, 22, 9, 3, 0, 11, 6.5, 3.0, 19, col=PAPER)

# Callouts: a number in a wobbly circle and a thin line
def tag(n, x, y, tx, ty, seed):
    pen([(W_(x), W_(y)), (W_(tx), W_(ty))], 2.4, fill=PAPER, seed=seed)
    d.ellipse([W_(tx) - 7, W_(ty) - 7, W_(tx) + 7, W_(ty) + 7], fill=PAPER, outline=INK, width=2)
    r = 15
    d.ellipse([W_(x - r), W_(y - r), W_(x + r), W_(y + r)], fill=(255, 214, 92), outline=INK, width=W_(2.2))
    d.text((W_(x), W_(y)), n, font=font("BOOKOSB.TTF", 17 * S), fill=INK, anchor="mm")


tag("1", 54, 168, 170, 300, 2)
tag("2", 46, 660, 210, 560, 3)
tag("3", 578, 150, 452, 290, 4)

# ---- right page ----
RX = 648
d.rectangle([W_(RX), W_(26), W_(1244), W_(66)], fill=(44, 72, 110))
for i in range(30):
    rune(W_(RX + 16 + i * 14.5), W_(36), seq[60 + i], 15, 9.5, col=(240, 229, 203))


# backbone panels: the real C-alpha trace from three directions, as if hand drawn
xyz, plddt = ca()
xyz = xyz - xyz.mean(0)


def rot(a, b):
    a, b = np.deg2rad(a), np.deg2rad(b)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ Ry


panels = [(RX, 80, 188, 188, 20, 15), (RX + 200, 80, 188, 188, 140, 30), (RX + 400, 80, 188, 188, 260, -20)]
for pi, (x, y, w, h, a, b) in enumerate(panels):
    box(x, y, x + w, y + h, 2.2, seed=20 + pi, fill=(246, 238, 216))
    p = xyz @ rot(a, b).T
    k = 2.55
    sx, sy = W_(x + w / 2) + p[:, 0] * k * S, W_(y + h / 2) - p[:, 1] * k * S
    for i in range(len(p) - 1):
        low = plddt[i] < 0.7
        col = (232, 84, 96) if low else INK
        d.line([(sx[i], sy[i]), (sx[i + 1], sy[i + 1])], fill=col, width=W_(2.5 if not low else 2.2))
    rune(W_(x + 8), W_(y + 8), seq[pi * 40 + 3], 12, 8)
    rune(W_(x + 20), W_(y + 8), seq[pi * 40 + 4], 12, 8)

# Rune paragraphs: every mark on this page spells the real sequence in order
bk = (232, 84, 96)
next_i = rune_block(RX + 2, 286, 26, 6, 0)
d.rectangle([W_(RX), W_(434), W_(RX + 392), W_(652)], outline=INK, width=W_(2.2))
next_i = rune_block(RX + 12, 448, 26, 8, next_i)
# A side box with a key icon page: the lock diagram, drawn without any claim
box(RX + 404, 288, 1244, 652, 2.2, seed=40, fill=(226, 232, 214))
# Fold over key and lock: the frame of the story, hand drawn, from the shot outline of the real silhouette
kx, ky = RX + 498, 392
sm = view(320, 180, zoom=0.92)["mask"] > 0.5
sm = np.asarray(sm)
ys, xs = np.where(sm & ~(np.roll(sm, 1, 0) & np.roll(sm, -1, 0) & np.roll(sm, 1, 1) & np.roll(sm, -1, 1)))
for x_, y_ in zip(xs, ys):
    cx = W_(kx - 160 + x_ * 1.0)
    cy = W_(ky - 88 + y_ * 1.0)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=INK)
# key
keyp = [(RX + 432, 560), (RX + 492, 560)]
pen([(W_(a), W_(b)) for a, b in keyp], 4.2, seed=41)
d.ellipse([W_(RX + 412), W_(546), W_(RX + 440), W_(574)], outline=INK, width=W_(4))
pen([(W_(RX + 480), W_(560)), (W_(RX + 480), W_(572))], 4, seed=42)
pen([(W_(RX + 490), W_(560)), (W_(RX + 490), W_(574))], 4, seed=43)
d.polygon([(W_(RX + 508), W_(540)), (W_(RX + 508), W_(580)), (W_(RX + 548), W_(560))], outline=INK, fill=(255, 214, 92))
for j in range(3):
    pen([(W_(RX + 442 + j * 40), W_(610)), (W_(RX + 472 + j * 40), W_(610))], 2.2, seed=50 + j)
rune_block(RX + 420, 596, 11, 2, next_i, 11, 7.0, 3.5, 20)

# Label as a stuck-on printed slip so it stays perfectly legible
slip = Image.new("RGBA", (W_(372), W_(38)), (252, 247, 232, 255))
ds = ImageDraw.Draw(slip)
ds.rectangle([3, 3, W_(372) - 4, W_(38) - 4], outline=INK, width=W_(1.6))
ds.text((W_(186), W_(19)), LABEL, font=font("georgiab.ttf", 22 * S), fill=INK, anchor="mm")
slip = slip.rotate(-1.4, expand=True, resample=Image.BICUBIC)
im.paste(slip, (W_(224), W_(668)), slip)

# Pencil marks from a previous owner: only a ring and a question mark
pc = (64, 70, 84)
ring = [(W_(900 + 92 * np.cos(t) * (1 + 0.06 * np.sin(t * 3))), W_(174 + 78 * np.sin(t))) for t in np.linspace(0.3, 7.0, 90)]
ImageDraw.Draw(im).line(ring, fill=pc, width=W_(1.6), joint="curve")
ImageDraw.Draw(im).text((W_(1010), W_(92)), "?", font=font("Inkfree.ttf", 58 * S), fill=pc, anchor="mm")

# ---- to float, downsample, age ----
A = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
fib = fbm(H, W, 3, 3, 5)
blot = fbm(H, W, 90, 4, 9)
A *= (0.965 + 0.07 * fib[..., None])
A *= 1 - 0.13 * np.clip((blot - 0.56) * 6, 0, 1)[..., None] * hexc("#3c5a86")
# ink breakup: print sits on the paper grain
A = A + np.clip(0.5 - A, 0, 1) * (fib[..., None] > 0.70) * 0.35
# Fold, spine shading, one hard crease
xs = 620.0
spine = np.exp(-np.abs(xx - xs) / 34) * 0.42 + np.exp(-np.abs(xx - xs) / 5) * 0.46
A *= 1 - spine[..., None]
hl = np.exp(-((xx - xs - 42) / 22) ** 2) * 0.08
A = np.clip(A + hl[..., None], 0, 1)
cr = np.abs(yy - 360 - (xx - 300) * 0.015 - (fbm(H, W, 40, 2, 2) - 0.5) * 3) < 1.0

dk = A.mean(2) < 0.45
wear = (noise(H, W, 2, 12) > 0.42)
A = np.where((cr & wear)[..., None], A * 0.4 + hexc("#efe2c6") * 0.6, A)
cr2 = np.abs(xx - 950 - (yy - 300) * -0.02 - (fbm(H, W, 40, 2, 3) - 0.5) * 3) < 0.8
A = np.where((cr2 & wear & (A.mean(2) < 0.6))[..., None], hexc("#efe2c6"), A)
# Staple
for yy0 in (180, 540):
    A[yy0:yy0 + 42, 618:622] = hexc("#c8ccd0") * (0.8 + 0.4 * np.linspace(0, 1, 42))[:, None, None]
# Tilted on a dark desk
BG = gauss(fbm(H, W, 50, 3, 3), 1) * 0.10 + 0.05
yy2, xx2 = yy, xx
t = np.deg2rad(-2.1)
cx, cy = 640, 360
sc = 1.040
sx = cx + (np.cos(t) * (xx - cx) + np.sin(t) * (yy - cy)) * sc
sy = cy + (-np.sin(t) * (xx - cx) + np.cos(t) * (yy - cy)) * sc
pg = sample(np.ones((H, W), np.float32), sx, sy)
B = sample(A, sx, sy)
pg_s = gauss(np.roll(np.roll(pg, 12, 0), 9, 1), 12)
desk = ramp(BG, [(0, "#0e1014"), (0.2, "#262228")])
rgb = desk * (1 - pg_s[..., None] * 0.75)
rgb = rgb * (1 - pg[..., None]) + B * pg[..., None]
rgb *= (0.86 + 0.2 * np.clip(1.25 - np.hypot((xx - 500) / 900, (yy - 300) / 620), 0, 1))[..., None]
save(rgb, OUT / "d8_tunic_manual.png")
