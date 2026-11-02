"""HKBU SCIE1007 coursework science video. S1 insert shots: real 3D close-ups on the same bone table, cut into the long holds of the film. One object does one thing in each. All schematic, no maker's marks.

a: a tablet bursts through the foil of a strip and lands on the table, 2.3 s, over "Nexavar".
b: two vials are set down and the liquid settles, 2.6 s, over "atezolizumab + bevacizumab".
c: ten figures; red drains out of seven and three stay, 3.0 s, over "three in ten".

Run: blender.exe -b -t 4 -P bl_inserts.py -- <a|b|c> <out dir> [first] [last] [samples] [size]
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

P, gk = B.P, B.gk
argv = sys.argv[sys.argv.index("--") + 1:]
SHOT, OUT = argv[0], argv[1]
FRAMES = dict(a=138, b=156, c=180)[SHOT]
FIRST = int(argv[2]) if len(argv) > 2 else 0
LAST = min(int(argv[3]), FRAMES - 1) if len(argv) > 3 else FRAMES - 1
SAMPLES = int(argv[4]) if len(argv) > 4 else 64
SIZE = int(argv[5]) if len(argv) > 5 else 1
FPS = 60.0


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def lerp(a, b, x):
    return tuple(p + (q - p) * x for p, q in zip(a, b))


def stage():
    """The same table and sun as the plates, seen from low down. Camera rays that miss the floor see bone, so there is no horizon. Reflections see one big window behind the objects, because a low camera never sees the plates' window above."""
    sc = P.scene(samples=SAMPLES, w=1920 * SIZE, h=1080 * SIZE)
    sc.cycles.denoising_use_gpu = True
    sc.render.use_persistent_data = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.fps = int(FPS)
    nt = sc.world.node_tree
    pick = lambda kind: [n for n in nt.nodes if n.type == kind]
    pick("VECT_MATH")[0].inputs[1].default_value = (-0.22, 0.92, 0.32)
    win = pick("MAP_RANGE")[1]
    win.inputs[1].default_value, win.inputs[2].default_value = 0.74, 0.97
    win.inputs[3].default_value, win.inputs[4].default_value = dict(a=0.2, b=0.1, c=0.04)[SHOT], dict(a=1.25, b=2.0, c=2.6)[SHOT]
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
    return sc


def lens(sc, mm, stop):
    d = bpy.data.cameras.new("cam")
    d.lens, d.sensor_width = mm, 36
    d.clip_start, d.clip_end = 0.05, 400
    d.dof.use_dof, d.dof.aperture_fstop = True, stop
    c = bpy.data.objects.new("cam", d)
    sc.collection.objects.link(c)
    sc.camera = c
    c.rotation_mode = "QUATERNION"
    return c


def shoot(c, f, eye, at, focus=None):
    v = Vector(at) - Vector(eye)
    c.location, c.rotation_quaternion = eye, v.to_track_quat("-Z", "Y")
    c.data.dof.focus_distance = (Vector(focus) - Vector(eye)).length if focus else v.length
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_quaternion", frame=f)
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


# ---------------------------------------------------------------- shot a: the strip and the tablet
HALF = (2.0, 1.12)                      # the plates' strip: 400 x 224 px
POCKETS = [(c * 0.92, r * 0.50) for r in (-1, 1) for c in (-1.5, -0.5, 0.5, 1.5)]
HERO = POCKETS[2]
Z_FOIL, RIM = 0.25, 0.34
TEAR, LEAVE, LAND = 0.55, 0.75, 1.46    # seconds: foil tears, tablet clears it, tablet lands
SPOT = (1.02, -2.02)
TABLET = [(0, 0.115), (0.08, 0.112), (0.16, 0.100), (0.24, 0.078), (0.285, 0.056), (0.30, 0.04), (0.30, -0.04), (0.285, -0.056), (0.24, -0.078), (0.16, -0.100), (0.08, -0.112), (0, -0.115)]
G = 8.0                                 # gravity in table units: a macro lens running slow


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


def shot_a(sc):
    c = lens(sc, 60, 0.5)
    strip = Strip()
    hero = lathe(TABLET, strip.tablet_mat, "hero")
    hero.rotation_mode = "QUATERNION"
    last = None
    for f in range(FRAMES + 1):
        t = f / FPS
        loc, q = tablet_path(t)
        if last is not None and q.dot(last) < 0:
            q.negate()
        last = q.copy()
        hero.location, hero.rotation_quaternion = loc, q
        hero.keyframe_insert("location", frame=f)
        hero.keyframe_insert("rotation_quaternion", frame=f)
        x = smooth(t / (FRAMES / FPS))
        pull = smooth((t - LEAVE) / (LAND - LEAVE + 0.1))
        look = lerp((HERO[0] - 0.05, HERO[1] - 0.15, 0.25), (SPOT[0] - 0.25, SPOT[1] + 0.45, 0.14), pull)
        shoot(c, f, lerp((1.55, -6.55, 1.72), (1.15, -5.85, 1.42), x), look, lerp((*HERO, 0.3), (SPOT[0] + 0.08, SPOT[1] - 0.23, 0.12), pull))
    return strip.update


# ---------------------------------------------------------------- shot b: two vials set down
VIAL_R = 62 / 200


def px(profile):
    return [(r / 200, (a + 125) / 200) for r, a in profile]


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


def set_down(root, xy, land, swing):
    """Falls from above the frame and slows, but still touches down with a small knock, then rocks on its base."""
    drop, h, last = 0.62, 1.95, None
    ax = (math.cos(swing), math.sin(swing), 0)
    for f in range(FRAMES + 1):
        t = f / FPS
        s = min(1.0, max(0.0, (t - land + drop) / drop))
        d = t - land
        rock = math.radians(1.5) * math.exp(-d / 0.28) * math.cos(2 * math.pi * 3.2 * d) if d > 0 else math.radians(1.5) * (1 - s)
        q = Quaternion(ax, rock)
        if last is not None and q.dot(last) < 0:
            q.negate()
        last = q.copy()
        root.location = (xy[0], xy[1], h * (1 - s) * (1 - 0.7 * s) + VIAL_R * abs(math.sin(rock)))
        root.rotation_quaternion = q
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_quaternion", frame=f)


def vial(xy, land, swing):
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
    dose = Dose(root, liquid, swing)
    set_down(root, xy, land, swing)
    return lambda t: dose.update(t - land)


def shot_b(sc):
    c = lens(sc, 85, 0.6)
    back = empty("old_strip")
    back.location = (-2.1, 4.0, 0)
    strip = Strip(back)
    strip.update(9.0)
    tab = lathe(TABLET, strip.tablet_mat, "hero", back)
    tab.location = (SPOT[0] + 0.25, SPOT[1] - 0.25, 0.115)
    first, second = vial((-0.48, 0.0), 0.62, 0.5), vial((0.52, 0.30), 1.18, 2.2)
    for f in range(FRAMES + 1):
        x = smooth(f / FRAMES)
        shoot(c, f, lerp((-0.72, -7.3, 1.08), (-0.20, -6.75, 1.0), x), (-0.40, 0.1, 0.63), (0.03, 0.1, 0.63))

    def update(t):
        first(t)
        second(t)
    return update


# ---------------------------------------------------------------- shot c: ten figures, seven drain
GAP, TALL = 0.75, 0.85
DRAIN = [None, None, None] + [0.25 + i * 0.22 for i in range(7)]   # the same stagger as the film's table


def outline():
    """The stand-in's plain person shape, base on the table. Same shape as bl_plate.py's figure, standing up."""
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


def pipe(a, b, r, mat, name, z):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r, 8
    cu.use_fill_caps = True
    s = cu.splines.new("POLY")
    s.points.add(1)
    s.points[0].co, s.points[1].co = (*a, z, 1), (*b, z, 1)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o


def shot_c(sc):
    c = lens(sc, 50, 0.8)
    poly = outline()
    mats = []
    for i in range(10):
        m = fill_mat(i)
        mats.append(m)
        o = B.extrude([poly], 0.14, 0.03, name="figure", mat=m)
        o.rotation_euler = (math.pi / 2, 0, 0)
        o.location = (i * GAP, 0.07, 0)
    glass = pipe((-9, -0.17), (40, -0.17), 0.10, B.clear_glass(), "glass", 0.10)
    glass.visible_shadow, glass.visible_diffuse = False, False
    wet = pipe((-9, -0.17), (40, -0.17), 0.075, B.fluid(P.RED, (0.9, 0.05, 0.03)), "liquid", 0.10)
    wet.visible_diffuse = False
    for f in range(FRAMES + 1):
        x = smooth(f / FRAMES)
        shoot(c, f, lerp((-2.45, -7.25, 1.02), (-2.2, -6.95, 0.92), x), lerp((2.5, 0.0, 0.44), (2.56, 0.0, 0.42), x), (1.15, 0, 0.45))

    def update(t):
        for i, m in enumerate(mats):
            n = m.node_tree.nodes
            go = DRAIN[i]
            n["phase"].outputs[0].default_value = 5.0 * t + i * 1.7
            n["level"].outputs[0].default_value = 2.0 if go is None else TALL * 1.03 * (1 - smooth((t - go) / 0.85)) - 0.03 * smooth((t - go) / 0.85)
    return update


sc = stage()
update = dict(a=shot_a, b=shot_b, c=shot_c)[SHOT](sc)
sc.frame_start, sc.frame_end = 0, FRAMES
for f in range(FIRST, LAST + 1):
    sc.frame_set(f)
    update(f / FPS)
    gk.render("%s/%s_%04d.png" % (OUT, SHOT, f))
print("INSERT_OK", SHOT, FIRST, LAST)
