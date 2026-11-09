"""HKBU SCIE1007 coursework science video. A look test on shot k (S3, the lock and the key, 285.8-312.0 s): the same camera, the same beats and the same lock-and-key story,
made a different way so it stops reading as a toy. Kept in its own file and run inside bl_inserts.py (BL_EXTRA); bl_inserts.py, plate_kit.py and bl_shots.py are not touched.

Both versions share the new build and the new motion:
  build:  the key is a thin stamped blank (0.10 thick, was 0.24) with crisp chamfers, square-cut teeth and a keyway groove; the lock is half as thick (0.34, was 0.62) with
          small chamfers. The pocket is still cut from the key's own blade, so the key still fits only its own lock.
  motion: nothing is thrown and nothing bounces. Things glide in from beyond the frame and ease to a stop (quintic ease-out); a key is lifted, carried, and lowered into
          the pocket with an ease-in-out that ends at zero speed. The lock no longer jolts.
lk1, "machined object": satin powder-coat blue lock, red anodised aluminium key with a fine brushed grain, no clear coat.
lk2, "specimen under the lamp": the same table lit by one soft overhead lamp in a dim room; the lock is blue cast resin and the key red wax-like resin, both letting light into their edges.

Run:  BL_EXTRA=bl_look.py blender.exe -b -t 4 -P bl_inserts.py -- lk1 <out dir> [first] [last] [samples] [size] [step]
Check: LOOK_CLASH=<step> with the same command renders nothing and measures every <step> frames how close each moving thing comes to every other solid (BVH overlap and distance).
"""
META = {"lk1": (285.8, 1644, 0.2, 0.9), "lk2": (285.8, 1644, 0.2, 0.9)}

LK_KEY_H = 0.10                         # key thickness, F3 units (the old key 0.24)
LK_LOCK_H = 0.34                        # lock thickness (old 0.62)
LK_FLOOR = 0.22                         # floor of the pocket (old 0.36)
LK_SEAT = LK_FLOOR + 0.003              # a seated key rests 0.003 above the pocket floor, so contact is never read as overlap
LK_TOP = LK_LOCK_H + 0.003              # the wrong key rests on the top of the other lock
LK_FLY = 0.5                            # a glide in, seconds; it ends on the old landing times, and starts no earlier than the old throw did (304.55 s for the second lock)
LK_LOWER_A, LK_LOWER_B = 0.6, 0.4       # how long each key takes to go down into place, ending on the old hit times
LK_FROM = dict(FROM_K, key_a=(-0.6, -2.6))     # the first key now slides in low, so it comes from the lower left; from the old lower right it would cut through the first lock


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 5


def lk_slab(polys, h, cham, z=0.0, name="slab", mat=None):
    """Like bl_shots.extrude, but with a single flat chamfer instead of a rounded one: a machined edge, not a moulded one."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions, cu.fill_mode = "2D", "BOTH"
    cu.extrude, cu.bevel_depth, cu.bevel_resolution = max(h / 2 - cham, 1e-4), cham, 0
    for poly in polys:
        s = cu.splines.new("POLY")
        s.points.add(len(poly) - 1)
        for p, q in zip(s.points, poly):
            p.co = (q[0], q[1], 0, 1)
        s.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.view_layer.objects.active
    o.location.z = z + h / 2
    bpy.ops.object.transform_apply(location=True)
    if mat:
        o.data.materials.append(mat)
    return o


def lk_union(a, b):
    md = a.modifiers.new("join", "BOOLEAN")
    md.operation, md.solver, md.object = "UNION", "EXACT", b
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(b)


def lk_flat(o):
    """Flat shading on the faces that are flat, smooth only across the small chamfers."""
    for p in o.data.polygons:
        p.use_smooth = False


def lk_key(x0, y, mat):
    """A thin key blank lying flat, bow on the left, blade from x0: one solid, square teeth, a groove along the blade, a ring hole near the bow's end."""
    blade = lk_slab([B.round_poly(B.key_blade(x0, y, start=0.14), 0.008)], LK_KEY_H, 0.014, name="blade")
    ring, hole = [], []
    cx = x0 - 0.6
    for i in range(160):
        a = 2 * math.pi * i / 160
        ring.append((cx + 0.52 * math.cos(a), y + 0.52 * math.sin(a)))
        hole.append((cx - 0.2 + 0.13 * math.cos(-a), y + 0.13 * math.sin(-a)))
    bow = lk_slab([ring, hole], LK_KEY_H, 0.014, name="bow")
    lk_union(blade, bow)
    groove = lk_slab([[(x0 + 0.02, y + 0.035), (x0 + 1.55, y + 0.035), (x0 + 1.55, y + 0.075), (x0 + 0.02, y + 0.075)]], 0.06, 0.0001, z=LK_KEY_H - 0.025, name="groove")
    B.boolean(blade, groove)
    lk_flat(blade)
    blade.data.materials.clear()
    blade.data.materials.append(mat)
    for p in blade.data.polygons:
        p.material_index = 0
    return blade


def lk_lock(cx, cy, rad, bumps, cutter, mat):
    o = lk_slab([B.blob(cx, cy, rad, bumps)], LK_LOCK_H, 0.02, name="lock")
    c = lk_slab([cutter], 0.6, 0.0001, z=LK_FLOOR, name="cut")
    B.boolean(o, c)
    b = o.modifiers.new("bev", "BEVEL")
    b.limit_method, b.angle_limit, b.width, b.segments = "ANGLE", math.radians(40), 0.008, 2
    lk_flat(o)
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- materials
def lk_grain(nt, b, scale, strength, along_x=True):
    """A very fine grain in the bump: brushed streaks along x, or an even satin tooth."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale * 0.04, scale, scale) if along_x else (scale, scale, scale)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Detail"].default_value = 4
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    nt.links.new(mp.outputs[0], nz.inputs[0])
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])


def lk_mat(name, rgb, rough, metal=0.0, spec=0.35, sss=0.0, radius=(0.1, 0.1, 0.1), sss_scale=0.1, grain=None):
    m, nt, out = gk._mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = 0.0
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = radius
        b.inputs["Subsurface Scale"].default_value = sss_scale
    if grain:
        lk_grain(nt, b, *grain)
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def lk_mats(ver):
    if ver == "lk1":
        return dict(key=lk_mat("key_anod", P.RED, 0.36, metal=0.55, spec=0.5, grain=(140.0, 0.08, True)),
                    lock_a=lk_mat("lock_satin", P.KLEIN, 0.55, spec=0.3, grain=(260.0, 0.03, False)),
                    lock_b=lk_mat("lock_satin_b", (0.008, 0.03, 0.62), 0.55, spec=0.3, grain=(260.0, 0.03, False)))
    return dict(key=lk_mat("key_resin", (0.75, 0.02, 0.012), 0.42, spec=0.4, sss=0.5, radius=(1.0, 0.15, 0.1), sss_scale=0.06),
                lock_a=lk_mat("lock_resin", (0.0, 0.03, 0.5), 0.4, spec=0.4, sss=0.6, radius=(0.2, 0.35, 1.0), sss_scale=0.05),
                lock_b=lk_mat("lock_resin_b", (0.005, 0.045, 0.68), 0.4, spec=0.4, sss=0.6, radius=(0.2, 0.35, 1.0), sss_scale=0.05))


def lk_lamp(sc):
    """lk2: dim the room and the sun, hang one soft lamp over the two locks, and add a low light from behind that draws the chamfers."""
    nt = sc.world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND" and n.inputs[1].is_linked)
    src = bg.inputs[1].links[0].from_socket
    dim = nt.nodes.new("ShaderNodeMath")
    dim.operation, dim.inputs[1].default_value = "MULTIPLY", 0.22
    nt.links.new(src, dim.inputs[0])
    nt.links.new(dim.outputs[0], bg.inputs[1])
    bpy.data.objects["sun"].data.energy = P.SUN * 0.12
    d = bpy.data.lights.new("lamp", "AREA")
    d.shape, d.size, d.size_y = "ELLIPSE", 10.0, 6.0
    d.energy, d.spread = 130.0, math.radians(34)
    o = bpy.data.objects.new("lamp", d)
    sc.collection.objects.link(o)
    o.location = (72.2, -2.7, 14.0)
    o.visible_glossy = False                                          # the top camera looks straight down the lamp's axis: seen in the flat tops it washes them out
    r = bpy.data.lights.new("rim", "SUN")
    r.energy, r.angle = 0.9, math.radians(4)
    r.use_shadow = False                                              # it only draws the edges; its long shadows would read as a second object
    ro = bpy.data.objects.new("rim", r)
    sc.collection.objects.link(ro)
    ro.rotation_euler = (math.radians(-74), 0, math.radians(165))     # low, from behind the locks and a little right


# ---------------------------------------------------------------- the four movers and where they go
def lk_things(ver):
    root = empty("table")
    root.location, root.scale = (*K_AT, 0), (K_S, K_S, K_S)
    mats = lk_mats(ver)

    def held(o):
        e = empty("mover")
        e.parent = root
        o.parent = e
        return e
    x_a, y = -4.3, -0.1
    lock_a = held(lk_lock(-2.42, -0.02, 1.62, [(2, 0.06, 0.8), (3, 0.05, 2.1), (5, 0.022, 0.4)], B.round_poly(B.key_blade(x_a, y, c=0.035), 0.01), mats["lock_a"]))
    key_a = held(lk_key(x_a, y, mats["key"]))
    other = [(x, 2 * y + 0.3 - v) for x, v in B.key_blade(3.3, y, c=0.035, teeth=((0.34, 0.30), (0.78, 0.17)), blade=1.2, t=0.26)]
    lock_b = held(lk_lock(4.3, -0.05, 1.3, [(2, 0.05, 2.4), (3, 0.075, 0.5), (4, 0.03, 1.2)], B.round_poly(other, 0.01), mats["lock_b"]))
    key_b = held(lk_key(1.0, y, mats["key"]))
    return dict(lock_a=lock_a, key_a=key_a, lock_b=lock_b, key_b=key_b)


def lk_glide(t, name):
    """Offset from where a thing comes to rest: it slides in from the same side as the old throw, a little above the table, and eases to a stop with no bounce."""
    x = ease_out((t - LAND_K[name] + LK_FLY) / LK_FLY)
    dx, dy = LK_FROM[name]
    return dx * (1 - x) / K_S, dy * (1 - x) / K_S, 0.25 * (1 - x) ** 2


def lk_carried(t, rise, hit, rest, lower):
    """A key lifted, carried at CARRY and lowered: up with smooth(), down with smooth() over the last `lower` seconds, so it arrives at zero speed."""
    if t < hit - lower:
        return CARRY * smooth((t - rise[0]) / rise[1])
    return CARRY + (rest - CARRY) * smooth((t - hit + lower) / lower)


def lk_place(t):
    over_a, over_b = smooth((t - OVER_A[0]) / OVER_A[1]), smooth((t - OVER_B[0]) / OVER_B[1])
    at = {}
    for name, x, y_at, z in (("lock_a", 0.0, 0.0, 0.0),
                             ("key_a", -GAP_A * (1 - over_a), 0.0, lk_carried(t, RISE_A, HIT_A, LK_SEAT, LK_LOWER_A)),
                             ("lock_b", 0.0, 0.0, 0.0),
                             ("key_b", BACK_B + (OVER_LOCK_B[0] - BACK_B) * over_b, OVER_LOCK_B[1] * over_b, lk_carried(t, RISE_B, HIT_B, LK_TOP, LK_LOWER_B))):
        dx, dy, h = lk_glide(t, name)
        if name == "key_a" and t > K_LEAVE[0]:
            u = smooth((t - K_LEAVE[0]) / K_LEAVE[1])         # straight up out of the pocket, then off the view: no longer a fling
            dx, h = -3.0 * u / K_S, h + 40.0 * u / K_S
        at[name] = (x + dx, y_at + dy, h + z)
    return at


def lk_clash(sc, things, step):
    """Measure, frame by frame, the gap between every pair of solids, and between each solid and the table. Nothing is rendered."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    solids = {n: o.children[0] for n, o in things.items()}
    pairs = [("key_a", "lock_a"), ("key_a", "lock_b"), ("key_a", "key_b"), ("key_b", "lock_b"), ("key_b", "lock_a"), ("lock_a", "lock_b")]
    worst = {p: (1e9, -1) for p in pairs}
    clashes, floor_low = [], (1e9, -1)
    for f in range(0, FRAMES, step):
        t = START + f / FPS
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        live = {n: t >= LAND_K[n] - LK_FLY for n in solids}
        world = {}
        for n, o in solids.items():
            e = o.evaluated_get(dg)
            m = e.matrix_world
            me = e.to_mesh()
            vs = [m @ v.co for v in me.vertices]
            ps = [tuple(p.vertices) for p in me.polygons]
            e.to_mesh_clear()
            world[n] = (vs, BVHTree.FromPolygons(vs, ps))
            if live[n]:
                zmin = min(v.z for v in vs)
                if zmin < floor_low[0]:
                    floor_low = (zmin, f)
        for a, b in pairs:
            if not (live[a] and live[b]):
                continue
            (va, ta), (vb, tb) = world[a], world[b]
            hit = ta.overlap(tb)
            d = min(min(tb.find_nearest(v)[3] for v in va), min(ta.find_nearest(v)[3] for v in vb))
            if hit:
                clashes.append((f, a, b, len(hit)))
                d = 0.0
            if d < worst[(a, b)][0]:
                worst[(a, b)] = (d, f)
        if f % 120 == 0:
            print("CLASH f%d t%.2f" % (f, t), flush=True)
    print("CLASH frames checked: %d (every %d of %d)" % (len(range(0, FRAMES, step)), step, FRAMES))
    print("CLASH clashes: %d" % len(clashes))
    for c in clashes[:20]:
        print("  f%d %.2fs %s x %s: %d face pairs" % (c[0], START + c[0] / FPS, c[1], c[2], c[3]))
    for (a, b), (d, f) in worst.items():
        if f >= 0:
            print("CLASH closest %s - %s: %.4f table units (%.4f F3 units) at f%d %.2fs" % (a, b, d, d / K_S, f, START + f / FPS))
    print("CLASH lowest point of any solid: z %.4f at f%d (table top is 0)" % floor_low)


def shot_lk(sc, sky, ver):
    c = lens(sc, 2.8)
    things = lk_things(ver)
    if ver == "lk2":
        lk_lamp(sc)
    last_q[0] = None
    for f in range(FRAMES + 1):
        t = START + f / FPS
        for name, p in lk_place(t).items():
            things[name].location = p
            things[name].keyframe_insert("location", frame=f)
        near = K_FALL[0] + K_FALL[1] / 2 < t < K_CLIMB[0] + K_CLIMB[1] / 2 or K_FALL2[0] + K_FALL2[1] / 2 < t < K_CLIMB2[0] + K_CLIMB2[1] / 2 or t > K_DIVE[0] + K_DIVE[1] / 2
        shoot(c, f, k_view(t), k_focus(t) if near else TOP_K["at"])
    if os.environ.get("LOOK_CLASH"):
        lk_clash(sc, things, int(os.environ["LOOK_CLASH"]))
        sys.exit(0)

    def update(t):
        for name, o in things.items():
            for part in o.children:
                part.hide_render = t < LAND_K[name] - LK_FLY
        if t >= K_DIVE[0]:
            sky(1 - smooth((t - K_DIVE[0]) / K_DIVE[1]))
        elif t < 300:
            sky(1 - smooth((t - K_FALL[0]) / K_FALL[1]) + smooth((t - K_CLIMB[0]) / K_CLIMB[1]))
        else:
            sky(1 - smooth((t - K_FALL2[0]) / K_FALL2[1]) + smooth((t - K_CLIMB2[0]) / K_CLIMB2[1]))
    return update


SHOTS["lk1"] = lambda sc, sky: shot_lk(sc, sky, "lk1")
SHOTS["lk2"] = lambda sc, sky: shot_lk(sc, sky, "lk2")
