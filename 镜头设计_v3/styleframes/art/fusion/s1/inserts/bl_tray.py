"""HKBU SCIE1007 课程作业的科普视频。出镜段"托盘"试片 1：2-08 末尾 → 3-01（D 出镜）→ 3-02 开头。由 bl_inserts.py 的 BL_EXTRA 接口运行（旧文件只读引用）。

托盘是台面上的一格：一块有厚度的骨白板，顶面一圈朱红边，放在透明底上（地面是 shadow catcher，只留接触阴影），Remotion 再把它叠到细胞纸底上、人旁边。
锁和钥匙就是 shot k（3-02 的锁和钥匙）的同一套模型、材质和摆位：k_things() 的 lock_a、key_a，台面坐标也一样。
所以推近时相机直接从托盘机位落到 shot k 的机位（k_view），推近完成后托盘的板子和地面合成一张台面，画面接上 S3_all_2.mp4。

帧号 = 试片成片帧号（60 fps）。时间表见 BEATS（由 src/v3/tray/beats.json 同一份数）：
  3-01 片头在第 92 帧；Okay 123、To 173、this 202、picture 268、lock 314、and 376、key 424、句尾 439；推近 443–467；
  3-02 录音从第 466 帧开始，shot k 的时间 k = 287.0 + (f - 466) / 60；第 562 帧（k 288.6，S3_all_2 文件内 5.6 秒，相纸已滑出画面）交给 S3。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_tray.py blender.exe -b -P bl_inserts.py -- tray <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
TRAY_TRACK=<json>  每帧物体在屏幕上的框和锚点、穿模检查，不渲染
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

META = {"tray": (0.0, 742, 0.2, 0.9)}

T301 = 92                                   # 3-01 片头
BEATS = dict(okay=123, to=173, this=202, picture=268, lock=314, and_=376, key=424, end=439, push=443, push_end=467, vo302=466, hand=562)
TW, TD, TH = 7.4, 5.8, 0.28                 # 托盘宽、深、厚（台面单位）
LOCK_C = Vector(on_k(-2.42, -0.02))         # lock_a 的中心（shot k 的摆位）
TC = Vector((LOCK_C.x - 1.05, LOCK_C.y - 0.05, 0.0))   # 托盘中心：锁偏右，钥匙从左边进来
BOX = (900, 220, 1780, 820)                 # 托盘占位框（1920×1080）
SCALE_208 = 0.46                            # 2-08 画面拉远时缩到的倍数，缩放中心 = 托盘中心 (1340, 520)
ST_208 = [228, 512, 790, 1072, 1395, 1705]  # 2-08 末帧六站的 x，y = 515，玻璃泡半径约 64 px
KF = lambda f: 287.0 + (f - BEATS["vo302"]) / FPS       # shot k 的时间


def sm(a, b, f):
    return smooth((f - a) / max(b - a, 1e-6))


def tray_shot(sc, sky):
    c = lens(sc, 2.8)
    c.data.dof.use_dof = False
    sc.render.film_transparent = True
    fl = bpy.data.objects["floor"]
    things = k_things()
    for n in ("lock_b", "key_b"):
        for p in things[n].children:
            p.hide_render = True
    lock_m, key_m = things["lock_a"], things["key_a"]
    root = lock_m.parent

    # ---------------------------------------------------------------- 托盘：骨白板 + 朱红边（和台面镜头同一种骨白、同一种朱红）
    bone = gk._mat("tray_bone")
    d_ = bone[1].nodes.new("ShaderNodeBsdfDiffuse")
    d_.inputs["Color"].default_value = (*P.BONE_LIN, 1)
    bone[1].links.new(d_.outputs[0], bone[2].inputs["Surface"])
    bone = bone[0]
    red = P.gloss(P.RED, 0.18, 0.7)
    rr = lambda w, h, r: B.round_poly([(-w, h), (w, h), (w, -h), (-w, -h)], r, 10)
    slab_e = empty("tray")
    slab_e.location = (TC.x, TC.y, 0.0)                 # 原点在顶面；缩 z 时顶面不动，板子往下变薄
    slab = B.extrude([rr(TW / 2, TD / 2, 0.22)], TH, 0.03, z=-TH, name="tray_slab", mat=bone)
    slab.parent = slab_e
    BW = 0.075
    rim = B.extrude([rr(TW / 2 - 0.12, TD / 2 - 0.12, 0.16), rr(TW / 2 - 0.12 - BW, TD / 2 - 0.12 - BW, 0.13)[::-1]], 0.012, 0.004, z=-0.004, name="tray_rim", mat=red)
    rim_e = empty("tray_rim_e")
    rim_e.location = (TC.x, TC.y, 0.0)
    rim.parent = rim_e
    fl.is_shadow_catcher = True

    # ---------------------------------------------------------------- 相机：托盘机位（俯角 48°，50 mm，镜头平移把托盘放进占位框）
    from bpy_extras.object_utils import world_to_camera_view as w2c
    corners = [Vector((TC.x + sx * TW / 2, TC.y + sy * TD / 2, z)) for sx in (-1, 1) for sy in (-1, 1) for z in (0.0, -TH)]

    def place(v, shx, shy):
        eye = eye_of(v)
        c.location = eye
        c.rotation_quaternion = (Vector(v["at"]) - Vector(eye)).to_track_quat("-Z", "Y")
        c.data.lens = v["mm"]
        c.data.shift_x, c.data.shift_y = shx, shy
        bpy.context.view_layer.update()
        p = [w2c(sc, c, q) for q in corners]
        return [min(q.x for q in p) * 1920, (1 - max(q.y for q in p)) * 1080, max(q.x for q in p) * 1920, (1 - min(q.y for q in p)) * 1080]
    WIDE = dict(at=(TC.x, TC.y, 0.0), az=0.0, el=math.radians(48), d=20.0, mm=50.0)
    shx, shy = -0.198, 0.0
    for it in range(30):
        b = place(WIDE, shx, shy)
        if it < 3:
            print("FIT", it, WIDE["d"], shx, shy, b, flush=True)
        WIDE["d"] *= (b[2] - b[0]) / (BOX[2] - BOX[0])
        shx -= ((BOX[0] + BOX[2]) / 2 - (b[0] + b[2]) / 2) / 1920
        shy -= ((b[1] + b[3]) / 2 - 520) / 1920
    b = place(WIDE, shx, shy)
    print("TRAY_FIT d %.2f shift %.3f %.3f box %s" % (WIDE["d"], shx, shy, [round(x) for x in b]), flush=True)

    def ray(px, py):
        """屏幕点 → 托盘顶面（z=0）上的台面坐标（当前是托盘机位）。"""
        mw = c.matrix_world
        fx = (px - 960) / 1920 * 36 + shx * 36
        fy = (540 - py) / 1920 * 36 + shy * 36
        d = (mw.to_3x3() @ Vector((fx, fy, -c.data.lens))).normalized()
        o = mw.translation
        return o + d * (-o.z / d.z)

    # ---------------------------------------------------------------- 路线：2-08 末帧六站缩 0.46 倍后的屏幕位置，打到托盘顶面上
    glass, fluid = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03))
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    glow_m, glow_n, glow_o = gk._mat("tgt_glow")
    gb = glow_n.nodes.new("ShaderNodeBsdfPrincipled")
    gb.inputs["Base Color"].default_value = gb.inputs["Emission Color"].default_value = (*P.RED, 1)
    gb.inputs["Roughness"].default_value = 0.2
    gb.inputs["Coat Weight"].default_value = 0.7
    glow_n.links.new(gb.outputs[0], glow_o.inputs["Surface"])
    glow = gb.inputs["Emission Strength"]
    sx_ = lambda x: 1340 + (x - 960) * SCALE_208
    sy_ = 520 + (515 - 540) * SCALE_208
    pts = [ray(sx_(x), sy_) for x in ST_208]
    r_px = 64 * SCALE_208
    R = (ray(sx_(ST_208[2]) + r_px, sy_) - pts[2]).length                 # 玻璃泡半径（台面单位）
    route = empty("route")
    mid = sum(pts[1:], Vector()) / 5
    route.location = mid

    def torus(r, a, name, mat, parent, at):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=a, location=(0, 0, 0), major_segments=128, minor_segments=20)
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        B.smooth(o)
        o.parent = parent
        o.location = at
        return o

    def sphere(r, name, mat, parent, at, zs=0.85):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0), segments=64, ring_count=32)
        o = bpy.context.object
        o.name = name
        o.scale = (1, 1, zs)
        o.data.materials.append(mat)
        B.smooth(o)
        o.parent = parent
        o.location = at
        return o

    zc = R * 0.85
    for i, p in enumerate(pts[1:], 1):
        at = (p.x - mid.x, p.y - mid.y, zc)
        g = sphere(R, "st_glass%d" % i, glass, route, at)
        g.visible_shadow = False
        torus(R + 0.004, R * 0.08, "st_ink%d" % i, ink, route, at)
        if i <= 2:
            torus(R * 1.33, R * 0.07, "st_red%d" % i, red, route, (at[0], at[1], 0.02))
    # 六站之间的玻璃管（从第 1 站一直到第 6 站；第 1 站离开以后，左端留一个空位）
    bpy.ops.mesh.primitive_cylinder_add(radius=R * 0.12, depth=(pts[5] - pts[0]).length, vertices=32, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    tb = bpy.context.object
    tb.data.materials.append(glass)
    tb.visible_shadow = False
    tb.parent = route
    tb.location = ((pts[0].x + pts[5].x) / 2 - mid.x, 0, zc)
    reds = [o for o in route.children if o.name.startswith("st_red")]

    tgt = empty("target")                               # 第 1 站 Target：红液玻璃泡 + 黑环 + 朱红外环
    tgt.location = pts[0]
    tgt_bulb = empty("tgt_bulb")
    tgt_bulb.parent = tgt
    g = sphere(R, "tgt_glass", glass, tgt_bulb, (0, 0, zc))
    g.visible_shadow = False
    sphere(R * 0.93, "tgt_fluid", glow_m, tgt_bulb, (0, 0, zc), 0.85)
    torus(R + 0.004, R * 0.08, "tgt_ink", ink, tgt_bulb, (0, 0, zc))
    ring_e = empty("tgt_ring")
    ring_e.parent = tgt
    torus(R * 1.33, R * 0.07, "tgt_red", glow_m, ring_e, (0, 0, 0.0))
    ring_e.location = (0, 0, 0.02)

    # ---------------------------------------------------------------- 钥匙、锁：shot k 的位置（F3 单位，root 下）
    rest_k = Vector(k_place(287.0)["key_a"]) + Vector((-float(os.environ.get("TRAY_KEY_SHORT", "0.15")), 0, 0))   # shot k 的摆位刀尖压进锁壁一点（k 自己就这样），托盘这边停短 0.15 不穿
    rest_l = Vector(k_place(287.0)["lock_a"])
    LCF = Vector((-2.42, -0.02, 0.0))                   # 锁的转轴（F3 单位）
    lock_r = 1.62 * K_S                                 # 锁的半径（台面单位）
    seat_s = (lock_r + 0.45) / (R * 1.33)               # 朱红外环放大到锁外面一圈

    # 钥匙从上方偏左递进来：起点在画面上沿以外
    STOP = rest_k + Vector((-0.6, 0.0, 0.0))

    # ---------------------------------------------------------------- 每帧的状态
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
        # 第 1 站：Okay 亮一下、升起；To 时移到锁的位置；this 落回；picture 压平，外环展开成锁座
        up = 0.30 * (sm(BEATS["okay"] - 6, BEATS["okay"], f) - sm(BEATS["this"] - 6, BEATS["this"], f))
        mv = sm(BEATS["to"] - 22, BEATS["to"], f)
        p0 = pts[0].lerp(Vector((LOCK_C.x, LOCK_C.y, 0.0)), mv)
        s["tgt"] = (Vector((p0.x, p0.y, up)), 1.0)
        press = sm(BEATS["picture"] - 16, BEATS["picture"], f)
        s["bulb_scale"] = (max(1e-3, 1 - press), max(1e-3, 1 - press))
        s["ring_scale"] = 1 + (seat_s - 1) * press
        s["ring_z"] = 1 - 0.6 * press
        s["glow"] = 3.0 * math.exp(-max(0, f - BEATS["okay"]) / 10) * (f >= BEATS["okay"] - 6) + 0.0
        # 拉远接上时第 2、3 站的朱红外环收掉（回到第 1 站）
        s["reds"] = 1 - sm(110, 130, f)
        # To：其余五站退到托盘后沿、缩到 40%
        back = Vector((TC.x + 0.9, TC.y + TD / 2 - 0.55, 0.0))
        s["route"] = (mid.lerp(back, mv), 1 - 0.6 * mv)
        # 锁：从画面上方落下，lock 落地，回弹 8 帧；转 25° 露锁槽再转回
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
        s["lock"] = (Vector((rest_l.x, rest_l.y, rest_l.z + lz / K_S)), rot, vis)
        # 钥匙：406 起从上方偏左递进来，418 碰到托盘，滑到 424 停在锁槽前；推近时继续往锁走，520 到 shot k 的位置
        Kk = BEATS["key"]
        start = STOP + Vector((0.35, 0.9, 11.0 / K_S))
        if f < Kk - 18:
            kp, kvis = start, False
        elif f < Kk - 6:
            x = (f - Kk + 18) / 12
            touch = STOP + Vector((-0.45, 0.0, 0.0))
            kp, kvis = Vector((start.x + (touch.x - start.x) * smooth(x), start.y + (touch.y - start.y) * smooth(x), start.z * (1 - x * x))), True
        elif f < BEATS["push"]:
            x = sm(Kk - 6, Kk, f)
            kp, kvis = (STOP + Vector((-0.45, 0, 0))).lerp(STOP, x), True
        else:
            kp, kvis = STOP.lerp(rest_k, sm(BEATS["push"], 520, f)), True
        s["key"] = (kp, kvis)
        # 推近：托盘板变薄、朱红边沉下、地面升到顶面；路线残留和锁座收掉
        x = sm(BEATS["push"] + 4, BEATS["push_end"], f)
        s["thin"] = max(1e-3, 1 - x)
        s["fade"] = max(1e-3, 1 - sm(BEATS["push"], BEATS["push"] + 18, f))
        s["sky"] = 1.0 if f < BEATS["push_end"] else (1 - smooth((KF(f) - K_FALL[0]) / K_FALL[1]))
        return s

    obs = [tgt, tgt_bulb, ring_e, route, lock_m, key_m, slab_e, rim_e, fl] + reds

    def apply(f):
        s = state(f)
        v, (a, b_) = view(f)
        shoot(c, f, v, v["at"])
        c.data.shift_x, c.data.shift_y = a, b_
        c.data.keyframe_insert("shift_x", frame=f)
        c.data.keyframe_insert("shift_y", frame=f)
        p, _ = s["tgt"]
        tgt.location = p
        tgt_bulb.scale = (s["bulb_scale"][0],) * 3
        k = s["ring_scale"]
        ring_e.scale = (k, k, s["ring_z"])
        ring_e.location.z = 0.02 - 0.08 * (1 - s["fade"])          # 推近时锁座沉进托盘面（不缩，缩会扫过锁脚）
        route.location = s["route"][0]
        route.scale = (s["route"][1] * s["fade"],) * 3
        for o in reds:
            o.scale = (max(1e-3, s["reds"]),) * 3
        lp, rot, vis = s["lock"]
        q = Quaternion((0, 0, 1), rot)
        lock_m.rotation_quaternion = q
        lock_m.location = lp + LCF - q @ LCF
        key_m.location = s["key"][0]
        slab_e.scale = (1, 1, s["thin"])
        rim_e.location.z = -0.03 * (1 - s["thin"])
        fl.location.z = -TH * s["thin"]
        glow.default_value = s["glow"]
        glow.keyframe_insert("default_value", frame=f)
        for o in obs:
            for path in ("location", "rotation_quaternion", "scale"):
                if path != "rotation_quaternion" or o.rotation_mode == "QUATERNION":
                    o.keyframe_insert(path, frame=f)
        return s

    for f in range(FRAMES + 1):
        apply(f)
    track = os.environ.get("TRAY_TRACK")

    def update(t):
        f = int(round(t * FPS))
        s = state(f)
        for p in lock_m.children:
            p.hide_render = not s["lock"][2]
            p.visible_shadow = s["lock"][0].z - rest_l.z < 2.0 / K_S          # 锁还在画面外高处时不投影（否则托盘外先出现一块孤立的灰影）
        for p in key_m.children:
            p.hide_render = not s["key"][1]
        fl.is_shadow_catcher = f < BEATS["push_end"]
        for o in (slab, rim):
            o.hide_render = f >= BEATS["push_end"]
        for o in route.children_recursive + tgt.children_recursive:
            o.hide_render = f >= BEATS["push_end"] or (o.name.startswith("tgt_") and o.parent is tgt_bulb and s["bulb_scale"][0] < 0.01)
        sky(s["sky"])

    if track:
        run_track(sc, c, update, track, lock_m, key_m, tgt, route, ring_e, slab, rim)
    return update


def world_bvh(o, dg):
    from mathutils.bvhtree import BVHTree
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = o.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    return t


def run_track(sc, c, update, path, lock_m, key_m, tgt, route, ring_e, slab, rim):
    """每帧：各物体在屏幕上的框、锚点；钥匙和锁、钥匙和托盘、锁和托盘有没有穿插。"""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils.bvhtree import BVHTree
    groups = dict(lock=lock_m.children, key=key_m.children, target=[o for o in tgt.children_recursive if o.type == "MESH"],
                  route=[o for o in route.children_recursive if o.type == "MESH"])
    out = []
    for f in range(FRAMES + 1):
        sc.frame_set(f)
        update(f / FPS)
        dg = bpy.context.evaluated_depsgraph_get()
        row = dict(f=f)
        bvh = {}
        for name, objs in groups.items():
            xs, ys, zmin = [], [], 1e9
            vis = [o for o in objs if not o.hide_render]
            for o in vis:
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                mw = o.matrix_world
                vv = list(me.vertices)
                co = [mw @ v.co for v in vv[::max(1, len(vv) // 400)]]
                for p in co:
                    q = w2c(sc, c, p)
                    if q.z > 0:
                        xs.append(q.x * 1920)
                        ys.append((1 - q.y) * 1080)
                    zmin = min(zmin, p.z)
                ev.to_mesh_clear()
            if xs:
                row[name] = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)), round(zmin, 3)]
            if name in ("lock", "key", "target") and vis:
                bvh[name] = [world_bvh(o, dg) for o in vis if o.name in ("tgt_red",) or name != "target"]
        for a_, b_ in (("lock", "key"), ("lock", "target"), ("key", "target")):
            if bvh.get(a_) and bvh.get(b_):
                n_ = sum(len(a.overlap(b)) for a in bvh[a_] for b in bvh[b_])
                if n_:
                    row["clash_%s_%s" % (a_, b_)] = n_
        for nm, o in (("lock_c", lock_m.children[0]),):
            q = w2c(sc, c, o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8))
            row[nm] = [round(q.x * 1920), round((1 - q.y) * 1080)]
        q = w2c(sc, c, tgt.matrix_world.translation)
        row["target_c"] = [round(q.x * 1920), round((1 - q.y) * 1080)]
        out.append(row)
    json.dump(out, open(path, "w"), indent=0)
    print("TRAY_TRACK_OK", path, flush=True)
    import sys
    sys.exit(0)


SHOTS["tray"] = tray_shot
