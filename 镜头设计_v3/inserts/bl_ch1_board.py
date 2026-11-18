"""HKBU SCIE1007 课程作业的科普视频：第 1 章三段三维（1-02、1-09、1-10），和样片 2-03 同一块定版大板、同一套做法。
场景是 G:/cdk20/work/kit/board_final.blend，排位不动；有几格在这一镜里换了内容（见各段的 build_*）。
所有帧号都从 映射/keys/<段>.json 读（映射/events/<段>.json 经 resolve.py 算出），脚本里不写帧号。

  1-02  大板开场：1,412 的字牌、小人、印着 2022 的日历；香港地图；玻璃肝、肺、结肠（三种最致命的癌）；地球仪和两块排名牌
  1-09  药的路：主料杆就是路，上面 7 个站点牌（Target … Approval，和二维页一字不差）；一粒红白胶囊一站一站跳过去，
        说到哪站落到哪站；Any step can fail 时后面三站的灰胶囊裂成两半
  1-10  奖章、名字牌、AlphaFold 芯片；说到 predicts the shape 时一串珠链从芯片出来，沿一条事先算好、不自交的路绕成一团，
        外面长出一层透明的蛋白表面

动作的做法照抄 bl_s203_board.py（生长 gn_grow、热料材质 hero_mat、拔 break_gates、鼓包 Path2、镜头 track）。
不穿模靠几何保证并逐帧 BVH 检查：浮起来的零件、跳的胶囊、珠链，对板上所有不动的东西，以及互相之间。

    blender -b --factory-startup -P bl_ch1_board.py -- build 1-02 OUT.blend [采样]     搭场景、打关键帧、存盘、跑自检（OUT.check.json）
    blender -b --factory-startup -P bl_ch1_board.py -- frames IN.blend OUTDIR 0,120,300 [采样] [百分比]
整段渲染：bash render_ch1.sh 1-02；合成出片：bash finish_ch1.sh 1-02。
"""
import json
import math
import sys
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit_parts as KP  # noqa: E402
import bl_s203_board as S  # noqa: E402

MM = KP.MM
BOARD = "G:/cdk20/work/kit/board_final.blend"
LENS, FSTOP, AZ, EL = 50, 16.0, -8.0, 38.0
SHAKE = 0.5
lerp, clamp, smooth, smoother, pop, track = S.lerp, S.clamp, S.smooth, S.smoother, S.pop, S.track


# ---------------------------------------------------------------- 打开大板、材质

def load_keys(seg):
    Kd = json.loads((HERE.parent / "映射" / "keys" / f"{seg}.json").read_text(encoding="utf-8"))
    return Kd, {e["id"]: e for e in Kd["events"]}


def open_board(Kd, samples):
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_"):
            bpy.data.objects.remove(o)
    sc.render.fps, sc.render.fps_base = 60, 1.0
    sc.frame_start, sc.frame_end = 0, Kd["len_f"] - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.cycles.samples = samples; sc.cycles.seed = 7; sc.cycles.use_animated_seed = False
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.max_bounces = 12; sc.cycles.transmission_bounces = 12; sc.cycles.glossy_bounces = 6
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    return sc


def kit():
    """KP.Kit() 会新建一套同名材质（带 .001）；换回板里已有的那套，免得一块板上两套白。"""
    K = KP.Kit()
    for attr, m in list(vars(K).items()):
        if isinstance(m, bpy.types.Material) and "." in m.name:
            base = m.name.split(".")[0]
            if base in bpy.data.materials:
                setattr(K, attr, bpy.data.materials[base]); bpy.data.materials.remove(m)
    return K


def board():
    return bpy.data.objects["board"]


def cell(name):
    return bpy.data.objects[name]


def cxy(c):
    t = c.matrix_world.translation
    return t.x / MM, t.y / MM


def replace_cell(K, name, part):
    """这一镜里换一格的内容：删掉旧的一格（外圈、浇口、零件），在同一位置用新零件重新搭一格（KP.make_cell）。"""
    old = bpy.data.objects[name]
    x, y = old.location.x / MM, old.location.y / MM
    for o in list(old.children_recursive) + [old]:
        bpy.data.objects.remove(o)
    new = KP.make_cell(K, part, x, y, 0, name=name)
    new.parent = board()
    bpy.context.view_layer.update()                       # 不更新的话 matrix_world 还是单位阵，后面按位置取的格子中心全错
    return new


def fit_text(o, maxw):
    bpy.context.view_layer.update()
    w = o.dimensions.x / MM
    if w > maxw:
        o.scale = (maxw / w,) * 3


def text_plate(K, lines, w=44.0, hy=7.0, sizes=None, name="p16_plate"):
    """白色字牌（Instrument Serif 正体），一行或两行；字太宽就整体缩到牌里。"""
    P = KP.Part(K, name, "white")
    P.box(0, 0, w / 2, hy, 2.8, K.white, r=1.8, bevel=0.6)
    sizes = sizes or [7.6] * len(lines)
    gap = 0.45 * sum(sizes) / len(sizes)
    tot = sum(sizes) + gap * (len(lines) - 1)
    y = tot / 2
    for t, sz in zip(lines, sizes):
        o = P.text(t, sz, 0, y - sz / 2 - 0.3, 1.4, K.ink)
        fit_text(o, w - 6.0)
        y -= sz + gap
    P.gate(-w / 2, 0, "-x"); P.gate(w / 2, 0, "+x")
    return P.done()


def calendar_year(K, year):
    """零件 10 日历，格子换成印上去的年份。"""
    P = KP.Part(K, "p10_calendar", "green"); m = K.green
    P.box(0, 5.2, 10.5, 10.2, 3.0, m, r=1.6)
    P.box(0, 12.8, 10.5, 2.6, 4.2, m, r=1.4)
    for s in (-1, 1):
        P.cyl(s * 5.2, 15.0, 1.6, 1.0, 3.2, m, axis="y", bevel=0.3)
    o = P.text(year, 7.4, 0, 3.4, 1.5, K.inkw)
    fit_text(o, 18.0)
    P.box(0, -12.2, 25, 2.8, 2.4, m, r=1.0)
    for i in range(11):
        P.inkbox(-22.5 + 4.5 * i, -11.2 - (0.0 if i % 5 == 0 else 0.5), 0.28, 1.7 if i % 5 == 0 else 1.0, K.inkw, 1.2)
    P.gate(-10.3, 5.2, "-x"); P.gate(10.3, 5.2, "+x"); P.gate(-25, -12.2, "-x")
    return P.done()


# ---------------------------------------------------------------- 长：每块料各自挂同一个生长节点（各自保留材质）

def prep(o, root, lmax):
    """零件的一块料换成零件坐标里的网格（修改器算进去），长边对半切到 lmax mm 以下，生长的台阶才细。
    切细以后法线从原来的网格抄回来（数据传递，最近面插值），不然三角扇在亮面上会出一片锤纹。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    me.transform(o.matrix_local)
    mats = list(getattr(o.data, "materials", []))
    name = o.name
    src = None
    if lmax and len(me.vertices) < 20000:
        src = KP.link(bpy.data.objects.new(name + "_nsrc", me.copy()))
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        for _ in range(8):
            long = [e for e in bm.edges if e.calc_length() > lmax * MM]
            if not long or len(bm.verts) > 300000:
                break
            bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        bm.to_mesh(me); bm.free()
    bpy.data.objects.remove(o)
    n = KP.link(bpy.data.objects.new(name, me), root)
    if not me.materials and mats:
        for m in mats:
            me.materials.append(m)
    if src is not None:
        dt = n.modifiers.new("nrm", "DATA_TRANSFER"); dt.object = src
        dt.use_loop_data = True; dt.data_types_loops = {"CUSTOM_NORMAL"}; dt.loop_mapping = "POLYINTERP_NEAREST"
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(n.evaluated_get(dg))
        n.modifiers.clear(); n.data = me2; bpy.data.meshes.remove(me); me2.name = name
        old = src.data; bpy.data.objects.remove(src); bpy.data.meshes.remove(old)
    return n


class Grow:
    """一组料从 gates 长出来（gn_grow），共用一个进度控制。objs 的坐标就是零件坐标（prep 过）。"""
    _mats = {}

    def __init__(self, name, root, objs, gates, fresh, emit=1.8, step=0.7, s=0.62, fonts=(), cell_x=None):
        self.name, self.root, self.objs, self.fonts = name, root, objs, list(fonts)
        for o in objs:                                     # 每组料自己一套热料材质（熔接线的数值各管各的）
            for i, m in enumerate(o.data.materials):
                key = (m.name, fresh, name)
                if key not in Grow._mats:
                    Grow._mats[key] = S.hero_mat(f"{name}_{m.name}", m, fresh, emit)
                o.data.materials[i] = Grow._mats[key]
        co = np.concatenate([S.coords(o) / MM for o in objs])
        g = np.array([(gx, gy) for gx, gy, *_ in gates], float)
        d = np.sqrt(((co[:, None, :2] - g[None]) ** 2).sum(-1)).min(1)
        self.amax = float(d.max())
        self.nmax = max(1, int(math.ceil(float(np.abs(co[:, 2]).max()) / step)))
        self.ctrl = KP.link(bpy.data.objects.new(name + "_T", None))
        ng, self.tau = S.gn_grow(name, [tuple(x) for x in g], self.amax, step, self.nmax, s, self.ctrl)
        self.s, self.t_end = s, 1 + 2 * self.tau
        for o in objs:
            md = o.modifiers.new("grow", "NODES"); md.node_group = ng
        self.ink = []
        for t in self.fonts:
            half = self.amax if cell_x is None else max(abs(gx) for gx, *_ in gates)
            mt = S.ink_reveal(t.data.materials[0], cell_x * MM if cell_x is not None else 0.0, half)
            t.data.materials.clear(); t.data.materials.append(mt)
            self.ink.append(mt)
        self.mats = sorted({m.name for o in objs for m in o.data.materials})

    def key(self, f, e):
        """一帧的生长进度、过冲、熔接线、印字。只在动的那一段打关键帧。"""
        if f < e["f_start"] - 2 or f > e["f_end"] + 34:
            return
        T = self.t_end * clamp((f - e["f_start"]) / max(1, e["f_end"] - e["f_start"]))
        self.ctrl.location.x = T; self.ctrl.keyframe_insert("location", frame=f)
        for o in self.objs:
            o.scale = (1, 1, 1 + 0.03 * max(0.0, 1 - abs(f - e["f_end"]) / 5.0))
            o.keyframe_insert("scale", frame=f)
        for mn in self.mats:
            wv = bpy.data.materials[mn].node_tree.nodes["weld"].outputs[0]
            wv.default_value = 0.42 * clamp(1 - (f - e["f_end"]) / 30.0) if f >= e["f_start"] else 0.0
            wv.keyframe_insert("default_value", frame=f)
        for mt in self.ink:
            rv = mt.node_tree.nodes["reveal"].outputs[0]
            rv.default_value = max(0.0, self.amax * (T - (1 - self.s) - 0.5 * self.tau) / self.s) * MM
            rv.keyframe_insert("default_value", frame=f)


def hero_parts(cell_obj, lmax=0.7):
    """一格零件的料（prep 过）和字。"""
    root = KP.part_of(cell_obj)
    kids = [o for o in root.children if not o.hide_render and "_cut" not in o.name and "_hole" not in o.name]
    fonts = [o for o in kids if o.type == "FONT"]
    objs = [prep(o, root, lmax) for o in kids if o.type in ("MESH", "CURVE")]
    return root, objs, fonts


# ---------------------------------------------------------------- 拔、浮

def combined(objs, name, parent):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return KP.link(bpy.data.objects.new(name, me), parent)


def eject_setup(cell_obj, root, objs, e, scar):
    """拔：浇口换成残根和白色断口（S.break_gates，用合起来的一个网格算残根退多少），预备时浇口拉细。"""
    tmp = combined(objs, cell_obj.name + "_tmp", root)
    brk = S.break_gates(cell_obj, tmp, scar, e["f_land"])
    for o in list(tmp.children):                       # 断口的位置是零件坐标；tmp 在零件根下是单位变换，直接换父物体
        o.parent = root
    bpy.data.objects.remove(tmp)
    for cone in [o for o in cell_obj.children if o.name.startswith(cell_obj.name + "_g") and not o.name.endswith(("_spur", "_stub", "_scar"))]:
        cone.scale = (1, 1, 1); cone.keyframe_insert("scale", frame=e["f_start"])
        cone.scale = (0.5, 0.5, 1.04); cone.keyframe_insert("scale", frame=e["f_land"] - 1)
    return brk


def shake(f, e, k=1.0, lag=0):
    t = f - lag - e["f_land"]
    if t < 0:
        return k * 0.35 * clamp(1 + t / max(1, e["f_land"] - e["f_start"])) ** 2 if lag == 0 else 0.0
    D = e["f_end"] - e["f_land"]
    return -k * SHAKE * math.exp(-t / 5.0) * math.cos(2 * math.pi * t / 7.5) * (1 - smooth((t - (D - 5)) / 5))


class Float:
    """拔起来以后浮着：弹起 H mm，过头一点回弹，轻轻上下浮动；朝镜头抬 tilt 度；yaw(f) 是自转（度）。"""
    def __init__(self, e, H, tilt=13.0, bob=0.8, bob_t=44.0, yaw=None, sway=0.0, roll=6.0, settle=0.0):
        self.e, self.H, self.tilt, self.bob, self.bob_t, self.yaw, self.sway, self.roll = e, H, tilt, bob, bob_t, yaw, sway, roll
        self.settle = settle          # 大件：先竖直升 settle 帧离开浇口残根，再开始转

    def pose(self, f):
        e = self.e
        if f < e["f_start"]:
            return 0.0, 0.0, 0.0, 0.0
        if f < e["f_land"]:
            return 0.7 * ((f - e["f_start"] + 1) / (e["f_land"] - e["f_start"])) ** 2, 0.0, 0.0, 0.0
        D = e["f_end"] - e["f_land"]
        t = (f - e["f_land"]) / D
        tb = f - e["f_land"] - 6
        # 接着拔之前已经升起的 0.7 mm，不掉回去
        z = 0.7 + (self.H - 0.7) * pop(t) + (self.bob * math.sin(2 * math.pi * tb / self.bob_t) * smooth(tb / 16.0) if tb > 0 else 0.0)
        tilt = self.tilt * smooth(t)
        roll = self.roll * math.exp(-4.0 * t) * math.sin(2 * math.pi * 1.6 * t) * smooth(t / 0.12)      # 先离开浇口再晃（大件晃得少）
        yaw = 5.0 * math.exp(-(f - e["f_land"]) / 16.0) * math.sin(2 * math.pi * (f - e["f_land"]) / 23.0)
        if self.yaw:
            yaw += self.yaw(f)
        if self.sway:
            yaw += self.sway * math.sin(2 * math.pi * (f - e["f_land"]) / 150.0) * smooth((f - e["f_land"]) / 30.0)
        if self.settle:
            g = smooth((f - e["f_land"]) / self.settle)
            tilt, roll, yaw = tilt * g, roll * g, yaw * g
        return z, tilt, roll, yaw


class Ejectable:
    """一格零件：拔、浮，以及这一格和周围几格的颤。"""
    def __init__(self, cell_obj, root, objs, e, flt, all_cells, scar, reach=80.0):
        self.cell, self.root, self.objs, self.e, self.flt = cell_obj, root, objs, e, flt
        self.brk = eject_setup(cell_obj, root, objs, e, scar)
        c0 = cell_obj.matrix_world.translation
        self.near = [c for c in all_cells if c is not cell_obj and (c.matrix_world.translation - c0).length < reach * MM]
        self.base = cell_obj.location.z
        root.rotation_mode = "ZYX"

    def key(self, f, nz):
        e = self.e
        sh = shake(f, e)
        self.cell.location.z = self.base + sh * MM; self.cell.keyframe_insert("location", frame=f)
        for c in self.near:
            nz[c.name] = nz.get(c.name, 0.0) + shake(f, e, 0.45, lag=2)
        z, tilt, roll, yaw = self.flt.pose(f)
        self.root.location = (0, 0, (z - (sh if f >= e["f_land"] else 0.0)) * MM)
        self.root.rotation_euler = (math.radians(tilt), math.radians(roll), math.radians(yaw))
        self.root.keyframe_insert("location", frame=f); self.root.keyframe_insert("rotation_euler", frame=f)


def key_near(nz, base_z, f):
    for n, v in nz.items():
        c = bpy.data.objects[n]; c.location.z = base_z[n] + v * MM; c.keyframe_insert("location", frame=f)


# ---------------------------------------------------------------- 鼓包、镜头

def put_pulse(o, x, y, ang, r, k, f, zb):
    o.location = (x * MM, y * MM, zb * MM)
    o.rotation_euler = (0, 0, ang)
    o.scale = ((2.3 * r + 4.0) * k, (1.25 * r + 2.0) * k, (1.25 * r + 2.0) * k)
    for dp in ("location", "rotation_euler", "scale"):
        o.keyframe_insert(dp, frame=f)


class Pulse:
    """一个鼓包沿 path 从 e.f_start 走到 e.f_land（到浇口前），然后瘪下去；split 给了就在那一点分成两股（镜像到 mirror_x 另一侧）。"""
    def __init__(self, name, mat, path, e, split=None, mirror_x=None):
        self.o = S.make_pulse(name, mat)
        self.ob = S.make_pulse(name + "b", mat) if split is not None else None
        self.path, self.e, self.split, self.mx = S.Path2(path), e, split, mirror_x

    def key(self, f, zb):
        e = self.e
        if f < e["f_start"] - 2 or f > e["f_land"] + 12:
            return
        t = clamp((f - e["f_start"]) / max(1, e["f_land"] - e["f_start"]))
        u = 0.5 * smooth(t) + 0.5 * t
        x, y, a, r = self.path.at(u)
        breathe = 1 + 0.05 * math.sin(2 * math.pi * f / 36.0)
        on = f >= e["f_start"]
        sp = self.split is not None and u >= self.path.u_of(self.split)
        k = (0.8 if sp else 1.0) * (1 - smooth((f - e["f_land"]) / 10.0)) * breathe * (1.0 if on else 0.0)
        put_pulse(self.o, x, y, a, r, k, f, zb)
        if self.ob is not None:
            put_pulse(self.ob, 2 * self.mx - x, y, math.pi - a, r, k if sp else 0.0, f, zb)


class Camera:
    """几个机位 (帧, x, y, z, 距离) 连成折线再高斯平滑；镜头方向不变（俯 EL、方位 AZ），对焦在目标点。"""
    def __init__(self, sc, knots, NF, zb, sigma=10.0):
        ks = sorted(knots, key=lambda k: k[0])
        self.TX, self.TY, self.TZ, self.TD = (track([(k[0], k[i]) for k in ks], NF, sigma) for i in (1, 2, 3, 4))
        self.cam = KP.camera(sc, (0, 0, 0), 1.0, EL, AZ, lens=LENS, fstop=FSTOP)
        self.cdir = self.cam.location.normalized()
        self.pos = []
        for f in range(NF):
            tgt = Vector((self.TX[f] * MM, self.TY[f] * MM, (zb + self.TZ[f]) * MM))
            self.cam.location = tgt + self.cdir * float(self.TD[f])
            self.cam.keyframe_insert("location", frame=f)
            self.cam.data.dof.focus_distance = float(self.TD[f])
            self.cam.data.dof.keyframe_insert("focus_distance", frame=f)
            self.pos.append(tuple(self.cam.location))


# ---------------------------------------------------------------- 自检：穿模

def mesh_bvh(objs, dg):
    co_all, polys, off = [], [], 0
    for o in objs:
        if o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is None or len(me.polygons) == 0:
            if me is not None:
                ev.to_mesh_clear()
            continue
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        M = np.array(ev.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        polys += [tuple(i + off for i in p.vertices) for p in me.polygons]
        off += len(co); co_all.append(co)
        ev.to_mesh_clear()
    if not co_all:
        return None
    co = np.concatenate(co_all)
    return BVHTree.FromPolygons(co.tolist(), polys), co.min(0), co.max(0)


def clip_check(sc, movers, f0, f1, step=1, tag="CH1"):
    """逐帧 BVH 面面相交：每个动的东西（movers：name、objs、f_from、own 前缀、f_break、active(f)）对板上所有不动的东西，以及动的东西两两之间。
    不动的东西在最后一帧取（拔过以后那几格的颤已经停了）。自己那一格的浇口在断开之前本来连着零件，不查；断开以后查残根。
    鼓包、白色断口、隐藏的东西不查。"""
    t0 = time.time()
    mine = set()
    for m in movers:
        mine |= set(m["objs"])
    sc.frame_set(f1)
    dg = bpy.context.evaluated_depsgraph_get()
    lo_all, hi_all = None, None
    for f in range(f0, f1 + 1, 8):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for m in movers:
            if f < m["f_from"]:
                continue
            b = mesh_bvh(m["objs"], dg)
            if b:
                lo_all = b[1] if lo_all is None else np.minimum(lo_all, b[1]); hi_all = b[2] if hi_all is None else np.maximum(hi_all, b[2])
    sc.frame_set(f1)
    dg = bpy.context.evaluated_depsgraph_get()
    statics = {}
    pad = 0.03
    for o in sc.objects:
        if o.type not in ("MESH", "CURVE", "FONT") or o in mine or o.hide_render:
            continue
        if o.name.startswith(("pulse_", "seam_", "sweep", "refl_")) or "_scar" in o.name or "_hole" in o.name or "_cut" in o.name:
            continue
        b = mesh_bvh([o], dg)
        if not b or lo_all is None or (b[1] > hi_all + pad).any() or (b[2] < lo_all - pad).any():
            continue
        statics[o.name] = b
    hits, nchk = [], 0
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        H = {}
        for m in movers:
            if f < m["f_from"] or (m.get("active") and not m["active"](f)):
                continue
            objs = m["objs"] if not m.get("objs_at") else m["objs_at"](f)
            b = mesh_bvh(objs, dg)
            if b:
                H[m["name"]] = (b, m)
        for k, (h, m) in H.items():
            tree, lo, hi = h
            for name, (st, slo, shi) in statics.items():
                if m.get("own") and name.startswith(m["own"]):
                    if f < m["f_break"] or not name.endswith(("_stub", "_spur")):
                        continue
                if m.get("skip") and m["skip"](name):
                    continue
                if (lo > shi).any() or (hi < slo).any():
                    continue
                nchk += 1
                if tree.overlap(st):
                    hits.append((f, k, name))
        ks = list(H)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                (ta, la, ha), _ = H[ks[i]]
                (tb, lb, hb), _ = H[ks[j]]
                if (la > hb).any() or (ha < lb).any():
                    continue
                nchk += 1
                if ta.overlap(tb):
                    hits.append((f, ks[i], ks[j]))
    by = {}
    for f, a, b in hits:
        by.setdefault(f"{a} × {b}", []).append(f)
    summ = {k: dict(frames=len(v), first=v[0], last=v[-1]) for k, v in by.items()}
    print(f"{tag} 穿模检查：第 {f0}–{f1} 帧，不动的物体 {len(statics)} 个，{nchk} 次 BVH 相交，穿模 {len(hits)} 处 {summ if hits else ''}（{time.time() - t0:.0f}s）")
    sc.frame_set(0)
    return dict(f0=f0, f1=f1, statics=len(statics), tests=nchk, hits=len(hits), by_pair=summ)


def finish(sc, Kd, cam, heroes, clip, out_blend, t0, extra=None):
    sc.frame_set(0)
    Path(out_blend).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    print(f"CH1 saved {out_blend} in {time.time() - t0:.0f}s")
    S0, S1 = Kd["sentences"][0]["f0"], Kd["sentences"][-1]["f1"]
    rep = dict(seg=Kd["group"], words_hash=Kd.get("words_hash"), events={e["id"]: [e["f_start"], e["f_land"], e["f_end"]] for e in Kd["events"]})
    rep.update(extra or {})
    rep["smooth"] = S.smooth_check(sc, Kd, cam.pos, S0, S1)
    rep["layout"] = S.layout_check(sc, cam.cam, heroes)
    rep["clip"] = clip()
    rep["pass"] = bool(rep["smooth"]["pass"] and rep["clip"]["hits"] == 0)
    rp = Path(out_blend).with_suffix(".check.json")
    rp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("CH1 report", rp, "总判", "过" if rep["pass"] else "不过")
    return rep


def all_cells():
    return [o for o in board().children if o.name.startswith("z") and "_c" in o.name]


# ================================================================ 1-02 大板开场

def build_102(out_blend, samples):
    t0 = time.time()
    Kd, EV = load_keys("1-02")
    NF = Kd["len_f"]
    sc = open_board(Kd, samples)
    K = kit()
    M = bpy.data.materials
    zb = board().location.z / MM
    # 这一镜换内容的几格
    replace_cell(K, "z1_c0_r3", text_plate(K, ["1,412"], sizes=[8.6]))
    replace_cell(K, "z1_c0_r4", calendar_year(K, "2022"))
    replace_cell(K, "z1_c0_r0", text_plate(K, ["6th most common"], w=48.0, sizes=[6.2]))
    replace_cell(K, "z1_c2_r0", text_plate(K, ["3rd deadliest"], w=48.0, sizes=[6.2]))
    cells = all_cells()
    C = {k: cell(n) for k, n in dict(num="z1_c0_r3", cal="z1_c0_r4", six="z1_c0_r0", third="z1_c2_r0", ppl1="z1_c2_r2", ppl2="z1_c2_r3",
                                     hk="z1_c1_r4", liver="z1_c0_r1", lung="z1_c1_r3", globe="z1_c1_r0").items()}
    P = {k: cxy(c) for k, c in C.items()}
    # 板脚：从这几格的空处看过去，后面的板脚像一根柱子顶着浮起来的零件（2-03 同样的问题），这一镜去掉
    feet = [o for o in bpy.data.objects["board"].children if o.name.startswith("foot")
            and any(abs(o.matrix_world.translation.x / MM - x) < 40 and -5 < o.matrix_world.translation.y / MM - y < 55 for x, y in P.values())]
    for o in feet:
        bpy.data.objects.remove(o)
    print("CH1 去掉板脚", len(feet))
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    G, R, OBJ = {}, {}, {}
    for k, fresh in (("num", "#FFF6DC"), ("cal", "#B8F0C0"), ("six", "#FFF6DC"), ("third", "#FFF6DC"), ("ppl1", "#FFF6DC"), ("ppl2", "#FFF6DC"),
                     ("hk", "#FFF6DC"), ("globe", "#FFF6DC")):
        root, objs, fonts = hero_parts(C[k])
        R[k], OBJ[k] = root, objs
        G[k] = Grow("grow_" + k, root, objs, json.loads(root["gates"]), fresh, emit=1.4, fonts=fonts, cell_x=P[k][0])
    # 玻璃肝：去掉给定位销的凸台和孔（和 2-03 一样），玻璃壳细分一次
    r_lv = KP.part_of(C["liver"])
    kids = [o for o in r_lv.children if o.type == "MESH" and not o.hide_render]
    shell = next(o for o in kids if o.data.materials[0].name.startswith("kit_organ_glass") and len(o.data.vertices) > 5000)
    vessel = next(o for o in kids if o.data.materials[0].name.startswith("kit_red"))
    for o in kids:
        if o not in (shell, vessel):
            bpy.data.objects.remove(o)
    for md in [md for md in shell.modifiers if md.type == "BOOLEAN"]:
        shell.modifiers.remove(md)
    S.bake_mesh(shell, subdiv=1)
    shell = prep(shell, r_lv, None); vessel = prep(vessel, r_lv, None)
    g_lv = json.loads(r_lv["gates"])
    R["liver"], OBJ["liver"] = r_lv, [shell, vessel]
    G["liver_s"] = Grow("grow_liver_shell", r_lv, [shell], g_lv, "#FF8A8A", emit=1.6, step=2.6)
    G["liver_v"] = Grow("grow_liver_vessel", r_lv, [vessel], g_lv, "#FF6A70", emit=1.8, step=2.6)
    # 肺和肠：一格里两组料，肺（玻璃肺 + 红气管）从 −x 的浇口长，结肠从 +x 的浇口长
    r_lg = KP.part_of(C["lung"])
    lg = [prep(o, r_lg, None) for o in r_lg.children if o.type == "MESH" and not o.hide_render]
    g_lg = json.loads(r_lg["gates"])
    xc = {o.name: float(S.coords(o)[:, 0].mean()) / MM for o in lg}
    lung = [o for o in lg if xc[o.name] < 0]; colon = [o for o in lg if xc[o.name] >= 0]
    R["lung"], OBJ["lung"] = r_lg, lg
    G["lung"] = Grow("grow_lung", r_lg, lung, [g for g in g_lg if g[2] == "-x"], "#FF8A8A", emit=1.6, step=1.4)
    G["colon"] = Grow("grow_colon", r_lg, colon, [g for g in g_lg if g[2] == "+x"], "#FF8A8A", emit=1.6, step=1.4)
    print("CH1 1-02 heroes", {k: (len(v), [o.name for o in v][:4]) for k, v in OBJ.items()}, "lung", [o.name for o in lung], "colon", [o.name for o in colon])
    grow_ev = dict(num="num_grow", cal="cal_grow", six="six_grow", third="third_grow", ppl1="ppl_1", ppl2="ppl_2", hk="hk_grow", globe="globe_grow",
                   liver_s="liver_grow", liver_v="liver_grow", lung="lung_grow", colon="colon_grow")
    lag_v = 2

    # 拔、浮
    spin0 = EV["globe_spin"]
    yaw_g = lambda f: 0.0 if f < spin0["f_start"] else 0.55 * (f - spin0["f_start"]) * 1.0 + 0.0      # noqa: E731  地球仪慢慢自转（度）
    EJ = dict(num=Ejectable(C["num"], R["num"], OBJ["num"], EV["num_eject"], Float(EV["num_eject"], 14.0, tilt=14.0), cells, scar),
              liver=Ejectable(C["liver"], r_lv, OBJ["liver"], EV["liver_eject"], Float(EV["liver_eject"], 8.0, tilt=6.0, bob=0.6, roll=1.5, settle=8.0), cells, scar, reach=115.0),
              lung=Ejectable(C["lung"], r_lg, lg, EV["organ_eject"], Float(EV["organ_eject"], 10.0, tilt=10.0, roll=3.0), cells, scar),
              globe=Ejectable(C["globe"], R["globe"], OBJ["globe"], EV["globe_eject"], Float(EV["globe_eject"], 13.0, tilt=8.0, yaw=yaw_g), cells, scar))
    base_z = {c.name: c.location.z for c in cells}

    # 鼓包
    RM_, RL, RK = KP.R_MAIN, KP.R_LOOP, 1.2
    x0 = (bpy.data.objects["sprue_cone"].matrix_world.translation.x / MM) + 6
    m_pulse = S.hero_mat("pulse_white", M["kit_white"], "#FFEFD0", emit=2.2)
    m_pulse.node_tree.nodes["soft"].outputs[0].default_value = 0.32
    nx, ny = P["num"]
    pa = [(x0, 0, RM_), (nx, 0, RM_), (nx, -RM_, RK), (nx, ny + KP.CY, RL)] + S.half_loop(nx, ny, 1, "t", "s") + [(nx + 24.0, ny, RK)]
    lx, ly = P["liver"]
    gx2 = lx + g_lv[2][0]
    lvb = ly - (KP.CY + KP.PY / 2)
    pb = [(x0, 0, RM_), (nx, 0, RM_), (nx, RM_, RK), (nx, lvb, RL), (gx2, lvb, RL), (gx2, lvb + 4.5, RK)]
    gx_, gy_ = P["globe"]
    cxr = lx + KP.CX + KP.PX / 2
    pc = [(x0, 0, RM_), (gx_, 0, RM_), (gx_, RM_, RK), (gx_, lvb, RL), (cxr - 5, lvb, RL), (cxr, lvb + 5, RL), (cxr, ly + KP.CY + KP.PY / 2 - 5, RL),
          (cxr - 5, ly + KP.CY + KP.PY / 2, RL), (gx_, ly + KP.CY + KP.PY / 2, RL), (gx_, gy_ - KP.CY, RK), (gx_ + KP.CX - 5, gy_ - KP.CY, RL),
          (gx_ + KP.CX, gy_ - 15.5, RL), (gx_ + 9.5, gy_ - 15.5, RK)]
    PU = [Pulse("pulse_1", m_pulse, pa, EV["pulse_a"], split=3, mirror_x=nx), Pulse("pulse_2", m_pulse, pb, EV["pulse_b"]), Pulse("pulse_3", m_pulse, pc, EV["pulse_c"])]

    # 镜头
    e = EV
    kn = [(0, -432, -42, 0, 0.250), (e["num_grow"]["f_land"], -440, -38, 0, 0.236), (e["num_grow"]["f_end"], -438, -36, 0, 0.238),
          (e["cam_a"]["f_land"], -388, -22, 0, 0.292), (e["ppl_2"]["f_end"], -392, -26, 0, 0.29), (e["cal_grow"]["f_land"] + 20, -418, -48, 0, 0.27),
          (e["num_eject"]["f_end"], -424, -44, 5, 0.27), (e["cam_b"]["f_land"], -398, -54, 2, 0.265), (e["hk_grow"]["f_end"], -398, -50, 2, 0.27),
          (e["liver_grow"]["f_land"] + 10, -404, 28, 4, 0.33), (e["liver_eject"]["f_end"], -404, 34, 8, 0.33), (e["cam_c"]["f_land"], -396, 12, 6, 0.345),
          (e["lung_grow"]["f_end"], -388, 2, 6, 0.335), (e["organ_eject"]["f_end"], -392, 6, 8, 0.345), (e["cam_d"]["f_start"], -392, 10, 8, 0.345),
          (e["cam_d"]["f_land"], -379, 106, 4, 0.275), (e["cam_d"]["f_end"], -379, 109, 5, 0.27), (e["globe_eject"]["f_end"], -379, 114, 9, 0.245),
          (e["six_grow"]["f_land"] + 20, -418, 121, 7, 0.258), (e["six_grow"]["f_end"], -412, 122, 7, 0.262),
          (e["third_grow"]["f_land"] + 20, -382, 126, 7, 0.298), (NF - 1, -379, 127, 7, 0.305)]      # 结尾三格（6th、地球、3rd）一起进画
    cam = Camera(sc, kn, NF, zb)
    KP.lights(-0.39, 0.02, 1.35)

    # 逐帧关键帧
    nz_cells = set()
    for f in range(NF):
        for k, g in G.items():
            ev_ = EV[grow_ev[k]]
            if k == "liver_v":
                ev_ = dict(ev_, f_start=ev_["f_start"] + lag_v, f_end=ev_["f_end"] + lag_v)
            g.key(f, ev_)
        for p in PU:
            p.key(f, zb)
        nz = {}
        for ej in EJ.values():
            ej.key(f, nz)
        key_near(nz, base_z, f); nz_cells |= set(nz)
    rep_extra = dict(gates={k: v.brk for k, v in EJ.items()})

    def clip():
        mv = [dict(name=k, objs=[o for o in ej.root.children_recursive if o.type in ("MESH", "FONT", "CURVE")], f_from=ej.e["f_start"], own=ej.cell.name + "_g", f_break=ej.e["f_land"])
              for k, ej in EJ.items()]
        return clip_check(sc, mv, min(m["f_from"] for m in mv), NF - 1)
    heroes = dict(num=(OBJ["num"][0], EV["num_grow"]["f_end"]), liver=(shell, EV["liver_grow"]["f_end"]), globe=(OBJ["globe"][0], EV["globe_grow"]["f_end"]))
    return finish(sc, Kd, cam, heroes, clip, out_blend, t0, rep_extra)


# ================================================================ 1-09 药的路

CAP_L, CAP_R, CAP_R2 = 12.0, 2.45, 2.6       # 胶囊长、身子半径、帽半径（mm）
BAND_R, BAND_r = 2.72, 0.3                    # 改进以后接缝上那圈金箍
HOP_H = 22.0                                  # 站与站之间跳多高


def capsule_part(K, name, m_body, m_cap, cat="white"):
    """一粒胶囊：轴沿零件的 Y，身子和帽是两块料，帽套在身子外面。"""
    P = KP.Part(K, name, cat)
    h = CAP_L / 2
    body = P.capsule(0, -h, 0.9, CAP_R, m_body)
    cap = P.capsule(0, -0.9, h, CAP_R2, m_cap)
    P.gate(0, 0, "-y")
    return P.done(), body, cap


def build_109(out_blend, samples):
    t0 = time.time()
    Kd, EV = load_keys("1-09")
    NF = Kd["len_f"]
    sc = open_board(Kd, samples)
    K = kit()
    M = bpy.data.materials
    B = board()
    zb = B.location.z / MM
    RM_ = KP.R_MAIN
    cone = bpy.data.objects["sprue_cone"]
    x_cone = cone.matrix_world.translation.x / MM
    z_cone = (cone.matrix_world.translation.z - B.matrix_world.translation.z) / MM + 5.0       # 注料口顶面（板面坐标）
    # 站点牌：按字找（KP.STATIONS），每站的牌子、字、小柱子
    st_root = bpy.data.objects["stations"]
    texts = {o.data.body: o for o in st_root.children if o.type == "FONT"}
    assert [s for s in KP.STATIONS if s in texts] == KP.STATIONS, f"站点牌的字对不上：{sorted(texts)}"
    sx = [texts[s].matrix_world.translation.x / MM for s in KP.STATIONS]
    boxes = {}
    for o in st_root.children:
        if o.type != "MESH":
            continue
        c = S.coords(o)
        M_ = np.array(o.matrix_world)
        w = (c @ M_[:3, :3].T + M_[:3, 3]) / MM
        mx = float(w[:, 0].mean())
        i = int(np.argmin([abs(mx - s) for s in sx]))
        if abs(mx - sx[i]) < 3.0:
            boxes[i] = o
    print("CH1 1-09 stations", [round(s, 1) for s in sx], {i: o.name for i, o in boxes.items()})
    m_st = {}
    for i, o in boxes.items():
        m_st[i] = S.hero_mat(f"station_{i}", M["kit_white"], "#FFE9B0", emit=1.6)
        o.data.materials.clear(); o.data.materials.append(m_st[i])

    # 主料杆：自己一份材质，路上的亮光（walks the same road）是材质里沿 x 走的一段亮
    runner = bpy.data.objects["main_runner"]
    m_run = M["kit_white"].copy(); m_run.name = "runner_glint"
    nt = m_run.node_tree; Nn, Ln = nt.nodes, nt.links
    out = next(n for n in Nn if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    gl = Nn.new("ShaderNodeBsdfPrincipled"); gl.inputs["Base Color"].default_value = KP.lin("#FFEFD0")
    gl.inputs["Roughness"].default_value = 0.03; gl.inputs["Coat Weight"].default_value = 1.0
    gl.inputs["Emission Color"].default_value = KP.lin("#FFEFD0"); gl.inputs["Emission Strength"].default_value = 2.4
    geo = Nn.new("ShaderNodeNewGeometry"); sep = Nn.new("ShaderNodeSeparateXYZ"); Ln.new(geo.outputs["Position"], sep.inputs[0])
    xv = Nn.new("ShaderNodeValue"); xv.name = "glint_x"; xv.outputs[0].default_value = -9.0

    def mnode(op, a, b):
        n = Nn.new("ShaderNodeMath"); n.operation = op
        for i_, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i_].default_value = v
            else:
                Ln.new(v, n.inputs[i_])
        return n.outputs[0]
    q = mnode("DIVIDE", mnode("SUBTRACT", sep.outputs[0], xv.outputs[0]), 0.016)
    fac = mnode("EXPONENT", mnode("MULTIPLY", mnode("MULTIPLY", q, q), -1.0), None)
    mix = Nn.new("ShaderNodeMixShader"); Ln.new(fac, mix.inputs[0]); Ln.new(src, mix.inputs[1]); Ln.new(gl.outputs[0], mix.inputs[2])
    Ln.new(mix.outputs[0], out.inputs["Surface"])
    runner.data.materials.clear(); runner.data.materials.append(m_run)
    x_end = max(p.co.x for sp in runner.data.splines for p in sp.points) / MM

    # 胶囊（白身红帽）和三粒灰胶囊
    root, body, cap = capsule_part(K, "drug_capsule", M["kit_white"], M["kit_red"], "red")
    root.parent = B
    root.rotation_mode = "ZYX"                    # 先转 −90° 让轴沿板的 x，再绕板的 y 翻跟头
    objs = [prep(o, root, 0.5) for o in (body, cap)]
    g_cap = Grow("grow_capsule", root, objs, [(0.0, 0.0, "-y", 0.0)], "#FFF6DC", emit=1.4, step=0.5)
    m_body, m_cap = objs[0].data.materials[0], objs[1].data.materials[0]
    bpy.ops.mesh.primitive_torus_add(major_radius=BAND_R * MM, minor_radius=BAND_r * MM, major_segments=64, minor_segments=16, rotation=(math.pi / 2, 0, 0))
    band = bpy.context.object; band.name = "capsule_band"; bpy.ops.object.shade_smooth()
    m_band = S.hero_mat("band_gold", M["kit_gold"], "#FFE08A", emit=2.0)
    band.data.materials.append(m_band); band.parent = root
    m_ghost = KP.mat_clear("ghost_grey", rgb=(0.80, 0.80, 0.84), density=9.0, rough=0.10, coat=0.6)
    GH = []
    ghost_st = [3, 4, 5]
    for j, i in enumerate(ghost_st):
        r_, b_, c_ = capsule_part(K, f"ghost_{j}", m_ghost, m_ghost, "clear")
        r_.parent = B
        ob = [prep(o, r_, 0.5) for o in (b_, c_)]
        gg = Grow(f"grow_ghost_{j}", r_, ob, [(0.0, 0.0, "-y", 0.0)], "#E8E8F0", emit=0.6, step=0.5)
        GH.append(dict(root=r_, body=ob[0], cap=ob[1], g=gg, x=sx[i] + 24.0))      # 裂开后身子往左滑 3 mm，离牌子还有 3.5 mm

    # 胶囊的路线：注料口 → 每站牌子右边 19 mm；Trials 以后三小跳
    xs = [s + 19.0 for s in sx]
    z_run = RM_ + CAP_R2 + 0.15                                      # 躺在料杆顶上时中心的高度（留 0.15 mm：长满时过冲 3% 也不碰）
    z_cone_c = z_cone + CAP_R2 + 0.3
    hops = [("hop_0", x_cone, z_cone_c, xs[0], HOP_H, True)]
    for i in range(1, 6):
        hops.append((f"hop_{i}", xs[i - 1], z_run, xs[i], HOP_H, True))
    hops += [("phase_1", xs[5], z_run, xs[5] + 8, 7.0, False), ("phase_2", xs[5] + 8, z_run, xs[5] + 16, 7.0, False),
             ("phase_3", xs[5] + 16, z_run, xs[5] + 24, 7.0, False), ("hop_6", xs[5] + 24, z_run, xs[6], HOP_H, True)]
    assert xs[6] + CAP_L / 2 + 2 < x_end, "Approval 那一站的落点超出主料杆"
    e_imp = EV["improve"]
    lift = lambda f: (BAND_R + BAND_r - CAP_R2) * smoother((f - e_imp["f_start"]) / (e_imp["f_end"] - e_imp["f_start"]))  # noqa: E731

    def cap_pose(f):
        """胶囊中心（板面坐标 mm）、绕 y 的翻转角（度）、x/z 方向的压扁。"""
        x, z, rot, sq = x_cone, z_cone_c, 0.0, 0.0
        for name, xa, za, xb, h, flip in hops:
            e = EV[name]
            if f < e["f_start"]:
                break
            if f <= e["f_land"]:
                t = (f - e["f_start"]) / (e["f_land"] - e["f_start"])
                if t < 0.12:                                          # 预备：先往下一蹲
                    return xa, za, 0.0, -0.10 * math.sin(math.pi * t / 0.12)
                u = (t - 0.12) / 0.88
                ue = 0.5 * smooth(u) + 0.5 * u
                x = lerp(xa, xb, ue)
                z = lerp(za, z_run, ue) + h * 4 * u * (1 - u)
                rot = -360.0 * smoother(clamp((u - 0.15) / 0.7)) if flip else 0.0
                return x, z, rot, 0.0
            x, z = xb, z_run
            t = (f - e["f_land"]) / max(1, e["f_end"] - e["f_land"])
            sq = 0.14 * math.exp(-3.5 * t) * math.cos(2 * math.pi * 1.2 * t) * (1 - t)
        e = EV["cap_nod"]
        if e["f_start"] <= f <= e["f_end"]:
            t = (f - e["f_start"]) / (e["f_end"] - e["f_start"])
            z += 4.0 * math.sin(math.pi * clamp(t / 0.6)) if t < 0.6 else 0.0
            if t >= 0.6:
                sq = 0.08 * math.sin(math.pi * (t - 0.6) / 0.4)
        return x, z, rot, sq

    # 站点牌：亮一下（m_st 的 soft）；路上的亮光经过时轻轻弹一下（牌子、字、小柱子一起抬 1 mm）
    e_gl = EV["road_glint"]
    glint_x = lambda f: lerp(x_cone, x_end + 20, 0.5 * smooth((f - e_gl["f_start"]) / (e_gl["f_land"] - e_gl["f_start"])) + 0.5 * clamp((f - e_gl["f_start"]) / (e_gl["f_land"] - e_gl["f_start"])))  # noqa: E731
    posts = {}
    for o in st_root.children:
        if o.type == "MESH" and o not in boxes.values():
            c = S.coords(o); M_ = np.array(o.matrix_world)
            mx = float(((c @ M_[:3, :3].T + M_[:3, 3]) / MM)[:, 0].mean())
            i = int(np.argmin([abs(mx + 15.5 - s) for s in sx]))
            posts[i] = o
    st_objs = {i: [boxes[i], texts[KP.STATIONS[i]]] + ([posts[i]] if i in posts else []) for i in range(7)}
    st_z0 = {o.name: o.location.z for v in st_objs.values() for o in v}

    # 镜头
    e = EV
    cx_ = lambda i: sx[i] + 9.0     # noqa: E731  牌子和落在右边的胶囊一起的中心
    D_ST, D_HOP = 0.165, 0.215                       # 落站时、跳在半路时镜头离多远（站牌的字要看得清）
    kn = [(0, x_cone + 10, -4, 6, 0.20), (e["cam_a"]["f_land"], x_cone + 6, -2, 9, 0.16), (e["cap_grow"]["f_end"], x_cone + 6, -2, 10, 0.155),
          (e["cam_wide"]["f_start"], x_cone + 10, -2, 10, 0.17), (e["cam_wide"]["f_land"], -60, -14, 0, 1.02), (e["cam_wide"]["f_end"], -40, -14, 0, 1.0),
          (e["cam_t"]["f_land"], cx_(0) - 4, -2, 8, D_ST), (e["hop_0"]["f_end"], cx_(0), -2, 8, D_ST)]
    for i, (cev, hev) in enumerate([("cam_h", "hop_1"), ("cam_i", "hop_2"), ("cam_c", "hop_3"), ("cam_an", "hop_4"), ("cam_tr", "hop_5")], start=1):
        fm = (e[hev]["f_start"] + e[hev]["f_land"]) // 2
        kn += [(fm, (cx_(i - 1) + cx_(i)) / 2, -4, 12, D_HOP), (e[cev]["f_land"], cx_(i), -2, 8, D_ST)]
    xg_mid = (sx[3] + sx[5]) / 2 + 24.0                 # fail：三粒灰胶囊（Cells、Animals、Trials）一起在画面里
    kn += [(e["st_1"]["f_end"] + 20, cx_(1) + 2, -2, 8, D_ST - 0.005), (e["cap_nod"]["f_end"], cx_(1) + 3, -2, 8, D_ST - 0.01), (e["improve"]["f_end"], cx_(2) + 2, -2, 8, D_ST - 0.005),
           (e["phase_1"]["f_land"], cx_(5) + 12, -2, 8, D_ST + 0.01), (e["phase_3"]["f_end"], cx_(5) + 24, -2, 8, D_ST + 0.01),
           ((e["hop_6"]["f_start"] + e["hop_6"]["f_land"]) // 2, (cx_(5) + cx_(6)) / 2 + 12, -4, 12, D_HOP), (e["cam_ap"]["f_land"], cx_(6), -2, 8, D_ST),
           (e["cam_end"]["f_start"], cx_(6) - 2, -2, 8, D_ST + 0.005), (e["cam_end"]["f_land"] + 12, xg_mid, -6, 4, 0.44), (NF - 1, xg_mid, -6, 4, 0.45)]
    cam = Camera(sc, kn, NF, zb, sigma=9.0)
    KP.lights(0.0, 0.05, 2.3)

    # 逐帧
    e_fail = EV["ghost_fail"]
    for f in range(NF):
        g_cap.key(f, EV["cap_grow"])
        for gh in GH:
            gh["g"].key(f, EV["ghost_in"])
        x, z, rot, sq = cap_pose(f)
        z += lift(f)
        sxz = 1 + sq; szz = 1 - sq
        root.location = (x * MM, 0, (z - CAP_R2 * (1 - szz)) * MM)
        root.rotation_euler = (0, math.radians(rot), math.radians(-90))
        root.scale = (1.0, sxz, szz)            # 零件的 Y 是胶囊的轴；转过 −90° 以后沿板的 x
        for dp in ("location", "rotation_euler", "scale"):
            root.keyframe_insert(dp, frame=f)
        tb = clamp((f - e_imp["f_start"]) / (e_imp["f_end"] - e_imp["f_start"]))
        band.scale = (lerp(0.86, 1.0, smoother(tb)),) * 3 if f >= e_imp["f_start"] else (0.0, 0.0, 0.0)
        band.keyframe_insert("scale", frame=f)
        m_band.node_tree.nodes["soft"].outputs[0].default_value = 0.8 * (1 - smooth((f - e_imp["f_land"]) / 14.0)) if f >= e_imp["f_start"] else 0.0
        m_band.node_tree.nodes["soft"].outputs[0].keyframe_insert("default_value", frame=f)
        eg = EV["cap_glow"]
        gv = 0.55 * math.sin(math.pi * clamp((f - eg["f_start"]) / (eg["f_end"] - eg["f_start"])))
        for mt in (m_body, m_cap):
            mt.node_tree.nodes["soft"].outputs[0].default_value = gv
            mt.node_tree.nodes["soft"].outputs[0].keyframe_insert("default_value", frame=f)
        # 站点牌亮
        for i in range(7):
            es = EV[f"st_{i}"]
            t = (f - es["f_start"]) / max(1, es["f_end"] - es["f_start"])
            v = 0.7 * smooth(t / 0.15) * (1 - smooth((t - 0.45) / 0.55)) if 0 <= t <= 1 else 0.0
            m_st[i].node_tree.nodes["soft"].outputs[0].default_value = v
            m_st[i].node_tree.nodes["soft"].outputs[0].keyframe_insert("default_value", frame=f)
            xg = glint_x(f) if e_gl["f_start"] <= f <= e_gl["f_land"] + 10 else -9e9
            up = 1.0 * math.exp(-((xg - sx[i]) / 16.0) ** 2)
            for o in st_objs[i]:
                o.location.z = st_z0[o.name] + up * MM; o.keyframe_insert("location", frame=f)
        xv.outputs[0].default_value = glint_x(f) * MM if e_gl["f_start"] <= f <= e_gl["f_land"] + 10 else -9.0
        xv.outputs[0].keyframe_insert("default_value", frame=f)
        # 灰胶囊：Any step 时长出来，fail 时裂成两半往两边滑开
        for gh in GH:
            r_ = gh["root"]
            r_.location = (gh["x"] * MM, 0, z_run * MM); r_.rotation_euler = (0, 0, math.radians(-90))
            r_.keyframe_insert("location", frame=f); r_.keyframe_insert("rotation_euler", frame=f)
            t = clamp((f - e_fail["f_start"]) / (e_fail["f_end"] - e_fail["f_start"]))
            d = 3.0 * smoother(clamp((t - 0.25) / 0.75))
            jolt = 0.8 * math.sin(math.pi * clamp(t / 0.4)) if t < 0.4 else 0.0
            gh["body"].location = (0, -d * MM, jolt * MM); gh["cap"].location = (0, d * MM, jolt * 0.6 * MM)
            gh["body"].keyframe_insert("location", frame=f); gh["cap"].keyframe_insert("location", frame=f)
    rep_extra = dict(stations=dict(zip(KP.STATIONS, [round(s, 1) for s in sx])), landing_x=[round(x, 1) for x in xs], runner_end=round(x_end, 1))

    def clip():
        eb = EV["improve"]
        mv = [dict(name="capsule", objs=objs, f_from=EV["cap_grow"]["f_end"]),
              dict(name="band", objs=[band], f_from=eb["f_end"])]
        for j, gh in enumerate(GH):
            mv.append(dict(name=f"ghost_{j}", objs=[gh["body"], gh["cap"]], f_from=EV["ghost_in"]["f_end"]))
        return clip_check(sc, mv, EV["cap_grow"]["f_end"], NF - 1)
    heroes = dict(capsule=(objs[1], EV["cap_grow"]["f_end"]))
    return finish(sc, Kd, cam, heroes, clip, out_blend, t0, rep_extra)


# ================================================================ 1-10 奖章、名字、AlphaFold、珠链折叠

BEAD_R, BEAD_D = 1.1, 2.3                    # 珠子半径、相邻珠子的间距（mm）
BALL_R, BALL_K = 6.0, 10.0                    # 折好以后那一团：球面螺线的半径、圈数系数
BALL_Z = 22.0                                 # 那一团的中心在芯片上方多高
SURF_R = 2.7                                  # 蛋白表面：每颗珠子外面多大一圈球（并起来再重新布线、磨圆）


def chain_path(port, center):
    """珠链走的路（芯片坐标，mm）：从口子里竖直出来，平滑接到球面螺线的起点，再一圈圈绕到顶。返回每 0.1 mm 一点和累计路程。"""
    th = np.linspace(math.pi - 0.35, 0.35, 4000)
    sp = np.stack([np.sin(th) * np.cos(BALL_K * th), np.sin(th) * np.sin(BALL_K * th), np.cos(th)], 1) * BALL_R + np.array(center)
    up = np.array([port[0], port[1], port[2] + 9.0])
    a, b = up, sp[0]
    ta = np.array([0, 0, 1.0]) * 14.0
    tb = (sp[1] - sp[0]) / np.linalg.norm(sp[1] - sp[0]) * 14.0
    s = np.linspace(0, 1, 400)[:, None]
    h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    conn = h00 * a + h10 * ta + h01 * b + h11 * tb
    line = np.linspace(np.array(port, float), up, 200)
    P = np.concatenate([line, conn[1:], sp[1:]])
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s_ = np.concatenate([[0], np.cumsum(d)])
    L = s_[-1]
    ss = np.arange(0, L, 0.1)
    Q = np.stack([np.interp(ss, s_, P[:, k]) for k in range(3)], 1)
    s_conn = float(s_[len(line) - 1 + len(conn) - 1])
    return Q, ss, s_conn


def path_clearance(Q, ss, gap):
    """路上任意两点，沿路相隔 ≥ gap 的，最近有多远（珠子不互相穿的条件：≥ 2 × 半径）。"""
    step = 5
    q, s = Q[::step], ss[::step]
    D = np.linalg.norm(q[:, None] - q[None], axis=2)
    far = np.abs(s[:, None] - s[None]) >= gap
    return float(D[far].min())


def build_110(out_blend, samples):
    t0 = time.time()
    Kd, EV = load_keys("1-10")
    NF = Kd["len_f"]
    sc = open_board(Kd, samples)
    K = kit()
    M = bpy.data.materials
    zb = board().location.z / MM
    replace_cell(K, "z1_c0_r4", calendar_year(K, "2024"))
    replace_cell(K, "z1_c1_r5", text_plate(K, ["Nobel Prize in Chemistry 2024 (part):", "Demis Hassabis, John Jumper"], w=50.0, hy=10.0, sizes=[3.3, 4.1],
                                           name="p16_names"))
    cells = all_cells()
    C = dict(cal=cell("z1_c0_r4"), medal=cell("z1_c0_r5"), names=cell("z1_c1_r5"), chip=cell("z1_c2_r5"))
    P = {k: cxy(c) for k, c in C.items()}
    chip_root = KP.part_of(C["chip"])
    assert any(o.type == "FONT" and o.data.body == "AlphaFold" for o in chip_root.children), "z1_c2_r5 不是 AlphaFold 芯片"
    port_xy = (-9.6, 9.6)
    for o in list(chip_root.children):                   # 芯片角上的白点就是珠链出来的口子：去掉白点，换成一圈口
        if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "kit_ink_white":
            c = S.coords(o).mean(0) / MM
            if math.hypot(c[0] - port_xy[0], c[1] - port_xy[1]) < 1.5:
                bpy.data.objects.remove(o)
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)
    G, R, OBJ = {}, {}, {}
    for k, fresh in (("cal", "#B8F0C0"), ("medal", "#FFE6A0"), ("names", "#FFF6DC"), ("chip", "#8A8AA0")):
        root, objs, fonts = hero_parts(C[k])
        R[k], OBJ[k] = root, objs
        G[k] = Grow("grow_" + k, root, objs, json.loads(root["gates"]), fresh, emit=1.4, fonts=fonts, cell_x=P[k][0])
    grow_ev = dict(cal="cal_grow", medal="medal_grow", names="names_grow", chip="chip_grow")
    e_sp = EV["medal_spin"]
    EJ = dict(medal=Ejectable(C["medal"], R["medal"], OBJ["medal"], EV["medal_eject"], Float(EV["medal_eject"], 17.0, tilt=28.0, sway=22.0), cells, scar))
    base_z = {c.name: c.location.z for c in cells}

    # 珠链：芯片角上的口子出来；路先算好，检查不自交
    z_chip_top = 2.0
    port = (port_xy[0], port_xy[1], z_chip_top - BEAD_R)
    Q, ss, s_conn = chain_path(port, (0.0, 0.0, BALL_Z))
    L = float(ss[-1])
    clr = path_clearance(Q, ss, 2 * BEAD_D)
    assert clr >= 2 * BEAD_R + 0.1, f"珠链的路离自己太近：{clr:.2f} mm"
    N = int((L - s_conn) // BEAD_D) + 1
    print(f"CH1 1-10 chain: 路长 {L:.1f} mm（接到螺线 {s_conn:.1f}），{N} 颗珠子，路上最近 {clr:.2f} mm")
    chip_c = Vector((P["chip"][0] * MM, P["chip"][1] * MM, zb * MM))
    m_bead = S.hero_mat("bead_blue", M["kit_blue"], "#7A9BFF", emit=2.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=(BEAD_R + 0.45) * MM, minor_radius=0.32 * MM, major_segments=48, minor_segments=12,
                                     location=(chip_c.x + port_xy[0] * MM, chip_c.y + port_xy[1] * MM, chip_c.z + (z_chip_top + 0.05) * MM))
    port_o = bpy.context.object; port_o.name = "chain_port_ring"; bpy.ops.object.shade_smooth(); port_o.data.materials.append(M["kit_ink_white"])
    port_o.parent = chip_root; port_o.matrix_parent_inverse = chip_root.matrix_world.inverted()
    e_cg = EV["chip_grow"]
    for f_, sc_ in ((0, 0.0), (e_cg["f_land"] + 10, 0.0), (e_cg["f_end"], 1.0)):
        port_o.scale = (sc_,) * 3; port_o.keyframe_insert("scale", frame=f_)
    beads = []
    for i in range(N):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=BEAD_R * MM, segments=24, ring_count=12)
        b = bpy.context.object; b.name = f"bead_{i:03d}"; bpy.ops.object.shade_smooth(); b.data.materials.append(m_bead)
        beads.append(b)
    e_out, e_fold = EV["chain_out"], EV["chain_fold"]

    def head(f):
        t = clamp((f - e_out["f_start"]) / (e_fold["f_end"] - e_out["f_start"]))
        return L * (0.35 * t + 0.65 * smoother(t)) if f >= e_out["f_start"] else -1.0

    def bead_at(i, f):
        s = head(f) - i * BEAD_D
        if s <= 0:
            return None, 0.0
        k = clamp(s / (2 * BEAD_R))
        j = min(len(ss) - 1, int(s / 0.1))
        return Q[j], k
    # 蛋白表面：折好的那一团（最后一帧的珠子）外面每颗一个球，中间再填一个，并起来重新布线、磨圆
    fin = [bead_at(i, NF - 1)[0] for i in range(N)]
    assert all(p is not None for p in fin)
    bm = bmesh.new()
    from mathutils import Matrix
    for p, rr in [(p, SURF_R) for p in fin] + [(np.array((0.0, 0.0, BALL_Z)), BALL_R - 1.2)]:
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rr * MM, matrix=Matrix.Translation(Vector(p) * MM))
    me = bpy.data.meshes.new("protein_surface"); bm.to_mesh(me); bm.free()
    surf = KP.link(bpy.data.objects.new("protein_surface", me))
    rmd = surf.modifiers.new("rm", "REMESH"); rmd.mode = "VOXEL"; rmd.voxel_size = 0.3 * MM
    smd = surf.modifiers.new("sm", "SMOOTH"); smd.iterations = 12; smd.factor = 0.6
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(surf.evaluated_get(dg)); surf.modifiers.clear(); surf.data = me2
    for p_ in me2.polygons:
        p_.use_smooth = True
    sb = BVHTree.FromPolygons([tuple(v.co) for v in me2.vertices], [tuple(p_.vertices) for p_ in me2.polygons])
    dmin = min(sb.find_nearest(Vector(p) * MM)[3] for p in fin) / MM
    assert dmin > BEAD_R + 0.4, f"蛋白表面离珠子太近：{dmin:.2f} mm"
    print(f"CH1 1-10 surface: {len(me2.vertices)} 点，珠心到表面最近 {dmin:.2f} mm（珠子半径 {BEAD_R}）")
    m_sf = KP.mat_clear("protein_glass", rgb=(0.62, 0.80, 1.0), density=28.0, rough=0.06, coat=0.6)
    nt = m_sf.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    srcs, srcv = out.inputs["Surface"].links[0].from_socket, out.inputs["Volume"].links[0].from_socket
    fa = nt.nodes.new("ShaderNodeValue"); fa.name = "fade"; fa.outputs[0].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fa.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(srcs, mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    mv_ = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fa.outputs[0], mv_.inputs[0]); nt.links.new(srcv, mv_.inputs[2])
    nt.links.new(mv_.outputs[0], out.inputs["Volume"])
    surf.data.materials.append(m_sf)
    surf.parent = chip_root; surf.matrix_parent_inverse = chip_root.matrix_world.inverted()
    surf.location = chip_c
    for b in beads:
        b.parent = chip_root; b.matrix_parent_inverse = chip_root.matrix_world.inverted()

    # 鼓包：注料口 → 主料杆 → 第 1 列往下穿过第 3 行那一格 → 日历左边的浇口
    RM_, RL, RK = KP.R_MAIN, KP.R_LOOP, 1.2
    x0 = (bpy.data.objects["sprue_cone"].matrix_world.translation.x / MM) + 6
    cx0, cy3 = P["cal"][0], -31.0
    cy4 = P["cal"][1]
    m_pulse = S.hero_mat("pulse_white", M["kit_white"], "#FFEFD0", emit=2.2)
    m_pulse.node_tree.nodes["soft"].outputs[0].default_value = 0.32
    pa = [(x0, 0, RM_), (cx0, 0, RM_), (cx0, -RM_, RK), (cx0, cy3 + KP.CY, RL)] + S.half_loop(cx0, cy3, -1, "t", "b")[1:] + \
         [(cx0, cy4 + KP.CY, RK)] + S.half_loop(cx0, cy4, -1, "t", "s")[1:] + [(cx0 - KP.CX, cy4 + 5.2, RL), (cx0 - 13.0, cy4 + 5.2, RK)]
    PU = [Pulse("pulse_1", m_pulse, pa, EV["pulse_a"])]

    # 镜头
    e = EV
    mx_, my_ = P["medal"]
    nx_, ny_ = P["names"]
    hx_, hy_ = P["chip"]
    kn = [(0, -382, 2, 0, 0.50), (e["cam_a"]["f_land"], -402, -66, 0, 0.33), (e["cam_a"]["f_end"], -412, -80, 0, 0.30),
          (e["cal_grow"]["f_land"] + 15, -432, -86, 0, 0.255), (e["cal_grow"]["f_end"], -434, -94, 0, 0.25),
          (e["cam_medal"]["f_land"], mx_ + 12, my_ + 8, 4, 0.225), (e["medal_grow"]["f_end"], mx_ + 12, my_ + 9, 7, 0.23),
          (e["cam_names"]["f_land"], (mx_ + nx_) / 2 + 4, ny_ + 6, 10, 0.27), (e["names_grow"]["f_end"], (mx_ + nx_) / 2 + 8, ny_ + 6, 10, 0.27),
          (e["cam_chip"]["f_land"], (nx_ + hx_) / 2 + 12, hy_ + 5, 6, 0.255), (e["chip_grow"]["f_end"], hx_ - 8, hy_ + 4, 8, 0.22),
          (e["chain_out"]["f_land"], hx_ - 4, hy_ + 2, 12, 0.20), (e["cam_fold"]["f_land"], hx_, hy_ + 2, BALL_Z - 4, 0.175), (NF - 1, hx_, hy_ + 2, BALL_Z - 3, 0.168)]
    cam = Camera(sc, kn, NF, zb)
    KP.lights(-0.38, -0.06, 1.35)

    e_sf = EV["surface"]
    for f in range(NF):
        for k, g in G.items():
            g.key(f, EV[grow_ev[k]])
        for p in PU:
            p.key(f, zb)
        nz = {}
        for ej in EJ.values():
            ej.key(f, nz)
        key_near(nz, base_z, f)
        if e_out["f_start"] - 2 <= f <= e_fold["f_end"] + 2 or f in (0, NF - 1):
            for i, b in enumerate(beads):
                p, k = bead_at(i, f)
                if p is None:
                    p, k = np.array(port), 0.0
                b.location = Vector((p[0] * MM, p[1] * MM, p[2] * MM)) + chip_c
                b.scale = (k, k, k)
                b.keyframe_insert("location", frame=f); b.keyframe_insert("scale", frame=f)
        v = smoother((f - e_sf["f_start"]) / max(1, e_sf["f_end"] - e_sf["f_start"]))
        fa.outputs[0].default_value = v; fa.outputs[0].keyframe_insert("default_value", frame=f)
        m_bead.node_tree.nodes["soft"].outputs[0].default_value = 0.35 * math.sin(math.pi * clamp((f - e_out["f_start"]) / (e_fold["f_end"] - e_out["f_start"])))
        m_bead.node_tree.nodes["soft"].outputs[0].keyframe_insert("default_value", frame=f)
    rep_extra = dict(chain=dict(beads=N, path_mm=round(L, 1), clearance_mm=round(clr, 2), surface_gap_mm=round(dmin, 2)))

    def clip():
        mv = [dict(name="medal", objs=[o for o in R["medal"].children_recursive if o.type in ("MESH", "FONT", "CURVE")], f_from=EV["medal_eject"]["f_start"],
                   own=C["medal"].name + "_g", f_break=EV["medal_eject"]["f_land"])]

        def out_beads(f):                                   # 还在口子里冒出来的珠子不查（本来就是从口子里出来）
            return [b for i, b in enumerate(beads) if head(f) - i * BEAD_D >= 2 * BEAD_R + 0.3]
        mv.append(dict(name="chain", objs=beads, objs_at=out_beads, f_from=e_out["f_start"]))
        mv.append(dict(name="surface", objs=[surf], f_from=e_sf["f_start"]))
        return clip_check(sc, mv, EV["medal_eject"]["f_start"], NF - 1)
    heroes = dict(medal=(OBJ["medal"][0], EV["medal_grow"]["f_end"]), names=(OBJ["names"][0], EV["names_grow"]["f_end"]), chip=(OBJ["chip"][0], EV["chip_grow"]["f_end"]))
    return finish(sc, Kd, cam, heroes, clip, out_blend, t0, rep_extra)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        fn = dict(zip(("1-02", "1-09", "1-10"), (build_102, build_109, build_110)))[a[1]]
        fn(a[2], int(a[3]) if len(a) > 3 else 48)
    elif a[0] == "frames":
        S.frames(a[1], a[2], [int(x) for x in a[3].split(",")], int(a[4]) if len(a) > 4 else None, int(a[5]) if len(a) > 5 else None)
