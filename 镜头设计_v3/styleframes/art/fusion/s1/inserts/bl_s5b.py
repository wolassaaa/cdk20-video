"""HKBU SCIE1007 课程作业的科普视频。S5 的 5-01、5-07、5-10 三段台面版（11-10 通宵第二批，Claude），由 bl_inserts.py 的 BL_EXTRA 接口运行。
bl_s5.py（4-10、5-04）别的工人还在改，这里不动它，只在运行时读进来，借它的 shot_s410 搭出 4-10 最后一帧的台面。

`s501`：接 4-10 最后一帧（7 把钥匙一行）。镜头往下落到前面的格子 39；七张纸卡（论文 Fig. 5 的结构，骨白底版裁切，见 make_s5b_cards.py）
从画面上方一张张落到格子里，排成一行，和后面那行钥匙一一对应。卡上的编号、Kd 和"Kd: lower = tighter"小尺在 Remotion（s5b.jsx）里叠。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s5b.py blender.exe -b -t 4 -P bl_inserts.py -- s501 <输出目录> [首帧] [末帧] [采样] [尺寸] [步长]
BL_S5B_PROJ=<秒>：只打印那一刻卡片在画面上的位置（给 s5b.jsx 定字的位置），不渲染。
"""
import math
import os

import bpy
from mathutils import Quaternion, Vector

META = {"s501": (625.0, 1020, 0.2, 0.9)}   # 5-01 10:25-10:42，17 秒
MY_META = dict(META)                        # bl_s5.py 读进来时会把 META 换成它自己的

_here = os.path.dirname(os.path.abspath(XFILE))
exec(compile(open(os.path.join(_here, "bl_s5.py"), encoding="utf-8").read(), "bl_s5.py", "exec"))
CARDS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))), "remotion_public", "fusion_s5b")
NAMES = ["001", "004", "007", "009", "015", "019", "025"]          # Fig. 5 的七个，和 4-10 那行钥匙从左到右一一对应
CW, CD, CT = 0.105, 0.070, 0.0025                                   # 纸卡：宽、深、厚（贴图 600 x 400）
CGAP = 0.112


def s410_end(sc, sky):
    """4-10 的最后一帧，动画全清掉；返回 4-10 的 ctx（钥匙、那一行、结尾机位）。"""
    upd = shot_s410(sc, sky)
    X = upd.ctx
    upd(T0 + 1499 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    return X


def card_mat(name):
    m = bpy.data.materials.new("s5b_card_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.75
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(CARDS, "card_%s.png" % name))
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def paper_card(sc, name, edge):
    """一张纸卡：薄板，顶面贴论文的结构图（UV 铺满顶面），四边和底面是纸色。原点在底面中心。"""
    import bmesh
    me = bpy.data.meshes.new("s5b_card_" + name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(CW, CD, CT), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, CT / 2), verts=bm.verts)
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        top = f.normal.z > 0.5
        f.material_index = 0 if top else 1
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = ((co.x / CW + 0.5), (co.y / CD + 0.5)) if top else (0.02, 0.02)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(card_mat(name))
    me.materials.append(edge)
    o = bpy.data.objects.new("s5b_card_" + name, me)
    sc.collection.objects.link(o)
    o.rotation_mode = "QUATERNION"
    return o


def shot_s501(sc, sky):
    """5-01（10:25-10:42，C 画外音）。0-1 s 是 4-10 的最后一帧，不动；1.0-3.0 s 镜头落到格子 39（一次移动，2 秒）；
    2.6 s 起七张纸卡从画面上方一张张直落进格子 39，每张 0.55 秒，缓停，不弹；4.5 s 后台面不再动，字在 Remotion 里出。"""
    X = s410_end(sc, sky)
    end_v, q_row = X["end_v"], X["q_row"]
    T5 = MY_META["s501"][0]
    yaw = math.radians(20.0)
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

    T_M, T_ME = 1.0, 3.0
    T_LAND0, T_STAG, T_DROP, Z0 = 2.6, 0.22, 0.55, 0.9
    card_v = dict(at=tuple(ROW - ru * 0.045 + Vector((0.0, 0.06, 0.0))), az=yaw, el=math.radians(50.0), d=1.17, mm=45.0)

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M:
            return dict(end_v)
        if t < T_ME:
            return mix(end_v, card_v, smooth((t - T_M) / (T_ME - T_M)))
        return dict(card_v)

    def focus(t):
        a_, b_ = Vector(end_v["at"]), ROW
        return a_.lerp(b_, smooth((t - T_M) / (T_ME - T_M)))

    def card_z(i, t):
        """直落：从 Z0 落到台面，缓入缓停（末速为零），不弹。落之前在画面上方外面。"""
        t1 = T_LAND0 + T_STAG * i
        t0 = t1 - T_DROP
        if t < t0:
            return Z0
        x = min(1.0, (t - t0) / T_DROP)
        return Z0 * (1.0 - smooth(x))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None

    def keyed(e, i, t, f):
        e.animation_data_clear()
        for df in (-1, 0, 1):
            e.location = home[i] + Vector((0, 0, card_z(i, t + df / FPS)))
            e.keyframe_insert("location", frame=f + df)
        e.location = home[i] + Vector((0, 0, card_z(i, t)))

    def update(t_abs):
        t = t_abs - T5
        f = int(round(t * FPS))
        shoot(c, f, cam(t), focus(t))
        for i, e in enumerate(cards):
            e.rotation_quaternion = q_row
            t1 = T_LAND0 + T_STAG * i
            if t1 - T_DROP - 0.05 <= t <= t1 + 0.05:
                keyed(e, i, t, f)
            else:
                e.animation_data_clear()
                e.location = home[i] + Vector((0, 0, card_z(i, t)))
            e.hide_render = card_z(i, t) >= Z0 - 1e-6 and t < t1          # 落之前不在台面上
        sky(0.2)

    update.view = cam
    update.ctx = dict(X, cards=cards, card_home=home, card_v=card_v, row=ROW)

    # ---------------------------------------------------------------- 穿模检查（解析：卡在格子里、彼此不叠、不入台面、不碰钥匙那一格）
    if SHOT == "s501" and not os.environ.get("BL_NOCHECK"):
        bad = {}
        half_x, half_y = 0.95 / 2 - 0.06, 0.84 / 2 - 0.06          # 格子内沿（留出圆角槽壁）
        corners = [Vector((sx * CW / 2, sy * CD / 2, 0)) for sx in (-1, 1) for sy in (-1, 1)]
        qm = q_row.to_matrix()
        for i in range(7):
            for k in corners:
                p = home[i] + qm @ k
                if abs(p.x - c39.x) > half_x or abs(p.y - c39.y) > half_y:
                    bad.setdefault("card %s / cell wall" % NAMES[i], []).append(tuple(round(v, 3) for v in p))
        # 相邻两张：沿行方向的间隙
        gap = CGAP - CW
        if gap <= 0.002:
            bad["card / card"] = [gap]
        for f in range(0, FRAMES, 2):
            for i in range(7):
                if card_z(i, f / FPS) < -1e-6:
                    bad.setdefault("card / table", []).append(f)
        print("S501 clashes:", "none" if not bad else "")
        for k, v in bad.items():
            print("S501 clash %s: %s" % (k, v[:3]))
        print("S501 card gap %.4f, cell margin x %.3f y %.3f" % (gap, half_x - max(abs((home[i] + qm @ k).x - c39.x) for i in range(7) for k in corners),
                                                              half_y - max(abs((home[i] + qm @ k).y - c39.y) for i in range(7) for k in corners)))
    if os.environ.get("BL_S5B_PROJ"):
        from bpy_extras.object_utils import world_to_camera_view
        tp = float(os.environ["BL_S5B_PROJ"])
        sc.frame_set(int(round(tp * FPS)))
        update(T5 + tp)
        bpy.context.view_layer.update()
        for i, e in enumerate(cards):
            for nm, off in (("mid", (0, 0)), ("front", (0, -CD / 2)), ("back", (0, CD / 2)), ("left", (-CW / 2, 0)), ("right", (CW / 2, 0))):
                p = home[i] + q_row.to_matrix() @ Vector((off[0], off[1], CT))
                v = world_to_camera_view(sc, c, p)
                print("S501 proj %s %s %.0f %.0f" % (NAMES[i], nm, v.x * 1920, (1 - v.y) * 1080))
        import sys
        sys.exit(0)
    return update


SHOTS["s501"] = shot_s501
