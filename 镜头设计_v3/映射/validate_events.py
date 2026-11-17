"""HKBU SCIE1007 课程作业的科普视频：事件表校验（映射/events/<段>.json，格式见 映射/事件表格式.md）。

逐段检查，任何一项不过退出码 1：
  V1 格式    schema、id 唯一、verb 在 flow/grow/eject/retract/appear/move/camera_to/morph/snap 里、ease 合法
  V2 词存在  at / until 引用的词都在总表这段里（wid、'cost'、'and#2' 都行）
  V3 顺序    f_start ≤ f_land ≤ f_end，都在 0..段长−1；until 不早于 at；at.event 只能引用前面的事件
  V4 空档    每句说话期间（首词开口 → 末词说完），没有任何事件在动的连续时间 ≤ 90 帧（1.5 s）
  V5 到句尾  每句里最后一个事件的结束帧 ≥ 句尾 − 2 帧（动作不早停）
另外报告（不判）：每句落点数、最长"无落点"间隔。

用法：
  _env/footage/Scripts/python.exe 镜头设计_v3/映射/validate_events.py [段 ...] [--json 映射/_reports/validate.json]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import maplib as M  # noqa: E402
import resolve as RS  # noqa: E402

GAP = 90
END_TOL = 2


def longest_uncovered(a, b, ivs):
    """[a, b] 里没有被任何区间盖住的最长连续帧数和起点。"""
    cov = sorted((max(a, x), min(b, y)) for x, y in ivs if y >= a and x <= b)
    best, at, cur = 0, a, a
    for x, y in cov:
        if x > cur and x - cur > best:
            best, at = x - cur, cur
        cur = max(cur, y)
    if b - cur > best:
        best, at = b - cur, cur
    return best, at


def validate(group, T):
    G = T.group(group)
    D = json.loads(RS.events_path(G.name).read_text(encoding="utf-8"))
    P = {"V1": [], "V2": [], "V3": [], "V4": [], "V5": []}
    if D.get("schema", RS.SCHEMA) != RS.SCHEMA:
        P["V1"].append(f"schema 不是 {RS.SCHEMA}")
    ids = [RS.normalize(e).get("id") for e in D.get("events", [])]
    for i in {x for x in ids if ids.count(x) > 1}:
        P["V1"].append(f"id 重复：{i}")
    for e in map(RS.normalize, D.get("events", [])):
        if e.get("verb") not in RS.VERBS:
            P["V1"].append(f"{e.get('id')}: verb {e.get('verb')!r} 不在 {RS.VERBS}")
        if e.get("ease", "inout") not in RS.EASES:
            P["V1"].append(f"{e.get('id')}: ease {e.get('ease')!r} 不在 {RS.EASES}")
    evs, probs = RS.resolve_doc(G, D)
    P["V2"] += probs
    for e in evs:
        if not (0 <= e["f_start"] <= e["f_land"] <= e["f_end"] <= G.len_f - 1):
            P["V3"].append(f"{e['id']}: 帧 {e['f_start']}/{e['f_land']}/{e['f_end']} 顺序或越界（段长 {G.len_f}）")
        if e.get("end_before_land"):
            P["V3"].append(f"{e['id']}: until 早于 at")
    rows = []
    for s in G.sentences:
        ivs = [(e["f_start"], max(e["f_land"], e["f_end"])) for e in evs]
        gap, gat = longest_uncovered(s["f0"], s["f1"], ivs)
        inside = [e for e in evs if e["f_start"] <= s["f1"] and max(e["f_land"], e["f_end"]) >= s["f0"]]
        last_end = max([max(e["f_land"], e["f_end"]) for e in inside] or [-1])
        lands = sorted(e["f_land"] for e in evs if s["f0"] <= e["f_land"] <= s["f1"])
        lg = max([b - a for a, b in zip([s["f0"]] + lands, lands + [s["f1"]])] or [s["f1"] - s["f0"]])
        rows.append(dict(sid=s["sid"], f0=s["f0"], f1=s["f1"], events=len(inside), lands=len(lands), gap_f=gap, gap_at=gat,
                         land_gap_f=lg, last_end=last_end))
        if gap > GAP:
            P["V4"].append(f"{s['sid']}: {gap} 帧无事件（从段内第 {gat} 帧起）")
        if last_end < s["f1"] - END_TOL:
            P["V5"].append(f"{s['sid']}: 末事件结束 {last_end} < 句尾 {s['f1']}")
    ok = not any(P.values())
    return dict(group=G.name, ok=ok, events=len(evs), problems=P, sentences=rows)


def main(argv):
    T = M.load()
    names = [a for a in argv if not a.startswith("--") and not a.endswith(".json")]
    names = names or sorted(p.stem for p in RS.EVENTS.glob("*.json") if not p.stem.endswith(".regions"))
    R = []
    for n in names:
        n = n.replace("_", "+") if n.replace("_", "+") in {g["group"] for g in T.d["groups"]} else n
        r = validate(n, T)
        R.append(r)
        bad = {k: v for k, v in r["problems"].items() if v}
        print(f"{r['group']:22} {'通过' if r['ok'] else '不过'}  事件 {r['events']:3}  " + "  ".join(f"{k}×{len(v)}" for k, v in bad.items()))
        for k, v in bad.items():
            for x in v[:4]:
                print(f"    {k} {x}")
    if "--json" in argv:
        out = Path(argv[argv.index("--json") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    n_ok = sum(r["ok"] for r in R)
    print(f"共 {len(R)} 段，通过 {n_ok}，不过 {len(R) - n_ok}")
    return n_ok == len(R)


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
