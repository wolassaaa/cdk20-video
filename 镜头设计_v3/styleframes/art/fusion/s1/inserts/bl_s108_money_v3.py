"""HKBU SCIE1007 课程作业的科普视频：动效升级样板 A，1-08"钱"段（审片/总管/动效升级方案_20261116 第 2.1、5.1 节；打磨清单"导演意见 11-16 钱"）。

台词（C 画外音，15.5 s）："Start the search the year we were born, and it might only be ready now. It can cost almost
2.8 billion US dollars. And of drugs tested in people, only about one in ten reaches the market."

直觉句：
- 前半句（时间）：红料沿一条很长的弯流道慢慢流，路边的小格一格格被灌满；"now" 时流到钞票格。路长 = 时间长。
- 钱：流道边三个钞票格里一张张"长"出风格化钞票（绿纸感 + "$"，没有人像、编号、真钞图案），顶针顶起，翻一下往下掉，
  在前面堆成一叠；说 cost / almost / billion / US / dollars 时各落一张，billion 时一阵落好几张；"$2.8 billion" 凸字在说到时长出。
- 1 in 10：料流到一排十个药格，十颗胶囊一颗颗长出（drugs … people）；"only about" 时九颗收回料里，"one" 时剩下那颗被顶起，
  "reaches the market" 时它跳到钱堆顶上落定。
时间全部从词级时间（粗剪/对时/beats_v8/1-08.json，没有就用 beats/1-08.json）算，60 fps，段长 = 录音长。
钞票和胶囊的掉落是逐帧关键帧（预算路径 + 离地夹角限制），不用刚体；检查见 mode=check。

用法：blender -b -P bl_s108_money_v1.py -- build            存 _work/s108_v1.blend 和事件表
      blender -b -P bl_s108_money_v1.py -- check            穿模 / 落点对词 / 1.5 s 有动作 / 悬空，写 _work/s108_check_v1.json
      blender -b -P bl_s108_money_v1.py -- render OUT [f0 f1 step samples]
"""
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mold_kit_v3 as MK  # noqa: E402

V3 = HERE.parents[4]
WORK = HERE / "_work_s108"
WORK.mkdir(exist_ok=True)
FONT = V3 / "remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"
FPS = 60
VER = "v3"


def load_words():
    for p in (V3 / "粗剪/对时/beats_v8/1-08.json", V3 / "粗剪/对时/beats/1-08.json"):
        if p.exists():
            B = json.loads(p.read_text(encoding="utf-8"))
            return B["words"], str(p)
    raise SystemExit("没有 1-08 节拍表")


WORDS, WORDS_SRC = load_words()
NF = int(round(15.498 * FPS))            # 930 帧，录音长


def wf(word, k=1):
    hits = [w for w in WORDS if w["w"].strip(",.").lower() == word.lower()]
    return int(round(hits[k - 1]["t0"] * FPS))


def wend():
    return int(round(WORDS[-1]["t1"] * FPS))


# ---------------------------------------------------------------- 布局（米）
T_BILL = 0.0025
BILL_L, BILL_W = 0.156, 0.066
CAV = {"A": (-0.19, 0.10), "B": (0.0, 0.10), "C": (0.19, 0.10)}
RUN_Y = 0.17
R_RUN, R_FLOW, Z_FLOW = 0.005, 0.0044, -0.0004
R_GATE, R_GFLOW, Z_GFLOW = 0.0022, 0.0017, -0.0003
STACK = (-0.155, -0.078)
PILL_R, PILL_H = 0.0045, 0.015
PILL_Y = -0.078
PILL_RUN_Y = -0.036
PILLS_X = [0.33 - 0.032 * k for k in range(10)]
KEEP = 6                                  # 留下的那颗（右数第 7 颗）
TEXT_C = (-0.155, -0.172)
LABEL_C = (-0.035, -0.128)

CTRL = [(-1.24, -0.02), (-0.92, -0.02), (-0.92, 0.13), (-0.80, 0.13), (-0.80, -0.13), (-0.68, -0.13), (-0.68, 0.13),
        (-0.56, 0.13), (-0.56, -0.13), (-0.44, -0.13), (-0.44, RUN_Y), (0.38, RUN_Y), (0.38, PILL_RUN_Y), (0.005, PILL_RUN_Y)]


def runner_path():
    P = MK.chaikin(CTRL, 5)
    pts, _ = MK.resample(P, 0.002)
    return [tuple(p) for p in pts]


def nearest_s(pts, xy):
    P = np.array(pts)
    d = np.hypot(P[:, 0] - xy[0], P[:, 1] - xy[1])
    i = int(d.argmin())
    return float(MK.arclen(P)[i])


# ---------------------------------------------------------------- 时间表（全部从词算）

def schedule(pts):
    S = MK.arclen(pts)
    E = []                                                     # 落点事件：id, obj, word, frame, kind
    # 钞票：格、落点（词）。每格两次之间 ≥32 帧。
    bills = [("A", "cost", None), ("B", "almost", None), ("C", None, 430), ("A", "billion", None), ("B", None, 472),
             ("C", None, 482), ("A", "US", None), ("B", None, 508), ("C", "dollars", None)]
    B = []
    for i, (cav, word, at) in enumerate(bills):
        L = wf(word) if word else at
        B.append(dict(i=i, cav=cav, word=word, land=L, grow=L - 60, eject=L - 42, fly=L - 36))
        E.append(dict(id=f"bill{i}", obj=f"bill_{i}", word=word, frame=L, kind="land"))
    # 时间段的小格：在 year / born / might / ready 时长满（grow 结束），流道前端提前 21 帧经过它的浇口
    first, gA = wf("Start"), nearest_s(pts, (CAV["A"][0], RUN_Y))
    gB, gC = nearest_s(pts, (CAV["B"][0], RUN_Y)), nearest_s(pts, (CAV["C"][0], RUN_Y))
    t_now = wf("now")
    speed = gA / (t_now - first)
    wells = []
    for k, word in enumerate(("year", "born", "might", "ready")):
        L = wf(word)
        s = speed * (L - 21 - first)
        x, y = MK.point_at(pts, s)
        i = int(np.searchsorted(S, s))
        tx, ty = pts[min(i + 1, len(pts) - 1)][0] - pts[max(i - 1, 0)][0], pts[min(i + 1, len(pts) - 1)][1] - pts[max(i - 1, 0)][1]
        n = math.hypot(tx, ty)
        nx, ny = ty / n, -tx / n                                 # 右手法线
        # 拐弯处放外侧：看前后 3 cm 的转向
        a = np.array(MK.point_at(pts, max(s - 0.03, 0))), np.array(MK.point_at(pts, s + 0.03))
        cross = (np.array([x, y]) - a[0])[0] * (a[1] - np.array([x, y]))[1] - (np.array([x, y]) - a[0])[1] * (a[1] - np.array([x, y]))[0]
        if cross > 1e-6:                                       # 左转 → 外侧在右
            side = 1
        elif cross < -1e-6:
            side = -1
        else:
            side = 1
        c = (x + side * nx * 0.036, y + side * ny * 0.036)
        wells.append(dict(k=k, word=word, land=L, grow=L - 17, gate=L - 21, s=s, root=(x, y), c=c))
        E.append(dict(id=f"well{k}", obj=f"well_{k}", word=word, frame=L, kind="grow"))
    # 流道前端：Start 进画，经过各浇口，now 到 A 格，接着 B、C，然后慢流到药排，And 时到第一颗药格
    p0 = nearest_s(pts, (PILLS_X[0], PILL_RUN_Y))
    head = [(first, 0.0), (t_now, gA), (t_now + 20, gB), (t_now + 40, gC), (wf("and", 2), p0)]
    for k in range(1, 10):
        head.append((wf("and", 2) + 12 * k, nearest_s(pts, (PILLS_X[k], PILL_RUN_Y))))
    head.append((wf("and", 2) + 12 * 9 + 10, S[-1] - 0.004))
    E.append(dict(id="head_now", obj="flow", word="now", frame=t_now, kind="head", s=gA))
    E.append(dict(id="head_and", obj="flow", word="and#2", frame=wf("and", 2), kind="head", s=p0))
    # 凸字 "$2.8 billion"：$2.8 在 "2.8" 时长满，billion 一个字母一个字母在 "billion" 这个词里长完
    letters = []
    txt = "$2.8 billion"
    f28, fb = wf("2.8"), wf("billion")
    for j, ch in enumerate(txt):
        if ch == " ":
            continue
        if j < 4:
            done = f28 - (3 - j) * 3
        else:
            done = fb + 4 * (j - 5)
        letters.append(dict(j=j, ch=ch, done=done))
    E.append(dict(id="text_28", obj="letter_3", word="2.8", frame=f28, kind="grow"))
    # 药：drugs 起每 7 帧长满一颗；only 起九颗依次收回（每 6 帧一颗）；one 时留下那颗被顶到位；reaches 起跳，market 落定
    pills = []
    fd = wf("drugs")
    order = [k for k in range(10) if k != KEEP]
    f_only, f_one = wf("only", 2), wf("one")
    ends = []
    e = f_only + 10
    for _ in order:
        while abs(e - f_one) < 6:
            e += 1
        ends.append(e)
        e += 6
    for k in range(10):
        p = dict(k=k, grow=fd + 12 * k - 16, land=fd + 12 * k)
        if k != KEEP:
            p["retract_end"] = ends[order.index(k)]
            p["retract"] = p["retract_end"] - 14
        pills.append(p)
        E.append(dict(id=f"pill{k}", obj=f"pill_{k}", word="drugs" if k == 0 else None, frame=p["land"], kind="grow"))
        if k != KEEP:
            E.append(dict(id=f"pillx{k}", obj=f"pill_{k}", word="only#2" if order.index(k) == 0 else None, frame=p["retract"] + 4, kind="start"))
    keep = dict(lift=f_one - 6, lifted=f_one, hop=wf("reaches"), land=wf("market"), settle=min(wend() - 3, wf("market") + 26))
    E.append(dict(id="keep_up", obj=f"pill_{KEEP}", word="one", frame=f_one, kind="lift", z=-(PILL_R + 0.0005) - 0.00008 + 0.016 + PILL_R + 0.0004))
    E.append(dict(id="keep_hop", obj=f"pill_{KEEP}", word="reaches", frame=keep["hop"], kind="start"))
    E.append(dict(id="keep_land", obj=f"pill_{KEEP}", word="market", frame=keep["land"], kind="land"))
    return dict(bills=B, wells=wells, head=head, letters=letters, pills=pills, keep=keep, events=E, speed=speed)


# ---------------------------------------------------------------- 搭场景

def build():
    sc = MK.reset_scene()
    MK.render_setup(sc)
    sc.frame_start, sc.frame_end = 0, NF - 1
    MK.world(sc, 0.10)
    M = MK.materials()
    font = bpy.data.fonts.load(str(FONT))
    pts = runner_path()
    T = schedule(pts)
    random.seed(108)

    # 底模
    plate = MK.Plate(-1.30, 0.50, -0.25, 0.26, res=0.0008)
    plate.runner(pts, R_RUN)
    gates = []
    for c, (cx, cy) in CAV.items():
        g = [(cx, RUN_Y), (cx, cy + BILL_W / 2 + 0.0015)]
        plate.runner(g, R_GATE)
        gates.append((c, g))
        plate.pocket_rrect((cx, cy), BILL_L / 2 + 0.0006, BILL_W / 2 + 0.0006, 0.0056, T_BILL)
        plate.pin_hole((cx, cy), 0.003, 0.06)
    for w in T["wells"]:
        g = [w["root"], (w["root"][0] + (w["c"][0] - w["root"][0]) * 0.62, w["root"][1] + (w["c"][1] - w["root"][1]) * 0.62)]
        plate.runner(g, R_GATE)
        w["gate_pts"] = g
        plate.pocket_rrect(w["c"], 0.0162, 0.0162, 0.0161, 0.0025)
    for k, x in enumerate(PILLS_X):
        a, b = (x, PILL_Y - PILL_H / 2), (x, PILL_Y + PILL_H / 2)
        plate.pocket_capsule(a, b, PILL_R + 0.0005)
        plate.runner([(x, PILL_RUN_Y), (x, PILL_Y + PILL_H / 2 + PILL_R + 0.0012)], R_GATE)
    plate.pin_hole((PILLS_X[KEEP], PILL_Y), 0.0024, 0.04)
    # 外圈 3 cm 斜到 −0.3 mm，接一张大底板（同材质），看不到边
    X, Y = plate.X, plate.Y
    e = np.minimum.reduce([X - X.min(), X.max() - X, Y - Y.min(), Y.max() - Y])
    k = np.clip(e / 0.03, 0, 1)
    plate.Z = plate.Z * k + (-0.0003) * (1 - k)
    po = plate.build(M["bone"])
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.00035))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.data.materials.append(M["bone"])

    # 流
    tube, head = MK.flow_tube("flow", pts, R_FLOW, Z_FLOW, M["red"])
    MK.flow_keys(tube, head, T["head"], 0, NF - 1)
    head_hide = T["head"][-1][0] + 1
    MK.vis(head, T["head"][0][0], head_hide)                    # 料走到底，圆头并进料管
    S = MK.arclen(pts)

    def head_frame(s):
        for (fa, sa), (fb, sb) in zip(T["head"], T["head"][1:]):
            if sa <= s <= sb:
                return fa + (fb - fa) * (s - sa) / max(sb - sa, 1e-9)
        return T["head"][-1][0]

    # 时间小格
    disc_me = MK.slab("disc", [(0.0154 * math.cos(a), 0.0154 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)], 0, 0.006, 0.0012)
    for w in T["wells"]:
        gt, _ = MK.flow_tube(f"wgate_{w['k']}", w["gate_pts"] + [w["c"]], R_GFLOW, Z_GFLOW, M["red"], head=False)
        MK.gate_fill(gt, w["gate"])
        o = MK.new_obj(f"well_{w['k']}", disc_me.copy(), [M["red"]])
        o.location = (w["c"][0], w["c"][1], -0.0025 + 0.00012)
        d = Vector((w["root"][0] - w["c"][0], w["root"][1] - w["c"][1], 0)).normalized() * 0.0154
        MK.grow_keys(o, (d.x, d.y, 0))
        MK.grow(o, w["grow"], fill=5, bulge=12)
        o["kind"] = "part"

    # 钞票格的浇口料管（一次灌满，之后一直是满的）
    for c, g in gates:
        gt, _ = MK.flow_tube(f"gate_{c}", g, R_GFLOW, Z_GFLOW, M["red"], head=False)
        first_bill = min(b["grow"] for b in T["bills"] if b["cav"] == c)
        MK.gate_fill(gt, int(head_frame(nearest_s(pts, (CAV[c][0], RUN_Y)))) + 2)

    # 顶针
    pins = {}
    for c, (cx, cy) in CAV.items():
        p = MK.pin_obj(f"pin_{c}", 0.0016, 0.03, M["chrome"])
        p.location = (cx, cy, -T_BILL - 0.00008)
        pins[c] = p
    kx = PILLS_X[KEEP]
    kpin = MK.pin_obj("pin_pill", 0.0016, 0.03, M["chrome"])
    kpin.location = (kx, PILL_Y, -(PILL_R + 0.0005) - 0.00008)

    # 钞票
    bill_me, BI = MK.bill_mesh("bill", font, BILL_L, BILL_W, T_BILL)
    BI["top"] = max(v.co.z for v in bill_me.vertices)
    pitch = BI["top"] + 0.00025
    zbase = float(max(plate.height(STACK[0] + dx, STACK[1] + dy) for dx in np.linspace(-0.09, 0.09, 19) for dy in np.linspace(-0.045, 0.045, 9))) + 0.0001
    stack = []
    pin_frames = {c: [] for c in CAV}
    for b in T["bills"]:
        cx, cy = CAV[b["cav"]]
        o = MK.new_obj(f"bill_{b['i']}", bill_me.copy(), [M["bill"], M["bill_ink"]])
        o["kind"] = "part"
        rest = Matrix.Translation((cx, cy, -T_BILL + 0.00015))
        MK.grow_keys(o, BI["gate"])
        done = MK.grow(o, b["grow"], fill=5, bulge=12)
        yaw = math.radians(random.uniform(-11, 11))
        off = (random.uniform(-0.005, 0.005), random.uniform(-0.004, 0.004))
        top = zbase + pitch * len(stack)
        tgt = Matrix.Translation((STACK[0] + off[0], STACK[1] + off[1], top)) @ Matrix.Rotation(yaw, 4, "Z")
        stack.append(dict(M=tgt, top=top + pitch, land=b["land"]))
        poses = {f: rest for f in range(b["grow"], b["eject"] + 1)}
        up = 0.012
        for kf in range(1, 7):
            poses[b["eject"] + kf] = Matrix.Translation((0, 0, up * MK.ease_in(kf / 6, 2))) @ rest
        pin_frames[b["cav"]].append(b["eject"])
        start = poses[b["fly"]]
        poses.update(flight(start, tgt, b["fly"], b["land"], BI, top, i=b["i"], apex={"A": 0.075, "B": 0.125, "C": 0.10}[b["cav"]]))
        for f in range(b["land"], NF):
            poses[f] = tgt
        if b["i"] >= 7:                                            # dollars 落完到 And 之间：顶上两张错开 5 mm 再归位
            for f in range(522, 561):
                u = (f - 522) / 38
                dx = 0.005 * math.sin(math.pi * MK.ease_in_out(u))
                poses[f] = Matrix.Translation((dx, 0.0015 * math.sin(math.pi * u), 0)) @ tgt
        MK.bake_pose(o, poses)
        b["tgt"], b["top"] = tgt, top
    for c, fs in pin_frames.items():
        base = pins[c].location.copy()
        for f in fs:
            MK.pin_stroke(pins[c], base, f, up=0.012, rise=6, hold=0, fall=10)

    # 凸字 "$2.8 billion"（Instrument Serif，红料，凸 1.6 mm，从台面长起来）
    txt = "$2.8 billion"
    size = 0.036
    full = MK.text_mesh(txt, font, size, 0.0016, name="probe")
    fw = max(v.co.x for v in full.vertices) - min(v.co.x for v in full.vertices) + 0.0012 * (len(txt) - 1)
    x0 = TEXT_C[0] - fw / 2
    for L in T["letters"]:
        j, ch = L["j"], L["ch"]
        pre = MK.text_mesh(txt[:j + 1], font, size, 0.0016, name="pre")
        right = max(v.co.x for v in pre.vertices) - min(v.co.x for v in pre.vertices)
        cme = MK.text_mesh(ch, font, size, 0.0016, name=f"ch{j}")
        cw = max(v.co.x for v in cme.vertices) - min(v.co.x for v in cme.vertices)
        zmin = min(v.co.z for v in cme.vertices)
        o = MK.new_obj(f"letter_{j}", cme, [M["red"]])
        o["kind"] = "part"
        cx = x0 + right - cw / 2 + 0.0012 * j
        zb = float(max(plate.height(cx + dx, TEXT_C[1] + dy) for dx in np.linspace(-cw / 2, cw / 2, 5) for dy in np.linspace(-0.015, 0.015, 7))) + 0.0001
        o.location = (cx, TEXT_C[1], zb - zmin)
        MK.grow_keys(o, (0, 0, 0), film=0.06, seed=1.0)
        MK.grow(o, L["done"] - 14, fill=3, bulge=11)

    # 药（胶囊）
    cap_me, CI = MK.capsule_mesh("capsule", PILL_R, PILL_H)
    Rt = PILL_R + 0.0005

    def trough(x, y):
        d = math.hypot(x, max(abs(y) - PILL_H / 2, 0))
        return -math.sqrt(max(Rt * Rt - d * d, 0))

    order9 = [k for k in range(10) if k != KEEP]
    for p in T["pills"]:
        x = PILLS_X[p["k"]]
        o = MK.new_obj(f"pill_{p['k']}", cap_me.copy(), [M["red"], M["part_bone"]])
        o["kind"] = "part"
        o.location = (x, PILL_Y, 0.0)
        MK.grow_keys(o, CI["gate"], floor_fn=trough)
        MK.grow(o, p["grow"], fill=5, bulge=11)
        gt, _ = MK.flow_tube(f"pgate_{p['k']}", [(x, PILL_RUN_Y), (x, PILL_Y + PILL_H / 2 + PILL_R + 0.0012)], R_GFLOW, Z_GFLOW, M["red"], head=False)
        MK.gate_fill(gt, p["grow"] - 4)
        if "retract" in p:
            MK.retract(o, p["retract"], soft=4, shrink=10)
            # market 落定后，空药格的浇口料退回主沟（收），一直动到话说完
            f0 = wf("market") + 2 + 3 * order9.index(p["k"])
            for f, v in ((f0, 1.0),) + tuple((f0 + kk, 1 - MK.ease_in_out(kk / 14)) for kk in range(1, 15)):
                gt.data.bevel_factor_end = v
                gt.data.keyframe_insert("bevel_factor_end", frame=f)
        else:
            K = T["keep"]
            base = kpin.location.copy()
            up = 0.016
            # 顶针：one 前 6 帧顶起 up，之后到 reaches 再慢慢多顶 4 mm（话没说完不停），跳走后 10 帧退回
            hop = K["hop"]
            def pin_z(f):
                if f <= K["lift"]:
                    return base.z
                if f <= K["lifted"]:
                    return base.z + up * MK.ease_in((f - K["lift"]) / 6, 2)
                if f <= hop:
                    return base.z + up + 0.004 * MK.ease_in_out((f - K["lifted"]) / (hop - K["lifted"]))
                return base.z + (up + 0.004) * (1 - MK.ease_in_out((f - hop) / 10))
            for f in range(K["lift"], hop + 11):
                kpin.location = (base.x, base.y, pin_z(f))
                kpin.keyframe_insert("location", frame=f)
            rest = Matrix.Translation((x, PILL_Y, 0.0))
            poses = {f: rest for f in range(p["grow"], K["lift"] + 1)}
            for f in range(K["lift"] + 1, hop + 1):
                poses[f] = Matrix.Translation((x, PILL_Y, max(0.0, pin_z(f) + PILL_R + 0.0004)))
            top_bill = T["bills"][-1]
            loc_local = Vector((0.045, 0.0, BI["top"] + 0.00015 + PILL_R))
            end = top_bill["tgt"] @ Matrix.Translation(loc_local)
            poses.update(flight(poses[hop], end, hop, K["land"], dict(L=2 * PILL_R, W=PILL_H + 2 * PILL_R, top=2 * PILL_R, pill=True),
                                top_bill["top"], i=99, apex=0.07, flips=1.0, start_floor=pin_z(hop) + 0.0012))
            for f in range(K["land"], NF):
                poses[f] = end
            MK.bake_pose(o, poses)
            MK.vis(o, p["grow"])

    # "1 in 10" 凸字：market 落定后一个字一个字长出来，长到话说完
    lab = "1 in 10"
    fm = wf("one")
    xs = 0.0
    for j, ch in enumerate(lab):
        if ch == " ":
            xs += 0.008
            continue
        cme = MK.text_mesh(ch, font, 0.026, 0.0014, name=f"lab{j}")
        cw = max(v.co.x for v in cme.vertices) - min(v.co.x for v in cme.vertices)
        zmin = min(v.co.z for v in cme.vertices)
        o = MK.new_obj(f"label_{j}", cme, [M["red"]])
        o["kind"] = "part"
        cx = LABEL_C[0] + xs + cw / 2
        zb = float(max(plate.height(cx + dx, LABEL_C[1] + dy) for dx in np.linspace(-cw / 2, cw / 2, 5) for dy in np.linspace(-0.011, 0.011, 7))) + 0.0001
        o.location = (cx, LABEL_C[1], zb - zmin)
        xs += cw + 0.003
        MK.grow_keys(o, (0, 0, 0), film=0.06, seed=1.0)
        MK.grow(o, fm + 4 * j, fill=3, bulge=11)

    # 灯和机位
    MK.lights(target=(0.25, 0.0, 0.0), size=3.2, key=58.0, fill=12.0)
    cam = MK.camera(lens=50.0, fstop=4.0)
    head_x = []
    for f in range(NF):
        sx = None
        for (fa, sa), (fb, sb) in zip(T["head"], T["head"][1:]):
            if fa <= f <= fb:
                sx = sa + (sb - sa) * (f - fa) / max(fb - fa, 1e-9)
        if sx is None:
            sx = T["head"][0][1] if f < T["head"][0][0] else T["head"][-1][1]
        head_x.append(MK.point_at(pts, sx)[0])
    head_x = np.convolve(np.array(head_x), np.ones(25) / 25, mode="same")
    t_now = wf("now")
    for f in range(NF):
        follow = min(max(head_x[f] + 0.12, -0.95), 0.035)        # 机位跟料头走（领先 12 cm），到 now 停在格子区
        u = MK.ease_in_out((f - (wf("ready") + 1)) / 30)          # ready 圆饼鼓完（261）才起步，30 帧到格子区
        tx = follow * (1 - u) + 0.035 * u
        if f > 560:
            tx = 0.035 + 0.01 * MK.ease_in_out((f - 560) / 60)
        tgt = Vector((tx, 0.0, 0.0))
        dist = 1.02 + 0.1 * (1 - u)
        u = MK.ease_in_out((f - 846) / 80)
        tgt = tgt.lerp(Vector((STACK[0] + 0.03, STACK[1] + 0.005, 0.02)), u)
        dist = dist + (0.62 - dist) * u
        MK.cam_key(cam, f, tgt, dist, pitch_deg=54.0 + 4.0 * u)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    T["stack"] = [dict(top=s["top"], land=s["land"]) for s in stack]
    T["zbase"], T["pitch"] = zbase, pitch
    return sc, T


def flight(start, tgt, f0, f1, BI, top, i=0, apex=0.10, flips=1.0, long_axis="X", start_floor=None):
    """脱→掉：从顶起位置沿三次贝塞尔飞到落点；中途绕长轴翻 flips 圈、轻摆，越靠近下面的东西摆得越小（离地夹角限制），
    最后 4 帧放平；落点帧 = f1（ease-out，像纸一样飘下来）。返回 {帧: Matrix}。"""
    p0, p3 = start.to_translation(), tgt.to_translation()
    q0, q3 = start.to_quaternion(), tgt.to_quaternion()
    side = Vector((0.025 * math.sin(i * 1.7), 0.02 * math.cos(i * 2.3), 0))
    p1 = p0 + Vector((0, 0, apex * 0.9))
    p2 = p3 + Vector((0, 0, apex)) + side
    L, W = BI["L"], BI["W"]
    hl, hw = L / 2, W / 2
    n = f1 - f0
    out = {}
    stack_xy = Vector((STACK[0], STACK[1], 0))
    for k in range(n + 1):
        t = k / n
        u = t * t * (3 - 2 * t) * 0.35 + (1 - (1 - t) ** 2.2) * 0.65
        pos = MK.bezier(p0, p1, p2, p3, u)
        flip = 2 * math.pi * flips * MK.ease_in_out((t - 0.12) / 0.5)
        rock = 0.22 * math.sin(2 * math.pi * 2.2 * t + i) * (1 - t) ** 1.2
        yaw_q = q0.slerp(q3, MK.ease_in_out(t))
        near = (Vector((pos.x, pos.y, 0)) - stack_xy).length < 0.13
        support = (top if near else 0.0) + 0.0055
        if start_floor is not None and (Vector((pos.x, pos.y, 0)) - Vector((p0.x, p0.y, 0))).length < 0.03:
            support = max(support, start_floor)
        hz = BI["top"]
        zs = (0, hz) if not BI.get("pill") else (-hz / 2, hz / 2)
        scale, q = 1.0, yaw_q
        for _ in range(16):
            dev = (flip * scale + math.pi) % (2 * math.pi) - math.pi
            rq = Quaternion((1, 0, 0), dev) @ Quaternion((0, 1, 0), rock * scale)
            q = yaw_q @ rq
            R = q.to_matrix()
            low = min((R @ Vector((sx * hl, sy * hw, sz))).z for sx in (-1, 1) for sy in (-1, 1) for sz in zs) + pos.z
            if low >= support:
                break
            scale *= 0.7
        else:
            q = yaw_q
        if t > 0.94:
            q = yaw_q
        out[f0 + k] = Matrix.Translation(pos) @ q.to_matrix().to_4x4()
    out[f1] = tgt
    return out


# ---------------------------------------------------------------- 检查

def eval_tris(o, dg):
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    mw = oe.matrix_world
    V = [mw @ v.co for v in me.vertices]
    me.calc_loop_triangles()
    F = [tuple(t.vertices) for t in me.loop_triangles]
    oe.to_mesh_clear()
    return V, F


def check(T):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    plate = bpy.data.objects["mold_plate"]
    sc.frame_set(0)
    PV, PF = eval_tris(plate, dg)
    PB = BVHTree.FromPolygons(PV, PF)
    solids = [o for o in sc.objects if o.get("kind") == "part" or o.name.startswith("pin_")]
    flows = [o for o in sc.objects if o.name.startswith(("flow", "gate_", "wgate_", "pgate_"))]
    clashes, sig_prev, moving = [], {}, []
    hover = []
    rest_since = {}
    for f in range(NF):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        vis_ = [o for o in solids + flows if not o.hide_render]
        geo = {}
        for o in vis_:
            V, F = eval_tris(o, dg)
            if not F:
                continue
            geo[o.name] = (V, F, BVHTree.FromPolygons(V, F), np.array(V).min(0), np.array(V).max(0))
        # 穿模：件-件、件-底模、料-底模（料和件同一种熔料，相接处不算）
        names = list(geo)
        for a_i, a in enumerate(names):
            Va, Fa, Ba, lo_a, hi_a = geo[a]
            is_flow_a = bpy.data.objects[a] in flows
            if Ba.overlap(PB):
                clashes.append((f, a, "mold_plate"))
            if is_flow_a:
                continue
            for b in names[a_i + 1:]:
                if bpy.data.objects[b] in flows:
                    continue
                Vb, Fb, Bb, lo_b, hi_b = geo[b]
                if (lo_a > hi_b + 1e-4).any() or (lo_b > hi_a + 1e-4).any():
                    continue
                if Ba.overlap(Bb):
                    clashes.append((f, a, b))
        # 动作
        sig = {}
        for n_, (V, F, _, lo, hi) in geo.items():
            sig[n_] = np.concatenate([lo, hi, np.array(V[:: max(1, len(V) // 40)]).ravel()[:120]])
        mv = []
        for n_, s in sig.items():
            p = sig_prev.get(n_)
            if p is None or p.shape != s.shape or np.abs(p - s).max() > 2e-5:
                mv.append(n_)
                rest_since[n_] = f
        moving.append(mv)
        sig_prev = sig
        # 悬空：静止 ≥5 帧的件，最低几个点往下打射线，2 mm 内要碰到底模或别的件
        if f % 6 == 0:
            for n_, (V, F, B_, lo, hi) in geo.items():
                o = bpy.data.objects[n_]
                if o.get("kind") != "part" or f - rest_since.get(n_, f) < 5:
                    continue
                lo_l = Vector(o.bound_box[0]); hi_l = Vector(o.bound_box[6])
                best = 1.0
                mw = o.matrix_world
                for ux in np.linspace(0.25, 0.75, 5):
                    for uy in np.linspace(0.25, 0.75, 5):
                        pl = Vector((lo_l.x + (hi_l.x - lo_l.x) * ux, lo_l.y + (hi_l.y - lo_l.y) * uy, hi_l.z + 0.001))
                        pw = mw @ pl
                        own = B_.ray_cast(pw, Vector((0, 0, -1)), 0.1)
                        if own[0] is None:
                            continue
                        # 自己的最低面
                        q = own[0]
                        while True:
                            nxt = B_.ray_cast(q - Vector((0, 0, 1e-6)), Vector((0, 0, -1)), 0.1)
                            if nxt[0] is None:
                                break
                            q = nxt[0]
                        q = q - Vector((0, 0, 1e-6))
                        for tree in [PB] + [geo[m][2] for m in geo if m != n_ and bpy.data.objects[m].get("kind") == "part"]:
                            hit = tree.ray_cast(q, Vector((0, 0, -1)), 0.01)
                            if hit[0] is not None:
                                best = min(best, hit[3])
                if best > 0.0015:
                    hover.append((f, n_, round(best * 1000, 2)))
    # 落点对词
    land = []
    for e in T["events"]:
        if not e.get("word"):
            continue
        base, _, kk = e["word"].partition("#")
        wfr = wf(base, int(kk or 1))
        meas = measure(e, moving, T)
        land.append(dict(id=e["id"], word=e["word"], word_frame=wfr, measured=meas, diff=None if meas is None else meas - wfr))
    # 1.5 s 窗口
    f_first = int(round(WORDS[0]["t0"] * FPS))
    still, run, worst = [], 0, 0
    for f in range(f_first, wend() + 1):
        run = 0 if moving[f] else run + 1
        worst = max(worst, run)
    still_runs = []
    run = 0
    for f in range(NF):
        if moving[f]:
            if run >= 30:
                still_runs.append((f - run, f - 1))
            run = 0
        else:
            run += 1
    res = dict(
        version=VER, words=WORDS_SRC, frames=NF,
        clash_frames=sorted(set(c[0] for c in clashes)), clash_pairs=sorted(set((c[1], c[2]) for c in clashes)), clash_n=len(clashes),
        landing=land, landing_max_abs=max(abs(x["diff"]) for x in land if x["diff"] is not None),
        longest_still_frames=worst, still_runs_ge_30=still_runs, last_word_end=wend(),
        last_motion=max(f for f in range(NF) if moving[f]),
        hover=hover[:50], hover_n=len(hover),
    )
    res["pass"] = dict(clash=res["clash_n"] == 0, landing=res["landing_max_abs"] <= 3 and all(x["measured"] is not None for x in land),
                       motion=worst < 90 and res["last_motion"] >= wend() - 3, hover=res["hover_n"] == 0)
    (WORK / f"s108_check_{VER}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("CHECK", json.dumps(res["pass"]), "clash", res["clash_n"], res["clash_pairs"][:8], "land", res["landing_max_abs"], "still", worst, "hover", res["hover_n"], hover[:5])


def measure(e, moving, T):
    """从烘好的数据量落点：land = 物体最后一次停下（之后 ≥4 帧不动）；grow = 长完；retract = 消失；head = 圆头到位置。"""
    name = e["obj"]
    f_ref = e["frame"]
    if e["kind"] == "head":
        tube = bpy.data.objects["flow"]
        pts = [tuple(p) for p in tube["pts"]]
        total = MK.arclen(pts)[-1]
        for f in range(max(0, f_ref - 30), min(NF, f_ref + 30)):
            bpy.context.scene.frame_set(f)
            if tube.data.bevel_factor_end * total >= e["s"] - 0.001:
                return f
        return None
    if e["kind"] == "lift":
        o = bpy.data.objects[name]
        for f in range(max(0, f_ref - 30), min(NF, f_ref + 30)):
            bpy.context.scene.frame_set(f)
            if o.matrix_world.translation.z >= e["z"] - 0.0002:
                return f
        return None
    if e["kind"] == "retract":
        o = bpy.data.objects[name]
        for f in range(max(0, f_ref - 30), min(NF, f_ref + 30)):
            bpy.context.scene.frame_set(f)
            if o.hide_render:
                return f - 1
        return None
    if e["kind"] == "start":
        for f in range(max(1, f_ref - 20), min(NF, f_ref + 20)):
            if name in moving[f] and name not in moving[f - 1]:
                return f - 1
        return None
    # land / grow / lift：f_ref 附近，name 在 f 还动、f+1..f+4 都不动 → f 是停下那帧
    best = None
    for f in range(max(1, f_ref - 20), min(NF - 4, f_ref + 20)):
        if name in moving[f] and all(name not in moving[g] for g in range(f + 1, f + 4)):
            if best is None or abs(f - f_ref) < abs(best - f_ref):
                best = f
    return best


# ---------------------------------------------------------------- 入口

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["build"]
    mode = argv[0]
    sc, T = build()
    ev = dict(words=WORDS_SRC, frames=NF, events=T["events"], bills=[{k: v for k, v in b.items() if k not in ("tgt",)} for b in T["bills"]],
              pills=T["pills"], keep=T["keep"], head=T["head"], letters=T["letters"],
              wells=[{k: v for k, v in w.items() if k != "gate_pts"} for w in T["wells"]])
    (WORK / f"s108_events_{VER}.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if mode == "build":
        bpy.ops.wm.save_as_mainfile(filepath=str(WORK / f"s108_{VER}.blend"))
        print("BUILD_OK")
    elif mode == "check":
        check(T)
    elif mode == "render":
        out = argv[1]
        f0, f1 = int(argv[2]) if len(argv) > 2 else 0, int(argv[3]) if len(argv) > 3 else NF - 1
        step = int(argv[4]) if len(argv) > 4 else 1
        if len(argv) > 5:
            sc.cycles.samples = int(argv[5])
        if len(argv) > 6:
            sc.render.resolution_percentage = int(argv[6])
        os.makedirs(out, exist_ok=True)
        for f in range(f0, f1 + 1, step):
            p = os.path.join(out, f"s108_{f:04d}.png")
            if os.path.exists(p):
                continue
            sc.frame_set(f)
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
        print("RENDER_OK")


main()
