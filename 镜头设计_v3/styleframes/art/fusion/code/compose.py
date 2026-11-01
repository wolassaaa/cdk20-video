"""HKBU SCIE1007 coursework science video. Fusion direction: type, leader lines, evidence marks and the one small cell view over the Blender layers, then the colour script.

Run: python compose.py [f1 f2 ... colour]
Everything is drawn at 2x and reduced, so a 2 px line stays a clean 2 px line. On-screen words are copied from 06_科学优先简报.md. The only number outside that list is the 6,000 tick on F5, taken from the 001 line.
Fonts (Google Fonts, SIL OFL): Instrument Serif, Inter Tight. File copies live in S1/v2/_code/s110/fonts/.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
ROOT = HERE + "../"
WORK, STILLS = ROOT + "_work/", ROOT + "stills/"
FONTS = HERE + "../../../S1/v2/_code/s110/fonts/"
SS = 2

INK = (17, 17, 19, 255)
SOFT = (84, 84, 88, 255)
RED = (232, 25, 15, 255)
DARK = (154, 14, 8, 255)
KLEIN = (0, 47, 167, 255)
BONE = (237, 235, 228, 255)
WHITE = (255, 255, 255, 255)


def serif(size, italic=False):
    return ImageFont.truetype(FONTS + ("InstrumentSerif-Italic.ttf" if italic else "InstrumentSerif-Regular.ttf"), size * SS)


def sans(size, weight=500):
    f = ImageFont.truetype(FONTS + "InterTight.ttf", size * SS)
    f.set_variation_by_axes([weight])
    return f


class Plate:
    def __init__(self, name):
        self.base = Image.open(WORK + name).convert("RGBA") if name else Image.new("RGBA", (1920, 1080), BONE)
        self.ov = Image.new("RGBA", (1920 * SS, 1080 * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.ov)

    def text(self, xy, s, font, fill=INK, anchor="ls", spacing=None):
        x, y = xy
        self.d.text((x * SS, y * SS), s, font=font, fill=fill, anchor=anchor)

    def bbox(self, xy, s, font, anchor="ls"):
        b = self.d.textbbox((xy[0] * SS, xy[1] * SS), s, font=font, anchor=anchor)
        return [v / SS for v in b]

    def line(self, a, b, fill=INK, w=2.0):
        self.d.line([a[0] * SS, a[1] * SS, b[0] * SS, b[1] * SS], fill=fill, width=int(round(w * SS)))

    def poly(self, pts, fill=INK, w=2.0):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=int(round(w * SS)), joint="curve")

    def dot(self, xy, r=5, fill=INK, outline=None):
        x, y = xy
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill, outline=outline, width=int(1.5 * SS))

    def rect(self, box, fill=INK):
        self.d.rectangle([v * SS for v in box], fill=fill)

    def leader(self, tip, knee, end=None, fill=INK, w=2.0, r=6, on_colour=False):
        """Textbook leader line: a dot on the thing, a thin line to the word. on_colour: the dot sits on a coloured object, so it goes bone with a dark ring."""
        pts = [tip, knee] + ([end] if end else [])
        self.poly(pts, fill, w)
        self.dot(tip, r, BONE if on_colour else fill, INK if on_colour else None)

    def dashed_circle(self, c, r, fill=INK, w=2.5, n=14, duty=0.55):
        x, y = c
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + duty) / n
            self.d.arc([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], math.degrees(a0), math.degrees(a1), fill=fill, width=int(round(w * SS)))

    def dashed_line(self, a, b, fill=INK, w=2.5, on=12, off=9):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = 0
        while t < L:
            e = min(L, t + on)
            self.line((a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e), fill, w)
            t += on + off

    def evidence(self, kind, x, y, s, size=30, fill=INK):
        """The four kinds of evidence differ by mark shape, not colour: solid square, dashed circle, open diamond, hatched square."""
        r = size * 0.5
        cy = y - size * 0.36
        cx = x + r
        if kind == "measured":
            self.rect([cx - r, cy - r, cx + r, cy + r], fill)
        elif kind == "predicted":
            self.dashed_circle((cx, cy), r, fill, 2.5, 10)
        elif kind == "docking":
            self.poly([(cx, cy - r * 1.15), (cx + r * 1.15, cy), (cx, cy + r * 1.15), (cx - r * 1.15, cy), (cx, cy - r * 1.15)], fill, 2.5)
        elif kind == "schematic":
            self.poly([(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r), (cx - r, cy - r)], fill, 2.5)
            for k in (-1, 0, 1):
                o = k * r * 0.7
                self.line((max(cx - r, cx - r + o), min(cy + r, cy + r + o)), (min(cx + r, cx + r + o), max(cy - r, cy - r + o)), fill, 2)
        self.text((x + size + 14, y), s, sans(size, 600), fill)

    def mini_road(self, x, y, lit, step=46, fill=RED):
        """Six stations, no words. lit counts how many stations the line has reached."""
        pts = [x + i * step for i in range(6)]
        self.dashed_line((pts[0], y), (pts[5], y), SOFT, 2.5, 6, 6)
        if lit:
            self.line((pts[0] - 16, y), (pts[lit - 1], y), fill, 6)
        for i, p in enumerate(pts):
            if i < lit:
                self.dot((p, y), 9, INK)
            else:
                self.dot((p, y), 8, BONE, SOFT)

    def multiply(self, draw):
        """Pale flat shapes that sit under everything: painted at 2x on white, reduced, multiplied onto the render, so real shadows stay."""
        im = Image.new("RGB", (1920 * SS, 1080 * SS), (255, 255, 255))
        draw(ImageDraw.Draw(im))
        a = np.asarray(im.resize((1920, 1080), Image.LANCZOS)).astype(np.float32) / 255
        b = np.asarray(self.base.convert("RGB")).astype(np.float32) / 255
        self.base = Image.fromarray((np.clip(a * b, 0, 1) * 255 + 0.5).astype(np.uint8)).convert("RGBA")

    def clipped(self, im, cx, cy, r):
        """Paste a 2x RGBA layer, cut to a circle. Nothing from the cell view leaves the lens."""
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=255)
        a = np.asarray(im).astype(np.float32)
        a[..., 3] *= np.asarray(m).astype(np.float32) / 255
        self.ov.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"))

    def paste(self, im, xy):
        self.ov.alpha_composite(im.resize((im.width * SS, im.height * SS), Image.LANCZOS), (xy[0] * SS, xy[1] * SS))

    def save(self, name):
        a = np.asarray(self.ov).astype(np.float32) / 255
        a[..., :3] *= a[..., 3:4]
        h, w = a.shape[:2]
        a = a.reshape(h // SS, SS, w // SS, SS, 4).mean((1, 3))         # plain box reduction of premultiplied colour
        b = np.asarray(self.base).astype(np.float32) / 255
        out = b[..., :3] * (1 - a[..., 3:4]) + a[..., :3]
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILLS + name)
        print("saved", name)


CELL, NUCLEUS = (221, 217, 206, 255), (188, 183, 170, 255)
MOL = (226, 222, 212)


def soft(pts, n=2):
    """Corner cutting: a plain polygon with its corners rounded."""
    for _ in range(n):
        q = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            q += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        pts = q
    return pts


def cells(cx, cy, R, gap=6.0):
    """Twelve flat liver cells: the hexagon tiling centred on a corner gives rings of 3, 3 and 6 cells around the lens centre. Schematic, not to scale."""
    im = Image.new("RGBA", (1920 * SS, 1080 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = math.sqrt(3) * R
    centres = []
    for j in range(-4, 5):
        for i in range(-4, 5):
            x = (i + (0.5 if j % 2 else 0)) * w
            y = j * 1.5 * R + R                         # a tile corner lands on the lens centre
            centres.append((math.hypot(x, y), x, y))
    centres.sort()
    for _, x, y in centres[:12]:
        hexa = [(cx + x + (R - gap / 1.7) * math.sin(k * math.pi / 3), cy + y + (R - gap / 1.7) * math.cos(k * math.pi / 3)) for k in range(6)]
        d.polygon([(a * SS, b * SS) for a, b in soft(hexa)], fill=CELL)
        n = R * 0.27
        d.ellipse([(cx + x - n) * SS, (cy + y - n) * SS, (cx + x + n) * SS, (cy + y + n) * SS], fill=NUCLEUS)
    return im


def tangents(a, ra, b, rb):
    """The two outer tangent segments between circles a and b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    base, off = math.atan2(dy, dx), math.acos((ra - rb) / L)
    out = []
    for sgn in (1, -1):
        t = base + sgn * off
        out.append(((a[0] + ra * math.cos(t), a[1] + ra * math.sin(t)), (b[0] + rb * math.cos(t), b[1] + rb * math.sin(t))))
    return out


def f1():
    p = Plate("r1.png")
    p.text((96, 460), "1,412", serif(250), RED)
    p.text((104, 570), "deaths in Hong Kong, 2022", sans(50, 500))
    p.leader((1640, 352), (1640, 196), (1696, 196), SOFT)
    p.text((1708, 209), "liver", sans(40, 600))
    p.leader((1262, 716), (1262, 860), (1296, 860), RED)
    p.text((1308, 873), "portal vein", sans(40, 600), DARK)
    p.leader((1184, 296), (1240, 110), (1300, 110), KLEIN)
    p.text((1310, 123), "hepatic veins", sans(40, 600), KLEIN)
    p.text((96, 1012), "HKCaR 2022 · BodyParts3D, DBCLS, CC BY 4.0", sans(26, 500), SOFT)
    # the one cell view: a small ring on the right lobe, away from the vessel trunks, opened in the lens. Only the lens is schematic, its tag touches the rim
    ring, rr, lc, lr = (1610, 432), 30, (1720, 770), 150
    for u, v in tangents(ring, rr, lc, lr):
        p.line(u, v, INK, 1.5)
    p.d.ellipse([(ring[0] - rr) * SS, (ring[1] - rr) * SS, (ring[0] + rr) * SS, (ring[1] + rr) * SS], outline=INK, width=int(2.5 * SS))
    p.clipped(cells(lc[0], lc[1], 55), lc[0], lc[1], lr - 4)
    p.line((lc[0], lc[1] + lr + 3), (lc[0], 958), INK, 2)
    p.evidence("schematic", 1604, 1006, "schematic", 36)
    p.save("F1.png")


def f2():
    p = Plate("r2.png")
    # crop marks at all four corners of the print: the phone clip lands inside them, the grey shape goes when real footage arrives
    x0, y0, x1, y1 = 124, 112, 828, 968
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        p.line((x, y), (x + dx * 44, y), BONE, 3)
        p.line((x, y), (x, y + dy * 44), BONE, 3)
    q = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
    for i, s in enumerate(q):
        p.text((960, 336 + i * 92), s, serif(84))
    p.save("F2.png")


def f3():
    p = Plate("r3.png")

    def cell_view(d):
        # a faint cell edge, a double line, and seven flat small shapes tucked inside its top-left curve. The one cell view of this frame
        for k in (0, 20):
            e = [960 - (1130 - k), 540 - (640 - k), 960 + (1130 - k), 540 + (640 - k)]
            d.ellipse([v * SS for v in e], outline=(219, 215, 204), width=int(4 * SS))
        for x, y, r, L, ang in ((118, 322, 20, 0, 0), (196, 236, 17, 12, 0.5), (300, 176, 23, 0, 0), (402, 104, 16, 13, -0.4), (262, 318, 15, 11, 2.2), (392, 250, 19, 0, 0), (512, 136, 17, 0, 0)):
            ca, sa = math.cos(ang) * L, math.sin(ang) * L
            d.line([(x - ca) * SS, (y - sa) * SS, (x + ca) * SS, (y + sa) * SS], fill=MOL, width=int(2 * r * SS))
            for u, v in ((x - ca, y - sa), (x + ca, y + sa)):
                d.ellipse([(u - r) * SS, (v - r) * SS, (u + r) * SS, (v + r) * SS], fill=MOL)
    p.multiply(cell_view)
    # locks at 160 px per unit
    p.leader((640, 330), (640, 150), (700, 150), KLEIN, on_colour=True)
    p.text((710, 164), "target (a protein)", sans(44, 600), KLEIN)
    p.leader((130, 610), (130, 900), (190, 900), DARK, on_colour=True)
    p.text((200, 914), "candidate (a small molecule)", sans(44, 600), DARK)
    # the key that fits
    ox, oy = 640, 556
    p.dot((ox, oy), 42, BONE, None)
    p.poly([(ox - 24, oy + 2), (ox - 6, oy + 22), (ox + 26, oy - 22)], INK, 8)
    # the refused key
    cx, cy = 1412, 556
    p.dot((cx, cy), 42, BONE, None)
    for s in (1, -1):
        p.line((cx - 24, cy - 24 * s), (cx + 24, cy + 24 * s), INK, 8)
    p.leader((cx, cy - 44), (cx, 260), None, INK)
    p.text((cx, 240), "selectivity", sans(52, 700), INK, "ms")
    p.evidence("schematic", 1320, 1000, "schematic", 36)
    p.save("F3.png")


def f4():
    p = Plate("r4.png")
    tip = (1331, 451)
    p.leader(tip, (1440, 400), (1470, 400), RED, on_colour=True)
    p.text((1480, 430), "floppy tail", serif(104), RED)
    p.text((1484, 500), "low confidence", sans(44, 600), DARK)
    # legend: words only, ribbon against beads, so it reads without colour too
    x, y = 1484, 700
    p.rect([x, y - 16, x + 92, y + 16], KLEIN)
    p.text((x + 118, y + 14), "more confident", sans(38, 500))
    for i in range(4):
        p.dot((x + 13 + i * 22, y + 73), 11, RED)
    p.text((x + 118, y + 88), "less confident", sans(38, 500))
    p.evidence("predicted", 96, 1012, "AlphaFold DB v6 · predicted", 30)
    p.save("F4.png")


def pocket(cx, cy, r):
    """Our re-docked 048 in the pale pocket, cropped square round the ligand. Returns a 2x layer."""
    po = Image.open(WORK + "pose_048_pale.png").convert("RGBA")
    li = Image.open(WORK + "pose_048_redlig.png").convert("RGBA")
    x0, y0, x1, y1 = li.getbbox()
    side = max(x1 - x0, y1 - y0) / 0.76
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box = (round(mx - side / 2), round(my - side / 2), round(mx + side / 2), round(my + side / 2))
    im = po.crop(box)
    im.alpha_composite(li.crop(box))
    d = round(2 * r * SS)
    im = im.resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (1920 * SS, 1080 * SS), (0, 0, 0, 0))
    out.paste(im, (round((cx - r) * SS), round((cy - r) * SS)))
    return out


def f5():
    p = Plate("r5.png")
    x0, s = 180, 1440 / 6000                       # px at 0 nM, px per nM, same on both rows
    yA, yB = 540, 775
    tx = x0 + 6000 * s
    p.text((x0, 150), "Enzyme IC50", serif(96))
    p.text((x0, 470), "001 > 6,000 nM", sans(58, 600), KLEIN)
    p.text((x0, 690), "048 = 33.4 ± 22.6 nM", sans(58, 700), RED)
    # 6,000 is a floor for 001: the tick marks it, the tube runs on out of frame. The same tick drops through the 048 row, so both rows visibly share one scale
    p.line((tx, yA - 62), (tx, yA + 62), INK, 3)
    p.dashed_line((tx, yA + 70), (tx, yB + 48), SOFT, 2, 8, 6)
    p.text((tx, yA - 74), "6,000", sans(36, 600), INK, "ms")
    for cx in (1704, 1766, 1828):
        p.poly([(cx - 14, yA - 22), (cx + 10, yA), (cx - 14, yA + 22)], WHITE, 6)
    p.text((x0 + 30, yB + 17), "Just this much cuts the enzyme's activity in half.", sans(50, 500))
    # MEASURED holds both rows in one bracket
    bx = 148
    p.poly([(x0 - 10, yA - 44), (bx, yA - 44), (bx, 1001), (x0 - 6, 1001)], INK, 2)
    p.line((x0 - 10, yB - 40), (bx, yB - 40), INK, 2)
    p.evidence("measured", x0, 1012, "MEASURED · Ren 2023, Fig. 9A", 30)
    # the pocket with 048 inside, the docking tag on a line to the rim
    c, r = (1640, 222), 190
    p.clipped(pocket(c[0], c[1], r - 5), c[0], c[1], r - 5)
    p.evidence("docking", 1052, 236, "OUR RE-DOCKING", 36)
    p.line((1412, 223), (c[0] - r - 2, 223), INK, 2)
    p.save("F5.png")


def f6():
    p = Plate("r6.png")
    st = [228, 512, 790, 1072, 1395, 1704]
    y = 516
    D = 60
    # stations not reached: dashed ring, no collar
    for x in st[4:]:
        p.dashed_circle((x, y), 62, SOFT, 3, 16)
    # how far 048 got
    fx = st[3]
    p.line((fx, y - 62), (fx, 300 + D), RED, 3)
    p.dot((fx, 300 + D), 6, RED)
    p.text((fx, 270 + D), "048", serif(170), RED, "ms")
    names = [["Target"], ["Hit"], ["Improve"], ["Cells & animals"], ["Clinical trials", "1-2-3"], ["Approval"]]
    for x, n in zip(st, names):
        for i, s in enumerate(n):
            p.text((x, 610 + D + i * 46), s, sans(40, 600), INK, "ms")
    p.text((st[3], 720 + D), "cells: first tests", sans(36, 500), DARK, "ms")
    p.text((st[3], 772 + D), "animals: not reported", sans(36, 500), SOFT, "ms")
    b = p.bbox((st[3], 772 + D), "animals: not reported", sans(36, 500), "ms")
    p.dashed_line((b[0], 786 + D), (b[2], 786 + D), SOFT, 2, 8, 6)
    for x in st[4:]:
        p.text((x, 772 + D), "not reported", sans(36, 500), SOFT, "ms")
        b = p.bbox((x, 772 + D), "not reported", sans(36, 500), "ms")
        p.dashed_line((b[0], 786 + D), (b[2], 786 + D), SOFT, 2, 8, 6)
    p.save("F6.png")


def shares(path):
    """Share of the frame that is red, blue, or dark (ink and the person), measured on the finished still. The rest is bone."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 120) & (g < 90) & (b < 90)
    blue = (b > 110) & (r < 80)
    dark = (r < 190) & (g > 90) & ~red & ~blue | ((r < 70) & (b < 80))
    return red.mean(), blue.mean(), dark.mean()


def colour():
    """S1 to S8, width by running time. Top: the object that stands for the section, without its type. Bottom: colour shares measured from the finished frame. S7 and S8 borrow F6 and F2 until they have their own frames."""
    secs = [("S1", 141, "r1", "F1", 0.62), ("S2", 142, "r2", "F2", 0.24), ("S3", 129, "r3", "F3", 0.15),
            ("S4", 213, "r4", "F4", 0.34), ("S5", 139, "r5", "F5", 0.17), ("S6", 151, "r6", "F6", 0.32),
            ("S7", 49, "r6", "F6", 0.73), ("S8", 99, "r2", "F2", 0.23)]
    tot = sum(s[1] for s in secs)
    p = Plate(None)
    p.ov = Image.new("RGBA", (1920 * SS, 480 * SS), (0, 0, 0, 0))
    p.d = ImageDraw.Draw(p.ov)
    p.base = Image.new("RGBA", (1920, 480), BONE)
    x = 0.0
    top, mid, bot = 84, 330, 432
    for name, t, layer, still, cx in secs:
        w = 1920 * t / tot
        x0, x1 = round(x), round(x + w)
        im = Image.open(WORK + layer + ".png").convert("RGB")
        ch, cw = mid - top, x1 - x0
        sh = 620
        sw = cw * sh / ch
        left = min(max(0, im.width * cx - sw / 2), im.width - sw)
        cy = {"r6": 520, "r2": 440, "r5": 600}.get(layer, 500)
        crop = im.crop((round(left), round(cy - sh / 2), round(left + sw), round(cy + sh / 2))).resize((cw, ch), Image.LANCZOS)
        p.base.paste(crop.convert("RGBA"), (x0, top))
        red, blue, dark = shares(STILLS + still + ".png")
        print("%s %s bone %.0f%% red %.1f%% blue %.1f%% dark %.1f%%" % (name, still, 100 * (1 - red - blue - dark), 100 * red, 100 * blue, 100 * dark))
        y = bot
        H = bot - mid - 8
        for frac, col in ((dark, INK), (blue, KLEIN), (red, RED)):
            h = H * frac
            if h > 0.5:
                p.rect([x0, y - h, x1, y], col)
            y -= h
        p.line((x1 - 1.5, 0), (x1 - 1.5, 480), WHITE, 3)
        p.text((x0 + 10, 60), name, sans(36, 700), INK)
        p.text((x0 + 10, 464), "%d:%02d" % (t // 60, t % 60), sans(24, 500), SOFT)
        x += w
    a = np.asarray(p.ov).astype(np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    a = a.reshape(480, SS, 1920, SS, 4).mean((1, 3))
    b = np.asarray(p.base).astype(np.float32) / 255
    out = b[..., :3] * (1 - a[..., 3:4]) + a[..., :3]
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILLS + "colour_script.png")
    print("saved colour_script.png")


if __name__ == "__main__":
    T = {"f1": f1, "f2": f2, "f3": f3, "f4": f4, "f5": f5, "f6": f6, "colour": colour}
    for k in (sys.argv[1:] or T):
        T[k]()
