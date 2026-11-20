"""HKBU SCIE1007 课程作业的科普视频：全片那一整块拼装模型大板的零件库（清单见 审片/总管/全局统筹_板件与资产_v1.md）。
46 种零件，每种一个生成函数，函数名带清单编号（p03_person、p19_cdk20 …）。零件都画在一格里：
板面是 XY 平面，Z 是厚度，原点在格子中心，零件不超出 ±26 × ±16 mm；每件登记自己的浇口点（大件 2–3 个，小件 1 个），
挂到格子外圈的料杆上，浇口是细锥，尖头在零件一侧，拔下来时在这里断。
器官（肝、肝内血管、肺、气管支气管、结肠直肠）是真实解剖网格：BodyParts3D, © The Database Center for Life Science, CC BY 4.0
（kit_organs.py 整理成 G:/cdk20/work/kit/organs.npz）。片尾 credits 要写这一条，kit_data.json 的 credits 里也有。
材质只有三类：亮面实色（红、克莱因蓝、绿、骨白、黑）、香槟金电镀、透明（淡粉 / 无色 / 淡黄 / 磨砂）。
    blender -b --factory-startup -P kit_parts.py -- catalog 1|2 OUT.png [采样] [百分比]
    blender -b --factory-startup -P kit_parts.py -- board pano|z1|z34|z5 OUT.png [采样] [百分比]
目录图的编号和英文名由 kit_label.py 按同名 .json 里的像素位置写上去。单位：函数里写毫米，建模时换成米。
"""

import json
import os
import math
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

MM = 0.001
FONTS = Path("D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts")
WORK_ROOT = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))   # 11-20 晚：帧、缓存一律写 G（D 是系统盘）；D:/cdk20_work 是指向这里的目录联接
CDK20_NPZ = WORK_ROOT / "kit/cdk20.npz"       # styleframes/art/fusion/s1/inserts/make_cdk20_mesh.py 生成
HDRI = Path(os.environ.get("CDK20_BLENDER_DIR", "D:/software/blender-5.3")) / "5.3/datafiles/studiolights/world/studio.exr"
EXPO = -3.85
CX, CY = 30.0, 20.0            # 一格外圈料杆的半宽、半高（mm）
PX, PY = 66.0, 46.0            # 格距
R_LOOP, R_MAIN, R_FRAME = 1.5, 5.0, 3.4


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


# ---------------------------------------------------------------- 三类材质


def mat_solid(name, col, rough=0.1, coat=0.6, sss=0.05):
    """亮面实色塑料。"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.04
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.004, 0.002, 0.0015)
        p.inputs["Subsurface Scale"].default_value = 0.01
    return m


def mat_plated(name, col="#E2CFA0", rough=0.06):
    """香槟金电镀：全金属镜面。"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = 1.0
    return m


def mat_clear(name, rgb=(0.95, 0.55, 0.62), density=18.0, rough=0.02, coat=0.0):
    """透明：折射 + 体积吸收（厚处颜色深、薄处近乎无色）。rough 调高就是磨砂，coat 给磨砂件一层亮的清漆高光。
    影子射线直接穿过去（只被体积染色），不然透明件会把自己身下的台面压成一团灰。"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.49
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.03
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.97, 0.97, 0.97, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*rgb, 1)
    va.inputs["Density"].default_value = density
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


class Kit:
    """全片共用的一套材质。"""
    def __init__(self):
        self.red = mat_solid("kit_red", "#C8102E")
        self.blue = mat_solid("kit_blue", "#002FA7", rough=0.12)
        self.green = mat_solid("kit_green", "#5E8A64", rough=0.12)
        self.white = mat_solid("kit_white", "#F4F1EA")
        self.black = mat_solid("kit_black", "#1E1E20", rough=0.14)
        self.gold = mat_plated("kit_gold")
        self.clear = mat_clear("kit_clear_pink")                                   # 淡粉透明
        self.clear0 = mat_clear("kit_clear", rgb=(0.90, 0.97, 0.98), density=3.0)   # 无色透明
        self.yellow = mat_clear("kit_clear_yellow", rgb=(1.0, 0.90, 0.05), density=420.0)
        self.cellpink = mat_clear("kit_cell_pink", rgb=(0.96, 0.42, 0.55), density=55.0)
        self.frost = mat_clear("kit_frost", rgb=(0.50, 0.75, 1.0), density=42.0, rough=0.16, coat=1.0)
        self.tail = mat_clear("kit_tail", rgb=(0.22, 0.42, 1.0), density=520.0, rough=0.15)   # 淡蓝半透明
        self.liquid = mat_clear("kit_liquid", rgb=(0.97, 0.38, 0.52), density=120.0)
        self.nuc_red = mat_clear("kit_nucleus_red", rgb=(0.8, 0.05, 0.12), density=160.0)
        self.liq_blue = mat_clear("kit_liquid_blue", rgb=(0.30, 0.68, 1.0), density=120.0)
        self.land = mat_solid("kit_land", "#B9B2A4", rough=0.22, coat=0.3)
        self.organ_m = mat_clear("kit_organ_glass_mid", rgb=(1.0, 0.36, 0.34), density=330.0)   # 一格大小的肝：再浓一档，小了也看得出外形
        self.dishpink = mat_clear("kit_dish_pink", rgb=(1.0, 0.30, 0.48), density=520.0)
        self.gold_satin = mat_plated("kit_gold_satin", rough=0.32)
        self.blue_hi = mat_solid("kit_blue_hi", "#3D6BE6", rough=0.12)
        self.organ = mat_clear("kit_organ_glass", rgb=(1.0, 0.42, 0.40), density=26.0)          # 器官：淡红通透玻璃（大件）
        self.organ_s = mat_clear("kit_organ_glass_small", rgb=(1.0, 0.40, 0.38), density=230.0)   # 同一种玻璃，小件厚度小，浓一点
        self.nuc_grey = mat_clear("kit_nucleus_grey", rgb=(0.62, 0.62, 0.66), density=110.0)
        self.ink = mat_solid("kit_ink_dark", "#1F1E1C", rough=0.3, coat=0.2, sss=0)       # 印在浅色件上的字
        self.inkw = mat_solid("kit_ink_white", "#F7F4EE", rough=0.25, coat=0.2, sss=0)    # 印在深色件上的字
        self.inkg = mat_solid("kit_ink_grey", "#9A968C", rough=0.3, coat=0.2, sss=0)

    def cat(self, key):
        return {"red": self.red, "blue": self.blue, "green": self.green, "white": self.white, "black": self.black,
                "gold": self.gold, "clear": self.clear0, "organ": self.organ_s}[key]


# ---------------------------------------------------------------- 造型工具（都用毫米）


def link(o, parent=None):
    bpy.context.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


def rrect(cx, cy, hx, hy, r, n=6):
    r = min(r, hx, hy)
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + sx * (hx - r), cy + sy * (hy - r)
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def arc(cx, cy, r, a0, a1, n=16, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def circle(cx, cy, r, n=48, ry=None):
    return arc(cx, cy, r, 0, 360 - 360 / n, n - 1, ry)


def ngon(cx, cy, r, n, rot=0.0):
    return [(cx + r * math.cos(math.radians(rot + 360 * k / n)), cy + r * math.sin(math.radians(rot + 360 * k / n))) for k in range(n)]


def smooth_loop(pts, n=6):
    out = []
    N = len(pts)
    for i in range(N):
        p0, p1, p2, p3 = (Vector(pts[(i + k) % N]) for k in (-1, 0, 1, 2))
        for j in range(n):
            t = j / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append(tuple(q))
    return out


def smooth_path(pts, n=8):
    P = [Vector(tuple(p) + (0.0,) * (3 - len(p))) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(P[-2]))
    return out


DATA = json.loads((Path(__file__).parent / "kit_data.json").read_text(encoding="utf-8"))     # kit_mols.py 生成：001、048、ATP 的原子坐标，香港轮廓


_ORG = {}


def organ(key):
    """真实解剖网格（BodyParts3D, CC BY 4.0），kit_organs.py 整理好的：顶点（毫米，真实大小，板面坐标）和三角形。"""
    import numpy as np
    if not _ORG:
        d = np.load(str(WORK_ROOT / "kit/organs.npz"))
        _ORG.update({k: d[k] for k in d.files})
    return _ORG[key + "_v"], _ORG[key + "_f"]


def organ_gates(P, v, s, dirs):
    """器官件的浇口：板面附近（|z| < 1.5 mm）最靠外的点。"""
    import numpy as np
    w = v * np.array(s)
    near = np.abs(w[:, 2]) < 1.5
    for d in dirs:
        dv = {"-x": (-1, 0), "+x": (1, 0), "-y": (0, -1), "+y": (0, 1)}[d]
        k = int(np.argmax((w[:, 0] * dv[0] + w[:, 1] * dv[1]) * near - 1e6 * (~near)))
        P.gate(w[k, 0] - dv[0] * 0.5, w[k, 1] - dv[1] * 0.5, d, w[k, 2])


def clip_line(pts, p0, p1, gap):
    """多边形裁到直线 p0→p1 左侧、离线 gap 以外的部分。"""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1])).normalized(); n = Vector((-d.y, d.x))
    f = lambda p: (p[0] - p0[0]) * n.x + (p[1] - p0[1]) * n.y - gap
    out = []
    N = len(pts)
    for i in range(N):
        a, b = pts[i], pts[(i + 1) % N]
        fa, fb = f(a), f(b)
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def mol_part(P, key, s, m, ra, rb, big=(), cx=0.0, cy=0.0):
    """按真实原子坐标做球棍：一个原子一个球，一根键一根棍。s 是毫米每埃。返回原子的毫米坐标。"""
    d = DATA[key]
    xyz = [(cx + a[1] * s, cy + a[2] * s, a[3] * s) for a in d["atoms"]]
    for i, j in d["bonds"]:
        P.tube([xyz[i], xyz[j]], rb, m)
    for a, p in zip(d["atoms"], xyz):
        P.ball(p[0], p[1], p[2], ra * (1.45 if a[0] in big else 1.0), m, seg=20)
    return xyz


def clip_x(pts, x0, keep_less):
    """多边形裁到 x<x0（或 x>x0）一侧。"""
    out = []
    N = len(pts)
    inside = (lambda p: p[0] <= x0) if keep_less else (lambda p: p[0] >= x0)
    for i in range(N):
        a, b = pts[i], pts[(i + 1) % N]
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (x0 - a[0]) / (b[0] - a[0])
            out.append((x0, a[1] + t * (b[1] - a[1])))
    return out


class Part:
    """一格里的零件。所有坐标是毫米；at() 设后面图形的偏移，一格里放几件小东西时用。"""
    def __init__(self, K, name, cat):
        self.K, self.name, self.cat = K, name, cat
        self.root = link(bpy.data.objects.new(name, None))
        self.gates, self.ox, self.oy, self.n = [], 0.0, 0.0, 0

    def nm(self, t):
        self.n += 1
        return f"{self.name}_{t}{self.n}"

    def at(self, ox=0.0, oy=0.0):
        self.ox, self.oy = ox, oy
        return self

    def slab(self, pts, t, m, z=0.0, bevel=0.5, holes=(), seg=3, cuts=()):
        name = self.nm("s")
        bm = bmesh.new()
        vs = [bm.verts.new(((p[0] + self.ox) * MM, (p[1] + self.oy) * MM, (z - t / 2) * MM)) for p in pts]
        f = bm.faces.new(vs)
        bmesh.ops.recalc_face_normals(bm, faces=[f])
        if f.normal.z > 0:
            f.normal_flip()
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
            v.co.z += t * MM
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = link(bpy.data.objects.new(name, me), self.root)
        for (hx, hy, hr) in holes:
            bpy.ops.mesh.primitive_cylinder_add(radius=hr * MM, depth=(t * 4 + 2) * MM, vertices=40, location=((hx + self.ox) * MM, (hy + self.oy) * MM, z * MM))
            c = bpy.context.object; c.hide_render = c.hide_viewport = True; c.parent = self.root; c.name = name + "_cut"
            bo = o.modifiers.new("hole", "BOOLEAN"); bo.object = c; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
        for cp in cuts:                          # 压出来的浅槽：拿一块同形状的料去减
            c = self.slab(cp[0], cp[1], m, z=cp[2], bevel=0)
            c.hide_render = c.hide_viewport = True; c.name = name + "_cut"
            bo = o.modifiers.new("cut", "BOOLEAN"); bo.object = c; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
        if bevel:
            b = o.modifiers.new("bv", "BEVEL"); b.width = bevel * MM; b.segments = seg; b.limit_method = "ANGLE"
            o.modifiers.new("wn", "WEIGHTED_NORMAL")
        for p in me.polygons:
            p.use_smooth = bool(bevel)
        o.data.materials.append(m)
        return o

    def box(self, cx, cy, hx, hy, t, m, z=0.0, r=1.0, bevel=0.5):
        return self.slab(rrect(cx, cy, hx, hy, r) if r else [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)], t, m, z, bevel)

    def disc(self, cx, cy, r, t, m, z=0.0, bevel=0.5, ry=None, hole=None):
        return self.slab(circle(cx, cy, r, ry=ry), t, m, z, bevel, holes=[(cx, cy, hole)] if hole else ())

    def ring(self, cx, cy, ro, ri, t, m, z=0.0, bevel=0.5, n=64):
        """圆环（不走布尔）。"""
        name = self.nm("r")
        bm = bmesh.new()
        L = []
        for rr, zz in ((ro, -t / 2), (ro, t / 2), (ri, t / 2), (ri, -t / 2)):
            L.append([bm.verts.new(((cx + self.ox + rr * math.cos(2 * math.pi * k / n)) * MM, (cy + self.oy + rr * math.sin(2 * math.pi * k / n)) * MM, (z + zz) * MM)) for k in range(n)])
        for i in range(4):
            for k in range(n):
                bm.faces.new((L[i][k], L[i][(k + 1) % n], L[(i + 1) % 4][(k + 1) % n], L[(i + 1) % 4][k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = link(bpy.data.objects.new(name, me), self.root)
        if bevel:
            b = o.modifiers.new("bv", "BEVEL"); b.width = bevel * MM; b.segments = 3; b.limit_method = "ANGLE"
            o.modifiers.new("wn", "WEIGHTED_NORMAL")
        for p in me.polygons:
            p.use_smooth = True
        o.data.materials.append(m)
        return o


    def mesh(self, v, f, m, s=(1.0, 1.0, 1.0), x=0.0, y=0.0, z=0.0):
        """现成的三角网格（毫米），按 s 缩放后放到 (x, y, z)。"""
        import numpy as np
        name = self.nm("m")
        w = (np.asarray(v, dtype=float) * np.array(s) + np.array([x + self.ox, y + self.oy, z])) * MM
        me = bpy.data.meshes.new(name)
        me.from_pydata(w.tolist(), [], np.asarray(f).tolist())
        for p in me.polygons:
            p.use_smooth = True
        o = link(bpy.data.objects.new(name, me), self.root)
        o.data.materials.append(m)
        return o

    def capsule(self, x, y0, y1, r, m, z=0.0):
        """两头圆的圆棒，轴沿 Y。"""
        return self.lathe([(0.02, y0), (r * 0.5, y0 + r * 0.13), (r * 0.87, y0 + r * 0.5), (r, y0 + r), (r, y1 - r), (r * 0.87, y1 - r * 0.5), (r * 0.5, y1 - r * 0.13), (0.02, y1)], m, x, 0, z)

    def inkbox(self, cx, cy, hx, hy, m, z):
        """印上去的色块：0.3 mm 厚，贴在 z 这个面上。"""
        return self.slab([(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)], 0.3, m, z + 0.15, 0)

    def cyl(self, x, y, z, r, h, m, axis="z", bevel=0.3):
        rot = {"z": (0, 0, 0), "y": (math.radians(90), 0, 0), "x": (0, math.radians(90), 0)}[axis]
        bpy.ops.mesh.primitive_cylinder_add(radius=r * MM, depth=h * MM, vertices=48, location=((x + self.ox) * MM, (y + self.oy) * MM, z * MM), rotation=rot)
        o = bpy.context.object; o.name = self.nm("c")
        if bevel:
            b = o.modifiers.new("bv", "BEVEL"); b.width = bevel * MM; b.segments = 3; b.limit_method = "ANGLE"
        bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = self.root
        return o

    def ball(self, x, y, z, r, m, sc=(1, 1, 1), seg=32):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * MM, location=((x + self.ox) * MM, (y + self.oy) * MM, z * MM), segments=seg, ring_count=seg // 2)
        o = bpy.context.object; o.name = self.nm("b"); o.scale = sc
        bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = self.root
        return o

    def torus(self, x, y, z, R, r, m, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=R * MM, minor_radius=r * MM, major_segments=64, minor_segments=12,
                                         location=((x + self.ox) * MM, (y + self.oy) * MM, z * MM), rotation=rot)
        o = bpy.context.object; o.name = self.nm("t")
        bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = self.root
        return o

    def tube(self, pts, r, m, smooth=False):
        if smooth:
            pts = smooth_path(pts)
        name = self.nm("tb")
        cv = bpy.data.curves.new(name, "CURVE"); cv.dimensions = "3D"
        sp = cv.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            p = tuple(p) + (0.0,) * (3 - len(p))
            sp.points[i].co = ((p[0] + self.ox) * MM, (p[1] + self.oy) * MM, p[2] * MM, 1)
        cv.bevel_depth = r * MM; cv.bevel_resolution = 6; cv.use_fill_caps = True
        o = link(bpy.data.objects.new(name, cv), self.root)
        o.data.materials.append(m)
        return o

    def lathe(self, prof, m, x, y, z=0.0, seg=48):
        """回转体，轴沿板面里的 Y；prof 是 (半径, 沿轴位置) 的折线，首尾收到轴上。"""
        name = self.nm("l")
        bm = bmesh.new()
        rings = []
        for r, t in prof:
            r = max(r, 0.02)
            rings.append([bm.verts.new(((x + self.ox + r * math.cos(2 * math.pi * k / seg)) * MM, (y + self.oy + t) * MM, (z + r * math.sin(2 * math.pi * k / seg)) * MM)) for k in range(seg)])
        for i in range(len(rings) - 1):
            for k in range(seg):
                bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
        bm.faces.new(rings[0]); bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(35))
        o = link(bpy.data.objects.new(name, me), self.root)
        o.data.materials.append(m)
        return o

    def text(self, body, size, x, y, z, m, italic=False, align="CENTER", rot=0.0):
        name = self.nm("tx")
        cu = bpy.data.curves.new(name, "FONT")
        cu.body = body
        cu.font = bpy.data.fonts.load(str(FONTS / ("InstrumentSerif-Italic.ttf" if italic else "InstrumentSerif-Regular.ttf")), check_existing=True)
        cu.size = size * MM; cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = 0.15 * MM
        o = link(bpy.data.objects.new(name, cu), self.root)
        o.location = ((x + self.ox) * MM, (y + self.oy) * MM, (z + 0.15) * MM)
        o.rotation_euler = (0, 0, math.radians(rot))
        o.data.materials.append(m)
        return o

    def gate(self, x, y, d, z=0.0):
        """登记一个浇口：零件边上的点（mm）、朝外的方向 '+x' '-x' '+y' '-y'，和这个点离板面的高度。"""
        self.gates.append((float(x + self.ox), float(y + self.oy), d, float(z)))

    def done(self):
        self.root["gates"] = json.dumps(self.gates)
        self.root["cat"] = self.cat
        return self.root


def key_shape(P, x0, y0, k, m, seed=0, hole=True):
    """真钥匙：圆柄带孔、柄肩、钥匙杆上一道纵槽、下沿一排高低不等的齿、头部斜切。k 是比例（1 = 杆长 50 mm）。"""
    rnd = random.Random(seed)
    teeth = [0.0] + [rnd.choice((0.8, 1.4, 2.2, 3.0, 3.6, 4.2)) for _ in range(7)]
    L, H = 50 * k, 7.5 * k
    pts = [(x0, y0 + H / 2), (x0 + L - 4 * k, y0 + H / 2), (x0 + L, y0 + H / 2 - 3 * k), (x0 + L, y0 - H / 2)]
    n = len(teeth)
    for i, t in enumerate(reversed(teeth)):
        xa = x0 + L - (i + 0.5) * (L - 12 * k) / n - 2 * k
        pts.append((xa + 1.8 * k, y0 - H / 2 - t * k))
        pts.append((xa - 1.8 * k, y0 - H / 2 - t * k))
    pts += [(x0 + 8 * k, y0 - H / 2), (x0, y0 - H / 2)]
    th = max(2.2 * k, 1.0)
    P.slab(pts, th, m, bevel=0.4 * k)
    P.slab(rrect(x0 + 26 * k, y0 + 1.2 * k, 20 * k, 0.7 * k, 0.6 * k), th + 0.4 * k, m, bevel=0.2 * k)
    P.slab(circle(x0 - 13 * k, y0, 12 * k, ry=9.5 * k), th + 0.6 * k, m, bevel=0.8 * k, holes=[(x0 - 16 * k, y0, 3.5 * k)] if hole else ())
    P.slab(rrect(x0 + 0.5 * k, y0, 1.8 * k, 5.5 * k, 0.8 * k), th + 0.8 * k, m, bevel=0.4 * k)


def cdk20_body(P, m, size=36.0, peg=True):
    """CDK20：AlphaFold 预测结构的外形包络（公开模型），背面一根定位销。"""
    import numpy as np
    d = np.load(str(CDK20_NPZ))
    v = d["verts"] - d["verts"].mean(0)
    q = Vector(d["mouth"].tolist()).rotation_difference(Vector((0.35, 0.0, 0.94)))
    v = v @ np.array(q.to_matrix()).T
    v *= size * MM / float((v[:, :2].max(0) - v[:, :2].min(0)).max())
    v -= (v.max(0) + v.min(0)) / 2
    me = bpy.data.meshes.new(P.nm("cdk20"))
    me.from_pydata(v.tolist(), [], d["quads"].tolist())
    o = link(bpy.data.objects.new(me.name, me), P.root)
    for f in me.polygons:
        f.use_smooth = True
    o.data.materials.append(m)
    zmin = float(v[:, 2].min()) / MM
    if peg:
        P.cyl(0, 0, zmin - 2.0, 2.0, 6.0, m, bevel=0.4)
    for dv, d_ in (((-1, 0), "-x"), ((1, 0), "+x"), ((0, -1), "-y")):
        k = int(np.argmax((v[:, 0] * dv[0] + v[:, 1] * dv[1]) * (np.abs(v[:, 2]) < 4 * MM)))
        P.gate(v[k, 0] / MM - dv[0] * 0.4, v[k, 1] / MM - dv[1] * 0.4, d_, v[k, 2] / MM)
    return o


# ---------------------------------------------------------------- 46 种零件


def p01_frame(K):
    P = Part(K, "p01_frame", "white"); m = K.white
    P.tube([(-24, 6), (24, 6)], 2.6, m)
    P.tube([(-8, 6), (-8, -6)], 1.5, m)
    P.tube([(-8, -6), (6, -6)], 1.5, m)
    bpy.ops.mesh.primitive_cone_add(radius1=1.3 * MM, radius2=0.5 * MM, depth=4 * MM, vertices=24, location=(8 * MM, -6 * MM, 0), rotation=(0, math.radians(90), 0))
    c = bpy.context.object; bpy.ops.object.shade_smooth(); c.data.materials.append(m); c.parent = P.root
    P.disc(14, -6, 4.2, 2.4, m, bevel=0.8)
    P.box(12, 6, 8.5, 4.6, 1.6, m, z=2.6, r=1.2, bevel=0.4)
    P.text("A 1", 6.6, 12, 5.8, 3.4, K.ink)
    P.cyl(-18, 6, 4.0, 2.6, 4.0, m)
    P.gate(-24, 6, "-x"); P.gate(24, 6, "+x")
    return P.done()

STATIONS = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"]


def station_plate(P, label, x, y, z=0.0):
    P.box(x, y, 11.5, 3.4, 2.0, K_white(P), z=z, r=1.4, bevel=0.5)
    P.text(label, 4.6, x, y - 0.15, z + 1.0, P.K.ink)


def K_white(P):
    return P.K.white


def p02_stations(K):
    P = Part(K, "p02_stations", "white")
    for i, s in enumerate(STATIONS):
        x, y = (-13.5 if i % 2 == 0 else 13.5), 12.6 - (i // 2) * 8.4
        if i == 6:
            x = 0
        station_plate(P, s, x, y)
        if i == 6:
            P.gate(0, y - 3.4, "-y")
        else:
            P.gate(x + (-11.5 if x < 0 else 11.5), y, "-x" if x < 0 else "+x")
    return P.done()


def person(P, m, ox):
    """玩具小人，全是回转体：圆头、上宽下窄的身子、两条圆胳膊、两条圆腿。"""
    P.at(ox, 0)
    P.ball(0, 10.6, 0, 4.3, m)
    P.lathe([(0.02, 6.6), (3.6, 6.5), (5.4, 5.4), (5.8, 3.6), (5.0, -1.0), (4.3, -3.6), (3.0, -4.6), (0.02, -4.7)], m, 0, 0)
    for s in (-1, 1):
        P.capsule(s * 6.9, -4.2, 5.6, 1.7, m)
        P.capsule(s * 2.35, -15.2, -2.6, 2.1, m)
    P.gate(-2.35, -15.0, "-y")
    P.at()


def p03_person(K):
    P = Part(K, "p03_person", "white")
    person(P, K.white, -11); person(P, K.red, 11)
    return P.done()

LIVER = [(-0.5, 0.1), (-0.44, 0.24), (-0.28, 0.33), (-0.04, 0.33), (0.18, 0.27), (0.36, 0.18), (0.5, 0.08),
         (0.42, 0.04), (0.24, 0.0), (0.1, -0.05), (0.03, -0.1), (-0.06, -0.17), (-0.22, -0.29), (-0.38, -0.3), (-0.48, -0.14)]


LIVER_SOCKET = (-13.0, 3.5)
LIVER_SOCKET_MM = (-50.0, 12.0)        # 真实肝网格上凸台的位置（毫米，乘零件比例）
LIVER_DEPTH = 0.42                      # 肝前后方向的厚度压到多少


def p04_liver(K, big=False):
    """玻璃肝（复合件，透明壳和红血管同时长）：外壳是真实的肝网格，淡红通透玻璃；里面是实色红的肝内血管树
    （门静脉、肝动脉、肝静脉）。右叶上有给 CDK20 定位销用的玻璃凸台和孔。3 个浇口。
    big=True 是大板上的主角尺寸，占 2 × 2 格；默认是一格大小。前后方向的厚度按 DEPTH 压过（真肝前后有 16 cm，原样放不进板）。"""
    import numpy as np
    P = Part(K, "p04_liver", "organ")
    v, f = organ("liver"); vv, vf = organ("vessel")
    k = 0.47 if big else 0.214
    s = (k, k, k * LIVER_DEPTH)
    shell = P.mesh(v, f, K.organ if big else K.organ_m, s)
    P.mesh(vv, vf, K.red, s)
    sx, sy = LIVER_SOCKET_MM[0] * k, LIVER_SOCKET_MM[1] * k
    w = v * np.array(s)
    top = float(w[np.hypot(w[:, 0] - sx, w[:, 1] - sy) < 4.5, 2].max())
    bpy.ops.mesh.primitive_cylinder_add(radius=2.3 * MM, depth=0.2, vertices=40, location=(sx * MM, sy * MM, 0))
    c = bpy.context.object; c.hide_render = c.hide_viewport = True; c.parent = P.root; c.name = "p04_liver_hole"
    bo = shell.modifiers.new("hole", "BOOLEAN"); bo.object = c; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
    P.ring(sx, sy, 4.4, 2.3, 3.2, K.organ_s, z=top - 0.2, bevel=0.5)
    organ_gates(P, v, s, ("-x", "+x", "-y"))
    if big:
        P.root["span"] = (2, 2)
    P.root["socket"] = (sx, sy, top + 1.4)
    return P.done()


def p05_lung_gut(K):
    """肺和肠：真实网格。左右两肺（五叶）是淡红玻璃，里面的气管和支气管树是实色红；结肠加直肠也是淡红玻璃。和肝同一种材质。"""
    P = Part(K, "p05_lung_gut", "organ"); g = K.organ_s
    v, f = organ("lung"); av, af = organ("airway")
    k = 0.098; s = (k, k, k * 0.6)
    P.at(-13.5, -2.0)
    P.mesh(v, f, g, s); P.mesh(av, af, K.red, s)
    organ_gates(P, v, s, ("-x",))
    v, f = organ("colon")
    k = 0.097; s = (k, k, k * 0.6)
    P.at(14.0, 0.0)
    P.mesh(v, f, g, s)
    organ_gates(P, v, s, ("+x",))
    P.at()
    return P.done()


def p06_globe(K):
    """地球仪：球面上的陆地是真实海岸线（Natural Earth 1:10m 的陆地栅格，kit_data.json 的 LAND），高出海面 0.45 mm；
    朝观众的一面是亚洲和太平洋。地轴斜 23°，外面一道弧形支架和底座。"""
    import base64
    import numpy as np
    P = Part(K, "p06_globe", "white"); m = K.white
    cx, cy, R, tilt = 0.0, 2.8, 10.0, math.radians(-23)
    L = DATA["LAND"]
    mask = np.unpackbits(np.frombuffer(base64.b64decode(L["bits"]), dtype=np.uint8))[: L["w"] * L["h"]].reshape(L["h"], L["w"]).astype(float)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1.0, location=(0, 0, 0))
    o = bpy.context.object; o.name = P.nm("globe"); me = o.data
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    lat = np.degrees(np.arcsin(np.clip(co[:, 1], -1, 1))); lon = (np.degrees(np.arctan2(co[:, 0], co[:, 2])) + 115.0 + 180.0) % 360.0 - 180.0
    px = np.clip(((lon + 180.0) / 360.0 * L["w"]).astype(int), 0, L["w"] - 1); py = np.clip(((90.0 - lat) / 180.0 * L["h"]).astype(int), 0, L["h"] - 1)
    co *= ((R + 0.45 * mask[py, px]) * MM)[:, None]
    me.vertices.foreach_set("co", co.ravel()); me.update()
    o.matrix_world = Matrix.Translation((cx * MM, cy * MM, 0)) @ Matrix.Rotation(tilt, 4, "Z")
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.data.materials.append(K.land); o.parent = P.root
    tri = np.empty(len(me.polygons) * 3, dtype=np.int64); me.polygons.foreach_get("vertices", tri)
    me.polygons.foreach_set("material_index", (mask[py, px][tri.reshape(-1, 3)].mean(1) > 0.5).astype(np.int32))      # 陆地用浅暖灰，和骨白的海分开
    ax = (math.sin(-tilt), math.cos(tilt))                     # 地轴方向（板面内）
    a_top = 90 + math.degrees(tilt)
    P.tube(arc(cx, cy, R + 2.4, a_top, a_top + 215, 40), 1.0, m)
    for sgn in (1, -1):
        P.ball(cx + sgn * ax[0] * (R + 1.5), cy + sgn * ax[1] * (R + 1.5), 0, 1.1, m, seg=16)
    P.tube([(0, cy - R - 2.4), (0, -14.0)], 1.3, m)
    P.lathe([(0.02, -16.0), (7.0, -16.0), (7.0, -15.0), (2.2, -13.4), (0.02, -13.4)], m, 0, 0)
    P.gate(-6.9, -15.5, "-x"); P.gate(6.9, -15.5, "+x")
    return P.done()


HK_LAND = [
    [(8, 22), (10, 27), (15, 30), (20, 33), (27, 36), (33, 37), (38, 35), (41, 32), (39, 28), (34, 27), (36, 24), (42, 26), (46, 24),
     (47, 19), (44, 15), (41, 16), (39, 12), (36, 14), (33, 13), (30, 12), (27, 14), (24, 17), (19, 18), (14, 19), (10, 19)],
    [(2, 10), (6, 14), (11, 15), (16, 13), (18, 10), (14, 8), (11, 5), (6, 5), (2, 7)],
    [(24, 9), (28, 10.5), (33, 10), (36, 8), (34, 5), (30, 4), (26, 5), (23, 7)],
]


def p07_hk_map(K):
    """香港地图片：轮廓是 Natural Earth 1:10m 的公开边界（kit_data.json 的 HK）。海面印细横线，陆地高出 3.4 mm。"""
    P = Part(K, "p07_hk_map", "white"); m = K.white
    P.box(0, 0, 25, 16.5, 1.6, m, r=2.0)
    polys = DATA["HK"]
    xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = min(44.0 / (max(xs) - min(xs)), 29.0 / (max(ys) - min(ys)))
    for i in range(13):
        P.inkbox(0, -14.4 + 2.4 * i, 23.0, 0.12, K.inkg, 0.8)
    for poly in polys:
        P.slab([((x - mx) * k + 1.5, (y - my) * k - 0.6) for x, y in poly], 3.4, m, z=0.8 + 1.7, bevel=0.5)
    P.box(-16.0, 12.6, 8.2, 2.5, 1.2, m, z=0.8 + 0.6, r=1.0, bevel=0.3)
    P.text("Hong Kong", 3.5, -16.0, 12.5, 2.0, K.ink, italic=True)
    P.gate(-25, 0, "-x"); P.gate(25, 0, "+x")
    return P.done()


def capsule(P, x, y, K, L=15.0, r=4.2):
    P.cyl(x, y, 0, r, L, K.white, axis="x", bevel=0)
    P.ball(x - L / 2, y, 0, r, K.white); P.ball(x + L / 2, y, 0, r, K.white)
    P.cyl(x, y, 0, r + 0.35, 3.2, K.gold, axis="x", bevel=0.25)
    P.gate(x - L / 2 - r + 0.3, y, "-x")


def p08_capsule(K):
    P = Part(K, "p08_capsule", "white")
    for y in (11.0, 0, -11.0):
        capsule(P, 0, y, K)
    return P.done()


def p09_iv_bag(K):
    P = Part(K, "p09_iv_bag", "clear"); m = K.clear0
    P.box(0, 2.5, 9.5, 10.5, 7.0, m, r=3.0, bevel=2.6)
    P.slab(rrect(0, 0.6, 8.2, 7.6, 2.4), 5.0, K.liq_blue, z=0, bevel=2.0)        # 袋里淡蓝的药液
    P.slab(rrect(0, 14.3, 3.2, 1.9, 1.2), 2.0, m, holes=[(0, 14.6, 1.0)])
    P.cyl(0, -9.2, 0, 1.3, 3.0, m, axis="y")
    P.cyl(0, -12.3, 0, 2.0, 3.6, m, axis="y")
    P.tube([(0, -14), (0, -16)], 0.6, m)
    for i in range(4):
        P.inkbox(6.2, 8.5 - i * 3.2, 1.6, 0.25, K.ink, 3.5)
    P.gate(-9.3, 2.5, "-x"); P.gate(9.3, 2.5, "+x")
    return P.done()


def p10_calendar(K):
    P = Part(K, "p10_calendar", "green"); m = K.green
    P.box(0, 5.2, 10.5, 10.2, 3.0, m, r=1.6)
    P.box(0, 12.8, 10.5, 2.6, 4.2, m, r=1.4)
    for s in (-1, 1):
        P.cyl(s * 5.2, 15.0, 1.6, 1.0, 3.2, m, axis="y", bevel=0.3)
    for j in range(3):
        for i in range(4):
            P.inkbox((i - 1.5) * 4.7, 7.8 - j * 4.4, 1.5, 1.4, K.inkw, 1.5)
    P.box(0, -12.2, 25, 2.8, 2.4, m, r=1.0)
    for i in range(11):
        P.inkbox(-22.5 + 4.5 * i, -11.2 - (0.0 if i % 5 == 0 else 0.5), 0.28, 1.7 if i % 5 == 0 else 1.0, K.inkw, 1.2)
    P.gate(-10.3, 5.2, "-x"); P.gate(10.3, 5.2, "+x"); P.gate(-25, -12.2, "-x")
    return P.done()


def p11_bill(K):
    P = Part(K, "p11_bill", "green"); m = K.green
    P.box(0, 0, 22, 10.5, 2.0, m, r=1.4)
    P.slab(rrect(0, 0, 20, 8.5, 1.0), 2.6, m, bevel=0.3)
    P.box(0, 0, 18.6, 7.1, 2.0, m, r=0.8, bevel=0.2)
    P.disc(0, 0, 5.0, 3.2, m, bevel=0.6)
    P.text("$", 7.5, 0, -0.2, 1.6, K.inkw)
    for sx in (-1, 1):
        P.disc(sx * 13.5, 0, 1.9, 2.8, m, bevel=0.4)
    P.gate(-22, 0, "-x"); P.gate(22, 0, "+x")
    return P.done()


def p12_medal(K):
    P = Part(K, "p12_medal", "gold"); m = K.gold
    cy = -4.5
    for s in (-1, 1):
        P.slab([(s * 2.4, cy + 9.0), (s * 9.5, 16.0), (s * 4.6, 16.0), (-s * 1.0, cy + 10.5)], 1.6, m, z=-0.6, bevel=0.3)
    P.disc(0, cy, 11.0, 3.0, m, bevel=0.8)
    P.torus(0, cy, 1.5, 9.9, 0.8, m)
    bust = [(-5, -8), (-4, -3), (-6, 1), (-5, 6), (-1, 9), (3, 8), (5, 5), (5, 2), (7, 0), (5, -1), (5, -3), (3, -5), (3, -8)]
    P.slab(smooth_loop([(x * 0.78, y * 0.78 + cy - 0.3) for x, y in bust], 5), 1.3, m, z=1.5 + 0.6, bevel=0.5)
    P.torus(0, cy + 11.4, 0, 1.6, 0.55, m)
    P.gate(-11, cy, "-x"); P.gate(11, cy, "+x")
    return P.done()


def p13_chip(K, label="AI"):
    P = Part(K, "p13_chip", "black"); m = K.black
    for i in range(6):
        t = -8.75 + 3.5 * i
        for s in (-1, 1):
            P.box(s * 12.6, t, 1.8, 0.85, 1.2, m, r=0.3, bevel=0.2)
            P.box(t, s * 12.6, 0.85, 1.8, 1.2, m, r=0.3, bevel=0.2)
    P.box(0, 0, 11.2, 11.2, 4.0, m, r=1.4, bevel=0.7)
    P.box(0, 0, 8.6, 8.6, 0.8, m, z=2.4, r=0.8, bevel=0.3)
    P.text(label, 3.0 if len(label) > 9 else 3.6 if len(label) > 3 else 6.0, 0, -0.1, 2.8, K.inkw)
    P.cyl(-9.6, 9.6, 2.05, 0.7, 0.3, K.inkw, bevel=0)
    P.gate(-14.2, 1.75, "-x"); P.gate(14.2, -1.75, "+x")
    return P.done()


def p14_buildings(K):
    P = Part(K, "p14_buildings", "white"); m = K.white
    P.at(-18, 0)                                    # 大学：台阶、四根柱子、三角山墙
    P.box(0, -5.0, 7.2, 7.0, 6.0, m, z=-1.0, r=0.3, bevel=0.2)
    P.box(0, -13.0, 8.4, 1.3, 9.0, m, r=0.4, bevel=0.3)
    for x in (-5.4, -1.8, 1.8, 5.4):
        P.box(x, -5.0, 1.0, 6.8, 8.0, m, r=0.9, bevel=0.6)
    P.box(0, 2.9, 8.2, 1.1, 9.0, m, r=0.3, bevel=0.3)
    P.slab([(-8.6, 4.0), (8.6, 4.0), (0, 10.5)], 9.0, m, bevel=0.5)
    P.gate(0, -14.2, "-y")
    P.at(0, 0)                                      # 医院：方楼、十字、窗、门
    P.box(0, -2.8, 7.5, 11.5, 9.0, m, r=0.8)
    P.inkbox(0, 4.6, 2.7, 0.95, K.ink, 4.5); P.inkbox(0, 4.6, 0.95, 2.7, K.ink, 4.5)
    for x in (-3.8, 3.8):
        for y in (-1.8, -6.0, -10.2):
            P.inkbox(x, y, 1.4, 1.2, K.ink, 4.5)
    P.inkbox(0, -11.6, 1.3, 2.6, K.ink, 4.5)
    P.gate(0, -14.2, "-y")
    P.at(18, 0)                                     # 科学园：高塔、矮楼、圆顶
    P.box(-3.6, -1.2, 3.6, 13.0, 9.0, m, r=0.8)
    for y in (8.0, 4.4, 0.8, -2.8, -6.4, -10.0):
        P.inkbox(-3.6, y, 2.3, 0.7, K.ink, 4.5)
    P.disc(4.2, -5.6, 4.0, 7.6, m, bevel=0.8)
    P.box(4.2, -9.8, 4.2, 4.4, 8.0, m, r=0.6)
    P.inkbox(4.2, -11.4, 2.6, 1.0, K.ink, 4.0)
    P.tube([(-3.6, 11.8), (-3.6, 15.6)], 0.5, m)
    P.gate(0, -14.2, "-y")
    P.at()
    return P.done()


def p15_sample_tube(K):
    P = Part(K, "p15_sample_tube", "clear")
    for ox in (-13, 0, 13):
        P.at(ox, 0)
        P.lathe([(0.02, -14.0), (2.0, -13.5), (3.2, -12.2), (3.6, -10.4), (3.6, 8.0), (0.02, 8.0)], K.clear0, 0, 0)
        P.lathe([(0.02, -13.0), (1.6, -12.6), (2.5, -11.6), (2.8, -10.2), (2.8, -3.0), (0.02, -3.0)], K.liquid, 0, 0)
        P.cyl(0, 10.4, 0, 4.3, 5.0, K.clear0, axis="y", bevel=0.6)
        P.gate(0, -13.8, "-y")
    P.at()
    return P.done()


def p16_plate(K, label="Case study", w=44.0, italic=True):
    P = Part(K, "p16_plate", "white")
    P.box(0, 0, w / 2, 7.0, 2.8, K.white, r=1.8, bevel=0.6)
    P.text(label, 7.6 if len(label) < 12 else 6.0, 0, -0.3, 1.4, K.ink, italic=italic)
    P.gate(-w / 2, 0, "-x"); P.gate(w / 2, 0, "+x")
    return P.done()


def p17_paper_book(K):
    P = Part(K, "p17_paper_book", "white"); m = K.white
    P.at(-15, 0)
    P.box(0.9, -0.9, 8.8, 12.4, 0.8, m, z=-0.5, r=0.4, bevel=0.2)
    P.box(0, 0, 8.8, 12.4, 1.2, m, z=0.4, r=0.4, bevel=0.2)
    P.inkbox(-1.6, 9.0, 5.4, 1.0, K.ink, 1.0)
    for i in range(4):
        P.inkbox(0, 5.6 - 1.9 * i, 6.8, 0.32, K.inkg, 1.0)
    P.inkbox(-3.2, -6.2, 3.4, 3.4, K.inkg, 1.0)
    for i in range(4):
        P.inkbox(4.0, -3.6 - 1.8 * i, 2.8, 0.32, K.inkg, 1.0)
    P.gate(-8.8, 0, "-x")
    P.at(12, 0)
    P.box(0, -0.4, 13.2, 10.2, 1.6, m, z=-0.7, r=1.0, bevel=0.4)
    for s in (-1, 1):
        P.box(s * 6.3, 0, 5.9, 9.2, 3.2, m, z=1.0, r=1.2, bevel=1.2)
        for i in range(6):
            P.inkbox(s * 6.3, 5.6 - 2.2 * i, 3.9, 0.3, K.inkg, 2.6)
    P.gate(13.2, -0.4, "+x")
    P.at()
    return P.done()


def p18_loupe_checklist(K):
    P = Part(K, "p18_loupe_checklist", "black"); m = K.black
    P.at(-13.5, 0)
    P.ring(0, 5.0, 9.6, 7.4, 3.6, m, bevel=0.8)
    P.box(0, -5.2, 2.5, 1.1, 4.2, m, r=0.5, bevel=0.4)
    P.box(0, -10.6, 1.9, 5.2, 3.6, m, r=1.6, bevel=0.9)
    P.gate(-9.5, 5.0, "-x")
    P.at(13.5, 0)
    P.box(0, -1.2, 9.6, 13.2, 2.4, m, r=1.5)
    P.slab(rrect(0, -2.2, 8.0, 11.0, 0.6), 0.5, K.inkw, z=1.45, bevel=0)
    P.box(0, 11.6, 4.2, 1.8, 3.8, m, r=0.8, bevel=0.5)
    for i in range(4):
        y = 5.0 - 4.6 * i
        P.slab([(-6.8, y + 0.1), (-5.9, y - 1.2), (-3.6, y + 1.5), (-4.1, y + 1.9), (-5.9, y - 0.2), (-6.3, y + 0.5)], 0.3, K.ink, z=1.85, bevel=0)
        P.inkbox(1.8, y, 4.4, 0.4, K.ink, 1.7)
    P.gate(9.6, -1.2, "+x")
    P.at()
    return P.done()


def p19_cdk20(K):
    P = Part(K, "p19_cdk20", "blue")
    cdk20_body(P, K.blue)
    return P.done()


def p20_pocket(K, with_key=False):
    """CDK20 的口袋近景件：两叶之间一道开口，里面是放钥匙的腔；腔底一块凸起的亮蓝卡扣是铰链位（hinge）。"""
    P = Part(K, "p20_pocket", "blue"); m = K.blue
    cx = -5.0 if with_key else 2.0
    P.at(cx, 0)
    a = math.degrees(math.asin(2.6 / 6.4))
    body = [(17, 2.6)] + arc(-1, 0, 6.4, a, 360 - a, 28) + [(17, -2.6), (17, -11), (14, -14), (-18, -14), (-21, -11), (-21, 11), (-18, 14), (14, 14), (17, 11)]
    P.slab(body, 6.0, m, bevel=0.9)
    P.slab(smooth_loop([(-9, 6.5), (-4, 11.5), (6, 12), (14, 9.5), (14.5, 5.2), (7, 7.2), (-2, 8.4)]), 1.6, m, z=3.0 + 0.6, bevel=0.6)      # N 叶
    P.slab(smooth_loop([(-9, -6.5), (-2, -8.6), (7, -7.4), (14.5, -5.2), (14, -10.5), (6, -12.4), (-4, -11.8)]), 2.2, m, z=3.0 + 0.9, bevel=0.7)   # C 叶
    P.box(-9.6, 0, 1.9, 4.6, 3.4, K.blue_hi, z=3.0 + 1.7, r=0.9, bevel=0.6)      # 卡扣
    P.box(-8.2, 0, 0.9, 2.4, 1.2, K.blue_hi, z=3.0 + 3.4 + 0.6, r=0.5, bevel=0.3)
    P.text("hinge", 4.6, -16.2, 0, 3.0, K.inkw, italic=True, rot=90)
    P.gate(-21, 0, "-x"); P.gate(0, -14, "-y"); P.gate(0, 14, "+y")
    P.at()
    if with_key:
        key_shape(P, cx + 2.0, -0.2, 0.42, K.gold, seed=48)
    return P.done()


def p21_lock(K):
    P = Part(K, "p21_lock", "blue"); m = K.blue
    P.tube([(-6, -2), (-6, 8.5)] + arc(0, 8.5, 6, 180, 0, 20) + [(6, -2)], 1.9, m)
    P.box(0, -5.5, 10.5, 9.0, 7.0, m, r=2.2, bevel=1.3)
    P.cyl(0, -3.6, 3.65, 2.1, 0.3, K.ink, bevel=0)
    P.slab([(-0.8, -4.2), (0.8, -4.2), (1.4, -9.2), (-1.4, -9.2)], 0.3, K.ink, z=3.65, bevel=0)
    P.gate(-10.5, -5.5, "-x"); P.gate(10.5, -5.5, "+x")
    return P.done()


def p22_key(K, seed=1):
    P = Part(K, "p22_key", "gold")
    key_shape(P, -9.0, 0.6, 0.62, K.gold, seed=seed)
    P.gate(-24.3, 0.6, "-x"); P.gate(22.0, 1.0, "+x")
    return P.done()


def cell(P, K, ox, kind, r=10.5):
    P.at(ox, 0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r * MM, location=(ox * MM, 0, 0))
    c = bpy.context.object; c.name = P.nm("cell"); c.scale = (1, 1, 0.9)
    tx = bpy.data.textures.new(c.name, "CLOUDS"); tx.noise_scale = 0.006
    dm = c.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.0012
    bpy.ops.object.shade_smooth(); c.data.materials.append(K.cellpink if kind == "cancer" else K.clear0); c.parent = P.root
    P.ball(1.5, 1.2, 0.4, 3.7, K.nuc_red if kind == "cancer" else K.nuc_grey, sc=(1, 1, 0.8))
    if kind == "cancer":
        for x, y in ((-5.0, -2.5), (-2.5, 5.5), (5.6, -3.6)):
            P.ball(x, y, 0.5, 1.15, K.blue, seg=16)
    P.gate(0, -r + 0.6, "-y")
    P.at()


def p23_cell(K, kind="both"):
    P = Part(K, "p23_cell", "clear")
    if kind == "both":
        cell(P, K, -12.5, "cancer"); cell(P, K, 12.5, "control")
    else:
        cell(P, K, 0, kind, r=13.0)
    return P.done()


def p24_atp(K):
    """ATP：真实结构（腺嘌呤、核糖、三个磷酸），坐标由 RDKit 从 SMILES 生成；磷原子的球大一号。"""
    P = Part(K, "p24_atp", "clear"); m = K.yellow
    xyz = mol_part(P, "ATP", 3.3, m, 1.9, 0.9, big=("P",))
    l = min(xyz, key=lambda p: p[0]); r = max(xyz, key=lambda p: p[0])
    P.gate(l[0] - 1.0, l[1], "-x", l[2]); P.gate(r[0] + 1.0, r[1], "+x", r[2])
    return P.done()


def p25_tumour_chips(K):
    """52 片肿瘤样本小方片：36 片红、16 片白，挂在四根细料条上。"""
    P = Part(K, "p25_tumour_chips", "red")
    rnd = random.Random(52)
    white = set(rnd.sample(range(52), 16))
    for j in range(4):
        y = (1.5 - j) * 7.4
        P.tube([(-25.4, y, -0.4), (25.4, y, -0.4)], 0.5, K.white)
        for i in range(13):
            P.box((i - 6) * 3.9, y, 1.6, 2.6, 1.8, K.white if j * 13 + i in white else K.red, r=0.4, bevel=0.35)
    for s in (-1, 1):
        P.tube([(s * 25.4, 11.1, -0.4), (s * 25.4, -11.1, -0.4)], 0.5, K.white)
    P.gate(-25.4, 0, "-x"); P.gate(25.4, 0, "+x")
    return P.done()


def p26_survival(K):
    P = Part(K, "p26_survival", "white")
    P.box(0, 0, 21, 14.5, 2.0, K.white, r=1.6)
    P.inkbox(-16, 0, 0.3, 11.3, K.ink, 1.0); P.inkbox(0, -11, 16.3, 0.3, K.ink, 1.0)
    z = 1.6
    P.tube([(x, y, z) for x, y in ((-16, 10), (-10, 10), (-10, 8.2), (-3, 8.2), (-3, 6.4), (5, 6.4), (5, 5.0), (15, 5.0))], 0.55, K.ink)
    P.tube([(x, y, z) for x, y in ((-16, 10), (-12, 10), (-12, 5), (-7, 5), (-7, 0.5), (-1, 0.5), (-1, -3.5), (6, -3.5), (6, -7), (15, -7))], 0.7, K.red)
    P.gate(-21, 0, "-x"); P.gate(21, 0, "+x")
    return P.done()


def p27_data_disks(K):
    P = Part(K, "p27_data_disks", "black"); m = K.black
    P.box(0, 0, 25, 11, 1.6, m, r=2.0)
    for i in range(5):
        for s in (-1, 1):
            for k in range(3):
                P.cyl((i - 2) * 10, s * 5.4, 0.8 + 1.1 + 2.7 * k, 4.2, 2.2, m, bevel=0.5)
            P.cyl((i - 2) * 10, s * 5.4, 4.0, 3.4, 6.0, m, bevel=0)
    P.gate(-25, 0, "-x"); P.gate(25, 0, "+x")
    return P.done()


def p28_top20(K):
    P = Part(K, "p28_top20", "white")
    P.box(0, 0, 22, 15.5, 2.0, K.white, r=1.6)
    P.text("Top 20", 4.2, 0, 12.2, 1.0, K.ink, italic=True)
    rnd = random.Random(20)
    for c in range(2):
        x0 = -11 + 22 * c
        for i in range(10):
            y = 8.2 - 2.3 * i
            hot = (c == 0 and i == 3)
            if hot:
                P.slab(rrect(x0, y, 9.8, 1.0, 0.5), 0.9, K.blue, z=1.0 + 0.45, bevel=0.2)
                continue
            P.inkbox(x0 - 8.4, y, 0.5, 0.5, K.ink, 1.0)
            w = rnd.uniform(4.2, 7.4)
            P.inkbox(x0 - 7.0 + w, y, w, 0.36, K.inkg, 1.0)
    P.gate(-22, 0, "-x"); P.gate(22, 0, "+x")
    return P.done()


def p29_cdk20_unknown(K):
    P = Part(K, "p29_cdk20_unknown", "clear")
    cdk20_body(P, K.frost, peg=False)
    return P.done()


def p30_aa_chain(K):
    P = Part(K, "p30_aa_chain", "blue"); m = K.blue
    pts = [(-22 + 44 * u, 7.5 * math.sin(2 * math.pi * 1.25 * u)) for u in [i / 12 for i in range(13)]]
    P.tube(pts, 0.9, m, smooth=True)
    for i, (x, y) in enumerate(pts):
        k = i % 4
        if k == 0:
            P.ball(x, y, 0, 2.7, m)
        elif k == 1:
            P.box(x, y, 2.3, 2.3, 4.6, m, r=0.7, bevel=0.6)
        elif k == 2:
            P.slab(ngon(x, y, 2.9, 6, 0), 4.2, m, bevel=0.6)
        else:
            P.cyl(x, y, 0, 2.5, 4.4, m, bevel=0.6)
    P.gate(-24.5, 0, "-x"); P.gate(24.5, 7.5, "+x")
    return P.done()


def p31_tail(K):
    P = Part(K, "p31_tail", "blue"); m = K.tail
    path = [(-21, -5), (-16, 6), (-10, -8), (-4, 7), (2, -9), (8, 8), (13, -6), (18, 5), (22, -2), (23.5, 7)]
    P.tube(path, 1.7, m, smooth=True)
    P.ball(23.5, 7, 0, 2.3, m)
    P.box(-22.5, -6.5, 2.8, 2.8, 5.0, K.blue, r=1.0, bevel=0.8)        # 接到 CDK20 的那一头是实色
    P.gate(-25.3, -6.5, "-x")
    return P.done()


def p32_nippers(K):
    P = Part(K, "p32_nippers", "black"); m = K.black
    for s in (1, -1):
        P.slab([(-25, 6.2 * s), (-24.4, 10.4 * s), (-6, 5.6 * s), (3, 4.6 * s), (3, 0.6 * s), (-6, 1.9 * s)], 3.0, m, bevel=0.6)
        P.slab(smooth_loop([(-26, 6.0 * s), (-25.2, 11.6 * s), (-18, 10.0 * s), (-10.5, 7.9 * s), (-11.2, 3.2 * s), (-18, 4.4 * s)], 4), 4.6, m, bevel=1.2)
        P.slab([(1, 0.25 * s), (13.5, 0.25 * s), (15.5, 1.6 * s), (9.0, 7.2 * s), (1, 5.6 * s)], 3.4, m, bevel=0.7)
    P.cyl(3.6, 0, 0, 3.1, 4.8, m, bevel=0.6)
    P.cyl(3.6, 0, 2.5, 1.1, 0.4, K.inkw, bevel=0)
    P.gate(-24.6, 9.0, "-x"); P.gate(-24.6, -9.0, "-x")
    return P.done()


def p33_db_rack(K):
    P = Part(K, "p33_db_rack", "black"); m = K.black
    for ox in (-11, 11):
        P.at(ox, 0)
        P.box(0, 0, 8.6, 15.2, 6.0, m, r=1.2, bevel=0.7)
        for i in range(5):
            y = 11.4 - 5.7 * i
            P.box(0, y, 7.0, 2.2, 1.0, m, z=3.4, r=0.5, bevel=0.3)
            P.cyl(-5.2, y, 4.0, 0.55, 0.3, K.inkw, bevel=0); P.cyl(-3.4, y, 4.0, 0.55, 0.3, K.inkw, bevel=0)
            P.inkbox(2.6, y, 3.0, 0.3, K.inkg, 3.9)
        P.gate(-8.6 if ox < 0 else 8.6, 0, "-x" if ox < 0 else "+x")
    P.at()
    return P.done()


def p34_flask(K):
    P = Part(K, "p34_flask", "clear")
    P.lathe([(0.02, -11.5), (8.4, -11.5), (9.4, -10.6), (9.4, -9.6), (2.7, 3.6), (2.7, 11.0), (3.5, 11.5), (3.5, 12.6), (0.02, 12.6)], K.clear0, 0, 0)
    P.lathe([(0.02, -10.7), (7.8, -10.7), (8.4, -9.8), (5.4, -3.8), (0.02, -3.8)], K.liquid, 0, 0)
    for i in range(3):
        P.inkbox(0, -6.0 + 3.0 * i, 2.0 - 0.45 * i, 0.22, K.ink, 9.4 - (3.6 + 3.0 * i) * 0.508 + 0.05)
    P.gate(-9.2, -10.2, "-x"); P.gate(9.2, -10.2, "+x")
    return P.done()

LOOP_WORDS = ["Imagine", "Make", "Test", "Change"]


def p35_loop(K):
    P = Part(K, "p35_loop", "white"); m = K.white
    P.ring(0, 0, 11.4, 8.6, 1.4, m, bevel=0.4)
    for q in range(4):
        a0, a1 = -(q * 90 - 60), -(q * 90 + 0)          # 顺时针
        outer = [(12.6 * math.cos(math.radians(a)), 12.6 * math.sin(math.radians(a))) for a in [a0 + (a1 - a0) * k / 12 for k in range(13)]]
        inner = [(7.8 * math.cos(math.radians(a)), 7.8 * math.sin(math.radians(a))) for a in [a1 + (a0 - a1) * k / 12 for k in range(13)]]
        pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
        P.slab(outer + [pol(14.6, a1), pol(10.2, a1 - 20), pol(5.8, a1)] + inner, 3.0, m, bevel=0.6)
    for (sx, sy), w in zip(((-1, 1), (1, 1), (1, -1), (-1, -1)), LOOP_WORDS):
        P.box(sx * 19.0, sy * 13.0, 7.0, 2.8, 1.8, m, r=1.2, bevel=0.4)
        P.text(w, 3.6, sx * 19.0, sy * 13.0 - 0.1, 0.9, K.ink, italic=True)
        P.gate(sx * 26.0, sy * 13.0, "+x" if sx > 0 else "-x")
    P.gate(0, -11.3, "-y")
    return P.done()


def p36_sieve(K):
    P = Part(K, "p36_sieve", "black"); m = K.black
    cx, R = -4.0, 11.6
    P.ring(cx, 0, 13.4, R, 5.0, m, bevel=0.9)
    for k in range(-4, 5):
        t = k * 2.5
        h = math.sqrt((R + 0.6) ** 2 - t * t)
        P.tube([(cx + t, -h, -1.2), (cx + t, h, -1.2)], 0.32, m)
        P.tube([(cx - h, t, -1.2), (cx + h, t, -1.2)], 0.32, m)
    P.slab(rrect(15.5, 0, 7.4, 2.0, 1.8), 3.0, m, bevel=0.8, holes=[(20, 0, 0.9)])
    P.gate(cx - 13.3, 0, "-x"); P.gate(22.8, 0, "+x")
    return P.done()


def mini_key(P, x, y, up, m, seed):
    """一把竖着的小钥匙（长 7.2 mm）：圆柄带孔、杆、一排齿。up=1 柄在下、尖朝上。"""
    rnd = random.Random(seed)
    P.ring(x, y, 1.75, 0.7, 1.1, m, bevel=0.25, n=32)
    pts = [(-0.55, 1.4), (-0.55, 5.0), (-0.15, 5.5), (0.55, 5.5)]
    for i in range(3):
        t = rnd.choice((0.55, 0.85, 1.15)); y0 = 4.6 - 1.05 * i
        pts += [(0.55, y0 + 0.2), (0.55 + t, y0 + 0.2), (0.55 + t, y0 - 0.45), (0.55, y0 - 0.45)]
    pts += [(0.55, 1.4)]
    P.slab([(x + px, y + up * py) for px, py in pts], 1.0, m, bevel=0.2)


def p37_key_heap(K):
    """小钥匙阵列（8,918 把那一堆的代表，成片时用实例铺）：6 × 4 整齐排在两根细料条上，每把齿形不同，互不相碰。"""
    P = Part(K, "p37_key_heap", "gold"); m = K.gold
    n = 0
    for rail in (8.0, -8.0):
        P.tube([(-25.0, rail), (25.0, rail)], 0.55, m)
        for up in (1, -1):
            for i in range(6):
                x = (i - 2.5) * 8.2
                mini_key(P, x, rail + up * 2.2, up, m, 8918 + n); n += 1
        P.gate(-25.0, rail, "-x"); P.gate(25.0, rail, "+x")
    return P.done()


def p38_dial(K, label="Score"):
    P = Part(K, "p38_dial", "black"); m = K.black
    cy = 3.0
    P.box(0, -12.6, 8.5, 2.9, 2.8, m, r=1.2, bevel=0.5)
    P.disc(0, cy, 12.6, 4.0, m, bevel=0.8)
    P.torus(0, cy, 2.0, 11.6, 0.8, m)
    pol = lambda r, a: (r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    for i in range(9):
        a = 210 - 30 * i
        r0 = 7.4 if i % 4 == 0 else 8.4
        P.slab([pol(r0, a - 2), pol(10.2, a - 1.6), pol(10.2, a + 1.6), pol(r0, a + 2)], 0.3, K.inkw, z=2.15, bevel=0)
    P.slab([pol(1.0, 150), pol(8.6, 62), pol(1.0, -30)], 0.5, K.inkw, z=2.35, bevel=0)
    P.cyl(0, cy, 2.6, 1.7, 1.2, m)
    P.text(label, 3.8, 0, -12.7, 1.4, K.inkw, italic=True)
    P.gate(-12.6, cy, "-x"); P.gate(12.6, cy, "+x")
    return P.done()


def molecule(P, key, K, s, ra, rb):
    """论文里的化合物（001 或 048）：按真实结构的原子坐标做球棍，香槟金电镀；下面挂一块缎面金的编号牌，深色字。"""
    xyz = mol_part(P, key, s, K.gold, ra, rb, cy=5.2)
    low = min((p for p in xyz if abs(p[0]) < 2.6 * s), key=lambda p: p[1])
    P.tube([low, (0, -7.6, 0)], rb * 1.15, K.gold)
    P.box(0, -11.2, 8.0, 3.6, 1.8, K.gold_satin, r=1.2, bevel=0.4)
    P.text(key, 6.0, 0, -11.35, 0.9, K.ink)
    P.gate(0, -14.8, "-y")


def p39_molecules(K, which="both"):
    P = Part(K, "p39_molecules", "gold")
    if which == "both":
        P.at(-13.5, 0); molecule(P, "001", K, 1.62, 0.95, 0.42)
        P.at(13.5, 0); molecule(P, "048", K, 1.62, 0.95, 0.42)
    else:
        molecule(P, which, K, 3.0, 1.45, 0.62)
    P.at()
    return P.done()


def p40_dish(K):
    P = Part(K, "p40_dish", "clear"); m = K.clear0
    P.ring(0, 0, 14.0, 12.8, 5.0, m, bevel=0.5)
    P.disc(0, 0, 14.0, 1.0, m, z=-2.0, bevel=0.3)
    P.disc(0, 0, 12.6, 2.2, K.dishpink, z=-0.4, bevel=0.3)
    rnd = random.Random(40)
    for _ in range(9):
        r = 9.5 * math.sqrt(rnd.random()); a = rnd.uniform(0, 6.28)
        P.ball(r * math.cos(a), r * math.sin(a), 0.3, rnd.uniform(0.9, 1.6), K.nuc_red, sc=(1, 1, 0.5), seg=16)
    P.gate(-14, 0, "-x"); P.gate(14, 0, "+x")
    return P.done()


def p41_then_now(K):
    P = Part(K, "p41_then_now", "white"); m = K.white
    P.box(0, 0, 25, 15.5, 1.6, m, r=2.0)
    P.box(0, -2.5, 0.8, 12.0, 3.4, m, z=0.9, r=0.6, bevel=0.4)
    for s, w in ((-1, "Before"), (1, "Now")):
        cx = s * 12.6
        for (x, y, hx, hy) in ((cx, 6.6, 10.4, 0.6), (cx, -13.0, 10.4, 0.6), (cx - 10.4, -3.2, 0.6, 10.4), (cx + 10.4, -3.2, 0.6, 10.4)):
            P.box(x, y, hx, hy, 2.4, m, z=0.8, r=0.5, bevel=0.4)
        P.text(w, 4.6, cx, 11.0, 0.8, K.ink, italic=True)
    P.gate(-25, 0, "-x"); P.gate(25, 0, "+x")
    return P.done()


def p42_bead_pile(K):
    P = Part(K, "p42_bead_pile", "white"); m = K.white
    P.box(0, 0, 22, 14, 1.2, m, z=-0.6, r=3.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.25 * MM, segments=16, ring_count=8)
    proto = bpy.context.object; bpy.ops.object.shade_smooth(); proto.data.materials.append(m)
    me = proto.data; bpy.data.objects.remove(proto)
    rnd = random.Random(42)
    for k in range(5):
        Rk = 11.0 - 2.4 * k
        z = 1.25 + 2.05 * k
        j = -8
        while j <= 8:
            y = j * 2.2
            i = -12
            while i <= 12:
                x = i * 2.55 + (1.27 if (j + k) % 2 else 0)
                if (x / (Rk * 1.6)) ** 2 + (y / Rk) ** 2 <= 1.0:
                    o = link(bpy.data.objects.new(P.nm("bead"), me), P.root)
                    o.location = ((x + rnd.uniform(-0.12, 0.12)) * MM, (y + rnd.uniform(-0.12, 0.12)) * MM, z * MM)
                i += 1
            j += 1
    P.gate(-22, 0, "-x"); P.gate(22, 0, "+x")
    return P.done()


def p43_mouse(K):
    P = Part(K, "p43_mouse", "white"); m = K.white
    P.tube([(-13, -2.5), (-18.5, -6.5), (-22.5, -3), (-24.5, 4.5)], 0.75, m, smooth=True)
    P.ball(-3, -1.5, 0, 8.0, m, sc=(1.4, 0.9, 0.72), seg=48)
    P.ball(9.5, -0.8, 0, 5.4, m, sc=(1.2, 0.92, 0.85), seg=48)
    P.ball(15.2, -2.0, 0, 2.6, m, sc=(1.5, 0.9, 0.9))
    P.ball(19.0, -2.4, 0, 1.0, K.ink, seg=16)
    P.cyl(6.6, 4.6, 2.2, 3.9, 1.5, m, bevel=0.6)
    P.cyl(11.4, 5.4, 0.2, 3.7, 1.5, m, bevel=0.6)
    P.ball(12.4, 0.6, 3.9, 0.85, K.ink, seg=16)
    for x, y in ((-9.5, -8.4), (0.5, -8.6), (8.5, -6.4)):
        P.ball(x, y, 0, 1.7, m, sc=(1.6, 0.7, 1.0), seg=16)
    P.gate(-3, -8.5, "-y"); P.gate(-1, 5.4, "+y")
    return P.done()


def p44_plug_bin(K):
    P = Part(K, "p44_plug_bin", "green"); g = K.green
    P.at(-18, 0)
    for s in (-1, 1):
        P.box(s * 2.7, 7.2, 0.9, 3.8, 1.6, g, r=0.5, bevel=0.3)
    P.box(0, -1.0, 5.8, 5.4, 5.0, g, r=1.8, bevel=1.0)
    P.box(0, -7.6, 2.2, 1.6, 3.6, g, r=0.8, bevel=0.5)
    P.tube([(0, -8.5), (0.3, -12), (2.5, -14.5), (5.5, -15)], 1.1, g, smooth=True)
    P.gate(-5.8, -1.0, "-x")
    P.at(-2.5, 0)
    P.slab([(2.2, 15), (-5.2, 0.4), (-0.8, 0.4), (-3.2, -15), (5.6, 2.4), (1.0, 2.4), (4.8, 15)], 3.0, g, bevel=0.6)
    P.gate(-3.0, -14.2, "-y")
    P.at(15.5, 0)
    k = K.black
    P.lathe([(0.02, -14.5), (5.0, -14.5), (5.5, -14.0), (6.9, 6.2), (0.02, 6.2)], k, 0, 0)         # 上大下小的圆桶
    for phi in range(-75, 76, 25):                                                                # 桶身一圈竖条纹
        sn, cs = math.sin(math.radians(phi)), math.cos(math.radians(phi))
        P.tube([(5.62 * sn, -13.0, 5.62 * cs), (6.82 * sn, 5.2, 6.82 * cs)], 0.5, k)
    P.lathe([(0.02, 6.2), (8.3, 6.2), (8.5, 6.6), (8.5, 7.8), (7.6, 8.8), (3.0, 9.6), (0.02, 9.7)], k, 0, 0)     # 盖子：比桶口大一圈，顶上微鼓
    P.tube([(-2.6, 9.2, 0)] + [(2.6 * math.cos(math.radians(a_)), 9.4 + 2.4 * math.sin(math.radians(a_)), 0) for a_ in range(180, -1, -20)] + [(2.6, 9.2, 0)], 0.6, k)   # 提手
    P.gate(6.6, -1.0, "+x")
    P.at()
    return P.done()


def p45_track(K):
    P = Part(K, "p45_track", "white"); m = K.white
    P.box(0, 0, 25, 12, 1.6, m, r=2.4)
    for y in (-10.2, 10.2):
        P.box(0, y, 23.5, 0.7, 1.6, m, z=1.2, r=0.6, bevel=0.4)
    for i in range(9):
        P.inkbox(-16 + 3.9 * i, 0, 1.2, 0.3, K.ink, 0.8)
    P.inkbox(-20, 0, 0.35, 9.0, K.ink, 0.8)
    for i in range(2):
        for j in range(12):
            if (i + j) % 2 == 0:
                P.inkbox(19.6 + 1.5 * i, -8.25 + 1.5 * j, 0.75, 0.75, K.ink, 0.8)
    for y in (-5.1, 5.1):
        P.slab([(-9, y - 0.8), (-2.5, y - 0.8), (-2.5, y - 2.2), (1.5, y), (-2.5, y + 2.2), (-2.5, y + 0.8), (-9, y + 0.8)], 0.3, K.inkg, z=0.95, bevel=0)
        P.box(8.5, y, 3.4, 1.9, 2.2, m, z=1.9, r=0.9, bevel=0.6)          # 两条道上各一辆小车
        P.box(8.0, y, 1.6, 1.4, 1.4, m, z=3.4, r=0.6, bevel=0.4)
    P.gate(-25, 0, "-x"); P.gate(25, 0, "+x")
    return P.done()


def p46_newspaper(K):
    P = Part(K, "p46_newspaper", "white"); m = K.white
    P.box(1.0, -1.0, 20, 14.6, 0.8, m, z=-0.5, r=0.4, bevel=0.2)
    P.box(0, 0, 20, 14.6, 1.2, m, z=0.4, r=0.4, bevel=0.2)
    P.text("Daily News", 4.8, 0, 11.0, 1.0, K.ink)
    P.inkbox(0, 8.0, 18, 0.22, K.ink, 1.0)
    P.text("AI discovers a cancer drug", 3.1, 0, 5.2, 1.0, K.ink, italic=True)
    P.inkbox(0, 2.6, 18, 0.12, K.ink, 1.0)
    P.inkbox(-9.6, -5.4, 8.0, 6.6, K.inkg, 1.0)
    for i in range(8):
        P.inkbox(9.0, 0.6 - 1.8 * i, 8.6 if i != 7 else 5.0, 0.28, K.inkg, 1.0)
    P.gate(-20, 0, "-x"); P.gate(20, 0, "+x")
    return P.done()

CATALOG = [   # (编号, 英文名, 生成)
    ("01", "Frame, runner, gate, tag", p01_frame), ("02", "Station plates", p02_stations), ("03", "Person", p03_person),
    ("04", "Liver", p04_liver), ("05", "Lungs, intestine", p05_lung_gut), ("06", "Globe", p06_globe),
    ("07", "Hong Kong map", p07_hk_map), ("08", "Capsules", p08_capsule), ("09", "IV bag", p09_iv_bag),
    ("10", "Calendar, year ruler", p10_calendar), ("11", "Banknote", p11_bill), ("12", "Nobel medal", p12_medal),
    ("13", "Chip", lambda K: p13_chip(K, "AlphaFold")), ("14", "Buildings", p14_buildings), ("15", "Sample tubes", p15_sample_tube),
    ("16", "Word plate", p16_plate), ("17", "Paper, book", p17_paper_book), ("18", "Magnifier, checklist", p18_loupe_checklist),
    ("19", "CDK20", p19_cdk20), ("20", "CDK20 pocket", p20_pocket), ("21", "Lock", p21_lock),
    ("22", "Key", p22_key), ("23", "Cells", p23_cell), ("24", "ATP", p24_atp),
    ("25", "Tumour samples (52)", p25_tumour_chips), ("26", "Survival curve", p26_survival), ("27", "Data disks", p27_data_disks),
    ("28", "Top-20 list", p28_top20), ("29", "CDK20, shape unknown", p29_cdk20_unknown), ("30", "Amino-acid chain", p30_aa_chain),
    ("31", "Low-confidence tail", p31_tail), ("32", "Nippers", p32_nippers), ("33", "Database racks", p33_db_rack),
    ("34", "Flask", p34_flask), ("35", "Loop", p35_loop), ("36", "Sieve", p36_sieve),
    ("37", "Small keys (8,918)", p37_key_heap), ("38", "Score dial", p38_dial), ("39", "Compounds 001, 048", p39_molecules),
    ("40", "Culture dish", p40_dish), ("41", "Before / now tray", p41_then_now), ("42", "Bead pile", p42_bead_pile),
    ("43", "Mouse", p43_mouse), ("44", "Plug, bolt, waste bin", p44_plug_bin), ("45", "Two-lane track", p45_track),
    ("46", "Headline", p46_newspaper),
]


# ---------------------------------------------------------------- 格子、浇口


def gate_geo(name, a, b, m, parent):
    """料杆 a → 零件 b（米）：远的先伸一段支杆，再接细锥，尖头在零件一侧（拔的时候在这里断）。"""
    a, b = Vector(a), Vector(b)
    if (b - a).length < 1e-5:
        return
    if (b - a).length > 0.006:
        mid = b - (b - a).normalized() * 0.0035
        cv = bpy.data.curves.new(name + "_spur", "CURVE"); cv.dimensions = "3D"
        sp = cv.splines.new("POLY"); sp.points.add(1)
        sp.points[0].co = (*a, 1); sp.points[1].co = (*mid, 1)
        cv.bevel_depth = 0.0011; cv.bevel_resolution = 5; cv.use_fill_caps = True
        o = link(bpy.data.objects.new(name + "_spur", cv), parent); o.data.materials.append(m)
        a = mid
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=0.0012, radius2=0.00045, depth=d.length, vertices=20, location=(a + b) / 2)
    o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = parent


def tube_w(name, pts, r, m, parent=None, cyclic=False):
    cv = bpy.data.curves.new(name, "CURVE"); cv.dimensions = "3D"
    sp = cv.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        p = tuple(p) + (0.0,) * (3 - len(p))
        sp.points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1)
    sp.use_cyclic_u = cyclic
    cv.bevel_depth = r * MM; cv.bevel_resolution = 6; cv.use_fill_caps = True
    o = link(bpy.data.objects.new(name, cv), parent)
    o.data.materials.append(m)
    return o


def make_cell(K, part, x, y, z=0.0, name="cell"):
    """一格：外圈一圈按类别上色的料杆，零件用自己登记的浇口挂在里面。x、y、z 是毫米。"""
    root = link(bpy.data.objects.new(name, None))
    m = K.cat(part["cat"])
    nx, ny = part.get("span", (1, 1))                  # 跨几格（肝是 2 × 2）；x、y 是左上那一格的中心
    hx, hy = CX + (nx - 1) * PX / 2, CY + (ny - 1) * PY / 2
    x, y = x + (nx - 1) * PX / 2, y - (ny - 1) * PY / 2
    tube_w(name + "_loop", rrect(0, 0, hx, hy, 5.0), R_LOOP, m, root, cyclic=True)
    part.parent = root
    for i, (gx, gy, d, gz) in enumerate(json.loads(part["gates"])):
        end = {"+x": (hx, gy), "-x": (-hx, gy), "+y": (gx, hy), "-y": (gx, -hy)}[d]
        gate_geo(f"{name}_g{i}", (end[0] * MM, end[1] * MM, 0), (gx * MM, gy * MM, gz * MM), m, root)
    root.location = (x * MM, y * MM, z * MM)
    return root


# ---------------------------------------------------------------- 场景


def scene_base(samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    r = sc.render
    r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 1080
    sc.cycles.samples = samples; sc.cycles.seed = 7; sc.cycles.use_denoising = True
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"; pr.get_devices()
    for d in pr.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = EXPO
    sc.cycles.caustics_refractive = True; sc.cycles.caustics_reflective = True
    sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16; sc.cycles.volume_bounces = 4
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(str(HDRI))
    N["Background"].inputs[1].default_value = 0.35
    L.new(env.outputs["Color"], N["Background"].inputs["Color"])
    return sc


def backdrop():
    m_bg = mat_solid("backdrop", "#F3EEE6", rough=0.45, coat=0.0, sss=0)
    prof = [(0, -2.5, 0)] + [(0, 0.9 + 0.35 * math.sin(math.radians(a)), 0.35 - 0.35 * math.cos(math.radians(a))) for a in range(0, 91, 5)] + [(0, 1.25, 2.0)]
    bm = bmesh.new()
    rows = [[bm.verts.new((x, p[1], p[2])) for p in prof] for x in (-3, 3)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new("sweep"); bm.to_mesh(me); bm.free()
    sw = link(bpy.data.objects.new("sweep", me))
    for p in me.polygons:
        p.use_smooth = True
    sw.data.materials.append(m_bg)


def lights(cx=0.0, cy=0.0, k=1.0):
    """和样片一 v4 同一套灯：主光、补光、顶上一条长灯、轮廓光，外加两块只给反射看的白卡（电镀件要映出亮的东西）。"""
    c = Vector((cx, cy, 0))
    for name, loc, size, energy, sy in (("key", (-0.7, -0.5, 0.9), 0.9, 120, None), ("fill", (0.8, -0.6, 0.35), 0.7, 25, None),
                                        ("strip", (0.0, -0.25, 0.75), 0.6, 45, 0.12), ("rim", (0.3, 0.5, 0.6), 0.5, 30, None)):
        loc = Vector(loc) * k
        bpy.ops.object.light_add(type="AREA", location=c + loc)
        o = bpy.context.object; o.name = name
        o.data.shape = "RECTANGLE"; o.data.size = size * k; o.data.size_y = (sy or size) * k; o.data.energy = energy * k * k; o.data.color = (1, 0.97, 0.93)
        o.rotation_euler = (-loc + Vector((0, 0, 0.08))).to_track_quat("-Z", "Y").to_euler()
    for nm, loc, rot, sz in (("refl_top", (0, 0.2, 1.3), (0, 0, 0), 5.0), ("refl_left", (-1.0, -0.8, 0.5), (math.radians(70), 0, math.radians(-50)), 1.2)):
        bpy.ops.mesh.primitive_plane_add(size=sz * k, location=c + Vector(loc) * k, rotation=rot)
        rp = bpy.context.object; rp.name = nm
        em = bpy.data.materials.new(nm); em.use_nodes = True
        nt = em.node_tree; nt.nodes.clear()
        e_ = nt.nodes.new("ShaderNodeEmission"); e_.inputs["Strength"].default_value = 6.0
        o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e_.outputs[0], o_.inputs["Surface"])
        rp.data.materials.append(em)
        rp.visible_camera = False; rp.visible_diffuse = False; rp.visible_shadow = False; rp.visible_volume_scatter = False


def camera(sc, tgt, dist, el, az, lens=50, fstop=None, focus=None, ortho=None):
    cam_d = bpy.data.cameras.new("cam"); cam = link(bpy.data.objects.new("camera", cam_d)); sc.camera = cam
    tgt = Vector(tgt)
    e, a = math.radians(el), math.radians(az)
    cam.location = tgt + Vector((dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens; cam_d.clip_start = 0.01; cam_d.clip_end = 20
    if ortho:
        cam_d.type = "ORTHO"; cam_d.ortho_scale = ortho
    if fstop:
        cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = fstop
        cam_d.dof.focus_distance = (Vector(focus if focus is not None else tgt) - cam.location).length
    return cam


def render(sc, out, pct):
    sc.render.resolution_percentage = pct
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


def build_catalog(page, out, samples=256, pct=100):
    """零件目录图：一页 6 × 4 格，俯拍，像说明书的零件表。"""
    from bpy_extras.object_utils import world_to_camera_view
    sc = scene_base(samples)
    K = Kit()
    backdrop()
    items = CATALOG[:24] if page == 1 else CATALOG[24:]
    zb, ry = 20.0, 54.0
    labels = []
    for i, (num, name, fn) in enumerate(items):
        c, r = i % 6, i // 6
        x, y = (c - 2.5) * PX, (1.5 - r) * ry + 6.0
        make_cell(K, fn(K), x, y, zb, name=f"cell_{num}")
        labels.append((num, name, (x * MM, (y - CY - 6.5) * MM, zb * MM)))
    lights(0, 0, 1.0)
    cam = camera(sc, (0, 0.002, zb * MM), 1.2, 66, 0, ortho=0.43)
    bpy.context.view_layer.update()
    js = []
    for num, name, p in labels:
        v = world_to_camera_view(sc, cam, Vector(p))
        js.append({"num": num, "name": name, "x": v.x, "y": 1 - v.y})
    Path(out).with_suffix(".json").write_text(json.dumps({"page": page, "labels": js}, ensure_ascii=False, indent=1), encoding="utf-8")
    render(sc, out, pct)


# ---- 整块大板：8 个区，每区几列，每列 6 格（主料杆上面 3 格、下面 3 格）


def ZONES(K):
    c = lambda s: (lambda K: p13_chip(K, s))
    pl = lambda s: (lambda K: p16_plate(K, s))
    return [
        (1, [[p03_person, lambda K: p04_liver(K, big=True), None, p11_bill, p10_calendar, p12_medal],     # None：被玻璃肝（2 × 2）占着的格
             [p06_globe, None, None, p05_lung_gut, p07_hk_map, p09_iv_bag],
             [pl("Liver cancer"), p08_capsule, p03_person, p03_person, p11_bill, c("AlphaFold")]]),
        (2, [[p14_buildings, pl("Case study"), p17_paper_book, p18_loupe_checklist, p15_sample_tube, pl("Research question")]]),
        (3, [[p19_cdk20, p20_pocket, p21_lock, lambda K: p22_key(K, 2), p24_atp, lambda K: p23_cell(K, "cancer")],
             [p29_cdk20_unknown, p28_top20, p26_survival, p25_tumour_chips, p27_data_disks, c("PandaOmics")]]),
        (4, [[p30_aa_chain, p31_tail, c("AlphaFold"), p32_nippers, p33_db_rack, p36_sieve],
             [p35_loop, c("Chemistry42"), p34_flask, p37_key_heap, lambda K: p22_key(K, 7), lambda K: p38_dial(K, "Score")]]),
        (5, [[lambda K: p39_molecules(K, "001"), lambda K: p39_molecules(K, "048"), lambda K: p20_pocket(K, True),
              lambda K: p38_dial(K, "Kd"), p40_dish, p23_cell]]),
        (6, [[p41_then_now, p42_bead_pile, p10_calendar, p43_mouse, p44_plug_bin, p08_capsule]]),
        (7, [[pl("Next steps"), p45_track, p29_cdk20_unknown, p43_mouse, p34_flask, lambda K: p39_molecules(K, "048")]]),
        (8, [[p46_newspaper, pl("Conclusion"), c("AI"), p19_cdk20, lambda K: p22_key(K, 48), p42_bead_pile]]),
    ]

ROWS = [123.0, 77.0, 31.0, -31.0, -77.0, -123.0]
ZGAP, BAY_W, HY_F = 8.0, 100.0, 150.0


def make_board(K, zones=None, skip_feet=()):
    """搭整块大板，不放灯和相机。zones 不给就用 ZONES(K)；skip_feet 是不要的支脚 (第几根, 前/后/中 = -1/1/0)。
    返回 board、zone_x（各区中心 x，mm）、colx（每列的区号和 x）、zb（板面离台面的高度，mm）、xl/xr（外框左右）。"""
    zones = zones or ZONES(K)
    ncol = sum(len(z[1]) for z in zones)
    total = ncol * PX + (len(zones)) * ZGAP + BAY_W
    x = -total / 2 + PX / 2
    zb = 30.0
    board = link(bpy.data.objects.new("board", None))
    W = K.white
    colx, zone_x, own = [], {}, {}
    for zi, cols in zones:
        xs = []
        for col in cols:
            for r, fn in enumerate(col):
                if fn is None:
                    continue
                part = fn(K)
                nx, ny = part.get("span", (1, 1))
                for dx in range(nx):
                    for dy in range(ny):
                        own[(len(colx) + dx, r + dy)] = (len(colx), r)
                make_cell(K, part, x, ROWS[r], 0, name=f"z{zi}_c{len(colx)}_r{r}").parent = board
            colx.append((zi, x)); xs.append(x)
            x += PX
        zone_x[zi] = sum(xs) / len(xs)
        x += ZGAP
    x_cells_r = colx[-1][1] + CX
    bay_c = x_cells_r + ZGAP + BAY_W / 2 - 4
    xl, xr = colx[0][1] - CX - 6, bay_c + BAY_W / 2 + 2
    # 外框、主料杆
    tube_w("frame", rrect((xl + xr) / 2, 0, (xr - xl) / 2, HY_F, 10.0), R_FRAME, W, board, cyclic=True)
    tube_w("main_runner", [(xl, 0), (bay_c - BAY_W / 2 + 8, 0)], R_MAIN, W, board)
    bpy.ops.mesh.primitive_cone_add(radius1=5.5 * MM, radius2=2.6 * MM, depth=10 * MM, vertices=48, location=(xl * MM, 0, 5 * MM))
    cn = bpy.context.object; cn.name = "sprue_cone"; bpy.ops.object.shade_smooth(); cn.data.materials.append(W); cn.parent = board
    # 格子之间、格子到外框和主料杆的短连杆
    for i, (zi, cx) in enumerate(colx):
        for r, y in enumerate(ROWS):
            if i + 1 < len(colx) and own.get((i, r)) != own.get((i + 1, r)):
                tube_w("lk", [(cx + CX, y), (colx[i + 1][1] - CX, y)], 1.2, W, board)
            if r in (0, 1, 3, 4) and own.get((i, r)) != own.get((i, r + 1)):
                tube_w("lk", [(cx, y - CY), (cx, ROWS[r + 1] + CY)], 1.2, W, board)
        tube_w("lk", [(cx, ROWS[0] + CY), (cx, HY_F)], 1.2, W, board)
        tube_w("lk", [(cx, ROWS[-1] - CY), (cx, -HY_F)], 1.2, W, board)
        tube_w("lk", [(cx, ROWS[2] - CY), (cx, R_MAIN - 0.5)], 1.2, W, board)
        tube_w("lk", [(cx, ROWS[3] + CY), (cx, -R_MAIN + 0.5)], 1.2, W, board)
    for y in ROWS:
        tube_w("lk", [(xl, y), (colx[0][1] - CX, y)], 1.2, W, board)
        tube_w("lk", [(x_cells_r, y), ((bay_c - BAY_W / 2 + 8) if abs(y) < 100 else xr, y)], 1.2, W, board)
    # 主料杆上的 7 个站点牌（零件 02）
    SP = Part(K, "stations", "white"); SP.root.parent = board
    x0, x1 = colx[0][1] - 6, colx[-1][1] + 6
    for i, s in enumerate(STATIONS):
        sx = x0 + (x1 - x0) * i / 6
        SP.cyl(sx - 15.5, 0, R_MAIN + 0.6, 2.6, 2.0, W, bevel=0.6)
        station_plate(SP, s, sx, 0, z=R_MAIN + 0.8)
    # 各区的区号牌，挂在上边框上
    ZP = Part(K, "zone_tags", "white"); ZP.root.parent = board
    for zi, zx in zone_x.items():
        ZP.box(zx, HY_F, 7.0, 4.2, 1.8, W, z=R_FRAME, r=1.2, bevel=0.4)
        ZP.text(str(zi), 6.4, zx, HY_F - 0.2, R_FRAME + 0.9, K.ink)
    # 最右端：成品位（空的底板，留四个带孔的定位凸台）
    BP = Part(K, "bay", "white"); BP.root.parent = board
    bw, bh = BAY_W / 2 - 8, 104.0
    organ("liver")
    lvs = [(bay_c + float(x) * 0.33, 52.0 + float(y) * 0.33) for x, y in _ORG["liver_outline"]]
    seats = [(lvs, 1.8, 1.5), (circle(bay_c, 4.0, 19.5), 1.8, 1.5), (rrect(bay_c + 6, -27.0, 17.0, 2.9, 1.0), 1.8, 1.5),
             (circle(bay_c - 19, -27.0, 8.0, ry=6.4), 1.8, 1.5), (circle(bay_c - 17, -52.0, 12.0), 1.8, 1.5), (circle(bay_c + 17, -52.0, 12.0), 1.8, 1.5),
             (rrect(bay_c, -80.0, 34.0, 4.6, 4.6), 1.8, 1.5)]
    pins = [(bay_c + LIVER_SOCKET_MM[0] * 0.33, 52.0 + LIVER_SOCKET_MM[1] * 0.33, 2.3), (bay_c, 4.0, 2.3), (bay_c - 19, -27.0, 1.8), (bay_c - 17, -52.0, 1.6), (bay_c + 17, -52.0, 1.6)] + \
           [(bay_c - 30 + 10 * i, -80.0, 1.3) for i in range(7)]
    BP.slab(rrect(bay_c, 0, bw, bh, 6.0), 3.0, W, bevel=0.6, holes=pins, cuts=seats)
    for (x_, y_, w_, h_) in ((bay_c, bh - 0.5, bw - 5, 1.0), (bay_c, -bh + 0.5, bw - 5, 1.0), (bay_c - bw + 0.5, 0, 1.0, bh - 5), (bay_c + bw - 0.5, 0, 1.0, bh - 5)):
        BP.box(x_, y_, w_, h_, 2.0, W, z=1.5 + 1.0, r=0.9, bevel=0.4)
    BP.box(bay_c, bh - 12, 26, 4.8, 1.2, W, z=1.5 + 0.6, r=1.4, bevel=0.3)
    BP.text("Finished model", 6.0, bay_c, bh - 12.2, 2.7, K.ink, italic=True)
    for s_ in (-1, 1):
        for dx in (-22, 22):
            tube_w("lk", [(bay_c + dx, s_ * bh), (bay_c + dx, s_ * HY_F)], 1.6, W, board)
    tube_w("lk", [(bay_c + bw, 0), (xr, 0)], 1.6, W, board)
    for y in (-60, 60):
        tube_w("lk", [(bay_c + bw, y), (xr, y)], 1.4, W, board)
    # 支脚
    nfeet = 7
    for i in range(nfeet):
        fx = xl + 14 + (xr - xl - 28) * i / (nfeet - 1)
        for fy in (-HY_F, HY_F, 0):
            h = zb - (R_FRAME if fy else R_MAIN)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.0032, depth=h * MM, vertices=32, location=(fx * MM, fy * MM, -(zb - h / 2 - 0.0) * MM + (zb - h) / 2 * MM * 0 - (h / 2) * MM * 0))
            o = bpy.context.object; o.name = "foot"; o.location = (fx * MM, fy * MM, (-zb + h / 2) * MM)
            bpy.ops.object.shade_smooth(); o.data.materials.append(W); o.parent = board
            if (i, (fy > 0) - (fy < 0)) in skip_feet:
                bpy.data.objects.remove(o)
    board.location = (0, 0, zb * MM)
    bpy.context.view_layer.update()
    return dict(board=board, zone_x=zone_x, colx=colx, zb=zb, xl=xl, xr=xr)


def part_of(cell):
    """格子里的零件根（空物体，带 gates、cat 属性）。"""
    return next(c for c in cell.children if "gates" in c.keys())


def loop_of(cell):
    """格子外圈那一圈料杆。"""
    return bpy.data.objects[cell.name + "_loop"]


def gates_of(cell):
    """格子里所有的浇口物体（细锥 name_g0…，远的还有一段支杆 name_g0_spur）。"""
    return [c for c in cell.children if c.name.startswith(cell.name + "_g")]


def check_gates(board, tol=0.8):
    """每个浇口的尖头离自己那件零件的表面不超过 tol 毫米（不悬空）。返回不合格的 (格子, 第几个浇口, 距离)。"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    bad = []
    for cell in [c for c in board.children if c.name.startswith("z") and "_c" in c.name]:
        part = part_of(cell)
        trees = []
        stack = list(part.children)
        while stack:
            o = stack.pop(); stack += list(o.children)
            if o.hide_render or o.type not in ("MESH", "CURVE", "FONT"):
                continue
            ev = o.evaluated_get(dg); me = ev.to_mesh()
            if len(me.polygons):
                bm = bmesh.new(); bm.from_mesh(me); bm.transform(ev.matrix_world)
                bmesh.ops.triangulate(bm, faces=bm.faces[:])
                trees.append(BVHTree.FromBMesh(bm)); bm.free()
            ev.to_mesh_clear()
        for i, (gx, gy, d, gz) in enumerate(json.loads(part["gates"])):
            tip = cell.matrix_world @ Vector((gx * MM, gy * MM, gz * MM))
            dist = min((9.0 if (r := t.find_nearest(tip)[3]) is None else r) for t in trees) / MM
            if dist > tol:
                bad.append((cell.name, i, round(dist, 2)))
    return bad


def build_board(view, out, samples=256, pct=100):
    sc = scene_base(samples)
    K = Kit()
    backdrop()
    B = make_board(K)
    zone_x, zb = B["zone_x"], B["zb"]
    zc = lambda zi, y=0.0, z=0.0: (zone_x[zi] * MM, y * MM, (zb + z) * MM)
    if view == "save":                                # 定版：存成 .blend（全景的灯和相机），顺便跑浇口检查
        lights(0, 0, 1.6)
        camera(sc, (0.005, -0.012, zb * MM), 1.53, 46, -18, lens=45, fstop=11, focus=(0, -0.05, zb * MM))
        bad = check_gates(B["board"])
        print("KIT_GATE_CHECK cells", len([c for c in B["board"].children if "_c" in c.name]), "bad", bad)
        bpy.ops.wm.save_as_mainfile(filepath=out)
        return
    if view == "pano":
        lights(0, 0, 1.6)
        camera(sc, (0.005, -0.012, zb * MM), 1.53, 46, -18, lens=45, fstop=11, focus=(0, -0.05, zb * MM))
    elif view == "liver":
        # 玻璃肝近景：低机位、长焦、浅景深，对着占 2 × 2 格的玻璃肝
        lv = bpy.data.objects["p04_liver"].matrix_world.translation
        t = (lv.x - 0.004, lv.y - 0.004, lv.z + 0.006)
        lights(t[0], 0.03, 1.0)
        camera(sc, t, 0.43, 34, -24, lens=85, fstop=4.0, focus=(lv.x - 0.01, lv.y - 0.012, lv.z + 0.012))
    elif view.startswith("zone"):
        # 分区检查图：从正前上方看一个区，全清晰
        t = zc(int(view[4:]), 0, 4)
        lights(t[0], 0, 1.0)
        camera(sc, t, 0.80, 62, 0, lens=50, fstop=16)
    else:
        if view == "z1":
            t = zc(1, 40, 4); dist, f = 0.36, 4.0
        elif view == "z34":
            t = (((zone_x[3] + zone_x[4]) / 2 - 20) * MM, 0.060, (zb + 4) * MM); dist, f = 0.42, 4.0
        else:
            t = zc(5, 50, 4); dist, f = 0.34, 4.0
        lights(t[0], 0, 1.0)
        camera(sc, t, dist, 32, -32, lens=50, fstop=f)
    render(sc, out, pct)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    smp = int(a[3]) if len(a) > 3 else 256
    pct = int(a[4]) if len(a) > 4 else 100
    if a[0] == "catalog":
        build_catalog(int(a[1]), a[2], smp, pct)
    elif a[0] == "board":
        build_board(a[1], a[2], smp, pct)
