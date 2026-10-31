"""HKBU SCIE1007 coursework science video. Clay direction, T4 (W2): CDK20 seen for the first time.

Real surface, one unfired mass of soft clay under the desk lamp that has just come on. AI prediction = soft, unfired.
Real pLDDT decides which parts are left rough and pale. Only the label on the tag.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

sc = scene(samples=180)
v, q, conf = load_surface()
c = (v.min(0) + v.max(0)) / 2
v = (v - c) * 0.1 @ rot(90, 0, 0).T @ rot(0, 0, -14).T @ rot(-12, 0, 0).T
v *= 2.05
n = vertex_normals(v, q)
g = np.random.default_rng(4)
# real tail: rougher, less worked
lump = g.normal(size=(len(v), 3))
from_tail = np.clip((0.72 - conf) / 0.2, 0, 1)
wob = np.sin(v @ np.array([3.1, 1.2, 2.3]) + 1) * np.sin(v @ np.array([-1.7, 3.3, 1.1]))
v = v + n * (wob * from_tail * 0.07)[:, None]
# thumbs on the side the camera sees
front = np.nonzero(n[:, 1] < -0.45)[0]
idx = g.choice(front, 20, replace=False)
v2, fp, fm = thumbs(v, n, 0, centres=idx, R=1.25, depth=0.2)
v2[:, 2] -= v2[:, 2].min() + 1.9                      # plonked down: what would be under the table is squashed flat
v2[:, 2] = np.maximum(v2[:, 2], 0.0)
v2[:, 1] += 2.0
ob = add_mesh("cdk20", v2, q)
add_attr(ob, "conf", conf)
attach_clay(ob, fp, fm)
soft = clay_material("soft", (0.46, 0.35, 0.26), rough=0.5, sss=0.25, ridge=0.02, tail_col=(0.86, 0.82, 0.74))
ob.data.materials.append(soft)

table(back=20)
wall(y=30, col=(0.12, 0.06, 0.02))
cm = clay_material("crumb", (0.55, 0.49, 0.41), rough=0.6, sss=0.2)
crumbs(120, (-14, 14, -12, 2), cm, seed=3, avoid=lambda p: (np.hypot(p[:, 0], (p[:, 1] - 2) / 0.7) < 7.6))

# paper tag on a pin stuck in the clay
paper_quad("flag_label.png", 4.3, 0.59, (3.7, -7.7, 0.36), rot_euler=(np.radians(78), 0, np.radians(-3)), curl=0.02, seed=2)
spot((9, -13, 6), (3.7, -7.7, 0.3), 700, angle=16, blend=0.6, radius=0.3, color=(1.0, 0.92, 0.82))

# The lamp that just came on: tight, warm, from high left, room falls away to almost nothing
spot((-13, -7, 30), (0.4, 1.0, 2.5), 62000, angle=40, blend=0.3, radius=0.7)
area((17, -13, 5), (0, 0, 3), 420, 9, (0.5, 0.65, 1.0))
world_rgb((0.012, 0.012, 0.016), 1.0)
haze(0.0016)
camera((-3.0, -19.0, 1.0), (0.2, 0, 5.2), lens=26, dof=13.5, fstop=0.12)
print(render(sc, "T4"))
