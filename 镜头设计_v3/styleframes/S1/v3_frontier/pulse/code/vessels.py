"""PULSE: thin red threads along the liver's own vessels (BodyParts3D portal + hepatic veins).

Centreline extraction with no extra tools: from every vertex cast a ray inward across the vessel; the midpoint of
that chord lies near the centreline. Grid-average those midpoints, join them with a minimum spanning tree, prune
twigs, smooth each branch.

blender -b --factory-startup -t 3 -P vessels.py -- --pts ../data/points.npz --out ../data/threads.npz
Writes: pts (M,3) metres, par (M,) parent index or -1, rad (M,) local vessel radius in metres at installation scale.
"""
import bpy, bmesh, sys, argparse, time
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--pts", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--grid", type=float, default=0.07)       # metres at installation scale (2.3 mm real)
ap.add_argument("--link", type=float, default=0.30)
ap.add_argument("--twig", type=float, default=0.55)       # prune side branches shorter than this
A = ap.parse_args(argv)

ANAT = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
d = np.load(A.pts); K = float(d["K"]); SHIFT = d["shift"]
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)


def medial(name):
    bpy.ops.wm.stl_import(filepath=ANAT + name + ".stl")
    o = bpy.context.selected_objects[0]; me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co = Vector(np.array(v.co[:]) * 0.001 * K + SHIFT)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.006)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    out = []
    for v in bm.verts:
        n = v.normal
        if n.length < 0.5: continue
        o_ = v.co - n * 0.004
        hit = tree.ray_cast(o_, -n, 1.2)
        if hit[0] is None: continue
        # the far wall must face us (a real chord across the lumen, not a graze)
        if hit[1].dot(n) > -0.2: continue
        c = (v.co + hit[0]) / 2
        out.append((*c, (hit[0] - v.co).length / 2))
    bm.free()
    print(name, "medial pts", len(out), "(%.1fs)" % (time.time() - t0))
    return np.array(out)


def tree(M, g, link, twig):
    # grid average
    key = np.floor(M[:, :3] / g).astype(np.int64)
    uk, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    Q = np.stack([np.bincount(inv, M[:, c]) / np.bincount(inv) for c in range(4)], 1)
    P_, R_ = Q[:, :3], Q[:, 3]
    n = len(P_)
    # Prim MST, O(n^2); edges longer than `link` simply leave the piece as its own tree
    intree = np.zeros(n, bool); best = np.full(n, np.inf); par = np.full(n, -1)
    start = int(np.argmax(R_)); intree[start] = True
    best = np.linalg.norm(P_ - P_[start], axis=1); par[:] = start; par[start] = -1
    for _ in range(n - 1):
        cand = np.where(~intree)[0]
        j = cand[np.argmin(best[cand])]
        if best[j] > link: par[j] = -1             # a new root
        intree[j] = True
        dj = np.linalg.norm(P_ - P_[j], axis=1)
        upd = (~intree) & (dj < best)
        best[upd] = dj[upd]; par[upd] = j
    # prune twigs: repeatedly drop leaf chains shorter than `twig`
    alive = np.ones(n, bool)
    for _ in range(6):
        kids = np.bincount(par[(par >= 0) & alive], minlength=n)
        leaves = np.where(alive & (kids == 0))[0]
        for lf in leaves:
            chain = [lf]; L = 0.0; c = lf
            while par[c] >= 0 and kids[par[c]] == 1 and alive[par[c]]:
                L += np.linalg.norm(P_[c] - P_[par[c]]); c = par[c]; chain.append(c)
            if par[c] >= 0:
                L += np.linalg.norm(P_[c] - P_[par[c]])
            if L < twig: alive[chain] = False
    idx = np.where(alive)[0]; remap = -np.ones(n, int); remap[idx] = np.arange(len(idx))
    P2, R2 = P_[idx], R_[idx]
    par2 = np.array([remap[par[i]] if par[i] >= 0 and alive[par[i]] else -1 for i in idx])
    # smooth along the tree, keep junctions and tips loosely pinned
    for _ in range(14):
        acc = P2.copy(); cnt = np.ones(len(P2))
        ch = par2 >= 0
        np.add.at(acc, np.where(ch)[0], P2[par2[ch]]); np.add.at(cnt, np.where(ch)[0], 1)
        np.add.at(acc, par2[ch], P2[np.where(ch)[0]]); np.add.at(cnt, par2[ch], 1)
        P2 = 0.5 * P2 + 0.5 * acc / cnt[:, None]
    print("tree: %d -> %d nodes, %d roots (%.1fs)" % (n, len(P2), (par2 < 0).sum(), time.time() - t0))
    return P2, par2, R2


Ps, pars, rads = [], [], []
off = 0
for nm in ("portal_vein_hepatic", "hepatic_veins"):
    M = medial(nm)
    p_, q_, r_ = tree(M, A.grid, A.link, A.twig)
    Ps.append(p_); pars.append(np.where(q_ >= 0, q_ + off, -1)); rads.append(r_); off += len(p_)
pts = np.concatenate(Ps); par = np.concatenate(pars); rad = np.concatenate(rads)
seg = np.linalg.norm(pts[par >= 0] - pts[par[par >= 0]], axis=1)
print("threads: %d nodes, total length %.1f m, longest link %.2f m, radius %.3f-%.3f" % (len(pts), seg.sum(), seg.max(), rad.min(), rad.max()))
np.savez(A.out, pts=pts, par=par, rad=rad, split=np.array([len(Ps[0])]))
