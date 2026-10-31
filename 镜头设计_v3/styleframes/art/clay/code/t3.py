"""HKBU SCIE1007 coursework science video. Clay direction, T3 (3-08): the darkest moment.

A block of dark clay with one empty keyhole pushed through it. A prop, not a structure, so it carries the crumpled paper
tag every schematic gets in this film. Nothing has been lit yet except a sliver along the table.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa
from PIL_free import keyhole  # noqa

sc = scene(samples=160)
table(back=20, dark=1.0)
wall(y=30, col=(0.003, 0.003, 0.003))

NX, NY = 620, 470
W, H = 17.0, 12.9
x, y = np.meshgrid(np.linspace(-W / 2, W / 2, NX), np.linspace(-H / 2, H / 2, NY))
g = np.random.default_rng(3)
z = np.zeros_like(x) + 1.5
ph = g.uniform(0, 6, 12)
z += 0.11 * np.sin(x * 0.8 + ph[0]) * np.sin(y * 0.7 + ph[1]) + 0.07 * np.sin(x * 1.7 + ph[2] + y * 0.6) + 0.04 * np.sin(y * 2.9 + ph[3] - x)
m = keyhole(x, y)                                        # 1 inside the hole, soft lip a little outside
lip = np.clip(1 - m["d"] / 0.5, 0, 1) ** 2
z = z + lip * 0.16 * (m["d"] > 0) - 3.6 * (m["d"] <= 0)   # pushed through by a finger, a raised lip round it
e = np.minimum.reduce([x + W / 2, W / 2 - x, y + H / 2, H / 2 - y])
z = z * np.sqrt(np.clip(e / 0.7, 0.0, 1.0))
vv = np.c_[x.ravel(), y.ravel(), z.ravel()].astype(np.float32)
i = np.arange(NX * NY).reshape(NY, NX)
q = np.c_[i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, 1:].ravel(), i[1:, :-1].ravel()]
ob = add_mesh("block", vv, q)
n = np.tile(np.array([0, 0, 1.0], np.float32), (len(vv), 1))
idx = g.choice(np.nonzero((m["d"].ravel() > 0.8) & (m["d"].ravel() < 3.0))[0], 9, replace=False)
v2, fp, fm = thumbs(vv, n, 0, centres=idx, R=1.0, depth=0.12)
ob.data.vertices.foreach_set("co", v2.ravel()); ob.data.update()
attach_clay(ob, fp, fm)
ob.data.materials.append(clay_material("dark", (0.022, 0.018, 0.016), rough=0.42, sss=0.05, ridge=0.008))
ob.location = (1.6, 1.0, 0)

paper_quad("flag_sch.png", 11.0, 1.54, (-3.2, -9.2, 0.05), rot_euler=(0, 0, np.radians(2)), crumple=0.22, seed=4, n=70)
paper_quad("flag_sch2.png", 3.8, 1.24, (7.0, -9.1, 0.05), rot_euler=(0, 0, np.radians(-3)), crumple=0.3, seed=8, n=50)

spot((-26, 8, 9), (2, 1, 1.5), 20000, angle=46, blend=0.5, radius=0.4, color=(1.0, 0.86, 0.72))
spot((-3, -20, 22), (0, -9.3, 0), 3200, angle=44, blend=0.5, radius=0.5, color=(1.0, 0.9, 0.8))
world_rgb((0.001, 0.001, 0.0014), 1.0)
camera((0.0, -24.0, 34.0), (0.0, -3.0, 0.0), lens=50)
print(render(sc, "T3"))
