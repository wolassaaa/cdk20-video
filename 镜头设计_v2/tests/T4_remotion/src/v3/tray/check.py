"""HKBU SCIE1007 课程作业的科普视频。托盘试片 1 自查：亮度、动作对词、静止间隔、避让、穿模、帧条、联系表。用法：python check.py <成片.mp4> <输出目录>"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path("D:/。hkbu/molecular science")
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
HERE = Path(__file__).parent
B = json.load(open(HERE / "beats.json", encoding="utf-8"))
mp4, out = Path(sys.argv[1]), Path(sys.argv[2])
W, H = 960, 540
raw = subprocess.run([FF, "-v", "error", "-i", str(mp4), "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
n = len(fr)
lum = (fr.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean(axis=(1, 2))
plate = subprocess.run([FF, "-v", "error", "-i", str(HERE.parents[3] / "../../镜头设计_v3/粗剪/样片/托盘试片1/_work/public/plate.mp4"), "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
paper = float((np.frombuffer(plate, np.uint8).reshape(H, W, 3).astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean())
rep = {"frames": n, "paper_luma": round(paper, 1), "min_luma": round(float(lum.min()), 1), "min_luma_frame": int(lum.argmin()), "min_ratio": round(float(lum.min() / paper), 3)}
T = B["t301"]
w = B["words_301"]
rep["person_full"] = B["person_in"][1]
rep["okay"] = T + w["Okay"]
rep["gap_person_to_okay"] = T + w["Okay"] - B["person_in"][1]
rep["last_word_end"] = T + w["end"]
rep["push_start"] = B["push"][0]
lands = []
for a in B["actions"]:
    if a["word"]:
        wf = T + w[a["word"]]
        lands.append({"action": a["name"], "word": a["word"], "word_frame": wf, "land": a["land"], "diff": a["land"] - wf})
rep["landings"] = lands
# 物体动作间隔：动作区间（节拍表）合并后最长空档；只算到交给 S3 之前
iv = sorted((a["start"], a["land"]) for a in B["actions"])
cover, gaps, cur = [], [], 0
last_end = B["pull"][0]
for s_, e_ in iv:
    if s_ > last_end:
        gaps.append((last_end, s_))
    last_end = max(last_end, e_)
gaps.append((last_end, B["s3_in"][1]))
rep["object_gaps"] = [(a, b, b - a) for a, b in gaps]
rep["max_object_gap"] = max(b - a for a, b in gaps)
# 托盘画面里（x 860 以右）逐帧像素变化，人不算；镜头静止段
tr = fr[:, :, 430:, :].astype(np.int16)
d = np.abs(np.diff(tr, axis=0)).mean(axis=(1, 2, 3))
still, run = [], 0
for i, v in enumerate(d, 1):
    run = run + 1 if v < 0.05 else 0
    still.append(run)
rep["max_still_run_px_tray"] = int(max(still))
rep["max_still_run_end"] = int(np.argmax(still)) + 1
# 避让和穿模（Blender 记录）
tk = json.load(open(HERE.parents[3] / "../../镜头设计_v3/粗剪/样片/托盘试片1/_work/track.json"))
bad = [(r["f"], k, r[k][0]) for r in tk if B["pull"][0] <= r["f"] < B["push"][0] for k in ("lock", "key", "target", "route") if k in r and r[k][3] > 0 and r[k][1] < 1080 and r[k][0] < 860]
rep["objects_x_lt_860_before_push"] = bad[:10]
rep["clash_frames_before_handoff"] = sorted({r["f"] for r in tk if r["f"] < B["s3_in"][1] for k in r if k.startswith("clash")})
rep["clash_frames_after_520_inherited_from_shot_k"] = len([r for r in tk if r["f"] >= 520 and any(k.startswith("clash") for k in r)])
json.dump(rep, open(out / "自查.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in rep.items() if k not in ("landings",)}, ensure_ascii=False))
for l in lands:
    print(l)


def strip(c, name, label):
    fs = [c + k for k in range(-6, 7)]
    tw, th = 320, 180
    im = Image.new("RGB", (tw * 13, th + 24), "white")
    dr = ImageDraw.Draw(im)
    for i, x in enumerate(fs):
        im.paste(Image.fromarray(fr[min(x, n - 1)]).resize((tw, th)), (i * tw, 24))
        dr.text((i * tw + 4, 4), f"{x}" + (" *" if x == c else ""), fill="black")
    dr.text((tw * 6 + 40, 4), label, fill="red")
    im.save(out / name, quality=88)


strip(B["pull"][1] - 6, "帧条_拉远接点.jpg", "2-08 route -> tray route")
strip(B["s3_in"][1] - 4, "帧条_推近接S3.jpg", "tray key -> 3-02 key close-up")
strip(B["push"][1], "帧条_推近落点.jpg", "push lands on shot k camera")
cols, tw, th = 6, 320, 180
idx = list(range(0, n, 15))
im = Image.new("RGB", (cols * tw, ((len(idx) + cols - 1) // cols) * (th + 18)), "white")
dr = ImageDraw.Draw(im)
for i, x in enumerate(idx):
    X, Y = (i % cols) * tw, (i // cols) * (th + 18)
    im.paste(Image.fromarray(fr[x]).resize((tw, th)), (X, Y + 18))
    dr.text((X + 4, Y + 3), f"f{x}  {x / 60:.2f}s", fill="black")
im.save(out / "联系表_每0.25秒.jpg", quality=85)
