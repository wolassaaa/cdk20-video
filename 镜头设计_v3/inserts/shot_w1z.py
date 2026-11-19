"""HKBU SCIE1007 课程作业的科普视频：大标题 W1《零重力开箱》（镜头设计_v3/深化/07_大标题与大片感.md 第一节），连 1-11 最后 2 秒、2-01 开头 2 秒。

世界：就是那块大板。拍 1 的鼓点上零件从浇口脱落、重力关掉，浮起来；子弹时间里镜头在零件群里绕 120°；
时间恢复后零件排成一个环，环中间一条镀铬料杆滑进来挂着片名字母，字母一个个剪下、翻半圈落位；
红色问号晚半拍；深色副标题长牌从后面转进来；课程牌、Section、Group、名单牌像卫星绕一圈落位；
八块章节牌在环里一对一对转到正面（主讲人名字）；定格让观众读；最后零件被吸回大板一个个插回浇口，
镜头跟着最后一块 CDK20 俯冲，贴着料杆落到第 2 区楼群，接 2-01。

时间单位：一"拍单位" u = 2 个音乐拍（Godmother 121.483 BPM，0.9878 s）。W1 从 1-11 结束那一帧算，共 17 u = 16.79 s。
07 文档的逐拍表按 04 的"10 秒内信息出齐"整体前移（见 TL 表和报告），定格从 1 u 延长到 4 u。
物理：零重力下的运动是解析的（匀速漂、缓停、慢转），逐帧烘焙成关键帧；不穿模由凸包逐帧检查保证（check 里的 clip_pairs）。
名字：只有 --final 时在本进程里由 title_names 读进内存直接生成文字，不打印、不落盘。
"""
import json
import math
import random
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

import kit_deep as D
import bl_guide as BG
import kit_h20 as H
import shot_w0w1 as S

MM = 0.001
FPS = 60
U = 2 * 60.0 / S.BPM                       # 一个拍单位（秒）
TAIL, HEAD = S.TAIL, S.HEAD
NF_W1 = S.NF_W1
NF = TAIL + NF_W1 + HEAD
C = Vector((-4.0, 0.0, 700.0))             # 片名中心（mm）
RING_A, RING_B = 680.0, 400.0              # 零件环（XZ 平面里的椭圆）
TAG_W, TAG_H = 270.0, 150.0
FRAME_HW, FRAME_HH = 830.0, 462.0          # 读字机位下画面的半宽、半高（mm，片名平面上）
CAP_TITLE = 86.0
SP_HERO = 2.4                              # 挂在章节牌旁边的主角零件小一点，好排
SP = 2.7                                   # 零件离开大板后放大到 3 倍（零重力里"浮肿"开，环才撑得起片名），回板时缩回原大

# 逐拍表（单位 u；W1 第 0 帧 = 1-11 最后一帧之后）
TL = dict(skim=0.0, brk=1.0, bt_in=1.5, bt_out=2.9, resume=3.0, rod_in=3.0, rod_set=3.5, sweep=3.5,
          cuts=[4.0, 4.25, 4.5, 4.75, 5.0, 5.25], q_cut=5.75, q_land=6.25, rod_out=5.9,
          sub_in=6.25, sub_land=7.0, sat_in=6.9, sat_land=[7.5, 7.6, 7.7, 7.75],
          tags=[7.75, 8.25, 8.75, 9.25], read=9.5, read_end=13.5, suck=13.5, suck_end=15.0, land=17.0)


def Fu(u):
    """拍单位 → w1z 序列帧。"""
    return TAIL + round(FPS * U * u)


def clamp01(t):
    return min(1.0, max(0.0, t))


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_out3(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in2(t):
    t = clamp01(t)
    return t * t


def catmull(pts, s):
    """过所有点的 Catmull-Rom 曲线，s ∈ [0, 1] 均匀分到各段。"""
    n = len(pts) - 1
    x = clamp01(s) * n
    i = min(int(x), n - 1)
    t = x - i
    p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n, i + 2)]
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def bez(p0, p1, p2, p3, s):
    a = 1 - s
    return p0 * a ** 3 + p1 * 3 * a * a * s + p2 * 3 * a * s * s + p3 * s ** 3


# ---------------------------------------------------------------- 快速烘焙（每帧一个键，foreach_set）


def fast_bake(o, path, arr):
    """o 可以是 ID（物体、曲线、灯）或 ID 里的结构（节点插口、dof）：fcurve 挂在 o.id_data 上，路径用全路径找。"""
    arr = np.asarray(arr, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[:, None]
    n, k = arr.shape
    is_arr = hasattr(getattr(o, path), "__len__")
    if is_arr:
        for i in range(k):
            o.keyframe_insert(path, index=i, frame=0)
    else:
        o.keyframe_insert(path, frame=0)
    idb = o.id_data
    full = path if idb == o else o.path_from_id(path)
    ad = idb.animation_data
    fcs = [fc for fc in BG._fcurves(ad.action) if fc.data_path == full]
    for fc in fcs:
        i = fc.array_index if k > 1 else 0
        fc.keyframe_points.clear()
        fc.keyframe_points.add(n)
        co = np.empty(2 * n, np.float32)
        co[0::2] = np.arange(n)
        co[1::2] = arr[:, i]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("handle_left", co)
        fc.keyframe_points.foreach_set("handle_right", co)
        fc.update()


def qfix(Q):
    """四元数逐帧同号，子帧插值（运动模糊）不绕远路。"""
    Q = np.array(Q, dtype=np.float64)
    for f in range(1, len(Q)):
        if np.dot(Q[f], Q[f - 1]) < 0:
            Q[f] = -Q[f]
    return Q


# ---------------------------------------------------------------- 物体：每个会飞的东西一条轨迹


class Body:
    def __init__(self, obj, kind, name):
        self.o, self.kind, self.name = obj, kind, name
        self.o.rotation_mode = "QUATERNION"
        bpy.context.view_layer.update()
        mw = obj.matrix_world.copy()
        # "转动坐标系"：只去掉物体的平移和转动（不去缩放），世界点 = R(q) @ p + location
        Rt = np.array(mw.to_quaternion().to_matrix()).T
        T = np.array(mw.translation)
        pts, tris, base = [], [], 0
        exact = kind == "letter"                    # 字母挨得近、凹进去的地方多：用真网格查，不用凸包
        dg = bpy.context.evaluated_depsgraph_get()
        for m in [obj] + list(obj.children_recursive):
            if m.type in ("MESH", "FONT", "CURVE") and not m.hide_render:
                eo = m.evaluated_get(dg)
                me = eo.to_mesh()
                if me is not None and len(me.vertices):
                    co = np.empty(3 * len(me.vertices))
                    me.vertices.foreach_get("co", co)
                    co = co.reshape(-1, 3)
                    M = np.array(eo.matrix_world)
                    wv = co @ M[:3, :3].T + M[:3, 3]
                    pts.append((wv - T) @ Rt.T)
                    if exact:
                        me.calc_loop_triangles()
                        tv = np.empty(3 * len(me.loop_triangles), dtype=np.int64)
                        me.loop_triangles.foreach_get("vertices", tv)
                        tris.append(tv.reshape(-1, 3) + base)
                    base += len(me.vertices)
                eo.to_mesh_clear()
        P = np.concatenate(pts) if pts else np.zeros((1, 3))
        lo, hi = P.min(0), P.max(0)
        self.half = (hi - lo) / 2 / MM
        self.c_local = Vector(((lo + hi) / 2).tolist())
        self.r = float(np.linalg.norm(P - (lo + hi) / 2, axis=1).max()) / MM
        # 凸包（局部坐标，米），穿模检查用
        if exact:
            self.hv, self.hf = P, np.concatenate(tris).tolist()
            bm = None
        else:
            bm = bmesh.new()
            step = max(1, len(P) // 6000)
        if bm is not None:
            for p in P[::step]:
                bm.verts.new(p)
            if len(bm.verts) >= 4:
                h = bmesh.ops.convex_hull(bm, input=bm.verts)
                drop = list({v for v in h["geom_interior"] + h["geom_unused"] if isinstance(v, bmesh.types.BMVert)})
                bmesh.ops.delete(bm, geom=drop, context="VERTS")
                idx = {v: i for i, v in enumerate(bm.verts)}
                self.hv = np.array([v.co[:] for v in bm.verts])
                self.hf = [[idx[v] for v in f.verts] for f in bm.faces]
            else:
                self.hv, self.hf = None, None
            bm.free()
        self.q0 = mw.to_quaternion()
        self.s0 = obj.scale.copy()
        self.sp = 1.0                               # 最大缩放（排槽位用）
        self.scl = np.ones(NF)                      # 逐帧缩放
        self.c0 = (mw @ self.c_local) / MM          # 静止时的中心（mm）
        self.cen = None                             # (NF, 3) mm
        self.quat = None                            # (NF, 4)

    @property
    def R(self):
        return self.r * self.sp

    def bake(self):
        R = [Quaternion(q).to_matrix() for q in self.quat]
        loc = np.array([tuple(Vector(self.cen[f]) * MM - R[f] @ (self.c_local * self.scl[f])) for f in range(NF)])
        fast_bake(self.o, "location", loc)
        fast_bake(self.o, "rotation_quaternion", qfix(self.quat))
        if np.ptp(self.scl) > 1e-6:
            fast_bake(self.o, "scale", np.outer(self.scl, np.array(self.s0)))


def detach(o):
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw


# ---------------------------------------------------------------- 搭字、牌


def fix_overlap(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    mats = list(o.data.materials)
    cap = o["cap_mm"]
    no = bpy.data.objects.new(o.name, me)
    bpy.context.scene.collection.objects.link(no)
    no.matrix_world = o.matrix_world.copy()
    no["cap_mm"] = cap
    for m in mats:
        if m.name not in [x.name for x in me.materials]:
            me.materials.append(m)
    bpy.data.objects.remove(o)
    rm = no.modifiers.new("rm", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = 0.3 * MM
    rm.use_smooth_shade = True
    bpy.context.view_layer.objects.active = no
    bpy.ops.object.modifier_apply(modifier="rm")
    o_ref = no
    return o_ref


def mat_chrome(name="w1_dark_chrome"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.36, 0.37, 0.40, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.14
    return m


def font_obj(K, body, cap, mat, italic=False, extrude=1.0, bevel=0.3, align="LEFT", font=None):
    """竖立、字面朝 −Y 的字（原点在基线左端或中间）。cap = 大写字高 mm。"""
    cu = bpy.data.curves.new("w1t", "FONT")
    cu.body = "H"
    cu.font = font or bpy.data.fonts.load(str(D.FONTS / ("InstrumentSerif-Italic.ttf" if italic else "InstrumentSerif-Regular.ttf")), check_existing=True)
    cu.size = cap * MM
    cu.align_x = align
    cu.align_y = "BOTTOM_BASELINE"
    o = bpy.data.objects.new("w1t", cu)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    h = o.dimensions.y
    cu.size *= cap * MM / h
    cu.body = body
    cu.extrude = extrude * MM / 2
    cu.bevel_depth = bevel * MM
    cu.bevel_resolution = 2
    cu.resolution_u = 4
    o.data.materials.append(mat)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Quaternion((1, 0, 0), math.radians(90))
    o["cap_mm"] = cap
    bpy.context.view_layer.update()
    return o


def width_mm(o):
    bpy.context.view_layer.update()
    return o.dimensions.x / MM


def plate(K, name, w, h, t, mat, r=6.0):
    """竖立的圆角板（中心原点，板面朝 −Y），厚 t mm。"""
    P = D.Part(K, name, "white")
    o = P.box(0, 0, w / 2, h / 2, t, mat, r=r, bevel=min(1.2, t / 3))
    root = P.done()
    o.parent = None
    bpy.data.objects.remove(root)
    o.name = name
    o.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    o.rotation_mode = "QUATERNION"
    return o


def put_text_on(pl, txt, x, z, y_face):
    """字贴在板面上（板局部坐标：x 右、z 上、板面在 y_face）。"""
    txt.parent = pl
    txt.location = (x * MM, y_face * MM, z * MM)
    txt.rotation_quaternion = Quaternion((1, 0, 0), math.radians(90))


def name_case(s):
    """名字统一成"姓全大写 + 名首字母大写"（有的名字文件整行大写，有的只有姓大写）；只在内存里改，不落盘。"""
    w = s.split()
    return " ".join([w[0]] + [x.capitalize() if x.isupper() else x for x in w[1:]]) if len(w) > 1 else s


def fit(o, wmax, cap_min):
    w = width_mm(o)
    if w > wmax:
        s = wmax / w
        if o["cap_mm"] * s < cap_min - 1e-6:
            raise ValueError("w1z: text does not fit")
        o.data.size *= s
        o["cap_mm"] = o["cap_mm"] * s
    return o["cap_mm"]


# ---------------------------------------------------------------- 主搭建


CH_TITLES, CH_PEOPLE = H.TITLES, H.PEOPLE        # 和盒盖版同一份章名、主讲人
CH_HERO = ("z1_c0_r0", "z2_c3_r3", "z3_c4_r2", "z8_c11_r4", "z4_c7_r2", "z8_c11_r2", "z7_c10_r1", "z8_c11_r0")
CH_ANG = (112.5, 67.5, 22.5, -22.5, -67.5, -112.5, -157.5, 157.5)     # 顺时针从左上起


def build(sc, args):
    t0 = time.time()
    root, cells = S.load_board(sc)
    S.relight(sc, True)
    sc.view_settings.exposure += args.expo_w1
    sc.frame_start, sc.frame_end = 0, NF - 1
    K = D.Kit()
    rnd = random.Random(20261121)
    members = None
    if args.final:
        import title_names
        members = title_names.load_members(draft=False)
    ink, inkw, inkg = K.ink, K.inkw, K.inkg
    chrome = mat_chrome()

    # ---- 零件
    bodies = []
    parts = {}
    for cn in sorted(cells):
        try:
            p = D.part_of(cells[cn])
        except StopIteration:
            continue
        detach(p)
        b = Body(p, "part", cn)
        parts[cn] = b
        bodies.append(b)
    # ---- 章节牌 + 主角零件
    tags = []
    for k in range(8):
        hw, hh = TAG_W / 2, TAG_H / 2
        pl = plate(K, f"w1_tag_{k}", TAG_W, TAG_H, 4.0, K.white, r=8)
        num = font_obj(K, str(k + 1), 40, K.red, extrude=0.6, bevel=0.15)
        put_text_on(pl, num, -hw + 14, 16, -2.3)
        tt = font_obj(K, CH_TITLES[k], 26, ink, extrude=0.5, bevel=0.1)
        if width_mm(tt) <= TAG_W - 70:
            put_text_on(pl, tt, -hw + 52, 16, -2.3)
        else:                                   # 长章名折成两行（"How much did / computers help?"）
            bpy.data.objects.remove(tt)
            w = CH_TITLES[k].split()
            cut = min(range(1, len(w)), key=lambda i: abs(len(" ".join(w[:i])) - len(" ".join(w[i:]))))
            for li, (line, zb) in enumerate(((" ".join(w[:cut]), 46), (" ".join(w[cut:]), 16))):
                t2_ = font_obj(K, line, 25, ink, extrude=0.5, bevel=0.1)
                fit(t2_, TAG_W - 70, 25)
                put_text_on(pl, t2_, -hw + 52, zb, -2.3)
        ln = plate(K, f"w1_tag_rule_{k}", TAG_W - 28, 1.2, 0.6, inkg, r=0.4)
        ln.parent = pl
        ln.location = (0, -2.3 * MM, 3 * MM)
        names = ["All four of us"] if k == 0 else [(name_case(members[m]["name"]) if members else None) for m in CH_PEOPLE[k]]
        two = len(names) > 1
        for j, nm in enumerate(names):
            # 一行名字：字高 28、基线 -32；两行：字高 25、行距 34（= 1.36 倍字高，斜体 g/y 下伸不碰下一行大写）
            z = (-29 - 34 * j) if two else -32
            if nm:
                t = font_obj(K, nm, 25 if two else 28, ink, italic=True, extrude=0.5, bevel=0.1)
                fit(t, TAG_W - 30, 21)
                put_text_on(pl, t, -hw + 14, z, -2.3)
            else:
                pad = plate(K, f"w1_namepad_{k}_{j}", 170, 18, 0.6, inkg, r=2)
                pad.parent = pl
                pad.location = ((-hw + 14 + 85) * MM, -2.3 * MM, (z + 10) * MM)
        back = font_obj(K, f"No. {k + 1}", 12, inkg, extrude=0.3, bevel=0.05, align="CENTER")
        back.parent = pl
        back.location = (0, 2.3 * MM, -12 * MM)
        back.rotation_quaternion = Quaternion((0, 0, 1), math.pi) @ Quaternion((1, 0, 0), math.radians(90))
        a = math.radians(CH_ANG[k])
        pos = Vector((C.x + RING_A * math.cos(a), 0.0, C.z + RING_B * math.sin(a)))
        pl.location = (0, 0, 0)
        b = Body(pl, "tag", f"tag_{k}")
        b.slot = pos
        b.k = k
        tags.append(b)
        bodies.append(b)
    # ---- 片名字母、问号、料杆
    title = "WORTH TESTING"
    title_mat = D.mat_solid("w1_title_white", "#E6E2D8", rough=0.3, coat=0.12, sss=0.03)   # 片名白：比 kit 白暗一点、糙一点，高光不冲到 0.95
    q_mat = D.mat_solid("w1_qmark_red", "#C8102E", rough=0.24, coat=0.1, sss=0.03)       # 红问号：高光收一点
    full = font_obj(K, title + "?", CAP_TITLE, chrome)
    W = width_mm(full) + 6.0 * len(title)
    bpy.data.objects.remove(full)
    xs = []
    for i in range(len(title) + 1):
        pre = font_obj(K, (title + "?")[:i] + "I", CAP_TITLE, chrome)
        ii = font_obj(K, "I", CAP_TITLE, chrome)
        xs.append(width_mm(pre) - width_mm(ii) + 6.0 * i)
        bpy.data.objects.remove(pre)
        bpy.data.objects.remove(ii)
    x_left = C.x - W / 2
    base_z = C.z + 20.0
    letters = []
    for i, ch in enumerate(title + "?"):
        if ch == " ":
            continue
        o = font_obj(K, ch, CAP_TITLE, q_mat if ch == "?" else title_mat, extrude=14, bevel=1.4)     # 白色亮面塑料字，红问号；料杆、浇口镀铬
        if ch == "W":                           # W 的字形轮廓互相压着，挤出后里面露出一道棱：转成网格、体素重拓扑合成一块
            o = fix_overlap(o)
        o.location = (0, 0, 0)
        b = Body(o, "letter", f"L{i}_{ch}")
        b.ch, b.i = ch, i
        # 最终位置：中心 = 字原点 + 局部中心（字竖立朝 −Y）
        b.slot = Vector((x_left + xs[i], 0.0, base_z)) + Vector(Quaternion((1, 0, 0), math.radians(90)) @ b.c_local) / MM
        letters.append(b)
        bodies.append(b)
    rod_len = 2 * max(abs(b.slot.x - C.x) * 1.05 for b in letters) + 120
    rod_z = C.z + 20 + CAP_TITLE + 34
    bpy.ops.mesh.primitive_cylinder_add(radius=6 * MM, depth=rod_len * MM, vertices=48, rotation=(0, math.radians(90), 0))
    rod = bpy.context.object
    rod.name = "w1_chrome_rod"
    bpy.ops.object.shade_smooth()
    rod.data.materials.append(chrome)
    hang = []
    for n, b in enumerate(letters):
        hx = (b.slot.x - C.x) * 1.05             # 挂的位置就在落位位置正后方、略散开
        hang.append(hx)
        top = CAP_TITLE + 6
        bpy.ops.mesh.primitive_cone_add(radius1=0.8 * MM, radius2=2.4 * MM, depth=26 * MM, vertices=20,
                                        location=(hx * MM, 0, -19 * MM))
        g = bpy.context.object
        g.name = f"w1_gate_{n}"
        bpy.ops.object.shade_smooth()
        g.data.materials.append(chrome)
        g.parent = rod
        b.hang_dx = hx
    # ---- 副标题（深色长牌；透明亚克力在 24 采样下透出体积光噪点，白字发花，改成跟 Section/Group 同一种深色牌）
    sub_pl = plate(K, "w1_subtitle", 1000, 52, 5.0, K.black, r=5)
    sub_t = font_obj(K, "How computers help find cancer drug candidates: the CDK20 story", 27, inkw, italic=True, extrude=0.5, bevel=0.1, align="CENTER")
    print("W1_SUBW", round(width_mm(sub_t)), flush=True)
    fit(sub_t, 970, 22)
    put_text_on(sub_pl, sub_t, 0, -9, -2.8)
    subb = Body(sub_pl, "plate", "subtitle")
    subb.slot = Vector((C.x, 0.0, C.z - 40))
    bodies.append(subb)
    # ---- 卫星牌：课程（红）、Section、Group（深灰）、名单（白）
    sats = []
    crs = plate(K, "w1_course", 410, 96, 5.0, K.red, r=8)
    t1 = font_obj(K, "SCIE1007", 36, inkw, extrude=0.6, bevel=0.15, align="CENTER")
    put_text_on(crs, t1, 0, 4, -2.8)
    t2 = font_obj(K, "Molecular Science in Daily Life", 26, inkw, italic=True, extrude=0.5, bevel=0.1, align="CENTER")
    fit(t2, 390, 22)
    put_text_on(crs, t2, 0, -38, -2.8)
    sec = plate(K, "w1_section", 250, 56, 5.0, K.black, r=7)
    put_text_on(sec, font_obj(K, "Section 20007", 30, inkw, extrude=0.6, bevel=0.15, align="CENTER"), 0, -15, -2.8)
    grp = plate(K, "w1_group", 200, 56, 5.0, K.black, r=7)
    put_text_on(grp, font_obj(K, "Group 3B", 30, inkw, extrude=0.6, bevel=0.15, align="CENTER"), 0, -15, -2.8)
    ros = plate(K, "w1_roster", 680, 92, 4.0, K.white, r=6)
    for i, m in enumerate("ABCD"):
        cx, zb = (-330 + 340 * (i % 2)), (6 - 36 * (i // 2))
        if members:
            v = members[m]
            t = font_obj(K, name_case(v["name"]) + ("   " + v["id"] if v["id"] else ""), 26, ink, italic=True, extrude=0.5, bevel=0.1)
            fit(t, 320, 20)
            put_text_on(ros, t, cx, zb, -2.3)
        else:
            pad = plate(K, f"w1_rospad_{m}", 280, 18, 0.6, inkg, r=2)
            pad.parent = ros
            pad.location = ((cx + 140) * MM, -2.3 * MM, (zb + 10) * MM)
    slots = {"course": Vector((C.x, 0, C.z + 200)), "section": Vector((C.x - 190, 0, C.z - 118)),
             "group": Vector((C.x + 190, 0, C.z - 118)), "roster": Vector((C.x, 0, C.z - 205))}
    for nm, ob in (("course", crs), ("section", sec), ("group", grp), ("roster", ros)):
        b = Body(ob, "plate", nm)
        b.slot = slots[nm]
        sats.append(b)
        bodies.append(b)

    for b in parts.values():
        b.sp = SP
    # ---- 环上的槽位：章节牌固定，主角零件挂在牌外侧，其余零件在环带里
    # 字、牌、主角零件在画面里不许被挡：它们之间按 XZ 平面（镜头正对）的距离隔开，不管前后
    taken = [(b.slot, b.r) for b in tags] + [(b.slot, b.r) for b in letters] + [(subb.slot, 0)]

    Dread = (2 * FRAME_HW + 40) * 50.0 / 36.0       # 读字机位到片名平面的距离（mm）

    def proj(p, r):
        """读字机位看过去：p 投到片名平面（y = 0）上的位置和半径（近大远小）。"""
        k = Dread / max(200.0, Dread + p.y)
        return C.x + (p.x - C.x) * k, C.z + (p.z - C.z) * k, r * k

    def free(p, r, pad=10.0):
        px, pz, pr = proj(p, r)
        for q, rq in taken:
            if math.hypot(px - q.x, pz - q.z) < pr + rq + pad:
                return False
        # 环中间留给字和牌：内椭圆
        dx, dz = (px - C.x) / (RING_A * 0.80), (pz - C.z) / (RING_B * 0.80)
        if dx * dx + dz * dz < 1.0:
            return False
        if p.z - r < 140:
            return False
        return True

    def in_frame(p, r):
        return abs(p.x - C.x) + r <= FRAME_HW and abs(p.z - C.z) + r <= FRAME_HH

    hero = {}
    for k, cn in enumerate(CH_HERO):
        b = parts.get(cn)
        if b is None:
            continue
        b.sp = SP_HERO
        tg = tags[k].slot
        out = Vector((tg.x - C.x, 0, tg.z - C.z)).normalized()
        side = Vector((-out.z, 0, out.x))
        best = None
        for d in range(0, 300, 4):
            for ang in (0, 35, -35, 60, -60, 90, -90, 120, -120, 150, -150, 180):
                a = math.radians(ang)
                dirv = out * math.cos(a) + side * math.sin(a)
                p = tg + dirv * (tags[k].r * 0.75 + b.R + 6 + d)
                p.y = 0.0
                if free(p, b.R, 6) and in_frame(p, b.R):
                    best = p
                    break
            if best:
                break
        if best is None:
            raise SystemExit(f"w1z: no hero slot for chapter {k + 1}")
        b.slot = best
        b.arc = 1 if best.z > C.z else -1
        taken.append((best, b.R))
        hero[cn] = k
    rest_parts = [b for cn, b in parts.items() if cn not in hero]
    # 按大板上的 x 排到环上的角度（相邻的还相邻，飞的路线少交叉）
    # 大板后三排（y > 0）→ 环的上半圈，前三排 → 下半圈；左右顺序不变（飞的路线不交叉）
    top_arc = sorted([b for b in rest_parts if b.c0.y > 0], key=lambda b: (b.c0.x, -b.c0.y))
    bot_arc = sorted([b for b in rest_parts if b.c0.y <= 0], key=lambda b: (b.c0.x, b.c0.y))
    band = []                                   # 环带里的普通零件：彼此按三维距离隔开，可以前后错开

    def free3(p, r, pad):
        return all((p - q).length >= r + rq + pad for q, rq in band)
    seq = [(b, 172 - 164 * i / max(1, len(top_arc) - 1), +1) for i, b in enumerate(top_arc)] + \
          [(b, 188 + 164 * i / max(1, len(bot_arc) - 1), -1) for i, b in enumerate(bot_arc)]
    for n_, (b, a_deg, arc) in enumerate(seq):
        a0 = math.radians(a_deg)
        b.arc = arc
        b.front = n_ % 4 == 2                       # 每四件有一件漂在镜头前（前景，虚着，给画面纵深）
        for tries in range(6000):
            spread = 6 + (tries // 300) * 4
            a = a0 + math.radians(rnd.uniform(-spread, spread))
            s = rnd.uniform(0.95, 1.35 + 0.45 * min(1.0, tries / 3000))
            if b.front:
                y = rnd.uniform(-720, -420)
                s *= 0.85
            else:
                y = rnd.uniform(-60, 200) if arc > 0 else rnd.uniform(-200, 60)
            p = Vector((C.x + RING_A * s * math.cos(a), y, C.z + RING_B * s * math.sin(a)))
            if free(p, b.R, 10) and free3(p, b.R, 10):
                break
        else:
            raise SystemExit("w1z: ring slots full")
        b.slot = p
        band.append((p, b.R))

    # ---- 时间：子弹时间（τ 是零件自己的"物理时间"）
    tau = np.zeros(NF)
    for F in range(1, NF):
        u = (F - TAIL) / (FPS * U)
        s = 1.0
        if TL["bt_in"] <= u <= TL["resume"]:
            ramp_in = smooth((u - TL["bt_in"]) / 0.15)
            ramp_out = smooth((u - TL["bt_out"]) / (TL["resume"] - TL["bt_out"]))
            s = 1.0 - 0.9 * ramp_in * (1 - ramp_out)
        tau[F] = tau[F - 1] + (s / FPS if F >= Fu(TL["brk"]) else 0.0)

    f_brk = Fu(TL["brk"])
    f_suck, f_suck_end = Fu(TL["suck"]), Fu(TL["suck_end"])
    # 吸回的顺序：环上低的（离大板近）先回，高的后回，CDK20 最后（u15）——上面的落下来时下面已经空了
    cdk = parts["z3_c4_r0"]
    order = sorted([b for b in parts.values() if b is not cdk], key=lambda b: b.slot.z) + [cdk]
    arr_f = {}
    for i, b in enumerate(order):
        arr_f[b.name] = round(Fu(TL["suck"] + 0.55) + (f_suck_end - Fu(TL["suck"] + 0.55)) * i / (len(order) - 1))

    def spin_axis():
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
        return v.normalized()

    for b in parts.values():
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        ax, w = spin_axis(), rnd.uniform(0.25, 0.7) * (0.4 if b.name in hero else 1.0)
        T = rnd.uniform(2.1, 2.3)                   # 物理时间里飞到槽位用多久
        h1 = rnd.uniform(90, 130)
        p0, p3 = b.c0, b.slot
        if b.arc > 0:                               # 上半圈的从后面上去，下半圈的从前面走，两层不相交
            p1 = p0 + Vector((0, 140, h1))
            p2 = p3 + Vector((0, 150, -60))
        else:
            p1 = p0 + Vector((0, -110, h1 * 0.6))
            p2 = p3 + Vector((0, -120, -40))
        fa = arr_f[b.name]
        fret0 = max(fa - 46, f_suck)
        bob = rnd.uniform(0, 6.28)
        cs = qs = None
        for F in range(NF):
            t = tau[F]
            if F < f_brk:
                c, q = p0, b.q0
            else:
                b.scl[F] = 1 + (b.sp - 1) * smooth((t - 0.25) / 1.3)
                s_ = 0.12 * ease_out3(t / 0.35) + 0.88 * smooth(t / T)     # 断开那一下先弹起一点，之后慢慢浮
                c = bez(p0, p1, p2, p3, s_)
                c = c + Vector((0, 0, 3.0 * math.sin(0.9 * t + bob))) * smooth((t - T * 0.8) / 0.6)
                ang = w * t * smooth(t / 0.5)
                q = Quaternion(ax, ang) @ b.q0
                if F >= fret0:
                    if cs is None:
                        cs, qs = c.copy(), q.copy()
                    v = clamp01((F - fret0) / (fa - fret0))
                    lift = b.c0 + Vector((0, 0, 60))
                    e = ease_in2(v)
                    c = bez(cs, cs + (lift - cs) * 0.4, lift, b.c0, e) if v < 1 else b.c0
                    q = qs.slerp(b.q0, smooth(v)) if v < 1 else b.q0
                    b.scl[F] = b.sp + (1 - b.sp) * smooth(v / 0.6)
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(q)
        b.arrive = fa
    # ---- 章节牌：和零件一起从大板后面升起，背面朝镜头；点亮时转到正面
    for k, b in enumerate(tags):
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        # 牌在自己点亮的那一拍才从暗处（大板后上方）沿 Y 直飞到槽位，落位同时翻到正面——之前不在画面里挡事
        start = Vector((b.slot.x, 1100.0, b.slot.z + 60.0))
        q_back = Quaternion((0, 0, 1), math.pi)
        f_on = Fu(TL["tags"][k // 2])
        f_in = f_on - TAG_FLY
        f_off0 = Fu(TL["suck"])
        for F in range(NF):
            t = tau[F]
            v_in = clamp01((F - f_in) / TAG_FLY)
            c = start.lerp(b.slot, ease_out3(v_in))
            c = c + Vector((0, 0, 2.0 * math.sin(0.8 * t + k))) * smooth((F - f_on) / 30.0)
            if F < f_on - 2:
                q = q_back
            else:
                v = (F - (f_on - 2)) / 16.0
                ang = math.pi * (1 - smooth(v)) + math.radians(-7 * math.sin(math.pi * clamp01((F - f_on - 12) / 10)) if F > f_on + 12 else 0)
                q = Quaternion((0, 0, 1), ang)
            c = away(c, F, f_off0)
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(q)          # 牌的网格本身已经竖起、正面朝 −Y：单位四元数 = 正面朝镜头
        b.f_on = f_on
        hide_before(b.o, f_in - 1)
        hide_after(b.o, f_off0 + AWAY_N)
        b.vis = (f_in, f_off0 + AWAY_N)
    # ---- 字母：挂在料杆上（背面朝镜头）→ 剪 → 翻半圈落位 → 定住 → 吸走
    f_rod0, f_rod1 = Fu(TL["rod_in"]), Fu(TL["rod_set"])
    f_rodout = Fu(TL["rod_out"])
    rod_y = 420.0

    def rod_x(F):
        if F < f_rod0:
            return C.x + 2200
        if F < f_rod1:
            return C.x + 2200 * (1 - ease_out3((F - f_rod0) / (f_rod1 - f_rod0)))
        if F < f_rodout:
            return C.x + 6 * math.sin((F - f_rod1) / 23)
        return C.x - 2600 * ease_in2((F - f_rodout) / 50.0)
    rod_pos = np.array([(rod_x(F), rod_y, rod_z) for F in range(NF)])
    fast_bake(rod, "location", rod_pos * MM)
    pairs = []
    L = letters[:-1]
    lo, hi = 0, len(L) - 1
    while lo <= hi:
        pairs.append([L[lo]] + ([L[hi]] if hi != lo else []))
        lo += 1
        hi -= 1
    cut_f = {}
    for i, grp_ in enumerate(pairs):
        for b in grp_:
            cut_f[b.name] = Fu(TL["cuts"][min(i, len(TL["cuts"]) - 1)])
    cut_f[letters[-1].name] = Fu(TL["q_cut"])
    q_face = Quaternion((1, 0, 0), math.radians(90))
    q_rev = Quaternion((0, 0, 1), math.pi) @ q_face
    flash_specs = []
    for n, b in enumerate(letters):
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        fc = cut_f[b.name]
        fl = fc + (round(FPS * U * (TL["q_land"] - TL["q_cut"])) if b.ch == "?" else round(FPS * U * 0.5))
        b.cut, b.land = fc, fl
        top_off = Quaternion(q_rev) @ b.c_local / MM
        f_off0 = Fu(TL["suck"])
        for F in range(NF):
            hang_c = Vector((rod_pos[F][0] + b.hang_dx, rod_y, rod_z - 32 - b.half[1] + 1.0))   # 字顶咬住浇口尖 1 mm
            if F < fc:
                c, q = hang_c, q_rev
                # 剪之前料杆进场时字母跟着轻晃
            else:
                v = (F - fc) / max(1, fl - fc)
                h0 = Vector(b.cen[fc - 1])
                if v < 1:
                    # 前 70 %：飞到槽位正前方 60 mm（翻完半圈）；后 30 %：只沿 Y 直插进槽位（XZ 轮廓和落位时一样，碰不到邻字）
                    # 前半段从已落位的字上方翻过去（Zt 高于片名顶），再在字前面 60 mm 的平面里落下来
                    stage = b.slot + Vector((0, -60, 0))
                    zt = C.z + 200
                    way = [h0, Vector((h0.x, 200, h0.z + 20)), Vector((C.x + ((h0.x + stage.x) / 2 - C.x) * 0.88, 50, zt)),
                           Vector((stage.x, -60, zt - 20)), stage]
                    if v < 0.7:
                        c = catmull(way, smooth(v / 0.7))
                    else:
                        c = stage.lerp(b.slot, ease_in2((v - 0.7) / 0.3))
                    q = Quaternion((0, 0, 1), math.pi * (1 - smooth(v / 0.62))) @ q_face
                else:
                    k = F - fl
                    over = 4.0 * math.sin(math.pi * k / 8) if k <= 8 else (1.2 * math.sin(math.pi * (k - 8) / 6) if k <= 14 else 0.0)
                    c = b.slot + Vector((0, -over, 0))
                    q = q_face
            c = away(Vector(c), F, f_off0)
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(q)
        hide_after(b.o, f_off0 + AWAY_N)
        b.vis = (0, f_off0 + AWAY_N)
        flash_specs.append((fc, Vector((rod_pos[fc][0] + b.hang_dx, rod_y, rod_z - 32))))
    # ---- 副标题：从后面转着进来
    f_s0, f_s1 = Fu(TL["sub_in"]), Fu(TL["sub_land"])
    subb.cen = np.zeros((NF, 3))
    subb.quat = np.zeros((NF, 4))
    s_start = Vector((C.x + 60, 340.0, C.z - 180))
    for F in range(NF):
        v = clamp01((F - f_s0) / (f_s1 - f_s0))
        s_ = smooth(v)
        c = bez(s_start, s_start + Vector((0, -120, 60)), subb.slot + Vector((0, 120, -40)), subb.slot, s_)
        q = Quaternion((0, 0, 1), math.radians(150) * (1 - s_)) @ Quaternion((1, 0, 0), math.radians(25 * (1 - s_)))
        c = away(c, F, Fu(TL["suck"]))
        subb.cen[F] = tuple(c)
        subb.quat[F] = tuple(q)
    hide_before(sub_pl, f_s0 - 1)
    hide_after(sub_pl, Fu(TL["suck"]) + AWAY_N)
    subb.vis = (f_s0, Fu(TL["suck"]) + AWAY_N)
    # ---- 卫星：在环前面（y = −215，环带最前沿以外）绕一圈，再退到 y = 0 落位；身后拖一条细光迹
    trails = []
    f_sat0 = Fu(TL["sat_in"])
    for i, b in enumerate(sats):
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        fl = Fu(TL["sat_land"][i])
        th1 = math.atan2((b.slot.z - C.z) / 0.5, (b.slot.x - C.x))
        th0 = th1 + math.radians(330 + 25 * i)
        ao, bo = 560.0, 290.0
        y_orb = -250.0 - 30.0 * i
        pts_tr = []
        for F in range(NF):
            v = clamp01((F - f_sat0) / (fl - f_sat0))
            s_ = smooth(v)
            th = th0 + (th1 - th0) * s_
            ring = Vector((C.x + ao * math.cos(th), y_orb, C.z + bo * math.sin(th)))
            back = smooth((v - 0.75) / 0.25)
            c = ring.lerp(Vector((b.slot.x, y_orb, b.slot.z)), smooth((v - 0.45) / 0.30))
            c.y = y_orb * (1 - back)
            if v >= 1:
                k = F - fl
                c = b.slot + Vector((0, -2.5 * math.sin(math.pi * k / 8) if k <= 8 else 0.0, 0))
            c = away(c, F, Fu(TL["suck"]))
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(Quaternion())
            if f_sat0 <= F <= fl:
                pts_tr.append(tuple(c))
        hide_before(b.o, f_sat0 - 1)
        hide_after(b.o, Fu(TL["suck"]) + AWAY_N)
        b.vis = (f_sat0, Fu(TL["suck"]) + AWAY_N)
        trails.append(make_trail(f"w1_trail_{i}", pts_tr, f_sat0, fl))
    # ---- 零件和章节牌飞行时互相让一让（位置迭代：凸包相交就沿两心连线各推 1.5 mm，推开量逐帧衰减并平滑）
    movers = list(parts.values()) + tags
    t_sep = time.time()
    n_push = separate(movers, f_brk, Fu(TL["read"]), fixed=letters) + separate(movers, f_suck, NF)
    print(f"W1_SEPARATE pushes={n_push} {time.time() - t_sep:.0f}s", flush=True)
    # ---- 烘焙所有物体
    for b in bodies:
        b.bake()
    # ---- 剪口闪一点白、大板断开时浇口迸出的灰尘
    flash_mat = emit_mat("w1_flash", 18.0)
    for i, (fc, p) in enumerate(flash_specs):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=2.2 * MM, subdivisions=2, location=p * MM)
        o = bpy.context.object
        o.name = f"w1_cutflash_{i}"
        o.data.materials.append(flash_mat)
        sc_ = np.zeros((NF, 3))
        for F in range(fc - 1, min(NF, fc + 6)):
            sc_[F] = [math.sin(math.pi * clamp01((F - fc + 1) / 6))] * 3
        sc_ = np.maximum(sc_, 1e-4)
        fast_bake(o, "scale", sc_)
        o.visible_shadow = False
    dust(root, cells, tau, f_brk, rnd)
    # ---- 体积光：一盏侧逆光聚光灯穿过零件群，薄雾只在 W1 里
    vol, beam = volume_and_beam(sc, f_brk, f_suck_end)
    # 光束不打片名字母：字顶被侧逆光直射会冲到 1.0（灯光链接：排除）
    ex = bpy.data.collections.new("w1_beam_exclude")
    for b_ in letters:
        for m_ in [b_.o] + list(b_.o.children_recursive):
            ex.objects.link(m_)
    beam.light_linking.receiver_collection = ex
    for it in ex.collection_objects:
        it.light_linking.link_state = "EXCLUDE"
    mood(sc, f_brk, Fu(TL["brk"] + 0.6), Fu(TL["suck"] + 0.5), Fu(TL["suck_end"] + 0.4))

    # ---- 镜头
    cam = D.camera(sc, (0, 0, 0), 1, 30, 0)
    lens = 50.0
    mapc = cells["z1_c1_r4"]
    mpart = parts["z1_c1_r4"]
    mc = mpart.c0
    rise = S.W111["Kong_end"] - (S.L111 - TAIL)
    z2 = parts["z2_c3_r0"]
    ztag = S.zone_tag(root, 2)
    tc = BG.center(ztag[0]) / MM
    z2t = ((z2.c0.x + tc.x) / 2, z2.c0.y * 0.6 + tc.y * 0.4, (z2.c0.z + tc.z) / 2)
    ring_w = 2 * FRAME_HW + 40                  # 读字机位：八块牌、主角零件都在 FRAME_HW × FRAME_HH 里（槽位时就按这个框排的）
    st = S.state
    keys = [(0, st((mc.x, mc.y, mc.z), 52.0, -14.0, 176.0, lens), "stop"),
            (rise, st((mc.x + 3.0, mc.y + 1.0, mc.z), 50.0, -14.0, 170.0, lens), "stop"),
            (Fu(0.75), st((-240.0, -10.0, 55.0), 18.0, -36.0, 300.0, lens), "pass"),   # 起身放慢：接点（TAIL）两侧相邻帧 SSIM 要过 T4
            (Fu(TL["brk"]), st((-140.0, 0.0, 60.0), 13.0, -32.0, 330.0, lens), "pass"),
            (Fu(TL["bt_in"]), st((-4.0, 0.0, 190.0), 14.0, -30.0, 430.0, lens), "pass"),
            (Fu(TL["bt_out"]), st((-4.0, 0.0, 250.0), 12.0, 90.0, 470.0, lens), "pass"),
            (Fu(TL["rod_set"] + 0.5), st((C.x, 0.0, C.z + 50), 3.0, 0.0, 1100.0, lens), "pass"),
            (Fu(TL["q_land"]), st((C.x, 0.0, C.z + 45), 2.0, 0.0, 980.0, lens), "pass"),
            (Fu(TL["read"]), st((C.x, 0.0, C.z), 1.0, 0.0, ring_w, lens), "stop"),
            (Fu(TL["read_end"]), st((C.x, 0.0, C.z), 1.0, 0.0, ring_w * 0.975, lens), "stop"),
            (Fu(TL["suck"] + 0.85), st((C.x, 0.0, C.z - 230), 14.0, -8.0, ring_w * 1.08, lens), "pass"),   # 先看零件往下"倒灌"回大板
            (Fu(TL["suck_end"]), st(tuple(cdk.c0 + Vector((0, 0, 8))), 36.0, -18.0, 330.0, lens), "pass"),
            (TAIL + NF_W1, st(z2t, 30.0, -15.0, 235.0, lens), "pass"),
            (NF - 1, st((z2t[0] + 2.0, z2t[1], z2t[2]), 30.5, -15.5, 235.0 * 0.95, lens), "stop")]
    tr = S.Track(keys)
    poses, focus = [], []
    for F in range(NF):
        tx, ty, tz, pitch, az, ld = tr.at(F)
        hand = Vector((math.sin(F / 23) * 0.35 + math.sin(F / 9.7) * 0.12, math.cos(F / 31) * 0.3, math.sin(F / 17) * 0.25))
        loc, q = S.cam_pose(Vector((tx, ty, tz)) + hand, pitch, az, math.exp(ld))
        q = q @ Quaternion((0, 0, 1), math.radians(0.12 * math.sin(F / 19)))        # 手持感 ≤ 0.3°
        for fk, amp in ((Fu(TL["brk"]), 2.0), (Fu(TL["suck_end"]), 1.2)):           # 冲击帧 2 帧微震
            k = F - fk
            if 0 <= k <= 2:
                loc = loc + Vector((0, 0, amp * MM * (1 if k == 0 else -0.6 if k == 1 else 0.2)))
        poses.append((loc, q))
        focus.append(Vector((tx, ty, tz)) * MM if F >= rise else mpart.o.matrix_world @ Vector((6 * MM, 3 * MM, 3 * MM)))
    fd = S.bake_camera(cam, sc, poses, lens, 2.8, focus)
    # 光圈：1-11 尾 f/8（跟原来的板面镜头一样深），子弹时间 f/2，读字 f/4，回板面 f/8
    fs = []
    for F in range(NF):
        u = (F - TAIL) / (FPS * U)
        v = 8.0
        for (ua, ub, a, b_) in ((0.2, 1.4, 8.0, 2.0), (2.9, 4.0, 2.0, 4.0), (13.5, 15.5, 4.0, 8.0)):
            if u >= ua:
                v = a + (b_ - a) * smooth((u - ua) / (ub - ua))
        fs.append(v)
    fast_bake(cam.data.dof, "aperture_fstop", fs)
    # ---- 扫光（拍 3.5）：一条长灯从左到右扫过字面
    sweep_light(sc, Fu(TL["sweep"]), Fu(TL["sweep"] + 0.5))
    # ---- 引导：八块牌点亮时的轮廓光（05：焦点点名 + 轮廓光；这里牌都在同一焦平面，焦点已在上面）
    rims = {}
    for b in tags:
        it = S.plan_item(f"w1z_tag{b.k}", f"tag{b.k}", b.f_on + 8, Fu(TL["read"]) + 30, rise=18, relax=36)
        rims[it["id"]] = S.rim(it, [b.o], cam, sc, args.rim_w1 * 2.5)
    # 1-11 尾：地图预颤（和盒盖版一样）
    ffl = S.W111["Hong"] - (S.L111 - TAIL)
    it = S.plan_item("w1_map", "map", ffl, rise + 10)
    S.rim(it, [mpart.o], cam, sc, args.rim_w1 * 0.25)
    BG.guide_tick(mpart.o, [g for g in D.gates_of(mapc) if not g.name.endswith("_spur")], D.loop_of(mapc), ffl, rot_deg=0.8)

    for o in bpy.data.objects:                  # 雾只散射光束（轮廓光、扫光是后加的，这里再过一遍）
        if o.type == "LIGHT" and o.name != "w1_beam":
            o.visible_volume_scatter = False
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.frame_set(0)
    # ---- 检查
    chk = dict(part="w1z", nf=NF, bpm=S.BPM, unit_s=U, tl=TL, tail=TAIL, head=HEAD, nf_w1=NF_W1, final=bool(args.final),
               bodies=len(bodies), parts=len(parts), ring_width_mm=round(ring_w, 1),
               events=events_table(letters, tags, sats, subb, cdk, f_brk),
               focus_m=[round(v, 4) for v in fd], cam_loc_mm=[[round(c / MM, 2) for c in p[0]] for p in poses],
               build_s=round(time.time() - t0, 1))
    chk["clip"] = clip_check(bodies, rod, rod_pos)
    chk["cam_clear_mm"] = cam_clear(bodies, poses)
    chk["px"] = text_px(sc, cam, letters, tags, sats, subb)
    chk["title_box"] = title_box(sc, cam, letters, [Fu(TL["q_land"]) + 20, Fu(TL["read"]) + 20, Fu(TL["read"]) + 120])
    return cam, chk


AWAY_N = 52
TAG_FLY = 40


def away(c, F, f0):
    """吸走：先沿 +Y 直着往后退（在镜头正对的平面上不挪，所以碰不到环上的零件），再往上出画，之后隐藏。"""
    if F < f0:
        return c
    e1 = ease_in2((F - f0) / 24.0)
    e2 = ease_in2((F - f0 - 14) / 34.0)
    return c + Vector((0, 700 * e1, 800 * e2))


def hide_after(o, f):
    for m in [o] + list(o.children_recursive):
        for F, v in ((f, False), (f + 1, True)):
            m.hide_render = v
            m.keyframe_insert("hide_render", frame=F)


def hide_before(o, f):
    for m in [o] + list(o.children_recursive):
        for F, v in ((0, True), (f, True), (f + 1, False)):
            m.hide_render = v
            m.keyframe_insert("hide_render", frame=F)


def emit_mat(name, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    e.inputs["Color"].default_value = (1, 0.97, 0.92, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def make_trail(name, pts, f0, f1):
    """卫星身后的细光迹：沿路径的细管，bevel_factor 头追尾，落位时整条收掉。"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    pts = pts[::2] if len(pts) > 4 else pts
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1)
    cu.bevel_depth = 0.5 * MM
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(emit_mat(name + "_m", 3.0))
    o.visible_shadow = False
    end, start = [], []
    for F in range(NF):
        v = clamp01((F - f0) / max(1, f1 - f0))
        end.append(v)
        start.append(max(0.0, min(v, v - 0.35)) if F < f1 else min(1.0, 1.0))
    cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = "SPLINE"
    fast_bake(cu, "bevel_factor_end", end)
    fast_bake(cu, "bevel_factor_start", start)
    return o


def dust(root, cells, tau, f_brk, rnd):
    """大板断开那一下，浇口迸出的细灰（白色小颗粒，体积光里看得到），按 τ 走，子弹时间里几乎停住。"""
    m = D.mat_solid("w1_dust", "#F7F3EA", rough=0.6, coat=0.0, sss=0)
    gates = [g for c in cells.values() for g in D.gates_of(c) if not g.name.endswith("_spur")]
    rnd.shuffle(gates)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=1)
    base = bpy.context.object
    base.data.materials.append(m)
    me = base.data
    bpy.data.objects.remove(base)
    for i, g in enumerate(gates[:180]):
        p0 = g.matrix_world.translation / MM
        for j in range(2):
            o = bpy.data.objects.new(f"w1_dust_{i}_{j}", me)
            bpy.context.scene.collection.objects.link(o)
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), abs(rnd.gauss(0, 1)) + 0.8)).normalized() * rnd.uniform(60, 220)
            r = rnd.uniform(0.35, 0.8)
            loc = np.zeros((NF, 3))
            scl = np.zeros((NF, 3))
            for F in range(NF):
                t = tau[F]
                dt = t if F >= f_brk else 0.0
                p = p0 + v * (1 - math.exp(-dt * 1.6)) / 1.6
                loc[F] = tuple(p * MM)
                life = 1.0 - smooth((dt - 1.0) / 0.8)
                scl[F] = [r * MM * (life if F >= f_brk else 0.0001)] * 3
            fast_bake(o, "location", loc)
            fast_bake(o, "scale", np.maximum(scl, 1e-7))
            o.visible_shadow = False


def volume_and_beam(sc, f0, f1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.1, 0.7))
    v = bpy.context.object
    v.name = "w1_haze"
    v.dimensions = (3.2, 3.0, 1.6)
    m = bpy.data.materials.new("w1_haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    v.data.materials.append(m)
    dens = []
    for F in range(NF):
        a = smooth((F - f0) / 30.0) * (1 - smooth((F - (f1 - 30)) / 50.0))
        dens.append(DENS * a)
    fast_bake(pv.inputs["Density"], "default_value", dens)
    sc.cycles.volume_step_rate = 4.0
    sc.cycles.volume_bounces = 0
    bpy.ops.object.light_add(type="SPOT", location=(-0.95, 1.05, 1.55))
    L = bpy.context.object
    L.name = "w1_beam"
    L.data.spot_size = math.radians(26)
    L.data.spot_blend = 0.35
    L.data.shadow_soft_size = 0.02
    L.data.energy = 0.0
    for o in bpy.data.objects:                  # 雾只散射这一束光：别的灯不进体积，画面不发灰
        if o.type == "LIGHT" and o is not L:
            o.visible_volume_scatter = False
    L.data.color = (1.0, 0.96, 0.9)
    L.rotation_euler = (Vector((0.05, -0.1, 0.45)) - L.location).to_track_quat("-Z", "Y").to_euler()
    en = []
    for F in range(NF):
        a = smooth((F - f0) / 20.0) * (1 - smooth((F - (f1 - 30)) / 50.0))
        en.append(BEAM_W * a)
    fast_bake(L.data, "energy", en)
    return v, L


DENS, BEAM_W = 0.16, 6000.0
MOOD = dict(world=0.20, key=0.40, fill=0.35, strip=0.30, rim=1.0, softbox=0.50, cards=0.30, backdrop=0.30)
FRONT_W = 420.0                            # 零重力段的正面柔光（镜头后方），片名正面亮、顶面不冲


def mood(sc, f0, f1, f2, f3):
    """零重力那一段把影棚灯压暗（背景变深灰，镀铬和白牌才跳出来，光束看得见），回板时再亮回原样接 2-01。"""
    def m(F, lvl):
        a = smooth((F - f0) / max(1, f1 - f0)) * (1 - smooth((F - f2) / max(1, f3 - f2)))
        return 1 + (lvl - 1) * a
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name in MOOD:
            e0 = o.data.energy
            fast_bake(o.data, "energy", [e0 * m(F, MOOD[o.name]) for F in range(NF)])
    bg = sc.world.node_tree.nodes["Background"].inputs[1]
    b0 = bg.default_value
    fast_bake(bg, "default_value", [b0 * m(F, MOOD["world"]) for F in range(NF)])
    for nm in ("refl_top", "refl_left"):
        st = bpy.data.objects[nm].active_material.node_tree.nodes["Emission"].inputs["Strength"]
        s0 = st.default_value
        fast_bake(st, "default_value", [s0 * m(F, MOOD["cards"]) for F in range(NF)])
    bpy.ops.object.light_add(type="AREA", location=(C.x * MM, -2.7, C.z * MM + 0.35))
    fr = bpy.context.object
    fr.name = "w1_front"
    fr.data.shape = "RECTANGLE"
    fr.data.size, fr.data.size_y = 1.8, 1.0
    fr.data.color = (1, 0.975, 0.95)
    fr.rotation_euler = (Vector((C.x * MM, 0, C.z * MM)) - fr.location).to_track_quat("-Z", "Y").to_euler()
    fr.visible_camera = False
    fast_bake(fr.data, "energy", [FRONT_W * (m(F, 0.0) - 1) / -1 for F in range(NF)])
    # 背景布本身也压暗（影棚"关灯"），2-01 前恢复
    bc = bpy.data.materials["backdrop"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    c0 = np.array(bc.default_value)
    fast_bake(bc, "default_value", [np.r_[c0[:3] * m(F, MOOD["backdrop"]), c0[3]] for F in range(NF)])


def sweep_light(sc, f0, f1):
    bpy.ops.object.light_add(type="AREA", location=(0, -1.2, 1.0))
    L = bpy.context.object
    L.name = "w1_sweep"
    L.data.shape = "RECTANGLE"
    L.data.size, L.data.size_y = 0.05, 1.4
    L.data.color = (1, 0.98, 0.95)
    L.rotation_euler = (math.radians(90), 0, 0)
    loc, en = [], []
    for F in range(NF):
        v = clamp01((F - f0) / (f1 - f0))
        loc.append(((-1.4 + 2.8 * smooth(v)) , -0.9, C.z * MM + 0.15))
        en.append(260.0 * math.sin(math.pi * v) if 0 < v < 1 else 0.0)
    fast_bake(L, "location", loc)
    fast_bake(L.data, "energy", en)
    L.visible_camera = False


def events_table(letters, tags, sats, subb, cdk, f_brk):
    ev = [dict(id="break", u=TL["brk"], f=f_brk, what="大板断开，零件脱离浇口，重力关掉")]
    for b in letters:
        ev.append(dict(id=f"cut_{b.name}", f=b.cut, what=f"剪下 {b.ch}"))
        ev.append(dict(id=f"land_{b.name}", f=b.land, what=f"{b.ch} 落位"))
    for b in tags:
        ev.append(dict(id=f"tag_{b.k}", f=b.f_on, what=f"第 {b.k + 1} 块章节牌转正"))
    ev.append(dict(id="cdk_last", f=Fu(TL["suck_end"]), what="CDK20 最后插回浇口"))
    ev.append(dict(id="land_2_01", f=TAIL + NF_W1, what="落在第 2 区楼群，2-01 开始"))
    return ev


def _hull_tree(b, f, cen=None):
    if b.hv is None:
        return None
    R = np.array(Quaternion(b.quat[f]).to_matrix())
    k = b.scl[f]
    loc = np.array(b.cen[f] if cen is None else cen) * MM - R @ (np.array(b.c_local) * k)
    vw = (b.hv * k) @ R.T + loc
    return BVHTree.FromPolygons([tuple(x) for x in vw], b.hf)


def separate(movers, F0, F1, step=1.5, iters=12, decay=0.94, fixed=()):
    """逐帧：把上一帧的推开量衰减后加上，再查凸包相交，相交的两件沿两心连线各推 step mm，直到不相交。推开量逐帧衰减（像弹簧），不再另做平滑。"""
    n = len(movers)
    allb = list(movers) + list(fixed)              # fixed：只挡别人、自己不让（字母挂在料杆上）
    radF = np.stack([b.r * b.scl for b in allb])
    vis = [getattr(b, "vis", (0, NF)) for b in allb]
    off = np.zeros((n, 3))
    OFF = np.zeros((NF, n, 3))
    pushes = 0
    for F in range(F0, min(F1, NF)):
        off *= decay
        P = np.stack([b.cen[F] for b in allb])
        P[:n] += off
        live = np.array([v[0] <= F <= v[1] for v in vis])
        rad = radF[:, F]
        for _ in range(iters):
            d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
            cand = np.argwhere(np.triu(d < (rad[:, None] + rad[None, :]), 1))
            trees, moved = {}, False
            for i, j in cand:
                if not (live[i] and live[j]):
                    continue
                if i >= n and j >= n:
                    continue
                for a in (i, j):
                    if a not in trees:
                        trees[a] = _hull_tree(allb[a], F, P[a])
                if trees[i] is None or trees[j] is None or not trees[i].overlap(trees[j]):
                    continue
                v = P[i] - P[j]
                v = v / (np.linalg.norm(v) + 1e-9)
                wi, wj = (1.0, 1.0) if j < n else (2.0, 0.0)
                P[i] += v * step * wi
                P[j] -= v * step * wj
                off[i] += v * step * wi
                if j < n:
                    off[j] -= v * step * wj
                trees.pop(i)
                trees.pop(j)
                moved = True
                pushes += 1
            if not moved:
                break
        OFF[F] = off
    for i, b in enumerate(movers):
        b.cen += OFF[:, i, :]
    return pushes


def clip_check(bodies, rod, rod_pos, step=2):
    """会动的东西两两之间（凸包）是否重叠：先用包围球筛，再建凸包 BVH 查。返回重叠的 (a, b, 帧数, 第一帧)。"""
    N = len(bodies)
    cen = np.stack([b.cen for b in bodies])           # (N, NF, 3)
    radF = np.stack([b.r * b.scl for b in bodies])
    hits = {}
    # 同一张牌/卫星的子物体本来就贴在一起；牌和自己的字不算。凸包对凹的零件偏保守，所以先报，再看
    for F in range(0, NF, step):
        P = cen[:, F, :]
        rad = radF[:, F]
        d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
        cand = np.argwhere(np.triu(d < (rad[:, None] + rad[None, :]), 1))
        trees = {}
        for i, j in cand:
            vi, vj = getattr(bodies[i], "vis", (0, NF)), getattr(bodies[j], "vis", (0, NF))
            if not (vi[0] <= F <= vi[1] and vj[0] <= F <= vj[1]):
                continue
            for a in (i, j):
                if a not in trees:
                    trees[a] = _hull_tree(bodies[a], F)
            if trees[i] is not None and trees[j] is not None and trees[i].overlap(trees[j]):
                key = (bodies[i].name, bodies[j].name)
                h = hits.setdefault(key, [0, F])
                h[0] += 1
    return [[a, b, n, f] for (a, b), (n, f) in sorted(hits.items(), key=lambda x: x[1][1])]


def cam_clear(bodies, poses):
    cen = np.stack([b.cen for b in bodies])
    radF = np.stack([b.r * b.scl for b in bodies])
    vis = [getattr(b, "vis", (0, NF)) for b in bodies]
    worst = (1e9, -1, "")
    for F in range(NF):
        cl = np.array(poses[F][0]) / MM
        d = np.linalg.norm(cen[:, F, :] - cl, axis=1) - radF[:, F]
        d = np.where([v[0] <= F <= v[1] for v in vis], d, 1e9)
        i = int(np.argmin(d))
        if d[i] < worst[0]:
            worst = (float(d[i]), F, bodies[i].name)
    return dict(min_mm=round(worst[0], 1), frame=worst[1], body=worst[2])


def cap_px(sc, cam, ob, cap):
    bpy.context.view_layer.update()
    mw = ob.matrix_world
    xs = [min(v[0] for v in ob.bound_box), max(v[0] for v in ob.bound_box)]
    res = []
    for x in (xs[0], (xs[0] + xs[1]) / 2, xs[1]):
        p0 = mw @ Vector((x, 0, 0))
        up = (mw.to_3x3() @ Vector((0, 1, 0))).normalized() * cap * MM
        a, b = world_to_camera_view(sc, cam, p0), world_to_camera_view(sc, cam, p0 + up)
        res.append(math.hypot((b.x - a.x) * 1920, (b.y - a.y) * 1080))
    return round(sum(res) / 3, 1)


def text_px(sc, cam, letters, tags, sats, subb):
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    out = {}
    for lbl, F in (("title_landed", Fu(TL["q_land"]) + 20), ("read", Fu(TL["read"]) + 30)):
        sc.frame_set(F)
        d = {"title": min(cap_px(sc, cam, b.o, CAP_TITLE) for b in letters if b.ch not in "?")}
        fonts = lambda o: [m for m in o.children_recursive if m.type == "FONT"]          # noqa: E731
        d["subtitle"] = min(cap_px(sc, cam, m, m["cap_mm"]) for m in fonts(subb.o))
        for b in sats:
            fs = fonts(b.o)
            if fs:
                d[b.name] = min(cap_px(sc, cam, m, m["cap_mm"]) for m in fs)
        tf = [m for b in tags for m in fonts(b.o) if not m.data.body.startswith("No.")]
        if tf:
            d["tags_min"] = min(cap_px(sc, cam, m, m["cap_mm"]) for m in tf)
            d["tag_names_min"] = min([cap_px(sc, cam, m, m["cap_mm"]) for m in tf if m.data.font and "Italic" in m.data.font.filepath] or [0])
        out[lbl] = d
    return out


def title_box(sc, cam, letters, frames):
    out = {}
    for F in frames:
        sc.frame_set(F)
        bpy.context.view_layer.update()
        pts = [world_to_camera_view(sc, cam, b.o.matrix_world @ Vector(c)) for b in letters for c in b.o.bound_box]
        x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
        y0, y1 = 1 - max(p.y for p in pts), 1 - min(p.y for p in pts)
        out[str(F)] = [round(max(0, x0) * 1920), round(max(0, y0) * 1080), round(min(1, x1) * 1920), round(min(1, y1) * 1080)]
    return out
