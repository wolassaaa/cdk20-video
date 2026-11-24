"""HKBU SCIE1007 课程作业的科普视频：可复用的快速渲染模板（审片/总管/渲染提速_20261116）。

一个文件两种用法：
  1) 外面用系统 Python 调（发令器）：
       python fast_render.py SCENE.blend --out DIR [--f0 0 --f1 59] [--engine cycles|eevee] [--profile preview|final]
                             [--blender PATH] [--bake/--no-bake] [--split auto|1|2] [--samples N] [--pct 100]
     步骤：
       a. --bake（默认开）：在 Blender 里逐帧比较几何，找出几何在动的物体（shape key、修改器、几何节点、曲线
          bevel 生长、字），把它们在 [f0, f1+1] 烘成一个 Alembic，换成 Mesh Sequence Cache 读缓存，
          另存 _render_tmp/fast_render/<场景>_<f0>_<f1>/baked.blend。渲染时不再每帧算 shape key / 修改器。
       b. 整段一次渲：blender -b baked.blend -P fast_render.py -s f0 -e f1 -a，persistent_data 开，
          不再每帧单独调一次 render(write_still)。
       c. --engine 切 Cycles / EEVEE，同一个 .blend。
       d. --split auto：先开一路；探测 25 秒显卡占用，平均 < 70% 且另一个 GPU 槽空着，就再开第二路。
          两路渲同一帧段，靠占位文件（use_placeholder + 不覆盖）各拿各的帧，谁快谁多拿。
          槽位和 styleframes/art/gpu_slot.sh 是同一组（.slots/1、.slots/2），全机最多两个 Blender。
       e. --profile preview：半分辨率、Cycles 8 采样 / EEVEE 16；final：全分辨率、Cycles 用场景采样
          （没设就 24）/ EEVEE 64。--samples、--pct 可以再覆盖。
     结束写 DIR/_fast_render.json：每路用时、秒/帧（按出图时间）、显卡占用采样。
  2) Blender 里（-P 进来，-- 后第一个词是子命令）：
       bake  ABC BLEND f0 f1      烘焙并另存
       apply ENGINE PROFILE OUT [samples] [pct]   只改渲染设置（后面跟 -a 由 Blender 自己整段渲）
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]                      # D:/。hkbu/molecular science
SLOTS = HERE.parents[2] / ".slots"          # styleframes/art/.slots，和 gpu_slot.sh 共用
BLENDER_DEFAULT = "D:/software/tools/blender.exe"


# ====================================================================== Blender 里

def _geo_sig(o, dg):
    """几何指纹：顶点数 + 坐标和。看不到的物体也照算（hide_render 动画不影响几何）。"""
    import numpy as np
    ev = o.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        return None
    if me is None:
        return None
    n = len(me.vertices)
    if n == 0:
        ev.to_mesh_clear()
        return (0,)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    sig = (n, len(me.polygons), round(float(co.sum()), 7), round(float(np.abs(co).sum()), 7))
    ev.to_mesh_clear()
    return sig


def find_animated(sc, f0, f1, samples=16):
    """在 f0..f1 里均匀取样，几何指纹变了的物体就是"动画几何"。物体级移动/旋转/显隐不算（那些不贵，留关键帧）。"""
    cand = [o for o in sc.objects if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META", "CURVES")]
    n = min(samples, f1 - f0 + 1)
    frames = sorted({f0 + round(i * (f1 - f0) / max(1, n - 1)) for i in range(n)})
    sigs = {o.name: set() for o in cand}
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for o in cand:
            sigs[o.name].add(_geo_sig(o, dg))
    return [bpy.data.objects[k] for k, v in sigs.items() if len(v) > 1]


def _as_mesh_object(o, f0):
    """曲线/字体对象换成网格对象（缓存修改器只能挂在网格上）；网格对象原地清掉 shape key 和修改器。"""
    sc = bpy.context.scene
    sc.frame_set(f0)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    obj_mats = [(s.link, s.material) for s in o.material_slots]
    if o.type == "MESH":
        if o.data.shape_keys:
            o.shape_key_clear()
        o.modifiers.clear()
        o.data = me
        tgt = o
    else:
        tgt = bpy.data.objects.new(o.name + "__c", me)
        for c in o.users_collection:
            c.objects.link(tgt)
        tgt.parent, tgt.parent_type = o.parent, o.parent_type
        tgt.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        tgt.matrix_basis = o.matrix_basis.copy()
        if o.animation_data and o.animation_data.action:
            ad = tgt.animation_data_create()
            ad.action = o.animation_data.action
            if hasattr(o.animation_data, "action_slot") and o.animation_data.action_slot is not None:
                try:
                    ad.action_slot = o.animation_data.action_slot
                except Exception:
                    pass
        for attr in ("hide_render", "hide_viewport", "visible_camera", "visible_shadow", "visible_diffuse",
                     "visible_glossy", "visible_transmission", "visible_volume_scatter", "is_holdout", "pass_index"):
            if hasattr(o, attr):
                setattr(tgt, attr, getattr(o, attr))
        for ch in list(o.children):
            mw = ch.matrix_world.copy()
            ch.parent = tgt
            ch.matrix_world = mw
        name = o.name
        bpy.data.objects.remove(o)
        tgt.name = name
    for i, (link, mat) in enumerate(obj_mats):
        if link == "OBJECT" and i < len(tgt.material_slots):
            tgt.material_slots[i].link = "OBJECT"
            tgt.material_slots[i].material = mat
    return tgt


def bake(abc, out_blend, f0, f1):
    sc = bpy.context.scene
    t0 = time.time()
    anim = find_animated(sc, f0, f1)
    names = [o.name for o in anim]
    for o in anim:
        _MESH_NAMES[o.name] = o.data.name
    print(f"FAST_BAKE animated {len(names)}: {names[:30]}", flush=True)
    if not names:
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
        return
    for o in sc.objects:
        o.select_set(False)
    muted = _mute_vis_curves(anim)
    hidden = []
    for o in anim:
        hidden.append((o, o.hide_viewport, o.hide_get(), o.hide_render))
        o.hide_viewport = o.hide_render = False
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = anim[0]
    # f1+1：运动模糊要看下一帧
    bpy.ops.wm.alembic_export(filepath=abc, start=f0, end=f1 + 1, selected=True, flatten=True, curves_as_mesh=True,
                              uvs=True, normals=True, face_sets=True, export_hair=False, export_particles=False,
                              evaluation_mode="RENDER", apply_subdiv=False, triangulate=False)
    for o, hv, hs, hr in hidden:
        o.hide_viewport, o.hide_render = hv, hr
        o.hide_set(hs)
    for fc in muted:
        fc.mute = False
    print(f"FAST_BAKE abc {time.time() - t0:.1f}s", flush=True)
    before = set(bpy.data.cache_files)
    bpy.ops.cachefile.open(filepath=abc)
    cf = (set(bpy.data.cache_files) - before).pop()
    cf.is_sequence = False
    for nm in names:
        o = bpy.data.objects[nm]
        tgt = _as_mesh_object(o, f0)
        m = tgt.modifiers.new("fast_cache", "MESH_SEQUENCE_CACHE")
        m.cache_file = cf
        # flatten 后路径是 /<物体名>/<网格名>；网格名取导出时的数据名
        m.object_path = _abc_path(nm, tgt.data.name if tgt.name == nm else nm)
        m.read_data = {"VERT", "POLY", "UV", "COLOR"}
        m.use_vertex_interpolation = True
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print(f"FAST_BAKE done {time.time() - t0:.1f}s -> {out_blend}", flush=True)


def _abc_name(n):
    return "".join("_" if ch in " .:" else ch for ch in n)


_MESH_NAMES = {}


def _abc_path(objname, _unused=None):
    """flatten=True 时路径是 /<物体名>/<网格名>，导出器把空格、点、冒号换成下划线。
    后台模式下 cache_file.object_paths 是空的，所以按导出前记下的网格名拼。"""
    return f"/{_abc_name(objname)}/{_abc_name(_MESH_NAMES[objname])}"


def _fcurves(action):
    if action is None:
        return []
    out = list(getattr(action, "fcurves", []) or [])
    for L in getattr(action, "layers", []):
        for st in L.strips:
            for cb in getattr(st, "channelbags", []):
                out += list(cb.fcurves)
    return out


def _mute_vis_curves(objs):
    """导出器跳过视图里隐藏的物体；显隐有关键帧时先静音这些曲线，导完恢复。"""
    muted = []
    for o in objs:
        ad = o.animation_data
        for fc in _fcurves(ad.action if ad else None):
            if fc.data_path in ("hide_viewport", "hide_render") and not fc.mute:
                fc.mute = True
                muted.append(fc)
    return muted


def apply(engine, profile, out, samples=None, pct=None):
    sc = bpy.context.scene
    r = sc.render
    eng = engine.lower()
    if eng == "eevee":
        r.engine = "BLENDER_EEVEE"
        e = sc.eevee
        e.taa_render_samples = samples or (16 if profile == "preview" else 64)
        for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True)):
            if hasattr(e, attr):
                setattr(e, attr, val)
    else:
        r.engine = "CYCLES"
        pr = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                pr.compute_device_type = kind
                pr.get_devices()
                if any(d.type == kind for d in pr.devices):
                    break
            except TypeError:
                continue
        for d in pr.devices:
            d.use = d.type != "CPU"
        sc.cycles.device = "GPU"
        base = sc.cycles.samples if sc.cycles.samples and sc.cycles.samples < 1024 else 24
        sc.cycles.samples = samples or (8 if profile == "preview" else base)
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPTIX"
        if os.environ.get("CDK20_DENOISER", "").lower() == "oidn":   # 11-24 透明件补渲：换 OpenImageDenoise（显卡）；默认不设 = 不变
            sc.cycles.denoiser = "OPENIMAGEDENOISE"
            sc.cycles.denoising_use_gpu = True
            sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
            sc.cycles.denoising_prefilter = "ACCURATE"
        sc.cycles.use_auto_tile = False
    r.use_persistent_data = True
    r.resolution_percentage = pct or (50 if profile == "preview" else 100)
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA" if r.film_transparent else "RGB"   # 透明底片（出镜旁动效要叠真人）留 alpha
    r.image_settings.compression = 15
    r.use_overwrite = False
    r.use_placeholder = True
    r.filepath = os.path.join(out, "f_####")
    print(f"FAST_APPLY {r.engine} {profile} res {r.resolution_percentage}% samples "
          f"{sc.cycles.samples if r.engine == 'CYCLES' else sc.eevee.taa_render_samples} -> {out}", flush=True)


def blender_main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        return
    if argv[0] == "bake":
        bake(argv[1], argv[2], int(argv[3]), int(argv[4]))
    elif argv[0] == "apply":
        apply(argv[1], argv[2], argv[3], int(argv[4]) if len(argv) > 4 and argv[4] != "-" else None,
              int(argv[5]) if len(argv) > 5 and argv[5] != "-" else None)


# ====================================================================== 外面（发令器）

def blender_count():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq blender.exe", "/NH"], capture_output=True, text=True).stdout
    return sum(1 for ln in out.splitlines() if ln.lower().startswith("blender.exe"))


class GpuLog:
    def __init__(self):
        self.samples = []
        self.p = subprocess.Popen(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits",
                                   "-lms", "500"], stdout=subprocess.PIPE, text=True)
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()

    def _read(self):
        for ln in self.p.stdout:
            try:
                u, m = [int(x) for x in ln.split(",")]
                self.samples.append((time.time(), u, m))
            except ValueError:
                pass

    def mean(self, t0=0, t1=1e20):
        v = [u for t, u, _ in self.samples if t0 <= t <= t1]
        return sum(v) / len(v) if v else None

    def stop(self):
        self.p.terminate()


class Slot:
    """和 gpu_slot.sh 同一组槽：mkdir 原子占位，后台每分钟刷新时间，免得被当成 15 分钟废弃。"""
    def __init__(self, wait=True):
        SLOTS.mkdir(parents=True, exist_ok=True)
        self.d = None
        while self.d is None:
            for s in (1, 2):
                d = SLOTS / str(s)
                try:
                    d.mkdir()
                    self.d = d
                    break
                except FileExistsError:
                    if time.time() - d.stat().st_mtime > 900:
                        try:
                            d.rmdir()
                        except OSError:
                            pass
            if self.d is None:
                if not wait:
                    raise TimeoutError
                time.sleep(3)
        self.alive = True
        threading.Thread(target=self._beat, daemon=True).start()

    def _beat(self):
        while self.alive:
            try:
                os.utime(self.d)
            except OSError:
                pass
            time.sleep(60)

    def release(self):
        self.alive = False
        try:
            self.d.rmdir()
        except OSError:
            pass


def _env():
    e = dict(os.environ)
    e["TEMP"] = e["TMP"] = "D:/render_tmp"
    os.makedirs("D:/render_tmp", exist_ok=True)
    return e


def launch(a):
    import argparse  # noqa: F401
    blend = Path(a.scene).resolve()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rep = dict(scene=str(blend), blender=a.blender, engine=a.engine, profile=a.profile, f0=a.f0, f1=a.f1, bake=a.bake)
    T0 = time.time()
    src = blend
    if a.bake:
        # Alembic 在 Windows 上读不了带中文/全角字符的路径（写得出、读出来是空的），缓存一律放纯 ASCII 目录
        import hashlib
        key = hashlib.md5(str(blend).encode("utf-8")).hexdigest()[:8]
        wd = Path(os.environ.get("FAST_RENDER_CACHE", "G:/cdk20/work/fast_render")) / f"{key}_{a.f0}_{a.f1}_{Path(a.blender).parent.name}"
        wd.mkdir(parents=True, exist_ok=True)
        baked = wd / "baked.blend"
        if a.rebake or not baked.exists() or baked.stat().st_mtime < blend.stat().st_mtime:
            t = time.time()
            subprocess.run([a.blender, "-b", str(blend), "--python-exit-code", "1", "-P", str(Path(__file__).resolve()), "--",
                            "bake", str(wd / "geo.abc"), str(baked), str(a.f0), str(a.f1)], check=True, env=_env())
            rep["bake_s"] = round(time.time() - t, 1)
        src = baked
    cmd = [a.blender, "-b", str(src), "--python-exit-code", "1", "-P", str(Path(__file__).resolve()),
           "-s", str(a.f0), "-e", str(a.f1), "-a", "--", "apply", a.engine, a.profile, str(out),
           str(a.samples) if a.samples else "-", str(a.pct) if a.pct else "-"]
    gpu = GpuLog()
    procs, slots, starts = [], [], []

    waits = []

    def start():
        tw = time.time()
        s = Slot()
        waits.append(round(time.time() - tw, 1))
        slots.append(s)
        logf = open(out / f"_way{len(procs) + 1}.log", "w", encoding="utf-8")
        starts.append(time.time())
        procs.append(subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=_env()))

    start()
    nfr = a.f1 - a.f0 + 1
    want2 = a.split == "2" or a.split == "auto"
    if want2 and nfr >= 8:
        # 先等第一帧出图（场景加载、BVH 建完），再看 25 秒占用
        t_end = time.time() + 600
        while time.time() < t_end and procs[0].poll() is None and not _done_frames(out):
            time.sleep(1)
        tp = time.time()
        while time.time() < tp + 25 and procs[0].poll() is None:
            time.sleep(1)
        u = gpu.mean(tp, time.time())
        rep["probe_util"] = u
        left = nfr - len(_done_frames(out))
        go = procs[0].poll() is None and left >= 6 and blender_count() <= 1 and (a.split == "2" or (u is not None and u < 70))
        if go:
            try:
                s_free = not all((SLOTS / str(i)).exists() for i in (1, 2))
            except OSError:
                s_free = False
            if s_free:
                start()
        rep["ways"] = len(procs)
    codes = [p.wait() for p in procs]
    for s in slots:
        s.release()
    gpu.stop()
    T1 = time.time()
    frames = sorted(_done_frames(out))
    mt = sorted(f.stat().st_mtime for f in frames)
    rep.update(codes=codes, slot_wait_s=waits, ways=len(procs), frames=len(frames), wall_s=round(T1 - T0, 1),
               render_wall_s=round(T1 - starts[0], 1),
               s_per_frame_steady=round((mt[-1] - mt[0]) / max(1, len(mt) - 1), 3) if len(mt) > 1 else None,
               s_per_frame_total=round((T1 - T0) / max(1, len(frames)), 3),
               gpu_util_mean=round(gpu.mean(starts[0], T1) or 0, 1),
               gpu_util_steady=round(gpu.mean(mt[0], mt[-1]) or 0, 1) if len(mt) > 1 else None,
               gpu_mem_max=max((m for _, _, m in gpu.samples), default=None))
    (out / "_fast_render.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FAST_RENDER", json.dumps(rep, ensure_ascii=False))
    return 0 if all(c == 0 for c in codes) else 1


def _done_frames(out):
    return [p for p in Path(out).glob("f_*.png") if p.stat().st_size > 0]


def cli():
    import argparse
    ap = argparse.ArgumentParser(description="快速渲染模板（烘焙 + 整段 + 自动两路）")
    ap.add_argument("scene")
    ap.add_argument("--out", required=True)
    ap.add_argument("--f0", type=int, default=0)
    ap.add_argument("--f1", type=int, default=59)
    ap.add_argument("--engine", default="cycles", choices=["cycles", "eevee"])
    ap.add_argument("--profile", default="final", choices=["preview", "final"])
    ap.add_argument("--blender", default=BLENDER_DEFAULT)
    ap.add_argument("--bake", dest="bake", action="store_true", default=True)
    ap.add_argument("--no-bake", dest="bake", action="store_false")
    ap.add_argument("--rebake", action="store_true")
    ap.add_argument("--split", default="auto", choices=["auto", "1", "2"])
    ap.add_argument("--samples", type=int)
    ap.add_argument("--pct", type=int)
    sys.exit(launch(ap.parse_args()))


if IN_BLENDER:
    blender_main()
elif __name__ == "__main__":
    cli()
