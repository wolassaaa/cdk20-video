"""HKBU SCIE1007 coursework science video. S6 (12:44-15:15, the scorecard: before vs now, and where 048 stands), the 3D table under the Remotion words (s6.jsx).
Storyboard: 镜头设计_v3/styleframes/art/fusion/s6/00_S6分镜_v1.md. Look, materials and colours are the current film's (plate_kit, bl_inserts); things are set down
and come to rest, nothing is thrown, bounces or shakes. Runs inside bl_inserts.py through BL_EXTRA.

One shot, s6, on an empty stretch of the table (x 150-200), on bl_inserts' 60 fps clock from 764.0 s:
the board (two columns of four cells), what each row puts in its cells, the four dashed boxes' corner with the AI screen, and the road.
Words, tape measures, dashed boxes, tags and source lines are Remotion's; it reads the camera from S6_TRACK.

Run: BL_EXTRA=bl_s6.py blender.exe -b -P bl_inserts.py -- s6 <out> 0 9060 16 1 2
S6_PLAN=<json>   writes the frames that change (the rest are held) and the times, renders nothing
S6_TRACK=<json>  writes the camera every other frame for Remotion, renders nothing
S6_CLASH=1       checks every frame where something moves for clashes, renders nothing
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Quaternion, Vector

META = {"s6": (764.0, 9061, 0.2, 0.9)}

BC = (160.0, -2.7)                          # the board's middle
CW, CH = 2.7, 1.0                           # a cell, outer
COLS = (-1.0, 2.0)                          # BEFORE, NOW
ROWS = (1.65, 0.45, -0.75, -1.95)
EX = 16.0                                   # the corner with the four dashed boxes, from the board's middle
RX = 28.0                                   # the road's middle
ST = [-4.0 + 1.6 * i for i in range(6)]     # the road's six stations, from RX
RR = 0.31                                   # a station's radius, as the S1 road
SZ = W.SURFACE_Z / K


def at(x, y, z=0.0):
    return (BC[0] + x, BC[1] + y, z)


def cell(c, r):
    return COLS[c], ROWS[r]


# ---------------------------------------------------------------- times, film seconds; s6.jsx reads the same numbers from S6_TRACK
T = dict(
    start=764.0, end=915.0,
    climb=(764.0, 4.4), hdr_b=768.2, hdr_n=768.7, ask=769.6,
    row1=771.0, flask=(772.0, 0.7), lab=772.8, dash=(774.4, 1.0), noshape=775.6, fall1=(778.6, 1.6), cdk=(780.0, 2.2), climb1=(782.4, 1.6), afdb=782.6, free=783.2,
    row2=785.0, fall2=(786.4, 1.4), tube1=787.2, tube10=788.2, tube100=789.2, millions=790.6, neck=792.0, climb2=(792.6, 1.6),
    fall_k=(794.4, 1.4), keys=(794.6, 1.6), designed=796.0, shrink=(798.0, 1.8), dots=(799.9, 0.6), climb_k=(800.4, 1.4), slam=801.9, made=802.6,
    oncam=(804.6, 1.0), print_d=805.0, print_b=808.0,
    row3=811.0, road_b=(811.6, 0.6), tape_b=(812.8, 1.6), years=814.0, ring_b=815.4, start_b=815.8, road_n=(817.4, 0.6), tape_n=818.6, fill_n=(818.6, 1.2), plus=821.2, fill_n2=(821.2, 1.2),
    row4=824.0, turn_set=(825.0, 0.6), fall_t=(825.3, 1.2), turn=(826.4, 2.4), round=826.9, climb_t=(829.1, 1.4), slot=830.6,
    fair=(837.6, 1.8), sources=839.6, quote=845.0,
    slide_e=(851.0, 2.6), boxes=(855.3, 856.5, 857.6, 859.0), maybe=859.8, plug=861.6, power=862.0, prize=865.2,
    slide_r=(867.6, 2.2), tag048=869.6, lit=(870.6, 872.0, 873.4, 874.9), notyet=876.4,
    cyan=(881.5, 4.5), cyan_tag=885.0, exs=(891.0, 1.4), strike=892.8, public=898.5,
    print_b2=906.0, weeks=911.0,
)


# ---------------------------------------------------------------- the camera
def top(x, y, mm):
    return dict(TOP, at=at(x, y), mm=mm)


V_LOW = polar(at(-0.6, -5.8, 2.4), at(0.4, 0.5, 0.0), 40)
V_BOARD = top(1.3, 0.2, 480)
V_ROW = [top(1.3, r - 0.1, 560) for r in ROWS]
V_CDK = polar(at(2.0, -2.6, 2.3), at(2.0, 1.6, 0.25), 50)
V_TUBES = polar(at(-1.1, -3.1, 2.9), at(-1.4, 0.5, 0.15), 45)
V_KEYS = polar(at(2.25, -2.0, 1.75), at(2.0, 0.5, 0.0), 40)
V_TURN = polar(at(-1.0, -4.1, 1.75), at(-1.3, -1.9, 0.05), 45)
V_PRINT = top(6.6, 0.2, 560)
V_FAIR = top(1.3, -0.25, 470)
V_E = top(EX, -0.2, 520)
V_ROAD = top(RX, -0.5, 520)


def glide(p, q, x):
    """Between two views from overhead: the middle and the lens ease together, the lens on a log scale."""
    x = smooth(x)
    return dict(p, at=lerp(p["at"], q["at"], x), mm=math.exp(math.log(p["mm"]) + (math.log(q["mm"]) - math.log(p["mm"])) * x))


def s6_view(t):
    u = lambda k: (t - T[k][0]) / T[k][1]
    if t < T["climb"][0] + T["climb"][1]:
        return climb(V_LOW, V_BOARD, smooth(u("climb")))
    if t < T["row1"] - 0.2:
        return V_BOARD
    if t < T["fall1"][0]:
        return glide(V_BOARD, V_ROW[0], (t - T["row1"] + 0.2) / 1.6)
    if t < T["climb1"][0]:
        return fall(V_ROW[0], V_CDK, smooth(u("fall1")))
    if t < T["row2"] - 0.4:
        return climb(V_CDK, V_ROW[0], smooth(u("climb1")))
    if t < T["fall2"][0]:
        return glide(V_ROW[0], V_ROW[1], (t - T["row2"] + 0.4) / 1.6)
    if t < T["climb2"][0]:
        return fall(V_ROW[1], V_TUBES, smooth(u("fall2")))
    if t < T["fall_k"][0]:
        return climb(V_TUBES, V_ROW[1], smooth(u("climb2")))
    if t < T["climb_k"][0]:
        return fall(V_ROW[1], V_KEYS, smooth(u("fall_k")))
    if t < T["oncam"][0]:
        return climb(V_KEYS, V_ROW[1], smooth(u("climb_k")))
    if t < T["row3"] - 0.2:
        return glide(V_ROW[1], V_PRINT, u("oncam"))
    if t < T["row4"] - 0.4:
        return glide(V_PRINT, V_ROW[2], (t - T["row3"] + 0.2) / 1.6)
    if t < T["fall_t"][0]:
        return glide(V_ROW[2], V_ROW[3], (t - T["row4"] + 0.4) / 1.6)
    if t < T["climb_t"][0]:
        return fall(V_ROW[3], V_TURN, smooth(u("fall_t")))
    if t < T["fair"][0]:
        return climb(V_TURN, V_ROW[3], smooth(u("climb_t")))
    if t < T["slide_e"][0]:
        return glide(V_ROW[3], V_FAIR, u("fair"))
    if t < T["slide_r"][0]:
        return glide(V_FAIR, V_E, u("slide_e"))
    return glide(V_E, V_ROAD, u("slide_r"))


# ---------------------------------------------------------------- the things
ink = None
DOWN = 0.9                                  # how high a thing starts when it is set down


def set_down(t, at_, d, high=DOWN):
    """Height over its rest while it is lowered in: it comes down and slows to rest, no bounce. Below the table before, so it is hidden."""
    x = (t - at_) / d
    if x < 0:
        return None
    return high * (1 - smooth(x)) ** 1.0


class Mover:
    """A rigid thing that is set down at its own spot: its children ride on one empty."""

    def __init__(self, name, xy, when, d, z0=0.0):
        self.e = empty(name)
        self.xy, self.when, self.d, self.z0 = xy, when, d, z0
        self.e.location = (*xy, -50)

    def h(self, t):
        return set_down(t, self.when, self.d)

    def update(self, t):
        h = self.h(t)
        self.e.location = (*self.xy, -50 if h is None else self.z0 + h)
        for o in self.e.children_recursive:
            o.hide_render = h is None

    def sig(self, t):
        h = self.h(t)
        return -1.0 if h is None else round(h, 4)


def rim(cx, cy, w, h, mat):
    outer = box(cx - w / 2, cx + w / 2, cy + h / 2, cy - h / 2, 0.09)
    inner = box(cx - w / 2 + 0.03, cx + w / 2 - 0.03, cy + h / 2 - 0.03, cy - h / 2 + 0.03, 0.07)
    return B.extrude([outer, inner[::-1]], 0.02, 0.005, name="cell", mat=mat)


def dashed(pts, gap, name, mat, r_px=1.6, closed=True):
    """Dashes along a polyline in table units; returns the dash objects in order, for drawing them one by one."""
    p = np.array(pts + ([pts[0]] if closed else []), float)
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    n = max(1, round(run[-1] / gap))
    out = []
    for i in range(n):
        s = np.linspace(i, i + 0.55, 6) * run[-1] / n
        d = np.c_[np.interp(s, run, p[:, 0]), np.interp(s, run, p[:, 1])]
        out.append(pipe([(x * K, -y * K) for x, y in d], r_px, mat, name))
    return out


def key_parts(steel, ink_m):
    """The W3 key (version 1's last one: blade, bow and the ring of six on the bow), in its own units; bl_inserts' shot_hk builds it the same way."""
    import bmesh
    from mathutils import Matrix
    parts = [B.extrude([B.round_poly(B.key_blade(-0.075, 0.0, start=0.14), 0.03)], 0.2, 0.04, z=-0.1, name="s6_blade", mat=steel)]
    ring_ = [(-0.875 + 0.75 * math.cos(2 * math.pi * i / 96), 0.75 * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    parts.append(B.extrude([ring_], 0.24, 0.05, z=-0.12, name="s6_bow", mat=steel))
    bm = bmesh.new()
    bc = Vector((-0.875, 0.0, 0.14))
    hexa = [bc + Vector((0.42 * math.cos(math.radians(30 + 60 * i)), 0.42 * math.sin(math.radians(30 + 60 * i)), 0.0)) for i in range(6)]
    for c_ in hexa:
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.085, matrix=Matrix.Translation(c_))
    for i in range(6):
        a_, b_ = hexa[i], hexa[(i + 1) % 6]
        d_ = b_ - a_
        M = Matrix.Translation((a_ + b_) / 2) @ Vector((0, 0, 1)).rotation_difference(d_.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.04, radius2=0.04, depth=d_.length, matrix=M)
    me = bpy.data.meshes.new("s6_hex")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ink_m)
    o = bpy.data.objects.new("s6_hex", me)
    bpy.context.scene.collection.objects.link(o)
    parts.append(o)
    for p in parts:
        p.location.z += 0.12            # the key's underside on z 0
        bpy.context.view_layer.update()
    return parts


def s6_things(sc):
    global ink
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    rim_m = gk.surface((0.60, 0.585, 0.54), 0.7, 0.1)
    glass, red = B.clear_glass(), B.fluid(P.RED, (0.9, 0.05, 0.03))
    cap = P.gloss(P.KLEIN, 0.25, 0.6)
    tray = gk.surface((0.74, 0.725, 0.67), 0.7, 0.1)
    card_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    steel = P.gloss((0.6, 0.59, 0.57), 0.22, 0.5)
    movers, statics = [], []

    # the board: two columns of four cells, there from the start
    for c in range(2):
        for r in range(4):
            x, y = cell(c, r)
            statics.append(rim(*at(x, y)[:2], CW, CH, rim_m))

    # row 1, before: a well plate from 4-06's turntable, big (a flask seen from overhead reads as a ball), and the cell's dashed empty frame drawn dash by dash
    fx, fy = at(*cell(0, 0))[:2]
    m = Mover("plate", (fx + 0.76, fy), T["flask"][0], T["flask"][1])
    o = B.extrude([box(-0.46, 0.46, 0.31, -0.31, 0.05)], 0.05, 0.01, name="plate", mat=tray)
    o.parent = m.e
    for i in range(12):
        for j in range(8):
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.026, depth=0.006, location=(-0.385 + 0.07 * i, -0.245 + 0.07 * j, 0.051))
            w_ = bpy.context.object
            w_.data.materials.append(red if (i * 7 + j * 3) % 11 == 0 else ink)
            w_.parent = o
    movers.append(m)
    l, r_, tp, bt = fx - 1.15, fx + 0.25, fy + 0.34, fy - 0.34
    dashes = dashed([(l, tp), (r_, tp), (r_, bt), (l, bt)], 0.12, "s6_dash", ink)

    # row 1, now: the predicted CDK20, lowered into its cell with its pocket looking up
    d = np.load(HERE + "frames/cdk20.npz")
    q = Quaternion((1, 0, 0), -(math.pi / 2 - P_UP))
    q0 = Vector(d["mouth"].tolist()).rotation_difference(Vector((0, -math.cos(P_UP), math.sin(P_UP))))
    v = (d["verts"] @ np.array(q0.to_matrix()).T) * P_S
    me = bpy.data.meshes.new("s6_cdk20")
    me.from_pydata(v.tolist(), [], d["quads"].tolist())
    me.materials.append(P.gloss(P.KLEIN, 0.34, 0.7))
    pts = v @ np.array(q.to_matrix()).T
    s = 0.8 / float(max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1])))
    nx, ny = at(*cell(1, 0))[:2]
    m = Mover("cdk20", (nx - 0.35, ny), T["cdk"][0], T["cdk"][1], z0=-float(pts[:, 2].min()) * s + 0.002)
    o = bpy.data.objects.new("s6_cdk20", me)
    sc.collection.objects.link(o)
    B.smooth(o)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion, o.scale = q, (s, s, s)
    o.location = (-float(pts[:, 0].mean()) * s, -float(pts[:, 1].mean()) * s, 0)
    o.parent = m.e
    m.d, m.high = T["cdk"][1], 2.4
    m.h = lambda t, m=m: set_down(t, m.when, m.d, 2.4)
    movers.append(m)

    # row 2, before: one tube, ten, a hundred, spilling out of the cell into the margin on its left
    bx, by = at(*cell(0, 1))[:2]
    TS = 0.3                                 # the S3 tube at this size: 0.37 tall, 0.06 wide
    spots = []
    for i in range(-14, 9):
        for j in range(-2, 3):
            x, y = bx + i * 0.16 + (0.08 if j % 2 else 0), by + j * 0.17
            if x > bx + 1.25:
                continue
            on_rim = lambda a, lo, hi: lo - 0.075 < a < hi + 0.075
            if on_rim(x, bx - CW / 2, bx - CW / 2 + 0.03) or on_rim(x, bx + CW / 2 - 0.03, bx + CW / 2):
                continue
            if on_rim(y, by - CH / 2, by - CH / 2 + 0.03) or on_rim(y, by + CH / 2 - 0.03, by + CH / 2):
                continue
            if x < bx - CW / 2 - 0.05 and (j >= 0 or x < bx - CW / 2 - 1.0):
                continue                     # the margin keeps its top for the row's name; the spill stops short of the words
            spots.append((x, y))
    mid = (bx - 0.1, by)
    spots.sort(key=lambda p: (p[0] - mid[0]) ** 2 + (p[1] - mid[1]) ** 2)
    tubes = []
    for n, p in enumerate(spots):
        when = T["tube1"] if n == 0 else T["tube10"] + 0.05 * (n - 1) if n < 10 else T["tube100"] + 0.011 * (n - 10)
        m = Mover("tube", p, when, 0.5)
        tb = Vial((0, 0), 0, glass, red, cap)
        tb.dose.parent.parent = m.e
        tb.dose.parent.location = (0, 0, 0)
        tb.dose.parent.scale = (TS,) * 3
        tb.update(0.0)
        tubes.append(m)
    movers += tubes

    # row 2, now: the W3 key, a carpet of them set down; they shrink away from the edges in, and 13 ink dots are left
    kx, ky = at(*cell(1, 1))[:2]
    parts = key_parts(steel, ink)
    KS = 0.13 / 3.25
    keys = []
    for j in range(7):
        for i in range(17):
            x, y = kx - 1.12 + i * 0.14 + (0.05 if j % 2 else 0), ky + 0.33 - j * 0.11
            m = Mover("key", (x, y), T["keys"][0] + 0.07 * i + 0.03 * j, 0.5)
            for p in parts:
                c_ = p.copy()
                sc.collection.objects.link(c_)
                c_.parent = m.e
                c_.scale = (KS,) * 3
                c_.location = (p.location.x * KS, p.location.y * KS, p.location.z * KS)
            m.gone = T["shrink"][0] + 1.5 * (1 - min(1.0, math.hypot((x - kx) / 1.2, (y - ky) / 0.4)))     # gone before the dots start
            keys.append(m)
    for p in parts:
        bpy.data.objects.remove(p)
    movers += keys
    dots = []
    for i in range(13):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.045, depth=0.004, location=(kx - 0.78 + i * 0.13, ky, 0.002))
        o = bpy.context.object
        o.data.materials.append(ink)
        dots.append(o)

    # row 3: a small road in each cell, set down; the one on the right fills its first stretch, then a little more
    roads = []
    for c, when in ((0, T["road_b"]), (1, T["road_n"])):
        rx, ry = at(*cell(c, 2))[:2]
        m = Mover("road", (rx, ry + 0.08), when[0], when[1])
        xs = [-1.05 + 0.42 * i for i in range(6)]
        g = pipe([((rx + xs[0]) * K, -(ry + 0.08) * K), ((rx + xs[5]) * K, -(ry + 0.08) * K)], 3.0, glass, "road_glass")
        g.visible_shadow, g.visible_diffuse = False, False
        kids = [g]
        for x in xs:
            before = set(bpy.data.objects)
            B.bulb(rx + x, ry + 0.08, SZ, 0.13, ink, None, width=0.011)
            kids += list(set(bpy.data.objects) - before)
        if c == 1:
            wet = pipe([((rx + xs[0]) * K, -(ry + 0.08) * K), ((rx + xs[5]) * K, -(ry + 0.08) * K)], 2.2, red, "road_wet")
            wet.visible_diffuse = False
            wet.data.bevel_factor_mapping_end = "SPLINE"
            first = Bulb(rx + xs[0], red, ry + 0.08, SZ, 0.12)
            kids += [wet, first.o]
            small = dict(wet=wet, first=first, x0=rx + xs[0], xs=[rx + x for x in xs])
        for o in kids:          # world space now, ride the mover from here
            o.parent = m.e
            o.matrix_parent_inverse = Matrix_t(m)
        m.local = True
        roads.append(m)
    movers += roads

    # row 4, before: 4-06's turntable, small, with five things on it; it turns once
    tx, ty = at(*cell(0, 3))[:2]
    tt = Mover("turntable", (tx - 0.3, ty), T["turn_set"][0], T["turn_set"][1])
    spin = empty("turn_spin")
    spin.parent = tt.e
    spin.rotation_mode = "XYZ"
    TT = 0.03
    lathe([(0, 0), (0.4, 0), (0.41, 0.012), (0.4, TT), (0, TT)], tray, "turn_disc", spin, 128)
    tr = tube3d([(0.29 * math.cos(a), 0.29 * math.sin(a), TT + 0.002) for a in np.linspace(0, 2 * math.pi, 97)], 0.004, ink, "turn_track")
    tr.parent = spin
    for k in range(5):
        a = math.radians(90 + 72 * k)
        px_, py_ = 0.29 * math.cos(a), 0.29 * math.sin(a)
        if k == 0:              # an idea card
            o = B.extrude([box(-0.07, 0.07, 0.05, -0.05, 0.01)], 0.012, 0.003, name="turn_card", mat=card_m)
        elif k == 1:            # a sample vial
            o = lathe([(0, 0), (0.035, 0), (0.035, 0.12), (0, 0.12)], glass, "turn_vial", None, 32)
            lathe([(0, 0.004), (0.028, 0.004), (0.028, 0.07), (0, 0.07)], red, "turn_dose", o, 32)
        elif k == 2:            # a well plate
            o = B.extrude([box(-0.08, 0.08, 0.055, -0.055, 0.012)], 0.02, 0.004, name="turn_plate", mat=tray)
            for i in range(4):
                for j in range(3):
                    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.011, depth=0.004, location=(-0.054 + 0.036 * i, -0.036 + 0.036 * j, 0.021))
                    w_ = bpy.context.object
                    w_.data.materials.append(red if (i + j) % 3 == 0 else ink)
                    w_.parent = o
        elif k == 3:            # a red cross, lying flat
            arm = [(-0.06, -0.016), (0.06, -0.016), (0.06, 0.016), (-0.06, 0.016)]
            o = B.extrude([B.round_poly(arm, 0.008)], 0.014, 0.003, name="turn_cross", mat=P.gloss(P.RED, 0.22, 0.6))
            o2 = B.extrude([B.round_poly([(y, x) for x, y in arm], 0.008)], 0.014, 0.003, z=0.0005, name="turn_cross2", mat=P.gloss(P.RED, 0.22, 0.6))
            o2.parent = o
        else:                   # a spanner on a bolt
            o = B.extrude([B.round_poly([(-0.07, -0.012), (0.05, -0.012), (0.05, 0.012), (-0.07, 0.012)], 0.006)], 0.01, 0.002, name="turn_spanner", mat=P.gloss((0.42, 0.42, 0.44), 0.3, 0.3))
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.022, depth=0.03, location=(0.06, 0, 0.015))
            bolt = bpy.context.object
            bolt.data.materials.append(P.gloss((0.42, 0.42, 0.44), 0.3, 0.3))
            bolt.parent = o
        o.parent = spin
        o.location = (px_, py_, TT + 0.001)
        o.rotation_euler = (0, 0, a - math.pi / 2)
    # the pointer: a small red mark on the table at the turntable's left, clear of the disc (0.41) and of the cell's rim
    pt = B.extrude([[(tx - 0.3 - 0.56, ty - 0.05), (tx - 0.3 - 0.47, ty), (tx - 0.3 - 0.56, ty + 0.05)]], 0.012, 0.003, name="turn_pointer", mat=P.gloss(P.RED, 0.22, 0.6))
    pt.parent = tt.e
    pt.matrix_parent_inverse = Matrix_t(tt)
    movers.append(tt)

    # the corner with the dashed boxes: 4-07's AI screen, lying on the table, rings on it
    sx, sy = at(EX - 3.3, 1.0)[:2]
    scr = B.extrude([box(sx - 0.75, sx + 0.75, sy + 0.5, sy - 0.5, 0.06)], 0.04, 0.01, name="ai_screen", mat=gk.surface((0.0, 0.03, 0.35), 0.35, 0.4))
    glow = bpy.data.materials.new("ai_ring")
    glow.use_nodes = True
    bs = glow.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.4, 0.55, 1.0, 1)
    bs.inputs["Emission Color"].default_value = (0.35, 0.5, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 1.2
    for i in range(3):
        for j in range(2):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.012, location=(sx - 0.42 + 0.42 * i, sy + 0.2 - 0.4 * j, 0.045), major_segments=64, minor_segments=12)
            bpy.context.object.data.materials.append(glow)
    statics.append(scr)

    # the road: six stations and the glass line, as the S1 road; the red runs station by station to half of the fourth
    y_r = at(0, -0.3)[1]
    xr = [at(RX + s_, 0)[0] for s_ in ST]
    g = pipe([((xr[0] - 0.9) * K, -y_r * K), ((xr[5] + 0.6) * K, -y_r * K)], W.TUBE_R, glass, "road_glass")
    g.visible_shadow, g.visible_diffuse = False, False
    wet = pipe([((xr[0] - 0.9) * K, -y_r * K), ((xr[5] + 0.6) * K, -y_r * K)], W.FLUID_R, red, "road_wet")
    wet.visible_diffuse = False
    wet.data.bevel_factor_mapping_end = "SPLINE"
    for i, x in enumerate(xr[:4]):          # stations ahead get a dashed ring in Remotion, no bulb (as F6)
        B.bulb(x, y_r, SZ, RR, ink, None, width=0.022)
    bulbs = [Bulb(x, red, y_r, SZ) for x in xr[:4]]
    road = dict(wet=wet, bulbs=bulbs, xs=xr, x0=xr[0] - 0.9, x1=xr[5] + 0.6)
    return dict(movers=movers, statics=statics, dashes=dashes, tubes=tubes, keys=keys, dots=dots, small=small, spin=spin, road=road, turntable=tt)


def Matrix_t(m):
    """The inverse of where a mover will rest, so world-built children keep their place when it is set down."""
    from mathutils import Matrix
    return Matrix.Translation((-m.xy[0], -m.xy[1], -m.z0))


def road_front(t):
    """The red's front on the big road: to each station as its word lands, half way through the fourth."""
    x = ST[0] - RR - 0.1
    for i, at_ in enumerate(T["lit"]):
        goal = ST[i] + (RR if i < 3 else 0.0)
        x += (goal - x) * smooth((t - at_ + 0.6) / 0.9)
    return x


def small_front(t, sm):
    """The red's front in the small road on the right of row 3: the first stretch (station one to two), then half way on to three."""
    a = smooth((t - T["fill_n"][0]) / T["fill_n"][1])
    b = smooth((t - T["fill_n2"][0]) / T["fill_n2"][1])
    xs = sm["xs"]
    return xs[0] - 0.13 + (xs[1] + 0.13 - xs[0] + 0.13) * a + 0.21 * b


def shot_s6(sc, sky):
    c = lens(sc, 40.0)
    th = s6_things(sc)
    road, sm = th["road"], th["small"]

    def dot_scale(t):
        return smooth((t - T["dots"][0]) / T["dots"][1])

    def key_scale(m, t):
        return 1 - smooth((t - m.gone) / 0.35)

    def turn(t):
        return 2 * math.pi * smooth((t - T["turn"][0]) / T["turn"][1])

    def dash_n(t):
        return int(round(len(th["dashes"]) * smooth((t - T["dash"][0]) / T["dash"][1])))

    def update(t):
        for m in th["movers"]:
            m.update(t)
        for m in th["keys"]:
            k = key_scale(m, t)
            m.e.scale = (max(k, 1e-4),) * 3
            if k <= 0:
                for o in m.e.children:
                    o.hide_render = True
        for o in th["dots"]:
            s_ = dot_scale(t)
            o.scale = (max(s_, 1e-4), max(s_, 1e-4), 1)
            o.hide_render = s_ <= 0
        n = dash_n(t)
        for i, o in enumerate(th["dashes"]):
            o.hide_render = i >= n
        th["spin"].rotation_euler.z = turn(t)
        f = small_front(t, sm)
        sm["wet"].data.bevel_factor_end = max(0.0, (f - sm["xs"][0]) / (sm["xs"][5] - sm["xs"][0]))
        sm["wet"].hide_render = f <= sm["xs"][0]
        sm["first"].update(f)
        x = BC[0] + RX + road_front(t)
        road["wet"].data.bevel_factor_end = max(0.0, (x - road["x0"]) / (road["x1"] - road["x0"]))
        road["wet"].hide_render = t < T["lit"][0] - 0.7
        for b in road["bulbs"]:
            b.update(x)
        v = s6_view(t)
        sky(smooth((v["el"] - 0.75) / 0.7))

    def sig(t):
        """What the frame shows, rounded: a frame equal to the one before is held, not rendered."""
        v = s6_view(t)
        out = [round(a, 4) for a in v["at"]] + [round(v["el"], 4), round(v["d"], 3), round(v["mm"], 2), round(v["az"], 4)]
        out += [m.sig(t) for m in th["movers"]]
        out += [round(key_scale(m, t), 3) for m in th["keys"]]
        out += [round(dot_scale(t), 3), dash_n(t), round(turn(t), 4), round(small_front(t, sm), 4), round(road_front(t), 4)]
        return tuple(out)

    for f in range(FRAMES):
        t = START + f / FPS
        v = s6_view(t)
        shoot(c, f, v, v["at"])
    update.sig = sig
    update.th = th
    update.fn = dict(key_scale=key_scale, turn=turn, dot_scale=dot_scale)

    if os.environ.get("S6_PLAN"):
        s6_plan(update, os.environ["S6_PLAN"])
        raise SystemExit(0)
    if os.environ.get("S6_TRACK"):
        s6_track(os.environ["S6_TRACK"])
        raise SystemExit(0)
    if os.environ.get("S6_CLASH"):
        s6_clash(sc, update)
        raise SystemExit(0)
    return update


def s6_plan(update, path):
    """Every other frame (30 fps): the ones whose picture changes. The take holds each one until the next."""
    keep, last = [], None
    for f in range(0, FRAMES - 1, 2):
        s_ = update.sig(START + f / FPS)
        if s_ != last:
            keep.append(f)
        last = s_
    json.dump(dict(frames=keep), open(path, "w"))
    print("PLAN_OK %d of %d frames change" % (len(keep), len(range(0, FRAMES, 2))))


def s6_track(path):
    """The camera every other frame, for Remotion to put the words on the table: eye, the point it looks at, lens mm. Times too, so both read one set."""
    cam = []
    for f in range(0, FRAMES - 1, 2):
        v = s6_view(START + f / FPS)
        cam.append([round(a, 4) for a in eye_of(v)] + [round(a, 4) for a in v["at"]] + [round(v["mm"], 3)])
    geo = dict(BC=BC, CW=CW, CH=CH, COLS=COLS, ROWS=ROWS, EX=EX, RX=RX, ST=ST, RR=RR)
    json.dump(dict(fps=30, start=T["start"], cam=cam, T=T, geo=geo), open(path, "w"), separators=(",", ":"))
    print("TRACK_OK", path, len(cam))


def s6_clash(sc, update):
    """Every 60 fps frame where something moves: each moving solid against every solid near it (BVH overlap, then the nearest vertex gap), and how low it goes.
    The liquid inside the glass, the glass line (a curve) and the dashes lying flat are left out: they are meant to touch or are flat ink. The small roads' and the
    big road's bulbs sink into the table on purpose, as the S1 road does, so they are left out of the lowest point."""
    from mathutils.bvhtree import BVHTree
    th, fn = update.th, update.fn
    groups, gsig = {}, {}

    def solids(e):
        return [o for o in ([e] + list(e.children_recursive)) if o.type == "MESH" and not any(w in o.name for w in ("liquid", "wet", "dose", "bulbfluid"))]
    for i, m in enumerate(th["movers"]):
        n = "%s%d" % (m.e.name.split(".")[0], i)
        groups[n] = (m, solids(m.e))
        if m in th["keys"]:
            gsig[n] = lambda t, m=m: (m.sig(t), fn["key_scale"](m, t))          # exact: a rounded scale can stop changing while the key is still there
        elif m is th["turntable"]:
            gsig[n] = lambda t, m=m: (m.sig(t), round(fn["turn"](t), 4))
        else:
            gsig[n] = lambda t, m=m: m.sig(t)
    for i, o in enumerate(th["statics"]):
        groups["rim%d" % i] = (None, [o])
        gsig["rim%d" % i] = lambda t: 0
    for i, o in enumerate(th["dots"]):
        groups["dot%d" % i] = (None, [o])
        gsig["dot%d" % i] = lambda t: fn["dot_scale"](t)

    def world(objs, dg):
        vs, ps = [], []
        for o in objs:
            if o.hide_render:
                continue
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            b = len(vs)
            vs += [e.matrix_world @ v.co for v in me.vertices]
            ps += [tuple(b + j for j in p.vertices) for p in me.polygons]
            e.to_mesh_clear()
        return vs, ps
    cache, last = {}, {}
    clashes, near, low, n_checked, n_moving = [], (1e9, -1, ""), (1e9, -1, ""), 0, 0
    for f in range(FRAMES):
        t = START + f / FPS
        now = {n: g(t) for n, g in gsig.items()}
        live = [n for n in groups if now[n] != last.get(n, "none")]
        last = now
        if not live:
            continue
        n_moving += 1
        sc.frame_set(f)
        update(t)
        dg = bpy.context.evaluated_depsgraph_get()
        for n in live:
            vs, ps = world(groups[n][1], dg)
            if vs:
                a = np.array([tuple(v) for v in vs])
                cache[n] = (vs, ps, a.min(0), a.max(0), BVHTree.FromPolygons(vs, ps))
            else:
                cache.pop(n, None)
        if f == 0:
            continue                         # the first frame only fills the cache
        n_checked += 1
        done = set()
        for n in live:
            if n not in cache:
                continue
            vn, pn, lo_n, hi_n, tn = cache[n]
            if groups[n][0] is not None and not n.startswith("road") and lo_n[2] < low[0]:
                low = (float(lo_n[2]), f, n)
            for o, (vo, po, lo_o, hi_o, to) in cache.items():
                if o == n or (o, n) in done:
                    continue
                done.add((n, o))
                if (np.maximum(lo_n, lo_o) - np.minimum(hi_n, hi_o) > 0.05).any():
                    continue
                hit = tn.overlap(to)
                if hit:
                    clashes.append((f, n, o, len(hit)))
                    continue
                d = min(min(to.find_nearest(v)[3] for v in vn[::5]), min(tn.find_nearest(v)[3] for v in vo[::5]))
                if d < near[0]:
                    near = (d, f, "%s - %s" % (n, o))
    print("CLASH frames where something moves: %d of %d; checked %d" % (n_moving, FRAMES, n_checked))
    print("CLASH clashes: %d" % len(clashes))
    for c_ in clashes[:40]:
        print("CLASH  f%d %.3fs %s x %s: %d face pairs" % (c_[0], START + c_[0] / FPS, c_[1], c_[2], c_[3]))
    print("CLASH closest pair: %.4f table units at f%d %.2fs (%s)" % (near[0], near[1], START + near[1] / FPS, near[2]))
    print("CLASH lowest point of a moving solid (roads left out): z %.4f at f%d (%s)" % low)


SHOTS["s6"] = shot_s6
