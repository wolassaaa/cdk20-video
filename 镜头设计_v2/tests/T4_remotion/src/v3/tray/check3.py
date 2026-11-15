"""HKBU SCIE1007 课程作业的科普视频。托盘样板 1–3 机器检查（下一步方案_20261116 第 3.3 节的过关线）。
用法：python check3.py <样板目录>     读 样板1_3-01_v2.mp4、样板2_4-11_4-12_v2.mp4、样板3_3-09_v2.mp4 和 _work 里的穿模记录，写 _work/检查_v2.json 并打印表。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("D:/。hkbu/molecular science")
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
HERE = Path(__file__).resolve().parent
D = Path(sys.argv[1])
WK = D / "_work"
S = json.load(open(HERE / "sample3.json", encoding="utf-8"))
B2 = json.load(open(HERE / "beats2.json", encoding="utf-8"))
FUS = ROOT / "镜头设计_v3/styleframes/art/fusion"
Y = np.array([0.2126, 0.7152, 0.0722], np.float32)


def frames(mp4, w=960, h=540):
    raw = subprocess.run([FF, "-v", "error", "-i", str(mp4), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def img(path_or_args, w=960, h=540):
    if isinstance(path_or_args, Path):
        return np.asarray(Image.open(path_or_args).convert("RGB").resize((w, h)), np.uint8)
    raw = subprocess.run([FF, "-v", "error", *path_or_args, "-frames:v", "1", "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def diff(a, b):
    return round(float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()), 2)


def gaps(actions, a, b):
    iv = sorted((s, e) for _, s, e in actions)
    out, last = [], a
    for s, e in iv:
        if s > last:
            out.append(s - last)
        last = max(last, e)
    if b > last:
        out.append(b - last)
    return max(out or [0])


def common(fr, paper, start, nxt):
    lum = (fr.astype(np.float32) @ Y).mean(axis=(1, 2))
    return dict(frames=len(fr), seconds=round(len(fr) / 60, 2), min_luma_ratio=round(float(lum.min() / paper), 3),
                join_in=diff(start, fr[0]), join_out=diff(fr[-1], nxt))


rep = {}
# ---------------- 样板 1（试片 v2 的帧，时间线 84–466）
fr = frames(D / "样板1_3-01_v2.mp4")
paper = float((img(ROOT / "镜头设计_v3/粗剪/样片/托盘试片1/_work2/public/plate.mp4", ) if False else img(["-i", str(ROOT / "镜头设计_v3/粗剪/样片/托盘试片1/_work2/public/plate.mp4")])).astype(np.float32).dot(Y).mean())
start = img(["-ss", "280.98", "-i", str(FUS / "s1/inserts/S1S2_table_3_1080_v2.mp4")])           # 2-08 末帧（试片 v2 的拉远起点同一帧）
nxt = img(["-ss", "4.0", "-i", str(FUS / "s1/inserts/S3_all_nocards_1080_v2.mp4")])             # 3-02 画面第一帧
r = common(fr, paper, start, nxt)
T, w = B2["t301"], B2["words_301"]
tk = json.load(open(ROOT / "镜头设计_v3/粗剪/样片/托盘试片1/_work2/track.json"))
r.update(landing_max_diff=max(abs(a["land"] - (T + w[a["word"]])) for a in B2["actions"] if a.get("word")),
         max_object_gap=gaps([(a["name"], a["start"], a["land"]) for a in B2["actions"]], 108, 443),
         person_to_first_word=T + w["Okay"] - B2["person_in"][1], last_word_to_push=B2["push"][0] - (T + w["end"]),
         objects_in_person_half=len([1 for t in tk if 108 <= t["f"] < 443 for k in ("lock", "key", "target", "route", "rims") if k in t and t[k][0] < 860 and t[k][3] > 0]),
         objects_below_930=len([1 for t in tk if 84 <= t["f"] < 467 for k in ("lock", "key", "target", "route") if k in t and t[k][3] > 930 and t[k][1] < 1080]),
         clash_frames=len([1 for t in tk if 84 <= t["f"] < 467 and any(k.startswith("clash") for k in t)]), min_text_px=60)
rep["样板1_3-01"] = r

# ---------------- 样板 2、3
for name, fn, nxt_src in (("t411", "样板2_4-11_4-12_v2.mp4", None), ("t309", "样板3_3-09_v2.mp4", None)):
    C = S[name]
    fr = frames(D / fn)
    pub = WK / f"pub_{name}"
    paper = float(img(["-i", str(pub / "plate0.mp4")]).astype(np.float32).dot(Y).mean())
    r = common(fr, paper, img(pub / "start.png"), img(pub / "end.png"))
    W = C["words"]
    r["landing_max_diff"] = max(abs(f - W[wd]) for _, wd, f in C["landings"])
    r["max_object_gap"] = gaps(C["actions"], C["pull"][1], C["push"][0])
    r["person_to_first_word"] = min(v for k, v in W.items() if not k.startswith("end")) - C["person_in"][1]
    last = max(v for k, v in W.items() if k == "end")
    r["last_word_to_push"] = C["push"][0] - last
    rows = json.load(open(WK / f"clash_{name}.json"))
    parts = C.get("parts") or [dict(at=0, until=C["frames"], person_side=C["person_side"])]
    bad = 0
    below = 0
    for t in rows:
        if t["f"] >= C["push"][0]:
            continue
        p = next(p for p in parts if p["at"] <= t["f"] < p["until"])
        for k, b in t["box"].items():
            if b[3] < 0 or b[1] > 1080:
                continue
            if (p["person_side"] == "left" and b[0] < 860) or (p["person_side"] == "right" and b[2] > 1060):
                bad += 1
            if b[3] > 930:
                below += 1
    if name == "t411":                         # 正反打：A 段第一帧（cut）人立刻在画面里，开口 Not 的帧
        r["cut_to_A_first_word"] = W["Not"] - C["cut"]
    r["objects_in_person_half"] = bad
    r["objects_below_930"] = below
    r["clash_frames"] = len([t for t in rows if t["clash"]])
    r["min_text_px"] = min(n["size"] for n in C["notes"])
    rep[{"t411": "样板2_4-11_4-12", "t309": "样板3_3-09"}[name]] = r

PASS = dict(landing_max_diff=lambda v: v <= 3, max_object_gap=lambda v: v <= 90, objects_in_person_half=lambda v: v == 0, min_luma_ratio=lambda v: v >= 0.35,
            person_to_first_word=lambda v: v >= 6, cut_to_A_first_word=lambda v: v >= 6, last_word_to_push=lambda v: v >= 4, join_in=lambda v: v <= 8, join_out=lambda v: v <= 8,
            min_text_px=lambda v: v >= 56, objects_below_930=lambda v: v == 0, clash_frames=lambda v: v == 0)
for k, r in rep.items():
    r["fails"] = [x for x, ok in PASS.items() if x in r and not ok(r[x])]
json.dump(rep, open(WK / "检查_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, r in rep.items():
    print(k, json.dumps(r, ensure_ascii=False))
