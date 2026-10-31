"""HKBU SCIE1007 coursework science video. Clay direction: the work table every shot shares, and its materials.

Scale: 1 unit = 2 cm, so a thumb print is about 1.6 units across. Real CDK20 surface and pLDDT come from the project's data.
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blcommon import *  # noqa
from common import OUT, ROOT, WORK, load_surface, rot, smooth_field, vertex_normals  # noqa

RES = float(os.environ.get("CLAY_RES", "1.0"))


def scene(samples=160, bounces=6):
    sc = reset(int(1920 * RES), int(1080 * RES), samples=samples, bounces=bounces)
    sc.cycles.sample_clamp_indirect = 8
    return sc


def img(name, srgb=True):
    im = bpy.data.images.load(str(WORK / name))
    if not srgb:
        im.colorspace_settings.name = "Non-Color"
    return im


def table(back=20.0, dark=0.0):
    """Mat 60 x 40 centred on the origin, on a wood table cut at y = back. dark 0..1 kills the green for the heavy shots."""
    v = np.array([[-30, -20, 0.02], [30, -20, 0.02], [30, min(back, 20), 0.02], [-30, min(back, 20), 0.02]], np.float32)
    o = add_mesh("mat", v, np.array([[0, 1, 2, 3]]), smooth=False)
    m, p = principled("mat", rough=0.62)
    t = m.node_tree
    tc = t.nodes.new("ShaderNodeTexCoord")
    mp = t.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 60, 1 / 40, 1)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    t.links.new(tc.outputs["Object"], mp.inputs[0])
    ti = t.nodes.new("ShaderNodeTexImage")
    ti.image = img("mat.jpg")
    t.links.new(mp.outputs[0], ti.inputs[0])
    hs = t.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 1 - dark
    hs.inputs["Value"].default_value = 1 - 0.75 * dark
    t.links.new(ti.outputs[0], hs.inputs["Color"])
    t.links.new(hs.outputs[0], p.inputs["Base Color"])
    p.inputs["Specular IOR Level"].default_value = 0.35
    o.data.materials.append(m)
    # the table the mat lies on
    w = np.array([[-60, -40, 0], [60, -40, 0], [60, back + 0.5, 0], [-60, back + 0.5, 0],
                  [-60, -40, -3], [60, -40, -3], [60, back + 0.5, -3], [-60, back + 0.5, -3]], np.float32)
    fa = np.array([[0, 1, 2, 3], [4, 7, 6, 5], [2, 6, 7, 3], [0, 4, 5, 1], [1, 5, 6, 2], [3, 7, 4, 0]])
    tb = add_mesh("table", w, fa, smooth=False)
    tm, tp = principled("wood", (0.20 * (1 - dark * 0.8), 0.10 * (1 - dark * 0.8), 0.05 * (1 - dark * 0.8)), 0.5)
    tb.data.materials.append(tm)
    return o


def wall(y=26.0, col=(0.85, 0.42, 0.05), rough=0.8):
    v = np.array([[-200, y, -30], [200, y, -30], [200, y, 120], [-200, y, 120]], np.float32)
    o = add_mesh("wall", v, np.array([[0, 1, 2, 3]]), smooth=False)
    m, p = principled("wall", col, rough)
    o.data.materials.append(m)
    return o


def clay_material(name, col, rough=0.5, sss=0.35, tail_col=None, ridge=0.012):
    """Soft clay. Whorl prints come from per-dent coordinates stored on the mesh ('fp', 'fpm'); fine grain everywhere else."""
    M = bpy.data.materials.new(name)
    M.use_nodes = True
    nt = M.node_tree
    P = nt.nodes["Principled BSDF"]
    P.inputs["Roughness"].default_value = rough
    P.inputs["Subsurface Weight"].default_value = sss
    P.inputs["Subsurface Radius"].default_value = (0.25, 0.1, 0.05)
    P.inputs["Subsurface Scale"].default_value = 0.2
    P.inputs["Specular IOR Level"].default_value = 0.42
    if tail_col is None:
        P.inputs["Base Color"].default_value = (*col, 1)
    else:
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "conf"
        r = nt.nodes.new("ShaderNodeValToRGB")
        e = r.color_ramp.elements
        e[0].position = 0.62; e[0].color = (*tail_col, 1)
        e[1].position = 0.76; e[1].color = (*col, 1)
        nt.links.new(a.outputs["Fac"], r.inputs[0])
        nt.links.new(r.outputs[0], P.inputs["Base Color"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 26; fine.inputs["Detail"].default_value = 7
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    big = nt.nodes.new("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = 3.2; big.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], big.inputs["Vector"])
    fp = nt.nodes.new("ShaderNodeAttribute"); fp.attribute_name = "fp"
    fm = nt.nodes.new("ShaderNodeAttribute"); fm.attribute_name = "fpm"
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"; wave.rings_direction = "SPHERICAL"
    wave.inputs["Scale"].default_value = 6.0
    wave.inputs["Distortion"].default_value = 2.2
    wave.inputs["Detail"].default_value = 1.0
    wave.inputs["Detail Scale"].default_value = 0.9
    nt.links.new(fp.outputs["Vector"], wave.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(wave.outputs[1], mul.inputs[0]); nt.links.new(fm.outputs["Fac"], mul.inputs[1])
    # hand burnish: patches of smooth, patches of grain
    g1 = nt.nodes.new("ShaderNodeMath"); g1.operation = "MULTIPLY"; g1.inputs[1].default_value = 0.5
    nt.links.new(fine.outputs[0], g1.inputs[0])
    g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = "MULTIPLY"; g2.inputs[1].default_value = 3.0
    nt.links.new(big.outputs[0], g2.inputs[0])
    a1 = nt.nodes.new("ShaderNodeMath"); a1.operation = "ADD"
    nt.links.new(g1.outputs[0], a1.inputs[0]); nt.links.new(g2.outputs[0], a1.inputs[1])
    a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = "MULTIPLY_ADD"; a2.inputs[1].default_value = 0.9
    nt.links.new(mul.outputs[0], a2.inputs[0]); nt.links.new(a1.outputs[0], a2.inputs[2])
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 1.0; b.inputs["Distance"].default_value = ridge
    nt.links.new(a2.outputs[0], b.inputs["Height"])
    nt.links.new(b.outputs[0], P.inputs["Normal"])
    return M


def thumbs(v, n, k, seed=1, R=0.85, depth=0.16, centres=None):
    """Press k thumbs into a mesh. Returns displaced verts, whorl coordinates, whorl mask."""
    g = np.random.default_rng(seed)
    v2 = v.copy()
    fp = np.zeros_like(v)
    fm = np.zeros(len(v), np.float32)
    idx = centres if centres is not None else g.choice(len(v), k, replace=False)
    for i in idx:
        c, nn = v[i], n[i]
        a = np.cross(nn, g.normal(size=3)); a /= np.linalg.norm(a)
        b = np.cross(nn, a)
        dv = v - c
        x, y = dv @ a, dv @ b
        z = dv @ nn
        r2 = (x / (R * 0.74)) ** 2 + (y / R) ** 2
        near = (r2 < 1.0) & (np.abs(z) < R)
        w = np.zeros(len(v), np.float32)
        w[near] = np.cos(np.sqrt(r2[near]) * 1.5708) ** 2
        v2 -= n * (w * depth)[:, None]
        upd = w > fm
        fp[upd] = np.c_[x[upd], y[upd], np.zeros(upd.sum())]
        fm = np.maximum(fm, np.clip(w * 3.2, 0, 1))
    return v2, fp, fm


def get_vn(ob):
    v = np.zeros(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("co", v)
    n = np.zeros(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("normal", n)
    return v.reshape(-1, 3), n.reshape(-1, 3)


def attach_clay(ob, fp, fm):
    add_attr(ob, "fp", fp, kind="FLOAT_VECTOR")
    add_attr(ob, "fpm", fm)


def lump_template(sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1)
    t = bpy.context.object
    nv = len(t.data.vertices)
    tv = np.zeros(nv * 3, np.float32); t.data.vertices.foreach_get("co", tv); tv = tv.reshape(-1, 3)
    nf = len(t.data.polygons)
    tf = np.zeros(nf * 3, np.int32); t.data.polygons.foreach_get("vertices", tf); tf = tf.reshape(-1, 3)
    bpy.data.objects.remove(t)
    return tv, tf


def crumbs(n, region, mat, seed=5, rmin=0.03, rmax=0.2, avoid=None, sub=2):
    """Scraps of clay on the mat. region (x0, x1, y0, y1). avoid is an optional function p -> bool mask."""
    tv, tf = lump_template(sub)
    g = np.random.default_rng(seed)
    xs = g.uniform(region[0], region[1], n * 3)
    ys = g.uniform(region[2], region[3], n * 3)
    p = np.c_[xs, ys, np.zeros(len(xs))]
    if avoid is not None:
        p = p[~avoid(p)]
    p = p[:n]
    vs, fs = [], []
    for i, c in enumerate(p):
        r = rmin + (rmax - rmin) * g.random() ** 2.5
        a = g.normal(size=(3, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
        d = sum(g.uniform(0.08, 0.2) * np.sin(g.uniform(2, 5) * (tv @ x) + g.uniform(0, 6)) for x in a)
        vv = tv * (1 + d[:, None]) * r * g.uniform(0.7, 1.3, 3) * np.array([1, 1, 0.7]) + c + np.array([0, 0, r * 0.55])
        vs.append(vv); fs.append(tf + i * len(tv))
    o = add_mesh("crumbs", np.concatenate(vs), np.concatenate(fs), tris=True)
    o.data.materials.append(mat)
    add_attr(o, "fp", np.zeros((len(o.data.vertices), 3)), kind="FLOAT_VECTOR")
    add_attr(o, "fpm", np.zeros(len(o.data.vertices)))
    return o


def rounded_slab(w, h, t, bevel=0.14):
    """Slab with soft edges, top face UV 0..1 stored as 'uvw' for the painted texture. Centre at origin, sits on z = 0."""
    nx, ny = 80, int(80 * h / w)
    u, v_ = np.meshgrid(np.linspace(0, 1, nx), np.linspace(0, 1, ny))
    x = (u - 0.5) * w
    y = (v_ - 0.5) * h
    edge = np.minimum.reduce([x + w / 2, w / 2 - x, y + h / 2, h / 2 - y])
    z = t - bevel + bevel * np.sqrt(np.clip(1 - (1 - np.clip(edge / bevel, 0, 1)) ** 2, 0, 1))
    top = np.c_[x.ravel(), y.ravel(), z.ravel()]
    i = np.arange(nx * ny).reshape(ny, nx)
    q = np.c_[i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, 1:].ravel(), i[1:, :-1].ravel()]
    bottom = top.copy(); bottom[:, 2] = 0
    verts = np.r_[top, bottom]
    N = nx * ny
    border = np.r_[i[0, :], i[1:, -1], i[-1, -2::-1], i[-2:0:-1, 0]]
    side = np.c_[border, np.roll(border, -1), np.roll(border, -1) + N, border + N]
    qb = q[:, ::-1] + N
    qs = np.r_[q, side[:, ::-1], qb]
    ob = add_mesh("slab", verts.astype(np.float32), qs.astype(np.int32), smooth=True)
    uv = np.c_[(verts[:, 0] / w + 0.5), (verts[:, 1] / h + 0.5), np.zeros(len(verts))]
    add_attr(ob, "uvw", uv, kind="FLOAT_VECTOR")
    return ob


def glazed_mat(name, tex, bump=None, rough=0.08, craze=0.1):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    P = t.nodes["Principled BSDF"]
    P.inputs["Roughness"].default_value = rough
    P.inputs["Coat Weight"].default_value = 1.0
    P.inputs["Coat Roughness"].default_value = 0.03
    P.inputs["Specular IOR Level"].default_value = 0.6
    a = t.nodes.new("ShaderNodeAttribute"); a.attribute_name = "uvw"
    ti = t.nodes.new("ShaderNodeTexImage"); ti.image = img(tex); ti.extension = "EXTEND"
    t.links.new(a.outputs["Vector"], ti.inputs[0])
    t.links.new(ti.outputs[0], P.inputs["Base Color"])
    # crazing of the fired glaze
    vor = t.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 3.4
    tc = t.nodes.new("ShaderNodeTexCoord")
    nz = t.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    mx = t.nodes.new("ShaderNodeMix"); mx.data_type = "VECTOR"
    mx.inputs[0].default_value = 0.12
    t.links.new(tc.outputs["Object"], mx.inputs[4])
    t.links.new(nz.outputs["Color"], mx.inputs[5])
    t.links.new(mx.outputs[1], vor.inputs["Vector"])
    cl = t.nodes.new("ShaderNodeMath"); cl.operation = "GREATER_THAN"; cl.inputs[1].default_value = 0.012
    t.links.new(vor.outputs["Distance"], cl.inputs[0])
    b = t.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = craze; b.inputs["Distance"].default_value = 0.02
    t.links.new(cl.outputs[0], b.inputs["Height"])
    if bump:
        th = t.nodes.new("ShaderNodeTexImage"); th.image = img(bump, srgb=False); th.extension = "EXTEND"
        t.links.new(a.outputs["Vector"], th.inputs[0])
        b2 = t.nodes.new("ShaderNodeBump")
        b2.inputs["Strength"].default_value = 0.6; b2.inputs["Distance"].default_value = 0.05
        t.links.new(th.outputs[0], b2.inputs["Height"])
        t.links.new(b.outputs[0], b2.inputs["Normal"])
        t.links.new(b2.outputs[0], P.inputs["Normal"])
    else:
        t.links.new(b.outputs[0], P.inputs["Normal"])
    return m


def paper_quad(tex, w, h, loc, rot_euler=(0, 0, 0), curl=0.0, seed=0, n=40, rough=0.75, crumple=0.0):
    """A sheet of paper with a slight lift at the corners. Lies in XY, texture upright when viewed from +Z."""
    g = np.random.default_rng(seed)
    nx, ny = n, max(2, int(n * h / w))
    u, v_ = np.meshgrid(np.linspace(0, 1, nx), np.linspace(0, 1, ny))
    x, y = (u - 0.5) * w, (v_ - 0.5) * h
    z = curl * (((u - 0.5) * 2) ** 4 + ((v_ - 0.5) * 2) ** 4 * 0.6) + 0.01
    z = z + 0.02 * curl * np.sin(u * 7 + g.uniform(0, 6)) * np.sin(v_ * 5 + g.uniform(0, 6))
    if crumple:
        for _ in range(26):
            a = g.uniform(0, 6.283)
            d = np.cos(a) * x + np.sin(a) * y - g.uniform(-w / 2, w / 2) * 0.8
            z = z + crumple * g.uniform(0.3, 1) * np.abs(d) * g.uniform(0.04, 0.14)
        z = z - z.min() + 0.02
    vv = np.c_[x.ravel(), y.ravel(), z.ravel()].astype(np.float32)
    i = np.arange(nx * ny).reshape(ny, nx)
    q = np.c_[i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, 1:].ravel(), i[1:, :-1].ravel()]
    ob = add_mesh("paper", vv, q, smooth=not crumple)
    add_attr(ob, "uvw", np.c_[u.ravel(), v_.ravel(), np.zeros(nx * ny)], kind="FLOAT_VECTOR")
    m, p = principled("paper", rough=rough)
    t = m.node_tree
    a = t.nodes.new("ShaderNodeAttribute"); a.attribute_name = "uvw"
    ti = t.nodes.new("ShaderNodeTexImage"); ti.image = img(tex)
    t.links.new(a.outputs["Vector"], ti.inputs[0])
    t.links.new(ti.outputs[0], p.inputs["Base Color"])
    p.inputs["Specular IOR Level"].default_value = 0.25
    ob.data.materials.append(m)
    ob.location = loc
    ob.rotation_euler = rot_euler
    return ob


def haze(density, box=(-60, 60, -40, 60, -3, 70), col=(1.0, 0.86, 0.68)):
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (*col, 1)
    pv.inputs["Anisotropy"].default_value = 0.4
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(pv.outputs[0], o.inputs["Volume"])
    x0, x1, y0, y1, z0, z1 = box
    v = np.array([[x, y, z] for z in (z0, z1) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))], np.float32)
    q = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    b = add_mesh("haze", v, q, smooth=False)
    b.data.materials.append(m)
    bpy.context.scene.cycles.volume_bounces = 1
    bpy.context.scene.cycles.volume_step_rate = 4


def spot(loc, look, energy, angle=40, blend=0.3, radius=0.4, color=(1.0, 0.86, 0.66)):
    d = bpy.data.lights.new("spot", "SPOT")
    d.energy, d.color, d.spot_size, d.spot_blend, d.shadow_soft_size = energy, color, np.radians(angle), blend, radius
    ob = bpy.data.objects.new("spot", d)
    ob.location = Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y")
    bpy.context.scene.collection.objects.link(ob)
    return ob
