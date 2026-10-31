"""HKBU SCIE1007 coursework science video, dawn art direction. T4: stand on the real CDK20 surface, near the pocket, and look across it. No height field, no talus: the true mesh, 1.2 million vertices, every crest an atom's relief.
blender -b -t 4 -P bl_t4c.py -- <outdir> [--test] [--theta 45 --rad 26 --h 2 --focal 24 --sunaz 35 --sunel 3.5]
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
ap.add_argument("--theta", type=float, default=45)
ap.add_argument("--rad", type=float, default=26)
ap.add_argument("--h", type=float, default=2)
ap.add_argument("--focal", type=float, default=24)
ap.add_argument("--sunaz", type=float, default=35)
ap.add_argument("--sunel", type=float, default=3.5)
ap.add_argument("--look", type=float, default=0)
ap.add_argument("--samples", type=int, default=160)
ap.add_argument("--name", default="T4")
A = ap.parse_args(argv)

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work")
ROOT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus"
D = np.load(WORK + "/rock_full.npz")
V, Q, C = D["verts"].astype(np.float64), D["quads"], D["conf"]
res = json.load(open(ROOT + "/code/cdk20_backbone_view.json"))["res"]
ca = {r["i"]: np.array(r["ca"]) for r in res}
cen = np.mean([ca[i] for i in range(1, 303)], 0)
pocket = (ca[33] + ca[84]) / 2
nl, cl = np.mean([ca[i] for i in range(5, 85)], 0), np.mean([ca[i] for i in range(100, 290)], 0)
op = pocket - cen; op /= np.linalg.norm(op)
lobe = nl - cl; lobe -= op * np.dot(lobe, op); lobe /= np.linalg.norm(lobe)
side = np.cross(op, lobe)
R = np.stack([lobe, np.cross(op, lobe), op], 0)
P = (V - pocket) @ R.T * .1

sc = B.setup(samples=A.samples, pct=33 if A.test else 100)
rock = B.diffuse("rock", (0.8, 0.8, 0.8))
ob = B.mesh("cdk", P, Q, rock, attrs={"conf": C})


def shot(name, theta, rad, h, look):
    t = math.radians(theta)
    pos = np.array([math.cos(t), math.sin(t), 0]) * rad * .1
    pos[2] = h * .1
    fwd = -pos[:2] / np.linalg.norm(pos[:2])
    yaw = math.degrees(math.atan2(fwd[0], fwd[1])) + look
    for o in list(bpy.data.objects):
        if o.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(o)
    B.camera(tuple(pos), A.focal, yaw_deg=yaw)
    s = B.sun("sun", yaw + A.sunaz, A.sunel, angle=.8)
    B.layers(A.out, name, {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [s], data_scale=20)
    return yaw


if A.test:
    sc.cycles.samples = 48
    var = [(th, rad, h) for th in range(0, 360, 45) for rad, h in ((24, 3), (34, 6))]
    for k, (th, rad, h) in enumerate(var):
        shot(f"t{k:02d}", th, rad, h, 0)
        print("VAR", k, th, rad, h, flush=True)
else:
    shot(A.name, A.theta, A.rad, A.h, A.look)
