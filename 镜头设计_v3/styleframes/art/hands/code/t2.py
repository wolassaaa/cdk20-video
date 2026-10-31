"""HKBU SCIE1007 coursework science video. Hands T2: a seated person speaking, side-back, in a grey world. The hand is real: one frame of our phone clip, kept by the skin channel, and it is the only thing in focus.
The body is an out-of-focus grey placeholder until the members film. A real clip goes through grey_world.grade_frame() instead. Question in Instrument Serif 56 px, in two furrows. No gold yet: gold does not start until S4."""
from hk import *
from phone import cut, place, over

LINES = ["How can computer-aided methods help scientists", "find and assess potential cancer drug candidates?"]


def smooth(pts, n=14):
    p = np.array(pts, np.float32)
    p = np.vstack([p[-1], p, p[0], p[1]])
    out = []
    for i in range(1, len(p) - 2):
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3))
    return [tuple(q) for q in np.vstack(out)]


def ell(cx, cy, rx, ry, a=0):
    c, s = math.cos(a), math.sin(a)
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c) for t in np.linspace(0, 6.28, 64)]


xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
rgb, _ = ash(None, tone=0.46, seed=37, light=0.8)
pool = np.exp(-(((xx - 760) / 900) ** 2 + ((yy - 380) / 620) ** 2))[..., None]
rgb = rgb * (0.56 + 0.70 * pool)

BL = 15
head = gblur(poly(ell(1440, 300, 150, 186, -0.14)), BL)
hair = gblur(poly(smooth([(1300, 200), (1420, 124), (1560, 160), (1610, 300), (1590, 430), (1520, 492), (1450, 470), (1420, 390), (1398, 300), (1320, 262)])), BL)
neck = gblur(poly(smooth([(1360, 440), (1520, 450), (1560, 620), (1320, 620)], 8)), BL)
torso = gblur(poly(smooth([(1000, 1180), (1050, 790), (1150, 640), (1320, 570), (1540, 560), (1760, 650), (1900, 820), (1980, 1180)], 12)), BL + 3)
arm = gblur(poly(smooth([(1140, 650), (1210, 760), (1120, 950), (1000, 960), (800, 760), (770, 680), (830, 640), (1000, 780), (1040, 730)], 10)), BL)

body = np.maximum(torso, arm)
fold = gblur(vnoise(W, H, 120, 6, 3), 8)
lit = np.clip((1600 - xx) / 800, 0, 1)
shade = 0.10 + 0.20 * lit * np.clip(0.3 + (fold - 0.35) * 2.6, 0, 1.2)
rgb = comp(rgb, body, np.stack([shade, shade, shade * 1.02], -1))

skin_col = SKIN[1] * 0.92
rgb = comp(rgb, neck, skin_col * (0.34 + 0.46 * np.clip((1470 - xx) / 150, 0, 1))[..., None])
rgb = comp(rgb, head, skin_col * (0.40 + 0.46 * np.clip((1400 - xx) / 110, 0, 1))[..., None])
hc = 0.035 + 0.05 * vnoise(W, H, 40, 8, 3) * np.clip((1560 - xx) / 240, 0, 1)
rgb = comp(rgb, hair, np.stack([hc, hc, hc * 1.03], -1))

# photo grain over the figure, so it lives in the same air as the wall
g = gblur(vnoise(W, H, 3, 77, 2), 0.6)
rgb = rgb * (0.94 + 0.12 * g)[..., None]

a, p = cut(690, "Left")
h1 = place(a, p, 0, (850, 742), 128, 1.32)
rgb = over(rgb, h1, shadow=0.0)
# the wrist goes into the sleeve, which is out of focus like the rest of the body
cuff = gblur(poly(smooth([(806, 676), (930, 660), (1090, 760), (1120, 980), (900, 1000), (706, 806)], 10)), BL)
cs = 0.10 + 0.20 * np.clip((1600 - xx) / 800, 0, 1) * np.clip(0.3 + (fold - 0.35) * 2.6, 0, 1.2)
rgb = comp(rgb, cuff, np.stack([cs, cs, cs * 1.02], -1))

f = font(SERIF, 56)
d = ImageDraw.Draw(Image.new("L", (8, 8)))
fur = np.zeros((H, W), np.float32)
txt = np.zeros((H, W), np.float32)
for i, l in enumerate(LINES):
    tw = d.textlength(l, font=f)
    y = 88 + i * 98
    im = Image.new("L", (W * 2, H * 2), 0)
    ImageDraw.Draw(im).rounded_rectangle((36 * 2, (y - 45) * 2, (64 + tw + 56) * 2, (y + 45) * 2), 90, fill=255)
    fur = np.maximum(fur, np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255)
    txt = np.maximum(txt, layer(sprite_text(l, f, pad=8), 76, y - 42))


def streak(cell, seed, stretch):
    n_ = vnoise(W // stretch + 2, H, cell, seed, 3)
    return np.asarray(Image.fromarray(n_).resize((W, H), Image.BICUBIC), np.float32)


edge = (streak(9, 12, 14) - 0.5) * 1.15 + (streak(4, 14, 22) - 0.5) * 0.55
fm = np.clip((gblur(fur, 3.0) + edge * np.clip(gblur(fur, 14) * 2.6, 0, 1) - 0.44) * 4.2, 0, 1)
fm = gblur(fm, 0.8)
rgb = rgb * (1 - gblur(fur, 16)[..., None] * 0.22)
rgb = comp(rgb, fm, np.array([0.016, 0.016, 0.018], np.float32))
rgb = comp(rgb, gblur(txt, 0.45), np.array([0.92, 0.92, 0.92], np.float32))
rgb = vignette(rgb, 0.38)
save(rgb, "T2.png")
