"""HKBU SCIE1007 课程作业的科普视频：第 5 章六段（5-01、5-03、5-07、5-08、W4、5-10）的节拍表（下一步方案_20261116 第 1.2 节）。

每个事件挂在 C 录音里的一个词上（W4 挂在歌的拍上）。layer "3d" 的事件由 inserts/bl_s5d.py 读去定 Blender 里的时间常数；
其余由 Remotion（src/v3/fusion/s5d.jsx）按 kind 画：ink 印刷字、note 钢笔字（Caveat）、keyed 关键词加红线、ul 红线、leader 引线、
ring 墨线圈、pen 墨线（可带箭头）、tag OUR RE-DOCKING、fade 让一组字退场、以及各段自己的 calendar、bars、keyturn、road、dots。
坐标是 1920x1080 画面像素（Blender 探点 S5D_PROJ 量过的）。写完跑 beats_resolve.py 换算帧并自检。
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "beats"
SRC_PAPER = "Ren 2023"


def seg(name, events=None, audio=None, **kw):
    a = dict(kind="VO", head=0.15, tail=0.25, pmax=1.2, pkeep=0.7)
    a.update(audio or {})
    d = dict(seg=name, fps=60, speaker="C", audio=a, events=events, **kw)
    (OUT / f"{name}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def E(id, word=None, **k):
    e = dict(id=id)
    if word is not None:
        e["word"] = word
    e.update(k)
    return e


CARD_X = [299 + 237.5 * i for i in range(7)]
CARDS = [("001", "Kd 9.2 µM")] + [(n, "Kd > 30 µM") for n in ("004", "007", "009", "015", "019", "025")]

# ------------------------------------------------------------------ 5-01
seg("5-01", fade_end=1150, events=[
    E("cam1", "truth.", lead=74, layer="3d", obj="cam"),
    *[E(f"card{i}", "Seven", lag=round(i * 170 / 6), layer="3d", obj="cards") for i in range(7)],
    *[E(f"num{i}", "Seven", lag=round(i * 170 / 6) + 4, kind="ink", x=CARD_X[i], y=548, size=30, text=CARDS[i][0], anchor="middle", dur=14, obj="cards", out="up_s") for i in range(7)],
    E("made", "made", lag=14, kind="note", x=150, y=250, size=50, text="seven real molecules, made in a lab", dur=40, out="up_s"),
    E("q", "Do", kind="note", x=150, y=330, size=50, text="do any grab CDK20?", dur=30, out="down_s"),
    E("up", "grab", lead=79, layer="3d", obj="cam"),
    E("up_s", "grab", lag=-79, kind="mark"),
    E("down_s", "Grip", lag=-76, kind="mark"),
    E("ring", "CDK20?", kind="ring", cx=1275, cy=262, rx=190, ry=170, dur=24, out="down_s"),
    E("ringlbl", "CDK20?", lag=8, kind="ink", x=1060, y=280, size=48, text="CDK20", anchor="end", dur=14, out="down_s"),
    E("down", "Grip", lead=76, layer="3d", obj="cam"),
    *[E(f"kd{i}", "Kd:", lag=i * 3, kind="ink", x=CARD_X[i], y=734, size=28, text=CARDS[i][1], anchor="middle", dur=16, obj="kdlab") for i in range(7)],
    E("def1", "measured", kind="ink", font="serif", x=150, y=210, size=40, text="Kd ≈ how much molecule it takes", dur=40),
    E("ulmol", "molecule", kind="ul", x=150, y=210, size=40, before="Kd ≈ how much ", key="molecule", dur=12),
    E("ulhow", "how", kind="ul", x=150, y=210, size=40, before="Kd ≈ ", key="how much", dur=12),
    E("pile", after="ulmol", gap=48, kind="dots", x=CARD_X[0] + 150, y=520, n=14, dur=24),
    E("def2", "it", kind="ink", font="serif", x=150, y=262, size=40, text="to grab half the protein", dur=30),
    E("ulhalf", "half", kind="ul", x=150, y=262, size=40, before="to grab ", key="half", dur=10),
    E("ulprot", "protein.", kind="ul", x=150, y=262, size=40, before="to grab half the ", key="protein", dur=12),
    E("lower", "Lower", kind="keyed", x=150, y=370, size=64, parts=["Kd: lower = ", "tighter", ""], dur=40),
    E("gauge", "tighter.", kind="gauge", x=150, y=412, dur=30),
], source=[[0, "Illustration · structures and Kd: Ren 2023, Fig. 5, p. 1447", "binding assay · cards cut from the paper's figure, not redrawn"]])

# ------------------------------------------------------------------ 5-03
seg("5-03", fade_end=998, events=[
    E("hl001", "001's", kind="ring", cx=CARD_X[0], cy=630, rx=110, ry=95, dur=20, fill="red", out="cam1s"),
    E("kd", "9.2", kind="keyed", x=80, y=236, size=84, parts=["Kd = ", "9.2", " ± 0.5 µM"], dur=36, out="pocket_out"),
    E("lbl", "9.2", lag=6, kind="ink", x=84, y=150, size=30, text="001 · binding to CDK20", dur=14, out="pocket_out"),
    E("n3", "micromolar.", kind="ink", x=84, y=290, size=30, text="(n = 3)", dur=12, out="pocket_out"),
    E("cam1s", "micromolar.", lag=-70, kind="mark"),
    E("lift", "micromolar.", lag=-60, layer="3d", obj="cards", lead=0, dur=66),
    E("cards_gone", "micromolar.", lag=25, layer="3d", obj="cards"),
    E("cam1", "other", lead=180, layer="3d", obj="cam"),
    E("tag", "six?", kind="tag", x=560, y=748, leader=[[760, 610], [700, 700]], text="OUR RE-DOCKING (AutoDock Vina)", sub="not the authors' coordinates", out="pocket_out"),
    E("six", "All", kind="ink", font="serif", x=84, y=362, size=40, text="the other six: Kd > 30 µM", dur=30, out="pocket_out"),
    E("ul30", "30.", kind="ul", x=84, y=362, size=40, before="the other six: Kd ", key="> 30 µM", dur=12, out="pocket_out"),
    E("weaker", "weaker.", kind="note", x=88, y=430, size=52, text="much weaker", lead=20, dur=26, out="pocket_out"),
    E("pocket_out", "And", kind="fade", dur=20),
    E("m2", "part.", lead=136, layer="3d", obj="cam"),
    E("cal", "clock", kind="calendar", x=94, y=560, c=56, cross_to="days,", dur=36, out="end"),
    E("days30", "30", kind="keyed", x=90, y=470, size=110, parts=["", "30", " days"], dur=30, out="end"),
    E("from", "from", kind="ink", x=94, y=520, size=30, text="from picking the target to the first confirmed hit", dur=40, out="end"),
    E("road", "picking", layer="3d", obj="road", lead=54),
    E("target", "target", kind="ink", x=0, y=0, size=34, text="Target", anchor="middle", at_pt="st0", dur=12, obj="roadlbl"),
    E("arrow", "first", kind="pen", from_pt="st0", to_pt="st1", head=14, dur=20, obj="roadlbl"),
    E("fill", "hit.", lead=150, layer="3d", obj="road"),
    E("hit", "hit.", lag=6, kind="ink", x=0, y=0, size=34, text="Hit", anchor="middle", at_pt="st1", dur=12, fill="red", obj="roadlbl"),
], source=[[0, "Kd: Ren 2023, Fig. 5, p. 1447 · pose: our AutoDock Vina re-docking into the AlphaFold model", "predicted · CDK20 surface shown see-through"],
           ["pocket_out", "Illustration · 30 days: Ren 2023, pp. 1443, 1447", ""]])

# ------------------------------------------------------------------ 5-07
seg("5-07", fade_end=1262, events=[
    E("not", "all.", kind="note", x=140, y=300, size=52, text="not at all", lead=10, dur=20, out="loop"),
    E("cam1", "This", lead=106, layer="3d", obj="cam"),
    E("loop", "This", lag=10, kind="loop", d="M1740 300 Q1590 120 1400 190", end=[1400, 190], ang=-2.75, dur=40, out="never"),
    E("again", "loop", kind="note", x=1180, y=150, size=46, text="the loop, again", dur=24, out="keys_in"),
    E("ulagain", "again,", kind="ul", x=1180, y=150, size=46, before="the loop, ", key="again", font="hand", dur=12, out="keys_in"),
    E("now", "now", kind="note", x=140, y=360, size=48, text="now with real lab data", dur=30, out="keys_in"),
    E("bead1", "lab", lead=50, kind="bead", along="loop", dur=50),
    E("bead2", "in,", lead=60, kind="bead", along="loop", dur=60),
    E("tube", "inside.", kind="ring", cx=0, cy=0, rx=90, ry=150, at_pt="tube", dur=16, out="keys_in"),
    E("results", "results", kind="note", x=140, y=430, size=48, text="results back in", dur=24, out="keys_in"),
    E("pred", "predicted", kind="note", x=140, y=500, size=48, text="+ a predicted pose of 001", dur=34, out="keys_in"),
    E("pocket", "pose", kind="pocket", x=980, y=430, w=560, h=360, dur=30, out="keys_in"),
    E("mol", "001", kind="molink", x=1000, y=470, dur=26, out="keys_in"),
    E("plbl", "pocket.", kind="ink", font="serif", x=980, y=760, size=40, text="pocket (predicted)", anchor="middle", dur=16, out="keys_in"),
    E("keys_in", "Sixteen", layer="3d", obj="keys", lead=30),
    E("r2", "Sixteen", lag=6, kind="ink", x=142, y=330, size=34, text="Round 2", dur=12),
    E("d16", "new", kind="ink", font="serif", x=140, y=420, size=72, text="16 designed", dur=24),
    E("keys_in_end", "designs.", layer="3d", obj="keys"),
    E("keys_out", "Six", layer="3d", obj="keys2", lead=0, dur=48),
    E("t6", "Six", lag=6, kind="ink", font="serif", x=140, y=505, size=72, text="→ 6 tested", dur=24),
    E("ul6", "tested.", kind="ul", x=140, y=505, size=72, before="→ ", key="6 tested", dur=14),
    E("slide", "tested.", lag=12, lead=60, layer="3d", obj="keys"),
    E("within", "within", kind="ink", x=142, y=580, size=32, text="within 30 days", dur=20),
    E("ul30", "30", kind="ul", x=142, y=580, size=32, before="within ", key="30 days", dur=12),
    E("first", "first", kind="ink", x=142, y=622, size=32, text="of the first hit", dur=16),
    E("hitring", "hit.", kind="ring", cx=0, cy=0, rx=46, ry=40, at_pt="key0", dur=14, fill="red"),
], source=[[0, "Illustration · 16 designed, 6 made and tested, within 30 days: Ren 2023, p. 1448", "predicted binding mode as the guide: p. 1444 · keys, tube and loop drawn"]])

# ------------------------------------------------------------------ 5-08
seg("5-08", fade_end=1060, events=[
    E("one", "one", kind="ring", cx=0, cy=0, rx=46, ry=40, at_pt="key0", dur=14, fill="red", out="k_off"),
    E("n048", "048,", kind="note", x=0, y=0, size=48, text="048", at_pt="key0", dy=-70, dur=14, out="k_off"),
    E("k_off", "048,", lag=4, kind="mark"),
    E("cam1", "fifteen", lead=133, layer="3d", obj="cam"),
    E("kd", "grabbed", kind="ink", font="serif", x=80, y=232, size=76, text="Kd = 566.7 ± 256.2 nM", dur=40, out="m2s"),
    E("lbl", "grabbed", lag=8, kind="ink", x=84, y=150, size=30, text="048 · binding to CDK20", dur=14, out="m2s"),
    E("fold", "fifteen", lag=8, kind="ink", font="serif", x=84, y=300, size=52, text="about 15× tighter than 001", dur=30, out="m2s"),
    E("tag", "times", kind="tag", x=480, y=748, leader=[[745, 600], [640, 700]], text="OUR RE-DOCKING (AutoDock Vina)", sub="not the authors' coordinates", out="m2s"),
    E("ul15", "tighter.", kind="ul", x=84, y=300, size=52, before="about ", key="15×", dur=12, out="m2s"),
    E("lys", "Then", kind="leader", pts=[[1232, 352], [1300, 250]], text="Lys33", tx=1310, ty=244, size=36, dur=20, out="m2s"),
    E("hb", "the", lag=-12, kind="note", x=1310, y=150, size=46, text="hydrogen bond", dur=24, out="m2s"),
    E("f049", "enzyme", lag=-20, kind="ink", x=84, y=900, size=28, text="049: 360.0 ± 14.1 nM — also tighter than 001; the cell test went to 048", dur=40, out="m2s"),
    E("m2s", "test.", lag=-20, kind="fade", dur=20),
    E("m2", "needed", lead=156, layer="3d", obj="cam"),
    E("test", "test.", kind="ink", font="serif", x=64, y=250, size=40, text="enzyme test (IC50)", dur=20),
    E("halves", "Remember,", kind="ink", x=64, y=294, size=30, text="the dose that halves its activity", dur=26),
    E("l001", "001", kind="ink", font="serif", x=30, y=420, size=48, text="001", dur=10),
    E("bar1", "more", lead=60, kind="bar", which=0),
    E("t001", "6,000", kind="ink", font="serif", x=100, y=490, size=58, text="> 6,000 nM", dur=20),
    E("ul001", "nanomolar.", kind="ul", x=100, y=490, size=58, before="> ", key="6,000 nM", dur=12),
    E("scale", "nanomolar.", lag=50, kind="ink", x=64, y=700, size=28, text="bars to the same scale · lower = stronger", dur=24),
    E("l048", "048", kind="ink", font="serif", x=30, y=620, size=48, text="048", dur=10),
    E("r048", after="l048", gap=45, kind="ring", cx=75, cy=604, rx=62, ry=42, dur=24, fill="red"),
    E("ul048", "needed#2", kind="ul", x=30, y=620, size=48, before="", key="048", dur=10),
    E("bar2", "just", lead=50, kind="bar", which=1),
    E("t048", "33.4.", kind="keyed", x=130, y=620, size=58, parts=["= ", "33.4", " ± 22.6 nM"], dur=30),
    E("end", "33.4.", lag=60, kind="ring", cx=0, cy=0, rx=60, ry=46, at_pt="tube", dur=16, fill="red"),
], source=[[0, "Kd, 15×, 049: Ren 2023, p. 1448 · pose and Lys33 bond: our AutoDock Vina re-docking into the AlphaFold model", "predicted · CDK20 surface shown see-through"],
           ["m2s", "Illustration · IC50: 001 > 6,000 nM, Ren 2023, p. 1447 · 048 = 33.4 ± 22.6 nM (n = 3), p. 1448", "kinase activity assay · tube and dose rule drawn"]])

# ------------------------------------------------------------------ W4（歌的拍；暂用 Sacrifice 第 52–55 小节，见 README）
seg("W4", [
    E("shell", "b2", layer="3d", obj="shell"),
    E("cam1", "b4", lead=88, layer="3d", obj="cam"),
    E("tag", "b4", lag=8, kind="tag", x=480, y=748, leader=[[745, 600], [640, 700]], text="OUR RE-DOCKING (AutoDock Vina)", sub="", out="b12f"),
    *[E(f"turn{k}", f"b{5 + k}", kind="keyturn", step=k + 1, obj="key", out="b12f") for k in range(4)],
    E("glow", "b9", kind="ring", cx=950, cy=520, rx=300, ry=200, dur=16, fill="red", out="b12f"),
    E("improve", "b11", kind="road", x=1180, y=900, dur=18, out="b12f"),
    E("b12f", "b12", lag=-16, kind="fade", dur=20),
    E("next", "b14", kind="note", x=150, y=200, size=52, text="next: living cells", dur=24),
    E("cam2", at=7.85, lead=118, layer="3d", obj="cam"),
], audio=dict(kind="MUSIC", song="Sacrifice - The Weeknd[Dawn FM].flac", start=103.27, beat=0.49178, beats=16, fade=0.25),
    source=[[0, "Illustration · our re-docking (AutoDock Vina) · music: stand-in", ""]])

# ------------------------------------------------------------------ 5-10
seg("5-10", fade_end=1725, events=[
    E("step", "step:", kind="keyed", x=120, y=170, size=72, parts=["the big step: ", "living cells", ""], dur=40),
    E("dishes", "cells.", kind="ring", cx=0, cy=0, rx=120, ry=95, at_pt="huh7_dish", dur=18),
    E("cal3", "After", kind="minical", x=1600, y=170, dur=12),
    E("p1", "three", kind="minipage", n=1),
    E("p2", "days", kind="minipage", n=2),
    E("p3", "with", kind="minipage", n=3),
    E("w048", "048,", kind="note", x=1540, y=330, size=48, text="3 days with 048", dur=24),
    E("add", "048,", lag=50, kind="leader", pts_at=["huh7_dish", "hek_dish"], tx=0, ty=0, text="", dur=20),
    E("huh7", "Huh7", kind="ink", font="serif", x=0, y=0, size=44, text="Huh7", at_pt="huh7_lbl", dur=12),
    E("liver", "cancer", kind="ink", x=0, y=0, size=28, text="liver cancer cells", at_pt="huh7_sub", dur=20),
    E("packed", "packed", kind="note", x=0, y=0, size=44, text="packed with CDK20", at_pt="huh7_note", dur=30),
    E("ulcdk", "CDK20,", kind="ul", x=0, y=0, size=44, before="packed with ", key="CDK20", font="hand", at_pt="huh7_note", dur=12),
    E("cdk_dots", "CDK20,", lag=40, kind="dots", at_pt="huh7_dish", dur=18, fill="blue"),
    E("lost", "lost", lag=8, kind="ink", x=110, y=478, size=32, text="dose of 048 →", dur=20),
    E("slide0", "lost", layer="3d", obj="slider"),
    E("half", "half", kind="note", x=110, y=540, size=46, text="half the living-cell signal gone", dur=36),
    E("sig1", "living-cell", kind="ul", x=110, y=540, size=46, before="half the ", key="living-cell", font="hand", dur=12),
    E("sig2", "signal", kind="ul", x=110, y=540, size=46, before="half the living-cell ", key="signal", font="hand", dur=12),
    E("about", "about", kind="pen", at_pt="huh7_ic", dur=10),
    E("huh7_stop", "210", layer="3d", obj="slider"),
    E("v210", "210", lag=6, kind="keyed", x=0, y=0, size=48, parts=["", "208.7", " ± 3.3 nM"], at_pt="huh7_val", dur=20),
    E("nm1", "nanomolar.", kind="ul", x=0, y=0, size=48, before="", key="208.7", at_pt="huh7_val", dur=1),
    E("cmp", "Comparison", kind="ink", font="serif", x=0, y=0, size=44, text="HEK293", at_pt="hek_lbl", dur=14),
    E("cmp2", "cells,#2", kind="ink", x=0, y=0, size=28, text="comparison cells", at_pt="hek_sub", dur=16),
    E("hek", "HEK293,", kind="ul", x=0, y=0, size=44, before="", key="HEK293", at_pt="hek_lbl", dur=12),
    E("hek2", "HEK293,", lag=8, kind="ring", cx=0, cy=0, rx=125, ry=100, at_pt="hek_dish", dur=18),
    E("hek_go", after="hek2", gap=90, kind="note", x=0, y=0, size=40, text="still going…", at_pt="hek_note", dur=20, out="hekhalf"),
    E("needed", "needed", kind="pen", at_pt="hek_ic", dur=10),
    E("hek_stop", "1,700.", layer="3d", obj="slider"),
    E("v1700", "1,700.", lag=6, kind="keyed", x=0, y=0, size=48, parts=["", "1,706.7", " ± 670.0 nM"], at_pt="hek_val", dur=20),
    E("link", after="v1700", gap=60, kind="pen", from_pt="huh7_ic", to_pt="hek_ic", dash=True, dur=24),
    E("hekhalf", after="link", gap=50, kind="note", x=0, y=0, size=40, text="half gone, at last", at_pt="hek_note2", dur=24),
    E("roughly", "Roughly", kind="bracket", at_pt="bracket", dur=20),
    E("eight", "eight", kind="note", x=0, y=0, size=52, text="~8× (our calculation)", at_pt="eight", dur=26, fill="red"),
    E("foot", "more.", kind="ink", x=120, y=930, size=26, text="HEK293 is not normal liver tissue", dur=20),
], audio=dict(pmax=0.9, pkeep=0.5),
    source=[[0, "Illustration · Huh7 208.7 ± 3.3 nM, HEK293 1,706.7 ± 670.0 nM: Ren 2023, Fig. 9B, p. 1448", "cell viability assay · dishes and cells drawn · ~8× is our calculation"]])
print("written", sorted(p.name for p in OUT.glob("*.json")))
