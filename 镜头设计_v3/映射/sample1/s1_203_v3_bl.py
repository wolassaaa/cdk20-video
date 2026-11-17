"""HKBU SCIE1007 课程作业的科普视频：样片一 2-03 静帧 v3（导演 11-17 意见：高达模型那种整块板件，明亮有光泽）。

主体是一整块板件（Gunpla 式）：矩形外框 + 横竖圆截面料杆组成的网格，所有零件经细小浇口挂在料杆上，
框角和料杆上有零件编号小牌（A、A1…），料杆交点有注胶口圆点。板件斜立在浅色无缝背景上，产品照的光。
零件：CDK20（项目里的 AlphaFold 包络，make_cdk20_mesh.py）、肝形件、Case study 字牌、CDK20 名牌，
以及后面各句要用的零件（胶囊、钥匙、钞票）。
三个状态对应 2-03 的三个时刻（帧取 keys/2-03.json）：
  a  开头（answer 前后）：红料从外框左侧注胶口进来，沿料杆流；零件都还是白板
  b  中段（CDK20 之后）：红料流到 CDK20 的浇口，CDK20 件注满成克莱因蓝，字牌已印 Case study
  c  句尾（cancer）：肝形件注满红；CDK20 从浇口剪下，拼到肝上；框上留下浇口残桩

    blender -b --factory-startup -P s1_203_v3_bl.py -- build OUT.blend a|b|c
单位：米。
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
MAP = HERE.parent
K = json.loads((MAP / "keys" / "2-03.json").read_text(encoding="utf-8"))
EV = {e["id"]: e for e in K["events"]}
FONTS = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts")
CDK20_NPZ = Path("G:/cdk20/work/sample1/cdk20.npz")       # styleframes/art/fusion/s1/inserts/make_cdk20_mesh.py 生成
HDRI = Path("G:/software/blender-5.3/5.3/datafiles/studiolights/world/studio.exr")

BG, BONE, INK, RED, KLEIN, GREEN, CHROME = "#F3EEE6", "#F4F1EA", "#1F1E1C", "#C8102E", "#002FA7", "#7C9A7E", "#2A2A2A"
R_BAR, R_FRAME = 0.0028, 0.0036
FX, FY = 0.15, 0.10                    # 外框半宽、半高
VX = (-0.05, 0.05)                     # 竖料杆
HY = (-0.02,)                          # 横料杆
EXPO = -3.85
TILT = 72                              # 板件后仰后与桌面夹角


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def plastic(name, col, rough=0.12, coat=0.7, sss=0.08, trans=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.05
    p.inputs["Metallic"].default_value = metal
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.004, 0.002, 0.0015)
        p.inputs["Subsurface Scale"].default_value = 0.01
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    return m


def link(o, parent=None):
    bpy.context.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


def tube(name, pts, r, m, parent, caps=True):
    cv = bpy.data.curves.new(name, "CURVE"); cv.dimensions = "3D"
    sp = cv.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2] if len(p) > 2 else 0.0, 1)
    cv.bevel_depth = r; cv.bevel_resolution = 8; cv.use_fill_caps = caps
    o = link(bpy.data.objects.new(name, cv), parent)
    o.data.materials.append(m)
    return o


def ball(name, loc, r, m, parent, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent
    return o


def cyl(name, loc, r, h, m, parent, rot=(0, 0, 0), bevel=0.0003):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=48, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    if bevel:
        b = o.modifiers.new("bv", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent
    return o


def slab(name, pts, thick, m, parent, bevel=0.0007, z=0.0):
    """平面轮廓挤出成板件，倒圆边。"""
    bm = bmesh.new()
    vs = [bm.verts.new((p[0], p[1], z - thick / 2)) for p in pts]
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if f.normal.z > 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z += thick
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me), parent)
    b = o.modifiers.new("bv", "BEVEL"); b.width = bevel; b.segments = 4; b.limit_method = "ANGLE"
    o.modifiers.new("ws", "WEIGHTED_NORMAL")
    for p in me.polygons:
        p.use_smooth = True
    o.data.materials.append(m)
    return o


def rrect(cx, cy, hx, hy, r, n=8):
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + sx * (hx - r), cy + sy * (hy - r)
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def smooth_loop(pts, n=8):
    out = []
    N = len(pts)
    for i in range(N):
        p0, p1, p2, p3 = (Vector(pts[(i + k) % N]) for k in (-1, 0, 1, 2))
        for j in range(n):
            t = j / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append((q.x, q.y))
    return out


def text(name, body, size, loc, m, parent, font="InstrumentSerif-Regular.ttf", extrude=0.0003, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(str(FONTS / font), check_existing=True)
    cu.size = size; cu.align_x = align; cu.align_y = "CENTER"
    cu.extrude = extrude; cu.bevel_depth = extrude * 0.3
    o = link(bpy.data.objects.new(name, cu), parent)
    o.location = loc
    o.data.materials.append(m)
    return o


def gate(name, a, b, m, parent):
    """浇口：料杆 → 零件的细颈，料杆一侧粗、零件一侧细。"""
    a, b = Vector(tuple(a) + (0.0,) * (3 - len(a))), Vector(tuple(b) + (0.0,) * (3 - len(b)))
    if (b - a).length > 0.009:                       # 远的零件：先从料杆伸出一段细支杆，再接短浇口
        mid = b - (b - a).normalized() * 0.004
        tube(name + "_spur", [a[:], mid[:]], R_BAR * 0.7, m, parent)
        a = mid
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=0.0014, radius2=0.0006, depth=d.length, vertices=24,
                                    location=(a + b) / 2)
    o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent
    return o


def tag(name, label, loc, m, m_ink, parent, w=0.016, h=0.009):
    o = slab(name, rrect(loc[0], loc[1], w / 2, h / 2, 0.0015), 0.0014, m, parent, bevel=0.0004)
    text(name + "_t", label, h * 0.62, (loc[0], loc[1], 0.0008), m_ink, parent, extrude=0.00025)
    return o


def cdk20_mesh(m, parent, size=0.052):
    import numpy as np
    d = np.load(str(CDK20_NPZ))
    v = d["verts"] - d["verts"].mean(0)
    q = Vector(d["mouth"].tolist()).rotation_difference(Vector((0.35, 0.0, 0.94)))
    v = v @ np.array(q.to_matrix()).T
    v *= size / float((v.max(0) - v.min(0)).max())
    v -= (v.max(0) + v.min(0)) / 2
    me = bpy.data.meshes.new("cdk20_part")
    me.from_pydata(v.tolist(), [], d["quads"].tolist())
    o = link(bpy.data.objects.new("cdk20_part", me), parent)
    for f in me.polygons:
        f.use_smooth = True
    o.data.materials.append(m)
    return o, v


LIVER = [(-0.5, 0.1), (-0.44, 0.24), (-0.28, 0.33), (-0.04, 0.33), (0.18, 0.27), (0.36, 0.18), (0.5, 0.08),
         (0.42, 0.04), (0.24, 0.0), (0.1, -0.05), (0.03, -0.1), (-0.06, -0.17), (-0.22, -0.29), (-0.38, -0.3), (-0.48, -0.14)]


def build(out, state):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 60
    r = sc.render
    r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 1080
    sc.cycles.samples = 256; sc.cycles.seed = 7
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    sc.view_settings.exposure = EXPO

    # 世界：反射用 studio HDRI，相机看到的是浅色底
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(str(HDRI))
    bg = N["Background"]; bg.inputs[1].default_value = 0.35
    L.new(env.outputs["Color"], bg.inputs["Color"])

    m_bg = plastic("backdrop", BG, rough=0.45, coat=0.0, sss=0.0)
    m_bone = plastic("bone_gloss", BONE, rough=0.1, coat=0.8, sss=0.12)
    m_red = plastic("red_gloss", RED, rough=0.1, coat=0.6, sss=0.05)
    m_blue = plastic("klein_gloss", KLEIN, rough=0.16, coat=0.45, sss=0.0)
    m_ink = plastic("ink", INK, rough=0.3, coat=0.3, sss=0.0)
    m_green = plastic("bill_green", GREEN, rough=0.12, coat=0.8, sss=0.08)
    m_chrome = plastic("chrome", CHROME, rough=0.18, coat=0.5, sss=0.0, metal=1.0)

    # 无缝背景：地面 + 弧形转上去的背板
    prof = [(0, -1.5, 0)] + [(0, 0.35 + 0.35 * math.sin(math.radians(a)), 0.35 - 0.35 * math.cos(math.radians(a))) for a in range(0, 91, 5)] + [(0, 0.7, 1.5)]
    bm = bmesh.new()
    rows = [[bm.verts.new((x, p[1], p[2])) for p in prof] for x in (-2, 2)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new("sweep"); bm.to_mesh(me); bm.free()
    sw = link(bpy.data.objects.new("sweep", me))
    for p in me.polygons:
        p.use_smooth = True
    sw.data.materials.append(m_bg)

    # 板件根：在 XY 里搭，最后整体立起来（后仰 TILT），下沿贴桌
    root = bpy.data.objects.new("sheet", None); link(root)
    # 外框
    fr = [(-FX, -FY), (FX, -FY), (FX, FY), (-FX, FY), (-FX, -FY)]
    tube("frame", fr, R_FRAME, m_bone, root)
    for x in VX:
        tube(f"bar_v{x}", [(x, -FY), (x, FY)], R_BAR, m_bone, root)
    for y in HY:
        tube(f"bar_h{y}", [(-FX, y), (FX, y)], R_BAR, m_bone, root)
    # 注胶口圆点：外框四角和交点
    for x, y in [(-FX, -FY), (FX, -FY), (FX, FY), (-FX, FY)] + [(x, y) for x in VX for y in HY] + [(x, s * FY) for x in VX for s in (1, -1)]:
        cyl("sprue_dot", (x, y, R_BAR * 0.95), 0.0022, 0.0012, m_bone, root)
    # 编号牌：框角 A，各零件旁 A1…A6
    tag("tag_A", "A", (-FX + 0.014, FY - 0.0), m_bone, m_ink, root, w=0.02, h=0.013)

    filled_cdk = state in ("b", "c")
    m_cdk = m_blue if filled_cdk else m_bone

    # --- 零件 1：CDK20（上中格） ---
    cx, cy = 0.0, 0.042
    cdk, v = cdk20_mesh(m_cdk, root)
    cdk.location = (cx, cy, 0.0)
    gate_pts = []
    import numpy as np
    for gx, gy, bx, by in ((cx, cy, VX[0], cy), (cx, cy, VX[1], cy), (cx, cy, cx, HY[0])):
        dirv = np.array([bx - gx, by - gy, 0.0]); dirv /= np.linalg.norm(dirv)
        k = int(np.argmax(v @ dirv * (np.abs(v[:, 2]) < 0.006)))
        p = v[k] + np.array([cx, cy, 0])
        gate_pts.append(((bx if bx != cx else p[0], by if by != cy else p[1], 0.0), tuple(p)))
    if state != "c":
        for i, (a, b) in enumerate(gate_pts):
            gate(f"gate_cdk{i}", a, b, m_bone if state == "a" else m_blue, root)
    else:
        for i, (a, b) in enumerate(gate_pts):          # 剪下后的残桩
            a, b = Vector(a), Vector(b)
            gate(f"stub_cdk{i}", a, a + (b - a).normalized() * 0.0025, m_blue, root)
    tag("tag_A1", "A1", (VX[0] + 0.012, FY - 0.0), m_bone, m_ink, root)

    # --- 零件 2：Case study 字牌（左上格）+ CDK20 名牌 ---
    plate = slab("plate_case", rrect(-0.1, 0.05, 0.034, 0.012, 0.003), 0.003, m_bone, root)
    gate("gate_pl0", (VX[0], 0.05), (-0.066, 0.05), m_bone, root)
    gate("gate_pl1", (-FX, 0.05), (-0.134, 0.05), m_bone, root)
    if state in ("b", "c"):
        text("t_case", "Case study", 0.0125, (-0.1, 0.0495, 0.0017), m_ink, root, font="InstrumentSerif-Italic.ttf", extrude=0.0001)
    npl = slab("plate_cdk20", rrect(0.027, 0.0, 0.02, 0.0075, 0.0025), 0.0026, m_blue if filled_cdk else m_bone, root)
    gate("gate_np0", (VX[1], 0.0), (0.0472, 0.0), m_blue if filled_cdk else m_bone, root)
    if filled_cdk:
        text("t_cdk20", "CDK20", 0.0095, (0.027, -0.0002, 0.0015), plastic("ink_white", "#F7F5F0", rough=0.2), root, extrude=0.0003)
    tag("tag_A2", "A2", (-FX + 0.014, 0.075), m_bone, m_ink, root)

    # --- 零件 3：肝形件（左下格） ---
    lv = smooth_loop([(x * 0.085 - 0.1, y * 0.085 - 0.058) for x, y in LIVER])
    liver = slab("liver_part", lv, 0.004, m_red if state == "c" else m_bone, root, bevel=0.0012)
    gate("gate_lv0", (-0.1, HY[0]), (-0.1035, -0.0302), m_red if state == "c" else m_bone, root)
    gate("gate_lv1", (-FX, -0.05), (-0.1414, -0.05), m_bone, root)
    tag("tag_A3", "A3", (-FX + 0.014, -FY), m_bone, m_ink, root)
    if state == "c":
        text("t_liver", "liver cancer", 0.0095, (-0.121, -0.069, 0.0021), plastic("ink_w2", "#FBF8F2", rough=0.2), root,
             font="InstrumentSerif-Italic.ttf", extrude=0.0003)

    # --- 后面各句用的零件（白板，还没注） ---
    for i in range(4):                                       # 胶囊（右上格）
        x = 0.07 + i * 0.019
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=(x, 0.045, 0), segments=32, ring_count=16)
        c = bpy.context.object; c.name = f"capsule_{i}"; c.scale = (1, 2.4, 1)
        bpy.ops.object.shade_smooth(); c.data.materials.append(m_bone); c.parent = root
        gate(f"gate_cap{i}", (x, FY), (x, 0.045 + 0.0144), m_bone, root)
    tag("tag_A4", "A4", (VX[1] + 0.012, FY), m_bone, m_ink, root)
    for i in range(3):                                       # 钥匙（中下格）
        x = -0.03 + i * 0.03
        k = slab(f"key_{i}", rrect(x, -0.05, 0.004, 0.022, 0.002), 0.0025, m_bone, root)
        cyl(f"key_bow{i}", (x, -0.075, 0), 0.008, 0.0025, m_bone, root)
        for t in range(2):
            slab(f"key_tooth{i}{t}", rrect(x + 0.006, -0.035 + t * 0.008, 0.003, 0.002, 0.0008), 0.0025, m_bone, root)
        gate(f"gate_key{i}", (x, HY[0]), (x, -0.0283), m_bone, root)
    tag("tag_A5", "A5", (0.0, -FY), m_bone, m_ink, root)
    slab("bill", rrect(0.1, -0.06, 0.038, 0.017, 0.002), 0.0022, m_bone, root)   # 钞票（右下格）
    gate("gate_bill0", (VX[1], -0.06), (0.062, -0.06), m_bone, root)
    gate("gate_bill1", (FX, -0.06), (0.138, -0.06), m_bone, root)
    tag("tag_A6", "A6", (FX - 0.014, -FY), m_bone, m_ink, root)

    # --- 红料：从外框左侧注胶口进来，沿横料杆往右流 ---
    reach = {"a": -0.085, "b": 0.0, "c": 0.0}[state]
    tube("red_flow", [(-FX - 0.02, HY[0], 0), (-FX, HY[0], 0), (reach, HY[0], 0)], R_BAR * 1.08, m_red, root)
    ball("red_head", (reach, HY[0], 0), R_BAR * 1.12, m_red, root, scale=(1.4, 1, 1))
    tube("sprue_in", [(-FX - 0.04, HY[0], 0), (-FX - 0.002, HY[0], 0)], 0.004, m_red, root)
    if state in ("b", "c"):
        tube("red_up", [(0.0, HY[0], 0), (0.0, gate_pts[2][1][1] - 0.006, 0)], R_BAR * 1.08, m_red, root)
    if state == "c":
        tube("red_v0", [(VX[0], HY[0], 0), (VX[0], -FY + 0.02, 0)], R_BAR * 1.08, m_red, root)

    # 立起来：绕 X 转，下沿落桌
    root.rotation_euler = (math.radians(TILT), 0, 0)
    root.location = (0, 0, FY * math.sin(math.radians(TILT)) + R_FRAME + 0.002)
    # 底下两个小支脚（不然悬空）
    for x in (-0.135, 0.135):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.045, 0.004))
        st = bpy.context.object; st.name = "stand"; st.scale = (0.008, 0.05, 0.008); st.data.materials.append(m_bone)
        st.modifiers.new("bv", "BEVEL").width = 0.002

    # 句尾：CDK20 从框上剪下，拼到肝上
    if state == "c":
        bpy.context.view_layer.update()
        Mw = root.matrix_world
        cdk.parent = None
        cdk.matrix_world = Mw @ Matrix.Translation((-0.098, -0.052, 0.013)) @ Matrix.Scale(0.62, 4)

    # 光：左上大柔光 + 右侧补光 + 顶上一块长条反光板（给高光）
    def area(name, loc, size, energy, col=(1, 0.97, 0.93), shape="RECTANGLE", sy=None):
        bpy.ops.object.light_add(type="AREA", location=loc)
        o = bpy.context.object; o.name = name
        o.data.shape = shape; o.data.size = size; o.data.size_y = sy or size; o.data.energy = energy; o.data.color = col
        o.rotation_euler = (-Vector(loc) + Vector((0, 0, 0.08))).to_track_quat("-Z", "Y").to_euler()
        return o
    area("key", (-0.7, -0.5, 0.9), 0.9, 120)
    area("fill", (0.8, -0.6, 0.35), 0.7, 25)
    area("strip", (0.0, -0.25, 0.75), 0.6, 45, sy=0.12)
    area("rim", (0.3, 0.5, 0.6), 0.5, 30)

    # 机位
    cam_d = bpy.data.cameras.new("cam"); cam = link(bpy.data.objects.new("camera", cam_d)); sc.camera = cam
    cam_d.dof.use_dof = True
    Mw = root.matrix_world
    bpy.context.view_layer.update()
    Mw = root.matrix_world
    if state == "a":
        tgt = Mw @ Vector((0.0, 0.0, 0.0)); lens, dist, fstop, el, az = 55, 0.78, 5.6, 20, -12
        focus = Mw @ Vector((-0.085, HY[0], 0))
    elif state == "b":
        tgt = Mw @ Vector((0.006, 0.026, 0.0)); lens, dist, fstop, el, az = 100, 0.40, 2.8, 18, -12
        focus = Mw @ Vector((0.0, 0.042, 0.01))
    else:
        tgt = Mw @ Vector((-0.09, -0.06, 0.0)); lens, dist, fstop, el, az = 85, 0.40, 2.8, 16, 10
        focus = cdk.matrix_world.translation
    cam_d.lens = lens; cam_d.dof.aperture_fstop = fstop
    e, a = math.radians(el), math.radians(az)
    cam.location = tgt + Vector((dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.dof.focus_distance = (focus - cam.location).length

    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("V3_BUILT", out, state)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], a[2])
