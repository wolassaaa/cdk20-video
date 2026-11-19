"""HKBU SCIE1007 课程作业的科普视频：W1/W5 套件盒盖 h20（标题卡）。

规格：镜头设计_v3/深化/04_片头与大标题重做.md 第四节 h20。单位毫米，盒盖局部原点在底边框平面中心，
X 右、Y 后、Z 上，顶面 Z = 64。亮面塑料，材质只用 Kit 里的。
名字只由调用方传入（names），本文件不读任何名字文件；draft=True 且没给名字时，名字行是空白占位牌。

和规格不同、已在建模报告里写明的三处：
1. 侧面加强肋凸 0.8 会让外形超出 H1 的 ±0.5，所以肋做在 0.9 深的浅槽里，肋面比外皮低 0.1。
2. 章节牌的浇口锥如果跟牌一起转，牌立起时它会扎进顶面 2.5 mm；改成固定在料杆浮雕上，
   细端停在离铰链轴 1.15 mm 处，边唇在浇口处断开 8 mm。
3. 牌背面的肋凸 0.4 会扎进顶面（牌底只离顶面 0.2），所以肋做在牌背的槽里，肋面比牌背低 0.2。
"""
import json
import math

import bpy
from mathutils import Vector
import kit_deep as D

WIDTH, LENGTH, HEIGHT = 986., 332., 64.
TOP = HEIGHT
CAV_X, CAV_Y, CEIL = 980.8, 326.8, 61.5
TITLES = ("Four a day", "Our question", "The lock", "AI helps cut a key",
          "In the lab", "How much did computers help?", "What next?", "The answer")
PEOPLE = ((), ("A", "C"), ("D", "B"), ("B", "A"), ("C",), ("D", "B"), ("A",), ("C",))
TAG_HINGE_Y, AXIS_Z = -63.5, TOP + 1.0
ROAD_Y, ROAD_R = -58., 3.
CAP16 = 17.   # 规格写 16；全盖机位下 16 mm 只有 27 px，H5 要 ≥ 28 px，所以这三行（课程名、副标题、Section 牌）用 17
LIFT = .02          # 能动的贴面件（问号、红线、课程牌）离底面的缝，渲染看不出，相交检查不算接触


# ---------------------------------------------------------------- 小工具


def _box(P, name, x, y, w, h, zc, t, m, r=2., bevel=.2):
    o = P.box(x, y, w / 2, h / 2, t, m, z=zc, r=r, bevel=bevel)
    o.name = P.nm(name)
    return o


def _cut(target, cutter, front=False):
    """布尔减。front=True 放在倒角之前（让切出来的口一起倒角），否则放在倒角之后、加权法线之前（刻线保持锐利）。"""
    cutter.hide_render = cutter.hide_viewport = True
    cutter.name = target.name + "_cut"
    mod = target.modifiers.new("recess", "BOOLEAN")
    mod.object, mod.operation, mod.solver = cutter, "DIFFERENCE", "EXACT"
    n = len(target.modifiers)
    if front:
        target.modifiers.move(n - 1, 0)
    else:
        wn = [i for i, md in enumerate(target.modifiers) if md.type == "WEIGHTED_NORMAL"]
        if wn:
            target.modifiers.move(n - 1, wn[0])
    return mod


def _frame(P, name, x, y, w, h, r, line, zc, depth, mat):
    """圆角矩形环（截面 line × depth），做刻线刀具或凸唇。w、h 是外缘尺寸。"""
    ext = D.rrect(x, y, w / 2, h / 2, r)
    inner = D.rrect(x, y, w / 2 - line, h / 2 - line, max(r - line, .1))
    n = len(ext)
    pts = [(a, b, c) for c in (zc - depth / 2, zc + depth / 2) for a, b in ext + inner]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [(j, i, 2 * n + i, 2 * n + j), (n + i, n + j, 3 * n + j, 3 * n + i),
                  (i, j, n + j, n + i), (2 * n + j, 2 * n + i, 3 * n + i, 3 * n + j)]
    return D._mesh(P, name, pts, faces, mat)


def _text(P, body, cap, x, y, base, mat, *, italic=False, align="LEFT", relief=.3, bevel=0.):
    """一行凸字：cap 是大写字母高（量 'H' 定字号），(x, y) 是基线上的对齐点，字从 base 往上凸 relief。"""
    ob = P.text("H", cap, x, y, 0, mat, italic=italic, align=align)
    cu = ob.data
    cu.align_y = "BOTTOM_BASELINE"
    cu.extrude = cu.bevel_depth = 0.
    bpy.context.view_layer.update()
    h = ob.dimensions.y
    if h > 0:
        cu.size *= cap * D.MM / h
    cu.body = body
    cu.resolution_u = 3 if cap >= 12 else 2
    bv = min(bevel, relief / 3)
    cu.extrude = (relief / 2 - bv) * D.MM
    cu.bevel_depth = bv * D.MM
    cu.bevel_resolution = 1
    ob.location = D._mm((x, y, base + relief / 2))
    ob["cap_mm"] = cap
    bpy.context.view_layer.update()
    return ob


def _width(ob):
    bpy.context.view_layer.update()
    return ob.dimensions.x / D.MM


def _xmax(ob):
    bpy.context.view_layer.update()
    return max((ob.matrix_world @ Vector(v)).x for v in ob.bound_box) / D.MM


def _fit(ob, width, minimum, label):
    """字宽超过 width 就整体缩小字号，最小 minimum（大写字高，mm）；放不下就报错。返回实际字高。"""
    cap = ob["cap_mm"]
    w = _width(ob)
    if w <= width:
        return cap
    target = cap * width / w
    if target < minimum - 1e-6:
        raise ValueError(f"h20: {label} does not fit {width:.0f} mm at {minimum:.1f} mm cap height")
    ob.data.size *= target / cap
    ob["cap_mm"] = target
    return target


def _spec(P, role, **kw):
    spec = json.loads(P.root.get("rig", "{}"))
    spec[role] = kw
    P.root["rig"] = json.dumps(spec)


# ---------------------------------------------------------------- 盒盖本体


def _shell(P):
    K = P.K
    shell = _box(P, "shell", 0, 0, WIDTH, LENGTH, HEIGHT / 2, HEIGHT, K.white, r=6, bevel=.6)
    # 2.5 mm 顶板，内腔 980.8 × 326.8（规格值，壁厚 2.6）。在倒角之前切，壁底的内外边一起倒角。
    _cut(shell, _box(P, "cavity", 0, 0, CAV_X, CAV_Y, (CEIL - 1) / 2, CEIL + 1, K.white, r=3.5, bevel=0), front=True)
    # 侧面离顶边 6 mm 一圈分件线，0.15 宽、0.15 深。
    _cut(shell, _frame(P, "side_seam", 0, 0, WIDTH + 1, LENGTH + 1, 6.5, .65, TOP - 6, .15, K.white))
    # 顶面离边 12 mm 一圈 0.6 宽、0.2 深的细槽框。
    _cut(shell, _frame(P, "top_frame_groove", 0, 0, WIDTH - 24, LENGTH - 24, 5, .6, TOP, .4, K.white))
    # 课程牌凹槽 129 × 41 × 0.6。
    _cut(shell, _box(P, "badge_socket", -399, 130, 129, 41, TOP, 1.2, K.white, r=4.4, bevel=0))
    # 盒绘区凹槽 x 130…463、y −30…100，深 1.2；槽底沿边一圈 0.6 宽、0.2 深细槽。
    _cut(shell, _box(P, "art_tray", 296.5, 35, 333, 130, TOP, 2.4, K.white, r=5, bevel=0))
    _cut(shell, _frame(P, "art_tray_groove", 296.5, 35, 327, 124, 3, .6, TOP - 1.2, .4, K.white))
    # 顶针印：内腔顶面 8 个（Ø0.8 深 0.2），顶面左下角、右下角各 1 个。
    for x in (-367.5, -122.5, 122.5, 367.5):
        for y in (-82, 82):
            _cut(shell, P.cyl(x, y, CEIL, .4, .4, K.white, bevel=0))
    for x in (-471, 471):
        _cut(shell, P.cyl(x, -144, TOP, .4, .4, K.white, bevel=0))
    # 加强肋：四个侧面各 2 条，宽 3、凸 0.8、高 40，从左右边各 120 mm 起。
    # 肋放在 0.9 深的浅槽里（槽宽 7、高 43），肋面比外皮低 0.1，外形不超出 986 × 332。
    ribs = []
    for s in (-1, 1):
        for x in (-373, 373):
            yo = s * LENGTH / 2
            _cut(shell, _box(P, "rib_pocket", x, yo, 7, 1.8, 32, 43, K.white, r=.6, bevel=0))
            ribs.append(_box(P, "side_rib", x, yo - s * (.9 + .02 - .41), 3, .82, 32, 40, K.white, r=.3, bevel=.15))
        for y in (-46, 46):
            xo = s * WIDTH / 2
            _cut(shell, _box(P, "rib_pocket", xo, y, 1.8, 7, 32, 43, K.white, r=.6, bevel=0))
            ribs.append(_box(P, "side_rib", xo - s * (.9 + .02 - .41), y, .82, 3, 32, 40, K.white, r=.3, bevel=.15))
    # 极细的二次倒角，让切出来的槽口在高光里有一条亮边。
    fine = shell.modifiers.new("fine_bevel", "BEVEL")
    fine.width, fine.segments, fine.limit_method = .05 * D.MM, 1, "ANGLE"
    fine.angle_limit = math.radians(40)
    wn = [i for i, md in enumerate(shell.modifiers) if md.type == "WEIGHTED_NORMAL"]
    shell.modifiers.move(len(shell.modifiers) - 1, wn[0])
    # 前侧面居中刻字（字是墨色，凸 0.08，嵌进去 0.04：像填墨刻字，不顶出外形）。
    side = _text(P, "SCIE1007 · Section 20007 · Group 3B", 7, 0, 0, 0, K.ink, align="CENTER", relief=.12)
    side.rotation_euler.x = math.pi / 2
    side.location = D._mm((0, -LENGTH / 2 + .04 - .06, 24))
    return shell, ribs


# ---------------------------------------------------------------- 顶面


def _top(P):
    K = P.K
    info = {}
    # 课程牌：红色圆角板，底面落在凹槽底（顶面下 0.6）。
    badge = D._move(P, "badge", "loc", (0, 12))
    plate = _box(P, "course_badge", -399, 130, 128, 40, TOP - .6 + LIFT + .8, 1.6, K.red, r=4, bevel=.4)
    t = _text(P, "SCIE1007", 18, -399, 130 - 9, TOP - .6 + LIFT + 1.6 - .01, K.inkw, align="CENTER")
    D._adopt(badge, plate, t)
    # 课程名。
    course = _text(P, "Molecular Science in Daily Life", CAP16, -320, 122, TOP - .01, K.ink, italic=True)
    info["course_end_x"] = _xmax(course)
    # 片名和问号。
    title = _text(P, "WORTH TESTING", 48, -463, 48, TOP - .01, K.ink, relief=1., bevel=.2)
    info["title_end_x"] = end = _xmax(title)
    q = D._move(P, "qmark", "loc", (0, 10))
    qm = _text(P, "?", 48, end + 6, 48, TOP + LIFT, K.red, relief=1., bevel=.2)
    D._adopt(q, qm)
    info["qmark_end_x"] = qend = _xmax(qm)
    # 红线：左端 x = −463，长度到问号右边，缩放原点在左端。
    rule = D._empty(f"{P.name}__rule", P.root)
    rule["role"] = "rule"
    D._place(rule, (-463, 36, TOP))
    _spec(P, "rule", type="scale", axis="X", min=0, max=1, rest=1, unit="ratio")
    bar = _box(P, "red_rule", (-463 + qend) / 2, 36, qend + 463, 1.4, TOP + LIFT + .2, .4, K.red, r=.65, bevel=.12)
    D._adopt(rule, bar)
    # 副标题：16 mm 字高放不下就缩到最小 14。右边界取 600 mm 和盒绘槽左边留 6 mm 两者较小（x ≤ 124）。
    sub = _text(P, "How computers help find cancer drug candidates: the CDK20 story", CAP16, -463, 10,
                TOP - .01, K.ink, italic=True)
    info["subtitle_cap_mm"] = _fit(sub, min(600., 124 + 463), 14., "subtitle")
    info["subtitle_width_mm"] = _width(sub)
    # 小标题。
    _text(P, "Inside this kit · who presents each part", 9, -463, -44, TOP - .01, K.ink, italic=True)
    return info


def _illustrations(P):
    """盒绘区：三格并排（肝、CDK20、钥匙 048），整组放大 1.6 倍，格子最低点离槽底 0.25。"""
    K = P.K
    floor = TOP - 1.2
    factories = (D.p04_liver, D.p19_cdk20, lambda k: D.p22_key(k, 48))
    cells = []
    for i, factory in enumerate(factories):
        joint = D._move(P, f"art_{i}", "loc", (0, 3))
        part = factory(K)
        if "span" in part:
            del part["span"]
        cell = D.make_cell(K, part, 0, 0, 0, name=f"{P.name}_art_{i}")
        cell.scale = (1.6,) * 3
        cell.location = D._mm((296.5 + (i - 1) * 66 * 1.6, 35, 0))
        bpy.context.view_layer.update()
        obs = [o for o in cell.children_recursive if o.type in ("MESH", "CURVE", "FONT") and not o.hide_render]
        dg = bpy.context.evaluated_depsgraph_get()
        low = 1e9
        for o in obs:
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            if len(me.vertices):
                low = min(low, min((eo.matrix_world @ v.co).z for v in me.vertices))
            eo.to_mesh_clear()
        cell.location.z = (floor + .25) * D.MM - low
        D._adopt(joint, cell)
        cells.append(cell)
        # 三角面预算（整盒 ≤ 40 万）：盒绘零件在盒盖上只有 60 mm 大，网格大于 2 万面的按比例简化到约 2.5 万。
        for o in obs:
            if o.type == "MESH":
                n = sum(len(pg.vertices) - 2 for pg in o.data.polygons)
                if n > 20000:
                    md = o.modifiers.new("box_art_budget", "DECIMATE")
                    md.ratio = 25000 / n
    return cells


def _tag_back(P, plate, x, y, w, h, n, mat_text):
    """章节牌背面：2 条竖肋（在槽里）、2 个顶针印、刻 No. n（字在浅槽里，不凸出牌背）。"""
    K = P.K
    back = AXIS_Z - .8
    out = []
    for dx in (-w * .3, w * .3):
        _cut(plate, _box(P, "rib_bed", x + dx, y, 2.4, h * .72, back, 1.2, K.white, r=.5, bevel=0))
        out.append(_box(P, "back_rib", x + dx, y, .8, h * .70, back + .6 - .2, .4, K.white, r=.3, bevel=.1))
    for dx in (-w * .15, w * .15):
        _cut(plate, P.cyl(x + dx, y - h * .3, back, .4, .4, K.white, bevel=0))
    _cut(plate, _box(P, "number_bed", x, y + h * .18, 16, 6, back, .3, K.white, r=.8, bevel=0))
    t = _text(P, f"No. {n}", 3, x, 0, 0, mat_text, align="CENTER", relief=.1)
    t.rotation_euler.x = math.pi
    t.location = D._mm((x, y + h * .18 + 1.5, back + .15 - .05))
    out.append(t)
    return out


def _name_slot(P, x, yb, names, letter, k, line):
    """一行名字：有名字就印斜体名字（字高 6.0 往下缩到 92 mm 宽，最小 5.2）；没有就是空白占位牌。"""
    K = P.K
    face = AXIS_Z + .8
    if names:
        t = _text(P, names[letter], 6, x - 46, yb, face - .01, K.ink, italic=True)
        _fit(t, 92, 5.2, f"plate {k + 1} / member {letter}")
        return [t]
    return [_box(P, "blank_name_pad", x - 46 + 31, yb + 3, 62, 6.4, face + .14, .3, K.inkg, r=1.2, bevel=.08)]


def _tags(P, names):
    K = P.K
    # 料杆浮雕：半圆截面 R3，两端半球头（下半埋在顶板里）。
    road = D._cyl(P, (0, ROAD_Y, TOP), (1, 0, 0), ROAD_R, 926, K.white, .0)
    road.name = P.nm("sprue_runner_relief")
    road.pass_index = 20
    for x in (-463, 463):
        cap = P.ball(x, ROAD_Y, TOP, ROAD_R, K.white, seg=32)
        cap.name = P.nm("sprue_runner_cap")
        cap.pass_index = 20
    face = AXIS_Z + .8
    for k, title in enumerate(TITLES):
        x, y = -399 + 114 * k, TAG_HINGE_Y - 32
        j = D._move(P, f"tag_{k}", "rot", (-90, 0), pivot=(x, TAG_HINGE_Y, AXIS_Z), axis=(1, 0, 0))
        plate = _box(P, "chapter_plate", x, y, 104, 64, AXIS_Z, 1.6, K.white, r=3, bevel=.4)
        # 正面一圈边唇 0.8 宽、凸 0.4，铰链边中间浇口处断开 8 mm。
        lip = _frame(P, "chapter_plate_lip", x, y, 103.2, 63.2, 2.6, .8, face + .2 - .01, .42, K.white)
        _cut(lip, _box(P, "lip_gate_notch", x, TAG_HINGE_Y, 8, 3, face + .2, 1.2, K.white, r=0, bevel=0))
        parts = [plate, lip]
        parts.append(_text(P, str(k + 1), 12, x - 44, y + 14, face - .01, K.ink))
        label = _text(P, title, 6.5, x - 30, y + 18, face - .01, K.ink)
        if _width(label) > 78:
            words = title.split()
            for n in range(len(words) - 1, 0, -1):
                label.data.body = " ".join(words[:n])
                if _width(label) <= 78:
                    break
            parts.append(_text(P, " ".join(words[n:]), 6.5, x - 30, y + 8, face - .01, K.ink))
        parts.append(label)
        parts.append(_box(P, "chapter_divider", x, y + 2, 92, .4, face + .1 - .01, .2, K.inkg, r=.15, bevel=.04))
        if k == 0:
            parts.append(_text(P, "All four of us", 6, x - 46, y - 12, face - .01, K.ink, italic=True))
        else:
            for line, letter in enumerate(PEOPLE[k]):
                parts += _name_slot(P, x, y - 12 - 12 * line, names, letter, k, line)
        parts += _tag_back(P, plate, x, y, 104, 64, k + 1, K.inkg)
        D._adopt(j, *parts)
        # 浇口锥固定在料杆浮雕上：粗端 Ø1.6 埋进料杆，细端 Ø0.8 停在离铰链轴 1.15 mm。
        y0, y1 = ROAD_Y - math.sqrt(ROAD_R ** 2 - (AXIS_Z - TOP) ** 2) + .3, TAG_HINGE_Y + 1.15
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.8 * D.MM, radius2=.4 * D.MM,
                                        depth=(y0 - y1) * D.MM, location=D._mm((x, (y0 + y1) / 2, AXIS_Z)))
        cone = bpy.context.object
        cone.name = P.nm("tag_gate_cone")
        cone.rotation_euler.x = math.pi / 2       # 锥轴沿 −Y：粗端朝料杆（+Y），细端朝牌
        cone.data.materials.append(K.white)
        bpy.ops.object.shade_smooth()
        cone.parent = P.root
    # Section 牌：黑色，铰链在上边 y = +150，平躺时占 y +116…+150。
    j = D._move(P, "sec_plate", "rot", (-90, 0), pivot=(338, 150, AXIS_Z), axis=(1, 0, 0))
    plate = _box(P, "section_plate", 338, 133, 250, 34, AXIS_Z, 1.6, K.black, r=3, bevel=.4)
    t = _text(P, "Section 20007 · Group 3B", CAP16, 338, 125, face - .01, K.inkw, align="CENTER")
    cap = _fit(t, 236, 10., "section plate")
    t.location.y = (133 - cap / 2) * D.MM
    parts = [plate, t]
    back = AXIS_Z - .8
    for dy in (-9, 0, 9):
        _cut(plate, _box(P, "sec_rib_bed", 338, 133 + dy, 226, 2.4, back, 1.2, K.black, r=.5, bevel=0))
        parts.append(_box(P, "sec_back_rib", 338, 133 + dy, 222, .8, back + .4, .4, K.black, r=.3, bevel=.1))
    for x in (226, 450):
        _cut(plate, P.cyl(x, 128.5, back, .4, .4, K.black, bevel=0))
    # 铰链：牌两端各一节销（跟牌转），下面各一根 Ø1.6 浇口小柱（固定在顶面），销底离柱顶 0.25。
    for pin_x, post_x in ((215.25, 211.5), (460.75, 464.5)):
        parts.append(D._cyl(P, (pin_x, 150, AXIS_Z), (1, 0, 0), .55, 9.5, K.black, .05))
        post = P.cyl(post_x, 150, TOP + .05, .8, .4, K.black, bevel=.05)
        post.name = P.nm("sec_gate_post")
    D._adopt(j, *parts)
    P.root["section_cap_mm"] = cap


# ---------------------------------------------------------------- 主函数和 rig


def h20_kit_box(K, names=None, draft=False):
    if names is not None and any(not names.get(key) for key in "ABCD"):
        missing = [key for key in "ABCD" if not names.get(key)]
        if not draft:
            raise ValueError("h20: names required for final render (missing " + ", ".join(missing) + ")")
        names = None
    if names is None and not draft:
        raise ValueError("h20: names required for final render")
    P = D.Part(K, "h20_kit_box", "white")
    lift = D._move(P, "lid_lift", "loc", (0, 80))
    hinge = D._move(P, "lid_hinge", "rot", (0, 104), pivot=(0, LENGTH / 2, 0), axis=(-1, 0, 0))
    _shell(P)
    info = _top(P)
    _illustrations(P)
    _tags(P, names)
    for key, val in info.items():
        P.root[key] = val
    P.root["placeholder_names"] = names is None
    bpy.context.view_layer.update()
    # 顶面所有件（包括各角色的空物体）都挂到 lid_hinge 下，保持静止姿态不变。
    # 注意：给 .parent 赋值会把 matrix_parent_inverse 清成单位阵，所以先存下来再算。
    hinv = hinge.matrix_parent_inverse.copy()
    for ob in tuple(P.root.children):
        if ob not in {lift, hinge}:
            old = ob.matrix_parent_inverse.copy()
            ob.parent = hinge
            ob.matrix_parent_inverse = hinv.inverted() @ old
    linv = lift.matrix_parent_inverse.copy()
    hinge.parent = lift
    hinge.matrix_parent_inverse = linv.inverted() @ hinv
    P.root["triangle_budget"] = 400000
    return P.done()


def rig(root):
    spec = json.loads(root["rig"])
    return {ob["role"]: ob for ob in root.children_recursive if ob.get("role") in spec}


def pose(root, role, value):
    cfg = json.loads(root["rig"])[role]
    j = rig(root)[role]
    value = max(cfg["min"], min(cfg["max"], value))
    if cfg["type"] == "rot":
        j.rotation_euler.x = math.radians(value)
    elif cfg["type"] == "loc":
        j.location.z = value * D.MM
    else:
        j.scale.x = max(value, 1e-4)
    j["pose_value"] = value
    return value


def rest(root):
    for role, spec in json.loads(root["rig"]).items():
        pose(root, role, spec["rest"])
