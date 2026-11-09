"""HKBU SCIE1007 课程作业的科普视频。S5 的 5-01、5-07、5-10 三段台面版（11-10 通宵第二批，Claude），由 bl_inserts.py 的 BL_EXTRA 接口运行。
bl_s5.py（4-10、5-04）别的工人还在改，这里不动它，只在运行时读进来，借它的 shot_s410 搭出 4-10 最后一帧的台面。

`s501`：接 4-10 最后一帧（7 把钥匙一行）。镜头往下落到前面的格子 39；七张纸卡（论文 Fig. 5 的结构，骨白底版裁切，见 make_s5b_cards.py）
从画面上方一张张落到格子里，排成一行，和后面那行钥匙一一对应。卡上的编号、Kd 和"Kd: lower = tighter"小尺在 Remotion（s5b.jsx）里叠。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s5b.py blender.exe -b -t 4 -P bl_inserts.py -- s501 <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
BL_S5B_PROJ=<秒>：只打印那一刻卡片在画面上的位置（给 s5b.jsx 定字的位置），不渲染。
"""
import math
import os

import bpy
from mathutils import Quaternion, Vector

META = {"s501": (625.0, 1020, 0.2, 0.9), "s507": (693.0, 1200, 0.2, 0.9), "s510": (738.0, 1440, 0.2, 0.9)}   # 5-01 10:25-10:42，17 秒；5-07 11:33-11:53，20 秒；5-10 12:18-12:42，24 秒
MY_META = dict(META)                        # bl_s5.py 读进来时会把 META 换成它自己的

_here = os.path.dirname(os.path.abspath(XFILE))
exec(compile(open(os.path.join(_here, "bl_s5.py"), encoding="utf-8").read(), "bl_s5.py", "exec"))
CARDS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))), "remotion_public", "fusion_s5b")
NAMES = ["001", "004", "007", "009", "015", "019", "025"]          # Fig. 5 的七个，和 4-10 那行钥匙从左到右一一对应
CW, CD, CT = 0.105, 0.070, 0.0025                                   # 纸卡：宽、深、厚（贴图 600 x 400）
CGAP = 0.112


def s410_end(sc, sky):
    """4-10 的最后一帧，动画全清掉；返回 4-10 的 ctx（钥匙、那一行、结尾机位）。"""
    upd = shot_s410(sc, sky)
    X = upd.ctx
    upd(T0 + 1499 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    return X


def card_mat(name):
    m = bpy.data.materials.new("s5b_card_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.75
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(CARDS, "card_%s.png" % name))
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def paper_card(sc, name, edge):
    """一张纸卡：薄板，顶面贴论文的结构图（UV 铺满顶面），四边和底面是纸色。原点在底面中心。"""
    import bmesh
    me = bpy.data.meshes.new("s5b_card_" + name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(CW, CD, CT), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, CT / 2), verts=bm.verts)
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        top = f.normal.z > 0.5
        f.material_index = 0 if top else 1
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = ((co.x / CW + 0.5), (co.y / CD + 0.5)) if top else (0.02, 0.02)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(card_mat(name))
    me.materials.append(edge)
    o = bpy.data.objects.new("s5b_card_" + name, me)
    sc.collection.objects.link(o)
    o.rotation_mode = "QUATERNION"
    return o


def shot_s501(sc, sky):
    """5-01（10:25-10:42，C 画外音）。0-1 s 是 4-10 的最后一帧，不动；1.0-3.0 s 镜头落到格子 39（一次移动，2 秒）；
    2.6 s 起七张纸卡从画面上方一张张直落进格子 39，每张 0.55 秒，缓停，不弹；4.5 s 后台面不再动，字在 Remotion 里出。"""
    X = s410_end(sc, sky)
    end_v, q_row = X["end_v"], X["q_row"]
    T5 = MY_META["s501"][0]
    yaw = math.radians(20.0)
    ru = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    c39 = Vector((*cell_at(39), 0.0))
    ROW = c39 + Vector((0.0, -0.02, 0.0))
    home = [ROW + ru * (i - 3) * CGAP for i in range(7)]
    edge = bpy.data.materials.new("s5b_paper")
    edge.diffuse_color = (0.93, 0.9, 0.84, 1)
    edge.use_nodes = True
    eb = next(n for n in edge.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    eb.inputs["Base Color"].default_value = (0.93, 0.9, 0.84, 1)
    eb.inputs["Roughness"].default_value = 0.8
    cards = [paper_card(sc, n, edge) for n in NAMES]

    T_M, T_ME = 1.0, 3.0
    T_LAND0, T_STAG, T_DROP, Z0 = 2.6, 0.22, 0.55, 0.9
    card_v = dict(at=tuple(ROW - ru * 0.045 + Vector((0.0, 0.06, 0.0))), az=yaw, el=math.radians(50.0), d=1.17, mm=45.0)

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M:
            return dict(end_v)
        if t < T_ME:
            return mix(end_v, card_v, smooth((t - T_M) / (T_ME - T_M)))
        return dict(card_v)

    def focus(t):
        a_, b_ = Vector(end_v["at"]), ROW
        return a_.lerp(b_, smooth((t - T_M) / (T_ME - T_M)))

    def card_z(i, t):
        """直落：从 Z0 落到台面，缓入缓停（末速为零），不弹。落之前在画面上方外面。"""
        t1 = T_LAND0 + T_STAG * i
        t0 = t1 - T_DROP
        if t < t0:
            return Z0
        x = min(1.0, (t - t0) / T_DROP)
        return Z0 * (1.0 - smooth(x))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def keyed(e, i, t, f):
        e.animation_data_clear()
        for df in (-1, 0, 1):
            e.location = home[i] + Vector((0, 0, card_z(i, t + df / FPS)))
            e.keyframe_insert("location", frame=f + df)
        e.location = home[i] + Vector((0, 0, card_z(i, t)))

    def update(t_abs):
        t = t_abs - T5
        f = int(round(t * FPS))
        shoot(c, f, cam(t), focus(t))
        for i, e in enumerate(cards):
            e.rotation_quaternion = q_row
            t1 = T_LAND0 + T_STAG * i
            if t1 - T_DROP - 0.05 <= t <= t1 + 0.05:
                keyed(e, i, t, f)
            else:
                e.animation_data_clear()
                e.location = home[i] + Vector((0, 0, card_z(i, t)))
            e.hide_render = card_z(i, t) >= Z0 - 1e-6 and t < t1          # 落之前不在台面上
        sky(0.2)

    update.view = cam
    update.ctx = dict(X, cards=cards, card_home=home, card_v=card_v, row=ROW)

    # ---------------------------------------------------------------- 穿模检查（解析：卡在格子里、彼此不叠、不入台面、不碰钥匙那一格）
    if SHOT == "s501" and not os.environ.get("BL_NOCHECK"):
        bad = {}
        half_x, half_y = 0.95 / 2 - 0.06, 0.84 / 2 - 0.06          # 格子内沿（留出圆角槽壁）
        corners = [Vector((sx * CW / 2, sy * CD / 2, 0)) for sx in (-1, 1) for sy in (-1, 1)]
        qm = q_row.to_matrix()
        for i in range(7):
            for k in corners:
                p = home[i] + qm @ k
                if abs(p.x - c39.x) > half_x or abs(p.y - c39.y) > half_y:
                    bad.setdefault("card %s / cell wall" % NAMES[i], []).append(tuple(round(v, 3) for v in p))
        # 相邻两张：沿行方向的间隙
        gap = CGAP - CW
        if gap <= 0.002:
            bad["card / card"] = [gap]
        for f in range(0, FRAMES, 2):
            for i in range(7):
                if card_z(i, f / FPS) < -1e-6:
                    bad.setdefault("card / table", []).append(f)
        print("S501 clashes:", "none" if not bad else "")
        for k, v in bad.items():
            print("S501 clash %s: %s" % (k, v[:3]))
        print("S501 card gap %.4f, cell margin x %.3f y %.3f" % (gap, half_x - max(abs((home[i] + qm @ k).x - c39.x) for i in range(7) for k in corners),
                                                              half_y - max(abs((home[i] + qm @ k).y - c39.y) for i in range(7) for k in corners)))
    if os.environ.get("BL_S5B_PROJ") and SHOT == "s501":
        from bpy_extras.object_utils import world_to_camera_view
        tp = float(os.environ["BL_S5B_PROJ"])
        sc.frame_set(int(round(tp * FPS)))
        update(T5 + tp)
        bpy.context.view_layer.update()
        for i, e in enumerate(cards):
            for nm, off in (("mid", (0, 0)), ("front", (0, -CD / 2)), ("back", (0, CD / 2)), ("left", (-CW / 2, 0)), ("right", (CW / 2, 0))):
                p = home[i] + q_row.to_matrix() @ Vector((off[0], off[1], CT))
                v = world_to_camera_view(sc, c, p)
                print("S501 proj %s %s %.0f %.0f" % (NAMES[i], nm, v.x * 1920, (1 - v.y) * 1080))
        import sys
        sys.exit(0)
    return update


SHOTS["s501"] = shot_s501


def copy_key(sc, src, name):
    """拷一把 4-10 的钢钥匙：空物体和它下面的网格都拷，网格数据共用。"""
    e = src.copy()
    e.name = name
    e.animation_data_clear()
    sc.collection.objects.link(e)
    for ch in src.children:
        c2 = ch.copy()
        c2.animation_data_clear()
        c2.parent = e
        c2.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
        sc.collection.objects.link(c2)
        c2.hide_render = False
    e.rotation_mode = "QUATERNION"
    return e


def shot_s507(sc, sky):
    """5-07（11:33-11:53，C 画外音）。接 5-04 的最后一帧（格子 21 的酶活试管和剂量尺，特写）。
    0-1 s 不动；1.0-3.2 s 镜头退成中景，左边空着的格子 20 进画（"loop kicks in again"）；
    9.6 s 起格子 20 里 16 把新钥匙一把把长出来（4×4，W3 那一下提示光 0.6 秒内退掉；"Sixteen new designs"）；
    11.3 s 其中 10 把缩没，11.8-12.9 s 剩下 6 把贴着台面滑到格子前沿排成一行（"Six made and tested"，4-10 挑 7 把的同一个做法）；之后不动。
    回路（试管里的实验数据回到设计这边）、Round 2 的字在 Remotion 里画。"""
    upd = shot_s504(sc, sky)
    T504 = META["s504"][0]
    v_end = upd.view(1439 / FPS)
    upd(T504 + 1439 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    T5 = MY_META["s507"][0]
    ob = bpy.data.objects
    seven = [o for o in ob if o.type == "EMPTY" and o.name.startswith(("w3_rain", "w3_orb")) and len(o.children) and not all(ch.hide_render for ch in o.children)]
    src = min(seven, key=lambda o: o.location.z)
    KS, ZK = src.scale[0], src.location.z
    c20 = Vector((*cell_at(20), 0.0))
    c21 = Vector((*cell_at(21), 0.0))
    yaw = Quaternion((0, 0, 1), math.radians(90.0)) @ Quaternion(src.rotation_quaternion)
    GX = c20.x + 0.15                                  # 钥匙靠格子 20 的右半边，离试管近一点，镜头能推近一档
    grid = [Vector((GX + (cx - 1.5) * 0.14, c20.y + 0.03 + (1.5 - cy) * 0.12, ZK)) for cy in range(4) for cx in range(4)]
    TESTED = [1, 2, 5, 6, 9, 10]                       # 中间两列的 6 把留下（只往前直走，路线互不相交）
    slot = {k: Vector((GX + (j - 2.5) * 0.075, c20.y - 0.25, ZK)) for j, k in enumerate(sorted(TESTED, key=lambda k: (grid[k].x, -grid[k].y)))}
    new = [copy_key(sc, src, "s507_key%02d" % i) for i in range(16)]
    T_M, T_ME = 1.0, 3.2
    T_GROW, T_GSTAG, T_GDUR = 9.6, 0.07, 0.5          # 第 2 版：一把把从画面上方直落进格子（原来是原地长出来）
    T_SHRINK, T_SDUR = 11.3, 0.8                       # 第 2 版：没留下的 10 把整批升出画外（原来是原地缩没，06 第 5 节不许）
    Z_HI = 1.0
    T_SLIDE, T_SLIDE_E = 11.8, 12.9
    mid_v = dict(at=(c20.x + 0.13, c20.y - 0.04, 0.0), az=0.0, el=math.radians(56.0), d=1.3, mm=45.0)          # 第 2 版：推近一档；试管放到画面右边缘，玻璃顶不再从右上标题后面过

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M:
            return dict(v_end)
        if t < T_ME:
            return mix(v_end, mid_v, smooth((t - T_M) / (T_ME - T_M)))
        return dict(mid_v)

    def focus(t):
        return Vector(v_end["at"]).lerp(Vector(mid_v["at"]), smooth((t - T_M) / (T_ME - T_M)))

    out_order = [i for i in range(16) if i not in TESTED]

    def size(i, t):
        """大小不变；只是落下之前、升走之后不在台面上（返回 0 当作不在）。"""
        if t < T_GROW + T_GSTAG * i:
            return 0.0
        if i not in TESTED and t > T_SHRINK + 0.03 * out_order.index(i) + T_SDUR:
            return 0.0
        return 1.0

    def where(i, t):
        p_ = Vector(grid[i])
        t0 = T_GROW + T_GSTAG * i
        p_.z = ZK + (Z_HI - ZK) * (1.0 - smooth((t - t0) / T_GDUR))          # 直落，末速为零，不弹
        if i in TESTED:
            q_ = grid[i].lerp(slot[i], smooth((t - T_SLIDE) / (T_SLIDE_E - T_SLIDE)))
            return Vector((q_.x, q_.y, p_.z))
        t1 = T_SHRINK + 0.03 * out_order.index(i)
        p_.z += (Z_HI - ZK) * smooth((t - t1) / T_SDUR)                        # 整批升走，出画上方
        return p_

    def glow(i, t):
        return 0.0

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def place(e, i, t):
        s_ = size(i, t)
        e.location, e.rotation_quaternion, e.scale = where(i, t), yaw, (KS * max(s_, 1e-4),) * 3

    def update(t_abs):
        t = t_abs - T5
        f = int(round(t * FPS))
        shoot(c, f, cam(t), focus(t))
        for i, e in enumerate(new):
            moving = T_GROW + T_GSTAG * i - 0.05 <= t <= T_SLIDE_E + 0.05
            e.animation_data_clear()
            if moving:
                for df in (-1, 0, 1):
                    place(e, i, t + df / FPS)
                    for path in ("location", "rotation_quaternion", "scale"):
                        e.keyframe_insert(path, frame=f + df)
            place(e, i, t)
            vis = size(i, t) > 1e-3
            g_ = glow(i, t)
            for ch in e.children:
                ch.hide_render = not vis
                ch.color = (g_, 0, 0, 1)
        sky(0.2)

    update.view = cam
    update.ctx = dict(keys16=new, tested=TESTED, slot=slot, mid_v=mid_v)
    print("S507 c20 %s src %s KS %.5f ZK %.4f" % (tuple(round(v, 3) for v in c20), src.name, KS, ZK))

    # ---------------------------------------------------------------- 穿模检查（每两帧）：钥匙的点云对格子内沿、对彼此、对台面
    if SHOT == "s507" and not os.environ.get("BL_NOCHECK"):
        import numpy as np
        bpy.context.view_layer.update()
        inv = src.matrix_world.inverted()
        pts = np.array([tuple(inv @ (ch.matrix_world @ v.co)) for ch in src.children if not ch.hide_render for v in ch.data.vertices])
        pts = pts[np.linspace(0, len(pts) - 1, min(500, len(pts))).astype(int)]
        R = np.array(yaw.to_matrix())
        bad, near = {}, [9.0]
        half_x, half_y = 0.95 / 2 - 0.06, 0.84 / 2 - 0.06
        for f in range(0, FRAMES, 2):
            t = f / FPS
            ws = []
            for i in range(16):
                s_ = size(i, t)
                if s_ <= 1e-3:
                    ws.append(None)
                    continue
                w_ = pts @ R.T * (KS * s_) + np.array(tuple(where(i, t)))
                ws.append(w_)
                if (w_[:, 2] < 1e-4).any():
                    bad.setdefault("key / table", []).append(t)
                if (np.abs(w_[:, 0] - c20.x) > half_x).any() or (np.abs(w_[:, 1] - c20.y) > half_y).any():
                    bad.setdefault("key / cell wall", []).append(t)
            for i in range(16):
                for j in range(i + 1, 16):
                    if ws[i] is None or ws[j] is None:
                        continue
                    d_ = np.sqrt(((ws[i][::4, None] - ws[j][None, ::4]) ** 2).sum(-1)).min()
                    near[0] = min(near[0], d_)
                    if d_ < 0.002:
                        bad.setdefault("key / key", []).append((t, i, j))
        ext = pts * KS
        print("S507 key size %.3f x %.3f x %.3f" % tuple(ext.max(0) - ext.min(0)))
        print("S507 clashes:", "none" if not bad else "")
        for k, v in bad.items():
            print("S507 clash %s: %d, first %s" % (k, len(v), v[0]))
        print("S507 closest two keys come: %.4f" % near[0])
    if os.environ.get("BL_S5B_PROJ") and SHOT == "s507":
        from bpy_extras.object_utils import world_to_camera_view
        tp = float(os.environ["BL_S5B_PROJ"])
        update(T5 + tp)
        bpy.context.view_layer.update()
        tube = ob.get("s504_tube")
        for nm, p_ in [("c20", c20), ("c21", c21), ("tube", Vector(tube.location) if tube else c21), ("tube_top", Vector(tube.location) + Vector((0, 0, 0.30)))] + [("slot%d" % k, v) for k, v in sorted(slot.items())] + [("grid%d" % i, grid[i]) for i in (0, 3, 12, 15)]:
            v = world_to_camera_view(sc, c, p_)
            print("S507 proj %s %.0f %.0f" % (nm, v.x * 1920, (1 - v.y) * 1080))
        import sys
        sys.exit(0)
    return update


SHOTS["s507"] = shot_s507


IC50_HUH7, IC50_HEK, DOSE_MAX = 208.7, 1706.7, 1800.0          # nM，Ren 2023 p1448 / Fig. 9B；剂量尺 0-1,800 nM 线性，不标数


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def shot_s510(sc, sky):
    """5-10（12:18-12:42，C 画外音）。先接 5-07 的最后一帧（W4 还没做；W4 做的时候让它停在这一帧，或者这一段改接 W4）。
    0-1 s 不动；1.0-3.4 s 镜头往前落到格子 29：两只玻璃培养皿，后排 Huh7、前排 HEK293，每只 40 个细胞；
    各带一条墨线剂量尺和一个钢滑块（5-04 的做法，尺子 0-1,800 nM 线性，不标数），尺上一道长一点的墨线是各自的 IC50。
    9.6-16.0 s 两个滑块一起走：Huh7 皿里的细胞在滑块走到 208.7 那道线以前就缩没一半（很快），HEK293 一路慢慢缩，到 1,706.7 那道才缩没一半。之后不动。"""
    import bmesh
    import random
    upd = shot_s507(sc, sky)
    v_end = upd.view(1199 / FPS)
    upd(MY_META["s507"][0] + 1199 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    T5 = MY_META["s510"][0]
    ob = bpy.data.objects
    ink = ob["s504_axis"].material_slots[0].material
    steel = ob["s504_marker"].material_slots[0].material
    glass = ob["s504_tube"].material_slots[0].material
    pink = P.gloss((0.86, 0.50, 0.50), 0.35, 0.6)          # 和 S7 7-02 培养皿同一组颜色
    pale = P.gloss((0.93, 0.87, 0.72), 0.35, 0.6)
    c29 = Vector((*cell_at(29), 0.0))
    R_D, H_D, WL, GEL = 0.085, 0.016, 0.0018, 0.005
    RC, NC = 0.0085, 40
    AXH, MK = 0.0016, 0.028
    L0, L1 = c29.x - 0.12, c29.x + 0.34
    rows = [dict(name="huh7", y=c29.y + 0.16, med=pale, cell=pink, ic=IC50_HUH7), dict(name="hek", y=c29.y - 0.15, med=pale, cell=pale, ic=IC50_HEK)]
    T_M, T_ME = 1.0, 3.4
    T_D0, T_D1 = 9.6, 16.0
    view = dict(at=(c29.x + 0.06, c29.y - 0.02, 0.0), az=0.0, el=math.radians(44.0), d=1.35, mm=45.0)

    def box(name, lo, hi, mat):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)) @ Matrix.Diagonal((hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], 1)))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        sc.collection.objects.link(o)
        return o

    rnd = random.Random(510)
    for r in rows:
        r["dx"] = c29.x - 0.27
        e = bpy.data.objects.new("s510_dish_" + r["name"], None)
        sc.collection.objects.link(e)
        e.location = (r["dx"], r["y"], 0.0)
        lathe([(0, 0), (R_D, 0), (R_D, H_D), (R_D - WL, H_D), (R_D - WL, WL), (0, WL)], glass, "s510_base_" + r["name"], e, 64)
        lathe([(0, WL), (R_D - WL - 0.0004, WL), (R_D - WL - 0.0004, WL + GEL), (0, WL + GEL + 0.0004)], r["med"], "s510_gel_" + r["name"], e, 64)
        pts = []          # 细胞：胶面上的小扁圆，彼此不叠
        while len(pts) < NC:
            a_, rr = rnd.uniform(0, 2 * math.pi), (R_D - WL - RC - 0.004) * math.sqrt(rnd.random())
            q = (rr * math.cos(a_), rr * math.sin(a_))
            if all(math.hypot(q[0] - p_[0], q[1] - p_[1]) > 2 * RC + 0.003 for p_ in pts):
                pts.append(q)
        cells = []
        for k, q in enumerate(pts):
            c_ = lathe([(0, 0), (RC, 0), (RC * 0.92, RC * 0.35), (RC * 0.55, RC * 0.62), (0, RC * 0.7)], r["cell"], "s510_cell_%s_%02d" % (r["name"], k), e, 24)
            c_.location = (q[0], q[1], WL + GEL)
            cells.append(c_)
        r["cells"], r["pts"] = cells, pts
        order = list(range(NC))
        rnd.shuffle(order)
        r["die"] = order[:NC // 2]                       # 到 IC50 时没了的一半
        AY = r["y"]
        box("s510_axis_" + r["name"], (L0, AY - 0.003, 0.0), (L1, AY + 0.003, AXH), ink)
        for i in range(7):
            x_ = L0 + (L1 - L0) * i / 6
            box("s510_tick_%s%d" % (r["name"], i), (x_ - 0.0025, AY - 0.022, 0.0), (x_ + 0.0025, AY - 0.003, AXH), ink)
        xm = L0 + (L1 - L0) * r["ic"] / DOSE_MAX
        r["xm"] = xm
        box("s510_ic50_" + r["name"], (xm - 0.003, AY - 0.040, 0.0), (xm + 0.003, AY - 0.003, AXH * 1.5), ink)
        r["marker"] = box("s510_marker_" + r["name"], (-MK / 2, -MK / 2, 0.0), (MK / 2, MK / 2, 0.018), steel)
        r["mk_y"] = AY + 0.020
        r["t_ic"] = T_D0 + (T_D1 - T_D0) * r["ic"] / DOSE_MAX

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M:
            return dict(v_end)
        if t < T_ME:
            return mix(v_end, view, smooth((t - T_M) / (T_ME - T_M)))
        return dict(view)

    def focus(t):
        return Vector(v_end["at"]).lerp(Vector(view["at"]), smooth((t - T_M) / (T_ME - T_M)))

    def dose_x(t):
        return L0 + (L1 - L0) * clamp01((t - T_D0) / (T_D1 - T_D0))

    def cell_size(r, k, t):
        """死的那一半，在滑块从 0 走到自己 IC50 的这段时间里一个个缩没（顺序打乱）；活的一直在。"""
        if k not in r["die"]:
            return 1.0
        j = r["die"].index(k)
        t_end = T_D0 + (r["t_ic"] - T_D0) * (j + 1) / len(r["die"])
        return 1.0 - smooth((t - (t_end - 0.35)) / 0.35)

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def update(t_abs):
        t = t_abs - T5
        f = int(round(t * FPS))
        shoot(c, f, cam(t), focus(t))
        moving = T_D0 - 0.05 <= t <= T_D1 + 0.05
        for r in rows:
            mk = r["marker"]
            mk.animation_data_clear()
            if moving:
                for df in (-1, 0, 1):
                    mk.location = (dose_x(t + df / FPS), r["mk_y"], 0.0)
                    mk.keyframe_insert("location", frame=f + df)
            mk.location = (dose_x(t), r["mk_y"], 0.0)
            for k, c_ in enumerate(r["cells"]):
                c_.animation_data_clear()
                s_ = cell_size(r, k, t)
                if moving and k in r["die"]:
                    for df in (-1, 0, 1):
                        sz = max(cell_size(r, k, t + df / FPS), 1e-4)
                        c_.scale = (sz, sz, sz)
                        c_.keyframe_insert("scale", frame=f + df)
                c_.scale = (max(s_, 1e-4),) * 3
                c_.hide_render = s_ <= 1e-3
        sky(0.2)

    update.view = cam
    update.ctx = dict(rows=rows, view=view)
    print("S510 c29 %s marks huh7 %.3f at %.2fs, hek %.3f at %.2fs" % (tuple(round(v, 3) for v in c29), rows[0]["xm"], rows[0]["t_ic"], rows[1]["xm"], rows[1]["t_ic"]))

    # ---------------------------------------------------------------- 穿模检查（解析）：皿、尺、滑块都在格子 29 内沿里，滑块不碰尺子和皿，细胞在皿里不叠
    if SHOT == "s510" and not os.environ.get("BL_NOCHECK"):
        bad = {}
        half_x, half_y = 0.95 / 2 - 0.06, 0.84 / 2 - 0.06
        for r in rows:
            ext = [(r["dx"] - R_D, r["y"] - R_D), (r["dx"] + R_D, r["y"] + R_D), (L1 + MK / 2, r["mk_y"] + MK / 2), (L0, r["y"] - 0.040)]
            for (x_, y_) in ext:
                if abs(x_ - c29.x) > half_x or abs(y_ - c29.y) > half_y:
                    bad.setdefault("%s / cell wall" % r["name"], []).append((round(x_, 3), round(y_, 3)))
            if r["mk_y"] - MK / 2 < r["y"] + 0.003 + 0.001:
                bad.setdefault("marker / rule", []).append(r["name"])
            if L0 - MK / 2 < r["dx"] + R_D + 0.002:
                bad.setdefault("marker / dish", []).append(r["name"])
            for i, p_ in enumerate(r["pts"]):
                if math.hypot(*p_) + RC > R_D - WL:
                    bad.setdefault("cell / dish wall", []).append(i)
        if rows[0]["y"] - R_D < rows[1]["mk_y"] + MK / 2 + 0.01 and False:
            bad["row / row"] = [1]
        gap_rows = (rows[0]["y"] - 0.040) - (rows[1]["mk_y"] + MK / 2)
        dish_gap = (rows[0]["y"] - R_D) - (rows[1]["y"] + R_D)
        if gap_rows < 0.005 or dish_gap < 0.005:
            bad["row / row"] = [round(gap_rows, 3), round(dish_gap, 3)]
        print("S510 clashes:", "none" if not bad else "")
        for k, v in bad.items():
            print("S510 clash %s: %s" % (k, v[:3]))
        print("S510 rows gap %.3f, dishes gap %.3f" % (gap_rows, dish_gap))
    if os.environ.get("BL_S5B_PROJ") and SHOT == "s510":
        from bpy_extras.object_utils import world_to_camera_view
        tp = float(os.environ["BL_S5B_PROJ"])
        update(T5 + tp)
        bpy.context.view_layer.update()
        for r in rows:
            for nm, p_ in [("dish", Vector((r["dx"], r["y"], 0.0))), ("dish_back", Vector((r["dx"], r["y"] + R_D, 0.0))), ("dish_front", Vector((r["dx"], r["y"] - R_D, 0.0))),
                           ("rule0", Vector((L0, r["y"], 0.0))), ("rule1", Vector((L1, r["y"], 0.0))), ("mark", Vector((r["xm"], r["y"] - 0.04, 0.0)))]:
                v = world_to_camera_view(sc, c, p_)
                print("S510 proj %s %s %.0f %.0f" % (r["name"], nm, v.x * 1920, (1 - v.y) * 1080))
        import sys
        sys.exit(0)
    return update


SHOTS["s510"] = shot_s510
