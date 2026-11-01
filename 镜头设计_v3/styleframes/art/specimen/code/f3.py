"""HKBU SCIE1007 coursework science video. F3 plate: schematic only. Two padlocks in glass with a blue plate inside each, one red key. The left plate has the key's own shape cut out, the right plate has a different one. Nothing here is a real structure."""
import json
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/specimen/code")
import sp
from sp import gk

A = sp.args()
sc = sp.scene(A["samples"], A["pct"])
PX = 170
WIDTH = 1920 / PX
TEETH_A, TEETH_B = [0.24, 0.10, 0.26, 0.12], [0.09, 0.27, 0.08, 0.25]
TIP = 0.55                              # key tip height in the lock when seated


def rrect(w, h, r, cz=0.0, n=8):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a) + cz))
    return pts


def blade(teeth, tip=0.0, length=1.35, pad=0.0):
    """Key profile, tip up, teeth on the right. pad widens it, for the hole in the plate."""
    L, S = -0.16 - pad, 0.04 + pad
    pts = [(L, tip - length), (L, tip - 0.05), (L + 0.06, tip + pad), (S + 0.02, tip + pad)]
    for i, d in enumerate(teeth):
        z = tip - 0.05 - i * 0.26
        pts += [(S, z), (S + d, z - 0.03), (S + d, z - 0.15), (S, z - 0.20)]
    pts.append((S, tip - length))
    return pts


def extrude(name, poly, y0, y1, loc, mat=None):
    n = len(poly)
    verts = [(x, y0, z) for x, z in poly] + [(x, y1, z) for x, z in poly]
    faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.validate()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if mat:
        me.materials.append(mat)
    return o


def key(x, z, mat):
    b = extrude("blade", blade(TEETH_A, length=1.3), -0.06, 0.06, (x, 0, z), mat)
    bv = b.modifiers.new("b", "BEVEL")
    bv.width, bv.segments = 0.012, 2
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.095, major_segments=96, minor_segments=24, location=(x - 0.06, 0, z - 1.3 - 0.36), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.object
    t.data.materials.append(mat)
    for p in t.data.polygons:
        p.use_smooth = True


def lock(x, teeth, zc, glass, plate_mat):
    body = extrude("body", rrect(2.0, 1.75, 0.22), -0.26, 0.26, (x, 0, zc), glass)
    b = body.modifiers.new("b", "BEVEL")
    b.width, b.segments, b.limit_method, b.angle_limit = 0.05, 6, "ANGLE", math.radians(35)
    for p in body.data.polygons:
        p.use_smooth = True
    pl = extrude("plate", rrect(1.62, 1.4, 0.12, cz=0.0), -0.03, 0.03, (x, 0, zc), plate_mat)
    hole = extrude("hole", blade(teeth, tip=TIP - zc + 0.0 + (zc - 0.0) * 0 + 0.0, length=2.6, pad=0.022), -0.3, 0.3, (x, 0, zc))
    hole.hide_render = True
    m = pl.modifiers.new("cut", "BOOLEAN")
    m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", hole
    # shackle
    c = bpy.data.curves.new("sh", "CURVE")
    c.dimensions, c.bevel_depth, c.bevel_resolution, c.resolution_u = "3D", 0.115, 8, 12
    s = c.splines.new("POLY")
    pts = [(-0.62, 0.8), (-0.62, 1.2)] + [(-0.62 * math.cos(a), 1.2 + 0.62 * math.sin(a)) for a in [math.pi * i / 48 for i in range(1, 48)]] + [(0.62, 1.2), (0.62, 0.8)]
    s.points.add(len(pts) - 1)
    for p, (px, pz) in zip(s.points, pts):
        p.co = (px, 0, pz, 1)
    so = bpy.data.objects.new("sh", c)
    bpy.context.scene.collection.objects.link(so)
    so.location = (x, 0, zc)
    c.materials.append(glass)


G = gk.glass(tint=(0.93, 0.95, 1.0), rough=0.03)
PLATE = sp.tissue(sp.BLUE, rough=0.3, coat=0.5, glow=0.3)
RED = sp.tissue(sp.RED, rough=0.2, coat=1.0, glow=0.82)
XL, XR, ZC = -1.75, 2.15, 0.0
lock(XL, TEETH_A, ZC, G, PLATE)
lock(XR, TEETH_B, ZC, G, PLATE)
key(XL, TIP, RED)
key(XR, -1.2, RED)                      # stopped under the right lock, gap wide enough for the stop mark

AZ, EL = math.radians(22), 0.0
T = Vector((0.2, 0, -0.74))
pos = T + 14 * Vector((-math.sin(AZ) * math.cos(EL), -math.cos(AZ) * math.cos(EL), math.sin(EL)))
cam = sp.ortho(pos, T, WIDTH)
sp.softbox("key", (-5, -7, 6), tuple(T), 5.0, 8, 6)
sp.softbox("rimL", (-6, 3, 1), tuple(T), 26, 0.5, 10, (0.8, 0.86, 1.0))
sp.softbox("rimR", (7, 3, 1), tuple(T), 18, 0.5, 10, (0.8, 0.86, 1.0))
sp.softbox("hl", (2, -6, 2), tuple(T), 2.5, 0.4, 8)
sp.softbox("front", (5, -7, -3), tuple(T), 0.5, 9, 5, (0.7, 0.78, 1.0))
gk.render(sp.PLATES + "f3.png")

from bpy_extras.object_utils import world_to_camera_view as w2c
P = {}
for k, v in dict(lockL=(XL, 0, 0.0), lockL_edge=(XL - 1.0, 0, 0.3), lockR=(XR, 0, 0.0), keyL=(XL - 0.06, 0, -1.1), keyR=(XR - 0.06, 0, -1.0), tipR=(XR, 0, -1.2), bowL=(XL - 0.06, 0, TIP - 1.66)).items():
    p = w2c(sc, cam, Vector(v))
    P[k] = (round(p.x * 1920), round((1 - p.y) * 1080))
json.dump(P, open(sp.PLATES + "f3.json", "w"))
print("POINTS", P)
