"""HKBU SCIE1007 coursework science video. W3 explored again (11-09, the director: the first W3 is not direct enough, not his "key changing at speed", and looks a bit childish).
Three short tests of one picture: a key hangs over a complicated lock and changes shape wildly to the beat, and never goes in.
w3a: A, mechanical precision. A macro shot at f/4: a steel key hangs tip down over the keyhole; its seven pins slide in and out of the blade to new cut depths on every
     sixteenth note (eighths for the first two beats), the lock's three dials click round, the middle one the other way, with real motion blur.
w3b: B, liquid metal, after W2: the key is one mirror-metal metaball that flows from one key shape to the next, holds each one for a moment on the beat, melts again.
w3c: the plate under C (TouchDesigner draws the outlines over it): A's lock from A's camera at 3 s, no key.
The lock and keys are drawn; the keyhole is the cut through the ATP pocket of the AlphaFold DB v6 model (pocket_outline.py, as in S3 and 4-09), the blue dot is Met84.
Units are metres: the lock is 10 cm across, the key about 9 cm long. Frame 0 is the downbeat of bar 104 of Take My Breath (207.711 s), 121 BPM.
Run: BL_EXTRA=<this file> blender -b -P bl_inserts.py -- w3a <out dir> 0 359 16 1 2
W3X_CHECK=1 renders nothing: it poses every frame and prints how close the key comes to the lock (the no-clipping rule).
"""
META = {"w3a": (0.0, 360, 0.2, 0.9), "w3b": (0.0, 360, 0.2, 0.9), "w3c": (0.0, 1, 0.2, 0.9)}

import bmesh   # noqa: E402
from mathutils.bvhtree import BVHTree   # noqa: E402

X_BEAT = 60.0 / 121.0
X_RL = 0.05                  # the lock's radius
X_HR = 0.0135                # the keyhole's half size
X_TOP = 0.016                # the face plate's top: the highest point of the lock
X_CHECK = bool(os.environ.get("W3X_CHECK"))


def x_steel(name, rgb=(0.72, 0.71, 0.69), rough=0.2, aniso=0.0):
    m, nt, out = gk._mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Anisotropic"].default_value = aniso
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, b


def x_deselect():
    for o in bpy.context.selected_objects:          # B.extrude applies transforms to whatever is selected
        o.select_set(False)


def x_circle(r, n=160, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def x_lock(sc):
    """The lock lying on the table, keyhole up: a Klein blue puck, a steel face plate with the pocket's outline cut through it, three steel dials round it, Met84's blue dot
    on the keyhole's edge and one red index on the plate. Returns the dials (to turn) and every part (for the clash check)."""
    blue = P.gloss(P.KLEIN, 0.3, 0.6)
    steel, _ = x_steel("w3x_dialsteel", (0.7, 0.69, 0.67), 0.26)
    plate_m, _ = x_steel("w3x_plate", (0.74, 0.73, 0.71), 0.16)
    ink = gk.surface((0.012, 0.012, 0.014), 0.45)
    red = P.gloss(P.RED, 0.3, 0.5)
    parts = []
    b, R = 0.0025, X_RL
    prof = [(0.0, 0.0), (R - b, 0.0)] + [(R - b + b * math.sin(a), b - b * math.cos(a)) for a in np.linspace(0.2, math.pi / 2, 5)] + \
        [(R - b + b * math.cos(a), 0.010 - b + b * math.sin(a)) for a in np.linspace(0, math.pi / 2, 6)] + [(0.0, 0.010)]
    parts.append(lathe(prof, blue, "w3x_puck", None, 192))
    parts.append(lathe([(0.0, 0.0101), (0.021, 0.0101)], ink, "w3x_well", None, 96))           # the keyhole's floor reads dark
    ol = json.load(open(HERE + "frames/pocket_outline.json"))
    hole = np.array(ol["points"], float) * X_HR
    plate = B.extrude([x_circle(0.0215), [tuple(p) for p in hole[::-1]]], X_TOP - 0.010, 0.0007, z=0.010, name="w3x_faceplate", mat=plate_m)
    x_deselect()
    parts.append(plate)
    # Met84's dot just outside the keyhole's edge, on the plate's top
    hp = hole[HK_HINGE_I]
    out_ = hp / np.linalg.norm(hp)
    dot_m, _ = x_steel("w3x_dot", (0.2, 0.3, 1.0), 0.3)
    dn = dot_m.node_tree.nodes["Principled BSDF"]
    dn.inputs["Metallic"].default_value = 0.0
    dn.inputs["Base Color"].default_value = dn.inputs["Emission Color"].default_value = (*P.BLUE, 1)
    dn.inputs["Emission Strength"].default_value = 1.2
    dot = lathe([(0.0, 0.0), (0.0011, 0.0), (0.00115, 0.0003), (0.0008, 0.0006), (0.0, 0.0007)], dot_m, "w3x_dot", None, 32)
    dot.location = (float(hp[0] + 0.0016 * out_[0]), float(hp[1] + 0.0016 * out_[1]), X_TOP)
    parts.append(dot)
    # the dials: (inner, outer, height, ticks)
    DIALS = [(0.0222, 0.0296, 0.0052, 72), (0.0304, 0.0381, 0.0044, 60), (0.0389, 0.0478, 0.0036, 48)]
    dials = []
    for k, (ri, ro, h, n) in enumerate(DIALS):
        e = empty("w3x_dial%d" % k)
        e.location = (0, 0, 0.010)
        bb = 0.0004
        pr = [(ri, 0.0), (ro, 0.0), (ro, h - bb), (ro - bb, h), (ri + bb, h), (ri, h - bb), (ri, 0.0)]
        parts.append(lathe(pr, steel, "w3x_ring%d" % k, e, 256))
        bm = bmesh.new()
        for i in range(n):
            a = 2 * math.pi * i / n
            long_ = i % 6 == 0
            ln = (ro - ri) * (0.62 if long_ else 0.34)
            M = Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((ro - bb - ln / 2, 0, h)) @ Matrix.Diagonal((ln, 0.00045 if long_ else 0.0003, 0.0003, 1))
            bmesh.ops.create_cube(bm, size=1.0, matrix=M)
        me = bpy.data.meshes.new("w3x_ticks%d" % k)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(ink)
        o = bpy.data.objects.new("w3x_ticks%d" % k, me)
        sc.collection.objects.link(o)
        o.parent = e
        parts.append(o)
        dials.append((e, n))
    # one red index on the face plate, far side of the keyhole
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.0, 0.0188, X_TOP)) @ Matrix.Diagonal((0.0011, 0.0026, 0.0007, 1)))
    me = bpy.data.meshes.new("w3x_index")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(red)
    o = bpy.data.objects.new("w3x_index", me)
    sc.collection.objects.link(o)
    parts.append(o)
    return dials, parts


def x_studio(sc):
    """A product-shot trick: a black mat on the table in front of the lock with one bright strip across it, seen only in reflections. The camera, the light and
    the shadows never see it, so the table stays bone; the key's upright face mirrors the mat instead of the bone table, and reads as dark steel with one moving highlight."""
    def card(name, x0, x1, y0, y1, z, col, emit):
        m, nt, out = gk._mat(name)
        if emit:
            e = nt.nodes.new("ShaderNodeEmission")
            e.inputs[0].default_value, e.inputs[1].default_value = (*col, 1), emit
        else:
            e = nt.nodes.new("ShaderNodeBsdfDiffuse")
            e.inputs[0].default_value = (*col, 1)
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        o = mesh(name, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(0, 1, 2, 3)], m)
        o.visible_camera = o.visible_diffuse = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
        return o
    card("w3x_mat", -0.6, 0.6, -0.9, -0.056, 0.0004, (0.01, 0.01, 0.011), 0)
    card("w3x_strip", -0.6, 0.6, -0.175, -0.150, 0.0006, (1.0, 0.98, 0.95), 6.0)
    card("w3x_strip2", -0.6, 0.6, -0.42, -0.40, 0.0006, (1.0, 0.98, 0.95), 2.5)


def x_world_tris(objs):
    """Every triangle of these objects in world space, as it stands now."""
    dg = bpy.context.evaluated_depsgraph_get()
    vs, ts = [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        me.calc_loop_triangles()
        mw = oe.matrix_world
        base = len(vs)
        vs += [tuple(mw @ v.co) for v in me.vertices]
        ts += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]
        oe.to_mesh_clear()
    return vs, ts


def x_nearest(key_objs, lock_objs, every=1):
    """The nearest any point of the key comes to the lock's surface, and whether any key point is inside the lock (below its top and within its rim)."""
    vs, ts = x_world_tris(lock_objs)
    tree = BVHTree.FromPolygons(vs, ts)
    kv, _ = x_world_tris(key_objs)
    kv = kv[::every]
    best = min(tree.find_nearest(Vector(p))[3] for p in kv)
    inside = sum(1 for p in kv if p[2] < X_TOP and math.hypot(p[0], p[1]) < X_RL)
    return best, inside, min(p[2] for p in kv)


def x_dial_angle(k, t, n, events, ease=0.06):
    """Dial k clicks round (k + 1) ticks on every event, the middle dial the other way."""
    i = sum(1 for e in events if e <= t)
    x = 0.0
    if i:
        x = smooth((t - events[i - 1]) / ease)
    steps = max(0, i - 1) + x
    return (-1 if k == 1 else 1) * (k + 1) * steps * 2 * math.pi / n


def x_camera(sc, v0, v1, focus, stop):
    c = lens(sc, stop)
    last_q[0] = None
    for f in range(FRAMES):
        x = smooth(f / max(1, FRAMES - 1)) * 0.6 + 0.4 * f / max(1, FRAMES - 1)          # slow, nearly even, eased only a little
        v = dict(at=lerp(v0["at"], v1["at"], x), az=v0["az"] + (v1["az"] - v0["az"]) * x, el=v0["el"] + (v1["el"] - v0["el"]) * x,
                 d=v0["d"] + (v1["d"] - v0["d"]) * x, mm=v0["mm"])
        shoot(c, f, v, focus)
    return c


def x_key_frame():
    """Key space: x runs up the key from its tip (x = 0, pointing down), y across it (cuts on the -y edge), z through it. This turns it upright, its face to the camera."""
    return Matrix(((0, -1, 0), (0, 0, 1), (-1, 0, 0))).to_quaternion()


# ---------------------------------------------------------------- A
XA_L, XA_W, XA_T = 0.040, 0.009, 0.0026           # blade length, width, thickness
XA_NP, XA_PW, XA_PL, XA_PT = 7, 0.0029, 0.0070, 0.0018          # pins: count, width along the blade, length, thickness
XA_DEPTH = [0.0006, 0.0016, 0.0026, 0.0036, 0.0046, 0.0056]     # six cut depths, as on a real key
XA_GAP = 0.0075                                    # the tip's height over the face plate


def shot_w3a(sc, sky, plate_only=False):
    sky(0.0)
    sc.render.motion_blur_shutter = 1.0           # rendered every second 60 fps frame: a 180 degree shutter at 30 fps
    dials, lock_parts = x_lock(sc)
    x_studio(sc)
    v0 = dict(at=(0.004, 0.0, 0.037), az=math.radians(-11), el=math.radians(16), d=0.29, mm=100)
    v1 = dict(at=(0.004, 0.0, 0.036), az=math.radians(-4), el=math.radians(13.5), d=0.25, mm=100)
    focus = (0.0, -0.0013, 0.040)          # the key's front face
    if plate_only:
        vm = dict(at=lerp(v0["at"], v1["at"], 0.5), az=(v0["az"] + v1["az"]) / 2, el=(v0["el"] + v1["el"]) / 2, d=(v0["d"] + v1["d"]) / 2, mm=100)
        c = x_camera(sc, vm, vm, focus, 5.6)
        sc.frame_set(0)
        from bpy_extras.object_utils import world_to_camera_view
        px_ = lambda p: tuple(round(v_, 1) for v_ in ((world_to_camera_view(sc, c, Vector(p)).x * 1920), (1 - world_to_camera_view(sc, c, Vector(p)).y) * 1080))
        tip, top = (0.0, 0.0, X_TOP + XA_GAP), (0.0, 0.0, X_TOP + XA_GAP + XA_L)
        print("W3XC view", {k: (round(math.degrees(v), 2) if k in ("az", "el") else v) for k, v in vm.items()})
        print("W3XC key on screen (1920x1080): tip %s, blade top %s, %.2f px per mm" % (px_(tip), px_(top), math.dist(px_(tip), px_(top)) / (XA_L * 1000)))
        return lambda t: None
    x_camera(sc, v0, v1, focus, 5.6)

    key_m, _ = x_steel("w3x_key", (0.8, 0.79, 0.76), 0.09)
    pin_m, _ = x_steel("w3x_pin", (0.84, 0.83, 0.8), 0.07)
    ink = gk.surface((0.012, 0.012, 0.014), 0.4)
    root = empty("w3x_key")
    root.rotation_quaternion = x_key_frame()
    L, W, T = XA_L, XA_W, XA_T
    blade = B.round_poly([(-L - 0.004, W / 2 + 0.0022), (-L + 0.0045, W / 2 + 0.0022), (-L + 0.0055, W / 2), (-0.0065, W / 2), (0.0, 0.0006), (0.0, -0.0006),
                          (-0.003, -W / 2), (-L - 0.004, -W / 2)], 0.0007)
    RB = 0.0115
    bc = (-L - 0.003 - RB, 0.0)
    parts = [B.extrude([blade], T, 0.0004, z=-T / 2, name="w3x_blade", mat=key_m),
             B.extrude([x_circle(RB, 160, *bc), x_circle(0.0042, 96, *bc)[::-1]], T + 0.0006, 0.0006, z=-(T + 0.0006) / 2, name="w3x_bow", mat=key_m)]
    x_deselect()
    bm = bmesh.new()          # the ring of six on the bow, as on 4-09's keys
    hexa = [Vector((bc[0] + 0.0078 * math.cos(math.radians(30 + 60 * i)), bc[1] + 0.0078 * math.sin(math.radians(30 + 60 * i)), -(T + 0.0006) / 2)) for i in range(6)]
    for i, c_ in enumerate(hexa):
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.00085, matrix=Matrix.Translation(c_))
        a_, b_ = c_, hexa[(i + 1) % 6]
        d_ = b_ - a_
        M = Matrix.Translation((a_ + b_) / 2) @ Vector((0, 0, 1)).rotation_difference(d_.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.00035, radius2=0.00035, depth=d_.length, matrix=M)
    me = bpy.data.meshes.new("w3x_hex")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ink)
    hx = bpy.data.objects.new("w3x_hex", me)
    sc.collection.objects.link(hx)
    B.smooth(hx)
    parts.append(hx)
    for o in parts:
        o.parent = root
    pin_poly = B.round_poly([(-XA_PW / 2, XA_PL), (-XA_PW / 2, 0.0013), (0.0, 0.0), (XA_PW / 2, 0.0013), (XA_PW / 2, XA_PL)], 0.0004)
    PX = np.linspace(-L + 0.0075, -0.0090, XA_NP)
    pins = []
    for j in range(XA_NP):
        o = B.extrude([pin_poly], XA_PT, 0.0003, z=-XA_PT / 2, name="w3x_pin%d" % j, mat=pin_m)
        x_deselect()
        o.parent = root
        pins.append(o)
    assert XA_PL - XA_DEPTH[0] < W - 0.0005, "a pin's hidden end would come out of the blade's back"
    assert PX[1] - PX[0] > XA_PW + 0.0004, "pins would touch"

    # when the pins re-cut: eighths for the first two beats, then every sixteenth
    EV = [i * X_BEAT / 2 for i in range(4)] + [2 * X_BEAT + i * X_BEAT / 4 for i in range(80)]
    EV = [e for e in EV if e < FRAMES / FPS + 0.1]
    g = np.random.default_rng(2023)
    CUTS = [g.integers(0, len(XA_DEPTH), XA_NP)]
    for _ in EV:
        c_ = g.integers(0, len(XA_DEPTH), XA_NP)
        while (c_ == CUTS[-1]).sum() > 2:          # most pins move every time
            c_ = g.integers(0, len(XA_DEPTH), XA_NP)
        CUTS.append(c_)
    STAG, TR = 0.007, 0.05          # the ripple runs from the tip to the bow; each pin takes 50 ms to slide
    DEV = [i * X_BEAT for i in range(16)]          # the dials click on the beat for a bar, then on every eighth
    DEV = DEV[:4] + [4 * X_BEAT + i * X_BEAT / 2 for i in range(24)]

    def depth(j, t):
        tj = t - STAG * j
        i = sum(1 for e in EV if e <= tj)
        a_ = XA_DEPTH[CUTS[max(0, i - 1)][j]] if i else XA_DEPTH[CUTS[0][j]]
        b_ = XA_DEPTH[CUTS[i][j]]
        return a_ + (b_ - a_) * smooth((tj - EV[i - 1]) / TR) if i else b_

    def key_pose(t):
        beat = t / X_BEAT
        jolt = math.exp(-(beat % 1) / 0.12) if t >= 0 else 0.0          # a small lift on every beat
        z = X_TOP + XA_GAP + 0.0012 * jolt + 0.0006 * math.sin(2 * math.pi * t / 2.9)
        yaw = math.radians(9) * math.sin(2 * math.pi * t / 5.2 + 0.4)
        tilt = math.radians(2.0) * math.sin(2 * math.pi * t / 3.7)
        return Vector((0.0, 0.0, z)), Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), tilt) @ x_key_frame()

    def pose(t):
        loc, q = key_pose(t)
        root.location, root.rotation_quaternion = loc, q
        for j, o in enumerate(pins):
            o.location = (float(PX[j]), -W / 2 - depth(j, t), 0.0)
        for k, (e, n) in enumerate(dials):
            e.rotation_quaternion = Quaternion((0, 0, 1), x_dial_angle(k, t, n, DEV))

    key_objs = parts + pins
    if X_CHECK:
        worst = (1.0, 0, 0)
        for f in range(FRAMES):
            pose(f / FPS)
            bpy.context.view_layer.update()
            r = x_nearest(key_objs, lock_parts, 3)
            worst = min(worst, r)
            if f % 60 == 0:
                print("W3XA check frame %d: nearest %.2f mm, key points inside the lock %d, lowest key point %.2f mm over the table" % (f, r[0] * 1000, r[1], r[2] * 1000))
        print("W3XA CHECK nearest %.2f mm over %d frames, key points inside the lock %d, lowest %.2f mm (lock top %.1f mm)" % (worst[0] * 1000, FRAMES, worst[1], worst[2] * 1000, X_TOP * 1000))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)

    def update(t):
        f = round((t - START) * FPS)
        for o in [root] + pins + [e for e, _ in dials]:
            o.animation_data_clear()
        for s_ in (-0.5, 0.5):          # keyed either side of the frame, so the shutter sees the motion
            pose((f + s_) / FPS)
            root.keyframe_insert("location", frame=f + s_)
            root.keyframe_insert("rotation_quaternion", frame=f + s_)
            for o in pins:
                o.keyframe_insert("location", frame=f + s_)
            for e, _ in dials:
                e.keyframe_insert("rotation_quaternion", frame=f + s_)
    return update


def shot_w3c(sc, sky):
    return shot_w3a(sc, sky, plate_only=True)


# ---------------------------------------------------------------- B
XB_N = 280                  # metaballs
XB_R = 0.0042               # their radius at rest: big against their 2 mm spacing, so the sheet comes out smooth
XB_GAP = 0.0105             # the tip's height over the face plate
XB_U = 100.0                # the metaball is built 100 times too big and scaled down: Blender will not mesh it finer than 5 mm


def x_inside(pts, poly):
    """Even-odd test of many points against one polygon."""
    x, y = pts[:, 0], pts[:, 1]
    px_, py_ = poly[:, 0], poly[:, 1]
    qx, qy = np.roll(px_, -1), np.roll(py_, -1)
    cross = ((py_[None, :] > y[:, None]) != (qy[None, :] > y[:, None]))
    xint = px_[None, :] + (y[:, None] - py_[None, :]) * (qx - px_)[None, :] / np.where(qy - py_ == 0, 1e-12, qy - py_)[None, :]
    return ((cross & (x[:, None] < xint)).sum(1) % 2) == 1


def x_key_shape(g):
    """One drawn key outline in key space (tip at the origin, running up -x): bow, blade and cuts all vary. Returns the outer outline and its holes."""
    L = g.uniform(0.034, 0.046)
    W = g.uniform(0.0095, 0.0125)
    nt = int(g.integers(3, 7))
    xs = np.linspace(-L + 0.007, -0.008, nt)
    tw = min(0.0028, (xs[1] - xs[0]) * 0.42) if nt > 1 else 0.0028
    pts = [(-L - 0.003, W / 2), (-0.0055, W / 2), (0.0, 0.0)]
    both = g.random() < 0.3
    for xc in xs[::-1]:
        d = g.uniform(0.0015, 0.0062)
        pts += [(xc + tw, -W / 2), (xc + tw * 0.4, -W / 2 - d), (xc - tw * 0.4, -W / 2 - d), (xc - tw, -W / 2)]
    pts.append((-L - 0.003, -W / 2))
    if both:          # some keys are cut on both edges
        top = [(-L - 0.003, W / 2)]
        for xc in xs[1::2]:
            d = g.uniform(0.0015, 0.0045)
            top += [(xc - tw, W / 2), (xc - tw * 0.4, W / 2 + d), (xc + tw * 0.4, W / 2 + d), (xc + tw, W / 2)]
        pts = top + pts[1:]
    blade = np.array(B.round_poly(pts, 0.0008))
    kind = int(g.integers(0, 4))
    RB = g.uniform(0.011, 0.0145)
    bc = np.array([-L - 0.002 - RB, 0.0])
    a = np.linspace(0, 2 * math.pi, 120, endpoint=False)
    if kind == 0:            # round
        r = np.full_like(a, RB)
    elif kind == 1:          # six sided
        r = RB * np.cos(math.pi / 6) / np.cos((a + math.pi / 6) % (math.pi / 3) - math.pi / 6)
    elif kind == 2:          # rounded square
        r = RB * 0.92 / (np.abs(np.cos(a)) ** 5 + np.abs(np.sin(a)) ** 5) ** 0.2
    else:                    # three lobes
        r = RB * (0.82 + 0.18 * np.cos(3 * a))
    bow = np.c_[bc[0] + r * np.cos(a), bc[1] + r * np.sin(a)]
    hole = np.c_[bc[0] + 0.0045 * np.cos(a), bc[1] + 0.0045 * np.sin(a)]
    return [blade, bow], [hole]


def x_fill(shape, n, g):
    """n points spread evenly over a key shape, ordered up the key so that point i of one shape flows to point i of the next."""
    outs, holes = shape
    allp = np.concatenate(outs)
    lo, hi = allp.min(0), allp.max(0)

    def grid(s):
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0], s), np.arange(lo[1], hi[1], s * 0.866))
        xs = xs + (np.arange(xs.shape[0])[:, None] % 2) * s / 2
        p = np.c_[xs.ravel(), ys.ravel()]
        ok = np.zeros(len(p), bool)
        for o in outs:
            ok |= x_inside(p, o)
        for h in holes:
            ok &= ~x_inside(p, h)
        return p[ok]
    s_lo, s_hi = 0.0008, 0.005
    for _ in range(30):
        s = (s_lo + s_hi) / 2
        if len(grid(s)) > n:
            s_lo = s
        else:
            s_hi = s
    p = grid(s_lo)
    p = p[np.sort(g.choice(len(p), n, replace=False))]
    return p[np.lexsort((p[:, 1], np.round(p[:, 0] / 0.003)))], s_lo


def shot_w3b(sc, sky):
    sky(0.0)
    dials, lock_parts = x_lock(sc)
    x_studio(sc)
    v0 = dict(at=(0.0, 0.0, 0.050), az=math.radians(-10), el=math.radians(13), d=0.42, mm=85)
    v1 = dict(at=(0.0, 0.0, 0.048), az=math.radians(-3), el=math.radians(11), d=0.38, mm=85)
    x_camera(sc, v0, v1, (0.0, 0.0, 0.052), 4.5)

    g = np.random.default_rng(121)
    NS = int(FRAMES / FPS / X_BEAT) + 3
    SH, spacing = [], []
    for _ in range(NS):
        p, s = x_fill(x_key_shape(g), XB_N, g)
        SH.append(np.c_[p, np.zeros(len(p))])
        spacing.append(s)
    print("W3XB %d shapes, %d balls each, spacing %.2f-%.2f mm" % (NS, XB_N, min(spacing) * 1000, max(spacing) * 1000))
    KF = g.normal(0, 150, (3, 3))
    PH = g.uniform(0, 6.3, 3)          # one phase per wave, not per ball: the whole body flows together
    WF = g.uniform(5, 9, 3)

    mbd = bpy.data.metaballs.new("w3x_mb")
    mbd.resolution, mbd.render_resolution, mbd.threshold = 0.08, 0.045, 5.0
    els = []
    for p in SH[0]:
        e = mbd.elements.new()
        e.co, e.radius = tuple(p * XB_U), XB_R * XB_U
        els.append(e)
    liq, lb = x_steel("w3x_liquid", (0.62, 0.62, 0.65), 0.04)
    mbd.materials.append(liq)
    mb = bpy.data.objects.new("w3x_mb", mbd)
    sc.collection.objects.link(mb)
    mb.rotation_mode = "QUATERNION"
    mb.scale = (1 / XB_U,) * 3

    def balls(t):
        """Shape k is crisp on beat k; it trembles a moment, melts and flows into shape k + 1, landing on the next beat. A bar's downbeat splashes harder."""
        b = t / X_BEAT
        k = int(math.floor(b))
        w = b - k
        A, Bn = SH[k], SH[k + 1]
        HOLD = 0.3
        if w < HOLD:          # landing: the surface rings once, as one body, and goes still
            wob = 0.0014 * math.exp(-w / 0.08) * math.sin(2 * math.pi * w / 0.13) if k else 0.0
            pos, melt = A + wob * np.sin(A @ KF.T + WF * t + PH), 0.0
        else:
            x = smooth((w - HOLD) / (1 - HOLD))
            melt = math.sin(math.pi * x) ** 0.8 * (1.35 if (k + 1) % 4 == 0 else 1.0)
            pos = A + (Bn - A) * x
        flow = np.sin(pos @ KF.T + WF * t + PH)
        c = pos.mean(0)
        bulge = (pos - c) * np.array([0.0, 0.3, 0.0]) * melt          # it swells across the key, never along it, so the tip never reaches down
        pos = pos + bulge + 0.0028 * melt * flow
        return pos, XB_R * (1.3 + 0.3 * melt)          # never back to bare size: under a mirror finish the balls' lattice shows as dimples

    def key_pose(t):
        z = X_TOP + XB_GAP + 0.0005 * math.sin(2 * math.pi * t / 2.9)
        yaw = math.radians(12) * math.sin(2 * math.pi * t / 5.5 + 0.3)
        return Vector((0.0, 0.0, z)), Quaternion((0, 0, 1), yaw) @ x_key_frame()

    DEV = [i * X_BEAT for i in range(16)]

    def pose(t):
        mb.location, mb.rotation_quaternion = key_pose(t)
        pos, r = balls(t)
        for e, p in zip(els, pos * XB_U):
            e.co, e.radius = tuple(p), r * XB_U
        for k, (e, n) in enumerate(dials):
            e.rotation_quaternion = Quaternion((0, 0, 1), x_dial_angle(k, t, n, DEV, 0.08))

    if X_CHECK:
        mbd.resolution = mbd.render_resolution          # measure the surface that renders
        worst = (1.0, 0, 0)
        for f in range(FRAMES):
            pose(f / FPS)
            bpy.context.view_layer.update()
            r = x_nearest([mb], lock_parts, 2)
            worst = min(worst, r)
            if f % 60 == 0:
                print("W3XB check frame %d: nearest %.2f mm, inside %d, lowest %.2f mm" % (f, r[0] * 1000, r[1], r[2] * 1000))
        print("W3XB CHECK nearest %.2f mm over %d frames, liquid points inside the lock %d, lowest %.2f mm (lock top %.1f mm)" % (worst[0] * 1000, FRAMES, worst[1], worst[2] * 1000, X_TOP * 1000))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)

    def update(t):
        f = round((t - START) * FPS)
        pose(t)
        for e, _ in dials:
            e.animation_data_clear()
        for s_ in (-0.5, 0.5):
            for k, (e, n) in enumerate(dials):
                e.rotation_quaternion = Quaternion((0, 0, 1), x_dial_angle(k, (f + s_) / FPS, n, DEV, 0.08))
                e.keyframe_insert("rotation_quaternion", frame=f + s_)
    return update


SHOTS["w3a"] = shot_w3a
SHOTS["w3b"] = shot_w3b
SHOTS["w3c"] = shot_w3c
