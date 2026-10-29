"""python sheet.py DIR OUT [--cols 2] [--w 960] -- tile f_*.png into a contact sheet with frame labels."""
import sys, glob, os
from PIL import Image, ImageDraw
a = sys.argv[1:]; d, out = a[0], a[1]
cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 2
tw = int(a[a.index("--w") + 1]) if "--w" in a else 960
fs = sorted(glob.glob(os.path.join(d, "f_*.png")))
ims = [Image.open(f).convert("RGB") for f in fs]
th = int(tw * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (cols * tw, rows * th), (6, 6, 6))
dr = ImageDraw.Draw(sh)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * tw, (i // cols) * th
    sh.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
    dr.text((x + 10, y + 8), "f%s" % os.path.basename(f)[2:6], fill=(232, 255, 58))
q = 92
while True:
    if out.lower().endswith(".jpg"): sh.save(out, quality=q)
    else: sh.save(out); break
    if os.path.getsize(out) <= 2_000_000 or q < 40: break
    q -= 6
print("sheet", out, os.path.getsize(out))
