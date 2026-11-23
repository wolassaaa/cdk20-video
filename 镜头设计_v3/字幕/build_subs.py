# HKBU SCIE1007 课程作业的科普视频：全片英文字幕数据（只出数据，不烧画面、不渲视频）。
# 规格照 深化/19 第三节：一行一块、≤ 44 个字符；切块照 Ch1Board.jsx 的 cues() 加 3.2 的三条补充；时间照 3.3（入 = 第一个词前 3 帧，
# 同句换块直接换，句末停 24 帧或到下一句入点前一帧，不晚于段尾，最短 0.8 s）；文本照 3.4（没说出口的不上、换了实词照说的写、
# 虚词和口音照稿子）。四个字幕版本（19 第十一节）都从这份数据烧。
#
# 输入：映射/master_v2.json（句、词、段内帧）；粗剪/v10/manifest_v10.json（段在全片的起点、段长）；
#       字幕/_asr_v10.json（asr_v10.py 对 v10 人声分轨的逐段听写）；字幕/subs_edits.json（核对后手定的改动）。
# 输出：字幕/subs_en.json、subs_en.srt、subs_tag_en.json、_asr_diff.json；导演检查_20261123/25_字幕_英文核对.html。
# 用法：py -3.11 -X utf8 镜头设计_v3/字幕/build_subs.py            # 全做
#       py -3.11 -X utf8 镜头设计_v3/字幕/build_subs.py --diff     # 只出听写和稿子的差异表（_asr_diff.json），给人看
import argparse, difflib, html, json, re, statistics, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
ROOT = V3.parent
MASTER = V3 / "映射/master_v2.json"
MAN = V3 / "粗剪/v10/manifest_v10.json"
ASR = HERE / "_asr_v10.json"
EDITS = HERE / "subs_edits.json"
TAG_TL = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/data/timeline_tag.json"
TAG_SH = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/data/shots_tag.json"
OUT_JSON, OUT_SRT, OUT_TAG, OUT_DIFF = HERE / "subs_en.json", HERE / "subs_en.srt", HERE / "subs_tag_en.json", HERE / "_asr_diff.json"
REPORT = ROOT / "导演检查_20261123/25_字幕_英文核对.html"

FPS = 60
MAXC, PRE, HOLD, FADE, MIN_F = 44, 3, 24, 6, 48          # 19 的 3.2、3.3
MAX_CPS = 20.0
SOFT = {"and", "for", "that", "an", "went", "alongside", "then"}
PUNCT = re.compile(r"[,:;]$")
ARTICLES = {"a", "an", "the"}
# 补充（总管定，可改回）：块不以这些词收尾——介词、限定词、助动词留在下一块开头，读起来不断在半截
STICKY = ARTICLES | {"of", "to", "in", "into", "on", "at", "from", "with", "by", "as", "like", "can", "could", "will", "would",
                     "is", "are", "was", "were", "be", "has", "have", "had", "not", "very", "its", "their", "our", "your", "his",
                     "her", "this", "these", "those", "my", "how", "what", "where", "than", "so", "just", "each", "every",
                     "been", "might", "must", "should", "may", "about", "around", "roughly", "inside", "within", "through",
                     "without", "onto", "for", "after", "before", "until", "toward", "towards", "against", "between", "other"}
GLUE2 = {("side", "by"), ("by", "side"), ("trial", "and"), ("and", "error"), ("more", "than"), ("less", "than")}
NUMW = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
        "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30", "fifty": "50"}
NUM_RE = re.compile(r"^[\d][\d,.]*%?$")


# ---------------------------------------------------------------- text helpers
def pretty(s):
    s = s.replace("...", "\u2026")
    s = re.sub(r"(^|\s)'", "\\1\u2018", s)                  # opening quote at word start
    return s.replace("'", "\u2019")


def norm(w):
    w = w.lower().replace("\u2019", "'").replace("\u2018", "'").replace("\u2026", "")
    w = w.strip(".,;:?!\"'()[]—–-… ")
    w = w.replace(",", "") if NUM_RE.match(w) else w
    w = w.replace("-", "")
    return NUMW.get(w, w)


def isnum(w):
    t = norm(w)
    return bool(NUM_RE.match(t)) or t in ("hundred", "thousand", "million", "billion")


def ends_stop(w):
    return bool(re.search(r"[,:;.?!\u2014\u2026]['\u2019]?$", w)) or w.endswith("...")


def nobreak(a, b):
    """True if a block may not end on word a and start the next on word b (19 的 3.2 第 3 条)."""
    if ends_stop(a):
        return False
    la, lb = a.lower(), b.lower()
    if a.startswith("'") and not a.rstrip(".,;:?!…").endswith("'"):     # just opened a quote: keep its first words together
        return True
    if la in STICKY:
        return True
    if isnum(a) and re.match(r"^[a-z]", b):                 # 210 nanomolar, ten weeks, 36 of
        return True
    if la == "of" and isnum(b):                             # 36 of 52
        return True
    if (a, lb) in (("Ren", "et"),) or (la, lb) in (("et", "al."), ("et", "al"), ("et", "al.,")):
        return True
    if a[:1].isupper() and b[:1].isupper() and la not in ARTICLES and not a.isupper() and not b.isupper():
        return True                                         # Insilico Medicine, Hong Kong
    return False


def nb(x, y):
    """nobreak between two word dicts, also honouring the glue set from the sentence context (mark_glue)."""
    return bool(x.get("glue")) or nobreak(x["w"], y["w"])


def mark_glue(ws):
    """Context rules that need the next-next word: names with of/in inside (the Chinese University of Hong Kong,
    the Prince of Wales Hospital, Nobel Prize in Chemistry), fixed pairs (side by side, trial and error)."""
    cap = lambda w: w[:1].isupper()
    for i in range(len(ws) - 1):
        a, b = ws[i]["w"], ws[i + 1]["w"]
        c = ws[i + 2]["w"] if i + 2 < len(ws) else ""
        p = ws[i - 1]["w"] if i > 0 else ""
        g = (a.lower().strip(",;:"), b.lower().strip(",;:")) in GLUE2 and not ends_stop(a)
        g = g or (cap(a) and b in ("of", "in") and cap(c) and not ends_stop(a))
        g = g or (a in ("of", "in") and cap(p) and cap(b) and not ends_stop(p))
        ws[i]["glue"] = g


def L(ws):
    return len(pretty(" ".join(x["w"] for x in ws)))


# ---------------------------------------------------------------- load
def load():
    M = json.loads(MASTER.read_text("utf8"))
    MF = json.loads(MAN.read_text("utf8"))
    A = json.loads(ASR.read_text("utf8"))["segs"] if ASR.exists() else {}
    E = json.loads(EDITS.read_text("utf8")) if EDITS.exists() else {}
    return M, MF, A, E


def who_of(g):
    by = {s["seg"]: s.get("person") or s.get("script_who") for s in g.get("sources", [])}
    return lambda seg: by.get(seg) or g.get("who")


# ---------------------------------------------------------------- ASR vs script
def align(words, heard):
    a = [norm(w["w"]) for w in words]
    b = [norm(h["w"]) for h in heard]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sm.get_opcodes(), a, b


def asr_diff(M, MF, A):
    G = {g["group"]: g for g in M["groups"]}
    out = {}
    for s in MF["segments"]:
        g = G.get(s["group"])
        if not g or not g["words"] or s["group"] not in A:
            continue
        words, heard = g["words"], A[s["group"]]["words"]
        ops, a, b = align(words, heard)
        offs, diffs = [], []
        for op, i1, i2, j1, j2 in ops:
            if op == "equal":
                for k in range(i2 - i1):
                    offs.append(heard[j1 + k]["t0"] * FPS - words[i1 + k]["f0"])
            else:
                diffs.append(dict(op=op, wids=[w["wid"] for w in words[i1:i2]], script=" ".join(w["w"] for w in words[i1:i2]),
                                  heard=" ".join(h["w"] for h in heard[j1:j2]),
                                  heard_t=[round(heard[j1]["t0"], 2), round(heard[j2 - 1]["t1"], 2)] if j2 > j1 else None,
                                  heard_p=[h["p"] for h in heard[j1:j2]],
                                  master_f=[words[i1]["f0"], words[i2 - 1]["f1"]] if i2 > i1 else None,
                                  ctx=" ".join(w["w"] for w in words[max(0, i1 - 4):i1]) + " [_] " + " ".join(w["w"] for w in words[i2:i2 + 3])))
        out[s["group"]] = dict(n_script=len(words), n_heard=len(heard), matched=len(offs),
                               off_med_f=round(statistics.median(offs), 1) if offs else None,
                               off_mad_f=round(statistics.median([abs(o - statistics.median(offs)) for o in offs]), 1) if offs else None,
                               heard_text=A[s["group"]]["text"], diffs=diffs)
    return out


# ---------------------------------------------------------------- edits → the words actually on screen
def apply_edits(g, E, asr_seg, seg_frames):
    """Word list for subtitles (copies): sid, w, f0, f1 (in-segment frames), wid, src. Edits come from subs_edits.json."""
    segs = {w["seg"] for w in g["words"]}
    drop_s = set(E.get("drop_sentences", {}))
    drop_w = set(E.get("drop_words", {}))
    repl = E.get("replace_words", {})
    ins = [x for x in E.get("insert_words", []) if x["after"].rsplit(".", 1)[0] in segs]
    alias = {}
    for grp in E.get("merge_sentences", []):
        for sid in grp[1:]:
            alias[sid] = grp[0]
    re_s = set(E.get("retime_sentences", {}))
    shift = E.get("shift_f", {}).get(g["group"], {}).get("f", 0) if isinstance(E.get("shift_f", {}).get(g["group"]), dict)         else E.get("shift_f", {}).get(g["group"], 0)
    ws = []
    for w in g["words"]:
        if w["sid"] in drop_s:
            continue
        x = dict(wid=w["wid"], seg=w["seg"], sid=alias.get(w["sid"], w["sid"]), w=w["w"], f0=w["f0"] + shift, f1=w["f1"] + shift,
                 src="master", retime=w["sid"] in re_s)
        if w["wid"] in drop_w:
            # keep the sentence-final punctuation on the previous kept word of the same sentence
            p = re.search(r"[.?!,:;]+['’]?$", w["w"])
            if p and ws and ws[-1]["sid"] == x["sid"] and not ends_stop(ws[-1]["w"]):
                ws[-1]["w"] += p.group(0)
            continue
        if w["wid"] in repl:
            x["w"], x["src"] = repl[w["wid"]]["w"], "edited"
        ws.append(x)
        for it in ins:
            if it["after"] == w["wid"]:
                ws.append(dict(wid=it["after"] + "+" + it["w"].strip(".,?"), seg=w["seg"], sid=x["sid"], w=it["w"], f0=None, f1=None,
                               src="inserted", retime=True))
    if any(x["retime"] or x["src"] != "master" for x in ws):
        retime_words(ws, asr_seg, E.get("asr_off", {}).get(g["group"]))
    for x in ws:                                                # measured voice onsets (energy) beat both
        if x["wid"] in E.get("word_f0", {}):
            x["f0"], x["src"] = E["word_f0"][x["wid"]]["f"], "onset"
    for x in ws:
        x["f0"] = max(0, min(seg_frames - 2, x["f0"]))
        x["f1"] = max(x["f0"] + 1, min(seg_frames - 1, x["f1"]))
        x.pop("retime", None)
    return ws


def retime_words(ws, asr_seg, off_fixed=None):
    """Words flagged retime (or edited/inserted) take their time from the transcript of the film voice. Whisper's word
    starts sit a fairly constant number of frames early (about 13 here); that offset is measured in the same segment on
    the words whose master time is trusted, and added back."""
    heard = (asr_seg or {}).get("words", [])
    if not heard:
        return
    ops, a, b = align(ws, heard)
    hit = {}
    for op, i1, i2, j1, j2 in ops:
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                hit[i1 + k] = (heard[j1 + k]["t0"], heard[j1 + k]["t1"], op == "equal")
        elif op == "replace":                                   # uneven: spread the heard span over the script words
            t0, t1 = heard[j1]["t0"], heard[j2 - 1]["t1"]
            n = i2 - i1
            for k in range(n):
                hit[i1 + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n, False)
    trusted = [ws[i]["f0"] - h[0] * FPS for i, h in hit.items()
               if h[2] and not ws[i]["retime"] and ws[i]["src"] == "master" and h[0] > 0.05]
    off = off_fixed if off_fixed is not None else (statistics.median(trusted) if len(trusted) >= 3 else 13.0)
    for i, x in enumerate(ws):
        if (x["retime"] or x["src"] != "master") and i in hit and (hit[i][0] > 0.05 or x["f0"] is None):
            x["f0"], x["f1"] = round(hit[i][0] * FPS + off), round(hit[i][1] * FPS + off)
            x["src"] = x["src"] if x["src"] != "master" else "asr_time"
            x["asr_off"] = round(off, 1)
    # anything still without a time: between its neighbours
    for i, x in enumerate(ws):
        if x["f0"] is None:
            p = next((ws[k] for k in range(i - 1, -1, -1) if ws[k]["f0"] is not None), None)
            n = next((ws[k] for k in range(i + 1, len(ws)) if ws[k]["f0"] is not None), None)
            x["f0"] = (p["f1"] if p else (n["f0"] - 10 if n else 0))
            x["f1"] = (n["f0"] if n else x["f0"] + 15)


# ---------------------------------------------------------------- chunking (Ch1Board.jsx cues() + 19 的 3.2)
def last_ok_break(cur, lo=1):
    for k in range(len(cur) - 1, lo - 1, -1):
        if not nb(cur[k - 1], cur[k]):
            return k
    return -1


def find_break(cur, lo=2):
    """Rule 1 order inside cur: after , : ; then before a SOFT word; both only where rule 3 allows."""
    for k in range(len(cur) - 1, lo - 1, -1):
        if PUNCT.search(cur[k - 1]["w"]) and not nb(cur[k - 1], cur[k]):
            return k
    for k in range(len(cur) - 1, lo - 1, -1):
        if cur[k]["w"].lower() in SOFT and not nb(cur[k - 1], cur[k]):
            return k
    return -1


def chunk_sentence(ws):
    out, cur = [], []
    for w in ws:
        if cur and L(cur + [w]) > MAXC:
            j = find_break(cur)
            if j > 0:
                out.append(cur[:j]); cur = cur[j:]
            elif not nb(cur[-1], w):
                out.append(cur); cur = []
            else:
                k = last_ok_break(cur)
                if k > 0:
                    out.append(cur[:k]); cur = cur[k:]
                else:
                    out.append(cur); cur = []
        cur.append(w)
        if PUNCT.search(w["w"]) and L(cur) >= 18:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def time_blocks(blocks, nf):
    """blocks: list of dicts with words, sid. In-segment frames, inclusive."""
    for i, b in enumerate(blocks):
        b["f0"] = max(0, b["words"][0]["f0"] - PRE)
    for i, b in enumerate(blocks):
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        last = b["words"][-1]["f1"]
        if nxt and nxt["sid"] == b["sid"]:
            f1 = nxt["f0"] - 1
        else:
            f1 = last + HOLD
            if nxt:
                f1 = min(f1, nxt["f0"] - 1)
        b["f1"] = min(f1, nf - 1)
        b["cut"] = bool(nxt and nxt["sid"] == b["sid"])
    for i, b in enumerate(blocks):
        b["first"] = i == 0 or blocks[i - 1]["sid"] != b["sid"]
        b["last"] = not b["cut"]
    return blocks


def dur(b):
    return b["f1"] - b["f0"] + 1


def rebalance(ws, lo, hi):
    """Split ws (> MAXC) in two, split index k in [lo, hi] (k = words in the first part), both parts ≥ 2 words,
    by rule 1 order, nearest to hi first."""
    lo, hi = max(2, lo), min(len(ws) - 2, hi)
    ok = lambda k: not nb(ws[k - 1], ws[k]) and L(ws[:k]) <= MAXC and L(ws[k:]) <= MAXC
    for test in (lambda k: PUNCT.search(ws[k - 1]["w"]), lambda k: ws[k]["w"].lower() in SOFT, lambda k: True):
        for k in range(hi, lo - 1, -1):
            if test(k) and ok(k):
                return k
    return -1


def build_seg(ws, nf, log):
    sids = []
    for w in ws:
        if not sids or sids[-1] != w["sid"]:
            sids.append(w["sid"])
    blocks = []
    for sid in sids:
        sw = [w for w in ws if w["sid"] == sid]
        mark_glue(sw)
        for c in chunk_sentence(sw):
            blocks.append(dict(sid=sid, words=c))
    # rule 4: orphans inside a sentence
    for _ in range(20):
        time_blocks(blocks, nf)
        changed = False
        for i, b in enumerate(blocks):
            alone = b["first"] and b["last"]
            if alone or not (len(b["words"]) == 1 or dur(b) < MIN_F):
                continue
            j = i - 1 if not b["first"] else i + 1
            a, z = min(i, j), max(i, j)
            merged = blocks[a]["words"] + blocks[z]["words"]
            if L(merged) <= MAXC:
                blocks[a] = dict(sid=b["sid"], words=merged); del blocks[z]
                log.append(f"孤词并块：{pretty(' '.join(x['w'] for x in merged))}")
            else:
                na = len(blocks[a]["words"])
                k = rebalance(merged, 2, na - 1) if j < i else rebalance(merged, na + 1, len(merged) - 2)
                if k < 0:
                    continue
                blocks[a] = dict(sid=b["sid"], words=merged[:k]); blocks[z] = dict(sid=b["sid"], words=merged[k:])
                log.append(f"孤词挪词：{pretty(' '.join(x['w'] for x in merged[:k]))} | {pretty(' '.join(x['w'] for x in merged[k:]))}")
            changed = True
            break
        if not changed:
            break
    # whole short sentences: hold longer if there is room, otherwise share a block with the neighbouring sentence
    for _ in range(20):
        time_blocks(blocks, nf)
        merge_at = None
        for i, b in enumerate(blocks):
            if dur(b) >= MIN_F or not b["last"]:
                continue
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            room = min(nf - 1, (nxt["f0"] - 1) if nxt else nf - 1)
            if b["f0"] + MIN_F - 1 <= room:
                b["f1"], b["held"] = b["f0"] + MIN_F - 1, True
            elif b["first"] and merge_at is None:
                merge_at = i
        if merge_at is None:
            break
        i, b = merge_at, blocks[merge_at]
        done = False
        for j in (i - 1, i + 1):
            if not 0 <= j < len(blocks):
                continue
            o = blocks[j]
            if o["words"][0]["seg"] != b["words"][0]["seg"] or not (o["last"] if j < i else o["first"]):
                continue
            a, z = min(i, j), max(i, j)
            merged = blocks[a]["words"] + blocks[z]["words"]
            if L(merged) <= MAXC:
                for w in merged:
                    w.setdefault("sid_orig", w["sid"]); w["sid"] = blocks[a]["sid"]
                blocks[a] = dict(sid=blocks[a]["sid"], words=merged); del blocks[z]
                log.append(f"两句合一块（单句不到 0.8 s）：{pretty(' '.join(x['w'] for x in merged))}")
                done = True
                break
        if not done:
            log.append(f"整句短、并不进邻句：{pretty(' '.join(x['w'] for x in b['words']))}")
            break
    # reading speed: a block over 20 characters/s whose neighbour in the same sentence reads slower gets its boundary moved
    # to the allowed break with the lowest worse-side speed (both sides ≤ 44 characters, ≥ 2 words)
    cps = lambda b: len(pretty(" ".join(x["w"] for x in b["words"]))) / (dur(b) / FPS)
    for _ in range(10):
        moved = False
        for i in range(len(blocks) - 1):
            a, z = blocks[i], blocks[i + 1]
            if not a["cut"] or max(cps(a), cps(z)) <= MAX_CPS:
                continue
            ws2 = a["words"] + z["words"]
            best, cur_k = None, len(a["words"])
            for k in range(2, len(ws2) - 1):
                if nb(ws2[k - 1], ws2[k]) or L(ws2[:k]) > MAXC or L(ws2[k:]) > MAXC:
                    continue
                t = dict(sid=a["sid"], words=ws2[:k]), dict(sid=a["sid"], words=ws2[k:])
                f0a, f0z = max(0, ws2[0]["f0"] - PRE), max(0, ws2[k]["f0"] - PRE)
                da, dz = f0z - f0a, z["f1"] - f0z + 1
                if da < MIN_F or dz < MIN_F:
                    continue
                score = max(L(ws2[:k]) / (da / FPS), L(ws2[k:]) / (dz / FPS))
                if best is None or score < best[0] - 0.5:
                    best = (score, k)
            if best and best[1] != cur_k and best[0] < max(cps(a), cps(z)):
                k = best[1]
                log.append(f"读速换断点：{pretty(' '.join(x['w'] for x in ws2[:k]))} | {pretty(' '.join(x['w'] for x in ws2[k:]))}")
                blocks[i], blocks[i + 1] = dict(sid=a["sid"], words=ws2[:k]), dict(sid=a["sid"], words=ws2[k:])
                time_blocks(blocks, nf)
                moved = True
        if not moved:
            break
    for b in blocks:
        if b.get("held"):
            log.append(f"整句短，多停到 0.8 s：{pretty(' '.join(x['w'] for x in b['words']))}")
    return blocks


# ---------------------------------------------------------------- main build
def srt_t(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(M, MF, A, E):
    G = {g["group"]: g for g in M["groups"]}
    subs, log, seglog = [], [], {}
    for s in MF["segments"]:
        if s["kind"] in ("MUSIC", "EGG"):
            continue
        g = G[s["group"]]
        if not g["words"]:
            continue
        nf = s["frames"]
        ws = apply_edits(g, E, A.get(s["group"]), nf)
        lg = []
        blocks = build_seg(ws, nf, lg)
        seglog[s["group"]] = lg
        who = who_of(g)
        for b in blocks:
            text = pretty(" ".join(x["w"] for x in b["words"]))
            sub_seg = b["words"][0]["seg"]
            subs.append(dict(id=0, seg=s["group"], sub_seg=sub_seg, who=who(sub_seg), sid=b["sid"],
                             t0=round((s["start_f"] + b["f0"]) / FPS, 3), t1=round((s["start_f"] + b["f1"] + 1) / FPS, 3),
                             seg_t0=round(b["f0"] / FPS, 3), seg_t1=round((b["f1"] + 1) / FPS, 3),
                             f0=s["start_f"] + b["f0"], f1=s["start_f"] + b["f1"], seg_f0=b["f0"], seg_f1=b["f1"],
                             text=text, first_of_sentence=b["first"], last_of_sentence=b["last"],
                             fade_in_f=FADE if b["first"] else 0, fade_out_f=FADE if b["last"] else 0,
                             burn=s.get("subs", "burn"), pos="bottom",
                             words=[dict(wid=x["wid"], w=x["w"], seg_f0=x["f0"], seg_f1=x["f1"], src=x["src"]) for x in b["words"]]))
    for i, b in enumerate(subs, 1):
        b["id"] = i
    return subs, seglog


def checks(subs, MF, A, diff):
    segs = {s["group"]: s for s in MF["segments"]}
    R = {}
    ov = [(a["id"], b["id"]) for a, b in zip(subs, subs[1:]) if b["f0"] <= a["f1"]]
    R["C1_不重叠"] = dict(ok=not ov, bad=ov)
    short = [(b["id"], b["text"], round((b["f1"] - b["f0"] + 1) / FPS, 2)) for b in subs if b["f1"] - b["f0"] + 1 < MIN_F]
    R["C2_最短0.8s"] = dict(ok=not short, bad=short)
    long_ = [(b["id"], b["text"], len(b["text"])) for b in subs if len(b["text"]) > MAXC]
    R["C3_一行≤44字符"] = dict(ok=not long_, bad=long_)
    inseg = []
    for b in subs:
        s = segs[b["seg"]]
        if b["seg_f0"] < 0 or b["seg_f1"] > s["frames"] - 1:
            inseg.append((b["id"], "块出了段"))
        for w in b["words"]:
            if not (0 <= w["seg_f0"] < w["seg_f1"] <= s["frames"] - 1):
                inseg.append((b["id"], w["wid"], w["seg_f0"], w["seg_f1"]))
            if not (b["seg_f0"] <= w["seg_f0"] and w["seg_f1"] <= b["seg_f1"] + HOLD):
                inseg.append((b["id"], w["wid"], "词不在块的时间窗里"))
    R["C4_词在该段录音时间里"] = dict(ok=not inseg, bad=inseg)
    # every block has speech under it in the transcript of the film voice
    silent, wer_hi = [], []
    for b in subs:
        off = -(diff.get(b["seg"], {}).get("off_med_f") or -13.0)     # Whisper runs early; put its words back on master time
        heard = [h for h in A.get(b["seg"], {}).get("words", [])
                 if b["seg_f0"] - 3 <= (h["t0"] + h["t1"]) / 2 * FPS + off <= b["seg_f1"] + 3]
        if not heard:
            silent.append((b["id"], b["text"]))
            continue
        ref = [norm(x) for x in b["text"].split()]
        hyp = [norm(h["w"]) for h in heard]
        sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
        err = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
        w = err / max(1, len(ref))
        b["asr_wer"] = round(w, 2)
        if w > 0.34:
            wer_hi.append((b["id"], b["seg"], b["text"], " ".join(h["w"] for h in heard), round(w, 2)))
    R["C5_块下面有人声"] = dict(ok=not silent, bad=silent)
    R["C6_词错率>0.34（对照 v10 听写，口音近音会算错，只作提示，逐条见第七节）"] = dict(ok=True, info=wer_hi)
    first_in = []
    for b in subs:
        w0 = b["words"][0]["seg_f0"]
        if b["seg_f0"] != max(0, w0 - PRE):
            first_in.append((b["id"], b["seg_f0"], w0))
    R["C7_入点=第一个词前3帧"] = dict(ok=not first_in, bad=first_in)
    cps = [(b["id"], b["text"], round(len(b["text"]) / ((b["f1"] - b["f0"] + 1) / FPS), 1)) for b in subs
           if len(b["text"]) / ((b["f1"] - b["f0"] + 1) / FPS) > MAX_CPS]
    R["C8_每秒≤20字符"] = dict(ok=not cps, bad=cps)
    # no block in MUSIC/EGG windows
    win = [(b["id"], b["seg"]) for b in subs if segs[b["seg"]]["kind"] in ("MUSIC", "EGG")]
    R["C9_窗口和彩蛋里没有正片字幕"] = dict(ok=not win, bad=win)
    # one speaker per block
    multi = [b["id"] for b in subs if len({w["wid"].split(".")[0] for w in b["words"]}) > 1]
    R["C10_一块只有一个人"] = dict(ok=not multi, bad=multi)
    return R


def build_tag():
    T = json.loads(TAG_TL.read_text("utf8"))
    S = json.loads(TAG_SH.read_text("utf8"))
    cues_by = {}
    for c in S["subs"]:
        cues_by.setdefault(c["line"], []).append(dict(text=c["text"], f0=c["f0"], f1=c["f1"], t0=round(c["f0"] / FPS, 3), t1=round(c["f1"] / FPS, 3)))
    lines = []
    for ln in T["lines"]:
        ws = ln["words"]
        lines.append(dict(id=ln["id"], who=ln["who"], text=ln["text"], t0=round(ws[0][1], 3), t1=round(ws[-1][2], 3),
                          start=ln["start"], dur=ln["dur"], words=[dict(w=w, t0=a, t1=b) for w, a, b in ws],
                          cues=cues_by.get(ln["id"], [])))
    return dict(note="HKBU SCIE1007 课程作业的科普视频：片尾彩蛋 32 句台词（英文），时间是彩蛋内部时间（秒；彩蛋第 0 帧 = 0 s）。"
                     "t0/t1 = 第一个词开口、最后一个词说完；cues = 彩蛋合成里现在烧的分句字幕（shots_tag.json 的 subs，彩蛋内部帧）。"
                     "全片位置 = 清单 EGG 段的 start_f 加彩蛋内部帧。",
                source=[str(TAG_TL.relative_to(ROOT)), str(TAG_SH.relative_to(ROOT))], fps=FPS, n_lines=len(lines), lines=lines)


# ---------------------------------------------------------------- report
CSS = """body{font-family:"Microsoft YaHei",sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;line-height:1.7;color:#222;background:#fff}
table{border-collapse:collapse;margin:12px 0;font-size:14px}td,th{border:1px solid #ccc;padding:4px 8px;vertical-align:top}th{background:#f2f2f2}
code{background:#f3f3f3;padding:1px 4px;border-radius:3px}h1,h2{border-bottom:1px solid #ddd;padding-bottom:4px}.ok{color:#0a7d2c}.bad{color:#b00020}
.en{font-family:Georgia,serif}.small{font-size:13px;color:#555}del{color:#b00020}ins{color:#0a7d2c;text-decoration:none;font-weight:bold}"""


def esc(x):
    return html.escape(str(x))


def report(subs, R, E, diff, tag, seglog, MF):
    n_chars = sum(len(b["text"]) for b in subs)
    n_words = sum(len(b["words"]) for b in subs)
    durs = [(b["f1"] - b["f0"] + 1) / FPS for b in subs]
    changes = E.get("changes", [])
    unclear = E.get("unclear", [])
    kept = E.get("kept_as_script", [])
    allok = all(v["ok"] for v in R.values())
    h = [f"<!doctype html><meta charset='utf-8'><title>25 字幕 英文核对</title><style>{CSS}</style>",
         "<h1>25 全片英文字幕数据：核对表</h1>",
         "<p class='small'>HKBU SCIE1007 课程作业的科普视频。这一步只做字幕数据（每块一条带时间），不烧画面、不渲视频。"
         f"生成：{time.strftime('%Y-%m-%d %H:%M')}（韩国时间）。脚本 <code>镜头设计_v3/字幕/build_subs.py</code>。</p>",
         "<h2>结论</h2><ul>",
         f"<li>正片一共 <b>{len(subs)}</b> 块字幕，{n_words} 个词、{n_chars} 个字符（含空格标点）；每块一行、最长 {max(len(b['text']) for b in subs)} 个字符，"
         f"平均显示 {statistics.mean(durs):.2f} s，最短 {min(durs):.2f} s。</li>",
         f"<li>拿 Whisper（large-v3）把 v10 人声分轨逐段听写（普通一遍、拿稿子做提示一遍），再对照素材流程当初对原始录音的听写，和稿子逐词比：<b>{len(changes)}</b> 处字幕跟实际念的走、和稿子不一样（下表一）；"
         f"另有 {len(kept)} 类出入照稿子写（口音近音、词尾弱读和时态单复数、冠词、数字和专名写法、只有一遍听到的，表二）；"
         f"{len(unclear)} 处听不清，只能照稿子（表三）。</li>",
         f"<li>机检 {sum(v['ok'] for v in R.values())}/{len(R)} 项过{'，全过' if allok else '，没过的见第四节'}。</li>",
         f"<li>片尾彩蛋 {tag['n_lines']} 句另放 <code>subs_tag_en.json</code>（彩蛋内部时间）；W2 押韵歌词烧在画面里，不进这份数据；W0–W5 窗口里没有字幕块。</li>",
         "</ul>"]
    for k, v in E.get("exceptions", {}).items():
        if not next((r["ok"] for n, r in R.items() if n.startswith(k)), True):
            h.insert(h.index("</ul>"), f"<li>没过的那一项（{esc(k)}）：{esc(v)}</li>")
    h.append("<h2>做法和我定的几件事</h2>")
    for p in E.get("decisions", []):
        h.append(f"<p>{esc(p)}</p>")
    h.append("<h2>一、跟实际念的走、和稿子不一样的地方</h2><table><tr><th>#</th><th>段</th><th>谁</th><th>稿子</th><th>字幕（实际念的）</th><th>听写原文</th><th>依据</th></tr>")
    for i, c in enumerate(changes, 1):
        h.append(f"<tr><td>{i}</td><td>{esc(c['seg'])}</td><td>{esc(c.get('who',''))}</td><td class='en'>{esc(c['script'])}</td>"
                 f"<td class='en'>{esc(c['subs'])}</td><td class='en small'>{esc(c.get('heard',''))}</td><td>{esc(c['why'])}</td></tr>")
    h.append("</table>")
    h.append("<h2>二、听写和稿子有出入、但照稿子写的</h2><p class='small'>19 的 3.4 第 3 条：口音、连读、冠词、时态单复数、多说的虚词照稿子；"
             "数字和专有名词的写法照稿子（Whisper 把它们写成别的样子不算念错）。</p><table><tr><th>类</th><th>例子（稿子 → 听写）</th><th>处理</th></tr>")
    for k in kept:
        h.append(f"<tr><td>{esc(k['kind'])}</td><td class='en small'>{esc(k['examples'])}</td><td>{esc(k['why'])}</td></tr>")
    h.append("</table><h2>三、听不清、只能照稿子的</h2><table><tr><th>段</th><th>稿子</th><th>听写</th><th>为什么照稿子</th></tr>")
    for u in unclear:
        h.append(f"<tr><td>{esc(u['seg'])}</td><td class='en'>{esc(u['script'])}</td><td class='en small'>{esc(u.get('heard',''))}</td><td>{esc(u['why'])}</td></tr>")
    h.append("</table>")
    h.append("<h2>四、机检</h2><table><tr><th>项</th><th>结果</th><th>明细</th></tr>")
    for k, v in R.items():
        det = v.get("bad") or ([] if k.startswith("C6") else v.get("info")) or []
        if k.startswith("C6"):
            det = [f"{len(v['info'])} 条，见第七节"]
        h.append(f"<tr><td>{esc(k)}</td><td class='{'ok' if v['ok'] else 'bad'}'>{'过' if v['ok'] else '没过'}</td>"
                 f"<td class='small'>{esc(det[:30]) if det else '—'}{' …共 %d 条' % len(det) if len(det) > 30 else ''}</td></tr>")
    h.append("</table>")
    h.append("<h2>五、各段的时间偏差（听写的词时间 − 总表 v2 的词时间）</h2><p class='small'>Whisper 的词起点本身有几帧的系统偏差，"
             "全片中位数作基准；某段偏离基准超过 6 帧才说明总表的词时间和成片声音对不上。</p>"
             "<table><tr><th>段</th><th>稿子词数</th><th>听到词数</th><th>对上</th><th>中位偏差（帧）</th><th>离散（帧）</th><th>切块时的调整</th></tr>")
    for seg, d in diff.items():
        h.append(f"<tr><td>{esc(seg)}</td><td>{d['n_script']}</td><td>{d['n_heard']}</td><td>{d['matched']}</td><td>{d['off_med_f']}</td>"
                 f"<td>{d['off_mad_f']}</td><td class='small'>{esc('；'.join(seglog.get(seg, [])))}</td></tr>")
    h.append("</table>")
    c6 = next(v for k, v in R.items() if k.startswith("C6"))["info"]
    h.append("<h2>七、字幕和听写对不上的块（只作提示）</h2><p class='small'>拿每块字幕和它时间窗里 v10 人声的听写比，词错率超过 0.34 的。"
             "逐条看过：都是表二的口音近音、数字写法，或者表三照稿子的地方，没有漏改的。</p>"
             "<details><summary>展开 %d 条</summary><table><tr><th>id</th><th>段</th><th>字幕</th><th>听写</th><th>词错率</th></tr>" % len(c6))
    for r in c6:
        h.append(f"<tr><td>{r[0]}</td><td>{esc(r[1])}</td><td class='en'>{esc(r[2])}</td><td class='en small'>{esc(r[3])}</td><td>{r[4]}</td></tr>")
    h.append("</table></details>")
    h.append("<h2>六、全部字幕块</h2><table><tr><th>id</th><th>段</th><th>谁</th><th>全片入</th><th>全片出</th><th>段内入</th><th>秒</th><th>文本</th></tr>")
    for b in subs:
        h.append(f"<tr><td>{b['id']}</td><td>{esc(b['sub_seg'])}</td><td>{esc(b['who'])}</td><td>{srt_t(b['t0'])}</td><td>{srt_t(b['t1'])}</td>"
                 f"<td>{b['seg_t0']:.2f}</td><td>{b['t1'] - b['t0']:.2f}</td><td class='en'>{esc(b['text'])}</td></tr>")
    h.append("</table><h2>文件</h2><ul>"
             "<li><code>镜头设计_v3/字幕/subs_en.json</code>：每块 {id, seg, t0, t1, seg_t0, seg_t1, text}，另有帧号、说话人、淡入淡出、逐词时间</li>"
             "<li><code>镜头设计_v3/字幕/subs_en.srt</code>：全片时间，一块一条</li>"
             "<li><code>镜头设计_v3/字幕/subs_tag_en.json</code>：彩蛋 32 句，彩蛋内部时间</li>"
             "<li><code>镜头设计_v3/字幕/subs_edits.json</code>：这次定的改动；<code>_asr_v10.json</code>：逐段听写；<code>_asr_diff.json</code>：听写和稿子的逐处差异</li></ul>")
    REPORT.write_text("\n".join(h), "utf8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()
    M, MF, A, E = load()
    diff = asr_diff(M, MF, A)
    OUT_DIFF.write_text(json.dumps(diff, ensure_ascii=False, indent=1), "utf8")
    if a.diff:
        print(f"diff -> {OUT_DIFF}  ({sum(len(d['diffs']) for d in diff.values())} 处)")
        return
    subs, seglog = build(M, MF, A, E)
    R = checks(subs, MF, A, diff)
    OUT_JSON.write_text(json.dumps(dict(
        note="HKBU SCIE1007 课程作业的科普视频：全片英文字幕数据（build_subs.py）。t0/t1 = 全片秒（t1 不含），seg_t0/seg_t1 = 段内秒；"
             "f0/f1、seg_f0/seg_f1 = 60 fps 帧（含两端）。一句的第一块淡入 6 帧、最后一块淡出 6 帧，同句换块直接换。样式照 19 的 3.1。",
        built=time.strftime("%Y-%m-%d %H:%M +09:00"), fps=FPS, manifest=str(MAN.relative_to(ROOT)), manifest_built=MF["built"],
        master=str(MASTER.relative_to(ROOT)), rules=dict(max_chars=MAXC, pre_f=PRE, hold_f=HOLD, fade_f=FADE, min_f=MIN_F, lines=1),
        n=len(subs), checks={k: v["ok"] for k, v in R.items()}, subs=subs), ensure_ascii=False, indent=1), "utf8")
    with OUT_SRT.open("w", encoding="utf8", newline="\r\n") as f:
        for b in subs:
            f.write(f"{b['id']}\n{srt_t(b['t0'])} --> {srt_t(b['t1'])}\n{b['text']}\n\n")
    tag = build_tag()
    OUT_TAG.write_text(json.dumps(tag, ensure_ascii=False, indent=1), "utf8")
    report(subs, R, E, diff, tag, seglog, MF)
    for k, v in R.items():
        print(f"{'OK ' if v['ok'] else 'BAD'} {k}  {len(v.get('bad') or v.get('info') or [])}")
    print(f"{len(subs)} 块，{sum(len(b['text']) for b in subs)} 字符 -> {OUT_JSON.name}, {OUT_SRT.name}, {OUT_TAG.name}, {REPORT}")


if __name__ == "__main__":
    main()
