"""HKBU SCIE1007 课程作业的科普视频：B 档（Remotion + SVG + GSAP）页面用的 Blender 素材。

11_铺开排序.md 第五节：B 档页面的零件不用 SVG 去画，用 Blender 渲出来的图；Remotion 只管动。这里出三样：

  plate <区号...>   L0 背景：虚化的三维大板，每区一条 720 帧（12 秒）的慢移镜头，焦外约 21 px，比 A 档板面暗 0.3 档。
                    G:/cdk20/work/bplate/zone<N>/####.jpg（来回播放由页面做）。断点续渲：已有的帧跳过。
  sprites [组...]   L2 零件贴图：带透明通道的 PNG，主光在画面左上、暖色，和大板同一套灯；按 2 倍尺寸出。
                    G:/cdk20/work/bsprite/<零件>/<姿态>.png；裁边和尺寸表由 b_sprite_post.py 做。
  wipe <名...>      T5 焦点擦除层：34 帧带透明通道，零件完全虚化从右往左飞过，第 17 帧盖满画面。
                    G:/cdk20/work/bwipe/<名>/####.png。名：runner key socket capsule chip liver。

用法（项目根目录）：
  D:/software/blender-5.3/blender.exe -b --factory-startup -P 镜头设计_v3/inserts/b_assets.py -- plate 5 3 4 8
  D:/software/blender-5.3/blender.exe -b --factory-startup -P 镜头设计_v3/inserts/b_assets.py -- sprites
  D:/software/blender-5.3/blender.exe -b --factory-startup -P 镜头设计_v3/inserts/b_assets.py -- wipe runner socket
可选：blur=像素（背景焦外，默认 21；v2 规则用 12）、suffix=_v2（背景输出目录后缀）、samples=N（背景默认 128、阈值 thr=0.005；贴图 64；擦除 16）、fmul=（背景光圈校正）、test（plate 只渲 1 帧到 zone<N>_test，量时间）、replace（贴图、擦除重渲）。

一律 Cycles + OptiX GPU + OptiX 降噪，不回落 CPU；GPU_PAUSED / GPU_HOLD 存在时等。
"""
import json
import math
import os
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy
from mathutils import Vector, Matrix

WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
if not WORK.exists():
    sys.exit(f"工作盘 {WORK} 不在（G 盘拔了？）：停下，不改写到 C、D。")
BOARD = WORK / "kit/board_final.blend"
FLAGS = [Path.home() / "cdk20_guard" / "GPU_PAUSED", HERE.parents[1] / "_env/queue/GPU_HOLD"]

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPT = {a.split("=")[0]: a.split("=")[1] for a in ARGS if "=" in a}
SAMPLES = int(OPT.get("samples", 16))
TEST = "test" in ARGS


def wait_gpu():
    while any(p.exists() for p in FLAGS):
        print("WAIT_GPU", flush=True)
        time.sleep(15)


def gpu(sc, samples):
    sc.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"
    pr.get_devices()
    gpus = []
    for d in pr.devices:
        d.use = d.type != "CPU"
        if d.use:
            gpus.append(d.name)
    sc.cycles.device = "GPU"
    if not gpus:
        sys.exit("没有 OptiX GPU：不回落 CPU，退出")
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.cycles.adaptive_threshold = float(OPT.get("thr", 0.02))
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    sc.cycles.max_bounces = 10
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.sample_clamp_indirect = 10.0
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    print("RENDER_DEVICE", sc.cycles.device, pr.compute_device_type, gpus, flush=True)


# ---------------------------------------------------------------- L0 背景大板

def zone_center(n):
    cells = [o for o in bpy.data.objects if o.name.startswith(f"z{n}_c") and "_r" in o.name and o.parent and o.parent.name == "board"]
    if not cells:
        sys.exit(f"大板里没有第 {n} 区")
    ps = [o.matrix_world.translation for o in cells]
    c = sum(ps, Vector()) / len(ps)
    return c, cells


def clear_lights():
    for o in list(bpy.data.objects):
        if o.type == "LIGHT" or o.name in ("refl_top", "refl_left"):
            bpy.data.objects.remove(o, do_unlink=True)


# 每区机位：俯角、方位角、距离（米）。z5 和样片里的板面近景同一个机位（kit_parts.build_board 的 z5）。
PLATE_CAM = {1: (30, -28, 0.42), 2: (32, -24, 0.36), 3: (32, -30, 0.38), 4: (32, -30, 0.38),
             5: (32, -32, 0.34), 6: (32, -26, 0.34), 7: (32, -26, 0.34), 8: (32, -30, 0.34)}
NF = 720
BLUR_PX = 21.0          # 目标焦外（1080p 像素），落在 18–25
FOCUS_D = 0.10          # 对焦在板前 0.1 m 的空中：整块板都在焦外，前后虚得均匀
FMUL = 0.25            # 实测校正：薄透镜公式算出的光圈数在 Cycles 里只虚到约 5 px，乘 0.25 到 20–25 px（11-20 试渲 zone5）


def plate(n):
    import kit_parts as KP
    bpy.ops.wm.open_mainfile(filepath=str(BOARD))
    sc = bpy.context.scene
    gpu(sc, int(OPT.get("samples", 128)))       # 大光圈焦外在 16 采样下金件、红件有颗粒，背景用 128 采样 + 0.005 阈值
    sc.cycles.adaptive_threshold = float(OPT.get("thr", 0.005))
    # 1280×720：整块板都在 20 px 以上的焦外，没有高于半奈奎斯特的细节；页面放大 1.5 倍（在 1.6 倍上限内），渲染快一倍多（1920 宽 6.6 s/帧，两个 Blender 共卡）
    pw = int(OPT.get("w", 1280))
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = pw, pw * 9 // 16, 100
    sc.render.fps, sc.render.fps_base = 60, 1.0
    sc.render.use_motion_blur = False
    sc.render.film_transparent = False
    sc.view_settings.exposure -= 0.3              # 比 A 档板面暗 0.3 档
    c, cells = zone_center(n)
    tgt = Vector((c.x, c.y + 0.02, c.z + 0.004))
    clear_lights()
    KP.lights(tgt.x, 0, 1.0)
    el, az, dist = PLATE_CAM[n]
    cam = KP.camera(sc, tgt, dist, el, az, lens=50)
    cd = cam.data
    cd.sensor_width = 36.0
    cd.dof.use_dof = True
    cd.dof.focus_distance = FOCUS_D
    f = cd.lens / 1000.0
    blur = float(OPT.get("blur", BLUR_PX))     # 11-21 B 档视觉规则 v2 R03：焦外 ≤ 14 px，第二版大板用 blur=12、出到 zone<N>_v2
    c_mm = blur / 1920 * 36.0
    k = (f * f / (FOCUS_D - f)) * 1000.0 * (dist - FOCUS_D) / dist      # 毫米·光圈数
    cd.dof.aperture_fstop = k / c_mm * float(OPT.get("fmul", FMUL))
    # 慢移：沿板面横移 40 mm、往前推 6 mm，正弦缓入缓出（来回播放时转折处速度为 0，不跳）
    base, fwd = cam.location.copy(), (tgt - cam.location).normalized()
    side = Vector((1, 0, 0))
    for fr in range(NF):
        u = 0.5 - 0.5 * math.cos(math.pi * fr / (NF - 1))
        cam.location = base + side * (-0.020 + 0.040 * u) + fwd * (0.006 * u)
        cam.keyframe_insert("location", frame=fr)
    for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    out = WORK / "bplate" / (f"zone{n}{OPT.get('suffix', '')}_test" if TEST else f"zone{n}{OPT.get('suffix', '')}")
    out.mkdir(parents=True, exist_ok=True)
    for z0 in out.glob("*.jpg"):              # 上次中断留下的占位空文件（use_placeholder）删掉重渲
        if z0.stat().st_size == 0:
            z0.unlink()
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.render.use_overwrite = TEST
    sc.render.use_placeholder = not TEST
    sc.render.filepath = str(out / "####")
    sc.frame_start, sc.frame_end = (0, 0) if TEST else (0, NF - 1)
    (out / "plate.json").write_text(json.dumps(dict(zone=n, frames=NF, fps=60, blur_px=blur, focus_m=FOCUS_D, fstop=round(cd.dof.aperture_fstop, 2),
                                                    el=el, az=az, dist=dist, samples=sc.cycles.samples, ev=-0.3, size=[pw, pw * 9 // 16], note="来回播放：页面帧 f → 背景帧 pingpong(f, 720)"),
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    wait_gpu()
    t = time.time()
    bpy.ops.render.render(animation=True)
    n_done = sc.frame_end - sc.frame_start + 1
    print(f"PLATE_DONE zone{n} {n_done} frames {time.time() - t:.1f}s ({(time.time() - t) / n_done:.2f} s/f)", flush=True)


# ---------------------------------------------------------------- L2 零件贴图

def fresh(samples=64):
    import kit_parts as KP
    sc = KP.scene_base(samples)
    gpu(sc, samples)
    sc.render.film_transparent = True
    # 玻璃（皿、细胞、烧瓶、试管、肝、插座罩）透明：页面上透过玻璃看到的是真正的大板，不是渲染时看不见的台面（11-20 试渲：皿里透出一块暗方块）
    sc.cycles.film_transparent_glass = True
    sc.cycles.film_transparent_roughness = 0.1
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.use_motion_blur = False
    K = KP.Kit()
    return sc, K


def light_rig(az, k):
    """大板那套灯（主光左上、暖色，加补光、顶灯条、轮廓光和两块反射白卡），整体绕 Z 转到机位的方位角：
    不管从哪个方向拍，主光都在画面左上。"""
    import kit_parts as KP
    before = set(bpy.data.objects)
    KP.lights(0, 0, k)
    rig = bpy.data.objects.new("light_rig", None)
    bpy.context.scene.collection.objects.link(rig)
    for o in set(bpy.data.objects) - before:
        if o is rig:
            continue
        o.parent = rig
    rig.rotation_euler = (0, 0, math.radians(az))
    return rig


def bbox_world(roots):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for r in roots:
        for o in [r] + list(r.children_recursive):
            if o.type not in ("MESH", "CURVE", "FONT") or o.hide_render or "_cut" in o.name or "_hole" in o.name:
                continue
            if any(m.object is o for ob in bpy.data.objects for m in getattr(ob, "modifiers", []) if m.type == "BOOLEAN"):
                continue
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return pts


def ortho_cam(sc, pts, az, el, long_px):
    """正交机位，方位角 az、俯角 el（和 kit_parts.camera 同一约定：az=0 从 -Y 看，screen right=+X）；按投影外框定画幅，长边 long_px 像素。"""
    e, a = math.radians(el), math.radians(az)
    d = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))
    c = sum(pts, Vector()) / len(pts)
    cd = bpy.data.cameras.new("spr_cam")
    cam = bpy.data.objects.new("spr_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = c + d * 2.0
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    M = cam.matrix_world.inverted()
    loc = [M @ p for p in pts]
    xs, ys = [p.x for p in loc], [p.y for p in loc]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    w, h = w * 1.08, h * 1.08
    cd.type = "ORTHO"
    cd.ortho_scale = max(w, h)
    cd.clip_start, cd.clip_end = 0.001, 10
    if w >= h:
        rx, ry = long_px, max(8, round(long_px * h / w))
    else:
        rx, ry = max(8, round(long_px * w / h)), long_px
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = rx, ry, 100
    sc.camera = cam
    return cam


def shoot(sc, part, pose, roots, az, el, long_px):
    out = WORK / "bsprite" / part / f"{pose}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and "replace" not in ARGS:
        print("SKIP", part, pose)
        return
    pts = bbox_world(roots)
    size = max((p - pts[0]).length for p in pts)
    rig = light_rig(az, max(0.12, 3.2 * size))
    # 台面：只给反光和反弹光看，镜头里不出现（贴图透明底）。零件放在台面上方，和大板上一样被浅色台面托着亮
    zmin = min(p.z for p in pts)
    bpy.ops.mesh.primitive_plane_add(size=40 * size, location=(sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts), zmin - 0.0005))
    floor = bpy.context.object
    floor.data.materials.append(bpy.data.materials.get("backdrop") or __import__("kit_parts").mat_solid("backdrop", "#F3EEE6", rough=0.45, coat=0.0, sss=0))
    floor.visible_camera = False
    floor.visible_transmission = False         # 透过玻璃不看见台面（否则透明玻璃底下露出台面边）
    floor.parent = rig
    cam = ortho_cam(sc, pts, az, el, long_px)
    # 锚点（未裁边的像素坐标）：插孔口 mouth、插头座 seat、触点 contact 这些定位空物体，灯，和零件根的原点。页面用它对位（插头插进孔、灯的光晕）
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    anc = {}
    for r in roots:
        for o in [r] + list(r.children_recursive):
            key = o.get("locator") or (o.get("lamp") and f"lamp_{o['lamp']}") or (o is r and f"origin_{r.name.split('.')[0]}")
            if key and key not in anc:
                v = world_to_camera_view(sc, cam, o.matrix_world.translation)
                anc[key] = [round(v.x * rx, 1), round((1 - v.y) * ry, 1)]
    out.with_suffix(".json").write_text(json.dumps(dict(size=[rx, ry], az=az, el=el, mm_per_px=cam.data.ortho_scale / max(rx, ry) * 1000, anchors=anc)), encoding="utf-8")
    wait_gpu()
    t = time.time()
    sc.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print("SPRITE", part, pose, f"{time.time() - t:.1f}s", flush=True)
    for o in list(rig.children):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(rig, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def hide_all():
    for o in bpy.context.scene.objects:
        if o.type != "CAMERA":
            o.hide_render = True


def show(root, on=True):
    for o in [root] + list(root.children_recursive):
        if o.get("lamp") in ("on", "off"):
            continue                     # 灯的开关由 pose 管
        if "_cut" in o.name or "_hole" in o.name:
            continue
        o.hide_render = not on


def sprites(groups):
    import kit_parts as KP
    import kit_socket as S
    MM = KP.MM
    sc, K = fresh(64)
    want = lambda g: not groups or g in groups

    def tidy():
        for o in list(bpy.data.objects):
            if o.type != "CAMERA":
                bpy.data.objects.remove(o, do_unlink=True)

    def set_lamp(root, on):
        S.pose(root, "lamp_out", 1 if on else 0)
        if "lamp_in" in json.loads(root.get("rig", "{}")):
            S.pose(root, "lamp_in", 1 if on else 0)

    def plug(which, scale, x_mm, twist=0.0):
        p = S.h02b_plug(K, which=which, scale=scale)
        p.location = Vector((x_mm * MM, 0, 0))
        S.pose(p, "twist", twist)
        return p

    # 插座（CDK20）hero：合盖，孔面在 +X
    if want("socket"):
        tidy()
        r = S.h01b_cdk20_socket(K)
        S.rest(r)
        set_lamp(r, True)
        shoot(sc, "socket", "hero_34", [r], 58, 26, 1400)
        shoot(sc, "socket", "hero_face", [r], 90, 0, 1400)
        p = plug("048", 1.0, S.SEAT_W, 90)
        S.pose(r, "tab", -25)
        set_lamp(r, False)
        shoot(sc, "socket", "hero_face_048clamp", [r, p], 90, 0, 1400)
        shoot(sc, "socket", "hero_34_048clamp", [r, p], 58, 26, 1400)
        bpy.data.objects.remove(p, do_unlink=True) if False else None
    # 插座 mini（圆孔，红环）：十台小插座、细胞里的那台
    if want("mini"):
        tidy()
        m = S.h01b_cdk20_socket(K, lod="mini", pattern="round")
        S.rest(m)
        set_lamp(m, True)
        shoot(sc, "mini", "m34_on", [m], 58, 26, 900)
        shoot(sc, "mini", "mface_on", [m], 90, 0, 900)
        for which, tw, lamp, tab, pose_name in (("A", 0, True, 0, "m34_plugA"), ("001", 12, True, 0, "m34_001"), ("048", 90, False, -25, "m34_048clamp")):
            p = plug(which, 0.4, 0.4 * S.SEAT_W, tw)
            S.pose(m, "tab", tab)
            set_lamp(m, lamp)
            shoot(sc, "mini", pose_name, [m, p], 58, 26, 900)
            if pose_name == "m34_048clamp":
                shoot(sc, "mini", "mface_048clamp", [m, p], 90, 0, 900)
            for o in [p] + list(p.children_recursive):
                o.hide_render = True
        S.pose(m, "tab", -25)
        set_lamp(m, False)
        shoot(sc, "mini", "mface_off", [m], 90, 0, 900)
    # 插头：侧面（针朝左）和柄端（正对柄面，页面里转它就是拧卡口）
    if want("plugs"):
        for which in ("001", "048", "ATP", "A", "B", "C", "D", "E", "F", "blank"):
            tidy()
            p = S.h02b_plug(K, which=which)
            shoot(sc, "plug", f"{which}_side", [p], 0, 12, 900)
            shoot(sc, "plug", f"{which}_end", [p], 90, 0, 700)
            shoot(sc, "plug", f"{which}_34", [p], 35, 24, 900)
    # AlphaFold 预测模型（4-03 "predicted model"）：CA 主链管，按 pLDDT 上色：≥70 克莱因蓝，50–70 蓝高光，<50 红（和 W2 喷头同一套颜色）
    # 机位：从蛋白中心朝 Arg305（尾巴落进 ATP 口袋的那一个）看过去，口袋和横过来的尾巴朝镜头
    if want("af"):
        tidy()
        pdb = WORK / "structures/AF-Q8IZL9-F1-model_v6.pdb"
        ca = [(int(l[22:26]), Vector((float(l[30:38]), float(l[38:46]), float(l[46:54]))), float(l[60:66]))
              for l in pdb.read_text().splitlines() if l.startswith("ATOM") and l[12:16].strip() == "CA"]
        cen = sum((p for _, p, _ in ca), Vector()) / len(ca)
        r305 = next(p for i, p, _ in ca if i == 305)
        mats = {"hi": K.blue, "mid": K.blue_hi if hasattr(K, "blue_hi") else K.blue, "lo": K.red}
        cls = lambda b: "hi" if b >= 70 else ("mid" if b >= 50 else "lo")
        root = bpy.data.objects.new("af_root", None)
        sc.collection.objects.link(root)
        runs, cur = [], None
        for i, (_, p, b) in enumerate(ca):
            c = cls(b)
            if cur is None or cur[0] != c:
                cur = [c, [ca[i - 1][1]] if i else []]
                runs.append(cur)
            cur[1].append(p)
        for c, pts in runs:
            cu = bpy.data.curves.new("af_" + c, "CURVE")
            cu.dimensions = "3D"
            cu.bevel_depth = 0.95 * MM
            cu.bevel_resolution = 4
            sp = cu.splines.new("NURBS")
            sp.points.add(len(pts) - 1)
            for k, p in enumerate(pts):
                q = (p - cen) * MM
                sp.points[k].co = (q.x, q.y, q.z, 1)
            sp.order_u = min(4, len(pts))
            sp.use_endpoint_u = True
            sp.resolution_u = 8
            ob = bpy.data.objects.new("af_" + c, cu)
            ob.data.materials.append(mats[c])
            sc.collection.objects.link(ob)
            ob.parent = root
        d = (r305 - cen).normalized()
        az = math.degrees(math.atan2(d.x, -d.y))
        el = math.degrees(math.asin(max(-1, min(1, d.z))))
        info = dict(az=az, el=el, n=len(ca), lo=[i for i, _, b in ca if b < 50])
        (WORK / "bsprite" / "af").mkdir(parents=True, exist_ok=True)
        (WORK / "bsprite" / "af" / "af.json").write_text(json.dumps(info), encoding="utf-8")
        shoot(sc, "af", "front305", [root], az, el, 1400)
        shoot(sc, "af", "side", [root], az + 70, 15, 1400)
    # 零件库里的件（kit_parts）
    if want("parts"):
        for name, fn, az, el, px in (("liver", lambda: KP.p04_liver(K, big=True), -10, 72, 1600),
                                     ("cell", lambda: KP.p23_cell(K, "cancer"), -18, 40, 900),
                                     ("cells", lambda: KP.p23_cell(K, "both"), -18, 40, 1200),
                                     ("dish", lambda: KP.p40_dish(K), -18, 42, 1000),
                                     ("flask", lambda: KP.p34_flask(K), 0, 85, 900),
                                     ("calendar", lambda: KP.p10_calendar(K), -18, 36, 900),
                                     ("hkmap", lambda: KP.p07_hk_map(K), -18, 50, 1000),
                                     ("beads", lambda: KP.p42_bead_pile(K), -18, 40, 1000),
                                     ("tube", lambda: KP.p15_sample_tube(K), 0, 70, 900),
                                     ("chip_pandaomics", lambda: KP.p13_chip(K, "PandaOmics"), -18, 40, 900),
                                     ("chip_chemistry42", lambda: KP.p13_chip(K, "Chemistry42"), -18, 40, 900),
                                     ("chip_alphafold", lambda: KP.p13_chip(K, "AlphaFold"), -18, 40, 900),
                                     ("person", lambda: KP.p03_person(K), -18, 24, 700),
                                     ("mol001", lambda: KP.p39_molecules(K, "001"), -18, 50, 1100),
                                     ("mol048", lambda: KP.p39_molecules(K, "048"), -18, 50, 1100)):
            tidy()
            r = fn()
            shoot(sc, name, "34", [r], az, el, px)
    # B 第 2 批要的件：药（胶囊、输液袋）、钱、奖章、废料桶、筛子、回路、数据库架、论文书
    if want("parts2"):
        for name, fn, az, el, px in (("capsule", lambda: KP.p08_capsule(K), -18, 40, 900),
                                     ("ivbag", lambda: KP.p09_iv_bag(K), -10, 30, 900),
                                     ("bill", lambda: KP.p11_bill(K), -18, 50, 900),
                                     ("medal", lambda: KP.p12_medal(K), -10, 40, 800),
                                     ("plugbin", lambda: KP.p44_plug_bin(K), -18, 36, 1000),
                                     ("sieve", lambda: KP.p36_sieve(K), -18, 48, 1000),
                                     ("loop", lambda: KP.p35_loop(K), -18, 55, 1000),
                                     ("dbrack", lambda: KP.p33_db_rack(K), -18, 36, 1000),
                                     ("book", lambda: KP.p17_paper_book(K), -18, 50, 1000),
                                     ("globe", lambda: KP.p06_globe(K), -18, 24, 900)):
            tidy()
            r = fn()
            shoot(sc, name, "34", [r], az, el, px)


    # B 第 4 批（规则 v2：真实对象，不用黑名单图标）：小鼠、挂锁（锁上 / 打开）、一摞硬币、两道跑道、Top 20 表、数据盘
    if want("parts3"):
        def coins():
            P = KP.Part(K, "coins", "gold")
            for i in range(6):
                P.disc(0.6 * math.sin(i * 1.7), 0.5 * math.cos(i * 2.3), 9.0, 1.8, K.gold, z=i * 2.0, bevel=0.5)
            P.gate(-9.5, 0, "-x")
            return P.done()

        def lock(opened):
            r = KP.p21_lock(K)
            if opened:
                sh = next(o for o in r.children_recursive if "_tb" in o.name)
                pivot = Vector((6 * MM, -2 * MM, 0))
                sh.matrix_world = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-35), 4, "Z") @ Matrix.Translation(-pivot)
                                   @ Matrix.Translation((0, 4.5 * MM, 0)) @ sh.matrix_world)
            return r
        for name, pose, fn, az, el, px in (("mouse", "34", lambda: KP.p43_mouse(K), -18, 34, 900),
                                           ("lock", "closed", lambda: lock(False), -10, 62, 700),
                                           ("lock", "open", lambda: lock(True), -10, 62, 700),
                                           ("coins", "34", coins, -18, 30, 700),
                                           ("track", "34", lambda: KP.p45_track(K), -14, 46, 1400),
                                           ("top20", "34", lambda: KP.p28_top20(K), -8, 62, 1000),
                                           ("disks", "34", lambda: KP.p27_data_disks(K), -18, 40, 1000)):
            tidy()
            r = fn()
            bpy.context.view_layer.update()
            shoot(sc, name, pose, [r], az, el, px)


# ---------------------------------------------------------------- T5 焦点擦除层

WIPE_NF, WIPE_MID = 34, 17


def wipe(name):
    import kit_parts as KP
    import kit_socket as S
    sc = KP.scene_base(SAMPLES)
    gpu(sc, max(SAMPLES, 16))
    K = KP.Kit()
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.fps, sc.render.fps_base = 60, 1.0
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    cd = bpy.data.cameras.new("wcam")
    cam = bpy.data.objects.new("wcam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.radians(90), 0, 0)       # 看 +Y
    cd.lens, cd.sensor_width = 35, 36
    cd.clip_start = 0.005
    cd.dof.use_dof = True
    cd.dof.focus_distance = 3.0
    cd.dof.aperture_fstop = 1.2
    depth = 0.24
    # 零件放大到比画面宽 2 倍以上，完全虚化
    if name == "runner":
        # 和出镜段段首同一组料杆（shot_oncam.fg_wipe）：白色料杆加一个浇口，倾 14°，带暖白自发光
        root = bpy.data.objects.new("W_root", None); sc.collection.objects.link(root)
        mw = K.white.copy()
        pb = next(n for n in mw.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        pb.inputs["Emission Color"].default_value = (1.0, 0.93, 0.84, 1)
        pb.inputs["Emission Strength"].default_value = 1.3
        for i, dx in enumerate((-0.085, 0.085)):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=1.8, vertices=48, location=(dx, 0, 0))
            o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(mw); o.parent = root
        bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.02, depth=0.16, vertices=32, location=(0, -0.06, 0.1), rotation=(0, math.radians(90), 0))
        g = bpy.context.object; bpy.ops.object.shade_smooth(); g.data.materials.append(mw); g.parent = root
        root.rotation_euler = (0, math.radians(14), 0)
        span = 0.62
    else:
        build = {"key": lambda: KP.p22_key(K, 2), "socket": lambda: S.h01b_cdk20_socket(K), "capsule": lambda: KP.p08_capsule(K),
                 "chip": lambda: KP.p13_chip(K, "AI"), "liver": lambda: KP.p04_liver(K, big=True)}[name]
        part = build()
        pts = bbox_world([part])
        c = sum(pts, Vector()) / len(pts)
        size = max((p - c).length for p in pts) * 2
        root = bpy.data.objects.new("W_root", None); sc.collection.objects.link(root)
        part.parent = root
        part.location = -c
        s = 0.62 / size
        root.scale = (s * 1.25, s * 1.25, s * 1.25)
        root.rotation_euler = (math.radians(70), math.radians(10), math.radians(-12))   # 板面零件立起来朝镜头
        span = 0.62
        for o in [part] + list(part.children_recursive):      # 近处、离灯远：加一点自发光，焦外是亮的色块不是一团灰
            for sl in getattr(o, "material_slots", []):
                if sl.material and sl.material.use_nodes:
                    m2 = sl.material.copy()
                    pb = next((n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    if pb:
                        bc = pb.inputs["Base Color"].default_value
                        pb.inputs["Emission Color"].default_value = (bc[0], bc[1], bc[2], 1)
                        pb.inputs["Emission Strength"].default_value = 0.9
                    sl.material = m2
    light_rig(0, 1.0)
    for o in bpy.data.objects:
        if o.name.startswith("light_rig"):
            o.location = (0, depth, 0)
    # 从右往左飞过，第 17 帧在画面正中
    for fr in range(-2, WIPE_NF + 2):
        x = 0.012 * 0 + (WIPE_MID - fr) * (2 * span / WIPE_NF) * 1.05
        root.location = (x, depth, 0)
        root.keyframe_insert("location", frame=fr)
    out = WORK / "bwipe" / name
    out.mkdir(parents=True, exist_ok=True)
    sc.render.use_overwrite = "replace" in ARGS
    sc.render.use_placeholder = False
    sc.render.filepath = str(out / "####")
    sc.frame_start, sc.frame_end = 0, WIPE_NF - 1
    wait_gpu()
    t = time.time()
    bpy.ops.render.render(animation=True)
    (out / "wipe.json").write_text(json.dumps(dict(name=name, frames=WIPE_NF, cover=WIPE_MID, dir="right_to_left", depth_m=depth,
                                                   note="A 段结尾用 0–17 帧（进），B 页开头用 17–33 帧（出）；盖满那一帧对齐接点"), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"WIPE_DONE {name} {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    pos = [a for a in ARGS if "=" not in a and a not in ("test", "replace")]
    if not pos:
        sys.exit(__doc__)
    cmd, rest = pos[0], pos[1:]
    if cmd == "plate":
        for z in rest:
            plate(int(z))
    elif cmd == "sprites":
        sprites(rest)
    elif cmd == "wipe":
        for w in rest:
            wipe(w)
    else:
        sys.exit(__doc__)
