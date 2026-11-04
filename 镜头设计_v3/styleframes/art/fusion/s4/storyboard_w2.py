"""HKBU SCIE1007 coursework science video. A six-panel storyboard sheet for the new opening of S4 (W2 to 4-05): instead of a bead chain, the AI keeps guessing the shape of CDK20 until most of it holds still; the part it is unsure of, the tail, never settles and lies across the keyhole, and is cut off. Drawn flat over S3's last frame; the outline comes from the AlphaFold DB v6 model seen from above, the guesses are drawn. A sketch for the director, not a film frame. Run: python storyboard_w2.py"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
INS = HERE + "../s1/inserts/"
FONTS = HERE + "../../../../remotion_public/fusion_s1/fonts/"
HAND = FONTS + "Caveat.ttf"
SERIF = FONTS + "InstrumentSerif-Regular.ttf"
SANS = FONTS + "InterTight.ttf"
CN = "C:/Windows/Fonts/msyh.ttc"
INK, BLUE, RED = (14, 14, 16), (0, 47, 167), (214, 34, 38)
CELL = (2114, 658, 3164, 1506)               # the red cell at 4K
HOLE = np.array((2650.0, 1072.0))            # keyhole centre at 4K
W, H = 3840, 2160                            # everything is drawn on the whole 4K frame, then each panel crops it
MAIN = (1690, 512, 3610, 1592)               # the cell, with room above for the note
WIDE = (1900, 520, 3840, 1611)               # pulled back: this cell and the empty one to its right
PANEL = (840, 472)

bg = Image.open(INS + "frames/q/q_4260.png").convert("RGB")       # S3's last frame: the empty cell, the dashed keyhole

# the keyhole, fitted to the dashes in the frame (pocket_outline.py's points, y down)
pts = np.array(json.load(open(INS + "frames/pocket_outline.json"))["points"]) * (1, -1)
key = (pts - pts.min(0)) * 332.0 + (2316.0, 808.0)

lines = [l for l in open(HERE + "../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in lines])
AA = dict(ALA="A", ARG="R", ASN="N", ASP="D", CYS="C", GLN="Q", GLU="E", GLY="G", HIS="H", ILE="I", LEU="L", LYS="K", MET="M", PHE="F", PRO="P", SER="S", THR="T", TRP="W", TYR="Y", VAL="V")
seq = "".join(AA[l[17:20]] for l in lines)
top = ca[:, :2] * (1, -1)                      # the model seen from above, y down
lo, hi = top[:302].min(0) - 5.5, top[:302].max(0) + 5.5
S = float(min((CELL[2] - CELL[0] - 120) / (hi - lo)[0], (CELL[3] - CELL[1] - 120) / (hi - lo)[1]))      # pixels per angstrom: CDK20 fills its cell
xy = (top - (lo + hi) / 2) * S + ((CELL[0] + CELL[2]) / 2, (CELL[1] + CELL[3]) / 2)
tail = np.array([np.mean(top[max(301, i - 2):i + 3], 0) for i in range(301, len(top))])           # the tail, 302-346, smoothed a little
tail = (tail - top[304]) * S + HOLE            # laid across the keyhole, Arg305 on it
mid = (tail.min(0) + tail.max(0) + 2 * HOLE) / 4
CLOSE = tuple(int(v) for v in (mid[0] - 680, mid[1] - 382, mid[0] + 680, mid[1] + 383))     # pushed in over the tail and the keyhole


def smooth_mask(p, rad, blur, cut=0.35):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for x, y in p:
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
    return np.clip((m - cut) * 12 + 0.5, 0, 1)


def poly_mask(p, grow=0):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([tuple(q) for q in p], fill=255)
    if grow:            # a rim round the keyhole, drawn as a thick outline
        d.line([tuple(q) for q in p] + [tuple(p[0])], fill=255, width=2 * grow, joint="curve")
    return np.asarray(m.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255


def warp(m, seed, amp):
    """A smooth random bend of the mask: one of the AI's guesses."""
    g = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.zeros_like(xx)
    dy = np.zeros_like(xx)
    for _ in range(3):
        k, ph = g.uniform(0.003, 0.008, 2), g.uniform(0, 6.3, 2)
        dx += amp * np.sin(k[0] * (xx - HOLE[0]) + k[1] * (yy - HOLE[1]) + ph[0])
        dy += amp * np.sin(k[1] * (xx - HOLE[0]) - k[0] * (yy - HOLE[1]) + ph[1])
    sx = np.clip(xx + dx, 0, W - 1).astype(int)
    sy = np.clip(yy + dy, 0, H - 1).astype(int)
    return m[sy, sx]


def edge(m, width=0.25):
    return np.clip(1 - np.abs(m - 0.5) / width, 0, 1)


def paint(img, alpha, rgb):
    a = np.asarray(img, np.float32)
    a = a + (np.array(rgb, np.float32) - a) * alpha[:, :, None]
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))


def stroke(path, width, rgb, alpha, img):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.line([tuple(q) for q in path], fill=255, width=int(width), joint="curve")
    for x, y in (path[0], path[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=255)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    return paint(img, a * alpha, rgb)


def note(img, text, xy, size=64, fill=INK, rot=-2):
    f = ImageFont.truetype(HAND, size)
    box = ImageDraw.Draw(img).textbbox((0, 0), text, font=f)
    t = Image.new("RGBA", (box[2] + 20, box[3] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((10, 10), text, font=f, fill=fill + (255,))
    t = t.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.paste(t, (int(xy[0]), int(xy[1])), t)
    return img


def crop(img, box, label=True):
    p = img.crop(box).resize((1680, 945), Image.LANCZOS)
    if label:
        ImageDraw.Draw(p).text((36, 945 - 62), "Illustration · AlphaFold DB v6, AF-Q8IZL9-F1 · predicted", font=ImageFont.truetype(SANS, 28), fill=(90, 90, 90))
    return p


def swing(angle=0.0, bend=0.0):
    """The tail swung round where it leaves the model and bent: the tail's own guesses."""
    rel = tail - tail[0]
    k = np.linspace(0, 1, len(tail))
    a = np.radians(angle) * k + np.radians(bend) * k ** 2
    c, s = np.cos(a), np.sin(a)
    return tail[0] + np.c_[rel[:, 0] * c - rel[:, 1] * s, rel[:, 0] * s + rel[:, 1] * c]


hole = poly_mask(key)
lock = np.clip(np.maximum(smooth_mask(xy[:302], 5.5 * S, 3.2 * S), poly_mask(key, 75)) - hole, 0, 1)      # CDK20 round its keyhole: the pocket stays open
GHOSTS = [(-38, 12), (26, -20), (-16, 34), (44, 8)]
TW = 2.4 * S
panels = []

# 1: the lock no one had measured
panels.append(note(crop(bg, MAIN, False), "no one had measured its shape", (70, 40)))

# 2: the AI only has the instructions: the sequence, a line of letters, runs into the cell
p = bg.copy()
f = ImageFont.truetype(SERIF, 64)
d = ImageDraw.Draw(p)
n = 34
for i in range(n):
    u = i / (n - 1)
    x = MAIN[0] + 60 + u * (HOLE[0] - MAIN[0] - 60)
    y = MAIN[3] - 140 + u * (HOLE[1] - MAIN[3] + 140) - math.sin(u * math.pi) * 180
    shade = int(170 * (1 - u) ** 2)
    d.text((x, y), seq[i], font=f, fill=(shade + 14, shade + 14, shade + 16), anchor="mm")
panels.append(note(crop(p, MAIN, False), "CDK20's sequence: 346 letters", (70, 40)))

# 3: guess after guess, the outline keeps changing
p = bg.copy()
for i, seed in enumerate((3, 8, 13, 21)):
    g = warp(lock, seed, 55)
    p = paint(p, g * 0.06, INK)
    p = paint(p, edge(g) * (0.35 + 0.15 * i), INK)
panels.append(note(crop(p, MAIN), "the AI guesses its shape, again and again", (70, 40)))

# 4: most of it holds still and fills in blue: the part the AI is sure of
p = bg.copy()
for seed in (5, 9):
    p = paint(p, edge(warp(lock, seed, 14)) * 0.3, BLUE)
p = paint(p, lock * 0.92, BLUE)
p = paint(p, edge(lock, 0.2) * 0.9, INK)
for a, b in GHOSTS:
    p = stroke(swing(a, b), TW, INK, 0.25, p)
panels.append(note(crop(p, MAIN), "sure = holds still, blue", (70, 40), fill=BLUE))

base = paint(paint(bg.copy(), lock * 0.92, BLUE), edge(lock, 0.2) * 0.9, INK)

# 5: pushed in: the tail never settles, and it lies across the keyhole
p = base.copy()
for a, b in GHOSTS:
    p = stroke(swing(a, b), TW, RED, 0.35, p)
p = stroke(swing(), TW * 1.1, RED, 1.0, p)
p = crop(p, CLOSE)
ImageDraw.Draw(p).rounded_rectangle((40, 650, 1010, 850), 24, fill=(246, 244, 239))
p = note(p, "not sure = won't hold still", (70, 650), fill=RED)
panels.append(note(p, "...and it lies across the keyhole", (70, 730), size=56))

# 6: cut off and set down in the next cell; the keyhole is clear
p = base.copy()
p = stroke(swing() - swing().mean(0) + (3560, 1080), TW * 1.1, RED, 1.0, p)
panels.append(note(crop(p, WIDE), "cut off: residues 1-302 kept", (70, 40)))

CAP = [
    ("W2 开头", "这把锁没人量过：S3 结尾的空格子，只有虚线锁孔"),
    ("W2", "AI 手上只有“说明书”：CDK20 的序列，一串字母走进格子"),
    ("W2", "AI 一遍遍猜它的形状，轮廓不停地变"),
    ("W2 大和弦", "大部分越变越慢，定住，填成蓝色：这些 AI 很有把握"),
    ("4-03", "镜头推近：只有尾巴一直定不下来，红色，来回晃，正好横在锁孔上"),
    ("4-05", "B 做剪刀手，尾巴被剪掉，放进旁边一格，锁孔露出来"),
]
M, CH = 28, 120
sheet = Image.new("RGB", (3 * PANEL[0] + 4 * M, 170 + 2 * (PANEL[1] + CH) + M + 110), (246, 244, 239))
d = ImageDraw.Draw(sheet)
d.text((M, 30), "S4 开头分镜草图：AI 猜锁的形状（W2 至 4-05）", font=ImageFont.truetype(CN, 46), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 不是成片：平面草图，最后的形状用 AlphaFold DB v6 的真实模型，猜的过程是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (img, (when, text)) in enumerate(zip(panels, CAP)):
    x = M + (i % 3) * (PANEL[0] + M)
    y = 170 + (i // 3) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), "%d  %s" % (i + 1, when), font=ImageFont.truetype(CN, 26), fill=RED)
    d.text((x, y + PANEL[1] + 50), text, font=ImageFont.truetype(CN, 26), fill=INK)
d.text((M, sheet.size[1] - 95), "台词只改 4-01（B 画外音）两句：Every protein comes with written instructions: its sequence, a long line of letters. Those letters decide the lock's shape.", font=ImageFont.truetype(CN, 24), fill=INK)
d.text((M, sheet.size[1] - 55), "4-03、4-05 原话不动：没把握的尾巴横在锁孔上，科学家把它剪掉。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_storyboard_1.png")
sheet.save(HERE + "W2_storyboard_1.jpg", quality=90)
print("STORYBOARD_OK", sheet.size)
