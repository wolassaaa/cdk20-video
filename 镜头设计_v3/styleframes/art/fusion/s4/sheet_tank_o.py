"""HKBU SCIE1007 coursework science video. Sets the three stills of the culture tank rebuilt from sci-fi references (bl_inserts.py shot o, notes in 培养罐参考.md) out as one sheet with Chinese captions. Run: python sheet_tank_o.py <folder with o_0000.png ... o_0002.png>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
CN = "C:/Windows/Fonts/msyh.ttc"
INK, RED, PAPER = (14, 14, 16), (214, 34, 38), (246, 244, 239)
SRC = sys.argv[1]
ims = [Image.open("%s/o_%04d.png" % (SRC, i)).convert("RGB") for i in range(3)]
M, BIG, SMALL = 30, (1920, 1080), (945, 531)
W = BIG[0] + 2 * M
sheet = Image.new("RGB", (W, 170 + BIG[1] + 100 + SMALL[1] + 130 + 100), PAPER)
d = ImageDraw.Draw(sheet)
d.text((M, 30), "培养罐第五版：照科幻片的培养罐重做", font=ImageFont.truetype(CN, 48), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 试渲静帧：蓝红形状和转轮上的数是 AlphaFold DB v6 的真实值，机器、雾和气泡是示意", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
sheet.paste(ims[0].resize(BIG, Image.LANCZOS), (M, 170))
y = 170 + BIG[1]
d.text((M, y + 12), "1  正面（W2 里台面的灯暗下去）", font=ImageFont.truetype(CN, 30), fill=RED)
d.text((M, y + 56), "罐子自己发光，上下是带分缝和发光方块的高壳子，一圈机械臂从上面夹住；老虎机是右边伸出的一块屏", font=ImageFont.truetype(CN, 26), fill=INK)
y += 100
for i, (img, (t, c)) in enumerate(zip(ims[1:], [("2  近一点，从右边看", "四只机械臂、气泡、后面的竖灯条\n夹尾巴的机械手以后从这圈臂里伸下来"), ("3  台面灯亮着", "开罐喷气以后灯亮回来\n接 4-01 的白台面")])):
    x = M + i * (SMALL[0] + M)
    sheet.paste(img.resize(SMALL, Image.LANCZOS), (x, y))
    d.text((x, y + SMALL[1] + 10), t, font=ImageFont.truetype(CN, 28), fill=RED)
    d.multiline_text((x, y + SMALL[1] + 50), c, font=ImageFont.truetype(CN, 24), fill=INK, spacing=8)
d.multiline_text((M, sheet.size[1] - 88), "参考和要点见 s4/培养罐参考.md。照参考改的：罐子自己是光源，上下是高壳子而不是平盖，\n玻璃两头藏进壳子，上面有东西吊着，一侧不对称，罐里冒气泡。", font=ImageFont.truetype(CN, 24), fill=INK, spacing=8)
sheet.save(HERE + "W2_tank_5.jpg", quality=90)
print("SHEET_OK", sheet.size)
