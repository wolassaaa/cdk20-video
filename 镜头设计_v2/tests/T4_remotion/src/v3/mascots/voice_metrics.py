# HKBU SCIE1007 coursework video: AI mascot insert v2. Objective voice checks (we cannot listen):
# pitch range / variation (semitones), speaking rate, energy variation, pauses, clipping, pitch breaks,
# and Whisper ASR (text match + word timings). Runs in D:/cdk20_work/tts/cbx.
#   python voice_metrics.py <out.json> <wav> [<wav> ...] [--text "expected text" | --lines]
import json, os, re, sys
import numpy as np, soundfile as sf, parselmouth

_asr = None


def asr():
    global _asr
    if _asr is None:
        import torch
        from transformers import pipeline
        _asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", torch_dtype=torch.float16, device="cuda:0")
    return _asr


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + words(n % 100))
    return words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + words(n % 1000))


def norm(s):
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s.lower())
    s = re.sub(r"\d+", lambda m: " " + words(int(m.group())) + " ", s)
    s = s.replace("-", " ").replace("a.i.", "ai")
    s = re.sub(r"[^a-z' ]", " ", s)
    return s.split()


def wer(ref, hyp):
    r, h = " ".join(norm(ref)).split(), " ".join(norm(hyp)).split()
    d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    if "".join(r) == "".join(h):   # "storytime" vs "story time"
        return 0.0
    return d[-1, -1] / max(1, len(r))


def measure(path, text=None, do_asr=True):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(1)
    clip = float(np.mean(np.abs(x) > 0.99))
    hop = int(sr * 0.01)
    fr = np.array([np.sqrt(np.mean(x[i:i + hop * 2] ** 2) + 1e-12) for i in range(0, len(x) - hop * 2, hop)])
    db = 20 * np.log10(fr + 1e-9)
    on = db > (db.max() - 35)
    idx = np.where(on)[0]
    s0, s1 = (idx[0], idx[-1]) if len(idx) else (0, len(db) - 1)
    span = (s1 - s0 + 1) * 0.01
    # pauses inside speech (>=150 ms)
    pauses, run = 0, 0
    for v in on[s0:s1 + 1]:
        run = run + 1 if not v else 0
        if run == 15: pauses += 1
    snd = parselmouth.Sound(x, sr)
    pt = snd.to_pitch(time_step=0.01, pitch_floor=90, pitch_ceiling=650)
    f0 = pt.selected_array["frequency"]
    v = f0[f0 > 0]
    st = 12 * np.log2(v / 100.0) if len(v) else np.array([0.0])
    # pitch breaks: adjacent voiced frames jumping > 7 semitones (octave errors / cracks)
    f0s = 12 * np.log2(np.where(f0 > 0, f0, np.nan) / 100.0)
    jumps = int(np.nansum(np.abs(np.diff(f0s)) > 7))
    voiced_db = db[on[: len(db)]]
    # clarity: harmonics-to-noise ratio over voiced frames (low HNR = breathy / hoarse)
    hn = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=90).values.flatten()
    hnr = float(np.mean(hn[hn > -100])) if np.any(hn > -100) else 0.0
    out = dict(file=os.path.basename(path), dur=round(len(x) / sr, 3), speech_s=round(span, 3), lead_s=round(s0 * 0.01, 3), tail_s=round(len(x) / sr - s1 * 0.01, 3),
               f0_mean_hz=round(float(np.mean(v)) if len(v) else 0, 1), f0_range_st=round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2),
               f0_sd_st=round(float(np.std(st)), 2), energy_sd_db=round(float(np.std(voiced_db)), 2), pauses=pauses, pitch_breaks=jumps, clip=round(clip, 5), hnr_db=round(hnr, 2))
    if text:
        out["words"] = len(text.split())
        out["wps"] = round(len(text.split()) / max(0.1, span), 2)
    if do_asr:
        import librosa
        x16 = librosa.resample(x.astype(np.float32), orig_sr=sr, target_sr=16000)
        r = asr()({"raw": x16, "sampling_rate": 16000}, return_timestamps="word", generate_kwargs={"language": "en"})
        out["asr"] = r["text"].strip()
        out["word_times"] = [[c["text"].strip(), round(c["timestamp"][0] or 0, 3), round(c["timestamp"][1] or 0, 3)] for c in r.get("chunks", [])]
        if text:
            out["wer"] = round(wer(text, out["asr"]), 3)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    dst = a.pop(0)
    text = None
    if "--text" in a:
        i = a.index("--text"); text = a[i + 1]; del a[i:i + 2]
    res = [measure(p, text) for p in a]
    json.dump(res, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in res:
        print({k: v for k, v in r.items() if k != "word_times"})
