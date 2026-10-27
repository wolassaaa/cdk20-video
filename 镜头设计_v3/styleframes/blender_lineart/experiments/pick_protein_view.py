import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bl_protein_ink as B
from ink_common import *
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
mode = sys.argv[sys.argv.index("--") + 2]
if mode == "score":
    res = []
    for yaw in range(-150, 180, 30):
        for pitch in (-25, 5, 35):
            B.YAW, B.PITCH = yaw, pitch
            S = B.build(preview=True)
            cam = S["cam"]
            bm = bmesh.new()
            for o in S["elems"]:
                b2 = bm_world(o); me = bpy.data.meshes.new("t"); b2.to_mesh(me); b2.free(); bm.from_mesh(me)
            bvh = BVHTree.FromBMesh(bm)
            pts = [o.location for o in S["lig"][:29] if o.name.startswith("Sphere")]
            vis = 0
            for p in pts:
                d = p - cam.location; L = d.length
                h = bvh.ray_cast(cam.location, d / L, L)
                vis += h[0] is None or h[3] > L - 0.02
            pp = [world_to_pix(cam, p) for p in pts]
            area = (max(x for x, _ in pp) - min(x for x, _ in pp)) * (max(y for _, y in pp) - min(y for _, y in pp))
            tail = [world_to_pix(cam, S["P"](S["ca"][r]["xyz"])) for r in range(303, 347)]
            tin = sum(0 < x < 960 * 0.7 and 0 < y < 540 for x, y in tail) / len(tail)
            res.append((vis / len(pts), area, tin, yaw, pitch))
            print("SCORE", yaw, pitch, round(vis / len(pts), 2), int(area), round(tin, 2), flush=True)
else:
    V = [tuple(map(float, v.split(","))) for v in mode.split(";")]
    for i, (yaw, pitch) in enumerate(V):
        B.YAW, B.PITCH = yaw, pitch
        S = B.build(preview=True)
        p = B.render_passes(S, os.path.join(OUT, "_pv"), f"v{i}")
        B.composite(p, os.path.join(OUT, f"pv_{i}.png"))
