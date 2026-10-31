"""HKBU SCIE1007 coursework science video. Clay direction, T5 (W4): the key turns.

Straight down on the table. Measured = white glazed fired tile with cobalt lettering, hard and glossy. Our re-docking =
pencil on paper, drawn from the project's own 048 render (redrawn, structure unchanged), in a dashed pencil box.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *  # noqa

sc = scene(samples=160)
table(back=20)

# pencil sheet, left
paper_quad("pencil.png", 12.7, 15.24, (-7.5, -0.05, 0.03), rot_euler=(0, 0, np.radians(2.5)), curl=0.25, seed=3)

# fired tile, right
t = rounded_slab(15.0, 8.7, 0.55, bevel=0.17)
t.location = (6.9, 2.75, 0.02)
t.rotation_euler = (0, 0, np.radians(-1.6))
t.data.materials.append(glazed_mat("t5", "tile_t5.png", "tile_t5_h.png"))

# caption slip
paper_quad("flag_caption.png", 14.6, 3.3, (7.0, -4.6, 0.03), rot_euler=(0, 0, np.radians(1.0)), curl=0.12, seed=4)

# a real pencil laid across the corner of the sheet
R, L = 0.3, 10.0
th = np.linspace(0, 6.283, 7)[:-1]
ring = np.c_[R * np.cos(th), R * np.sin(th)]
xs = [-L / 2, L / 2]
vv = []
for x in xs:
    vv.append(np.c_[np.full(6, x), ring])
vv = np.concatenate(vv + [[[L / 2 + 1.1, 0, 0]], [[-L / 2, 0, 0]]]).astype(np.float32)
fa = [[k, (k + 1) % 6, (k + 1) % 6 + 6, k + 6] for k in range(6)]
tris = []
for k in range(6):
    tris += [[k + 6, (k + 1) % 6 + 6, 12, 12], [(k + 1) % 6, k, 13, 13]]
pen = add_mesh("pencil", vv, np.array(fa + tris), smooth=False)
pm, pp = principled("pen", (0.9, 0.55, 0.03), 0.3)
g2 = pm.node_tree
geo = g2.nodes.new("ShaderNodeTexCoord")
sx = g2.nodes.new("ShaderNodeSeparateXYZ")
g2.links.new(geo.outputs["Object"], sx.inputs[0])
ramp = g2.nodes.new("ShaderNodeValToRGB")
e = ramp.color_ramp.elements
e[0].position = 0.905; e[0].color = (0.9, 0.55, 0.03, 1)
e[1].position = 0.91; e[1].color = (0.82, 0.62, 0.42, 1)
e2 = ramp.color_ramp.elements.new(0.97); e2.color = (0.82, 0.62, 0.42, 1)
e3 = ramp.color_ramp.elements.new(0.975); e3.color = (0.03, 0.03, 0.035, 1)
mr = g2.nodes.new("ShaderNodeMapRange")
mr.inputs[1].default_value = -L / 2; mr.inputs[2].default_value = L / 2 + 1.1
g2.links.new(sx.outputs["X"], mr.inputs[0])
g2.links.new(mr.outputs[0], ramp.inputs[0])
g2.links.new(ramp.outputs[0], pp.inputs["Base Color"])
pen.data.materials.append(pm)
pen.location = (-2.0, -2.4, 0.31)
pen.rotation_euler = (0, 0, np.radians(106))

# dry scraps
cm = clay_material("crumb", (0.55, 0.44, 0.34), rough=0.7, sss=0.1)
crumbs(70, (-14.5, 14.5, -8.3, 8.3), cm, seed=8, rmin=0.04, rmax=0.26,
       avoid=lambda p: (np.abs(p[:, 0] - 6.9) < 8) & (p[:, 1] > -6.4) | (np.abs(p[:, 0] + 7.5) < 6.2) & (np.abs(p[:, 1]) < 7.5))

# lamp high on the left gives hard shadows; a thin strip reflects as a single streak in the tile's far corner
spot((-30, 18, 26), (2, 0, 0), 110000, angle=60, blend=0.6, radius=0.5)
a = area((23, 11, 26), (9, 5, 0), 300, 1, (1.0, 0.97, 0.92))
a.data.shape = "RECTANGLE"; a.data.size = 0.7; a.data.size_y = 22
area((10, -20, 30), (0, 0, 0), 1400, 18, (0.75, 0.84, 1.0))
world_rgb((0.14, 0.13, 0.13), 1.0)
camera((0.0, 0.0, 41.0), (0.0, 0.001, 0.0), lens=50)
print(render(sc, "T5"))
