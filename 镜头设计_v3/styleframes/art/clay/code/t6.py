"""HKBU SCIE1007 coursework science video. Clay direction, T6 (6-10): the road map.

A row of little model stations on the table, used 12 times in the film. Three are fired and glazed and sit in the lamp.
The fourth is soft clay and the lamp stops at its door. The last two have not been made yet: raw lumps. Props, not science.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

S8 = bool(os.environ.get("S8"))   # the same row at the end of the film: colour-script frame only
sc = scene(samples=90 if S8 else 160)
table(back=14)
wall(y=15, col=(0.62, 0.11, 0.05) if S8 else (0.80, 0.34, 0.04))

XS = [-12.5, -7.5, -2.5, 2.5, 7.5, 12.5]
SY = 2.2


def house(x, y):
    """A small hand-built station: walls, pitched roof, an arched door cut through, then softened by a voxel remesh."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 1.35))
    b = bpy.context.object
    b.scale = (3.0, 2.4, 2.7)
    apply_mods(b)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    v = np.array([[x - 1.9, y - 1.5, 2.6], [x + 1.9, y - 1.5, 2.6], [x + 1.9, y + 1.5, 2.6], [x - 1.9, y + 1.5, 2.6],
                  [x - 1.9, y - 0.0, 4.1], [x + 1.9, y - 0.0, 4.1]], np.float32)
    q = np.array([[0, 3, 2, 1], [0, 1, 5, 4], [2, 3, 4, 5], [3, 0, 4, 4], [1, 2, 5, 5]])
    roof = add_mesh("roof", v, q, smooth=False)
    u = b.modifiers.new("j", "BOOLEAN"); u.operation, u.object = "UNION", roof
    apply_mods(b)
    bpy.data.objects.remove(roof)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.62, depth=4, location=(x, y, 1.05), rotation=(np.radians(90), 0, 0))
    c1 = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.5))
    c2 = bpy.context.object
    c2.scale = (1.24, 4, 1.1)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for cut in (c1, c2):
        d = b.modifiers.new("d", "BOOLEAN"); d.operation, d.object = "DIFFERENCE", cut
        apply_mods(b)
        bpy.data.objects.remove(cut)
    remesh_smooth(b, voxel=0.05, smooth=6, factor=0.6)
    # built by hand: nothing is square
    gw = np.random.default_rng(int(x * 7) & 255)
    v, _n = get_vn(b)
    ph = gw.uniform(0, 6, 6)
    v[:, 0] += 0.11 * np.sin(v[:, 2] * 1.3 + ph[0]) + 0.05 * np.sin(v[:, 1] * 2.1 + ph[1])
    v[:, 1] += 0.09 * np.sin(v[:, 2] * 1.1 + ph[2]) + 0.05 * np.sin(v[:, 0] * 2.3 + ph[3])
    v[:, 2] += 0.09 * np.sin(v[:, 0] * 1.7 + ph[4]) * (v[:, 2] > 1) + 0.06 * np.sin(v[:, 1] * 2.2 + ph[5]) * (v[:, 2] > 1)
    b.data.vertices.foreach_set("co", v.ravel())
    b.data.update()
    b.data.polygons.foreach_set("use_smooth", np.ones(len(b.data.polygons), bool))
    b.data.update()
    b.data.materials.clear()   # the boolean leaves an empty slot 0, which renders as the default grey
    return b


def _unused(ob):
    v = np.zeros(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("co", v)
    n = np.zeros(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("normal", n)
    return v.reshape(-1, 3), n.reshape(-1, 3)


def glaze(name, col):
    m, p = principled(name, col, 0.12)
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.05
    t = m.node_tree
    tc = t.nodes.new("ShaderNodeTexCoord")
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4; nz.inputs["Detail"].default_value = 5
    t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    r = t.nodes.new("ShaderNodeValToRGB")
    e = r.color_ramp.elements
    e[0].position = 0.38; e[0].color = (col[0] * 0.74, col[1] * 0.74, col[2] * 0.74, 1)
    e[1].position = 0.62; e[1].color = (*col, 1)
    t.links.new(nz.outputs[0], r.inputs[0])
    t.links.new(r.outputs[0], p.inputs["Base Color"])
    return m


G = [glaze("g1", (0.95, 0.62, 0.05)), glaze("g2", (0.65, 0.06, 0.03)), glaze("g3", (0.02, 0.32, 0.36))]
soft = clay_material("soft", (0.46, 0.36, 0.27), rough=0.55, sss=0.25, ridge=0.02)
for x, m in zip(XS[:3], G):
    h = house(x, SY)
    h.data.materials.append(m)

# Station 4: same walls but raw, soft, thumbed, not fired
h4 = house(XS[3], SY)
v4, n4 = get_vn(h4)
v4b, fp, fm = thumbs(v4, n4, 9, seed=3, R=0.8, depth=0.09)
h4.data.vertices.foreach_set("co", v4b.ravel())
h4.data.update()
attach_clay(h4, fp, fm)
h4.data.materials.append(soft)

# Stations 5 and 6: not made yet, only the lump of clay they will come from
tv, tf = lump_template(5)
for k, x in enumerate(XS[4:]):
    gg = np.random.default_rng(40 + k)
    a = gg.normal(size=(7, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
    d = sum(gg.uniform(0.04, 0.12) * np.sin(gg.uniform(1.5, 4) * (tv @ u) + gg.uniform(0, 6)) for u in a)
    vv = tv * (1 + d[:, None]) * np.array([1.7, 1.5, 1.35]) + np.array([x, SY, 1.15])
    vv[:, 2] = np.maximum(vv[:, 2], 0.0)
    l = add_mesh("lump", vv, tf, tris=True)
    vv2, fp2, fm2 = thumbs(vv, tv, 6, seed=50 + k, R=0.8, depth=0.1)
    l.data.vertices.foreach_set("co", vv2.ravel()); l.data.update()
    attach_clay(l, fp2, fm2)
    l.data.materials.append(soft)

# The road: a rolled and pressed coil, glazed as far as station 4's door, then broken unfired pieces
RY = -1.15
DOOR = XS[3]
path = np.linspace(-15.2, DOOR, 180)
ty = RY + 0.16 * np.sin(path * 0.9)
sides = 12
th = np.linspace(0, 6.283, sides, endpoint=False)
vv = []
for x, y in zip(path, ty):
    rr = 0.32 + 0.015 * np.sin(x * 3.1)
    vv.append(np.c_[np.full(sides, x), y + np.cos(th) * rr * 1.5, 0.02 + (np.sin(th) + 1) * rr * 0.42])
vv = np.concatenate(vv).astype(np.float32)
qq = []
for i in range(len(path) - 1):
    for k in range(sides):
        qq.append([i * sides + k, (i + 1) * sides + k, (i + 1) * sides + (k + 1) % sides, i * sides + (k + 1) % sides])
rd = add_mesh("road", vv, np.array(qq))
rd.data.materials.append(glaze("road", (0.90, 0.80, 0.62)))
# dashes
gd = np.random.default_rng(6)
tv2, tf2 = lump_template(3)
xd = DOOR + 1.15
vs, fs = [], []
i = 0
while xd < 15.2:
    a = gd.normal(size=(3, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
    d = sum(gd.uniform(0.03, 0.09) * np.sin(gd.uniform(2, 4) * (tv2 @ u) + gd.uniform(0, 6)) for u in a)
    vvv = tv2 * (1 + d[:, None]) * np.array([0.42, 0.3, 0.17]) + np.array([xd, RY + 0.16 * np.sin(xd * 0.9), 0.16])
    vs.append(vvv); fs.append(tf2 + i * len(tv2)); i += 1
    xd += 1.2
dash = add_mesh("dash", np.concatenate(vs), np.concatenate(fs), tris=True)
add_attr(dash, "fp", np.zeros((len(dash.data.vertices), 3)), kind="FLOAT_VECTOR")
add_attr(dash, "fpm", np.zeros(len(dash.data.vertices)))
dash.data.materials.append(soft)

# 048: one bright glazed bead on the road at the door of station 4
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.46, location=(DOOR - 0.9, RY, 0.55))
bd = bpy.context.object
bpy.ops.object.shade_smooth()
bd.data.materials.append(glaze("bead", (0.03, 0.10, 0.62)))

# Paper flags on cocktail sticks, facing the camera
pick, _ = principled("stick", (0.72, 0.52, 0.32), 0.6)


def flagpost(tex, x, y, z, w=4.25, h=1.72, lean=0.0, base=None):
    paper_quad(tex, w, h, (x, y, z), rot_euler=(np.radians(85), 0, np.radians(lean)), curl=0.03, seed=int(x * 10) & 255, n=16)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=z, location=(x, y + 0.3, z / 2))
    s = bpy.context.object
    s.data.materials.append(pick)


Y = SY - 0.2
names = ["target", "hit", "improve", "cells", "trials", "approval"]
for i, (x, nm) in enumerate(zip(XS, names)):
    flagpost(f"flag_{nm}.png", x, Y, 6.0, lean=(-1) ** i * 1.2)
for x in XS[3:]:
    flagpost("flag_nr.png", x, Y - 0.1, 7.95, h=1.02)
paper_quad("flag_048.png", 1.6, 0.92, (DOOR - 1.75, -3.25, 0.6), rot_euler=(np.radians(60), 0, np.radians(-6)), curl=0.02, seed=9, n=10)

crumbs(70, (-15.5, 15.5, -7, 0.5), clay_material("crumb", (0.5, 0.41, 0.32), rough=0.7, sss=0.1), seed=12, rmin=0.03, rmax=0.15,
       avoid=lambda p: np.abs(p[:, 1] - RY) < 0.8)

# Lamp over the finished half. Its edge is the story: it stops at the door of station 4.
if S8:
    area((0, -12, 20), (0, 2, 2), 7000, 26, (1.0, 0.74, 0.5))
else:
    spot((-9.5, -9, 28), (-5.2, 1.0, 0), 34000, angle=47, blend=0.14, radius=0.35)
    spot((-8, -4, 24), (-9.5, 15, 7), 26000, angle=52, blend=0.12, radius=0.35)
area((14, -14, 9), (8, 2, 2), 220, 8, (0.45, 0.58, 1.0))
world_rgb((0.018, 0.018, 0.024), 1.0)
camera((0.0, -33.0, 9.0), (0.0, 0.0, 4.15), lens=42)
for o in bpy.data.objects:
    if o.type == "MESH" and len(o.data.polygons) > 3000:
        print("DBG", o.name, o.data.name, len(o.data.polygons), [m.name if m else None for m in o.data.materials], [ms.link for ms in o.material_slots], set(np.array([p.material_index for p in o.data.polygons[:5000]]).tolist()), o.hide_render)
if not os.environ.get("DBG"):
    print(render(sc, "../_work/S8" if S8 else "T6"))
