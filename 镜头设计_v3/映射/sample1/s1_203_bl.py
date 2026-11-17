"""HKBU SCIE1007 课程作业的科普视频：样片一 2-03（设计语言_v1 第 11 节）Blender 5.3 主体层。

台词 "And we'll answer it with one case study: CDK20 in liver cancer."
纸桌面上一块骨白模板：主流道 + 五个盖着磨砂盖的型腔；红料流过，挑中第 3 个，顶出克莱因蓝 CDK20 件，
肝形矮墙长出，红料漫进肝里。所有帧号读 映射/keys/2-03.json（resolve.py 出），脚本里不写帧号。
印在世界里的字（Case study / CDK20 / liver cancer）在 Blender 里做成贴面字，才能贴合透视；字幕和出处行在 Remotion。

    blender -b --factory-startup -P s1_203_bl.py -- build OUT.blend [samples]
    blender -b OUT.blend -P s1_203_bl.py -- check          量投影（底部 20%、主角大小、字号）和穿模
然后 inserts/fast_render.py 整段渲。单位：米。
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MAP = HERE.parent
sys.path.insert(0, str(MAP))
import bl_maptable as BM  # noqa: E402

K = json.loads((MAP / "keys" / "2-03.json").read_text(encoding="utf-8"))
EV = {e["id"]: e for e in K["events"]}
W = {w["wid"]: w for w in K["words"]}
S1 = K["sentences"][0]
FONTS = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts")

PAPER, SHADE, BONE, INK, RED, KLEIN = "#EDE9DF", "#D9D6CC", "#F6F3EC", "#1F1E1C", "#C8102E", "#002FA7"

T_TOP = 0.02                      # 模板顶面
CAV_X = [-0.22, -0.11, 0.0, 0.11, 0.22]
CAV_Y, CAV_R = 0.005, 0.018
RUN_Y = -0.07
GATE_Y = -0.05
LIVER_PTS = [(0.06, -0.12), (0.15, -0.08), (0.38, -0.03), (0.5, 0.03), (0.42, 0.13), (0.2, 0.26), (-0.05, 0.33),
             (-0.3, 0.34), (-0.46, 0.24), (-0.5, 0.05), (-0.48, -0.16), (-0.36, -0.3), (-0.15, -0.32), (-0.04, -0.2)]
LIVER_S, LIVER_DY = 0.15, 0.012
INLET = Vector((0.0, -0.022, T_TOP))


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def mat(name, col, rough=0.55, sss=0.0, trans=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.004, 0.003, 0.002)
        p.inputs["Subsurface Scale"].default_value = 0.01
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    return m


def P(m):
    return m.node_tree.nodes["Principled BSDF"]


def kv(sock, f, v):
    sock.default_value = v
    sock.keyframe_insert("default_value", frame=f)


def key(o, path, f, v, interp="BEZIER"):
    BM._key(o, path, f, v, interp)


def link(o):
    bpy.context.collection.objects.link(o)
    return o


def cube(name, size, loc, m, bevel=0.0008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3
    o.data.materials.append(m)
    return o


def cyl(name, r, h, loc, m, bevel=0.0006, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    o = bpy.context.object
    o.name = name
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o


def liver_xy():
    return [(x * LIVER_S, y * LIVER_S + LIVER_DY) for x, y in LIVER_PTS]


def smooth_loop(pts, n=8):
    """闭合 Catmull-Rom 采样，返回平滑轮廓点。"""
    out = []
    N = len(pts)
    for i in range(N):
        p0, p1, p2, p3 = (Vector(pts[(i + k) % N]) for k in (-1, 0, 1, 2))
        for j in range(n):
            t = j / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def poly_curve(name, pts3, depth, m, closed=False):
    cv = bpy.data.curves.new(name, "CURVE"); cv.dimensions = "3D"
    sp = cv.splines.new("POLY"); sp.points.add(len(pts3) - 1)
    for i, p in enumerate(pts3):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    cv.bevel_depth = depth; cv.bevel_resolution = 6; cv.use_fill_caps = True
    o = link(bpy.data.objects.new(name, cv))
    o.data.materials.append(m)
    return o


def stamp_text(name, body, font, size, loc, m, rot_z=0.0, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(str(font), check_existing=True)
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = 0.0
    o = link(bpy.data.objects.new(name, cu))
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    o.data.materials.append(m)
    o.visible_shadow = False                 # 印上去的字没有投影
    return o


def fade_mat(name, col, rough=0.6):
    """印上去的墨：alpha 由一个 Value 节点控制（0 → 1），盖印用。"""
    m = mat(name, col, rough=rough)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    a = N.new("ShaderNodeValue"); a.name = a.label = "alpha"
    a.outputs[0].default_value = 0.0
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(a.outputs[0], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(P(m).outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    return m, a.outputs[0]


def stamp(obj, alpha, f0, z_rest):
    """6 帧从 0 到 100%，同时 1 mm 下压。"""
    kv(alpha, f0 - 1, 0.0)
    kv(alpha, f0, 0.0)
    kv(alpha, f0 + 6, 1.0)
    x, y, _ = obj.location
    key(obj, "location", f0, (x, y, z_rest + 0.001))
    key(obj, "location", f0 + 6, (x, y, z_rest))


def build(out_blend, samples=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    BM.setup_scene("2-03", scene=sc)
    r = sc.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = 1920, 1080
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    sc.cycles.samples = samples
    sc.cycles.seed = 7
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "AgX - Base Contrast" if False else "None"
    sc.view_settings.exposure = -0.2
    w = bpy.data.worlds.new("w"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = lin("#EFE8DC")
    w.node_tree.nodes["Background"].inputs[1].default_value = WORLD_S

    # ---------------- 材质 ----------------
    m_paper = mat("paper", PAPER, rough=0.9)
    nt = m_paper.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 6
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], P(m_paper).inputs["Normal"])
    m_bone = mat("bone", BONE, rough=0.55, sss=0.1)
    m_lid = mat("lid_frost", BONE, rough=0.6, sss=0.1, trans=0.55)
    m_groove = mat("groove", SHADE, rough=0.8)
    m_etch = mat("etch", "#E3DFD5", rough=0.8)
    m_scar = mat("scar", "#E6E1D6", rough=0.75)
    m_red_run = mat("red_runner", RED, rough=0.15)
    m_red_liv = mat("red_liver", RED, rough=0.15)
    m_part = mat("cdk20_part", RED, rough=0.45, sss=0.05)
    m_pin = mat("pin", "#8E8A82", rough=0.35)
    P(m_pin).inputs["Metallic"].default_value = 1.0

    # ---------------- 桌面、模板 ----------------
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    fl = bpy.context.object; fl.name = "table"; fl.data.materials.append(m_paper)

    tpl = cube("template", (0.6, 0.18, T_TOP), (0, 0, T_TOP / 2), m_bone, bevel=0.0008)
    for v in tpl.data.vertices:                 # 拔模角：顶面每边内收 1.5 mm
        if v.co.z > 0:
            v.co.x -= math.copysign(0.0015, v.co.x); v.co.y -= math.copysign(0.0015, v.co.y)
    # 型腔：模板上挖 6 mm 深的圆坑
    for i, x in enumerate(CAV_X):
        c = cyl(f"cut_{i}", CAV_R, 0.012, (x, CAV_Y, T_TOP), m_bone, bevel=0)
        c.modifiers.clear()
        bo = tpl.modifiers.new(f"cav{i}", "BOOLEAN"); bo.object = c; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
        c.hide_render = c.hide_viewport = True
    tpl.modifiers.move(tpl.modifiers.find("bevel"), len(tpl.modifiers) - 1)
    bpy.context.view_layer.objects.active = tpl
    bpy.ops.object.shade_smooth()
    # 分模线：模板侧面中线一圈细缝
    cube("parting_line", (0.6012, 0.1812, 0.0005), (0, 0, T_TOP * 0.55), m_groove, bevel=0)
    # 顶针印：模板顶面浅圆印
    for x, y in ((-0.27, 0.06), (-0.27, -0.035), (0.27, 0.06), (0.27, -0.035), (-0.165, 0.065), (0.165, 0.065)):
        cyl("ejector_mark", 0.0045, 0.0003, (x, y, T_TOP + 0.00005), m_scar, bevel=0)
    # 主流道沟
    cube("runner_groove", (0.585, 0.013, 0.0004), (-0.0, RUN_Y, T_TOP + 0.0001), m_groove, bevel=0)
    # 浇口通道（流道 → 型腔）和浇口针
    pins = []
    for i, x in enumerate(CAV_X):
        cube(f"gate_ch_{i}", (0.006, abs(RUN_Y - (CAV_Y - CAV_R)), 0.0004), (x, (RUN_Y + CAV_Y - CAV_R) / 2, T_TOP + 0.0001), m_groove, bevel=0)
        pins.append(cyl(f"gate_pin_{i}", 0.0032, 0.006, (x, GATE_Y, T_TOP - 0.001), m_bone, bevel=0.0005))
        if i != 2:
            cyl(f"gate_scar_{i}", 0.0012, 0.0008, (x, GATE_Y + 0.008, T_TOP + 0.0004), m_scar, bevel=0.0002)
    # 磨砂盖
    lids = [cyl(f"lid_{i}", CAV_R + 0.0025, 0.0035, (x, CAV_Y, T_TOP + 0.00175), m_lid, bevel=0.0009) for i, x in enumerate(CAV_X)]

    # 肝形浅刻线 + 矮墙（开口留在浇口通道处）
    lv = smooth_loop(liver_xy())
    groove = poly_curve("liver_groove", [(p.x, p.y, T_TOP - 0.0002) for p in lv] + [(lv[0].x, lv[0].y, T_TOP - 0.0002)], 0.00045, m_etch)
    wall = poly_curve("liver_wall", [(p.x, p.y, T_TOP) for p in lv], 0.002, m_bone)
    wall.data.bevel_factor_mapping_end = "SPLINE"
    # 肝里的红料：填满轮廓的薄片，按到入口的距离揭开
    bm = bmesh.new()
    vs = [bm.verts.new((p.x, p.y, T_TOP + 0.0004)) for p in lv]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("liver_red"); bm.to_mesh(me); bm.free()
    lr = link(bpy.data.objects.new("liver_red", me))
    sol = lr.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.0008; sol.offset = 1
    lr.data.materials.append(m_red_liv)
    nt = m_red_liv.node_tree
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    dist = N.new("ShaderNodeVectorMath"); dist.operation = "DISTANCE"
    dist.inputs[1].default_value = (INLET.x, INLET.y, T_TOP)
    rad = N.new("ShaderNodeValue"); rad.name = rad.label = "radius"
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
    ss = N.new("ShaderNodeMapRange"); ss.interpolation_type = "SMOOTHSTEP"
    ss.inputs["From Min"].default_value = 0.002; ss.inputs["From Max"].default_value = -0.002
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 60; nz2.inputs["Detail"].default_value = 3
    wob = N.new("ShaderNodeMath"); wob.operation = "MULTIPLY_ADD"
    wob.inputs[1].default_value = 0.012; wob.inputs[2].default_value = -0.006
    add = N.new("ShaderNodeMath"); add.operation = "ADD"
    L.new(tc.outputs["Object"], nz2.inputs["Vector"]); L.new(nz2.outputs["Fac"], wob.inputs[0])
    L.new(tc.outputs["Object"], dist.inputs[0]); L.new(dist.outputs["Value"], add.inputs[0]); L.new(wob.outputs[0], add.inputs[1])
    L.new(add.outputs[0], sub.inputs[0]); L.new(rad.outputs[0], sub.inputs[1])
    L.new(sub.outputs[0], ss.inputs["Value"]); L.new(ss.outputs["Result"], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(P(m_red_liv).outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    r_liv = rad.outputs[0]

    # 红料：主流道（到第 3 个浇口）+ 料头鼓包 + 支流（流道 → 型腔 3）
    run = poly_curve("runner_red", [(-0.3, RUN_Y, T_TOP), (0.0, RUN_Y, T_TOP)], 0.0055, m_red_run)
    head = cyl("runner_head", 0.0058, 0.002, (-0.3, RUN_Y, T_TOP), m_red_run, bevel=0)
    head.modifiers.clear()
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0058, location=(-0.3, RUN_Y, T_TOP), segments=48, ring_count=24)
    bpy.data.objects.remove(head)
    head = bpy.context.object; head.name = "runner_head"; head.scale = (1.25, 1, 0.75)
    bpy.ops.object.shade_smooth(); head.data.materials.append(m_red_run)
    branch = poly_curve("branch_red", [(0.0, RUN_Y, T_TOP), (0.0, CAV_Y - CAV_R + 0.002, T_TOP)], 0.0028, m_red_run)
    branch2 = poly_curve("inlet_red", [(0.0, RUN_Y, T_TOP), (0.0, INLET.y, T_TOP)], 0.0032, m_red_liv)

    # CDK20 件：克莱因蓝的块状件（示意，不是结构），在型腔里由红料灌出
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(0, 0, 0))
    part = bpy.context.object; part.name = "cdk20_part"
    part.scale = (CAV_R * 0.93, CAV_R * 0.93, CAV_R * 0.6)
    bpy.ops.object.transform_apply(scale=True)
    tex = bpy.data.textures.new("lumps", "CLOUDS"); tex.noise_scale = 0.022
    dm = part.modifiers.new("lumps", "DISPLACE"); dm.texture = tex; dm.strength = 0.0025; dm.mid_level = 0.5
    bpy.ops.object.shade_smooth()
    part.data.materials.append(m_part)
    bpy.ops.mesh.primitive_torus_add(major_radius=CAV_R * 0.93, minor_radius=0.00035, major_segments=128, minor_segments=8,
                                     location=(0, 0, 0))
    seam = bpy.context.object; seam.name = "part_parting_line"; seam.data.materials.append(m_part)
    bpy.ops.object.shade_smooth()
    # 原点放在浇口一侧（-y），灌注时从这一侧向另一侧长
    for v in part.data.vertices:
        v.co.y += CAV_R * 0.93
    for v in seam.data.vertices:
        v.co.y += CAV_R * 0.93
    part_z0 = T_TOP - 0.004
    seam.parent = part
    part.location = (0.0, CAV_Y - CAV_R * 0.93, part_z0)
    # 顶针（三根）
    ej = [cyl(f"ej_pin_{k}", 0.0016, 0.02, (0.009 * math.cos(a), CAV_Y + 0.009 * math.sin(a), T_TOP - 0.02), m_pin, bevel=0.0002)
          for k, a in enumerate((math.radians(90), math.radians(210), math.radians(330)))]

    # 小标牌（Case study），从型腔左侧的槽里顶出
    plate_x, plate_y = 0.0, 0.0745
    plate = cube("plate", (0.084, 0.02, 0.002), (plate_x, plate_y, T_TOP - 0.0012), m_bone, bevel=0.0004)
    m_t1, a_t1 = fade_mat("ink_case", INK)
    t_case = stamp_text("t_case", "Case study", FONTS / "InstrumentSerif-Italic.ttf", 0.0155, (0, -0.0005, 0.00101), m_t1)
    t_case.parent = plate
    # CDK20 字：型腔下方
    m_t2, a_t2 = fade_mat("ink_cdk20", INK)
    t_cdk = stamp_text("t_cdk20", "CDK20", FONTS / "InstrumentSerif-Regular.ttf", 0.0125, (0.024, 0.024, T_TOP + 0.0006), m_t2, align="LEFT")
    # liver cancer：肝形下方（模板前沿外的桌面上）
    m_t3, a_t3 = fade_mat("ink_liver", INK)
    m_t4, a_t4 = fade_mat("ink_cancer", RED, rough=0.4)
    t_liv = stamp_text("t_liver", "liver", FONTS / "InstrumentSerif-Italic.ttf", 0.013, (-0.003, -0.0815, T_TOP + 0.0006), m_t3, align="RIGHT")
    t_can = stamp_text("t_cancer", "cancer", FONTS / "InstrumentSerif-Italic.ttf", 0.013, (0.003, -0.0815, T_TOP + 0.0006), m_t4, align="LEFT")

    # ---------------- 光 ----------------
    bpy.ops.object.light_add(type="AREA", location=(-2.2, 2.2, 3.0))
    key_l = bpy.context.object; key_l.name = "key"
    key_l.data.size = 2.6; key_l.data.energy = KEY_W
    key_l.data.color = (1.0, 0.965, 0.92)        # 约 4800 K
    key_l.rotation_euler = Vector((2.2, -2.2, -3.0)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(1.2, -0.3, 0.5))
    fill_l = bpy.context.object; fill_l.name = "fill"
    fill_l.data.size = 1.0; fill_l.data.energy = KEY_W * 0.15
    fill_l.data.color = (1.0, 0.95, 0.9)
    fill_l.rotation_euler = Vector((-1.2, 0.3, -0.5)).to_track_quat("-Z", "Y").to_euler()

    # ---------------- 机位（50 mm，B 俯角 40°） ----------------
    bpy.ops.object.empty_add(location=(0, 0, 0)); tgt = bpy.context.object; tgt.name = "cam_target"
    bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = "camera"
    cam.data.lens = 50
    cam.data.dof.use_dof = False
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    sc.camera = cam

    def cam_at(target, dist, elev):
        e = math.radians(elev)
        return (target[0], target[1] - dist * math.cos(e), target[2] + dist * math.sin(e))

    B_T, B_D, B_E = (0.0, -0.035, T_TOP), 0.86, 40       # 全景：五个型腔都在
    P_T, P_D, P_E = (0.0, -0.022, T_TOP), 0.30, 28       # 推到第 3 个型腔
    L_T, L_D, L_E = (0.0, -0.042, T_TOP), 0.47, 40       # 略拉远，整个肝形进画

    # ---------------- 关键帧：全部取 keys/2-03.json ----------------
    f_first = 0
    e = EV["cam_push"]
    for f, (T_, D_, E_) in ((f_first, (B_T, B_D, B_E)), (e["f_start"], (B_T, B_D, B_E)), (e["f_land"], (P_T, P_D, P_E))):
        key(tgt, "location", f, T_); key(cam, "location", f, cam_at(T_, D_, E_))
    e = EV["cam_pull"]
    for f, (T_, D_, E_) in ((e["f_start"], (P_T, P_D, P_E)), (e["f_land"], (L_T, L_D, L_E))):
        key(tgt, "location", f, T_); key(cam, "location", f, cam_at(T_, D_, E_))

    # flow_in：料头匀速从左端走到第 3 个浇口
    e = EV["flow_in"]
    rd = run.data
    rd.bevel_factor_end = 0.0; rd.keyframe_insert("bevel_factor_end", frame=e["f_start"])
    rd.bevel_factor_end = 1.0; rd.keyframe_insert("bevel_factor_end", frame=e["f_end"])
    key(head, "location", e["f_start"], (-0.3, RUN_Y, T_TOP), "LINEAR")
    key(head, "location", e["f_end"], (0.0, RUN_Y, T_TOP), "LINEAR")
    for fc in BM._fcurves(rd):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # 湿 → 哑光：流动时 0.15，停下 30 帧内到 0.5
    kv(P(m_red_run).inputs["Roughness"], e["f_end"], 0.15)
    kv(P(m_red_run).inputs["Roughness"], e["f_end"] + 30, 0.5)

    # pass_1 / pass_2：浇口针下点 1 mm 再回，没开
    for eid, i in (("pass_1", 0), ("pass_2", 1)):
        e = EV[eid]; p = pins[i]; z = p.location.z
        key(p, "location", e["f_start"], (p.location.x, GATE_Y, z))
        key(p, "location", e["f_land"], (p.location.x, GATE_Y, z - 0.001))
        key(p, "location", e["f_end"], (p.location.x, GATE_Y, z))
    # gate_one：第 3 个浇口针缩回，料头拐进去
    e = EV["gate_one"]; p = pins[2]; z = p.location.z
    key(p, "location", e["f_start"], (0.0, GATE_Y, z)); key(p, "location", e["f_land"], (0.0, GATE_Y, z - 0.0045))
    # head 拐进支流后藏进支流料（缩小）
    key(head, "scale", e["f_land"], (1.25, 1, 0.75)); key(head, "scale", e["f_land"] + 10, (0.6, 0.6, 0.5))
    # fill：支流长到型腔，型腔里从浇口一侧向另一侧漫开（磨砂盖下看是一团变大的暖红）
    e = EV["fill"]
    bd = branch.data
    bd.bevel_factor_end = 0.0; bd.keyframe_insert("bevel_factor_end", frame=e["f_start"])
    bd.bevel_factor_end = 1.0; bd.keyframe_insert("bevel_factor_end", frame=e["f_start"] + 14)
    f_fill0 = e["f_start"] + 12
    key(part, "scale", e["f_start"], (0.001, 0.001, 0.4)); key(part, "scale", f_fill0, (0.15, 0.12, 0.6))
    key(part, "scale", e["f_end"], (1, 1, 1))
    kv(P(m_part).inputs["Roughness"], e["f_end"], 0.2)

    # cdk20_eject：盖子先抬起移开；红变蓝 12 帧在落点前；顶针把件顶起 12 mm，再慢转 20°
    e = EV["cdk20_eject"]
    lid = lids[2]; lz = lid.location.z
    key(lid, "location", e["f_start"], (0.0, CAV_Y, lz))
    key(lid, "location", e["f_start"] + 7, (0.0, CAV_Y + 0.004, lz + 0.032))
    key(lid, "location", e["f_start"] + 22, (0.0, 0.16, lz + 0.09))
    key(lid, "location", e["f_start"] + 32, (0.0, 0.32, lz + 0.2))
    col = P(m_part).inputs["Base Color"]
    kv(col, e["f_land"] - 12, lin(RED)); kv(col, e["f_land"], lin(KLEIN))
    kv(P(m_part).inputs["Roughness"], e["f_land"], 0.45)
    lift = 0.012
    px, py, _ = part.location
    key(part, "location", e["f_start"] + 5, (px, py, part_z0)); key(part, "location", e["f_land"], (px, py, part_z0 + lift))
    for p in ej:
        x, y, z = p.location
        key(p, "location", e["f_start"], (x, y, z)); key(p, "location", e["f_land"], (x, y, z + lift + 0.0005))
    # 旋转绕件中心：父到一个在型腔中心的空物体
    bpy.ops.object.empty_add(location=(0.0, CAV_Y, 0)); piv = bpy.context.object; piv.name = "part_pivot"
    part.parent = piv; part.location = (px, py - CAV_Y, part.location.z)
    for fc in BM._fcurves(part):
        if fc.data_path == "location" and fc.array_index == 1:
            for kp in fc.keyframe_points:
                kp.co[1] -= CAV_Y; kp.handle_left[1] -= CAV_Y; kp.handle_right[1] -= CAV_Y
    key(piv, "rotation_euler", e["f_land"], (0, 0, 0)); key(piv, "rotation_euler", e["f_end"], (0, 0, math.radians(20)))
    # 盖子移开后，第 3 个型腔里的支流料尾哑光
    # ink_cdk20
    e = EV["ink_cdk20"]
    stamp(t_cdk, a_t2, e["f_land"], T_TOP + 0.0006)

    # plate_case：标牌从槽里顶出（落点到位），再落平
    e = EV["plate_case"]
    key(plate, "location", e["f_start"], (plate_x, plate_y, T_TOP - 0.0012))
    key(plate, "location", e["f_land"], (plate_x, plate_y, T_TOP + 0.006))
    key(plate, "rotation_euler", e["f_start"], (0, 0, 0)); key(plate, "rotation_euler", e["f_land"], (math.radians(-8), 0, 0))
    key(plate, "location", e["f_end"], (plate_x, plate_y, T_TOP + 0.001))
    key(plate, "rotation_euler", e["f_end"], (0, 0, 0))
    kv(a_t1, e["f_land"], 0.0); kv(a_t1, e["f_land"] + 6, 1.0)

    # liver_grow：刻线长成矮墙（从浇口一侧沿轮廓到另一侧）
    e = EV["liver_grow"]
    wd = wall.data
    wd.bevel_factor_end = 0.0; wd.keyframe_insert("bevel_factor_end", frame=e["f_start"])
    wd.bevel_factor_end = 0.62; wd.keyframe_insert("bevel_factor_end", frame=e["f_land"])
    wd.bevel_factor_end = 1.0; wd.keyframe_insert("bevel_factor_end", frame=e["f_end"])
    key(wall, "scale", e["f_start"], (1, 1, 0.2)); key(wall, "scale", e["f_land"], (1, 1, 1))

    # cancer_red：红料从入口漫进肝里，绕着蓝件铺开，句尾停
    e = EV["cancer_red"]
    b2 = branch2.data
    b2.bevel_factor_end = 0.0; b2.keyframe_insert("bevel_factor_end", frame=e["f_start"])
    b2.bevel_factor_end = 1.0; b2.keyframe_insert("bevel_factor_end", frame=e["f_land"])
    kv(r_liv, e["f_start"], 0.0); kv(r_liv, e["f_land"], 0.012)
    kv(r_liv, e["f_end"], R_LIVER_MAX)
    kv(P(m_red_liv).inputs["Roughness"], e["f_end"], 0.15)
    kv(P(m_red_liv).inputs["Roughness"], sc.frame_end, 0.3)
    # ink_cancer
    e = EV["ink_cancer"]
    stamp(t_liv, a_t3, e["f_land"], T_TOP + 0.0006)
    stamp(t_can, a_t4, e["f_land"], T_TOP + 0.0006)

    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print("S1_203_BUILT", out_blend, sc.frame_start, sc.frame_end, r.fps)


R_LIVER_MAX = 0.044
KEY_W, WORLD_S = 170.0, 0.06


# ====================================================================== 检查
def px_bbox(sc, cam, objs, f):
    from bpy_extras.object_utils import world_to_camera_view
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys = [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        for v in me.vertices:
            p = world_to_camera_view(sc, cam, ev.matrix_world @ v.co)
            xs.append(p.x * 1920); ys.append((1 - p.y) * 1080)
        ev.to_mesh_clear()
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def check():
    sc = bpy.context.scene
    cam = sc.camera
    O = bpy.data.objects
    res = {}
    parts = [o for o in O if o.type in ("MESH", "CURVE", "FONT") and not o.hide_render and o.name != "table"]
    worst = 0
    for f in range(sc.frame_start, sc.frame_end + 1, 4):
        bb = px_bbox(sc, cam, parts, f)
        worst = max(worst, bb[3])
    res["max_bottom_px_all_parts"] = round(worst, 1)
    bb = px_bbox(sc, cam, [O["cdk20_part"], O["lid_2"]], EV["cdk20_eject"]["f_land"])
    bb2 = px_bbox(sc, cam, [O["cdk20_part"]], EV["cdk20_eject"]["f_land"])
    res["part_plus_cavity_h_206"] = round(max(bb[3], bb2[3]) - min(bb2[1], bb[1]), 1) if bb else None
    cavb = px_bbox(sc, cam, [O["cdk20_part"]] + [o for o in O if o.name.startswith("ej_pin")], EV["cdk20_eject"]["f_land"])
    res["part_bbox_206"] = [round(x) for x in cavb]
    for f in (EV["cam_push"]["f_land"], EV["cam_pull"]["f_land"], sc.frame_end):
        res[f"liver_bbox_{f}"] = [round(x) for x in px_bbox(sc, cam, [O["liver_groove"]], f)]
        res[f"template_bbox_{f}"] = [round(x) for x in px_bbox(sc, cam, [O["template"]], f)]
    for n, f in (("t_case", EV["plate_case"]["f_end"]), ("t_cdk20", sc.frame_end), ("t_liver", sc.frame_end), ("t_cancer", sc.frame_end),
                 ("t_cdk20", EV["ink_cdk20"]["f_end"])):
        b = px_bbox(sc, cam, [O[n]], f)
        res[f"{n}_{f}_px"] = [round(x) for x in b]
    for f in (0, EV["cam_push"]["f_start"]):
        res[f"template_bbox_{f}"] = [round(x) for x in px_bbox(sc, cam, [O["template"]], f)]
    # 穿模：盖子底面 vs 件顶面；件 vs 模板顶（件中心离开型腔前不许横移）
    clash = []
    for f in range(EV["cdk20_eject"]["f_start"] - 2, EV["cdk20_eject"]["f_end"] + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        lid = O["lid_2"].evaluated_get(dg); pt = O["cdk20_part"].evaluated_get(dg)
        lb = [lid.matrix_world @ Vector(c) for c in lid.bound_box]; pb = [pt.matrix_world @ Vector(c) for c in pt.bound_box]
        lmin = Vector([min(v[i] for v in lb) for i in range(3)]); lmax = Vector([max(v[i] for v in lb) for i in range(3)])
        pmin = Vector([min(v[i] for v in pb) for i in range(3)]); pmax = Vector([max(v[i] for v in pb) for i in range(3)])
        if all(lmin[i] < pmax[i] and pmin[i] < lmax[i] for i in range(3)) and f > EV["cdk20_eject"]["f_start"]:
            clash.append(f)
    res["lid_part_clash_frames"] = clash
    # 镜头路线：相机始终在桌面以上、在任何件之外
    lowz = min((sc.frame_set(f), cam.matrix_world.translation.z)[1] for f in range(sc.frame_start, sc.frame_end + 1))
    res["camera_min_z"] = round(lowz, 3)
    print("S1_CHECK " + json.dumps(res))


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], int(a[2]) if len(a) > 2 else 32)
    elif a[0] == "check":
        check()
