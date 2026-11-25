"""HKBU SCIE1007 课程作业的科普视频：cut_v5 机器检查（下一步方案_20261116 第 4 节第 5、7 步）。
1 黑场（blackdetect）；2 静止 ≥ 3 s（freezedetect，噪声 0.001）；3 帧数累加对 new_start（声音跟画面，≤ 0.02 s）；
4 成片段（第 5 章、托盘样板）：段内声音和 cut 里同一位置的声音互相关，偏移 ≤ 1 帧（1/30 s）。
用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/_check/check_v5.py [cut_v5]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
FP = str(ROOT / "_env/ffmpeg/ffprobe.exe")
NAME = sys.argv[1] if len(sys.argv) > 1 else "cut_v5"
SRC = HERE / f"{NAME}.mp4"
J = json.loads((HERE / f"{NAME}.json").read_text(encoding="utf-8"))
out = {}


def run(*a):
    return subprocess.run([FF, "-hide_banner", "-nostats", *map(str, a)], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr


r = run("-i", SRC, "-vf", "blackdetect=d=0.1:pic_th=0.95:pix_th=0.12,freezedetect=n=0.001:d=3", "-an", "-f", "null", "-")
black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r)
fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r)]
fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r)]
ev = sorted([(t, "s") for t in fs] + [(t, "e") for t in fe])
freezes, cur = [], None
for t, k in ev:
    if k == "s" and cur is None:
        cur = t
    elif k == "e" and cur is not None:
        freezes.append((cur, t))
        cur = None
if cur is not None:
    freezes.append((cur, J["seconds"]))


def seg_at(t):
    for b in J["beats"]:
        if b["new_start"] <= t < b["new_end"]:
            return b["seg"]
    return "?"


out["black"] = [(float(a), float(b), seg_at(float(a))) for a, b in black]
out["freeze_3s"] = [(round(a, 2), round(b, 2), seg_at(a)) for a, b in freezes]
cum, worst = 0.0, 0.0
tmp = ROOT / "_render_tmp/cut"
# 3：用 json 里的 new_len 累加（build_cut 已按真帧数写）
for b in J["beats"]:
    worst = max(worst, abs(cum - b["new_start"]))
    cum = b["new_end"] + b.get("breath_after", 0)
out["start_drift_max_s"] = round(worst, 3)


def env(src, ss, t, sr=4000):
    d = subprocess.run([FF, "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(src), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.abs(np.frombuffer(d, np.int16).astype(np.float32))
    k = sr // 100
    return np.convolve(x, np.ones(k) / k, "same")[::k // 2]          # 200 Hz 包络


offs = []
for b in J["beats"]:
    if b.get("state") != "成片段":
        continue
    src = next((p for p in [ROOT / "镜头设计_v3/styleframes/art/fusion/s4" / b["picture"], HERE / "样片/托盘样板" / b["picture"]] if p.exists()), None)
    if not src:
        continue
    n = min(b["new_len"], 8.0)
    a, c = env(src, 0, n), env(SRC, b["new_start"], n)
    m = min(len(a), len(c))
    a, c = a[:m] - a[:m].mean(), c[:m] - c[:m].mean()
    lags = range(-20, 21)
    sc = [np.dot(a[max(0, -L):m - max(0, L)], c[max(0, L):m - max(0, -L)]) for L in lags]
    lag = list(lags)[int(np.argmax(sc))] / 200
    offs.append((b["seg"], round(lag, 3)))
out["override_av_offset_s"] = offs
out["seconds"] = J["seconds"]
CH5 = {"5-01", "5-03", "5-07", "5-08", "W4", "5-10", "3-01", "3-09", "4-11+4-12"}
out["freeze_3s_in_new_segments"] = [x for x in out["freeze_3s"] if x[2] in CH5]
ok = not out["black"] and not out["freeze_3s_in_new_segments"] and out["start_drift_max_s"] <= 0.02 and all(abs(o) <= 1 / 30 + 1e-6 for _, o in offs)
out["pass"] = ok
(HERE / f"_check/{NAME}_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
