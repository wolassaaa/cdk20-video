"""HKBU SCIE1007 coursework science video. W3 explored again (11-09, the director: the first W3 is not direct enough, not his "key changing at speed", and looks a bit childish).
Three short tests of one picture: a key hangs over a complicated lock and changes shape wildly to the beat, and never goes in.
w3a: A, mechanical precision. A macro shot at f/4: a steel key hangs tip down over the keyhole; its seven pins slide in and out of the blade to new cut depths on every
     sixteenth note (eighths for the first two beats), the lock's three dials click round, the middle one the other way, with real motion blur.
w3b: B, liquid metal, after W2: the key is one mirror-metal metaball that flows from one key shape to the next, holds each one for a moment on the beat, melts again.
w3c: the plate under C (TouchDesigner draws the outlines over it): A's lock from A's camera at 3 s, no key.
w3l: the director picked B (11-09): the full W3 for the film, B's liquid key on W3's own table and lock (see shot_w3l).
The lock and keys are drawn; the keyhole is the cut through the ATP pocket of the AlphaFold DB v6 model (pocket_outline.py, as in S3 and 4-09), the blue dot is Met84.
Units are metres: the lock is 10 cm across, the key about 9 cm long. Frame 0 is the downbeat of bar 104 of Take My Breath (207.711 s), 121 BPM.
Run: BL_EXTRA=<this file> blender -b -P bl_inserts.py -- w3a <out dir> 0 359 16 1 2
W3X_CHECK=1 renders nothing: it poses every frame and prints how close the key comes to the lock (the no-clipping rule).
"""
META = {"w3a": (0.0, 360, 0.2, 0.9), "w3b": (0.0, 360, 0.2, 0.9), "w3c": (0.0, 1, 0.2, 0.9), "w3l": (574.0, 952, 0.2, 0.9)}

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
    span = float((hi - lo).max())
    s_lo, s_hi = span / 100, span / 5          # spacing searched relative to the shape, so it works in metres and in key units alike
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


# ---------------------------------------------------------------- W3 in full, direction B (picked 11-09)
XL_S = 46.0                 # B's key shapes are in metres; this takes them to the 4-09 key's own units (blade 1.7 long, bow 0.75 round)
XL_N = 280


def x_cells(fn):
    """The cells a nested function closes over, by name: the way into shot_w3's inner state without touching bl_inserts.py."""
    return dict(zip(fn.__code__.co_freevars, fn.__closure__ or ()))


def shot_w3l(sc, sky):
    """W3 (09:34-09:50, 8 bars of Take My Breath from bar 104), direction B. It is shot_w3 with three things swapped through its closures, so the first two bars (the push
    in from 4-09's last frame, the plate lifting into the lock) and the last bar (everything stops, the keys rain into the carpet, the camera climbs) are W3's own frames
    and both joins hold. Bars 2-6: in place of the steel key changing its cut, one black liquid-metal key hangs in front of the lock and becomes a new key on every
    beat (bars 2-4), every half beat (bar 5), every sixteenth (bar 6), melting a little harder each time, while the camera comes in close. It never settles and never goes
    in: on bar 7's downbeat it is held, turns to steel as it is carried down, and lies in the carpet as one key among the others. The 40 keys that circled the lock
    in the first W3 now only fall into their places from above, with the rest. No hop on landing (低龄感诊断 item 5).
    Run: BL_EXTRA=bl_w3x.py blender -b -P bl_inserts.py -- w3l <out dir> 0 951 16 0.5 2. W3X_CHECK=1: no render, every frame's nearest approach printed."""
    upd = shot_w3(sc, sky)
    cu = x_cells(upd)
    key_pose0 = cu["key_pose"].cell_contents
    ck = x_cells(key_pose0)
    hover_pose, flier_pose, rain_pose, rain = (ck[n].cell_contents for n in ("hover_pose", "flier_pose", "rain_pose", "rain"))
    cf = x_cells(flier_pose)
    slots, fl_slot, FL_T, FL_D, T_STOP, lock_pose = (cf[n].cell_contents for n in ("slots", "fl_slot", "FL_T", "FL_D", "T_STOP", "lock_pose"))
    KS = x_cells(cu["place"].cell_contents)["KS"].cell_contents
    ORB, pings, hov, NO = cu["ORB"].cell_contents, cu["pings"].cell_contents, cu["hov"].cell_contents, cu["NO"].cell_contents
    BEAT, BAR = W3_BEAT, W3_BAR
    T_HOV, T_RAIN = 2 * BAR, T_STOP + BEAT / 2
    T_SWAP = FL_T["h"] + 0.55 * FL_D          # the liquid becomes the steel key in mid air, small on screen as the camera climbs
    END = (FRAMES - 1) / FPS

    # 1. no hop on landing; the hovering key keeps the cut it ends W3 with, so the last frame is W3's
    cf["settle"].cell_contents = lambda dt: 0.0
    FINAL_CUT = cu["hover_cut"].cell_contents(END) % 24
    cu["hover_cut"].cell_contents = lambda t: FINAL_CUT
    # 2. the 40 circling keys fall into their slots from above, nearest the lock first, among the rest of the rain
    #    (only a little yaw and tilt: neighbours fall together and sit 0.021 apart, and a 0.2 rad yaw swept one key's end into the next)
    g = np.random.default_rng(1104)
    Lc = Vector(tuple(lock_pose(10.0)[0]))
    order = sorted(range(NO), key=lambda i: (Vector(slots[fl_slot[i]]) - Vector((Lc.x, Lc.y, 0.0))).length)
    orb_rain = {i: dict(slot=fl_slot[i], t0=T_RAIN + 0.02 + 0.35 * n / NO + float(g.uniform(0, 0.04)), yaw=float(g.uniform(-0.05, 0.05)), tilt=float(g.uniform(-0.08, 0.08)))
                for n, i in enumerate(order)}
    T_ORB = max(d_["t0"] for d_ in orb_rain.values())

    def key_pose(i, t):
        if i == "h":
            return None if t < T_SWAP else key_pose0("h", t)
        if isinstance(i, int):
            return rain_pose(orb_rain[i], t)
        return key_pose0(i, t)
    cu["key_pose"].cell_contents = key_pose

    # 3. the liquid key, in the 4-09 key's own units (tip toward +x, cuts on -y), riding the hovering key's pose
    rng = np.random.default_rng(104)          # W3's own cuts, drawn the same way, to reach its last one
    cut_teeth = []
    for v_ in range(24):
        xs_ = np.linspace(0.5, 1.36, 3 + v_ % 2)
        cut_teeth.append(tuple((float(x_), float(rng.uniform(0.05, 0.36))) for x_ in xs_))
    a_ = np.linspace(0, 2 * math.pi, 120, endpoint=False)
    target = ([np.array(B.round_poly(B.key_blade(-0.075, 0.0, teeth=cut_teeth[FINAL_CUT], start=0.14), 0.03)), np.c_[-0.875 + 0.75 * np.cos(a_), 0.75 * np.sin(a_)]], [])

    def to_key(shape):
        f_ = lambda q: np.c_[1.625 + q[:, 0] * XL_S, q[:, 1] * XL_S]
        return [f_(q) for q in shape[0]], [f_(q) for q in shape[1]]
    # when each shape lands: the beat in bars 2-4, half beats in bar 5, sixteenths in bar 6; bar 7's downbeat brings the last, W3's own key
    LAND = [T_HOV + BEAT * k for k in range(0, 12)] + [T_HOV + 12 * BEAT + BEAT / 2 * k for k in range(8)] + [T_HOV + 16 * BEAT + BEAT / 4 * k for k in range(16)] + [T_STOP]
    AMP = [0.6 if t_ < 3 * BAR else 0.85 if t_ < 4 * BAR else 1.0 if t_ < 5 * BAR else 1.15 if t_ < 6 * BAR else 1.3 for t_ in LAND]
    HOLD = [0.35 if t_ < 4 * BAR else 0.3 if t_ < 5 * BAR else 0.22 if t_ < 6 * BAR else 0.12 for t_ in LAND]
    SH = []
    for k in range(len(LAND)):
        p_, _ = x_fill(target if k == len(LAND) - 1 else to_key(x_key_shape(g)), XL_N, g)
        SH.append(np.c_[p_, np.zeros(len(p_))])
    KF = g.normal(0, 150 / XL_S, (3, 3))
    PH = g.uniform(0, 6.3, 3)
    WF = g.uniform(5, 9, 3)
    R0 = 0.0042 * XL_S

    def balls(t):
        """Shape k lands on LAND[k], rings once as one body and holds, melts, swells across the key and flows into shape k + 1."""
        if t < LAND[0]:
            return SH[0], R0 * 1.3
        k = len(LAND) - 1 if t >= LAND[-1] else max(j for j in range(len(LAND)) if LAND[j] <= t)
        A_, since = SH[k], t - LAND[k]
        still = A_ + 0.064 * math.exp(-since / 0.08) * math.sin(2 * math.pi * since / 0.13) * np.sin(A_ @ KF.T + WF * t + PH)
        if k == len(LAND) - 1:
            return still, R0 * 1.3
        w = (t - LAND[k]) / (LAND[k + 1] - LAND[k])
        hold = HOLD[k + 1]
        if w < hold:
            return still, R0 * 1.3
        x = smooth((w - hold) / (1 - hold))
        melt = math.sin(math.pi * x) ** 0.8 * AMP[k + 1]
        pos = A_ + (SH[k + 1] - A_) * x
        c_ = pos.mean(0)
        pos = pos + (pos - c_) * np.array([0.0, 0.3, 0.0]) * melt + 0.13 * melt * np.sin(pos @ KF.T + WF * t + PH)
        return pos, R0 * (1.3 + 0.3 * melt)

    def chaos(t):
        """A turn about the upright that grows through bars 5 and 6 and is gone by the stop: the wilder bars swing the key a little."""
        e_ = smooth((t - 4 * BAR) / BAR) * (1 - smooth((t - T_STOP + 0.3) / 0.3))
        return 0.22 * e_ * math.sin(2 * math.pi * t / (2 * BEAT)) + 0.08 * e_ * math.sin(2 * math.pi * t / (BEAT / 2) + 1.0)

    mbd = bpy.data.metaballs.new("w3l_mb")
    mbd.resolution, mbd.render_resolution, mbd.threshold = 0.037, 0.021, 5.0
    els = []
    for p_ in SH[0]:
        e_ = mbd.elements.new()
        e_.co, e_.radius = tuple(p_), R0
        els.append(e_)
    liq, lb = x_steel("w3l_liquid", (0.006, 0.006, 0.007), 0.04)          # W2's black mirror fluid: a dark dielectric, no clear coat
    lb.inputs["Metallic"].default_value = 0.0
    mbd.materials.append(liq)
    mb = bpy.data.objects.new("w3l_mb", mbd)
    sc.collection.objects.link(mb)
    mb.rotation_mode = "QUATERNION"
    mb.hide_render = True
    STEEL, T_TURN = (0.6, 0.59, 0.57), FL_T["h"]

    def liquid(t):
        ps = key_pose0("h", t)          # W3's own hovering key: hover, then carried down to its slot
        on = ps is not None and t < T_SWAP
        mb.hide_render = not on
        if not on:
            return False
        loc, q, s_ = ps
        mb.location, mb.rotation_quaternion, mb.scale = loc, Quaternion((0, 0, 1), chaos(t)) @ q, (KS * s_,) * 3
        pos, r = balls(t)
        for e_, p_ in zip(els, pos):
            e_.co, e_.radius = tuple(p_), r
        x = smooth((t - T_TURN) / (T_SWAP - T_TURN))          # turning to steel as it is carried down
        lb.inputs["Base Color"].default_value = (*lerp((0.006, 0.006, 0.007), STEEL, x), 1)
        lb.inputs["Roughness"].default_value = 0.04 + 0.18 * x
        return True

    # 4. the camera: W3's own until bar 2, in close on the liquid key through bar 6, back onto W3's own path by the end of the climb
    view0 = upd.view
    K = Vector(tuple(hover_pose(T_HOV + 8 * BEAT)[0]))          # the hovering key's origin at a still moment of its bob
    Kc = K + Vector((0, 0, -0.02))
    f0 = sc.camera.data.dof.aperture_fstop
    my = [(2 * BAR, view0(2 * BAR)),
          (2 * BAR + 2 * BEAT, dict(at=tuple(Kc + Vector((0, 0, -0.1))), az=math.radians(-4), el=math.radians(9), d=1.15, mm=45.0)),
          (3 * BAR, dict(at=tuple(Kc + Vector((0, 0, -0.08))), az=math.radians(-2), el=math.radians(8.5), d=1.0, mm=45.0)),
          (4.5 * BAR, dict(at=tuple(Kc + Vector((0, 0, -0.03))), az=math.radians(6), el=math.radians(7), d=0.78, mm=50.0)),
          (6 * BAR, dict(at=tuple(Kc), az=math.radians(12), el=math.radians(6), d=0.62, mm=50.0)),
          (T_STOP, dict(at=tuple(Kc), az=math.radians(16), el=math.radians(6.5), d=0.58, mm=50.0))]

    def mixv(p, q, x):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def mine(t):
        for (ta, a), (tb, b) in zip(my, my[1:]):
            if t < tb:
                return mixv(a, b, smooth((t - ta) / (tb - ta)))
        return my[-1][1]
    B0, B1 = T_STOP - 0.3, T_RAIN + 0.7

    def view(t):
        if t < 2 * BAR or t >= B1:
            return view0(t)
        x = smooth((t - B0) / (B1 - B0))
        v = mixv(mine(t), view0(t), x)
        v["at"] = lerp(mine(t)["at"], view0(t)["at"], x * x)          # the eye pulls back first and lets go of the key last, so the key stays in frame
        return v

    # a soft box only reflections see, held toward the camera from the key: the black liquid shows a gradient and a lit rim instead of reading as a flat cut-out.
    # It shines only while the liquid is up close and is gone well before the end, so the last frame is W3's.
    cm, cnt, cout = gk._mat("w3l_softbox")
    em = cnt.nodes.new("ShaderNodeEmission")
    tco = cnt.nodes.new("ShaderNodeTexCoord")
    sep = cnt.nodes.new("ShaderNodeSeparateXYZ")
    rmp = cnt.nodes.new("ShaderNodeMapRange")
    rmp.interpolation_type = "SMOOTHSTEP"
    rmp.inputs[1].default_value, rmp.inputs[2].default_value, rmp.inputs[3].default_value, rmp.inputs[4].default_value = 0.0, 1.0, 0.15, 1.0
    cnt.links.new(tco.outputs["Generated"], sep.inputs[0])
    cnt.links.new(sep.outputs["Y"], rmp.inputs[0])
    mul = cnt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    cnt.links.new(rmp.outputs[0], mul.inputs[0])
    cnt.links.new(mul.outputs[0], em.inputs["Strength"])
    em.inputs["Color"].default_value = (1.0, 0.985, 0.96, 1)
    cnt.links.new(em.outputs[0], cout.inputs["Surface"])
    card = mesh("w3l_softbox", [(-1.3, -0.6, 0), (1.3, -0.6, 0), (1.3, 0.6, 0), (-1.3, 0.6, 0)], [(0, 1, 2, 3)], cm)
    card.visible_camera = card.visible_diffuse = card.visible_shadow = card.visible_transmission = card.visible_volume_scatter = False
    card.rotation_mode = "QUATERNION"

    def softbox(t):
        glow_ = 14.0 * smooth((t - 2 * BAR + 0.4) / 0.8) * (1 - smooth((t - T_STOP) / 0.45))
        card.hide_render = glow_ <= 0
        mul.inputs[1].default_value = glow_
        eye = Vector(eye_of(view(t)))
        d_ = (eye - Kc).normalized()
        card.location = Kc + 2.6 * d_ + Vector((0, 0, 1.1))          # behind and above the camera, as seen from the key
        card.rotation_quaternion = (Kc - card.location).to_track_quat("Z", "Y")          # its face toward the key, its gradient bright at the top

    def fstop(t):
        near = smooth((t - 2 * BAR) / BAR) * (1 - smooth((t - B0) / (B1 - B0)))
        return math.exp(math.log(f0) + (math.log(4.0) - math.log(f0)) * near)
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    last_q[0] = None
    for f in range(FRAMES):
        v = view(f / FPS)
        shoot(c, f, v, v["at"])
        c.data.dof.aperture_fstop = fstop(f / FPS)
        c.data.dof.keyframe_insert("aperture_fstop", frame=f)
    print("W3L: %d shapes, cut %d at the end, swap to steel at %.2f s, f-stop %.1f -> 4.0, bar %.3f s, orb keys fall %.2f-%.2f s" % (
        len(SH), FINAL_CUT, T_SWAP, f0, BAR, T_RAIN, T_ORB))

    def update(t):
        upd(t)
        for o in pings:          # nothing comes up out of the screen's rings any more
            o.hide_render = True
        liquid(t - START)
        softbox(t - START)
    update.view = view

    if X_CHECK:
        mbd.resolution = mbd.render_resolution
        skip = {mb.name}
        for e_ in [hov] + [d_["obj"] for d_ in ORB] + [d_["obj"] for d_ in rain]:
            skip |= {o.name for o in e_.children_recursive} | {e_.name}
        upd(START + T_HOV + 1.0)
        bpy.context.view_layer.update()
        statics = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name not in skip and o.name != "floor" and not o.name.startswith("w3_ping")]
        vs, ts = x_world_tris(statics)
        tree = BVHTree.FromPolygons(vs, ts)
        print("W3L check: %d still objects, %d triangles" % (len(statics), len(ts)))
        kpts = []
        for o in hov.children:
            kpts += [tuple(v_.co) for v_ in o.data.vertices]
        kpts = np.array(kpts)[np.random.default_rng(3).choice(len(kpts), 200, replace=False)]

        def kworld(ps):
            loc, q, s_ = ps
            return kpts @ np.array(q.to_matrix()).T * (KS * s_) + np.array(tuple(loc))
        if os.environ.get("W3X_GAP"):          # the carpet's own gap: every orb key in its slot on the last frame, nearest neighbours, to read orb_key against
            rest = {i: kworld(key_pose(i, END)) for i in range(NO) if key_pose(i, END) is not None}
            gap = min(float(np.sqrt(((a_[::3, None] - b_[None, ::3]) ** 2).sum(-1)).min()) for i, a_ in rest.items() for j, b_ in rest.items()
                      if i < j and np.linalg.norm(a_.mean(0) - b_.mean(0)) < 0.16)
            print("W3L GAP carpet neighbours at rest %.4f (%d keys)" % (gap, len(rest)))
            print("INSERT_OK", SHOT, "gap")
            sys.exit(0)
        pair = None
        best = dict(liq_lock=(9.0, 0), liq_key=(9.0, 0), liq_floor=(9.0, 0), orb_lock=(9.0, 0), orb_key=(9.0, 0))
        ids = ["h"] + list(range(NO)) + [("r", n) for n in range(len(rain))]
        RAIN_ONLY = bool(os.environ.get("W3X_RAIN"))          # only the frames of the fall, keys only (the liquid is gone by then)
        for f in range(FRAMES):
            t = f / FPS
            if RAIN_ONLY and not T_RAIN - 0.1 <= t <= T_ORB + 1.0:
                continue
            on = False if RAIN_ONLY else liquid(t)
            moving = {}
            if on or T_RAIN <= t <= T_ORB + 1.0:
                for i in ids:
                    ps = key_pose(i, t)
                    if ps is not None:
                        moving[i] = kworld(ps)
            if on:
                bpy.context.view_layer.update()
                lv, _ = x_world_tris([mb])
                lv = np.array(lv[::3])
            if on and len(lv):          # empty while the drop is still a speck
                best["liq_lock"] = min(best["liq_lock"], (min(tree.find_nearest(Vector(tuple(p_)))[3] for p_ in lv), f))
                best["liq_floor"] = min(best["liq_floor"], (float(lv[:, 2].min()), f))
                for w_ in moving.values():
                    if np.linalg.norm(w_.mean(0) - lv.mean(0)) < 0.4:
                        best["liq_key"] = min(best["liq_key"], (float(np.sqrt(((lv[::4, None] - w_[None, ::4]) ** 2).sum(-1)).min()), f))
            for i, w_ in moving.items():
                if not isinstance(i, int) or t > orb_rain[i]["t0"] + 0.7:
                    continue          # an orb key in the air
                best["orb_lock"] = min(best["orb_lock"], (min(tree.find_nearest(Vector(tuple(p_)))[3] for p_ in w_[::5]), f))
                for j, w2 in moving.items():
                    if j != i and np.linalg.norm(w_.mean(0) - w2.mean(0)) < 0.16:
                        dk = float(np.sqrt(((w_[::3, None] - w2[None, ::3]) ** 2).sum(-1)).min())
                        if dk < best["orb_key"][0]:
                            best["orb_key"], pair = (dk, f), (i, j)
            if f % 120 == 0:
                print("W3L check frame %d: %s" % (f, {k: round(v_[0], 4) for k, v_ in best.items()}))
        print("W3L CHECK (table units; the hovering key is %.3f long) %s" % (3.25 * KS * 3.2, {k: "%.4f at frame %d" % v_ for k, v_ in best.items()}))
        print("W3L CHECK orb_key pair", pair)
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["w3a"] = shot_w3a
SHOTS["w3b"] = shot_w3b
SHOTS["w3c"] = shot_w3c
SHOTS["w3l"] = shot_w3l
