"""contact sheet: python sheet.py OUT.jpg COLS SCALE f1,f2,... [frames dir] [x0,y0,x1,y1 crop]"""
import sys, os
from PIL import Image, ImageDraw

out, cols, scale = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
fr = [int(x) for x in sys.argv[4].split(",")]
base = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frames")
box = [int(v) for v in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
ims = []
for f in fr:
    im = Image.open(os.path.join(base, f"f_{f:04d}.png")).convert("RGB")
    if box:
        im = im.crop(box)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 4), f"{f}  {f / 30:.2f}s", fill=(237, 235, 228))
    ims.append(im)
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (cols * w + (cols - 1) * 4, rows * h + (rows - 1) * 4), (40, 40, 40))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols) * (w + 4), (i // cols) * (h + 4)))
sh.save(out, quality=92)
