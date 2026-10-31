"""HKBU SCIE1007 coursework science video, dawn art direction. T4: the real CDK20 surface as a two-lobed massif at the blue hour, with the pocket as the canyon between the lobes.
blender -b -t 4 -P bl_t4.py -- <outdir> [--test] [--tilt 50 --yaw 20 --flip 1 --sunaz 70 --sunel 5]
--test renders a sheet of framings at a third size. Otherwise one 1080p set of layers: sun, sky, data.
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
ap.add_argument("--tilt", type=float, default=35)
ap.add_argument("--yaw", type=float, default=-30)
ap.add_argument("--flip", type=float, default=-1)
ap.add_argument("--sunaz", type=float, default=70)
ap.add_argument("--sunel", type=float, default=6)
ap.add_argument("--dist", type=float, default=12.2)
ap.add_argument("--camz", type=float, default=.3)
ap.add_argument("--focal", type=float, default=38)
ap.add_argument("--samples", type=int, default=160)
A = ap.parse_args(argv)

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "_work")
ROOT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus"
D = np.load(WORK + "/rock_full.npz")
V, Q, C = D["verts"] * 0.1, D["quads"], D["conf"]
res = json.load(open(ROOT + "/code/cdk20_backbone_view.json"))["res"]
ca = {r["i"]: np.array(r["ca"]) * 0.1 for r in res}
cen = np.mean([ca[i] for i in range(1, 303)], 0)
pocket = (ca[33] + ca[84]) / 2
nl, cl = np.mean([ca[i] for i in range(5, 85)], 0), np.mean([ca[i] for i in range(100, 290)], 0)
op = pocket - cen; op /= np.linalg.norm(op)
lobe = nl - cl; lobe -= op * np.dot(lobe, op); lobe /= np.linalg.norm(lobe)
side = np.cross(op, lobe)


def frame(tilt, yaw, flip):
    """Protein -> world. tilt turns the pocket from facing the lens toward facing the sky. Lobes lie left and right of it."""
    x, up = lobe * flip, side * flip
    t = math.radians(tilt)
    z = op * math.sin(t) + up * math.cos(t)
    y = np.cross(z, x)
    R = np.stack([x, y, z], 0)
    a = math.radians(yaw)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return Rz @ R


def place(R, camz):
    p = (V - cen) @ R.T
    lo, hi = p[:, 2].min(), p[:, 2].max()
    p[:, 2] -= lo + (hi - lo) * camz
    return p


sc = B.setup(samples=A.samples, pct=50 if A.test else 100)
rock = B.diffuse("rock", (0.8, 0.8, 0.8))
nt = rock.node_tree
tc, mp, nz, bp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping"), nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeBump")
mp.inputs["Scale"].default_value = (1, 1, .6)      # stretched up the slope, so low light finds gullies
nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value, nz.inputs["Roughness"].default_value = 26, 9, .62
bp.inputs["Strength"].default_value, bp.inputs["Distance"].default_value = .45, .03
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], nz.inputs["Vector"])
nt.links.new(nz.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], nt.nodes["Principled BSDF"].inputs["Normal"])
sun = B.sun("sun", A.sunaz, A.sunel, angle=1.0)
cam = B.camera((0, -A.dist, 0), A.focal, shift_x=-.065)
ob = None
if A.test:
    sc.cycles.samples = 48
    var = [(75, -30, -1, 62), (55, -30, -1, 62), (75, 25, -1, 62), (55, 25, 1, 62), (75, -30, 1, 62), (35, -30, -1, 62), (75, -30, -1, -62), (55, 25, -1, 62)]
    for k, (tilt, yaw, flip, saz) in enumerate(var):
        R = frame(tilt, yaw, flip)
        bpy.data.objects.remove(sun)
        sun = B.sun("sun", saz, A.sunel, angle=1.0)
        if ob: bpy.data.objects.remove(ob)
        ob = B.mesh("cdk", place(R, A.camz), Q, rock, attrs={"conf": C})
        B.layers(A.out, f"t{k:02d}", {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [sun], data_scale=20)
        print("VAR", k, tilt, yaw, flip, saz, flush=True)
else:
    R = frame(A.tilt, A.yaw, A.flip)
    p = place(R, A.camz)
    ob = B.mesh("cdk", p, Q, rock, attrs={"conf": C})
    B.layers(A.out, "T4", {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [sun], data_scale=20)
    zshift = (((V - cen) @ R.T)[:, 2] - p[:, 2]).mean()
    pw = (pocket - cen) @ R.T - np.array([0, 0, zshift])
    f = A.focal / 36 * 1920
    d = pw - np.array([0, -A.dist, 0])
    print("POCKET_PX", 960 + f * d[0] / d[1], 720 - f * d[2] / d[1], flush=True)
    json.dump({"R": R.tolist(), "zshift": float(zshift), "pocket_px": [960 + f * d[0] / d[1], 720 - f * d[2] / d[1]]}, open(os.path.join(A.out, "T4_frame.json"), "w"))
