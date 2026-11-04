"""HKBU SCIE1007 coursework science video. Lays the pen notes and the source line on the six 3D stills of the new S4 opening (bl_inserts.py shot v: the AI guesses CDK20's shape) and sets them out as one sheet with Chinese captions, like the flat storyboard W2_storyboard_1. Run: python stills_w2.py <folder with v_0000.png ... v_0005.png>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
FONTS = HERE + "../../../../remotion_public/fusion_s1/fonts/"
HAND, SANS, CN = FONTS + "Caveat.ttf", FONTS + "InterTight.ttf", "C:/Windows/Fonts/msyh.ttc"
INK, BLUE, RED, PAPER = (14, 14, 16), (0, 47, 167), (214, 34, 38), (246, 244, 239)
SRC = sys.argv[1]
PANEL = (840, 472)

NOTES = [
    [("no one had measured its shape", INK)],
    [("CDK20's sequence: 346 letters", INK)],
    [("the AI guesses its shape, again and again", INK)],
    [("sure = holds still, blue", BLUE)],
    [("not sure = won't hold still", RED), ("...and it lies across the keyhole", INK)],
    [("cut off: residues 1-302 kept", INK)],
]
CAP = [
    ("W2 开头", "这把锁没人量过：S3 结尾的空格子，只有虚线锁孔"),
    ("W2", "AI 手上只有“说明书”：CDK20 的序列，一串字母走进格子"),
    ("W2", "AI 一遍遍猜它的形状，好几个半透明的猜法叠在一起"),
    ("W2 大和弦", "大部分定住，变成实心的蓝：这些 AI 很有把握"),
    ("4-03", "镜头推近：只有尾巴一直定不下来，红色，正好横在锁孔上"),
    ("4-05", "B 做剪刀手，尾巴被剪掉，放到旁边一格，锁孔露出来"),
]


def note(img, text, xy, size, fill, rot=-2):
    f = ImageFont.truetype(HAND, size)
    box = ImageDraw.Draw(img).textbbox((0, 0), text, font=f)
    t = Image.new("RGBA", (box[2] + 20, box[3] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((10, 10), text, font=f, fill=fill + (255,))
    t = t.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.paste(t, (int(xy[0]), int(xy[1])), t)


panels = []
for i in range(6):
    p = Image.open("%s/v_%04d.png" % (SRC, i)).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((36, 30, 1040, 60 + 90 * len(NOTES[i])), 26, fill=PAPER)      # the notes get their own paper, never over the model
    for k, (text, col) in enumerate(NOTES[i]):
        note(p, text, (64, 34 + 90 * k), 72 if k == 0 else 62, col)
    if i >= 2:
        d.text((40, 1080 - 62), "Illustration · AlphaFold DB v6, AF-Q8IZL9-F1 · predicted", font=ImageFont.truetype(SANS, 30), fill=(90, 90, 90))
    p.save("%s/v_note_%04d.png" % (SRC, i))
    panels.append(p)

M, CH = 28, 120
sheet = Image.new("RGB", (3 * PANEL[0] + 4 * M, 170 + 2 * (PANEL[1] + CH) + M + 110), PAPER)
d = ImageDraw.Draw(sheet)
d.text((M, 30), "S4 开头 3D 静帧：AI 猜锁的形状（W2 至 4-05）", font=ImageFont.truetype(CN, 46), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 试渲静帧，不是成片：蓝色和红色是 AlphaFold DB v6 的真实形状，半透明的猜法是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (img, (when, text)) in enumerate(zip(panels, CAP)):
    x = M + (i % 3) * (PANEL[0] + M)
    y = 170 + (i // 3) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), "%d  %s" % (i + 1, when), font=ImageFont.truetype(CN, 26), fill=RED)
    d.text((x, y + PANEL[1] + 50), text, font=ImageFont.truetype(CN, 26), fill=INK)
d.text((M, sheet.size[1] - 95), "台词只改 4-01（B 画外音）两句：Every protein comes with written instructions: its sequence, a long line of letters. Those letters decide the lock's shape.", font=ImageFont.truetype(CN, 24), fill=INK)
d.text((M, sheet.size[1] - 55), "4-03、4-05 原话不动：没把握的尾巴横在锁孔上，科学家把它剪掉。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_stills_1.jpg", quality=90)
print("SHEET_OK", sheet.size)
