"""HKBU SCIE1007 课程作业的科普视频：事件表 → 帧号（词→动画映射第二阶段，导演 11-16 23:30 意见）。

读 映射/events/<段>.json（格式见 映射/事件表格式.md）和总表 映射/master_v1.json（词的实测时间，cut 同一套 condense），
把每个事件算成原生 60 fps 帧号，段内帧（f_*）和片内帧（F_* = 段在片里的起点帧 + 段内帧）都给，写 映射/keys/<段>.json，
Blender / Remotion 接口用第一阶段的 bl_maptable.py、src/v3/map/mapTable.mjs（本脚本不往 Remotion 目录写）。

纯 Python（不用 numpy / bpy），validate_events.py、build_master.py、map_bl.py 都 import 这里的 resolve_doc()。

用法：
  _env/footage/Scripts/python.exe 镜头设计_v3/映射/resolve.py            全部 events/*.json
  _env/footage/Scripts/python.exe 镜头设计_v3/映射/resolve.py 1-08 2-03  只算这几段
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import maplib as M  # noqa: E402

FPS = 60
EVENTS = HERE / "events"
KEYS = HERE / "keys"
RM_KEYS = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/map/keys"
VERBS = ("flow", "grow", "eject", "retract", "appear", "move", "camera_to", "morph", "snap")   # morph＝变，snap＝拼（11-17 加）
EASES = ("linear", "in", "out", "inout", "hold")
SCHEMA = "cdk20.events/1"


def fname(group):
    return group.replace("+", "_")


def events_path(group):
    return EVENTS / f"{fname(group)}.json"


class ResolveError(Exception):
    pass


def find_word(G, ref, seg=None):
    """ref：wid（1-08.w018）、'cost'、'and#2'（第 2 个 and）。多段组可给 seg 只在那一段里找。"""
    if ref in G._w:
        return G._w[ref]
    try:
        return G.key(ref if "#" in ref else ref + "#1", seg)
    except (KeyError, IndexError):
        raise ResolveError(f"{G.name}: 没有词 {ref!r}" + (f"（段 {seg}）" if seg else ""))


def normalize(e):
    """第一阶段的老写法（eid / land / lag / start.word）转成现在的写法，其余字段原样。"""
    e = dict(e)
    if "eid" in e and "id" not in e:
        e["id"] = e.pop("eid")
    if "land" in e and "at" not in e:
        lw = e.pop("land")
        e["at"] = dict(word=lw["word"], off=e.pop("lag", 0))
    if "start" in e and "lead" not in e and isinstance(e["start"], dict) and "word" in e["start"]:
        e["_start_word"] = e.pop("start")["word"]
    return e


def sentence_of(G, w):
    return G._s[w["sid"]]


def resolve_doc(G, D):
    """G：maplib.Group；D：事件表 dict。返回 (events, problems)。events 按表里的顺序，每个带 f_start/f_land/f_end（段内 60 fps）。"""
    out, probs, by_id = [], [], {}
    for k, e0 in enumerate(D.get("events", [])):
        e = normalize(e0)
        eid = e.get("id") or f"e{k:03d}"
        try:
            seg = e.get("seg")
            at = e.get("at")
            if at is None:
                raise ResolveError(f"{eid}: 没有 at（起于哪个词）")
            if "word" in at:
                w = find_word(G, at["word"], seg)
                land = w["f0"] + int(at.get("off", 0))
                anchor = dict(word=w["wid"], w=w["w"], key=w["key"], sid=w["sid"], word_f0=w["f0"])
            elif "event" in at:
                if at["event"] not in by_id:
                    raise ResolveError(f"{eid}: at.event {at['event']!r} 不在它前面")
                p = by_id[at["event"]]
                land = p["f_land"] + int(at.get("off", 0))
                anchor = dict(word=p["word"], w=p.get("w"), key=p.get("key"), sid=p["sid"], word_f0=p.get("word_f0"), after=p["id"])
            else:
                raise ResolveError(f"{eid}: at 要有 word 或 event")
            if "_start_word" in e:
                start = find_word(G, e["_start_word"], seg)["f0"]
            else:
                start = land - int(e.get("lead", 0))
            u = e.get("until")
            until = None
            if u is None:
                end = land
            elif "word" in u:
                uw = find_word(G, u["word"], seg)
                end = (uw["f0"] if u.get("edge") == "start" else uw["f1"]) + int(u.get("off", 0))
                until = uw["wid"]
            elif "sentence_end" in u:
                sid = anchor["sid"] if u["sentence_end"] is True else u["sentence_end"]
                if sid not in G._s:
                    raise ResolveError(f"{eid}: 没有句 {sid}")
                end = G._s[sid]["f1"] + int(u.get("off", 0))
                until = sid
            elif "dur" in u:
                end = land + int(u["dur"])
            elif "event" in u:
                if u["event"] not in by_id:
                    raise ResolveError(f"{eid}: until.event {u['event']!r} 不在它前面")
                end = by_id[u["event"]]["f_end"] + int(u.get("off", 0))
                until = u["event"]
            else:
                raise ResolveError(f"{eid}: until 要有 word / sentence_end / dur / event")
            r = dict(id=eid, obj=e.get("obj", eid), verb=e.get("verb"), ease=e.get("ease", "inout"), means=e.get("means", ""),
                     f_start=int(start), f_land=int(land), f_end=int(max(end, land)), until=until, **anchor)
            for k2 in ("value", "to", "migrated", "role", "tool"):
                if k2 in e:
                    r[k2] = e[k2]
            if end < land:
                r["end_before_land"] = True
            by_id[eid] = r
            out.append(r)
        except ResolveError as x:
            probs.append(str(x))
    return out, probs


def words_hash(G):
    s = json.dumps([(w["wid"], w["f0"], w["f1"]) for w in G.words] + [G.len_f], ensure_ascii=False)
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def keys_for(group, T=None):
    T = T or M.load()
    G = T.group(group)
    D = json.loads(events_path(G.name).read_text(encoding="utf-8"))
    evs, probs = resolve_doc(G, D)
    F0 = G.d["cut_start_f"]
    for e in evs:
        e.update(F_start=F0 + e["f_start"], F_land=F0 + e["f_land"], F_end=F0 + e["f_end"])
    K = dict(schema="cdk20.keys/1", note="HKBU SCIE1007 课程作业的科普视频：resolve.py 算出的事件帧（不要手改，改 events/ 再重跑）。",
             group=G.name, segs=G.segs, tool=D.get("tool"), fps=FPS, len_f=G.len_f, cut=T.d["cut"]["name"], cut_start_f=F0,
             cut_start_s=G.d["cut_start_s"], master_built=T.d["built"], words_hash=words_hash(G),
             events_src=str(events_path(G.name).relative_to(ROOT)).replace("\\", "/"),
             words=[dict(wid=w["wid"], w=w["w"], key=w["key"], sid=w["sid"], f0=w["f0"], f1=w["f1"], F0=F0 + w["f0"], F1=F0 + w["f1"]) for w in G.words],
             sentences=[dict(sid=s["sid"], text=s["text"], w_first=s["w_first"], w_last=s["w_last"], f0=s["f0"], f1=s["f1"]) for s in G.sentences],
             holds=D.get("holds", []), events=evs, problems=probs)
    return K


def write_index():
    RM_KEYS.mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in RM_KEYS.glob("*.json"))
    lines = ["// HKBU SCIE1007 课程作业的科普视频：resolve.py 自动生成，不要手改。", ""]
    for i, n in enumerate(names):
        lines.append(f"import k{i} from './{n}.json';")
    lines.append("")
    lines.append("const KEYS = {")
    for i, n in enumerate(names):
        K = json.loads((RM_KEYS / f"{n}.json").read_text(encoding="utf-8"))
        for s in [K["group"]] + K["segs"]:
            lines.append(f"  {json.dumps(s)}: k{i},")
    lines.append("};")
    lines.append("export default KEYS;")
    (RM_KEYS / "index.js").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv):
    T = M.load()
    KEYS.mkdir(exist_ok=True)
    names = argv or sorted(p.stem for p in EVENTS.glob("*.json") if not p.stem.endswith(".regions"))
    bad = 0
    for n in names:
        g = T.group(n.replace("_", "+") if n.replace("_", "+") in {x["group"] for x in T.d["groups"]} else n).name
        K = keys_for(g, T)
        txt = json.dumps(K, ensure_ascii=False, indent=1)
        (KEYS / f"{fname(g)}.json").write_text(txt, encoding="utf-8")
        bad += bool(K["problems"])
        print(f"{g:22} 事件 {len(K['events']):3}  问题 {len(K['problems'])}" + (f"  {K['problems'][:3]}" if K["problems"] else ""))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
