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
START = dict(a=32.1, w=35.12, b=35.15, c=43.35, f=78.8, g=146.0, h=224.5, k=285.8, p=312.0, q=330.0, x=330.0, y=412.0, z=437.0, v=412.0, u=412.0, t=412.0, r=412.0, s=412.0, n=412.0, o=412.0)[SHOT]
FRAMES = dict(a=198, w=24, b=218, c=310, f=960, g=414, h=654, k=1644, p=1080, q=4920, x=4920, y=1501, z=721, v=6, u=2551, t=6, r=6, s=6, n=4, o=3)[SHOT]
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
    low, high = dict(a=0.2, w=0.2, b=0.1, c=0.04, f=0.25, g=0.2, h=0.2, k=0.2, p=0.2, q=0.2, x=0.2, y=0.2, z=0.2, v=0.2, u=0.2, t=0.2, r=0.2, s=0.2, n=0.2, o=0.2)[SHOT], dict(a=1.25, w=1.25, b=2.0, c=2.6, f=2.0, g=2.0, h=2.0, k=0.9, p=0.9, q=0.9, x=0.9, y=0.9, z=0.9, v=0.9, u=0.9, t=0.9, r=0.9, s=0.9, n=0.9, o=0.9)[SHOT]

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


def shot_o(sc, sky):
    """The culture tank rebuilt from sci-fi film references (镜头设计_v3/styleframes/art/fusion/s4/培养罐参考.md, 11-04 14:35): the tank is its own light, a straight glass tube whose ends hide in two tall housings with seams and lit squares, hung from above by a mast, a ring and four clamping arms (the claw for the tail comes later from the same ring), the slot machine a screen on an arm at its side. The room dims for W2. 0 the hero view, dimmed; 1 the top, closer, from the right: the reels and the pipes; 2 the hero view with the room lit, as when the tank opens. The machine, the mist and the bubbles are drawn; the blue shape, the red tail and the four numbers come from the AlphaFold DB v6 model. Run: blender -b -P bl_inserts.py -- o <out dir> 0 2 64 1"""
    base_update = shot_v(sc, sky)
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
    g = np.random.default_rng(5)
    bub = emit((0.75, 0.97, 1.0), 2.0)
    for _ in range(46):
        a, r = g.uniform(0, 2 * math.pi), 0.27 * math.sqrt(g.uniform(0.02, 1))
        joint(C + Vector((r * math.cos(a), r * math.sin(a), g.uniform(0.31, 0.87 + T))), float(g.uniform(0.004, 0.011)), bub)
    for o in ob:                # the console's own lever goes; the lever is on the base
        if o.parent and o.parent.name.startswith("lever"):
            o.hide_render = True
    # the lever on the base, front right: pull it and the reels on top spin
    la = math.radians(68)
    radial(la, 0.38, 0.2, (0.06, 0.03, 0.06), gun, 0.006)
    beam(around(la, 0.40, 0.2), around(la, 0.47, 0.4), 0.014, steel)
    joint(around(la, 0.40, 0.2), 0.022, steel)
    joint(around(la, 0.47, 0.4), 0.03, mat(P.RED, 0.2, 0.0, 0.6))

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


sc, sky = stage()
update = dict(a=shot_a, w=shot_w, b=shot_b, c=shot_c, f=shot_f, g=shot_g, h=shot_h, k=shot_k, p=shot_p, q=shot_q, x=shot_x, y=shot_y, z=shot_z, v=shot_v, u=shot_u, t=shot_t, r=shot_r, s=shot_s, n=shot_n, o=shot_o)[SHOT](sc, sky)
sc.frame_start, sc.frame_end = 0, FRAMES
for f in range(FIRST, LAST + 1, STEP):
    sc.frame_set(f)
    update(START + f / FPS)
    gk.render("%s/%s_%04d.png" % (OUT, SHOT, f))
print("INSERT_OK", SHOT, FIRST, LAST)
