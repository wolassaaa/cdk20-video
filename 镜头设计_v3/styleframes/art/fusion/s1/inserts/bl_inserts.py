"""HKBU SCIE1007 coursework science video. S1 table shots: the film's own table, seen first from the film's own overhead view, with a camera that falls to it and climbs back. What lies flat on the page stands up when the camera comes down, and lies back down when it leaves. All schematic, no maker's marks.

a: 32.1-35.4 s. An empty table; a foil strip lands; the camera falls to it; a tablet bursts through the foil and lands.
w: 35.12-35.52 s. A vial falls past the lens, alone on a clear film. It hides the cut from a to b.
b: 35.15-38.78 s. Two vials are set down; the camera climbs back and they lie down where the full view has them.
c: 43.35-48.52 s. The camera falls to the ten flat figures, they stand, seven drain and lie down, three stay, the camera climbs back.
f: 78.8-94.8 s. The camera falls to the road and rides along it as the red line fills the six bulbs; it climbs back and the line runs home.
g: 146.0-152.9 s. The camera falls to the map, three sample tubes are set down, their red rises one after another, they lie down where the full view has them.
h: 224.5-235.4 s. The camera falls to the table, the six source cards are set down two by two, each pair lies back as the next arrives, the camera climbs back.
k: 285.8-312.0 s. A lock and a key land beside the print; the camera slides off it, falls to the lock, then the key, and follows the key into its pocket; it climbs back, a second lock and key land, and the camera falls again to watch that key land on the wrong lock. From 312.0 s shot p takes over. The stills between come from the same frames, held.
p: 312.0-330.0 s. The first key lifts out; the camera falls from the full view to the first lock, which swells into the CDK20 model where it stands; the model turns slowly and a plug lands in its real ATP pocket.
q: 330.0-412.0 s. Further along the same table: 52 sample tubes, 36 of them rise red; ten thin tubes run into one and reach the list of 20; the first road bulb fills; a grid of mostly empty cells, one holding CDK20 over an empty keyhole. Between its moves the frames are held.

Times are seconds on the film's clock. Table units are the plates': 200 px to the unit, y flipped.
Run: blender.exe -b -t 4 -P bl_inserts.py -- <a|w|b|c> <out dir> [first] [last] [samples] [size] [step] [model]
Shots kept in another file: set BL_EXTRA=<file.py>. That file starts with META = {"<shot>": (start s, frames, sky low, sky high)} as a plain literal, defines shot_<name>(sc, sky)
like the ones here and adds it with SHOTS["<name>"] = shot_<name>; it runs inside this script, so every function here is in reach. w3_end(sc, sky) gives the table as W3 leaves it.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
sys.path[:0] = [HERE + "../code/", HERE + "../../code/"]
import bl_shots as B   # noqa: E402
import world as W      # noqa: E402

P, gk = B.P, B.gk
argv = sys.argv[sys.argv.index("--") + 1:]
SHOT, OUT = argv[0], argv[1]
XFILE = os.environ.get("BL_EXTRA")    # shots kept in another file; see the note at the top
XMETA = {}
if XFILE:
    import ast
    XMETA = next(ast.literal_eval(n.value) for n in ast.parse(open(XFILE, encoding="utf-8").read()).body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "META")
START = dict(a=32.1, w=35.12, b=35.15, c=43.35, f=78.8, g=146.0, h=224.5, k=285.8, p=312.0, q=330.0, x=330.0, y=412.0, z=437.0, v=412.0, u=412.0, t=412.0, r=412.0, s=412.0, n=412.0, o=412.0, m=412.0, j=412.0, l=412.0, e=412.0, d=412.0, i=437.0, i2=463.0, i3=480.0, i4=505.0, lp=508.5, hz=557.0, hk=557.0, w3=574.0, **{k: v[0] for k, v in XMETA.items()})[SHOT]
FRAMES = dict(a=198, w=24, b=218, c=310, f=960, g=414, h=654, k=1644, p=1080, q=4920, x=4920, y=1501, z=721, v=6, u=2551, t=6, r=6, s=6, n=4, o=3, m=1171, j=1055, l=1055, e=1055, d=1517, i=1560, i2=1020, i3=1080, i4=210, lp=2490, hz=1020, hk=1020, w3=952, **{k: v[1] for k, v in XMETA.items()})[SHOT]
FIRST = int(argv[2]) if len(argv) > 2 else 0
LAST = min(int(argv[3]), FRAMES - 1) if len(argv) > 3 else FRAMES - 1
SAMPLES = int(argv[4]) if len(argv) > 4 else 64
SIZE = float(argv[5]) if len(argv) > 5 else 1
STEP = int(argv[6]) if len(argv) > 6 else 1
ONLY = argv[7] if len(argv) > 7 else ""      # "model": shot p shows the finished model in place of the growing shape, for the dissolve at the end of the growth
FPS = 60.0
K = W.PPU
TOP = dict(at=(24.0, -2.7, 0.0), az=0.0, el=math.radians(89.9), d=160.0, mm=600.0)    # a very long lens, high up: the full view's frame at the table, to within a pixel


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def lerp(a, b, x):
    return tuple(p + (q - p) * x for p, q in zip(a, b))


def stage():
    """The same table and sun as the plates. Camera rays that miss the floor see bone, so there is no horizon. Reflections see one big window behind the objects while the camera is low, because a low camera never sees the plates' window above; sky(x) slides it back overhead as the camera climbs."""
    sc = P.scene(samples=SAMPLES, w=int(1920 * SIZE), h=int(1080 * SIZE))
    sc.cycles.denoising_use_gpu = True
    sc.render.use_persistent_data = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.fps = int(FPS)
    nt = sc.world.node_tree
    pick = lambda kind: [n for n in nt.nodes if n.type == kind]
    dot, win = pick("VECT_MATH")[0], pick("MAP_RANGE")[1]
    low, high = dict(a=0.2, w=0.2, b=0.1, c=0.04, f=0.25, g=0.2, h=0.2, k=0.2, p=0.2, q=0.2, x=0.2, y=0.2, z=0.2, v=0.2, u=0.2, t=0.2, r=0.2, s=0.2, n=0.2, o=0.2, m=0.2, j=0.2, l=0.2, e=0.2, d=0.2, i=0.2, i2=0.2, i3=0.2, i4=0.2, lp=0.2, hz=0.2, hk=0.2, w3=0.2, **{k: v[2] for k, v in XMETA.items()})[SHOT], dict(a=1.25, w=1.25, b=2.0, c=2.6, f=2.0, g=2.0, h=2.0, k=0.9, p=0.9, q=0.9, x=0.9, y=0.9, z=0.9, v=0.9, u=0.9, t=0.9, r=0.9, s=0.9, n=0.9, o=0.9, m=0.9, j=0.9, l=0.9, e=0.9, d=0.9, i=0.9, i2=0.9, i3=0.9, i4=0.9, lp=0.9, hz=0.9, hk=0.9, w3=0.9, **{k: v[3] for k, v in XMETA.items()})[SHOT]

    def sky(x):
        dot.inputs[1].default_value = lerp((-0.22, 0.92, 0.32), P.WINDOW, x)
        win.inputs[1].default_value, win.inputs[2].default_value = lerp((0.74, 0.97), (0.92, 0.975), x)
        win.inputs[3].default_value, win.inputs[4].default_value = lerp((low, high), (0.03, 7.0), x)
    sky(0)
    bone = nt.nodes.new("ShaderNodeBackground")
    bone.inputs[0].default_value = (*P.BONE_LIN, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pick("LIGHT_PATH")[0].outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(pick("BACKGROUND")[0].outputs[0], mix.inputs[1])
    nt.links.new(bone.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], pick("OUTPUT_WORLD")[0].inputs[0])
    P.floor()
    bpy.data.objects["floor"].scale = (5, 5, 1)
    P.sun()
    return sc, sky


def lens(sc, stop):
    d = bpy.data.cameras.new("cam")
    d.sensor_width = 36
    d.clip_start, d.clip_end = 0.05, 400
    d.dof.use_dof, d.dof.aperture_fstop = True, stop
    c = bpy.data.objects.new("cam", d)
    sc.collection.objects.link(c)
    sc.camera = c
    c.rotation_mode = "QUATERNION"
    return c


def polar(eye, at, mm):
    v = Vector(eye) - Vector(at)
    return dict(at=tuple(at), az=math.atan2(v.x, -v.y), el=math.asin(v.z / v.length), d=v.length, mm=mm)


def eye_of(v):
    c = math.cos(v["el"])
    return (v["at"][0] + v["d"] * math.sin(v["az"]) * c, v["at"][1] - v["d"] * math.cos(v["az"]) * c, v["at"][2] + v["d"] * math.sin(v["el"]))


def fall(p, q, x):
    """From a high view p down to a low view q. Distance and lens ease on a log scale, so the fall reads at one even speed. The tilt comes late: the camera drops first and looks up as it lands."""
    y = smooth((x - 0.2) / 0.8)
    log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
    return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * y, d=log("d"), mm=log("mm"))


def climb(p, q, x):
    """The same move run backwards: from a low view p up to a high view q."""
    return fall(q, p, 1 - x)


last_q = [None]


def shoot(c, f, v, focus):
    eye = eye_of(v)
    q = (Vector(v["at"]) - Vector(eye)).to_track_quat("-Z", "Y")
    if last_q[0] is not None and q.dot(last_q[0]) < 0:
        q.negate()
    last_q[0] = q.copy()
    c.location, c.rotation_quaternion = eye, q
    c.data.lens = v["mm"]
    c.data.dof.focus_distance = (Vector(focus) - Vector(eye)).length
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_quaternion", frame=f)
    c.data.keyframe_insert("lens", frame=f)
    c.data.dof.keyframe_insert("focus_distance", frame=f)


def mesh(name, verts, faces, mat, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    B.smooth(o)
    o.parent = parent
    return o


def lathe(profile, mat, name, parent=None, n=96):
    """Turns a (radius, height) profile about the z axis."""
    verts = [(r * math.cos(2 * math.pi * j / n), r * math.sin(2 * math.pi * j / n), z) for r, z in profile for j in range(n)]
    faces = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j) for i in range(len(profile) - 1) for j in range(n)]
    return mesh(name, verts, faces, mat, parent)


def empty(name):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_mode = "QUATERNION"
    return o


def pipe(pts, r_px, mat, name, taper=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r_px / K, 8
    cu.use_fill_caps = True
    s = cu.splines.new("POLY")
    s.points.add(len(pts) - 1)
    for i, (q, xy) in enumerate(zip(s.points, pts)):
        q.co = (xy[0] / K, -xy[1] / K, W.SURFACE_Z / K, 1)
        if taper:
            q.radius = taper[i]
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o


def tube(front):
    """The glass line of the full view, filled as far as x = front."""
    path = W.PATHS["main_a"]
    glass = pipe(path, W.TUBE_R, B.clear_glass(), "glass")
    glass.visible_shadow, glass.visible_diffuse = False, False
    wet = pipe(path if front is None else path[:int(W.s_at("main_a", (front, 1010)) / 4) + 1], W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid")
    wet.visible_diffuse = False


# ---------------------------------------------------------------- the strip and the tablet, twice the plates' size in their own units
HALF = (2.0, 1.12)
S = 0.5                                 # own units to table units
POCKETS = [(c * 0.92, r * 0.50) for r in (-1, 1) for c in (-1.5, -0.5, 0.5, 1.5)]
HERO = POCKETS[2]
Z_FOIL, RIM = 0.25, 0.34
TEAR, LEAVE, LAND = 0.55, 0.75, 1.46    # seconds after 33.0: foil tears, tablet clears it, tablet lands
SPOT = (1.1, -1.5)                      # just below the strip on the table, above the word Nexavar in the full view
TABLET = [(0, 0.115), (0.08, 0.112), (0.16, 0.100), (0.24, 0.078), (0.285, 0.056), (0.30, 0.04), (0.30, -0.04), (0.285, -0.056), (0.24, -0.078), (0.16, -0.100), (0.08, -0.112), (0, -0.115)]
G = 8.0                                 # gravity in the strip's units: a macro lens running slow


def on_strip(p):
    return (W.BLISTER[0] / K + p[0] * S, -W.BLISTER[1] / K + p[1] * S, p[2] * S)


def tablet_rest(tilt):
    """Height of the centre when the tablet lies tilted on the table."""
    return -min(h * math.cos(tilt) - r * math.sin(tilt) for r, h in TABLET)


def ground(t, x, y):
    """Foil height: faint crinkle, a raised disc over each pocket, and the swelling over the hero pocket before it tears."""
    z = Z_FOIL + 0.010 * np.sin(3.1 * x + 1.3 * y + 0.7) * np.sin(2.3 * y - 1.1 * x)
    z = z + 0.0045 * np.sin(11 * x + 4 * y + 2) * np.sin(9 * y - 5 * x + 1) + 0.0018 * np.sin(27 * x - 13 * y) * np.sin(23 * y + 11 * x)
    for px, py in POCKETS:
        r = np.hypot(x - px, y - py)
        q = np.clip((0.42 - r) / 0.10, 0, 1)
        z = z + 0.026 * q * q * (3 - 2 * q)
    return z + 0.10 * smooth((t - 0.05) / 0.5) * np.exp(-(np.hypot(x - HERO[0], y - HERO[1]) / 0.27) ** 2)


def torn(t):
    x = (t - TEAR) / 0.16
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    x -= 1
    return 1 + 2.7 * x ** 3 + 1.7 * x ** 2


class Strip:
    def __init__(self, parent=None):
        foil, nt, out = gk._mat("foil")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = (0.70, 0.70, 0.72, 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.28
        nt.links.new(b.outputs[0], out.inputs["Surface"])
        self.skin = b
        nx, ny = 501, 281
        x, y = np.meshgrid(np.linspace(-HALF[0], HALF[0], nx), np.linspace(-HALF[1], HALF[1], ny))
        cr = 0.09
        cx, cy = HALF[0] - cr, HALF[1] - cr
        dx, dy = np.abs(x) - cx, np.abs(y) - cy
        r = np.hypot(dx, dy)
        out_corner = (dx > 0) & (dy > 0) & (r > cr)
        x = np.where(out_corner, np.sign(x) * (cx + dx / np.maximum(r, 1e-6) * cr), x)
        y = np.where(out_corner, np.sign(y) * (cy + dy / np.maximum(r, 1e-6) * cr), y)
        r = np.hypot(x - HERO[0], y - HERO[1])
        near = (r >= RIM) & (r < RIM + 0.0096)        # pull the grid onto the rim so the hole is a clean circle
        x = np.where(near, HERO[0] + (x - HERO[0]) / r * RIM, x)
        y = np.where(near, HERO[1] + (y - HERO[1]) / r * RIM, y)
        keep = np.hypot(x - HERO[0], y - HERO[1]) >= RIM - 1e-5
        ids = np.arange(nx * ny).reshape(ny, nx)
        q = np.stack((ids[:-1, :-1], ids[:-1, 1:], ids[1:, 1:], ids[1:, :-1]), 2).reshape(-1, 4)
        q = q[keep.ravel()[q].all(1)]
        self.x, self.y = x.ravel(), y.ravel()
        v = np.stack((self.x, self.y, ground(0, self.x, self.y)), 1)
        self.sheet = mesh("foil", v.tolist(), q.tolist(), foil, parent)
        sol = self.sheet.modifiers.new("skin", "SOLIDIFY")
        sol.thickness, sol.offset = 0.014, -1
        rng = np.random.default_rng(7)
        cuts = np.sort(rng.uniform(0, 2 * math.pi, 1) + np.arange(6) * (2 * math.pi / 6) + rng.uniform(-0.3, 0.3, 6))
        self.petals = []
        for i in range(6):
            a0, a1 = cuts[i], cuts[(i + 1) % 6] + (2 * math.pi if i == 5 else 0)
            m, k = 13, 13
            rim = np.stack((HERO[0] + RIM * np.cos(np.linspace(a0, a1, k)), HERO[1] + RIM * np.sin(np.linspace(a0, a1, k))), 1)
            tip = np.array(HERO) + rng.uniform(-0.025, 0.025, 2)
            s = np.linspace(0, 1, m)
            faces = [(u * m + j, u * m + j + 1, (u + 1) * m + j + 1, (u + 1) * m + j) for u in range(k - 1) for j in range(m - 1)]
            xy = rim[:, None, :] + (tip - rim)[:, None, :] * s[None, :, None]
            v = np.dstack((xy, ground(0, xy[..., 0], xy[..., 1]))).reshape(-1, 3)
            self.petals.append(dict(o=mesh("petal", v.tolist(), faces, foil, parent), rim=rim, tip=tip, s=s, lift=rng.uniform(0.72, 1.12)))
        tablet, dome = P.gloss((0.32, 0.012, 0.008), 0.25, 0.6), B.clear_glass()
        self.tablet_mat = tablet
        for xy in POCKETS:
            d = lathe([(0.38 * math.sin(a), Z_FOIL * (1 - math.cos(a))) for a in np.linspace(0, math.pi / 2, 12)], dome, "dome", parent)
            d.location = (*xy, 0)
            d.visible_shadow = False
            if xy != HERO:
                c = lathe(TABLET, tablet, "tablet", parent)
                c.location = (*xy, 0.118)

    def seen(self, x):
        """Mirror foil for a low camera; from overhead, where the dark room would turn it to chrome, the plain pale strip of the plates."""
        self.skin.inputs["Metallic"].default_value = 1.0 - 0.8 * x
        self.skin.inputs["Roughness"].default_value = 0.28 + 0.27 * x
        self.skin.inputs["Base Color"].default_value = (*lerp((0.70, 0.70, 0.72), (0.80, 0.80, 0.80), x), 1)

    def update(self, t):
        v = np.stack((self.x, self.y, ground(t, self.x, self.y)), 1)
        self.sheet.data.vertices.foreach_set("co", v.astype(np.float32).ravel())
        self.sheet.data.update()
        k = torn(t)
        for p in self.petals:
            s, rim, tip = p["s"], p["rim"], p["tip"]
            root = rim.mean(0)
            lg = np.linalg.norm(tip - root)
            ang = p["lift"] * k * (2.2 + 0.5 * s)
            mid = (ang[:-1] + ang[1:]) / 2
            rho = lg * np.concatenate(([0], np.cumsum(np.cos(mid) * np.diff(s))))
            up = lg * np.concatenate(([0], np.cumsum(np.sin(mid) * np.diff(s))))[None, :]
            flat = rim[:, None, :] + (tip - rim)[:, None, :] * s[None, :, None]
            w = (1 - s) * (1 + min(k, 1) * 0.22 * np.sin(19 * s + p["lift"] * 9))
            xy = root[None, None, :] + ((tip - root) / lg)[None, None, :] * rho[None, :, None] + (rim - root)[:, None, :] * w[None, :, None]
            zr = ground(t, rim[:, 0], rim[:, 1])[:, None]
            z = ground(t, flat[..., 0], flat[..., 1]) * (1 - min(k, 1)) + zr * min(k, 1) + up
            p["o"].data.vertices.foreach_set("co", np.dstack((xy, z)).astype(np.float32).ravel())
            p["o"].data.update()


def tablet_path(t):
    """Location and rotation of the hero tablet. The tumble ends tilted; on the table the tilt dies away while it circles faster, like a dropped coin."""
    z0, z1, tilt0 = 0.118, 0.42, 0.34
    vz = (tablet_rest(tilt0) - z1 + 0.5 * G * (LAND - LEAVE) ** 2) / (LAND - LEAVE)
    dx, dy = SPOT[0] - HERO[0], SPOT[1] - HERO[1]
    ln = math.hypot(dx, dy)
    axis = (dy / ln, -dx / ln, 0)
    speed = ln / (LAND - LEAVE)
    if t < TEAR:
        return (HERO[0], HERO[1], z0 + 0.09 * smooth((t - 0.05) / 0.5)), Quaternion()
    if t < LEAVE:
        x = (t - TEAR) / (LEAVE - TEAR)
        return (HERO[0], HERO[1], z0 + 0.09 + (z1 - z0 - 0.09) * x * x), Quaternion()
    if t < LAND:
        x, d = (t - LEAVE) / (LAND - LEAVE), t - LEAVE
        z = z1 + vz * d - 0.5 * G * d * d
        return (HERO[0] + dx * x, HERO[1] + dy * x, z), Quaternion(axis, tilt0 + (1 - x) * 2 * math.pi)
    d = t - LAND
    tilt = tilt0 * math.exp(-d / 0.30)
    phi = math.atan2(axis[1], axis[0]) + 2 * math.pi * (1.1 * d + 1.7 * d * d)
    v = vz - G * (LAND - LEAVE)
    hop, v, t0 = 0.0, -0.33 * v, 0.0
    for _ in range(3):
        span = 2 * v / G
        if d < t0 + span:
            hop = v * (d - t0) - 0.5 * G * (d - t0) ** 2
            break
        t0, v = t0 + span, v * 0.33
    slide = 0.11 * speed * (1 - math.exp(-d / 0.11))
    roll = 0.22 * tilt
    return (SPOT[0] + dx / ln * slide - roll * math.sin(phi), SPOT[1] + dy / ln * slide + roll * math.cos(phi), tablet_rest(tilt) + hop), Quaternion((math.cos(phi), math.sin(phi), 0), tilt)


def spent_strip():
    """The strip as it stays for the rest of the scene: torn, the tablet at rest beside it."""
    root = empty("strip")
    root.location, root.scale = on_strip((0, 0, 0)), (S, S, S)
    strip = Strip(root)
    strip.update(9.0)
    hero = lathe(TABLET, strip.tablet_mat, "hero", root)
    hero.rotation_mode = "QUATERNION"
    hero.location, hero.rotation_quaternion = tablet_path(9.0)
    return strip


def a_view(t):
    t = max(0.0, t - 33.0)
    x = smooth(t / 2.3)
    pull = smooth((t - LEAVE) / (LAND - LEAVE + 0.1))
    look = lerp((HERO[0] - 0.05, HERO[1] - 0.15, 0.25), (SPOT[0] - 0.25, SPOT[1] + 0.45, 0.14), pull)
    return polar(on_strip(lerp((1.55, -6.55, 1.72), (1.15, -5.85, 1.42), x)), on_strip(look), 60), on_strip(lerp((*HERO, 0.3), (SPOT[0] + 0.08, SPOT[1] - 0.23, 0.12), pull))


def strip_height(t):
    """Falls from above the lens onto the table, with one small bounce."""
    x = (t - 32.3) / 0.32
    if x < 1:
        return 110 * (1 - max(0.0, x) ** 2)
    d = t - 32.62
    return 0.04 * math.sin(math.pi * d / 0.16) if d < 0.16 else 0.0


def a_fall(t):
    return smooth((t - 32.5) / 0.85)


def shot_a(sc, sky):
    c = lens(sc, 1.0)
    tube(3950)
    Crowd(False)
    root = empty("strip")
    root.scale = (S, S, S)
    strip = Strip(root)
    hero = lathe(TABLET, strip.tablet_mat, "hero", root)
    hero.rotation_mode = "QUATERNION"
    last = None
    for f in range(FRAMES + 1):
        t = START + f / FPS
        loc, q = tablet_path(t - 33.0)
        if last is not None and q.dot(last) < 0:
            q.negate()
        last = q.copy()
        hero.location, hero.rotation_quaternion = loc, q
        hero.keyframe_insert("location", frame=f)
        hero.keyframe_insert("rotation_quaternion", frame=f)
        root.location = (*on_strip((0, 0, 0))[:2], strip_height(t))
        root.keyframe_insert("location", frame=f)
        v, focus = a_view(t)
        shoot(c, f, fall(TOP, v, a_fall(t)), focus if a_fall(t) > 0.5 else on_strip((0, 0, 0)))

    def update(t):
        strip.update(t - 33.0)
        strip.seen(1 - a_fall(t))
        sky(1 - a_fall(t))
    return update


# ---------------------------------------------------------------- the vials
VIAL_R = 62 / K
STAND = [(x / K, -(y + 125) / K - VIAL_R) for x, y in W.VIALS]    # upright here, each vial lies down onto its spot in the full view


def px(profile):
    return [(r / K, (a + 125) / K) for r, a in profile]


class Dose:
    """The liquid in a vial. Its surface is a tilting plane with a ring wave on top, a damped swing started when the vial lands."""

    R, ZT, N = 0.30, 0.855, 64
    ROWS = [(0, 0.03, 0), (0.28, 0.03, 0), (0.295, 0.04, 0), (0.30, 0.08, 0)] + [(0.30, None, w) for w in (0.25, 0.5, 0.75, 0.95, 1)] + [(0.30 * k / 6, None, 1) for k in (5.7, 5, 4, 3, 2, 1, 0)]

    def __init__(self, parent, mat, swing):
        n = self.N
        self.swing, q = swing, np.linspace(0, 2 * math.pi, n, endpoint=False)
        self.r = np.repeat([a[0] for a in self.ROWS], n)
        self.w = np.repeat([a[2] for a in self.ROWS], n)
        self.z0 = np.repeat([a[1] if a[1] is not None else 0.08 for a in self.ROWS], n)
        self.x, self.y = self.r * np.tile(np.cos(q), len(self.ROWS)), self.r * np.tile(np.sin(q), len(self.ROWS))
        faces = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j) for i in range(len(self.ROWS) - 1) for j in range(n)]
        self.o = mesh("dose", np.stack((self.x, self.y, self.z(0.0)), 1).tolist(), faces, mat, parent)

    def z(self, d):
        amp = 0.16 * math.exp(-d / 0.62) * math.sin(2 * math.pi * 2.3 * d) if d > 0 else 0.0
        rip = 0.016 * math.exp(-d / 0.36) * math.sin(2 * math.pi * 4.7 * d) if d > 0 else 0.0
        a = self.swing
        surf = self.ZT + amp * (self.x * math.cos(a) + self.y * math.sin(a)) + rip * ((self.r / self.R) ** 2 - 0.5) + 0.012 * (self.r / self.R) ** 8
        return np.where(self.w > 0, 0.08 + (surf - 0.08) * self.w, self.z0)

    def update(self, d):
        self.o.data.vertices.foreach_set("co", np.stack((self.x, self.y, self.z(d)), 1).astype(np.float32).ravel())
        self.o.data.update()


def lying(d):
    """How far a vial has tipped back, d seconds after it starts: it falls like a hinged lid and knocks twice."""
    if d <= 0:
        return 0.0
    if d < 0.42:
        return math.pi / 2 * (d / 0.42) ** 2
    d -= 0.42
    return math.pi / 2 - math.radians(3.2) * abs(math.sin(2 * math.pi * 3.4 * d)) * math.exp(-d / 0.09)


def set_down(root, xy, land, swing, tip):
    """Falls from above the frame and slows, but still touches down with a small knock, then rocks on its base. Later it tips back about the far edge of its base."""
    drop, h, last = 0.62, 1.95, None
    ax = (math.cos(swing), math.sin(swing), 0)
    for f in range(FRAMES + 1):
        t = START + f / FPS
        s = min(1.0, max(0.0, (t - land + drop) / drop))
        d = t - land
        rock = math.radians(1.5) * math.exp(-d / 0.28) * math.cos(2 * math.pi * 3.2 * d) if d > 0 else math.radians(1.5) * (1 - s)
        back = lying(t - tip)
        q = Quaternion((1, 0, 0), -back) @ Quaternion(ax, rock)
        if last is not None and q.dot(last) < 0:
            q.negate()
        last = q.copy()
        root.location = (xy[0], xy[1] + VIAL_R * (1 - math.cos(back)), VIAL_R * math.sin(back) + h * (1 - s) * (1 - 0.7 * s) + VIAL_R * abs(math.sin(rock)))
        root.rotation_quaternion = q
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_quaternion", frame=f)


def vial_body(swing):
    glass, paper = B.clear_glass(), gk.surface((0.86, 0.85, 0.81), 0.5, 0.2)
    liquid = B.fluid((0.42, 0.52, 0.86), (0.8, 0.86, 0.96))
    cap, seal = P.gloss(P.KLEIN, 0.25, 0.6), gk.surface((0.62, 0.62, 0.64), 0.35, 0.5)
    root = empty("vial")
    o = lathe(px([(0, -125), (54, -125), (62, -117), (62, 52), (55, 68), (41, 84), (38, 96), (0, 96)]), glass, "vial_glass", root)
    o.visible_shadow = False
    lathe(px([(0, -100), (63.5, -100), (63.5, -10), (0, -10)]), paper, "vial_label", root)
    lathe(px([(0, -34), (63.9, -34), (63.9, -24), (0, -24)]), cap, "vial_band", root)
    lathe(px([(0, 92), (44, 92), (46, 96), (46, 112), (0, 112)]), seal, "vial_seal", root)
    lathe(px([(0, 112), (40, 112), (40, 126), (36, 130), (0, 130)]), cap, "vial_cap", root)
    return root, Dose(root, liquid, swing)


def vial(xy, land, swing, tip):
    root, dose = vial_body(swing)
    set_down(root, xy, land, swing, tip)
    return lambda t: dose.update(t - land)


def shot_w(sc, sky):
    """The first vial, close to the lens and far out of focus, on a clear film."""
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    bpy.data.objects["floor"].visible_camera = False
    c = lens(sc, 1.0)
    v, focus = a_view(35.27)
    eye = Vector(eye_of(v))
    look = (Vector(v["at"]) - eye).normalized()
    fill = P.sun(1.1, 40.0)                     # from the lens, so the wipe stays as pale as the table instead of blinking dark
    fill.rotation_mode = "QUATERNION"
    fill.rotation_quaternion = look.to_track_quat("-Z", "Y")
    root, _ = vial_body(0.5)
    for f in range(FRAMES + 1):
        t = START + f / FPS
        shoot(c, f, v, focus)
        root.location = (*(eye + look * 0.92).xy, eye.z - 0.35 - 5.2 * (t - 35.27) - 1.2 * (t - 35.27) ** 2)
        root.keyframe_insert("location", frame=f)
    return lambda t: None


B_AT = (24.35, -2.2, 0.62)
CLIMB_B = (37.55, 1.1)


def b_view(t):
    x = smooth((t - 35.15) / 2.6)
    return polar(lerp((29.2, -8.6, 1.08), (28.7, -8.2, 1.0), x), B_AT, 85)


def shot_b(sc, sky):
    c = lens(sc, 0.6)
    tube(3950)
    Crowd(False)
    strip = spent_strip()
    first, second = vial(STAND[0], 35.92, 0.5, 37.75), vial(STAND[1], 36.48, 2.2, 37.85)
    focus = (STAND[0][0], STAND[0][1], 0.63)
    for f in range(FRAMES + 1):
        t = START + f / FPS
        x = smooth((t - CLIMB_B[0]) / CLIMB_B[1])
        shoot(c, f, climb(b_view(t), TOP, x), focus if x < 0.5 else TOP["at"])

    def update(t):
        first(t)
        second(t)
        x = smooth((t - CLIMB_B[0]) / CLIMB_B[1])
        strip.seen(x)
        sky(x)
    return update


# ---------------------------------------------------------------- ten figures
TALL = 0.85
FEET = -985 / K                         # the line their feet stand on in the full view
DRAIN = [None, None, None] + [44.6 + i * 0.22 for i in range(7)]   # the same stagger as the film's table
RISE = [43.62 + i * 0.045 for i in range(10)]
DOWN = [47.85 + i * 0.06 for i in range(3)] + [46.95 + i * 0.07 for i in range(7)]   # the seven first; the three last, as the camera leaves


def outline():
    """The stand-in's plain person shape, feet on y = 0. Same shape as bl_plate.py's figure."""
    half = [(0, 435), (60, 420), (98, 360), (104, 300), (92, 235), (62, 185), (52, 150), (56, 120), (100, 92), (210, 62), (270, 30), (300, -30), (315, -120), (330, -300), (340, -420)]
    ctrl = half + [(-x, y) for x, y in reversed(half[1:])]
    n, pts = len(ctrl), []
    for i in range(n):
        a, b, c, d = [Vector(ctrl[(i + k) % n]) for k in (-1, 0, 1, 2)]
        for t in (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            pts.append(0.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    k = TALL / 855.0
    return [(q.x * k, (q.y + 420) * k) for q in pts]


def fill_mat(i):
    """Red below a level, pale above it. The level is a liquid surface: it trembles a little across the figure."""
    m, nt, out = gk._mat("fill%d" % i)
    pale = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pale.inputs["Base Color"].default_value = (0.70, 0.69, 0.655, 1)
    pale.inputs["Roughness"].default_value = 0.55
    pale.inputs["Specular IOR Level"].default_value = 0.15
    red = nt.nodes.new("ShaderNodeBsdfPrincipled")
    red.inputs["Base Color"].default_value = (*P.RED, 1)
    red.inputs["Roughness"].default_value = 0.3
    red.inputs["Specular IOR Level"].default_value = 0.2
    red.inputs["Coat Weight"].default_value = 0.25
    red.inputs["Coat Roughness"].default_value = 0.08
    pos = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos.outputs["Position"], sep.inputs[0])
    level = nt.nodes.new("ShaderNodeValue")
    level.name = "level"
    phase = nt.nodes.new("ShaderNodeValue")
    phase.name = "phase"
    a = nt.nodes.new("ShaderNodeMath")
    a.operation = "MULTIPLY"
    a.inputs[1].default_value = 9.0
    nt.links.new(sep.outputs["X"], a.inputs[0])
    b = nt.nodes.new("ShaderNodeMath")
    nt.links.new(a.outputs[0], b.inputs[0])
    nt.links.new(phase.outputs[0], b.inputs[1])
    c = nt.nodes.new("ShaderNodeMath")
    c.operation = "SINE"
    nt.links.new(b.outputs[0], c.inputs[0])
    d = nt.nodes.new("ShaderNodeMath")
    d.operation = "MULTIPLY"
    d.inputs[1].default_value = 0.010
    nt.links.new(c.outputs[0], d.inputs[0])
    e = nt.nodes.new("ShaderNodeMath")
    nt.links.new(level.outputs[0], e.inputs[0])
    nt.links.new(d.outputs[0], e.inputs[1])
    f = nt.nodes.new("ShaderNodeMath")
    f.operation = "SUBTRACT"
    nt.links.new(sep.outputs["Z"], f.inputs[0])
    nt.links.new(e.outputs[0], f.inputs[1])
    r = nt.nodes.new("ShaderNodeMapRange")
    r.inputs[1].default_value, r.inputs[2].default_value = -0.004, 0.004
    r.inputs[3].default_value, r.inputs[4].default_value = 0.0, 1.0
    nt.links.new(f.outputs[0], r.inputs[0])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(r.outputs[0], mx.inputs[0])
    nt.links.new(red.outputs[0], mx.inputs[1])
    nt.links.new(pale.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


class Crowd:
    """Ten figures lying flat where the full view has them, each hinged at its feet like a pop-up in a book."""

    def __init__(self, red):
        poly = outline()
        self.mats, self.figs = [], []
        for i, (x, _) in enumerate(W.TEN):
            m = fill_mat(i)
            m.node_tree.nodes["level"].outputs[0].default_value = 2.0 if red else -1.0
            self.mats.append(m)
            o = B.extrude([poly], 0.10, 0.03, name="figure", mat=m)
            o.select_set(False)                  # extrude applies transforms to everything selected
            o.location = (x / K, FEET, 0)
            self.figs.append(o)

    def angle(self, i, t):
        """Up from flat. They come up past upright and settle; they go down like a hinged lid."""
        up, down = RISE[i], DOWN[i]
        d = t - up
        a = math.pi / 2 * smooth(d / 0.45)
        if d > 0.45:
            a += math.radians(3) * math.exp(-(d - 0.45) / 0.16) * math.sin(2 * math.pi * 2.6 * (d - 0.45))
        d = (t - down) / 0.46
        return a * (1 - max(0.0, min(1.0, d)) ** 2)

    def pose(self):
        for f in range(FRAMES + 1):
            t = START + f / FPS
            for i, o in enumerate(self.figs):
                a = self.angle(i, t)
                o.rotation_euler = (a, 0, 0)
                o.location.y = FEET + 0.05 * math.sin(a)
                o.keyframe_insert("rotation_euler", frame=f)
                o.keyframe_insert("location", frame=f)

    def update(self, t):
        for i, m in enumerate(self.mats):
            n = m.node_tree.nodes
            go = DRAIN[i]
            n["phase"].outputs[0].default_value = 5.0 * t + i * 1.7
            n["level"].outputs[0].default_value = 2.0 if go is None else TALL * 1.03 * (1 - smooth((t - go) / 0.85)) - 0.03 * smooth((t - go) / 0.85)


C_FALL, C_CLIMB = (43.5, 0.9), (47.35, 1.0)


def c_view(t):
    x = smooth((t - 44.3) / 3.0)
    return polar(lerp((17.5, -12.175, 0.30), (17.75, -11.875, 0.26), x), lerp((22.45, -4.925, 1.10), (22.51, -4.925, 1.08), x), 50)


def shot_c(sc, sky):
    c = lens(sc, 0.8)
    tube(5422)
    strip = spent_strip()
    for xy, s in zip(STAND, (0.5, 2.2)):
        vial(xy, 30.0, s, 31.0)
    crowd = Crowd(True)
    crowd.pose()
    focus = (21.1, FEET, 0.45)
    for f in range(FRAMES + 1):
        t = START + f / FPS
        a, b = smooth((t - C_FALL[0]) / C_FALL[1]), smooth((t - C_CLIMB[0]) / C_CLIMB[1])
        v = climb(c_view(t), TOP, b) if b > 0 else fall(TOP, c_view(t), a)
        shoot(c, f, v, focus if 0.5 < a and b < 0.5 else TOP["at"])

    def update(t):
        crowd.update(t)
        x = 1 - smooth((t - C_FALL[0]) / C_FALL[1]) + smooth((t - C_CLIMB[0]) / C_CLIMB[1])
        strip.seen(x)
        sky(x)
    return update


# ---------------------------------------------------------------- the road
RING = 0.31
TOP_F = dict(TOP, at=(62.4, -2.7, 0.0))
XS = [x / K for x, _ in W.STATIONS]
Y_ROAD = -W.ROAD_Y / K
END_F = (W.STATIONS[5][0] + 90) / K
STEPS = [80.7, 81.9, 84.3, 85.6, 88.1, 91.6]    # the film's six words; each bulb is full as its word lands
F_FALL, F_CLIMB, F_BACK = (78.9, 1.3), (92.2, 1.3), (93.1, 1.4)


def road_front(t):
    """Table x of the liquid's front. It runs from bulb to bulb, and at the end it runs back into the first."""
    x = XS[0] + RING
    for i in range(1, 6):
        x += (XS[i] + RING - x) * smooth((t - STEPS[i] + 0.75) / 0.75)
    return x + (XS[0] + RING - x) * smooth((t - F_BACK[0]) / F_BACK[1])


class Bulb:
    """The liquid in a road bulb. Everything past the front is held on it, so the part-full bulb ends in a straight line, as the plates draw it."""

    def __init__(self, x, mat, y=None, z=None, r=RING * 0.93):
        n, m, y, z = 96, 48, Y_ROAD if y is None else y, W.SURFACE_Z / K if z is None else z
        q, p = np.meshgrid(np.linspace(0, 2 * math.pi, n, endpoint=False), np.linspace(0, math.pi, m + 1))
        self.left = x - r
        self.x, self.y, self.z = (x + r * np.sin(p) * np.cos(q)).ravel(), (y + r * np.sin(p) * np.sin(q)).ravel(), (z + 0.85 * r * np.cos(p)).ravel()
        faces = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j) for i in range(m) for j in range(n)]
        self.o = mesh("bulbfluid", np.stack((self.x, self.y, self.z), 1).tolist(), faces, mat)
        self.o.visible_diffuse = False

    def update(self, front):
        self.o.hide_render = front <= self.left
        self.o.data.vertices.foreach_set("co", np.stack((np.minimum(self.x, front), self.y, self.z), 1).astype(np.float32).ravel())
        self.o.data.update()


def shot_f(sc, sky):
    c = lens(sc, 1.0)
    tube(None)
    red, ink = B.fluid(P.RED, (0.9, 0.05, 0.03)), gk.surface((0.012, 0.012, 0.014), 0.3)
    for pts in (W.PATHS["main_b"], W.ROAD_TUBE):
        g = pipe(pts, W.TUBE_R, B.clear_glass(), "glass")
        g.visible_shadow, g.visible_diffuse = False, False
    wet = pipe(W.ROAD_TUBE, W.FLUID_R, red, "road")
    wet.visible_diffuse = False
    wet.data.bevel_factor_mapping_end = "SPLINE"
    bulbs = []
    for i, x in enumerate(XS):
        B.bulb(x, Y_ROAD, W.SURFACE_Z / K, RING, ink, None if i else red, width=0.022)
        if i:
            bulbs.append(Bulb(x, red))
    ts = START + np.arange(FRAMES + 1) / FPS
    track = np.interp(ts, STEPS, XS)
    box = np.ones(91) / 91
    for _ in range(2):
        track = np.convolve(np.pad(track, 45, "edge"), box, "valid")        # steps become one long glide
    for f, t in enumerate(ts):
        x = float(track[f])
        v = polar((x - 2.3, -6.3, 0.42), (x + 0.5, Y_ROAD, 0.40), 50)
        a, b = smooth((t - F_FALL[0]) / F_FALL[1]), smooth((t - F_CLIMB[0]) / F_CLIMB[1])
        shoot(c, f, climb(v, TOP_F, b) if b > 0 else fall(TOP_F, v, a), (x, Y_ROAD, 0.1) if 0.5 < a and b < 0.5 else TOP_F["at"])

    def update(t):
        x = road_front(t)
        wet.data.bevel_factor_end = (x - XS[0]) / (END_F - XS[0])
        for b in bulbs:
            b.update(x)
        sky(1 - smooth((t - F_FALL[0]) / F_FALL[1]) + smooth((t - F_CLIMB[0]) / F_CLIMB[1]))
    return update


# ---------------------------------------------------------------- the sample tubes on the map
TOP_G = dict(TOP, at=(14340 / K, -1540 / K, 0.0), mm=1800.0)
TK = 0.22 / K                             # the plates' tube profile, in table units
BASE_G = [(x / K, -(y + 190 * 0.22) / K) for x, y in W.SAMPLES]    # the foot of each tube: lying down from here it lands on its spot in the full view
G_FALL, G_CLIMB = (146.0, 1.1), (151.6, 1.1)
SET_G = [147.25, 147.6, 147.95]
RAISE_G = [149.6, 150.2, 150.8]           # "one protein kept showing up raised": the red climbs to the level the full view has
DOWN_G = [151.75 + i * 0.06 for i in range(3)]


def map_table():
    """The map tile of the plates: the raised land and the thinning red line."""
    land = gk.surface((0.74, 0.725, 0.67), 0.7, 0.1)
    for r in W.HK["rings_simple"]:
        pts = [W.m2w(*p) for p in r["p"]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) < W.MAP[0] or min(xs) > W.MAP[2] or max(ys) < W.MAP[1] or min(ys) > W.MAP[3]:
            continue
        poly = [(x / K, -y / K) for x, y in pts]
        if poly[0] == poly[-1]:
            poly = poly[:-1]
        B.extrude([poly], 0.02, 0.006, name="land", mat=land).select_set(False)
    pts, n = W.PATHS["map"] + W.PATHS["exit"][1:], len(W.PATHS["map"])
    k = [min(1, max(0.3, 1 - 0.7 * i / (n * 0.45)) + max(0, i - len(pts) + 90) / 90 * 0.7) for i in range(len(pts))]
    g = pipe(pts, W.TUBE_R, B.clear_glass(), "glass", taper=k)
    g.visible_shadow, g.visible_diffuse = False, False
    wet = pipe(pts, W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid", taper=k)
    wet.visible_diffuse = False
    return g, wet


class Sample:
    """A sample tube, hinged at its foot. It is set down upright and later lies back on the map like a lid. The red is cut flat at a level that can rise."""

    def __init__(self, xy, land, rise, down, glass, red, cap):
        self.xy, self.land, self.down, self.rise = xy, land, down, rise
        z = lambda a: (a + 190) * TK
        self.root = empty("sample")
        o = lathe([(r * TK, z(a)) for r, a in [(0, -190), (34, -176), (42, -150), (42, 150), (0, 150)]], glass, "sample", self.root)
        o.visible_shadow = False
        lathe([(r * TK, z(a)) for r, a in [(0, 150), (46, 150), (46, 205), (0, 205)]], cap, "sample_cap", self.root)
        self.dose = lathe([(r * TK, z(a)) for r, a in [(0, -178), (30, -166), (36, -146), (36, 30), (0, 30)]], red, "sample_dose", self.root)
        self.dose.visible_diffuse = False
        self.parts = list(self.root.children)
        n = len(self.dose.data.vertices)
        self.v = np.zeros(n * 3, np.float32)
        self.dose.data.vertices.foreach_get("co", self.v)
        self.top, self.low = z(30), z(-105)
        for f in range(FRAMES + 1):
            t = START + f / FPS
            s, d = min(1.0, max(0.0, (t - land + 0.6) / 0.6)), t - land
            hop = 0.012 * math.exp(-d / 0.09) * abs(math.sin(2 * math.pi * 4.5 * d)) if d > 0 else 0.0
            back = math.pi / 2 * min(1.0, max(0.0, (t - down) / 0.42)) ** 2
            self.root.location = (xy[0], xy[1], 2.2 * (1 - s) * (1 - 0.6 * s) + hop + 10 / K * math.sin(back))
            self.root.rotation_quaternion = Quaternion((1, 0, 0), -back)
            self.root.keyframe_insert("location", frame=f)
            self.root.keyframe_insert("rotation_quaternion", frame=f)

    def update(self, t):
        for o in self.parts:
            o.hide_render = t < self.land - 0.6     # the overhead view must not see it waiting above the table
        level = self.low + (self.top - self.low) * smooth((t - self.rise) / 0.85)
        v = self.v.copy()
        v[2::3] = np.minimum(v[2::3], level)
        self.dose.data.vertices.foreach_set("co", v)
        self.dose.data.update()


def g_view(t):
    x = smooth((t - 147.0) / 4.8)
    cx, cy = BASE_G[1]
    return polar(lerp((cx - 1.17, cy - 1.11, 0.10), (cx - 1.08, cy - 1.03, 0.09), x), lerp((cx - 0.17, cy + 0.17, 0.235), (cx - 0.17, cy + 0.17, 0.225), x), 50)


def shot_g(sc, sky):
    c = lens(sc, 2.8)
    road = map_table()
    glass, red, cap = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03)), P.gloss(P.KLEIN, 0.25, 0.6)
    tubes = [Sample(xy, *when, glass, red, cap) for xy, *when in zip(BASE_G, SET_G, RAISE_G, DOWN_G)]
    focus = (BASE_G[1][0], BASE_G[1][1], 0.2)
    for f in range(FRAMES + 1):
        t = START + f / FPS
        a, b = smooth((t - G_FALL[0]) / G_FALL[1]), smooth((t - G_CLIMB[0]) / G_CLIMB[1])
        v = climb(g_view(t), TOP_G, b) if b > 0 else fall(TOP_G, g_view(t), a)
        shoot(c, f, v, focus if 0.5 < a and b < 0.5 else TOP_G["at"])

    def update(t):
        for s in tubes:
            s.update(t)
        for o in road:
            o.data.bevel_factor_start = 0.3 if 146.77 < t < 146.84 else 0.0     # the falling camera crosses the road's first stretch, out of frame; without it nothing red flashes past the lens
        sky(1 - smooth((t - G_FALL[0]) / G_FALL[1]) + smooth((t - G_CLIMB[0]) / G_CLIMB[1]))
    return update


# ---------------------------------------------------------------- the source cards
TOP_H = dict(TOP, at=(20160 / K, -1620 / K, 0.0))
LAND_H = [225.4, 227.0, 227.75, 229.6, 231.2, 233.2]    # as the voice names each source
BACK_H = [227.55, 227.62, 231.0, 231.07, 234.35, 234.42]
H_FALL, H_CLIMB = (224.5, 1.1), (234.2, 1.1)
ROWS_T = (225.6, 228.0, 231.4)
PAGE = (19296, 1190, 600, 850)


def leaf(name, w, h, image):
    """A sheet of card lying face up, its near edge on the x axis. The picture is on the top face; every other face takes the paper's plain margin."""
    t = 0.02
    m, nt, out = gk._mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Specular IOR Level"].default_value = 0.1
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image)
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    glow = nt.nodes.new("ShaderNodeEmission")     # an upright card faces away from the sun; this keeps it paper-pale
    glow.name = "glow"
    glow.inputs["Strength"].default_value = 0.0
    nt.links.new(tex.outputs["Color"], glow.inputs["Color"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(b.outputs[0], add.inputs[0])
    nt.links.new(glow.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    v = [(0, 0, 0), (w, 0, 0), (w, h, 0), (0, h, 0), (0, 0, t), (w, 0, t), (w, h, t), (0, h, t)]
    o = mesh(name, v, [(4, 5, 6, 7), (0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m)
    for p in o.data.polygons:
        p.use_smooth = False
    uv = o.data.uv_layers.new(name="uv").data
    for i in range(len(uv)):
        uv[i].uv = (0.985, 0.5)
    for i, q in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv[i].uv = q
    return o


class Cards:
    """Six cards, each set down on its near edge at its spot in the grid. Each lies back like a lid onto that spot."""

    def __init__(self):
        self.o = []
        for i in range(6):
            col, row = i % 2, i // 2
            o = leaf("card%d" % i, 520 / K, 170 / K, HERE + "frames/cards/card_%d.png" % i)
            o.location = ((19960 + col * 540) / K, -(1280 + row * 186 + 170) / K, 0)
            self.o.append(o)
        for f in range(FRAMES + 1):
            t = START + f / FPS
            for o, land, back in zip(self.o, LAND_H, BACK_H):
                o.rotation_euler = (self.angle(t, land, back), 0, 0)
                o.location.z = 3.4 * (1 - min(1.0, max(0.0, (t - land + 0.6) / 0.6))) * (1 - 0.6 * min(1.0, max(0.0, (t - land + 0.6) / 0.6)))
                o.keyframe_insert("rotation_euler", frame=f)
                o.keyframe_insert("location", frame=f)

    @staticmethod
    def angle(t, land, back):
        d = t - land
        rock = math.radians(2.2) * math.exp(-d / 0.2) * math.cos(2 * math.pi * 3.0 * d) if d > 0 else 0.0
        x = min(1.0, max(0.0, (t - back) / 0.46))
        return (math.pi / 2 + rock) * (1 - x * x)

    def update(self, t):
        for o, land, back in zip(self.o, LAND_H, BACK_H):
            o.hide_render = t < land - 0.6
            o.data.materials[0].node_tree.nodes["glow"].inputs["Strength"].default_value = 0.27 * max(0.0, math.sin(self.angle(t, land, back)))


def shot_h(sc, sky):
    c = lens(sc, 2.0)
    path = W.PATHS["s2"]
    g = pipe(path, W.TUBE_R, B.clear_glass(), "glass")
    g.visible_shadow, g.visible_diffuse = False, False
    pipe(path[:int(W.s_at("s2", (19800, 2060)) / 4) + 1], W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid").visible_diffuse = False
    paper = leaf("paper", PAGE[2] / K, PAGE[3] / K, HERE + "frames/cards/paper.png")
    paper.location = (PAGE[0] / K, -(PAGE[1] + PAGE[3]) / K, 0)
    cards = Cards()
    ts = START + np.arange(FRAMES + 1) / FPS
    track = np.interp(ts, ROWS_T, [-(1450 + i * 186) / K for i in range(3)])
    box = np.ones(61) / 61
    for _ in range(2):
        track = np.convolve(np.pad(track, 30, "edge"), box, "valid")
    x = 20490 / K
    for f, t in enumerate(ts):
        y = float(track[f])
        v = polar((x - 3.7, y - 5.6, 0.50), (x - 0.35, y, 0.80), 40)
        a, b = smooth((t - H_FALL[0]) / H_FALL[1]), smooth((t - H_CLIMB[0]) / H_CLIMB[1])
        shoot(c, f, climb(v, TOP_H, b) if b > 0 else fall(TOP_H, v, a), (x, y, 0.4) if 0.5 < a and b < 0.5 else TOP_H["at"])

    def update(t):
        cards.update(t)
        sky(1 - smooth((t - H_FALL[0]) / H_FALL[1]) + smooth((t - H_CLIMB[0]) / H_CLIMB[1]))
    return update


# ---------------------------------------------------------------- the lock and the key
K_AT = (72.0, -2.7)                     # the middle of the view with both locks, x 14400 on the film's table
K_S = 0.8                               # F3 was drawn at 160 px to the unit; the table is 200


def on_k(x, y=0.0, z=0.0):
    return (K_AT[0] + x * K_S, K_AT[1] + y * K_S, z * K_S)


TOP_K = dict(TOP, at=on_k(0))
TOP_K1 = dict(TOP, at=on_k(-5.6))       # the first lock beside the print
TOP_K2 = dict(TOP, at=on_k(-0.9))
L_LOCK = polar((66.9, -7.2, 1.9), (70.0, -2.7, 0.25), 45)
L_KEY = polar((64.4, -4.4, 0.7), (68.3, -2.78, 0.28), 40)
L_SEAT = polar((67.83, -6.0, 3.58), (69.0, -2.8, 0.5), 45)     # high enough to look down on the pocket with the key above it
L_DOOR = polar((73.7, -5.75, 3.68), (74.9, -2.55, 0.6), 45)
K_PAN, K_FALL, K_CLIMB = (287.0, 1.0), (287.75, 1.5), (297.3, 1.4)
K_FALL2, K_CLIMB2 = (305.7, 1.0), (308.3, 1.1)
K_DIVE, K_LEAVE = (312.15, 1.05), (312.0, 0.5)
L_DIVE = dict(at=(69.35, -2.78, 0.29), az=0.0, el=math.radians(89.9), d=0.3, mm=45.0)     # the floor of the first pocket fills the frame
LAND_K = dict(lock_a=286.55, key_a=286.8, lock_b=305.1, key_b=305.35)
FROM_K = dict(lock_a=(2.5, 0.6), key_a=(1.2, -2.6), lock_b=(1.6, 0.5), key_b=(0.8, -2.6))     # how far from where it lands each throw starts, off the edge of the view, in table units
FLY_K = 0.55
RISE_A, OVER_A, HIT_A = (294.6, 0.7), (294.95, 1.25), 296.8
RISE_B, OVER_B, HIT_B = (306.6, 0.5), (306.75, 0.7), 307.85
FALL_T = 0.3                            # the last stretch of a key, straight down
CARRY = 1.05                            # height a key crosses a lock at, clear of its top at 0.62
GAP_A = 1.75                            # how far back of its seat the first key lies, in F3's units
BACK_B = -0.30                          # where the second key lies
OVER_LOCK_B = (2.3, 0.3)                # how far it moves to lie over the second pocket, in F3's units


def flight(t, land):
    return min(1.0, max(0.0, (t - land + FLY_K) / FLY_K))


def drop(t, land, high=40.0):
    """Height of a thing thrown down at the table, with one small bounce."""
    x = flight(t, land)
    if x < 1:
        return high * (1 - x * x)
    d = t - land
    return 0.05 * abs(math.sin(math.pi * d / 0.17)) * math.exp(-d / 0.11)


def thrown(t, name):
    """Offset of a thrown thing from where it lands, in F3's units. At this long lens height shows only as size, so a straight drop would just appear in the frame; the throw has to cross the edge of the view."""
    x, (dx, dy) = flight(t, LAND_K[name]), FROM_K[name]
    return dx * (1 - x) / K_S, dy * (1 - x) / K_S, drop(t, LAND_K[name]) / K_S


def jolt(t, at, size):
    d = t - at
    return size * math.exp(-d / 0.12) * abs(math.sin(2 * math.pi * 5 * d)) if d > 0 else 0.0


def carried(t, rise, hit, rest, ring, beat, fade):
    """Height of a key lifted off the table, carried over a lock and dropped. The pockets are open at the top, and the teeth only match them at the seat, so sliding in from the side would pass through the lock."""
    if t < hit - FALL_T:
        return CARRY * smooth((t - rise[0]) / rise[1])
    if t < hit:
        x = (t - hit + FALL_T) / FALL_T
        return CARRY + (rest - CARRY) * x * x
    d = t - hit
    return rest + ring * abs(math.sin(math.pi * d / beat)) * math.exp(-d / fade)


def low_k(t):
    return fall(fall(L_LOCK, L_KEY, smooth((t - 290.6) / 2.0)), L_SEAT, smooth((t - 293.9) / 2.4))


def k_view(t):
    if t >= K_DIVE[0]:
        return fall(TOP_K, L_DIVE, smooth((t - K_DIVE[0]) / K_DIVE[1]))
    if t < 300:
        pan = dict(TOP, at=lerp(TOP_K1["at"], TOP_K2["at"], smooth((t - K_PAN[0]) / K_PAN[1])))
        a, b = smooth((t - K_FALL[0]) / K_FALL[1]), smooth((t - K_CLIMB[0]) / K_CLIMB[1])
        return climb(low_k(t), TOP_K, b) if b > 0 else fall(pan, low_k(t), a)
    a, b = smooth((t - K_FALL2[0]) / K_FALL2[1]), smooth((t - K_CLIMB2[0]) / K_CLIMB2[1])
    return climb(L_DOOR, TOP_K, b) if b > 0 else fall(TOP_K, L_DOOR, a)


def k_focus(t):
    if t >= K_DIVE[0]:
        return L_DIVE["at"]
    if t < 290.6:
        return (70.0, -2.7, 0.3)
    if t < 294.2:
        return lerp((70.0, -2.7, 0.3), (67.6, -2.78, 0.2), smooth((t - 290.6) / 2.0))
    if t < 300:
        return lerp((67.6, -2.78, 0.2), (69.0, -2.8, 0.55), smooth((t - 293.9) / 2.4))
    return (74.9, -2.55, 0.6)


def k_things():
    """The two locks and two keys, as movers under one table empty scaled from F3's units."""
    root = empty("table")
    root.location, root.scale = (*K_AT, 0), (K_S, K_S, K_S)

    def held(parts):
        e = empty("mover")
        e.parent = root
        for o in parts:
            o.parent = e
        return e
    red = P.gloss(P.RED, 0.18, 0.7)
    x_a, y = -4.3, -0.1

    def key_at(x):
        parts = B.key(x, y, red, z=0.0)
        parts[0].location.z = -0.008        # the blade's end lies inside the bow at the same height, and in the air the two faces show as a black patch
        return held(parts)
    lock_a = held([B.lock(-2.42, -0.02, 1.62, [(2, 0.06, 0.8), (3, 0.05, 2.1), (5, 0.022, 0.4)], B.round_poly(B.key_blade(x_a, y, c=0.035), 0.03), P.gloss(P.KLEIN, 0.2, 0.7))])
    key_a = key_at(x_a)
    # the other lock's pocket has its notches on the far side, so with the blade over it the teeth land on the top of the lock
    other = [(x, 2 * y + 0.3 - v) for x, v in B.key_blade(3.3, y, c=0.035, teeth=((0.34, 0.30), (0.78, 0.17)), blade=1.2, t=0.26)]
    lock_b = held([B.lock(4.3, -0.05, 1.3, [(2, 0.05, 2.4), (3, 0.075, 0.5), (4, 0.03, 1.2)], B.round_poly(other, 0.03), P.gloss((0.008, 0.03, 0.62), 0.2, 0.7))])
    key_b = key_at(1.0)
    return dict(lock_a=lock_a, key_a=key_a, lock_b=lock_b, key_b=key_b)


def k_place(t):
    """Where each of the four things is at time t, in F3's units under the table."""
    over_a, over_b = smooth((t - OVER_A[0]) / OVER_A[1]), smooth((t - OVER_B[0]) / OVER_B[1])
    at = {}
    for name, x, y_at, z in (("lock_a", 0.0, 0.0, jolt(t, HIT_A, 0.02)),
                             ("key_a", -GAP_A * (1 - over_a), 0.0, carried(t, RISE_A, HIT_A, 0.36, 0.03, 0.13, 0.09)),
                             ("lock_b", 0.0, 0.0, jolt(t, HIT_B, 0.03)),
                             ("key_b", BACK_B + (OVER_LOCK_B[0] - BACK_B) * over_b, OVER_LOCK_B[1] * over_b, carried(t, RISE_B, HIT_B, 0.62, 0.3, 0.26, 0.2))):
        dx, dy, h = thrown(t, name)
        if name == "key_a" and t > K_LEAVE[0]:
            u = (t - K_LEAVE[0]) / K_LEAVE[1]         # straight up out of the pocket first, then off the edge of the view
            dx, h = -3.0 * u * u / K_S, h + 40.0 * u * u / K_S
        at[name] = (x + dx, y_at + dy, h + z)
    return at


def shot_k(sc, sky):
    c = lens(sc, 2.8)
    things = k_things()
    for f in range(FRAMES + 1):
        t = START + f / FPS
        for name, p in k_place(t).items():
            things[name].location = p
            things[name].keyframe_insert("location", frame=f)
        near = K_FALL[0] + K_FALL[1] / 2 < t < K_CLIMB[0] + K_CLIMB[1] / 2 or K_FALL2[0] + K_FALL2[1] / 2 < t < K_CLIMB2[0] + K_CLIMB2[1] / 2 or t > K_DIVE[0] + K_DIVE[1] / 2
        shoot(c, f, k_view(t), k_focus(t) if near else TOP_K["at"])

    def update(t):
        for name, o in things.items():
            for part in o.children:
                part.hide_render = t < LAND_K[name] - FLY_K
        if t >= K_DIVE[0]:
            sky(1 - smooth((t - K_DIVE[0]) / K_DIVE[1]))
        elif t < 300:
            sky(1 - smooth((t - K_FALL[0]) / K_FALL[1]) + smooth((t - K_CLIMB[0]) / K_CLIMB[1]))
        else:
            sky(1 - smooth((t - K_FALL2[0]) / K_FALL2[1]) + smooth((t - K_CLIMB2[0]) / K_CLIMB2[1]))
    return update


# ---------------------------------------------------------------- the CDK20 model
P_AT = on_k(-2.42, -0.02)[:2]           # where the first lock stands: it turns into the model there
P_S = 0.05                              # table units to the Angstrom
P_UP = math.radians(16)                 # how far above the table the pocket looks
P_YAW = (-20.0, 6.0)                    # degrees at the start and when it stops, the pocket stays in view
P_BACK = (312.4, 2.6)                   # the camera falls from the full view to the model
P_GROW = (312.7, 2.2)                   # the lock swells into the model
P_PLUG, P_FLY = 326.6, 0.55             # the plug lands and the turning stops
P_R = 0.2                               # radius of the plug
L_PROT = polar((P_AT[0] - 1.0, -12.3, 3.3), (P_AT[0] - 1.0, -2.7, 1.55), 50)
VOX = 0.02                              # voxel of the two distance fields, table units
VOX_SOFT = 0.05                         # voxel of their blurred copies
NEAR = 1.0                              # the sharp fields only count near the start and the end, where the surface is close to one shape
REACH = 3.0                             # how far the fields reach; the model's top is 2.8 above the lock's


def yaw_p(t):
    x = min(1.0, (t - P_BACK[0]) / (P_PLUG - P_BACK[0]))
    d = t - P_PLUG
    return math.radians(P_YAW[0] + (P_YAW[1] - P_YAW[0]) * x + (1.2 * math.exp(-d / 0.14) * math.sin(math.pi * 2 * d / 0.3) if d > 0 else 0.0))


def rays(o, on):
    for k in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(o, k, on)


def morph(src, dst, fac, mat, lo, hi):
    """The lock swells into the model. Both become distance fields; the surface is drawn where their blend crosses zero, so one shape grows out of the other with no seam. Halfway, a plain blend creases where the fields' ridges meet, so blurred copies of both are mixed in by the middle of the growth and it swells like dough. The objects are read with their modifiers and where they stand."""
    ng = bpy.data.node_groups.new("morph", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes.new, ng.links.new
    pos = N("GeometryNodeInputPosition")
    sock = lambda node, ident: next(s for s in node.inputs if s.identifier == ident)

    def blend(a, b, by):
        m = N("ShaderNodeMix")
        m.data_type = "FLOAT"
        L(by, sock(m, "Factor_Float"))
        L(a, sock(m, "A_Float"))
        L(b, sock(m, "B_Float"))
        return m.outputs[0]

    def sample(grid):
        s = N("GeometryNodeSampleGrid")
        s.data_type = "FLOAT"
        L(grid, s.inputs["Grid"])
        L(pos.outputs[0], s.inputs["Position"])
        return s.outputs[0]
    val, bump = N("ShaderNodeValue"), N("ShaderNodeValue")
    sharp, soft = [], []
    for o in (src, dst):
        oi = N("GeometryNodeObjectInfo")
        oi.transform_space = "RELATIVE"
        oi.inputs["Object"].default_value = o
        sdf, coarse = N("GeometryNodeMeshToSDFGrid"), N("GeometryNodeMeshToSDFGrid")
        for g, v in ((sdf, VOX), (coarse, VOX_SOFT)):      # the blurred copy needs no fine voxels, and on them the blur is very slow
            g.inputs["Voxel Size"].default_value = v
            g.inputs["Band Width"].default_value = int((REACH if g is coarse else NEAR) / v)
            L(oi.outputs["Geometry"], g.inputs["Mesh"])
        mean = N("GeometryNodeSDFGridMean")
        mean.inputs["Width"].default_value, mean.inputs["Iterations"].default_value = 3, 3
        L(coarse.outputs[0], mean.inputs["Grid"])
        sharp.append(sample(sdf.outputs[0]))
        soft.append(sample(mean.outputs[0]))
    field = blend(blend(*sharp, val.outputs[0]), blend(*soft, val.outputs[0]), bump.outputs[0])
    cube = N("GeometryNodeCubeGridTopology")
    cube.inputs["Bounds Min"].default_value, cube.inputs["Bounds Max"].default_value = lo, hi
    for i, a in enumerate("XYZ"):
        cube.inputs["Resolution " + a].default_value = int(round((hi[i] - lo[i]) / VOX))
    ftg = N("GeometryNodeFieldToGrid")
    ftg.grid_items.new("FLOAT", "sdf")
    L(cube.outputs[0], ftg.inputs["Topology"])
    L(field, ftg.inputs[1])
    g2m = N("GeometryNodeGridToMesh")
    L(ftg.outputs[0], g2m.inputs["Grid"])
    sm = N("GeometryNodeSetShadeSmooth")
    L(g2m.outputs[0], sm.inputs["Geometry"])
    sm_mat = N("GeometryNodeSetMaterial")
    sm_mat.inputs["Material"].default_value = mat
    L(sm.outputs[0], sm_mat.inputs["Geometry"])
    L(sm_mat.outputs[0], N("NodeGroupOutput").inputs[0])
    me = bpy.data.meshes.new("morph")
    o = bpy.data.objects.new("morph", me)
    bpy.context.scene.collection.objects.link(o)
    o.modifiers.new("morph", "NODES").node_group = ng
    o.cycles.use_motion_blur = False     # the surface is rebuilt each frame, so there is nothing to blur between
    for f in range(FRAMES + 1):
        x = fac(START + f / FPS)
        val.outputs[0].default_value, bump.outputs[0].default_value = x, math.sqrt(4 * x * (1 - x))
        val.outputs[0].keyframe_insert("default_value", frame=f)
        bump.outputs[0].keyframe_insert("default_value", frame=f)
    return o


def shot_p(sc, sky):
    c = lens(sc, 8.0)
    d = np.load(HERE + "frames/cdk20.npz")
    mouth, pocket = Vector(d["mouth"].tolist()), Vector(d["pocket"].tolist())
    front = Vector((0, -math.cos(P_UP), math.sin(P_UP)))
    q = mouth.rotation_difference(front)
    R = np.array(q.to_matrix())
    v = (d["verts"] @ R.T) * P_S
    pk = np.array(q @ pocket) * P_S
    fr = np.array(front)
    off = (v - pk) - ((v - pk) @ fr)[:, None] * fr
    out = float(((v[np.linalg.norm(off, axis=1) < 3.0 * P_S] - pk) @ fr).max())     # how far the surface is from the pocket's centre, along the way out
    clear = lambda p: float(np.linalg.norm(v - p, axis=1).min())
    rest = next(s for s in np.arange(0, 3, 0.005) if clear(pk + fr * s) >= P_R + 0.005)     # the plug stops where it touches the walls
    # it comes in along the way out, curving in from high on the right; no step of the path may touch the surface
    way = lambda u: pk + fr * (rest + 7.0 * u) + np.array([2.2, 0.0, 3.0]) * u * u
    assert all(clear(way(u)) >= P_R for u in np.arange(0, 1.01, 0.02))
    me = bpy.data.meshes.new("cdk20")
    me.from_pydata(v.tolist(), [], d["quads"].tolist())
    me.materials.append(P.gloss(P.KLEIN, 0.34, 0.7))
    o = bpy.data.objects.new("cdk20", me)
    sc.collection.objects.link(o)
    B.smooth(o)
    o.rotation_mode = "QUATERNION"
    o.location = (*P_AT, -float(v[:, 2].min()))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=P_R, segments=96, ring_count=48)
    plug = bpy.context.object
    plug.name = "plug"
    bpy.ops.object.shade_smooth()
    plug.data.materials.append(P.gloss(P.RED, 0.18, 0.7))
    plug.parent = o

    def at_mouth(t, s):
        return Vector(o.location) + Quaternion((0, 0, 1), yaw_p(t)) @ (Vector(pk.tolist()) + front * s)

    # the locks and keys stay where the last shot left them; the first key is lifting out as this one starts
    things = k_things()
    for name, p in k_place(START).items():
        things[name].location = p
    lock = things["lock_a"].children[0]
    grow = lambda t: smooth((t - P_GROW[0]) / P_GROW[1])
    if SHOT != "p":         # later shots see only the second lock and key, still lying where they were left
        rays(lock, False)
        for part in things["key_a"].children:
            part.hide_render = True
    if SHOT == "p":
        mat = P.gloss(P.KLEIN, 0.2, 0.7)
        rough = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Roughness"]
        half = 2.1      # wide enough for the turning model's corners; a field cut off at the box edge leaves a fin
        blob = morph(lock, o, grow, mat, (P_AT[0] - half, P_AT[1] - half, -0.05), (P_AT[0] + half, P_AT[1] + half, 3.6))
    track = []
    for f in range(FRAMES + 1):
        t = START + f / FPS
        o.rotation_quaternion = Quaternion((0, 0, 1), yaw_p(t))
        o.keyframe_insert("rotation_quaternion", frame=f)
        u = max(0.0, 1 - (t - P_PLUG + P_FLY) / P_FLY)
        plug.location = tuple(way(u))
        plug.keyframe_insert("location", frame=f)
        if SHOT == "p":
            things["key_a"].location = k_place(t)["key_a"]
            things["key_a"].keyframe_insert("location", frame=f)
            rough.default_value = 0.2 + 0.14 * grow(t)      # the model's paint is a little softer than the lock's
            rough.keyframe_insert("default_value", frame=f)
        x = smooth((t - P_BACK[0]) / P_BACK[1])
        view = fall(TOP_K, L_PROT, x)
        shoot(c, f, view, lerp(TOP_K["at"], (P_AT[0], P_AT[1] - 1.2, 1.6), x))
        cam = (Vector(eye_of(view)), last_q[0].to_matrix().inverted())
        p = cam[1] @ (at_mouth(t, out) - cam[0])
        k = view["mm"] / 36 / -p.z
        track.append([round(960 + 1920 * k * p.x, 1), round(540 - 1920 * k * p.y, 1)])
    if FIRST == 0 and SHOT == "p":
        json.dump(track[::6], open(HERE + "frames/p_track.json", "w"))

    def update(t):
        plug.hide_render = t < P_PLUG - P_FLY
        for part in things["key_a"].children:
            part.hide_render = SHOT != "p" or t > K_LEAVE[0] + 0.7
        if SHOT == "p":
            g = 1.0 if ONLY == "model" else grow(t)
            rays(lock, g <= 0)              # the lock, then the growing shape, then the model itself
            rays(blob, 0 < g < 1)
            blob.modifiers["morph"].show_render = 0 < g < 1     # the fields are costly; build them only while it grows
            rays(o, g >= 1)
            sky(1 - smooth((t - P_BACK[0]) / P_BACK[1]))
    return update


# ---------------------------------------------------------------- the road from the suspect to the empty cell
Q_RACK = (90.5, -2.7)                   # the 52 tubes, 13 to a row
Q_STEP = 0.62
Q_DEEP = 0.8
Q_RISE, Q_EACH = 333.8, 0.1             # the first tube starts, and the gap to the next
V_RACK = polar((90.5, -12.8, 15.4), (90.5, -2.1, 0.4), 50)
V_IN = dict(V_RACK, d=V_RACK["d"] * 0.94)
V_SIDE = polar((88.1, -16.0, 19.6), (88.1, -2.6, 0.4), 50)     # the print goes on the left
TOP_R = dict(TOP, at=(104.0, -2.7, 0.0))
TOP_L = dict(TOP, at=(113.6, -2.7, 0.0))
TOP_C = dict(TOP, at=(127.0, -2.3, 0.0))
TOP_Z = dict(TOP, at=(126.4, -2.3, 0.0), mm=1800.0)
Q_FLOW, Q_RUN = 363.0, 2.4              # the ten streams start, and how long each takes to reach the join
JOIN = 105.5
Q_CARD = (110.9, 116.3, -1.0, -4.2)     # left, right, top, bottom
Q_ROAD = -4.72
Q_LIT = 379.6
Q_GONE = 390.0                          # the model is in the frame before this and gone from the one at it; the page fades between them
SEEN = (3, 17, 26, 34)


def cell_at(i):
    return TOP_C["at"][0] + (i % 9 - 4) * 0.95, TOP_C["at"][1] - (i // 9 - 2) * 0.84


def box(l, r, top, bot, rad=0.06):
    return B.round_poly([(l, top), (r, top), (r, bot), (l, bot)], rad)


def q_view(t):
    if t < 333.2:
        return fall(L_PROT, V_RACK, smooth((t - 330.0) / 3.0))     # the model now stands ten units further back
    if t < 350.4:
        return fall(V_RACK, V_IN, smooth((t - 333.2) / 6.0))
    if t < 358.6:
        return fall(V_IN, V_SIDE, smooth((t - 350.4) / 1.5))
    if t < 363.0:
        return fall(V_SIDE, TOP_R, smooth((t - 358.6) / 2.0))
    if t < 382.6:
        return dict(TOP_R, at=lerp(TOP_R["at"], TOP_L["at"], smooth((t - 367.6) / 2.4)))
    if t < 398.0:
        return dict(TOP_L, at=lerp(TOP_L["at"], TOP_C["at"], smooth((t - 382.6) / 2.0)))
    return fall(TOP_C, TOP_Z, smooth((t - 398.0) / 3.0))


class Vial:
    """A sample tube standing on the rack. The red is cut flat at a level that can rise."""

    def __init__(self, xy, rise, glass, red, cap):
        self.rise, self.was = rise, None
        root = empty("vial")
        root.location = (*xy, 0.05)
        o = lathe([(0, 0.0), (0.16, 0.03), (0.2, 0.12), (0.2, 1.1), (0, 1.1)], glass, "vial", root, 48)
        o.visible_shadow = False
        lathe([(0, 1.1), (0.205, 1.1), (0.205, 1.22), (0, 1.22)], cap, "vial_cap", root, 48)
        self.dose = lathe([(0, 0.015), (0.14, 0.04), (0.17, 0.12), (0.17, 1.0), (0, 1.0)], red, "vial_dose", root, 48)
        self.dose.visible_diffuse = False
        self.v = np.zeros(len(self.dose.data.vertices) * 3, np.float32)
        self.dose.data.vertices.foreach_get("co", self.v)

    def update(self, t):
        level = 0.24 + 0.68 * (smooth((t - self.rise) / 0.5) if self.rise else 0.0)
        if level != self.was:
            v = self.v.copy()
            v[2::3] = np.minimum(v[2::3], level)
            self.dose.data.vertices.foreach_set("co", v)
            self.dose.data.update()
            self.was = level


def shot_q(sc, sky):
    shot_p(sc, sky)             # the model is where the last piece left it
    c = sc.camera
    model = bpy.data.objects["cdk20"]
    cover = [model, bpy.data.objects["plug"]]
    glass, red, cap = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03)), P.gloss(P.KLEIN, 0.25, 0.6)
    tray = gk.surface((0.74, 0.725, 0.67), 0.7, 0.1)
    x0, y0 = Q_RACK[0] - 6 * Q_STEP, Q_RACK[1] + 1.5 * Q_DEEP
    B.extrude([box(x0 - 0.42, x0 + 12 * Q_STEP + 0.42, y0 + 0.42, y0 - 3 * Q_DEEP - 0.42, 0.14)], 0.05, 0.02, name="tray", mat=tray)
    tubes = []
    for i in range(52):     # the far row first: the count reads like lines of text
        tubes.append(Vial((x0 + (i % 13) * Q_STEP, y0 - (i // 13) * Q_DEEP), Q_RISE + i * Q_EACH if i < 36 else 0, glass, red, cap))

    # ten streams into one
    wet = []
    blue = B.fluid(P.KLEIN, (0.02, 0.08, 0.7))

    def stream(pts, r, name):
        g = pipe(pts, r, B.clear_glass(), name)
        g.visible_shadow, g.visible_diffuse = False, False
        w = pipe(pts, r * 0.62, blue, name + "_wet")
        w.visible_diffuse = False
        w.data.bevel_factor_mapping_end = "SPLINE"
        w.data.bevel_factor_end = 0.0
        wet.append(w)
    for i in range(10):
        y = -0.25 - i * 0.544
        stream([((98.8 + (JOIN - 98.8) * u) * K, -(y + (-2.7 - y) * smooth(u * 1.1 - 0.1)) * K) for u in np.linspace(0, 1, 160)], 4.5, "stream")
    stream([(JOIN * K - 8, 2.7 * K), (Q_CARD[0] * K + 6, 2.7 * K)], 9.0, "main")

    # the list: 20 rows, and the paper names only one of them
    l, r, top, bot = Q_CARD
    B.extrude([box(l, r, top, bot)], 0.03, 0.01, name="card", mat=gk.surface((0.93, 0.925, 0.89), 0.6, 0.15))
    bar = gk.surface((0.70, 0.685, 0.63), 0.7, 0.1)
    for i in range(1, 20):
        bx, by = l + 0.2 + (i // 10) * 2.6, top - 0.34 - (i % 10) * 0.28
        B.extrude([box(bx, bx + 2.4, by + 0.05, by - 0.05, 0.05)], 0.008, 0.003, z=0.03, name="row", mat=bar)

    # the road, small, with its first station about to fill
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    bx = [111.6 + i * 0.92 for i in range(6)]
    g = pipe([(bx[0] * K, -Q_ROAD * K), (bx[5] * K, -Q_ROAD * K)], 3.5, B.clear_glass(), "road")
    g.visible_shadow, g.visible_diffuse = False, False
    for x in bx:
        B.bulb(x, Q_ROAD, W.SURFACE_Z / K, 0.2, ink, None, width=0.016)
    first = Bulb(bx[0], red, Q_ROAD, None, 0.186)

    # the grid: most cells empty, a few holding a shape someone has measured
    rim, red_rim = gk.surface((0.60, 0.585, 0.54), 0.7, 0.1), gk.surface(P.RED, 0.5, 0.2)
    shape = P.gloss(P.KLEIN, 0.34, 0.7)
    for i in range(45):
        cx, cy = cell_at(i)
        outer, inner = box(cx - 0.435, cx + 0.435, cy + 0.35, cy - 0.35, 0.07), box(cx - 0.42, cx + 0.42, cy + 0.335, cy - 0.335, 0.06)
        B.extrude([outer, inner[::-1]], 0.016, 0.004, name="cell", mat=red_rim if i == 22 else rim)
        if i in SEEN:
            B.extrude([B.blob(cx, cy, 0.17 + 0.01 * (i % 5), [(2, 0.08, i * 1.3), (3, 0.07, i * 2.1), (5, 0.03, i * 0.7)])], 0.2, 0.07, name="shape", mat=shape)

    keyhole = empty("keyhole")
    # the empty keyhole: the hollow of CDK20's own pocket, cut through the predicted model (pocket_outline.py), dashed because no one had measured it
    cx, cy = cell_at(22)
    hole = np.array(json.load(open(HERE + "frames/pocket_outline.json"))["points"]) * 0.28 + (cx, cy)
    hole = np.r_[hole, hole[:1]]
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(hole, axis=0), axis=1))]
    n = max(1, round(run[-1] / 0.06))
    for i in range(n):          # a dash and a gap, the dashes a little over half
        s = np.linspace(i, i + 0.6, 8) * run[-1] / n
        dash = np.c_[np.interp(s, run, hole[:, 0]), np.interp(s, run, hole[:, 1])]
        pipe([(x * K, -y * K) for x, y in dash], 1.3, ink, "keyhole").parent = keyhole

    # the same model, small, with its pocket looking up
    me = model.data
    q = Quaternion((1, 0, 0), -(math.pi / 2 - P_UP))
    pts = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", pts)
    pts = pts.reshape(-1, 3) @ np.array(q.to_matrix()).T
    d = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(d["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    pk = np.array(q @ (q0 @ Vector(d["pocket"].tolist()))) * P_S
    s = 0.31 / float(np.linalg.norm(pts[:, :2] - pk[:2], axis=1).max())
    small = bpy.data.objects.new("cdk20_small", me)
    sc.collection.objects.link(small)
    small.rotation_mode = "QUATERNION"
    small.rotation_quaternion, small.scale = q, (s, s, s)
    small.location = (cx - pk[0] * s, cy - pk[1] * s, -float(pts[:, 2].min()) * s + 0.01)

    for f in range(FRAMES + 1):
        t = START + f / FPS
        v = q_view(t)
        shoot(c, f, v, lerp((P_AT[0], P_AT[1] - 1.2, 1.6), v["at"], smooth((t - START) / 3.0)))

    def update(t):
        for o in cover:
            o.hide_render = t > 333.0
        small.hide_render = t >= Q_GONE
        for tube_ in tubes:
            tube_.update(t)
        for i, w in enumerate(wet[:10]):
            w.data.bevel_factor_end = smooth((t - Q_FLOW - 0.11 * i) / Q_RUN)
        wet[10].data.bevel_factor_end = smooth((t - Q_FLOW - 2.8) / 3.8)
        first.update(bx[0] - 0.2 + 0.4 * smooth((t - Q_LIT) / 1.0))
        sky(smooth((q_view(t)["el"] - 0.75) / 0.7))
    return update


# ---------------------------------------------------------------- S4 idea stills, not in the film yet
X_FOLD = {0: 0.0, 1: 0.55, 2: 1.0, 3: 1.0}     # frame: how far the chain has folded; frame 3 has the tail cut off


def shot_x(sc, sky):
    """Stills for the S4 proposal (W2, 4-03, 4-05): in the empty cell where S3 ends, a chain of 346 beads, one per residue of the AlphaFold model, lies coiled like a dropped necklace, lifts and folds into the model's real shape. Beads at 70 or more confidence are Klein blue, below 70 blood red, so the floppy tail shows. The folding path is drawn: AlphaFold does not simulate folding. Frame 3 has residues 303-346 cut away and lying on the table. Run: blender -b -P bl_inserts.py -- x <out dir> 0 3 32 1"""
    shot_q(sc, sky)
    sc.render.use_motion_blur = False       # stills: each frame is a separate pose and camera
    for name in ("cdk20_small", "cdk20", "plug"):
        bpy.data.objects[name].hide_render = True
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]

    cx, cy = cell_at(22)
    lines = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
    ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in lines])
    conf = np.array([float(l[60:66]) for l in lines])
    ca -= ca[:302].mean(0)
    # small enough that the whole necklace coils inside the cell: a spiral of radius 0.3 with rows 2.3 beads apart holds pi 0.3^2 / gap of chain
    s = math.sqrt(math.pi * 0.3 ** 2 / (2.3 * 0.42 * 3.8 * 3.8 * (len(ca) - 1)))
    folded = ca * s + (cx, cy, 0.0)
    folded[:, 2] += 0.03 - folded[:, 2].min()
    r = 3.8 * s * 0.42
    # the necklace: an even spiral on the cell floor, inside out, beads one spacing apart
    gap = 2.3 * r
    th, coil = 0.0, []
    for i in range(len(ca)):
        rad = 0.05 + gap * th / (2 * math.pi)
        coil.append((cx + rad * math.cos(th), cy + rad * math.sin(th), r))
        th += 3.8 * s / max(rad, 0.05)
    coil = np.array(coil)
    blue, red = P.gloss(P.KLEIN, 0.22, 0.7), P.gloss(P.RED, 0.22, 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16)
    proto = bpy.context.object
    bpy.ops.object.shade_smooth()
    me = {}
    for name, m in (("blue", blue), ("red", red)):
        me[name] = proto.data.copy()
        me[name].materials.clear()
        me[name].materials.append(m)
    bpy.data.objects.remove(proto)
    beads = []
    for i in range(len(ca)):
        o = bpy.data.objects.new("bead", me["blue" if conf[i] >= 70 else "red"])
        sc.collection.objects.link(o)
        beads.append(o)
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()

    def update(t):
        f = round((t - START) * FPS)
        k = X_FOLD[f]
        lift = 0.22 * math.sin(math.pi * k)
        for i, o in enumerate(beads):
            u = smooth((k - 0.3 * i / len(beads)) / 0.7) if 0 < k < 1 else k
            p = coil[i] + (folded[i] - coil[i]) * u
            p[2] += lift * math.sin(math.pi * u)
            if f == 3 and i >= 302:      # the tail, snipped, lies in a loose line on the table to the right
                j = i - 302
                p = np.array((cx + 0.95 + 0.2 * math.sin(j * 0.16), cy - 0.27 + j * 0.0125, r))     # in the next cell, clear of the rims
            o.location = tuple(p)
        for o in dashes:            # the necklace lies where the dashes are; they show again once it lifts
            o.hide_render = f == 0
        v = polar((cx + 0.6, cy - 2.4, 1.5 + 0.3 * k), (cx + (0.3 if f == 3 else 0.0), cy, 0.15 + 0.12 * k), 70 if f < 3 else 58)
        shoot(c, f, v, v["at"])
        sky(0.3)
    return update


def shot_y(sc, sky):
    """W2 motion test for the S4 proposal, 412-437 s: S3's empty cell, seen from where S3 ends. An ink bead chain is lowered into it and coils up, is lifted like a necklace and folds into the AlphaFold model in the air (path from w2_path.py, no two beads ever overlap), then sets down on the lock and recolours by confidence, blue at 70 or more, red below. The darkness at the start is laid on afterwards. Run: blender -b -P bl_inserts.py -- y <out dir> [first] [last] [samples] [size]"""
    global START
    START = 330.0
    shot_q(sc, sky)             # the table, the grid and the keyhole as S3 left them
    START = 412.0
    for name in ("cdk20_small", "cdk20", "plug"):
        bpy.data.objects[name].hide_render = True
    d = np.load(HERE + "frames/w2_path.npz")
    pos, conf, r = d["pos"], d["conf"], float(d["r"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16)
    proto = bpy.context.object
    bpy.ops.object.shade_smooth()
    me = {}
    for name, m in (("ink", P.gloss((0.012, 0.012, 0.014), 0.25, 0.7)), ("blue", P.gloss(P.KLEIN, 0.22, 0.7)), ("red", P.gloss(P.RED, 0.22, 0.7))):
        me[name] = proto.data.copy()
        me[name].materials.clear()
        me[name].materials.append(m)
    bpy.data.objects.remove(proto)
    beads = []
    for i in range(len(conf)):
        o = bpy.data.objects.new("bead", me["ink"])
        sc.collection.objects.link(o)
        beads.append(o)
    lock = 412.0 + 19.5
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    end = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    for f in range(FRAMES):
        t = START + f / FPS
        v = fall(TOP_Z, end, smooth((t - 414.5) / 5.0))
        v["az"] += math.radians(14) * smooth((t - 420.0) / 17.0)       # a slow turn round the model while it folds and after
        shoot(c, f, v, lerp(TOP_Z["at"], (127.0, -2.3, 0.22), smooth((t - 414.5) / 5.0)))
        for i, o in enumerate(beads):
            o.location = tuple(pos[f, i].tolist())
            o.keyframe_insert("location", frame=f)
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]
    bpy.context.view_layer.update()
    mid = np.array([tuple(o.matrix_world @ Vector(np.mean(o.bound_box, 0).tolist())) for o in dashes])

    def update(t):
        q = pos[min(FRAMES - 1, max(0, round((t - START) * FPS)))]
        low = q[q[:, 2] < 3 * r]
        for o, m in zip(dashes, mid):       # a dash is hidden only while a bead lies on it: S3 leaves them showing, the coil covers them, the lift uncovers them
            o.hide_render = bool(len(low)) and float(np.min(np.hypot(low[:, 0] - m[0], low[:, 1] - m[1]))) < 1.6 * r
        for i, o in enumerate(beads):
            o.data = me["ink"] if t < lock + 1.2 * i / len(beads) else me["blue" if conf[i] >= 70 else "red"]
        sky(0.2)
    return update


def shot_z(sc, sky):
    """Tail cut test for the S4 proposal (ideas 2 and 3), straight after shot y, 437-449 s: the coloured bead model holds, the camera pushes in over the red tail lying across the pocket, the tail is snipped off at 302/303, lifted out, swung over the empty cell to the right and paid out into it (path from tail_path.py), and the camera pulls back to show both cells. Run: blender -b -P bl_inserts.py -- z <out dir> [first] [last] [samples] [size]"""
    global START
    START = 330.0
    shot_q(sc, sky)
    START = 437.0
    for name in ("cdk20_small", "cdk20", "plug"):
        bpy.data.objects[name].hide_render = True
    d = np.load(HERE + "frames/tail_path.npz")
    pos, conf, r = d["pos"], d["conf"], float(d["r"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16)
    proto = bpy.context.object
    bpy.ops.object.shade_smooth()
    me = {}
    for name, m in (("blue", P.gloss(P.KLEIN, 0.22, 0.7)), ("red", P.gloss(P.RED, 0.22, 0.7))):
        me[name] = proto.data.copy()
        me[name].materials.clear()
        me[name].materials.append(m)
    bpy.data.objects.remove(proto)
    beads = []
    for i in range(len(conf)):
        o = bpy.data.objects.new("bead", me["blue" if conf[i] >= 70 else "red"])
        sc.collection.objects.link(o)
        beads.append(o)
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]
    bpy.context.view_layer.update()
    mid = np.array([tuple(o.matrix_world @ Vector(np.mean(o.bound_box, 0).tolist())) for o in dashes])
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)        # where shot y ends
    held["az"] += math.radians(14)
    close = dict(held, at=tuple(pos[0, 302:].mean(0).tolist()), d=1.0, el=math.radians(58))
    wide = dict(held, at=(127.5, -2.42, 0.22), d=2.9, el=math.radians(40))      # both cells, and room above for the tail on its way over

    def view(a, b, x):
        return dict(a, at=lerp(a["at"], b["at"], x), d=a["d"] * (b["d"] / a["d"]) ** x, el=a["el"] + (b["el"] - a["el"]) * x, az=a["az"] + (b["az"] - a["az"]) * x)

    for f in range(FRAMES):
        t = f / FPS
        v = view(held, close, smooth((t - 0.5) / 4.5)) if t < 6.3 else view(close, wide, smooth((t - 6.3) / 4.0))      # in over the tail, then back out as it is lifted
        shoot(c, f, v, v["at"])
        for i, o in enumerate(beads[302:], 302):
            o.location = tuple(pos[f, i].tolist())
            o.keyframe_insert("location", frame=f)
    for i, o in enumerate(beads[:302]):
        o.location = tuple(pos[0, i].tolist())

    def update(t):
        q = pos[min(FRAMES - 1, max(0, round((t - START) * FPS)))]
        low = q[q[:, 2] < 3 * r]
        for o, m in zip(dashes, mid):       # as in shot y: a dash is hidden only while a bead lies on it
            o.hide_render = bool(len(low)) and float(np.min(np.hypot(low[:, 0] - m[0], low[:, 1] - m[1]))) < 1.6 * r
        sky(0.2)
    return update


def tube3d(pts, r, mat, name):
    """A smooth 3D tube through pts, in the object's own units."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r, 6
    cu.use_fill_caps = True
    s = cu.splines.new("NURBS")
    s.points.add(len(pts) - 1)
    for q, p in zip(s.points, pts):
        q.co = (*p, 1)
    s.order_u, s.use_endpoint_u = 4, True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o


def see_through(rgb, alpha):
    m = P.gloss(rgb, 0.4, 0.3)
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Alpha"].default_value = alpha
    return m


def shot_v(sc, sky):
    """Stills for the new S4 opening (the storyboard W2_storyboard_1): instead of a bead chain, the AI keeps guessing CDK20's shape. 0 the empty cell where S3 ends; 1 the sequence, a line of letters, walks into the cell; 2 guesses, see-through and bent, over the keyhole; 3 most of it holds still in Klein blue (residues 1-302), the tail still a blur of guesses; 4 pushed in: the tail in red, never settling, lies across the keyhole; 5 pulled back: the tail is cut off and lies coiled in the next cell (the coil from tail_path.py). The guesses are drawn; the blue shape and the red tail are the AlphaFold DB v6 model. Notes are laid on afterwards. Run: blender -b -P bl_inserts.py -- v <out dir> 0 5 64 1"""
    global START
    START = 330.0
    shot_q(sc, sky)             # the table, the grid and the keyhole as S3 left them
    START = 412.0
    sc.render.use_motion_blur = False
    small = bpy.data.objects["cdk20_small"]
    for name in ("cdk20_small", "cdk20", "plug"):
        bpy.data.objects[name].hide_render = True
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]
    cx, cy = cell_at(22)
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]

    # the model's own frame: the same turn and scale as S3's small model, so the shapes sit where it sat
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    heavy = lambda last, first=1: np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H" and first <= int(l[22:26]) <= last])
    centre = heavy(346).mean(0)
    local = lambda x: (np.asarray(x) - centre) @ R.T * P_S          # angstrom, PDB frame -> the small model's mesh
    core_npz = np.load(HERE + "frames/cdk20_core.npz")
    core_v = local(core_npz["verts"] + heavy(302).mean(0))
    ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[12:16].strip() == "CA"])
    tail = local(ca[301:])          # 302-346: from the last kept residue out to the end
    tail_npz = np.load(HERE + "frames/cdk20_tail.npz")
    tail_v = local(tail_npz["verts"] + heavy(346, 303).mean(0))     # the tail's own surface, 303-346: Arg305 reaches into the pocket, so it plugs the mouth

    def place(o):
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion, o.scale, o.location = small.rotation_quaternion, small.scale, small.location
        return o

    def mesh(v, faces, mat, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(v.tolist(), [], faces.tolist())
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        sc.collection.objects.link(o)
        B.smooth(o)
        return place(o)

    def bend(v, seed, amp):
        """A smooth random bend of the shape: one of the AI's guesses."""
        g = np.random.default_rng(seed)
        out = v.copy()
        for _ in range(3):
            k, ph = g.uniform(0.08, 0.2, 3), g.uniform(0, 6.3, 3)
            out += amp * np.sin(v @ k[:, None] + ph)
        return out

    core = mesh(core_v, core_npz["quads"], P.gloss(P.KLEIN, 0.34, 0.7), "core")
    ghosts = []
    for seed, g, turn, dx in ((3, 0.22, -28, -0.07), (8, 0.4, 4, 0.0), (21, 0.58, 32, 0.07)):     # three guesses, each its own grey and turned a little, so they read apart
        o = mesh(bend(local(full["verts"] + centre), seed, 7.0 * P_S), full["quads"], see_through((g, g, g + 0.03), 0.3), "guess")
        o.rotation_quaternion = Quaternion((0, 0, 1), math.radians(turn)) @ o.rotation_quaternion
        o.location = (o.location[0] + dx, o.location[1], o.location[2])
        ghosts.append(o)

    # the tail's guesses: swung round where it leaves the model, the swings that keep it furthest from the kept part's surface
    def turn_by(axis, ang):
        return np.array(Quaternion(Vector(axis).normalized(), math.radians(ang)).to_matrix())

    def near(p):
        return min(float(np.sqrt(((core_v - q) ** 2).sum(1)).min()) for q in p)
    g = np.random.default_rng(1)
    tries = [turn_by(g.normal(size=3), g.uniform(18, 40)) for _ in range(400)]
    clear = [near((tail[5:] - tail[0]) @ M.T + tail[0]) for M in tries]        # the first few beyond the cut swing very little, so only the rest are tested
    picks = [tries[i] for i in np.argsort(clear)[::-1][:4]]
    print("tail guesses clear of the kept part by %.1f A or more" % (sorted(clear)[-4] / P_S))
    red = P.gloss(P.RED, 0.22, 0.7)
    tail_main = mesh(tail_v, tail_npz["quads"], red, "tail")
    tail_grey = [mesh((tail_v - tail[0]) @ M.T + tail[0], tail_npz["quads"], see_through((0.3, 0.3, 0.33), 0.45), "tail_guess") for M in picks]
    tail_red = [mesh((tail_v - tail[0]) @ M.T + tail[0], tail_npz["quads"], see_through(P.RED, 0.3), "tail_guess") for M in picks]
    cut = mesh(tail_v, tail_npz["quads"], red, "tail_cut")         # set down in the next cell, lying on its flattest side
    bpy.context.view_layer.update()
    w = np.array([tuple(cut.matrix_world @ v.co) for v in cut.data.vertices])
    flat = np.linalg.eigh(np.cov((w - w.mean(0)).T))[1][:, 0]       # the direction it is thinnest in goes straight up
    lay = Vector(flat.tolist()).rotation_difference(Vector((0, 0, 1)))
    turned = (w - w.mean(0)) @ np.array(lay.to_matrix()).T
    cut.rotation_quaternion = lay @ cut.rotation_quaternion
    spot = Vector((cx + 0.95, cy, 0.002 - float(turned[:, 2].min())))
    cut.location = spot + lay @ (cut.location - Vector(w.mean(0).tolist()))

    # the sequence: CDK20's first 20 letters, set in the film's serif, lying on the table and walking into the cell
    AA = dict(ALA="A", ARG="R", ASN="N", ASP="D", CYS="C", GLN="Q", GLU="E", GLY="G", HIS="H", ILE="I", LEU="L", LYS="K", MET="M", PHE="F", PRO="P", SER="S", THR="T", TRP="W", TYR="Y", VAL="V")
    seq = "".join(AA[l[17:20]] for l in pdb if l[12:16].strip() == "CA")
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    letters = []

    def path(u):
        return (cx - 1.3 + 1.3 * u, cy - 0.2 + 0.2 * u)
    for i in range(20):         # standing up like type blocks, facing the camera, so they read
        u = i / 19
        cu = bpy.data.curves.new("letter", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = seq[i], font, 0.12, 0.012
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        o = bpy.data.objects.new("letter", cu)
        sc.collection.objects.link(o)
        cu.materials.append(ink)
        o.location = (*path(u), 0.06)
        o.rotation_euler = (math.pi / 2, 0, 0)
        letters.append(o)

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)        # where the bead test ended: the cell from the front, a little above
    bpy.context.view_layer.update()
    mw = small.matrix_world
    mid = mw @ Vector((np.asarray(full["pocket"]) @ R.T * P_S).tolist())         # the pocket
    out = (mw.to_3x3() @ Vector((R @ np.asarray(full["mouth"])).tolist())).normalized()       # and its way out
    views = [held, held, held, dict(held, el=math.radians(50)),
             dict(at=tuple(mid), az=math.atan2(out.x, -out.y), el=math.radians(68), d=1.0, mm=60.0),     # from above, on the side the pocket opens to
             dict(held, at=(127.5, -2.42, 0.22), d=2.9, el=math.radians(40))]
    for f, v in enumerate(views):
        shoot(c, f, v, v["at"])
    show = {0: [], 1: letters, 2: ghosts, 3: [core] + tail_grey, 4: [core, tail_main] + tail_red, 5: [core, cut]}
    every = letters + ghosts + [core, tail_main, cut] + tail_grey + tail_red

    def update(t):
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        for o in every:
            o.hide_render = o not in show[f]
        for o in dashes:            # the dashed keyhole shows until the solid model covers it
            o.hide_render = f >= 3
        sky(0.2)
    return update


def shot_u(sc, sky):
    """Motion test of the new S4 opening, W2 to 4-05 (the stills are shot v), 412-454.5 s with 4-01 and 4-02 cut short: S3's empty cell; CDK20's sequence, a line of letters, walks into it; the AI's guesses swell up where the letters go in, three see-through shapes that keep bending; they agree, and most of it holds still in Klein blue (residues 1-302); the tail turns red and keeps swinging (three swings from u_path.py, each tested clear of the kept part); the camera pushes in over the pocket; the tail comes to rest across it; it is cut at 302/303, draws tight onto its backbone, and is drawn out along its own path, low over the model and into the next cell, where it winds into a coil (u_path_2.py, every frame checked). The guesses are drawn; the blue shape and the red tail are the AlphaFold DB v6 model. Notes and the source line are laid on afterwards. Run: blender -b -P bl_inserts.py -- u <out dir> [first] [last] [samples] [size] [step]"""
    global START
    START = 330.0
    shot_q(sc, sky)             # the table, the grid and the keyhole as S3 left them
    START = 412.0
    sc.render.use_motion_blur = False           # the shapes are rebuilt every frame
    small = bpy.data.objects["cdk20_small"]
    for name in ("cdk20_small", "cdk20", "plug"):
        bpy.data.objects[name].hide_render = True
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]
    cx, cy = cell_at(22)
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    heavy = lambda last, first=1: np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H" and first <= int(l[22:26]) <= last])
    centre = heavy(346).mean(0)
    local = lambda x: (np.asarray(x) - centre) @ R.T * P_S          # angstrom, PDB frame -> the small model's mesh
    core_npz, tail_npz = np.load(HERE + "frames/cdk20_core.npz"), np.load(HERE + "frames/cdk20_tail.npz")
    core_A = core_npz["verts"] + heavy(302).mean(0)          # both surfaces in angstrom, PDB frame
    tail_A = tail_npz["verts"] + heavy(346, 303).mean(0)
    ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[12:16].strip() == "CA"])
    ut = np.load(HERE + "frames/u_tail_2.npz")        # version 2: the tail crawls low into the next cell (version 1, u_tail.npz, hung it up out of frame)
    pivot, picks = ut["pivot"], [Matrix(M.tolist()).to_quaternion() for M in ut["picks"]]
    T_CUT = float(ut["t0"])

    def place(o):
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion, o.scale, o.location = small.rotation_quaternion, small.scale, small.location
        return o

    def mesh(v, faces, name):
        m = P.gloss((0.4, 0.4, 0.43), 0.34, 0.7)
        me = bpy.data.meshes.new(name)
        me.from_pydata(local(v).tolist(), [], faces.tolist())
        me.materials.append(m)
        o = bpy.data.objects.new(name, me)
        sc.collection.objects.link(o)
        B.smooth(o)
        return place(o)

    def paint(o, rgb, alpha):
        b = next(n for n in o.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Alpha"].default_value = alpha
        o.hide_render = alpha < 0.01

    def set_verts(o, v):
        o.data.vertices.foreach_set("co", local(v).ravel())
        o.data.update()

    # three guesses, each a core and a tail that bend together; guess 1 becomes the answer
    G = [dict(seed=3, grey=0.22, turn=-18, dx=-0.05, ph=0.0), dict(seed=8, grey=0.4, turn=0, dx=0.0, ph=0.37), dict(seed=21, grey=0.58, turn=18, dx=0.05, ph=0.71)]
    for j, gd in enumerate(G):
        r_ = np.random.default_rng(gd["seed"])
        gd["k"] = r_.normal(size=(3, 3)) * 0.07                # three waves, 40-100 A long, across the 60 A model
        gd["phase"] = r_.uniform(0, 6.3, (3, 3))
        gd["w"] = r_.uniform(0.9, 1.6, 3)                      # each keeps changing its mind at its own pace
        gd["core"], gd["tail"] = mesh(core_A, core_npz["quads"], "guess_core"), mesh(tail_A, tail_npz["quads"], "guess_tail")

    def bent(v, gd, t, amp):
        if amp <= 0:
            return v
        out = v.copy()
        for i in range(3):
            out = out + amp * np.sin(v @ gd["k"][i][:, None] + gd["phase"][i] + gd["w"][i] * t) / 3 ** 0.5
        return out

    def swung(v, t, ph, amp):
        """The tail never settles: from the real pose out to one of the tested swings and back, over and over."""
        if amp <= 0:
            return v
        x = t / 1.4 + ph
        q = Quaternion().slerp(picks[int(x) % len(picks)], amp * (1 - math.cos(2 * math.pi * (x % 1))) / 2)
        return pivot + (v - pivot) @ np.array(q.to_matrix()).T

    # the cut: the tail's surface draws tight onto its backbone, then the backbone tube takes over
    line = ca[302:]
    a_, b_ = line[:-1], line[1:]
    foot = np.zeros_like(tail_A)
    best = np.full(len(tail_A), np.inf)
    for p, q in zip(a_, b_):
        s = np.clip(((tail_A - p) @ (q - p)) / ((q - p) @ (q - p)), 0, 1)
        f_ = p + s[:, None] * (q - p)
        d = np.linalg.norm(tail_A - f_, axis=1)
        take = d < best
        best[take], foot[take] = d[take], f_[take]
    off = tail_A - foot
    tight = foot + off / np.maximum(np.linalg.norm(off, axis=1), 1e-6)[:, None] * 1.6
    tube = tube3d(ut["pos"][0].astype(float), float(ut["tr"]), P.gloss(P.RED, 0.34, 0.7), "tail_cut")

    # the sequence: CDK20's first 20 letters walk in from the left, standing like type blocks, and go into the cell
    AA = dict(ALA="A", ARG="R", ASN="N", ASP="D", CYS="C", GLN="Q", GLU="E", GLY="G", HIS="H", ILE="I", LEU="L", LYS="K", MET="M", PHE="F", PRO="P", SER="S", THR="T", TRP="W", TYR="Y", VAL="V")
    seq = "".join(AA[l[17:20]] for l in pdb if l[12:16].strip() == "CA")
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    letters = []
    for i in range(20):
        cu = bpy.data.curves.new("letter", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = seq[i], font, 0.17, 0.017
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        o = bpy.data.objects.new("letter", cu)
        sc.collection.objects.link(o)
        cu.materials.append(ink)
        o.rotation_euler = (math.pi / 2, 0, 0)
        letters.append(o)

    # the camera: down from S3's last view to the cell, a slow drift while it guesses, in over the pocket for 4-03, back out for the cut
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    bpy.context.view_layer.update()
    mw = small.matrix_world
    mid = mw @ Vector((np.asarray(full["pocket"]) @ R.T * P_S).tolist())
    out = (mw.to_3x3() @ Vector((R @ np.asarray(full["mouth"])).tolist())).normalized()
    drift = dict(held, az=held["az"] + math.radians(8))
    az_in = math.atan2(out.x, -out.y)
    az_in += round((drift["az"] - az_in) / (2 * math.pi)) * 2 * math.pi
    close = dict(at=tuple(mid), az=az_in, el=math.radians(64), d=1.6, mm=60.0)       # the whole pocket side in frame, the tail across it
    wide = dict(held, at=(127.5, -2.42, 0.3), d=3.3, el=math.radians(36))

    def view(a, b, x):
        return dict(a, at=lerp(a["at"], b["at"], x), d=a["d"] * (b["d"] / a["d"]) ** x, el=a["el"] + (b["el"] - a["el"]) * x, az=a["az"] + (b["az"] - a["az"]) * x, mm=a["mm"] + (b["mm"] - a["mm"]) * x)

    for f in range(FRAMES):
        t = f / FPS
        if t < 8.0:
            x = smooth((t - 2.5) / 5.0)
            shoot(c, f, fall(TOP_Z, held, x), lerp(TOP_Z["at"], held["at"], x))
            continue
        if t < 26.5:
            v = view(held, drift, smooth((t - 8.0) / 18.5))
        elif t < 34.0:
            v = view(drift, close, smooth((t - 26.5) / 5.0))
        else:
            v = view(close, wide, smooth((t - 34.0) / 4.5))
        shoot(c, f, v, v["at"])

    grey_of = lambda gd: (gd["grey"], gd["grey"], gd["grey"] + 0.03)

    def update(t):
        t -= START
        grow = smooth((t - 8.6) / 3.5)
        settle = smooth((t - 17.5) / 2.5)
        amp = 7.0 * (1 - 0.6 * smooth((t - 12.0) / 5.5)) * (1 - settle)
        red = smooth((t - 19.0) / 1.5)
        wob = smooth((t - 18.5) / 2.0) * (1 - smooth((t - 31.0) / 1.5))
        for i, o in enumerate(letters):
            p = (t - 3.0) * 0.19 - i * 0.055          # slow enough to read a few as they pass
            o.hide_render = not 0 <= p < 1
            o.location = (cx - 3.5 + 3.25 * p, cy - 0.25 + 0.2 * p, 0.085)
            o.scale = (1 - smooth((p - 0.88) / 0.12),) * 3
        for j, gd in enumerate(G):
            for o in (gd["core"], gd["tail"]):
                k = 0.55 + 0.45 * grow
                o.rotation_quaternion = Quaternion((0, 0, 1), math.radians(gd["turn"]) * (1 - settle)) @ small.rotation_quaternion
                o.scale = tuple(k * s for s in small.scale)
                o.location = (small.location[0] + gd["dx"] * (1 - settle), small.location[1], small.location[2] + (1 - k) * 0.25)
            main = j == 1
            if grow > 0:
                set_verts(gd["core"], bent(core_A, gd, t, amp))
            core_rgb = lerp(grey_of(gd), P.KLEIN, settle) if main else grey_of(gd)
            paint(gd["core"], core_rgb, 0.55 * grow + 0.45 * settle if main else 0.12 * grow * (1 - settle))      # the leading guess reads through the others
            v = swung(bent(tail_A, gd, t, amp), t, gd["ph"], wob)
            if main and t >= T_CUT:
                v = tail_A + (tight - tail_A) * smooth((t - T_CUT - 0.1) / 0.8)
            if grow > 0:
                set_verts(gd["tail"], v)
            tail_rgb = lerp(grey_of(gd), P.RED, red)
            if main:
                paint(gd["tail"], tail_rgb, 0 if t >= T_CUT + 0.95 else 0.55 * grow + 0.45 * red)
            else:
                paint(gd["tail"], tail_rgb, (0.12 + 0.18 * red) * grow * (1 - smooth((t - 31.0) / 1.5)))
        tube.hide_render = t < T_CUT + 0.95
        if not tube.hide_render:
            pos = ut["pos"][min(len(ut["pos"]) - 1, round((t - T_CUT) * FPS))]
            for q, p in zip(tube.data.splines[0].points, pos):
                q.co = (*p.tolist(), 1)
        for i, o in enumerate(dashes):          # the dashed keyhole shows under the guesses and goes dash by dash as the answer turns solid
            o.hide_render = settle > 0.2 + 0.6 * i / len(dashes)
        sky(0.2)
    return update


def shot_t(sc, sky):
    """Stills for the S4 opening as a culture tank, the director's idea of 11-04 (W2 to Harder Better Faster Stronger): 0 a sci-fi culture tank stands in S3's empty cell, a question mark hangs in its liquid; 1 CDK20's sequence, a line of letters, goes in at the port on its foot; 2 a guess forms in the liquid, one more on every beat; 3 it settles: most of it Klein blue (residues 1-302), the tail red; 4 the liquid drains through the foot and the glass lifts away; 5 open: CDK20 stands in the cell as W2 leaves it for 4-01. Built on shot v's shapes; the guesses are drawn, the blue shape and the red tail are the AlphaFold DB v6 model. Notes are laid on afterwards. Run: blender -b -P bl_inserts.py -- t <out dir> 0 5 64 1"""
    shot_v(sc, sky)
    cx, cy = cell_at(22)
    pick = lambda prefix: [o for o in bpy.data.objects if o.name.split(".")[0] == prefix]
    letters, ghosts, tail_g = pick("letter"), pick("guess"), pick("tail_guess")
    core, tail = bpy.data.objects["core"], bpy.data.objects["tail"]
    dashes = [o for o in bpy.data.objects if o.parent and o.parent.name == "keyhole"]

    def alpha(o, a):
        b = next(n for n in o.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Alpha"].default_value = a
    alpha(ghosts[1], 0.85)          # the guess on this beat, nearly solid; the last one fading behind it
    alpha(ghosts[0], 0.15)

    metal = P.gloss((0.55, 0.57, 0.61), 0.28, 0.2)
    next(n for n in metal.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = 1.0

    def liquid():
        """Pale cyan, clear like the film's glass: nothing bends, a little gloss where it faces away."""
        m, nt, out = gk._mat("liquid")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        tr.inputs[0].default_value = (0.80, 0.94, 0.97, 1)
        g = nt.nodes.new("ShaderNodeBsdfGlossy")
        g.inputs["Roughness"].default_value = 0.05
        fr = nt.nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = 1.33
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(fr.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(g.outputs[0], mx.inputs[2])
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        pure = nt.nodes.new("ShaderNodeBsdfTransparent")
        pure.inputs[0].default_value = (0.9, 0.97, 0.98, 1)
        mx2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mx2.inputs[0])
        nt.links.new(mx.outputs[0], mx2.inputs[1])
        nt.links.new(pure.outputs[0], mx2.inputs[2])
        nt.links.new(mx2.outputs[0], out.inputs["Surface"])
        return m

    def cyl(name, r, depth, z, mat, caps=True):
        bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=r, depth=depth, location=(cx, cy, z), end_fill_type="NGON" if caps else "NOTHING")
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        return o

    # the tank stands on a glass floor laid across the cell's raised border (0.016 high): the cell is too narrow for a round foot inside it, and the keyhole shows through the floor
    R_GL, TOP, FLOOR = 0.385, 0.8, 0.017 + 0.012
    floor_ = cyl("tank_floor", 0.40, 0.012, 0.017 + 0.006, B.clear_glass())
    bpy.ops.mesh.primitive_torus_add(major_radius=0.392, minor_radius=0.016, major_segments=160, minor_segments=24, location=(cx, cy, FLOOR + 0.016))
    foot = bpy.context.object
    foot.data.materials.append(metal)
    bpy.ops.object.shade_smooth()
    glass = cyl("tank_glass", R_GL, TOP - FLOOR, (TOP + FLOOR) / 2, B.clear_glass(), caps=False)
    glass.visible_shadow = False
    cap = cyl("tank_cap", 0.41, 0.05, TOP + 0.025, metal)
    pipe = cyl("tank_pipe", 0.05, 0.3, TOP + 0.2, metal)        # the feed: the sequence goes in at its open top
    bpy.ops.mesh.primitive_torus_add(major_radius=0.392, minor_radius=0.022, major_segments=160, minor_segments=24, location=(cx, cy, TOP - 0.01))
    lip = bpy.context.object
    lip.data.materials.append(metal)
    bpy.ops.object.shade_smooth()
    lid = [glass, cap, pipe, lip]
    juice = cyl("tank_liquid", R_GL - 0.006, 0.6, FLOOR + 0.002 + 0.3, liquid())
    juice.visible_shadow = False
    g = np.random.default_rng(7)
    bubbles = []
    white = P.gloss((0.95, 0.97, 0.98), 0.1, 0.3)
    for _ in range(36):
        a, r = g.uniform(0, 2 * math.pi), 0.34 * math.sqrt(g.uniform(0.05, 1))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=float(g.uniform(0.006, 0.016)), segments=16, ring_count=8, location=(cx + r * math.cos(a), cy + r * math.sin(a), float(g.uniform(0.06, 0.58))))
        o = bpy.context.object
        o.data.materials.append(white)
        bpy.ops.object.shade_smooth()
        bubbles.append(o)
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    cu = bpy.data.curves.new("ask", "FONT")
    cu.body, cu.font, cu.size, cu.extrude = "?", font, 0.34, 0.03
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    ask = bpy.data.objects.new("ask", cu)
    sc.collection.objects.link(ask)
    cu.materials.append(gk.surface((0.012, 0.012, 0.014), 0.3))
    for i, o in enumerate(letters):         # the sequence streams through the air into the feed's open top, clear of the table and its raised borders
        u = i / (len(letters) - 1)
        o.location = (cx - 1.5 + 1.42 * u, cy - 0.05 * u, 0.75 + 0.36 * u + 0.12 * math.sin(math.pi * u))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    near = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.42), 60)
    near["d"] *= 1.3
    ask.location, ask.rotation_euler = (cx, cy, 0.4), (math.pi / 2, 0, near["az"])     # faces the lens
    cu.size = 0.4
    views = [near, dict(near, at=(126.7, -2.3, 0.6), d=near["d"] * 1.15), near, near, dict(near, d=near["d"] * 1.2, at=(127.0, -2.3, 0.6)), polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)]
    for f, v in enumerate(views):
        shoot(c, f, v, (cx, cy, 0.3))
    UP = {2: 0.12, 3: 0.12, 4: FLOOR - 0.01, 5: FLOOR - 0.01}         # it hangs in the liquid while it forms, then rests on the glass floor
    rest = {o.name: tuple(o.location) for o in [core, tail] + ghosts}

    def update(t):
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        show = {0: [ask], 1: [ask] + letters, 2: ghosts[:2], 3: [core, tail], 4: [core, tail], 5: [core, tail]}[f]
        for o in letters + ghosts + tail_g + [core, tail, bpy.data.objects["tail_cut"], ask]:
            o.hide_render = o not in show
        for o in [core, tail] + ghosts:
            x, y, z = rest[o.name]
            o.location = (x, y, z + UP.get(f, 0.0))
        juice.hide_render = f >= 4
        for o in bubbles:
            o.hide_render = f >= 4
        for o in lid:
            o.hide_render = f == 5
            o.location.z = {glass: (TOP + FLOOR) / 2, cap: TOP + 0.025, pipe: TOP + 0.2, lip: TOP - 0.01}[o] + (0.45 if f == 4 else 0.0)
        for o in dashes:
            o.hide_render = f >= 3
        sky(0.2)
    return update


def shot_r(sc, sky):
    """Stills for the culture tank, version 2 (the director's notes of 11-04 13:05): the tank is filled with mist, not liquid, and stands in a dark machine ring with a cyan light strip and a slot-machine reel on its front. 0 a question mark hangs in the mist, the reel shows "?"; 1 the question mark is sucked up the pipe as if by a vacuum, the reel starts to spin; 2 in thick mist CDK20 forms in a frenzy, shaking hard, the reel a blur; 3 the mist thins and the shape turns solid, blue and red, still trembling, the reel lands on a small CDK20; 4 the glass lifts and the steam bursts out with a bang; 5 open, the last steam drifting off. Built on shot t. The guesses, the mist and the machine are drawn; the blue shape and the red tail are the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- r <out dir> 0 5 64 1"""
    base_update = shot_t(sc, sky)
    cx, cy = cell_at(22)
    ob = bpy.data.objects
    for name in ("tank_liquid", "tank_floor"):
        ob[name].hide_render = name == "tank_liquid"
    for o in ob:
        if o.name.startswith("Sphere") or (o.name.startswith("Torus") and abs(o.location.z - 0.045) < 0.01):
            o.hide_render = True             # no bubbles in the mist; the foot ring gives way to the machine ring
    ask, core, tail = ob["ask"], ob["core"], ob["tail"]
    ghosts = [o for o in ob if o.name.split(".")[0] == "guess"]
    lid = [ob["tank_glass"], ob["tank_cap"], ob["tank_pipe"]] + [o for o in ob if o.name.startswith("Torus") and o.location.z > 0.5]
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5

    def emit(rgb, power):
        m, nt, out = gk._mat("glow")
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value, e.inputs[1].default_value = (*rgb, 1), power
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        return m

    def mist_mat(name, rgb, scale):
        """Steam: scattering volume broken up by noise, so it reads as wisps, not fog."""
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (*rgb, 1)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = 6
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs[1].default_value, ramp.inputs[2].default_value = 0.42, 0.75
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(nz.outputs[0], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], vol.inputs["Density"])
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        return m, mul.inputs[1]

    def solid(name, verts_r, depth, z, mat):
        bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=verts_r, depth=depth, location=(cx, cy, z))
        o = bpy.context.object
        o.name = name
        o.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        return o

    # the machine ring: rests on the cell's raised border like the glass floor, a hole in the middle so the keyhole still shows
    dark = P.gloss((0.06, 0.065, 0.075), 0.3, 0.5)
    next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = 0.6
    ring = solid("machine_ring", 0.45, 0.08, 0.017 + 0.04, dark)
    hole = solid("ring_hole", 0.389, 0.2, 0.06, dark)
    cut = ring.modifiers.new("hole", "BOOLEAN")
    cut.operation, cut.object = "DIFFERENCE", hole
    hole.hide_render = hole.hide_viewport = True
    ob["tank_floor"].scale = (0.389 / 0.40, 0.389 / 0.40, 1)
    cyan = emit((0.25, 0.9, 1.0), 9.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.452, minor_radius=0.005, major_segments=160, minor_segments=12, location=(cx, cy, 0.072))
    bpy.context.object.data.materials.append(cyan)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.392, minor_radius=0.004, major_segments=160, minor_segments=12, location=(cx, cy, 0.79))
    strip_top = bpy.context.object
    strip_top.data.materials.append(cyan)
    lid.append(strip_top)

    # the reel: a drum behind a window in a box on the ring's front, facing the lens
    c = sc.camera
    near = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.42), 60)
    near["d"] *= 1.3
    front = Vector((math.sin(near["az"]), -math.cos(near["az"]), 0))
    side = Vector((math.cos(near["az"]), math.sin(near["az"]), 0))
    spot = Vector((cx, cy, 0)) + front * 0.47
    yaw = Quaternion((0, 0, 1), near["az"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(spot.x, spot.y, 0.085))
    box = bpy.context.object
    box.rotation_mode = "QUATERNION"
    box.rotation_quaternion = yaw
    box.scale = (0.26, 0.08, 0.13)
    box.data.materials.append(dark)
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(spot - front * 0.03 + Vector((0, 0, 0.09))))
    win = bpy.context.object
    win.rotation_mode = "QUATERNION"
    win.rotation_quaternion = yaw
    win.scale = (0.18, 0.08, 0.07)
    cut = box.modifiers.new("window", "BOOLEAN")
    cut.operation, cut.object = "DIFFERENCE", win
    win.hide_render = win.hide_viewport = True
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(spot + Vector((0, 0, 0.09))))
    edge_ = bpy.context.object          # a glowing frame round the window
    edge_.rotation_mode = "QUATERNION"
    edge_.rotation_quaternion = yaw
    edge_.scale = (0.19, 0.075, 0.08)
    edge_.data.materials.append(cyan)
    inner = edge_.modifiers.new("frame", "BOOLEAN")
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(spot + Vector((0, 0, 0.09))))
    edge_cut = bpy.context.object
    edge_cut.rotation_mode = "QUATERNION"
    edge_cut.rotation_quaternion = yaw
    edge_cut.scale = (0.175, 0.2, 0.065)
    inner.operation, inner.object = "DIFFERENCE", edge_cut
    edge_cut.hide_render = edge_cut.hide_viewport = True
    drum = empty("drum")
    drum.location = tuple(spot + Vector((0, 0, 0.09)))
    drum.rotation_mode = "QUATERNION"
    drum.rotation_quaternion = yaw
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.05, depth=0.16, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    barrel = bpy.context.object
    barrel.data.materials.append(P.gloss((0.9, 0.92, 0.93), 0.4, 0.1))
    barrel.parent = drum
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    ink = emit((0.02, 0.02, 0.025), 1.0)
    faces = []
    for k in range(8):           # round the drum: question marks, and one small CDK20
        a = 2 * math.pi * k / 8
        holder = empty("face")
        holder.parent = drum
        holder.rotation_euler = (a, 0, 0)
        if k == 0:
            me = core.data.copy()
            o = bpy.data.objects.new("reel_cdk20", me)
            sc.collection.objects.link(o)
            o.scale = (0.016,) * 3
            o.location = (0, -0.052, 0)
            o.rotation_euler = (math.pi / 2, 0, 0)
        else:
            cu = bpy.data.curves.new("q", "FONT")
            cu.body, cu.font, cu.size, cu.extrude = "?", font, 0.045, 0.002
            cu.align_x, cu.align_y = "CENTER", "CENTER"
            cu.materials.append(ink)
            o = bpy.data.objects.new("reel_q", cu)
            sc.collection.objects.link(o)
            o.location = (0, -0.051, 0)
            o.rotation_euler = (math.pi / 2, 0, 0)
        o.parent = holder
        faces.append(o)
    # the mist inside the tank, and the burst of steam when it opens
    mist = solid("mist", 0.378, 0.74, 0.029 + 0.37, None)
    mist.data.materials.clear()
    mm, mist_density = mist_mat("mist", (0.86, 0.97, 1.0), 9.0)
    mist.data.materials.append(mm)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24, location=(cx, cy, 0.3))
    puff = bpy.context.object
    puff.name = "steam_puff"
    pm, puff_density = mist_mat("steam", (0.95, 0.98, 1.0), 4.0)
    puff.data.materials.append(pm)

    # the camera holds still between stills; only the things that shake, spin or rush are blurred
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f, v in enumerate([near, near, near, near, dict(near, d=near["d"] * 1.2, at=(127.0, -2.3, 0.6)), polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.3), 60)]):
        for s in (-0.3, 0.0, 0.3):          # the same view on both sides of each still, so the camera never blurs
            shoot(c, f + s, v, (cx, cy, 0.3))
    g = np.random.default_rng(11)

    def shake(o, f, amp, base):
        """A hard tremble inside the shutter: five places in a quarter of a frame each way."""
        o.animation_data_clear()
        for s in (-0.25, -0.12, 0.0, 0.12, 0.25):
            o.location = tuple(np.asarray(base) + g.normal(0, amp, 3) * (1, 1, 0.5))
            o.keyframe_insert("location", frame=f + s)
    rest = {o.name: tuple(o.location) for o in [core, tail] + ghosts}
    turns = {1: 3.0, 2: 9.0}         # reel turns in one shutter

    def update(t):
        base_update(t)              # shot t's show and hide, the lid's place
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        ob["tank_liquid"].hide_render = True
        for o in ob:
            if o.name.startswith("Sphere"):
                o.hide_render = True
        for o in [x for x in ob if x.name.split(".")[0] == "letter"]:
            o.hide_render = True                 # no letters flying in: the sequence is not shown here
        ask.hide_render = f > 1
        ask.animation_data_clear()
        if f == 1:                  # sucked up the pipe, stretched thin
            ask.scale = (0.35, 2.6, 1)
            for s, z in ((-0.25, 0.48), (0.25, 0.74)):
                ask.location = (cx, cy, z)
                ask.keyframe_insert("location", frame=f + s)
        else:
            ask.scale = (1, 1, 1)
            ask.location = (cx, cy, 0.4)
        for o in [core, tail] + ghosts:
            x, y, z = rest[o.name]
            up = {2: 0.12, 3: 0.12}.get(f, 0.019)
            if f in (2, 3) and not o.hide_render:
                shake(o, f, 0.022 if f == 2 else 0.006, (x, y, z + up))
            else:
                o.animation_data_clear()
                o.location = (x, y, z + up)
        drum.animation_data_clear()
        a0 = {0: 2 * math.pi * 1 / 8, 3: 0.0, 4: 0.0, 5: 0.0}.get(f, 0.0)
        if f in turns:
            for s in (-0.25, 0.25):
                drum.rotation_quaternion = yaw @ Quaternion((1, 0, 0), a0 + turns[f] * 2 * math.pi * (s + 0.25))
                drum.keyframe_insert("rotation_quaternion", frame=f + s)
        else:
            drum.rotation_quaternion = yaw @ Quaternion((1, 0, 0), -a0)
        mist.hide_render = f >= 4
        mist_density.default_value = {0: 14.0, 1: 22.0, 2: 40.0, 3: 6.0}.get(f, 0.0)
        puff.hide_render = f < 4
        puff.scale = (0.75, 0.75, 0.32) if f == 4 else (1.15, 1.15, 0.55)
        puff.location = (cx, cy, 0.22 if f == 4 else 0.45)
        puff_density.default_value = 30.0 if f == 4 else 5.0
        strip_top.hide_render = f == 5
        strip_top.location.z = 0.79 + (0.45 if f == 4 else 0.0)
    return update


def shot_s(sc, sky):
    """Stills for the culture tank, version 3 (the director's notes of 11-04 14:05): a finer machine, and a real slot machine with four reels that land on AlphaFold's own confidence (pLDDT, the mean over each stretch of CDK20 in AlphaFold DB v6): 87, 92 and 95 in blue, the tail 303-346 at 47 in red. 0 a question mark hangs in the mist, the reels show "??"; 1 the question mark is sucked up the pipe, the lever is pulled, the reels start; 2 in mist CDK20 forms in a frenzy, shaking, the reels a blur; 3 the mist thins, the shape is solid, the reels land; 4 the glass lifts and steam bursts out; 5 open. Built on shot t (shot r is version 2). The machine, the mist and the guesses are drawn; the blue shape, the red tail and the four numbers come from the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- s <out dir> 0 5 64 1"""
    base_update = shot_t(sc, sky)
    cx, cy = cell_at(22)
    C = Vector((cx, cy, 0))
    ob = bpy.data.objects
    hide_always = [ob["tank_liquid"]] + [o for o in ob if o.name.startswith("Sphere") or o.name.split(".")[0] == "letter" or (o.name.startswith("Torus") and abs(o.location.z - 0.045) < 0.01)]
    ask, core, tail = ob["ask"], ob["core"], ob["tail"]
    ghosts = [o for o in ob if o.name.split(".")[0] == "guess"]
    glass, cap, pipe = ob["tank_glass"], ob["tank_cap"], ob["tank_pipe"]
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
    conf = np.array([float(l[60:66]) for l in pdb])
    res = np.array([int(l[22:26]) for l in pdb])
    STRETCH = [(1, 100), (101, 200), (201, 302), (303, 346)]
    SCORE = [int(round(conf[(res >= a) & (res <= b)].mean())) for a, b in STRETCH]
    print("reels land on", SCORE)

    def mat(rgb, rough, metal=0.0, coat=0.2):
        m = P.gloss(rgb, rough, coat)
        next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = metal
        return m

    def emit(rgb, power):
        m, nt, out = gk._mat("glow")
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value, e.inputs[1].default_value = (*rgb, 1), power
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        return m

    steel, dark, rubber = mat((0.66, 0.68, 0.72), 0.22, 1.0), mat((0.07, 0.075, 0.085), 0.32, 0.5, 0.5), mat((0.03, 0.03, 0.035), 0.55)
    cyan, amber = emit((0.25, 0.9, 1.0), 9.0), emit((1.0, 0.55, 0.12), 8.0)
    label = emit((0.78, 0.86, 0.9), 2.5)

    def finish(o, m, bevel=0.0):
        if m is not None:
            o.data.materials.clear()
            o.data.materials.append(m)
        if bevel:
            b = o.modifiers.new("bevel", "BEVEL")
            b.width, b.segments, b.limit_method = bevel, 3, "ANGLE"
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        except Exception:
            bpy.ops.object.shade_smooth()
        o.select_set(False)
        return o

    def cyl(r, depth, at, m, bevel=0.0, rot=None, n=96):
        bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=depth, location=tuple(at))
        o = bpy.context.object
        if rot is not None:
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = rot
        return finish(o, m, bevel)

    def ring_(R, r, z, m, at=None):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=160, minor_segments=16, location=tuple(at) if at is not None else (cx, cy, z))
        return finish(bpy.context.object, m)

    def cut(o, cutter):
        b = o.modifiers.new("cut", "BOOLEAN")
        b.operation, b.object = "DIFFERENCE", cutter
        cutter.hide_render = cutter.hide_viewport = True

    near = polar((127.55, -4.55, 1.75), (127.0, -2.36, 0.38), 60)
    near["d"] *= 1.45
    yaw = Quaternion((0, 0, 1), near["az"])
    front = yaw @ Vector((0, -1, 0))
    side = yaw @ Vector((1, 0, 0))
    around = lambda a, rad, z: C + (yaw @ Quaternion((0, 0, 1), a)) @ Vector((0, -rad, 0)) + Vector((0, 0, z))     # a = 0 faces the lens

    # the machine ring under the tank, resting on the cell's raised border; its hole keeps the keyhole in view through the glass floor
    ring = cyl(0.45, 0.08, (cx, cy, 0.057), dark, 0.006, n=160)
    cut(ring, cyl(0.389, 0.3, (cx, cy, 0.06), None, n=160))
    ob["tank_floor"].scale = (0.389 / 0.40, 0.389 / 0.40, 1)
    ring_(0.452, 0.0045, 0.057, cyan)
    ring_(0.447, 0.007, 0.097, steel)
    for k in range(12):
        cyl(0.011, 0.01, around(2 * math.pi * (k + 0.5) / 12, 0.42, 0.102), steel, 0.002, n=24)
    before = set(o.name for o in ob)
    # four struts from the ring to the cap, clear of the glass, none in front of the window; they belong to the lid and lift with it
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = around(a, 0.405, (0.097 + 0.78) / 2)
        cyl(0.011, 0.78 - 0.097, p, steel, 0.002, n=32)
        cyl(0.018, 0.02, around(a, 0.405, 0.107), steel, 0.003, n=32)
        cyl(0.018, 0.02, around(a, 0.405, 0.77), steel, 0.003, n=32)
    # the cap in tiers, bolted, with collars round the top of the glass, status lights, and a valve on the pipe
    finish(cap, steel, 0.006)
    cyl(0.31, 0.03, (cx, cy, 0.82), dark, 0.005, n=160)
    cyl(0.16, 0.025, (cx, cy, 0.845), steel, 0.004, n=96)
    ring_(0.392, 0.006, 0.766, steel)
    ring_(0.392, 0.006, 0.748, steel)
    for k in range(16):
        cyl(0.009, 0.01, around(2 * math.pi * (k + 0.5) / 16, 0.37, 0.81), steel, 0.002, n=20)
    lights = []
    for k, m in enumerate((cyan, cyan, amber)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, segments=16, ring_count=8, location=tuple(around(math.radians(-14 + 14 * k), 0.395, 0.79)))
        lights.append(finish(bpy.context.object, m))
    finish(pipe, steel, 0.003)
    for z in (0.88, 1.0):
        ring_(0.058, 0.008, z, steel)
    wheel = ring_(0.1, 0.008, 0.94, dark)
    for k in range(4):
        cyl(0.005, 0.2, (cx, cy, 0.94), steel, rot=Quaternion((0, 0, 1), k * math.pi / 4) @ Quaternion((0, 1, 0), math.pi / 2), n=12)
    lid = [glass, cap, pipe] + [o for o in ob if o.name not in before]        # everything on the cap lifts with it, lights and struts too; shot t moves the glass, the cap, the pipe and the lip
    lid_z = {o.name: o.location.z for o in lid}
    # two hoses from the cap down the back to the ring
    for a in (math.radians(140), math.radians(-140)):
        pts = [around(a, 0.30, 0.83), around(a, 0.47, 0.88), around(a, 0.53, 0.6), around(a, 0.52, 0.3), around(a, 0.44, 0.13), around(a, 0.43, 0.1)]
        h = tube3d([tuple(p) for p in pts], 0.014, rubber, "hose")

    # the slot machine on the ring's front: four reels behind four windows, a lever on the right
    W_, H_, D_ = 0.66, 0.2, 0.1
    mid = C + front * 0.505 + Vector((0, 0, 0.022 + H_ / 2))
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(mid))
    house = bpy.context.object
    house.rotation_mode = "QUATERNION"
    house.rotation_quaternion = yaw
    house.scale = (W_, D_, H_)
    finish(house, dark, 0.008)
    xs = [-0.24, -0.08, 0.08, 0.24]
    zc = mid.z + 0.005
    for x in xs:
        bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(mid + side * x + front * 0.045 + Vector((0, 0, 0.005))))
        w = bpy.context.object
        w.rotation_mode = "QUATERNION"
        w.rotation_quaternion = yaw
        w.scale = (0.11, 0.04, 0.09)
        cut(house, w)
        bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(mid + side * x - front * 0.005 + Vector((0, 0, 0.005))))
        hollow = bpy.context.object          # room inside for the reel, behind the front wall
        hollow.rotation_mode = "QUATERNION"
        hollow.rotation_quaternion = yaw
        hollow.scale = (0.115, 0.085, 0.13)
        cut(house, hollow)
        for dz in (-0.048, 0.048):          # a glowing line over and under each window
            bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(mid + side * x + front * (D_ / 2 + 0.001) + Vector((0, 0, 0.005 + dz))))
            g_ = bpy.context.object
            g_.rotation_mode = "QUATERNION"
            g_.rotation_quaternion = yaw
            g_.scale = (0.112, 0.002, 0.004)
            g_.data.materials.append(cyan)
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    sans = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InterTight.ttf")

    def text(body, size, at, m, f=sans, extrude=0.0005):
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = body, f, size, extrude
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.materials.append(m)
        o = bpy.data.objects.new("txt", cu)
        sc.collection.objects.link(o)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = yaw @ Quaternion((1, 0, 0), math.pi / 2)
        o.location = tuple(at)
        return o
    face_front = front * (D_ / 2 + 0.0015)
    text("AlphaFold confidence (pLDDT)", 0.019, mid + face_front + Vector((0, 0, 0.078)), label)
    for x, (a, b) in zip(xs, STRETCH):
        text("%d–%d" % (a, b), 0.016, mid + face_front + side * x + Vector((0, 0, -0.07)), label)
    drum_white = mat((0.93, 0.93, 0.9), 0.35)
    ink_m = mat((0.02, 0.02, 0.025), 0.4)
    blue_m, red_m = mat(P.KLEIN, 0.3), mat(P.RED, 0.3)
    g = np.random.default_rng(3)
    drums, N = [], 10
    for j, x in enumerate(xs):
        d = empty("drum")
        d.location = tuple(mid + side * x + Vector((0, 0, 0.005)))        # radius 0.045: inside the hollow, 5 mm behind the front wall
        d.rotation_quaternion = yaw
        barrel = cyl(0.045, 0.1, (0, 0, 0), drum_white, rot=Quaternion((0, 1, 0), math.pi / 2), n=64)
        barrel.parent = d
        for k in range(N):
            h = empty("face")
            h.parent = d
            h.rotation_quaternion = Quaternion((1, 0, 0), 2 * math.pi * k / N)
            body = str(SCORE[j]) if k == 0 else ("??" if k == N // 2 else str(int(g.integers(10, 99))))
            m = (blue_m if SCORE[j] >= 70 else red_m) if k == 0 else ink_m
            cu = bpy.data.curves.new("num", "FONT")
            cu.body, cu.font, cu.size, cu.extrude = body, font, 0.04, 0.0015
            cu.align_x, cu.align_y = "CENTER", "CENTER"
            cu.materials.append(m)
            o = bpy.data.objects.new("num", cu)
            sc.collection.objects.link(o)
            o.parent = h
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
            o.location = (0, -0.0462, 0)
        drums.append(d)
    lever = empty("lever")
    lever.location = tuple(mid + side * (W_ / 2 + 0.012) + Vector((0, 0, 0.0)))
    cyl(0.02, 0.024, (0, 0, 0), steel, rot=Quaternion((0, 1, 0), math.pi / 2), n=32).parent = lever
    rod = cyl(0.007, 0.2, (0.012, 0, 0.1), steel, n=16)
    rod.parent = lever
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.024, segments=24, ring_count=12, location=(0.012, 0, 0.2))
    knob = finish(bpy.context.object, mat(P.RED, 0.2, 0.0, 0.6))
    knob.parent = lever

    # mist inside, and the burst of steam when it opens
    def mist_mat(name, rgb, scale):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (*rgb, 1)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = 6
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs[1].default_value, ramp.inputs[2].default_value = 0.45, 0.78
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(nz.outputs[0], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], vol.inputs["Density"])
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        return m, mul.inputs[1]
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.375, depth=0.72, location=(cx, cy, 0.031 + 0.36))
    mist = bpy.context.object
    mm, mist_d = mist_mat("mist", (0.86, 0.97, 1.0), 9.0)
    mist.data.materials.append(mm)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24, location=(cx, cy, 0.2))
    puff = bpy.context.object
    puff.name = "steam_puff"
    pm, puff_d = mist_mat("steam", (0.95, 0.98, 1.0), 5.0)
    puff.data.materials.append(pm)

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f, v in enumerate([near, near, near, near, dict(near, d=near["d"] * 1.15, at=(127.0, -2.36, 0.55)), dict(near, at=(127.0, -2.36, 0.3), d=near["d"] * 0.95)]):
        for s in (-0.3, 0.0, 0.3):
            shoot(c, f + s, v, (cx, cy, 0.3))
    rng = np.random.default_rng(11)

    def shake(o, f, amp, base):
        o.animation_data_clear()
        for s in (-0.25, -0.12, 0.0, 0.12, 0.25):
            o.location = tuple(np.asarray(base) + rng.normal(0, amp, 3) * (1, 1, 0.5))
            o.keyframe_insert("location", frame=f + s)
    rest = {o.name: tuple(o.location) for o in [core, tail] + ghosts}
    hoses = [o for o in ob if o.name.split(".")[0] == "hose"]

    def update(t):
        base_update(t)
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        for o in hide_always:
            o.hide_render = True
        ask.hide_render = f > 1
        ask.animation_data_clear()
        if f == 1:                  # sucked up the pipe, stretched thin
            ask.scale = (0.35, 2.6, 1)
            for s, z in ((-0.25, 0.5), (0.25, 0.74)):
                ask.location = (cx, cy, z)
                ask.keyframe_insert("location", frame=f + s)
        else:
            ask.scale = (1, 1, 1)
            ask.location = (cx, cy, 0.4)
        for o in [core, tail] + ghosts:
            x, y, z = rest[o.name]
            up = {2: 0.12, 3: 0.12}.get(f, 0.019)
            if f in (2, 3) and not o.hide_render:
                shake(o, f, 0.02 if f == 2 else 0.005, (x, y, z + up))
            else:
                o.animation_data_clear()
                o.location = (x, y, z + up)
        for j, d in enumerate(drums):
            d.animation_data_clear()
            if f in (1, 2):         # spinning: each reel its own speed, blurred in the shutter
                turns = (1.5 if f == 1 else 5.0) * (1 + 0.25 * j)
                for s in (-0.25, 0.25):
                    d.rotation_quaternion = yaw @ Quaternion((1, 0, 0), 2 * math.pi * turns * (s + 0.25))
                    d.keyframe_insert("rotation_quaternion", frame=f + s)
            else:
                k = N // 2 if f == 0 else 0
                d.rotation_quaternion = yaw @ Quaternion((1, 0, 0), -2 * math.pi * k / N)
        lever.rotation_quaternion = yaw @ Quaternion((1, 0, 0), math.radians(-75 if f == 1 else 0))
        mist.hide_render = f >= 4
        mist_d.default_value = {0: 5.0, 1: 6.0, 2: 4.0, 3: 1.2}.get(f, 0.0)        # thin enough at 2 for the forming shape to show through
        puff.hide_render = f < 4
        puff.scale = (0.55, 0.55, 0.2) if f == 4 else (0.75, 0.75, 0.3)
        puff.location = (cx, cy, 0.2 if f == 4 else 0.32)
        puff_d.default_value = 14.0 if f == 4 else 2.0
        for o in lid:
            if o in (glass, cap, pipe):
                continue
            o.hide_render = f == 5
            o.location.z = lid_z[o.name] + (0.45 if f == 4 else 0.0)
        for o in hoses:
            o.hide_render = f >= 4
        for o in lights:
            o.hide_render = f == 5
        sky(0.2)
    return update


def shot_n(sc, sky):
    """Four looks for the culture tank, after the director's note of 11-04 14:15 (the top of shot s looks like a pot: no design sense, not sci-fi, not cool). One still each, CDK20 settled in thin mist, the four reels landed on AlphaFold's confidence: 0 white hardware, 1 dark gunmetal with fins and cables, 2 a glass capsule in floating light rings, 3 a hexagonal pod. Taller and slimmer than shot s, built from turned profiles with rounded edges, the slot machine a console leaning out of the base. The machine and the mist are drawn; the blue shape, the red tail and the four numbers come from the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- n <out dir> 0 3 64 1"""
    base_update = shot_v(sc, sky)
    ob = bpy.data.objects
    core, tail = ob["core"], ob["tail"]
    every = [o for o in ob if o.name.split(".")[0] in ("letter", "guess", "tail_guess", "tail_cut")]
    C = Vector((127.03, -2.35, 0.0))          # the centre of the smallest circle round the model
    UP = 0.25
    for o in (core, tail):
        o.location.z += UP
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
    conf = np.array([float(l[60:66]) for l in pdb])
    res = np.array([int(l[22:26]) for l in pdb])
    STRETCH = [(1, 100), (101, 200), (201, 302), (303, 346)]
    SCORE = [int(round(conf[(res >= a) & (res <= b)].mean())) for a, b in STRETCH]
    print("reels land on", SCORE)

    hero = dict(at=(C.x, C.y, 0.53), az=math.atan2(0.55, 2.19), el=math.radians(13), d=3.0, mm=40.0)       # low and close: the tank stands tall
    yaw = Quaternion((0, 0, 1), hero["az"])
    front = yaw @ Vector((0, -1, 0))
    around = lambda a, rad, z: C + (yaw @ Quaternion((0, 0, 1), a)) @ Vector((0, -rad, 0)) + Vector((0, 0, z))     # a = 0 faces the lens

    def mat(rgb, rough, metal=0.0, coat=0.3):
        m = P.gloss(rgb, rough, coat)
        next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = metal
        return m

    def emit(rgb, power):
        m, nt, out = gk._mat("glow")
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value, e.inputs[1].default_value = (*rgb, 1), power
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        return m

    def glass_m(rgb):
        m = B.clear_glass()
        next(n for n in m.node_tree.nodes if n.type == "BSDF_TRANSPARENT").inputs[0].default_value = (*rgb, 1)
        return m

    def sharp(o, angle=32):
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
        except Exception:
            bpy.ops.object.shade_smooth()
        o.select_set(False)
        return o

    def rnd(pts, b=0.005):
        """Rounds every corner of a profile with a three-point fillet, so edges catch a highlight."""
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            p, q, r = (np.array(x, float) for x in (pts[i - 1], pts[i], pts[i + 1]))
            a, c = p - q, r - q
            la, lc = np.linalg.norm(a), np.linalg.norm(c)
            s = min(b, la / 2.5, lc / 2.5)
            u, v = a / la * s, c / lc * s
            out += [tuple(q + u), tuple(q + (u + v) * 0.3), tuple(q + v)]
        return out + [pts[-1]]

    def turn(profile, m, b=0.005, n=160, rot=0.0, z0=None):
        o = lathe(rnd(profile, b) if b else profile, m, "tank_part", n=n)
        o.location = tuple(C)
        o.rotation_euler = (0, 0, rot)
        return sharp(o)

    def loop(outer, inner, m, b=0.003, n=160, rot=0.0):
        """A thick-walled shell: up the outside, back down the inside, closed."""
        return turn(list(outer) + list(inner) + [outer[0]], m, b, n, rot)

    def ring_(R, r, z, m):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=160, minor_segments=12, location=(C.x, C.y, z))
        o = bpy.context.object
        o.data.materials.append(m)
        bpy.ops.object.shade_smooth()
        return o

    def block(size, at, rot, m, bevel=0.003, parent=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(at))
        o = bpy.context.object
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
        o.scale = size
        o.data.materials.append(m)
        if bevel:
            bv = o.modifiers.new("bevel", "BEVEL")
            bv.width, bv.segments, bv.limit_method = bevel, 3, "ANGLE"
        o.parent = parent
        return sharp(o)

    def radial(a, rad, z, size, m, bevel=0.002):
        """A block standing at angle a round the tank, its depth pointing out from the axis."""
        return block(size, around(a, rad, z), yaw @ Quaternion((0, 0, 1), a), m, bevel)

    cutters = []

    def cut(o, cutter):
        b = o.modifiers.new("cut", "BOOLEAN")
        b.operation, b.object = "DIFFERENCE", cutter
        cutter.hide_render = cutter.hide_viewport = True
        cutters.append(cutter)

    def mist_in(r, z0, z1, density):
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=z1 - z0, location=(C.x, C.y, (z0 + z1) / 2))
        o = bpy.context.object
        m = bpy.data.materials.new("mist")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (0.86, 0.97, 1.0, 1)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 7.0, 6
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value, mr.inputs[2].default_value = 0.45, 0.8
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation, mul.inputs[1].default_value = "MULTIPLY", density
        nt.links.new(nz.outputs[0], mr.inputs[0])
        nt.links.new(mr.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], vol.inputs["Density"])
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        o.data.materials.append(m)
        return o

    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    sans = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InterTight.ttf")

    def text(body, size, at, m, f, parent, extrude=0.0005):
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = body, f, size, extrude
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.materials.append(m)
        o = bpy.data.objects.new("txt", cu)
        sc.collection.objects.link(o)
        o.parent = parent
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
        o.location = tuple(at)
        return o

    drum_white, ink_m = mat((0.93, 0.93, 0.9), 0.35), mat((0.02, 0.02, 0.025), 0.4)
    blue_m, red_m = mat(P.KLEIN, 0.3), mat(P.RED, 0.3)

    def console(shell, plate, trim, label, knob, reach, lean=18):
        """The slot machine: a box leaning back out of the base's front, four reels behind four windows, a lever on the right. Built in its own frame: x along it, -y out of the face, z up its face."""
        W_, H_, D_ = 0.56, 0.17, 0.1
        con = empty("console")
        con.rotation_quaternion = yaw @ Quaternion((1, 0, 0), math.radians(-lean))
        con.location = tuple(C + front * (reach + D_ / 2 - 0.02) + Vector((0, 0, 0.135)))
        house = block((W_, D_, H_), (0, 0, 0), Quaternion(), shell, 0.012, con)
        face = block((W_ - 0.03, 0.004, H_ - 0.03), (0, -D_ / 2 - 0.001, 0), Quaternion(), plate, 0.0, con)
        xs = [-0.195, -0.065, 0.065, 0.195]
        for x in xs:
            for target in (house, face):
                w = block((0.1, 0.05, 0.075), (x, -D_ / 2, 0.005), Quaternion(), shell, 0.0, con)
                cut(target, w)
            hollow = block((0.108, 0.085, 0.13), (x, 0.005, 0.005), Quaternion(), shell, 0.0, con)
            cut(house, hollow)
            for dz in (-0.044, 0.044):
                block((0.102, 0.002, 0.003), (x, -D_ / 2 - 0.004, 0.005 + dz), Quaternion(), trim, 0.0, con)
        text("AlphaFold confidence (pLDDT)", 0.017, (0, -D_ / 2 - 0.0035, 0.064), label, sans, con)
        for x, (a, b) in zip(xs, STRETCH):
            text("%d–%d" % (a, b), 0.014, (x, -D_ / 2 - 0.0035, -0.058), label, sans, con)
        g = np.random.default_rng(3)
        for j, x in enumerate(xs):
            d = empty("drum")
            d.parent = con
            d.location = (x, 0, 0.005)
            bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.042, depth=0.092)
            barrel = bpy.context.object
            barrel.rotation_mode = "QUATERNION"
            barrel.rotation_quaternion = Quaternion((0, 1, 0), math.pi / 2)
            barrel.data.materials.append(drum_white)
            bpy.ops.object.shade_smooth()
            barrel.parent = d
            for k in range(10):
                h = empty("face")
                h.parent = d
                h.rotation_quaternion = Quaternion((1, 0, 0), 2 * math.pi * k / 10)
                body = str(SCORE[j]) if k == 0 else str(int(g.integers(10, 99)))
                cu = bpy.data.curves.new("num", "FONT")
                cu.body, cu.font, cu.size, cu.extrude = body, font, 0.038, 0.0015
                cu.align_x, cu.align_y = "CENTER", "CENTER"
                cu.materials.append((blue_m if SCORE[j] >= 70 else red_m) if k == 0 else ink_m)
                o = bpy.data.objects.new("num", cu)
                sc.collection.objects.link(o)
                o.parent = h
                o.rotation_mode = "QUATERNION"
                o.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
                o.location = (0, -0.0432, 0)
        lev = empty("lever")
        lev.parent = con
        lev.location = (W_ / 2 + 0.012, 0, 0.0)
        hub = block((0.024, 0.04, 0.04), (0, 0, 0), Quaternion(), shell, 0.006, lev)
        rod = block((0.008, 0.008, 0.17), (0.006, 0, 0.085), Quaternion(), mat((0.7, 0.72, 0.75), 0.15, 1.0), 0.002, lev)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, segments=24, ring_count=12, location=(0.006, 0, 0.17))
        k_ = bpy.context.object
        k_.data.materials.append(knob)
        bpy.ops.object.shade_smooth()
        k_.parent = lev

    cyan = emit((0.3, 0.9, 1.0), 12.0)
    cyan_soft = emit((0.3, 0.9, 1.0), 4.0)
    amber = emit((1.0, 0.45, 0.08), 14.0)
    label = emit((0.82, 0.9, 0.95), 2.5)
    chrome = mat((0.8, 0.82, 0.85), 0.12, 1.0)
    black = mat((0.012, 0.012, 0.016), 0.06, 0.0, 1.0)
    looks = []

    def look(build):
        before = set(o.name for o in ob)
        build()
        looks.append([o for o in ob if o.name not in before and o not in cutters])

    def white_hardware():
        white = mat((0.9, 0.9, 0.88), 0.28, 0.0, 0.7)
        turn([(0.001, 0.016), (0.40, 0.016), (0.42, 0.04), (0.42, 0.09), (0.39, 0.115), (0.36, 0.12), (0.36, 0.13), (0.345, 0.135), (0.001, 0.135)], white, 0.008)
        turn([(0.4185, 0.056), (0.424, 0.058), (0.424, 0.078), (0.4185, 0.08)], black, 0.0015)
        ring_(0.4245, 0.0022, 0.068, cyan)
        loop([(0.332, 0.13), (0.332, 0.89)], [(0.322, 0.89), (0.322, 0.13)], glass_m((0.93, 0.985, 1.0))).visible_shadow = False
        ring_(0.337, 0.005, 0.138, chrome)
        turn([(0.001, 0.902), (0.326, 0.902), (0.326, 0.884), (0.384, 0.884), (0.384, 0.95), (0.30, 0.962), (0.30, 1.0), (0.2, 1.008), (0.12, 1.045), (0.001, 1.045)], white, 0.007)      # stacked tiers, not a lid
        turn([(0.3835, 0.902), (0.3885, 0.904), (0.3885, 0.932), (0.3835, 0.934)], black, 0.0012)
        ring_(0.389, 0.0018, 0.918, cyan)
        turn([(0.2995, 0.972), (0.3035, 0.974), (0.3035, 0.99), (0.2995, 0.992)], black, 0.001)
        ring_(0.304, 0.0016, 0.982, cyan)
        turn([(0.001, 1.044), (0.09, 1.044), (0.09, 1.052), (0.001, 1.052)], black, 0.002)
        ring_(0.1, 0.0035, 1.046, cyan)
        for a in (math.radians(60), math.radians(180), math.radians(300)):       # three spines, none in front of the shape
            radial(a, 0.356, 0.51, (0.03, 0.034, 0.78), white, 0.006)
            radial(a, 0.374, 0.51, (0.006, 0.002, 0.62), cyan_soft, 0.0)
        turn([(0.001, 1.05), (0.055, 1.05), (0.055, 1.085), (0.035, 1.095), (0.035, 1.12), (0.001, 1.125)], chrome, 0.004)      # an emitter on top
        for z in (1.07, 1.105):
            ring_(0.056 if z < 1.09 else 0.036, 0.003, z, cyan)
        ring_(0.312, 0.004, 0.146, cyan)
        ring_(0.312, 0.004, 0.876, cyan)
        mist_in(0.305, 0.14, 0.88, 1.6)
        console(white, black, cyan, label, mat(P.RED, 0.2, 0.0, 0.6), 0.40)

    def gunmetal():
        gun = mat((0.085, 0.09, 0.1), 0.34, 1.0, 0.3)
        steel = mat((0.62, 0.64, 0.68), 0.22, 1.0)
        rubber = mat((0.02, 0.02, 0.024), 0.5)
        turn([(0.001, 0.016), (0.42, 0.016), (0.42, 0.062), (0.40, 0.072), (0.40, 0.10), (0.37, 0.118), (0.345, 0.135), (0.001, 0.135)], gun, 0.006)
        for k in range(40):
            radial(2 * math.pi * k / 40, 0.427, 0.04, (0.009, 0.03, 0.044), gun, 0.0015)
        ring_(0.418, 0.007, 0.04, amber)
        loop([(0.332, 0.13), (0.332, 0.875)], [(0.322, 0.875), (0.322, 0.13)], glass_m((0.95, 0.97, 0.98))).visible_shadow = False
        for k in range(6):
            a = math.radians(30 + 60 * k)
            radial(a, 0.343, 0.5, (0.02, 0.018, 0.75), gun, 0.003)
            radial(a, 0.353, 0.5, (0.004, 0.002, 0.6), amber if k in (2, 3) else cyan_soft, 0.0)
        turn([(0.001, 0.882), (0.326, 0.882), (0.326, 0.868), (0.40, 0.868), (0.405, 0.915), (0.37, 0.94), (0.30, 0.94), (0.30, 0.975), (0.21, 0.995), (0.001, 0.995)], gun, 0.006)
        ring_(0.402, 0.003, 0.895, cyan)
        for k in range(28):         # cooling fins on the crown
            radial(2 * math.pi * (k + 0.5) / 28, 0.255, 0.965, (0.006, 0.09, 0.05), gun, 0.0012)
        turn([(0.001, 0.99), (0.09, 0.99), (0.09, 1.05), (0.07, 1.065), (0.001, 1.065)], steel, 0.004)
        ring_(0.092, 0.004, 1.02, cyan)
        for a in (math.radians(150), math.radians(180), math.radians(210)):     # cables down the back, from the crown into the base
            pts = [around(a, 0.37, 0.93), around(a, 0.47, 0.96), around(a, 0.55, 0.75), around(a, 0.55, 0.35), around(a, 0.47, 0.1), around(a, 0.405, 0.088)]
            tube3d([tuple(p) for p in pts], 0.016, rubber, "cable")
        ring_(0.312, 0.004, 0.146, amber)
        ring_(0.312, 0.004, 0.862, cyan)
        mist_in(0.305, 0.14, 0.865, 1.6)
        console(gun, black, amber, label, mat((1.0, 0.45, 0.08), 0.2, 0.0, 0.6), 0.43)

    def capsule():
        dome = [(0.332 * math.cos(u), 0.80 + 0.2 * math.sin(u)) for u in np.linspace(0, math.pi / 2 - 0.01, 14)]
        inner = [(0.322 * math.cos(u), 0.80 + 0.19 * math.sin(u)) for u in np.linspace(math.pi / 2 - 0.01, 0, 14)]
        loop([(0.332, 0.13)] + dome, inner + [(0.322, 0.13)], glass_m((0.93, 0.985, 1.0)), 0.0).visible_shadow = False
        turn([(0.001, 0.016), (0.385, 0.016), (0.41, 0.032), (0.41, 0.095), (0.385, 0.115), (0.345, 0.122), (0.345, 0.135), (0.001, 0.135)], black, 0.008)
        ring_(0.4105, 0.0022, 0.064, cyan)
        ring_(0.39, 0.004, 0.02, cyan)
        white = mat((0.92, 0.92, 0.9), 0.25, 0.0, 0.7)
        for z in (0.44, 0.71):      # two rings held off the glass by nothing: they float
            turn([(0.37, z - 0.006), (0.395, z - 0.006), (0.395, z + 0.006), (0.37, z + 0.006), (0.37, z - 0.006)], white, 0.003)
            ring_(0.3695, 0.0025, z, cyan)
        ring_(0.312, 0.004, 0.146, cyan)
        turn([(0.001, 0.985), (0.05, 0.985), (0.05, 0.989), (0.001, 0.989)], cyan, 0.0)
        mist_in(0.305, 0.14, 0.86, 1.6)
        console(black, black, cyan, label, mat(P.RED, 0.2, 0.0, 0.6), 0.39)

    def hex_pod():
        rot = math.atan2(front.y, front.x) - math.pi / 6           # a flat face toward the lens
        white = mat((0.9, 0.9, 0.88), 0.28, 0.0, 0.7)
        graphite = mat((0.05, 0.052, 0.058), 0.3, 0.6, 0.6)
        turn([(0.001, 0.016), (0.47, 0.016), (0.47, 0.075), (0.445, 0.098), (0.41, 0.125), (0.001, 0.125)], white, 0.008, 6, rot)
        turn([(0.4705, 0.04), (0.476, 0.042), (0.476, 0.05), (0.4705, 0.052)], cyan, 0.0, 6, rot)
        loop([(0.385, 0.12), (0.385, 0.875)], [(0.375, 0.875), (0.375, 0.12)], glass_m((0.93, 0.985, 1.0)), 0.0, 6, rot).visible_shadow = False
        for k in range(6):
            a = rot + math.pi / 3 * k
            p = C + Vector((0.39 * math.cos(a), 0.39 * math.sin(a), 0.5))
            q = Quaternion((0, 0, 1), a)
            block((0.03, 0.026, 0.76), p, q, graphite, 0.005)
            block((0.003, 0.006, 0.6), p + q @ Vector((0.015, 0, 0)), q, cyan_soft, 0.0)
        turn([(0.001, 0.87), (0.40, 0.87), (0.43, 0.88), (0.43, 0.925), (0.31, 0.985), (0.13, 1.005), (0.001, 1.005)], graphite, 0.008, 6, rot)
        turn([(0.4305, 0.897), (0.436, 0.899), (0.436, 0.906), (0.4305, 0.908)], cyan, 0.0, 6, rot)
        turn([(0.001, 1.0), (0.12, 1.0), (0.12, 1.012), (0.001, 1.012)], white, 0.003, 6, rot)
        ring_(0.312, 0.004, 0.14, cyan)
        ring_(0.312, 0.004, 0.86, cyan)
        mist_in(0.3, 0.135, 0.865, 1.6)
        console(white, graphite, cyan, label, mat(P.RED, 0.2, 0.0, 0.6), 0.41)

    for build in (white_hardware, gunmetal, capsule, hex_pod):
        look(build)

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f in range(4):
        for s in (-0.3, 0.0, 0.3):
            shoot(c, f + s, hero, (C.x, C.y, 0.5))
    sc.render.use_motion_blur = False

    def update(t):
        base_update(t)
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        for o in every:
            o.hide_render = True
        core.hide_render = tail.hide_render = False
        for o in ob:
            if o.parent and o.parent.name == "keyhole":
                o.hide_render = True
        for i, parts in enumerate(looks):
            for o in parts:
                o.hide_render = i != f
        sky(0.2)
    return update


TANK = {}          # handles shot o leaves for shot m, which animates the same tank


def shot_o(sc, sky):
    """The culture tank rebuilt from sci-fi film references (镜头设计_v3/styleframes/art/fusion/s4/培养罐参考.md, 11-04 14:35): the tank is its own light, a straight glass tube whose ends hide in two tall housings with seams and lit squares, hung from a ring on four rods with four clamping arms (the claw for the tail comes later from the same ring); version 6 (11-04 14:43): a bundle of eight pipes fans out of the crown, the slot machine sits on the crown on a plinth, the lever is on the base. The room dims for W2. 0 the hero view, dimmed; 1 the top, closer, from the right: the reels and the pipes; 2 the hero view with the room lit, as when the tank opens. The machine, the mist and the bubbles are drawn; the blue shape, the red tail and the four numbers come from the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- o <out dir> 0 2 64 1"""
    base_update = shot_v(sc, sky)
    before_tank = set(o.name for o in bpy.data.objects)
    ob = bpy.data.objects
    core, tail = ob["core"], ob["tail"]
    every = [o for o in ob if o.name.split(".")[0] in ("letter", "guess", "tail_guess", "tail_cut")]
    C = Vector((127.03, -2.35, 0.0))          # the centre of the smallest circle round the model
    UP = 0.43
    for o in (core, tail):
        o.location.z += UP
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
    conf = np.array([float(l[60:66]) for l in pdb])
    res = np.array([int(l[22:26]) for l in pdb])
    STRETCH = [(1, 100), (101, 200), (201, 302), (303, 346)]
    SCORE = [int(round(conf[(res >= a) & (res <= b)].mean())) for a, b in STRETCH]
    print("reels land on", SCORE)

    hero = dict(at=(C.x, C.y, 0.9), az=math.atan2(0.55, 2.19), el=math.radians(12), d=4.5, mm=40.0)
    T = 0.2          # the glass runs 0.2 taller than the first try: the tank reads as a tube, not a canister
    yaw = Quaternion((0, 0, 1), hero["az"])
    front = yaw @ Vector((0, -1, 0))
    around = lambda a, rad, z: C + (yaw @ Quaternion((0, 0, 1), a)) @ Vector((0, -rad, 0)) + Vector((0, 0, z))     # a = 0 faces the lens

    def mat(rgb, rough, metal=0.0, coat=0.3):
        m = P.gloss(rgb, rough, coat)
        next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = metal
        return m

    def emit(rgb, power):
        m, nt, out = gk._mat("glow")
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value, e.inputs[1].default_value = (*rgb, 1), power
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        return m

    def glass_m(rgb):
        m = B.clear_glass()
        next(n for n in m.node_tree.nodes if n.type == "BSDF_TRANSPARENT").inputs[0].default_value = (*rgb, 1)
        return m

    def sharp(o, angle=32):
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
        except Exception:
            bpy.ops.object.shade_smooth()
        o.select_set(False)
        return o

    def rnd(pts, b=0.005):
        """Rounds every corner of a profile with a three-point fillet, so edges catch a highlight."""
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            p, q, r = (np.array(x, float) for x in (pts[i - 1], pts[i], pts[i + 1]))
            a, c = p - q, r - q
            la, lc = np.linalg.norm(a), np.linalg.norm(c)
            s = min(b, la / 2.5, lc / 2.5)
            u, v = a / la * s, c / lc * s
            out += [tuple(q + u), tuple(q + (u + v) * 0.3), tuple(q + v)]
        return out + [pts[-1]]

    def turn(profile, m, b=0.005, n=160, rot=0.0, z0=None):
        o = lathe(rnd(profile, b) if b else profile, m, "tank_part", n=n)
        o.location = tuple(C)
        o.rotation_euler = (0, 0, rot)
        return sharp(o)

    def loop(outer, inner, m, b=0.003, n=160, rot=0.0):
        """A thick-walled shell: up the outside, back down the inside, closed."""
        return turn(list(outer) + list(inner) + [outer[0]], m, b, n, rot)

    def ring_(R, r, z, m):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=160, minor_segments=12, location=(C.x, C.y, z))
        o = bpy.context.object
        o.data.materials.append(m)
        bpy.ops.object.shade_smooth()
        return o

    def block(size, at, rot, m, bevel=0.003, parent=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(at))
        o = bpy.context.object
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
        o.scale = size
        o.data.materials.append(m)
        if bevel:
            bv = o.modifiers.new("bevel", "BEVEL")
            bv.width, bv.segments, bv.limit_method = bevel, 3, "ANGLE"
        o.parent = parent
        return sharp(o)

    def radial(a, rad, z, size, m, bevel=0.002):
        """A block standing at angle a round the tank, its depth pointing out from the axis."""
        return block(size, around(a, rad, z), yaw @ Quaternion((0, 0, 1), a), m, bevel)

    cutters = []

    def cut(o, cutter):
        b = o.modifiers.new("cut", "BOOLEAN")
        b.operation, b.object = "DIFFERENCE", cutter
        cutter.hide_render = cutter.hide_viewport = True
        cutters.append(cutter)

    def mist_in(r, z0, z1, density):
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=z1 - z0, location=(C.x, C.y, (z0 + z1) / 2))
        o = bpy.context.object
        m = bpy.data.materials.new("mist")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (0.86, 0.97, 1.0, 1)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 7.0, 6
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value, mr.inputs[2].default_value = 0.45, 0.8
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation, mul.inputs[1].default_value = "MULTIPLY", density
        nt.links.new(nz.outputs[0], mr.inputs[0])
        nt.links.new(mr.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], vol.inputs["Density"])
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        o.data.materials.append(m)
        return o

    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    sans = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InterTight.ttf")

    def text(body, size, at, m, f, parent, extrude=0.0005):
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = body, f, size, extrude
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.materials.append(m)
        o = bpy.data.objects.new("txt", cu)
        sc.collection.objects.link(o)
        o.parent = parent
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
        o.location = tuple(at)
        return o

    drum_white, ink_m = mat((0.93, 0.93, 0.9), 0.35), mat((0.02, 0.02, 0.025), 0.4)
    blue_m, red_m = mat(P.KLEIN, 0.3), mat(P.RED, 0.3)

    def console(shell, plate, trim, label, knob, reach, lean=18):
        """The slot machine: a box leaning back out of the base's front, four reels behind four windows, a lever on the right. Built in its own frame: x along it, -y out of the face, z up its face."""
        W_, H_, D_ = 0.56, 0.17, 0.1
        con = empty("console")
        con.rotation_quaternion = yaw @ Quaternion((1, 0, 0), math.radians(-lean))
        con.location = tuple(C + front * (reach + D_ / 2 - 0.02) + Vector((0, 0, 0.135)))
        house = block((W_, D_, H_), (0, 0, 0), Quaternion(), shell, 0.012, con)
        face = block((W_ - 0.03, 0.004, H_ - 0.03), (0, -D_ / 2 - 0.001, 0), Quaternion(), plate, 0.0, con)
        xs = [-0.195, -0.065, 0.065, 0.195]
        for x in xs:
            for target in (house, face):
                w = block((0.1, 0.05, 0.075), (x, -D_ / 2, 0.005), Quaternion(), shell, 0.0, con)
                cut(target, w)
            hollow = block((0.108, 0.085, 0.13), (x, 0.005, 0.005), Quaternion(), shell, 0.0, con)
            cut(house, hollow)
            for dz in (-0.044, 0.044):
                block((0.102, 0.002, 0.003), (x, -D_ / 2 - 0.004, 0.005 + dz), Quaternion(), trim, 0.0, con)
        text("AlphaFold confidence (pLDDT)", 0.017, (0, -D_ / 2 - 0.0035, 0.064), label, sans, con)
        for x, (a, b) in zip(xs, STRETCH):
            text("%d–%d" % (a, b), 0.014, (x, -D_ / 2 - 0.0035, -0.058), label, sans, con)
        g = np.random.default_rng(3)
        for j, x in enumerate(xs):
            d = empty("drum")
            d.parent = con
            d.location = (x, 0, 0.005)
            bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.042, depth=0.092)
            barrel = bpy.context.object
            barrel.rotation_mode = "QUATERNION"
            barrel.rotation_quaternion = Quaternion((0, 1, 0), math.pi / 2)
            barrel.data.materials.append(drum_white)
            bpy.ops.object.shade_smooth()
            barrel.parent = d
            for k in range(10):
                h = empty("face")
                h.parent = d
                h.rotation_quaternion = Quaternion((1, 0, 0), 2 * math.pi * k / 10)
                body = str(SCORE[j]) if k == 0 else str(int(g.integers(10, 99)))
                cu = bpy.data.curves.new("num", "FONT")
                cu.body, cu.font, cu.size, cu.extrude = body, font, 0.038, 0.0015
                cu.align_x, cu.align_y = "CENTER", "CENTER"
                cu.materials.append((blue_m if SCORE[j] >= 70 else red_m) if k == 0 else ink_m)
                o = bpy.data.objects.new("num", cu)
                sc.collection.objects.link(o)
                o.parent = h
                o.rotation_mode = "QUATERNION"
                o.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
                o.location = (0, -0.0432, 0)
        lev = empty("lever")
        lev.parent = con
        lev.location = (W_ / 2 + 0.012, 0, 0.0)
        hub = block((0.024, 0.04, 0.04), (0, 0, 0), Quaternion(), shell, 0.006, lev)
        rod = block((0.008, 0.008, 0.17), (0.006, 0, 0.085), Quaternion(), mat((0.7, 0.72, 0.75), 0.15, 1.0), 0.002, lev)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, segments=24, ring_count=12, location=(0.006, 0, 0.17))
        k_ = bpy.context.object
        k_.data.materials.append(knob)
        bpy.ops.object.shade_smooth()
        k_.parent = lev

    cyan = emit((0.3, 0.9, 1.0), 12.0)
    cyan_soft = emit((0.3, 0.9, 1.0), 4.0)
    label = emit((0.82, 0.9, 0.95), 2.5)
    shell = mat((0.80, 0.81, 0.80), 0.32, 0.0, 0.5)         # pale hard shell: catches the tank's own glow
    band = mat((0.05, 0.055, 0.06), 0.3, 0.4, 0.6)
    gun = mat((0.07, 0.075, 0.085), 0.3, 1.0, 0.3)
    black = mat((0.012, 0.012, 0.016), 0.06, 0.0, 1.0)
    rubber = mat((0.02, 0.02, 0.024), 0.5)

    def beam(p, q, w, m):
        p, q = Vector(p), Vector(q)
        o = block((w, w, (q - p).length), (p + q) / 2, Vector((0, 0, 1)).rotation_difference(q - p), m, 0.004)
        return o

    def joint(p, r, m):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12, location=tuple(p))
        o = bpy.context.object
        o.data.materials.append(m)
        bpy.ops.object.shade_smooth()
        return o

    def lit_panels(z, n, a0, size, m):
        """Small glowing squares set round a housing wall."""
        for k in range(n):
            radial(a0 + 2 * math.pi * k / n, 0.371, z, size, m, 0.0)

    # the glass: a straight tube whose ends hide inside the two housings
    loop([(0.315, 0.27), (0.315, 0.91 + T)], [(0.305, 0.91 + T), (0.305, 0.27)], glass_m((0.9, 0.98, 1.0)), 0.0).visible_shadow = False
    # the base housing: a wide foot, a tall wall with seams and lit squares, a lip the glass sinks into
    turn([(0.001, 0.016), (0.43, 0.016), (0.43, 0.05), (0.40, 0.062), (0.37, 0.07), (0.37, 0.118), (0.362, 0.121), (0.362, 0.127), (0.37, 0.13),
          (0.37, 0.2), (0.362, 0.203), (0.362, 0.209), (0.37, 0.212), (0.37, 0.27), (0.335, 0.298), (0.318, 0.3), (0.318, 0.28), (0.001, 0.28)], shell, 0.006)
    turn([(0.4305, 0.026), (0.436, 0.028), (0.436, 0.04), (0.4305, 0.042)], band, 0.0015)
    ring_(0.437, 0.0022, 0.034, cyan)
    lit_panels(0.165, 10, math.pi / 10, (0.05, 0.004, 0.022), cyan_soft)
    for k in range(20):         # vents round the foot
        radial(2 * math.pi * (k + 0.5) / 20, 0.38, 0.09, (0.012, 0.03, 0.03), band, 0.002)
    ring_(0.318, 0.006, 0.302, cyan)
    # the top housing, the same family turned upside down, with a hub the mast plugs into; built at the first try's height, then lifted by T
    before_top = set(o.name for o in ob)
    turn([(0.001, 0.88), (0.318, 0.88), (0.318, 0.882), (0.335, 0.884), (0.37, 0.912), (0.37, 0.97), (0.362, 0.973), (0.362, 0.979), (0.37, 0.982),
          (0.37, 1.06), (0.33, 1.1), (0.22, 1.12), (0.22, 1.15), (0.12, 1.16), (0.001, 1.16)], shell, 0.006)
    turn([(0.3705, 1.005), (0.376, 1.007), (0.376, 1.035), (0.3705, 1.037)], band, 0.0015)
    ring_(0.3765, 0.0018, 1.021, cyan)
    lit_panels(0.94, 10, 0.0, (0.05, 0.004, 0.02), cyan_soft)
    ring_(0.318, 0.006, 0.878, cyan)
    # the hanger: a ring held up by three rods, four arms from it that clamp the top housing (the director's note of 14:43: no single mast)
    steel = mat((0.62, 0.64, 0.68), 0.2, 1.0)
    turn([(0.40, 1.29), (0.48, 1.29), (0.48, 1.33), (0.40, 1.33), (0.40, 1.29)], gun, 0.004)
    ring_(0.481, 0.0025, 1.31, cyan)
    for k in range(4):          # hangers above the four arms
        a = math.pi / 4 + k * math.pi / 2
        beam(around(a, 0.44, 1.32), around(a, 0.44, 3.0), 0.022, gun)
    # a bundle of pipes and cables, thick and thin, out of the back of the crown and up out of frame
    for a_, r0, rr, m_p, lean, top in ((180, 0.12, 0.034, steel, 0.25, 2.8), (150, 0.2, 0.022, rubber, 0.7, 2.4), (210, 0.2, 0.022, rubber, 0.7, 2.4), (120, 0.16, 0.018, gun, 0.9, 2.1),
                                       (240, 0.16, 0.018, gun, 0.9, 2.1), (100, 0.24, 0.014, rubber, 1.2, 1.9), (260, 0.24, 0.014, rubber, 1.2, 1.9), (180, 0.25, 0.02, gun, 0.5, 2.6)):
        aa = math.radians(a_)       # each rises a little, then arcs back and out, so the bundle fans instead of standing like bars
        pts = [around(aa, r0, 1.11), around(aa, r0, 1.26), around(aa, r0 + lean * 0.15, 1.42), around(aa, r0 + lean * 0.5, 1.62), around(aa, r0 + lean, top * 0.9), around(aa, r0 + lean * 1.3, top + 0.6)]
        tube3d([tuple(p) for p in pts], rr, m_p, "pipe")
        bpy.ops.mesh.primitive_torus_add(major_radius=rr + 0.006, minor_radius=0.007, major_segments=48, minor_segments=10, location=tuple(around(aa, r0, 1.165)))
        cl = bpy.context.object
        cl.data.materials.append(steel)
        bpy.ops.object.shade_smooth()
    # the slot machine sits on the crown, on a plinth, facing the lens; its own lever is hidden, the lever is on the base
    block((0.5, 0.11, 0.25), C + front * 0.1 + Vector((0, 0, 1.24)), yaw, band, 0.006)       # tall enough to lift the reels clear above the ring
    console(shell, black, cyan, label, mat(P.RED, 0.2, 0.0, 0.6), 0.4)
    con = [o for o in ob if o.name.startswith("console")][-1]
    con.scale = (0.9, 0.9, 0.9)
    con.location = tuple(C + front * 0.1 + Vector((0, 0, 1.365 + 0.085 * 0.9)))
    bd = next(n for n in drum_white.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bd.inputs["Emission Color"].default_value, bd.inputs["Emission Strength"].default_value = (1, 1, 0.97, 1), 0.8      # the reels are lit from inside, so the numbers read in the dark
    con.rotation_quaternion = yaw
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        sh, el, hd = around(a, 0.45, 1.29), around(a, 0.56, 1.16), around(a, 0.40, 1.03)
        beam(sh, el, 0.046, gun)
        beam(el, hd, 0.04, gun)
        beam(lerp(sh, el, 0.3), lerp(el, hd, 0.6), 0.014, mat((0.7, 0.72, 0.75), 0.15, 1.0))       # a piston across the elbow
        joint(el, 0.038, gun)
        joint(sh, 0.026, gun)
        radial(a, 0.385, 1.03, (0.06, 0.03, 0.07), band, 0.004)                  # the clamp pad on the housing
        radial(a, 0.401, 1.03, (0.03, 0.002, 0.006), cyan, 0.0)
    for a in (math.radians(160), math.radians(200), math.radians(180)):        # cables from the ring down into the back of the top housing
        pts = [around(a, 0.44, 1.29), around(a, 0.5, 1.2), around(a, 0.46, 1.09), around(a, 0.36, 1.07)]
        tube3d([tuple(p) for p in pts], 0.012, rubber, "cable")
    for o in ob:
        if o.name not in before_top and o.parent is None:
            o.location.z += T
    # inside: a light strip at the back for a rim on the shape, glowing mist, bubbles
    radial(math.pi, 0.296, 0.59 + T / 2, (0.02, 0.004, 0.6 + T), emit((0.6, 0.95, 1.0), 6.0), 0.0)
    m_ = mist_in(0.302, 0.285, 0.895 + T, 1.0)
    vol = next(n for n in m_.data.materials[0].node_tree.nodes if n.type == "PRINCIPLED_VOLUME")
    vol.inputs["Emission Color"].default_value = (0.25, 0.85, 1.0, 1)
    vol.inputs["Emission Strength"].default_value = 0.5          # any brighter and the red tail washes to pink
    TANK.clear()
    TANK["bubbles"] = []
    g = np.random.default_rng(5)
    bub = emit((0.75, 0.97, 1.0), 2.0)
    for _ in range(46):
        a, r = g.uniform(0, 2 * math.pi), 0.27 * math.sqrt(g.uniform(0.02, 1))
        TANK["bubbles"].append(joint(C + Vector((r * math.cos(a), r * math.sin(a), g.uniform(0.31, 0.87 + T))), float(g.uniform(0.004, 0.011)), bub))
    for o in ob:                # the console's own lever goes; the lever is on the base
        if o.parent and o.parent.name.startswith("lever"):
            o.hide_render = True
    # the lever on the base, front right: pull it and the reels on top spin
    la = math.radians(68)
    radial(la, 0.38, 0.2, (0.06, 0.03, 0.06), gun, 0.006)
    lever = empty("lever_pivot")         # the rod and knob turn about the hub's own axis, tangent to the base
    lever.location = tuple(around(la, 0.40, 0.2))
    bpy.context.view_layer.update()
    for o in (beam(around(la, 0.40, 0.2), around(la, 0.47, 0.4), 0.014, steel), joint(around(la, 0.40, 0.2), 0.022, steel), joint(around(la, 0.47, 0.4), 0.03, mat(P.RED, 0.2, 0.0, 0.6))):
        o.parent = lever
        o.matrix_parent_inverse = lever.matrix_world.inverted()
    TANK.update(lever=lever, lever_axis=yaw @ Quaternion((0, 0, 1), la) @ Vector((1, 0, 0)), mist_density=next(n for n in m_.data.materials[0].node_tree.nodes if n.type == "MATH").inputs[1],
                drums=[o for o in ob if o.name.startswith("drum")], drum_white=drum_white, C=C, T=T, UP=UP, yaw=yaw, hero=hero)

    # lights: a white key from the front left keeps blue and red true; the room dims for W2 and comes back when the tank opens
    kd = bpy.data.lights.new("key", "AREA")
    kd.size, kd.energy = 0.6, 30.0
    key = bpy.data.objects.new("key", kd)
    sc.collection.objects.link(key)
    key.location = tuple(around(math.radians(-40), 1.7, 1.4))
    recv = bpy.data.collections.new("key_lights_only_the_shape")      # light linking: the key lights the blue and red shape and nothing else, so the dimmed table stays dark
    recv.objects.link(core)
    recv.objects.link(tail)
    key.light_linking.receiver_collection = recv
    key.rotation_mode = "QUATERNION"
    key.rotation_quaternion = (Vector((C.x, C.y, 0.69)) - key.location).to_track_quat("-Z", "Y")
    sun_o = next(o for o in ob if o.type == "LIGHT" and o.data.type == "SUN")
    sun_e = sun_o.data.energy
    wnt = sc.world.node_tree
    bgs = [n for n in wnt.nodes if n.type == "BACKGROUND"]
    dim = wnt.nodes.new("ShaderNodeMath")
    dim.operation = "MULTIPLY"
    src = bgs[0].inputs[1].links[0].from_socket
    wnt.links.new(src, dim.inputs[0])
    wnt.links.new(dim.outputs[0], bgs[0].inputs[1])
    bone_s = bgs[1].inputs[1].default_value
    TANK.update(key=key, recv=recv, dim=dim, bgs=bgs, bone_s=bone_s, sun=sun_o, sun_e=sun_e, parts=[o for o in ob if o.name not in before_tank and o.type != "LIGHT"])

    close = dict(at=(C.x, C.y, 1.42), az=hero["az"] + math.radians(24), el=math.radians(14), d=2.4, mm=40.0)      # the top: reels and pipes
    views = [hero, close, hero]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f, v in enumerate(views):
        for s in (-0.3, 0.0, 0.3):
            shoot(c, f + s, v, (C.x, C.y, 0.69))
    sc.render.use_motion_blur = False

    def update(t):
        base_update(t)
        f = min(FRAMES - 1, max(0, round((t - START) * FPS)))
        for o in every:
            o.hide_render = True
        core.hide_render = tail.hide_render = False
        for o in ob:
            if o.parent and o.parent.name == "keyhole":
                o.hide_render = True
        k = 1.0 if f == 2 else 0.05
        sky(0.2)
        dim.inputs[1].default_value = k
        bgs[1].inputs[1].default_value = bone_s * k
        sun_o.data.energy = sun_e * k
        key.hide_render = f == 2
    return update


def shot_m(sc, sky):
    """W2 motion, part one, on the tank of shot o (version 6, the director's OK of 11-04 14:57), on a 123 BPM grid until the song arrives (one beat 0.488 s, one bar 1.95 s): bars 0-1 the tank comes down on its rig onto S3's empty cell as the room dims; bar 2 the lever pulls itself, the tank gurgles; bar 3 the question mark is sucked up into the top and the four reels start; bars 4-7 in the mist a shape forms in a frenzy, a new guess on every beat, shaking, turning, the mist thinning as it firms up; bar 8 the reels stop one by one on the beat, 87 92 95: the shape holds in Klein blue; 47: the tail turns red and keeps pulsing; bar 9 the camera comes down to the shape. The guesses are drawn (smooth random bends of the real model, kept inside the glass); the blue shape, the red tail and the four numbers come from the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- m <out dir> 0 1170 16 0.5 2"""
    shot_o(sc, sky)
    ob = bpy.data.objects
    C, T, UP, yaw, hero = TANK["C"], TANK["T"], TANK["UP"], TANK["yaw"], TANK["hero"]
    core, tail, small = ob["core"], ob["tail"], ob["cdk20_small"]
    for o in ob:                # S3's letters and old guesses never show here
        if o.name.split(".")[0] in ("letter", "guess", "tail_guess", "tail_cut"):
            o.hide_render = True
    dashes = [o for o in ob if o.parent and o.parent.name == "keyhole"]
    sky(0.2)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    B_ = 60.0 / 123.0
    beat = lambda n: n * B_

    # the guess: the real model, unbent as its basis, with eight bent guesses as shape keys
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    heavy = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H"])
    centre = heavy.mean(0)
    base_v = (full["verts"] + centre - centre) @ R.T * P_S
    me = bpy.data.meshes.new("frenzy")
    me.from_pydata(base_v.tolist(), [], full["quads"].tolist())
    grey = see_through((0.75, 0.78, 0.82), 0.5)
    g_bsdf = next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    me.materials.append(grey)
    guess = bpy.data.objects.new("frenzy", me)
    sc.collection.objects.link(guess)
    B.smooth(guess)
    guess.rotation_mode = "QUATERNION"
    guess.rotation_quaternion, guess.scale = small.rotation_quaternion, small.scale
    guess.location = Vector(small.location) + Vector((0, 0, UP))
    bpy.context.view_layer.update()
    M = guess.matrix_world.copy()
    Mi = M.inverted()
    guess.shape_key_add(name="Basis")
    world0 = (np.c_[base_v, np.ones(len(base_v))] @ np.array(M).T)[:, :3]
    zc = float(world0[:, 2].mean())
    LIM_R, Z_LO, Z_HI = 0.282, 0.315, 1.065         # inside the glass (0.305) less the shake, clear of the back light strip (0.294); between the two housings
    keys = []
    for k in range(8):
        gr = np.random.default_rng(40 + k)
        v = base_v.copy()
        for _ in range(3):
            kk, ph = gr.uniform(0.08, 0.2, 3), gr.uniform(0, 6.3, 3)
            v = v + 7.0 * P_S * np.sin(base_v @ kk[:, None] + ph)
        w = (np.c_[v, np.ones(len(v))] @ np.array(M).T)[:, :3]
        d = w[:, :2] - np.array([C.x, C.y])
        rmax = float(np.sqrt((d ** 2).sum(1)).max())
        if rmax > LIM_R:                # squeeze the guess sideways until it fits the glass
            w[:, :2] = np.array([C.x, C.y]) + d * (LIM_R / rmax)
        lo, hi = float(w[:, 2].min()), float(w[:, 2].max())
        if lo < Z_LO or hi > Z_HI:
            s_ = min(1.0, (Z_HI - Z_LO) / (hi - lo))
            w[:, 2] = (w[:, 2] - (lo + hi) / 2) * s_ + (Z_LO + Z_HI) / 2
        sk = guess.shape_key_add(name="guess%d" % k)
        sk.data.foreach_set("co", (np.c_[w, np.ones(len(w))] @ np.array(Mi).T)[:, :3].astype(np.float32).ravel())
        keys.append(sk)
    print("guess keys fit: r <= %.3f, z %.3f-%.3f" % (LIM_R, Z_LO, Z_HI))

    # everything turns about the tank's axis through the shape's middle, so turning never brings it nearer the glass
    pivot = empty("frenzy_pivot")
    pivot.location = (C.x, C.y, zc)
    bpy.context.view_layer.update()
    for o in (guess, core, tail):
        mw = o.matrix_world.copy()
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
        o.matrix_world = mw
    TANK["recv"].objects.link(guess)

    # the whole tank, the rig and the shape come down together
    root = empty("tank_root")
    for o in TANK["parts"] + [pivot]:
        if o.parent is None and o is not root:
            o.parent = root
    red_m = tail.active_material
    r_bsdf = next(n for n in red_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    tail_red = tuple(r_bsdf.inputs["Base Color"].default_value)
    tail_grey = see_through((0.55, 0.58, 0.63), 0.5)
    t_bsdf = next(n for n in tail_grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED")

    # the question mark, dark in the glowing mist, facing the lens
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    cu = bpy.data.curves.new("ask", "FONT")
    cu.body, cu.font, cu.size, cu.extrude = "?", font, 0.6, 0.03
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.materials.append(gk.surface((0.004, 0.004, 0.005), 0.3))
    ask = bpy.data.objects.new("ask_m", cu)
    sc.collection.objects.link(ask)
    ask.parent = root
    ask.rotation_mode = "QUATERNION"
    ask.rotation_quaternion = yaw @ Quaternion((1, 0, 0), math.pi / 2)
    ask_home = Vector((C.x, C.y, zc))

    # the reels start on "??"
    for d in TANK["drums"]:
        for h in d.children:
            if h.name.startswith("face") and abs(h.rotation_quaternion.angle - math.pi) < 0.01:
                for o in h.children:
                    o.data.body = "??"
    bubbles = TANK["bubbles"]
    bub0 = [Vector(o.location) for o in bubbles]

    # the beats
    LAND, LEVER, SUCK, FORM, STOP = beat(7), beat(8), beat(12), beat(13), [beat(32), beat(33), beat(34), beat(35)]
    END = 19.5
    DROP = 2.2

    def drop_z(t):
        """Lowered on its rig, slowing to a stop on the cell's border: no bounce, it would sink into the border."""
        x = min(1.0, max(0.0, t / LAND))
        return DROP * (1 - x) ** 2.2

    def lever_angle(t):
        u = t - LEVER
        if u < 0:
            return 0.0
        if u < 0.12:
            return math.radians(60) * smooth(u / 0.12)
        if u < 0.5:
            return math.radians(60)
        return math.radians(60) * (1 - smooth((u - 0.5) / 0.5))

    def bubble_rise(t):
        """Height risen so far: slow drift, four times as fast in the two seconds after the lever (the gurgle)."""
        boost = lambda x: max(0.0, min(x, LEVER + 2.0) - LEVER)
        return 0.06 * t + 0.24 * boost(t) - 0.24 * max(0.0, min(t, LEVER + 2.0) - (LEVER + 1.4)) * 0.5

    UPR, DN = 0.25, 0.45          # each reel winds up in 0.25 s and slows to a stop over 0.45 s, ending exactly on its beat

    def run(t, ts, te):
        """Turns so far, in seconds at full speed."""
        if t <= ts:
            return 0.0
        if t <= ts + UPR:
            return (t - ts) ** 2 / (2 * UPR)
        if t <= te - DN:
            return (t - ts) - UPR / 2
        if t <= te:
            u = t - (te - DN)
            return (te - DN - ts) - UPR / 2 + u - u * u / (2 * DN)
        return (te - ts) - UPR / 2 - DN / 2

    spins = []
    for j in range(4):
        ts, te = SUCK + 0.06 * j, STOP[j]
        total = run(te + 1, ts, te)
        n = round((5.0 * 2 * math.pi * total - math.pi) / (2 * math.pi))        # about five turns a second
        spins.append((ts, te, (math.pi + 2 * math.pi * n) / total))

    def reel_angle(j, t):
        ts, te, w = spins[j]
        return -math.pi - w * run(t, ts, te)         # starts on face 5, "??", ends a whole number of turns later on face 0

    rng = np.random.default_rng(9)
    turns = rng.uniform(-35, 35, 64)
    jit = rng.normal(0, 1, (64, 3))

    def frenzy(t):
        """Which two guesses blend, how far, the turn about the axis, the jitter, how bent, how solid."""
        n = int((t - FORM) / B_)
        x = smooth(min(1.0, ((t - FORM) - n * B_) / 0.11))          # each new guess snaps in within 0.11 s of its beat
        calm = 1.0 - smooth((t - beat(22)) / (STOP[2] - beat(22)))       # from bar 5½ the guesses settle toward the real shape
        bend = 0.12 + 0.88 * calm
        ang = (turns[n % 64] * x + turns[(n - 1) % 64] * (1 - x)) * calm
        shake = (0.007 * calm + 0.002) * np.sin(np.array([71.0, 53.0, 97.0]) * t + jit[n % 64])
        return n, x, bend, ang, shake, 1.0 - calm

    hero_in = dict(hero, d=hero["d"] * 0.62, at=(C.x, C.y, 0.74))          # in on the shape while it forms; the reels come back at bar 8
    medium = dict(hero, d=3.1, at=(C.x, C.y, 1.15), el=math.radians(10))
    low_in = dict(at=(C.x, C.y, zc), az=hero["az"] - math.radians(10), el=math.radians(14), d=2.0, mm=45.0)
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)

    def view(t):
        if t < beat(8):
            v = blend(held, hero, smooth(t / beat(8)))
            if LAND <= t < LAND + 0.3:          # the thud of the landing, in the camera
                v["at"] = (v["at"][0], v["at"][1], v["at"][2] + 0.006 * math.sin(60 * (t - LAND)) * (1 - (t - LAND) / 0.3))
            return v
        if t < FORM:
            return hero
        if t < beat(31):
            return blend(hero, hero_in, smooth((t - FORM) / (beat(31) - FORM)))
        if t < beat(32):
            return blend(hero_in, medium, smooth((t - beat(31)) / B_))
        if t < beat(36):
            return medium
        return blend(medium, low_in, smooth((t - beat(36)) / (END - beat(36))))

    def blend(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])

    def key_pose(o, f, fn):
        """Keys o at f - 0.25 and f + 0.25 from fn(time), so the shutter sees the motion."""
        o.animation_data_clear()
        for s_ in (-0.25, 0.25):
            fn((f + s_) / FPS)
            o.keyframe_insert("location", frame=f + s_)
            o.keyframe_insert("rotation_quaternion", frame=f + s_)

    def update(t):
        t = t - START
        f = round(t * FPS)
        k = 1.0 - 0.95 * smooth((t - 0.5) / (LAND - 0.5))           # the room dims as the tank comes down
        TANK["dim"].inputs[1].default_value = k
        TANK["bgs"][1].inputs[1].default_value = TANK["bone_s"] * k
        TANK["sun"].data.energy = TANK["sun_e"] * k
        for o in dashes:
            o.hide_render = t > LAND - 0.3
        key_pose(root, f, lambda x: setattr(root, "location", (0, 0, drop_z(x))))
        lv = TANK["lever"]
        key_pose(lv, f, lambda x: setattr(lv, "rotation_quaternion", Quaternion(TANK["lever_axis"], lever_angle(x))))
        for o, p0 in zip(bubbles, bub0):
            z = 0.31 + ((p0.z - 0.31) + bubble_rise(t)) % (0.87 + T - 0.31)
            o.location = (p0.x, p0.y, z)
        # the question mark: hangs, then is pulled up into the top
        u = (t - SUCK) / 0.35
        ask.hide_render = u > 1.0
        if u <= 0:
            ask.animation_data_clear()
            ask.scale = (1, 1, 1)
            ask.location = ask_home + Vector((0, 0, 0.01 * math.sin(2.1 * t)))
        else:
            def pose(x):
                v_ = min(1.0, max(0.0, (x - SUCK) / 0.35)) ** 2
                ask.scale = (1 - 0.6 * v_, 1 + 2.2 * v_, 1)
                ask.location = ask_home + Vector((0, 0, (Z_HI + 0.12 - zc) * v_))
            key_pose(ask, f, pose)
        for j, d in enumerate(TANK["drums"]):
            key_pose(d, f, lambda x, j=j, d=d: setattr(d, "rotation_quaternion", Quaternion((1, 0, 0), reel_angle(j, x))))
        # the mist: thick while it guesses, thinning as the shape firms up
        TANK["mist_density"].default_value = 1.0 + 1.0 * smooth((t - SUCK) / 1.5) - 1.4 * smooth((t - beat(22)) / (STOP[2] - beat(22)))
        # the shape
        forming = FORM <= t < STOP[2]
        guess.hide_render = not forming
        core.hide_render = tail.hide_render = t < STOP[2]
        if t < FORM:
            pivot.animation_data_clear()
            pivot.rotation_quaternion = Quaternion()
        elif forming:
            n, x, bend, ang, shake, solid = frenzy(t)
            for i, sk in enumerate(keys):
                sk.value = bend * (x if i == n % 8 else (1 - x) if i == (n - 1) % 8 else 0.0)
            g_bsdf.inputs["Alpha"].default_value = 0.5 + 0.4 * solid          # it must read through the mist from the first beat
            g_bsdf.inputs["Base Color"].default_value = (*lerp((0.75, 0.78, 0.82), (0.12, 0.2, 0.55), solid), 1)

            def pose(xx):
                if xx < FORM:
                    xx = FORM
                nn, xa, _, a_, sh, _ = frenzy(min(xx, STOP[2] - 1e-3))
                pivot.rotation_quaternion = Quaternion((0, 0, 1), math.radians(a_))
                pivot.location = (C.x + sh[0], C.y + sh[1], zc + 0.5 * sh[2])
            key_pose(pivot, f, pose)
        else:
            pivot.animation_data_clear()
            pivot.rotation_quaternion = Quaternion()
            pivot.location = (C.x, C.y, zc)
            red = t >= STOP[3]
            tail.active_material = red_m if red else tail_grey
            pulse = 0.5 + 0.5 * math.cos(2 * math.pi * (t - STOP[3]) / B_) if red else 0.0
            r_bsdf.inputs["Emission Color"].default_value = (*tail_red[:3], 1)
            r_bsdf.inputs["Emission Strength"].default_value = 0.6 * pulse          # the tail keeps pulsing on the beat: the AI is not sure of it
    return update


def shot_j(sc, sky, ferro=False, spikes=True, meta=False, shake=False):
    """W2 motion without the tank (the director's note of 11-04 17:40: the tank is ugly, drop it): on a 123 BPM grid until the song arrives (one beat 0.488 s). Bars 0-1 S3's empty cell with the dashed keyhole; beat 4 the outline springs up off the table as a flat grey shape that stretches and flies up; beats 6-28 it hangs in the air in a frenzy, a new guess on every beat, tumbling, twitching on every half beat, greying into blue as it calms; beat 28 it snaps into the real model, the core Klein blue; beat 29 the tail turns red and keeps twitching between its guesses; beats 30-34 it floats down into its cell, where 4-01 goes on. The guesses are drawn (smooth random bends of the real model); the blue shape and the red tail are the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- j <out dir> 0 1054 16 0.5 2"""
    shot_v(sc, sky)
    ob = bpy.data.objects
    core, tail, small = ob["core"], ob["tail"], ob["cdk20_small"]
    tg = sorted([o for o in ob if o.name.split(".")[0] == "tail_guess"], key=lambda o: o.name)
    tail_ghosts = tg[4:]            # shot_v makes four grey swings of the tail, then the same four in see-through red
    for o in ob:
        if o.name.split(".")[0] in ("letter", "guess", "tail_guess", "tail_cut"):
            o.hide_render = True
    dashes = [o for o in ob if o.parent and o.parent.name == "keyhole"]
    sky(0.2)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    B_ = 60.0 / (123.477 if shake else 123.0)          # shot d is on Harder Better Faster Stronger itself, from 50.446 s, so the first sung bar is on beat 4 (音乐/W2_押韵字幕.md); the rest are on the old grid
    beat = lambda n: n * B_
    POP, APEX, CALM, SNAP, RED, DOWN, LAND, END = beat(4), beat(6), beat(20), beat(28), beat(29), beat(30), beat(34), (FRAMES - 1) / FPS
    MELT, WHIP, SPLAT, PULL = beat(30), beat(31), beat(32), beat(33)
    if shake:           # shot d: it stays up for the shake, comes down once the tail is off
        # version 4 (the director's note of 11-04 22:50: the tail went too fast, shake it longer, on the beat): the tail stays red and flickering to beat 32,
        # melts on 32, winds up on 33, shakes from 34 with a swing on every eighth note, lets go on 39 and splats on the downbeat of 40
        MELT, WHIP, SPLAT, PULL = beat(32), beat(34), beat(40), beat(41)
        DOWN, LAND = beat(40), beat(44)

    # the guess: the real model as its basis, eight bent guesses as shape keys, placed where S3's small model lay
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    base_v = full["verts"] @ R.T * P_S
    me = bpy.data.meshes.new("frenzy")
    me.from_pydata(base_v.tolist(), [], full["quads"].tolist())
    grey = see_through((0.42, 0.44, 0.48), 0.55)
    g_bsdf = next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    me.materials.append(grey)
    guess = bpy.data.objects.new("frenzy", me)
    sc.collection.objects.link(guess)
    B.smooth(guess)
    guess.rotation_mode = "QUATERNION"
    guess.rotation_quaternion, guess.scale, guess.location = small.rotation_quaternion, small.scale, small.location
    guess.shape_key_add(name="Basis")
    shapes = [base_v]
    for k in range(8):
        gr = np.random.default_rng(40 + k)
        v = base_v.copy()
        for _ in range(3):
            kk, ph = gr.uniform(0.08, 0.2, 3), gr.uniform(0, 6.3, 3)
            v = v + 8.0 * P_S * np.sin(base_v @ kk[:, None] + ph)
        guess.shape_key_add(name="guess%d" % k).data.foreach_set("co", v.astype(np.float32).ravel())
        shapes.append(v)
    keys = list(guess.data.shape_keys.key_blocks)[1:]
    if ferro:
        guess.shape_key_clear()
        keys, shapes = [], [base_v]
    bpy.context.view_layer.update()
    Mg = np.array(guess.matrix_world)
    world = [(np.c_[v, np.ones(len(v))] @ Mg.T)[:, :3] for v in shapes]
    P0 = Vector(world[0].mean(0).tolist())          # the pivot: the middle of the real shape at rest
    RB = max(float(np.sqrt(((w - np.array(P0)) ** 2).sum(1)).max()) for w in world)        # no part of any guess is further than this from the pivot
    LO = min(float(w[:, 2].min()) for w in world) - P0.z                                  # the lowest any guess reaches below the pivot, unturned
    RB0 = RB
    if ferro:
        # the ferrofluid look: spikes stand on an even scatter of points about 5 A apart, each a cone with hollow sides 2.6 A round its foot
        # a liquid body: the surface smoothed out (Taubin steps, so it does not shrink); it hardens back into the real surface as it calms
        quads = full["quads"]
        ed = np.concatenate([quads[:, [0, 1]], quads[:, [1, 2]], quads[:, [2, 3]], quads[:, [3, 0]]])
        ed = np.concatenate([ed, ed[:, ::-1]])
        deg = np.bincount(ed[:, 0], minlength=len(base_v)).astype(np.float64)[:, None]

        def lap(v):
            nb = v[ed[:, 1]]
            acc = np.stack([np.bincount(ed[:, 0], nb[:, k_], len(v)) for k_ in range(3)], 1)
            return acc / np.maximum(deg, 1) - v
        SM = base_v.copy()
        for _ in range(0 if meta else 3000 if not spikes else 1500):           # plain diffusion over about 15 A (20 A for shot e, which closes the deep cleft): the protein's lumps melt into one liquid body
            SM = SM + 0.5 * lap(SM)
        c0 = base_v.mean(0)
        SM = c0 + (SM - SM.mean(0)) * (np.linalg.norm(base_v - c0, axis=1).mean() / np.linalg.norm(SM - SM.mean(0), axis=1).mean())     # grown back to the model's size

        def normals(v):
            fn = np.cross(v[quads[:, 2]] - v[quads[:, 0]], v[quads[:, 3]] - v[quads[:, 1]])
            acc = np.zeros_like(v)
            for k_ in range(4):
                np.add.at(acc, quads[:, k_], fn)
            return acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
        NV = normals(SM)
        if float((NV * (SM - SM.mean(0))).sum()) < 0:
            NV = -NV
        A_ = full["verts"].astype(np.float64)
        gf = np.random.default_rng(23)
        cells = {}
        for i in gf.permutation(len(A_)):
            cells.setdefault(tuple((A_[i] // 6.0).astype(int)), i)
        from mathutils.kdtree import KDTree
        tips = list(cells.values())
        kd = KDTree(len(tips))
        for k_, i in enumerate(tips):
            kd.insert(A_[i].tolist(), k_)
        kd.balance()
        dist = np.array([kd.find(p_.tolist())[2] for p_ in A_])
        SPIKE = np.clip(1 - dist / 3.2, 0, 1) ** 2.5
        # patches where the fluid gathers and bristles, two a beat at random spots, each rising in 0.2 s and sinking over about a second
        ev_t = np.array([POP + (i + gf.uniform(0, 0.5)) * B_ / 2 for i in range(int((SNAP - POP) / (B_ / 2)))])
        ev_c = gf.integers(0, len(A_), len(ev_t))
        ev_s = gf.uniform(7, 11, len(ev_t))
        W = np.stack([np.exp(-((A_ - A_[c_]) ** 2).sum(1) / (2 * s_ ** 2)) for c_, s_ in zip(ev_c, ev_s)]).astype(np.float32)
        KF = gf.normal(0, 0.12, (3, 3))
        WF, PF = gf.uniform(2.0, 3.5, 3), gf.uniform(0, 6.3, 3)
        DMAX = 4 * 1.3 + 12 * 1.1 * 1.2 + 2.5 * 3 + float(np.linalg.norm(SM - base_v, axis=1).max()) / P_S          # the furthest the surface can move out, in A
        grow = DMAX * P_S * guess.scale[0]
        RB, LO = RB + grow, LO - grow
        if not spikes:
            # shot e, plain liquid: six big lobes slide round the body, each swelling and sinking on its own clock (two of them dents);
            # every half beat a bulge pushes out somewhere; faster, broader waves underneath
            DV = (SM - SM.mean(0)) / np.linalg.norm(SM - SM.mean(0), axis=1, keepdims=True)
            LOB_U = [Vector(gf.normal(size=3).tolist()).normalized() for _ in range(6)]
            LOB_AX = [Vector(gf.normal(size=3).tolist()).normalized() for _ in range(6)]
            LOB_W = gf.uniform(1.8, 3.0, 6) * gf.choice((-1, 1), 6)          # how fast each lobe slides round, rad/s
            LOB_F, LOB_P = gf.uniform(3.5, 5.5, 6), gf.uniform(0, 6.3, 6)       # how fast each swells and sinks
            LOB_A = np.array([9.0, 9.0, 8.0, 8.0, -3.0, -3.0])                   # A; the last two are shallow dents, deeper ones fold the surface over
            ev_s = gf.uniform(10, 15, len(ev_t))
            W = np.stack([np.exp(-((A_ - A_[c_]) ** 2).sum(1) / (2 * s_ ** 2)) for c_, s_ in zip(ev_c, ev_s)]).astype(np.float32)
            KF = gf.normal(0, 0.07, (3, 3))
            WF = gf.uniform(4.0, 6.0, 3)
        print("ferro: %d spikes, %d patches, surface moves out up to %.1f A" % (len(tips), len(ev_t), DMAX))
    H = max(0.9, 1.25 * RB + 0.16 - P0.z)            # high enough that a guess turned any way and twitching never meets the table
    print("pivot z %.3f, reach %.3f, lowest %.3f, rest bottom %.3f, flight %.3f" % (P0.z, RB, LO, float(world[0][:, 2].min()), H))

    pivot = empty("frenzy_pivot")
    pivot.location = P0
    bpy.context.view_layer.update()
    for o in [guess, core, tail] + tail_ghosts:
        mw = o.matrix_world.copy()
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
        o.matrix_world = mw
    Mrel = np.array(pivot.matrix_world.inverted() @ guess.matrix_world)
    red_m = tail.active_material
    r_bsdf = next(n for n in red_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    tail_red = tuple(r_bsdf.inputs["Base Color"].default_value)
    tail_grey = see_through((0.55, 0.58, 0.63), 0.6)
    gh_bsdf = [next(n for n in o.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED") for o in tail_ghosts]

    rng = np.random.default_rng(11)
    QS = [Quaternion(Vector(rng.normal(size=3).tolist()).normalized(), math.radians(rng.uniform(45, 100) * rng.choice((-1, 1)))) for _ in range(64)]
    OFF = rng.uniform(-1, 1, (64, 3)) * np.array([0.12, 0.12, 0.05])
    JIT = rng.normal(0, 1, (64, 3))

    def lift(t):
        if t < POP:
            return 0.0
        if t < APEX:
            u = (t - POP) / (APEX - POP)
            return H * (1 - (1 - u) ** 3)             # shot up, slowing to a hang
        bob = 0.04 * math.sin(2 * math.pi * (t - APEX) / (4 * B_))
        if t < DOWN:
            return H + bob
        return (H + bob) * (1 - smooth((t - DOWN) / (LAND - DOWN)))      # floats down, no bounce

    def stretch(t):
        """Squash and stretch of the spring off the table: flat, then tall and thin, then a ringing back to round."""
        u = t - POP
        if u < 0.14:
            x = smooth(u / 0.14)
            return 1.0 - 0.15 * x, 0.04 + 1.31 * x
        r = math.exp(-(u - 0.14) / 0.1) * math.cos(2 * math.pi * (u - 0.14) / 0.3)
        return 1.0 - 0.15 * r, 1.0 + 0.35 * r

    def calm_at(t):
        return 1.0 - smooth((t - CALM) / (SNAP - CALM))

    def bristle(t):
        """The whole surface bristles on every beat, half as much on the off-beat: up in 0.06 s, down over a quarter second."""
        out = 0.0
        for o_, k_ in ((0.0, 1.0), (B_ / 2, 0.5)):
            u = (t - POP - o_) % B_
            out += k_ * smooth(u / 0.06) * math.exp(-max(0.0, u - 0.06) / 0.25)
        return out

    def ferro_disp(t):
        """How far each vertex moves out along its normal at time t, in mesh units: patches bulge and spike, the beat bristles everything, a slow wave runs under it all."""
        cm = calm_at(t)
        if t < POP or cm <= 0:
            return np.zeros(len(base_v))
        u = t - ev_t
        g_ = np.where(u > 0, (u / 0.2) * np.exp(1 - u / 0.2), 0.0).astype(np.float32)
        pf = np.minimum(g_ @ W, 1.3)            # spikes only stand where a patch is strong: away from them the surface stays a clean mirror
        sg = bristle(t)
        flow = np.sin(A_ @ KF.T + WF * t + PF).sum(1)
        if not spikes:
            lob = np.zeros(len(A_))
            for k_ in range(6):
                u_ = Quaternion(LOB_AX[k_], LOB_W[k_] * t) @ LOB_U[k_]
                amp = LOB_A[k_] * (0.55 + 0.45 * math.sin(LOB_F[k_] * t + LOB_P[k_]))
                lob += amp * np.exp((DV @ np.array(u_) - 1) / 0.12)
            return cm * P_S * (lob + 7 * pf * (0.8 + 0.2 * sg) + 4 * flow)
        return cm * P_S * (4 * pf + 12 * SPIKE * np.clip((pf - 0.2) / 0.8, 0, None) * (0.6 + 0.4 * sg) + 2.5 * flow)

    def ferro_verts(t):
        cm = calm_at(t)
        return SM + (base_v - SM) * smooth(1 - cm) + NV * ferro_disp(t)[:, None]

    if meta:
        # shot e: the liquid is a metaball, one ball on every residue's CA, so neighbours fuse into one smooth body that can bulge, part and run back together;
        # at rest the balls sit on their own residues and the body is close to the real surface, which takes over at the snap
        pdb_ = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]
        hv = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb_ if l[76:78].strip() != "H"])
        ACA = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb_ if l[12:16].strip() == "CA"]) - hv.mean(0)
        HOME = ACA @ R.T * P_S
        C0 = HOME.mean(0)
        DN = (HOME - C0) / np.linalg.norm(HOME - C0, axis=1, keepdims=True)
        WB = np.stack([np.exp(-((ACA - ACA[k_]) ** 2).sum(1) / (2 * s_ ** 2)) for k_, s_ in zip(gf.integers(0, len(ACA), len(ev_t)), ev_s)])
        KB, PB = gf.normal(0, 0.07, (3, 3)), gf.uniform(0, 6.3, 3)
        RAD = 6.5 * P_S
        mbd = bpy.data.metaballs.new("liquidmb")
        mbd.resolution, mbd.render_resolution, mbd.threshold = 1.2 * P_S, 0.6 * P_S, 0.6
        els = []
        for p_ in HOME:
            e_ = mbd.elements.new()
            e_.co, e_.radius = p_.tolist(), RAD
            els.append(e_)
        mbd.materials.append(grey)
        mbo = bpy.data.objects.new("liquidmb", mbd)
        sc.collection.objects.link(mbo)
        mw_ = guess.matrix_world.copy()
        mbo.parent = pivot
        mbo.matrix_parent_inverse = pivot.matrix_world.inverted()
        mbo.matrix_world = mw_
        guess.hide_render = True

        def balls(t):
            cm = calm_at(t)
            if t < POP or cm <= 0:
                return HOME.copy()
            lob = np.zeros(len(HOME))
            for k_ in range(6):
                u_ = Quaternion(LOB_AX[k_], LOB_W[k_] * t) @ LOB_U[k_]
                lob += 1.3 * LOB_A[k_] * (0.55 + 0.45 * math.sin(LOB_F[k_] * t + LOB_P[k_])) * np.exp((DN @ np.array(u_) - 1) / 0.15)
            u = t - ev_t
            pf = np.minimum(np.where(u > 0, (u / 0.2) * np.exp(1 - u / 0.2), 0.0) @ WB, 1.3)
            flow = np.sin(ACA @ KB.T + WF * t + PB)
            body = C0 + (HOME - C0) * (1 - 0.2 * cm)            # a little rounder while it is liquid
            return body + cm * P_S * (DN * (lob + 9 * pf)[:, None] + 4 * flow)

    if meta:
        reach = max(float(np.linalg.norm(balls(f_ / FPS) - C0, axis=1).max()) for f_ in range(round(POP * FPS), round(SNAP * FPS), 3)) + 1.5 * RAD
        RB = reach * guess.scale[0]
        LO = -RB
        H = max(0.9, 1.25 * RB + 0.16 - P0.z)
        print("metaball: %d balls, reaches %.3f from the middle, flight %.3f" % (len(HOME), RB, H))
    elif ferro and not spikes:            # measure how far the liquid really reaches, and fly high enough for it
        reach = max(float(np.linalg.norm(ferro_verts(f_ / FPS)[::5] - (base_v.mean(0)), axis=1).max()) for f_ in range(round(POP * FPS), round(SNAP * FPS), 3))
        RB = reach * guess.scale[0]
        LO = -RB
        H = max(0.9, 1.25 * RB + 0.16 - P0.z)
        print("liquid: reaches %.3f from the middle, flight %.3f" % (RB, H))

    def state(t):
        """Where the pivot is, how it is turned and scaled, the shape-key weights, and how solid the guess looks, at time t."""
        n = max(0, int((t - POP) / B_))
        ub = (t - POP) - n * B_
        x = smooth(ub / 0.11)                      # each new guess snaps in within 0.11 s of its beat
        calm = 1.0 - smooth((t - CALM) / (SNAP - CALM))
        ramp = smooth((t - (APEX - 0.25)) / 0.25)        # no turning until it is well clear of the table
        w = [0.0] * 8
        w[n % 8] += 1.2 * calm * x
        w[(n - 1) % 8] += 1.2 * calm * (1 - x)
        q = Quaternion().slerp(QS[(n - 1) % 64].slerp(QS[n % 64], x), calm * ramp)
        if ferro:           # one smooth, quick tumble, no snaps: the fluid does the twitching
            rv = calm * ramp * 0.9 * np.sin(np.array([1.3, 1.7, 1.1]) * t + np.array([0.3, 2.1, 4.0]))
            ang = float(np.linalg.norm(rv))
            q = Quaternion(Vector(rv.tolist()).normalized(), ang) if ang > 1e-6 else Quaternion()
        uh = (t - POP) % (B_ / 2)
        spasm = math.exp(-uh / 0.08) * (1.0 if ub < B_ / 2 else 0.5)        # a twitch on every beat, a smaller one on the off-beat
        sh = (0.03 * calm + 0.004) * spasm * np.sin(np.array([71.0, 53.0, 97.0]) * t + JIT[n % 64])
        off = (OFF[(n - 1) % 64] * (1 - x) + OFF[n % 64] * x) * calm * ramp
        pulse = 1.0 + 0.1 * calm * ramp * spasm
        if ferro:
            off = calm * ramp * np.array([0.06 * math.sin(0.9 * t + 1), 0.06 * math.sin(1.2 * t + 2), 0.03 * math.sin(1.5 * t)])
            sh = sh * 0.3
            pulse = 1.0 + 0.03 * calm * ramp * bristle(t)
        if shake:
            q = Quaternion(TILT_AX, tilt(t)) @ Quaternion((0, 0, 1), yaw(t)) @ q
        sxy, sz = stretch(t) if t >= POP else (1.0, 0.04)
        snap = 1.0 + 0.06 * math.exp(-(t - SNAP) / 0.12) * math.cos(2 * math.pi * (t - SNAP) / 0.25) if t >= SNAP else 1.0
        s = (sxy * pulse * snap, sxy * pulse * snap, sz * pulse * snap)
        z = P0.z + lift(t) + off[2] + sh[2] + (bounce(t) if shake else 0.0)
        if t < APEX:
            z = max(z, 0.003 - s[2] * LO)            # while it springs up unturned, its lowest point stays on or above the table
        loc = Vector((P0.x + off[0] + sh[0], P0.y + off[1] + sh[1], z))
        return loc, q, s, w, 1.0 - calm, n

    if shake:
        # shot d: the tail melts back into red liquid, the body shakes like a wet dog, and the liquid is flung off into the next cell, where it splats and draws into a line
        AW = P_S * guess.scale[0]                   # world units to the Angstrom
        HT = HOME[302:]                             # residues 303-346, in the guess's mesh
        coil = np.load(HERE + "frames/u_tail_2.npz")["pos"][-1].astype(float)      # the flat coil in the next cell from u_path_2.py, one point per residue, same order
        CC = coil.mean(0)
        r_t = Mrel[:3, :3] @ HT.mean(0) + Mrel[:3, 3]
        sgn = 1.0 if -r_t[1] >= 0 else -1.0         # turn the way that swings the tail towards +x, the next cell
        Y0, TP, TAU = -sgn * math.radians(50), B_, 0.3          # a full swing there and back every beat, so it turns round on every eighth note
        WIND = MELT + B_                    # the wind-up, beat 33
        TR = WHIP + 5 * B_ + TP / 4         # it lets go on the sixth swing towards the next cell, a quarter beat after 39

        def env(u):
            """How big the shake is, u after it starts: it builds a little over the first bar, then dies quickly once the tail is gone."""
            if WHIP + u < TR:
                return 0.85 + 0.15 * smooth(u / (4 * B_))
            return math.exp(-(WHIP + u - TR) / TAU)
        TILT_AX = Vector((r_t[0], r_t[1], 0.0)).normalized()     # it rocks about the line out to the tail as well, so the tail itself stays on its throw

        def tilt(t):
            u = t - WHIP
            return 0.0 if u < 0 else math.radians(18) * env(u) * math.sin(2 * math.pi * u / TP)

        def bounce(t):
            u = t - WHIP
            if u < 0:
                return -0.04 * smooth((t - WIND) / (WHIP - WIND))        # it crouches into the wind-up
            return -0.04 * math.exp(-u / 0.08) + 0.035 * env(u) * abs(math.sin(2 * math.pi * u / TP))       # and hops on every swing, down on the eighth notes
        print("tail sits %.3f %.3f off the axis; shake turns %s" % (r_t[0], r_t[1], "left" if sgn > 0 else "right"))

        def yaw(t):
            if t < MELT:
                return 0.0
            if t < WHIP:
                return Y0 * env(0.0) * smooth((t - WIND) / (WHIP - WIND))          # wind up
            u = t - WHIP
            return Y0 * env(u) * math.cos(2 * math.pi * u / TP)      # the shake: turned furthest on every eighth note
        dist_ = np.linalg.norm(HT - HOME[301], axis=1)
        order = (dist_ - dist_.min()) / (dist_.max() - dist_.min())          # 0 at the cut end, 1 at the far tip
        T_REL = TR + 0.06 * (1 - order)            # the tip lets go first, as the turn is fastest
        T_LAND = SPLAT - 0.04 + 0.1 * (1 - order)
        tj = np.random.default_rng(5)
        LAND_P = CC + (coil - CC) * 0.45 + np.c_[tj.normal(0, 0.012, (len(HT), 2)), np.zeros(len(HT))]
        SPRD = CC + (coil - CC) * 1.1 + np.c_[tj.normal(0, 0.01, (len(HT), 2)), np.zeros(len(HT))]
        R_FLY, R_PUD, R_LINE = 2.0 * RAD * guess.scale[0], 1.4 * RAD * guess.scale[0], 3.0 * AW          # fat enough in flight and on the table to stay one liquid
        Z_PUD, Z_LINE = 0.15 * R_PUD, float(coil[0, 2])
        G_ = np.array([0.0, 0.0, -9.0])

        # as it melts, the red liquid runs out of the pocket and gathers on the outside: each ball climbs away from the nearest kept residue until it is 8 A clear,
        # so it never gets closer to the kept part than it started; this is where it is flung from
        KEPT = HOME[:302]
        OUT = HT.copy()
        for _ in range(300):
            dd = np.linalg.norm(OUT[:, None] - KEPT[None], axis=2)
            nn = dd.argmin(1)
            dmin = dd[np.arange(len(OUT)), nn]
            go = dmin < 8.0 * P_S
            if not go.any():
                break
            away = OUT - KEPT[nn]
            OUT[go] += 0.25 * P_S * away[go] / np.linalg.norm(away[go], axis=1, keepdims=True)
        print("tail gathers out of the pocket: balls move up to %.1f A" % (np.linalg.norm(OUT - HT, axis=1).max() / P_S))

        def attached(t):
            loc, q, s_, _, _, _ = state(t)
            Mp = np.array(Matrix.LocRotScale(loc, q, Vector(s_))) @ Mrel
            ht = HT + (OUT - HT) * smooth((t - MELT) / (0.8 * B_))
            w_ = (np.c_[ht, np.ones(len(HT))] @ Mp.T)[:, :3]
            liq = smooth((t - MELT) / (B_ / 2))
            return w_ + liq * 2.0 * AW * np.sin(HT @ KB.T * 1.5 + 9.0 * t + PB)        # it sloshes once it is liquid

        P_REL = np.array([attached(tr_)[k_] for k_, tr_ in enumerate(T_REL)])
        V_REL = np.array([(attached(tr_ + 1e-3)[k_] - attached(tr_ - 1e-3)[k_]) / 2e-3 for k_, tr_ in enumerate(T_REL)])
        PC = np.array(state(WHIP)[0])
        aw_ = P_REL - PC
        aw_[:, 2] = 0
        V_REL += 4.0 * aw_ / np.linalg.norm(aw_, axis=1, keepdims=True)           # and it leaves outwards, away from the body, as well as round
        FL_T = T_LAND - T_REL
        LP = LAND_P.copy()
        LP[:, 2] = Z_PUD
        V_IN = (LP - P_REL) / FL_T[:, None] - 0.5 * G_ * FL_T[:, None]
        V_LAND = V_IN + G_ * FL_T[:, None]

        def tail_balls(t):
            """Where every tail ball is at time t, in world units, and its radius."""
            if t < T_REL.min():
                return attached(t), np.full(len(HT), RAD * guess.scale[0] * (1 + 0.3 * smooth((t - MELT) / B_)))
            at_ = attached(t)
            pos, rad = np.zeros_like(at_), np.zeros(len(HT))
            for k_ in range(len(HT)):
                if t < T_REL[k_]:
                    pos[k_], rad[k_] = at_[k_], R_FLY
                    continue
                if t < T_LAND[k_]:            # a smooth arc that leaves at the speed it was flung and comes down like a thrown drop
                    x_, T_ = (t - T_REL[k_]) / FL_T[k_], FL_T[k_]
                    h00, h10, h01, h11 = 2 * x_ ** 3 - 3 * x_ ** 2 + 1, x_ ** 3 - 2 * x_ ** 2 + x_, -2 * x_ ** 3 + 3 * x_ ** 2, x_ ** 3 - x_ ** 2
                    pos[k_] = h00 * P_REL[k_] + h10 * T_ * V_REL[k_] + h01 * LP[k_] + h11 * T_ * V_LAND[k_]
                    rad[k_] = R_FLY
                    continue
                u = t - T_LAND[k_]
                sp = 1 - (1 - min(1.0, u / 0.14)) ** 3            # splat: out fast, slowing
                sq = SPRD[k_].copy()
                sq[2] = Z_PUD
                p_ = LP[k_] + (sq - LP[k_]) * sp
                r_ = R_FLY + (R_PUD - R_FLY) * sp
                x_ = smooth((t - PULL) / B_)         # it draws together into the line
                tgt = coil[k_]
                pos[k_] = p_ + (tgt - p_) * x_
                rad[k_] = r_ + (R_LINE - r_) * x_
            return pos, rad

        tmb = bpy.data.metaballs.new("tailmb")
        tmb.resolution, tmb.render_resolution, tmb.threshold = 1.2 * AW, 0.4 * AW, 0.6
        tels = []
        for p_ in HT:
            e_ = tmb.elements.new()
            e_.co, e_.radius = (0.0, 0.0, 0.0), RAD * guess.scale[0]
            tels.append(e_)
        tmb.materials.append(red_m)
        tmo = bpy.data.objects.new("tailmb", tmb)
        sc.collection.objects.link(tmo)
        tmo.hide_render = True
        line_o = tube3d(coil, float(np.load(HERE + "frames/u_tail_2.npz")["tr"]), red_m, "tail_line")      # the line it ends as: shot u's tube along the coil
        line_o.hide_render = True
        T_LINE = PULL + B_

    # the clearance check: every frame, the lowest point of whatever shows must stay above the table
    lowest = 9.0
    for f in range(round(POP * FPS), FRAMES):
        t = f / FPS
        loc, q, s, w, _, _ = state(t)
        v = balls(t) if meta else ferro_verts(t) if ferro else shapes[0] + sum(wi * (shapes[i + 1] - shapes[0]) for i, wi in enumerate(w) if wi)
        Mp = np.array(Matrix.LocRotScale(loc, q, Vector(s))) @ Mrel
        lowest = min(lowest, float(((np.c_[v[::7], np.ones(len(v[::7]))] @ Mp.T)[:, 2]).min()) - (1.5 * RAD * guess.scale[0] * max(s) if meta else 0.0))
    print("lowest point over the shot: %.4f above the table" % lowest)
    assert lowest > -0.001
    if shake:
        near_, low_ = 9.0, 9.0
        worst = None
        for f in range(round(MELT * FPS), round(T_LAND.max() * FPS)):
            t = f / FPS
            loc, q, s, _, _, _ = state(t)
            Mp = np.array(Matrix.LocRotScale(loc, q, Vector(s))) @ Mrel
            kept = (np.c_[HOME[:302], np.ones(302)] @ Mp.T)[:, :3]
            pos, rad = tail_balls(t)
            fly = (t >= T_REL + 0.05) & (t < T_LAND - 0.03)            # once it has left: at the moment it lets go the cut end still touches residue 302
            if fly.any():
                dd = np.linalg.norm(pos[fly][:, None] - kept[None], axis=2).min() / AW
                if dd < near_:
                    near_, worst = float(dd), (f, int(np.flatnonzero(fly)[np.linalg.norm(pos[fly][:, None] - kept[None], axis=2).min(1).argmin()]))
                low_ = min(low_, float((pos[fly][:, 2] - 0.6 * rad[fly]).min()))
        print("flung tail: at least %.1f A from the kept part's CA (frame, ball %s), lowest %.4f above the table in flight" % (near_, worst, low_))
        assert near_ > 6.0 and low_ > 0.0

    def blend(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    dair = 5.2 * RB0 * (1.15 if shake else 1.0)          # shot d: a little further out, and aimed a little low, so the bottom of the frame stays free for the captions
    ZO = -0.07 if shake else 0.0
    AZ0 = held["az"] - (math.radians(10) if ferro else 0.0)           # shot l: S2's blue pebble sits behind the cell at about 29 degrees, so the camera starts off that line and circles away from it
    ORB = math.radians(-60 if ferro else 60)
    air = lambda t: dict(at=(P0.x, P0.y, P0.z + lift(t) + ZO), az=AZ0, el=math.radians(6), d=dair, mm=40.0)
    land = dict(at=tuple(P0), az=held["az"], el=math.radians(35), d=2.6, mm=50.0)

    def view(t):
        if t < POP:
            return held
        if t < APEX + B_:
            v = blend(held, air(t), smooth((t - POP) / (APEX + B_ - POP)))
            v["at"] = (v["at"][0], v["at"][1], P0.z + 0.9 * lift(t) + ZO)         # the camera rides up with the jump, so the shape never leaves the frame
            return v
        if t < SNAP:
            x = smooth((t - APEX - B_) / (SNAP - APEX - B_))
            v = air(t)
            return dict(v, az=v["az"] + ORB * x, el=math.radians(6 + 8 * x), d=dair * (1 - 0.15 * x))
        top = dict(air(t), az=AZ0 + ORB, el=math.radians(14), d=dair * 0.85)
        if shake:           # out and round so the body in the air and the next cell are both in frame for the throw, then down to both cells
            mx = (P0.x + float(CC[0])) / 2
            fl = dict(at=(mx, P0.y - 0.15, 0.5 * (P0.z + H)), az=held["az"] - math.radians(25), el=math.radians(16), d=4.4, mm=40.0)
            fin = dict(at=(mx, float(CC[1]) - 0.22, 0.03), az=held["az"], el=math.radians(32), d=2.8, mm=45.0)          # aimed short of the cells, so they sit above the caption band
            push = dict(fin, az=held["az"] + math.radians(7), d=2.35)
            if t < SNAP + B_ / 2:
                return top
            if t < WHIP - B_ / 4:
                return blend(top, fl, smooth((t - SNAP - B_ / 2) / (WHIP - B_ / 4 - SNAP - B_ / 2)))
            if t < SPLAT + B_ / 2:
                u = t - WHIP
                if u > 0:           # the camera takes the shake too
                    k_ = 0.02 * env(u)
                    fl = dict(fl, at=(fl["at"][0] + k_ * math.sin(61 * u), fl["at"][1] + k_ * math.sin(47 * u + 1), fl["at"][2] + k_ * math.sin(73 * u + 2)))
                return fl
            if t < beat(46):
                return blend(fl, fin, smooth((t - SPLAT - B_ / 2) / (beat(46) - SPLAT - B_ / 2)))
            return blend(fin, push, smooth((t - beat(46)) / (END - beat(46))))          # the end of W2: a slow push in on both cells
        if t < DOWN:
            return top
        return blend(top, land, smooth((t - DOWN) / (END - DOWN)))

    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])

    def update(t):
        t = t - START
        f = round(t * FPS)
        for o in dashes:
            o.hide_render = t >= POP
        forming = POP <= t < SNAP
        guess.hide_render = meta or not forming
        if meta:
            mbo.hide_render = not forming
        core.hide_render = tail.hide_render = t < SNAP
        pivot.animation_data_clear()
        for s_ in (-0.25, 0.25):            # keyed either side of the frame, so the shutter sees the motion
            loc, q, s, _, _, _ = state((f + s_) / FPS)
            pivot.location, pivot.rotation_quaternion, pivot.scale = loc, q, s
            for p_ in ("location", "rotation_quaternion", "scale"):
                pivot.keyframe_insert(p_, frame=f + s_)
        _, _, _, w, solid, n = state(t)
        for k_, wi in zip(keys, w):
            k_.value = wi
        if ferro:           # black mirror fluid, turning Klein blue and less glossy as it settles into the real shape
            if forming and meta:
                rr = RAD * (1 + 0.5 * calm_at(t))         # fatter balls while it is liquid fuse into one smooth body; back to size as it settles
                for e_, p_ in zip(els, balls(t)):
                    e_.co, e_.radius = p_.tolist(), rr
            elif forming:
                me.vertices.foreach_set("co", ferro_verts(t).astype(np.float32).ravel())
                me.update()
            g_bsdf.inputs["Alpha"].default_value = 1.0
            g_bsdf.inputs["Base Color"].default_value = (*lerp((0.004, 0.004, 0.005), P.KLEIN, solid ** 1.5), 1)
            g_bsdf.inputs["Roughness"].default_value = 0.05 + 0.29 * solid
        else:
            g_bsdf.inputs["Alpha"].default_value = 0.55 + 0.4 * solid
            g_bsdf.inputs["Base Color"].default_value = (*lerp((0.42, 0.44, 0.48), P.KLEIN, solid), 1)
        red = t >= RED
        tail.active_material = red_m if red else tail_grey
        pulse = 0.5 + 0.5 * math.cos(2 * math.pi * (t - RED) / B_) if red else 0.0
        r_bsdf.inputs["Emission Color"].default_value = (*tail_red[:3], 1)
        r_bsdf.inputs["Emission Strength"].default_value = 0.6 * pulse
        m_ = int((t - RED) / B_) if red else -1
        for i, (o, b_) in enumerate(zip(tail_ghosts, gh_bsdf)):          # the tail never settles: one of its swings flickers on every beat
            o.hide_render = not (red and i == m_ % 4) or (shake and t >= MELT)
            b_.inputs["Alpha"].default_value = 0.45 * math.exp(-((t - RED) - m_ * B_) / 0.18) if red else 0.0
        if shake:
            tail.hide_render = tail.hide_render or t >= MELT
            tmo.hide_render = not MELT <= t < T_LINE
            line_o.hide_render = t < T_LINE
            if t >= MELT:
                pos, rad = tail_balls(t)
                for e_, p_, r_ in zip(tels, pos, rad):
                    e_.co, e_.radius = p_.tolist(), float(r_)
    return update

def shot_l(sc, sky):
    """W2 motion as a ferrofluid (the director's note of 11-04 17:58: smoother, like ferrofluid, a lump of clay pushing out here and there): shot j's jump, flight and landing, but the guess is one black mirror fluid whose surface never stops moving: patches gather and grow spikes, two a beat, the whole surface bristles on the beat, a slow wave runs under it, it tumbles smoothly; as it calms it turns Klein blue and sinks back into the real shape. Run: blender -b -P bl_inserts.py -- l <out dir> 0 1054 16 0.5 2"""
    return shot_j(sc, sky, ferro=True)


def shot_e(sc, sky):
    """W2 motion as a plain liquid (the director's note of 11-04 18:58: not spikes, a liquid changing fast and smoothly): shot l's black mirror fluid without the spikes, built as a metaball with one ball per residue: big lobes slide round it, swell and sink, a bulge pushes out on every half beat, broad waves run underneath, drops can part and run back; it turns Klein blue and settles into the real CDK20. Run: blender -b -P bl_inserts.py -- e <out dir> 0 1054 16 0.5 2"""
    return shot_j(sc, sky, ferro=True, spikes=False, meta=True)


def shot_d(sc, sky):
    """W2 motion with the tail shaken off (the director's pick of 11-04 20:45, way 3): shot e's liquid up to the snap and the red tail flickering; beat 30 the tail melts back into red liquid and the body winds up; beat 31 it shakes like a wet dog, about five turns a second dying away, and the red liquid is flung off in a streak, the tip first; beat 32 it splats in the next cell (cell 23) and spreads; beat 33 it draws together into a red line, the flat coil from u_path_2.py; beats 32-36 the blue body, residues 1-302, floats down into its cell with its pocket open. The flight is a smooth arc from the speed it was flung at to a falling drop, checked every frame clear of the kept part and of the table. Version 3 (11-04 22:05): on the song itself, 123.477 BPM, and 13 bars long (25.3 s, all of W2), the last bars a slow push in on both cells; the camera leaves the bottom of the frame for the rhyming captions (音乐/W2_押韵字幕.md). Version 4 (11-04 22:50, the tail went too fast): it melts on beat 32, winds up on 33, shakes from 34 with a turn on every eighth note, lets go a quarter beat after 39, splats on the downbeat of 40 and draws into the line on 41-42; the body comes down 40-44. Run: blender -b -P bl_inserts.py -- d <out dir> 0 1516 16 0.5 2"""
    return shot_j(sc, sky, ferro=True, spikes=False, meta=True, shake=True)




# 4-01 (07:17-07:43), B's voice-over, as the sentences are now timed (0.39 s a word); the real recording comes on 11-12 and moves these
I_VO = dict(start=0.0, ai=4.4, chain=7.6, order=13.6, learned=16.8, sure=20.0, end=26.0)
# 4-02 (07:43-08:00), the same, at 0.45 s a word
I2_VO = dict(before=0.0, now=3.1, downloaded=3.6, first=9.0, end=17.0)
# 4-03 (08:00-08:18), 44 words at 0.41 s a word
I3_VO = dict(closer=0.0, tail=1.5, model=6.6, block=10.4, trust=14.0, end=18.0)



def shot_i2(sc, sky):
    """4-02 (07:43-08:00, B's voice-over), straight on from shot i: the glass body fills back in, the letters lie down, the coil's blocks melt back into the red line, and the
    camera climbs over S3's whole grid, where only four of 45 cells hold a shape someone measured in a lab ("before"); then down to CDK20's cell, which now holds the free
    prediction ("now"), and in on it for the paper's "first time". Labels are laid on in Remotion (S402) at the screen spots printed here. Run: blender -b -P bl_inserts.py -- i2 <out dir> 0 1019 16 0.5 2"""
    return shot_i(sc, sky, part=2)


def shot_i3(sc, sky):
    """4-03 (08:00-08:18, B's voice-over), straight on from shot i2: "But look closer." The coil in the next cell comes up as its blocks again, mostly red; a see-through red
    copy of the tail peels off it and runs back along its own path to where the model put it, across the pocket; the camera goes in over the pocket and one block, Arg305,
    lights up inside it. Labels are laid on in Remotion (S403) at the screen spots printed here. Run: blender -b -P bl_inserts.py -- i3 <out dir> 0 1079 16 0.5 2"""
    return shot_i(sc, sky, part=3)


def shot_i4(sc, sky):
    """Back on the table after 4-05 (B on camera: "They cut the tail off"), the first 3.5 s of 4-06's voice-over: the see-through tail breaks into its own 44 blocks, which drift
    straight out from the body and shrink away, the tail's end first; the camera pulls back to the body and the real coil in the next cell. Run: blender -b -P bl_inserts.py -- i4 <out dir> 0 209 16 0.5 2"""
    return shot_i(sc, sky, part=4)

def smooth_np(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def rounded_block(n=4, p=6.0):
    """A unit block with rounded edges (a superellipsoid from a gridded cube, shared corners), as vertices and quads facing out."""
    ids, verts, quads = {}, [], []

    def vid(v):
        key = tuple(np.round(v, 6))
        if key not in ids:
            ids[key] = len(verts)
            verts.append(v)
        return ids[key]
    g = np.linspace(-1, 1, n + 1)
    for ax in range(3):
        for sg in (-1, 1):
            for i in range(n):
                for j in range(n):
                    q = []
                    for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                        v = np.zeros(3)
                        v[ax], v[(ax + 1) % 3], v[(ax + 2) % 3] = sg, g[a], g[b]
                        q.append(vid(v))
                    quads.append(q if sg > 0 else q[::-1])
    V = np.array(verts)
    return V / ((np.abs(V) ** p).sum(1, keepdims=True) ** (1 / p)), np.array(quads)


def shot_i(sc, sky, part=1):
    """4-01 (07:17-07:43, B's voice-over), straight on from W2's last frame (shot d): the blue body in its cell, the red coil in the next. The camera eases back to both cells.
    "A chain of building blocks": the body's surface turns to glass and shows the real chain inside, one small block on every residue's CA, strung on an ink thread; the red coil
    turns into its 44 blocks the same way. "The order of the blocks is the sequence": a light runs along the chain from residue 1, and the first 24 letters of CDK20's sequence
    stand up on the table one by one as it passes their blocks. "How sure it is about each part": every block takes its own AlphaFold DB v6 confidence, Klein blue for 70 and up,
    red below 70 (11 of the kept 302 are red, 4 of the tail's 44 are blue: the colours are the real per-residue values). The structure is AlphaFold DB v6; the blocks and the light
    are drawn. Times are in I_VO. Run: blender -b -P bl_inserts.py -- i <out dir> 0 1559 16 0.5 2"""
    global START
    shot_v(sc, sky)
    START = {1: 437.0, 2: 463.0, 3: 480.0, 4: 505.0}[part]
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    ob = bpy.data.objects
    for o in ob:
        if o.name.split(".")[0] in ("letter", "guess", "tail_guess", "tail_cut", "tail"):
            o.hide_render = True
        if o.parent and o.parent.name == "keyhole":
            o.hide_render = True
    core, small = ob["core"], ob["cdk20_small"]
    core.hide_render = False
    sky(0.2)
    V = I_VO
    cx, cy = cell_at(22)
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    R = np.array(q0.to_matrix())
    hv = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H"])
    cal = [l for l in pdb if l[12:16].strip() == "CA"]
    ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in cal])
    plddt = np.array([float(l[60:66]) for l in cal])
    AA = dict(ALA="A", ARG="R", ASN="N", ASP="D", CYS="C", GLN="Q", GLU="E", GLY="G", HIS="H", ILE="I", LEU="L", LYS="K", MET="M", PHE="F", PRO="P", SER="S", THR="T", TRP="W", TYR="Y", VAL="V")
    seq = "".join(AA[l[17:20]] for l in cal)
    HOME = (ca - hv.mean(0)) @ R.T * P_S          # the CAs in the model's mesh, as in shot d
    bpy.context.view_layer.update()
    Mc = np.array(core.matrix_world)
    P0 = Vector(((np.c_[full["verts"] @ R.T * P_S, np.ones(len(full["verts"]))] @ Mc.T)[:, :3]).mean(0).tolist())
    AW = P_S * small.scale[0]                      # world units to the Angstrom
    npz = np.load(HERE + "frames/u_tail_2.npz")
    coil = npz["pos"][-1].astype(float)            # the red coil W2 ends on, one point per residue 303-346, in world units
    CC = coil.mean(0)
    print("4-01: body at %.3f %.3f %.3f, coil at %.3f %.3f, %d red of the kept 302, %d blue of the tail's 44, AW %.5f" % (*P0, CC[0], CC[1], (plddt[:302] < 70).sum(), (plddt[302:] >= 70).sum(), AW))

    # the materials: glass the body and the coil can fade to, ink for the thread, the blocks coloured per vertex
    c_bsdf = next(n for n in core.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    red_line = P.gloss(P.RED, 0.22, 0.7)
    l_bsdf = next(n for n in red_line.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    tube3d(coil, float(npz["tr"]), red_line, "tail_line")
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    m, nt, out_ = gk._mat("blocks")
    bb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    at_c, at_g = nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeAttribute")
    at_c.attribute_name, at_g.attribute_name = "col", "glow"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2.5
    nt.links.new(at_c.outputs["Color"], bb.inputs["Base Color"])
    nt.links.new(at_c.outputs["Color"], bb.inputs["Emission Color"])
    nt.links.new(at_g.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs[0], bb.inputs["Emission Strength"])
    bb.inputs["Roughness"].default_value = 0.3
    bb.inputs["Coat Weight"].default_value = 0.5
    nt.links.new(bb.outputs[0], out_.inputs["Surface"])

    # the blocks: one on every CA, its long side along the chain; the kept 302 in the model's mesh, the tail's 44 on the coil in world units
    UB, UQ = rounded_block()

    def frames_along(pts):
        out = []
        for k in range(len(pts)):
            t_ = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]
            t_ = t_ / np.linalg.norm(t_)
            a_ = np.array([0.0, 0.0, 1.0]) if abs(t_[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
            u_ = np.cross(t_, a_)
            u_ /= np.linalg.norm(u_)
            out.append(np.stack([t_ * 1.15, u_, np.cross(t_, u_)], 1))     # a little longer along the chain
        return out
    HALF = 1.2                                      # A: blocks about 2.4 A across on a chain 3.8 A a step, so the thread shows between them
    tail_pts = coil.copy()
    tail_pts[:, 2] = np.maximum(tail_pts[:, 2], HALF * 1.2 * AW + 0.002)          # resting on the table, not in it
    sets = [(HOME[:302], frames_along(HOME[:302]), HALF * P_S, True), (tail_pts, frames_along(tail_pts), HALF * AW, False)]
    blk = []
    for pts, frs, h_, in_model in sets:
        me = bpy.data.meshes.new("blocks")
        loc = np.concatenate([UB @ F.T for F in frs]) * h_
        cen = np.repeat(pts, len(UB), 0)
        me.from_pydata((cen + loc).tolist(), [], np.concatenate([UQ + k * len(UB) for k in range(len(pts))]).tolist())
        me.attributes.new("col", "FLOAT_COLOR", "POINT")
        me.attributes.new("glow", "FLOAT", "POINT")
        me.materials.append(m)
        o = bpy.data.objects.new("blocks", me)
        sc.collection.objects.link(o)
        B.smooth(o)
        if in_model:
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion, o.scale, o.location = core.rotation_quaternion, core.scale, core.location
        blk.append((o, me, cen, loc, len(pts)))
    thread = tube3d(HOME[:302], 0.35 * P_S, ink, "thread")
    thread.rotation_mode = "QUATERNION"
    thread.rotation_quaternion, thread.scale, thread.location = core.rotation_quaternion, core.scale, core.location
    thread_t = tube3d(tail_pts, 0.35 * AW, ink, "thread")

    # when each block comes in, lights up and takes its colour; residue k of 346
    k_all = np.arange(346)
    # the flat coil first ("a chain of building blocks"), then the folded body ("that folds into a 3D shape")
    t_pop = np.where(k_all < 302, V["chain"] + 3.0 + 2.0 * k_all / 301, V["chain"] + 0.5 + 1.0 * (k_all - 302) / 43)
    NL = 24
    t_lit = np.where(k_all < NL, V["order"] + 0.2 + 2.0 * k_all / NL, V["order"] + 2.2 + 1.0 * (k_all - NL) / (345 - NL))
    t_col = V["sure"] + 0.4 + 2.2 * k_all / 345
    BONE_C = np.array([0.80, 0.78, 0.72])
    sure = np.where(plddt[:, None] >= 70, np.array(P.KLEIN), np.array(P.RED))

    # the sequence: CDK20's first 24 letters, standing in the bare band of table in front of both cells (no rim there), facing the camera
    font = bpy.data.fonts.load(HERE + "../../../../../remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf")
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    letters = []
    band_y = cy - 0.42
    x0, x1 = cx - 0.40, float(CC[0]) + 0.40
    for i in range(NL + 1):
        cu = bpy.data.curves.new("letter", "FONT")
        cu.body, cu.font, cu.size, cu.extrude = (seq[i] if i < NL else "…"), font, 0.1, 0.008
        cu.align_x, cu.align_y = "CENTER", "BOTTOM"
        o = bpy.data.objects.new("letter", cu)
        sc.collection.objects.link(o)
        cu.materials.append(ink)
        o.location = (x0 + (x1 - x0) * i / NL, band_y, 0.0)
        o.rotation_euler = (math.pi / 2, 0, held["az"])
        letters.append(o)

    # the camera: from W2's last frame (shot d's slow push) back to both cells, in on the body for the chain and the letters, round it, and back out for the colours
    mx = (P0.x + float(CC[0])) / 2
    fin = dict(at=(mx, float(CC[1]) - 0.22, 0.03), az=held["az"], el=math.radians(32), d=2.8, mm=45.0)
    v0 = dict(fin, az=held["az"] + math.radians(7), d=2.35)
    both = dict(at=(mx, cy - 0.10, 0.12), az=held["az"] + math.radians(3), el=math.radians(25), d=2.7, mm=45.0)
    flat = dict(at=(float(CC[0]), float(CC[1]) - 0.04, 0.02), az=held["az"] + math.radians(8), el=math.radians(38), d=1.35, mm=45.0)
    chain = dict(at=(P0.x + 0.05, P0.y - 0.10, 0.6 * P0.z), az=held["az"] - math.radians(12), el=math.radians(22), d=2.0, mm=45.0)
    order = dict(at=(P0.x + 0.40, cy - 0.28, 0.08), az=held["az"] - math.radians(6), el=math.radians(24), d=2.5, mm=45.0)
    learned = dict(order, at=(P0.x + 0.2, P0.y - 0.15, 0.6 * P0.z), az=held["az"] + math.radians(10), el=math.radians(24), d=2.4)
    sure_v = dict(both, az=held["az"] + math.radians(1), el=math.radians(28), d=2.9)
    keys = [(0.0, v0), (4.2, both), (V["chain"] - 0.3, both), (V["chain"] + 1.2, flat), (V["chain"] + 2.6, flat), (V["chain"] + 4.6, chain), (V["order"], chain),
            (V["order"] + 1.6, order), (V["learned"] + 0.4, order), (V["learned"] + 3.0, learned), (V["sure"], learned), (V["sure"] + 2.6, sure_v), (V["end"], dict(sure_v, d=2.75))]

    if part == 2:
        # 4-02: up over the whole grid, where only four cells hold a shape someone measured in a lab (S3's grid), then back down to CDK20's cell, which now holds the prediction
        V2 = I2_VO
        grid = dict(at=(cx + 0.45, cy - 0.15, 0.0), az=held["az"], el=math.radians(54), d=12.0, mm=45.0)
        cell = dict(at=(cx + 0.15, cy - 0.05, 0.08), az=held["az"] - math.radians(4), el=math.radians(40), d=3.4, mm=45.0)
        close = dict(at=(P0.x, P0.y - 0.05, 0.8 * P0.z), az=held["az"] - math.radians(10), el=math.radians(27), d=2.45, mm=45.0)
        keys = [(0.0, keys[-1][1]), (V2["now"] - 0.2, grid), (V2["downloaded"] + 1.4, grid), (V2["first"] - 0.6, cell), (V2["end"], close)]

    if part in (3, 4):
        # 4-03: "but look closer". The coil's blocks come up again in their own colours (the tail: mostly not sure); a see-through red copy of the tail peels off the coil and
        # runs back along its own path (u_tail_2.npz, the path W2's tail took out to the coil, played backwards; every frame of it was checked clear of the body) to where the
        # model put it, across the pocket; then one block, Arg305, lights up inside the pocket. The ghost and the block are drawn; where they sit is the AlphaFold DB v6 model.
        V3 = I3_VO
        ut = np.load(HERE + "frames/u_tail_2.npz")
        UPOS = ut["pos"].astype(float)
        ghost_l, ghost_s = see_through(P.RED, 0.0), see_through(P.RED, 0.0)
        gl_bsdf = next(n for n in ghost_l.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        gs_bsdf = next(n for n in ghost_s.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g_line = tube3d(UPOS[-1], float(ut["tr"]), ghost_l, "ghost_line")
        g_tail = ob["tail"]                    # shot v's tail surface, 303-346, where the model has it
        assert g_tail.type == "MESH"
        g_tail.data.materials[0] = ghost_s
        sc305 = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb
                          if int(l[22:26]) == 305 and l[12:16].strip() not in ("N", "CA", "C", "O") and l[76:78].strip() != "H"])
        A305 = (sc305.mean(0) - hv.mean(0)) @ R.T * P_S          # Arg305's side chain, the part that reaches into the pocket, in the model's mesh
        F305 = frames_along(HOME[:306])[304]
        me305 = bpy.data.meshes.new("arg305")
        L305 = (UB @ F305.T) * HALF * 1.6 * P_S          # a little bigger than 4-01's blocks, so the one block reads from here
        me305.from_pydata((A305 + L305).tolist(), [], UQ.tolist())
        me305.attributes.new("col", "FLOAT_COLOR", "POINT")
        me305.attributes.new("glow", "FLOAT", "POINT")
        me305.attributes["col"].data.foreach_set("color", np.tile([*P.RED, 1.0], len(UB)).astype(np.float32))     # pLDDT 58: red, as in 4-01
        me305.materials.append(m)
        arg = bpy.data.objects.new("arg305", me305)
        sc.collection.objects.link(arg)
        B.smooth(arg)
        arg.rotation_mode = "QUATERNION"
        arg.rotation_quaternion, arg.scale, arg.location = core.rotation_quaternion, core.scale, core.location
        bpy.context.view_layer.update()
        mw = small.matrix_world
        mid = mw @ Vector((np.asarray(full["pocket"]) @ R.T * P_S).tolist())
        way = (mw.to_3x3() @ Vector((R @ np.asarray(full["mouth"])).tolist())).normalized()
        az_in = math.atan2(way.x, -way.y)
        az_in += round((held["az"] - az_in) / (2 * math.pi)) * 2 * math.pi
        W305 = arg.matrix_world @ Vector(A305.tolist())
        side = W305 - P0          # the pocket's side of the body is where Arg305 sits: the camera goes round to that side
        print("4-03: mouth az %.0f, Arg305 side az %.0f" % (math.degrees(az_in), math.degrees(math.atan2(side.x, -side.y))))
        az_in = math.atan2(side.x, -side.y)
        az_in += round((held["az"] - az_in) / (2 * math.pi)) * 2 * math.pi
        print("4-03: Arg305 side chain %.1f A from the pocket's centre" % (np.linalg.norm(A305 - np.asarray(full["pocket"]) @ R.T * P_S) / P_S))
        close = dict(at=(P0.x, P0.y - 0.05, 0.8 * P0.z), az=held["az"] - math.radians(10), el=math.radians(27), d=2.45, mm=45.0)        # where 4-02 ends
        pair = dict(at=((P0.x + float(CC[0])) / 2 + 0.08, float(CC[1]) - 0.02, 0.12), az=held["az"] + math.radians(4), el=math.radians(30), d=2.6, mm=45.0)
        pocket = dict(at=tuple(lerp(tuple(mid), tuple(W305), 0.5)[:2]) + (float(lerp(tuple(mid), tuple(W305), 0.5)[2]) + 0.12,), az=az_in, el=math.radians(46), d=2.2, mm=50.0)
        inside = dict(pocket, d=1.95)          # the whole body stays clear of the corner tag
        keys = [(0.0, close), (1.4, dict(close, d=2.25)), (V3["tail"] + 0.6, pair), (V3["model"] + 0.2, pair), (V3["model"] + 3.4, pocket),
                (V3["block"] + 0.2, pocket), (V3["block"] + 2.8, inside), (V3["end"], dict(inside, d=1.9))]
    if part == 4:
        # after 4-05 ("they cut the tail off"): the ghost breaks into its own 44 blocks (on its CAs, in their colours), each drifts straight out from the body's centre and
        # shrinks away, the tail's end first; the camera pulls back to both cells, where the real coil still lies
        keys = [(0.0, keys[-1][1]), (0.5, keys[-1][1]), (3.4, dict(pair, d=2.7))]
        GH = HOME[302:]
        ghost_frs = frames_along(HOME[300:])[2:]
        me_g = bpy.data.meshes.new("ghost_blocks")
        LG = np.concatenate([UB @ F.T for F in ghost_frs]) * HALF * P_S
        CG = np.repeat(GH, len(UB), 0)
        me_g.from_pydata((CG + LG).tolist(), [], np.concatenate([UQ + k * len(UB) for k in range(44)]).tolist())
        me_g.attributes.new("col", "FLOAT_COLOR", "POINT")
        me_g.attributes.new("glow", "FLOAT", "POINT")
        me_g.attributes["col"].data.foreach_set("color", np.c_[np.repeat(sure[302:], len(UB), 0), np.ones(44 * len(UB))].astype(np.float32).ravel())
        me_g.materials.append(m)
        gb = bpy.data.objects.new("ghost_blocks", me_g)
        sc.collection.objects.link(gb)
        B.smooth(gb)
        gb.rotation_mode = "QUATERNION"
        gb.rotation_quaternion, gb.scale, gb.location = core.rotation_quaternion, core.scale, core.location
        core_c = (np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb if l[76:78].strip() != "H" and int(l[22:26]) <= 302]).mean(0) - hv.mean(0)) @ R.T * P_S
        away = GH - core_c
        away /= np.linalg.norm(away, axis=1)[:, None]
        t_go = 0.45 + 0.6 * (43 - np.arange(44)) / 43          # the tail's end goes first, Arg305's block (k 2) among the last

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return keys[-1][1]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])
    if part == 2:          # where the labels go: the measured shapes and CDK20's cell on screen, for the Remotion layer
        from bpy_extras.object_utils import world_to_camera_view
        spots = dict(cdk20=(cx, cy, 0.1), **{"seen%d" % i: (*cell_at(i), 0.1) for i in SEEN})
        for f in (round((I2_VO["now"] + 0.5) * FPS), round(I2_VO["downloaded"] + 1.0) * round(FPS), round((I2_VO["first"] + 1.0) * FPS), FRAMES - 1):
            sc.frame_set(f)
            print("4-02 frame %d:" % f, ", ".join("%s %.0f %.0f" % (k, *(lambda q: (q.x * 1920, (1 - q.y) * 1080))(world_to_camera_view(sc, c, Vector(p_)))) for k, p_ in spots.items()))
    if part == 3:          # the coil, the pocket and Arg305 on screen, for the Remotion layer (S403)
        from bpy_extras.object_utils import world_to_camera_view
        spots = dict(coil=(float(CC[0]), float(CC[1]), 0.03), pocket=tuple(mid), arg305=tuple(W305))
        for tt in (V3["tail"] + 3.0, V3["model"] + 3.6, V3["block"] + 1.0, V3["trust"] + 2.0, V3["end"] - 0.02):
            f = round(tt * FPS)
            sc.frame_set(f)
            print("4-03 frame %d:" % f, ", ".join("%s %.0f %.0f" % (k, *(lambda q: (q.x * 1920, (1 - q.y) * 1080))(world_to_camera_view(sc, c, Vector(p_)))) for k, p_ in spots.items()))

    def update3(t):
        c_bsdf.inputs["Alpha"].default_value = 1.0
        thread.hide_render = True
        for o in letters:
            o.hide_render = True
        blk[0][0].hide_render = True
        # the coil's 44 blocks come up again in their colours, then melt back into the line before the ghost leaves it
        up = smooth((t - V3["tail"] - 0.7) / 0.6) * (1 - smooth((t - V3["model"] + 0.5) / 0.6))
        l_bsdf.inputs["Alpha"].default_value = 1 - 0.84 * up
        thread_t.hide_render = bool(up <= 0)
        k = np.arange(44)
        pop = np.clip((t - (V3["tail"] + 0.8 + 0.8 * k / 43)) / 0.25, 0, 1)
        pop = (1 - (1 - pop) ** 3) * (1 - smooth((t - V3["model"] + 0.5) / 0.6))
        o, me, cen, loc, n = blk[1]
        nv = len(UB)
        me.vertices.foreach_set("co", (cen + loc * np.maximum(np.repeat(pop, nv)[:, None], 1e-3)).astype(np.float32).ravel())
        me.attributes["col"].data.foreach_set("color", np.c_[np.repeat(sure[302:], nv, 0), np.ones(n * nv)].astype(np.float32).ravel())
        me.attributes["glow"].data.foreach_set("value", np.zeros(n * nv, np.float32))
        me.update()
        o.hide_render = bool(pop.max() <= 0)
        # the ghost: off the coil and back along the path to the model's place for it, then the tail's own surface, see-through, across the pocket
        g = smooth((t - V3["model"] - 0.2) / 2.8)
        pos = UPOS[round((1 - g) * (len(UPOS) - 1))]
        for q, p_ in zip(g_line.data.splines[0].points, pos):
            q.co = (*p_.tolist(), 1)
        a_line = 0.5 * smooth((t - V3["model"] - 0.2) / 0.3) * (1 - smooth((t - V3["model"] - 3.0) / 0.6))
        gl_bsdf.inputs["Alpha"].default_value = a_line
        g_line.hide_render = bool(a_line <= 0.005)
        flash = math.exp(-((t - V3["trust"] - 2.7) / 0.35) ** 2)          # "a blocked door"
        a_tail = 0.34 * smooth((t - V3["model"] - 2.7) / 0.6) * (1 - 0.4 * smooth((t - V3["block"] - 0.1) / 0.5)) + 0.3 * flash
        gs_bsdf.inputs["Alpha"].default_value = a_tail
        g_tail.hide_render = bool(a_tail <= 0.005)
        # Arg305: one block, in the pocket
        u = min(1.0, max(0.0, (t - V3["block"] - 0.3) / 0.25))
        u = 1 - (1 - u) ** 3
        me305.vertices.foreach_set("co", (A305 + L305 * max(u, 1e-3)).astype(np.float32).ravel())
        glow = (0.5 + 1.2 * math.exp(-max(t - V3["block"] - 0.3, 0) / 0.6) + 0.8 * flash) * u
        me305.attributes["glow"].data.foreach_set("value", np.full(len(UB), glow, np.float32))
        me305.update()
        arg.hide_render = bool(u <= 0)

    def update4(t):
        c_bsdf.inputs["Alpha"].default_value, l_bsdf.inputs["Alpha"].default_value = 1.0, 1.0
        for o in letters + [thread, thread_t, blk[0][0], blk[1][0], g_line]:
            o.hide_render = True
        flash = 0.0
        a_tail = 0.34 * 0.6 * (1 - smooth((t - 0.1) / 0.45))
        gs_bsdf.inputs["Alpha"].default_value = a_tail
        g_tail.hide_render = bool(a_tail <= 0.005)
        u = 1 - smooth((t - 0.1) / 0.3)
        me305.vertices.foreach_set("co", (A305 + L305 * max(u, 1e-3)).astype(np.float32).ravel())
        me305.attributes["glow"].data.foreach_set("value", np.full(len(UB), 0.5 * u, np.float32))
        me305.update()
        arg.hide_render = bool(u <= 0)
        inn = smooth_np((t - 0.05) / 0.3)
        go = np.clip((t - t_go) / 1.1, 0, 1)
        size = inn * (1 - smooth_np(go))
        drift = (go ** 1.5)[:, None] * 9.0 * P_S * away          # out to 9 A from where it sat
        nv = len(UB)
        me_g.vertices.foreach_set("co", (np.repeat(GH + drift, nv, 0) + LG * np.maximum(np.repeat(size, nv)[:, None], 1e-3)).astype(np.float32).ravel())
        me_g.attributes["glow"].data.foreach_set("value", np.repeat(0.6 * (1 - go), nv).astype(np.float32))
        me_g.update()
        gb.hide_render = bool(size.max() <= 0)

    def update(t):
        t = t - START
        if part == 3:
            return update3(t)
        if part == 4:
            return update4(t)
        back = 0.0
        if part == 2:          # it starts as 4-01 ends; the glass fills back in, the letters lie down and the coil's blocks melt back into the line
            back, t = smooth((t - 0.3) / 1.4), I_VO["end"] + t
        c_bsdf.inputs["Alpha"].default_value = 1 - 0.84 * smooth((t - V["chain"] - 2.6) / 1.2) * (1 - back)            # the surface to glass: 1 to 0.16
        l_bsdf.inputs["Alpha"].default_value = 1 - 0.84 * smooth((t - V["chain"] - 0.2) / 1.0) * (1 - back)
        thread.hide_render = bool(t < V["chain"] + 2.9 or back >= 1)
        thread_t.hide_render = bool(t < V["chain"] + 0.4 or back >= 1)
        pop = np.clip((t - t_pop) / 0.25, 0, 1)
        pop = (1 - (1 - pop) ** 3) * (1 - back)
        lit = np.where(t >= t_lit, np.exp(-np.maximum(t - t_lit, 0) / 0.35), 0.0)
        cm = smooth_np((t - t_col) / 0.3)
        col = BONE_C[None] * (1 - cm[:, None]) + sure * cm[:, None]
        for (o, me, cen, loc, n), ks in zip(blk, (slice(0, 302), slice(302, 346))):
            nv = len(UB)
            s_ = np.repeat(pop[ks], nv)[:, None]
            me.vertices.foreach_set("co", (cen + loc * np.maximum(s_, 1e-3)).astype(np.float32).ravel())
            cc_ = np.c_[np.repeat(col[ks], nv, 0), np.ones(n * nv)]
            me.attributes["col"].data.foreach_set("color", cc_.astype(np.float32).ravel())
            me.attributes["glow"].data.foreach_set("value", np.repeat(lit[ks], nv).astype(np.float32))
            me.update()
            o.hide_render = bool(pop[ks].max() <= 0)
        for i, o in enumerate(letters):
            ti = t_lit[i] if i < NL else t_lit[NL] + 0.1
            u = min(1.0, max(0.0, (t - ti) / 0.18))
            u = (1 - (1 - u) ** 3) * (1 - smooth(back * 1.4))
            o.hide_render = bool(u <= 0)
            o.scale = (1.0, max(u, 1e-3), 1.0)            # it stands up out of the table
    return update


# 4-06 (08:25-08:43, A) and 4-07 (08:43-09:10, A), on the 4-06 clock, at about 0.43 and 0.48 s a word until the recording comes on 11-12
LP_VO = dict(mind=0.0, think=3.0, imagine=6.4, make=7.8, test=8.7, fails=9.6, tweak=10.5, again=11.4, every=12.6, ai=18.0, chem=23.4, invent=31.0, hours=39.2, end=45.0)
LP_T0 = 3.5             # the shot starts where shot i4 ends, 3.5 s into 4-06


def attr_mat(name, mult):
    """Colour and glow per vertex, like 4-01's blocks."""
    m, nt, out_ = gk._mat(name)
    bb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    at_c, at_g = nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeAttribute")
    at_c.attribute_name, at_g.attribute_name = "col", "glow"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = mult
    nt.links.new(at_c.outputs["Color"], bb.inputs["Base Color"])
    nt.links.new(at_c.outputs["Color"], bb.inputs["Emission Color"])
    nt.links.new(at_g.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs[0], bb.inputs["Emission Strength"])
    bb.inputs["Roughness"].default_value = 0.35
    nt.links.new(bb.outputs[0], out_.inputs["Surface"])
    return m


def attr_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(verts).tolist(), [], [list(map(int, f)) for f in faces])          # faces may differ in size
    me.attributes.new("col", "FLOAT_COLOR", "POINT")
    me.attributes.new("glow", "FLOAT", "POINT")
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    B.smooth(o)
    return o, me


def set_attr(me, col, glow):
    n = len(me.vertices)
    me.attributes["col"].data.foreach_set("color", np.c_[np.broadcast_to(np.asarray(col, np.float32), (n, 3)), np.ones(n)].astype(np.float32).ravel())
    me.attributes["glow"].data.foreach_set("value", np.broadcast_to(np.asarray(glow, np.float32), (n,)).astype(np.float32).copy())


def ring_geo(r, rr, n=64, m=8):
    """A torus about z: its vertices, faces and each vertex's angle round the ring."""
    a = np.repeat(np.linspace(0, 2 * np.pi, n, endpoint=False), m)
    b = np.tile(np.linspace(0, 2 * np.pi, m, endpoint=False), n)
    v = np.c_[(r + rr * np.cos(b)) * np.cos(a), (r + rr * np.cos(b)) * np.sin(a), rr * np.sin(b)]
    f = [(i * m + j, i * m + (j + 1) % m, ((i + 1) % n) * m + (j + 1) % m, ((i + 1) % n) * m + j) for i in range(n) for j in range(m)]
    return v, np.array(f), a, b


def shot_lp(sc, sky):
    """4-06 and 4-07 (08:28.5-09:10, A's voice-over), straight on from shot i4. The camera leaves CDK20's cell for the empty cell in front of it (31), where a small turntable is
    set down with five things from the film's table on it: an idea card, a sample vial, a well plate, a red cross lying flat and a spanner on a bolt. "Imagine a molecule. Make
    it. Test it. It fails. Tweak it. Try again.": each word turns the next one to the front, and it does its one thing (a molecule is sketched on the card, the vial fills, the
    wells light, the cross stands up, the spanner turns the bolt). "Every single round in a real lab costs time and money": two more laps, and at the end of each a clock in
    the corner ticks on and a coin drops onto a stack. 4-07: the cell's floor lights up as a screen, the turntable spins faster and faster, its things shrink into a comet of
    light going round; "dozens of AI models side by side": it splits into 42 small rings across the screen (Ivanenkov 2023 says 40 and more; the count is drawn); "invent new
    molecules for this exact keyhole, score them, learn from the scores": sparks fly from the rings to CDK20's pocket and back, and each ring flares as one comes home;
    "within hours": the clock's hands spin. All of it is drawn; the body and its pocket are AlphaFold DB v6. Times are LP_VO. Run: blender -b -P bl_inserts.py -- lp <out dir> 0 2489 16 0.5 2"""
    global START
    upd4 = shot_i(sc, sky, part=4)
    upd4(505.0 + 3.5)                       # everything as shot i4 leaves it
    START = 505.0 + LP_T0
    V = LP_VO
    ob = bpy.data.objects
    core = ob["core"]
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    bpy.context.view_layer.update()
    wv = np.array([tuple(core.matrix_world @ v.co) for v in core.data.vertices])
    P0 = Vector(wv.mean(0).tolist())
    CC = np.load(HERE + "frames/u_tail_2.npz")["pos"][-1].astype(float).mean(0)
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    mid = ob["cdk20_small"].matrix_world @ Vector((np.asarray(full["pocket"]) @ np.array(q0.to_matrix()).T * P_S).tolist())
    cx, cy = cell_at(31)
    Z0 = 0.002                              # the screen's thickness: everything in the cell stands on it
    C = Vector((cx, cy + 0.02, Z0))
    front = math.atan2(-math.cos(held["az"]), math.sin(held["az"]))          # the turntable's side that faces the camera

    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    card_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    tray = gk.surface((0.74, 0.725, 0.67), 0.7, 0.1)
    steel = P.gloss((0.42, 0.42, 0.44), 0.3, 0.3)
    red = P.gloss(P.RED, 0.22, 0.6)
    am = attr_mat("lp_glow", 3.0)

    # the turntable and what stands on it; it turns about its own centre, so everything on it is parented to it
    turn = empty("turntable")
    turn.location = C
    turn.rotation_mode = "XYZ"
    TT = 0.014
    disc = lathe([(0, 0), (0.27, 0), (0.275, 0.006), (0.27, TT), (0, TT)], tray, "turntable_disc", turn, 128)
    track = tube3d([(0.19 * math.cos(a), 0.19 * math.sin(a), TT + 0.001) for a in np.linspace(0, 2 * math.pi, 97)], 0.0022, ink, "track")
    track.parent = turn
    R0 = 0.19

    def station(k, name):
        a = math.radians(72 * k)
        e = empty(name)
        e.parent = turn
        e.rotation_mode = "XYZ"
        e.location = (R0 * math.cos(a), R0 * math.sin(a), TT)
        e.rotation_euler = (0, 0, a + math.pi / 2)            # local -y points out from the centre, local +x along the track
        return e
    st = [station(k, n) for k, n in enumerate(("st_card", "st_vial", "st_plate", "st_cross", "st_spanner"))]

    # 0 the idea card, leaning back a little, a molecule sketched on its face
    card = B.extrude([box(-0.042, 0.042, 0.11, 0.0, 0.01)], 0.006, 0.0015, name="card", mat=card_m)
    card.parent, card.rotation_mode = st[0], "XYZ"
    card.rotation_euler = (math.radians(75), 0, 0)
    card.location = (0, 0.012, 0)
    hexa = [(0.02 * math.cos(math.radians(30 + 60 * i)), 0.058 + 0.02 * math.sin(math.radians(30 + 60 * i)), 0.0068) for i in range(7)]
    sketch = [tube3d(hexa, 0.0016, ink, "sketch"), tube3d([hexa[0], (0.036, 0.078, 0.0068), (0.036, 0.094, 0.0068)], 0.0016, ink, "sketch"),
              tube3d([hexa[3], (-0.036, 0.042, 0.0068), (-0.03, 0.026, 0.0068)], 0.0016, ink, "sketch")]
    for o in sketch:
        o.parent = card
        o.data.bevel_factor_mapping_end = "SPLINE"
        o.data.bevel_factor_end = 0.0

    # 1 the vial, red rising in it on "make it"
    vial_root = empty("lp_vial")
    vial_root.parent = st[1]
    glass = lathe([(0, 0.0), (0.019, 0.003), (0.022, 0.012), (0.022, 0.095), (0, 0.095)], B.clear_glass(), "lp_vial_glass", vial_root, 48)
    glass.visible_shadow = False
    lathe([(0, 0.095), (0.0235, 0.095), (0.0235, 0.11), (0, 0.11)], P.gloss(P.KLEIN, 0.25, 0.6), "lp_vial_cap", vial_root, 48)
    dose = lathe([(0, 0.002), (0.016, 0.005), (0.019, 0.012), (0.019, 0.09), (0, 0.09)], B.fluid(P.RED, (0.9, 0.05, 0.03)), "lp_vial_dose", vial_root, 48)
    dose.visible_diffuse = False
    dose_v = np.zeros(len(dose.data.vertices) * 3, np.float32)
    dose.data.vertices.foreach_get("co", dose_v)

    # 2 the well plate: 3 by 4 wells that light Klein blue on "test it", then go red when it fails
    plate = B.extrude([box(-0.06, 0.06, 0.042, -0.042, 0.008)], 0.018, 0.003, name="lp_plate", mat=card_m)
    plate.parent = st[2]
    wv_, wf_ = [], []
    for i in range(12):
        x, y = -0.039 + (i % 4) * 0.026, -0.022 + (i // 4) * 0.022
        g = [(x + 0.0085 * math.cos(2 * math.pi * j / 16), y + 0.0085 * math.sin(2 * math.pi * j / 16)) for j in range(16)]
        base = len(wv_)
        wv_ += [(px_, py_, 0.0185) for px_, py_ in g] + [(px_, py_, 0.0205) for px_, py_ in g]
        wf_ += [tuple(base + 16 + j for j in range(16))] + [(base + j, base + (j + 1) % 16, base + 16 + (j + 1) % 16, base + 16 + j) for j in range(16)]
    wells, wells_me = attr_mesh("lp_wells", wv_, wf_, am)
    wells.parent = st[2]
    WELL_ORDER = np.repeat(np.arange(12), 32)

    # 3 the red cross: lies flat, stands up on its bottom edge when the round fails
    hinge = empty("lp_cross")
    hinge.parent, hinge.rotation_mode = st[3], "XYZ"
    hinge.location = (0, -0.04, 0.0)          # its bottom edge, 4 cm out from the station: lying flat it reaches inward, standing it faces out
    for s_ in (1, -1):
        ang = math.radians(45 * s_)
        bar = [(px_ * math.cos(ang) - py_ * math.sin(ang), 0.04 + px_ * math.sin(ang) + py_ * math.cos(ang))
               for px_, py_ in B.round_poly([(-0.05, -0.011), (0.05, -0.011), (0.05, 0.011), (-0.05, 0.011)], 0.008)]
        o = B.extrude([bar], 0.014, 0.003, name="lp_cross_bar", mat=red)
        o.parent = hinge

    # 4 the spanner on a bolt: on "tweak it" it turns the bolt a sixth of a turn
    bolt = lathe([(0, 0), (0.0095, 0), (0.0095, 0.022), (0, 0.022)], steel, "lp_bolt", st[4], 6)
    pivot = empty("lp_spanner")
    pivot.parent, pivot.rotation_mode = st[4], "XYZ"
    pivot.location = (0, 0, 0.004)
    head = [(0.022 * math.cos(a_), 0.022 * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    hole = [(0.0115 * math.cos(a_), 0.0115 * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 6, endpoint=False)][::-1]
    o = B.extrude([head, hole], 0.009, 0.002, name="lp_spanner_head", mat=steel)
    o.parent = pivot
    o = B.extrude([box(-0.008, 0.008, 0.12, 0.016, 0.006)], 0.008, 0.002, name="lp_spanner_handle", mat=steel)
    o.parent = pivot
    o.rotation_euler = (0, 0, math.radians(-90))           # the handle lies along the track

    # in the cell's front corners, off the turntable: a clock that ticks on a quarter at the end of each round, and a stack the round's coin drops onto
    clock_at = (cx - 0.35, cy + 0.0)          # beside the turntable, left and right, where the camera always sees them
    face = lathe([(0, 0), (0.055, 0), (0.057, 0.005), (0.055, 0.011), (0, 0.011)], card_m, "lp_clock", None, 96)
    face.location = (*clock_at, Z0)
    rim_ = tube3d([(clock_at[0] + 0.05 * math.cos(a_), clock_at[1] + 0.05 * math.sin(a_), 0.0115 + Z0) for a_ in np.linspace(0, 2 * math.pi, 65)], 0.0018, ink, "lp_clock_rim")
    hands = []
    for L_, w_ in ((0.028, 0.0035), (0.043, 0.0025)):
        h_ = empty("lp_hand")
        h_.location, h_.rotation_mode = (*clock_at, 0.012 + Z0), "XYZ"
        o = B.extrude([box(-w_, w_, L_, -0.006, w_ * 0.9)], 0.002, 0.0006, name="lp_hand_bar", mat=ink)
        o.parent = h_
        hands.append(h_)
    coin_at = (cx + 0.35, cy + 0.0)
    coins = []
    for i in range(3):
        o = lathe([(0, 0), (0.028, 0), (0.03, 0.0035), (0.028, 0.007), (0, 0.007)], P.gloss((0.62, 0.6, 0.55), 0.3, 0.5), "lp_coin", None, 64)
        o.location = (coin_at[0] + 0.003 * (i % 2), coin_at[1] - 0.002 * i, Z0)
        coins.append(o)

    # the director's note of 11-05: a 3D dizzy emoji beside the turntable, standing in for the chemist. It nods at each step; through the two paid laps its head goes round
    # with the turntable, its eyes turn to crosses, stars circle and it falls over on its side; as the turntable spins up inside the computer it pops up and splits, again
    # and again, each one smaller, until 64 of it cover the turntable (the director's 11-05 note); they ride round with it and flatten with it into the ring of light. Drawn: the face is ours, no emoji font.
    import bmesh
    yel = P.gloss((1.0, 0.6, 0.02), 0.28, 0.5)
    fv = Vector((math.cos(front), math.sin(front), 0.0))          # towards the camera
    lv = Vector((-math.sin(front), math.cos(front), 0.0))         # screen right
    cam_yaw = front + math.pi / 2                                  # turns the face (local -y) to the camera

    tear_m = P.gloss((0.25, 0.55, 1.0), 0.15, 0.6)

    def emo_mesh(name, face):
        """One head with one face: beam, shock, wince (can't watch), sad or dizzy. The face looks out along local -y."""
        bm = bmesh.new()

        def put(kind, M, mi):
            if kind == "s":
                r_ = bmesh.ops.create_uvsphere(bm, u_segments=40 if mi == 0 else 12, v_segments=20 if mi == 0 else 8, radius=1.0, matrix=M)
            else:
                r_ = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
            for f_ in {f for v in r_["verts"] for f in v.link_faces}:
                f_.material_index = mi
                f_.smooth = kind == "s"

        def frame(d, at, sx, sy, sz, spin=0.0):
            n = Vector(d).normalized()
            t1 = Vector((0, 0, 1)).cross(n).normalized()
            t2 = n.cross(t1)
            a = t1 * math.cos(spin) + t2 * math.sin(spin)
            b = n.cross(a)
            M = Matrix((a * sx, b * sy, n * sz)).transposed().to_4x4()
            M.translation = n * at
            return M
        def dots(pts, r=0.045):
            for q in pts:
                put("s", frame(q, 0.99, r, r, r), 1)

        def line(a, b, n):
            return [tuple(a[i] + (b[i] - a[i]) * u for i in range(3)) for u in np.linspace(0, 1, n)]
        put("s", Matrix.Identity(4), 0)
        for sx_ in (-1, 1):
            ex = 0.36 * sx_
            eye = (ex, -0.9, 0.24)
            if face == "dizzy":
                for sp in (math.pi / 4, -math.pi / 4):
                    put("c", frame(eye, 0.985, 0.36, 0.085, 0.09, sp), 1)
            elif face == "beam":                                         # closed, smiling eyes: an arch
                dots([(ex + u, -0.9, 0.2 + 0.1 * (1 - (u / 0.14) ** 2)) for u in np.linspace(-0.14, 0.14, 9)])
            elif face == "shock":                                        # wide eyes, brows up
                put("s", frame(eye, 0.97, 0.12, 0.18, 0.06), 1)
                put("c", frame((ex, -0.8, 0.6), 0.99, 0.22, 0.06, 0.08, -0.2 * sx_), 1)
            elif face == "wince":                                        # squeezed shut: > on the left, < on the right
                tip = (ex + 0.08 * (-sx_), -0.9, 0.24)
                dots(line((ex + 0.1 * sx_, -0.9, 0.34), tip, 7) + line(tip, (ex + 0.1 * sx_, -0.9, 0.14), 7))
            else:                                                        # sad: small eyes, brows up at the middle
                put("s", frame(eye, 0.975, 0.07, 0.11, 0.06), 1)
                put("c", frame((ex, -0.84, 0.5), 0.99, 0.22, 0.06, 0.08, -0.4 * sx_), 1)
        if face == "dizzy":
            put("s", frame((0, -0.93, -0.38), 0.975, 0.14, 0.12, 0.06), 1)          # a small round "o"
        elif face == "beam":
            dots([(x, -0.93, -0.3 - 1.6 * (0.1225 - x * x)) for x in np.linspace(-0.35, 0.35, 15)], 0.06)          # a big grin
        elif face == "shock":
            put("s", frame((0, -0.93, -0.42), 0.97, 0.13, 0.19, 0.07), 1)           # a tall "O"
        elif face == "wince":
            zz = [(x, -0.93, -0.38 + (0.045 if i % 2 else -0.045)) for i, x in enumerate(np.linspace(-0.26, 0.26, 7))]
            dots([q for a, b in zip(zz, zz[1:]) for q in line(a, b, 5)], 0.035)       # a zigzag
        else:
            dots([(x, -0.93, -0.47 + 0.9 * (0.09 - x * x)) for x in np.linspace(-0.27, 0.27, 9)])   # a frown
            put("s", frame((-0.42, -0.86, 0.0), 0.99, 0.07, 0.13, 0.06), 2)          # a tear under the left eye
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for m_ in (yel, ink, tear_m):
            me.materials.append(m_)
        return me
    FACES = ["beam", "shock", "wince", "sad"]
    me_face = {k: emo_mesh("emo_" + k, k) for k in FACES}
    me_dizzy = emo_mesh("emo_dizzy", "dizzy")

    def emo_obj(name, me):
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        o.rotation_mode = "XYZ"
        o.hide_render = True
        return o
    orbit = empty("emo_orbit")
    orbit.rotation_mode = "XYZ"
    star_poly = [((0.016 if i % 2 == 0 else 0.007) * math.cos(math.pi / 2 + math.pi * i / 5), (0.016 if i % 2 == 0 else 0.007) * math.sin(math.pi / 2 + math.pi * i / 5)) for i in range(10)]
    stars = []
    for k in range(3):
        a_ = 2 * math.pi * k / 3
        s_o = B.extrude([star_poly], 0.005, 0.0012, name="emo_star", mat=yel)
        s_o.parent, s_o.rotation_mode = orbit, "XYZ"
        s_o.location, s_o.rotation_euler = (0.06 * math.cos(a_), 0.06 * math.sin(a_), 0.0), (math.pi / 2, 0, a_ + math.pi / 2)
        stars.append(s_o)

    NG = 6                                                        # six splits: 64 of it on the turntable at the end
    R_E = [0.05 * 0.885 ** g for g in range(NG + 1)]              # smaller each time, still big enough at the end to cover the turntable
    T_HOP = V["ai"] + 2.3                                         # up off the floor and onto the turntable's middle, 0.45 s
    T_CLEAR = V["ai"] + 2.4                                       # the five things shrink away, 1.2 s, to make room
    T_SPLIT = [V["ai"] + 2.95, V["ai"] + 3.4, V["ai"] + 3.8, V["ai"] + 4.15, V["ai"] + 4.45, V["ai"] + 4.7]          # faster and faster, with the turntable
    cnr = max([Vector((cx + sx_ * 0.38, cy + sy_ * 0.29, 0.0)) for sx_ in (-1, 1) for sy_ in (-1, 1)], key=lambda q: (q - C).to_2d().dot((lv - 0.6 * fv).to_2d()))          # the back right corner: clear of the pen notes along the bottom
    hub = cnr + (C - cnr).normalized() * 0.09
    E_rest = np.array((hub.x, hub.y))                              # where it watches from, on the cell's floor

    def room(p, r):
        """How far a head of radius r at p (on the floor) stays clear of the turntable, the cell's rim, the coins and the clock (want >= 0)."""
        return min(math.hypot(p[0] - C.x, p[1] - C.y) - 0.275 - r - 0.008, 0.405 - r - abs(p[0] - cx), 0.32 - r - abs(p[1] - cy),
                   math.hypot(p[0] - coin_at[0], p[1] - coin_at[1]) - 0.03 - r - 0.008, math.hypot(p[0] - clock_at[0], p[1] - clock_at[1]) - 0.057 - r - 0.008)
    ST = [np.array((R0 * math.cos(math.radians(72 * k)), R0 * math.sin(math.radians(72 * k)))) for k in range(5)]
    REACH = [0.06, 0.03, 0.075, 0.095, 0.125]                     # how far each thing reaches from its station: card, vial, plate, cross (standing or flat), spanner's handle

    def clear_s(t):
        return 1 - smooth((t - T_CLEAR) / 1.2)

    def plate_room(p, r, t):
        """A head of radius r at p in the turntable's frame, at time t: clear of the turntable's rim and of the shrinking things (want >= 0)."""
        out_ = 0.262 - r - math.hypot(p[0], p[1])
        if clear_s(t) > 0:
            out_ = min(out_, min(float(np.hypot(*(p - q))) - REACH[k] * clear_s(t) - r - 0.003 for k, q in enumerate(ST)))
        return out_
    cand = np.array([(x, y) for x in np.arange(-0.262, 0.262, 0.004) for y in np.arange(-0.262, 0.262, 0.004) if math.hypot(x, y) <= 0.262 - 0.021])
    pick = [int(np.argmin(np.hypot(cand[:, 0], cand[:, 1])))]
    dmin = np.hypot(cand[:, 0] - cand[pick[0], 0], cand[:, 1] - cand[pick[0], 1])
    for _ in range(2 ** NG - 1):                                    # spread out: each next leaf is the candidate farthest from those picked
        pick.append(int(np.argmax(dmin)))
        dmin = np.minimum(dmin, np.hypot(cand[:, 0] - cand[pick[-1], 0], cand[:, 1] - cand[pick[-1], 1]))
    leaves = cand[pick]
    nodes = []

    def build(idx, g, parent):
        pts = leaves[idx]
        nd = dict(g=g, pos=pts.mean(0), parent=parent, k=len([n_ for n_ in nodes if n_["g"] == g]))
        nodes.append(nd)
        if len(idx) > 1:
            c0 = pts - pts.mean(0)
            order = np.argsort(c0 @ np.linalg.svd(c0)[2][0])
            h = len(idx) // 2
            build([idx[i] for i in order[:h]], g + 1, nd)
            build([idx[i] for i in order[h:]], g + 1, nd)
    build(list(range(2 ** NG)), 0, None)
    for g in range(1, NG + 1):                                      # no bigger than its own generation's spacing allows, so no two of one generation touch
        P_ = np.array([nd["pos"] for nd in nodes if nd["g"] == g])
        D_ = np.hypot(*(P_[:, None] - P_[None]).transpose(2, 0, 1))
        np.fill_diagonal(D_, 9.0)
        R_E[g] = min(R_E[g], 0.46 * float(D_.min()))
    rng_e = np.random.default_rng(11)
    for nd in nodes:
        nd["yaw"], nd["ph"] = float(rng_e.uniform(0, 2 * math.pi)), float(rng_e.uniform(0, 2 * math.pi))
        nd["obj"] = emo_obj("emo_%d" % nd["g"], me_dizzy)
        if nd["g"]:
            nd["obj"].parent = turn                                 # rides round with the turntable, and blurs with it
    root = nodes[0]
    root_faces = {k: emo_obj("emo_" + k, me_face[k]) for k in FACES}

    def life(nd):
        return T_SPLIT[nd["g"] - 1], (T_SPLIT[nd["g"]] if nd["g"] < NG else V["ai"] + 6.0)
    worst = min(plate_room(nd["parent"]["pos"] + (nd["pos"] - nd["parent"]["pos"]) * smooth(min(1.0, (tt - life(nd)[0]) / 0.22)), R_E[nd["g"]], tt)
                for nd in nodes[1:] for tt in np.linspace(*life(nd), 12))
    sib = min(float(np.hypot(*(a["pos"] - b["pos"]))) - R_E[a["g"]] - R_E[b["g"]] for a in nodes for b in nodes if a is not b and a["g"] == b["g"])

    def emo_check():          # run once turn_angle is defined
        hop_worst = 9.0                                                 # the hop: its underside over the things on the turntable while they are still there
        for u in np.linspace(0, 1, 40):
            tt = T_HOP + 0.45 * u
            xy = E_rest + (np.array((C.x, C.y)) - E_rest) * smooth(u)
            z_bot = TT * smooth(u) + 0.25 * math.sin(math.pi * u)
            a_ = turn_angle(tt)
            for k, q in enumerate(ST):
                w_ = np.array((C.x + q[0] * math.cos(a_) - q[1] * math.sin(a_), C.y + q[0] * math.sin(a_) + q[1] * math.cos(a_)))
                if float(np.hypot(*(xy - w_))) < REACH[k] * clear_s(tt) + R_E[0]:
                    hop_worst = min(hop_worst, z_bot - (TT + 0.125 * clear_s(tt)))
        print("4-06/07 emoji: watching spot %.3f clear on the floor; on the turntable, room to spare %.3f; closest two of one generation %.3f; the hop clears the things by %.3f (all want >= 0)" % (room(E_rest, R_E[0]), worst, sib, hop_worst))

    # the screen: the cell's own floor, dark with a blue glow once the loop goes inside the computer
    scr_m, nt, out_ = gk._mat("lp_screen")
    sb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    sb.inputs["Roughness"].default_value = 0.25
    sb.inputs["Emission Color"].default_value = (*P.BLUE, 1)
    nt.links.new(sb.outputs[0], out_.inputs["Surface"])
    screen = B.extrude([box(cx - 0.415, cx + 0.415, cy + 0.33, cy - 0.33, 0.055)], 0.002, 0.0005, name="lp_screen", mat=scr_m)

    # the comet that the turntable becomes, then 42 small ones, one per model, across the screen
    rv, rf, ra, rb = ring_geo(1.0, 0.03)
    GRID = [(cx - 0.24 + 0.08 * (i % 7), cy - 0.2375 + 0.095 * (i // 7)) for i in range(42)]          # 7 by 6, between the clock and the coins
    nR = len(rv)
    comets, comets_me = attr_mesh("lp_comets", np.zeros((42 * nR, 3)), np.concatenate([rf + k * nR for k in range(42)]), am)
    spin_ph = np.random.default_rng(5).uniform(0, 2 * np.pi, 42)
    spin_w = np.random.default_rng(6).uniform(0.8, 1.25, 42)

    # sparks: new molecules out to the pocket, and back with a score
    NSP = 48
    sv, sf, _, _ = ring_geo(0.6, 0.4, 8, 6)          # a small bead
    sparks, sparks_me = attr_mesh("lp_sparks", np.zeros((NSP * len(sv), 3)), np.concatenate([sf + k * len(sv) for k in range(NSP)]), am)
    g_ = np.random.default_rng(9)
    sp_from = g_.integers(0, 42, NSP)
    sp_t = V["invent"] + 0.5 + np.sort(g_.uniform(0, 6.0, NSP))
    sp_good = g_.uniform(0, 1, NSP) < 0.3          # how it scored: a few blue, most red
    # the director's 11-05 note: a spark that scores well makes CDK20 shake as it reaches the pocket. A twist about the body's upright axis through its middle (so it can
    # never dip into the table), with a small hop; 0.35 s each, back at rest after the last, so shot hz starts from the same body.
    hits = [float(sp_t[k]) + 0.9 for k in range(NSP) if sp_good[k]]
    core_rest = core.matrix_world.copy()
    piv = Matrix.Translation(P0)
    SH_A, SH_HOP, SH_LEN = math.radians(13.0), 0.012, 0.5          # the director asked for a bigger shake (11-05)

    def shake(t):
        ang, up = 0.0, 0.0
        for h in hits:
            x = t - h
            if 0 <= x < SH_LEN:
                env = math.exp(-x / 0.16) * (1 - x / SH_LEN)
                ang += SH_A * env * math.sin(2 * math.pi * 6.5 * x)
                up = max(up, SH_HOP * math.sin(math.pi * x / SH_LEN))
        return ang, up
    rr = float(np.max(np.hypot(wv[:, 0] - P0.x, wv[:, 1] - P0.y)))
    peak = max(abs(shake(h + x)[0]) for h in hits for x in np.linspace(0, SH_LEN, 60))
    print("4-07 shake: %d good sparks, %d shakes; at most %.1f degrees, so the body's far edge (%.3f out) moves %.4f sideways and lifts %.3f; it never goes down" % (
        int(np.sum(sp_good)), len(hits), math.degrees(peak), rr, 2 * rr * math.sin(peak / 2), SH_HOP))
    from mathutils.bvhtree import BVHTree as BVH_
    rim_o = min((o for o in bpy.data.objects if o.name.startswith("cell") and o.type == "MESH"),
                key=lambda o: ((o.matrix_world @ Vector(o.bound_box[0]) + o.matrix_world @ Vector(o.bound_box[6])) / 2 - P0).to_2d().length)
    dg = bpy.context.evaluated_depsgraph_get()
    rim_e = rim_o.evaluated_get(dg)
    rim_me = rim_e.to_mesh()
    rim_tree = BVH_.FromPolygons([tuple(rim_e.matrix_world @ v.co) for v in rim_me.vertices], [tuple(p_.vertices) for p_ in rim_me.polygons])
    sub = wv[::7]

    def rim_gap(a_, up):
        R_ = np.array(Matrix.Rotation(a_, 3, "Z"))
        q = (sub - np.array(P0)) @ R_.T + np.array(P0) + np.array((0, 0, up))
        return min(rim_tree.find_nearest(Vector(tuple(v)))[3] for v in q)
    print("4-07 shake: the body's closest approach to its red cell rim (%s): %.4f at rest, %.4f / %.4f twisted either way at the peak (want > 0.003)" % (
        rim_o.name, rim_gap(0.0, 0.0), rim_gap(peak, 0.0), rim_gap(-peak, 0.0)))
    way = ob["cdk20_small"].matrix_world.to_3x3() @ Vector((np.array(q0.to_matrix()) @ np.asarray(full["mouth"])).tolist())
    nrm = np.array(tuple(way.normalized()))                  # the way out of the pocket (cdk20.npz "mouth"), as S3's keyhole used it
    tgt = [0.04]
    target = np.array(tuple(mid)) + 0.04 * nrm               # just outside the pocket's mouth; the spark shrinks away there
    side = np.array((nrm[0], nrm[1], 0.0)) / max(1e-6, math.hypot(nrm[0], nrm[1]))

    shape = [None]

    def spark_at(g0, u):
        """Out of a ring, up and round the pocket's side of the body, and in at the mouth: a cubic curve, checked clear of the body below."""
        a1, h1, a2, h2 = shape[0]
        p1 = g0 + np.array((0, 0, h1)) + a1 * side
        p2 = target + a2 * nrm + np.array((0, 0, h2))
        return (1 - u) ** 3 * g0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * target

    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([tuple(v) for v in wv], [tuple(p_.vertices) for p_ in core.data.polygons])

    def crossings():
        """How many times the sparks' paths pass through the body's surface, and how close they come to it before the last 15% (the way into the mouth)."""
        n_, near_, where = 0, 9.0, []
        for k in range(42):
            us = np.linspace(0, 1, 120)
            pts = [spark_at(np.array((*GRID[k], 0.03)), u) for u in us]
            for u_, a_, b_ in zip(us, pts, pts[1:]):
                d_ = Vector(tuple(b_ - a_))
                hit = tree.ray_cast(Vector(tuple(a_)), d_.normalized(), d_.length)
                if hit[0] is not None:
                    n_ += 1
                    where.append(round(float(u_), 2))
            for q_ in pts[:102]:
                near_ = min(near_, tree.find_nearest(Vector(tuple(q_)))[3])
        crossings.where = sorted(set(where))[:12]
        return n_, near_
    for off in (0.07, 0.1, 0.13):
        target = np.array(tuple(mid)) + off * nrm
        for cand in [(a1, h1, a2, h2) for a2 in (0.3, 0.45, 0.6) for a1 in (0.3, 0.5, 0.7) for h1 in (0.35, 0.55) for h2 in (0.0, 0.1)]:
            shape[0] = cand
            n_x, near = crossings()
            if n_x == 0 and near >= 0.025:
                break
        print("4-07 sparks: end %.2f out of the mouth, path %s, %d crossings (at u %s), closest %.3f before the last 15%%" % (off, shape[0], n_x, crossings.where, near))
        if n_x == 0 and near >= 0.025:
            break

    # when things happen: the steps of the first round, then two even rounds
    steps = [V["imagine"], V["make"], V["test"], V["fails"], V["tweak"], V["again"]]
    laps = [(V["every"], V["every"] + 2.4), (V["every"] + 2.6, V["every"] + 5.0)]
    lap_end = [V["again"] + 0.45] + [b for a, b in laps]

    def turn_angle(t):
        """The turntable's angle: station k faces the camera after step k; then two laps at an even pace; then faster and faster inside the computer."""
        ang = front
        for i, ts in enumerate(steps[1:]):
            x = min(1.0, max(0.0, (t - ts) / 0.42))
            ang -= math.radians(72) * (smooth(x) + 0.06 * math.sin(math.pi * x) * (x < 1))
        for a, b in laps:
            ang -= 2 * math.pi * smooth((t - a) / (b - a))
        if t > V["ai"] + 2.6:          # spinning up: 0.4 turns a second, doubling every 0.9 s, up to 9
            u = t - V["ai"] - 2.6
            w0, k_ = 0.4, math.log(2) / 0.9
            T_ = math.log(9 / w0) / k_
            turns = w0 / k_ * (math.exp(k_ * min(u, T_)) - 1) + 9 * max(0.0, u - T_)
            ang -= 2 * math.pi * turns
        return ang

    # the camera: from shot i4's last view down to the turntable, round it a little through the rounds, up over the screen, back to see the pocket, in on the clock
    pair = dict(at=((P0.x + float(CC[0])) / 2 + 0.08, float(CC[1]) - 0.02, 0.12), az=held["az"] + math.radians(4), el=math.radians(30), d=2.7, mm=45.0)
    loop = dict(at=(C.x, C.y + 0.01, 0.05), az=held["az"], el=math.radians(36), d=1.3, mm=45.0)
    over = dict(at=(cx, cy, 0.0), az=held["az"] + math.radians(6), el=math.radians(60), d=1.5, mm=45.0)
    wide = dict(at=((cx + P0.x) / 2, (cy + P0.y) / 2 - 0.05, 0.12), az=held["az"] + math.radians(8), el=math.radians(40), d=2.9, mm=45.0)
    over_d = 2.2          # far enough that the 42 rings stay clear of the title at the top left and the source line at the bottom
    # round to the clock's far side, where the cell's rim and the bare table fill the bottom of the frame, so the source line never sits on the rings
    clock_v = dict(at=(*clock_at, 0.01), az=held["az"] - math.radians(115), el=math.radians(55), d=1.1, mm=45.0)
    keys = [(LP_T0, pair), (V["think"] + 3.0, loop), (V["every"], dict(loop, az=held["az"] + math.radians(4), d=1.24)), (V["ai"], dict(loop, az=held["az"] + math.radians(8), d=1.2)),
            (V["ai"] + 3.2, over), (V["chem"] + 3.0, dict(over, d=over_d)), (V["invent"] - 0.2, dict(over, d=over_d)), (V["invent"] + 2.0, wide), (V["hours"] - 1.2, dict(wide, d=2.8)),
            (V["hours"] + 2.8, clock_v), (V["end"], dict(clock_v, d=1.02))]

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return keys[-1][1]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None
    for f in range(FRAMES):
        t = LP_T0 + f / FPS
        v = view(t)
        shoot(c, f, v, v["at"])
        turn.rotation_euler = (0, 0, turn_angle(t))          # keyed, so the fast spin blurs
        turn.keyframe_insert("rotation_euler", index=2, frame=f)
    from bpy_extras.object_utils import world_to_camera_view
    spots = dict(turntable=tuple(C), clock=(*clock_at, 0.01), coins=(*coin_at, 0.02), pocket=tuple(mid))
    for tt in (V["imagine"], V["every"] + 1.0, V["chem"] + 4.0, V["invent"] + 3.0, V["end"] - 0.1):
        f = round((tt - LP_T0) * FPS)
        sc.frame_set(f)
        print("4-06/07 t %.1f:" % tt, ", ".join("%s %.0f %.0f" % (k, *(lambda q: (q.x * 1920, (1 - q.y) * 1080))(world_to_camera_view(sc, c, Vector(p_)))) for k, p_ in spots.items()))
    emo_check()
    for tt in (8.0, 14.0, 19.0, V["ai"] + 3.7, V["ai"] + 5.3):
        f = round((tt - LP_T0) * FPS)
        sc.frame_set(f)
        q_ = lambda p_: (lambda q: (q.x * 1920, (1 - q.y) * 1080))(world_to_camera_view(sc, c, Vector((p_[0], p_[1], 0.03))))
        print("4-06/07 emoji t %.1f: head %.0f %.0f" % (tt, *q_(E_rest)))

    near_s = 9.0                     # the sparks do not twist with the body: while it shakes, how close does any spark in flight come to the twisted surface?
    for h in hits:
        for tt in np.arange(h, h + SH_LEN, 1 / FPS):
            ang_, up_ = shake(tt)
            inv = (Matrix.Translation((0, 0, up_)) @ piv @ Matrix.Rotation(ang_, 4, "Z") @ piv.inverted()).inverted()
            for k in range(NSP):
                x = tt - sp_t[k]
                if 0 <= x < 1.8:
                    u = smooth(x / 0.9) if x < 0.9 else smooth(2 - x / 0.9)
                    if u < 0.85:          # the way in at the mouth, where it is meant to touch, is left out as before
                        q = inv @ Vector(tuple(spark_at(np.array((*GRID[sp_from[k]], 0.03)), u)))
                        near_s = min(near_s, tree.find_nearest(q)[3] - 0.016 * 0.5)
    print("4-07 shake: closest any spark in flight comes to the shaking body, less its own radius: %.4f (want > 0)" % near_s)
    things = [disc, track, card, vial_root, plate, hinge, pivot, bolt] + st

    def drop(t, at):
        """Set down from above: falls, lands at 'at', a small bounce."""
        x = t - at
        if x < -0.45:
            return 1.2
        if x < 0:
            return 1.2 * (x / -0.45) ** 2
        return 0.012 * abs(math.sin(min(x, 0.3) / 0.3 * math.pi)) * (1 - min(x, 0.3) / 0.3)

    def update(t):
        t = t - START + LP_T0
        # set down, one by one, while the camera comes over: the turntable first, then its five things
        h0 = drop(t, V["think"] + 1.2)
        turn.location = (C.x, C.y, Z0 + h0)
        disc.hide_render = track.hide_render = bool(h0 >= 1.2)
        for k, e in enumerate(st):
            hk = drop(t, V["think"] + 1.6 + 0.3 * k)
            e.location = (e.location[0], e.location[1], TT + hk)
            for o in e.children_recursive:
                o.hide_render = bool(hk >= 1.2)          # nothing hangs in view before it falls
        # inside the computer: the things shrink into the comet
        gone = smooth((t - V["ai"] - 4.4) / 1.6)
        for e in st:                                             # the five things go first, to make room for the emoji
            e.scale = (max(min(1 - gone, clear_s(t)), 1e-3),) * 3
        if clear_s(t) <= 0:
            for e in st:
                for o in e.children_recursive:
                    o.hide_render = True
        if gone >= 1:
            disc.hide_render = track.hide_render = True
            for e in st:
                for o in e.children_recursive:
                    o.hide_render = True
        turn.scale = (1.0, 1.0, max(1 - gone, 1e-3))
        # 0 the sketch, once per round
        s_ = smooth((t - V["imagine"] - 0.1) / 0.6)          # drawn once; it stays
        for i, o in enumerate(sketch):
            o.data.bevel_factor_end = min(1.0, max(0.0, s_ * 3 - i)) if s_ < 1 else 1.0
        # 1 the vial: fills on "make it", empties at the end of each round, fills again on the way round
        fill = 0.0
        for a, b in [(V["make"] + 0.35, lap_end[0])] + [(a + 0.48, b) for a, b in laps]:
            fill = max(fill, smooth((t - a) / 0.45) * (1 - smooth((t - b + 0.05) / 0.25)))
        level = 0.014 + 0.066 * fill
        v_ = dose_v.copy()
        v_[2::3] = np.minimum(v_[2::3], level)
        dose.data.vertices.foreach_set("co", v_)
        dose.data.update()
        # 2 the wells: blue one after another on "test it", red when it fails, dark again for the next round
        lit = np.zeros(12)
        bad = 0.0
        for a, fl, b in [(V["test"] + 0.35, V["fails"] + 0.4, lap_end[0])] + [(a + 0.96, a + 1.44, b) for a, b in laps]:
            on = np.clip((t - a - 0.03 * np.arange(12)) / 0.12, 0, 1) * (1 - smooth((t - b + 0.05) / 0.25))
            lit = np.maximum(lit, on)
            bad = max(bad, smooth((t - fl) / 0.3) * (1 - smooth((t - b + 0.05) / 0.25)))
        col = np.array(P.KLEIN)[None] * (1 - bad) + np.array(P.RED)[None] * bad
        bone = np.array((0.80, 0.78, 0.72))[None]
        cw = bone * (1 - lit[:, None]) + col * lit[:, None]
        set_attr(wells_me, np.repeat(cw, 32, 0), np.repeat(lit * 0.7, 32))
        wells_me.update()
        # 3 the cross stands up when it fails and lies down for the next round
        up = 0.0
        for a, b in [(V["fails"] + 0.4, lap_end[0])] + [(a + 1.44, b) for a, b in laps]:
            x = (t - a) / 0.35
            up = max(up, (smooth(x) + 0.12 * math.sin(math.pi * min(max(x, 0), 1))) * (1 - smooth((t - b + 0.1) / 0.3)))
        hinge.rotation_euler = (math.radians(90) * up, 0, 0)
        # 4 the spanner turns the bolt a sixth of a turn, every round
        tw = sum(smooth((t - a) / 0.4) for a in [V["tweak"] + 0.4] + [a + 1.92 for a, b in laps])
        pivot.rotation_euler = (0, 0, math.radians(60) * tw)
        bolt.rotation_euler = (0, 0, math.radians(60) * tw)
        # the clock ticks on a quarter at the end of each round; "within hours", the hands spin
        tick = sum(smooth((t - e_) / 0.18) for e_ in lap_end)
        fast = 0.0
        if t > V["hours"] + 1.6:
            u = t - V["hours"] - 1.6
            fast = 2.2 * u - 0.8 * max(0.0, u - 2.0) ** 2 if u < 3.375 else 2.2 * 3.375 - 0.8 * 1.375 ** 2
        hands[1].rotation_euler = (0, 0, -math.radians(90) * tick - 2 * math.pi * fast)
        hands[0].rotation_euler = (0, 0, math.radians(-120) - math.radians(7.5) * tick - 2 * math.pi * fast / 12)
        for i, o in enumerate(coins):           # a coin falls onto the stack at the end of each round
            x = t - lap_end[i]
            o.hide_render = bool(x < -0.5)
            fall_h = 0.0 if x >= 0 else 0.5 * (x / 0.5) ** 2
            o.location = (o.location[0], o.location[1], Z0 + 0.007 * i + fall_h + (0.004 * abs(math.sin(min(x, 0.2) / 0.2 * math.pi)) * (1 - min(x, 0.2) / 0.2) if x > 0 else 0))
        # the screen lights
        glow = smooth((t - V["ai"] - 0.8) / 1.8)
        sb.inputs["Base Color"].default_value = (*lerp((0.80, 0.78, 0.72), (0.01, 0.012, 0.03), glow), 1)
        sb.inputs["Emission Strength"].default_value = 0.35 * glow
        # the comet, then 42 of them
        comet = smooth((t - V["ai"] - 4.4) / 1.4)
        split = smooth((t - V["chem"] - 0.8) / 1.8)
        flare = np.zeros(42)
        for k in range(NSP):
            x = t - sp_t[k] - 1.8
            if 0 <= x < 0.6:
                flare[sp_from[k]] = max(flare[sp_from[k]], 1 - x / 0.6)
        verts, cols, glows = [], [], []
        head = turn_angle(t) - front
        for k in range(42):
            if split <= 0 and k > 0:
                cen, r = (C.x, C.y), 0.19
            else:
                g0 = GRID[k] if k else GRID[17]
                cen = lerp((C.x, C.y), g0, split)
                r = 0.19 + (0.031 - 0.19) * split
            ph = head if split <= 0 else head * (1 - split) + split * (spin_ph[k] + 2 * math.pi * 2.0 * spin_w[k] * (t - V["chem"]))
            rt = 0.0045 + 0.0035 * (1 - split)
            vv = np.c_[(r + rt * np.cos(rb)) * np.cos(ra + ph), (r + rt * np.cos(rb)) * np.sin(ra + ph), rt * np.sin(rb)]
            vv += (cen[0], cen[1], Z0 + 0.02 + 0.03 * (1 - split))
            tail = ra / (2 * np.pi)          # it turns clockwise, so its trail lies at larger angles: bright at the head, fading round to the tail
            verts.append(vv)
            cols.append(np.repeat(np.array(P.BLUE)[None], nR, 0) * (1 - 0.5 * flare[k]) + np.array((0.6, 0.75, 1.0))[None] * 0.5 * flare[k])
            glows.append(comet * (0.25 + 1.6 * (1 - tail) ** 2) * (1 + 1.5 * flare[k]) * (1 if (split > 0 or k == 0) else 0))
        comets_me.vertices.foreach_set("co", np.concatenate(verts).astype(np.float32).ravel())
        set_attr(comets_me, np.concatenate(cols), np.concatenate(glows))
        comets_me.update()
        comets.hide_render = bool(comet <= 0)
        # sparks: out along an arc to the pocket, back to their ring with a score
        pv, pc, pg = [], [], []
        for k in range(NSP):
            x = t - sp_t[k]
            g0 = np.array((*GRID[sp_from[k]], 0.03))
            if 0 <= x < 1.8:
                u = smooth(x / 0.9) if x < 0.9 else smooth(2 - x / 0.9)
                p_ = spark_at(g0, u)
                cc = np.array(P.BLUE) if x < 0.9 else (np.array(P.KLEIN) * 1.6 if sp_good[k] else np.array(P.RED))
                gl = 4.0
                sz = 0.016 * (1 - 0.6 * max(0.0, 1 - abs(x - 0.9) / 0.15))          # smaller as it touches the pocket
            else:
                p_, cc, gl, sz = g0, np.array(P.BLUE), 0.0, 1e-4
            pv.append(sv * sz + p_)
            pc.append(np.repeat(cc[None], len(sv), 0))
            pg.append(np.full(len(sv), gl))
        sparks_me.vertices.foreach_set("co", np.concatenate(pv).astype(np.float32).ravel())
        set_attr(sparks_me, np.concatenate(pc), np.concatenate(pg))
        sparks_me.update()
        sparks.hide_render = bool(t < V["invent"])
        ang_, up_ = shake(t)          # a good score: CDK20 shakes
        core.matrix_world = Matrix.Translation((0, 0, up_)) @ piv @ Matrix.Rotation(ang_, 4, "Z") @ piv.inverted() @ core_rest
        # the emoji: watches, nods, goes round with the laps, falls over, then splits and splits
        h_e = drop(t, V["think"] + 3.1)
        E = E_rest
        tg = C + R0 * fv
        dyaw = (math.atan2(tg.x - E[0], -(tg.y - E[1])) - cam_yaw + math.pi) % (2 * math.pi) - math.pi
        away = smooth((t - V["tweak"] - 0.1) / 0.3) * (1 - smooth((t - V["every"] - 0.1) / 0.4))          # "can't watch": it turns away
        yaw = cam_yaw + (0.6 - 0.95 * away) * dyaw + turn_angle(min(max(t, laps[1][0]), laps[1][1])) - turn_angle(laps[1][0])          # round once on the second lap
        nod = sum(0.22 * math.sin(math.pi * min(1.0, max(0.0, (t - ts) / 0.35))) for ts in steps)
        t_d, t_f = laps[0][1], laps[1][1]
        wob = smooth((t - t_d) / 0.6) * (1 - smooth((t - t_f) / 0.2))
        x_f = (t - t_f) / 0.4
        fall = (smooth(x_f) - 0.1 * math.sin(math.pi * min(1.0, max(0.0, (t - t_f - 0.4) / 0.3)))) * (1 - smooth((t - T_HOP) / 0.3))
        roll = 0.22 * wob * math.sin(2 * math.pi * 1.7 * (t - t_d)) + math.radians(88) * fall
        uh = min(1.0, max(0.0, (t - T_HOP) / 0.45))          # the hop onto the turntable's middle
        E = E_rest + (np.array((C.x, C.y)) - E_rest) * smooth(uh)
        hop = TT * smooth(uh) + 0.25 * math.sin(math.pi * uh)
        if uh >= 1:
            yaw = cam_yaw + turn_angle(t) - turn_angle(T_HOP + 0.45)          # on the turntable it rides round
        # the faces in turn: beaming while it goes well, shocked when it fails, can't watch the tweak and the next try, sad when it starts costing, then dizzy
        f_at = [(-1.0, "beam"), (V["fails"] + 0.1, "shock"), (V["tweak"] + 0.1, "wince"), (V["every"] + 0.1, "sad"), (t_d, "dizzy")]
        cur = [k for a, k in f_at if t >= a][-1]
        since = t - [a for a, k in f_at if t >= a][-1]
        pulse = 1 + 0.1 * math.sin(math.pi * min(1.0, since / 0.2)) if since < 0.2 and cur != "beam" else 1.0
        for o, on in [(root_faces[k], cur == k) for k in FACES] + [(root["obj"], cur == "dizzy")]:
            o.hide_render = bool(not on or h_e >= 1.2 or t >= T_SPLIT[0])
            o.location = (float(E[0]), float(E[1]), Z0 + R_E[0] + h_e + hop)
            o.scale = (R_E[0] * pulse,) * 3
            o.rotation_euler = (nod, roll, yaw)
        s_st = smooth((t - t_d) / 0.3) * (1 - smooth((t - T_HOP + 0.1) / 0.3))
        orbit.location = (float(E[0]), float(E[1]), Z0 + 2.15 * R_E[0] + hop)
        orbit.scale = (max(s_st, 1e-3),) * 3
        orbit.rotation_euler = (0, 0, 2 * math.pi * 1.2 * (t - t_d))
        for s_o in stars:
            s_o.hide_render = bool(s_st <= 0)
        for nd in nodes[1:]:
            g, o = nd["g"], nd["obj"]
            tb = T_SPLIT[g - 1]
            te = T_SPLIT[g] if g < NG else 99.0
            o.hide_render = bool(not (tb <= t < te) or gone >= 1)
            if o.hide_render:
                continue
            x = min(1.0, (t - tb) / 0.22)
            u = smooth(x)
            pp = nd["parent"]["pos"]
            p_ = pp + (nd["pos"] - pp) * u
            r = R_E[g - 1] * 0.85 + (R_E[g] - R_E[g - 1] * 0.85) * u
            o.location = (float(p_[0]), float(p_[1]), TT + r + 1.2 * R_E[g] * math.sin(math.pi * x))          # in the turntable's frame
            o.scale = (r,) * 3
            o.rotation_euler = (0, 0.25 * math.sin(2 * math.pi * 1.7 * t + nd["ph"]), nd["yaw"])
        sky(0.2)
    return update


HZ_VO = dict(shape=0.0, rule=2.6, hinge=3.2, filters=6.2, toss=7.4, toxic=8.6, score=10.6, easy=12.4, end=17.0)
HZ_START = 557.0        # shot lp ends at 550 (09:10), then 4-08 is A on camera for 7 s


def shot_hz(sc, sky):
    """4-09 (09:17-09:34, B's voice-over), back on the table after 4-08. Version A (the director's 11-05 pick: no new props, carry on in 4-07's world).
    "The team gave it the pocket's shape": the camera goes in close to CDK20's pocket, the pocket's patch of the surface turns to paper and an ink wireframe grows over it
    from the middle out (the real AlphaFold DB v6 surface within 15 A of the pocket's centre). "And one rule: every key must grip a spot called the hinge": a big red circle
    lights on the body's own surface round Met84 (the hinge residue in Ren 2023; in the v6 model its backbone lines the pocket), painted on, so nothing passes through.
    "Its filters are built to toss designs with reactive or possibly toxic groups": over at the screen, each of 4-07's 42 small rings sends up a small drawn molecule;
    the twelve with a red group flash, shrink and sink back into their own ring's hole, and that ring dims red. "And to score how drug-like and easy to make each one is":
    two bars grow beside each one that is left, one on each half of the line. The molecules and the scores are drawn; the body, the pocket and Met84 are AlphaFold DB v6.
    Run: blender -b -P bl_inserts.py -- hz <out dir> 0 1019 16 0.5 2"""
    global START
    from mathutils.bvhtree import BVHTree
    upd_lp = shot_lp(sc, sky)
    lp_off = LP_VO["end"] - LP_T0          # shot lp's update, run on: its rings keep turning, its clock stays where it stopped
    START = HZ_START
    V = HZ_VO
    ob = bpy.data.objects
    core = ob["core"]
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    bpy.context.view_layer.update()
    wv = np.array([tuple(core.matrix_world @ v.co) for v in core.data.vertices])
    P0 = Vector(wv.mean(0).tolist())
    CC = np.load(HERE + "frames/u_tail_2.npz")["pos"][-1].astype(float).mean(0)
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    smw = ob["cdk20_small"].matrix_world
    q0m = np.array(q0.to_matrix())
    to_w = lambda x: smw @ Vector((np.asarray(x) @ q0m.T * P_S).tolist())          # a point in the model's own frame (A) to the table
    mid = to_w(full["pocket"])
    unit = (to_w(np.asarray(full["pocket"]) + (1.0, 0, 0)) - mid).length          # table units to the Angstrom here
    nrm = (smw.to_3x3() @ Vector((q0m @ np.asarray(full["mouth"])).tolist())).normalized()          # the way out of the pocket
    pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM")]
    m84 = [l for l in pdb if int(l[22:26]) == 84]
    assert m84[0][17:20] == "MET"
    bb84 = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in m84 if l[12:16].strip() in ("N", "CA", "C", "O")]).mean(0)
    W84 = to_w(bb84)
    print("4-09: Met84 backbone %.1f A from the pocket's centre, pLDDT %s" % ((W84 - mid).length / unit, m84[0][60:66].strip()))
    tree = BVHTree.FromPolygons([tuple(v) for v in wv], [tuple(p_.vertices) for p_ in core.data.polygons])
    cx, cy = cell_at(31)
    C = Vector((cx, cy + 0.02, 0.002))

    ink_c = (0.012, 0.012, 0.014)
    ink = gk.surface(ink_c, 0.3)
    card_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    steel = P.gloss((0.42, 0.42, 0.44), 0.3, 0.3)
    red = P.gloss(P.RED, 0.22, 0.6)
    klein = P.gloss(P.KLEIN, 0.3, 0.5)

    # the pocket's patch: paper instead of blue, from the centre out, on the body's own surface
    dist = np.linalg.norm(wv - np.array(tuple(mid)), axis=1)
    m = core.active_material
    if m.users > 1:
        m = m.copy()
        core.active_material = m
    nt = m.node_tree
    cb = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    core.data.attributes.new("pk", "FLOAT", "POINT")
    core.data.attributes["pk"].data.foreach_set("value", (dist / unit).astype(np.float32))          # in A
    reveal = []

    def mask_node(nt_, attr):
        at_ = nt_.nodes.new("ShaderNodeAttribute")
        at_.attribute_name = attr
        mr = nt_.nodes.new("ShaderNodeMapRange")
        mr.clamp = True
        nt_.links.new(at_.outputs["Fac"], mr.inputs["Value"])
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
        reveal.append(mr)
        return mr
    mr = mask_node(nt, "pk")
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    if cb.inputs["Base Color"].is_linked:
        nt.links.new(cb.inputs["Base Color"].links[0].from_socket, mx.inputs[6])
    else:
        mx.inputs[6].default_value = cb.inputs["Base Color"].default_value
    mx.inputs[7].default_value = (0.9, 0.885, 0.84, 1)
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(mx.outputs[2], cb.inputs["Base Color"])
    def exit_from(p_, d_):
        """How far along d_ from p_ until the body is more than 4 A away for the next 5 A: where the cleft opens out."""
        for s_ in np.linspace(0.0, 1.0, 201):
            if all(tree.find_nearest(p_ + float(x) * d_)[3] > 4 * unit for x in np.linspace(s_, s_ + 5 * unit, 6)):
                return float(s_)
        return 1.0
    mouth_s = exit_from(mid, nrm)
    RMAX = 15.0          # the cleft between the two lobes and its lips; the pocket's centre lies deep inside it
    print("4-09: the cleft opens %.1f A out from the pocket's centre; patch out to %.1f A" % (mouth_s / unit, RMAX))

    # the ink wireframe over it: the same patch, thinned, lifted a hair off the surface
    keep = dist / unit < RMAX + 1.0
    polys = [tuple(p_.vertices) for p_ in core.data.polygons if keep[list(p_.vertices)].all()]
    used = sorted({i for p_ in polys for i in p_})
    re_ = {i: k for k, i in enumerate(used)}
    nrm_v = np.array([tuple((core.matrix_world.to_3x3() @ core.data.vertices[i].normal).normalized()) for i in used])
    pv = wv[used] + 0.0025 * nrm_v
    pme = bpy.data.meshes.new("hz_patch")
    pme.from_pydata(pv.tolist(), [], [[re_[i] for i in p_] for p_ in polys])
    patch = bpy.data.objects.new("hz_patch", pme)
    sc.collection.objects.link(patch)
    dec = patch.modifiers.new("dec", "DECIMATE")
    dec.ratio = min(1.0, 260.0 / max(1, len(polys)))          # few, so the lines read as a drawing, not a clump
    wf = patch.modifiers.new("wf", "WIREFRAME")
    wf.thickness, wf.use_even_offset, wf.use_replace, wf.offset = 0.0022, True, True, 0.0
    bpy.context.view_layer.update()
    wme = bpy.data.meshes.new_from_object(patch.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(patch)
    wire = bpy.data.objects.new("hz_wire", wme)
    sc.collection.objects.link(wire)
    wvv = np.zeros(len(wme.vertices) * 3)
    wme.vertices.foreach_get("co", wvv)
    wme.attributes.new("pk", "FLOAT", "POINT")
    wme.attributes["pk"].data.foreach_set("value", (np.linalg.norm(wvv.reshape(-1, 3) - np.array(tuple(mid)), axis=1) / unit).astype(np.float32))
    wm, wnt, wout = gk._mat("hz_wire")
    wb = wnt.nodes.new("ShaderNodeBsdfPrincipled")
    wb.inputs["Base Color"].default_value = (*ink_c, 1)
    wb.inputs["Roughness"].default_value = 0.4
    tr = wnt.nodes.new("ShaderNodeBsdfTransparent")
    ms = wnt.nodes.new("ShaderNodeMixShader")
    wmr = mask_node(wnt, "pk")
    wnt.links.new(wmr.outputs[0], ms.inputs[0])
    wnt.links.new(tr.outputs[0], ms.inputs[1])
    wnt.links.new(wb.outputs[0], ms.inputs[2])
    wnt.links.new(ms.outputs[0], wout.inputs["Surface"])
    wme.materials.append(wm)
    wire.visible_shadow = False
    print("4-09: pocket patch %d faces, wireframe from %d" % (len(polys), int(len(polys) * dec.ratio)))

    # the red circle round Met84: painted on the body's own surface, so nothing can pass through it
    hit = tree.find_nearest(W84)
    S84, n84 = Vector(hit[0]), Vector(hit[1]).normalized()
    if n84.dot(nrm) < 0:
        n84 = -n84
    print("4-09: the red circle is centred %.1f A from Met84's backbone" % (hit[3] / unit))
    d84 = np.linalg.norm(wv - np.array(tuple(S84)), axis=1) / unit
    core.data.attributes.new("hk", "FLOAT", "POINT")
    core.data.attributes["hk"].data.foreach_set("value", d84.astype(np.float32))
    RR, RW = 7.0, 1.1          # the circle's radius and its line's half width, in A

    def node(kind, op=None):
        n_ = nt.nodes.new(kind)
        if op:
            n_.operation = op
        return n_
    a84 = node("ShaderNodeAttribute")
    a84.attribute_name = "hk"
    dd = node("ShaderNodeMath", "SUBTRACT")
    nt.links.new(a84.outputs["Fac"], dd.inputs[0])
    ab_ = node("ShaderNodeMath", "ABSOLUTE")
    nt.links.new(dd.outputs[0], ab_.inputs[0])
    band = node("ShaderNodeMapRange")
    band.clamp = True
    nt.links.new(ab_.outputs[0], band.inputs["Value"])
    band.inputs["From Min"].default_value, band.inputs["From Max"].default_value = 0.0, RW
    band.inputs["To Min"].default_value, band.inputs["To Max"].default_value = 1.0, 0.0
    fill = node("ShaderNodeMapRange")
    fill.clamp = True
    nt.links.new(a84.outputs["Fac"], fill.inputs["Value"])
    fill.inputs["To Min"].default_value, fill.inputs["To Max"].default_value = 0.35, 0.0
    both = node("ShaderNodeMath", "MAXIMUM")
    nt.links.new(band.outputs[0], both.inputs[0])
    nt.links.new(fill.outputs[0], both.inputs[1])
    amt = node("ShaderNodeMath", "MULTIPLY")
    nt.links.new(both.outputs[0], amt.inputs[0])
    mx2 = node("ShaderNodeMix")
    mx2.data_type = "RGBA"
    nt.links.new(mx.outputs[2], mx2.inputs[6])
    mx2.inputs[7].default_value = (*P.RED[:3], 1)
    nt.links.new(amt.outputs[0], mx2.inputs[0])
    nt.links.new(mx2.outputs[2], cb.inputs["Base Color"])
    for l_ in list(cb.inputs["Emission Color"].links):
        nt.links.remove(l_)
    cb.inputs["Emission Color"].default_value = (*P.RED[:3], 1)
    em = node("ShaderNodeMath", "MULTIPLY")
    nt.links.new(amt.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], cb.inputs["Emission Strength"])

    # 4-07's 42 rings, where shot lp left them (they keep turning in place)
    upd_lp(HZ_START + lp_off)
    cme_ = bpy.data.meshes["lp_comets"]
    nR = len(cme_.vertices) // 42
    rco = np.zeros(len(cme_.vertices) * 3)
    cme_.vertices.foreach_get("co", rco)
    rco = rco.reshape(42, nR, 3)
    RC = rco.mean(1)
    ZR = float(RC[:, 2].mean())
    rad = np.hypot(rco[..., 0] - RC[:, None, 0], rco[..., 1] - RC[:, None, 1])
    HOLE, OUTR, RT = float(rad.min()), float(rad.max()), float((rco[..., 2] - RC[:, None, 2]).max())
    scr = ob["lp_screen"]
    SCR = max((scr.matrix_world @ Vector(b_)).z for b_ in scr.bound_box)
    print("4-09 rings: plane %.4f, hole %.4f, outer %.4f, tube %.4f; screen top %.4f" % (ZR, HOLE, OUTR, RT, SCR))

    # the small molecules: a ring of six atoms and one to three side groups, bone white on the dark screen; twelve carry a red group
    import bmesh
    bone = P.gloss((0.9, 0.885, 0.84), 0.3, 0.5)
    hot_m, hnt, hout = gk._mat("hz_hot")
    hb = hnt.nodes.new("ShaderNodeBsdfPrincipled")
    hb.inputs["Base Color"].default_value = hb.inputs["Emission Color"].default_value = (*P.RED[:3], 1)
    hb.inputs["Roughness"].default_value = 0.3
    hnt.links.new(hb.outputs[0], hout.inputs["Surface"])
    g_ = np.random.default_rng(21)
    BADS = sorted(int(k) for k in g_.choice(42, 12, replace=False))
    R6, AR, BR, SUB, RED_R = 0.0105, 0.003, 0.0014, 0.0085, 0.004
    mols = []
    for k in range(42):
        if k == 0:          # shot lp's first ring ends on GRID[17], stacked on ring 17: one molecule there, not two
            mols.append(None)
            continue
        bm = bmesh.new()

        def tag(r_, mi):
            for f_ in {f for v in r_["verts"] for f in v.link_faces}:
                f_.material_index = mi
                f_.smooth = True

        def ball(c_, r, mi=0):
            tag(bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r, matrix=Matrix.Translation(c_)), mi)

        def stick(a_, b_):
            d_ = b_ - a_
            M = (Matrix.Translation((a_ + b_) / 2) @ Vector((0, 0, 1)).rotation_difference(d_.normalized()).to_matrix().to_4x4())
            tag(bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=BR, radius2=BR, depth=d_.length, matrix=M), 0)
        hexa = [Vector((R6 * math.cos(math.radians(30 + 60 * i)), R6 * math.sin(math.radians(30 + 60 * i)), 0.0)) for i in range(6)]
        for c_ in hexa:
            ball(c_, AR)
        for i in range(6):
            stick(hexa[i], hexa[(i + 1) % 6])
        for j, v_ in enumerate(g_.choice(6, int(g_.integers(1, 4)), replace=False)):
            a_ = hexa[int(v_)]
            e_ = a_ + a_.normalized() * SUB
            stick(a_, e_)
            red_ = k in BADS and j == 0
            ball(e_, RED_R if red_ else AR, 1 if red_ else 0)
        me = bpy.data.meshes.new("hz_mol")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(bone)
        me.materials.append(hot_m)
        o = bpy.data.objects.new("hz_mol", me)
        sc.collection.objects.link(o)
        o.rotation_mode = "QUATERNION"
        lv_ = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", lv_)
        lv_ = lv_.reshape(-1, 3)
        mols.append(dict(obj=o, lv=lv_, ext=float(np.hypot(lv_[:, 0], lv_[:, 1]).max()), ph=float(g_.uniform(0, 2 * math.pi)), w=float(g_.uniform(-0.5, 0.5))))
    BADS = [k for k in BADS if k != 0]
    LIVE = list(range(1, 42))
    kept = [k for k in LIVE if k not in BADS]
    rank = np.argsort(np.argsort(np.hypot(RC[:, 0] - C.x, RC[:, 1] - C.y)))          # from the middle of the screen out
    T_POP = [V["filters"] + 0.6 + 0.025 * int(rank[k]) for k in range(42)]
    T_POP[0] = 99.0
    T_SINK = {k: V["toxic"] + 0.3 + 0.09 * i for i, k in enumerate(BADS)}
    T_BAR = [{k: V["score"] + 0.3 + 0.02 * i for i, k in enumerate(kept)}, {k: V["easy"] + 0.1 + 0.02 * i for i, k in enumerate(kept)}]
    H_MOL, TILT, MS = 0.046, math.radians(35), 1.4          # MS: drawn 1.4 times its first size, so it reads from the camera
    az_s = held["az"] + math.radians(6)
    rgt = np.array((math.cos(az_s), math.sin(az_s)))
    bhd = np.array((-math.sin(az_s), math.cos(az_s)))          # away from the camera, on the table
    n_face = Vector((-bhd[0] * math.sin(TILT), -bhd[1] * math.sin(TILT), math.cos(TILT)))          # each molecule leans to face the camera
    q_face = Vector((0, 0, 1)).rotation_difference(n_face)

    def mol_pose(k, t):
        """Where molecule k is at t: its height over its ring's plane, its scale and its turn in its own plane."""
        x = (t - T_POP[k]) / 0.45
        if x <= 0:
            return None
        u = smooth(x)
        s_ = MS * u * (1 + 0.15 * math.sin(math.pi * min(1.0, x)))
        zo = H_MOL * u + 0.0015 * u * math.sin(2 * math.pi * 0.5 * t + mols[k]["ph"])
        if k in T_SINK:
            y = (t - T_SINK[k]) / 0.5
            if y > 0:
                s_ *= 1 - smooth(2.0 * y)          # small enough for the ring's hole before it gets there
                zo = zo * (1 - smooth(y)) - 0.004 * smooth(y)
        if s_ <= 1e-3:
            return None
        return zo, s_, q_face @ Quaternion((0, 0, 1), mols[k]["ph"] + mols[k]["w"] * t)

    # checks: a molecule never touches its ring's tube or the screen on its way up or down; neighbours never meet
    low, tube = 9.0, 9.0
    for k in LIVE:
        lv_ = mols[k]["lv"][::3]
        t_end = T_SINK[k] + 0.8 if k in T_SINK else T_POP[k] + 1.0
        for tt in np.arange(T_POP[k], t_end, 1 / FPS):
            ps = mol_pose(k, tt)
            if ps is None:
                continue
            zo, s_, q = ps
            R_ = np.array(q.to_matrix())
            w_ = (lv_ @ R_.T) * s_ + (0, 0, zo)
            low = min(low, float((ZR + w_[:, 2]).min()) - SCR)
            r_ = np.hypot(w_[:, 0], w_[:, 1])
            inband = np.abs(w_[:, 2]) < RT + 0.001
            if inband.any():
                tube = min(tube, HOLE - float(r_[inband].max()))
    ext = max(mols[k]["ext"] for k in LIVE)
    ext *= MS
    sp_ = min(float(np.hypot(*(RC[a][:2] - RC[b][:2]))) for a in LIVE for b in LIVE if a < b)
    print("4-09 molecules: lowest point over the screen %.4f, room to the ring's tube while level with it %.4f, between neighbours %.4f (all want > 0)" % (
        low, tube, sp_ - 2 * ext * 1.15))

    # two score bars beside each molecule that is left, standing on the screen in the gap to the right of its ring (behind it they looked as if they ran through it)
    def glow_m(name, col, st):
        m_, n_, o_ = gk._mat(name)
        b_ = n_.nodes.new("ShaderNodeBsdfPrincipled")
        b_.inputs["Base Color"].default_value = b_.inputs["Emission Color"].default_value = (*col, 1)
        b_.inputs["Emission Strength"].default_value = st
        b_.inputs["Roughness"].default_value = 0.35
        n_.links.new(b_.outputs[0], o_.inputs["Surface"])
        return m_
    bar_m = [glow_m("hz_bar_a", (0.25, 0.45, 1.0), 1.2), glow_m("hz_bar_b", (0.9, 0.885, 0.84), 0.5)]
    BW, BD, B_OFF, B_GAP, B_MAX = 0.0024, 0.0024, 0.04, 0.0042, 0.07
    bars = {}
    for k in kept:
        for j in range(2):
            o = mesh("hz_bar", [(x_, y_, z_) for x_ in (-BW, BW) for y_ in (-BD, BD) for z_ in (0.0, 1.0)],
                     [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], bar_m[j])
            o.rotation_mode = "XYZ"
            xy = RC[k][:2] + np.array((B_OFF, (1 - 2 * j) * B_GAP))          # the first in front, the second behind it
            o.location = (float(xy[0]), float(xy[1]), SCR)
            bars[(k, j)] = dict(obj=o, score=float(g_.uniform(0.45, 0.95)), xy=xy)
    room_r, room_m = 9.0, 9.0
    for (k, j), b_ in bars.items():
        for cx_, cy_ in [(-BW, -BD), (-BW, BD), (BW, -BD), (BW, BD), (0, -BD), (0, BD), (-BW, 0), (BW, 0)]:
            q = b_["xy"] + np.array((cx_, cy_))
            for i in range(42):
                r_ = float(np.hypot(*(q - RC[i][:2])))
                room_r = min(room_r, max(r_ - OUTR, HOLE - r_))
                if i in kept:
                    room_m = min(room_m, r_ - mols[i]["ext"] * MS * 1.02)          # the bars come after the molecules have settled
    print("4-09 bars: room to the nearest ring's tube %.4f, to the nearest molecule %.4f (want > 0)" % (room_r, room_m))

    # the camera: in close to the pocket, closer on the red circle, over to the screen, across it, back to both cells
    d_cam = (nrm + n84).normalized()
    az_p = math.atan2(d_cam.x, -d_cam.y)
    az_p += round((held["az"] - az_p) / (2 * math.pi)) * 2 * math.pi
    el_p = min(math.radians(82), max(math.radians(32), math.asin(max(-1, min(1, d_cam.z)))))          # the mouth opens upward here: look down into it
    focus = mid + 0.7 * mouth_s * nrm          # the mouth
    # Met84 sits deep in the cleft: from the usual side none of the red circle shows. A search over views (printed below) found it best seen from az -121, el 57,
    # about two thirds of its line in sight. 4-09 comes after a cut (4-08 is on camera), so the shot opens on that side; it leaves up and over the top to the screen.
    AZ_R = math.radians(-121.0)
    AZ_R += round((held["az"] - AZ_R) / (2 * math.pi)) * 2 * math.pi
    def down(v, k):
        """The view with its aim moved k down the frame, so the scene sits higher in it (the source line at the bottom right stays on bare table)."""
        up_ = Vector((-math.sin(v["az"]) * math.sin(v["el"]), math.cos(v["az"]) * math.sin(v["el"]), math.cos(v["el"])))
        return dict(v, at=tuple(Vector(v["at"]) - k * up_))
    pocket_v = down(dict(at=tuple(lerp(tuple(S84), tuple(P0), 0.3)), az=AZ_R, el=math.radians(57), d=1.15, mm=45.0), 0.05)
    start_v = dict(pocket_v, at=tuple(lerp(tuple(S84), tuple(P0), 0.6)), az=AZ_R + math.radians(16), el=math.radians(45), d=2.0)
    ring_v = down(dict(pocket_v, at=tuple(lerp(tuple(S84), tuple(P0), 0.1)), d=0.9), 0.06)
    top_v = dict(at=tuple(lerp(tuple(P0), (C.x, C.y, ZR), 0.55)), az=(AZ_R + az_s) / 2, el=math.radians(80), d=1.9, mm=45.0)
    # aimed well past the screen's middle, so a band of bare table runs along the top of the frame: the notes, the title and the source line sit there, off the rings
    scr_a = dict(at=(C.x - 0.06 * rgt[0] + 0.22 * bhd[0], C.y - 0.06 * rgt[1] + 0.22 * bhd[1], ZR), az=az_s - math.radians(8), el=math.radians(35), d=0.9, mm=45.0)
    scr_b = dict(at=(C.x + 0.06 * rgt[0] + 0.22 * bhd[0], C.y + 0.06 * rgt[1] + 0.22 * bhd[1], ZR), az=az_s + math.radians(6), el=math.radians(37), d=0.84, mm=45.0)
    wide = dict(at=((cx + P0.x) / 2, (cy + P0.y) / 2 - 0.05, 0.12), az=held["az"] + math.radians(8), el=math.radians(40), d=2.9, mm=45.0)
    keys = [(0.0, start_v), (2.2, pocket_v), (V["hinge"] + 0.3, ring_v), (V["filters"] - 0.8, dict(ring_v, d=0.88)), (V["filters"] + 0.3, top_v), (V["filters"] + 1.4, scr_a),
            (V["easy"] + 1.6, scr_b), (V["end"] - 0.2, wide)]

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return keys[-1][1]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])
    from bpy_extras.object_utils import world_to_camera_view
    px_ = lambda p_: (lambda q: (q.x * 1920, (1 - q.y) * 1080, q.z))(world_to_camera_view(sc, c, Vector(tuple(p_))))
    # how much of the red circle's line the camera sees while it is lit
    sc.frame_set(round((V["hinge"] + 1.5) * FPS))
    cam = c.matrix_world.translation
    on_line = np.where(np.abs(d84 - RR) < 0.6 * RW)[0]
    nv = np.array([tuple((core.matrix_world.to_3x3() @ core.data.vertices[int(i)].normal).normalized()) for i in on_line])
    seen = []
    for i, n_ in zip(on_line, nv):
        p_ = Vector(tuple(wv[i])) + 0.0008 * Vector(tuple(n_))
        d_ = cam - p_
        x_, y_, z_ = px_(p_)
        if z_ > 0 and 0 <= x_ <= 1920 and 0 <= y_ <= 1080 and Vector(tuple(n_)).dot(d_) > 0 and tree.ray_cast(p_, d_.normalized(), d_.length)[0] is None:
            seen.append((x_, y_))
    seen = np.array(seen) if seen else np.zeros((0, 2))
    print("4-09 red circle: %d of %d points on its line in view and unhidden at t %.1f; on screen x %s, y %s" % (
        len(seen), len(on_line), V["hinge"] + 1.5, "%.0f-%.0f" % (seen[:, 0].min(), seen[:, 0].max()) if len(seen) else "-",
        "%.0f-%.0f" % (seen[:, 1].min(), seen[:, 1].max()) if len(seen) else "-"))
    vis_all = [(i, Vector(tuple(wv[i])), Vector(tuple(n_))) for i, n_ in zip(on_line, nv)]
    g_s = np.random.default_rng(8)
    found = []
    for _ in range(400):
        a_, r_ = g_s.uniform(0, 2 * math.pi), math.radians(75) * math.sqrt(g_s.uniform())
        dv = (Quaternion(nrm, a_) @ (Quaternion(nrm.orthogonal().normalized(), r_) @ nrm)).normalized()
        if dv.z < 0.25:
            continue
        eye = S84 + 1.0 * dv
        n_ok = sum(1 for i, p0, n_ in vis_all if n_.dot(eye - p0) > 0 and tree.ray_cast(p0 + 0.0008 * n_, (eye - p0).normalized(), (eye - p0).length)[0] is None)
        found.append((n_ok, math.degrees(math.atan2(dv.x, -dv.y)), math.degrees(math.asin(dv.z)), math.degrees(dv.angle(nrm))))
    found.sort(reverse=True)
    print("4-09 red circle, best views (seen of %d, az, el, off the mouth's axis):" % len(vis_all), "; ".join("%d %.0f %.0f %.0f" % f_ for f_ in found[:6]),
          "| the views so far: pocket az %.0f el %.0f" % (math.degrees(pocket_v["az"]), math.degrees(pocket_v["el"])))
    marks = dict(pocket=tuple(mid), met84=tuple(S84), ring_first=tuple(RC[0]), ring_6=tuple(RC[6]), ring_35=tuple(RC[35]), ring_last=tuple(RC[41]), screen_mid=(C.x, C.y, ZR),
                 far_edge=(cx, cy + 0.33, SCR), far_left=(cx - 0.415, cy + 0.33, SCR), far_right=(cx + 0.415, cy + 0.33, SCR), near_edge=(cx, cy - 0.33, SCR))
    for tt in (2.2, V["hinge"] + 1.5, V["toss"] + 1.0, V["score"] + 1.5, V["easy"] + 1.5, V["end"] - 0.1):
        sc.frame_set(round(tt * FPS))
        print("4-09 t %.1f:" % tt, ", ".join("%s %.0f %.0f" % (k, *px_(p_)[:2]) for k, p_ in marks.items()))
    # for the overlay: where the pocket and Met84 sit on screen, every 0.1 s while they are in view
    track = []
    for f in range(0, round((V["filters"] + 0.2) * FPS) + 1, 6):
        sc.frame_set(f)
        track.append([round(f / FPS, 1), *[round(v_) for v_ in px_(mid)[:2]], *[round(v_) for v_ in px_(S84)[:2]]])
    print("4-09 TRACK", json.dumps(track, separators=(",", ":")))
    RED3 = np.array(P.RED[:3])
    co0 = np.zeros(len(cme_.vertices) * 3, np.float32)

    def update(t):
        t = t - START
        upd_lp(START + lp_off + t)
        cme_.vertices.foreach_get("co", co0)          # shot lp's first ring sits on ring 17; folded to a point here, so the two never flicker through each other
        c3 = co0.reshape(42, nR, 3)
        c3[0] = RC[17]
        cme_.vertices.foreach_set("co", co0)
        cme_.update()
        # the patch, from the centre out, and back to blue at the end
        grow = smooth((t - 0.6) / 1.8) * (1 - smooth((t - V["end"] + 2.4) / 1.4))
        R = 0.5 + (RMAX - 0.5) * grow
        for n_ in reveal:
            n_.inputs["From Min"].default_value, n_.inputs["From Max"].default_value = R - 1.6, R
        wire.hide_render = bool(grow <= 0.001)
        # the red circle: opens out from Met84, pulses twice, stays lit until the camera leaves
        x = (t - V["hinge"] - 0.2) / 0.5
        on = smooth(x) * (1 - smooth((t - V["filters"] - 0.4) / 0.6))
        Rc = RR * (smooth(x) + 0.08 * math.sin(math.pi * min(1.0, max(0.0, x))))
        dd.inputs[1].default_value = Rc
        fill.inputs["From Min"].default_value, fill.inputs["From Max"].default_value = Rc - 0.6, Rc
        amt.inputs[1].default_value = on
        pul = 1.0 + sum(0.9 * math.sin(math.pi * (t - tp) / 0.35) for tp in (V["hinge"] + 1.0, V["hinge"] + 1.6) if 0 <= t - tp < 0.35)
        em.inputs[1].default_value = 2.5 * pul
        # the molecules
        for k, md in enumerate(mols):
            if md is None:
                continue
            ps = mol_pose(k, t)
            o = md["obj"]
            o.hide_render = ps is None
            if ps is None:
                o.location, o.scale = (float(RC[k][0]), float(RC[k][1]), ZR), (1e-3,) * 3
                continue
            zo, s_, q = ps
            o.location = (float(RC[k][0]), float(RC[k][1]), ZR + zo)
            o.scale = (s_,) * 3
            o.rotation_quaternion = q
        # the red groups light on "reactive or possibly toxic", blinking twice
        xb = t - V["toss"] - 0.6
        hb.inputs["Emission Strength"].default_value = 0.4 + (5.0 * max(0.0, math.sin(2 * math.pi * 1.6 * xb)) if 0 <= xb < 1.25 else 0.0) + (2.0 if xb >= 1.25 else 0.0)
        # the rings: a flash as each molecule comes up, red and dim once its molecule has sunk back
        if t >= T_POP[0] - 0.05:
            col = np.zeros(len(cme_.vertices) * 4, np.float32)
            cme_.attributes["col"].data.foreach_get("color", col)
            col = col.reshape(42, nR, 4)
            gl = np.zeros(len(cme_.vertices), np.float32)
            cme_.attributes["glow"].data.foreach_get("value", gl)
            gl = gl.reshape(42, nR)
            for k in range(42):
                xp = (t - T_POP[k]) / 0.35
                if 0 <= xp < 1:
                    gl[k] *= 1 + 1.5 * (1 - xp)
                if k in T_SINK:
                    rd = smooth((t - T_SINK[k] - 0.15) / 0.4)
                    col[k, :, :3] = col[k, :, :3] * (1 - rd) + RED3 * rd
                    gl[k] *= 1 - 0.55 * rd
            cme_.attributes["col"].data.foreach_set("color", col.ravel())
            cme_.attributes["glow"].data.foreach_set("value", gl.ravel())
            cme_.update()
        # the score bars
        for (k, j), b_ in bars.items():
            h = B_MAX * b_["score"] * smooth((t - T_BAR[j][k]) / 0.5)
            b_["obj"].scale = (1.0, 1.0, max(h, 1e-4))
            b_["obj"].hide_render = bool(h <= 1e-4)
        sky(0.2)
    return update


HK_HINGE_I = 104               # the outline point nearest Met84's backbone (0.7 A off it; Met84 lies 2.0 A off the cut's plane), from the kept cut of pocket_outline.py
HK_C = (-3.643, 5.65)          # the centre the outline was drawn about, in A (across, out) from the pocket's centre: pocket_outline.json is that outline less this, over its half size


def shot_hk(sc, sky):
    """4-09 version K (the director's 11-06 note: everyone must follow it, not only someone who has read the notes; the A version's small molecules and rings did not read).
    Built on the storyboard that read best in a blind test: the pocket is a keyhole and each design is a key, as the voice-over itself says ("every key").
    "The team gave it the pocket's shape": over CDK20 the pocket's outline (the hollow cut through the AlphaFold DB v6 model, pocket_outline.py, as S3's keyhole) lifts off
    and flies to the AI's screen, where a plate grows behind it: the outline becomes a keyhole. "And one rule: every key must grip a spot called the hinge": the outline carries
    a blue dot at Met84 (the hinge residue in Ren 2023), and one key comes up out of the screen and rests its tip on the dot. "Its filters are built to toss designs with
    reactive or possibly toxic groups": nine more keys come up out of the screen's rings and hop onto a belt in the next cell; it runs them through a gate with a warning sign,
    and the four carrying a red group are tossed into a bin. "And to score how drug-like and easy to make each one is": behind each key that is left two glass tubes fill,
    one capped with a pill, one with a flask. The keys, the groups and the scores are drawn; the pocket's outline and Met84 are the v6 model.
    Run: blender -b -P bl_inserts.py -- hk <out dir> 0 1019 16 0.5 2"""
    global START
    from mathutils.bvhtree import BVHTree
    import bmesh
    upd_lp = shot_lp(sc, sky)
    lp_off = LP_VO["end"] - LP_T0
    START = HZ_START
    V = HZ_VO
    ob = bpy.data.objects
    core = ob["core"]
    held = polar((127.55, -4.55, 1.75), (127.0, -2.3, 0.24), 60)
    bpy.context.view_layer.update()
    wv = np.array([tuple(core.matrix_world @ v.co) for v in core.data.vertices])
    P0 = Vector(wv.mean(0).tolist())
    full = np.load(HERE + "frames/cdk20.npz")
    q0 = Vector(full["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    smw = ob["cdk20_small"].matrix_world
    q0m = np.array(q0.to_matrix())
    to_w = lambda x: smw @ Vector((np.asarray(x) @ q0m.T * P_S).tolist())
    dir_w = lambda d: (smw.to_3x3() @ Vector((q0m @ np.asarray(d, float)).tolist())).normalized()
    mid = to_w(full["pocket"])
    unit = (to_w(np.asarray(full["pocket"]) + (1.0, 0, 0)) - mid).length
    nrm = dir_w(full["mouth"])
    tree = BVHTree.FromPolygons([tuple(v) for v in wv], [tuple(p_.vertices) for p_ in core.data.polygons])
    cx, cy = cell_at(31)
    c2x, c2y = cell_at(32)
    C = Vector((cx, cy + 0.02, 0.002))

    ink_c = (0.012, 0.012, 0.014)
    ink = gk.surface(ink_c, 0.3)
    card_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    steel = P.gloss((0.6, 0.59, 0.57), 0.22, 0.5)
    gate_m = P.gloss((0.1, 0.1, 0.105), 0.35, 0.4)
    bin_m = gk.surface((0.62, 0.6, 0.56), 0.6, 0.1)

    def glow_m(name, col, st):
        m_, n_, o_ = gk._mat(name)
        b_ = n_.nodes.new("ShaderNodeBsdfPrincipled")
        b_.inputs["Base Color"].default_value = b_.inputs["Emission Color"].default_value = (*col, 1)
        b_.inputs["Emission Strength"].default_value = st
        b_.inputs["Roughness"].default_value = 0.3
        n_.links.new(b_.outputs[0], o_.inputs["Surface"])
        return m_, b_
    hot_m, hot_b = glow_m("hk_hot", P.RED, 0.4)
    blue_m, blue_b = glow_m("hk_blue", P.BLUE, 1.0)
    sign_m, sign_b = glow_m("hk_sign", P.RED, 0.3)

    # the pocket's patch turns to paper, from the centre out (as in version A)
    dist = np.linalg.norm(wv - np.array(tuple(mid)), axis=1)
    m = core.active_material
    if m.users > 1:
        m = m.copy()
        core.active_material = m
    nt = m.node_tree
    cb = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    core.data.attributes.new("pk", "FLOAT", "POINT")
    core.data.attributes["pk"].data.foreach_set("value", (dist / unit).astype(np.float32))
    at_ = nt.nodes.new("ShaderNodeAttribute")
    at_.attribute_name = "pk"
    reveal = nt.nodes.new("ShaderNodeMapRange")
    reveal.clamp = True
    nt.links.new(at_.outputs["Fac"], reveal.inputs["Value"])
    reveal.inputs["To Min"].default_value, reveal.inputs["To Max"].default_value = 1.0, 0.0
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    if cb.inputs["Base Color"].is_linked:
        nt.links.new(cb.inputs["Base Color"].links[0].from_socket, mx.inputs[6])
    else:
        mx.inputs[6].default_value = cb.inputs["Base Color"].default_value
    mx.inputs[7].default_value = (0.9, 0.885, 0.84, 1)
    nt.links.new(reveal.outputs[0], mx.inputs[0])
    nt.links.new(mx.outputs[2], cb.inputs["Base Color"])
    RMAX = 15.0

    # 4-07's 42 rings, where shot lp left them
    upd_lp(HZ_START + lp_off)
    cme_ = bpy.data.meshes["lp_comets"]
    nR = len(cme_.vertices) // 42
    rco = np.zeros(len(cme_.vertices) * 3)
    cme_.vertices.foreach_get("co", rco)
    rco = rco.reshape(42, nR, 3)
    RC = rco.mean(1)
    ZR = float(RC[:, 2].mean())
    rad = np.hypot(rco[..., 0] - RC[:, None, 0], rco[..., 1] - RC[:, None, 1])
    HOLE, OUTR, RT = float(rad.min()), float(rad.max()), float((rco[..., 2] - RC[:, None, 2]).max())
    scr = ob["lp_screen"]
    sbb = np.array([tuple(scr.matrix_world @ Vector(b_)) for b_ in scr.bound_box])
    SCR = float(sbb[:, 2].max())
    print("4-09K rings: plane %.4f hole %.4f outer %.4f tube %.4f | rings x %.3f..%.3f y %.3f..%.3f | screen x %.3f..%.3f y %.3f..%.3f top %.4f | cell 31 %.3f %.3f" % (
        ZR, HOLE, OUTR, RT, RC[1:, 0].min(), RC[1:, 0].max(), RC[1:, 1].min(), RC[1:, 1].max(), sbb[:, 0].min(), sbb[:, 0].max(), sbb[:, 1].min(), sbb[:, 1].max(), SCR, cx, cy))

    # ---------------------------------------------------------------- the keyhole plate on the far edge of the screen
    OL = json.load(open(HERE + "frames/pocket_outline.json"))
    olp = np.array(OL["points"], float)
    HR, HC = 0.05, 0.088                     # the hole's half size and its centre's height on the plate
    PW, PH, TH = 0.15, 0.17, 0.014           # the plate's width, height and thickness
    hole2 = olp * HR + (0.0, HC)
    hinge2 = hole2[HK_HINGE_I]
    y_back = float(sbb[:, 1].max()) - 0.012
    px_c = float(np.clip(RC[1:, 0].max() - 0.1, cx - 0.3, cx + 0.3))
    plate = empty("hk_plate")
    plate.location = (px_c, y_back, SCR)
    plate.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
    y_f = y_back - TH
    pl_poly = box(-PW / 2, PW / 2, PH, 0.0, 0.02)
    front = B.extrude([pl_poly, [tuple(p) for p in hole2[::-1]]], TH - 0.004, 0.0015, z=0.004, name="hk_plate_front", mat=card_m)
    back = B.extrude([pl_poly], 0.004, 0.001, z=0.0, name="hk_plate_back", mat=ink)
    for o in (front, back):
        o.parent = plate
    room_pl = min(float(np.hypot(*(RC[k][:2] - (px_c + x_, y_f)))) - OUTR for k in range(1, 42) for x_ in np.linspace(-PW / 2, PW / 2, 15))
    print("4-09K plate: back %.3f, front %.3f, x %.3f; from its front edge to the nearest ring's outside %.4f (want > 0); screen far edge %.3f" % (
        y_back, y_f, px_c, room_pl, sbb[:, 1].max()))

    # the outline that flies there, with the hinge dot on it, in the plate's own units
    def poly_tube(pts, r, mat, name, cyclic=True):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth, cu.bevel_resolution = r, 4
        cu.use_fill_caps = True
        s = cu.splines.new("POLY")
        s.points.add(len(pts) - 1)
        for q, p in zip(s.points, pts):
            q.co = (*p, 1)
        s.use_cyclic_u = cyclic
        o = bpy.data.objects.new(name, cu)
        sc.collection.objects.link(o)
        cu.materials.append(mat)
        return o
    ol = empty("hk_outline")
    R_OL = 0.0016
    line = poly_tube([(x, y, 0.0) for x, y in hole2], R_OL, ink, "hk_outline_line")
    line.parent = ol
    line.data.bevel_factor_mapping_end = "SPLINE"
    dot = lathe([(0, -0.001), (0.0062, -0.001), (0.0065, 0.0), (0.0062, 0.001), (0, 0.001)], blue_m, "hk_dot", ol, 48)
    dot.location = (float(hinge2[0]), float(hinge2[1]), 0.0)
    # where it starts: the real outline over the pocket's mouth, at its real size
    th = math.radians(OL["deg"])
    m0 = np.asarray(full["mouth"], float) / np.linalg.norm(full["mouth"])
    a0 = np.cross(m0, [0, 0, 1.0])
    a0 /= np.linalg.norm(a0)
    b0 = np.cross(m0, a0)
    U_w, M_w = dir_w(math.cos(th) * a0 + math.sin(th) * b0), dir_w(m0)
    N_w = U_w.cross(M_w).normalized()
    kk = unit * OL["angstrom"] / HR
    Rm = Matrix((U_w, M_w, N_w)).transposed()
    q_pk = Rm.to_quaternion()
    base = mid + unit * (HK_C[0] * U_w + HK_C[1] * M_w) - kk * HC * M_w

    def ol_world(loc, q, s_):
        R_ = np.array(q.to_matrix())
        return np.c_[hole2, np.zeros(len(hole2))] @ R_.T * s_ + np.array(tuple(loc))

    lift = 0.0
    for lift in [float(x_) for x_ in range(60)]:
        w_ = ol_world(base + lift * unit * M_w, q_pk, kk)
        if min(tree.find_nearest(Vector(tuple(p)))[3] for p in w_[::2]) > 2.5 * unit:
            break
    ol_a = base + (lift + 1.0) * unit * M_w
    q_pl = plate.rotation_quaternion.copy()
    ol_b = Vector((px_c, y_f - R_OL - 0.0002, SCR))
    print("4-09K outline: real half size %.1f A = %.4f table units; lifted %.0f A off the pocket to clear the body by 2.5 A; scale at the pocket %.3f" % (
        OL["angstrom"], unit * OL["angstrom"], lift + 1.0, kk))
    T_OL0, T_OL1, T_FLY0, T_FLY1 = 0.8, 1.5, 1.9, 2.9
    T_PL0, T_PL1 = 2.5, 3.0

    def ol_pose(t):
        x = smooth((t - T_FLY0) / (T_FLY1 - T_FLY0))
        p_a, p_b = ol_a, ol_b          # up off the pocket first, then down in front of where the plate will stand
        c1, c2 = p_a + 0.12 * M_w + Vector((0, 0, 0.26)), p_b + Vector((0, -0.2, 0.22))
        loc = (1 - x) ** 3 * p_a + 3 * (1 - x) ** 2 * x * c1 + 3 * (1 - x) * x ** 2 * c2 + x ** 3 * p_b
        return loc, q_pk.slerp(q_pl, x), math.exp(math.log(kk) * (1 - x))

    # ---------------------------------------------------------------- the keys
    KS = 0.056 / 3.25
    KH = 0.12 * KS

    def key_parts(bad):
        parts = [B.extrude([B.round_poly(B.key_blade(-0.075, 0.0, start=0.14), 0.03)], 0.2, 0.04, z=-0.1, name="hk_blade", mat=steel)]
        ring_ = [(-0.875 + 0.75 * math.cos(2 * math.pi * i / 96), 0.75 * math.sin(2 * math.pi * i / 96)) for i in range(96)]
        parts.append(B.extrude([ring_], 0.24, 0.05, z=-0.12, name="hk_bow", mat=steel))
        bm = bmesh.new()

        def tag(r_, mi):
            for f_ in {f for v in r_["verts"] for f in v.link_faces}:
                f_.material_index = mi
                f_.smooth = True

        def ball(c_, r, mi=0):
            tag(bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r, matrix=Matrix.Translation(c_)), mi)

        def stick(a_, b_, r=0.04, mi=0):
            d_ = b_ - a_
            M = (Matrix.Translation((a_ + b_) / 2) @ Vector((0, 0, 1)).rotation_difference(d_.normalized()).to_matrix().to_4x4())
            tag(bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r, depth=d_.length, matrix=M), mi)
        bc = Vector((-0.875, 0.0, 0.14))
        hexa = [bc + Vector((0.42 * math.cos(math.radians(30 + 60 * i)), 0.42 * math.sin(math.radians(30 + 60 * i)), 0.0)) for i in range(6)]
        for c_ in hexa:
            ball(c_, 0.085)
        for i in range(6):
            stick(hexa[i], hexa[(i + 1) % 6])
        if bad:          # the reactive group: off the ring's top atom, out past the bow's edge
            top = bc + Vector((0, 0.42, 0))
            stick(top, bc + Vector((0, 1.0, 0)), 0.06, 1)
            ball(bc + Vector((0, 1.2, 0.06)), 0.3, 1)          # its bottom stays above the key's underside
        me = bpy.data.meshes.new("hk_hex")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(ink)
        me.materials.append(hot_m)
        o = bpy.data.objects.new("hk_hex", me)
        sc.collection.objects.link(o)
        parts.append(o)
        pts = []
        for o in parts:
            v_ = np.zeros(len(o.data.vertices) * 3)
            o.data.vertices.foreach_get("co", v_)
            pts.append(v_.reshape(-1, 3))
        pts = np.concatenate(pts)
        return parts, pts
    tmpl = {False: key_parts(False), True: key_parts(True)}
    for parts, _ in tmpl.values():
        for o in parts:
            o.hide_render = True
            o.location = (0, 0, -5)
    NK = 10
    BAD = (2, 4, 6, 8)
    g_ = np.random.default_rng(7)
    keys = []
    for i in range(NK):
        e = empty("hk_key")
        for o in tmpl[i in BAD][0]:
            c_ = o.copy()
            sc.collection.objects.link(c_)
            c_.location = (0, 0, 0)
            c_.hide_render = False
            c_.parent = e
        pts = tmpl[i in BAD][1]
        sub = pts[np.random.default_rng(i).choice(len(pts), min(400, len(pts)), replace=False)]
        keys.append(dict(obj=e, pts=sub * KS, yaw=float(g_.uniform(-0.6, 0.6))))
    for o in bpy.context.selected_objects:          # B.extrude applies transforms to whatever is selected; the key parts now share their meshes
        o.select_set(False)
    ext_k = float(np.hypot(keys[3]["pts"][:, 0], keys[3]["pts"][:, 1]).max())
    print("4-09K key: %.4f long, reaches %.4f from its centre, %.4f thick" % (3.25 * KS, ext_k, 2 * KH))

    # the belt in the next cell, its gate with a warning sign, the bin
    BWD, BH = 0.09, 0.012
    bx0, bx1 = c2x - 0.40, c2x + 0.40
    by = c2y + 0.05
    belt = B.extrude([box(bx0, bx1, by + BWD / 2, by - BWD / 2, 0.012)], BH, 0.003, name="hk_belt", mat=ink)
    bm_, bnt, bout = gk._mat("hk_belt")
    bb_ = bnt.nodes.new("ShaderNodeBsdfPrincipled")
    bb_.inputs["Roughness"].default_value = 0.6
    tc = bnt.nodes.new("ShaderNodeTexCoord")
    mp = bnt.nodes.new("ShaderNodeMapping")
    bnt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wvt = bnt.nodes.new("ShaderNodeTexWave")
    wvt.wave_type, wvt.bands_direction = "BANDS", "X"
    wvt.inputs["Scale"].default_value = 2 * math.pi / (20 * 0.02)
    bnt.links.new(mp.outputs["Vector"], wvt.inputs["Vector"])
    ramp = bnt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.45, 0.55
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (0.05, 0.05, 0.055, 1), (0.16, 0.16, 0.17, 1)
    bnt.links.new(wvt.outputs["Fac"], ramp.inputs["Fac"])
    bnt.links.new(ramp.outputs["Color"], bb_.inputs["Base Color"])
    bnt.links.new(bb_.outputs[0], bout.inputs["Surface"])
    belt.data.materials.clear()
    belt.data.materials.append(bm_)
    VB = 0.22                                 # the belt's speed
    XS = bx0 + 0.035                          # where the keys land on it
    S_G, S_T = 0.10, 0.16                     # the gate, and where a bad key is tossed
    gx = XS + S_G
    GH, GP = 0.11, 0.012
    gy0, gy1 = by - BWD / 2 - 0.014, by + BWD / 2 + 0.014
    gate = [B.extrude([box(gx - GP / 2, gx + GP / 2, y_ + GP / 2, y_ - GP / 2, 0.003)], GH, 0.002, name="hk_post", mat=gate_m) for y_ in (gy1,)]          # one post, behind: nothing stands between the camera and the keys
    gate.append(B.extrude([box(gx - GP / 2, gx + GP / 2, gy1 + GP / 2, gy0 - GP / 2, 0.003)], 0.014, 0.002, z=GH, name="hk_lintel", mat=gate_m))
    sign = empty("hk_sign")
    sign.location = (gx, gy0, GH + 0.014)          # standing on the lintel, over the near post
    sign.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
    tri = [(0.032 * math.cos(math.radians(90 + 120 * i)), 0.032 * math.sin(math.radians(90 + 120 * i)) + 0.016) for i in range(3)]
    B.extrude([B.round_poly(tri, 0.006)], 0.004, 0.001, z=0.0, name="hk_sign_tri", mat=sign_m).parent = sign
    B.extrude([box(-0.0028, 0.0028, 0.03, 0.0125, 0.0025)], 0.002, 0.0005, z=0.004, name="hk_sign_bar", mat=card_m).parent = sign
    B.extrude([box(-0.003, 0.003, 0.0095, 0.0035, 0.0028)], 0.002, 0.0005, z=0.004, name="hk_sign_dot", mat=card_m).parent = sign
    BIN_RI0, BIN_RI1, BIN_H, BIN_W = 0.043, 0.052, 0.07, 0.003
    bin_c = Vector((XS + S_T, by + BWD / 2 + BIN_RI1 + BIN_W + 0.012, 0.0))          # behind the belt, so it hides neither the belt nor the gate
    binn = lathe([(0, 0), (BIN_RI0 + BIN_W, 0), (BIN_RI1 + BIN_W, BIN_H), (BIN_RI1, BIN_H), (BIN_RI0, BIN_W), (0, BIN_W)], bin_m, "hk_bin")
    binn.location = bin_c

    # the tubes behind each key that is left
    glass = B.clear_glass()
    fill_m = [P.gloss(ink_c, 0.3, 0.6), P.gloss((0.55, 0.54, 0.5), 0.3, 0.6)]          # drug-like dark, easy to make light grey (blind read 5 still could not tell 0.3 grey from ink)
    TR, TUH = 0.0075, 0.1
    t_y = by + BWD / 2 + 0.03
    T_STOP = 10.3
    TL = [6.9 + 0.25 * i for i in range(NK)]          # 0.055 apart on the belt: room for a red group between two keys
    kept = [i for i in range(NK) if i not in BAD]
    s_end = {i: VB * (T_STOP - TL[i]) for i in kept}
    pill_m, flask_m = P.gloss((0.93, 0.925, 0.89), 0.3, 0.6), B.clear_glass()
    tubes = {}
    g_s = np.random.default_rng(31)
    for i in kept:
        for j in range(2):
            x_ = XS + s_end[i] + (2 * j - 1) * 0.0125
            o = lathe([(0, 0), (TR, 0), (TR, TUH), (0.0, TUH + 0.0005)], glass, "hk_tube", None, 32)
            o.location = (x_, t_y, 0.0)
            o.visible_shadow = False
            f_ = lathe([(0, 0.0008), (TR - 0.0012, 0.0008), (TR - 0.0012, 1.0), (0, 1.0)], fill_m[j], "hk_fill", None, 32)
            f_.location = (x_, t_y, 0.0)
            if j == 0:          # a pill lying across the tube's top
                cap = lathe([(0, -0.012), (0.0036, -0.0112), (0.0052, -0.009), (0.0058, -0.006), (0.0058, 0.006), (0.0052, 0.009), (0.0036, 0.0112), (0, 0.012)], pill_m, "hk_pill", None, 24)
                cap.rotation_mode = "XYZ"
                cap.rotation_euler = (0, math.pi / 2, 0.0)
                cap.location = (x_, t_y, TUH + 0.0005 + 0.0058)
            else:              # a small flask standing on it
                cap = lathe([(0, 0), (0.0088, 0), (0.0093, 0.0011), (0.003, 0.0125), (0.003, 0.0185), (0.0037, 0.0192), (0, 0.0192)], flask_m, "hk_flask", None, 24)
                cap.location = (x_, t_y, TUH + 0.0005)
            tubes[(i, j)] = dict(fill=f_, tube=o, cap=cap, cz=float(cap.location.z), score=float(g_s.uniform(0.45, 0.95)), x=x_)
    T_FILL = [{i: V["score"] + 0.3 + 0.12 * n for n, i in enumerate(kept)}, {i: V["easy"] + 0.1 + 0.12 * n for n, i in enumerate(kept)}]

    # the rings the keys come out of: key 0 from the ring nearest the plate, the rest from the screen's right-hand rings, nearest the belt first
    live = list(range(1, 42))
    r0 = min(live, key=lambda k: math.hypot(RC[k][0] - px_c, RC[k][1] - y_f))
    rest = sorted([k for k in live if k != r0], key=lambda k: -RC[k][0])[:NK - 1]
    rest.sort(key=lambda k: math.hypot(RC[k][0] - XS, RC[k][1] - by))
    RING = [r0] + rest
    Z_HOV = [ZR + 0.05 + 0.014 * (i % 2) for i in range(NK)]
    T_POP = [3.35] + [V["filters"] - 0.3 + 0.04 * n for n in range(NK - 1)]
    T_HOP = 0.55
    # blind read 4 could not see how a ring makes a key: as each key comes up, its ring flashes a halo and the key itself glows the screen's blue, then cools to bone.
    # Both run on the object colour (Object Info), since the keys share one material and the rings are one mesh.
    st_n = steel.node_tree.nodes
    st_b = next(n for n in st_n if n.type == "BSDF_PRINCIPLED")
    oi = st_n.new("ShaderNodeObjectInfo")
    sp = st_n.new("ShaderNodeSeparateColor")
    mu = st_n.new("ShaderNodeMath")
    mu.operation = "MULTIPLY"
    mu.inputs[1].default_value = 3.0
    steel.node_tree.links.new(oi.outputs["Color"], sp.inputs[0])
    steel.node_tree.links.new(sp.outputs[0], mu.inputs[0])
    steel.node_tree.links.new(mu.outputs[0], st_b.inputs["Emission Strength"])
    st_b.inputs["Emission Color"].default_value = (0.15, 0.3, 1.0, 1)
    for kd in keys:
        for o in kd["obj"].children:
            o.color = (0, 0, 0, 1)
    ping_m, ping_n, ping_o = gk._mat("hk_ping")
    p_em = ping_n.nodes.new("ShaderNodeEmission")
    p_em.inputs["Color"].default_value = (0.55, 0.7, 1.0, 1)
    p_em.inputs["Strength"].default_value = 4.0
    p_tr = ping_n.nodes.new("ShaderNodeBsdfTransparent")
    p_mx = ping_n.nodes.new("ShaderNodeMixShader")
    p_oi = ping_n.nodes.new("ShaderNodeObjectInfo")
    p_sp = ping_n.nodes.new("ShaderNodeSeparateColor")
    ping_n.links.new(p_oi.outputs["Color"], p_sp.inputs[0])
    ping_n.links.new(p_sp.outputs[0], p_mx.inputs[0])
    ping_n.links.new(p_tr.outputs[0], p_mx.inputs[1])
    ping_n.links.new(p_em.outputs[0], p_mx.inputs[2])
    ping_n.links.new(p_mx.outputs[0], ping_o.inputs["Surface"])
    rm_, rt_ = (HOLE + OUTR) / 2, (OUTR - HOLE) / 2 * 1.3          # a halo just round the ring's own tube
    halo_pf = [(rm_ + rt_ * math.cos(2 * math.pi * j / 16), rt_ * math.sin(2 * math.pi * j / 16)) for j in range(17)]
    pings = []
    for i in range(NK):
        o = lathe(halo_pf, ping_m, "hk_ping%d" % i, None, 64)
        o.location = (float(RC[RING[i]][0]), float(RC[RING[i]][1]), float(RC[RING[i]][2]))
        o.color = (0, 0, 0, 1)
        o.hide_render = True
        pings.append(o)
    q_belt = Quaternion((0, 0, 1), math.pi / 2)
    rest_z = BH + KH + 0.0003
    land = lambda i: Vector((XS, by, rest_z))
    # the grip: key 0 upright in front of the plate, its tip on the dot
    hc2 = olp.mean(0) * HR + (0.0, HC)
    d2 = (hinge2 - hc2) / np.linalg.norm(hinge2 - hc2)
    Xw, Zw = Vector((float(d2[0]), 0.0, float(d2[1]))), Vector((0, -1, 0))
    Yw = Zw.cross(Xw)
    q_grip = Matrix((Xw, Yw, Zw)).transposed().to_quaternion()
    y_key = y_f - R_OL * 2 - 0.0002 - 0.0005 - KH
    tip_l = Vector((1.625 * KS, 0.0, 0.0))
    dot_w = Vector((px_c + float(hinge2[0]), y_key, SCR + float(hinge2[1])))
    p_grip = dot_w - (q_grip @ tip_l)
    p_grip.y = y_key
    T_G0, T_G1, T_G2 = 3.9, 4.6, 5.4
    BAD_T = {i: TL[i] + S_T / VB for i in BAD}
    BIN_Z = {i: BIN_W + KH + 0.0003 + n * 0.0115 for n, i in enumerate(BAD)}          # a key with its red group stands 10 mm tall

    def bez(a_, c_, b_, x):
        return (1 - x) ** 2 * a_ + 2 * (1 - x) * x * c_ + x ** 2 * b_

    def key_pose(i, t):
        """Where key i is at t: location, turn and scale, or None before it shows."""
        kd = keys[i]
        if t < T_POP[i]:
            return None
        rc = Vector((float(RC[RING[i]][0]), float(RC[RING[i]][1]), ZR))
        q_h = Quaternion((0, 0, 1), kd["yaw"])
        x = (t - T_POP[i]) / 0.5
        hov = Vector((rc.x, rc.y, Z_HOV[i] + 0.0015 * math.sin(2 * math.pi * 0.6 * t + i)))
        if x < 1:          # up out of the ring, small while it is level with the ring's tube
            zz = ZR + (Z_HOV[i] - ZR) * smooth(min(1.0, x * 1.6))
            s_ = 0.25 * smooth(x / 0.25) + 1e-3 if x < 0.25 else 0.25 + 0.75 * smooth((x - 0.25) / 0.75)
            return Vector((rc.x, rc.y, zz)), q_h, s_
        if i == 0 and t < TL[0]:
            if t < T_G0:
                return hov, q_h, 1.0
            if t < T_G1:          # over to the plate, standing up as it comes
                y = smooth((t - T_G0) / (T_G1 - T_G0))
                ctrl = Vector((p_grip.x, p_grip.y - 0.12, max(p_grip.z, hov.z) + 0.04))
                return bez(hov, ctrl, p_grip, y), q_h.slerp(q_grip, y), 1.0
            if t < T_G2:
                nud = 0.0006 * math.sin(math.pi * min(1.0, max(0.0, (t - T_G1 - 0.05) / 0.25)))
                return p_grip + Xw * nud, q_grip, 1.0
            y = smooth((t - T_G2) / (TL[0] - T_G2))
            p_a = p_grip + Vector((0, -0.03, 0))
            ctrl = Vector(((p_grip.x + XS) / 2, min(p_grip.y, by) - 0.15, 0.26))
            if t < T_G2 + 0.25:
                return p_grip + (p_a - p_grip) * smooth((t - T_G2) / 0.25), q_grip, 1.0
            y = smooth((t - T_G2 - 0.25) / (TL[0] - T_G2 - 0.25))
            return bez(p_a, ctrl, land(0), y), q_grip.slerp(q_belt, y), 1.0
        if t < TL[i] - T_HOP:
            return hov, q_h, 1.0
        if t < TL[i]:
            y = smooth((t - TL[i] + T_HOP) / T_HOP)
            ctrl = Vector(((hov.x + XS) / 2, (hov.y + by) / 2, 0.15))
            return bez(hov, ctrl, land(i), y), q_h.slerp(q_belt, y), 1.0
        s_ = VB * (min(t, T_STOP) - TL[i])
        on = Vector((XS + s_, by, rest_z))
        if i in BAD and t >= BAD_T[i]:
            ta = BAD_T[i]
            p_a = Vector((XS + S_T, by, rest_z))
            top_ = Vector((bin_c.x, bin_c.y, BIN_H + 0.045))
            bot_ = Vector((bin_c.x, bin_c.y, BIN_Z[i]))
            q_bin = Quaternion((0, 0, 1), math.pi / 2 + 0.25 * (i - 5))
            y = (t - ta) / 0.5
            if y < 1:          # tossed up and over the bin's rim, turning over once on the way
                yy = smooth(y)
                ctrl = Vector((p_a.x, (p_a.y + top_.y) / 2, 0.21))
                spin = Quaternion((1, 0, 0), 2 * math.pi * smooth((y - 0.15) / 0.7))          # turns over once once it is clear of the belt
                return bez(p_a, ctrl, top_, yy), q_belt.slerp(q_bin, smooth((y - 0.5) / 0.5)) @ spin, 1.0
            y2 = min(1.0, (t - ta - 0.5) / 0.22)
            return top_ + (bot_ - top_) * (y2 * y2), q_bin, 1.0
        return on, q_belt, 1.0

    def key_world(i, t):
        ps = key_pose(i, t)
        if ps is None:
            return None
        loc, q, s_ = ps
        return keys[i]["pts"] @ np.array(q.to_matrix()).T * s_ + np.array(tuple(loc))

    # ---------------------------------------------------------------- checks
    rims = []
    for i_ in (30, 31, 32, 22, 23):
        x_, y_ = cell_at(i_)
        rims.append((x_, y_))

    def in_rim(p):
        """True where a point lies inside a cell's raised rim (outer box less inner box, 0.016 high)."""
        out_ = np.zeros(len(p), bool)
        for x_, y_ in rims:
            dx, dy = np.abs(p[:, 0] - x_), np.abs(p[:, 1] - y_)
            out_ |= (dx < 0.437) & (dy < 0.352) & ~((dx < 0.418) & (dy < 0.333)) & (p[:, 2] < 0.0175)
        return out_

    bad_hits = {}

    def hit(name, t):
        bad_hits.setdefault(name, []).append(round(t, 2))
    tube_xy = np.array([[v_["x"], t_y] for v_ in tubes.values()])
    for f in range(0, FRAMES, 2):
        t = f / FPS
        W_ = {i: key_world(i, t) for i in range(NK)}
        for i, w_ in W_.items():
            if w_ is None:
                continue
            ps = key_pose(i, t)
            # its own ring's tube, and every ring's tube, while level with them
            for k in range(1, 42):
                r_ = np.hypot(w_[:, 0] - RC[k][0], w_[:, 1] - RC[k][1])
                band = (np.abs(w_[:, 2] - ZR) < RT + 0.0005) & (r_ > HOLE - 0.0005) & (r_ < OUTR + 0.0005)
                if band.any():
                    hit("key %d / ring %d" % (i, k), t)
            if (w_[:, 2] < SCR - 1e-4).any() and (np.abs(w_[:, 0] - cx) < 0.42).all():
                hit("key %d / screen" % i, t)
            if in_rim(w_).any():
                hit("key %d / cell rim" % i, t)
            onb = (np.abs(w_[:, 0] - (bx0 + bx1) / 2) < (bx1 - bx0) / 2) & (np.abs(w_[:, 1] - by) < BWD / 2)
            if (onb & (w_[:, 2] < BH - 1e-4)).any():
                hit("key %d / belt" % i, t)
            if ((np.abs(w_[:, 0] - gx) < GP / 2 + 0.0005) & (((np.abs(w_[:, 1] - gy1) < GP / 2 + 0.0005) & (w_[:, 2] < GH + 0.0145)) | ((w_[:, 1] > gy0 - GP / 2 - 0.0005) & (w_[:, 1] < gy1 + GP / 2 + 0.0005) & (w_[:, 2] > GH - 0.0005) & (w_[:, 2] < GH + 0.0145)))).any():
                hit("key %d / gate" % i, t)
            rb = np.hypot(w_[:, 0] - bin_c.x, w_[:, 1] - bin_c.y)
            zb = w_[:, 2]
            r_in = BIN_RI0 + (BIN_RI1 - BIN_RI0) * np.clip(zb / BIN_H, 0, 1)
            if (((rb > r_in - 0.0005) & (rb < r_in + BIN_W + 0.0005) & (zb < BIN_H + 0.0005)) | ((rb < r_in) & (zb < BIN_W + 1e-4))).any():
                hit("key %d / bin" % i, t)
            if ((np.abs(w_[:, 0] - px_c) < PW / 2 + 0.0005) & (w_[:, 1] > y_f - 0.0003) & (w_[:, 1] < y_back + 0.0005) & (w_[:, 2] < SCR + PH + 0.0005)).any():
                hit("key %d / plate" % i, t)
            if t > T_FLY1 and i == 0:
                lw = np.c_[hole2[:, 0] + px_c, np.full(len(hole2), ol_b.y), hole2[:, 1] + SCR]
                dmin = min(float(np.linalg.norm(lw - p_, axis=1).min()) for p_ in w_[::4])
                if dmin < R_OL + 0.0002:
                    hit("key 0 / outline", t)
            if len(tube_xy) and (np.hypot(w_[:, None, 0] - tube_xy[None, :, 0], w_[:, None, 1] - tube_xy[None, :, 1]) < TR + 0.0005).any() and (w_[:, 2] < TUH + 0.01).any():
                hit("key %d / tube" % i, t)
            if (w_[:, 2] < 1e-4).any():
                hit("key %d / table" % i, t)
        for i in range(NK):
            for j in range(i + 1, NK):
                if W_[i] is None or W_[j] is None:
                    continue
                a_, b_ = W_[i], W_[j]
                if np.linalg.norm(a_.mean(0) - b_.mean(0)) > 0.08:
                    continue
                dmin = np.sqrt(((a_[::2, None, :] - b_[None, ::2, :]) ** 2).sum(-1)).min()
                if dmin < 0.0015:
                    hit("key %d / key %d" % (i, j), t)
    # the outline in flight, against the body, the plate and the rings
    for f in range(round(T_OL0 * FPS), round(T_FLY1 * FPS) + 1, 2):
        t = f / FPS
        loc, q, s_ = ol_pose(t)
        w_ = ol_world(loc, q, s_)
        if min(tree.find_nearest(Vector(tuple(p)))[3] for p in w_[::3]) < R_OL * s_ + 0.0005:
            hit("outline / body", t)
        if (w_[:, 2] < SCR + 0.002).any():
            hit("outline / screen", t)
        gr = smooth((t - T_PL0) / (T_PL1 - T_PL0))
        if gr > 0 and ((np.abs(w_[:, 0] - px_c) < PW / 2 * gr) & (w_[:, 1] > y_f - R_OL * s_) & (w_[:, 2] < SCR + PH * gr)).any():
            hit("outline / plate", t)
    print("4-09K clashes:", "none" if not bad_hits else "; ".join("%s at %s" % (k, v[:4]) for k, v in sorted(bad_hits.items())))
    print("4-09K times: tossed at %s; kept keys end at s %s; belt end %.3f" % (
        {i: round(v, 2) for i, v in BAD_T.items()}, {i: round(v, 3) for i, v in s_end.items()}, bx1 - XS))

    # ---------------------------------------------------------------- the camera
    pocket_v = dict(at=tuple(lerp(tuple(mid), tuple(ol_a), 0.8)), az=held["az"] - math.radians(6), el=math.radians(50), d=1.25, mm=45.0)
    fly_v = dict(at=tuple(lerp(tuple(ol_a), (px_c, y_f, SCR + 0.15), 0.6)), az=math.radians(4), el=math.radians(34), d=1.5, mm=45.0)
    start_v = dict(pocket_v, d=1.7, el=math.radians(48), az=held["az"] + math.radians(10))
    plate_v = dict(at=(px_c, y_f, SCR + 0.085), az=math.radians(6), el=math.radians(14), d=0.62, mm=45.0)
    grip_v = dict(plate_v, at=(px_c + 0.012, y_f, SCR + 0.075), d=0.4)
    belt_a = dict(at=(cx + 0.38, (cy + by) / 2 - 0.04, 0.03), az=math.radians(4), el=math.radians(48), d=0.85, mm=45.0)
    belt_b = dict(at=(XS + 0.17, by + 0.01, 0.03), az=math.radians(8), el=math.radians(44), d=0.74, mm=45.0)
    row_a = dict(at=(XS + 0.5, by + 0.035, 0.065), az=math.radians(8), el=math.radians(32), d=0.74, mm=45.0)
    row_b = dict(row_a, at=(XS + 0.48, by + 0.035, 0.068), az=math.radians(1), d=0.7)
    wide = dict(at=((cx + c2x) / 2, (cy + P0.y) / 2 - 0.05, 0.1), az=held["az"] + math.radians(2), el=math.radians(40), d=3.0, mm=45.0)
    toss_v = dict(at=(XS + S_T - 0.02, by + 0.035, 0.045), az=math.radians(6), el=math.radians(38), d=0.46, mm=45.0)          # in close on the first two tossed
    cams = [(0.0, start_v), (1.3, pocket_v), (1.9, pocket_v), (2.45, fly_v), (3.1, plate_v), (T_G1 - 0.2, grip_v), (T_G2, grip_v), (V["filters"] - 0.2, belt_a), (7.4, belt_a),
            (7.95, toss_v), (8.9, toss_v), (9.4, belt_b), (9.75, belt_b), (V["score"] + 0.2, row_a), (V["end"] - 2.2, row_b), (V["end"] - 0.2, wide)]

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(cams, cams[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return cams[-1][1]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])
    from bpy_extras.object_utils import world_to_camera_view
    px_ = lambda p_: (lambda q: (q.x * 1920, (1 - q.y) * 1080, q.z))(world_to_camera_view(sc, c, Vector(tuple(p_))))

    # for the overlay: where the things the notes point at sit on screen, every 0.1 s
    def anchors(t):
        loc, q, s_ = ol_pose(min(max(t, T_OL0), T_FLY1))
        olc = Vector(tuple(ol_world(loc, q, s_).mean(0)))
        dw = loc + q @ Vector((float(hinge2[0]), float(hinge2[1]), 0.0)) * s_
        tip = key_world(0, t)
        return dict(pk=mid, ol=olc, dot=dw, scr=Vector((cx + 0.15, cy - 0.12, SCR)), sign=sign.matrix_world.translation + Vector((0, 0, 0.016)),
                    bin=bin_c + Vector((0, 0, BIN_H)), tube0=Vector((tubes[(kept[2], 0)]["x"], t_y, TUH + 0.009)), tube1=Vector((tubes[(kept[2], 1)]["x"], t_y, TUH + 0.02)),
                    red=red_at(t),
                    cdk=P0)
    def red_at(t):          # the red ball of the first key tossed
        ps = key_pose(BAD[0], t)
        if ps is None:
            return Vector((0, 0, 0))
        loc, q, s_ = ps
        return loc + q @ (Vector((-0.875, 1.2, 0.2)) * KS * s_)
    track = []
    for f in range(0, FRAMES, 6):
        sc.frame_set(f)
        a = anchors(f / FPS)
        track.append([round(f / FPS, 1)] + [round(v_) for k in ("ol", "dot", "scr", "sign", "bin", "tube0", "tube1", "red", "cdk", "pk") for v_ in px_(a[k])[:2]])
    if SHOT == "hk":          # W3 builds on this shot and must not overwrite 4-09's track
        json.dump(dict(keys=["ol", "dot", "scr", "sign", "bin", "tube0", "tube1", "red", "cdk", "pk"], track=track), open(HERE + "frames/hk_track.json", "w"), separators=(",", ":"))
    for tt in (1.4, 3.0, 4.8, 6.6, 8.0, 9.0, 12.0, 14.5, 16.9):
        sc.frame_set(round(tt * FPS))
        a = anchors(tt)
        print("4-09K t %.1f:" % tt, ", ".join("%s %.0f %.0f" % (k, *px_(p_)[:2]) for k, p_ in a.items()))

    def update(t):
        t = t - START
        upd_lp(START + lp_off + t)
        cme_.vertices.foreach_get("co", co0)
        c3 = co0.reshape(42, nR, 3)
        c3[0] = RC[17]
        cme_.vertices.foreach_set("co", co0)
        cme_.update()
        grow = smooth((t - 0.3) / 1.2) * (1 - smooth((t - V["end"] + 2.4) / 1.4))
        R = 0.5 + (RMAX - 0.5) * grow
        reveal.inputs["From Min"].default_value, reveal.inputs["From Max"].default_value = R - 1.6, R
        # the outline: drawn round over the pocket, then off to the plate
        dr = smooth((t - T_OL0) / (T_OL1 - T_OL0))
        line.data.bevel_factor_end = max(dr, 1e-3)
        line.hide_render = dr <= 0
        loc, q, s_ = ol_pose(t)
        ol.location, ol.rotation_quaternion, ol.scale = loc, q, (s_,) * 3
        dot.hide_render = t < T_OL1 - 0.1
        dsc = smooth((t - T_OL1 + 0.1) / 0.3) * (1 + 0.35 * sum(math.sin(math.pi * (t - tp) / 0.3) for tp in (V["hinge"] + 0.1, V["hinge"] + 0.6, T_G1 + 0.05) if 0 <= t - tp < 0.3))
        dot.scale = (max(dsc, 1e-3), max(dsc, 1e-3), 1.0)
        blue_b.inputs["Emission Strength"].default_value = 1.0 + 3.0 * (dsc > 1.01)
        # the plate grows up behind the outline from its base
        gr = smooth((t - T_PL0) / (T_PL1 - T_PL0))
        plate.scale = (max(gr, 1e-3), max(gr, 1e-3), 1.0)
        for o in plate.children:
            o.hide_render = gr <= 0
        # the keys
        for i, kd in enumerate(keys):
            ps = key_pose(i, t)
            e = kd["obj"]
            for o in e.children:
                o.hide_render = ps is None
            if ps is None:
                e.scale = (1e-4,) * 3
                continue
            loc, q, s_ = ps
            e.location, e.rotation_quaternion, e.scale = loc, q, (KS * s_,) * 3
            g_ = 1.0 - smooth((t - T_POP[i] - 0.35) / 0.7)          # made in the ring: glowing as it comes up, cool by the time it hovers
            for o in e.children:
                o.color = (g_, 0, 0, 1)
        for i, o in enumerate(pings):
            x = (t - T_POP[i] + 0.12) / 0.6
            o.hide_render = not (0 <= x < 1)
            if 0 <= x < 1:
                o.color = (math.sin(math.pi * min(1.0, x * 1.6)) if x < 0.3125 else 1.0 - smooth((x - 0.3125) / 0.6875), 0, 0, 1)
                o.scale = (1 + 0.15 * x, 1 + 0.15 * x, 1.0)
        # the belt runs while keys are on it
        travel = VB * (min(max(t, TL[0]), T_STOP) - TL[0])
        mp.inputs["Location"].default_value[0] = -travel
        # the warning: the red groups light as the filters are named, the sign flashes as each bad key reaches the gate
        hot_b.inputs["Emission Strength"].default_value = 0.4 + (3.0 * max(0.0, math.sin(2 * math.pi * 1.6 * (t - V["toss"]))) if 0 <= t - V["toss"] < 1.25 else 0.0) + (1.5 if t >= V["toss"] + 1.25 else 0.0)
        sign_b.inputs["Emission Strength"].default_value = 0.3 + sum(4.0 * math.sin(math.pi * (t - BAD_T[i] + 0.15) / 0.45) for i in BAD if 0 <= t - BAD_T[i] + 0.15 < 0.45)
        # the score tubes fill
        for (i, j), tb in tubes.items():
            up = smooth((t - V["score"] + 0.6 - 0.06 * kept.index(i)) / 0.5)          # the empty tubes grow up from the table as the scoring starts, then the caps sit on
            tb["tube"].scale = (1.0, 1.0, max(up, 1e-3))
            tb["tube"].hide_render = up <= 0
            cu_ = smooth((t - V["score"] - 0.1 - 0.06 * kept.index(i)) / 0.3)
            tb["cap"].scale = (max(cu_, 1e-3),) * 3
            tb["cap"].location.z = TUH + 0.0005 + (tb["cz"] - TUH - 0.0005) * max(cu_, 1e-3)
            tb["cap"].hide_render = cu_ <= 0
            h = (TUH - 0.002) * tb["score"] * smooth((t - T_FILL[j][i]) / 0.6)
            tb["fill"].scale = (1.0, 1.0, max(h, 1e-4))
            tb["fill"].hide_render = h <= 1e-4
        sky(0.2)
    co0 = np.zeros(len(cme_.vertices) * 3, np.float32)
    update.ctx = dict(locals())          # W3 picks up from here
    return update


W3_START = 574.0               # 4-09 ends at 09:34
W3_BEAT = 60.0 / 121.0          # Take My Breath, bar 104 (207.711 s into the track) lands on 09:34
W3_BAR = 4 * W3_BEAT


def shot_w3(sc, sky):
    """W3 (09:34-09:50, 8 bars of The Weeknd - Take My Breath from bar 104, no voice-over): the music window between 4-09 and 4-10. Storyboard W3_storyboard_1.png.
    It picks up 4-09's last frame. Bar 0: the camera pushes in on the keyhole plate at the screen's far edge. Bar 1: the plate lifts off and grows into a lock, three
    tick rings coming up round the keyhole; the outline and its blue Met84 dot are the ones from 4-09. Bars 2-3: one key hovers over the lock and changes its cut on
    every beat while the rings click round a step each beat, alternate ways. Bars 4-5: the screen's rings send up more and more keys (half beats, then quarter beats),
    each one glowing as it comes up, and they circle the lock in three lanes. Bar 6: the circling runs up until the keys smear (real motion blur, keyframed). Bar 7: on
    the downbeat it all stops, and the keys rain down into the two empty cells on the left (21 and 30) as an even carpet, with more falling in from above, while the
    camera climbs to look down on them: 4-10 starts from that carpet. No key ever goes into the lock. The keys and the lock are drawn; the outline and Met84 are
    the AlphaFold DB v6 model's, as in 4-09.
    Run: blender -b -P bl_inserts.py -- w3 <out dir> 0 951 16 0.5 2"""
    global START
    import bmesh
    upd_hk = shot_hk(sc, sky)
    X = upd_hk.ctx
    START = HZ_START
    upd_hk(HZ_START + HZ_VO["end"])          # 4-09's last frame, held: nothing of it moves again
    START = W3_START
    ob = bpy.data.objects
    ob["lp_sparks"].hide_render = True          # 4-07's sparks, shrunk to 0.1 mm points in the rings' centres since 4-07: the keys come up through them
    plate, ol, keys, tmpl = X["plate"], X["ol"], X["keys"], X["tmpl"]
    RC, ZR, HOLE, OUTR, RT, SCR = X["RC"], X["ZR"], X["HOLE"], X["OUTR"], X["RT"], X["SCR"]
    px_c, y_f, y_back, TH, HC, PW, PH = X["px_c"], X["y_f"], X["y_back"], X["TH"], X["HC"], X["PW"], X["PH"]
    KS, KH, cx, cy, sbb, tree = X["KS"], X["KH"], X["cx"], X["cy"], X["sbb"], X["tree"]
    steel, ink, hot_m, ping_m, halo_pf = X["steel"], X["ink"], X["hot_m"], X["ping_m"], X["halo_pf"]
    BEAT, BAR = W3_BEAT, W3_BAR

    # ---------------------------------------------------------------- the lock: the plate and its outline on one pivot at the keyhole's centre
    L0 = Vector((px_c, y_back - TH / 2, SCR + HC))
    GS = 2.6                                  # how much the plate grows
    LZ = 1.0                                  # the keyhole's centre ends this high over the screen
    Lc = Vector((px_c, y_back - TH / 2, SCR + LZ))
    lk = empty("w3_lock")
    lk.location = L0
    bpy.context.view_layer.update()
    for o in (plate, ol):
        o.parent = lk
        o.matrix_parent_inverse = lk.matrix_world.inverted()
    T_LIFT0, T_LIFT1 = BAR + 0.05, 2 * BAR - 0.25

    def lock_pose(t):
        x = smooth((t - T_LIFT0) / (T_LIFT1 - T_LIFT0))
        s_ = 1 + (GS - 1) * smooth((t - T_LIFT0 - 0.35) / (T_LIFT1 - T_LIFT0 - 0.35))          # it lifts first and grows once it is clear
        return L0 + (Lc - L0) * x, s_

    # three dials round the keyhole, in front of the plate, in the plate's units (the lock scales them)
    DIAL = [(0.098, 36), (0.116, 24), (0.134, 16)]
    TR_D = 0.0032
    DY = -(TH / 2 + 0.0045)                   # in front of the plate's face and the outline
    T_DIAL = [BAR + 2 * BEAT + 0.1 * n for n in range(3)]          # beats 6, 6 and a bit: they open out as the lock finishes growing

    def dial(r, n, k):
        e = empty("w3_dial%d" % k)
        e.parent = lk
        e.location = (0.0, DY, 0.0)
        rg = lathe([(r + TR_D * math.cos(2 * math.pi * j / 16), TR_D * math.sin(2 * math.pi * j / 16)) for j in range(17)], steel, "w3_ring%d" % k, e, 160)
        rg.color = (0, 0, 0, 1)          # the keys' steel glows by object colour (4-09); the dials never glow
        for nm, mat, sel in (("w3_ticks%d" % k, ink, range(1, n)), ("w3_notch%d" % k, hot_m, range(0, 1))):
            bm = bmesh.new()
            for i in sel:
                a = 2 * math.pi * i / n
                M = Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((r + TR_D + 0.0045, 0, 0)) @ Matrix.Diagonal((0.008 if nm[3] == "t" else 0.011, 0.0022, 0.0035, 1))
                bmesh.ops.create_cube(bm, size=1.0, matrix=M)
            me = bpy.data.meshes.new(nm)
            bm.to_mesh(me)
            bm.free()
            me.materials.append(mat)
            o = bpy.data.objects.new(nm, me)
            sc.collection.objects.link(o)
            o.parent = e
        return e
    dials = [dial(r, n, k) for k, (r, n) in enumerate(DIAL)]
    D_OUT = DIAL[-1][0] + TR_D + 0.0045 + 0.0055          # the dials' outer reach, plate units

    def dial_turn(k, t):
        """Each dial clicks round one tick on every beat from bar 2, the middle one the other way; faster from bar 4."""
        if t < 2 * BAR:
            return 0.0
        n_ = DIAL[k][1]
        b_ = (t - 2 * BAR) / BEAT
        steps = math.floor(b_) + smooth((b_ % 1) / 0.25)
        if t > 4 * BAR:
            b2 = (t - 4 * BAR) / (BEAT / 2)
            steps = 8 + math.floor(b2) + smooth((b2 % 1) / 0.3)
        return (1 if k != 1 else -1) * (k + 1) * steps * 2 * math.pi / n_

    # ---------------------------------------------------------------- key shapes: the 4-09 key with a new cut for every beat
    rng = np.random.default_rng(104)
    cuts = []
    for v_ in range(24):
        n_t = 3 + v_ % 2
        xs_ = np.linspace(0.5, 1.36, n_t)
        teeth = tuple((float(x_), float(rng.uniform(0.05, 0.36))) for x_ in xs_)
        o = B.extrude([B.round_poly(B.key_blade(-0.075, 0.0, teeth=teeth, start=0.14), 0.03)], 0.2, 0.04, z=-0.1, name="w3_blade%d" % v_, mat=steel)
        o.hide_render = True
        o.location = (0, 0, -5)
        cuts.append(o.data)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    parts0 = tmpl[False][0]                   # blade, bow, the ring of six on the bow
    pts0 = tmpl[False][1]
    sub0 = pts0[np.random.default_rng(3).choice(len(pts0), min(160, len(pts0)), replace=False)]

    def make_key(name, cut):
        e = empty(name)
        for n_, o in enumerate(parts0):
            c_ = o.copy()
            sc.collection.objects.link(c_)
            c_.location = (0, 0, 0)
            c_.hide_render = False
            c_.parent = e
            c_.color = (0, 0, 0, 1)
            if n_ == 0:
                c_.data = cuts[cut % len(cuts)]
        e.scale = (1e-4,) * 3
        for o in e.children:
            o.hide_render = True
        return e

    def show(e, on):
        for o in e.children:
            o.hide_render = not on

    def glow(e, g_):
        for o in e.children:
            o.color = (g_, 0, 0, 1)

    # ---------------------------------------------------------------- the hovering key
    hov = make_key("w3_hover", 0)
    KSH = 3.2
    T_HOV = 2 * BAR
    HOV_L = Vector((0.0, -0.085, 0.0))        # in the lock's frame, scaled by it: in front of the circling lanes
    HOV_Z = 0.2                             # its centre over the keyhole's centre, lock units
    q_down = Quaternion((1, 0, 0), math.pi / 2) @ Quaternion((0, 0, 1), -math.pi / 2)          # standing in the lock's plane, tip down at the keyhole

    def hover_cut(t):
        if t < 4 * BAR:
            return int((t - T_HOV) / BEAT)
        if t < 6 * BAR:
            return 8 + int((t - 4 * BAR) / (BEAT / 2))
        return 24 + int((t - 6 * BAR) / (BEAT / 4))

    # ---------------------------------------------------------------- the circling keys
    NO = 40
    POP = [4 * BAR + i * BEAT / 2 for i in range(4)] + [4 * BAR + 2 * BEAT + i * BEAT / 4 for i in range(8)] + [5 * BAR + i * BEAT / 8 for i in range(28)]          # half beats, quarter beats, eighth beats
    RISE = 0.8
    JOIN = [p + RISE for p in POP]
    KSO = 2.6
    LANE_R = [0.47, 0.54, 0.61]
    LANE_Y = [-0.08, -0.115, -0.15]          # world offsets from the lock's mid plane, toward the camera
    DELTA = 2 * math.pi / 42
    ZQ = SCR + 0.2                            # the height the keys cross at, under every lane
    TH_E = -math.pi / 2                       # they join at the bottom of the circle, moving right
    T_STOP = 7 * BAR
    W_MAX = 13.0
    t_last, th_last = JOIN[-1], (NO - 1) * DELTA
    w_last = DELTA / (JOIN[-1] - JOIN[-2])

    def Theta(t):
        """How far the lanes have turned. Each key joins as the lanes come round by one step, so lane-mates keep three steps apart; after the last join it runs up to W_MAX."""
        if t <= JOIN[0]:
            return (t - JOIN[0]) * DELTA / (JOIN[1] - JOIN[0])
        if t <= t_last:
            k = max(i for i in range(NO) if JOIN[i] <= t)
            if k == NO - 1:
                return th_last
            return k * DELTA + (t - JOIN[k]) / (JOIN[k + 1] - JOIN[k]) * DELTA
        tt = min(t, T_STOP) - t_last
        T_ = T_STOP - t_last
        return th_last + w_last * tt + (W_MAX - w_last) * tt ** 3 / (3 * T_ ** 2)          # the speed climbs as tt squared

    by_x = sorted(range(1, 42), key=lambda k: RC[k][0])
    band = [by_x[27:], by_x[14:27], by_x[:14]]          # lane 0 takes its keys in furthest right, lane 2 furthest left: each takes them from its own third of the screen, so the paths up never cross
    band = [sorted(b_, key=lambda k: (-RC[k][1], -RC[k][0])) for b_ in band]          # the far rows first: their keys have the least way to go
    ORB = []
    for i in range(NO):
        ORB.append(dict(obj=make_key("w3_orb%d" % i, 3 + 5 * i), ring=band[i % 3][i // 3], lane=i % 3, yaw=float(rng.uniform(-0.6, 0.6))))
    pings = []
    for i in range(NO):
        o = lathe(halo_pf, ping_m, "w3_ping%d" % i, None, 64)
        r_ = ORB[i]["ring"]
        o.location = (float(RC[r_][0]), float(RC[r_][1]), float(RC[r_][2]))
        o.color = (0, 0, 0, 1)
        o.hide_render = True
        pings.append(o)

    def lane_pt(L, th):
        return Vector((Lc.x + LANE_R[L] * math.cos(th), Lc.y + LANE_Y[L], Lc.z + LANE_R[L] * math.sin(th)))

    def q_lane(th):
        return Quaternion((1, 0, 0), math.pi / 2) @ Quaternion((0, 0, 1), th + math.pi / 2)

    def bez3(a_, b_, c_, d_, x):
        return (1 - x) ** 3 * a_ + 3 * (1 - x) ** 2 * x * b_ + 3 * (1 - x) * x ** 2 * c_ + x ** 3 * d_

    def orb_air(i, t):
        """Key i circling, or on its way up: location, turn, scale; None before it comes up."""
        kd = ORB[i]
        if t < POP[i]:
            return None
        rc = Vector((float(RC[kd["ring"]][0]), float(RC[kd["ring"]][1]), ZR))
        q_h = Quaternion((0, 0, 1), kd["yaw"])
        L = kd["lane"]
        te = TH_E - 0.3 * L          # the lanes take their keys in at three points, so the keys coming up spread out
        if t < JOIN[i]:
            x = (t - POP[i]) / RISE
            if x < 0.25:          # 1: up out of its ring, small while it is level with the ring's tube
                y = x / 0.25
                s_ = KSO * (0.25 * smooth(y / 0.4) if y < 0.4 else 0.25 + 0.75 * smooth((y - 0.4) / 0.6))
                return Vector((rc.x, rc.y, ZR + 0.06 * smooth(y))), q_h, max(s_, 1e-3)
            j_ = lane_pt(L, te)
            q_ = Vector((j_.x, j_.y, ZQ))
            p0 = Vector((rc.x, rc.y, ZR + 0.06))
            if x < 0.6:          # 2: across, under every lane, to below its way in, standing up into its lane's plane as it goes
                y = (x - 0.25) / 0.35
                return bez3(p0, p0 + Vector((0, 0, 0.05)), q_ - Vector((0, 0, 0.05)), q_, smooth(y)), q_h.slerp(q_lane(te), smooth(y)), KSO
            y = (x - 0.6) / 0.4          # 3: up in that plane, past the outer lanes' keys, and into its lane at about the lane's speed
            tg = Vector((-math.sin(te), 0, math.cos(te)))
            return bez3(q_, q_ + Vector((0, 0, 0.08)), j_ - 0.12 * tg, j_, y * y * (2 - y)), q_lane(te), KSO
        th = te + Theta(t) - i * DELTA
        return lane_pt(L, th), q_lane(th), KSO

    # ---------------------------------------------------------------- the carpet: two empty cells, ten keys across and fourteen down in each
    CELLS = (21, 30)
    NX, NY = 10, 14
    slots = []
    for c_ in CELLS:
        x0_, y0_ = cell_at(c_)
        for r_ in range(NY):
            for k_ in range(NX):
                slots.append(Vector((x0_ - 0.34 + 0.0755 * k_ + (0.018 if r_ % 2 else 0.0), y0_ + 0.29 - 0.0446 * r_, KH + 0.0003)))
    NS = len(slots)
    q_flat = Quaternion((0, 0, 1), 0.0)
    T_RAIN = T_STOP + BEAT / 2                # held still for half a beat, then they come down
    # the circling keys and the hovering one land in the cell nearer the lock, nearest slot first; the rest fall in from above
    near = sorted(range(NS), key=lambda s: (slots[s] - Vector((Lc.x, Lc.y, 0.0))).length)
    fliers = list(range(NO)) + ["h"]
    stop_pos = {i: orb_air(i, T_STOP)[0] for i in range(NO)}
    stop_pos["h"] = None
    fl_slot = {}
    free = set(range(NS))
    # slots for the fliers: the leftmost flier takes the leftmost of the nearest free slots
    front = [s for s in near if s >= NX * NY and (s - NX * NY) // NX >= 3]          # cell 30's rows from the fourth on: in front of the lock's plane, so a path there never crosses the lock
    cand = sorted(front[:NO + 1], key=lambda s: (slots[s].x, -slots[s].y))
    order_f = sorted(range(NO), key=lambda i: (stop_pos[i].x, stop_pos[i].z))
    for i, s in zip(order_f, cand[:NO]):
        fl_slot[i] = s
        free.discard(s)
    fl_slot["h"] = cand[NO]
    free.discard(cand[NO])
    FL_T = {i: T_RAIN + 1.0 * BEAT * (n / NO) for n, i in enumerate(order_f)}
    FL_T["h"] = T_RAIN + 0.3 * BEAT
    FL_D = 0.95
    rest_s = sorted(free, key=lambda s: (slots[s] - Vector((Lc.x, Lc.y, 0.0))).length)
    NR = len(rest_s)
    rain = []
    for n, s in enumerate(rest_s):
        rain.append(dict(obj=make_key("w3_rain%d" % n, 7 + 11 * n), slot=s, t0=T_RAIN + 0.05 + 0.6 * n / NR + float(rng.uniform(0, 0.06)),
                         yaw=float(rng.uniform(-0.2, 0.2)), tilt=float(rng.uniform(-0.5, 0.5))))
    R_H, R_D = 1.6, 0.62                      # they fall from 1.6 above the table, 0.62 s to land

    def settle(dt):
        """A small hop after landing."""
        if dt < 0 or dt > 0.3:
            return 0.0
        return 0.004 * math.sin(math.pi * dt / 0.15) if dt < 0.15 else 0.0012 * math.sin(math.pi * (dt - 0.15) / 0.15)

    def flier_pose(i, t):
        """A circling key (or the hovering one) after the stop: held, then an arc down onto its slot."""
        if i == "h":
            lp_, ls_ = lock_pose(t)
            p_a = lp_ + Vector((HOV_L.x * ls_, HOV_L.y * ls_, HOV_Z * ls_))
            q_a, s_a = q_down, KSH
        else:
            p_a, q_a, s_a = orb_air(i, T_STOP)
        s_b = Vector(slots[fl_slot[i]])
        x = (t - FL_T[i]) / FL_D
        if x <= 0:
            return p_a, q_a, s_a
        if x >= 1:
            return s_b + Vector((0, 0, settle(t - FL_T[i] - FL_D))), q_flat, 1.0
        pos = bez3(p_a, p_a + Vector((0, -0.3, 0.2)), s_b + Vector((0, 0, 0.55)), s_b, min(1.0, max(0.0, x)))          # toward the camera first, clear of the lock
        return pos, q_a.slerp(q_flat, smooth(min(1.0, x / 0.85))), s_a + (1.0 - s_a) * smooth(x / 0.4)          # down to carpet size early, so they have room in the air

    def rain_pose(d, t):
        x = (t - d["t0"]) / R_D
        if x < 0:
            return None
        s_b = Vector(slots[d["slot"]])
        if x >= 1:
            return s_b + Vector((0, 0, settle(t - d["t0"] - R_D))), q_flat, 1.0
        z = R_H * (1 - x * x)
        w_ = 1 - x
        q = Quaternion((0, 0, 1), d["yaw"] * w_) @ Quaternion((1, 0, 0), d["tilt"] * w_)
        return s_b + Vector((0, 0, z)), q, 1.0

    def hover_pose(t):
        if t < T_HOV:
            return None
        if t >= FL_T["h"]:
            return flier_pose("h", t)
        lp_, ls_ = lock_pose(t)
        x = (t - T_HOV) / 0.35
        s_ = KSH * (smooth(x) if x < 1 else 1.0)
        bob = 0.004 * math.sin(2 * math.pi * (t - T_HOV) / (2 * BEAT))
        return lp_ + Vector((HOV_L.x * ls_, HOV_L.y * ls_, (HOV_Z + bob) * ls_)), q_down, max(s_, 1e-3)

    def key_pose(i, t):
        if i == "h":
            return hover_pose(t)
        if isinstance(i, int):
            if t >= T_STOP:
                return flier_pose(i, t)
            return orb_air(i, t)
        return rain_pose(rain[i[1]], t)

    ALL = ["h"] + list(range(NO)) + [("r", n) for n in range(NR)]
    obj_of = lambda i: hov if i == "h" else (ORB[i]["obj"] if isinstance(i, int) else rain[i[1]]["obj"])
    T_SET = max(max(d["t0"] for d in rain) + R_D, max(FL_T.values()) + FL_D) + 0.31          # every key lies still from here
    print("W3: lock to %.3f over the screen at x %.3f y %.3f, %.2fx; lanes %s; %d circling, %d raining, %d slots in cells %s" % (LZ, Lc.x, Lc.y, GS, LANE_R, NO, NR, NS, CELLS))

    # ---------------------------------------------------------------- the camera
    wide = X["wide"]
    push_v = dict(at=(px_c, y_f, SCR + 0.1), az=math.radians(5), el=math.radians(26), d=1.15, mm=45.0)
    lock_v = dict(at=(Lc.x, Lc.y, Lc.z + 0.08), az=math.radians(3), el=math.radians(10), d=2.7, mm=45.0)
    key_v = dict(lock_v, at=(Lc.x, Lc.y, Lc.z + 0.1), d=2.6, el=math.radians(8))
    orbit_a = dict(at=(Lc.x, Lc.y, Lc.z - 0.05), az=math.radians(-6), el=math.radians(14), d=3.6, mm=45.0)
    orbit_b = dict(orbit_a, az=math.radians(9), d=3.4)
    c21, c30 = cell_at(21), cell_at(30)
    high = dict(at=((c30[0] + c21[0]) / 2 + 0.55, (c30[1] + c21[1]) / 2 - 0.05, 0.15), az=math.radians(4), el=math.radians(58), d=4.6, mm=45.0)
    cams = [(0.0, wide), (BAR - 0.1, push_v), (BAR + 0.3, push_v), (2 * BAR, lock_v), (3 * BAR, key_v), (4 * BAR - 0.1, key_v), (5 * BAR, orbit_a), (T_STOP, orbit_b),
            (T_RAIN, orbit_b), (T_RAIN + 1.4, high)]

    def mix(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def view(t):
        for (ta, a), (tb, b) in zip(cams, cams[1:]):
            if t < tb:
                return mix(a, b, smooth((t - ta) / (tb - ta)))
        return cams[-1][1]
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])

    # ---------------------------------------------------------------- checks, every other frame, nothing rendered
    if SHOT == "w3":          # only when W3 itself renders; w3_end() skips them
        sub = sub0 * KS
        dial_pts = []
        for k, (r, n) in enumerate(DIAL):
            a_ = np.linspace(0, 2 * np.pi, 90, endpoint=False)
            rr = r + TR_D + 0.0045 + 0.0055
            dial_pts.append(np.c_[rr * np.cos(a_), np.full(90, DY), rr * np.sin(a_)])
        dial_pts = np.concatenate(dial_pts)
        pl_pts = np.array([(x_, y_, z_) for x_ in np.linspace(-PW / 2, PW / 2, 9) for y_ in (-TH / 2, TH / 2) for z_ in np.linspace(-HC, PH - HC, 9)])          # the plate's faces about the pivot

        def lock_world(t):
            loc, s_ = lock_pose(t)
            g_ = smooth((t - T_DIAL[0]) / 0.45)
            return (np.concatenate([dial_pts * g_, pl_pts]) if g_ > 0 else pl_pts) * s_ + np.array(tuple(loc))

        def kw(i, t):
            ps = key_pose(i, t)
            if ps is None:
                return None
            loc, q, s_ = ps
            return sub @ np.array(q.to_matrix()).T * s_ + np.array(tuple(loc))

        def in_rims(p):
            out_ = np.zeros(len(p), bool)
            for i_ in (12, 13, 14, 20, 21, 22, 23, 29, 30, 31, 32, 38, 39, 40):
                x_, y_ = cell_at(i_)
                dx, dy = np.abs(p[:, 0] - x_), np.abs(p[:, 1] - y_)
                out_ |= (dx < 0.437) & (dy < 0.352) & ~((dx < 0.418) & (dy < 0.333)) & (p[:, 2] < 0.0175)
            return out_
        bad = {}

        def hit(name, t):
            bad.setdefault(name, []).append(round(t, 2))
        others = [o for o in ob if o.type == "MESH" and not o.name.startswith(("w3_", "hk_", "floor", "lp_comets", "core", "cell")) and not o.hide_render]
        obb = []
        for o in others:
            bb = np.array([tuple(o.matrix_world @ Vector(b_)) for b_ in o.bound_box])
            if (bb.max(0) - bb.min(0))[:2].max() < 1.5:          # the table and its rims are checked on their own
                obb.append((o.name, bb.min(0), bb.max(0)))
        for name, lo, hi in obb:          # what stands in the carpet's cells already
            for c_ in CELLS:
                x_, y_ = cell_at(c_)
                if lo[0] < x_ + 0.42 and hi[0] > x_ - 0.42 and lo[1] < y_ + 0.33 and hi[1] > y_ - 0.33 and lo[2] < 0.3 and hi[2] > 0.0001:
                    hit("cell %d holds %s" % (c_, name), 0.0)
        scr_lo, scr_hi = sbb.min(0), sbb.max(0)
        from mathutils.bvhtree import BVHTree
        _bvh = {}

        def bvh_of(name):
            if name not in _bvh:
                o = ob[name]
                dg = bpy.context.evaluated_depsgraph_get()
                me = o.evaluated_get(dg).to_mesh()
                mw = o.matrix_world
                _bvh[name] = BVHTree.FromPolygons([tuple(mw @ v.co) for v in me.vertices], [tuple(p_.vertices) for p_ in me.polygons]) if len(me.polygons) else BVHTree.FromPolygons([tuple(mw @ v.co) for v in me.vertices] or [(0, 0, -9), (0, 0.001, -9), (0.001, 0, -9)], [(0, 1, 2)] if not len(me.vertices) else [(i, i, i) for i in range(len(me.vertices))])
            return _bvh[name]
        for f in range(0, FRAMES, 2):
            t = f / FPS
            lw = lock_world(t)
            if ((lw[:, 2] < SCR - 0.001) & (lw[:, 0] > scr_lo[0]) & (lw[:, 0] < scr_hi[0]) & (lw[:, 1] > scr_lo[1]) & (lw[:, 1] < scr_hi[1])).any():
                hit("lock / screen", t)
            if t > T_LIFT0 and min(tree.find_nearest(Vector(tuple(p)))[3] for p in lw[::7]) < 0.004:
                hit("lock / CDK20", t)
            Wd = {}
            for i in ALL:
                w_ = kw(i, t)
                if w_ is None:
                    continue
                Wd[i] = w_
                if (w_[:, 2] < 1e-4).any():
                    hit("key %s / table" % (i,), t)
                if in_rims(w_).any():
                    hit("key %s / cell rim" % (i,), t)
                if ((w_[:, 2] < SCR - 1e-4) & (w_[:, 0] > scr_lo[0]) & (w_[:, 0] < scr_hi[0]) & (w_[:, 1] > scr_lo[1]) & (w_[:, 1] < scr_hi[1])).any():
                    hit("key %s / screen" % (i,), t)
                for k in range(1, 42):
                    r_ = np.hypot(w_[:, 0] - RC[k][0], w_[:, 1] - RC[k][1])
                    if ((np.abs(w_[:, 2] - ZR) < RT + 0.0005) & (r_ > HOLE - 0.0005) & (r_ < OUTR + 0.0005)).any():
                        hit("key %s / ring %d" % (i, k), t)
                # the lock: within its outer reach and its slab
                loc, s_ = lock_pose(t)
                d_ = w_ - np.array(tuple(loc))
                rr = np.hypot(d_[:, 0], d_[:, 2])
                if ((rr < D_OUT * s_ + 0.002) & (d_[:, 1] > (DY - TR_D - 0.002) * s_ - 0.001) & (d_[:, 1] < TH / 2 * s_ + 0.001)).any():
                    hit("key %s / lock" % (i,), t)
                if ((np.abs(d_[:, 0]) < PW / 2 * s_ + 0.001) & (d_[:, 2] > -HC * s_ - 0.001) & (d_[:, 2] < (PH - HC) * s_ + 0.001) & (np.abs(d_[:, 1]) < TH / 2 * s_ + 0.002)).any():
                    hit("key %s / plate" % (i,), t)
                if w_[:, 2].min() < 0.6 and min(tree.find_nearest(Vector(tuple(p)))[3] for p in w_[::10]) < 0.003:
                    hit("key %s / CDK20" % (i,), t)
                for name, lo, hi in obb:
                    inb = ((w_ > lo - 0.001) & (w_ < hi + 0.001)).all(1)
                    if inb.any() and min(bvh_of(name).find_nearest(Vector(tuple(p)))[3] for p in w_[inb][::2]) < 0.001:
                        hit("key %s / %s" % (i, name), t)
            ks_ = list(Wd)
            cen = np.array([Wd[i].mean(0) for i in ks_])
            dd = np.sqrt(((cen[:, None] - cen[None]) ** 2).sum(-1)) if len(ks_) else np.zeros((0, 0))
            for a in range(len(ks_)):
                for b in range(a + 1, len(ks_)):
                    if dd[a, b] > 0.16:
                        continue
                    ia, ib = ks_[a], ks_[b]
                    if t > T_SET and not isinstance(ia, int) and not isinstance(ib, int) and ia != "h" and ib != "h":
                        continue          # both lying in their slots
                    if np.sqrt(((Wd[ia][::2, None] - Wd[ib][None, ::2]) ** 2).sum(-1)).min() < 0.0012:
                        hit("key %s / key %s" % (ia, ib), t)
        kinds = {}
        for k, v in bad.items():
            kinds.setdefault(k.split(" / ")[-1].split(" ")[0] if " / " in k else k, []).append((k, v[0]))
        print("W3 clashes:", "none" if not bad else "")
        for kd, l_ in sorted(kinds.items()):
            print("W3 clash %s: %d, first %s" % (kd, len(l_), sorted(l_, key=lambda z: z[1])[:5]))
        print("W3 times: last join %.2f, stop %.2f, rain %.2f-%.2f, last flier lands %.2f, clip end %.2f" % (
            JOIN[-1], T_STOP, T_RAIN, max(d["t0"] for d in rain) + R_D, max(FL_T[i] for i in FL_T) + FL_D, FRAMES / FPS))
        from bpy_extras.object_utils import world_to_camera_view
        for tt in (0.0, BAR, 2 * BAR + 0.5, 4 * BAR + 1.0, 6 * BAR, T_STOP, FRAMES / FPS - 0.05):
            sc.frame_set(round(tt * FPS))
            q_ = world_to_camera_view(sc, c, Lc)
            print("W3 t %.2f: lock on screen %.0f %.0f" % (tt, q_.x * 1920, (1 - q_.y) * 1080))

    # ---------------------------------------------------------------- per frame
    def place(e, ps, f):
        if ps is None:
            show(e, False)
            e.scale = (1e-4,) * 3
            return
        show(e, True)
        e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3

    def keyed(e, i, t, f):
        """Pose at f - 1, f, f + 1 as keys, so the render's motion blur sees how it moves."""
        e.animation_data_clear()
        for df in (-1, 0, 1):
            ps = key_pose(i, t + df / FPS)
            if ps is None:
                continue
            e.location, e.rotation_quaternion, e.scale = ps[0], ps[1], (KS * ps[2],) * 3
            e.keyframe_insert("location", frame=f + df)
            e.keyframe_insert("rotation_quaternion", frame=f + df)
            e.keyframe_insert("scale", frame=f + df)
        place(e, key_pose(i, t), f)

    def update(t):
        t = t - START
        f = round(t * FPS)
        loc, s_ = lock_pose(t)
        lk.location, lk.scale = loc, (s_,) * 3
        for k, e in enumerate(dials):
            g_ = smooth((t - T_DIAL[k]) / 0.45)
            e.scale = (max(g_, 1e-3),) * 3
            for o in e.children:
                o.hide_render = g_ <= 0
            e.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2) @ Quaternion((0, 0, 1), dial_turn(k, t))
        ch = hover_cut(t) if t >= T_HOV else 0
        hov.children[0].data = cuts[ch % len(cuts)]
        for i in ALL:
            e = obj_of(i)
            ps = key_pose(i, t)
            moving = ps is not None and (key_pose(i, t + 1 / FPS) is None or (key_pose(i, t + 1 / FPS)[0] - ps[0]).length > 1e-5)
            if moving:
                keyed(e, i, t, f)
            else:
                e.animation_data_clear()
                place(e, ps, f)
        for i in range(NO):
            g_ = 1.0 - smooth((t - POP[i] - 0.25) / 0.6) if t >= POP[i] else 0.0
            glow(ORB[i]["obj"], g_)
            x = (t - POP[i] + 0.12) / 0.6
            o = pings[i]
            o.hide_render = not (0 <= x < 1)
            if 0 <= x < 1:
                o.color = (math.sin(math.pi * min(1.0, x * 1.6)) if x < 0.3125 else 1.0 - smooth((x - 0.3125) / 0.6875), 0, 0, 1)
                o.scale = (1 + 0.15 * x, 1 + 0.15 * x, 1.0)
        sky(0.2)
    update.view = view          # w3_end() reads W3's last camera from it
    return update


def w3_end(sc, sky):
    """The table exactly as W3 leaves it: W3 built and posed at its last frame, then held still, no keyframes left, the camera at W3's last view and unkeyed. For shots in other
    files (BL_EXTRA) that pick up from W3; 4-10 starts there. Returns W3's update, in case a shot wants to move W3's keys or lock on from there."""
    global START
    keep = START
    upd = shot_w3(sc, sky)
    upd(W3_START + 951 / FPS)
    for o in bpy.data.objects:
        o.animation_data_clear()
    c = sc.camera
    c.data.animation_data_clear()
    v = upd.view(951 / FPS)          # W3's last camera, set once and left unkeyed: the new shot moves it from here
    shoot(c, 0, v, v["at"])
    c.animation_data_clear()
    c.data.animation_data_clear()
    START = keep
    return upd


sc, sky = stage()
SHOTS = dict(a=shot_a, w=shot_w, b=shot_b, c=shot_c, f=shot_f, g=shot_g, h=shot_h, k=shot_k, p=shot_p, q=shot_q, x=shot_x, y=shot_y, z=shot_z, v=shot_v, u=shot_u, t=shot_t, r=shot_r, s=shot_s, n=shot_n, o=shot_o, m=shot_m, j=shot_j, l=shot_l, e=shot_e, d=shot_d, i=shot_i, i2=shot_i2, i3=shot_i3, i4=shot_i4, lp=shot_lp, hz=shot_hz, hk=shot_hk, w3=shot_w3)
if XFILE:          # the other file's shots run here, with every function above in reach; it adds them to SHOTS
    exec(compile(open(XFILE, encoding="utf-8").read(), XFILE, "exec"))
update = SHOTS[SHOT](sc, sky)
sc.frame_start, sc.frame_end = 0, FRAMES
EXT = "png"
if os.environ.get("BL_JPEG"):          # the 4K 60 fps passes: a 4K PNG is ~10 MB, a JPEG at 95 ~2 MB, and the take re-encodes to H.264 anyway
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode, sc.render.image_settings.quality, EXT = "JPEG", "RGB", 95, "jpg"
if os.environ.get("BL_CPU"):          # a quick look while the card is busy
    sc.cycles.device = "CPU"
for f in ([int(x_) for x_ in os.environ["BL_FRAMES"].split(",")] if os.environ.get("BL_FRAMES") else range(FIRST, LAST + 1, STEP)):
    sc.frame_set(f)
    update(START + f / FPS)
    gk.render("%s/%s_%04d.%s" % (OUT, SHOT, f, EXT))
print("INSERT_OK", SHOT, FIRST, LAST)
