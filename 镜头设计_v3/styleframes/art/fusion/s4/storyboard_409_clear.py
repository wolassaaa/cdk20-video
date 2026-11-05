"""HKBU SCIE1007 coursework science video: storyboard sketches for a clearer 4-09 (the director's 11-06 note: the small molecules and rings in version A
do not read; make it clear to everyone). Three directions, four beats each, drawn flat for a blind read before any 3D work:
K: the pocket is a keyhole, each design is a key whose handle is a small molecule; a gate tips the keys with a red warning group into a bin; the rest get two bars.
C: each design is a card with a molecule drawing; cards with a red warning group are crumpled into a bin; the rest get two bars.
S: ball-and-stick molecules ride a belt through a scanner arch; the arch flashes red on a warning group and a trapdoor drops it into a bin; the rest get two bars.
Run: python storyboard_409_clear.py <out dir>"""
import math
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
W, H = 1280, 720
BONE, INK, SOFT, RED, DARK, KLEIN, BLUE = (237, 235, 228), (17, 17, 19), (84, 84, 88), (232, 25, 15), (154, 14, 8), (0, 47, 167), (31, 59, 255)
WHITE = (250, 249, 245)
try:
    HAND = ImageFont.truetype("C:/Windows/Fonts/segoepr.ttf", 30)
    SANS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
except OSError:
    HAND = SANS = ImageFont.load_default()


def hexagon(d, cx, cy, r, col=INK, w=4, rot=30):
    pts = [(cx + r * math.cos(math.radians(rot + 60 * i)), cy + r * math.sin(math.radians(rot + 60 * i))) for i in range(7)]
    d.line(pts, fill=col, width=w, joint="curve")
    return pts


def molecule(d, cx, cy, r, subs=(0, 2), bad=None, col=INK, w=4):
    """A ring of six with side groups; bad is the index of the side group that carries the red warning blob."""
    pts = hexagon(d, cx, cy, r, col, w)
    for k, v in enumerate(subs):
        a = math.radians(30 + 60 * v)
        x0, y0 = pts[v]
        x1, y1 = x0 + 0.8 * r * math.cos(a), y0 + 0.8 * r * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=col, width=w)
        if bad == k:
            d.ellipse([x1 - 0.42 * r, y1 - 0.42 * r, x1 + 0.42 * r, y1 + 0.42 * r], fill=RED)
            warn(d, x1, y1 - 0.85 * r, 0.32 * r)


def warn(d, x, y, s):
    d.polygon([(x, y - s), (x + s * 1.1, y + s * 0.8), (x - s * 1.1, y + s * 0.8)], fill=RED, outline=DARK)
    d.line([(x, y - s * 0.4), (x, y + s * 0.25)], fill=WHITE, width=max(2, int(s * 0.22)))
    d.ellipse([x - s * 0.1, y + s * 0.42, x + s * 0.1, y + s * 0.62], fill=WHITE)


def key(d, cx, cy, s, bad=False, ang=0.0, subs=(1, 4)):
    """A key lying right-pointing from its handle at (cx, cy): the handle is a small molecule's ring."""
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda x, y: (cx + x * ca - y * sa, cy + x * sa + y * ca)
    shaft = [P(0.9 * s, -0.13 * s), P(3.2 * s, -0.13 * s), P(3.2 * s, 0.13 * s), P(0.9 * s, 0.13 * s)]
    d.polygon(shaft, fill=(200, 196, 186), outline=INK)
    teeth = [P(2.3 * s, 0.13 * s), P(2.3 * s, 0.5 * s), P(2.6 * s, 0.5 * s), P(2.6 * s, 0.3 * s), P(2.85 * s, 0.3 * s), P(2.85 * s, 0.55 * s), P(3.2 * s, 0.55 * s), P(3.2 * s, 0.13 * s)]
    d.polygon(teeth, fill=(200, 196, 186), outline=INK)
    d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(200, 196, 186), outline=INK, width=3)
    molecule(d, cx, cy, 0.55 * s, subs=subs, w=3)
    if bad:          # the warning group, on a short stalk off the handle so it reads at a glance
        x1, y1 = P(-1.35 * s, -0.75 * s)
        d.line([P(-0.8 * s, -0.45 * s), (x1, y1)], fill=INK, width=3)
        d.ellipse([x1 - 0.32 * s, y1 - 0.32 * s, x1 + 0.32 * s, y1 + 0.32 * s], fill=RED)
        warn(d, x1, y1 - 0.8 * s, 0.3 * s)


def cdk20(d, cx, cy, r):
    pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        rr = r * (1 + 0.08 * math.sin(5 * a) + 0.05 * math.sin(9 * a + 1))
        if -0.5 < a - 0.4 < 0.5:
            rr *= 0.72          # the pocket, a notch on the right
        pts.append((cx + rr * math.cos(a), cy - rr * math.sin(a)))
    d.polygon(pts, fill=KLEIN, outline=(0, 30, 110))


def keyhole(d, cx, cy, s, fill=WHITE):
    d.ellipse([cx - s, cy - 1.6 * s, cx + s, cy + 0.4 * s], fill=fill, outline=INK, width=3)
    d.polygon([(cx - 0.45 * s, cy), (cx + 0.45 * s, cy), (cx + 0.8 * s, cy + 2.2 * s), (cx - 0.8 * s, cy + 2.2 * s)], fill=fill, outline=INK)
    d.ellipse([cx - 0.55 * s, cy - 1.15 * s, cx + 0.55 * s, cy - 0.05 * s], fill=INK)
    d.polygon([(cx - 0.25 * s, cy - 0.3 * s), (cx + 0.25 * s, cy - 0.3 * s), (cx + 0.42 * s, cy + 1.8 * s), (cx - 0.42 * s, cy + 1.8 * s)], fill=INK)


def bin_(d, cx, cy, s):
    d.polygon([(cx - s, cy - s), (cx + s, cy - s), (cx + 0.78 * s, cy + s), (cx - 0.78 * s, cy + s)], fill=(190, 186, 176), outline=INK)
    for k in (-0.45, 0, 0.45):
        d.line([(cx + k * s, cy - 0.8 * s), (cx + 0.85 * k * s, cy + 0.85 * s)], fill=SOFT, width=3)
    d.rectangle([cx - 1.1 * s, cy - 1.15 * s, cx + 1.1 * s, cy - s], fill=SOFT)


def bars(d, x, y, v1, v2, h=110):
    """Two upright score bars with their icons under them: a pill (drug-like) and a flask (easy to make)."""
    for j, (v, icon) in enumerate(((v1, "pill"), (v2, "flask"))):
        bx = x + j * 34
        d.rectangle([bx, y - h, bx + 22, y], outline=SOFT, width=2)
        d.rectangle([bx, y - h * v, bx + 22, y], fill=BLUE if j == 0 else KLEIN)
        iy = y + 22
        if icon == "pill":
            d.rounded_rectangle([bx - 2, iy - 8, bx + 24, iy + 8], 8, fill=WHITE, outline=INK, width=2)
            d.rounded_rectangle([bx - 2, iy - 8, bx + 11, iy + 8], 8, fill=RED)
        else:
            d.polygon([(bx + 7, iy - 12), (bx + 15, iy - 12), (bx + 15, iy - 3), (bx + 24, iy + 12), (bx - 2, iy + 12), (bx + 7, iy - 3)], fill=WHITE, outline=INK)


def screen(d, x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], 18, fill=(10, 14, 40), outline=(120, 120, 124), width=8)
    for i in range(4):
        for j in range(3):
            cx, cy = x0 + 40 + i * (x1 - x0 - 80) / 3, y0 + 40 + j * (y1 - y0 - 80) / 2
            d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], outline=BLUE, width=4)


def note(d, x, y, s, col=DARK):
    d.text((x, y), s, font=HAND, fill=col)


def panel():
    im = Image.new("RGB", (W, H), BONE)
    return im, ImageDraw.Draw(im)


def p_pocket(kind):
    im, d = panel()
    cdk20(d, 380, 380, 210)
    if kind == "K":
        keyhole(d, 900, 300, 80)
        d.line([(560, 340), (800, 300)], fill=SOFT, width=2)
        d.ellipse([948, 262, 978, 292], fill=RED)
        note(d, 820, 520, "the pocket's shape")
        note(d, 990, 240, "the hinge")
    else:
        d.ellipse([560, 300, 640, 380], outline=RED, width=6)
        note(d, 660, 300, "the hinge")
        note(d, 620, 520, "the pocket's shape")
    return im


def k_rule():
    im, d = panel()
    keyhole(d, 640, 300, 140)
    key(d, 300, 330, 70, ang=-0.05)
    d.ellipse([700, 200, 740, 240], fill=RED)
    d.line([(520, 330), (705, 225)], fill=SOFT, width=2)
    note(d, 760, 160, "every key must grip here")
    return im


def k_toss():
    im, d = panel()
    screen(d, 40, 160, 300, 420)
    d.rounded_rectangle([300, 450, 1240, 500], 20, fill=(150, 150, 154))
    for i in range(10):
        d.ellipse([320 + i * 92, 470, 340 + i * 92, 490], fill=SOFT)
    d.rectangle([700, 220, 720, 450], fill=SOFT)
    d.rectangle([860, 220, 880, 450], fill=SOFT)
    d.rectangle([700, 200, 880, 230], fill=SOFT)
    warn(d, 790, 170, 34)
    key(d, 400, 410, 34)
    key(d, 560, 410, 34, bad=True)
    key(d, 1020, 410, 34)
    key(d, 1140, 600, 34, bad=True, ang=0.9)
    bin_(d, 1090, 640, 70)
    note(d, 340, 80, "out: reactive or possibly toxic groups")
    return im


def k_score():
    im, d = panel()
    for i, (v1, v2) in enumerate(((0.8, 0.6), (0.5, 0.9), (0.9, 0.7), (0.6, 0.4))):
        x = 140 + i * 280
        key(d, x, 470, 40, ang=-math.pi / 2)
        bars(d, x + 60, 470, v1, v2)
    bin_(d, 1180, 600, 60)
    note(d, 300, 80, "scored: drug-like? easy to make?")
    return im


def c_deal():
    im, d = panel()
    screen(d, 40, 160, 300, 420)
    for i in range(5):
        x, y = 380 + i * 170, 220 + (i % 2) * 120
        d.rectangle([x, y, x + 140, y + 180], fill=WHITE, outline=INK, width=2)
        molecule(d, x + 70, y + 90, 32, subs=((0, 3), (1, 4), (2,), (0, 2, 4), (5,))[i], bad=0 if i in (1, 3) else None)
    return im


def c_toss():
    im, d = panel()
    for i in range(3):
        x, y = 260 + i * 200, 260
        d.rectangle([x, y, x + 140, y + 180], fill=WHITE, outline=INK, width=2)
        molecule(d, x + 70, y + 90, 32, subs=((0, 3), (2,), (5,))[i])
    d.ellipse([920, 300, 1040, 400], fill=WHITE, outline=INK, width=2)          # a crumpled card
    d.line([(940, 320), (1010, 380), (960, 390), (1020, 330)], fill=SOFT, width=2)
    warn(d, 985, 290, 22)
    bin_(d, 1060, 560, 80)
    note(d, 260, 80, "out: reactive or possibly toxic groups")
    return im


def c_score():
    im, d = panel()
    for i, (v1, v2) in enumerate(((0.8, 0.6), (0.5, 0.9), (0.9, 0.7))):
        x, y = 200 + i * 320, 260
        d.rectangle([x, y, x + 160, y + 200], fill=WHITE, outline=INK, width=2)
        molecule(d, x + 80, y + 100, 36, subs=((0, 3), (2,), (5,))[i])
        bars(d, x + 190, y + 200, v1, v2)
    note(d, 260, 80, "scored: drug-like? easy to make?")
    return im


def ball_mol(d, cx, cy, r, bad=False):
    pts = [(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    for i in range(6):
        d.line([pts[i], pts[(i + 1) % 6]], fill=SOFT, width=5)
    for p in pts:
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=WHITE, outline=INK)
    e = (pts[0][0] + 0.8 * r, pts[0][1] + 0.45 * r)
    d.line([pts[0], e], fill=SOFT, width=5)
    if bad:
        d.ellipse([e[0] - 14, e[1] - 14, e[0] + 14, e[1] + 14], fill=RED)
    else:
        d.ellipse([e[0] - 9, e[1] - 9, e[0] + 9, e[1] + 9], fill=WHITE, outline=INK)


def s_belt(flash):
    im, d = panel()
    d.rounded_rectangle([40, 460, 1240, 510], 20, fill=(150, 150, 154))
    d.rounded_rectangle([560, 180, 760, 470], 30, outline=RED if flash else SOFT, width=26)
    for i, b in enumerate((False, True, False, False)):
        x = 160 + i * 330
        if flash and i == 1:
            continue
        ball_mol(d, x, 400, 40, bad=b)
    if flash:
        ball_mol(d, 660, 560, 40, bad=True)
        bin_(d, 660, 640, 60)
        warn(d, 660, 140, 30)
        note(d, 800, 160, "out: reactive or possibly toxic groups")
    else:
        note(d, 800, 160, "every design goes through")
    return im


def s_score():
    im, d = panel()
    d.rounded_rectangle([40, 460, 1240, 510], 20, fill=(150, 150, 154))
    for i, (v1, v2) in enumerate(((0.8, 0.6), (0.5, 0.9), (0.9, 0.7))):
        x = 220 + i * 360
        ball_mol(d, x, 400, 40)
        bars(d, x + 70, 450, v1, v2)
    note(d, 260, 80, "scored: drug-like? easy to make?")
    return im


def sheet(name, ims):
    s = Image.new("RGB", (2 * W, 2 * H), (255, 255, 255))
    for i, im in enumerate(ims):
        s.paste(im, ((i % 2) * W, (i // 2) * H))
    s.save("%s/sb409_%s.png" % (OUT, name))


sheet("K", [p_pocket("K"), k_rule(), k_toss(), k_score()])
sheet("C", [p_pocket("C"), c_deal(), c_toss(), c_score()])
sheet("S", [p_pocket("S"), s_belt(False), s_belt(True), s_score()])
print("ok")
