"""S1 v2 / 1-08 + 1-09 Blender plates (no text; labels are laid on top in Remotion).

  blender -b --factory-startup -P road3d.py -- --scene glass|vessel|gates|vials --state full|lit4 --out X.png [--samples 128] [--pct 100]

glass  : one long glass tube, six chambers; red beads suspended, failed beads settled grey; red thread = progress.
vessel : glossy red vessel snaking across a black table, six blue valve rings; it narrows at every valve, dead-end stubs = dropouts.
gates  : six light-frame gates (Flavin-like) in 3/4 perspective on a black mirror floor; red spheres thin out gate by gate.
vials  : ten glass vials; nine clouded grey, one vermilion (1-08, "one in ten").
--state lit4 : stations 1-4 lit, 5-6 dim (re-use proof).
"""
import bpy, sys, math, random, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--scene", default="glass")
ap.add_argument("--state", default="full")
ap.add_argument("--out", default="out.png")
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--anchors", default="")
ap.add_argument("--fstop", type=float, default=0.0)
ap.add_argument("--mask", default="")
A = ap.parse_args(argv)
LIT = 6 if A.state == "full" else 4

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn = bpy.context.scene
col = scn.collection


def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


VERM, BLUE, KLEIN, BONE, CYAN = lin("#FF3B1F"), lin("#1F3BFF"), lin("#002FA7"), lin("#EDEBE4"), lin("#29F0FF")


def mat(name, color=(0.8, 0.8, 0.8, 1), rough=0.3, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = estr
    return m


def emis(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = color; e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m


def put(obj, m):
    obj.data.materials.clear(); obj.data.materials.append(m)
    for p in obj.data.polygons: p.use_smooth = True
    return obj


def cyl(r, depth, loc, rot=(0, math.pi / 2, 0), verts=96, m=None, name="cyl"):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    if m: put(o, m)
    return o


def sphere(r, loc, m, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object; put(o, m); return o


def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = size; put(o, m); return o


def area(name, loc, target, size, power, color=(1, 1, 1, 1), shape="RECTANGLE", sy=None):
    d = bpy.data.lights.new(name, "AREA"); d.energy = power; d.color = color[:3]; d.shape = shape
    d.size = size; d.size_y = sy or size
    o = bpy.data.objects.new(name, d); col.objects.link(o); o.location = loc; o.visible_camera = False
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def point(loc, power, color, r=0.05):
    d = bpy.data.lights.new("pt", "POINT"); d.energy = power; d.color = color[:3]; d.shadow_soft_size = r
    o = bpy.data.objects.new("pt", d); col.objects.link(o); o.location = loc; o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False; return o


def camera(loc, target, lens=35, shift_y=0.0, focus=None):
    d = bpy.data.cameras.new("cam"); d.lens = lens; d.shift_y = shift_y
    if A.fstop > 0:
        d.dof.use_dof = True; d.dof.aperture_fstop = A.fstop
        d.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length
    o = bpy.data.objects.new("cam", d); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scn.camera = o; return o


def floor(rough=0.18, z=0.0, size=200, color=(0.004, 0.004, 0.004, 1)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    return put(bpy.context.object, mat("floor", color, rough=rough, coat=0.0))


def curve_tube(pts, radii, m, name="tube", res=6, bev=24):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 1.0; cu.bevel_resolution = bev; cu.use_fill_caps = True; cu.resolution_u = res
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for p, (x, y, z), r in zip(sp.points, pts, radii): p.co = (x, y, z, 1); p.radius = r
    sp.use_endpoint_u = True; sp.order_u = 4
    o = bpy.data.objects.new(name, cu); col.objects.link(o); cu.materials.append(m)
    return o


world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1)
random.seed(7)
ANCH = []

glass = mat("glass", (0.92, 0.95, 1.0, 1), rough=0.02, trans=1.0, ior=1.47)
red = mat("red", VERM, rough=0.12, coat=1.0)
grey = mat("grey", (0.09, 0.09, 0.09, 1), rough=0.55)
bone = mat("bone", BONE, rough=0.4)

# ====================================================================== GLASS TUBE
if A.scene == "glass":
    L, R = 15.0, 0.8; n = 6; cl = L / n
    tube = cyl(R, L, (0, 0, 1.2), m=glass, name="tube")
    sm = tube.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.035
    for i in range(n + 1):  # septa (end caps included), slightly frosted
        x = -L / 2 + i * cl
        cyl(R - 0.01, 0.05, (x, 0, 1.2), m=mat("sept", (0.9, 0.93, 1, 1), rough=0.12, trans=1.0), name="sep")
        cyl(R + 0.035, 0.07, (x, 0, 1.2), m=mat("collar", (0.6, 0.6, 0.6, 1), rough=0.25, metal=1.0), name="col")
    counts = [34, 17, 9, 5, 2, 1]
    for i in range(n):
        x0 = -L / 2 + i * cl
        on = i < LIT
        k = counts[i] if on else 0
        for _ in range(k):  # survivors: suspended red beads
            a, rr = random.random() * 6.283, math.sqrt(random.random()) * (R - 0.16)
            sphere(0.085 + 0.03 * random.random(), (x0 + 0.25 + random.random() * (cl - 0.5), rr * math.cos(a), 1.2 + rr * math.sin(a)), red)
        drop = (counts[i - 1] - counts[i]) if (i > 0 and on) else 0
        for j in range(drop):  # failures: grey, settled on the floor of the chamber
            sphere(0.08, (x0 + 0.3 + random.random() * (cl - 0.6), (random.random() - 0.5) * 0.55, 1.2 - R + 0.13 + 0.02 * random.random()), grey)
        ANCH.append((x0 + cl / 2, 0, 1.2 + R))
        if on:
            point((x0 + cl / 2, 0, 1.2), 22, BONE, 0.05)
    # red thread = progress along the axis
    end = -L / 2 + LIT * cl
    cyl(0.018, end + L / 2, ((end - L / 2) / 2, 0, 1.2), m=emis("thread", VERM, 6), name="thread", verts=16)
    floor(rough=0.12)
    area("key", (0, -6, 9), (0, 0, 1), 6, 900, BONE, sy=3)
    area("rimB", (0, 7, 3.5), (0, 0, 1.2), 20, 2200, BLUE, sy=2)
    area("rimL", (-12, 2, 3), (0, 0, 1.2), 4, 600, BLUE)
    camera((-1.6, -20.5, 4.6), (0.3, 0, 1.6), lens=44)

# ====================================================================== VESSEL + VALVES
elif A.scene == "vessel":
    # path across a black table (XY plane), S-curve
    P = [(-11, -2.4, 0), (-8, -3.0, 0), (-5, -0.6, 0), (-2.5, 1.6, 0), (0.5, 0.4, 0), (3, -1.8, 0), (6, -1.0, 0), (8.5, 1.4, 0), (11, 1.8, 0), (13, 1.2, 0)]
    cu = bpy.data.curves.new("path", "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("NURBS"); sp.points.add(len(P) - 1)
    for p, c in zip(sp.points, P): p.co = (*c, 1)
    sp.use_endpoint_u = True; sp.order_u = 4; cu.resolution_u = 64
    po = bpy.data.objects.new("path", cu); col.objects.link(po)
    dg = bpy.context.evaluated_depsgraph_get()
    me = po.evaluated_get(dg).to_mesh()
    vs = [v.co.copy() for v in me.vertices]
    po.evaluated_get(dg).to_mesh_clear(); bpy.data.objects.remove(po)
    # arc length param
    cum = [0.0]
    for a, b in zip(vs, vs[1:]): cum.append(cum[-1] + (b - a).length)
    T = cum[-1]

    def at(s):
        s = max(0, min(T, s))
        for i in range(1, len(cum)):
            if cum[i] >= s:
                u = (s - cum[i - 1]) / max(1e-6, cum[i] - cum[i - 1])
                p = vs[i - 1].lerp(vs[i], u); t = (vs[i] - vs[i - 1]).normalized(); return p, t
        return vs[-1], (vs[-1] - vs[-2]).normalized()

    st = [T * f for f in (0.12, 0.27, 0.42, 0.57, 0.72, 0.87)]
    rads = [0.85, 0.62, 0.45, 0.32, 0.22, 0.14, 0.08]

    def rad_at(s):
        k = sum(1 for x in st if s > x)
        r0 = rads[k]
        # smooth step just after each valve
        for x in st:
            if 0 < s - x < 0.6:
                kk = st.index(x); u = (s - x) / 0.6; u = u * u * (3 - 2 * u)
                return rads[kk] + (rads[kk + 1] - rads[kk]) * u
        return r0
    Z = 0.75
    cut = st[LIT - 1] + 0.9 if LIT < 6 else T + 1
    live, dead = [], []
    N = 260
    for i in range(N + 1):
        s = T * i / N; p, _ = at(s)
        (live if s <= cut else dead).append(((p.x, p.y, Z), rad_at(s)))
    if dead: dead.insert(0, live[-1])
    curve_tube([q for q, _ in live], [r for _, r in live], red, "live")
    ghost = mat("ghost", (0.01, 0.015, 0.12, 1), rough=0.2, coat=1.0)
    if dead: curve_tube([q for q, _ in dead], [r for _, r in dead], ghost, "dead")
    ring_on = mat("ringon", BONE, rough=0.25, coat=1.0)
    ring_off = mat("ringoff", (0.02, 0.02, 0.025, 1), rough=0.3)
    stub = mat("stub", (0.035, 0.012, 0.02, 1), rough=0.25, coat=1.0)
    rnd = random.Random(3)
    for k, s in enumerate(st):
        p, t = at(s)
        ANCH.append((p.x, p.y, Z))
        r = rads[k] + 0.06
        bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.08, minor_radius=0.12, location=(p.x, p.y, Z),
                                         major_segments=96, minor_segments=24)
        o = bpy.context.object
        o.rotation_euler = t.to_track_quat("Z", "Y").to_euler()
        put(o, ring_on if k < LIT else ring_off)
        if True: continue  # stubs dropped: narrowing alone carries attrition
        # dead-end stubs: dropouts peel off just before each valve and stop
        nst = [3, 3, 2, 2, 1, 1][k]
        for j in range(nst):
            s0 = s - 0.4 - j * 0.55
            q, tq = at(s0)
            nrm = Vector((-tq.y, tq.x, 0)) * (1 if (j + k) % 2 == 0 else -1)
            ln = 1.3 + rnd.random() * 0.9
            d = (tq * 0.35 + nrm).normalized(); d2 = (-tq * 0.6 + nrm).normalized()
            rr = rad_at(s0) * 0.42
            pts = [(q.x, q.y, Z * 0.8), (q.x + d.x * ln * 0.45, q.y + d.y * ln * 0.45, rr), (q.x + d.x * ln * 0.8 + d2.x * ln * 0.25, q.y + d.y * ln * 0.8 + d2.y * ln * 0.25, rr),
                   (q.x + d.x * ln * 0.9 + d2.x * ln * 0.55, q.y + d.y * ln * 0.9 + d2.y * ln * 0.55, rr)]
            curve_tube(pts, [rr * 1.25, rr * 1.0, rr * 1.0, rr * 1.0], stub, "stub")
            sphere(rr * 1.0, pts[-1], stub)
    floor(rough=0.55, color=lin("#0A1AFF") if A.state != "blk" else (0.004, 0.004, 0.004, 1))
    area("key", (-6, -8, 16), (0, 0, 0), 9, 2600, BONE, sy=6)
    area("fill", (10, 6, 10), (0, 0, 0), 8, 500, BONE)
    camera((0.9, -4.5, 26), (0.9, -0.1, 0), lens=42)

# ====================================================================== GATES
elif A.scene == "gates":
    n = 6; gap = 3.4
    dirv = Vector((1, 0, 0))
    gate_on = emis("gon", BONE, 9)
    gate_last = emis("glast", VERM, 12)
    gate_off = mat("goff", (0.02, 0.02, 0.022, 1), rough=0.35, metal=0.6)
    H, Wd, th = 3.2, 2.1, 0.07
    for i in range(n):
        x = i * gap
        ANCH.append((x, 0, H))
        m = (gate_last if i == n - 1 else gate_on) if i < LIT else gate_off
        box((th, th, H), (x, -Wd / 2, H / 2), m); box((th, th, H), (x, Wd / 2, H / 2), m)
        box((th, Wd + th, th), (x, 0, H), m)
        if i < LIT:  # soft spill on the floor from each lit gate
            d = bpy.data.lights.new("g", "AREA"); d.shape = "RECTANGLE"; d.size = Wd; d.size_y = 0.1
            d.energy = 120; d.color = (VERM if i == n - 1 else BONE)[:3]
            o = bpy.data.objects.new("g", d); col.objects.link(o); o.location = (x, 0, H - 0.05); o.rotation_euler = (0, 0, math.pi / 2)
    # the road: a red line on the floor
    x_end = (LIT - 1) * gap + (gap * 0.9 if LIT < n else 2.5)
    box((x_end + 6, 0.06, 0.006), ((x_end - 6) / 2, 0, 0.003), emis("road", VERM, 5))
    if LIT < n:
        box(((n - 1) * gap + 2.5 - x_end, 0.05, 0.004), ((x_end + (n - 1) * gap + 2.5) / 2, 0, 0.002), mat("roadoff", (0.05, 0.05, 0.05, 1), rough=0.5))
    # candidates: crowd before gate 1 and thinning through each gate; failures grey, pushed aside
    seg = [38, 17, 9, 5, 3, 2, 1]
    rnd = random.Random(11)
    for k, c in enumerate(seg):
        if k > LIT: break
        x0 = (k - 1) * gap if k > 0 else -6
        x1 = k * gap if k < n else k * gap - gap + 2.5
        if k == LIT and LIT < n: c = 1; x0, x1 = (k - 1) * gap + 0.4, (k - 1) * gap + 1.2
        for _ in range(c):
            sphere(0.16, (x0 + 0.35 + rnd.random() * (x1 - x0 - 0.7), (rnd.random() - 0.5) * (1.4 if k == 0 else 0.9) * (1 if k else 1.3), 0.16), red)
        if 0 < k <= min(LIT, n - 1) or (k == n and LIT == n):
            for _ in range(seg[k - 1] - seg[k]):  # dropped at gate k
                sphere(0.15, ((k - 1) * gap - 0.4 - rnd.random() * 0.8, (1 if rnd.random() < 0.5 else -1) * (Wd / 2 + 0.35 + rnd.random() * 0.9), 0.15), grey)
    floor(rough=0.08)
    area("key", (4, -8, 10), (7, 0, 0), 8, 500, BONE, sy=3)
    cdir = Vector((12.6, 15.6, 0)).normalized()
    wl = Vector((-4, -15, 0)) + cdir * 60
    bpy.ops.mesh.primitive_plane_add(size=1, location=(wl.x, wl.y, 4), rotation=(math.pi / 2, 0, math.atan2(cdir.y, cdir.x) - math.pi / 2))
    wall = bpy.context.object; wall.scale = (400, 9, 1); put(wall, emis("wall", BLUE, 0.9))
    camera((-4.0, -15.0, 3.6), (8.6, 0.6, 1.1), lens=28)

# ====================================================================== VIALS (1-08)
elif A.scene == "vials":
    cloud = mat("cloud", (0.5, 0.5, 0.52, 1), rough=0.35, trans=0.85, ior=1.33)
    liquid = mat("liq", VERM, rough=0.05, trans=0.0, coat=1.0, emit=VERM, estr=1.4)
    win = 6
    for i in range(10):
        x = (i - 4.5) * 0.92
        r, h = 0.3, 2.4
        v = cyl(r, h, (x, 0, h / 2), rot=(0, 0, 0), m=glass, name="vial")
        sm = v.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.025
        # rounded bottom handled by a sphere
        fill = 0.55 + 0.25 * ((i * 37) % 10) / 10
        lv = liquid if i == win else cloud
        cyl(r - 0.035, h * fill, (x, 0, h * fill / 2 + 0.03), rot=(0, 0, 0), m=lv, name="liq")
    point(((win - 4.5) * 0.95, -0.2, 0.9), 40, VERM, 0.1)
    floor(rough=0.08)
    area("key", (0, -6, 8), (0, 0, 1), 5, 600, BONE, sy=2)
    area("rimB", (0, 6, 3), (0, 0, 1.2), 20, 2500, BLUE, sy=3)
    camera((0, -15.5, 1.75), (0, 0, 1.3), lens=50)

# ====================================================================== NEON METRO (1-09)
elif A.scene == "neon":
    zt, zb = 2.4, -0.5
    path = [(-10.5, zt), (-2.2, zt), (0.7, zb), (10.5, zb)]
    stx = [(-8.3, zt), (-6.0, zt), (-3.7, zt), (2.2, zb), (5.0, zb), (7.9, zb)]
    wallm = mat("wall", (0.012, 0.012, 0.013, 1), rough=0.75)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.35, 0), rotation=(math.pi / 2, 0, 0))
    w = bpy.context.object; w.scale = (300, 60, 1); put(w, wallm)
    xcut = 99 if LIT >= 6 else stx[LIT - 1][0] + 0.9

    def poly_tube(pts, r, m, name):
        cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 10; cu.use_fill_caps = True
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for p_, c in zip(sp.points, pts): p_.co = (*c, 1)
        o = bpy.data.objects.new(name, cu); col.objects.link(o); cu.materials.append(m); return o

    dense = []
    for a, b in zip(path, path[1:]):
        for t in range(60):
            u = t / 60; dense.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    dense.append(path[-1])
    live = [(x, -0.05, z) for x, z in dense if x <= xcut]
    dead = [(x, -0.05, z) for x, z in dense if x >= xcut - 0.05]
    poly_tube(live, 0.075, emis("neon", VERM, 18), "live")
    poly_tube(live, 0.095, mat("jacket", (1, 1, 1, 1), rough=0.05, trans=1.0, ior=1.45), "jk")
    if len(dead) > 1:
        poly_tube(dead, 0.085, mat("unlit", (0.5, 0.5, 0.52, 1), rough=0.25, trans=0.6, ior=1.45), "dead")
        poly_tube(dead, 0.04, mat("wire", (0.05, 0.02, 0.02, 1), rough=0.4), "core")
    steel = mat("steel", (0.6, 0.6, 0.6, 1), rough=0.2, metal=1.0)
    for x, z in dense[::18]:
        cyl(0.025, 0.4, (x, 0.15, z), rot=(math.pi / 2, 0, 0), m=steel, verts=12)
    for i, (x, z) in enumerate(stx):
        on = i < LIT
        ANCH.append((x, -0.1, z))
        rr_ = 0.36 if i == 5 else 0.28
        cyl(rr_, 0.06, (x, 0.28, z), rot=(math.pi / 2, 0, 0), m=(emis("st%d" % i, BONE, 2.2) if on else mat("stoff", (0.09, 0.09, 0.09, 1), rough=0.5)), verts=64)
    ledge_z = -2.4
    box((22, 0.5, 0.06), (0.5, 0.05, ledge_z), mat("ledge", (0.02, 0.02, 0.02, 1), rough=0.25))
    cnt = [34, 17, 9, 5, 2, 1]
    for i in range(1, LIT):
        k = cnt[i - 1] - cnt[i]
        for j in range(k):
            sphere(0.13, (stx[i][0] - (min(k, 6) - 1) * 0.14 + (j % 6) * 0.28 + (j // 6 % 2) * 0.14, -0.05, ledge_z + 0.16 + (j // 6) * 0.25), grey)
    for j in range(34):
        sphere(0.13, (-9.4 + (j % 6) * 0.28 + (j // 6 % 2) * 0.14, -0.05, ledge_z + 0.16 + (j // 6) * 0.25), red)
    area("key", (-4, -9, 7), (0, 0, -0.8), 8, 900, BONE, sy=3)
    area("rimB", (2, -5, 12), (0, 0.3, 1.0), 26, 1400, BLUE, sy=3)
    area("rimB2", (-16, -3, -1), (0, 0, 0.5), 6, 500, BLUE)
    camera((-0.6, -20.0, 0.9), (-0.6, 0, 0.35), lens=36, focus=(0, 0, 0.5))

# ====================================================================== TYPOGRAPHIC ROAD (1-09)
elif A.scene == "typeroad":
    font = bpy.data.fonts.load("C:/Windows/Fonts/seguibl.ttf")
    words = ["TARGET", "HIT", "IMPROVE", "CELLS \u2192 ANIMALS", "TRIALS I \u00b7 II \u00b7 III", "APPROVAL"]
    gap = 6.0; road_w = 7.0
    lit_m = mat("paint", BONE, rough=0.35)
    off_m = mat("paintoff", (0.07, 0.07, 0.075, 1), rough=0.4)
    for i, wd in enumerate(words):
        y = 2 + i * gap
        bpy.ops.object.text_add(location=(0, y, 0.0))
        t = bpy.context.object; t.data.body = wd; t.data.font = font; t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
        t.data.size = 1.25 if len(wd) > 8 else 1.9; t.data.extrude = 0.025; t.data.bevel_depth = 0.004
        t.scale = (1.0, 2.3, 1.0); t.location.z = 0.026
        t.data.materials.append(lit_m if i < LIT else off_m)
        bpy.context.view_layer.update()
        ANCH.append((-(t.dimensions.x / 2) - 0.4, y, 0.0))
    edge = mat("edge", BONE, rough=0.4)
    for sx_ in (-road_w / 2, road_w / 2):
        box((0.08, 70, 0.004), (sx_, 28, 0.002), edge)
    yc = 99 if LIT >= 6 else 2 + (LIT - 1) * gap + gap * 0.55
    redm = emis("road", VERM, 4); offm = mat("roadoff", (0.06, 0.06, 0.06, 1), rough=0.5)
    for i in range(7):
        y0 = -8 if i == 0 else 2 + (i - 1) * gap + 1.6
        y1 = 2 + i * gap - 1.6 if i < 6 else 62
        y1c = min(y1, yc)
        if y1c > y0: box((0.14, y1c - y0, 0.006), (0, (y0 + y1c) / 2, 0.003), redm)
        if y1 > yc and LIT < 6: box((0.06, y1 - max(y0, yc), 0.004), (0, (max(y0, yc) + y1) / 2, 0.002), offm)
    cnt = [34, 17, 9, 5, 2, 1]; rnd = random.Random(2)
    for i in range(LIT):
        for j in range(cnt[i]):
            sphere(0.17, ((rnd.random() - 0.5) * road_w * 0.8, 2 + i * gap + 1.9 + rnd.random() * (gap - 3.8), 0.17), red)
        if i:
            for j in range(cnt[i - 1] - cnt[i]):
                sd = 1 if j % 2 else -1
                sphere(0.16, (sd * (road_w / 2 + 0.5 + rnd.random() * 1.5), 2 + i * gap - 1.5 - rnd.random() * 2.5, 0.16), grey)
    floor(rough=0.14)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 75, 3), rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.object; wall.scale = (400, 8, 1); put(wall, emis("wall", BLUE, 1.0))
    area("key", (0, 8, 14), (0, 14, 0), 14, 3000, BONE, sy=34)
    camera((0, -11.0, 11.5), (0, 11.0, 0.0), lens=30, focus=(0, 5, 0))

# ====================================================================== RECORDER STRIP (1-09), paper texture from Remotion
elif A.scene == "recorder":
    import bmesh
    img = bpy.data.images.load(A.mask)
    pm = bpy.data.materials.new("paper"); pm.use_nodes = True
    nt = pm.node_tree; b = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.55
    L, Wp, N, flat = 26.0, 3.0, 400, 17.0

    def centre(s):
        if s <= flat: return Vector((7.0 - s, 0, 0.002))
        u = s - flat; R0 = 1.1; ang = u / R0
        return Vector((7.0 - flat - R0 * math.sin(ang), 0, R0 * (1 - math.cos(ang)) + 0.002))
    bm = bmesh.new(); uv = bm.loops.layers.uv.new(); rows = []
    for i in range(N + 1):
        c = centre(L * i / N)
        rows.append((bm.verts.new((c.x, -Wp / 2, c.z)), bm.verts.new((c.x, Wp / 2, c.z))))
    for i in range(N):
        f = bm.faces.new((rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]))
        u0, u1 = 1 - i / N, 1 - (i + 1) / N
        for lp, uvv in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))): lp[uv].uv = uvv
    me = bpy.data.meshes.new("strip"); bm.to_mesh(me); o = bpy.data.objects.new("strip", me); col.objects.link(o)
    o.data.materials.append(pm); sm = o.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.01
    for p_ in me.polygons: p_.use_smooth = True
    box((3.2, 4.2, 1.3), (8.8, 0, 0.65), mat("body", lin("#002FA7"), rough=0.25, coat=1.0))
    box((0.1, 3.4, 0.08), (7.15, 0, 1.0), mat("slot", (0.4, 0.4, 0.4, 1), rough=0.2, metal=1.0))
    floor(rough=0.6)
    area("key", (2, -5, 9), (2, 0, 0), 7, 900, BONE, sy=4)
    area("rimB", (4, 12, 3), (0, 0, 0), 14, 1800, BLUE, sy=3)
    camera((-11.0, -10.0, 6.5), (-1.0, 0.3, 0.2), lens=32, focus=(-1, 0, 0))

# ====================================================================== COST STAIR (1-08)
elif A.scene == "stair":
    import bmesh
    cs, g = 0.2, 0.025; foot = 4
    bm = bmesh.new(); total = 0
    for k in range(20):
        n_ = 14 * (k + 1)  # cumulative; 1 cube = US$10M; last column = 280 = US$2.8B
        total += n_
        x0 = k * 1.15
        for j in range(n_):
            lx, ly, lz = j % foot, (j // foot) % foot, j // (foot * foot)
            r = bmesh.ops.create_cube(bm, size=cs)
            bmesh.ops.translate(bm, verts=r["verts"], vec=(x0 + lx * (cs + g), ly * (cs + g), lz * (cs + g) + cs / 2))
        ANCH.append((x0 + 0.33, -0.45, 0))
    me = bpy.data.meshes.new("cubes"); bm.to_mesh(me); o = bpy.data.objects.new("cubes", me); col.objects.link(o)
    bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.012; bv.segments = 2
    o.data.materials.append(mat("blueglass", lin("#2a45ff"), rough=0.12, trans=0.55, ior=1.5, coat=1.0))
    print("cubes", total)
    box((23.5, 0.05, 0.01), (10.9, -0.45, 0.005), emis("road", VERM, 5))
    tick = emis("tick", BONE, 1.5)
    for k in range(21):
        box((0.02, 0.18 if k % 5 else 0.34, 0.012), (k * 1.15 - 0.05, -0.45 - (0.09 if k % 5 else 0.17), 0.006), tick)
    floor(rough=0.32)
    area("key", (6, -8, 12), (11, 0, 0), 14, 3200, BONE, sy=6)
    area("rimB", (14, 10, 5), (11, 0, 1), 20, 2500, BLUE, sy=4)
    camera((-3.5, -12.0, 4.2), (11.5, 0.4, 1.2), lens=32, focus=(11, 0, 1))

# ====================================================================== FOGGED GLASS (1-08)
elif A.scene == "fog":
    img = bpy.data.images.load(A.mask); img.colorspace_settings.name = "Non-Color"
    pane = bpy.data.materials.new("pane"); pane.use_nodes = True
    nt = pane.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    clear = nt.nodes.new("ShaderNodeBsdfPrincipled"); clear.inputs["Transmission Weight"].default_value = 1; clear.inputs["Roughness"].default_value = 0.0
    fogb = nt.nodes.new("ShaderNodeBsdfPrincipled"); fogb.inputs["Transmission Weight"].default_value = 1; fogb.inputs["Roughness"].default_value = 0.45
    fogb.inputs["Base Color"].default_value = (0.85, 0.87, 0.9, 1)
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tx.outputs[0], mix.inputs[0]); nt.links.new(fogb.outputs[0], mix.inputs[1]); nt.links.new(clear.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    p_ = bpy.context.object; p_.scale = (16, 9, 1); put(p_, pane)
    rnd = random.Random(4)
    for j in range(26):
        x, z = (rnd.random() - 0.5) * 22, (rnd.random() - 0.5) * 12
        sphere(0.12 + rnd.random() * 0.25, (x, 5 + rnd.random() * 12, z), emis("b%d" % j, lin(rnd.choice(["#1F3BFF", "#0A1AFF", "#3a55ff", "#002FA7", "#EDEBE4" if A.state != "tally" else "#1F3BFF"])), 6 + rnd.random() * 14))
    if A.state == "tally":
        sphere(0.22, (0.55, 2.2, -0.05), emis("red", VERM, 60))
    else:
        for (x, z) in ((4.7, 1.2), (-3.5, -2.6)):
            sphere(0.45, (x, 8, z), emis("red", VERM, 30))
    area("key", (0, -6, 5), (0, 0, 0), 10, 120, BONE)
    camera((0, -9.0, 0), (0, 0, 0), lens=34, focus=(0, 0, 0))

# ====================================================================== LED COUNTER WALL (1-08, after Tatsuo Miyajima)
elif A.scene == "counter":
    SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd"}
    on_m = emis("ledon", VERM, 4.5); off_m = mat("ledoff", (0.22, 0.015, 0.01, 1), rough=0.35)
    on_b = emis("ledb", BLUE, 4.5); off_b = mat("ledboff", (0.01, 0.02, 0.2, 1), rough=0.35)
    unit_m = mat("unit", (0.008, 0.008, 0.009, 1), rough=0.25, coat=1.0)

    def digit(ch, x, z, s, onm, offm, y=-0.06):
        w, h, t = 1.0 * s, 1.8 * s, 0.17 * s
        box((w * 1.35, 0.12, h * 1.3), (x, 0.0, z), unit_m)  # housing
        segs = {"a": ((0, h / 2), True), "g": ((0, 0), True), "d": ((0, -h / 2), True),
                "f": ((-w / 2, h / 4), False), "b": ((w / 2, h / 4), False), "e": ((-w / 2, -h / 4), False), "c": ((w / 2, -h / 4), False)}
        for k, ((dx, dz), hor) in segs.items():
            m = onm if k in SEG.get(ch, "") else offm
            if hor: box((w - t * 1.2, 0.04, t), (x + dx, y, z + dz), m)
            else: box((t, 0.04, h / 2 - t * 1.2), (x + dx, y, z + dz), m)

    def row(txt, x0, z, s, onm, offm, pitch=1.55):
        for i, ch in enumerate(txt):
            if ch != " ": digit(ch, x0 + i * pitch * s, z, s, onm, offm)
    wall = mat("wall", (0.006, 0.006, 0.007, 1), rough=0.6)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.2, 0), rotation=(math.pi / 2, 0, 0))
    w_ = bpy.context.object; w_.scale = (300, 80, 1); put(w_, wall)
    # money: 2,800,000,000 big in red
    row("2800000000", -8.4, 1.9, 1.0, on_m, off_m, pitch=1.62)
    for k in (0, 3, 6):  # thousands separators
        box((0.12, 0.04, 0.34), (-8.4 + (k + 0.5) * 1.62 - 0.04, -0.06, 1.9 - 1.0), on_m, rot=(0, 0.35, 0))
    # time: two small blue counters, 2006 and 2026
    row("2006", -8.4, -1.6, 0.55, on_b, off_b)
    row("2026", 4.3, -1.6, 0.55, on_b, off_b)
    box((5.0, 0.04, 0.05), (1.0, -0.06, -1.6), emis("arrow", BONE, 2))
    # a field of tiny dark counters receding (the 1-in-10 / many-candidates texture)
    rnd = random.Random(8)
    for j in range(140):
        x, z = -18 + rnd.random() * 44, -4.2 + rnd.random() * 11
        if -9.8 < x < 9.4 and -2.9 < z < 3.9: continue
        digit(str(rnd.randint(1, 9)), x, z, 0.3, on_m if rnd.random() < 0.25 else off_m, off_m)
    floor(rough=0.15, z=-4.5)
    area("key", (-6, -10, 8), (0, 0, 0), 8, 250, BONE, sy=4)
    camera((-12.5, -16.0, 0.6), (-1.6, 0, 0.4), lens=34, focus=(-5, 0, 1.0))

# ====================================================================== render
if A.anchors:
    import json
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
    out = [[round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)] for v in (world_to_camera_view(scn, scn.camera, Vector(a)) for a in ANCH)]
    json.dump(out, open(A.anchors, "w")); print("ANCH", out); sys.exit(0)

scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        pref.compute_device_type = dev; pref.get_devices(); ok = False
        for d in pref.devices: d.use = (d.type == dev); ok |= d.use
        if ok: break
    except Exception as e: print("device", dev, e)
scn.cycles.device = "GPU"; scn.cycles.samples = A.samples
scn.cycles.use_denoising = True; scn.cycles.denoiser = "OPENIMAGEDENOISE"
scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16; scn.cycles.glossy_bounces = 8; scn.cycles.transparent_max_bounces = 16
scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = 1920, 1080, A.pct
vs_ = scn.view_settings; vs_.view_transform = "AgX"
try: vs_.look = "AgX - Punchy"
except Exception as e: print("look", e)
scn.render.image_settings.file_format = "PNG"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("WROTE", A.out)
