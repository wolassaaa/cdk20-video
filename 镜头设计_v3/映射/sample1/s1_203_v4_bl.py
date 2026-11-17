"""HKBU SCIE1007 课程作业的科普视频：样片一 2-03 静帧 v4（导演 11-17 对 v3 的意见）。

像高达模型那样分色分板，每块板整板一个颜色（分色方案见 导演检查_20261117/4_分色方案.html）：
  红板 A：疾病、肝、癌      蓝板 B：CDK20 和蛋白相关      绿板 C：钞票、成本
  白板 D：字牌、编号牌、通用件  黑板 E：工具、检测          电镀板 F（香槟金镜面）：候选化合物、钥匙
CDK20 是独立零件：背面带一根定位销；肝形件上有对位凸台和孔，句尾 CDK20 正插进去，两件之间留得出缝和层次。
三个状态（2-03 三个时刻）：
  a  开头：六块板摊在桌上，像刚拆开的一盒拼装模型；红板注胶口闪一下红料
  b  中段：蓝板立起来，镜头推到 CDK20 件，名牌印 CDK20
  c  句尾：红板立起来拍肝形件；CDK20 已从蓝板剪下（蓝板上留浇口残桩），正往肝上的对位孔里插

    blender -b --factory-startup -P s1_203_v4_bl.py -- build OUT.blend a|b|c
单位：米。帧号对应 keys/2-03.json：a≈f70（answer 后），b≈f240（CDK20 之后），c≈f343（句尾）。
"""
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

FONTS = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts")
CDK20_NPZ = Path("G:/cdk20/work/sample1/cdk20.npz")       # styleframes/art/fusion/s1/inserts/make_cdk20_mesh.py 生成
HDRI = Path("G:/software/blender-5.3/5.3/datafiles/studiolights/world/studio.exr")
EXPO = -3.85

SHEETS = {   # 名字: (颜色, 板号, 粗糙度, 金属)
    "red": ("#C8102E", "A", 0.1, 0.0),
    "blue": ("#002FA7", "B", 0.12, 0.0),
    "green": ("#5E8A64", "C", 0.12, 0.0),
    "white": ("#F4F1EA", "D", 0.1, 0.0),
    "black": ("#1E1E20", "E", 0.14, 0.0),
    "chrome": ("#E2CFA0", "F", 0.06, 1.0),
    "clear": ("#F6D9DE", "G", 0.02, 0.0),        # 透明件：淡玫瑰色玻璃感（styleframes/art/_shared/glass_kit.py 的 glass_tinted 做法）
}
KIND = {"red": "实色", "blue": "实色", "green": "实色", "white": "实色", "black": "实色", "chrome": "电镀", "clear": "透明"}
HX, HY = 0.12, 0.08                     # 板件外框半宽、半高
R_BAR, R_FRAME = 0.0026, 0.0034
BARS_X, BARS_Y = (-HX, 0.0, HX), (-HY, 0.0, HY)


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def clear_glass(name, rgb=(0.95, 0.55, 0.62), density=18.0):
    """透明件：折射 + 体积吸收（厚处颜色深、薄处近乎无色），沿用旧玻璃杆的做法。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.49
    b.inputs["Transmission Weight"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*rgb, 1)
    va.inputs["Density"].default_value = density
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


def plastic(name, col, rough=0.1, coat=0.6, metal=0.0, sss=0.05):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = 0.0 if metal else coat
    p.inputs["Coat Roughness"].default_value = 0.04
    if sss and not metal:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.004, 0.002, 0.0015)
        p.inputs["Subsurface Scale"].default_value = 0.01
    return m


def link(o, parent=None):
    bpy.context.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


def v3(p):
    return Vector(tuple(p) + (0.0,) * (3 - len(p)))


def tube(name, pts, r, m, parent):
    cv = bpy.data.curves.new(name, "CURVE"); cv.dimensions = "3D"
    sp = cv.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = tuple(v3(p)) + (1,)
    cv.bevel_depth = r; cv.bevel_resolution = 8; cv.use_fill_caps = True
    o = link(bpy.data.objects.new(name, cv), parent)
    o.data.materials.append(m)
    return o


def cyl(name, loc, r, h, m, parent, bevel=0.0003, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    o = bpy.context.object; o.name = name
    if bevel:
        b = o.modifiers.new("bv", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent
    return o


def slab(name, pts, thick, m, parent, bevel=0.0006, z=0.0, holes=()):
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
    for (hx, hy, hr) in holes:
        bpy.ops.mesh.primitive_cylinder_add(radius=hr, depth=thick * 4, vertices=48, location=(hx, hy, z))
        c = bpy.context.object; c.hide_render = c.hide_viewport = True
        c.parent = parent
        bo = o.modifiers.new("hole", "BOOLEAN"); bo.object = c; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
    b = o.modifiers.new("bv", "BEVEL"); b.width = bevel; b.segments = 4; b.limit_method = "ANGLE"
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
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


def text(name, body, size, loc, m, parent, font="InstrumentSerif-Regular.ttf", extrude=0.0002, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(str(FONTS / font), check_existing=True)
    cu.size = size; cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = extrude
    o = link(bpy.data.objects.new(name, cu), parent)
    o.location = loc
    o.data.materials.append(m)
    return o


def gate(name, part_pt, bar_pt, m, parent, stub=False):
    """料杆 → 零件：远的先伸一段支杆，再接 4 mm 的锥形细浇口。stub=True 只留剪下后的残桩。"""
    a, b = v3(bar_pt), v3(part_pt)
    if stub:
        b = a + (b - a).normalized() * 0.003
    elif (b - a).length > 0.008:
        mid = b - (b - a).normalized() * 0.004
        tube(name + "_spur", [a, mid], R_BAR * 0.7, m, parent)
        a = mid
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=0.0013, radius2=0.0006, depth=d.length, vertices=24, location=(a + b) / 2)
    o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent
    return o


def to_bar(p, axis):
    """从零件边上的点沿 axis（'+x' 等）走到最近的料杆。"""
    x, y = p[0], p[1]
    if axis in ("+x", "-x"):
        xs = [b for b in BARS_X if (b > x if axis == "+x" else b < x)]
        return (min(xs, key=lambda b: abs(b - x)), y)
    ys = [b for b in BARS_Y if (b > y if axis == "+y" else b < y)]
    return (x, min(ys, key=lambda b: abs(b - y)))


def tag(name, label, loc, m, m_ink, parent, w=0.016, h=0.009):
    slab(name, rrect(loc[0], loc[1], w / 2, h / 2, 0.0015), 0.0014, m, parent, bevel=0.0004)
    text(name + "_t", label, h * 0.62, (loc[0], loc[1], 0.00075), m_ink, parent, extrude=0.0002)


def frame(root, m, m_ink, letter):
    fr = [(-HX, -HY), (HX, -HY), (HX, HY), (-HX, HY), (-HX, -HY)]
    tube("frame", fr, R_FRAME, m, root)
    tube("bar_v", [(0, -HY), (0, HY)], R_BAR, m, root)
    tube("bar_h", [(-HX, 0), (HX, 0)], R_BAR, m, root)
    for x in BARS_X:
        for y in BARS_Y:
            cyl("sprue_dot", (x, y, R_BAR * 0.95), 0.002, 0.0011, m, root)
    tag("tag_" + letter, letter, (-HX + 0.016, HY), m, m_ink, root, w=0.022, h=0.013)
    bpy.ops.mesh.primitive_cone_add(radius1=0.0045, radius2=0.0022, depth=0.009, vertices=48, location=(-HX, 0.0, 0.0045))
    cn = bpy.context.object; cn.name = "sprue_cone"; bpy.ops.object.shade_smooth(); cn.data.materials.append(m); cn.parent = root


# ---------------------------------------------------------------- 零件
LIVER = [(-0.5, 0.1), (-0.44, 0.24), (-0.28, 0.33), (-0.04, 0.33), (0.18, 0.27), (0.36, 0.18), (0.5, 0.08),
         (0.42, 0.04), (0.24, 0.0), (0.1, -0.05), (0.03, -0.1), (-0.06, -0.17), (-0.22, -0.29), (-0.38, -0.3), (-0.48, -0.14)]
SOCKET = (-0.068, 0.04)                 # 肝上对位凸台的位置（板内坐标）


def cdk20_mesh(name, m, parent, size=0.05):
    import numpy as np
    d = np.load(str(CDK20_NPZ))
    v = d["verts"] - d["verts"].mean(0)
    q = Vector(d["mouth"].tolist()).rotation_difference(Vector((0.35, 0.0, 0.94)))
    v = v @ np.array(q.to_matrix()).T
    v *= size / float((v.max(0) - v.min(0)).max())
    v -= (v.max(0) + v.min(0)) / 2
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], d["quads"].tolist())
    o = link(bpy.data.objects.new(name, me), parent)
    for f in me.polygons:
        f.use_smooth = True
    o.data.materials.append(m)
    return o, v


def cdk20_part(m, parent, center, state_cut):
    """CDK20 独立件：蛋白外形 + 背面一根定位销（插进肝上的对位孔）。返回件的根。"""
    import numpy as np
    root = bpy.data.objects.new("cdk20_part", None); link(root, parent)
    root.location = (center[0], center[1], 0)
    body, v = cdk20_mesh("cdk20_body", m, root)
    zmin = float(v[:, 2].min())
    cyl("cdk20_peg", (0, 0, zmin - 0.003), 0.0038, 0.008, m, root, bevel=0.0005)
    gates = []
    for axis, dirv in (("-x", (-1, 0)), ("+x", (1, 0)), ("-y", (0, -1))):
        dv = np.array([dirv[0], dirv[1], 0.0])
        k = int(np.argmax(v @ dv * (np.abs(v[:, 2]) < 0.006)))
        p = (v[k, 0] + center[0], v[k, 1] + center[1])
        gates.append((p, to_bar(p, axis)))
    return root, gates, zmin


def uncured():
    m = bpy.data.materials.get("uncured")
    if m:
        return m
    m = bpy.data.materials.new("uncured"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = lin("#3D63E0")
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 0.85
    b.inputs["Coat Weight"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = lin("#1E46D0"); va.inputs["Density"].default_value = 60
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


def grow_material(obj, m_solid, front):
    """按件里的高度（从下面浇口一侧往上）分三段：已固化的实色 / 前沿 6 mm 未固化半透明料 / 还没长到的部分透明。"""
    m = bpy.data.materials.new("cdk20_growing"); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    solid = N.new("ShaderNodeBsdfPrincipled")
    ps = m_solid.node_tree.nodes["Principled BSDF"]
    for k in ("Base Color", "Roughness", "Coat Weight", "Coat Roughness", "Subsurface Weight"):
        solid.inputs[k].default_value = ps.inputs[k].default_value
    wet = N.new("ShaderNodeBsdfPrincipled")
    wet.inputs["Base Color"].default_value = lin("#3D63E0"); wet.inputs["Roughness"].default_value = 0.02
    wet.inputs["Transmission Weight"].default_value = 0.8; wet.inputs["Coat Weight"].default_value = 1.0
    tr = N.new("ShaderNodeBsdfTransparent")
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.003
    L.new(nz.outputs["Fac"], add.inputs[0]); L.new(sep.outputs["Y"], add.inputs[2])
    c1 = N.new("ShaderNodeMath"); c1.operation = "GREATER_THAN"; c1.inputs[1].default_value = front
    c2 = N.new("ShaderNodeMath"); c2.operation = "GREATER_THAN"; c2.inputs[1].default_value = front + 0.006
    L.new(add.outputs[0], c1.inputs[0]); L.new(add.outputs[0], c2.inputs[0])
    mx1 = N.new("ShaderNodeMixShader"); mx2 = N.new("ShaderNodeMixShader")
    L.new(c1.outputs[0], mx1.inputs[0]); L.new(solid.outputs[0], mx1.inputs[1]); L.new(wet.outputs[0], mx1.inputs[2])
    L.new(c2.outputs[0], mx2.inputs[0]); L.new(mx1.outputs[0], mx2.inputs[1]); L.new(tr.outputs[0], mx2.inputs[2])
    L.new(mx2.outputs[0], out.inputs["Surface"])
    obj.data.materials.clear(); obj.data.materials.append(m)


def grow_layers(obj, m_solid, frac, step=0.0016):
    """长到一半的样子（mold_kit_v4 的 grow：从 film 鼓成形）：高度压到 frac，按 1.6 mm 一层分台阶，
    边缘是硬的；最上面一层是亮的、略透明的新料（同色系浅蓝），下面是已固化的实色。"""
    import numpy as np
    me = obj.data
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    zmin = 0.0                                   # 从板面（浇口所在平面）往上下两面长
    h = np.abs(co[:, 2]) * frac
    hq = np.floor(h / step) * step + np.clip((h % step) / step * 3 - 2, 0, 1) * step   # 台阶：每层大部分是平台，台沿陡
    co[:, 2] = np.sign(co[:, 2]) * hq
    me.vertices.foreach_set("co", co.ravel()); me.update()
    top = float(hq.max())
    m = bpy.data.materials.new("cdk20_growing"); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    solid = N.new("ShaderNodeBsdfPrincipled")
    ps = m_solid.node_tree.nodes["Principled BSDF"]
    for k in ("Base Color", "Roughness", "Coat Weight", "Coat Roughness"):
        solid.inputs[k].default_value = ps.inputs[k].default_value
    wet = N.new("ShaderNodeBsdfPrincipled")
    wet.inputs["Base Color"].default_value = lin("#7A9BFF"); wet.inputs["Roughness"].default_value = 0.02
    wet.inputs["Transmission Weight"].default_value = 0.55; wet.inputs["Coat Weight"].default_value = 1.0
    wet.inputs["Emission Color"].default_value = lin("#6E90FF"); wet.inputs["Emission Strength"].default_value = 1.6
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = zmin + top - step * 2.1
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"
    L.new(sep.outputs["Z"], ab.inputs[0]); L.new(ab.outputs[0], gt.inputs[0])
    mx = N.new("ShaderNodeMixShader")
    L.new(gt.outputs[0], mx.inputs[0]); L.new(solid.outputs[0], mx.inputs[1]); L.new(wet.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    obj.data.materials.clear(); obj.data.materials.append(m)


def liver_part(m, parent, m_print, label):
    cx, cy, s = -0.06, 0.038, 0.095
    lv = smooth_loop([(x * s + cx, y * s + cy) for x, y in LIVER])
    o = slab("liver_part", lv, 0.004, m, parent, bevel=0.001)
    # 对位凸台 + 孔（拼装用）
    boss = cyl("liver_boss", (SOCKET[0], SOCKET[1], 0.0035), 0.0075, 0.003, m, parent, bevel=0.0006)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0041, depth=0.03, vertices=48, location=(SOCKET[0], SOCKET[1], 0))
    hc = bpy.context.object; hc.hide_render = hc.hide_viewport = True; hc.parent = parent
    for ob in (boss, o):
        bo = ob.modifiers.new("hole", "BOOLEAN"); bo.object = hc; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
        ob.modifiers.move(len(ob.modifiers) - 1, 0)
    if label:
        text("t_liver", "liver cancer", 0.0075, (-0.074, 0.0165, 0.00205), m_print, parent, font="InstrumentSerif-Italic.ttf")
    gate("g_liver0", (cx - 0.006, cy - 0.0285), to_bar((cx - 0.006, cy - 0.0285), "-y"), m, parent)
    gate("g_liver1", (cx - 0.0475, cy + 0.01), to_bar((cx - 0.0475, cy + 0.01), "-x"), m, parent)
    return o


def key_outline(x0, y0, L=0.05, H=0.0075):
    """真钥匙的齿形：从柄肩开始的钥匙杆，下沿是一排高低不等的齿，头部斜切。"""
    teeth = [0.0, 0.0035, 0.0012, 0.004, 0.0018, 0.0042, 0.0008, 0.003]
    pts = [(x0, y0 + H / 2), (x0 + L - 0.004, y0 + H / 2), (x0 + L, y0 + H / 2 - 0.003), (x0 + L, y0 - H / 2)]
    n = len(teeth)
    for i, t in enumerate(reversed(teeth)):
        xa = x0 + L - (i + 0.5) * (L - 0.012) / n - 0.002
        pts.append((xa + 0.0018, y0 - H / 2 - t))
        pts.append((xa - 0.0018, y0 - H / 2 - t))
    pts.append((x0 + 0.008, y0 - H / 2))
    pts.append((x0, y0 - H / 2))
    return pts


def key_part(name, m, parent, x0, y0):
    slab(name + "_blade", key_outline(x0, y0), 0.0022, m, parent, bevel=0.0004)
    # 钥匙杆上的一道纵向槽
    slab(name + "_groove", rrect(x0 + 0.026, y0 + 0.0012, 0.02, 0.0007, 0.0006), 0.0026, m, parent, bevel=0.0002)
    slab(name + "_bow", [(x0 - 0.013 + 0.012 * math.cos(math.radians(a)), y0 + 0.0095 * math.sin(math.radians(a))) for a in range(0, 360, 6)],
         0.0028, m, parent, bevel=0.0008, holes=[(x0 - 0.016, y0, 0.0035)])
    slab(name + "_shoulder", rrect(x0 + 0.0005, y0, 0.0018, 0.0055, 0.0008), 0.003, m, parent, bevel=0.0004)
    p = (x0 - 0.025, y0)
    gate(name + "_g", p, to_bar(p, "-x"), m, parent)


def sheet_parts(kind, root, m, m_ink, m_print, state):
    m_nuc = bpy.data.materials.get("nucleus") or clear_glass("nucleus", rgb=(0.8, 0.05, 0.12), density=120.0)
    if kind == "red":
        liver_part(m, root, m_print, state == "c")
        for i in range(3):                          # 肿块圆片
            cyl(f"disc_{i}", (0.03 + i * 0.03, 0.04, 0), 0.0095, 0.004, m, root, bevel=0.0012)
            gate(f"g_disc{i}", (0.03 + i * 0.03, 0.0305), (0.03 + i * 0.03, 0.0), m, root)
        for i in range(2):
            slab(f"lobe_{i}", smooth_loop([(x * 0.05 - 0.085 + i * 0.055, y * 0.05 - 0.04) for x, y in LIVER]), 0.003, m, root)
            gate(f"g_lobe{i}", (-0.085 + i * 0.055, -0.0255), (-0.085 + i * 0.055, 0.0), m, root)
        tag("tag_A1", "A1", (-0.012, HY), m, m_ink, root); tag("tag_A2", "A2", (HX - 0.014, 0.0), m, m_ink, root)
    elif kind == "blue":
        cut = state == "c"
        part, gates, _ = cdk20_part(m, root, (-0.06, 0.038), cut)
        for i, (p, b) in enumerate(gates):
            gate(f"g_cdk{i}", p, b, m, root, stub=cut)
        if state in ("a", "c"):                     # a：还没长；c：已剪走
            part.hide_render = True
            for ch in part.children:
                ch.hide_render = True
        if state == "b":                            # 正在长：从下面的浇口往上长，前沿是半透明、湿亮的未固化料
            grow_layers(bpy.data.objects["cdk20_body"], m, frac=0.62)
            bpy.data.objects["cdk20_peg"].hide_render = True
        npl = slab("plate_cdk20", rrect(0.06, 0.05, 0.03, 0.0095, 0.0025), 0.0028, m, root)
        text("t_cdk20", "CDK20", 0.011, (0.06, 0.0498, 0.0016), m_print, root)
        gate("g_np", (0.06, 0.0405), (0.06, 0.0), m, root)
        for i in range(3):
            cyl(f"bead_{i}", (0.035 + i * 0.025, 0.02, 0), 0.006, 0.004, m, root, bevel=0.0012)
            gate(f"g_bead{i}", (0.035 + i * 0.025, 0.014), (0.035 + i * 0.025, 0.0), m, root)
        for i in range(2):
            slab(f"domain_{i}", rrect(-0.085 + i * 0.05, -0.04, 0.017, 0.022, 0.009), 0.005, m, root, bevel=0.0015)
            gate(f"g_dom{i}", (-0.085 + i * 0.05, -0.018), (-0.085 + i * 0.05, 0.0), m, root)
        tag("tag_B1", "B1", (-0.012, HY), m, m_ink, root); tag("tag_B2", "B2", (HX - 0.014, 0.0), m, m_ink, root)
    elif kind == "clear":
        for i in range(3):                          # 细胞（看得见里面的核）
            x = -0.09 + i * 0.03
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.011, location=(x, 0.04, 0))
            c = bpy.context.object; c.name = f"cell_{i}"
            tx = bpy.data.textures.new(f"cl{i}", "CLOUDS"); tx.noise_scale = 0.006
            dm = c.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.0012
            bpy.ops.object.shade_smooth(); c.data.materials.append(m); c.parent = root
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035, location=(x + 0.002, 0.042, 0.001), segments=24, ring_count=12)
            nu = bpy.context.object; nu.name = f"nucleus_{i}"; bpy.ops.object.shade_smooth(); nu.data.materials.append(m_nuc); nu.parent = root
            gate(f"g_cell{i}", (x, 0.029), (x, 0.0), m, root)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(0.06, 0.04, 0), segments=64, ring_count=32)
        bw = bpy.context.object; bw.name = "pocket_bowl"; bw.scale = (1, 0.8, 0.45)
        bm = bmesh.new(); bm.from_mesh(bw.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.0001], context="VERTS"); bm.to_mesh(bw.data); bm.free()
        so = bw.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.0015
        bpy.ops.object.shade_smooth(); bw.data.materials.append(m); bw.parent = root
        gate("g_bowl", (0.038, 0.04), (0.0, 0.04), m, root)
        for i in range(3):                          # 小试管
            x = -0.09 + i * 0.03
            bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.05, vertices=48, location=(x, -0.04, 0), rotation=(math.radians(90), 0, 0))
            t = bpy.context.object; t.name = f"vial_{i}"; so = t.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.001
            bpy.ops.object.shade_smooth(); t.data.materials.append(m); t.parent = root
            gate(f"g_vial{i}", (x, -0.015), (x, 0.0), m, root)
        slab("dish", [(0.06 + 0.035 * math.cos(math.radians(a)), -0.04 + 0.03 * math.sin(math.radians(a))) for a in range(0, 360, 5)], 0.004, m, root)
        gate("g_dish", (0.06, -0.01), (0.06, 0.0), m, root)
        tag("tag_G1", "G1", (-0.012, HY), m, m_ink, root)
    elif kind == "green":
        for i, (x, y) in enumerate(((-0.06, 0.04), (0.06, 0.04), (-0.06, -0.04))):
            slab(f"bill_{i}", rrect(x, y, 0.045, 0.02, 0.002), 0.0022, m, root)
            slab(f"bill_rim{i}", rrect(x, y, 0.041, 0.016, 0.0015), 0.0028, m, root, holes=[])
            cyl(f"bill_seal{i}", (x, y, 0.0012), 0.0065, 0.0014, m, root)
            gate(f"g_bill{i}", (x - 0.045, y), to_bar((x - 0.045, y), "-x"), m, root)
            gate(f"g_billb{i}", (x + 0.045, y), to_bar((x + 0.045, y), "+x"), m, root)
        tag("tag_C1", "C1", (-0.012, HY), m, m_ink, root)
    elif kind == "white":
        slab("plate_case", rrect(-0.06, 0.04, 0.045, 0.014, 0.003), 0.003, m, root)
        text("t_case", "Case study", 0.0135, (-0.06, 0.0395, 0.0016), m_ink, root, font="InstrumentSerif-Italic.ttf")
        gate("g_case0", (-0.105, 0.04), (-HX, 0.04), m, root); gate("g_case1", (-0.015, 0.04), (0.0, 0.04), m, root)
        for i in range(4):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=(0.025 + i * 0.022, 0.04, 0), segments=32, ring_count=16)
            c = bpy.context.object; c.name = f"capsule_{i}"; c.scale = (1, 2.3, 1)
            bpy.ops.object.shade_smooth(); c.data.materials.append(m); c.parent = root
            gate(f"g_cap{i}", (0.025 + i * 0.022, 0.0285), (0.025 + i * 0.022, 0.0), m, root)
        for i in range(3):
            slab(f"washer_{i}", [(0.03 * math.cos(math.radians(a)) * 0.33 - 0.09 + i * 0.03, 0.01 * math.sin(math.radians(a)) - 0.04) for a in range(0, 360, 8)],
                 0.002, m, root, holes=[(-0.09 + i * 0.03, -0.04, 0.0035)])
            gate(f"g_w{i}", (-0.09 + i * 0.03, -0.03), (-0.09 + i * 0.03, 0.0), m, root)
        tag("tag_D1", "D1", (-0.012, HY), m, m_ink, root)
    elif kind == "black":
        for s in (1, -1):                           # 镊子两片
            slab(f"tweezer_{s}", [(-0.1, -0.04 + s * 0.0015), (-0.02, -0.04 + s * 0.006), (-0.018, -0.04 + s * 0.0035), (-0.1, -0.04 + s * 0.0005)], 0.0018, m, root)
        gate("g_tw", (-0.06, -0.036), (-0.06, 0.0), m, root)
        slab("loupe_ring", [(0.06 + 0.02 * math.cos(math.radians(a)), 0.045 + 0.02 * math.sin(math.radians(a))) for a in range(0, 360, 5)],
             0.004, m, root, holes=[(0.06, 0.045, 0.016)])
        slab("loupe_handle", rrect(0.06, 0.012, 0.004, 0.012, 0.002), 0.004, m, root)
        gate("g_loupe", (0.04, 0.045), (0.0, 0.045), m, root)
        slab("ruler", rrect(0.06, -0.04, 0.05, 0.007, 0.0015), 0.002, m, root)
        gate("g_ruler", (0.06, -0.033), (0.06, 0.0), m, root)
        tag("tag_E1", "E1", (-0.012, HY), m, m_ink, root)
    elif kind == "chrome":
        for i in range(3):
            key_part(f"key_{i}", m, root, -0.075 + (i % 2) * 0.12 if i < 2 else 0.045, 0.045 if i < 2 else -0.04)
        # 候选化合物：小球棍模型
        atoms = [(-0.07, -0.04), (-0.055, -0.03), (-0.04, -0.04), (-0.055, -0.052), (-0.085, -0.03)]
        for i, (x, y) in enumerate(atoms):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=(x, y, 0), segments=32, ring_count=16)
            a = bpy.context.object; a.name = f"atom_{i}"; bpy.ops.object.shade_smooth(); a.data.materials.append(m); a.parent = root
        for i, j in ((0, 1), (1, 2), (0, 3), (0, 4)):
            tube(f"bond_{i}{j}", [atoms[i], atoms[j]], 0.0016, m, root)
        gate("g_mol", (-0.04, -0.035), (0.0, -0.035), m, root)
        tag("tag_F1", "F1", (-0.012, HY), m, m_ink, root)


def make_sheet(kind, state, mats, M):
    col, letter, rough, metal = SHEETS[kind]
    m = mats[kind]
    root = bpy.data.objects.new("sheet_" + kind, None); link(root)
    frame(root, m, mats["ink_on_" + ("dark" if kind in ("red", "blue", "green", "black") else "light")], letter)
    sheet_parts(kind, root, m, mats["ink_on_" + ("dark" if kind in ("red", "blue", "green", "black") else "light")], mats["print_white"], state)
    root.matrix_world = M
    return root


def standing(x, y, yaw=0.0, tilt=74):
    """立起的板：绕 X 后仰，下沿贴桌。"""
    return (Matrix.Translation((x, y, HY * math.sin(math.radians(tilt)) + R_FRAME + 0.001))
            @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "X"))


def lying(x, y, z, yaw):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def build(out, state):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    r = sc.render
    r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 1080
    sc.cycles.samples = 256; sc.cycles.seed = 7
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    sc.view_settings.exposure = EXPO

    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(str(HDRI))
    N["Background"].inputs[1].default_value = 0.35
    L.new(env.outputs["Color"], N["Background"].inputs["Color"])

    mats = {k: plastic("sheet_" + k, v[0], rough=v[2], metal=v[3], coat=0.0 if v[3] else 0.6) for k, v in SHEETS.items() if k != "clear"}
    mats["clear"] = clear_glass("sheet_clear")
    sc.cycles.caustics_refractive = True; sc.cycles.caustics_reflective = True
    sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16; sc.cycles.volume_bounces = 4
    mats["ink_on_dark"] = plastic("ink_dark_bg", "#F7F4EE", rough=0.25, coat=0.2, sss=0)
    mats["ink_on_light"] = plastic("ink_light_bg", "#1F1E1C", rough=0.3, coat=0.2, sss=0)
    mats["print_white"] = mats["ink_on_dark"]
    m_bg = plastic("backdrop", "#F3EEE6", rough=0.45, coat=0.0, sss=0)

    prof = [(0, -1.5, 0)] + [(0, 0.45 + 0.35 * math.sin(math.radians(a)), 0.35 - 0.35 * math.cos(math.radians(a))) for a in range(0, 91, 5)] + [(0, 0.8, 1.5)]
    bm = bmesh.new()
    rows = [[bm.verts.new((x, p[1], p[2])) for p in prof] for x in (-2, 2)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new("sweep"); bm.to_mesh(me); bm.free()
    sw = link(bpy.data.objects.new("sweep", me))
    for p in me.polygons:
        p.use_smooth = True
    sw.data.materials.append(m_bg)

    cam_d = bpy.data.cameras.new("cam"); cam = link(bpy.data.objects.new("camera", cam_d)); sc.camera = cam
    cam_d.dof.use_dof = True

    # 一镜到底：七块板按剧本顺序连成一条长板，平放在桌上（下面有小支脚垫到同一高度），镜头沿着它推
    order = ["green", "white", "blue", "red", "clear", "black", "chrome"]
    pitch = 2 * HX + 0.012
    zb = 0.0265
    for i, k in enumerate(order):
        x = (i - 2) * pitch
        make_sheet(k, state, mats, lying(x, 0.0, zb, 0))
        if i:                                            # 板与板之间的连接杆
            for yy in (-0.04, 0.04):
                tube(f"link_{i}{yy}", [(x - pitch / 2 - 0.007, yy, zb), (x - pitch / 2 + 0.007, yy, zb)], R_BAR, mats[order[i - 1]], None)
        for fx in (-HX + 0.02, HX - 0.02):               # 支脚
            for fy in (-HY + 0.01, HY - 0.01):
                cyl("foot", (x + fx, fy, (zb - R_FRAME) / 2), 0.0028, zb - R_FRAME, mats[k], None, bevel=0.0004)
    bpy.context.view_layer.update()
    Mb = bpy.data.objects["sheet_blue"].matrix_world
    Mr = bpy.data.objects["sheet_red"].matrix_world
    if state == "c":
        # 剪下来的 CDK20 悬在肝上的对位孔正上方，销子对准孔，两件之间留 11 mm 的缝
        holder = bpy.data.objects.new("cdk20_free", None); link(holder)
        part, _, zmin = cdk20_part(mats["blue"], holder, (0, 0), True)
        holder.matrix_world = Mr @ Matrix.Translation((SOCKET[0], SOCKET[1], 0.005 - zmin + 0.011)) @ Matrix.Rotation(math.radians(12), 4, "Z")
    # 同一个机位系统：俯角 30°、从左前方顺着板看过去、50 mm；三张只是沿板推进、推近
    lens, el, az = 50, 30, -58
    if state == "a":
        tgt = Mb @ Vector((-0.17, -0.11, 0.0)); dist, fstop = 0.78, 5.6
        focus = Mb @ Vector((-0.12, 0.0, 0.0))
    elif state == "b":
        tgt = Mb @ Vector((-0.06, 0.036, 0.0)); dist, fstop = 0.21, 2.8
        focus = Mb @ Vector((-0.06, 0.038, 0.008))
    else:
        tgt = Mr @ Vector((-0.06, 0.036, 0.012)); dist, fstop = 0.33, 3.2
        focus = Mr @ Vector((SOCKET[0], SOCKET[1], 0.022))
    for name, loc, size, energy, sy in (("key", (-0.7, -0.5, 0.9), 0.9, 120, None), ("fill", (0.8, -0.6, 0.35), 0.7, 25, None),
                                        ("strip", (0.0, -0.25, 0.75), 0.6, 45, 0.12), ("rim", (0.3, 0.5, 0.6), 0.5, 30, None)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        o = bpy.context.object; o.name = name
        o.data.shape = "RECTANGLE"; o.data.size = size; o.data.size_y = sy or size; o.data.energy = energy; o.data.color = (1, 0.97, 0.93)
        o.rotation_euler = (-Vector(loc) + Vector((0, 0, 0.08))).to_track_quat("-Z", "Y").to_euler()

    # 电镀件要映出亮的东西：头顶和左前两块只给反射看的白卡（相机看不到，也不照亮漫反射）
    for nm, loc, rot, sz in (("refl_top", (0, -0.2, 1.3), (0, 0, 0), 1.6), ("refl_left", (-1.0, -0.8, 0.5), (math.radians(70), 0, math.radians(-50)), 1.2)):
        bpy.ops.mesh.primitive_plane_add(size=sz, location=loc, rotation=rot)
        rp = bpy.context.object; rp.name = nm
        em = bpy.data.materials.new(nm); em.use_nodes = True
        nt = em.node_tree; nt.nodes.clear()
        e_ = nt.nodes.new("ShaderNodeEmission"); e_.inputs["Strength"].default_value = 6.0
        o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e_.outputs[0], o_.inputs["Surface"])
        rp.data.materials.append(em)
        rp.visible_camera = False; rp.visible_diffuse = False; rp.visible_shadow = False; rp.visible_volume_scatter = False
    cam_d.lens = lens; cam_d.dof.aperture_fstop = fstop
    e, a = math.radians(el), math.radians(az)
    cam.location = tgt + Vector((dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.dof.focus_distance = (focus - cam.location).length
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("V4_BUILT", out, state)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], a[2])
