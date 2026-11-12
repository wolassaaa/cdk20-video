"""HKBU SCIE1007 coursework video: step 1 of the phone-footage pipeline, work out what each file is.

1. Speech to text with word times (faster-whisper on the GPU). Quiet video soundtracks get a temporary
   gain first; that boosted audio is only for transcription.
2. Fuzzy-match the words against the script lines: one file may hold one beat, several beats, or the
   same beat read several times; a video may also be a silent extra. Every beat-reading found is one
   asset, named by 04_命名规则.md (<person>_<cam|vo|ext|unk>_<beat>_t<take>), with its in/out time
   inside the original, a 0-100 score and a word-by-word diff against the script.
3. Products in 1_ident/: words/<file>.words.json, ident.json, ident.md, reshoot.md, cuts.json
   (suggested in/out per asset, confirmed: false, never burnt into anything), names.json
   (new name -> original, no copies), thumbs/<name>_thumb.jpg, library.json (one row per asset for the
   model that manages the library). Also rewrites this person's rows of 素材对照表.csv / .md.
   review.json is written later by the reviewer (GLM), not by this step.
"""
import csv
import io
import re
import subprocess
import time
from pathlib import Path

from rapidfuzz import fuzz

import common as C

HEAD_RE = re.compile(r"^\*\*(\d-\d\d) · (\d\d:\d\d)[–-](\d\d:\d\d) · ([A-Z]) · (ON-CAM|VO|on camera)\*\*")
NUM = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
NUM.update(thirty="30", forty="40", fifty="50", sixty="60", seventy="70", eighty="80", ninety="90")
SAME = {"ok": "okay", "cannot": "can't"}
NEG = {"not", "no", "never", "didn't", "don't", "isn't", "wasn't", "can't", "cannot", "won't", "doesn't", "nobody", "none", "without"}
TABLE_CSV = C.HERE / "素材对照表.csv"
TABLE_MD = C.HERE / "素材对照表.md"
COLS = ["新名字", "原文件", "原件里的起止", "人", "类", "段号", "片中时间", "台词", "实际念的", "差别", "第几条",
        "真实时长/剧本时长", "匹配分", "状态", "谁定的", "备注"]
CN_NUM = {c: i for i, c in enumerate("零一二三四五六七八九十")}


def inputs(ctx):
    return ctx.videos + ctx.audios + [C.SCRIPT_MD, ctx.out / C.STEP_DIRS[0] / "probe.json"]


def params(ctx):
    return {"ident": {k: v for k, v in ctx.cfg["ident"].items() if not k.startswith("_")}, "version": 9}


# ---------- script ----------

def secs(mmss):
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def load_script():
    beats, cur = [], None
    for line in C.SCRIPT_MD.read_text(encoding="utf-8").splitlines():
        m = HEAD_RE.match(line)
        if m:
            cur = {"beat": m.group(1), "t0": m.group(2), "t1": m.group(3), "who": m.group(4),
                   "kind": "vo" if m.group(5) == "VO" else "cam", "text": ""}
            cur["secs"] = secs(cur["t1"]) - secs(cur["t0"])
            beats.append(cur)
        elif cur is not None and line.startswith(">"):
            cur["text"] = (cur["text"] + " " + re.sub(r"[*_`]", "", line[1:]).strip()).strip()
        elif line.startswith(("**", "#")):
            cur = None
    for b in beats:
        b["tok"] = tokens(b["text"])
    return [b for b in beats if b["tok"]]


def tokens(text):
    """Comparable words: lower case, no punctuation, 'CDK20' -> cdk 20, 'three' -> 3, '048' -> 48."""
    t = text.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    t = re.sub(r"[^a-z0-9']+", " ", t)
    t = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", t)
    out = []
    for w in t.split():
        w = w.strip("'")
        if not w:
            continue
        w = NUM.get(w, w)
        w = SAME.get(w, w)
        if len(w) > 5 and re.search(r"ours?$", w):      # tumour = tumor
            w = re.sub(r"our(s?)$", r"or\1", w)
        if w.isdigit():
            w = str(int(w))
        out.append(w)
    return out


def glossary(beats):
    """Hard words of this person's lines (names, codes), given to the recogniser as a hint."""
    seen = []
    for b in beats:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9-]*", b["text"]):
            if (re.search(r"[A-Z]", w[1:]) or re.search(r"\d", w) or (w[0].isupper() and len(w) > 9)) and w not in seen:
                seen.append(w)
    return seen


# ---------- speech to text ----------

def transcribe_all(ctx, out, probe, hint):
    from faster_whisper import WhisperModel
    cfg = ctx.cfg["ident"]
    wdir = out / "words"
    wdir.mkdir(exist_ok=True)
    tmp = C.ENV / "tmp"
    tmp.mkdir(exist_ok=True)
    C.wait_for_gpu(6000)
    model = WhisperModel(cfg["asr_model"], device=cfg["asr_device"], compute_type=cfg["asr_compute_type"],
                         cpu_threads=C.CPU_THREADS, download_root=str(C.ENV / "cache" / "whisper"))
    res = {}
    for p in ctx.videos + ctx.audios:
        pr = probe[p.name]
        a = pr["audio"]
        if a is None:
            res[p.name] = {"file": p.name, "words": [], "text": "", "gain_db": 0, "note": "no audio track"}
            continue
        gain = 0.0 if a["lufs"] is None else max(0.0, min(30.0, cfg["asr_boost_to_lufs"] - a["lufs"]))
        wav = tmp / "asr_in.wav"
        C.ffmpeg("-i", p, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                 "-af", f"highpass=f=70,volume={gain:.1f}dB,alimiter=limit=0.9", wav)
        segs, _ = model.transcribe(str(wav), language="en", beam_size=5, word_timestamps=True,
                                   condition_on_previous_text=False,
                                   vad_filter=True, vad_parameters={"min_silence_duration_ms": 500, "speech_pad_ms": 200},
                                   initial_prompt="Glossary: " + ", ".join(hint) + "." if hint else None)
        words, nsp = [], []
        for s in segs:
            nsp.append(round(s.no_speech_prob, 3))
            for w in s.words or []:
                words.append({"w": w.word.strip(), "t0": round(w.start, 3), "t1": round(w.end, 3), "p": round(w.probability, 3)})
        r = {"file": p.name, "gain_db": round(gain, 1), "no_speech_prob": nsp,
             "text": " ".join(w["w"] for w in words), "words": words}
        C.write_json(wdir / (p.name + ".words.json"), r)
        res[p.name] = r
        print(f"  {p.name[:16]:16} +{gain:4.1f} dB  {len(words):3d} 词  {r['text'][:70]}")
    del model
    return res


# ---------- matching ----------

def align(S, T):
    """Best place of script words S inside transcript words T (None = already used).
    Returns (cost, start, end, ops); ops are (kind, script_index, transcript_index)."""
    n, m = len(S), len(T)
    INF = 1e9
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    B = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0], B[i][0] = float(i), "del"
        for j in range(1, m + 1):
            t = T[j - 1]
            if t is None:
                sub = INF
            elif t == S[i - 1]:
                sub = 0.0
            else:
                sub = 0.5 if fuzz.ratio(t, S[i - 1]) >= 75 else 1.0
            c = [(D[i - 1][j - 1] + sub, "sub" if sub else "eq"), (D[i - 1][j] + 1, "del"),
                 (D[i][j - 1] + (1 if t is not None else INF), "ins")]
            D[i][j], B[i][j] = min(c, key=lambda x: x[0])
    j = min(range(m + 1), key=lambda k: D[n][k])
    cost, end, i, ops = D[n][j], j, n, []
    while i > 0:
        k = B[i][j]
        if k in ("eq", "sub"):
            ops.append((k, i - 1, j - 1)); i -= 1; j -= 1
        elif k == "del":
            ops.append(("del", i - 1, None)); i -= 1
        else:
            ops.append(("ins", None, j - 1)); j -= 1
    ops.reverse()
    while ops and ops[0][0] in ("ins",):
        ops.pop(0)
    used = [o[2] for o in ops if o[2] is not None]
    return cost, (min(used) if used else end), (max(used) + 1 if used else end), ops


def find_takes(words, beats, cfg):
    """Greedy: take the best-scoring beat placement, block those words, repeat."""
    tw = []           # comparable token -> index of the spoken word it came from
    for wi, w in enumerate(words):
        if re.match(r"^,\d{3}$", w["w"].strip(" .?!;:")) and tw and tw[-1][0].isdigit():     # "8" ",918" is one number
            tw[-1] = (tw[-1][0] + w["w"].strip()[1:4], tw[-1][1])
            continue
        for t in tokens(w["w"]):
            tw.append((t, wi))
    T = [t for t, _ in tw]
    found = []
    while True:
        best = None
        for b in beats:
            cost, s, e, ops = align(b["tok"], T)
            if e <= s:
                continue
            score = max(0.0, 100 * (1 - cost / len(b["tok"])))
            hit = sum(1 for o in ops if o[0] == "eq")
            if best is None or (score, hit) > (best["score"], best["hit"]):
                best = {"b": b, "score": score, "hit": hit, "s": s, "e": e, "ops": ops}
        if best is None or best["score"] < 100 * cfg["unsure_score"] or best["hit"] < 2:
            break
        b, ops = best["b"], best["ops"]
        diff = []
        for kind, si, ti in ops:
            if kind == "del":
                diff.append({"kind": "漏", "script": b["tok"][si]})
            elif kind == "ins":
                diff.append({"kind": "多", "said": T[ti]})
            elif kind == "sub":
                diff.append({"kind": "换", "script": b["tok"][si], "said": T[ti]})
        w0, w1 = tw[best["s"]][1], tw[best["e"] - 1][1]
        found.append({"beat": b["beat"], "script_kind": b["kind"], "who": b["who"], "score": round(best["score"], 1),
                      "t0": words[w0]["t0"], "t1": words[w1]["t1"], "said": " ".join(w["w"] for w in words[w0:w1 + 1]),
                      "diff": diff, "min_word_p": min(w["p"] for w in words[w0:w1 + 1])})
        for k in range(best["s"], best["e"]):
            T[k] = None
    left = [words[wi]["w"] for wi in sorted({wi for (t, wi), tt in zip(tw, T) if tt is not None})]
    return sorted(found, key=lambda f: f["t0"]), left


def diff_text(diff):
    part = []
    for d in diff:
        if d["kind"] == "漏":
            part.append(f"漏 {d['script']}")
        elif d["kind"] == "多":
            part.append(f"多 {d['said']}")
        else:
            part.append(f"{d['script']}→{d['said']}")
    return "；".join(part)


def key_diff(diff, hint_tok):
    """Differences that can change the meaning: numbers, negations, names and codes."""
    out = []
    for d in diff:
        for w in (d.get("script"), d.get("said")):
            if w and (w.isdigit() or w in NEG or w in hint_tok or w in NUM):
                out.append(d)
                break
    return out


def order_key(name, created):
    m = re.search(r"第([零一二三四五六七八九十]+)段", name)
    n = 0
    if m:
        s = m.group(1)
        n = (CN_NUM[s] if len(s) == 1 else 10 + CN_NUM[s[1]] if s[0] == "十" else CN_NUM[s[0]] * 10 + (CN_NUM[s[2]] if len(s) > 2 else 0))
    return (n, created or "", name)


# ---------- thumbnails ----------

def thumb(path, times, dst):
    from PIL import Image
    frames = []
    for t in times:
        raw = subprocess.run([C.FFMPEG, "-v", "error", "-nostdin", "-threads", str(C.CPU_THREADS), "-ss", f"{max(0, t):.3f}", "-i", str(path),
                              "-frames:v", "1", "-vf", "scale=480:-2," + C.SDR_VF, "-f", "image2pipe", "-c:v", "png", "-"],
                             capture_output=True).stdout
        if raw:
            frames.append(Image.open(io.BytesIO(raw)).convert("RGB"))
    if not frames:
        return False
    w, h = frames[0].size
    strip = Image.new("RGB", (w * len(frames) + 4 * (len(frames) - 1), h), "white")
    for i, f in enumerate(frames):
        strip.paste(f, (i * (w + 4), 0))
    strip.save(dst, quality=85)
    return True


# ---------- the table kept in git ----------

def update_table(person, rows):
    keep, old = [], {}
    if TABLE_CSV.exists():
        with open(TABLE_CSV, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("人") == person:
                    old[r["新名字"]] = r
                else:
                    keep.append(r)
    for r in rows:      # a verdict someone (GLM, the director) already gave stays, as long as the asset is the same
        o = old.get(r["新名字"])
        if o and o.get("谁定的") not in ("", "规则", None) and o.get("原文件") == r["原文件"] and o.get("原件里的起止") == r["原件里的起止"]:
            r["状态"], r["谁定的"], r["备注"] = o["状态"], o["谁定的"], o["备注"]
    allrows = sorted(keep + rows, key=lambda r: (r["人"], {"cam": 0, "vo": 1, "ext": 2, "unk": 3}.get(r["类"], 9), r["段号"], int(r["第几条"] or 0)))
    with open(TABLE_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(allrows)
    L = ["# 素材对照表", "", "HKBU SCIE1007 课程作业的科普视频。每条素材对到剧本的哪句台词。由流程第 1 步生成（`run.py <人的文件夹> --steps 1`），"
         "规则见 `04_命名规则.md`。给程序读的是同名的 `.csv`。这里不写组员的真名和学号。", "",
         "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
    for r in allrows:
        L.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in COLS) + " |")
    C.write_text(TABLE_MD, "\n".join(L) + "\n")


# ---------- main ----------

def run(ctx, out):
    cfg = ctx.cfg["ident"]
    P = ctx.person
    probe = {r["file"]: r for r in __import__("json").loads((ctx.out / C.STEP_DIRS[0] / "probe.json").read_text(encoding="utf-8"))["files"]}
    beats = load_script()
    mine = [b for b in beats if b["who"] == P]
    hint = glossary(mine)
    hint_tok = {t for h in hint for t in tokens(h)}
    tr = transcribe_all(ctx, out, probe, hint)

    files = sorted(ctx.videos, key=lambda p: order_key(p.name, probe[p.name]["created"])) + \
        sorted(ctx.audios, key=lambda p: order_key(p.name, probe[p.name]["created"]))
    assets, per_file, take_no, nx, nu = [], {}, {}, 0, 0
    for p in files:
        is_video = p in ctx.videos
        words = tr[p.name]["words"]
        dur = probe[p.name]["duration"]
        # this person's lines first; other people's lines only explain what is still unmatched
        found, left = find_takes(words, mine, cfg)
        if len(left) >= 4:
            other, _ = find_takes([w for w in words if not any(f["t0"] <= w["t0"] <= f["t1"] for f in found)],
                                  [b for b in beats if b["who"] != P], cfg)
            found = sorted(found + [f for f in other if f["score"] >= 100 * cfg["accept_score"]], key=lambda f: f["t0"])
            said = " ".join(f["said"] for f in found)
            left = [w for w in left if w not in said.split()]
        per_file[p.name] = {"takes": [], "left": " ".join(left), "text": tr[p.name]["text"]}
        if not found:
            quiet = probe[p.name]["audio"] is None or (probe[p.name]["audio"]["lufs"] or -99) < -40
            if is_video and (len(words) < 4 or quiet):
                nx += 1
                a = {"name": f"{P}_ext_x{nx:02d}_t1", "cls": "ext", "beat": f"x{nx:02d}", "take": 1, "score": None,
                     "note": "没人说话，当空镜" + (f"（转文字的模型在安静里编出了：{tr[p.name]['text']}）" if words else "")}
            else:
                nu += 1
                a = {"name": f"{P}_unk_u{nu:02d}_t1", "cls": "unk", "beat": f"u{nu:02d}", "take": 1, "score": None,
                     "note": "有人说话，但和剧本哪一段都对不上" if words else "录音里没转出字"}
            a.update(file=p.name, t0=0.0, t1=dur, said=tr[p.name]["text"], diff=[], in_=0.0, out=dur, script_kind=None, who=P)
            assets.append(a)
            per_file[p.name]["takes"].append(a["name"])
            continue
        for f in found:
            cls = "cam" if is_video else "vo"
            k = (cls, f["beat"])
            take_no[k] = take_no.get(k, 0) + 1
            notes = []
            if f["who"] != P:
                notes.append(f"这是剧本里 {f['who']} 的台词")
            if f["script_kind"] != cls:
                notes.append("剧本里这段是" + ("画外音，交的是视频" if cls == "cam" else "出镜，交的是录音"))
            if f["t0"] < 0.15:
                notes.append("一开头就在说话，前面没有气口，第一个词可能不全")
            if dur - f["t1"] < 0.15:
                notes.append("说到最后一刻，结尾没有气口")
            if f["score"] < 100 * cfg["accept_score"]:
                notes.append("只对上一部分，可能是没念完或念了别的")
            a = dict(f, name=f"{P}_{cls}_{f['beat']}_t{take_no[k]}", cls=cls, take=take_no[k], file=p.name,
                     in_=round(max(0.0, f["t0"] - cfg["cut_pad_in"]), 3), out=round(min(dur, f["t1"] + cfg["cut_pad_out"]), 3),
                     note="；".join(notes), key_diff=key_diff(f["diff"], hint_tok))
            assets.append(a)
            per_file[p.name]["takes"].append(a["name"])
        if left and len(left) >= 3:
            per_file[p.name]["note"] = "还有没对上的话：" + " ".join(left)

    # optional second opinion from the text model on the unsure ones (rules still decide)
    llm_note = "没开（config.json 的 ident.llm_assist 是 false）"
    if cfg.get("llm_assist"):
        import llm
        if not llm.ready():
            llm_note = "开了，但钥匙没填，跳过"
        else:
            n = 0
            for a in assets:
                if a["score"] is None or a["score"] < 85:
                    cand = "\n".join(f"{b['beat']}: {b['text']}" for b in mine)
                    try:
                        a["llm"] = llm.chat("A student read one line of a script aloud. Speech-to-text gave:\n"
                                            f"\"{a['said']}\"\nScript lines:\n{cand}\n"
                                            "Reply with JSON only: {\"beat\": \"<id or none>\", \"verdict\": \"ok|unsure|reject\", \"reason\": \"<one sentence>\"}")
                        n += 1
                    except (llm.KeysMissing, llm.LLMError) as e:
                        a["llm"] = "没问成：" + str(e)[:80]
            llm_note = f"开了，问了 {n} 条"

    bmap = {b["beat"]: b for b in beats}
    # thumbnails (video assets only): 2 frames each at the start, middle and end of the asset
    tdir = out / "thumbs"
    tdir.mkdir(exist_ok=True)
    for old in tdir.glob("*_thumb.jpg"):
        old.unlink()
    outputs = []
    for a in assets:
        if a["file"] in {p.name for p in ctx.videos}:
            t0, t1 = a["in_"], a["out"]
            mid = (t0 + t1) / 2
            ts = [t0, min(t0 + 0.5, mid), mid - 0.25, mid + 0.25, max(t1 - 0.5, mid), max(t1 - 0.08, 0)]
            dst = tdir / f"{a['name']}_thumb.jpg"
            if thumb(ctx.src / a["file"], ts, dst):
                a["thumb"] = f"thumbs/{dst.name}"
                outputs.append(dst)

    # rows
    rows, lib, cuts, names = [], [], [], {}
    for a in assets:
        b = bmap.get(a["beat"])
        pr = probe[a["file"]]
        real = round(a["t1"] - a["t0"], 2)
        problems = [w for w, _ in pr["issues"] if not w.startswith(("带 ", "HLG", "PQ"))]
        if a.get("key_diff"):
            problems.append("重点词有出入：" + diff_text(a["key_diff"]))
        status = "待看" if (a["score"] is not None and a["score"] >= 85 and a["who"] == P) else "存疑"
        rows.append({"新名字": a["name"], "原文件": a["file"], "原件里的起止": f"{a['t0']:.2f}–{a['t1']:.2f}", "人": P, "类": a["cls"],
                     "段号": a["beat"], "片中时间": f"{b['t0']}–{b['t1']}" if b else "", "台词": b["text"] if b else "",
                     "实际念的": a["said"], "差别": diff_text(a["diff"]), "第几条": a["take"],
                     "真实时长/剧本时长": f"{real:.1f}/{b['secs']}" if b else f"{real:.1f}/—",
                     "匹配分": "" if a["score"] is None else f"{a['score']:.0f}", "状态": status, "谁定的": "规则", "备注": a.get("note", "")})
        v = pr["video"]
        lib.append({"name": a["name"], "file": a["file"], "class": a["cls"], "beat": a["beat"], "take": a["take"],
                    "in_file": [a["t0"], a["t1"]], "duration": real, "script_seconds": b["secs"] if b else None,
                    "spec": ({"size": v["display"], "fps": v["fps_avg"], "transfer": v["transfer_kind"]} if v else {}) |
                            {"lufs": pr["audio"]["lufs"] if pr["audio"] else None},
                    "score": a["score"], "status": status, "problems": problems, "note": a.get("note", ""),
                    "said": a["said"], "thumb": a.get("thumb")})
        cuts.append({"name": a["name"], "file": a["file"], "in": a["in_"], "out": a["out"], "first_word": a["t0"], "last_word": a["t1"],
                     "file_duration": pr["duration"], "confirmed": False})
        names[a["name"] + "_raw" + Path(a["file"]).suffix] = {"file": a["file"], "in": a["t0"], "out": a["t1"]}

    # reshoot list
    got = {}
    for a in assets:
        if a["cls"] in ("cam", "vo") and a["who"] == P:
            got.setdefault(a["beat"], []).append(a)
    missing, wrong_kind, misread = [], [], []
    for b in mine:
        takes = got.get(b["beat"], [])
        right = [a for a in takes if a["cls"] == b["kind"]]
        if not takes:
            missing.append(b)
        elif not right:
            wrong_kind.append((b, takes))
        best = max(right or takes, key=lambda a: a["score"], default=None)
        if best and (best["score"] < 85 or all(a.get("key_diff") for a in (right or takes))):
            misread.append((b, best))

    C.write_json(out / "ident.json", {"person": P, "script_beats": [{k: b[k] for k in ("beat", "kind", "t0", "t1", "secs", "text")} for b in mine],
                                     "glossary_hint": hint, "llm_assist": llm_note, "files": per_file,
                                     "assets": [{k: v for k, v in a.items() if k != "min_word_p"} | {"min_word_p": a.get("min_word_p")} for a in assets],
                                     "missing": [b["beat"] for b in missing]})
    C.write_json(out / "cuts.json", {"person": P, "_note": "建议的入点、出点（秒，在原件里）。只是数据，不烧进任何片子；上片时才用。导演点头后把 confirmed 改成 true。", "cuts": cuts})
    C.write_json(out / "names.json", names)
    C.write_json(out / "library.json", {"person": P, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间", "assets": lib})
    update_table(P, rows)

    sh = lambda f: f if not f.endswith(".mp4") else f[:8] + "….mp4"
    R = [f"# {P} 的补拍清单（第 1 步）", "", f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间，规则自动出的，要人看过才算数。", "",
         "## 剧本里有、没交的段", ""]
    R += [f"- **{b['beat']}**（{'出镜' if b['kind'] == 'cam' else '画外音'}，{b['t0']}–{b['t1']}）：{b['text']}" for b in missing] or ["没有。"]
    R += ["", "## 交了，但形式不对的段", ""]
    R += [f"- **{b['beat']}** 剧本里是{'出镜' if b['kind'] == 'cam' else '画外音'}，交来的只有{'录音' if takes[0]['cls'] == 'vo' else '视频'}（{'、'.join(a['name'] for a in takes)}）" for b, takes in wrong_kind] or ["没有。"]
    R += ["", "## 念得和剧本有出入、要人判断的段", "", "规则：最好的一条匹配分不到 85，或者每一条都有重点词（数字、否定词、专名）对不上。转文字本身也会错，先听再定。", ""]
    R += [f"- **{b['beat']}** 最好的一条 {a['name']}（{a['score']:.0f} 分）：{diff_text(a['diff']) or '无差别'}\n  - 剧本：{b['text']}\n  - 念的：{a['said']}" for b, a in misread] or ["没有。"]
    C.write_text(out / "reshoot.md", "\n".join(R) + "\n")

    L = [f"# {P} 的素材：认片结果（第 1 步）", "", f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。"
         f"{len(ctx.videos)} 条视频、{len(ctx.audios)} 条录音，认出 {len(assets)} 条素材。剧本里 {P} 有 {sum(b['kind'] == 'cam' for b in mine)} 段出镜、"
         f"{sum(b['kind'] == 'vo' for b in mine)} 段画外音。转文字用 faster-whisper {cfg['asr_model']}；文字模型帮忙：{llm_note}。", "",
         "匹配分：剧本这一段的词，念对了百分之多少（漏一个、多一个、换一个各扣一个词；拼写接近的扣半个）。85 以上算认准，60 到 85 要对着台词再看，60 以下存疑。", "",
         "## 文件 → 段号", "", "| 原文件 | 时长 秒 | 认出的素材（段号、原件里的起止、分） | 没对上的话 |", "|---|---|---|---|"]
    for p in files:
        mine_a = [a for a in assets if a["file"] == p.name]
        L.append(f"| {sh(p.name)} | {probe[p.name]['duration']:.1f} | " + "<br>".join(
            f"{a['name']}（{a['t0']:.1f}–{a['t1']:.1f}" + (f"，{a['score']:.0f} 分" if a["score"] is not None else "") + "）" for a in mine_a)
            + f" | {per_file[p.name]['left']} |")
    L += ["", "## 段号 → 有哪几条", "", "| 段号 | 形式 | 剧本时长 秒 | 素材 | 真实时长 秒 | 差 秒 | 匹配分 | 和剧本的差别 |", "|---|---|---|---|---|---|---|---|"]
    for b in mine:
        takes = got.get(b["beat"], [])
        if not takes:
            L.append(f"| {b['beat']} | {'出镜' if b['kind'] == 'cam' else '画外音'} | {b['secs']} | **没交** |  |  |  |  |")
        for a in takes:
            real = a["t1"] - a["t0"]
            L.append(f"| {b['beat']} | {'出镜' if b['kind'] == 'cam' else '画外音'} | {b['secs']} | {a['name']} | {real:.1f} | {real - b['secs']:+.1f} | {a['score']:.0f} | {diff_text(a['diff'])} |")
    extra = [a for a in assets if a["cls"] in ("ext", "unk") or a["who"] != P]
    if extra:
        L += ["", "## 剧本以外的和没认出的", ""] + [f"- {a['name']}（{sh(a['file'])}，{a['t1'] - a['t0']:.1f} 秒）：{a.get('note', '')}" for a in extra]
    tot_s = sum(b["secs"] for b in mine if b["beat"] in got)
    tot_r = sum(max(got[b["beat"]], key=lambda a: a["score"])["t1"] - max(got[b["beat"]], key=lambda a: a["score"])["t0"] for b in mine if b["beat"] in got)
    L += ["", f"交了的段，剧本估的时长合计 {tot_s} 秒，每段取分最高的一条实际合计 {tot_r:.1f} 秒（{tot_r - tot_s:+.1f} 秒）。真实时长是第一个词开始到最后一个词结束，不含前后的气口。", "",
          "补拍清单见 `reshoot.md`；建议剪点见 `cuts.json`；缩略图条在 `thumbs/`；给素材管理员的清单是 `library.json`；管理员看完把结论写到 `review.json`"
          "（格式见 `镜头设计_v3/素材流程/06_产物和接口.md`）。", ""]
    C.write_text(out / "ident.md", "\n".join(L))
    return outputs + [out / n for n in ("ident.json", "ident.md", "reshoot.md", "cuts.json", "names.json", "library.json")] + \
        sorted((out / "words").glob("*.words.json"))
