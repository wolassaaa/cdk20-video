"""HKBU SCIE1007 课程作业的科普视频：注塑流道视觉语法的材质包和四个动词（审片/总管/动效升级方案_20261116 第 1 节）。

可复用 Blender 模块（Blender 5.1，Cycles/EEVEE 都能用），单位米。别的镜头脚本这样用：

    import sys; sys.path.insert(0, <本目录>)
    import mold_kit_v1 as MK
    MK.reset_scene(); MK.render_setup(sc)
    M = MK.materials()                        # bone / runner / red / blue / chrome / bill / bill_ink
    plate = MK.Plate(x0, x1, y0, y1, res)     # 骨白底模：加流道、型腔、顶针孔后 build()
    plate.runner(pts, r); plate.pocket_rrect(...); plate.pocket_capsule(...); plate.pin_hole(...)
    tube, head = MK.flow_tube(pts, r, M["red"])  # 流：MK.flow_keys(tube, head, [(帧, 弧长), ...])
    MK.grow_keys(obj, gate, floor)            # 长：shape key（种子→薄膜→满件），MK.grow(obj, f0, ...)
    MK.bake_pose(obj, {帧: Matrix})           # 脱：逐帧关键帧，不用刚体（no-clipping 规则）
    MK.retract(obj, f0, ...)                  # 收：失高光、缩回浇口、隐藏

规则（方案 1.2）：没有锐边（bevel ≥0.5 mm）、没有纯平面（台面 0.2 mm 大尺度起伏）、没有悬空。颜色只四种 + 钞票绿。
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- 颜色

def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


BONE, BONE_DEEP, RED, BLUE, CHROME = "#EDEBE4", "#D9D6CC", "#C8102E", "#002FA7", "#2B2D31"
BILL, BILL_INK = "#86A77F", "#3E6A47"   # 钞票：灰绿纸感 + 深绿凸纹（风格化，不是真钞）


# ---------------------------------------------------------------- 场景

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    return bpy.context.scene


def render_setup(sc, w=1920, h=1080, fps=60, samples=24, engine="CYCLES"):
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.fps = fps
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.image_settings.file_format = "PNG"
    if engine == "CYCLES":
        pr = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                pr.compute_device_type = kind
                pr.get_devices()
                if any(d.type == kind for d in pr.devices):
                    break
            except TypeError:
                continue
        for d in pr.devices:
            d.use = d.type != "CPU"
        sc.cycles.device = "GPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPTIX"
        sc.cycles.max_bounces = 6
        sc.render.use_persistent_data = True


def world(sc, strength=0.3):
    w = bpy.data.worlds.new("mold_world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = srgb(BONE)
    bg.inputs[1].default_value = strength
    sc.world = w


def lights(target=(0, 0, 0), size=1.4, key=900.0, fill=120.0):
    """方案 1.3：左上 45° 大面光（W3 柔光板做法），右后 15° 低角度暖补光，给分模线和浇口疤一条细高光。"""
    t = Vector(target)

    def area(name, d, power, sz, col):
        L = bpy.data.lights.new(name, "AREA")
        L.energy, L.size, L.color = power, sz, col
        o = bpy.data.objects.new(name, L)
        bpy.context.scene.collection.objects.link(o)
        o.location = t + d
        o.rotation_euler = (t - o.location).to_track_quat("-Z", "Y").to_euler()
        return o

    k = area("key", Vector((-1.0, 0.7, 0.75)).normalized() * 1.8, key, size, (1, 1, 1))
    f = area("rim", Vector((1.2, 1.0, 0.45)).normalized() * 1.6, fill, 0.5, (1.0, 0.86, 0.7))
    return k, f


# ---------------------------------------------------------------- 材质

def _principled(name, col, rough, coat=0.0, sss=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.12
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.004, 0.0015, 0.001)
        b.inputs["Subsurface Scale"].default_value = 0.6
    return m, nt, b


def _noise_bump(nt, b, scale, strength, dist, mask=None, extra=None):
    """细砂纹：噪波凹凸。mask 是 0–1 输出插口，只在 mask 处起砂；extra 是另一个高度插口（顶针印等），叠加。"""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    h = nz.outputs["Fac"]
    if mask is not None:
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(h, mul.inputs[0])
        nt.links.new(mask, mul.inputs[1])
        h = mul.outputs[0]
    if extra is not None:
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        nt.links.new(h, add.inputs[0])
        nt.links.new(extra, add.inputs[1])
        h = add.outputs[0]
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value = strength
    bu.inputs["Distance"].default_value = dist
    nt.links.new(h, bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return bu


def _soften(nt, b, rough):
    """收：物体颜色的 R 通道 0→1 时粗糙度升到 0.85（先失高光）。"""
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(oi.outputs["Color"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough
    mr.inputs["To Max"].default_value = 0.85
    nt.links.new(sep.outputs[0], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])


def _pin_marks(nt, centers, r=0.0012):
    """顶针圆印：物体坐标里若干个直径 2r 的浅圆坑（凹凸高度，圆内 −1）。"""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    out = None
    for c in centers:
        vd = nt.nodes.new("ShaderNodeVectorMath")
        vd.operation = "DISTANCE"
        vd.inputs[1].default_value = (c[0], c[1], c[2])
        nt.links.new(tc.outputs["Object"], vd.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath")
        lt.operation = "LESS_THAN"
        lt.inputs[1].default_value = r
        nt.links.new(vd.outputs["Value"], lt.inputs[0])
        if out is None:
            out = lt.outputs[0]
        else:
            mx = nt.nodes.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            nt.links.new(out, mx.inputs[0])
            nt.links.new(lt.outputs[0], mx.inputs[1])
            out = mx.outputs[0]
    neg = nt.nodes.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    neg.inputs[1].default_value = -0.6
    nt.links.new(out, neg.inputs[0])
    return neg.outputs[0]


def mat_mold():
    """底模：骨白哑光 0.55、清漆 0.08；流道（属性 runner）抛光 0.25；型腔底（属性 pocket）细砂纹（比例 400）。"""
    m, nt, b = _principled("mold_bone", srgb(BONE), 0.55, coat=0.08)
    ar = nt.nodes.new("ShaderNodeAttribute")
    ar.attribute_name = "runner"
    ap = nt.nodes.new("ShaderNodeAttribute")
    ap.attribute_name = "pocket"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.55
    mr.inputs["To Max"].default_value = 0.25
    nt.links.new(ar.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    _noise_bump(nt, b, 400.0, 0.35, 0.0004, mask=ap.outputs["Fac"])
    # 型腔底和流道沟底深一档骨白（#D9D6CC 再压一点），空格子、空沟在白台面上也认得出来
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    nt.links.new(ar.outputs["Fac"], mx.inputs[0])
    nt.links.new(ap.outputs["Fac"], mx.inputs[1])
    mc = nt.nodes.new("ShaderNodeMix")
    mc.data_type = "RGBA"
    mc.inputs["A"].default_value = srgb(BONE)
    mc.inputs["B"].default_value = srgb("#C9C5B8")
    nt.links.new(mx.outputs[0], mc.inputs["Factor"])
    nt.links.new(mc.outputs["Result"], b.inputs["Base Color"])
    return m


def mat_part(name, hexcol, pins=(), rough=0.3, coat=0.3, sss=0.15):
    """成形小件（料红 / 克莱因蓝 / 骨白件）：粗糙度 0.3、清漆 0.3、次表面 0.15，宽软高光；可收（物体颜色 R）。"""
    m, nt, b = _principled(name, srgb(hexcol), rough, coat=coat, sss=sss)
    _soften(nt, b, rough)
    extra = _pin_marks(nt, pins) if pins else None
    _noise_bump(nt, b, 900.0, 0.05, 0.0002, extra=extra)
    return m


def mat_chrome():
    m, nt, b = _principled("dark_chrome", srgb(CHROME), 0.16, metal=1.0)
    return m


def mat_bill(pins=()):
    """钞票：绿色纸感塑料片（纸纤维细噪波、粗糙度 0.62），底面顶针印。"""
    m, nt, b = _principled("bill_paper", srgb(BILL), 0.62, coat=0.1)
    _soften(nt, b, 0.62)
    extra = _pin_marks(nt, pins, 0.0016) if pins else None
    _noise_bump(nt, b, 1400.0, 0.12, 0.0002, extra=extra)
    return m


def materials(bill_pins=((0, 0, 0.0),)):
    return dict(
        bone=mat_mold(),
        red=mat_part("mold_red", RED),
        blue=mat_part("mold_blue", BLUE),
        part_bone=mat_part("mold_part_bone", BONE, sss=0.05),
        chrome=mat_chrome(),
        bill=mat_bill(bill_pins),
        bill_ink=mat_part("bill_ink", BILL_INK, rough=0.45, coat=0.15, sss=0.0),
    )


# ---------------------------------------------------------------- 底模（高度场）

def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-12
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    return np.hypot(px - ax - t * dx, py - ay - t * dy)


def rrect_sdf(px, py, c, hx, hy, rad, ang=0.0):
    ca, sa = math.cos(-ang), math.sin(-ang)
    x, y = px - c[0], py - c[1]
    x, y = x * ca - y * sa, x * sa + y * ca
    qx, qy = np.abs(x) - (hx - rad), np.abs(y) - (hy - rad)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad


class Plate:
    """骨白底模：一张高度场网格。型腔内壁有拔模斜度（壁宽 wall），流道是半圆截面，顶针孔是深孔。
    pocket/runner 两个点属性给材质（砂纹 / 抛光）。"""

    def __init__(self, x0, x1, y0, y1, res=0.00075):
        self.nx, self.ny = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
        xs, ys = np.linspace(x0, x1, self.nx), np.linspace(y0, y1, self.ny)
        self.X, self.Y = np.meshgrid(xs, ys)
        self.res = res
        # 方案 1.2：没有纯平面，0.2 mm 大尺度起伏
        self.Z = 0.0001 * (np.sin(self.X * 9.0 + 1.3) * np.cos(self.Y * 7.0) + 0.6 * np.sin(self.X * 4.1 - self.Y * 5.3))
        self.base = self.Z.copy()
        self.pocket = np.zeros_like(self.Z)
        self.runner_a = np.zeros_like(self.Z)

    def _win(self, xmin, xmax, ymin, ymax):
        x0 = self.X[0, 0]
        y0 = self.Y[0, 0]
        i0 = max(0, int((ymin - y0) / self.res) - 2)
        i1 = min(self.ny, int((ymax - y0) / self.res) + 3)
        j0 = max(0, int((xmin - x0) / self.res) - 2)
        j1 = min(self.nx, int((xmax - x0) / self.res) + 3)
        return np.s_[i0:i1, j0:j1]

    def _carve(self, sl, z, mask_attr=None, val=None):
        self.Z[sl] = np.minimum(self.Z[sl], z)
        if mask_attr is not None:
            mask_attr[sl] = np.maximum(mask_attr[sl], val)

    def runner(self, pts, r):
        """半圆截面流道，宽 2r、深 r（拐角是折线的圆角，pts 先做平滑）。"""
        for a, b in zip(pts, pts[1:]):
            sl = self._win(min(a[0], b[0]) - r, max(a[0], b[0]) + r, min(a[1], b[1]) - r, max(a[1], b[1]) + r)
            d = _seg_dist(self.X[sl], self.Y[sl], a, b)
            z = np.where(d < r, -np.sqrt(np.maximum(r * r - d * d, 0)), 1.0)
            self._carve(sl, z, self.runner_a, (d < r * 0.9).astype(float))

    def pocket_rrect(self, c, hx, hy, rad, depth, ang=0.0, wall=0.0015):
        """平底型腔：底在 −depth，内壁从 sdf 0 到 wall 斜上去（拔模 + 圆角），底面有砂纹。"""
        R = max(hx, hy) + wall
        sl = self._win(c[0] - R, c[0] + R, c[1] - R, c[1] + R)
        s = rrect_sdf(self.X[sl], self.Y[sl], c, hx, hy, rad, ang)
        k = np.clip(s / wall, 0, 1)
        k = k * k * (3 - 2 * k)
        z = np.where(s < wall, -depth * (1 - k), 1.0)
        self._carve(sl, z, self.pocket, (s < 0).astype(float))

    def pocket_capsule(self, a, b, r):
        """胶囊型腔：沿线段 ab 的半圆槽，半径 r。"""
        sl = self._win(min(a[0], b[0]) - r, max(a[0], b[0]) + r, min(a[1], b[1]) - r, max(a[1], b[1]) + r)
        d = _seg_dist(self.X[sl], self.Y[sl], a, b)
        z = np.where(d < r, -np.sqrt(np.maximum(r * r - d * d, 0)), 1.0)
        self._carve(sl, z, self.pocket, (d < r * 0.85).astype(float))

    def pin_hole(self, c, r, depth=0.03):
        sl = self._win(c[0] - r - 0.002, c[0] + r + 0.002, c[1] - r - 0.002, c[1] + r + 0.002)
        d = np.hypot(self.X[sl] - c[0], self.Y[sl] - c[1])
        k = np.clip((d - r) / 0.0008, 0, 1)
        self.Z[sl] = np.where(d < r + 0.0008, np.minimum(self.Z[sl], -depth * (1 - k) + self.Z[sl] * k), self.Z[sl])

    def height(self, x, y):
        """格点双线性插值的台面高度（检查和摆件用）。"""
        fx = (x - self.X[0, 0]) / self.res
        fy = (y - self.Y[0, 0]) / self.res
        j, i = int(fx), int(fy)
        tx, ty = fx - j, fy - i
        Z = self.Z
        return (Z[i, j] * (1 - tx) * (1 - ty) + Z[i, j + 1] * tx * (1 - ty) + Z[i + 1, j] * (1 - tx) * ty + Z[i + 1, j + 1] * tx * ty)

    def build(self, mat, name="mold_plate"):
        nx, ny = self.nx, self.ny
        co = np.stack([self.X, self.Y, self.Z], -1).reshape(-1, 3).astype(np.float32)
        ii, jj = np.meshgrid(np.arange(ny - 1), np.arange(nx - 1), indexing="ij")
        v0 = (ii * nx + jj).ravel()
        quads = np.stack([v0, v0 + 1, v0 + nx + 1, v0 + nx], -1).astype(np.int32)
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(co))
        me.vertices.foreach_set("co", co.ravel())
        me.loops.add(quads.size)
        me.loops.foreach_set("vertex_index", quads.ravel())
        me.polygons.add(len(quads))
        me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
        me.update(calc_edges=True)
        me.shade_smooth()
        for nm, arr in (("pocket", self.pocket), ("runner", self.runner_a)):
            at = me.attributes.new(nm, "FLOAT", "POINT")
            at.data.foreach_set("value", arr.ravel().astype(np.float32))
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o


def chaikin(pts, n=4, keep_ends=True):
    P = [tuple(p) for p in pts]
    for _ in range(n):
        Q = [P[0]] if keep_ends else []
        for a, b in zip(P, P[1:]):
            Q.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            Q.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if keep_ends:
            Q.append(P[-1])
        P = Q
    return P


def resample(pts, step):
    P = np.array(pts, float)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], step).tolist() + [s[-1]]
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], -1), float(s[-1])


def arclen(pts):
    P = np.array(pts, float)
    return np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])


def point_at(pts, s):
    P = np.array(pts, float)
    S = arclen(P)
    return float(np.interp(s, S, P[:, 0])), float(np.interp(s, S, P[:, 1]))


# ---------------------------------------------------------------- 件的几何

def _link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def rrect_poly(hx, hy, rad, n=10):
    pts = []
    for cx, cy, a0 in ((hx - rad, hy - rad, 0), (-hx + rad, hy - rad, 90), (-hx + rad, -hy + rad, 180), (hx - rad, -hy + rad, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


def slab(name, poly, z0, z1, bevel=0.0006, segs=3, mat_index=0):
    """多边形挤出成厚片，上下两圈边倒圆角（没有锐边）。返回 bmesh 几何的 Mesh。"""
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, z0)) for x, y in poly]
    vt = [bm.verts.new((x, y, z1)) for x, y in poly]
    n = len(poly)
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    bm.normal_update()
    edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-9]
    bmesh.ops.bevel(bm, geom=edges, offset=min(bevel, (z1 - z0) * 0.45), segments=segs, profile=0.5, affect="EDGES")
    for f in bm.faces:
        f.material_index = mat_index
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def text_mesh(s, font, size, depth, bevel=0.0003, name="txt"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.font = font
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    o = bpy.data.objects.new(name, cu)
    _link(o)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o)
    return me


def join_meshes(name, parts):
    """parts: [(mesh, Matrix, mat_index)] → 一个 Mesh。"""
    bm = bmesh.new()
    for me, M, mi in parts:
        t = bmesh.new()
        t.from_mesh(me)
        bmesh.ops.transform(t, matrix=M, verts=t.verts)
        for f in t.faces:
            f.material_index = mi
            f.smooth = True
        tmp = bpy.data.meshes.new("_t")
        t.to_mesh(tmp)
        t.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    return out


def bill_mesh(name, font, L=0.156, W=0.066, T=0.0025, relief=0.0005):
    """风格化钞票：圆角薄片（圆角 5 mm、倒边 0.8 mm），一圈分模线（凸 0.25 mm），深绿凸边框、中间椭圆章里一个 "$"，
    两头各一个小 "$"；+y 边中点一个浇口疤。没有人像、编号、真钞图案。原点在底面中心。"""
    parts = [(slab("b", rrect_poly(L / 2, W / 2, 0.005), 0, T, 0.0008), Matrix(), 0)]
    parts.append((slab("pl", rrect_poly(L / 2 + 0.00025, W / 2 + 0.00025, 0.00525), T * 0.42, T * 0.58, 0.00006, 1), Matrix(), 0))
    ring_o, ring_i = rrect_poly(L / 2 - 0.004, W / 2 - 0.004, 0.003), rrect_poly(L / 2 - 0.0055, W / 2 - 0.0055, 0.0018)
    bm = bmesh.new()
    n = len(ring_o)
    vo = [bm.verts.new((x, y, T - 0.0002)) for x, y in ring_o]
    vi = [bm.verts.new((x, y, T - 0.0002)) for x, y in ring_i]
    to = [bm.verts.new((x, y, T + relief)) for x, y in ring_o]
    ti = [bm.verts.new((x, y, T + relief)) for x, y in ring_i]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((to[i], to[j], ti[j], ti[i]))
        bm.faces.new((vo[i], to[i], to[j], vo[j])[::-1])
        bm.faces.new((vi[i], vi[j], ti[j], ti[i])[::-1])
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    rme = bpy.data.meshes.new("ring")
    bm.to_mesh(rme)
    bm.free()
    parts.append((rme, Matrix(), 1))
    oval = [(0.021 * math.cos(a), 0.019 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    oval_in = [(0.0185 * math.cos(a), 0.0165 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, T + relief * 0.6)) for x, y in oval]
    vi = [bm.verts.new((x, y, T + relief * 0.6)) for x, y in oval_in]
    bo = [bm.verts.new((x, y, T - 0.0002)) for x, y in oval]
    for i in range(48):
        j = (i + 1) % 48
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
        bm.faces.new((bo[i], bo[j], vo[j], vo[i]))
    ome = bpy.data.meshes.new("oval")
    bm.to_mesh(ome)
    bm.free()
    parts.append((ome, Matrix(), 1))
    big = text_mesh("$", font, 0.03, relief + 0.0004, name="d1")
    parts.append((big, Matrix.Translation((0, 0.0005, T + relief / 2 - 0.0002 + 0.0002)), 1))
    sm = text_mesh("$", font, 0.013, relief + 0.0004, name="d2")
    for sx in (-1, 1):
        parts.append((sm, Matrix.Translation((sx * (L / 2 - 0.016), 0.0003, T + relief / 2 - 0.0002 + 0.0002)), 1))
    nub = bpy.data.meshes.new("nub")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0008)
    bm.to_mesh(nub)
    bm.free()
    parts.append((nub, Matrix.Translation((0, W / 2 - 0.00045, T / 2)) @ Matrix.Diagonal((1, 1, 1, 1)), 0))
    me = join_meshes(name, parts)
    return me, dict(L=L, W=W, T=T, top=T + relief, gate=(0, W / 2, 0.0))


def capsule_mesh(name, r=0.0045, h=0.015, segs=32, rings=16):
    """胶囊（药）：沿 y，+y 半红、−y 半骨白（材质槽 0 / 1），中缝一圈分模线，+y 端浇口疤。原点在胶囊中心。"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    for v in bm.verts:
        v.co.y += h / 2 if v.co.y > 1e-9 else (-h / 2 if v.co.y < -1e-9 else 0)
    # 赤道环拆成两圈，好分色
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > h * 0.5], cuts=6)
    for f in bm.faces:
        f.material_index = 0 if f.calc_center_median().y > 0.0004 else 1
        f.smooth = True
    me0 = bpy.data.meshes.new("cap")
    bm.to_mesh(me0)
    bm.free()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r + 0.00022, radius2=r + 0.00022, depth=0.0007)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    seam = bpy.data.meshes.new("seam")
    bm.to_mesh(seam)
    bm.free()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.0007)
    nub = bpy.data.meshes.new("nub")
    bm.to_mesh(nub)
    bm.free()
    me = join_meshes(name, [(me0, Matrix(), 0), (seam, Matrix.Translation((0, 0.0004, 0)), 0), (nub, Matrix.Translation((0, h / 2 + r - 0.0004, 0)), 0)])
    for p in me.polygons:
        pass
    return me, dict(r=r, h=h, gate=(0, h / 2 + r, 0))


def new_obj(name, me, mats):
    o = bpy.data.objects.new(name, me)
    for m in mats:
        me.materials.append(m)
    return _link(o)


# ---------------------------------------------------------------- 曲线

def ease_in_out(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_out(u, p=3):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** p


def ease_in(u, p=2):
    u = min(max(u, 0.0), 1.0)
    return u ** p


def overshoot(u, amt=0.03):
    """长：ease-out，末尾 2 帧过冲 3%（到位时"硬一下"）。返回 0→1+amt→1 的值。"""
    u = min(max(u, 0.0), 1.0)
    if u < 0.82:
        return (1 + amt) * ease_out(u / 0.82)
    return 1 + amt * (1 - ease_in_out((u - 0.82) / 0.18))


# ---------------------------------------------------------------- 流

def flow_tube(name, pts, r, z, mat, head=True):
    """流：沿流道的圆截面料管（曲线 + 倒角），bevel_factor_end 按弧长推进；前端一个圆头球。"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = "SPLINE"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, z, 1)
    cu.materials.append(mat)
    o = _link(bpy.data.objects.new(name, cu))
    h = None
    if head:
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
        me = bpy.data.meshes.new(name + "_head")
        bm.to_mesh(me)
        bm.free()
        for f in me.polygons:
            f.use_smooth = True
        me.materials.append(mat)
        h = _link(bpy.data.objects.new(name + "_head", me))
    o["pts"] = [list(p) for p in pts]
    o["z"] = z
    return o, h


def flow_keys(tube, head, keys, f0, f1):
    """keys: [(帧, 弧长 m)]，中间线性（每段起停各 4 帧缓），逐帧写 bevel_factor_end 和圆头位置。f0 前隐藏。"""
    pts = [tuple(p) for p in tube["pts"]]
    S = arclen(pts)
    total = S[-1]
    kf = [k[0] for k in keys]
    ks = [k[1] for k in keys]

    def s_at(f):
        if f <= kf[0]:
            return ks[0]
        for (fa, sa), (fb, sb) in zip(keys, keys[1:]):
            if fa <= f <= fb:
                u = (f - fa) / max(fb - fa, 1e-9)
                ramp = min(4 / max(fb - fa, 1), 0.3)
                if u < ramp:
                    w = u * u / (2 * ramp * (1 - ramp))
                elif u > 1 - ramp:
                    w = 1 - (1 - u) ** 2 / (2 * ramp * (1 - ramp))
                else:
                    w = (u - ramp / 2) / (1 - ramp)
                return sa + (sb - sa) * w
        return ks[-1]

    out = {}
    for f in range(f0, f1 + 1):
        s = s_at(f)
        tube.data.bevel_factor_end = max(s / total, 0.0)
        tube.data.keyframe_insert("bevel_factor_end", frame=f)
        if head is not None:
            x, y = point_at(pts, s)
            head.location = (x, y, tube["z"])
            head.keyframe_insert("location", frame=f)
        out[f] = s
    vis(tube, kf[0])
    if head is not None:
        vis(head, kf[0])
    return out


def gate_fill(tube, f0, n=4):
    """浇口：短料管 n 帧里从流道冲进型腔（流道前端停 2 帧再冲的那一下）。"""
    for f, v in ((f0 - 1, 0.0), (f0, 0.0)):
        tube.data.bevel_factor_end = v
        tube.data.keyframe_insert("bevel_factor_end", frame=f)
    for k in range(1, n + 1):
        tube.data.bevel_factor_end = ease_in(k / n, 1.5)
        tube.data.keyframe_insert("bevel_factor_end", frame=f0 + k)
    vis(tube, f0)


def vis(o, f_on, f_off=None):
    """f_on 前隐藏，f_off 起隐藏（常量插值）。"""
    for f, hide in ((0, True), (f_on, False)) + (((f_off, True),) if f_off is not None else ()):
        if f == 0 and f_on == 0:
            continue
        o.hide_render = o.hide_viewport = hide
        o.keyframe_insert("hide_render", frame=f)
        o.keyframe_insert("hide_viewport", frame=f)


# ---------------------------------------------------------------- 长 / 收（shape key）

def grow_keys(o, gate, floor_fn=None, film=0.08, seed=0.03):
    """长：Basis = 成形件；film = 压成贴着型腔底的薄膜（料铺满）；seed = 缩到浇口一点（料刚进来）。
    floor_fn(x, y) 给物体坐标里型腔底的 z（默认平底 z=最低点）；薄膜厚度 = 原厚 × film。"""
    me = o.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    zmin = co[:, 2].min()
    o.shape_key_add(name="Basis", from_mix=False)
    fl = co.copy()
    if floor_fn is None:
        fl[:, 2] = zmin + 0.0001 + (co[:, 2] - zmin) * film
    else:
        fz = np.array([floor_fn(x, y) for x, y in co[:, :2]])
        fl[:, 2] = fz + 0.00045 + (co[:, 2] - zmin) * film
    g = np.array(gate, float)
    g[2] = (floor_fn(g[0], g[1]) + 0.00045) if floor_fn is not None else fl[:, 2].min()
    sd = g + (fl - g) * seed
    for nm, arr in (("film", fl), ("seed", sd)):
        kb = o.shape_key_add(name=nm, from_mix=False)
        kb.data.foreach_set("co", arr.ravel())
        kb.slider_min = -0.1
    return o


def _set_keys(o, f, film, seed):
    kb = o.data.shape_keys.key_blocks
    kb["film"].value = film
    kb["seed"].value = seed
    kb["film"].keyframe_insert("value", frame=f)
    kb["seed"].value = seed
    kb["seed"].keyframe_insert("value", frame=f)


def grow(o, f0, fill=5, bulge=12, amt=0.03):
    """长（方案 1.4）：料面从浇口铺满 fill 帧（seed→film），然后鼓成形 bulge 帧，ease-out 末尾过冲 3%。返回成形帧。"""
    vis(o, f0)
    _set_keys(o, f0, 0.0, 1.0)
    for k in range(1, fill + 1):
        u = ease_out(k / fill, 2)
        _set_keys(o, f0 + k, u, 1 - u)
    for k in range(1, bulge + 1):
        v = overshoot(k / bulge, amt)
        _set_keys(o, f0 + fill + k, 1 - v, 0.0)
    return f0 + fill + bulge


def soften(o, f0, n=4, back=False):
    """表面失高光（物体颜色 R 0→1），n 帧。"""
    for f, v in ((f0, 0.0), (f0 + n, 1.0)) if not back else ((f0, 1.0), (f0 + n, 0.0)):
        o.color = (v, 0, 0, 1)
        o.keyframe_insert("color", frame=f)


def retract(o, f0, soft=4, shrink=10):
    """收：先失高光 soft 帧，再满件→薄膜→缩回浇口 shrink 帧，然后隐藏。返回消失帧。"""
    soften(o, f0, soft)
    _set_keys(o, f0 + soft, 0.0, 0.0)
    for k in range(1, shrink + 1):
        u = ease_in_out(k / shrink)
        film = min(1.0, u * 1.6)
        seed = max(0.0, (u - 0.5) * 2)
        _set_keys(o, f0 + soft + k, film * (1 - seed), seed)
    end = f0 + soft + shrink
    vis(o, 0, end + 1)
    return end


# ---------------------------------------------------------------- 脱 / 掉落（逐帧关键帧，不用刚体）

def bake_pose(o, poses):
    """poses: {帧: Matrix(世界)}，逐帧写 location + 四元数旋转（LINEAR）。"""
    o.rotation_mode = "QUATERNION"
    for f in sorted(poses):
        loc, q, _ = poses[f].decompose()
        o.location = loc
        o.rotation_quaternion = q
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_quaternion", frame=f)


def bezier(p0, p1, p2, p3, u):
    a = 1 - u
    return p0 * a ** 3 + p1 * 3 * a * a * u + p2 * 3 * a * u * u + p3 * u ** 3


def pin_obj(name, r, length, mat):
    """顶针（暗铬圆柱，顶面圆角），原点在顶面。"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=length)
    bmesh.ops.translate(bm, vec=(0, 0, -length / 2), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = abs(p.normal.z) < 0.5
    o = new_obj(name, me, [mat])
    bv = o.modifiers.new("bv", "BEVEL")
    bv.width, bv.segments = 0.0003, 2
    return o


def pin_stroke(pin, base, f0, up=0.012, rise=6, hold=0, fall=10):
    """脱：顶针 rise 帧顶起 up（ease-in），停 hold 帧，fall 帧退回。返回顶到位的帧。"""
    z0 = Vector(base)
    for f, dz in ((f0, 0.0),) + tuple((f0 + k, up * ease_in(k / rise, 2)) for k in range(1, rise + 1)) + \
            ((f0 + rise + hold, up),) + tuple((f0 + rise + hold + k, up * (1 - ease_in_out(k / fall))) for k in range(1, fall + 1)):
        pin.location = z0 + Vector((0, 0, dz))
        pin.keyframe_insert("location", frame=f)
    return f0 + rise


def camera(name="cam", lens=50.0, fstop=4.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    o = _link(bpy.data.objects.new(name, cd))
    bpy.context.scene.camera = o
    return o


def cam_key(cam, f, target, dist, pitch_deg=55.0, yaw_deg=0.0):
    t = Vector(target)
    p, y = math.radians(pitch_deg), math.radians(yaw_deg)
    off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.location = t + off
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (t - cam.location).to_track_quat("-Z", "Y")
    cam.data.dof.focus_distance = dist
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_quaternion", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)
