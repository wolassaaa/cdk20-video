"""HKBU SCIE1007 课程作业的科普视频。托盘样板 2、3（11-16，下一步方案_20261116 第 3.2 节），由 bl_inserts.py 的 BL_EXTRA 接口运行。

托盘、格子、灯、机位拟合全部沿用 bl_tray2.py（运行时读它的源码，换掉节拍常数再执行；bl_tray2.py 本身不改）：
  t309  3-09（B 出镜，人在左，托盘在右）：锁在 "lock" 落进托盘（bl_tray2 的落法），钥匙坯在 "key" 递进来停在锁前（bl_tray2 的 STOP，离锁壁留空）；
        路线、目标站、红液管全部藏起；锁不转。压暗、推近进 W2 在 Remotion（Tray3.jsx）。
  t411  4-11（D，人在右，托盘在左）+ 4-12（A，人在左，托盘在右）：同一块托盘，机位只换镜头位移（托盘镜像到画面另一边，正反打）。
        七枚钢代币（4-10 挑出的七个）一行：Wait 跳一下、So 再跳、picked 往前一步、quite 退回、Only 后排试管竖直落下、lab 代币往右一格、tell 试管里红液升起。
        代币只在台面上平移、只竖直起落，和试管不在同一排（y 不同），路径不交；TRAY3_CLASH=1 逐帧量包围盒。
帧号 = 成片帧（60 fps），节拍在 Tray3.jsx 的同名常数里（src/v3/tray/sample3.json）。
运行：BL_EXTRA=bl_tray3.py blender.exe -b -P bl_inserts.py -- t309 <输出目录> [首帧] [末帧] [采样]
"""
import json
import math
import os

META = {"t309": (0.0, 341, 0.2, 0.9), "t411": (0.0, 641, 0.2, 0.9)}
_T3META = dict(META)
_T3 = json.load(open(HERE + "../../../../../../镜头设计_v2/tests/T4_remotion/src/v3/tray/sample3.json", encoding="utf-8"))
_BIG = 99999
if SHOT == "t309":
    _b = _T3["t309"]["blender"]
    _BEATS = dict(okay=_BIG, to=_BIG, this=_BIG, picture=_BIG, lock=_b["lock"], and_=_BIG, key=_b["key"], end=_BIG, push=_BIG, push_end=_BIG + 24, vo302=_BIG)
else:
    _BEATS = dict(okay=_BIG, to=_BIG, this=_BIG, picture=_BIG, lock=_BIG, and_=_BIG, key=_BIG, end=_BIG, push=_BIG, push_end=_BIG + 24, vo302=_BIG)
_src = open(HERE + "bl_tray2.py", encoding="utf-8").read()
for a, b in (("BEATS = dict(okay=123, to=173, this=202, picture=268, lock=314, and_=376, key=424, end=439, push=443, push_end=467, vo302=466)", "BEATS = _BEATS"),
             ("rot = math.radians(25) *", "rot = 0.0 *"),
             ("    for f in range(FRAMES + 1):\n        apply(f)", "    for f in range(FRAMES + 1):\n        apply(f)\n    TRAY3_CTX.update(c=c, lock=lock_m, key=key_m, route=route, tgt=tgt, feed=feed_e, slab=slab, X0=X0, X1=X1, Y0=Y0, Y1=Y1, TC=TC, shx=shx)")):
    if a not in _src:
        raise SystemExit("bl_tray3: bl_tray2.py 里找不到：%r" % a[:50])
    _src = _src.replace(a, b)
TRAY3_CTX = {}
exec(compile(_src, HERE + "bl_tray2.py", "exec"))
META = {**META, **_T3META}


def _hide_tree(o):
    for ch in o.children_recursive:
        ch.hide_render = True


def t309_shot(sc, sky):
    upd = tray2_shot(sc, sky)
    X = TRAY3_CTX

    def update(t):
        upd(t)
        for k in ("route", "tgt", "feed"):
            _hide_tree(X[k])
    if os.environ.get("TRAY3_CLASH"):
        clash_run(sc, update, dict(lock=list(X["lock"].children), key=list(X["key"].children)), [("lock", "key")])
    return update


def t411_shot(sc, sky):
    import bmesh
    upd = tray2_shot(sc, sky)
    X = TRAY3_CTX
    b = _T3["t411"]["blender"]
    c = X["c"]
    for k in ("lock", "key"):
        _hide_tree(X[k])
    # 镜头位移：原来的关键帧（托盘在右）拿出来，删掉曲线，逐帧自己设；4-11（cut 之前）整体往左挪到画面左边
    sc.frame_set(0)
    LENS, FD, SHY = c.data.lens, c.data.dof.focus_distance, c.data.shift_y
    c.data.animation_data_clear()                    # 这两段机位不动：焦距、对焦、位移都直接设
    c.data.lens, c.data.dof.focus_distance = LENS, FD
    SHX = X["shx"]
    MIRROR = (1340 - 480) / 1920                     # 托盘中心从 x 1340 挪到 480（D 在右，代币不进人那一半）
    X0, X1, Y0, Y1 = X["X0"], X["X1"], X["Y0"], X["Y1"]
    TW = X1 - X0
    steel = next(ch for ch in X["key"].children if ch.type == "MESH").material_slots[0].material
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    r, h = TW * 0.045, TW * 0.018
    gap = TW * 0.115
    cx0 = (X0 + X1) / 2 - 0.02 * TW
    ROW_Y = Y0 + 0.9
    home = [Vector((cx0 + (i - 3) * gap, ROW_Y, 0.0)) for i in range(7)]
    coins = []
    for i in range(7):
        e = empty("coin%d" % i)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=h)
        me = bpy.data.meshes.new("coin%d_m" % i)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(steel)
        o = bpy.data.objects.new("coin%d_b" % i, me)
        sc.collection.objects.link(o)
        o.parent = e
        o.location = (0, 0, h / 2)
        B.smooth(o)
        bpy.ops.mesh.primitive_torus_add(major_radius=r * 0.62, minor_radius=r * 0.06, location=(0, 0, 0), major_segments=64, minor_segments=10)
        tr = bpy.context.object
        tr.name = "coin%d_ink" % i
        tr.data.materials.append(ink)
        tr.parent = e
        tr.location = (0, 0, h + r * 0.03)
        coins.append(e)
    # 试管：后排右边，玻璃管 + 红液（液面从 0 升到 0.55）
    glass = B.clear_glass()
    red = B.fluid(P.RED, (0.9, 0.05, 0.03))
    TR, TH_ = TW * 0.055, TW * 0.32
    TUBE = Vector((cx0 + 2.2 * gap, ROW_Y + 1.35, 0.0))
    tube = empty("tube")
    bpy.ops.mesh.primitive_cylinder_add(radius=TR, depth=TH_, vertices=64, location=(0, 0, TH_ / 2))
    tg = bpy.context.object
    tg.name = "tube_glass"
    tg.data.materials.append(glass)
    tg.parent = tube
    B.smooth(tg)
    liq = empty("tube_liq")
    liq.parent = tube
    bpy.ops.mesh.primitive_cylinder_add(radius=TR * 0.82, depth=1.0, vertices=48, location=(0, 0, 0.5))
    lq = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    lq.name = "tube_fluid"
    lq.data.materials.append(red)
    lq.parent = liq
    liq.location = (0, 0, TR * 0.15)

    def sm_(a, b_, f):
        return smooth((f - a) / max(b_ - a, 1e-6))

    def hop(f, at, d=10):          # 竖直起落，落点 = at
        x = (f - (at - 2 * d)) / (2 * d)
        return 0.0 if x <= 0 or x >= 1 else math.sin(math.pi * x) * r * 1.2

    def coin_pos(i, f):
        p = Vector(home[i])
        p.y -= 0.35 * TW * 0.25 * (sm_(b["picked"] - 20, b["picked"], f) - sm_(b["quite"] - 18, b["quite"], f))
        p.x += 0.5 * gap * sm_(b["lab"] - 22 + i, b["lab"] + i * 0 , f)
        p.z = hop(f, b["wait"] + i) + hop(f, b["so"] + i) + hop(f, b["not"] + i, 8)
        return p

    def tube_z(f):
        L = b["only"]
        if f < L - 18:
            return 12.0
        if f < L:
            x = (f - L + 18) / 18
            return 12.0 * (1 - smooth(x))
        return 0.0
    FILL = sm_
    for f in range(FRAMES + 1):
        for i, e in enumerate(coins):
            e.location = coin_pos(i, f)
            e.keyframe_insert("location", frame=f)
        tube.location = TUBE + Vector((0, 0, tube_z(f)))
        tube.keyframe_insert("location", frame=f)
        liq.scale = (1, 1, max(1e-3, TH_ * 0.55 * FILL(b["lab"], b["tell"], f)))
        liq.keyframe_insert("scale", frame=f)

    def update(t):
        f = int(round(t * FPS))
        upd(t)
        for k in ("route", "tgt", "feed", "lock", "key"):
            _hide_tree(X[k])
        c.data.shift_x = SHX + (MIRROR if f < b["cut"] else 0.0)
        c.data.shift_y = SHY
        tvis = f >= b["only"] - 18
        for o in tube.children_recursive:
            o.hide_render = not tvis
        lq.hide_render = not tvis or f < b["lab"]
    if os.environ.get("TRAY3_CLASH"):
        groups = {"coin%d" % i: list(e.children) for i, e in enumerate(coins)}
        groups["tube"] = [tg, lq]
        pairs = [("coin%d" % i, "coin%d" % (i + 1)) for i in range(6)] + [("coin%d" % i, "tube") for i in range(7)]
        clash_run(sc, update, groups, pairs)
    return update


def clash_run(sc, update, groups, pairs):
    """逐帧：每组可见网格的世界包围盒和屏幕框；组和组的网格是否相交（BVH）。写 JSON 到 TRAY3_CLASH 指的文件，不渲染。"""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils.bvhtree import BVHTree
    rows = []
    for f in range(FRAMES):
        sc.frame_set(f)
        update(f / FPS)
        dg = bpy.context.evaluated_depsgraph_get()
        row = dict(f=f, box={}, clash=[])
        bv = {}
        for name, objs in groups.items():
            vis = [o for o in objs if not o.hide_render and o.type == "MESH"]
            xs, ys, trees = [], [], []
            for o in vis:
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                mw = o.matrix_world
                vv = [mw @ v.co for v in me.vertices]
                trees.append(BVHTree.FromPolygons(vv, [tuple(p.vertices) for p in me.polygons]))
                for q in vv[::max(1, len(vv) // 200)]:
                    s = w2c(sc, sc.camera, q)
                    if s.z > 0:
                        xs.append(s.x * 1920)
                        ys.append((1 - s.y) * 1080)
                ev.to_mesh_clear()
            if xs:
                row["box"][name] = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
            bv[name] = trees
        for a, b_ in pairs:
            if bv.get(a) and bv.get(b_) and sum(len(x.overlap(y)) for x in bv[a] for y in bv[b_]):
                row["clash"].append("%s/%s" % (a, b_))
        rows.append(row)
    json.dump(rows, open(os.environ["TRAY3_CLASH"], "w"))
    print("TRAY3_CLASH_OK", sum(1 for r in rows if r["clash"]), "clash frames", flush=True)
    raise SystemExit(0)


SHOTS["t309"] = t309_shot
SHOTS["t411"] = t411_shot
