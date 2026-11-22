"""HKBU SCIE1007 课程作业的科普视频：B 档第 4 批事件表（B4_事件_定稿.py.txt）校验脚本。

检查内容（11 段：6-01/02/03/06/07/08/09、7-02/03/04、8-02）：
1. 语法与结构：能否解析成 11 个标准 PAGES dict 条目，id 唯一。
2. 动词白名单：只用范例 _b_events_example.py.txt 里出现过的动词（appear/move/grow/snap/eject/morph）。
3. 词锚点：每条 ev 的 at 词#n 和 until 的 w:词#n 在 _B4_words.txt 及 master_v1.json 对应段里真实存在第 n 次（小写、去两头标点）。
4. 帧顺序与越界：0 <= f_start <= f_land <= f_end <= len_f - 1；until 不早于 at。
5. 句内节奏：
   - 无事件覆盖空档 <= 90 帧（validate_events V4）；
   - 每句内相邻落点（含句首到首落点、末落点到句尾）间隔 <= 90 帧（每句至少每 90 帧有一件事落下）；
   - 每句末事件结束帧 >= 句尾 - 2 帧（validate_events V5）。
6. 视线引导（对照 resolve.guide_plan 与 check_guides.keys_checks）：
   - V1 到位重叠 <= 1、交接重叠 <= 2；
   - V2 相邻 gon >= 36、每句 <= 3、任意 10 秒 <= 5；
   - V3 变化中占比 <= 45%；
   - V4/V5t 时间窗；
   - V6 ramp：每段最后一个引导 goff - gend >= 12（不贴段尾截断）。
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP_DIR = HERE.parents[1] / "映射"
sys.path.insert(0, str(MAP_DIR))

import maplib as M  # noqa: E402
import resolve as RS  # noqa: E402

EXPECTED_SEGS = [
    "6-01", "6-02", "6-03", "6-06", "6-07", "6-08", "6-09",
    "7-02", "7-03", "7-04", "8-02",
]
ALLOWED_VERBS = {"appear", "move", "grow", "snap", "eject", "morph"}
GAP_LIMIT = 90
END_TOL = 2


def parse_b4_words(path: Path):
    """独立解析 _B4_words.txt，与 master_v1.json 交叉校验。"""
    segs = {}
    cur = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            m = re.match(r"^##\s+(\S+)\s+.*len_f=(\d+)", line)
            if not m:
                raise ValueError(f"无法解析段头: {line}")
            cur = m.group(1)
            segs[cur] = {"len_f": int(m.group(2)), "sentences": [], "words": []}
        elif line.startswith("S: "):
            segs[cur]["sentences"].append(json.loads(line[3:]))
        elif line.startswith("WORDS (word, start_f, end_f): "):
            body = line.split(": ", 1)[1].strip()
            counts = {}
            for tok in body.split():
                w, f0 = tok.rsplit("@", 1)
                n = M.norm(w)
                counts[n] = counts.get(n, 0) + 1
                segs[cur]["words"].append({
                    "w": w, "norm": n, "idx": counts[n],
                    "key": f"{n}#{counts[n]}", "f0": int(f0),
                })
    return segs


def load_b4_pages(path: Path):
    """把 B4_事件_定稿.py.txt 解析成 dict（支持直接贴进 PAGES = { ... } 的条目片段或完整 PAGES = {...}）。"""
    txt = path.read_text(encoding="utf-8").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n", "", txt)
        txt = re.sub(r"\n```$", "", txt.strip())
    ns = {}
    if re.search(r"^\s*PAGES\s*=", txt, re.M):
        code = txt
    else:
        code = "PAGES = {\n" + txt + "\n}\n"
    ast.parse(code)
    exec(compile(code, str(path), "exec"), {"dict": dict}, ns)
    return ns["PAGES"]


def build_doc(seg, P):
    evs = []
    for (i, verb, w, off, lead, u, means, g) in P["ev"]:
        e = {
            "id": i, "obj": i, "verb": verb,
            "at": {"word": w, "off": off}, "lead": lead,
            "means": means, "tool": "remotion",
            "guide": {"kind": "focus", "target": [g]} if g else {"kind": "none"},
        }
        if u is not None:
            if u == "s":
                e["until"] = {"sentence_end": True}
            else:
                k, v = u.split(":", 1)
                e["until"] = {"word": v} if k == "w" else {"dur": int(v)}
        evs.append(e)
    return {
        "schema": "cdk20.events/1", "group": seg, "tool": "remotion",
        "note": P["note"], "tier": "B", "zone": P["zone"],
        "trans_in": P["trans_in"], "trans_out": P["trans_out"],
        "holds": [], "events": evs,
    }


def longest_uncovered(a, b, ivs):
    cov = sorted((max(a, x), min(b, y)) for x, y in ivs if y >= a and x <= b)
    best, at, cur = 0, a, a
    for x, y in cov:
        if x > cur and x - cur > best:
            best, at = x - cur, cur
        cur = max(cur, y)
    if b - cur > best:
        best, at = b - cur, cur
    return best, at


def union_len(ivs):
    tot, cur = 0, None
    for a, b in sorted(ivs):
        if cur is None or a > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur:
        tot += cur[1] - cur[0]
    return tot


def check_word_in_txt(seg_txt, ref):
    if "#" not in ref:
        return False, f"缺少 #n: {ref!r}"
    base, n_str = ref.rsplit("#", 1)
    if base != M.norm(base):
        return False, f"词未小写/去标点: {ref!r}（应为 {M.norm(base)}#{n_str}）"
    key = f"{base}#{int(n_str)}"
    keys = {w["key"] for w in seg_txt["words"]}
    if key not in keys:
        return False, f"_B4_words.txt 中不存在 {key!r}"
    return True, None


def main():
    txt_words = parse_b4_words(HERE / "_B4_words.txt")
    pages = load_b4_pages(HERE / "B4_事件_定稿.py.txt")
    T = M.load()

    all_ok = True
    missing = [s for s in EXPECTED_SEGS if s not in pages]
    extra = [s for s in pages if s not in EXPECTED_SEGS]
    if missing or extra:
        print(f"段号集合不匹配：缺少 {missing}，多余 {extra}")
        return 1

    for seg in EXPECTED_SEGS:
        P = pages[seg]
        errs = []
        # 字段完整
        for k in ("note", "zone", "trans_in", "trans_out", "ev"):
            if k not in P or not P[k]:
                errs.append(f"缺少字段 {k}")
        if not P.get("note", "").startswith("HKBU SCIE1007"):
            errs.append("note 开头未写明 HKBU SCIE1007")

        # 逐条 ev 基础检查
        seen_ids = set()
        for idx, row in enumerate(P["ev"]):
            if len(row) != 8:
                errs.append(f"第 {idx+1} 条长度不是 8: {row}")
                continue
            eid, verb, wref, off, lead, u, means, g = row
            if eid in seen_ids:
                errs.append(f"id 重复: {eid}")
            seen_ids.add(eid)
            if verb not in ALLOWED_VERBS:
                errs.append(f"{eid}: 动词 {verb!r} 不在范例白名单 {sorted(ALLOWED_VERBS)}")
            ok_w, msg_w = check_word_in_txt(txt_words[seg], wref)
            if not ok_w:
                errs.append(f"{eid} at: {msg_w}")
            if isinstance(u, str) and u.startswith("w:"):
                ok_u, msg_u = check_word_in_txt(txt_words[seg], u[2:])
                if not ok_u:
                    errs.append(f"{eid} until: {msg_u}")
            elif u not in (None, "s") and not (isinstance(u, str) and re.match(r"^d:\d+$", u)):
                errs.append(f"{eid}: 非法 until {u!r}")

        # 用 master_v1 + resolve 做精确帧号与引导检查
        G = T.group(seg)
        doc = build_doc(seg, P)
        evs, probs = RS.resolve_doc(G, doc)
        for p in probs:
            errs.append(f"resolve: {p}")

        for e in evs:
            if not (0 <= e["f_start"] <= e["f_land"] <= e["f_end"] <= G.len_f - 1):
                errs.append(f"{e['id']}: 帧顺序/越界 {e['f_start']}/{e['f_land']}/{e['f_end']} (len={G.len_f})")
            if e.get("end_before_land"):
                errs.append(f"{e['id']}: until 早于 at")

        # 每句覆盖空档 & 每句落点间隔 & 句尾
        max_gap = 0
        max_land_gap = 0
        for s in G.sentences:
            ivs = [(e["f_start"], max(e["f_land"], e["f_end"])) for e in evs]
            gap, gat = longest_uncovered(s["f0"], s["f1"], ivs)
            max_gap = max(max_gap, gap)
            if gap > GAP_LIMIT:
                errs.append(f"{s['sid']}: 覆盖空档 {gap} 帧 > {GAP_LIMIT} (起于 {gat})")
            inside = [e for e in evs if e["f_start"] <= s["f1"] and max(e["f_land"], e["f_end"]) >= s["f0"]]
            last_end = max([max(e["f_land"], e["f_end"]) for e in inside] or [-1])
            if last_end < s["f1"] - END_TOL:
                errs.append(f"{s['sid']}: 末事件结束 {last_end} < 句尾 {s['f1']} - {END_TOL}")
            lands = sorted(e["f_land"] for e in evs if s["f0"] <= e["f_land"] <= s["f1"])
            pts = [s["f0"]] + lands + [s["f1"]]
            lg = max(b - a for a, b in zip(pts, pts[1:]))
            max_land_gap = max(max_land_gap, lg)
            if lg > GAP_LIMIT:
                errs.append(f"{s['sid']}: 落点间隔 {lg} 帧 > {GAP_LIMIT} (lands={lands}, s=[{s['f0']},{s['f1']}])")

        # 引导检查（V1, V2, V3, V4, V5t, V6 ramp）
        guides = RS.guide_plan(evs, len_f=G.len_f, sentences=G.sentences)
        n = G.len_f
        held = max([sum(1 for g in guides if g["gon"] <= f <= g["gend"]) for f in range(n)] or [0])
        over = max([sum(1 for g in guides if g["gs"] <= f < g["goff"]) for f in range(n)] or [0])
        if held > 1 or over > 2:
            errs.append(f"guide V1: held={held}, over={over}")
        gaps = [b["gon"] - a["gon"] for a, b in zip(guides, guides[1:])]
        if any(x < 36 for x in gaps):
            errs.append(f"guide V2: 相邻 gon 最小 {min(gaps)} < 36")
        per = {}
        for g in guides:
            sid = RS._sid_at(G.sentences, g["land"])
            per.setdefault(sid, []).append(g["id"])
        if any(len(v) > 3 for v in per.values()):
            errs.append(f"guide V2: 单句引导超过 3 次 {per}")
        win = max([sum(1 for h in guides if g["gon"] <= h["gon"] < g["gon"] + 600) for g in guides] or [0])
        if win > 5:
            errs.append(f"guide V2: 10 秒内引导 {win} > 5")
        ch = []
        for g in guides:
            ch.append((g["gs"], g["land"]))
            if g["goff"] > g["gend"]:
                ch.append((g["gend"], g["goff"]))
        sp = sum(s["f1"] - s["f0"] for s in G.sentences)
        r3 = union_len(ch) / max(1, sp)
        if r3 > 0.45:
            errs.append(f"guide V3: 变化中占比 {r3:.1%} > 45%")
        bad4 = [g["id"] for g in guides if not (4 <= g["land"] - g["gon"] <= 12 and 16 <= g["land"] - g["gs"] <= 36)]
        if bad4:
            errs.append(f"guide V4: {bad4}")
        if guides:
            last_g = guides[-1]
            if last_g["goff"] - last_g["gend"] < 12:
                errs.append(f"guide V6 ramp: 末引导 {last_g['id']} goff-gend={last_g['goff']-last_g['gend']} < 12 (gend={last_g['gend']}, goff={last_g['goff']}, len={G.len_f})")

        status = "PASS" if not errs else "FAIL"
        print(f"[{status}] {seg:5s}  ev={len(evs):2d}  guides={len(guides):2d}  max_gap={max_gap:2d}  max_land_gap={max_land_gap:2d}  V3={r3:4.0%}")
        for err in errs:
            print(f"   - {err}")
        if errs:
            all_ok = False

    print("\n总结:", "全部 11 段通过！" if all_ok else "存在未通过项，请修复。")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
