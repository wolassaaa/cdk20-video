"""HKBU SCIE1007 课程作业的科普视频：把 S1 画外音的词级时间换算到粗剪 cut_v3 的时间轴。
换算照 build_cut.condense：头部裁到首词前 0.15 s；超过 pmax 的停顿压到 pkeep，每个接口再吃掉 xfade 秒。
出 words_S1.json：{段: [{w, t0, t1}]}，时间是 cut_v3.mp4 里的秒。"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
CUT = HERE.parent
ROOT = CUT.parent.parent
cut = json.loads((CUT / "cut_v3.json").read_text(encoding="utf-8"))
R = cut["rules"]
TIGHT = {"1-09"}
items = {}
for p in "ABCD":
    for it in json.loads((ROOT / "素材流程_out" / p / "5_place/place.json").read_text(encoding="utf-8"))["items"]:
        items[it["name"]] = it
out = {}
for b in cut["beats"]:
    if b["kind"] != "VO" or b["seg"] not in ("1-02", "1-04", "1-08", "1-09", "1-10", "1-11"):
        continue
    w = items[b["take"]]["words"]
    pmax, pkeep = (0.9, 0.5) if b["seg"] in TIGHT else (R["pause_max"], R["pause_keep"])
    half = pkeep / 2
    cuts = [(a["t1"] + half, c["t0"] - half) for a, c in zip(w, w[1:]) if c["t0"] - a["t1"] > pmax]
    s0 = max(0.0, w[0]["t0"] - R["head"])
    def m(t):
        return b["new_start"] + t - s0 - sum((c1 - c0) + R["xfade"] for c0, c1 in cuts if c1 <= t)
    out[b["seg"]] = [dict(w=x["w"], t0=round(m(x["t0"]), 3), t1=round(m(x["t1"]), 3)) for x in w]
    print(b["seg"], b["new_start"], "cuts", [(round(a, 2), round(c, 2)) for a, c in cuts], "pause_cut", b["pause_cut"])
(HERE / "words_S1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for s, ws in out.items():
    print(s, " ".join(f"{x['w']}@{x['t0']:.2f}" for x in ws))
