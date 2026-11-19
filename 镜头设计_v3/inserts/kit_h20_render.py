"""HKBU SCIE1007 课程作业的科普视频：h20 套件盒盖的验收和检查图。

    blender -b --factory-startup -P kit_h20_render.py -- check            只做几何验收（含大板），写 h20_report.json
    blender -b --factory-startup -P kit_h20_render.py -- render [only:a,b] 验收 + 出图（Cycles 64 采样）
    blender -b --factory-startup -P kit_h20_render.py -- preview           不搭大板，16 采样半尺寸，出到 tmp/h20/
名字一律用占位（draft=True），不读任何名字文件。
"""
import json
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import kit_deep as D
import kit_h20 as H

OUT = Path("G:/cdk20/work/kit_deep")
CACHE = OUT / "tmp" / "h20_board_cache.blend"
QUEUE = (HERE.parents[1] / "_env" / "queue", Path.home() / "cdk20_guard")
args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0]
only = set(",".join(a[5:] for a in args if a.startswith("only:")).split(",")) - {""}
preview = mode == "preview"
dest = OUT / "tmp" / "h20" if preview else OUT
dest.mkdir(parents=True, exist_ok=True)
sc = D.scene_base(16 if preview else 64)
sc.cycles.max_bounces = 8
sc.cycles.adaptive_threshold = .02
# 导演规定：出图一律 Cycles + OPTIX GPU + OptiX 降噪，不许回落 CPU。
sc.cycles.device = "GPU"
sc.cycles.denoiser = "OPTIX"
_prefs = bpy.context.preferences.addons["cycles"].preferences
_gpus = [d.name for d in _prefs.devices if d.use and d.type == "OPTIX"]
if _prefs.compute_device_type != "OPTIX" or not _gpus or any(d.use and d.type == "CPU" for d in _prefs.devices):
    raise SystemExit("h20: OPTIX GPU not active, refusing to render on CPU")
print("[h20] render device OPTIX:", _gpus, flush=True)
D.backdrop()
D.lights(-.004, 0, 1.6)
K = D.Kit()
data = {"target": "h20", "mode": mode, "renders": {}}
t0 = time.time()


def log(*a):
    print(f"[h20 {time.time() - t0:6.0f}s]", *a, flush=True)


# ---------------------------------------------------------------- 几何


def visible(root):
    return [o for o in root.children_recursive if o.type in ("MESH", "FONT", "CURVE")
            and not o.hide_render and not o.hide_viewport]


def geom(obs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    V, F = [], []
    for ob in obs:
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
        if me is None:
            continue
        me.calc_loop_triangles()
        n = len(V)
        mw = eo.matrix_world
        V.extend(mw @ v.co for v in me.vertices)
        F.extend((t.vertices[0] + n, t.vertices[1] + n, t.vertices[2] + n) for t in me.loop_triangles)
        eo.to_mesh_clear()
    return V, F


def bounds(V):
    a = np.array([tuple(v) for v in V]) / D.MM
    return a.min(0), a.max(0)


def tree(V, F):
    return BVHTree.FromPolygons(V, F, all_triangles=True)


def min_dist(Va, Ta, Vb, Tb, reach=4.):
    """两组网格的最小距离（mm，顶点到对方表面，双向），只看 reach 以内。"""
    best = reach
    r = reach * D.MM
    for V, T in ((Va, Tb), (Vb, Ta)):
        for v in V:
            hit = T.find_nearest(v, r)
            if hit[0] is not None and hit[3] / D.MM < best:
                best = hit[3] / D.MM
    return best


def near(V, lo, hi, pad):
    lo, hi = Vector(lo) * D.MM - Vector((pad,) * 3) * D.MM, Vector(hi) * D.MM + Vector((pad,) * 3) * D.MM
    return [v for v in V if lo.x <= v.x <= hi.x and lo.y <= v.y <= hi.y and lo.z <= v.z <= hi.z]


# ---------------------------------------------------------------- 大板（缓存成 .blend，第二次起直接读）


def board():
    if CACHE.exists():
        with bpy.data.libraries.load(str(CACHE)) as (src, dst):
            dst.objects = list(src.objects)
        for ob in dst.objects:
            sc.collection.objects.link(ob)
        root = next(o for o in dst.objects if o.name.startswith("board") and o.parent is None)
        log("board from cache", len(dst.objects), "objects")
        return root
    info = D.make_board(K)
    root = info["board"]
    obs = {root, *root.children_recursive}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(CACHE), obs, fake_user=False)
    log("board built and cached", info["xl"], info["xr"])
    return root


# ---------------------------------------------------------------- 相机和出图


def camera(target, pitch, az, width, lens=50., f8=False):
    cam = sc.camera
    if cam is None:
        cam = D.camera(sc, (0, 0, 0), 1, 30, 0)
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36
    cam.data.lens = lens
    dist = width * lens / 36
    e, a = math.radians(pitch), math.radians(az)
    t = D._mm(target)
    cam.location = t + Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e))) * dist * D.MM
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = .01
    cam.data.dof.use_dof = f8
    if f8:
        cam.data.dof.aperture_fstop = 8
        cam.data.dof.focus_distance = dist * D.MM
    return cam


def shot(label, target, pitch, az, width, *, hd=False, f8=False, lens=50.):
    cam = camera(target, pitch, az, width, lens, f8)
    sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if hd else (1600, 900)
    data["renders"][label] = dict(target=target, pitch=pitch, az=az, width_mm=width, lens=lens,
                                  fstop=8 if f8 else None, size=[sc.render.resolution_x, sc.render.resolution_y])
    if mode == "check" or (only and label not in only):
        return cam
    while any((b / m).exists() for b in QUEUE for m in ("GPU_HOLD", "GPU_PAUSED")):
        print("WAIT_GPU", flush=True)
        time.sleep(15)
    out = dest / f"h20_{label}.png"
    log("render", out.name)
    s = time.time()
    D.render(sc, str(out), 50 if preview else 100)
    data["renders"][label]["seconds"] = round(time.time() - s, 1)
    return cam


def cap_pixels(cam, ob, cap=None):
    """字的大写字高投影到画面上的像素数（取字的左右两端和中间三处的平均）。"""
    cap = cap or ob["cap_mm"]
    bpy.context.view_layer.update()
    mw = ob.matrix_world
    xs = [min(v[0] for v in ob.bound_box), max(v[0] for v in ob.bound_box)]
    res = []
    W, Hh = sc.render.resolution_x, sc.render.resolution_y
    for x in (xs[0], (xs[0] + xs[1]) / 2, xs[1]):
        p0 = world_to_camera_view(sc, cam, mw @ Vector((x, 0, ob.data.extrude)))
        up = (mw.to_3x3() @ Vector((0, 1, 0))).normalized() * cap * D.MM
        p1 = world_to_camera_view(sc, cam, mw @ Vector((x, 0, ob.data.extrude)) + up)
        res.append(math.hypot((p1.x - p0.x) * W, (p1.y - p0.y) * Hh))
    return round(sum(res) / 3, 1)


# ---------------------------------------------------------------- 主流程

try:
    H.h20_kit_box(K, names={"A": "Member A", "B": "Member B", "C": "Member C"})
except ValueError as exc:
    data["H6_missing_member_error"] = str(exc)
else:
    raise RuntimeError("h20 accepted names without D")
try:
    H.h20_kit_box(K)
except ValueError as exc:
    data["H6_no_names_error"] = str(exc)
else:
    raise RuntimeError("h20 accepted draft=False without names")
# 两次报错留下的半成品清掉。
for ob in [o for o in bpy.data.objects if o.name.startswith("h20_kit_box") or o.name.startswith("p04_liver")
           or o.name.startswith("p19_cdk20") or o.name.startswith("p22_key")]:
    bpy.data.objects.remove(ob, do_unlink=True)

lid = H.h20_kit_box(K, draft=True)
lid.location.x = -4 * D.MM
H.rest(lid)
J = H.rig(lid)
data["roles"] = sorted(J)
data["role_count"] = len(J)
for key in ("title_end_x", "qmark_end_x", "course_end_x", "subtitle_cap_mm", "subtitle_width_mm", "section_cap_mm"):
    data[key] = round(float(lid[key]), 2)
lid_obs = visible(lid)
LV, LF = geom(lid_obs)
data["triangles"] = len(LF)
shell_obs = [o for o in lid_obs if "_shell" in o.name or "side_rib" in o.name]
lo, hi = bounds(geom(shell_obs)[0])
data["H1_shell_size_mm"] = [round(float(v), 2) for v in hi - lo]
data["H1_pass"] = bool(np.all(np.abs((hi - lo) - np.array([986, 332, 64])) <= .5))
log("built lid", data["triangles"], "tris; shell", data["H1_shell_size_mm"])

# H4 和全部顶面角色：每个角色 11 个姿态，和盒盖其余部分做 BVH 相交 + 最小距离。
moving_roles = ["badge", "sec_plate", "qmark", "rule", "art_0", "art_1", "art_2"] + [f"tag_{k}" for k in range(8)]
spec = json.loads(lid["rig"])
roles_out = {}
for role in moving_roles:
    mine = set(visible(J[role]))
    others = [o for o in lid_obs if o not in mine]
    SV, SF = geom(others)
    ST = tree(SV, SF)
    lo_r, hi_r = spec[role]["min"], spec[role]["max"]
    rows = []
    for i in range(11):
        v = lo_r + (hi_r - lo_r) * i / 10
        H.pose(lid, role, v)
        MV, MF = geom(list(mine))
        MT = tree(MV, MF)
        b0, b1 = bounds(MV)
        crossing = len(MT.overlap(ST))
        d = min_dist(MV, MT, near(SV, b0, b1, 4), ST)
        rows.append([round(v, 3), crossing, round(d, 3)])
    H.pose(lid, role, spec[role]["rest"])
    need = .2 if role.startswith("tag") or role == "sec_plate" else 0.
    worst = min(r[2] for r in rows)
    roles_out[role] = dict(samples_value_crossings_mindist=rows, min_dist_mm=worst,
                           crossings=sum(r[1] for r in rows), need_mm=need,
                           pass_=bool(sum(r[1] for r in rows) == 0 and worst >= need - 1e-3))
    log(role, "crossings", roles_out[role]["crossings"], "min", worst)
data["H4_roles"] = roles_out
data["H4_pass"] = all(r["pass_"] for r in roles_out.values())

if not preview:
    B = board()
    bpy.context.view_layer.update()
    BV, BF = geom(visible(B))
    BT = tree(BV, BF)
    bl, bh = bounds(BV)
    data["board_bounds_mm"] = [[round(float(x), 2) for x in bl], [round(float(x), 2) for x in bh]]
    data["board_highest_mm"] = round(float(bh[2]), 2)
    data["roof_margin_mm"] = round(CEILING := H.CEIL - float(bh[2]), 2)
    # 只拿离盒盖可能近的大板顶点（高处和四周）去量到盒盖表面的距离。
    ext = np.array([tuple(v) for v in BV]) / D.MM
    keep = (ext[:, 2] > 30) | (np.abs(ext[:, 0] + 4) > 455) | (np.abs(ext[:, 1]) > 140)
    BVn = [BV[i] for i in np.nonzero(keep)[0]]
    log("board", len(BV), "verts,", len(BVn), "near the lid")

    def lid_vs_board(reach=30.):
        V, F = geom(lid_obs)
        T = tree(V, F)
        crossing = len(T.overlap(BT))
        best = reach
        r = reach * D.MM
        for v in BVn:
            hit = T.find_nearest(v, r)
            if hit[0] is not None and hit[3] / D.MM < best:
                best = hit[3] / D.MM
        lowv = [v for v in V if v.z < 120 * D.MM]
        for v in lowv:
            hit = BT.find_nearest(v, r)
            if hit[0] is not None and hit[3] / D.MM < best:
                best = hit[3] / D.MM
        table = min(v.z for v in V) / D.MM
        return crossing, round(best, 3), round(table, 3)

    H.rest(lid)
    c, d, tz = lid_vs_board()
    data["H2_rest"] = dict(crossings=c, min_dist_mm=d, pass_=c == 0 and d >= 2)
    log("H2", data["H2_rest"])
    path = []
    for i in range(11):
        H.pose(lid, "lid_lift", 8 * i)
        c, d, tz = lid_vs_board()
        path.append(["lift", 8 * i, c, d, tz])
    for i in range(11):
        H.pose(lid, "lid_hinge", 10.4 * i)
        c, d, tz = lid_vs_board()
        path.append(["hinge", round(10.4 * i, 1), c, d, tz])
    H.rest(lid)
    data["H3_path_kind_value_crossings_boardmin_lidlowz"] = path
    data["H3_pass"] = all(p[2] == 0 and p[3] >= 2 for p in path) and \
        all(p[4] >= 2 for p in path if not (p[0] == "lift" and p[1] == 0))
    log("H3 pass", data["H3_pass"])
    (OUT / "h20_report.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

floor = bpy.data.objects.get("sweep")
if mode != "check":
    # 1 合盖落下：盒盖在板上方 150 mm，牌都立着，课程牌、问号还在上面，红线没长出来。
    H.pose(lid, "lid_lift", 0)
    lid.location.z = 150 * D.MM
    for r, v in (("badge", 12), ("qmark", 10), ("rule", 0), ("sec_plate", -90)):
        H.pose(lid, r, v)
    for k in range(8):
        H.pose(lid, f"tag_{k}", -90)
    shot("lid_drop", (-4, 0, 60), 35, -20, 986 / .92 * 1.12)
    lid.location.z = 0
    # 2 各牌倒下中段（b7 前后）：牌 1–2 已平、牌 3 弹起、牌 4 倒到一半，5–8 立着。
    for r in ("badge", "qmark", "rule", "sec_plate"):
        H.pose(lid, r, spec[r]["rest"])
    for k, v in enumerate((0, 0, -6, -46, -90, -90, -90, -90)):
        H.pose(lid, f"tag_{k}", v)
    shot("tags_midway", (-120, -80, 70), 38, -14, 560)
    # 3 全部到位：全盖机位（俯角 80°，盒盖宽占画面 90%）。
    H.rest(lid)
    cam = shot("all_seated", (-4, 0, 64), 80, 0, 986 / .9)
    if mode != "preview":
        pass
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    texts = {o.name: o for o in lid_obs if o.type == "FONT"}
    pick = lambda s: next(o for o in lid_obs if o.type == "FONT" and o.data.body == s)
    data["H5_full_cover_px_1080p"] = {
        "title": cap_pixels(cam, pick("WORTH TESTING")),
        "course_name": cap_pixels(cam, pick("Molecular Science in Daily Life")),
        "SCIE1007": cap_pixels(cam, pick("SCIE1007")),
        "section_plate": cap_pixels(cam, pick("Section 20007 · Group 3B")),
        "subtitle": cap_pixels(cam, pick("How computers help find cancer drug candidates: the CDK20 story")),
    }
    # H7：牌全立时，在全盖机位里每块牌的投影宽度（像素，竖直方向）和字面是否朝向相机。
    for k in range(8):
        H.pose(lid, f"tag_{k}", -90)
    bpy.context.view_layer.update()
    plate = next(o for o in visible(J["tag_0"]) if "chapter_plate" in o.name and "lip" not in o.name)
    pts = [world_to_camera_view(sc, cam, plate.matrix_world @ Vector(c)) for c in plate.bound_box]
    label0 = next(o for o in visible(J["tag_0"]) if o.type == "FONT" and o.data.body == "Four a day")
    face_n = (label0.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    view = (cam.location - label0.matrix_world.translation).normalized()
    data["H7_text_normal_dot_view"] = round(face_n.dot(view), 3)
    data["H7_upright_tag_px_1080p"] = round((max(p.y for p in pts) - min(p.y for p in pts)) * 1080, 1)
    data["H7_text_faces_camera"] = bool(face_n.dot(view) > 0)
    H.rest(lid)
    # 4 盒盖翻开 50° 和 100°（先抬 80）。
    H.pose(lid, "lid_lift", 80)
    H.pose(lid, "lid_hinge", 50)
    shot("lid_open_50", (-4, 60, 120), 26, -22, 1500)
    H.pose(lid, "lid_hinge", 100)
    shot("lid_open", (-4, 80, 110), 24, -22, 1500)
    H.rest(lid)
    # 5 3/4 斜视，1920×1080。
    shot("threequarter", (-40, 0, 40), 30, -34, 1180, hd=True)
    # 6 两张 f/8 对焦近景（牌近景机位：俯角 75°，画面宽 342 mm）。
    cam = shot("closeup_tags_1_3", (-285, -95.5, 65.8), 75, 0, 342, f8=True, lens=85)
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    data["H5_tag_closeup_px_1080p"] = {
        "chapter_title": cap_pixels(cam, pick("Our question")),
        "chapter_number": cap_pixels(cam, pick("2")),
        "names_line_all_four": cap_pixels(cam, pick("All four of us")),
    }
    shot("closeup_tags_6_8", (285, -95.5, 65.8), 75, 0, 342, f8=True, lens=85)
    if preview:
        shot("corner_detail", (-420, -150, 50), 22, -40, 160, f8=True, lens=85)

data["seconds"] = round(time.time() - t0)
name = "h20_report_preview.json" if preview else "h20_report.json"
(OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("H20_DONE", json.dumps({k: v for k, v in data.items() if k not in ("H4_roles", "renders")}, default=str), flush=True)
