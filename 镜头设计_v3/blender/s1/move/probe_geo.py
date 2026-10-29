import bpy, bmesh, sys, os, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo
D = os.path.normpath(os.path.join(HERE, "..", "..", "..", "assets", "anatomy", "bp3d_v4_groups_stl"))
objs = []
for n in ["portal_tributaries_splenic_SMV", "portal_vein_hepatic"]:
    bpy.ops.wm.stl_import(filepath=os.path.join(D, n + ".stl"))
    objs.append(bpy.context.selected_objects[0])
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
o = bpy.context.active_object
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.verts.ensure_lookup_table()
co = np.array([v.co[:] for v in bm.verts])
edges = [(e.verts[0].index, e.verts[1].index) for e in bm.edges]
lab = geo.islands(len(co), edges)
t = time.time()
extra = geo.bridge_edges(co, lab)
seed = int(co[:, 2].argmin())
dist, pred = geo.geodesic(co, edges, extra, seed)
print("geo time", time.time() - t, "max d", dist.max(), "inf", np.isinf(dist).sum())

def path(t):
    p = []
    while t != -1: p.append(t); t = pred[t]
    return p[::-1]
# intrahepatic tips: right-most, left-most (exclude splenic: x>57 in tributaries, z<1095)
m = co[:, 2] > 1095
iR = np.where(m)[0][co[m, 0].argmin()]; iL = np.where(m)[0][co[m, 0].argmax()]
pR, pL = path(iR), path(iL)
print("dR", dist[iR], "dL", dist[iL])
for s in range(0, int(min(dist[iR], dist[iL])), 10):
    a = pR[np.searchsorted(dist[pR], s)]; b = pL[np.searchsorted(dist[pL], s)]
    print("s", s, "R", np.round(co[a]), "L", np.round(co[b]), "sep %.1f" % np.linalg.norm(co[a] - co[b]))
np.savez(os.path.join(HERE, "cache_probe.npz"), co=co, dist=dist)
