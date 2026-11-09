"""HKBU SCIE1007 课程作业的科普视频。S7（15:15-16:04，A 画外音）的三段 3D 插入，写在我自己的文件里，由 bl_inserts.py 的 BL_EXTRA 接口运行，不改 bl_inserts.py。
分镜 fusion/s7s8/00_S7S8分镜_v1.md。三段都接 4-09 钥匙版（shot_hk）最后一帧的台面：CDK20、AI 屏幕和 42 个环、传送带、门、桶、打分管都停在 4-09 收尾的样子。

`s703`（7-03，"And feed every result, including the failures, back into the next round"）：4-09 那只装着 4 把被扔钥匙的桶升起来，挪到带子上方，
  倒过来把钥匙一把把倒回带子上；带子倒着走，4-09 留下的 6 把钥匙和倒回来的 4 把一起回到屏幕，各自跳回当初出来的那个环，环亮一下。桶回原位。
  每把被扔的钥匙落进它在带子上原来的空位（4-09 里它就是从那个位置被扔掉的）。
`s702`（7-02，"Test it in more liver cancer cells and normal liver cells"）：前排一个空格里，两行培养皿（上行肝癌细胞粉色、下行正常肝细胞浅黄）
  一个变两个、两个变四个：新皿从上方竖直放下到自己的位置，不叠在旧皿上。
`s704`（7-04，"An AI route and a classic route"）：旁边空格里两只秒表平放，按钮同时按下，两根红针一起走。

动的东西都按几何算路径；文件末尾每段都有逐帧不渲染的穿模检查，和 shot_hk 用的同一套判据（钥匙对环、屏幕、格子边、带子、门柱门梁、桶、打分管、台面、钥匙之间），
另用 BVH 量最近距离，打印 "s78 ... clashes:" 和 "s78 ... nearest:" 两行。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s78.py blender.exe -b -t 4 -P bl_inserts.py -- s703 <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
只查穿模不渲染：加 BL_S78_CHECK=1（查完就退出）。
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

# 开始时间是片子时钟（秒），和 s78.jsx 里插入的位置对上：S7 从 915.0 s 开始
META = {"s702": (921.5, 330, 0.2, 0.9), "s703": (944.1, 348, 0.2, 0.9), "s704": (951.0, 222, 0.2, 0.9)}          # 7-02 从 15:21.5、7-03 从 15:44.1、7-04 从 15:51.0（S7 的 6.5 s、29.1 s、36.0 s）
HK_END = 1019 / 60.0


def hk_end(sc, sky):
    """4-09 钥匙版最后一帧的台面，摆好后把相机关键帧清掉，交回 shot_hk 的局部变量。"""
    global START
    keep = START
    upd = shot_hk(sc, sky)
    upd(HZ_START + HK_END)
    for o in bpy.data.objects:
        o.animation_data_clear()
    sc.camera.animation_data_clear()
    sc.camera.data.animation_data_clear()
    START = keep
    last_q[0] = None
    return upd.ctx


def deselect():
    """B.extrude 会把所有选中的东西一起应用变换；每做一个就取消选择。"""
    for o in bpy.context.selected_objects:
        o.select_set(False)


def world_bvh(objs):
    vs, fs = [], []
    for o in objs:
        me = o.data
        n0 = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in me.vertices]
        fs += [tuple(n0 + i for i in p_.vertices) for p_ in me.polygons]
    return BVHTree.FromPolygons(vs, fs)


def nearest(tree, pts):
    return min(tree.find_nearest(Vector(tuple(p)))[3] for p in pts)


def run_check(name, check):
    import os
    import sys
    rep = check()
    print("s78 %s clashes:" % name, rep[0])
    print("s78 %s nearest:" % name, rep[1])
    if os.environ.get("BL_S78_CHECK"):
        print("INSERT_OK", name, "check")
        sys.exit(0)


# ================================================================ 7-03 · 桶把钥匙倒回去
def shot_s703(sc, sky):
    C = hk_end(sc, sky)
    keys, key_pose, BAD, TL, T_STOP, VB = C["keys"], C["key_pose"], C["BAD"], C["TL"], C["T_STOP"], C["VB"]
    XS, by, BWD, BH, bx0, bx1, rest_z, q_belt = C["XS"], C["by"], C["BWD"], C["BH"], C["bx0"], C["bx1"], C["rest_z"], C["q_belt"]
    RC, RING, Z_HOV, ZR, HOLE, OUTR, RT, SCR = C["RC"], C["RING"], C["Z_HOV"], C["ZR"], C["HOLE"], C["OUTR"], C["RT"], C["SCR"]
    pings, mp, binn, bin_c = C["pings"], C["mp"], C["binn"], Vector(C["bin_c"])
    BIN_RI0, BIN_RI1, BIN_H, BIN_W, BIN_Z = C["BIN_RI0"], C["BIN_RI1"], C["BIN_H"], C["BIN_W"], C["BIN_Z"]
    gx, GP, GH, gy0, gy1, tubes, t_y, TR, TUH = C["gx"], C["GP"], C["GH"], C["gy0"], C["gy1"], C["tubes"], C["t_y"], C["TR"], C["TUH"]
    in_rim, KS, cx, cy, V = C["in_rim"], C["KS"], C["cx"], C["cy"], C["V"]
    px_c, PW, PH, y_f, y_back = C["px_c"], C["PW"], C["PH"], C["y_f"], C["y_back"]
    NK = len(keys)
    t_end = HK_END
    pose0 = {i: key_pose(i, t_end) for i in range(NK)}
    travel0 = VB * (min(max(t_end, TL[0]), T_STOP) - TL[0])

    # ---------------------------------------------------------------- 时间
    VBB = 0.30                       # 带子倒着走的速度
    T_UP0, T_UP1, T_TIP1 = 0.30, 0.80, 1.40          # 升起；挪到带子上方并倒过来
    T_RUN = 1.50                     # 带子开始倒着走
    X_POUR = XS + 0.17               # 桶口对着的带子位置
    T_BACK0, T_BACK1 = 3.40, 4.40    # 桶回原位
    slot = {i: VB * (T_STOP - TL[i]) for i in range(NK)}          # 每把钥匙在带子上的位置（4-09 结束时，从 XS 量）
    T_LAND = {i: T_RUN + (XS + slot[i] - X_POUR) / VBB for i in BAD}
    T_HOME = {i: T_RUN + slot[i] / VBB for i in range(NK)}            # 到带子起点 XS
    T_HOP, T_SINK = 0.50, 0.35
    SLIDE, DROP = 0.22, 0.30
    print("s703 times: land %s, home %s" % ({i: round(v, 2) for i, v in T_LAND.items()}, {i: round(v, 2) for i, v in T_HOME.items()}))

    # ---------------------------------------------------------------- 桶：绕底面中心转，先升，再挪到带子上方、倒过来
    BASE0 = Vector((bin_c.x, bin_c.y, 0.0))
    TIP = math.radians(135)
    axis_pour = Vector((0, -math.sin(TIP), math.cos(TIP)))
    BASE_P = Vector((X_POUR, 0, 0)) + Vector((0, by, 0.084)) - axis_pour * BIN_H          # 桶口中心在 (X_POUR, by, 0.084)
    UP = Vector((bin_c.x, bin_c.y, BASE_P.z))
    binn.rotation_mode = "QUATERNION"

    def bin_pose(t):
        """桶底中心的位置、转角。"""
        if t < T_UP0:
            return BASE0.copy(), Quaternion()
        if t < T_UP1:
            return BASE0.lerp(UP, smooth((t - T_UP0) / (T_UP1 - T_UP0))), Quaternion()
        if t < T_BACK0:
            x = smooth((t - T_UP1) / (T_TIP1 - T_UP1))
            more = math.radians(12) * smooth((t - T_TIP1) / (T_LAND[BAD[0]] - T_TIP1))          # 一边倒一边再歪一点，最后一把（BAD[0]）落下时到头
            return UP.lerp(BASE_P, x), Quaternion((1, 0, 0), TIP * x + more)
        x = smooth((t - T_BACK0) / (T_BACK1 - T_BACK0))
        q_last = bin_pose(T_BACK0 - 1e-4)[1]
        if x < 0.5:
            y = x / 0.5
            return BASE_P.lerp(UP, y), q_last.slerp(Quaternion(), y)
        return UP.lerp(BASE0, (x - 0.5) / 0.5), Quaternion()

    # ---------------------------------------------------------------- 钥匙
    in_bin = {i: (pose0[i][0] - BASE0, pose0[i][1]) for i in BAD}          # 桶里的钥匙：相对桶底中心

    def bez(a_, c_, b_, x):
        return (1 - x) ** 2 * a_ + 2 * (1 - x) * x * c_ + x ** 2 * b_

    def on_belt_x(i, t):
        return XS + slot[i] - VBB * max(0.0, t - T_RUN)

    def key_at(i, t):
        """钥匙 i 在 t 的位置、转角、大小；None 是已经回到环里不见了。"""
        q_h = Quaternion((0, 0, 1), keys[i]["yaw"])
        if i in BAD and t < T_LAND[i]:
            loc_b, q_b = in_bin[i]
            B_, Q_ = bin_pose(t)
            t_s = T_LAND[i] - DROP - SLIDE
            if t < t_s:
                return B_ + Q_ @ loc_b, Q_ @ q_b, 1.0
            out_loc = Vector((0, 0, BIN_H + 0.034))          # 整把钥匙出了桶口
            if t < t_s + SLIDE:
                y = smooth((t - t_s) / SLIDE)
                return B_ + Q_ @ loc_b.lerp(out_loc, y), Q_ @ q_b, 1.0
            p_out = B_ + Q_ @ out_loc
            q_out = Q_ @ q_b
            y = (t - t_s - SLIDE) / DROP
            land = Vector((X_POUR, by, rest_z))
            ctrl = Vector((X_POUR, p_out.y - 0.01, p_out.z))
            return bez(p_out, ctrl, land, y * y), q_out.slerp(q_belt, smooth(y / 0.8)), 1.0
        if t < T_HOME[i]:
            return Vector((on_belt_x(i, t), by, rest_z)), q_belt, 1.0
        rc = Vector((float(RC[RING[i]][0]), float(RC[RING[i]][1]), ZR))
        hov = Vector((rc.x, rc.y, Z_HOV[i]))
        x = (t - T_HOME[i]) / T_HOP
        if x < 1:          # 跳回自己的环上方：和 4-09 跳上带子是同一条弧，倒着走
            y = smooth(x)
            a_ = Vector((XS, by, rest_z))
            ctrl = Vector(((hov.x + XS) / 2, (hov.y + by) / 2, 0.15))
            return bez(a_, ctrl, hov, y), q_belt.slerp(q_h, y), 1.0
        x = (t - T_HOME[i] - T_HOP) / T_SINK
        if x < 1:          # 沉回环里，变小，和 4-09 从环里出来倒过来
            zz = Z_HOV[i] + (ZR - Z_HOV[i]) * smooth(x)
            return Vector((rc.x, rc.y, zz)), q_h, max(1e-3, 1.0 - smooth(x))
        return None

    def key_world(i, t):
        ps = key_at(i, t)
        if ps is None:
            return None
        loc, q, s_ = ps
        return keys[i]["pts"] @ np.array(q.to_matrix()).T * s_ + np.array(tuple(loc))

    # ---------------------------------------------------------------- 检查（判据照 shot_hk）
    bme = binn.data
    bin_local = BVHTree.FromPolygons([tuple(v.co) for v in bme.vertices], [tuple(p_.vertices) for p_ in bme.polygons])
    bin_v = np.array([tuple(v.co) for v in bme.vertices])
    gate_objs = [o for o in bpy.data.objects if o.name.startswith("hk_post") or o.name.startswith("hk_lintel")]
    gate_t = world_bvh(gate_objs)
    belt_t = world_bvh([bpy.data.objects["hk_belt"]])
    tube_xy = np.array([[v_["x"], t_y] for v_ in tubes.values()])

    def check():
        hits, near = {}, dict(key_bin=9.0, key_gate=9.0, key_belt_gap=9.0, key_key=9.0, bin_gate=9.0, bin_belt_gap=9.0, bin_tube=9.0, bin_table=9.0)

        def hit(nm, t):
            hits.setdefault(nm, []).append(round(t, 2))
        for f in range(0, FRAMES):
            t = f / FPS
            B_, Q_ = bin_pose(t)
            Rm = np.array(Q_.to_matrix())
            bw = bin_v @ Rm.T + np.array(tuple(B_))
            # 桶对台面、带子、门、打分管
            if t > T_UP0 and t < T_BACK1:
                near["bin_table"] = min(near["bin_table"], float(bw[:, 2].min()))
                if (bw[:, 2] < -1e-4).any():
                    hit("bin / table", t)
            onb = (np.abs(bw[:, 0] - (bx0 + bx1) / 2) < (bx1 - bx0) / 2) & (np.abs(bw[:, 1] - by) < BWD / 2)
            if onb.any():
                near["bin_belt_gap"] = min(near["bin_belt_gap"], float(bw[onb, 2].min() - BH))
                if (bw[onb, 2] < BH + 1e-4).any():
                    hit("bin / belt", t)
            if f % 2 == 0:
                near["bin_gate"] = min(near["bin_gate"], nearest(gate_t, bw[::3]))
            if ((np.abs(bw[:, 0] - gx) < GP / 2 + 0.0005) & (((np.abs(bw[:, 1] - gy1) < GP / 2 + 0.0005) & (bw[:, 2] < GH + 0.0145)) | ((bw[:, 1] > gy0 - GP / 2 - 0.0005) & (bw[:, 1] < gy1 + GP / 2 + 0.0005) & (bw[:, 2] > GH - 0.0005) & (bw[:, 2] < GH + 0.0145)))).any():
                hit("bin / gate", t)
            dxy = np.hypot(bw[:, None, 0] - tube_xy[None, :, 0], bw[:, None, 1] - tube_xy[None, :, 1]) - TR
            low = bw[:, 2] < TUH + 0.013
            if low.any():
                near["bin_tube"] = min(near["bin_tube"], float(dxy[low].min()))
                if (dxy[low] < 0.0005).any():
                    hit("bin / tube", t)
            W_ = {i: key_world(i, t) for i in range(NK)}
            Qi = Q_.inverted()
            for i, w_ in W_.items():
                if w_ is None:
                    continue
                # 钥匙对桶：换到桶自己的坐标里，用 shot_hk 的桶壁判据，再量到桶网格的最近距离
                lw = (w_ - np.array(tuple(B_))) @ np.array(Qi.to_matrix()).T
                rb, zb = np.hypot(lw[:, 0], lw[:, 1]), lw[:, 2]
                r_in = BIN_RI0 + (BIN_RI1 - BIN_RI0) * np.clip(zb / BIN_H, 0, 1)
                if (((rb > r_in - 0.0005) & (rb < r_in + BIN_W + 0.0005) & (zb > -0.0005) & (zb < BIN_H + 0.0005)) | ((rb < r_in) & (zb > -0.0005) & (zb < BIN_W + 1e-4))).any():
                    hit("key %d / bin" % i, t)
                if f % 2 == 0:
                    near["key_bin"] = min(near["key_bin"], nearest(bin_local, lw[::4]))
                    near["key_gate"] = min(near["key_gate"], nearest(gate_t, w_[::4]))
                for k in range(1, 42):
                    if k == RING[i] and key_at(i, t)[2] < 0.999:
                        continue          # 正沉进自己的环：变小、从环心走，和 4-09 出来时一样
                    r_ = np.hypot(w_[:, 0] - RC[k][0], w_[:, 1] - RC[k][1])
                    if ((np.abs(w_[:, 2] - ZR) < RT + 0.0005) & (r_ > HOLE - 0.0005) & (r_ < OUTR + 0.0005)).any():
                        hit("key %d / ring %d" % (i, k), t)
                if (w_[:, 2] < SCR - 1e-4).any() and (np.abs(w_[:, 0] - cx) < 0.42).all() and key_at(i, t)[2] > 0.999:
                    hit("key %d / screen" % i, t)
                if in_rim(w_).any():
                    hit("key %d / cell rim" % i, t)
                onb = (np.abs(w_[:, 0] - (bx0 + bx1) / 2) < (bx1 - bx0) / 2) & (np.abs(w_[:, 1] - by) < BWD / 2)
                if onb.any():
                    near["key_belt_gap"] = min(near["key_belt_gap"], float(w_[onb, 2].min() - BH))
                    if (w_[onb, 2] < BH - 1e-4).any():
                        hit("key %d / belt" % i, t)
                if ((np.abs(w_[:, 0] - gx) < GP / 2 + 0.0005) & (((np.abs(w_[:, 1] - gy1) < GP / 2 + 0.0005) & (w_[:, 2] < GH + 0.0145)) | ((w_[:, 1] > gy0 - GP / 2 - 0.0005) & (w_[:, 1] < gy1 + GP / 2 + 0.0005) & (w_[:, 2] > GH - 0.0005) & (w_[:, 2] < GH + 0.0145)))).any():
                    hit("key %d / gate" % i, t)
                if ((np.abs(w_[:, 0] - px_c) < PW / 2 + 0.0005) & (w_[:, 1] > y_f - 0.0003) & (w_[:, 1] < y_back + 0.0005) & (w_[:, 2] < SCR + PH + 0.0005)).any():
                    hit("key %d / plate" % i, t)
                if (np.hypot(w_[:, None, 0] - tube_xy[None, :, 0], w_[:, None, 1] - tube_xy[None, :, 1]) < TR + 0.0005).any() and (w_[:, 2] < TUH + 0.01).any():
                    hit("key %d / tube" % i, t)
                if (w_[:, 2] < 1e-4).any():
                    hit("key %d / table" % i, t)
            for i in range(NK):
                for j in range(i + 1, NK):
                    if W_[i] is None or W_[j] is None:
                        continue
                    a_, b_ = W_[i], W_[j]
                    if np.linalg.norm(a_.mean(0) - b_.mean(0)) > 0.08:
                        continue
                    dmin = float(np.sqrt(((a_[::2, None, :] - b_[None, ::2, :]) ** 2).sum(-1)).min())
                    near["key_key"] = min(near["key_key"], dmin)
                    if dmin < 0.0015:
                        hit("key %d / key %d" % (i, j), t)
        rep = "none" if not hits else "; ".join("%s at %s" % (k, v[:4]) for k, v in sorted(hits.items()))
        return rep, ", ".join("%s %.4f" % kv for kv in near.items())

    # ---------------------------------------------------------------- 相机：先看桶和带子，钥匙往屏幕走时退到能看见屏幕、带子和桶
    v_bin = dict(at=(X_POUR - 0.02, by + 0.02, 0.06), az=math.radians(8), el=math.radians(30), d=0.85, mm=45.0)
    v_wide = dict(at=((cx + X_POUR) / 2 + 0.05, (cy + by) / 2 - 0.02, 0.03), az=math.radians(5), el=math.radians(40), d=1.45, mm=45.0)
    v_end = dict(v_wide, d=1.35, az=math.radians(3))
    cams = [(0.0, v_bin), (1.9, v_bin), (3.0, v_wide), (FRAMES / FPS, v_end)]

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(cams, cams[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return cams[-1][1]

    run_check("s703", check)
    c = sc.camera

    def update(t_abs):
        t = t_abs - START
        f = int(round(t * FPS))
        v = view(t)
        shoot(c, f, v, v["at"])
        B_, Q_ = bin_pose(t)
        binn.location, binn.rotation_quaternion = B_, Q_
        for i, kd in enumerate(keys):
            e = kd["obj"]
            ps = key_at(i, t)
            for o in e.children:
                o.hide_render = ps is None
            if ps is None:
                e.scale = (1e-4,) * 3
                continue
            loc, q, s_ = ps
            e.location, e.rotation_quaternion, e.scale = loc, q, (KS * s_,) * 3
            g_ = smooth((t - T_HOME[i] - T_HOP) / T_SINK) if t > T_HOME[i] + T_HOP else 0.0          # 回到环里时发蓝光，和 4-09 出来时一样
            for o in e.children:
                o.color = (g_, 0, 0, 1)
        for i, o in enumerate(pings):
            x = (t - T_HOME[i] - T_HOP - T_SINK + 0.25) / 0.6
            o.hide_render = not (0 <= x < 1)
            if 0 <= x < 1:
                o.color = (math.sin(math.pi * min(1.0, x * 1.6)) if x < 0.3125 else 1.0 - smooth((x - 0.3125) / 0.6875), 0, 0, 1)
                o.scale = (1 + 0.15 * x, 1 + 0.15 * x, 1.0)
        mp.inputs["Location"].default_value[0] = -(travel0 - VBB * max(0.0, t - T_RUN))
        sky(0.2)
    return update


# ================================================================ 7-02 · 培养皿一个变两个、两个变四个
def shot_s702(sc, sky):
    C = hk_end(sc, sky)
    in_rim = C["in_rim"]
    x0, y0 = cell_at(40)
    glass = B.clear_glass()
    pink = P.gloss((0.86, 0.50, 0.50), 0.35, 0.6)
    pale = P.gloss((0.93, 0.87, 0.72), 0.35, 0.6)
    R_D, H_D, WL = 0.056, 0.014, 0.0016
    rows = [(y0 + 0.11, pink), (y0 - 0.11, pale)]
    xs = [x0 - 0.24 + 0.16 * k for k in range(4)]
    T_IN = [None, 1.0, 2.3, 2.3]          # 第 0 个一开始就在；第 1 个 1.0 s 放下；第 2、3 个 2.3 s 一起放下
    DROP_H, DUR = 0.22, 0.6
    dishes = []
    for r_i, (yy, med) in enumerate(rows):
        for k, xx in enumerate(xs):
            e = empty("s702_dish")
            base = lathe([(0, 0), (R_D, 0), (R_D, H_D), (R_D - WL, H_D), (R_D - WL, WL), (0, WL)], glass, "s702_base", e, 64)
            gel = lathe([(0, WL), (R_D - WL - 0.0004, WL), (R_D - WL - 0.0004, WL + 0.006), (0, WL + 0.0066)], med, "s702_gel", e, 64)
            lid = lathe([(0, H_D + 0.0018), (R_D + 0.003, H_D + 0.0018), (R_D + 0.003, H_D - 0.004), (R_D + 0.003 - WL, H_D - 0.004), (R_D + 0.003 - WL, H_D + 0.0018 - WL), (0, H_D + 0.0018 - WL)], glass, "s702_lid", e, 64)
            e.location = (xx, yy, 0.0)
            dishes.append(dict(obj=e, x=xx, y=yy, t=T_IN[k], r=R_D + 0.003))

    def z_of(d, t):
        if d["t"] is None:
            return 0.0
        x = (t - d["t"]) / DUR
        if x <= 0:
            return None
        return DROP_H * (1 - out_cubic(x))

    def check():
        hits, gap, rim = {}, 9.0, 9.0
        for f in range(FRAMES):
            t = f / FPS
            live = [(d, z_of(d, t)) for d in dishes]
            live = [(d, z) for d, z in live if z is not None]
            for a in range(len(live)):
                da, za = live[a]
                for b in range(a + 1, len(live)):
                    db, zb = live[b]
                    g = math.hypot(da["x"] - db["x"], da["y"] - db["y"]) - da["r"] - db["r"]
                    gap = min(gap, g)
                    if g < 0 and abs(za - zb) < H_D + 0.002:
                        hits.setdefault("dish / dish", []).append(round(t, 2))
                ring = np.array([[da["x"] + da["r"] * math.cos(u), da["y"] + da["r"] * math.sin(u), za] for u in np.linspace(0, 2 * math.pi, 48)])
                if in_rim(ring).any():
                    hits.setdefault("dish / cell rim", []).append(round(t, 2))
                rim = min(rim, 0.418 - (abs(da["x"] - x0) + da["r"]), 0.333 - (abs(da["y"] - y0) + da["r"]))
                if za < -1e-6:
                    hits.setdefault("dish / table", []).append(round(t, 2))
        return ("none" if not hits else "; ".join("%s at %s" % (k, v[:4]) for k, v in hits.items())), "dish to dish %.4f, dish to cell rim (inside) %.4f" % (gap, rim)

    def out_cubic(x):
        x = min(1.0, max(0.0, x))
        return 1 - (1 - x) ** 3

    run_check("s702", check)
    v0 = dict(at=(x0, y0 - 0.01, 0.01), az=math.radians(4), el=math.radians(24), d=1.05, mm=50.0)
    v1 = dict(v0, d=0.9, az=math.radians(-2), el=math.radians(27))
    c = sc.camera

    def update(t_abs):
        t = t_abs - START
        f = int(round(t * FPS))
        v = mix_v(v0, v1, smooth(t / (FRAMES / FPS)))
        shoot(c, f, v, v["at"])
        for d in dishes:
            z = z_of(d, t)
            for o in d["obj"].children:
                o.hide_render = z is None
            if z is not None:
                d["obj"].location = (d["x"], d["y"], z)
        sky(0.2)
    return update


def mix_v(p, q, x):
    log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
    return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))


# ================================================================ 7-04 · 两只秒表一起走
def shot_s704(sc, sky):
    C = hk_end(sc, sky)
    in_rim = C["in_rim"]
    x0, y0 = cell_at(41)
    body_m = P.gloss((0.05, 0.05, 0.055), 0.3, 0.6)
    face_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    red = P.gloss(P.RED, 0.3, 0.6)
    steel = P.gloss((0.6, 0.59, 0.57), 0.22, 0.5)
    RB, HB, RF = 0.062, 0.02, 0.052
    T_PRESS, T_GO, TURN = 0.55, 0.68, 3.0          # 按下；针开始走；转一圈的秒数
    watches = []
    deselect()
    for k, xx in enumerate((x0 - 0.15, x0 + 0.15)):
        e = empty("s704_watch")
        e.location = (xx, y0, 0.0)
        lathe([(0, 0), (RB - 0.004, 0), (RB, 0.004), (RB, HB - 0.004), (RB - 0.004, HB), (0, HB)], body_m, "s704_body", e, 96)
        lathe([(0, HB), (RF, HB), (RF, HB + 0.0008), (0, HB + 0.0008)], face_m, "s704_face", e, 96)
        for j in range(12):
            a = 2 * math.pi * j / 12
            tk = B.extrude([box(-0.0012, 0.0012, 0.0, -0.007 if j % 3 else -0.011, 0.0005)], 0.0006, 0.0002, z=0.0, name="s704_tick", mat=ink)
            deselect()
            tk.parent = e
            tk.matrix_parent_inverse = Matrix()
            tk.location = (RF * 0.88 * math.sin(a), RF * 0.88 * math.cos(a), HB + 0.0008)
            tk.rotation_mode = "XYZ"
            tk.rotation_euler = (0, 0, -a)
        hand = empty("s704_hand")
        hand.parent = e
        hand.location = (0, 0, HB + 0.0016)
        hb = B.extrude([box(-0.0013, 0.0013, RF * 0.82, -0.008, 0.0012)], 0.0008, 0.0003, z=0.0, name="s704_handbar", mat=red)
        deselect()
        hb.parent = hand
        hb.matrix_parent_inverse = Matrix()
        hub = lathe([(0, 0), (0.0035, 0), (0.0035, 0.0018), (0, 0.0018)], red, "s704_hub", hand, 24)
        stem = lathe([(0, 0), (0.0045, 0), (0.0045, 0.012), (0, 0.012)], steel, "s704_stem", e, 24)
        stem.rotation_mode = "XYZ"
        stem.rotation_euler = (-math.pi / 2, 0, 0)
        stem.location = (0, RB - 0.001, HB / 2)
        btn = empty("s704_btn")
        btn.parent = e
        lathe([(0, 0.006), (0.005, 0.006), (0.005, 0), (0.0075, 0), (0.0075, 0.007), (0.006, 0.0085), (0, 0.0085)], steel, "s704_cap", btn, 32).rotation_mode = "XYZ"          # 套在表柄上的帽，里面有 6 mm 深的孔
        for o in btn.children:
            o.rotation_euler = (-math.pi / 2, 0, 0)
        watches.append(dict(obj=e, hand=hand, btn=btn, x=xx))

    def btn_y(t):
        x = (t - T_PRESS) / 0.16
        push = math.sin(math.pi * min(1.0, max(0.0, x))) if 0 <= x <= 1 else 0.0
        return RB - 0.001 + 0.012 - 0.001 - 0.0045 * push          # 帽套进表柄 1 mm；按下再进 4.5 mm，孔深 6 mm

    def check():
        hits = {}
        bore = 9.0
        for f in range(FRAMES):
            t = f / FPS
            bore = min(bore, 0.006 - ((RB - 0.001 + 0.012) - btn_y(t)))          # 表柄尖到帽孔底还剩多少
            if bore < 0:
                hits.setdefault("stem / cap", []).append(round(t, 2))
            for w in watches:
                pts = np.array([[w["x"] + RB * math.cos(u), y0 + RB * math.sin(u), 0.0] for u in np.linspace(0, 2 * math.pi, 48)] + [[w["x"], y0 + btn_y(t) + 0.0085, HB / 2]])
                if in_rim(pts).any():
                    hits.setdefault("watch / cell rim", []).append(round(t, 2))
        d = abs(watches[0]["x"] - watches[1]["x"]) - 2 * RB
        return ("none" if not hits else "; ".join("%s at %s" % (k, v[:4]) for k, v in hits.items())), "watch to watch %.4f, hand above face %.4f, stem tip to bottom of cap bore %.4f" % (d, 0.0008, bore)

    run_check("s704", check)
    v0 = dict(at=(x0, y0, 0.012), az=math.radians(2), el=math.radians(42), d=0.78, mm=50.0)
    v1 = dict(v0, d=0.66, az=math.radians(-3))
    c = sc.camera

    def update(t_abs):
        t = t_abs - START
        f = int(round(t * FPS))
        v = mix_v(v0, v1, smooth(t / (FRAMES / FPS)))
        shoot(c, f, v, v["at"])
        ang = -2 * math.pi * max(0.0, t - T_GO) / TURN
        for w in watches:
            w["hand"].rotation_mode = "XYZ"
            w["hand"].rotation_euler = (0, 0, ang)
            w["btn"].location = (0, btn_y(t), HB / 2)
        sky(0.2)
    return update


SHOTS["s702"] = shot_s702
SHOTS["s703"] = shot_s703
SHOTS["s704"] = shot_s704
