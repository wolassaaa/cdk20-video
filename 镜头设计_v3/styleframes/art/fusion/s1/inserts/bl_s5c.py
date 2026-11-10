"""HKBU SCIE1007 课程作业的科普视频。S5 第二批里我做的两段画外音：5-03（10:48-11:02，C 画外音，14 秒）、5-08（11:53-12:09，C 画外音，16 秒），由 bl_inserts.py 的 BL_EXTRA 接口运行。
（bl_s5b.py 是另一位做 5-01 的文件，这里不碰。）

台面接 bl_s5.py：先把 5-04 的第 0 帧（= 4-10 的末帧）原样搭出来（W3 的台面、锁、CDK20、7 把钥匙那一行、格子 21 的试管和剂量尺），
再在 CDK20 的口袋里放我们自己用 AutoDock Vina 重对接出来的姿态（镜头设计_v2/tests/T6_molecules/poses.json：001 是 mode 3，−7.944；048 是 mode 2，−8.838）。
姿态和台面上的 CDK20 是同一个坐标系（AlphaFold 模型 AF-Q8IZL9-F1 v6 的原坐标，302 个 CA 逐个对得上），所以照 shot_v 的那套换算直接放，不挪不转。
分子只按 poses.json 里的原子和键画球棍，不另画结构。字、数、日历在 Remotion 里叠（src/v3/fusion/s5c.jsx）。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s5c.py blender.exe -b -P bl_inserts.py -- s503 <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
S5C_TRACK=<json>  每两帧的相机和要贴字的点，给 Remotion，不渲染
S5C_PLAN=<json>   只写会变的帧（其余由 take 重复），不渲染
S5C_CLASH=1       穿模检查，不渲染
S5C_PROBE=1       打印口袋、分子、相机的位置，不渲染
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

META = {"s503": (648.0, 840, 0.2, 0.9), "s508": (713.0, 960, 0.2, 0.9)}   # 5-03 14 秒；5-08 16 秒
_MINE = dict(META)
exec(compile(open(HERE + "bl_s5b.py", encoding="utf-8").read(), HERE + "bl_s5b.py", "exec"))   # 只读：它读进 bl_s5.py（shot_s410、shot_s504），也有 5-01 纸卡的 paper_card
META = {**META, **_MINE}
POSES = HERE + "../../../../../../镜头设计_v2/tests/T6_molecules/poses.json"
PDB = HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"


def table_at_504(sc, sky):
    """5-04 第 0 帧的台面，摆好、去掉所有关键帧；返回 5-04 的 update（view(0) 是它的开头机位）。"""
    upd = shot_s504(sc, sky)
    upd(META["s504"][0])
    for o in bpy.data.objects:
        o.animation_data_clear()
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    return upd


def to_core():
    """AlphaFold 原坐标（埃）→ 台面世界坐标：shot_v 建 core 时用的同一套（减模型中心、转到口袋朝前上 16°、乘 P_S），再乘 core 在台面上的摆放。"""
    pdb = [l for l in open(PDB) if l.startswith("ATOM")]
    centre = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H" and int(l[22:26]) <= 346]).mean(0)
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    core = bpy.data.objects["core"]
    bpy.context.view_layer.update()
    M = np.array(core.matrix_world)

    def f(x):
        loc = (np.asarray(x, float) - centre) @ R.T * P_S
        return loc @ M[:3, :3].T + M[:3, 3]
    f.scale = float(np.linalg.norm(M[:3, 0])) * P_S                  # 1 埃在台面上多长
    f.mouth = Vector(tuple(M[:3, :3] @ (R @ np.asarray(full["mouth"])))).normalized()     # 口袋朝外的方向（世界）
    return f


def atom_r(el):
    return 0.55 if el == "C" else 0.62          # 埃；球棍图的球，不是范德华半径


BOND_R = 0.22


def ball_stick(name, pose, f, mats):
    """poses.json 的一个姿态画成球棍：原子一个球，键一根棍（双键也画一根）。返回 (空物体, 每个原子和键的物体, 原子世界坐标)。"""
    import bmesh
    atoms = np.array([a[1:] for a in pose["atoms"]], float)
    els = [a[0] for a in pose["atoms"]]
    W = f(atoms)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    s = f.scale
    parts = []

    def solid(nm, bm, mat, loc, q=None):
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        for pl in me.polygons:
            pl.use_smooth = True
        o = bpy.data.objects.new(nm, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent = root
        o.location = tuple(loc)
        if q is not None:
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = q
        return o
    for i, (p, el) in enumerate(zip(W, els)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=atom_r(el) * s)
        parts.append(("a", i, solid("%s_a%d" % (name, i), bm, mats["C" if el == "C" else "X"], p)))
    for k, (i, j, order) in enumerate(pose["bonds"]):
        a, b = Vector(tuple(W[i])), Vector(tuple(W[j]))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=BOND_R * s, radius2=BOND_R * s, depth=(b - a).length)
        parts.append(("b", (i, j), solid("%s_b%d" % (name, k), bm, mats["C"], (a + b) / 2, Vector((0, 0, 1)).rotation_difference(b - a))))
    return root, parts, W


def mol_mats():
    """碳和键用钥匙的钢（001、048 就是片里的钥匙），杂原子用台面墨色，不新加颜色、不发光。"""
    ob = bpy.data.objects
    mov = ob["w3_hover"]
    steel = next(c_ for c_ in mov.children if c_.name.startswith("hk_bow")).material_slots[0].material.copy()
    steel.name = "s5c_steel"
    for nd in steel.node_tree.nodes:
        for k in ("Emission Strength", "Strength"):
            if k in nd.inputs and (nd.type == "BSDF_PRINCIPLED" or nd.type == "EMISSION"):
                for ln in list(nd.inputs[k].links):
                    steel.node_tree.links.remove(ln)
                nd.inputs[k].default_value = 0.0
    steel.node_tree.animation_data_clear()
    ink = ob["w3_ticks0"].material_slots[0].material.copy()
    ink.name = "s5c_ink"
    return {"C": steel, "X": ink}


def see_core():
    """CDK20 的外壳是平滑包络（cdk20_core.npz），比真实的分子表面鼓，重对接姿态有一部分原子落在包络里面。
    近景里把外壳调成半透明（只调 core 自己的一份材质拷贝，试管里的蓝液不跟着变），退镜时回到不透明，和 5-04 第 0 帧一样。返回 set(不透明度)。"""
    ob = bpy.data.objects
    core = ob["core"]
    objs = [core] + [o for o in core.children_recursive if o.type == "MESH"]
    m0 = core.material_slots[0].material
    m = m0.copy()
    m.name = "s5c_core"
    for o in objs:
        for sl in o.material_slots:
            if sl.material == m0:
                sl.material = m
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    # 半透明时只留朝镜头的那层：背面（外壳里面的褶子）全透，不然一层层叠成一团
    geo, inv_, mul, val = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeValue")
    inv_.operation, mul.operation = "SUBTRACT", "MAXIMUM"
    inv_.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs["Backfacing"], inv_.inputs[1])          # 1 - 背面
    # 不透明度 a：正面 = a；背面 = 0，但 a = 1 时背面也不透（MAX(a 的整数部分, ...)），和原材质一模一样
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(val.outputs[0], mul2.inputs[0])
    nt.links.new(inv_.outputs[0], mul2.inputs[1])
    flo = nt.nodes.new("ShaderNodeMath")
    flo.operation = "FLOOR"
    nt.links.new(val.outputs[0], flo.inputs[0])
    nt.links.new(mul2.outputs[0], mul.inputs[0])
    nt.links.new(flo.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs["Alpha"])

    def set_(a):
        val.outputs[0].default_value = a
    return set_


def project(v, p):
    """台面点 → 1920x1080 像素（和 s5c.jsx 同一个公式，相机不滚转）。"""
    eye = Vector(eye_of(v))
    d = (Vector(v["at"]) - eye).normalized()
    r = Vector((d.y, -d.x, 0)).normalized()
    u = r.cross(d)
    q = Vector(tuple(p)) - eye
    F = v["mm"] / 36 * 1920
    z = q.dot(d)
    return (960 + F * q.dot(r) / z, 540 - F * q.dot(u) / z)


def clash_lig(Wa, f, pose, tag):
    """分子不动（重对接姿态），量一次就够：每个原子球、每根棍离 CDK20 表面多远，有没有进到表面里面。"""
    from mathutils.bvhtree import BVHTree
    core = bpy.data.objects["core"]
    dg = bpy.context.evaluated_depsgraph_get()
    bv = BVHTree.FromObject(core, dg)
    inv = core.matrix_world.inverted()
    k = core.scale[0]
    worst, bad = 9.0, 0
    probes = [(Wa[i], atom_r(a[0])) for i, a in enumerate(pose["atoms"])]
    probes += [(Wa[i] * (1 - u) + Wa[j] * u, BOND_R) for i, j, _ in pose["bonds"] for u in np.linspace(0, 1, 7)]
    for p, r in probes:
        q = inv @ Vector(tuple(p))
        loc, nrm, _, dist = bv.find_nearest(q)
        out = (q - loc).dot(nrm) > 0
        gap = (dist * k - r * f.scale) if out else -(dist * k + r * f.scale)
        worst = min(worst, gap)
        bad += gap < 0
    print("%s clashes:" % tag, "none" if not bad else "%d of %d probes inside CDK20" % (bad, len(probes)), "· closest gap %.5f (%.2f A)" % (worst, worst / f.scale))
    return bad


def side_modes(update, cam, sig, Wa, f, pose, tag, pts, T):
    T0_ = META[SHOT][0]
    if os.environ.get("S5C_PROBE"):
        v = cam(float(os.environ["S5C_PROBE"]))
        print("S5C core scale/A %.4f mouth %s mid %s" % (f.scale, tuple(round(x, 3) for x in f.mouth), tuple(round(x, 3) for x in Wa.mean(0))))
        print("S5C lig px", [tuple(round(x) for x in project(v, p)) for p in Wa], "mid", project(v, Wa.mean(0)))
    if os.environ.get("S5C_TRACK"):
        cams = []
        for fr in range(0, FRAMES - 1, 2):
            v = cam(fr / FPS)
            cams.append([round(x, 4) for x in eye_of(v)] + [round(x, 4) for x in v["at"]] + [round(v["mm"], 3)])
        json.dump(dict(fps=30, cam=cams, pts=pts, T=T), open(os.environ["S5C_TRACK"], "w"), separators=(",", ":"))
        print("TRACK_OK", len(cams))
    if os.environ.get("S5C_PLAN"):
        keep, last = [], None
        for fr in range(0, FRAMES - 1, 2):
            s_ = sig(T0_ + fr / FPS)
            if s_ != last:
                keep.append(fr)
            last = s_
        json.dump(dict(frames=keep), open(os.environ["S5C_PLAN"], "w"))
        print("PLAN_OK", len(keep))
    if os.environ.get("S5C_CLASH"):
        clash_lig(Wa, f, pose, tag)
    if any(os.environ.get(k) for k in ("S5C_PROBE", "S5C_TRACK", "S5C_PLAN", "S5C_CLASH")):
        raise SystemExit(0)


# ==================================================================== 5-03
LIFT_CAM = float(os.environ.get("S5C_LIFT", "1.2"))          # 第一次移动中段相机抬多少（见 mix）
LAND = float(os.environ.get("S5C_EASE", "0.6"))


def land(x):
    """第一次移动的缓动：前段快一些、后段慢慢落定（x 的 LAND 次方再 smooth）。落进口袋那一段 CDK20 一下铺满画面，放慢它，整段的快慢更匀。"""
    x = min(1.0, max(0.0, x))
    return smooth(x ** LAND)
S503 = dict(m1=(1.0, float(os.environ.get("S5C_M1", "4.0"))), lift=(1.0, 0.07, 1.1), m2=(7.0, 2.6), kd=1.4, six=3.0, tag=5.2, out=6.8, cal=9.7, cal_end=12.6,
            road=(9.7, 0.9), fill=(10.8, 1.0), rise=(12.0, 0.9))          # 路线：落下、红到 Hit、升走（第 2 版，协调方要补 ROAD MAP）


def small_road(cx, cy, n=6, gap=0.14, rad=0.045):
    """S6 第 3 行那种小路线，缩到一格的一半：一根玻璃管串 n 个玻璃泡（黑圈），红液从第一站往后流（照 bl_s6.py 的 row 3）。
    所有东西挂在一个空物体上，只上下动。返回 dict(e, xs, wet, fluid=[第一、第二站的红液])。"""
    glass, red, ink = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03)), gk.surface((0.012, 0.012, 0.014), 0.3)
    sz = W.SURFACE_Z / K
    xs = [cx + (i - (n - 1) / 2) * gap for i in range(n)]
    e = empty("s503_road")
    g = pipe([(xs[0] * K, -cy * K), (xs[-1] * K, -cy * K)], 1.1, glass, "s503_road_glass")
    g.visible_shadow, g.visible_diffuse = False, False
    kids = [g]
    for x in xs:
        before = set(bpy.data.objects)
        B.bulb(x, cy, sz, rad, ink, None, width=0.004)
        kids += list(set(bpy.data.objects) - before)
    wet = pipe([(xs[0] * K, -cy * K), (xs[-1] * K, -cy * K)], 0.8, red, "s503_road_wet")
    wet.visible_diffuse = False
    wet.data.bevel_factor_mapping_end = "SPLINE"
    fluid = [Bulb(x, red, cy, sz, rad * 0.92) for x in xs[:2]]
    kids += [wet] + [b.o for b in fluid]
    from mathutils import Matrix
    for o in kids:
        o.parent = e
        o.matrix_parent_inverse = Matrix.Translation((0, 0, 0))
    e.location = (0, 0, 0)
    return dict(e=e, xs=xs, wet=wet, fluid=fluid, kids=kids, rad=rad)


def cards_501(sc):
    """5-01 末帧格子 39 里的七张纸卡，照 bl_s5b.py 的 shot_s501 摆（用它的 paper_card、NAMES、CGAP，不改它的文件）。返回 (卡, 位置, 朝向, 5-01 末机位)。"""
    yaw = math.radians(20.0)
    q_row = Quaternion((0, 0, 1), yaw)
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
    for e, h in zip(cards, home):
        e.location, e.rotation_quaternion = h, q_row
    card_v = dict(at=tuple(ROW - ru * 0.045 + Vector((0.0, 0.06, 0.0))), az=yaw, el=math.radians(50.0), d=1.17, mm=45.0)
    return cards, home, q_row, card_v


def shot_s503(sc, sky):
    """5-03 第一版（Claude，11-10）。前接 5-01 末帧（格子 39 的七张纸卡；5-02 出镜插在中间），后接 5-04 第 0 帧（= 4-10 末帧）。
    0–1.0 s 5-01 末机位不动。1.0–3.2 s 第一次移动：落到 CDK20 口袋的近景，七张纸卡同时一张张竖直升出画外（4-10 里钥匙升走的同一个做法，不扔不弹）；
    口袋里坐着 001（我们的重对接姿态），CDK20 外壳在近景里半透明，看得见里面的分子。Kd 卡、OUR RE-DOCKING 标签在 Remotion。
    6.6–8.8 s 第二次移动：退到 5-04 的开头机位；001 淡掉、外壳回到不透明（它在口袋里，退远了本来也小得看不见）。8.8 s 后相机不动，
    Remotion 画 30 天的墨线日历，12.6 s 收掉；最后 1.4 秒是干净的 5-04 第 0 帧。"""
    upd504 = table_at_504(sc, sky)
    end_v = upd504.view(0.0)
    cards, home, q_row, card_v = cards_501(sc)
    c30 = Vector((*cell_at(30), 0.0))
    road = small_road(c30.x, c30.y + 0.24)          # 格子 30 后半格；前半格是 7 把钥匙那一行
    f = to_core()
    P = json.load(open(POSES))
    pose = P["poses"]["001"]
    root, parts, Wa = ball_stick("lig001", pose, f, mol_mats())
    mid = Vector(tuple(Wa.mean(0)))
    _e = os.environ.get("S503_POCKET", "")            # 试机位："daz,el,d,mm"
    _e = [float(x) for x in _e.split(",")] if _e else [-60.0, 36.0, 0.6, 50.0]
    pocket_v = dict(at=tuple(mid), az=end_v["az"] + math.radians(_e[0]), el=math.radians(_e[1]), d=_e[2], mm=_e[3])
    T5 = META["s503"][0]
    a0, ad = S503["m1"]
    b0, bd = S503["m2"]
    l0, ls, ld = S503["lift"]
    LIFT_Z = 1.6

    def mix(p, q, x, lift=0.0):
        """lift：中段把距离放大 (1 + lift) 倍再收回，相机抬起来看全一点，画面上的横移就慢下来（不然贴着台面平移，一帧跳 30 多级）。"""
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d") * (1 + lift * math.sin(math.pi * x)), mm=log("mm"))

    def cam(t):
        if t < a0:
            return dict(card_v)
        if t < a0 + ad:
            return mix(card_v, pocket_v, land((t - a0) / ad), LIFT_CAM)
        if t < b0:
            return dict(pocket_v)
        if t < b0 + bd:
            return mix(pocket_v, end_v, smooth((t - b0) / bd))
        return dict(end_v)

    def focus(t):
        if t < b0:
            return Vector(card_v["at"]).lerp(mid, smooth((t - a0) / ad))
        return mid.lerp(Vector(end_v["at"]), smooth((t - b0) / bd))

    def card_z(i, t):
        """竖直升起：缓起（起步速度为零），越升越快，一直升出画面（LIFT_Z），之后藏起来。"""
        x = (t - l0 - ls * i) / ld
        if x <= 0:
            return 0.0
        return LIFT_Z if x >= 1 else LIFT_Z * 2 * smooth(x * 0.5)

    def alpha(t):
        return 1.0 - smooth((t - b0 - 0.2) / 1.4)

    def road_z(t):
        """路线：从画面上方竖直落下、缓停（不弹）；红液流到第二站；再竖直升出画外（5-04 第 0 帧这格是空的）。None = 不在台面上。"""
        r0, rd = S503["road"]
        u0, ud = S503["rise"]
        if t < r0 or t >= u0 + ud:
            return None
        if t < r0 + rd:
            return 1.2 * (1 - smooth((t - r0) / rd))
        if t < u0:
            return 0.0
        x = (t - u0) / ud
        return 1.6 * 2 * smooth(x * 0.5)

    def road_front(t):
        f0, fd = S503["fill"]
        xs, r = road["xs"], road["rad"]
        return xs[0] - r - 0.01 + (xs[1] + r - (xs[0] - r - 0.01)) * smooth((t - f0) / fd)

    mats = list({o.material_slots[0].material.name: o.material_slots[0].material for _, _, o in parts}.values())
    alpha_in = [next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"] for m in mats]
    shell = see_core()
    SHELL = float(os.environ.get("S503_SHELL", "0.38"))          # 近景里 CDK20 外壳的不透明度；1 = 不透明（对照静帧）

    def shell_a(t):
        return 1.0 - (1.0 - SHELL) * smooth((t - a0 - 0.2) / (ad + 0.2)) * (1.0 - smooth((t - b0) / bd))          # 变透明拉长到 3 秒多，免得和下落挤在同一秒

    c = sc.camera
    last_q[0] = None

    def update(t_abs):
        t = t_abs - T5
        fr = int(round(t * FPS))
        shoot(c, fr, cam(t), focus(t))
        for i, e in enumerate(cards):
            e.animation_data_clear()
            if l0 + ls * i - 0.05 <= t <= l0 + ls * i + ld + 0.05:
                for df in (-1, 0, 1):
                    e.location = home[i] + Vector((0, 0, card_z(i, t + df / FPS)))
                    e.keyframe_insert("location", frame=fr + df)
            e.location = home[i] + Vector((0, 0, card_z(i, t)))
            e.hide_render = card_z(i, t) >= LIFT_Z - 1e-6
        a = alpha(t)
        for s_ in alpha_in:
            s_.default_value = a
        shell(shell_a(t))
        for _, _, o in parts:
            o.hide_render = a <= 0.001
        z = road_z(t)
        road["e"].location = (0, 0, -50 if z is None else z)
        fx = road_front(t)
        xs = road["xs"]
        road["wet"].data.bevel_factor_end = max(0.0, (fx - xs[0]) / (xs[-1] - xs[0]))
        for o in road["kids"]:
            o.hide_render = z is None
        road["wet"].hide_render = z is None or fx <= xs[0]
        for b in road["fluid"]:
            b.update(fx)
            b.o.hide_render = b.o.hide_render or z is None
        sky(0.2)

    def sig(t_abs):
        t = t_abs - T5
        if t >= b0 + bd:
            z = road_z(t)
            return ("end", None if z is None else round(z, 5), round(road_front(t), 5))
        if t < a0:
            return "card"
        if a0 + ad + 0.4 <= t < b0:          # 外壳变透明比镜头多走 0.4 秒
            return "pocket"
        return ("move", round(t, 4))

    update.view, update.sig = cam, sig
    if os.environ.get("S5C_PROBE"):
        v = end_v
        print("S503 road px", [tuple(round(x) for x in project(v, (x_, c30.y + 0.24, 0.0))) for x_ in road["xs"]])
    print("S503 card_v %s pocket_v %s end_v %s" % (card_v, pocket_v, end_v))
    if os.environ.get("S5C_CLASH"):
        clash_cards(home, q_row, card_z, cam)
    side_modes(update, cam, sig, Wa, f, pose, "S503", dict(lig=list(mid), cards=[list(h) for h in home]), S503)
    return update


def clash_cards(home, q_row, card_z, cam):
    """纸卡只竖直升：看升起的那根柱子（七张卡的平面范围，台面到 1.6）里有没有别的实体，再看升起的卡离相机最近多少。"""
    cm = q_row.to_matrix()
    cs = [h + cm @ Vector((sx * CW / 2, sy * CD / 2, 0)) for h in home for sx in (-1, 1) for sy in (-1, 1)]
    lo = Vector((min(p.x for p in cs), min(p.y for p in cs), CT + 0.0005))
    hi = Vector((max(p.x for p in cs), max(p.y for p in cs), 1.6 + CT))
    bad = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or o.name.startswith(("floor", "cell", "s5b_card", "lig001")):
            continue
        bb = [o.matrix_world @ Vector(b) for b in o.bound_box]
        if all(min(p[k] for p in bb) < hi[k] and max(p[k] for p in bb) > lo[k] for k in range(3)):
            bad.append(o.name)
    near_cam = 9.0
    for fr in range(FRAMES):
        t = fr / FPS
        eye = Vector(eye_of(cam(t)))
        for i, h in enumerate(home):
            z = card_z(i, t)
            if 0 < z < 1.6:
                near_cam = min(near_cam, (h + Vector((0, 0, z)) - eye).length)
    print("S503 cards: %s; closest a rising card comes to the camera %.3f" % ("nothing in the way" if not bad else "in the way: " + ", ".join(bad[:8]), near_cam))


SHOTS["s503"] = shot_s503


# ==================================================================== 5-08
S508 = dict(m1=(1.0, 3.6), m2=(6.8, 2.6), kd=1.4, fold=2.6, tag=4.6, lys=4.8, f049=5.4, out=6.6, test=9.5, b001=9.8, b048=11.6)          # 字的时刻和 s5c.jsx 的 S508_T 一样


def lys33(f, mat, root):
    """Lys33 的侧链（poses.json 里那个残基的原子），按名字顺次连成细棍：CA-CB-CG-CD-CE-NZ。返回 {原子名: 世界坐标}。"""
    import bmesh
    P = json.load(open(POSES))
    at = {a[0]: f(np.array(a[2:5], float)) for a in P["residues"]["Lys33"]["atoms"]}
    s = f.scale
    chain = [n for n in ("CA", "CB", "CG", "CD", "CE", "NZ") if n in at]
    objs = []
    for n in chain:
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=(0.5 if n == "NZ" else 0.3) * s)
        me = bpy.data.meshes.new("lys33_" + n)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        for pl in me.polygons:
            pl.use_smooth = True
        o = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent, o.location = root, tuple(at[n])
        objs.append(o)
    for a_, b_ in zip(chain, chain[1:]):
        a, b = Vector(tuple(at[a_])), Vector(tuple(at[b_]))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.14 * s, radius2=0.14 * s, depth=(b - a).length)
        me = bpy.data.meshes.new("lys33_%s%s" % (a_, b_))
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        o = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent, o.location = root, tuple((a + b) / 2)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(b - a)
        objs.append(o)
    return at, objs


def hbond(f, a, b, mat, root, n=6):
    """氢键画成一串墨线短划（a 到 b 之间 n 段，留空）。"""
    import bmesh
    a, b = Vector(tuple(a)), Vector(tuple(b))
    L = (b - a).length
    objs = []
    for k in range(n):
        u0, u1 = (k + 0.2) / n, (k + 0.75) / n
        p, q = a.lerp(b, u0), a.lerp(b, u1)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.09 * f.scale, radius2=0.09 * f.scale, depth=(q - p).length)
        me = bpy.data.meshes.new("hb%d" % k)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        o = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent, o.location = root, tuple((p + q) / 2)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(q - p)
        objs.append(o)
    return objs, L


def shot_s508(sc, sky):
    """5-08 第一版（Claude，11-10）。前接 5-07 末帧（bl_s5b.py 的 shot_s507：格子 20 前沿 6 把新钥匙，中景），后接 5-09 出镜（相纸）。
    0–1.0 s 5-07 末机位不动。1.0–3.2 s 第一次移动：落到 CDK20 口袋的近景，口袋里是 048（我们的重对接姿态，poses.json mode 2），
    Lys33 的侧链（墨色细棍）和它跟 048 之间的氢键（墨线短划，3.4 埃，poses.json 的 contacts）。外壳半透明，同 5-03。
    6.4–8.6 s 第二次移动：退到 5-04 的酶活特写（格子 21 的试管和剂量尺，5-04 结尾的样子）；048 淡掉、外壳回不透明。之后不动，两根柱子在 Remotion。"""
    upd507 = shot_s507(sc, sky)
    T507 = MY_META["s507"][0]
    v507 = upd507.view(1199 / FPS)
    upd507(T507 + 1199 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    assay_v = dict(at=(125.95, -2.2, 0.05), az=math.radians(0.0), el=math.radians(32.0), d=1.6, mm=45.0)     # 5-04 的结尾机位（bl_s5.py shot_s504 的 assay_v）
    f = to_core()
    P = json.load(open(POSES))
    pose = P["poses"]["048"]
    mats = mol_mats()
    root, parts, Wa = ball_stick("lig048", pose, f, mats)
    lys_at, lys_objs = lys33(f, mats["X"], root)
    hb = next(cn for cn in pose["contacts"] if cn["partner"].startswith("Lys33"))
    hb_objs, hb_L = hbond(f, f(np.array(hb["lig"])), lys_at["NZ"], mats["X"], root)
    mid = Vector(tuple(Wa.mean(0)))
    _e = os.environ.get("S508_POCKET", "")
    _e = [float(x) for x in _e.split(",")] if _e else [-40.0, 36.0, 0.62, 50.0]
    pocket_v = dict(at=tuple(mid), az=math.radians(_e[0]), el=math.radians(_e[1]), d=_e[2], mm=_e[3])
    T5 = META["s508"][0]
    a0, ad = S508["m1"]
    b0, bd = S508["m2"]

    def mix(p, q, x, lift=0.0):
        """lift：中段把距离放大 (1 + lift) 倍再收回，相机抬起来看全一点，画面上的横移就慢下来（不然贴着台面平移，一帧跳 30 多级）。"""
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d") * (1 + lift * math.sin(math.pi * x)), mm=log("mm"))

    def cam(t):
        if t < a0:
            return dict(v507)
        if t < a0 + ad:
            return mix(v507, pocket_v, land((t - a0) / ad), LIFT_CAM)
        if t < b0:
            return dict(pocket_v)
        if t < b0 + bd:
            return mix(pocket_v, assay_v, smooth((t - b0) / bd))
        return dict(assay_v)

    def focus(t):
        if t < b0:
            return Vector(v507["at"]).lerp(mid, smooth((t - a0) / ad))
        return mid.lerp(Vector((125.95, -2.3, 0.05)), smooth((t - b0) / bd))

    def alpha(t):
        return 1.0 - smooth((t - b0 - 0.2) / 1.4)

    all_parts = [o for _, _, o in parts] + lys_objs + hb_objs
    mlist = list({o.material_slots[0].material.name: o.material_slots[0].material for o in all_parts}.values())
    alpha_in = [next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"] for m in mlist]
    shell = see_core()
    SHELL = float(os.environ.get("S508_SHELL", "0.38"))

    def shell_a(t):
        return 1.0 - (1.0 - SHELL) * smooth((t - a0 - 0.2) / (ad + 0.2)) * (1.0 - smooth((t - b0) / bd))          # 变透明拉长到 3 秒多，免得和下落挤在同一秒

    last_q[0] = None

    def update(t_abs):
        t = t_abs - T5
        shoot(c, int(round(t * FPS)), cam(t), focus(t))
        a = alpha(t)
        for s_ in alpha_in:
            s_.default_value = a
        shell(shell_a(t))
        for o in all_parts:
            o.hide_render = a <= 0.001
        sky(0.2)

    def sig(t_abs):
        t = t_abs - T5
        if t < a0:
            return "s507"
        if a0 + ad + 0.4 <= t < b0:          # 外壳变透明比镜头多走 0.4 秒
            return "pocket"
        if t >= b0 + bd:
            return "assay"
        return ("move", round(t, 4))

    update.view, update.sig = cam, sig
    print("S508 v507 %s pocket_v %s hbond %.2f A" % (v507, pocket_v, hb_L / f.scale))
    if os.environ.get("S5C_PROBE"):
        v = cam(float(os.environ["S5C_PROBE"]))
        print("S508 NZ px", project(v, lys_at["NZ"]), "CA px", project(v, lys_at["CA"]), "hb lig px", project(v, f(np.array(hb["lig"]))))
    side_modes(update, cam, sig, Wa, f, pose, "S508", dict(lig=list(mid), nz=list(lys_at["NZ"])), S508)
    return update


SHOTS["s508"] = shot_s508
