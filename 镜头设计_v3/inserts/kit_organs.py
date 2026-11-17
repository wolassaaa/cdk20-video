"""HKBU SCIE1007 课程作业的科普视频：把真实解剖网格整理成零件库用的轻量网格（写到 G:/cdk20/work/kit/organs.npz，kit_parts.py 读它）。

网格来源：BodyParts3D, © The Database Center for Life Science, CC BY 4.0（assets/anatomy/，说明见 bp3d_v3_stl/SOURCE.md）。
  肝：bp3d_v4_groups_stl 的 liver_parenchyma_segments + gallbladder，融成一张闭合的皮（体素重网格，同 blender/s1/lookdev/liver_lookdev.py）
  肝内血管：portal_vein_hepatic、hepatic_artery、hepatic_veins
  肺：FMA7333、7383、7337（右肺三叶）、FMA7370、7371（左肺两叶）；气管和支气管树：FMA7394、FMA7409
  结肠：FMA14543nsn；直肠：FMA14544
坐标从身体坐标（前 = −y，病人右 = −x，上 = z）转到板面坐标：板的 X = 身体 x（正面看过去的样子），板的 Y = 身体 z，板的 Z（朝观众）= −身体 y。
每组以自己外壳的包围盒中心为原点，单位毫米、真实大小，不压扁不变形；面数减到板上够用的程度，轮廓不动。

    blender -b --factory-startup -P kit_organs.py
"""
import math
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

A = Path("D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy")
OUT = Path("G:/cdk20/work/kit/organs.npz")
G4, V3 = A / "bp3d_v4_groups_stl", A / "bp3d_v3_stl"
bpy.ops.wm.read_factory_settings(use_empty=True)


def load(paths):
    obs = []
    for p in paths:
        bpy.ops.wm.stl_import(filepath=str(p))
        obs.append(bpy.context.selected_objects[0])
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    for v in o.data.vertices:                       # 身体坐标 → 板面坐标
        x, y, z = v.co
        v.co = (x, z, -y)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.02)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data); bm.free()
    return o


def skin(o, voxel, smooth=6):
    """融成一张闭合的皮，再抹平体素台阶。"""
    bpy.context.view_layer.objects.active = o
    o.data.remesh_voxel_size = voxel
    bpy.ops.object.voxel_remesh()
    m = o.modifiers.new("lap", "LAPLACIANSMOOTH"); m.iterations = smooth; m.lambda_factor = 0.8
    bpy.ops.object.modifier_apply(modifier="lap")


def reduce(o, faces):
    n = len(o.data.polygons) * (2 if any(len(p.vertices) == 4 for p in o.data.polygons) else 1)
    if n > faces:
        bpy.context.view_layer.objects.active = o
        m = o.modifiers.new("dec", "DECIMATE"); m.ratio = faces / n
        bpy.ops.object.modifier_apply(modifier="dec")
    m = o.modifiers.new("tri", "TRIANGULATE")
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="tri")


def arrays(o, centre=None, clip=None):
    v = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
    f = np.empty(len(o.data.polygons) * 3, dtype=np.int64); o.data.polygons.foreach_get("vertices", f); f = f.reshape(-1, 3)
    if centre is None:
        centre = (v.max(0) + v.min(0)) / 2
    v = v - centre
    if clip is not None:                             # 只留落在外壳包围盒里的三角形
        ok = np.all((v > clip[0]) & (v < clip[1]), axis=1)
        f = f[ok[f].all(1)]
        used = np.unique(f); idx = -np.ones(len(v), dtype=np.int64); idx[used] = np.arange(len(used))
        v, f = v[used], idx[f]
    return v.astype(np.float32), f.astype(np.int32), centre


out = {}
# ---- 肝
liver = load([G4 / "liver_parenchyma_segments.stl", G4 / "gallbladder.stl"])
skin(liver, 2.0); reduce(liver, 36000)
lv, lf, c = arrays(liver)
out["liver_v"], out["liver_f"] = lv, lf
ves = load([G4 / "portal_vein_hepatic.stl", G4 / "hepatic_artery.stl", G4 / "hepatic_veins.stl"])
reduce(ves, 70000)
vv, vf, _ = arrays(ves, c)
# 血管只留肝里面的：顶点在肝的皮以内，或者伸出皮外不超过 5 mm（肝门那里留一小截）
bvh = BVHTree.FromPolygons((lv.astype(float)).tolist(), lf.tolist())
keep = np.zeros(len(vv), dtype=bool)
for i, pnt in enumerate(vv):
    loc, nor, _, dist = bvh.find_nearest(Vector(pnt.tolist()))
    keep[i] = (Vector(pnt.tolist()) - loc).dot(nor) < 0 or dist < 5.0
vf = vf[keep[vf].all(1)]
used = np.unique(vf); idx = -np.ones(len(vv), dtype=np.int64); idx[used] = np.arange(len(used))
out["vessel_v"], out["vessel_f"] = vv[used], idx[vf].astype(np.int32)
# 肝的正面投影轮廓（成品位压槽用）：从投影中心往外每 2° 取最远的点
ang = np.degrees(np.arctan2(lv[:, 1], lv[:, 0])); rad = np.hypot(lv[:, 0], lv[:, 1])
ol = []
for a in range(-180, 180, 2):
    k = np.abs((ang - a + 180) % 360 - 180) < 1.5
    r = rad[k].max()
    ol.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a))))
out["liver_outline"] = np.array(ol, dtype=np.float32)
# ---- 肺 + 气管支气管
lung = load([V3 / f"FMA{n}.stl" for n in (7333, 7383, 7337, 7370, 7371)])
skin(lung, 2.5, smooth=4); reduce(lung, 30000)
out["lung_v"], out["lung_f"], c = arrays(lung)
air = load([V3 / "FMA7394.stl", V3 / "FMA7409.stl"])
reduce(air, 24000)
out["airway_v"], out["airway_f"], _ = arrays(air, c)
# ---- 结肠 + 直肠
colon = load([V3 / "FMA14543nsn.stl", V3 / "FMA14544.stl"])
skin(colon, 2.0, smooth=4); reduce(colon, 30000)
out["colon_v"], out["colon_f"], _ = arrays(colon)
np.savez_compressed(OUT, **out)
for k, v in out.items():
    print("ORGAN", k, v.shape, (v.min(0).round(1), v.max(0).round(1)) if v.dtype == np.float32 else "")
