"""HKBU SCIE1007 coursework science video. Lays the pen notes and the source line on the six 3D stills of the S4 opening as a culture tank (bl_inserts.py shot t, the director's idea of 11-04, W2 to Harder Better Faster Stronger) and sets them out as one sheet with Chinese captions, like the flat storyboard W2_storyboard_1. Run: python stills_tank.py <folder with t_0000.png ... t_0005.png>"""
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
    [("in goes the sequence: 346 letters", INK)],
    [("a new guess on every beat", INK)],
    [("sure = blue    not sure = red", BLUE)],
    [("drain it, open it", INK)],
    [("CDK20, as the AI predicts it", INK)],
]
CAP = [
    ("W2 开头", "S3 的空格子上立着一个科幻培养罐，淡青色的液体里悬着一个问号"),
    ("W2", "CDK20 的序列（一串字母）从顶上的进料管送进去"),
    ("W2", "罐里的形状一拍换一个：AI 一遍遍猜它的形状"),
    ("W2 大和弦", "定住：大部分是蓝色（AI 有把握），尾巴是红色（没把握）"),
    ("W2 结尾", "液体排掉，玻璃罩往上提走"),
    ("接 4-01", "开罐：CDK20 立在格子里，留着玻璃底板；后面接推近和机械手"),
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
    p = Image.open("%s/t_%04d.png" % (SRC, i)).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(p)
    wide = max(ImageDraw.Draw(p).textbbox((0, 0), t, font=ImageFont.truetype(HAND, 58))[2] for t, _ in NOTES[i])
    y0 = 1080 - 170 - 90 * len(NOTES[i]) if i == 1 else 30          # panel 2: the letters fly in along the top, so its note goes low
    d.rounded_rectangle((36, y0, 100 + wide, y0 + 14 + 80 * len(NOTES[i])), 26, fill=PAPER)      # paper only as wide as the words, clear of the tank and the model
    for k, (text, col) in enumerate(NOTES[i]):
        note(p, text, (64, y0 + 4 + 90 * k), 58, col)
    if i >= 2:
        d.text((40, 1080 - 62), "Illustration · AlphaFold DB v6, AF-Q8IZL9-F1 · predicted", font=ImageFont.truetype(SANS, 30), fill=(90, 90, 90))
    p.save("%s/t_note_%04d.png" % (SRC, i))
    panels.append(p)

M, CH = 28, 120
sheet = Image.new("RGB", (3 * PANEL[0] + 4 * M, 170 + 2 * (PANEL[1] + CH) + M + 110), PAPER)
d = ImageDraw.Draw(sheet)
d.text((M, 30), "S4 开头 3D 静帧：培养罐里猜出 CDK20（W2，配 Harder Better Faster Stronger）", font=ImageFont.truetype(CN, 46), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 试渲静帧，不是成片：蓝色和红色是 AlphaFold DB v6 的真实形状，灰色的猜法和培养罐是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (img, (when, text)) in enumerate(zip(panels, CAP)):
    x = M + (i % 3) * (PANEL[0] + M)
    y = 170 + (i // 3) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), "%d  %s" % (i + 1, when), font=ImageFont.truetype(CN, 26), fill=RED)
    d.text((x, y + PANEL[1] + 50), text, font=ImageFont.truetype(CN, 26), fill=INK)
d.text((M, sheet.size[1] - 95), "台词只改 4-01（B 画外音）两句：Every protein comes with written instructions: its sequence, a long line of letters. Those letters decide the lock's shape.", font=ImageFont.truetype(CN, 24), fill=INK)
d.text((M, sheet.size[1] - 55), "罐太大放不进格子里面，所以罐子站在一块玻璃底板上，底板搭在格子凸起的边框上，锁孔从玻璃底下透出来。4-03、4-05 接推近和机械手。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_tank_stills_1.jpg", quality=90)
print("SHEET_OK", sheet.size)
