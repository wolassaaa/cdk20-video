"""HKBU SCIE1007 课程作业的科普视频。4-10（09:49-10:14，A 画外音）等 S5 的画外音段，写在我自己的文件里，由 bl_inserts.py 的 BL_EXTRA 接口运行。

`s410`：从 W3 最后一帧（骨白台面上两格钥匙地毯、锁停在 CDK20 上方）接着走——
地毯铺满两格 → 镜头退成俯视、锁在右上方 → 一把钥匙升起来飞到锁孔、插进去、刻度环一格一格咬住（打分）
→ 退回俯视，没被选中的钥匙一片一片缩没，只剩 54 把 → 其中 47 把也缩没，7 把浮起来停在台面上方。

画什么照锁定剧本 4-10 的画面说明；数字（8,918 / 54 / 7）在 Remotion 里叠，不在这里。
导演的硬规矩：动的东西按几何算路径，不能穿模。文件末尾有逐帧的不渲染检查。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s5.py blender.exe -b -t 4 -P bl_inserts.py -- s410 <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
快速看：加 BL_CPU=1、BL_FRAMES=0,600、尺寸 0.3。
"""
import math

import bpy
import numpy as np
from mathutils import Quaternion, Vector

META = {"s410": (589.867, 1500, 0.2, 0.9), "s504": (662.0, 1440, 0.2, 0.9)}   # 4-10 25 秒；5-04 24 秒
T0 = 589.867


def _with_prefix(prefix):
    return [bpy.data.objects[n] for n in sorted(bpy.data.objects.keys()) if n.startswith(prefix)]


def show(e, on):
    """W3 的钥匙是空物体带一群子网格，可见性要一把把设，不能只设空物体。"""
    for o in e.children:
        o.hide_render = not on


def shot_s410(sc, sky):
    """4-10 第二版（Claude 接手 DS，11-10）。机位表在 s4/4-10_机位表.md，验收照 06 第 9 节。
    0-5 s W3 末机位不动（全景，两格钥匙地毯）；5.0-7.2 s 落到锁的近景（az 25、el 24）；W3 悬过的那把钥匙从地毯升起，
    长回 W3 里悬着的大小（W3 的升起变大、落下变小），从画面左边横着走到锁孔前，往锁孔口推进去，刻度环一格一格咬过去（打分），
    再原路退回地毯、缩回原大；16.9-18.9 s 退到结尾机位（格子 30 在左前、CDK20 和锁在右后）；没进短名单的钥匙从远到近一片片
    往上升出画外（W3 落雨倒过来），剩 54 把；再升走 47 把，7 把贴着台面在格子 30 里滑成一行，刀刃朝画面右边；最后 1 秒不动。
    不放大东西给人看；不悬空（只有正在拿起、飞、落下的那几秒离台）。"""
    upd_w3 = w3_end(sc, sky)
    v0 = upd_w3.view(951 / FPS)
    ob = bpy.data.objects

    lk = ob["w3_lock"]
    LC = Vector(lk.location)
    LS = lk.scale[0]

    keys = [o for o in _with_prefix("w3_rain") + _with_prefix("w3_orb") + [ob["w3_hover"]]
            if o.type == "EMPTY" and len(o.children)]
    for o in keys:
        o.animation_data_clear()
        show(o, True)
    home = {o.name: Vector(o.location) for o in keys}
    rot0 = {o.name: Quaternion(o.rotation_quaternion) for o in keys}
    KS = keys[0].scale[0]
    mov = ob["w3_hover"]

    # W3 的 24 种刀片网格整体在 z = -5（钥匙坐标）：shot_w3 先把刀片物体挪到 -5 藏起来，网格跟着烤进去了，
    # 换到钥匙上以后刀片在钥匙下面 0.086，躺在地毯上时藏在台面底下，只看得见圆头。这里拷一份抬回 0（和 4-09 的 hk_blade 一样在 -0.1..0.1）。
    if not os.environ.get("BL_W3BLADE"):
        fixed = {}
        for o in keys:
            for ch in o.children:
                me = ch.data
                if not me.name.startswith("w3_blade"):
                    continue
                if me.name not in fixed:
                    vv = np.zeros(len(me.vertices) * 3)
                    me.vertices.foreach_get("co", vv)
                    vv = vv.reshape(-1, 3)
                    m2 = me.copy()
                    m2.name = me.name + "_up"
                    if vv[:, 2].mean() < -1.0:
                        vv[:, 2] += 5.0
                    m2.vertices.foreach_set("co", vv.ravel())
                    m2.update()
                    fixed[me.name] = m2
                ch.data = fixed[me.name]

    # 钥匙自己的点（空物体坐标，未乘 KS），给穿模检查和贴锁孔用
    bpy.context.view_layer.update()
    inv = mov.matrix_world.inverted()
    kpts = []
    for ch in mov.children:
        for v in ch.data.vertices:
            kpts.append(tuple(inv @ (ch.matrix_world @ v.co)))
    kpts = np.array(kpts)
    kpts = kpts[np.linspace(0, len(kpts) - 1, min(600, len(kpts))).astype(int)]

    # ---------------------------------------------------------------- 短名单 54、挑出来的 7
    c30, c39 = Vector((*cell_at(30), 0.0)), Vector((*cell_at(39), 0.0))
    in30 = sorted([o for o in keys if abs(home[o.name].x - c30.x) < 0.45 and abs(home[o.name].y - c30.y) < 0.4],
                  key=lambda o: (-round(home[o.name].y, 3), home[o.name].x))
    keep = [in30[int(round(i * (len(in30) - 1) / 53.0))] for i in range(54)]          # 均匀散在格子 30 里
    if mov not in keep:
        j = min(range(54), key=lambda i: (home[keep[i].name] - home[mov.name]).length)
        keep[j] = mov
    by_x = sorted(keep, key=lambda o: home[o.name].x)
    seven = [by_x[int(round(i * 53 / 6.0))] for i in range(7)]
    if mov not in seven:
        j = min(range(7), key=lambda i: abs(home[seven[i].name].x - home[mov.name].x))
        seven[j] = mov
    seven = sorted(seven, key=lambda o: home[o.name].x)
    keep_n, seven_n = {o.name for o in keep}, {o.name for o in seven}
    # 7 把在格子 30 前半排成一行，刀刃朝画面右边：行的方向就是结尾机位的横向（az 20°）
    ROW_GAP, ROW_YAW = 0.08, math.radians(20.0)
    ROW_C = Vector((126.12, -3.30, 0.0))
    ru = Vector((math.cos(ROW_YAW), math.sin(ROW_YAW), 0.0))
    seven = sorted(seven, key=lambda o: home[o.name].dot(ru))
    row_at = {o.name: Vector((ROW_C.x, ROW_C.y, home[o.name].z)) + ru * (i - 3) * ROW_GAP for i, o in enumerate(seven)}
    q_row = Quaternion((0, 0, 1), ROW_YAW)

    # ---------------------------------------------------------------- 时刻（片中秒，4-10 起点算 0）
    T_M1, T_M1E = 5.0, 7.2            # 全景 → 锁近景
    T_UP, T_FLY, T_SIDE, T_FRONT, T_IN = 7.3, 7.8, 9.2, 10.0, 10.7          # 钥匙：升起、飞、到锁左边、到锁孔前、推到锁孔口
    T_CLICK0, T_CLICK1 = 11.0, 15.2   # 刻度环咬 8 格（"scores the fit"）
    T_BACK, T_HOME = 15.5, 16.8       # 退回地毯
    T_M2, T_M2E = 16.9, 18.9          # 锁近景 → 结尾机位
    T_THIN = 18.9                      # 没进短名单的升走
    T_47 = 20.7                        # 短名单里没被挑的 47 把升走
    T_SLIDE = 21.9                     # 7 把贴着台面滑成一行
    RISE, RISE_H = 0.9, 3.0

    # ---------------------------------------------------------------- 相机
    # 第 3 版（SilverHawk 第 3 轮建议）：锁近景 at 往左后挪，4-09 传送带九成出画、不压右下出处行；结尾 el 21→24、d 2.8→2.9，看 7 把的视线 25.4°→28.2°
    lock_v = dict(at=(LC.x - 0.40, LC.y - 0.05, LC.z - 0.20), az=math.radians(26.0), el=math.radians(30.0), d=4.2, mm=45.0)
    end_v = dict(at=(126.35, -3.12, 0.2), az=math.radians(20.0), el=math.radians(24.0), d=2.9, mm=45.0)
    if os.environ.get("BL_S410_END"):          # 备选结尾取景，只出静帧给导演挑："x,y,z,az,el,d"
        _e = [float(v) for v in os.environ["BL_S410_END"].split(",")]
        end_v = dict(at=tuple(_e[:3]), az=math.radians(_e[3]), el=math.radians(_e[4]), d=_e[5], mm=float(_e[6]) if len(_e) > 6 else 45.0)

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M1:
            return dict(v0)
        if t < T_M1E:
            return fall(v0, lock_v, smooth((t - T_M1) / (T_M1E - T_M1)))
        if t < T_M2:
            return dict(lock_v)
        if t < T_M2E:
            return mix(lock_v, end_v, smooth((t - T_M2) / (T_M2E - T_M2)))
        return dict(end_v)

    def focus(t):
        """对焦跟着主角：地毯 → 锁孔 → 前排。"""
        fa = Vector(v0["at"])
        fl = Vector((LC.x, LC.y - 0.2, LC.z))
        fe = Vector((ROW_C.x, ROW_C.y, 0.0))
        if t < T_M1E:
            return fa.lerp(fl, smooth((t - T_M1) / (T_M1E - T_M1)))
        return fl.lerp(fe, smooth((t - T_M2) / (T_M2E - T_M2)))

    # ---------------------------------------------------------------- 试锁那把
    q_flat = Quaternion((1, 0, 0), 0.0)
    q_face = Quaternion((1, 0, 0), math.pi / 2)          # 立在和锁板平行的平面里，正面对镜头，刀刃朝 +x（锁孔那边）
    KSH = 3.2                                            # W3 里悬在锁前那把的大小
    # 锁孔口在哪：锁板和轮廓在锁孔附近最靠前的面
    front_y = None
    for ch in lk.children_recursive:
        if ch.type != "MESH" or ch.name.startswith(("w3_ring", "w3_ticks", "w3_notch")):
            continue
        mw = ch.matrix_world
        for v in ch.data.vertices:
            p = mw @ v.co
            if abs(p.x - LC.x) < 0.13 and abs(p.z - LC.z) < 0.08:
                front_y = p.y if front_y is None else min(front_y, p.y)
    back_k = float((kpts @ np.array(q_face.to_matrix()).T)[:, 1].max()) * KS * KSH          # 钥匙朝锁板那一面离中心多远
    Y_IN = front_y - back_k - 0.006
    if os.environ.get("BL_CLASHTEST"):          # 自测穿模检查：故意把钥匙推进锁板 1 厘，检查应当报 lock
        Y_IN = front_y + 0.01
    Y_OUT = LC.y - 0.24
    start = home[mov.name]
    p_up = Vector((start.x, start.y, 0.25))
    p_side = Vector((LC.x - 0.5, Y_OUT, LC.z))
    p_front = Vector((LC.x, Y_OUT, LC.z))
    p_in = Vector((LC.x, Y_IN, LC.z))

    def bez3(a_, b_, c_, d_, x):
        return (1 - x) ** 3 * a_ + 3 * (1 - x) ** 2 * x * b_ + 3 * (1 - x) * x ** 2 * c_ + x ** 3 * d_

    def trip(t):
        """去的路：升起 → 飞到锁左边（一边长大、一边立起来）→ 横着走到锁孔前 → 推到锁孔口。回来是同一条路倒着走。"""
        if t < T_UP:
            return start, q_flat, 1.0
        if t < T_FLY:
            x = smooth((t - T_UP) / (T_FLY - T_UP))
            return start.lerp(p_up, x), q_flat, 1.0
        if t < T_SIDE:
            x = (t - T_FLY) / (T_SIDE - T_FLY)
            y = smooth(x)
            return bez3(p_up, p_up + Vector((0, 0, 0.45)), p_side - Vector((0.3, 0, 0)), p_side, y), q_flat.slerp(q_face, smooth(x / 0.7)), 1.0 + (KSH - 1.0) * smooth(x / 0.5)
        if t < T_FRONT:
            return p_side.lerp(p_front, smooth((t - T_SIDE) / (T_FRONT - T_SIDE))), q_face, KSH
        if t < T_IN:
            return p_front.lerp(p_in, smooth((t - T_FRONT) / (T_IN - T_FRONT))), q_face, KSH
        # 在锁孔口贴着锁板的平面轻轻左右转着找角度（转轴是锁板的法线），往回退时摆正；钥匙对角半长 0.10，离最里一圈刻度环 0.25，转不碰。
        # 再叠一个 1.5° 的慢摆和 3 mm 的慢慢上抬，钥匙在锁口每一帧都在动（BL_CAMCHECK 把停在半空、矩阵不变的东西记成悬空）；上抬在退回时收掉
        x = min(1.0, (t - T_IN) / (T_BACK - T_IN))
        a_ = math.radians(7.0) * math.sin(2 * math.pi * 2.5 * x) * (1 - smooth(x)) * smooth(x / 0.15) + math.radians(1.5) * math.sin(math.pi * x)
        return p_in + Vector((0, 0, LIFT * x)), Quaternion((0, 1, 0), a_) @ q_face, KSH

    LIFT = 0.003

    def mov_pose(t):
        if t < T_BACK:
            return trip(t)
        x = (t - T_BACK) / (T_HOME - T_BACK)
        if x >= 1:
            return seven_pose(mov, t)
        p_, q_, k_ = trip(T_IN - x * (T_IN - T_UP))    # 原路倒回去，快一倍多
        return p_ + Vector((0, 0, LIFT * (1 - smooth(min(1.0, x / 0.3))))), q_, k_

    # ---------------------------------------------------------------- 地毯上的其他钥匙
    far_order = sorted([o for o in keys if o.name not in keep_n], key=lambda o: (-home[o.name].y, home[o.name].x))
    t_out = {o.name: T_THIN + 1.2 * i / max(1, len(far_order) - 1) for i, o in enumerate(far_order)}
    cut47 = sorted([o for o in keep if o.name not in seven_n], key=lambda o: (-home[o.name].y, home[o.name].x))
    t_out.update({o.name: T_47 + 0.3 * i / max(1, len(cut47) - 1) for i, o in enumerate(cut47)})

    def seven_pose(o, t):
        s_, e_ = home[o.name], row_at[o.name]
        i = seven.index(o)
        x = (t - T_SLIDE - 0.05 * i) / 1.4
        if x <= 0:
            return s_, q_flat, 1.0
        if x >= 1:
            return e_, q_row, 1.0
        u = smooth(x)          # 贴着台面滑过去、转过来，缓停，不弹
        return s_.lerp(e_, u), q_flat.slerp(q_row, u), 1.0

    def pose(o, t):
        """位置、转角、大小（乘 KS 之前）；None 是已经不在了。"""
        nm = o.name
        if nm == mov.name:
            return mov_pose(t)
        if nm in seven_n:
            return seven_pose(o, t)
        if nm in t_out:
            x = (t - t_out[nm]) / RISE
            if x <= 0:
                return home[nm], rot0[nm], 1.0
            if x >= 1:
                return None
            return home[nm] + Vector((0, 0, RISE_H * x * x)), rot0[nm], 1.0
        return home[nm], rot0[nm], 1.0

    # ---------------------------------------------------------------- 刻度环：咬 8 格
    dials = [ob.get("w3_dial%d" % k) for k in range(3)]
    DIAL_N = (36, 24, 16)
    dial0 = [Quaternion(e.rotation_quaternion) if e is not None else None for e in dials]

    def dial_q(k, t):
        n_steps = 8
        if t <= T_CLICK0:
            st = 0.0
        else:
            b_ = min(n_steps, (t - T_CLICK0) / ((T_CLICK1 - T_CLICK0) / n_steps))
            st = math.floor(b_) + (smooth((b_ % 1) / 0.3) if b_ < n_steps else 0.0)
        return dial0[k] @ Quaternion((0, 0, 1), (1 if k != 1 else -1) * st * 2 * math.pi / DIAL_N[k])

    # ---------------------------------------------------------------- 逐帧
    def place(e, ps):
        if ps is None:
            show(e, False)
            return
        show(e, True)
        e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3

    def keyed(e, t, f):
        """f-1、f、f+1 三帧打关键帧，动态模糊才有。"""
        e.animation_data_clear()
        for df in (-1, 0, 1):
            ps = pose(e, t + df / FPS)
            if ps is None:
                continue
            e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3
            for path in ("location", "rotation_quaternion", "scale"):
                e.keyframe_insert(path, frame=f + df)
        place(e, pose(e, t))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def update(t_abs):
        t = t_abs - T0
        f = int(round(t * FPS))
        v = cam(t)
        shoot(c, f, v, focus(t))
        for o in keys:
            ps = pose(o, t)
            nx = pose(o, t + 1 / FPS)
            pv = pose(o, t - 1 / FPS)
            moving = ps is not None and ((nx is not None and ((nx[0] - ps[0]).length > 1e-6 or abs(nx[2] - ps[2]) > 1e-6 or nx[1].rotation_difference(ps[1]).angle > 1e-5))
                                         or (pv is not None and (pv[0] - ps[0]).length > 1e-6))
            if moving:
                keyed(o, t, f)
            else:
                o.animation_data_clear()
                place(o, ps)
        g_ = 1.0 - smooth((t - T_UP) / 0.6) if t >= T_UP else 0.0          # W3 的提示光：升起那一下亮，0.6 秒退掉
        for ch in mov.children:
            ch.color = (g_, 0, 0, 1)
        for k, e in enumerate(dials):
            if e is not None:
                e.rotation_quaternion = dial_q(k, t)
        sky(0.2)

    update.view = cam
    update.ctx = dict(keys=keys, mov=mov, home=home, rot0=rot0, KS=KS, KSH=KSH, kpts=kpts, LC=LC, lk=lk, dials=dials, dial0=dial0, DIAL_N=DIAL_N,
                      q_face=q_face, q_row=q_row, row_at=row_at, seven=seven, p_side=p_side, p_front=p_front, p_in=p_in, lock_v=lock_v, end_v=end_v,
                      t_out=t_out, seven_n=seven_n, keyed_pose=pose)
    print("S410 keys %d in30 %d keep %d seven %d KS %.5f front_y %.4f Y_IN %.4f back_k %.4f" % (len(keys), len(in30), len(keep_n), len(seven_n), KS, front_y, Y_IN, back_k))
    print("S410 seven homes", [tuple(round(v, 3) for v in home[o.name]) for o in seven])

    # ---------------------------------------------------------------- 穿模检查：每两帧一次，不渲染（只在 s410 自己跑时）
    if SHOT == "s410" and not os.environ.get("BL_NOCHECK"):
        from mathutils.bvhtree import BVHTree
        dg = bpy.context.evaluated_depsgraph_get()

        def bvh_of(objs):
            vs, fs = [], []
            for o in objs:
                me = o.evaluated_get(dg).to_mesh()
                mw = o.matrix_world
                n0 = len(vs)
                vs += [tuple(mw @ v.co) for v in me.vertices]
                fs += [tuple(n0 + i for i in p.vertices) for p in me.polygons]
            return BVHTree.FromPolygons(vs, fs)
        lock_parts = [o for o in lk.children_recursive if o.type == "MESH" and not o.hide_render]
        bv_lock = bvh_of(lock_parts)
        bv_core = bvh_of([o for o in ob if o.type == "MESH" and (o.name == "core" or (o.parent is not None and o.parent.name == "core"))])
        others = []
        for o in ob:
            if o.type != "MESH" or o.hide_render or o.name.startswith(("w3_", "floor", "cell")) or o in lock_parts:
                continue
            p_ = o
            while p_.parent is not None:
                p_ = p_.parent
            if p_.name.startswith("w3_"):
                continue
            bb = np.array([tuple(o.matrix_world @ Vector(b_)) for b_ in o.bound_box])
            if (bb.max(0) - bb.min(0))[:2].max() < 1.5:
                others.append((o, bb.min(0), bb.max(0)))
        bv_o = {}

        def in_rims(p):
            out_ = np.zeros(len(p), bool)
            for i_ in range(63):
                x_, y_ = cell_at(i_)
                dx, dy = np.abs(p[:, 0] - x_), np.abs(p[:, 1] - y_)
                out_ |= (dx < 0.437) & (dy < 0.352) & ~((dx < 0.418) & (dy < 0.333)) & (p[:, 2] < 0.0175)
            return out_

        def world(ps):
            loc, q, s_ = ps
            return kpts @ np.array(q.to_matrix()).T * (KS * s_) + np.array(tuple(loc))
        bad = {}

        def hit(name, t):
            bad.setdefault(name, []).append(round(t, 2))
        near_min = [9.0]
        rest_w = {}
        for f in range(0, FRAMES, 2):
            t = f / FPS
            W_ = {}
            for o in keys:
                ps = pose(o, t)
                if ps is None:
                    continue
                if ps[0] == home[o.name] and ps[2] == 1.0 and ps[1] == rot0[o.name]:
                    W_[o.name] = None          # 躺在原位，没动
                    continue
                W_[o.name] = world(ps)
            for nm, w_ in W_.items():
                if w_ is None:
                    continue
                rising = nm in t_out and nm not in seven_n and nm != mov.name          # 从原位笔直往上升，脚下和四周都空着，只查上面有没有东西
                if not rising:
                    if (w_[:, 2] < 1e-4).any():
                        hit("key %s / table" % nm, t)
                    if in_rims(w_).any():
                        hit("key %s / cell rim" % nm, t)
                lo_, hi_ = w_.min(0), w_.max(0)
                if hi_[2] > 0.5 and lo_[0] < 127.7 and hi_[0] > 126.6:
                    dmin = min(bv_lock.find_nearest(Vector(tuple(p)))[3] for p in w_[::3])
                    near_min[0] = min(near_min[0], dmin)
                    if dmin < 0.002:
                        hit("key %s / lock" % nm, t)
                if lo_[2] < 0.6 and hi_[0] > 126.7 and lo_[0] < 127.3 and hi_[1] > -2.7 and min(bv_core.find_nearest(Vector(tuple(p)))[3] for p in w_[::5]) < 0.003:
                    hit("key %s / CDK20" % nm, t)
                for o, lo, hi in others:
                    if (hi_ < lo - 0.002).any() or (lo_ > hi + 0.002).any():
                        continue
                    inb = ((w_ > lo - 0.002) & (w_ < hi + 0.002)).all(1)
                    if inb.any():
                        if o.name not in bv_o:
                            bv_o[o.name] = bvh_of([o])
                        if min(bv_o[o.name].find_nearest(Vector(tuple(p)))[3] for p in w_[inb][::2]) < 0.001:
                            hit("key %s / %s" % (nm, o.name), t)
            for nm in [n for n in (mov.name, *seven_n) if W_.get(n) is not None]:          # 试锁那把和 7 把：和离得近的每一把钥匙比
                c_ = W_[nm].mean(0)
                for o2 in keys:
                    n2 = o2.name
                    if n2 == nm or n2 not in W_:
                        continue
                    p2 = pose(o2, t)[0]
                    if (Vector(tuple(c_)) - p2).length > 0.3:
                        continue
                    if W_[n2] is None:
                        if n2 not in rest_w:
                            rest_w[n2] = world((home[n2], rot0[n2], 1.0))
                        w2 = rest_w[n2]
                    else:
                        w2 = W_[n2]
                    if np.sqrt(((W_[nm][::3, None] - w2[None, ::3]) ** 2).sum(-1)).min() < 0.0012:
                        hit("key %s / key %s" % tuple(sorted((nm, n2))), t)
        kinds = {}
        for k, v in bad.items():
            kinds.setdefault(k.split(" / ")[-1].split(" ")[0], []).append((k, v[0]))
        print("S410 clashes:", "none" if not bad else "")
        for kd, l_ in sorted(kinds.items()):
            print("S410 clash %s: %d, first %s" % (kd, len(l_), sorted(l_, key=lambda z: z[1])[:5]))
        print("S410 closest the moving key comes to the lock: %.4f" % near_min[0])
    return update


SHOTS["s410"] = shot_s410

def shot_s504(sc, sky):
    """5-04（11:02-11:26，C 画外音）三维版第一版（Claude，11-10）。接 4-10 的最后一帧（5-03 还没做，做的时候让它停在这一帧）。
    0-1 s 不动；001 的钥匙（4-10 里试过锁、进了 7 把的那一把）从那一行升起，相机跟着它回到锁的近景，钥匙进到锁孔口；
    想拧，只拧得动 7 度上下就顶住（晃两下停住），刻度环只咬一格；10.4-12.4 s 相机退到格子 21：一管酶活（克莱因蓝，CDK20 的颜色）
    和一条墨线剂量尺（6 格，不标数）。滑块从小剂量往大剂量走，蓝液一点点往下，走完 6 格还没到一半；滑块滑过尺子的头、一直到格子边，
    蓝液才落到一半那条线（"Above 6,000 nanomolar"）。数字（> 6,000 nM）和红笔 weak. 在 Remotion 里叠，照 s4/5-04_数字对照.md。"""
    import bmesh
    upd410 = shot_s410(sc, sky)
    X = upd410.ctx
    upd410(T0 + 1499 / FPS)                          # 4-10 的最后一帧
    ob = bpy.data.objects
    for o in ob:
        o.animation_data_clear()
    T5 = META["s504"][0]
    keys, mov, KS, KSH, kpts, LC = X["keys"], X["mov"], X["KS"], X["KSH"], X["kpts"], X["LC"]
    q_face, q_row, p_side, p_front, p_in = X["q_face"], X["q_row"], X["p_side"], X["p_front"], X["p_in"]
    lock_v, end_v, dials, dial0, DIAL_N = X["lock_v"], X["end_v"], X["dials"], X["dial0"], X["DIAL_N"]
    start = Vector(X["row_at"][mov.name])

    # ---------------------------------------------------------------- 格子 21：一管酶活、一条剂量尺、一个滑块（材质都拿台面上现成的）
    mat_of = lambda name: ob[name].material_slots[0].material
    glass = mat_of("hk_tube")
    steel = next(c_ for c_ in mov.children if c_.name.startswith("hk_bow")).material_slots[0].material.copy()
    # 钥匙的材质带 W3 那种"点亮"的自发光（跟着物体颜色走），滑块用一份不发光的拷贝（04 第 2 节不新加发光）
    steel.name = "s504_steel"
    for nd in steel.node_tree.nodes:
        for k in ("Emission Strength", "Strength"):
            if k in nd.inputs and (nd.type == "BSDF_PRINCIPLED" or nd.type == "EMISSION"):
                for ln in list(nd.inputs[k].links):
                    steel.node_tree.links.remove(ln)
                nd.inputs[k].default_value = 0.0
    steel.node_tree.animation_data_clear()
    ink = mat_of("w3_ticks0")
    blue = next(o for o in ob if o.type == "MESH" and len(o.material_slots) and (o.name == "core" or (o.parent is not None and o.parent.name == "core"))).material_slots[0].material
    c21 = Vector((*cell_at(21), 0.0))
    TUBE = Vector((c21.x - 0.33, c21.y + 0.08, 0.0))
    TR, TH_ = 0.032, 0.30
    tube = lathe([(0, 0.0), (TR, 0.0), (TR, TH_), (0.0, TH_ + 0.0005)], glass, "s504_tube", None, 48)
    tube.location = TUBE
    tube.visible_shadow = False
    fill = lathe([(0, 0.0015), (TR - 0.003, 0.0015), (TR - 0.003, 1.0), (0, 1.0)], blue, "s504_fill", None, 48)
    fill.parent = tube                                          # 蓝液和一半那条线都挂在管子上，算管子的一部分
    FILL0 = TH_ - 0.02
    half = lathe([(TR + 0.0004, -0.0012), (TR + 0.0022, -0.0012), (TR + 0.0022, 0.0012), (TR + 0.0004, 0.0012)], ink, "s504_half", tube, 48)
    half.location = (0, 0, FILL0 / 2)                           # 一半那条线，刻在管子外面
    AX0, AX1, AY = c21.x - 0.24, c21.x + 0.28, c21.y - 0.10   # 剂量尺：6 格
    AXH = 0.0016

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
    box("s504_axis", (AX0, AY - 0.003, 0.0), (AX1, AY + 0.003, AXH), ink)
    for i in range(7):
        x_ = AX0 + (AX1 - AX0) * i / 6
        box("s504_tick%d" % i, (x_ - 0.0025, AY - 0.022, 0.0), (x_ + 0.0025, AY - 0.003, AXH), ink)
    MK = 0.028
    marker = box("s504_marker", (-MK / 2, -MK / 2, 0.0), (MK / 2, MK / 2, 0.018), steel)
    MK_Y = AY + 0.020                                           # 滑块走在尺子后面一点，贴着台面，不压尺子
    MK_END = c21.x + 0.35                                       # 过了尺子头（AX1 = +0.28），停在格子里，不压格子边
    marker.location = (AX0, MK_Y, 0.0)

    # ---------------------------------------------------------------- 时刻
    T_UP, T_FLY, T_SIDE, T_FRONT, T_IN = 1.0, 1.5, 3.0, 3.6, 4.2
    T_TRY = 5.0                       # 拧
    T_M1, T_M1E = 1.6, 3.8            # 相机跟着钥匙回锁近景
    T_M2, T_M2E = 10.4, 12.4          # 退到格子 21
    T_DOSE0, T_DOSE1 = 13.4, 17.8     # 滑块走过 6 格
    T_PAST0, T_PAST1 = 17.8, 19.4     # 滑过尺子头，到格子边；蓝液落到一半
    assay_v = dict(at=(125.95, -2.2, 0.05), az=math.radians(0.0), el=math.radians(32.0), d=1.6, mm=45.0)
    LEAD = float(os.environ.get("BL_S504_LEAD", "0.6"))   # 退到格子 21 时 at 先走完的比例

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M1:
            return dict(end_v)
        if t < T_M1E:
            return mix(end_v, lock_v, smooth((t - T_M1) / (T_M1E - T_M1)))
        if t < T_M2:
            return dict(lock_v)
        if t < T_M2E:
            # 先往左摇、再推近：锁从画面右边出去，不从右上标题框后面扫过
            x = (t - T_M2) / (T_M2E - T_M2)
            v = mix(lock_v, assay_v, smooth(x))
            v["at"] = lerp(lock_v["at"], assay_v["at"], smooth(min(1.0, x / LEAD)))
            return v
        return dict(assay_v)

    def focus(t):
        a_, b_, c_ = start, Vector((LC.x, LC.y - 0.2, LC.z)), Vector((c21.x, AY, 0.05))
        if t < T_M2:
            return a_.lerp(b_, smooth((t - T_M1) / (T_M1E - T_M1)))
        return b_.lerp(c_, smooth((t - T_M2) / (T_M2E - T_M2)))

    p_up = Vector((start.x, start.y, 0.25))

    def bez3(a_, b_, c_, d_, x):
        return (1 - x) ** 3 * a_ + 3 * (1 - x) ** 2 * x * b_ + 3 * (1 - x) * x ** 2 * c_ + x ** 3 * d_

    def turn(t):
        """想拧：7 度就顶住，晃两下停住。转轴是锁板法线（钥匙贴着锁板的平面转）。"""
        if t < T_TRY:
            return 0.0
        x = t - T_TRY
        return math.radians(7.0 * smooth(x / 0.5) + 2.0 * math.sin(2 * math.pi * x / 0.32) * math.exp(-x * 2.2) * smooth(x / 0.3))

    def mov_pose(t):
        if t < T_UP:
            return start, q_row, 1.0
        if t < T_FLY:
            return start.lerp(p_up, smooth((t - T_UP) / (T_FLY - T_UP))), q_row, 1.0
        if t < T_SIDE:
            x = (t - T_FLY) / (T_SIDE - T_FLY)
            return bez3(p_up, p_up + Vector((0, 0, 0.45)), p_side - Vector((0.3, 0, 0)), p_side, smooth(x)), q_row.slerp(q_face, smooth(x / 0.7)), 1.0 + (KSH - 1.0) * smooth(x / 0.5)
        if t < T_FRONT:
            return p_side.lerp(p_front, smooth((t - T_SIDE) / (T_FRONT - T_SIDE))), q_face, KSH
        if t < T_IN:
            return p_front.lerp(p_in, smooth((t - T_FRONT) / (T_IN - T_FRONT))), q_face, KSH
        # 卡在锁里时慢慢往上抬 3 mm，到镜头离开锁为止；不然 BL_CAMCHECK 把它记成停在半空（4-10 锁口那段同样处理）
        return p_in + Vector((0, 0, 0.003 * min(1.0, (t - T_IN) / (T_M2E - T_IN)))), Quaternion((0, 1, 0), turn(t)) @ q_face, KSH

    def dial_q(k, t):
        st = smooth((t - T_TRY - 0.1) / 0.3)          # 只咬一格
        return dial0[k] @ Quaternion((0, 0, 1), (1 if k != 1 else -1) * st * 2 * math.pi / DIAL_N[k])

    def dose_x(t):
        if t < T_DOSE0:
            return AX0
        if t < T_DOSE1:
            return AX0 + (AX1 - AX0) * smooth((t - T_DOSE0) / (T_DOSE1 - T_DOSE0))
        return AX1 + (MK_END - AX1) * smooth((t - T_PAST0) / (T_PAST1 - T_PAST0))

    def level(t):
        """酶活：走完 6 格只掉到八成，过了尺子头才落到一半。"""
        a_ = 0.2 * smooth((t - T_DOSE0) / (T_DOSE1 - T_DOSE0))
        b_ = 0.3 * smooth((t - T_PAST0) / (T_PAST1 - T_PAST0 + 0.3))
        return 1.0 - a_ - b_          # 1.0 → 0.8 → 0.5

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def keyed(e, t, f, fn):
        e.animation_data_clear()
        for df in (-1, 0, 1):
            ps = fn(t + df / FPS)
            e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3
            for path in ("location", "rotation_quaternion", "scale"):
                e.keyframe_insert(path, frame=f + df)
        ps = fn(t)
        e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3

    def update(t_abs):
        t = t_abs - T5
        f = int(round(t * FPS))
        v = cam(t)
        shoot(c, f, v, focus(t))
        if T_UP - 0.02 <= t <= T_IN + 0.02 or T_TRY <= t <= T_TRY + 3.0:
            keyed(mov, t, f, mov_pose)
        else:
            mov.animation_data_clear()
            ps = mov_pose(t)
            mov.location, mov.rotation_quaternion, mov.scale = ps[0], ps[1], (KS * ps[2],) * 3
        show(mov, True)
        g_ = 1.0 - smooth((t - T_UP) / 0.6) if t >= T_UP else 0.0
        for ch in mov.children:
            ch.color = (g_, 0, 0, 1)
        for k, e in enumerate(dials):
            if e is not None:
                e.rotation_quaternion = dial_q(k, t)
        marker.location = (dose_x(t), MK_Y, 0.0)
        fill.scale = (1.0, 1.0, FILL0 * level(t))
        sky(0.2)

    update.view = cam
    print("S504 start %s p_in %s tube %s axis %.3f-%.3f marker end %.3f" % (tuple(round(v, 3) for v in start), tuple(round(v, 3) for v in p_in), tuple(round(v, 3) for v in TUBE), AX0, AX1, MK_END))

    # ---------------------------------------------------------------- 穿模检查（每两帧，不渲染，只在 s504 自己跑时）
    if SHOT == "s504" and not os.environ.get("BL_NOCHECK"):
        from mathutils.bvhtree import BVHTree
        dg = bpy.context.evaluated_depsgraph_get()
        lock_parts = [o for o in X["lk"].children_recursive if o.type == "MESH" and not o.hide_render]
        vs, fs = [], []
        for o in lock_parts:
            me = o.evaluated_get(dg).to_mesh()
            n0 = len(vs)
            vs += [tuple(o.matrix_world @ v_.co) for v_ in me.vertices]
            fs += [tuple(n0 + i for i in p_.vertices) for p_ in me.polygons]
        bv_lock = BVHTree.FromPolygons(vs, fs)
        bad, near = {}, [9.0]
        others = [o for o in keys if o is not mov and not all(ch.hide_render for ch in o.children)]
        for f in range(0, FRAMES, 2):
            t = f / FPS
            loc, q, s_ = mov_pose(t)
            w_ = kpts @ np.array(q.to_matrix()).T * (KS * s_) + np.array(tuple(loc))
            if (w_[:, 2] < 1e-4).any():
                bad.setdefault("key / table", []).append(t)
            if w_[:, 2].max() > 0.5:
                dmin = min(bv_lock.find_nearest(Vector(tuple(p_)))[3] for p_ in w_[::3])
                near[0] = min(near[0], dmin)
                if dmin < 0.002:
                    bad.setdefault("key / lock", []).append(t)
            if t < T_SIDE:
                for o in others:
                    if (o.location - loc).length < 0.3:
                        w2 = kpts @ np.array(o.rotation_quaternion.to_matrix()).T * KS + np.array(tuple(o.location))
                        if np.sqrt(((w_[::3, None] - w2[None, ::3]) ** 2).sum(-1)).min() < 0.0012:
                            bad.setdefault("key / key %s" % o.name, []).append(t)
            mx = dose_x(t)          # 滑块：不碰尺子（在尺子后面走）、不压管子、不出格子
            if abs(MK_Y - AY) < MK / 2 + 0.003 + 0.001 or mx + MK / 2 > c21.x + 0.418 or (Vector((mx, MK_Y, 0)) - TUBE).length < TR + MK * 0.71:
                bad.setdefault("marker", []).append(t)
        print("S504 clashes:", "none" if not bad else "")
        for k, v in bad.items():
            print("S504 clash %s: %d, first %.2f" % (k, len(v), v[0]))
        print("S504 closest the key comes to the lock: %.4f" % near[0])
    return update


SHOTS["s504"] = shot_s504
