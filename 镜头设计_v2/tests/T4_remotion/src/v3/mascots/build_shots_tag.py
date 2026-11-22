# HKBU SCIE1007 coursework video: post-credits AI skit. Builds data/shots_tag.json (program output, never hand-edited)
# from shots_design.json (the 19 section 4.5 shot table), data/timeline_tag.json (voice = time base), lines_tag.json and
# cards_tag.json. Every frame number in the skit comes from a spoken word found here BY TEXT (numbers normalised with
# voice_metrics.norm), so a re-voiced line only needs this script to be re-run. ShowTag.jsx only draws what this file says.
#   python build_shots_tag.py            (system python is enough: json + difflib)
import difflib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from voice_metrics import norm
except Exception:  # voice_metrics imports parselmouth; fall back to a copy of norm()
    ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

    def _w(n):
        if n < 20: return ONES[n]
        if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
        if n < 1000: return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + _w(n % 100))
        if n < 1000000: return _w(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + _w(n % 1000))
        return _w(n // 1000000) + " million" + ("" if n % 1000000 == 0 else " " + _w(n % 1000000))

    def norm(s):
        s = re.sub(r"(?<=\d),(?=\d{3})", "", s.lower())
        s = re.sub(r"(\d+)\.(\d+)", lambda m: " " + _w(int(m.group(1))) + " point " + " ".join(ONES[int(d)] for d in m.group(2)) + " ", s)
        s = re.sub(r"\d+", lambda m: " " + _w(int(m.group())) + " ", s)
        s = s.replace("-", " ").replace("a.i.", "ai").replace("ai's", "ais")
        s = re.sub(r"[^a-z' ]", " ", s)
        return s.split()

FPS = 60
TL = json.load(open(os.path.join(HERE, "data", "timeline_tag.json"), encoding="utf-8"))
LINES = {l["id"]: l for l in json.load(open(os.path.join(HERE, "lines_tag.json"), encoding="utf-8"))["lines"]}
CARDS = json.load(open(os.path.join(HERE, "cards_tag.json"), encoding="utf-8"))["cards"]
DESIGN = json.load(open(os.path.join(HERE, "shots_design.json"), encoding="utf-8"))
L = {l["id"]: l for l in TL["lines"]}
NF = int(round(TL["total"] * FPS))            # composition length; egg_mix.wav is cut to exactly NF / 60 s
fr = lambda t: int(round(t * FPS))
WHO_DIR = {"Claude": "claude", "ChatGPT": "gpt", "DeepSeek": "deepseek", "Gemini": "gemini"}
ORDER = {"Claude": 0, "ChatGPT": 1, "DeepSeek": 2, "Gemini": 3}


# ------------------------------------------------------------------ word times by text
def align(lid):
    """Text tokens of the line (from lines_tag.json) -> start time, via the Whisper words of the final take."""
    l = L[lid]
    text_tok = norm(LINES[lid]["text"])
    wt, wtime = [], []
    for w, s, e in l["words"]:
        for tk in norm(w):
            wt.append(tk); wtime.append(s)
    sm = difflib.SequenceMatcher(None, text_tok, wt, autojunk=False)
    t = [None] * len(text_tok)
    for a, b, n in sm.get_matching_blocks():
        for i in range(n):
            t[a + i] = wtime[b + i]
    # a few tokens Whisper spelt differently ("alpha folds" for "alphafold's", "rentos or tib") - match them leniently
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "replace":
            for i in range(a0, a1):
                if t[i] is None and b0 < b1:
                    t[i] = wtime[min(b1 - 1, b0 + round((i - a0) * (b1 - b0) / max(1, a1 - a0)))]
    t0 = l["start"] + 0.04
    end = l["start"] + l["dur"]
    if t[0] is None:
        t[0] = t0                      # the line is trimmed to its voice onset: its first word starts there
    for i in range(len(t)):            # interpolate any token still unmatched
        if t[i] is None:
            j = i
            while j < len(t) and t[j] is None: j += 1
            a = t[i - 1]; b = t[j] if j < len(t) else end - 0.15
            for k in range(i, j): t[k] = a + (b - a) * (k - i + 1) / (j - i + 1)
    return text_tok, t


AL = {lid: align(lid) for lid in L}


def wt(lid, word, nth=1):
    """Start time of the nth occurrence of `word` (may be several words, e.g. 'two hundred eleven') in line lid."""
    toks, times = AL[lid]
    key = norm(word)
    hits = [i for i in range(len(toks) - len(key) + 1) if toks[i:i + len(key)] == key]
    if len(hits) < nth:
        raise KeyError(f"{lid}: '{word}' #{nth} not found in {toks}")
    return times[hits[nth - 1]]


wf = lambda lid, word, nth=1: fr(wt(lid, word, nth))
lstart = lambda lid: fr(L[lid]["start"])
lend = lambda lid: fr(L[lid]["start"] + L[lid]["dur"])
last_word = lambda lid: fr(AL[lid][1][-1])


# ------------------------------------------------------------------ shots
KIND = {"half": "half", "bust": "bust", "split": "split", "wide3": "wide", "wide4": "wide", "dual": "dual", "black": "black", "empty": "empty"}
Z = {"half": [1.24, 1.31], "bust": [1.55, 1.60], "split": [1.48, 1.53], "dual": [1.00, 0.94]}
shots = []
for r in DESIGN:
    sid = r["id"]
    if sid == "S01":
        f0 = 0
    elif sid == "S13":
        f0 = lend("L05") - 27
    elif sid == "S79":
        f0 = lend("L32")
    else:
        f0 = wf(r["line"], r["word"], r["nth"] or 1) - r["lead_f"]
    s = {"id": sid, "line": r["line"], "f0": f0, "kind": KIND[r["kind"]], "who": r["who"], "side": r["side"], "art": r["art"],
         "card": r["card"], "enter": r["enter"], "n_wide": 4 if r["kind"] == "wide4" else 3 if r["kind"] == "wide3" else 0}
    if s["kind"] in Z: s["z"] = list(Z[s["kind"]])
    shots.append(s)
shots.sort(key=lambda s: s["f0"])
assert [s["id"] for s in shots] == [r["id"] for r in DESIGN], "shot order changed"
for i, s in enumerate(shots):
    s["f1"] = shots[i + 1]["f0"] if i + 1 < len(shots) else NF
S = {s["id"]: s for s in shots}

# zoom details from 4.3 / 4.5
S["S03"]["z"] = [0.80, 0.85]
for k in ("S41",): S[k]["z"] = [0.76, 0.72]
for k in ("S72", "S75", "S77"): S[k]["z"] = [0.72, 0.76]
S["S53"]["z"] = [0.94, 1.00]
S["S60"]["z"] = [0.94, 1.00]

# speaker of each shot = whoever owns the line being spoken at the shot's middle (for halo, dimming, mouths)
def speaking(f):
    out = []
    for l in TL["lines"]:
        if lstart(l["id"]) <= f < lend(l["id"]): out.append(l["who"])
    return out


# ------------------------------------------------------------------ entries, exits, pushes, shakes, acts
WHIP_OUT = {"S09": ("R", 5), "S13": ("L", 4), "S17": ("R", 5), "S25": ("R", 5), "S33": ("R", 5), "S38": ("R", 5), "S46": ("L", 5), "S67": ("L", 5)}
WHIP_IN = ["S10", "S14", "S18", "S24", "S26", "S29", "S34", "S36", "S39", "S47", "S56", "S61", "S65", "S68", "S70"]
PUSH = {"S10": ("L04", "Binding", 1, 0.08), "S14": ("L06", "Cute", 1, 0.04), "S18": ("L07", "Company", 1, 0.08), "S34": ("L13", "Company-reported", 1, 0.08),
        "S36": ("L14", "Fine", 1, 0.04), "S39": ("L15", "A", 1, 0.08), "S51": ("L19", "RSI", 1, 0.08), "S58": ("L22", "Focus", 1, 0.08)}
WHIP_TRAVEL = 4   # frames of travel inside the 8-frame whip-in; the last 4 frames are still (E10: still >= 4 frames before the word)
for sid, (d, n) in WHIP_OUT.items():
    S[sid]["whip_out"] = {"dir": d, "n": n}
for sid in WHIP_IN:
    s = S[sid]; prev = shots[shots.index(s) - 1]
    if "whip_out" in prev:
        d = prev["whip_out"]["dir"]
    else:
        pw = prev["who"] if isinstance(prev["who"], str) else None
        d = "R" if pw is None or ORDER[s["who"]] >= ORDER.get(pw, 0) else "L"
    s["whip_in"] = {"dir": d, "n": WHIP_TRAVEL}
for sid, (lid, w, n, amt) in PUSH.items():
    S[sid]["push"] = {"f": wf(lid, w, n), "amt": amt}

SHAKE = []   # {f, n, amp}
def shake(lid, w, n=1, frames=1, amp=6, nth=1):
    SHAKE.append({"f": wf(lid, w, nth), "n": frames, "amp": amp})
shake("L03", "venom"); shake("L07", "report"); shake("L08", "fish", amp=6); shake("L11", "Bold"); shake("L12", "Hey")
shake("L13", "Company-reported"); shake("L22", "Focus"); shake("L22", "real", frames=2, amp=8); shake("L32", "bye", frames=2, amp=8)
for p in PUSH.values():
    SHAKE.append({"f": wf(p[0], p[1], p[2]) + int(round(0.16 * FPS)), "n": 1, "amp": 6})   # 1 frame +-6 px at the end of a snap push

# per-shot art changes and small acting
ART_AT = []   # {shot, who, art, f}
def art_at(sid, who, art, f): ART_AT.append({"shot": sid, "who": who, "art": art, "f": f})
art_at("S03", "DeepSeek", "full_laugh", wf("L02", "bragging"))
art_at("S09", "Claude", "bust_wink", wf("L03", "bound"))
art_at("S17", "ChatGPT", "bust_wink", last_word("L06"))
art_at("S25", "Claude", "bust_wink", wf("L10", "Claude"))
art_at("S49", "Gemini", "bust_surprised", wf("L19", "Wait"))
art_at("S51", "Gemini", "bust_laugh", wf("L19", "RSI"))
art_at("S64", "Gemini", "bust_wink", wf("L24", "cute"))
art_at("S67", "ChatGPT", "bust_wink", last_word("L25"))
art_at("S74", "ChatGPT", "bust_wink", wf("L29", "decide") - 6)
art_at("S77", "DeepSeek", "full_wave", wf("L31", "Bye"))
art_at("S78", "Gemini", "full_wave", wf("L32", "bye"))
# S41: the three keep the previous shots' faces until "Excuse"
exc = wf("L16", "Excuse")
S["S41"]["art"] = {"Claude": "full_shy", "ChatGPT": "full_smug", "DeepSeek": "full_laugh", "Gemini": "full_smug"}
for w in ("Claude", "ChatGPT", "DeepSeek"): art_at("S41", w, "full_surprised", exc)

ACT = []   # {shot, who, type, f, d}
def act(sid, who, typ, f, d=30, **kw): ACT.append(dict(shot=sid, who=who, type=typ, f=f, d=d, **kw))
act("S11", "Claude", "sink", S["S11"]["f0"] + 4, 24)
act("S12", "Claude", "nod", S["S12"]["f0"], 40)                           # head down 30 px and back up
act("S19", "ChatGPT", "blink2", S["S19"]["f0"] + 6, 40)                    # double blink
act("S20", "ChatGPT", "sigh", wf("L08", "Quiet"), 40)                       # body drops, tilts 3 deg
act("S56", "ChatGPT", "tilt", S["S56"]["f0"], 1)                            # full_smug tilted 3 deg for the whole shot
act("S58", "Claude", "sigh", wf("L22", "Focus"), 36)
for k, w in enumerate(("Dinner", "Wait")):
    act("S77", "DeepSeek", "jump", wf("L31", w), 16)
act("S77", "DeepSeek", "run_left", wf("L31", "Bye"), 50)
act("S77", "Claude", "run_left", wf("L31", "Bye") + 8, 70)
act("S77", "ChatGPT", "run_left", wf("L31", "Bye") + 14, 70)
act("S78", "Gemini", "run_right", wf("L32", "bye"), 40)

# ------------------------------------------------------------------ big hit, flashes, particles, lights
FX = {
    "hit": {"f": wf("L09", "NOT"), "flash": 2, "lines": 14, "push": int(round(0.16 * FPS)), "shake": 3},
    "glint": [S["S11"]["f0"]],                                            # one white glint along the split diagonal
    "sparks": [  # light particles: {f, x, y, col, n}
        {"f": lend("L01"), "x": 960, "y": 540, "col": "#7fe6ff", "n": 46},
        {"f": exc, "x": 1500, "y": 330, "col": "#c9b8ff", "n": 36},
        {"f": wf("L19", "RSI"), "x": 960, "y": 380, "col": "#c9b8ff", "n": 30},
        {"f": wf("L20", "cure"), "x": 1400, "y": 380, "col": "#c9b8ff", "n": 40},
        {"f": wf("L24", "cute"), "x": 960, "y": 380, "col": "#ffd0f0", "n": 26},
    ],
    "sub_shake": {"f": wf("L01", "yet"), "n": 2},
    "light_up": {"f": S["S02"]["f0"], "sweep": 6, "boxes": 18},
    "dim": {"f0": S["S52"]["f0"], "f1": S["S56"]["f0"], "to": 0.35, "ramp": 10},
    "s79": {"f0": S["S79"]["f0"], "empty": 12, "off": [12 + 0, 12 + 15, 12 + 30], "text_in": 42, "text_hold": 48, "fade": 24,
            "text": "WORTH TESTING? · HKBU SCIE1007 · Group 3B"},
}

# ------------------------------------------------------------------ name tags, voice card, disclosure line
NT = json.load(open(os.path.join(HERE, "nametags_tag.json"), encoding="utf-8"))
TAGS = [
    {"who": "DeepSeek", "kind": "big", "f_in": wf("L02", "Behind"), "f_out": S["S03"]["f0"], "voice": True},
    {"who": "Claude", "kind": "small", "f_in": S["S03"]["f0"], "f_out": S["S04"]["f0"]},
    {"who": "ChatGPT", "kind": "small", "f_in": S["S03"]["f0"] + 6, "f_out": S["S04"]["f0"]},
    {"who": "Claude", "kind": "big", "f_in": wf("L03", "I'll"), "f_out": S["S05"]["f0"]},
    {"who": "ChatGPT", "kind": "big", "f_in": wf("L06", "Cute"), "f_out": S["S15"]["f0"]},
    {"who": "Gemini", "kind": "over", "f_in": exc, "f_out": S["S42"]["f0"]},
]
DISCLOSE = {"f_in": S["S02"]["f0"], "f_out": S["S02"]["f0"] + 240,
            "text": "Post-credits skit · fictional AI characters · synthetic voices · sources on each card"}

# ------------------------------------------------------------------ clones (order from lines_tag _clone_order)
ORDERC = json.load(open(os.path.join(HERE, "lines_tag.json"), encoding="utf-8"))["_clone_order"]
pops = [wf("L16", "won"), wf("L17", "raised"), wf("L19", "more"), wf("L19", "me"), wf("L20", "Recursive"), wf("L20", "Improvement")]
away_end, still_t = AL["L24"][1][norm("Okay, fine... got carried away.").__len__() - 1], wt("L24", "Still")
pause_f = fr((away_end + 0.25 + still_t) / 2) if still_t - away_end > 0.3 else fr(still_t) - 8
rets = sorted([wf("L24", "fine"), wf("L24", "Got"), wf("L24", "carried"), wf("L24", "away"), pause_f])
repops = [wf("L32", "Save"), wf("L32", "six"), wf("L32", "six") + 6, wf("L32", "seats"), wf("L32", "seats") + 6]
CLONES = []
for k in range(6):
    c = {"k": k + 1, "name": ORDERC[k], "tag": "tag_" + ORDERC[k].replace(" ", "-") + ".png", "on": [[pops[k], None]]}
    if k >= 1:   # clones 6..2 go back in, one per beat, Exp-1120 first
        c["on"][0][1] = rets[5 - k] if 5 - k < len(rets) else rets[-1]
        c["on"].append([repops[k - 1], None])
    CLONES.append(c)
CLONE_RUN = wf("L32", "bye")
CLONE_SWAY = [wf("L23", "release"), lend("L23")]
CLONE_TAGLIGHT = [S["S60"]["f0"] + 6 + 10 * i for i in range(6)]

# ------------------------------------------------------------------ cards
def split_stat(st):
    for sep in (" vs ", " → "):
        if sep in st:
            a, b = st.split(sep, 1)
            return [a, sep.strip() + " " + b]
    return [st]


def count_spec(txt):
    if re.fullmatch(r"\d{4}", txt): return None                      # a year pops as a fixed value
    m = re.fullmatch(r"(\D*)(\d+)(\D.*|)", txt)
    if m and "." not in txt and "~" not in txt and "+" not in txt: return {"pre": m.group(1), "n": int(m.group(2)), "post": m.group(3)}
    return None


HITS = {  # 4.4 landing words: rows (one per stat line), note, extras
    "0": {"rows": [("L03", "seventeen", 1)], "note": ("L04", "Binding", 1), "first": S["S05"]["f0"],
          "funnel": [("L03", "Sixty-four", 1), ("L03", "three hundred", 1), ("L03", "two hundred eleven", 1), ("L03", "seventeen", 1)]},
    "1": {"rows": [("L06", "fifty", 1)], "note": ("L07", "report", 1), "first": wf("L06", "mini")},
    "2": {"rows": [("L16", "2024", 1)], "note": ("L16", "makers", 1), "first": S["S42"]["f0"]},
    "3": {"rows": [("L17", "six", 1)], "note": ("L18", "patient", 1), "first": wf("L17", "Isomorphic")},
    "4": {"rows": [("L20", "cure", 1)], "note": ("L22", "real", 1), "first": wf("L20", "I'm"), "side_note": ("L21", "Forty-two", 1), "stamp": ("L22", "real", 1)},
    "5": {"rows": [("L26", "up", 1), ("L26", "down", 1)], "note": ("L27", "phase", 1), "first": S["S66"]["f0"]},
    "6": {"rows": [("L10", "coming", 1)], "note": None, "note_f": last_word("L10"), "first": wf("L10", "ads", 1),
          "desc_lines": [("L10", "Ads", 2), ("L10", "But", 1)]},
    "7": {"rows": [("L11", "tungsten", 1)], "note": ("L11", "office", 1), "first": S["S27"]["f0"]},
    "8": {"rows": [("L12", "zero", 1), ("L12", "zero", 2)], "note": ("L13", "Company", 1), "first": wf("L12", "human")},
    "9": {"rows": [("L14", "over", 1), ("L14", "about", 1)], "note": ("L15", "first", 1), "first": wf("L14", "Novo")},
}
CARDS_OUT = {}
for cid, h in HITS.items():
    c = CARDS[cid]
    rows = split_stat(c["stat"])
    assert len(rows) == len(h["rows"]), cid
    out = {"id": cid, "kicker": c["subtitle"], "title": c["title"], "desc": c["desc"], "note": c["note"], "src": c["src"], "first": h["first"],
           "rows": [{"text": t, "f": wf(*h["rows"][i]), "count": count_spec(t)} for i, t in enumerate(rows)],
           "note_f": wf(*h["note"]) if h.get("note") else h["note_f"], "joke": c.get("is_joke", False)}
    if "funnel" in h:
        segs = re.split(r"( · | → )", c["funnel"])
        out["funnel"] = [{"text": t, "f": wf(*h["funnel"][i // 2]) if i % 2 == 0 else None} for i, t in enumerate(segs)]
    if "side_note" in h: out["side_note"] = {"text": c["side_note"], "f": wf(*h["side_note"])}
    if "stamp" in h: out["stamp"] = {"text": c["stamp"], "f": wf(*h["stamp"])}
    if "desc_lines" in h:
        parts = re.split(r"(?<=\.) ", c["desc"])
        out["desc_lines"] = [{"text": t, "f": wf(*h["desc_lines"][i])} for i, t in enumerate(parts)]
    CARDS_OUT[cid] = out

b = CARDS["banner"]
bl = re.split(r"(?<=\.) ", b["stat"])
BANNER = {"kicker": b["title"], "src": b["src"],
          "lines": [[{"w": w, "f": wf("L28", w)} for w in bl[0].split()], [{"w": w, "f": wf("L29", w)} for w in bl[1].split()]],
          "f_in": S["S73"]["f0"], "f_out": S["S76"]["f0"], "fade": 8}
# the closing banner lands: line 1 fully on "search", line 2 fully on "decide" (each word on its own word)

# ------------------------------------------------------------------ subtitles: one clause at a time, verbatim from lines_tag
MAXC = 52
def chunks(text):
    parts = [p for p in re.split(r'(?<=[.!?:])\s+|(?<=[.!?:]")\s+|(?<=—)', text) if p and p.strip()]
    out = []
    for p in parts:
        p = p.strip()
        while len(p) > MAXC:
            cut = [m.end() for m in re.finditer(r", ", p) if 12 < m.end() < len(p) - 8]
            if cut:
                i = min(cut, key=lambda x: abs(x - len(p) / 2))
            else:
                sp = [m.start() for m in re.finditer(" ", p)]
                i = min(sp, key=lambda x: abs(x - len(p) / 2)) + 1
            out.append(p[:i].strip()); p = p[i:].strip()
        out.append(p)
    return out


SUBS = []
lids = [l["id"] for l in TL["lines"]]
for li, lid in enumerate(lids):
    ch = chunks(LINES[lid]["text"])
    assert re.sub(r"\s+", "", "".join(ch)) == re.sub(r"\s+", "", LINES[lid]["text"]), lid
    toks, times = AL[lid]
    pos = 0; starts = []
    for c in ch:
        n = len(norm(c)); starts.append(times[min(pos, len(times) - 1)]); pos += n
    nxt = lstart(lids[li + 1]) if li + 1 < len(lids) else NF
    for j, c in enumerate(ch):
        f0 = lstart(lid) if j == 0 else fr(starts[j] - 0.03)
        f1 = fr(starts[j + 1] - 0.03) if j + 1 < len(ch) else min(lend(lid) + 9, nxt - 6)
        SUBS.append({"who": LINES[lid]["who"], "text": c, "f0": f0, "f1": f1, "line": lid})

# ------------------------------------------------------------------ voice per line (mouth envelope, word onsets)
VOICE = []
for l in TL["lines"]:
    VOICE.append({"id": l["id"], "who": l["who"], "f0": lstart(l["id"]), "f1": lend(l["id"]), "env": l["env"],
                  "onsets": sorted(set(fr(t) for t in AL[l["id"]][1])), "expr": LINES[l["id"]]["expr"]})

out = {"_note": "HKBU SCIE1007 coursework video: post-credits skit, generated by build_shots_tag.py - do not edit",
       "fps": FPS, "frames": NF, "total": TL["total"], "shots": shots, "shake": SHAKE, "art_at": ART_AT, "act": ACT, "fx": FX,
       "tags": TAGS, "nametags": NT, "disclose": DISCLOSE, "clones": CLONES, "clone_run": CLONE_RUN, "clone_sway": CLONE_SWAY,
       "clone_taglight": CLONE_TAGLIGHT, "cards": CARDS_OUT, "banner": BANNER, "subs": SUBS, "voice": VOICE,
       "has_gemini": [s["id"] for s in shots if (s["who"] == "Gemini" or (isinstance(s["who"], list) and "Gemini" in s["who"]))]}
json.dump(out, open(os.path.join(HERE, "data", "shots_tag.json"), "w", encoding="utf-8"), ensure_ascii=False)

# ------------------------------------------------------------------ report
print("frames", NF, "total", TL["total"])
for s in shots:
    d = (s["f1"] - s["f0"]) / FPS
    print(f"{s['id']} {s['f0']:5d}-{s['f1']:5d} {d:5.2f}s {s['kind']:6s} {s['who'] if isinstance(s['who'], str) else '/'.join(s['who'] or [])}{'  >3s!' if d > 3.0 else ''}{'  <0!' if d <= 0 else ''}")
print("longest", max((s["f1"] - s["f0"]) / FPS for s in shots), "shortest", min((s["f1"] - s["f0"]) / FPS for s in shots))
