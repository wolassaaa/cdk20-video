# HKBU SCIE1007 课程作业的科普视频
# Self-check script for H1: nametags_tag.json & shots_design.json

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\。hkbu\molecular science")
MD_PATH = ROOT / "镜头设计_v3/深化/19_声音字幕片尾与整片收口.md"
LINES_PATH = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/lines_tag.json"
NAMETAGS_PATH = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/nametags_tag.json"
SHOTS_PATH = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/shots_design.json"
TIMELINE_PATH = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/mascots/data/timeline_tag.json"

VALID_EXPRS = {
    "neutral", "blink", "talk_a", "talk_o", "wink", "laugh", "smug",
    "pout", "surprised", "shy", "sigh", "think", "wave", "prop",
}
VALID_PREFIXES = {"full", "bust"}


def clean_text(s: str) -> str:
    s = s.lower().replace("-", " ").replace("—", " ")
    s = re.sub(r"[^a-z0-9'\s]", " ", s)
    return " ".join(s.split())


def main() -> int:
    errors = []
    notes = []

    # 1. Check nametags_tag.json
    nametags = json.loads(NAMETAGS_PATH.read_text(encoding="utf-8"))
    expected_chars = ["DeepSeek", "Claude", "ChatGPT", "Gemini"]
    if set(nametags.keys()) != set(expected_chars):
        errors.append(f"nametags keys mismatch: {list(nametags.keys())}")
    for ch in expected_chars:
        entry = nametags.get(ch, {})
        if set(entry.keys()) != {"no", "name", "subtitle", "voice"}:
            errors.append(f"nametags[{ch}] keys mismatch: {list(entry.keys())}")
        for k, v in entry.items():
            if not isinstance(v, str) or not v.strip():
                errors.append(f"nametags[{ch}][{k}] is not a non-empty string")

    # Cross-check nametags verbatim against 19 section 4.2(3)
    md = MD_PATH.read_text(encoding="utf-8")
    m_nt = re.search(r"\*\*（三）名牌数据。\*\*.*?\n\| 角色 \|.*?\n\|---.*?\n(.*?)\n\n", md, re.S)
    if not m_nt:
        errors.append("Could not find 4.2(3) nametags table in 19")
    else:
        nt_rows = [r for r in m_nt.group(1).strip().splitlines() if r.startswith("|")]
        if len(nt_rows) != 4:
            errors.append(f"Expected 4 nametag rows in 19, got {len(nt_rows)}")
        for r in nt_rows:
            cols = [c.strip() for c in r.split("|")[1:-1]]
            ch, no, name, subtitle, voice = cols
            if nametags.get(ch) != {"no": no, "name": name, "subtitle": subtitle, "voice": voice}:
                errors.append(f"nametags[{ch}] differs from 19 table: {nametags.get(ch)} vs {(no, name, subtitle, voice)}")

    # 2. Check shots_design.json
    lines_data = json.loads(LINES_PATH.read_text(encoding="utf-8"))["lines"]
    lines_map = {l["id"]: l for l in lines_data}
    tl_data = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))["lines"]
    tl_map = {l["id"]: l for l in tl_data}

    shots = json.loads(SHOTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(shots, list) or len(shots) != 79:
        errors.append(f"Expected 79 shots, got {len(shots) if isinstance(shots, list) else type(shots)}")

    required_fields = {"id", "line", "word", "nth", "lead_f", "kind", "who", "side", "art", "enter", "card", "clones", "fx"}
    for idx, s in enumerate(shots, 1):
        expected_id = f"S{idx:02d}"
        if s.get("id") != expected_id:
            errors.append(f"Shot index {idx} has id={s.get('id')}, expected {expected_id}")
        missing = required_fields - set(s.keys())
        if missing:
            errors.append(f"{expected_id} missing fields: {missing}")

        lid = s.get("line")
        if lid not in lines_map:
            errors.append(f"{expected_id} line {lid!r} not found in lines_tag.json")
            continue

        line_txt = lines_map[lid]["text"]
        word = s.get("word")
        if word is not None:
            w_clean = clean_text(word)
            t_clean = clean_text(line_txt)
            pattern = r"(?<!\w)" + re.escape(w_clean) + r"(?!\w)"
            matches = re.findall(pattern, t_clean)
            if not matches:
                errors.append(f"{expected_id} word {word!r} (clean={w_clean!r}) not found in {lid} text {line_txt!r}")
            elif s.get("nth") and len(matches) < s["nth"]:
                errors.append(f"{expected_id} nth={s['nth']} exceeds occurrences ({len(matches)}) of {word!r} in {lid}")

            tl_words = " ".join(clean_text(w[0]) for w in tl_map[lid]["words"])
            if not re.search(pattern, tl_words):
                notes.append(f"{expected_id} ({lid}) word {word!r} in lines_tag.json but differs in current Whisper timeline_tag.json: {[w[0] for w in tl_map[lid]['words']]}")
        else:
            notes.append(f"{expected_id} ({lid}) has word=null (non-word anchor in 4.5: {s.get('fx', '').split('|')[0].strip()})")

        art = s.get("art")
        art_values = []
        if isinstance(art, str):
            art_values = [art]
        elif isinstance(art, dict):
            art_values = list(art.values())
        elif art is not None:
            errors.append(f"{expected_id} unexpected art type: {type(art)}")

        for av in art_values:
            if "_" not in av:
                errors.append(f"{expected_id} invalid art token {av!r}")
                continue
            prefix, expr = av.split("_", 1)
            if prefix not in VALID_PREFIXES or expr not in VALID_EXPRS:
                errors.append(f"{expected_id} invalid art {av!r} (prefix={prefix}, expr={expr})")

    m_st = re.search(r"### 4\.5 镜头表.*?\n\| 镜 \|.*?\n\|---.*?\n(.*?)\n\n按现在的时间线", md, re.S)
    if not m_st:
        errors.append("Could not find 4.5 shot table in 19")
    else:
        st_rows = [r for r in m_st.group(1).strip().splitlines() if r.startswith("|")]
        if len(st_rows) != len(shots):
            errors.append(f"Row count mismatch vs 19 4.5: {len(st_rows)} vs {len(shots)}")

    print("=== _check_H1.py ===")
    print(f"nametags_tag.json: {len(nametags)} characters verified verbatim against 19_声音字幕片尾与整片收口.md 4.2(3)")
    print(f"shots_design.json: {len(shots)} shots (S01..S{len(shots):02d}), all lines in lines_tag.json, all word/art checks ran")
    if notes:
        print(f"Notes ({len(notes)}):")
        for n in notes:
            print("  -", n)
    if errors:
        print(f"FAIL ({len(errors)} errors):")
        for e in errors:
            print("  !", e)
        return 1
    print("PASS: 0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
