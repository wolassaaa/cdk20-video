"""HKBU SCIE1007 课程作业的科普视频：Blender 侧读总表的通用入口（在 Blender 自带的 Python 里 import）。

    import sys; sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/映射")
    import bl_maptable as BM
    g = BM.setup_scene("2-03")                 # 场景 fps=60、帧范围 0..len_f-1，返回总表这一段（maplib.Group）
    e = g.event("cavity_one")
    BM.key_event(obj, "scale", e, (0, 0, 0), (1, 1, 1))      # f_start 起动 → f_land 到位（落点 = 词开口）
    BM.key_sustain(obj, "location", e, a, b)                  # f_land → f_end 持续（说到哪个词 / 句尾）
所有关键帧帧号直接取总表，脚本里不写任何秒数或帧数。原生 60 帧渲染，不对成片变速。

自测（不渲染，只在 Blender 里按 2-03 的事件打关键帧再读回 F 曲线，核对帧号和总表一致）：
    blender -b --factory-startup -P 镜头设计_v3/映射/bl_maptable.py -- selftest 2-03
"""
import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import maplib as M  # noqa: E402


def setup_scene(group, table=None, scene=None):
    sc = scene or bpy.context.scene
    g = M.load(table).group(group)
    sc.render.fps, sc.render.fps_base = 60, 1.0
    sc.frame_start, sc.frame_end = 0, g.len_f - 1
    return g


def _key(obj, path, frame, value, interp="BEZIER"):
    setattr(obj, path, value) if not isinstance(value, (tuple, list)) else setattr(obj, path, type(getattr(obj, path))(value))
    obj.keyframe_insert(data_path=path, frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for fc in _fcurves(obj):
            if fc.data_path == path:
                for kp in fc.keyframe_points:
                    if int(round(kp.co[0])) == frame:
                        kp.interpolation = interp


def _fcurves(obj):
    act = obj.animation_data.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []                                         # Blender 5.x 分层动作：layers → strips → channelbag
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


def key_event(obj, path, ev, v_from, v_to, interp="BEZIER"):
    """起动 → 落点。f_start 处 v_from，f_land 处 v_to。"""
    _key(obj, path, ev["f_start"], v_from, interp)
    _key(obj, path, ev["f_land"], v_to, interp)


def key_sustain(obj, path, ev, v_from, v_to, interp="LINEAR"):
    """落点 → 持续到 f_end（until 词说完 / 句尾）。持续段线性：一直在动，到 f_end 才停。"""
    if ev["f_end"] > ev["f_land"]:
        _key(obj, path, ev["f_land"], v_from, interp)
        _key(obj, path, ev["f_end"], v_to, interp)


def keyframes(obj, path):
    if not obj.animation_data:
        return []
    return sorted({int(round(kp.co[0])) for fc in _fcurves(obj) if fc.data_path == path for kp in fc.keyframe_points})


def selftest(group):
    g = setup_scene(group)
    bad, rows = 0, []
    for e in g.events():
        bpy.ops.object.empty_add()
        ob = bpy.context.object
        ob.name = e["eid"]
        key_event(ob, "scale", e, (0, 0, 0), (1, 1, 1))
        key_sustain(ob, "location", e, (0, 0, 0), (0, 0, 1))
        want_s = sorted({e["f_start"], e["f_land"]})
        want_l = sorted({e["f_land"], e["f_end"]}) if e["f_end"] > e["f_land"] else []
        got_s, got_l = keyframes(ob, "scale"), keyframes(ob, "location")
        # 落点那一帧的值：scale 必须刚好到 1
        bpy.context.scene.frame_set(e["f_land"])
        at_land = round(ob.scale[0], 4)
        bpy.context.scene.frame_set(max(0, e["f_land"] - 1))
        before = round(ob.scale[0], 4)
        ok = got_s == want_s and got_l == want_l and at_land == 1.0 and (before < 1.0 or e["f_land"] == e["f_start"])
        bad += not ok
        rows.append(dict(eid=e["eid"], want=want_s + want_l, got=got_s + got_l, scale_at_land=at_land, scale_before=before, ok=ok))
    res = dict(group=group, blender=bpy.app.version_string, fps=bpy.context.scene.render.fps, frame_end=bpy.context.scene.frame_end,
               len_f=g.len_f, events=rows, pass_all=bad == 0)
    (HERE / "_cache" / f"bl_selftest_{group}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BL_MAPTABLE_SELFTEST", json.dumps(dict(group=group, events=len(rows), bad=bad, fps=res["fps"], frame_end=res["frame_end"])))


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a and a[0] == "selftest":
        selftest(a[1] if len(a) > 1 else "2-03")
