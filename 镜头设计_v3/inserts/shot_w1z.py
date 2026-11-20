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
import os
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
TAG_W, TAG_H, TAG_T = 270.0, 150.0, 3.0    # 章节牌：亮面塑料，厚 3 mm
FRAME_HW, FRAME_HH = 830.0, 462.0          # 读字机位下画面的半宽、半高（mm，片名平面上）
CAP_TITLE = 92.0                           # 英雄帧（画宽 1150 mm）里片名字高 ≥ 140 px
SP_HERO = 2.4                              # 挂在章节牌旁边的主角零件小一点，好排
SP = 3.1                                   # 零件离开大板后放大到 3 倍多（零重力里"浮肿"开，环才撑得起片名），回板时缩回原大
HERO_X, HERO_Z = 0.92, 0.70                # 英雄帧时零件环收紧（围住片名），第②③拍随镜头拉开涨回读字环
HERO_W = 1150.0                            # 英雄帧画宽（片名平面上，mm）

# 逐拍表（单位 u；W1 第 0 帧 = 1-11 最后一帧之后）
# 11-21 第二轮：信息分三拍——①英雄帧（只有片名 + 副标题 + 零件群，1.5 s）②课程、Section、Group 依次入画 ③拉开到读字全景，八块牌上环
TL = dict(skim=0.0, brk=1.0, bt_in=1.5, bt_out=2.5, resume=2.6, rod_in=2.4, rod_set=3.0, sweep=3.0,
          cuts=[3.5, 3.75, 4.0, 4.25, 4.5, 4.75], q_cut=5.25, q_land=5.75, rod_out=5.4,
          sub_in=5.4, sub_land=6.0, hero=5.75, sweep2=6.2, hero_end=7.25, expand_end=9.0,
          sat_in=[7.25, 7.45, 7.65, 8.1], sat_land=[7.85, 8.05, 8.25, 8.7],
          tags=[8.5, 8.75, 9.0, 9.25], read=9.5, read_end=13.5, suck=13.5, suck_end=15.0, land=17.0)


def Fu(u):
    """拍单位 → w1z 序列帧。"""
    return TAIL + round(FPS * U * u)


def hero_pos(p):
    """读字环上的点 → 英雄帧时收紧环上的点（XZ 向片名中心缩，Y 不变）。"""
    return Vector((C.x + (p.x - C.x) * HERO_X, p.y, C.z + (p.z - C.z) * HERO_Z))


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
        if np.ptp(self.scl) > 1e-6 or abs(self.scl[0] - 1) > 1e-6:
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
    tag_mat = D.mat_solid("w1_tag_gloss", "#EEEAE3", rough=0.1, coat=0.9, sss=0.02)     # 亮面塑料牌：倒角边吃高光
    yf = -(TAG_T / 2 + 0.3)                                                             # 字贴在牌面上
    for k in range(8):
        hw, hh = TAG_W / 2, TAG_H / 2
        pl = plate(K, f"w1_tag_{k}", TAG_W, TAG_H, TAG_T, tag_mat, r=8)
        num = font_obj(K, str(k + 1), 40, K.red, extrude=0.6, bevel=0.15)
        put_text_on(pl, num, -hw + 14, 16, yf)
        tt = font_obj(K, CH_TITLES[k], 26, ink, extrude=0.5, bevel=0.1)
        if width_mm(tt) <= TAG_W - 70:
            put_text_on(pl, tt, -hw + 52, 16, yf)
        else:                                   # 长章名折成两行（"How much did / computers help?"）
            bpy.data.objects.remove(tt)
            w = CH_TITLES[k].split()
            cut = min(range(1, len(w)), key=lambda i: abs(len(" ".join(w[:i])) - len(" ".join(w[i:]))))
            for li, (line, zb) in enumerate(((" ".join(w[:cut]), 46), (" ".join(w[cut:]), 16))):
                t2_ = font_obj(K, line, 25, ink, extrude=0.5, bevel=0.1)
                fit(t2_, TAG_W - 70, 25)
                put_text_on(pl, t2_, -hw + 52, zb, yf)
        ln = plate(K, f"w1_tag_rule_{k}", TAG_W - 28, 1.2, 0.6, inkg, r=0.4)
        ln.parent = pl
        ln.location = (0, yf * MM, 3 * MM)
        # 牌挂在一小段料杆上：顶边正中一个细浇口 + 一截横着的料杆头（和大板同一种镀铬）
        bpy.ops.mesh.primitive_cone_add(radius1=1.0 * MM, radius2=2.2 * MM, depth=14 * MM, vertices=16, location=(0, 0, (hh + 6.5) * MM))
        g = bpy.context.object
        g.name = f"w1_tag_gate_{k}"
        bpy.ops.object.shade_smooth()
        g.data.materials.append(chrome)
        g.parent = pl
        bpy.ops.mesh.primitive_cylinder_add(radius=2.6 * MM, depth=70 * MM, vertices=24, location=(0, 0, (hh + 15.5) * MM), rotation=(0, math.radians(90), 0))
        g = bpy.context.object
        g.name = f"w1_tag_runner_{k}"
        bpy.ops.object.shade_smooth()
        g.data.materials.append(chrome)
        g.parent = pl
        names = ["All four of us"] if k == 0 else [(name_case(members[m]["name"]) if members else None) for m in CH_PEOPLE[k]]
        two = len(names) > 1
        for j, nm in enumerate(names):
            # 一行名字：字高 28、基线 -32；两行：字高 25、行距 34（= 1.36 倍字高，斜体 g/y 下伸不碰下一行大写）
            z = (-29 - 34 * j) if two else -32
            if nm:
                t = font_obj(K, nm, 25 if two else 28, ink, italic=True, extrude=0.5, bevel=0.1)
                fit(t, TAG_W - 30, 21)
                put_text_on(pl, t, -hw + 14, z, yf)
            else:
                pad = plate(K, f"w1_namepad_{k}_{j}", 170, 18, 0.6, inkg, r=2)
                pad.parent = pl
                pad.location = ((-hw + 14 + 85) * MM, yf * MM, (z + 10) * MM)
        # 背面：大号红色章节号（飞进来转面时看到的是号码，不是空白牌）
        bk = font_obj(K, str(k + 1), 92, K.red, extrude=0.8, bevel=0.2, align="CENTER")
        bk.parent = pl
        bk.location = (0, -yf * MM, -46 * MM)
        bk.rotation_quaternion = Quaternion((0, 0, 1), math.pi) @ Quaternion((1, 0, 0), math.radians(90))
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
    # 片名：高光白亮面（清漆层很亮，扫光过去拉出一条硬高光）；红问号亮面 + 一点自发光。最亮处由合成里的高光肩压在 0.95 以下
    title_mat = D.mat_solid("w1_title_white", "#ECE8E1", rough=0.12, coat=1.0, sss=0.03)
    q_mat = D.mat_solid("w1_qmark_red", "#D0102A", rough=0.1, coat=1.0, sss=0.03)
    for m_ in (title_mat, q_mat):
        bs = m_.node_tree.nodes["Principled BSDF"]
        bs.inputs["Coat Roughness"].default_value = 0.03
    bs = q_mat.node_tree.nodes["Principled BSDF"]
    bs.inputs["Emission Color"].default_value = (1.0, 0.04, 0.05, 1)
    bs.inputs["Emission Strength"].default_value = 0.0         # 落位后才亮起来（见下面 q_glow）
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
    Dhero = HERO_W * 50.0 / 36.0                    # 英雄帧机位到片名平面的距离

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
        # 英雄帧（环收紧、镜头近）里也不许挡片名和副标题
        hp = hero_pos(p)
        kh = Dhero / max(200.0, Dhero + hp.y)
        hx, hz, hr = C.x + (hp.x - C.x) * kh, C.z + (hp.z - C.z) * kh, r * kh
        if abs(hx - C.x) < 520 + hr + pad and C.z - 80 - hr - pad < hz < C.z + 130 + hr + pad:
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
        # 读字环和英雄帧时收紧的环里都要彼此隔开
        return all((p - q).length >= r + rq + pad and (hero_pos(p) - hero_pos(q)).length >= r + rq + pad * 0.5 for q, rq in band)
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
        p0, p3 = b.c0, hero_pos(b.slot)             # 先飞到英雄帧的收紧环，第②③拍再涨到读字环
        d_exp = b.slot - p3
        f_e0, f_e1 = Fu(TL["hero_end"]), Fu(TL["expand_end"])
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
                c = c + d_exp * smooth((F - f_e0) / (f_e1 - f_e0))
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
    # ---- 章节牌：在自己那一拍才从暗处（环外后上方）飞进来，一边飞一边绕竖轴转半圈，落位那一帧正好转到正面
    # （不再先背面朝前停着等——背面空白的牌不出现在画面里）
    for k, b in enumerate(tags):
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        out = Vector((b.slot.x - C.x, 0, b.slot.z - C.z)).normalized()
        start = b.slot + out * 520.0 + Vector((0, 900.0, 80.0))
        mid = b.slot + out * 140.0 + Vector((0, 260.0, 30.0))
        f_on = Fu(TL["tags"][k // 2])
        f_in = f_on - TAG_FLY
        f_off0 = Fu(TL["suck"])
        spin = 1 if b.slot.x < C.x else -1
        for F in range(NF):
            t = tau[F]
            v_in = clamp01((F - f_in) / TAG_FLY)
            s_ = ease_out3(v_in)
            c = bez(start, mid, b.slot + Vector((0, 60.0, 0)), b.slot, s_)
            c = c + Vector((0, 0, 2.0 * math.sin(0.8 * t + k))) * smooth((F - f_on) / 30.0)
            ang = spin * math.pi * (1 - smooth(v_in))
            if F > f_on:                         # 落位后余振：一下 −7° 再回正
                ang += math.radians(-7 * spin * math.sin(math.pi * clamp01((F - f_on) / 12)) * math.exp(-(F - f_on) / 14))
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
    # 红问号落位那一下亮起一点自发光，吸走时熄掉
    fq = Fu(TL["q_land"])
    fast_bake(q_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value",
              [Q_GLOW * smooth((F - fq) / 14.0) * (1 - smooth((F - Fu(TL["suck"])) / 30.0)) for F in range(NF)])
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
    for i, b in enumerate(sats):
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        f_sat0 = Fu(TL["sat_in"][i])
        fl = Fu(TL["sat_land"][i])
        th1 = math.atan2((b.slot.z - C.z) / 0.5, (b.slot.x - C.x))
        th0 = th1 + math.radians(250 + 20 * i)          # 绕不到一整圈：每块各自从画外绕进来
        ao, bo = 560.0, 290.0
        y_orb = -250.0 - 30.0 * i
        pts_tr = []
        for F in range(NF):
            v = clamp01((F - f_sat0) / (fl - f_sat0))
            s_ = smooth(v)
            th = th0 + (th1 - th0) * s_
            kr = 1.0 + 1.4 * (1 - smooth(v / 0.45))       # 从画外螺旋绕进来（开始时轨道半径 2.4 倍，在画面外）
            ring = Vector((C.x + ao * kr * math.cos(th), y_orb, C.z + bo * kr * math.sin(th)))
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
    # ---- 远景：环后面的小零件、雾里的尘粒
    far = far_parts(parts, rnd)
    bodies.extend(far)
    motes(rnd)
    movers = list(parts.values()) + tags + far
    t_sep = time.time()
    n_push = separate(movers, f_brk, Fu(TL["read"]), fixed=letters + sats + [subb]) + separate(movers, f_suck, NF)
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
    mood(sc, Fu(TL["brk"] + 0.35), Fu(TL["brk"] + 1.7), Fu(TL["suck"] + 0.5), Fu(TL["suck_end"] + 0.4), tags)
    highlight_shoulder(sc, Fu(TL["brk"] + 0.35), Fu(TL["brk"] + 1.7), Fu(TL["suck"] + 0.5), Fu(TL["suck_end"] + 0.4))

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
    # 焦距：1-11 尾 50 mm；起身时边推边换到 24 mm 广角（贴近零件的大板断开和子弹时间）；升到料杆时回 50 mm
    lens_arr = np.array([lens_at(F) for F in range(NF)])
    st = lambda tgt, p, a, w: S.state(tgt, p, a, w, 36.0)           # noqa: E731  最后一维存 ln(画宽)，距离 = 画宽 × 焦距 / 36
    # 子弹时间：在浮着的零件之间穿过去（离零件 < 60 mm），路线按零件实际位置搜出来
    f_bt0, f_bt1 = Fu(TL["bt_in"]), Fu(TL["bt_out"])
    bt = bt_path(list(parts.values()), f_bt0, f_bt1, lens_arr)
    chk_bt = bt["chk"]

    def st_of(loc_mm, look_mm, F):
        d = loc_mm - look_mm
        dist = d.length
        return [look_mm.x, look_mm.y, look_mm.z, math.degrees(math.asin(d.z / dist)),
                math.degrees(math.atan2(d.x, -d.y)), math.log(dist * 36.0 / lens_arr[F])]
    hz = C.z + 25
    keys = [(0, st((mc.x, mc.y, mc.z), 52.0, -14.0, 176.0), "stop"),
            (rise, st((mc.x + 3.0, mc.y + 1.0, mc.z), 50.0, -14.0, 170.0), "stop"),
            (Fu(0.75), st((-220.0, -20.0, 60.0), 16.0, -34.0, 280.0), "pass"),   # 起身放慢：接点（TAIL）两侧相邻帧 SSIM 要过 T4
            (Fu(TL["brk"]), st((-170.0, -40.0, 70.0), 11.0, -30.0, 230.0), "pass"),   # 广角贴近零件：断开那一下零件从镜头前弹起
            (f_bt0, st_of(bt["loc"][0], bt["look"][0], f_bt0), "pass"),
            (f_bt1, st_of(bt["loc"][-1], bt["look"][-1], f_bt1), "pass"),
            (Fu(TL["rod_set"] + 0.2), st((C.x, 0.0, C.z + 60), 3.0, 0.0, 1100.0), "pass"),
            (Fu(TL["hero"]), st((C.x, 0.0, hz), 2.0, 0.0, HERO_W), "stop"),             # ①英雄帧：只有片名 + 副标题 + 零件群
            (Fu(TL["hero_end"]), st((C.x, 0.0, hz), 2.0, 0.0, HERO_W * 0.965), "stop"),  #   1.5 s 慢推
            (Fu(8.15), st((C.x - 50, 0.0, C.z - 20), 4.0, 7.0, 1380.0), "pass"),        # ②镜头往下、往左绕一点，课程、Section、Group 依次入画
            (Fu(TL["read"]), st((C.x, 0.0, C.z), 1.0, 0.0, ring_w), "stop"),            # ③拉开到读字全景
            (Fu(TL["read_end"]), st((C.x, 0.0, C.z), 1.0, 0.0, ring_w * 0.975), "stop"),
            (Fu(TL["suck"] + 0.85), st((C.x, 0.0, C.z - 230), 14.0, -8.0, ring_w * 1.08), "pass"),   # 先看零件往下"倒灌"回大板
            (Fu(TL["suck_end"]), st(tuple(cdk.c0 + Vector((0, 0, 8))), 36.0, -18.0, 330.0), "pass"),
            (TAIL + NF_W1, st(z2t, 30.0, -15.0, 235.0), "pass"),
            (NF - 1, st((z2t[0] + 2.0, z2t[1], z2t[2]), 30.5, -15.5, 235.0 * 0.95), "stop")]
    tr = S.Track(keys)
    poses, focus = [], []
    shakes = ((Fu(TL["brk"]), 3.2, 0.45), (Fu(TL["suck_end"]), 1.2, 0.15))      # 冲击：位移 mm、转角 °，4 帧衰减
    for F in range(NF):
        tx, ty, tz, pitch, az, ld = tr.at(F)
        hand = Vector((math.sin(F / 23) * 0.35 + math.sin(F / 9.7) * 0.12, math.cos(F / 31) * 0.3, math.sin(F / 17) * 0.25))
        dist = math.exp(ld) * lens_arr[F] / 36.0
        loc, q = S.cam_pose(Vector((tx, ty, tz)) + hand * (lens_arr[F] / 50.0), pitch, az, dist)
        tgt = Vector((tx, ty, tz)) * MM
        w = bt_weight(F, f_bt0, f_bt1)
        if w > 0:                                # 子弹时间：换成搜出来的穿行路线（两头 10 帧交叉过渡）
            n_ = len(bt["loc"])
            i = min(max(F - f_bt0, 0), n_ - 1)
            ex = F - f_bt0 - i                   # 两头外推（按端点速度）
            i1, i2 = (0, 1) if ex < 0 else (n_ - 2, n_ - 1)
            v0 = bt["loc"][i2] - bt["loc"][i1]
            pl_ = bt["loc"][i] + v0 * ex
            lk = bt["look"][i] + v0 * ex
            q_bt = (lk - pl_).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(bt["roll"][i]))
            loc = loc.lerp(pl_ * MM, w)
            q = q.slerp(q_bt, w)
            tgt = tgt.lerp(lk * MM, w)
        q = q @ Quaternion((0, 0, 1), math.radians(0.12 * math.sin(F / 19)))        # 手持感 ≤ 0.3°
        for fk, amp, rot in shakes:
            k = F - fk
            if 0 <= k <= 4:
                a_ = (1, -0.7, 0.4, -0.2, 0.08)[k]
                loc = loc + Vector((amp * 0.4 * a_, 0, amp * a_)) * MM
                q = q @ Quaternion((1, 0, 0), math.radians(rot * a_)) @ Quaternion((0, 1, 0), math.radians(rot * 0.6 * a_))
        poses.append((loc, q))
        focus.append(tgt if F >= rise else mpart.o.matrix_world @ Vector((6 * MM, 3 * MM, 3 * MM)))
    fd = S.bake_camera(cam, sc, poses, lens, 2.8, focus)
    cam.data.clip_start = 0.004
    fast_bake(cam.data, "lens", lens_arr)
    # 光圈：1-11 尾 f/8（跟原来的板面镜头一样深），断开 f/2.8，子弹时间 f/2，读字 f/4，回板面 f/8
    fs = []
    for F in range(NF):
        u = (F - TAIL) / (FPS * U)
        v = 8.0
        for (ua, ub, a, b_) in ((0.2, 1.0, 8.0, 2.8), (1.2, 1.6, 2.8, 2.0), (2.5, 3.6, 2.0, 4.0), (13.5, 15.5, 4.0, 8.0)):
            if u >= ua:
                v = a + (b_ - a) * smooth((u - ua) / (ub - ua))
        fs.append(v)
    fast_bake(cam.data.dof, "aperture_fstop", fs)
    # ---- 前景三层纵深：前景几块大零件贴着镜头慢慢掠过（强虚化）
    fg = foreground(parts, poses, lens_arr)
    bodies.extend(fg)
    # 镜头贴近零件时零件让一让（让完重新烘焙）
    av = [b for b in list(parts.values()) + tags + far]
    n_av = avoid_camera(av, poses)
    for b in av:
        b.bake()
    print(f"W1_AVOID moved={n_av}", flush=True)
    # ---- 扫光：料杆到位时扫一次字背；英雄帧里一条硬高光从左到右扫过亮面片名
    sweep_light(sc, Fu(TL["sweep"]), Fu(TL["sweep"] + 0.5), "w1_sweep", 260.0, -0.9)
    sweep_light(sc, Fu(TL["sweep2"]), Fu(TL["sweep2"] + 0.7), "w1_sweep2", SWEEP2_W, -1.05, only=[b.o for b in letters])
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
    chk["bullet_time"] = chk_bt
    chk["lens"] = dict(tail=lens_arr[0], brk=lens_arr[Fu(TL["brk"])], bt=lens_arr[Fu(TL["bt_in"]) + 5], hero=lens_arr[Fu(TL["hero"])])
    chk["layers"] = layers_check(sc, cam, fg, far, parts, tags, sats)
    chk["px"] = text_px(sc, cam, letters, tags, sats, subb)
    chk["title_box"] = title_box(sc, cam, letters, [Fu(TL["q_land"]) + 20, Fu(TL["sweep2"]) + 20, Fu(TL["read"]) + 20, Fu(TL["read"]) + 120])
    return cam, chk


AWAY_N = 52
TAG_FLY = 40


def lens_at(F):
    """逐帧焦距：50 → 24（起身到大板断开）→ 24（子弹时间）→ 50（升到料杆）。"""
    u = (F - TAIL) / (FPS * U)
    if u < 0.3:
        return 50.0
    if u < 1.0:
        return 50.0 + (24.0 - 50.0) * smooth((u - 0.3) / 0.7)
    if u < 2.55:
        return 24.0
    if u < 3.2:
        return 24.0 + 26.0 * smooth((u - 2.55) / 0.65)
    return 50.0


def bt_weight(F, f0, f1):
    return smooth((F - (f0 - 10)) / 20.0) * (1 - smooth((F - (f1 - 10)) / 20.0))


def avoid_camera(movers, poses, margin=24.0, decay=0.9):
    """镜头贴着零件走时（断开、子弹时间、升起）：离镜头不到 margin 的零件沿"离开镜头"的方向让开，
    让开量前后按指数包络摊开（提前开始让、之后慢慢回去），不会一帧跳过去。返回让过的件数。"""
    moved = 0
    for b in movers:
        vis = getattr(b, "vis", (0, NF))
        dfc = np.zeros(NF)
        dirs = np.zeros((NF, 3))
        for F in range(NF):
            if not (vis[0] <= F <= vis[1]):
                continue
            cl = np.array(poses[F][0]) / MM
            v = b.cen[F] - cl
            dn = np.linalg.norm(v)
            if dn - b.r * b.scl[F] > margin:
                continue
            hd = hull_dist(b, F, cl)
            dirs[F] = v / max(dn, 1e-6)
            if hd < margin:
                dfc[F] = margin - hd
        if dfc.max() <= 0:
            continue
        moved += 1
        sf, sb = dfc.copy(), dfc.copy()
        for F in range(1, NF):
            sf[F] = max(sf[F], sf[F - 1] * decay)
        for F in range(NF - 2, -1, -1):
            sb[F] = max(sb[F], sb[F + 1] * decay)
        env = np.maximum(sf, sb)
        k = int(np.argmax(dfc))
        d0 = dirs[k]
        for F in range(NF):
            if env[F] > 1e-3:
                dv = dirs[F] if np.linalg.norm(dirs[F]) > 0 else d0
                b.cen[F] = b.cen[F] + dv * env[F] * 1.15
    return moved


def hull_dist(b, F, p_mm):
    """点到物体凸包表面的距离（mm），在凸包里面为负。"""
    tree = _hull_tree(b, F)
    if tree is None:
        return 1e9
    loc, nrm, idx, dist = tree.find_nearest(Vector(tuple(p_mm)) * MM)
    if loc is None:
        return 1e9
    R = np.array(Quaternion(b.quat[F]).to_matrix())
    cen = Vector(tuple(b.cen[F])) * MM
    if (loc - cen).dot(nrm) < 0:                 # 法线朝里就翻过来（凸包，中心一定在里面）
        nrm = -nrm
    d = dist / MM
    return -d if (Vector(tuple(p_mm)) * MM - loc).dot(nrm) < 0 else d


def bt_path(parts, f0, f1, lens_arr):
    """子弹时间的穿行路线：沿 +X 横穿浮起来的零件层（零件此时几乎停住），在一族直线里搜：
    镜头离零件凸包最近处 15–60 mm、正前方不被零件整个挡住；用包围球粗筛，前 40 条再用真凸包精算。"""
    n = f1 - f0 + 1
    P = np.stack([b.cen[f0:f1 + 1] for b in parts])               # (N, n, 3)
    Rr = np.stack([b.r * b.scl[f0:f1 + 1] for b in parts])       # (N, n)
    s = np.linspace(0, 1, n)
    # 路线限在零件层中间：高度在零件中心高度中位数 −20…+50 mm，前后不出零件层（不贴着板面、不沿边走）
    zmid = float(np.median(P[:, n // 2, 2]))
    ylo, yhi = np.percentile(P[:, n // 2, 1], 20), np.percentile(P[:, n // 2, 1], 80)
    zs = [round(zmid + dz) for dz in range(-20, 51, 14)]
    ys = [round(v) for v in np.linspace(ylo, yhi, 7)]
    cands = []
    for xa in (-520.0, -470.0, -420.0):
        for L in (520.0, 600.0, 680.0):
            for y0 in ys:
                for y1 in ys:
                    for z0 in zs:
                        for z1 in zs:
                            cands.append((xa, xa + L, y0, y1, z0, z1))
    C_ = np.array(cands, dtype=np.float64)
    best = []
    for i0 in range(0, len(C_), 600):
        cc = C_[i0:i0 + 600]
        cam = np.stack([cc[:, 0:1] + (cc[:, 1:2] - cc[:, 0:1]) * s, cc[:, 2:3] + (cc[:, 3:4] - cc[:, 2:3]) * s,
                        cc[:, 4:5] + (cc[:, 5:6] - cc[:, 4:5]) * s], axis=2)          # (M, n, 3)
        d = np.linalg.norm(P[None] - cam[:, None], axis=3) - Rr[None]                 # (M, N, n)
        dmin = d.min(1)                                                               # (M, n)
        fwd = (cc[:, None, :] * 0)                                                    # 占位
        dirv = np.stack([cc[:, 1] - cc[:, 0], cc[:, 3] - cc[:, 2], cc[:, 5] - cc[:, 4]], 1)
        dirv /= np.linalg.norm(dirv, axis=1, keepdims=True)
        rel = P[None] - cam[:, None]                                                   # (M, N, n, 3)
        along = np.einsum("mknj,mj->mkn", rel, dirv)
        perp = np.sqrt(np.maximum(0, (rel ** 2).sum(3) - along ** 2))
        block = ((along > 0) & (along < 140) & (perp < Rr[None] * 0.8)).any(1).sum(1)  # 正前方 14 cm 内被零件堵住的帧
        near = ((dmin < 70)).sum(1)
        ok = dmin.min(1) > -25
        score = near - 3 * block - 1000 * (~ok)
        for j in np.argsort(-score)[:40]:
            best.append((float(score[j]), tuple(cc[j])))
        del fwd
    best.sort(key=lambda x: -x[0])
    chosen, ch_d = None, None
    for sc_, c in best[:40]:
        A = Vector((c[0], c[2], c[4]))
        B = Vector((c[1], c[3], c[5]))
        dmin_all, n60 = 1e9, 0
        for k in range(n):
            p = A.lerp(B, k / (n - 1))
            dk = 1e9
            for bi, b in enumerate(parts):
                if np.linalg.norm(P[bi, k] - np.array(p)) - Rr[bi, k] > 90:
                    continue
                dk = min(dk, hull_dist(b, f0 + k, p))
            dmin_all = min(dmin_all, dk)
            n60 += dk < 60
        if dmin_all >= 15 and n60 >= 6:
            chosen, ch_d = c, (dmin_all, n60)
            break
        if chosen is None or (dmin_all >= 10 and (ch_d is None or n60 > ch_d[1])):
            if dmin_all >= 10:
                chosen, ch_d = c, (dmin_all, n60)
    if chosen is None:
        raise SystemExit("w1z: no bullet-time path")
    A = Vector((chosen[0], chosen[2], chosen[4]))
    B = Vector((chosen[1], chosen[3], chosen[5]))
    dirv = (B - A).normalized()
    look_dir = (dirv + Vector((0, 0, -0.14))).normalized()
    locs, looks, rolls = [], [], []
    fdist = []
    for k in range(n):
        p = A.lerp(B, k / (n - 1))
        # 对焦：前方 30° 锥里最近的零件
        best_d = 260.0
        for bi in range(len(parts)):
            r_ = Vector(tuple(P[bi, k])) - p
            al = r_.dot(look_dir)
            if 40 < al < 400 and (r_ - look_dir * al).length < al * 0.55:
                best_d = min(best_d, al)
        fdist.append(best_d)
    fs = np.convolve(np.pad(fdist, 6, mode="edge"), np.ones(13) / 13, mode="valid")
    for k in range(n):
        p = A.lerp(B, k / (n - 1))
        locs.append(p)
        looks.append(p + look_dir * float(fs[k]))
        rolls.append(-6.0 * smooth(k / (n - 1)))                  # 穿过去时镜头慢慢歪 6°
    return dict(loc=locs, look=looks, roll=rolls,
                chk=dict(A=[round(v, 1) for v in A], B=[round(v, 1) for v in B], min_hull_mm=round(ch_d[0], 1), cloud_zmid=round(zmid, 1),
                         frames_lt60=int(ch_d[1]), frames=n))


def dup_part(src, name):
    """零件的一份拷贝（共用网格），不带动画；按第 0 帧（还在大板上、原大）的样子拷。"""
    bpy.context.scene.frame_set(0)
    mp = {}
    for o in [src] + list(src.children_recursive):
        n_ = o.copy()
        n_.animation_data_clear()
        bpy.context.scene.collection.objects.link(n_)
        mp[o] = n_
    for o, n_ in mp.items():
        if o.parent in mp:
            n_.parent = mp[o.parent]
            n_.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    root = mp[src]
    root.parent = None
    root.matrix_world = src.matrix_world.copy()
    root.name = name
    bpy.context.view_layer.update()
    return root


# 前景：(格子, 英雄帧位置 (x, z 以半画宽为单位), 读字时位置, 离镜头 mm, 在画面里的半径（半画宽的几分之几）, 横漂速度)
FG = (("z3_c4_r2", (-0.92, 0.80), (-1.10, 1.06), 430.0, 0.40, 0.035),
      ("z8_c11_r4", (0.96, -0.82), (1.12, -1.04), 380.0, 0.42, -0.03),
      ("z1_c0_r0", (0.80, 0.95), (1.12, 1.05), 520.0, 0.34, -0.025),
      ("z4_c7_r2", (-0.78, -0.98), (-1.12, -1.06), 560.0, 0.36, 0.03))


def foreground(parts, poses, lens_arr):
    """前景几块大零件：跟着镜头的坐标系摆（英雄帧在四角、读字时退到角外一半），自己慢慢横漂、慢转，强虚化；
    第 4.4 拍从画外漂进来，吸回时往下甩出画面后隐藏。用拷贝，不占环上的零件。"""
    out = []
    rnd = random.Random(7)
    f_in, f_h = Fu(4.4), Fu(TL["hero"])
    f_e0, f_e1 = Fu(TL["hero_end"]), Fu(TL["read"])
    f_s = Fu(TL["suck"])
    f_out = f_s + 40
    for i, (cn, H_, R_, d, frac, vx) in enumerate(FG):
        src = parts[cn].o
        o = dup_part(src, f"w1_fg_{i}")
        b = Body(o, "fg", f"fg_{i}")
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        hw = d * 18.0 / 50.0
        k = frac * hw / b.r
        b.scl[:] = k
        b.sp = k
        ax = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        wv = rnd.uniform(0.12, 0.22) * rnd.choice((-1, 1))
        sgn = 1 if H_[0] > 0 else -1
        for F in range(NF):
            Fc = min(max(F, f_in), f_out)
            loc, q = poses[Fc]
            e = smooth((Fc - f_e0) / (f_e1 - f_e0))
            xs = H_[0] + (R_[0] - H_[0]) * e + vx * (Fc - f_h) / FPS
            zs = H_[1] + (R_[1] - H_[1]) * e
            xs += sgn * 0.9 * (1 - smooth((Fc - f_in) / (f_h - f_in)))          # 从画外漂进来
            ex = smooth((Fc - f_s) / 40.0)                                       # 吸回：往外、往下甩出去
            xs += sgn * 1.2 * ex
            zs -= 1.4 * ex
            local = Vector((xs * hw, zs * hw * 9 / 16, -d))
            c = Vector(loc) / MM + q @ local
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(Quaternion(ax, wv * Fc / FPS) @ b.q0)
        b.vis = (f_in, f_out)
        b.bake()
        hide_before(o, f_in - 1)
        hide_after(o, f_out)
        out.append(b)
    return out


def far_parts(parts, rnd, n=22):
    """远景：环后面 0.5–0.95 m 深处十几块小零件（拷贝），时间恢复后从暗处显出来，慢漂慢转，吸回时往上飘走。"""
    pool = [b for cn, b in sorted(parts.items()) if cn not in CH_HERO and cn != "z3_c4_r0"]
    rnd.shuffle(pool)
    out, placed = [], []
    f0, f1 = Fu(TL["resume"]), Fu(TL["resume"] + 0.6)
    f_s = Fu(TL["suck"])
    for i, src in enumerate(pool[:n]):
        o = dup_part(src.o, f"w1_far_{i}")
        b = Body(o, "far", f"far_{i}")
        Dr, Dh = (2 * FRAME_HW + 40) * 50.0 / 36.0, HERO_W * 50.0 / 36.0
        rr = src.R * 1.6

        def off_title(p):
            # 远景零件在读字和英雄帧两个机位里都不许从片名、副标题、课程牌的缝里露出来
            for D_, hw, z0, z1 in ((Dr, 640, -280, 260), (Dh, 560, -100, 150)):
                k_ = D_ / (D_ + p.y)
                dx, dz, r_ = (p.x - C.x) * k_, (p.z - C.z) * k_, rr * k_
                if abs(dx) < hw + r_ and z0 - r_ < dz < z1 + r_:
                    return False
            return True
        for _ in range(4000):
            p = Vector((C.x + rnd.uniform(-1150, 1150), rnd.uniform(520, 920), rnd.uniform(260, 1320)))
            vel = Vector((rnd.gauss(0, 1), rnd.gauss(0, 0.3), rnd.gauss(0, 1))).normalized() * rnd.uniform(8, 18)    # mm/s
            pe = p + vel * ((Fu(TL["suck"]) - f0) / FPS)
            if all((p - q).length > 260 for q in placed) and all(off_title(p + (pe - p) * s_) for s_ in (0, 0.25, 0.5, 0.75, 1)):
                break
        placed.append(p)
        k = 1.6
        b.sp = k
        ax = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        wv = rnd.uniform(0.1, 0.3)
        b.cen = np.zeros((NF, 3))
        b.quat = np.zeros((NF, 4))
        for F in range(NF):
            t = (F - f0) / FPS
            c = p + vel * t + Vector((0, 0, 900)) * ease_in2((F - f_s) / 70.0)
            b.cen[F] = tuple(c)
            b.quat[F] = tuple(Quaternion(ax, wv * t) @ b.q0)
            b.scl[F] = max(1e-3, k * smooth((F - f0) / (f1 - f0)) * (1 - smooth((F - f_s - 30) / 40.0)))
        b.vis = (f0, f_s + 70)
        hide_before(o, f0 - 1)
        hide_after(o, f_s + 70)
        out.append(b)
    return out


def motes(rnd, n=260):
    """远景尘粒：雾里飘的细颗粒，四分之一带一点自发光（虚化后成光斑）。"""
    m_d = D.mat_solid("w1_mote", "#AEB6C6", rough=0.6, coat=0.0, sss=0)
    m_e = emit_mat("w1_mote_glow", 5.0)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=1)
    base = bpy.context.object
    me_d = base.data
    me_d.materials.append(m_d)
    me_e = me_d.copy()
    me_e.materials[0] = m_e
    bpy.data.objects.remove(base)
    f0, f1 = Fu(TL["brk"] + 0.3), Fu(TL["suck_end"])
    for i in range(n):
        glow = i % 4 == 0
        o = bpy.data.objects.new(f"w1_mote_{i}", me_e if glow else me_d)
        bpy.context.scene.collection.objects.link(o)
        o.visible_shadow = False
        p = Vector((C.x + rnd.uniform(-1500, 1500), rnd.uniform(150, 1050), rnd.uniform(160, 1450)))   # 只在片名平面后面（远景），不在字前面糊成光斑
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1) + 0.3)).normalized() * rnd.uniform(4, 14)
        r = rnd.uniform(1.2, 2.6) * (0.8 if glow else 1.0)
        ph = rnd.uniform(0, 6.28)
        loc = np.zeros((NF, 3))
        scl = np.zeros((NF, 3))
        for F in range(NF):
            t = F / FPS
            c = p + v * t + Vector((math.sin(t * 0.7 + ph) * 6, 0, math.cos(t * 0.5 + ph) * 5))
            loc[F] = tuple(c * MM)
            a = smooth((F - f0) / 60.0) * (1 - smooth((F - (f1 - 40)) / 40.0))
            scl[F] = [max(1e-7, r * MM * a)] * 3
        fast_bake(o, "location", loc)
        fast_bake(o, "scale", scl)


def highlight_shoulder(sc, f0, f1, f2, f3):
    """合成里的高光肩：零重力段（深色背景、强轮廓光、亮面字）把线性 0.62 以上的亮部柔和压到 0.85 以下
    （显示值约 0.92），片名区最大亮度 < 0.95；1-11 尾和 2-01 头系数为 0，跟原片一样。"""
    ng = bpy.data.node_groups.new("w1_comp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    cv = ng.nodes.new("CompositorNodeCurveRGB")
    out = ng.nodes.new("NodeGroupOutput")
    mp = cv.mapping
    mp.extend = "HORIZONTAL"
    # 合成在曝光之前：先乘 k = 2^曝光 换成显示前的亮度（0–1），过曲线，再除回去
    k = 2.0 ** sc.view_settings.exposure
    c = mp.curves[3]
    c.points[0].location = (0.0, 0.0)
    c.points[1].location = (1.0, 0.85)
    c.points.new(0.62, 0.62)
    c.points.new(0.80, 0.77)
    mp.update()

    def mul(v):
        m = ng.nodes.new("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = "MULTIPLY"
        m.inputs[0].default_value = 1.0
        m.inputs[7].default_value = (v, v, v, 1.0)
        return m
    m1, m2 = mul(k), mul(1.0 / k)
    ng.links.new(rl.outputs["Image"], m1.inputs[6])
    ng.links.new(m1.outputs[2], cv.inputs["Image"])
    ng.links.new(cv.outputs["Image"], m2.inputs[6])
    ng.links.new(m2.outputs[2], out.inputs["Image"])
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    fast_bake(cv.inputs["Factor"], "default_value",
              [smooth((F - f0) / max(1, f1 - f0)) * (1 - smooth((F - f2) / max(1, f3 - f2))) for F in range(NF)])
    return ng


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
    pv.inputs["Color"].default_value = (0.55, 0.68, 1.0, 1.0)   # 雾偏蓝：光柱是冷白，不把背景染灰
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
    # 光束斜着落在片名后面（y > 0）：镜头不是对着光束往里看，雾不会糊满整个画面，只在字后面亮出一道光柱
    L.rotation_euler = (Vector((0.25, 0.55, 0.05)) - L.location).to_track_quat("-Z", "Y").to_euler()
    en = []
    for F in range(NF):
        a = smooth((F - f0) / 20.0) * (1 - smooth((F - (f1 - 30)) / 50.0))
        en.append(BEAM_W * a)
    fast_bake(L.data, "energy", en)
    return v, L


DENS, BEAM_W = float(os.environ.get("W1_DENS", 0.07)), float(os.environ.get("W1_BEAM_W", 6000.0))   # 环境变量只给试渲排查用
# 11-21 第二轮：近黑深蓝（#0B1020）背景，影棚灯压得更低，靠背后的强逆光和轮廓光把东西勾出来
MOOD = dict(world=0.10, key=0.30, fill=0.22, strip=0.18, rim=1.0, softbox=0.35, cards=0.12)
BG_LIN = (0.0033, 0.0052, 0.0144)          # #0B1020 的线性值
FRONT_W = 300.0                            # 零重力段的正面柔光（镜头后方），片名正面亮
BACK_W = 1400.0                            # 背后两盏逆光（每盏）
WALL_W = 45.0                              # 墙上一团深蓝的光（给背景一点层次）
TAGSPEC_W = 1600.0                         # 章节牌翻面时扫过的反光
SWEEP2_W = 900.0                           # 英雄帧扫过片名的硬高光
Q_GLOW = 0.8                               # 红问号自发光


def area(name, loc_mm, aim_mm, size, size_y, color):
    bpy.ops.object.light_add(type="AREA", location=tuple(Vector(loc_mm) * MM))
    L = bpy.context.object
    L.name = name
    L.data.shape = "RECTANGLE"
    L.data.size, L.data.size_y = size, size_y
    L.data.color = color
    L.rotation_euler = (Vector(aim_mm) * MM - L.location).to_track_quat("-Z", "Y").to_euler()
    L.visible_camera = False
    L.visible_volume_scatter = False
    return L


def mood(sc, f0, f1, f2, f3, tags):
    """零重力那一段：影棚灯压暗，背景布和世界光换成近黑深蓝；背后两盏强逆光、墙上一团深蓝光；回板时全部还原接 2-01。"""
    def a(F):
        return smooth((F - f0) / max(1, f1 - f0)) * (1 - smooth((F - f2) / max(1, f3 - f2)))

    def m(F, lvl):
        # 按倍数（对数）渐暗：每一小段亮度掉的比例一样，不会在最后一截突然黑下去（T5）
        return lvl ** a(F)
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name in MOOD:
            e0 = o.data.energy
            fast_bake(o.data, "energy", [e0 * m(F, MOOD[o.name]) for F in range(NF)])
    wn = sc.world.node_tree.nodes["Background"]
    b0 = wn.inputs[1].default_value
    fast_bake(wn.inputs[1], "default_value", [b0 * m(F, MOOD["world"]) for F in range(NF)])
    w0 = np.array(wn.inputs[0].default_value)
    wb = np.array([0.30, 0.42, 1.0, 1.0])
    fast_bake(wn.inputs[0], "default_value", [w0 + (wb - w0) * a(F) for F in range(NF)])
    for nm in ("refl_top", "refl_left"):
        st = bpy.data.objects[nm].active_material.node_tree.nodes["Emission"].inputs["Strength"]
        s0 = st.default_value
        fast_bake(st, "default_value", [s0 * m(F, MOOD["cards"]) for F in range(NF)])
    fr = area("w1_front", (C.x, -2700, C.z + 350), C, 1.8, 1.0, (1, 0.975, 0.95))
    fast_bake(fr.data, "energy", [FRONT_W * a(F) for F in range(NF)])
    # 背后两盏逆光（高、偏两侧，朝镜头方向斜打）：字、牌、零件都有一圈亮边
    for nm, sx in (("w1_back_L", -1), ("w1_back_R", 1)):
        L = area(nm, (C.x + sx * 820, 760, C.z + 560), (C.x - sx * 120, -300, C.z - 40), 0.6, 0.6, (0.86, 0.92, 1.0))
        fast_bake(L.data, "energy", [BACK_W * a(F) for F in range(NF)])
    gl = area("w1_wallglow", (C.x, 980, C.z + 150), (C.x, 1300, C.z + 220), 1.4, 0.9, (0.30, 0.45, 1.0))
    fast_bake(gl.data, "energy", [WALL_W * a(F) for F in range(NF)])
    # 章节牌翻面时扫过的反光：一块大灯在镜头左前方、和牌一样高，只照牌（灯光链接）
    ts = area("w1_tagspec", (C.x - 1100, -1900, C.z + 40), C, 1.4, 0.35, (1, 0.98, 0.95))
    col = bpy.data.collections.new("w1_tagspec_only")
    for b in tags:
        for m_ in [b.o] + list(b.o.children_recursive):
            col.objects.link(m_)
    ts.light_linking.receiver_collection = col
    f_t0, f_t1 = Fu(TL["tags"][0]) - TAG_FLY, Fu(TL["read"]) + 40
    fast_bake(ts.data, "energy", [TAGSPEC_W * smooth((F - f_t0) / 20.0) * (1 - smooth((F - f_t1) / 40.0)) for F in range(NF)])
    # 背景布本身换成近黑深蓝（影棚"关灯"），2-01 前恢复
    bp = bpy.data.materials["backdrop"].node_tree.nodes["Principled BSDF"]
    bc = bp.inputs["Base Color"]
    c0 = np.array(bc.default_value)
    bl = np.array(list(BG_LIN) + [1.0])
    rat = bl / np.maximum(c0, 1e-4)
    fast_bake(bc, "default_value", [c0 * rat ** a(F) for F in range(NF)])    # 也按倍数渐变
    # 背景布的白色镜面反光会把深蓝冲成灰：零重力段关掉它的镜面、调到全哑
    sp = bp.inputs["Specular IOR Level"]
    s0 = sp.default_value
    fast_bake(sp, "default_value", [s0 * (1 - a(F)) for F in range(NF)])
    ro = bp.inputs["Roughness"]
    r0 = ro.default_value
    fast_bake(ro, "default_value", [r0 + (1 - r0) * a(F) for F in range(NF)])
    # 新加的正面光、逆光和扫光不照背景布（灯光链接排除），背景保持近黑
    sweep = bpy.data.objects.get("sweep")
    if sweep is not None:
        ex = bpy.data.collections.new("w1_no_backdrop")
        ex.objects.link(sweep)
        for co in ex.collection_objects:          # 只有背景布这一件
            co.light_linking.link_state = "EXCLUDE"
        for L in (fr, bpy.data.objects["w1_back_L"], bpy.data.objects["w1_back_R"]):
            L.light_linking.receiver_collection = ex


def sweep_light(sc, f0, f1, name, power, y_m, only=None):
    """一条竖着的窄长灯从左到右扫过片名前方：亮面字上拉出一道移动的硬高光。"""
    bpy.ops.object.light_add(type="AREA", location=(0, -1.2, 1.0))
    L = bpy.context.object
    L.name = name
    L.data.shape = "RECTANGLE"
    L.data.size, L.data.size_y = 0.05, 1.4
    L.data.color = (1, 0.98, 0.95)
    L.rotation_euler = (math.radians(90), 0, 0)
    loc, en = [], []
    for F in range(NF):
        v = clamp01((F - f0) / (f1 - f0))
        loc.append(((-1.4 + 2.8 * smooth(v)), y_m, C.z * MM + 0.15))
        en.append(power * math.sin(math.pi * v) if 0 < v < 1 else 0.0)
    fast_bake(L, "location", loc)
    fast_bake(L.data, "energy", en)
    L.visible_camera = False
    if only:                                    # 只照这些物体（灯光链接）：英雄帧那道高光只走片名，不在副标题深色牌上反出一块白斑
        col = bpy.data.collections.new(name + "_only")
        for o in only:
            for m_ in [o] + list(o.children_recursive):
                col.objects.link(m_)
        L.light_linking.receiver_collection = col


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
    """镜头离任何会动的东西最近多少：包围球粗筛，球距 < 60 mm 的再用真凸包（字母用真网格）精算。"""
    cen = np.stack([b.cen for b in bodies])
    radF = np.stack([b.r * b.scl for b in bodies])
    vis = [getattr(b, "vis", (0, NF)) for b in bodies]
    worst = (1e9, -1, "")
    for F in range(NF):
        cl = np.array(poses[F][0]) / MM
        d = np.linalg.norm(cen[:, F, :] - cl, axis=1) - radF[:, F]
        live = np.array([v[0] <= F <= v[1] for v in vis])
        d = np.where(live, d, 1e9)
        for i in np.where(d < 60)[0]:
            d[i] = hull_dist(bodies[i], F, cl)
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
    for lbl, F in (("title_landed", Fu(TL["q_land"]) + 20), ("hero", Fu(TL["hero"]) + 45), ("read", Fu(TL["read"]) + 30)):
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


def layers_check(sc, cam, fg, far, parts, tags, sats):
    """三层纵深和三拍信息量：英雄帧中段、读字中段各量一次——前景大零件占画面多少（按 0.75 倍包围球投影，192×108 栅格），
    中景零件、远景零件在画面里几块；英雄帧整段里有没有课程牌/Section/Group/名单/章节牌进画。"""
    out = {}
    gx, gy = np.meshgrid((np.arange(192) + 0.5) / 192, (np.arange(108) + 0.5) / 108)

    def disk(b, F):
        sc.frame_set(F)
        c = Vector(tuple(b.cen[F])) * MM
        v = world_to_camera_view(sc, cam, c)
        if v.z <= 0.01:
            return None
        lens = cam.data.lens
        rpx = 0.75 * b.r * b.scl[F] * MM / v.z * lens / 36.0          # 以画宽为 1
        return v.x, v.y, rpx

    def inframe(b, F):
        if not (getattr(b, "vis", (0, NF))[0] <= F <= getattr(b, "vis", (0, NF))[1]):
            return False
        d = disk(b, F)
        return d is not None and -d[2] < d[0] < 1 + d[2] and -d[2] * 16 / 9 < d[1] < 1 + d[2] * 16 / 9
    for lbl, F in (("hero", Fu(TL["hero"]) + 45), ("read", Fu(TL["read"]) + 120)):
        mask = np.zeros_like(gx, dtype=bool)
        for b in fg:
            d = disk(b, F)
            if d:
                mask |= ((gx - d[0]) ** 2 + ((gy - (1 - d[1])) * 9 / 16) ** 2) < d[2] ** 2
        out[lbl] = dict(frame=F, fg_cover_pct=round(100 * mask.mean(), 1),
                        mid_parts=sum(inframe(b, F) for b in parts.values()), far_parts=sum(inframe(b, F) for b in far))
    seen = set()
    for F in range(Fu(TL["hero"]), Fu(TL["hero_end"]) + 1, 3):
        for b in list(sats) + list(tags):
            if inframe(b, F):
                seen.add(b.name)
    out["hero_window_s"] = round((Fu(TL["hero_end"]) - Fu(TL["hero"])) / FPS, 2)
    out["hero_extra_items"] = sorted(seen)
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
