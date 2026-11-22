"""HKBU SCIE1007 课程作业的科普视频：三维钻取 3-02 —— 细胞壳里的三台小插座（设计：深化/18_剩余画面设计定稿.md 的 2.1，11-23）。

"Inside your cells, proteins do a lot of the work. Most drugs grab one protein tightly and change what it does,
slotting into a pocket like a key into a lock."

一镜到底（引擎 shot_drill.py，帧号全部来自 映射/keys/3-02.json）：
  K0  段首：接 3-01 末帧（handoff.json 的 tail_pose：镜头在销子锁剖开的象限里，贴着金色锁芯和白色上销），全虚。
  退  "Inside" 镜头退出锁、沿料杆横移到细胞壳（K1）；"cells" 壳的上盖绕后沿铰链翻开，镜头压进壳里（K2）。
  亮  "proteins" 三台小插座的灯从左到右依次亮（焦点点名中间那台）；"work" 三台开工：左边齿轮转、三台活塞推细胞鼓、右边推杆走。
  换  "drugs" 金色假插头从壳前方飞进来，停在中间那台孔轴旁；"grab" 中间那台的黄色 ATP 先沿孔轴弹出、升起让路、掉到壳底，
      假插头摆到孔轴上插进去（留 2 mm）；"tightly" 推到底"咔"，中间那台整台震一下，镜头微震。
  停  "change" 中间那台灯灭、活塞停在半程、细胞不再鼓；左右两台照常。
  推  "pocket" 镜头推到中间那台的插孔面，红环亮；"key" 焦点和轮廓光落到假插头的柄上；"lock" 红环占画宽 73%，停住出段，
      末帧红环的圆 = 3-03 第 0 帧金色锁孔环的圆（drill/3-02/handoff.json，T3 匹配形，误差 ≤ 4 px）。
零件：kit_deep_r5.u05_cell_shell + place_cell_sockets（三台 h01b mini，0.232 倍，孔型 slots / round / tri）、kit_socket.h02b_plug
（三把 ATP、一把 048，柄面刻字和卡口销藏掉）、kit_deep_r3.h06_pin_lock（own，剖开，钥匙插着、锁芯转 32°、锁梁弹起）。
不穿模：插头只沿孔轴进出；ATP 先退出孔桶再升起、往左让开，048 在孔轴右侧等着，两把插头轴线错开；clip 逐帧 BVH 查。
"""
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_drill as SD  # noqa: E402
from shot_drill import MM, clamp, smooth, smoother, ease_out, ease_in, spring, ramp, lerp, settle  # noqa: E402

SEG = "3-02"
BOARD = SD.WORK_ROOT / "kit" / "board_final.blend"
SENSOR = 2.0                 # 小插座只有 10 mm：末帧镜头离孔口约 7 mm。8 mm 传感器下真焦距 11 mm > 对焦距离（薄透镜失效），这一段改用 2 mm
LS = 2.0                     # 销子锁放大（同 3-03）
LOCK_FROM_CELL = (-120.0, 0.0, 40.0)
ROD_Y, ROD_Z, ROD_R = 3.0, 0.0, 2.2
ROD_X0, ROD_XR = -62.0, 43.5  # 料杆左端、右端（锁单位）；右端立柱落在细胞壳那一格左边
KEY_S = 1.3
SEATW = 12.03                # 插头凸缘到位时的 W（kit_socket.SEAT_W）
RING_W0, RING_W1, RING_R0, RING_R1 = 11.75, 12.25, 7.05, 8.0   # 中间那台的红环（mini 自带的环埋在孔桶壁里看不见，这里补一个，套在插头凸缘外圈）
H48 = (44.5, 17.0, 0.0)      # 048 等候位（中间那台的局部毫米：针尖离孔口 16，孔轴右侧 17，给 ATP 让出孔轴）
W_PROUD = 14.03              # "grab" 时 048 插到离底 2 mm，"tightly" 推到底
ATP_OUT = 30.0               # ATP 沿孔轴退出到凸缘 W = 30（针尖离开孔桶）
ATP_UP = (31.0, -16.0, 15.0)  # 再升起、往左让开
KR_F = 24                                # 出锁中间键（11-23 3-01 新末帧更贴近销子，14 帧出锁太快、亮度一帧跳 0.07）
HEAD_FOC = 18                            # 段首焦点从全虚缓到清楚的帧数
HEAD_K = 0.2                             # 段首转场灯倍率（试渲定）
SB_DIST, SB_SIZE, SB_W = 2.2, 2.6, 0.12   # 段尾柔光板：离孔口 2.2 倍末帧机距、直径 2.6 倍、功率 W（试渲定）
ATP_REST = (-6.0, -10.3)     # 掉到壳底的位置（壳局部毫米，凸缘中心 x、y），柄朝 +x，卡耳朝上，针那头低 10°
LID_OPEN, LID_PEAK = 106.0, 110.0
HANDOFF = SD.WORK_ROOT / "drill" / "3-02" / "handoff.json"
HO_301 = SD.WORK_ROOT / "oncam" / "3-01" / "handoff.json"
OUT_DIR = SD.ROOT / "导演检查_20261123"
OUT_MP4 = OUT_DIR / "16_钻取_3-02.mp4"
SRC_TOY = "Illustration (our toy model)"
SRC_BOX = (64, 886, 928)     # 出处行：左 x、上沿、下沿（18 的 1.6）
INK = (31, 30, 28)
BONE = (244, 241, 234)
INK_NOTE = (255, 66, 48)
NOTE_STROKE = (5, (255, 250, 244))


# ================================================================ 时间表
class T:
    def __init__(self, EV):
        g = lambda i, k="f_land": EV[i][k]  # noqa: E731
        tri = lambda i: (g(i, "f_start"), g(i), g(i, "f_end"))  # noqa: E731
        self.cam_out, self.shell, self.cam_in = tri("cam_out"), tri("shell_open"), tri("cam_in")
        self.lamps, self.run, self.enter = tri("lamps"), tri("run"), tri("plug_enter")
        self.swap, self.plug, self.clack = tri("swap"), tri("plug_in"), tri("clack")
        self.off, self.pocket, self.ring = tri("off"), tri("cam_pocket"), tri("ring")
        self.key, self.fill = tri("key_rim"), tri("cam_fill")
        # 由上面派生的几个时刻
        self.swing = (self.swap[1], self.swap[1] + 5)              # 048 从等候位摆到孔轴上
        self.atp_rise = (self.swap[0] + 8, self.swap[1])           # ATP 退出孔桶后升起让路
        self.atp_fall = (self.swap[1], self.swap[1] + 20)          # 掉到壳底
        self.home = (self.clack[1] - 4, self.clack[1])             # 048 推到底


# ================================================================ 机构（纯函数：帧 → 数值）
def lid_angle(t, f):
    a, b, c = t.shell
    if f < a:
        return 0.0
    if f < a + 6:                                                    # 预备：上盖先被顶开一条缝
        return 1.5 * smoother((f - a) / 6.0)
    if f < b:
        return lerp(1.5, LID_PEAK, smoother((f - a - 6) / (b - a - 6)))
    return LID_OPEN + (LID_PEAK - LID_OPEN) * math.cos(2 * math.pi * (f - b) / 20.0) * math.exp(-(f - b) / 7.0)


def lamp_level(t, f, i):
    on = t.lamps[1] + 4 * (i - 1)                                    # 左 102、中 106、右 110
    v = ramp(f, on - 3, on + 1, ease_out)
    if i == 1:
        v *= 1 - ramp(f, t.off[0], t.off[1])
    return v


def run_speed(t, f, i):
    v = ramp(f, t.run[0], t.run[1])
    if i == 1:
        v *= 1 - ramp(f, t.off[0], t.off[1])
    return v


PERIOD = 48.0


def machine(t, nf):
    """每台每帧：(活塞 0–5, 细胞缩放, 输出端值)。相位按速度积分；中间那台断电时相位停在推到一半。"""
    phase = [[0.0] * nf for _ in range(3)]
    for i in range(3):
        p = 0.0
        for f in range(nf):
            p += run_speed(t, f, i) / PERIOD
            phase[i][f] = p
    offs = [0.37, 0.0, 0.71]
    fr = phase[1][min(nf - 1, t.off[1] + 2)] % 1.0
    offs[1] = (0.17 - fr) % 1.0                                      # 断电时活塞正好在推的半程
    out = []
    for i in range(3):
        rows = []
        for f in range(nf):
            x = (phase[i][f] + offs[i]) % 1.0
            push = 4.0 * smoother(x / 0.35) if x < 0.35 else 4.0 * (1 - smoother((x - 0.35) / 0.65))
            bulge = math.sin(math.pi * clamp(x / 0.7)) ** 2
            w_run = ramp(f, t.run[0], t.run[1])
            L = lamp_level(t, f, i)
            idle_p = 0.5 + 0.25 * math.sin(2 * math.pi * f / 70.0 + i)
            idle_c = 1.0 + 0.02 * math.sin(2 * math.pi * f / 70.0 + i + 0.8)
            pis = lerp(0.5 + (idle_p - 0.5) * L, 0.4 + push, w_run)
            cel = lerp(1.0 + (idle_c - 1.0) * L, 1.0 + 0.2 * bulge, w_run)
            if i == 0:
                o = 360.0 * (phase[i][f] + offs[i]) + 6.0 * math.sin(2 * math.pi * f / 90.0) * L * (1 - w_run)
            elif i == 2:
                o = 2.0 - 2.0 * math.cos(2 * math.pi * (phase[i][f] + offs[i]))
                o = lerp(0.3 * L * (1 + math.sin(2 * math.pi * f / 80.0)), o, w_run)
            else:
                o = 0.0
            rows.append((pis, cel, o))
        out.append(rows)
    return out


def p48_local(t, f, start_local):
    """048 在中间那台局部毫米里的 (位置, 四元数参数 (偏航°, 横滚°))。"""
    e0, e1, e2 = t.enter
    s0, s1 = t.swing
    p0, p1, p2 = t.plug
    h0, h1 = t.home
    H = H48
    if f < e0:
        return start_local, (-40.0, 30.0)
    if f < e1:                                                       # 飞进来（二次曲线，先高后低），转正
        u = ease_out((f - e0) / (e1 - e0), 2.2)
        P0, P2 = start_local, H
        P1 = tuple(lerp(a, b, 0.55) for a, b in zip(P0, P2))
        P1 = (P1[0], P1[1], P1[2] + 22.0)
        p = tuple((1 - u) ** 2 * a + 2 * u * (1 - u) * b + u * u * c for a, b, c in zip(P0, P1, P2))
        k = smoother((f - e0) / (e1 - e0) * 1.15)
        return p, (-40.0 * (1 - k), 30.0 * (1 - k))
    if f < s0:                                                       # 等候：落位余振 + 慢浮
        bob = 0.5 * math.sin(2 * math.pi * (f - e1) / 60.0) * ramp(f, e1 + 6, e1 + 20)
        return (H[0], H[1], H[2] + settle(f, e1, 1.2, n=1.0, dur=e2 - e1 + 6) + bob), (0.0, 0.0)
    if f < s1:                                                       # 摆到孔轴上（ATP 已经升起让开）
        u = smoother((f - s0) / (s1 - s0))
        return (lerp(H[0], 34.0, u), lerp(H[1], 0.0, u), H[2] + 1.0 * math.sin(math.pi * u)), (-6.0 * math.sin(math.pi * u), 0.0)
    if f < p1:                                                       # 沿孔轴插进去，留 2 mm
        u = (f - s1) / (p1 - s1)
        return (lerp(34.0, W_PROUD, ease_out(u, 2.2)), 0.0, 0.0), (0.0, 0.0)
    if f < h0 - 4:
        return (W_PROUD + max(0.0, settle(f, p1, 0.25, n=1.0, dur=p2 - p1 + 4)), 0.0, 0.0), (0.0, 0.0)
    if f < h0:                                                       # 预备：往外收一点
        return (W_PROUD + 0.35 * smooth((f - h0 + 4) / 4.0), 0.0, 0.0), (0.0, 0.0)
    if f < h1:                                                       # "tightly"：推到底
        return (lerp(W_PROUD + 0.35, SEATW, ease_in((f - h0) / (h1 - h0), 2.0)), 0.0, 0.0), (0.0, 0.0)
    return (SEATW, 0.0, 0.0), (0.0, 0.0)


# ================================================================ 搭场景
def build(seg, samples=16):
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    import kit_parts as KP
    import kit_deep as D
    import kit_deep_r3 as M3
    import kit_deep_r5 as R5
    import kit_socket as S_
    SD.SENSOR = SENSOR
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    sc = SD.open_board(BOARD, NF, samples)
    board = bpy.data.objects["board"]
    zb = board.location.z
    cell, old = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p23_cell"))
    c23 = cell.matrix_world.translation.copy()
    print("DRILL cell", cell.name, [round(v / MM, 2) for v in c23], "zb", round(zb / MM, 2), "old", old.name,
          [round(v / MM, 2) for v in old.location], [round(v, 3) for v in cell.matrix_world.to_scale()], flush=True)
    SD.hide_tree(old)
    for g in KP.gates_of(cell):
        SD.hide_tree(g)
    Kt = KP.Kit()

    # ---- 细胞壳 + 三台小插座 + 插头（先在原点 1:1 搭好、烘修改器，再挂进格子）
    shell = R5.u05_cell_shell(Kt)
    # kit_deep_r5（11-23 04:49 版）在 kit_clear 的 Volume 上接了一个按物体属性混的 Mix Shader，Blender 5.3 Cycles（CPU/GPU 都一样）
    # 渲到用 kit_clear 的件就闪退（二分查到：只把 Volume 直连回原吸收就不崩）。不改 Codex 的零件文件，只在本段把 Volume 直连回原吸收，
    # 等于回到 04:49 以前的样子（本段第一版正式渲就是那样）
    for m_ in bpy.data.materials:
        nt_ = m_.node_tree
        if nt_ is None or nt_.nodes.get("u05 thin rim mix") is None:
            continue
        out_ = next(n_ for n_ in nt_.nodes if n_.type == "OUTPUT_MATERIAL")
        vm_ = out_.inputs["Volume"].links[0].from_node if out_.inputs["Volume"].is_linked else None
        if vm_ is not None and vm_.type == "MIX_SHADER" and vm_.inputs[1].is_linked:
            nt_.links.new(vm_.inputs[1].links[0].from_socket, out_.inputs["Volume"])
            nt_.nodes.remove(vm_)
    shell["drill_role"] = "shell"
    socks = R5.place_cell_sockets(Kt, shell)
    SS = float(shell["socket_scale"])
    for i, s_ in enumerate(socks):
        s_["drill_role"] = f"sock_{i}"
        S_.rest(s_)
    plugs = []
    for i, s_ in enumerate(socks):
        pl = S_.h02b_plug(Kt, which="ATP")
        pl["drill_role"] = f"atp_{i}"
        if i != 1:
            pl.parent = s_
            pl.matrix_parent_inverse = Matrix.Identity(4)
            pl.location = (SEATW * MM, 0, 0)
            pl.rotation_mode = "QUATERNION"
            pl.rotation_quaternion = Quaternion()
            pl.scale = (1, 1, 1)
        else:
            pl.parent = shell
            pl.matrix_parent_inverse = Matrix.Identity(4)
        plugs.append(pl)
    p48 = S_.h02b_plug(Kt, which="048")
    p48["drill_role"] = "048"
    p48.parent = socks[1]
    p48.matrix_parent_inverse = Matrix.Identity(4)
    p48.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    print("DRILL baked modifiers", SD.apply_modifiers(shell), SD.apply_modifiers(p48), sum(SD.apply_modifiers(p) for p in plugs), flush=True)
    for i in (0, 2):                                                 # 左右两台的 ATP 针藏掉：mini 的触点孔型和标准针不配，针整根埋在触点块里，看不见
        for o in plugs[i].children_recursive:
            nm = o.name.split(".")[0]
            if o.type == "MESH" and any(k in nm for k in ("needle", "blade", "cap")) and "core" not in nm:
                SD.hide_tree(o)
    hidden48 = set()
    for o in p48.children_recursive:                                 # 048：这里还没有名字（刻字藏掉）；mini 的孔桶没有卡口槽（卡口销藏掉）
        nm = o.name.split(".")[0]
        if o.type == "FONT" or "bayonet_pin" in nm:
            SD.hide_tree(o)
            hidden48 |= {o} | set(o.children_recursive)

    # 中间那台的红环（自己补的环，挂在插座上）
    def ring_mesh(name, w0, w1, r0, r1, n=160):
        vs, fs = [], []

        def circ(w, r):
            b = len(vs)
            vs.extend((w * MM, r * math.cos(2 * math.pi * k / n) * MM, r * math.sin(2 * math.pi * k / n) * MM) for k in range(n))
            return b
        for (wa, ra), (wb, rb), flip in (((w0, r1), (w1, r1), False), ((w0, r0), (w1, r0), True), ((w1, r1), (w1, r0), False), ((w0, r0), (w0, r1), False)):
            a_, b_ = circ(wa, ra), circ(wb, rb)
            for k in range(n):
                q = (a_ + k, a_ + (k + 1) % n, b_ + (k + 1) % n, b_ + k)
                fs.append(q[::-1] if flip else q)
        me = bpy.data.meshes.new(name)
        me.from_pydata(vs, [], fs)
        me.validate()
        for i_, p in enumerate(me.polygons):
            p.use_smooth = i_ < 2 * n
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        return ob
    ring_m = Kt.red.copy()
    ring_m.name = "drill302_ring_red"
    ring_em = SD.add_emission(ring_m, (1.0, 0.04, 0.02), 0.0)
    ring = ring_mesh("drill302_ring", RING_W0, RING_W1, RING_R0, RING_R1)
    ring.data.materials.append(ring_m)
    ring.parent = socks[1]
    ring.matrix_parent_inverse = Matrix.Identity(4)

    # 挂进格子：壳的根放在原来那件零件的位置
    shell.parent = cell
    shell.matrix_parent_inverse = Matrix.Identity(4)
    shell.location = old.location.copy()
    bpy.context.view_layer.update()
    Msh = shell.matrix_world.copy()
    O = [Vector(s_.location) / MM for s_ in socks]                   # 插座原点（壳局部毫米）
    print("DRILL socket scale", SS, "origins", [[round(v, 3) for v in o_] for o_ in O], flush=True)
    for i, (gx, gy, d, gz) in enumerate(json.loads(shell["gates"])):     # 浇口：格子外圈 → 底盘前沿
        end = {"+x": (KP.CX, gy), "-x": (-KP.CX, gy), "+y": (gx, KP.CY), "-y": (gx, -KP.CY)}[d]
        KP.gate_geo(f"{cell.name}_u05_g{i}", Vector((end[0] * MM, end[1] * MM, 0)) + shell.location,
                    Vector((gx * MM, gy * MM, gz * MM)) + shell.location, Kt.cat("white"), cell)

    Rz = Matrix.Rotation(-math.pi / 2, 4, "Z")
    Rz3 = Rz.to_3x3()
    q_ax = Rz.to_quaternion()

    def dy_sock(f, i):                                               # "咔"：中间那台在座上被顶得往上一跳（0.3 mm），旁边两台跟着轻颤；只往上，不进座子
        if i == 1:
            return abs(settle(f, t.clack[1], 0.3, n=2.0, dur=14))
        return abs(settle(f, t.clack[1] + 2, 0.08, n=1.5, dur=10))

    def O_at(f, i):
        return O[i] + Vector((0, 0, dy_sock(f, i)))

    def sl2sh(p, f=0, i=1):
        """插座局部毫米 → 壳局部毫米。"""
        return O_at(f, i) + Rz3 @ (Vector(p) * SS)

    def sh2sl(p, f=0, i=1):
        return Rz3.transposed() @ ((Vector(p) - O_at(f, i)) / SS)

    def sh2w(p):
        return Msh @ (Vector(p) * MM)

    def sock_mat(f, i=1):                                            # 插座世界矩阵（不含缩放）
        return Msh @ Matrix.Translation(O_at(f, i) * MM) @ Rz

    for f in range(NF):
        for i, s_ in enumerate(socks):
            s_.location = O_at(f, i) * MM
            s_.keyframe_insert("location", frame=f)

    # ---- 上盖、灯、活塞、细胞、输出端
    lid_j = D.rig(shell)["shell"]
    for f in range(NF):
        D.pose(shell, "shell", min(LID_PEAK, max(0.0, lid_angle(t, f))))
        lid_j.keyframe_insert("rotation_euler", index=0, frame=f)
    nuc = [o for o in shell.children_recursive if o.name.split(".")[0].endswith(("u05_nucleus", "u05_nucleus_film"))]
    for o in nuc:                                                    # 开盖带动细胞核晃一下
        base = o.location.copy()
        for f in range(NF):
            o.location = base + Vector((0, 0, settle(f, t.shell[1] - 2, 0.25 * MM, n=1.5, dur=14)))
            o.keyframe_insert("location", frame=f)
    mach = machine(t, NF)
    lamp_mats, lamp_on_f = [], []
    for i, s_ in enumerate(socks):
        rg = S_.rig(s_)
        ons = [o for o in s_.children_recursive if o.get("lamp") == "on"]
        offs = [o for o in s_.children_recursive if o.get("lamp") == "off"]
        lts = [o for o in s_.children_recursive if o.type == "LIGHT"]
        m0 = ons[0].active_material
        lm = m0.copy()
        lm.name = f"drill302_lamp_{i}"
        for o in ons:
            o.data = o.data.copy()
            o.data.materials.clear()
            o.data.materials.append(lm)
        em = [n for n in lm.node_tree.nodes if n.type == "EMISSION"]
        bs = [n for n in lm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        sock_in = em[0].inputs["Strength"] if em else bs[0].inputs["Emission Strength"]
        s_max = float(sock_in.default_value) or 4.0
        lamp_mats.append(lm)
        on_f = [lamp_level(t, f, i) > 0.02 for f in range(NF)]
        lamp_on_f.append(on_f)
        for o in ons + offs:
            want = o in ons
            seq = [(0, not (on_f[0] if want else not on_f[0]))]
            for f in range(1, NF):
                if on_f[f] != on_f[f - 1]:
                    seq += [(f - 1, not (on_f[f - 1] if want else not on_f[f - 1])), (f, not (on_f[f] if want else not on_f[f]))]
            SD.hide_tree(o, seq)
        for f in range(NF):
            L = lamp_level(t, f, i)
            sock_in.default_value = s_max * L
            sock_in.keyframe_insert("default_value", frame=f)
            for lo_ in lts:
                lo_.data.energy = 0.03 * SS * SS * L
                lo_.data.keyframe_insert("energy", frame=f)
            pis, cel, o_ = mach[i][f]
            S_.pose(s_, "piston", pis)
            rg["piston"].keyframe_insert("location", frame=f)
            S_.pose(s_, "cell", cel)
            rg["cell"].keyframe_insert("scale", frame=f)
            if "out" in rg:
                if i == 0:
                    rg["out"].rotation_euler.x = math.radians(o_)
                    rg["out"].keyframe_insert("rotation_euler", index=0, frame=f)
                else:
                    rg["out"].location.z = clamp(o_, 0.0, 4.0) * MM
                    rg["out"].keyframe_insert("location", index=2, frame=f)
    for f in range(NF):                                              # 红环亮（pocket）
        g = 0.40 * ramp(f, t.ring[0], t.ring[1] + 8, ease_out)
        ring_em.inputs["Strength"].default_value = g
        ring_em.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # ---- ATP（中间那台）：插着 → 沿轴弹出 → 升起让路 → 掉到壳底 → 弹一下停住
    atp = plugs[1]
    q_lie = Quaternion((0, 1, 0), math.radians(-10.0)) @ Quaternion((1, 0, 0), math.pi)
    atp.rotation_mode = "QUATERNION"
    atp.scale = (SS, SS, SS)
    atp.location = Vector((ATP_REST[0], ATP_REST[1], 5.0)) * MM
    atp.rotation_quaternion = q_lie
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = 1e9
    for o in [atp] + list(atp.children_recursive):
        if o.type == "MESH" and not o.hide_render:
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            Mrel = Msh.inverted() @ e.matrix_world
            for v in me.vertices:
                zmin = min(zmin, (Mrel @ v.co).z / MM)
            e.to_mesh_clear()
    rest_z = 5.0 - zmin + 0.03                                       # 底盘上面 z = 0
    P_rest = Vector((ATP_REST[0], ATP_REST[1], rest_z))
    print("DRILL atp rest z", round(rest_z, 3), flush=True)
    s0, s1, s2 = t.swap
    r0, r1 = t.atp_rise
    g0, g1 = t.atp_fall

    def atp_state(f):
        """返回 (壳局部毫米, 壳局部四元数)。"""
        if f < s0 - 4:
            return sl2sh((SEATW, 0, 0), f), q_ax
        if f < s0:                                                   # 预颤：往外一点
            return sl2sh((SEATW + 0.2 * math.sin(math.pi * (f - s0 + 4) / 4), 0, 0), f), q_ax
        if f < r0:                                                   # 沿孔轴弹出
            return sl2sh((lerp(SEATW, ATP_OUT, ease_out((f - s0) / (r0 - s0), 2.6)), 0, 0), f), q_ax
        if f < r1:                                                   # 升起、往左让开
            u = smoother((f - r0) / (r1 - r0))
            p = (lerp(ATP_OUT, ATP_UP[0], u), lerp(0.0, ATP_UP[1], u), lerp(0.0, ATP_UP[2], u))
            return sl2sh(p, f), q_ax @ Quaternion((1, 0, 0), math.radians(-8 * math.sin(math.pi * u)))
        Pu = sl2sh(ATP_UP, r1)
        if f < g1:                                                   # 掉下去：水平匀速，竖直加速；边掉边翻成躺着
            u = (f - g0) / (g1 - g0)
            p = Pu.lerp(P_rest, u)
            p.z = Pu.z + (P_rest.z - Pu.z) * u * u + 1.2 * u * (1 - u)
            return p, q_ax.slerp(q_lie, smoother(min(1.0, u * 1.15)))
        b = 0.30 * abs(math.sin(math.pi * (f - g1) / 7.0)) * math.exp(-(f - g1) / 5.0) if f < g1 + 14 else 0.0
        return P_rest + Vector((0, 0, b)), q_lie
    atp_tr = []
    for f in range(NF):
        p, q = atp_state(f)
        SD.key_xform(atp, f, loc=p * MM, quat=q, scale=(SS, SS, SS))
        atp_tr.append(tuple(p))

    # ---- 048：从壳的正前方飞进来 → 孔轴右侧等着 → 摆到孔轴上插进去 → "tightly" 推到底
    start_sh = Vector((16.0, -48.0, O[1].z + 9.0))
    start_l = tuple(sh2sl(start_sh, 0))
    p48_tr = []
    for f in range(NF):
        pl_, (yaw, roll) = p48_local(t, f, start_l)
        q = Quaternion((0, 0, 1), math.radians(yaw)) @ Quaternion((1, 0, 0), math.radians(roll))
        SD.key_xform(p48, f, loc=Vector(pl_) * MM, quat=q)
        p48_tr.append(tuple(pl_))
    for o in [p48] + list(p48.children_recursive):                  # 飞进来之前藏着（藏掉的刻字、卡口销不动）
        if o not in hidden48:
            for f_, h_ in ((0, True), (t.enter[0] - 1, True), (t.enter[0], False)):
                o.hide_render = o.hide_viewport = h_
                o.keyframe_insert("hide_render", frame=f_)
                o.keyframe_insert("hide_viewport", frame=f_)

    # ---- 销子锁（3-01 末帧的样子：钥匙插着、锁芯转 32°、锁梁弹起；剖开）+ 料杆
    L1 = Vector((c23.x + LOCK_FROM_CELL[0] * MM, c23.y + LOCK_FROM_CELL[1] * MM, zb + LOCK_FROM_CELL[2] * MM))
    lk = M3.h06_pin_lock(Kt, preset="own", cut=True)
    D.rest(lk)
    lk["drill_role"] = "lock"
    bpy.context.view_layer.update()
    pts = [m.matrix_world @ Vector(c) for m in [lk] + list(lk.children_recursive)
           if m.type in ("MESH", "CURVE", "FONT") and not m.hide_render for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c0 = (lo + hi) / 2
    O1 = L1 - Vector((c0.x, 0.0, c0.z)) * LS
    MS = Matrix.Translation(O1) @ Matrix.Diagonal((LS, LS, LS, 1))
    lk.matrix_world = MS
    jr = D.rig(lk)
    jr["plug"].rotation_euler.x = math.radians(32.0)
    jr["shackle"].location.z = 3.6 * MM

    def LW(p):
        return MS @ (Vector(p) * MM)
    key = D.h02_key(Kt, which="048", scale=KEY_S)
    key["drill_role"] = "key"
    for o in key.children_recursive:
        if o.type == "FONT":
            SD.hide_tree(o)
        elif o.type == "MESH":
            bb = [Vector(v) for v in o.bound_box]
            cc = sum(bb, Vector()) / 8 / MM
            if abs(cc.x + 3.5) < 0.3 and abs(cc.y + 3.54) < 0.3 and cc.z > 0.6:
                SD.hide_tree(o)
    Wv, Uv = Vector((0, -1, 0)), Vector((0, 0, 1))
    origin = Vector((0, -1.5, -0.55))
    rot3 = Matrix((-Wv, -Uv, -Vector((1, 0, 0)))).transposed()
    off = float(key["insertion_offset_u_mm"])
    Kin = Matrix.Translation(((origin + off * Uv) - rot3 @ Vector((6.5 * KEY_S, 0, 0))) * MM) @ rot3.to_4x4() @ Matrix.Diagonal((KEY_S, KEY_S, KEY_S, 1))
    pv = origin * MM
    Mk = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(32.0), 4, Wv) @ Matrix.Translation(-pv) @ Kin
    key.matrix_world = Matrix.Translation(O1) @ Matrix.Diagonal((LS, LS, LS, 1)) @ Mk
    rack = bpy.data.objects.new("drill_rack", None)
    sc.collection.objects.link(rack)
    rack["drill_role"] = "rack"
    blue = Kt.cat("blue")

    def rod(name, pl_):
        return KP.tube_w(name, [tuple(v / MM for v in LW(p)) for p in pl_], ROD_R, blue, rack)
    z_board = (zb - O1.z) / (MM * LS)
    rod("rack_main_L", [(ROD_X0, ROD_Y, ROD_Z), (-14.0, ROD_Y, ROD_Z)])
    rod("rack_main_R", [(14.0, ROD_Y, ROD_Z), (ROD_XR, ROD_Y, ROD_Z)])
    rod("rack_post_L", [(ROD_X0, ROD_Y, ROD_Z), (ROD_X0, ROD_Y, z_board + 0.5)])
    rod("rack_post_R", [(ROD_XR, ROD_Y, ROD_Z), (ROD_XR, ROD_Y, z_board + 0.5)])
    for sgn in (-1, 1):
        KP.gate_geo(f"rack_lockgate_{'L' if sgn < 0 else 'R'}", LW((sgn * 14.0, ROD_Y, ROD_Z)), LW((sgn * 10.05, ROD_Y, ROD_Z)), blue, rack)

    # ---- 镜头
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = SENSOR
    cam_d.clip_start = 0.0002
    cam_d.clip_end = 30.0
    # K0：3-01 末帧镜头在锁局部里的位置和朝向（3-01 镜头在原点看 +Y、+Z 向上；shift 折进视线方向）
    hj = json.loads(HO_301.read_text(encoding="utf-8"))["tail_pose"]
    M301 = Matrix(hj["matrix"])
    Mi = M301.inverted()
    c_l = (Mi @ Vector((0, 0, 0))) / MM
    R301 = M301.to_3x3().normalized()
    d_l = (R301.transposed() @ Vector((0.318, 1.0, 0.043))).normalized()
    up_l = (R301.transposed() @ Vector((0, 0, 1))).normalized()
    v = -d_l
    k0 = dict(f=0, space="lock", tgt=tuple(c_l + d_l * 8.0), az=math.degrees(math.atan2(v.y, v.x)), el=math.degrees(math.asin(v.z)), dist=8.0, lens=23.4)
    q0 = d_l.to_track_quat("-Z", "Y")
    r0_ = math.degrees(math.atan2(-up_l.dot(q0 @ Vector((1, 0, 0))), up_l.dot(q0 @ Vector((0, 1, 0)))))
    k0["roll"] = r0_
    pins_l = Vector((1.8, -4.75, 2.6))
    kr = dict(f=KR_F, space="lock", tgt=tuple(pins_l), az=k0["az"] - 8.0, el=26.0, dist=34.0, lens=30.0, roll=0.0, ease="in")   # 起步缓（第 0→1 帧亮度跳 0.076 > 0.06）
    K1 = dict(space="shell", tgt=(0.0, -1.0, 6.0), az=-40.0, el=30.0, dist=122.0, lens=50.0)
    K2 = dict(space="shell", tgt=(0.0, -2.5, 4.5), az=-50.0, el=50.0, dist=72.0, lens=50.0)   # 76 时落位帧三台只占 48%（18 验收 ≥ 50%）

    def mix(a, b, u):
        return dict(space=a["space"], tgt=tuple(lerp(x, y, u) for x, y in zip(a["tgt"], b["tgt"])), az=lerp(a["az"], b["az"], u),
                    el=lerp(a["el"], b["el"], u), dist=a["dist"] * (b["dist"] / a["dist"]) ** u, lens=lerp(a["lens"], b["lens"], u))
    zax = O[1].z
    LENS_END = 135.0                                                 # 长焦：048 的柄伸出孔口 10 mm，镜头近了柄会被透视放大、盖住红环
    D_END = (LENS_END / 36.0 * SD.OUT_W) * RING_R1 / 700.0               # 末帧：红环外圈 = 700 px
    keys = [k0, kr,
            dict(f=t.cam_out[1], ease="out", **K1),
            dict(f=t.cam_in[1], ease="in", **mix(K1, K2, 0.27)),
            dict(f=t.cam_in[2], ease="out", **K2),
            dict(f=t.enter[0], space="shell", tgt=(0.5, -3.0, 4.6), az=-47.0, el=47.0, dist=68.0, lens=50.0),
            dict(f=t.plug[1], space="shell", tgt=(0.8, -5.0, zax), az=-42.0, el=40.0, dist=60.0, lens=50.0),
            dict(f=t.off[1], space="shell", tgt=(0.3, -4.5, zax), az=-45.0, el=40.0, dist=56.0, lens=50.0),
            dict(f=t.pocket[0], space="shell", tgt=(0.0, -4.8, zax), az=-40.0, el=34.0, dist=50.0, lens=50.0),
            # pocket 一步落到孔口正前方，635–703 停住（只有红环亮、048 柄上轮廓光）：慢绕 + 大虚背景会被 S4 当成混帧（第一版 650–684 共 35 帧）
            dict(f=t.pocket[1], space="sock", tgt=(RING_W1, 0.0, 0.0), az=-8.0, el=6.0, dist=D_END * 1.025, lens=LENS_END),
            dict(f=t.fill[0], space="sock", tgt=(RING_W1, 0.0, 0.0), az=-8.0, el=6.0, dist=D_END * 1.025, lens=LENS_END),
            dict(f=t.fill[1], space="sock", tgt=(RING_W1, 0.0, 0.0), az=0.0, el=0.0, dist=D_END * 1.012, lens=LENS_END),
            dict(f=NF - 1, space="sock", tgt=(RING_W1, 0.0, 0.0), az=0.0, el=0.0, dist=D_END, lens=LENS_END, ease="linear")]
    rigc = SD.CamRig(keys, lambda f: sock_mat(f), MM * SS,
                     spaces={"lock": (lambda f: Matrix.Translation(O1), MM * LS), "shell": (lambda f: Msh, MM)})
    rigc.shake(t.clack[1], 0.25, 4)

    def drift(f, eye, tgt):
        d = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        upv = right.cross(fwd)
        k = ramp(f, 20, 60) * (1 - ramp(f, t.pocket[0], t.pocket[1]))
        o = (right * 0.008 * math.sin(f / 97.0) + upv * 0.006 * (math.cos(f / 131.0) - 1.0)) * d * k
        return o, o * 0.6
    recs = rigc.bake(cam, NF, drift=drift)
    for f in range(NF):                                              # 段首去掉手持感；段尾 40 帧收掉（末帧圆要和 3-03 对上，误差 ≤ 4 px）
        w = (1 - ramp(f, 0, 20)) + ramp(f, NF - 46, NF - 12)
        if w <= 0:
            continue
        eye, tgt_, lens, q = recs[f]
        e2, t2, l2, roll = rigc.at(f)
        q_pure = (t2 - e2).normalized().to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(roll))
        q2 = q.slerp(q_pure, clamp(w))
        cam.rotation_quaternion = q2
        cam.keyframe_insert("rotation_quaternion", frame=f)
        recs[f] = (eye, tgt_, lens, q2)

    # ---- 灯：大板那套（以细胞壳为中心）+ 壳前一盏柔光
    KP.lights(c23.x, c23.y, 1.0)
    fl_d = bpy.data.lights.new("drill_front_fill", "AREA")
    fl_d.shape = "RECTANGLE"
    fl_d.size, fl_d.size_y = 0.20, 0.12
    fl_d.color = (1, .98, .95)
    fl_d.energy = 5.0
    fo = bpy.data.objects.new("drill_front_fill", fl_d)
    sc.collection.objects.link(fo)
    ctr = sh2w((0, -3, 5))
    fo.location = ctr + Vector((-0.06, -0.30, 0.16))
    fo.rotation_euler = (ctr - fo.location).to_track_quat("-Z", "Y").to_euler()
    # 轮廓光：只照 048（灯光链接），"key" 上亮起
    coll = bpy.data.collections.new("drill302_lit_048")
    for o in [p48] + list(p48.children_recursive):
        if o.type == "MESH":
            coll.objects.link(o)
    rl = bpy.data.lights.new("drill302_rim_048", "AREA")
    rl.shape = "DISK"
    rl.size = 0.004
    rl.color = (0.92, 0.96, 1.0)
    ro = bpy.data.objects.new("drill302_rim_048", rl)
    sc.collection.objects.link(ro)
    ro.light_linking.receiver_collection = coll
    ro.parent = socks[1]
    ro.matrix_parent_inverse = Matrix.Identity(4)
    ro.location = Vector((40.0, 26.0, 30.0)) * MM                    # 插座局部：孔口右上后方，打 048 柄的边
    ro.rotation_mode = "QUATERNION"
    ro.rotation_quaternion = (Vector((18.0, 0, 0)) - Vector((40.0, 26.0, 30.0))).to_track_quat("-Z", "Y")
    # 段尾提亮（18 的 1.8 段尾浅色面）：048 柄是镜面金，正对镜头时映的是镜头背后的暗处（第一版末 15 帧 0.37）。
    # 镜头背后孔轴上放一块只照 048、只给反射看的柔光板，柄面映出亮的一片；pocket 推进的大动作里亮起
    sb = bpy.data.lights.new("drill302_softbox_048", "AREA")
    sb.shape = "DISK"
    sb.size = SB_SIZE * D_END * MM
    sb.color = (1.0, 0.98, 0.94)
    sbo = bpy.data.objects.new("drill302_softbox_048", sb)
    sc.collection.objects.link(sbo)
    sbo.light_linking.receiver_collection = coll
    sbo.visible_camera = False
    sbo.visible_diffuse = False
    sb.use_shadow = False
    sbo.parent = socks[1]
    sbo.matrix_parent_inverse = Matrix.Identity(4)
    sbo.location = Vector((RING_W1 + SB_DIST * D_END, 0.0, 0.0)) * MM     # 插座局部毫米（父物体带 0.232 缩放）
    sbo.rotation_mode = "QUATERNION"
    sbo.rotation_quaternion = Vector((-1.0, 0, 0)).to_track_quat("-Z", "Y")
    for f in range(NF):
        sb.energy = SB_W * ramp(f, t.pocket[0] + 10, t.pocket[1] - 5)
        sb.keyframe_insert("energy", frame=f)
    # 段首转场灯（18 的 1.8）：3-01 11-23 新末帧对着金色锁芯和白色上销，全虚时平均亮度只有 0.40。
    # 镜头左上后方一盏只照销子锁的面光（灯光链接），0–20 帧开、30 帧关，"功率为主光 3 倍"按照度折算（主光 120 W、离 1.27 m）
    lcol = bpy.data.collections.new("drill302_lit_lock")
    for o in [lk] + list(lk.children_recursive):
        if o.type == "MESH":
            lcol.objects.link(o)
    e0_, t0_ = Vector(recs[0][0]), Vector(recs[0][1])
    dv_ = e0_ - t0_
    up_ = recs[0][3] @ Vector((0, 1, 0))
    rt_ = recs[0][3] @ Vector((1, 0, 0))
    hl_loc = t0_ + dv_ * 2.0 + up_ * (0.8 * dv_.length) - rt_ * (0.5 * dv_.length)
    hl = bpy.data.lights.new("drill302_trans_head", "AREA")
    hl.shape = "DISK"; hl.size = 1.5 * dv_.length
    hl.color = (1.0, 0.98, 0.95)
    hl.use_shadow = False
    hlo = bpy.data.objects.new("drill302_trans_head", hl)
    sc.collection.objects.link(hlo)
    hlo.location = hl_loc
    hlo.rotation_euler = (t0_ - hl_loc).to_track_quat("-Z", "Y").to_euler()
    hlo.visible_camera = False
    hlo.light_linking.receiver_collection = lcol
    en_h = 3.0 * 120.0 * ((t0_ - hl_loc).length / 1.27) ** 2 * HEAD_K
    for fk, v in ((0, 1.0), (20, 1.0), (30, 0.0)):
        hl.energy = en_h * v
        hl.keyframe_insert("energy", frame=fk)
    for f in range(NF):
        rl.energy = 0.05 * ramp(f, t.key[0], t.key[1], ease_out) * (1 - 0.4 * ramp(f, t.key[2], t.fill[1]))
        rl.keyframe_insert("energy", frame=f)

    # ---- 焦点和光圈（2 mm 传感器：光圈按"焦点前后 Δ 毫米处弥散 c 像素"逐帧解）
    def mid_c(f):
        return sh2w(O_at(f, 1) + Vector((0, -1.0, 0.0)))

    def mouth(f, w=RING_W1):
        return sock_mat(f) @ (Vector((w, 0, 0)) * MM * SS)

    def p48_w(f):
        return sock_mat(f) @ ((Vector(p48_tr[f]) + Vector((5.8, 0, 0))) * MM * SS)
    shell_c = sh2w((0, -1, 5))
    focus_plan = [(0, lambda f: shell_c), (10, lambda f: LW(pins_l)), (30, lambda f: shell_c), (t.lamps[1] - 6, mid_c),
                  (t.enter[0] + 10, p48_w), (t.swap[0] - 4, lambda f: mouth(f, SEATW + 4)), (t.off[1] + 20, mid_c),
                  (t.pocket[0] + 20, lambda f: mouth(f)), (t.key[1] - 4, p48_w)]
    # 末尾不再拉回孔口：柄面和红环前后只差 0.4 mm，弥散 ≈ 2 px；第一版 716–736 的回拉焦点被 S4 当成混帧

    def focus_at(f):
        p = focus_plan[0][1](f)
        for (fa, fn) in focus_plan[1:]:
            if f >= fa - 10:
                p = p.lerp(fn(f), smooth((f - fa + 10) / 20.0))
        return p
    # (起帧, Δ 毫米, 弥散像素)；段首 0–9 帧固定 f/1（全虚）
    coc_plan = [(10, 20.0, 5.0), (t.cam_out[1], 16.0, 4.0), (t.cam_in[2], 6.0, 4.0), (t.pocket[0], 6.0, 4.0), (t.pocket[1], 2.0, 10.0)]

    def target_coc(f):
        d_, c_ = coc_plan[0][1], coc_plan[0][2]
        for (fa, da, ca), (fb, db, cb) in zip(coc_plan, coc_plan[1:] + [(10 ** 6, coc_plan[-1][1], coc_plan[-1][2])]):
            if fa <= f:
                u = 0.0 if f < fb - 12 else smooth((f - fb + 12) / 24)
                d_, c_ = lerp(da, db, u), lerp(ca, cb, u)
        return d_, c_
    dof = cam_d.dof
    dof.use_dof = True
    dof.aperture_blades = 0
    fst, focus_d = [], []
    for f in range(NF):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        S = max(0.0015, (focus_at(f) - eye).dot(fwd))
        if f < HEAD_FOC:                                             # 段首全虚 → 清楚：对焦距离按对数从 1.5 mm 缓到第 HEAD_FOC 帧的目标，不在第 10 帧突然对上
            eH, _, _, qH = recs[HEAD_FOC]
            SH = max(0.0015, (focus_at(HEAD_FOC) - eH).dot(qH @ Vector((0, 0, -1))))
            S = math.exp(lerp(math.log(0.0015), math.log(SH), smooth(f / HEAD_FOC)))
        fpx = lens / 36.0 * SD.OUT_W
        fl = lens * SENSOR / 36.0 * MM
        dm, cp = target_coc(f)
        N = fpx * fl * abs(1 / S - 1 / (S + dm * MM)) / cp
        N = lerp(1.0, N, ramp(f, 8, 22))
        N = min(32.0, max(0.8, N))
        dof.focus_distance = S
        dof.aperture_fstop = N
        dof.keyframe_insert("focus_distance", frame=f)
        dof.keyframe_insert("aperture_fstop", frame=f)
        fst.append(N)
        focus_d.append(S)

    SD.linear_all([cam, shell, atp, p48, ro] + socks + list(shell.children_recursive) + list(p48.children_recursive)
                  + [o for o in bpy.data.objects if o.type == "LIGHT"])
    for m in lamp_mats + [ring_m]:
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            import bl_guide as BG
            for fc in BG._fcurves(m.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- 机检数据 + 给合成用的投影
    def proj(f, p):
        return SD.project(recs[f], p, sensor_w=36.0)

    def ring_screen(f, R=RING_R1):
        c = proj(f, mouth(f))
        rr = []
        for k in range(24):
            a_ = 2 * math.pi * k / 24
            pp = proj(f, sock_mat(f) @ (Vector((RING_W1, R * math.cos(a_), R * math.sin(a_))) * MM * SS))
            if pp and c:
                rr.append(math.hypot(pp[0] - c[0], pp[1] - c[1]))
        return (c[0], c[1], sum(rr) / len(rr)) if c and rr else None
    sc.frame_set(0)
    bpy.context.view_layer.update()
    sock_corners = []
    for s_ in socks:
        pts_ = [m.matrix_world @ Vector(cn) for m in [s_] + list(s_.children_recursive) if m.type == "MESH" and not m.hide_render
                and m.get("drill_role") is None and not any(a.get("drill_role", "").startswith(("atp", "048")) for a in _anc(m)) for cn in m.bound_box]
        lo_ = Vector((min(p.x for p in pts_), min(p.y for p in pts_), min(p.z for p in pts_)))
        hi_ = Vector((max(p.x for p in pts_), max(p.y for p in pts_), max(p.z for p in pts_)))
        sock_corners.append([Vector((x, y, z)) for x in (lo_.x, hi_.x) for y in (lo_.y, hi_.y) for z in (lo_.z, hi_.z)])

    def box_of(f, corners):
        pp = [proj(f, c) for c in corners]
        pp = [p for p in pp if p]
        if not pp:
            return None
        return [min(p[0] for p in pp), min(p[1] for p in pp), max(p[0] for p in pp), max(p[1] for p in pp)]
    frames = []
    for f in range(NF):
        bx = box_of(f, [c for cs in sock_corners for c in cs])
        frames.append(dict(f=f, eye=list(recs[f][0]), q=list(recs[f][3]), lens=recs[f][2], fstop=fst[f], focus=focus_d[f],
                           ring=list(ring_screen(f)) if f >= t.pocket[0] - 60 and ring_screen(f) else None,
                           socks=bx, p48=list(proj(f, p48_w(f)) or [0, 0, 0]), p48_mid=list(proj(f, sock_mat(f) @ (Vector(p48_tr[f]) * MM * SS)) or [0, 0, 0]),
                           lamp=[lamp_level(t, f, i) for i in range(3)], lid=lid_angle(t, f)))
    (W / "cam.json").write_text(json.dumps(dict(seg=seg, nf=NF, frames=frames)), encoding="utf-8")

    def area_pct(bx):
        if not bx:
            return None
        x0, y0, x1, y1 = max(0, bx[0]), max(0, bx[1]), min(SD.OUT_W, bx[2]), min(SD.OUT_H, bx[3])
        return round(max(0, x1 - x0) * max(0, y1 - y0) / (SD.OUT_W * SD.OUT_H) * 100, 1)
    acc = dict(sensor_mm=SENSOR, socket_scale=SS, socket_origins_mm=[[round(v, 3) for v in o_] for o_ in O], atp_rest_z=round(rest_z, 3))
    re = ring_screen(NF - 1)
    H0 = json.loads(HANDOFF.read_text(encoding="utf-8")) if HANDOFF.exists() else dict(ring_cx=960.0, ring_cy=540.0, ring_r=700.0)
    acc["handoff_target"] = {k: H0[k] for k in ("ring_cx", "ring_cy", "ring_r", "by")}
    acc["ring_end"] = [round(x, 2) for x in re]
    acc["ring_end_err_px"] = round(math.hypot(re[0] - H0["ring_cx"], re[1] - H0["ring_cy"]), 2)
    acc["ring_end_r_err_px"] = round(abs(re[2] - H0["ring_r"]), 2)
    acc["ring_end_width_px"] = round(2 * re[2], 1)
    acc["ring_width_px"] = {str(f): round(2 * ring_screen(f)[2], 1) for f in (t.pocket[1], t.fill[0], t.fill[1], NF - 1)}
    acc["K2_socks_area_pct"] = {str(f): area_pct(frames[f]["socks"]) for f in (t.cam_in[2], t.run[1], t.enter[0], t.clack[1], t.off[1], t.pocket[0])}
    acc["K2_socks_box"] = {str(f): [round(v) for v in frames[f]["socks"]] for f in (t.cam_in[2], t.run[1], t.off[1])}
    # 断电：四样（灯、灯光、活塞、细胞）在哪一帧停下
    pis_mid = [mach[1][f][0] for f in range(NF)]
    cel_mid = [mach[1][f][1] for f in range(NF)]
    still = lambda arr: next(f for f in range(t.off[0], NF) if all(abs(arr[g] - arr[f]) < 1e-4 for g in range(f, min(NF, f + 30))))  # noqa: E731
    acc["power_off"] = dict(word_f=t.off[1], lamp_off_f=next(f for f in range(t.off[0], NF) if lamp_level(t, f, 1) <= 0.02),
                            piston_stop_f=still(pis_mid), cell_stop_f=still(cel_mid), piston_value=round(pis_mid[t.off[1] + 5], 2))
    acc["lamps_on_f"] = [next(f for f in range(NF) if lamp_level(t, f, i) > 0.5) for i in range(3)]
    acc["lid_peak"] = round(max(lid_angle(t, f) for f in range(NF)), 2)
    acc["k0"] = dict(eye_lock_mm=[round(v, 2) for v in c_l], az=round(k0["az"], 2), el=round(k0["el"], 2), roll=round(r0_, 2))
    coc = []
    for f in range(0, NF, 30):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        S = focus_d[f]
        fpx = lens / 36.0 * SD.OUT_W
        fl = lens * SENSOR / 36.0 * MM
        dm, cp = target_coc(f)
        coc.append(dict(f=f, N=round(fst[f], 2), S_mm=round(S / MM, 2), coc_at_dm=round(fpx * fl / fst[f] * abs(1 / S - 1 / (S + dm * MM)), 2),
                        coc_board=round(fpx * fl / fst[f] * abs(1 / S - 1 / max(1e-4, (Vector((c23.x, c23.y, zb)) - eye).dot(fwd))), 2)))
    acc["coc"] = coc
    (W / "build_check.json").write_text(json.dumps(acc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL acc", json.dumps({k: v for k, v in acc.items() if k != "coc"}, ensure_ascii=False, default=str)[:3000], flush=True)
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


def _anc(o):
    p = o.parent
    while p is not None:
        yield p
        p = p.parent


# ================================================================ 穿模检查
def _meshes(root, skip_roles=()):
    out = []
    for o in [root] + list(root.children_recursive):
        nm = o.name.split(".")[0]
        if o.type not in ("MESH", "CURVE", "FONT") or nm.endswith("_cut") or o.hide_render:
            continue
        if any(a.get("drill_role") in skip_roles for a in [o] + list(_anc(o))):
            continue
        out.append(o)
    return out


def clip_plan(sc):
    """048 vs 中间那台；ATP vs 中间那台；ATP vs 048；ATP、048 vs 壳和左右两台；上盖 vs 插座和插头；"咔"时中间那台 vs 旁边。"""
    import bpy
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    shell = R["shell"]
    plugs = ("atp_0", "atp_1", "atp_2", "048")
    socks = [R[f"sock_{i}"] for i in range(3)]
    s_m = [_meshes(s_, skip_roles=plugs) for s_ in socks]
    a_m = _meshes(R["atp_1"])
    k_m = _meshes(R["048"])
    side_plugs = _meshes(R["atp_0"]) + _meshes(R["atp_2"])
    lid_j = [o for o in shell.children if o.type == "EMPTY" and o.get("role") == "shell"][0]
    shell_all = _meshes(shell, skip_roles=plugs + ("sock_0", "sock_1", "sock_2"))
    lid_m = [o for o in shell_all if lid_j in set(_anc(o))]
    fixed_m = [o for o in shell_all if o not in lid_m]
    frames = set(range(0, NF, 3)) | set(range(t.shell[0], t.shell[2] + 10)) | set(range(t.enter[0], t.atp_fall[1] + 16)) \
        | set(range(t.home[0] - 6, t.clack[2] + 4))

    def groups(f):
        g = [("048_vs_mid", k_m, s_m[1]), ("atp_vs_mid", a_m, s_m[1]), ("atp_vs_048", a_m, k_m),
             ("atp_vs_rest", a_m, fixed_m + lid_m + s_m[0] + s_m[2] + side_plugs),
             ("048_vs_rest", k_m, fixed_m + lid_m + s_m[0] + s_m[2] + side_plugs)]
        if t.shell[0] <= f <= t.shell[2] + 10:
            g.append(("lid_vs_inside", lid_m, s_m[0] + s_m[1] + s_m[2] + side_plugs + a_m + [o for o in fixed_m if "nucleus" in o.name]))
        if t.clack[0] <= f <= t.clack[2] + 4:
            g.append(("mid_vs_side", s_m[1], s_m[0] + s_m[2] + side_plugs + [o for o in fixed_m if "nucleus" not in o.name and o.name != "u05_seat_1"]))
            # u05_seat_1 是中间那台的托座：插座坐在它顶面上（面贴面），"咔"只往上跳，贴面不算穿模；只在零跳高的帧被报，故不查
        return [x + (shell,) for x in g]
    near = s_m[0] + s_m[1] + s_m[2] + a_m + k_m + side_plugs + shell_all + _meshes(R["lock"]) + _meshes(R["key"])
    return dict(frames=sorted(frames), groups=groups, cam_near=lambda f: near, ref=None)


# ================================================================ 合成：标签、批注、出处行
def ink_arrow(*a, **k):
    import drill_304
    return drill_304.ink_arrow(*a, **k)


def _src_layer(alpha):
    from PIL import Image, ImageDraw
    lay = Image.new("RGBA", (SD.OUT_W, SD.OUT_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    fnt = SD._font(30)
    x0, y0, y1 = SRC_BOX
    tb = dr.textbbox((0, 0), SRC_TOY, font=fnt, anchor="lm")
    pad = 14
    dr.rounded_rectangle([x0, y0, x0 + (tb[2] - tb[0]) + 2 * pad, y1], radius=10, fill=(*BONE, int(255 * 0.8 * alpha)))
    dr.text((x0 + pad, (y0 + y1) / 2), SRC_TOY, font=fnt, fill=(*INK, int(255 * alpha)), anchor="lm")
    return lay


def comp_frames(seg, flist=None):
    import numpy as np
    from PIL import Image
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    camj = json.loads((W / "cam.json").read_text(encoding="utf-8"))["frames"]
    for f in (flist if flist is not None else range(NF)):
        pil = Image.open(W / "frames" / f"f_{f:04d}.png").convert("RGBA")
        c = camj[f]
        # 标签 proteins：三台上方，proteins 出、drugs 前 6 帧退
        kl = ramp(f, t.lamps[1] - 2, t.lamps[1] + 10, ease_out) * (1 - ramp(f, t.enter[1] - 12, t.enter[1] - 6))
        if kl > 0.003 and c["socks"]:
            x0, y0, x1, y1 = c["socks"]
            tx, ty = (x0 + x1) / 2, max(70.0, y0 - 24 - 8 * (1 - kl))
            it = dict(text="proteins", xy=(tx, ty), size=44, color=INK, anchor="ms", shadow=False, halo=BONE)
            pil = Image.alpha_composite(pil, SD.draw_text_layer([it], lambda it_: kl))
        # 批注 drug：drugs 后 4 帧出，细箭头指假插头的柄，pocket 前退
        kd = ramp(f, t.enter[1] + 4, t.enter[1] + 16, ease_out) * (1 - ramp(f, t.pocket[1] - 30, t.pocket[1] - 6))
        if kd > 0.003:
            px, py = c["p48"][0], c["p48"][1]
            tx, ty = min(SD.OUT_W - 150.0, px + 190), max(120.0, py - 150)
            it = dict(text="drug", xy=(tx, ty), size=40, color=INK_NOTE, hand=True, anchor="ms", stroke=NOTE_STROKE, shadow=False)
            pil = Image.alpha_composite(pil, SD.draw_text_layer([it], lambda it_: kd))
            ke = clamp((f - t.enter[1] - 8) / 14.0)
            if ke > 0:
                ang = math.atan2(ty - 30 - py, tx - 40 - px)
                p1 = (px + 46 * math.cos(ang), py + 46 * math.sin(ang))
                pil = Image.alpha_composite(pil, ink_arrow((tx - 40, ty - 30), p1, 0.12, ease_out(ke), width=4.0, color=INK_NOTE, alpha=kd))
        base_a = ramp(f, 10, 30) * (1 - ramp(f, NF - 22, NF - 2))
        if base_a > 0.003:
            pil = Image.alpha_composite(pil, _src_layer(base_a))
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


# ================================================================ 声音
def audio(seg):
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    C = SD.click

    def snap(s, g=0.20):
        return C([(3100, 1.0), (5200, 0.5)], 9, 3, g, s)

    def clack(s, g=0.22):
        return C([(900, 1.0), (1900, 0.6), (3300, 0.3)], 22, 5, g, s)

    def thunk(s, g=0.22):
        return C([(260, 1.0), (520, 0.5), (1400, 0.25)], 40, 6, g, s)

    def tick(s, g=0.08):
        return C([(2400, 1.0), (4100, 0.4)], 6, 2, g, s)
    hits = [(0, SD.whoosh(0.55, 0.12, 30, f0=2600, f1=400), 0.4),
            (t.shell[0] + 5, snap(1, 0.12), 0.5), (t.shell[1], thunk(2, 0.14), 0.5)]
    for i in range(3):
        hits.append((t.lamps[1] + 4 * (i - 1), tick(3 + i, 0.10), 0.35 + 0.15 * i))
    hits += [(t.run[1], tick(7, 0.07), 0.35), (t.run[1] + 2, tick(8, 0.06), 0.65),
             (t.enter[0] + 4, SD.whoosh((t.enter[1] - t.enter[0]) / SD.FPS, 0.07, 9, f0=500, f1=2400), 0.75),
             (t.swap[0] + 2, clack(10, 0.14), 0.5), (t.atp_fall[1], tick(11, 0.12), 0.4), (t.atp_fall[1] + 7, tick(12, 0.07), 0.4),
             (t.plug[1], clack(13, 0.18), 0.55), (t.clack[1], clack(14, 0.26), 0.5), (t.clack[1] + 1, snap(15, 0.18), 0.5),
             (t.off[1], thunk(16, 0.18), 0.5), (t.off[1] + 2, tick(17, 0.06), 0.5),
             (t.ring[0] - 4, SD.whoosh(0.5, 0.05, 18, f0=300, f1=1500), 0.5)]
    SD.mix_audio(seg, hits, W / "mix.wav")
    (W / "audio_hits.json").write_text(json.dumps([[h[0], round(h[2], 2)] for h in hits]), encoding="utf-8")


# ================================================================ 自检
def check(seg):
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
    res["frames_below_0.35"] = [int(i) for i in np.where(luma < 0.35)[0]]
    res["luma_jumps_gt_0.06"] = [[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma)) if abs(luma[i] - luma[i - 1]) > 0.06]
    res["luma_mean"] = round(float(luma.mean()), 3)
    res["luma_min"] = [int(np.argmin(luma)), round(float(luma.min()), 3)]
    res["luma_head15"] = [round(float(x), 3) for x in luma[:15]]
    res["luma_tail15"] = [round(float(x), 3) for x in luma[-15:]]
    res["luma_every_30"] = [round(float(x), 3) for x in luma[::30]]
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-map", "0:a", "-f", "null", "-"], capture_output=True, text=True)
    res["audio_ok"] = pr.returncode == 0
    M = json.loads((SD.MAPD / "master_v2.json").read_text(encoding="utf-8"))          # keys 是按 master_v2 算的
    g = dict(next(x for x in M["groups"] if x["group"] == seg or seg in x["segs"]))
    g["events"] = K["events"]
    tmp_map = W / "map_with_events.json"
    tmp_map.write_text(json.dumps(dict(fps=M.get("fps", 60), groups=[g]), ensure_ascii=False), encoding="utf-8")
    py = SD.ROOT / "_env/footage/Scripts/python.exe"
    r = subprocess.run([str(py), str(SD.MAPD / "check_sync.py"), str(OUT_MP4), seg], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(SD.ROOT), env=dict(os.environ, PYTHONIOENCODING="utf-8", CDK20_MAP=str(tmp_map)))
    cs = SD.MAPD / "_reports" / f"sync_{seg}_{OUT_MP4.stem}.json"
    res["check_sync_out"] = (r.stdout[-3000:] + r.stderr[-800:]).strip()
    if cs.exists():
        res["check_sync"] = json.loads(cs.read_text(encoding="utf-8"))
    clip = W / "clip.json"
    if clip.exists():
        res["clip"] = {k: v for k, v in json.loads(clip.read_text(encoding="utf-8")).items() if k != "hits"}
    bc = W / "build_check.json"
    if bc.exists():
        res["acceptance"] = {k: v for k, v in json.loads(bc.read_text(encoding="utf-8")).items() if k != "coc"}
    (W / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL check", json.dumps({k: v for k, v in res.items() if k not in ("check_sync", "luma_every_30")}, ensure_ascii=False, default=str)[:5000], flush=True)


def sheet(seg, step="6"):
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
        name = f"16_钻取_3-02_抽帧_{len(pages) + 1:02d}.jpg"
        im.save(SD.work(seg) / name, quality=86)
        pages.append(name)
    (SD.work(seg) / "sheets.json").write_text(json.dumps(dict(step=step, pages=pages, frames=idx)), encoding="utf-8")
    print("DRILL sheet", pages, flush=True)
