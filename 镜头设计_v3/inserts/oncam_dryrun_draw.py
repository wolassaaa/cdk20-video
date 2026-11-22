"""HKBU SCIE1007 课程作业的科普视频：oncam_dryrun.py 投影点 → 叠在人物图上的构图示意拼图（系统 Python 跑，Blender 里没有 PIL）。
python oncam_dryrun_draw.py 段号 → $CDK20_WORK/oncam/<段>/proj/proj_sheet.jpg"""
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
seg = sys.argv[1]
d = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work")) / "oncam" / seg / "proj"
J = json.load(open(d / "proj.json"))
P = J["person_box"]
tiles = []
for f, fr in J["frames"].items():
    im = Image.new("RGB", (1920, 1080), (58, 58, 62))
    pim = Image.open(fr["person"]).convert("RGBA").resize((P["w"], P["h"]))
    im.paste(pim, (P["x"], P["y"]), pim)
    dr = ImageDraw.Draw(im)
    for x, y, r, g, b in fr["pts"]:
        dr.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(r, g, b))
    if fr.get("box"):
        dr.rectangle(fr["box"], outline=(0, 255, 0), width=2)
    dr.line([(0, 940), (1920, 940)], fill=(255, 255, 0), width=2)
    dr.line([(1880, 0), (1880, 1080)], fill=(255, 255, 0), width=2)
    dr.text((12, 12), f"{seg} f{f}", fill=(255, 255, 0))
    tiles.append(im.resize((640, 360)))
cols = 4
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (640 * cols, 360 * rows))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * 640, (i // cols) * 360))
sheet.save(d / "proj_sheet.jpg", quality=85)
print(d / "proj_sheet.jpg")
