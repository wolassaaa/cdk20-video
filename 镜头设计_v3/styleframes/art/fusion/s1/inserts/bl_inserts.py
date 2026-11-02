"""HKBU SCIE1007 coursework science video. S1 table shots: the film's own table, seen first from the film's own overhead view, with a camera that falls to it and climbs back. What lies flat on the page stands up when the camera comes down, and lies back down when it leaves. All schematic, no maker's marks.

a: 32.1-35.4 s. An empty table; a foil strip lands; the camera falls to it; a tablet bursts through the foil and lands.
w: 35.12-35.52 s. A vial falls past the lens, alone on a clear film. It hides the cut from a to b.
b: 35.15-38.78 s. Two vials are set down; the camera climbs back and they lie down where the full view has them.
c: 43.35-48.52 s. The camera falls to the ten flat figures, they stand, seven drain and lie down, three stay, the camera climbs back.

Times are seconds on the film's clock. Table units are the plates': 200 px to the unit, y flipped.
Run: blender.exe -b -t 4 -P bl_inserts.py -- <a|w|b|c> <out dir> [first] [last] [samples] [size] [step]
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
sys.path[:0] = [HERE + "../code/", HERE + "../../code/"]
import bl_shots as B   # noqa: E402
import world as W      # noqa: E402

P, gk = B.P, B.gk
argv = sys.argv[sys.argv.index("--") + 1:]
SHOT, OUT = argv[0], argv[1]
START = dict(a=32.1, w=35.12, b=35.15, c=43.35)[SHOT]
FRAMES = dict(a=198, w=24, b=218, c=310)[SHOT]
FIRST = int(argv[2]) if len(argv) > 2 else 0
LAST = min(int(argv[3]), FRAMES - 1) if len(argv) > 3 else FRAMES - 1
SAMPLES = int(argv[4]) if len(argv) > 4 else 64
SIZE = float(argv[5]) if len(argv) > 5 else 1
STEP = int(argv[6]) if len(argv) > 6 else 1
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
    low, high = dict(a=0.2, w=0.2, b=0.1, c=0.04)[SHOT], dict(a=1.25, w=1.25, b=2.0, c=2.6)[SHOT]

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


def pipe(pts, r_px, mat, name):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r_px / K, 8
    cu.use_fill_caps = True
    s = cu.splines.new("POLY")
    s.points.add(len(pts) - 1)
    for q, xy in zip(s.points, pts):
        q.co = (xy[0] / K, -xy[1] / K, W.SURFACE_Z / K, 1)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o


def tube(front):
    """The glass line of the full view, filled as far as x = front."""
    path = W.PATHS["main_a"]
    glass = pipe(path, W.TUBE_R, B.clear_glass(), "glass")
    glass.visible_shadow, glass.visible_diffuse = False, False
    wet = pipe(path[:int(W.s_at("main_a", (front, 1010)) / 4) + 1], W.FLUID_R, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid")
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


sc, sky = stage()
update = dict(a=shot_a, w=shot_w, b=shot_b, c=shot_c)[SHOT](sc, sky)
sc.frame_start, sc.frame_end = 0, FRAMES
for f in range(FIRST, LAST + 1, STEP):
    sc.frame_set(f)
    update(START + f / FPS)
    gk.render("%s/%s_%04d.png" % (OUT, SHOT, f))
print("INSERT_OK", SHOT, FIRST, LAST)
