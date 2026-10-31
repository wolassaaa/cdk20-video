"""HKBU SCIE1007 coursework science video. Style scout c1: flat graphic realism, one real protein running through a colour-block mosaic. Method only."""
from common import *

Y, M, B, K, P_, C = [hexrgb(h) for h in ("#D2FF00", "#FF1F9C", "#1B22FF", "#08080A", "#F2F0E6", "#22E6FF")]
Q = warp(load(), zoom=0.95, cx=935, cy=525, rot=-0.16, ox=760, oy=366)
n, m, ao, dep, conf = Q["normal"], Q["mask"], Q["ao"], Q["depth"], Q["conf"]
hard = (m > 0.5).astype(np.float32)
hard = gblur(hard, 0.6)
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))


def ldot(l):
    l = np.array(l, np.float32)
    return (n * (l / np.linalg.norm(l))).sum(-1)


key = ldot((-0.62, 0.62, 0.48))        # hard top-left sun, like a flat game render
back = ldot((0.85, -0.45, 0.10))
hv = np.array((-0.62, 0.62, 0.48), np.float32); hv = hv / np.linalg.norm(hv) + np.array((0, 0, 1.0), np.float32); hv /= np.linalg.norm(hv)
spec = np.clip((n * hv).sum(-1), 0, 1) ** 60
tone = np.clip(key * 0.5 + 0.55, 0, 1) * (0.25 + 0.75 * np.clip(ao * 1.25 - 0.2, 0, 1))


crease_t = float(np.percentile(ao[m > 0.5], 13))


def s(a, e=0.012):
    """Crisp threshold with a touch of AA."""
    return np.clip((a + e) / (2 * e), 0, 1)


def toon(shadow, mid, light, rim):
    # clean graphic read of the form: two lit tones, one flat shadow, ink only in the real creases
    o = np.ones((H, W, 3), np.float32) * mid
    o = comp(o, s(key - 0.60), light)
    o = comp(o, s(0.14 - key), shadow)
    o = comp(o, s(back - 0.50) * s(0.2 - key), rim)
    o = comp(o, s(crease_t - ao, 0.02), K)
    o = comp(o, s(spec - 0.80), P_)
    return o


def contour(bg, ink, f=170):
    v = np.sin((dep + (1 - ao) * 0.03) * f)
    w = 0.25 + 0.75 * np.clip(1 - tone * 1.4, 0, 1)
    o = np.ones((H, W, 3), np.float32) * bg
    return comp(o, s(v - (1 - w * 1.2), 0.1), ink)


def halftone(bg, ink, pitch=9, ang=0.5):
    u = xx * math.cos(ang) + yy * math.sin(ang)
    v = -xx * math.sin(ang) + yy * math.cos(ang)
    d = np.hypot((u / pitch) % 1 - 0.5, (v / pitch) % 1 - 0.5)
    r = 0.72 * np.sqrt(np.clip(1 - tone * 1.5, 0, 1))
    o = np.ones((H, W, 3), np.float32) * bg
    return comp(o, s(r - d, 0.05), ink)


def hatch(bg, ink, pitch=7, ang=-0.9):
    u = (xx * math.cos(ang) + yy * math.sin(ang)) / pitch
    t = np.abs(u % 1 - 0.5) * 2
    w = np.clip(1.1 - tone * 1.7, 0.02, 1)
    o = np.ones((H, W, 3), np.float32) * bg
    return comp(o, s(w - t, 0.08), ink)


T = 3  # gutter
panels = [
    ((0, 0, 330, 720), Y, None),
    ((330, 0, 830, 450), Y, toon(K, M, P_, B)),
    ((830, 0, 1280, 200), B, toon(K, C, P_, M)),
    ((830, 200, 1095, 450), P_, halftone(P_, K, pitch=7)),
    ((1095, 200, 1280, 450), M, toon(K, Y, P_, B)),
    ((330, 450, 640, 720), C, hatch(C, K, pitch=6)),
    ((640, 450, 1095, 720), B, toon(K, M, Y, C)),
    ((1095, 450, 1280, 720), K, None),
]

rgb = np.ones((H, W, 3), np.float32) * K
for (x0, y0, x1, y1), bg, tex in panels:
    p = np.zeros((H, W), np.float32)
    p[y0 + T:y1 - T, x0 + T:x1 - T] = 1
    if x0 == 0:
        p[y0 + T:y1 - T, 0:x1 - T] = 1
    rgb = comp(rgb, p, bg)
    if tex is not None:
        rgb = comp(rgb, p * hard, tex)

# Low confidence tail keeps its own treatment everywhere it appears: cut out, line only. Real pLDDT.
tail = (conf < 0.7) & (m > 0.5)
tl = gblur(tail.astype(np.float32), 0.7)
stripe = s(np.sin((xx + yy) * 0.9), 0.2)
panel_mask = np.ones((H, W), np.float32)
panel_mask[:, :330] = 0
panel_mask[450:, 1095:] = 0
rgb = comp(rgb, tl * panel_mask * stripe, K)

# wordmark: stretched block letters run the whole frame edge, protein bites into them
spr = type_sprite("CDK20", font(F + "impact.ttf", 330), sx=1.03, sy=1.0, pad=0)
sc = 716 / spr.width
spr = spr.resize((716, int(spr.height * sc * 1.28)), Image.LANCZOS)
rgb = paste_sprite(rgb, spr, 168, 360, K, rot=90)

# black silhouette of the protein keeps crossing into the wordmark panel as a magenta shadow block
lm = np.zeros((H, W), np.float32)
lm[3:717, :327] = 1
rgb = comp(rgb, lm * hard, toon(K, M, P_, B))

# stickers
mono = FX + "MartianMono.ttf"
mf = font(mono, 15)
lb = type_sprite(LABEL, font(F + "consolab.ttf", 25), pad=9)
box = Image.new("L", lb.size, 255)
rgb = paste_sprite(rgb, box, 1090 + 95, 512, P_) if False else rgb
tag = np.zeros((H, W), np.float32)
tag[654:698, 690:1078] = 1
rgb = comp(rgb, tag, K)
rgb = paste_sprite(rgb, lb, 884, 676, Y)

# real pLDDT barcode, 346 bars
_, conf_r, _ = read_pdb()
bars = np.zeros((H, W), np.float32)
x0, x1 = 1108, 1267
for i, c in enumerate(conf_r):
    x = x0 + (x1 - x0) * i / 345
    h = 18 + 96 * c
    bars[int(700 - h):700, int(x):int(x) + 1] = 1 if i % 2 == 0 else 0.8
rgb = comp(rgb, bars, Y)
num = type_sprite("346", font(F + "impact.ttf", 74), pad=2)
rgb = paste_sprite(rgb, num, 1165, 512, P_)
rgb = paste_sprite(rgb, type_sprite("RESIDUES", font(F + "consolab.ttf", 16), pad=1), 1188, 556, M)
for (x, y) in [(330, 450), (830, 200), (1095, 450), (640, 450), (830, 450), (1095, 200)]:
    c = np.zeros((H, W), np.float32)
    c[y - 9:y + 9, x - 2:x + 2] = 1
    c[y - 2:y + 2, x - 9:x + 9] = 1
    rgb = comp(rgb, c, P_)

# hazard strip on the top of the blue panel
hz = ((xx + yy) % 26 < 13).astype(np.float32)
strip = np.zeros((H, W), np.float32)
strip[3:17, 1040:1277] = 1
rgb = comp(rgb, strip, Y)
rgb = comp(rgb, strip * hz, K)
finish(rgb, "c1_marathon_graphic_realism.png")
