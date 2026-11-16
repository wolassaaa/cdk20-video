"""HKBU SCIE1007 课程作业的科普视频。托盘出镜模板（11-16，cut_v6，下一步方案_20261116 第 3 节）：一个台面 + 物件库，每段只给节拍表。
由 bl_inserts.py 的 BL_EXTRA 接口运行；节拍表是 prep4.py 解好的 JSON（TRAY4_SPEC 指过来，帧号 = 成片帧 60 fps）。

托盘、灯、机位拟合沿用 bl_tray2.py（和 bl_tray3 一样运行时读源码换掉节拍常数，原文件不改）；锁和钥匙也是 bl_tray2 的那一对。
物件库（位置用托盘坐标 u 左→右、v 前→后，0–1）：
  coin 钢代币（4-12 那七枚）  tube 玻璃管 + 红液  pawn 小人（骨白，可变红、可倒下）  bead 小钢珠（可变红）
  card 纸卡  ring 环（循环轮；bead 可沿环顶绕圈）  lock / key（bl_tray2 的锁和钥匙，位置固定，lock 落下、key 递进、两者一起转）
动词（只用这些，路径都在台面上平移或竖直起落，倒下朝前方空地）：
  drop 竖直落下（落点 = 词）  lift 竖直升走  slide 平移到 (u,v)  hop 跳一下  tip 朝前倒下  red 变红  fill 液面升到 level
  orbit 沿环顶绕圈（从落点起转到 until）  turn 锁和钥匙绕锁心转 deg 度（back 为真则转回）
镜像：spec.parts[i].tray = "left" / "right"，到这一段的帧就把机位位移换到那一边（托盘镜像正反打，同 4-11/4-12 样板）。
运行：TRAY4_SPEC=<json> BL_EXTRA=bl_tray4.py blender -b -P bl_inserts.py -- tm4 <输出目录> [首帧] [末帧] [采样]
TRAY4_CLASH=<out.json> 时不渲染，逐 4 帧量物件两两是否相交（BVH），写 JSON。
"""
import json
import math
import os

META = {"tm4": (0.0, 4000, 0.2, 0.9)}
_T4META = dict(META)
_SPEC = json.load(open(os.environ["TRAY4_SPEC"], encoding="utf-8"))
FRAMES = int(_SPEC["frames"])
_BIG = 99999
_LK = _SPEC.get("lockkey", {})
_BEATS = dict(okay=_BIG, to=_BIG, this=_BIG, picture=_BIG, lock=_LK.get("lock", _BIG), and_=_BIG, key=_LK.get("key", _BIG), end=_BIG,
              push=_BIG, push_end=_BIG + 24, vo302=_BIG)
_src = open(HERE + "bl_tray2.py", encoding="utf-8").read()
for a, b in (("BEATS = dict(okay=123, to=173, this=202, picture=268, lock=314, and_=376, key=424, end=439, push=443, push_end=467, vo302=466)", "BEATS = _BEATS"),
             ("rot = math.radians(25) *", "rot = 0.0 *"),
             ("    for f in range(FRAMES + 1):\n        apply(f)", "    for f in range(FRAMES + 1):\n        apply(f)\n    TRAY4_CTX.update(c=c, lock=lock_m, key=key_m, route=route, tgt=tgt, feed=feed_e, slab=slab, X0=X0, X1=X1, Y0=Y0, Y1=Y1, TC=TC, shx=shx, LC=LC)")):
    if a not in _src:
        raise SystemExit("bl_tray4: bl_tray2.py 里找不到：%r" % a[:50])
    _src = _src.replace(a, b)
TRAY4_CTX = {}
exec(compile(_src, HERE + "bl_tray2.py", "exec"))
META = {**META, **_T4META}
FRAMES = int(_SPEC["frames"])


def _hide_tree(o, h=True):
    for ch in o.children_recursive:
        ch.hide_render = h


def tm4_shot(sc, sky):
    import bmesh
    upd = tray2_shot(sc, sky)
    X = TRAY4_CTX
    c = X["c"]
    for k in ("route", "tgt", "feed"):
        _hide_tree(X[k])
    sc.frame_set(0)
    LENS, FD, SHY = c.data.lens, c.data.dof.focus_distance, c.data.shift_y
    c.data.animation_data_clear()
    c.data.lens, c.data.dof.focus_distance = LENS, FD
    SHX = X["shx"]
    MIRROR = (1340 - 480) / 1920
    X0, X1, Y0, Y1 = X["X0"], X["X1"], X["Y0"], X["Y1"]
    TW, TD = X1 - X0, Y1 - Y0
    steel = next(ch for ch in X["key"].children if ch.type == "MESH").material_slots[0].material
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    m_, nt_, out_ = gk._mat("tray4_steel")           # 灰钢（珠子用；代币沿用 4-12 样板的红钢）
    bs_ = nt_.nodes.new("ShaderNodeBsdfPrincipled")
    bs_.inputs["Base Color"].default_value = (0.50, 0.51, 0.53, 1)
    bs_.inputs["Metallic"].default_value = 1.0
    bs_.inputs["Roughness"].default_value = 0.28
    nt_.links.new(bs_.outputs[0], out_.inputs["Surface"])
    grey = m_
    bone_m = gk.surface((0.86, 0.84, 0.79), 0.6, 0.05)
    paper = gk.surface((0.93, 0.92, 0.88), 0.8, 0.0)
    redm = gk.surface(P.RED, 0.45, 0.15)
    glass = B.clear_glass()
    fluid = B.fluid(P.RED, (0.9, 0.05, 0.03))

    def uv(u, v, z=0.0):
        return Vector((X0 + u * TW, Y0 + v * TD, z))

    def mesh_cyl(name, r, h, mat, parent, z0=0.0, verts=48):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=(0, 0, 0))
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        o.parent = parent
        o.location = (0, 0, z0 + h / 2)
        B.smooth(o)
        return o

    def mesh_sph(name, r, mat, parent, z):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16, location=(0, 0, 0))
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        o.parent = parent
        o.location = (0, 0, z)
        B.smooth(o)
        return o

    objs = {}                       # name -> dict(e=empty, lib, meshes, red_meshes, home, h, ...)
    for name, d in _SPEC["objects"].items():
        lib = d["lib"]
        if lib in ("lock", "key"):
            objs[name] = dict(lib=lib, e=X[lib], meshes=[m for m in X[lib].children if m.type == "MESH"], red=[], h=0.0)
            continue
        e = empty("o_" + name)
        o = dict(lib=lib, e=e, meshes=[], red=[], home=uv(*d["at"]), fill=None)
        if lib == "coin":
            r, h = TW * 0.045, TW * 0.018
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=h)
            me = bpy.data.meshes.new(name + "_m")
            bm.to_mesh(me)
            bm.free()
            me.materials.append(steel)
            m = bpy.data.objects.new(name + "_b", me)
            sc.collection.objects.link(m)
            m.parent = e
            m.location = (0, 0, h / 2)
            B.smooth(m)
            bpy.ops.mesh.primitive_torus_add(major_radius=r * 0.62, minor_radius=r * 0.06, location=(0, 0, 0), major_segments=64, minor_segments=10)
            t = bpy.context.object
            t.name = name + "_ink"
            t.data.materials.append(ink)
            t.parent = e
            t.location = (0, 0, h + r * 0.03)
            o["meshes"] += [m, t]
            o["h"], o["r"] = h, r
        elif lib == "tube":
            TR, TH_ = TW * 0.032, TW * 0.20
            o["meshes"].append(mesh_cyl(name + "_glass", TR, TH_, glass, e, 0.0, 64))
            liq = empty("o_" + name + "_liq")
            liq.parent = e
            bpy.ops.mesh.primitive_cylinder_add(radius=TR * 0.82, depth=1.0, vertices=48, location=(0, 0, 0.5))
            lq = bpy.context.object
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
            lq.name = name + "_fluid"
            lq.data.materials.append(fluid)
            lq.parent = liq
            liq.location = (0, 0, TR * 0.15)
            o["meshes"].append(lq)
            o["fill"], o["fill_h"] = liq, TH_ * 0.85
            o["h"], o["r"] = TH_, TR
        elif lib == "pawn":
            r, h = TW * 0.022, TW * 0.085
            for mat, lst in ((bone_m, o["meshes"]), (redm, o["red"])):
                lst.append(mesh_cyl(name + "_body" + ("_r" if lst is o["red"] else ""), r, h, mat, e))
                lst.append(mesh_sph(name + "_head" + ("_r" if lst is o["red"] else ""), r * 1.05, mat, e, h + r * 0.9))
            o["h"], o["r"] = h + 2 * r, r
        elif lib == "bead":
            r = TW * d.get("size", 0.016)
            o["meshes"].append(mesh_sph(name + "_s", r, grey, e, r))
            o["red"].append(mesh_sph(name + "_sr", r, redm, e, r))
            o["h"], o["r"] = 2 * r, r
        elif lib == "card":
            w_, l_, t_ = TW * 0.10, TW * 0.13, TW * 0.006
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, t_ / 2))
            m = bpy.context.object
            m.scale = (w_, l_, t_)
            m.name = name + "_card"
            m.data.materials.append(paper)
            m.parent = e
            o["meshes"].append(m)
            o["h"], o["r"] = t_, l_ / 2
        elif lib == "ring":
            R_ = TW * d.get("size", 0.10)
            bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=TW * 0.007, location=(0, 0, TW * 0.007), major_segments=96, minor_segments=12)
            m = bpy.context.object
            m.name = name + "_ring"
            m.data.materials.append(ink)
            m.parent = e
            o["meshes"].append(m)
            o["h"], o["r"], o["R"] = TW * 0.014, R_, R_
        objs[name] = o

    # ---------------------------------------------------------------- 逐帧状态
    EV = sorted(_SPEC["events"], key=lambda e: e["f_land"])
    H_DROP = TW * 0.9

    def sm_(a, b_, f):
        return smooth((f - a) / max(b_ - a, 1e-6))

    def state(name, f):
        o = objs[name]
        p = Vector(o["home"])
        vis = False
        q = Quaternion()
        red = False
        level = 0.0
        for e in EV:
            if e["obj"] != name or f < e["f_start"]:
                continue
            a, L = e["f_start"], e["f_land"]
            v = e["verb"]
            x = 1.0 if f >= L else (f - a) / max(L - a, 1)
            if v == "drop":
                vis = True
                if "to" in e:
                    p = uv(*e["to"])
                p = Vector((p.x, p.y, H_DROP * (1 - x * x)))
            elif v == "lift":
                p = Vector((p.x, p.y, H_DROP * x * x))
                if f >= L:
                    vis = False
            elif v == "slide":
                t = uv(*e["to"])
                s = smooth(x)
                p = Vector((p.x + (t.x - p.x) * s, p.y + (t.y - p.y) * s, p.z))
            elif v == "hop":
                if f < L:
                    p = Vector((p.x, p.y, p.z + math.sin(math.pi * x) * e.get("h", 0.6) * TW * 0.05))
            elif v == "tip":
                ang = -math.pi / 2 * (x * x)
                q = Quaternion((1, 0, 0), ang)
                piv = Vector((0, -o["r"], 0))
                p = p + piv - q @ piv
            elif v == "red":
                if f >= L:
                    red = True
            elif v == "fill":
                level = e.get("from", level) + (e["level"] - e.get("from", level)) * smooth(x)
            elif v == "orbit":
                ring = objs[e["ring"]]
                c0 = ring["home"]
                R_ = ring["R"]
                until = e.get("until", FRAMES)
                ft = min(f, until)
                # 角速度从 0 起加速到 w，再按 e["w2"] 在 fast 之后加快
                t_ = max(0, ft - a)
                w = e.get("w", 0.05)
                ang = e.get("a0", -math.pi / 2) + w * t_ * min(1, t_ / 30) / (1 if t_ >= 30 else 2)
                if "fast" in e and ft > e["fast"]:
                    ang += (e.get("w2", 0.15) - w) * (ft - e["fast"]) * min(1, (ft - e["fast"]) / 30) / 2
                p = Vector((c0.x + R_ * math.cos(ang), c0.y + R_ * math.sin(ang), TW * 0.014))
        return p, vis, q, red, level

    names = [n for n, o in objs.items() if o["lib"] not in ("lock", "key")]
    for f in range(FRAMES + 1):
        for n in names:
            o = objs[n]
            p, vis, q, red, level = state(n, f)
            o["e"].location = p
            o["e"].rotation_mode = "QUATERNION"
            o["e"].rotation_quaternion = q
            o["e"].keyframe_insert("location", frame=f)
            o["e"].keyframe_insert("rotation_quaternion", frame=f)
            if o.get("fill") is not None:
                o["fill"].scale = (1, 1, max(1e-3, o["fill_h"] * level))
                o["fill"].keyframe_insert("scale", frame=f)

    # 锁和钥匙一起转（绕锁心，z 轴）：在 bl_tray2 写好的关键帧上再套一层
    turns = [e for e in EV if e["verb"] == "turn"]
    if turns:
        LC = X["LC"]
        lk = [X["lock"], X["key"]]
        base = {}
        for f in range(FRAMES + 1):
            sc.frame_set(f)
            base[f] = [(Vector(o.location), Quaternion(o.rotation_quaternion) if o.rotation_mode == "QUATERNION" else None) for o in lk]
        for f in range(FRAMES + 1):
            ang = 0.0
            for e in turns:
                a, L = e["f_start"], e["f_land"]
                deg = math.radians(e["deg"])
                if f >= a:
                    ang += deg * smooth((f - a) / max(L - a, 1))
                if e.get("back") and f >= L + e.get("hold", 12):
                    b0 = L + e.get("hold", 12)
                    ang -= deg * smooth((f - b0) / max(e.get("back_dur", 14), 1))
            qz = Quaternion((0, 0, 1), ang)
            for o, (loc, rq) in zip(lk, base[f]):
                o.location = LC + qz @ (loc - LC)
                o.keyframe_insert("location", frame=f)
                if rq is not None:
                    o.rotation_quaternion = qz @ rq
                    o.keyframe_insert("rotation_quaternion", frame=f)

    parts = _SPEC["parts"]

    def tray_side(f):
        side = parts[0]["tray"]
        for p_ in parts:
            if f >= p_["at"]:
                side = p_["tray"]
        return side

    def update(t):
        f = int(round(t * FPS))
        upd(t)
        for k in ("route", "tgt", "feed"):
            _hide_tree(X[k])
        if not _LK.get("lock_used"):
            _hide_tree(X["lock"])
        if not _LK.get("key_used"):
            _hide_tree(X["key"])
        c.data.shift_x = SHX + (MIRROR if tray_side(f) == "left" else 0.0)
        c.data.shift_y = SHY
        for n in names:
            o = objs[n]
            _, vis, _, red, level = state(n, f)
            for m in o["meshes"]:
                m.hide_render = not vis or (red and bool(o["red"]) and not m.name.endswith("_fluid") and not m.name.endswith("_glass"))
            for m in o["red"]:
                m.hide_render = not (vis and red)
            if o.get("fill") is not None:
                for m in o["meshes"]:
                    if m.name.endswith("_fluid"):
                        m.hide_render = not vis or level < 0.01

    if os.environ.get("TRAY4_CLASH"):
        groups = {n: objs[n]["meshes"] + objs[n]["red"] for n in names}
        if _LK.get("lock_used"):
            groups["lock"] = [m for m in X["lock"].children if m.type == "MESH"]
        if _LK.get("key_used"):
            groups["key"] = [m for m in X["key"].children if m.type == "MESH"]
        gn = list(groups)
        pairs = [(a, b_) for i, a in enumerate(gn) for b_ in gn[i + 1:]
                 if not ({a, b_} <= {"lock", "key"}) and not any(e["verb"] == "orbit" and {e["obj"], e["ring"]} == {a, b_} for e in EV)]
        _clash4(sc, update, groups, pairs)
    return update


def _clash4(sc, update, groups, pairs):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils.bvhtree import BVHTree
    rows = []
    for f in range(0, FRAMES, 4):
        sc.frame_set(f)
        update(f / FPS)
        dg = bpy.context.evaluated_depsgraph_get()
        row = dict(f=f, box={}, clash=[])
        bv = {}
        for name, objs_ in groups.items():
            vis = [o for o in objs_ if not o.hide_render and o.type == "MESH"]
            xs, ys, trees = [], [], []
            for o in vis:
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                mw = o.matrix_world
                vv = [mw @ v.co for v in me.vertices]
                trees.append(BVHTree.FromPolygons(vv, [tuple(p.vertices) for p in me.polygons]))
                for q in vv[::max(1, len(vv) // 100)]:
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
    json.dump(rows, open(os.environ["TRAY4_CLASH"], "w"))
    print("TRAY4_CLASH_OK", sum(1 for r in rows if r["clash"]), "clash frames", flush=True)
    raise SystemExit(0)


SHOTS["tm4"] = tm4_shot
