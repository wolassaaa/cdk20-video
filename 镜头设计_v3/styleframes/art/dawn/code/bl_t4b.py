"""HKBU SCIE1007 coursework science video, dawn art direction. T4: CDK20 relief (real surface read from above the pocket, see make_relief.py) as a massif at the blue hour.
blender -b -t 4 -P bl_t4b.py -- <outdir> [--test] [--azim 200 --dist 7 --camz .55 --focal 30 --sunaz 40 --sunel 3.5]
azim is where the camera stands around the massif, in degrees, 0 = looking along +Y of the relief.
"""
import argparse, json, math, os, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_core as B

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--test", action="store_true")
ap.add_argument("--azim", type=float, default=0)
ap.add_argument("--dist", type=float, default=8.0)
ap.add_argument("--camz", type=float, default=.7)
ap.add_argument("--focal", type=float, default=32)
ap.add_argument("--sunaz", type=float, default=38)
ap.add_argument("--sunel", type=float, default=3.5)
ap.add_argument("--samples", type=int, default=160)
ap.add_argument("--sx", type=float, default=0.0)
ap.add_argument("--name", default="T4")
A = ap.parse_args(argv)

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work")
R = np.load(WORK + "/relief.npz")
Z, K, lo, DX, base, pk = R["Z"], R["K"], R["lo"], float(R["DX"]), float(R["base"]), R["pocket"]
ny, nx = Z.shape
xs, ys = (lo[0] + DX * np.arange(nx)) * .1, (lo[1] + DX * np.arange(ny)) * .1
X, Y = np.meshgrid(xs, ys)


def build(azim, camz):
    a = math.radians(azim)
    c, s = math.cos(a), math.sin(a)
    x, y = X * c - Y * s, X * s + Y * c
    zr = (Z - base) * .1
    z0 = zr.max() * camz
    v = np.stack([x.ravel(), y.ravel(), (zr - z0).ravel()], 1)
    px = np.array([pk[0] * .1 * c - pk[1] * .1 * s, pk[0] * .1 * s + pk[1] * .1 * c, (pk[2] - base) * .1 - z0])
    return v, px


idx = np.arange(nx * ny).reshape(ny, nx)
quads = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
sc = B.setup(samples=A.samples, pct=33 if A.test else 100)
rock = B.diffuse("rock", (0.8, 0.8, 0.8))
sun = B.sun("sun", A.sunaz, A.sunel, angle=.8)
cam = B.camera((0, -A.dist, 0), A.focal, shift_x=A.sx)
ob = None
if A.test:
    sc.cycles.samples = 48
    var = [(az, sa) for az in range(0, 360, 30) for sa in (40,)] + [(az, -40) for az in (0, 90, 180, 270)]
    for k, (az, sa) in enumerate(var):
        v, _ = build(az, A.camz)
        if ob: bpy.data.objects.remove(ob)
        bpy.data.objects.remove(sun)
        sun = B.sun("sun", sa, A.sunel, angle=.8)
        ob = B.mesh("cdk", v, quads, rock, attrs={"conf": K.ravel()})
        B.layers(A.out, f"t{k:02d}", {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [sun], data_scale=20)
        print("VAR", k, az, sa, flush=True)
else:
    v, px = build(A.azim, A.camz)
    ob = B.mesh("cdk", v, quads, rock, attrs={"conf": K.ravel()})
    B.layers(A.out, A.name, {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [sun], data_scale=20)
    f = A.focal / 36 * 1920
    d = px - np.array([0, -A.dist, 0])
    pkpx = [float(960 + f * d[0] / d[1] - A.sx * 1920), float(720 - f * d[2] / d[1])]
    print("POCKET_PX", pkpx, flush=True)
    json.dump({"pocket_px": pkpx}, open(os.path.join(A.out, f"{A.name}_frame.json"), "w"))
