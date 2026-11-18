"""HKBU SCIE1007 课程作业的科普视频：大板样片 2-03（"And we'll answer it with one case study: CDK20 in liver cancer."），
一镜到底，5.7 秒，原生 60 fps。场景是定版大板 G:/cdk20/work/kit/board_final.blend，排位一格不动。

想法：有一股料在料杆里走，镜头被它带着走。
  流  一个鼓包沿主料杆向右滑到第 2 区的岔口，拐上支杆，分成两股从两头喂给 Case study 字牌；主料杆的岔口留下半个鼓包等着。
      字牌长满后鼓包接着走到 CDK20 的框。
  长  料从浇口沿零件漫开，漫到的地方一层层垒到零件本来的表面；前沿是亮的热料，两股料汇合处有一条很浅的熔接线，随后消失；
      长满时过冲 3% 再回落。玻璃肝是复合件，玻璃壳和红血管同时长，血管晚两帧。
  拔  先绷 3 帧（零件被往上带，浇口拉细），断开那一帧不缓动，换成短一截的残根和白色断口；
      自己那一格和周围几格跟着颤几下再静下来。零件弹起时带转动，慢慢稳住。
  讲  CDK20 拔起后自己飘着（没有定位销，下面什么也不顶着）：轻轻上下浮动，自转慢下来带一点余振；
      然后自己飞向第 1 区的玻璃肝，路上缩到能整个装进肝里，镜头跟着它往回走；等在岔口的半个鼓包同时沿主料杆往左跑去喂肝。
  变  一道波从肝的左头扫到右头，波到的地方玻璃变软发亮；先扫过 CDK20 要进去的地方，CDK20 顶下来之前已经走远。
  挤  （11-18 导演改，替换原来的"拼"）CDK20 顶到肝表面，表面被压得凹下去、越压越慢，整只肝往下让一点；CDK20 被软软推回一点，
      再用力往下挤：顶面上预留的入口（平时收成一点）张开、包着它的腰，它整个滑进透明的肝里，周围的血管被挤开；
      进去以后入口和凹陷流动着合拢，荡开一圈很浅的波纹，隔着玻璃看得见 CDK20 在肝里。
      不穿模是靠几何保证的：肝壳和血管每帧按 CDK20 的外形包络沿射线往外推（cavity()），推完一定在包络以外，
      且推的映射是一一对应的，壳和血管的里外关系不变；每帧的结果存成形状键。
  滑  镜头是一条连续的曲线（位置、距离、对焦都平滑过），全程不停死；焦点比镜头先到下一个零件；开运动模糊。

所有帧号都从 映射/keys/2-03.json 读（映射/events/2-03.json 经 resolve.py 算出），脚本里不写帧号。

    blender -b --factory-startup -P bl_s203_board.py -- build OUT.blend [采样]     搭场景、打关键帧、存盘、跑三项自检
    blender -b --factory-startup -P bl_s203_board.py -- frames IN.blend OUTDIR 0,120,300 [采样] [百分比]   抽帧预览
整段渲染：bash render_s203.sh（断点续渲）；合成出片：bash finish_s203.sh。
自检写到 OUT.check.json：穿模（逐帧 BVH，含 CDK20 对肝壳、血管，肝壳对血管）、丝滑检查表（审片/总管/动效打磨要点_v1.md 第四节）、主角在画面里的位置。
"""
import json
import math
import sys
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit_parts as KP  # noqa: E402

MM = KP.MM
KEYS = HERE.parent / "映射" / "keys" / "2-03.json"
BOARD = "G:/cdk20/work/kit/board_final.blend"

# ---- 设计参数（长度都是毫米；时间一律来自 keys）
H_CDK, H_LIVER = 20.0, 8.0    # 拔起后浮空的高度
YAW_RATE = 0.7                # 浮空自转，度每帧
LENS, FSTOP, AZ, EL = 50, 16.0, -8.0, 38.0
SHAKE = 0.5                   # 拔的一瞬间，那一格料杆弹回去的幅度
TURN = 0.62                   # 第一段鼓包：前六成时间走主料杆，到岔口
# 11-18 导演改：不要定位销；CDK20 飘起来，飞到玻璃肝上，顶一下被推回，再挤进肝里
S_IN = 0.62                   # 飞向肝的路上缩到原来的几成（肝最厚处约 28 mm，要整个装进去）
GAP = 0.6                     # 肝的表面、血管让开 CDK20 外形包络的距离
A_CAV = 2.5                   # 腔变形影响到包络半径的几倍（≥ 2 才保证推到包络以外；大一点凹得宽、软）
R_HOLE, R_CL, R_TOP = 2.0, 7.0, 18.0     # 顶面入口挖多大；入口收拢时带动多大一圈；顶面波纹的范围
TOP_COVER = 3.5               # 进去以后 CDK20 最高处上面还盖着多厚的玻璃
CLEAR, DENT, BACK = 6.0, 5.0, 3.0        # 悬在肝表面上方多高；第一次顶压下去多深；被推回多少
BOB, BOB_T = 0.9, 40.0        # 飘着时上下浮动的幅度（mm）和周期（帧）
CAM_LAND, CAM_END = 0.226, 0.204     # 镜头到肝时、句尾时离入口多远（米）：推近到看得清凹下去、挤进去


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def smoother(t):
    t = clamp(t)
    return t * t * t * (t * (6 * t - 15) + 10)


def pop(t):
    """拔：断开的一瞬间最快，过头一点，回弹一次，慢慢稳住。t 0→1，返回 0→1。"""
    t = clamp(t)
    return 1 - math.exp(-5.0 * t) * math.cos(2 * math.pi * 1.1 * t) * (1 - t) ** 2


def track(knots, n, sigma):
    """几个 (帧, 值) 连成折线，再做高斯平滑：得到每帧一个值，速度、加速度都连续，中间不停死。"""
    fs = np.array([k[0] for k in knots], float); vs = np.array([k[1] for k in knots], float)
    pad = int(4 * sigma)
    x = np.arange(-pad, n + pad)
    y = np.interp(x, fs, vs)
    lo, hi = x < fs[0], x > fs[-1]                         # 两头按最后一段的斜率接着走，免得平滑以后速度掉到 0
    y[lo] = vs[0] + (x[lo] - fs[0]) * (vs[1] - vs[0]) / (fs[1] - fs[0])
    y[hi] = vs[-1] + (x[hi] - fs[-1]) * (vs[-1] - vs[-2]) / (fs[-1] - fs[-2])
    k = np.exp(-0.5 * (np.arange(-pad, pad + 1) / sigma) ** 2); k /= k.sum()
    return np.convolve(y, k, mode="same")[pad:pad + n]


# ---------------------------------------------------------------- 零件：合成一个网格、生长、材质


def fuse(root, name, mat, voxel=None, skip=None):
    """零件的各块料合成一个网格（字留着不动）。voxel（mm）给了就重新布线成均匀小格，生长的台阶和变形要用。
    skip(o) 为真的那块料直接删掉（CDK20 的定位销）。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    gone = []
    for o in list(root.children):
        if o.type == "FONT":
            continue
        gone.append(o)
        if o.hide_render or (skip and o.type == "MESH" and skip(o)):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_local)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for o in gone:
        bpy.data.objects.remove(o)
    o = KP.link(bpy.data.objects.new(name, me), root)
    if voxel:
        r = o.modifiers.new("rm", "REMESH"); r.mode = "VOXEL"; r.voxel_size = voxel * MM; r.adaptivity = 0.0
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.clear()
        o.data = me2
        bpy.data.meshes.remove(me)
        me2.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.clear(); o.data.materials.append(mat)
    return o


def coords(o):
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def gn_grow(name, gates, amax, step, nmax, s, ctrl):
    """长：料从浇口（gates，mm）沿板面漫开，漫到的地方一层层（step mm）往上下两面垒，垒到零件本来的表面为止。
    ctrl 是一个空物体，它的 location.x 就是生长进度 T（0 → 1 + 2τ）。最上面一层半标成 fresh，材质里是亮的新料。"""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    def m(op, a, b=None, clamp_=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp_
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(N.new("GeometryNodeInputPosition").outputs[0], sep.inputs[0])
    x, y, z = sep.outputs
    dmin = d2 = None                 # 离最近、第二近的浇口多远；两个差不多远的地方就是两股料汇合的熔接线
    for gx, gy in gates:
        dx, dy = m("SUBTRACT", x, gx * MM), m("SUBTRACT", y, gy * MM)
        d = m("SQRT", m("ADD", m("MULTIPLY", dx, dx), m("MULTIPLY", dy, dy)))
        if dmin is None:
            dmin = d
        else:
            hi = m("MAXIMUM", dmin, d)
            d2 = hi if d2 is None else m("MINIMUM", d2, hi)
            dmin = m("MINIMUM", dmin, d)
    A = m("DIVIDE", dmin, amax * MM)
    weld = m("SUBTRACT", 1.0, m("DIVIDE", m("SUBTRACT", d2, dmin), 0.8 * MM), clamp_=True) if d2 is not None else None
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = ctrl; oi.transform_space = "ORIGINAL"
    st = N.new("ShaderNodeSeparateXYZ"); L.new(oi.outputs["Location"], st.inputs[0])
    T = st.outputs[0]
    tau = (1 - s) / nmax
    started = m("GREATER_THAN", T, 1e-6)
    u = m("MULTIPLY", m("MAXIMUM", m("ADD", m("DIVIDE", m("SUBTRACT", T, m("MULTIPLY", A, s)), tau), 0.7), 0.0), started)
    ramp = m("MULTIPLY", m("SUBTRACT", m("FRACT", u), 0.7), 1 / 0.3, clamp_=True)      # 每层大半时间是平台，台沿陡
    hq = m("MULTIPLY", m("ADD", m("FLOOR", u), ramp), step * MM)
    zc = m("MINIMUM", m("ABSOLUTE", z), hq)
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(x, comb.inputs[0]); L.new(y, comb.inputs[1]); L.new(m("MULTIPLY", m("SIGN", z), zc), comb.inputs[2])
    sp = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(comb.outputs[0], sp.inputs["Position"])
    fresh = m("SUBTRACT", 1.0, m("DIVIDE", m("SUBTRACT", hq, zc), 1.5 * step * MM), clamp_=True)
    sa = N.new("GeometryNodeStoreNamedAttribute"); sa.data_type = "FLOAT"; sa.domain = "POINT"
    sa.inputs["Name"].default_value = "fresh"
    L.new(sp.outputs[0], sa.inputs["Geometry"]); L.new(fresh, next(i for i in sa.inputs if i.name == "Value" and i.enabled))
    last = sa.outputs[0]
    if weld is not None:
        sw = N.new("GeometryNodeStoreNamedAttribute"); sw.data_type = "FLOAT"; sw.domain = "POINT"
        sw.inputs["Name"].default_value = "weld"
        L.new(last, sw.inputs["Geometry"]); L.new(weld, next(i for i in sw.inputs if i.name == "Value" and i.enabled))
        last = sw.outputs[0]
    dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = "POINT"
    L.new(last, dl.inputs["Geometry"]); L.new(m("LESS_THAN", hq, 1e-7), dl.inputs["Selection"])
    L.new(dl.outputs[0], go.inputs[0])
    return ng, tau


def hero_mat(name, base, fresh_hex, emit=2.5):
    """零件自己的材质：平时是 kit 的材质（实色或玻璃）；下面三种时候混成亮的、湿的热料：
    fresh 属性（生长前沿）、soft 属性或 soft 数值（变形的那道波、整件变软）、weld 属性 × weld 数值（刚汇合的熔接线，很浅，随后消失）。"""
    mt = base.copy(); mt.name = name
    N, L = mt.node_tree.nodes, mt.node_tree.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    w = N.new("ShaderNodeBsdfPrincipled")
    w.inputs["Base Color"].default_value = KP.lin(fresh_hex)
    w.inputs["Roughness"].default_value = 0.03
    w.inputs["Coat Weight"].default_value = 1.0
    w.inputs["Coat Roughness"].default_value = 0.02
    w.inputs["Emission Color"].default_value = KP.lin(fresh_hex)
    w.inputs["Emission Strength"].default_value = emit

    def mx(a, b, op="MAXIMUM"):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = True
        L.new(a, n.inputs[0]); L.new(b, n.inputs[1])
        return n.outputs[0]

    def attr(k):
        n = N.new("ShaderNodeAttribute"); n.attribute_name = k
        return n.outputs["Fac"]

    def val(k):
        n = N.new("ShaderNodeValue"); n.name = k; n.outputs[0].default_value = 0.0
        return n.outputs[0]

    fac = mx(mx(attr("fresh"), mx(attr("soft"), val("soft"))), mx(attr("weld"), val("weld"), "MULTIPLY"))
    mix = N.new("ShaderNodeMixShader")
    L.new(fac, mix.inputs[0]); L.new(src, mix.inputs[1]); L.new(w.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return mt


def ink_reveal(base, cx_world, half):
    """字牌上的字：最上一层料从两头漫到哪，字就印到哪。reveal（mm）是从两头往里已经漫到的距离，按帧打关键帧。"""
    mt = base.copy(); mt.name = "ink_reveal"
    N, L = mt.node_tree.nodes, mt.node_tree.links
    p = N["Principled BSDF"]
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    dx = N.new("ShaderNodeMath"); dx.operation = "SUBTRACT"; L.new(sep.outputs[0], dx.inputs[0]); dx.inputs[1].default_value = cx_world
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(dx.outputs[0], ab.inputs[0])
    fe = N.new("ShaderNodeMath"); fe.operation = "SUBTRACT"; fe.inputs[0].default_value = half * MM; L.new(ab.outputs[0], fe.inputs[1])
    rv = N.new("ShaderNodeValue"); rv.name = "reveal"; rv.outputs[0].default_value = 0.0
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; L.new(fe.outputs[0], lt.inputs[0]); L.new(rv.outputs[0], lt.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(lt.outputs[0], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(p.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return mt


def add_grow(o, gates, step, s, name):
    co = coords(o) / MM
    g = np.array([(gx, gy) for gx, gy, _, _ in gates])
    d = np.sqrt(((co[:, None, :2] - g[None]) ** 2).sum(-1)).min(1)
    amax = float(d.max())
    nmax = int(math.ceil(float(np.abs(co[:, 2]).max()) / step))
    ctrl = KP.link(bpy.data.objects.new(name + "_T", None))
    ng, tau = gn_grow(name, [tuple(x) for x in g], amax, step, nmax, s, ctrl)
    md = o.modifiers.new("grow", "NODES"); md.node_group = ng
    return dict(ctrl=ctrl, tau=tau, t_end=1 + 2 * tau, amax=amax, s=s, nmax=nmax)


# ---------------------------------------------------------------- 浇口：断开后的残根、白色断口


def gate_ends(cone):
    """浇口锥在格子坐标里的两头：a 是料杆一侧，b 是零件一侧的尖。"""
    zs = [v.co.z for v in cone.data.vertices]
    axis = cone.matrix_local.to_3x3() @ Vector((0, 0, 1))
    c = cone.matrix_local.translation
    return c + axis * min(zs), c + axis * max(zs)


def break_gates(cell, part, white, f_break):
    """拔的那一帧：完整的浇口锥换成短一截的残根（短到零件往上走时不会刮到），残根头上和零件上各留一个白色断口。
    残根退多少由零件几何算：零件在浇口平面以下、正对浇口的那一条里，朝浇口方向鼓出去最远的地方再让 0.5 mm。"""
    co = coords(part) / MM
    bvh = BVHTree.FromPolygons([tuple(v) for v in coords(part)], [tuple(p.vertices) for p in part.data.polygons])
    out = []
    for cone in [o for o in cell.children if o.name.startswith(cell.name + "_g") and not o.name.endswith("_spur")]:
        a, b = gate_ends(cone)
        d = (a - b).normalized()
        n2 = np.array([-d.y, d.x])
        rel = co[:, :2] - np.array([b.x, b.y]) / MM
        near = (np.abs(rel @ n2) < 1.6) & (co[:, 2] < b.z / MM + 1.4)
        over = float((rel[near] @ np.array([d.x, d.y])).max()) if near.any() else 0.0
        depth = (a - b).length / MM
        cut = min(max(0.9, over + 0.5), depth - 0.4)
        b2 = b + d * cut * MM
        r2 = 0.45 + (1.2 - 0.45) * cut / depth
        bpy.ops.mesh.primitive_cone_add(radius1=1.2 * MM, radius2=r2 * MM, depth=(a - b2).length, vertices=20, location=(a + b2) / 2)
        st = bpy.context.object; st.name = cone.name + "_stub"
        st.rotation_euler = (b2 - a).to_track_quat("Z", "Y").to_euler()
        bpy.ops.object.shade_smooth(); st.data.materials.append(cone.data.materials[0]); st.parent = cell
        bpy.ops.mesh.primitive_uv_sphere_add(radius=(r2 + 0.06) * MM, segments=16, ring_count=8, location=b2 - d * 0.05 * MM)
        s1 = bpy.context.object; s1.name = cone.name + "_scar"; bpy.ops.object.shade_smooth()
        s1.data.materials.append(white); s1.parent = cell
        s1.scale = (1, 1, 1)
        hit = bvh.find_nearest(b)[0]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55 * MM, segments=16, ring_count=8, location=hit)
        s2 = bpy.context.object; s2.name = cone.name + "_scar_part"; bpy.ops.object.shade_smooth()
        s2.data.materials.append(white); s2.parent = part
        for o, before in ((cone, False), (st, True), (s1, True), (s2, True)):
            o.hide_render = o.hide_viewport = before
            o.keyframe_insert("hide_render", frame=f_break - 1); o.keyframe_insert("hide_viewport", frame=f_break - 1)
            o.hide_render = o.hide_viewport = not before
            o.keyframe_insert("hide_render", frame=f_break); o.keyframe_insert("hide_viewport", frame=f_break)
        out.append(dict(gate=cone.name, cut_mm=round(cut, 2), overhang_mm=round(over, 2)))
    return out


# ---------------------------------------------------------------- 变的那道波、料杆里的鼓包


def gn_wave(name, ctrl, amp, sigma):
    """变：一道波沿 x 扫过去。ctrl 的 location.x 是波峰的位置（米，零件坐标）。波到的地方表面沿法线鼓起 amp mm，
    并把 soft 属性写成 0–1，材质里这一带是软的、亮的热料；波过去就恢复。"""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(N.new("GeometryNodeInputPosition").outputs[0], sep.inputs[0])
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = ctrl; oi.transform_space = "ORIGINAL"
    st = N.new("ShaderNodeSeparateXYZ"); L.new(oi.outputs["Location"], st.inputs[0])

    def m(op, a, b=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    q = m("DIVIDE", m("SUBTRACT", sep.outputs[0], st.outputs[0]), sigma * MM)
    g = m("EXPONENT", m("MULTIPLY", m("MULTIPLY", q, q), -1.0))
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"
    L.new(N.new("GeometryNodeInputNormal").outputs[0], sc_.inputs[0]); L.new(m("MULTIPLY", g, amp * MM), sc_.inputs["Scale"])
    sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(sc_.outputs[0], sp.inputs["Offset"])
    sa = N.new("GeometryNodeStoreNamedAttribute"); sa.data_type = "FLOAT"; sa.domain = "POINT"
    sa.inputs["Name"].default_value = "soft"
    L.new(sp.outputs[0], sa.inputs["Geometry"]); L.new(g, next(i for i in sa.inputs if i.name == "Value" and i.enabled))
    L.new(sa.outputs[0], go.inputs[0])
    return ng


class Path2:
    """料杆上的一条路：[(x, y, 料杆半径), …]，毫米，板面坐标。at(u) 给出走到 u（0–1，按路程）时的位置、方向、半径。"""
    def __init__(self, pts):
        self.p = np.array(pts, float)
        d = np.hypot(*np.diff(self.p[:, :2], axis=0).T)
        self.s = np.concatenate([[0], np.cumsum(d)])

    def at(self, u):
        s = clamp(u) * self.s[-1]
        i = int(min(max(np.searchsorted(self.s, s, side="right") - 1, 0), len(self.p) - 2))
        t = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i])
        a, b = self.p[i], self.p[i + 1]
        # 方向取前后各 2.5 mm 的连线，拐弯时鼓包是转过去的，不是跳过去的
        s0, s1 = max(0, s - 2.5), min(self.s[-1], s + 2.5)
        q0 = [np.interp(s0, self.s, self.p[:, k]) for k in (0, 1)]; q1 = [np.interp(s1, self.s, self.p[:, k]) for k in (0, 1)]
        return lerp(a[0], b[0], t), lerp(a[1], b[1], t), math.atan2(q1[1] - q0[1], q1[0] - q0[0]), lerp(a[2], b[2], t)

    def u_of(self, k):
        return self.s[k] / self.s[-1]


def half_loop(cx, cy, side, frm, to):
    """沿一格的外圈走：frm、to 取 'b'（下边中点）、's'（侧边中点）、't'（上边中点）；side = +1 走右半圈，−1 走左半圈。"""
    r, R = KP.CX, KP.R_LOOP
    ring = [("b", (cx, cy - KP.CY)), (None, (cx + side * (r - 5), cy - KP.CY)), (None, (cx + side * r, cy - KP.CY + 5)),
            ("s", (cx + side * r, cy)), (None, (cx + side * r, cy + KP.CY - 5)), (None, (cx + side * (r - 5), cy + KP.CY)), ("t", (cx, cy + KP.CY))]
    names = [n for n, _ in ring]
    i, j = names.index(frm), names.index(to)
    seq = ring[i:j + 1] if i <= j else ring[j:i + 1][::-1]
    return [(p[0], p[1], R) for _, p in seq]


def make_pulse(name, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=MM, segments=32, ring_count=16)
    o = bpy.context.object; o.name = name; bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    o.scale = (0, 0, 0)
    return o


# ---------------------------------------------------------------- 挤进肝：外形包络、选入口、开口、合拢、腔变形


def smoothv(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Envelope:
    """CDK20 的外形包络：从零件中心往每个方向，最远的表面点多远（毫米，零件自己的坐标，未缩放）。
    每个方向取 12° 锥里所有顶点的最远距离，比真外形略大一圈，三角面也包在里面。查表时双线性插值。"""
    def __init__(self, co, nt=91, nph=180, alpha=12.0):
        r = np.linalg.norm(co, axis=1)
        u = co / r[:, None]
        th = np.linspace(0, math.pi, nt)
        ph = np.linspace(0, 2 * math.pi, nph, endpoint=False)
        T, P = np.meshgrid(th, ph, indexing="ij")
        G = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], -1).reshape(-1, 3)
        ca = math.cos(math.radians(alpha))
        rho = np.zeros(len(G))
        for i in range(0, len(G), 256):
            d = G[i:i + 256] @ u.T
            rho[i:i + 256] = np.where(d > ca, r[None, :], 0.0).max(1)
        self.tab = rho.reshape(nt, nph)
        self.nt, self.nph = nt, nph

    def __call__(self, d):
        d = d / np.linalg.norm(d, axis=1)[:, None]
        th = np.arccos(np.clip(d[:, 2], -1, 1)) / math.pi * (self.nt - 1)
        ph = (np.arctan2(d[:, 1], d[:, 0]) % (2 * math.pi)) / (2 * math.pi) * self.nph
        i0 = np.clip(np.floor(th).astype(int), 0, self.nt - 2); ft = th - i0
        j0 = np.floor(ph).astype(int) % self.nph; fp = ph - np.floor(ph); j1 = (j0 + 1) % self.nph
        t = self.tab
        return t[i0, j0] * (1 - ft) * (1 - fp) + t[i0 + 1, j0] * ft * (1 - fp) + t[i0, j1] * (1 - ft) * fp + t[i0 + 1, j1] * ft * fp


def cavity(P, c, R, s, env):
    """CDK20 在肝里撑出的腔：以它的中心为原点，沿每条射线把点往外推，推到包络（乘缩放、加 GAP）以外，
    离得越远推得越少，到包络半径的 A_CAV 倍处为零。r' = r + ρ(1 − r/(aρ))²，a ≥ 2 时 r' ≥ ρ 且沿射线单调，
    所以：肝的壳和血管都不会进到 CDK20 里（不穿模）；不同射线上的点不会挤到一起，壳和血管的里外关系不变。"""
    d = P - c
    r = np.linalg.norm(d, axis=1)
    sel = r < A_CAV * (s * float(env.tab.max()) + GAP)
    out = P.copy()
    if sel.any():
        rr = r[sel]
        u = d[sel] / rr[:, None]
        rho = s * env(u @ R) + GAP                                  # u @ R：世界方向转回 CDK20 自己的方向（R 的转置）
        k = np.clip(1 - rr / (A_CAV * rho), 0, None)
        out[sel] = c + u * (rr + rho * k * k)[:, None]
    return out


def closure(P, mask, Ex, Ey, r_h, z_c, m):
    """肝顶面入口：m = 1 时开口的一圈收成一点（看不出有口），m = 0 时是原来的开口。只动顶面入口附近（mask）。"""
    Q = P.copy()
    if m <= 0:
        return Q
    dx, dy = P[:, 0] - Ex, P[:, 1] - Ey
    rl = np.hypot(dx, dy)
    w = np.where(rl <= r_h, 1.0, 1 - smoothv((rl - r_h) / (R_CL - r_h))) * mask
    r2 = np.sqrt(np.maximum(0.0, rl ** 2 - m * r_h ** 2 * w))      # 沿半径单调：收拢不会让面折叠
    k = np.where(rl > 1e-9, r2 / np.maximum(rl, 1e-9), 0.0)
    Q[:, 0] = Ex + dx * k
    Q[:, 1] = Ey + dy * k
    wz = m * (1 - smoothv((rl - r_h) / 2.0)) * mask                # 口沿那一圈高度拉平，收成一点时不起棱
    Q[:, 2] = P[:, 2] + wz * (z_c - P[:, 2])
    return Q


def _bvh_part(P, o):
    return BVHTree.FromPolygons([tuple(v) for v in P], [tuple(p.vertices) for p in o.data.polygons])


def _hits(bvh, x, y, down=True):
    """沿竖线打穿，返回所有交点的 z（从上往下或从下往上排）。"""
    out = []
    o = Vector((x, y, 300.0 if down else -300.0))
    d = Vector((0, 0, -1.0 if down else 1.0))
    for _ in range(20):
        h = bvh.ray_cast(o, d)
        if h[0] is None:
            break
        out.append(h[0].z)
        o = h[0] + d * 0.01
    return out


def choose_entry(P_sh, shell, P_vs, vessel, sx, sy, r_up, r_dn, r_max):
    """在原定位孔附近找 CDK20 挤进去的地方：整个包络（缩小后）放进肝里，上面盖着至少 TOP_COVER 的玻璃、下面留 3 mm；
    中心往下走的那条竖线（和旁边 0.8 mm 的四条）上不能有血管（中心要是穿过血管，血管就会被捅穿）。
    满足的里面挑肝最厚的，离原定位孔近一点的优先。"""
    bs, bv = _bvh_part(P_sh, shell), _bvh_part(P_vs, vessel)
    best = None
    for gx in np.arange(-10, 10.1, 2.0):
        for gy in np.arange(-10, 10.1, 2.0):
            x, y = sx + gx, sy + gy
            top, bot = _hits(bs, x, y), _hits(bs, x, y, down=False)
            if not top or not bot:
                continue
            zt, zb_ = top[0], bot[0]
            c_fin = zt - TOP_COVER - r_up
            if c_fin - r_dn < zb_ + 3.0:
                continue
            thin = []
            for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
                for rr in (0.5 * r_max, 0.95 * r_max):
                    t2, b2 = _hits(bs, x + rr * math.cos(a), y + rr * math.sin(a)), _hits(bs, x + rr * math.cos(a), y + rr * math.sin(a), down=False)
                    thin.append((t2[0] - b2[0]) if t2 and b2 else 0.0)
            ok = True
            for ox, oy in ((0, 0), (0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8)):
                hv = [z for z in _hits(bv, x + ox, y + oy) if c_fin - 1.0 < z < zt]
                if hv:
                    ok = False
                    break
            if not ok:
                continue
            score = min(thin) - 0.3 * math.hypot(gx, gy)
            if best is None or score > best[0]:
                best = (score, dict(x=round(float(x), 2), y=round(float(y), 2), z_top=round(float(zt), 2), z_bottom=round(float(zb_), 2),
                                    c_final=round(float(c_fin), 2), min_thick=round(float(min(thin)), 2)))
    assert best is not None, "原定位孔附近找不到能把 CDK20 整个装进去、又不捅穿血管的地方"
    return best[1]


def refine(o, M_, Ex, Ey, rad, lmax):
    """入口附近（离入口竖线 rad 以内）的长边对半切，直到都短于 lmax（毫米）。挤的时候网格被撑开好几倍，
    长三角形会从 CDK20 的包络上横着切过去；切短以后每条边撑开后还贴着包络。只加点，不改形状。"""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    A = M_[:3, :3] / MM; b = M_[:3, 3] / MM
    n0 = len(bm.verts)
    for _ in range(8):
        long_ = []
        for e in bm.edges:
            p0, p1 = A @ np.array(e.verts[0].co) + b, A @ np.array(e.verts[1].co) + b
            if np.linalg.norm(p1 - p0) > lmax and math.hypot((p0[0] + p1[0]) / 2 - Ex, (p0[1] + p1[1]) / 2 - Ey) < rad:
                long_.append(e)
        if not long_:
            break
        r = bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return dict(verts_before=n0, verts_after=len(me.vertices), left_long=len(long_))


def cut_entry(shell, Ms, Ex, Ey, z_top):
    """在肝顶面入口处挖一个 R_HOLE 的小口（只挖顶面一层）。平时由 closure() 收成一点，挤的时候张开包住 CDK20 的腰。"""
    me = shell.data
    bm = bmesh.new(); bm.from_mesh(me)
    A = Ms[:3, :3] / MM; b = Ms[:3, 3] / MM
    part = lambda v: A @ np.array(v.co) + b                         # noqa: E731
    gone = []
    for fc in bm.faces:
        p = A @ np.array(fc.calc_center_median()) + b
        if math.hypot(p[0] - Ex, p[1] - Ey) < R_HOLE and p[2] > z_top - 3.0:
            gone.append(fc)
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    rim = [part(v) for v in bm.verts if v.is_boundary]
    rim = [p for p in rim if math.hypot(p[0] - Ex, p[1] - Ey) < R_HOLE + 2.0]
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    rl = [math.hypot(p[0] - Ex, p[1] - Ey) for p in rim]
    assert rim and len(gone) > 0, "入口没挖出来"
    return dict(faces=len(gone), rim_verts=len(rim), r_h=round(max(rl), 3), r_min=round(min(rl), 3), z_rim=round(float(np.mean([p[2] for p in rim])), 3))


# ---------------------------------------------------------------- 搭场景、打关键帧


def find_cells():
    """按内容找格子，不写死格子名（kit_README.md）。"""
    cells = [o for o in bpy.data.objects["board"].children if o.name.startswith("z") and "_c" in o.name]

    def pick(pred):
        return next(c for c in cells if pred(c, KP.part_of(c)))
    return dict(plate=pick(lambda c, p: c.name.startswith("z2_") and any(ch.type == "FONT" and ch.data.body == "Case study" for ch in p.children)),
                cdk=pick(lambda c, p: c.name.startswith("z3_") and p.name.startswith("p19_cdk20")),
                liver=pick(lambda c, p: "span" in p.keys())), cells


def bake_mesh(o, subdiv=0):
    """把修改器（布尔孔）算进网格；subdiv 次对半细分，生长的台阶才不会跟着粗三角形走。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    old = o.data; o.data = me; bpy.data.meshes.remove(old)
    if subdiv:
        bm = bmesh.new(); bm.from_mesh(me)
        for _ in range(subdiv):
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
        bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return o


def build(out_blend, samples=64):
    t0 = time.time()
    Kd = json.loads(KEYS.read_text(encoding="utf-8"))
    EV = {e["id"]: e for e in Kd["events"]}
    NF = Kd["len_f"]
    S0, S1 = Kd["sentences"][0]["f0"], Kd["sentences"][-1]["f1"]
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_"):
            bpy.data.objects.remove(o)
    sc.render.fps, sc.render.fps_base = 60, 1.0
    sc.frame_start, sc.frame_end = 0, NF - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.cycles.samples = samples; sc.cycles.seed = 7; sc.cycles.use_animated_seed = False      # 固定采样种子
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.max_bounces = 12; sc.cycles.transmission_bounces = 12; sc.cycles.glossy_bounces = 6
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    M = bpy.data.materials
    cell, all_cells = find_cells()
    c_k = cell["cdk"].matrix_world.translation
    legs = [o for o in bpy.data.objects["board"].children if o.name.startswith("foot") and (o.matrix_world.translation.xy - c_k.xy).length < 45 * MM]
    for o in legs:                                             # 11-18：CDK20 那一格后面的一根板脚，从空格里看过去像一根柱子把 CDK20 顶起来，这一镜去掉
        bpy.data.objects.remove(o)
    print("S203 去掉板脚", len(legs))
    zb = bpy.data.objects["board"].location.z / MM
    cx = {k: c.matrix_world.translation.x / MM for k, c in cell.items()}
    cy = {k: c.matrix_world.translation.y / MM for k, c in cell.items()}
    print("S203 cells", {k: (c.name, round(cx[k], 1), round(cy[k], 1)) for k, c in cell.items()})

    # ---- 三件主角
    r_pl, r_ck, r_lv = (KP.part_of(cell[k]) for k in ("plate", "cdk", "liver"))
    g_pl, g_ck, g_lv = (json.loads(r["gates"]) for r in (r_pl, r_ck, r_lv))
    m_pl = hero_mat("hero_white", M["kit_white"], "#FFF6DC", emit=1.3)
    m_ck = hero_mat("hero_blue", M["kit_blue"], "#7A9BFF", emit=2.2)
    m_gl = hero_mat("hero_glass", M["kit_organ_glass"], "#FF8A8A", emit=1.6)
    m_vs = hero_mat("hero_vessel", M["kit_red"], "#FF6A70", emit=1.8)
    plate = fuse(r_pl, "hero_plate", m_pl, voxel=0.2)
    # 11-18 导演改：CDK20 不要定位销（那根细圆柱），拔起来以后是自己飘着的
    cdk = fuse(r_ck, "hero_cdk20", m_ck, skip=lambda o: len(o.data.vertices) < 1000)
    txt = next(o for o in r_pl.children if o.type == "FONT")
    half_pl = float(np.abs(coords(plate)[:, 0]).max()) / MM
    txt.data.materials.clear(); txt.data.materials.append(ink_reveal(M["kit_ink_dark"], cell["plate"].matrix_world.translation.x, half_pl))
    kids = [o for o in r_lv.children if o.type == "MESH" and not o.hide_render]
    shell = next(o for o in kids if o.data.materials[0].name.startswith("kit_organ_glass") and len(o.data.vertices) > 5000)
    vessel = next(o for o in kids if o.data.materials[0].name.startswith("kit_red"))
    ring = next(o for o in kids if o not in (shell, vessel))
    bpy.data.objects.remove(ring)                                  # 凸台是给定位销的，销没了，凸台也不要
    for md in [md for md in shell.modifiers if md.type == "BOOLEAN"]:
        shell.modifiers.remove(md)                                 # 定位孔原来上下打穿；不要它，入口自己在顶面开
    bake_mesh(shell, subdiv=1)
    shell.name = "hero_liver_shell"; vessel.name = "hero_liver_vessel"
    shell.data.materials.clear(); shell.data.materials.append(m_gl)
    vessel.data.materials.clear(); vessel.data.materials.append(m_vs)
    sx, sy = (float(v) for v in r_lv["socket"][:2])

    # ---- 挤进肝：CDK20 的外形包络、入口位置、肝顶面上的入口（平时合拢成一点）
    cc = coords(cdk) / MM
    env = Envelope(cc)
    rho_dn, rho_up = (float(env(np.array([[0, 0, k]]))[0]) for k in (-1.0, 1.0))
    Ms, Mv = np.array(shell.matrix_local), np.array(vessel.matrix_local)
    to_part = lambda o, M_: (coords(o) / MM) @ M_[:3, :3].T + M_[:3, 3] / MM      # noqa: E731  物体坐标（米）→ 肝零件坐标（毫米）
    P_sh, P_vs = to_part(shell, Ms), to_part(vessel, Mv)
    ent = choose_entry(P_sh, shell, P_vs, vessel, sx, sy, S_IN * rho_up + GAP, S_IN * rho_dn + GAP, S_IN * float(env.tab.max()) + GAP)
    Ex, Ey, z_top, c_fin = ent["x"], ent["y"], ent["z_top"], ent["c_final"]
    hole = cut_entry(shell, Ms, Ex, Ey, z_top)
    rf = dict(shell=refine(shell, Ms, Ex, Ey, 34.0, 0.5), vessel=refine(vessel, Mv, Ex, Ey, 34.0, 0.4))
    P_vs = to_part(vessel, Mv)
    P_sh = to_part(shell, Ms)
    top_mask = (np.hypot(P_sh[:, 0] - Ex, P_sh[:, 1] - Ey) < R_TOP) & (P_sh[:, 2] > z_top - 4.0)
    print(f"S203 entry: CDK20 包络 下 {rho_dn:.2f} 上 {rho_up:.2f} 最大 {env.tab.max():.2f} mm（未缩放）; 入口 {ent}; 开口 {hole}; 加密 {rf}")

    G = dict(plate=add_grow(plate, g_pl, 0.7, 0.62, "grow_plate"),
             cdk=add_grow(cdk, g_ck, 1.6, 0.62, "grow_cdk20"),
             shell=add_grow(shell, g_lv, 2.6, 0.62, "grow_liver_shell"),
             vessel=add_grow(vessel, g_lv, 2.6, 0.62, "grow_liver_vessel"))
    wave_c = KP.link(bpy.data.objects.new("wave_x", None)); wave_c.location.x = 1.0
    wm = shell.modifiers.new("wave", "NODES"); wm.node_group = gn_wave("liver_wave", wave_c, 1.3, 7.0)
    print(f"S203 geometry: cdk verts {len(cc)} z {cc[:, 2].min():.2f}..{cc[:, 2].max():.2f}; shell verts {len(shell.data.vertices)} vessel {len(vessel.data.vertices)}; "
          f"socket ({sx:.1f}, {sy:.1f}); plate verts {len(plate.data.vertices)}")
    print("S203 grow", {k: {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "ctrl"} for k, v in G.items()})

    # ---- 拔：浇口残根和白色断口；预备时浇口被拉细
    e_ej, e_fly, e_pr, e_in, e_cl = EV["cdk_eject"], EV["cdk_fly"], EV["cdk_press"], EV["cdk_enter"], EV["liver_close"]
    l_ej, l_mo = EV["liver_eject"], EV["liver_morph"]
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    brk = dict(cdk=break_gates(cell["cdk"], cdk, scar, e_ej["f_land"]), liver=break_gates(cell["liver"], shell, scar, l_ej["f_land"]))
    print("S203 gates", brk)
    for k, e in (("cdk", e_ej), ("liver", l_ej)):
        for cone in [o for o in cell[k].children if o.name.startswith(cell[k].name + "_g") and not o.name.endswith(("_spur", "_stub", "_scar"))]:
            cone.scale = (1, 1, 1); cone.keyframe_insert("scale", frame=e["f_start"])
            cone.scale = (0.5, 0.5, 1.04); cone.keyframe_insert("scale", frame=e["f_land"] - 1)

    # ---- 路径：从零件几何算（肝零件坐标，毫米）
    rd = S_IN * rho_dn + GAP                                       # 缩小后，CDK20 中心到最低处（含让开的距离）
    c_touch = z_top + rd                                           # CDK20 最低处刚碰到肝顶面时，中心的高度
    c_app = c_touch + CLEAR                                        # 飞到时悬在这里
    z_rim = float(hole["z_rim"])
    print(f"S203 path: 碰到 {c_touch:.2f} 悬停 {c_app:.2f} 第一次压到 {c_touch - DENT:.2f} 推回到 {c_touch - DENT + BACK:.2f} 最后 {c_fin:.2f}（肝顶面 {z_top:.2f}）")

    def spring(t):
        """从静止出发、过冲一点再停稳的 0→1。"""
        t = clamp(t)
        w = 2 * math.pi * 0.85
        return 1 - math.exp(-4.5 * t) * (math.cos(w * t) + 4.5 / w * math.sin(w * t))

    def cz(f):
        """CDK20 中心在肝零件坐标里的高度（入口那条竖线上）。"""
        if f <= e_pr["f_start"]:
            return c_app
        if f <= e_pr["f_land"]:                                    # 顶：越压越慢，阻力
            t = (f - e_pr["f_start"]) / (e_pr["f_land"] - e_pr["f_start"])
            return c_app - (CLEAR + DENT) * (1 - (1 - t) ** 2.4)
        z1 = c_touch - DENT + BACK
        if f <= e_in["f_start"]:                                   # 被软软推回
            t = (f - e_pr["f_land"]) / (e_in["f_start"] - e_pr["f_land"])
            return c_touch - DENT + BACK * spring(t)
        if f <= e_in["f_land"]:                                    # 再用力挤：先往上一缩，然后越来越快地滑进去，最后收住
            t = (f - e_in["f_start"]) / (e_in["f_land"] - e_in["f_start"])
            a = 0.9 * math.sin(math.pi * min(t / 0.22, 1.0)) ** 2 if t < 0.22 else 0.0
            u = clamp((t - 0.1) / 0.9)
            return z1 + a - (z1 - c_fin) * smoother(u ** 1.35)
        t = (f - e_in["f_land"]) / max(1, e_in["f_end"] - e_in["f_land"])
        return c_fin - 0.8 * math.sin(math.pi * clamp(t)) * (1 - clamp(t)) ** 0.5       # 到底一沉再回位

    def press(f):
        """肝被顶的程度（毫米）：第一次顶的时候按 CDK20 压下去多深，挤进去以后慢慢放掉。"""
        if f <= e_in["f_start"]:
            return max(0.0, c_touch - cz(f))
        return max(0.0, c_touch - cz(e_in["f_start"])) * (1 - smooth((f - e_in["f_start"]) / 10.0))

    def sink(f):
        """整只肝被顶得往下让一点；挤进去那一下再沉一下、回位。"""
        s = -0.22 * press(f)
        if e_in["f_start"] < f:
            t = (f - e_in["f_start"]) / (e_in["f_end"] + 4 - e_in["f_start"])
            s -= 1.1 * math.sin(math.pi * clamp(t)) ** 2 * (1 - clamp(t))
        return s

    def shake(f, e, k=1.0, lag=0):
        """拔的前后，那一格料杆的上下：先被零件带起来一点，断开的一帧弹回去，颤几下静下来。"""
        t = f - lag - e["f_land"]
        if t < 0:
            return k * 0.35 * clamp(1 + t / max(1, e["f_land"] - e["f_start"])) ** 2 if lag == 0 else 0.0
        D = e["f_end"] - e["f_land"]
        return -k * SHAKE * math.exp(-t / 5.0) * math.cos(2 * math.pi * t / 7.5) * (1 - smooth((t - (D - 5)) / 5))

    yaw_acc = [0.0]
    for f in range(NF):
        r = 0.0
        if f > e_ej["f_land"]:
            r = YAW_RATE * (1 + 3.0 * math.exp(-(f - e_ej["f_land"]) / 9.0)) * (1 - smoother((f - e_fly["f_start"]) / (e_in["f_land"] - e_fly["f_start"])))
        yaw_acc.append(yaw_acc[-1] + r)

    def liver_z(f):
        if f < l_ej["f_start"]:
            return 0.0
        if f < l_ej["f_land"]:
            return 0.5 * ((f - l_ej["f_start"] + 1) / (l_ej["f_land"] - l_ej["f_start"])) ** 2
        return H_LIVER * pop((f - l_ej["f_land"]) / (l_ej["f_end"] - l_ej["f_land"])) + sink(f)

    def bob(f):
        """飘着：轻轻上下浮动。"""
        t = f - e_ej["f_land"] - 6
        return BOB * math.sin(2 * math.pi * t / BOB_T) * smooth(t / 16.0) if t > 0 else 0.0

    liver0 = (cx["liver"], cy["liver"], zb)

    def cdk_world(f):
        """CDK20 中心的世界坐标（毫米）和姿态：(x, y, z, 低头, 侧倾, 自转, 缩放)。"""
        ox, oy = cx["cdk"], cy["cdk"]
        yaw = yaw_acc[f]
        if f < e_ej["f_start"]:
            return ox, oy, zb, 0.0, 0.0, 0.0, 1.0
        if f < e_ej["f_land"]:                                     # 预备：往上绷
            return ox, oy, zb + 0.7 * ((f - e_ej["f_start"] + 1) / (e_ej["f_land"] - e_ej["f_start"])) ** 2, 0.0, 0.0, 0.0, 1.0
        D = e_ej["f_end"] - e_ej["f_land"]
        t = (f - e_ej["f_land"]) / D
        z = zb + H_CDK * pop(t) + bob(f)
        tilt = 13.0 * smooth(t)                                    # 浮起来以后朝镜头低一点头
        roll = 7.0 * math.exp(-4.0 * t) * math.sin(2 * math.pi * 1.6 * t)       # 弹起时带的晃
        yaw += 6.0 * math.exp(-(f - e_ej["f_land"]) / 16.0) * math.sin(2 * math.pi * (f - e_ej["f_land"]) / 23.0)   # 自转的余振
        x, y, s = ox, oy, 1.0
        if f > e_fly["f_start"]:
            t = clamp((f - e_fly["f_start"]) / (e_fly["f_land"] - e_fly["f_start"]))
            lz = lerp(H_LIVER, liver_z(f), smooth((t - 0.6) / 0.4))
            ax, ay, az = liver0[0] + Ex, liver0[1] + Ey, zb + lz + c_app
            x, y = lerp(ox, ax, smoother(t)), lerp(oy, ay, smoother(t))
            z = lerp(z, az, smooth(t / 0.38))                      # 先升够高，越过板上所有东西，再平移到入口上方
            tilt *= 1 - smooth((t - 0.3) / 0.6)
            roll += 9.0 * math.sin(2 * math.pi * t) * (1 - t) ** 0.5     # 起步身子往后仰，刹车往前倾
            s = lerp(1.0, S_IN, smoother(t))
        if f > e_fly["f_land"]:                                    # 到了以后跟着肝走（肝坐标里沿入口竖线上下）
            x, y, z = liver0[0] + Ex, liver0[1] + Ey, zb + liver_z(f) + cz(f)
            tilt = 0.0
            roll = 2.5 * math.sin(math.pi * clamp((f - e_pr["f_start"]) / (e_in["f_start"] - e_pr["f_start"]))) * math.sin(2 * math.pi * (f - e_pr["f_start"]) / 9.0)
            if e_in["f_start"] < f:
                t = (f - e_in["f_start"]) / (e_in["f_end"] - e_in["f_start"])
                yaw += 5.0 * math.sin(2 * math.pi * 1.5 * t) * (1 - clamp(t)) ** 1.5     # 往里挤的时候扭一扭
            s = S_IN
        return x, y, z, tilt, roll, yaw, s

    # ---- 鼓包走的路（板面坐标）
    RM, RL, RK = KP.R_MAIN, KP.R_LOOP, 1.2
    px, py, kx, ky = cx["plate"], cy["plate"], cx["cdk"], cy["cdk"]
    below = py - KP.PY                                              # 字牌下面那一格的中心 y
    lvx = cx["liver"] + KP.PX / 2                                   # 肝的框右半边那根接主料杆的支杆
    lv_bot = cy["liver"] - (KP.CY + KP.PY / 2)
    last = half_loop(px, py, 1, "b", "s")
    pa = Path2([(px - 130, 0, RM), (px, 0, RM), (px, RM, RK)] + half_loop(px, below, 1, "b", "t") + [(px, py - KP.CY - 0.1, RK)] + last)
    k_split, k_turn = len(pa.p) - len(last), 1                      # 走到字牌框下边中点分成两股；第 1 个点离开主料杆
    pb = Path2([(px + KP.CX, py, RL), (kx - KP.CX, py, RK)] + half_loop(kx, py, -1, "s", "t") + [(kx, ky - KP.CY, RL)])
    pc = Path2([(px, 0, RM), (lvx, 0, RM), (lvx, RM, RK), (lvx, lv_bot, RL)])
    e_pa, e_pb, e_pc = EV["pulse_a"], EV["pulse_b"], EV["pulse_c"]
    m_pulse = hero_mat("pulse_white", M["kit_white"], "#FFEFD0", emit=2.2)
    m_pulse.node_tree.nodes["soft"].outputs[0].default_value = 0.32
    P1, P1b, P2 = make_pulse("pulse_1", m_pulse), make_pulse("pulse_1b", m_pulse), make_pulse("pulse_2", m_pulse)

    def put(o, x, y, ang, r, k, f):
        """鼓包：包住料杆的一个纺锤，料杆粗它就大。k 是大小（0 = 没有）。"""
        o.location = (x * MM, y * MM, zb * MM)
        o.rotation_euler = (0, 0, ang)
        o.scale = ((2.3 * r + 4.0) * k, (1.25 * r + 2.0) * k, (1.25 * r + 2.0) * k)
        for dp in ("location", "rotation_euler", "scale"):
            o.keyframe_insert(dp, frame=f)

    def pulse_frame(f):
        ta = clamp((f - e_pa["f_start"]) / (e_pa["f_land"] - e_pa["f_start"]))
        ut = pa.u_of(k_turn)                                       # 前六成时间在主料杆上走（镜头跟着），后四成拐上支杆到浇口前收住
        ua = ut * (0.5 * smooth(ta / TURN) + 0.5 * ta / TURN) if ta < TURN else ut + (1 - ut) * (1 - (1 - (ta - TURN) / (1 - TURN)) ** 1.6)
        breathe = 1 + 0.05 * math.sin(2 * math.pi * f / 36.0)
        if f <= e_pb["f_start"]:
            x, y, a, r = pa.at(ua)
            k = (1.0 if ua < pa.u_of(k_split) else 0.8) * (1 - 0.35 * smooth((f - e_pa["f_land"]) / 10.0))   # 分股后小一号；喂料时再瘪一点
            put(P1, x, y, a, r, k * breathe, f)
            on = ua >= pa.u_of(k_split) and f < e_pa["f_land"] + 6
            put(P1b, 2 * px - x, y, math.pi - a, r, (0.8 * (1 - smooth((f - e_pa["f_land"]) / 6.0))) if on else 0.0, f)
        else:
            tb = clamp((f - e_pb["f_start"]) / (e_pb["f_land"] - e_pb["f_start"]))
            x, y, a, r = pb.at(smooth(tb))
            put(P1, x, y, a, r, 0.52 * breathe * (1 - smooth((f - e_pb["f_land"]) / 8.0)), f)
            put(P1b, px, py, 0, RL, 0.0, f)
        # 留在岔口的半个鼓包：P1 拐上支杆时分出来，等着；CDK20 起飞前后沿主料杆往左跑去喂肝
        tc = clamp((f - e_pc["f_start"]) / (e_pc["f_land"] - e_pc["f_start"]))
        x, y, a, r = pc.at(smoother(tc))
        k2 = 0.62 * smooth((ua - pa.u_of(k_turn)) / 0.06) * breathe * (1 - smooth((f - e_pc["f_land"]) / 8.0))
        put(P2, x, y, a, r, k2, f)

    # ---- 镜头：被料带着走。几个机位连成折线再平滑，位置、距离、对焦都是连续曲线
    c1, c2, c3 = EV["cam_plate"], EV["cam_cdk"], EV["cam_liver"]
    lx, ly = cx["liver"], cy["liver"]
    fa = lambda u: e_fly["f_start"] + u * (e_fly["f_land"] - e_fly["f_start"])  # noqa: E731  CDK20 飞到几成的那一帧
    fj = e_pa["f_start"] + TURN * (e_pa["f_land"] - e_pa["f_start"])          # 鼓包到岔口的那一帧
    kn_x = [(0, px - 97), (c1["f_start"], px - 95), (fj, px - 30), (c1["f_land"], px - 18), (c2["f_start"], px - 10), (c2["f_land"], kx - 26),
            (c3["f_start"], kx - 30), (fa(0.28), kx - 118), (fa(0.53), lx + 30), (fa(0.80), lx + 6 + 0.4 * Ex), (c3["f_land"], lx + 0.9 * Ex), (NF - 1, lx + Ex)]
    kn_y = [(0, 34), (c1["f_land"], 38), (c2["f_start"], 44), (c2["f_land"], ky - 24), (c3["f_start"], ky - 26), (fa(0.28), ky - 36),
            (fa(0.53), ly - 4), (c3["f_land"], ly - 7 + 0.5 * Ey), (NF - 1, ly - 6 + 0.6 * Ey)]
    kn_z = [(0, 4), (c2["f_start"], 6), (c2["f_land"], 13), (c3["f_start"], 16), (fa(0.28), 28), (fa(0.53), 24), (c3["f_land"], H_LIVER + z_top - 1), (NF - 1, H_LIVER + z_top - 3)]
    kn_d = [(0, 0.252), (c1["f_land"], 0.240), (c2["f_start"], 0.237), (c2["f_land"], 0.226), (c3["f_start"], 0.230), (fa(0.28), 0.296),
            (fa(0.53), 0.294), (c3["f_land"], CAM_LAND), (NF - 1, CAM_END)]
    TX, TY, TZ, TD = (track(k, NF, 9.0) for k in (kn_x, kn_y, kn_z, kn_d))
    cam = KP.camera(sc, (0, 0, 0), 1.0, EL, AZ, lens=LENS, fstop=FSTOP)
    cdir = cam.location.normalized()
    KP.lights((px + lx) / 2 * MM + 0.02, 0.05, 1.35)

    def world(k, p):
        return Vector(((cx[k] + p[0]) * MM, (cy[k] + p[1]) * MM, (zb + p[2]) * MM))

    # 对焦：先到。镜头还在路上，焦点已经落到下一个零件上；最后落在肝里的 CDK20 上
    w_ck = track([(0, 0), (c2["f_start"] - 4, 0), (c2["f_start"] + 22, 1), (NF - 1, 1)], NF, 5.0)
    w_lv = track([(0, 0), (c3["f_start"] + 6, 0), (c3["f_start"] + 36, 0.6), (e_fly["f_land"] - 12, 0.6), (e_fly["f_land"], 1.0), (NF - 1, 1.0)], NF, 5.0)
    cam_pos = []
    for f in range(NF):
        tgt = Vector((TX[f] * MM, TY[f] * MM, (zb + TZ[f]) * MM))
        cam.location = tgt + cdir * float(TD[f])
        cam.keyframe_insert("location", frame=f)
        cam_pos.append(tuple(cam.location))
        X, Y, Z = cdk_world(f)[:3]
        p = world("plate", (0, 0, 1.4)).lerp(Vector((X * MM, Y * MM, Z * MM)), clamp(float(w_ck[f]))).lerp(
            world("liver", (Ex, Ey, liver_z(f) + min(z_top - 2.0, cz(f) + 3.0))), clamp(float(w_lv[f])))
        cam.data.dof.focus_distance = (p - cam.location).dot(-cdir)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)

    # ---- 挤进肝：每帧把肝的壳和血管按 CDK20 的位置算好，存成形状键（只在 CDK20 挨近以后才有）
    def rim_m(f):
        """入口合拢的程度：1 = 合成一点（平时），0 = 开着（CDK20 中心经过顶面的那几帧）。"""
        if f <= e_in["f_start"]:
            return 1.0
        m_open = 1 - smooth((f - e_in["f_start"]) / 4.0)
        d = z_rim - cz(f)
        m_close = smooth((d - 3.0) / 4.0) if d > 0 else 0.0
        return max(m_open, m_close)

    def ripple(f):
        """合拢以后荡开一圈很浅的波纹：(振幅 mm, 走了多远 mm)。"""
        if f < e_cl["f_start"]:
            return 0.0, 0.0
        t = (f - e_cl["f_start"]) / max(1, NF - 1 - e_cl["f_start"])
        return 0.35 * smooth((f - e_cl["f_start"]) / 3.0) * (1 - smooth(t)), 0.9 * (f - e_cl["f_start"])

    def pre_shell(f):
        """形变前先做的两件事（只动顶面入口附近）：入口合拢、波纹。"""
        m = rim_m(f)
        Q = closure(P_sh, top_mask, Ex, Ey, hole["r_h"], z_rim, m)
        a, run = ripple(f)
        if a > 0:
            rl = np.hypot(Q[:, 0] - Ex, Q[:, 1] - Ey)
            env_r = np.exp(-((rl - run - 2.0) / 3.0) ** 2) * (1 - smoothv((rl - (R_TOP - 4)) / 4.0)) * smoothv((P_sh[:, 2] - (z_top - 6.0)) / 2.5)
            Q[:, 2] += a * env_r * np.sin(2 * math.pi * (rl - run) / 5.0)
        return Q, m

    def cdk_part(f):
        """CDK20 的中心（肝零件坐标）、转动矩阵、缩放。"""
        X, Y, Z, tilt, roll, yaw, s = cdk_world(f)
        c = np.array([X - liver0[0], Y - liver0[1], Z - zb - liver_z(f)])
        R = np.array(Euler((math.radians(tilt), math.radians(roll), math.radians(yaw)), "ZYX").to_matrix())
        return c, R, s

    rest_sh, _ = pre_shell(0)
    f_def0 = None
    defs = {}
    for f in range(e_fly["f_start"], NF):
        c, R, s = cdk_part(f)
        Q, m = pre_shell(f)
        Qs = cavity(Q, c, R, s, env)
        Qv = cavity(P_vs, c, R, s, env)
        moved = max(float(np.abs(Qs - rest_sh).max()), float(np.abs(Qv - P_vs).max()))
        if f_def0 is None and moved < 1e-4:
            continue
        if f_def0 is None:
            f_def0 = f
        if abs(c[2] - z_rim) < 2.5 and np.hypot(c[0] - Ex, c[1] - Ey) < 0.5:
            assert m < 0.05, f"第 {f} 帧 CDK20 中心离入口 {c[2] - z_rim:.2f} mm 时入口还没张开（m={m:.2f}）"
        defs[f] = (Qs, Qv)
    assert f_def0 is not None and f_def0 > e_fly["f_start"], "形变一开始就不是零，往前多算几帧"

    def add_keys(o, M_, rest, frames_pos):
        Mi = np.linalg.inv(M_)
        tobj = lambda P: ((P * MM) @ Mi[:3, :3].T + Mi[:3, 3]).ravel()      # noqa: E731
        o.shape_key_add(name="Basis", from_mix=False)
        kr = o.shape_key_add(name="rest", from_mix=False); kr.data.foreach_set("co", tobj(rest))
        kr.value = 1.0; kr.keyframe_insert("value", frame=f_def0 - 1)
        kr.value = 0.0; kr.keyframe_insert("value", frame=f_def0)
        for f, P in frames_pos:
            k = o.shape_key_add(name=f"f{f:04d}", from_mix=False); k.data.foreach_set("co", tobj(P))
            k.value = 0.0; k.keyframe_insert("value", frame=f - 1)
            if f + 1 < NF:
                k.keyframe_insert("value", frame=f + 1)
            k.value = 1.0; k.keyframe_insert("value", frame=f)
        o.data.shape_keys.use_relative = True

    add_keys(shell, Ms, rest_sh, [(f, d[0]) for f, d in sorted(defs.items())])
    add_keys(vessel, Mv, P_vs, [(f, d[1]) for f, d in sorted(defs.items())])
    # 肝壳上的修改器顺序：形状键先算，再生长、变的那道波（这两样到挤的时候都已经是原样）
    print(f"S203 形状键：第 {f_def0}–{NF - 1} 帧，共 {len(defs)} 帧；入口最早张开在第 {next((f for f in range(NF) if rim_m(f) < 0.5), None)} 帧")

    # ---- 逐帧关键帧（全部由 keys 的事件帧算出）
    r_ck.rotation_mode = "ZYX"                 # 先自转再低头：低头的方向一直朝镜头，不跟着转
    near = {}
    for k, reach in (("cdk", 80.0), ("liver", 115.0)):
        c0 = cell[k].matrix_world.translation
        near[k] = [c for c in all_cells if c not in cell.values() and (c.matrix_world.translation - c0).length < reach * MM]
    base_z = {c.name: c.location.z for c in all_cells}
    grow_ev = dict(plate="plate_grow", cdk="cdk_grow", shell="liver_grow", vessel="liver_grow")
    grown = dict(plate=plate, cdk=cdk, shell=shell, vessel=vessel)
    for f in range(NF):
        pulse_frame(f)
        sh = {"cdk": shake(f, e_ej), "liver": shake(f, l_ej)}      # 格子的颤动
        for k in ("cdk", "liver"):
            cell[k].location.z = base_z[cell[k].name] + sh[k] * MM
            cell[k].keyframe_insert("location", frame=f)
        nz = {}
        for k, e in (("cdk", e_ej), ("liver", l_ej)):
            for c in near[k]:
                nz[c.name] = nz.get(c.name, 0.0) + shake(f, e, 0.45, lag=2)
        for n, v in nz.items():
            c = bpy.data.objects[n]; c.location.z = base_z[n] + v * MM; c.keyframe_insert("location", frame=f)
        X, Y, Z, tilt, roll, yaw, s = cdk_world(f)
        zc = Z - zb - (sh["cdk"] if f >= e_ej["f_land"] else 0.0)  # 断开以前零件跟着格子动；断开以后格子颤，零件不颤
        r_ck.location = ((X - cx["cdk"]) * MM, (Y - cy["cdk"]) * MM, zc * MM)
        r_ck.rotation_euler = (math.radians(tilt), math.radians(roll), math.radians(yaw))
        r_ck.scale = (s, s, s)
        r_ck.keyframe_insert("location", frame=f); r_ck.keyframe_insert("rotation_euler", frame=f); r_ck.keyframe_insert("scale", frame=f)
        r_lv.location = (0, 0, (liver_z(f) - (sh["liver"] if f >= l_ej["f_land"] else 0.0)) * MM)
        r_lv.keyframe_insert("location", frame=f)
        for k, eid in grow_ev.items():
            e, g, o = EV[eid], G[k], grown[k]
            lag = 2 if k == "vessel" else 0                        # 复合件：两种料同时到，血管晚两帧
            g["ctrl"].location.x = g["t_end"] * clamp((f - lag - e["f_start"]) / (e["f_end"] - e["f_start"]))
            g["ctrl"].keyframe_insert("location", frame=f)
            o.scale = (1, 1, 1 + 0.03 * max(0.0, 1 - abs(f - lag - e["f_end"]) / 5.0))      # 长满时过冲 3% 再回落
            o.keyframe_insert("scale", frame=f)
            wv = o.data.materials[0].node_tree.nodes["weld"].outputs[0]                       # 熔接线：很浅，长满后半秒淡掉
            wv.default_value = 0.42 * clamp(1 - (f - e["f_end"]) / 30.0) if f >= e["f_start"] else 0.0
            wv.keyframe_insert("default_value", frame=f)
        g = G["plate"]
        rv = txt.data.materials[0].node_tree.nodes["reveal"].outputs[0]
        rv.default_value = max(0.0, g["amax"] * (g["ctrl"].location.x - (1 - g["s"]) - 0.5 * g["tau"]) / g["s"]) * MM
        rv.keyframe_insert("default_value", frame=f)
        # 变：波从 −x 一头扫到 +x 一头，f_land 时正好扫过入口；CDK20 顶下来之前已经走远
        v = (Ex + 60.0) / (l_mo["f_land"] - l_mo["f_start"])
        xw = -60.0 + v * (f - l_mo["f_start"])
        wave_c.location.x = xw * MM if (l_mo["f_start"] <= f and xw < 75) else 1.0
        wave_c.keyframe_insert("location", frame=f)
        # 挤的时候肝壳有点发软发亮（阻力），进去以后凝回
        sv = m_gl.node_tree.nodes["soft"].outputs[0]
        sv.default_value = 0.16 * smooth((f - e_pr["f_start"]) / 4.0) * (1 - smooth((f - e_cl["f_land"]) / 8.0))
        sv.keyframe_insert("default_value", frame=f)
    sc.frame_set(0)
    Path(out_blend).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    print(f"S203 saved {out_blend} in {time.time() - t0:.0f}s")
    rep = dict(keys=str(KEYS), words_hash=Kd["words_hash"], events={k: [e["f_start"], e["f_land"], e["f_end"]] for k, e in EV.items()},
               gates=brk, entry=ent, hole=hole, scale_in_liver=S_IN, gap_mm=GAP, shape_keys=[f_def0, NF - 1],
               cdk_z=dict(touch=round(c_touch, 2), hover=round(c_app, 2), dent=round(c_touch - DENT, 2), final=round(c_fin, 2)))
    rep["smooth"] = smooth_check(sc, Kd, cam_pos, S0, S1)
    rep["layout"] = layout_check(sc, cam, dict(plate=(plate, EV["plate_grow"]["f_end"]), cdk=(cdk, EV["cdk_grow"]["f_end"]), liver=(shell, EV["liver_grow"]["f_end"])))
    rep["clip"] = clip_check(sc, EV, cell, cdk, dict(shell=shell, vessel=vessel), f_def0)
    rep["pass"] = bool(rep["smooth"]["pass"] and rep["clip"]["hits"] == 0 and rep["clip"]["vessel_new"] == 0)
    rp = Path(out_blend).with_suffix(".check.json")
    rp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("S203 report", rp, "总判", "过" if rep["pass"] else "不过")
    return rep


# ---------------------------------------------------------------- 自检：丝滑检查表、画面位置、穿模


def smooth_check(sc, Kd, cam_pos, S0, S1):
    """审片/总管/动效打磨要点_v1.md 第四节的五项。"""
    P = np.array(cam_pos)
    v = np.linalg.norm(np.diff(P, axis=0), axis=1)
    j = np.linalg.norm(np.diff(P, n=3, axis=0), axis=1)
    spikes = []
    for i in range(len(j)):
        nb = np.concatenate([j[max(0, i - 10):i], j[i + 1:i + 11]])
        med = max(float(np.median(nb)), 1e-7)                      # 1e-7 m：低于 0.1 微米每帧³ 的不算
        if j[i] > 4 * med:
            spikes.append((i, round(float(j[i] / med), 1)))
    vmin = float(v[S0:S1].min())
    ev = [e for e in Kd["events"] if e.get("tool") != "remotion"]
    clash = []
    for kind in ("f_start", "f_end"):
        for a in range(len(ev)):
            for b in range(a + 1, len(ev)):
                if abs(ev[a][kind] - ev[b][kind]) < 2:
                    clash.append((kind, ev[a]["id"], ev[b]["id"], ev[a][kind], ev[b][kind]))
    ej = [dict(id=e["id"], lead=e["f_land"] - e["f_start"], ring=e["f_end"] - e["f_land"]) for e in ev if e["verb"] == "eject"]
    ej_ok = all(x["lead"] >= 2 and x["ring"] >= 12 for x in ej)
    mb = bool(sc.render.use_motion_blur)
    ok = not spikes and vmin > 0 and not clash and ej_ok and mb
    print(f"S203 丝滑检查表：镜头加加速度尖峰 {len(spikes)} 处{spikes[:5] if spikes else ''}；句内镜头最低速度 {vmin * 1000:.3f} mm/帧；"
          f"动作起止帧重合 {len(clash)} 处{clash[:4] if clash else ''}；拔 {ej}；运动模糊 {'开' if mb else '关'} →", "过" if ok else "不过")
    return dict(jerk_spikes=spikes, cam_speed_min_mm=round(vmin * 1000, 4), boundary_clash=clash, ejects=ej, motion_blur=mb, **{"pass": bool(ok)})


def layout_check(sc, cam, heroes):
    """主角零件长好以后，每 4 帧看一次它的包围盒在画面里的位置（0–1，y 从上往下）。"""
    from bpy_extras.object_utils import world_to_camera_view
    out = {}
    for k, (o, f0) in heroes.items():
        lo = [1, 1]; hi = [0, 0]
        for f in range(f0, sc.frame_end + 1, 4):
            sc.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            ev = o.evaluated_get(dg)
            for c in ev.bound_box:
                p = world_to_camera_view(sc, cam, ev.matrix_world @ Vector(c))
                lo = [min(lo[0], p.x), min(lo[1], 1 - p.y)]; hi = [max(hi[0], p.x), max(hi[1], 1 - p.y)]
        out[k] = dict(x=[round(lo[0], 3), round(hi[0], 3)], y=[round(lo[1], 3), round(hi[1], 3)])
    print("S203 画面位置", out)
    sc.frame_set(0)
    return out


def world_bvh(o, dg):
    ev = o.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        return None
    if me is None or len(me.polygons) == 0:
        if me is not None:
            ev.to_mesh_clear()
        return None
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    M = np.array(ev.matrix_world)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(co.tolist(), polys), co.min(0), co.max(0)


def clip_check(sc, EV, cell, cdk, liver, f_def0):
    """逐帧穿模检查（BVH 面面相交）：CDK20 对 一路飞过的所有东西（框、料杆、浇口残根、别的格子里的零件、站点牌），
    CDK20 对 玻璃肝的壳、血管（挤进去的全过程），玻璃肝的壳 对 板上不动的东西。没拔之前零件和自己的浇口本来就连着，只在拔之后查浇口。
    肝开始变形（f_def0）以后，再查肝壳对血管：相交的面对数不能比变形前一帧多（血管被挤开时不能顶出肝壳）。
    鼓包、白色断口是有意贴着或包着别的东西的，不查。"""
    t0 = time.time()
    f_ej = {"cdk20": EV["cdk_eject"]["f_land"], "liver": EV["liver_eject"]["f_land"]}
    own = {"cdk20": cell["cdk"].name + "_g", "liver": cell["liver"].name + "_g"}
    fa, fb = EV["cdk_grow"]["f_start"], EV["liver_grow"]["f_start"]
    mine = {cdk, *liver.values()}
    x0 = cell["liver"].matrix_world.translation.x - 0.08
    x1 = cell["cdk"].matrix_world.translation.x + 0.05
    sc.frame_set(sc.frame_end)
    dg = bpy.context.evaluated_depsgraph_get()
    statics = {}
    for o in sc.objects:
        if o.type not in ("MESH", "CURVE", "FONT") or o in mine or o.parent in mine:
            continue
        if o.name.startswith(("pulse_", "seam_", "sweep", "refl_")) or "_scar" in o.name or o.name.endswith(("_cut", "_hole")) or "_hole" in o.name:
            continue
        p = o.matrix_world.translation
        board_level = o.name.startswith(("frame", "main_runner", "lk", "sprue")) or (o.parent is not None and o.parent.name in ("stations", "zone_tags"))
        if not board_level and not (x0 <= p.x <= x1):
            continue
        b = world_bvh(o, dg)
        if b:
            statics[o.name] = b
    hits, nchk = [], 0
    vs_base, vs_new, vs_touch = None, [], 0
    for f in range(fa, sc.frame_end + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        H = {"cdk20": world_bvh(cdk, dg)}
        if f >= fb:
            H["liver"] = world_bvh(liver["shell"], dg)
        for k, h in H.items():
            if h is None:
                continue
            tree, lo, hi = h
            for name, (st, slo, shi) in statics.items():
                if name.startswith(own[k]):
                    if f < f_ej[k] or not name.endswith(("_stub", "_spur")):
                        continue                               # 还连在浇口上；断开后完整的浇口锥已换成残根
                if (lo > shi).any() or (hi < slo).any():
                    continue
                nchk += 1
                if tree.overlap(st):
                    hits.append((f, k, name))
        if f >= fb and H["cdk20"]:
            ta, lo, hi = H["cdk20"]
            for k2, o2 in liver.items():
                if o2.hide_render:
                    continue
                h2 = H.get("liver") if k2 == "shell" else world_bvh(o2, dg)
                if not h2 or (lo > h2[2]).any() or (hi < h2[1]).any():
                    continue
                nchk += 1
                if ta.overlap(h2[0]):
                    hits.append((f, "cdk20", "liver_" + k2))
        if f >= f_def0 and H.get("liver"):
            hv = world_bvh(liver["vessel"], dg)
            dv = {b for a, b in H["liver"][0].overlap(hv[0])} if hv else set()
            for o in liver.values():                               # 同一帧不加形状键（只留原形）再查一次，做对照
                o.show_only_shape_key = True; o.active_shape_key_index = 0
            dg2 = bpy.context.evaluated_depsgraph_get(); dg2.update()
            hs0, hv0 = world_bvh(liver["shell"], dg2), world_bvh(liver["vessel"], dg2)
            rv = {b for a, b in hs0[0].overlap(hv0[0])} if hs0 and hv0 else set()
            new = dv - rv                                          # 原形里不碰肝壳、挤的时候被顶到肝壳上的血管面
            far = 0
            if new:                                                # 原形里本来就贴着肝壳（0.3 mm 以内）的不算，那是两张面一起被推、插值差一点
                ev0 = liver["vessel"].evaluated_get(dg2); me0 = ev0.to_mesh()
                M0 = np.array(ev0.matrix_world)
                for b in new:
                    dmin = min(hs0[0].find_nearest(Vector(M0[:3, :3] @ np.array(me0.vertices[vi].co) + M0[:3, 3]))[3] for vi in me0.polygons[b].vertices)
                    far += dmin > 0.3 * MM
                ev0.to_mesh_clear()
            for o in liver.values():
                o.show_only_shape_key = False
            bpy.context.evaluated_depsgraph_get().update()
            vs_base = max(vs_base or 0, len(rv))
            if far:
                vs_new.append((f, far))
            vs_touch += len(new) - far
    by = {}
    for f, a, b in hits:
        by.setdefault(f"{a} × {b}", []).append(f)
    summ = {k: dict(frames=len(v), first=v[0], last=v[-1]) for k, v in by.items()}
    print(f"S203 穿模检查：第 {fa}–{sc.frame_end} 帧，不动的物体 {len(statics)} 个，做了 {nchk} 次 BVH 相交，穿模 {len(hits)} 处 {summ if hits else ''}；"
          f"肝壳对血管：原形里本来就碰到肝壳的血管面最多 {vs_base} 个，挤的时候新碰到的帧 {len(vs_new)} {vs_new[:6] if vs_new else ''}（原本贴着肝壳、插值擦到的 {vs_touch} 面次不算）（{time.time() - t0:.0f}s）")
    sc.frame_set(0)
    return dict(f0=fa, f1=sc.frame_end, statics=len(statics), tests=nchk, hits=len(hits), by_pair=summ,
                vessel_base=vs_base, vessel_new=len(vs_new), vessel_new_frames=vs_new[:20], vessel_already_touching=vs_touch)


def frames(blend, outdir, flist, samples=None, pct=None):
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"; pr.get_devices()
    for d in pr.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.cycles.denoiser = "OPTIX"
    sc.render.use_persistent_data = True
    if samples:
        sc.cycles.samples = samples
    if pct:
        sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = "PNG"
    for f in flist:
        t = time.time()
        sc.frame_set(f)
        sc.render.filepath = str(Path(outdir) / f"p_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"S203 frame {f} {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], int(a[2]) if len(a) > 2 else 64)
    elif a[0] == "frames":
        frames(a[1], a[2], [int(x) for x in a[3].split(",")], int(a[4]) if len(a) > 4 else None, int(a[5]) if len(a) > 5 else None)
