"""HKBU SCIE1007 课程作业的科普视频：音乐段 W2（25 秒 = 1500 帧，Harder, Better, Faster, Stronger）按新模板三维重做（设计：深化/20_W2W3新模板重做.md 第二、三、六、七节，11-24）。

没有念词：时间基准是歌的拍子，帧号全由卡点表 音乐/卡点/W2_HBFS.json 算（make_keys），帧 = round(60 × (grid_fix + 拍长 × 拍号))。
一镜到底，都在亮面拼装大板上：
  第 0–4 拍   磨砂 CDK20（p29）躺在 z3_c5_r0；焦点点名到 AlphaFold 芯片（z4_c6_r2），芯片浇口预颤，一个骨白鼓包沿料杆走到磨砂件的浇口，
              被"吃"进去：磨砂壳起波纹、换成暖灰熔料（6 帧交叉）、压扁到 0.85。
  第 4–28 拍  液团跳起（浇口断，留骨白疤），每拍换一个"猜测"形状（种子 40+k，和旧版同种），半拍抽动；挤、拧、翻落在第 6、8、10 拍；
              第 12 拍起慢慢变蓝、往左飘到 CDK20 的家上方；第 21/23/25/27 拍幅度 0.6/0.4/0.2/0.05；第 28 拍和 h01b 插座外壳重合，同一帧换成插座。
  第 29–39¼ 拍 红尾巴（AlphaFold 303–346 号残基的走向，推到壳外）冒出来、半拍一跳；第 32 拍化成液体；第 33 拍蓄力；第 34 拍起每个八分音符甩一下，
              尾巴按弹簧链滞后；第 39¼ 拍根部放开，尖头在前沿弧线飞，穿过 z3_c5_r0 的空框落到台面上。
  第 40–44 拍 尾巴摊开、第 41–42 拍收成一圈红线（阿基米德螺线 2.5 圈）；插座从浮着转成躺平、落回 z3_c4_r0，第 44 拍碰上三根浇口（T7）。
  第 48 拍起  镜头升到插座正上方，沿孔轴钻进插孔，帧 1483 起骨白内壁盖满（接 4-01 的 socket_bore 擦除层）。
液团和尾巴的形状逐帧在 build 里用 numpy 算好写成 PC2（G:/cdk20/work/drill/W2/blob.pc2、tail.pc2），Blender 只回放（Mesh Cache 修改器）。
押韵字幕和出处行不在这里：Remotion 合成 W2LyricsLayer 出透明 PNG，comp_w23.py 叠。
"""
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_drill as SD  # noqa: E402
import drill_504 as D5  # noqa: E402
from shot_drill import MM, clamp, smooth, smoother, ease_out, ease_in, ramp, lerp, settle  # noqa: E402

SEG = "W2"
BOARD = D5.BOARD
S, BC, H_FLOAT, FACE = D5.S, D5.BC, D5.H_FLOAT, D5.FACE
SHEET = HERE.parent / "音乐" / "卡点" / "W2_HBFS.json"
OUT_DIR = SD.ROOT / "导演检查_20261124"
OUT_MP4 = OUT_DIR / "03_W2_重做.mp4"
AUDIO_SRC = SD.ROOT / "导演检查_20261123" / "24_W2_加工.mp4"
STRUCT = D5.STRUCT
NPZ = D5.SURF
APEX = (-105.0, 118.0, 72.0)                     # 液团跳到的最高点（世界毫米）
LAND = (-99.0, 127.0)                            # 红尾巴落到台面上的点（z3_c5_r0 框里，世界 xy 毫米）
COIL_C = (-99.0, 136.0)                          # 红线圈中心（台面上；见 review：比 20 号文档往后挪，好从框里看见）
GUESS_A = 4.5                                    # 猜测变形幅度（插座单位 mm）
TAIL_R = 1.0                                     # 尾巴管半径（插座单位 → 世界里 ×S）
NODES = 44
SUBR = 3                                         # 每段节点之间再插几圈
RING = 16


# ================================================================ 卡点表 → 事件帧
def beat_sheet():
    s = json.loads(SHEET.read_text(encoding="utf-8"))
    s["beat_s"] = 60.0 / s["bpm"]
    return s


def fb(s, b):
    """第 b 拍 → 段内帧（含底鼓偏移 grid_fix）。"""
    return round(SD.FPS * (s["grid_fix_s"] + s["beat_s"] * b))


def beat_of(s, f):
    return (f / SD.FPS - s["grid_fix_s"]) / s["beat_s"]


def make_keys():
    s = beat_sheet()
    B = s["w2"]["beats"]
    F = lambda k: fb(s, B[k])  # noqa: E731
    nf = s["w2"]["len_f"]
    ev = [
        ("chip_focus", "camera_to", "chip_focus", F("chip_focus") - 8, F("chip_focus"), F("pulse"), "第 0.5 拍：焦点点名到 AlphaFold 芯片（拍前 8 帧到位）"),
        ("pulse", "flow", "pulse", F("pulse"), F("pulse_end"), F("pulse_end") + 6, "第 1–3.2 拍：骨白鼓包从芯片浇口沿料杆走到磨砂 CDK20"),
        ("eat", "grow", "pulse_end", F("pulse_end"), F("squash_end"), F("jump"), "第 3.2–3.8 拍：鼓包被吃进去，磨砂壳起波纹、换熔料、压扁 0.85"),
        ("jump", "eject", "jump", F("jump") - 6, F("jump"), F("squeeze"), "第 4 拍：液团跳起，三根浇口断"),
        ("squeeze", "move", "squeeze", F("squeeze") - 6, F("squeeze"), F("squeeze") + 20, "第 6 拍：squeeze it，竖向挤到 0.72"),
        ("twist", "twist", "twist", F("twist") - 8, F("twist"), F("twist") + 40, "第 8 拍：twist it，上半拧 35°"),
        ("turn", "move", "turn", F("turn") - 8, F("turn"), F("turn") + 20, "第 10 拍：turn it，整团翻 90°"),
        ("slower", "move", "slower", F("slower"), F("slower"), F("slower") + 10, "第 21 拍：Slower，幅度 0.6"),
        ("calmer", "move", "calmer", F("calmer"), F("calmer"), F("calmer") + 10, "第 23 拍：calmer，幅度 0.4、抽动停"),
        ("firmer", "move", "firmer", F("firmer"), F("firmer"), F("firmer") + 10, "第 25 拍：firmer，幅度 0.2、熔化度 0"),
        ("bluer", "move", "bluer", F("blue_start"), F("bluer"), F("bluer") + 10, "第 27 拍：bluer，颜色到克莱因蓝"),
        ("settle", "clamp", "settle", F("float_at"), F("settle"), F("settle") + 14, "第 28 拍：定形，换成 h01b 插座（T7）"),
        ("tail", "appear", "tail", F("tail") - 8, F("tail"), F("liquid"), "第 29 拍：红尾巴冒出来，半拍一跳"),
        ("liquid", "grow", "liquid", F("liquid"), F("liquid") + 18, F("windup"), "第 32 拍：尾巴化成红色液体"),
        ("windup", "twist", "windup", F("windup"), F("shake"), F("shake"), "第 33 拍：插座反拧 −25° 蓄力"),
        ("shake", "twist", "shake", F("shake"), F("shake"), F("fling"), "第 34–39 拍：湿狗甩，每个八分音符甩一下"),
        ("fling", "eject", "fling", F("fling"), F("fling"), F("land"), "第 39¼ 拍：红尾巴甩飞"),
        ("land", "move", "land", F("fling"), F("land"), F("land") + 12, "第 40 拍：落在台面上，12 帧摊开"),
        ("coil", "retract", "coil", F("coil"), F("coil_end"), F("coil_end"), "第 41–42 拍：收成一圈红线"),
        ("seat", "plug_in", "seat", F("land"), F("seat"), F("seat") + 14, "第 40–44 拍：插座转成躺平、落回格子，碰上浇口（T7）"),
        ("rise", "camera_to", "rise", F("rise") - 40, F("rise") + 10, F("bore_full"), "第 48 拍：镜头升到插座正上方，沿孔轴钻进插孔"),
        ("bore_full", "camera_to", "bore_full", F("rise") + 10, F("bore_full"), nf - 1, "第 50.7 拍：孔桶骨白内壁盖满画面"),
    ]
    events = [dict(id=i, verb=v, beat=B[bk], f_start=a, f_land=l, f_end=e, means=m) for i, v, bk, a, l, e, m in ev]
    return dict(seg=SEG, len_f=nf, time_base="music", song=s["song"], bpm=s["bpm"], song_t0=s["w2"]["song_t_at_beat"][1], events=events)


class T:
    def __init__(self, EV):
        s = beat_sheet()
        B = s["w2"]["beats"]
        self.s = s
        self.F = {k: fb(s, v) for k, v in B.items()}
        self.nf = s["w2"]["len_f"]

    def __getattr__(self, k):
        F = self.__dict__.get("F", {})
        if k in F:
            return F[k]
        raise AttributeError(k)

    def b(self, f):
        return beat_of(self.s, f)

    def f(self, b):
        return fb(self.s, b)


# ================================================================ 液团的随拍曲线（纯函数，拍号 b）
def guess_amp(b):
    if b < 12:
        return 1.0
    if b < 20:
        return lerp(1.0, 0.7, (b - 12) / 8)
    pts = [(20, 0.7), (21, 0.6), (23, 0.4), (25, 0.2), (27, 0.05), (28, 0.0)]
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        if b < b1:
            # 每个落点拍上 0.3 拍内落到新幅度，之后保持（Slower / calmer / firmer / bluer 落在拍上）
            if b1 == 28:
                return lerp(v0, v1, smoother((b - b0) / (b1 - b0)))
            return v0 if b < b1 - 0.3 else lerp(v0, v1, smoother((b - (b1 - 0.3)) / 0.3))
    return 0.0


def melt_of(b):
    return 1.0 - smoother((b - 20) / 5.0)


def blue_of(b):
    return smoother((b - 12) / 15.0)


def twitch_of(b):
    """每半拍（反拍上）抽一下，幅度 0.25；第 23 拍（calmer）起停。"""
    if b < 4 or b >= 23:
        return 0.0
    ph = (b * 2) % 2.0                                                  # 0–2：0 正拍，1 反拍
    if 1.0 <= ph < 1.35:
        return 0.25 * math.sin(math.pi * (ph - 1.0) / 0.35)
    return 0.0


def guess_mix(b):
    """返回 (上一个猜测号, 下一个猜测号, 过渡权重)；号 −1 = 不变形。每拍换下一个，拍点起 0.6 拍 smootherstep。"""
    if b < 4:
        return -1, -1, 0.0
    g = int(math.floor(b - 4))
    w = smoother(((b - 4) - g) / 0.6)
    return (g - 1) % 8 if g > 0 else -1, g % 8, w


def jump_curve(u):
    """0 → 1 带 8% 过冲：欠阻尼二阶、初速不为 0（起跳是弹出去的）。u = 0–1（两拍）。"""
    if u <= 0:
        return 0.0
    z = 0.62
    wd = math.pi / 0.55
    w = wd / math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * u) * math.cos(wd * u)


def shake_angle(t, f):
    """插座绕竖轴的角（度）：第 33 拍反拧 −25°，第 34 拍起每个八分音符甩到一头 ±32°，第 39 拍以后回正（40.5 拍前停稳）。"""
    b = t.b(f)
    if b < 33:
        return 0.0
    if b < 34:
        return -25.0 * smoother(b - 33)
    keys = [(33.999, -25.0)] + [(34 + 0.5 * k, 32.0 if k % 2 == 0 else -32.0) for k in range(11)]   # 34 … 39
    if b < 39:
        for (b0, v0), (b1, v1) in zip(keys, keys[1:]):
            if b < b1:
                return lerp(v0, v1, smoother((b - b0) / (b1 - b0)))
    u = (b - 39) / 1.5
    if u >= 1:
        return 0.0
    return 32.0 * (1 - smoother(u)) * math.cos(2.2 * math.pi * u * 0.5)


# ================================================================ 工具（numpy）
def write_pc2(path, frames_iter, npts, nsamp):
    with open(path, "wb") as fo:
        fo.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, npts, 0.0, 1.0, nsamp))
        n = 0
        for arr in frames_iter:
            fo.write(arr.astype("<f4").tobytes())
            n += 1
    assert n == nsamp, (n, nsamp)


def taubin(V, E, n=40, lam=0.5, mu=-0.53):
    import numpy as np
    deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)[:, None]
    deg[deg == 0] = 1

    def L(X):
        acc = np.zeros_like(X)
        np.add.at(acc, E[:, 0], X[E[:, 1]])
        np.add.at(acc, E[:, 1], X[E[:, 0]])
        return acc / deg - X
    X = V.copy()
    for _ in range(n):
        X = X + lam * L(X)
        X = X + mu * L(X)
    return X


def catmull(P, sub):
    """节点链 → 加密的中线（端点各延一个虚点）。"""
    import numpy as np
    P = np.asarray(P, float)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(sub):
            u = k / sub
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-1])
    return np.array(out)


def tube_verts(C, rad, vs, hs):
    """中线 C (M,3)、每圈半径 rad (M,)、竖向/横向缩放 vs/hs (M,) → 顶点 (M*RING + 2, 3)。截面竖轴取世界 Z（贴在台面上时摊平）。"""
    import numpy as np
    M = len(C)
    T_ = np.gradient(C, axis=0)
    T_ /= np.maximum(1e-9, np.linalg.norm(T_, axis=1))[:, None]
    Z = np.array([0, 0, 1.0])
    side = np.cross(T_, Z)
    bad = np.linalg.norm(side, axis=1) < 0.15
    side[bad] = np.cross(T_[bad], np.array([1.0, 0, 0]))
    side /= np.linalg.norm(side, axis=1)[:, None]
    up = np.cross(side, T_)
    th = np.linspace(0, 2 * math.pi, RING, endpoint=False)
    ring = (np.cos(th)[None, :, None] * side[:, None, :] * (rad * hs)[:, None, None]
            + np.sin(th)[None, :, None] * up[:, None, :] * (rad * vs)[:, None, None])
    V = C[:, None, :] + ring
    return np.vstack([V.reshape(-1, 3), C[:1], C[-1:]])


def tube_faces(M):
    F = []
    for i in range(M - 1):
        for j in range(RING):
            a, b = i * RING + j, i * RING + (j + 1) % RING
            F.append((a, b, b + RING, a + RING))
    c0, c1 = M * RING, M * RING + 1
    for j in range(RING):
        F.append((c0, (j + 1) % RING, j))
        F.append((c1, (M - 1) * RING + j, (M - 1) * RING + (j + 1) % RING))
    return F


def bezier(P0, P1, P2, P3, n=200):
    import numpy as np
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 3 * P0 + 3 * (1 - u) ** 2 * u * P1 + 3 * (1 - u) * u * u * P2 + u ** 3 * P3


def arclen(P):
    import numpy as np
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def along(P, s_cum, s):
    """折线 P 上弧长 s 处的点（s 可越界：两头沿端点切线外推）。"""
    import numpy as np
    s = np.atleast_1d(s)
    out = np.empty((len(s), 3))
    for k, v in enumerate(s):
        if v <= 0:
            d = P[1] - P[0]
            out[k] = P[0] + d / np.linalg.norm(d) * v
        elif v >= s_cum[-1]:
            d = P[-1] - P[-2]
            out[k] = P[-1] + d / np.linalg.norm(d) * (v - s_cum[-1])
        else:
            i = int(np.searchsorted(s_cum, v) - 1)
            i = max(0, min(len(P) - 2, i))
            u = (v - s_cum[i]) / max(1e-9, s_cum[i + 1] - s_cum[i])
            out[k] = P[i] + (P[i + 1] - P[i]) * u
    return out


# ================================================================ 搭场景
def build(seg, samples=16):
    import bpy
    import numpy as np
    from mathutils import Matrix, Quaternion, Vector
    from mathutils.bvhtree import BVHTree
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
    by_name = lambda n: SD.find_cell(lambda c, p: c.name == n)  # noqa: E731
    home, p19 = by_name("z3_c4_r0")
    ucell, p29 = by_name("z3_c5_r0")
    chip_cell, chip = by_name("z4_c6_r2")
    hx, hy = home.matrix_world.translation.x, home.matrix_world.translation.y
    ux, uy = ucell.matrix_world.translation.x, ucell.matrix_world.translation.y
    print("DRILL cells home", round(hx / MM, 1), round(hy / MM, 1), "unknown", round(ux / MM, 1), round(uy / MM, 1),
          "chip", [round(v / MM, 1) for v in chip_cell.matrix_world.translation], "zb", round(zb / MM, 1), flush=True)
    assert p29.name.startswith("p29_cdk20_unknown") and chip.name.startswith("p13_chip"), (p29.name, chip.name)
    chip_txt = next(o for o in chip.children_recursive if o.type == "FONT")
    assert chip_txt.data.body == "AlphaFold", chip_txt.data.body

    # ---- 藏件：p19（家里换成插座）、销子锁、钥匙、表盘、胶囊（连各自的浇口，格框留着）
    SD.hide_tree(p19)
    for g in KP.gates_of(home):
        SD.hide_tree(g)
    banned = ("p21_lock", "p22_key", "p38_dial", "p08_capsule")
    hidden_banned = []
    for c in [o for o in board.children if o.name.startswith("z") and "_c" in o.name]:
        try:
            p = KP.part_of(c)
        except StopIteration:
            continue
        if p.name.split(".")[0] in banned:
            SD.hide_tree(p)
            for g in KP.gates_of(c):
                SD.hide_tree(g)
            hidden_banned.append(p.name)
    for o in bpy.data.objects:
        if o.name.split(".")[0].startswith(banned):
            o.hide_render = o.hide_viewport = True
    print("DRILL hidden", hidden_banned, flush=True)

    Kt = KP.Kit()
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)

    # ---- 磨砂 CDK20（p29）：原浇口藏掉，按它的外形重打三根（第 4 拍一起断）
    p29_meshes = [o for o in p29.children_recursive if o.type == "MESH"]
    gate_mat = next((g.data.materials[0] for g in KP.gates_of(ucell) if g.type == "MESH" and g.data.materials), Kt.cat("clear"))
    for g in KP.gates_of(ucell):
        SD.hide_tree(g)
    bpy.context.view_layer.update()
    ends = [((-KP.CX, 4.0, 0), (1, 0, 0)), ((KP.CX, -4.0, 0), (-1, 0, 0)), ((0, -KP.CY, 0), (0, 1, 0))]
    ugates = SD.make_gates(ucell, p29_meshes, ends, gate_mat, ucell.name + "_w2")
    print("DRILL p29 gates", [(round(g["tip"].x / MM, 1), round(g["tip"].y / MM, 1)) for g in ugates], flush=True)
    SD.break_gates(ugates, t.squash_end - 6, t.jump, scar)
    dg = bpy.context.evaluated_depsgraph_get()
    e29 = p29_meshes[0].evaluated_get(dg)
    m29 = e29.to_mesh()
    m29.calc_loop_triangles()
    p29_bvh = BVHTree.FromPolygons([tuple(e29.matrix_world @ v.co) for v in m29.vertices], [tuple(tr.vertices) for tr in m29.loop_triangles], all_triangles=True)
    e29.to_mesh_clear()
    p29_bb = [p29_meshes[0].matrix_world @ Vector(c) for c in p29_meshes[0].bound_box]
    P29C = sum(p29_bb, Vector()) / 8
    p29_dims = Vector([max(p[i] for p in p29_bb) - min(p[i] for p in p29_bb) for i in range(3)])

    # ---- 插座（h01b，盖合上、灯照 rest）
    sock = S_.h01b_cdk20_socket(Kt)
    sock["drill_role"] = "socket"
    rig = S_.rig(sock)
    S_.rest(sock)
    print("DRILL baked modifiers", SD.apply_modifiers(sock), flush=True)
    for ch in rig["flow"].children:
        SD.hide_tree(ch)
    for lo_ in [o for o in sock.children_recursive if o.type == "LIGHT" and "lamp" in o.name]:
        lo_.data.energy = 0.03 * S * S
    bpy.context.view_layer.update()
    s_meshes = [o for o in sock.children_recursive if o.type == "MESH" and not o.hide_render]
    # 插座局部（mm）的 BVH：静止位姿、根在原点 1:1 时取
    sv, sf = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in s_meshes:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        me.calc_loop_triangles()
        b0 = len(sv)
        sv += [tuple((e.matrix_world @ v.co) / MM) for v in me.vertices]
        sf += [tuple(b0 + i for i in tr.vertices) for tr in me.loop_triangles]
        e.to_mesh_clear()
    sock_bvh = BVHTree.FromPolygons(sv, sf, all_triangles=True)
    bore_objs = [o for o in s_meshes if ("barrel_" in o.name or "contact_block_" in o.name)]

    # ---- 插座的两个位姿（drill_504 浮着、drill_W4 躺平），浮着的极慢漂；甩；落回格子
    q_up = SD.basis_quat(FACE, up=(0, 0, 1))
    q_lie = SD.basis_quat((0, 0, 1), up=(0, 1, 0))
    bc = Vector(BC) * MM * S
    C0 = Vector((hx, hy, zb))
    C1 = Vector((hx, hy + 4 * MM, zb + H_FLOAT * MM))
    f_rot_done = t.land + int(round(0.64 * (t.seat - t.land)))         # 离板面 14 mm 时转完

    def float_c(f):
        return C1 + Vector((0, 0, 0.25 * MM * math.sin(2 * math.pi * f / 160.0)))

    def sock_state(f):
        """返回插座中心（BC 点，世界）和朝向。"""
        sway = Quaternion((0, 0, 1), math.radians(0.35 * math.sin(2 * math.pi * f / 210.0)))
        th = Quaternion((0, 0, 1), math.radians(shake_angle(t, f)))
        q_f = th @ sway @ q_up
        if f < t.land:
            return float_c(f), q_f
        if f < f_rot_done:
            u = smoother((f - t.land) / (f_rot_done - t.land))
            c = float_c(f).lerp(Vector((hx, hy, zb + 14 * MM)), u)
            return c, q_f.slerp(q_lie, u)
        if f < t.seat:
            u = ease_in((f - f_rot_done) / (t.seat - f_rot_done), 1.8)
            return Vector((hx, hy, zb + 14 * MM * (1 - u))), q_lie
        return Vector((hx, hy, zb + abs(settle(f, t.seat, 0.35 * MM, n=1.5, dur=14)))), q_lie

    smats = []
    s_center = []
    for f in range(NF):
        c, q = sock_state(f)
        R = q.to_matrix().to_4x4()
        smats.append(Matrix.Translation(c - (q.to_matrix() @ bc)) @ R)
        s_center.append(c)

    # ---- 家里的三根浇口：按躺平位姿打（整段都在；第 44 拍插座落上来时尖头正好碰到外壳）
    sock.matrix_world = (Matrix.Translation(C0 - (q_lie.to_matrix() @ bc)) @ q_lie.to_matrix().to_4x4()) @ Matrix.Diagonal((S, S, S, 1))
    bpy.context.view_layer.update()
    shell = [o for o in sock.children_recursive if o.type == "MESH" and "shell" in o.name and not o.hide_render]
    hgates = SD.make_gates(home, shell, ends, Kt.cat("blue"), home.name + "_w2sock")
    print("DRILL home gates", len(hgates), flush=True)
    for g in hgates:                                                     # 落上来时浇口抖一下
        cone = g["cone"]
        for f in range(t.seat - 1, t.seat + 16):
            k = 1.0 + settle(f, t.seat, 0.12, n=2.0, dur=14)
            cone.scale = (k, k, 1.0 - 0.5 * (k - 1.0))
            cone.keyframe_insert("scale", frame=f)
    for f in range(NF):
        loc, q, _ = smats[f].decompose()
        SD.key_xform(sock, f, loc=loc, quat=q, scale=(S, S, S))
    for m in [sock] + list(sock.children_recursive):                    # 只动本来就显示的件（布尔刀具、灭灯件一直藏着）
        if not m.hide_render:
            for f_, h_ in ((0, True), (t.settle - 1, True), (t.settle, False)):
                m.hide_render = m.hide_viewport = h_
                m.keyframe_insert("hide_render", frame=f_)
                m.keyframe_insert("hide_viewport", frame=f_)

    # ================= 液团 w2_blob：静止形状 = 插座外壳（外包络网格，体素重建 0.6 mm），每帧顶点写 PC2
    import bmesh
    outline, cc = S_.shell_outline()
    cw, cu = cc
    lv = [(-20.9, .90), (-20.7, .915), (-20.1, .945), (-19.0, .975), (-17.2, 1.0), (-8.0, 1.0), (0.0, 1.0), (5.0, 1.0), (9.6, 1.0),
          (11.4, .975), (12.4, .945), (12.85, .915), (13.0, .90)]
    bm = bmesh.new()
    rings = []
    for z, k in lv:
        rings.append([bm.verts.new(((cw + k * (p[0] - cw)) * MM, (cu + k * (p[1] - cu)) * MM, z * MM)) for p in outline])
    n_o = len(outline)
    for i in range(len(rings) - 1):
        for j in range(n_o):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % n_o], rings[i + 1][(j + 1) % n_o], rings[i + 1][j]))
    bmesh.ops.contextual_create(bm, geom=rings[0])
    bmesh.ops.contextual_create(bm, geom=rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me0 = bpy.data.meshes.new("w2_blob_src")
    bm.to_mesh(me0)
    bm.free()
    tmp = bpy.data.objects.new("w2_blob_src", me0)
    sc.collection.objects.link(tmp)
    rm = tmp.modifiers.new("vox", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = 0.6 * MM
    rm.adaptivity = 0.0
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me_b = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(tmp)
    me_b.name = "w2_blob"
    NV = len(me_b.vertices)
    V0 = np.zeros(NV * 3)
    me_b.vertices.foreach_get("co", V0)
    N0 = np.zeros(NV * 3)
    me_b.vertices.foreach_get("normal", N0)
    N0 = N0.reshape(-1, 3)
    V0 = V0.reshape(-1, 3) / MM                                          # 插座局部 mm
    # 贴到插座外壳的真表面上（壳加厚的那 1.2 mm、孔口面板），孔口一圈压成凹坑
    rr = np.hypot(V0[:, 1], V0[:, 2])
    snapped = 0
    for i in range(NV):
        if V0[i, 0] > 9.0 and rr[i] < 8.6:
            continue
        n_ = Vector(N0[i])
        hit = sock_bvh.ray_cast(Vector(V0[i]) + n_ * 3.0, -n_, 6.0)       # 从外面往里打：贴最外一层（壳加厚 1.2 mm 那面）
        if hit[0] is not None:
            V0[i] = hit[0][:]
            snapped += 1
    env_bvh = BVHTree.FromPolygons([tuple(v) for v in V0], [tuple(p.vertices) for p in me_b.polygons])   # 外包络（贴到壳外表面以后、压孔口凹坑以前；尾巴推到壳外用）
    mouth = (V0[:, 0] > 9.0) & (rr < 8.6)
    dent = np.clip(1 - (rr / 7.6) ** 4, 0, 1)
    V0[mouth, 0] -= 5.0 * dent[mouth]
    E = np.array([e.vertices[:] for e in me_b.edges])
    me_b.vertices.foreach_set("co", (V0 * MM).ravel())
    me_b.update()
    Nr = np.zeros(NV * 3)
    me_b.vertices.foreach_get("normal", Nr)
    Nr = Nr.reshape(-1, 3)
    Vt = taubin(V0, E)
    print("DRILL blob verts", NV, "snapped", snapped, "mouth dent", int(mouth.sum()), flush=True)
    # 八个猜测（种子 40+k，和旧版同种子）
    D_g = []
    for k in range(8):
        rng = np.random.default_rng(40 + k)
        d = np.zeros(NV)
        for wgt in (0.5, 0.3, 0.2):
            kv = rng.uniform(0.14, 0.36, 3) * rng.choice([-1.0, 1.0], 3)
            ph = rng.uniform(0, 2 * math.pi)
            d += wgt * np.sin(V0 @ kv + ph)
        D_g.append(GUESS_A * d)
    zero = np.zeros(NV)

    melt = KP.mat_solid("w2_melt", "#9A968C", rough=0.06, coat=1.0, sss=0.05)
    mb = next(n for n in melt.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    blue_rgba = tuple(next(n for n in Kt.blue.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value)
    grey_rgba = tuple(mb.inputs["Base Color"].default_value)
    blob = bpy.data.objects.new("w2_blob", me_b)
    sc.collection.objects.link(blob)
    for p in me_b.polygons:
        p.use_smooth = True
    me_b.materials.append(melt)
    blob["drill_role"] = "blob"
    F_B0, F_B1 = t.jump + 2, t.settle - 1                               # 液团可见的帧（前后各由 p29、插座接上）
    SD.hide_tree(blob, [(0, True), (F_B0 - 1, True), (F_B0, False), (F_B1, False), (F_B1 + 1, True)])

    # 液团的位置、朝向（世界）
    rng_ax = np.random.default_rng(77)
    axes = [Vector(rng_ax.normal(size=3)).normalized() for _ in range(8)]

    def tumble_q(b):
        q = q_lie.copy()
        n_bar = (b - 4) / 4.0
        for m in range(int(max(0, math.floor(n_bar))) + 1):
            frac = clamp(n_bar - m)
            if frac <= 0:
                break
            q = Quaternion(axes[m % 8], math.radians(90 * smoother(frac))) @ q
        tu = ramp(b, 9.75, 10.0, lambda x: x) if b < 10 else 1.0
        flip = 90 * (smoother(tu) if b < 10 else 1.0 + settle(b, 10.0, 0.1, n=1.5, dur=0.7))
        q = Quaternion((1, 0, 0), math.radians(flip)) @ q
        return q

    def blob_state(f):
        b = t.b(f)
        if b < 6:
            u = clamp((b - 4) / 2.0)
            c = P29C.lerp(Vector(APEX) * MM, jump_curve(u))
        else:
            c = Vector(APEX) * MM + Vector((0, 0, 1.0 * MM * math.sin(2 * math.pi * (b - 6) / 8)))
        if b >= 12:
            u = smoother((b - 12) / 15.5)
            c = c.lerp(float_c(f), u)
        q = tumble_q(b)
        if b >= 20:
            u = smoother((b - 20) / 7.5)
            q = q.slerp(q_up @ Quaternion(), u) if u < 1 else q_up.copy()
            if u >= 1:
                q = s_state_q(f)
        return c, q

    def s_state_q(f):
        return sock_state(f)[1]

    bmats, b_center = {}, {}
    for f in range(F_B0 - 2, F_B1 + 3):
        c, q = blob_state(f)
        if f >= t.float_at:
            c, q = sock_state(f)
        bmats[f] = Matrix.Translation(c - (q.to_matrix() @ bc)) @ q.to_matrix().to_4x4()
        b_center[f] = c
    for f in range(F_B0 - 2, F_B1 + 3):
        loc, q, _ = bmats[f].decompose()
        SD.key_xform(blob, f, loc=loc, quat=q, scale=(S, S, S))
    # 刚跳起时液团就是磨砂件的样子（同一帧换件不跳）：液团每个顶点从中心沿径向打到磨砂件最外一层，得到"磨砂件形状"的局部坐标，
    # 第 4–5.6 拍里从它熔成插座外包络（之后才开始猜）
    A_s = np.array(bmats[F_B0]) @ np.diag([S * MM, S * MM, S * MM, 1])
    Wv = V0 @ A_s[:3, :3].T + A_s[:3, 3]
    cb = np.array(b_center[F_B0])
    P29L = np.empty_like(V0)
    lift = np.array(b_center[F_B0] - P29C)
    for i in range(NV):
        dvec = Vector(tuple(Wv[i] - cb)).normalized()
        o_ = P29C + dvec * 0.06
        h = p29_bvh.ray_cast(o_, -dvec, 0.07)
        hw = np.array(h[0]) if h[0] is not None else np.array(P29C + dvec * 0.010)
        P29L[i] = hw + lift
    A_si = np.linalg.inv(A_s)
    P29L = P29L @ A_si[:3, :3].T + A_si[:3, 3]
    grow0 = 1.0

    def blob_local(f):
        b = t.b(f)
        g0, g1, w = guess_mix(b)
        d = (D_g[g0] if g0 >= 0 else zero) * (1 - w) + (D_g[g1] if g1 >= 0 else zero) * w
        tw = twitch_of(b)
        if tw:
            d = d + tw * D_g[(g1 + 1) % 8]
        a = guess_amp(b)
        m = melt_of(b)
        V = V0 + m * (Vt - V0) + (a * d)[:, None] * Nr
        mp = smoother((b - 4.0) / 1.6)
        if mp < 1:
            V = P29L * (1 - mp) + V * mp
        # 世界空间的"挤 / 拧"（竖直方向是世界的）：局部 → 世界 → 变形 → 回局部
        sq = 0.0
        if 5.75 <= b < 6:
            sq = 0.28 * smoother((b - 5.75) / 0.25)
        elif b >= 6:
            sq = 0.28 * math.exp(-4.0 * (b - 6)) * math.cos(2 * math.pi * 1.2 * (b - 6))
        twa = 0.0
        if 7.7 <= b < 8:
            twa = 35.0 * smoother((b - 7.7) / 0.3)
        elif 8 <= b < 9.6:
            twa = 35.0 * (1 - smoother((b - 8.0) / 1.6))
        if abs(sq) > 1e-4 or abs(twa) > 1e-3:
            A = np.array(bmats[f]) @ np.diag([S * MM, S * MM, S * MM, 1])
            Wp = V @ A[:3, :3].T + A[:3, 3]
            c = np.array(b_center[f])
            Wp = Wp - c
            if abs(sq) > 1e-4:
                kz = 1 - sq
                kxy = 1 / math.sqrt(kz)
                Wp = Wp * np.array([kxy, kxy, kz])
            if abs(twa) > 1e-3:
                hz = max(1e-6, np.abs(Wp[:, 2]).max())
                ang = np.radians(twa) * np.clip(Wp[:, 2] / hz, 0, 1)
                ca, sa = np.cos(ang), np.sin(ang)
                x, y = Wp[:, 0].copy(), Wp[:, 1].copy()
                Wp[:, 0], Wp[:, 1] = ca * x - sa * y, sa * x + ca * y
            Wp = Wp + c
            Ai = np.linalg.inv(A)
            V = Wp @ Ai[:3, :3].T + Ai[:3, 3]
        return V

    blob_frames = list(range(F_B0 - 2, F_B1 + 3))
    blob_boxes = {}
    sub_i = np.linspace(0, NV - 1, 600).astype(int)

    def blob_iter():
        for f in blob_frames:
            V = blob_local(f)
            A = np.array(bmats[f]) @ np.diag([S * MM, S * MM, S * MM, 1])
            blob_boxes[f] = (V[sub_i] @ A[:3, :3].T + A[:3, 3])
            yield V * MM
    write_pc2(W / "blob.pc2", blob_iter(), NV, len(blob_frames))
    mc = blob.modifiers.new("cache", "MESH_CACHE")
    mc.cache_format = "PC2"
    mc.filepath = str(W / "blob.pc2")
    mc.frame_start = float(blob_frames[0])
    mc.frame_scale = 1.0
    mc.play_mode = "SCENE"
    mc.time_mode = "FRAME"
    mc.interpolation = "LINEAR"
    mc.deform_mode = "OVERWRITE"
    print("DRILL blob pc2", len(blob_frames), "frames", flush=True)
    # 底色灰 → 克莱因蓝（第 12–27 拍），最后 3 拍粗糙度、清漆走到 K.blue 的值（第 28 拍换插座时不跳）
    rough_blue = next(n for n in Kt.blue.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Roughness"].default_value
    coat_blue = next(n for n in Kt.blue.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Coat Weight"].default_value
    for f in range(t.squash_end - 8, F_B1 + 2, 2):
        b = t.b(f)
        u = blue_of(b)
        mb.inputs["Base Color"].default_value = tuple(lerp(grey_rgba[i], blue_rgba[i], u) for i in range(4))
        mb.inputs["Base Color"].keyframe_insert("default_value", frame=f)
        v = smoother((b - 25) / 3.0)
        mb.inputs["Roughness"].default_value = lerp(0.06, rough_blue, v)
        mb.inputs["Roughness"].keyframe_insert("default_value", frame=f)
        mb.inputs["Coat Weight"].default_value = lerp(1.0, coat_blue, v)
        mb.inputs["Coat Weight"].keyframe_insert("default_value", frame=f)

    # ---- p29 被吃：表面波纹（Wave）、磨砂 → 熔料 6 帧交叉、压扁 0.85；第 4 拍弹出去两帧后换成液团
    pm = p29_meshes[0]
    mix_m = pm.data.materials[0].copy()
    mix_m.name = "w2_p29_frost_to_melt"
    nt = mix_m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    lk = next(l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface")
    src_sock = lk.from_socket
    pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for nm_ in ("Base Color", "Roughness", "Coat Weight"):
        pb.inputs[nm_].default_value = mb.inputs[nm_].default_value
    pb.inputs["Base Color"].default_value = grey_rgba
    mxs = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(src_sock, mxs.inputs[1])
    nt.links.new(pb.outputs[0], mxs.inputs[2])
    nt.links.new(mxs.outputs[0], out.inputs["Surface"])
    vol = [l for l in nt.links if l.to_node == out and l.to_socket.name == "Volume"]
    pm.data.materials.clear()
    pm.data.materials.append(mix_m)
    for f, v in ((0, 0.0), (t.pulse_end, 0.0), (t.pulse_end + 6, 1.0)):
        mxs.inputs[0].default_value = v
        mxs.inputs[0].keyframe_insert("default_value", frame=f)
    if vol:                                                              # 熔料不透明：体积吸收 6 帧里关掉
        va = vol[0].from_node
        dens = va.inputs["Density"].default_value
        for f, v in ((0, dens), (t.pulse_end, dens), (t.pulse_end + 6, 0.0)):
            va.inputs["Density"].default_value = v
            va.inputs["Density"].keyframe_insert("default_value", frame=f)
    wv = pm.modifiers.new("w2_ripple", "WAVE")
    wv.use_normal = True
    wv.width = 6 * MM
    wv.narrowness = 1.2
    wv.speed = 0.25 * MM
    wv.time_offset = float(t.pulse_end)
    wv.start_position_object = None
    for f, h in ((0, 0.0), (t.pulse_end, 0.0), (t.pulse_end + 6, 0.45 * MM), (t.jump, 0.45 * MM), (t.jump + 2, 0.0)):
        wv.height = h
        wv.keyframe_insert("height", frame=f)
    p29.rotation_mode = "XYZ"
    base_loc = p29.location.copy()
    for f in range(0, F_B0 + 1):
        kz = 1.0
        if t.pulse_end <= f < t.jump:
            kz = 1 - 0.15 * ease_in((f - t.pulse_end) / max(1, t.squash_end - t.pulse_end), 1.6) if f < t.squash_end else 0.85
        if f >= t.jump:
            kz = 1.08
        p29.scale = (1, 1, kz)
        p29.keyframe_insert("scale", frame=f)
        dz = 0.0
        if f >= t.jump:
            c, _ = blob_state(f)
            dz = (c - P29C).z
        p29.location = base_loc + Vector((0, 0, dz)) * (1.0 / max(1e-9, ucell.matrix_world.to_scale()[2]))
        p29.keyframe_insert("location", frame=f)
    for m in [p29] + list(p29.children_recursive):
        if not m.hide_render:
            for f_, h_ in ((0, False), (F_B0 - 1, False), (F_B0, True)):
                m.hide_render = m.hide_viewport = h_
                m.keyframe_insert("hide_render", frame=f_)
                m.keyframe_insert("hide_viewport", frame=f_)

    # ================= 红尾巴 w2_tail：AlphaFold 303–346 号残基 → 插座局部，推到壳外
    d = np.load(str(NPZ))
    v = d["verts"].astype(float)
    c0 = v.mean(0)
    mn = d["mouth"].astype(float)
    mn /= np.linalg.norm(mn)
    if S_.FLIP_MOUTH:
        mn = -mn
    yaw = math.atan2(mn[1], mn[0])
    Rz = np.array([[math.cos(-yaw), -math.sin(-yaw), 0], [math.sin(-yaw), math.cos(-yaw), 0], [0, 0, 1]])
    m2 = Rz @ mn
    pitch = math.atan2(m2[2], m2[0])
    Ry = np.array([[math.cos(pitch), 0, math.sin(pitch)], [0, 1, 0], [-math.sin(pitch), 0, math.cos(pitch)]])
    Rm = Ry @ Rz
    w_ = (v - c0) @ Rm.T
    pk = (d["pocket"].astype(float) - c0) @ Rm.T
    s_env = 36.0 / max(np.ptp(w_[:, 0]), np.ptp(w_[:, 1]))
    hull = S_._hull((w_ - pk)[:, :2] * s_env)
    shift = np.array([cw, cu]) - hull.mean(0)
    ca = [(r_, x, y, z) for (_, r_, rn, an, el, x, y, z, bf) in SD.pdb_atoms(STRUCT) if an == "CA" and 302 <= r_ <= 346]
    ca.sort()
    xyz = np.array([[x, y, z] for _, x, y, z in ca])
    loc = ((xyz - c0) @ Rm.T - pk) * s_env
    loc[:, :2] += shift
    root302 = loc[0].copy()
    path_raw = loc[1:]                                                   # 303–346：44 个节点

    def push_out(P, clear, iters=8):
        P = np.array(P, float)
        for it in range(iters):
            if it:                                                       # 先平滑再推（最后一步一定是推，推完不再被平滑拉回壳里）
                P[1:-1] = 0.5 * P[1:-1] + 0.25 * (P[:-2] + P[2:])
            for i in range(len(P)):
                q, n, _, dist = env_bvh.find_nearest(Vector(P[i]))
                if q is None:
                    continue
                sgn = (Vector(P[i]) - q).dot(n)
                if sgn < clear:
                    P[i] = np.array(q + n * (clear + 0.05))
                hit = sock_bvh.find_nearest(Vector(P[i]), clear + 1.0)
                if hit[0] is not None and hit[3] < clear:
                    dv = Vector(P[i]) - hit[0]
                    dv = dv.normalized() if dv.length > 1e-6 and dv.dot(hit[1]) > 0 else hit[1]   # 点在壁里（法线背面）时沿法线往外
                    P[i] = np.array(hit[0] + dv * (clear + 0.05))
        return P

    def min_clear(P):
        out_ = 99.0
        for p in P:
            q, n, _, dd = env_bvh.find_nearest(Vector(p))
            sg = (Vector(p) - q).dot(n) if q is not None else 99
            h = sock_bvh.find_nearest(Vector(p), 5.0)
            out_ = min(out_, sg, h[3] if h[0] is not None else 99)
        return out_

    CLEAR = TAIL_R + 0.3
    G0 = push_out(path_raw, CLEAR)
    guesses = []
    for sd_ in (60, 61, 62):
        rng = np.random.default_rng(sd_)
        u_ = np.linspace(0, 1, NODES)
        off = np.zeros((NODES, 3))
        for j in range(3):
            fq = rng.uniform(0.6, 1.8, 3)
            phs = rng.uniform(0, 2 * math.pi, 3)
            off += np.sin(2 * math.pi * fq[None, :] * u_[:, None] + phs[None, :]) * rng.uniform(0.4, 1.0)
        off *= 3.0 / max(1e-9, np.linalg.norm(off, axis=1).max())
        off *= np.clip(u_ * 4, 0, 1)[:, None]                             # 根部钉住
        guesses.append(push_out(G0 + off, CLEAR))
    LIQ_CLEAR = 1.6 + 0.3
    G_liq = push_out(G0, LIQ_CLEAR)
    print("DRILL tail clearance (mm, local)", round(min_clear(G0), 3), [round(min_clear(g), 3) for g in guesses], "liquid", round(min_clear(G_liq), 3),
          "root302", [round(x, 1) for x in root302], flush=True)

    # 尾巴逐帧节点（世界米）
    F_T0 = t.tail - 8                                                   # 拍前 8 帧从根部长出来，第 29 拍长满
    sock_np = [np.array(m) for m in smats]
    Ssc = S * MM

    def L2W(f, P):
        A = sock_np[f]
        return (P * Ssc) @ A[:3, :3].T + A[:3, 3]

    def W2L(f, X):
        A = np.linalg.inv(sock_np[f])
        return (X @ A[:3, :3].T + A[:3, 3]) / Ssc

    def local_target(f):
        b = t.b(f)
        if b < 32:
            hb = (b - 29) * 2
            i0 = int(math.floor(max(0, hb)))
            u = smoother((hb - i0) / 0.35)
            return guesses[i0 % 3] * (1 - u) + guesses[(i0 + 1) % 3] * u
        u = smoother((b - 32) / 0.6)
        last = guesses[int(math.floor((32 - 29) * 2)) % 3]
        return last * (1 - u) + G_liq * u

    def radius_of(f):
        return lerp(TAIL_R, 1.6, smoother((f - t.liquid) / 18.0))

    nodes = {}
    sim_from = t.windup - 6
    x = v_ = None
    k_root, k_tip = (2 * math.pi * 12) ** 2, (2 * math.pi * 2.6) ** 2
    kk = np.array([k_tip + (k_root - k_tip) * (1 - i / (NODES - 1)) ** 2 for i in range(NODES)])[:, None]
    cdamp = 2 * 0.32 * np.sqrt(kk)
    sub = 4
    dt = 1.0 / (SD.FPS * sub)
    def target_l(f):
        Pl = local_target(f)
        if f >= t.shake:                                                 # 甩的时候往外拉长（离根越远拉得越多）
            Pl = Pl[0] + (Pl - Pl[0]) * (1.0 + 0.18 * smoother((f - t.shake) / 20.0))
        return Pl

    for f in range(F_T0, t.fling):
        Pl = target_l(f)
        Tw = L2W(f, Pl)
        if f < sim_from:
            nodes[f] = Tw
            continue
        if x is None:
            x = Tw.copy()
            v_ = (Tw - L2W(f - 1, target_l(f - 1))) * SD.FPS
        Tw0 = L2W(f - 1, target_l(f - 1)) if f > sim_from else Tw
        for k in range(sub):
            tgt = Tw0 + (Tw - Tw0) * ((k + 1) / sub)
            a = kk * (tgt - x) - cdamp * v_
            v_ = v_ + a * dt
            x = x + v_ * dt
            x[0] = tgt[0]
            v_[0] = 0
        loc_ = W2L(f, x)
        loc_ = push_out(loc_, radius_of(f) * 1.15 + 0.45, iters=1)       # 滞后的节点不许钻进壳里（留出液面起伏和节点间弦的下垂）
        loc_[0] = Pl[0]
        x = L2W(f, loc_)
        nodes[f] = x.copy()
    # 甩飞：根部放开，节点沿"自己 + 弧线 + 台面"一条路滑，尖头在前
    Q = nodes[t.fling - 1]
    tip_v = (nodes[t.fling - 1][-1] - nodes[t.fling - 3][-1]) * (SD.FPS / 2)
    ztab = 0.0
    Lp = np.array([LAND[0] * MM, LAND[1] * MM, ztab + (1.6 * S + 0.06) * MM])   # 落点是管心：离台面一个管半径
    P0 = Q[-1]
    dirv = tip_v / max(1e-9, np.linalg.norm(tip_v))
    side = np.array([1.0, 0, 0])
    P1 = P0 + (0.5 * dirv + 0.9 * side + np.array([0, 0, 0.25])) * 0.030
    P2 = Lp + np.array([0, 0, 0.060])
    flight = bezier(P0, P1, P2, Lp, 240)
    tdir = np.array([COIL_C[0] - LAND[0], COIL_C[1] - LAND[1], 0.0]) * MM
    tdir = tdir / max(1e-9, np.linalg.norm(tdir))
    Lq = arclen(Q[::-1])                                                 # 尖头 → 根
    L_tail = Lq[-1]
    table_seg = np.array([Lp + tdir * (L_tail + 0.012) * u for u in np.linspace(0, 1, 60)])
    road = np.vstack([Q, flight[1:], table_seg[1:]])                    # 根 → 尖 → 弧线 → 台面
    s_road = arclen(road)
    s_nodes0 = arclen(Q)
    s_tipL = s_road[len(Q) - 1]                                          # 尖头在路上的弧长
    s_land = s_road[len(Q) - 1 + len(flight) - 1]
    Lb = s_land - s_tipL
    F_L, F_flat = t.land, t.land + 12

    def dist_of(f):
        if f <= t.fling:
            return 0.0
        if f < F_L:
            u = (f - t.fling) / (F_L - t.fling)
            return Lb * (0.55 * u + 0.45 * u * u)
        u = ease_out((f - F_L) / (F_flat - F_L), 2.0)
        return Lb + (L_tail + 0.004) * u

    spiral_n = 400
    th_max = 2.5 * 2 * math.pi
    ths = np.linspace(0, th_max, spiral_n)
    rs = (2.5 + (9.0 - 2.5) * ths / th_max) * MM
    spiral = np.c_[COIL_C[0] * MM + rs * np.cos(ths + 1.0), COIL_C[1] * MM + rs * np.sin(ths + 1.0), np.full(spiral_n, ztab)]
    s_sp = arclen(spiral)

    def tail_state(f):
        """返回 (节点 44×3 世界米, 每节点半径 mm 世界, 竖向缩放, 横向缩放)。"""
        rad0 = radius_of(f) * S
        if f < t.fling:
            P = nodes[f]
            g = smoother((f - F_T0) / 8.0)
            if g < 1:                                                    # 冒出来：从根部长出
                P = P[0] + (P - P[0]) * max(0.02, g)
                rad0 = rad0 * max(0.05, g)
            vs = np.ones(NODES)
            hs = np.ones(NODES)
            rad = np.full(NODES, rad0)
            if f >= t.liquid:                                            # 液体：管面起伏
                ph = (f - t.liquid) / SD.FPS
                rad = rad * (1 + 0.12 * np.sin(2 * math.pi * (np.arange(NODES) / 9.0 - 1.6 * ph)) * smoother((f - t.liquid) / 18.0))
            return P, rad, vs, hs
        dd = dist_of(f)
        s = s_nodes0 + dd
        P = along(road, s_road, s)
        still_on = s < s_tipL                                            # 还在"自己那一段"路上的节点跟着插座走（插座甩完还在回正）
        if still_on.any():
            P[still_on] = L2W(f, W2L(t.fling - 1, P[still_on]))
        on_tab = np.clip((s - s_land) / 0.004, 0, 1)                     # 落到台面上的那几节
        fl = on_tab * smoother((f - F_L) / 12.0)
        vs = 1 - 0.7 * fl
        hs = 1 + 1.2 * fl
        rad = np.full(NODES, 1.6 * S)
        if f >= t.coil:                                                  # 收成红线圈：沿螺线排开，截面回圆，管半径 1.2
            u = smoother((f - t.coil) / max(1, t.coil_end - t.coil))
            tgt_s = np.linspace(s_sp[-1], 0, NODES)                      # 根在外圈、尖在里面
            Psp = along(spiral, s_sp, tgt_s)
            P = P * (1 - u) + Psp * u
            vs = vs * (1 - u) + 1.0 * u
            hs = hs * (1 - u) + 1.0 * u
            rad = rad * (1 - u) + 1.2 * u
        P = P.copy()
        low = ztab + (rad * MM) * vs + 0.06 * MM                         # 贴台面（留 0.06 mm）
        P[:, 2] = np.where(on_tab > 0, low, P[:, 2])
        return P, rad, vs, hs

    taper = np.ones(NODES)
    taper[-8:] = np.linspace(1.0, 0.45, 8)
    tail_frames = list(range(F_T0, NF))
    M_r = (NODES - 1) * SUBR + 1
    tail_boxes = {}

    fixes = {}

    def clear_rings(f, C, R_):
        """加密后的中线逐圈查：圈心离插座表面（外包络 + 实际网格）不到 半径 + 0.15 mm 就沿法线推出去（插座局部 mm 里算）。"""
        L_ = W2L(f, C)
        Rl = R_ / Ssc
        n_fix = 0
        for _ in range(3):
            moved = False
            for i in range(1, len(L_)):
                need = Rl[i] + 0.15
                q, n, _, _ = env_bvh.find_nearest(Vector(L_[i]))
                if q is not None:
                    sg = (Vector(L_[i]) - q).dot(n)
                    if sg < need:
                        L_[i] = np.array(q + n * (need + 0.02))
                        moved = True
                        n_fix += 1
                h = sock_bvh.find_nearest(Vector(L_[i]), need + 0.5)
                if h[0] is not None and h[3] < need:
                    dv = Vector(L_[i]) - h[0]
                    dv = dv.normalized() if dv.length > 1e-6 and dv.dot(h[1]) > 0 else h[1]
                    L_[i] = np.array(h[0] + dv * (need + 0.02))
                    moved = True
                    n_fix += 1
            if not moved:
                break
            L_[1:-1] = 0.6 * L_[1:-1] + 0.2 * (L_[:-2] + L_[2:])
        fixes[f] = n_fix
        return L2W(f, L_)

    def tail_iter():
        for f in tail_frames:
            P, rad, vs, hs = tail_state(f)
            tail_boxes[f] = P
            C = catmull(P, SUBR)
            ii = np.linspace(0, NODES - 1, M_r)
            R_ = np.interp(ii, np.arange(NODES), rad * taper) * MM
            if f < t.fling + 40:
                C = clear_rings(f, C, R_ * np.maximum(np.interp(ii, np.arange(NODES), vs), np.interp(ii, np.arange(NODES), hs)))
            if f >= t.fling:                                             # 加密的中线在拐角会冲过头（Catmull-Rom），贴台面的圈不许低于台面
                C[:, 2] = np.maximum(C[:, 2], ztab + R_ * np.interp(ii, np.arange(NODES), vs) + 0.06 * MM)
            yield tube_verts(C, R_, np.interp(ii, np.arange(NODES), vs), np.interp(ii, np.arange(NODES), hs))
    me_t = bpy.data.meshes.new("w2_tail")
    P_, rad_, vs_, hs_ = tail_state(F_T0)
    C_ = catmull(P_, SUBR)
    V_ = tube_verts(C_, np.full(M_r, TAIL_R * S * MM), np.ones(M_r), np.ones(M_r))
    me_t.from_pydata(V_.tolist(), [], tube_faces(M_r))
    for p in me_t.polygons:
        p.use_smooth = True
    me_t.materials.append(Kt.red)
    tail = bpy.data.objects.new("w2_tail", me_t)
    sc.collection.objects.link(tail)
    tail["drill_role"] = "tail"
    write_pc2(W / "tail.pc2", tail_iter(), len(V_), len(tail_frames))
    mt = tail.modifiers.new("cache", "MESH_CACHE")
    mt.cache_format = "PC2"
    mt.filepath = str(W / "tail.pc2")
    mt.frame_start = float(tail_frames[0])
    mt.play_mode = "SCENE"
    mt.time_mode = "FRAME"
    mt.interpolation = "LINEAR"
    mt.deform_mode = "OVERWRITE"
    SD.hide_tree(tail, [(0, True), (F_T0 - 1, True), (F_T0, False)])
    print("DRILL tail ring fixes", sum(fixes.values()), "max/frame", max(fixes.values()) if fixes else 0, flush=True)
    print("DRILL tail", len(V_), "verts", len(tail_frames), "frames; flight", round(Lb / MM, 1), "mm; tail length", round(L_tail / MM, 1), "mm", flush=True)

    # ================= 走料鼓包：芯片浇口 → 料杆 → 磨砂件的浇口
    tip_g = min(ugates, key=lambda g: abs(g["tip"].y / MM - (uy / MM - 4)) + (0 if g["tip"].x > ux else 99))
    tgx, tgy = tip_g["tip"].x / MM, tip_g["tip"].y / MM
    cx6, cy2 = chip_cell.matrix_world.translation.x / MM, chip_cell.matrix_world.translation.y / MM
    R1, R2 = KP.R_LOOP, 1.2
    pts = [(cx6 - 14.2, cy2 + 1.75, 1.0), (cx6 - 30, cy2 + 1.75, R1), (cx6 - 30, cy2 + 15, R1), (cx6 - 25, cy2 + 20, R1), (cx6, cy2 + 20, R1),
           (cx6, cy2 + 26, R2), (cx6 - 25, cy2 + 26, R1), (cx6 - 30, cy2 + 31, R1), (cx6 - 30, cy2 + 61, R1), (cx6 - 25, cy2 + 66, R1), (cx6, cy2 + 66, R1),
           (cx6, cy2 + 72, R2), (cx6 - 25, cy2 + 72, R1), (cx6 - 30, cy2 + 77, R1), (cx6 - 30, uy / MM, R1), (ux / MM + 30, uy / MM, R2), (ux / MM + 30, tgy, R1),
           (tgx, tgy, 0.8)]
    pmat = BG.pulse_mat(Kt.white, gain=1.0)
    pulse, pulse_pos, pulse_path = BG.guide_runner(pts, t.pulse, t.pulse_end, zb / MM, pmat, name="w2_pulse", eat=6, ease=True)
    chip_gates = [g for g in KP.gates_of(chip_cell) if g.type == "MESH"]
    for g in chip_gates:                                                 # 芯片浇口预颤 6 帧（第 1 拍出发前）
        for f in range(t.pulse - 7, t.pulse + 1):
            k = 1.0 - 0.18 * math.sin(math.pi * clamp((f - (t.pulse - 6)) / 6.0))
            g.scale = (k, k, 1.0)
            g.keyframe_insert("scale", frame=f)

    # ================= 英雄件中心（镜头空间、焦点、灯都跟它）
    def hero_c(f):
        if f < F_B0:
            return P29C
        if f <= F_B1:
            return b_center.get(f, s_center[f])
        return s_center[f]

    # ---- 镜头
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0
    Wm = lambda x, y, z: (x * MM, y * MM, z * MM)  # noqa: E731

    def hk(f, az_w, el, dist_mm, lens, right_mm=0.0, up_mm=0.0, ease="inout"):
        """hero 空间的键：目标 = 英雄件中心 + 画面右移/上移（毫米），方位用世界写法（0 = 从 −Y 看）。"""
        a = math.radians(az_w)
        off = (-right_mm * math.cos(a), -right_mm * math.sin(a), -up_mm)
        return dict(f=f, space="hero", tgt=off, az=az_w - 90.0, el=el, dist=dist_mm, lens=lens, ease=ease)

    mid_E = ((hx + ux) / 2 / MM, (hy + uy) / 2 / MM)
    keys = [
        dict(f=0, space="world", tgt=Wm(-62, 77, 38), az=28, el=32, dist=0.190, lens=35),
        dict(f=t.f(1.8), space="world", tgt=Wm(-70, 92, 37), az=25, el=31, dist=0.168, lens=36),
        dict(f=t.pulse_end, space="world", tgt=Wm(ux / MM, uy / MM + 4, 11), az=18, el=30, dist=0.132, lens=40),
        dict(f=t.jump, space="world", tgt=Wm(ux / MM, uy / MM + 2, 24), az=16, el=26, dist=0.140, lens=42),
        # 20 号表里的距离（110、105）按 K12 实测放大：液团猜形状时外接框比插座大 40%（变形 + 刚跳起时和磨砂件一样大），显示高要 520–640 px
        hk(t.jump + 10, 14, 20, 150, 44, up_mm=4.0),                     # 跳起时镜头马上跟上去（不让液团冲出画面上沿太久）
        hk(t.f(5.2), 12, 16, 166, 45, up_mm=8.0),
        hk(t.f(12), 2, 17, 170, 45, up_mm=7.0),
        hk(t.cam_d, -8, 18, 150, 45, right_mm=12.0, up_mm=2.0),
        hk(t.f(24), -8, 18, 125, 45, right_mm=11.0, up_mm=2.2),
        hk(t.float_at, -8, 18, 106, 45, right_mm=9.8, up_mm=2.6),
        hk(t.settle, -8, 18, 104, 45, right_mm=9.8, up_mm=2.6),
        hk(t.windup, -8, 18, 98, 45, right_mm=9.4, up_mm=2.6),
        dict(f=t.shake, space="world", tgt=Wm(mid_E[0], mid_E[1] + 4, 38.5), az=20, el=46, dist=0.178, lens=35),
        dict(f=t.seat, space="world", tgt=Wm(mid_E[0] - 3, mid_E[1] + 4, 34.5), az=20, el=46, dist=0.175, lens=35, ease="linear"),
        dict(f=t.rise - 40, space="world", tgt=Wm(mid_E[0] - 12, mid_E[1] + 2, 32), az=19, el=48, dist=0.161, lens=35),
        dict(f=t.rise + 10, space="sock", tgt=(12.0, 0.0, 0.0), az=0.0, el=-5.0, dist=78.0, lens=35),
        dict(f=t.bore_full, space="sock", tgt=(0.0, 0.0, 0.0), az=0.0, el=-5.0, dist=9.5, lens=35, ease="inout"),
        dict(f=NF - 1, space="sock", tgt=(0.0, 0.0, 0.0), az=0.0, el=-5.0, dist=8.6, lens=35, ease="linear"),
    ]
    rigc = SD.CamRig(keys, lambda f: smats[f], MM * S, spaces={"hero": (lambda f: Matrix.Translation(hero_c(f)), MM)})
    for fs_, amp, du in ((t.settle, 0.3, 4), (t.seat, 0.3, 4), (t.squeeze, 0.2, 3), (t.twist, 0.2, 3), (t.turn, 0.2, 3), (t.slower, 0.15, 3),
                         (t.calmer, 0.15, 3), (t.firmer, 0.15, 3), (t.bluer, 0.15, 3)):
        rigc.shake(fs_, amp, du)

    def drift(f, eye, tgt):
        dd = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        k = 1.0 - ramp(f, t.rise - 30, t.rise + 10)
        off = (right * 0.008 * math.sin(f / 97.0) + up * 0.006 * math.cos(f / 131.0)) * dd * k
        return off, off * 0.6
    recs = rigc.bake(cam, NF, drift=drift)

    # ---- 灯：大板主光（以两格中间为中心）+ 英雄件冷白轮廓光 + 浮着时下面的骨白反光卡 + 段尾孔桶转场灯
    KP.lights((hx + ux) / 2, (hy + uy) / 2 - 0.02, 1.0)
    key_l = bpy.data.objects["key"]
    hero_coll = bpy.data.collections.new("W2_hero_lit")
    sc.collection.children.link(hero_coll)
    for o in [blob, tail] + s_meshes + p29_meshes:
        hero_coll.objects.link(o)
    E_key = key_l.data.energy / (math.pi * (key_l.location - hero_c(400)).length ** 2)
    size_h = 0.027
    rim = bpy.data.lights.new("w2_rim", "AREA")
    rim.shape = "DISK"
    rim.size = 1.2 * size_h
    rim.color = (0.90, 0.95, 1.0)
    rim_o = bpy.data.objects.new("w2_rim", rim)
    sc.collection.objects.link(rim_o)
    rim_o.light_linking.receiver_collection = hero_coll
    rim_w = E_key * (3 * size_h) ** 2 * 3.0
    for f in range(NF):
        c = hero_c(f)
        to_cam = recs[f][0] - c
        a0 = math.atan2(to_cam.y, to_cam.x) + math.radians(135)
        el_ = math.radians(35)
        rim_o.location = c + Vector((math.cos(a0) * math.cos(el_), math.sin(a0) * math.cos(el_), math.sin(el_))) * 3 * size_h
        rim_o.rotation_mode = "QUATERNION"
        rim_o.rotation_quaternion = (c - rim_o.location).to_track_quat("-Z", "Y")
        rim_o.keyframe_insert("location", frame=f)
        rim_o.keyframe_insert("rotation_quaternion", frame=f)
        rim.energy = rim_w * (1 - ramp(f, t.rise - 20, t.rise + 10))
        rim.keyframe_insert("energy", frame=f)
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    card = bpy.context.object
    card.name = "w2_refl_card"
    card.scale = (0.080, 0.050, 1)
    cm = bpy.data.materials.new("w2_refl_card")
    cm.use_nodes = True
    cnt = cm.node_tree
    cnt.nodes.clear()
    ce = cnt.nodes.new("ShaderNodeEmission")
    ce.inputs["Color"].default_value = (0.905, 0.88, 0.83, 1)
    ce.inputs["Strength"].default_value = 1.2
    co = cnt.nodes.new("ShaderNodeOutputMaterial")
    cnt.links.new(ce.outputs[0], co.inputs["Surface"])
    card.data.materials.append(cm)
    card.visible_camera = False
    card.visible_shadow = False
    card.visible_volume_scatter = False
    for f in range(NF):
        card.location = hero_c(f) - Vector((0, 0, 0.020))
        card.keyframe_insert("location", frame=f)
    SD.hide_tree(card, [(0, True), (F_B0 - 1, True), (F_B0, False), (t.land + 20, False), (t.land + 21, True)])
    tl = bpy.data.lights.new("w2_bore_light", "AREA")
    tl.shape = "DISK"
    tl.size = 0.006
    tl.color = (1.0, 0.98, 0.95)
    tl_o = bpy.data.objects.new("w2_bore_light", tl)
    sc.collection.objects.link(tl_o)
    tl_o.parent = cam
    tl_o.location = (0.0, 0.004, 0.0)
    bore_coll = bpy.data.collections.new("W2_bore_lit")
    sc.collection.children.link(bore_coll)
    for o in bore_objs:
        bore_coll.objects.link(o)
    tl_o.light_linking.receiver_collection = bore_coll
    P_bore = 3 * E_key * math.pi * (0.012 ** 2)
    for f, v in ((0, 0.0), (1459, 0.0), (1475, P_bore), (NF - 1, P_bore)):
        tl.energy = v
        tl.keyframe_insert("energy", frame=f)

    # ---- 焦点和光圈
    chip_c = sum((chip_txt.matrix_world @ Vector(c) for c in chip_txt.bound_box), Vector()) / 8
    coil_w = Vector((COIL_C[0] * MM, COIL_C[1] * MM, 0.001))
    mouth_w = lambda f: smats[f] @ (Vector((12.0, 0, 0)) * MM * S)  # noqa: E731
    floor_w = lambda f: smats[f] @ (Vector((0.5, 0, 0)) * MM * S)  # noqa: E731
    fpts, fst = [], []
    for f in range(NF):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        p = P29C
        p = p.lerp(chip_c, ramp(f, t.chip_focus - 8, t.chip_focus))
        if f >= t.pulse:
            p = chip_c.lerp(Vector(pulse_pos(f)), ramp(f, t.pulse, t.pulse + 8))
        if f >= t.pulse_end:
            p = Vector(pulse_pos(t.pulse_end)).lerp(P29C, ramp(f, t.pulse_end, t.pulse_end + 8))
        if f >= t.jump:
            p = hero_c(f)
        if t.tail - 8 <= f < t.shake:
            tc = Vector(tuple(tail_state(max(F_T0, f))[0].mean(0)))
            p = hero_c(f).lerp(tc, ramp(f, t.tail - 8, t.tail) * 0.6)
        fs_ = 6.0
        if f < t.pulse:
            fs_ = 4.0
        elif f < t.pulse_end:
            fs_ = lerp(4.0, 5.0, ramp(f, t.pulse, t.pulse + 10))
        elif f < t.jump:
            fs_ = lerp(5.0, 6.0, ramp(f, t.pulse_end, t.jump))
        if f >= t.windup:
            # 两格都要实：焦平面放在插座和尾巴/线圈中间（按深度的调和平均），光圈 7，不够就 9、11
            tc = Vector(tuple(tail_state(f)[0].mean(0)))
            d1 = max(0.003, (hero_c(f) - eye).dot(fwd))
            d2 = max(0.003, (tc - eye).dot(fwd))
            dm = 2 * d1 * d2 / (d1 + d2)
            p = eye + fwd * lerp((p - eye).dot(fwd), dm, ramp(f, t.windup, t.shake))
            fs_ = 7.0
            for cand in (7.0, 9.0, 11.0):
                fs_ = cand
                if max(SD.coc_px(lens, cand, dm, d1), SD.coc_px(lens, cand, dm, d2)) <= 2.0:
                    break
            fs_ = lerp(6.0, fs_, ramp(f, t.windup, t.shake))
        if f >= t.rise - 40:
            m_ = mouth_w(f).lerp(floor_w(f), ramp(f, t.rise + 10, t.bore_full))
            p = p.lerp(m_, ramp(f, t.rise - 40, t.rise + 10))
            fs_ = lerp(fs_, 14.0, ramp(f, t.rise - 20, t.rise + 10))
        fpts.append(p)
        fst.append(fs_)
    for i in range(2, NF - 2):                                           # 光圈 5 帧平滑（候选档位切换不跳）
        fst[i] = sum(fst[i - 2:i + 3]) / 5
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    focus_d = []
    for f in range(NF):
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.aperture_fstop = fst[f]
        d.keyframe_insert("aperture_fstop", frame=f)
        d.focus_distance = max(0.003, (fpts[f] - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        focus_d.append(d.focus_distance)

    SD.linear_all([sock, cam, blob, tail, p29, card, rim_o, tl_o, pulse] + list(sock.children_recursive) + list(p29.children_recursive)
                  + [g["cone"] for g in hgates] + chip_gates + [o for o in bpy.data.objects if o.type == "LIGHT"])
    for m in (melt, mix_m):
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for fc in D5.SD_fcurves(m.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- cam.json：逐帧镜头 + 关键物件投影外接框（K10、K12 渲前量）
    s_sub = V0[np.linspace(0, NV - 1, 600).astype(int)]

    def bbox(pts_w, f):
        pp = [SD.project(recs[f], Vector(tuple(p))) for p in pts_w]
        pp = [p for p in pp if p]
        if not pp:
            return None
        xs, ys = [p[0] for p in pp], [p[1] for p in pp]
        return [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
    p29_pts = {}                                                         # 磨砂件真实轮廓（网格顶点抽样，不用三维包围盒，包围盒会大一圈）
    pv = np.array([v.co[:] for v in pm.data.vertices])[::max(1, len(pm.data.vertices) // 800)]
    for f in range(0, F_B0):
        sc.frame_set(f)
        A = np.array(pm.matrix_world)
        p29_pts[f] = pv @ A[:3, :3].T + A[:3, 3]
    camj = dict(seg=seg, nf=NF, frames=[])
    for f in range(NF):
        hero = None
        if f in blob_boxes and F_B0 <= f <= F_B1:
            hero = bbox(blob_boxes[f], f)
        elif f > F_B1:
            hero = bbox(L2W(f, s_sub), f)
        elif f < F_B0:
            hero = bbox(p29_pts[f], f)
        tb = bbox(tail_boxes[f], f) if f in tail_boxes else None
        tp = None
        if f in tail_boxes:
            tp = [[round(q[0]), round(q[1])] for q in (SD.project(recs[f], Vector(tuple(p))) for p in tail_boxes[f]) if q]
        ch = bbox([chip_txt.matrix_world @ Vector(c) for c in chip_txt.bound_box], f) if f < 120 else None
        camj["frames"].append(dict(f=f, eye=list(recs[f][0]), q=list(recs[f][3]), lens=recs[f][2], fstop=fst[f], focus=focus_d[f],
                                   hero=hero, tail=tb, tail_pts=tp, chip_txt=ch, beat=round(t.b(f), 3)))
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    coc = []
    for f in list(range(0, NF, 24)) + [NF - 1]:
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        Sd = focus_d[f]
        dh = (hero_c(f) - eye).dot(fwd)
        row = dict(f=f, beat=round(t.b(f), 2), fstop=round(fst[f], 1), focus_mm=round(Sd / MM, 1), hero_coc=round(SD.coc_px(lens, fst[f], Sd, max(0.003, dh)), 2))
        if f in tail_boxes:
            dt_ = (Vector(tuple(tail_boxes[f].mean(0))) - eye).dot(fwd)
            row["tail_coc"] = round(SD.coc_px(lens, fst[f], Sd, max(0.003, dt_)), 2)
        if f < t.pulse_end:
            row["chip_coc"] = round(SD.coc_px(lens, fst[f], Sd, max(0.003, (chip_c - eye).dot(fwd))), 2)
            row["p29_coc"] = round(SD.coc_px(lens, fst[f], Sd, max(0.003, (P29C - eye).dot(fwd))), 2)
            if t.pulse <= f <= t.pulse_end:
                row["pulse_coc"] = round(SD.coc_px(lens, fst[f], Sd, max(0.003, (Vector(pulse_pos(f)) - eye).dot(fwd))), 2)
        coc.append(row)
    chk = dict(coc=coc, gates_home=[dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in hgates],
               gates_p29=[dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in ugates],
               hidden_banned=hidden_banned, blob_verts=NV, tail_len_mm=round(L_tail / MM, 1), flight_mm=round(Lb / MM, 1),
               tail_clear_mm=round(min_clear(G0), 3), keys=K["events"], P_bore=P_bore, rim_w=rim_w, E_key=E_key,
               pulse_len_mm=round(pulse_path.s[-1], 1))
    (W / "build_check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


# ================================================================ 穿模检查的分组
_DEFORM = {"w2_blob", "w2_tail"}


def _patch_bvh():
    """液团、尾巴是 Mesh Cache 逐帧变形的：BVHCache 默认按名字缓存网格，这两个每帧重取。
    blender -P shot_drill.py 时引擎是 __main__，和这里 import 的 shot_drill 是两个模块对象：两边的类都要改。"""
    mods = [SD] + [m for m in (sys.modules.get("__main__"),) if m is not None and hasattr(m, "BVHCache")]
    for M_ in mods:
        cls = M_.BVHCache
        if getattr(cls, "_w2_patched", False):
            continue
        orig = cls._geo

        def _geo(self, o, dg, _orig=orig):
            if o.name in _DEFORM:
                self.geo.pop(o.name, None)
                self.trees.pop(o.name, None)
            return _orig(self, o, dg)
        cls._geo = _geo
        cls._w2_patched = True


def clip_plan(sc):
    import bpy
    _patch_bvh()
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, blob, tail = R["socket"], R["blob"], R["tail"]
    sc.frame_set(t.settle + 5)                                           # 插座在第 28 拍以前是藏着的：在它显示的帧上取件（藏着的件 _meshes_under 会跳过）
    s_m = D5._meshes_under(sock)
    print("DRILL clip plan: socket meshes", len(s_m), flush=True)
    mine = set([sock, blob, tail] + list(sock.children_recursive))
    hx, hy = sock.matrix_world.translation.x, sock.matrix_world.translation.y
    near = []
    for o in bpy.data.objects:
        if o in mine or o.type not in ("MESH", "CURVE") or o.hide_render or o.name.startswith(("w2_refl", "sweep", "refl_")):
            continue
        if o.name.split(".")[0].endswith("_cut"):
            continue
        bb = [o.matrix_world @ __import__("mathutils").Vector(c) for c in o.bound_box]
        cx = sum(p.x for p in bb) / 8
        cy = sum(p.y for p in bb) / 8
        if -0.215 < cx < -0.040 and 0.060 < cy < 0.175:
            near.append(o)
    sweep = [bpy.data.objects["sweep"]]
    print("DRILL clip plan: board meshes near", len(near), flush=True)
    fr = set(range(t.jump, NF, 2)) | set(range(t.settle - 4, t.settle + 4)) | set(range(t.fling - 6, t.coil_end + 4)) | set(range(t.land, t.seat + 16))

    def groups(f):
        g = []
        if t.jump <= f <= t.settle:
            g.append(("blob_vs_board", [blob], near, None))
        if f >= t.settle:
            g.append(("socket_vs_board", s_m, near, sock))
        if t.tail - 1 <= f:
            g.append(("tail_vs_socket", [tail], s_m, sock))
        if f >= t.fling:
            g.append(("tail_vs_board", [tail], near, None))
            g.append(("tail_vs_table", [tail], sweep, None))
        return g

    return dict(frames=sorted(fr), groups=groups, cam_near=lambda f: s_m, ref=sock)


# ================================================================ 合成、自检（comp_w23.py 合成；这里机检）
def beat_check(seg):
    """K2：事件落帧对公式；K3（T7b）：成片音轨 6–11 kHz 起音和原曲同一拍的起音（扣掉帧取整）——成片音轨是 24_W2_加工 的原样拷贝。"""
    import subprocess
    import numpy as np
    s = beat_sheet()
    K = make_keys()
    rows = []
    for e in K["events"]:
        exact = SD.FPS * (s["grid_fix_s"] + s["beat_s"] * e["beat"])
        rows.append(dict(id=e["id"], beat=e["beat"], f_land=e["f_land"], formula=round(exact, 2), err_f=round(e["f_land"] - exact, 2)))
    k2_ok = all(abs(r["err_f"]) <= 2 for r in rows)
    SR = 44100

    def hf_env(x):
        X = np.fft.rfft(x)
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        y = np.abs(np.fft.irfft(X * ((fr >= 6000) & (fr < 11000)), len(x)))
        k = int(0.003 * SR)
        return np.convolve(y, np.ones(k) / k, "same")

    def onset(env, t_):
        i0, i1 = int((t_ - 0.06) * SR), int((t_ + 0.16) * SR)
        seg_ = env[i0:i1]
        pk = int(np.argmax(seg_))
        base = float(np.median(env[int((t_ - 0.2) * SR):int((t_ - 0.07) * SR)]))
        thr = base + 0.3 * (seg_[pk] - base)
        return (i0 + int(np.argmax(seg_[:pk + 1] > thr))) / SR
    r = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    env = hf_env(np.frombuffer(r.stdout, np.float32).astype(np.float64))
    per = []
    for b in range(4, 48):
        if b % 4 == 2:                                                   # 网格位置 2：歌里提前的装饰音，不算（卡点表 grid_fix_note）
            continue
        f_ = fb(s, b)
        t_ = f_ / SD.FPS
        on = onset(env, t_)
        per.append(dict(beat=b, frame=f_, onset_minus_frame_ms=round((on - t_) * 1000, 1)))
    oa = np.array([x["onset_minus_frame_ms"] for x in per])
    t7b = dict(n=len(per), median_ms=round(float(np.median(oa)), 1), p90_abs_ms=round(float(np.percentile(np.abs(oa), 90)), 1), per_beat=per,
               how="成片音轨 6–11 kHz 3 ms 包络升到 30% 峰值的起音 − 画面拍点帧的时刻；≤ 17 ms = 一帧以内")
    t7b["ok"] = abs(t7b["median_ms"]) <= 17
    return dict(k2_rows=rows, k2_ok=k2_ok, t7b=t7b)


def check(seg):
    """渲完、合成以后：K1 帧数、K7 亮度、K16 音轨逐样本、K2/K3 卡拍、K10/K12 投影框（渲前已在 cam.json）、clip。"""
    import subprocess
    import numpy as np
    W = SD.work(seg)
    res = {}
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,r_frame_rate",
                         "-of", "json", str(OUT_MP4)], capture_output=True, text=True)
    res["K1_ffprobe"] = json.loads(pr.stdout or "{}")
    fr = SD.ff_frames(OUT_MP4, scale=(320, 180)).astype(np.float32) / 255
    luma = (0.2126 * fr[..., 0] + 0.7152 * fr[..., 1] + 0.0722 * fr[..., 2]).mean(axis=(1, 2))
    res["K1_frames"] = int(len(fr))
    res["K7"] = dict(min=round(float(luma.min()), 3), argmin=int(luma.argmin()), mean=round(float(luma.mean()), 3),
                     below_045=[int(i) for i in np.where(luma < 0.45)[0]],
                     jumps_gt_006=[[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma)) if abs(luma[i] - luma[i - 1]) > 0.06],
                     every_30=[round(float(x), 3) for x in luma[::30]])

    def pcm(p):
        r = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(p), "-vn", "-f", "s16le", "-"], capture_output=True)
        return np.frombuffer(r.stdout, np.int16)
    a1, a2 = pcm(OUT_MP4), pcm(AUDIO_SRC)
    res["K16"] = dict(samples=[int(len(a1)), int(len(a2))], identical=bool(len(a1) == len(a2) and np.array_equal(a1, a2)))
    res["beat"] = beat_check(seg)
    cj = json.loads((W / "cam.json").read_text(encoding="utf-8"))
    res["K10_K12"] = box_check(cj)
    clip = W / "clip.json"
    if clip.exists():
        res["K5_clip"] = {k: v for k, v in json.loads(clip.read_text(encoding="utf-8")).items() if k != "hits"}
    (W / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL check", json.dumps({k: (v if k != "K7" else {kk: vv for kk, vv in v.items() if kk != "every_30"}) for k, v in res.items()
                                     if k not in ("beat",)}, ensure_ascii=False, default=str)[:4000], flush=True)
    print("DRILL beat", json.dumps(dict(k2_ok=res["beat"]["k2_ok"], t7b={k: v for k, v in res["beat"]["t7b"].items() if k != "per_beat"}), ensure_ascii=False), flush=True)
    return res


# 押韵字幕的三个框（20 号 2.2，1080p）和出处行（右对齐到 1856，上沿 886 下沿 928）
LYR_BOXES = [((700, 772, 1680, 842), (110, 373)), ((160, 848, 760, 918), (605, 868)), ((1050, 168, 1830, 238), (1043, 1306))]
SRC_BOX = ((700, 886, 1856, 928), (18, 1500))


def box_check(cj):
    """K10：关键物件外接框离字框 ≥ 20 px（各自可见期间）、不进 y > 940；K12：第 6–28 拍液团高 520–640 px；K9：芯片刻字高。"""
    def gap(a, b):
        dx = max(b[0] - a[2], a[0] - b[2], 0)
        dy = max(b[1] - a[3], a[1] - b[3], 0)
        return max(dx, dy) if (dx == 0 or dy == 0) else math.hypot(dx, dy)
    bad, low, heights, chip_h = [], [], [], []
    for fr in cj["frames"]:
        f = fr["f"]
        for nm in ("hero", "tail"):
            bb = fr.get(nm)
            if not bb:
                continue
            if nm == "tail" and fr.get("tail_pts"):                     # 尾巴是一根细管：按节点逐点量（外接框在甩飞时会把两头框成一大块）
                for box, (a, b) in LYR_BOXES + [SRC_BOX]:
                    if a <= f <= b and f < 1364:
                        g_ = min(gap([x - 12, y - 12, x + 12, y + 12], box) for x, y in fr["tail_pts"])
                        if g_ < 20:
                            bad.append((f, nm, box[:2], round(g_, 1)))
                if f < 1364 and max(y for _, y in fr["tail_pts"]) + 12 > 940:
                    low.append((f, nm, max(y for _, y in fr["tail_pts"])))
                continue
            if f < 1364 and bb[3] > 940 and bb[1] < 1080:
                low.append((f, nm, bb[3]))
            for box, (a, b) in LYR_BOXES + [SRC_BOX]:
                if a <= f <= b and f < 1364 and gap(bb, box) < 20:
                    bad.append((f, nm, box[:2], round(gap(bb, box), 1)))
        if 6 <= fr["beat"] <= 28 and fr.get("hero"):
            heights.append((f, fr["hero"][3] - fr["hero"][1]))
        if fr.get("chip_txt") and 20 <= f <= 57:
            chip_h.append(fr["chip_txt"][3] - fr["chip_txt"][1])
    hs = [h for _, h in heights]

    def runs(lst):
        out, cur = [], None
        for x in lst:
            f = x[0]
            if cur and f - cur[1] <= 2 and cur[2] == x[1]:
                cur[1] = f
            else:
                cur = [f, f, x[1]]
                out.append(cur)
        return out
    return dict(K10_text_gap_lt20=runs(bad)[:40], K10_below_940=runs(low)[:40],
                K12_hero_h=dict(min=min(hs) if hs else None, max=max(hs) if hs else None,
                                out_of_520_640=runs([(f, "h") for f, h in heights if not 520 <= h <= 640])[:30]),
                K9_chip_text_px=dict(min=min(chip_h) if chip_h else None, max=max(chip_h) if chip_h else None))


def boxes(seg):
    """渲前就能量：python shot_drill.py boxes W2 → 打印 K9/K10/K12。"""
    cj = json.loads((SD.work(seg) / "cam.json").read_text(encoding="utf-8"))
    r = box_check(cj)
    (SD.work(seg) / "boxes.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL boxes", json.dumps(r, ensure_ascii=False)[:3000], flush=True)


def sheet(seg, step="6"):
    return D5.sheet(seg, step, out_mp4=OUT_MP4, prefix="03_W2_重做")
