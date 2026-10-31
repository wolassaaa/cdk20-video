"""HKBU SCIE1007 coursework science video. Clay direction, T1 (1-02): the heaviest shot.

The table is almost gone. One real liver (BodyParts3D) pressed from near-black clay, one fired black tile standing like a
headstone with the number on it. A measured number is fired and glazed, as everywhere in the film. No colour, no crumbs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

sc = scene(samples=180)
table(back=20, dark=1.0)
wall(y=30, col=(0.004, 0.004, 0.004))

bpy.ops.wm.stl_import(filepath=str(ROOT / "assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"))
L = bpy.context.selected_objects[0]
vv, _ = get_vn(L)
bb = vv.max(0) - vv.min(0)
print("liver bbox", vv.min(0), vv.max(0))
L.data.vertices.foreach_set("co", ((vv - (vv.max(0) + vv.min(0)) / 2) * (11.0 / bb.max())).ravel())
L.data.update()
remesh_smooth(L, voxel=0.26, smooth=4, factor=0.6)   # closes the gaps between the atlas's segments: one piece of clay
remesh_smooth(L, voxel=0.05, smooth=8, factor=0.6)
v, n = get_vn(L)
R = rot(*[float(x) for x in os.environ.get("LIVER_ROT", "0,0,0").split(",")])
v = v @ R.T
n = n @ R.T
g = np.random.default_rng(2)
idx = g.choice(np.nonzero(n[:, 1] < -0.2)[0], 14, replace=False)
v2, fp, fm = thumbs(v, n, 0, centres=idx, R=0.95, depth=0.1)
v2[:, 2] -= v2[:, 2].min() + 0.55
v2[:, 2] = np.maximum(v2[:, 2], 0)
v2 += np.array([-4.6, 5.0, 0], np.float32)
L.data.vertices.foreach_set("co", v2.ravel())
L.data.update()
attach_clay(L, fp, fm)
L.data.polygons.foreach_set("use_smooth", np.ones(len(L.data.polygons), bool))
L.data.update()
L.data.materials.append(clay_material("liver", (0.055, 0.012, 0.012), rough=0.36, sss=0.15, ridge=0.012))

t = rounded_slab(8.8, 4.4, 0.42, bevel=0.14)
t.rotation_euler = (np.radians(80), 0, np.radians(-4))
t.location = (3.6, -3.5, 2.2)
t.data.materials.append(glazed_mat("t1", "tile_t1.png", "tile_t1_h.png"))

spot((-9, -2, 26), (-4.6, 5.0, 3.0), 15000, angle=34, blend=0.5, radius=0.5, color=(1.0, 0.9, 0.82))
spot((10, -22, 15), (3.6, -3.4, 2.2), 3400, angle=27, blend=0.6, radius=0.6, color=(1.0, 0.94, 0.88))
spot((9, 26, 11), (-4.6, 5.0, 4.0), 5000, angle=26, blend=0.5, radius=0.5, color=(0.72, 0.76, 0.86))
world_rgb((0.0015, 0.0015, 0.002), 1.0)
camera((-0.5, -26.0, 6.6), (0.0, 0.0, 3.6), lens=40, dof=24.0, fstop=0.4)
print(render(sc, "T1"))
