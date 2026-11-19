"""HKBU SCIE1007 课程作业的科普视频：H01b / H02b 验收图的场景和出图组（Cycles + OPTIX GPU）。

用法：blender -b --factory-startup -P kit_socket_scenes.py -- <组名...> [preview] [replace]
组名：overview（合盖、开盖、3/4、S5 三态、通电/断电）、plugs（真插头通电、048 插入和拧卡口、001 卡 12°、A–F 半路、列队）、
close（C1–C9 对焦近景）、mini（三种孔型和入格）、id（S1/S4/S5 的像素统计）。
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy
from mathutils import Vector
import kit_deep as D
import kit_socket as S
import kit_socket_render as R

K = None
EXPO_DELTA = -0.2


KEY_SCALE = 0.6
WORLD_STRENGTH = 0.6


def key_scale(f):
    """主光、顶光、轮廓光和补光整体缩放（开盖舱内的白件不过曝用）。"""
    for n in ("key", "fill", "strip", "rim"):
        if n in bpy.data.objects:
            bpy.data.objects[n].data.energy *= f


def build_scene(samples=64, fill=1.1):
    global K
    sc = R.start(samples)
    K = R.K
    root = S.h01b_cdk20_socket(K)
    R.plinth(root)
    R.fill_light(root, fill)
    sc.view_settings.exposure += EXPO_DELTA          # 开盖舱内的白件不过曝；合盖图单独恢复
    key_scale(KEY_SCALE)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = WORLD_STRENGTH
    return sc, root


def hide(obj):
    for c in [obj] + list(obj.children_recursive):
        c.hide_render = True


def plug_on(root, which, d=0.0, twist=0.0, tilt=0.0, seed=None):
    p = S.h02b_plug(K, which=which, seed=seed) if seed is not None else S.h02b_plug(K, which=which)
    p.location = Vector(((S.SEAT_W + d) * D.MM, 0, root.location.z))
    S.pose(p, "twist", twist)
    S.pose(p, "tilt", tilt)
    return p


def power(root, on=True, piston=0.0, cell=1.0, flow=0.5):
    S.pose(root, "lamp_out", 1 if on else 0)
    S.pose(root, "lamp_in", 1 if on else 0)
    S.pose(root, "piston", piston)
    S.pose(root, "cell", cell)
    S.pose(root, "flow", flow if on else 0)
    for ch in S.rig(root)["flow"].children:
        ch.hide_viewport = False


C10 = dict(tgt=(-10, 0, -7), az=65, el=35, dist=66)
CMP = dict(tgt=(-8, 4, -9), az=75, el=52, dist=74)    # 开盖对比用机位：能同时看到接线柱、铜线、接线盒、光管、活塞、小细胞


def overview():
    sc, root = build_scene()
    power(root, False, 0.0, 1.0, 0)
    S.pose(root, "lid", 0)
    sc.view_settings.exposure -= EXPO_DELTA
    key_scale(1 / KEY_SCALE)
    R.cam_at(sc, (-5, 0, -2), 65, 35, 165)
    R.shoot(sc, "h01b_closed_1080", (1920, 1080))
    sc.view_settings.exposure += EXPO_DELTA
    key_scale(KEY_SCALE)
    S.pose(root, "lid", 110)
    R.cam_at(sc, (-12, 0, 2), 90, 18, 175)
    R.shoot(sc, "h01b_open_front_1080", (1920, 1080))
    R.cam_at(sc, C10["tgt"], C10["az"], C10["el"], C10["dist"])
    R.shoot(sc, "h01b_c10_open_34_1080", (1920, 1080))
    for a in (0, 55, 110):
        S.pose(root, "lid", a)
        R.cam_at(sc, (-10, 0, 0), 65, 35, 170)
        R.shoot(sc, f"h01b_s5_lid{a:03d}")
    S.pose(root, "lid", 110)
    for nm, on, pis, cl in (("power_on", True, 4.5, 1.4), ("power_off", False, 2.5, 1.15)):
        power(root, on, pis, cl, .55)
        R.cam_at(sc, C10["tgt"], 90, 55, 130)
        R.shoot(sc, f"h01b_{nm}")


def compare():
    """同机位（CMP）对比：空壳待机 → ATP 插入通电 → 048 拧死断电。"""
    sc, root = build_scene()
    S.pose(root, "lid", 110)
    power(root, False, 0.0, 1.0, 0)
    R.cam_at(sc, CMP["tgt"], CMP["az"], CMP["el"], CMP["dist"])
    R.shoot(sc, "h01b_cmp1_open_idle", (1920, 1080))
    p = plug_on(root, "ATP")
    power(root, True, 4.5, 1.4, .5)
    R.shoot(sc, "h01b_cmp2_atp_power_on", (1920, 1080))
    hide(p)
    q = plug_on(root, "048", 0.0, twist=90.0)
    S.pose(root, "tab", -25)
    power(root, False, 2.5, 1.15, 0)
    R.shoot(sc, "h01b_cmp3_048_clamped_power_off", (1920, 1080))


def plugs_group():
    sc, root = build_scene()
    S.pose(root, "lid", 110)
    p = plug_on(root, "ATP")
    power(root, True, 3.0, 1.3, .6)
    R.cam_at(sc, (2, 0, -3), 65, 38, 105)
    R.shoot(sc, "h02b_atp_inserted_power_on")
    S.pose(root, "lid", 0)
    R.cam_at(sc, (6, 0, 0), 75, 30, 95)
    R.shoot(sc, "h02b_atp_inserted_closed")
    S.pose(root, "lid", 110)
    hide(p)
    p = plug_on(root, "048")
    power(root, True, 0, 1.0, 0)
    for nm, d in (("000", 24.0), ("050", 12.0), ("100", 0.0)):
        p.location.x = (S.SEAT_W + d) * D.MM
        R.cam_at(sc, (6, 0, -2), 55, 30, 100)
        R.shoot(sc, f"h02b_048_insert_{nm}")
    p.location.x = S.SEAT_W * D.MM
    for ang in (0, 45, 90):
        S.pose(p, "twist", ang)
        S.pose(root, "tab", S.lug_tab_angle(ang))
        R.cam_at(sc, (9, 0, 0), 62, 40, 70)
        R.shoot(sc, f"h02b_048_twist_{ang:03d}")
    power(root, False, 5.0, 1.45, 0)
    R.cam_at(sc, (6, 0, -2), 70, 35, 105)
    R.shoot(sc, "h02b_048_clamped_power_off")
    hide(p)
    S.pose(root, "tab", 0)
    power(root, True, 2.0, 1.2, .5)
    q = plug_on(root, "001", 0.0, twist=12.0, tilt=1.5)
    R.cam_at(sc, (8, 0, -1), 62, 40, 75)
    R.shoot(sc, "h02b_001_stuck_12deg")
    hide(q)
    stops = {"A": 4.47, "B": 4.47, "C": 4.47, "D": 4.47, "E": 4.47, "F": 3.47}
    for w, d in stops.items():
        pl = plug_on(root, w, d)
        R.cam_at(sc, (4, 0, -1), 60, 30, 85)
        R.shoot(sc, f"h02b_{w}_stuck_halfway")
        hide(pl)
    sc2, root2 = build_scene()
    hide(root2)
    R.ZOFF = 0.0
    names = ["ATP", "048", "001", "A", "B", "C", "D", "E", "F", "blank"]
    for i, w in enumerate(names):
        pl = S.h02b_plug(K, which=w)
        pl.location = Vector(((i - 4.5) * 17.0 * D.MM, 0, 13.0 * D.MM))
        pl.rotation_euler = (0, math.radians(90), 0)
    pb = D.Part(K, "plinth2", "white")
    pb.box(0, 0, 100, 25, 1.6, K.white, z=.8, r=3, bevel=.3)
    R.cam_at(sc2, (0, 0, 14), 0, 8, 200, lens=35)
    R.shoot(sc2, "h02b_plug_lineup")
    for i, sd in enumerate((1, 2, 3, 4, 5)):
        pl = S.h02b_plug(K, which="blank", seed=sd)
        pl.location = Vector(((i - 2) * 17.0 * D.MM, -30 * D.MM, 13.0 * D.MM))
        pl.rotation_euler = (0, math.radians(90), 0)
    R.cam_at(sc2, (0, -30, 14), 0, 12, 120, lens=35)
    R.shoot(sc2, "h02b_plug_lineup_seeds")


def mini_group():
    sc = R.start(64)
    R.ZOFF = 0.0
    global K
    K = R.K
    for i, pat in enumerate(("round", "slots", "tri")):
        m = S.h01b_cdk20_socket(K, lod="mini", pattern=pat)
        m.location = Vector(((i - 1) * 26.0 * D.MM, 0, 4.0 * D.MM))
        if pat == "slots":
            S.pose(m, "out", 40)
        if pat == "tri":
            S.pose(m, "out", 2.5)
        S.pose(m, "piston", 1.5 * (i + 1))
    pb = D.Part(K, "plinth3", "white")
    pb.box(0, 0, 60, 24, 1.0, K.white, z=-.5, r=3, bevel=.3)
    R.cam_at(sc, (0, 0, 8), 0, 40, 105)
    R.shoot(sc, "h01b_mini_three")
    for ob in list(sc.objects):
        if ob.name.startswith("h01b_mini"):
            ob.hide_render = True
    for pat in ("round", "slots", "tri"):
        m = S.h01b_cdk20_socket(K, lod="mini", pattern=pat)
        m.location = Vector((0, 0, 4.0 * D.MM))
        S.pose(m, "piston", 3.0)
        R.cam_at(sc, (0, 0, 8), 90, 50, 58)
        R.shoot(sc, f"h01b_mini_{pat}")
        hide(m)
    import kit_parts as KP
    sc2 = R.start(64)
    R.ZOFF = 0.0
    K = R.K
    mm = S.h01b_cdk20_socket(K, lod="mini", pattern="round")
    KP.make_cell(K, mm, -66.0, 0)
    KP.make_cell(K, KP.p19_cdk20(K), 0, 0)
    KP.make_cell(K, KP.p21_lock(K), 66.0, 0)
    R.cam_at(sc2, (0, 0, 0), 0, 55, 260)
    R.shoot(sc2, "h01b_mini_in_cell_row")


SENSOR = 2.4          # 近景用微距小感光面：f/2.8 不变，景深够看清毫米级件


def close_cam(sc, tgt, az, el, dist, focus=None, width=22.0):
    c = R.cam_at(sc, tgt, az, el, dist, lens=dist * SENSOR / width, fstop=2.8, focus=focus or tgt, sensor=SENSOR)
    return c


def close_group():
    sc, root = build_scene(64)
    S.pose(root, "lid", 110)

    def shoot_close(tgt, az, el, dist, name, focus=None, width=22.0):
        close_cam(sc, tgt, az, el, dist, focus, width)
        R.shoot(sc, name, (1920, 1080))

    p = plug_on(root, "048", 0.0)
    power(root, True, 0, 1.0, 0)
    shoot_close((-3.2, 0, -1.2), 90, 62, 26, "h02b_c1_048_section_needle_tips")
    # C2：渲染专用，在下半孔桶 -U 侧壁开窗，露出卡口销和 L 槽（模型本身不改）
    barrel_low = [o for o in root.children_recursive if "barrel_lower" in o.name][0]
    wo = S.box(D.Part(K, "win_cut", "white"), "win", (0, 0, 0), (9, 3.0, 6), K.white, 0)
    wo.location = Vector((8.0 * D.MM, -6.9 * D.MM, root.location.z - 2.5 * D.MM))
    wo.parent = None
    wo.hide_render = True
    bm_ = barrel_low.modifiers.new("render_window", "BOOLEAN")
    bm_.object, bm_.operation, bm_.solver = wo, "DIFFERENCE", "EXACT"
    for ang, which, nm in ((0, "048", "000"), (12, "001", "012"), (90, "048", "090")):
        hide(p)
        p = plug_on(root, which, 0.0, twist=ang)
        shoot_close((8.0, -5.8, -1.8), 0, 22, 26, f"h02b_c2_bayonet_{nm}", focus=(8.0, -6.4, -1.8), width=18.0)
    barrel_low.modifiers.remove(bm_)
    hide(p)
    p = plug_on(root, "048", 0.0, twist=90.0)
    S.pose(root, "tab", -25)
    shoot_close((14.5, 8.0, 0), 180, 38, 26, "h02b_c3_tab_on_flange", width=18.0)
    S.pose(root, "tab", 0)
    hide(p)
    # C5 光管和光包
    power(root, True, 2.0, 1.2, .45)
    shoot_close((-7.5, 11.5, -8.0), 75, 50, 34, "h01b_c5_light_pipe_packets", width=24.0)
    # C6 三个鼓大阶段
    for nm, pis, cl in (("100", 0.0, 1.0), ("125", 2.5, 1.25), ("145", 5.0, 1.45)):
        power(root, True, pis, cl, .5)
        shoot_close((S.MECH_W, 2.0 - pis * 1.3, -3.3), 0, 40, 44, f"h01b_c6_piston_cell_{nm}", width=34.0)
    # C7 灯亮灯灭
    S.pose(root, "lid", 0)
    for nm, on in (("on", 1), ("off", 0)):
        S.pose(root, "lamp_out", on)
        shoot_close((-4.0, 0.0, 13.3), 70, 45, 22, f"h01b_c7_lamp_out_{nm}")
    S.pose(root, "lid", 110)
    for nm, on in (("on", 1), ("off", 0)):
        S.pose(root, "lamp_in", on)
        shoot_close((-3.0, 13.9, -7.35), 70, 40, 24, f"h01b_c7_lamp_in_{nm}", width=14.0)
    S.pose(root, "lamp_in", 1)
    shoot_close((-6.0, -7.0, -16.0), 90, 84, 40, "h01b_c8_back_plate", width=34.0)
    plug_on(root, "001", 0.0, tilt=1.7)
    shoot_close((6.0, -5.0, 0.0), 90, 82, 24, "h02b_c9_001_wobble", focus=(6.0, -5.0, -0.1), width=14.0)
    # C4 真假插头针尖并排
    sc4 = R.start(64)
    R.ZOFF = 0.0
    a = S.h02b_plug(R.K, which="ATP")
    b = S.h02b_plug(R.K, which="048")
    for pl, y in ((a, -7.5), (b, 7.5)):
        pl.location = Vector((0, y * D.MM, 13.0 * D.MM))
        pl.rotation_euler = (0, math.radians(90), 0)
    pb = D.Part(R.K, "plinth4", "white")
    pb.box(0, 0, 40, 30, 1.6, R.K.white, z=.8, r=3, bevel=.3)
    close_cam(sc4, (-1, 0, 29.5), 90, 66, 28, width=30.0)
    R.shoot(sc4, "h02b_c4_tip_compare", (1920, 1080))


def id_group():
    """S1/S4/S5 的像素统计：Workbench 平涂 ID 图 + 同机位 Cycles 图的亮度。"""
    import numpy as np
    import json
    sc, root = build_scene(64)
    res = {}
    cls = {"back": (1, 0, 0), "mid": (1, 0, 0), "front": (1, 0, 0)}

    def paint(lid_visible=True):
        for ob in sc.objects:
            if ob.type != "MESH":
                continue
            ob.color = (0, 0, 0, 1)
            if ob.name.startswith("h01b_cdk20_socket"):
                lay = ob.get("layer")
                p = ob
                is_lid = False
                while p.parent is not None:
                    if p.get("role") == "lid":
                        is_lid = True
                    p = p.parent
                if is_lid:
                    ob.color = (0, 1, 0, 1)
                    if not lid_visible:
                        ob.hide_render = True
                elif ob.data.materials and ob.data.materials[0] and ob.data.materials[0].name.startswith("kit_white_warm"):
                    ob.color = (1, 1, 0, 1)
                elif lay in cls:
                    ob.color = (1, 0, 0, 1)
                elif lay == "shell":
                    ob.color = (0, 0, 1, 1)
                else:
                    ob.color = (1, 0, 0, 1)

    def pix(path):
        im = bpy.data.images.load(str(path))
        a = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)
        bpy.data.images.remove(im)
        return a

    lid_objs = []
    for ob in sc.objects:
        if ob.type == "MESH" and ob.name.startswith("h01b_cdk20_socket") and not ob.hide_render:
            p = ob
            while p.parent is not None:
                if p.get("role") == "lid":
                    lid_objs.append(ob)
                    break
                p = p.parent
    paint(True)
    views = {"c10": (C10["tgt"], C10["az"], C10["el"], C10["dist"])}
    views["cmp"] = (CMP["tgt"], CMP["az"], CMP["el"], CMP["dist"])
    for a in (0, 55, 110):
        views[f"lid{a:03d}"] = ((-10, 0, 0), 65, 35, 170)
    # Cycles 图的亮度，先出 c10（开盖）
    S.pose(root, "lid", 110)
    beauties = {}
    for nm_ in ("c10", "cmp"):
        R.cam_at(sc, *views[nm_])
        R.shoot(sc, f"tmp_id_beauty_{nm_}", (1920, 1080))
        beauties[nm_] = pix(R.OUT / f"tmp_id_beauty_{nm_}.png") if not R.PREVIEW else pix(R.OUT / "tmp" / f"tmp_id_beauty_{nm_}.png")
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "OBJECT"
    sc.display.render_aa = "OFF"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0
    sc.world.use_nodes = False
    sc.world.color = (0, 0, 0)
    for nm, (tgt, az, el, dist) in views.items():
        for vis in (True, False):
            a_ = 110 if nm in ("c10", "cmp") else int(nm[3:])
            S.pose(root, "lid", a_)
            for ob in lid_objs:
                ob.hide_render = False
            paint(vis)
            R.cam_at(sc, tgt, az, el, dist)
            sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
            out = R.OUT / "tmp" / f"id_{nm}_{'lid' if vis else 'nolid'}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            sc.render.filepath = str(out)
            bpy.ops.render.render(write_still=True)
            a = pix(out)
            yel = (a[:, 0] > .9) & (a[:, 1] > .9) & (a[:, 2] < .1)
            red = ((a[:, 0] > .9) & (a[:, 1] < .1) & (a[:, 2] < .1)) | yel
            grn = (a[:, 1] > .9) & (a[:, 0] < .1) & (a[:, 2] < .1)
            blu = (a[:, 2] > .9) & (a[:, 0] < .1) & (a[:, 1] < .1)
            res[f"{nm}_{'lid' if vis else 'nolid'}"] = dict(interior=int(red.sum()), lid=int(grn.sum()), shell=int(blu.sum()), total=len(a),
                                                            interior_frac=float(red.sum() / len(a)))
            if nm in ("c10", "cmp") and vis:
                beauty = beauties[nm]
                lum = .2126 * beauty[:, 0] + .7152 * beauty[:, 1] + .0722 * beauty[:, 2]
                res[f"{nm}_S4_interior_p5_luminance"] = float(np.percentile(lum[red], 5))
                res[f"{nm}_S4_interior_mean_luminance"] = float(lum[red].mean())
                res[f"{nm}_S4_shell_mean_luminance"] = float(lum[blu].mean())
                mx = beauty[:, :3].max(1)
                res[f"{nm}_white_parts_max_channel"] = float(mx[yel].max())
                res[f"{nm}_white_parts_p99_9"] = float(np.percentile(mx[yel], 99.9))
                res[f"{nm}_white_parts_p99"] = float(np.percentile(mx[yel], 99))
                res[f"{nm}_white_parts_mean"] = float(mx[yel].mean())
                res[f"{nm}_white_parts_frac_ge_0p98"] = float((mx[yel] >= .98).mean())
                res[f"{nm}_S4_black_pixels_in_interior_frac"] = float(((lum < .02) & red).sum() / max(red.sum(), 1))
    for nm in views:
        l, n = res.get(f"{nm}_lid"), res.get(f"{nm}_nolid")
        if l and n:
            res[f"S5_{nm}_cabin_blocked_by_lid_frac"] = 1 - l["interior"] / max(n["interior"], 1)
    (R.OUT / "h01b_h02b_report_id.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("WROTE id")


if __name__ == "__main__":
    flags = R.flags
    groups = [f for f in flags if f in ("overview", "plugs", "mini", "close", "id", "compare")]
    table = {"overview": overview, "plugs": plugs_group, "mini": mini_group, "close": close_group, "id": id_group, "compare": compare}
    for g in groups or ["overview"]:
        table[g]()
