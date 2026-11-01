"""HKBU SCIE1007 coursework science video. F6 plate: the six stations of the road map as six glass tubes. Orthographic row."""
import json
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/specimen/code")
import sp
from sp import gk

A = sp.args()
sc = sp.scene(A["samples"], A["pct"])
FILL = [0.86, 0.86, 0.86, 0.30, 0, 0]
R, H, GAP = 0.17, 1.42, 0.96
PX = 300                                # px per unit
WIDTH = 1920 / PX
gk.floor_mirror(rough=0.12)
G = gk.glass()
L = gk.liquid(sp.RED, glow=1.0)
for i, f in enumerate(FILL):
    gk.tube((i - 2.5) * GAP, 0, fill=f, r=R, h=H, mat_glass=G, mat_liq=L)
EL = math.radians(5)
T = Vector((0, 0, 0.62))
pos = T + 12 * Vector((0, -math.cos(EL), math.sin(EL)))
cam = sp.ortho(pos, T, WIDTH)
gk.rig_cold(k=1.0)
sp.softbox("front", (-3, -6, 3), (0, 0, 1), 2.0, 4, 4)
gk.render(sp.PLATES + "f6.png")

from bpy_extras.object_utils import world_to_camera_view as w2c
pts = []
for i, f in enumerate(FILL):
    x = (i - 2.5) * GAP
    a = w2c(sc, cam, Vector((x, 0, R + H)))
    b = w2c(sc, cam, Vector((x, 0, 0)))
    c = w2c(sc, cam, Vector((x, 0, R + H * f)))
    pts.append({"x": a.x * 1920, "top": (1 - a.y) * 1080, "bottom": (1 - b.y) * 1080, "liquid": (1 - c.y) * 1080})
json.dump(pts, open(sp.PLATES + "f6.json", "w"))
print("POINTS", pts)
