"""HKBU SCIE1007 课程作业的科普视频：技术选型小测试（11-17）Blender 5.3 一方。
2-03 一句（A 出镜）"…one case study: CDK20 in liver cancer." 出镜旁动效小样：右半一个骨白展示台，
台面上长出克莱因蓝 CDK20 示意体，衬线字（Instrument Serif）贴在展示台正面随词写出。
所有时间读 映射/keys/2-03.json（resolve.py 出），脚本里不写秒数/帧号；场景帧率、帧范围由 bl_maptable.setup_scene 设。
透明底（film_transparent + 地面 shadow catcher），后期叠人。

    blender -b --factory-startup -P tech_203_bl.py -- build OUT.blend [samples]
然后用 inserts/fast_render.py 整段渲。
"""
import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
MAP = HERE.parent
sys.path.insert(0, str(MAP))
import bl_maptable as BM  # noqa: E402

K = json.loads((MAP / "keys" / "2-03.json").read_text(encoding="utf-8"))
EV = {e["id"]: e for e in K["events"]}
S1 = K["sentences"][0]
FONT = MAP / "_cache" / "remotion_public" / "fonts" / "InstrumentSerif-Regular.ttf"

BONE, INK, RED, KLEIN, CHROME = "#ECE6DA", "#2A2622", "#B3261E", "#1F3FBF", "#4A4D52"


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def mat(name, col, rough=0.5, metal=0.0, coat=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = lin(emit)
        p.inputs["Emission Strength"].default_value = 0.0
    return m


def key(obj, path, f, v, interp="BEZIER"):
    BM._key(obj, path, f, v, interp)


def reveal_mat(name, col, obj, width):
    """左→右写出：物体坐标 X 和一条关键帧化的写线比，写线左边不透明、右边透明（软边 0.04）。"""
    m = mat(name, col, rough=0.62)
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    p = N["Principled BSDF"]
    out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    edge = N.new("ShaderNodeValue")
    edge.name = edge.label = "edge"
    mr = N.new("ShaderNodeMath"); mr.operation = "SUBTRACT"
    ss = N.new("ShaderNodeMapRange"); ss.interpolation_type = "SMOOTHSTEP"
    ss.inputs["From Min"].default_value = 0.04
    ss.inputs["From Max"].default_value = -0.04
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(tc.outputs["Object"], sep.inputs[0])
    L.new(sep.outputs["X"], mr.inputs[0]); L.new(edge.outputs[0], mr.inputs[1])
    L.new(mr.outputs[0], ss.inputs["Value"])
    L.new(ss.outputs["Result"], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(p.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    obj.data.materials.append(m)
    return edge, width


def key_edge(edge_node, width, f0, f1):
    v = edge_node.outputs[0]
    v.default_value = -0.08
    v.keyframe_insert("default_value", frame=f0)
    v.default_value = width + 0.08
    v.keyframe_insert("default_value", frame=f1)


def text_obj(name, body, size, x, z, y):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(str(FONT), check_existing=True)
    cu.size = size
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.update()
    return o, o.dimensions.x


def build(out_blend, samples=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    BM.setup_scene("2-03", scene=sc)                     # fps 60、帧 0..len_f-1，全来自总表
    r = sc.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = 1920, 1080
    r.film_transparent = True
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    sc.cycles.samples = samples
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.052, 0.058, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    f_in0, f_in1 = S1["f0"], EV["runner_flow"]["f_start"]   # 开口起，展示台从右滑进，到 answer 起动前到位

    # 展示台
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.45))
    pl = bpy.context.object; pl.name = "plinth"
    pl.scale = (3.1, 1.1, 0.9)
    bpy.ops.object.transform_apply(scale=True)
    bv = pl.modifiers.new("bevel", "BEVEL"); bv.width = 0.035; bv.segments = 5
    pl.data.materials.append(mat("bone", BONE, rough=0.42, coat=0.15))
    bpy.ops.object.shade_smooth()

    # 底座（暗铬托槽），one 时长出
    bpy.ops.mesh.primitive_cylinder_add(radius=0.44, depth=0.04, vertices=96, location=(0.75, 0, 0.92))
    seat = bpy.context.object; seat.name = "seat"
    seat.data.materials.append(mat("chrome", CHROME, rough=0.22, metal=1.0))
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.012, location=(0.75, 0, 0.94), major_segments=128)
    ring = bpy.context.object; ring.name = "ring"
    ringm = mat("ringred", RED, rough=0.3, emit=RED); ring.data.materials.append(ringm)

    # 流道：台面前沿一条红料
    cv = bpy.data.curves.new("runner", "CURVE"); cv.dimensions = "3D"
    sp = cv.splines.new("POLY"); sp.points.add(1)
    sp.points[0].co = (-1.5, -0.5, 0.905, 1); sp.points[1].co = (1.5, -0.5, 0.905, 1)
    cv.bevel_depth = 0.018; cv.bevel_resolution = 6; cv.use_fill_caps = True
    run = bpy.data.objects.new("runner", cv); bpy.context.collection.objects.link(run)
    run.data.materials.append(mat("red", RED, rough=0.28, coat=0.6))

    # CDK20 示意体（不是结构，只是示意形体）
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=0.36, location=(0.75, 0, 0.94 + 0.34))
    cdk = bpy.context.object; cdk.name = "cdk20"
    tex = bpy.data.textures.new("lumps", "CLOUDS"); tex.noise_scale = 0.35
    dm = cdk.modifiers.new("lumps", "DISPLACE"); dm.texture = tex; dm.strength = 0.09; dm.mid_level = 0.5
    cdk.data.materials.append(mat("klein", KLEIN, rough=0.32, coat=1.0))
    bpy.ops.object.shade_smooth()

    # 地面接影
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    fl = bpy.context.object; fl.name = "floor"; fl.is_shadow_catcher = True

    # 字：贴在展示台正面（y = 正面 − 1 mm）
    yf = -0.551
    x0 = -1.38
    t1, w1 = text_obj("t_case", "One case study", 0.34, x0, 0.50, yf)
    t2, w2 = text_obj("t_cdk", "CDK20", 0.27, x0, 0.16, yf)
    t3, w3 = text_obj("t_liver", "in liver", 0.27, x0 + w2 + 0.09, 0.16, yf)
    t4, w4 = text_obj("t_cancer", "cancer.", 0.27, x0 + w2 + 0.09 + w3 + 0.09, 0.16, yf)
    e1 = reveal_mat("ink1", INK, t1, w1)
    e2 = reveal_mat("ink2", INK, t2, w2)
    e3 = reveal_mat("ink3", INK, t3, w3)
    e4 = reveal_mat("red_t", RED, t4, w4)
    for t in (t1, t2, t3, t4):
        t.parent = pl

    # 灯
    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.5, 5.5))
    k = bpy.context.object; k.data.size = 4; k.data.energy = 900; k.data.color = (1, 0.96, 0.9)
    k.rotation_euler = (math.radians(45), 0, math.radians(-38))
    bpy.ops.object.light_add(type="AREA", location=(3.5, 3, 3))
    rl = bpy.context.object; rl.data.size = 3; rl.data.energy = 500; rl.data.color = (0.85, 0.9, 1)
    rl.rotation_euler = (math.radians(-60), 0, math.radians(135))

    # 机位：展示台落在画面右半
    bpy.ops.object.empty_add(location=(0.4, 0, 1.15)); tgt = bpy.context.object
    bpy.ops.object.camera_add(location=(2.3, -7.4, 2.5)); cam = bpy.context.object
    cam.data.lens = 48; cam.data.shift_x = -0.21
    c = cam.constraints.new("TRACK_TO"); c.target = tgt
    sc.camera = cam

    # ---------- 关键帧：全部取 keys/2-03.json ----------
    key(pl, "location", f_in0, (4.2, 0, 0)); key(pl, "location", f_in1, (0, 0, 0))
    for o in (seat, ring, cdk, run):
        o.parent = pl
    e = EV["runner_flow"]
    cv.bevel_factor_end = 0.0; cv.keyframe_insert("bevel_factor_end", frame=e["f_start"])
    cv.bevel_factor_end = 0.15; cv.keyframe_insert("bevel_factor_end", frame=e["f_land"])
    cv.bevel_factor_end = 1.0; cv.keyframe_insert("bevel_factor_end", frame=e["f_end"])
    e = EV["cavity_one"]
    BM.key_event(seat, "scale", e, (0.001, 0.001, 1), (1, 1, 1))
    BM.key_event(ring, "scale", e, (0.001, 0.001, 1), (1, 1, 1))
    e = EV["tag_case"]
    key_edge(e1[0], w1, e["f_start"], e["f_end"])
    e = EV["part_cdk20"]
    BM.key_event(cdk, "scale", e, (0.001, 0.001, 0.001), (1, 1, 1))
    key(cdk, "rotation_euler", e["f_start"], (0, 0, 0), "LINEAR")
    key(cdk, "rotation_euler", sc.frame_end, (0, 0, math.radians(95)), "LINEAR")   # 长出后一直慢转到段尾
    key_edge(e2[0], w2, e["f_start"], e["f_land"] + (e["f_end"] - e["f_land"]) // 3)
    e = EV["liver_in"]
    key_edge(e3[0], w3, e["f_start"], e["f_land"] + 12)
    e = EV["cancer_red"]
    key_edge(e4[0], w4, e["f_start"], e["f_end"] - 6)
    p = ringm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    p.default_value = 0; p.keyframe_insert("default_value", frame=e["f_start"])
    p.default_value = 2.0; p.keyframe_insert("default_value", frame=e["f_land"])
    p.default_value = 4.0; p.keyframe_insert("default_value", frame=e["f_end"])

    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print("TECH203_BUILT", out_blend, "frames", sc.frame_start, sc.frame_end, "fps", r.fps)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "build":
        build(a[1], int(a[2]) if len(a) > 2 else 32)
