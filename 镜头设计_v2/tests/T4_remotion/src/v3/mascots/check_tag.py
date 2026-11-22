# HKBU SCIE1007 coursework video: post-credits skit self-check (19 section 4.8, E1-E10).
#   python check_tag.py data            -> data checks (E1 shot lengths, E3/E4 card timing, E7 text, E9, E10) as JSON
#   python check_tag.py frames <dir> [a-b] -> E2 luma / frozen frames on the rendered JPEG sequence
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SH = json.load(open(os.path.join(HERE, "data", "shots_tag.json"), encoding="utf-8"))
LINES = {l["id"]: l for l in json.load(open(os.path.join(HERE, "lines_tag.json"), encoding="utf-8"))["lines"]}
CARDS = json.load(open(os.path.join(HERE, "cards_tag.json"), encoding="utf-8"))["cards"]
shots = SH["shots"]


def shot_at(f):
    r = shots[0]
    for s in shots:
        if f >= s["f0"]: r = s
    return r


def first_shot(cid):
    for s in shots:
        if s["card"] is not None and str(s["card"]) == cid: return s


def card_op(cid, f):
    s = shot_at(f)
    if s["card"] is None or str(s["card"]) != cid: return 0.0, s["id"]
    c = SH["cards"][cid]
    op = 1.0
    if s["id"] == "S53" or first_shot(cid)["id"] == s["id"]:
        op = 0.0 if f < c["first"] else min(1.0, (f - c["first"]) / 8)
    if "whip_out" in s:
        op *= 1 - min(1, max(0, (f - (s["f1"] - s["whip_out"]["n"] - 3)) / 4))
    return op, s["id"]


def data_checks():
    out = {}
    durs = [((s["f1"] - s["f0"]) / 60, s["id"]) for s in shots]
    out["E1"] = {"shots": len(shots), "longest_s": round(max(durs)[0], 3), "longest": max(durs)[1], "shortest_s": round(min(durs)[0], 3), "over_3s": [i for d, i in durs if d > 3.0]}
    # E3/E4: each number / note lands on its word with the card fully on screen; numbers never final before the word
    e34 = []
    for cid, c in SH["cards"].items():
        ev = [("row" + str(i), r["f"]) for i, r in enumerate(c["rows"])] + [("note", c["note_f"])]
        if c.get("side_note"): ev.append(("side_note", c["side_note"]["f"]))
        if c.get("stamp"): ev.append(("stamp", c["stamp"]["f"]))
        if c.get("funnel"): ev += [("funnel", x["f"]) for x in c["funnel"] if x["f"] is not None]
        for name, f in ev:
            if cid == "4" and name == "row0":
                pass
            op, sid = card_op(cid, f)
            small = sid == "S53"
            e34.append({"card": cid, "what": name, "f": f, "shot": sid, "opacity": round(op, 3), "ok": op >= 0.999 and not small})
    out["E3_E4"] = e34
    out["E3_E4_fail"] = [x for x in e34 if not x["ok"]]
    # E7 text: subtitles rebuild every line verbatim; card fields equal cards_tag.json
    sub_ok = []
    for lid, l in LINES.items():
        joined = "".join(s["text"] for s in SH["subs"] if s["line"] == lid)
        sub_ok.append(re.sub(r"\s+", "", joined) == re.sub(r"\s+", "", l["text"]))
    card_ok = []
    for cid, c in SH["cards"].items():
        src = CARDS[cid]
        stat = "".join(r["text"] if i == 0 else (" " + r["text"]) for i, r in enumerate(c["rows"]))
        card_ok.append(all([c["title"] == src["title"], c["kicker"] == src["subtitle"], c["desc"] == src["desc"], c["note"] == src["note"], c["src"] == src["src"], stat == src["stat"],
                            ("".join(x["text"] for x in c["funnel"]) == src["funnel"]) if c.get("funnel") else True]))
    b = SH["banner"]
    banner_ok = " ".join(" ".join(x["w"] for x in ln) for ln in b["lines"]) == CARDS["banner"]["stat"] and b["src"] == CARDS["banner"]["src"]
    out["E7"] = {"subtitle_lines_ok": sum(sub_ok), "lines": len(sub_ok), "cards_ok": sum(card_ok), "cards": len(card_ok), "banner_ok": banner_ok}
    # E9 (11-23): skit + closing credits card (CREDITS_F frames) must stay within 119.5 s
    jsx = open(os.path.join(HERE, "ShowTag.jsx"), encoding="utf-8").read()
    cf = int(re.search(r"export const CREDITS_F = (\d+);", jsx).group(1))
    total = SH["frames"] + cf
    out["E9"] = {"frames": total, "skit_frames": SH["frames"], "credits_frames": cf, "seconds": round(total / 60, 3), "ok": total / 60 <= 119.5}
    # E6 sources (11-23): no per-card source line, no disclosure, no voice prompt; every card source is on the closing card
    block = jsx[jsx.index("const CREDIT_SOURCES"):jsx.index("const CreditsCard")]
    credits = " ".join(re.findall(r'"([^"]*)"', block))
    def toks(t):
        t = t.replace("Joke card (satire); roadshow ref:", "")
        return [w for w in re.findall(r"[A-Za-z][A-Za-z]{2,}|\d{4}", t) if w[0].isupper() or w.isdigit()]
    per = []
    seen = set()
    for cid, c in CARDS.items():
        if cid == "banner" or c["src"] in seen: continue
        seen.add(c["src"])
        tk = toks(c["src"]); hit = [w for w in tk if w in credits]
        per.append({"card": cid, "src": c["src"], "tokens": len(tk), "found": len(hit), "ok": len(hit) >= 0.8 * len(tk)})
    gem = "Gemini character design by ZipZipPipe. Reference images: genderswapai.com." in credits
    note = "Fictional AI characters. Synthetic voices (Chatterbox TTS). Not affiliated with or endorsed by DeepSeek, Anthropic, OpenAI or Google." in credits
    gone = {k: (k not in jsx) for k in ("Source: {", "VoiceCard", "<Disclosure", "<CloneTags", "<Ghost", "B.kicker")}
    sizes = [int(x) for x in re.findall(r"fontSize: (\d+)", jsx[jsx.index("const CreditsCard"):jsx.index("// ---------------------------------------------------------------- main")])]
    out["E6_sources"] = {"cards": per, "gemini_line": gem, "disclaimer": note, "removed": gone, "credit_font_min_px": min(sizes),
                         "ok": all(x["ok"] for x in per) and gem and note and all(gone.values()) and min(sizes) >= 30}
    # E10: each line's first word: the speaker is in the shot and has been still >= 4 frames (L01 excepted: black by script)
    e10 = []
    for v in SH["voice"]:
        if v["id"] == "L01": continue
        f = v["onsets"][0]
        s = shot_at(f)
        who = s["who"] if isinstance(s["who"], list) else [s["who"]]
        settle = s["f0"]
        if "whip_in" in s: settle = s["f0"] + s["whip_in"]["n"]
        if s["id"] == "S41": settle = s["f0"] + 8
        if s["id"] == "S03": settle = s["f0"] + 6 + 14
        if s["kind"] == "split": settle = s["f0"] + 11
        still = f - settle
        e10.append({"line": v["id"], "who": v["who"], "f": f, "shot": s["id"], "in_shot": v["who"] in who, "still_frames": still, "ok": v["who"] in who and still >= 4})
    out["E10"] = e10
    out["E10_fail"] = [x for x in e10 if not x["ok"]]
    return out


def frame_checks(d, rng=None):
    import numpy as np
    from PIL import Image
    files = sorted(f for f in os.listdir(d) if f.endswith(".jpeg") or f.endswith(".jpg"))
    def num(fn): return int(re.findall(r"(\d+)", fn)[-1])
    if rng:
        a, b = map(int, rng.split("-")); files = [x for x in files if a <= num(x) <= b]
    s01 = shots[1]["f0"]; s79 = [s for s in shots if s["id"] == "S79"][0]["f0"]
    dark, same, prev, lum = [], [], None, {}
    for fn in files:
        im = np.asarray(Image.open(os.path.join(d, fn)).convert("L").reduce(2), dtype=np.int16)
        f = num(fn); m = float(im.mean()); lum[f] = round(m, 1)
        if m < 20 and not (f < s01 or f >= s79): dark.append([f, round(m, 1)])
        if prev is not None and np.array_equal(prev, im) and not (f < s01 and m < 2): same.append(f)
        prev = im
    return {"frames": len(files), "dark_outside_S01_S79": dark, "identical_neighbours": same, "min_luma": min(lum.values()), "mean_luma": round(sum(lum.values()) / len(lum), 1)}


if __name__ == "__main__":
    if sys.argv[1] == "data":
        r = data_checks()
        print(json.dumps({k: v for k, v in r.items() if k not in ("E3_E4", "E10")}, ensure_ascii=False, indent=1))
        json.dump(r, open(os.path.join(HERE, "data", "check_tag_data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        print(json.dumps(frame_checks(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), indent=1))
