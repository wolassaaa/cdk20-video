"""HKBU SCIE1007 coursework science video. S6 storyboard sketch, two flat panels for the director: the scoreboard made of table cells (BEFORE | NOW, four rows of
objects the viewer has already met) and the road with three tags (6-10, 6-11). Row 4's NOW cell is left as a marked slot for the teammate who does the S5 content.
Run: python storyboard_s6.py"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/"
BONE, INK, SOFT, RED, KLEIN, CELL, GREY = (237, 235, 228), (17, 17, 19), (84, 84, 88), (232, 25, 15), (0, 47, 167), (200, 198, 192), (170, 168, 163)
W, H = 1600, 900
serif = ImageFont.truetype(FONTS + "InstrumentSerif-Regular.ttf", 64)
serif_i = ImageFont.truetype(FONTS + "InstrumentSerif-Italic.ttf", 40)
sans = ImageFont.truetype(FONTS + "InterTight.ttf", 20)
note = ImageFont.truetype(FONTS + "Caveat[wght].ttf", 30)
zh = ImageFont.truetype(FONTS + "NotoSerifSC-VF.ttf", 26)


def dashed_rect(d, box, col, dash=14):
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), dash * 2):
        d.line([x, y0, min(x + dash, x1), y0], fill=col, width=4)
        d.line([x, y1, min(x + dash, x1), y1], fill=col, width=4)
    for y in range(int(y0), int(y1), dash * 2):
        d.line([x0, y, x0, min(y + dash, y1)], fill=col, width=4)
        d.line([x1, y, x1, min(y + dash, y1)], fill=col, width=4)


def scoreboard():
    im = Image.new("RGB", (W, H), BONE)
    d = ImageDraw.Draw(im)
    d.text((330, 30), "BEFORE", font=serif, fill=SOFT)
    d.text((930, 30), "NOW", font=serif, fill=INK)
    rows = ["seeing the lock", "finding a hit", "time", "improving the key"]
    for r in range(4):
        y = 120 + r * 190
        d.text((40, y + 60), rows[r], font=note, fill=INK)
        L, R = (300, y, 760, y + 165), (880, y, 1340, y + 165)
        d.rounded_rectangle(L, 22, outline=CELL, width=8)
        d.rounded_rectangle(R, 22, outline=CELL, width=8)
        if r == 0:
            dashed_rect(d, (350, y + 25, 560, y + 140), GREY)
            d.polygon([(620, y + 130), (700, y + 130), (675, y + 70), (675, y + 40), (645, y + 40), (645, y + 70)], outline=SOFT, width=3)
            for k in range(30):
                a = 2 * math.pi * k / 30
                rr = 55 + 10 * math.sin(5 * a) + 6 * math.sin(11 * a)
                d.ellipse([1040 + rr * math.cos(a) - 14, y + 82 + 0.8 * rr * math.sin(a) - 14, 1040 + rr * math.cos(a) + 14, y + 82 + 0.8 * rr * math.sin(a) + 14], fill=KLEIN)
            d.text((1150, y + 120), "predicted · free", font=note, fill=INK)
        elif r == 1:
            for i in range(40):
                for j in range(6):
                    x, yy = 315 + 11 * i, y + 20 + 22 * j
                    d.rounded_rectangle([x, yy, x + 6, yy + 17], 3, fill=GREY)
            d.text((780, y + 110), "millions", font=note, fill=SOFT)
            for k in range(13):
                d.ellipse([930 + 22 * k, y + 70, 944 + 22 * k, y + 84], fill=INK)
            d.text((1230, y + 52), "13", font=serif_i, fill=INK)
            d.line([1230, y + 102, 1270, y + 102], fill=RED, width=4)
        elif r == 2:
            d.line([320, y + 85, 740, y + 85], fill=INK, width=3)
            d.ellipse([320 - 6, y + 79, 332, y + 91], outline=RED, width=3)
            d.text((470, y + 100), "10–17 years", font=note, fill=SOFT)
            d.line([900, y + 85, 960, y + 85], fill=RED, width=5)
            d.line([960, y + 85, 1020, y + 85], fill=INK, width=5)
            d.text((900, y + 100), "30 days -> hit, +30 -> better key", font=note, fill=INK)
        else:
            d.ellipse([440, y + 25, 620, y + 145], outline=SOFT, width=5)
            d.text((640, y + 60), "lab rounds", font=note, fill=SOFT)
            dashed_rect(d, (910, y + 20, 1310, y + 145), RED)
            d.text((925, y + 60), "slot: filled from the paper's figure by our teammate", font=sans, fill=RED)
    d.text((300, 862), "different sources · scale and speed, not one race", font=note, fill=INK)
    return im


def road():
    im = Image.new("RGB", (W, H), BONE)
    d = ImageDraw.Draw(im)
    names = ["target", "hit", "improve", "cells | animals", "trials", "approval"]
    xs = [180 + 250 * i for i in range(6)]
    d.line([xs[0], 450, xs[-1], 450], fill=GREY, width=6)
    for i, x in enumerate(xs):
        r = 52
        if i < 2:
            d.ellipse([x - r, 450 - r, x + r, 450 + r], fill=RED)
        elif i == 2:
            d.ellipse([x - r, 450 - r, x + r, 450 + r], fill=(240, 120, 110))
        elif i == 3:
            d.pieslice([x - r, 450 - r, x + r, 450 + r], 90, 270, fill=RED)
            d.arc([x - r, 450 - r, x + r, 450 + r], 270, 90, fill=GREY, width=4)
        else:
            d.arc([x - r, 450 - r, x + r, 450 + r], 0, 360, fill=GREY, width=4)
        d.text((x - 60, 520), names[i], font=note, fill=INK if i < 4 else SOFT)
    d.text((xs[4] - 70, 560), "not reported", font=sans, fill=SOFT)
    d.rounded_rectangle([xs[3] - 110, 296, xs[3] + 40, 358], 10, outline=INK, width=3)
    d.text((xs[3] - 95, 300), "048", font=serif_i, fill=INK)
    d.text((xs[3] - 160, 250), "made public for other researchers", font=note, fill=INK)
    d.rounded_rectangle([xs[5] - 140, 640, xs[5] + 130, 690], 10, outline=(0, 140, 160), width=3)
    d.text((xs[5] - 130, 650), "lirafugratinib · FDA 2026", font=sans, fill=INK)
    d.line([xs[0], 665, xs[5] - 140, 665], fill=(0, 140, 160), width=3)
    d.rounded_rectangle([xs[2] - 110, 740, xs[2] + 110, 790], 10, outline=SOFT, width=3)
    d.text((xs[2] - 100, 750), "EXS-21546 · stopped", font=sans, fill=SOFT)
    d.line([xs[2] - 115, 765, xs[2] + 115, 765], fill=RED, width=4)
    return im


sheet = Image.new("RGB", (2 * W + 90, H + 160), BONE)
ds = ImageDraw.Draw(sheet)
ds.text((30, 20), "S6 · 12:44–15:15 · 草图 v1：左是计分板（6-01 到 6-08），右是路线和三枚标签（6-10、6-11）", font=zh, fill=INK)
sheet.paste(scoreboard(), (30, 80))
sheet.paste(road(), (60 + W, 80))
for x in (30, 60 + W):
    ds.rectangle([x, 80, x + W - 1, 80 + H - 1], outline=CELL, width=2)
ds.text((30, H + 100), "第 4 行右格是空位，由接手 S5 的同伴照论文原图填；其余格子放全片已出现过的旧物。", font=zh, fill=SOFT)
out = HERE + "/S6_storyboard_1.png"
sheet.save(out)
print("STORYBOARD_OK", sheet.size)
