"""HKBU SCIE1007 coursework science video. Sets the four culture-tank looks (bl_inserts.py shot n, after the director's note of 11-04 14:15) out as one sheet with Chinese captions, for the director to pick one. Run: python sheet_tank_looks.py <folder with n_0000.png ... n_0003.png>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
SANS = HERE + "../../../../remotion_public/fusion_s1/fonts/InterTight.ttf"
CN = "C:/Windows/Fonts/msyh.ttc"
INK, RED, PAPER = (14, 14, 16), (214, 34, 38), (246, 244, 239)
SRC = sys.argv[1]
PANEL = (1260, 709)
CAP = [
    ("A  白色硬件", "白色烤漆机身分层，黑玻璃带配青色灯线，三根白色立柱，顶上一个镀铬发射头"),
    ("B  深色机甲", "枪灰金属，底座一圈散热片透出橙光，罐盖带散热鳍片，背后三根线缆插回底座"),
    ("C  悬浮光环", "整只玻璃胶囊，没有金属盖；两道白色光环悬空套在外面，黑色底座底下发青光"),
    ("D  六角舱", "六面玻璃，石墨色立柱带灯线，六角形分层顶盖和白色底座"),
]
M, CH = 30, 110
sheet = Image.new("RGB", (2 * PANEL[0] + 3 * M, 170 + 2 * (PANEL[1] + CH) + 70), PAPER)
d = ImageDraw.Draw(sheet)
d.text((M, 30), "培养罐造型：四个方向，挑一个往下做", font=ImageFont.truetype(CN, 48), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 试渲静帧：都停在定住那一拍；四个转轮停在 AlphaFold DB v6 每段的平均 pLDDT（87、92、95 蓝，47 红），蓝红形状是真实模型，机器是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (title, text) in enumerate(CAP):
    img = Image.open("%s/n_%04d.png" % (SRC, i)).convert("RGB")
    x = M + (i % 2) * (PANEL[0] + M)
    y = 170 + (i // 2) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), title, font=ImageFont.truetype(CN, 30), fill=RED)
    d.text((x, y + PANEL[1] + 56), text, font=ImageFont.truetype(CN, 26), fill=INK)
d.text((M, sheet.size[1] - 60), "罐子比上一版高、瘦，所有罐子都站在同一个格子上，镜头放低一点。挑中以后再补：抽真空、雾、转轮转、开罐喷气、机械手。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_tank_looks_1.jpg", quality=90)
print("SHEET_OK", sheet.size)
