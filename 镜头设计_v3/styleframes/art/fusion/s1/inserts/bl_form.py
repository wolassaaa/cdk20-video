"""HKBU SCIE1007 coursework science video. Form test on shot k (S3, the lock and the key, 287.0-312.0 s): the same lock, key, materials, light and motion as shot k
(k_things, k_place, plate_kit as they are), shown three other ways. Only the camera, the framing and, in F2, a cut-away change. Kept in its own file and run inside
bl_inserts.py (BL_EXTRA); bl_inserts.py, plate_kit.py and bl_shots.py are not touched.

fk1, macro product film: a low camera close to the table, a wide-open lens with the focus riding on the key, the lock and key filling the frame, slow pushes and drifts.
fk2, cut-away: both locks and both keys are cut through the teeth along the way the key goes in, and the cut faces are a paler shade of the same colour; the camera looks
     at the cut from the front, so the teeth can be seen dropping into the notches of the right lock and standing on the solid top of the wrong one.
fk3, deep-focus telephoto: one continuous camera at a middle height with a long lens and everything in focus, no falling and climbing, the things large in frame.

The first 0.75 s is shot k's own pan, so the cut from the shot before stays as it is. After it each version runs its own camera through keys (eye, look-at, lens),
joined by a Catmull-Rom curve so the camera never stops dead between them.

Run:   BL_EXTRA=bl_form.py blender.exe -b -t 3 -P bl_inserts.py -- fk1 <out dir> [first] [last] [samples] [size] [step]
Check: FORM_CLASH=<step> measures the gaps between every pair of solids, each solid and the table, and the camera and every solid; nothing is rendered.
Track: FORM_TRACK=<json> writes where the label points sit on screen, every other frame from 287.0 s (frame 72), for the words laid over in Remotion.
"""
META = {"fk1": (285.8, 1644, 0.2, 0.9), "fk2": (285.8, 1644, 0.2, 0.9), "fk3": (285.8, 1644, 0.2, 0.9)}

FK_IN = 287.75                          # shot k's own pan runs to here; each version falls from it into its first key
FK_CUT_KEY = -0.36                      # fk2: where each key is cut, in its own F3 units: through all three teeth
FK_CUT = dict(lock_a=-0.36, lock_b=-0.06)     # fk2: where each lock is cut, under the table: the plane the key's teeth sit in when it comes down on that lock


def fk_v(at, az, el, d, mm):
    return dict(at=at, az=math.radians(az), el=math.radians(el), d=d, mm=mm)


FK_LIFT = 0.004                         # every key rides this much above where shot k puts it, so lying on a surface is a touch, not an overlap


FK_BACK = dict(key_a=-0.06, key_b=0.08)     # shot k lays each key down with its tip or bow just inside the edge of a lock; these move the resting place clear


def fk_place(t):
    at = k_place(t)
    over = dict(key_a=smooth((t - OVER_A[0]) / OVER_A[1]), key_b=smooth((t - OVER_B[0]) / OVER_B[1]))
    ride = dict(key_a=jolt(t, HIT_A, 0.02), key_b=jolt(t, HIT_B, 0.03))     # a seated key jumps with the lock it sits in when the lock is knocked
    for n in ("key_a", "key_b"):
        at[n] = (at[n][0] + FK_BACK[n] * (1 - over[n]), at[n][1], at[n][2] + FK_LIFT + ride[n])
    if t > K_LEAVE[0]:          # the first key leaves straight up until its teeth clear the pocket, then sideways: shot k's sideways start scrapes the pocket wall
        u = (t - K_LEAVE[0]) / K_LEAVE[1]
        x0 = at["key_a"][0] + 3.0 * u * u / K_S
        at["key_a"] = (x0 - 3.0 * max(0.0, u - 0.12) ** 2 / K_S, at["key_a"][1], at["key_a"][2])
    return at


def fk_key_at(name, t, local):
    """World point of a key-local F3 point at time t."""
    p = fk_place(t)[name]
    return on_k(local[0] + p[0], local[1] + p[1], local[2] + p[2])


# The keys. Each is (time, view); a view's "at" may be a function of t, so the camera can ride on a moving key.
KEYS = dict(
    fk1=[(289.25, fk_v((69.75, -2.75, 0.25), -28, 9, 6.5, 85)),
         (292.5, fk_v((68.3, -2.78, 0.15), -40, 9, 5.2, 85)),
         (294.6, fk_v((67.7, -2.68, 0.3), -30, 10, 6.4, 85)),
         (296.0, fk_v(lambda t: fk_key_at("key_a", t, (-4.1, 0.05, 0.32)), -18, 13, 6.0, 85)),
         (297.6, fk_v((68.4, -2.72, 0.05), -12, 14, 6.0, 85)),
         (299.6, fk_v((69.7, -2.76, 0.25), -8, 15, 7.6, 70)),
         (304.6, fk_v((69.75, -2.76, 0.25), -6, 15, 7.2, 70)),
         (306.3, fk_v((74.3, -2.74, 0.45), 14, 12, 7.0, 85)),
         (307.9, fk_v((74.4, -2.77, 0.42), 18, 13, 6.6, 85)),
         (309.3, fk_v((72.05, -2.74, 0.3), 0, 14, 16.5, 60)),
         (312.0, fk_v((72.05, -2.74, 0.3), 0, 14, 15.8, 60))],
    fk2=[(289.25, fk_v((70.0, -2.95, 0.25), -4, 13, 7.0, 70)),
         (292.5, fk_v((68.9, -2.95, 0.3), -8, 12, 6.2, 70)),
         (294.8, fk_v((67.95, -2.95, 0.5), -6, 11, 6.4, 70)),
         (296.4, fk_v((68.0, -2.95, 0.95), -3, 9, 5.8, 70)),
         (298.0, fk_v((68.3, -2.95, 0.3), -3, 9, 4.6, 70)),
         (299.6, fk_v((69.55, -2.9, 0.3), -2, 13, 7.4, 70)),
         (304.6, fk_v((69.55, -2.9, 0.3), -2, 13, 7.2, 70)),
         (306.3, fk_v((74.4, -2.7, 0.45), 3, 10, 6.2, 70)),
         (307.9, fk_v((74.5, -2.7, 0.4), 3, 9, 5.4, 70)),
         (309.3, fk_v((72.05, -2.85, 0.3), 0, 12, 17.0, 60)),
         (312.0, fk_v((72.05, -2.85, 0.3), 0, 12, 16.4, 60))],
    fk3=[(289.25, fk_v((69.3, -2.75, 0.2), -30, 32, 15.0, 100)),
         (293.0, fk_v((68.4, -2.68, 0.2), -26, 31, 13.5, 100)),
         (296.4, fk_v(lambda t: fk_key_at("key_a", t, (-3.9, 0.08, 0.5)), -20, 30, 12.0, 115)),
         (298.4, fk_v((68.9, -2.66, 0.25), -16, 31, 12.0, 115)),
         (300.0, fk_v((69.6, -2.76, 0.25), -10, 33, 15.5, 95)),
         (304.6, fk_v((69.75, -2.76, 0.25), -8, 33, 15.0, 95)),
         (306.4, fk_v((74.9, -2.66, 0.35), 8, 30, 12.5, 115)),
         (307.9, fk_v((75.0, -2.66, 0.35), 12, 30, 12.0, 115)),
         (309.3, fk_v((72.05, -2.74, 0.3), 0, 33, 22.0, 80)),
         (312.0, fk_v((72.05, -2.74, 0.3), 0, 33, 21.4, 80))],
)
STOP = dict(fk1=0.45, fk2=40.0, fk3=40.0)     # fk1 wide open (the table is huge, so the f-number is far below a real lens's); the others everything sharp


def fk_eye_at(v, t):
    at = v["at"](t) if callable(v["at"]) else v["at"]
    vv = dict(v, at=at)
    return Vector(eye_of(vv)), Vector(at), math.log(v["mm"])


def fk_cam(ver, t):
    """Eye, look-at and lens at time t."""
    keys = KEYS[ver]
    if t < FK_IN:
        v = k_view(t)
        return Vector(eye_of(v)), Vector(v["at"]), v["mm"]
    if t < keys[0][0]:
        top = k_view(FK_IN)
        first = dict(keys[0][1], at=fk_eye_at(keys[0][1], t)[1][:])
        v = fall(top, first, (t - FK_IN) / (keys[0][0] - FK_IN))
        return Vector(eye_of(v)), Vector(v["at"]), v["mm"]
    if t >= keys[-1][0]:
        e, a, m = fk_eye_at(keys[-1][1], t)
        return e, a, math.exp(m)
    i = max(j for j in range(len(keys)) if keys[j][0] <= t)
    t0, t1 = keys[i][0], keys[i + 1][0]
    u = (t - t0) / (t1 - t0)
    pts = [fk_eye_at(keys[min(max(j, 0), len(keys) - 1)][1], t) for j in (i - 1, i, i + 1, i + 2)]
    if i == 0:
        pts[0] = tuple(2 * a - b for a, b in zip(pts[1], pts[2]))     # the first key leaves at the speed of the fall's end, about still

    def cr(a, b, c, d):
        return 0.5 * (2 * b + (c - a) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (3 * b - a - 3 * c + d) * u * u * u)
    e = cr(*(p[0] for p in pts))
    a = cr(*(p[1] for p in pts))
    m = cr(*(p[2] for p in pts))
    return e, a, math.exp(m)


def fk_focus(ver, t):
    if ver != "fk1":
        return None
    if t < 305.0:
        return fk_key_at("key_a", t, (-3.2, -0.1, 0.12))
    if t < 309.6:
        return fk_key_at("key_b", t, (2.0, -0.1, 0.12))
    return on_k(0.0, 0.0, 0.3)


# ---------------------------------------------------------------- fk2: the cut
def fk_section(rgb):
    """A cut face: matte, a paler shade of the part's colour, with thin 45 degree hatching a shade darker, as in a drawing's section."""
    m, nt, out = gk._mat("section")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Specular IOR Level"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type, wv.bands_direction, wv.wave_profile = "BANDS", "DIAGONAL", "SAW"
    wv.inputs["Scale"].default_value = 5.0
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation, gt.inputs[1].default_value = "GREATER_THAN", 0.86
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*rgb, 1)
    mix.inputs["B"].default_value = (*(c * 0.55 for c in rgb), 1)
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], gt.inputs[0])
    nt.links.new(gt.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def fk_cutaway(o, y_cut, pale):
    """Cut away everything of o in front of y_cut (towards the camera) and paint the new face a paler shade."""
    box = B.extrude([[(-30, -30), (-30, y_cut), (30, y_cut), (30, -30)]], 4.0, 0.0001, z=-2.0, name="cutter")
    B.boolean(o, box)
    names = [m.name if m else "" for m in o.data.materials]
    if pale.name not in names:
        o.data.materials.append(pale)
        names.append(pale.name)
    k = names.index(pale.name)
    for p in o.data.polygons:
        if p.normal.y < -0.99 and abs(p.center.y - y_cut) < 1e-3:
            p.material_index = k
            p.use_smooth = False


def fk_things(ver):
    """k_things, and in fk2 the cut-away of every part."""
    root = empty("table")
    root.location, root.scale = (*K_AT, 0), (K_S, K_S, K_S)

    def held(parts):
        e = empty("mover")
        e.parent = root
        for o in parts:
            o.parent = e
        return e
    red = P.gloss(P.RED, 0.18, 0.7)
    klein = P.gloss(P.KLEIN, 0.2, 0.7)
    blue_b = P.gloss((0.008, 0.03, 0.62), 0.2, 0.7)
    x_a, y = -4.3, -0.1

    def key_at(x):
        """B.key, made one solid and a hair slimmer. The curve's round bevel grows an outline by its 0.05 all round, and the pocket is only 0.035 larger than the
        blade, so shot k's seated key sits 0.015 into the pocket walls; here the blade is cut 0.02 inside its outline. Shot k also lowers the blade 0.008 so its top
        is not one plane with the bow's, which sinks it into whatever the key lies on; here blade and bow are joined instead."""
        blade = B.extrude([B.round_poly(B.key_blade(x, y, c=-0.02, start=0.14), 0.03)], 0.24, 0.05, z=0.0, name="blade", mat=red)
        ring, hole = [], []
        cx = x - 0.62
        for i in range(160):
            a_ = 2 * math.pi * i / 160
            ring.append((cx + 0.54 * math.cos(a_), y + 0.54 * math.sin(a_)))
            hole.append((cx + 0.28 * math.cos(-a_), y + 0.28 * math.sin(-a_)))
        bow = B.extrude([ring, hole], 0.24, 0.05, z=0.0, name="bow", mat=red)
        md = blade.modifiers.new("join", "BOOLEAN")
        md.operation, md.solver, md.object = "UNION", "EXACT", bow
        bpy.context.view_layer.objects.active = blade
        bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(bow)
        blade.data.materials.clear()
        blade.data.materials.append(red)
        for p in blade.data.polygons:
            p.material_index = 0
        return [blade]
    la = B.lock(-2.42, -0.02, 1.62, [(2, 0.06, 0.8), (3, 0.05, 2.1), (5, 0.022, 0.4)], B.round_poly(B.key_blade(x_a, y, c=0.035), 0.03), klein)
    ka = key_at(x_a)
    other = [(x, 2 * y + 0.3 - v) for x, v in B.key_blade(3.3, y, c=0.035, teeth=((0.34, 0.30), (0.78, 0.17)), blade=1.2, t=0.26)]
    lb = B.lock(4.3, -0.05, 1.3, [(2, 0.05, 2.4), (3, 0.075, 0.5), (4, 0.03, 1.2)], B.round_poly(other, 0.03), blue_b)
    kb = key_at(1.0)
    if ver == "fk2":
        pale = fk_section
        p_red, p_a, p_b = pale((0.95, 0.12, 0.08)), pale((0.008, 0.05, 0.53)), pale((0.02, 0.08, 0.78))
        fk_cutaway(la, FK_CUT["lock_a"], p_a)
        fk_cutaway(lb, FK_CUT["lock_b"], p_b)
        for o in ka + kb:
            fk_cutaway(o, FK_CUT_KEY, p_red)
    return dict(lock_a=held([la]), key_a=held(ka), lock_b=held([lb]), key_b=held(kb))


# ---------------------------------------------------------------- checks and the label track
def fk_meshes(things, dg):
    from mathutils.bvhtree import BVHTree
    out = {}
    for n, mover in things.items():
        vs, ps = [], []
        for o in mover.children:
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            base = len(vs)
            vs += [e.matrix_world @ v.co for v in me.vertices]
            ps += [tuple(base + i for i in p.vertices) for p in me.polygons]
            e.to_mesh_clear()
        out[n] = (vs, BVHTree.FromPolygons(vs, ps), ps)
    return out


def fk_clash(sc, things, step):
    pairs = [("key_a", "lock_a"), ("key_a", "lock_b"), ("key_a", "key_b"), ("key_b", "lock_b"), ("key_b", "lock_a"), ("lock_a", "lock_b")]
    worst = {p: (1e9, -1) for p in pairs}
    clashes, low, cam_near = [], (1e9, -1), (1e9, -1, "")
    frames = list(range(0, FRAMES, step))
    for f in frames:
        t = START + f / FPS
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        live = {n: t >= LAND_K[n] - FLY_K for n in things}
        w = fk_meshes(things, dg)
        eye = sc.camera.matrix_world.translation
        for n, (vs, tree, _) in w.items():
            if not live[n]:
                continue
            z = min(v.z for v in vs)
            if z < low[0]:
                low = (z, f)
            d = tree.find_nearest(eye)[3]
            if d is not None and d < cam_near[0]:
                cam_near = (d, f, n)
        for a, b in pairs:
            if not (live[a] and live[b]):
                continue
            (va, ta), (vb, tb) = w[a][:2], w[b][:2]
            hit = ta.overlap(tb)
            d = 0.0 if hit else min(min(tb.find_nearest(v)[3] for v in va), min(ta.find_nearest(v)[3] for v in vb))
            if hit:
                clashes.append((f, a, b, len(hit)))
                if os.environ.get("FORM_WHERE") and f % 100 == 0:
                    ca = [sum((va[i] for i in w[a][2][p_]), Vector()) / len(w[a][2][p_]) for p_, _ in hit]
                    lo = [min(c_[k] for c_ in ca) for k in range(3)]
                    hi = [max(c_[k] for c_ in ca) for k in range(3)]
                    loc = lambda q: tuple(round((q[k] - (K_AT[k] if k < 2 else 0)) / K_S, 3) for k in range(3))
                    print("CLASH_WHERE f%d %s x %s: %d pairs, %s faces in F3 box %s - %s" % (f, a, b, len(hit), a, loc(lo), loc(hi)))
            if d < worst[(a, b)][0]:
                worst[(a, b)] = (d, f)
    print("CLASH frames checked: %d (every %d of %d)" % (len(frames), step, FRAMES))
    print("CLASH clashes: %d" % len(clashes))
    runs = []
    for c in clashes:          # runs of frames per pair
        if runs and runs[-1][2] == c[1] and runs[-1][3] == c[2] and c[0] - runs[-1][1] <= step:
            runs[-1][1], runs[-1][4] = c[0], max(runs[-1][4], c[3])
        else:
            runs.append([c[0], c[0], c[1], c[2], c[3]])
    for a, b, x, y, n in runs:
        print("CLASH  %.3f-%.3fs (f%d-f%d) %s x %s: up to %d face pairs" % (START + a / FPS, START + b / FPS, a, b, x, y, n))
    for (a, b), (d, f) in worst.items():
        if f >= 0:
            print("CLASH closest %s - %s: %.4f table units (%.4f F3 units) at f%d %.2fs" % (a, b, d, d / K_S, f, START + f / FPS))
    print("CLASH lowest point of any solid: z %.4f at f%d (table top is 0)" % low)
    print("CLASH camera closest to a solid: %.3f table units (%s) at f%d %.2fs; lowest eye z checked below" % (cam_near[0], cam_near[2], cam_near[1], START + cam_near[1] / FPS))
    ez = min((fk_cam(VER[0], START + f / FPS)[0].z, f) for f in frames)
    print("CLASH lowest camera: z %.3f at f%d %.2fs" % (ez[0], ez[1], START + ez[1] / FPS))


def fk_track(sc, path):
    """Screen points of the label targets every other frame from 287.0 s: the lock's top, the key's bow, the tick, the wrong key's tip, the second lock."""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    pts = dict(lock=lambda t: on_k(-2.0, 0.9, 0.62), bow=lambda t: fk_key_at("key_a", t, (-4.92, -0.1, 0.24)),
               tick=lambda t: on_k(-1.45, -0.1, 0.62), cross=lambda t: fk_key_at("key_b", t, (2.75, -0.1, 0.24)),
               lockb=lambda t: on_k(4.3, 0.6, 0.62))
    out = {k: [] for k in pts}
    for f in range(72, 1572, 2):
        t = START + f / FPS
        sc.frame_set(f)
        for k, fn in pts.items():
            p = w2c(sc, sc.camera, Vector(fn(t)))
            out[k].append([round(p.x * 1920, 1), round((1 - p.y) * 1080, 1)])
    json.dump(out, open(path, "w"))
    print("TRACK_OK", path)


VER = [None]


def shot_fk(sc, sky, ver):
    VER[0] = ver
    c = lens(sc, STOP[ver])
    things = fk_things(ver)
    last_q[0] = None
    for f in range(FRAMES + 1):
        t = START + f / FPS
        for name, p in fk_place(t).items():
            things[name].location = p
            things[name].keyframe_insert("location", frame=f)
        eye, at, mm = fk_cam(ver, t)
        v = polar(tuple(eye), tuple(at), mm)
        foc = fk_focus(ver, t)
        if t < FK_IN:
            near = False
            foc = TOP_K["at"]
        if foc is not None:          # Blender focuses on a plane: put the focus point on the lens axis at the key's depth, not at its straight-line distance
            ax = (at - eye).normalized()
            foc = tuple(eye + ax * (Vector(foc) - eye).dot(ax))
        shoot(c, f, v, foc if foc is not None else tuple(at))
    if os.environ.get("FORM_CLASH"):
        fk_clash(sc, things, int(os.environ["FORM_CLASH"]))
        sys.exit(0)
    if os.environ.get("FORM_TRACK"):
        fk_track(sc, os.environ["FORM_TRACK"])
        sys.exit(0)

    def update(t):
        for name, o in things.items():
            for part in o.children:
                part.hide_render = t < LAND_K[name] - FLY_K
        x = smooth((t - K_FALL[0]) / K_FALL[1])          # the reflections' window: low while the camera is low, as in shot k
        if ver == "fk3":
            x *= 0.6
        sky(1 - x)
    return update


SHOTS["fk1"] = lambda sc, sky: shot_fk(sc, sky, "fk1")
SHOTS["fk2"] = lambda sc, sky: shot_fk(sc, sky, "fk2")
SHOTS["fk3"] = lambda sc, sky: shot_fk(sc, sky, "fk3")
