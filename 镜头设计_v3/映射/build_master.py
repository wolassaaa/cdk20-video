"""HKBU SCIE1007 课程作业的科普视频：建立全片"段 → 句 → 词 → 画面事件"总表（导演 11-16 23:30 意见：从零建立词→动画映射）。

时间基准是实测录音：
  1. 先按 cut_v8 的拼法（build_cut_v8 同一套 condense / word_map / 托盘接头）预测每个词在成片里的时刻；
  2. 再用录音本身核对：把每段原始录音按停顿切块，在 cut_v8.mp4 的声音里做归一化互相关（8 kHz，精度 0.125 ms），
     找到每一块真实所在的位置。总表里的词时间用实测值，预测值只用来对照（pred_dev_f）。
  找不到（相关系数低于 0.6）的块不编数，标 unverified，进缺项报告。
句和词 ID 按剧本 v3.3 锚定：<段>.w<剧本里第几个词>（三位数），<段>.s<第几句>；录音里多出来的词是 <段>.x<序号>。
台词锁定，所以同一个词的 ID 不会因为重录、重剪、改停顿而变；重复词（only、and、the）各有自己的 ID，另给 key="词#第几次"。

画面事件从现有"原生按词生成"的来源导入（每个来源标 tool / native / 帧基准），再统一解到段内 60 fps 帧和全片秒：
  - 映射/events/<段>.json            新的手写事件表（以后的做法，见 README）
  - 样板 A 1-08 bl_s108_money_v4      _work_s108/s108_events_v4.json（Blender，原生 60 fps；尚未接进 cut_v8）
  - 第 5 章 bl_s5d 节拍表              粗剪/对时/beats/5-0x.json、5-10、W4（Blender，原生 60 fps；cut_v8 里又按事件锚点重铺过）
  - 托盘出镜 v8                        T4_remotion/src/v3/tray/_resolved8/*.json、sample3.json、beats2.json（Remotion+Blender，60 fps）
画外音 40 段在 cut_v8 里是"旧动画按词变速"（retime_v8），没有语义事件：照实标 picture=warp、事件 0，进未决。

用法：_env/footage/Scripts/python.exe 镜头设计_v3/映射/build_master.py [--cut cut_v8]
出：映射/master_v1.json（总表）、映射/master_v1_words.csv（全片逐词，方便人看）
中间文件（cut 声音 8 kHz 缓存）写 映射/_cache/（不进库）。
"""
import csv
import difflib
import hashlib
import json
import re
import subprocess
import sys
import time
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
ROOT = V3.parent
CUT = V3 / "粗剪"
sys.path[:0] = [str(HERE), str(CUT), str(CUT / "对时")]
import build_cut as BC  # noqa: E402
import build_rough as R  # noqa: E402
import retime_v6 as RT  # noqa: E402
import maplib as M  # noqa: E402

FPS = 60
SR = 8000
CUTNAME = sys.argv[sys.argv.index("--cut") + 1] if "--cut" in sys.argv else "cut_v8"
CUT_MP4 = CUT / f"{CUTNAME}.mp4"
CUT_JSON = CUT / f"{CUTNAME}.json"
WORK = HERE / "_cache"                 # G:/cdk20/work 本工具写不进（11-16 记录）；缓存约 35 MB，*.npy 已在 .gitignore
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
TRAY = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/tray"
S108 = V3 / "styleframes/art/fusion/s1/inserts/_work_s108/s108_events_v4.json"
OUT = HERE / "master_v1.json"
NCC_MIN = 0.6
CHUNK_GAP = 0.8                       # 录音里停顿超过这个就切块（cut 只在 ≥0.9 s 的停顿里剪，块内不会有剪口）

# cut_v8 的规则（build_cut_v8.py 里的常量，照抄，用来"预测"；真值以实测为准）
PAUSE_TIGHT = {"1-09", "5-10", "6-10", "6-11"}
SPEECH_FROM = {"6-09": 1.91}
CH5 = {"5-01", "5-03", "5-07", "5-08", "5-10"}
TRAY_SAMPLES = {"3-01", "3-09", "4-11+4-12"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sha(p, n=1 << 20):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        h.update(f.read(n))
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- 声音
def cut_audio():
    WORK.mkdir(parents=True, exist_ok=True)
    st = CUT_MP4.stat()
    tag = f"{CUTNAME}_{st.st_size}_{int(st.st_mtime)}"
    f = WORK / f"{tag}_8k.npy"
    if f.exists():
        return np.load(f)
    log("抽 cut 声音", CUT_MP4.name)
    raw = subprocess.run([FF, "-v", "error", "-i", str(CUT_MP4), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    np.save(f, a)
    return a


_TAKE = {}


def take_audio(it):
    p = it["dir"] / it["wav"]
    if p not in _TAKE:
        x, sr = sf.read(str(p), always_2d=True)
        x = x.mean(axis=1)
        g = gcd(SR, sr)
        _TAKE[p] = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return _TAKE[p]


def ncc_search(snip, hay):
    n = len(snip)
    if len(hay) < n + 1:
        return 0, 0.0
    s = snip - snip.mean()
    s /= (np.linalg.norm(s) + 1e-9)
    c = fftconvolve(hay, s[::-1], mode="valid")
    cs = np.concatenate([[0.0], np.cumsum(hay.astype(np.float64) ** 2)])
    cm = np.concatenate([[0.0], np.cumsum(hay.astype(np.float64))])
    var = (cs[n:] - cs[:-n]) - (cm[n:] - cm[:-n]) ** 2 / n
    r = c / np.sqrt(np.maximum(var, 1e-12))
    k = int(np.argmax(r))
    return k, float(r[k])


def chunks(words):
    out, cur = [], [0]
    for i in range(1, len(words)):
        if words[i]["t0"] - words[i - 1]["t1"] > CHUNK_GAP:
            out.append(cur)
            cur = []
        cur.append(i)
    out.append(cur)
    return out


def measure(it, words, A, S, E, pred=None):
    """把录音 it 的词（take 时间）在 cut 声音 A 的 [S, E] 秒里逐块找到。返回 [(全片 t0, t1, ncc, 块号)]。"""
    x = take_audio(it)
    res = [None] * len(words)
    cursor = S - 0.3
    for ci, idx in enumerate(chunks(words)):
        a = max(0.0, words[idx[0]]["t0"] - 0.03)
        b = words[idx[-1]]["t1"] + 0.03
        snip = x[int(a * SR):int(b * SR)]
        if pred is not None:
            c = pred(a)
            w0, w1 = c - 0.45, c + 0.45 + (b - a)
        else:
            w0, w1 = cursor, E + 0.5
        w0, w1 = max(0.0, w0), min(len(A) / SR, w1)
        k, r = ncc_search(snip, A[int(w0 * SR):int(w1 * SR)])
        delta = (int(w0 * SR) + k) / SR - a
        for i in idx:
            res[i] = (words[i]["t0"] + delta, words[i]["t1"] + delta, round(r, 3), ci)
        if r >= NCC_MIN:
            cursor = b + delta - 0.05
    return res


# ---------------------------------------------------------------- 剧本
def script_text():
    out, cur = {}, None
    for line in (V3 / "script/script_v3.3.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\*\*(\S+) · ", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur and line.startswith("> "):
            out[cur].append(line[2:].strip())
    return {k: " ".join(v) for k, v in out.items()}


def sentence_ids(tokens):
    sid, out = 1, []
    for i, t in enumerate(tokens):
        out.append(sid)
        bare = t.rstrip("\"'”’)")
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if re.search(r"[.?!]$", bare) and (not bare.endswith("...") or nxt[:1].isupper()):
            sid += 1
    return out


def align(seg, script, rec):
    """剧本词 ↔ 录音词。返回 (每个录音词的 (wid, 剧本序号或 None, sid, match), 缺的剧本词)。"""
    st = script.split()
    sids = sentence_ids(st)
    a = [M.norm(t) for t in st]
    b = [M.norm(w["w"]) for w in rec]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    res, missing, nx = [None] * len(rec), [], 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1):
                i = i1 + k
                res[j1 + k] = (f"{seg}.w{i + 1:03d}", i, sids[i], "equal" if op == "equal" else "replace")
        else:
            for i in range(i1, i2):
                missing.append(dict(wid=f"{seg}.w{i + 1:03d}", w=st[i], sid=f"{seg}.s{sids[i]}"))
            for j in range(j1, j2):
                nx += 1
                res[j] = (f"{seg}.x{nx:02d}", None, None, "extra")
    last = 1
    for j, r in enumerate(res):                 # 多出来的词归到前一个词那句
        if r[2] is None:
            res[j] = (r[0], r[1], last, r[3])
        last = res[j][2]
    sents = {}
    for t, s in zip(st, sids):
        sents.setdefault(s, []).append(t)
    return res, missing, {k: " ".join(v) for k, v in sents.items()}


# ---------------------------------------------------------------- 事件导入
def ev(eid, obj, verb, seg, word, f_start, f_land, f_end, tool, native, source, **kw):
    return dict(eid=eid, obj=obj, verb=verb, seg=seg, word_ref=word, f_start=int(f_start), f_land=int(f_land), f_end=int(f_end),
                tool=tool, native=native, source=source, **kw)


def imp_authored(G):
    """手写事件表 映射/events/<段>.json（格式见 映射/事件表格式.md）。解析统一交给 resolve.resolve_doc（新写法 at/until 和
    第一阶段的 land/lead/start/until 都认）。migrate_beats_v8 自动迁移的表只认 1-08（完整转好，替代 s108 导入）；
    其余迁移表的事件和下面 beats / 托盘导入是同一来源，不重复导入。"""
    import resolve as RS
    f = HERE / "events" / f"{G['group'].replace('+', '_')}.json"
    if not f.exists():
        return [], None
    D = json.loads(f.read_text(encoding="utf-8"))
    if D.get("migrated") and G["group"] != "1-08":
        return [], None
    g = M.Group(G)
    evs, probs = RS.resolve_doc(g, D)
    if probs:
        G["issues"] += [f"events/{f.name}: {x}" for x in probs]
    out = []
    for e in evs:
        out.append(ev(e["id"], e["obj"], e["verb"], G["group"] if "+" not in G["group"] else None, e["word"], e["f_start"], e["f_land"], e["f_end"],
                      D.get("tool", "any"), True, str(f.relative_to(ROOT)), means=e.get("means", ""), until=e.get("until"), ref_mode="wid",
                      lag=e["f_land"] - (e.get("word_f0") or e["f_land"])))
    G["holds"] = D.get("holds", [])
    return out, dict(file=str(f.relative_to(ROOT)), tool=D.get("tool"), note=D.get("note", ""))


def imp_s108():
    D = json.loads(S108.read_text(encoding="utf-8"))
    extra = {}
    for b in D["bills"]:
        extra[f"bill{b['i']}"] = (b["grow"], b["land"])
    for w in D["wells"]:
        extra[f"well{w['k']}"] = (w["grow"], w["land"])
    for p in D["pills"]:
        extra[f"pill{p['k']}"] = (p["grow"], p["land"])
        if "retract" in p:
            extra[f"pillx{p['k']}"] = (p["retract"], p["retract_end"])
    out = []
    for e in D["events"]:
        a, b = extra.get(e["id"], (e["frame"], e["frame"]))
        land = e["frame"]
        out.append(ev(e["id"], e["obj"], e["kind"], "1-08", e.get("word"), min(a, land), land, max(b, land), "blender", True,
                      str(S108.relative_to(ROOT)), ref_mode="norm"))
    return out, dict(file=str(S108.relative_to(ROOT)), tool="blender", frames=D["frames"],
                     render="inserts/S1_108_money_1080_v4.mp4", in_cut=False,
                     note="样板 A 第 4 版，Fable 第 5 轮 PASS；cut_v8 里 1-08 仍是旧动画变速，尚未换成这条")


def imp_beats(seg):
    f = CUT / "对时/beats" / f"{seg}.json"
    D = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for e in D["events"]:
        w = e.get("word")
        if w and w.startswith("b") and w[1:].isdigit():
            w = None                                  # W4 拍，不是词
        out.append(ev(e["id"], e.get("obj", e["id"]), e.get("verb", e.get("kind", "land")), seg, w,
                      e["f_start"], e["f_land"], e["f_end"], "blender", True, str(f.relative_to(ROOT)), lag=e.get("lag", 0), ref_mode="raw"))
    return out, dict(file=str(f.relative_to(ROOT)), tool="blender", hash=D.get("hash"), frames=D.get("frames", {}).get("len"))


def imp_tray(group):
    f = TRAY / "_resolved8" / (group.replace("+", "_") + ".json")
    if not f.exists():
        return [], None
    D = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for k, e in enumerate(D["events"]):
        w = e.get("word")
        seg = None
        if w and ":" in w:
            pi, w = w.split(":", 1)
            seg = D["parts"][int(pi)]["seg"]
        out.append(ev(f"t{k:02d}_{e['verb']}_{e['obj']}", e["obj"], e["verb"], seg, w, e["f_start"], e["f_land"], e.get("f_end", e["f_land"]),
                      "remotion+blender", True, str(f.relative_to(ROOT)), ref_mode="nearest"))
    return out, dict(file=str(f.relative_to(ROOT)), tool="remotion+blender", frames=D["frames"],
                     note="托盘 Blender 层只渲偶数帧（奇数帧用前一帧），60 fps 交付时是 30 步进")


def imp_samples(group):
    out = []
    if group == "3-01":
        f = TRAY / "beats2.json"
        D = json.loads(f.read_text(encoding="utf-8"))
        jsx = (TRAY / "Sample1_v8.jsx").read_text(encoding="utf-8")       # v8 成片 = 时间线 CUT..END（beats2 的 cut_from=30 是 v2 的）
        cut = int(re.search(r"CUT = (\d+)", jsx).group(1))
        for k, a in enumerate(D["actions"]):
            if a.get("word") is None:
                continue
            out.append(ev(f"s1_{k:02d}", a["name"], "action", "3-01", a["word"], a["start"] - cut, a["land"] - cut, a["land"] - cut,
                          "remotion+blender", True, str(f.relative_to(ROOT)), ref_mode="nearest"))
        return out, dict(file=str(f.relative_to(ROOT)), tool="remotion+blender", frame_base=f"时间线帧 − {cut}")
    f = TRAY / "sample3.json"
    S = json.loads(f.read_text(encoding="utf-8"))
    key = "t309" if group == "3-09" else "t411"
    segs = ["3-09"] if group == "3-09" else ["4-11", "4-12"]
    for k, (obj, word, fr) in enumerate(S[key]["landings"]):
        seg = segs[0] if len(segs) == 1 or fr < S[key].get("cut", 10 ** 9) else segs[1]
        out.append(ev(f"{key}_{k:02d}", obj, "land", seg, word, fr, fr, fr, "remotion+blender", True, str(f.relative_to(ROOT)), ref_mode="nearest"))
    return out, dict(file=str(f.relative_to(ROOT)), tool="remotion+blender", key=key)


# ---------------------------------------------------------------- 主体
def main():
    C = json.loads(CUT_JSON.read_text(encoding="utf-8"))
    beats = {b["seg"]: b for b in R.read_script()}
    TXT = script_text()
    avail = BC.takes()
    A = cut_audio()
    log(f"cut 声音 {len(A) / SR:.2f} s")
    groups, all_missing = [], []
    for row in C["beats"]:
        gname = row["seg"]
        segs = gname.split("+")
        S, E = row["new_start"], row["new_end"]
        G = dict(group=gname, segs=segs, kind=row["kind"], who=row.get("who"), cut_start_s=S, cut_end_s=E,
                 cut_start_f=M.frame(S), len_s=round(E - S, 3), len_f=M.frame(E - S),
                 picture=row.get("picture"), cut_state=row.get("state"), words=[], sentences=[], events=[], sources=[], issues=[])
        # 画面方式
        if row["kind"] == "MUSIC":
            G["picture_mode"] = {"W2": "final_approved", "W3": "final_approved", "W4": "native_blender_rewarped"}.get(gname, "title_or_still")
            G["time_base"] = "music"
        elif gname in CH5:
            G["picture_mode"] = "native_blender_rewarped"
        elif row["kind"] == "VO":
            G["picture_mode"] = "warp"
        else:
            G["picture_mode"] = "native_tray"
        # ---- 词
        for seg in segs:
            if row["kind"] == "MUSIC":
                break
            cand = avail.get(seg, [])
            who = beats.get(seg, {}).get("who")
            it = next((c for c in cand if c["name"] == row.get("take")), None) or next((c for c in cand if c["person"] == who), cand[0] if cand else None)
            if not it:
                G["issues"].append(f"{seg}: 没有录音")
                continue
            words = [dict(w) for w in it["words"]]
            if seg in SPEECH_FROM:
                t0 = SPEECH_FROM[seg]
                words = [w for w in words if w["t1"] > t0]
                words[0]["t0"] = t0
            pred = None
            if G["picture_mode"] == "warp" or gname in CH5 or seg == "5-04":
                tight = seg in PAUSE_TIGHT
                wm = RT.word_map(dict(it, words=words), BC.RULES["head"], 0.9 if tight else BC.RULES["pause_max"], 0.5 if tight else BC.RULES["pause_keep"])
                pred = lambda t, wm=wm: S + wm(t)  # noqa: E731
            meas = measure(it, words, A, S, E, pred)
            al, missing, stext = align(seg, TXT.get(seg, ""), words)
            all_missing += missing
            occ = {}
            for w, m, a_ in zip(words, meas, al):
                g0, g1, r, ci = m
                n = M.norm(w["w"])
                occ[n] = occ.get(n, 0) + 1
                rec = dict(wid=a_[0], seg=seg, w=w["w"], norm=n, occ=occ[n], key=f"{n}#{occ[n]}", sid=f"{seg}.s{a_[2]}", match=a_[3],
                           t0=round(g0 - S, 4), t1=round(g1 - S, 4), f0=M.frame(g0 - S), f1=M.frame(g1 - S),
                           g0=round(g0, 4), g1=round(g1, 4), G0=M.frame(g0), ncc=r, chunk=ci, verified=r >= NCC_MIN,
                           src=dict(take=it["name"], t0=w["t0"], t1=w["t1"]))
                if pred is not None:
                    rec["pred_dev_f"] = round((pred(w["t0"]) - g0) * FPS, 2)
                G["words"].append(rec)
            G["sources"].append(dict(seg=seg, take=it["name"], wav=str((it["dir"] / it["wav"]).relative_to(ROOT)), person=it["person"],
                                     script_who=who, take_sha=sha(it["dir"] / it["wav"])))
            if missing:
                G["issues"].append(f"{seg}: 剧本词录音里没有 {len(missing)} 个：" + " ".join(x["w"] for x in missing))
            # 句
            for sid in sorted({int(x["sid"].rsplit("s", 1)[1]) for x in G["words"] if x["seg"] == seg}):
                ws = [x for x in G["words"] if x["seg"] == seg and x["sid"] == f"{seg}.s{sid}"]
                G["sentences"].append(dict(sid=f"{seg}.s{sid}", seg=seg, text=stext.get(sid, ""), w_first=ws[0]["wid"], w_last=ws[-1]["wid"],
                                           t0=ws[0]["t0"], t1=ws[-1]["t1"], f0=ws[0]["f0"], f1=ws[-1]["f1"], g0=ws[0]["g0"], g1=ws[-1]["g1"]))
        unv = [w["wid"] for w in G["words"] if not w["verified"]]
        if unv:
            G["issues"].append(f"录音核对不上（ncc<{NCC_MIN}）{len(unv)} 个词：" + " ".join(unv[:12]))
        # ---- 事件
        imports = []
        evs, src = imp_authored(G)
        if src:
            imports.append((evs, src))
        if gname == "1-08" and not src:
            imports.append(imp_s108())
        if gname in CH5 or gname == "W4":
            imports.append(imp_beats(gname))
        if G["picture_mode"] == "native_tray":
            imports.append(imp_samples(gname) if gname in TRAY_SAMPLES else imp_tray(gname))
        for evs, src in imports:
            if not src:
                continue
            G.setdefault("event_sources", []).append(src)
            for e in evs:
                G["events"].append(resolve_event(G, e, src))
        mark_staggers(G)
        groups.append(G)
        log(f"{gname:22} {G['picture_mode']:24} 词 {len(G['words']):3}  句 {len(G['sentences']):2}  事件 {len(G['events']):3}  "
            f"ncc 最低 {min([w['ncc'] for w in G['words']] or [1]):.2f}")
    T = dict(schema="cdk20.wordmap/1", note="HKBU SCIE1007 课程作业的科普视频：全片 段→句→词→画面事件 总表。格式说明见 映射/README.md。",
             built=time.strftime("%Y-%m-%d %H:%M:%S +09:00"), fps=FPS, cut=dict(name=CUTNAME, mp4=str(CUT_MP4.relative_to(ROOT)),
             json=str(CUT_JSON.relative_to(ROOT)), size=CUT_MP4.stat().st_size, mtime=int(CUT_MP4.stat().st_mtime), seconds=C["seconds"],
             note="cut_v8.mp4 本身是 30 fps；总表帧号一律 60 fps（新动画原生 60 帧渲染用）"),
             script="镜头设计_v3/script/script_v3.3.md（锁定）", rules=dict(time_base="实测录音（cut 声音互相关）", ncc_min=NCC_MIN, chunk_gap_s=CHUNK_GAP,
             frame="f = round(t × 60)，段内帧 0 = 段在成片里的起点", wid="<段>.w<剧本第几个词>；录音多出的词 <段>.x<序号>"),
             missing_script_words=all_missing, groups=groups)
    OUT.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(HERE / "master_v1_words.csv", "w", newline="", encoding="utf-8-sig") as fp:
        wr = csv.writer(fp)
        wr.writerow(["group", "seg", "sid", "wid", "key", "word", "g0_s", "g1_s", "G0_f60", "local_f0", "local_f1", "ncc", "verified", "take", "take_t0"])
        for G in groups:
            for w in G["words"]:
                wr.writerow([G["group"], w["seg"], w["sid"], w["wid"], w["key"], w["w"], w["g0"], w["g1"], w["G0"], w["f0"], w["f1"], w["ncc"],
                             w["verified"], w["src"]["take"], w["src"]["t0"]])
    log("写", OUT.relative_to(ROOT), f"{sum(len(g['words']) for g in groups)} 词，{sum(len(g['events']) for g in groups)} 事件")


def mark_staggers(G):
    """同一个词上、同一个动词的一串事件（托盘里 8 颗药一颗接一颗落、Millions 时 46 粒往下掉）：
    离词开口最近的那个是 primary（要求 ≤2 帧），其余是 stagger（有意错开的跟随拍，只要求单调、不出这句）。"""
    series = {}
    for e in G["events"]:
        if e["verb"] == "mark":            # beats_resolve 的 kind=mark：有意带 lag 的标记，不算落点
            e["role"] = "mark"
            continue
        if e.get("word") is not None:
            series.setdefault((e["word"], e["verb"], e.get("source")), []).append(e)
    for evs in series.values():
        p = min(evs, key=lambda e: (abs(e["word_dev_f"]), e["f_land"]))
        for e in evs:
            e["role"] = "primary" if e is p else "stagger"
            if e is not p:
                e["stagger_of"] = p["eid"]
    for e in G["events"]:
        e.setdefault("role", "free")       # 不挂词的事件（after / at / 拍）


def resolve_event(G, e, src):
    """把导入的事件挂到总表的词上：word_ref → wid；记下事件落点和词开口的帧差。"""
    e = dict(e)
    e.setdefault("group", G["group"])
    ref = e.pop("word_ref", None) if "word_ref" in e else e.get("word")
    mode = e.pop("ref_mode", "wid")
    e["word"] = None
    if ref:
        ws = [w for w in G["words"] if e.get("seg") in (None, w["seg"])]
        hit = None
        if ref in {w["wid"] for w in ws}:
            hit = next(w for w in ws if w["wid"] == ref)
        else:
            base, _, n = ref.partition("#")
            if mode == "raw":                  # beats_resolve 的老写法：录音原文（带标点）完全一样才算，#k = 第 k 次
                cands = [w for w in ws if w["w"] == base]
            else:                              # norm（bl_s108 的 wf）/ nearest（托盘：同词取离落点最近的那次）
                cands = [w for w in ws if w["w"] == base] if mode == "nearest" else []
                cands = cands or [w for w in ws if w["norm"] == M.norm(base)]
            if cands and mode == "nearest" and not n:
                hit = min(cands, key=lambda w: abs(w["f0"] - e["f_land"]))
            elif cands and int(n or 1) <= len(cands):
                hit = cands[int(n or 1) - 1]
        if hit:
            e["word"] = hit["wid"]
            e["word_dev_f"] = e["f_land"] - (hit["f0"] + e.get("lag", 0))
        else:
            e["word_missing"] = ref
    e["ref"] = dict(raw=ref, mode=mode) if ref else None
    e["g_start"] = round(G["cut_start_s"] + e["f_start"] / FPS, 4)
    e["g_land"] = round(G["cut_start_s"] + e["f_land"] / FPS, 4)
    e["g_end"] = round(G["cut_start_s"] + e["f_end"] / FPS, 4)
    return e


if __name__ == "__main__":
    main()
