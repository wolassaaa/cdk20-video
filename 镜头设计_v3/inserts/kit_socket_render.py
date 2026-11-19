"""HKBU SCIE1007 课程作业的科普视频：H01b 插座和 H02b 插头组的验收出图（Cycles + OPTIX GPU，OptiX 降噪）。

用法：blender -b --factory-startup -P kit_socket_render.py -- <组名> [preview] [replace]
组名：overview（合盖、开盖、3/4、插入通电、048 拧卡口、001 12°、A–F 半路）、close（C1–C10 对焦近景）。
输出 G:/cdk20/work/kit_deep/h01b_*.png、h02b_*.png。
"""
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy
from mathutils import Vector
import kit_deep as D
import kit_socket as S

OUT = Path("G:/cdk20/work/kit_deep")
QUEUE = [HERE.parents[1] / "_env" / "queue", Path.home() / "cdk20_guard"]
flags = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = "preview" in flags
REPLACE = "replace" in flags
W, H = (800, 450) if PREVIEW else (1600, 900)


def wait_gpu():
    while any((b / m).exists() for b in QUEUE for m in ("GPU_HOLD", "GPU_PAUSED")):
        print("WAIT_GPU", flush=True)
        time.sleep(12)


def setup(samples=64):
    sc = D.scene_base(samples if not PREVIEW else 12)
    sc.cycles.max_bounces = 10
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.cycles.adaptive_threshold = .02
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "PNG"
    # 确认没有回落 CPU
    pr = bpy.context.preferences.addons["cycles"].preferences
    gpus = [d.name for d in pr.devices if d.use and d.type != "CPU"]
    print("RENDER_DEVICE", sc.cycles.device, pr.compute_device_type, gpus, flush=True)
    assert sc.cycles.device == "GPU" and gpus
    D.backdrop()
    D.lights()
    return sc


def fill_light(root, energy=2.5, side=None):
    """舱内补光：60×40 毫米面光，放在分件面上方前侧，仰角 30°，对着机舱；再加一盏从 -U 侧来的低角度侧光，让面和面有明暗差。"""
    off = Vector((0, 0, root.location.z))
    tgt = Vector((-9, 0, -8)) * D.MM + off
    ld = bpy.data.lights.new("fill_cabin", "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = 60 * D.MM, 40 * D.MM
    ld.energy = energy
    ld.color = (1, .98, .95)
    ob = D.link(bpy.data.objects.new("fill_cabin", ld))
    el = math.radians(30)
    ob.location = tgt + Vector((math.cos(el), 0, math.sin(el))) * .12
    ob.rotation_euler = (tgt - ob.location).to_track_quat("-Z", "Y").to_euler()
    sd = 0.8 if side is None else side
    ls = bpy.data.lights.new("side_cabin", "AREA")
    ls.shape = "RECTANGLE"
    ls.size, ls.size_y = 40 * D.MM, 30 * D.MM
    ls.energy = sd
    ls.color = (.92, .96, 1.0)
    o2 = D.link(bpy.data.objects.new("side_cabin", ls))
    o2.location = tgt + Vector((-.01, -.09, .05))
    o2.rotation_euler = (tgt - o2.location).to_track_quat("-Z", "Y").to_euler()
    return ob


def plinth(root, h=1.6):
    """给零件垫一块台面（毫米级零件的底座），返回台面物体。"""
    bpy.context.view_layer.update()
    zmin = min((root.matrix_world @ Vector(c)).z for ob in root.children_recursive
               if ob.type == "MESH" for c in ob.bound_box)
    root.location.z += (h * D.MM - zmin)
    global ZOFF
    ZOFF = root.location.z
    pl = D.Part(K, "plinth", "white")
    pl.box(0, 0, 70, 70, h, K.white, z=h / 2, r=3, bevel=.3)
    return pl.root


ZOFF = 0.0


def cam_at(sc, tgt, az, el, dist, lens=50, fstop=None, focus=None, sensor=None):
    t = Vector(tgt) * D.MM + Vector((0, 0, ZOFF))
    c = D.camera(sc, t, dist * D.MM, el, az, lens=lens, fstop=fstop,
                 focus=(Vector(focus) * D.MM + Vector((0, 0, ZOFF))) if focus is not None else None)
    if sensor:
        c.data.sensor_width = sensor
    c.data.clip_start = .0002
    return c


RES = None


def shoot(sc, name, res=None):
    wait_gpu()
    res = res or RES or (W, H)
    sc.render.resolution_x, sc.render.resolution_y = (res[0] // 2, res[1] // 2) if PREVIEW else res
    out = OUT / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not REPLACE:
        print("SKIP", out.name)
        return
    t = time.time()
    D.render(sc, str(PREVIEW and (OUT / "tmp" / f"{name}.png") or out), 100)
    print("DONE", name, round(time.time() - t, 1), "s", flush=True)


def set_cam(sc, cam):
    sc.camera = cam


K = None


def start(samples=64):
    global K
    sc = setup(samples)
    import kit_parts as KP
    K = KP.Kit()
    return sc
