"""HKBU SCIE1007 coursework science video. S1 motion test: joins the overlapping tiles bl_plate.py renders for a very large plate, then removes them.

Run: python stitch.py <out.png> <width> <height> <cols> <rows> <overlap>
"""
import os
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
out = sys.argv[1]
w, h, cols, rows, lap = [int(v) for v in sys.argv[2:7]]
full = Image.new("RGB", (w, h))
names = []
for j in range(rows):
    for i in range(cols):
        name = "%s_%d_%d.png" % (out[:-4], i, j)
        tile = Image.open(name).convert("RGB")
        a, c = i * w // cols, j * h // rows
        b, d = (i + 1) * w // cols, (j + 1) * h // rows
        x, y = a - max(0, a - lap), c - max(0, c - lap)
        full.paste(tile.crop((x, y, x + b - a, y + d - c)), (a, c))
        names.append(name)
full.save(out, compress_level=1)
for name in names:
    os.remove(name)
print("STITCHED", out)
