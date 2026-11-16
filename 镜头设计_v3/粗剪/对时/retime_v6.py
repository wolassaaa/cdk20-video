"""HKBU SCIE1007 课程作业的科普视频：cut_v6 全片按词对时（下一步方案_20261116 第 2 节）。

对每个画外音段（第 5 章成片段、托盘段、音乐窗除外）：
  1. 声音：和 build_cut_v5 同一套 condense（头 0.15 s、长停顿压短、尾空），词时间换算到段内秒；
  2. 画面动作：读这段源片（资源清单的文件和文件内秒，60 fps 原片），帧差找动作起点；
     S1 六段用手量的锚点（S1_锚点.json：哪个动作对哪个词）；
  3. 锚点：动作 ↔ 词，动态规划选一串先后一致、相邻倍速在阈值内的锚点（相机在动的区间 0.75–1.35，其余 0.6–1.6），
     最后一个锚点之后 1.0× 放到这段画面结束（含段后呼吸），源片不够才放慢；不许末帧停住；
  4. 判定（方案 2.1）：强行对上全部候选锚点时的倍速 → 变速 / 重渲 / Remotion 重出；1080p 一律按选中的锚点变速出片
     （源是 60 fps，0.6× 以上不重复帧），判成重渲 / 重出的写进节拍表，4K 阶段按同一节拍表重出；
  5. 检查：对时后每个 1.5 s 窗口里要有一个落在词上（±0.15 s）的画面动作，没有的窗口记下来。
出：对时/beats/<段>.json（words、anchors、retime、verdict、gaps），画面 _render_tmp/cut6/vo/<段>.mp4（1080p30，长度 = 声音 + 呼吸）。
用法：python retime_v6.py [段号…]（build_cut_v6.py 也直接 import 它）
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CUT = HERE.parent
sys.path.insert(0, str(CUT))
import build_cut_v5 as BC  # noqa: E402
import build_rough as R  # noqa: E402

ROOT = BC.ROOT
FF = BC.FFMPEG
TMP = ROOT / "_render_tmp/cut6"
BEATS = HERE / "beats"
S1A = json.loads((HERE / "S1_锚点.json").read_text(encoding="utf-8"))["segments"]
MW, MH = 160, 90


# v6 审片后：4-10 换 11-11 的 4-10k 版（钥匙逐把试进锁，动作多）
HARD_END = {"4-03"}  # 源片在 fout 处接占位卡，尾巴不得越过 fout
SRC_OVERRIDE = {"4-10": (R.P / "styleframes/art/fusion/s4/S4_410k_novo_1080_v1.mp4", 0.0, 25.0, "")}   # s410k.jsx review=false 重出，不带测试台词字幕


def assets():
    return R.read_assets()


def word_map(it, head, pmax, pkeep):
    w = it["words"]
    half = pkeep / 2
    cuts = [(a["t1"] + half, b["t0"] - half) for a, b in zip(w, w[1:]) if b["t0"] - a["t1"] > pmax]
    s0 = max(0.0, w[0]["t0"] - head)
    return lambda t: t - s0 - sum((c1 - c0) + BC.RULES["xfade"] for c0, c1 in cuts if c1 <= t)


def motion(src, t0, dur):
    """源片 t0 起 dur 秒，60 fps，每帧和前一帧的平均绝对差（0–1）。"""
    p = subprocess.Popen([FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(src), "-an",
                          "-vf", f"fps=60,scale={MW}:{MH}:flags=area,format=gray", "-f", "image2pipe", "-c:v", "rawvideo", "-"],
                         stdout=subprocess.PIPE)
    raw = p.stdout.read()
    p.wait()
    a = np.frombuffer(raw, np.uint8)
    n = len(a) // (MW * MH)
    a = a[:n * MW * MH].reshape(n, MH, MW).astype(np.float32) / 255
    d = np.zeros(n, np.float32)
    t = np.zeros((n, 9 * 16), np.float32)
    if n > 1:
        df = np.abs(a[1:] - a[:-1])
        d[1:] = df.mean(axis=(1, 2))
        t[1:] = df.reshape(n - 1, 9, 10, 16, 10).mean(axis=(2, 4)).reshape(n - 1, -1)   # 16×9 小块：角上出一行字也量得到
    motion.tiles = t
    return d


def onsets(d):
    """动作起点（秒）：任一小块的帧差（平滑 5 帧）从前 0.3 s 的安静处陡升到明显动的那一帧；两个起点至少隔 0.25 s。"""
    t = getattr(motion, "tiles", None)
    if t is None or len(t) < 20:
        return []
    k = np.ones(5) / 5
    s = np.apply_along_axis(lambda x: np.convolve(x, k, "same"), 0, t)
    n = len(s)
    base = np.stack([s[max(0, i - 18):i + 1].min(axis=0) for i in range(n)])
    rise = (s - base).max(axis=1)
    out, last = [], -99
    for i in range(2, n - 2):                     # 三档门槛任一被向上穿过就算一个起点（连续在动的段也能分出新动作）
        if any(rise[i] > th >= rise[i - 1] for th in (0.004, 0.015, 0.05)) and i - last >= 15:
            out.append(i / 60)
            last = i
    return out


def content(w):
    x = "".join(c for c in w if c.isalnum())
    return len(x) >= 4 or any(c.isdigit() for c in x)


def plan_dp(cands, L, avail, d, cam_thr):
    """cands: [(src, cut, dev)]；返回选中的锚点（含 (0,0)）。avail = 源片可用秒（从段首起）。"""
    cands = sorted(set(cands), key=lambda c: (c[1], c[0]))
    P = [(0.0, 0.0, 0.0)] + cands

    def ok(a, b):
        ds, dc = b[0] - a[0], b[1] - a[1]
        if ds < 0.15 or dc < 0.15:
            return False
        s = ds / dc
        seg = d[int(a[0] * 60):int(b[0] * 60) + 1]
        moving = len(seg) and (seg > cam_thr).mean() > 0.8
        lo, hi = (0.75, 1.35) if moving else (0.6, 1.6)
        return lo <= s <= hi

    def tail_ok(a):
        rem_c = L - a[1]
        if rem_c <= 0:
            return False
        rem_s = avail - a[0]
        return rem_s / rem_c >= 0.5 or rem_s >= rem_c

    best = [-1e9] * len(P)
    prev = [-1] * len(P)
    best[0] = 0
    for j in range(1, len(P)):
        for i in range(j):
            if best[i] > -1e8 and ok(P[i], P[j]):
                v = best[i] + 1 - 0.15 * P[j][2]
                if v > best[j]:
                    best[j], prev[j] = v, i
    ends = [j for j in range(len(P)) if best[j] > -1e8 and tail_ok(P[j])]
    j = max(ends, key=lambda j: best[j]) if ends else 0
    chain = []
    while j >= 0:
        chain.append(P[j])
        j = prev[j]
    return chain[::-1]


def forced_speeds(cands):
    """强行对上每个动作最近的那个候选（S1：手量的全部锚点）时的倍速。"""
    pts = [(0.0, 0.0)] + sorted({(c[0], c[1]) for c in cands}, key=lambda c: c[1])
    sp = []
    for a, b in zip(pts, pts[1:]):
        dc = b[1] - a[1]
        sp.append(((b[0] - a[0]) / dc) if dc > 1e-3 else 99.0)
    return sp


def verdict(seg, src, sp, gaps):
    remotion = any(k in str(src) for k in ("S1S2_table", "S6_nocards", "S7_nocards", "S8_nocards"))
    if any(s <= 0 for s in sp):
        v = "重渲（锚点先后和台词相反）"
    elif any(s < 0.5 or s > 2.0 for s in sp):
        v = "重渲（倍速超出 0.5–2.0）"
    elif gaps:
        v = "重渲或补动作（有 1.5 s 窗口没有落在词上的动作）"
    else:
        v = "变速"
    if remotion and not v.startswith("变速"):
        v = "Remotion 按节拍表重出（" + v + "）"
    return v


def retime(seg, it, L, words, piece_len, out, src=None, fin=None, fout=None):
    """it: 录音条目；L: 声音秒；words: 段内词 [{w,t0,t1}]；piece_len: 画面要出的秒（声音 + 呼吸）。"""
    A = assets()[seg]
    pre = ""
    if seg in SRC_OVERRIDE:
        src, fin, fout, pre = SRC_OVERRIDE[seg]
        pre = pre + "," if pre else ""
    src = src or (R.P / A["file"])
    fin = A["fin"] if fin is None else fin
    fout = A["fout"] if fout is None else fout
    dur_file = R.probe_duration(src)
    avail = min(dur_file - fin, fout - fin + (0.0 - 1 / 60 if seg in HARD_END else 0.5))      # v6 审片：不播到这段文件内时间之后（后面是别的段或占位卡）
    d = motion(src, fin, min(avail, max(fout - fin, piece_len) + 4))
    ev = onsets(d)
    slot = fout - fin
    r = slot / max(L, 1e-3)
    cam_thr = max(0.004, float(np.percentile(d, 60)))
    cands, hand = [], False
    if seg in S1A:
        hand = True
        S = S1A[seg]
        for a in S["actions"]:
            if not a.get("word"):
                continue
            hits = [x for x in words if x["w"] == a["word"]]
            if hits:
                cands.append((round(a["src_t"] - S["src_start"], 3), hits[0]["t0"], 0.0))
    else:
        for e in ev:
            for x in words:
                if content(x["w"]):
                    dev = abs(e - x["t0"] * r)
                    if dev <= 2.5:
                        cands.append((round(e, 3), x["t0"], dev))
    chain = plan_dp(cands, L, avail, d, cam_thr)
    if hand:
        sp_forced = forced_speeds(cands)
    else:
        sp_forced = []
    # 映射：锚点之间匀速；最后一个锚点后 1.0×，源不够就匀速放慢到画面末尾
    pts = [(c[0], c[1]) for c in chain]
    ls, lc = pts[-1]
    rem_c = piece_len - lc
    rem_s = min(rem_c, avail - ls)
    pts.append((ls + rem_s, piece_len))
    plan = [dict(src0=round(a[0], 3), src1=round(b[0], 3), out0=round(a[1], 3), out1=round(b[1], 3), speed=round((b[0] - a[0]) / (b[1] - a[1]), 3))
            for a, b in zip(pts, pts[1:]) if b[1] - a[1] > 1e-3]

    def fwd(s):                                   # 源秒 → 段内秒
        for p in plan:
            if p["src0"] <= s <= p["src1"]:
                return p["out0"] + (s - p["src0"]) / p["speed"]
        return None
    landed = [fwd(e) for e in ev]
    landed = [t for t in landed if t is not None]
    on_word = sorted(t for t in landed if any(abs(t - x["t0"]) <= 0.15 for x in words))
    on_word = sorted(set(on_word) | {c[1] for c in chain[1:]})
    xs = [0.0] + on_word + [L]
    gaps = [(round(a, 2), round(b, 2)) for a, b in zip(xs, xs[1:]) if b - a > 1.5]
    sp_all = sp_forced or [p["speed"] for p in plan]
    v = verdict(seg, src, sp_all, gaps)
    # 出片：分段 trim + setpts，拼起来，fps 30
    t0 = fin
    fc = (f"[0:v]{pre[:-1]}[s0];[s0]split={len(plan)}" + "".join(f"[i{k}]" for k in range(len(plan))) + ";") if pre else ""
    fc += "".join(f"[{'i' + str(k) if pre else '0:v'}]trim=start={p['src0']:.4f}:end={p['src1']:.4f},setpts=(PTS-STARTPTS)/{p['speed']:.5f}[v{k}];" for k, p in enumerate(plan))
    fc += "".join(f"[v{k}]" for k in range(len(plan))) + f"concat=n={len(plan)}:v=1:a=0,fps=30,scale=1920:1080:flags=lanczos:out_range=tv,format=yuv420p,setsar=1,tpad=stop_mode=clone:stop_duration=0.2[v]"
    out.parent.mkdir(parents=True, exist_ok=True)
    r_ = subprocess.run([FF, "-y", "-v", "error", "-ss", f"{t0:.3f}", "-i", str(src), "-filter_complex", fc, "-map", "[v]", "-frames:v", str(int(round(piece_len * 30))),
                         *BC.NV, "-an", str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r_.returncode:
        raise SystemExit(f"{seg} 变速出片失败：{r_.stderr[-800:]}")
    B = dict(seg=seg, fps=60, speaker=it["person"], kind="VO",
             note="HKBU SCIE1007 课程作业的科普视频。cut_v6 对时节拍表（retime_v6.py 写）：词是段内秒；anchors 是 [源片秒（段首起）, 段内秒]；retime 是分段倍速。",
             audio=dict(take=it["name"], seconds=round(L, 3), piece=round(piece_len, 3)),
             source=dict(file=str(Path(src).relative_to(R.P)) if str(src).startswith(str(R.P)) else str(src), fin=fin, fout=fout),
             anchor_mode="手量（S1_锚点.json）" if hand else "帧差自动",
             words=words, motion_onsets=[round(e, 3) for e in ev],
             anchors=[[round(a, 3), round(b, 3)] for a, b, _ in chain[1:]],
             events=[dict(id=f"a{k}", word=next(x["w"] for x in words if abs(x["t0"] - b) < 1e-6), src=round(a, 3), f_land=int(round(b * 60))) for k, (a, b, _) in enumerate(chain[1:])],
             frames=dict(len=int(round(L * 60)), first_word=int(round(words[0]["t0"] * 60)), last_word_end=int(round(words[-1]["t1"] * 60))),
             retime=plan, forced_speeds=[round(s, 3) for s in sp_forced], gaps_1p5s=gaps, verdict=v,
             min_speed=round(min(p["speed"] for p in plan), 3), max_speed=round(max(p["speed"] for p in plan), 3))
    BEATS.mkdir(exist_ok=True)
    (BEATS / f"{seg}.json").write_text(json.dumps(B, ensure_ascii=False, indent=1), encoding="utf-8")
    return B
