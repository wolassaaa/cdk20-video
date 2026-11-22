"""HKBU SCIE1007 课程作业的科普视频：停顿裁剪（trim_pauses.py）和总表 v2 的检查（17 文档任务单 T1；19 文档 7.3）。

T1 各项：
  T1 段长      每段裁好的声音正好少了各刀之和（采样数），总表 v2 的段长 = v1 − 各刀帧数之和
  T2 词        全片每个词自己的长度（帧、秒）不变；词序（wid 序列）不变；被裁段的词正好前移它前面各刀之和
  T3 声音      每个词在裁好的声音里的采样和原声逐位相同（交叉区以外）；被删掉的地方都在登记的停顿里、离词边界 ≥ 60 ms
  T4 切口      切口（交叉区和两边各 5 ms）相邻采样差 ≤ 0.1（满幅 1.0）
  T5 别的段    没裁的段：段内词帧、句帧、段长和 v1 一帧不差
  T6 总表检查  check_master.py 对 master_v2：C1–C4 全过；C5、C6 的不过项和 v1 完全相同（v1 就有、在没裁的段里），没有新增
用法：python -X utf8 镜头设计_v3/映射/check_trim.py [--no-master]    （check_master 用 _env/footage 的 python 跑）
出：映射/_reports/check_trim.json；退出码 0 = 全过
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import trim_pauses as TP  # noqa: E402

FPS, SR, SPF, H = TP.FPS, TP.SR, TP.SPF, TP.H
FOOT_PY = ROOT / "_env/footage/Scripts/python.exe"
R = {}


def res(k, ok, msg):
    R[k] = [bool(ok), msg]
    print(f"{'过  ' if ok else '不过'} {k}：{msg}")


def wav(p):
    with wave.open(str(p), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())


def main():
    T1 = json.loads(TP.V1.read_text(encoding="utf-8"))
    T2 = json.loads(TP.V2.read_text(encoding="utf-8"))
    G1 = {g["group"]: g for g in T1["groups"]}
    G2 = {g["group"]: g for g in T2["groups"]}
    trims = {p.stem[5:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted(TP.OUT.glob("trim_*.json"))}
    listed = {r["seg"] for r in TP.read_list()}
    bad1, bad2, bad3, bad4, bad5 = [], [], [], [], []
    worst_step = 0.0
    if set(trims) != listed:
        bad1.append(f"trim json 的段 {sorted(set(trims) ^ listed)} 和清单对不上")
    if [g["group"] for g in T1["groups"]] != [g["group"] for g in T2["groups"]]:
        bad2.append("段的顺序变了")
    for name, g1 in G1.items():
        g2 = G2[name]
        w1, w2 = g1["words"], g2["words"]
        if [w["wid"] for w in w1] != [w["wid"] for w in w2]:
            bad2.append(f"{name} 词序变了")
            continue
        for a, b in zip(w1, w2):
            if a["f1"] - a["f0"] != b["f1"] - b["f0"] or abs((a["t1"] - a["t0"]) - (b["t1"] - b["t0"])) > 2e-4:
                bad2.append(f"{a['wid']} 词长变了")
        tr = trims.get(name.replace("+", "_"))
        if not tr:
            if g1["len_f"] != g2["len_f"] or any(a["f0"] != b["f0"] or a["f1"] != b["f1"] for a, b in zip(w1, w2)) \
                    or any((a["f0"], a["f1"]) != (b["f0"], b["f1"]) for a, b in zip(g1["sentences"], g2["sentences"])):
                bad5.append(name)
            continue
        cuts = tr["cuts"]
        tot_f = sum(c["del_f"] for c in cuts)
        tot_s = sum(c["del_samples"] for c in cuts)
        x = wav(TP.SRC / f"{name}.wav")
        y = wav(TP.OUT / f"{name}.wav")
        if len(y) != len(x) - tot_s or tr["samples_out"] != len(y):
            bad1.append(f"{name} 声音 {len(x)} → {len(y)} 采样，应少 {tot_s}")
        if g2["len_f"] != g1["len_f"] - tot_f:
            bad1.append(f"{name} 总表段长 {g1['len_f']} → {g2['len_f']}，应少 {tot_f}")
        # 词前移量 = 它前面各刀之和；词的采样逐位相同
        for a, b in zip(w1, w2):
            n = sum(c["del_f"] for c in cuts if c["e"] <= a["t0"] * SR)
            if a["f0"] - b["f0"] != n or a["f1"] - b["f1"] != n:
                bad2.append(f"{a['wid']} 前移 {a['f0'] - b['f0']} 帧，应 {n}")
            s0, s1 = int(round(a["t0"] * SR)), int(round(a["t1"] * SR))
            d = n * SPF
            if s1 <= len(x) and s1 - d <= len(y) and not np.array_equal(x[s0:s1], y[s0 - d:s1 - d]):
                bad3.append(f"{a['wid']}（{a['w']}）在裁好的声音里不一样")
        # 删掉的地方：在登记的停顿里、离词边界 ≥ 60 ms
        for c in cuts:
            wa = next(w for w in w1 if w["wid"] == c["words"][0])
            wb = next(w for w in w1 if w["wid"] == c["words"][1])
            if c["s"] - H < (wa["t1"] + TP.EDGE) * SR - 1 or c["e"] + H > (wb["t0"] - TP.EDGE) * SR + 1:
                bad3.append(f"{name} {c['text']}：切口离词边界不到 60 ms")
            if (wa["f1"], wb["f0"]) != (c["list_a"], c["list_b"]):
                bad3.append(f"{name} {c['text']}：不是清单登记的那处停顿")
        # 切口相邻采样差
        yf = y.astype(np.float32) / 32768.0
        pos_out, pos_in = 0, 0
        for c in cuts:
            pos_out += c["s"] - H - pos_in
            a, b = max(1, pos_out - 240), min(len(yf), pos_out + 2 * H + 240)
            step = float(np.abs(np.diff(yf[a - 1:b], axis=0)).max())
            worst_step = max(worst_step, step)
            if step > 0.1:
                bad4.append(f"{name} 切口 {c['t_s']} s：相邻采样差 {step:.3f}")
            pos_out += 2 * H
            pos_in = c["e"] + H
    res("T1 段长", not bad1, f"{len(trims)} 段，每段少的正好是各刀之和（采样、帧都对）" if not bad1 else "；".join(bad1[:8]))
    res("T2 词", not bad2, f"{sum(len(g['words']) for g in T1['groups'])} 个词长度、词序都不变，被裁段的词前移量 = 前面各刀之和" if not bad2 else "；".join(bad2[:8]))
    res("T3 声音", not bad3, "每个词的采样和原声逐位相同；65 刀都在登记的停顿里、离词边界 ≥ 60 ms" if not bad3 else "；".join(bad3[:8]))
    res("T4 切口", not bad4, f"相邻采样差最大 {worst_step:.4f}（上限 0.1）" if not bad4 else "；".join(bad4[:8]))
    res("T5 别的段", not bad5, f"没裁的 {len(G1) - len(trims)} 段段内帧和 v1 一帧不差" if not bad5 else f"变了：{bad5}")
    if "--no-master" not in sys.argv:
        base = HERE / "_reports/_v1基线_1122"
        base.mkdir(parents=True, exist_ok=True)
        r1 = subprocess.run([FOOT_PY, "-X", "utf8", HERE / "check_master.py", "--map", "master_v1.json", "--out", base], capture_output=True, text=True, encoding="utf-8", errors="replace")
        r2 = subprocess.run([FOOT_PY, "-X", "utf8", HERE / "check_master.py", "--map", "master_v2.json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        C1 = json.loads((base / "report_v1.json").read_text(encoding="utf-8"))["checks"]
        C2 = json.loads((HERE / "report_v2.json").read_text(encoding="utf-8"))["checks"]
        main_ok = all(C2[k]["pass"] for k in ("C1_time_base", "C2_repeated_words", "C3_missing_words", "C4_cross_sentence"))
        same = all(json.dumps(C1[k].get(f), sort_keys=True) == json.dumps(C2[k].get(f), sort_keys=True)
                   for k, f in (("C5_frame_bounds", "list"), ("C6_event_word_2f", "fails")))
        untrimmed = all(x[1] not in trims for x in C2["C5_frame_bounds"]["list"]) and \
            all(x[0].replace("+", "_") not in trims for x in C2["C6_event_word_2f"]["fails"])
        c1 = C2["C1_time_base"]
        res("T6 总表检查", main_ok and same and untrimmed and r2.returncode in (0, 1),
            f"check_master v2：C1–C4 全过（C1 逐词在裁过的 cut 声音里复核 {c1['per_word_checked']} 个，最大偏差 {c1['per_word_dev_max_f']} 帧）；"
            f"C5 {'过' if C2['C5_frame_bounds']['pass'] else '不过 ' + str(C2['C5_frame_bounds']['list'])}、"
            f"C6 {'过' if C2['C6_event_word_2f']['pass'] else '不过 ' + str(C2['C6_event_word_2f']['fails'])}，"
            f"{'和 v1 完全相同（旧托盘事件，没裁的段），没有新增' if same and untrimmed else '和 v1 不同！'}")
    ok = all(v[0] for v in R.values())
    out = HERE / "_reports/check_trim.json"
    out.write_text(json.dumps(dict(results=R, pass_=ok, worst_step=worst_step), ensure_ascii=False, indent=1), encoding="utf-8")
    print("总判：", "全过" if ok else "有不过项", "→", out)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
