"""HKBU SCIE1007 课程作业的科普视频：v6 对时段内秒 → v8 段内秒（经源片秒换算）。accent_v8.py、serif_fix_v8.py 用。"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def v6_to_v8(seg, t6):
    B6 = json.loads((HERE / "beats" / f"{seg}.json").read_text(encoding="utf-8"))
    src = None
    for p in B6["retime"]:
        if p["out0"] <= t6 <= p["out1"]:
            src = p["src0"] + (t6 - p["out0"]) * p["speed"]
            break
    if src is None:
        src = B6["retime"][-1]["src1"]
    S = json.loads((HERE / "beats_v8" / f"{seg}.json").read_text(encoding="utf-8"))["src_s"]
    fin = json.loads((HERE / "beats_v8" / f"{seg}.json").read_text(encoding="utf-8"))["source"]["fin"]
    s_abs = src                       # v6 retime 的 src 是段首起的秒，v8 src_s 也是段首起
    for j, s in enumerate(S):
        if s >= s_abs:
            return round(j / 30, 3)
    return round(len(S) / 30, 3)
