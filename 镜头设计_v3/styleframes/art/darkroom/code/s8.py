"""HKBU SCIE1007 coursework science video. S8 of the darkroom direction, for the colour script only: the bench in the dark with one crack of daylight from the door. Only a crack, because 048 is not a medicine yet."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="s8"))
sc = dr.setup(A.samples, A.pct, bounces=5)
DAY = (1.0, 0.93, 0.80)
wall_m = pbr("wall", lin("100E10"), rough=0.7)
box("wallL", (-30, 12, -2), (1.15, 12.4, 16), wall_m)
box("wallR", (1.32, 12, -2), (30, 12.4, 16), wall_m)
box("lintel", (1.1, 12, 10.5), (1.4, 12.4, 16), wall_m)
box("floor", (-30, -30, -2.1), (30, 12, -2), pbr("floor", lin("1A1818"), rough=0.32, spec=0.6))
sheet("day", 6, 16, loc=(1.24, 13.2, 6), rot=(math.pi / 2, 0, 0), nx=1, ny=1, mat=emit("day", DAY, 26))
area("spill", (1.24, 13, 5), (1.0, 0, -2), 0.2, 9, DAY, 900)
camera((-3.2, -12, 2.2), (0.2, 6, 2.4), lens=38)
dr.render(sc, A.name)
