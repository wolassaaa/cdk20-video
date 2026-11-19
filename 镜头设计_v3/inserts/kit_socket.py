"""HKBU SCIE1007 课程作业的科普视频：H01b 插座（CDK20 外壳）和 H02b 插头组。

单位毫米。坐标：W = +X，沿插孔轴朝外；U = +Y；Z 向上。原点 O = 插孔底触点面中心。
入口：h01b_cdk20_socket(K, lod, pattern)、h02b_plug(K, which, scale, seed)、build、pose、rest、rig。
风格同 kit_deep：每个角色一个空物体（名字 <零件>__<角色>，自定义属性 role），rig 写在根的 JSON 里。
"""
import json
import math
import random

import numpy as np
import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import kit_deep as D
from kit_parts import CDK20_NPZ, circle, smooth_path

MM = D.MM
SEAM = 0.075          # 分件缝半宽：下半壳顶面 Z=-0.075，上半壳底面 Z=+0.075
FACE_W = 12.0         # 孔口面板前表面
SEAT_W = 12.03        # 插头凸缘前面到位时的 W（和孔口面板留 0.03）
FLIP_MOUTH = True     # 见报告：npz 的 mouth 方向朝内，取反作为 +W
BOTTOM_Z, TOP_Z = -20.9, 13.0
LID_MAX = 110.0
GROOVE_W0, GROOVE_W1 = 7.40, 8.70       # 卡口环槽的轴向范围（W）
PIN_W = 8.03                            # 048 卡口销所在 W
SILL_DEG = 16.5                         # 环槽入口加宽区的终点角，001 的销被它挡住

# 机构几何（毫米，W,U,Z）
PLATE = dict(c=(-5.4, -0.25, -16.8), s=(30.0, 33.5, 1.6))     # 顶面 Z=-16.0
MECH_W, MECH_Z = -13.5, -3.3
BARREL_U0, BARREL_U1 = 4.0, 15.0
PAD_REST_U = 1.8
PIPE = [(-4, 0, -6.4), (-4, 0, -13.2), (-7.0, 0, -13.2), (-7.0, 10.0, -13.2), (MECH_W, 10.0, -13.2), (MECH_W, 10.0, -6.5)]


# ------------------------------------------------------------------ 基本工具

def _mm(p):
    return Vector(p) * MM


def _bev(bev, mind):
    """倒角宽：大件不小于 0.2，不大于 0.8，也不超过最小尺寸的四分之一。"""
    if bev <= 0:
        return 0
    return min(max(bev, .2), .8, mind / 4)


def box(P, name, c, s, mat, bev=.12):
    ob = D._local_box(P, c, (1, 0, 0), (0, 1, 0), s[0] / 2, s[1] / 2, s[2], mat, _bev(bev, min(s)))
    ob.name = P.nm(name)
    return ob


def cyl(P, name, c, axis, r, h, mat, bev=.08):
    ob = D._cyl(P, c, axis, r, h, mat, _bev(bev, min(2 * r, h)))
    ob.name = P.nm(name)
    return ob


def tube(P, name, c, axis, ro, ri, h, mat, bev=0.):
    ob = D._tube_axis(P, c, axis, ro, ri, h, mat, _bev(bev, min(ro - ri, h)), n=64)
    ob.name = P.nm(name)
    return ob


def ball(P, name, c, r, mat, seg=24):
    ob = P.ball(c[0], c[1], c[2], r, mat, seg=seg)
    ob.name = P.nm(name)
    return ob


def prism(P, name, pts, t, mat, center, ex, ey, bev=0.):
    """多边形（局部 x,y 毫米）沿 z=ex×ey 拉出厚度 t，居中。"""
    ex, ey = Vector(ex).normalized(), Vector(ey).normalized()
    ob = P.slab(pts, t, mat, bevel=bev)
    ob.name = P.nm(name)
    ez = ex.cross(ey)
    ob.matrix_basis = Matrix.Translation(_mm(center)) @ Matrix((ex, ey, ez)).transposed().to_4x4()
    return ob


def label(P, text, size, loc, rot, mat):
    ob = P.text(text, size, 0, 0, 0, mat)
    ob.data.extrude = .012 * MM
    ob.location = _mm(loc)
    ob.rotation_euler = rot
    return ob


def cut(target, cutter):
    D._boolean(target, cutter)
    return target


def sector_prism(P, name, r0, r1, a0, a1, w0, w1, n=14):
    """绕 W 轴的环扇棱柱（U-Z 平面里角度从 +U 向 +Z），W 从 w0 到 w1，做刀具用。"""
    bm = bmesh.new()
    ring = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        ring.append((r1 * math.cos(a), r1 * math.sin(a)))
    for k in range(n, -1, -1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        ring.append((r0 * math.cos(a), r0 * math.sin(a)))
    v0 = [bm.verts.new((w0 * MM, y * MM, z * MM)) for y, z in ring]
    v1 = [bm.verts.new((w1 * MM, y * MM, z * MM)) for y, z in ring]
    m = len(ring)
    bm.faces.new(v0[::-1])
    bm.faces.new(v1)
    for i in range(m):
        bm.faces.new((v0[i], v0[(i + 1) % m], v1[(i + 1) % m], v1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(P.nm(name))
    bm.to_mesh(me)
    bm.free()
    ob = D.link(bpy.data.objects.new(me.name, me), P.root)
    ob.data.materials.append(P.K.white)
    return ob


def sweep_tube(P, name, pts, ro, ri, mat, n=20):
    """空心管：沿折线扫出内外两层壁（内径 ri），两端用环形端面封口。管里的光包不和管壁体积重叠。"""
    pts = [Vector(p) for p in pts]
    # 平行移动坐标架
    tang = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tang.append((b - a).normalized())
    ref = Vector((0, 0, 1)) if abs(tang[0].z) < .9 else Vector((1, 0, 0))
    u = tang[0].cross(ref).normalized()
    frames = []
    for i, t in enumerate(tang):
        u = (u - t * u.dot(t)).normalized()
        frames.append((u.copy(), t.cross(u).normalized()))
    bm = bmesh.new()
    rings = {}
    for tag, r in (("o", ro), ("i", ri)):
        rings[tag] = []
        for p, (uu, vv) in zip(pts, frames):
            rings[tag].append([bm.verts.new((p + (math.cos(math.tau * k / n) * uu + math.sin(math.tau * k / n) * vv) * r) * MM)
                               for k in range(n)])
    for i in range(len(pts) - 1):
        for k in range(n):
            k1 = (k + 1) % n
            bm.faces.new((rings["o"][i][k], rings["o"][i][k1], rings["o"][i + 1][k1], rings["o"][i + 1][k]))
            bm.faces.new((rings["i"][i][k], rings["i"][i + 1][k], rings["i"][i + 1][k1], rings["i"][i][k1]))
    for i in (0, len(pts) - 1):
        for k in range(n):
            k1 = (k + 1) % n
            bm.faces.new((rings["o"][i][k], rings["o"][i][k1], rings["i"][i][k1], rings["i"][i][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(P.nm(name))
    bm.to_mesh(me)
    bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    ob = D.link(bpy.data.objects.new(me.name, me), P.root)
    ob.data.materials.append(mat)
    return ob


def rounded_path(pts, radius, seg=8):
    """折线在转角处倒圆（二次贝塞尔）。"""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = (a - b), (c - b)
        t = min(radius, d1.length / 2, d2.length / 2)
        e1, e2 = b + d1.normalized() * t, b + d2.normalized() * t
        for k in range(seg + 1):
            s = k / seg
            out.append((1 - s) ** 2 * e1 + 2 * s * (1 - s) * b + s * s * e2)
    out.append(pts[-1])
    return out


# ------------------------------------------------------------------ rig（自己的一套，兼容 kit_deep 的 JSON 约定）

_REST = {}


def _basis(axis, track):
    a = Vector(axis).normalized()
    b = a.cross(Vector((0, 0, 1)))
    if b.length < .1:
        b = a.cross(Vector((0, 1, 0)))
    b.normalize()
    c = a.cross(b)
    cols = (a, b, c) if track == "X" else (b, c, a)
    m = Matrix((cols[0], cols[1], cols[2])).transposed().to_4x4()
    return m


def joint(P, role, typ, lo, hi, pivot=(0, 0, 0), axis=(1, 0, 0), rest=0, parent=None, unit=""):
    j = D._empty(f"{P.name}__{role}", parent or P.root)
    j["role"] = role
    track = {"rot": "X", "loc": "Z"}.get(typ, "X")
    world = Matrix.Translation(_mm(pivot)) @ _basis(axis, track)
    pw = _REST.get(parent.name, Matrix.Identity(4)) if parent else Matrix.Identity(4)
    j.matrix_parent_inverse = pw.inverted() @ world
    _REST[j.name] = world
    spec = json.loads(P.root.get("rig", "{}"))
    spec[role] = dict(type=typ, axis=track, min=lo, max=hi, rest=rest,
                      unit={"rot": "deg", "loc": "mm"}.get(typ, unit))
    P.root["rig"] = json.dumps(spec)
    return j


def adopt(j, *objs):
    for ob in objs:
        if ob is None:
            continue
        ob.parent = j
        ob.matrix_parent_inverse = _REST[j.name].inverted()
        for mod in ob.modifiers:
            if mod.type == "BOOLEAN" and mod.object and mod.object.parent != j:
                adopt(j, mod.object)


def rig(root):
    spec = json.loads(root.get("rig", "{}"))
    return {o["role"]: o for o in root.children_recursive if o.type == "EMPTY" and o.get("role") in spec}


def _lerp_path(pts, s, trim=1.3):
    L = [0.]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    t = trim + min(max(s, 0), 1) * (L[-1] - 2 * trim)      # 光包离光管两端各留 1.3，不碰端帽
    for i in range(len(pts) - 1):
        if L[i + 1] >= t:
            f = (t - L[i]) / max(L[i + 1] - L[i], 1e-9)
            return pts[i].lerp(pts[i + 1], f)
    return pts[-1]


def pose(root, role, value):
    spec = json.loads(root.get("rig", "{}"))[role]
    j = rig(root)[role]
    v = min(max(value, spec["min"]), spec["max"])
    typ = spec["type"]
    if typ == "rot":
        j.rotation_euler.x = math.radians(v)
    elif typ == "loc":
        j.location.z = v * MM
    elif typ == "scale":
        j.scale = (v, v, v)
    elif typ == "switch":
        on = v >= .5
        for ch in j.children:
            k = ch.get("lamp")
            if k == "on":
                ch.hide_render = ch.hide_viewport = not on
            elif k == "off":
                ch.hide_render = ch.hide_viewport = on
            elif ch.type == "LIGHT":
                ch.data.energy = ch["watts"] if on else 0.
    elif typ == "path":
        pts = [Vector(p) for p in json.loads(root["pipe_path_mm"])]
        for ch in j.children:
            if "ball_i" not in ch:
                continue
            s = v - .12 * ch["ball_i"]
            ch.hide_render = ch.hide_viewport = s < 0 or v <= 0
            ch.location = _lerp_path(pts, s) * MM
    j["pose_value"] = v
    return v


def rest(root):
    for role, spec in json.loads(root.get("rig", "{}")).items():
        pose(root, role, spec["rest"])


def lug_tab_angle(twist_deg):
    """插头拧到 >= 80° 时卡扣开始转，90° 时 -25°（动画联动用）。"""
    s = min(max((twist_deg - 80.) / 10., 0), 1)
    return -25. * s * s * (3 - 2 * s)


# ------------------------------------------------------------------ 外壳
# AlphaFold 包络在 Z=0 分件面上只有约 18 毫米宽，装不下机舱（见报告）。外壳改为：
# 取包络（插孔轴水平后）俯视轮廓的凸包，和"装得下机舱的圆角矩形"在极坐标上取大者，
# 保留包络的有机起伏；轮廓沿 Z 拉出，上下边倒圆，前面压平到 W=SHELL_FRONT。

SHELL_FRONT = 11.7
HULL_K = 1.0
FIT_RECT = (-23.2, 11.7, -19.8, 19.4)          # W0, W1, U0, U1：机舱外包加壁厚余量
_OUT_CACHE = {}


def _envelope_top_view():
    d = np.load(str(CDK20_NPZ))
    v = d["verts"].astype(float)
    c0 = v.mean(0)
    mn = d["mouth"].astype(float)
    mn /= np.linalg.norm(mn)
    if FLIP_MOUTH:
        mn = -mn
    yaw = math.atan2(mn[1], mn[0])
    Rz = np.array([[math.cos(-yaw), -math.sin(-yaw), 0], [math.sin(-yaw), math.cos(-yaw), 0], [0, 0, 1]])
    m2 = Rz @ mn
    pitch = math.atan2(m2[2], m2[0])
    Ry = np.array([[math.cos(pitch), 0, math.sin(pitch)], [0, 1, 0], [-math.sin(pitch), 0, math.cos(pitch)]])
    R = Ry @ Rz
    w = (v - c0) @ R.T
    pk = (d["pocket"].astype(float) - c0) @ R.T
    s = 36.0 / max(np.ptp(w[:, 0]), np.ptp(w[:, 1]))
    w = (w - pk) * s
    return w[:, :2]


def _hull(pts):
    pts = sorted(map(tuple, pts))
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(pts[::-1])
    return np.array(lo[:-1] + up[:-1])


def shell_outline(n=180):
    """壳体俯视轮廓（W,U 毫米），顺序逆时针，中心在机舱矩形中心。"""
    if "o" in _OUT_CACHE:
        return _OUT_CACHE["o"]
    hull = _hull(_envelope_top_view())
    w0, w1, u0, u1 = FIT_RECT
    cw, cu = (w0 + w1) / 2, (u0 + u1) / 2
    hw, hu = (w1 - w0) / 2, (u1 - u0) / 2
    # 包络凸包的中心对到矩形中心
    hull = hull - hull.mean(0) + np.array([cw, cu])
    th = np.linspace(0, math.tau, n, endpoint=False)
    rh = []
    for t in th:
        d = np.array([math.cos(t), math.sin(t)])
        best = 0
        for i in range(len(hull)):
            a, b = hull[i] - [cw, cu], hull[(i + 1) % len(hull)] - [cw, cu]
            e = b - a
            m = d[0] * (-e[1]) + d[1] * e[0]
            if abs(m) < 1e-9:
                continue
            tt = (a[0] * (-e[1]) + a[1] * e[0]) / m
            uu = (a[0] * (-d[1]) + a[1] * d[0]) / m
            if tt > 0 and -1e-9 <= uu <= 1 + 1e-9:
                best = max(best, tt)
        rh.append(best)
    rh = np.array(rh) * HULL_K
    a_, b_ = hw * 1.13, hu * 1.13
    rs = np.array([1.0 / (abs(math.cos(t) / a_) ** 4 + abs(math.sin(t) / b_) ** 4) ** .25 for t in th])
    r = np.maximum(rh, rs)
    k = np.ones(9) / 9
    r = np.convolve(np.concatenate([r[-8:], r, r[:8]]), k, "same")[8:-8]
    pts = np.stack([cw + r * np.cos(th), cu + r * np.sin(th)], 1)
    pts[:, 0] = np.minimum(pts[:, 0], SHELL_FRONT)
    out = (pts, (cw, cu))
    _OUT_CACHE["o"] = out
    return out


def _ring_levels(sign):
    if sign < 0:
        return [(-SEAM, 1.0), (-17.2, 1.0), (-19.0, .975), (-20.1, .945), (-20.7, .915), (BOTTOM_Z, .90)]
    return [(SEAM, 1.0), (9.6, 1.0), (11.4, .975), (12.4, .945), (12.85, .915), (TOP_Z, .90)]


def shell_halves(P, K, step=1):
    outline, c = shell_outline()
    outline = outline[::step]
    c = Vector((c[0], c[1], 0))
    halves = {}
    for name, sign in (("lower", -1), ("upper", 1)):
        bm = bmesh.new()
        rings = []
        for z, k in _ring_levels(sign):
            rings.append([bm.verts.new(((c.x + k * (p[0] - c.x)) * MM, (c.y + k * (p[1] - c.y)) * MM, z * MM)) for p in outline])
        n = len(outline)
        for i in range(len(rings) - 1):
            for j in range(n):
                bm.faces.new((rings[i][j], rings[i][(j + 1) % n], rings[i + 1][(j + 1) % n], rings[i + 1][j]))
        end = bmesh.ops.contextual_create(bm, geom=rings[-1])["faces"]
        start = bmesh.ops.contextual_create(bm, geom=rings[0])["faces"]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.delete(bm, geom=start, context="FACES_ONLY")
        me = bpy.data.meshes.new(P.nm("shell_" + name))
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        ob = D.link(bpy.data.objects.new(me.name, me), P.root)
        ob.data.materials.append(K.blue)
        sd = ob.modifiers.new("wall", "SOLIDIFY")
        sd.thickness = -1.2 * MM
        sd.offset = 1
        sd.use_even_offset = True
        sd.use_rim = True
        _apply_mods(ob)
        ob.modifiers.new("wn", "WEIGHTED_NORMAL")
        halves[name] = ob
    return halves


def _apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


# ------------------------------------------------------------------ H01b hero

def _tags(ob, layer):
    ob["layer"] = layer
    return ob


def _glow(K, strength=2.0):
    """灯珠和光包用 K.yellow 的一份拷贝（kit_clear_yellow_lit），在暗处自发光；K.yellow 本身不动（真插头 ATP 仍是纯透明黄）。"""
    if getattr(K, "yellow_lit", None) is not None:
        return K.yellow_lit
    m = K.yellow.copy()
    m.name = "kit_clear_yellow_lit"
    nt = m.node_tree
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    link = [l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface"][0]
    src = link.from_socket
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, .62, .02, 1)
    em.inputs["Strength"].default_value = strength
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(src, add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    K.yellow_lit = m
    return m


def h01b_cdk20_socket(K, lod="hero", pattern="round"):
    _glow(K)
    if lod == "mini":
        return _mini(K, pattern)
    if lod != "hero":
        raise ValueError(lod)
    P = D.Part(K, "h01b_cdk20_socket", "blue")
    fixed, lid = [], []

    def F(ob, layer="front"):
        fixed.append(_tags(ob, layer)); return ob

    def L(ob, layer="front"):
        lid.append(_tags(ob, layer)); return ob

    # ---- 外壳
    halves = shell_halves(P, K)
    low, up = halves["lower"], halves["upper"]
    # 孔口面板（两半，Ø14.4 孔）
    for name, sign in (("lower", -1), ("upper", 1)):
        z0 = -9.0 if sign < 0 else SEAM
        z1 = -SEAM if sign < 0 else 9.0
        fp = box(P, "faceplate_" + name, (FACE_W - .6, 0, (z0 + z1) / 2), (1.2, 23.0, z1 - z0), K.blue, .3)
        cut(fp, cyl(P, "mouth_hole", (FACE_W - .6, 0, 0), (1, 0, 0), 7.2, 4, K.blue, 0))
        (F if sign < 0 else L)(fp, "shell")
    for ob in (low,):
        cut(ob, cyl(P, "mouth_cut", (FACE_W - 2.0, 0, 0), (1, 0, 0), 7.3, 6, K.blue, 0))
        F(ob, "shell")
    cut(up, cyl(P, "mouth_cut", (FACE_W - 2.0, 0, 0), (1, 0, 0), 7.3, 6, K.blue, 0))
    L(up, "shell")

    # ---- 孔桶（上下半）、红环、触点块
    def halfspace(sign):
        return box(P, "half_cut", (FACE_W / 2, 0, sign * 20), (40, 40, 40), K.white, 0)

    barrel = {}
    for sign in (-1, 1):
        t = tube(P, "barrel_" + ("lower" if sign < 0 else "upper"), (6.01, 0, 0), (1, 0, 0), 7.0, 5.15, 11.98, K.white, .12)
        cut(t, box(P, "half_cut", (6, 0, -sign * 20 + sign * SEAM), (40, 40, 40), K.white, 0))
        barrel[sign] = t
    for sign, t in barrel.items():
        for dirn in (1, -1):
            a0, a1 = (-9.0, 100.0) if dirn == 1 else (171.0, 280.0)
            cut(t, sector_prism(P, "groove", 5.0, 6.15, a0, a1, GROOVE_W0, GROOVE_W1))
            cut(t, sector_prism(P, "sill_pocket", 5.0, 6.15, a0, a0 + 9.0 + SILL_DEG, GROOVE_W1 - .01, 9.6))
            cut(t, box(P, "entry_slot", (9.7, dirn * 5.6, 0), (4.7, 1.15, 1.3), K.white, 0))
            cut(t, ball(P, "detent", (PIN_W, dirn * 5.9 * math.cos(math.radians(88)), 5.9 * math.sin(math.radians(88)) * dirn), .75, K.white))
        # 红环凹槽
        cut(t, tube(P, "ring_groove", (11.8, 0, 0), (1, 0, 0), 6.7, 5.7, .4, K.white))
    F(barrel[-1], "front")
    L(barrel[1], "front")
    for sign in (-1, 1):
        rr = tube(P, "red_ring_" + ("lower" if sign < 0 else "upper"), (11.78, 0, 0), (1, 0, 0), 6.62, 5.78, .36, K.red)
        cut(rr, box(P, "half_cut", (11.8, 0, -sign * 20 + sign * SEAM), (40, 40, 40), K.white, 0))
        for su in (-1, 1):
            cut(rr, box(P, "pin_gap", (11.78, su * 6.2, 0), (.6, 2.0, 1.8), K.white, 0))
        (F if sign < 0 else L)(rr, "front")

    blocks = {}
    for sign in (-1, 1):
        z0, z1 = (-5.4, -SEAM) if sign < 0 else (SEAM, 5.4)
        b = box(P, "contact_block_" + ("lower" if sign < 0 else "upper"), (-3.0, 0, (z0 + z1) / 2), (6.0, 12.0, z1 - z0), K.white, .25)
        cut(b, cyl(P, "hole_round", (-2.75, 2.7, 0), (1, 0, 0), .95, 5.6, K.white, 0))
        cut(b, box(P, "hole_slot", (-2.75, -2.7, 0), (5.6, 1.0, 3.1), K.white, 0))
        cut(b, cyl(P, "hole_ground", (-2.75, 0, -3.3), (1, 0, 0), .8, 5.6, K.white, 0))
        blocks[sign] = b
    F(blocks[-1], "front")
    L(blocks[1], "front")

    # ---- 后层
    pl = PLATE
    plate = box(P, "back_plate", pl["c"], pl["s"], K.white, .3)
    cut(plate, box(P, "wire_groove", (-4, 8.0, -16.0), (28, 1.6, 1.6), K.white, 0))
    cut(plate, box(P, "wire_groove", (-4, -4.5, -16.0), (28, 1.6, 1.6), K.white, 0))
    for c in ((-12.0, -9.5), (-1.0, -9.5), (-1.0, 9.8)):
        cut(plate, box(P, "plate_vent", (c[0], c[1], -15.6), (6.0, 2.0, 1.2), K.white, 0))
    for c in ((-16.5, -9.5), (-16.5, 3.0), (-5.0, 12.5)):          # 顶针印 Ø0.8、深 0.1
        cut(plate, cyl(P, "ejector_pit", (c[0], c[1], -16.0), (0, 0, 1), .4, .2, K.white, 0))
    F(plate, "back")
    F(box(P, "data_plate", (-13.0, 12.2, -15.95), (6.0, 2.6, .3), K.blue_hi, .08), "back")
    label(P, "01", 1.4, (-13.0, 12.2, -15.62), (0, 0, 0), K.white)
    label(P, "CDK20-01", 1.0, (7.0, -10.0, -15.98), (0, 0, 0), K.black).parent = P.root
    for sx in (-17.0, 6.0):
        for sy in (-12.0, 12.0):
            F(cyl(P, "pad", (sx, sy, -18.5), (0, 0, 1), 1.5, 1.8, K.white, .2), "back")
    for c, s in (((-5, -16.0, -15.2), (28, 1.0, 1.6)), ((-5, 15.7, -15.2), (28, 1.0, 1.6)),
                 ((-19.9, -0.25, -15.2), (1.0, 31, 1.6)), ((9.1, -0.25, -15.2), (1.0, 31, 1.6)), ((5.0, -0.25, -15.2), (1.0, 28, 1.6))):
        F(box(P, "rib", c, s, K.white, .15), "back")
    for rx in (-14.0, -8.0, -2.0, 4.0):
        for ry in (-16.0, 15.7):
            F(D._screw(P, (rx, ry, -14.38), (0, 0, 1), .45, K.gold_satin), "back")
    for sx, sy in ((-17.8, -13.6), (-17.8, 13.6), (7.8, -13.6), (7.8, 13.6)):
        F(cyl(P, "screw_post", (sx, sy, -14.5), (0, 0, 1), 1.2, 3.0, K.white, .15), "back")
        F(D._screw(P, (sx, sy, -12.98), (0, 0, 1), .9, K.gold_satin), "back")
    # 走线（两根）和线夹
    for u, pts in ((8.0, [(-12, 8, -15.2), (-2, 8, -15.2), (6, 8, -15.2)]), (-4.5, [(-12, -4.5, -15.2), (-2, -4.5, -15.2), (6, -4.5, -15.2)])):
        wire = sweep_tube(P, "harness", [(-14, u, -15.2), (-4, u, -15.2), (8, u, -15.2)], .7, .6, K.clear0, 14)
        F(wire, "back")
        core = P.tube([(-14, u, -15.2), (8, u, -15.2)], .3, K.gold_satin)
        core.name = P.nm("harness_core")
        F(core, "back")
        for w in (-10, -4, 2, 8 - 1):
            clip = prism(P, "wire_clip", [(1.1 * math.cos(math.radians(a)), 1.1 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
                         + [(.8 * math.cos(math.radians(a)), .8 * math.sin(math.radians(a))) for a in range(180, -1, -15)],
                         1.0, K.white, (w, u, -15.2), (0, 1, 0), (0, 0, 1))
            F(clip, "back")

    # ---- 中层：搭桥板、立柱、活塞筒、光管
    bridge = box(P, "bridge_plate", (MECH_W, 9.5, -9.0), (8.0, 14.0, 1.2), K.blue_hi, .25)   # U 2.5..16.5
    cut(bridge, cyl(P, "pipe_hole", (MECH_W, 10.0, -9.0), (0, 0, 1), 1.8, 3, K.white, 0))
    F(bridge, "mid")
    cut(bridge, box(P, "bridge_slot", (MECH_W, 5.0, -9.0), (4.0, 1.4, 3), K.blue_hi, 0))
    cut(bridge, box(P, "bridge_slot", (MECH_W, 14.4, -9.0), (4.0, 1.4, 3), K.blue_hi, 0))
    for sx in (-3.2, 3.2):
        for sy in (3.6, 15.4):
            F(D._screw(P, (MECH_W + sx, sy, -8.38), (0, 0, 1), .7, K.gold_satin), "mid")
    for sx, sy in ((MECH_W - 2.6, 4.0), (MECH_W + 2.6, 4.0), (MECH_W - 2.6, 15.0), (MECH_W + 2.6, 15.0)):
        F(cyl(P, "bridge_post", (sx, sy, -12.5), (0, 0, 1), 1.3, 7.0, K.blue_hi, .15), "mid")
    barrel_t = tube(P, "piston_barrel", (MECH_W, (BARREL_U0 + BARREL_U1) / 2, MECH_Z), (0, 1, 0), 3.0, 2.8, BARREL_U1 - BARREL_U0, K.white, .1)
    cut(barrel_t, box(P, "view_window", (MECH_W, 9.5, MECH_Z + 2.0), (3.2, 9.0, 4.0), K.white, 0))
    F(barrel_t, "mid")
    F(tube(P, "barrel_band", (MECH_W, 9.5, MECH_Z), (0, 1, 0), 3.2, 2.95, .6, K.gold_satin, .08), "mid")
    F(tube(P, "barrel_band_red", (MECH_W, 14.2, MECH_Z), (0, 1, 0), 3.15, 2.95, .5, K.red, .06), "mid")
    F(cyl(P, "barrel_cap", (MECH_W, BARREL_U1 + .3, MECH_Z), (0, 1, 0), 3.2, .6, K.white, .15), "mid")
    F(tube(P, "rod_bushing", (MECH_W, BARREL_U0 - .45, MECH_Z), (0, 1, 0), 3.5, .9, .88, K.gold_satin, .1), "mid")
    F(tube(P, "rod_washer", (MECH_W, BARREL_U0 - .95, MECH_Z), (0, 1, 0), 1.7, .9, .3, K.gold_satin, .05), "mid")
    for su in (6.0, 13.0):
        sd = box(P, "barrel_saddle", (MECH_W, su, (MECH_Z - 5.1 + -8.4) / 2 + 2.4), (8.0, 1.2, 5.0), K.white, .2)
        cut(sd, cyl(P, "saddle_hole", (MECH_W, su, MECH_Z), (0, 1, 0), 3.05, 4, K.white, 0))
        F(sd, "mid")
    # 小细胞托盘
    tray = box(P, "cell_tray", (MECH_W, -9.5, -10.7), (14.0, 15.0, 1.0), K.white, .25)
    F(tray, "mid")
    for su_ in (-1, 1):
        F(box(P, "tray_rail", (MECH_W + su_ * 6.6, -9.5, -9.7), (.8, 15.0, 1.0), K.blue_hi, .12), "mid")
    for uu in (-15, -12, -9, -6, -3.5):
        F(box(P, "tray_groove", (MECH_W, uu, -10.15), (11.0, .5, .12), K.black, 0), "mid")
    for sx in (-18.0, -9.0):
        for sy in (-15.5, -5.5):
            F(cyl(P, "tray_leg", (sx, sy, -13.4), (0, 0, 1), 1.0, 4.6, K.white, .12), "mid")
    # 光管
    path = rounded_path(PIPE, 2.4)
    pipe = sweep_tube(P, "light_pipe", path, 1.1, .95, K.clear)
    F(pipe, "mid")
    P.root["pipe_path_mm"] = json.dumps([list(p) for p in path])
    for c, ax in (((-4, 0, -9.5), (0, 0, 1)), ((-7.0, 5, -13.2), (0, 1, 0)), ((-10.5, 10, -13.2), (1, 0, 0))):
        F(tube(P, "pipe_clip", c, ax, 1.7, 1.15, 1.2, K.white, .1), "mid")

    # ---- 前层：支撑、触点叶、卡扣
    F(tube(P, "pipe_port", (-4, 0, -6.0), (0, 0, 1), 1.9, 1.15, .8, K.gold_satin, .1), "front")
    for su in (-4.3, 4.3):
        F(cyl(P, "block_pillar", (-3.0, su, -10.8), (0, 0, 1), 1.3, 10.8, K.blue_hi, .15), "front")
    for sw in (1.8, 8.4):
        sd = box(P, "barrel_cradle", (sw, 0, -9.8), (1.4, 16.4, 12.2), K.white, .25)
        cut(sd, cyl(P, "cradle_hole", (sw, 0, 0), (1, 0, 0), 7.05, 4, K.white, 0))
        for cu in (-3.5, 3.5):
            cut(sd, cyl(P, "cradle_vent", (sw, cu, -11.5), (1, 0, 0), 1.3, 4, K.white, 0))
        F(sd, "front")
    for sy in (-10.0, 10.0):
        F(D._screw(P, (FACE_W + .0, sy, -7.5), (1, 0, 0), .8, K.gold_satin), "shell")
        # 孔口细框线（0.2 深）
    fl = [o for o in fixed if o.name.endswith("faceplate_lower") or "faceplate_lower" in o.name][0]
    cut(fl, box(P, "frame_line", (FACE_W - .1, 0, -8.0), (.2, 18.0, .3), K.white, 0))

    # 接线叶（可动）
    leaf_a = cyl(P, "contact_leaf_a", (-4.65, 2.7, 0), (1, 0, 0), .8, .3, K.gold_satin, .05)
    leaf_b = box(P, "contact_leaf_b", (-4.65, -2.7, 0), (.3, .8, 2.9), K.gold_satin, .05)
    # 卡扣与铰链销
    TAB = (12.9, 9.3, 0.0)
    ear = box(P, "tab_ear", (12.65, 9.3, -1.9), (1.4, 2.0, 1.4), K.blue, .15)
    F(ear, "shell")
    F(cyl(P, "tab_pin", (TAB[0], TAB[1], -.2), (0, 0, 1), .7, 3.2, K.gold_satin, .05), "shell")
    tab_body = prism(P, "tab_arm", [(-.6, -.6), (2.3, -.6), (2.3, -2.2), (3.8, -2.2), (3.8, .6), (-.6, .6)],
                     1.6, K.red, (TAB[0], TAB[1], 0), (1, 0, 0), (0, 1, 0), .15)
    cut(tab_body, cyl(P, "tab_hole", (TAB[0], TAB[1], 0), (0, 0, 1), .78, 4, K.red, 0))
    # 灯
    lamp_out_c = (-4.0, 0.0, TOP_Z + .3)
    lamp_in_c = (-3.0, -9.5, -1.0)

    # ---- 角色
    outline, _c = shell_outline()
    hinge_x = float(outline[:, 0].min()) - 2.0
    pk = outline[int(np.argmin(outline[:, 0]))]
    F(cyl(P, "locating_peg", (float(pk[0]) - .5, float(pk[1]), -7.0), (1, 0, 0), 1.0, 3.0, K.blue, .2), "shell")
    P.root["hinge_w_mm"] = hinge_x
    j_lid = joint(P, "lid", "rot", 0, LID_MAX, pivot=(hinge_x, 0, SEAM), axis=(0, -1, 0))
    # 铰链
    kn = cyl(P, "hinge_knuckle_lid", (hinge_x, 0, SEAM), (0, 1, 0), 1.5, 7.0, K.gold_satin, .1)
    arm_l = box(P, "hinge_arm_lid", (hinge_x + 1.4, 0, SEAM + .9), (2.8, 6.0, 1.6), K.blue, .15)
    L(kn, "shell"); L(arm_l, "shell")
    for su in (-9.0, 9.0):
        F(cyl(P, "hinge_knuckle", (hinge_x, su, SEAM), (0, 1, 0), 1.5, 5.0, K.gold_satin, .1), "shell")
        F(box(P, "hinge_arm", (hinge_x + 1.4, su, -SEAM - .9), (2.8, 4.6, 1.6), K.blue, .15), "shell")
    # 盖内：外灯、标签凸台、加强筋
    lo = cyl(P, "lamp_out_on", lamp_out_c, (0, 0, 1), 1.5, .6, K.yellow_lit, .1)
    lo["lamp"] = "on"
    lof = cyl(P, "lamp_out_off", lamp_out_c, (0, 0, 1), 1.5, .6, K.clear0, .1)
    lof["lamp"] = "off"
    lof.hide_render = lof.hide_viewport = True
    bezel = tube(P, "lamp_bezel", (lamp_out_c[0], lamp_out_c[1], TOP_Z + .1), (0, 0, 1), 2.1, 1.55, .4, K.gold_satin, .08)
    lbl = box(P, "label_boss", (-14.0, 0, TOP_Z + .2), (7.0, 2.4, .4), K.blue_hi, .1)
    label(P, "CDK20", 1.4, (-14.0, 0, TOP_Z + .42), (0, 0, 0), K.white)
    for u in (-6.0, 6.0):
        L(box(P, "lid_rib", (-10.0, u, TOP_Z - 2.2), (22.0, 1.0, 2.0), K.blue, .15), "shell")
    L(bezel, "shell"); L(lbl, "shell")
    adopt(j_lid, *[o for o in lid])
    # 标签文字随盖
    for ob in P.root.children:
        if ob.type == "FONT" and ob.location.z > 5 * MM:
            adopt(j_lid, ob)

    j_leafa = joint(P, "leaf_a", "loc", -.6, 0, pivot=(-4.65, 2.7, 0), axis=(1, 0, 0))
    j_leafb = joint(P, "leaf_b", "loc", -.6, 0, pivot=(-4.65, -2.7, 0), axis=(1, 0, 0))
    adopt(j_leafa, leaf_a)
    adopt(j_leafb, leaf_b)
    j_tab = joint(P, "tab", "rot", -25, 0, pivot=TAB, axis=(0, 0, 1))
    adopt(j_tab, tab_body)

    # 活塞 + 小细胞
    j_pis = joint(P, "piston", "loc", 0, 5.0, pivot=(MECH_W, 0, MECH_Z), axis=(0, -1, 0))
    rod = cyl(P, "piston_rod", (MECH_W, 6.9, MECH_Z), (0, 1, 0), .8, 9.0, K.gold_satin, .08)
    head = cyl(P, "piston_head", (MECH_W, 11.0, MECH_Z), (0, 1, 0), 2.6, 1.4, K.gold_satin, .12)
    pad = cyl(P, "rod_pad", (MECH_W, PAD_REST_U + .3, MECH_Z), (0, 1, 0), 1.6, .6, K.red, .12)
    adopt(j_pis, rod, head, pad)
    j_cell = joint(P, "cell", "scale", 1.0, 1.45, pivot=(MECH_W, PAD_REST_U - .1, MECH_Z), axis=(1, 0, 0), rest=1.0, parent=j_pis)
    cc = (MECH_W, PAD_REST_U - .1 - 4.5, MECH_Z)
    shell_c = ball(P, "cell_shell", cc, 4.5, K.clear0, 48)
    nuc = ball(P, "cell_nucleus", cc, 1.6, K.cellpink, 32)
    adopt(j_cell, shell_c, nuc)

    # 光包
    j_flow = joint(P, "flow", "path", 0, 1, pivot=(0, 0, 0), axis=(1, 0, 0))
    for i in range(3):
        bl = ball(P, "light_packet", PIPE[0], .8, K.yellow_lit, 24)
        bl["ball_i"] = i
        bl.hide_render = bl.hide_viewport = True
        adopt(j_flow, bl)

    # 灯
    j_lo = joint(P, "lamp_out", "switch", 0, 1, pivot=lamp_out_c, axis=(1, 0, 0), rest=1, parent=j_lid)
    adopt(j_lo, lo, lof)
    li = ball(P, "lamp_in_on", lamp_in_c, .8, K.yellow_lit, 20)
    li["lamp"] = "on"
    lif = ball(P, "lamp_in_off", lamp_in_c, .8, K.clear0, 20)
    lif["lamp"] = "off"
    lif.hide_render = lif.hide_viewport = True
    F(box(P, "lamp_in_bracket", (-3.0, -9.5, -9.05), (1.4, 1.4, 14.1), K.white, .15), "front")
    j_li = joint(P, "lamp_in", "switch", 0, 1, pivot=lamp_in_c, axis=(1, 0, 0), rest=1)
    adopt(j_li, li, lif)
    for j, c, w in ((j_lo, lamp_out_c, .4), (j_li, lamp_in_c, .4)):
        ld = bpy.data.lights.new(j.name + "_light", "POINT")
        ld.energy = w
        ld.shadow_soft_size = .0004
        lo_ = D.link(bpy.data.objects.new(ld.name, ld))
        lo_.location = _mm(c)
        lo_["watts"] = w
        lo_.visible_camera = False
        adopt(j, lo_)

    # 空物体：对位
    for nm, pos in (("mouth", (FACE_W, 0, 0)), ("seat", (SEAT_W, 0, 0)), ("approach", (36.0, 0, 0)),
                    ("contact", (0, 0, 0)), ("hinge", (hinge_x, 0, SEAM))):
        e = D._empty(f"{P.name}__{nm}", P.root)
        e.location = _mm(pos)
        e["locator"] = nm

    # 浇口：轮廓最靠外的三点（-W、-U、+U）
    for key, dn in ((lambda p: -p[0], "-x"), (lambda p: -p[1], "-y"), (lambda p: p[1], "+y")):
        p = max(outline, key=key)
        P.gate(float(p[0]) + (.4 if dn == "-x" else 0), float(p[1]) + (.4 if dn == "-y" else -.4 if dn == "+y" else 0), dn, -6.0)
    rest(P.root)
    return P.done()


# ------------------------------------------------------------------ mini 版（缩到 0.40，壳不能开，前半壳透明）

def _mini(K, pattern):
    if pattern not in ("round", "slots", "tri"):
        raise ValueError(pattern)
    P = D.Part(K, "h01b_mini_" + pattern, "blue")
    halves = shell_halves(P, K, 4)
    low, up = halves["lower"], halves["upper"]
    up.data.materials.clear()
    up.data.materials.append(K.clear0)
    for h in (low, up):
        cut(h, cyl(P, "mouth_cut", (FACE_W - 2.0, 0, 0), (1, 0, 0), 7.3, 6, K.blue, 0))
    ring_m = K.red if pattern == "round" else K.white
    for sign in (-1, 1):
        t = tube(P, "barrel_" + ("lower" if sign < 0 else "upper"), (6.01, 0, 0), (1, 0, 0), 7.0, 5.15, 11.98, K.white, .12)
        cut(t, box(P, "half_cut", (6, 0, -sign * 20 + sign * SEAM), (40, 40, 40), K.white, 0))
        tube(P, "ring_" + ("lower" if sign < 0 else "upper"), (11.82, 0, 0), (1, 0, 0), 6.62, 5.78, .32, ring_m, .06)
    for sign in (-1, 1):
        z0, z1 = (-5.4, -SEAM) if sign < 0 else (SEAM, 5.4)
        b = box(P, "contact_block", (-3.0, 0, (z0 + z1) / 2), (6.0, 12.0, z1 - z0), K.white, .25)
        if pattern == "round":
            cut(b, cyl(P, "hole_round", (-2.75, 2.7, 0), (1, 0, 0), .95, 5.6, K.white, 0))
            cut(b, box(P, "hole_slot", (-2.75, -2.7, 0), (5.6, 1.0, 3.1), K.white, 0))
            cut(b, cyl(P, "hole_ground", (-2.75, 0, -3.3), (1, 0, 0), .8, 5.6, K.white, 0))
        elif pattern == "slots":
            for uu in (-3.0, 3.0):
                cut(b, box(P, "hole_slot", (-2.75, uu, 0), (5.6, 1.0, 3.1), K.white, 0))
        else:
            for uu, zz in ((0, 2.6), (-2.5, -1.6), (2.5, -1.6)):
                cut(b, cyl(P, "hole_tri", (-2.75, uu, zz), (1, 0, 0), .75, 5.6, K.white, 0))
    plate = box(P, "back_plate", PLATE["c"], PLATE["s"], K.white, .3)
    for sx, sy in ((-17.8, -13.6), (-17.8, 13.6), (7.8, -13.6), (7.8, 13.6)):
        cyl(P, "screw_post", (sx, sy, -14.5), (0, 0, 1), 1.2, 3.0, K.white, .15)
    bridge = box(P, "bridge_plate", (MECH_W, 9.5, -9.0), (8.0, 14.0, 1.2), K.blue_hi, .25)
    for sx, sy in ((MECH_W - 2.6, 4.0), (MECH_W + 2.6, 4.0), (MECH_W - 2.6, 15.0), (MECH_W + 2.6, 15.0)):
        cyl(P, "bridge_post", (sx, sy, -12.5), (0, 0, 1), 1.3, 7.0, K.blue_hi, .15)
    for su in (-4.3, 4.3):
        cyl(P, "block_pillar", (-3.0, su, -10.8), (0, 0, 1), 1.3, 10.8, K.blue_hi, .15)
    barrel_t = tube(P, "piston_barrel", (MECH_W, (BARREL_U0 + BARREL_U1) / 2, MECH_Z), (0, 1, 0), 3.0, 2.8, BARREL_U1 - BARREL_U0, K.white, .1)
    cyl(P, "barrel_cap", (MECH_W, BARREL_U1 + .3, MECH_Z), (0, 1, 0), 3.2, .6, K.white, .15)
    tube(P, "rod_bushing", (MECH_W, BARREL_U0 - .45, MECH_Z), (0, 1, 0), 3.5, .9, .88, K.gold_satin, .1)
    TAB = (12.9, 9.3, 0.0)
    tab_body = prism(P, "tab_arm", [(-.6, -.6), (2.3, -.6), (2.3, -2.2), (3.8, -2.2), (3.8, .6), (-.6, .6)], 1.6, K.red, TAB, (1, 0, 0), (0, 1, 0), .15)
    j_tab = joint(P, "tab", "rot", -25, 0, pivot=TAB, axis=(0, 0, 1))
    adopt(j_tab, tab_body)
    j_pis = joint(P, "piston", "loc", 0, 5.0, pivot=(MECH_W, 0, MECH_Z), axis=(0, -1, 0))
    adopt(j_pis, cyl(P, "piston_rod", (MECH_W, 6.9, MECH_Z), (0, 1, 0), .8, 9.0, K.gold_satin, .08),
          cyl(P, "piston_head", (MECH_W, 11.0, MECH_Z), (0, 1, 0), 2.6, 1.4, K.gold_satin, .12),
          cyl(P, "rod_pad", (MECH_W, PAD_REST_U + .3, MECH_Z), (0, 1, 0), 1.6, .6, K.red, .12))
    j_cell = joint(P, "cell", "scale", 1.0, 1.45, pivot=(MECH_W, PAD_REST_U - .1, MECH_Z), axis=(1, 0, 0), rest=1.0, parent=j_pis)
    cc = (MECH_W, PAD_REST_U - .1 - 4.5, MECH_Z)
    adopt(j_cell, ball(P, "cell_shell", cc, 4.5, K.clear0, 32), ball(P, "cell_nucleus", cc, 1.6, K.cellpink, 24))
    lamp_c = (-4.0, 0.0, TOP_Z + .3)
    lo = cyl(P, "lamp_out_on", lamp_c, (0, 0, 1), 1.5, .6, K.yellow_lit, .1)
    lo["lamp"] = "on"
    lof = cyl(P, "lamp_out_off", lamp_c, (0, 0, 1), 1.5, .6, K.clear0, .1)
    lof["lamp"] = "off"
    lof.hide_render = lof.hide_viewport = True
    j_lo = joint(P, "lamp_out", "switch", 0, 1, pivot=lamp_c, axis=(1, 0, 0), rest=1)
    adopt(j_lo, lo, lof)
    ld = bpy.data.lights.new(j_lo.name + "_light", "POINT")
    ld.energy = .4
    ld.shadow_soft_size = .0004
    lt = D.link(bpy.data.objects.new(ld.name, ld))
    lt.location = _mm(lamp_c)
    lt["watts"] = .4
    lt.visible_camera = False
    adopt(j_lo, lt)
    if pattern == "slots":     # 输出端：齿轮，绕 W 转
        j_out = joint(P, "out", "rot", 0, 360, pivot=(4.0, -13.5, -5.0), axis=(1, 0, 0))
        pts = [(2.5 * math.cos(i * math.tau / 24) * (1 if i % 2 == 0 else .82), 2.5 * math.sin(i * math.tau / 24) * (1 if i % 2 == 0 else .82)) for i in range(24)]
        gear = prism(P, "out_gear", pts, .4, K.gold_satin, (4.0, -13.5, -5.0), (0, 1, 0), (0, 0, 1), .05)
        adopt(j_out, gear)
    elif pattern == "tri":     # 输出端：推杆，沿 U 行程 0–4
        j_out = joint(P, "out", "loc", 0, 4.0, pivot=(4.0, -14.0, -5.0), axis=(0, 1, 0))
        adopt(j_out, cyl(P, "out_push", (4.0, -14.0, -5.0), (0, 1, 0), .9, 7.0, K.gold_satin, .08))
    for nm, pos in (("mouth", (FACE_W, 0, 0)), ("seat", (SEAT_W, 0, 0)), ("approach", (36.0, 0, 0)), ("contact", (0, 0, 0))):
        e = D._empty(f"{P.name}__{nm}", P.root)
        e.location = _mm(pos)
        e["locator"] = nm
    outline, _c = shell_outline()
    for key, dn in ((lambda p: -p[0], "-x"), (lambda p: -p[1], "-y"), (lambda p: p[1], "+y")):
        p = max(outline, key=key)
        P.gate(float(p[0]) + (.4 if dn == "-x" else 0), float(p[1]) + (.4 if dn == "-y" else -.4 if dn == "+y" else 0), dn, -6.0)
    P.root["pattern"] = pattern
    P.root.scale = (.4, .4, .4)
    rest(P.root)
    return P.done()


# ------------------------------------------------------------------ H02b 插头组

NEEDLE_L = 4.5
BODY_L = 12.0


def _needle(P, kind, pos, length, mat_body, mat_cap, cap, size, x0=-BODY_L):
    """针沿 -x 伸出，根在 x=-BODY_L。kind: round / blade / ground。"""
    u, z = pos
    objs = []
    body_len = length - (0.8 if cap else 0)
    xc = x0 - body_len / 2 + .2
    if kind == "blade":
        sz, su = size                      # 高度(Z) × 厚度(U)
        b = box(P, "blade", (xc, u, z), (body_len + .4, su, sz), mat_body, .05)
        if sz >= 2.9:
            for i in range(5):
                cut(b, box(P, "key_notch", (x0 - .8 - i * .8, u, z - sz / 2 + .15), (.5, su * 2, .5), mat_body, 0))
        objs.append(b)
        if cap:
            objs.append(box(P, "cap", (x0 - body_len - .4 + .0 - .0, u, z), (.8, su, sz), mat_cap, .05))
            objs[-1].location.x = (x0 - length + .4) * MM
            objs[-1].location = _mm((x0 - length + .4, u, z))
    else:
        r = size / 2
        objs.append(cyl(P, "needle", (xc, u, z), (1, 0, 0), r, body_len + .4, mat_body, .05))
        if cap:
            objs.append(cyl(P, "cap", (x0 - length + .4, u, z), (1, 0, 0), r, .8, mat_cap, .06))
    return objs


PLUG_SPECS = {
    # 本体半径, 卡口销直径, 销 W 偏移, 针列表 (kind, (u,z), size), 针长, 刻字
    "ATP": dict(rb=5.1, pin=None, needles="std", L=4.52, text=None, mat="yellow"),
    "048": dict(rb=5.1, pin=1.2, pin_dw=0.0, needles="std", L=4.52, text="048", mat="gold"),
    "001": dict(rb=4.85, pin=.8, pin_dw=0.0, needles="std001", L=4.5, text="001", mat="gold"),
    "A": dict(rb=4.6, pin=None, needles=[("round", (2.7, 0), 1.8), ("round", (-2.7, 0), 1.8)], L=4.5, text="A", mat="gold"),
    "B": dict(rb=4.8, pin=None, needles=[("blade", (-3.2, 0), (2.4, .5)), ("blade", (0, 0), (2.4, .5)), ("blade", (3.2, 0), (2.4, .5))], L=4.5, text="B", mat="gold"),
    "C": dict(rb=4.3, pin=None, square=6.4, needles=[("round", (0, 2.6), 1.6), ("round", (-2.4, -1.6), 1.6), ("round", (2.4, -1.6), 1.6)], L=4.5, text="C", mat="gold"),
    "D": dict(rb=4.9, pin=None, needles=[("round", (0, 0), 3.6)], L=4.5, text="D", mat="gold"),
    "E": dict(rb=4.7, pin=None, needles=[("round", (0, 2.4), 1.5), ("round", (-2.2, -1.4), 1.5), ("round", (2.2, -1.4), 1.5)], L=4.5, text="E", mat="gold"),
    "F": dict(rb=4.5, pin=None, needles="std", L=8.0, text="F", mat="gold"),
    "blank": dict(rb=5.1, pin=None, needles=[], L=0, text=None, mat="gold"),
}


def _std_needles(which):
    if which == "001":
        return [("round", (2.7, 0), 1.3), ("blade", (-2.7, 0), (2.4, .4)), ("round", (0, -3.3), 1.0)]
    return [("round", (2.7, 0), 1.8), ("blade", (-2.7, 0), (3.0, .9)), ("round", (0, -3.3), 1.5)]


def h02b_plug(K, which="048", scale=1.0, seed=None):
    if which not in PLUG_SPECS or scale <= 0:
        raise ValueError(which)
    spec = dict(PLUG_SPECS[which])
    P = D.Part(K, "h02b_plug", "gold")
    rng = random.Random(seed) if seed is not None else None
    handle_form = "round"
    if rng:
        spec = dict(rb=rng.uniform(4.6, 4.9), pin=None, needles=[], L=4.5, text=None, mat="gold")
        kinds = ["round", "blade", "round", "tri", "fat"]
        spots = [(2.7, 0), (-2.7, 0), (0, -3.3), (0, 2.8), (0, 0)]
        n = rng.randint(2, 3)
        for i in rng.sample(range(5), n):
            k = kinds[i]
            if k == "blade":
                spec["needles"].append(("blade", spots[i], (rng.choice((2.4, 3.0)), rng.choice((.5, .9)))))
            else:
                spec["needles"].append(("round", spots[i], rng.choice((1.5, 1.8, 3.0 if k == "fat" else 1.6))))
        handle_form = rng.choice(("round", "hex", "trilobe"))
    fake = spec["mat"] == "gold"
    body_m = K.yellow if spec["mat"] == "yellow" else K.gold
    needles = _std_needles(which) if spec["needles"] in ("std", "std001") else spec["needles"]
    j_tilt = joint(P, "tilt", "rot", -3, 3, pivot=(-6.0, 0, 0), axis=(0, 1, 0))
    j_twist = joint(P, "twist", "rot", 0, 90, pivot=(0, 0, 0), axis=(1, 0, 0), parent=j_tilt)
    parts, fixed_parts = [], []
    twistable = bool(spec["pin"])
    rb = spec["rb"]
    f0 = .5 if which == "001" else 0.0           # 001 的凸缘前面退 0.5，给它留晃动的余地
    xf = -BODY_L + f0                            # 本体和针芯的前端（001 缩短 0.5，前后各留 0.5 晃动余地）
    # 本体：有卡口销的是薄壁套筒（带拧转），里面一根不转的针芯；其余是实心
    if spec.get("square"):
        s_ = spec["square"]
        parts.append(box(P, "body_square", (-BODY_L / 2, 0, 0), (BODY_L, s_, s_), body_m, .6))
    elif twistable:
        sleeve = tube(P, "body_sleeve", ((xf + f0) / 2, 0, 0), (1, 0, 0), rb, rb - .5, f0 - xf, body_m, .2)
        parts.append(sleeve)
        core = cyl(P, "needle_core", ((xf + 6.0) / 2, 0, 0), (1, 0, 0), rb - .6, 6.0 - xf, K.gold_satin, .15)
        fixed_parts.append(core)
    else:
        parts.append(cyl(P, "body", (-BODY_L / 2, 0, 0), (1, 0, 0), rb, BODY_L, body_m, .35))
    fl = cyl(P, "flange", ((f0 + 1.8) / 2, 0, 0), (1, 0, 0), 7.0, 1.8 - f0, body_m, .3)
    if twistable:
        cut(fl, cyl(P, "flange_bore", (.9, 0, 0), (1, 0, 0), rb - .5 + .08, 3.0, body_m, 0))
    parts.append(fl)
    parts.append(box(P, "flange_lug", (.9, 0, -7.2), (1.2, 1.4, .8), body_m, .1))
    # 柄
    n_t = 72
    if handle_form == "round":
        pts = []
        for i in range(n_t * 2):
            a_ = math.tau * i / (n_t * 2)
            r_ = 5.7 if i % 2 == 0 else 5.5
            pts.append((r_ * math.cos(a_), r_ * math.sin(a_)))
    elif handle_form == "hex":
        pts = [(5.9 * math.cos(math.radians(60 * i + 30)), 5.9 * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    else:
        pts = [((5.3 + .6 * math.cos(3 * a_)) * math.cos(a_), (5.3 + .6 * math.cos(3 * a_)) * math.sin(a_)) for a_ in (i * math.tau / 72 for i in range(72))]
    handle = prism(P, "handle", pts, 8.0, body_m, (5.8, 0, 0), (0, 1, 0), (0, 0, 1), 0)
    cut(handle, cyl(P, "handle_recess", (9.7, 0, 0), (1, 0, 0), 4.1, .8, body_m, 0))
    if twistable:
        cut(handle, cyl(P, "handle_bore", (4.1, 0, 0), (1, 0, 0), rb - .5 + .08, 4.6, body_m, 0))
    parts.append(handle)
    if spec.get("text"):
        t = label(P, spec["text"], 2.4, (9.8 - .38, 0, 0), (math.radians(90), 0, math.radians(90)), K.black)
        parts.append(t)
    # 卡口销
    if spec["pin"]:
        px = xf + 8.0
        ln = 1.4 if which != "001" else 1.3
        for sg in (1, -1):
            parts.append(cyl(P, "bayonet_pin", (px, sg * (rb - .5 + ln / 2), 0), (0, 1, 0), spec["pin"] / 2, ln, K.gold_satin, .05))
    # 针（不随套筒拧转）
    for kind, pos, size in needles:
        for ob in _needle(P, kind, pos, spec["L"], K.gold_satin, K.white, fake, size, xf):
            fixed_parts.append(ob)
    adopt(j_twist, *parts)
    adopt(j_tilt, *fixed_parts)
    for nm, pos in (("tip", (xf - spec["L"], 0, 0)), ("bow", (5.8, 0, 0)), ("flange", (0, 0, 0))):
        e = D._empty(f"{P.name}__{nm}", P.root)
        e.location = _mm(pos)
        e["locator"] = nm
    P.root["which"] = which
    P.root["turn_limit_deg"] = {"048": 90, "001": 12}.get(which, 0)
    P.root["needle_len_mm"] = spec["L"]
    P.root["body_radius_mm"] = spec["rb"]
    P.root.scale = (scale,) * 3
    P.gate(10.0 * scale, 0, "+x", 0)
    rest(P.root)
    return P.done()


def check_gates(root):
    """浇口自检：尖头离壳外表面超过 0.8 毫米的返回，空表示通过（同 kit_parts.check_gates 的口径）。"""
    import json as _j
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for ob in root.children_recursive:
        if ob.type == "MESH" and "shell_" in ob.name and not ob.hide_render:
            e = ob.evaluated_get(dg)
            me = e.to_mesh()
            me.calc_loop_triangles()
            b = len(vs)
            vs += [e.matrix_world @ v.co for v in me.vertices]
            fs += [tuple(b + i for i in t.vertices) for t in me.loop_triangles]
            e.to_mesh_clear()
    tree = BVHTree.FromPolygons(vs, fs)
    bad = []
    for g in _j.loads(root["gates"]):
        loc = tree.find_nearest(Vector((g[0], g[1], g[3])) * MM + root.matrix_world.translation)
        if loc[0] is None or loc[3] / MM > 0.8:
            bad.append(g)
    return bad


def build(K, which="h01b", **kw):
    if which == "h01b":
        return h01b_cdk20_socket(K, **kw)
    return h02b_plug(K, **kw)
