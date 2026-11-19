"""HKBU SCIE1007 课程作业的科普视频：P0 预览验收，输出在 G:。"""
import itertools
import json
import os
import random
import sys
from pathlib import Path
import math
import time

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import kit_deep as D
import kit_parts_hd as KP

out = Path("G:/cdk20/work/kit_deep")
name = sys.argv[sys.argv.index("--")+1]
opts = sys.argv[sys.argv.index("--")+2:]
sc = KP.scene_base(64)
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.image_settings.file_format = "PNG"
K = KP.Kit()
f = getattr(D, name)
root = f(K)
bpy.context.view_layer.update()
variant = {}

def collect(r):
    dg = bpy.context.evaluated_depsgraph_get()
    groups = {}
    for o in r.children_recursive:
        if o.hide_render or o.type not in ("MESH", "CURVE", "FONT"):
            continue
        p = o
        while p.parent != r:
            p = p.parent
        key = p.get("role", "fixed")
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        vs = [ev.matrix_world @ a.co / D.MM for a in me.vertices]
        polygons = [tuple(t.vertices) for t in me.loop_triangles]
        mat = [m.name for m in me.materials if m]
        ev.to_mesh_clear()
        if not polygons:
            continue
        groups.setdefault(key, []).append((o, vs, polygons, mat))
    return groups

def bbox_main(groups):
    vs = [p for g in groups.values() for o, vs, f, m in g for p in vs]
    lo = [round(min(p[i] for p in vs), 4) for i in range(3)]
    hi = [round(max(p[i] for p in vs), 4) for i in range(3)]
    return [lo, hi]

def record(r):
    bpy.context.view_layer.update()
    groups = collect(r)
    n = sum(len(f) for g in groups.values() for o, vs, f, m in g)
    return {"bounds_mm": bbox_main(groups), "triangles": n,
            "materials": sorted({m for g in groups.values() for _, _, _, mats in g for m in mats}),
            "roles": list(D.rig(r))}

data = record(root)
groups = collect(root)
rj = D.rig(root)
rig = json.loads(root.get("rig", "{}"))
data["rig"] = rig
data["properties"] = {k: root.get(k) for k in ("seat_to_surface_mm", "source_triangles", "preview_status", "tooth_profile", "turn_limit_deg", "bow_form") if k in root}
if name == "h01_cdk20_lockworks":
    probe = D.Part(K, "h01_source_probe", "blue")
    exterior, seat, w = D._shell_source(probe)
    bpy.context.view_layer.update()
    ex = collect(probe.root)
    lo, hi = bbox_main(ex)
    pts_span = math.dist(lo, hi)
    data["r1_h01_envelope_check"] = {
        "closed_source_bounds_mm": [lo, hi],
        "closed_source_max_possible_straight_span_mm": pts_span,
        "strip_12_marks_minimum_mm": 11 * 3.3 + 2,
        "strip_12_marks_plus_40_travel_minimum_mm": 11 * 3.3 + 2 + 40,
        "existing_20mm_span_plus_40_travel_mm": 20 + 40,
        "seat_relative_mouth_w_mm": root["seat_to_surface_mm"],
        "existing_sleeve_w_max_mm": 5.0,
        "existing_sleeve_axial_overrun_mm": 5.0 - root["seat_to_surface_mm"],
    }
    for ob in probe.root.children_recursive:
        ob.hide_render = True
benches = [(o.name, round(m.width / D.MM, 3)) for g in groups.values() for o, _, _, _ in g
           for m in o.modifiers if m.type == "BEVEL"]
data["bevel_sample_modifiers_not_edge_check"] = random.Random(42).sample(benches, min(20, len(benches)))

def geom(g):
    cache = {}
    for key, group in g.items():
        cache[key] = []
        for o, vs, faces, mats in group:
            local = [(o.matrix_world.inverted() @ (p * D.MM)) / D.MM for p in vs]
            cache[key].append((o, local, faces))
    return cache

def trees(items):
    pieces = []
    for o, local, faces in items:
        verts = [o.matrix_world @ (v * D.MM) / D.MM for v in local]
        lo = [min(p[i] for p in verts) for i in range(3)]
        hi = [max(p[i] for p in verts) for i in range(3)]
        pieces.append((o.name, lo, hi, BVHTree.FromPolygons(verts, faces, all_triangles=True)))
    return pieces

def hits(a, b):
    for n, lo, hi, t in a:
        for n2, lo2, hi2, t2 in b:
            if all(hi[i]-lo2[i]>1e-4 and hi2[i]-lo[i]>1e-4 for i in range(3)):
                if t.overlap(t2):
                    yield [n, n2]

if rj and "quick" not in opts:
    D.rest(root)
    bpy.context.view_layer.update()
    cache = geom(collect(root))
    static = {k: trees(items) for k, items in cache.items()}
    data["unfiltered_bvh_surface_crossings"] = {}
    data["endpoint_actual"] = {}
    for role, spec in rig.items():
        vis = cache.get(role, [])
        obstacles = [(k, a) for k, a in static.items() if k != role]
        report = []
        ends = []
        for step in range(11):
            value = spec["min"] + (spec["max"] - spec["min"]) * step / 10
            D.pose(root, role, value)
            bpy.context.view_layer.update()
            if step in (0, 10):
                joint = rj[role]
                actual = (math.degrees(joint.rotation_euler.x) if spec["type"] == "rot"
                          else joint.location.z/D.MM if spec["type"] == "loc"
                          else list(joint.location / D.MM) if spec["type"] == "path" else None)
                ends.append(actual)
            t = trees(vis)
            pairs = {k: pairs for k, old in obstacles if (pairs := list(hits(t, old)))}
            if pairs:
                report.append(dict(pose=round(value, 5), pairs=pairs))
        data["unfiltered_bvh_surface_crossings"][role] = report
        data["endpoint_actual"][role] = ends
        D.pose(root, role, spec["rest"])
    bpy.context.view_layer.update()
    D.rest(root)

if name == "h03_loop_track" and "quick" not in opts:
    dg = bpy.context.evaluated_depsgraph_get()
    def span(obj, axes):
        ev = obj.evaluated_get(dg)
        mesh = ev.to_mesh()
        sizes = [round((max(v.co[i] for v in mesh.vertices)-min(v.co[i] for v in mesh.vertices))
                       *obj.scale[i]/D.MM, 4) for i in axes]
        ev.to_mesh_clear()
        return sizes
    base = next(o for o in root.children if "_engraved_base" in o.name)
    tree = D._tree(base)
    def floor_z(x,y):
        return round(tree.ray_cast(D._mm((x,y,9)),Vector((0,0,-1)))[0].z/D.MM,4)
    data["r1_station_plates_mm"] = {o["station"]:span(o,(0,1)) for o in root.children if "station" in o}
    data["r1_station_glyph_height_mm"] = {o["station_label"]:span(o,(1,))[0]
                                           for o in root.children if "station_label" in o}
    data["r1_grid_cut_mm"] = [floor_z(12.8,-8.8),floor_z(12,-8.8)]
    D.rest(root)
    bpy.context.view_layer.update()
    cache = geom(collect(root))
    land = [(key, trees(value)) for key, value in cache.items() if key.startswith(("coin_s", "clock_s"))]
    data["landing_pair_crossings"] = [(a,b) for (a,ta),(b,tb) in itertools.combinations(land,2)
                                        if any(hits(ta,tb))]
    obst = [i for k, v in cache.items() if k != "car" for i in trees(v)]
    data["car_193_crossing_samples"] = []
    for i in range(193):
        D.pose(root,"car",i/192)
        bpy.context.view_layer.update()
        results = list(hits(trees(cache["car"]),obst))
        if results:
            data["car_193_crossing_samples"].append([i,results])
    D.rest(root)
    D.pose(root,"press",-2.5)
    carried = D.h02_key(K,which="blank",scale=.35)
    carried.rotation_euler.z = math.pi
    # 柄在冲头下限中心，键坯以小车承台顶面作独立检具，不是动画联动。
    carried.location = D._mm((-3.5*.35,-10,5.835+.8*.35))
    bpy.context.view_layer.update()
    keymesh = collect(carried)
    pressmesh = collect(root)["press"]
    press_bottom = min(p.z for _, vs, _, _ in pressmesh for p in vs)
    key_top = max(p.z for g in keymesh.values() for _, vs, _, _ in g for p in vs
                  if abs(p.x)<.8 and abs(p.y+10)<.8)
    data["press_to_carried_blank_mm"] = round(press_bottom-key_top,6)
    for ob in carried.children_recursive:
        ob.hide_render = True
    D.rest(root)
if name == "h06_pin_lock":
    complete = f(K,cut=False)
    data["uncut"] = record(complete)
    for ob in complete.children_recursive:
        ob.hide_render = True
if name == "h04_chem42_chip":
    plate = next(o for o in root.children if o.get("role")=="screen")
    data["screen_uv"] = [list(u.uv) for u in plate.data.uv_layers.active.data]
    data["count_of_loop_cars"] = sum(r.startswith("loop_") for r in rig)
    data["layout_check_mm"] = {"mini_footprint":[9.,5.4], "pitch":[5.6,3.4],
                             "neighbor_overlap":[3.4,2.0], "grid_slots":36,
                             "empty_center":4,"remaining_slots":32}
if name in ("h01_cdk20_lockworks", "h03_loop_track"):
    probe = f(K, lod="mini")
    data["mini"] = record(probe)
    data["mini"]["rig"] = json.loads(probe["rig"])
    for obj in [probe] + probe.children_recursive:
        obj.hide_render = True
if name == "h02_key":
    # 射线量成品（未挂框、scale=1），不是布尔刀具公称值。
    def face_z(obj, x, y, side):
        hit = D._tree(obj).ray_cast(D._mm((x,y,side*3)), Vector((0,0,-side)))[0]
        return None if hit is None else round(hit.z/D.MM, 4)
    handle = next(o for o in root.children if "__knurled_bow" in o.name or "_knurled_bow" in o.name)
    blade = next(o for o in root.children if "_bevelled_blade" in o.name)
    data["r1_key_cut_surfaces_mm"] = {
        "bow_outer_face": face_z(handle,-6.2,0,1),
        "bow_ring_floor": face_z(handle,-5.60,0,1),
        "blade_faces": [face_z(blade,4.0,.65,z) for z in (1,-1)],
        "blade_guide_floors": [face_z(blade,4.0,.41,z) for z in (1,-1)],
        "blade_bevel_nominal": .20,
    }
    keys = [f(K, seed=i) for i in range(50)]
    data["seed_unique_count"] = len({(tuple(o["tooth_profile"]), o["bow_form"]) for o in keys})
    data["seed_geometry_profile_unique_count"] = len({(tuple(o["tooth_profile_modelled"]), o["bow_form"]) for o in keys})
    for kk in keys + [f(K, which="001"), f(K, which="blank"), f(K, scale=1.3, spiky=True)]:
        if kk not in keys:
            data.setdefault("variants", []).append(record(kk))
        for o in kk.children_recursive:
            o.hide_render = True
if name == "h06_pin_lock":
    for preset in ("other_a", "other_b"):
        kk = f(K, preset=preset)
        variant[preset] = record(kk)
        for o in kk.children_recursive:
            o.hide_render = True
    # 用钥匙实网格向下投射各销中心；记录在该截面接触时预测的分界误差。
    def key_contact(origin, w, u, v, scale, which):
        key = D.h02_key(K, which=which, scale=scale)
        rot = Matrix((-w,-u,-v)).transposed()
        key.rotation_euler = rot.to_euler()
        key.location = (origin + key["insertion_offset_u_mm"]*u - rot@Vector((6.5*scale,0,0)))*D.MM
        bpy.context.view_layer.update()
        kv, kf = [], []
        for group in collect(key).values():
            for _, verts, tris, _ in group:
                kf.extend(tuple(len(kv)+i for i in tr) for tr in tris)
                kv.extend(verts)
        tree = BVHTree.FromPolygons(kv,kf,all_triangles=True)
        readings = []
        for i in range(5):
            q = origin + (.5+i)*scale*w
            cr = tree.ray_cast(q + 4*u,-u,8)[0]
            readings.append(None if cr is None else round((cr-q).dot(u),5))
        for ob in key.children_recursive:
            ob.hide_render = True
        return readings

    w,u,v = map(Vector, ((0,-1,0),(0,0,1),(1,0,0)))
    heights = key_contact(Vector((0,-1.5,-.55)),w,u,v,1.3,"048")
    def seams(readings, lengths, radius):
        return [None if val is None else round(val + length - radius,4)
                for val, length in zip(readings,lengths)]
    data["seam_errors_from_key_raycast_mm"] = {
        preset: seams(heights, lengths, 2.3*1.3) for preset,lengths in D._LOCK_PRESETS.items()}
    a = D.Part(K,"h01_key_reference","blue")
    src,center,w = D._shell_source(a)
    u = (Vector((0,0,1))-w.z*w).normalized()
    v = u.cross(w)
    for ob in a.root.children_recursive:
        ob.hide_render = True
    data["h01_seam_errors_from_key_raycast_mm"] = {
        n: seams(key_contact(center,w,u,v,1.,n),D._PIN_LENGTHS,2.3)
        for n in ("048","001")}
    data["presets"] = variant

board = KP.link(bpy.data.objects.new("check_board", None))
cell = KP.make_cell(K, root, -33, 0, 30, name="z1_c0_r0")
cell.parent = board
old_name = {"h01_cdk20_lockworks":"p19_cdk20", "h02_key":"p22_key", "h06_pin_lock":"p21_lock",
            "h03_loop_track":"p20_pocket", "h04_chem42_chip":"p13_chip"}[name]
old = getattr(KP, old_name)(K)
oldcell = KP.make_cell(K, old, 33, 0, 30, name="z1_c1_r0")
oldcell.parent = board
bpy.context.view_layer.update()
data["bad_gates"] = KP.check_gates(board)
data["compare"] = old_name

def save():
    (out / (name+"_report_r1.json")).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=list), encoding="utf-8")

save()
if "quick" in opts or "no_render" in opts:
    print("P0_DONE", name, data["bounds_mm"], data["triangles"], data["bad_gates"], flush=True)
    sys.exit(0)

# 姿态图共用灯；有暂停标记时，不开下一张图。
def focus_camera(cam, suffix):
    # 相机中央射线击中可见主体的实网格。把测得的表面点设为对焦空物体原点；
    # 镜头与感光宽度按同比缩短，保住构图，同时压低宏观近景的散焦量。
    gs = collect(root)
    if suffix == "press_fit":
        gs.update({f"key_{k}": v for k,v in collect(carried).items()})
    vs, fs = [], []
    for group in gs.values():
        for _, vertices, faces, _ in group:
            fs.extend(tuple(i+len(vs) for i in f) for f in faces)
            vs.extend(v * D.MM for v in vertices)
    tree = BVHTree.FromPolygons(vs, fs, all_triangles=True)
    bpy.context.view_layer.update()
    origin = cam.matrix_world.translation.copy()
    axis = cam.matrix_world.to_3x3() @ Vector((0,0,-1))
    hit = tree.ray_cast(origin, axis)[0]
    if hit is None:
        hits2 = [h for dx in (-.18,-.09,0,.09,.18) for dy in (-.14,-.07,0,.07,.14)
                 if (h := tree.ray_cast(origin,cam.matrix_world.to_3x3() @
                     Vector((dx,dy,-1)).normalized())[0]) is not None]
        if not hits2:
            raise RuntimeError(f"{suffix}: no subject surface in focus range")
        hit = min(hits2,key=lambda v:(v-origin).normalized().angle(axis))
    # 正好对着命中的点，距离和轴向深度一致。
    cam.rotation_euler = (hit-origin).to_track_quat("-Z","Y").to_euler()
    empty = KP.link(bpy.data.objects.new("focus_surface_"+suffix,None))
    empty.location = hit
    cam.data.dof.focus_object = empty
    cam.data.dof.focus_distance = (hit-origin).length
    cam.data.dof.aperture_fstop = 8
    # 宽幅采集仅渲染中央有效视窗；构图不变，但有效光圈直径更小。
    # 这使毫米级零件的前后缘仍能在实打实的 f/8 景深内。
    lens0 = cam.data.lens
    effective = max(1., lens0/36.)
    crop = max(1,int(effective))
    cam.data.sensor_width = 1.0
    cam.data.lens = effective/crop
    sc.render.resolution_x, sc.render.resolution_y = 1600*crop, 900*crop
    sc.render.use_border = sc.render.use_crop_to_border = crop > 1
    lo_crop, hi_crop = (.5-.5/crop)+1e-7, (.5+.5/crop)+1e-7
    sc.render.border_min_x = sc.render.border_min_y = lo_crop
    sc.render.border_max_x = sc.render.border_max_y = min(1,hi_crop)
    bpy.context.view_layer.update()
    fr = [Vector((v.x/crop,v.y/crop,v.z))
          for v in cam.data.view_frame(scene=sc)]
    lo = [min(x[i] for x in fr) for i in (0,1)]
    hi = [max(x[i] for x in fr) for i in (0,1)]
    rays, depths = 0, []
    for j in range(45):
        for i in range(80):
            dr = Vector((lo[0]+(hi[0]-lo[0])*(i+.5)/80,
                         lo[1]+(hi[1]-lo[1])*(j+.5)/45, fr[0].z))
            w = (cam.matrix_world.to_3x3() @ dr).normalized()
            found = tree.ray_cast(origin,w)[0]
            rays += 1
            if found is not None:
                depths.append((found-origin).dot((hit-origin).normalized()))
    f = cam.data.lens/1000
    sensor = cam.data.sensor_width/1000
    d0 = (hit-origin).length
    # 薄透镜的采样最大散焦直径，报告中另作肉眼检查。
    coc = max((f*f*abs(d-d0)/(8*d*(d0-f))*1600*crop/sensor for d in depths), default=None)
    data.setdefault("detail_optics", {})[suffix] = dict(
        fstop=8, lens_mm=cam.data.lens, sensor_mm=cam.data.sensor_width,
        focus_mm=d0/D.MM, focus_point_mm=list(hit/D.MM),
        subject_fraction=len(depths)/rays, samples=rays, blur_diameter_px=coc, crop=crop)


def pic(suffix, target, dist, lens=50, fstop=None, angle=35, az=-25):
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.use_border = sc.render.use_crop_to_border = False
    qdir = Path(__file__).resolve().parents[2] / "_env" / "queue"
    while any((qdir/m).exists() for m in ("GPU_HOLD", "GPU_PAUSED")):
        print(f"{name}: waiting for GPU hold before {suffix}", flush=True)
        time.sleep(12)
    cam = KP.camera(sc, target, dist, angle, az, lens=lens, fstop=fstop)
    cam.data.clip_start = .001
    if fstop is not None:
        focus_camera(cam, suffix)
    KP.render(sc, str(out/(name+"_"+suffix+"_r1.png")), 100)
    data.setdefault("renders", []).append(suffix)
    save()

KP.backdrop()
KP.lights(0, 0, 1)

def plinth(label, x, y, w, h, z):
    pp = D.Part(K,label,"white")
    bpy.data.objects["sweep"].location.z = (z-1.61)*D.MM
    return pp.box(x, y, w/2,h/2,1.6,K.white,z=z-.8,r=2,bevel=.24)

def minimum_z(r):
    bpy.context.view_layer.update()
    return bbox_main(collect(r))[0][2]
# V12：只在对照帧显示格框。保持 close / open 同一机位。
for role in ("shell", "lid"):
    if role in rj:
        D.pose(root, role, 0)
if name == "h01_cdk20_lockworks":
    D.pose(root, "bead", 0)
plinth("compare_base",0,0,127,42,min(minimum_z(root),minimum_z(old)))
pic("compare", (0, 0, .031), .225)
for o in tuple(bpy.context.scene.objects):
    if o.name.startswith("compare_base"):
        o.hide_render = True
for c in (cell, oldcell):
    for o in c.children:
        if o != root:
            o.hide_render = True
            for desc in o.children_recursive:
                desc.hide_render = True
cell.location.x = 0
plinth("sheet_base",0,0,68 if name=="h01_cdk20_lockworks" else 56,
       68 if name in ("h01_cdk20_lockworks","h04_chem42_chip") else 36,minimum_z(root))
if name == "h06_pin_lock":
    # 下露的外套保留净空，锁体两侧分别落到实物托座上。
    perch = D.Part(K,"lock_perch","white")
    for x in (-6,6):
        perch.box(x,0,2.2,6.2,1.1,K.white,z=25.45,r=.32,bevel=.12)
box = data["bounds_mm"]
cx, cy, cz = [(a+b)/2*D.MM for a,b in zip(*box)]
t = (cx, cy, cz+.030)
dist = max(.028, 2.1*max((b-a)*D.MM for a,b in zip(*box)))
if name in ("h01_cdk20_lockworks", "h06_pin_lock"):
    dist *= 1.35
pic("closed", t, dist)
for role in ("shell", "lid"):
    if role in rj:
        D.pose(root, role, rig[role]["max"])
if any(k in rj for k in ("shell", "lid")):
    pic("open", t, dist)
if name == "h04_chem42_chip":
    for i, digit in enumerate((8,9,1,8)):
        D.pose(root, f"odo_{i}", 36*digit)
    bpy.context.view_layer.update()
    data["odo_top_reading"] = "".join(
        max((o for o in rj[f"odo_{i}"].children if o.type=="FONT"),
            key=lambda o: (o.matrix_world.to_3x3()@Vector((0,0,1))).z).data.body
        for i in range(4))
    pic("odo8918", (.0191, 0, .0332), .027, lens=74, fstop=8, angle=62, az=88)
    pic("top", (0,0,.034), .11, angle=90, az=0)
    sample = f(K,screen_seq=str(out/"tmp"/"screen_uv_test.png"))
    sample.location.z = .03
    D.pose(sample,"lid",120)
    for ob in root.children_recursive:
        if not ob.hide_viewport:
            ob.hide_render = True
    pic("screen_uv", (0,0,.034), .10, angle=90, az=0)
    for ob in sample.children_recursive:
        ob.hide_render = True
    for ob in root.children_recursive:
        if not ob.hide_viewport:
            ob.hide_render = False
if name == "h02_key":
    trio = [f(K,which="001"), f(K,which="blank"), f(K,seed=31,spiky=True)]
    root.hide_render = False
    for ob in root.children_recursive:
        if not ob.hide_viewport:
            ob.hide_render = True
    for i, item in enumerate(trio):
        item.location = D._mm((0,(i-1)*9.0,30))
    pic("variants", (0,0,.03), .070, lens=49, angle=77, az=0)
    for item in trio:
        for ob in item.children_recursive:
            ob.hide_render = True
    for ob in root.children_recursive:
        if not ob.hide_viewport:
            ob.hide_render = False
if name == "h03_loop_track":
    pic("station_labels", (0,0,.0345), .080, lens=48, angle=87, az=1)
    D.pose(root, "press", -2.5)
    D.pose(root, "blank_up", 3)
    D.pose(root, "car", .33)
if name == "h06_pin_lock":
    D.pose(root, "shackle", 4)
if name == "h01_cdk20_lockworks":
    D.pose(root, "arm", -32)
    D.pose(root, "latch", -25)
detail = {
    "h01_cdk20_lockworks": (t,.029,52,38,-12),
    "h02_key": ((-.0035,-.0023,.0307),.028,161,87,0),
    "h03_loop_track": ((.0092,-.0035,.0365),.028,105,58,160),
    "h06_pin_lock": ((.0005,-.0052,.0340),.028,112,13,91),
    "h04_chem42_chip": ((.004,0,.031),.029,49,59,0),
}[name]
target, distance, focal, el, az = detail
pic("detail", target, distance, lens=focal, fstop=8, angle=el, az=az)
if name == "h02_key":
    pic("detail_teeth", (.0037,.00025,.0304), .029, lens=261, fstop=8, angle=88, az=0)
    root.rotation_euler.x = math.pi
    pic("detail_reverse", (.0037,-.00025,.0304), .029, lens=261, fstop=8, angle=88, az=0)
    root.rotation_euler.x = 0
if name in ("h01_cdk20_lockworks", "h06_pin_lock", "h04_chem42_chip"):
    for role in rj:
        if rig[role]["type"] in ("rot", "loc") and role not in ("shell", "lid"):
            D.rest(root)
            for lid in ("shell", "lid"):
                if lid in rj:
                    D.pose(root, lid, rig[lid]["max"])
            D.pose(root, role, rig[role]["max"])
            pic("max_"+role, t, dist)

if name=="h03_loop_track":
    D.rest(root)
    D.pose(root,"car",.25)
    D.pose(root,"press",-2.5)
    carried.location.z += .03
    for ob in carried.children_recursive:
        if not ob.hide_viewport:
            ob.hide_render = False
    pic("press_fit", (0,-.010,.03655), .028, lens=145, fstop=8, angle=22, az=90)
    for ob in carried.children_recursive:
        ob.hide_render = True
    for role, value in (("blank_up",3),("press",-2.5),("test_push",1.5),("file",1),("car",1)):
        D.rest(root)
        D.pose(root,role,value)
        pic("travel_"+role,t,dist)
    for k in range(8):
        D.rest(root)
        for station in range(4):
            for kind in ("coin","clock"):
                D.pose(root,f"{kind}_s{station}_{k}",6)
        pic(f"max_tokens_layer_{k}",t,dist)
print("P0_DONE", name, data["bounds_mm"], data["triangles"], data["bad_gates"], flush=True)
