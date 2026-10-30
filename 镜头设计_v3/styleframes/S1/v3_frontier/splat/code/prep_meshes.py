"""Load the BodyParts3D liver set, make one clean closed parenchyma skin, export triangle soups as npz.
blender -b --factory-startup -t 3 -P prep_meshes.py -- OUT.npz
Units: 1 = 100 mm, body axes (anterior -y, patient right -x, up +z), centred on the skin bbox centre.
"""
import bpy, bmesh, sys
import numpy as np

out = sys.argv[sys.argv.index("--") + 1]
V4 = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
S = 0.01
bpy.ops.wm.read_factory_settings(use_empty=True)


def load(name, keep=None):
    bpy.ops.wm.stl_import(filepath=V4 + name + ".stl")
    o = bpy.context.selected_objects[0]
    me = o.data
    for v in me.vertices: v.co = v.co * S
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    if keep:
        bad = [v for v in bm.verts if not keep(v.co / S)]
        bmesh.ops.delete(bm, geom=bad, context="VERTS")
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    o.name = name
    return o


def apply_all(o):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)


def arrays(o):
    me = o.data
    me.calc_loop_triangles()
    v = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
    t = np.zeros(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t); t = t.reshape(-1, 3)
    # smooth vertex normals (area weighted)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    fn = np.cross(b - a, c - a)
    vn = np.zeros_like(v)
    for k in range(3): np.add.at(vn, t[:, k], fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    return v, t, vn


lp = load("liver_parenchyma_segments"); gb = load("gallbladder")
bpy.ops.object.select_all(action="DESELECT"); lp.select_set(True); gb.select_set(True)
bpy.context.view_layer.objects.active = lp; bpy.ops.object.join()
skin = lp
skin.data.remesh_voxel_size = 0.016
bpy.ops.object.voxel_remesh()
lap = skin.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = 8; lap.lambda_factor = 0.8
apply_all(skin)

parts = {"skin": skin}
parts["portal"] = load("portal_vein_hepatic")
parts["portal_x"] = load("portal_tributaries_splenic_SMV", keep=lambda c: c.z > 1030 and c.x < 25)
parts["artery"] = load("hepatic_artery")
parts["hveins"] = load("hepatic_veins")
parts["ivc"] = load("inferior_vena_cava")
parts["bile"] = load("intrahepatic_bile_ducts")

data = {k: arrays(o) for k, o in parts.items()}

# interior points of the skin (for the milky volume splats): BVH nearest-point + normal sign test
from mathutils.bvhtree import BVHTree
from mathutils import Vector
sv_, st_, _ = data["skin"]
bvh = BVHTree.FromPolygons([tuple(map(float, x)) for x in sv_], [tuple(map(int, x)) for x in st_])
rng = np.random.default_rng(3)
lo, hi = sv_.min(0), sv_.max(0)
cand = lo + rng.random((260000, 3)) * (hi - lo)
inside, depth = [], []
for p in cand:
    co, n, i, d = bvh.find_nearest(Vector(p))
    if co is None: continue
    if (Vector(p) - co).dot(n) < 0:
        inside.append(p); depth.append(d)
vol = np.array(inside, np.float32); vdep = np.array(depth, np.float32)
print("volume points", len(vol))
sv = data["skin"][0]
centre = (sv.min(0) + sv.max(0)) / 2
res = {"centre": centre, "vol_p": vol - centre, "vol_d": vdep}
for k, (v, t, vn) in data.items():
    res[k + "_v"] = v - centre; res[k + "_t"] = t; res[k + "_n"] = vn
    print("%-8s verts %7d tris %7d  bbox %s" % (k, len(v), len(t), np.round(v.max(0) - v.min(0), 3)))
np.savez_compressed(out, **res)
print("saved", out, "centre", centre)
