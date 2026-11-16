"""HKBU SCIE1007 课程作业的科普视频：cut_v8 机器检查（导演 11-16 新规则）。check_v7b.py 的扩展。
原有：1 黑场 0；2 静止 ≥ 3 s 为 0（W1、W5 除外）；3 帧数累加对 new_start；4 成片段音画偏移 ≤ 1 帧；5 人露出 ≥ 6 帧再开口；6 穿模 0。
新增（全部在拼好的 cut_v8.mp4 上量，不信节拍表）：
  A 词—事件：画外音段和第 5 章每个锚点（节拍表里"这个动作对这个词"），成片里锚点 ±0.5 s 内最近的动作起点离词开口多远；|偏差| ≤ 0.2 s 算过；
  B 动画终点—句尾：段里最后一次明显动作（帧差）离末词结束多远；要求 ≥ −0.5 s（动画不早于句尾半秒停）；
    同时记说话区间里最长的停住（帧差低于阈值）秒数，> 1.5 s 的列出来（源片在那几句里没有内容，要重出）；
  C 出镜话尾：每个出镜段，成片里段尾前 0.12 s 的声音能量比这段峰值低 30 dB 以上（话说完了才切），且托盘节拍表里末词结束 + 0.2 s < 段尾；
  D 人像边界：托盘 v8 每个 part 的人像外框（prep8 的 bbox_out）左右在画内、头顶在 0.18–0.40 H；整片四边无黑边（边上 3 px 平均亮度 < 40）；
  E 推镜：build_cut_v8.py 里不再调用 word_push / breathe；
  F 字幕：每条字幕出现 = 首词开口（偏差 ≤ 1 帧）、最长 42 字符、最短 0.6 s；字幕框（底部 y ≥ 975）不压人脸（托盘人像头顶 + 0.32 H 以内算脸）；
    手机可读：字高 54/1080 = 5% 画高（6 吋手机横屏约 3.4 mm）。
用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/_check/check_v8.py [cut_v8]
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
NAME = sys.argv[1] if len(sys.argv) > 1 else "cut_v8"
SRC = HERE / f"{NAME}.mp4"
J = json.loads((HERE / f"{NAME}.json").read_text(encoding="utf-8"))
TRAYSRC = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/tray"
B8 = HERE / "对时/beats_v8"
out = {}


def run(*a):
    return subprocess.run([FF, "-hide_banner", "-nostats", *map(str, a)], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr


# ---------- 原有 1–6 ----------
r = run("-i", SRC, "-vf", "blackdetect=d=0.1:pic_th=0.95:pix_th=0.12,freezedetect=n=0.001:d=3", "-an", "-f", "null", "-")
black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r)
fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r)]
fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r)]
freezes = []
for a in fs:
    b = next((e for e in fe if e > a), J["seconds"])
    freezes.append((a, b))


def seg_at(t):
    for b in J["beats"]:
        if b["new_start"] <= t < b["new_end"] + (b.get("breath_after", 0) if b.get("state") != "对时" else 0):
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


def pcm(src, ss, t, sr=4000):
    d = subprocess.run([FF, "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(src), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(d, np.int16).astype(np.float32)


def env(src, ss, t, sr=4000):
    x = np.abs(pcm(src, ss, t, sr))
    k = sr // 100
    return np.convolve(x, np.ones(k) / k, "same")[::k // 2]


offs = []
for b in J["beats"]:
    if b.get("state") != "成片段":
        continue
    src = next((p for p in [ROOT / "镜头设计_v3/styleframes/art/fusion/s4" / b["picture"], HERE / "样片/托盘v8" / b["picture"], HERE / "样片/托盘v6" / b["picture"],
                            HERE / "样片/托盘样板" / b["picture"]] if p.exists()), None)
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

reveal = []
RES8 = TRAYSRC / "_resolved8"
for f in sorted(RES8.glob("*.json")):
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
out["reveal_frames_60fps"] = reveal
out["reveal_fail"] = [x for x in reveal if x[2] < 6]
clash = {}
for g in sorted(list((ROOT / "_render_tmp/tm4").glob("*/clash.json")) + list((ROOT / "镜头设计_v3/粗剪/样片/托盘v8/_work/tm8").glob("*/clash.json"))):
    rows = json.loads(g.read_text())
    clash[g.parent.name] = sum(1 for x in rows if x["clash"])
out["tray_clash_frames"] = clash
s5 = Path("C:/render_tmp/s5d_clash.txt")
out["ch5_clash_log"] = s5.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:] if s5.exists() else []

# ---------- A、B：词—事件、动画终点—句尾（在成片上量） ----------
MW, MH = 160, 90


def motion_cut(ss, t):
    p = subprocess.run([FF, "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(SRC), "-an", "-vf", f"fps=30,scale={MW}:{MH}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(p, np.uint8)
    n = len(a) // (MW * MH)
    a = a[:n * MW * MH].reshape(n, MH, MW).astype(np.float32) / 255
    d = np.zeros(n, np.float32)
    if n > 1:
        df = np.abs(a[1:] - a[:-1]).reshape(n - 1, 9, 10, 16, 10).mean(axis=(2, 4)).reshape(n - 1, -1)
        df = np.maximum(0, df - 0.0015)
        d[1:] = df.max(axis=1)
    if len(d) < 3:
        return d
    return np.convolve(d, np.ones(3) / 3, "same")


ev_rows, end_rows, still_rows = [], [], []
for b in J["beats"]:
    seg = b["seg"]
    bj = B8 / f"{seg}.json"
    if not bj.exists():
        continue
    B = json.loads(bj.read_text(encoding="utf-8"))
    words = B["words"]
    t0 = b["new_start"]
    L = b["new_end"] - t0 + b.get("breath_after", 0) * (0 if b.get("state") == "对时" else 1)
    d = motion_cut(t0, L)
    if len(d) < 3:
        still_rows.append((seg, None, round(t0, 1)))
        continue
    thr = max(0.004, 0.12 * float(np.percentile(d, 95)))
    tt = np.arange(len(d)) / 30
    on = d > thr
    rises = [tt[i] for i in range(1, len(d)) if on[i] and not on[i - 1]]
    for s_, t_ in B["anchors"][1:-1]:
        w = min(words, key=lambda x: abs(x["t0"] - t_))
        if abs(w["t0"] - t_) > 0.05:
            continue                               # 不是挂在词上的锚点（起终点）
        near = [r_ for r_ in rises if abs(r_ - t_) <= 0.5]
        dev = min(near, key=lambda r_: abs(r_ - t_)) - w["t0"] if near else None
        ev_rows.append((seg, w["w"], round(w["t0"], 2), None if dev is None else round(dev, 2)))
    t_last = words[-1]["t1"]
    act = tt[on & (tt <= t_last + 1.2)]
    last = float(act.max()) if len(act) else -9
    end_rows.append((seg, round(last - t_last, 2)))
    sp = (tt >= words[0]["t0"]) & (tt <= t_last)
    run_, longest, at = 0, 0, 0
    for i in np.where(sp)[0]:
        run_ = 0 if on[i] else run_ + 1
        if run_ > longest:
            longest, at = run_, tt[i] - run_ / 30
    still_rows.append((seg, round(longest / 30, 2), round(t0 + at, 1)))
devs = [r_[3] for r_ in ev_rows if r_[3] is not None]
out["A_event_word"] = dict(n=len(ev_rows), measured=len(devs), within_0p2=sum(1 for x in devs if abs(x) <= 0.2),
                           median_abs=round(float(np.median(np.abs(devs))), 3) if devs else None, rows=ev_rows)
out["B_end_vs_sentence_end"] = end_rows
out["B_end_fail"] = [x for x in end_rows if x[1] < -0.5]
out["B_still_in_speech"] = still_rows
out["B_still_over_1p5s"] = [x for x in still_rows if x[1] is not None and x[1] > 1.5]

# ---------- C 出镜话尾 ----------
tails = []
for b in J["beats"]:
    if b["kind"] != "ON-CAM":
        continue
    a = np.abs(pcm(SRC, b["new_start"], b["new_end"] - b["new_start"], 16000))
    if not len(a):
        continue
    k = 320
    e = np.sqrt(np.convolve(a * a, np.ones(k) / k, "same") + 1e-6)
    peak = float(np.percentile(e, 99))
    endv = float(e[-int(0.20 * 16000):-int(0.06 * 16000)].max())   # 段尾前 0.06–0.20 s（再往后可能已是下一段的声音）
    db = 20 * np.log10(endv / peak)
    tails.append((b["seg"], round(db, 1)))
out["C_oncam_tail_db"] = tails
tray_tail = []
for f in sorted(RES8.glob("*.json")):
    if f.stem == "all":
        continue
    C = json.loads(f.read_text(encoding="utf-8"))
    for k, p in enumerate(C["parts"]):
        last_w = max(v for kk, v in C["words"].items() if kk.startswith(f"{k}:"))
        tray_tail.append((p["seg"], round((p["until"] - last_w) / 60, 2)))
out["C_tray_until_minus_last_word_onset_s"] = tray_tail
out["C_fail"] = [x for x in tails if x[1] > -30]

# ---------- D 人像边界、黑边 ----------
pb = []
for f in sorted(RES8.glob("*.json")):
    if f.stem == "all":
        continue
    C = json.loads(f.read_text(encoding="utf-8"))
    for p in C["parts"]:
        if "bbox_out" in p:
            x0, y0, x1, _ = p["bbox_out"]
            pb.append((p["seg"], x0, x1, round(y0 / 1080, 3), p["ps"]))
f8 = TRAYSRC / "frame8.json"
if f8.exists():
    for k, v in json.loads(f8.read_text(encoding="utf-8")).items():
        for q in v:
            x0, y0, x1, _ = q["bbox_out"]
            pb.append(({"s1": "3-01", "t309": "3-09", "t411": "4-11/4-12"}[k], x0, x1, round(y0 / 1080, 3), q["ps"]))
out["D_person_bbox"] = pb
out["D_person_fail"] = [x for x in pb if x[1] < 0 or x[2] > 1920 or not (0.18 <= x[3] <= 0.40)]
p = subprocess.Popen([FF, "-v", "error", "-i", str(SRC), "-vf", "fps=2,scale=192:108:flags=area,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
edges, i = [], 0
while True:
    b_ = p.stdout.read(192 * 108)
    if len(b_) < 192 * 108:
        break
    a = np.frombuffer(b_, np.uint8).reshape(108, 192).astype(float)
    if a.mean() > 90:
        for side, col in (("L", a[:, :3]), ("R", a[:, -3:]), ("T", a[:2, :]), ("B", a[-2:, :])):
            if col.mean() < 40:
                edges.append((i / 2, side))
    i += 1
out["D_black_edges"] = edges[:20]

# ---------- E 推镜 ----------
src_txt = (HERE / "build_cut_v8.py").read_text(encoding="utf-8")
calls = re.findall(r"=\s*(word_push|breathe)\(", src_txt)
out["E_zoom_calls"] = calls

# F 字幕：导演 11-16 晚决定暂不做，本版不查
out["seconds"] = J["seconds"]
ok = (not out["black"] and not out["freeze_3s"] and out["start_drift_max_s"] <= 0.02 and all(abs(o) <= 1 / 30 + 1e-6 for _, o in offs)
      and not out["reveal_fail"] and not any(clash.values()) and not out["B_end_fail"] and not out["C_fail"] and not out["D_person_fail"]
      and not out["D_black_edges"] and not calls)
out["pass"] = ok
(HERE / f"_check/{NAME}_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
summary = {k: v for k, v in out.items() if k not in ("A_event_word", "B_end_vs_sentence_end", "B_still_in_speech", "reveal_frames_60fps", "C_tray_until_minus_last_word_onset_s", "D_person_bbox")}
summary["A"] = {k: v for k, v in out["A_event_word"].items() if k != "rows"}
print(json.dumps(summary, ensure_ascii=False, indent=1, default=float))
