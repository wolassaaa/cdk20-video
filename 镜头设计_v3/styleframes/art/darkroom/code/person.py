"""HKBU SCIE1007 coursework science video. Grey stand-in for a teammate filmed on a phone: a plain clay bust in an ordinary room with window light, framed the way a phone on a shelf would. It is only there to show how the print treats real footage."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args()
sc = dr.setup(A.samples, A.pct, bounces=5)
sc.render.resolution_x, sc.render.resolution_y = 1200, 1500
# a dress-form bust lofted from cross sections, so head, neck and shoulder run as one surface
# z, half width, half depth, forward offset
P = np.array([(1.724, 0.030, 0.034, -0.015), (1.720, 0.046, 0.054, -0.015), (1.708, 0.064, 0.074, -0.015), (1.688, 0.080, 0.092, -0.015), (1.655, 0.090, 0.103, -0.015),
              (1.590, 0.094, 0.108, -0.018), (1.540, 0.090, 0.104, -0.022), (1.495, 0.078, 0.092, -0.030), (1.455, 0.062, 0.076, -0.024),
              (1.425, 0.056, 0.062, -0.008), (1.395, 0.058, 0.060, 0.002), (1.365, 0.066, 0.064, 0.006), (1.340, 0.092, 0.074, 0.008),
              (1.318, 0.135, 0.086, 0.010), (1.298, 0.178, 0.096, 0.012), (1.276, 0.212, 0.104, 0.012), (1.245, 0.232, 0.110, 0.010),
              (1.200, 0.240, 0.116, 0.006), (1.120, 0.238, 0.122, 0.000), (1.000, 0.226, 0.122, 0.000), (0.700, 0.212, 0.118, 0.000)])
zz = np.linspace(P[0, 0], P[-1, 0], 260)
rows = [np.interp(-zz, -P[:, 0], P[:, i]) for i in (1, 2, 3)]
ker = np.ones(7) / 7
rows = [np.convolve(np.pad(r, 3, mode="edge"), ker, mode="valid") for r in rows]
N = 96
th = np.linspace(0, 2 * np.pi, N, endpoint=False)
cs, sn = np.cos(th), np.sin(th)
ex = 2 / 2.5
vs = []
for i, z in enumerate(zz):
    x = rows[0][i] * np.sign(cs) * np.abs(cs) ** ex
    y = rows[1][i] * np.sign(sn) * np.abs(sn) ** ex + rows[2][i]
    vs += [(float(x[j]), float(y[j]), float(z)) for j in range(N)]
fs = [(i * N + j, i * N + (j + 1) % N, (i + 1) * N + (j + 1) % N, (i + 1) * N + j) for i in range(len(zz) - 1) for j in range(N)]
fs += [tuple(range(N))[::-1], tuple(range((len(zz) - 1) * N, len(zz) * N))]
me = bpy.data.meshes.new("bust")
me.from_pydata(vs, [], fs)
for f in me.polygons:
    f.use_smooth = True
me.validate()
me.update()
m = link(bpy.data.objects.new("bust", me))
m.location.x = -0.04
m.data.materials.append(pbr("clay", (0.34, 0.34, 0.34), rough=0.6))
wall = pbr("wall", lin("A8A49C"), rough=0.8)
box("wall", (-6, 1.6, -1), (6, 1.7, 5), wall)
box("door", (0.62, 1.55, 0), (1.25, 1.6, 2.6), pbr("door", lin("6E6A62"), rough=0.6))
box("shelf", (-1.25, 1.2, 1.02), (-0.5, 1.6, 1.06), pbr("shelf", lin("4A4640"), rough=0.5))
for i, (x, h) in enumerate([(-1.18, 0.24), (-1.09, 0.28), (-1.0, 0.21), (-0.92, 0.26), (-0.80, 0.23)]):
    box(f"b{i}", (x, 1.3, 1.06), (x + 0.075, 1.5, 1.06 + h), pbr(f"b{i}", lin(["5A5650", "33302C", "77736A", "45413B", "65615A"][i]), rough=0.6))
box("floor", (-6, -4, -0.02), (6, 3, 0), pbr("floor", lin("6A6660"), rough=0.6))
area("win", (-2.2, -1.1, 2.0), (0, 0, 1.5), 1.6, 2.2, (1, 0.97, 0.92), 360)
area("room", (2.0, -1.8, 2.6), (0, 0.6, 1.2), 3, 3, (1, 0.93, 0.84), 30)
camera((0.10, -1.72, 1.46), (0.0, 0, 1.35), lens=50, fstop=2.8, focus=1.64)
dr.render(sc, "person")
