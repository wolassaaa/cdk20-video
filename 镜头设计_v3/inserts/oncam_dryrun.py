"""HKBU SCIE1007 课程作业的科普视频：出镜段 recipe 干跑（不开大板、不渲染、不占显卡）。
在空场景里跑 recipe，抽几帧把所有可见网格的顶点投影到出片像素，叠在人物逐帧图上，出构图示意图；顺带跑穿模检查、打印每帧零件框。
blender -b --factory-startup -P oncam_dryrun.py -- 段号 帧,帧,...（排队等位用 G:/cdk20/work/oncam/harn.sh 段:帧,帧 …）"""
import sys
import json
import bpy
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/inserts")
import shot_oncam as S
import kit_parts as KP
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
seg = argv[0]
frames = [int(x) for x in argv[1].split(",")]
sc = bpy.context.scene
for o in list(sc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
w = bpy.data.worlds.new("w")
w.use_nodes = True
sc.world = w
sc.frame_start, sc.frame_end = 0, 2000
cfg = S.seg_cfg(seg)
W = dict(sc=sc, kit=KP.Kit(), cfg=cfg, light={"kelvin": 5300.0}, rig={})
R = S.RECIPES[cfg["recipe"]](W)
print("HARN recipe ok", json.dumps(R["info"], default=str)[:600], flush=True)
out = S.WORK / seg / "proj"
out.mkdir(parents=True, exist_ok=True)
Mc = S.cam_basis()
nf = cfg["nf"]
boxes = {}
for f in range(0, nf, 2):
    sc.frame_set(f)
    bb = [S.project(Mc, S.SHIFT, p) for p in R["bbox"](f)]
    bb = [p for p in bb if p[2] > 1e-6]
    if bb:
        boxes[f] = [round(min(p[0] for p in bb)), round(min(p[1] for p in bb)), round(max(p[0] for p in bb)), round(max(p[1] for p in bb))]
json.dump(boxes, open(out / "boxes.json", "w"))
dump = {}
for f in frames:
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in sc.objects:
        if o.type not in ("MESH", "CURVE", "FONT") or o.hide_render:
            continue
        try:
            e = o.evaluated_get(dg)
            me = e.to_mesh()
        except Exception:
            continue
        mw = o.matrix_world
        col = (230, 60, 50)
        if o.active_material is not None and o.active_material.node_tree is not None:
            bsdf = next((n for n in o.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf is not None:
                c = bsdf.inputs["Base Color"].default_value
                col = tuple(int(255 * min(1, max(0, x)) ** (1 / 2.2)) for x in c[:3])
        V = me.vertices
        step = max(1, len(V) // 3000)
        for i in range(0, len(V), step):
            x, y, z = S.project(Mc, S.SHIFT, mw @ V[i].co)
            if z > 1e-6 and -50 < x < 2000 and -50 < y < 1150:
                pts.append((round(x, 1), round(y, 1), *col))
        e.to_mesh_clear()
    dump[f] = dict(person=str(S.person_png(cfg, f)), pts=pts, box=boxes.get(f))
json.dump(dict(seg=seg, person_box=S.PERSON, frames=dump), open(out / "proj.json", "w"))
print("HARN proj", out / "proj.json", flush=True)
print("HARN checks", json.dumps(R["checks"]()), flush=True)
