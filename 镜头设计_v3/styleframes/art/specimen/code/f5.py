"""HKBU SCIE1007 coursework science video. F5 plate: two graduated glass tubes lying on their side, true linear scale. 0 nM at x = 120 px, 6,000 nM at x = 1620 px, so 0.25 px per nM on screen. 001 runs off the frame because the paper only gives a lower limit. 048 is 33.4 nM of the same tube: 8.35 px."""
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/specimen/code")
import sp
from sp import gk

A = sp.args()
sc = sp.scene(A["samples"], A["pct"])
PX = 400                               # px per unit
WIDTH = 1920 / PX
X0 = (120 - 960) / PX                  # world x of 0 nM
NM = 0.25 / PX                         # world units per nM
Y1, Y2 = (540 - 318) / PX, (540 - 560) / PX   # tube centres on screen: y = 318 and y = 560
R = 0.075


def rod(x0, x1, z, r, mat, ends=False):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=x1 - x0, location=((x0 + x1) / 2, 0, z), rotation=(0, math.pi / 2, 0))
    o = bpy.context.object
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    o.data.materials.append(mat)
    if ends:
        m = o.modifiers.new("b", "BEVEL")
        m.width, m.segments, m.limit_method = r * 0.96, 16, "ANGLE"
    return o


G = gk.glass(tint=(0.95, 0.97, 1.0), rough=0.02)
RL = gk.liquid(sp.RED, glow=0.55)
RIGHT = 6.0                             # far beyond the right edge of frame
for z in (Y1, Y2):
    rod(X0 - 0.12, RIGHT, z, R, G, ends=True)
rod(X0, RIGHT, Y1, R - 0.012, RL)                 # 001: goes on past the frame, no end on it
rod(X0, X0 + 33.4 * NM, Y2, R - 0.012, RL)        # 048: 33.4 nM of the same scale

sp.ortho((0, -10, 0), (0, 0, 0), WIDTH)
sp.softbox("top", (0, -1.5, 4), (0, 0, 0), 9, 16, 0.5, (0.45, 0.55, 1.0))
sp.softbox("bot", (0, -1.5, -4), (0, 0, 0), 9, 16, 0.5, (0.45, 0.55, 1.0))
sp.softbox("hl", (0, -5, 1.4), (0, 0, 0), 1.6, 16, 0.5)
gk.render(sp.PLATES + "f5.png")
