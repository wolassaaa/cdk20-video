"""HKBU SCIE1007 coursework science video. Clay direction, colour-script frame for S7 (three suggestions).

Cool morning light on the same table: three fresh lumps, nothing fired yet. Only used as a strip in colour_script.png.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

sc = scene(samples=90)
table(back=14)
wall(y=15, col=(0.20, 0.34, 0.46))
soft = clay_material("soft", (0.62, 0.55, 0.46), rough=0.55, sss=0.25, ridge=0.02)
tv, tf = lump_template(5)
for k, x in enumerate((-7.0, 0.0, 7.0)):
    gg = np.random.default_rng(70 + k)
    a = gg.normal(size=(7, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
    d = sum(gg.uniform(0.04, 0.12) * np.sin(gg.uniform(1.5, 4) * (tv @ u) + gg.uniform(0, 6)) for u in a)
    vv = tv * (1 + d[:, None]) * np.array([2.3, 2.0, 1.8]) + np.array([x, 1.0, 1.6])
    vv[:, 2] = np.maximum(vv[:, 2], 0.0)
    l = add_mesh("lump", vv, tf, tris=True)
    vv2, fp, fm = thumbs(vv, tv, 6, seed=80 + k, R=0.9, depth=0.14)
    l.data.vertices.foreach_set("co", vv2.ravel()); l.data.update()
    attach_clay(l, fp, fm)
    l.data.materials.append(soft)
area((-16, -14, 22), (0, 1, 1), 5200, 22, (0.72, 0.84, 1.0))
area((18, -6, 8), (0, 1, 2), 500, 10, (1.0, 0.92, 0.84))
world_rgb((0.20, 0.25, 0.30), 1.0)
camera((0.0, -24.0, 7.0), (0.0, 0.0, 3.0), lens=40)
print(render(sc, "../_work/S7"))
