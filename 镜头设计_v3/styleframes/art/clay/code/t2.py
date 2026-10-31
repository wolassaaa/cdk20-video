"""HKBU SCIE1007 coursework science video. Clay direction, T2 (2-02): a person sits behind the table and speaks.

The person is a flat plate behind the table edge: that is how the phone footage will arrive, cut out and warm graded.
Here the plate is a side-on stand-in (make_tex.py person), lit like the lamp in the shot. Question on a card taped to the wall.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

sc = scene(samples=160)
BACK = 7.0
table(back=BACK)
wall(y=18, col=(0.82, 0.42, 0.06))

# person plate
W, H = 14.0, 17.0
v = np.array([[-W / 2, 0, 0], [W / 2, 0, 0], [W / 2, 0, H], [-W / 2, 0, H]], np.float32)
pl = add_mesh("person", v, np.array([[0, 1, 2, 3]]), smooth=False)
add_attr(pl, "uvw", np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], np.float32), kind="FLOAT_VECTOR")
m = bpy.data.materials.new("plate")
m.use_nodes = True
t = m.node_tree
t.nodes.clear()
o = t.nodes.new("ShaderNodeOutputMaterial")
a = t.nodes.new("ShaderNodeAttribute"); a.attribute_name = "uvw"
ti = t.nodes.new("ShaderNodeTexImage"); ti.image = img("person.png"); ti.extension = "CLIP"
t.links.new(a.outputs["Vector"], ti.inputs[0])
em = t.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 1.0
t.links.new(ti.outputs[0], em.inputs["Color"])
tr = t.nodes.new("ShaderNodeBsdfTransparent")
mx = t.nodes.new("ShaderNodeMixShader")
t.links.new(ti.outputs["Alpha"], mx.inputs[0])
t.links.new(tr.outputs[0], mx.inputs[1])
t.links.new(em.outputs[0], mx.inputs[2])
t.links.new(mx.outputs[0], o.inputs["Surface"])
pl.data.materials.append(m)
pl.location = (-7.0, BACK + 2.5, -4.0)

# question card taped to the wall
paper_quad("card.png", 15.0, 11.25, (8.8, 17.75, 8.3), rot_euler=(np.radians(90), np.radians(-1.2), 0), curl=0.02, seed=5, n=20)
tape, tp = principled("tape", (0.86, 0.78, 0.55), 0.5)
for x, z, r in ((3.2, 13.8, 14), (14.4, 13.8, -12)):
    v = np.array([[-1.3, 0, -0.32], [1.3, 0, -0.32], [1.3, 0, 0.32], [-1.3, 0, 0.32]], np.float32)
    k = add_mesh("tape", v, np.array([[0, 1, 2, 3]]), smooth=False)
    k.location = (x, 17.7, z); k.rotation_euler = (0, np.radians(r), 0)
    k.data.materials.append(tape)

# what is on the table: this morning's soft lump, thumbed, not yet anything
tv, tf = lump_template(6)
g = np.random.default_rng(3)
ax = g.normal(size=(6, 3)); ax /= np.linalg.norm(ax, axis=1, keepdims=True)
d = sum(g.uniform(0.05, 0.1) * np.sin(g.uniform(1.5, 3.5) * (tv @ u) + g.uniform(0, 6)) for u in ax)
vv = tv * (1 + d[:, None]) * np.array([2.6, 2.2, 1.7]) + np.array([8.0, -3.6, 1.45])
vv[:, 2] = np.maximum(vv[:, 2], 0.0)
L = add_mesh("lump", vv, tf, tris=True)
vv2, fp, fm = thumbs(vv, tv, 12, seed=4, R=1.15, depth=0.26)
L.data.vertices.foreach_set("co", vv2.ravel()); L.data.update()
attach_clay(L, fp, fm)
clay = clay_material("soft", (0.46, 0.36, 0.27), rough=0.5, sss=0.25, ridge=0.02)
L.data.materials.append(clay)
crumbs(90, (-16, 16, -13, 5), clay, seed=7, rmin=0.04, rmax=0.22, avoid=lambda p: np.hypot(p[:, 0] - 8.0, p[:, 1] + 3.6) < 3.2)

# desk lamp high right, warm, falling on the card and the person's lit side
spot((10, -7, 27), (5, 8, 5), 42000, angle=75, blend=0.7, radius=1.6)
area((-18, -8, 12), (-7, 9, 7), 500, 10, (1.0, 0.8, 0.62))
spot((22, -12, 3.6), (8.0, -3.6, 1.6), 4200, angle=20, blend=0.5, radius=0.25, color=(1.0, 0.86, 0.72))
world_rgb((0.16, 0.13, 0.11), 1.0)
camera((0.5, -27.0, 10.5), (0.5, 5.0, 4.9), lens=36, dof=36.5, fstop=0.3)
print(render(sc, "T2"))
