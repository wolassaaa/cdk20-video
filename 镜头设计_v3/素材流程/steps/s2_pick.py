"""HKBU SCIE1007 coursework video: step 2 选条、对稿 of the phone-footage pipeline.

The script is the text. Whatever a member actually said, subtitles and the mapping use the script's words; speech
recognition only helps find where each script word sits in time. For every take step 1 matched to a script line:
  1. forced alignment (torchaudio MMS_FA) of the script line itself onto the take's audio, a little wider than step 1's
     first/last word so a cut-off first word is found again; numbers are spelled out to align, shown as written
  2. per script word: start, end, alignment score, and what recognition heard at that moment (for reference only)
  3. per take: suggested in/out from the aligned first/last word, a script-text SRT, words that aligned weakly
  4. per line: takes ranked (score, then how close to the script length), the best one suggested, confirmed: false
Input:  1_ident/ident.json, 1_ident/words/, the originals (read only)
Output: 2_pick/align/<name>.json and .srt, 2_pick/picks.json, 2_pick/对稿.md
Times are seconds in the original file.
"""
import re
import time

import numpy as np

import common as C

PAD_BEFORE, PAD_AFTER = 2.5, 1.0        # s searched around step 1's first/last word
IN_LEAD, OUT_TAIL = 0.3, 0.45           # suggested cut: before the first word, after the last (handbook G7: 0.2–0.4, 0.3–0.6)
WEAK = 0.35                             # mean token probability under this: the word may be missing or said differently
SR = 16000

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say(n):
    """Number as spoken English words (up to millions)."""
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10]] + (say(n % 10) if n % 10 else [])
    if n < 1000:
        return [ONES[n // 100], "hundred"] + (say(n % 100) if n % 100 else [])
    for size, word in ((10 ** 6, "million"), (1000, "thousand")):
        if n >= size:
            return say(n // size) + [word] + (say(n % size) if n % size else [])


def spoken(tok):
    """One script token -> the words to align ([] for pure punctuation). Years like 2023 read as twenty twenty three."""
    t = tok.lower().replace("’", "'").replace("×", " times ")
    out = []
    for part in re.findall(r"[a-z']+|\d[\d,]*(?:\.\d+)?", t):
        if part[0].isdigit():
            num = part.replace(",", "")
            if "." in num:
                a, b = num.split(".")
                out += say(int(a)) + ["point"] + [ONES[int(d)] for d in b]
            elif len(num) == 4 and "," not in part and 1900 <= int(num) <= 2099:
                out += say(int(num[:2])) + (say(int(num[2:])) if int(num[2:]) else ["hundred"])
            else:
                out += say(int(num))
        else:
            w = part.strip("'")
            if w:
                out.append(w)
    return out


def inputs(ctx):
    d1 = ctx.out / C.STEP_DIRS[1]
    return [d1 / "ident.json"] + sorted((d1 / "words").glob("*.words.json"))


def params(ctx):
    return {"pad": [PAD_BEFORE, PAD_AFTER], "cut": [IN_LEAD, OUT_TAIL], "weak": WEAK, "version": 1}


def load_audio(path, t0, t1):
    import soundfile as sf
    wav = C.ENV / "tmp" / "align_in.wav"
    wav.parent.mkdir(exist_ok=True)
    C.ffmpeg("-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(SR),
             "-af", "highpass=f=70,dynaudnorm=f=150:g=15", "-c:a", "pcm_s16le", wav)
    y, _ = sf.read(str(wav), dtype="float32")
    return y


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(words, max_chars=42):
    """Script-text subtitles: break after . ? ! : ; or when a line would pass max_chars."""
    cues, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        if re.search(r"[.?!:;]$", w["w"]) or len(text) >= max_chars:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return "\n".join(f"{i}\n{srt_time(c[0]['t0'])} --> {srt_time(c[-1]['t1'])}\n{' '.join(x['w'] for x in c)}\n"
                     for i, c in enumerate(cues, 1))


def run(ctx, out):
    import torch
    import torchaudio
    ident = C.read_json(ctx.out / C.STEP_DIRS[1] / "ident.json")
    beats = {b["beat"]: b for b in ident["script_beats"]}
    durs = {f["file"]: f["duration"] for f in C.read_json(ctx.out / C.STEP_DIRS[0] / "probe.json")["files"]}
    wdir = ctx.out / C.STEP_DIRS[1] / "words"
    adir = out / "align"
    adir.mkdir(exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if dev == "cuda":
        C.wait_for_gpu(3000)
    else:
        torch.set_num_threads(C.CPU_THREADS)
    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model(with_star=False).to(dev).eval()
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
    outputs, takes = [], []
    for a in ident["assets"]:
        b = beats.get(a["beat"])
        if not b or a["cls"] not in ("cam", "vo"):
            continue
        src = ctx.src / a["file"]
        dur = durs[a["file"]]
        w0, w1 = max(0.0, a["t0"] - PAD_BEFORE), min(dur, a["t1"] + PAD_AFTER)
        y = load_audio(src, w0, w1)
        toks = b["text"].split()
        groups = [spoken(t) for t in toks]
        flat = [w for g in groups for w in g]
        with torch.inference_mode():
            em, _ = model(torch.from_numpy(y)[None].to(dev))
            spans = aligner(em[0], tokenizer(flat))
        sec = len(y) / SR / em.shape[1]
        heard = C.read_json(wdir / (a["file"] + ".words.json"))["words"]
        words, k = [], 0
        for tok, g in zip(toks, groups):
            if not g:                              # punctuation only: rides on the previous word
                if words:
                    words[-1]["w"] += " " + tok
                continue
            sp = [s for w in spans[k:k + len(g)] for s in w]
            k += len(g)
            t0, t1 = w0 + sp[0].start * sec, w0 + sp[-1].end * sec
            score = float(np.mean([s.score for s in sp]))
            near = [h["w"] for h in heard if h["t1"] > t0 - 0.05 and h["t0"] < t1 + 0.05]
            words.append({"w": tok, "t0": round(t0, 3), "t1": round(t1, 3), "score": round(score, 3), "heard": " ".join(near)})
        weak = [w for w in words if w["score"] < WEAK]
        first, last = words[0]["t0"], words[-1]["t1"]
        cut_in, cut_out = round(max(0.0, first - IN_LEAD), 2), round(min(dur, last + OUT_TAIL), 2)
        rec = {"name": a["name"], "file": a["file"], "beat": a["beat"], "class": a["cls"], "take": a["take"],
               "script": b["text"], "first_word": first, "last_word": last, "in": cut_in, "out": cut_out,
               "spoken_seconds": round(last - first, 2), "script_seconds": b["secs"], "step1_score": a["score"],
               "mean_score": round(float(np.mean([w["score"] for w in words])), 3),
               "weak_words": [w["w"] for w in weak], "words": words,
               "_note": "字以稿子为准；heard 只是语音识别在这个时间听到的，供参考，不进字幕。时间是原件里的秒。"}
        C.write_json(adir / f"{a['name']}.json", rec)
        C.write_text(adir / f"{a['name']}.srt", srt(words))
        outputs += [adir / f"{a['name']}.json", adir / f"{a['name']}.srt"]
        takes.append(rec)
        print(f"  {a['name']:16} {len(words):3d} 词  {first:6.2f}–{last:6.2f}  弱 {len(weak)}")

    # one suggested take per line
    picks = []
    for beat in sorted({t["beat"] for t in takes}):
        ts = sorted((t for t in takes if t["beat"] == beat),
                    key=lambda t: (-(t["step1_score"] or 0) - 100 * t["mean_score"], abs(t["spoken_seconds"] - t["script_seconds"])))
        picks.append({"beat": beat, "pick": ts[0]["name"], "others": [t["name"] for t in ts[1:]],
                      "in": ts[0]["in"], "out": ts[0]["out"], "confirmed": False})
    C.write_json(out / "picks.json", {"person": ctx.person, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间",
                                      "_note": "每段建议用哪一条和剪点（原件里的秒）。导演点头后 confirmed 改 true。", "picks": picks})

    L = [f"# {ctx.person} 的对稿（第 2 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。",
         "", "**稿子是什么，字幕和对照就是什么。** 这一步把剧本这一段的每个词对到录音里的时间上；组员念得和稿子不一样的地方不改字、不算错、不进补拍。"
         "\"弱\"是这个词对得不太牢（可能没念、念成别的、或被别的声音盖住），只影响这个词的时间准不准；剪片对字幕时看一眼就行。", "",
         "| 新名字 | 第一个词 | 最后一个词 | 建议剪点 | 念的时长 / 剧本 | 平均对齐分 | 弱的词 |", "|---|---|---|---|---|---|---|"]
    for t in takes:
        L.append(f"| {t['name']} | {t['first_word']:.2f} | {t['last_word']:.2f} | {t['in']:.2f}–{t['out']:.2f} | "
                 f"{t['spoken_seconds']:.1f} / {t['script_seconds']} | {t['mean_score']:.2f} | {'、'.join(t['weak_words']) or '—'} |")
    L += ["", "每条的逐词时间在 `align/<新名字>.json`（`heard` 一栏是识别听到的，只作参考），字幕草稿 `align/<新名字>.srt`（稿子原文，时间是原件里的秒）。",
          "每段建议的条和剪点在 `picks.json`，`confirmed` 等导演点头。", ""]
    C.write_text(out / "对稿.md", "\n".join(L))
    return outputs + [out / "picks.json", out / "对稿.md"]
