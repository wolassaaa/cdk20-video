"""D1 试验对比图：1-01 第 180 帧脸部 400×400（原样 / 弱+0.4 / 弱+0.7 / 中+0.4 / 中+0.7），再放大 2 倍一行。"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shot_oncam as S
cfg = S.seg_cfg("1-01")
_, _, (nx, ny) = S.face_boxes(cfg, 180)
cx, cy = int(nx + S.PERSON["x"]), int(ny + S.PERSON["y"] - 30)
tags = ["base", "w04", "w07", "m04", "m07"]
T = Path("G:/cdk20/work/oncam/_d1_trial")
sheet = Image.new("RGB", (400 * 5, 400 + 24), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, t in enumerate(tags):
    im = Image.open(T / f"f180_{t}.png").crop((cx - 200, cy - 200, cx + 200, cy + 200))
    sheet.paste(im, (i * 400, 24)); d.text((i * 400 + 6, 6), t, fill=(255, 255, 255))
sheet.save(T / "sheet_face.png")
print(cx, cy)
