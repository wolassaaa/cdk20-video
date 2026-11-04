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
START = dict(a=32.1, w=35.12, b=35.15, c=43.35, f=78.8, g=146.0, h=224.5, k=285.8, p=312.0, q=330.0, x=330.0, y=412.0, z=437.0, v=412.0, u=412.0)[SHOT]
FRAMES = dict(a=198, w=24, b=218, c=310, f=960, g=414, h=654, k=1644, p=1080, q=4920, x=4920, y=1501, z=721, v=6, u=2551)[SHOT]
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
    low, high = dict(a=0.2, w=0.2, b=0.1, c=0.04, f=0.25, g=0.2, h=0.2, k=0.2, p=0.2, q=0.2, x=0.2, y=0.2, z=0.2, v=0.2, u=0.2)[SHOT], dict(a=1.25, w=1.25, b=2.0, c=2.6, f=2.0, g=2.0, h=2.0, k=0.9, p=0.9, q=0.9, x=0.9, y=0.9, z=0.9, v=0.9, u=0.9)[SHOT]

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


sc, sky = stage()
update = dict(a=shot_a, w=shot_w, b=shot_b, c=shot_c, f=shot_f, g=shot_g, h=shot_h, k=shot_k, p=shot_p, q=shot_q, x=shot_x, y=shot_y, z=shot_z, v=shot_v, u=shot_u)[SHOT](sc, sky)
sc.frame_start, sc.frame_end = 0, FRAMES
for f in range(FIRST, LAST + 1, STEP):
    sc.frame_set(f)
    update(START + f / FPS)
    gk.render("%s/%s_%04d.png" % (OUT, SHOT, f))
print("INSERT_OK", SHOT, FIRST, LAST)
