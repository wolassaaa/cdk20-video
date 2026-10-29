import bpy, bmesh, sys, os
import numpy as np
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "anatomy", "bp3d_v4_groups_stl")
D = os.path.normpath(D)
print("VER", bpy.app.version_string)
for n in ["portal_vein_hepatic", "portal_tributaries_splenic_SMV"]:
    bpy.ops.wm.stl_import(filepath=os.path.join(D, n + ".stl"))
    o = bpy.context.selected_objects[0]
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.verts.ensure_lookup_table()
    # islands
    seen = set(); isl = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); c = []
        while st:
            x = st.pop(); c.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        isl.append(c)
    co = np.array([v.co[:] for v in bm.verts])
    print(n, "verts", len(bm.verts), "islands", len(isl))
    for c in sorted(isl, key=len, reverse=True)[:25]:
        p = co[c]
        print("  isl", len(c), "zmin %.0f zmax %.0f" % (p[:,2].min(), p[:,2].max()), "ctr", np.round(p.mean(0)))
    lo = co[co[:,2].argmin()]; print("  lowest", lo)
