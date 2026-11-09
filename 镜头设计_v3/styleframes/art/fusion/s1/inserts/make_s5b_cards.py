"""HKBU SCIE1007 课程作业的科普视频。5-01 的七张纸卡贴图：从论文 Fig. 5 骨白底 2x 版裁出七个结构（不重画），底色提到纸色，统一比例放进 600 x 400 的卡里。
输出到 镜头设计_v3/remotion_public/fusion_s5b/card_<编号>.png（bl_s5b.py 读）。用法：python make_s5b_cards.py
"""
import glob
import os

import numpy as np
from PIL import Image

V3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
SRC = glob.glob(os.path.join(V3, "交接_4-10_S5", "论文", "Ren2023_Fig5_*2x.png"))[0]
OUT = os.path.join(V3, "remotion_public", "fusion_s5b")
os.makedirs(OUT, exist_ok=True)
# 每个结构在 1x 图上的框（左、上、右、下），只框结构，不带下面的标签框
BOX = {"001": (445, 86, 948, 305), "004": (60, 515, 485, 708), "007": (515, 446, 880, 712), "009": (905, 495, 1338, 668),
       "015": (130, 824, 415, 1112), "019": (520, 835, 900, 1105), "025": (905, 880, 1342, 1060)}
a = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
bg = np.median(a[200:260, 40:200].reshape(-1, 3), 0)
paper = np.array([247, 243, 234.0])
im = Image.fromarray(np.clip(a * (paper / bg), 0, 255).astype(np.uint8))
W, H = 600, 400
s = (W - 40) / (2 * 503)          # 一个比例给七张：最宽的 001 填满卡宽，别的照原图大小
for k, (l, t, r, b) in BOX.items():
    c = im.crop((l * 2, t * 2, r * 2, b * 2))
    c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    card = Image.new("RGB", (W, H), tuple(int(v) for v in paper))
    card.paste(c, ((W - c.width) // 2, (H - c.height) // 2))
    card.save(os.path.join(OUT, "card_%s.png" % k))
print("CARDS_OK", OUT)
