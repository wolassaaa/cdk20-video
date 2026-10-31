"""HKBU SCIE1007 coursework science video. Renders the BodyParts3D liver as a single silver image: one raking lamp on black. The result is the picture printed on the T1 paper."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *
import bmesh

A = dr.args()
sc = dr.setup(A.samples, A.pct, bounces=4)
sc.render.resolution_x, sc.render.resolution_y = 2400, 1600
STL = os.path.join(V3, "assets", "anatomy", "bp3d_v4_groups_stl", "liver_parenchyma_segments.stl").replace("\\", "/")
C = Vector((-10.35, -122.87, 1105.54))
bpy.ops.wm.stl_import(filepath=STL)
o = bpy.context.selected_objects[0]
me = o.data
for v in me.vertices:
    v.co = (v.co - C) * 0.01
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0015)
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
r = o.modifiers.new("fuse", "REMESH")     # the source is cut into Couinaud segments; fuse them so the seams do not read as stitching
r.mode, r.voxel_size, r.use_smooth_shade = "VOXEL", 0.016, True
s = o.modifiers.new("sm", "SMOOTH")
s.iterations, s.factor = 24, 0.7
me.materials.append(pbr("clay", (0.62, 0.62, 0.62), rough=0.34, spec=0.55))
cam_d = 6.4
az, el = math.radians(-14), math.radians(6)
tgt = Vector((0.0, 0.0, -0.05))
pos = tgt + cam_d * Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
camera(tuple(pos), tuple(tgt), lens=62)
area("key", (-5.2, -2.6, 3.8), (0, 0, 0), 2.4, 2.4, (1, 1, 1), 420)
area("low", (3.8, -4.0, -2.0), (0, 0, 0), 3, 3, (1, 1, 1), 26)
dr.render(sc, "liver_img")
