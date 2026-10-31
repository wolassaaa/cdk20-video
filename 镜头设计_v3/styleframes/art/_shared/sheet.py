"""HKBU SCIE1007 coursework science video. Contact sheets for picking looks: python sheet.py out.jpg cols tile_w file[=caption] ..."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/msyh.ttc"


def sheet(out, items, cols=4, tw=480, ratio=9 / 16, pad=10, cap=30):
    th = round(tw * ratio)
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + cap + pad) + pad), (20, 20, 20))
    d, f = ImageDraw.Draw(im), ImageFont.truetype(FONT, 18)
    for i, (path, label) in enumerate(items):
        x, y = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + cap + pad)
        t = Image.open(path).convert("RGB")
        t.thumbnail((tw, th), Image.LANCZOS)
        im.paste(t, (x + (tw - t.width) // 2, y + (th - t.height) // 2))
        d.text((x, y + th + 3), label, font=f, fill=(237, 235, 228))
    im.save(out, quality=88)
    return im.size


if __name__ == "__main__":
    out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    items = [(a.split("=")[0], a.split("=")[1] if "=" in a else Path(a).stem) for a in sys.argv[4:]]
    print(sheet(out, items, cols, tw))
