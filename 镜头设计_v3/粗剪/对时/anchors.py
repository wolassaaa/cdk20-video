"""HKBU SCIE1007 课程作业的科普视频：S1 画面动作 ↔ 台词词的锚点表和分段变速表。
输入 motion_S1.npy（motion.py）、words_S1.json（words_in_cut.py）、../cut_v3.json。
出 S1_锚点.json 和 S1_锚点表.md 的表格部分（打印到 stdout，再贴进 md）。"""
import json, numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent
d = np.load(H / "motion_S1.npy"); FPS = 30
W = json.loads((H / "words_S1.json").read_text(encoding="utf-8"))
B = {b["seg"]: b for b in json.loads((H.parent / "cut_v3.json").read_text(encoding="utf-8"))["beats"]}
# (段, 动作, 粗剪里的秒（正数 = 抽帧估计、帧差细调；负数 = 字区实测）, 对应词, 第几次出现) ；词 None = 没有对应台词
A = {
 "1-02": [("肝脏淡入", 8.5, "That's", 1), ("大字 1,412 写出", -9.1, "1,412", 1), ("deaths in Hong Kong, 2022 出现", 9.9, "2022", 1),
          ("四个小人依次变红（about four a day）", 10.4, "alone.", 1), ("门静脉开始充红", 12.6, "Here,", 1), ("Top 3 deadliest in HK 出现", 12.9, "three", 1),
          ("lung · colorectal · liver 出现", 13.4, "lung", 1), ("肝静脉变蓝 + hepatic veins 标签", 16.8, "not", 1),
          ("World: 6th most common 出现", 20.0, "sixth", 1), ("3rd deadliest 出现", 20.8, "third", 1), ("放大镜圆圈出现", 21.5, None, 0),
          ("整段字淡出", 24.9, "deadliest.", 1)],
 "1-04": [("药板落进画面", 32.9, "treatment", 1), ("药片顶破铝箔", 33.9, "changed", 1), ("叠字 Nexavar", 33.4, "Nexavar", 1),
          ("药瓶贴镜头落下盖全屏", 35.3, "to", 1), ("atezolizumab 写出", 35.9, "atezolizumab", 1), ("+ bevacizumab 写出", 36.4, "bevacizumab.", 1),
          ("镜头升回全景（两图标 + 箭头）", 38.0, "But", 1), ("十个人从左依次变红", 41.4, "ten", 1), ("镜头落进人排，人立起", 43.9, "patients", 1),
          ("七个灰的躺下", 45.3, "alive", 1), ("~3 in 10 写出", -46.8, "five", 1), ("镜头升回全景", 47.6, "The", 2), ("画面左移出场", 51.2, "need.", 1)],
 "1-08": [("三张人形纸卡（另一人在删，可裁）", 60.7, "Start", 1), ("时间轴刻度 10 出现", 64.0, "might", 1), ("四个人形小人在 17 处立起", 65.0, "ready", 1),
          ("10–17 years 标注", 66.7, "now.", 1), ("十个圆点出现", 67.9, "It", 1), ("~US$2.8 billion 写出", 68.1, "2.8", 1),
          ("圆点依次变红", 70.3, "drugs", 1), ("九个点褪成灰", 73.2, "one", 1), ("about 1 in 10 写出", 73.9, "ten", 1), ("reaches the market 写出", 74.8, "reaches", 1)],
 "1-09": [("六站路线图出现", 77.3, "To", 1), ("红液走到第一站", 78.5, "journey.", 1), ("镜头落到台面（3D 玻璃泡）", 80.2, "Every", 1),
          ("Target 标签", -81.6, "target.", 1), ("Hit 标签 + 第二泡变红", -82.8, "hit,", 1), ("Improve 标签", -85.2, "Improve", 1),
          ("Cells & animals 标签", -86.5, "cells,", 1), ("Clinical trials 1-2-3 标签", -89.0, "trials:", 1), ("Approval 标签", -92.5, "approval.", 1),
          ("镜头升回全景", 93.2, "Any", 1), ("Any step can fail. 出现", 94.0, "can", 1), ("红液退回第一站", 96.0, "fail.", 1)],
 "1-10": [("路线重画成一条 L 线", 101.0, "Now", 1), ("CDK20 模型开始长出", 102.0, "AlphaFold,", 1), ("predicted 标签", 103.9, "predicts", 1),
          ("Nobel Prize 写出", -104.0, "Nobel", 1), ("in Chemistry", -104.4, "Chemistry", 1), ("2024", -104.8, "2024,", 1),
          ("Demis Hassabis", -106.4, "Demis", 1), ("John Jumper", -106.9, "John", 1), ("红色尾链长出", 107.3, "proteins.", 1)],
 "1-11": [("香港地图出现", 115.3, "So", 1), ("红线开始画", 116.4, "follow", 1), ("镜头推近", 120.4, "And", 1),
          ("Sha Tin 标签", 122.9, "here,", 1), ("Pak Shek Kok 标签", 124.9, "Kong.", 1)],
}
def refine(t, lo, hi):
    """抽帧（每 0.5 s）给的大约时间 ±0.3 s 内，取帧差上升最陡的一帧当动作开始。"""
    a, b = max(int((t - 0.3) * FPS), int(lo * FPS) + 1), min(int((t + 0.3) * FPS), int(hi * FPS) - 1)
    jump = d[a:b] - d[a - 1:b - 1]
    if len(jump) == 0 or jump.max() < 0.01: return round(t, 1)
    return round((a + int(np.argmax(jump))) / FPS, 1)
def word(seg, w, n):
    k = 0
    for x in W[seg]:
        if x["w"] == w:
            k += 1
            if k == n: return x["t0"]
    raise KeyError((seg, w, n))
out = {"note": "HKBU SCIE1007 课程作业的科普视频。时间都是 cut_v3.mp4 的秒；src 是 S1S2_table_2.mp4 文件内的秒（= old_start + cut − new_start）。",
       "segments": {}}
for seg, rows in A.items():
    b = B[seg]; ns, os_, oe = b["new_start"], b["old_start"], b["old_end"]
    pic_end = ns + (oe - os_)
    aud_end = W[seg][-1]["t1"]
    R = []
    for act, t, w, n in rows:
        t = -t if t < 0 else refine(t, ns, pic_end)   # 负数 = 已按字区深色像素实测，不再细调
        wt = word(seg, w, n) if w else None
        R.append(dict(action=act, cut_t=t, src_t=round(os_ + t - ns, 2), word=w, word_t=wt,
                      offset=round(t - wt, 2) if wt is not None else None))
    # 能当锚点的：有词、按词时间单调（最长上升子序列）
    idx = [i for i, r in enumerate(R) if r["word_t"] is not None]
    idx.sort(key=lambda i: R[i]["src_t"])
    best = []
    for i in idx:   # O(n^2) LIS on word_t
        cand = [c for c in best if R[c[-1]]["word_t"] < R[i]["word_t"] - 0.15]
        best.append((max(cand, key=len) if cand else []) + [i])
    keep = set(max(best, key=len))
    for i, r in enumerate(R):
        r["anchor"] = i in keep
    offs = [r["offset"] for r in R if r["offset"] is not None]
    last_act = max(r["cut_t"] for r in R)
    out["segments"][seg] = dict(new_start=ns, src_start=os_, src_end=oe, picture_end_cut=round(pic_end, 2), audio_first_word=W[seg][0]["t0"],
                                audio_end_cut=aud_end, mean_offset=round(float(np.mean(offs)), 2), mean_abs_offset=round(float(np.mean(np.abs(offs))), 2),
                                max_offset=max(offs, key=abs), actions=R)
# 变速表：锚点 (src → 词时间)，段头尾补边界
for seg, S in out["segments"].items():
    pts = [(S["src_start"] if seg != "1-08" else 64.0 - 0.3, S["audio_first_word"] - 0.15)]
    if seg == "1-08": pts[0] = (63.4 + 0.0, S["audio_first_word"] - 0.15)   # 1-08 先裁掉 60–63.4 的纸卡
    for r in sorted([r for r in S["actions"] if r["anchor"]], key=lambda r: r["src_t"]):
        if r["src_t"] > pts[-1][0] + 0.1 and r["word_t"] > pts[-1][1] + 0.1:
            pts.append((r["src_t"], r["word_t"]))
    out_end = S["audio_end_cut"] + 0.25
    end_src = min(S["src_end"], pts[-1][0] + (out_end - pts[-1][1]))   # 最后一个锚点后按 1.0× 放，到声音完 +0.25 s 为止，多余的画面裁掉
    S["tail_cut_src"] = round(S["src_end"] - end_src, 2)
    pts.append((end_src, out_end))
    S["retime"] = [dict(src0=round(a[0], 2), src1=round(b[0], 2), out0=round(a[1], 2), out1=round(b[1], 2),
                        speed=round((b[0] - a[0]) / (b[1] - a[1]), 2),
                        flag=("慢，60 fps 交片要补帧" if (b[0] - a[0]) / (b[1] - a[1]) < 0.6 else "快，看得出赶" if (b[0] - a[0]) / (b[1] - a[1]) > 1.6 else "")) for a, b in zip(pts, pts[1:]) if b[1] > a[1]]
(H / "S1_锚点.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for seg, S in out["segments"].items():
    print(f"\n### {seg}\n\n画面 {S['new_start']}–{S['picture_end_cut']}（此后末帧停住），声音 {S['audio_first_word']}–{S['audio_end_cut']}。"
          f"平均偏差 {S['mean_offset']:+.1f} s（绝对值平均 {S['mean_abs_offset']:.1f} s），最大 {S['max_offset']:+.1f} s。\n")
    print("| 动作 | 画面时间 | 对应词 | 词时间 | 偏差 | 处理 |\n|---|---|---|---|---|---|")
    for r in S["actions"]:
        h = "锚点" if r["anchor"] else ("无台词，跟前后锚点走" if r["word"] is None else "和别的锚点顺序冲突，不作锚点，跟着走")
        print(f"| {r['action']} | {r['cut_t']:.1f} | {r['word'] or '—'} | {'' if r['word_t'] is None else f'{r[chr(119)+chr(111)+chr(114)+chr(100)+chr(95)+chr(116)]:.2f}'} | "
              f"{'' if r['offset'] is None else f'{r[chr(111)+chr(102)+chr(102)+chr(115)+chr(101)+chr(116)]:+.1f}'} | {h} |")
    print("\n变速：" + "；".join(f"src {x['src0']}–{x['src1']} → {x['out0']}–{x['out1']} ×{x['speed']}{'（'+x['flag']+'）' if x['flag'] else ''}" for x in S["retime"]) + f"；尾部裁掉 src {S['tail_cut_src']} s")
