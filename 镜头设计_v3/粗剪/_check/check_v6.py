"""HKBU SCIE1007 课程作业的科普视频：cut_v6 机器检查（下一步方案_20261116 第 3.3、4 节）。check_v5.py 的扩展：
1 黑场 0（blackdetect）；
2 静止 ≥ 3 s 为 0（freezedetect 噪声 0.001），片名 W1 和片尾 W5 的出处段除外；
3 帧数累加对 new_start（声音跟画面，≤ 0.02 s）；
4 成片段（第 5 章、托盘段）：段内声音和 cut 里同一位置的声音互相关，偏移 ≤ 1 帧（1/30 s）；
  对时段（画外音变速）：段的声音放在 new_start，词时间来自同一份 condense，偏移看 3；
5 人露出 ≥ 6 帧再开口：托盘段读 tray/_resolved/<组>.json（人淡入完 / 切进来那一帧 → 首词帧），三条样板读 sample3.json、beats2.json；
6 穿模 0：托盘段读 bl_tray4 的 clash.json，样板读 clash_t309/t411.json，第 5 章读 C:/render_tmp/s5d_clash.txt（单独列出）。
用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/_check/check_v6.py [cut_v6]
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
NAME = sys.argv[1] if len(sys.argv) > 1 else "cut_v6"
SRC = HERE / f"{NAME}.mp4"
J = json.loads((HERE / f"{NAME}.json").read_text(encoding="utf-8"))
TRAYSRC = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/tray"
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
        if b["new_start"] <= t < b["new_end"] + b.get("breath_after", 0):
            return b["seg"]
    return "?"


out["black"] = [(float(a), float(b), seg_at(float(a))) for a, b in black]
out["freeze_3s_all"] = [(round(a, 2), round(b, 2), seg_at(a)) for a, b in freezes]
out["freeze_3s"] = [x for x in out["freeze_3s_all"] if x[2] not in ("W1", "W5")]
cum, worst = 0.0, 0.0
for b in J["beats"]:
    worst = max(worst, abs(cum - b["new_start"]))
    cum = b["new_end"] + (b.get("breath_after", 0) if b.get("state") != "对时" else 0)
out["start_drift_max_s"] = round(worst, 3)


def env(src, ss, t, sr=4000):
    d = subprocess.run([FF, "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(src), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.abs(np.frombuffer(d, np.int16).astype(np.float32))
    k = sr // 100
    return np.convolve(x, np.ones(k) / k, "same")[::k // 2]


offs = []
for b in J["beats"]:
    if b.get("state") != "成片段":
        continue
    src = next((p for p in [ROOT / "镜头设计_v3/styleframes/art/fusion/s4" / b["picture"], HERE / "样片/托盘v6" / b["picture"], HERE / "样片/托盘样板" / b["picture"]] if p.exists()), None)
    if not src:
        continue
    n = min(b["new_len"], 8.0)
    a, c = env(src, 0, n), env(SRC, b["new_start"], n)
    m = min(len(a), len(c))
    a, c = a[:m] - a[:m].mean(), c[:m] - c[:m].mean()
    lags = range(-20, 21)
    sc = [np.dot(a[max(0, -L):m - max(0, L)], c[max(0, L):m - max(0, -L)]) for L in lags]
    offs.append((b["seg"], round(list(lags)[int(np.argmax(sc))] / 200, 3)))
out["override_av_offset_s"] = offs

# 5 人露出 → 开口
reveal = []
for f in sorted((TRAYSRC / "_resolved").glob("*.json")):
    if f.stem == "all":
        continue
    C = json.loads(f.read_text(encoding="utf-8"))
    for k, p in enumerate(C["parts"]):
        shown = C["person_in"][1] if k == 0 else p["at"]
        first = min(v for kk, v in C["words"].items() if kk.startswith(f"{k}:"))
        reveal.append((C["name"], p["seg"], first - shown))
S3 = json.loads((TRAYSRC / "sample3.json").read_text(encoding="utf-8"))
reveal.append(("样板3", "3-09", min(S3["t309"]["words"].values()) - S3["t309"]["person_in"][1]))
w411 = S3["t411"]["words"]
reveal.append(("样板2", "4-11", w411["Wait."] - S3["t411"]["person_in"][1]))
reveal.append(("样板2", "4-12", w411["Not"] - S3["t411"]["cut"]))
B2 = json.loads((TRAYSRC / "beats2.json").read_text(encoding="utf-8"))
if "person_in" in B2 and "words" in B2:
    reveal.append(("样板1", "3-01", min(v for v in B2["words"].values() if isinstance(v, (int, float))) - B2["person_in"][1]))
out["reveal_frames_60fps"] = reveal
out["reveal_fail"] = [x for x in reveal if x[2] < 6]

# 6 穿模
clash = {}
for g in sorted((ROOT / "_render_tmp/tm4").glob("*/clash.json")):
    rows = json.loads(g.read_text())
    clash[g.parent.name] = sum(1 for x in rows if x["clash"])
for k in ("t309", "t411"):
    p = HERE / f"样片/托盘样板/_work/clash_{k}.json"
    if p.exists():
        rows = json.loads(p.read_text())
        clash["样板_" + k] = sum(1 for x in rows if x.get("clash"))
out["tray_clash_frames"] = clash
s5 = Path("C:/render_tmp/s5d_clash.txt")
out["ch5_clash_log"] = s5.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-8:] if s5.exists() else []
out["seconds"] = J["seconds"]
ok = (not out["black"] and not out["freeze_3s"] and out["start_drift_max_s"] <= 0.02 and all(abs(o) <= 1 / 30 + 1e-6 for _, o in offs)
      and not out["reveal_fail"] and not any(clash.values()))
out["pass"] = ok
(HERE / f"_check/{NAME}_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
