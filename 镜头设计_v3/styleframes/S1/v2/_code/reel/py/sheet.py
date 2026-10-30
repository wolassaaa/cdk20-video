"""Contact sheet: python sheet.py OUT.jpg cols img1[:label] img2[:label] ...  (labels in msyh)"""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols = sys.argv[1], int(sys.argv[2]); items = sys.argv[3:]
tw, th, lab, pad = 640, 360, 34, 10
rows = (len(items) + cols - 1) // cols
sh = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (14, 14, 14))
fnt = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
d = ImageDraw.Draw(sh)
for i, it in enumerate(items):
    p, _, l = it.partition("::")
    x, y = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + lab + pad)
    sh.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y + lab))
    d.text((x, y + 6), l or p.split("/")[-1], font=fnt, fill=(237, 235, 228))
sh.save(out, quality=88)
