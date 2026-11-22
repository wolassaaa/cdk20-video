# HKBU SCIE1007 课程作业的科普视频：把多张静帧拼成一张联系表，方便一眼看整段。
# 用法：python sheet.py <输出.png> <列数> <输入1.png> <输入2.png> ...
import sys
from PIL import Image, ImageDraw

out, cols = sys.argv[1], int(sys.argv[2])
files = sys.argv[3:]
TW, TH = 640, 360
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * TW, rows * TH), (237, 233, 223))
for i, p in enumerate(files):
    im = Image.open(p).convert("RGB").resize((TW - 8, TH - 8), Image.LANCZOS)
    x, y = (i % cols) * TW + 4, (i // cols) * TH + 4
    sheet.paste(im, (x, y))
    d = ImageDraw.Draw(sheet)
    d.rectangle([x - 1, y - 1, x + TW - 8, y + TH - 8], outline=(110, 107, 99))
    d.text((x + 6, y + 6), p.rsplit("\\", 1)[-1], fill=(200, 16, 46))
sheet.save(out)
print(out, sheet.size)
