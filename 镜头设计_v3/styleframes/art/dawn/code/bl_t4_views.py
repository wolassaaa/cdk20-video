"""HKBU SCIE1007 coursework science video, dawn art direction. Framing test: low white-light views of the real CDK20 surface as a mountain range, to pick the T4 camera.
blender -b -t 4 -P bl_t4_views.py -- <outdir>
"""
import json, math, os, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_core as B
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
ROOT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus"
D = np.load(ROOT + "/_work/cdk20_surface.npz")
V, Q, C = D["verts"] * 0.1, D["quads"], D["conf"]
res = json.load(open(ROOT + "/code/cdk20_backbone_view.json"))["res"]
ca = {r["i"]: np.array(r["ca"]) * 0.1 for r in res}
cen = np.mean([ca[i] for i in range(1, 303)], 0)
pocket = (ca[33] + ca[84]) / 2
nl = np.mean([ca[i] for i in range(5, 85)], 0)
cl = np.mean([ca[i] for i in range(100, 290)], 0)
print("pocket", pocket, "cen", cen)
op = pocket - cen; op /= np.linalg.norm(op)
lobe = nl - cl; lobe /= np.linalg.norm(lobe)
side = np.cross(op, lobe); side /= np.linalg.norm(side)


def rot(vec, axis, deg):
    a = math.radians(deg); axis = axis / np.linalg.norm(axis)
    return vec * math.cos(a) + np.cross(axis, vec) * math.sin(a) + axis * np.dot(axis, vec) * (1 - math.cos(a))


views = []
for up_name, up0 in (("Nup", lobe), ("Cup", -lobe), ("Sideup", side), ("-Sideup", -side)):
    for az in (-50, 0, 50):
        views.append((up_name, az, up0))

sc = B.setup(samples=48, pct=25)
sc.cycles.use_denoising = True
m = B.diffuse("rock", (0.8, 0.8, 0.8))
sun = B.sun("sun", 75, 7)
cam = B.camera((0, -13, 0), 50)
ob = None
for k, (name, az, up0) in enumerate(views):
    view = rot(-op, up0, az)        # the way the camera looks, in protein frame
    fwd = view / np.linalg.norm(view)
    up = up0 - fwd * np.dot(up0, fwd); up /= np.linalg.norm(up)
    right = np.cross(fwd, up)
    R = np.stack([right, fwd, up], 0)       # protein -> world (x right, y into scene, z up)
    p = (V - cen) @ R.T
    zmin, zmax = p[:, 2].min(), p[:, 2].max()
    p[:, 2] -= zmin + (zmax - zmin) * 0.35     # camera height sits 35 % up the model
    if ob:
        bpy.data.objects.remove(ob)
    ob = B.mesh("cdk", p, Q, m)
    B.layers(out, f"view{k:02d}", {"lit": (0.06, ["sun"])}, [sun])
    print("VIEW", k, name, az, flush=True)
    np.save(os.path.join(out, f"view{k:02d}_R.npy"), R)
