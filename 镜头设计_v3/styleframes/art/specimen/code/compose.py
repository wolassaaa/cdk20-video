"""HKBU SCIE1007 coursework science video. Lays type, leader lines and evidence tags over the specimen plates and writes stills/F1..F6.png and colour_script.png. All drawing is at 2x and downsampled once.

Run with plain python: python compose.py [F1 F2 ...]
Fonts: Inter Tight, Instrument Serif, Martian Mono (Google Fonts, SIL OFL), from S1/v2/_code/s110/fonts.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PL, OUT = HERE.parent / "plates", HERE.parent / "stills"
ART = HERE.parents[1]
FONTS = ART.parent / "S1/v2/_code/s110/fonts"
S2 = ART.parent / "S2plus/public"
W, H, SS = 1920, 1080, 2
RED, DEEP, KLEIN, BLUE, BONE = (232, 25, 15), (154, 14, 8), (0, 47, 167), (31, 59, 255), (237, 235, 228)
DIM = (178, 176, 171)                    # bone at about 75 percent on black
M = 96


def sans(px, wght=500):
    f = ImageFont.truetype(str(FONTS / "InterTight.ttf"), px * SS)
    f.set_variation_by_axes([wght])
    return f


def mono(px, wght=400):
    f = ImageFont.truetype(str(FONTS / "MartianMono.ttf"), px * SS)
    f.set_variation_by_axes([wght, 100])
    return f


def serif(px):
    return ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), px * SS)


class C:
    """One frame: a plate underneath, an overlay drawn at 2x on top."""

    def __init__(self, plate=None):
        self.base = Image.open(plate).convert("RGB").resize((W, H), Image.LANCZOS) if plate else Image.new("RGB", (W, H), (0, 0, 0))
        self.o = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.o)

    def text(self, xy, s, font, fill=BONE, anchor="la"):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=font, fill=fill, anchor=anchor)

    def width(self, s, font):
        return font.getlength(s) / SS

    def line(self, pts, fill=BONE, w=2):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=int(w * SS), joint="curve")

    def ring(self, xy, r=8, fill=BONE, w=2, dot=True):
        x, y = xy
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], outline=fill, width=int(w * SS))
        if dot:
            q = 2.5
            self.d.ellipse([(x - q) * SS, (y - q) * SS, (x + q) * SS, (y + q) * SS], fill=fill)

    def leader(self, start, *rest, fill=BONE, w=2):
        """A label line: from the label, one bend, and a small ring that lands on the structure."""
        pts = [start, *rest]
        ex, ey = pts[-1]
        px, py = pts[-2]
        L = math.hypot(ex - px, ey - py) or 1
        pts[-1] = (ex - (ex - px) / L * 8, ey - (ey - py) / L * 8)
        self.line(pts, fill, w)
        self.ring((ex, ey), 8, fill, w)

    def dashes(self, a, b, on, off, fill=BONE, w=2):
        (x0, y0), (x1, y1) = a, b
        L = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < L:
            e = min(t + on, L)
            self.line([(x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L), (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)], fill, w)
            t += on + off

    def tag(self, kind, s, x, y, anchor="l", px=26):
        """Evidence tags differ by line, never only by colour.
        measured: solid filled plate. predicted: dashed outline. docking: dotted outline. schematic: double outline."""
        f = mono(px, 500)
        tw = self.width(s, f)
        h, pad = px + 26, 18
        x0 = x if anchor == "l" else x - tw - 2 * pad
        x1, y1 = x0 + tw + 2 * pad, y + h
        if kind == "measured":
            self.d.rectangle([x0 * SS, y * SS, x1 * SS, y1 * SS], fill=BONE)
            self.text((x0 + pad, y + h / 2), s, f, (0, 0, 0), "lm")
            return x0, x1
        if kind == "schematic":
            self.d.rectangle([x0 * SS, y * SS, x1 * SS, y1 * SS], outline=BONE, width=2 * SS // 2)
            self.d.rectangle([(x0 + 6) * SS, (y + 6) * SS, (x1 - 6) * SS, (y1 - 6) * SS], outline=BONE, width=2 * SS // 2)
        else:
            on, off, w = (14, 9, 2) if kind == "predicted" else (2.5, 7, 3)
            for a, b in (((x0, y), (x1, y)), ((x1, y), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y))):
                self.dashes(a, b, on, off, BONE, w)
        self.text((x0 + pad, y + h / 2), s, f, BONE, "lm")
        return x0, x1

    def road(self, x, y, lit=0, scale=1.0, before=False):
        """Small road map: six tube outlines, lit ones filled red. before = a red dot in front of the first tube."""
        r, h, gap = 11 * scale, 44 * scale, 40 * scale
        if before:
            q = 6 * scale
            self.d.ellipse([(x - 30 * scale - q) * SS, (y + h - r - q) * SS, (x - 30 * scale + q) * SS, (y + h - r + q) * SS], fill=RED)
        for i in range(6):
            cx = x + i * gap
            if i < lit:
                self.d.rounded_rectangle([(cx - r) * SS, y * SS, (cx + r) * SS, (y + h) * SS], radius=r * SS, fill=RED)
            self.d.rounded_rectangle([(cx - r) * SS, y * SS, (cx + r) * SS, (y + h) * SS], radius=r * SS, outline=BONE, width=2 * SS)

    def save(self, name):
        im = self.o.resize((W, H), Image.LANCZOS)
        b = self.base.convert("RGBA")
        b.alpha_composite(im)
        OUT.mkdir(exist_ok=True)
        b.convert("RGB").save(OUT / name)
        print("saved", name)


def fade(im, y0, y1):
    """Darken the plate towards black between two rows, for type to sit on."""
    a = np.asarray(im).astype(np.float32)
    k = 1 - np.clip((np.arange(H) - y0) / (y1 - y0), 0, 1)
    return Image.fromarray((a * k[:, None, None]).astype(np.uint8))


def F1():
    c = C(PL / "f1.png")
    f = json.load(open(PL / "f1.json"))
    c.text((M - 6, 330), "1,412", sans(210, 500), BONE, "ls")
    c.text((M, 396), "deaths in Hong Kong, 2022", sans(50, 500))
    lab = sans(36, 500)
    c.text((M, 640), "liver", lab)
    c.leader((M + 86, 662), LIVER)
    c.text((1490, 92), "hepatic veins", lab)
    c.leader((1478, 114), (1340, 114), HEPATIC)
    c.text((1340, 806), "portal vein", lab)
    c.leader((1328, 828), (1296, 828), PORTAL)
    c.text((M, H - M + 6), "HKCaR 2022 · BodyParts3D, DBCLS, CC BY 4.0", mono(24), DIM, "ls")
    px = f["px_per_100mm"] / 2                                     # 5 cm
    x1 = W - M
    c.line([(x1 - px, H - M), (x1, H - M)], BONE, 2)
    c.line([(x1 - px, H - M - 10), (x1 - px, H - M + 10)], BONE, 2)
    c.line([(x1, H - M - 10), (x1, H - M + 10)], BONE, 2)
    c.text((x1, H - M - 22), "5 cm", mono(24), DIM, "rs")
    c.save("F1.png")


def F3():
    c = C(PL / "f3.png")
    p = json.load(open(PL / "f3.json"))
    lab = sans(36, 500)
    c.text((M, 300), "target (a protein)", lab)
    c.leader((M + 276, 322), (p["lockL"][0] - 175, 322), (p["lockL_edge"][0] + 30, 400))
    c.text((M, 730), "candidate", lab)
    c.text((M, 776), "(a small molecule)", lab)
    c.leader((M + 294, 798), (p["bowL"][0] - 86, 798), (p["bowL"][0] - 40, p["bowL"][1] + 40))
    c.text((960, 880), "selectivity", sans(72, 500), BONE, "ms")
    mx, my = p["tipR"]
    my -= 26
    r = 17
    for (a_, b_) in (((mx - r, my - r), (mx + r, my + r)), ((mx - r, my + r), (mx + r, my - r))):
        c.line([a_, b_], (0, 0, 0), 11)
    for (a_, b_) in (((mx - r, my - r), (mx + r, my + r)), ((mx - r, my + r), (mx + r, my - r))):
        c.line([a_, b_], BONE, 5)
    c.tag("schematic", "schematic", M, H - M - 40)
    c.road(W - M - 200, M - 30, 0, 1.0, before=True)
    c.save("F3.png")


def F4():
    c = C(PL / "f4.png")
    p = json.load(open(PL / "f4.json"))
    x = 1330
    c.text((x, 420), "floppy tail", sans(84, 500), RED)
    c.text((x, 520), "low confidence", sans(44, 500))
    c.leader((x - 18, 462), (1240, 462), TAIL)
    lg = sans(36, 500)
    y0 = 650
    c.d.rounded_rectangle([x * SS, y0 * SS, (x + 74) * SS, (y0 + 22) * SS], radius=8 * SS, fill=BONE)
    c.text((x + 96, y0 + 12), "more confident", lg, BONE, "lm")
    c.d.rounded_rectangle([x * SS, (y0 + 64) * SS, (x + 74) * SS, (y0 + 74) * SS], radius=5 * SS, fill=RED)
    c.text((x + 96, y0 + 70), "less confident", lg, BONE, "lm")
    c.tag("predicted", "AlphaFold DB v6 · predicted", M, H - M - 40)
    bar = p["px_per_nm"] * 2                                       # 2 nm
    bx = W - M
    c.line([(bx - bar, H - M - 8), (bx, H - M - 8)], BONE, 2)
    c.line([(bx - bar, H - M - 18), (bx - bar, H - M + 2)], BONE, 2)
    c.line([(bx, H - M - 18), (bx, H - M + 2)], BONE, 2)
    c.text((bx, H - M - 30), "2 nm", mono(24), DIM, "rs")
    c.road(W - M - 200, M - 30, 1, 1.0)
    c.save("F4.png")


def F5():
    c = C(PL / "f5.png")
    x0, per_nm = 120, 0.25
    x6k = x0 + 6000 * per_nm
    Y1, Y2, R = 318, 560, 30
    c.text((M, M + 34), "Enzyme IC50", sans(64, 500), BONE, "ls")
    c.road(W - M - 200, M - 30, 3, 1.0)
    for y in (Y1, Y2):                                             # graduations: one tick every 1,000 nM on both tubes
        for k in range(0, 7):
            x = x0 + k * 1000 * per_nm
            n = 18 if k in (0, 6) else 10
            c.line([(x, y - R - n), (x, y - R - 2)], BONE, 2)
    c.text((x6k + 14, Y1 - 62), "001 > 6,000 nM", sans(44, 500), BONE, "rs")
    for i in range(3):                                             # no end on this bar: chevrons run off the frame
        x = 1660 + i * 84
        c.line([(x, Y1 - 15), (x + 18, Y1), (x, Y1 + 15)], (0, 0, 0), 5)
    # 048: the value and its error bar, drawn to the same scale
    v, e = 33.4 * per_nm, 22.6 * per_nm
    ey = Y2 + R + 24
    c.line([(x0 + v - e, ey - 16), (x0 + v - e, ey), (x0 + v + e, ey), (x0 + v + e, ey - 16)], BONE, 2)   # a bracket, 11 px wide: the +/- range to scale
    c.line([(x0 + v, ey), (x0 + v, ey + 64), (x0 + 58, ey + 64)], BONE, 2)
    c.text((x0 + 70, ey + 62), "048 = 33.4 ± 22.6 nM", sans(84, 600), RED, "lm")
    c.text((x0 + 70, ey + 152), "Just this much cuts the enzyme's activity in half.", sans(40, 500), BONE, "lm")
    c.tag("measured", "MEASURED · Ren 2023, Fig. 9A", x0, H - M - 40)
    # our docking, in a dotted round case
    im = Image.open(S2 / "pose_048_blue.png").convert("RGBA")
    im.alpha_composite(Image.open(S2 / "pose_048_lig.png").convert("RGBA").resize(im.size, Image.LANCZOS))
    D = 296
    th = im.crop((300, 180, 1720, 1600)).resize((D, D), Image.LANCZOS)
    cx, cy = W - M - D // 2, 770
    mask = Image.new("L", (D * 2, D * 2), 0)
    ImageDraw.Draw(mask).ellipse([4, 4, D * 2 - 4, D * 2 - 4], fill=255)
    mask = mask.resize((D, D), Image.LANCZOS)
    c.base.paste(th.convert("RGB"), (cx - D // 2, cy - D // 2), Image.composite(th.getchannel("A"), Image.new("L", (D, D), 0), mask))
    for i in range(120):
        a = 2 * math.pi * i / 120
        x, y = cx + (D / 2 + 8) * math.cos(a), cy + (D / 2 + 8) * math.sin(a)
        c.d.ellipse([(x - 1.6) * SS, (y - 1.6) * SS, (x + 1.6) * SS, (y + 1.6) * SS], fill=BONE)
    c.tag("docking", "OUR RE-DOCKING", W - M, H - M - 40, "r")
    c.save("F5.png")


def F6():
    b = fade(Image.open(PL / "f6.png").convert("RGB").resize((W, H), Image.LANCZOS), 726, 770)
    b.save(PL / "_f6_faded.png")
    c = C(PL / "_f6_faded.png")
    p = json.load(open(PL / "f6.json"))
    nm = sans(36, 600)
    bd = sans(36, 500)
    rows = [(["Target"], []), (["Hit"], []), (["Improve"], []), (["Cells & animals"], ["cells: first tests", "animals:", "not reported"]),
            (["Clinical trials", "1-2-3"], ["not reported"]), (["Approval"], ["not reported"])]
    for q, (a, b2) in zip(p, rows):
        y = 776
        for s in a:
            c.text((q["x"], y), s, nm, BONE, "ma")
            y += 46
        y += 8
        for s in b2:
            c.text((q["x"], y), s, bd, DIM, "ma")
            y += 46
    t = p[3]
    c.text((t["x"], 196), "048", sans(84, 600), RED, "ms")
    c.leader((t["x"], 208), (t["x"], t["liquid"] + 2), fill=RED, w=3)
    c.save("F6.png")


def F2():
    WX, WY, WW, WH = 560, 72, 1264, 711
    # placeholder wall and an outline of where the speaker sits. Real phone footage replaces both, at this size, 16:9, no roto needed.
    wall = Image.new("RGB", (WW, WH), (17, 17, 19))
    a = np.asarray(wall).astype(np.float32)
    yy, xx = np.mgrid[0:WH, 0:WW]
    k = 1.25 - 0.9 * ((xx / WW - 0.5) ** 2 + (yy / WH - 0.45) ** 2) ** 0.5 * 1.6
    wall = Image.fromarray(np.clip(a * k[..., None], 0, 255).astype(np.uint8))
    base = Image.new("RGB", (W, H), (0, 0, 0))
    base.paste(wall, (WX, WY))
    base.save(PL / "_f2_base.png")
    c = C(PL / "_f2_base.png")
    c.d.rectangle([(WX - 6) * SS, (WY - 6) * SS, (WX + WW + 6) * SS, (WY + WH + 6) * SS], outline=DIM, width=2)
    cx, top = WX + WW / 2, WY + 120
    head = [(cx + 92 * math.cos(t) * (1 - 0.08 * math.sin(t)), top + 118 + 118 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 90)]
    for a_, b_ in zip(head[::2], head[1::2]):
        c.line([a_, b_], BONE, 2)
    y0 = top + 232
    for sg in (-1, 1):                                             # neck into shoulder, one smooth curve
        P = [(cx + sg * 46, y0), (cx + sg * 52, y0 + 66), (cx + sg * 300, y0 + 60), (cx + sg * 322, WY + WH - 6)]
        B = [tuple(sum(w_ * q[i] for w_, q in zip(((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3), P)) for i in (0, 1)) for t in np.linspace(0, 1, 60)]
        for a_, b_ in zip(B[::2], B[1::2]):
            c.line([a_, b_], BONE, 2)
    c.text((WX + 28, WY + 28), "PLACEHOLDER · phone footage", mono(24), DIM, "la")
    c.road(M + 50, WY + WH - 75, 0, 1.7, before=True)
    q = "How can computer-aided methods help scientists find and assess"
    q2 = "potential cancer drug candidates?"
    f = serif(66)
    c.text((M, 842), q, f)
    c.text((M, 922), q2, f)
    c.save("F2.png")


def colour_script():
    secs = [("S1", 141), ("S2", 142), ("S3", 129), ("S4", 213), ("S5", 139), ("S6", 151), ("S7", 49), ("S8", 99)]
    total = sum(s for _, s in secs)
    srcs = [(PL / "f1.png", 0.66, 0.46), (OUT / "F2.png", 0.62, 0.46), (PL / "f3.png", 0.34, 0.45), (PL / "f4.png", 0.36, 0.5), (OUT / "F5.png", 0.84, 0.535), (PL / "_f6_faded.png", 0.3, 0.42), (PL / "_f6_faded.png", 0.725, 0.42), (PL / "f1.png", 0.74, 0.32)]
    im = Image.new("RGB", (W, 480), (0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FONTS / "MartianMono.ttf"), 24)
    f.set_variation_by_axes([400, 100])
    x = 0
    edges = []
    for i, ((nm, s), (src, u, v)) in enumerate(zip(secs, srcs)):
        x1 = round(sum(t for _, t in secs[:i + 1]) / total * W)
        w_ = x1 - x
        fr = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
        h_ = 396
        s_ = h_ / 620                                             # crop 620 px tall from the frame, scaled to the strip
        cw = min(W, w_ / s_)
        cx0 = min(max(0, u * W - cw / 2), W - cw)
        cy0 = min(max(0, v * H - 310), H - 620)
        th = fr.crop((round(cx0), round(cy0), round(cx0 + cw), round(cy0 + 620))).resize((w_, h_), Image.LANCZOS)
        im.paste(th, (x, 0))
        d.text((x + 10, 412), nm, font=f, fill=BONE)
        edges.append(x)
        x = x1
    for e in edges[1:]:
        d.line([(e, 0), (e, 396)], fill=(0, 0, 0), width=4)
    im.save(OUT / "colour_script.png")
    print("saved colour_script")


LIVER, PORTAL, HEPATIC, TAIL = (782, 662), (1262, 828), (1226, 222), (1186, 511)
ALL = dict(F1=F1, F2=F2, F3=F3, F4=F4, F5=F5, F6=F6, CS=colour_script)
if __name__ == "__main__":
    for k in sys.argv[1:] or ALL:
        ALL[k]()
