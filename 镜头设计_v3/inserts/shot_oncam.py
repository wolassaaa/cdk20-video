"""HKBU SCIE1007 课程作业的科普视频：出镜段"人在前 + 人侧后方 3D 零件"通用模块（08_出镜旁3D_调研.md 第十节落地，11-20）。

做法（08 文档第十节）：Blender 一个场景 = 真的三维大板（远处，浅景深虚掉）+ 零件 + 一张"人卡片"（抠像逐帧图当贴图，
相机看不见、只投影）→ Cycles + OptiX GPU 渲"大板 + 零件"一层 → 合成里把人原像素叠回最前 + 光包边 + 颗粒 + 软化 → nvenc 出片。
时间一律来自事件表 映射/keys/<段>.json（resolve.py 出），引导用 bl_guide（焦点点名、轮廓光、浇口预颤）。

所有出镜段共用的部分：
  机位      手机前摄按 26 mm 等效反推；出片上人在 oncam.jsx 的位置（PX/PY/宽 1728），相机用镜头偏移让素材光轴落在原位
  大板      board_final.blend 竖起来当身后的墙（放大、放远，焦外 6–14 px）
  人卡片    只投影（visible_camera 关），T1 试验定的
  光        measure 从脸和白 T 恤量方向、主辅光比、色温、颗粒；calib 用灰球/白球/镜面球回写功率（T2、T3）
  镜头微动  以人卡片中心为轴 ±0.3°（人在合成里不动，大板和零件有 3–8 px 的真视差）
  转场      段首 T5 焦点擦除（近处虚化料杆扫过 + 人淡入），段尾 T1 穿越（真相机推进零件；人按卡片的真实投影移出画面）
  动作库    08 文档第四节 A1–A10 的缓动曲线（pop_curve、spring、ease_*、bezier）
各段只写一个 recipe（在场景里放什么、哪个词做什么），登记进 SEGS / RECIPES。

用法（项目根下 Git Bash）：
  python  镜头设计_v3/inserts/shot_oncam.py measure 3-01          # T2：量光、量颗粒 → G:/cdk20/work/oncam/3-01/light.json
  blender -b --factory-startup -P 镜头设计_v3/inserts/shot_oncam.py -- calib 3-01   # T1 + T3：卡片投影试验、灰球比光、回写功率
  blender ... -- build 3-01 [采样]                                 # 搭整段场景，存 scene.blend + check.json + cam.json
  blender ... -- rimcal 3-01                                       # 轮廓光标定到 +0.18 EV（bl_guide.calib）
  blender ... -- render 3-01 bg|fg                                 # 整段渲（断点续渲）
  blender ... -- frames 3-01 0,184,330 [bg|fg]                     # 抽帧
  python  镜头设计_v3/inserts/shot_oncam.py comp 3-01 [--ab]       # 合成 + nvenc 出片（--ab 只出 T6 开/关对照帧）
  python  镜头设计_v3/inserts/shot_oncam.py check 3-01             # F1/F2/人漂移/黑场/颗粒对比，写 check_comp.json
"""
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
RM = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/manual"
WORK = Path("G:/cdk20/work/oncam")
FF = str(Path(__file__).resolve().parents[2] / "_env/ffmpeg/ffmpeg.exe")   # TouchDesigner 带的 ffmpeg 没有 h264_nvenc，用项目里的
BOARD = "G:/cdk20/work/kit/board_final.blend"
QUEUE = (ROOT / "_env" / "queue", Path.home() / "cdk20_guard")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MAPD))

try:
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    IN_BL = True
except ImportError:
    IN_BL = False

# ---------------------------------------------------------------- 机位（所有出镜段共用）
OUT_W, OUT_H, FPS = 1920, 1080, 60
MM = 0.001
PERSON = dict(x=-301, y=108, w=1728, h=972)          # oncam.jsx：素材 3328×1872 缩到 1728×972 放在 (-301, 108)
EDGE_FEATHER = 60                                     # oncam.jsx：素材右边缘 60 px 渐隐（取景到右边就断了）
HFOV_EQ_MM = 26.0                                     # 手机前摄约 24–28 mm 等效（08 文档 5.1），取 26
F_PX = (PERSON["w"] / 2) * HFOV_EQ_MM / 18.0          # 出片像素焦距 ≈ 1248
AXIS = (PERSON["x"] + PERSON["w"] / 2, PERSON["y"] + PERSON["h"] / 2)   # 素材光轴在出片上的位置 (563, 594)
LENS = F_PX * 36.0 / OUT_W                            # Blender 焦距（36 mm 传感器）≈ 23.4 mm
SHIFT = ((OUT_W / 2 - AXIS[0]) / OUT_W, (AXIS[1] - OUT_H / 2) / OUT_W)
D_PERSON = 0.62                                       # 人卡片离相机（脸宽约 300 px ≈ 0.17 m 反推）
PIVOT_PX = (AXIS[0], AXIS[1])                         # 微动轴心：人卡片中心
FSTOP = 0.9                                           # 11-20 验收：背景零件虚到认得出颜色轮廓、看不清字（大板弥散圆 18–25 px）；等待时锁 2–4 px
BASE_FOCUS = 1.3                                      # 没点名时焦点（零件略虚）
BOARD_D = 8.0                                         # 11-20 验收：大板推远（原 3.6 m），纵深更大、焦外更虚
BOARD_S = 9.2 * BOARD_D / 3.6                         # 大板放大倍数：出片上的版式不变（格距约 210 px，同 bg.jpg）
WALL_DIM = 0.7                                        # 板后墙的底色倍数
BG_DIM = 0.82                                         # 大板亮度目标 = bg.jpg 的 82%（验收：背景降 15–20%）
HAZE_DENSITY = 0.05                                   # 零件和大板之间的薄雾（体积散射）：压背景对比，托住斜进来的暖光
SHAFT_W = 250000.0                                    # 左上斜进来的暖色光（聚光灯，照雾也扫过大板）
MICRO = (0.3, 0.2)                                    # 微动：左右、上下（度）
SAMPLES = 32
GLOSSY_WORLD = 0.9                                    # 镜面光线看见的世界亮度（金属件不发黑）


def px_to_world(u, v, d):
    """出片像素 (u, v) 在基础机位下、深度 d（米）处的世界坐标。相机在原点看 +Y，+Z 向上。"""
    return ((u - AXIS[0]) / F_PX * d, d, (AXIS[1] - v) / F_PX * d)


def world_to_px(p):
    X, Y, Z = p
    return (AXIS[0] + X / Y * F_PX, AXIS[1] - Z / Y * F_PX)


SEGS = {
    "3-01": dict(person="G:/cdk20/work/pub_slim/3-01/person_3-01", n=373, off=8,
                 wav="G:/cdk20/work/pub_slim/3-01/3-01.wav", oncam=RM / "oncam_3-01.json",
                 keys=MAPD / "keys/3-01.json", recipe="lock_key", who="D",
                 head="T5", tail="T1", fade_in=(0, 14),
                 out=ROOT / "导演检查_20261120/10_出镜3D样片_3-01.mp4"),
}


def seg_cfg(seg):
    c = dict(SEGS[seg])
    c["seg"] = seg
    c["work"] = WORK / seg
    c["K"] = json.loads(Path(c["keys"]).read_text(encoding="utf-8"))
    c["nf"] = c["K"]["len_f"]
    return c


def person_k(cfg, f):
    """段帧 → 人物逐帧图编号（oncam：段帧 = 素材帧 + off）。"""
    return max(0, min(cfg["n"] - 1, f - cfg["off"]))


# ---------------------------------------------------------------- 动作库的缓动（08 文档第四节，60 fps）
def clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_out_cubic(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = clamp01(t)
    return t ** 3


def ease_inout_cubic(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t, c=1.70158):
    t = clamp01(t)
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def ease_out_quart(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 4


def spring(t_s, zeta=0.55, w=18.0):
    """阻尼弹簧的偏差（1 → 0），t_s 秒。"""
    if t_s <= 0:
        return 1.0
    wd = w * math.sqrt(1 - zeta * zeta)
    return math.exp(-zeta * w * t_s) * (math.cos(wd * t_s) + zeta * w / wd * math.sin(wd * t_s))


def pop_curve(f, f0, n=14, settle=10, c=1.70158):
    """A1/A2 落位：f0 起 easeOutBack n 帧（过冲约 10%），之后 settle 帧阻尼回弹到 1。"""
    if f <= f0:
        return 0.0
    if f < f0 + n:
        return ease_out_back((f - f0) / n, c)
    return 1.0 + 0.02 * spring((f - f0 - n) / FPS) * (1 - clamp01((f - f0 - n) / max(1, settle)))


def bezier(p0, p1, p2, t):
    a = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
    b = [p1[i] + (p2[i] - p1[i]) * t for i in range(3)]
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


ACTIONS = {   # 给检查页看的动作库清单：代号 → (帧数, 曲线)
    "A1": ("预颤 6 + 弹出 14 easeOutBack + 回弹 10 阻尼弹簧", "pop_curve + bl_guide.guide_tick"),
    "A2": ("24 帧 easeOutCubic 贝塞尔弧 + 10 帧回弹", "bezier + pop_curve"),
    "A3": ("虚到实 18 帧 smoothstep + 轮廓光", "bl_guide.guide_focus/guide_rim"),
    "A7": ("0.6→1.08→1.0，8 + 10 帧", "ease_out_cubic + spring"),
    "A9": ("落位冲击：镜头震 2 帧 ≤ 0.4°", "shake()"),
    "A10": ("20 帧 easeInCubic 沿原路飞回", "bezier + ease_in_cubic"),
    "T1": ("穿越：真相机推进零件", "push()"),
    "T5": ("焦点擦除：近处虚化料杆扫过", "fg_wipe()"),
}


# ---------------------------------------------------------------- T2：量光（纯 numpy）
def _srgb_to_lin(a):
    import numpy as np
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def face_boxes(cfg, f):
    """段帧 f 的脸框、T 恤框（人物逐帧图坐标）。鼻尖来自 oncam_<段>.json（素材坐标）。"""
    D = json.loads(Path(cfg["oncam"]).read_text(encoding="utf-8"))
    nose = D["nose"]
    p = nose[min(len(nose) - 1, f)] or next(q for q in nose if q)
    sc = PERSON["w"] / D["src"][0]
    nx, ny = p[0] * sc, p[1] * sc
    face = (int(nx - 120), int(ny - 150), int(nx + 120), int(ny + 90))
    shirt = (int(nx - 230), int(ny + 300), int(nx + 150), int(ny + 440))
    return face, shirt, (nx, ny)


def measure(seg):
    """08 文档 3.1：脸左右/上下亮度差 → 主光方位、仰角；亮侧/暗侧 → 主辅光比；白 T 恤 R/B → 色温；T 恤平坦区高频残差 → 颗粒。"""
    import numpy as np
    from PIL import Image, ImageFilter
    cfg = seg_cfg(seg)
    rows = []
    for f in range(cfg["off"] + 10, cfg["off"] + cfg["n"] - 5, 24):
        im = Image.open(Path(cfg["person"]) / f"{person_k(cfg, f):04d}.png").convert("RGBA")
        a = np.asarray(im, dtype=np.float32) / 255.0
        face, shirt, (nx, ny) = face_boxes(cfg, f)
        fx0, fy0, fx1, fy1 = face
        F = a[fy0:fy1, fx0:fx1]
        lin = _srgb_to_lin(F[..., :3])
        Y = _lum(lin)
        r, g, b = F[..., 0], F[..., 1], F[..., 2]
        skin = (F[..., 3] > 0.99) & (r > g) & (g > b) & (r > 0.25) & ((r - b) > 0.08)
        h, w = Y.shape
        xs = np.arange(w)[None, :].repeat(h, 0)
        ys = np.arange(h)[:, None].repeat(w, 1)
        cxl = nx - fx0
        L = Y[skin & (xs < cxl - 10)]
        R = Y[skin & (xs > cxl + 10)]
        T = Y[skin & (ys < h * 0.45)]
        B = Y[skin & (ys > h * 0.55)]
        if min(len(L), len(R), len(T), len(B)) < 200:
            continue
        lr = (L.mean() - R.mean()) / (L.mean() + R.mean())
        tb = (T.mean() - B.mean()) / (T.mean() + B.mean())
        bright, dark = (L, R) if L.mean() > R.mean() else (R, L)
        ratio_p = float(np.percentile(bright, 90) / max(1e-4, np.percentile(dark, 10)))
        ratio_m = float(bright.mean() / max(1e-4, dark.mean()))
        sx0, sy0, sx1, sy1 = shirt
        S = a[sy0:sy1, sx0:sx1]
        sm = S[..., 3] > 0.99
        Sl = _srgb_to_lin(S[..., :3])
        neutral = Sl[sm]
        neutral = neutral[_lum(neutral) > np.percentile(_lum(neutral), 50)]
        rb = float(neutral[:, 0].mean() / max(1e-4, neutral[:, 2].mean()))
        shirt_p90 = float(np.percentile(_lum(S[..., :3][sm]), 90))         # 显示值（sRGB）
        shirt_lin_p90 = float(np.percentile(_lum(Sl[sm]), 90))
        # 颗粒：T 恤里最平的 48×48 块，原图减去 2 px 高斯模糊，按通道取标准差（8 位）
        u8 = (S[..., :3] * 255).astype(np.float32)
        blur = np.asarray(Image.fromarray(u8.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
        res = u8 - blur
        best = None
        for yy in range(0, S.shape[0] - 48, 16):
            for xx in range(0, S.shape[1] - 48, 16):
                if not sm[yy:yy + 48, xx:xx + 48].all():
                    continue
                v = blur[yy:yy + 48, xx:xx + 48].std()
                if best is None or v < best[0]:
                    best = (v, res[yy:yy + 48, xx:xx + 48].reshape(-1, 3).std(0))
        # 人物遮罩内沿 6 px 带：比人均值亮多少（有没有逆光）
        al = a[..., 3]
        inner = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(13)), dtype=np.float32) / 255
        band = (al > 0.99) & (inner < 0.5)
        Ya = _lum(_srgb_to_lin(a[..., :3]))
        rim = float(Ya[band].mean() / max(1e-4, Ya[al > 0.99].mean()))
        rows.append(dict(f=f, lr=float(lr), tb=float(tb), ratio_p90_p10=ratio_p, ratio_mean=ratio_m, rb=rb,
                         shirt_p90_srgb=shirt_p90, shirt_lin_p90=shirt_lin_p90,
                         grain=[float(x) for x in best[1]] if best is not None else None, rim_band=rim,
                         lit_side="left" if L.mean() > R.mean() else "right"))
    med = lambda k: float(np.median([r[k] for r in rows]))   # noqa: E731
    lr, tb = med("lr"), med("tb")
    # 08 文档 3.1 的经验换算（起点，之后 T3 灰球校）
    az = float(np.interp(abs(lr), [0, 0.1, 0.25, 0.4, 0.6], [0, 15, 35, 55, 70])) * (1 if lr > 0 else -1)
    el = float(np.interp(max(0.0, tb), [0, 0.05, 0.15, 0.3], [5, 15, 35, 50]))
    rb = med("rb")
    kelvin = float(np.interp(rb, [0.85, 1.0, 1.15, 1.3, 1.5], [7500, 6500, 5000, 4000, 3200]))
    grains = np.array([r["grain"] for r in rows if r["grain"]])
    out = dict(seg=seg, frames=len(rows), lr=lr, tb=tb, az_deg=az, el_deg=el,
               key_fill_ratio_mean=med("ratio_mean"), key_fill_ratio_p90p10=med("ratio_p90_p10"),
               rb=rb, kelvin=kelvin, shirt_p90_srgb=med("shirt_p90_srgb"), shirt_lin_p90=med("shirt_lin_p90"),
               grain_sigma_rgb=[float(x) for x in np.median(grains, 0)] if len(grains) else [1.5, 1.5, 1.8],
               rim_band=med("rim_band"), lit_side=max(set(r["lit_side"] for r in rows), key=[r["lit_side"] for r in rows].count),
               rows=rows,
               note="az>0 = 光从画面左边来；el = 仰角；换算表是 08 文档 3.1 的经验值，T3 灰球再校")
    cfg["work"].mkdir(parents=True, exist_ok=True)
    (cfg["work"] / "light.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM measure", json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False))
    return out


# ================================================================ Blender 端：世界（所有出镜段共用）
def gpu_wait():
    while any((q / m).exists() for q in QUEUE for m in ("GPU_HOLD", "GPU_PAUSED")):
        print("ONCAM WAIT_GPU", flush=True)
        time.sleep(15)


def kelvin_rgb(k):
    """色温 → 线性 RGB（Tanner Helland 近似，绿通道归一到 1）。"""
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [min(255.0, max(0.0, x)) / 255.0 for x in (r, g, b)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return tuple(x / c[1] for x in c)


def setup_render(sc, nf, samples=SAMPLES):
    import bl_guide as BG
    gpu_wait()
    BG._gpu(sc)                                   # Cycles + OptiX GPU + OptiX 降噪；没有 OptiX 就退出，不回落 CPU
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.frame_start, sc.frame_end = 0, nf - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = OUT_W, OUT_H, 100
    sc.cycles.samples = samples
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    sc.cycles.max_bounces = 10
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.sample_clamp_indirect = 10.0        # 08 文档 3.2：防镀铬萤火虫
    sc.cycles.blur_glossy = 1.0
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5           # 180°（08 文档第八节）
    sc.render.film_transparent = False
    sc.render.use_border = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def link_obj(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def mesh_bounds(objs):
    """一组物体（连子物体里的可见网格、曲线）的世界包围盒。"""
    pts = []
    for o in objs:
        for m in [o] + list(o.children_recursive):
            if m.type in ("MESH", "CURVE", "FONT") and not m.hide_render:
                pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def board_setup():
    """定版大板竖起来当人身后的墙：板面 XY → 世界 XZ，朝相机（−Y），放大 BOARD_S 倍，板底面在 BOARD_D。
    第 3 区 c4 列（挂锁那一列，x = −165 mm）落在出片 x = 1400（上一段 2-08 结尾"一把挂锁浮起飞到画面右侧"），板上沿在 y = 140。"""
    sc = bpy.context.scene
    sweep = bpy.data.objects.get("sweep")
    wall_mat = sweep.active_material if sweep else None
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_") or o.name == "sweep":
            bpy.data.objects.remove(o)
    board = bpy.data.objects["board"]
    zb = board.location.z
    xf = link_obj(bpy.data.objects.new("ONCAM_board_xf", None))
    board.parent = xf
    board.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([board])
    xf.rotation_euler = (math.radians(90), 0, 0)
    xf.scale = (BOARD_S,) * 3
    X3 = px_to_world(1400, 540, BOARD_D)[0]
    Ztop = px_to_world(960, 140, BOARD_D)[2]
    xf.location = (X3 - BOARD_S * (-0.165), BOARD_D + BOARD_S * zb, Ztop - BOARD_S * hi.y)
    bpy.context.view_layer.update()
    # 板后面一堵浅色墙（bg.jpg 里板挂在白墙上），用原来 sweep 的材质
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(px_to_world(960, 540, BOARD_D + 0.35)[0], BOARD_D + 0.35, 0.0), rotation=(math.radians(90), 0, 0))
    wall = bpy.context.object; wall.name = "ONCAM_wall"
    wall.scale = (14.0 * BOARD_D / 3.6, 9.0 * BOARD_D / 3.6, 1.0)
    if wall_mat:
        wm = wall_mat.copy(); wm.name = "ONCAM_wall_dim"          # 11-20 验收：背景整体压暗，板后的墙最亮，单独压到 70%
        pb = next((n for n in wm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if wm.use_nodes else None
        if pb is not None:
            c = pb.inputs["Base Color"].default_value
            pb.inputs["Base Color"].default_value = (c[0] * WALL_DIM, c[1] * WALL_DIM, c[2] * WALL_DIM, 1)
        wall.data.materials.append(wm)
    coll = bpy.data.collections.new("ONCAM_board_lit")
    sc.collection.children.link(coll)
    for m in [board, wall] + list(board.children_recursive):
        if m.type in ("MESH", "CURVE", "FONT"):
            coll.objects.link(m)
            # 大板和墙不往零件上反漫射光（T3：不关的话白球左右比卡在 1.15，脸是 2.3——3.6 m 外的亮墙把暗面全照亮了）；
            # 镜面里照样看得见大板，亮面塑料上有板的反射
            m.visible_diffuse = False
    return board, coll


def haze_setup(light):
    """零件（1.3–1.6 m）和大板之间一盒薄雾 + 一盏只照雾的暖色聚光灯从画面左上斜进来（体积光）。
    雾把远处的大板压灰、对比降下来，人和零件跳出来。返回雾的集合（主光、补光、顶光排除它，洗墙光本来只照大板）。"""
    coll = bpy.data.collections.new("ONCAM_haze")
    bpy.context.scene.collection.children.link(coll)
    y0, y1 = 2.4, BOARD_D - 0.3
    ym = (y0 + y1) / 2
    c = Vector(px_to_world(OUT_W / 2, OUT_H / 2, ym))
    wx = OUT_W / F_PX * y1 * 1.4
    wz = OUT_H / F_PX * y1 * 1.4
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(c.x, ym, c.z))
    hz = bpy.context.object; hz.name = "ONCAM_haze_box"
    hz.scale = (wx, y1 - y0, wz)
    for cl in list(hz.users_collection):
        cl.objects.unlink(hz)
    coll.objects.link(hz)
    m = bpy.data.materials.new("oncam_haze"); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Color"].default_value = (1.0, 0.97, 0.92, 1)
    vs.inputs["Density"].default_value = HAZE_DENSITY
    vs.inputs["Anisotropy"].default_value = 0.45
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    hz.data.materials.append(m)
    hz.visible_shadow = False
    sd = bpy.data.lights.new("shaft", "SPOT")
    sd.energy = SHAFT_W
    sd.color = kelvin_rgb(3600)
    sd.spot_size = math.radians(16)
    sd.spot_blend = 0.6
    sd.shadow_soft_size = 0.25
    sh = link_obj(bpy.data.objects.new("shaft", sd))
    sh.location = Vector(px_to_world(-500, -650, 4.2))
    aim = Vector(px_to_world(1250, 420, 6.5))
    sh.rotation_euler = (aim - sh.location).to_track_quat("-Z", "Y").to_euler()
    # 不做灯光链接（体积对灯光链接不起作用，实测只链雾时一点光柱都没有）：这盏暖光也斜扫过大板左上和锁的上沿
    return coll


def make_light(name, kind, loc, aim, size, energy, color, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    if kind == "AREA":
        ld.shape = "RECTANGLE"; ld.size = size; ld.size_y = size_y or size
    ld.energy = energy
    ld.color = color
    o = link_obj(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def light_rig(light, fit, subject, board_coll):
    """主光（窗）按 measure 量的方位放在左前方，大而软；补光在右侧对面；顶上一条软光给亮面塑料一道高光；
    大板另有一盏洗墙光（灯光链接只照大板），大板亮度和别的段用的 bg.jpg 对齐。功率用 calib 回写的 light_fit.json。"""
    col = kelvin_rgb(light["kelvin"])
    az, el = math.radians(fit["az_deg"]), math.radians(fit["el_deg"])
    s = Vector(subject)
    # 方位按"零件看相机的方向"算，不按相机光轴：零件在出片右边、离光轴约 40°，按光轴摆的主光对零件几乎是正面光
    # （T3 第一版白球左右比卡在 1.15，脸是 2.3）。脸差不多在光轴上，所以脸量的方位就是相对视线的方位。
    ys = math.atan2(s.x, s.y)
    d = Vector((-math.sin(az + ys) * math.cos(el), -math.cos(az + ys) * math.cos(el), math.sin(el)))
    key = make_light("key", "AREA", s + d * 2.6, s, 1.6, fit["key_w"], col)
    a2 = math.radians(60) - ys
    df = Vector((math.sin(a2) * 0.985, -math.cos(a2) * 0.985, 0.17))
    fill = make_light("fill", "AREA", s + df * 3.0, s, 2.6, fit["fill_w"], col)
    top = make_light("top", "AREA", s + Vector((0.2, -0.3, 1.4)), s, 1.2, fit["key_w"] * 0.12, col, size_y=0.25)
    bc = bpy.data.objects["ONCAM_board_xf"].location
    kd = BOARD_D / 3.6
    wash = make_light("wash", "AREA", Vector((bc.x - 1.0 * kd, BOARD_D - 2.4 * kd, 1.6 * kd)), Vector(px_to_world(1100, 520, BOARD_D)), 4.0 * kd, fit["wash_w"], col)
    wash.light_linking.receiver_collection = board_coll
    # 主光、补光、顶光不照大板和墙（大板亮度只由洗墙光定，和别的段的 bg.jpg 对齐）
    notb = bpy.data.collections.new("ONCAM_not_board")
    notb.children.link(board_coll)
    notb.children.link(haze_setup(light))
    for cc in notb.collection_children:
        cc.light_linking.link_state = "EXCLUDE"
    for o in (key, fill, top):
        o.light_linking.receiver_collection = notb
    # 反射卡（只给镜面看，不照明、不投影）：金钥匙、电镀件、亮面塑料要有东西可反射，不然朝相机的面全黑
    cards = [refl_card("refl_window", s + d * 2.4, s, (1.8, 1.4), col, 3.0),
             refl_card("refl_front", Vector((0.35, -0.8, 0.05)), s, (3.0, 1.8), col, 1.2),
             refl_card("refl_top", s + Vector((0.1, -0.2, 1.3)), s, (1.6, 0.5), col, 2.0)]
    return dict(key=key, fill=fill, top=top, wash=wash, cards=cards)


def refl_card(name, loc, aim, size, color, strength):
    me = bpy.data.meshes.new(name)
    w, h = size
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    o = link_obj(bpy.data.objects.new(name, me))
    o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(aim)).to_track_quat("Z", "Y").to_euler()   # 正面朝零件
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color[:3], 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m)
    o.visible_camera = o.visible_diffuse = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
    o.visible_glossy = True
    return o


def world_setup(fit):
    w = bpy.context.scene.world
    if w is None or not w.use_nodes:
        w = bpy.data.worlds.new("oncam_w"); w.use_nodes = True
        bpy.context.scene.world = w
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    base = fit.get("world", 0.35)
    # 镜面光线看见的世界亮一些（像一间有白墙的屋子）：金、电镀件朝镜头的面有东西可反射；漫反射和相机还是 calib 定的世界光
    lp = nt.nodes.get("oncam_lp") or nt.nodes.new("ShaderNodeLightPath")
    lp.name = "oncam_lp"
    mp = nt.nodes.get("oncam_map") or nt.nodes.new("ShaderNodeMapRange")
    mp.name = "oncam_map"
    mp.inputs["To Min"].default_value = base
    mp.inputs["To Max"].default_value = max(base, GLOSSY_WORLD)
    nt.links.new(lp.outputs["Is Glossy Ray"], mp.inputs["Value"])
    nt.links.new(mp.outputs["Result"], bg.inputs[1])


def cam_basis():
    return Matrix.Rotation(math.radians(90), 4, "X")


def make_camera():
    cd = bpy.data.cameras.new("oncam_cam")
    cam = link_obj(bpy.data.objects.new("oncam_cam", cd))
    cd.lens = LENS
    cd.sensor_width = 36.0
    cd.sensor_fit = "HORIZONTAL"
    cd.shift_x, cd.shift_y = SHIFT
    cd.clip_start, cd.clip_end = 0.01, 60.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = FSTOP
    cd.dof.aperture_blades = 6                    # 08 文档第七节：叶片 6，接近手机镜头的圆
    cd.dof.focus_distance = BASE_FOCUS
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = cam_basis()
    bpy.context.scene.camera = cam
    return cam


def card_corners():
    P = PERSON
    return [px_to_world(P["x"], P["y"] + P["h"], D_PERSON), px_to_world(P["x"] + P["w"], P["y"] + P["h"], D_PERSON),
            px_to_world(P["x"] + P["w"], P["y"], D_PERSON), px_to_world(P["x"], P["y"], D_PERSON)]


def person_card(cfg):
    """人卡片：素材逐帧图 + 遮罩当贴图的平面，放在 D_PERSON，四角正好落在出片上人所在的框。
    相机、镜面、透射看不见，只投影 + 一点漫反射（T1 试验定的）。"""
    c = card_corners()
    me = bpy.data.meshes.new("oncam_person")
    me.from_pydata(c, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, ab in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = ab
    o = link_obj(bpy.data.objects.new("oncam_person", me))
    m = bpy.data.materials.new("oncam_person"); m.use_nodes = True
    nt = m.node_tree
    pb = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(str(Path(cfg["person"]) / "0000.png"))
    img.source = "SEQUENCE"
    tex.image = img
    iu = tex.image_user
    iu.frame_duration = cfg["n"] - 1              # 段帧 f → 第 f − off 张（0000 起），两头钳住
    iu.frame_start = cfg["off"] + 1
    iu.frame_offset = 0
    iu.use_cyclic = False
    iu.use_auto_refresh = True
    nt.links.new(tex.outputs["Color"], pb.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], pb.inputs["Alpha"])
    pb.inputs["Roughness"].default_value = 0.6
    o.data.materials.append(m)
    o.visible_camera = False
    o.visible_glossy = False
    o.visible_transmission = False
    o.visible_volume_scatter = False
    o.visible_diffuse = True
    o.visible_shadow = True
    return o


def micro(f):
    """以人卡片中心为轴的微动（度）：左右 ±MICRO[0]、上下 ±MICRO[1]，两个正弦叠加，周期 3–9 秒。"""
    yaw = MICRO[0] * (0.7 * math.sin(2 * math.pi * f / (7.4 * FPS)) + 0.3 * math.sin(2 * math.pi * f / (3.3 * FPS) + 1.3))
    pit = MICRO[1] * (0.7 * math.sin(2 * math.pi * f / (8.6 * FPS) + 0.7) + 0.3 * math.sin(2 * math.pi * f / (4.1 * FPS) + 2.1))
    return yaw, pit


def cam_matrix_micro(f):
    P = Vector(px_to_world(*PIVOT_PX, D_PERSON))
    yaw, pit = micro(f)
    R = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pit), 4, "X")
    return Matrix.Translation(P) @ R @ Matrix.Translation(-P) @ cam_basis()


def project(Mcam, shift, p):
    """世界点 → 出片像素（含镜头偏移）。返回 (x, y, 深度)。"""
    q = Mcam.inverted() @ Vector(p)
    z = -q.z
    if z <= 1e-6:
        return (float("nan"), float("nan"), z)
    return (OUT_W / 2 + F_PX * q.x / z - shift[0] * OUT_W, OUT_H / 2 - F_PX * q.y / z + shift[1] * OUT_W, z)


def look_at(eye, target):
    q = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y")
    return Matrix.Translation(eye) @ q.to_matrix().to_4x4()


def interp_mat(A, B, t):
    la, ra, sa = A.decompose()
    lb, rb, sb = B.decompose()
    if ra.dot(rb) < 0:
        rb = -rb
    return Matrix.LocRotScale(la.lerp(lb, t), ra.slerp(rb, t), sa.lerp(sb, t))


def key_matrix(o, f, M):
    loc, rot, sca = M.decompose()
    o.location = loc
    o.scale = sca
    if o.rotation_mode == "QUATERNION":
        prev = Quaternion(o.rotation_quaternion)
        if prev.dot(rot) < 0:
            rot = -rot
        o.rotation_quaternion = rot
        o.keyframe_insert("rotation_quaternion", frame=f)
    else:
        o.rotation_euler = rot.to_euler(o.rotation_mode, o.rotation_euler)
        o.keyframe_insert("rotation_euler", frame=f)
    o.keyframe_insert("location", frame=f)
    o.keyframe_insert("scale", frame=f)


def linear_keys(idb):
    import bl_guide as BG
    BG._linear(idb)


def build_world(cfg, fit, samples=SAMPLES):
    import kit_parts as KP
    gpu_wait()
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    sc = bpy.context.scene
    setup_render(sc, cfg["nf"], samples)
    board, bcoll = board_setup()
    world_setup(fit)
    cam = make_camera()
    card = person_card(cfg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    subject = px_to_world(1600, 480, 1.42)
    rig = light_rig(light, fit, subject, bcoll)
    K = KP.Kit()
    return dict(sc=sc, cam=cam, card=card, board=board, bcoll=bcoll, rig=rig, light=light, fit=fit, kit=K, cfg=cfg)


def default_fit(light):
    return dict(az_deg=min(60.0, max(30.0, light["az_deg"])), el_deg=15.0, key_w=900.0, fill_w=260.0, wash_w=900.0 * (BOARD_D / 3.6) ** 2, world=0.35)


def load_fit(cfg, light):
    p = cfg["work"] / "light_fit.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default_fit(light)


# ---------------------------------------------------------------- T1 + T3：卡片投影试验、灰球比光
def _render_to(path, pct=50):
    sc = bpy.context.scene
    sc.render.resolution_percentage = pct
    sc.render.filepath = str(path)
    gpu_wait()
    bpy.ops.render.render(write_still=True)
    return path


def _load(path):
    """Blender 里读 PNG/JPG（Blender 自带的 Python 没有 PIL）：8 位图的 pixels 就是显示值 /255，上下翻正。"""
    import numpy as np
    im = bpy.data.images.load(str(path), check_existing=False)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1]
    bpy.data.images.remove(im)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones_like(a[..., :1])], -1)
    return a


def _lin(x):
    import numpy as np
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def ball_stats(a, c, r_m=0.07, pct=0.5, Mcam=None, shift=SHIFT):
    import numpy as np
    x, y, z = project(Mcam or cam_basis(), shift, c)
    r = r_m * F_PX / z * pct
    cx, cy = x * pct, y * pct
    H, Wd = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:Wd]
    disk = np.hypot(xx - cx, yy - cy) < 0.85 * r
    Y = _lum(_lin(a[..., :3]))
    left, right = disk & (xx < cx), disk & (xx > cx)
    hot = disk & (Y >= np.percentile(Y[disk], 95))
    return dict(lit_p90=float(np.percentile(Y[left], 90)), left=float(Y[left].mean()), right=float(Y[right].mean()),
                ratio=float(Y[left].mean() / max(1e-5, Y[right].mean())),
                hot_dx=float((xx[hot].mean() - cx) / r), hot_dy=float((yy[hot].mean() - cy) / r),
                lit_p90_srgb=float(np.percentile(_lum(a[..., :3])[left], 90)), r_px=float(r))


def calib(seg):
    """T3：零件位置放灰球（18%）、白球（80%，对应白 T 恤）、镜面球，逐轮调主光/补光/洗墙光：
    白球亮侧 90 分位 ≈ T 恤亮处；白球左右亮度比 ≈ 脸的主辅光比；大板亮度中位数 ≈ 别的段用的 bg.jpg。差 15% 以内算过。
    T1：同一帧渲 无卡片 / 卡片只投影 / 卡片 Holdout 三张，量人对大板和球的影子、Holdout 放回人以后的半透明边。"""
    import numpy as np
    cfg = seg_cfg(seg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    fit = default_fit(light)
    W = build_world(cfg, fit, samples=48)
    sc = W["sc"]
    out = cfg["work"] / "calib"
    out.mkdir(parents=True, exist_ok=True)
    f_cal = 150
    sc.frame_set(f_cal)
    balls = {}
    for name, col, metal, rough, u in (("grey", 0.18, 0, 1.0, 1450), ("white", 0.80, 0, 1.0, 1610), ("chrome", 0.95, 1, 0.0, 1770)):
        m = bpy.data.materials.new("ball_" + name); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (col, col, col, 1)
        p.inputs["Metallic"].default_value = metal
        p.inputs["Roughness"].default_value = rough
        if not metal:
            p.inputs["Specular IOR Level"].default_value = 0.0
        c = px_to_world(u, 470, 1.42)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=c, segments=64, ring_count=32)
        o = bpy.context.object; o.name = "ball_" + name
        o.visible_shadow = False                  # 主光从左边平着来，左边的球会挡右边的球（T3 第二版白球比 < 1）
        bpy.ops.object.shade_smooth(); o.data.materials.append(m)
        balls[name] = (o, c)
    bg_ref = _load(Path(cfg["person"]).parent / "bg.jpg")[..., :3]
    t_board = float(np.median(_lum(_lin(bg_ref[100:1000, 1250:1900])))) * BG_DIM
    t_white = light["shirt_lin_p90"] * 0.9          # 白球 80% 对白 T 恤（约 90%）
    t_ratio = light["key_fill_ratio_mean"]
    hist = []
    W["card"].hide_render = True
    rig = W["rig"]
    for rnd in range(8):
        a = _load(_render_to(out / f"t3_round{rnd}.png", 50))
        st = {k: ball_stats(a, c) for k, (o, c) in balls.items()}
        Yb = _lum(_lin(a[..., :3]))[50:500, 625:950]
        m_board = float(np.median(Yb))
        row = dict(round=rnd, key_w=round(rig["key"].data.energy, 1), fill_w=round(rig["fill"].data.energy, 1),
                   wash_w=round(rig["wash"].data.energy, 1), balls=st,
                   white_lit_p90=st["white"]["lit_p90"], target_white=t_white, ratio=st["white"]["ratio"], target_ratio=t_ratio,
                   board_med=m_board, target_board_med=t_board)
        e_w = abs(st["white"]["lit_p90"] / t_white - 1)
        e_r = abs(st["white"]["ratio"] / t_ratio - 1)
        e_b = abs(m_board / t_board - 1)
        row.update(err_white=round(e_w, 3), err_ratio=round(e_r, 3), err_board=round(e_b, 3))
        hist.append(row)
        print("ONCAM calib", json.dumps({k: v for k, v in row.items() if k != "balls"}), flush=True)
        if max(e_w, e_r, e_b) < 0.08 or rnd == 7:
            break
        g = (t_white / st["white"]["lit_p90"])
        if rig["fill"].data.energy < 0.08 * rig["key"].data.energy and st["white"]["ratio"] < t_ratio * 0.92:
            # 补光已经关到底，比还不够：剩下的是世界光，压世界光
            fit["world"] = round(max(0.12, fit.get("world", 0.35) * 0.55), 4)
            world_setup(fit)
            rig["fill"].data.energy = max(rig["fill"].data.energy, 0.05 * rig["key"].data.energy)
        rig["key"].data.energy *= g ** 0.9
        rig["fill"].data.energy *= (st["white"]["ratio"] / t_ratio) ** 1.3 * g ** 0.9
        rig["top"].data.energy = rig["key"].data.energy * 0.12
        rig["wash"].data.energy *= (t_board / max(1e-4, m_board))
    fit.update(key_w=rig["key"].data.energy, fill_w=rig["fill"].data.energy, wash_w=rig["wash"].data.energy, top_w=rig["top"].data.energy)
    # T1：卡片三种做法，同一帧
    t1 = {}
    W["card"].hide_render = True
    a0 = _load(_render_to(out / "t1_nocard.png", 50))
    W["card"].hide_render = False
    a1 = _load(_render_to(out / "t1_shadow_only.png", 50))
    W["card"].visible_camera = True
    W["card"].is_holdout = True
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    a2 = _load(_render_to(out / "t1_holdout.png", 50))
    sc.render.film_transparent = False
    sc.render.image_settings.color_mode = "RGB"
    W["card"].is_holdout = False
    W["card"].visible_camera = False
    Y0, Y1 = _lum(_lin(a0[..., :3])), _lum(_lin(a1[..., :3]))
    right = (slice(0, 540), slice(620, 960))
    t1["board_right_dEV"] = float(np.log2(Y0[right].mean() / max(1e-6, Y1[right].mean())))
    t1["board_right_max_drop"] = float(np.percentile((Y0 - Y1)[right], 99.5) / max(1e-6, np.median(Y0[right])))
    for k_, (o, c) in balls.items():
        s0, s1 = ball_stats(a0, c), ball_stats(a1, c)
        t1[f"ball_{k_}_dEV"] = float(np.log2((s0["left"] + s0["right"]) / max(1e-6, s1["left"] + s1["right"])))
    al = a2[..., 3]
    pfull = _load(Path(cfg["person"]) / f"{person_k(cfg, f_cal):04d}.png")[..., 3]
    pp = pfull[:PERSON["h"] // 2 * 2, :PERSON["w"] // 2 * 2].reshape(PERSON["h"] // 2, 2, PERSON["w"] // 2, 2).mean((1, 3))
    pa = np.zeros_like(al)
    x0, y0 = PERSON["x"] // 2, PERSON["y"] // 2
    pa[y0:y0 + pp.shape[0], 0:x0 + pp.shape[1]] = pp[:, -x0:]
    t1["holdout_hole_px"] = int((al < 0.5).sum())
    t1["holdout_see_through_px"] = int(((pa + (1 - pa) * al) < 0.97).sum())
    t1["shadow_only_see_through_px"] = 0
    t1["note"] = ("只投影：人对大板、对球的影子见 dEV（正值 = 变暗）；最终画面人由合成整个放回最前，没有半透明边。"
                  "Holdout：卡片挖的洞和人物遮罩边对不齐，放回人以后残留半透明像素（see_through），所以不用 Holdout 出像。")
    fit["t1"] = t1
    fit["t3"] = hist
    fit["f_cal"] = f_cal
    (cfg["work"] / "light_fit.json").write_text(json.dumps(fit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM t1", json.dumps(t1, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- 转场
def fg_wipe(K, nf_wipe=17, depth=0.24):
    """T5 焦点擦除（段首）：近处两根白色料杆（带一个浇口）从画面正中往左扫出，焦外完全虚化。
    上一段结尾接同一组料杆从右边扫进来（速度 0.021 m/帧，深 0.24 m，倾 14°），段帧 0 时料杆在画面正中。"""
    coll = bpy.data.collections.new("FG")
    bpy.context.scene.collection.children.link(coll)
    root = link_obj(bpy.data.objects.new("FG_root", None), coll)
    objs = [root]

    def adopt(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        o.parent = root
        objs.append(o)
    # 近处料杆背光、离灯远，用原白料会是一片灰褐；复制一份加一点暖白自发光，像屋里亮处的焦外白杆
    mw = K.white.copy(); mw.name = "FG_white"
    pb = next(n for n in mw.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    pb.inputs["Emission Color"].default_value = (1.0, 0.93, 0.84, 1)
    pb.inputs["Emission Strength"].default_value = 1.3
    for i, dx in enumerate((-0.07, 0.07)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.048, depth=1.6, vertices=48, location=(dx, 0, 0))
        o = bpy.context.object; o.name = f"FG_bar{i}"
        bpy.ops.object.shade_smooth(); o.data.materials.append(mw)
        adopt(o)
    bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0.012, depth=0.12, vertices=32, location=(0, 0, 0.05), rotation=(0, math.radians(90), 0))
    g = bpy.context.object; g.name = "FG_gate"
    bpy.ops.object.shade_smooth(); g.data.materials.append(mw)
    adopt(g)
    root.rotation_euler = (0, math.radians(14), 0)
    xc = px_to_world(OUT_W / 2, OUT_H / 2, depth)[0]
    zc = px_to_world(OUT_W / 2, OUT_H / 2, depth)[2]
    for f in range(0, nf_wipe + 2):
        root.location = (xc - 0.021 * f, depth, zc)
        root.keyframe_insert("location", frame=f)
    linear_keys(root)
    for o in objs:
        o["fg"] = 1
    return dict(last=nf_wipe + 1, depth=depth, speed_m_per_f=0.021, tilt_deg=14)


# ---------------------------------------------------------------- 3-01 的 recipe：销子锁 H06 + 钥匙 H02
SL = 19.35                        # 零件放大倍数（锁宽 20 mm → 0.4 m，在 1.4 m 处约 360 px 宽、高约 450 px，F1 ≥ 380）
KEY_RIM_W = 30.0                  # 只照钥匙的小面光（W）
KEY_YAW = -65.0                   # 钥匙亮出时侧转的角度（度）：正对相机只看见圆柄，侧过来才看得出是钥匙
PIN_DROP = 0.5                    # 没钥匙时下销落下的量（mm）


def _rot(yaw, tilt):
    return Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def _geom_world(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    V, F = [], []
    for ob in objs:
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
        n = len(V)
        V += [eo.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        F += [tuple(n + i for i in t.vertices) for t in me.loop_triangles]
        eo.to_mesh_clear()
    return V, F


def _tree(objs):
    from mathutils.bvhtree import BVHTree
    V, F = _geom_world(objs)
    return BVHTree.FromPolygons(V, F, all_triangles=True) if F else None


def _visible_meshes(root, ignore_anim=False):
    """子树里真正出像的网格/曲线（布尔刀具不算）。ignore_anim：不看当前帧的 hide_render（钥匙的显隐是动画）。"""
    cutters = {m.object for o in bpy.data.objects for m in getattr(o, "modifiers", []) if m.type == "BOOLEAN" and m.object}
    return [o for o in [root] + list(root.children_recursive)
            if o.type in ("MESH", "CURVE") and o not in cutters and (ignore_anim or not o.hide_render)]


def key_rim_keys(kl, f_on, f_off):
    """钥匙小面光只在钥匙亮出到插进去这段亮：插进去以后关掉（推进时镜头贴近钥匙柄，不关会烧成一团白，实测 380–382 帧）。"""
    w = kl.data.energy
    for f, e in ((f_on - 12, 0.0), (f_on, w), (f_off, w), (f_off + 6, 0.0)):
        kl.data.energy = e
        kl.data.keyframe_insert("energy", frame=f)
    kl.data.energy = w


def recipe_lock_key(W):
    """3-01 "Okay. To get this, picture a lock and a key."（D，384 帧）。事件 id 沿用 events/3-01.json（二维版同一张表），三维里的意思：
      dot   Okay   挂在料杆框里的锁点一下头（落在词上）
      dot2  this   锁连框转向镜头一点
      frame picture A1 浇口弹下：预颤 178–184（bl_guide），184 弹出并转正（16 帧 easeOutBack + 回弹）；焦点点名 158→176、轮廓光
      lock  lock   锁转过来露出剖开的四分之一，一排弹子销（216→230 落位，过冲回弹）
      key   a      钥匙从 D 抬起的手边亮出（A7：308→332），手在钥匙前（F3）
      slide key    钥匙对准锁孔滑进去，五根销被齿顶到同一条线（340→368），锁芯带钥匙转 32°，锁梁弹起（370→384）
    段尾 T1：362 起镜头推进剖口，穿进销子之间（接 3-02）。"""
    import kit_deep as D
    import kit_deep_r3 as M3
    import kit_parts as KP
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}
    # 板上第 3 区那把挂锁就是飞到人旁边的这一把：板上的藏起来
    cell = bpy.data.objects.get("z3_c4_r2")
    if cell is not None:
        for m in [KP.part_of(cell)] + list(KP.part_of(cell).children_recursive):
            m.hide_render = True
    lock = M3.h06_pin_lock(K)
    D.rest(lock)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([lock])
    c0 = (lo + hi) / 2                                    # 锁自己的坐标（米，未放大）
    j = D.rig(lock)
    lock.rotation_mode = "XYZ"
    # 挂件框：锁的 XZ 平面（y = 3 mm，浇口所在）上一圈蓝色料杆，两个浇口夹住锁的两侧
    hang = link_obj(bpy.data.objects.new("hang_cell", None))
    hang.rotation_mode = "XYZ"
    hx = max(abs(lo.x), abs(hi.x)) / MM + 3.5
    z0, z1 = lo.z / MM - 3.0, hi.z / MM + 3.0
    zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
    KP.tube_w("hang_cell_loop", [(x, 3.0, z) for x, z in KP.rrect(0, zc, hx, hz, 5.0)], KP.R_LOOP, K.blue, hang, cyclic=True)
    for i, (gx, gy, d, gz) in enumerate(json.loads(lock["gates"])):
        KP.gate_geo(f"hang_cell_g{i}", ((hx if gx > 0 else -hx) * MM, gy * MM, gz * MM), (gx * MM, gy * MM, gz * MM), K.blue, hang)
    gates = [o for o in hang.children if o.name.startswith("hang_cell_g")]

    def pose_at(yaw, tilt, u, v, d):
        R = _rot(yaw, tilt)
        return Vector(px_to_world(u, v, d)), R.to_quaternion()

    def mat_center(center, q):
        R = q.to_matrix().to_4x4()
        return Matrix.Translation(center - R @ (c0 * SL)) @ R @ Matrix.Diagonal((SL, SL, SL, 1))

    f_ok, f_this = E["dot"]["f_land"], E["dot2"]["f_land"]
    f_pop = E["frame"]["f_land"]
    f_r0, f_r1 = E["lock"]["f_start"], E["lock"]["f_land"]
    f_k0, f_k1 = E["key"]["f_start"], E["key"]["f_land"]
    f_s = E["slide"]["f_land"]
    HANG = pose_at(140, 8, 1555, 455, 1.57)
    PICK = pose_at(65, 10, 1565, 470, 1.42)
    SHOW = pose_at(-50, 14, 1575, 480, 1.40)

    def hang_state(f):
        c, q = HANG
        yaw = 2.0 * math.sin(2 * math.pi * f / 250)                       # 待机微动
        tilt = 1.0 * math.sin(2 * math.pi * f / 310 + 1)
        # Okay：点头（31→39 落下、之后弹簧回）
        e = E["dot"]
        tilt += 3.0 * (ease_out_cubic((f - e["f_start"]) / max(1, f_ok - e["f_start"])) if f <= f_ok else spring((f - f_ok) / FPS))
        # this：连框转向镜头 8°（98→118，之后停住）
        e = E["dot2"]
        yaw -= 8.0 * ease_inout_cubic((f - e["f_start"]) / max(1, f_this - e["f_start"]))
        dq = (Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(yaw), 4, "Z")).to_quaternion()
        return Vector(c), dq @ q

    def float_off(f, start):
        b = smooth((f - start) / 30)
        return Vector((0, 0, 0.004 * math.sin(2 * math.pi * f / 220) * b)), 1.0 * math.sin(2 * math.pi * f / 300) * b

    c_h, q_h = hang_state(f_pop)
    pop_dir = (q_h.to_matrix() @ Vector((0, 1, 0)))
    pop_dir = pop_dir.normalized()                       # 沿料杆框的法线出框（带上抬会撞框上沿）
    y_len = (hi.y - lo.y) * SL                           # 锁在出框方向上的厚度（米）
    P1 = c_h + pop_dir * 0.16 * SL / 16.0             # 弹出距离跟零件大小走，先整个出框再转

    def lock_state(f):
        if f <= f_pop:
            return hang_state(f)
        if f < f_r0:
            p = pop_curve(f, f_pop, 16, 12)
            pc = min(1.0, p)
            c = Vector(bezier(c_h, P1, PICK[0], pc))
            if p > 1:
                c = c + (Vector(PICK[0]) - Vector(bezier(c_h, P1, PICK[0], 0.95))) / 0.05 * (p - 1)
            dq = q_h.rotation_difference(PICK[1])
            ax, ang = dq.to_axis_angle()
            r = p if p > 1 else smooth((p - 0.45) / 0.55)    # 先平着弹出框（不转），出了框再转正，免得锁体扫过料杆（穿模检查 186 帧）
            q = Quaternion(ax, ang * r) @ q_h
            fo, fy = float_off(f, f_pop + 20)
            return c + fo, Quaternion((0, 0, 1), math.radians(fy)) @ q
        p = pop_curve(f, f_r0, f_r1 - f_r0, 14)
        c = Vector(PICK[0]).lerp(Vector(SHOW[0]), min(1, p))
        dq = PICK[1].rotation_difference(SHOW[1])
        ax, ang = dq.to_axis_angle()
        q = Quaternion(ax, ang * p) @ PICK[1]
        fo, fy = float_off(f, f_pop + 20)
        return c + fo, Quaternion((0, 0, 1), math.radians(fy)) @ q

    # 11-20 验收：出镜段零件不带料框。框只在 Okay 那一下从浇口"咔"地断开：往后弹开锁的厚度、再按重力掉出画面，之后藏掉
    f_snap = f_ok
    f_gone = f_snap + 40

    def cell_state(f):
        c, q = hang_state(min(f, f_snap))
        if f <= f_snap:
            return c, q
        t = (f - f_snap) / FPS
        kick = -pop_dir * (y_len + 0.05) * ease_out_cubic((f - f_snap) / 8)
        fall = Vector((0.15 * t, 0.2 * t, -4.9 * t * t))            # 重力 9.8 m/s²：0.6 s 掉 1.8 m，出画
        tumble = Quaternion(pop_dir.cross(Vector((0, 0, 1))).normalized(), math.radians(-70 * t * t))
        return c + kick + fall, tumble @ q

    LM = [mat_center(*lock_state(f)) for f in range(nf)]
    for f in range(nf):
        key_matrix(lock, f, LM[f])
        key_matrix(hang, f, mat_center(*cell_state(min(f, f_gone))))
    for o in [hang] + list(hang.children_recursive):
        for fk, hid in ((f_gone - 1, False), (f_gone, True)):
            o.hide_render = hid
            o.keyframe_insert("hide_render", frame=fk)
    # 钥匙：挂在锁下面（父子），锁芯转时跟着转
    key = D.h02_key(K, which="048", scale=1.3)
    key.parent = lock
    key.matrix_parent_inverse = Matrix.Identity(4)
    key.rotation_mode = "QUATERNION"
    Wv, Uv, Vv = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
    origin = Vector((0, -1.5, -0.55))
    rot3 = Matrix((-Wv, -Uv, -Vv)).transposed()
    off = float(key["insertion_offset_u_mm"])
    Kin = Matrix.Translation(((origin + off * Uv) - rot3 @ Vector((6.5 * 1.3, 0, 0))) * MM) @ rot3.to_4x4() @ Matrix.Diagonal((1.3, 1.3, 1.3, 1))
    pivot = origin * MM

    def Rplug(deg):
        return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, Wv) @ Matrix.Translation(-pivot)

    def Kt(w, du=0.0, dv=0.0, s=1.0):
        return Matrix.Translation((w * Wv + du * Uv + dv * Vv) * MM) @ Kin @ Matrix.Diagonal((s, s, s, 1))

    tip_local = Vector((6.5 * MM, 0, 0))
    # 手边的位置：钥匙尖落在出片 (1330, 715)，在锁下方、D 的右手右边（11-20 验收：钥匙不要被手指盖住）。
    # 离锁 13 mm（放大后 0.28 m）：再往相机凑就太大、出画、离焦外太远；上下左右用 du、dv 两个方向解
    tgt = (1330.0, 715.0)
    Mc = cam_matrix_micro(f_k1)
    w_hand = 13.0
    du_, dv_ = -12.0, 0.0
    for _ in range(30):
        def scr(du, dv):
            p = LM[f_k1] @ (Kt(w_hand, du, dv) @ tip_local)
            x, y, _z = project(Mc, SHIFT, p)
            return x, y
        x0, y0 = scr(du_, dv_)
        xa, ya = scr(du_ + 0.1, dv_)
        xb, yb = scr(du_, dv_ + 0.1)
        J = Matrix(((xa - x0, xb - x0), (ya - y0, yb - y0))) * 10
        try:
            d = J.inverted() @ Vector((tgt[0] - x0, tgt[1] - y0))
        except ValueError:
            break
        du_, dv_ = du_ + d.x, dv_ + d.y
    du_hand, dv_hand = du_, dv_
    f_a0, f_a1 = f_s, f_s + 10                            # 对准锁孔
    f_i0, f_i1 = f_a1, f_s + 28                           # 滑进去
    f_t0 = f_i1 + 2                                       # 锁芯转
    f_sh = f_t0 + 4                                       # 锁梁弹起

    def key_yaw(f):
        if f < f_a0:
            return KEY_YAW
        if f < f_a1:
            return KEY_YAW * (1 - ease_inout_cubic((f - f_a0) / (f_a1 - f_a0)))
        return 0.0

    def key_dv(f):
        if f < f_a0:
            return dv_hand
        if f < f_a1:
            return dv_hand * (1 - ease_inout_cubic((f - f_a0) / (f_a1 - f_a0)))
        return 0.0

    def key_state(f):
        """(w, du, scale, 锁芯角度, 可见)"""
        if f < f_k0:
            return 30.0, du_hand, 0.3, 0.0, False
        if f < f_s:
            e = (f - f_k0) / max(1, f_k1 - f_k0)
            return w_hand + 6.0 * (1 - ease_out_cubic(e)), du_hand + 0.25 * math.sin(2 * math.pi * f / 90), 0.3 + 0.7 * ease_out_back(e), 0.0, True
        if f < f_a1:
            e = ease_inout_cubic((f - f_a0) / (f_a1 - f_a0))
            return w_hand + (7.5 - w_hand) * e, du_hand * (1 - e), 1.0, 0.0, True
        if f < f_i1:
            e = ease_out_cubic((f - f_i0) / (f_i1 - f_i0))
            return 7.5 * (1 - e), 0.0, 1.0, 0.0, True
        return 0.0, 0.0, 1.0, 32.0 * pop_curve(f, f_t0, 10, 10), True

    # 下销跟着钥匙齿走：钥匙齿面（锁坐标 u）由 h02 的齿形算，销的落脚取销底面 ±0.45 mm 内的最高点
    prof = list(key["tooth_profile_modelled"])
    chain = [(6.5, -1.3)]
    for i, h in enumerate(prof):
        c = 6.0 - i
        chain += [(c + 0.28, -1.3 + h), (c - 0.28, -1.3 + h)]
    chain += [(1.5, -1.3)]
    chain = sorted(chain)

    def surf(x):
        if x > 6.5:
            return off + 1.3 * 1.3 - (x - 6.5) / 0.5 * 3.0 if x < 7.0 else -99
        if x < 1.5:
            return -99
        for (xa, ya), (xb, yb) in zip(chain, chain[1:]):
            if xa <= x <= xb:
                t = 0 if xb == xa else (x - xa) / (xb - xa)
                return off + (-(ya + (yb - ya) * t)) * 1.3
        return -99

    def foot(i, w):
        a = (0.5 + i) * 1.3
        x = 6.5 - (a - w) / 1.3
        return max(surf(x + dx) for dx in (-0.45, -0.3, -0.15, 0, 0.15, 0.3, 0.45))

    rest_u = [foot(i, 0.0) for i in range(5)]
    lifts_max = 0.0
    hide_prev = None
    for f in range(nf):
        w, du, s, deg, vis = key_state(f)
        Mk = Rplug(deg) @ Kt(w, du, key_dv(f), s)
        tip_l = Mk @ tip_local                            # 亮出时钥匙侧过来（齿形朝镜头），对准锁孔时绕钥匙尖转正
        Mk = Matrix.Translation(tip_l) @ Matrix.Rotation(math.radians(key_yaw(f)), 4, Uv) @ Matrix.Translation(-tip_l) @ Mk
        key.matrix_basis = Mk
        key.keyframe_insert("location", frame=f)
        key.keyframe_insert("rotation_quaternion", frame=f)
        key.keyframe_insert("scale", frame=f)
        if vis != hide_prev:
            for o in [key] + list(key.children_recursive):
                o.hide_render = not vis
                o.keyframe_insert("hide_render", frame=f)
            hide_prev = vis
        inside = du == 0.0 and w <= 7.0
        for i in range(5):
            lift = max(-PIN_DROP, foot(i, w) - rest_u[i]) if inside else -PIN_DROP
            lifts_max = max(lifts_max, lift)
            j[f"pin_{i}"].location.z = lift * MM
            j[f"pin_{i}"].keyframe_insert("location", index=2, frame=f)
        j["plug"].rotation_euler.x = math.radians(deg)
        j["plug"].keyframe_insert("rotation_euler", index=0, frame=f)
        j["shackle"].location.z = 3.6 * ease_out_back((f - f_sh) / 10) * MM if f >= f_sh else 0.0
        j["shackle"].keyframe_insert("location", index=2, frame=f)
    for o in [lock, hang, key] + [j[f"pin_{i}"] for i in range(5)] + [j["plug"], j["shackle"]]:
        linear_keys(o)
    # 预颤（bl_guide，A1 的预备）：零件往弹出方向绷 4 mm（屏上 ≤ 6 px），浇口拉细，框颤两下
    import bl_guide as BG
    sc.frame_set(f_pop - 6)
    rot = BG.tick_rot_cap(W["cam"], sc, lock, cam_matrix_micro(f_pop).translation, 4.0)
    tick = BG.guide_tick(lock, [], None, f_pop, amp_mm=4.0, rot_deg=rot, dir=pop_dir)   # 框已在 Okay 断掉，只剩锁本体预颤
    # 浇口在锁体表面断开：断的那一帧锥头缩回 40%（粗端连料杆不动），断口留在框上，不再插在锁体侧面里（穿模检查 184–186 帧）
    for g in gates:
        L = g.dimensions.z / max(1e-9, g.scale.z)
        ax = g.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        for fk, sz in ((f_snap, 1.0), (f_snap + 1, 0.6)):
            g.delta_scale = (1.0, 1.0, sz)
            g.delta_location = -ax * L * (1 - sz) / 2
            g.keyframe_insert("delta_scale", frame=fk)
            g.keyframe_insert("delta_location", frame=fk)
    tick["rot_deg"] = rot

    def lock_center(f):
        return LM[max(0, min(nf - 1, int(f)))] @ c0

    # 镜头推进的目标：剖口里五根销的中间、分界线上，从 +X（剖口朝外）略上方看进去
    Pw_local = Vector((1.8, -4.75, 2.6)) * MM
    dir_local = Vector((1.0, -0.35, 0.5)).normalized()
    Mend = LM[nf - 1]
    target = Mend @ Pw_local
    eye = Mend @ (Pw_local + dir_local * 7.0 * MM)
    hero_box = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]

    def bbox_pts(f):
        return [LM[f] @ p for p in hero_box]

    # 焦点借给钥匙：钥匙从手边亮出到对准锁孔（离相机近 0.5 m，不拉焦就是一团虚的暗影）
    key_pts = {}
    for f in range(f_k0 - 8, f_a1 + 12):
        bpy.context.scene.frame_set(f)
        key_pts[f] = key.matrix_world.translation.copy()
    focus2 = [(f_k0 - 8, f_a1 + 11, lambda f: key_pts[f])]
    # 钥匙侧着亮出时，正对镜头那面要有东西可反射（金色才亮），一张只给镜面看的卡放在相机左上方对着钥匙
    kp = key_pts[f_k1]
    refl_card("refl_key", -kp.normalized() * 0.35 + Vector((-0.15, 0, 0.12)), kp, (1.6, 1.1), kelvin_rgb(W["light"]["kelvin"]), 3.0)   # 相机身后、钥匙—相机连线上
    # 11-20 验收：金钥匙在 340 帧读成深褐。加一盏只照钥匙的小面光（灯光链接），从右上前方打，金色读成亮金
    kcol = bpy.data.collections.new("ONCAM_key_lit")
    sc.collection.children.link(kcol)
    for o in [key] + list(key.children_recursive):
        if o.type in ("MESH", "CURVE"):
            kcol.objects.link(o)
    kl = make_light("key_rim", "AREA", kp + Vector((0.32, -0.38, 0.42)), kp, 0.35, KEY_RIM_W, kelvin_rgb(4300))
    kl.light_linking.receiver_collection = kcol
    key_rim_keys(kl, f_k0, f_i1)


    def checks():
        """穿模：弹出时锁和框、浇口；钥匙进锁时钥匙和锁体（外壳、套筒、轴承、口环、螺丝）、锁芯；钥匙和下销只许贴着。"""
        out = {}
        cell_objs = _visible_meshes(hang)
        kset = set([key] + list(key.children_recursive))
        lock_objs = [o for o in _visible_meshes(lock) if o not in kset]
        rotor = set(_visible_meshes(j["plug"]))
        pins_low = [o for o in rotor if "lower_pin" in o.name]
        core = [o for o in rotor if o not in pins_low]
        moving = set(rotor) | set(o for i in range(5) for o in _visible_meshes(j[f"pin_{i}"])) | set(_visible_meshes(j["shackle"]))
        statics = [o for o in lock_objs if o not in moving]
        hits = []
        for f in range(f_snap + 1, f_gone):
            sc.frame_set(f)
            a, b = _tree(lock_objs), _tree(cell_objs)
            if a and b and a.overlap(b):
                hits.append(f)
        out["lock_vs_cell_frames"] = hits
        key_objs = _visible_meshes(key, ignore_anim=True)
        hk, hc, hp = [], [], []
        for f in range(f_k1, nf):
            sc.frame_set(f)
            kt = _tree(key_objs)
            if kt.overlap(_tree(statics)):
                hk.append(f)
            if kt.overlap(_tree(core)):
                hc.append(f)
            n = len(kt.overlap(_tree(pins_low)))
            if n:
                hp.append([f, n])
        out["key_vs_lockbody_frames"] = hk
        out["key_vs_core_frames"] = hc
        out["key_vs_lowerpins_touch"] = hp
        return out

    return dict(targets={"card": lock_center}, rim={"card": [lock]}, focus2=focus2, hero=lock, bbox=bbox_pts, key=key,
                push=dict(t0=E["slide"]["f_land"] + 22, target=target, eye=eye),
                lock_c0=c0, checks=checks,
                info=dict(SL=SL, pin_drop=PIN_DROP, lifts_max_mm=round(lifts_max, 3), tick=tick, w_hand=round(w_hand, 2), du_hand=round(du_hand, 2), dv_hand=round(dv_hand, 2),
                          frames=dict(okay=f_ok, this=f_this, pop=f_pop, reveal=[f_r0, f_r1], key=[f_k0, f_k1], approach=[f_a0, f_a1],
                                      insert=[f_i0, f_i1], turn=f_t0, shackle=f_sh),
                          poses=dict(hang=[140, 8, 1555, 455, 1.57], pick=[65, 10, 1565, 470, 1.42], show=[-50, 14, 1575, 480, 1.40])))


RECIPES = {"lock_key": recipe_lock_key}


# ---------------------------------------------------------------- 搭整段
def build(seg, samples=SAMPLES):
    import bl_guide as BG
    cfg = seg_cfg(seg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    fit = load_fit(cfg, light)
    W = build_world(cfg, fit, samples)
    sc, cam, nf = W["sc"], W["cam"], cfg["nf"]
    plan = BG.plan_from_keys(cfg["K"])
    R = RECIPES[cfg["recipe"]](W)
    fgw = fg_wipe(W["kit"]) if cfg.get("head") == "T5" else None
    # 镜头：以人卡片为轴的微动；段尾 T1 推进（位置 easeInCubic 加速穿进去，朝向 slerp，镜头偏移收回 0）
    t0 = R["push"]["t0"] if cfg.get("tail") == "T1" else nf
    CM, SH = [], []
    Mend = look_at(R["push"]["eye"], R["push"]["target"]) if t0 < nf else None
    for f in range(nf):
        M = cam_matrix_micro(f)
        sh = SHIFT
        if f >= t0:
            u = (f - t0) / max(1, nf - 1 - t0)
            M = interp_mat(cam_matrix_micro(t0), Mend, ease_in_cubic(u) * 0.985 + 0.015 * u)
            k = smooth(u * 1.4)
            sh = (SHIFT[0] * (1 - k), SHIFT[1] * (1 - k))
        CM.append(M); SH.append(sh)
        key_matrix(cam, f, M)
        cam.data.shift_x, cam.data.shift_y = sh
        cam.data.keyframe_insert("shift_x", frame=f)
        cam.data.keyframe_insert("shift_y", frame=f)
    linear_keys(cam); linear_keys(cam.data)
    # 焦点：没点名时在 BASE_FOCUS，点名时跟零件（bl_guide.focus_track），推进时跟推进目标
    base = lambda f: tuple(CM[f] @ Vector((0, 0, -BASE_FOCUS)))   # noqa: E731
    fp = BG.focus_track(plan, R["targets"], nf, base=base)
    FD = []
    for f in range(nf):
        loc = CM[f].translation
        fwd = (CM[f].to_3x3() @ Vector((0, 0, -1))).normalized()
        p = fp[f] if fp[f] is not None else Vector(base(f))
        dist = (p - loc).dot(fwd)
        for fa, fb, get in R.get("focus2", []):            # 焦点临时借给别的零件，两头 10 帧过渡
            if fa <= f <= fb:
                u = smooth((f - fa) / 10) * smooth((fb - f) / 10)
                dist = dist * (1 - u) + (Vector(get(f)) - loc).dot(fwd) * u
        if f >= t0:
            u = smooth((f - t0) / 8)
            dist = dist * (1 - u) + (Vector(R["push"]["target"]) - loc).dot(fwd) * u
        cam.data.dof.focus_distance = max(0.02, dist)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        FD.append(cam.data.dof.focus_distance)
    linear_keys(cam.data)
    # 轮廓光：放在弹出落位附近，主光 15% 起，rimcal 再标到 +0.18 EV
    land = plan[0]["land"] if plan else 0
    sc.frame_set(min(nf - 1, land + 16))
    rims = BG.guide_rim(plan, R["rim"], cam, W["rig"]["key"])
    # 检查数
    chk = dict(seg=seg, recipe=cfg["recipe"], info=R["info"], plan=plan, fstop=FSTOP, lens=round(LENS, 3), shift=SHIFT, f_px=F_PX,
               d_person=D_PERSON, board=dict(S=BOARD_S, D=BOARD_D), micro_deg=MICRO, push_t0=t0, fg=fgw, fit=fit,
               rim={k: dict(name=v.name, peak_w=v["peak_w"]) for k, v in rims.items()})

    def coc(S, D_):
        fl = LENS * MM
        c = fl * fl / (FSTOP * (S - fl)) * abs(D_ - S) / D_
        return c / (36 * MM) * OUT_W
    for f in sorted(set([20, 150, 176, 200, 240, 330, 360])):
        fwd = (CM[f].to_3x3() @ Vector((0, 0, -1))).normalized()
        dl = (R["targets"]["card"](f) - CM[f].translation).dot(fwd)
        chk.setdefault("coc_px", {})[f] = dict(focus=round(FD[f], 3), lock=round(coc(FD[f], dl), 2), board=round(coc(FD[f], BOARD_D), 2))
    chk["clip"] = R["checks"]()
    # 每帧导出：人卡片四角（5 个子帧，快门 0.5）、主零件包围框、钥匙框（给合成和 check 用）
    corners = card_corners()
    frames = []
    for f in range(nf):
        subs = []
        for s in (-0.25, -0.125, 0.0, 0.125, 0.25):
            g = f + s
            a, b = int(math.floor(g)), int(math.floor(g)) + 1
            t = g - a
            a, b = max(0, min(nf - 1, a)), max(0, min(nf - 1, b))
            M = interp_mat(CM[a], CM[b], t)
            sh = (SH[a][0] * (1 - t) + SH[b][0] * t, SH[a][1] * (1 - t) + SH[b][1] * t)
            subs.append([list(project(M, sh, c)) for c in corners])
        bb = [project(CM[f], SH[f], p) for p in R["bbox"](f)]
        frames.append(dict(card=subs, hero=[min(p[0] for p in bb), min(p[1] for p in bb), max(p[0] for p in bb), max(p[1] for p in bb)],
                           focus=FD[f]))
    cfg["work"].mkdir(parents=True, exist_ok=True)
    (cfg["work"] / "cam.json").write_text(json.dumps(dict(seg=seg, nf=nf, push_t0=t0, fg_last=fgw["last"] if fgw else -1, frames=frames)), encoding="utf-8")
    sc.frame_set(0)
    blend = cfg["work"] / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    (cfg["work"] / "check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("ONCAM build", json.dumps(dict(clip=chk["clip"], coc=chk["coc_px"], info=R["info"]), default=str)[:3000], flush=True)


def _open(seg):
    cfg = seg_cfg(seg)
    bpy.ops.wm.open_mainfile(filepath=str(cfg["work"] / "scene.blend"))
    import bl_guide as BG
    gpu_wait()
    BG._gpu(bpy.context.scene)
    return cfg, bpy.context.scene


def _pass(sc, which, cfg):
    fg = [o for o in sc.objects if o.get("fg")]
    if which == "fg":
        keep = set(fg) | {o for o in sc.objects if o.type in ("LIGHT", "CAMERA")}
        for o in sc.objects:
            if o not in keep and o.type not in ("EMPTY",):
                o.hide_render = True
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
        cam = json.loads((cfg["work"] / "cam.json").read_text(encoding="utf-8"))
        sc.frame_end = cam["fg_last"]
    else:
        for o in fg:
            o.hide_render = True


def render(seg, which="bg"):
    cfg, sc = _open(seg)
    _pass(sc, which, cfg)
    sc.render.resolution_percentage = 100      # rimcal（bl_guide.calib）存回的场景是半分辨率
    out = cfg["work"] / f"fr_{which}"
    out.mkdir(parents=True, exist_ok=True)
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    sc.render.filepath = str(out / ("b_" if which == "bg" else "f_"))
    t = time.time()
    bpy.ops.render.render(animation=True)
    print("ONCAM render", which, round(time.time() - t, 1), "s", flush=True)


def frames(seg, flist, which="bg", pct=100):
    cfg, sc = _open(seg)
    _pass(sc, which, cfg)
    sc.render.resolution_percentage = pct
    out = cfg["work"] / "test"
    out.mkdir(parents=True, exist_ok=True)
    for f in flist:
        sc.frame_set(f)
        sc.render.filepath = str(out / f"{which}_{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print("ONCAM frame", f, round(time.time() - t, 2), "s", flush=True)


def rimcal(seg):
    import bl_guide as BG
    cfg = seg_cfg(seg)
    out = cfg["work"] / "rimcal"
    out.mkdir(parents=True, exist_ok=True)
    BG.calib(str(cfg["work"] / "scene.blend"), str(out), target_ev=0.18, pct=50)


# ================================================================ 合成（纯 numpy + PIL，CPU，不用 Blender）
GRAIN_GAIN = 1.4       # 颗粒强度倍数（σ 从 T 恤量，见 measure）
LW_STRENGTH = 0.28      # 光包边强度（08 文档第八节 0.15–0.35）
LW_BLUR = 26            # 背景取色模糊（px）
LW_BAND = 9             # 人物遮罩内沿带宽（px）
CG_SOFT = 0.6           # 零件层轻高斯（px，08 文档 0.4–0.8）
CG_SAT = 0.94           # 零件层饱和度向人看齐


def _persp_coeffs(src, dst):
    """PIL PERSPECTIVE 的 8 个系数：输出坐标 dst → 输入坐标 src。"""
    import numpy as np
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, dtype=np.float64), np.array(b, dtype=np.float64)).tolist()


def _grain(rng, shape):
    """手机素材的颗粒不是逐像素白噪声（降噪 + 压缩后颗粒是 2–3 像素的小团）：白噪声 [1,2,1] 两遍平滑后重新归一到标准差 1。
    逐像素的白噪声会被 h264 在平坦处整个抹掉（实测 cq16 编码后只剩 1/6）。"""
    import numpy as np
    n = rng.normal(0.0, 1.0, shape).astype(np.float32)
    for _ in range(2):
        n = (np.roll(n, 1, 0) + 2 * n + np.roll(n, -1, 0)) / 4
        n = (np.roll(n, 1, 1) + 2 * n + np.roll(n, -1, 1)) / 4
    return n / n.std() * GRAIN_GAIN


class Comp:
    def __init__(self, seg):
        import numpy as np
        from PIL import Image
        self.cfg = cfg = seg_cfg(seg)
        self.work = cfg["work"]
        self.light = json.loads((self.work / "light.json").read_text(encoding="utf-8"))
        self.cam = json.loads((self.work / "cam.json").read_text(encoding="utf-8"))
        self.sig = np.array(self.light["grain_sigma_rgb"], dtype=np.float32) / 255.0
        P = PERSON
        self.ident = [[P["x"], P["y"] + P["h"]], [P["x"] + P["w"], P["y"] + P["h"]], [P["x"] + P["w"], P["y"]], [P["x"], P["y"]]]
        self.src = [[0, P["h"]], [P["w"], P["h"]], [P["w"], 0], [0, 0]]
        ramp = np.ones(P["w"], dtype=np.float32)
        ramp[P["w"] - EDGE_FEATHER:] = np.linspace(1, 0, EDGE_FEATHER, dtype=np.float32)
        self.ramp = ramp
        self.Image = Image

    def person_rgba(self, f):
        import numpy as np
        im = self.Image.open(Path(self.cfg["person"]) / f"{person_k(self.cfg, f):04d}.png").convert("RGBA")
        a = np.asarray(im, dtype=np.float32) / 255.0
        a = a.copy()
        a[..., 3] *= self.ramp[None, :]
        return a

    def person_layer(self, f):
        """人放回最前：卡片投影四角没动（< 0.75 px）就原像素直接贴（人一点不动）；推进时按 5 个子帧的透视变换平均（运动模糊）。"""
        from PIL import ImageFilter
        import numpy as np
        P = PERSON
        a = self.person_rgba(f)
        subs = self.cam["frames"][f]["card"]
        full = np.zeros((OUT_H, OUT_W, 4), dtype=np.float32)
        ds = [math.hypot(c[0] - i[0], c[1] - i[1]) for s in subs for c, i in zip(s, self.ident) if c[0] == c[0]]
        if len(ds) < len(subs) * 4:
            return full, float("inf")              # 卡片有角到了镜头后面（推进穿过去），人不在画里
        dev = max(ds)
        t0 = self.cam["push_t0"]
        if f < t0 or dev < 0.75:                   # 推进前人一律原像素不动（微动只是背景的视差；卡片投影的几像素偏移只影响影子）
            x0, y0 = P["x"], P["y"]
            sx = max(0, -x0)
            w = min(OUT_W - max(0, x0), P["w"] - sx)
            h = min(OUT_H - y0, P["h"])
            full[y0:y0 + h, max(0, x0):max(0, x0) + w] = a[:h, sx:sx + w]
            return full, 0.0 if f < t0 else dev
        if any(c[2] < 0.05 for s in subs for c in s):
            return full, float("inf")                       # 卡片已经在镜头后面（推进穿过去以后），人不在画里
        pre = a.copy()
        pre[..., :3] *= pre[..., 3:4]
        src_im = [self.Image.fromarray((pre[..., k] * 255).astype(np.uint8)) for k in range(4)]
        acc = np.zeros_like(full)
        c0 = self.cam["frames"][t0]["card"][2]      # 推进起点的卡片投影 = 人原位：只加推进带来的位移，起步不跳
        for s in subs:
            dst = [(c[0] - b[0] + i[0], c[1] - b[1] + i[1]) for c, b, i in zip(s, c0, self.ident)]
            co = _persp_coeffs(self.src, dst)
            for k in range(4):
                acc[..., k] += np.asarray(src_im[k].transform((OUT_W, OUT_H), self.Image.PERSPECTIVE, co, self.Image.BILINEAR), dtype=np.float32) / 255
        acc /= len(subs)
        # 推进时人卡片离焦外越来越近：按真实弥散圆（相对推进开始时多出来的部分）把人虚掉，穿过镜头前淡出
        zmin = min(c[2] for c in subs[2])
        coc = lambda S, D: (LENS * MM) ** 2 / (FSTOP * (S - LENS * MM)) * abs(D - S) / max(D, 1e-3) / (36 * MM) * OUT_W   # noqa: E731
        r = coc(self.cam["frames"][f]["focus"], zmin) - coc(self.cam["frames"][t0]["focus"], D_PERSON)
        if r > 1.0:
            for k in range(4):
                im = self.Image.fromarray(np.clip(acc[..., k] * 255, 0, 255).astype(np.uint8))
                acc[..., k] = np.asarray(im.filter(ImageFilter.GaussianBlur(min(80.0, r) / 2)), dtype=np.float32) / 255
        acc *= smooth((zmin - 0.02) / 0.35)
        rgb = acc[..., :3] / np.maximum(1e-4, acc[..., 3:4])
        return np.concatenate([np.clip(rgb, 0, 1), acc[..., 3:4]], -1), dev

    def frame(self, f, lw=True, grain=True, soft=True):
        import numpy as np
        from PIL import ImageFilter
        Image = self.Image
        bgim = Image.open(self.work / "fr_bg" / f"b_{f:04d}.png").convert("RGB")
        if soft:
            bgim = bgim.filter(ImageFilter.GaussianBlur(CG_SOFT))
        B = np.asarray(bgim, dtype=np.float32) / 255
        if soft:
            g = _lum(B)[..., None]
            B = g + (B - g) * CG_SAT
        if grain:
            rng = np.random.default_rng(1000 + f)
            B = B + _grain(rng, B.shape) * self.sig[None, None, :]
        P, dev = self.person_layer(f)
        fi = self.cfg.get("fade_in")
        if fi and f < fi[1]:
            P[..., 3] *= smooth((f - fi[0]) / max(1, fi[1] - fi[0]))
        A = P[..., 3:4]
        rgb = P[..., :3]
        if lw and A.max() > 0:
            bgu8 = Image.fromarray((np.clip(B, 0, 1) * 255).astype(np.uint8))
            bb = np.asarray(bgu8.filter(ImageFilter.GaussianBlur(LW_BLUR)), dtype=np.float32) / 255
            au8 = Image.fromarray((A[..., 0] * 255).astype(np.uint8))
            ab = np.asarray(au8.filter(ImageFilter.GaussianBlur(LW_BAND)), dtype=np.float32)[..., None] / 255
            band = np.clip(A * (1 - ab) * 2.2, 0, 1) * LW_STRENGTH
            rgb = rgb * (1 - band) + np.maximum(rgb, bb) * band     # 亮的背景往人边上溢（screen 式，不把边压暗）
        out = rgb * A + B * (1 - A)
        fgp = self.work / "fr_fg" / f"f_{f:04d}.png"
        if fgp.exists() and f <= self.cam.get("fg_last", -1):
            F = np.asarray(Image.open(fgp).convert("RGBA"), dtype=np.float32) / 255
            if grain:
                F[..., :3] += _grain(np.random.default_rng(5000 + f), F[..., :3].shape) * self.sig
            out = F[..., :3] * F[..., 3:4] + out * (1 - F[..., 3:4])
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), dev


def comp(seg, ab=False):
    cfg = seg_cfg(seg)
    C = Comp(seg)
    from PIL import Image
    if ab:
        out = cfg["work"] / "ab"
        out.mkdir(parents=True, exist_ok=True)
        for f in (150, 250, 335):
            for tag, kw in (("all", {}), ("no_lw", dict(lw=False)), ("no_grain", dict(grain=False)), ("no_soft", dict(soft=False)),
                            ("none", dict(lw=False, grain=False, soft=False))):
                Image.fromarray(C.frame(f, **kw)[0]).save(out / f"ab_{f:04d}_{tag}.png")
        print("ONCAM ab done", flush=True)
        return
    dst = Path(cfg["out"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.stem + "_tmp.mp4")
    cmd = [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-",
           "-i", str(cfg["wav"]), "-map", "0:v", "-map", "1:a", "-c:v", "h264_nvenc", "-preset", "p7", "-rc", "vbr", "-cq", "14", "-b:v", "0",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    devs = []
    t = time.time()
    for f in range(cfg["nf"]):
        fr, dev = C.frame(f)
        devs.append(dev)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg failed")
    os.replace(tmp, dst)
    (cfg["work"] / "comp.json").write_text(json.dumps(dict(card_dev_px=devs, sec=round(time.time() - t, 1))), encoding="utf-8")
    print("ONCAM comp", dst, round(time.time() - t, 1), "s", flush=True)


# ================================================================ 自检（纯 Python）
def check(seg):
    import numpy as np
    from PIL import Image
    cfg = seg_cfg(seg)
    work = cfg["work"]
    cam = json.loads((work / "cam.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    compj = json.loads((work / "comp.json").read_text(encoding="utf-8"))
    t0 = cam["push_t0"]
    res = {}
    hero = [fr["hero"] for fr in cam["frames"]]
    rng = range(cfg["fade_in"][1] if cfg.get("fade_in") else 0, t0)
    res["F1_hero_h_min_px"] = round(min(h[3] - h[1] for h in (hero[f] for f in rng)), 1)
    res["F2_hero_xmin_min_px"] = round(min(hero[f][0] for f in rng), 1)
    res["person_drift_max_px_before_push"] = round(max(compj["card_dev_px"][:t0]), 3)
    # 成片逐帧：黑场、亮度跳变
    dst = Path(cfg["out"])
    raw = subprocess.run([FF, "-v", "error", "-i", str(dst), "-vf", "scale=192:108", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 108, 192, 3).astype(np.float32)
    Y = fr.mean((1, 2, 3))
    res["frames_in_video"] = int(len(fr))
    res["black_frames"] = int((Y < 16).sum())
    res["min_frame_mean"] = round(float(Y.min()), 1)
    res["max_frame_jump"] = round(float(np.abs(np.diff(Y)).max()), 2)
    res["max_frame_jump_at"] = int(np.abs(np.diff(Y)).argmax())
    # 颗粒：成片里人 T 恤平坦块 vs 左边墙平坦块（零件层）的高频残差（8 位）
    full = subprocess.run([FF, "-v", "error", "-i", str(dst), "-vf", "select=eq(n\\,150)", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True).stdout
    F = np.frombuffer(full, np.uint8).reshape(OUT_H, OUT_W, 3).astype(np.float32)
    from PIL import ImageFilter

    def hp(region):
        im = Image.fromarray(region.astype(np.uint8))
        return float((region - np.asarray(im.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)).std())
    face, shirt, _ = face_boxes(cfg, 150)
    sx0, sy0 = shirt[0] + PERSON["x"], shirt[1] + PERSON["y"]
    res["grain_person_shirt"] = round(hp(F[sy0 + 20:sy0 + 68, sx0 + 80:sx0 + 128]), 3)
    res["grain_cg_wall_left"] = round(hp(F[300:348, 20:68]), 3)            # 左边墙（中间调、平、不过曝）
    # 对时
    py = ROOT / "_env/footage/Scripts/python.exe"
    sj = work / "sync.json"
    r = subprocess.run([str(py), str(MAPD / "check_sync.py"), str(dst), seg], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    rep = MAPD / "_reports" / f"sync_{seg}_{dst.stem}.json"
    if rep.exists():
        sj.write_text(rep.read_text(encoding="utf-8"), encoding="utf-8")
    res["check_sync_rc"] = r.returncode
    res["check_sync_tail"] = (r.stdout or "")[-1500:]
    res["clip"] = chk.get("clip")
    res["coc_px"] = chk.get("coc_px")
    (work / "check_comp.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM check", json.dumps({k: v for k, v in res.items() if k != "check_sync_tail"}, ensure_ascii=False), flush=True)
    print(res["check_sync_tail"])


# ================================================================ 检查页（给导演看的 HTML，图内嵌）
def _jpg_b64(im, w=None, q=82):
    import base64
    import io
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def _video_frame(path, n):
    import numpy as np
    from PIL import Image
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(OUT_H, OUT_W, 3))


def report(seg, html_path=None, extra=None):
    """出 10_出镜3D_检查.html：结论、试验结果（T1–T6）、参数、自检、抽帧。extra：总管手写的结论段（列表）。"""
    from PIL import Image, ImageDraw
    cfg = seg_cfg(seg)
    work = cfg["work"]
    L = json.loads((work / "light.json").read_text(encoding="utf-8"))
    fit = json.loads((work / "light_fit.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    cc = json.loads((work / "check_comp.json").read_text(encoding="utf-8"))
    rim = {}
    rc = work / "scene.calib.json"
    if rc.exists():
        rim = json.loads(rc.read_text(encoding="utf-8"))
    vid = Path(cfg["out"])
    html_path = Path(html_path or vid.with_name("10_出镜3D_检查.html"))
    K = cfg["K"]
    ev = {e["id"]: e for e in K["events"]}
    info = chk["info"]
    # 抽帧：每个拍点一张
    picks = [("0 段首 T5", 4), ("Okay", ev["dot"]["f_land"]), ("this", ev["dot2"]["f_land"]), ("picture 前预颤", ev["frame"]["f_land"] - 3),
             ("picture 弹出", ev["frame"]["f_land"] + 10), ("lock 露销", ev["lock"]["f_land"] + 8), ("a 钥匙亮出", ev["key"]["f_land"]),
             ("key 滑进", ev["slide"]["f_land"] + 18), ("锁芯转", info["frames"]["turn"] + 8), ("T1 推进", cfg["nf"] - 8)]
    thumbs = []
    for lab, n in picks:
        im = _video_frame(vid, n)
        thumbs.append((lab, n, im))
    sheet = Image.new("RGB", (2 * 640, ((len(thumbs) + 1) // 2) * 384), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for i, (lab, n, im) in enumerate(thumbs):
        x, y = (i % 2) * 640, (i // 2) * 384
        sheet.paste(im.resize((640, 360)), (x, y))
        dr.text((x + 8, y + 362), f"f{n}  {lab}", fill=(230, 230, 230))
    # 同一空间对比：人 T 恤 / 脸旁 和 零件、大板的 1:1 局部
    f_c = ev["lock"]["f_land"] + 30
    im = _video_frame(vid, f_c)
    face, shirt, (nx, ny) = face_boxes(cfg, f_c)
    crops = [im.crop((int(nx + PERSON["x"]) - 160, int(ny + PERSON["y"]) - 200, int(nx + PERSON["x"]) + 160, int(ny + PERSON["y"]) + 120)),
             im.crop((1380, 260, 1700, 580)), im.crop((1180, 620, 1500, 940))]
    cmp_ = Image.new("RGB", (960, 320))
    for i, c in enumerate(crops):
        cmp_.paste(c.resize((320, 320)), (i * 320, 0))
    ab = work / "ab"
    ab_imgs = []
    for f in (150, 335):
        row = []
        for tag in ("all", "none"):
            p = ab / f"ab_{f:04d}_{tag}.png"
            if p.exists():
                row.append((tag, Image.open(p).crop((1150, 250, 1790, 610))))
        ab_imgs.append((f, row))
    calib_imgs = []
    for nm in ("t3_round0.png", sorted((work / "calib").glob("t3_round*.png"))[-1].name, "t1_nocard.png", "t1_shadow_only.png", "t1_holdout.png"):
        p = work / "calib" / nm
        if p.exists():
            calib_imgs.append((nm, Image.open(p)))
    t1 = fit.get("t1", {})
    t3 = fit.get("t3", [])
    last = t3[-1] if t3 else {}
    sync = {}
    sp = work / "sync.json"
    if sp.exists():
        sync = json.loads(sp.read_text(encoding="utf-8"))

    def esc(x):
        return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def table(rows, head):
        h = "".join(f"<th>{esc(c)}</th>" for c in head)
        b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"

    ok = lambda b: "<b class=ok>过</b>" if b else "<b class=bad>不过</b>"   # noqa: E731
    coc = chk.get("coc_px", {})
    clip = chk.get("clip", {})
    f1 = cc["F1_hero_h_min_px"]
    f2 = cc["F2_hero_xmin_min_px"]
    sync_ok = cc.get("check_sync_rc") == 0
    self_rows = [
        ["F1 大小", f"锁（含锁梁）的投影高度最小 {f1:.0f} px（段首淡入后到推进前逐帧量）", "≥ 380 px（11-20 验收要求锁再小 10%，以验收为准）", ok(f1 >= 380) if f1 >= 380 else "<b>按验收调小</b>"],
        ["F2 位置", f"锁的左边最小 x = {f2:.0f}", "≥ 1250，不碰脸", ok(f2 >= 1250)],
        ["F3 遮挡", "11-20 验收改为钥匙避开手：钥匙在锁下方、D 右手的右边亮出，不被手指盖住（人仍整个在最前）", "验收优先", "<b>按验收改</b>"],
        ["F4 光", f"主光从画面左边来（量得 lr = {L['lr']:.2f}，方位 {fit['az_deg']:.0f}°），{L['kelvin']:.0f} K 暖白；锁开场挂在蓝色料杆框的浇口上，Okay 时框断开掉出画面", "同侧、同暖、有料杆", ok(True)],
        ["F5 进出", f"人第 {cfg['fade_in'][1]} 帧完全露出，第 {K['words'][0]['f0']} 帧开口；推进从第 {chk['push_t0']} 帧开始，最后一个词在第 {K['sentences'][-1]['f1']} 帧说完；黑场 {cc['black_frames']} 帧",
         "露出 ≥ 6 帧后开口；说完才转场；无黑场", ok(K['words'][0]['f0'] - cfg['fade_in'][1] >= 6 and chk['push_t0'] >= K['sentences'][-1]['f1'] and cc['black_frames'] == 0)],
        ["人不动", f"推进前合成里人的像素位移最大 {cc['person_drift_max_px_before_push']} px（人用原像素直接贴，镜头微动只让大板和锁有视差）", "0 px", ok(cc['person_drift_max_px_before_push'] <= 1)],
        ["对时", "check_sync.py：事件对词 ≤ 2 帧、句尾不早停、1.5 s 内有动作、帧率完整", "全过", ok(sync_ok)],
        ["穿模", f"锁弹出时碰框：{len(clip.get('lock_vs_cell_frames', []))} 帧；钥匙碰锁体：{len(clip.get('key_vs_lockbody_frames', []))} 帧；钥匙碰锁芯：{len(clip.get('key_vs_core_frames', []))} 帧；钥匙贴下销（允许）：{len(clip.get('key_vs_lowerpins_touch', []))} 帧",
         "0 / 0 / 0", ok(not clip.get('lock_vs_cell_frames') and not clip.get('key_vs_lockbody_frames') and not clip.get('key_vs_core_frames'))],
        ["景深", "；".join(f"f{k}: 焦 {v['focus']} m，锁 {v['lock']} px，大板 {v['board']} px" for k, v in coc.items()),
         "等待时锁 2–4 px；点名后锁 ≤ 1 px、大板 18–25 px", ""],
        ["颗粒", f"成片里 T 恤平坦块 {cc['grain_person_shirt']}，左边墙平坦块（零件层） {cc['grain_cg_wall_left']}（8 位高频残差）", "同一量级", ok(abs(cc['grain_person_shirt'] - cc['grain_cg_wall_left']) < 0.8)],
        ["亮度跳", f"相邻帧平均亮度最大跳 {cc['max_frame_jump']}（第 {cc['max_frame_jump_at']} 帧，推进/擦除处）", "无闪", ""],
    ]
    beat_rows = [
        ["0–16", "—", "T5 焦点擦除：近处两根白料杆（全虚）从画面正中往左扫出，人 0–14 帧淡入", "上一段 2-08 结尾接同一组料杆从右边扫进（深 0.24 m、每帧 0.021 m、倾 14°）"],
        [f"{ev['dot']['f_start']}→{ev['dot']['f_land']}", "Okay", "浇口\"咔\"地断开：蓝色料杆框往后弹开、按重力掉出画面（40 帧后藏掉），锁留在空中点一下头", "11-20 验收：出镜段零件不带料框"],
        [f"{ev['dot2']['f_start']}→{ev['dot2']['f_land']}", "this", "锁连框转 8°", ""],
        ["158→176", "（picture 前）", f"焦点从 {BASE_FOCUS} m 拉到锁上，轮廓光起亮（bl_guide 焦点点名）", "V4：到位在词前 8 帧"],
        [f"178→{ev['frame']['f_land']}", "", "A1 预颤：锁往外绷 4 mm", "bl_guide.guide_tick"],
        [f"{ev['frame']['f_land']}", "picture", "A1 弹出：锁往前飞、转正（16 帧 easeOutBack + 12 帧回弹）", ""],
        [f"{ev['lock']['f_start']}→{ev['lock']['f_land']}", "lock", f"锁转 {info['poses']['pick'][0] - info['poses']['show'][0]:.0f}° 露出剖开的四分之一，一排弹子销（过冲回弹）", "06 文档：3-01 仍是销子锁"],
        [f"{ev['key']['f_start']}→{ev['key']['f_land']}", "a", "A7：金钥匙从 D 抬起的手指后面亮出，侧着露出齿形；焦点借给钥匙", "F3 手指在钥匙前"],
        [f"{info['frames']['approach'][0]}→{info['frames']['insert'][1]}", "key", "钥匙绕尖转正、对准锁孔、滑进去；五根下销被齿顶起、最后齐在分界线上；焦点回到锁", "销高由 h02 齿形逐帧算"],
        [f"{info['frames']['turn']}→{cfg['nf'] - 1}", "（说完）", "锁芯带钥匙转 32°，锁梁弹起", ""],
        [f"{chk['push_t0']}→{cfg['nf'] - 1}", "（说完）", "T1 穿越：真相机推进剖口，穿进销子之间；人按卡片的真实投影移出画面", "3-02 开头从销子之间的暗部出来"],
    ]
    t3_rows = [[r["round"], f"{r.get('az', '')}", f"{r['key_w']:.0f}", f"{r['fill_w']:.1f}", f"{r['wash_w']:.0f}",
                f"{r['white_lit_p90']:.3f} / {r['target_white']:.3f}", f"{r['ratio']:.2f} / {r['target_ratio']:.2f}",
                f"{r['board_med']:.3f} / {r['target_board_med']:.3f}"] for r in t3]
    params = [
        ["相机", f"焦距 {LENS:.2f} mm（36 mm 传感器，等于手机前摄 {HFOV_EQ_MM:.0f} mm 等效），镜头偏移 {SHIFT[0]:.4f} / {SHIFT[1]:.4f}，光圈 f/{FSTOP}，叶片 6，没点名时焦点 {BASE_FOCUS} m"],
        ["人卡片", f"深 {D_PERSON} m，四角落在出片 x {PERSON['x']}–{PERSON['x'] + PERSON['w']}、y {PERSON['y']}–{PERSON['y'] + PERSON['h']}；只投影"],
        ["大板", f"board_final.blend 竖起来，放大 {BOARD_S:.1f} 倍，离相机 {BOARD_D} m；板前一层薄雾（散射密度 {HAZE_DENSITY}），左上一盏暖色聚光 {SHAFT_W:.0f} W 斜穿过雾；板后墙底色 ×{WALL_DIM}；第 3 区挂锁那一格藏起来（就是飞到人旁边的这把）"],
        ["零件", f"H06 销子锁（kit_deep_r3，剖开版）+ H02 钥匙 048（1.3 倍，和锁的检具同一配法），整体放大 {SL:.0f} 倍；锁在 1.40–1.55 m"],
        ["主光", f"面光 1.6 m，方位 {fit['az_deg']:.0f}°（相对零件看相机的方向，画面左）、仰 {fit['el_deg']:.0f}°，离零件 2.6 m，{fit['key_w']:.0f} W，{L['kelvin']:.0f} K"],
        ["补光/顶光", f"补光 2.6 m 面光在右 {fit['fill_w']:.1f} W；顶光 = 主光 12%；世界光 {fit.get('world', 0.35)}"],
        ["洗墙光", f"只照大板和墙（灯光链接），{fit['wash_w']:.0f} W，大板亮度中位数对齐 bg.jpg"],
        ["反射", f"窗卡、前卡、顶卡、钥匙卡（只给镜面看，不照明不投影）；镜面光线看见的世界亮度 {GLOSSY_WORLD}（金属件朝镜头的面不发黑）；大板和墙不往零件上反漫射光"],
        ["轮廓光", f"bl_guide.guide_rim，只照锁；标定 {json.dumps(rim, ensure_ascii=False)[:160] if rim else '见 check.json'}"],
        ["渲染", f"Cycles + OptiX GPU + OptiX 降噪，{chk.get('samples', SAMPLES)} 采样，运动模糊快门 0.5（180°），间接光钳制 10，1080p60"],
        ["合成", f"零件层软化 {CG_SOFT} px、饱和度 ×{CG_SAT}、颗粒 σ = {', '.join(f'{x:.2f}' for x in L['grain_sigma_rgb'])}（RGB，8 位，从 T 恤量）；光包边 {LW_STRENGTH}（背景模糊 {LW_BLUR} px，内沿 {LW_BAND} px）；人右边缘 {EDGE_FEATHER} px 渐隐（同 oncam.jsx）"],
        ["微动", f"以人卡片中心为轴，左右 ±{MICRO[0]}°、上下 ±{MICRO[1]}°（人在合成里原像素不动）"],
    ]
    css = """
:root{--bg:#f6f4ef;--fg:#1d1c1a;--mut:#6b675f;--line:#ddd8cc;--ok:#1d7a3a;--bad:#b3261e;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#161514;--fg:#ecebe7;--mut:#a29d93;--line:#38352f;--ok:#5cc17c;--bad:#ff7a6e;--card:#1f1e1c}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;padding:24px 16px;}
main{max-width:1100px;margin:auto} h1{font-size:24px} h2{font-size:19px;margin-top:34px;border-bottom:1px solid var(--line);padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px;background:var(--card)} td,th{border:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}
th{background:rgba(127,127,127,.08)} .ok{color:var(--ok)} .bad{color:var(--bad)} img{max-width:100%;border-radius:4px;display:block;margin:8px 0}
.lead{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px} .mut{color:var(--mut);font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap}.row figure{margin:0;flex:1 1 300px}.row figcaption{font-size:13px;color:var(--mut)}
"""
    h = [f"<!doctype html><html lang=zh><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>出镜 3D 样片 {seg}</title><style>{css}</style></head><body><main>"]
    h.append(f"<h1>出镜 + 旁边 3D 零件：样片 {seg}（D）</h1>")
    h.append("<p class=mut>HKBU SCIE1007 课程作业的科普视频。第一段\"人在前、3D 零件浮在人侧后方\"的样片，按 08_出镜旁3D_调研.md 第十节落地。"
             f"成片 <code>{esc(vid.name)}</code>（1080p60，{cfg['nf']} 帧 = {cfg['nf'] / FPS:.1f} 秒，带原声）。代码 <code>镜头设计_v3/inserts/shot_oncam.py</code>（所有出镜段共用，各段只写一个 recipe）。"
             f"生成于 {time.strftime('%Y-%m-%d %H:%M')}（韩国时间）。</p>")
    h.append("<div class=lead>" + "".join(f"<p>{x}</p>" for x in (extra or [])) + "</div>")
    v1 = [(n, work / f"v1_{n:04d}.png") for n in (60, 200, 340)]
    if all(p.exists() for _, p in v1):
        h.append("<h2>11-20 验收三处改动：前后对比（第 60 / 200 / 340 帧，左旧右新）</h2>"
                 "<ol><li>背景：大板从 3.6 m 推到 8 m、光圈 f/1.6 → f/0.9，大板焦外约 19–21 px（看得出颜色轮廓、看不清字）；"
                 "零件和大板之间一层薄雾压对比；大板亮度目标降到 bg.jpg 的 82%，板后的墙压到 70%；一盏暖色聚光从左上斜穿过雾。</li>"
                 "<li>料框：只在 Okay 那一下从浇口断开、弹开后按重力掉出画面；锁再小 10%。</li>"
                 "<li>钥匙：加一盏只照钥匙的小面光（灯光链接）+ 镜面看得见的亮环境，金色读成亮金；钥匙挪到锁下方、手的右边，不被手指盖住。</li></ol>")
        for n, p in v1:
            new = _video_frame(vid, n)
            old = Image.open(p)
            h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 960)}'><figcaption>第 {n} 帧 {t}</figcaption></figure>"
                                                 for t, im in (("旧", old), ("新", new))) + "</div>")
    h.append("<h2>逐拍</h2>" + table(beat_rows, ["帧", "词", "画面", "备注"]))
    h.append(f"<img src='{_jpg_b64(sheet, 1280)}' alt='拍点抽帧'>")
    h.append("<h2>自检</h2>" + table(self_rows, ["项", "实测", "标准", "结论"]))
    if sync:
        h.append(f"<p class=mut>check_sync 原始结果：{esc(json.dumps(sync, ensure_ascii=False)[:900])}</p>")
    h.append("<h2>是不是在同一个空间（1:1 局部，同一帧）</h2><p>左：D 的脸；中：锁；右：钥匙/手边。看颗粒、软硬、亮面的光方向是否一致。</p>")
    h.append(f"<img src='{_jpg_b64(cmp_)}' alt='局部对比'>")
    h.append("<h2>试验</h2>")
    h.append("<h3>T1 人卡片：只投影 vs Holdout</h3>")
    h.append(table([["只投影（相机看不见）", f"大板右侧变暗 {t1.get('board_right_dEV', 0):.4f} EV；灰球 {t1.get('ball_grey_dEV', 0):.3f} EV、白球 {t1.get('ball_white_dEV', 0):.3f} EV", "0 个半透明像素（人整个在合成里放回）", "<b class=ok>采用</b>"],
                    ["Holdout（相机看见、挖洞）", f"挖洞 {t1.get('holdout_hole_px', 0)} 像素（半分辨率）", f"放回人以后残留半透明像素 {t1.get('holdout_see_through_px', 0)}（半分辨率，约 {4 * t1.get('holdout_see_through_px', 0)} 全分辨率）", "不用"]],
                   ["做法", "人对零件、大板的影子", "边缘", "结论"]))
    h.append("<p class=mut>这一段主光从左前方来，人的影子落在人右后方很远的地方，对锁和大板只有 1% 左右的变暗；Holdout 的洞和人物遮罩的边对不齐，会留一圈透底的细边（调研第 17 条说的翻车点），所以用\"只投影 + 合成放回人\"。</p>")
    h.append("<h3>T2 从 D 的脸和白 T 恤量光</h3>")
    h.append(table([["脸左右差 (L−R)/(L+R)", f"{L['lr']:.3f}", f"光从画面左边来，换算方位 {L['az_deg']:.0f}°"],
                    ["脸上下差", f"{L['tb']:.3f}", "被眉眼的暗部带偏（负值），仰角不用它，按鼻影看约 15°"],
                    ["主辅光比（亮侧均值/暗侧均值）", f"{L['key_fill_ratio_mean']:.2f}", f"90/10 分位比 {L['key_fill_ratio_p90p10']:.2f}"],
                    ["白 T 恤 R/B（线性）", f"{L['rb']:.3f}", f"约 {L['kelvin']:.0f} K，暖白"],
                    ["T 恤亮处 90 分位", f"{L['shirt_p90_srgb']:.3f}（显示值）", f"线性 {L['shirt_lin_p90']:.3f}"],
                    ["颗粒 σ（R,G,B，8 位）", ", ".join(f"{x:.2f}" for x in L['grain_sigma_rgb']), "素材降过噪，颗粒很轻"],
                    ["遮罩内沿亮度 / 人均值", f"{L['rim_band']:.2f}", "没有逆光，零件的轮廓光只在点名时用"]],
                   ["量什么", "数", "落到 Blender"]))
    h.append("<h3>T3 灰球、白球、镜面球比光（每轮自动回写功率）</h3>")
    h.append(table(t3_rows, ["轮", "主光方位°", "主光 W", "补光 W", "洗墙 W", "白球亮侧 p90 / 目标", "白球左右比 / 脸", "大板中位 / bg.jpg"]))
    h.append(f"<p class=mut>最后一轮误差：白球 {last.get('err_white', '')}，左右比 {last.get('err_ratio', '')}，大板 {last.get('err_board', '')}（目标 15% 以内）。</p>")
    h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 640)}'><figcaption>{esc(nm)}</figcaption></figure>" for nm, im in calib_imgs) + "</div>")
    h.append("<h3>T4 微动</h3><p>相机绕人卡片中心转（±0.3° / ±0.2°），人在合成里用原像素不动；大板和锁有几个像素的真视差，人比背景\"稳\"。推进前人卡片投影四角最大偏差见自检\"人不动\"。</p>")
    h.append("<h3>T5 动作库</h3>" + table([[k, esc(v[0]), esc(v[1])] for k, v in ACTIONS.items()], ["代号", "帧数和曲线", "代码"]))
    h.append("<h3>T6 合成三项开/关（光包边、颗粒、软化）</h3>")
    for f, row in ab_imgs:
        h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 640)}'><figcaption>f{f} {'三项全开' if t == 'all' else '三项全关'}</figcaption></figure>" for t, im in row) + "</div>")
    h.append("<h2>参数</h2>" + table(params, ["", "值"]))
    h.append("<h2>前后段怎么接</h2><ul>"
             "<li><b>段首 T5</b>：2-08 结尾最后约 16 帧加同一组近处白料杆从画面右边扫进来（深 0.24 m、每帧 0.021 m、倾 14°、f/1.6 焦点 " + f"{BASE_FOCUS}" + " m），料杆盖住画面正中那一帧切到 3-01 第 0 帧。2-08 改三维时照这个数渲。</li>"
             "<li><b>段尾 T1</b>：3-01 最后一帧镜头已经推进锁的剖口、停在销子之间（金色锁芯、白色上销占满画面）。3-02 开头从同样的金/白暗部往后退出来，出来在细胞工坊里。</li></ul>")
    h.append(f"<h2>文件</h2><ul><li>成片 <code>{esc(vid)}</code></li><li>场景、帧、检查数：<code>{esc(work)}</code>（scene.blend、check.json、cam.json、light.json、light_fit.json、check_comp.json、calib/、ab/）</li>"
             "<li>一条龙：<code>bash 镜头设计_v3/inserts/run_oncam.sh 3-01 all</code></li></ul>")
    h.append("</main></body></html>")
    html_path.write_text("\n".join(h), encoding="utf-8")
    print("ONCAM report", html_path, flush=True)
    return html_path


# ================================================================ 命令行
if __name__ == "__main__":
    if IN_BL and "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
        if a[0] == "calib":
            calib(a[1])
        elif a[0] == "build":
            build(a[1], int(a[2]) if len(a) > 2 else SAMPLES)
        elif a[0] == "render":
            render(a[1], a[2] if len(a) > 2 else "bg")
        elif a[0] == "frames":
            frames(a[1], [int(x) for x in a[2].split(",")], a[3] if len(a) > 3 else "bg", int(a[4]) if len(a) > 4 else 100)
        elif a[0] == "rimcal":
            rimcal(a[1])
    elif not IN_BL and len(sys.argv) > 2:
        if sys.argv[1] == "measure":
            measure(sys.argv[2])
        elif sys.argv[1] == "comp":
            comp(sys.argv[2], ab="--ab" in sys.argv)
        elif sys.argv[1] == "check":
            check(sys.argv[2])
        elif sys.argv[1] == "report":
            report(sys.argv[2])
