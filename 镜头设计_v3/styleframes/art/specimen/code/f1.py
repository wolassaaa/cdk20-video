"""HKBU SCIE1007 coursework science video. F1 plate: the real liver (BodyParts3D, DBCLS, CC BY 4.0) as a glass specimen, whole organ in frame. 1 unit = 100 mm, orthographic, so the scale bar is true."""
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
WIDTH = 4.0  # image width in units: 480 px per 100 mm
AZ, EL = math.radians(14), math.radians(-6)
TARGET = Vector((-0.64, 0.0, -0.06))  # puts the organ in the right two thirds of the frame

skin = gk.liver_skin(sp.shell(blend=0.28, edge=0.46, rough=0.14, haze=0.03, fill=0.045, rgb=(0.82, 0.86, 0.95)))
gk.stl("portal_vein_hepatic", sp.tissue(sp.RED, glow=0.42), subdiv=1)
gk.stl("portal_tributaries_splenic_SMV", sp.tissue(sp.RED, glow=0.42), keep=lambda c: c.z > 1030 and c.x < 25, subdiv=1)
gk.stl("hepatic_veins", sp.tissue(sp.BLUE, glow=0.22), subdiv=1)

pos = TARGET + 9 * Vector((-math.sin(AZ) * math.cos(EL), -math.cos(AZ) * math.cos(EL), math.sin(EL)))
sp.ortho(pos, TARGET, WIDTH)
fwd = (TARGET - pos).normalized()
right = fwd.cross(Vector((0, 0, 1))).normalized()
up = right.cross(fwd)
rel = lambda x, y, z: tuple(TARGET + right * x + up * y + fwd * z)
sp.softbox("key", rel(2.2, 2.4, -4), tuple(TARGET), 2.6, 5, 4)
sp.softbox("fill", rel(-3.5, 0.2, -3.5), tuple(TARGET), 0.8, 4, 4)
sp.softbox("rimL", rel(-3.6, 0.4, 3.0), tuple(TARGET), 30, 0.3, 6, (0.9, 0.93, 1.0))
sp.softbox("rimR", rel(3.8, 1.0, 2.6), tuple(TARGET), 14, 0.3, 5, (0.9, 0.93, 1.0))
gk.render(sp.PLATES + "f1.png")
json.dump({"px_per_100mm": 1920 / WIDTH}, open(sp.PLATES + "f1.json", "w"))
