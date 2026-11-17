"""HKBU SCIE1007 课程作业的科普视频：给零件目录图写上编号和英文名（位置来自 kit_parts.py 渲染时写的同名 .json）。

    python kit_label.py RENDER.png OUT.png      # RENDER 可以是 4K，输出缩到 1920×1080
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts")
src, out = Path(sys.argv[1]), sys.argv[2]
im = Image.open(src).convert("RGB").resize((1920, 1080), Image.LANCZOS)
d = ImageDraw.Draw(im)
js = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
f_num = ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), 30)
f_name = ImageFont.truetype(str(FONTS / "InstrumentSerif-Italic.ttf"), 26)
for L in js["labels"]:
    x, y = L["x"] * 1920, L["y"] * 1080 + 9
    wn = d.textlength(L["num"], font=f_num); wm = d.textlength(L["name"], font=f_name)
    x0 = x - (wn + 12 + wm) / 2
    d.text((x0, y), L["num"], font=f_num, fill="#1F1E1C", anchor="ls")
    d.text((x0 + wn + 12, y), L["name"], font=f_name, fill="#6E6B63", anchor="ls")
f_h = ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), 34)
d.text((88, 62), f"Parts list  {js['page']} / 2", font=f_h, fill="#1F1E1C", anchor="ls")
d.text((1832, 62), "Illustration", font=f_name, fill="#6E6B63", anchor="rs")
im.save(out)
