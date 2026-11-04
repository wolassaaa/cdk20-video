"""HKBU SCIE1007 coursework science video. Lays the pen notes and the source line on the six 3D stills of the S4 opening as a culture tank, version 3 (bl_inserts.py shot s, the director's notes of 11-04 14:05: a finer machine, a four-reel slot machine that lands on AlphaFold's own confidence) and sets them out as one sheet with Chinese captions, like the flat storyboard W2_storyboard_1. Run: python stills_slot_tank.py <folder with s_0000.png ... s_0005.png>"""
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
    [("vacuum: the question goes", INK), ("pull the lever", INK)],
    [("a new guess on every beat", INK)],
    [("sure: 87  92  95", BLUE), ("not sure: 47", RED)],
    [("open it: bang", INK)],
    [("CDK20, as the AI predicts it", INK)],
]
CAP = [
    ("W2 开头", "罐里起雾，雾里悬着一个问号；下面老虎机的四个转轮都是 ??"),
    ("W2", "问号像抽真空一样被吸上管子；拉杆拉下，四个转轮开始转"),
    ("W2", "雾里 CDK20 疯狂成形、一直在抖，一拍换一个猜法；转轮转成一片"),
    ("W2 大和弦", "雾散了，形状变实；转轮停在 87、92、95（蓝）和 47（红）"),
    ("W2 结尾", "罐盖连同支架往上提，蒸汽砰地喷出来"),
    ("接 4-01", "开罐：CDK20 立在格子里；后面接推近和机械手"),
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
    p = Image.open("%s/s_%04d.png" % (SRC, i)).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(p)
    NS, LH = 44, 70          # notes and source stay left of the slot machine (it starts about x 660)
    wide = max(ImageDraw.Draw(p).textbbox((0, 0), t, font=ImageFont.truetype(HAND, NS))[2] for t, _ in NOTES[i])
    y0 = 1080 - 140 - LH * len(NOTES[i])          # low left: the top left has S3's neighbour shape
    d.rounded_rectangle((36, y0, 90 + wide, y0 + 18 + LH * len(NOTES[i])), 22, fill=PAPER)      # paper only as wide as the words
    for k, (text, col) in enumerate(NOTES[i]):
        note(p, text, (56, y0 + 2 + LH * k), NS, col)
    if i >= 2:
        for k, line in enumerate(("Illustration · AlphaFold DB v6,", "AF-Q8IZL9-F1 · predicted")):
            d.text((40, 1080 - 96 + 34 * k), line, font=ImageFont.truetype(SANS, 26), fill=(90, 90, 90))
    p.save("%s/s_note_%04d.png" % (SRC, i))
    panels.append(p)

M, CH = 28, 120
sheet = Image.new("RGB", (3 * PANEL[0] + 4 * M, 170 + 2 * (PANEL[1] + CH) + M + 110), PAPER)
d = ImageDraw.Draw(sheet)
d.text((M, 30), "S4 开头 3D 静帧第三版：培养罐 + 四轮老虎机（W2，配 Harder Better Faster Stronger）", font=ImageFont.truetype(CN, 46), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 试渲静帧，不是成片：蓝红形状和转轮上的四个数是 AlphaFold DB v6 的真实值（每段的平均 pLDDT），灰色猜法、雾和机器是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (img, (when, text)) in enumerate(zip(panels, CAP)):
    x = M + (i % 3) * (PANEL[0] + M)
    y = 170 + (i // 3) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), "%d  %s" % (i + 1, when), font=ImageFont.truetype(CN, 26), fill=RED)
    d.text((x, y + PANEL[1] + 50), text, font=ImageFont.truetype(CN, 26), fill=INK)
d.text((M, sheet.size[1] - 95), "台词只改 4-01（B 画外音）两句：Every protein comes with written instructions: its sequence, a long line of letters. Those letters decide the lock's shape.", font=ImageFont.truetype(CN, 24), fill=INK)
d.text((M, sheet.size[1] - 55), "转轮四段：1–100、101–200、201–302、303–346（尾巴）。70 以上算有把握，所以前三个蓝、最后一个红。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_tank_stills_3.jpg", quality=90)
print("SHEET_OK", sheet.size)
