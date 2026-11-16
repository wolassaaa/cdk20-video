"""HKBU SCIE1007 课程作业的科普视频：把现有 45 段节拍表（粗剪/对时/beats_v8/*.json）自动转成新事件表 映射/events/<段>.json。

能转多少转多少：
  1. 1-08 钱段：按样板 A v4（inserts/_work_s108/s108_events_v4.json + bl_s108_money_v4.py 里的机位/压实/收料/1 in 10 时间）完整转，
     有词的事件 off=0 直接落在总表实测词上；没词的（第 3 张钞票 430 帧这类）挂最近的词 + 偏移帧（偏移按 v4 自己的词表算，保留设计间隔）。
  2. 有语义事件的段（第 5 章 beats/<段>.json 经总表导入的事件）：逐个转成 at=词+偏移、lead、until dur。
  3. 只有变速锚点的段（retime_v8 的 anchors：[源片秒, 段内秒]）：每两个锚点之间转成一个 obj=footage、verb=move 的事件，
     value=[源片起秒, 源片止秒]，挂最近的词 + 偏移。这样旧动画可以按表原生重渲（不再变速），但它们不是"说到哪个词哪个东西出现"的语义事件，
     单列进清单"要手写语义事件"。
已有的手写事件表（events/ 里已经有、且不是本脚本写的）不覆盖。
出：events/<段>.json、映射/_reports/迁移清单.json 和 迁移清单.md。

用法：_env/footage/Scripts/python.exe 镜头设计_v3/映射/migrate_beats_v8.py [--force]
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V3 = HERE.parent
sys.path.insert(0, str(HERE))
import maplib as M  # noqa: E402
import resolve as RS  # noqa: E402
import validate_events as VE  # noqa: E402

BEATS = V3 / "粗剪/对时/beats_v8"
S108 = V3 / "styleframes/art/fusion/s1/inserts/_work_s108/s108_events_v4.json"
REP = HERE / "_reports"
TAG = "migrate_beats_v8"
VERB = {"land": "eject", "lift": "eject", "start": "retract", "head": "flow", "grow": "grow", "ring": "appear", "keyed": "appear",
        "label": "appear", "mark": "appear", "text": "appear", "count": "appear", "fade": "appear", "flow": "flow", "eject": "eject",
        "retract": "retract", "appear": "appear", "move": "move", "camera_to": "camera_to", "action": "move", "pulse": "appear",
        "cam": "camera_to", "camera": "camera_to", "slide": "move", "push": "move", "hop": "move", "drop": "move", "pop": "appear"}


def nearest(words, f, f0key="f0"):
    i = min(range(len(words)), key=lambda k: (abs(words[k][f0key] - f), k))
    return i, f - words[i][f0key]


def at_word(G, Gw_v4, f, word_key=None):
    """v4 帧 f → (wid, off)。有词就 off=0 落在那个词上；没词挂最近的词（按 v4 词表算偏移）。"""
    if word_key:
        return dict(word=RS.find_word(G, word_key)["wid"], off=0)
    i, off = nearest(Gw_v4, f)
    return dict(word=G.words[i]["wid"], off=int(off))


def ev(eid, obj, verb, at, lead=0, until=None, ease="inout", means="", **kw):
    e = dict(id=eid, obj=obj, verb=verb, at=at)
    if lead:
        e["lead"] = int(lead)
    if until:
        e["until"] = until
    e["ease"] = ease
    if means:
        e["means"] = means
    e.update(kw)
    return e


def mig_108(G):
    D = json.loads(S108.read_text(encoding="utf-8"))
    vw = [dict(f0=int(round(w["t0"] * 60)), f1=int(round(w["t1"] * 60))) for w in D["words"]] if isinstance(D["words"], list) else None
    if vw is None or len(vw) != len(G.words):
        B = json.loads((BEATS / "1-08.json").read_text(encoding="utf-8"))
        vw = [dict(f0=int(round(w["t0"] * 60)), f1=int(round(w["t1"] * 60))) for w in B["words"]]
    assert len(vw) == len(G.words), "1-08 v4 词表和总表词数不同"
    A = lambda f, k=None: at_word(G, vw, f, k)  # noqa: E731

    def S(f, k):
        """跟随拍：挂在这一串的那个词上，偏移按 v4 自己的词表算（保留 12 帧 / 6 帧的设计间隔）。"""
        w = RS.find_word(G, k)
        i = G.words.index(w)
        return dict(word=w["wid"], off=int(f - vw[i]["f0"]))
    E = []
    head = D["head"]
    E.append(ev("head_start", "flow", "flow", A(head[0][0], "start"), until=dict(word="now", edge="start"), ease="linear",
                means="Start：红料从左边进画，沿流道走，经过四个时间小格的浇口，now 到 A 格"))
    for w in D["wells"]:
        E.append(ev(f"well{w['k']}", f"well_{w['k']}", "grow", A(w["land"], w["word"]), lead=w["land"] - w["gate"], ease="out",
                    means=f"{w['word']}：时间小格（圆饼）长满"))
    E.append(ev("head_now", "flow", "flow", A(head[1][0], "now"), until=dict(word="and#2", edge="start"), ease="linear",
                means="now：料头到 A 格，再经 B、C 慢流到药排"))
    E.append(ev("cam_follow", "camera", "camera_to", A(261, "ready"), until=dict(dur=31), off_note="ready 圆饼鼓完 +1 帧起步",
                means="ready 鼓完后机位停到格子区"))
    E[-1]["at"]["off"] = 1
    for b in D["bills"]:
        E.append(ev(f"bill{b['i']}", f"bill_{b['i']}", "eject", A(b["land"], b["word"]), lead=b["land"] - b["grow"], ease="out",
                    eject_lead=b["land"] - b["eject"], fly_lead=b["land"] - b["fly"],
                    means=(f"{b['word']}：" if b["word"] else "") + f"第 {b['i'] + 1} 张钞票长满、顶出、翻落成叠"))
    letters = D["letters"]
    f28 = next(e["frame"] for e in D["events"] if e["id"] == "text_28")
    E.append(ev("text_28", "letters_$2.8", "grow", A(f28, "2.8"), lead=f28 - min(L["done"] for L in letters if L["j"] < 4) + 14, ease="out",
                means="2.8：凸字 $2.8 长满"))
    fb = min(L["done"] for L in letters if L["j"] > 4)
    E.append(ev("text_billion", "letters_billion", "grow", A(fb, "billion"), lead=14, until=dict(dur=max(L["done"] for L in letters) - fb),
                ease="out", means="billion：一个字母一个字母长完"))
    E.append(ev("stack_press", "stack", "move", A(522), until=dict(dur=561 - 522), means="dollars 落完：顶上两张错开 5 mm 再归位（压实）",
                value_note="v4 写死 522–561，v6 改读这里"))
    E.append(ev("cam_push", "camera", "camera_to", A(head[4][0], "and#2"), until=dict(dur=45), means="And：真机位推向药格"))
    for p in D["pills"]:
        k = p["k"]
        E.append(ev(f"pill{k}", f"pill_{k}", "grow", S(p["land"], "drugs"), lead=p["land"] - p["grow"], ease="out",
                    means="drugs：十颗胶囊依次长满" if k == 0 else ""))
    E.append(ev("head_and", "flow", "flow", A(head[4][0], "and#2"), until=dict(dur=head[-1][0] - head[4][0]), ease="linear",
                means="And：料头流过十个药格"))
    for p in D["pills"]:
        if "retract" in p:
            fr = p["retract"] + 4
            first = fr == min(q["retract"] + 4 for q in D["pills"] if "retract" in q)
            E.append(ev(f"pillx{p['k']}", f"pill_{p['k']}", "retract", S(fr, "only#2"), lead=4,
                        until=dict(dur=p["retract_end"] - fr), means="only：九颗依次收回浇口" if first else ""))
    K = D["keep"]
    E.append(ev("keep_up", f"pill_6", "eject", A(K["lifted"], "one"), lead=K["lifted"] - K["lift"], ease="out", means="one：留下那颗被顶针顶起"))
    E.append(ev("label_1in10", "letters_1in10", "grow", A(K["lifted"], "one"), until=dict(dur=4 * 6), ease="out", means="one：凸字 1 in 10 一个字一个字长"))
    E.append(ev("keep_hop", "pill_6", "move", A(K["hop"], "reaches"), until=dict(word="market", edge="start"), means="reaches：那颗跳向钱堆"))
    E.append(ev("cam_pull", "camera", "camera_to", A(K["hop"], "reaches"), until=dict(dur=48), means="reaches 前 6 帧起拉到钱堆和药排之间"))
    E[-1]["at"]["off"] = -6
    E.append(ev("keep_land", "pill_6", "move", A(K["land"], "market"), until=dict(sentence_end=True), ease="out",
                means="market：落定在钱堆上，轻轻落稳到句尾"))
    E.append(ev("gates_retract", "gates", "retract", A(K["land"], "market"), until=dict(sentence_end=True), ease="inout",
                means="market 后空药格的浇口料依次退回主沟，动到话说完", stagger=3, lead_off=2))
    E.append(ev("cam_settle", "camera", "camera_to", A(K["land"], "market"), until=dict(dur=40), means="market：轻推到钱堆"))
    return dict(schema=RS.SCHEMA, group="1-08", tool="blender", migrated=TAG,
                note="HKBU SCIE1007 课程作业的科普视频。1-08 钱段完整事件表（由样板 A v4 迁移，bl_s108_money_v6.py 只从这里读时间）。",
                source=str(S108.relative_to(ROOT)).replace("\\", "/"), holds=[], events=E)


def mig_semantic(G, evs):
    out = []
    for e in evs:
        verb = VERB.get(e["verb"])
        if e.get("word"):
            w = G._w[e["word"]]
            at = dict(word=w["wid"], off=int(e["f_land"] - w["f0"]))
        else:
            i, off = nearest(G.words, e["f_land"])
            at = dict(word=G.words[i]["wid"], off=int(off))
        x = ev(e["eid"], e.get("obj") or e["eid"], verb or "appear", at, lead=e["f_land"] - e["f_start"],
               until=dict(dur=e["f_end"] - e["f_land"]) if e["f_end"] > e["f_land"] else None, migrated=f"{TAG}:semantic")
        if verb is None:
            x["verb_was"] = e["verb"]
        out.append(x)
    return out


def mig_anchors(G, B):
    A = B["anchors"]
    out = []
    for k, ((sa, ta), (sb, tb)) in enumerate(zip(A, A[1:])):
        fa, fb = int(round(ta * 60)), int(round(tb * 60))
        if fb <= fa:
            continue
        i, off = nearest(G.words, fa)
        out.append(ev(f"footage{k:02d}", "footage", "move", dict(word=G.words[i]["wid"], off=int(off)), until=dict(dur=fb - fa), ease="linear",
                      value=[round(sa, 3), round(sb, 3)], migrated=f"{TAG}:anchor",
                      means=f"旧动画源片 {sa:.2f}→{sb:.2f} s 在这段里播放（原生重渲时按这个对应，不再变速）"))
    return out


def main(force):
    T = M.load()
    REP.mkdir(exist_ok=True)
    RS.EVENTS.mkdir(exist_ok=True)
    rows = []
    for f in sorted(BEATS.glob("*.json")):
        seg = f.stem
        B = json.loads(f.read_text(encoding="utf-8"))
        G = T.group(seg)
        dst = RS.events_path(G.name)
        row = dict(seg=seg, group=G.name, anchors=len(B.get("anchors", [])), words=len(G.words))
        if dst.exists() and not force:
            old = json.loads(dst.read_text(encoding="utf-8"))
            if old.get("migrated") != TAG:
                row.update(kind="hand", note="已有手写事件表，没覆盖")
                rows.append(row)
                continue
        if seg == "1-08":
            D = mig_108(G)
            row["kind"] = "full"
        else:
            sem = [e for e in G.events() if e.get("native") and e.get("tool") == "blender"]
            E = mig_semantic(G, sem) if sem else []
            row["kind"] = "semantic+anchor" if E else "anchor_only"
            row["semantic_events"] = len(E)
            row["unmapped_verbs"] = sorted({e["verb_was"] for e in E if "verb_was" in e})
            E += mig_anchors(G, B)
            D = dict(schema=RS.SCHEMA, group=G.name, tool="blender" if sem else "warp_source", migrated=TAG,
                     note="HKBU SCIE1007 课程作业的科普视频。由 beats_v8 自动迁移：footage* 是旧动画变速锚点（结构性），"
                          + ("另有第 5 章语义事件。" if sem else "没有语义事件，要手写。"),
                     source=str(f.relative_to(ROOT)).replace("\\", "/"), holds=[], events=E)
        dst.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
        r = VE.validate(G.name, T)
        row.update(events=r["events"], valid=r["ok"], problems={k: len(v) for k, v in r["problems"].items() if v},
                   first=[x for v in r["problems"].values() for x in v][:2])
        rows.append(row)
        print(f"{seg}  {row['kind']:16} 事件 {row['events']:3}  {'通过' if row['valid'] else '不过 ' + str(row['problems'])}")
    (REP / "迁移清单.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    full = [r for r in rows if r["kind"] == "full"]
    sem = [r for r in rows if r["kind"] == "semantic+anchor"]
    anc = [r for r in rows if r["kind"] == "anchor_only"]
    L = ["# beats_v8 → 事件表 迁移清单", "", "HKBU SCIE1007 课程作业的科普视频。`映射/migrate_beats_v8.py` 生成，" + time.strftime("%Y-%m-%d %H:%M +09:00") + "。", "",
         f"共 {len(rows)} 段：完整转好 {len(full)}，语义事件 + 锚点 {len(sem)}，只有变速锚点 {len(anc)}，保留手写 {sum(r['kind'] == 'hand' for r in rows)}。"
         f"校验全过 {sum(bool(r.get('valid')) for r in rows)} 段。", "",
         "| 段 | 方式 | 事件 | 校验 | 要点 |", "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['seg']} | {r['kind']} | {r.get('events', '')} | {'过' if r.get('valid') else ('—' if r['kind'] == 'hand' else '不过')} | "
                 f"{r.get('note') or '；'.join(r.get('first', []))[:120]} |")
    L += ["", "## 转不了的（要手写语义事件）", "",
          "下面这些段在 cut_v8 里是旧动画按词变速，节拍表里只有锚点，没有\"说到哪个词哪个东西出现\"的信息。"
          "锚点已转成 footage 事件（可用来原生重渲旧动画），但语义事件要按剧本手写（看 映射/事件表格式.md）：", "",
          "、".join(r["seg"] for r in anc), ""]
    (REP / "迁移清单.md").write_text("\n".join(L), encoding="utf-8")
    return rows


if __name__ == "__main__":
    main("--force" in sys.argv)
