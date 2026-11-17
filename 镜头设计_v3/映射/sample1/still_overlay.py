"""HKBU SCIE1007 课程作业的科普视频：样片一 2-03 静帧叠字（桌沿字幕带 44 px + 左下出处行 28 px，设计语言_v1 第 4 节）。
    python still_overlay.py IN.png OUT.png FRAME
字幕和出处行出现的帧取 映射/keys/2-03.json。"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
MAP = Path(__file__).resolve().parents[1]
K = json.loads((MAP / "keys" / "2-03.json").read_text(encoding="utf-8"))
EV = {e["id"]: e for e in K["events"]}
W = {w["wid"]: w for w in K["words"]}
F = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
inp, out, f = sys.argv[1], sys.argv[2], int(sys.argv[3])
im = Image.open(inp).convert("RGB"); d = ImageDraw.Draw(im)
sub = None
if W["2-03.w001"]["f0"] <= f <= W["2-03.w008"]["f1"]:
    sub = "And we'll answer it with one case study:"
elif f >= W["2-03.w009"]["f0"]:
    sub = "CDK20 in liver cancer."
if sub:
    ft = ImageFont.truetype(str(F), 44)
    d.text((960, 930), sub, font=ft, fill="#1F1E1C", anchor="ms")
if f >= EV["source_line"]["f_land"]:
    ft = ImageFont.truetype(str(F), 28)
    d.text((48, 1048), "Ren et al., Chem. Sci. 2023 · Illustration", font=ft, fill="#6E6B63", anchor="ls")
im.save(out)
