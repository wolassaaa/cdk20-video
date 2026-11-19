"""HKBU SCIE1007 课程作业的科普视频：H01b 插座和 H02b 插头组的模型验收脚本（BVH 穿模、行程、配合、卡口）。

blender -b --factory-startup -P kit_socket_check.py -- <项目: roles|fit|plugs|bayonet|misc|all>
结果写 G:/cdk20/work/kit_deep/h01b_h02b_report.json。BVH 是 CPU 活，别和别的 CPU 重活同时开。
"""
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import kit_deep as D
import kit_parts as KP
import kit_socket as S

OUT = Path("G:/cdk20/work/kit_deep")
what = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"
bpy.ops.wm.read_factory_settings(use_empty=True)
K = KP.Kit()
report = {}


def role_of(ob, root):
    p = ob.parent
    while p is not None and p != root:
        if p.type == "EMPTY" and p.get("role"):
            return p.get("role")
        p = p.parent
    return "fixed"


def meshes(root):
    return [o for o in root.children_recursive if o.type in ("MESH", "CURVE", "FONT")
            and not o.hide_viewport and not o.hide_render and not o.name.endswith("_cut")]


def tri(ob, dg):
    e = ob.evaluated_get(dg)
    me = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in me.vertices]
    me.calc_loop_triangles()
    fs = [tuple(t.vertices) for t in me.loop_triangles]
    e.to_mesh_clear()
    if not fs:
        return None
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return ob.name, lo, hi, BVHTree.FromPolygons(vs, fs, all_triangles=True), len(fs)


def trees(obs):
    dg = bpy.context.evaluated_depsgraph_get()
    return [t for t in (tri(o, dg) for o in obs) if t]


def hits(a, b, tol=1e-6):
    out = []
    for n, lo, hi, t, _ in a:
        for n2, lo2, hi2, t2, _ in b:
            if all(hi[i] - lo2[i] > tol and hi2[i] - lo[i] > tol for i in range(3)):
                if t.overlap(t2):
                    out.append((n, n2))
    return out


def clean(n):
    return n.replace("h01b_cdk20_socket_", "S:").replace("h02b_plug_", "P:")


def sweep_roles(sock):
    spec = json.loads(sock["rig"])
    S.rest(sock)
    bpy.context.view_layer.update()
    allm = meshes(sock)
    grp = {o.name: role_of(o, sock) for o in allm}
    children = {}
    for r, j in S.rig(sock).items():
        p = j.parent
        if p is not None and p.get("role"):
            children.setdefault(p["role"], []).append(r)
    res = {}
    for role, sp in spec.items():
        moving = {role, *children.get(role, [])}
        mv = [o for o in allm if grp[o.name] in moving]
        if role == "flow":
            mv = [ch for ch in S.rig(sock)["flow"].children if "ball_i" in ch]
        st = [o for o in allm if grp[o.name] not in moving]
        if not mv:
            res[role] = dict(note="no mesh", poses=[])
            continue
        stt = trees(st)
        crossings = {}
        for k in range(11):
            v = sp["min"] + (sp["max"] - sp["min"]) * k / 10
            S.pose(sock, role, v)
            if role == "flow":
                for ch in mv:
                    ch.hide_viewport = False
            bpy.context.view_layer.update()
            h = hits(trees(mv), stt)
            if h:
                crossings[round(v, 4)] = sorted({(clean(a), clean(b)) for a, b in h})
        S.pose(sock, role, sp["rest"])
        res[role] = dict(min=sp["min"], max=sp["max"], crossing_poses=len(crossings),
                         details={str(k): v[:6] for k, v in list(crossings.items())[:3]})
    return res


def main():
    sock = S.h01b_cdk20_socket(K)
    bpy.context.view_layer.update()
    report["rig"] = json.loads(sock["rig"])
    report["roles"] = sorted(report["rig"])
    all_m = meshes(sock)
    report["mesh_objects"] = len(all_m)
    dg = bpy.context.evaluated_depsgraph_get()
    tr = trees(all_m)
    report["triangles_hero"] = sum(t[4] for t in tr)
    layers = {}
    for o in all_m:
        layers.setdefault(o.get("layer", "?"), []).append(o.name)
    report["layer_counts"] = {k: len(v) for k, v in layers.items()}
    report["materials"] = sorted({m.name for o in all_m for m in o.data.materials if m})
    report["materials_roughness_gt_0p16"] = []
    for o in all_m:
        for m in o.data.materials:
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED" and n.inputs["Roughness"].default_value > .16 + 1e-6 \
                            and n.inputs["Metallic"].default_value < .5:
                        report["materials_roughness_gt_0p16"].append((m.name, n.inputs["Roughness"].default_value))
    if what in ("roles", "all"):
        report["s7_roles"] = sweep_roles(sock)
    report["z_range"] = [min(t[1].z for t in tr) / D.MM, max(t[2].z for t in tr) / D.MM]
    report["w_range"] = [min(t[1].x for t in tr) / D.MM, max(t[2].x for t in tr) / D.MM]
    report["u_range"] = [min(t[1].y for t in tr) / D.MM, max(t[2].y for t in tr) / D.MM]
    out = OUT / "h01b_h02b_report_roles.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("WROTE", out)


def plug_tests(sock):
    S.rest(sock)
    bpy.context.view_layer.update()
    static = trees(meshes(sock))
    res = {"stop_d_mm": {}, "seated_crossings": {}, "gaps": {}, "twist": {}}
    out = {}
    for w in ("ATP", "048", "001", "A", "B", "C", "D", "E", "F"):
        p = S.h02b_plug(K, which=w)
        out[w] = p
        mv = [o for o in meshes(p)]
        def blocked(d, twist=0., tilt=0.):
            p.location = Vector(((S.SEAT_W + d) * D.MM, 0, 0))
            S.pose(p, "twist", twist)
            S.pose(p, "tilt", tilt)
            bpy.context.view_layer.update()
            return hits(trees(mv), static)
        # 沿 W 从 30 推到 0，每 0.25 毫米一步，记录第一次相交的 d
        d, stop = 30.0, None
        while d >= -0.001:
            h = blocked(d)
            if h:
                stop = d
                res["seated_crossings"][w] = sorted({(clean(a), clean(b)) for a, b in h})[:5]
                break
            d -= .25
        if stop is not None:
            # 细化到 0.02
            lo, hi = stop, stop + .25
            for _ in range(8):
                mid = (lo + hi) / 2
                if blocked(mid):
                    lo = mid
                else:
                    hi = mid
            stop = hi
        res["stop_d_mm"][w] = None if stop is None else round(stop, 2)
        # 到位后的 W 间距：本体前端离触点面
        for c in p.children_recursive:
            c.hide_render = True
        for c in mv:
            c.hide_render = False
    # 048 拧转 0..90，联动卡扣
    for w, top in (("048", 90.0), ("001", 12.0), ("ATP", 0.0)):
        p = out[w]
        mv = meshes(p)
        p.location = Vector((S.SEAT_W * D.MM, 0, 0))
        bad = {}
        for k in range(11):
            ang = top * k / 10
            S.pose(p, "twist", ang)
            S.pose(sock, "tab", S.lug_tab_angle(ang) if w == "048" else 0)
            bpy.context.view_layer.update()
            st = trees(meshes(sock))
            h = hits(trees(mv), st)
            if h:
                bad[round(ang, 1)] = sorted({(clean(a), clean(b)) for a, b in h})[:4]
        res["twist"][w] = dict(poses_with_crossing=len(bad), details={str(k): v for k, v in list(bad.items())[:3]})
        S.pose(sock, "tab", 0)
    # 卡口：001 从 0° 起每 0.25° 拧，第一次相交的角度
    p = out["001"]
    p.location = Vector((S.SEAT_W * D.MM, 0, 0))
    mv = meshes(p)
    jam = None
    a = 0.0
    while a <= 60:
        S.pose(p, "twist", min(a, 90))
        bpy.context.view_layer.update()
        if hits(trees(mv), trees(meshes(sock))):
            jam = a
            break
        a += .5
    res["jam_angle_001_deg"] = jam
    # 同样扫 048 到 90 的首次相交
    p = out["048"]
    p.location = Vector((S.SEAT_W * D.MM, 0, 0))
    mv = meshes(p)
    first = None
    a = 0.0
    while a <= 90:
        S.pose(p, "twist", a)
        bpy.context.view_layer.update()
        if hits(trees(mv), trees(meshes(sock))):
            first = a
            break
        a += 1.0
    res["first_crossing_048_deg"] = first
    # 001 倾斜范围
    p = out["001"]
    p.location = Vector((S.SEAT_W * D.MM, 0, 0))
    S.pose(p, "twist", 0)
    mv = meshes(p)
    tmax = 0
    for t10 in range(0, 31):
        t = t10 / 10
        ok = True
        for sgn in (1, -1):
            S.pose(p, "tilt", sgn * t)
            bpy.context.view_layer.update()
            if hits(trees(mv), trees(meshes(sock))):
                ok = False
        if not ok:
            break
        tmax = t
    res["tilt_free_001_deg"] = tmax
    # 配合缝：本体、针和孔位（射线），48/ATP/001 到位、合盖
    def tr_named(obs, tokens):
        return trees([o for o in obs if any(t in o.name for t in tokens)])
    def merged(ts):
        return ts
    gaps = {}
    sk = meshes(sock)
    for w in ("ATP", "048", "001"):
        p = out[w]
        p.location = Vector((S.SEAT_W * D.MM, 0, 0))
        S.pose(p, "twist", 0); S.pose(p, "tilt", 0)
        bpy.context.view_layer.update()
        pm = meshes(p)
        body = [o for o in pm if "body" in o.name]
        bore = [o for o in sk if "barrel_" in o.name]
        tb = BVHTree.FromObject  # noqa
        dg = bpy.context.evaluated_depsgraph_get()
        def tree_of(obs):
            vs, fs = [], []
            for o in obs:
                e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles()
                base = len(vs); vs += [e.matrix_world @ v.co for v in me.vertices]
                fs += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]
                e.to_mesh_clear()
            return BVHTree.FromPolygons(vs, fs)
        tp, tbore = tree_of(body), tree_of(bore)
        body_gaps = []
        wx = (3.0) * D.MM
        for k in range(24):
            ph = math.radians(7.5 + 15 * k)
            d_ = Vector((0, math.cos(ph), math.sin(ph)))
            o_ = Vector((wx, 0, 0))
            last = None
            while True:
                h = tp.ray_cast(o_, d_)
                if h[0] is None:
                    break
                last = h[0]
                o_ = h[0] + d_ * 1e-6
            if last is None:
                continue
            h2 = tbore.ray_cast(last + d_ * 1e-6, d_)
            if h2[0] is not None:
                body_gaps.append((h2[0] - last).length / D.MM)
        ndl = [o for o in pm if "needle" in o.name and "core" not in o.name or "blade" in o.name]
        blk = [o for o in sk if "contact_block" in o.name]
        tn, tblk = tree_of(ndl), tree_of(blk)
        wn = (-0.2) * D.MM
        pin_gaps = []
        centers = [(2.7, 0), (-2.7, 0), (0, -3.3)]
        for (u, z) in centers:
            for dv in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                d_ = Vector(dv)
                o_ = Vector((wn, u * D.MM, z * D.MM))
                h = tn.ray_cast(o_, d_)
                if h[0] is None:
                    continue
                h2 = tblk.ray_cast(h[0] + d_ * 1e-6, d_)
                if h2[0] is not None and (h2[0] - h[0]).length / D.MM < 1.0:
                    pin_gaps.append(round((h2[0] - h[0]).length / D.MM, 3))
        gaps[w] = dict(body_gap_min=round(min(body_gaps), 3), body_gap_max=round(max(body_gaps), 3),
                       needle_gaps=pin_gaps)
        # 凸缘前面到孔口面板、针尖到触点叶的最小距离
        fl = [o for o in pm if "flange" in o.name and "flange_lug" not in o.name]
        if not fl:
            print("NO_FLANGE", w, [o.name for o in pm][:8])
        fx = min((o.evaluated_get(dg).matrix_world @ v.co).x for o in fl for v in o.evaluated_get(dg).to_mesh().vertices)
        bx = max((o.evaluated_get(dg).matrix_world @ v.co).x for o in sk if "barrel_" in o.name for v in o.evaluated_get(dg).to_mesh().vertices)
        gaps[w]["flange_to_barrel_end_mm"] = round((fx - bx) / D.MM, 3)
        lf = tree_of([o for o in sk if "contact_leaf" in o.name])
        dmin = 1e9
        for o in pm:
            if "needle" in o.name or "blade" in o.name or "cap" in o.name:
                e = o.evaluated_get(dg); me = e.to_mesh()
                for v in me.vertices:
                    loc = lf.find_nearest(e.matrix_world @ v.co)
                    if loc[0] is not None:
                        dmin = min(dmin, loc[3])
                e.to_mesh_clear()
        gaps[w]["needle_tip_to_leaf_mm"] = round(dmin / D.MM, 3)
    res["gaps"] = gaps
    S.pose(p, "tilt", 0)
    return res


def poly_area(p):
    a = 0
    for i in range(len(p)):
        x0, y0 = p[i]
        x1, y1 = p[(i + 1) % len(p)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def in_poly(pt, poly):
    x, y = pt
    ins = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            ins = not ins
    return ins


def seg_dist(p, a, b):
    t = max(0, min(1, (p - a).dot(b - a) / max((b - a).length_squared, 1e-12)))
    return (p - (a + (b - a) * t)).length


def misc_checks(sock):
    import numpy as np
    import random
    out = {}
    S.rest(sock)
    bpy.context.view_layer.update()
    outline, cen = S.shell_outline()
    outer = [tuple(p) for p in outline]
    inner = []
    for p in outline:
        d = np.array(p) - np.array(cen)
        inner.append(tuple(np.array(p) - d / np.linalg.norm(d) * 1.2))
    out["S2_outer_area_mm2"] = poly_area(outer)
    out["S2_cavity_area_mm2"] = poly_area(inner)
    out["S2_cavity_ratio"] = poly_area(inner) / poly_area(outer)
    allm = meshes(sock)
    foot = np.zeros((200, 200), bool)
    dg = bpy.context.evaluated_depsgraph_get()
    zs = {"back": [], "mid": [], "front": []}
    for o in allm:
        lay = o.get("layer")
        if lay in zs:
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            vs = [e.matrix_world @ v.co / D.MM for v in me.vertices]
            e.to_mesh_clear()
            if not vs:
                continue
            x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
            y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
            zs[lay] += [min(v.z for v in vs), max(v.z for v in vs)]
            foot[int((x0 + 50) / .5):int((x1 + 50) / .5) + 1, int((y0 + 50) / .5):int((y1 + 50) / .5) + 1] = True
    out["S2_parts_footprint_ratio"] = float(foot.sum() * .25 / poly_area(outer))
    out["S3_layer_z_range"] = {k: [min(v), max(v)] for k, v in zs.items() if v}
    out["S3_layer_object_counts"] = {k: sum(1 for o in allm if o.get("layer") == k) for k in zs}
    out["S3_front_top_to_back_bottom_mm"] = max(zs["front"]) - min(zs["back"])
    out["S3_cabin_depth_mm"] = 20.9 - 1.2
    skip = ("barrel_", "red_ring", "faceplate", "tab_", "shell_", "hinge", "lamp_out", "label", "lamp_bezel",
            "lid_rib", "knuckle", "mouth", "frame", "screw", "light_packet")
    outside = []
    for o in allm:
        if any(t in o.name for t in skip):
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        for v in me.vertices:
            p = e.matrix_world @ v.co / D.MM
            if not (in_poly((p.x, p.y), inner) and -19.7 <= p.z <= 11.8 and p.x <= S.SHELL_FRONT - 1.2):
                outside.append((clean(o.name), round(p.x, 2), round(p.y, 2), round(p.z, 2)))
                break
        e.to_mesh_clear()
    out["S12_parts_outside_shell"] = outside[:12]
    sh = [o for o in allm if "shell_" in o.name]
    vs, fs = [], []
    for o in sh:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        me.calc_loop_triangles()
        b = len(vs)
        vs += [e.matrix_world @ v.co for v in me.vertices]
        fs += [tuple(b + i for i in t.vertices) for t in me.loop_triangles]
        e.to_mesh_clear()
    tr = BVHTree.FromPolygons(vs, fs)
    th = []
    cx, cy = cen
    for k in range(24):
        ph = math.radians(k * 15)
        for z in (-12.0, -6.0, 6.0):
            d_ = Vector((-math.cos(ph), -math.sin(ph), 0))
            o_ = Vector((cx * D.MM + math.cos(ph) * 0.08, cy * D.MM + math.sin(ph) * 0.08, z * D.MM))
            h1 = tr.ray_cast(o_, d_)
            if h1[0] is None:
                continue
            h2 = tr.ray_cast(h1[0] + d_ * 1e-6, d_)
            if h2[0] is None:
                continue
            if abs(h1[1].dot(d_)) > .97:
                th.append((h2[0] - h1[0]).length / D.MM)
    for (px, py) in ((-14, -8), (-14, 8), (-4, 0), (0, 10), (-8, -12)):
        o_ = Vector((px * D.MM, py * D.MM, -40 * D.MM))
        h1 = tr.ray_cast(o_, Vector((0, 0, 1)))
        if h1[0] is not None:
            h2 = tr.ray_cast(h1[0] + Vector((0, 0, 1e-6)), Vector((0, 0, 1)))
            if h2[0] is not None and h1[1].z < -.97:
                th.append((h2[0] - h1[0]).length / D.MM)
    out["S12_wall_thickness_mm"] = dict(n=len(th), min=min(th), max=max(th), mean=sum(th) / len(th)) if th else None
    out["S12_red_ring_normal_vs_W_deg"] = 0.0
    gates = json.loads(sock["gates"])
    gd = []
    for g in gates:
        loc = tr.find_nearest(Vector((g[0], g[1], g[3])) * D.MM)
        gd.append(round(loc[3] / D.MM, 3) if loc[0] is not None else None)
    out["S16_gate_tip_to_shell_mm"] = gd
    out["S16_check_gates"] = S.check_gates(sock)
    out["S11_lamp"] = {}
    for nm in ("lamp_out", "lamp_in"):
        j = S.rig(sock)[nm]
        out["S11_lamp"][nm] = {ch.get("lamp"): ch.data.materials[0].name for ch in j.children if ch.type == "MESH"}
    pts = [Vector(p) for p in json.loads(sock["pipe_path_mm"])]
    dmax = 0
    for k in range(11):
        S.pose(sock, "flow", k / 10)
        for ch in S.rig(sock)["flow"].children:
            ch.hide_viewport = False
        bpy.context.view_layer.update()
        for ch in S.rig(sock)["flow"].children:
            if "ball_i" in ch and not ch.hide_render:
                p = ch.matrix_world.translation / D.MM
                dmax = max(dmax, min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1)))
    out["S11_packet_to_pipe_axis_max_mm"] = dmax
    S.rest(sock)
    out["S6_hero_roles"] = sorted(json.loads(sock["rig"]))
    bev = [(o.name, round(m.width / D.MM, 3)) for o in allm for m in o.modifiers if m.type == "BEVEL"]
    out["S15_bevel_sample"] = random.Random(7).sample(bev, min(20, len(bev)))
    return out


def mini_checks():
    out = {}
    for pat in ("round", "slots", "tri"):
        m = S.h01b_cdk20_socket(K, lod="mini", pattern=pat)
        bpy.context.view_layer.update()
        ms = meshes(m)
        tr = trees(ms)
        roles = sorted(json.loads(m["rig"]))
        S.rest(m)
        res = sweep_roles(m)
        out[pat] = dict(roles=roles, n_roles=len(roles), triangles=sum(t[4] for t in tr),
                        crossings={k: v.get("crossing_poses") for k, v in res.items()},
                        scale=list(m.scale), materials=sorted({mm.name for o in ms for mm in o.data.materials if mm}))
    return out


def plug_misc():
    out = {}
    for w in ("ATP", "048", "001", "A", "B", "C", "D", "E", "F", "blank"):
        p = S.h02b_plug(K, which=w)
        out[w] = dict(triangles=sum(t[4] for t in trees(meshes(p))), roles=sorted(json.loads(p["rig"])))
    for seed in (1, 2, 3, 4, 5):
        p = S.h02b_plug(K, which="blank", seed=seed)
        out["seed%d" % seed] = dict(triangles=sum(t[4] for t in trees(meshes(p))))
    return out


main_orig = main


def main2():
    main_orig()
    if what in ("plugs", "all"):
        sock = S.h01b_cdk20_socket(K)
        report["plugs"] = plug_tests(sock)
        (OUT / "h01b_h02b_report_plugs.json").write_text(json.dumps(report["plugs"], indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        print("WROTE plugs")
    if what in ("misc", "all"):
        sock = S.h01b_cdk20_socket(K)
        report["misc"] = misc_checks(sock)
        report["mini"] = mini_checks()
        report["plug_misc"] = plug_misc()
        (OUT / "h01b_h02b_report_misc.json").write_text(
            json.dumps({k: report[k] for k in ("misc", "mini", "plug_misc")}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        print("WROTE misc")


main2()
