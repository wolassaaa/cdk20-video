"""HKBU SCIE1007 coursework science video, dawn art direction. T6: the road map as a real road at night. Six stations are six street lamps on a curve to the horizon.
Three are lit; the road beyond them has no light of its own, only a dashed line. One white-light layer per lamp, so lighting them one at a time in the film needs no further render.
blender -b -t 4 -P bl_t6.py -- <outdir>
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
ap.add_argument("--samples", type=int, default=200)
A = ap.parse_args(argv)

CAMH = 2.4
sc = B.setup(samples=A.samples, pct=A.pct)
cam = B.camera((0, 0, CAMH), 26, clip=(.1, 9000))


F_PX = 26 / 36 * 1920
POLE = 7.6
# stations are placed by where they should land on screen: x px and lamp height px, so six readable posts fit on one road
SX = [205, 690, 1010, 1240, 1420, 1560]
SH = [520, 300, 190, 125, 85, 60]
DEPTH = [F_PX * POLE / h for h in SH]
CTRL = [(-14.0, -6.0), (-11.5, 8.0)] + [((x - 960) * d / F_PX, d) for x, d in zip(SX, DEPTH)] + [((1700 - 960) * 420 / F_PX, 420.0), ((1800 - 960) * 2000 / F_PX, 2000.0), ((1800 - 960) * 2200 / F_PX, 2200.0)]
CTRL = np.array(CTRL) + np.array([4.4, 0])


def catmull(P, n=60):
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i:i + 4]
        d1, d2 = np.linalg.norm(p2 - p1), np.linalg.norm(p1 - p0) + 1e-6
        d3 = np.linalg.norm(p3 - p2) + 1e-6
        m1 = (p2 - p0) * d1 / (d1 + d2)
        m2 = (p3 - p1) * d1 / (d1 + d3)
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append((2 * t ** 3 - 3 * t ** 2 + 1) * p1 + (t ** 3 - 2 * t ** 2 + t) * m1 + (-2 * t ** 3 + 3 * t ** 2) * p2 + (t ** 3 - t ** 2) * m2)
    return np.array(out)


pts = catmull(CTRL)
ts = np.linspace(0, 1, len(pts))
tan = np.gradient(pts, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
nor = np.stack([-tan[:, 1], tan[:, 0]], 1)


def road(t):
    return np.array([np.interp(t, ts, pts[:, 0]), np.interp(t, ts, pts[:, 1])])


HW = 3.2
left, right = pts + nor * HW, pts - nor * HW
v = np.concatenate([np.c_[left, np.full(len(left), .02)], np.c_[right, np.full(len(right), .02)]])
n = len(left)
f = [[i, i + 1, n + i + 1, n + i] for i in range(n - 1)]
asphalt = B.diffuse("asphalt", (.19, .19, .2), rough=.42)
B.mesh("road", v, f, asphalt, smooth=False)

# ground: gentle real hills would hide the road, so a plain with a slow swell that falls away from the road
gx, gy = np.meshgrid(np.linspace(-500, 800, 420), np.concatenate([np.linspace(-20, 200, 200), np.linspace(204, 2400, 220)]))
r = np.random.default_rng(6)
gz = np.zeros_like(gx)
for k in range(6):
    a, b, c = r.uniform(.002, .02), r.uniform(.002, .02), r.uniform(0, 6)
    gz += np.sin(gx * a + c) * np.cos(gy * b + c) * (1.2 / (1 + k * .4))
near = np.min(np.hypot(gx[..., None] - pts[::20, 0], gy[..., None] - pts[::20, 1]), axis=-1)
gz = gz * np.clip((near - 8) / 60, 0, 1) - .03
gv = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1)
idx = np.arange(gx.size).reshape(gx.shape)
gf = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
grass = B.diffuse("ground", (.16, .15, .15))
B.mesh("ground", gv, gf, grass)

# line along the road: solid while lit, dashes from the door of station 4 on
paint = B.emission("line", (1, 1, 1), 1.0)
STATIONS = [ts[np.argmin(np.hypot(pts[:, 0] - (x - 960) * d / F_PX, pts[:, 1] - d))] for x, d in zip(SX, DEPTH)]
D4 = STATIONS[3] - .012       # the door of the fourth station
segs = []
step = (.0, )
ts2 = np.linspace(.0, 1, 2600)
pp = np.array([road(t) for t in ts2])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pp, axis=0), axis=1))]
LW = .11
tan2 = np.gradient(pp, axis=0); tan2 /= np.linalg.norm(tan2, axis=1, keepdims=True)
nor2 = np.stack([-tan2[:, 1], tan2[:, 0]], 1)


def strip(i0, i1, name):
    idx = np.arange(i0, i1)
    wd = (LW * (1 + s[idx] / 90))[:, None]
    a = pp[idx] + nor2[idx] * wd
    b = pp[idx] - nor2[idx] * wd
    v = np.r_[np.c_[a, np.full(len(a), .05)], np.c_[b, np.full(len(b), .05)]]
    m = len(a)
    return v, [[j, j + 1, m + j + 1, m + j] for j in range(m - 1)]


iD = int(np.searchsorted(ts2, D4))
v, f = strip(40, iD, "solid")
solid = B.mesh("solid", v, f, paint, smooth=False)
dash_v, dash_f, off = [], [], 0
pos, on = s[iD] + 2, True
while pos < s[-1] * .96:
    L = 3.2 * (1 + pos / 120) * (1 if on else 1.15)
    a, b = np.searchsorted(s, pos), np.searchsorted(s, pos + L)
    if on and b > a + 1:
        v, f = strip(a, b, "d")
        dash_v.append(v); dash_f += [[q + off for q in x] for x in f]; off += len(v)
    pos += L; on = not on
dashes = B.mesh("dashes", np.concatenate(dash_v), dash_f, paint, smooth=False)

# lamps. Same size in the world; perspective does the rest
metal = B.diffuse("metal", (.06, .06, .07), rough=.5)
ARM = 1.5


def bar(a, b, r, mat):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=10)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


lamps, heads = [], []
info = []
for k, t in enumerate(STATIONS):
    p = road(t)
    i = int(np.searchsorted(ts, t))
    side = nor[i] * (HW + 1.2)          # the left kerb
    base = p + side
    top = np.array([base[0], base[1], POLE])
    head = np.array([*(base - nor[i] * ARM), POLE - .18])
    bar((*base, 0), top, .09, metal)
    bar(top, head + np.array([0, 0, .18]), .05, metal)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.3, location=tuple(head))
    o = bpy.context.object
    o.scale = (1.1, 1.1, .45)
    heads.append(o)
    if k < 3:
        o.data.materials.append(B.emission(f"bulb{k}", (1, 1, 1), 22.0))
        ld = bpy.data.lights.new(f"lamp{k}", "SPOT")
        ld.energy, ld.spot_size, ld.spot_blend, ld.shadow_soft_size = 3300, math.radians(150), .6, .3
        l = bpy.data.objects.new(f"lamp{k}", ld)
        l.location = tuple(head - np.array([0, 0, .1]))
        l.rotation_euler = (0, 0, 0)
        sc.collection.objects.link(l)
        lamps.append(l)
    else:
        o.data.materials.append(metal)
    cam_p = np.array(head) - np.array([0, 0, CAMH])
    f_ = 26 / 36 * 1920
    info.append(dict(k=k, top=[960 + f_ * cam_p[0] / cam_p[1], 720 - f_ * cam_p[2] / cam_p[1]],
                     foot=[960 + f_ * base[0] / base[1], 720 + f_ * CAMH / base[1]]))
    print("STATION", k, info[-1], flush=True)

p4 = road(D4)
b4 = p4
f_ = 26 / 36 * 1920
door = [960 + f_ * b4[0] / b4[1], 720 + f_ * CAMH / b4[1]]
json.dump(dict(st=info, door=door), open(os.path.join(A.out, "T6_px.json"), "w"), indent=1) if os.path.isdir(A.out) else None

plan = {"sky": (1.0, [])}
for k, l in enumerate(lamps):
    plan[f"lamp{k}"] = (0.0, [l.name])
plan["solid"] = (0.0, ["solid"])
plan["dash"] = (0.0, ["dashes"])
plan["bulb"] = (0.0, [o.name for o in heads[:3]])
for k, o in enumerate(heads[:3]):
    o.name = f"bulbobj{k}"
plan["bulb"] = (0.0, [o.name for o in heads[:3]])
B.layers(A.out, "T6", plan, lamps + [solid, dashes] + heads[:3], data_scale=500)
json.dump(dict(st=info, door=door), open(os.path.join(A.out, "T6_px.json"), "w"), indent=1)
