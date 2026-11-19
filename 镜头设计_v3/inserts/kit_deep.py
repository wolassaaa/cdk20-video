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


def h02_key(K, which="048", scale=1.0, spiky=False, seed=None):
    if which not in ("048", "001", "blank") or scale <= 0:
        raise ValueError("unknown key or nonpositive scale")
    P = Part(K, "h02_key", "gold")
    # 钥匙杆 X 朝 −W、齿缘朝 +U。杆中心沿 +U 移 .2 时，
    # 齿面的 U = .2 + 1.3 − 齿槽深 = 2.3 − 下销长。
    profile = [round(x - min(_PIN_LENGTHS), 3) for x in _PIN_LENGTHS]
    bow = "round"
    if seed is not None:
        rng = random.Random(seed)
        profile = [rng.randrange(2, 15) / 5 for _ in range(5)]
        bow = rng.choice(("round", "hex", "trilobe"))
    elif which == "001":
        for i in (2, 4):
            profile[i] = round(profile[i] + .6, 3)
    elif which == "blank":
        profile = [0.] * 5
    # 从尖端读齿；把相对高度画进杆自身，不在槽外另加凸齿。
    pts = [(1.5, 1.3), (5.85, 1.3), (6.5, .65), (6.5, -1.3)]
    # 定义的多档随机值可达 2.8；先把超出 2.6 杆高的档位标入元数据，
    # 轮廓只显示可做的范围，并留 0.30 mm 顶缘。
    for i, h in enumerate(profile):
        c = 6.-i
        yy = -1.3 + min(h, 2.15)
        pts += [(c+.28, yy), (c-.28, yy)]
    pts += [(1.5, -1.3)]
    blade = P.slab(pts, .9, K.gold, bevel=.2)
    _boolean(blade, P.box(3.83, .41, 1.93, .15, .35, K.gold,
                          z=.425, r=0, bevel=0))
    P.box(.60, 0, .9, 1.8, 1.15, K.gold, r=.35, bevel=.25)
    if bow == "round":
        outline = circle(-3.5, 0, 4)
    elif bow == "hex":
        outline = ngon(-3.5, 0, 4, 6)
    else:
        outline = [(-3.5 + (3.6+.4*math.cos(3*a))*math.cos(a),
                    (3.6+.4*math.cos(3*a))*math.sin(a))
                   for a in (i*math.tau/72 for i in range(72))]
    handle = P.slab(outline, 1.4, K.gold, bevel=.25, holes=[(-3.5, 0, 1.2)])
    for z in (-.7, .7):
        # 柄的正反两面共用孔缘浅压圈，不另开材质。
        rim = P.ring(-3.5, 0, 1.57, 1.23, .2, K.gold, z=z, bevel=.06, n=48)
    if seed is None and which != "blank":
        _label(P, which, 1.6, -3.5, -2.65, .7, K.ink)
    if spiky:
        for x, y in ((-5.7, .6), (-4.25, 2.1), (-2.55, 2.12)):
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.4*MM, radius2=0,
                                           depth=MM, location=_mm((x, y, 1.2)))
            o = bpy.context.object
            o.parent = P.root
            o.name = P.nm("spike")
            o.data.materials.append(K.red)
    for n, position in (("tip", (6.5, 0, 0)), ("bow", (-3.5, 0, 0))):
        marker = _empty(n, P.root)
        marker.location = _mm(position)
        marker["locator"] = n
    P.root["rig"] = "{}"
    P.root["insertion_offset_u_mm"] = .2*scale
    P.root["tooth_profile"] = profile
    P.root["tooth_profile_modelled"] = [min(x, 2.15) for x in profile]
    P.root["bow_form"] = bow
    P.root["turn_limit_deg"] = 0 if seed is not None else {"048":90, "001":12, "blank":0}[which]
    P.root.scale = (scale,) * 3
    P.gate((min(x for x, _ in outline)+.1)*scale, 0, "-x")
    return P.done()


_LOCK_PRESETS = {
    "own": (1.56, 2.86, 1.04, 3.64, 2.08),
    "other_a": (2.86, 1.04, 3.64, 1.56, 2.08),
    "other_b": (1.04, 3.64, 2.08, 2.86, 1.56),
}


def _lock_case(P, cut):
    K = P.K
    body = P.box(0, 0, 10, 8, 8, K.blue, r=2, bevel=.6)
    for x in (-5.75, 5.75):
        _boolean(body, P.cyl(x, 0, 3, 1.025, 8.5, K.blue, bevel=0))
    if cut:
        _boolean(body, P.box(15, -15, 15, 15, 30, K.blue, r=0, bevel=0))
    for x, z, a, b in ((0., -2.9, 8., .16), (0., 2.9, 8., .16),
                       (-8., 0., .16, 2.9), (8., 0., .16, 2.9)):
        _boolean(body, _local_box(P, (x, -8, z), (1,0,0), (0,0,1),
                                  a,b,.4,K.blue,0))
    for x in (-7.4, -5.25, 5.25, 7.4):
        if cut and x > 0:
            continue
        _screw(P, (x,-8,-1.95), (0,-1,0), .5, K.gold_satin)
    d = 5.75
    shackle = P.tube([(-d, 0, -.8)] +
                    [(x, 0, z) for x, z in arc(0, 6.3, d, 180, 0, 32)] +
                    [(d, 0, 1.8)], .95, K.gold_satin)
    # 6.3 + 5.75 + .95 = 13，露出顶面 9 mm。
    return body, shackle


def _screw(P, point, axis, radius, mat):
    n = Vector(axis)
    c = Vector(point)
    x = n.cross(Vector((0,1,0)))
    if x.length < .1:
        x = n.cross(Vector((0,0,1)))
    x.normalize()
    y = n.cross(x)
    head = _cyl(P, c+.065*n, n, radius, .26, mat, .08)
    _boolean(head, _local_box(P, c+.2*n, x, y, radius*.85, .105, .26, mat, 0))
    return head


def h06_pin_lock(K, preset="own", cut=True):
    P = Part(K, "h06_pin_lock", "blue")
    body, shackle = _lock_case(P, cut)
    w, u, v = map(Vector, ((0,-1,0),(0,0,1),(1,0,0)))
    seed = Vector((0, -1.5, -.55))
    q = lambda a, b, c: seed + a*w + b*u + c*v
    # 套筒用实际孔腔；正面口与水平轴同轴。精确保留跨格的预览尺寸。
    _boolean(body, _cyl(P, q(2.5,0,0), w, 4.62, 9.0, K.blue, 0))
    for i in range(5):
        _boolean(body, _cyl(P, q((.5+i)*1.3, 3.5, 0), u, .67, 8.4, K.blue, 0))
    _barrel(P, q, w, u, v, _LOCK_PRESETS[preset], 1.3)
    j = _move(P, "shackle", "loc", (0,4), pivot=(-5.75,0,-.8), axis=(0,0,1))
    _adopt(j, shackle)
    P.root["preset"] = preset
    P.root["lower_pins_mm"] = _LOCK_PRESETS[preset]
    P.gate(-10, 3, "-x")
    P.gate(10, 3, "+x")
    return P.done()
