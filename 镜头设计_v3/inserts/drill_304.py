"""HKBU SCIE1007 课程作业的科普视频：第一段三维钻取 3-04 —— 镜头钻进"CDK20 插座"（设计：深化/06_插座比喻.md 第四节 3-04，11-20）。

"Our lock is CDK20. It's an enzyme, a protein with a chemical job. Its keyhole is a pocket where it normally grabs a small
molecule called ATP. Plug that pocket with the right key, and the enzyme can't do its job."

一镜到底（引擎 shot_drill.py，帧号全部来自 映射/keys/3-04.json）：
  T5  段首：3-03 留下的金钥匙（就是 048 假插头，钥匙杆 = 刀片）从镜头前飞过，完全虚化，遮住接缝。
  流  鼓包从锁那一格沿连杆往上，绕过口袋那一格，走到 CDK20 那一格的浇口；镜头跟着走。
  拔  插座（H01b，0.7 倍，躺在格子里，孔口朝上）绷一下，浇口断开，弹起，在空中转正（孔口朝镜头、盖在上）。
  开  "enzyme" 盖绕后沿铰链翻开（过冲回落），镜头进机舱：ATP 插着、灯亮，光包沿透明管流到活塞，活塞推小细胞。
  拔出 "keyhole" ATP 被顶出，飘到孔口左前方；盖合上，镜头绕到正面。
  钻  "pocket" 红环亮，镜头沿插孔轴推进；叠化到 AlphaFold DB 的 CDK20 预测模型（口袋墨线圈出，标 predicted model），再对称退回。
  插  "molecule called ATP" ATP 飞回插进去，灯亮。
  顶替 "Plug that pocket" 048 从右边进画，ATP 被顶出让开，048 插到底；"the right key" 拧卡口 90°，红色卡扣扣上。
  停  "the enzyme" 盖再翻开；"can't" 光包停在管里、活塞停在半程、细胞停、灯灭。之后镜头后拉，T2 甩镜接 3-05。
不穿模靠两件事：路径按零件几何设计（插头只沿孔轴进出、两插头错开轴线、转正前先升到包络半径以上），渲染前 clip 逐帧 BVH 查。
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

SEG = "3-04"
BOARD = SD.WORK_ROOT / "kit" / "board_final.blend"
STRUCT = SD.WORK_ROOT / "structures" / "AF-Q8IZL9-F1-model_v6.pdb"
SURF = SD.WORK_ROOT / "kit" / "cdk20.npz"           # 同一个模型的重原子软表面（Å，中心在重原子质心），口袋中心来自我们重新对接的 048
S = 0.7                                              # 插座、插头缩放（hero 55 mm 宽 → 挂进一格）
BC = (-7.7, -0.2, -3.95)                             # 插座外形包围盒中心（局部毫米）
H_FLOAT = 30.0                                       # 弹起后，插座中心离板面多高（毫米）
FACE = (-0.10, -1.0, 0.21)                           # 转正后孔口（+W）朝向：朝镜头，略往上仰
H_ATP = (24.0, -40.0, -8.0)                          # ATP 待机位（局部毫米，插头原点 = 凸缘前面）
H48_FIRST = (44.0, 24.0, 6.0)                        # 048 第一次停的位置："红环前方一个身位"
H48_OUT = (70.0, 48.0, 8.0)                          # 048 在机舱镜头期间待在画外
H48_IN = (48.0, 24.0, 4.0)                           # "Plug" 进画后停的位置
LID_OPEN = 104.0                                     # 盖翻开的角度（过冲到 109，铰链极限 110）
FSTOP = dict(board=3.5, cabin=7.0, front=6.0, drill=14.0)          # 传感器 8 mm（shot_drill.SENSOR）下的光圈
R_POCKET = 12.0                                      # 真实层：口袋墨线圈的半径（Å），叠化时对齐到红环


# ================================================================ 时间表
class T:
    """从 keys 读出的帧（段内 60 fps）。"""
    def __init__(self, EV):
        self.EV = EV
        g = lambda i, k="f_land": EV[i][k]  # noqa: E731
        self.wipe = (g("wipe", "f_start"), g("wipe"))
        self.pulse = (g("pulse", "f_start"), g("pulse"))
        self.tick, self.brk = g("sock_eject", "f_start"), g("sock_eject")
        self.turn = (g("sock_turn", "f_start"), g("sock_turn"))
        self.prep = (g("lid_prep", "f_start"), g("lid_prep"))
        self.open1 = (g("lid_open", "f_start"), g("lid_open"), g("lid_open", "f_end"))
        self.packet0 = g("packet", "f_start")
        self.push0 = g("piston_push")
        self.atp_out = (g("atp_out", "f_start"), g("atp_out"), g("atp_out", "f_end"))
        self.dim1 = (g("lamp_dim", "f_start"), g("lamp_dim", "f_end"))
        self.close = (g("lid_close", "f_start"), g("lid_close"), g("lid_close", "f_end"))
        self.ring = (g("ring_glow", "f_start"), g("ring_glow"), g("ring_glow", "f_end"))
        self.drill = (g("drill_in", "f_start"), g("drill_in"), g("drill_in", "f_end"))
        self.real_in = (g("real_in"), g("real_in", "f_end"))
        self.real_out = (g("real_out"), g("real_out", "f_end"))
        self.real0_in = (g("real0_in"), g("real0_in", "f_end"))            # 11-21：enzyme / a protein 上先出一次蛋白全貌（Gemini 必改）
        self.real0_out = (g("real0_out"), g("real0_out", "f_end"))
        self.cam_hold = (g("cam_hold"), g("cam_hold", "f_end"))            # 玩具层镜头在孔口停住的那段（原 real_out，玩具帧不重渲）
        self.note_protein = (g("note_protein"), g("note_protein", "f_end"))
        self.note_atp = (g("note_atp"), g("note_atp", "f_end"))
        self.drill_out = (g("drill_out", "f_start"), g("drill_out"))
        self.atp_free = (g("atp_free", "f_start"), g("atp_free"))
        self.atp_in = (g("atp_plug", "f_start"), g("atp_plug"), g("atp_plug", "f_end"))
        self.pon = (g("power_on", "f_start"), g("power_on", "f_end"))
        self.enter = (g("plug_enter", "f_start"), g("plug_enter"), g("plug_enter", "f_end"))
        self.swap = (g("atp_eject", "f_start"), g("atp_eject"), g("atp_eject", "f_end"))
        self.dim2 = (g("lamp_dim2", "f_start"), g("lamp_dim2", "f_end"))
        self.p48 = (g("plug048_in", "f_start"), g("plug048_in"), g("plug048_in", "f_end"))
        self.twist = (g("twist", "f_start"), g("twist"), g("twist", "f_end"))
        self.clamp = (g("clamp", "f_start"), g("clamp"), g("clamp", "f_end"))
        self.open2 = (g("lid_open2", "f_start"), g("lid_open2"), g("lid_open2", "f_end"))
        self.stop = g("stop")
        self.pull = (g("pull_back", "f_start"), g("pull_back"))
        self.whip = (g("whip", "f_start"), g("whip"))


# ================================================================ 机构的状态（纯函数：帧 → 数值）
def lid_angle(t, f):
    def opening(a, b, c):
        u = (f - a) / (b - a)
        if u <= 0:
            return 0.0
        if f <= b:
            return LID_OPEN * spring(u * 1.05, zeta=0.62, freq=0.62) if u < 1 else LID_OPEN
        return LID_OPEN + settle(f, b, 3.0, n=1.0, dur=c - b + 8)
    if f < t.open1[0]:
        return 0.0
    if f < t.close[0]:
        a = opening(*t.open1)
        return min(109.5, max(0.0, a))
    if f <= t.close[1]:
        u = (f - t.close[0]) / (t.close[1] - t.close[0])
        return LID_OPEN * (1 - ease_in(u, 2.4))
    if f < t.open2[0]:
        return max(0.0, abs(settle(f, t.close[1], 3.2, n=1.0, dur=t.close[2] - t.close[1] + 4)))
    return min(109.5, max(0.0, opening(*t.open2)))


def lamp_level(t, f):
    if f < t.dim1[0]:
        return 1.0
    if f < t.pon[0]:
        return lerp(1.0, 0.45, ramp(f, *t.dim1))
    if f < t.dim2[0]:
        return lerp(0.45, 1.0, ramp(f, t.pon[0], t.pon[0] + 10, ease_out))
    if f < t.stop:
        return lerp(1.0, 0.4, ramp(f, *t.dim2)) - 0.1 * ramp(f, t.dim2[1], t.stop)
    return lerp(0.3, 0.0, ramp(f, t.stop, t.stop + 4, ease_out))


def flow_speed(t, f):
    """光包的速度系数（1 = 45 帧走完一根管）：有真插头时 1；真插头走了只剩管里的余量，越爬越慢；can't 时停。"""
    if f >= t.stop:
        return 0.0
    if f < t.atp_out[0]:
        return 1.0
    if f < t.atp_in[1]:
        return lerp(1.0, 0.45, ramp(f, t.atp_out[0], t.atp_out[1]))
    if f < t.swap[0]:
        return 1.0
    return lerp(1.0, 0.044, ramp(f, t.swap[0], t.p48[1]))


def machine(t, nf):
    """逐帧模拟：光包出发、沿管走、到活塞触发一次推；返回每帧 (光包位置列表, 活塞值, 细胞缩放)。"""
    T_TUBE = 45.0
    deps = [t.packet0 + 4]
    while deps[-1] + 60 < t.atp_out[0]:
        deps.append(deps[-1] + 60)
    d = t.atp_in[1] + 3
    while d < t.swap[0] - 45:
        deps.append(d)
        d += 30

    def arrival(d0):
        s = 0.0
        for f in range(d0 + 1, nf):
            s += flow_speed(t, f) / T_TUBE
            if s >= 1.0:
                return f
        return 10 ** 6
    # 最后两颗：一颗在 can't 前 12 帧到活塞（推到一半停住），一颗停在管里
    d_x = min(range(t.swap[0] - 60, t.swap[0] - 2), key=lambda d0: abs(arrival(d0) - (t.stop - 12)))
    deps += [d_x, t.swap[0]]
    pos = {i: 0.0 for i in range(len(deps))}
    arrive = {}
    packets = []
    for f in range(nf):
        v = flow_speed(t, f) / T_TUBE
        cur = []
        for i, d0 in enumerate(deps):
            if f < d0 or i in arrive:
                continue
            if f > d0:
                pos[i] = min(1.0, pos[i] + v)
            if pos[i] >= 1.0:
                arrive[i] = f
                continue
            cur.append(pos[i])
        packets.append(cur)
    arr = sorted(arrive.values())
    # 活塞：到一颗推一次（推之前 6 帧缩回预备）；推的快慢跟着速度系数；can't 时停在原处
    pis, cel = [], []
    c = 1.0
    REST, PRE, OUT = 0.6, 0.0, 4.2
    growth_done = {}
    for f in range(nf):
        if f >= t.stop:
            pis.append(pis[-1])
            cel.append(cel[-1])
            continue
        p = REST
        for a in arr:
            if a - 6 <= f < a:
                p = lerp(REST, PRE, smooth((f - (a - 6)) / 6))
            sp = max(0.66, flow_speed(t, a))
            ext, back = 16 / sp, 30 / sp
            if a == arr[-1] and a < t.stop:
                ext = 2.0 * (t.stop - a)                 # 最后一下：can't 时正好推到一半
            if a <= f < a + ext:
                u = (f - a) / ext
                p = lerp(PRE, OUT, smoother(u))
                g0 = growth_done.get(a, c)
                growth_done.setdefault(a, c)
                c = g0 + 0.24 * (1.45 - g0) * smoother(u)
            elif a + ext <= f < a + ext + back:
                p = lerp(OUT, REST, smoother((f - a - ext) / back))
        pis.append(p)
        cel.append(min(1.45, c))
    return packets, pis, cel, dict(departures=deps, arrivals=arr)


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
    lock_cell, _ = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p21_lock"))
    pocket_cell, _ = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p20_pocket"))
    cx, cy = cell.matrix_world.translation.x, cell.matrix_world.translation.y
    print("DRILL cells", cell.name, lock_cell.name, pocket_cell.name, round(cx / MM, 1), round(cy / MM, 1), "zb", round(zb / MM, 1), flush=True)
    SD.hide_tree(old_part)
    for g in KP.gates_of(cell):
        SD.hide_tree(g)
    # 板脚：插座正下方那根会像柱子顶着它，这一镜去掉（照 2-03）
    for o in [o for o in board.children if o.name.startswith("foot") and (o.matrix_world.translation.xy - Vector((cx, cy))).length < 0.05]:
        bpy.data.objects.remove(o)

    Kt = KP.Kit()
    sock = S_.h01b_cdk20_socket(Kt)
    p48 = S_.h02b_plug(Kt, which="048")
    atp = S_.h02b_plug(Kt, which="ATP")
    for o in (p48, atp):
        o.parent = sock
        o.matrix_parent_inverse = Matrix.Identity(4)
    p48["drill_role"], atp["drill_role"], sock["drill_role"] = "048", "atp", "socket"
    rig = S_.rig(sock)
    S_.rest(sock)
    print("DRILL baked modifiers", SD.apply_modifiers(sock), flush=True)
    # 自带的 3 颗光包不用（自己做逐颗出发的光包）
    for ch in rig["flow"].children:
        SD.hide_tree(ch)

    # ---- 材质：灯珠单独一份（亮度可打关键帧），红环单独一份（会亮），光包一份
    lit = bpy.data.materials["kit_clear_yellow_lit"]
    lamp_m = lit.copy(); lamp_m.name = "drill_lamp_lit"
    for o in sock.children_recursive:
        if o.type == "MESH" and o.get("lamp") == "on":
            o.data.materials.clear(); o.data.materials.append(lamp_m)
    ring_m = bpy.data.materials["kit_red"].copy(); ring_m.name = "drill_ring_red"
    rings = [o for o in sock.children_recursive if o.type == "MESH" and "red_ring" in o.name]
    for o in rings:
        o.data.materials.clear(); o.data.materials.append(ring_m)
    ring_em = SD.add_emission(ring_m, (1.0, 0.04, 0.02), 0.0)      # 深红：AgX 下亮度高了会冲成白，强度压低

    # ---- 插座的位姿：躺在格子里（孔口朝上、盖朝板子上边）→ 弹起 → 转正 → 浮着
    q_lie = SD.basis_quat((0, 0, 1), up=(0, 1, 0))
    q_up = SD.basis_quat(FACE, up=(0, 0, 1))
    bc = Vector(BC) * MM * S
    C0 = Vector((cx, cy, zb))
    C1 = Vector((cx, cy + 4 * MM, zb + H_FLOAT * MM))

    def sock_center(f):
        h = 0.0
        if t.tick <= f < t.brk:                                         # 绷：往上被带一下
            h = 0.45 * MM * math.sin(math.pi * (f - t.tick) / (t.brk - t.tick))
        if f >= t.brk:
            u = (f - t.brk) / 46.0
            h = (H_FLOAT * MM) * spring(u, zeta=0.58, freq=0.85)
        c = C0 + Vector((0, 0, h))
        if f >= t.brk:                                                  # 弹起时顺带往板子里侧挪一点（让开下面的格子）
            c = c + (C1 - C0 - Vector((0, 0, H_FLOAT * MM))) * smoother((f - t.brk) / 50.0)
        if f >= t.turn[1]:
            c = c + Vector((0, 0, 0.25 * MM * math.sin(2 * math.pi * (f - t.turn[1]) / 160.0) * ramp(f, t.turn[1], t.turn[1] + 40)))
        dip = 0.0                                                        # 开盖前沉一下（预备），盖落下时被带一下
        if t.prep[0] <= f < t.prep[1] + 10:
            dip -= 0.6 * MM * (ramp(f, t.prep[0], t.prep[1], ease_in) if f < t.prep[1] else 1 - ramp(f, t.prep[1], t.prep[1] + 10, ease_out))
        dip += settle(f, t.close[1], -0.35 * MM, n=1.5, dur=12)
        return c + Vector((0, 0, dip))

    def sock_quat(f):
        if f < t.turn[0] + 4:
            return q_lie.copy()
        u = (f - t.turn[0] - 4) / (t.turn[1] - t.turn[0] - 4)
        k = spring(u, zeta=0.66, freq=0.75)
        if k <= 1:
            q = q_lie.slerp(q_up, max(0.0, k))
        else:                                                           # 过冲：绕世界 X 轴沿转动方向多转一点再回
            q = Quaternion((1, 0, 0), math.radians(90 * (k - 1))) @ q_up
        if f > t.turn[1]:
            q = q @ Quaternion((0, 0, 1), math.radians(0.35 * math.sin(2 * math.pi * (f - t.turn[1]) / 210.0)))
        return q

    def recoil(f):
        """插头到底、卡扣扣上时整台被顶一下（局部毫米，沿 −W）。"""
        return settle(f, t.atp_in[1], -0.25, n=1.2, dur=12) + settle(f, t.p48[1], -0.3, n=1.2, dur=12) + settle(f, t.clamp[1], -0.15, n=1.5, dur=10)

    mats = []
    for f in range(NF):
        q = sock_quat(f)
        R = q.to_matrix().to_4x4()
        c = sock_center(f)
        loc = c - (R.to_3x3() @ bc) + (R.to_3x3() @ Vector((recoil(f) * MM * S, 0, 0)))
        SD.key_xform(sock, f, loc=loc, quat=q, scale=(S, S, S))
        mats.append(Matrix.Translation(loc) @ R)
    M_float = Matrix.Translation(C1 - (q_up.to_matrix() @ bc)) @ q_up.to_matrix().to_4x4()

    def to_world(f, p_local_mm):
        return mats[f] @ (Vector(p_local_mm) * MM * S)

    # ---- 浇口：躺着时，从格子外圈左、右、下三边朝插座打射线
    sock.matrix_world = mats[0] @ Matrix.Diagonal((S, S, S, 1))
    bpy.context.view_layer.update()
    shell = [o for o in sock.children_recursive if o.type == "MESH" and "shell" in o.name and not o.hide_render]
    gates = SD.make_gates(cell, shell, [((-KP.CX, 4.0, 0), (1, 0, 0)), ((KP.CX, -4.0, 0), (-1, 0, 0)), ((0, -KP.CY, 0), (0, 1, 0))],
                          Kt.cat("blue"), cell.name + "_sock")
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    SD.break_gates(gates, t.tick, t.brk, scar)
    print("DRILL gates", [(g["cone"].name, round((g["tip"] - g["a"]).length / MM, 2)) for g in gates], flush=True)

    # ---- 机构：盖、灯、光包、活塞、细胞、红环
    packets_f, pis_f, cel_f, msched = machine(t, NF)
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
    lamp_lights = [o for o in sock.children_recursive if o.type == "LIGHT" and "lamp" in o.name]
    on_meshes = [o for o in sock.children_recursive if o.get("lamp") == "on"]
    off_meshes = [o for o in sock.children_recursive if o.get("lamp") == "off"]
    lamp_em = [n for n in lamp_m.node_tree.nodes if n.type == "EMISSION"][0]
    on_f = [lamp_level(t, f) > 0.02 for f in range(NF)]
    for o in on_meshes + off_meshes:
        want_on = o in on_meshes
        seq = [(0, not (on_f[0] if want_on else not on_f[0]))]
        for f in range(1, NF):
            if on_f[f] != on_f[f - 1]:
                seq += [(f - 1, not (on_f[f - 1] if want_on else not on_f[f - 1])), (f, not (on_f[f] if want_on else not on_f[f]))]
        SD.hide_tree(o, seq)
    for f in range(NF):
        S_.pose(sock, "lid", lid_angle(t, f))
        rig["lid"].keyframe_insert("rotation_euler", frame=f)
        S_.pose(sock, "piston", pis_f[f])
        rig["piston"].keyframe_insert("location", frame=f)
        S_.pose(sock, "cell", cel_f[f])
        rig["cell"].keyframe_insert("scale", frame=f)
        L = lamp_level(t, f)
        lamp_em.inputs["Strength"].default_value = 4.0 * L
        lamp_em.inputs["Strength"].keyframe_insert("default_value", frame=f)
        for lo_ in lamp_lights:
            lo_.data.energy = 0.03 * S * S * L
            lo_.data.keyframe_insert("energy", frame=f)
        cur = packets_f[f]
        for i, o in enumerate(pk_objs):
            vis = i < len(cur)
            o.location = S_._lerp_path(pipe, cur[i]) * MM if vis else o.location
            o.scale = (1, 1, 1) if vis else (0.001, 0.001, 0.001)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("scale", frame=f)
        g = 0.0
        if t.ring[0] <= f:
            g = 0.40 * ramp(f, t.ring[0], t.ring[1] + 6, ease_out) * (1 - ramp(f, t.ring[2], t.ring[2] + 24))
        ring_em.inputs["Strength"].default_value = g
        ring_em.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # ---- 插头：ATP（真插头）和 048（假插头），都挂在插座下面，位姿按局部毫米算（插头原点 = 凸缘前面，针朝 −W）
    SEATW = S_.SEAT_W
    axis_q = Quaternion()

    def atp_state(f):
        """返回 (位置 mm, 四元数)。"""
        a0, a1, a2 = t.atp_out
        if f < a0 - 4:
            return Vector((SEATW, 0, 0)), axis_q
        if f < a0:                                                       # 预颤：往里一点
            return Vector((SEATW + 0.15 * math.sin(math.pi * (f - a0 + 4) / 4), 0, 0)), axis_q          # 预颤只往外（往里会顶到触点）
        if f < a1:                                                       # 弹出：沿轴
            u = (f - a0) / (a1 - a0)
            return Vector((SEATW + 21.0 * ease_out(u, 2.6), 0, 0)), axis_q
        P0, P1 = Vector((SEATW + 21.0, 0, 0)), Vector(H_ATP)
        if f < t.atp_free[0]:
            u = ramp(f, a1, a2)
            p = P0.lerp(P1, u) + Vector((0, 0, 4.0 * math.sin(math.pi * u)))
            bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * (f - a2) / 140.0))) * ramp(f, a2, a2 + 30)
            return p + bob, Quaternion((0, 0, 1), math.radians(-6 * math.sin(math.pi * u)))
        b0, b1, b2 = t.atp_in
        fr0 = t.atp_free[0]
        hov = P1 + Vector((0, 0, 0.5 * math.sin(2 * math.pi * (fr0 - a2) / 140.0)))
        if f < b0:                                                       # 预颤（593–599）：往后缩一点
            return hov - Vector((0.5 * math.sin(math.pi * (f - fr0) / (b0 - fr0)), 0, 0)), axis_q
        APP = Vector((SEATW + 22.0, 0, 0))
        mid = b0 + int(0.62 * (b1 - b0))
        if f < mid:                                                      # 飞到孔轴前方（弧线）
            u = smoother((f - b0) / (mid - b0))
            p = hov.lerp(APP, u) + Vector((6.0 * math.sin(math.pi * u), 0, 3.0 * math.sin(math.pi * u)))
            return p, Quaternion((0, 0, 1), math.radians(12 * math.sin(math.pi * u)))
        if f < b1:                                                       # 沿轴插进去，最后 6 帧减速
            u = (f - mid) / (b1 - mid)
            return Vector((SEATW + 22.0 * (1 - ease_out(u, 2.2)), 0, 0)), axis_q
        s0, s1, s2 = t.swap
        if f < s0:
            return Vector((SEATW + max(0.0, settle(f, b1, 0.1, n=1.0, dur=b2 - b1)), 0, 0)), axis_q
        if f < s1:                                                       # 被顶出：沿轴弹出 22 mm
            u = (f - s0) / (s1 - s0)
            return Vector((SEATW + 22.0 * ease_out(u, 2.4), 0, 0)), axis_q
        P0 = Vector((SEATW + 22.0, 0, 0))
        u = ramp(f, s1, s2, lambda x: 1 - (1 - x) ** 4)
        p = P0.lerp(Vector(H_ATP), u) + Vector((0, -3.0 * math.sin(math.pi * u), 9.0 * math.sin(math.pi * u)))
        tumble = 22 * math.sin(math.pi * u) * (1 - u)
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * (f - s2) / 140.0))) * ramp(f, s2, s2 + 30)
        return p + bob, Quaternion((0, 1, 0), math.radians(tumble))

    # 鼓包的路（板面毫米）：锁那一格的上边 → 连杆 → 口袋那一格的右半圈 → 连杆 → CDK20 那一格的下边（浇口根）
    lx, ly = lock_cell.matrix_world.translation.x / MM, lock_cell.matrix_world.translation.y / MM
    px_, py_ = pocket_cell.matrix_world.translation.x / MM, pocket_cell.matrix_world.translation.y / MM
    X, Y0 = cx / MM, cy / MM
    rr = 5.0
    path = [(lx, ly + KP.CY, 1.2), (px_, py_ - KP.CY, KP.R_LOOP), (px_ + KP.CX - rr, py_ - KP.CY, KP.R_LOOP)]
    for k in range(1, 6):
        a = -math.pi / 2 + k * math.pi / 2 / 6
        path.append((px_ + KP.CX - rr + rr * math.cos(a), py_ - KP.CY + rr + rr * math.sin(a), KP.R_LOOP))
    path += [(px_ + KP.CX, py_ - KP.CY + rr, KP.R_LOOP), (px_ + KP.CX, py_ + KP.CY - rr, KP.R_LOOP)]
    for k in range(1, 6):
        a = k * math.pi / 2 / 6
        path.append((px_ + KP.CX - rr + rr * math.cos(a), py_ + KP.CY - rr + rr * math.sin(a), KP.R_LOOP))
    path += [(px_ + KP.CX - rr, py_ + KP.CY, KP.R_LOOP), (px_, py_ + KP.CY, KP.R_LOOP), (X, Y0 - KP.CY, 1.2)]
    mr = bpy.data.objects.get("main_runner")
    base_m = (mr.active_material if mr and mr.active_material else None) or bpy.data.materials["kit_white"]
    pulse, ppos, P2 = BG.guide_runner(path, t.pulse[0], t.pulse[1], zb / MM, BG.pulse_mat(base_m), name="drill_pulse", eat=6)
    pulse.scale = pulse.scale  # noqa

    # 048：段首 T5 从镜头前飞过 → 跟鼓包 → 停在红环前方一个身位 → 画外 → "Plug" 进画 → 插 → 拧
    # 需要镜头轨迹，先算镜头（键在下面），再回来烘焙 048。
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = 36.0
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0

    def sock_ctr_world(f):
        return to_world(f, BC)

    lock_c = lock_cell.matrix_world.translation
    keys = [
        dict(f=0, space="world", tgt=(lx * MM, (ly + 14) * MM, zb), az=-6, el=36, dist=0.175, lens=50),
        dict(f=t.pulse[0] + 8, space="world", tgt=(lx * MM, (ly + 16) * MM, zb), az=-6, el=36, dist=0.172, lens=50),
        dict(f=t.brk, space="world", tgt=(X * MM, (Y0 - 6) * MM, zb + 6 * MM), az=-8, el=34, dist=0.150, lens=50, ease="inout"),
        dict(f=t.turn[1] + 6, space="world", tgt=tuple(C1 + Vector((0, 0, -2 * MM))), az=-14, el=24, dist=0.140, lens=50),
        dict(f=t.prep[0], space="sock", tgt=(-4.0, 0.0, -2.0), az=-30, el=22, dist=170, lens=50),
        dict(f=t.open1[0], space="sock", tgt=(-5.0, 0.0, -3.0), az=-27, el=26, dist=158, lens=50),
        dict(f=EV["cam_cabin"]["f_land"], space="sock", tgt=(-6.0, 2.0, -8.0), az=-62, el=58, dist=92, lens=35),
        dict(f=t.push0, space="sock", tgt=(-9.0, -1.0, -8.0), az=-68, el=61, dist=82, lens=35),
        dict(f=t.atp_out[0], space="sock", tgt=(-2.0, 1.0, -7.0), az=-58, el=56, dist=94, lens=35),
        dict(f=EV["cam_front"]["f_land"], space="sock", tgt=(12.0, 0.0, 0.0), az=-22, el=17, dist=128, lens=50),
        dict(f=t.drill[0], space="sock", tgt=(12.0, 0.0, 0.0), az=-20, el=15, dist=122, lens=50),
        dict(f=t.drill[1], space="sock", tgt=(4.0, 0.0, 0.0), az=0, el=0, dist=58, lens=50),
        dict(f=t.drill[2], space="sock", tgt=(4.0, 0.0, 0.0), az=0, el=0, dist=52, lens=50, ease="linear"),
        dict(f=t.cam_hold[1], space="sock", tgt=(4.0, 0.0, 0.0), az=0, el=0, dist=58, lens=50),
        dict(f=t.drill_out[1], space="sock", tgt=(12.0, -2.0, 0.0), az=-26, el=16, dist=126, lens=50),
        dict(f=t.atp_in[2], space="sock", tgt=(12.0, -1.0, 0.0), az=-20, el=17, dist=122, lens=50),
        dict(f=EV["cam_side"]["f_land"], space="sock", tgt=(16.0, 5.0, 0.0), az=17, el=17, dist=132, lens=50),
        dict(f=t.p48[1], space="sock", tgt=(14.0, 2.0, 0.0), az=12, el=16, dist=112, lens=50),
        dict(f=t.twist[1], space="sock", tgt=(15.0, 4.0, 0.0), az=24, el=21, dist=92, lens=50),
        dict(f=t.open2[0], space="sock", tgt=(12.0, 0.0, 0.0), az=14, el=24, dist=110, lens=50),
        dict(f=EV["cam_cabin2"]["f_land"], space="sock", tgt=(-7.0, 0.0, -8.0), az=-62, el=58, dist=88, lens=35),
        dict(f=t.stop + 10, space="sock", tgt=(-10.0, -2.0, -8.0), az=-68, el=61, dist=80, lens=35),
        dict(f=t.pull[1], space="sock", tgt=(-3.0, 0.0, -3.0), az=-34, el=36, dist=205, lens=40, ease="inout"),
    ]
    # 鼓包期间：镜头目标跟着鼓包（±8 帧平均，拐角不顿），起动不早于 6 帧
    def pulse_follow(f):
        xs = [Vector(ppos(min(t.pulse[1], max(t.pulse[0], f + k)))) for k in range(-8, 9)]
        p = sum(xs, Vector()) / len(xs)
        return p
    rigc = SD.CamRig(keys, lambda f: mats[f], MM * S)
    base_at = rigc.at

    def at_with_pulse(f):
        eye, tgt, lens, roll = base_at(f)
        if f < t.brk:
            w = ramp(f, t.pulse[0] + 6, t.pulse[0] + 22) * (1 - ramp(f, t.pulse[1] - 6, t.brk + 2))
            tgt2 = pulse_follow(f) + Vector((0, 4 * MM, 0))
            d = tgt2 - tgt
            eye, tgt = eye + d * w, tgt + d * w
        return eye, tgt, lens, roll
    rigc.at = at_with_pulse
    for fs_, amp in ((t.brk, 0.22), (t.close[1], 0.18), (t.atp_in[1], 0.14), (t.p48[1], 0.18), (t.clamp[1], 0.16), (t.stop, 0.12)):
        rigc.shake(fs_, amp, 6)

    def drift(f, eye, tgt):
        d = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        k = 1.0 - 0.85 * (ramp(f, t.drill[0], t.drill[1]) * (1 - ramp(f, t.cam_hold[1], t.drill_out[1])))   # 钻的时候不漂（对位）
        off = (right * 0.010 * math.sin(f / 97.0) + up * 0.007 * math.cos(f / 131.0)) * d * k
        return off, off * 0.6
    recs = rigc.bake(cam, NF, drift=drift)
    # 甩镜（T2）：最后几帧镜头绕竖直轴往左甩（朝第 1 区的玻璃肝），越甩越快；真镜头运动 + 运动模糊
    w0, w1 = t.whip
    for f in range(w0, NF):
        u = (f - w0) / max(1, (w1 - w0))
        yaw = math.radians(78.0) * ease_in(u, 2.6)
        eye, tgt, lens, q = recs[f]
        q2 = Quaternion((0, 0, 1), yaw) @ q
        cam.rotation_quaternion = q2
        cam.keyframe_insert("rotation_quaternion", frame=f)
        recs[f] = (eye, tgt, lens, q2)

    # ---- 048 的轨迹（需要镜头）
    def cam_space(f, x, y, z):
        """镜头坐标（镜头前方 z 米、右 x、上 y）→ 世界。"""
        eye, _, _, q = recs[f]
        return eye + q @ Vector((x, y, -z))

    f_follow_end = EV["key_follow"]["f_land"]
    hov1_w = M_float @ (Vector(H48_FIRST) * MM * S)

    def p48_world(f):
        a, b = t.wipe
        if f <= b + 4:                                                  # T5：镜头前 28 mm，从左下往右上快速掠过
            u = (f - a + 2) / (b - a + 6)
            return cam_space(f, lerp(-0.030, 0.034, u), lerp(-0.006, 0.010, u), 0.028)
        lag = 14
        fp = min(t.pulse[1], max(t.pulse[0], f - lag))
        follow = Vector(ppos(fp)) + Vector((16 * MM, -10 * MM, 18 * MM))
        if f <= b + 18:                                                  # 从镜头前离开，接到鼓包后面
            u = smoother((f - b - 4) / 14.0)
            return cam_space(b + 4, 0.034, 0.010, 0.028).lerp(follow, u)
        if f < t.pulse[1] - 4:
            return follow
        u = ramp(f, t.pulse[1] - 4, f_follow_end)
        mid = follow.lerp(hov1_w, 0.5) + Vector((0, 0, 8 * MM))
        p = follow.lerp(mid, u) .lerp(mid.lerp(hov1_w, u), u)
        return p

    def p48_state(f):
        """返回 (局部位置 mm, 局部四元数, 拧角)。"""
        twist = 0.0
        if f < f_follow_end + 2:
            pw = p48_world(f)
            pl = mats[f].inverted() @ pw / (MM * S)
            # 朝向：段首在世界里大致朝前飞，渐渐转成和插孔同轴
            eye, _, _, qc = recs[min(f, NF - 1)]
            qw_fly = SD.basis_quat(qc @ Vector((1, 0.15, 0)), up=qc @ Vector((0, 1, 0)))   # 侧面对着镜头，像一把钥匙横着飞过
            q_loc_target = Quaternion()
            q_loc_fly = mats[f].to_quaternion().inverted() @ qw_fly
            u = ramp(f, t.pulse[1] - 10, f_follow_end)
            q = q_loc_fly.slerp(q_loc_target, u) @ Quaternion((1, 0, 0), math.radians(40 * math.sin(f / 9.0) * (1 - u)))
            return pl, q, twist
        e0, e1, e2 = t.enter
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * f / 150.0)))
        if f < t.open1[0] + 30:
            return Vector(H48_FIRST) + bob * ramp(f, f_follow_end, f_follow_end + 20), Quaternion(), twist
        if f < e0:
            u = ramp(f, t.open1[0] + 30, t.open1[0] + 90)
            return Vector(H48_FIRST).lerp(Vector(H48_OUT), u) + bob, Quaternion(), twist
        if f < e1:
            u = (f - e0) / (e1 - e0)
            return Vector(H48_OUT).lerp(Vector(H48_IN), ease_out(u, 2.4)) + bob, Quaternion((0, 0, 1), math.radians(-10 * (1 - ease_out(u)))), twist
        i0, i1, i2 = t.p48
        hov = Vector(H48_IN) + bob
        if f < i0:
            return hov + Vector((0, 0, settle(f, e1, 0.4, n=1.0, dur=12))), Quaternion(), twist
        APP = Vector((SEATW + 20.0, 0, 0))
        sw0 = max(i0, t.swap[1] + 8)                                    # ATP 让开轴线以后才摆过来
        mid = sw0 + int(0.5 * (i1 - sw0))
        if f < sw0:
            return hov, Quaternion(), twist
        if f < mid:                                                     # 从右前方摆到孔轴上
            u = smoother((f - sw0) / (mid - sw0))
            return Vector(H48_IN).lerp(APP, u) + Vector((5.0 * math.sin(math.pi * u), 0, 2.0 * math.sin(math.pi * u))), Quaternion((0, 0, 1), math.radians(-8 * math.sin(math.pi * u))), twist
        if f < i1:
            u = (f - mid) / (i1 - mid)
            return Vector((SEATW + 20.0 * (1 - ease_out(u, 2.2)), 0, 0)), Quaternion(), twist
        d = max(0.0, settle(f, i1, 0.1, n=1.0, dur=i2 - i1)) if f < i2 + 2 else 0.0
        w0_, w1_, w2_ = t.twist
        if f >= w0_:
            if f <= w1_:
                twist = 90.0 * smoother((f - w0_) / (w1_ - w0_))
            else:
                twist = 90.0 - abs(settle(f, w1_, 1.2, n=1.5, dur=w2_ - w1_))
        return Vector((SEATW + d, 0, 0)), Quaternion(), twist

    atp_track, p48_track = [], []
    for f in range(NF):
        pa, qa = atp_state(f)
        SD.key_xform(atp, f, loc=pa * MM, quat=qa)
        atp_track.append(tuple(pa))
        pl, ql, tw = p48_state(f)
        SD.key_xform(p48, f, loc=pl * MM, quat=ql)
        S_.pose(p48, "twist", tw)
        S_.rig(p48)["twist"].keyframe_insert("rotation_euler", frame=f)
        tab = S_.lug_tab_angle(tw)
        if f >= t.clamp[1]:
            tab = -25.0 + abs(settle(f, t.clamp[1], 1.2, n=1.5, dur=t.clamp[2] - t.clamp[1]))
        S_.pose(sock, "tab", tab)
        rig["tab"].keyframe_insert("rotation_euler", frame=f)
        p48_track.append(tuple(pl))

    # ---- 灯光：大板那套主光（以 CDK20 那一格为中心）+ 舱内补光（挂在插座上，开盖时亮）
    KP.lights(cx, cy, 1.0)
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
        a = lid_angle(t, f)
        fill.energy = 0.55 * S * S * clamp(a / 60.0) + 0.06
        fill.keyframe_insert("energy", frame=f)

    # ---- 焦点：引导表（焦点点名）+ 钻的时候钉在孔口
    plan = BG.plan_from_keys(K)

    def mouth_w(f):
        return to_world(f, (12.0, 0, 0))

    def output_w(f):
        p = pis_f[f]
        return to_world(f, (-13.5, -2.8 - p, -4.0))

    targets = dict(socket=lambda f: to_world(f, BC), seam=lambda f: to_world(f, (11.7, -8.0, 0.0)), output=output_w, keyhole=mouth_w,
                   atp=lambda f: to_world(f, tuple(Vector(atp_track[f]) + Vector((2.0, 0, 0)))),
                   entry=lambda f: to_world(f, tuple(Vector(p48_track[f]) + Vector((2.0, 0, 0)))))
    base = lambda f: Vector(ppos(min(t.pulse[1], max(t.pulse[0], f))))  # noqa: E731
    fpts = BG.focus_track(plan, targets, NF, base=base)
    for f in range(NF):                                                  # 钻：焦点在孔里（红环和触点面之间）
        w = ramp(f, t.ring[0] - 10, t.drill[1] - 20) * (1 - ramp(f, t.cam_hold[1], t.atp_in[0] + 20))
        if w > 0:
            fpts[f] = fpts[f].lerp(to_world(f, (8.0, 0, 0)), w)
        w2 = ramp(f, t.atp_in[1] - 20, t.atp_in[1]) * (1 - ramp(f, t.enter[0] - 6, t.enter[1] - 8))
        if w2 > 0:
            fpts[f] = fpts[f].lerp(mouth_w(f), w2)
        w3 = ramp(f, t.swap[0] - 10, t.swap[0]) * (1 - ramp(f, t.p48[1], t.p48[1] + 6))
        if w3 > 0:                                                       # 顶替：ATP 被顶出、048 插进去都发生在孔口，焦点钉在孔口（048 等候时虚着）
            fpts[f] = fpts[f].lerp(mouth_w(f), w3)
        if f < 12:                                                       # T5：焦点在远处（板上），前景金件完全虚化
            fpts[f] = base(f)
    # 光圈：分段（大板 / 正面 / 舱内 / 钻），换段时 24 帧平滑过渡
    phases = [(0, FSTOP["board"]), (t.prep[0], FSTOP["front"]), (t.open1[1], FSTOP["cabin"]), (t.atp_out[1] + 20, FSTOP["front"]),
              (t.drill[0] + 20, FSTOP["drill"]), (t.drill_out[1], FSTOP["front"]), (t.open2[1], FSTOP["cabin"]), (t.pull[0] + 20, FSTOP["front"])]
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    fst = []
    for f in range(NF):
        v = phases[0][1]
        for (fa, va), (fb, vb) in zip(phases, phases[1:] + [(10 ** 6, phases[-1][1])]):
            if fa <= f:
                v = va if f < fb - 12 else lerp(va, vb, smooth((f - fb + 12) / 24))
        fst.append(v)
        d.aperture_fstop = v
        d.keyframe_insert("aperture_fstop", frame=f)
    focus_d = []
    for f in range(NF):
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.focus_distance = max(0.003, (fpts[f] - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        focus_d.append(d.focus_distance)

    # ---- 轮廓光（灯光链接，只照被点名的零件；落点帧按当时镜头摆）
    key = bpy.data.objects["key"]
    rim_groups = dict(socket=[sock], seam=[o for o in sock.children_recursive if o.type == "MESH" and ("faceplate" in o.name or "shell" in o.name)],
                      output=[o for o in sock.children_recursive if o.type == "MESH" and any(k in o.name for k in ("piston", "cell_", "rod_pad"))],
                      keyhole=rings + [o for o in sock.children_recursive if o.type == "MESH" and "barrel" in o.name],
                      atp=[atp], entry=[p48])
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
        k_irr = key.data.energy / (key.matrix_world.translation - Vector(pts[0])).length ** 2     # 主光在这里的照度（近似）
        pw = 1.0 * k_irr * (3.0 * size) ** 2                         # 轮廓光离零件 3 倍尺寸，照度约和主光相当（只照边缘）
        lt = BG.guide_rim([it], rim_groups, cam, key, power=pw)
        rims.update(lt)
        for lo_ in lt.values():                                          # 灯跟着插座走（插座在动，灯不能留在原地）
            aim = bpy.data.objects[lo_.name + "_aim"]
            for ob in (lo_, aim):
                ob.parent = sock
                ob.matrix_parent_inverse = sock.matrix_world.inverted()       # 当前是落点帧：灯留在当时的位置，之后跟着插座走
    SD.linear_all([sock, atp, p48, cam, pulse] + list(sock.children_recursive) + list(atp.children_recursive) + list(p48.children_recursive)
                  + [o for o in bpy.data.objects if o.type == "LIGHT"])
    for m in (lamp_m, ring_m):
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for fc in SD_fcurves(m.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- 给合成和真实层用：每帧镜头、红环在画面上的圆（中心、半径）、几个点的投影
    ring_c = [to_world(f, (11.78, 0, 0)) for f in range(NF)]
    camj = dict(seg=seg, nf=NF, frames=[])
    for f in range(NF):
        eye, tgt, lens, q = recs[f]
        rc = SD.project(recs[f], ring_c[f])
        # 半径：圆上 8 个点的投影到中心的平均距离（斜看时取平均）
        rad = []
        Mf = mats[f]
        for k in range(8):
            a = 2 * math.pi * k / 8
            p = Mf @ (Vector((11.78, 6.2 * math.cos(a), 6.2 * math.sin(a))) * MM * S)
            pp = SD.project(recs[f], p)
            if pp and rc:
                rad.append(math.hypot(pp[0] - rc[0], pp[1] - rc[1]))
        camj["frames"].append(dict(f=f, eye=list(eye), q=list(q), lens=lens, fstop=fst[f], focus=focus_d[f],
                                   ring=[rc[0], rc[1], sum(rad) / len(rad)] if rc and rad else None,
                                   sock=list(SD.project(recs[f], to_world(f, BC)) or [0, 0, 0]),
                                   lamp=lamp_level(t, f), lid=lid_angle(t, f)))
    camj["machine"] = msched
    camj["gates"] = [dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in gates]
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    # 弥散圆（焦点目标前后各 ±8 mm 局部、和板面）抽查
    coc = []
    for f in range(0, NF, 30):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        Sd = focus_d[f]
        dc = (to_world(f, BC) - eye).dot(fwd)
        coc.append(dict(f=f, fstop=round(fst[f], 1), focus_mm=round(Sd / MM, 1), sock_mm=round(dc / MM, 1),
                        coc_sock=round(SD.coc_px(lens, fst[f], Sd, dc), 2),
                        coc_pm8=round(max(SD.coc_px(lens, fst[f], Sd, Sd + 8 * MM * S), SD.coc_px(lens, fst[f], Sd, Sd - 8 * MM * S)), 2)))
    chk = dict(coc=coc, rims={k: dict(name=v.name, peak_w=round(v["peak_w"], 3)) for k, v in rims.items()}, plan=plan,
               gates=camj["gates"], machine=msched)
    (W / "build_check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


def SD_fcurves(action):
    import bl_guide as BG
    return BG._fcurves(action)


# ================================================================ 穿模检查的分组（shot_drill.clip_run 调）
def _roots(sc):
    import bpy
    r = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    if len(r) < 3:                                                       # 旧场景没标记：按名字认
        r = {"socket": bpy.data.objects["h01b_cdk20_socket"], "048": bpy.data.objects["h02b_plug"], "atp": bpy.data.objects["h02b_plug.001"]}
    return r


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
        if o.type in ("MESH", "CURVE", "FONT") and not o.name.endswith("_cut") and not o.name.startswith("drill_packet"):
            out.append(o)
    return out


def clip_plan(sc):
    """穿模分组：插头 vs 插座、两个插头互相、插座在板上那几秒 vs 板子周围、盖动的时候 vs 其余。"""
    import bpy
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = _roots(sc)
    sock, p48, atp = R["socket"], R["048"], R["atp"]
    plugs = [p48, atp]
    s_m = _meshes_under(sock, skip=plugs)
    a_m = [o for o in [atp] + _meshes_under(atp) if o.type in ("MESH", "CURVE", "FONT")]
    k_m = [o for o in [p48] + _meshes_under(p48) if o.type in ("MESH", "CURVE", "FONT")]

    lid_j = [o for o in sock.children_recursive if o.type == "EMPTY" and o.get("role") == "lid"][0]
    on_lid = lambda o: lid_j in set(_ancestors(o))  # noqa: E731   盖上的灯（lamp_out）也算盖：它装在盖的孔里
    lid_m = [o for o in s_m if on_lid(o)]
    not_lid = [o for o in s_m if not on_lid(o)]
    sc.frame_set(0)
    c0 = sock.matrix_world.translation.copy()
    sock_set = set(s_m) | set(a_m) | set(k_m)
    board_near = [o for o in sc.objects if o.type == "MESH" and o not in sock_set and "_sock" not in o.name
                  and not o.name.startswith("drill_") and o.name != "board" and (o.matrix_world.translation.xy - c0.xy).length < 0.07]
    board_near += [bpy.data.objects["board"]]
    frames = set(range(0, NF, 3))
    for a, b in ((t.brk - 2, t.turn[1] + 10), (t.atp_out[0], t.atp_out[2]), (t.atp_in[0], t.atp_in[2] + 4), (t.swap[0], t.swap[2]),
                 (t.enter[0], t.clamp[2] + 4), (t.close[0], t.close[2]), (t.open1[0], t.open1[1] + 4), (t.open2[0], t.open2[1] + 4)):
        frames |= set(range(max(0, a), min(NF, b + 1)))

    def groups(f):
        g = [("plug_vs_socket", a_m + k_m, s_m), ("atp_vs_048", a_m, k_m)]
        if f <= t.turn[1] + 20:
            g.append(("socket_vs_board", s_m + a_m + k_m, board_near))
        if t.open1[0] <= f <= t.close[2] or f >= t.open2[0]:
            g.append(("lid_vs_body", lid_m, not_lid))
        return g
    return dict(frames=sorted(frames), groups=groups, cam_near=lambda f: s_m + a_m + k_m + board_near, ref=sock)


# ================================================================ 真实结构层：AlphaFold DB 的 CDK20 预测模型
PLDDT = [(90, (0.0, 0.325, 0.839)), (70, (0.396, 0.796, 0.953)), (50, (1.0, 0.859, 0.075)), (-1, (1.0, 0.490, 0.271))]   # AlphaFold DB 的四色


def windows(t):
    """真实层出现的两段：(进起, 进止, 出起, 出止, 后退量)。
    第一段（enzyme, a protein）镜头本来就远，红环小，口袋墨线圈对在红环上时整个蛋白都在画里，不再退；
    第二段（where it normally grabs ... ATP）钻到孔口，站稳后退一点看全貌，ATP 落地前回到对位。"""
    return [(t.real0_in[0], t.real0_in[1], t.real0_out[0], t.real0_out[1], 0.0),
            (t.real_in[0], t.real_in[1], t.real_out[0], t.real_out[1], 0.75)]


def window_at(t, f):
    for w in windows(t):
        if w[0] - 2 <= f <= w[3] + 1:
            return w
    return None


def real_pull(t, f):
    """真实层镜头往后退的量（0–1）：叠化快完时开始退，退出叠化开始前回到 0 附近（红环和墨线圈重新对上）。"""
    w = window_at(t, f)
    if w is None or w[4] <= 0:
        return 0.0
    a = smooth((f - w[1]) / 34.0)
    b = smooth((f - (w[2] - 8)) / 30.0)
    return clamp(a - b)


def build_real(seg, mode="render", *frames):
    """另开一个场景渲真实层（透明底 RGBA）：主链 CA 管子按 pLDDT 上 AlphaFold DB 的四色，外面一层半透明分子表面；
    镜头每帧摆到"口袋墨线圈（R_POCKET Å）正好压在玩具红环上"：方向 = 口袋往外最空的方向，距离 = R·fpx/r_px，镜头平移对到红环中心。"""
    import bpy
    import numpy as np
    from mathutils import Quaternion, Vector
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]
    WS = [(w[0] - 2, w[3] + 1, w[4]) for w in windows(t)]
    f0, f1 = WS[0][0], WS[-1][1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    SD.gpu(sc)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64                                             # 半透明壳 24 采样有颗粒；只渲叠化那几秒
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = SD.OUT_W, SD.OUT_H, 100
    sc.render.fps = SD.FPS
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.frame_start, sc.frame_end = f0, f1
    A = 0.01                                                           # 1 Å = 1 cm（场景单位）

    at = SD.pdb_atoms(STRUCT)
    xyz = np.array([a[5:8] for a in at])
    cen = xyz.mean(0)
    xyz = xyz - cen
    npz = np.load(SURF)
    pocket = np.array(npz["pocket"], float)
    dirv, clear = SD.way_out(xyz, pocket)
    print("DRILL real way_out", [round(float(x), 3) for x in dirv], "clear", round(float(clear), 2), "pocket", list(np.round(pocket, 2)),
          "mouth", list(np.round(np.array(npz["mouth"], float), 3)), flush=True)

    # 分子表面（半透明）
    me = bpy.data.meshes.new("cdk20_surface")
    me.from_pydata([tuple(v * A) for v in npz["verts"].astype(float)], [], [tuple(q) for q in npz["quads"].tolist()])
    me.update()
    dpk = np.linalg.norm(npz["verts"].astype(float) - pocket[None, :], axis=1)
    pk_w = np.clip((POCKET_HL_R - dpk) / 3.0, 0.0, 1.0)                  # 口袋中心 POCKET_HL_R Å 以内染珊瑚红（11-21 Gemini 必改：标出口袋）
    at_pk = me.attributes.new("pocket_w", "FLOAT", "POINT")
    at_pk.data.foreach_set("value", pk_w.astype(np.float32).tolist())
    surf = bpy.data.objects.new("cdk20_surface", me)
    sc.collection.objects.link(surf)
    me.shade_smooth()
    ms = bpy.data.materials.new("real_surface")                       # 玻璃壳：正对镜头几乎透明，轮廓边上发白（看得出口袋的凹）
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
    atn = nt.nodes.new("ShaderNodeAttribute")                         # 口袋高亮：底色、透明度按 pocket_w 混到珊瑚红，略发光（同 5-04）
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

    # 主链管子：按 pLDDT 分段（相邻两段共用一个点，管子不断）
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

    # 镜头 + 跟着镜头的三盏灯
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
    up0 = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    lens = 35.0
    fpx = lens / 36.0 * SD.OUT_W
    cam.rotation_mode = "QUATERNION"
    log = []
    for f in [f_ for a_, b_, _ in WS for f_ in range(a_, b_ + 1)]:
        r = camj[f]["ring"]
        if not r:
            continue
        cx, cy, rp = r
        D0 = R_POCKET * fpx / max(rp, 40.0) * A
        D = D0 * (1.0 + 0.75 * real_pull(t, f))                       # 站稳后退一点看全貌，退出前回到对位
        wa, wb, _ = next(w for w in WS if w[0] <= f <= w[1])
        u = (f - wa) / max(1, wb - wa)
        q = (-d).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(-8.0 + 16.0 * u))     # 镜头看 −Z
        cam.location = P + d * D
        cam.rotation_quaternion = q
        cam_d.lens = lens
        cam_d.shift_x = (SD.OUT_W / 2 - cx) / SD.OUT_W                 # 11-21 改正号：shift_x 为正时轴上的点往左走（原来写反，口袋落在红环关于画面中心的镜像处）
        cam_d.shift_y = (cy - SD.OUT_H / 2) / SD.OUT_W
        for path, ob in (("location", cam), ("rotation_quaternion", cam), ("lens", cam_d), ("shift_x", cam_d), ("shift_y", cam_d)):
            ob.keyframe_insert(path, frame=f)
        log.append(dict(f=f, D_A=round(D / A, 2), k=D0 / D, ring=[round(cx, 1), round(cy, 1), round(rp, 1)]))
    SD.linear_all([cam])
    (W / "real_cam.json").write_text(json.dumps(dict(way_out=list(map(float, dirv)), clear=float(clear), cam=log), indent=1), encoding="utf-8")
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
    for a_, b_, _ in WS:
        if os.environ.get("REAL_F0"):                                   # 返修几帧：REAL_F0=… REAL_F1=… DRILL_OVERWRITE=1
            a_, b_ = max(a_, int(os.environ["REAL_F0"])), min(b_, int(os.environ["REAL_F1"]))
            if a_ > b_:
                continue
        SD.render_range(W / "real.blend", W / "real", a_, b_, prefix="r_")


# ================================================================ 合成：叠化到真实层、墨线圈、出处行、标签
SRC_TOY = "Illustration (our toy model) · CDK20 case: Ren et al. 2023"
SRC_REAL = "CDK20: AlphaFold DB AF-Q8IZL9-F1 (predicted, CC BY 4.0)"
INK_RED = (232, 25, 15)
INK_NOTE = (255, 66, 48)                                             # 手写批注：比墨线圈的红亮一档，深色真实层上也醒目（11-21 Gemini 第二轮）
NOTE_STROKE = (5, (255, 250, 244))
SRC_SIZE, SRC_XY, PLATE = 30, (96, 1046), ((14, 16, 24), 0.66, 12, 8)   # 11-21 Gemini 必改：出处行 Instrument Serif、放大、深色底衬（同 5-04）
NOTE_PROTEIN = "CDK20, a protein"
NOTE_ATP = "ATP binds here"
POCKET_HL_R = 9.0
OUT_DIR = SD.ROOT / "导演检查_20261121"
OUT_MP4 = OUT_DIR / "16_钻取_3-04.mp4"


def ink_arrow(p0, p1, bend, k, width=5.0, color=INK_RED, alpha=1.0):
    """手画箭头：二次曲线从 p0 写到 p1（k = 写到哪，0–1），最后 12% 长出箭头；底下垫一道白，花背景上也看得清。"""
    from PIL import Image, ImageDraw
    s = 2
    lay = Image.new("RGBA", (SD.OUT_W * s, SD.OUT_H * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    cxp, cyp = mx + nx * bend, my + ny * bend
    n = 48
    m = max(2, int(n * clamp(k)))
    pts = []
    for i in range(m + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cxp + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cyp + u * u * y1))
    P = [(x * s, y * s) for x, y in pts]
    for wd, col, aa in ((width + 5, (255, 250, 244), 0.55), (width, color, 1.0)):
        dr.line(P, fill=(*col, int(255 * alpha * aa)), width=int(wd * s), joint="curve")
    kh = clamp((k - 0.88) / 0.12)
    if kh > 0 and len(pts) > 2:
        ex, ey = pts[-1]
        px, py = pts[-3]
        ang = math.atan2(ey - py, ex - px)
        L = 26 * kh
        for sgn in (-1, 1):
            a2 = ang + math.pi + sgn * 0.5
            q = (ex + L * math.cos(a2), ey + L * math.sin(a2))
            for wd, col, aa in ((width + 5, (255, 250, 244), 0.55), (width, color, 1.0)):
                dr.line([(ex * s, ey * s), (q[0] * s, q[1] * s)], fill=(*col, int(255 * alpha * aa)), width=int(wd * s))
    return lay.resize((SD.OUT_W, SD.OUT_H), Image.LANCZOS)


def _lum_box(a, box):
    x0, y0, x1, y1 = box
    a = a[y0:y1, x0:x1].astype("float32") / 255
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())


def comp_frames(seg, flist=None):
    """生成合成后的帧（uint8 RGB）。flist=None 时全段。真实层两段（windows）：
    第一段 enzyme / a protein：蛋白全貌，口袋染红、墨线圈对在盒上红环，手写 "CDK20, a protein"；
    第二段 where ... ATP：钻进孔口，口袋墨线圈 + "pocket"，molecule 上手写 "ATP binds here" 和箭头指进口袋，
    收回红环时黄色 ATP 插头正好落地（ATP 这个词），手写留到通电后再淡出。
    11-21 Gemini 必改：出处行一律 Instrument Serif、30 号、深色底衬；左上角重复的模型标签删掉。"""
    import numpy as np
    from PIL import Image, ImageFilter
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]
    rk = {c['f']: c['k'] for c in json.loads((W / 'real_cam.json').read_text(encoding='utf-8'))['cam']} if (W / 'real_cam.json').exists() else {}
    WIN = windows(t)
    yy, xx = np.mgrid[0:SD.OUT_H, 0:SD.OUT_W].astype(np.float32)
    for f in (flist if flist is not None else range(NF)):
        img = np.asarray(Image.open(W / "frames" / f"f_{f:04d}.png").convert("RGB")).astype(np.float32) / 255
        out = img
        a_real = 0.0
        ring = camj[f]["ring"]
        rp = W / "real" / f"r_{f:04d}.png"
        w = next((w_ for w_ in WIN if w_[0] <= f <= w_[3]), None)
        if w and ring and rp.exists():
            ri0, ri1, ro0, ro1 = w[:4]
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
            R = u * (far + 160) - 80                                     # 从红环里面往外漫开（退出时收回红环）
            mask = np.clip((R - dist) / 160 + 0.5, 0, 1)
            bg = np.asarray(Image.fromarray((img * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
            bg = bg * 0.28 + np.array([0.035, 0.045, 0.075], np.float32) * 0.72
            real = rl[..., :3] * rl[..., 3:4] + bg * (1 - rl[..., 3:4])
            out = img * (1 - mask[..., None]) + real * mask[..., None]
        pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
        if ring and w and a_real > 0:                                    # 口袋墨线圈（真实层站稳以后）
            ri0, ri1, ro0, ro1 = w[:4]
            k = ramp(f, ri1 - 10, ri1 + 8) * (1 - ramp(f, ro0 - 8, ro0 + 6))
            cx, cy, r = ring
            r = r * rk.get(f, 1.0)
            if k > 0.003:
                rot = 0.35 * (f - ri0)
                pil = Image.alpha_composite(pil, SD.dashed_circle(cx, cy, r * 0.98, 9.0, (255, 250, 244), 0.55 * k, rot=rot))
                pil = Image.alpha_composite(pil, SD.dashed_circle(cx, cy, r * 0.98, 5.0, INK_RED, 1.0 * k, rot=rot))
            if w is WIN[1] and k > 0.003:
                items = [dict(text="pocket", xy=(cx + r * 0.74, cy - r * 0.78), size=78, color=INK_NOTE, hand=True, anchor="ls",
                              stroke=NOTE_STROKE, shadow=False)]
                pil = Image.alpha_composite(pil, SD.draw_text_layer(items, lambda it: k))
        # 手写 "CDK20, a protein"：protein 这个词落下，写在口袋圈左边；随第一段真实层收回淡出
        if ring:
            kn = ramp(f, t.note_protein[0], t.note_protein[1], ease_out) * (1 - ramp(f, t.real0_out[0] - 4, t.real0_out[0] + 12))
            if kn > 0.003:
                cx, cy, r = ring
                tx, ty = cx - r - 250, cy - r * 0.2 - 14 * (1 - kn)       # 放在蛋白左边的空处（蛋白主要在口袋右下），细箭头指到墨线圈
                items = [dict(text=NOTE_PROTEIN, xy=(tx, ty), size=74, color=INK_NOTE, hand=True, anchor="rs",
                              stroke=NOTE_STROKE, shadow=False)]
                pil = Image.alpha_composite(pil, SD.draw_text_layer(items, lambda it: kn))
                ke = clamp((f - t.note_protein[0] - 6) / 16.0)
                if ke > 0:
                    a_ = math.radians(195)
                    pil = Image.alpha_composite(pil, ink_arrow((tx + 14, ty - 22), (cx + r * 1.08 * math.cos(a_), cy + r * 1.08 * math.sin(a_)), 0.12,
                                                              ease_out(ke), width=4.0, color=INK_NOTE, alpha=kn))
        # 手写 "ATP binds here" + 箭头：ATP 这个词上写（Gemini 第三轮：原来在 molecule 上，字比声音早 1 秒），箭头指进插孔，黄插头落地同拍
        if ring:
            ka = ramp(f, t.note_atp[0], t.note_atp[1], ease_out) * (1 - ramp(f, t.enter[0] - 14, t.enter[0] + 4))   # 11-21：ATP 这个词上写，048 插头进场前淡出
            if ka > 0.003:
                cx, cy, r = ring
                r = r * rk.get(f, 1.0)
                tx, ty = cx - r * 1.05 - 330, cy + r * 0.9 + 70                  # 放到蛋白左下外面的空处，箭头拉长指进口袋
                tx, ty = max(tx, 260.0), min(ty, SD.OUT_H - 130.0)
                items = [dict(text=NOTE_ATP, xy=(tx, ty), size=74, color=INK_NOTE, hand=True, anchor="ms",
                              stroke=NOTE_STROKE, shadow=False)]
                pil = Image.alpha_composite(pil, SD.draw_text_layer(items, lambda it: clamp(ka * 1.6)))
                ke = clamp((f - t.note_atp[0] - 8) / (t.note_atp[1] - t.note_atp[0]))
                p0 = (tx + 150, ty - 52)
                ang = math.radians(135)
                p1 = (cx + r * 0.82 * math.cos(ang), cy + r * 0.82 * math.sin(ang))
                if ke > 0:
                    pil = Image.alpha_composite(pil, ink_arrow(p0, p1, -0.18, ease_out(ke), width=4.0, color=INK_NOTE, alpha=clamp(ka * 1.6)))
        # 出处行：玩具一行 / 真实一行（叠化时交换）；段首随 T5 淡入，甩镜时淡出
        base_a = ramp(f, 10, 30) * (1 - ramp(f, t.whip[0] - 4, t.whip[0] + 4))
        it_t = dict(text=SRC_TOY, xy=SRC_XY, size=SRC_SIZE, color=(240, 238, 232), anchor="ls", shadow=False, plate=PLATE)
        it_r = dict(text=SRC_REAL, xy=SRC_XY, size=SRC_SIZE, color=(240, 238, 232), anchor="ls", shadow=False, plate=PLATE)
        for it_, a_ in ((it_t, clamp(1 - 2 * a_real)), (it_r, clamp(2 * a_real - 1))):   # 两行各画一层（先淡出一行再淡入另一行，不叠字）
            if base_a * a_ > 0.003:
                pil = Image.alpha_composite(pil, SD.draw_text_layer([it_], lambda it, _a=a_: base_a * _a))
        yield f, np.asarray(pil.convert("RGB"))


def comp(seg, *a):
    import time
    W = SD.work(seg)
    if a and a[0] == "frames":                                           # 只出几张合成帧（看）
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
def audio(seg):
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]

    def pan(f):
        x = camj[min(f, len(camj) - 1)]["sock"][0]
        return clamp(0.5 + 0.35 * (x / SD.OUT_W - 0.5) * 2, 0.15, 0.85)
    C = SD.click

    def snap(s, g=0.20):                                                # 浇口断、卡扣
        return C([(3100, 1.0), (5200, 0.5)], 9, 3, g, s)

    def clack(s, g=0.24):                                               # 插头到底
        return C([(900, 1.0), (1900, 0.6), (3300, 0.3)], 22, 5, g, s)

    def thunk(s, g=0.26):                                               # 盖合上、停
        return C([(260, 1.0), (520, 0.5), (1400, 0.25)], 40, 6, g, s)

    def tick(s, g=0.10):                                                # 拧的棘轮
        return C([(2400, 1.0), (4100, 0.4)], 6, 2, g, s)
    hits = [(t.brk - 1, snap(1, 0.16), pan(t.brk)), (t.brk, snap(2, 0.22), pan(t.brk)), (t.brk + 1, snap(3, 0.14), pan(t.brk)),
            (t.open1[1], thunk(4, 0.14), pan(t.open1[1])), (t.close[1], thunk(5, 0.24), pan(t.close[1])),
            (t.atp_out[1] - 6, clack(6, 0.14), pan(t.atp_out[1])), (t.atp_in[1], clack(7, 0.24), pan(t.atp_in[1])),
            (t.swap[0] + 2, clack(8, 0.16), pan(t.swap[0])), (t.p48[1], clack(9, 0.28), pan(t.p48[1]))]
    for k in range(5):
        f = int(t.twist[0] + (t.twist[1] - t.twist[0]) * (k + 1) / 5)
        hits.append((f, tick(10 + k), pan(f)))
    hits += [(t.clamp[1], snap(20, 0.24), pan(t.clamp[1])), (t.open2[1], thunk(21, 0.12), pan(t.open2[1])), (t.stop, thunk(22, 0.22), pan(t.stop)),
             (0, SD.whoosh(0.28, 0.12, 30, f0=500, f1=3000), 0.65),
             (t.real0_in[0] - 4, SD.whoosh(0.6, 0.07, 32, f0=250, f1=1800), 0.6),               # 11-21：蛋白全貌进出各一道轻风声
             (t.real0_out[0], SD.whoosh(0.5, 0.06, 33, f0=1800, f1=300), 0.6),
             (t.whip[0] - 4, SD.whoosh((t.whip[1] - t.whip[0] + 18) / SD.FPS, 0.22, 31), 0.3)]
    SD.mix_audio(seg, hits, W / "mix.wav")
    (W / "audio_hits.json").write_text(json.dumps([[h[0], round(h[2], 2)] for h in hits]), encoding="utf-8")


# ================================================================ 自检：黑帧、亮度跳变、真实层亮度、声音、check_sync、穿模
def check(seg):
    import os
    import subprocess
    import numpy as np
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    res = {}
    fr = SD.ff_frames(OUT_MP4, scale=(320, 180)).astype(np.float32) / 255
    res["video_frames"] = int(len(fr))
    res["expected_frames"] = NF
    luma = (0.2126 * fr[..., 0] + 0.7152 * fr[..., 1] + 0.0722 * fr[..., 2]).mean(axis=(1, 2))
    res["black_frames"] = [int(i) for i in np.where(luma < 0.03)[0]]
    res["luma_jumps_gt_0.06"] = [[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma))
                                 if abs(luma[i] - luma[i - 1]) > 0.06 and i < t.whip[0] - 2]
    res["luma_every_30"] = [round(float(x), 3) for x in luma[::30]]
    a, b = t.real_in[0] - 1, min(NF - 1, t.real_in[1] + 10)
    res["real_vs_toy_luma"] = dict(toy=round(float(luma[a]), 3), real=round(float(luma[b]), 3))
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-map", "0:a", "-f", "null", "-"], capture_output=True, text=True)
    res["audio_ok"] = pr.returncode == 0
    # 帧率检查（S4）按总表里的事件认"设计渐变"；总表（master_v1.json，全片共用，不动它）里这段还没有三维事件，
    # 就临时拼一张只有这一段的表：词、句照总表，事件用 keys（里面有 dissolve 叠化）。用 CDK20_MAP 指过去。
    M = json.loads((SD.MAPD / "master_v1.json").read_text(encoding="utf-8"))
    g = dict(next(x for x in M["groups"] if x["group"] == seg or seg in x["segs"]))
    g["events"] = K["events"]
    tmp_map = W / "map_with_events.json"
    tmp_map.write_text(json.dumps(dict(fps=M.get("fps", 60), groups=[g]), ensure_ascii=False), encoding="utf-8")
    py = SD.ROOT / "_env/footage/Scripts/python.exe"                   # 这个 python 只能写项目里少数目录：报告用它默认的 映射/_reports/
    r = subprocess.run([str(py), str(SD.MAPD / "check_sync.py"), str(OUT_MP4), seg], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(SD.ROOT), env=dict(os.environ, PYTHONIOENCODING="utf-8", CDK20_MAP=str(tmp_map)))
    cs = SD.MAPD / "_reports" / f"sync_{seg}_{OUT_MP4.stem}.json"
    res["check_sync_out"] = (r.stdout[-3000:] + r.stderr[-800:]).strip()
    if cs.exists():
        res["check_sync"] = json.loads(cs.read_text(encoding="utf-8"))
    clip = W / "clip.json"
    if clip.exists():
        res["clip"] = {k: v for k, v in json.loads(clip.read_text(encoding="utf-8")).items() if k != "hits"}
    (W / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL check", json.dumps({k: v for k, v in res.items() if k not in ("check_sync", "luma_every_30")}, ensure_ascii=False, default=str)[:5000], flush=True)


def sheet(seg, step="6"):
    """每 6 帧一张，6×6 一页，帧号写在角上；页存进导演检查文件夹（报告里引用）和工作目录。"""
    from PIL import Image, ImageDraw, ImageFont
    step = int(step)
    fr = SD.ff_frames(OUT_MP4, scale=(384, 216))
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
        name = f"16_钻取_3-04_抽帧_{len(pages) + 1:02d}.jpg"
        im.save(SD.work(seg) / name, quality=86)
        pages.append(name)
    (SD.work(seg) / "sheets.json").write_text(json.dumps(dict(step=step, pages=pages, frames=idx)), encoding="utf-8")
    print("DRILL sheet", pages, flush=True)


# ================================================================ 报告（给导演的 html，放导演检查文件夹）
def report(seg):
    import html
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    NF = K["len_f"]
    rd = lambda n: json.loads((W / n).read_text(encoding="utf-8")) if (W / n).exists() else {}  # noqa: E731
    chk, clip, rv, sh, bc = rd("check.json"), rd("clip.json"), rd("review.json"), rd("sheets.json"), rd("build_check.json")
    e = html.escape

    def stamp(k):
        p = W / f"render_t{k}.txt"
        return int(p.read_text().strip()) if p.exists() else None
    t0, t1, t2 = stamp(0), stamp(1), stamp(2)
    times = []
    if t0 and t1:
        times.append(("玩具层整段渲染（1030 帧，1080p60，16 采样，OptiX 降噪）", f"{(t1 - t0) / 60:.1f} 分钟，约 {(t1 - t0) / NF:.2f} 秒/帧"))
    if t1 and t2:
        times.append(("真实层（AlphaFold 模型，叠化那几秒）", f"{(t2 - t1) / 60:.1f} 分钟"))
    if (W / "comp_time.txt").exists():
        times.append(("合成 + nvenc 编码 + 混音", f"{float((W / 'comp_time.txt').read_text()) / 60:.1f} 分钟"))
    if rv.get("times"):                                                  # 返修重渲过的段，计时以人记的为准
        times = [tuple(x) for x in rv["times"]]
    if clip.get("sec"):
        times.append(("穿模逐帧 BVH 检查（CPU）", f"{clip['sec'] / 60:.1f} 分钟，{clip.get('frames')} 帧"))

    rows_ev = "".join(
        f"<tr><td>{e(x['id'])}</td><td>{e(x['verb'])}</td><td>{e(x.get('w') or '')}</td><td class=n>{x['f_start']}</td><td class=n>{x['f_land']}</td>"
        f"<td class=n>{x['f_end']}</td><td class=n>{x['f_land'] / 60:.2f}</td><td>{e(x.get('means', ''))}</td></tr>" for x in K["events"])
    items = rv.get("items", [])
    rows_ck = "".join(f"<tr class={'ok' if it['ok'] else 'bad'}><td>{e(it['item'])}</td><td>{'通过' if it['ok'] else '未过'}</td><td>{e(it['note'])}</td></tr>" for it in items)
    sync = chk.get("check_sync", {})
    sheets = "".join(f'<figure><img src="{e(p)}" loading="lazy"><figcaption>抽帧第 {i + 1} 页（每 6 帧一张，左上角是段内帧号）</figcaption></figure>'
                     for i, p in enumerate(sh.get("pages", [])))
    design = rv.get("design", [])
    concl = rv.get("conclusion", "")
    doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>节点 2 · 3-04 钻取样片</title>
<style>
:root{{--bg:#f6f5f1;--fg:#1b1b1d;--soft:#5d5d63;--line:#d9d6ce;--ok:#1d7a3a;--bad:#b3261e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--fg:#ecebe6;--soft:#a3a3a8;--line:#333338;--ok:#5cc27e;--bad:#ff8a80;--card:#1d1d20}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 16px 80px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:19px;margin:36px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
.sub{{color:var(--soft);margin:0 0 18px}} .concl{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--ok);padding:14px 18px;border-radius:6px}}
video{{width:100%;border-radius:6px;background:#000}} ul{{padding-left:22px}} li{{margin:4px 0}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}}
th,td{{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}} th{{background:rgba(127,127,127,.12)}}
td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} tr.ok td:nth-child(2){{color:var(--ok);font-weight:600}} tr.bad td:nth-child(2){{color:var(--bad);font-weight:600}}
figure{{margin:16px 0}} figure img{{width:100%;border-radius:4px}} figcaption{{color:var(--soft);font-size:13px}}
code{{font-size:13px}}
</style></head><body><main>
<h1>节点 2 · 3-04 三维钻取样片</h1>
<p class=sub>HKBU SCIE1007 课程作业的科普视频 · 第一段三维钻取镜头（玩具比喻，分子数据来自公开数据库）· 1080p60 · {NF / 60:.2f} 秒 · 2026-11-20</p>
<div class=concl>{concl}</div>
<h2>成片</h2>
<video src="13_节点2_3-04.mp4" controls preload="metadata"></video>
<h2>设计要点</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in design)}</ul>
<h2>自检清单（逐条）</h2><div class=tw><table><tr><th>检查项</th><th>结果</th><th>说明</th></tr>{rows_ck}</table></div>
<h2>对拍（check_sync）</h2><pre style="white-space:pre-wrap;font-size:13px">{e(chk.get('check_sync_out', '')[-2500:])}</pre>
<h2>渲染时长</h2><div class=tw><table><tr><th>步骤</th><th>用时</th></tr>{''.join(f'<tr><td>{e(a)}</td><td>{e(b)}</td></tr>' for a, b in times)}</table></div>
<h2>事件表（帧 = 段内 60 fps；全部挂在念词上）</h2><div class=tw><table><tr><th>事件</th><th>动作</th><th>词</th><th>起</th><th>落</th><th>止</th><th>落(秒)</th><th>画面</th></tr>{rows_ev}</table></div>
<h2>抽帧</h2>{sheets}
<p class=sub>代码：镜头设计_v3/inserts/shot_drill.py（通用引擎）+ drill_304.py（本段配方）+ run_drill.sh；事件表 映射/events/3-04.json；中间文件在 G:/cdk20/work/drill/3-04/。</p>
</main></body></html>"""
    out = OUT_DIR / "13_节点2_检查.html"
    out.write_text(doc, encoding="utf-8")
    print("DRILL report", out, flush=True)
