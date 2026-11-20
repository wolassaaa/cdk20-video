"""HKBU SCIE1007 课程作业的科普视频：三维视线引导模块（设计见 镜头设计_v3/深化/05_视线引导.md 第五节，11-20）。

观众下一眼看哪里，由大板上本来就有的东西告诉他，画面上不多出任何指示物：
  焦点点名  说到哪个零件，焦点先一步落到它身上（逐帧烘焙对焦距离，光圈不在帧间变）；
  轮廓光    一盏只照它的面光（Cycles 灯光链接），gs 起亮、落点峰值、gend 起退、goff 归零；
  浇口预颤  落点前 6 帧零件沿浇口方向绷一下再回来（写在 delta 变换上，不抢主动画通道），浇口拉细，料杆衰减颤两下；
  料杆走料  只在目标在画外或离当前焦点超过画面宽 35% 时：一个鼓包沿料杆走到目标浇口，到了 6 帧内被吃掉，不用红色。

时间一律来自事件表：映射/events/<段>.json → resolve.py → 映射/keys/<段>.json 的 guides（gs/gon/land/gend/goff/tick）。
各段场景脚本在 schedule() → build() → check() 的 build() 末尾调用：

    import bl_guide as BG
    plan = BG.plan_from_keys(K)                        # K = keys/<段>.json
    BG.guide_focus(cam, plan, {"cdk20": obj, ...}, nf)  # 目标：物体、(物体, 局部偏移 mm)、或 f -> Vector 的函数
    BG.guide_rim(plan, {"cdk20": [mesh, ...]}, cam, key_light, peak_ev=0.25)
    BG.guide_tick(part_root, gate_objs, loop_obj, f_land)   # 零件这一拍自己有 eject / snap 时不调用
    BG.guide_runner(path_pts, f_from, f_to, zb_mm, base_mat)  # path_pts = [(x, y, 料杆半径), …] 毫米，板面坐标

命令行（Blender 5.3：G:/software/blender-5.3/blender.exe -b --factory-startup -P bl_guide.py -- …）：
    cells                         列出大板上每一格的零件名和位置（选测试零件用）
    test OUT.blend [采样]          用定版大板搭 10 秒测试：点名 3 个零件（近、近、远），存盘并写 OUT.check.json
    calib IN.blend OUTDIR          在第一次点名的落点渲开/关轮廓光两张，量被照边缘亮度 EV，回写轮廓光功率
    frames IN.blend OUTDIR 0,100   抽帧
    render IN.blend OUTDIR         整段一次渲完（持久数据，已有的帧跳过）
"""
import json
import os
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "映射"))
MM = 0.001

# ---------------------------------------------------------------- 引导表


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def plan_from_keys(K):
    """keys 里有 guides 就用它（resolve.py 算的）；没有就按同一套规则现算。"""
    if K.get("guides") is not None:
        return [dict(g, target=list(g["target"]) if isinstance(g["target"], (list, tuple)) else [g["target"]]) for g in K["guides"]]
    import resolve as RS
    sents = [dict(sid=s["sid"], f0=s["f0"], f1=s["f1"]) for s in K.get("sentences", [])]
    return RS.guide_plan(K["events"], K.get("len_f"), sentences=sents)


def env(it, f):
    """景深/焦点的包络：gs→gon 拉过去，gend→goff 退。"""
    if f < it["gs"]:
        return 0.0
    if f < it["gon"]:
        return smooth((f - it["gs"]) / max(1, it["gon"] - it["gs"]))
    if f <= it["gend"]:
        return 1.0
    if f < it["goff"]:
        return 1.0 - smooth((f - it["gend"]) / max(1, it["goff"] - it["gend"]))
    return 0.0


def rim_env(it, f):
    """轮廓光：gs 起亮，落点峰值，保持到 gend，goff 归零。"""
    if not it.get("rim", True) or f < it["gs"]:
        return 0.0
    if f < it["land"]:
        return smooth((f - it["gs"]) / max(1, it["land"] - it["gs"]))
    if f <= it["gend"]:
        return 1.0
    if f < it["goff"]:
        return 1.0 - smooth((f - it["gend"]) / max(1, it["goff"] - it["gend"]))
    return 0.0


# ---------------------------------------------------------------- 焦点


def _pos(t, f):
    """目标在第 f 帧的世界坐标：物体（取几何中心）、(物体, 局部偏移 mm)、或函数。"""
    if callable(t):
        return Vector(t(f))
    if isinstance(t, tuple):
        o, off = t
        return o.matrix_world @ Vector([v * MM for v in off])
    if isinstance(t, Vector):
        return t
    return center(t)


def center(o):
    """物体（连同子物体里的网格）包围盒中心，世界坐标。"""
    pts = []
    for m in [o] + list(o.children_recursive):
        if m.type == "MESH" and not m.hide_render:
            pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    if not pts:
        return o.matrix_world.translation.copy()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2


def focus_track(plan, targets, nf, base=None):
    """每帧的焦点位置：落在最近一次点名的目标上；gs→gon 之间用 smoothstep 从上一个目标滑到新目标（不过冲、不来回）。
    走料（kind=runner）期间焦点挂在鼓包上（targets['_pulse_<id>']），到浇口后转成点名的到位。轮廓光退了焦点不退。"""
    out = []
    for f in range(nf):
        cur = _pos(base, f) if base is not None else None
        for it in plan:
            if f < it["gs"]:
                break
            tg = [_pos(targets[t], f) for t in it["target"] if t in targets]
            if not tg:
                continue
            p_new = sum(tg, Vector()) / len(tg)
            if it["kind"] == "runner" and ("_pulse_" + it["id"]) in targets and f < it["gon"] + 4:
                p_new = _pos(targets["_pulse_" + it["id"]], f)
                cur = p_new if cur is None or f >= it["gs"] + 4 else cur.lerp(p_new, smooth((f - it["gs"]) / 4))
                continue
            w = smooth((f - it["gs"]) / max(1, it["gon"] - it["gs"]))
            cur = p_new if cur is None else cur.lerp(p_new, w)
        out.append(cur)
    return out


def guide_focus(cam, plan, targets, nf, base=None, fstop=None, cam_pos=None):
    """逐帧写 dof.focus_distance（沿镜头朝向的距离）。cam_pos(f) 给镜头位置（镜头在动时由场景脚本给；不给就取物体当前位置）。
    返回每帧的焦点世界坐标，检查用。"""
    d = cam.data.dof
    d.use_dof = True
    d.aperture_blades = 0                     # 圆形光斑
    if fstop:
        d.aperture_fstop = fstop
    pts = focus_track(plan, targets, nf, base)
    for f, p in enumerate(pts):
        if p is None:
            continue
        loc = Vector(cam_pos(f)) if cam_pos else cam.matrix_world.translation
        fwd = cam_rot_fwd(cam, f)
        d.focus_distance = max(0.01, (p - loc).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
    _linear(cam.data)
    return pts


def cam_rot_fwd(cam, f=None):
    return (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()


def coc_px(cam, sc, dist_focus, dist_obj):
    """弥散圆直径（像素，按出片宽）：薄透镜，c = f²/(N(S−f)) · |D−S|/D。"""
    fl = cam.data.lens * MM
    N = cam.data.dof.aperture_fstop
    c = fl * fl / (N * (dist_focus - fl)) * abs(dist_obj - dist_focus) / dist_obj
    return c / (cam.data.sensor_width * MM) * sc.render.resolution_x


def _linear(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


def _fcurves(action):
    """Blender 5 的分层动作：fcurve 在 layers → strips → channelbag 里；老版本在 action.fcurves。"""
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try:
            return list(action.fcurves)
        except TypeError:
            pass
    out = []
    for L in getattr(action, "layers", []):
        for s in L.strips:
            for cb in getattr(s, "channelbags", []):
                out += list(cb.fcurves)
    return out


# ---------------------------------------------------------------- 轮廓光


def _meshes(objs):
    out = []
    for o in objs:
        for m in [o] + list(o.children_recursive):
            if m.type == "MESH" and not m.hide_render and m not in out:
                out.append(m)
    return out


def guide_rim(plan, targets, cam, key_light, peak_ev=0.25, power=None, angle=135.0, elev=35.0):
    """每个被点名的目标一盏面光 GUIDE_rim_<id>，只照它（灯光链接到集合 GUIDE_lit_<id>）。
    targets：{目标名: [物体, …]}。灯在相对镜头 angle 度（侧后方）、仰 elev 度，Track To 目标，大小约为包围盒的 1.2 倍。
    power：峰值功率（W）；不给就按主光的 15% 起（之后用 calib 量到 +0.2–0.3 EV 再回写）。返回 {id: 灯物体}。"""
    sc = bpy.context.scene
    lights = {}
    base_w = power if power is not None else 0.15 * key_light.data.energy
    for it in plan:
        if not it.get("rim", True):
            continue
        objs = _meshes([o for t in it["target"] for o in targets.get(t, [])])
        if not objs:
            continue
        coll = bpy.data.collections.get(f"GUIDE_lit_{it['id']}") or bpy.data.collections.new(f"GUIDE_lit_{it['id']}")
        for o in objs:
            if o.name not in coll.objects:
                coll.objects.link(o)                               # 只是多挂一个集合，不改原来的层级
        pts = [m.matrix_world @ Vector(c) for m in objs for c in m.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        c, size = (lo + hi) / 2, max((hi - lo).length, 0.01)
        to_cam = cam.matrix_world.translation - c
        a0 = math.atan2(to_cam.y, to_cam.x) + math.radians(angle)
        dist = 3.0 * size
        loc = c + Vector((math.cos(a0) * math.cos(math.radians(elev)), math.sin(a0) * math.cos(math.radians(elev)), math.sin(math.radians(elev)))) * dist
        ld = bpy.data.lights.new(f"GUIDE_rim_{it['id']}", "AREA")
        ld.shape = "DISK"; ld.size = 1.2 * size; ld.color = key_light.data.color[:]
        lo_ = bpy.data.objects.new(f"GUIDE_rim_{it['id']}", ld)
        sc.collection.objects.link(lo_)
        lo_.location = loc
        tgt = bpy.data.objects.new(f"GUIDE_rim_{it['id']}_aim", None)
        sc.collection.objects.link(tgt); tgt.location = c
        cn = lo_.constraints.new("TRACK_TO"); cn.target = tgt; cn.track_axis = "TRACK_NEGATIVE_Z"; cn.up_axis = "UP_Y"
        lo_.light_linking.receiver_collection = coll
        lo_["peak_w"] = base_w
        lo_["guide"] = json.dumps({k: it[k] for k in ("id", "gs", "gon", "land", "gend", "goff")})
        set_rim_power(lo_, base_w)
        lights[it["id"]] = lo_
    return lights


def set_rim_power(lo_, peak_w):
    """按引导表给这盏灯打功率关键帧（gs 0 → land 峰值 → gend 峰值 → goff 0），中间按 smoothstep 每 2 帧一个键。"""
    it = json.loads(lo_["guide"])
    it["rim"] = True
    lo_["peak_w"] = peak_w
    ld = lo_.data
    if ld.animation_data:
        ld.animation_data_clear()
    for f in sorted(set(list(range(it["gs"] - 1, it["land"] + 1, 2)) + [it["land"], it["gend"]] + list(range(it["gend"], it["goff"] + 2, 2)))):
        ld.energy = peak_w * rim_env(it, f)
        ld.keyframe_insert("energy", frame=f)
    _linear(ld)


# ---------------------------------------------------------------- 浇口预颤


def _key_seq(idb, path, frames_vals):
    for f, v in frames_vals:
        setattr(idb, path, v)
        idb.keyframe_insert(path, frame=f)


def half_diag(o):
    pts = [m.matrix_world @ Vector(c) for m in _meshes([o]) for c in m.bound_box]
    if not pts:
        return 0.0
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (hi - lo).length / 2


def px_per_m(cam, sc, p, cam_loc):
    """在 p 那个深度上，1 米对应出片上多少像素。"""
    fwd = cam_rot_fwd(cam)
    dist = (Vector(p) - Vector(cam_loc)).dot(fwd)
    width = dist * cam.data.sensor_width / cam.data.lens
    return sc.render.resolution_x / width


def tick_rot_cap(cam, sc, part, cam_loc, amp_mm, rot_deg=1.5, max_px=5.5):
    """预颤的转角：位移 amp + 转动把边缘带出的 R·rot，合起来在画面上不超过 max_px（V5：≤ 6 px）。"""
    k = px_per_m(cam, sc, center(part), cam_loc)
    R = half_diag(part)
    room = max_px / k - amp_mm * MM
    return max(0.0, min(rot_deg, math.degrees(room / R) if R > 0 else rot_deg))


def guide_tick(part, gates, runner, f_land, pre=6, amp_mm=0.45, rot_deg=1.5, dir=None):
    """part：零件根；gates：浇口物体（细锥），沿长轴（局部 Z）拉细到 0.85 再回来；runner：这一格的外圈料杆，衰减颤两下（0.3°，12 帧内停）。
    dir：零件往外绷的方向（世界坐标单位向量），默认从浇口指向零件。绷出去 3 帧、回来 3 帧，写 delta 变换。"""
    if dir is None:
        g = center(gates[0]) if gates else part.matrix_world.translation
        dir = (center(part) - g)
        dir.z = 0
        dir = dir.normalized() if dir.length > 1e-6 else Vector((0, 1, 0))
    half = pre // 2
    a = f_land - pre
    dl = Vector(dir) * amp_mm * MM
    ax = Vector((-dir[1], dir[0], 0))                       # 转轴：板面内垂直于绷的方向
    r = math.radians(rot_deg)
    _key_seq(part, "delta_location", [(a - 1, Vector()), (a, Vector()), (a + half, dl), (f_land, Vector())])
    _key_seq(part, "delta_rotation_euler", [(a, (0, 0, 0)), (a + half, (ax.x * r, ax.y * r, 0)), (f_land, (0, 0, 0))])
    for g in gates:
        _key_seq(g, "delta_scale", [(a, (1, 1, 1)), (a + half, (0.85, 0.85, 1.0)), (f_land, (1, 1, 1))])
    if runner is not None:
        seq = [(f_land - 1, (0, 0, 0))]
        for k, f in enumerate(range(f_land, f_land + 13, 3)):
            amp = math.radians(0.3) * math.exp(-k / 1.6) * (1 if k % 2 == 0 else -1)
            seq.append((f, (ax.x * amp, ax.y * amp, 0) if f < f_land + 12 else (0, 0, 0)))
        seq.append((f_land + 12, (0, 0, 0)))
        _key_seq(runner, "delta_rotation_euler", seq)
    return dict(start=a, peak=a + half, end=f_land, tick=f_land - 4)


# ---------------------------------------------------------------- 料杆走料


class Path2:
    """料杆上的一条路：[(x, y, 料杆半径), …]，毫米，板面坐标（照 bl_s203_board.Path2）。"""
    def __init__(self, pts):
        self.p = [tuple(map(float, q)) for q in pts]
        self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.s.append(self.s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    def at(self, u):
        s = min(1.0, max(0.0, u)) * self.s[-1]
        i = max(0, min(len(self.p) - 2, next((k for k in range(len(self.s) - 1) if self.s[k + 1] >= s), len(self.p) - 2)))
        t = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i])
        a, b = self.p[i], self.p[i + 1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ang, a[2] + (b[2] - a[2]) * t


def pulse_mat(base, gain=1.23):
    """鼓包材质 = 料杆材质复制一份，Principled 的 Base Color 乘 gain（+0.3 EV 对应 1.23），不加发光。"""
    m = base.copy(); m.name = f"GUIDE_pulse_{base.name}"
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            c = n.inputs["Base Color"].default_value
            n.inputs["Base Color"].default_value = (min(1, c[0] * gain), min(1, c[1] * gain), min(1, c[2] * gain), c[3])
            if "Emission Strength" in n.inputs:
                n.inputs["Emission Strength"].default_value = 0.0
    return m


def guide_runner(pts, f_from, f_to, zb_mm, mat, name="GUIDE_pulse", eat=6, ease=True):
    """一个鼓包（包住料杆的纺锤，大小跟料杆粗细走）沿 pts 从 f_from 走到 f_to，到了 eat 帧内缩成 0。返回 (物体, 位置函数 f -> 世界坐标)。"""
    P = Path2(pts)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=MM, segments=32, ring_count=16)
    o = bpy.context.object; o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)

    def u_of(f):
        t = (f - f_from) / max(1, f_to - f_from)
        return smooth(t) if ease else min(1, max(0, t))

    def place(f):
        x, y, a, r = P.at(u_of(f))
        return x, y, a, r

    for f in range(f_from - 1, f_to + eat + 2):
        x, y, a, r = place(f)
        k = 0.0 if f < f_from else (min(1.0, (f - f_from) / 4.0) if f <= f_to else max(0.0, 1 - smooth((f - f_to) / eat)))
        o.location = (x * MM, y * MM, zb_mm * MM)
        o.rotation_euler = (0, 0, a)
        o.scale = ((2.3 * r + 4.0) * k, (1.25 * r + 2.0) * k, (1.25 * r + 2.0) * k)
        for dp in ("location", "rotation_euler", "scale"):
            o.keyframe_insert(dp, frame=f)
    _linear(o)

    def pos(f):
        x, y, _, _ = place(f)
        return (x * MM, y * MM, zb_mm * MM)
    return o, pos, P


# ---------------------------------------------------------------- 10 秒测试（定版大板，点名 3 个零件）

BOARD = os.environ.get("CDK20_WORK", "G:/cdk20/work") + "/kit/board_final.blend"
FPS, NF = 60, 600
LENS, FSTOP, AZ, EL = 50, 5.0, -6.0, 40.0


def list_cells():
    import kit_parts as KP
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    for o in sorted([o for o in bpy.data.objects["board"].children if o.name.startswith("z") and "_c" in o.name], key=lambda o: o.name):
        p = KP.part_of(o)
        t = o.matrix_world.translation
        print(f"CELL {o.name:12} {p.name if p else '-':24} x={t.x / MM:7.1f} y={t.y / MM:7.1f} cat={p.get('cat') if p else ''} gates={p.get('gates') if p else ''}")


def test_plan():
    """测试用的引导表（照 resolve.guide_plan 的规则写出的数，假想的三个词：落点 100、260、470）。"""
    evs = [dict(id="a", obj="a", verb="move", f_start=80, f_land=100, f_end=190, guide=dict(kind="focus", target="a")),
           dict(id="b", obj="b", verb="move", f_start=240, f_land=260, f_end=350, guide=dict(kind="focus", target="b")),
           dict(id="c", obj="c", verb="move", f_start=390, f_land=470, f_end=560, guide=dict(kind="runner", target="c", travel=72, arrive=4))]
    import resolve as RS
    return RS.guide_plan(evs, NF, sentences=[dict(sid="s1", f0=60, f1=300), dict(sid="s2", f0=330, f1=580)])


def test_build(out_blend, samples=16):
    import kit_parts as KP
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_"):
            bpy.data.objects.remove(o)
    sc.render.engine = "CYCLES"
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.frame_start, sc.frame_end = 0, NF - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.cycles.samples = samples; sc.cycles.seed = 7; sc.cycles.use_animated_seed = False
    _gpu(sc)
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.max_bounces = 12
    zb = bpy.data.objects["board"].location.z / MM
    cells = {o.name: o for o in bpy.data.objects["board"].children if o.name.startswith("z") and "_c" in o.name}
    # 选格子：第 3 区贴主料杆的锁（r2）和钥匙（r3）做近处点名，第 5 区的凹槽（r2）做远处（在画外，走料过去）
    pick = dict(a="z3_c4_r2", b="z3_c4_r3", c="z5_c8_r2")
    for k, n in list(pick.items()):
        if n not in cells or KP.part_of(cells[n]) is None:
            alt = sorted([c for c in cells if c.endswith("_r2") and KP.part_of(cells[c]) is not None and c not in pick.values()])
            pick[k] = alt[0]
    part = {k: KP.part_of(cells[n]) for k, n in pick.items()}
    pos = {k: cells[n].matrix_world.translation / MM for k, n in pick.items()}
    print("GUIDE pick", {k: (pick[k], part[k].name, round(pos[k].x, 1), round(pos[k].y, 1)) for k in pick})
    plan = test_plan()
    print("GUIDE plan", plan)

    # 镜头：开头框住 a、b（c 在画外右边）；走料时镜头跟着鼓包滑过去（起动不早于 gs+6），最后停在 c
    KP.lights((pos["a"].x + pos["c"].x) / 2 * MM, 0.05, 1.35)
    key = bpy.data.objects["key"]
    cam = KP.camera(sc, (0, 0, 0), 1.0, EL, AZ, lens=LENS, fstop=FSTOP)
    cdir = cam.location.normalized()
    run = next(it for it in plan if it["kind"] == "runner")
    ab = (pos["a"] + pos["b"]) / 2
    # 走料的路：b 的外圈下边中点 → 主料杆 → c 那一列 → c 的外圈下边中点
    sg = lambda v: 1.0 if v > 0 else -1.0      # noqa: E731  格子在主料杆哪一边
    by0, cy0 = pos["b"].y - sg(pos["b"].y) * KP.CY, pos["c"].y - sg(pos["c"].y) * KP.CY
    pts = [(pos["b"].x, by0, KP.R_LOOP), (pos["b"].x, sg(pos["b"].y) * KP.R_MAIN, 1.2), (pos["b"].x, 0, KP.R_MAIN), (pos["c"].x, 0, KP.R_MAIN),
           (pos["c"].x, sg(pos["c"].y) * KP.R_MAIN, 1.2), (pos["c"].x, cy0, KP.R_LOOP)]
    mr = bpy.data.objects.get("main_runner")
    base_m = (mr.active_material if mr and mr.active_material else None) or bpy.data.materials.get("kit_white") or bpy.data.materials[0]
    pulse, ppos, P = guide_runner(pts, run["gs"], run["gon"], zb, pulse_mat(base_m))       # 鼓包 = 料杆本色提亮，不是红色
    f_cam0 = run["gs"] + 6                      # 镜头跟焦点，不领焦点：起动不早于 gs + 6
    D0 = 0.36

    def cam_target(f):
        # 走料时镜头跟着鼓包（鼓包 ±8 帧的平均，拐角不顿），鼓包在画面上几乎不动；起步用 12 帧缓入；到了以后停在 c 上
        if f <= f_cam0:
            return Vector((ab.x * MM, (ab.y - 8) * MM, zb * MM))
        xs = sum(ppos(min(run["gon"], max(run["gs"], f + k)))[0] for k in range(-8, 9)) / 17 / MM
        x = ab.x + (xs - ab.x) * smooth((f - f_cam0) / 12)
        w = smooth((x - ab.x) / max(1e-6, pos["c"].x - ab.x))
        y = (ab.y - 8) + (pos["c"].y - 14 - (ab.y - 8)) * w
        return Vector((x * MM, y * MM, zb * MM))

    cam_loc = []
    for f in range(NF):
        drift = Vector((math.sin(f / 97) * 0.6 * MM, math.cos(f / 131) * 0.4 * MM, 0))       # 定机位上极慢的漂，不停死
        cam.location = cam_target(f) + drift + cdir * D0
        cam.keyframe_insert("location", frame=f)
        cam_loc.append(tuple(cam.location))
    _linear(cam)
    targets = {k: Vector(center(part[k])) for k in pick}
    targets["_pulse_" + run["id"]] = ppos
    fp = guide_focus(cam, plan, targets, NF, base=Vector(((ab.x) * MM, (ab.y - 30) * MM, zb * MM)), fstop=FSTOP, cam_pos=lambda f: cam_loc[f])
    # 轮廓光：主光 15% 起，calib 再量
    rims = guide_rim(plan, {k: [part[k]] for k in pick}, cam, key)
    # 预颤：每次点名一次（这三件这一拍都没有自己的拔 / 拼）
    ticks = {}
    for it in plan:
        k = it["target"][0]
        cell = cells[pick[k]]
        rot = tick_rot_cap(cam, sc, part[k], cam_loc[it["land"]], 0.45)
        ticks[it["id"]] = guide_tick(part[k], [g for g in KP.gates_of(cell) if not g.name.endswith("_spur")], KP.loop_of(cell), it["land"], rot_deg=rot)
        ticks[it["id"]]["rot_deg"] = round(rot, 3)
        ticks[it["id"]]["max_px"] = round(px_per_m(cam, sc, center(part[k]), cam_loc[it["land"]]) * (0.45 * MM + math.radians(rot) * half_diag(part[k])), 2)
    # 检查数：焦点拉动帧数、弥散圆、走料速度
    sc.frame_set(0)
    fwd = cam_rot_fwd(cam)
    chk = dict(pick=pick, plan=plan, ticks=ticks, fstop=FSTOP, lens=LENS)
    coc = {}
    for it in plan:
        f = it["gon"] + 2
        cl = Vector(cam_loc[f])
        S = (fp[f] - cl).dot(fwd)
        coc[it["id"]] = {k: round(coc_px(cam, sc, S, (targets[k] - cl).dot(fwd)), 2) for k in pick}
        # 背景板面：目标后面 46 mm（隔一行）的板面点
        bg = Vector((targets[it["target"][0]].x, targets[it["target"][0]].y + 46 * MM, zb * MM))
        coc[it["id"]]["board_behind"] = round(coc_px(cam, sc, S, (bg - cl).dot(fwd)), 2)
    chk["coc_px"] = coc
    # 走料速度（屏上，画面宽/秒）：鼓包投影的逐帧位移
    from bpy_extras.object_utils import world_to_camera_view
    sp = []
    for f in range(run["gs"], run["gon"]):
        sc.frame_set(f); a_ = world_to_camera_view(sc, cam, Vector(ppos(f)))
        sc.frame_set(f + 1); b_ = world_to_camera_view(sc, cam, Vector(ppos(f + 1)))
        sp.append(abs(b_.x - a_.x) * FPS)
    chk["runner_speed_max_wps"] = round(max(sp), 3)
    chk["runner_speed_at"] = run["gs"] + max(range(len(sp)), key=lambda i: sp[i])
    chk["runner_speed_profile"] = [round(v, 2) for v in sp[::4]]
    sc.frame_set(run["gs"])
    vis = world_to_camera_view(sc, cam, targets["c"])
    chk["runner_target_screen_x_at_gs"] = round(vis.x, 3)
    chk["runner_target_far"] = bool(vis.x > 1.0 or vis.x < 0.0 or abs(vis.x - world_to_camera_view(sc, cam, targets["b"]).x) > 0.35)
    chk["camera_start_after_gs6"] = f_cam0 >= run["gs"] + 6
    chk["rim_lights"] = {k: dict(name=v.name, peak_w=v["peak_w"], receivers=[o.name for o in v.light_linking.receiver_collection.objects]) for k, v in rims.items()}
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    Path(out_blend).with_suffix(".check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("GUIDE check", json.dumps(chk, ensure_ascii=False, default=str)[:3000])


def _gpu(sc):
    """一律 Cycles + OptiX GPU、OptiX 降噪；没有 OptiX 显卡就报错退出，不回落 CPU（导演 11-20：少用 CPU）。"""
    sc.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"; pr.get_devices()
    gpus = [d for d in pr.devices if d.type == "OPTIX"]
    if not gpus:
        raise SystemExit("bl_guide: 没有 OptiX 设备，不回落 CPU")
    for d in pr.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.render.use_persistent_data = True


def frames(blend, outdir, flist, pct=None):
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    _gpu(sc)
    if pct:
        sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = "PNG"
    for f in flist:
        sc.frame_set(f)
        sc.render.filepath = str(Path(outdir) / f"g_{f:04d}.png")
        bpy.ops.render.render(write_still=True)


def render_all(blend, outdir):
    """整段一次渲完（持久数据）；已有的帧跳过（断点续渲）。"""
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    _gpu(sc)
    sc.render.image_settings.file_format = "PNG"
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    sc.render.filepath = str(Path(outdir) / "g_")
    bpy.ops.render.render(animation=True)


def calib(blend, outdir, target_ev=0.25, pct=50, rounds=2):
    """在每盏轮廓光的落点帧渲关灯一张、开灯几张（半分辨率），只在被照零件投到画面上的框里量：
    开灯比关灯亮出 1/255 以上的像素（被照到的边缘）平均亮度比 → EV；按"加的光 ∝ 功率"调到 target_ev，再渲一次确认，回写 blend。
    同时报全帧平均亮度比（V6：引导引起的全帧变化 ≤ 3%）。"""
    import numpy as np
    from bpy_extras.object_utils import world_to_camera_view
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    _gpu(sc)
    sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = "PNG"
    rep = {}

    def shot(lo_, w, f, tag, it):
        set_rim_power(lo_, w)
        sc.frame_set(f)
        p = str(Path(outdir) / f"calib_{it['id']}_{tag}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p)
        a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1, :, :3]
        bpy.data.images.remove(im)
        return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

    for lo_ in [o for o in sc.objects if o.name.startswith("GUIDE_rim_") and o.type == "LIGHT"]:
        it = json.loads(lo_["guide"])
        f = it["land"]
        w = float(lo_["peak_w"])
        off = shot(lo_, 0.0, f, "off", it)
        H, W_ = off.shape
        objs = list(lo_.light_linking.receiver_collection.objects)
        uv = [world_to_camera_view(sc, sc.camera, m.matrix_world @ Vector(c)) for m in objs for c in m.bound_box]
        x0, x1 = int(max(0, min(q.x for q in uv)) * W_), int(min(1, max(q.x for q in uv)) * W_) + 1
        y0, y1 = int(max(0, 1 - max(q.y for q in uv)) * H), int(min(1, 1 - min(q.y for q in uv)) * H) + 1
        hist = []
        for r_ in range(rounds + 1):
            on = shot(lo_, w, f, f"on{r_}", it)
            box_on, box_off = on[y0:y1, x0:x1], off[y0:y1, x0:x1]
            mask = box_on > box_off + 1.0 / 255
            if mask.sum() < 20:
                hist.append(dict(w=round(w, 2), ev=0.0, px=int(mask.sum())))
                w *= 4
                continue
            ratio = float(box_on[mask].mean() / max(1e-6, box_off[mask].mean()))
            ev = math.log2(ratio)
            hist.append(dict(w=round(w, 2), ev=round(ev, 3), px=int(mask.sum()), box_ratio=round(float(box_on.mean() / max(1e-6, box_off.mean())), 4),
                             frame_ratio=round(float(on.mean() / max(1e-6, off.mean())), 4)))
            if r_ == rounds or abs(ev - target_ev) < 0.03:
                break
            w *= (2 ** target_ev - 1) / max(1e-6, ratio - 1)
        rep[it["id"]] = dict(box=[x0, y0, x1, y1], rounds=hist, final_w=round(hist[-1]["w"], 2), final_ev=hist[-1]["ev"])
        set_rim_power(lo_, hist[-1]["w"])
    bpy.ops.wm.save_mainfile()
    Path(blend).with_suffix(".calib.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("GUIDE calib", json.dumps(rep))


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "cells":
        list_cells()
    elif a[0] == "test":
        test_build(a[1], int(a[2]) if len(a) > 2 else 16)
    elif a[0] == "render":
        render_all(a[1], a[2])
    elif a[0] == "calib":
        calib(a[1], a[2])
    elif a[0] == "frames":
        frames(a[1], a[2], [int(x) for x in a[3].split(",")], int(a[4]) if len(a) > 4 else None)
