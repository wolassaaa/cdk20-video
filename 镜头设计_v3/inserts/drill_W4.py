"""HKBU SCIE1007 课程作业的科普视频：第三段三维钻取 W4（音乐段，7.87 s = Sacrifice 16 拍）—— CDK20 插座内部，048 转到底（设计：深化/06_插座比喻.md 第四节 W4，11-20）。

没有念词：时间基准是歌的拍子。帧号全由卡点表 音乐/卡点/W4_Sacrifice.json 算（make_keys），做法见技能 beat-retime。
场景和 5-04 同一台插座、同一个浮着的位姿（drill_504.py 的常量），一镜到底：
  第 0–2 拍   breakdown（底鼓停）：盖开着，ATP 插着、灯亮、光包流、活塞推细胞；048 从右前方摆到孔轴上，ATP 被顶出让开，
              第 2 拍底鼓和贝斯砸回来，048 插到底（缝 0.05，几乎不晃）。
  第 2–3 拍   镜头从侧面绕到机舱上方、钻到触点块；第 2.75 拍起 24 帧叠化到我们自己重新对接的 048 姿态（OUR RE-DOCKING）。
  第 3–9.75 拍 真实层停 3 秒：墨线的 048 从口袋外转进对接姿态，第 6 拍落定；口袋那一片表面染红、墨线圈出，第 6、8 拍圈跳一下；
              第 4 拍手写 048 落下。
  第 9.75–11 拍 叠化退回玩具，镜头退到侧面看孔口。
  第 11–12 拍 048 拧卡口 90°，第 12 拍（实底鼓）红卡扣扣上凸缘：灯灭、光包停在管里、活塞缩回、细胞停。
  第 12.5–14 拍 镜头后拉出插座，飞到主料杆；第 14 拍（第 4 小节第一拍）Improve 站亮成红色。
  第 14–16 拍 镜头沿料杆往前，看到 Cells 站（接 5-10）。
不穿模靠两件事：插头只沿孔轴进出、横移前 ATP 先让开（路径同 5-04、3-04 已验过的待机位），渲染前 clip 逐帧 BVH 查。
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_drill as SD  # noqa: E402
import drill_504 as D5  # noqa: E402
from shot_drill import MM, clamp, smooth, smoother, ease_out, ramp, lerp, settle  # noqa: E402

SEG = "W4"
BOARD = D5.BOARD
S, BC, H_FLOAT, FACE, H_ATP = D5.S, D5.BC, D5.H_FLOAT, D5.FACE, D5.H_ATP
LID_OPEN = D5.LID_OPEN
ALIGN = D5.ALIGN
H48 = (46.0, 24.0, 5.0)                               # 048 段首待机位（插座右前方，同 3-04 的 H48_IN 一带，验过不穿模）
FSTOP = dict(front=6.0, cabin=7.0, drill=14.0, board=4.0)
LIGAND = D5.DOCK / "dock_048.sdf"
SHEET = HERE.parent / "音乐" / "卡点" / "W4_Sacrifice.json"
OUT_MP4 = D5.OUT_DIR / "16_钻取_W4.mp4"
SRC_REAL = "CDK20: AlphaFold DB AF-Q8IZL9-F1 (predicted, CC BY 4.0) · 048 pose: our AutoDock Vina run"
T_TUBE = 45.0


# ================================================================ 卡点表 → 事件帧
def beat_sheet():
    s = json.loads(SHEET.read_text(encoding="utf-8"))
    s["beat_s"] = 60.0 / s["bpm"]
    return s


def fb(s, b):
    """第 b 拍 → 段内帧。"""
    return round(SD.FPS * s["beat_s"] * b)


def make_keys():
    """音乐段没有念词：按卡点表算出和 resolve.py 同格式的 keys（f_start / f_land / f_end），shot_drill.load_keys 读这里。"""
    s = beat_sheet()
    B = s["w4"]["beats"]
    DS = s["w4"].get("dissolve_f", 24)
    F = lambda k: fb(s, B[k])  # noqa: E731
    nf = fb(s, s["w4"]["nbeats"])
    ev = [
        ("swap", "eject_swap", "swap", F("swap") + 2, F("swap") + 14, F("swap") + 44, "第 0 拍：048 往孔口摆，ATP 被顶出、让到左前方（breakdown 的空拍里）"),
        ("p48_in", "plug_in", "p48_land", F("p48_land") - 21, F("p48_land"), F("p48_land") + 12, "第 2 拍：底鼓和贝斯回来，048 沿孔轴插到底"),
        ("drill_in", "camera_to", "drill", F("drill"), F("drill_land"), F("drill_land") + 16, "第 2–3 拍：镜头从侧面绕到机舱上方，钻到触点块"),
        ("real_in", "dissolve", "real_in", F("real_in"), F("real_in"), F("real_in") + DS, "第 2.75 拍：叠化到我们重新对接的 048 姿态（OUR RE-DOCKING）"),
        ("note048", "appear", "note", F("note") - 8, F("note"), F("note") + 12, "第 4 拍：配体旁手写的红色 048 落下"),
        ("lig_land", "move", "lig_land", F("real_in"), F("lig_land"), F("lig_land") + 18, "第 6 拍：墨线的 048 从口袋外转进对接姿态落定，口袋圈跳一下"),
        ("pulse2", "move", "pulse2", F("pulse2"), F("pulse2"), F("pulse2") + 16, "第 8 拍：口袋圈再跳一下"),
        ("real_out", "dissolve", "real_fade", F("real_fade"), F("real_fade"), F("real_fade") + DS, "第 9.25 拍：收回红环退回玩具（真实层共 3.6 秒）；11-21 Gemini 说 9.75 拍那次像硬切（叠化和镜头急退同时发生），提前半拍，先在停着的触点块上收完再退镜头"),
        ("cam_hold", "camera_to", "real_out", F("real_out"), F("real_out"), F("real_out") + DS, "第 9.75 拍前：玩具层镜头停在触点块上（原 real_out 的时刻，玩具帧不变）"),
        ("drill_out", "camera_to", "real_out", F("real_out"), F("twist") + 4, F("twist") + 4, "第 9.75–11 拍：镜头从触点块退到插座侧面，看孔口和卡扣"),
        ("twist", "twist", "twist", F("twist"), F("clamp"), F("clamp") + 14, "第 11–12 拍：048 拧卡口 90°"),
        ("clamp", "clamp", "clamp", F("clamp") - 4, F("clamp"), F("clamp") + 14, "第 12 拍：红卡扣扣上凸缘"),
        ("power_off", "power_off", "clamp", F("clamp"), F("clamp") + 2, F("clamp") + 20, "第 12 拍：灯灭、光包停在管里、活塞缩回、细胞停"),
        ("pull_out", "camera_to", "pull", F("pull"), F("improve"), F("improve"), "第 12.5–14 拍：镜头后拉出插座，飞到主料杆"),
        ("improve", "appear", "improve", F("improve") - 6, F("improve"), F("improve") + 20, "第 14 拍：主料杆上 Improve 站亮成红色"),
        ("to_cells", "camera_to", "improve", F("improve"), nf - 1, nf - 1, "第 14–16 拍：镜头沿料杆往前，看到 Cells 站（接 5-10）"),
    ]
    events = [dict(id=i, verb=v, beat=B[bk], f_start=a, f_land=l, f_end=e, means=m) for i, v, bk, a, l, e, m in ev]
    return dict(seg=SEG, len_f=nf, time_base="music", song=s["song"], bpm=s["bpm"], song_t0=s["w4"]["song_t_at_beat"][1], events=events)


class T:
    def __init__(self, EV):
        g = lambda i, k="f_land": EV[i][k]  # noqa: E731
        tri = lambda i: (g(i, "f_start"), g(i), g(i, "f_end"))  # noqa: E731
        self.swap = tri("swap")
        self.p48 = tri("p48_in")
        self.drill = tri("drill_in")
        self.real_in = (g("real_in"), g("real_in", "f_end"))
        self.real_out = (g("real_out"), g("real_out", "f_end"))
        self.cam_hold = (g("cam_hold"), g("cam_hold", "f_end"))
        self.note = tri("note048")
        self.name = (self.note[0], self.note[1])                         # drill_504.comp_frames 的手写编号
        self.lig = tri("lig_land")
        self.pushes = [g("lig_land"), g("pulse2")]                       # 口袋圈跳的拍
        self.drill_out = (g("drill_out", "f_start"), g("drill_out"))
        self.twist = tri("twist")
        self.clamp = tri("clamp")
        self.off = tri("power_off")
        self.pull = (g("pull_out", "f_start"), g("pull_out"))
        self.improve = tri("improve")
        self.end = g("to_cells")
        self.rush = (10 ** 6, 10 ** 6)


# ================================================================ 机构（纯函数）
def lid_angle(t, f):
    """盖整段开着（5-09 之后接进来就是开盖的机舱），只极轻地晃；卡扣扣上时被震一下。"""
    return LID_OPEN + 0.6 * math.sin(2 * math.pi * f / 170.0) + settle(f, t.clamp[1], 1.4, n=1.5, dur=16)


def lamp_level(t, f):
    """灯：卡扣扣上前一直亮；扣上前 2 帧闪一下，扣上后 4 帧灭到 0。"""
    c = t.clamp[1]
    if f < c - 2:
        return 1.0
    if f < c:
        return 0.35
    return lerp(0.6, 0.0, ramp(f, c, c + 4, ease_out))


def machine(t, nf, s):
    """光包每拍从源头出发（45 帧走完一根管），到活塞推一下 —— 推落在拍上；卡扣扣上那一帧全部停住，活塞缩回到 0、细胞不再长。"""
    beat_f = SD.FPS * s["beat_s"]
    c = t.clamp[1]
    arrivals = []
    b = -4
    while True:
        a = round(beat_f * b)
        if a >= c:
            break
        if b % 2 == 0:                                                   # 每两拍到一颗（偶数拍 = 实底鼓）
            arrivals.append(a)
        b += 1
    deps = [a - int(T_TUBE) for a in arrivals]
    deps.append(c - 22)                                                  # 最后一颗：扣上时停在管子半路
    packets, pis, cel = [], [], []
    REST, PRE, OUT = 0.6, 0.0, 4.2
    cg = 1.0
    for f in range(nf):
        ff = min(f, c)
        packets.append([(ff - d) / T_TUBE for d in deps if d < ff < d + T_TUBE])
        if f >= c:
            pis.append(lerp(pis[c - 1], 0.0, ease_out(clamp((f - c) / 14.0))))
            cel.append(cel[c - 1])
            continue
        p = REST
        bump = 0.0
        for a in arrivals:
            if a - 6 <= f < a:
                p = lerp(REST, PRE, smooth((f - (a - 6)) / 6))
            if a <= f < a + 16:
                p = lerp(PRE, OUT, smoother((f - a) / 16))
                bump = 0.07 * smoother((f - a) / 16)
            elif a + 16 <= f < a + 40:
                p = lerp(OUT, REST, smoother((f - a - 16) / 24))
                bump = 0.07 * (1 - smoother((f - a - 16) / 24))
        n_push = sum(1 for a in arrivals if a <= f)
        cg = 1.12 + 0.20 * (1 - math.exp(-n_push / 6.0))
        pis.append(p)
        cel.append(min(1.45, cg + bump))
    return packets, pis, cel, dict(departures=deps, arrivals=arrivals)


# ================================================================ 搭场景
def build(seg, samples=16):
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    import kit_parts as KP
    import kit_socket as S_
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    s = beat_sheet()
    NF = K["len_f"]
    sc = SD.open_board(BOARD, NF, samples)
    board = bpy.data.objects["board"]
    zb = board.location.z
    cell, old_part = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p19_cdk20"))
    cx, cy = cell.matrix_world.translation.x, cell.matrix_world.translation.y
    print("DRILL cell", cell.name, round(cx / MM, 1), round(cy / MM, 1), "zb", round(zb / MM, 1), flush=True)
    SD.hide_tree(old_part)
    for g in KP.gates_of(cell):
        SD.hide_tree(g)
    for o in [o for o in board.children if o.name.startswith("foot") and (o.matrix_world.translation.xy - Vector((cx, cy))).length < 0.05]:
        bpy.data.objects.remove(o)

    # ---- 主料杆上的站牌：按 x 排序，第 3 块 Improve、第 4 块 Cells（kit_parts.STATIONS）
    st_root = bpy.data.objects.get("stations")
    plates = []
    for o in (st_root.children_recursive if st_root else []):
        if o.type != "MESH":
            continue
        dims = [o.dimensions.x / MM, o.dimensions.y / MM]
        if 20.0 < dims[0] < 26.0 and 5.0 < dims[1] < 9.0:
            plates.append(o)
    def top(o):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return Vector((sum(p.x for p in bb) / 8, sum(p.y for p in bb) / 8, max(p.z for p in bb)))
    plates.sort(key=lambda o: top(o).x)                                  # 站牌的原点都在零件根上，按包围盒中心排
    assert len(plates) == 7, ("站牌数", len(plates), [o.name for o in plates])
    imp, cells_p = plates[2], plates[3]
    texts = [o for o in st_root.children_recursive if o.type in ("FONT", "MESH") and o not in plates]
    imp_txt = min(texts, key=lambda o: (top(o).xy - top(imp).xy).length)
    P_imp, P_cells = top(imp), top(cells_p)
    print("DRILL stations", [round(top(o).x / MM, 1) for o in plates], "Improve", [round(v / MM, 1) for v in P_imp], "Cells", [round(v / MM, 1) for v in P_cells],
          "text", imp_txt.name, getattr(imp_txt.data, "body", "-"), flush=True)

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
    for ch in rig["flow"].children:
        SD.hide_tree(ch)
    lit = bpy.data.materials["kit_clear_yellow_lit"]
    lamp_m = lit.copy(); lamp_m.name = "drill_lamp_lit"
    for o in sock.children_recursive:
        if o.type == "MESH" and o.get("lamp") == "on":
            o.data.materials.clear(); o.data.materials.append(lamp_m)

    # ---- 插座：浮在 CDK20 那一格上方（和 5-04 同一个位姿），极慢地漂；插到底、扣上时被顶一下
    q_up = SD.basis_quat(FACE, up=(0, 0, 1))
    q_lie = SD.basis_quat((0, 0, 1), up=(0, 1, 0))
    bc = Vector(BC) * MM * S
    C0 = Vector((cx, cy, zb))
    C1 = Vector((cx, cy + 4 * MM, zb + H_FLOAT * MM))

    def recoil(f):
        return settle(f, t.p48[1], -0.3, n=1.2, dur=12) + settle(f, t.clamp[1], -0.18, n=1.5, dur=10)

    mats = []
    for f in range(NF):
        q = q_up @ Quaternion((0, 0, 1), math.radians(0.35 * math.sin(2 * math.pi * f / 210.0)))
        R = q.to_matrix().to_4x4()
        c = C1 + Vector((0, 0, 0.25 * MM * math.sin(2 * math.pi * f / 160.0)))
        loc = c - (R.to_3x3() @ bc) + (R.to_3x3() @ Vector((recoil(f) * MM * S, 0, 0)))
        mats.append(Matrix.Translation(loc) @ R)
    M_float = Matrix.Translation(C1 - (q_up.to_matrix() @ bc)) @ q_up.to_matrix().to_4x4()

    def to_world(f, p_local_mm):
        return mats[f] @ (Vector(p_local_mm) * MM * S)

    # ---- 断掉的浇口留在格子里（3-04 拔下来时断的）
    sock.matrix_world = (Matrix.Translation(C0 - (q_lie.to_matrix() @ bc)) @ q_lie.to_matrix().to_4x4()) @ Matrix.Diagonal((S, S, S, 1))
    bpy.context.view_layer.update()
    shell = [o for o in sock.children_recursive if o.type == "MESH" and "shell" in o.name and not o.hide_render]
    gates = SD.make_gates(cell, shell, [((-KP.CX, 4.0, 0), (1, 0, 0)), ((KP.CX, -4.0, 0), (-1, 0, 0)), ((0, -KP.CY, 0), (0, 1, 0))],
                          Kt.cat("blue"), cell.name + "_sock")
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    SD.break_gates(gates, -30, -20, scar)
    for f in range(NF):
        loc, q, _ = mats[f].decompose()
        SD.key_xform(sock, f, loc=loc, quat=q, scale=(S, S, S))

    # ---- 机构：盖、灯、光包、活塞、细胞
    packets_f, pis_f, cel_f, msched = machine(t, NF, s)
    pipe = [Vector(p) for p in json.loads(sock["pipe_path_mm"])]
    NP = max(1, max(len(p) for p in packets_f))
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
    lamp_em = [n for n in lamp_m.node_tree.nodes if n.type == "EMISSION"]
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
        for n in lamp_em:
            n.inputs["Strength"].default_value = 4.0 * L
            n.inputs["Strength"].keyframe_insert("default_value", frame=f)
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

    # ---- Improve 站亮红：站牌和字各一份材质，底色从白渐到红、自发光（深红，AgX 下不冲白）
    def redden(o, name):
        """物体级材质（站牌的网格可能和别的站牌共用，不能改网格上的材质）。"""
        if not o.material_slots or not o.material_slots[0].material:
            return None
        m = o.material_slots[0].material.copy(); m.name = name
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = m
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        return m, bsdf
    red_plate = redden(imp, "drill_improve_plate")
    i0, i1, i2 = t.improve
    if red_plate and red_plate[1]:
        bsdf = red_plate[1]
        c0 = tuple(bsdf.inputs["Base Color"].default_value)
        for f in range(max(0, i0 - 1), NF):
            u = ramp(f, i0, i1, ease_out)
            bsdf.inputs["Base Color"].default_value = tuple(lerp(c0[k], (0.85, 0.035, 0.02, 1)[k], u) for k in range(4))
            bsdf.inputs["Base Color"].keyframe_insert("default_value", frame=f)
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1)
            bsdf.inputs["Emission Strength"].default_value = 0.55 * u + 0.25 * max(0.0, settle(f, i1, 1.0, n=1.0, dur=14))
            bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
            if f == max(0, i0 - 1):
                bsdf.inputs["Emission Color"].keyframe_insert("default_value", frame=f)

    # ---- 两个插头：ATP（真插头）被顶出、048 插到底、拧 90°、卡扣扣上
    SEATW = S_.SEAT_W
    axis_q = Quaternion()

    def atp_state(f):
        s0, s1, s2 = t.swap
        if f < s0 - 2:
            return Vector((SEATW, 0, 0)), axis_q
        if f < s0:
            return Vector((SEATW + 0.15 * math.sin(math.pi * (f - s0 + 2) / 2), 0, 0)), axis_q
        if f < s1:
            u = (f - s0) / (s1 - s0)
            return Vector((SEATW + 22.0 * ease_out(u, 2.4), 0, 0)), axis_q
        P0 = Vector((SEATW + 22.0, 0, 0))
        u = ramp(f, s1, s2, lambda x: 1 - (1 - x) ** 4)
        p = P0.lerp(Vector(H_ATP), u) + Vector((0, -3.0 * math.sin(math.pi * u), 9.0 * math.sin(math.pi * u)))
        tumble = 22 * math.sin(math.pi * u) * (1 - u)
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * (f - s2) / 140.0))) * ramp(f, s2, s2 + 30)
        return p + bob, Quaternion((0, 1, 0), math.radians(tumble))

    def p48_state(f):
        """返回 (局部 mm, 局部四元数, 拧角)。"""
        bob = Vector((0, 0, 0.5 * math.sin(2 * math.pi * f / 150.0)))
        i0_, i1_, i2_ = t.p48
        APP = Vector((SEATW + 20.0, 0, 0))
        sw0 = t.swap[1] + 6                                              # ATP 离开轴线以后才摆过来
        mid = i0_
        if f < sw0:
            return Vector(H48) + bob, Quaternion(), 0.0
        if f < mid:
            u = smoother((f - sw0) / (mid - sw0))
            hv = Vector(H48) + bob
            return hv.lerp(APP, u) + Vector((5.0 * math.sin(math.pi * u), 0, 2.0 * math.sin(math.pi * u))), Quaternion((0, 0, 1), math.radians(-8 * math.sin(math.pi * u))), 0.0
        if f < i1_:
            u = (f - mid) / (i1_ - mid)
            return Vector((SEATW + 20.0 * (1 - ease_out(u, 2.2)), 0, 0)), Quaternion(), 0.0
        d = max(0.0, settle(f, i1_, 0.1, n=1.0, dur=i2_ - i1_)) if f < i2_ + 2 else 0.0
        w0_, w1_, w2_ = t.twist
        tw = 0.0
        if f >= w0_:
            tw = 90.0 * smoother((f - w0_) / (w1_ - w0_)) if f <= w1_ else 90.0 - abs(settle(f, w1_, 1.2, n=1.5, dur=w2_ - w1_))
        return Vector((SEATW + d, 0, 0)), Quaternion(), tw

    r48 = S_.rig(p48)
    p48_track = []
    for f in range(NF):
        pa, qa = atp_state(f)
        SD.key_xform(atp, f, loc=pa * MM, quat=qa)
        pl, ql, tw = p48_state(f)
        SD.key_xform(p48, f, loc=pl * MM, quat=ql)
        S_.pose(p48, "twist", tw)
        r48["twist"].keyframe_insert("rotation_euler", frame=f)
        tab = S_.lug_tab_angle(tw)
        if f >= t.clamp[1]:
            tab = -25.0 + abs(settle(f, t.clamp[1], 1.2, n=1.5, dur=t.clamp[2] - t.clamp[1]))
        S_.pose(sock, "tab", tab)
        rig["tab"].keyframe_insert("rotation_euler", frame=f)
        p48_track.append(tuple(pl))

    # ---- 镜头
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = 36.0
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0
    ax, ay, az_, ar = ALIGN
    run_dir = (P_cells - P_imp).normalized()
    keys = [
        dict(f=0, space="sock", tgt=(15.0, 8.0, -1.0), az=32, el=27, dist=124, lens=45),                 # 孔口、ATP 插着、048 在右前方
        dict(f=t.swap[2] - 6, space="sock", tgt=(13.5, 5.0, -0.5), az=26, el=24, dist=108, lens=48),     # 048 摆过来时往孔口靠
        dict(f=t.p48[1], space="sock", tgt=(12.0, 3.0, 0.0), az=20, el=22, dist=99, lens=50),            # 第 2 拍插到底
        dict(f=t.drill[1], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=36, lens=50),            # 第 3 拍钻到触点块
        dict(f=t.drill[2], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=33, lens=50, ease="linear"),
        dict(f=t.cam_hold[0], space="sock", tgt=(ax, ay, az_), az=-40, el=84, dist=31, lens=50, ease="linear"),
        dict(f=t.drill_out[1], space="sock", tgt=(12.0, 3.0, 0.0), az=22, el=23, dist=100, lens=50),     # 第 11 拍退到侧面看拧
        dict(f=t.clamp[1], space="sock", tgt=(9.0, 3.0, -1.5), az=10, el=30, dist=106, lens=48),          # 第 12 拍扣上：孔口、卡扣、盖上的灯一起进画
        dict(f=t.pull[0], space="sock", tgt=(4.0, 3.0, -3.0), az=-6, el=38, dist=118, lens=45),           # 停住的机器（细胞不长了）
        dict(f=t.pull[1], space="world", tgt=tuple(P_imp + Vector((0, 0, 1.0 * MM))), az=-8, el=48, dist=0.088, lens=50),   # 第 14 拍 Improve 亮红（牌占画面宽约 40%）
        dict(f=t.pull[1] + 14, space="world", tgt=tuple(P_imp + Vector((3.0 * MM, 0, 1.0 * MM))), az=-10, el=46, dist=0.086, lens=50),
        dict(f=NF - 1, space="world", tgt=tuple(P_cells + Vector((0, 0, 1.0 * MM))), az=-22, el=34, dist=0.100, lens=48, ease="out"),   # 沿料杆到 Cells 站
    ]
    rigc = SD.CamRig(keys, lambda f: mats[f], MM * S)
    for fs_, amp in ((t.p48[1], 0.20), (t.clamp[1], 0.18), (t.improve[1], 0.10)):
        rigc.shake(fs_, amp, 6)

    def drift(f, eye, tgt):
        d = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        k = 1.0 - 0.85 * (ramp(f, t.drill[0], t.drill[1]) * (1 - ramp(f, t.cam_hold[1], t.drill_out[1])))
        k *= 1.0 - ramp(f, t.pull[0], t.pull[0] + 10)                   # 后拉、沿杆走的时候不加漂移（本身在动）
        off = (right * 0.010 * math.sin(f / 97.0) + up * 0.007 * math.cos(f / 131.0)) * d * k
        return off, off * 0.6
    recs = rigc.bake(cam, NF, drift=drift)

    # ---- 灯光：大板主光（以插座和 Improve 站中间为中心）+ 舱内补光（挂在插座上）
    mid_xy = (C1 + P_imp) / 2
    KP.lights(mid_xy.x, mid_xy.y, 1.0)
    fill = bpy.data.lights.new("drill_fill", "AREA")
    fill.shape = "RECTANGLE"; fill.size, fill.size_y = 60 * MM * S, 40 * MM * S
    fill.color = (1, .98, .95)
    fill.energy = 0.55 * S * S + 0.06
    fo = bpy.data.objects.new("drill_fill", fill)
    sc.collection.objects.link(fo)
    fo.parent = sock
    tgt_l = Vector((-9, 0, -8))
    el = math.radians(32)
    fo.location = (tgt_l + Vector((math.cos(el), 0, math.sin(el))) * 120) * MM
    fo.rotation_euler = (tgt_l - Vector(fo.location) / MM).to_track_quat("-Z", "Y").to_euler()
    fo.scale = (1 / S, 1 / S, 1 / S)
    sf = bpy.data.lights.new("drill_station_fill", "AREA")              # 站牌上一块柔光（后拉以后的主体）
    sf.shape = "RECTANGLE"; sf.size, sf.size_y = 0.14, 0.06
    sf.color = (1, .97, .93)
    sf.energy = 1.6
    sfo = bpy.data.objects.new("drill_station_fill", sf)
    sc.collection.objects.link(sfo)
    sfo.location = P_imp.lerp(P_cells, 0.5) + Vector((-0.02, -0.12, 0.13))
    sfo.rotation_euler = (P_imp.lerp(P_cells, 0.5) - sfo.location).to_track_quat("-Z", "Y").to_euler()

    # ---- 焦点和光圈
    mouth_w = lambda f: to_world(f, (12.0, 0, 0))  # noqa: E731
    al_w = lambda f: to_world(f, (ax, ay, az_))  # noqa: E731
    cab_w = lambda f: to_world(f, (4.0, 2.0, -3.0))  # noqa: E731
    fpts = []
    for f in range(NF):
        p = mouth_w(f)
        w = ramp(f, t.drill[0], t.drill[1] - 6) * (1 - ramp(f, t.cam_hold[1], t.drill_out[1]))
        p = p.lerp(al_w(f), w)
        w2 = ramp(f, t.clamp[1] + 4, t.pull[0])
        p = p.lerp(cab_w(f), w2)
        w3 = ramp(f, t.pull[0] + 6, t.pull[1] - 4)
        st = P_imp.lerp(P_cells, ramp(f, t.pull[1], NF - 1, smooth) * 0.85)
        p = p.lerp(st, w3)
        fpts.append(p)
    phases = [(0, FSTOP["front"]), (t.drill[0] + 14, FSTOP["drill"]), (t.cam_hold[1] + 6, FSTOP["front"]), (t.clamp[1] + 6, FSTOP["cabin"]),
              (t.pull[0] + 20, FSTOP["board"])]
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    fst, focus_d = [], []
    for f in range(NF):
        v = phases[0][1]
        for (fa, va), (fb_, vb) in zip(phases, phases[1:] + [(10 ** 6, phases[-1][1])]):
            if fa <= f:
                span = 20
                v = va if f < fb_ - span // 2 else lerp(va, vb, smooth((f - fb_ + span // 2) / span))
        fst.append(v)
        d.aperture_fstop = v
        d.keyframe_insert("aperture_fstop", frame=f)
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.focus_distance = max(0.003, (fpts[f] - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        focus_d.append(d.focus_distance)

    SD.linear_all([sock, atp, p48, cam] + list(sock.children_recursive) + list(atp.children_recursive) + list(p48.children_recursive)
                  + [o for o in bpy.data.objects if o.type == "LIGHT"])
    for m in [lamp_m] + ([red_plate[0]] if red_plate else []):
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for fc in D5.SD_fcurves(m.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- cam.json：每帧镜头、对位圈在画面上的圆、插座和站牌投影
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
                                   improve=list(SD.project(recs[f], P_imp) or [0, 0, 0]),
                                   cells=list(SD.project(recs[f], P_cells) or [0, 0, 0]),
                                   lid=lid_angle(t, f), lamp=lamp_level(t, f)))
    camj["machine"] = msched
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    coc = []
    for f in list(range(0, NF, 24)) + [NF - 1]:
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        Sd = focus_d[f]
        coc.append(dict(f=f, fstop=round(fst[f], 1), focus_mm=round(Sd / MM, 1),
                        coc_pm8=round(max(SD.coc_px(lens, fst[f], Sd, Sd + 8 * MM * S), SD.coc_px(lens, fst[f], Sd, Sd - 8 * MM * S)), 2)))
    chk = dict(coc=coc, machine=msched, stations=dict(improve=[round(v / MM, 1) for v in P_imp], cells=[round(v / MM, 1) for v in P_cells],
                                                       run_dir=[round(v, 3) for v in run_dir]),
               gates=[dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in gates],
               keys=K["events"])
    (W / "build_check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    _ = M_float
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


# ================================================================ 穿模检查的分组
def clip_plan(sc):
    import bpy
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, p48, atp = R["socket"], R["048"], R["atp"]
    s_m = D5._meshes_under(sock, skip=[p48, atp])
    a_m, k_m = D5._solid(atp), D5._solid(p48)
    frames = set(range(0, NF, 2)) | set(range(0, t.p48[2] + 6)) | set(range(t.twist[0], min(NF, t.clamp[2] + 6)))

    def groups(f):
        return [("plug_vs_socket", a_m + k_m, s_m, sock), ("atp_vs_048", a_m, k_m, sock)]

    return dict(frames=sorted(frames), groups=groups, cam_near=lambda f: s_m, ref=sock)


# ================================================================ 真实层（drill_504.build_real，换配体 048 + 配体转进口袋）
def lig_motion(t, f, d, q):
    """墨线的 048 从口袋外（沿口袋往外最空的方向 7 Å、绕这个方向转 -70°）转进对接姿态：第 lig 落点落定，带一点过冲；之后极轻地呼吸。
    转动先完成（到 75% 路程时转完），平移后完成 —— 转的时候人还在口袋外面。"""
    from mathutils import Quaternion
    a, l_, e = t.lig
    u = clamp((f - a) / max(1, l_ - a))
    ur = smoother(clamp(u / 0.75))
    ut = smoother(u)
    off = 7.0 * (1 - ut) + max(0.0, settle(f, l_, 0.5, n=1.0, dur=e - l_)) if f >= l_ else 7.0 * (1 - ut)
    ang = -70.0 * (1 - ur) + (settle(f, l_, 4.0, n=1.0, dur=e - l_) if f >= l_ else 0.0)
    ang += 1.2 * math.sin(2 * math.pi * (f - l_) / 90.0) * ramp(f, l_ + 10, l_ + 40)
    return tuple(d * off), Quaternion(d, math.radians(ang))


def real_pull(t, f):
    a = smoother(clamp((f - t.real_in[0]) / max(40.0, t.real_out[0] - t.real_in[0])))
    b = smooth((f - (t.real_out[0] - 6)) / 26.0)
    return clamp(a - b)


def build_real(seg, mode="render", *frames):
    return D5.build_real(seg, mode, *frames, ligand=LIGAND, Tcls=T, lig_motion=lig_motion, pull=real_pull)


# ================================================================ 合成
def src_alpha(t, f):
    return ramp(f, 6, 24) * (1 - ramp(f, t.pull[0], t.pull[0] + 10))   # 后拉到大板时出处行收掉（大板段不是我们示意的机构）


def comp_frames(seg, flist=None):
    return D5.comp_frames(seg, flist, Tcls=T, src_real=SRC_REAL, note="048", src_alpha=src_alpha,
                          note_at=lambda t: (t.note[0], t.note[1]), pulses=lambda t: t.pushes)


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


# ================================================================ 声音：歌（卡点表的选段、音量包络、低通）+ 塑料声
def _interp_beats(pts, b):
    if b <= pts[0][0]:
        return pts[0][1]
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        if b0 <= b <= b1:
            u = smooth((b - b0) / max(1e-9, b1 - b0))
            return v0 + (v1 - v0) * u
    return pts[-1][1]


def song_track(sr=48000):
    """卡点表的选段：第 0 拍 = 歌里 song_t_at_beat 秒；增益 × 包络（smoothstep 段间）× 随时间变的低通（对数频率上平滑扫）。"""
    import subprocess
    import numpy as np
    s = beat_sheet()
    mx = s["w4"]["mix"]
    K = make_keys()
    n = int(round(K["len_f"] / SD.FPS * sr))
    t0 = s["w4"]["song_t_at_beat"][1]
    pre = mx.get("pre_roll_s", 0.0)
    src = HERE.parent / "音乐" / "原曲" / s["file"]
    r = subprocess.run([SD.FF_NV, "-v", "error", "-ss", f"{t0 - pre:.4f}", "-t", f"{n / sr + pre + 0.2:.4f}", "-i", str(src), "-ac", "2", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    y = np.frombuffer(r.stdout, np.float32).astype(np.float64).reshape(-1, 2)
    i_pre = int(round(pre * sr))
    y = y[i_pre:i_pre + n]
    if len(y) < n:
        y = np.vstack([y, np.zeros((n - len(y), 2))])
    beat = s["beat_s"]
    tb = np.arange(n) / sr / beat                                       # 每个采样在第几拍
    env = np.array([_interp_beats(mx["env_beats"], b) for b in tb[::64]])
    env = np.interp(np.arange(n), np.arange(0, n, 64)[:len(env)], env)
    lpb = [[p[0], math.log(p[1])] for p in mx["lowpass_beats"]]
    lp = np.array([math.exp(_interp_beats(lpb, b)) for b in tb[::64]])
    fc = np.interp(np.arange(n), np.arange(0, n, 64)[:len(lp)], lp)
    out = y * mx["gain"]
    k0 = int(np.argmax(fc < 17000)) if (fc < 17000).any() else n
    if k0 < n:                                                          # 两级一阶低通，只在开始扫频以后逐采样算
        a = 1.0 - np.exp(-2 * np.pi * fc / sr)
        z1 = out[k0 - 1].copy() if k0 > 0 else np.zeros(2)
        z2 = z1.copy()
        seg_ = out[k0:].copy()
        for i in range(len(seg_)):
            ai = a[k0 + i]
            z1 += ai * (seg_[i] - z1)
            z2 += ai * (z1 - z2)
            seg_[i] = z2
        out[k0:] = seg_
    return out * env[:, None], dict(t0=t0, gain=mx["gain"], env_end=float(env[-1]), fc_end=float(fc[-1]))


def audio(seg):
    import wave
    import numpy as np
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    sr = 48000
    mix, info = song_track(sr)
    n = len(mix)
    C = SD.click
    X = dict(snap=lambda sd, g: C([(3100, 1.0), (5200, 0.5)], 9, 3, g, sd), clack=lambda sd, g: C([(900, 1.0), (1900, 0.6), (3300, 0.3)], 22, 5, g, sd),
             thunk=lambda sd, g: C([(260, 1.0), (520, 0.5), (1400, 0.25)], 40, 6, g, sd), tick=lambda sd, g: C([(2400, 1.0), (4100, 0.4)], 6, 2, g, sd))
    G = 0.8                                                             # 给歌让位
    hits = [(t.swap[0] + 2, X["clack"](1, 0.10 * G), 0.42), (t.p48[1], X["clack"](2, 0.22 * G), 0.5),
            (t.drill[0], SD.whoosh((t.drill[1] - t.drill[0]) / SD.FPS, 0.10 * G, 3, f0=400, f1=2600), 0.5),
            (t.real_out[0], SD.whoosh(24 / SD.FPS, 0.06 * G, 4, f0=2600, f1=500), 0.5)]
    w0, w1, _ = t.twist
    for k in range(3):
        f = int(w0 + (w1 - w0) * (k + 1) / 4)
        hits.append((f, X["tick"](10 + k, 0.09 * G), 0.55))
    hits += [(t.clamp[1] - 1, X["snap"](20, 0.26 * G), 0.55), (t.off[1], X["thunk"](21, 0.16 * G), 0.5),
             (t.pull[0], SD.whoosh((t.pull[1] - t.pull[0] + 8) / SD.FPS, 0.14 * G, 22, f0=300, f1=2200), 0.5),
             (t.improve[1], X["tick"](23, 0.08 * G), 0.4)]
    for f, y, pan in hits:
        i = int(round(f / SD.FPS * sr))
        j = min(n, i + len(y))
        if i >= n or j <= i:
            continue
        mix[i:j, 0] += y[:j - i] * (1 - pan) * 0.9
        mix[i:j, 1] += y[:j - i] * pan * 0.9
    mix = np.tanh(mix / 0.9) * 0.9 if np.abs(mix).max() > 0.85 else mix  # 软限幅，不整体拉低
    with wave.open(str(W / "mix.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    (W / "audio_hits.json").write_text(json.dumps(dict(song=info, hits=[[h[0], round(h[2], 2)] for h in hits]), ensure_ascii=False), encoding="utf-8")
    print("DRILL audio", W / "mix.wav", round(n / sr, 3), "s", info, flush=True)


# ================================================================ 自检
def beat_check(seg):
    """T7 事件落拍（帧 = 拍网格）；T7b 成片音轨里歌的军鼓/镲片（6–11 kHz）起音离画面拍点（同 check_w0w1 的量法）。"""
    import subprocess
    import numpy as np
    s = beat_sheet()
    K = make_keys()
    B = s["w4"]["beats"]
    beat_f = SD.FPS * s["beat_s"]
    rows = []
    for e in K["events"]:
        exact = beat_f * e["beat"]
        rows.append(dict(id=e["id"], beat=e["beat"], f_land=e["f_land"], beat_frame=round(exact, 2), song_s=round(s["w4"]["song_t_at_beat"][1] + e["beat"] * s["beat_s"], 3)))
    grid_ok = all(abs(2 * b - round(2 * b)) < 1e-6 or abs(4 * b - round(4 * b)) < 1e-6 for b in B.values())
    SR = 44100

    def hf_env(x):                                                      # 6–11 kHz（军鼓、镲片），3 ms 包络
        X = np.fft.rfft(x)
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        y = np.abs(np.fft.irfft(X * ((fr >= 6000) & (fr < 11000)), len(x)))
        k = int(0.003 * SR)
        return np.convolve(y, np.ones(k) / k, "same")

    def onset_ms(env, t_):                                              # 从底噪升到 30% 峰值的那一刻，相对 t_（毫秒）
        i0, i1 = int((t_ - 0.06) * SR), int((t_ + 0.08) * SR)
        seg_ = env[i0:i1]
        pk = int(np.argmax(seg_))
        base = float(np.median(env[int((t_ - 0.15) * SR):int((t_ - 0.07) * SR)]))
        thr = base + 0.3 * (seg_[pk] - base)
        j = int(np.argmax(seg_[:pk + 1] > thr))
        return round(((i0 + j) / SR - t_) * 1000, 1)

    r = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    env = hf_env(np.frombuffer(r.stdout, np.float32).astype(np.float64))
    # 原曲同一段（不加包络、不低通）：歌自己在拍网格上的起音。歌本身有提前的装饰音、breakdown 里没有军鼓，
    # 这些偏差在原曲里就有，不是"歌放错了位置"；T7b 量的是成片里的起音 − 原曲里同一拍的起音（11-21 改，W1 的量法只比网格）
    t_song0 = s["w4"]["song_t_at_beat"][1]
    src = HERE.parent / "音乐" / "原曲" / s["file"]
    pad = 1.0
    r2 = subprocess.run([SD.FF_NV, "-v", "error", "-ss", f"{t_song0 - pad:.4f}", "-t", f"{len(env) / SR + 2 * pad:.4f}", "-i", str(src), "-ac", "1", "-ar", str(SR),
                         "-f", "f32le", "-"], capture_output=True, check=True)
    env_raw = hf_env(np.frombuffer(r2.stdout, np.float32).astype(np.float64))
    hits = json.loads((SD.work(seg) / "audio_hits.json").read_text(encoding="utf-8"))["hits"]
    sfx_t = [h[0] / SD.FPS for h in hits]
    per = []
    for b in range(1, s["w4"]["nbeats"] - 2):
        if b % 4 == 2:                                                  # 网格位置 2 那一拍有提前的装饰音，跳过（见卡点表 grid_fix_note）
            continue
        t_ = round(beat_f * b) / SD.FPS
        if any(abs(t_ - x_) < 0.06 for x_ in sfx_t):
            continue
        tb = b * s["beat_s"]
        fin, raw = onset_ms(env, t_), onset_ms(env_raw, pad + tb)
        per.append(dict(beat=b, final_vs_frame_ms=fin, song_vs_grid_ms=raw, err_ms=round(fin + (t_ - tb) * 1000 - raw, 1)))
    oa = np.array([x["err_ms"] for x in per]) if per else np.zeros(1)
    t7b = dict(n=len(per), median_ms=round(float(np.median(oa)), 1), p90_abs_ms=round(float(np.percentile(np.abs(oa), 90)), 1), per_beat=per,
               how="成片音轨 6–11 kHz 起音 − 原曲同一拍的起音（扣掉画面帧取整的差）；≤ 17 ms = 一帧以内")
    t7b["ok"] = t7b["n"] >= 6 and abs(t7b["median_ms"]) <= 17 and t7b["p90_abs_ms"] <= 25
    return dict(rows=rows, grid_ok=grid_ok, t7b=t7b)


def check(seg):
    K, EV = SD.load_keys(seg)
    t = T(EV)
    res = D5.check(seg, out_mp4=OUT_MP4, luma_until=t.pull[0], sync=False)
    bc = beat_check(seg)
    res["beat_check"] = bc
    (SD.work(seg) / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL beat", json.dumps(dict(grid_ok=bc["grid_ok"], t7b={k: v for k, v in bc["t7b"].items() if k not in ("per_beat", "how")}), ensure_ascii=False), flush=True)
    return res


def sheet(seg, step="6"):
    return D5.sheet(seg, step, out_mp4=OUT_MP4, prefix="16_钻取_W4")


def report(seg=None):
    return D5.report(seg)
