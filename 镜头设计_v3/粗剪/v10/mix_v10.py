"""HKBU SCIE1007 课程作业的科普视频：v10 最小混音（M2，19 的 2.1–2.3、2.5、2.6）。位 1，11-23。

人声分轨 + 底乐（含窗口歌、混响甩尾）→ 量综合响度 → 整体增益到 −14.0 LUFS → 4 倍过采样真峰值限幅（−2.1 dBTP，给 AAC 留余量）→ master_v10.wav。
19 的 2.3 第 6 条写的 pedalboard.Limiter 实际是 JUCE 限幅器：先过一级 −10 dB、4:1 的压缩，再把阈值补到 0 dBFS，等于加了总线压缩
（试跑 LRA 掉到 3.7、要倒扣 8.7 dB），和同条的“不加总线压缩”冲突，所以换成 synth_bed.tp_limit。音效层以后补（2.4）。

  py -3.11 -X utf8 镜头设计_v3/粗剪/v10/mix_v10.py            # 底乐和清单对不上就先重渲底乐（约 6 分钟），再混、再查
  py -3.11 -X utf8 镜头设计_v3/粗剪/v10/mix_v10.py --check    # 只查已有的 master_v10.wav

底乐和人声分轨都由 `镜头设计_v3/音乐/synth_bed.py` 的 v10 模式按当前清单 `粗剪/v10/manifest_v10.json` 出：
  - 人声分轨 voice.wav：每段拉齐到 −14.5 LUFS，修两头、补句尾（2.3 第 1 条），EGG 段用成片自带的声音（彩蛋对白和彩蛋底乐已混好）。
  - 音乐 bed_v10.wav：底乐五轨 + 窗口歌 + 甩尾，已闪避（2.2）、已乘母带增益。
别人渲的 `G:/cdk20/work/bed_v10/` 是按 00:10 的旧清单（64606 帧）渲的，段长对不上，不拿来切接；本脚本的底乐渲到
`G:/cdk20/work/audio/v10/bed/`（CDK20_BED_OUT），用 `_manifest_sig.json` 记它对应的清单，清单一变就重渲。

输出 `G:/cdk20/work/audio/v10/master_v10.wav`（48 kHz、24 bit 立体声）和 `qc_audio_v10.json`（M1、M2、M5、M9、M10、M11）。
19 的 2.3 写的是 `音乐/mix_v10.py` 出 `master.wav`；这次按任务单放在 粗剪/v10，文件名 master_v10.wav。
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

OUT = Path("G:/cdk20/work/audio/v10")
BED = OUT / "bed"
os.environ["CDK20_BED_OUT"] = str(BED)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "镜头设计_v3/音乐"))
import synth_bed as SB                     # noqa: E402  (puts pydeps and the footage venv on sys.path)
import numpy as np                         # noqa: E402
from scipy import signal                   # noqa: E402
import soundfile as sf                     # noqa: E402

SR, FPS = SB.SR, SB.FPS
MAN = HERE / "manifest_v10.json"
MASTER = OUT / "master_v10.wav"
QC = OUT / "qc_audio_v10.json"
FF_READ = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
TARGET, TOL, CEIL = -14.0, 0.3, -1.5
LIM_CEIL = -2.1   # 限幅上限：母带要 ≤ −1.5 dBTP，编成 AAC 320k 后还要 ≤ −1.0；试跑 −1.6 上片后 AAC 是 −0.8，所以多留 0.5 dB
BLK = SR * 60

# 11-24 R2-05（导演检查_20261124/_审查批2.md）：这几段人声按"和前后段同响度 ±1 LU"补增益。
# 做法：混音前量每段念词时段（manifest 的 first_word_f…last_word_end_f）人声 + 底乐的综合响度（BS.1770，K 加权、门限），
# 和前后最近的有词段的平均比，差 > VOICE_TOL 就给这段人声补上这个差（只乘人声分轨，段两头 20 ms 线性过渡），限 ±VOICE_MAX。
# 审查单写的固定值（5-09 +4.5、5-05+5-06 +2.5、6-10 +2.0 dB）是在 rc07 上量的念词时段 RMS；11-24 用同一个 rc07 复量（K 加权综合响度）
# 三段和前后段的差都在 ±0.6 LU 内，按量的数补（量出来差 ≤ 1 LU 就不加）；要硬加固定值，写进 VOICE_GAIN_FIXED（优先于量的数）。
VOICE_FIX = ("5-09", "5-05+5-06", "6-10")
VOICE_GAIN_FIXED = {}          # 例：{"5-09": 4.5}；空 = 全按量的数
VOICE_TOL, VOICE_MAX, VOICE_RAMP = 1.0, 6.0, SR // 50


def man_sig(M):
    rows = [(s["group"], s["frames"], s.get("voice_wav") or "", s["file"] if s["group"] == "EGG" else "") for s in M["segments"]]
    return hashlib.sha1(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()


def ensure_bed(M, force=False):
    sig = man_sig(M)
    stamp = BED / "_manifest_sig.json"
    ok = (not force and stamp.exists() and json.loads(stamp.read_text("utf8")).get("sig") == sig
          and (BED / "voice.wav").exists() and (BED / "bed_v10.wav").exists()
          and sf.info(str(BED / "voice.wav")).frames == M["total_f"] * (SR // FPS))
    if ok:
        print("底乐和人声分轨已对上当前清单，直接用", BED, flush=True)
        return json.loads((BED / "render_info.json").read_text("utf8"))
    print("底乐按当前清单重渲（synth_bed --full 的 v10 流程）→", BED, flush=True)
    BED.mkdir(parents=True, exist_ok=True)
    SB.V10_OUT.mkdir(parents=True, exist_ok=True)
    P = SB.v10_full()
    stamp.write_text(json.dumps(dict(sig=sig, total_f=M["total_f"], manifest_built=M.get("built"),
                                     segments=[[s["group"], s["frames"]] for s in M["segments"]],
                                     made=time.strftime("%Y-%m-%d %H:%M")), ensure_ascii=False, indent=1), "utf8")
    return json.loads((BED / "render_info.json").read_text("utf8"))


def tp_env(x):
    """4 倍过采样的逐采样真峰值包络。"""
    return np.abs(signal.resample_poly(x, 4, 1, axis=0)).reshape(-1, 4, x.shape[1]).max(axis=(1, 2))[:len(x)]


def seg_lufs(fv, fm, a, z):
    """[a, z) 采样里人声 + 底乐的综合响度（BS.1770 门限）。"""
    fv.seek(a); fm.seek(a)
    y = (fv.read(z - a, dtype="float64", always_2d=True) + fm.read(z - a, dtype="float64", always_2d=True))
    if y.shape[1] == 1:
        y = np.repeat(y, 2, 1)
    k = signal.lfilter(SB._KB1, SB._KA1, y, axis=0)
    k = signal.lfilter(SB._KB2, SB._KA2, k, axis=0)
    pw = np.pad((k ** 2).sum(1), (0, (-len(k)) % SB.BIN)).reshape(-1, SB.BIN).sum(1)
    return SB.lufs_bins(pw)


def voice_gains(M, fv, fm):
    """R2-05：VOICE_FIX 里每段的人声增益（dB）和量的数。返回 ([(起采样, 止采样, dB)], info)。"""
    S, spf = M["segments"], SR // FPS
    def span(s):
        if s.get("first_word_f") is None or s.get("last_word_end_f") is None or s["group"] == "EGG" or s["kind"] == "MUSIC":
            return None
        return (s["start_f"] + s["first_word_f"]) * spf, (s["start_f"] + s["last_word_end_f"]) * spf
    out, info = [], {}
    for i, s in enumerate(S):
        if s["group"] not in VOICE_FIX:
            continue
        sp = span(s)
        if not sp:
            continue
        me = seg_lufs(fv, fm, *sp)
        nb = []
        for rng in (range(i - 1, -1, -1), range(i + 1, len(S))):
            for j in rng:
                q = span(S[j])
                if q:
                    nb.append((S[j]["group"], seg_lufs(fv, fm, *q)))
                    break
        ref = float(np.mean([v for _, v in nb])) if nb else me
        d = ref - me
        g = VOICE_GAIN_FIXED.get(s["group"], d if abs(d) > VOICE_TOL else 0.0)
        g = float(np.clip(g, -VOICE_MAX, VOICE_MAX))
        info[s["group"]] = dict(self_lufs=round(me, 2), neighbours={k: round(v, 2) for k, v in nb}, diff_lu=round(d, 2), gain_db=round(g, 2),
                                how="固定值" if s["group"] in VOICE_GAIN_FIXED else ("按量的数补齐" if g else f"差 ≤ {VOICE_TOL} LU，不加"))
        print("人声增益", s["group"], info[s["group"]], flush=True)
        if abs(g) > 1e-3:
            out.append((s["start_f"] * spf, (s["start_f"] + s["frames"]) * spf, g))
    return out, info


def mix(M):
    n = M["total_f"] * (SR // FPS)
    fv, fm = sf.SoundFile(str(BED / "voice.wav")), sf.SoundFile(str(BED / "bed_v10.wav"))
    assert fv.frames == n and fm.frames == n, (fv.frames, fm.frames, n)
    vg, vinfo = voice_gains(M, fv, fm)

    def vgain(a, z):
        """[a, z) 采样的人声增益包络（段内 dB 值，段两头 VOICE_RAMP 采样线性过渡）。"""
        g = np.ones(z - a, np.float32)
        for s0, s1, db in vg:
            lo, hi = max(a, s0), min(z, s1)
            if lo >= hi:
                continue
            t = np.arange(lo, hi)
            w = np.minimum(1.0, np.minimum(t - s0 + 1, s1 - t) / VOICE_RAMP)
            g[lo - a:hi - a] *= (1.0 + (SB.db(db) - 1.0) * w).astype(np.float32)
        return g[:, None]

    def read(a, z):
        fv.seek(a); fm.seek(a)
        return fv.read(z - a, dtype="float32", always_2d=True) * vgain(a, z) + fm.read(z - a, dtype="float32", always_2d=True)

    def kacc(bins, y, zs):
        k, zs[0] = signal.lfilter(SB._KB1, SB._KA1, y, axis=0, zi=zs[0])
        k, zs[1] = signal.lfilter(SB._KB2, SB._KA2, k, axis=0, zi=zs[1])
        pw = np.pad((k ** 2).sum(1), (0, (-len(k)) % SB.BIN))
        return pw.reshape(-1, SB.BIN).sum(1)

    # 第一遍：相加，量综合响度（不压）
    bins = np.zeros(int(np.ceil(n / SB.BIN)))
    zs = [np.zeros((2, 2)), np.zeros((2, 2))]
    for a in range(0, n, BLK):
        z = min(n, a + BLK)
        p = kacc(bins, read(a, z).astype(np.float64), zs)
        bins[a // SB.BIN:a // SB.BIN + len(p)] += p
    L1 = SB.lufs_bins(bins)
    info = dict(sum_lufs=round(L1, 2), voice_gain=vinfo, limiter="4 倍过采样真峰值限幅（synth_bed.tp_limit，前瞻窗 241 采样），不用 pedalboard.Limiter")
    # 第二遍起：整体增益 → 真峰值限幅（上限 LIM_CEIL）→ 量 → 差 > 0.3 LU 再调一次
    gain_db, ceil = TARGET - L1, LIM_CEIL
    tmp = OUT / "_master_tmp.wav"
    for it in range(4):
        g = SB.db(gain_db)
        out = sf.SoundFile(str(tmp), "w", SR, 2, "PCM_24")
        bins = np.zeros_like(bins)
        zs = [np.zeros((2, 2)), np.zeros((2, 2))]
        tpk, tpl_n = 0.0, 0
        for a in range(0, n, BLK):
            z = min(n, a + BLK)
            y = read(a, z).astype(np.float64) * g
            e = tp_env(y)
            if e.max() > SB.db(ceil):
                tpl_n += int((e > SB.db(ceil)).sum())
                y = SB.tp_limit(y, e, SB.db(ceil))
            tpk = max(tpk, float(tp_env(y).max()))
            out.write(y.astype(np.float32))
            p = kacc(bins, y, zs)
            bins[a // SB.BIN:a // SB.BIN + len(p)] += p
        out.close()
        L2 = SB.lufs_bins(bins)
        tp_db = 20 * np.log10(tpk + 1e-12)
        info[f"pass{it + 1}"] = dict(gain_db=round(gain_db, 2), ceiling_dbtp=round(ceil, 2), lufs=round(L2, 2), tp_dbtp_4x=round(tp_db, 2),
                                     tp_limited_samples=tpl_n)
        print("混音第", it + 1, "遍", info[f"pass{it + 1}"], flush=True)
        if abs(L2 - TARGET) <= TOL and tp_db <= CEIL:
            break
        gain_db += TARGET - L2
        if tp_db > CEIL:
            ceil -= tp_db - CEIL + 0.05
    fv.close(); fm.close()
    if MASTER.exists():
        MASTER.replace(MASTER.with_name(f"master_v10.bak_{time.strftime('%m%d_%H%M')}.wav"))
    tmp.replace(MASTER)
    return info


# ------------------------------------------------------------------ 检查（19 的 2.6）
def ebur(path):
    r = subprocess.run([FF_READ, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    tail = r[r.rfind("Summary:"):]
    g = lambda p: float(re.search(p, tail).group(1))
    return dict(I=g(r"I:\s+(-?[\d.]+) LUFS"), LRA=g(r"LRA:\s+(-?[\d.]+) LU"), TP=g(r"Peak:\s+(-?[\d.]+) dBFS"))


def silences(path, noise=-50, d=0.5):
    r = subprocess.run([FF_READ, "-hide_banner", "-nostats", "-i", str(path), "-af", f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r)]
    return [(s, en[i] if i < len(en) else None) for i, s in enumerate(st)]


def rd(path, t0, t1):
    with sf.SoundFile(str(path)) as f:
        a = max(0, int(round(t0 * SR)))
        f.seek(a)
        return f.read(max(0, int(round(t1 * SR)) - a), dtype="float64", always_2d=True)


def check(M, rinfo, minfo):
    segs = M["segments"]
    T = M["total_f"] / FPS
    R = dict(file=str(MASTER), manifest_built=M.get("built"), total_f=M["total_f"], made=time.strftime("%Y-%m-%d %H:%M"),
             bed_dir=str(BED), mix=minfo, items={})
    I = R["items"]
    # M1、M2、M3（M3 不在本次必过之列，照记）
    e = ebur(MASTER)
    I["M1"] = dict(want="−14.5 到 −13.5 LUFS", I=e["I"], ok=-14.5 <= e["I"] <= -13.5)
    with sf.SoundFile(str(MASTER)) as f:
        tpk = 0.0
        dc = np.zeros(2)
        nan = False
        n = f.frames
        while True:
            x = f.read(BLK, dtype="float64", always_2d=True)
            if not len(x):
                break
            nan |= bool(np.isnan(x).any())
            dc += x.sum(0)
            tpk = max(tpk, float(tp_env(x).max()))
    tp4 = 20 * np.log10(tpk + 1e-12)
    I["M2"] = dict(want="master_v10.wav ≤ −1.5 dBTP（成片 AAC ≤ −1.0 由拼片后再量）", ffmpeg_peak=e["TP"], numpy_4x=round(tp4, 2),
                   ok=max(e["TP"], tp4) <= -1.5 + 1e-6)
    I["M3_记录"] = dict(want="5–11 LU（本次不要求）", LRA=e["LRA"], ok=5 <= e["LRA"] <= 11)
    # M5 底乐让位：逐段只取说话时间，人声 vs（底乐 + 歌 + 甩尾）
    hp_b = signal.butter(2, [120, 6000], "bp", fs=SR, output="sos")
    rows = []
    for s in segs:
        if s["kind"] not in ("VO", "ON-CAM") or s["group"] == "EGG":
            continue
        t0, t1 = s["start_f"] / FPS, (s["start_f"] + s["frames"]) / FPS
        v, m = rd(BED / "voice.wav", t0, t1), rd(BED / "bed_v10.wav", t0, t1)
        x = signal.sosfilt(hp_b, v.mean(1))
        n20 = len(x) // 960 * 960
        r = 20 * np.log10(np.sqrt((x[:n20] ** 2).reshape(-1, 960).mean(1)) + 1e-12)
        mk = np.repeat(r > -45, 960)
        if mk.sum() < SR // 2:
            continue
        Lv, Lm = SB.lufs(v[:n20][mk]), SB.lufs(m[:n20][mk])
        need = 14.0 if s["kind"] == "VO" else 15.5
        rows.append(dict(seg=s["group"], kind=s["kind"], voice=round(Lv, 2), music=round(Lm, 2), gap=round(Lv - Lm, 2), need=need,
                         ok=Lv - Lm >= need))
    gaps = [r_["gap"] for r_ in rows]
    med = float(np.median(gaps)) if gaps else None
    I["M5"] = dict(want="画外音段差 ≥ 14.0 LU，出镜段 ≥ 15.5，全片中位 15 ± 1", median=round(med, 2) if med is not None else None,
                   n=len(rows), bad=[r_ for r_ in rows if not r_["ok"]], ok=bool(rows) and all(r_["ok"] for r_ in rows) and abs(med - 15) <= 1,
                   per_segment=rows)
    # M9 歌的干声：每个窗口之后第一个旁白词开口那一刻 ≤ −60 dBFS（song.npy 是干声，乘母带增益，不算闪避，偏严）
    song = np.load(BED / "_work/song.npy", mmap_mode="r")
    passes = sorted(k for k in minfo if k.startswith("pass"))
    gm = SB.db(rinfo.get("master_db", 0.0)) * SB.db(minfo[passes[-1]]["gain_db"] if passes else 0.0)
    m9 = []
    for i, s in enumerate(segs):
        if s["kind"] != "MUSIC" or s["group"] == "W0":
            continue
        for s2 in segs[i + 1:]:
            if s2["kind"] == "VO" and s2.get("first_word_f") is not None:
                t = (s2["start_f"] + s2["first_word_f"]) / FPS
                a = int(t * SR)
                seg = np.asarray(song[max(0, a - 480):a + 480], dtype=np.float64) * gm
                pk = float(20 * np.log10(np.abs(seg).max() + 1e-12))
                m9.append(dict(window=s["group"], word_seg=s2["group"], t=round(t, 3), song_dry_peak_dbfs=round(pk, 1), ok=pk <= -60))
                break
    I["M9"] = dict(want="窗口后第一个旁白词开口那一刻，歌的干声 ≤ −60 dBFS（取 ±10 ms 峰值）", rows=m9, ok=all(r_["ok"] for r_ in m9))
    # M10 意外的静音：只许 W5 结束到彩蛋第一个词之间（≤ 1.6 s）和文件末尾
    sil = silences(MASTER)
    egg = next((s for s in segs if s["group"] == "EGG"), None)
    w5 = next((s for s in segs if s["group"] == "W5"), None)
    allowed = []
    if egg is not None:
        allowed.append((w5["start_f"] / FPS + w5["frames"] / FPS - 0.6 if w5 else egg["start_f"] / FPS - 0.6,
                        (egg["start_f"] + (egg.get("first_word_f") or 0)) / FPS + 0.6))
    # 5-05 停转结束到 5-06 段尾是设计的静音（19 的 M7 例外、M8 要求 < −70 dBFS），记作允许
    s56 = next((s for s in segs if s["group"].startswith("5-05")), None)
    designed = [(s56["start_f"] / FPS, (s56["start_f"] + s56["frames"]) / FPS + 0.25)]  # 静音可以伸进 5-07 段首 0.25 s（下一段第一声之前） if s56 else []
    bad, ok_designed = [], []
    for s0, s1 in sil:
        s1_ = s1 if s1 is not None else T
        at_end = s1 is None or s1_ >= T - 0.05
        inside = any(a_ <= s0 and s1_ <= b_ for a_, b_ in allowed) and (s1_ - s0) <= 1.6
        if not (at_end or inside) and any(a_ <= s0 and s1_ <= b_ for a_, b_ in designed):
            ok_designed.append(dict(start=round(s0, 3), end=round(s1_, 3), dur=round(s1_ - s0, 3), why="5-05 停转后的设计静音（M8）"))
        elif not (at_end or inside):
            bad.append(dict(start=round(s0, 3), end=round(s1_, 3), dur=round(s1_ - s0, 3), seg=next(
                (x["group"] for x in segs if x["start_f"] / FPS <= s0 < (x["start_f"] + x["frames"]) / FPS), None)))
    I["M10"] = dict(want="silencedetect −50 dB / 0.5 s：只许 W5→彩蛋第一个词（≤ 1.6 s）和文件末尾", found=[(round(a_, 3), round(b_, 3) if b_ else None) for a_, b_ in sil],
                    designed=ok_designed, bad=bad, ok=not bad)
    # M11 接缝：每个段界 ±10 ms，人声、音乐、母带三条的相邻采样差；直流；NaN
    worst = []
    for s in segs[1:]:
        t = s["start_f"] / FPS
        for name, p in (("voice", BED / "voice.wav"), ("music", BED / "bed_v10.wav"), ("master", MASTER)):
            x = rd(p, t - 1.0, t + 1.0)
            dd = np.abs(np.diff(x, axis=0)).max(1)
            c = int(1.0 * SR)
            d = float(dd[c - 480:c + 480].max())
            ctx = float(max(dd[:c - 480].max(), dd[c + 480:].max()))          # 接缝两侧 10 ms–1 s 里内容本身（别的鼓点）的最大相邻差
            worst.append((d, s["group"], name, round(ctx, 4)))
    worst.sort(reverse=True)
    pops = [w for w in worst if w[0] > 0.1 and w[0] > 1.5 * w[3]]               # 比 0.1 大、又比两侧内容大一半以上才算爆音
    dcv = (dc / max(1, n)).tolist()
    I["M11"] = dict(want="段界 ±10 ms 相邻采样差 ≤ 0.1；超过的要不大于接缝两侧 10 ms–1 s 内容自身最大差的 1.5 倍（鼓、噪声起音不算爆音）；直流 < 1e-4；没有 NaN",
                    max_jump=round(worst[0][0], 4) if worst else 0,
                    worst=[dict(jump=round(a_, 4), seg=b_, stem=c_, context_max=d_) for a_, b_, c_, d_ in worst[:8]],
                    pops=[dict(jump=round(a_, 4), seg=b_, stem=c_, context_max=d_) for a_, b_, c_, d_ in pops],
                    dc=[round(v_, 7) for v_ in dcv], nan=nan,
                    ok=not pops and max(abs(v_) for v_ in dcv) < 1e-4 and not nan)
    need = ["M1", "M2", "M5", "M9", "M10", "M11"]
    R["pass"] = {k: bool(I[k]["ok"]) for k in need}
    R["all_pass"] = all(R["pass"].values())
    QC.write_text(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), "utf8")
    print(json.dumps(R["pass"], ensure_ascii=False), "全过" if R["all_pass"] else "有不过", flush=True)
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只查已有的 master_v10.wav")
    ap.add_argument("--rebed", action="store_true", help="不管签名，强制重渲底乐")
    A = ap.parse_args()
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    M = json.loads(MAN.read_text("utf8"))
    if A.check:
        rinfo = json.loads((BED / "render_info.json").read_text("utf8"))
        minfo = json.loads(QC.read_text("utf8")).get("mix", {}) if QC.exists() else {}
    else:
        rinfo = ensure_bed(M, A.rebed)
        print(f"底乐就绪（{time.time() - t0:.0f} s）", flush=True)
        minfo = mix(M)
        print(f"母带写完（{time.time() - t0:.0f} s）", MASTER, flush=True)
    check(M, rinfo, minfo)
    print(f"用时 {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
