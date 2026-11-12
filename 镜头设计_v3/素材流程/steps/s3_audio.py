"""HKBU SCIE1007 coursework video: step 3 声音 of the phone-footage pipeline. Runs on the CPU (no 5080 needed).

Every take step 2 aligned (cam and vo), the WHOLE original soundtrack, same length as the original:
  1. 48 kHz mono; if step 0 found clipping, ffmpeg adeclip first (A5)
  2. DeepFilterNet3 noise suppression, at most enhance_atten_lim_db off, so gaps keep faint room tone (A2, A4)
  3. one gain for the whole file, set from the loudness of the spoken part only (step 2's cut), then a true-peak
     limiter: every take lands at target_lufs, true peak under true_peak_db (A7)
  4. checks (handbook G3): loudness of the spoken part, true peak, noise floor and speech level of the spoken part,
     clipped samples, length against the decoded original, and the script re-aligned onto the processed sound:
     no solidly aligned word moves (words not eaten); the noise floor is measured where nobody speaks. The aligner is a little less sure of denoised speech
     (mean score about -0.02, up to -0.08 on single takes, timings unchanged), so its mean is only reported; timing
     is checked only on words that aligned solidly before (weak ones, e.g. a word the member skipped, wander)
     A take whose noise floor is still over the limit is redone once with EXTRA_ATTEN dB more suppression.
Not done here: de-reverb (A3), plosives and sibilance (A6), room-tone matching between people (A8, in step 5).
Input:  the originals (read only), 0_probe/probe.json, 2_pick/align/<name>.json
Output: 3_audio/<name>_aud.wav (48 kHz, 24 bit, mono), 3_audio/results.json, 3_audio/声音验收.md
"""
import time

import numpy as np
import soundfile as sf

import common as C
import enhance_models as E
from steps.s2_pick import Aligner, load_audio

SR = 48000
NAME_SUFFIX = "_aud"
CHECK = {"lufs_tol": 1.0, "floor_max_db": -40.0, "speech_over_floor_db": 25.0, "len_tol_s": 0.02,
         "word_shift_max_s": 0.15, "word_shift_note_s": 0.05, "solid": 0.5,                    # timing is checked on words aligned at least this well
         "collapse": [0.4, 0.15]}                                   # a word over 0.4 before and under 0.15 after = eaten
EXTRA_ATTEN = 6


def takes(ctx):
    adir = ctx.out / C.STEP_DIRS[2] / "align"
    return [C.read_json(p) for p in sorted(adir.glob("*.json"))]


def inputs(ctx):
    return [ctx.src / t["file"] for t in takes(ctx)] + [ctx.out / C.STEP_DIRS[0] / "probe.json"] + \
        sorted((ctx.out / C.STEP_DIRS[2] / "align").glob("*.json"))


def params(ctx):
    return {"audio": {k: v for k, v in ctx.cfg["audio"].items() if not k.startswith("_")}, "check": CHECK, "extra_atten": EXTRA_ATTEN, "version": 7}


def span_measure(path, t0, t1):
    tmp = C.tmp() / "s3_span.wav"
    C.ffmpeg("-i", path, "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-c:a", "pcm_s24le", tmp)
    return E.measure(tmp)


def gap_floor(path, speech, gain_db=0.0):
    """Noise floor where nobody speaks (dB): the file before the speech (to 0.15 s before it) and after it (from
    0.3 s after it), `speech` being step 2's [start, end] of what was actually said. Median of 50 ms window levels,
    so the tap of a finger starting or stopping the recording does not count as floor. Inside the line the
    aligner's word ends are too tight to find true pauses. None when under 0.2 s of quiet."""
    z, sr = sf.read(str(path), dtype="float32")
    if z.ndim > 1:
        z = z.mean(axis=1)
    win = int(sr * 0.05)
    levels = []
    for g in (z[: max(0, int((speech[0] - 0.15) * sr))], z[int((speech[1] + 0.3) * sr):]):
        n = len(g) // win
        if n:
            levels.append(np.sqrt((g[: n * win].reshape(n, win) ** 2).mean(axis=1)))
    if not levels or sum(map(len, levels)) < 4:
        return None
    return round(float(20 * np.log10(np.median(np.concatenate(levels)) + 1e-12)) + gain_db, 1)


def run(ctx, out):
    cfg = ctx.cfg["audio"]
    target, tp = cfg["target_lufs"], cfg["true_peak_db"]
    probe = {f["file"]: f for f in C.read_json(ctx.out / C.STEP_DIRS[0] / "probe.json")["files"]}
    tmp = C.tmp()
    tmp.mkdir(exist_ok=True)
    fa = Aligner()
    rows, outputs = [], []
    for t in takes(ctx):
        src = ctx.src / t["file"]
        pr = probe[t["file"]]
        t_start = time.time()
        raw = tmp / "s3_raw.wav"
        af = "adeclip" if pr["audio"]["clip_runs"] else "anull"
        C.ffmpeg("-i", src, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-af", af, "-c:a", "pcm_s24le", raw)
        before = span_measure(raw, t["in"], t["out"])
        enh = tmp / "s3_enh.wav"
        dst = out / f"{t['name']}{NAME_SUFFIX}.wav"
        lim = 10 ** ((tp - 0.2) / 20)
        atten = cfg.get("enhance_atten_lim_db")
        for atten in (atten, atten + EXTRA_ATTEN):     # a noisier recording gets one second pass with a bit more taken off
            y, sr = E.deepfilternet3(raw, atten)
            sf.write(enh, y, sr, subtype="PCM_24")
            gain = target - span_measure(enh, t["in"], t["out"])["lufs"]
            for _ in range(3):  # the limiter eats a little loudness: measure and top up; 4x oversampled so it catches true peaks
                C.ffmpeg("-i", enh, "-af", f"volume={gain:.2f}dB,aresample={SR * 4},alimiter=limit={lim:.4f}:level=disabled:attack=3:release=60,"
                         f"aresample={SR}", "-ar", str(SR), "-c:a", "pcm_s24le", dst)
                after = span_measure(dst, t["in"], t["out"])
                if abs(after["lufs"] - target) <= 0.3:
                    break
                gain += target - after["lufs"]
            floor = gap_floor(dst, t["speech"])
            if floor is None or floor <= CHECK["floor_max_db"]:
                break
        whole = E.measure(dst)
        z, _ = sf.read(str(dst), dtype="float32")
        clipped = int((np.abs(z) >= 0.999).sum())
        len_diff = round((len(z) - sf.info(str(raw)).frames) / SR, 3)
        w0, w1 = max(0.0, t["first_word"] - 2.5), min(pr["duration"], t["last_word"] + 1.0)
        re_al = fa.words(load_audio(dst, w0, w1), t["script"], w0)
        score_after = float(np.mean([w["score"] for w in re_al]))
        # timing is judged on words that were solid before and sit among solid neighbours: next to a word the member
        # skipped or said differently the aligner can settle either way, before and after denoising
        ws = t["words"]
        stable = [i for i, b in enumerate(ws) if b["score"] >= CHECK["solid"] and all(x["score"] >= 0.35 for x in ws[max(0, i - 2): i + 3])]
        shift = max([abs(re_al[i]["t0"] - ws[i]["t0"]) for i in stable] or [0.0])
        eaten = [b["w"] for a, b in zip(re_al, t["words"]) if b["score"] > CHECK["collapse"][0] and a["score"] < CHECK["collapse"][1]]
        r = {"name": t["name"], "file": t["file"], "declip": af == "adeclip", "atten_db": atten, "gain_db": round(gain, 1),
             "before": before, "after": after, "true_peak_db": whole["true_peak_db"], "clipped_samples": clipped,
             "length_diff_s": len_diff, "score_before": t["mean_score"], "score_after": round(score_after, 3),
             "word_shift_max_s": round(shift, 3), "eaten": eaten,
             "gap_floor_db": floor, "gap_floor_before_same_level_db": gap_floor(raw, t["speech"], gain),
             "seconds": round(time.time() - t_start, 1)}
        fails = []
        if abs(after["lufs"] - target) > CHECK["lufs_tol"]:
            fails.append(f"响度 {after['lufs']}")
        if whole["true_peak_db"] is not None and whole["true_peak_db"] > tp:
            fails.append(f"真峰值 {whole['true_peak_db']}")
        if floor is not None and floor > CHECK["floor_max_db"]:
            fails.append(f"底噪 {floor}")
        if floor is not None and after["speech_db"] - floor < CHECK["speech_over_floor_db"]:
            fails.append(f"人声只高出底噪 {after['speech_db'] - floor:.1f} dB")
        if clipped:
            fails.append(f"削波 {clipped} 个采样")
        if abs(len_diff) > CHECK["len_tol_s"]:
            fails.append(f"时长差 {len_diff} 秒")
        if shift > CHECK["word_shift_max_s"]:
            fails.append(f"词的时间挪了 {shift:.2f} 秒")
        r["fails"] = fails
        r["notes"] = (["对齐模型对这几个词没把握了（时间没变，要看一眼）：" + "、".join(eaten)] if eaten else []) +                      ([f"有词的时间挪了 {shift:.2f} 秒（不到 {CHECK['word_shift_max_s']} 秒，字幕不受影响）"] if shift > CHECK["word_shift_note_s"] else [])
        rows.append(r)
        outputs.append(dst)
        print(f"  {t['name']:16} 压 {atten} {gain:+5.1f} dB  {after['lufs']:6.1f} LUFS  峰 {whole['true_peak_db']}  底噪 {r['gap_floor_before_same_level_db']}→{floor}"
              f"  词挪 {shift:.3f}  {'过' if not fails else '没过：' + '；'.join(fails)}")

    C.write_json(out / "results.json", {"person": ctx.person, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间",
                                        "target": {"lufs": target, "true_peak_db": tp}, "check": CHECK, "rows": rows})
    ok = sum(1 for r in rows if not r["fails"])
    L = [f"# {ctx.person} 的声音验收（第 3 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。{len(rows)} 条，过 {ok} 条。",
         f"处理：整条原声 → 有削波的先 adeclip → DeepFilterNet3（最多压 {cfg.get('enhance_atten_lim_db')} dB）→ 按说话那一段的响度定一个增益 → 真峰值限制。"
         "响度和人声只量说话那一段（第 2 步的剪点之间）；底噪量的是没人说话的地方（第一个词之前、最后一个词之后，按第 2 步的词时间），"
         f"底噪还超标的，再多压 {EXTRA_ATTEN} dB 重做一次。", "",
         f"标准：响度 {target}±{CHECK['lufs_tol']} LUFS；真峰值 ≤ {tp} dB；没人说话处的底噪 ≤ {CHECK['floor_max_db']} dB；人声高出底噪 ≥ {CHECK['speech_over_floor_db']} dB；"
         f"无削波；时长和解码后的原声差 ≤ {CHECK['len_tol_s']} 秒；稿子重新对到处理后的声音上，原来对得牢、前后两个词也对得牢的词（对齐分 ≥ {CHECK['solid']}）时间挪动 ≤ {CHECK['word_shift_max_s']} 秒。"
         "平均对齐分只作参考（降噪后对齐模型略不那么确定，词的时间不变）；某个词的对齐分塌下去的，写在备注里看一眼，不算没过。", "",
         "底噪的“前”是原声拉到同样响度时同一处的底噪，前后可以直接比。", "",
         "| 新名字 | 去削波 | 压 dB | 增益 dB | 响度 后 | 底噪 前→后 | 人声−底噪 后 | 真峰值 | 词最多挪 秒 | 平均对齐分 前→后 | 结果 | 备注 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a, f = r["after"], r["gap_floor_db"]
        over = "—" if f is None else f"{a['speech_db'] - f:.1f}"
        L.append(f"| {r['name']} | {'是' if r['declip'] else '—'} | {r['atten_db']} | {r['gain_db']:+.1f} | {a['lufs']} | {r['gap_floor_before_same_level_db']} → {f} | "
                 f"{over} | {r['true_peak_db']} | {r['word_shift_max_s']:.3f} | "
                 f"{r['score_before']:.3f} → {r['score_after']:.3f} | {'过' if not r['fails'] else '；'.join(r['fails'])} | {'；'.join(r['notes']) or '—'} |")
    L += ["", f"成品：`3_audio/<新名字>{NAME_SUFFIX}.wav`，48 kHz 24 位单声道，和原件一样长，时间点和原件一一对应（第 2 步的剪点直接能用）。", ""]
    C.write_text(out / "声音验收.md", "\n".join(L))
    return outputs + [out / "results.json", out / "声音验收.md"]
