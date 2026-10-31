"""HKBU SCIE1007 coursework science video. T2 of the darkroom direction: the person is a fibre print on the drying line under the warm inspection lamp, the question hangs beside them under the safelight. The print border is what lets any phone clip sit in the film."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="t2"))
sc = dr.setup(A.samples, A.pct, bounces=6)
SAFE = (1.0, 0.022, 0.006)
WARM = (1.0, 0.70, 0.40)
box("wall", (-40, 12.4, -30), (40, 12.6, 30), pbr("wall", lin("1A1412"), rough=0.75))


def curl(a=0.2, b=0.14, seed=0):
    def f(U, V):
        return a * (1 - V) ** 2.2 * np.sin(U * math.pi + seed) + b * (np.abs(U - 0.5) * 2) ** 3 * (1 - V) + 0.05 * np.sin(V * 7 + U * 3 + seed) * (1 - V) + 0.03 * np.sin(U * 9 + seed)
    return f


PW, PH = 6.0, 7.5
QW, QH = 7.6, 7.6 * 1320 / 2200
Y_LINE = 4.45
px, qx = -3.2, 5.4
sheet("person", PW, PH, loc=(px, 0, Y_LINE - PH / 2), rot=(math.pi / 2, 0, math.radians(14)), nx=120, ny=150, warp=curl(0.34, 0.22, 0.4),
      mat=dr.paper_mat("person", os.path.join(WORK, "t2_person.png"), rough=0.5, spec=0.3))
sheet("q", QW, QH, loc=(qx, 7.4, Y_LINE + 0.25 - QH / 2), rot=(math.pi / 2, 0, math.radians(-16)), nx=120, ny=100, warp=curl(0.26, 0.2, 1.6),
      mat=dr.paper_mat("q", os.path.join(WORK, "t2_q.png"), rough=0.55, spec=0.3))
# line and pegs
wire = pbr("wire", lin("2A2522"), rough=0.4)
a, b = Vector((-18, -3.2, Y_LINE + 0.28)), Vector((24, 13.2, Y_LINE + 0.70))
d = b - a
bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=d.length, location=(a + b) / 2, vertices=12)
o = bpy.context.object
o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
o.data.materials.append(wire)
wood = pbr("peg", lin("6B5438"), rough=0.5)
for x, y0, z in [(px - 1.8, -0.75, Y_LINE + 0.1), (px + 1.8, 0.75, Y_LINE + 0.13), (qx - 2.2, 6.4, Y_LINE + 0.36), (qx + 2.2, 8.2, Y_LINE + 0.42)]:
    box(f"pega{x}", (x - 0.1, y0 - 0.1, z - 0.34), (x + 0.1, y0 - 0.02, z + 0.42), wood)
    box(f"pegb{x}", (x - 0.1, y0 + 0.02, z - 0.34), (x + 0.1, y0 + 0.1, z + 0.42), wood)

# warm inspection lamp only on the print; safelight on the rest of the room
spot("insp", (px + 6.5, -9, 3.0), (px, 0, 0.7), WARM, 3600, size=1.1, cone=50, blend=0.5)
spot("safe", (qx + 6, -3, 6.6), (qx, 7.2, 1.8), SAFE, 3800, size=1.0, cone=34, blend=0.6)
area("room", (12, 2, 7), (6, 10, 0), 8, 6, SAFE, 900)
camera((1.0, -19.0, 1.0), (1.3, 0, 0.5), lens=38, fstop=1.3, focus=19.2)
dr.render(sc, A.name)
