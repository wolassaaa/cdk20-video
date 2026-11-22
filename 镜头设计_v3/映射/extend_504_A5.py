"""HKBU SCIE1007 课程作业的科普视频：18 的 A5——5-04 配音被粗剪截在 "nanomolar" 中间，"Weak." 没进片。
把 5-04 的配音按源录音接长、总表 master_v2.json 里 5-04 的段长和末尾两个词的时间改过来，后面各段整体后移。

做法（一次性，可重跑：每次都从备份的原版算，不会越接越长）：
  1. 配音：映射/_cache/remotion_public/map/5-04.wav（和 G:/cdk20/work/map_cache/… 同一份）前 SPLICE_S 秒原样保留，
     从这一刻（"nanomolar" 前的停顿里，−50 dBFS）起换成源录音 素材流程_out/C/3_audio/C_vo_5-04_t1_aud.wav 的同一位置
     （互相关定位，和缓存版逐段相关 0.996–0.998、增益 0.997），接口 5 ms 等功率交叉，末尾 30 ms 淡出；新长 = NEW_F ÷ 60 秒。
  2. 总表：5-04 的 len_f / len_s / cut_end_s 加 ADD_F 帧；"nanomolar." 的 t1、"Weak." 的 t0/t1 按源录音能量重量
     （10 ms 一格，> −35 dBFS 算有声）；句 s6、s7 的结尾跟着改；5-04 之后各段 cut_start_f/s、cut_end_s，词 g0/g1/G0，句 g0/g1，
     事件 g_start/g_land/g_end 全部后移 ADD_F 帧。trim 里加 inserts_list 一行，check_master 的逐词复核按它在 v2 声音里补同样长的空白。
  3. 改前备份：master_v2.json → master_v2.bak_1123_A5.json；两份 5-04.wav → 5-04.bak_1123_A5.wav（备份已在就不再盖）。

用法（项目根）：python -X utf8 镜头设计_v3/映射/extend_504_A5.py [--dry]
"""
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
SR, FPS = 48000, 60
GROUP = "5-04"
OLD_F = 1420
NEW_F = 1510                      # A5 写"约 54 帧"；量出来 "Weak." 在原段尾后 1.00–1.37 s，54 帧装不下，取 90 帧（Weak 说完后留 7 帧）
ADD_F = NEW_F - OLD_F
SPLICE_S = 23.25                  # 段内秒："nanomolar" 前的停顿（缓存版 23.20–23.32 s 都在 −50 dBFS 以下）
RAW = ROOT / "素材流程_out/C/3_audio/C_vo_5-04_t1_aud.wav"
WAVS = [ROOT / "镜头设计_v3/映射/_cache/remotion_public/map/5-04.wav", Path("G:/cdk20/work/map_cache/remotion_public/map/5-04.wav")]
MAP = HERE / "master_v2.json"
BAK = HERE / "master_v2.bak_1123_A5.json"


def read_raw():
    b = subprocess.run([FF, "-v", "error", "-i", str(RAW), "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"], capture_output=True).stdout
    return np.frombuffer(b, np.float32).astype(np.float64)


def read_wav(p):
    with wave.open(str(p), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        b = w.readframes(n)
    assert sw == 2 and sr == SR, (p, sw, sr)
    return np.frombuffer(b, np.int16).reshape(-1, ch).astype(np.float64) / 32768.0, ch


def write_wav(p, x):
    y = np.clip(np.round(x * 32767), -32768, 32767).astype(np.int16)
    tmp = p.with_name(p.stem + "_tmp.wav")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(y.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())
    tmp.replace(p)


def align(raw, cur):
    """缓存版 t=0 在源录音里的秒数（用缓存版 20–23.2 s 那一段互相关）和增益。"""
    a0, a1 = 20.0, 23.2
    x = cur[int(a0 * SR):int(a1 * SR)]
    best = None
    for off in range(int(20.2 * SR), int(20.8 * SR)):
        y = raw[off:off + len(x)]
        c = float(np.dot(x, y))
        if best is None or c > best[0]:
            best = (c, off)
    off = best[1]
    y = raw[off:off + len(x)]
    corr = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))
    gain = float(np.dot(x, y) / np.dot(y, y))
    return off / SR - a0, gain, corr


def words_from_energy(raw, t_off, gain):
    """段内秒：nanomolar 的结尾、Weak 的起止（10 ms 一格，> −35 dBFS）。"""
    def db(t):
        a = raw[int((t + t_off) * SR):int((t + t_off + 0.01) * SR)] * gain
        return 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-12)
    ts = np.arange(23.30, 25.30, 0.01)
    on = [t for t in ts if db(t) > -35]
    # 两团：nanomolar（23.3x 起）和 Weak（24.6x 起），中间隔 ≥ 0.2 s 的静
    groups, cur = [], [on[0]]
    for t in on[1:]:
        if t - cur[-1] > 0.2:
            groups.append(cur)
            cur = [t]
        else:
            cur.append(t)
    groups.append(cur)
    assert len(groups) >= 2, groups
    nano, weak = groups[0], groups[1]
    return round(nano[0], 3), round(nano[-1] + 0.01, 3), round(weak[0], 3), round(weak[-1] + 0.01, 3)


def main():
    dry = "--dry" in sys.argv
    raw = read_raw()
    bak0 = WAVS[0].with_name("5-04.bak_1123_A5.wav")
    src0 = bak0 if bak0.exists() else WAVS[0]
    cur, ch = read_wav(src0)
    assert abs(len(cur) / SR - OLD_F / FPS) < 0.01, f"缓存版长 {len(cur) / SR:.3f} s，不是 {OLD_F} 帧的原版"
    t_off, gain, corr = align(raw, cur.mean(axis=1))
    n0, n1, w0, w1 = words_from_energy(raw, t_off, gain)
    print(f"源录音偏移 {t_off:.4f} s，增益 {gain:.4f}，相关 {corr:.4f}；nanomolar {n0}–{n1} s，Weak {w0}–{w1} s（段内）")
    assert w1 < NEW_F / FPS - 0.05, "Weak 说完离新段尾不到 0.05 s"

    # ---- 1. 配音
    ns, nn = int(SPLICE_S * SR), int(round(NEW_F / FPS * SR))
    x = int(0.005 * SR)
    r0 = int(round((SPLICE_S + t_off) * SR)) - x                          # 源录音里对应缓存版第 ns − x 个采样
    tail = raw[r0:r0 + (nn - ns + x)] * gain                              # tail[i] ↔ 缓存版第 ns − x + i 个采样
    tail = np.repeat(tail[:, None], ch, axis=1)
    out = np.zeros((nn, ch))
    out[:ns] = cur[:ns]
    k = np.linspace(0, 1, x)[:, None]
    out[ns - x:ns] = cur[ns - x:ns] * np.cos(k * np.pi / 2) + tail[:x] * np.sin(k * np.pi / 2)  # 5 ms 等功率交叉（落在停顿里）
    out[ns:ns + len(tail) - x] = tail[x:]
    f = int(0.03 * SR)
    out[-f:] *= np.linspace(1, 0, f)[:, None]
    print(f"新配音 {len(out) / SR:.4f} s = {len(out) / SR * FPS:.2f} 帧；接口在 {SPLICE_S} s；末 50 ms 峰值 {20 * np.log10(np.abs(out[-int(0.05 * SR):]).max() + 1e-12):.1f} dBFS")

    # ---- 2. 总表
    T = json.loads((BAK if BAK.exists() else MAP).read_text(encoding="utf-8"))
    G = T["groups"]
    gi = [g["group"] for g in G].index(GROUP)
    g = G[gi]
    assert g["len_f"] == OLD_F, g["len_f"]
    add_s = ADD_F / FPS
    g["len_f"] = NEW_F
    g["len_s"] = round(NEW_F / FPS, 4)
    g["cut_end_s"] = round(g["cut_start_s"] + g["len_s"], 4)
    W = {w["norm"]: w for w in g["words"]}
    for key, (a, b) in (("nanomolar", (n0, n1)), ("weak", (w0, w1))):
        w = W[key]
        d_src = w["src"]["t0"] - w["t0"]
        w.update(t0=a, t1=b, f0=round(a * FPS), f1=round(b * FPS), g0=round(g["cut_start_s"] + a, 4), g1=round(g["cut_start_s"] + b, 4),
                 G0=g["cut_start_f"] + round(a * FPS), verified=True, match="A5_extend")
        w["src"].update(t0=round(a + d_src, 3), t1=round(b + d_src, 3))
        w["a5_note"] = "18 的 A5（11-23）：原段尾截在 nanomolar 中间，按源录音能量重量（> −35 dBFS）；Weak. 原来不在片里"
    for s in g["sentences"]:
        if s["w_last"] in (W["nanomolar"]["wid"], W["weak"]["wid"]):
            w = next(x for x in g["words"] if x["wid"] == s["w_last"])
            s.update(t1=w["t1"], f1=w["f1"], g1=w["g1"])
        if s["w_first"] == W["weak"]["wid"]:
            s.update(t0=W["weak"]["t0"], f0=W["weak"]["f0"], g0=W["weak"]["g0"])
    for h in G[gi + 1:]:
        h["cut_start_f"] += ADD_F
        h["cut_start_s"] = round(h["cut_start_s"] + add_s, 4)
        if "cut_end_s" in h:
            h["cut_end_s"] = round(h["cut_end_s"] + add_s, 4)
        for w in h["words"]:
            w["g0"] = round(w["g0"] + add_s, 4)
            w["g1"] = round(w["g1"] + add_s, 4)
            w["G0"] += ADD_F
        for s in h["sentences"]:
            s["g0"] = round(s["g0"] + add_s, 4)
            s["g1"] = round(s["g1"] + add_s, 4)
        for e in h["events"]:
            for kk in ("g_start", "g_land", "g_end"):
                if e.get(kk) is not None:
                    e[kk] = round(e[kk] + add_s, 4)
    tr = T.setdefault("trim", {})
    tr["inserts_list"] = [dict(group=GROUP, v2_g_s=round(g["cut_start_s"] + OLD_F / FPS, 4), add_f=ADD_F,
                               why="18 的 A5：5-04 配音按源录音接长（nanomolar 说完、Weak.），后面各段后移；cut 声音里没有这一截，逐词复核时补空白")]
    if "len_f_v2" in tr:
        tr["len_f_v2_before_inserts"] = tr.get("len_f_v2_before_inserts", tr["len_f_v2"])
        tr["len_f_v2"] = tr["len_f_v2_before_inserts"] + ADD_F
    T["note"] = T["note"].split(" 11-23 A5：")[0] + f" 11-23 A5：5-04 段尾接长 {ADD_F} 帧（{OLD_F} → {NEW_F}），后面各段后移，见 trim.inserts_list 和 映射/extend_504_A5.py。"
    if dry:
        print("dry：不写")
        return
    if not BAK.exists():
        shutil.copy2(MAP, BAK)
    for p in WAVS:
        b = p.with_name("5-04.bak_1123_A5.wav")
        if p.exists() and not b.exists():
            shutil.copy2(p, b)
    for p in WAVS:
        write_wav(p, out)
    tmp = MAP.with_name(MAP.stem + "_tmp.json")
    tmp.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(MAP)
    print(f"写好：{MAP.name}（5-04 {OLD_F} → {NEW_F} 帧，后面 {len(G) - gi - 1} 段后移 {ADD_F} 帧），配音 {len(WAVS)} 份；备份 {BAK.name}、5-04.bak_1123_A5.wav")


if __name__ == "__main__":
    main()
