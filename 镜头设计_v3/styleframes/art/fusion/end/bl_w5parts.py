"""HKBU SCIE1007 课程作业的科普视频：片尾卡 W5 的新背景——零件库零件在空中零重力漂浮、互相碰撞（Blender 刚体，Cycles，显卡）。

只做背景层：零件在一个看不见的盒子里漂，景深虚掉，透明底（RGBA）。字层和合成在 comp_w5parts.py。
零件全部来自 inserts/kit_parts_hd.py（精模版），亮面塑料材质照零件库；碰撞形状用凸包，先烘焙到关键帧再渲。

    blender -b --factory-startup -P bl_w5parts.py -- build OUT.blend [采样]     搭场景、逐帧算刚体、卡拍子、自检、烘成关键帧、存盘
    blender -b --factory-startup -P bl_w5parts.py -- still IN.blend OUT.png 第几帧(film) [采样] [百分比]
    blender -b --factory-startup -P bl_w5parts.py -- frames IN.blend OUTDIR 起 止 [步长] [采样]    渲 30 fps 的第 起..止 帧（film 序号），已有的跳过

时间：film 秒 t 对应模拟帧 WARM+1+round(t*60)；先空跑 WARM 帧（4 秒）让零件散开、在动，镜头从第 WARM+1 帧开始。
拍子：W5 用的歌是 Wake Me Up (feat. Justice) 4:16.9–4:49.7，约 111 BPM（research/music_curation.md）。这首还没下载，
拍点没测过，所以这里把 111 BPM 当网格、截取处的第一拍当小节头（BPM、第一拍时间放在下面两个常量，拿到歌后只改这两个数重跑）。
每小节第 1 拍"重撞"两对，第 3 拍"轻撞"一对；撞击发生在拍子上，之前 1 到 1.6 秒两个零件被轻轻推向对方（动力学转接，速度 0.35–1.1 米/秒）。
"""
import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "inserts"))
import kit_parts_hd as KP  # noqa: E402

FPS = 60
WARM = 240                      # 空跑帧数（镜头之前）
NF = 1980                       # 33 秒 × 60
NSIM = WARM + NF
BPM = 111.0                     # 拿到 Wake Me Up 的拍点后改这两个
BEAT0 = 0.0                     # 截取片段里第一个小节头的时间（秒）
SC = 24.0                       # 零件库是毫米，放大 24 倍（50 mm → 1.2 m），刚体才稳
LX, LY, LZ = 4.6, 2.4, 2.6      # 看不见的盒子半宽、半深、半高（米）
CAM_D = 12.0

# (函数名, 份数, 参数)
PARTS = [("p22_key", 4, "seed"), ("p03_person", 2, None), ("p21_lock", 2, None), ("p34_flask", 2, None), ("p10_calendar", 2, None),
         ("p11_bill", 2, None), ("p12_medal", 2, None), ("p13_chip", 2, None), ("p09_iv_bag", 2, None), ("p15_sample_tube", 2, None),
         ("p17_paper_book", 2, None), ("p18_loupe_checklist", 2, None), ("p14_buildings", 2, None), ("p43_mouse", 1, None),
         ("p46_newspaper", 1, None), ("p27_data_disks", 1, None), ("p44_plug_bin", 1, None), ("p04_liver", 1, None),
         ("p19_cdk20", 2, None), ("p08_capsule", 1, None), ("p23_cell", 1, None), ("p06_globe", 1, None)]


def fuse(root, name):
    """零件的各块料（含字）合成一个网格，量好中心，放大 SC 倍。材质保留。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    objs, gone = [], []

    def walk(o):
        for c in o.children:
            walk(c)
        gone.append(o)
        if o is root or o.hide_render:
            return
        if o.type in ("MESH", "FONT", "CURVE"):
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            n = bpy.data.objects.new(o.name + "_f", me)
            n.matrix_world = o.matrix_world.copy()
            bpy.context.collection.objects.link(n)
            objs.append(n)
    walk(root)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.data.transform(j.matrix_world)
    j.matrix_world = Matrix.Identity(4)
    co = np.empty(len(j.data.vertices) * 3, np.float32)
    j.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    c = (co.max(0) + co.min(0)) / 2
    j.data.transform(Matrix.Translation(-Vector(c)))
    j.data.transform(Matrix.Scale(SC, 4))
    j.name = name; j.data.name = name
    for o in gone:
        bpy.data.objects.remove(o)
    return j


def hull_of(me):
    bm = bmesh.new(); bm.from_mesh(me)
    h = bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=h["geom_interior"] + h["geom_unused"], context="VERTS")
    v = np.array([x.co[:] for x in bm.verts], np.float64)
    idx = {x: i for i, x in enumerate(bm.verts)}
    f = [[idx[x] for x in fc.verts] for fc in bm.faces]
    bm.free()
    return v, f


def make_scene(samples):
    sc = KP.scene_base(samples)
    sc.render.fps = FPS
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"; sc.render.image_settings.color_depth = "8"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    K = KP.Kit()
    KP.lights(0, 0, SC)
    cam = KP.camera(sc, (0, 0, 0), CAM_D, 0, 0, lens=50, fstop=3.0, focus=(0, -8.0, 0))
    return sc, K


def build(out, samples):
    t0 = time.time()
    sc, K = make_scene(samples)
    rnd = random.Random(2026)
    src = {}
    inst = []                                    # (名字, 基础网格, 半径, 包围球半径)
    for fn, n, mode in PARTS:
        for k in range(n):
            key = (fn, k if mode == "seed" else 0)
            if key not in src:
                root = getattr(KP, fn)(K, seed=k + 1) if mode == "seed" else getattr(KP, fn)(K)
                src[key] = fuse(root, "%s_%d" % (fn, key[1]))
                src[key].hide_render = True; src[key].hide_viewport = True
            inst.append((fn, k, src[key]))
    objs, R, RB, hulls = [], [], [], []
    for i, (fn, k, base) in enumerate(inst):
        j = rnd.uniform(0.85, 1.2)
        me = base.data.copy(); me.transform(Matrix.Scale(j, 4))
        o = bpy.data.objects.new("w5_%02d_%s" % (i, fn), me)
        bpy.context.collection.objects.link(o)
        o.rotation_mode = "QUATERNION"
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        d = np.sort(co.max(0) - co.min(0))[::-1]
        R.append(float(0.25 * (d[0] + d[1])))
        RB.append(float(np.linalg.norm(co, axis=1).max()))
        objs.append(o)
    for b in src.values():
        bpy.data.objects.remove(b)
    # ---- 刚体世界
    sc.frame_start, sc.frame_end = 1, NSIM
    bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    sc.gravity = (0, 0, 0)
    w.substeps_per_frame = 20; w.solver_iterations = 40
    w.point_cache.frame_start = 1; w.point_cache.frame_end = NSIM
    for o in objs:
        for q in bpy.context.view_layer.objects:
            q.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.rigidbody.object_add()
        rb = o.rigid_body
        rb.collision_shape = "CONVEX_HULL"; rb.mass = 1.0; rb.restitution = 0.85; rb.friction = 0.25
        rb.linear_damping = 0.03; rb.angular_damping = 0.06
        rb.use_margin = True; rb.collision_margin = 0.006
    walls = []
    for nm, c, dim in (("xp", (LX + .5, 0, 0), (1, 2 * LY + 2, 2 * LZ + 2)), ("xn", (-LX - .5, 0, 0), (1, 2 * LY + 2, 2 * LZ + 2)),
                       ("yp", (0, LY + .5, 0), (2 * LX + 2, 1, 2 * LZ + 2)), ("yn", (0, -LY - .5, 0), (2 * LX + 2, 1, 2 * LZ + 2)),
                       ("zp", (0, 0, LZ + .5), (2 * LX + 2, 2 * LY + 2, 1)), ("zn", (0, 0, -LZ - .5), (2 * LX + 2, 2 * LY + 2, 1))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        o = bpy.context.object; o.name = "wall_" + nm; o.dimensions = dim; o.hide_render = True
        bpy.ops.rigidbody.object_add(type="PASSIVE")
        o.rigid_body.collision_shape = "BOX"; o.rigid_body.restitution = 1.0; o.rigid_body.friction = 0.1
        o.rigid_body.use_margin = True; o.rigid_body.collision_margin = 0.006
        walls.append(o)
    N = len(objs)
    # ---- 起始位置：互相不挨着
    P = []
    for i in range(N):
        for _ in range(4000):
            p = np.array([rnd.uniform(-LX + RB[i], LX - RB[i]), rnd.uniform(-LY + RB[i], LY - RB[i]), rnd.uniform(-LZ + RB[i], LZ - RB[i])])
            if all(np.linalg.norm(p - P[j]) > (RB[i] + RB[j]) * 1.05 for j in range(len(P))):
                break
        else:
            raise SystemExit("起始位置放不下，减零件数")
        P.append(p)
    P = np.array(P)
    Q = []
    for i in range(N):
        q = Quaternion((rnd.gauss(0, 1) for _ in range(4))); q.normalize(); Q.append(q)
    pose = {}                                    # 最近一次转接时设定的

    def handoff(i, f, p, q, v, spin):
        """从帧 f 之后的 3 帧让零件 i 走运动学，第 f+4 帧放手：它带着速度 v（米/秒）和自转 spin（弧度/秒，三维向量）继续飞。"""
        o = objs[i]
        ang = spin.length
        for s in (1, 2, 3):
            o.rigid_body.kinematic = True
            o.keyframe_insert("rigid_body.kinematic", frame=f + s)
            o.location = Vector(p) + Vector(v) * (s / FPS)
            q2 = (Quaternion(spin.normalized(), ang * s / FPS) @ q) if ang > 1e-6 else q
            o.rotation_quaternion = q2
            o.keyframe_insert("location", frame=f + s)
            o.keyframe_insert("rotation_quaternion", frame=f + s)
        o.rigid_body.kinematic = False
        o.keyframe_insert("rigid_body.kinematic", frame=f + 4)
        busy[i] = f + 4

    busy = [0] * N
    hulls = [hull_of(o.data) for o in objs]

    def contact_frame(i, j, pi_, pj_, qi, qj, vi, vj, wi, wj, fmax):
        """两个凸包按匀速直线加匀速自转飞，第几帧（从踢出帧算起）第一次重叠。没撞上返回 None。"""
        def tree(a, p, q, v, w, s_):
            qq = (Quaternion(w.normalized(), w.length * s_ / FPS) @ q).to_matrix()
            vw = hulls[a][0] @ np.array(qq).T + np.array(p) + np.array(v) * (s_ / FPS)
            return BVHTree.FromPolygons([tuple(x) for x in vw], hulls[a][1])
        s_ = 4
        while s_ <= fmax:
            if tree(i, pi_, qi, vi, wi, s_).overlap(tree(j, pj_, qj, vj, wj, s_)):
                return s_
            s_ += 2
        return None
    for i in range(N):
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))); d.normalize()
        o = objs[i]
        o.location = Vector(P[i]); o.rotation_quaternion = Q[i]
        handoff(i, 0, P[i], Q[i], d * rnd.uniform(0.15, 0.5), Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized() * rnd.uniform(0.1, 0.5))
    # ---- 拍子表：film 秒 -> 一次撞击，重（一个小节头撞 2 对）或轻（第 3 拍撞 1 对）
    beat = 60.0 / BPM
    events = []                                  # (撞击帧, 轻重)
    k = 0
    while True:
        t = BEAT0 + k * beat
        if t > NF / FPS - 0.3:
            break
        if t > -1.0:
            if k % 4 == 0:
                events += [(WARM + 1 + round(t * FPS), "heavy"), (WARM + 1 + round(t * FPS), "heavy")]
            elif k % 4 == 2:
                events.append((WARM + 1 + round(t * FPS), "light"))
        k += 1
    plan = []                                    # (踢出帧, 撞击帧, 轻重)
    for c, kind in events:
        T = rnd.uniform(1.0, 1.6)
        plan.append((max(6, c - round(T * FPS)), c, kind, T))
    plan.sort()
    planned = []                                 # 实际排了的对 (i, j, 撞击帧, 踢出帧)
    LOC = np.zeros((NSIM + 1, N, 3)); QUA = np.zeros((NSIM + 1, N, 4))
    last_used = [-999] * N
    pi = 0
    skipped = 0
    for f in range(1, NSIM + 1):
        sc.frame_set(f)
        for i, o in enumerate(objs):
            m = o.matrix_world
            LOC[f, i] = m.translation[:]
            QUA[f, i] = m.to_quaternion()[:]
        if f < 3:
            continue
        vel = (LOC[f] - LOC[f - 1]) * FPS
        # 慢下来的零件轻轻推一下（每 1.5 秒查一次）
        if f % 90 == 0:
            for i in range(N):
                if busy[i] < f and np.linalg.norm(vel[i]) < 0.18 and f - last_used[i] > 60:
                    d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1) * 0.6)); d.normalize()
                    p = LOC[f, i]; q = Quaternion(QUA[f, i])
                    # 推向盒子里面
                    d = d - Vector(p / np.array([LX, LY, LZ]) * 0.6); d.normalize()
                    handoff(i, f, p, q, d * rnd.uniform(0.3, 0.6), Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized() * rnd.uniform(0.2, 0.6))
                    last_used[i] = f
        while pi < len(plan) and plan[pi][0] <= f:
            fk, c, kind, T = plan[pi]; pi += 1
            T = (c - f) / FPS
            if T < 0.5:
                skipped += 1; continue
            best = None
            pos = LOC[f]
            for i in range(N):
                if busy[i] >= f or last_used[i] > f - 45:
                    continue
                if abs(pos[i, 0]) > LX - 0.8 or abs(pos[i, 2]) > LZ - 0.6 or abs(pos[i, 1]) > LY - 0.5:
                    continue
                for j in range(i + 1, N):
                    if busy[j] >= f or last_used[j] > f - 45:
                        continue
                    dvec = pos[j] - pos[i]; d = float(np.linalg.norm(dvec))
                    gap = d - (R[i] + R[j])
                    sp = gap / (2 * T)
                    if not (0.35 <= sp <= 1.1):
                        continue
                    # 画面里要看得到：两个都在可见范围内（透视后）
                    ok = True
                    for kk in range(N):
                        if kk in (i, j):
                            continue
                        seg = dvec / d
                        t_ = float(np.dot(pos[kk] - pos[i], seg))
                        if 0 < t_ < d:
                            if np.linalg.norm(pos[kk] - pos[i] - t_ * seg) < RB[kk] + 0.35:
                                ok = False; break
                    if not ok:
                        continue
                    vis = (abs(pos[i, 0]) < 3.6 and abs(pos[j, 0]) < 3.6 and abs(pos[i, 2]) < 2.2 and abs(pos[j, 2]) < 2.2)
                    score = abs(sp - 0.65) + (0 if vis else 0.8) + rnd.uniform(0, 0.25)
                    if best is None or score < best[0]:
                        best = (score, i, j, sp, dvec / d)
            if best is None:
                skipped += 1; continue
            _, i, j, sp, n = best
            spins = [Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized() * rnd.uniform(0.3, 0.9) for _ in (0, 1)]
            qi_, qj_ = Quaternion(QUA[f, i]), Quaternion(QUA[f, j])
            target = c - f
            lo, hi = 0.2, 1.4
            gl = contact_frame(i, j, LOC[f, i], LOC[f, j], qi_, qj_, Vector(n * hi), Vector(-n * hi), spins[0], spins[1], target + 60)
            for _ in range(7):                    # 二分速度：让两个凸包刚好在撞击帧碰上
                mid = (lo + hi) / 2
                g = contact_frame(i, j, LOC[f, i], LOC[f, j], qi_, qj_, Vector(n * mid), Vector(-n * mid), spins[0], spins[1], target + 60)
                if g is None or g > target:
                    lo = mid
                else:
                    hi = mid
            sp = (lo + hi) / 2 if gl is not None else sp
            for a, sgn, sn in ((i, 1, spins[0]), (j, -1, spins[1])):
                handoff(a, f, LOC[f, a], Quaternion(QUA[f, a]), Vector(n * sgn * sp), sn)
                last_used[a] = f
            planned.append((i, j, c, f, kind))
        if f % 300 == 0:
            print("sim frame", f, "of", NSIM, "%.0fs" % (time.time() - t0), flush=True)
    print("sim done: planned", len(planned), "pairs, skipped", skipped, flush=True)
    # ---- 自检：穿模（凸包互相重叠）
    over = {}
    worst = 0
    t1 = time.time()
    for f in range(WARM + 1, NSIM + 1):
        pos = LOC[f]
        trees = {}
        for i in range(N):
            for j in range(i + 1, N):
                if np.linalg.norm(pos[i] - pos[j]) > RB[i] + RB[j]:
                    continue
                for a in (i, j):
                    if a not in trees:
                        Rm = np.array(Quaternion(QUA[f, a]).to_matrix())
                        vw = hulls[a][0] @ Rm.T + pos[a]
                        trees[a] = BVHTree.FromPolygons([tuple(x) for x in vw], hulls[a][1])
                if trees[i].overlap(trees[j]):
                    over.setdefault((i, j), []).append(f)
    n_pairs = len(over)
    n_frames = sorted({f for fs in over.values() for f in fs})
    print("overlap check %.0fs: pairs with overlap %d, frames with overlap %d" % (time.time() - t1, n_pairs, len(n_frames)), flush=True)
    # ---- 自检：撞击和拍子对得上吗（速度突变）
    V = np.diff(LOC, axis=0) * FPS               # V[f-1] 是 f-1 到 f 的速度
    dv = np.linalg.norm(np.diff(V, axis=0), axis=2)      # dv[k] 对应 f = k+2 附近
    offs, hit = [], 0
    for i, j, c, fk, kind in planned:
        win = range(max(4, c - 24), min(NSIM - 2, c + 24))
        cand = [(f, max(dv[f - 2, i], dv[f - 2, j])) for f in win if f - 2 < len(dv)]
        cand = [x for x in cand if x[1] > 0.12]
        if cand:
            f_, _ = max(cand, key=lambda x: x[1]); offs.append(f_ - c); hit += 1
    # 所有速度突变（含撞墙）按帧列出，看有多少落在拍子上
    allev = []
    for f in range(WARM + 1, NSIM - 1):
        if (dv[f - 2] > 0.25).any():
            allev.append(f)
    # ---- 烘成关键帧：去掉刚体，每帧一个关键帧
    for q in bpy.context.view_layer.objects:
        q.select_set(False)
    for o in objs:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        o.animation_data_clear()
        bpy.ops.rigidbody.object_remove()
        o.select_set(False)
    bpy.ops.rigidbody.world_remove()
    for o in walls:
        bpy.data.objects.remove(o)
    for i, o in enumerate(objs):
        for f in range(WARM + 1, NSIM + 1):
            o.location = Vector(LOC[f, i]); o.rotation_quaternion = Quaternion(QUA[f, i])
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_quaternion", frame=f)
    sc.frame_start, sc.frame_end = WARM + 1, NSIM
    sc.frame_set(WARM + 1)
    np.savez_compressed(Path(out).with_suffix(".npz"), loc=LOC[WARM + 1:], quat=QUA[WARM + 1:], radius=np.array(R))
    names = [o.name for o in objs]
    rep = {"objects": N, "names": names, "planned_pairs": len(planned), "skipped_events": skipped, "pairs_with_overlap": n_pairs,
           "frames_with_overlap": len(n_frames), "overlap_pairs": [[names[a], names[b], fs[0], len(fs)] for (a, b), fs in list(over.items())[:30]],
           "beat_offsets_frames_at60": offs, "planned_hit": hit,
           "beat_events_planned": [[names[i], names[j], round((c - WARM - 1) / FPS, 3), kind] for i, j, c, fk, kind in planned],
           "bpm": BPM, "beat0": BEAT0, "speed_max": float(np.linalg.norm(V[WARM:], axis=2).max()), "speed_mean": float(np.linalg.norm(V[WARM:], axis=2).mean()),
           "sim_seconds": round(time.time() - t0, 1)}
    Path(out).with_suffix(".check.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print("saved", out, "check ->", Path(out).with_suffix(".check.json"), flush=True)


def gpu():
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"; pr.get_devices()
    for d in pr.devices:
        d.use = d.type != "CPU"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = "OPTIX"          # 导演 11-20：降噪也走显卡
    print("cycles device", bpy.context.scene.cycles.device, [d.name for d in pr.devices if d.use], "denoiser", bpy.context.scene.cycles.denoiser, flush=True)


def still(blend, out, n, samples, pct):
    bpy.ops.wm.open_mainfile(filepath=blend)
    gpu()
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.frame_set(WARM + 1 + 2 * n)
    sc.render.resolution_percentage = pct
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


def frames(blend, outdir, n0, n1, step, samples):
    bpy.ops.wm.open_mainfile(filepath=blend)
    gpu()
    sc = bpy.context.scene
    sc.cycles.samples = samples
    Path(outdir).mkdir(parents=True, exist_ok=True)
    t0 = time.time(); done = 0
    for n in range(n0, n1 + 1, step):
        p = Path(outdir) / ("bg_%04d.png" % n)
        if p.exists() and p.stat().st_size > 0:
            continue
        sc.frame_set(WARM + 1 + 2 * n)
        sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        done += 1
        if done % 10 == 0:
            print("frame", n, "done", done, "%.1f s/frame" % ((time.time() - t0) / done), flush=True)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], int(a[2]) if len(a) > 2 else 24)
    elif a[0] == "still":
        still(a[1], a[2], int(a[3]), int(a[4]) if len(a) > 4 else 32, int(a[5]) if len(a) > 5 else 100)
    elif a[0] == "frames":
        frames(a[1], a[2], int(a[3]), int(a[4]), int(a[5]) if len(a) > 5 else 1, int(a[6]) if len(a) > 6 else 24)
