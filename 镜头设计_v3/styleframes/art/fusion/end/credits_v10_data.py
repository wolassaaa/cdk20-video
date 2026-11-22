"""HKBU SCIE1007 课程作业的科普视频：片尾 W5 滚动字幕的文字数据。

从 镜头设计_v3/深化/19_声音字幕片尾与整片收口.md 的 5.4 原样抽出全部上屏文字，写成
镜头设计_v2/tests/T4_remotion/src/v3/fusion/credits_v10.json（credits_v10.jsx 读它），再逐字核对一遍（19 的 5.6 W6）。

和 5.4 原文有意的不同（都是总管 11-23 交接单和两条补充定的）：
  1. {GEMINI_CREDIT} 填成导演 11-22 定的 Gemini 新形象出处行；
  2. AI 声明第三段先用稳妥版 "We checked the key facts and numbers …"（19 第八节第 4 条的默认）；
  3. 删掉 "Post-credits skit sources" 整节（导演 11-23：彩蛋的出处集中在彩蛋自己的收尾卡上，片尾不再重复）；
  4. 在 "Data, models and images" 后面加一节 "Logos and badges"（导演 11-23：正片里的 logo、徽标、数据库标识统一列到片尾，只列文字）。
组员名字在 json 里只留 {NAME_A}–{NAME_D}，渲染时由 comp_w5roll.py 在本机读名单、经命令行参数传进 Remotion。

    python credits_v10_data.py build     抽取并写 json
    python credits_v10_data.py check     W6：json 和 5.4 逐字比（只许上面两处不同）、没有 {…} 残留（名字占位除外）、没有 TBC、编号 1–27 连续、条数对
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("D:/。hkbu/molecular science")
DOC = ROOT / "镜头设计_v3/深化/19_声音字幕片尾与整片收口.md"
OUT = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/fusion/credits_v10.json"

GEMINI_CREDIT = "Gemini character design by ZipZipPipe. Reference images: genderswapai.com."
AI_OLD = "We checked every fact and number against the sources listed here."
AI_NEW = "We checked the key facts and numbers against the sources listed here."

DROP = {"Post-credits skit sources"}
LOGOS = {"head": "Logos and badges", "after": "Data, models and images", "items": [
    "\"AlphaFold DB v6 · predicted\" badge and the CDK20 model AF-Q8IZL9-F1: AlphaFold Protein Structure Database, EMBL-EBI and Google DeepMind, CC BY 4.0.",
    "UniProt Q8IZL9 (the CDK20 sequence): UniProt Knowledgebase, the UniProt Consortium, CC BY 4.0.",
    "AlphaFold name on the kit chip: AlphaFold, Google DeepMind (Jumper et al. 2021).",
    "PandaOmics and Chemistry42 names on the kit chips, and the Insilico Medicine plate: the platforms and company named in Ren et al. 2023.",
    "\"OUR RE-DOCKING (AutoDock Vina)\" tag: AutoDock Vina, Scripps Research, open source (Apache 2.0).",
    "GLOBOCAN 2022 label: International Agency for Research on Cancer (IARC), via Bray et al. 2024.",
    "Hong Kong Cancer Registry label: Hospital Authority, Hong Kong.",
    "Product, company and database names are shown only to name our sources. All trademarks belong to their owners.",
]}

# 每节的排法（19 的 5.3）：align 居中 / 左对齐；columns 两栏只给参考文献和彩蛋出处
LAYOUT = {
    "Main paper": dict(columns=1, align="left"),
    "References": dict(columns=2, align="left"),
    "Logos and badges": dict(columns=1, align="left"),
    "Data, models and images": dict(columns=1, align="left"),
    "Music": dict(columns=1, align="center"),
    "Made with": dict(columns=1, align="center"),
    "Use of generative AI": dict(columns=1, align="left"),
}


def section_text():
    t = DOC.read_text(encoding="utf-8")
    a = t.index("### 5.4 上屏文字")
    b = t.index("说明：", a)
    return t[a:b]


def parse(raw):
    """返回 (title 行列表, [(节名, [(类别, 文字)])])。类别：num（带编号 n）、bullet、para。"""
    title, secs, cur, in_code = [], [], None, False
    for line in raw.splitlines()[1:]:
        s = line.rstrip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            if s:
                title.append(s)
            continue
        m = re.match(r"^\*\*(.+?)\*\*", s)
        if m and not s.startswith("**片名块"):
            cur = (m.group(1), [])
            secs.append(cur)
            continue
        if not s or cur is None:
            continue
        m = re.match(r"^(\d+)\. (.*)$", s)
        if m:
            cur[1].append(("num", int(m.group(1)), m.group(2)))
        elif s.startswith("- "):
            cur[1].append(("bullet", None, s[2:]))
        else:
            cur[1].append(("para", None, s))
    return title, secs


def build():
    title, secs = parse(section_text())
    data = {"title": title, "sections": [], "ai": []}
    for head, items in secs:
        if head in DROP:
            continue
        if head == "Use of generative AI":
            data["ai"] = [x[2].replace(AI_OLD, AI_NEW) for x in items]
            continue
        lay = LAYOUT[head]
        sec = {"head": head, "columns": lay["columns"], "align": lay["align"], "numbered": items[0][0] == "num", "items": []}
        for kind, n, s in items:
            s = s.replace("{GEMINI_CREDIT}", GEMINI_CREDIT)
            if kind == "num":
                sec["items"].append({"n": n, "text": s})
            elif kind == "bullet":
                sec["items"].append({"bullet": True, "text": s})
            else:
                sec["items"].append({"text": s, "note": head == "Music" and s.startswith("Short excerpts")})
        data["sections"].append(sec)
        if head == LOGOS["after"]:
            data["sections"].append({"head": LOGOS["head"], "columns": 1, "align": "left", "numbered": False,
                                     "items": [{"bullet": True, "text": t} for t in LOGOS["items"]]})
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", OUT)


def check():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    title, secs = parse(section_text())
    bad = []
    if d["title"] != title:
        bad.append("title differs")
    want = []
    ai = []
    for head, items in secs:
        if head in DROP:
            continue
        for kind, n, s in items:
            s = s.replace("{GEMINI_CREDIT}", GEMINI_CREDIT).replace(AI_OLD, AI_NEW)
            (ai if head == "Use of generative AI" else want).append((head, n, s))
        if head == LOGOS["after"]:
            want += [(LOGOS["head"], None, t) for t in LOGOS["items"]]
    want += ai
    got = []
    for sec in d["sections"]:
        for it in sec["items"]:
            got.append((sec["head"], it.get("n"), it["text"]))
    got += [("Use of generative AI", None, s) for s in d["ai"]]
    if got != want:
        for g, w in zip(got, want):
            if g != w:
                bad.append(f"differs: {g[2][:60]!r} vs {w[2][:60]!r}")
        if len(got) != len(want):
            bad.append(f"count {len(got)} vs {len(want)}")
    flat = json.dumps(d, ensure_ascii=False)
    left = [x for x in re.findall(r"\{[^{}\"]*\}", flat) if x not in ("{NAME_A}", "{NAME_B}", "{NAME_C}", "{NAME_D}")]
    if left:
        bad.append("placeholders left: %s" % left)
    if "TBC" in flat or "[TEAM" in flat:
        bad.append("TBC/[TEAM left")
    nums = [it["n"] for s in d["sections"] for it in s["items"] if "n" in it]
    if nums != list(range(1, 19)):
        bad.append("numbering %s" % nums)
    counts = {s["head"]: len(s["items"]) for s in d["sections"]}
    exp = {"Main paper": 1, "References": 17, "Data, models and images": 6, "Logos and badges": len(LOGOS["items"]), "Music": 7, "Made with": 3}
    if counts != exp:
        bad.append("counts %s" % counts)
    if len(d["ai"]) != 4:
        bad.append("ai paragraphs %d" % len(d["ai"]))
    diffs = sum(GEMINI_CREDIT in x[2] for x in want) + sum(AI_NEW in x[2] for x in want) + 2   # + dropped skit section + added logos section
    print(json.dumps({"W6": "pass" if not bad else "fail", "problems": bad, "items": len(got), "numbered": len(nums), "intended_diffs": diffs}, ensure_ascii=False))
    return not bad


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    sys.exit(0 if check() else 1)
