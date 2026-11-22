# HKBU SCIE1007 coursework video: AI mascot insert v2. Tighten the picked takes for banter pace, then re-measure.
# Chatterbox at high exaggeration leaves long dramatic pauses (~2 words/s). Here: internal silences longer than
# MAX_GAP are cut down (trimming silence only; the voice itself is never sped up or slowed - project hard rule),
# and pitch excursions are widened (INTON, Praat PSOLA, duration unchanged).
# Word times for the event table come from Whisper on the FINAL audio. Runs in $CDK20_WORK/tts/cbx.
#   python finalize_takes.py [ids]
import json, os, sys
import numpy as np, soundfile as sf
from voice_metrics import measure
HERE = os.path.dirname(os.path.abspath(__file__))
LINES_FILE = os.environ.get("LINES", "lines.json")
V = os.environ.get("VOICE_OUT", os.environ.get("CDK20_WORK", "D:/cdk20_work") + "/mascots/voice_v2")
# env overrides (post-credits skit, 19 section 4.2: MAX_GAP=0.11 MAX_GAP_END=0.18 to fit 113.0 s without any speed change)
MAX_GAP = float(os.environ.get("MAX_GAP", "0.14"))          # s, longest pause kept inside a sentence
MAX_GAP_END = float(os.environ.get("MAX_GAP_END", "0.22"))  # s, pauses that were > 0.45 s (sentence ends) keep this much
# intonation boost: pitch excursions around the line's median are stretched by this factor (in semitones).
# Claude needs it most (edge-tts Emma already moved a lot but sounded hoarse).
INTON = {"Claude": 1.25, "GPT": 1.1, "ChatGPT": 1.1, "DeepSeek": 1.1, "Gemini": 1.15}


def squeeze(x, sr):
    hop = int(sr * 0.01)
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(x), hop)])
    on = db > db.max() - 38
    out, i, n = [], 0, len(on)
    while i < n:
        j = i
        while j < n and on[j] == on[i]: j += 1
        seg = x[i * hop: j * hop]
        dur = (j - i) * 0.01
        if not on[i] and i > 0 and j < n and dur > MAX_GAP:
            keep = MAX_GAP_END if dur > 0.45 else MAX_GAP
            k = int(keep * sr); h = k // 2
            fade = np.linspace(1, 0, min(h, 240))
            a, b = seg[:h].copy(), seg[-(k - h):].copy()
            a[-len(fade):] *= fade; b[:len(fade)] *= fade[::-1]
            seg = np.concatenate([a, b])
        out.append(seg)
        i = j
    return np.concatenate(out)


def intonate(y, sr, k):
    if abs(k - 1) < 1e-3:
        return y
    import parselmouth
    from parselmouth.praat import call
    snd = parselmouth.Sound(y, sr)
    f0 = snd.to_pitch(time_step=0.01, pitch_floor=90, pitch_ceiling=650).selected_array["frequency"]
    med = float(np.median(f0[f0 > 0]))
    man = call(snd, "To Manipulation", 0.01, 90, 650)
    pt = call(man, "Extract pitch tier")
    call(pt, "Formula", f"{med} * (self / {med}) ^ {k}")
    call([pt, man], "Replace pitch tier")
    return call(man, "Get resynthesis (overlap-add)").values.flatten()


def main():
    lines_path = LINES_FILE if os.path.isabs(LINES_FILE) else os.path.join(HERE, LINES_FILE)
    cfg = json.load(open(lines_path, encoding="utf-8"))
    pick = json.load(open(f"{V}/final/pick.json", encoding="utf-8"))
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    ff = f"{V}/final/final.json"
    fin = json.load(open(ff, encoding="utf-8")) if os.path.exists(ff) else {}
    for ln in cfg["lines"]:
        if only and ln["id"] not in only:
            continue
        x, sr = sf.read(pick[ln["id"]]["path"], always_2d=True)
        y = squeeze(x.mean(1), sr)
        k = ln.get("inton", INTON[ln["who"]])
        y = intonate(y, sr, k)
        y = y / max(1.0, np.abs(y).max() / 0.98)
        dst = f"{V}/final/{ln['id']}.wav"
        sf.write(dst, y, sr)
        m = measure(dst, ln["text"])
        fin[ln["id"]] = {"path": dst, "take": os.path.basename(pick[ln["id"]]["path"]), "inton": k, "metrics": m}
        print(ln["id"], f"{len(x) / sr:.2f}s -> {m['dur']:.2f}s", "wps", m.get("wps"), "wer", m.get("wer"), "rng", m["f0_range_st"], "hnr", m["hnr_db"], "|", m["asr"], flush=True)
    json.dump(fin, open(ff, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
