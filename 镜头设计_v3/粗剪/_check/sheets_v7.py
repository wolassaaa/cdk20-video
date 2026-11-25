"""HKBU SCIE1007 课程作业的科普视频：给审片子代理出 cut_v7 的联系表。每 1 秒一格，一张 10×6 = 60 秒，格子左上角写片内秒。
出：粗剪/_check/cut_v7_sheets/sheet_NN.jpg；外加每段首末帧对照 joins_NN.jpg（上一段末帧 | 下一段首帧，看接头）。
用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/_check/sheets_v6.py [cut_v7]
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
NAME = sys.argv[1] if len(sys.argv) > 1 else "cut_v7"
SRC = HERE / f"{NAME}.mp4"
J = json.loads((HERE / f"{NAME}.json").read_text(encoding="utf-8"))
OUT = HERE / f"_check/{NAME}_sheets"
OUT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "_render_tmp/cut7/frames"
TMP.mkdir(parents=True, exist_ok=True)
W, H = 320, 180
font = ImageFont.load_default()
subprocess.run([FF, "-v", "error", "-y", "-i", str(SRC), "-vf", f"fps=1,scale={W}:{H}", str(TMP / "f_%05d.jpg")], check=True)
fr = sorted(TMP.glob("f_*.jpg"))


def seg_at(t):
    for b in J["beats"]:
        if b["new_start"] <= t < b["new_end"] + (b.get("breath_after", 0) if b.get("state") != "对时" else 0):
            return b["seg"]
    return ""


for k in range(0, len(fr), 60):
    sh = Image.new("RGB", (W * 10, H * 6), "white")
    for i, f in enumerate(fr[k:k + 60]):
        im = Image.open(f)
        d = ImageDraw.Draw(im)
        t = k + i
        d.rectangle([0, 0, 110, 14], fill="black")
        d.text((3, 2), f"{t // 60}:{t % 60:02d} {seg_at(t + 0.5)}", fill="yellow", font=font)
        sh.paste(im, ((i % 10) * W, (i // 10) * H))
    sh.save(OUT / f"sheet_{k // 60:02d}.jpg", quality=82)
# 接头：每个段界前 0.1 s 和后 0.1 s
pairs = []
for a, b in zip(J["beats"], J["beats"][1:]):
    t = b["new_start"]
    pairs.append((a["seg"], b["seg"], t))
rows = []
for a, b, t in pairs:
    ims = []
    for tt in (max(0, t - 0.1), t + 0.1):
        p = TMP / f"j_{tt:.2f}.jpg"
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{tt:.3f}", "-i", str(SRC), "-frames:v", "1", "-vf", f"scale={W}:{H}", str(p)], check=True)
        ims.append(Image.open(p))
    r = Image.new("RGB", (W * 2 + 4, H), "black")
    r.paste(ims[0], (0, 0))
    r.paste(ims[1], (W + 4, 0))
    ImageDraw.Draw(r).text((4, 4), f"{a} -> {b} @ {t:.1f}s", fill="yellow", font=font)
    rows.append(r)
for k in range(0, len(rows), 24):
    sh = Image.new("RGB", ((W * 2 + 4) * 3, H * 8), "white")
    for i, r in enumerate(rows[k:k + 24]):
        sh.paste(r, ((i % 3) * (W * 2 + 4), (i // 3) * H))
    sh.save(OUT / f"joins_{k // 24:02d}.jpg", quality=82)
print("sheets", len(fr) // 60 + 1, "joins", len(rows))
