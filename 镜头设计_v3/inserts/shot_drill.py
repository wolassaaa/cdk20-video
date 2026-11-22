"""HKBU SCIE1007 课程作业的科普视频：三维钻取段的通用引擎（第一段 3-04 钻进 CDK20 插座，11-20）。

一个钻取段 = 大板上的一格零件被点名 → 弹起转正 → 打开 → 镜头钻进机构 → 最深处叠化到公开的真实结构 → 退出 → 转场接下一段。
本文件只放各段共用的部分；每段的编排写在 drill_<段号去横线>.py（例：drill_304.py），里面给 CFG 和 choreograph(ctx)。

时间一律来自 映射/keys/<段>.json（映射/events/<段>.json 经 resolve.py 算出）；脚本里不写帧号，只写"哪个事件的哪一帧"。
帧、场景、缓存一律写 $CDK20_WORK/drill/<段>/（默认 G:/cdk20/work；D 是系统盘，只放代码、文档和导演检查的成品）。

    blender -b --factory-startup -P shot_drill.py -- build  段 [采样]          搭场景、逐帧烘焙、存 scene.blend 和 cam.json、跑穿模自检
    blender -b --factory-startup -P shot_drill.py -- stills 段 0,60,240 [百分比] 抽几帧试渲（不覆盖正式帧）
    blender -b --factory-startup -P shot_drill.py -- render 段 [f0 f1]          整段一次渲完（持久数据，已有的帧跳过）
    blender -b --factory-startup -P shot_drill.py -- real   段                  真实结构层（只渲叠化那几十帧）
    blender -b --factory-startup -P shot_drill.py -- clip   段                  逐帧穿模（BVH，CPU）
    python shot_drill.py comp 段 | audio 段 | check 段 | sheet 段 | report 段  合成、声音、自检、抽帧表、检查页（纯 Python）
一条龙：bash run_drill.sh 段 [步骤]。做法写在项目技能 .claude/skills/drill-3d/SKILL.md。
"""
import importlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAPD = HERE.parent / "映射"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MAPD))
WORK_ROOT = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
FPS = 60
OUT_W, OUT_H = 1920, 1080
FF_NV = str(ROOT / "_env/ffmpeg/ffmpeg.exe")                       # 有 h264_nvenc，但只能往少数几个目录写文件：输出走管道
FF_TD = "D:/software/TouchDesigner/bin/ffmpeg.exe"                 # 能写文件，没有 nvenc：只用来封装（-c copy）
FONTS = HERE.parent / "remotion_public/fusion_s1/fonts"
QUEUE_FLAGS = [ROOT / "_env/queue/GPU_HOLD", ROOT / "_env/queue/GPU_PAUSED", Path.home() / "cdk20_guard/GPU_PAUSED"]

try:
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

MM = 0.001
SENSOR = 8.0          # 镜头传感器宽（毫米）。零件是毫米级的微距：用小传感器 + 等效焦距，对焦距离永远大于真焦距（薄透镜成立），景深也可控


# ================================================================ 段配置
def seg_mod(seg):
    return importlib.import_module("drill_" + seg.replace("-", ""))


def work(seg):
    w = WORK_ROOT / "drill" / seg
    w.mkdir(parents=True, exist_ok=True)
    return w


def load_keys(seg):
    """事件帧：默认读 映射/keys/<段>.json（念词段，resolve.py 出的）。音乐段没有念词，配方里给 make_keys() 按拍点表现算同样格式的 keys（不写进 映射/keys/）。"""
    try:
        M = seg_mod(seg)
    except ImportError:
        M = None
    if M is not None and hasattr(M, "make_keys"):
        K = M.make_keys()
        return K, {e["id"]: e for e in K["events"]}
    K = json.loads((MAPD / "keys" / f"{seg}.json").read_text(encoding="utf-8"))
    EV = {e["id"]: e for e in K["events"]}
    return K, EV


# ================================================================ 缓动
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def smoother(t):
    t = clamp(t)
    return t * t * t * (t * (6 * t - 15) + 10)


def ease_out(t, p=3.0):
    return 1 - (1 - clamp(t)) ** p


def ease_in(t, p=2.0):
    return clamp(t) ** p


def spring(t, zeta=0.55, freq=1.6):
    """0 → 1，从静止出发，过冲一点再停稳（欠阻尼二阶）；t ≥ 1 时已基本停住。"""
    t = clamp(t, 0.0, 10.0)
    w = 2 * math.pi * freq
    wd = w * math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + zeta * w / wd * math.sin(wd * t))


def ramp(f, a, b, fn=smoother):
    """f 从 a 到 b 走 0 → 1。"""
    if b <= a:
        return 1.0 if f >= b else 0.0
    return fn(clamp((f - a) / (b - a)))                                  # 先夹到 0–1：传进来的缓动函数不一定自己夹（3-04 ATP 飞过头又飞回来就是这个）


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def settle(f, f0, amp, n=2.5, dur=14):
    """落位后的衰减余振：f0 起 dur 帧内摆 n 下，幅度 amp 衰减到 0。"""
    if f < f0 or f > f0 + dur:
        return 0.0
    t = (f - f0) / dur
    return amp * math.sin(math.pi * 2 * n * t) * (1 - t) ** 2


# ================================================================ Blender：场景
def gpu(sc):
    """Cycles + OptiX GPU、OptiX 降噪；没有 OptiX 设备就报错退出，不回落 CPU（导演 11-20）。"""
    sc.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"
    pr.get_devices()
    gpus = [d for d in pr.devices if d.type == "OPTIX"]
    if not gpus:
        raise SystemExit("shot_drill: 没有 OptiX 设备，不回落 CPU")
    for d in pr.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.render.use_persistent_data = True
    print("DRILL device", [d.name for d in gpus], flush=True)


def open_board(board, nf, samples):
    bpy.ops.wm.open_mainfile(filepath=str(board))
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_"):
            bpy.data.objects.remove(o)
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.frame_start, sc.frame_end = 0, nf - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = OUT_W, OUT_H, 100
    sc.cycles.samples = samples
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.cycles.glossy_bounces = 6
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    gpu(sc)
    return sc


def find_cell(pred):
    import kit_parts as KP
    cells = [o for o in bpy.data.objects["board"].children if o.name.startswith("z") and "_c" in o.name]
    for c in cells:
        p = KP.part_of(c)
        if p is not None and pred(c, p):
            return c, p
    raise SystemExit("shot_drill: 找不到格子")


def hide_tree(o, frames_vals=None):
    """整棵物体树隐藏（frames_vals=None）或按 [(帧, 隐藏?)] 打开关键帧。"""
    for m in [o] + list(o.children_recursive):
        if frames_vals is None:
            m.hide_render = m.hide_viewport = True
            continue
        for f, h in frames_vals:
            m.hide_render = m.hide_viewport = h
            m.keyframe_insert("hide_render", frame=f)
            m.keyframe_insert("hide_viewport", frame=f)


def key_xform(o, f, loc=None, quat=None, scale=None):
    """逐帧烘焙：位置（米）、四元数、缩放。"""
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if quat is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = quat
        o.keyframe_insert("rotation_quaternion", frame=f)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert("scale", frame=f)


def basis_quat(fwd, up=(0, 0, 1)):
    """零件局部 +X 对准 fwd、局部 +Z 尽量朝 up（插座和插头都用 W = +X、Z 向上）。"""
    f = Vector(fwd).normalized()
    u = Vector(up)
    y = u.cross(f)
    if y.length < 1e-6:
        y = Vector((0, 1, 0)).cross(f)
    y.normalize()
    z = f.cross(y)
    return Matrix((f, y, z)).transposed().to_quaternion()


def linear_all(objs):
    import bl_guide as BG
    for o in objs:
        for idb in (o, getattr(o, "data", None)):
            if idb is not None and getattr(idb, "animation_data", None):
                BG._linear(idb)


def mat_emission_key(mat, frames_vals, input_name="Strength"):
    """给材质里的 Emission 节点打强度关键帧（灯亮灭、红环亮用）。"""
    em = [n for n in mat.node_tree.nodes if n.type == "EMISSION"]
    if not em:
        return
    sock = em[0].inputs[input_name]
    for f, v in frames_vals:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)


def apply_modifiers(root):
    """零件在静止位姿（原点、1:1）时把布尔等修改器烘成网格：零件挪到板上、缩放以后，共面的布尔面会因浮点误差逐帧翻转（红环一帧有一帧没）。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    obs = [o for o in [root] + list(root.children_recursive) if o.type == "MESH" and len(o.modifiers)]
    for o in obs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        o.modifiers.clear()
        o.data = me
    return len(obs)


def add_emission(mat, color, strength):
    """在材质的 Surface 上叠一个 Emission（Add Shader），返回 Emission 节点。"""
    nt = mat.node_tree
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    lk = [l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface"][0]
    src = lk.from_socket
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(src, add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return em


# ================================================================ 镜头
class CamRig:
    """镜头由一串机位键驱动，键之间按缓动插值；键有两种空间：
      world：tgt 是世界坐标（米），az/el 照 kit_parts.camera（az=0 时镜头在 −Y 一侧往 +Y 看），dist 米；
      sock ：tgt 是零件局部毫米（插座 W,U,Z），az/el 是零件局部（az=0 正对 +W，正 az 往 +U 转），dist 毫米（未缩放）。
    sock 键随零件当帧的位姿换成世界坐标。相邻两键同空间时插值球坐标（绕着走，不穿过零件），跨空间时插值世界位置。
    额外：极慢漂移（不停死）、≤ 0.3° 手持感、落位微震（2 帧）。"""

    def __init__(self, keys, part_mat, scale_mm_to_m, spaces=None):
        self.keys = sorted(keys, key=lambda k: k["f"])
        self.part_mat = part_mat              # f -> 零件根的世界矩阵（无缩放）
        self.s = scale_mm_to_m                # 零件局部毫米 → 米（含零件缩放）
        self.spaces = dict(spaces or {})      # 别的零件空间：{名字: (f -> 世界矩阵, 毫米 → 米)}，键里 space=名字（5-04 的料架）
        self.shakes = []

    def shake(self, f, amp_deg=0.25, dur=6):
        self.shakes.append((f, amp_deg, dur))

    def _world(self, k, f):
        if k.get("space", "world") == "world":
            t = Vector(k["tgt"])
            e, a = math.radians(k["el"]), math.radians(k["az"])
            eye = t + Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e))) * k["dist"]
            return eye, t
        M, s = self.spaces[k["space"]] if k["space"] in self.spaces else (self.part_mat, self.s)
        M = M(f)
        t_l = Vector(k["tgt"])
        e, a = math.radians(k["el"]), math.radians(k["az"])
        eye_l = t_l + Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * k["dist"]
        return M @ (eye_l * s), M @ (t_l * s)

    def at(self, f):
        ks = self.keys
        if f <= ks[0]["f"]:
            k0 = k1 = ks[0]; t = 0.0
        elif f >= ks[-1]["f"]:
            k0 = k1 = ks[-1]; t = 0.0
        else:
            i = max(j for j in range(len(ks)) if ks[j]["f"] <= f)
            k0, k1 = ks[i], ks[i + 1]
            fn = {"inout": smoother, "out": ease_out, "in": ease_in, "linear": clamp, "smooth": smooth}[k1.get("ease", "inout")]
            t = fn((f - k0["f"]) / max(1, k1["f"] - k0["f"]))
        lens = lerp(k0.get("lens", 50), k1.get("lens", 50), t)
        roll = lerp(k0.get("roll", 0.0), k1.get("roll", 0.0), t)
        sp0, sp1 = k0.get("space", "world"), k1.get("space", "world")
        if sp0 == sp1 and k0 is not k1:
            k = dict(k1)
            k.update(tgt=vlerp(k0["tgt"], k1["tgt"], t), az=lerp(k0["az"], k1["az"], t), el=lerp(k0["el"], k1["el"], t),
                     dist=k0["dist"] * (k1["dist"] / k0["dist"]) ** t)
            eye, tgt = self._world(k, f)
        else:
            e0, t0 = self._world(k0, f)
            e1, t1 = self._world(k1, f)
            eye, tgt = e0.lerp(e1, t), t0.lerp(t1, t)
        return eye, tgt, lens, roll

    def bake(self, cam, nf, drift=None, hand_deg=0.12):
        """逐帧写镜头位置、朝向、焦距。drift(f) -> (位移米, 偏航度) 由段脚本给（不停死）。返回每帧的 (eye, tgt, lens)。"""
        out = []
        cam.rotation_mode = "QUATERNION"
        for f in range(nf):
            eye, tgt, lens, roll = self.at(f)
            if drift:
                d_eye, d_tgt = drift(f, eye, tgt)
                eye, tgt = eye + d_eye, tgt + d_tgt
            fwd = (tgt - eye).normalized()
            q = fwd.to_track_quat("-Z", "Y")
            # 手持感：几个不成倍数的慢正弦，合起来 ≤ 0.3°
            hx = hand_deg * (0.6 * math.sin(f / 23.0) + 0.4 * math.sin(f / 9.7 + 1.3))
            hy = hand_deg * (0.6 * math.sin(f / 29.0 + 0.7) + 0.4 * math.sin(f / 11.3 + 2.1))
            for (fs, amp, dur) in self.shakes:
                if fs <= f < fs + dur:
                    k = (f - fs) / dur
                    hx += amp * math.sin(math.pi * 3 * k) * (1 - k) ** 2
                    hy += 0.6 * amp * math.sin(math.pi * 3 * k + 1.0) * (1 - k) ** 2
            q = q @ Quaternion((1, 0, 0), math.radians(hx)) @ Quaternion((0, 1, 0), math.radians(hy)) @ Quaternion((0, 0, 1), math.radians(roll))
            cam.location = eye
            cam.rotation_quaternion = q
            cam.data.sensor_width = SENSOR
            cam.data.lens = lens * SENSOR / 36.0              # lens 是 35 mm 等效焦距
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_quaternion", frame=f)
            cam.data.keyframe_insert("lens", frame=f)
            out.append((eye.copy(), tgt.copy(), lens, q.copy()))
        return out


def project(cam_rec, p, sensor_w=36.0):
    """世界点 p 在第 f 帧画面上的像素坐标和深度（不依赖 Blender 场景状态）。cam_rec = (eye, tgt, lens, quat)。"""
    eye, _, lens, q = cam_rec
    d = q.inverted() @ (Vector(p) - eye)
    if d.z >= -1e-9:
        return None
    fpx = lens / sensor_w * OUT_W
    return (OUT_W / 2 + fpx * d.x / -d.z, OUT_H / 2 - fpx * d.y / -d.z, -d.z)


def focus_bake(cam, recs, pts, fstop):
    """逐帧焦距（沿镜头朝向）；pts[f] 是焦点世界坐标。"""
    d = cam.data.dof
    d.use_dof = True
    d.aperture_blades = 0
    d.aperture_fstop = fstop
    out = []
    for f, p in enumerate(pts):
        eye, _, _, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        d.focus_distance = max(0.002, (Vector(p) - eye).dot(fwd))
        d.keyframe_insert("focus_distance", frame=f)
        out.append(d.focus_distance)
    return out


def coc_px(lens, fstop, S, D, sensor_w=36.0):
    """弥散圆直径（像素）。lens 是 35 mm 等效焦距，按 SENSOR 换成真焦距；S 对焦距离、D 物距，米。"""
    sensor_w = SENSOR
    fl = lens * SENSOR / 36.0 * MM
    c = fl * fl / (fstop * max(1e-6, S - fl)) * abs(D - S) / max(1e-6, D)
    return c / (sensor_w * MM) * OUT_W


# ================================================================ 大板：浇口、断开、走料
def make_gates(cell, part_meshes, ends_local, mat, name):
    """从格子外圈的点（格子局部毫米）朝零件打射线，命中点就是浇口尖；返回 [(锥, 起点, 尖)]。"""
    from mathutils.bvhtree import BVHTree
    import kit_parts as KP
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for o in part_meshes:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        me.calc_loop_triangles()
        b = len(vs)
        vs += [e.matrix_world @ v.co for v in me.vertices]
        fs += [tuple(b + i for i in t.vertices) for t in me.loop_triangles]
        e.to_mesh_clear()
    tree = BVHTree.FromPolygons(vs, fs, all_triangles=True)
    out = []
    Mc = cell.matrix_world
    for i, (a_l, d_l) in enumerate(ends_local):
        a = Mc @ (Vector(a_l) * MM)
        d = (Mc.to_3x3() @ Vector(d_l)).normalized()
        hit = tree.ray_cast(a, d, 0.2)
        if hit[0] is None:
            continue
        tip = hit[0] - d * 0.05 * MM
        before = set(bpy.data.objects.keys())
        KP.gate_geo(f"{name}_g{i}", Mc.inverted() @ a, Mc.inverted() @ tip, mat, cell)
        new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
        cone = next(o for o in new if not o.name.endswith("_spur"))
        out.append(dict(cone=cone, spur=[o for o in new if o.name.endswith("_spur")], a=a, tip=tip, dir=d))
    return out


def break_gates(gates, f_tick, f_break, scar_mat, stub_mm=1.3):
    """拔：f_tick → f_break 浇口被拉细（预颤），f_break 那一帧锥换成短一截的残根，残根头上一个白色断口。"""
    import kit_parts as KP
    for g in gates:
        cone = g["cone"]
        cone.scale = (1, 1, 1)
        cone.keyframe_insert("scale", frame=f_tick)
        cone.scale = (0.7, 0.7, 1.0)
        cone.keyframe_insert("scale", frame=f_break - 1)
        a, tip, d = g["a"], g["tip"], g["dir"]
        L = (tip - a).length
        b2 = tip - d * min(stub_mm * MM, 0.6 * L)
        bpy.ops.mesh.primitive_cone_add(radius1=1.2 * MM, radius2=0.7 * MM, depth=(b2 - a).length, vertices=20, location=(a + b2) / 2)
        st = bpy.context.object
        st.name = cone.name + "_stub"
        st.rotation_euler = (b2 - a).to_track_quat("Z", "Y").to_euler()
        bpy.ops.object.shade_smooth()
        st.data.materials.append(cone.data.materials[0])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75 * MM, segments=16, ring_count=8, location=b2)
        sc_ = bpy.context.object
        sc_.name = cone.name + "_scar"
        bpy.ops.object.shade_smooth()
        sc_.data.materials.append(scar_mat)
        for o, visible_before in ((cone, True), (st, False), (sc_, False)):
            hide_tree(o, [(f_break - 1, not visible_before), (f_break, visible_before)])


# ================================================================ 真实结构层（AlphaFold DB 模型）
def pdb_atoms(path):
    """PDB 的重原子：[(链, 残基号, 残基名, 原子名, 元素, x, y, z, B)]，B 列在 AlphaFold 文件里是 pLDDT。"""
    out = []
    for l in Path(path).read_text(encoding="utf-8").splitlines():
        if l.startswith("ATOM") and l[76:78].strip() != "H":
            out.append((l[21], int(l[22:26]), l[17:20], l[12:16].strip(), l[76:78].strip(),
                        float(l[30:38]), float(l[38:46]), float(l[46:54]), float(l[60:66])))
    return out


def way_out(xyz, pocket, n=600):
    """从口袋中心往外，周围最空的方向（沿射线 2 Å 以外离原子最近的距离最大）。返回单位向量和那个距离。"""
    import numpy as np
    i = np.arange(n) + 0.5
    z, a = 1 - 2 * i / n, math.pi * (1 + 5 ** 0.5) * i
    dirs = np.c_[np.sqrt(1 - z * z) * np.cos(a), np.sqrt(1 - z * z) * np.sin(a), z]
    rel = xyz - pocket
    best, bd = None, -1
    for k in range(n):
        s = rel @ dirs[k]
        off = np.linalg.norm(rel - s[:, None] * dirs[k], axis=1)
        m = off[s > 2].min() if (s > 2).any() else 99
        if m > bd:
            bd, best = m, dirs[k]
    return best, bd


# ================================================================ 渲染
def wait_gpu():
    while any(p.exists() for p in QUEUE_FLAGS):
        print("DRILL wait GPU flag", flush=True)
        time.sleep(15)


def render_range(blend, outdir, f0=None, f1=None, prefix="f_"):
    """整段一次渲完（持久数据）；已有的帧跳过（断点续渲）。"""
    wait_gpu()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    sc = bpy.context.scene
    gpu(sc)
    if f0 is not None:
        sc.frame_start = f0
    if f1 is not None:
        sc.frame_end = f1
    Path(outdir).mkdir(parents=True, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    redo = os.environ.get("DRILL_OVERWRITE") == "1"                    # 返修时整段重渲（覆盖旧帧）；默认断点续渲
    sc.render.use_overwrite = redo
    sc.render.use_placeholder = not redo
    sc.render.filepath = str(Path(outdir) / prefix) + "####"
    t = time.time()
    bpy.ops.render.render(animation=True)
    print("DRILL render done", sc.frame_start, sc.frame_end, round(time.time() - t, 1), "s", flush=True)


def stills(blend, outdir, flist, pct=50, samples=None):
    wait_gpu()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    sc = bpy.context.scene
    gpu(sc)
    sc.render.resolution_percentage = pct
    if samples:
        sc.cycles.samples = samples
    Path(outdir).mkdir(parents=True, exist_ok=True)
    for f in flist:
        sc.frame_set(f)
        sc.render.filepath = str(Path(outdir) / f"s_{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"DRILL still {f} {time.time() - t:.1f}s", flush=True)


# ================================================================ 穿模（BVH，CPU）
class BVHCache:
    """逐帧穿模用的 BVH 缓存：网格只取一次（零件都是刚体，修改器已烘），树建在参考物体（零件根）的局部坐标里；
    某个物体相对参考物体的矩阵没变就直接复用上一棵树（插座整体在飘、在转，但机身各件相对它不动）。"""

    def __init__(self, ref=None):
        self.ref = ref
        self.geo = {}
        self.trees = {}

    def _geo(self, o, dg):
        if o.name not in self.geo:
            import numpy as np
            e = o.evaluated_get(dg)
            try:
                me = e.to_mesh()
            except RuntimeError:
                me = None
            if me is None:
                self.geo[o.name] = None
                return None
            me.calc_loop_triangles()
            vs = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
            fs = [tuple(t.vertices) for t in me.loop_triangles]
            e.to_mesh_clear()
            self.geo[o.name] = (vs, fs) if fs else None
        return self.geo[o.name]

    def get(self, objs, dg):
        import numpy as np
        from mathutils.bvhtree import BVHTree
        R = self.ref.matrix_world.inverted() if self.ref is not None else Matrix.Identity(4)
        out = []
        for o in objs:
            if o.type not in ("MESH", "CURVE", "FONT") or o.hide_render:
                continue
            g = self._geo(o, dg)
            if g is None:
                continue
            M = R @ o.matrix_world
            key = tuple(round(M[i][j], 7) for i in range(3) for j in range(4))
            hit = self.trees.get(o.name)
            if hit is None or hit[0] != key:
                vs, fs = g
                A = np.array(M, dtype=np.float64)
                w = vs @ A[:3, :3].T + A[:3, 3]
                lo, hi = Vector(w.min(0)), Vector(w.max(0))
                hit = (key, lo, hi, BVHTree.FromPolygons([tuple(p) for p in w], fs, all_triangles=True))
                self.trees[o.name] = hit
            out.append((o.name, hit[1], hit[2], hit[3]))
        return out


def bvh_world(objs, dg):
    return BVHCache().get(objs, dg)


def overlaps(A, B, pad=0.0):
    hits = []
    for n, lo, hi, t in A:
        for n2, lo2, hi2, t2 in B:
            if n == n2:
                continue
            if all(hi[i] + pad > lo2[i] and hi2[i] + pad > lo[i] for i in range(3)):
                if t.overlap(t2):
                    hits.append((n, n2))
    return hits


def clip_run(seg):
    """按段脚本给的分组逐帧查相交：groups(f) -> [(组名, 物体列表 A, 物体列表 B)]；镜头离最近表面的距离（不能进实体）。
    段脚本的 clip_plan 可给 ref（零件根）：树建在它的局部坐标里并缓存，几百帧也只要几分钟。"""
    W = work(seg)
    bpy.ops.wm.open_mainfile(filepath=str(W / "scene.blend"))
    sc = bpy.context.scene
    M = seg_mod(seg)
    plan = M.clip_plan(sc)
    ref = plan.get("ref")
    C = BVHCache(ref)
    caches = {}                                                          # 组可带第 4 项 = 这组的参考物体（几个各自刚性的东西：插座、料架）
    res = dict(frames=0, hits=[], cam_min_mm=None, cam_min_at=None)
    cam = sc.camera
    t = time.time()
    fl = plan["frames"]
    f0, f1 = int(os.environ.get("CLIP_F0", -1)), int(os.environ.get("CLIP_F1", 10 ** 6))   # 返修后只复查一段：CLIP_F0=1000 CLIP_F1=1419
    fl = [f for f in fl if f0 <= f <= f1] if f0 >= 0 or f1 < 10 ** 6 else fl
    for k, f in enumerate(fl):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        res["frames"] += 1
        for g in plan["groups"](f):
            gname, A, B = g[:3]
            if not A or not B:
                continue
            Cg = C if len(g) < 4 else caches.setdefault(g[3].name if g[3] is not None else "_world", BVHCache(g[3]))
            for h in overlaps(Cg.get(A, dg), Cg.get(B, dg)):
                res["hits"].append(dict(f=f, group=gname, a=h[0], b=h[1]))
        near = plan.get("cam_near")
        if near:
            T = C.get(near(f), dg)
            Rm = ref.matrix_world.inverted() if ref is not None else Matrix.Identity(4)
            p = Rm @ cam.matrix_world.translation
            sc_ = ref.matrix_world.to_scale()[0] if ref is not None else 1.0
            ds = [tr.find_nearest(p) for _, _, _, tr in T]
            dmin = min((d[3] for d in ds if d[0] is not None), default=9.0) * sc_
            if res["cam_min_mm"] is None or dmin / MM < res["cam_min_mm"]:
                res["cam_min_mm"], res["cam_min_at"] = round(dmin / MM, 3), f
        if k % 50 == 0:
            print(f"DRILL clip progress {k}/{len(fl)} f={f} hits={len(res['hits'])} {time.time() - t:.0f}s", flush=True)
    res["sec"] = round(time.time() - t, 1)
    hs = {}
    for h in res["hits"]:
        hs.setdefault(f"{h['group']}:{h['a']}|{h['b']}", []).append(h["f"])
    res["hit_summary"] = {k: [min(v), max(v), len(v)] for k, v in hs.items()}
    (W / ("clip.json" if fl is plan["frames"] else f"clip_{f0}_{f1}.json")).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL clip", json.dumps({k: v for k, v in res.items() if k != "hits"}, ensure_ascii=False)[:3000], flush=True)


# ================================================================ 合成（纯 numpy + PIL）
def _font(size, italic=False, sans=False, hand=False):
    from PIL import ImageFont
    if hand:                                                              # 笔记（Caveat，导演 11-17 定的手写字）
        return ImageFont.truetype(str(FONTS / "Caveat.ttf"), size)
    if sans:                                                              # 出处行：小号无衬线（照 Source 组件）
        return ImageFont.truetype(str(FONTS / "InterTight.ttf"), size)
    return ImageFont.truetype(str(FONTS / ("InstrumentSerif-Italic.ttf" if italic else "InstrumentSerif-Regular.ttf")), size)


def draw_text_layer(items, alpha_of):
    """items: [dict(text, xy, size, color, italic, anchor, shadow)]；alpha_of(item) 0–1。返回 RGBA PIL 图层。"""
    from PIL import Image, ImageDraw, ImageFilter
    lay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    dr, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for it in items:
        a = alpha_of(it)
        if a <= 0.003:
            continue
        fnt = _font(it["size"], it.get("italic", False), it.get("sans", False), it.get("hand", False))
        c = it.get("color", (255, 255, 255))
        if it.get("plate"):                                               # 深色底衬（出处行：压在亮板件上也读得出，11-20 Gemini 审 3-04）
            pc, pa, px_, py_ = it["plate"]
            x0, y0, x1, y1 = dr.textbbox(it["xy"], it["text"], font=fnt, anchor=it.get("anchor", "ls"))
            if it.get("plate_y"):                                         # 11-23（18 的 A1）：底衬上下沿写死（出处行 886–928），不随字形高低变
                y0, y1, py_ = it["plate_y"][0] + py_, it["plate_y"][1] - py_, py_
            dr.rounded_rectangle([x0 - px_, y0 - py_, x1 + px_, y1 + py_], radius=py_ + 2, fill=(*pc, int(255 * pa * a)))
        if it.get("halo"):                                                # 软光晕（模糊后的粗描边）：字压在花背景上也读得出，又不像硬描边
            hc = it["halo"]
            ds.text(it["xy"], it["text"], font=fnt, fill=(*hc, int(190 * a)), anchor=it.get("anchor", "ls"), stroke_width=4, stroke_fill=(*hc, int(190 * a)))
        elif it.get("shadow", True):
            ds.text((it["xy"][0], it["xy"][1] + 1), it["text"], font=fnt, fill=(0, 0, 0, int(150 * a)), anchor=it.get("anchor", "ls"))
        sw, sc_ = it.get("stroke", (0, (0, 0, 0)))
        dr.text(it["xy"], it["text"], font=fnt, fill=(*c, int(255 * a)), anchor=it.get("anchor", "ls"),
                stroke_width=sw, stroke_fill=(*sc_, int(235 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(2.2))
    return Image.alpha_composite(sh, lay)


def dashed_circle(cx, cy, r, width, color, alpha, dash_deg=9.0, gap_deg=5.0, rot=0.0):
    from PIL import Image, ImageDraw
    s = 2
    lay = Image.new("RGBA", (OUT_W * s, OUT_H * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    a = rot
    box = [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s]
    while a < rot + 360:
        dr.arc(box, a, a + dash_deg, fill=(*color, int(255 * alpha)), width=int(width * s))
        a += dash_deg + gap_deg
    return lay.resize((OUT_W, OUT_H), Image.LANCZOS)


def ff_frames(video, scale=None):
    """把视频读成 uint8 数组（N, H, W, 3）；scale=(w,h) 时先缩小。"""
    import numpy as np
    vf = ["-vf", f"scale={scale[0]}:{scale[1]}"] if scale else []
    w, h = scale or (OUT_W, OUT_H)
    raw = subprocess.run([FF_TD, "-v", "error", "-i", str(video)] + vf + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def encode(frames_iter, wav, out_mp4, tmp_dir):
    """nvenc 编码走管道（这台机器上带 nvenc 的 ffmpeg 只能写少数几个目录），再用 TD 的 ffmpeg 封装加声音、faststart。"""
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    mkv = tmp_dir / "video_nvenc.mkv"
    with open(mkv, "wb") as fo:
        p = subprocess.Popen([FF_NV, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "h264_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-cq", "15", "-b:v", "0", "-maxrate", "60M",
                              "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-f", "matroska", "pipe:1"],
                             stdin=subprocess.PIPE, stdout=fo)
        n = 0
        for fr in frames_iter:
            p.stdin.write(fr.tobytes())
            n += 1
        p.stdin.close()
        if p.wait() != 0:
            raise SystemExit("nvenc 编码失败")
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    # 封装加声音：TD 的 ffmpeg 没有 aac 编码器；带 nvenc 的那个能写导演检查文件夹（照 shot_oncam），先写 _tmp 再改名
    tmp = Path(out_mp4).with_name(Path(out_mp4).stem + "_tmp.mp4")
    r = subprocess.run([FF_NV, "-y", "-v", "error", "-i", str(mkv), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(tmp)])          # 不加 -shortest：声音和画面一样长，加了会丢最后一帧
    if r.returncode != 0:
        raise SystemExit("封装失败")
    os.replace(tmp, out_mp4)
    return n


# ================================================================ 声音（合成的塑料声，叠在配音上）
def click(freqs, decay_ms, noise_ms, gain, seed, sr=48000, dur=0.12):
    import numpy as np
    rnd = np.random.default_rng(seed)
    n = int(sr * dur)
    t = np.arange(n) / sr
    nz = np.diff(rnd.standard_normal(n), prepend=0.0)
    y = 0.9 * nz / np.abs(nz).max() * np.exp(-t / (noise_ms / 1000))
    for k, (fq, a) in enumerate(freqs):
        y += a * np.sin(2 * np.pi * fq * t + 0.7 * k) * np.exp(-t / (decay_ms / 1000 / (1 + 0.5 * k)))
    y[:24] *= np.linspace(0, 1, 24)
    return gain * y / np.abs(y).max()


def whoosh(dur_s, gain, seed, sr=48000, f0=300.0, f1=2600.0):
    """甩镜的风声：带通噪声，中心频率从 f0 扫到 f1，起落都软。"""
    import numpy as np
    rnd = np.random.default_rng(seed)
    n = int(sr * dur_s)
    x = rnd.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / sr)
    fc = math.sqrt(f0 * f1)
    X *= np.exp(-0.5 * (np.log(np.maximum(fr, 1) / fc) / 0.7) ** 2)
    y = np.fft.irfft(X, n)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    y = y * env
    return gain * y / np.abs(y).max()


def mix_audio(seg, hits, out_wav, sr=48000):
    """配音原速原样（映射/_cache/remotion_public/map/<段>.wav），叠段脚本给的声音 hits=[(帧, 波形, 声像 0–1)]。"""
    import numpy as np
    import wave
    K, _ = load_keys(seg)
    src = MAPD / "_cache" / "remotion_public" / "map" / f"{seg}.wav"
    with wave.open(str(src), "rb") as w:
        assert w.getframerate() == sr and w.getsampwidth() == 2, "配音应是 48 kHz 16 位"
        ch = w.getnchannels()
        vo = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768.0
    n = int(round(K["len_f"] / FPS * sr))
    mix = np.zeros((n, 2))
    m = min(n, len(vo))
    mix[:m] = vo[:m, :2] if ch >= 2 else np.repeat(vo[:m], 2, axis=1)
    peak = float(np.abs(mix).max()) or 0.5
    for f, y, pan in hits:
        i = int(round(f / FPS * sr))
        j = min(n, i + len(y))
        if i >= n or j <= i:
            continue
        mix[i:j, 0] += y[:j - i] * peak * (1 - pan)
        mix[i:j, 1] += y[:j - i] * peak * pan
    top = float(np.abs(mix).max())
    if top > 0.98:
        mix *= 0.98 / top
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"DRILL audio {out_wav}: {n / sr:.3f}s, {len(hits)} 声", flush=True)


# ================================================================ 命令行
def main():
    if IN_BLENDER and "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
    else:
        a = sys.argv[1:]
    cmd, seg = a[0], a[1]
    M = seg_mod(seg)
    W = work(seg)
    if cmd == "build":
        M.build(seg, int(a[2]) if len(a) > 2 else 16)
    elif cmd == "stills":
        fl = [int(x) for x in a[2].split(",")]
        pct = int(a[3]) if len(a) > 3 else 50
        stills(W / "scene.blend", W / "stills", fl, pct, int(a[4]) if len(a) > 4 else None)
    elif cmd == "render":
        f0 = int(a[2]) if len(a) > 2 else None
        f1 = int(a[3]) if len(a) > 3 else None
        render_range(W / "scene.blend", W / "frames", f0, f1)
    elif cmd == "real":
        M.build_real(seg, *(a[2:]))
    elif cmd == "realstills":
        M.build_real(seg, "stills", *(a[2:]))
    elif cmd == "clip":
        clip_run(seg)
    else:
        getattr(M, cmd)(seg, *a[2:])


if __name__ == "__main__":
    main()
