"""HKBU SCIE1007 课程作业的科普视频。出镜段"托盘"试片 1 第 2 版：2-08 末尾 → 3-01（D 出镜）→ 3-02 开头。由 bl_inserts.py 的 BL_EXTRA 接口运行（旧文件只读引用；第 1 版 bl_tray.py 保留不动）。

第 2 版按总管意见：托盘是台面的一块（和台面同一种骨白漫反射材质、同一套灯），顶面升起 S3 那种圆角灰色格边，只有当前格描朱红；
机位是台面镜头那种低斜角（俯角 35°）；锁宽占托盘宽 45% 以上；路线六站是玻璃半球，红液从左边流进第一站；
@Okay 第一站红半球亮起升高，To 时其余五站沿台面向后滑远，第一站放大留在中央；this 时格边升起；@picture 红半球压平，当前格的朱红边升起（锁座）；
@lock 锁落进朱红格，@key 钥匙递进来。推近时格边、路线沉回台面，板子变薄并入台面，相机落到 shot k 的机位，接 S3_all_2.mp4。

帧号和第 1 版相同（成片从第 30 帧起剪，见 src/v3/tray/beats2.json）。
运行：BL_EXTRA=bl_tray2.py blender.exe -b -P bl_inserts.py -- tray2 <输出目录> [首帧] [末帧] [采样]
TRAY_TRACK=<json>  每帧屏幕框、锚点、穿模检查，不渲染
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Quaternion, Vector

META = {"tray2": (0.0, 742, 0.2, 0.9)}

BEATS = dict(okay=123, to=173, this=202, picture=268, lock=314, and_=376, key=424, end=439, push=443, push_end=467, vo302=466)
BOX = (900, 220, 1780, 820)
SCALE_208 = 0.46
ST_208 = [228, 512, 790, 1072, 1395, 1705]
KF = lambda f: 287.0 + (f - BEATS["vo302"]) / FPS
EL = math.radians(float(os.environ.get("TRAY_EL", "35")))


def sm(a, b, f):
    return smooth((f - a) / max(b - a, 1e-6))


def tray2_shot(sc, sky):
    c = lens(sc, 2.8)
    c.data.dof.use_dof = False
    sc.render.film_transparent = True
    fl = bpy.data.objects["floor"]
    fl.is_shadow_catcher = True
    things = k_things()
    for n in ("lock_b", "key_b"):
        for p in things[n].children:
            p.hide_render = True
    lock_m, key_m = things["lock_a"], things["key_a"]
    bpy.context.view_layer.update()

    def wbox(objs):
        pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
        return [min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts)]
    rest_l = Vector(k_place(287.0)["lock_a"])
    rest_k = Vector(k_place(287.0)["key_a"]) + Vector((-0.15, 0, 0))     # shot k 的摆位刀尖压进锁壁一点，托盘这边停短 0.15（F3 单位）
    STOP = rest_k + Vector((-0.15, 0, 0))
    lock_m.location = rest_l
    key_m.location = STOP
    bpy.context.view_layer.update()
    LB, KB = wbox(lock_m.children), wbox(key_m.children)
    print("LOCK_BOX", [round(v, 3) for v in LB], "KEY_BOX", [round(v, 3) for v in KB], flush=True)
    LC = Vector(((LB[0] + LB[2]) / 2, (LB[1] + LB[3]) / 2, 0))

    # ---------------------------------------------------------------- 格子和托盘的范围（台面单位）
    M = 0.14
    cell = (LB[0] - M, LB[1] - M, LB[2] + M, LB[3] + M)                # 当前格 = 锁外一圈
    X0, X1 = KB[0] + 0.12, cell[2] + 0.16                               # 钥匙柄比托盘左沿伸出 0.12
    Y0 = cell[1] - 0.45
    TW = X1 - X0
    print("LOCK_SHARE %.3f of tray width %.2f" % ((LB[2] - LB[0]) / TW, TW), flush=True)
    TH = 0.24
    bone = gk._mat("tray_bone")
    d_ = bone[1].nodes.new("ShaderNodeBsdfDiffuse")
    d_.inputs["Color"].default_value = (*P.BONE_LIN, 1)
    bone[1].links.new(d_.outputs[0], bone[2].inputs["Surface"])
    bone = bone[0]
    grey = gk.surface((0.60, 0.585, 0.54), 0.7, 0.1)                   # S3 格子的灰边
    red_rim = gk.surface(P.RED, 0.5, 0.2)

    def rect(l, b_, r, t, rad):
        return B.round_poly([(l, t), (r, t), (r, b_), (l, b_)], rad, 10)

    from bpy_extras.object_utils import world_to_camera_view as w2c
    WIDE = dict(at=(0, 0, 0), az=0.0, el=EL, d=20.0, mm=50.0)
    shx, shy, depth = -0.2, 0.0, 6.0

    def corners(dp):
        return [Vector((x, y, z)) for x in (X0, X1) for y in (Y0, Y0 + dp) for z in (0.0, -TH)]

    def place(v, sx, sy, dp):
        eye = eye_of(v)
        c.location = eye
        c.rotation_quaternion = (Vector(v["at"]) - Vector(eye)).to_track_quat("-Z", "Y")
        c.data.lens = v["mm"]
        c.data.shift_x, c.data.shift_y = sx, sy
        bpy.context.view_layer.update()
        p = [w2c(sc, c, q) for q in corners(dp)]
        return [min(q.x for q in p) * 1920, (1 - max(q.y for q in p)) * 1080, max(q.x for q in p) * 1920, (1 - min(q.y for q in p)) * 1080]
    for it in range(60):
        WIDE["at"] = ((X0 + X1) / 2, Y0 + depth / 2, 0.0)
        b = place(WIDE, shx, shy, depth)
        WIDE["d"] *= (b[2] - b[0]) / (BOX[2] - BOX[0])
        shx -= ((BOX[0] + BOX[2]) / 2 - (b[0] + b[2]) / 2) / 1920
        shy -= (b[3] - BOX[3]) / 1920                                     # 前沿落在 820
        depth *= 1 + 0.5 * (b[1] - BOX[1]) / (b[3] - b[1])                 # 后沿到 220
        depth = min(max(depth, 3.0), 30.0)
    b = place(WIDE, shx, shy, depth)
    print("TRAY_FIT d %.2f shift %.3f %.3f depth %.2f box %s" % (WIDE["d"], shx, shy, depth, [round(x) for x in b]), flush=True)
    Y1 = Y0 + depth
    TC = Vector(((X0 + X1) / 2, (Y0 + Y1) / 2, 0))

    slab_e = empty("tray")
    slab_e.location = TC
    slab = B.extrude([rect(-TW / 2, -depth / 2, TW / 2, depth / 2, 0.2)], TH, 0.03, z=-TH, name="tray_slab", mat=bone)
    slab.parent = slab_e

    # 格边：当前格一圈（灰，picture 时上面再升起一圈朱红）；网格线延伸到托盘边（格子被托盘边截断，说明台面还在延续）
    cw, ch = cell[2] - cell[0], cell[3] - cell[1]
    R_W, R_H = 0.045, 0.035
    grid_e = empty("grid")
    rims = []

    def strip(x0, y0, x1, y1, mat, name):
        o = B.extrude([rect(x0, y0, x1, y1, min(R_W / 2 - 1e-3, 0.02))], R_H, 0.008, z=0.0, name=name, mat=mat)
        o.parent = grid_e
        rims.append(o)
        return o
    xs = [cell[0] - cw * k for k in range(0, 4)] + [cell[2]]
    ys = [cell[1] + ch * k for k in range(0, 12)]
    xs = [x for x in xs if X0 + 0.15 < x < X1 - 0.05]
    ys = [y for y in ys if Y0 + 0.1 < y < Y1 - 0.15]
    for x in xs:
        strip(x - R_W / 2, Y0 + 0.12, x + R_W / 2, Y1 - 0.12, grey, "rim_v")
    for y in ys:
        strip(X0 + 0.12, y - R_W / 2, X1 - 0.12, y + R_W / 2, grey, "rim_h")
    red_e = empty("redcell")
    red_e.location = (0, 0, 0)
    ro = B.extrude([rect(cell[0] - R_W * 0.7, cell[1] - R_W * 0.7, cell[2] + R_W * 0.7, cell[3] + R_W * 0.7, 0.09), rect(cell[0] + R_W * 0.7, cell[1] + R_W * 0.7, cell[2] - R_W * 0.7, cell[3] - R_W * 0.7, 0.07)[::-1]], R_H * 1.4, 0.01, z=0.0, name="red_cell", mat=red_rim)
    ro.parent = red_e

    def ray(px, py):
        mw = c.matrix_world
        fx = (px - 960) / 1920 * 36 + shx * 36
        fy = (540 - py) / 1920 * 36 + shy * 36
        d = (mw.to_3x3() @ Vector((fx, fy, -c.data.lens))).normalized()
        o = mw.translation
        return o + d * (-o.z / d.z)

    # ---------------------------------------------------------------- 路线：玻璃半球六站（2-08 末帧缩 0.46 倍后的位置），红液从左边流进第一站
    glass, ink = B.clear_glass(), gk.surface((0.012, 0.012, 0.014), 0.3)
    red = P.gloss(P.RED, 0.18, 0.7)
    glow_m, glow_n, glow_o = gk._mat("tgt_glow")
    gb = glow_n.nodes.new("ShaderNodeBsdfPrincipled")
    gb.inputs["Base Color"].default_value = gb.inputs["Emission Color"].default_value = (*P.RED, 1)
    gb.inputs["Roughness"].default_value = 0.16
    gb.inputs["Coat Weight"].default_value = 0.7
    glow_n.links.new(gb.outputs[0], glow_o.inputs["Surface"])
    glow = gb.inputs["Emission Strength"]
    sx_ = lambda x: 1340 + (x - 960) * SCALE_208
    sy_ = 520 + (515 - 540) * SCALE_208
    pts = [ray(sx_(x), sy_) for x in ST_208]
    R = (ray(sx_(ST_208[2]) + 64 * SCALE_208, sy_) - pts[2]).length

    def dome(r, mat, name, parent, at):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0), segments=96, ring_count=48)
        o = bpy.context.object
        o.name = name
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-5], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        o.data.materials.append(mat)
        B.smooth(o)
        o.parent = parent
        o.location = at
        return o

    def torus(r, a, name, mat, parent, at):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=a, location=(0, 0, 0), major_segments=128, minor_segments=20)
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        B.smooth(o)
        o.parent = parent
        o.location = at
        return o

    mid = sum(pts[1:], Vector()) / 5
    route = empty("route")
    route.location = mid
    for i, p in enumerate(pts[1:], 1):
        at = (p.x - mid.x, p.y - mid.y, 0.0)
        g = dome(R, glass, "st_glass%d" % i, route, at)
        g.visible_shadow = False
        torus(R + 0.006, R * 0.09, "st_ink%d" % i, ink, route, (at[0], at[1], R * 0.09))
    reds = []
    for i in (1, 2):
        p = pts[i]
        reds.append(torus(R * 1.3, R * 0.07, "st_red%d" % i, red, route, (p.x - mid.x, p.y - mid.y, R * 0.07)))
    bpy.ops.mesh.primitive_cylinder_add(radius=R * 0.1, depth=(pts[5] - pts[1]).length, vertices=32, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    tb = bpy.context.object
    tb.data.materials.append(glass)
    tb.visible_shadow = False
    tb.parent = route
    tb.location = ((pts[1].x + pts[5].x) / 2 - mid.x, 0, R * 0.12)

    tgt = empty("target")
    tgt.location = pts[0]
    tgt_body = empty("tgt_body")
    tgt_body.parent = tgt
    g = dome(R, glass, "tgt_glass", tgt_body, (0, 0, 0))
    g.visible_shadow = False
    fl_ = dome(R * 0.9, glow_m, "tgt_fluid", tgt_body, (0, 0, 0.002))
    fl_.scale = (1, 1, 0.62)                           # 红液只到玻璃半球六成高：读作装着红液的玻璃站，不是一个红按钮
    torus(R + 0.004, R * 0.05, "tgt_ink", ink, tgt_body, (0, 0, R * 0.05))
    # 红液管：从托盘左沿流进第一站
    feed_e = empty("feed")
    feed_e.location = (X0 + 0.1, pts[0].y, 0)
    L_FEED = pts[0].x - R * 0.8 - (X0 + 0.1)
    bpy.ops.mesh.primitive_cylinder_add(radius=R * 0.14, depth=1.0, vertices=32, location=(0.5, 0, 0), rotation=(0, math.pi / 2, 0))
    fd = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    fd.data.materials.append(B.fluid(P.RED, (0.9, 0.05, 0.03)))
    B.smooth(fd)
    fd.parent = feed_e
    fd.location = (0, 0, R * 0.16)

    T_BIG = (0.46 * TW) / (2 * R)                    # 第一站放大到托盘宽的 46%
    LCF = Vector((-2.42, -0.02, 0.0))

    W0 = dict(WIDE)

    def view(f):
        if f < BEATS["push"]:
            return W0, (shx, shy)
        kv = k_view(KF(max(f, BEATS["vo302"])))
        x = sm(BEATS["push"], BEATS["push_end"], f)
        if x >= 1:
            return kv, (0.0, 0.0)
        return fall(W0, kv, x), (shx * (1 - x), shy * (1 - x))

    def state(f):
        s = {}
        s["feed"] = max(1e-3, sm(86, 112, f) * (1 - sm(BEATS["to"] - 22, BEATS["to"] - 6, f)))
        up = 0.45 * (sm(BEATS["okay"] - 6, BEATS["okay"], f) - sm(BEATS["this"] - 6, BEATS["this"], f))
        mv = sm(BEATS["to"] - 22, BEATS["to"], f)
        p0 = pts[0].lerp(LC, mv)
        k = 1 + 0.45 * sm(BEATS["okay"] - 6, BEATS["okay"], f)
        k = k + (T_BIG - k) * mv
        press = sm(BEATS["picture"] - 16, BEATS["picture"], f)
        s["tgt"] = (Vector((p0.x, p0.y, up)), k, max(1e-3, 1 - press))
        s["glow"] = 4.0 * math.exp(-max(0, f - BEATS["okay"]) / 12) * (f >= BEATS["okay"] - 6) + 1.5 * press * (1 - sm(BEATS["picture"], BEATS["picture"] + 10, f))
        s["reds"] = max(1e-3, 1 - sm(110, 130, f))
        back = Vector((mid.x, Y1 - 0.9, 0.0))
        s["route"] = (mid.lerp(back, mv), 1 - 0.3 * mv)
        s["grid"] = sm(BEATS["this"] + 18, BEATS["this"] + 40, f)          # 格边从台面升起 220–242
        s["redcell"] = sm(BEATS["picture"] - 12, BEATS["picture"], f)
        L = BEATS["lock"]
        if f < L - 16:
            lz, vis = 9.0, False
        elif f < L:
            x = (f - L + 16) / 16
            lz, vis = 9.0 * (1 - x * x), True
        else:
            d = (f - L) / FPS
            lz, vis = 0.09 * abs(math.sin(math.pi * d / 0.13)) * math.exp(-d / 0.07), True
        rot = math.radians(25) * (sm(L + 18, L + 48, f) - sm(BEATS["and_"] - 12, BEATS["and_"], f))
        s["lock"] = (Vector((rest_l.x, rest_l.y, rest_l.z + lz / K_S)), rot, vis, lz)
        Kk = BEATS["key"]
        start = STOP + Vector((1.8, 0.9, 11.0 / K_S))
        touch = STOP + Vector((-0.2, 0.0, 0.0))
        if f < Kk - 18:
            kp, kvis = start, False
        elif f < Kk - 6:
            x = (f - Kk + 18) / 12
            kp, kvis = Vector((start.x + (touch.x - start.x) * x * x, start.y + (touch.y - start.y) * x * x, start.z * (1 - x * x))), True
        elif f < BEATS["push"]:
            kp, kvis = touch.lerp(STOP, sm(Kk - 6, Kk, f)), True
        else:
            kp, kvis = STOP.lerp(rest_k, sm(BEATS["push"], 520, f)), True
        s["key"] = (kp, kvis)
        x = sm(BEATS["push"] + 4, BEATS["push_end"], f)
        s["thin"] = max(1e-3, 1 - x)
        s["sink"] = sm(BEATS["push"], BEATS["push"] + 18, f)
        s["sky"] = 1.0 if f < BEATS["push_end"] else (1 - smooth((KF(f) - K_FALL[0]) / K_FALL[1]))
        return s

    obs = [tgt, tgt_body, route, lock_m, key_m, slab_e, fl, grid_e, red_e, feed_e] + reds

    def apply(f):
        s = state(f)
        v, (a, b_) = view(f)
        shoot(c, f, v, v["at"])
        c.data.shift_x, c.data.shift_y = a, b_
        c.data.keyframe_insert("shift_x", frame=f)
        c.data.keyframe_insert("shift_y", frame=f)
        p, k, flat = s["tgt"]
        tgt.location = p
        tgt_body.scale = (k * (1 + 0.15 * (1 - flat)), k * (1 + 0.15 * (1 - flat)), k * flat)
        route.location = s["route"][0] - Vector((0, 0, 0.6 * s["sink"]))
        route.scale = (s["route"][1],) * 3
        for o in reds:
            o.scale = (s["reds"],) * 3
        feed_e.scale = (L_FEED * s["feed"], 1, 1)
        grid_e.location.z = -R_H * 1.2 * (1 - s["grid"]) - 0.06 * s["sink"]
        red_e.location.z = -R_H * 1.6 * (1 - s["redcell"]) - 0.08 * s["sink"]
        lp, rot, vis, _ = s["lock"]
        q = Quaternion((0, 0, 1), rot)
        lock_m.rotation_quaternion = q
        lock_m.location = lp + LCF - q @ LCF
        key_m.location = s["key"][0]
        slab_e.scale = (1, 1, s["thin"])
        fl.location.z = -TH * s["thin"]
        glow.default_value = s["glow"]
        glow.keyframe_insert("default_value", frame=f)
        for o in obs:
            for path in ("location", "rotation_quaternion", "scale"):
                if path != "rotation_quaternion" or o.rotation_mode == "QUATERNION":
                    o.keyframe_insert(path, frame=f)

    for f in range(FRAMES + 1):
        apply(f)

    def update(t):
        f = int(round(t * FPS))
        s = state(f)
        for p in lock_m.children:
            p.hide_render = not s["lock"][2]
            p.visible_shadow = s["lock"][3] < 2.0
        for p in key_m.children:
            p.hide_render = not s["key"][1]
        fl.is_shadow_catcher = f < BEATS["push_end"]
        gone = f >= BEATS["push_end"]
        slab.hide_render = gone
        for o in rims + [ro, fd] + route.children_recursive:
            o.hide_render = gone
        fd.hide_render = gone or s["feed"] < 0.01
        for o in tgt_body.children:
            o.hide_render = gone or s["tgt"][2] < 0.03
        sky(s["sky"])

    if os.environ.get("TRAY_TRACK"):
        run_track2(sc, c, update, os.environ["TRAY_TRACK"], dict(lock=list(lock_m.children), key=list(key_m.children),
                   target=list(tgt_body.children), route=[o for o in route.children_recursive if o.type == "MESH"], rims=rims + [ro]),
                   (X0, Y0, X1, Y1), tgt)
    return update


def run_track2(sc, c, update, path, groups, tray, tgt):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils.bvhtree import BVHTree

    def wb(o, dg):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()
        return t
    out = []
    for f in range(FRAMES + 1):
        sc.frame_set(f)
        update(f / FPS)
        dg = bpy.context.evaluated_depsgraph_get()
        row = dict(f=f)
        bv = {}
        for name, objs in groups.items():
            xs, ys = [], []
            vis = [o for o in objs if not o.hide_render]
            for o in vis:
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                vv = list(me.vertices)
                for v in vv[::max(1, len(vv) // 300)]:
                    q = w2c(sc, c, o.matrix_world @ v.co)
                    if q.z > 0:
                        xs.append(q.x * 1920)
                        ys.append((1 - q.y) * 1080)
                ev.to_mesh_clear()
            if xs:
                row[name] = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
            if vis and name != "route":
                bv[name] = [wb(o, dg) for o in vis]
        for a_, b_ in (("lock", "key"), ("lock", "rims"), ("key", "rims"), ("lock", "target"), ("key", "target")):
            if bv.get(a_) and bv.get(b_):
                n_ = sum(len(a.overlap(b)) for a in bv[a_] for b in bv[b_])
                if n_:
                    row["clash_%s_%s" % (a_, b_)] = n_
        q = w2c(sc, c, tgt.matrix_world.translation)
        row["target_c"] = [round(q.x * 1920), round((1 - q.y) * 1080)]
        out.append(row)
    json.dump(out, open(path, "w"), indent=0)
    print("TRAY_TRACK_OK", path, flush=True)
    import sys
    sys.exit(0)


SHOTS["tray2"] = tray2_shot
