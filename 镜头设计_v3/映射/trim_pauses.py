"""HKBU SCIE1007 课程作业的科普视频：B 档画外音长停顿裁剪（19 文档 7.3；17 文档任务单 T1），出总表 v2。

为什么：接上片尾彩蛋后全片超过课程 20 分钟上限；B 档页面要全部重渲，先裁再渲。
只动 深化/15_B档_停顿清单.md 登记的 65 处（26 段）。master_v1.json 和旧声音（_cache/remotion_public/map/<段>.wav）不动。

规格（19 的 7.3，逐条）：
  - 句内停顿裁到 0.40 s（24 帧），句间裁到 0.55 s（33 帧）。删掉的长度按帧算：停顿帧数（词 f1 → 下一词 f0）− 目标帧数，
    所以每一刀都是整帧（800 采样 @48 kHz），段长、词帧都按整帧往前挪，不重新对齐。
  - 切在停顿里能量最低的地方：删除窗 [s, s+D] 在停顿里滑动（1 ms 步），代价 = 两个切口（各 ±10 ms）能量的较大者，
    外加删掉的那一块里最响处超过 −40 dBFS 的部分 × 0.5（尽量不删掉气口、词尾）；代价在最低值 +3 dB 以内的位置里，
    取离"留下的静音前后各一半"最近的一个。
  - 切口 15 ms 等功率交叉（cos / sin），交叉区整个落在删除窗两边，输出正好短 D。
  - 离任何词的边界不到 60 ms 的地方不切（交叉区也算在内）。段首第一个词之前、段尾最后一个词之后的留白不动。
输出（实体在 G 盘）：
  映射/_cache/remotion_public/map_trim/<段>.wav   裁好的声音（48 kHz 16 bit，和原来同格式；没被切的采样逐位相同）
  映射/_cache/remotion_public/map_trim/trim_<段>.json   每一刀：停顿、删掉的起止（段内秒、采样、帧）、切口能量、留下的前后静音
  映射/master_v2.json   格式和 master_v1 一样；被裁段的词、句、事件、holds、段长按删掉的帧往前挪；没裁的段段内帧一帧不动。
                        段在片里的起点（cut_start_*、g*、G0）跟着前面删掉的累计往前挪，全片首尾相接不断。
                        顶层多一个 trim 块（来源、规则、每一刀在 v1 全片时间轴上的位置），每段多一个 voice_wav（该用哪条声音）。
  映射/master_v2_words.csv

用法：python -X utf8 镜头设计_v3/映射/trim_pauses.py        （全部重做，幂等；只要 numpy。_env/footage 的 python 写不进 G 盘）
检查：映射/check_trim.py
"""
import copy
import csv
import json
import re
import sys
import time
from pathlib import Path

import wave

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V1 = HERE / "master_v1.json"
V2 = HERE / "master_v2.json"
LIST = ROOT / "镜头设计_v3/深化/15_B档_停顿清单.md"
SRC = HERE / "_cache/remotion_public/map"
OUT = HERE / "_cache/remotion_public/map_trim"
FPS = 60
SR = 48000
SPF = SR // FPS                     # 800 采样一帧
TARGET_F = {"句内": 24, "句间": 33}  # 0.40 s、0.55 s
XF = int(0.015 * SR)                 # 15 ms 交叉 = 720 采样
H = XF // 2
EDGE = 0.060                         # 离词边界 ≥ 60 ms
WIN = int(0.010 * SR)                # 切口能量窗 ±10 ms
STEP = SR // 1000                    # 滑动步 1 ms
NEAR_DB = 3.0
LOUD_DB = -40.0


def rel(p):
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def read_list():
    rows = []
    for ln in LIST.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d-\d\d) \| (句内|句间) \| (\d+) \| (\d+) \| (\d+) \|", ln)
        if m:
            rows.append(dict(seg=m.group(1), kind=m.group(2), a=int(m.group(3)), b=int(m.group(4))))
    if len(rows) != 65:
        sys.exit(f"停顿清单读到 {len(rows)} 处，应该是 65 处：清单格式变了？")
    return rows


def read_wav(p):
    with wave.open(str(p), "rb") as w:
        if w.getframerate() != SR or w.getsampwidth() != 2:
            sys.exit(f"{p} 不是 48 kHz 16 bit")
        ch = w.getnchannels()
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, ch).copy()


def write_wav(p, x):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.ascontiguousarray(x, dtype="<i2").tobytes())


def db(e):
    return 10 * np.log10(np.maximum(e, 1e-12))


def plan_seg(g, rows, x):
    """g：总表 v1 的段；rows：清单里这段的停顿；x：单声道 float。返回按时间排的刀。"""
    ws = g["words"]
    c2 = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])

    def energy(p):                                   # p 处 ±10 ms 的平均能量（dB）
        a, b = max(0, p - WIN), min(len(x), p + WIN)
        return db((c2[b] - c2[a]) / max(1, b - a))

    # 删除窗内部最响处（10 ms 窗）：先算 10 ms 步的能量序列
    e10 = db((c2[WIN:] - c2[:-WIN]) / WIN)          # e10[i] = [i, i+WIN) 的能量

    cuts = []
    for r in rows:
        hit = [i for i in range(len(ws) - 1) if ws[i]["f1"] == r["a"] and ws[i + 1]["f0"] == r["b"]]
        if len(hit) != 1:
            sys.exit(f"{r['seg']} 停顿 {r['a']}–{r['b']} 在总表 v1 里对不上词（找到 {len(hit)} 处）")
        i = hit[0]
        w0, w1 = ws[i], ws[i + 1]
        same = w0["sid"] == w1["sid"]
        if same != (r["kind"] == "句内"):
            sys.exit(f"{r['seg']} 停顿 {r['a']}–{r['b']}：清单写 {r['kind']}，总表里 {w0['sid']} / {w1['sid']}")
        gap_f = r["b"] - r["a"]
        D_f = gap_f - TARGET_F[r["kind"]]
        if D_f <= 0:
            continue
        D = D_f * SPF
        t1, t0n = w0["t1"], w1["t0"]
        lo = int(round((t1 + EDGE) * SR)) + H                   # 删除窗起点 s 的最小值（交叉区也离词 ≥ 60 ms）
        hi = int(round((t0n - EDGE) * SR)) - H - D               # 最大值
        if hi < lo:
            sys.exit(f"{r['seg']} 停顿 {r['a']}–{r['b']}：放不下（删 {D_f} 帧，离词边界不够 60 ms）")
        keep_s = (t0n - t1) - D / SR
        s_mid = int(round((t1 + keep_s / 2) * SR))               # 留下的静音前后各一半时的 s
        cand = []
        for s in range(lo, hi + 1, STEP):
            ec = max(energy(s), energy(s + D))
            a, b = s, s + D - WIN
            inner = float(e10[a:b + 1].max()) if b > a else ec
            cost = ec + 0.5 * max(0.0, inner - LOUD_DB)
            cand.append((cost, abs(s - s_mid), s, ec, inner))
        best = min(c[0] for c in cand)
        cost, _, s, ec, inner = min((c for c in cand if c[0] <= best + NEAR_DB), key=lambda c: (c[1], c[0]))
        cuts.append(dict(kind=r["kind"], list_a=r["a"], list_b=r["b"], gap_f=gap_f, target_f=TARGET_F[r["kind"]],
                         words=[w0["wid"], w1["wid"]], text=f"{w0['w']} … {w1['w']}",
                         word_t1=t1, next_t0=t0n, del_f=D_f, del_samples=D,
                         s=s, e=s + D, t_s=round(s / SR, 5), t_e=round((s + D) / SR, 5),
                         keep_before_s=round(s / SR - t1, 3), keep_after_s=round(t0n - (s + D) / SR, 3),
                         splice_db=round(float(ec), 1), deleted_max_db=round(float(inner), 1), cost=round(float(cost), 2),
                         split_off_ms=round((s - s_mid) / SR * 1000, 1)))
    cuts.sort(key=lambda c: c["s"])
    for a, b in zip(cuts, cuts[1:]):
        if b["s"] - H < a["e"] + H:
            sys.exit(f"{g['group']}：两刀太近（{a['t_s']}、{b['t_s']}）")
    return cuts


def apply(xs, cuts):
    """xs：(n, ch) float。按刀删，切口 15 ms 等功率交叉。返回新数组。"""
    th = (np.arange(XF) + 0.5) / XF * (np.pi / 2)
    fo, fi = np.cos(th)[:, None], np.sin(th)[:, None]
    parts, pos = [], 0
    for c in cuts:
        s, e = c["s"], c["e"]
        parts.append(xs[pos:s - H])
        parts.append(xs[s - H:s + H] * fo + xs[e - H:e + H] * fi)
        pos = e + H
    parts.append(xs[pos:])
    return np.concatenate(parts, axis=0)


def fmap(cuts_f):
    """段内帧映射：cuts_f = [(删除起帧, 删的帧数)]，起帧按删除窗起点所在帧算。删掉的那几帧里的帧映到切口。"""
    def m(f):
        out = f
        for a, n in cuts_f:
            if f >= a + n:
                out -= n
            elif f > a:
                out -= f - a
        return out
    return m


def main():
    t_start = time.time()
    rows = read_list()
    T1 = json.loads(V1.read_text(encoding="utf-8"))
    T2 = copy.deepcopy(T1)
    by = {}
    for r in rows:
        by.setdefault(r["seg"], []).append(r)
    OUT.mkdir(parents=True, exist_ok=True)
    G1 = {g["group"]: g for g in T1["groups"]}
    plans = {}
    for seg, rs in by.items():
        g = G1[seg]
        src = SRC / f"{seg}.wav"
        xi = read_wav(src)
        xf = xi.astype(np.float32) / 32768.0
        cuts = plan_seg(g, rs, xf.mean(axis=1))
        y = apply(xf, cuts)
        yi = np.clip(np.round(y * 32768.0), -32768, 32767).astype(np.int16)
        # 没被切、不在交叉区的采样逐位等于原来的
        pos_in, pos_out = 0, 0
        for c in cuts:
            n = c["s"] - H - pos_in
            assert np.array_equal(yi[pos_out:pos_out + n], xi[pos_in:pos_in + n])
            pos_out += n + XF
            pos_in = c["e"] + H
        assert np.array_equal(yi[pos_out:], xi[pos_in:])
        dst = OUT / f"{seg}.wav"
        write_wav(dst, yi)
        tot = sum(c["del_f"] for c in cuts)
        rec = dict(schema="cdk20.trim/1", note="HKBU SCIE1007 课程作业的科普视频：trim_pauses.py 出，每一刀删掉的段内起止（19 文档 7.3）。",
                   seg=seg, src=rel(src), out=rel(dst), sr=SR, samples_in=len(xi), samples_out=len(yi),
                   len_f_v1=g["len_f"], len_f_v2=g["len_f"] - tot, removed_f=tot, removed_s=round(tot / FPS, 4),
                   rules=dict(target_s={"句内": 0.40, "句间": 0.55}, crossfade_ms=15, edge_ms=60, energy_win_ms=20, near_db=NEAR_DB),
                   cuts=cuts, built=time.strftime("%Y-%m-%d %H:%M:%S +09:00"))
        (OUT / f"trim_{seg}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        plans[seg] = cuts
        print(f"{seg}  {len(cuts)} 刀  删 {tot:3d} 帧（{tot / FPS:5.2f} s）  {g['len_f']} → {g['len_f'] - tot}  "
              f"切口最响 {max(c['splice_db'] for c in cuts):.0f} dB  删掉部分最响 {max(c['deleted_max_db'] for c in cuts):.0f} dB")

    # ---------------- 总表 v2
    cum_f = 0
    trim_meta = []
    for g in T2["groups"]:
        name = g["group"]
        S1, F1 = g["cut_start_s"], g["cut_start_f"]
        g["cut_start_f"] = F1 - cum_f
        g["cut_start_s"] = round(S1 - cum_f / FPS, 4)
        cuts = plans.get(name, [])
        cf = [(c["s"] // SPF, c["del_f"]) for c in cuts]
        m = fmap(cf)
        sh_t = lambda t: t - sum(c["del_samples"] for c in cuts if c["e"] <= t * SR + 1e-6) / SR  # noqa: E731
        Sv2 = g["cut_start_s"]
        for w in g["words"]:
            n = sum(c["del_f"] for c in cuts if c["e"] <= w["t0"] * SR)
            n1 = sum(c["del_f"] for c in cuts if c["e"] <= w["t1"] * SR)
            if n != n1:
                sys.exit(f"{w['wid']} 被切到了")
            w["t0"] = round(w["t0"] - n / FPS, 4)
            w["t1"] = round(w["t1"] - n / FPS, 4)
            w["f0"] -= n
            w["f1"] -= n
            w["g0"] = round(Sv2 + w["t0"], 4)
            w["g1"] = round(Sv2 + w["t1"], 4)
            w["G0"] = g["cut_start_f"] + w["f0"]
            if n:
                w["trim_shift_f"] = n
        wid = {w["wid"]: w for w in g["words"]}
        for s in g["sentences"]:
            a, b = wid[s["w_first"]], wid[s["w_last"]]
            s.update(t0=a["t0"], t1=b["t1"], f0=a["f0"], f1=b["f1"], g0=a["g0"], g1=b["g1"])
        for e in g["events"]:
            for k in ("f_start", "f_land", "f_end"):
                e[k] = m(e[k])
            for k, fk in (("g_start", "f_start"), ("g_land", "f_land"), ("g_end", "f_end")):
                if k in e:
                    e[k] = round(Sv2 + e[fk] / FPS, 4)
        g["holds"] = [[m(a), m(b)] for a, b in g.get("holds", [])]
        tot = sum(c["del_f"] for c in cuts)
        g["len_f"] -= tot
        g["len_s"] = round(g["len_s"] - tot / FPS, 3)
        g["cut_end_s"] = round(g["cut_start_s"] + g["len_s"], 4)
        fn = name.replace("+", "_")
        if cuts:
            g["voice_wav"] = rel(OUT / f"{fn}.wav")
            g["trim"] = dict(removed_f=tot, cuts=len(cuts), json=rel(OUT / f"trim_{fn}.json"))
            for c in cuts:
                trim_meta.append(dict(group=name, kind=c["kind"], v1_g_s=round(S1 + c["t_s"], 5), v1_g_e=round(S1 + c["t_e"], 5),
                                      local_t_s=c["t_s"], local_t_e=c["t_e"], del_f=c["del_f"], words=c["words"]))
        elif (SRC / f"{fn}.wav").exists():
            g["voice_wav"] = rel(SRC / f"{fn}.wav")
        cum_f += tot
    T2["built"] = time.strftime("%Y-%m-%d %H:%M:%S +09:00")
    T2["note"] = ("HKBU SCIE1007 课程作业的科普视频：全片 段→句→词→画面事件 总表 v2 = v1 按 15_B档_停顿清单 裁停顿（19 文档 7.3）。"
                  "被裁段的词时间按删掉的帧往前挪，不重新对齐；没裁的段段内帧和 v1 一样。格式说明见 映射/README.md。")
    T2["derived_from"] = dict(master="镜头设计_v3/映射/master_v1.json", built=T1["built"], tool="镜头设计_v3/映射/trim_pauses.py")
    T2["trim"] = dict(list=rel(LIST), rules="句内 → 0.40 s，句间 → 0.55 s；能量最低处切，15 ms 等功率交叉，离词边界 ≥ 60 ms；段首段尾留白不动",
                      groups=len(plans), cuts=sum(len(v) for v in plans.values()), removed_f=cum_f, removed_s=round(cum_f / FPS, 3),
                      len_f_v1=sum(g["len_f"] for g in T1["groups"]), len_f_v2=sum(g["len_f"] for g in T2["groups"]),
                      timeline="v2 全片时间轴 = cut_v8 删掉下面各刀（v1_g_s → v1_g_e，cut_v8 的秒）", cuts_list=trim_meta)
    V2.write_text(json.dumps(T2, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(HERE / "master_v2_words.csv", "w", newline="", encoding="utf-8-sig") as fp:
        wr = csv.writer(fp)
        wr.writerow(["group", "seg", "sid", "wid", "key", "word", "g0_s", "g1_s", "G0_f60", "local_f0", "local_f1", "ncc", "verified", "take", "take_t0"])
        for G in T2["groups"]:
            for w in G["words"]:
                wr.writerow([G["group"], w["seg"], w["sid"], w["wid"], w["key"], w["w"], w["g0"], w["g1"], w["G0"], w["f0"], w["f1"], w["ncc"],
                             w["verified"], w["src"]["take"], w["src"]["t0"]])
    print(f"总表 v2：{len(plans)} 段 {T2['trim']['cuts']} 刀，删 {cum_f} 帧（{cum_f / FPS:.2f} s）；"
          f"总帧 {T2['trim']['len_f_v1']} → {T2['trim']['len_f_v2']}  → {rel(V2)}  （{time.time() - t_start:.0f} s）")


if __name__ == "__main__":
    main()
