"""HKBU SCIE1007 课程作业的科普视频：总表（映射/master_v1.json）的机器检查和覆盖/缺项报告。

检查项（每项 pass / fail，加明细）：
  C1 时间基准   段首尾相接（≤1 帧）；词按时间排、在段内；全片秒 = 段起点 + 段内秒；每个词都被录音核对过（ncc ≥ 0.6）；
                按 cut_v8 代码预测的词时刻和实测差 ≤1 帧；逐词复核（每个 ≥0.12 s 的词单独在 cut 声音 ±0.1 s 里再找一次）≤1 帧
  C2 重复词     wid 全片唯一；key（词#第几次）段内唯一；同一个词出现多次的都各有 ID
  C3 缺词       剧本 v3.3 的词录音里没有的、录音里多出来的
  C4 跨句       句不重叠、按顺序；挂在某句词上的 primary 落点在这句里（±2 帧）；在上一句开口前就起动的只列出（镜头长推这类有意的，不判不过）
  C5 帧边界     帧号是整数、在段内；f_start ≤ f_land ≤ f_end；全片帧 = 段起点帧 + 段内帧（±1）
  C6 事件对词   每串事件里挂词的 primary 落点离词开口 ≤2 帧（stagger 是有意错开的跟随拍，单列）
  C7 覆盖       每句：有没有原生按表生成的画面事件、落在这句词上的 primary 数、句内最长没有事件的空档、事件有没有持续到句尾
用法：_env/footage/Scripts/python.exe 镜头设计_v3/映射/check_master.py
出：映射/report_v1.json、映射/覆盖与未决_v1.md（再用 _env/tools/md2html.py 出 .html 给导演看）。退出码：C1–C6 全过 0，否则 1。
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_master as BM  # noqa: E402

FPS = 60
T = json.loads((HERE / "master_v1.json").read_text(encoding="utf-8"))
GROUPS = T["groups"]
NATIVE_IN_CUT = {"native_tray"}                       # cut_v8 里画面就是按事件原生 60 帧出的
NATIVE_SRC = {"native_tray", "native_blender_rewarped"}  # 源片按事件原生出，但 cut_v8 里可能又重铺过
R = {}


def res(key, ok, **kw):
    R[key] = dict(pass_=bool(ok), **kw)
    print(f"{key}: {'通过' if ok else '不过'}  " + "  ".join(f"{k}={v}" for k, v in kw.items() if not isinstance(v, (list, dict)))[:300])


# ---------------------------------------------------------------- C1
def c1():
    gaps, order, cons, unv, pdev = [], [], [], [], []
    for a, b in zip(GROUPS, GROUPS[1:]):
        d = b["cut_start_f"] - (a["cut_start_f"] + a["len_f"])
        if abs(d) > 1:
            gaps.append((a["group"], b["group"], d))
    for g in GROUPS:
        ws = g["words"]
        for x, y in zip(ws, ws[1:]):
            if y["t0"] < x["t0"] - 1e-6:
                order.append((g["group"], x["wid"], y["wid"]))
        for w in ws:
            if not (-0.02 <= w["t0"] <= g["len_s"] + 0.02 and w["t1"] <= g["len_s"] + 0.3):
                order.append((g["group"], w["wid"], "出段", w["t0"], g["len_s"]))
            if abs(w["g0"] - (g["cut_start_s"] + w["t0"])) > 1e-3:
                cons.append(w["wid"])
            if not w["verified"]:
                unv.append(w["wid"])
            if "pred_dev_f" in w:
                pdev.append(abs(w["pred_dev_f"]))
    # 逐词复核
    A = BM.cut_audio()
    takes = BM.BC.takes()
    by = {it["name"]: it for v in takes.values() for it in v}
    devs, bad, n = [], [], 0
    for g in GROUPS:
        for w in g["words"]:
            if w["src"]["t1"] - w["src"]["t0"] < 0.12:
                continue
            it = by[w["src"]["take"]]
            x = BM.take_audio(it)
            s0, s1 = w["src"]["t0"], w["src"]["t1"]
            snip = x[int(s0 * BM.SR):int(s1 * BM.SR)]
            w0 = w["g0"] - 0.1
            k, r = BM.ncc_search(snip, A[int(w0 * BM.SR):int((w["g0"] + (s1 - s0) + 0.1) * BM.SR)])
            found = int(w0 * BM.SR) / BM.SR + k / BM.SR
            dv = (found - w["g0"]) * FPS
            n += 1
            if r >= 0.5:
                devs.append(abs(dv))
                if abs(dv) > 1:
                    bad.append((w["wid"], round(dv, 2), round(r, 2)))
    d = np.array(devs)
    res("C1_time_base", not gaps and not order and not cons and not unv and (max(pdev or [0]) <= 1) and not bad,
        group_joins_bad=len(gaps), order_bad=len(order), global_mismatch=len(cons), unverified=len(unv),
        pred_dev_max_f=round(max(pdev or [0]), 3), per_word_checked=n, per_word_dev_max_f=round(float(d.max()), 3) if len(d) else None,
        per_word_dev_p95_f=round(float(np.percentile(d, 95)), 3) if len(d) else None, per_word_bad=bad[:20], joins=gaps[:10], order=order[:10])


# ---------------------------------------------------------------- C2
def c2():
    wids = Counter(w["wid"] for g in GROUPS for w in g["words"])
    dup = [k for k, v in wids.items() if v > 1]
    keys = Counter((w["seg"], w["key"]) for g in GROUPS for w in g["words"])
    kdup = [k for k, v in keys.items() if v > 1]
    rep = Counter((w["seg"], w["norm"]) for g in GROUPS for w in g["words"])
    repeated = {f"{s}:{n}": c for (s, n), c in rep.items() if c > 1}
    # 老写法（beats_resolve 按原文带标点数第几次）和规范化写法数出来不一样的事件
    legacy = [(g["group"], e["eid"], e["ref"]["raw"], e["word"]) for g in GROUPS for e in g["events"]
              if e.get("ref") and e["ref"]["mode"] == "raw" and e["word"]
              and next(w for w in g["words"] if w["wid"] == e["word"])["key"] != (M_norm(e["ref"]["raw"].split("#")[0]) + "#" + (e["ref"]["raw"].split("#")[1] if "#" in e["ref"]["raw"] else "1"))]
    res("C2_repeated_words", not dup and not kdup, words=sum(wids.values()), wid_dup=len(dup), key_dup=len(kdup),
        repeated_word_types=len(repeated), repeated_word_tokens=sum(repeated.values()), legacy_key_differs=len(legacy),
        legacy_examples=legacy[:10], dup=dup[:10])


def M_norm(s):
    return BM.M.norm(s)


# ---------------------------------------------------------------- C3
def c3():
    miss = T["missing_script_words"]
    extra = [(g["group"], w["wid"], w["w"]) for g in GROUPS for w in g["words"] if w["match"] == "extra"]
    known = {"6-09"}                                   # build_cut SPEECH_FROM：B 开头那句没录全，从 Fewer failed molecules 开始用（11-15 记录）
    unknown = [m for m in miss if m["wid"].split(".")[0] not in known]
    res("C3_missing_words", not unknown and not extra, missing=len(miss), missing_known=len(miss) - len(unknown), missing_unknown=len(unknown),
        extra=len(extra), missing_list=[(m["wid"], m["w"]) for m in miss], extra_list=extra[:20])


# ---------------------------------------------------------------- C4
def c4():
    ov, early, cross = [], [], []
    for g in GROUPS:
        ss = g["sentences"]
        for a, b in zip(ss, ss[1:]):
            if b["t0"] < a["t1"] - 1e-6:
                ov.append((a["sid"], b["sid"]))
        sid_of = {w["wid"]: w["sid"] for w in g["words"]}
        sent = {s["sid"]: s for s in ss}
        order = [s["sid"] for s in ss]
        for e in g["events"]:
            if not e.get("word"):
                continue
            s = sent[sid_of[e["word"]]]
            i = order.index(s["sid"])
            prev_start = sent[order[i - 1]]["f0"] if i else -10 ** 9
            if e["f_start"] < prev_start:
                early.append((g["group"], e["eid"], e["f_start"], s["sid"]))
            if e["role"] != "mark" and (e["f_land"] < s["f0"] - 2 or e["f_land"] > s["f1"] + 2):
                cross.append((g["group"], e["eid"], e["role"], e["f_land"], s["sid"], s["f0"], s["f1"]))
    stag_cross = [c for c in cross if c[2] == "stagger"]
    prim_cross = [c for c in cross if c[2] != "stagger"]
    res("C4_cross_sentence", not ov and not prim_cross, sentences=sum(len(g["sentences"]) for g in GROUPS),
        overlap=len(ov), starts_before_prev_sentence=len(early), primary_land_outside_sentence=len(prim_cross),
        stagger_land_outside_sentence=len(stag_cross), early_list=early[:10], primary_cross=prim_cross[:10], stagger_cross=stag_cross[:10])


# ---------------------------------------------------------------- C5
def c5():
    bad = []
    for g in GROUPS:
        for w in g["words"]:
            if not all(isinstance(w[k], int) for k in ("f0", "f1", "G0")) or w["f1"] < w["f0"] or abs(w["G0"] - (g["cut_start_f"] + w["f0"])) > 1:
                bad.append(("word", w["wid"]))
        for e in g["events"]:
            fs = (e["f_start"], e["f_land"], e["f_end"])
            if not all(isinstance(x, int) for x in fs) or not (e["f_start"] <= e["f_land"] <= e["f_end"]):
                bad.append(("event_order", g["group"], e["eid"], fs))
            elif e["f_start"] < 0 or e["f_end"] > g["len_f"]:
                bad.append(("event_range", g["group"], e["eid"], fs, g["len_f"]))
    res("C5_frame_bounds", not bad, problems=len(bad), list=bad[:20])
    return bad


# ---------------------------------------------------------------- C6
def c6():
    per, fails, stag = defaultdict(lambda: [0, 0]), [], []
    for g in GROUPS:
        for e in g["events"]:
            if e.get("word_dev_f") is None:
                continue
            if e["role"] == "mark":
                continue
            if e["role"] == "primary":
                k = (g["group"], e["source"].split("/")[-1].split("\\")[-1])
                per[k][0] += 1
                if abs(e["word_dev_f"]) > 2:
                    per[k][1] += 1
                    fails.append((g["group"], e["eid"], e["word"], e["word_dev_f"]))
            else:
                stag.append(e["word_dev_f"])
    miss = [(g["group"], e["eid"], e["word_missing"]) for g in GROUPS for e in g["events"] if e.get("word_missing")]
    n = sum(v[0] for v in per.values())
    res("C6_event_word_2f", not fails and not miss, primary_events=n, primary_over_2f=len(fails), unresolved_word_refs=len(miss),
        stagger_events=len(stag), by_group={f"{a} ({b})": f"{v[1]}/{v[0]} 超 2 帧" for (a, b), v in per.items()}, fails=fails[:40], missing=miss)
    return fails


# ---------------------------------------------------------------- C7
def c7(fails):
    failset = {(g, e) for g, e, *_ in fails}
    rows, tot = [], Counter()
    for g in GROUPS:
        sid_of = {w["wid"]: w["sid"] for w in g["words"]}
        for s in g["sentences"]:
            evs = [e for e in g["events"] if e["native"] and e["f_start"] <= s["f1"] and max(e["f_land"], e["f_end"]) >= s["f0"]]
            land = [e for e in evs if e.get("word") and sid_of.get(e["word"]) == s["sid"] and e["role"] == "primary" and (g["group"], e["eid"]) not in failset]
            # 句内最长没有事件在动/落的空档（帧）
            iv = sorted((max(s["f0"], e["f_start"]), min(s["f1"], max(e["f_land"], e["f_end"]))) for e in evs)
            cur, gap = s["f0"], 0
            for a, b in iv:
                gap = max(gap, a - cur)
                cur = max(cur, b)
            gap = max(gap, s["f1"] - cur)
            reach = bool(evs) and max(max(e["f_land"], e["f_end"]) for e in evs) >= s["f1"] - 2
            dur = s["t1"] - s["t0"]
            pm = g["picture_mode"]
            in_cut_native = pm in NATIVE_IN_CUT
            if not evs:
                st = "无事件"
            elif land and gap <= 90 and reach:
                st = "覆盖" if in_cut_native else "覆盖（源片原生，cut_v8 未原生）"
            else:
                st = "部分"
            if g["group"] == "1-08":
                st = st + "；样板 A v4 原生，未接进 cut_v8"
            tot[st] += dur
            rows.append(dict(group=g["group"], sid=s["sid"], text=s["text"], t=round(dur, 2), picture=pm, events=len(evs), landings=len(land),
                             gap_f=int(gap), reach_end=reach, status=st))
    speech = sum(r["t"] for r in rows)
    covered_native = sum(r["t"] for r in rows if r["status"] == "覆盖")
    any_cov = sum(r["t"] for r in rows if r["status"].startswith("覆盖"))
    res("C7_coverage", True, sentences=len(rows), speech_s=round(speech, 1),
        covered_native_in_cut_pct=round(100 * covered_native / speech, 1), covered_any_source_pct=round(100 * any_cov / speech, 1),
        by_status={k: round(v, 1) for k, v in tot.items()}, sentences_by_status=dict(Counter(r["status"] for r in rows)))
    return rows


def report(rows):
    cnt = Counter(g["picture_mode"] for g in GROUPS)
    L = ["# 词→画面映射：覆盖与未决（v1）", "",
         "HKBU SCIE1007 课程作业的科普视频。本报告由 `映射/check_master.py` 生成，总表 `映射/master_v1.json`，基准 cut_v8（声音实测）。", "",
         f"生成：{T['built']}。全片 {len(GROUPS)} 段，词 {sum(len(g['words']) for g in GROUPS)}，句 {len(rows)}，事件 {sum(len(g['events']) for g in GROUPS)}。", "",
         "## 检查结果", "", "| 项 | 结果 | 要点 |", "|---|---|---|"]
    for k, v in R.items():
        brief = "，".join(f"{a}={b}" for a, b in v.items() if a != "pass_" and not isinstance(b, (list, dict)))
        L.append(f"| {k} | {'通过' if v['pass_'] else '**不过**'} | {brief} |")
    L += ["", "## 画面方式（cut_v8 里每段的画面是怎么来的）", "", "| 方式 | 段数 | 含义 |", "|---|---|---|"]
    mean = {"warp": "旧动画按词变速凑录音（retime_v8）——要换成按表原生生成", "native_tray": "托盘出镜，按事件原生 60 fps（Blender 层只渲偶数帧）",
            "native_blender_rewarped": "第 5 章 Blender 按节拍表原生出，但 cut_v8 又按事件锚点重铺过", "final_approved": "W2/W3 批准成片，不动",
            "title_or_still": "片头、标题卡、片尾"}
    for k, v in cnt.items():
        L.append(f"| {k} | {v} | {mean.get(k, '')} |")
    L += ["", "## 每句覆盖", "", "状态：覆盖 = 有原生事件、至少一个落点对词 ≤2 帧、句内空档 ≤90 帧（1.5 s）、事件持续到句尾。", "",
          "| 段 | 句 | 秒 | 画面 | 事件 | 对词落点 | 最长空档(帧) | 到句尾 | 状态 | 台词 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['group']} | {r['sid']} | {r['t']} | {r['picture']} | {r['events']} | {r['landings']} | {r['gap_f']} | {'是' if r['reach_end'] else '否'} | {r['status']} | {r['text'][:70]} |")
    L += ["", "## 未决项", ""]
    for g in GROUPS:
        for i in g["issues"]:
            L.append(f"- {g['group']}：{i}")
    f6 = R["C6_event_word_2f"]["fails"]
    if f6:
        L.append(f"- 事件对词超 2 帧（primary）{len(f6)} 个，前 40 个：" + "；".join(f"{a} {b}→{c} {d:+d} 帧" for a, b, c, d in f6))
    L.append(f"- 画外音 {cnt['warp']} 段画面是变速旧动画，总表里没有语义事件：要按 `events/<段>.json` 写事件、原生出片（见 README 第 4 节）。")
    (HERE / "覆盖与未决_v1.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    c1()
    c2()
    c3()
    c4()
    c5()
    fails = c6()
    rows = c7(fails)
    out = dict(built=T["built"], checks={k: {("pass" if a == "pass_" else a): b for a, b in v.items()} for k, v in R.items()}, sentences=rows)
    (HERE / "report_v1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    report(rows)
    ok = all(v["pass_"] for k, v in R.items() if k != "C7_coverage")
    print("总判定（C1–C6）：", "全过" if ok else "有不过项（见 report_v1.json / 覆盖与未决_v1.md）")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
