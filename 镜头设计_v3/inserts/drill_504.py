"""HKBU SCIE1007 课程作业的科普视频：第二段三维钻取 5-04 —— CDK20 插座 + 十台小插座（设计：深化/06_插座比喻.md 第四节 5-04，11-20）。

"But then came a second test. Because grabbing a lock isn't the same as jamming it. Does 001 actually stop CDK20 from working?
That's measured as IC50: how much you need to cut the enzyme's activity in half. For 001? Above 6,000 nanomolar. Weak."

一镜到底（引擎 shot_drill.py，帧号全部来自 映射/keys/5-04.json）：
  T5   段首：5-03 飞来的 001 假插头从镜头前掠过，完全虚化，停到浮着的插座右前方。
  开   "second test" 盖翻开，ATP 插着、灯亮，光包流到活塞，活塞推小细胞。
  顶替 "Because grabbing" ATP 被顶出让到左前方，001 摆到孔轴上插到底（缝比 048 宽，在孔里晃）。
  钻   "a lock" 镜头从机舱上方钻到触点块，叠化到我们自己重新对接的 001 姿态（OUR RE-DOCKING，AutoDock Vina），再退回。
  拧   "jamming" 001 想拧卡口，只拧 12° 就卡住、抖一下、被弹回；卡扣不扣，灯一直亮。
  照干 "stop CDK20 from working" 三下活塞照推，细胞照鼓。
  量   "measured" 弹簧把 001 顶出来，盖合上，镜头平移到右边的料架：十台小插座（都插着 ATP、灯亮）和刻着 IC50 的剂量旋钮。
       旋钮往上拧，001 一把把插进小插座；扣上的灯灭，松着的照亮；拧过 6,000 的红刻线时只灭了 4 台，到头还有 6 台亮着。
  T5出 "Weak." 插座（盖合着）从画面左边冲进镜头，孔口面盖满画面，接出镜 5-05+06（位姿写 handoff_tail.json）。
不穿模靠两件事：路径按零件几何设计（插头只沿孔轴进出、横移前先退到针尖离开面板、两插头错开），渲染前 clip 逐帧 BVH 查。
"""
import json
import os
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_drill as SD  # noqa: E402
from shot_drill import MM, clamp, smooth, smoother, ease_out, ease_in, spring, ramp, lerp, settle  # noqa: E402

SEG = "5-04"
BOARD = SD.WORK_ROOT / "kit" / "board_final.blend"
STRUCT = SD.WORK_ROOT / "structures" / "AF-Q8IZL9-F1-model_v6.pdb"
SURF = SD.WORK_ROOT / "kit" / "cdk20.npz"
DOCK = SD.ROOT / "镜头设计_v2" / "tests" / "T6_molecules"          # 我们自己做的 Vina 重新对接（5-03 起片里已用），不重算
S = 0.7
BC = (-7.7, -0.2, -3.95)
H_FLOAT = 30.0
FACE = (-0.10, -1.0, 0.21)
H_ATP = (24.0, -40.0, -8.0)                          # ATP 被顶出后的待机位（3-04 验过不穿模）
H001 = (44.0, 26.0, 6.0)                             # 001 段首落下的待机位（插座右前方）
H001_OUT = (36.0, 30.0, 6.0)                         # 001 被顶出后的待机位（针尖 W≥20，离开面板和卡扣）
LID_OPEN = 104.0
FSTOP = dict(front=6.0, cabin=7.0, drill=14.0, rack=8.0)
R_POCKET = 12.0
POCKET_HL_R = 9.0
REAL_PULL_K = 0.40                                   # 真实层停留时镜头往后拉多少（0.75 时 3 秒后配体只剩几十像素，11-21 改小）                                    # 真实层口袋染色的半径（Å，以 cdk20.npz 的口袋中心为圆心）
ALIGN = (-1.5, 0.0, 5.4, 5.5)                        # 钻的对位圈：触点块顶面（局部 W, U, Z, 半径 mm）—— 001 的针插在这块里
RACK_AT = (6.0, 125.0, 8.0)                          # 料架原点（十台小插座的中心）相对浮着的插座：局部方向，世界毫米
MINI_U = [-42.0, -21.0, 0.0, 21.0, 42.0]
ROW_Z = [8.0, -12.0]
DIAL = (-1.6, -78.0, 0.0)                            # 剂量旋钮盘心（料架局部 mm）
DIAL_R = 16.0
MINI_EV = {"m1": 0, "m2": 1, "m3": 2, "m4": 3, "m5": 5, "m6": 6}
CLAMPED = {"m1", "m3", "m5", "m6"}                   # 扣上、灯灭的 4 台；m2、m4 松着
LIGAND = DOCK / "dock_001.sdf"


def dial_angle(v):
    """表针角（度，料架 U-Z 平面，0 = +U）：v=0 在左下 225°，v=1 在右下 −45°。"""
    return 225.0 - 270.0 * v


# ================================================================ 时间表
class T:
    def __init__(self, EV):
        self.EV = EV
        g = lambda i, k="f_land": EV[i][k]  # noqa: E731
        tri = lambda i: (g(i, "f_start"), g(i), g(i, "f_end"))  # noqa: E731
        self.wipe = (g("wipe", "f_start"), g("wipe"))
        self.hover = tri("key_hover")
        self.prep = (g("lid_prep", "f_start"), g("lid_prep"))
        self.open1 = tri("lid_open")
        self.cabin = g("cam_cabin")
        self.swap = tri("atp_eject")
        self.p001 = tri("plug001_in")
        self.lock = tri("cam_lock")
        self.twist_view = g("cam_twist")
        self.drill = tri("drill_in")
        self.real_in = (g("real_in"), g("real_in", "f_end"))
        self.real_out = (g("real_out"), g("real_out", "f_end"))
        self.drill_out = (g("drill_out", "f_start"), g("drill_out"))
        self.twist = tri("twist_try")
        self.name = tri("name001")
        self.pushes = [g("push_stop"), g("push_cdk"), g("push_working")]
        self.out = tri("p001_out")
        self.close = (self.out[1] + 24, self.out[1] + 56, self.out[1] + 68)
        self.rack = (g("cam_rack", "f_start"), g("cam_rack"))
        self.ic50 = tri("ic50_glow")
        self.tick = g("knob_tick", "f_start")
        self.turn = (g("knob_turn", "f_start"), g("knob_turn"), g("knob_turn", "f_end"))
        self.half = tri("half_mark")
        self.m_in = {k: tri(k + "_in") for k in MINI_EV}
        self.m_off = {k: tri(k + "_off") for k in CLAMPED}
        self.cross = g("m5_off")                                          # 表针过 6,000 红刻线
        self.stop = g("needle_stop")
        self.rush = (g("tail_rush", "f_start"), g("tail_rush"))
        self.hide_hero_plugs = self.rack[1] + 20


# ================================================================ 机构的状态（纯函数：帧 → 数值）
def lid_angle(t, f):
    a, b, c = t.open1
    if f < a:
        return 0.0
    if f < t.close[0]:
        u = (f - a) / (b - a)
        if f <= b:
            v = LID_OPEN * spring(u * 1.05, zeta=0.62, freq=0.62) if u < 1 else LID_OPEN
        else:
            v = LID_OPEN + settle(f, b, 3.0, n=1.0, dur=c - b + 8)
        return min(109.5, max(0.0, v))
    if f <= t.close[1]:
        u = (f - t.close[0]) / (t.close[1] - t.close[0])
        return LID_OPEN * (1 - ease_in(u, 2.4))
    return max(0.0, abs(settle(f, t.close[1], 3.2, n=1.0, dur=t.close[2] - t.close[1] + 4)))


def dial_value(t, f):
    """剂量旋钮 0–1：how 前一拍往回顶一下，之后一路往上拧，6,000 时到 0.75，nanomolar 顶到头，顶着抖。"""
    a0, a1 = t.turn[0], t.cross
    if f < t.tick:
        return 0.0
    if f < a0:
        return -0.011 * math.sin(math.pi * (f - t.tick) / max(1, a0 - t.tick))
    if f < a1:
        u = (f - a0) / (a1 - a0)
        w = 0.06                                                          # 起步 6% 的路用缓入，之后匀速（像手一直在拧）
        return 0.75 * (u * u / (2 * w) / (1 - w / 2) if u < w else (u - w / 2) / (1 - w / 2))
    if f < t.stop:
        u = (f - a1) / (t.stop - a1)
        return 0.75 + 0.25 * (u ** 1.25)
    return 1.0 - 0.010 * abs(math.sin(math.pi * (f - t.stop) / 3.0)) * math.exp(-(f - t.stop) / 9.0)


def hero_machine(t, nf):
    """插座里的光包、活塞、细胞（整段一直在干活：001 抓得住，关不掉）。三下点名的推（stop / CDK20 / working）落在词上。"""
    T_TUBE = 45.0
    forced = [p - 4 - int(T_TUBE) for p in t.pushes]                  # 光包到活塞 = 出发 + 45；推的中段落在词上
    deps = []
    d = -40
    while d < nf:
        if all(abs(d - x) > 22 for x in forced):
            deps.append(d)
        d += 52
    deps = sorted(deps + forced)
    packets, arrivals = [], sorted(dp + int(T_TUBE) for dp in deps)
    for f in range(nf):
        packets.append([(f - dp) / T_TUBE for dp in deps if dp < f < dp + T_TUBE])
    REST, PRE, OUT = 0.6, 0.0, 4.2
    pis, cel = [], []
    n_push = 0
    for f in range(nf):
        p = REST
        bump = 0.0
        for a in arrivals:
            if a - 6 <= f < a:
                p = lerp(REST, PRE, smooth((f - (a - 6)) / 6))
            if a <= f < a + 16:
                p = lerp(PRE, OUT, smoother((f - a) / 16))
                bump = 0.07 * smoother((f - a) / 16)
            elif a + 16 <= f < a + 46:
                p = lerp(OUT, REST, smoother((f - a - 16) / 30))
                bump = 0.07 * (1 - smoother((f - a - 16) / 30))
        n_push = sum(1 for a in arrivals if a <= f)
        base = 1.0 + 0.30 * (1 - math.exp(-n_push / 9.0))
        pis.append(p)
        cel.append(min(1.45, base + bump))
    return packets, pis, cel, dict(departures=deps, arrivals=arrivals)


def mini_machine(t, i, nf):
    """小插座 i 的活塞、细胞、灯（1 亮 0 灭）。扣上的那几台在 off 落点灭灯、活塞缩回、细胞停。"""
    key = next((k for k, v in MINI_EV.items() if v == i), None)
    f_off = t.m_off[key][1] if key in t.m_off else None
    period = 50 + 3 * i
    phase = (7 * i) % period
    REST, OUT = 0.6, 4.0
    pis, cel, lamp = [], [], []
    c = 1.0 + 0.04 * (i % 3)
    for f in range(nf):
        if f_off is not None and f >= f_off:
            p0 = pis[f_off - 1] if f_off > 0 else REST
            pis.append(lerp(p0, 0.0, ease_out(clamp((f - f_off) / 12.0))))
            cel.append(cel[-1])
            lamp.append(0.0 if f != f_off + 2 else 0.0)
            continue
        k = (f - phase) % period
        if k < 16:
            p = lerp(REST, OUT, smoother(k / 16))
        elif k < 40:
            p = lerp(OUT, REST, smoother((k - 16) / 24))
        else:
            p = REST
        if k == 15:
            c = c + 0.07 * (1.40 - c)
        pis.append(p)
        cel.append(c)
        on = 1.0
        if f_off is not None and f_off - 2 <= f < f_off:               # 灭之前闪一下
            on = 0.0 if f == f_off - 2 else 1.0
        lamp.append(on)
    return pis, cel, lamp


# ================================================================ 搭场景
def build(seg, samples=16):
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    import kit_parts as KP
    import kit_socket as S_
    import bl_guide as BG
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    sc = SD.open_board(BOARD, NF, samples)
    board = bpy.data.objects["board"]
    zb = board.location.z
    cell, old_part = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p19_cdk20"))
    cx, cy = cell.matrix_world.translation.x, cell.matrix_world.translation.y
    print("DRILL cell", cell.name, round(cx / MM, 1), round(cy / MM, 1), "zb", round(zb / MM, 1), flush=True)
    SD.hide_tree(old_part)
    for o in bpy.data.objects:                                       # 11-23 Z18：板上 Imagine 牌的字在段尾贴着屏右缘被切成半截（背景过路牌，不是念词），这段里只藏字
        if o.type == "FONT" and (o.data.body or "") == "Imagine" and o.parent and o.parent.name.startswith("p35_loop"):
            o.hide_render = True
    for g in KP.gates_of(cell):
        SD.hide_tree(g)
    for o in [o for o in board.children if o.name.startswith("foot") and (o.matrix_world.translation.xy - Vector((cx, cy))).length < 0.05]:
        bpy.data.objects.remove(o)

    Kt = KP.Kit()
    sock = S_.h01b_cdk20_socket(Kt)
    p001 = S_.h02b_plug(Kt, which="001")
    atp = S_.h02b_plug(Kt, which="ATP")
    for o in (p001, atp):
        o.parent = sock
        o.matrix_parent_inverse = Matrix.Identity(4)
    p001["drill_role"], atp["drill_role"], sock["drill_role"] = "001", "atp", "socket"
    rig = S_.rig(sock)
    S_.rest(sock)
    print("DRILL baked modifiers", SD.apply_modifiers(sock), flush=True)
    for ch in rig["flow"].children:
        SD.hide_tree(ch)
    lit = bpy.data.materials["kit_clear_yellow_lit"]
    for lo_ in [o for o in sock.children_recursive if o.type == "LIGHT" and "lamp" in o.name]:
        lo_.data.energy = 0.03 * S * S                                    # 灯整段亮（001 关不掉）；灯功率随缩放平方

    # ---- 插座：浮在 CDK20 那一格上方（3-04 结尾的位置），极慢地漂；开盖前沉一下，插头到底时被顶一下
    q_up = SD.basis_quat(FACE, up=(0, 0, 1))
    q_lie = SD.basis_quat((0, 0, 1), up=(0, 1, 0))
    bc = Vector(BC) * MM * S
    C0 = Vector((cx, cy, zb))
    C1 = Vector((cx, cy + 4 * MM, zb + H_FLOAT * MM))

    def sock_center(f):
        c = C1 + Vector((0, 0, 0.25 * MM * math.sin(2 * math.pi * f / 160.0)))
        dip = 0.0
        if t.prep[0] <= f < t.prep[1] + 10:
            dip -= 0.6 * MM * (ramp(f, t.prep[0], t.prep[1], ease_in) if f < t.prep[1] else 1 - ramp(f, t.prep[1], t.prep[1] + 10, ease_out))
        dip += settle(f, t.close[1], -0.35 * MM, n=1.5, dur=12)
        return c + Vector((0, 0, dip))

    def sock_quat(f):
        return q_up @ Quaternion((0, 0, 1), math.radians(0.35 * math.sin(2 * math.pi * f / 210.0)))

    def recoil(f):
        return (settle(f, t.p001[1], -0.3, n=1.2, dur=12) + settle(f, t.twist[1], -0.12, n=1.5, dur=10)
                + settle(f, t.out[1], 0.2, n=1.2, dur=10))

    def float_mat(f):
        q = sock_quat(f)
        R = q.to_matrix().to_4x4()
        loc = sock_center(f) - (R.to_3x3() @ bc) + (R.to_3x3() @ Vector((recoil(f) * MM * S, 0, 0)))
        return Matrix.Translation(loc) @ R
    mats = [float_mat(f) for f in range(NF)]                             # 段尾冲镜头的那几帧等镜头烘完再改
    M_float = Matrix.Translation(C1 - (q_up.to_matrix() @ bc)) @ q_up.to_matrix().to_4x4()

    def to_world(f, p_local_mm):
        return mats[f] @ (Vector(p_local_mm) * MM * S)

    # ---- 断掉的浇口留在格子里（3-04 拔下来时断的）：躺着的位姿下打射线做浇口，段首前就断开，只剩断茬
    sock.matrix_world = (Matrix.Translation(C0 - (q_lie.to_matrix() @ bc)) @ q_lie.to_matrix().to_4x4()) @ Matrix.Diagonal((S, S, S, 1))
    bpy.context.view_layer.update()
    shell = [o for o in sock.children_recursive if o.type == "MESH" and "shell" in o.name and not o.hide_render]
    gates = SD.make_gates(cell, shell, [((-KP.CX, 4.0, 0), (1, 0, 0)), ((KP.CX, -4.0, 0), (-1, 0, 0)), ((0, -KP.CY, 0), (0, 1, 0))],
                          Kt.cat("blue"), cell.name + "_sock")
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    SD.break_gates(gates, -30, -20, scar)

    # ---- 机构：盖、光包、活塞、细胞（灯整段亮）
    packets_f, pis_f, cel_f, msched = hero_machine(t, NF)
    pipe = [Vector(p) for p in json.loads(sock["pipe_path_mm"])]
    NP = max(len(p) for p in packets_f)
    pk_objs = []
    for i in range(NP):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8 * MM, segments=24, ring_count=12)
        o = bpy.context.object; o.name = f"drill_packet_{i}"
        bpy.ops.object.shade_smooth()
        o.data.materials.append(lit)
        o.parent = sock
        o.matrix_parent_inverse = Matrix.Identity(4)
        pk_objs.append(o)
    for f in range(NF):
        S_.pose(sock, "lid", lid_angle(t, f))
        rig["lid"].keyframe_insert("rotation_euler", frame=f)
        S_.pose(sock, "piston", pis_f[f])
        rig["piston"].keyframe_insert("location", frame=f)
        S_.pose(sock, "cell", cel_f[f])
        rig["cell"].keyframe_insert("scale", frame=f)
        cur = packets_f[f]
        for i, o in enumerate(pk_objs):
            vis = i < len(cur)
            o.location = S_._lerp_path(pipe, cur[i]) * MM if vis else o.location
            o.scale = (1, 1, 1) if vis else (0.001, 0.001, 0.001)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("scale", frame=f)

    # ---- 料架：一块高达板件式的白色流道框，两排各五台 H01b 小插座（都插着 ATP），左边一块剂量旋钮盘
    R_rack = q_up.to_matrix()
    rack_o = C1 + R_rack @ (Vector(RACK_AT) * MM)
    M_rack = Matrix.Translation(rack_o) @ R_rack.to_4x4()
    mr = bpy.data.objects.get("main_runner")
    run_m = (mr.active_material if mr and mr.active_material else None) or Kt.white
    import kit_deep as D
    P = D.Part(Kt, "drill_rack", "white")
    rack = P.root
    rack["drill_role"] = "rack"
    WF = -2.3                                                            # 流道所在的面（小插座壳体中间）
    U0, U1, Z0, Z1 = -100.0, 56.0, -26.0, 27.0
    rb_ = 1.6
    S_.cyl(P, "runner_top", (WF, (U0 + U1) / 2, Z1), (0, 1, 0), rb_, U1 - U0 + 2 * rb_, run_m, .4)
    S_.cyl(P, "runner_bot", (WF, (U0 + U1) / 2, Z0), (0, 1, 0), rb_, U1 - U0 + 2 * rb_, run_m, .4)
    for uu in (U0, -56.0, U1):
        S_.cyl(P, "runner_v", (WF, uu, (Z0 + Z1) / 2), (0, 0, 1), rb_, Z1 - Z0, run_m, .4)
    S_.cyl(P, "runner_mid", (WF, 0.0, -3.4), (0, 1, 0), 1.0, 112.0, run_m, .3)
    for uu in MINI_U:                                                     # 浇口：中杆 → 上排壳底；下杆 → 下排壳底
        S_.cyl(P, "gate_top", (WF, uu, -1.3), (0, 0, 1), .55, 2.4, run_m, .1)
        S_.cyl(P, "gate_bot", (WF, uu, -22.2), (0, 0, 1), .55, 4.6, run_m, .1)
    # 旋钮盘：白底板（焊在左竖杆和中竖杆之间）、黑盘、白刻度、红刻线、字
    S_.box(P, "dial_plate", (-3.4, DIAL[1], 0.0), (1.6, 42.0, 44.0), run_m, .4)
    S_.cyl(P, "dial_disc", DIAL, (1, 0, 0), DIAL_R, 2.0, Kt.black, .3)
    for k in range(21):
        v = k / 20
        a = math.radians(dial_angle(v))
        long_ = k % 5 == 0
        r0, r1 = (DIAL_R - 4.0, DIAL_R - 1.2) if long_ else (DIAL_R - 2.8, DIAL_R - 1.2)
        rc = (r0 + r1) / 2
        ob = S_.box(P, "dial_tick", (-0.45, DIAL[1] + rc * math.cos(a), rc * math.sin(a)), (0.3, r1 - r0, 0.45 if long_ else 0.3), Kt.inkw, 0)
        ob.rotation_euler = (a, 0, 0)
        ob.location = Vector((-0.45, DIAL[1] + rc * math.cos(a), rc * math.sin(a))) * MM
    a6 = math.radians(dial_angle(0.75))
    red6 = S_.box(P, "dial_red", (-0.40, 0, 0), (0.4, 4.6, 0.7), Kt.red, 0)
    red6.rotation_euler = (a6, 0, 0)
    red6.location = Vector((-0.40, DIAL[1] + (DIAL_R - 3.1) * math.cos(a6), (DIAL_R - 3.1) * math.sin(a6))) * MM
    peg = S_.cyl(P, "dial_peg", (0.0, DIAL[1] + (DIAL_R - 3.0) * math.cos(math.radians(-53)), (DIAL_R - 3.0) * math.sin(math.radians(-53))), (1, 0, 0), .8, 1.8, Kt.red, .1)
    ic50_m = Kt.inkw.copy(); ic50_m.name = "drill_ic50_ink"
    ic50_em = SD.add_emission(ic50_m, (1.0, 0.93, 0.80), 0.0)
    rot_txt = (math.radians(90), 0, math.radians(90))
    t_ic50 = S_.label(P, "IC50", 4.2, (-0.5, DIAL[1], -10.5), rot_txt, ic50_m)
    # 11-23 Z17：字号 2.2 → 4.4（全景时屏上 ≥ 28 px）。放大后在红刻度旁放不下（会压刻度和旋钮），挪到盘面上半（12 点、半径 8.6，刻度内圈和旋钮之间）
    t_6000 = S_.label(P, "6,000 nM", 4.4, (-0.5, DIAL[1], 8.6), rot_txt, Kt.inkw)
    t_0 = S_.label(P, "0", 2.6, (-0.5, DIAL[1] + 10.2 * math.cos(math.radians(225)), 10.2 * math.sin(math.radians(225)) - 0.9), rot_txt, Kt.inkw)
    # "half"：上排上方一道红色括线 + 字（上排五台 = 十台的一半）
    half_m = Kt.red.copy(); half_m.name = "drill_half_red"
    half_em = SD.add_emission(half_m, (1.0, 0.04, 0.02), 0.0)
    hb = [S_.box(P, "half_bar", (-0.6, 0.0, 17.6), (0.8, 100.0, 0.8), half_m, .1)]
    for uu in (-50.0, 50.0):
        hb.append(S_.box(P, "half_tick", (-0.6, uu, 16.4), (0.8, 0.8, 3.2), half_m, .1))
        S_.cyl(P, "half_post", (-0.9, uu, 21.6), (0, 0, 1), .45, 8.2, run_m, .1)
    hb.append(S_.label(P, "half", 4.6, (-0.2, 0.0, 21.4), rot_txt, half_m))     # 11-23 Z17：19.4 → 21.4，离括线 ≥ 20 px
    # 旋钮和表针：一个转轴空物体，挂在料架上
    spin = bpy.data.objects.new("drill_dial_spin", None)
    sc.collection.objects.link(spin)
    spin.parent = rack
    spin.location = Vector((0.0, DIAL[1], DIAL[2])) * MM
    P2 = D.Part(Kt, "drill_knob", "gold")
    S_.cyl(P2, "knob", (1.6, 0, 0), (1, 0, 0), 3.6, 2.6, Kt.gold, .3)
    for k in range(12):
        a = 2 * math.pi * k / 12
        S_.box(P2, "knob_grip", (1.6, 3.6 * math.cos(a), 3.6 * math.sin(a)), (2.2, .5, .5), Kt.gold_satin, .05)
    S_.box(P2, "needle", (0.55, (DIAL_R - 2.5) / 2, 0), (0.5, DIAL_R - 2.5, 1.0), Kt.gold_satin, .1)
    S_.box(P2, "needle_tail", (0.55, -3.0, 0), (0.5, 4.0, 1.6), Kt.gold_satin, .1)
    P2.root.parent = spin
    P2.root.matrix_parent_inverse = Matrix.Identity(4)
    spin.rotation_mode = "XYZ"

    # 十台小插座（H01b mini，圆孔，红环），插座孔里给 001 的卡口销刻一道环槽和两条入口槽（小插座本来没有卡口）
    minis, m_atp, m_001 = [], [], {}
    for i in range(10):
        m = S_.h01b_cdk20_socket(Kt, lod="mini", pattern="round")
        Pc = D.Part(Kt, "tmp_cut", "white")
        Pc.root.scale = m.scale.copy()                                     # 刀具和小插座同一缩放（布尔在世界坐标里算）
        cutters = []
        for o in [o for o in m.children_recursive if o.type == "MESH" and ("barrel_lower" in o.name or "barrel_upper" in o.name)]:
            cs = [S_.tube(Pc, "pin_groove", (8.53, 0, 0), (1, 0, 0), 6.05, 4.9, 1.4, Kt.white, 0)]
            cs += [S_.box(Pc, "pin_slot", (10.2, sg * 5.55, 0), (4.4, 1.3, 1.2), Kt.white, 0) for sg in (1, -1)]
            for c_ in cs:
                S_.cut(o, c_)
            cutters += cs
        bpy.context.view_layer.update()
        SD.apply_modifiers(m)
        for c_ in cutters + [Pc.root]:
            bpy.data.objects.remove(c_)
        j_lo = S_.rig(m)["lamp_out"]
        j_lo.scale = (1.8, 1.8, 1.8)                                    # 灯珠放大：料架是全景，灯是读数
        m.parent = rack
        m.matrix_parent_inverse = Matrix.Identity(4)
        m.location = Vector((0.0, MINI_U[i % 5], ROW_Z[i // 5])) * MM
        m["drill_role"] = f"mini_{i}"
        minis.append(m)
        a = S_.h02b_plug(Kt, which="ATP")
        a.parent = m
        a.matrix_parent_inverse = Matrix.Identity(4)
        a["drill_role"] = f"matp_{i}"
        m_atp.append(a)
    for k, i in MINI_EV.items():
        p = S_.h02b_plug(Kt, which="001")
        p.parent = minis[i]
        p.matrix_parent_inverse = Matrix.Identity(4)
        p["drill_role"] = f"m001_{i}"
        m_001[k] = p
    rack.parent = None
    rack.matrix_world = M_rack @ Matrix.Diagonal((S, S, S, 1))
    rack_mat = lambda f: M_rack  # noqa: E731

    def rack_world(p_mm):
        return M_rack @ (Vector(p_mm) * MM * S)

    # 小插座的机构和灯
    mini_state = [mini_machine(t, i, NF) for i in range(10)]
    for i, m in enumerate(minis):
        r = S_.rig(m)
        pis, cel, lamp = mini_state[i]
        on_m = [o for o in r["lamp_out"].children if o.get("lamp") == "on"]
        off_m = [o for o in r["lamp_out"].children if o.get("lamp") == "off"]
        lts = [o for o in r["lamp_out"].children if o.type == "LIGHT"]
        seq_on, seq_off = [(0, lamp[0] < .5)], [(0, lamp[0] >= .5)]
        for f in range(1, NF):
            if (lamp[f] >= .5) != (lamp[f - 1] >= .5):
                seq_on += [(f - 1, lamp[f - 1] < .5), (f, lamp[f] < .5)]
                seq_off += [(f - 1, lamp[f - 1] >= .5), (f, lamp[f] >= .5)]
        for o in on_m:
            SD.hide_tree(o, seq_on)
        for o in off_m:
            SD.hide_tree(o, seq_off)
        for lo_ in lts:
            for f, h in seq_on:
                lo_.data.energy = 0.0 if h else 0.03 * 0.4 * 0.4 * S * S * 3.0
                lo_.data.keyframe_insert("energy", frame=f)
        for f in range(NF):
            S_.pose(m, "piston", pis[f])
            r["piston"].keyframe_insert("location", frame=f)
            S_.pose(m, "cell", cel[f])
            r["cell"].keyframe_insert("scale", frame=f)

    # 小插座里的插头：ATP 被顶出后往前下方落出画（落到板面以前藏起来），001 从左前上方飞进来沿轴插到底
    SEATW = S_.SEAT_W
    g_fall, v_fall = 0.6, 2.4                                           # 11-20 clip：0.35/2.0 时 001 的柄在第 s+17 帧擦到正落下的 ATP 针，加快下落

    def matp_state(i, f):
        """返回 (局部 mm, 四元数, 藏?)"""
        key = next((k for k, v in MINI_EV.items() if v == i), None)
        if key is None:
            return Vector((SEATW, 0, 0)), Quaternion(), False
        s, l, e = t.m_in[key]
        if f < s:
            return Vector((SEATW, 0, 0)), Quaternion(), False
        if f < s + 3:
            return Vector((SEATW + 0.2 * math.sin(math.pi * (f - s) / 3), 0, 0)), Quaternion(), False
        if f < s + 9:
            return Vector((SEATW + 24.0 * ease_out((f - s - 3) / 6, 2.4), 0, 0)), Quaternion(), False
        tt = f - (s + 9)
        hide_at = 27 if i < 5 else 22
        p = Vector((SEATW + 24.0 + v_fall * tt, 0.6 * tt, -0.5 * g_fall * tt * tt))
        q = Quaternion((0, 1, 0), math.radians(5.0 * tt)) @ Quaternion((1, 0, 0), math.radians(3.0 * tt))
        return p, q, tt >= hide_at

    def m001_state(key, f):
        """返回 (局部 mm, 四元数, 拧角, 晃角, 藏?)"""
        s, l, e = t.m_in[key]
        if f < s:
            return Vector((140.0, -110.0, 70.0)), Quaternion(), 0.0, 0.0, True
        APP = Vector((SEATW + 18.0, 0, 0))
        fa = s + 20
        if f < fa:
            u = smoother((f - s) / 20.0)
            P0, Cc = Vector((140.0, -110.0, 70.0)), Vector((50.0, -40.0, 45.0))
            p = P0 * (1 - u) ** 2 + Cc * (2 * u * (1 - u)) + APP * u * u
            q = Quaternion((0, 0, 1), math.radians(-28 * (1 - u))) @ Quaternion((1, 0, 0), math.radians(50 * (1 - u) ** 2))
            return p, q, 0.0, 0.0, False
        if f < l:
            u = (f - fa) / max(1, l - fa)
            return Vector((SEATW + 18.0 * (1 - ease_out(u, 2.2)), 0, 0)), Quaternion(), 0.0, 0.0, False
        d = max(0.0, settle(f, l, 0.1, n=1.0, dur=e - l)) if f < e + 2 else 0.0
        tw, tilt = 0.0, 0.0
        if key in t.m_off:
            o0, o1, o2 = t.m_off[key]
            if f >= o0:
                tw = 90.0 * smoother((f - o0) / max(1, o1 - 2 - o0)) if f < o1 - 2 else 90.0 - abs(settle(f, o1 - 2, 1.2, n=1.5, dur=12))
        else:
            tilt = 0.8 * math.sin(2 * math.pi * (f - l) / 37.0 + 0.6 * MINI_EV[key]) * ramp(f, l, l + 10)
        tilt += settle(f, l, 1.0, n=1.5, dur=16)
        return Vector((SEATW + d, 0, 0)), Quaternion(), tw, tilt, False

    for i, a in enumerate(m_atp):
        seq = []
        prev = None
        for f in range(NF):
            p, q, h = matp_state(i, f)
            SD.key_xform(a, f, loc=p * MM, quat=q)
            if h != prev:
                seq += ([(f - 1, prev)] if prev is not None else []) + [(f, h)]
                prev = h
        SD.hide_tree(a, seq)
    for key, p_ in m_001.items():
        i = MINI_EV[key]
        r = S_.rig(p_)
        seq, prev = [], None
        for f in range(NF):
            p, q, tw, tl, h = m001_state(key, f)
            SD.key_xform(p_, f, loc=p * MM, quat=q)
            S_.pose(p_, "twist", tw)
            r["twist"].keyframe_insert("rotation_euler", frame=f)
            S_.pose(p_, "tilt", tl)
            r["tilt"].keyframe_insert("rotation_euler", frame=f)
            if key in t.m_off:
                tab = S_.lug_tab_angle(tw)
                o1, o2 = t.m_off[key][1], t.m_off[key][2]
                if f >= o1:
                    tab = -25.0 + abs(settle(f, o1, 1.2, n=1.5, dur=o2 - o1 + 4))
                S_.pose(minis[i], "tab", tab)
                S_.rig(minis[i])["tab"].keyframe_insert("rotation_euler", frame=f)
            if h != prev:
                seq += ([(f - 1, prev)] if prev is not None else []) + [(f, h)]
                prev = h
        SD.hide_tree(p_, seq)

    # 旋钮、IC50 字、half 括线的亮度
    for f in range(NF):
        spin.rotation_euler = (math.radians(dial_angle(dial_value(t, f))), 0, 0)
        spin.keyframe_insert("rotation_euler", frame=f)
        g = 0.0
        if f >= t.ic50[0]:
            g = 1.6 * ramp(f, t.ic50[0], t.ic50[1] + 4, ease_out) - 1.0 * ramp(f, t.ic50[1] + 10, t.ic50[2] + 30)
        ic50_em.inputs["Strength"].default_value = max(0.0, g)
        ic50_em.inputs["Strength"].keyframe_insert("default_value", frame=f)
        h = 0.0
        if f >= t.half[0]:
            h = 0.40 * ramp(f, t.half[0], t.half[1] + 4, ease_out) - 0.22 * ramp(f, t.half[1] + 12, t.half[2] + 30)
        half_em.inputs["Strength"].default_value = max(0.0, h)
        half_em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    for o in hb:                                                        # 11-21 Gemini：括线原来一直挂着，"IC50" 时就看得见；改成 "in half" 的 in 上才出现（同时发亮）
        SD.hide_tree(o, [(0, True), (t.half[0], False)])
    # 11-23 Z17：6,000 nM 放大后，镜头下摇到料架时（第 798–802 帧）字从屏上缘半截进画（scan_text 贴边）。
    # 照钻取规矩“标注类在词上出现”：念到 6,000 前 2 帧才出现（同 half 的做法），之前盘面只有刻度
    SD.hide_tree(t_6000, [(0, True), (t.cross - 2, False)])

    # ---- 插座里的两个插头：ATP（真插头）被顶出、001 插到底、在孔里晃、拧 12° 卡住弹回、被弹簧顶出
    axis_q = Quaternion()

    def atp_state(f):
        s0, s1, s2 = t.swap
        if f < s0 - 4:
            return Vector((SEATW, 0, 0)), axis_q
        if f < s0:
            return Vector((SEATW + 0.15 * math.sin(math.pi * (f - s0 + 4) / 4), 0, 0)), axis_q
        if f < s1:
            u = (f - s0) / (s1 - s0)
            return Vector((SEATW + 22.0 * ease_out(u, 2.4), 0, 0)), axis_q
        P0 = Vector((SEATW + 22.0, 0, 0))
        u = ramp(f, s1, s2, lambda x: 1 - (1 - x) ** 4)
        p = P0.lerp(Vector(H_ATP), u) + Vector((0, -3.0 * math.sin(math.pi * u), 9.0 * math.sin(math.pi * u)))
        tumble = 22 * math.sin(math.pi * u) * (1 - u)
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * (f - s2) / 140.0))) * ramp(f, s2, s2 + 30)
        return p + bob, Quaternion((0, 1, 0), math.radians(tumble))

    # 镜头先烘（001 段首要镜头坐标）
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = 36.0
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0
    ax, ay, az_, ar = ALIGN
    keys = [
        dict(f=0, space="sock", tgt=(-2.0, 4.0, -3.0), az=-22, el=22, dist=175, lens=50),
        dict(f=t.prep[1], space="sock", tgt=(-4.0, 2.0, -3.0), az=-28, el=27, dist=150, lens=50),
        dict(f=t.cabin, space="sock", tgt=(-3.0, 3.0, -7.0), az=-58, el=55, dist=100, lens=35),
        dict(f=t.p001[2], space="sock", tgt=(-2.0, 2.0, -6.0), az=-55, el=57, dist=96, lens=35),
        dict(f=t.lock[1], space="sock", tgt=(4.0, 1.0, -3.0), az=-50, el=52, dist=84, lens=35),        # a lock：往插孔靠近，看 001 在孔里晃
        dict(f=t.lock[2] + 20, space="sock", tgt=(5.0, 1.0, -2.5), az=-46, el=50, dist=82, lens=35),
        dict(f=t.twist_view, space="sock", tgt=(12.0, 4.0, 0.0), az=24, el=22, dist=104, lens=50),     # as：绕到侧面看拧卡口
        dict(f=t.drill[0], space="sock", tgt=(12.0, 3.0, 0.0), az=20, el=22, dist=99, lens=50),
        dict(f=t.drill[1], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=36, lens=50),          # Does：钻到触点块，叠化到真实层
        dict(f=t.drill[2], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=33, lens=50, ease="linear"),
        dict(f=t.real_out[0], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=31, lens=50, ease="linear"),
        dict(f=t.drill_out[1], space="sock", tgt=(-4.0, 2.0, -5.0), az=-50, el=48, dist=112, lens=35),  # working：退回机舱，输出端进画
        dict(f=t.out[0] - 12, space="sock", tgt=(-5.0, 1.0, -6.0), az=-56, el=52, dist=104, lens=35),
        dict(f=t.out[1] + 14, space="sock", tgt=(2.0, 8.0, -2.0), az=-26, el=32, dist=160, lens=40),
        dict(f=t.rack[1], space="rack", tgt=(0.0, -24.0, -1.0), az=10, el=14, dist=172, lens=35),
        dict(f=t.turn[0], space="rack", tgt=(0.0, -26.0, -1.0), az=8, el=13, dist=176, lens=35),
        dict(f=t.m_in["m1"][2], space="rack", tgt=(0.0, -22.0, 0.0), az=4, el=13, dist=170, lens=35),
        dict(f=t.half[1], space="rack", tgt=(0.0, -20.0, 1.0), az=0, el=14, dist=168, lens=35),
        dict(f=t.m_in["m5"][0], space="rack", tgt=(0.0, -21.0, 0.0), az=-3, el=13, dist=164, lens=35),
        dict(f=t.stop, space="rack", tgt=(0.0, -22.0, 0.0), az=-6, el=13, dist=158, lens=35),
        dict(f=NF - 1, space="rack", tgt=(0.0, -22.0, 0.0), az=-6.4, el=13, dist=157, lens=35, ease="linear"),
    ]
    rigc = SD.CamRig(keys, lambda f: mats[f], MM * S, spaces={"rack": (rack_mat, MM * S)})
    for fs_, amp in ((t.p001[1], 0.16), (t.twist[1], 0.12), (t.close[1], 0.14), (t.stop, 0.10)):
        rigc.shake(fs_, amp, 6)

    def drift(f, eye, tgt):
        d = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        k = 1.0 - 0.85 * (ramp(f, t.drill[0], t.drill[1]) * (1 - ramp(f, t.real_out[1], t.drill_out[1])))
        k *= 1.0 - ramp(f, t.rush[0] - 30, t.rush[0])                    # 段尾交接：镜头站稳
        off = (right * 0.010 * math.sin(f / 97.0) + up * 0.007 * math.cos(f / 131.0)) * d * k
        return off, off * 0.6
    recs = rigc.bake(cam, NF, drift=drift)

    def cam_space(f, x, y, z):
        eye, _, _, q = recs[f]
        return eye + q @ Vector((x, y, -z))

    # ---- 段尾：插座从画面左边冲进镜头（对数深度），孔口面正对镜头盖满画面；镜头不动
    r0, r1 = t.rush
    eye1, _, _, q1 = recs[NF - 1]
    fwd1, up1 = q1 @ Vector((0, 0, -1)), q1 @ Vector((0, 1, 0))
    q_end = SD.basis_quat(-fwd1, up=up1)
    D_END = 22.0 * MM                                                     # 孔口面离镜头 22 mm：插座面盖满 16:9
    face_l = Vector((12.0, 0, 0)) * MM * S
    P_end = eye1 + fwd1 * D_END
    M0 = mats[r0]
    face0 = M0 @ face_l
    rel0 = q1.inverted() @ (face0 - eye1)                                 # 镜头坐标（x 右、y 上、−z 前）
    z0, z1 = -rel0.z, D_END
    sx0, sy0 = rel0.x / z0, rel0.y / z0
    q0 = M0.to_quaternion()
    for f in range(r0, NF):
        u = (f - r0) / max(1, r1 - r0)
        e = ease_in(u, 1.7)
        z = math.exp(lerp(math.log(z0), math.log(z1), e))
        k = smoother(min(1.0, u * 1.15))
        sx, sy = lerp(sx0, 0.0, k), lerp(sy0, 0.0, k)
        face_w = eye1 + q1 @ Vector((sx * z, sy * z, -z))
        q = q0.slerp(q_end, smoother(min(1.0, u * 1.1)))
        R = q.to_matrix().to_4x4()
        mats[f] = Matrix.Translation(face_w - (R.to_3x3() @ face_l)) @ R
    for f in range(NF):
        loc, q, _ = mats[f].decompose()
        SD.key_xform(sock, f, loc=loc, quat=q, scale=(S, S, S))

    # ---- 001 的轨迹
    a_, b_ = t.wipe
    h0, h1, h2 = t.hover
    hov_w = M_float @ (Vector(H001) * MM * S)

    def p001_state(f):
        """返回 (局部 mm, 局部四元数, 拧角, 晃角)。"""
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * f / 150.0)))
        if f <= h1:
            if f <= b_ + 4:                                                  # T5：镜头前 28 mm 从左下往右上掠过
                u = (f - a_ + 2) / (b_ - a_ + 6)
                pw = cam_space(f, lerp(-0.030, 0.034, u), lerp(-0.006, 0.010, u), 0.028)
            else:
                u = smoother((f - b_ - 4) / max(1, h1 - b_ - 4))
                p0 = cam_space(b_ + 4, 0.034, 0.010, 0.028)
                mid = p0.lerp(hov_w, 0.5) + Vector((0, 0, 6 * MM))
                pw = p0.lerp(mid, u).lerp(mid.lerp(hov_w, u), u)
            pl = mats[f].inverted() @ pw / (MM * S)
            _, _, _, qc = recs[f]
            qw_fly = SD.basis_quat(qc @ Vector((1, 0.15, 0)), up=qc @ Vector((0, 1, 0)))
            q_loc_fly = mats[f].to_quaternion().inverted() @ qw_fly
            u2 = ramp(f, b_ + 4, h1)
            q = q_loc_fly.slerp(Quaternion(), u2) @ Quaternion((1, 0, 0), math.radians(40 * math.sin(f / 9.0) * (1 - u2)))
            return pl, q, 0.0, 0.0
        i0, i1, i2 = t.p001
        hov = Vector(H001) + bob * ramp(f, h1, h1 + 20) + Vector((0, 0, settle(f, h1, 0.6, n=1.0, dur=h2 - h1 + 6)))
        APP = Vector((SEATW + 20.0, 0, 0))
        sw0 = max(i0, t.swap[1] + 8)
        mid = sw0 + int(0.5 * (i1 - sw0))
        if f < sw0:
            return hov, Quaternion(), 0.0, 0.0
        if f < mid:
            u = smoother((f - sw0) / (mid - sw0))
            hv = Vector(H001) + bob
            return hv.lerp(APP, u) + Vector((5.0 * math.sin(math.pi * u), 0, 2.0 * math.sin(math.pi * u))), Quaternion((0, 0, 1), math.radians(-8 * math.sin(math.pi * u))), 0.0, 0.0
        if f < i1:
            u = (f - mid) / (i1 - mid)
            return Vector((SEATW + 20.0 * (1 - ease_out(u, 2.2)), 0, 0)), Quaternion(), 0.0, 0.0
        o0, o1, o2 = t.out
        # 插到底：缝宽，在孔里晃（≤ 1.6°）：到底时一下、每次活塞推一下、点名时一下，平时极慢地晃
        tilt = 1.4 * math.exp(-(f - i1) / 18.0) * math.sin(2 * math.pi * (f - i1) / 14.0)
        tilt += 0.45 * math.sin(2 * math.pi * f / 53.0) * ramp(f, i1, i1 + 30)
        for fk, amp in [(t.name[1], 1.0), (t.twist[1] + 9, 0.9)] + [(p, 0.5) for p in t.pushes]:
            tilt += settle(f, fk, amp, n=1.5, dur=18)
        tilt = max(-1.6, min(1.6, tilt))
        w0, w1, w2 = t.twist
        tw = 0.0
        if w0 <= f < w1:
            tw = 12.0 * smoother((f - w0) / (w1 - w0))
        elif w1 <= f < w1 + 9:                                              # 卡住：顶在 12° 抖
            tw = 12.0 - 0.9 * abs(math.sin(math.pi * (f - w1) / 3.0))
        elif w1 + 9 <= f < w2:                                              # 弹簧推回 0°
            tw = 12.0 * (1 - ease_out(clamp((f - w1 - 9) / 12.0), 2.6))
        if f < o0 - 4:
            return Vector((SEATW, 0, 0)), Quaternion(), tw, tilt
        if f < o0:
            return Vector((SEATW + 0.15 * math.sin(math.pi * (f - o0 + 4) / 4), 0, 0)), Quaternion(), 0.0, tilt * 0.5
        if f < o1:                                                          # 弹出：沿轴 24 mm（针尖离开面板和卡扣）
            u = (f - o0) / (o1 - o0)
            return Vector((SEATW + 24.0 * ease_out(u, 2.4), 0, 0)), Quaternion(), 0.0, 0.0
        P0 = Vector((SEATW + 24.0, 0, 0))
        u = ramp(f, o1, o2)
        p = P0.lerp(Vector(H001_OUT), u) + Vector((0, 0, 4.0 * math.sin(math.pi * u)))
        bob2 = Vector((0, 0, 0.5 * math.sin(2 * math.pi * (f - o2) / 140.0))) * ramp(f, o2, o2 + 30)
        return p + bob2, Quaternion((0, 0, 1), math.radians(10 * math.sin(math.pi * u))), 0.0, 0.0

    atp_track, p001_track = [], []
    r001 = S_.rig(p001)
    for f in range(NF):
        pa, qa = atp_state(f)
        SD.key_xform(atp, f, loc=pa * MM, quat=qa)
        atp_track.append(tuple(pa))
        pl, ql, tw, tl = p001_state(f)
        SD.key_xform(p001, f, loc=pl * MM, quat=ql)
        S_.pose(p001, "twist", tw)
        r001["twist"].keyframe_insert("rotation_euler", frame=f)
        S_.pose(p001, "tilt", tl)
        r001["tilt"].keyframe_insert("rotation_euler", frame=f)
        S_.pose(sock, "tab", S_.lug_tab_angle(tw))
        rig["tab"].keyframe_insert("rotation_euler", frame=f)
        p001_track.append(tuple(pl))
    hh = t.hide_hero_plugs                                                # 镜头到了料架以后，插座旁边两个待机的插头收掉（段尾冲镜头时不挡）
    SD.hide_tree(p001, [(0, False), (hh - 1, False), (hh, True)])
    SD.hide_tree(atp, [(0, False), (hh - 1, False), (hh, True)])

    # ---- 灯光：大板主光（以插座和料架中间为中心）+ 舱内补光（挂在插座上，开盖时亮）+ 料架正面一块柔光
    mid_xy = (C1 + rack_o) / 2
    KP.lights(mid_xy.x, mid_xy.y, 1.0)
    fill = bpy.data.lights.new("drill_fill", "AREA")
    fill.shape = "RECTANGLE"; fill.size, fill.size_y = 60 * MM * S, 40 * MM * S
    fill.color = (1, .98, .95)
    fo = bpy.data.objects.new("drill_fill", fill)
    sc.collection.objects.link(fo)
    fo.parent = sock
    tgt_l = Vector((-9, 0, -8))
    el = math.radians(32)
    fo.location = (tgt_l + Vector((math.cos(el), 0, math.sin(el))) * 120) * MM
    fo.rotation_euler = (tgt_l - Vector(fo.location) / MM).to_track_quat("-Z", "Y").to_euler()
    fo.scale = (1 / S, 1 / S, 1 / S)
    for f in range(NF):
        fill.energy = 0.55 * S * S * clamp(lid_angle(t, f) / 60.0) + 0.06
        fill.keyframe_insert("energy", frame=f)
    rf = bpy.data.lights.new("drill_rack_fill", "AREA")
    rf.shape = "RECTANGLE"; rf.size, rf.size_y = 0.16, 0.06
    rf.color = (1, .97, .93)
    rf.energy = 2.2
    rfo = bpy.data.objects.new("drill_rack_fill", rf)
    sc.collection.objects.link(rfo)
    rfo.location = rack_world((150.0, -20.0, 70.0))
    rfo.rotation_euler = (rack_world((0, -20.0, 0)) - rfo.location).to_track_quat("-Z", "Y").to_euler()

    # ---- 焦点
    plan = BG.plan_from_keys(K)

    def mouth_w(f):
        return to_world(f, (12.0, 0, 0))

    def output_w(f):
        return to_world(f, (-13.5, -2.8 - pis_f[f], -4.0))
    rack_c = rack_world((0.0, -20.0, 0.0))
    targets = dict(seam=lambda f: to_world(f, (11.7, -8.0, 0.0)), output=output_w, keyhole=mouth_w,
                   entry=lambda f: to_world(f, tuple(Vector(p001_track[f]) + Vector((2.0, 0, 0)))),
                   dial=lambda f: rack_world((0.6, DIAL[1], 0.0)), half=lambda f: rack_world((0.0, 0.0, 12.0)))
    base = lambda f: to_world(f, BC)  # noqa: E731
    fpts = BG.focus_track(plan, targets, NF, base=base)
    al_w = lambda f: to_world(f, (ax, ay, az_))  # noqa: E731
    for f in range(NF):
        w3 = ramp(f, t.swap[0] - 10, t.swap[0]) * (1 - ramp(f, t.p001[1], t.p001[1] + 6))
        if w3 > 0:                                                           # 顶替、插到底都在孔口：焦点钉在孔口
            fpts[f] = fpts[f].lerp(mouth_w(f), w3)
        w = ramp(f, t.drill[0], t.drill[1] - 10) * (1 - ramp(f, t.real_out[1], t.drill_out[1]))
        if w > 0:                                                            # 钻：焦点在触点块顶面
            fpts[f] = fpts[f].lerp(al_w(f), w)
        w4 = ramp(f, t.twist_view - 20, t.twist[0]) * (1 - ramp(f, t.drill[0], t.drill[0] + 16))
        if w4 > 0:                                                           # 拧：焦点在孔口（柄和卡扣）
            fpts[f] = fpts[f].lerp(mouth_w(f) + (mouth_w(f) - to_world(f, (0, 0, 0))) * 0.25, w4)
        w5 = ramp(f, t.out[1] + 10, t.rack[1] - 15) * (1 - ramp(f, t.rack[1] - 15, t.rack[1] + 10))
        if w5 > 0:                                                           # 平移到料架
            fpts[f] = fpts[f].lerp(rack_c, w5)
        if f < t.wipe[1]:                                                    # T5：焦点在插座，前景 001 完全虚化
            fpts[f] = base(f)
        w6 = ramp(f, r0 - 2, r0 + 8)
        if w6 > 0:                                                           # 段尾：焦点跟着冲过来的孔口面
            fpts[f] = fpts[f].lerp(mats[f] @ face_l, w6)
    phases = [(0, FSTOP["front"]), (t.open1[1], FSTOP["cabin"]), (t.twist_view - 30, FSTOP["front"]), (t.drill[0] + 20, FSTOP["drill"]),
              (t.drill_out[1], FSTOP["cabin"]), (t.out[1] + 20, FSTOP["rack"]), (r0, FSTOP["front"])]
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    fst, focus_d = [], []
    for f in range(NF):
        v = phases[0][1]
        for (fa, va), (fb, vb) in zip(phases, phases[1:] + [(10 ** 6, phases[-1][1])]):
            if fa <= f:
                span = 24 if fb != r0 else 8
                v = va if f < fb - span // 2 else lerp(va, vb, smooth((f - fb + span // 2) / span))
        fst.append(v)
        d.aperture_fstop = v
        d.keyframe_insert("aperture_fstop", frame=f)
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.focus_distance = max(0.003, (fpts[f] - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        focus_d.append(d.focus_distance)

    # ---- 轮廓光（灯光链接，只照被点名的零件）
    key = bpy.data.objects["key"]
    dial_objs = [o for o in P.root.children if o.type in ("MESH", "FONT") and o.name.startswith("drill_rack_dial")] + [t_ic50, t_6000, t_0] + \
        [o for o in P2.root.children_recursive if o.type == "MESH"]
    rim_groups = dict(seam=[o for o in sock.children_recursive if o.type == "MESH" and ("faceplate" in o.name or "shell" in o.name)],
                      output=[o for o in sock.children_recursive if o.type == "MESH" and any(k in o.name for k in ("piston", "cell_", "rod_pad"))],
                      keyhole=[o for o in sock.children_recursive if o.type == "MESH" and ("red_ring" in o.name or "barrel" in o.name)],
                      entry=[p001], dial=dial_objs, half=hb)
    rims = {}
    for it in plan:
        if not it.get("rim", True):
            continue
        sc.frame_set(it["land"])
        objs = BG._meshes([o for tg in it["target"] for o in rim_groups.get(tg, [])])
        if not objs:
            continue
        pts = [m.matrix_world @ Vector(c) for m in objs for c in m.bound_box]
        size = max((Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))) -
                    Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))).length, 0.004)
        k_irr = key.data.energy / (key.matrix_world.translation - Vector(pts[0])).length ** 2
        pw = 1.0 * k_irr * (3.0 * size) ** 2
        lt = BG.guide_rim([it], rim_groups, cam, key, power=pw)
        rims.update(lt)
        holder = rack if it["target"][0] in ("dial", "half") else sock
        for lo_ in lt.values():
            aim = bpy.data.objects[lo_.name + "_aim"]
            for ob in (lo_, aim):
                ob.parent = holder
                ob.matrix_parent_inverse = holder.matrix_world.inverted()
    SD.linear_all([sock, atp, p001, cam, rack, spin] + list(sock.children_recursive) + list(atp.children_recursive) + list(p001.children_recursive)
                  + list(rack.children_recursive) + [o for o in bpy.data.objects if o.type == "LIGHT"])
    for m in (ic50_m, half_m):
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for fc in SD_fcurves(m.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- cam.json：每帧镜头、对位圈在画面上的圆（中心、半径）、插座投影
    camj = dict(seg=seg, nf=NF, frames=[])
    for f in range(NF):
        rc = SD.project(recs[f], al_w(f))
        rad = []
        for k in range(8):
            a = 2 * math.pi * k / 8
            pp = SD.project(recs[f], to_world(f, (ax + ar * math.cos(a), ay + ar * math.sin(a), az_)))
            if pp and rc:
                rad.append(math.hypot(pp[0] - rc[0], pp[1] - rc[1]))
        camj["frames"].append(dict(f=f, eye=list(recs[f][0]), q=list(recs[f][3]), lens=recs[f][2], fstop=fst[f], focus=focus_d[f],
                                   ring=[rc[0], rc[1], sum(rad) / len(rad)] if rc and rad else None,
                                   sock=list(SD.project(recs[f], to_world(f, BC)) or [0, 0, 0]),
                                   rack=list(SD.project(recs[f], rack_c) or [0, 0, 0]),
                                   lid=lid_angle(t, f), dial=dial_value(t, f)))
    camj["machine"] = msched
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    # 段尾交接（出镜 5-05+06 的段首从这一帧退出来）：插座在镜头坐标里的位姿
    loc_e, q_e, _ = mats[NF - 1].decompose()
    rel_loc = q1.inverted() @ (loc_e - eye1)
    hand = dict(seg=seg, frame=NF - 1, note="HKBU SCIE1007 课程作业的科普视频：5-04 段尾，CDK20 插座（H01b hero，0.7 倍，盖合着，孔口空，灯亮）孔口面正对镜头盖满画面",
                cam=dict(eye=list(eye1), quat=list(q1), lens_35mm_equiv=recs[NF - 1][2], sensor_mm=SD.SENSOR, fstop=fst[NF - 1], focus_m=focus_d[NF - 1]),
                socket_world=dict(loc=list(loc_e), quat=list(q_e), scale=S),
                socket_in_camera=dict(loc_m=list(rel_loc), quat=list(q1.inverted() @ q_e), face_dist_m=D_END, axes="镜头坐标：x 右、y 上、−z 朝前"),
                state=dict(lid_deg=0.0, lamp="on", plug_in_mouth=None, tab_deg=0.0))
    (W / "handoff_tail.json").write_text(json.dumps(hand, ensure_ascii=False, indent=1), encoding="utf-8")
    coc = []
    for f in range(0, NF, 30):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        Sd = focus_d[f]
        dc = (to_world(f, BC) - eye).dot(fwd)
        coc.append(dict(f=f, fstop=round(fst[f], 1), focus_mm=round(Sd / MM, 1), sock_mm=round(dc / MM, 1),
                        coc_sock=round(SD.coc_px(lens, fst[f], Sd, dc), 2),
                        coc_pm8=round(max(SD.coc_px(lens, fst[f], Sd, Sd + 8 * MM * S), SD.coc_px(lens, fst[f], Sd, Sd - 8 * MM * S)), 2)))
    chk = dict(coc=coc, rims={k: dict(name=v.name, peak_w=round(v["peak_w"], 3)) for k, v in rims.items()}, plan=plan, machine=msched,
               gates=[dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in gates],
               rush=dict(z0_mm=round(z0 / MM, 1), sx0=round(sx0, 3), sy0=round(sy0, 3)))
    (W / "build_check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


def SD_fcurves(action):
    import bl_guide as BG
    return BG._fcurves(action)


# ================================================================ 穿模检查的分组
def _ancestors(o):
    p = o.parent
    while p is not None:
        yield p
        p = p.parent


def _meshes_under(root, skip=()):
    out = []
    for o in root.children_recursive:
        anc = set(_ancestors(o))
        if any(o == s or s in anc for s in skip):
            continue
        base = o.name.rsplit(".", 1)[0] if o.name.rsplit(".", 1)[-1].isdigit() else o.name   # 布尔刀具复制多份后名字带 .001
        if o.type in ("MESH", "CURVE", "FONT") and not base.endswith("_cut") and not o.hide_render and not o.name.startswith("drill_packet"):
            out.append(o)
    return out


def _solid(root):
    return [o for o in [root] + _meshes_under(root) if o.type in ("MESH", "CURVE", "FONT")]


def clip_plan(sc):
    """插头 vs 插座、两插头互相、盖动时 vs 机身；料架上：小插座里的插头 vs 小插座和料架、001 vs 落下的 ATP；段尾插座 vs 料架。"""
    import bpy
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, p001, atp, rack = R["socket"], R["001"], R["atp"], R["rack"]
    s_m = _meshes_under(sock, skip=[p001, atp])
    a_m, k_m = _solid(atp), _solid(p001)
    lid_j = [o for o in sock.children_recursive if o.type == "EMPTY" and o.get("role") == "lid"][0]
    on_lid = lambda o: lid_j in set(_ancestors(o))  # noqa: E731
    lid_m = [o for o in s_m if on_lid(o)]
    not_lid = [o for o in s_m if not on_lid(o)]
    minis = [R[f"mini_{i}"] for i in range(10)]
    matp = [R[f"matp_{i}"] for i in range(10)]
    m001 = [R[k] for k in R if k.startswith("m001_")]
    mini_body = [o for m in minis for o in _meshes_under(m, skip=[p for p in matp + m001 if p.parent == m])]
    rack_m = [o for o in _meshes_under(rack, skip=minis) if o.type in ("MESH", "FONT")]
    plugs_mini_atp = [o for p in matp for o in _solid(p)]
    plugs_mini_001 = [o for p in m001 for o in _solid(p)]
    # 11-21 Gemini：被顶出的 ATP 往下掉，会不会穿过料架下面板子上的零件（蛋白、链）——原来只查了料架。板上料架周围 0.3 m 内的实体
    mine = set([rack, sock] + list(rack.children_recursive) + list(sock.children_recursive))
    rc = rack.matrix_world.translation
    board_m = [o for o in bpy.data.objects if o.type == "MESH" and o not in mine and not o.hide_render
               and not o.name.split(".")[0].endswith("_cut") and (o.matrix_world.translation - rc).length < 0.3]
    frames = set(range(0, NF, 3))
    for a, b in ((t.swap[0], t.swap[2]), (t.p001[0], t.p001[2] + 4), (t.twist[0], t.twist[2]), (t.out[0], t.out[2]),
                 (t.open1[0], t.open1[1] + 4), (t.close[0], t.close[2]), (t.turn[0] - 40, NF - 1)):
        frames |= set(range(max(0, a), min(NF, b + 1)))

    def groups(f):
        g = [("plug_vs_socket", a_m + k_m, s_m, sock), ("atp_vs_001", a_m, k_m, sock)]
        if t.open1[0] <= f <= t.close[2] + 4:
            g.append(("lid_vs_body", lid_m, not_lid, sock))
        if f >= t.rack[0]:
            g.append(("mini_plugs_vs_rack", plugs_mini_atp + plugs_mini_001, mini_body + rack_m, rack))
            g.append(("mini_001_vs_atp", plugs_mini_001, plugs_mini_atp, rack))
            g.append(("mini_atp_vs_board", [o for o in plugs_mini_atp if not o.hide_render], board_m, None))   # 藏起来以后不算
        if f >= t.rush[0] - 2:
            g.append(("socket_vs_rack", s_m, mini_body + rack_m + plugs_mini_atp + plugs_mini_001, None))
        return g

    return dict(frames=sorted(frames), groups=groups, cam_near=lambda f: s_m, ref=sock)   # 料架段镜头离料架 ≥ 10 cm，只量插座（段尾它冲到 22 mm）


# ================================================================ 真实结构层：AlphaFold DB 的 CDK20 预测模型 + 我们重新对接的配体
PLDDT = [(90, (0.0, 0.325, 0.839)), (70, (0.396, 0.796, 0.953)), (50, (1.0, 0.859, 0.075)), (-1, (1.0, 0.490, 0.271))]
ELEM_COL = {"C": (0.93, 0.66, 0.16), "N": (0.16, 0.32, 0.95), "O": (0.92, 0.12, 0.08), "S": (0.95, 0.85, 0.2), "Cl": (0.2, 0.8, 0.3), "F": (0.5, 0.9, 0.5)}


def read_sdf(path, mode=1):
    """第 mode 个分子：[(元素, x, y, z)]（含氢）和键 [(i, j, 级)]（0 起）。"""
    blocks = Path(path).read_text(encoding="utf-8").split("$$$$")
    L = blocks[mode - 1].strip("\n").splitlines()
    i0 = next(i for i, l in enumerate(L) if "V2000" in l)
    na, nb = int(L[i0][0:3]), int(L[i0][3:6])
    atoms = [(L[i0 + 1 + k][31:34].strip(), float(L[i0 + 1 + k][0:10]), float(L[i0 + 1 + k][10:20]), float(L[i0 + 1 + k][20:30])) for k in range(na)]
    bonds = [(int(L[i0 + 1 + na + k][0:3]) - 1, int(L[i0 + 1 + na + k][3:6]) - 1, int(L[i0 + 1 + na + k][6:9])) for k in range(nb)]
    return atoms, bonds


def real_pull(t, f):
    """真实层镜头后拉的进度 0–1：叠化进来以后在整个停留时间里慢慢往后拉（停 3 秒，不能停死），退出时 30 帧推回孔口。"""
    a = smoother(clamp((f - t.real_in[0]) / max(40.0, t.real_out[0] - t.real_in[0])))
    b = smooth((f - (t.real_out[0] - 8)) / 30.0)
    return clamp(a - b)


def build_real(seg, mode="render", *frames, ligand=LIGAND, Tcls=None, lig_motion=None, pull=None):
    """真实层（透明底 RGBA）：主链 CA 管子按 pLDDT 上色、半透明分子表面、配体球棍（重原子；碳金色，氮蓝，氧红）。
    对接坐标和 AF 模型同一个坐标系（CA 坐标逐个相同），只减同一个重原子质心。镜头对位同 3-04：口袋 R_POCKET 圈压在对位圈上。
    lig_motion(t, f) -> (平移 Å 向量, 绕配体质心的四元数)：W4 用来让 048 滑进口袋；不给就静止。"""
    import bpy
    import numpy as np
    from mathutils import Matrix, Quaternion, Vector
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = (Tcls or T)(EV)
    pull = pull or real_pull
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]
    f0, f1 = t.real_in[0] - 2, t.real_out[1] + 1
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    SD.gpu(sc)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = SD.OUT_W, SD.OUT_H, 100
    sc.render.fps = SD.FPS
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.frame_start, sc.frame_end = f0, f1
    A = 0.01

    at = SD.pdb_atoms(STRUCT)
    xyz = np.array([a[5:8] for a in at])
    cen = xyz.mean(0)
    xyz = xyz - cen
    npz = np.load(SURF)
    pocket = np.array(npz["pocket"], float)
    dirv, clear = SD.way_out(xyz, pocket)

    me = bpy.data.meshes.new("cdk20_surface")
    me.from_pydata([tuple(v * A) for v in npz["verts"].astype(float)], [], [tuple(q) for q in npz["quads"].tolist()])
    me.update()
    vv = npz["verts"].astype(float)
    dpk = np.linalg.norm(vv - pocket[None, :], axis=1)
    pk_w = np.clip((POCKET_HL_R - dpk) / 3.0, 0.0, 1.0)                  # 口袋中心 POCKET_HL_R Å 以内染色，外沿 3 Å 渐变
    at_pk = me.attributes.new("pocket_w", "FLOAT", "POINT")
    at_pk.data.foreach_set("value", pk_w.astype(np.float32).tolist())
    surf = bpy.data.objects.new("cdk20_surface", me)
    sc.collection.objects.link(surf)
    me.shade_smooth()
    ms = bpy.data.materials.new("real_surface")
    ms.use_nodes = True
    nt = ms.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.70, 0.80, 0.95, 1)
    b.inputs["Roughness"].default_value = 0.18
    b.inputs["Coat Weight"].default_value = 0.6
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.05, 0.55
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
    # 口袋高亮（11-20 Gemini 审 3-04：真分子画面要标出口袋）：底色和透明度按 pocket_w 混到珊瑚红、略发光
    atn = nt.nodes.new("ShaderNodeAttribute")
    atn.attribute_name = "pocket_w"
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.inputs["A"].default_value = (0.70, 0.80, 0.95, 1)
    mixc.inputs["B"].default_value = (0.95, 0.26, 0.18, 1)
    nt.links.new(atn.outputs["Fac"], mixc.inputs["Factor"])
    nt.links.new(mixc.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (0.95, 0.20, 0.12, 1)
    emm = nt.nodes.new("ShaderNodeMath")
    emm.operation = "MULTIPLY"
    emm.inputs[1].default_value = 0.35
    nt.links.new(atn.outputs["Fac"], emm.inputs[0])
    nt.links.new(emm.outputs["Value"], b.inputs["Emission Strength"])
    amx = nt.nodes.new("ShaderNodeMix")
    amx.data_type = "FLOAT"
    amx.inputs["B"].default_value = 0.62
    nt.links.new(atn.outputs["Fac"], amx.inputs["Factor"])
    nt.links.new(mr.outputs["Result"], amx.inputs["A"])
    nt.links.new(amx.outputs["Result"], b.inputs["Alpha"])
    surf.data.materials.append(ms)

    ca = [(a[1], np.array(a[5:8]) - cen, a[8]) for a in at if a[3] == "CA"]
    cu = bpy.data.curves.new("cdk20_backbone", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.75 * A
    cu.bevel_resolution = 4
    cu.resolution_u = 6
    for k, (_, col) in enumerate(PLDDT):
        m = bpy.data.materials.new(f"plddt_{k}")
        m.use_nodes = True
        bb = m.node_tree.nodes["Principled BSDF"]
        bb.inputs["Base Color"].default_value = (*[c ** 2.2 for c in col], 1)
        bb.inputs["Roughness"].default_value = 0.3
        bb.inputs["Coat Weight"].default_value = 0.5
        cu.materials.append(m)

    def band(b_):
        return next(k for k, (lo, _) in enumerate(PLDDT) if b_ > lo)
    runs, cur = [], [ca[0]]
    for prev, r in zip(ca, ca[1:]):
        if r[0] != prev[0] + 1 or band(r[2]) != band(cur[-1][2]):
            runs.append(cur)
            cur = [prev, r] if r[0] == prev[0] + 1 else [r]
        else:
            cur.append(r)
    runs.append(cur)
    for run in runs:
        if len(run) < 2:
            continue
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(run) - 1)
        for bp, (_, p, _) in zip(sp.bezier_points, run):
            bp.co = tuple(p * A)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        sp.material_index = band(run[-1][2])
    bbo = bpy.data.objects.new("cdk20_backbone", cu)
    sc.collection.objects.link(bbo)

    # 配体：重原子球 + 键棍，挂在一个空物体（原点 = 配体重原子质心）下面，W4 让它动
    atoms, bonds = read_sdf(ligand, 1)
    heavy = [i for i, a in enumerate(atoms) if a[0] != "H"]
    lig_xyz = {i: np.array(atoms[i][1:4]) - cen for i in heavy}
    lc = sum(lig_xyz.values()) / len(lig_xyz)
    lig = bpy.data.objects.new("ligand", None)
    sc.collection.objects.link(lig)
    lig.location = Vector(lc * A)
    lig.rotation_mode = "QUATERNION"
    mats_e = {}
    for el_, col in ELEM_COL.items():
        m = bpy.data.materials.new("lig_" + el_)
        m.use_nodes = True
        bb = m.node_tree.nodes["Principled BSDF"]
        bb.inputs["Base Color"].default_value = (*[c ** 2.2 for c in col], 1)
        bb.inputs["Roughness"].default_value = 0.22
        bb.inputs["Coat Weight"].default_value = 0.8
        if el_ == "C":
            bb.inputs["Metallic"].default_value = 0.55
        bb.inputs["Emission Color"].default_value = (*[c ** 2.2 for c in col], 1)
        bb.inputs["Emission Strength"].default_value = 0.12
        mats_e[el_] = m
    for i in heavy:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42 * A, segments=32, ring_count=16, location=tuple((lig_xyz[i] - lc) * A))
        o = bpy.context.object
        o.name = f"lig_atom_{i}"
        bpy.ops.object.shade_smooth()
        o.data.materials.append(mats_e.get(atoms[i][0], mats_e["C"]))
        o.parent = lig
    for i, j, order in bonds:
        if i not in lig_xyz or j not in lig_xyz:
            continue
        pa, pb = Vector((lig_xyz[i] - lc) * A), Vector((lig_xyz[j] - lc) * A)
        mid, dv = (pa + pb) / 2, pb - pa
        for half, (p0, el_) in enumerate(((pa, atoms[i][0]), (pb, atoms[j][0]))):    # 两半按两端原子上色
            c = (p0 + mid) / 2
            bpy.ops.mesh.primitive_cylinder_add(radius=0.15 * A, depth=dv.length / 2, vertices=16, location=tuple(c))
            o = bpy.context.object
            o.name = f"lig_bond_{i}_{j}_{half}"
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = dv.to_track_quat("Z", "Y")
            bpy.ops.object.shade_smooth()
            o.data.materials.append(mats_e.get(el_, mats_e["C"]))
            o.parent = lig

    cam_d = bpy.data.cameras.new("real_cam")
    cam = bpy.data.objects.new("real_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = 36.0
    cam_d.clip_start = 0.01
    cam_d.clip_end = 100.0
    for name, pos, en, size in (("key", (-0.9, 0.9, 0.6), 60.0, 0.6), ("fill", (1.1, -0.2, 0.9), 18.0, 1.0), ("rim", (0.3, 1.0, -1.4), 45.0, 0.4)):
        ld = bpy.data.lights.new("real_" + name, "AREA")
        ld.energy, ld.size = en, size
        lo = bpy.data.objects.new("real_" + name, ld)
        sc.collection.objects.link(lo)
        lo.parent = cam
        lo.location = Vector(pos)
        lo.rotation_euler = (-Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.world = bpy.data.worlds.new("real_world")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.09, 1)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

    P = Vector(pocket * A)
    d = Vector(dirv).normalized()
    lens = 35.0
    fpx = lens / 36.0 * SD.OUT_W
    cam.rotation_mode = "QUATERNION"
    log = []
    for f in range(f0, f1 + 1):
        r = camj[f]["ring"]
        if not r:
            continue
        cx, cy, rp = r
        D0 = R_POCKET * fpx / max(rp, 40.0) * A
        D = D0 * (1.0 + REAL_PULL_K * pull(t, f))
        u = (f - f0) / max(1, f1 - f0)
        q = (-d).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(-8.0 + 16.0 * u))
        cam.location = P + d * D
        cam.rotation_quaternion = q
        cam_d.lens = lens
        cam_d.shift_x = (SD.OUT_W / 2 - cx) / SD.OUT_W                 # 11-21 改正号：shift_x 为正时轴上的点往左走（原来写反，口袋落在红环关于画面中心的镜像处）
        cam_d.shift_y = (cy - SD.OUT_H / 2) / SD.OUT_W
        for path, ob in (("location", cam), ("rotation_quaternion", cam), ("lens", cam_d), ("shift_x", cam_d), ("shift_y", cam_d)):
            ob.keyframe_insert(path, frame=f)
        if lig_motion is not None:
            dv_, ql = lig_motion(t, f, d, q)
            lig.location = Vector(lc * A) + Vector(dv_) * A
            lig.rotation_quaternion = ql
            lig.keyframe_insert("location", frame=f)
            lig.keyframe_insert("rotation_quaternion", frame=f)
        lp = cam.location
        log.append(dict(f=f, D_A=round(D / A, 2), k=D0 / D, ring=[round(cx, 1), round(cy, 1), round(rp, 1)],
                        lig=[round(x, 2) for x in (lig.location - P) / A]))
    SD.linear_all([cam, lig])
    lig_d = float(np.linalg.norm(lc - pocket))
    (W / "real_cam.json").write_text(json.dumps(dict(way_out=list(map(float, dirv)), clear=float(clear), ligand=str(ligand.name),
                                                     ligand_heavy_atoms=len(heavy), ligand_centroid_to_pocket_A=round(lig_d, 2), cam=log), indent=1), encoding="utf-8")
    print("DRILL real ligand", ligand.name, "heavy", len(heavy), "centroid→pocket Å", round(lig_d, 2), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "real.blend"))
    if mode == "stills":
        out = W / "real_stills"
        out.mkdir(parents=True, exist_ok=True)
        fl = [int(x) for x in frames[0].split(",")] if frames else [f0 + 2, (f0 + f1) // 2, f1 - 2]
        for f in fl:
            sc.frame_set(f)
            sc.render.filepath = str(out / f"r_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("DRILL real still", f, flush=True)
        return
    if os.environ.get("REAL_F0"):                                       # 返修几帧：REAL_F0=290 REAL_F1=313 DRILL_OVERWRITE=1 bash run_drill.sh W4 real
        f0, f1 = max(f0, int(os.environ["REAL_F0"])), min(f1, int(os.environ["REAL_F1"]))
    SD.render_range(W / "real.blend", W / "real", f0, f1, prefix="r_")


# ================================================================ 合成：叠化到真实层、墨线圈、标签、出处行
SRC_TOY = "Illustration (our toy model) · CDK20 case: Ren et al. 2023"
SRC_REAL = "CDK20: AlphaFold DB AF-Q8IZL9-F1 (predicted, CC BY 4.0) · 001 pose: our AutoDock Vina run"
SRC_SIZE = 30                                         # 出处行：Instrument Serif 30 px，深色底衬（11-20 Gemini 审 3-04：放大、加底衬、统一衬线体）
# 11-23（18 的 A1）：出处行移出字幕区——底衬左沿 x 64、上下沿 886–928（左中对齐，y 907）；OUR RE-DOCKING 标签底衬上沿 836（836–878）。
# 字体、字号、底衬颜色不变（3-03 位 2 同一做法；W4 借这里的 comp_frames，重合成时一起变）
LABEL_XY, LABEL_PLATE_Y = (76, 857), (836, 878)
SRC_XY, SRC_PLATE_Y = (76, 907), (886, 928)
PLATE = ((14, 16, 24), 0.66, 12, 8)
PLATE_REAL = ((14, 16, 24), 0.9, 12, 8)               # 11-23 Z18：真实层上 OUR RE-DOCKING 和 AlphaFold 出处行压在浅蓝蛋白管上，底衬 0.66 → 0.9（W4 借这里，一起变）
LABEL_REAL = "OUR RE-DOCKING (AutoDock Vina)"
NOTE_REAL = "001"
INK_RED = (232, 25, 15)
OUT_DIR = SD.ROOT / "导演检查_20261123"          # 11-23 A1/A5 重合成出新片，11-21 的旧片留着
OUT_MP4 = OUT_DIR / "16_钻取_5-04.mp4"


def _lum_box(a, box):
    x0, y0, x1, y1 = box
    a = a[y0:y1, x0:x1].astype("float32") / 255
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())


def comp_frames(seg, flist=None, *, Tcls=None, src_toy=SRC_TOY, src_real=SRC_REAL, label=LABEL_REAL, note=NOTE_REAL, src_alpha=None,
                note_at=None, pulses=None, note_style=None):
    """生成合成后的帧（uint8 RGB）。src_alpha(t, f) 给出处行整体透明度（段首淡入、段尾淡出）。
    note_at(t) -> (起, 落)：手写编号落下的帧（默认 001 这个词）；pulses(t) -> [帧]：口袋墨线圈跳一下的帧。"""
    import numpy as np
    from PIL import Image, ImageFilter
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = (Tcls or T)(EV)
    NF = K["len_f"]
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]
    ri0, ri1, ro0, ro1 = t.real_in[0], t.real_in[1], t.real_out[0], t.real_out[1]
    rk = {c['f']: c['k'] for c in json.loads((W / 'real_cam.json').read_text(encoding='utf-8'))['cam']} if (W / 'real_cam.json').exists() else {}
    lum_p = W / "src_lum.json"
    if lum_p.exists() and len(json.loads(lum_p.read_text())) == NF:
        lum = json.loads(lum_p.read_text())
    else:
        lum = []
        for f in range(NF):
            im = Image.open(W / "frames" / f"f_{f:04d}.png").convert("RGB").reduce(4)
            lum.append(_lum_box(np.asarray(im), (16, 250, 260, 270)))
        lum_p.write_text(json.dumps(lum))
    sm = [sum(lum[max(0, f - 20):f + 21]) / len(lum[max(0, f - 20):f + 21]) for f in range(NF)]  # noqa: F841（旧的自动选字色用，留着）
    n0, n1 = note_at(t) if note_at else (t.name[0], t.name[1])
    pulses_ = pulses(t) if pulses else t.pushes[:2]
    yy, xx = np.mgrid[0:SD.OUT_H, 0:SD.OUT_W].astype(np.float32)
    if src_alpha is None:
        src_alpha = lambda t_, f: ramp(f, 10, 30) * (1 - ramp(f, t_.rush[0], t_.rush[0] + 8))  # noqa: E731
    for f in (flist if flist is not None else range(NF)):
        img = np.asarray(Image.open(W / "frames" / f"f_{f:04d}.png").convert("RGB")).astype(np.float32) / 255
        out = img
        a_real = 0.0
        ring = camj[f]["ring"]
        rp = W / "real" / f"r_{f:04d}.png"
        if ri0 <= f <= ro1 and ring and rp.exists():
            rl = np.asarray(Image.open(rp).convert("RGBA")).astype(np.float32) / 255
            cx, cy, r = ring
            dist = np.hypot(xx - cx, yy - cy)
            far = float(max(np.hypot(cx, cy), np.hypot(SD.OUT_W - cx, cy), np.hypot(cx, SD.OUT_H - cy), np.hypot(SD.OUT_W - cx, SD.OUT_H - cy)))
            if f <= ri1:
                u = smooth((f - ri0) / (ri1 - ri0))
            elif f >= ro0:
                u = 1.0 - smooth((f - ro0) / (ro1 - ro0))
            else:
                u = 1.0
            a_real = u
            R = u * (far + 160) - 80
            mask = np.clip((R - dist) / 160 + 0.5, 0, 1)
            bg = np.asarray(Image.fromarray((img * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
            bg = bg * 0.28 + np.array([0.035, 0.045, 0.075], np.float32) * 0.72
            real = rl[..., :3] * rl[..., 3:4] + bg * (1 - rl[..., 3:4])
            out = img * (1 - mask[..., None]) + real * mask[..., None]
        pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
        if ring and ri0 <= f <= ro1 and a_real > 0:
            k = ramp(f, ri1 - 10, ri1 + 8) * (1 - ramp(f, ro0 - 8, ro0 + 6))
            cx, cy, r = ring
            r = r * rk.get(f, 1.0)
            if k > 0.003:
                pz = sum(settle(f, p_, 0.09, n=1.0, dur=16) for p_ in pulses_)   # 口袋圈在点名的词 / 拍上跳一下
                rr = r * 0.98 * (1 + max(0.0, pz))
                rot = 0.35 * (f - ri0)
                pil = Image.alpha_composite(pil, SD.dashed_circle(cx, cy, rr, 9.0, (255, 250, 244), 0.55 * k, rot=rot))
                pil = Image.alpha_composite(pil, SD.dashed_circle(cx, cy, rr, 5.0, INK_RED, 1.0 * k, rot=rot))
            kn = ramp(f, n0, n1, ease_out) * (1 - ramp(f, ro0 - 8, ro0 + 6))
            if kn > 0.003:
                ns = dict(size=78, color=INK_RED, stroke=(3, (255, 250, 244)))
                ns.update(note_style or {})                                  # W4 的 048（11-23 Z25）：深红、白描边 6、字 ×1.4
                items = [dict(text=note, xy=(cx + r * 0.74, cy - r * 0.78 - 14 * (1 - kn)), size=ns["size"], color=ns["color"], hand=True, anchor="ls",
                              stroke=ns["stroke"], shadow=False)]
                pil = Image.alpha_composite(pil, SD.draw_text_layer(items, lambda it: kn))
            kl = ramp(f, ri1 - 16, ri1 + 4) * (1 - ramp(f, ro0 - 2, ro0 + 14))
            if kl > 0.003:                                                   # 标签放出处行上面一行、同样深色底衬（11-21 Gemini 审 W4：压在蛋白和墨线圈上挡科学画面）
                items = [dict(text=label, xy=LABEL_XY, size=36, color=(244, 240, 232), anchor="lm", shadow=False, plate=PLATE_REAL, plate_y=LABEL_PLATE_Y)]
                pil = Image.alpha_composite(pil, SD.draw_text_layer(items, lambda it: kl))
        base_a = src_alpha(t, f)
        it_t = dict(text=src_toy, xy=SRC_XY, size=SRC_SIZE, color=(240, 238, 232), anchor="lm", shadow=False, plate=PLATE, plate_y=SRC_PLATE_Y)
        it_r = dict(text=src_real, xy=SRC_XY, size=SRC_SIZE, color=(240, 238, 232), anchor="lm", shadow=False, plate=PLATE_REAL, plate_y=SRC_PLATE_Y)
        for it_, a_ in ((it_t, clamp(1 - 2 * a_real)), (it_r, clamp(2 * a_real - 1))):   # 两行各画一层（底衬不互相盖掉字）
            if base_a * a_ > 0.003:
                pil = Image.alpha_composite(pil, SD.draw_text_layer([it_], lambda it, _a=a_: base_a * _a))
        yield f, np.asarray(pil.convert("RGB"))


def comp(seg, *a):
    import time
    W = SD.work(seg)
    if a and a[0] == "frames":
        from PIL import Image
        fl = [int(x) for x in a[1].split(",")]
        (W / "comp_stills").mkdir(exist_ok=True)
        for f, im in comp_frames(seg, fl):
            Image.fromarray(im).save(W / "comp_stills" / f"c_{f:04d}.png")
        print("DRILL comp stills", fl, flush=True)
        return
    wav = W / "mix.wav"
    if not wav.exists():
        audio(seg)
    tt = time.time()
    n = SD.encode((im for _, im in comp_frames(seg)), wav, OUT_MP4, W / "enc")
    (W / "comp_time.txt").write_text(str(round(time.time() - tt, 1)))
    print("DRILL comp", OUT_MP4, n, "帧", round(time.time() - tt, 1), "s", flush=True)


# ================================================================ 声音（合成的塑料声，落在事件帧上）
def _sfx():
    C = SD.click
    return dict(
        snap=lambda s, g=0.20: C([(3100, 1.0), (5200, 0.5)], 9, 3, g, s),
        clack=lambda s, g=0.24: C([(900, 1.0), (1900, 0.6), (3300, 0.3)], 22, 5, g, s),
        thunk=lambda s, g=0.26: C([(260, 1.0), (520, 0.5), (1400, 0.25)], 40, 6, g, s),
        tick=lambda s, g=0.10: C([(2400, 1.0), (4100, 0.4)], 6, 2, g, s),
        ratchet=lambda s, g=0.07: C([(3600, 1.0), (6100, 0.3)], 4, 1.5, g, s))


def audio(seg):
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]

    def pan(f, key="sock"):
        x = camj[min(f, len(camj) - 1)][key][0]
        return clamp(0.5 + 0.35 * (x / SD.OUT_W - 0.5) * 2, 0.15, 0.85)

    def mini_pan(i):
        return clamp(0.42 + 0.06 * (i % 5), 0.3, 0.75)
    X = _sfx()
    hits = [(0, SD.whoosh(0.28, 0.12, 30, f0=500, f1=3000), 0.65),
            (t.open1[1], X["thunk"](4, 0.12), pan(t.open1[1])),
            (t.swap[0] + 2, X["clack"](6, 0.16), pan(t.swap[0])), (t.p001[1], X["clack"](7, 0.26), pan(t.p001[1])),
            (t.drill[0], SD.whoosh((t.drill[1] - t.drill[0]) / SD.FPS, 0.08, 8, f0=400, f1=2600), 0.5),          # 钻进孔底、退回：轻风声
            (t.real_out[0], SD.whoosh((t.drill_out[1] - t.real_out[0]) / SD.FPS, 0.06, 9, f0=2600, f1=500), 0.5)]
    w0, w1, _ = t.twist
    for k in range(3):
        f = int(w0 + (w1 - w0) * (k + 1) / 3)
        hits.append((f, X["tick"](10 + k), pan(f)))
    hits += [(w1, X["thunk"](13, 0.14), pan(w1)), (w1 + 3, X["tick"](14, 0.06), pan(w1)), (w1 + 6, X["tick"](15, 0.05), pan(w1)),
             (w1 + 21, X["clack"](16, 0.10), pan(w1)),
             (t.out[1] - 6, X["clack"](17, 0.18), pan(t.out[1])), (t.close[1], X["thunk"](18, 0.22), pan(t.close[1]))]
    for f in range(t.turn[0], t.stop, 9):                                 # 旋钮的棘轮：一格一响
        hits.append((f, X["ratchet"](40 + f % 97, 0.05), 0.3))
    hits.append((t.tick, X["tick"](20, 0.08), 0.3))
    for key, i in MINI_EV.items():
        s, l, e = t.m_in[key]
        hits.append((s + 6, X["clack"](50 + i, 0.08), mini_pan(i)))       # ATP 被顶出
        hits.append((l, X["clack"](60 + i, 0.13), mini_pan(i)))           # 001 到底
        if key in t.m_off:
            o1 = t.m_off[key][1]
            hits.append((o1 - 2, X["snap"](70 + i, 0.15), mini_pan(i)))    # 卡扣
            hits.append((o1, X["thunk"](80 + i, 0.10), mini_pan(i)))       # 灯灭
    hits += [(t.stop, X["thunk"](90, 0.20), 0.3), (t.stop + 3, X["tick"](91, 0.05), 0.3), (t.stop + 6, X["tick"](92, 0.04), 0.3),
             (t.rush[0] - 4, SD.whoosh((t.rush[1] - t.rush[0] + 10) / SD.FPS, 0.24, 31, f0=250, f1=2200), 0.3)]
    SD.mix_audio(seg, hits, W / "mix.wav")
    (W / "audio_hits.json").write_text(json.dumps([[h[0], round(h[2], 2)] for h in hits]), encoding="utf-8")


# ================================================================ 自检
def check(seg, out_mp4=None, luma_until=None, sync=True):
    import os
    import subprocess
    import numpy as np
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    NF = K["len_f"]
    out_mp4 = Path(out_mp4) if out_mp4 else OUT_MP4
    if luma_until is None:
        luma_until = T(EV).rush[0] - 2
    res = {}
    fr = SD.ff_frames(out_mp4, scale=(320, 180)).astype(np.float32) / 255
    res["video_frames"] = int(len(fr))
    res["expected_frames"] = NF
    luma = (0.2126 * fr[..., 0] + 0.7152 * fr[..., 1] + 0.0722 * fr[..., 2]).mean(axis=(1, 2))
    res["black_frames"] = [int(i) for i in np.where(luma < 0.03)[0]]
    res["luma_jumps_gt_0.06"] = [[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma))
                                 if abs(luma[i] - luma[i - 1]) > 0.06 and i < luma_until]
    res["luma_jumps_after_designed_cut"] = [[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(max(1, luma_until), len(luma))
                                            if abs(luma[i] - luma[i - 1]) > 0.06]
    res["luma_every_30"] = [round(float(x), 3) for x in luma[::30]]
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(out_mp4), "-map", "0:a", "-f", "null", "-"], capture_output=True, text=True)
    res["audio_ok"] = pr.returncode == 0
    if sync:
        M = json.loads((SD.MAPD / "master_v1.json").read_text(encoding="utf-8"))
        g = dict(next(x for x in M["groups"] if x["group"] == seg or seg in x["segs"]))
        g["events"] = K["events"]
        tmp_map = W / "map_with_events.json"
        tmp_map.write_text(json.dumps(dict(fps=M.get("fps", 60), groups=[g]), ensure_ascii=False), encoding="utf-8")
        py = SD.ROOT / "_env/footage/Scripts/python.exe"
        r = subprocess.run([str(py), str(SD.MAPD / "check_sync.py"), str(out_mp4), seg], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(SD.ROOT), env=dict(os.environ, PYTHONIOENCODING="utf-8", CDK20_MAP=str(tmp_map)))
        cs = SD.MAPD / "_reports" / f"sync_{seg}_{out_mp4.stem}.json"
        res["check_sync_out"] = (r.stdout[-3000:] + r.stderr[-800:]).strip()
        if cs.exists():
            res["check_sync"] = json.loads(cs.read_text(encoding="utf-8"))
    clip = W / "clip.json"
    if clip.exists():
        res["clip"] = {k: v for k, v in json.loads(clip.read_text(encoding="utf-8")).items() if k != "hits"}
    (W / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL check", json.dumps({k: v for k, v in res.items() if k not in ("check_sync", "luma_every_30")}, ensure_ascii=False, default=str)[:5000], flush=True)
    return res


def sheet(seg, step="6", out_mp4=None, prefix="16_钻取_5-04"):
    from PIL import Image, ImageDraw, ImageFont
    step = int(step)
    fr = SD.ff_frames(Path(out_mp4) if out_mp4 else OUT_MP4, scale=(384, 216))
    idx = list(range(0, len(fr), step))
    cols, rows = 6, 6
    fnt = ImageFont.truetype(str(SD.FONTS / "InterTight.ttf"), 18)
    pages = []
    for p in range(0, len(idx), cols * rows):
        chunk = idx[p:p + cols * rows]
        im = Image.new("RGB", (cols * 388 + 4, ((len(chunk) + cols - 1) // cols) * 220 + 4), (20, 20, 22))
        dr = ImageDraw.Draw(im)
        for k, i in enumerate(chunk):
            x, y = 4 + (k % cols) * 388, 4 + (k // cols) * 220
            im.paste(Image.fromarray(fr[i]), (x, y))
            dr.rectangle([x, y, x + 58, y + 22], fill=(0, 0, 0))
            dr.text((x + 4, y + 2), str(i), font=fnt, fill=(255, 255, 255))
        name = f"{prefix}_抽帧_{len(pages) + 1:02d}.jpg"
        im.save(SD.work(seg) / name, quality=86)
        pages.append(name)
    (SD.work(seg) / "sheets.json").write_text(json.dumps(dict(step=step, pages=pages, frames=idx)), encoding="utf-8")
    print("DRILL sheet", pages, flush=True)


def publish_sheets(seg):
    """抽帧页从工作目录拷到导演检查文件夹（看完、确认要给导演看的才拷）。"""
    import shutil
    sh = json.loads((SD.work(seg) / "sheets.json").read_text(encoding="utf-8"))
    for n in sh["pages"]:
        shutil.copyfile(SD.work(seg) / n, OUT_DIR / n)
    print("DRILL published", sh["pages"], flush=True)


# ================================================================ 报告（5-04 和 W4 一页，给导演的 html）
def report(seg=None):
    import html
    e = html.escape
    segs = [("5-04", "16_钻取_5-04.mp4", "旁白段 · 23.7 秒"), ("W4", "16_钻取_W4.mp4", "音乐段 · Sacrifice 16 拍"),
            ("3-04", "16_钻取_3-04.mp4", "旁白段 · 17.2 秒 · 按 Gemini 必改返修")]
    body = []
    concl_all = []
    for sg, mp4, sub in segs:
        W = SD.WORK_ROOT / "drill" / sg
        rd = lambda n: json.loads((W / n).read_text(encoding="utf-8")) if (W / n).exists() else {}  # noqa: E731
        chk, rv, sh = rd("check.json"), rd("review.json"), rd("sheets.json")
        if not rv:
            body.append(f"<h2>{e(sg)}</h2><p class=sub>还没做完。</p>")
            continue
        concl_all.append(f"<p><b>{e(sg)}</b>：{rv.get('conclusion', '')}</p>")
        try:
            K, _ = SD.load_keys(sg)
        except Exception:
            K = dict(events=[])
        times = [tuple(x) for x in rv.get("times", [])]
        rows_ev = "".join(
            f"<tr><td>{e(x['id'])}</td><td>{e(x['verb'])}</td><td>{e(str(x.get('w') or x.get('beat', '')))}</td><td class=n>{x['f_start']}</td><td class=n>{x['f_land']}</td>"
            f"<td class=n>{x['f_end']}</td><td class=n>{x['f_land'] / 60:.2f}</td><td>{e(x.get('means', ''))}</td></tr>" for x in K["events"])
        rows_ck = "".join(f"<tr class={'ok' if it['ok'] else 'bad'}><td>{e(it['item'])}</td><td>{'通过' if it['ok'] else '未过'}</td><td>{e(it['note'])}</td></tr>"
                          for it in rv.get("items", []))
        sheets = "".join(f'<figure><img src="{e(p)}" loading="lazy"><figcaption>{e(sg)} 抽帧第 {i + 1} 页（每 6 帧一张，左上角是段内帧号）</figcaption></figure>'
                         for i, p in enumerate(sh.get("pages", [])))
        sync = e(chk.get("check_sync_out", "")[-2000:]) if chk.get("check_sync_out") else e(json.dumps(rv.get("beat_check", {}), ensure_ascii=False, indent=1))
        s4_only = "总判： 不过" in sync and all("不过" not in x for x in sync.splitlines() if x.strip()[:2] in ("S1", "S2", "S3"))
        if s4_only:
            sync += "\n（这里“不过”只因为 S4 帧率项；S4 在原始渲染帧上同样报，是误报，见上面自检表的“帧率”一行）"   # 只有 S4 不过时给导演一句话
        body.append(f"""<h2>{e(sg)} · {e(sub)}</h2>
<video src="{e(mp4)}" controls preload="metadata"></video>
<h3>这段做了什么</h3><ul>{''.join(f'<li>{e(x)}</li>' for x in rv.get('design', []))}</ul>
<h3>自检（逐条）</h3><div class=tw><table><tr><th>检查项</th><th>结果</th><th>说明</th></tr>{rows_ck}</table></div>
<h3>对拍</h3><pre>{sync}</pre>
<h3>渲染时长</h3><div class=tw><table><tr><th>步骤</th><th>用时</th></tr>{''.join(f'<tr><td>{e(a)}</td><td>{e(b)}</td></tr>' for a, b in times)}</table></div>
<h3>事件表（帧 = 段内 60 fps）</h3><div class=tw><table><tr><th>事件</th><th>动作</th><th>词 / 拍</th><th>起</th><th>落</th><th>止</th><th>落(秒)</th><th>画面</th></tr>{rows_ev}</table></div>
<h3>抽帧</h3>{sheets}""")
    extra = ""
    p_extra = SD.WORK_ROOT / "drill" / "report_extra.json"
    if p_extra.exists():
        ex = json.loads(p_extra.read_text(encoding="utf-8"))
        extra = "".join(f"<h2>{e(sec['title'])}</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in sec['items'])}</ul>" for sec in ex)
    doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>插座三段钻取</title>
<style>
:root{{--bg:#f6f5f1;--fg:#1b1b1d;--soft:#5d5d63;--line:#d9d6ce;--ok:#1d7a3a;--bad:#b3261e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--fg:#ecebe6;--soft:#a3a3a8;--line:#333338;--ok:#5cc27e;--bad:#ff8a80;--card:#1d1d20}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 16px 80px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:21px;margin:44px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}} h3{{font-size:17px;margin:26px 0 8px}}
.sub{{color:var(--soft);margin:0 0 18px}} .concl{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--ok);padding:10px 18px;border-radius:6px}}
video{{width:100%;border-radius:6px;background:#000}} ul{{padding-left:22px}} li{{margin:4px 0}} pre{{white-space:pre-wrap;font-size:13px;background:var(--card);border:1px solid var(--line);padding:10px;border-radius:6px;overflow-x:auto}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}}
th,td{{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}} th{{background:rgba(127,127,127,.12)}}
td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} tr.ok td:nth-child(2){{color:var(--ok);font-weight:600}} tr.bad td:nth-child(2){{color:var(--bad);font-weight:600}}
figure{{margin:16px 0}} figure img{{width:100%;border-radius:4px}} figcaption{{color:var(--soft);font-size:13px}}
</style></head><body><main>
<h1>插座三段：5-04、W4 三维钻取 + 3-04 返修</h1>
<p class=sub>HKBU SCIE1007 课程作业的科普视频 · 玩具比喻，分子姿态是我们自己用 AutoDock Vina 重新对接的（画面标 OUR RE-DOCKING），蛋白是 AlphaFold DB 预测模型 · 1080p60 · 2026-11-21（韩国时间）</p>
<div class=concl>{''.join(concl_all)}</div>
{extra}
{''.join(body)}
<p class=sub>代码：镜头设计_v3/inserts/shot_drill.py（通用引擎）+ drill_504.py、drill_W4.py、drill_304.py（三段配方）+ run_drill.sh；事件表 映射/events/5-04.json、3-04.json，W4 拍点表 音乐/卡点/W4_Sacrifice.json；中间文件在 G:/cdk20/work/drill/。</p>
</main></body></html>"""
    out = OUT_DIR / "16_钻取_检查.html"
    out.write_text(doc, encoding="utf-8")
    print("DRILL report", out, flush=True)
