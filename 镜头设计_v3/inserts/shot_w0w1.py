"""HKBU SCIE1007 课程作业的科普视频：片头 W0（2.80 s）和大标题 W1（16.83 s）两段三维镜头，连同 1-11 最后 2 秒、2-01 开头 2 秒的衔接。

依据：镜头设计_v3/深化/04_片头与大标题重做.md（逐拍镜头表、验收表）、05_视线引导.md（引导手法，用 bl_guide.py）、
导演意见_1120.md（不硬切、不用红点）。盒盖 h20 来自 kit_h20.py（已验收），大板用 kit_h20_render.py 的缓存 .blend。

时间一律按拍子算：歌的速度、每个大动作落在第几拍都写在卡点表里（音乐/卡点/<段名>_<歌名>.json，beat_sheet.py 读；
环境变量 CDK20_SEG、CDK20_SONG 选表，默认 w0w1 + Blinding Lights 171.007 BPM，一拍 0.3509 s）。
换歌时画面设计不动，只写一张新表，做法见 .claude/skills/beat-retime/SKILL.md。
盒盖版 w1x 是留给 W5 的旧镜头，仍按它原来的 Godmother 拍长（BPM_L）。

两个部分：
  w0    W0 冷开场 168 帧：三下打击点出玻璃肝 → CDK20 → 钥匙 048（焦点点名 + 只照它的轮廓光），全板灯 3% → 100%，焦点拉到镜头前 0.3 m；
        结尾按 07 第二节 T5 焦点擦除接 1-01：一本白色"纸和书"零件贴着镜头（40 mm）从右往左飞过、完全虚掉，
        盖满画面的那几帧里换到 1-01（换点在第 168 帧，正好在盖满的中间）；
  w0wipe 只渲这本书（透明底，第 150–183 帧），合成时叠在 W0 尾和 1-01 头上，两边是同一个动作。
  w1z   11-21 定的《零重力开箱》（07 第一节），代码在 shot_w1z.py；w1x 盒盖版留给 W5 结尾。
  w1x   1-11 最后 120 帧（镜头在香港地图上，"Kong." 说完起升）+ W1 1007 帧（旧拍长；盒盖落下、片名、课程牌、Section 牌、八块牌、盒盖翻开）
        + 2-01 开头 120 帧（镜头落在第 2 区楼群），一镜到底。

名字和学号：只有 --final 时，在这个 Blender 进程里由 title_names.load_members() 读到内存，直接生成文字网格；
不打印、不写日志、不写任何中间文件，--final 时也不许 --save .blend。默认（草稿）是灰条占位。

    blender -b --factory-startup --python-exit-code 1 -P shot_w0w1.py -- w0|w1x [--final] [--samples 24] [--pct 100]
            [--frames all|a-b|f1,f2,…] [--out DIR] [--save X.blend] [--check-only]
渲染一律 Cycles + OPTIX GPU + OptiX 降噪，不回落 CPU（bl_guide._gpu）。帧写在 $CDK20_WORK/w1/<部分>/（默认 D:/cdk20_work）。
"""
import json
import math
import os
import random
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "映射"))
import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import kit_deep as D
import kit_h20 as H
import bl_guide as BG
import beat_sheet as BS

MM = 0.001
FPS = 60
ROOT = HERE.parents[1]
WORK_ROOT = Path(os.environ.get("CDK20_WORK", "D:/cdk20_work"))    # 11-20：G 盘拔走了，工作目录可配置
WORK = WORK_ROOT / "w1"
CACHE = WORK_ROOT / "kit_deep" / "tmp" / "h20_board_cache.blend"
GODMOTHER = ROOT / "镜头设计_v3" / "音乐" / "拍子" / "Godmother.json"
CAVEAT = ROOT / "镜头设计_v2" / "tests" / "T4_remotion" / "public" / "oncam2" / "fonts" / "Caveat.ttf"
QUEUE = (ROOT / "_env" / "queue", Path.home() / "cdk20_guard")

# ---------------------------------------------------------------- 拍子和镜头表（全部按"第几拍"写）

SHEET = BS.load()                                   # 卡点表：现在用的歌
BPM = SHEET["bpm"]
BPM_L = json.loads(GODMOTHER.read_text(encoding="utf-8"))["bpm"]    # 盒盖版 w1x 的旧拍长（留给 W5，不跟着换歌）
W0B = SHEET["w0"]["beats"]                          # W0：三下、灯亮、拉虚、换到 1-01 各在第几拍
LEAD = 2                 # w1x：W1 前面空 2 拍，b0 = 盒盖落地
TAIL, HEAD = 120, 120    # 1-11 最后 2 秒、2-01 开头 2 秒
L111 = 691               # 1-11 在粗剪 v9 里的帧数
W111 = {"Hong": 644, "Kong_end": 676}     # 1-11 段内帧（master_v1：Hong t0 10.73 s，Kong. t1 11.271 s）


def beat_s():
    return 60.0 / BPM


def w0_f(n):
    """W0 里第 n 拍的帧（第 0 拍 = 第 1 下打击 = 第 0 帧）。"""
    return round(FPS * beat_s() * n)


def w1_f(n):
    """盒盖版 w1x 里第 n 拍的帧（b0 = 盒盖落地，前面空 LEAD 拍；旧拍长）。"""
    return round(FPS * 60.0 / BPM_L * (LEAD + n))


NF_W0 = w0_f(W0B["cut"])                     # 168（第 8 拍 = 1-01 的第 0 帧）
WIPE = (NF_W0 - 18, NF_W0 - 7, NF_W0 + 15)    # T5 擦除：进画、开始盖满、离开（W0 帧号，NF_W0 起是 1-01 的第 0 帧）
W0_LENS = 20.0                                # W0 广角（11-21 第二轮：贴近零件）
NF_W1 = BS.f_of_beat(SHEET, SHEET["w1"]["nbeats"])        # 1010（第 48 拍 = 2-01 第一帧），w1z 用
NF_W1L = int(FPS * 60.0 / BPM_L * (LEAD + 32))            # 1007：盒盖版 w1x 的旧长度
NF_W1X = TAIL + NF_W1L + HEAD


def F_w1(n):
    """w1x 序列里第 n 拍的帧。"""
    return TAIL + w1_f(n)


def schedule():
    """镜头表：每个动作的接触帧 = 它的拍点。返回 {部分: [事件]}，事件帧是各自序列里的帧。"""
    b = W0B
    w0 = [dict(id="hit1_liver", beat=b["hit1"], f=w0_f(b["hit1"]), what="第 1 下：引导 → 第 1 区玻璃肝，肝跳 0.8 mm"),
          dict(id="hit2_cdk20", beat=b["hit2"], f=w0_f(b["hit2"]), what="第 2 下：引导 → 第 3 区 CDK20，跳 0.8 mm"),
          dict(id="hit3_key048", beat=b["hit3"], f=w0_f(b["hit3"]), what="第 3 下：引导 → 第 8 区钥匙 048，跳 1.0 mm 转 4°"),
          dict(id="lights_up", beat=b["lights_up"], f=w0_f(b["lights_up"]), f_end=w0_f(b["lights_full"]), what="全板灯 3% → 100%，待机微动起"),
          dict(id="defocus", beat=b["defocus"], f=w0_f(b["defocus"]), f_end=NF_W0, what="焦点拉到镜头前 0.3 m"),
          dict(id="wipe_T5", f=WIPE[0], f_cover=WIPE[1], f_cut=NF_W0, f_end=WIPE[2],
               what="T5 焦点擦除：白色零件贴镜头飞过，盖满时换到 1-01（合成里叠透明层）")]
    w1 = [dict(id="rise", f=W111["Kong_end"] - (L111 - TAIL), what="1-11 \"Kong.\" 说完，镜头起升"),
          dict(id="lid_fall", beat=-1, f=F_w1(-1), what="盒盖从画面上方落入"),
          dict(id="lid_land", beat=0, f=F_w1(0), what="盒盖落地（歌第一拍）"),
          dict(id="full_cover", beat=2, f=F_w1(2), what="镜头到全盖"),
          dict(id="qmark", beat=2, f=F_w1(2), what="红色 ? 落进片名，红线长出"),
          dict(id="badge", beat=3, f=F_w1(3), what="SCIE1007 课程牌卡入（引导 → 课程牌和课程名）"),
          dict(id="sec_plate", beat=4, f=F_w1(4), what="Section 20007 · Group 3B 牌落平")]
    for k, b in enumerate((5, 6, 7, 8, 10, 12, 14, 16)):
        w1.append(dict(id=f"tag_{k}", beat=b, f=F_w1(b), what=f"第 {k + 1} 块章节牌落平"))
    w1 += [dict(id="pull_back", beat=16, f=F_w1(16), f_end=F_w1(20), what="拉回全盖"),
           dict(id="read_hold", beat=20, f=F_w1(20), f_end=F_w1(28), what="全盖停留通读，慢推 3%")]
    for i, b in enumerate((24, 25, 26)):
        w1.append(dict(id=f"art_{i}", beat=b, f=F_w1(b), what=("肝", "CDK20", "钥匙")[i] + " 轻跳 3 mm"))
    w1 += [dict(id="lid_lift", beat=28, f=F_w1(28), what="盒盖抬起 80 mm"),
           dict(id="lid_open", beat=29, f=F_w1(29), f_end=F_w1(31), what="盒盖翻开 0→104→100°（引导 → 第 2 区区号牌和楼群）"),
           dict(id="land_2_01", beat=32, f=TAIL + NF_W1L, what="镜头落在第 2 区楼群，2-01 开始")]
    return dict(w0=w0, w1x=w1)


# ---------------------------------------------------------------- 小工具


def clamp01(t):
    return min(1.0, max(0.0, t))


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def smoother(t):
    t = clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def ease_in(t):
    t = clamp01(t)
    return t * t


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) * (1 - t)


def arc(f, a, n, amp):
    """f 在 [a, a+n] 内走一个正弦拱（0 → amp → 0），其余为 0。"""
    if a <= f <= a + n:
        return amp * math.sin(math.pi * (f - a) / n)
    return 0.0


def fcurves(idb):
    ad = idb.animation_data
    return BG._fcurves(ad.action) if ad and ad.action else []


def linearize(idb):
    for fc in fcurves(idb):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


def bake(idb, path, values, index=-1):
    """values[f] 逐帧的值（标量或元组）；只在值有变化的地方打键（变化段两头各留一个键），插值线性。"""
    n = len(values)
    for f in range(n):
        v = values[f]
        prev = values[f - 1] if f > 0 else None
        nxt = values[f + 1] if f + 1 < n else None
        if f in (0, n - 1) or v != prev or v != nxt:
            if index >= 0:
                getattr(idb, path)[index] = v
                idb.keyframe_insert(path, index=index, frame=f)
            else:
                setattr(idb, path, v)
                idb.keyframe_insert(path, frame=f)
    linearize(idb)


def gpu_wait():
    while any((b / m).exists() for b in QUEUE for m in ("GPU_HOLD", "GPU_PAUSED")):
        print("WAIT_GPU", flush=True)
        time.sleep(15)


def bbox_world(objs):
    pts = []
    for o in objs:
        for m in [o] + list(o.children_recursive):
            if m.type in ("MESH", "FONT", "CURVE") and not m.hide_render:
                pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


# ---------------------------------------------------------------- 镜头：参数轨（目标点 mm、俯角、方位、log 距离）用单调 Hermite 插值


def cam_pose(target_mm, pitch, az, dist_mm):
    e, a = math.radians(pitch), math.radians(az)
    t = Vector(target_mm) * MM
    loc = t + Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e))) * dist_mm * MM
    q = (t - loc).to_track_quat("-Z", "Y")
    return loc, q


def width_dist(width_mm, lens):
    return width_mm * lens / 36.0


class Track:
    """关键状态 [(帧, [tx, ty, tz, 俯角, 方位, ln 距离], 'stop'|'pass')]；pass 的切线逐分量取调和平均（Fritsch–Carlson，不过冲、不来回）。"""

    def __init__(self, keys):
        self.k = keys
        self.m = []
        n = len(keys)
        for i, (F, v, mode) in enumerate(keys):
            if mode == "stop" or i == 0 or i == n - 1:
                self.m.append([0.0] * len(v))
                continue
            F0, v0, _ = keys[i - 1]
            F1, v1, _ = keys[i + 1]
            row = []
            for a, b, c in zip(v0, v, v1):
                d0, d1 = (b - a) / (F - F0), (c - b) / (F1 - F)
                row.append(0.0 if d0 * d1 <= 0 else 2.0 / (1.0 / d0 + 1.0 / d1))
            self.m.append(row)

    def at(self, F):
        k = self.k
        if F <= k[0][0]:
            return list(k[0][1])
        if F >= k[-1][0]:
            return list(k[-1][1])
        for i in range(len(k) - 1):
            Fa, va, _ = k[i]
            Fb, vb, _ = k[i + 1]
            if Fa <= F <= Fb:
                h = Fb - Fa
                t = (F - Fa) / h
                h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
                h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
                return [h00 * a + h10 * h * ma + h01 * b + h11 * h * mb
                        for a, b, ma, mb in zip(va, vb, self.m[i], self.m[i + 1])]
        return list(k[-1][1])


def state(target, pitch, az, width, lens):
    return [target[0], target[1], target[2], pitch, az, math.log(width_dist(width, lens))]


# ---------------------------------------------------------------- 场景


def setup(samples):
    sc = D.scene_base(samples)
    BG._gpu(sc)                                   # OPTIX GPU + OptiX 降噪，不回落 CPU
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.cycles.max_bounces = 8
    sc.cycles.adaptive_threshold = .02
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    D.backdrop()
    D.lights(-.004, 0, 1.6)
    return sc


def relight(sc, lid_mode):
    """04 文档：盒盖顶面主光偏亮（片名一带高光过曝）→ 压主光、加一块大柔光箱补回来，顶上的反光卡也压一档。"""
    O = bpy.data.objects
    key = O["key"]
    key.data.energy *= 0.5
    key.data.size *= 1.6
    key.data.size_y *= 1.6
    O["strip"].data.energy *= 0.55
    bpy.ops.object.light_add(type="AREA", location=(-0.004 - 0.25, -0.75, 1.55))
    sb = bpy.context.object
    sb.name = "softbox"
    sb.data.shape = "RECTANGLE"
    sb.data.size, sb.data.size_y = 2.2, 1.2
    sb.data.energy = 230.0
    sb.data.color = (1, 0.975, 0.945)
    sb.rotation_euler = (Vector((-0.004, 0.0, 0.03)) - sb.location).to_track_quat("-Z", "Y").to_euler()
    for nm in ("refl_top",):
        m = O[nm].active_material
        m.node_tree.nodes["Emission"].inputs["Strength"].default_value = 3.0
    return key


def load_board(sc):
    with bpy.data.libraries.load(str(CACHE)) as (src, dst):
        dst.objects = list(src.objects)
    for ob in dst.objects:
        sc.collection.objects.link(ob)
    root = next(o for o in dst.objects if o.name.startswith("board") and o.parent is None)
    bpy.context.view_layer.update()
    cells = {o.name: o for o in root.children if o.name.startswith("z") and "_c" in o.name}
    return root, cells


def zone_tag(root, n):
    """区号牌 n：zone_tags 下 body == n 的字，连同离它最近的那块牌底板。"""
    zt = next(o for o in root.children if o.name.startswith("zone_tags"))
    txt = next(o for o in zt.children if o.type == "FONT" and o.data.body == str(n))
    base = min((o for o in zt.children if o.type == "MESH"),
               key=lambda o: (o.matrix_world.translation - txt.matrix_world.translation).length)
    return [txt, base]


def text_cap(P, body, cap, x, y, base, mat, italic=False, font=None, relief=.3, align="LEFT"):
    ob = H._text(P, body, cap, x, y, base, mat, italic=italic, relief=relief, align=align)
    if font is not None:
        ob.data.font = font
        ob.data.body = "H"
        bpy.context.view_layer.update()
        h = ob.dimensions.y
        if h > 0:
            ob.data.size *= cap * MM / h
        ob.data.body = body
    return ob


# ---------------------------------------------------------------- 焦点和引导


def bake_camera(cam, sc, poses, lens, fstop, focus_pts):
    """poses[f] = (loc, quat)；focus_pts[f] = 世界坐标点或 ('dist', 米)。逐帧打键。返回逐帧焦距（米）。"""
    cam.data.lens = lens
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.01
    cam.data.clip_end = 30
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.aperture_blades = 0
    cam.rotation_mode = "QUATERNION"
    fd = []
    for f, (loc, q) in enumerate(poses):
        cam.location = loc
        cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
        p = focus_pts[f]
        if isinstance(p, tuple) and p and p[0] == "dist":
            d = p[1]
        else:
            fwd = q @ Vector((0, 0, -1))
            d = max(0.05, (Vector(p) - loc).dot(fwd))
        cam.data.dof.focus_distance = d
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        fd.append(d)
    linearize(cam)
    linearize(cam.data)
    return fd


def rim(plan_item, objs, cam, sc, power, angle=135.0, elev=35.0):
    """bl_guide 的轮廓光（灯光链接只照被点名的零件），灯的位置按落点那一帧的镜头算。"""
    sc.frame_set(max(0, plan_item["land"]))
    bpy.context.view_layer.update()
    lights = BG.guide_rim([plan_item], {plan_item["target"][0]: objs}, cam, bpy.data.objects["key"], power=power, angle=angle, elev=elev)
    return lights[plan_item["id"]]


def plan_item(id_, target, land, gend, rise=12, gon_lead=8, relax=24):
    return dict(id=id_, target=[target], kind="focus", gs=land - rise, gon=land - gon_lead, land=land,
                gend=gend, goff=gend + relax, rim=True)


# ---------------------------------------------------------------- W0


def build_w0(sc, args):
    root, cells = load_board(sc)
    key = relight(sc, False)
    nf = NF_W0
    sc.frame_start, sc.frame_end = 0, nf - 1
    liver_c, cdk_c, key_c = cells["z1_c0_r1"], cells["z3_c4_r0"], cells["z8_c11_r4"]
    parts = {"liver": D.part_of(liver_c), "cdk20": D.part_of(cdk_c), "key048": D.part_of(key_c)}
    hits = {"liver": w0_f(W0B["hit1"]), "cdk20": w0_f(W0B["hit2"]), "key048": w0_f(W0B["hit3"])}
    up0, up1 = w0_f(W0B["lights_up"]), w0_f(W0B["lights_full"])

    # 全板灯 3% → 100%（第 4–5 拍）：所有灯、世界光、反光卡一起乘 m(f)
    m = [0.03 + 0.97 * smooth((f - up0) / (up1 - up0)) for f in range(nf)]
    for o in [o for o in bpy.data.objects if o.type == "LIGHT" and not o.name.startswith("GUIDE_")]:
        e0 = o.data.energy
        bake(o.data, "energy", [e0 * v for v in m])
    bg = sc.world.node_tree.nodes["Background"].inputs[1]
    b0 = bg.default_value
    for f in range(nf):
        bg.default_value = b0 * m[f]
        bg.keyframe_insert("default_value", frame=f)
    for nm in ("refl_top", "refl_left"):
        st = bpy.data.objects[nm].active_material.node_tree.nodes["Emission"].inputs["Strength"]
        s0 = st.default_value
        for f in range(nf):
            st.default_value = s0 * m[f]
            st.keyframe_insert("default_value", frame=f)
    linearize(sc.world.node_tree)

    # 镜头（11-21 第二轮）：20 mm 广角贴着板面，三下各停在被点亮的零件跟前（约 13 cm），两下之间甩过去；
    # 每一下落在拍上时镜头轻震 4 帧；第 4–5 拍全板灯亮起时拉起来看整块大板
    lens = W0_LENS
    P = {k: BG.center(v) for k, v in parts.items()}
    pm = {k: v / MM for k, v in P.items()}
    st = lambda t, p, a, w: state(t, p, a, w, 36.0)        # noqa: E731  最后一维 ln(画宽)
    keys = [(hits["liver"], st(pm["liver"] + Vector((0, 0, 10)), 24.0, -28.0, 240.0), "stop"),
            (hits["cdk20"], st(pm["cdk20"] + Vector((0, 0, 10)), 26.0, -12.0, 240.0), "stop"),
            (hits["key048"], st(pm["key048"] + Vector((0, 0, 8)), 28.0, 18.0, 220.0), "stop"),
            (up0, st((150.0, -20.0, 30.0), 30.0, 8.0, 420.0), "pass"),
            (up1, st((-40.0, 0.0, -10.0), 30.0, -12.0, 1000.0), "pass"),
            (nf - 1, st((-40.0, 0.0, -10.0), 31.0, -13.0, 940.0), "stop")]
    tr = Track(keys)
    poses = []
    for f in range(nf):
        tx, ty, tz, pitch, az, ld = tr.at(f)
        dist = math.exp(ld) * lens / 36.0
        drift = Vector((math.sin(f / 37) * 0.4, math.cos(f / 53) * 0.3, math.sin(f / 29) * 0.2))
        loc, q = cam_pose(Vector((tx, ty, tz)) + drift, pitch, az, dist)
        for h in hits.values():                              # 落拍微震：4 帧衰减
            k = f - h
            if 0 <= k <= 4:
                a_ = (1, -0.7, 0.4, -0.2, 0.08)[k]
                loc = loc + Vector((0.5 * a_, 0, 1.4 * a_)) * MM
                q = q @ Quaternion((1, 0, 0), math.radians(0.35 * a_)) @ Quaternion((0, 0, 1), math.radians(0.25 * a_))
        poses.append((loc, q))
    cam = D.camera(sc, (0, 0, 0), 1, 30, 0)
    # 焦点点名：第 0 帧在肝上；第 2、3 下前 8 帧到位（起拉 18 帧）；第 4 拍起拉到镜头前 0.3 m
    order = [("liver", hits["liver"]), ("cdk20", hits["cdk20"]), ("key048", hits["key048"])]
    focus = []
    f_out0 = w0_f(W0B["defocus"])
    for f in range(nf):
        p = P["liver"]
        for name, land in order[1:]:
            gon, gs = land - 8, land - 8 - 14
            if f >= gs:
                p = p.lerp(P[name], smooth((f - gs) / (gon - gs)))
        focus.append(p)
    fd = bake_camera(cam, sc, poses, lens, 2.8, focus)
    # 拉虚：f_out0 起焦距从当前值缓到 0.3 m（直接改逐帧焦距键）
    for f in range(f_out0, nf):
        d = fd[f_out0] + (0.08 - fd[f_out0]) * smoother((f - f_out0) / (nf - 1 - f_out0))   # 20 mm 广角景深深，拉到 8 cm 才虚得开
        cam.data.dof.focus_distance = d
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        fd[f] = d
    linearize(cam.data)

    # 轮廓光：每下打击点亮一件（爬升 12 帧，第 1 下在第 0 帧已经亮着），下一件起来时退；第 3 下的一直留到全板灯亮起
    f_out0_plan = w0_f(W0B["defocus"])
    items = [plan_item("w0_liver", "liver", hits["liver"], hits["cdk20"] - 10, rise=0, gon_lead=0, relax=18),
             plan_item("w0_cdk20", "cdk20", hits["cdk20"], hits["key048"] - 10, relax=18),
             plan_item("w0_key", "key048", hits["key048"], f_out0_plan, relax=up1 - f_out0_plan)]
    rims = {}
    for it in items:
        ang, el = (162.0, 32.0) if it["id"] == "w0_key" else (120.0, 50.0)      # 金钥匙平躺，灯放在镜面反射方向才亮得起来
        rims[it["id"]] = rim(it, [parts[it["target"][0]]], cam, sc, args.rim_w0 * (0.2 if it["id"] == "w0_key" else 1.0), angle=ang, elev=el)

    # 三下的零件动作：跳起（delta_location z），钥匙另转 4° 回正；浇口颤 3 帧；CDK20 格子外圈料杆轻颤
    jump = {"liver": 0.8, "cdk20": 0.8, "key048": 1.0}
    rnd = random.Random(11)
    idle_parts = []
    for c in sorted(cells):
        try:
            idle_parts.append(D.part_of(cells[c]))
        except StopIteration:
            pass
    phase = {p.name: (rnd.uniform(0, 2 * math.pi), rnd.uniform(70, 115), rnd.uniform(0.6, 1.0)) for p in idle_parts}
    for p in idle_parts:
        name = next((k for k, v in parts.items() if v == p), None)
        ph, per, a = phase[p.name]
        loc, rot = [], []
        for f in range(nf):
            z = 0.0
            rz = 0.0
            if name:
                h = hits[name]
                z = arc(f, h, 6, jump[name]) * MM
                if name == "key048":
                    rz = math.radians(arc(f, h, 10, 4.0))
            ramp = smooth((f - up0) / 30)                     # 待机微动从第 4 拍开始
            rz += math.radians(0.35 * a) * ramp * math.sin(2 * math.pi * f / per + ph)
            z += 0.12 * MM * ramp * math.sin(2 * math.pi * f / (per * 1.3) + ph * 0.7)
            loc.append((0.0, 0.0, round(z, 7)))
            rot.append((0.0, 0.0, round(rz, 7)))
        bake(p, "delta_location", loc)
        bake(p, "delta_rotation_euler", rot)
    for name, cell in (("liver", liver_c), ("cdk20", cdk_c), ("key048", key_c)):
        h = hits[name]
        for g in [g for g in D.gates_of(cell) if not g.name.endswith("_spur")]:
            vals = [(1.0, 1.0, 1.0)] * nf
            for f in range(max(0, h), min(nf, h + 4)):
                s = 1 - arc(f, h, 3, 0.15)
                vals[f] = (s, s, 1.0)
            bake(g, "delta_scale", vals)
    lp = D.loop_of(cdk_c)
    vals = []
    for f in range(nf):
        k = f - hits["cdk20"]
        a = math.radians(0.3) * math.exp(-k / 5) * math.sin(math.pi * k / 3) if 0 <= k <= 12 else 0.0
        vals.append((0.0, 0.0, round(a, 7)))
    bake(lp, "delta_rotation_euler", vals)

    clear = board_clear(poses)
    wiper, wipe_cov = add_wiper(sc, cam, poses)
    chk = dict(part="w0", nf=nf, bpm=BPM, beat_s=beat_s(), song=SHEET["song"], beats=W0B, hits=hits, lights_up=[up0, up1], defocus=[f_out0, nf - 1], wipe=WIPE,
               wipe_cover_frames=wipe_cov, lens_mm=W0_LENS, cam_clear_mm=clear,
               focus_m=[round(v, 4) for v in fd], rims={k: v.name for k, v in rims.items()},
               plan=items, cam_loc_mm=[[round(c / MM, 2) for c in p[0]] for p in poses])
    return cam, chk


def board_clear(poses):
    """镜头离大板（板、料杆、零件，第 0 帧位置）最近多少 mm：所有可见网格合成一棵 BVH，逐帧查最近点。"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    V, Fc = [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or o.name.startswith(("backdrop", "refl_", "w0_wiper")):
            continue
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        base = len(V)
        M = eo.matrix_world
        V.extend([tuple(M @ v.co) for v in me.vertices])
        Fc.extend([[base + i for i in pl.vertices] for pl in me.polygons])
        eo.to_mesh_clear()
    tree = BVHTree.FromPolygons(V, Fc)
    best = (1e9, -1)
    for f, (loc, q) in enumerate(poses):
        hit = tree.find_nearest(loc)
        if hit[0] is not None and hit[3] / MM < best[0]:
            best = (hit[3] / MM, f)
    return dict(min_mm=round(best[0], 1), frame=best[1])


def add_wiper(sc, cam, poses):
    """T5 焦点擦除用的前景零件：零件库的"纸和书"（白），放大到宽约 100 mm，贴着镜头 40 mm 从右往左横穿。
    位置按镜头坐标系算（镜头在 W0 里只慢推），W0 最后一帧之后镜头停在最后一个姿态。返回盖满整个画面的帧。"""
    K = D.Kit()
    P = D.Part(K, "w0_wiper_part", "white")                 # 一块白色亮面料牌（实心，虚掉以后整块不透）
    P.box(0, 0, 105, 48, 6.0, K.white, r=8, bevel=1.2)   # 20 mm 广角画面宽：料牌加宽到 210 mm 才盖得满
    root = P.done()
    for o in [root] + list(root.children_recursive):
        if o.type == "MESH":
            o.visible_shadow = False
    bpy.context.view_layer.update()
    k = 1.0
    root.scale = (k, k, k)
    root.rotation_mode = "QUATERNION"
    root.name = "w0_wiper"
    bpy.context.view_layer.update()
    bb = bbox_world([root])
    ctr = (bb[0] + bb[1]) / 2 - root.matrix_world.translation    # 包围盒中心相对根（已放大、未转）
    f0, f1, f2 = WIPE
    dist = 0.040
    half_w = dist * 18.0 / W0_LENS                           # 40 mm 处半个画面宽
    W = 0.210
    x_in, x_out = half_w + W / 2 + 0.004, -(half_w + W / 2 + 0.004)
    cov = []
    for f in range(f0 - 2, f2 + 2):
        loc, q = poses[min(f, len(poses) - 1)]
        v = clamp01((f - f0) / (f2 - f0))
        x = x_in + (x_out - x_in) * v
        tilt = Quaternion((0, 1, 0), math.radians(10 - 20 * v))   # 零件平放时的 +Z 对着镜头；飞过时轻轻偏转
        p_cam = Vector((x, 0.004 * math.sin(math.pi * v), -dist))
        R = q @ tilt
        root.rotation_quaternion = R
        root.location = loc + q @ p_cam - R @ ctr
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_quaternion", frame=f)
        if abs(x) <= W / 2 - half_w - 0.008:          # 减去虚化光斑半径（约 7 mm）
            cov.append(f)
    linearize(root)
    sc.frame_set(0)
    return root, [min(cov), max(cov)] if cov else []


# ---------------------------------------------------------------- W1（连 1-11 尾、2-01 头）


def roster(K, hinge, members, final):
    """名单行：料杆浮雕上方、盒绘槽下方一行，A–D 四位"名字 学号"。草稿是灰条。"""
    P = D.Part(K, "h20_roster", "white")
    top = H.TOP
    small = next(o for o in bpy.data.objects if o.type == "FONT" and o.data.body == "Inside this kit · who presents each part")
    x0 = max(-272.0, H._xmax(small) - (-4.0) + 18.0)
    x1 = 463.0
    slot = (x1 - x0) / 4
    base_y, cap = -47.0, 15.0
    info = {}
    for i, m in enumerate("ABCD"):
        x = x0 + slot * i
        if final:
            v = members[m]
            t1 = H._text(P, v["name"], cap, x, base_y, top - .01, K.ink, italic=True)
            c1 = H._fit(t1, slot - 8 - (0 if not v["id"] else 0), 11., f"roster {m}")
            info[m] = dict(cap=round(c1, 2))
            if v["id"]:
                body = t1.data.body
                t1.data.body = body + "  " + v["id"]
                c1 = H._fit(t1, slot - 8, 11., f"roster {m}")
                info[m] = dict(cap=round(c1, 2))
        else:
            H._box(P, "roster_pad", x + 62, base_y + cap / 2, 124, cap * .55, top + .14, .3, K.inkg, r=1.6, bevel=.08)
            info[m] = dict(cap=cap, draft=True)
    root = P.done()
    bpy.context.view_layer.update()
    root.parent = hinge
    root.matrix_parent_inverse = hinge.matrix_world.inverted()
    root.location = (-4 * MM, 0, 0)
    return root, info, dict(x0=x0, slot=slot, base_y=base_y)


def pen_note(K, hinge, body, x, y, cap, f_on, f_done):
    """Caveat 手写批注（字贴在盒盖顶面上），用材质里的写出遮罩从左到右写出来。"""
    P = D.Part(K, "h20_pen", "white")
    m = bpy.data.materials.new("pen_note_red")
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.62, 0.03, 0.04, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    val = N.new("ShaderNodeValue")
    val.name = "reveal"
    cmp_ = N.new("ShaderNodeMath")
    cmp_.operation = "LESS_THAN"
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    out = N["Material Output"]
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[0], cmp_.inputs[0])
    nt.links.new(val.outputs[0], cmp_.inputs[1])
    nt.links.new(cmp_.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    font = bpy.data.fonts.load(str(CAVEAT), check_existing=True)
    t = text_cap(P, body, cap, x, y, H.TOP - .01, m, font=font, relief=.12)
    bpy.context.view_layer.update()
    w = t.dimensions.x
    for f, v in ((0, -0.002), (f_on, -0.002), (f_done, w + 0.002)):
        val.outputs[0].default_value = v
        val.outputs[0].keyframe_insert("default_value", frame=f)
    root = P.done()
    root.parent = hinge
    root.matrix_parent_inverse = hinge.matrix_world.inverted()
    root.location = (-4 * MM, 0, 0)
    return t


def build_w1x(sc, args):
    root, cells = load_board(sc)
    key = relight(sc, True)
    sc.view_settings.exposure += args.expo_w1          # 白盒盖顶面整片接近纯白：整体压一点，片名区最大亮度 < 0.95
    nf = NF_W1X
    sc.frame_start, sc.frame_end = 0, nf - 1
    K = D.Kit()
    members = None
    if args.final:
        import title_names
        members = title_names.load_members(draft=False)
        lid = H.h20_kit_box(K, names={m: v["name"] for m, v in members.items()})
    else:
        lid = H.h20_kit_box(K, draft=True)
    lid.location.x = -4 * MM
    H.rest(lid)
    bpy.context.view_layer.update()
    J = H.rig(lid)
    hinge = J["lid_hinge"]
    ros, ros_info, ros_geom = roster(K, hinge, members, args.final)
    note = pen_note(K, hinge, "just watched", -446.0, -143.0, 8.5, F_w1(5) + 8, F_w1(5) + 38)
    spec = json.loads(lid["rig"])
    ev = {e["id"]: e for e in schedule()["w1x"]}

    def role_vals(role, fn):
        cfg = spec[role]
        path, idx = {"rot": ("rotation_euler", 0), "loc": ("location", 2), "scale": ("scale", 0)}[cfg["type"]]
        out = []
        for f in range(nf):
            v = max(cfg["min"], min(cfg["max"], fn(f)))
            if cfg["type"] == "rot":
                out.append(round(math.radians(v), 7))
            elif cfg["type"] == "loc":
                out.append(round(v * MM, 7))
            else:
                out.append(round(max(v, 1e-4), 6))
        bake(J[role], path, out, index=idx)
        return out

    fb = {n: F_w1(n) for n in range(-2, 33)}

    def fall_rot(f, contact, dur, b1, b2):
        """立着（−90）的牌倒下：加速倒（像木板），contact 帧落平，然后回弹 −b1 → 0 → −b2 → 0（14 帧）。"""
        if f < contact - dur:
            return -90.0
        if f < contact:
            return -90.0 + 90.0 * ease_in((f - (contact - dur)) / dur)
        return -(arc(f, contact, 8, b1) + arc(f, contact + 8, 6, b2))

    land = fb[0]
    # 牌在盒盖落地时晃一下（只往前晃，±3° 的一半在立着那一侧被铰链挡住）
    def upright_wobble(f):
        k = f - land
        return 3.0 * abs(math.sin(math.pi * k / 5)) * math.exp(-k / 4) if 0 <= k <= 12 else 0.0

    tag_beats = (5, 6, 7, 8, 10, 12, 14, 16)
    for k, b in enumerate(tag_beats):
        c = fb[b]
        role_vals(f"tag_{k}", lambda f, c=c: fall_rot(f, c, 14, 5.0, 1.5) + (upright_wobble(f) if f < c - 14 else 0.0))
    # 前一块牌被带得轻跳 0.5 mm（delta_location，跟着牌一起）
    for k in range(7):
        c = fb[tag_beats[k + 1]]
        bake(J[f"tag_{k}"], "delta_location", [(0.0, 0.0, round(arc(f, c, 6, 0.5) * MM, 7)) for f in range(nf)])
    role_vals("sec_plate", lambda f: fall_rot(f, fb[4], 15, 6.0, 2.0) + (upright_wobble(f) if f < fb[4] - 15 else 0.0))
    # 课程牌：b3 前悬在 12 mm，b3−6 起先抬 1 mm（预备）再 4 帧卡下去，落后颤 0.3 mm
    def badge(f):
        c = fb[3]
        if f < c - 7:
            return 12.0
        if f < c - 4:
            return 12.0 + 1.0 * smooth((f - (c - 7)) / 3)
        if f < c:
            return 13.0 * (1 - ease_in((f - (c - 4)) / 4))
        return arc(f, c, 4, 0.3)
    role_vals("badge", badge)
    # 问号：b2 前 9 帧从 250 mm 上方加速落下（rig 上限 10 mm 以外直接写 location），落后弹 1.2 mm
    qj = J["qmark"]
    qv = []
    for f in range(nf):
        c = fb[2]
        if f < c - 9:
            z = 250.0
        elif f < c:
            z = 250.0 * (1 - ease_in((f - (c - 9)) / 9))
        else:
            z = arc(f, c, 8, 1.2)
        qv.append(round(z * MM, 7))
    bake(qj, "location", qv, index=2)
    qobjs = [o for o in qj.children_recursive if o.type in ("FONT", "MESH")]
    for o in qobjs:
        bake(o, "hide_render", [f < fb[2] - 9 for f in range(nf)])
    role_vals("rule", lambda f: ease_out((f - fb[2]) / (fb[3] - fb[2])) if f >= fb[2] else 0.0)
    title = next(o for o in bpy.data.objects if o.type == "FONT" and o.data.body == "WORTH TESTING")
    bake(title, "delta_location", [(0.0, 0.0, round(arc(f, fb[2], 4, 0.25) * MM, 7)) for f in range(nf)])
    for i, b in enumerate((24, 25, 26)):
        role_vals(f"art_{i}", lambda f, c=fb[b]: arc(f, c, 10, 3.0))
    # 盒盖抬起：b28−6 起整盒轻压（以底面为原点 z 向缩 1.5%，不碰台面），b28 起一拍抬到 80 mm
    role_vals("lid_lift", lambda f: 80.0 * smooth((f - fb[28]) / (fb[29] - fb[28])) if f >= fb[28] else 0.0)
    def hinge_ang(f):
        a, b = fb[29], fb[31]
        if f < a:
            return 0.0
        u = (f - a) / (b - a)
        return 104.0 * smooth(u / 0.75) - 4.0 * smooth((u - 0.75) / 0.25)
    role_vals("lid_hinge", hinge_ang)

    # 盒盖整体：下落、落地回弹、几下顶面轻震、抬前轻压
    # 起落高度：至少 300 mm（规格），并且在 W1 0.49 s 之前整个盒盖都在画面外（下面算好镜头以后再定）
    cam = D.camera(sc, (0, 0, 0), 1, 30, 0)
    lens = 50.0
    # ---- 镜头参数轨
    mapc = cells["z1_c1_r4"]
    mpart = D.part_of(mapc)
    mc = BG.center(mpart) / MM
    map_focus = mpart.matrix_world @ Vector((6.0 * MM, 3.0 * MM, 3.0 * MM))   # 地图上沙田—白石角一带
    lidw = H.WIDTH
    full = lambda s=1.0: state((-4.0, -2.0, 64.0), 80.0, 0.0, lidw / 0.9 * s, lens)       # noqa: E731
    tags_y = -95.5
    tag_x = lambda k: -4.0 + (-399.0 + 114.0 * k)                                        # noqa: E731
    z2 = cells["z2_c3_r0"]
    bld = D.part_of(z2)
    ztag = zone_tag(root, 2)
    bc = BG.center(bld) / MM
    tc = BG.center(ztag[0]) / MM
    z2t = ((bc.x + tc.x) / 2, (bc.y * 0.6 + tc.y * 0.4), (bc.z + tc.z) / 2)
    keys = [(0, state((mc.x, mc.y, mc.z), 52.0, -14.0, 176.0, lens), "stop"),
            (ev["rise"]["f"], state((mc.x + 3.0, mc.y + 1.0, mc.z), 52.0, -14.0, 168.0, lens), "stop"),
            (fb[0], state((-22.0, 6.0, 40.0), 35.0, -20.0, lidw / 0.86, lens), "pass"),
            (fb[2], full(), "stop"),
            (fb[4], full(0.99), "stop"),
            (fb[5], state((tag_x(1), tags_y, 65.8), 75.0, 0.0, 328.0, lens), "stop"),
            (fb[16], state((tag_x(6), tags_y, 65.8), 75.0, 0.0, 328.0, lens), "stop"),
            (fb[20], full(), "stop"),
            (fb[28], full(0.97), "stop"),
            (TAIL + NF_W1L, state(z2t, 30.0, -15.0, 235.0, lens), "pass"),
            (nf - 1, state((z2t[0] + 2.0, z2t[1], z2t[2]), 30.5, -15.5, 235.0 * 0.95, lens), "stop")]
    tr = Track(keys)
    poses = []
    for f in range(nf):
        tx, ty, tz, pitch, az, ld = tr.at(f)
        jit = Vector((math.sin(f / 41) * 0.5, math.cos(f / 59) * 0.4, math.sin(f / 71) * 0.3))   # 极慢的漂，镜头不死
        loc, q = cam_pose(Vector((tx, ty, tz)) + jit, pitch, az, math.exp(ld))
        k = f - land
        if 0 <= k <= 6:                                                                     # 落地震 1.5 mm、0.3°，6 帧
            s = math.sin(math.pi * k / 3) * (1 - k / 6)
            loc = loc + Vector((0, 0, 1.5 * MM * s))
            q = q @ Quaternion((0, 0, 1), math.radians(0.3) * s)
        poses.append((loc, q))
    # 焦点：跟镜头目标点（它就是这一刻的主体）；1-11 尾在地图的沙田一带；俯冲时挂在区号牌和楼群之间
    focus = []
    for f in range(nf):
        tx, ty, tz, *_ = tr.at(f)
        p = Vector((tx, ty, tz)) * MM
        if f < ev["rise"]["f"]:
            p = map_focus
        focus.append(p)
    fd = bake_camera(cam, sc, poses, lens, 8.0, focus)

    # ---- 盒盖下落高度：W1 0.49 s（b−1）之前整个盒盖在画面外
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    shell = [o for o in lid.children_recursive if o.type == "MESH" and "_shell" in o.name and not o.hide_render]
    corners_local = []
    for o in shell:
        corners_local += [o.matrix_world @ Vector(c) for c in o.bound_box]
    f_fall = fb[-1]

    def visible_at(f, z_mm):
        loc, q = poses[f]
        cam.location, cam.rotation_quaternion = loc, q
        bpy.context.view_layer.update()
        for c in corners_local:
            p = c + Vector((0, 0, z_mm * MM))
            v = world_to_camera_view(sc, cam, p)
            if v.z > 0 and -0.02 <= v.x <= 1.02 and -0.02 <= v.y <= 1.02:
                return True
        # 角都在画外时，盒盖底面中心也看一下（盒盖比画面大的情况）
        v = world_to_camera_view(sc, cam, Vector((-4 * MM, 0, z_mm * MM)))
        return v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1

    h0 = 300.0
    while any(visible_at(f, h0) for f in range(max(0, f_fall - 30), f_fall + 1, 2)) and h0 < 3000:
        h0 += 25.0
    def lid_z(f):
        if f < f_fall:
            return h0
        if f < land:
            return h0 * (1 - ease_in((f - f_fall) / (land - f_fall)))
        k = f - land
        z = arc(k, 0, 8, 4.0) + arc(k, 8, 10, 1.0)
        for c in (fb[3], fb[4]):                                   # 课程牌卡入、Section 牌落平时顶面轻震
            z += abs(arc(f, c, 4, 0.25))
        return z
    bake(lid, "location", [round(lid_z(f) * MM, 7) for f in range(nf)], index=2)
    def squash(f):
        c = fb[28]
        return 1.0 - arc(f, c - 6, 8, 0.015)
    bake(lid, "scale", [round(squash(f), 6) for f in range(nf)], index=2)

    # ---- 引导（05 文档）：1-11 尾 "Hong" 点名地图（焦点已在地图上，轮廓光 + 浇口预颤）；b3 课程牌和课程名（轮廓光）；
    #      b29–b31 第 2 区区号牌和楼群（焦点 + 轮廓光）。全盖停留段不加引导。没有任何点、圈、箭头。
    ffl = W111["Hong"] - (L111 - TAIL)
    items = [plan_item("w1_map", "map", ffl, ev["rise"]["f"] + 10),
             plan_item("w1_badge", "badge", fb[3], fb[3] + 50),
             plan_item("w1_zone2", "zone2", fb[31] + 14, nf - 40)]
    course = next(o for o in bpy.data.objects if o.type == "FONT" and o.data.body == "Molecular Science in Daily Life")
    tgt_objs = {"map": [mpart], "badge": [J["badge"], course], "zone2": [bld] + ztag}
    rims = {}
    for it in items:
        rims[it["id"]] = rim(it, tgt_objs[it["target"][0]], cam, sc, args.rim_w1 * {"map": 0.25, "badge": 0.6, "zone2": 0.6}[it["target"][0]])
    tick = BG.guide_tick(mpart, [g for g in D.gates_of(mapc) if not g.name.endswith("_spur")], D.loop_of(mapc), ffl,
                         rot_deg=BG.tick_rot_cap(cam, sc, mpart, poses[ffl][0], 0.45))

    # ---- 检查数
    sc.frame_set(0)
    chk = dict(part="w1x", nf=nf, bpm=BPM_L, tail=TAIL, head=HEAD, nf_w1=NF_W1L, lid_start_mm=h0,
               beats={str(n): fb[n] for n in fb}, events=schedule()["w1x"], plan=items, tick=tick,
               roster=ros_info, roster_geom=ros_geom, final=bool(args.final),
               focus_m=[round(v, 4) for v in fd], cam_loc_mm=[[round(c / MM, 2) for c in p[0]] for p in poses])
    chk["lid_cam_clear_mm"] = lid_camera_clearance(sc, lid, poses, range(fb[27], nf, 3))
    chk["px"] = text_px(sc, cam, lid, ros, note, fb, members is not None)
    chk["title_box"] = title_boxes(sc, cam, lid, [fb[0], fb[2] + 40, fb[24], fb[27]])
    return cam, chk


def lid_camera_clearance(sc, lid, poses, frames):
    """俯冲时镜头离盒盖网格的最近距离（mm）。"""
    obs = [o for o in lid.children_recursive if o.type in ("MESH", "FONT") and not o.hide_render]
    out = []
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        V, T = [], []
        for o in obs:
            if "_shell" not in o.name:
                continue
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            n = len(V)
            me.calc_loop_triangles()
            V += [eo.matrix_world @ v.co for v in me.vertices]
            T += [(t.vertices[0] + n, t.vertices[1] + n, t.vertices[2] + n) for t in me.loop_triangles]
            eo.to_mesh_clear()
        tree = BVHTree.FromPolygons(V, T, all_triangles=True)
        hit = tree.find_nearest(poses[f][0], 5.0)
        out.append([f, round(hit[3] / MM, 1) if hit[0] is not None else 9999])
    return out


def cap_px(sc, cam, ob, cap):
    bpy.context.view_layer.update()
    mw = ob.matrix_world
    xs = [min(v[0] for v in ob.bound_box), max(v[0] for v in ob.bound_box)]
    res = []
    W, Hh = sc.render.resolution_x, sc.render.resolution_y
    for x in (xs[0], (xs[0] + xs[1]) / 2, xs[1]):
        p0 = mw @ Vector((x, 0, 0))
        up = (mw.to_3x3() @ Vector((0, 1, 0))).normalized() * cap * MM
        a, b = world_to_camera_view(sc, cam, p0), world_to_camera_view(sc, cam, p0 + up)
        res.append(math.hypot((b.x - a.x) * W, (b.y - a.y) * Hh))
    return round(sum(res) / 3, 1)


def text_px(sc, cam, lid, ros, note, fb, final):
    """T3：全盖机位（b24）和牌近景（牌倒下后）的大写字高像素，1080p。名字只记 A–D 字母。"""
    fonts = [o for o in lid.children_recursive if o.type == "FONT"]
    by = lambda s: next(o for o in fonts if o.data.body == s)            # noqa: E731
    out = {}
    sc.frame_set(fb[24])
    out["full_cover_b24"] = {
        "title": cap_px(sc, cam, by("WORTH TESTING"), 48), "SCIE1007": cap_px(sc, cam, by("SCIE1007"), 18),
        "course_name": cap_px(sc, cam, by("Molecular Science in Daily Life"), by("Molecular Science in Daily Life")["cap_mm"]),
        "section_plate": cap_px(sc, cam, by("Section 20007 · Group 3B"), by("Section 20007 · Group 3B")["cap_mm"]),
        "subtitle": cap_px(sc, cam, by("How computers help find cancer drug candidates: the CDK20 story"),
                           by("How computers help find cancer drug candidates: the CDK20 story")["cap_mm"])}
    rf = [o for o in ros.children_recursive if o.type == "FONT"]
    if rf:
        out["full_cover_b24"]["roster_min"] = min(cap_px(sc, cam, o, o["cap_mm"]) for o in rf)
    sc.frame_set(fb[6] + 6)
    out["closeup_b6"] = {"chapter_title_2": cap_px(sc, cam, by("Our question"), 6.5),
                         "all_four_of_us": cap_px(sc, cam, by("All four of us"), 6.0),
                         "pen_note": cap_px(sc, cam, note, 8.5)}
    if rf:
        out["closeup_b6"]["roster_min"] = min(cap_px(sc, cam, o, o["cap_mm"]) for o in rf)
    if final:
        names = [o for o in fonts if o.get("cap_mm") and o.data.body not in ("All four of us",) and o.data.font
                 and "Italic" in o.data.font.filepath and o.matrix_world.translation.y < -0.07]
        sc.frame_set(fb[16] + 4)
        out["closeup_b16_names_min"] = min(cap_px(sc, cam, o, o["cap_mm"]) for o in names) if names else None
    return out


def title_boxes(sc, cam, lid, frames):
    """片名区域（片名、问号、红线、副标题、课程名）在画面上的框，给亮度检查用（像素，左上原点）。"""
    fonts = [o for o in lid.children_recursive if o.type in ("FONT",)]
    want = ("WORTH TESTING", "?", "How computers help find cancer drug candidates: the CDK20 story", "Molecular Science in Daily Life")
    obs = [o for o in fonts if o.data.body in want]
    out = {}
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        pts = [world_to_camera_view(sc, cam, o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box]
        x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
        y0, y1 = 1 - max(p.y for p in pts), 1 - min(p.y for p in pts)
        out[str(f)] = [round(max(0, x0) * 1920), round(max(0, y0) * 1080), round(min(1, x1) * 1920), round(min(1, y1) * 1080)]
    return out


# ---------------------------------------------------------------- 出图


def parse_frames(s, nf):
    if s in (None, "all"):
        return None
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [f for f in out if 0 <= f < nf]


def render(sc, outdir, frames, pct, step=1):
    outdir.mkdir(parents=True, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if sc.render.film_transparent else "RGB"
    sc.render.use_persistent_data = True
    gpu_wait()
    if frames is None:
        sc.render.use_overwrite = False
        sc.render.use_placeholder = True
        sc.render.filepath = str(outdir / "f_")
        sc.frame_step = step                      # 预览 1080p30：隔帧渲（帧号仍是 60 fps 的帧号）
        t = time.time()
        bpy.ops.render.render(animation=True)
        print(f"W1_RENDER_DONE {time.time() - t:.0f}s", flush=True)
        return
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = str(outdir / f"f_{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"W1_FRAME {f} {time.time() - t:.1f}s", flush=True)


class Args:
    pass


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    args = Args()
    args.part = a[0]
    args.final = "--final" in a
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d          # noqa: E731
    args.samples = int(opt("--samples", 16))      # 11-20 导演：一律 16 + OptiX 降噪，看得出噪点的镜头才加，最多 24
    args.pct = int(opt("--pct", 100))
    args.frames = opt("--frames", "none")
    args.step = int(opt("--step", 1))
    args.save = opt("--save")
    args.rim_w0 = float(opt("--rim-w0", 450))
    args.rim_w1 = float(opt("--rim-w1", 24))
    args.expo_w1 = float(opt("--expo-w1", -0.4))
    tag = "final" if args.final else "draft"
    args.out = Path(opt("--out", str(WORK / f"{args.part}_{tag}")))
    if args.final and args.save:
        raise SystemExit("--final 不许存 .blend（名字不落盘）")
    t0 = time.time()
    sc = setup(args.samples)
    if args.part == "w0":
        cam, chk = build_w0(sc, args)
        nf = NF_W0
    elif args.part == "w1x":
        cam, chk = build_w1x(sc, args)
        nf = NF_W1X
    elif args.part == "w0wipe":                    # 只出擦除用的那本书（透明底），叠在 W0 尾和 1-01 头上
        cam, chk = build_w0(sc, args)
        keep = {o for o in bpy.data.objects if o.name.startswith(("w0_wiper", "w0_wiper_part"))}
        keep |= {c for o in list(keep) for c in o.children_recursive}
        for o in bpy.data.objects:
            if o.type in ("MESH", "CURVE", "FONT", "EMPTY") and o not in keep:
                o.hide_render = True
        sc.render.film_transparent = True
        sc.frame_start, sc.frame_end = WIPE[0], WIPE[2]
        chk["part"] = "w0wipe"
        nf = WIPE[2] + 1
    elif args.part == "w1z":                       # 11-21 定的《零重力开箱》（07 文档第一节），盒盖版 w1x 留给 W5
        import shot_w1z
        cam, chk = shot_w1z.build(sc, args)
        nf = shot_w1z.NF
    else:
        raise SystemExit("part: w0 | w1x | w1z")
    chk["build_s"] = round(time.time() - t0, 1)
    chk["samples"] = args.samples
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("W1_BUILD", json.dumps({k: v for k, v in chk.items() if k not in ("focus_m", "cam_loc_mm", "plan", "events")},
                                 ensure_ascii=False, default=str)[:4000], flush=True)
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=args.save)
    if "--check-only" in a:
        return
    if args.frames == "none":
        return
    fr = None if args.frames == "all" else parse_frames(args.frames, nf)
    render(sc, args.out, fr, args.pct, args.step)


if __name__ == "__main__":
    main()
