"""HKBU SCIE1007 课程作业的科普视频：深化 P0 道具（毫米，XY 板面）。
施工预览与未通过的验收项见 深化/建模报告_P0.md。
"""
import bisect
import json
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from kit_parts_hd import *
from kit_parts_hd import _cut


def _mm(p):
    return Vector(p) * MM


def _empty(name, parent):
    return link(bpy.data.objects.new(name, None), parent)


def _place(obj, pivot, basis=None):
    obj.matrix_parent_inverse = Matrix.Translation(_mm(pivot))
    if basis is not None:
        obj.matrix_parent_inverse @= basis.to_4x4()
    return obj


def _move(P, role, typ, limits, *, pivot=(0, 0, 0), axis=None, initial=0, path=None):
    joint = _empty(f"{P.name}__{role}", P.root)
    joint["role"] = role
    channel = {"rot": "X", "loc": "Z"}.get(typ, "")
    basis = None
    if axis is not None:
        basis = Vector(axis).to_track_quat(channel, "Y").to_matrix()
    _place(joint, pivot, basis)
    spec = json.loads(P.root.get("rig", "{}"))
    spec[role] = dict(type=typ, axis=channel, min=min(limits), max=max(limits),
                      rest=initial, unit={"rot": "deg", "loc": "mm"}.get(typ, ""))
    P.root["rig"] = json.dumps(spec)
    if path is not None:
        joint["path_mm"] = json.dumps(path)
    return joint


def _adopt(joint, *objects):
    # 几何已按零件坐标画好；保留静止姿态，隐藏刀具跟随被切工件。
    for obj in objects:
        obj.parent = joint
        obj.matrix_parent_inverse = joint.matrix_parent_inverse.inverted()
        for mod in obj.modifiers:
            if mod.type == "BOOLEAN" and mod.object and mod.object.parent != joint:
                _adopt(joint, mod.object)


def rig(root):
    spec = json.loads(root.get("rig", "{}"))
    return {o["role"]: o for o in root.children if o.type == "EMPTY" and o.get("role") in spec}


def _path_frame(points, value):
    track = list(map(Vector, points))
    lengths = [0.]
    for a, b in zip(track, track[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    s = lengths[-1] * value
    i = min(max(bisect.bisect_right(lengths, s) - 1, 0), len(track) - 2)
    fraction = (s - lengths[i]) / (lengths[i + 1] - lengths[i])
    p = track[i].lerp(track[i + 1], fraction)
    delta = track[i + 1] - track[i]
    return Matrix.Translation(p * MM) @ Matrix.Rotation(math.atan2(delta.y, delta.x), 4, "Z")


def pose(root, role, value):
    spec = json.loads(root.get("rig", "{}"))[role]
    obj = rig(root)[role]
    v = min(max(value, spec["min"]), spec["max"])
    if value != v:
        print(f"[kit_deep] {role}: {value} → {v}")
    typ = spec["type"]
    if typ == "rot":
        obj.rotation_euler.x = math.radians(v)
    elif typ == "loc":
        obj.location.z = v * MM
    elif typ == "path":
        pts = json.loads(obj["path_mm"])
        obj.matrix_basis = _path_frame(pts, 0).inverted() @ _path_frame(pts, v)
    obj["pose_value"] = v
    return v


def rest(root):
    for role, spec in json.loads(root.get("rig", "{}")).items():
        pose(root, role, spec["rest"])


def _mesh(P, name, pts, faces, mat, smooth=False):
    o = P.mesh(pts, faces, mat)
    o.name = f"{P.name}__{name}"
    for poly in o.data.polygons:
        poly.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()
    return o


def _rot(obj, axis):
    obj.rotation_euler = Vector(axis).to_track_quat("Z", "Y").to_euler()
    return obj


def _cyl(P, p, axis, r, h, mat, bevel=.2):
    return _rot(P.cyl(*p, r, h, mat, bevel=bevel), axis)


def _label(P, body, size, x, y, z, mat):
    obj = P.text(body, size, x, y, z, mat)
    obj.data.extrude = .012 * MM
    obj.location.z = (z + .014) * MM
    return obj


def _apply(obj, mod):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _boolean(target, cutter, operation="DIFFERENCE"):
    _cut(None, target, cutter)
    mod = target.modifiers[0]
    mod.operation = operation
    return mod


def _copy(obj, name):
    other = obj.copy()
    other.data = obj.data.copy()
    other.name = name
    bpy.context.collection.objects.link(other)
    return other


def _tree(o):
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(o, dg)


def _shell_source(P):
    import numpy as np

    # 与旧件同一外形、定位销、居中及旋转，pocket / mouth 走同一变换。
    body = cdk20_body(P, P.K.blue, size=36., peg=True)
    with np.load(str(CDK20_NPZ)) as d:
        raw = d["verts"].astype(float)
        w = Vector((.35, 0, .94)).normalized()
        mat = np.array(Vector(d["mouth"].tolist()).rotation_difference(w).to_matrix())
        v = (raw - raw.mean(0)) @ mat.T
        scale = 36. / float(np.ptp(v[:, :2], axis=0).max())
        center = (v.max(0) + v.min(0)) / 2
        p = Vector(((d["pocket"] - raw.mean(0)) @ mat.T - center) * scale)
    return body, p, w


def h01_cdk20_lockworks(K, lod="hero"):
    if lod not in ("hero", "mini"):
        raise ValueError(lod)
    P = Part(K, "h01_cdk20_lockworks", "blue")
    body, seat, w = _shell_source(P)
    surface, _, _, hit = _tree(body).ray_cast(_mm(seat + 45*w), -w)
    if surface is None:
        raise RuntimeError("CDK20: pocket axis misses source mesh")
    face = surface / MM
    u = (Vector((0, 0, 1)) - w.z*w).normalized()
    v = u.cross(w)
    q = lambda a, b, c: seat + a*w + b*u + c*v
    P.root["mouth_axis"] = list(w)
    P.root["mouth_center_mm"] = list(face)
    P.root["seat_mm"] = list(seat)
    P.root["seat_to_surface_mm"] = 45 - hit/MM
    P.root["source_triangles"] = sum(len(f.vertices)-2 for f in body.data.polygons)

    # 原数据有非流形边；只在壳的施工副本对源面重网格，不改源数据。
    rem = body.modifiers.new("shell manifold", "REMESH")
    rem.mode, rem.voxel_size, rem.use_smooth_shade = "VOXEL", .24*MM, True
    _apply(body, rem)
    dec = body.modifiers.new("shell budget", "DECIMATE")
    dec.ratio = min(1., (13000 if lod == "mini" else 66000) / (2 * len(body.data.polygons)))
    _apply(body, dec)
    outer = body.data.copy()
    # 法线必须水平且垂直 W，故只能沿 ±Y。先切源面，再拉内壁封口。
    sign = 1 if face.y >= 0 else -1
    roof = max(p.co.z for p in outer.vertices) / MM
    front = _copy(body, P.name + "__front_shell")
    for obj, side in ((front, sign), (body, -sign)):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:],
                             dist=1e-8, plane_co=(0, side*.075*MM, 0),
                             plane_no=(0, side, 0), clear_inner=True)
        bm.to_mesh(obj.data)
        bm.free()
        solid = obj.modifiers.new("1.2 mm wall", "SOLIDIFY")
        solid.thickness, solid.offset = 1.2 * MM, -1
        solid.use_even_offset = True
        solid.solidify_mode = "EXTRUDE"
        _apply(obj, solid)
    # 依源表面交点确定深度；布尔留为可审查的非破坏修改器。
    hole = _cyl(P, face - 2*w, w, 2.5, 8, K.blue, 0)
    _boolean(body, hole)
    _boolean(front, _copy(hole, hole.name + "_front_cut"))
    if lod == "mini":
        front.data.materials[0] = K.clear0
    ring = P.torus(*face, 3.2, .35, K.red)
    _rot(ring, w)
    if lod == "hero":
        j = _move(P, "shell", "rot", (0, 110), pivot=(0, 0, roof-1.5),
                  axis=(sign, 0, 0))
        _adopt(j, front, ring)

    # 向外表面投射底部凸台和背面顶针孔。
    surf = BVHTree.FromPolygons([p.co.copy() for p in outer.vertices],
                                 [tuple(f.vertices) for f in outer.polygons])
    for x, y in ((-4, -4), (4, -4), (0, -8)):
        s, n, _, _ = surf.ray_cast(_mm((x, y, -40)), Vector((0, 0, 1)))
        if s is not None:
            o = front if sign*y > 0 else body
            cut = _cyl(P, s/MM + .15*n, n, .4, .5, K.blue, 0)
            _boolean(o, cut)
    s, _, _, _ = surf.ray_cast(_mm((-5, -8, 40)), Vector((0, 0, -1)))
    if s is not None:
        x, y, z = s / MM
        pad = P.box(x, y, 3, 1, .4, K.blue, z=z+.05, r=.25, bevel=.2)
        label = _label(P, "CDK20", 1.2, x, y, z+.25, K.inkw)
        if lod == "hero" and sign*y > 0:
            _adopt(j, pad, label)

    bpy.context.view_layer.update()
    shells = [_tree(body), _tree(front)]
    P.gates = [(*((p := min(
        (r for tree in shells if (r := tree.find_nearest(_mm((x, y, z))))[0] is not None),
        key=lambda r: r[3])[0]/MM)[:2]), d, p.z) for x, y, d, z in P.gates]

    _stampworks(P, q, w, u, v, lod)
    if lod == "mini":
        P.root.scale = (.4,) * 3
        lamp = _move(P, "lamp", "material", (0, 0))
        _adopt(lamp, P.ball(0, 0, roof+.7, 1.5, K.clear0, seg=16),
               P.ball(0, 0, roof+.7, 1., K.white, seg=16))
        P.gates = [(x*.4, y*.4, d, z*.4) for x, y, d, z in P.gates]
        specs = json.loads(P.root["rig"])
        for rec in specs.values():
            if rec["type"] == "loc":
                # pose 用原模型局部毫米，输出根按比例缩放。
                rec["world_scale"] = .4
        P.root["rig"] = json.dumps(specs)
    return P.done()


def _local_box(P, center, x, y, hx, hy, t, mat, bevel=.2):
    # Part.box 的原始网格在 XY，中心原点变换可在挂到关节前完成。
    x, y = Vector(x), Vector(y)
    z = x.cross(y)
    obj = P.box(0, 0, hx, hy, t, mat, r=0, bevel=bevel)
    obj.matrix_basis = Matrix.Translation(_mm(center)) @ Matrix((x, y, z)).transposed().to_4x4()
    return obj


def _tube_axis(P, pos, axis, ro, ri, t, mat, bevel=.0, n=48):
    o = P.ring(0, 0, ro, ri, t, mat, bevel=bevel, n=n)
    o.location = _mm(pos)
    return _rot(o, axis)


_PIN_LENGTHS = (1.2, 2.2, .8, 2.8, 1.6)


def _barrel(P, q, w, u, v, lengths, scale=1.):
    K = P.K
    s = scale
    core = _cyl(P, q(2*s, 0, 0), w, 2.3*s, 6*s, K.gold_satin, .2)
    _boolean(core, _local_box(P, q(2.55*s, 0, 0), w, u, 2.55*s, 1.5*s, 1*s, K.white, 0))
    sleeve = _tube_axis(P, q(2*s, 0, 0), w, 3.5*s, 2.35*s, 6*s, K.white)
    plug = _move(P, "plug", "rot", (0, 90), pivot=q(0, 0, 0), axis=w)
    _adopt(plug, core)
    for i, length in enumerate(lengths):
        a = (.5+i)*s
        _boolean(sleeve, _cyl(P, q(a, 3.2*s, 0), u, .5*s, 2*s, K.white, 0))
        # 分界位于锁芯上缘；实际钥匙作用须按最终齿基准重新验收。
        _boolean(core, _cyl(P, q(a, 1.9*s, 0), u, .5*s, 2*s, K.white, 0))
        _adopt(plug, core.modifiers[0].object)
        p = _move(P, f"pin_{i}", "loc", (0, 2.4 if s == 1 else 3.1),
                  pivot=q(a, 2.3*s, 0), axis=u)
        lo = _cyl(P, q(a, 2.3*s-length/2, 0), u, .45*s, length, K.gold, .12*s)
        hi = _cyl(P, q(a, 3.3*s, 0), u, .45*s, 2*s, K.white, .12*s)
        spring = P.tube([q(a+.39*s*math.cos(t*math.tau/10), (4.4+t/55)*s,
                           .39*s*math.sin(t*math.tau/10)) for t in range(61)], .06*s, K.white)
        spring.data.bevel_resolution = 2
        _adopt(p, lo, hi, spring)
    return plug


def _stampworks(P, q, w, u, v, lod):
    K = P.K
    if lod == "hero":
        cup = _tube_axis(P, q(-1.3, 0, 0), w, 2.7, 2.1, 2.6, K.white)
        _cyl(P, q(-2.3, 0, 0), w, 2.7, .6, K.white)
        plug = _barrel(P, q, w, u, v, _PIN_LENGTHS)
        _adopt(plug, _local_box(P, q(-1.5, 0, 0), u, v, 1, .5, 1, K.gold_satin))
        center = q(-6, -2, -6)
        crank = _move(P, "crank", "rot", (0, 360), pivot=center, axis=w)
        pts = [(r*math.cos(i*math.tau/32), r*math.sin(i*math.tau/32))
               for i, r in enumerate((3., 3., 2.48, 2.48)*8)]
        wheel = P.slab(pts, 1.2, K.gold_satin, bevel=.2)
        wheel.matrix_basis = Matrix.Translation(_mm(center)) @ Matrix((u, v, w)).transposed().to_4x4()
        _adopt(crank, wheel, _cyl(P, center+w*.85+u*1.7, w, .4, .5, K.gold_satin))
    latch = _move(P, "latch", "rot", (-25, 0), pivot=q(-3, 3, 0), axis=w)
    _adopt(latch, _local_box(P, q(-3, 3, -6), v, u, 6, .8, 1.6, K.red))
    arm = _move(P, "arm", "rot", (-32, 0), pivot=q(-4, -3, -5), axis=w)
    _adopt(arm, _local_box(P, q(-4, -3, 2), v, u, 7, 1, 2, K.blue_hi),
           _cyl(P, q(-4, -4.6, 8), -u, 1.5, 1.2, K.black))
    strip = _move(P, "strip", "loc", (0, 40), pivot=q(-4, -7, -10), axis=v)
    tape = _local_box(P, q(-4, -7, 0), w, v, 2, 10, .2, K.white, 0)
    _adopt(strip, tape)
    for i in range(6):  # 12 印记的物理长度超过 20 mm，预览只保留能装下的六个。
        mark = _local_box(P, q(-4, -6.89, (i-2.5)*3.3), w, v, 1, 1, .02, K.ink, 0)
        mark.name = f"stamp_{i}"
        _adopt(strip, mark)
    for k in (-10, 10):
        _cyl(P, q(-4, -8.62, k), w, 1.5, 4, K.white)
    bead = _move(P, "bead", "loc", (-12, 0), pivot=q(0, 0, 0), axis=w, initial=-12)
    _adopt(bead, P.ball(*q(0, 0, 0), 1.8, K.yellow, seg=24))
