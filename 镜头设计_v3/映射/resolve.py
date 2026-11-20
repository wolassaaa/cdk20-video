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
VERBS = ("flow", "grow", "eject", "retract", "appear", "move", "camera_to", "morph", "snap",   # morph＝变，snap＝拼（11-17 加）
         "plug_in", "plug_out", "twist", "clamp", "power_on", "power_off", "eject_swap",   # 插座比喻的动作词（06_插座比喻.md 4.0，11-20 登记）
         "dissolve")   # dissolve＝叠化（11-20，三维钻取到真实结构；frame_integrity 认它是设计渐变）
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
            for k2 in ("value", "to", "migrated", "role", "tool", "guide"):
                if k2 in e:
                    r[k2] = e[k2]
            if end < land:
                r["end_before_land"] = True
            by_id[eid] = r
            out.append(r)
        except ResolveError as x:
            probs.append(str(x))
    return out, probs


# ---------- 视线引导（05_视线引导.md，11-20）----------
# 事件可带可选字段 guide：{"kind": "focus"|"runner"|"none", "target": 图层id或列表, "g_on": 8, "pull": 18,
#   "travel": 32（走料时长）, "arrive": 4（走料比落点早几帧到浇口）, "nudge": true/false（预颤）, "rim": true/false（轮廓光）,
#   "box": [x, y, w, h]（目标在画面上的框，预颤的转心和亮度检查用）, "dist": 0.41（走料距离占画面宽）, "from": 起点}
# 不写 guide 时：grow / eject / snap / move → focus，目标 = obj；其余动词（appear、camera_to、flow、morph、retract）不引导。
# kit.jsx 的 guidePlan() 照同一套规则（有 K.guides 时直接用这里算好的）。
GUIDE = dict(gOn=8, pull=18, minGap=36, hold=120, relax=30, travel=32, arrive=4, sameGap=120)
GUIDE_VERBS = ("grow", "eject", "snap", "move")
SELF_PREP = ("grow", "eject", "snap")      # 这一拍零件自己在长 / 拔 / 拼，它的预备就是预颤，不另加


def _sid_at(sents, f):
    """f 落在哪一句（不在句里就取最近的一句）。"""
    best = None
    for s in sents or []:
        if s["f0"] <= f <= s["f1"]:
            return s["sid"]
        d = min(abs(f - s["f0"]), abs(f - s["f1"]))
        if best is None or d < best[0]:
            best = (d, s["sid"])
    return best[1] if best else None


def guide_plan(evs, len_f=None, P=GUIDE, sentences=None):
    """evs：resolve_doc 的事件（带 f_start/f_land/f_end，原 guide 字段在 e['guide']）。返回按时间排好的引导列表。
    V2 的上限也在这里守住：每句最多 3 次、任意 10 秒最多 5 次，超出的并进前一个（不点）。"""
    items = []
    for e in sorted(evs, key=lambda x: x["f_land"]):
        g = e.get("guide") or {}
        kind = g.get("kind") or ("focus" if e.get("verb") in GUIDE_VERBS else "none")
        if kind == "none" or e.get("obj") == "footage":      # 迁移来的变速锚点不是语义事件
            continue
        tg = g.get("target", e.get("obj", e["id"]))
        tg = list(tg) if isinstance(tg, (list, tuple)) else [tg]
        land = e["f_land"]
        if kind == "runner":
            gon = land - int(g.get("arrive", P["arrive"]))
            gs = gon - int(g.get("travel", P["travel"]))
        else:
            gon = land - int(g.get("g_on", P["gOn"]))
            gs = gon - int(g.get("pull", P["pull"]))
        if gs < 0:                       # 开场第一拍来不及提前，就不引导（定场）
            continue
        gend = max(land, min(e["f_end"], land + P["hold"]))
        selfprep = e.get("verb") in SELF_PREP and land - e["f_start"] <= 34
        it = dict(id=e["id"], target=tg, kind=kind, gs=gs, gon=gon, land=land, gend=gend, goff=gend + P["relax"], tick=land - 4,
                  nudge=bool(g.get("nudge", not selfprep)), rim=bool(g.get("rim", True)), ev_s=e["f_start"], events=[e["id"]])
        for k in ("box", "dist", "path", "from"):
            if k in g:
                it[k] = g[k]
        if items:
            p = items[-1]
            if set(p["target"]) == set(tg) and gs < p["goff"] + P["sameGap"]:
                p["events"].append(e["id"])            # 同一个东西刚点过，不再点
                continue
            if gon - p["gon"] < P["minGap"]:           # 两次点名太近：并进前一个，只点一次
                p["target"] = p["target"] + [t for t in tg if t not in p["target"]]
                p["gend"] = max(p["gend"], gend)
                p["goff"] = p["gend"] + P["relax"]
                p["events"].append(e["id"])
                continue
            sid = _sid_at(sentences, land)
            if (sentences and sum(_sid_at(sentences, q["land"]) == sid for q in items) >= 3) or sum(q["gon"] > gon - 600 for q in items) >= 5:
                p["events"].append(e["id"])            # 这一句 / 这 10 秒已经够密了
                continue
        items.append(it)
    for p, n in zip(items, items[1:]):                 # 前一个还没退完，下一个就开始拉：交接，焦点从前一个滑到下一个
        if p["goff"] > n["gs"]:
            p["gend"] = max(p["land"], min(p["gend"], n["gs"]))
            p["goff"] = max(p["gend"], min(p["goff"], n["gon"]))
            p["handoff"] = n["id"]
    if len_f:
        for it in items:
            it["goff"] = min(it["goff"], len_f - 1)
            it["gend"] = min(it["gend"], it["goff"])
    return items


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
    guides = guide_plan(evs, G.len_f, sentences=[dict(sid=x["sid"], f0=x["f0"], f1=x["f1"]) for x in G.sentences])
    owner = {it["id"]: it for it in guides}
    into = {x: it["id"] for it in guides for x in it["events"][1:]}
    for e in evs:
        it = owner.get(e["id"])
        if it:
            e.update(g_start=it["gs"], g_on=it["gon"], g_end=it["gend"], g_off=it["goff"], g_tick=it["tick"],
                     G_start=F0 + it["gs"], G_on=F0 + it["gon"], G_end=F0 + it["gend"], G_off=F0 + it["goff"], G_tick=F0 + it["tick"])
        elif e["id"] in into:
            e["guide_into"] = into[e["id"]]
    for it in guides:
        it.update(G_start=F0 + it["gs"], G_on=F0 + it["gon"], G_land=F0 + it["land"], G_end=F0 + it["gend"], G_off=F0 + it["goff"], G_tick=F0 + it["tick"])
    K = dict(schema="cdk20.keys/1", note="HKBU SCIE1007 课程作业的科普视频：resolve.py 算出的事件帧（不要手改，改 events/ 再重跑）。",
             group=G.name, segs=G.segs, tool=D.get("tool"), fps=FPS, len_f=G.len_f, cut=T.d["cut"]["name"], cut_start_f=F0,
             cut_start_s=G.d["cut_start_s"], master_built=T.d["built"], words_hash=words_hash(G),
             events_src=str(events_path(G.name).relative_to(ROOT)).replace("\\", "/"),
             words=[dict(wid=w["wid"], w=w["w"], key=w["key"], sid=w["sid"], f0=w["f0"], f1=w["f1"], F0=F0 + w["f0"], F1=F0 + w["f1"]) for w in G.words],
             sentences=[dict(sid=s["sid"], text=s["text"], w_first=s["w_first"], w_last=s["w_last"], f0=s["f0"], f1=s["f1"]) for s in G.sentences],
             holds=D.get("holds", []), events=evs, guides=guides, problems=probs)
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
