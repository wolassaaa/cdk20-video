"""HKBU SCIE1007 课程作业的科普视频：三维钻取 3-03 —— 三把销子锁（设计：深化/18_剩余画面设计定稿.md 的 2.2，11-22）。

"Scientists call the lock the target, and the key a candidate molecule. A good key fits its own lock tightly,
and opens no one else's. That's called selectivity."

一镜到底（引擎 shot_drill.py，帧号全部来自 映射/keys/3-03.json）：
  K0  段首 T3：金色锁孔环（1 号锁的前口环）占满画面，和 3-02 末帧红环同圆心同半径（读 drill/3-02/handoff.json）。
  退  "Scientists" 镜头从锁孔退到 1 号锁的 3/4 角（K1）；"lock" 剖切刀从锁顶往下扫，露出五根弹子销。
  牌  "target" 上面料杆的牌子 target 弹下；"key" 金钥匙从左边料杆的浇口弹下、转成 3/4 角露出齿；
      "candidate" 钥匙下方的牌子 candidate molecule 弹下。
  插  "fits" 钥匙滑进 1 号锁，销被齿一根根顶起；"own" 推到底，五根销齐到分界线；"tightly" 锁芯带钥匙转 32°，锁梁弹起。
  试  "opens" 镜头右移，2、3 号锁入画；钥匙回正抽出；"no" 插进 2 号锁，销卡在分界线上，抖两下转不动，被推出；
      "else's" 插进 3 号锁，同样转不动，退出，停在 3 号锁旁。
  收  "That's" 后拉到 K2（三把锁一排，1 号锁梁开着）；"selectivity" 长牌弹下。最后 8 帧向右甩镜（T2）接 3-04。
零件：kit_deep_r3.h06_pin_lock（cut=True，1 号 own，2、3 号 other_a、other_b），kit_deep.h02_key("048")（编号字藏掉），
kit_parts.p16_plate 三块刻字牌。三把锁挂在同一根横料杆上（料杆从锁两侧的浇口接进去），牌子挂在上面一根料杆上，料架两头有立柱落到板面。
不穿模：钥匙只沿锁孔轴进出，横移时钥匙尖在锁面前 ≥ 2 mm；2、3 号锁里只让锁芯连钥匙抖 ±2°（≤ 3°）；clip 逐帧 BVH 查钥匙对三把锁、牌子对料架。
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

SEG = "3-03"
BOARD = SD.WORK_ROOT / "kit" / "board_final.blend"
LS = 2.0                                     # 锁的放大（20 mm 宽 → 40 mm）。下面"锁单位"= 锁自己的毫米（未放大）
SPACING = 30.0                               # 锁间距（锁单位）= 60 mm（18 的 2.2）
PRESETS = ["own", "other_a", "other_b"]      # _LOCK_PRESETS 里不是 own 的按字典序前两个
LOCK_FROM_CELL = (-120.0, 0.0, 40.0)         # 1 号锁中心：p23_cell 那一格左边 120 mm、离板面 40 mm（= 3-02 那把锁的位置）
ROD_Y, ROD_Z, TOP_Z = 3.0, 0.0, 28.0         # 横料杆（锁单位，1 号锁局部）：主杆在浇口高度，上杆挂牌子
ROD_X0, ROD_X1 = -62.0, 92.0                 # 料架左右两头（立柱）
ROD_R = 2.2                                  # 料杆半径（世界毫米）
# target 牌宽 11-22 从 30 放到 33：30 时 K1 屏上宽 293–303 px，卡在 18 的 2.2 的 ≥ 300 线上
PLATES = dict(target=dict(label="target", w=33.0, s=0.8), cand=dict(label="candidate molecule", w=52.0, s=0.6),
              sel=dict(label="selectivity", w=44.0, s=1.2))
KEY_S = 1.3                                  # 钥匙相对锁的缩放（销距 1.3 mm）
KEY_YAW = -65.0                              # 钥匙亮出时侧转（齿形朝镜头）
PIN_DROP = 0.5
HOVER = dict(w=16.0, du=-1.0, dv=-17.0, yaw=KEY_YAW)        # 钥匙弹下后浮着的位置（1 号锁的钥匙坐标）；11-23 从 -26 挪到 -17：-26 时 f222–354 钥匙半截出画
REST3 = dict(w=14.0, du=-1.5, dv=2 * SPACING + 17.0, yaw=-40.0)   # 试完 3 号锁后停在它右边
RING_R_MM = 4.91                             # 前口金环外半径（锁单位，kit_deep_r3 front_bevel_ring）
RING_C = (0.0, -7.89, -0.55)                 # 前口金环中心（锁单位）
HANDOFF_DEFAULT = dict(ring_cx=960.0, ring_cy=540.0, ring_r=700.0)
FSTOP = dict(k0=5.0, k1=8.0, wide=9.0)
OUT_DIR = SD.ROOT / "导演检查_20261123"
OUT_MP4 = OUT_DIR / "16_钻取_3-03.mp4"
SRC_TOY = "Illustration (our toy model)"
SRC_SIZE, SRC_XY, PLATE_BG = 30, (96, 1046), ((14, 16, 24), 0.66, 12, 8)


# ================================================================ 时间表
def make_keys():
    """正式表（events/3-03.json，tool=blender，Hydrogen 照 18 填）到了就用 映射/keys/3-03.json；没到用施工位的草稿（drill/3-03/keys_draft.json）。"""
    p = SD.MAPD / "keys" / f"{SEG}.json"
    K = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if K.get("tool") != "blender":
        K = json.loads((SD.WORK_ROOT / "drill" / SEG / "keys_draft.json").read_text(encoding="utf-8"))
        print("DRILL 用草稿 keys（正式事件表还没到）", flush=True)
    return K


class T:
    def __init__(self, EV):
        g = lambda i, k="f_land": EV[i][k]  # noqa: E731
        self.cam_out = (g("cam_out", "f_start"), g("cam_out"))
        self.cut = (g("cut_open", "f_start"), g("cut_open"), g("cut_open", "f_end"))
        self.pt = (g("plate_target", "f_start"), g("plate_target"), g("plate_target", "f_end"))
        self.key_up = (g("key_up", "f_start"), g("key_up"), g("key_up", "f_end"))
        self.pc = (g("plate_cand", "f_start"), g("plate_cand"), g("plate_cand", "f_end"))
        self.key_in = (g("key_in", "f_start"), g("key_in"), g("key_in", "f_end"))
        self.pins = (g("pins", "f_start"), g("pins"), g("pins", "f_end"))
        self.turn = (g("turn", "f_start"), g("turn"), g("turn", "f_end"))
        self.row = (g("cam_row", "f_start"), g("cam_row"), g("cam_row", "f_end"))
        self.try2 = (g("try2", "f_start"), g("try2"), g("try2", "f_end"))
        self.try3 = (g("try3", "f_start"), g("try3"), g("try3", "f_end"))
        self.wide = (g("cam_wide", "f_start"), g("cam_wide"), g("cam_wide", "f_end"))
        self.ps = (g("plate_sel", "f_start"), g("plate_sel"), g("plate_sel", "f_end"))
        self.whip = (g("whip", "f_start"), g("whip"))


# ================================================================ 钥匙的动作（纯函数：帧 → 钥匙坐标参数）
def key_params(t, f):
    """返回 dict(mode, w, du, dv, yaw, deg, lock)：
    mode = runner（还挂在料杆上）/ pop（弹下途中，u = 进度）/ free（钥匙坐标）；w 离插到底的距离（锁单位，往外为正），
    du 上下、dv 左右（含锁的间距：2 号锁 dv = 30），yaw 绕钥匙尖的侧转，deg 锁芯转角（lock 是哪把锁的锁芯）。"""
    k0, k1, k2 = t.key_up
    if f < k1:
        return dict(mode="runner", pre=clamp((f - k0) / max(1, k1 - k0)) if f >= k0 else 0.0)
    if f < k1 + 20:
        return dict(mode="pop", u=(f - k1) / 20.0)
    bob = 0.25 * math.sin(2 * math.pi * f / 110.0)
    H = dict(HOVER)
    a0, a1, a2 = t.key_in
    al = a0 + 14                                                     # 对准锁孔
    if f < a0:
        return dict(mode="free", w=H["w"], du=H["du"] + bob, dv=H["dv"], yaw=H["yaw"], deg=0.0, lock=0)
    if f < al:
        e = smoother((f - a0) / (al - a0))
        return dict(mode="free", w=lerp(H["w"], 7.5, e), du=lerp(H["du"] + bob, 0.0, e), dv=lerp(H["dv"], 0.0, e), yaw=lerp(H["yaw"], 0.0, e), deg=0.0, lock=0)
    p0, p1, p2 = t.pins
    if f < a1:                                                       # 滑进去一大半（销被齿一根根顶起）
        return dict(mode="free", w=lerp(7.5, 2.0, ease_out((f - al) / (a1 - al), 2.2)), du=0.0, dv=0.0, yaw=0.0, deg=0.0, lock=0)
    if f < p0:
        return dict(mode="free", w=2.0 + 0.12 * math.sin(math.pi * (f - a1) / 9.0) * (1 - ramp(f, a1, p0)), du=0.0, dv=0.0, yaw=0.0, deg=0.0, lock=0)
    if f < p1:                                                       # own：推到底，五根销齐到分界线
        return dict(mode="free", w=2.0 * (1 - ease_out((f - p0) / (p1 - p0), 2.4)), du=0.0, dv=0.0, yaw=0.0, deg=0.0, lock=0)
    t0, t1, t2 = t.turn
    r0 = t.row[0]
    if f < r0:
        if f < t0:
            deg = 0.0
        elif f < t1:
            deg = 32.0 * ease_out((f - t0) / (t1 - t0), 3.0)
        else:
            deg = 32.0 + settle(f, t1, 1.2, n=1.5, dur=t2 - t1)
        return dict(mode="free", w=0.0, du=0.0, dv=0.0, yaw=0.0, deg=deg, lock=0)
    b1 = r0 + 6                                                      # 先回正 6 帧
    if f < b1:
        return dict(mode="free", w=0.0, du=0.0, dv=0.0, yaw=0.0, deg=32.0 * (1 - smoother((f - r0) / 6.0)), lock=0)
    wo = b1 + 14                                                     # 再抽出
    if f < wo:
        return dict(mode="free", w=14.0 * smoother((f - b1) / 14.0), du=0.0, dv=0.0, yaw=0.0, deg=0.0, lock=0)
    s0, s1, s2 = t.try2
    if f < s0:                                                       # 在锁面前横移到 2 号锁
        e = smoother((f - wo) / max(1, s0 - wo))
        return dict(mode="free", w=14.0, du=1.2 * math.sin(math.pi * e), dv=SPACING * e, yaw=0.0, deg=0.0, lock=1)
    if f < s1:                                                       # 插进 2 号锁
        return dict(mode="free", w=14.0 * (1 - ease_out((f - s0) / (s1 - s0), 2.2)), du=0.0, dv=SPACING, yaw=0.0, deg=0.0, lock=1)
    j1 = s1 + 10                                                     # 抖两下（±2°），转不动
    if f < j1:
        return dict(mode="free", w=0.0, du=0.0, dv=SPACING, yaw=0.0, deg=2.0 * math.sin(2 * math.pi * 2 * (f - s1) / 10.0), lock=1)
    q0, q1, q2 = t.try3
    po = j1 + 8                                                      # 被弹簧推出
    tr0 = po - 2
    ins = q1 - 5
    if f < tr0:
        return dict(mode="free", w=10.0 * ease_out((f - j1) / 8.0, 2.6), du=0.0, dv=SPACING, yaw=0.0, deg=0.0, lock=1)
    if f < ins:                                                      # 横移到 3 号锁（钥匙尖已在锁面外）
        e = smoother((f - tr0) / max(1, ins - tr0))
        w = 10.0 * ease_out((f - j1) / 8.0, 2.6) if f < po else 10.0
        return dict(mode="free", w=w, du=0.9 * math.sin(math.pi * e), dv=SPACING * (1 + e), yaw=0.0, deg=0.0, lock=2)
    if f < q1:                                                       # 插进 3 号锁
        return dict(mode="free", w=10.0 * (1 - ease_out((f - ins) / (q1 - ins), 2.0)), du=0.0, dv=2 * SPACING, yaw=0.0, deg=0.0, lock=2)
    j3 = q1 + 12
    if f < j3:
        return dict(mode="free", w=0.0, du=0.0, dv=2 * SPACING, yaw=0.0, deg=2.0 * math.sin(2 * math.pi * 2 * (f - q1) / 12.0), lock=2)
    o3 = j3 + 9
    if f < o3:
        return dict(mode="free", w=12.0 * ease_out((f - j3) / 9.0, 2.6), du=0.0, dv=2 * SPACING, yaw=0.0, deg=0.0, lock=2)
    R = REST3
    e = smoother((f - o3) / max(1, q2 - o3))
    b = 0.25 * math.sin(2 * math.pi * f / 110.0) * ramp(f, q2, q2 + 30)
    return dict(mode="free", w=lerp(12.0, R["w"], e), du=lerp(0.0, R["du"], e) + b, dv=lerp(2 * SPACING, R["dv"], e), yaw=lerp(0.0, R["yaw"], e), deg=0.0, lock=2)


def plate_state(f, ev, drop, sway=2.0):
    """牌子：ev = (起, 落, 止)。起 → 落 浇口绷（往上拉一点），落 那一帧断开，往下掉 drop（锁单位）带回弹，摆 sway° 衰减停稳，之后慢慢浮。
    返回 (下降量, 摆角°)。"""
    a, b, c = ev
    if f < a:
        return 0.0, 0.0
    if f < b:
        return -0.15 * math.sin(math.pi * (f - a) / max(1, b - a)), 0.0
    u = (f - b) / max(14.0, c - b if c - b < 40 else 30.0)
    d = drop * spring(u, zeta=0.5, freq=1.1)
    ang = sway * math.sin(2 * math.pi * (f - b) / 22.0) * math.exp(-(f - b) / 18.0)
    fl = 0.18 * math.sin(2 * math.pi * (f - b) / 150.0) * ramp(f, b + 20, b + 50)
    return d + fl, ang


# ================================================================ 搭场景
def build(seg, samples=16):
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    import kit_parts as KP
    import kit_deep as D
    import kit_deep_r3 as M3
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    sc = SD.open_board(BOARD, NF, samples)
    board = bpy.data.objects["board"]
    zb = board.location.z
    cell23, _ = SD.find_cell(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p23_cell"))
    c23 = cell23.matrix_world.translation
    L1 = Vector((c23.x + LOCK_FROM_CELL[0] * MM, c23.y + LOCK_FROM_CELL[1] * MM, zb + LOCK_FROM_CELL[2] * MM))
    print("DRILL cell", cell23.name, [round(v / MM, 1) for v in c23], "zb", round(zb / MM, 1), flush=True)
    Kt = KP.Kit()

    # ---- 三把锁
    locks, rigs, cutters = [], [], []
    c0 = None
    for i, pre in enumerate(PRESETS):
        lk = M3.h06_pin_lock(Kt, preset=pre, cut=True)
        D.rest(lk)
        lk["drill_role"] = f"lock_{i + 1}"
        bpy.context.view_layer.update()
        if c0 is None:
            pts = [m.matrix_world @ Vector(c) for m in [lk] + list(lk.children_recursive)
                   if m.type in ("MESH", "CURVE", "FONT") and not m.hide_render for c in m.bound_box]
            lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
            hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
            c0 = (lo + hi) / 2
            bounds_mm = ([round(v / MM, 2) for v in lo], [round(v / MM, 2) for v in hi])
            print("DRILL lock bounds mm", bounds_mm, flush=True)
        locks.append(lk)
        rigs.append(D.rig(lk))
    O1 = L1 - Vector((c0.x, 0.0, c0.z)) * LS                         # 锁局部原点（x、z 对中心，y 不动：前口在 y = −8）

    def MS(i):
        return Matrix.Translation(O1 + Vector((SPACING * i * MM * LS, 0, 0))) @ Matrix.Diagonal((LS, LS, LS, 1))

    def LW(p, i=0):
        """锁单位（第 i 把锁的局部毫米）→ 世界（米）。"""
        return MS(i) @ (Vector(p) * MM)
    for i, lk in enumerate(locks):
        lk.matrix_world = MS(i)
    bpy.context.view_layer.update()

    # 剖切刀（四分之一象限的盒子）：1 号锁的刀从锁顶往下扫开；2、3 号一开始就剖着
    for i, lk in enumerate(locks):
        cs = []
        for o in [lk] + list(lk.children_recursive):
            for md in getattr(o, "modifiers", []):
                if md.type == "BOOLEAN" and md.object is not None:
                    cu = md.object
                    dims = [v / MM for v in cu.dimensions]
                    if dims[0] > 15 and dims[2] > 15 and cu not in cs:      # 象限盒：x、z 都约 20 mm
                        cs.append(cu)
        cutters.append(cs)
    print("DRILL cutters", [len(c) for c in cutters], flush=True)
    a, b, c = t.cut
    up = Vector((0, 0, 22.0 * MM * LS))
    for cu in cutters[0]:
        W0 = cu.matrix_world.copy()
        for f in [0, a] + list(range(a + 1, c + 1)) + [c + 1]:
            u = smoother((f - a) / max(1, c - a)) if f >= a else 0.0
            cu.matrix_world = Matrix.Translation(up * (1 - u)) @ W0
            cu.keyframe_insert("location", frame=f)
    bpy.context.view_layer.update()

    # ---- 料架：主杆（浇口高度，锁两侧接进去）、上杆（挂牌子）、两头立柱落到板面
    frame = bpy.data.objects.new("drill_rack", None)
    sc.collection.objects.link(frame)
    frame["drill_role"] = "rack"
    blue = Kt.cat("blue")

    def rod(name, pts_lock):
        return KP.tube_w(name, [tuple(v / MM for v in LW(p)) for p in pts_lock], ROD_R, blue, frame)
    z_board = (zb - O1.z) / (MM * LS)                                # 板面在锁单位里的高度
    rods = [rod("rack_main_L", [(ROD_X0, ROD_Y, ROD_Z), (-14.0, ROD_Y, ROD_Z)]),
            rod("rack_main_12", [(14.0, ROD_Y, ROD_Z), (SPACING - 14.0, ROD_Y, ROD_Z)]),
            rod("rack_main_23", [(SPACING + 14.0, ROD_Y, ROD_Z), (2 * SPACING - 14.0, ROD_Y, ROD_Z)]),
            rod("rack_main_R", [(2 * SPACING + 14.0, ROD_Y, ROD_Z), (ROD_X1, ROD_Y, ROD_Z)]),
            rod("rack_top", [(ROD_X0, ROD_Y, ROD_Z), (ROD_X0, ROD_Y, TOP_Z), (ROD_X1, ROD_Y, TOP_Z), (ROD_X1, ROD_Y, ROD_Z)]),
            rod("rack_post_L", [(ROD_X0, ROD_Y, ROD_Z), (ROD_X0, ROD_Y, z_board + 0.5)]),
            rod("rack_post_R", [(ROD_X1, ROD_Y, ROD_Z), (ROD_X1, ROD_Y, z_board + 0.5)])]
    for i in range(3):                                               # 锁两侧的浇口（料杆 → 锁身）
        for sgn in (-1, 1):
            KP.gate_geo(f"rack_lockgate_{i}_{'L' if sgn < 0 else 'R'}", LW((sgn * 14.0, ROD_Y, ROD_Z), i), LW((sgn * 10.05, ROD_Y, ROD_Z), i), blue, frame)
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)

    def gate(name, a_w, b_w):
        before = set(bpy.data.objects.keys())
        KP.gate_geo(name, a_w, b_w, blue, frame)
        new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
        cone = next(o for o in new if not o.name.endswith("_spur"))
        return dict(cone=cone, spur=[o for o in new if o.name.endswith("_spur")], a=Vector(a_w), tip=Vector(b_w), dir=(Vector(b_w) - Vector(a_w)).normalized())

    # ---- 牌子：躺着造（字面 +Z），转成字面朝镜头（−Y）挂起来
    Rx = Matrix.Rotation(math.radians(90), 4, "X")
    plates, plate_mats, plate_track = {}, {}, {}
    hang = dict(target=dict(x=0.0, z=TOP_Z - 6.0 + 0.0, top=True, drop=1.6, ev=t.pt),
                sel=dict(x=SPACING, z=TOP_Z - 7.3, top=True, drop=2.0, ev=t.ps),
                cand=dict(x=-50.0, z=ROD_Z - 5.6, top=True, drop=0.0, ev=t.pc))
    for name, spec in PLATES.items():
        pl = KP.p16_plate(Kt, label=spec["label"], w=spec["w"], italic=False)
        pl["drill_role"] = "plate_" + name
        plates[name] = pl
    gates_all = []
    for name, pl in plates.items():
        spec, h = PLATES[name], hang[name]
        s = spec["s"]
        hh = 7.0 * s / LS                                            # 牌子半高（锁单位）
        P0 = LW((h["x"], ROD_Y, h["z"]))
        M0 = Matrix.Translation(P0) @ Rx @ Matrix.Diagonal((s, s, s, 1))
        pl.matrix_world = M0
        bpy.context.view_layer.update()
        # 浇口：杆底 → 牌子上沿（两处）
        z_rod = (TOP_Z if name != "cand" else ROD_Z) - ROD_R / LS / 1.0 * 0.5
        gs = []
        for k, dx in enumerate((-spec["w"] * s / LS / 4, spec["w"] * s / LS / 4)):
            gs.append(gate(f"rack_pgate_{name}_{k}", LW((h["x"] + dx, ROD_Y, z_rod)), LW((h["x"] + dx, ROD_Y, h["z"] + hh - 0.03))))
        e0, e1, e2 = h["ev"]
        SD.break_gates(gs, e0, e1, scar)
        gates_all += gs
        plate_mats[name] = (P0, s, h, hh)
    # 候选牌：弹下以后飘到钥匙下方（浮着的钥匙在 HOVER）
    CAND_FLOAT = (-21.0, -12.0, -10.5)       # 跟着钥匙右移 6（11-23；钥匙后来又右移 3，牌子不再跟，离 1 号锁左面留 3）

    for f in range(NF):
        for name, pl in plates.items():
            P0, s, h, hh = plate_mats[name]
            e0, e1, e2 = h["ev"]
            if name == "cand":
                if f < e1:
                    d, ang = plate_state(f, h["ev"], 0.0)
                    p = P0 + Vector((0, 0, -d * MM * LS))
                else:
                    u = clamp((f - e1) / 26.0)
                    k = spring(u * 1.2, zeta=0.55, freq=0.9)
                    tgt = LW(CAND_FLOAT)
                    mid = P0.lerp(tgt, 0.5) + Vector((0, 0, -3.0 * MM * LS))
                    p = P0.lerp(mid, min(1.0, k)).lerp(mid.lerp(tgt, min(1.0, k)), min(1.0, k)) if k <= 1 else tgt + (tgt - mid) * (k - 1) * 0.6
                    p = p + Vector((0, 0, 0.18 * MM * LS * math.sin(2 * math.pi * (f - e1) / 150.0) * ramp(f, e1 + 30, e1 + 60)))
                    ang = 3.0 * math.sin(2 * math.pi * (f - e1) / 24.0) * math.exp(-(f - e1) / 20.0)
            else:
                d, ang = plate_state(f, h["ev"], h["drop"])
                p = P0 + Vector((0, 0, -d * MM * LS))
            M = Matrix.Translation(p) @ Matrix.Rotation(math.radians(ang), 4, "Y") @ Rx
            SD.key_xform(pl, f, loc=p, quat=M.to_quaternion(), scale=(s, s, s))
            plate_track.setdefault(name, []).append(tuple(p))

    # ---- 钥匙
    key = D.h02_key(Kt, which="048", scale=KEY_S)
    key["drill_role"] = "key"
    for o in key.children_recursive:                                 # 不刻编号：藏掉 048 字和下划线
        if o.type == "FONT":
            SD.hide_tree(o)
        elif o.type == "MESH":
            bb = [Vector(v) for v in o.bound_box]
            cc = sum(bb, Vector()) / 8 / MM
            if abs(cc.x + 3.5) < 0.3 and abs(cc.y + 3.54) < 0.3 and cc.z > 0.6:
                SD.hide_tree(o)
    Wv, Uv, Vv = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
    origin = Vector((0, -1.5, -0.55))
    rot3 = Matrix((-Wv, -Uv, -Vv)).transposed()
    off = float(key["insertion_offset_u_mm"])
    Kin = Matrix.Translation(((origin + off * Uv) - rot3 @ Vector((6.5 * KEY_S, 0, 0))) * MM) @ rot3.to_4x4() @ Matrix.Diagonal((KEY_S, KEY_S, KEY_S, 1))
    tip_local = Vector((6.5 * MM, 0, 0))

    def key_local(w, du, dv, yaw, deg, lock):
        """1 号锁局部（米，未放大）里钥匙的矩阵。"""
        pv = (origin + Vv * SPACING * lock) * MM
        Rp = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(deg), 4, Wv) @ Matrix.Translation(-pv)
        Mk = Rp @ Matrix.Translation((w * Wv + du * Uv + dv * Vv) * MM) @ Kin
        tip = Mk @ tip_local
        return Matrix.Translation(tip) @ Matrix.Rotation(math.radians(yaw), 4, Uv) @ Matrix.Translation(-tip) @ Mk

    # 挂在左边主杆下面：钥匙杆朝 +x（朝 1 号锁），齿缘朝下，刻面朝镜头
    Rr = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()        # 钥匙 X→+x，Y→+z，Z→−y
    KEY_HANG = (-30.0, ROD_Y, ROD_Z - 9.0)
    M_run = Matrix.Translation(Vector(KEY_HANG) * MM) @ Rr @ Matrix.Diagonal((KEY_S, KEY_S, KEY_S, 1))
    bow_top = Vector(KEY_HANG) + Vector((-3.5 * KEY_S, 0, 4.0 * KEY_S))
    kg = gate("rack_keygate", LW((bow_top.x, ROD_Y, ROD_Z - ROD_R / LS * 0.5)), LW((bow_top.x, ROD_Y, bow_top.z - 0.03)))
    SD.break_gates([kg], t.key_up[0], t.key_up[1], scar)
    gates_all.append(kg)
    M_hover = key_local(HOVER["w"], HOVER["du"], HOVER["dv"], HOVER["yaw"], 0.0, 0)

    def dec(M):
        l, q, s = M.decompose()
        return l, q, s
    S1 = Matrix.Diagonal((LS, LS, LS, 1))
    key_tr, key_state = [], []
    for f in range(NF):
        kp = key_params(t, f)
        if kp["mode"] == "runner":
            Ml = Matrix.Translation(Vector((0, 0, 0.25 * kp["pre"] * math.sin(math.pi * kp["pre"])) ) * MM) @ M_run
        elif kp["mode"] == "pop":                                    # 弹下：先往下、往前离开料杆，再转成 3/4 角飞到浮着的位置
            u = kp["u"]
            k = spring(u, zeta=0.6, freq=0.95)
            l0, q0, s0 = dec(M_run)
            l1, q1, s1 = dec(M_hover)
            mid = l0.lerp(l1, 0.35) + Vector((0, -4.0, -3.0)) * MM
            lp = l0.lerp(mid, min(1.0, k)).lerp(mid.lerp(l1, min(1.0, k)), min(1.0, k)) if k <= 1 else l1 + (l1 - mid).normalized() * (k - 1) * 2.0 * MM
            qr = q0.slerp(q1, clamp(smoother(u * 1.3)))
            Ml = Matrix.LocRotScale(lp, qr, s1)
        else:
            Ml = key_local(kp["w"], kp["du"], kp["dv"], kp["yaw"], kp["deg"], kp["lock"])
        Mw = Matrix.Translation(O1) @ S1 @ Ml
        l, q, s = Mw.decompose()
        SD.key_xform(key, f, loc=l, quat=q, scale=s)
        key_tr.append(tuple(Mw @ Vector((0.0, 0, 0))))
        key_state.append(kp)

    # ---- 销、锁芯、锁梁（三把锁各自）
    prof = list(key["tooth_profile_modelled"])
    chain = [(6.5, -1.3)]
    for i, h in enumerate(prof):
        cc = 6.0 - i
        chain += [(cc + 0.28, -1.3 + h), (cc - 0.28, -1.3 + h)]
    chain += [(1.5, -1.3)]
    chain = sorted(chain)

    def surf(x):
        if x > 6.5:
            return off + 1.3 * 1.3 - (x - 6.5) / 0.5 * 3.0 if x < 7.0 else -99
        if x < 1.5:
            return -99
        for (xa, ya), (xb, yb) in zip(chain, chain[1:]):
            if xa <= x <= xb:
                tt = 0 if xb == xa else (x - xa) / (xb - xa)
                return off + (-(ya + (yb - ya) * tt)) * 1.3
        return -99

    def foot(i, w):
        aa = (0.5 + i) * 1.3
        x = 6.5 - (aa - w) / 1.3
        return max(surf(x + dx) for dx in (-0.45, -0.3, -0.15, 0, 0.15, 0.3, 0.45))
    rest_u = [foot(i, 0.0) for i in range(5)]
    max_rot_23 = 0.0
    pin_lifts = {0: [], 1: [], 2: []}
    for f in range(NF):
        kp = key_state[f]
        for li in range(3):
            j = rigs[li]
            inside = kp["mode"] == "free" and abs(kp["dv"] - SPACING * li) < 1e-6 and abs(kp["du"]) < 1e-6 and kp["w"] <= 7.0
            lifts = []
            for i in range(5):
                lift = max(-PIN_DROP, foot(i, kp["w"]) - rest_u[i]) if inside else -PIN_DROP
                j[f"pin_{i}"].location.z = lift * MM
                j[f"pin_{i}"].keyframe_insert("location", index=2, frame=f)
                lifts.append(round(lift, 3))
            pin_lifts[li].append(lifts)
            deg = kp.get("deg", 0.0) if kp["mode"] == "free" and kp.get("lock") == li else 0.0
            if li > 0:
                max_rot_23 = max(max_rot_23, abs(deg))
            j["plug"].rotation_euler.x = math.radians(deg)
            j["plug"].keyframe_insert("rotation_euler", index=0, frame=f)
            sh = 0.0
            if li == 0 and f >= t.turn[1] - 2:
                x = clamp((f - (t.turn[1] - 2)) / 10.0)
                sh = 3.6 * (1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2)
            j["shackle"].location.z = sh * MM
            j["shackle"].keyframe_insert("location", index=2, frame=f)

    # ---- 镜头（1 号锁空间：tgt 锁单位，az=0 看 +x 面、−90 正对锁前口；dist 锁单位）
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.sensor_width = 36.0
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0
    hof = SD.WORK_ROOT / "drill" / "3-02" / "handoff.json"
    H0 = dict(HANDOFF_DEFAULT)
    if hof.exists():
        try:
            hj = json.loads(hof.read_text(encoding="utf-8"))
            if hj.get("by") == "3-02":                                # 3-02 做完了：对它的末帧红环
                H0 = dict(ring_cx=hj["ring_cx"], ring_cy=hj["ring_cy"], ring_r=hj["ring_r"])
        except (ValueError, KeyError):
            pass
    lens0 = 50.0
    fpx0 = lens0 / 36.0 * SD.OUT_W
    d0 = fpx0 * RING_R_MM / H0["ring_r"]                             # 锁单位
    # 环心不在画面中心时：把目标点从环心沿画面方向挪（正对时 az=-90，画面右 = +x，画面下 = −z）
    sx = (H0["ring_cx"] - SD.OUT_W / 2) / fpx0 * d0
    sy = (H0["ring_cy"] - SD.OUT_H / 2) / fpx0 * d0
    k0_tgt = (RING_C[0] - sx, RING_C[1], RING_C[2] + sy)
    keys = [
        dict(f=0, space="lock", tgt=k0_tgt, az=-90.0, el=0.0, dist=d0, lens=lens0),
        dict(f=t.cam_out[1], space="lock", tgt=(-9.0, 0.0, 5.0), az=-62.0, el=14.0, dist=112.0, lens=50, ease="out"),
        dict(f=t.key_in[0] - 10, space="lock", tgt=(-8.0, 0.0, 4.5), az=-60.0, el=14.0, dist=106.0, lens=50),
        dict(f=t.pins[1], space="lock", tgt=(-4.0, -3.0, 2.5), az=-56.0, el=15.0, dist=84.0, lens=50),
        dict(f=t.row[0], space="lock", tgt=(-3.0, -3.0, 3.0), az=-57.0, el=15.0, dist=88.0, lens=50),
        dict(f=t.row[1], space="lock", tgt=(SPACING + 6.0, -2.0, 4.0), az=-70.0, el=13.0, dist=118.0, lens=50),
        dict(f=t.try3[1], space="lock", tgt=(SPACING + 16.0, -2.0, 4.0), az=-71.0, el=13.0, dist=114.0, lens=50),
        dict(f=t.wide[0], space="lock", tgt=(SPACING + 14.0, -1.0, 5.0), az=-72.0, el=13.0, dist=118.0, lens=50),
        dict(f=t.wide[1], space="lock", tgt=(SPACING, 0.0, 9.0), az=-78.0, el=12.0, dist=146.0, lens=50),
        dict(f=t.wide[2], space="lock", tgt=(SPACING, 0.0, 9.0), az=-78.0, el=12.0, dist=150.0, lens=50, ease="linear"),
        dict(f=NF - 1, space="lock", tgt=(SPACING, 0.0, 9.0), az=-78.0, el=12.0, dist=152.0, lens=50, ease="linear"),
    ]
    rigc = SD.CamRig(keys, lambda f: Matrix.Translation(O1), MM * LS, spaces={"lock": (lambda f: Matrix.Translation(O1), MM * LS)})
    rigc.shake(t.turn[1], 0.22, 6)
    rigc.shake(t.try2[1], 0.08, 4)
    rigc.shake(t.try3[1], 0.08, 4)

    def drift(f, eye, tgt):
        d = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        upv = right.cross(fwd)
        k = ramp(f, 30, 70)                                          # 段首对位（T3）时不漂
        o = (right * 0.008 * math.sin(f / 97.0) + upv * 0.006 * (math.cos(f / 131.0) - 1.0)) * d * k
        return o, o * 0.6
    recs = rigc.bake(cam, NF, drift=drift)
    for f in range(0, 40):                                           # 段首去掉手持感（第 0 帧金环要和 3-02 末帧对上，误差 ≤ 4 px）
        eye, tgt, lens, q = recs[f]
        e2, t2, l2, _r = rigc.at(f)
        q0 = (t2 - e2).normalized().to_track_quat("-Z", "Y")
        q2 = q0.slerp(q, ramp(f, 0, 40))
        cam.rotation_quaternion = q2
        cam.keyframe_insert("rotation_quaternion", frame=f)
        recs[f] = (eye, tgt, lens, q2)
    w0, w1 = t.whip
    for f in range(w0, NF):                                          # 甩镜（T2）：向右越甩越快
        u = (f - w0) / max(1, (w1 - w0))
        yaw = math.radians(-78.0) * ease_in(u, 2.6)
        eye, tgt, lens, q = recs[f]
        q2 = Quaternion((0, 0, 1), yaw) @ q
        cam.rotation_quaternion = q2
        cam.keyframe_insert("rotation_quaternion", frame=f)
        recs[f] = (eye, tgt, lens, q2)

    # ---- 灯：大板那套（以三把锁中间为中心）+ 前面一盏柔光补锁面
    mid = LW((SPACING, 0, 4.0))
    KP.lights(mid.x, mid.y, 1.0)
    fl_d = bpy.data.lights.new("drill_front_fill", "AREA")
    fl_d.shape = "RECTANGLE"; fl_d.size, fl_d.size_y = 0.30, 0.18
    fl_d.color = (1, .98, .95)
    fl_d.energy = 6.0
    fo = bpy.data.objects.new("drill_front_fill", fl_d)
    sc.collection.objects.link(fo)
    fo.location = mid + Vector((0.05, -0.45, 0.12))
    fo.rotation_euler = (mid - fo.location).to_track_quat("-Z", "Y").to_euler()

    # ---- 焦点和光圈
    def ring_w(f):
        return LW(RING_C)

    def lock_c(i):
        return lambda f: LW((0, -4.0, 2.0), i)

    def plate_c(name):
        return lambda f: Vector(plate_track[name][f])

    def key_c(f):
        return Vector(key_tr[f])
    focus_plan = [(0, ring_w), (t.cam_out[1] - 10, lock_c(0)), (t.pt[0] - 4, plate_c("target")), (t.pt[2] + 10, lock_c(0)),
                  (t.key_up[0], key_c), (t.pc[1] - 2, lambda f: key_c(f).lerp(Vector(plate_track["cand"][f]), 0.5)),
                  (t.key_in[0], lambda f: LW((0, -7.0, -0.5), 0)), (t.row[0] + 18, key_c), (t.try2[0] + 6, lambda f: LW((0, -7.0, -0.5), 1)),
                  (t.try3[0] + 12, lambda f: LW((0, -7.0, -0.5), 2)), (t.wide[0], lock_c(1))]

    def focus_at(f):
        p = focus_plan[0][1](f)
        for (fa, fn) in focus_plan[1:]:
            if f >= fa - 12:
                p = p.lerp(fn(f), smooth((f - fa + 12) / 24.0))
        return p
    phases = [(0, FSTOP["k0"]), (t.cam_out[1], FSTOP["k1"]), (t.row[0], FSTOP["wide"])]
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    fst, focus_d = [], []
    for f in range(NF):
        v = phases[0][1]
        for (fa, va), (fb, vb) in zip(phases, phases[1:] + [(10 ** 6, phases[-1][1])]):
            if fa <= f:
                v = va if f < fb - 12 else lerp(va, vb, smooth((f - fb + 12) / 24))
        fst.append(v)
        d.aperture_fstop = v
        d.keyframe_insert("aperture_fstop", frame=f)
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.focus_distance = max(0.003, (focus_at(f) - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        focus_d.append(d.focus_distance)

    SD.linear_all([cam, key, frame] + locks + list(plates.values()) + [o for lk in locks for o in lk.children_recursive]
                  + list(key.children_recursive) + [o for p in plates.values() for o in p.children_recursive]
                  + [g["cone"] for g in gates_all] + [o for g in gates_all for o in g["spur"]] + cutters[0]
                  + [o for o in bpy.data.objects if o.name.endswith("_stub") or o.name.endswith("_scar")])

    # ---- 机检数据：第 0 帧金环、K2 锁高、牌子字高、2/3 号锁转角
    def proj(f, p):
        return SD.project(recs[f], p)

    def ring_screen(f):
        cxy = proj(f, ring_w(f))
        rr = []
        for k in range(16):
            a_ = 2 * math.pi * k / 16
            pp = proj(f, LW((RING_C[0] + RING_R_MM * math.cos(a_), RING_C[1], RING_C[2] + RING_R_MM * math.sin(a_))))
            if pp and cxy:
                rr.append(math.hypot(pp[0] - cxy[0], pp[1] - cxy[1]))
        return (cxy[0], cxy[1], sum(rr) / len(rr)) if cxy and rr else None

    def screen_box(f, objs):
        sc.frame_set(f)
        pts = []
        for o in objs:
            for m in [o] + list(o.children_recursive):
                if m.type in ("MESH", "CURVE", "FONT") and not m.hide_render:
                    for c in m.bound_box:
                        pp = proj(f, m.matrix_world @ Vector(c))
                        if pp:
                            pts.append(pp)
        if not pts:
            return None
        return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]

    def text_px(f, pl):
        sc.frame_set(f)
        tx = [m for m in pl.children_recursive if m.type == "FONT"][0]
        dg = bpy.context.evaluated_depsgraph_get()
        me = tx.evaluated_get(dg).to_mesh()
        ys = []
        for v in me.vertices:
            pp = proj(f, tx.matrix_world @ v.co)
            if pp:
                ys.append(pp[1])
        tx.evaluated_get(dg).to_mesh_clear()
        return round(max(ys) - min(ys), 1) if ys else None
    r0 = ring_screen(0)
    acc = dict(handoff_target=H0, ring_f0=[round(x, 1) for x in r0] if r0 else None)
    if r0:
        acc["ring_err_px"] = round(math.hypot(r0[0] - H0["ring_cx"], r0[1] - H0["ring_cy"]), 2)
        acc["ring_r_err_px"] = round(abs(r0[2] - H0["ring_r"]), 2)
    fk2 = [t.wide[2], (t.ps[1] + t.ps[2]) // 2, t.whip[0] - 1]
    acc["K2_lock_height_pct"] = {}
    for f in fk2:
        hs = []
        for lk in locks:
            bx = screen_box(f, [lk])
            hs.append(round((bx[3] - bx[1]) / SD.OUT_H * 100, 1) if bx else None)
        acc["K2_lock_height_pct"][str(f)] = hs
    fK1 = [t.pt[2] + 20, t.pc[2], t.key_in[0] - 12]
    acc["plate_px"] = {}
    for name, frames_ in (("target", fK1 + fk2), ("cand", fK1), ("sel", fk2)):
        acc["plate_px"][name] = {str(f): dict(text_h=text_px(f, plates[name]), box=[round(v) for v in (screen_box(f, [plates[name]]) or [0, 0, 0, 0])]) for f in frames_}
    acc["key_rot_max_deg_lock23"] = round(max_rot_23, 2)
    acc["pin_lifts_at"] = {"pins_land(1号)": pin_lifts[0][t.pins[1] + 2], "try2(2号)": pin_lifts[1][t.try2[1] + 1], "try3(3号)": pin_lifts[2][t.try3[1] + 1]}
    sc.frame_set(0)
    camj = dict(seg=seg, nf=NF, frames=[dict(f=f, eye=list(recs[f][0]), q=list(recs[f][3]), lens=recs[f][2], fstop=fst[f], focus=focus_d[f],
                                             key=list(proj(f, Vector(key_tr[f])) or [0, 0, 0])) for f in range(NF)])
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    coc = []
    for f in range(0, NF, 30):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        Sd = focus_d[f]
        coc.append(dict(f=f, fstop=round(fst[f], 1), focus_mm=round(Sd / MM, 1),
                        coc_pm8=round(max(SD.coc_px(lens, fst[f], Sd, Sd + 8 * MM * LS), SD.coc_px(lens, fst[f], Sd, Sd - 8 * MM * LS)), 2),
                        coc_lock1=round(SD.coc_px(lens, fst[f], Sd, (LW((0, 0, 2), 0) - eye).dot(fwd)), 2),
                        coc_key=round(SD.coc_px(lens, fst[f], Sd, (Vector(key_tr[f]) - eye).dot(fwd)), 2)))
    acc["coc"] = coc
    acc["lock_scale"], acc["bounds_lock_mm"] = LS, bounds_mm
    (W / "build_check.json").write_text(json.dumps(acc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not (hof.exists() and json.loads(hof.read_text(encoding="utf-8")).get("by") == "3-02") and r0:
        hof.parent.mkdir(parents=True, exist_ok=True)
        hof.write_text(json.dumps(dict(ring_cx=round(r0[0], 1), ring_cy=round(r0[1], 1), ring_r=round(r0[2], 1), by="3-03",
                                       note="HKBU SCIE1007 课程作业的科普视频：3-02 还没做（11-22 夜），施工位 2 先按 3-03 第 0 帧金色锁孔环的实测圆写在这里。"
                                            "3-02 做的时候末帧红环对这个圆（T3 匹配形，误差 ≤ 4 px），做完把 by 改成 3-02，3-03 下次 build 会反过来对 3-02。"),
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL acc", json.dumps({k: v for k, v in acc.items() if k != "coc"}, ensure_ascii=False, default=str)[:3000], flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


# ================================================================ 穿模检查
def _role_roots():
    import bpy
    return {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}


def _meshes(root, skip_pins=False):
    out = []
    for o in [root] + list(root.children_recursive):
        nm = o.name.split(".")[0]
        if o.type not in ("MESH", "CURVE", "FONT") or nm.endswith("_cut") or o.hide_render:
            continue
        if skip_pins and ("lower_pin" in nm or "upper_pin" in nm or "spring" in nm):
            continue
        out.append(o)
    return out


def clip_plan(sc):
    """钥匙 vs 三把锁（下销、上销可以贴着钥匙，不算）、钥匙 vs 料架、牌子 vs 锁和料架和别的牌子。镜头离最近表面。"""
    import bpy
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = _role_roots()
    key = R["key"]
    locks = [R[f"lock_{i}"] for i in (1, 2, 3)]
    rack = R["rack"]
    k_m = _meshes(key)
    lock_m = [m for lk in locks for m in _meshes(lk, skip_pins=True)]
    rod_m = [o for o in rack.children if o.type in ("CURVE", "MESH") and o.name.startswith("rack_") and "gate" not in o.name]
    plates = {n: R["plate_" + n] for n in ("target", "cand", "sel")}
    p_m = {n: _meshes(p) for n, p in plates.items()}
    # 1 号锁的剖切刀在 cut_open 里往下扫，锁壳、锁芯这些带布尔的件网格是逐帧变的；引擎的 BVHCache 网格只取一次（按刚体设计），
    # 会拿第 0 帧的整锁去和钥匙比（11-22 第一次 clip：钥匙刃对 inset_housing 报 365–488 共 124 次，逐帧精确重算是 0）。这里让这些件每帧重取网格。
    vol = {o.name for o in _meshes(locks[0]) if any(m.type == "BOOLEAN" for m in getattr(o, "modifiers", []))}
    # 引擎用 blender --python shot_drill.py 跑时，clip_run 里的 BVHCache 属于 __main__，和这里 import 的 shot_drill 不是同一个类，两个都补
    for mod in {id(m): m for m in (SD, sys.modules.get("__main__")) if m is not None and hasattr(m, "BVHCache")}.values():
        cls = mod.BVHCache
        if getattr(cls, "_vol_patched", False):
            continue

        def _mk(orig):
            def _geo(self, o, dg):
                if o.name in vol:
                    self.geo.pop(o.name, None)
                    self.trees.pop(o.name, None)
                return orig(self, o, dg)
            return _geo
        cls._geo = _mk(cls._geo)
        cls._vol_patched = True
    frames = set(range(0, NF, 3)) | set(range(t.key_up[0], t.try3[2] + 4)) | set(range(t.pt[0], t.pt[2] + 20)) | set(range(t.pc[0], t.pc[1] + 40)) \
        | set(range(t.ps[0], min(NF, t.ps[1] + 30)))

    def groups(f):
        g = [("key_vs_locks", k_m, lock_m), ("key_vs_rack", k_m, rod_m)]
        for n, pm in p_m.items():
            others = [m for n2, pm2 in p_m.items() if n2 != n for m in pm2]
            g.append((f"plate_{n}_vs_rest", pm, lock_m + rod_m + others + k_m))
        return g
    return dict(frames=sorted(frames), groups=groups, cam_near=lambda f: lock_m + k_m + rod_m + [m for pm in p_m.values() for m in pm], ref=None)


# ================================================================ 合成：出处行
def comp_frames(seg, flist=None):
    import numpy as np
    from PIL import Image
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    for f in (flist if flist is not None else range(NF)):
        pil = Image.open(W / "frames" / f"f_{f:04d}.png").convert("RGBA")
        base_a = ramp(f, 24, 44) * (1 - ramp(f, t.whip[0] - 4, t.whip[0] + 4))
        it = dict(text=SRC_TOY, xy=SRC_XY, size=SRC_SIZE, color=(240, 238, 232), anchor="ls", shadow=False, plate=PLATE_BG)
        if base_a > 0.003:
            pil = Image.alpha_composite(pil, SD.draw_text_layer([it], lambda it_: base_a))
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

    def tick(s, g=0.08):
        return C([(2400, 1.0), (4100, 0.4)], 6, 2, g, s)

    def rattle(s, g=0.10):
        return C([(1500, 1.0), (2900, 0.5)], 10, 3, g, s)
    hits = [(t.pt[1], snap(1, 0.18), 0.5), (t.key_up[1], snap(2, 0.20), 0.35), (t.pc[1], snap(3, 0.16), 0.35),
            (t.cut[0], SD.whoosh((t.cut[2] - t.cut[0]) / SD.FPS, 0.05, 4, f0=1800, f1=600), 0.55)]
    al = t.key_in[0] + 14
    for i in range(5):                                               # 销被齿顶起（滑进去时一根一根）
        hits.append((int(al + (t.key_in[1] - al) * (i + 0.5) / 5), tick(10 + i), 0.55))
    hits += [(t.pins[1], clack(20, 0.16), 0.55), (t.turn[1], clack(21, 0.24), 0.55), (t.turn[1] + 4, snap(22, 0.18), 0.55),
             (t.try2[1], clack(23, 0.14), 0.6)]
    for k in range(2):
        hits.append((t.try2[1] + 2 + 5 * k, rattle(30 + k), 0.6))
        hits.append((t.try3[1] + 2 + 6 * k, rattle(40 + k), 0.7))
    hits += [(t.try3[1], clack(24, 0.14), 0.7), (t.try2[1] + 10, tick(25, 0.10), 0.6), (t.try3[1] + 12, tick(26, 0.10), 0.7),
             (t.ps[1], snap(27, 0.20), 0.55), (t.whip[0] - 4, SD.whoosh((t.whip[1] - t.whip[0] + 18) / SD.FPS, 0.22, 31), 0.7)]
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
    res["luma_jumps_gt_0.06"] = [[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma))
                                 if abs(luma[i] - luma[i - 1]) > 0.06 and i < t.whip[0] - 2]
    res["luma_mean"] = round(float(luma.mean()), 3)
    res["luma_every_30"] = [round(float(x), 3) for x in luma[::30]]
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-map", "0:a", "-f", "null", "-"], capture_output=True, text=True)
    res["audio_ok"] = pr.returncode == 0
    M = json.loads((SD.MAPD / "master_v1.json").read_text(encoding="utf-8"))
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
        name = f"16_钻取_3-03_抽帧_{len(pages) + 1:02d}.jpg"
        im.save(SD.work(seg) / name, quality=86)
        pages.append(name)
    (SD.work(seg) / "sheets.json").write_text(json.dumps(dict(step=step, pages=pages, frames=idx)), encoding="utf-8")
    print("DRILL sheet", pages, flush=True)
