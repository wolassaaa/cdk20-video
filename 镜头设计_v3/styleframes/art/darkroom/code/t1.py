"""HKBU SCIE1007 coursework science video. T1 of the darkroom direction: a silver print of the real liver lying wet in the developer tray under the safelight. One sheet, one lamp, everything else black."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="t1"))
sc = dr.setup(A.samples, A.pct, bounces=8)
SAFE = (1.0, 0.022, 0.006)
PW, PH = 10.0, 10.0 * 2200 / 3000
TX, TY, D = 7.2, 5.6, 0.75

ink = pbr("tray", lin("0B0908"), rough=0.32, spec=0.5)
box("base", (-TX - 0.4, -TY - 0.4, -D - 0.1), (TX + 0.4, TY + 0.4, -D), ink)
box("wallB", (-TX - 0.4, TY, -D), (TX + 0.4, TY + 0.4, 0.28), ink)
box("wallF", (-TX - 0.4, -TY - 0.4, -D), (TX + 0.4, -TY, 0.28), ink)
box("wallL", (-TX - 0.4, -TY, -D), (-TX, TY, 0.28), ink)
box("wallR", (TX, -TY, -D), (TX + 0.4, TY, 0.28), ink)
# ribs in the tray floor, the way real trays are moulded
for x in np.arange(-6.6, 7, 1.5):
    box(f"rib{x}", (x, -TY, -D), (x + 0.12, TY, -D + 0.06), ink)
box("bench", (-60, -60, -D - 0.6), (60, 60, -D - 0.1), pbr("bench", lin("060505"), rough=0.6))


def cockle(U, V):
    return 0.05 * np.sin(U * 3.1 + 0.5) * np.sin(V * 2.3 + 1.0) + 0.09 * (np.clip(0.06 - U, 0, 1) / 0.06) ** 2 + 0.07 * (np.clip(V - 0.95, 0, 1) / 0.05) ** 2


sheet("print", PW, PH, loc=(0.12, 0.05, -D + 0.32), rot=(0, 0, math.radians(-3.2)), nx=160, ny=120, warp=cockle,
      mat=dr.paper_mat("print", os.path.join(WORK, "t1_print.png"), rough=0.5, spec=0.35))
box("liquid", (-TX + 0.01, -TY + 0.01, -D + 0.01), (TX - 0.01, TY - 0.01, 0), dr.liquid("dev", tint=(1, 0.8, 0.7), density=0.0, rings=(-3, 3), ring_scale=0.22, ring_amp=0.012, noise_amp=0.012, rough=0.09))

# safelight hung high and behind the sheet: its round reflection sits soft in the wet surface; a second soft spill lights the paper and dies toward the edges, and is not seen in the liquid
d = bpy.data.lights.new("safe", "AREA")
d.shape, d.size, d.size_y, d.color, d.energy = "ELLIPSE", 2.2, 2.2, SAFE, 1500
o = link(bpy.data.objects.new("safe", d))
o.location = (-8.2, 11.0, 7.6)
o.rotation_euler = (Vector((-8.2, 11.0, 7.6)) - Vector((-2, 2, 0))).to_track_quat("Z", "Y").to_euler()
sp = spot("spill", (-1.2, -2.0, 10.5), (0.2, -0.9, 0), SAFE, 1300, size=1.8, cone=74, blend=1.0)
sp.visible_glossy = False
camera((0.0, -9.4, 11.4), (0.1, 0.08, -0.25), lens=42, fstop=0.9, focus=14.6)
dr.render(sc, A.name)
