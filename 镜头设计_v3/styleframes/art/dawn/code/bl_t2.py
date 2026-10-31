"""HKBU SCIE1007 coursework science video, dawn art direction. T2: a person is a lit window at dusk. A plain low building on the fixed horizon, one large window, phone footage goes behind the glass.
Layers: sky (dusk fill on the wall), spill (warm light from the room, on the wall, sill and ground), mask (white where the footage shows). Corner positions go to T2_px.json for the corner pin.
blender -b -t 4 -P bl_t2.py -- <outdir>
"""
import argparse, json, math, os, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_core as B
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=220)
A = ap.parse_args(argv)

sc = B.setup(samples=A.samples, pct=A.pct)
CAMH = 1.3
YAW = 9.0
FOC = 33
cam = B.camera((0, -9.2, CAMH), FOC, yaw_deg=YAW, shift_x=-.145, clip=(.1, 3000))

wall_m = B.diffuse("wall", (.34, .32, .33))
frame_m = B.diffuse("frame", (.05, .045, .045))
ground_m = B.diffuse("ground", (.16, .15, .16))
sill_m = B.diffuse("sill", (.42, .4, .4))
glassback = B.emission("back", (1, 1, 1), 1.0)


def box(name, lo, hi, mat):
    lo, hi = np.array(lo, float), np.array(hi, float)
    c = (lo + hi) / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(c))
    o = bpy.context.object
    o.scale = tuple(hi - lo)
    o.name = name
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# window, 16:9, wide enough to hold a seated person at half frame. Metres; x right, y into the wall, z up
WX0, WX1, WZ0, WZ1 = -4.05, 0.05, 1.65, 3.95
DEP = .32
WALL_X = (-9, 1.36)
ROOF = 6.4
box("w_left", (WALL_X[0], 0, 0), (WX0, DEP, ROOF), wall_m)
box("w_right", (WX1, 0, 0), (WALL_X[1], DEP, ROOF), wall_m)
box("w_low", (WX0, 0, 0), (WX1, DEP, WZ0), wall_m)
box("w_high", (WX0, 0, WZ1), (WX1, DEP, ROOF), wall_m)
box("sill", (WX0 - .14, -.14, WZ0 - .08), (WX1 + .14, DEP, WZ0), sill_m)
box("lintel", (WX0 - .06, -.02, WZ1), (WX1 + .06, .08, WZ1 + .16), frame_m)
F = .06
fr = [box("f_l", (WX0, .16, WZ0), (WX0 + F, .22, WZ1), frame_m), box("f_r", (WX1 - F, .16, WZ0), (WX1, .22, WZ1), frame_m),
      box("f_t", (WX0, .16, WZ1 - F), (WX1, .22, WZ1), frame_m), box("f_b", (WX0, .16, WZ0), (WX1, .22, WZ0 + F), frame_m)]
mx = WX0 + (WX1 - WX0) * .77
fr.append(box("f_m", (mx - .025, .16, WZ0), (mx + .025, .22, WZ1), frame_m))        # one mullion, well off the speaker's face
# a second window on the same wall, dark, holding a little of the sky: this is one building, and 8-07 uses four of its windows
dark = B.diffuse("darkglass", (.02, .02, .03), rough=.12)
box("dark", (.5, -.03, 2.0), (1.12, .0, 3.95), dark)
box("dark_s", (.44, -.1, 1.93), (1.18, .0, 2.0), sill_m)
# a roof edge and the ground
box("roof", (WALL_X[0] - .2, -.25, ROOF), (WALL_X[1] + .25, DEP + .3, ROOF + .14), frame_m)
gv = [(-400, -40, 0), (400, -40, 0), (400, 3000, 0), (-400, 3000, 0)]
B.mesh("ground", gv, [[0, 1, 2, 3]], ground_m, smooth=False)

# the room: an emitter plane behind the glass. Bright in the spill layer, white in the mask layer
room = B.mesh("room", [(WX0, DEP + .05, WZ0), (WX1, DEP + .05, WZ0), (WX1, DEP + .05, WZ1), (WX0, DEP + .05, WZ1)], [[0, 1, 2, 3]], glassback, smooth=False)
# area light just inside, throwing the room's light out of the window onto the sill and the ground
ld = bpy.data.lights.new("spill", "AREA")
ld.shape, ld.size, ld.size_y, ld.energy = "RECTANGLE", WX1 - WX0, WZ1 - WZ0, 320
sp = bpy.data.objects.new("spill", ld)
sp.location = ((WX0 + WX1) / 2, DEP + .02, (WZ0 + WZ1) / 2 + .1)
sp.rotation_euler = (math.radians(-100), 0, 0)
sc.collection.objects.link(sp)

plan = {"sky": (1.0, []), "spill": (0.0, ["spill"]), "mask": (0.0, ["room"])}
B.layers(A.out, "T2", plan, [sp, room], data_scale=500)

# corners of the window opening on screen, inside the frame, for the corner pin. Computed by Blender's own camera so the shift and yaw are right
from bpy_extras.object_utils import world_to_camera_view
pts = {}
for k, q in dict(bl=(WX0, DEP, WZ0), br=(WX1, DEP, WZ0), tr=(WX1, DEP, WZ1), tl=(WX0, DEP, WZ1)).items():
    v = world_to_camera_view(sc, sc.camera, Vector(q))
    pts[k] = [v.x * 1920, (1 - v.y) * 1080]
json.dump(pts, open(os.path.join(A.out, "T2_px.json"), "w"), indent=1)
print("CORNERS", pts, flush=True)
