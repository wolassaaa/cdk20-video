"""Frame 3 - CDK20 (AlphaFold model AF-Q8IZL9, CC BY 4.0) as ink line art, our docked 048 pose in electric cyan.

Run (from this folder):
  blender -b --factory-startup --python bl_protein_ink.py -- bl_protein_ink.png [--preview]

  * core 1-302 (mean pLDDT 91.5) as a "pipes and planks" cartoon built from the real CA coordinates:
    helices = straight pipes (SVD line fit), strands = flat arrows, loops = thin tubes. Secondary structure is
    estimated from CA geometry (P-SEA-style distance rules) - fine for a drawing, not a DSSP assignment.
    Line Art draws the outlines; elements behind the ligand plane become a thin grey ghost; the shadow side of
    every pipe gets cross-contour hatch rings (python strokes, sliced along the pipe axis).
  * tail 303-346 (mean pLDDT 47): a thin CA tube drawn as a nervous, broken, doubled pencil line - the drawing is
    uncertain where the model is uncertain. In the AlphaFold model it runs through the ATP pocket where 048 is
    docked (the pose file only contains residues 1-302).
  * 048: our AutoDock Vina re-docking pose (poses.json), heavy atoms as ball-and-stick: flat cyan + black keylines
    + offset dot-screen echo; its H-bond contacts as cyan dashes.
Scale: 1 Å -> 0.1 m.
"""
import bpy, sys, os, time, math, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink_common import *
from mathutils.bvhtree import BVHTree

S_ = 0.1
LIG = "048"
YAW, PITCH, ROLL = -30.0, 35.0, 0.0  # camera orbit around the pocket axis (degrees), picked from a scored contact sheet
BACK_DEPTH = 10.0                   # elements whose centre is this many Å behind the ligand -> ghost
FIT_H = 0.86                        # protein core height as a fraction of the frame height
CENTER = (0.37, 0.50)
COIL_R = 0.10                       # loop tube radius (Å): thin enough that Line Art reads it as one bold line               # where the protein's bbox centre lands (fraction of frame), labels go right


def read_pdb(path):
    atoms = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("ATOM"):
            atoms.append(dict(res=int(line[22:26]), name=line[12:16].strip(), resn=line[17:20],
                              xyz=np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
                              b=float(line[60:66]), el=line[76:78].strip()))
    return atoms


def assign_ss(X):
    """P-SEA-like CA-distance rules. Returns a string of H/E/C, one char per residue."""
    n = len(X)
    d = lambda i, k: np.linalg.norm(X[i] - X[i + k]) if i + k < n else 99.0
    ss = ["C"] * n
    for i in range(n - 4):
        if abs(d(i, 2) - 5.5) < 0.6 and abs(d(i, 3) - 5.3) < 0.6 and abs(d(i, 4) - 6.4) < 0.7:
            for k in range(5):
                ss[i + k] = "H"
    for i in range(n - 3):
        if abs(d(i, 2) - 6.7) < 0.5 and abs(d(i, 3) - 9.9) < 0.8:
            far = [j for j in range(n) if abs(j - i) > 3]
            if min(np.linalg.norm(X[i] - X[j]) for j in far) < 5.4:
                for k in range(3):
                    if ss[i + k] != "H":
                        ss[i + k] = "E"
    s = "".join(ss)
    s = re.sub(r"(?<!H)H{1,5}(?!H)", lambda m: "C" * len(m.group()), s)   # helices >= 6
    s = re.sub(r"(?<!E)E{1,3}(?!E)", lambda m: "C" * len(m.group()), s)   # strands >= 4
    return s


def segments(s):
    return [(m.group()[0], m.start(), m.end() - 1) for m in re.finditer(r"H+|E+|C+", s)]


def finish_mesh(name, verts, faces, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    for p in me.polygons:
        p.use_smooth = False
    return o


def pipe(X, coll, radius=2.2, nseg=28):
    """Straight cylinder fitted through helix CAs (Å input)."""
    c = X.mean(0)
    _, _, vt = np.linalg.svd(X - c)
    ax = vt[0] * np.sign(np.dot(vt[0], X[-1] - X[0]))
    t0, t1 = np.dot(X[0] - c, ax) - 0.8, np.dot(X[-1] - c, ax) + 0.8
    a, b = c + ax * t0, c + ax * t1
    u = np.cross(ax, [0.3, 0.5, 0.8]); u /= np.linalg.norm(u)
    v = np.cross(ax, u)
    verts, faces = [], []
    for e in (a, b):
        for k in range(nseg):
            th = 2 * math.pi * k / nseg
            verts.append(tuple((e + radius * (u * math.cos(th) + v * math.sin(th))) * S_))
    for k in range(nseg):
        k2 = (k + 1) % nseg
        faces.append((k, k2, nseg + k2, nseg + k))
    faces.append(tuple(range(nseg))[::-1])
    faces.append(tuple(range(nseg, 2 * nseg)))
    o = finish_mesh("helix", verts, faces, coll)
    return o, a * S_, b * S_, ax


def arrow(X, coll, half_w=1.0, half_t=0.22):
    """Flat beta-strand arrow along the smoothed CA path; width axis perpendicular to the pleat."""
    n = len(X)
    Xp = np.vstack([X[:1], X, X[-1:]])
    sm = np.array([(Xp[i] + 2 * Xp[i + 1] + Xp[i + 2]) / 4 for i in range(n)])
    sm[0], sm[-1] = X[0] * 0.5 + sm[0] * 0.5, X[-1] + (X[-1] - X[-2]) * 0.35
    verts, faces = [], []
    prev_side = None
    for i in range(n):
        tng = sm[min(i + 1, n - 1)] - sm[max(i - 1, 0)]
        tng /= np.linalg.norm(tng)
        pleat = X[i] - sm[i] if 0 < i < n - 1 else (X[1] - sm[1] if n > 2 else np.cross(tng, [0, 0, 1]))
        pleat = pleat - tng * np.dot(pleat, tng)
        if np.linalg.norm(pleat) < 1e-6:
            pleat = np.cross(tng, [0, 0, 1])
        pleat /= np.linalg.norm(pleat)
        side = np.cross(tng, pleat)
        if prev_side is not None and np.dot(side, prev_side) < 0:
            side = -side
        prev_side = side
        nrm = np.cross(side, tng)
        w = half_w
        if i == n - 2:
            w = half_w * 1.8          # arrow head shoulder
        if i == n - 1:
            w = 0.08
        for sw, st in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            verts.append(tuple((sm[i] + side * w * sw + nrm * half_t * st) * S_))
    for i in range(n - 1):
        a, b = 4 * i, 4 * (i + 1)
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((a + k, a + k2, b + k2, b + k))
    faces.append((3, 2, 1, 0))
    faces.append((4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 2, 4 * (n - 1) + 3))
    return finish_mesh("strand", verts, faces, coll)


def tube_mesh(points, radius, coll, name, res_u=6, bevel_res=3):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth, cd.bevel_resolution, cd.resolution_u = radius, bevel_res, res_u
    cd.use_fill_caps = True
    sp = cd.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for j, p in enumerate(points):
        sp.points[j].co = (*p, 1)
    sp.use_endpoint_u, sp.order_u = True, min(4, len(points))
    ob = bpy.data.objects.new(name, cd)
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.shade_smooth()
    return ob


def build(preview=False, seed=7):
    sc = reset_scene((960, 540) if preview else (1920, 1080))
    D = json.load(open(POSES, encoding="utf-8"))
    pose = D["poses"][LIG]
    atoms = read_pdb(PDB)
    ca = {a["res"]: a for a in atoms if a["name"] == "CA"}
    lig_all = [(a[0], np.array(a[1:])) for a in pose["atoms"]]
    keep = [i for i, (el, _) in enumerate(lig_all) if el != "H"]
    lc = np.mean([lig_all[i][1] for i in keep], axis=0)
    P = lambda xyz: Vector((np.asarray(xyz) - lc) * S_)   # ligand centre at the origin
    cf, cb, ct, clig, cg, lab = (collection(n) for n in ("front", "back", "tail", "lig", "ink", "labels"))

    # --- view basis: look into the cleft (ligand centre away from protein centre), N-lobe up
    pc = np.mean([a["xyz"] for a in atoms if a["res"] <= 302], axis=0)
    nl = np.mean([ca[r]["xyz"] for r in ca if r <= 85], axis=0)
    cl = np.mean([ca[r]["xyz"] for r in ca if 95 <= r <= 300], axis=0)
    out = Vector(lc - pc).normalized()
    up = Vector(nl - cl)
    up = (up - out * out.dot(up)).normalized()
    side = out.cross(up)
    yaw, pitch = math.radians(YAW), math.radians(PITCH)
    view = (out * math.cos(yaw) + side * math.sin(yaw)) * math.cos(pitch) + up * math.sin(pitch)
    fwd = -np.array(view)
    up_img = Matrix.Rotation(math.radians(ROLL), 3, view) @ up

    # --- cartoon of residues 1-302 (Å arrays in, scene units out)
    R = [r for r in sorted(ca) if r <= 302]
    X = np.array([ca[r]["xyz"] for r in R]) - lc
    ss = assign_ss(np.array([ca[r]["xyz"] for r in R]))
    elems = []          # (object, kind, collection-key)
    pipes = []          # (object, axis) for hatching
    segs = segments(ss)
    for kind, i0, i1 in segs:
        if kind == "H":
            o, a, b, ax = pipe(X[i0:i1 + 1], cf)
            pipes.append((o, ax))
        elif kind == "E":
            o = arrow(X[i0:i1 + 1], cf)
        else:
            j0, j1 = max(0, i0 - 1), min(len(R) - 1, i1 + 1)
            pts = [Vector(x * S_) for x in X[j0:j1 + 1]]
            if len(pts) < 2:
                continue
            o = tube_mesh(pts, COIL_R * S_, cf, "coil")
        dep = float(np.dot(X[i0:i1 + 1].mean(0), fwd))
        if dep > BACK_DEPTH:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            cb.objects.link(o)
        elems.append(o)
    print("SS", "".join(k for k, _, _ in segs), "helices", sum(k == "H" for k, _, _ in segs),
          "strands", sum(k == "E" for k, _, _ in segs))
    tail = tube_mesh([P(ca[r]["xyz"]) for r in sorted(ca) if r >= 302], COIL_R * S_, ct, "tail")

    # --- ligand ball-and-stick (heavy atoms only)
    RAD = {"C": 0.30, "N": 0.32, "O": 0.32, "S": 0.38}
    lig_objs = []
    for i in keep:
        el, xyz = lig_all[i]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=RAD.get(el, 0.3) * S_, location=P(xyz), segments=32,
                                             ring_count=16)
        o = bpy.context.object
        bpy.ops.object.shade_smooth()
        move_to(o, clig)
        lig_objs.append(o)
    for i, j, order in pose["bonds"]:
        if i not in keep or j not in keep:
            continue
        a, b = P(lig_all[i][1]), P(lig_all[j][1])
        d = b - a
        offs = [Vector()] if order < 1.9 else [d.cross(Vector(view)).normalized() * 0.08 * S_ * k for k in (-1, 1)]
        for off in offs:
            bpy.ops.mesh.primitive_cylinder_add(radius=(0.10 if order < 1.9 else 0.065) * S_, depth=d.length,
                                                location=(a + b) / 2 + off, vertices=16)
            o = bpy.context.object
            o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
            bpy.ops.object.shade_smooth()
            move_to(o, clig)
            lig_objs.append(o)
    for o in elems + [tail] + lig_objs:
        hide_from_camera(o)

    # --- camera on the view axis; distance fitted so the folded core (1-302) spans FIT_H of the frame height,
    # then shifted so the protein sits left (labels go right)
    cam = camera(tuple(view * 10.0), (0, 0, 0), 50)
    look_at(cam, (0, 0, 0), up_img)
    corep = [P(ca[r]["xyz"]) for r in R]
    Hh, Ww = sc.render.resolution_y, sc.render.resolution_x
    for _ in range(6):
        pp = [world_to_pix(cam, p) for p in corep]
        span = max((max(y for _, y in pp) - min(y for _, y in pp)) / Hh,
                   (max(x for x, _ in pp) - min(x for x, _ in pp)) / Hh / 1.25)
        cam.location = Vector(cam.location) * (span / FIT_H)
    pp = [world_to_pix(cam, p) for p in corep]
    cx = (max(x for x, _ in pp) + min(x for x, _ in pp)) / 2 / Ww
    cy = (max(y for _, y in pp) + min(y for _, y in pp)) / 2 / Hh
    cam.data.shift_x = cx - 0.5 + (0.5 - CENTER[0])
    cam.data.shift_y = -(cy - 0.5) * Hh / Ww - (0.5 - CENTER[1]) * Hh / Ww
    px = px_at(cam, Vector((0, 0, 0)))

    # --- ink: front cartoon firm, back cartoon ghost, tail nervous
    gp = gp_object("prot_ink", cg)
    lineart(gp, "front", cf, INK, 1.8 * px, contour=True, crease=True, crease_deg=100, smooth=0.2)
    ink_mods(gp, px, "front", wobble=0.9, freq=0.1, smooth_steps=4, thick_var=0.7, seed=seed, step=2,
             overshoot=0.06, dash=(34, 1))
    lineart(gp, "back", cb, INK, 0.9 * px, contour=True, crease=True, crease_deg=100, smooth=0.2)
    ink_mods(gp, px, "back", wobble=1.1, freq=0.1, smooth_steps=4, thick_var=0.5, seed=seed + 5, step=2,
             dash=(22, 3), opacity=0.4)
    gpt = gp_object("tail_ink", cg)
    lineart(gpt, "tail", ct, INK, 1.3 * px, contour=True, crease=False)
    ink_mods(gpt, px, "tail", wobble=5.0, freq=0.22, smooth_steps=1, thick_var=1.0, seed=seed + 1, step=2,
             overshoot=0.25, dash=(8, 4), opacity=0.95)
    mul = gpt.modifiers.new("scribble", "GREASE_PENCIL_MULTIPLY")    # several nervous passes = uncertainty
    mul.duplicates, mul.distance, mul.offset = 3, 4.0 * px, 0.4
    mul.use_fade, mul.fading_thickness, mul.fading_opacity, mul.fading_center = True, 0.6, 0.5, 0.5
    n2 = gpt.modifiers.new("scribble_noise", "GREASE_PENCIL_NOISE")
    n2.factor, n2.noise_scale, n2.factor_thickness = 4.0 * px / NOISE_K, 0.3, 0.6
    n2.use_random, n2.seed, n2.step = True, seed + 9, 2

    # --- hatch rings on the shadow side of the front pipes (sliced along each pipe's own axis)
    bpy.context.view_layer.update()
    L = (Vector(cam.matrix_world.to_3x3() @ Vector((-0.55, 0.65, 0.55)))).normalized()   # upper-left key light
    bm_all = bmesh.new()
    for o in elems + [tail]:
        bm_all.from_mesh(o.data)
    bvh = BVHTree.FromBMesh(bm_all)
    rng = np.random.default_rng(seed)
    hatch = []
    vdir = Vector(view)
    for o, ax in pipes:
        if cb in o.users_collection or abs(Vector(ax).dot(vdir)) > 0.75:   # end-on pipes would stack rings
            continue
        b = bm_world(o)
        ch = slice_chains(b, Vector(ax), 10 * px)
        hatch += hatch_strokes(ch, L, cam.location, bvh, px, thr=-0.05, jitter=0.15, rng=rng, stroke=(200, 400),
                               min_len=6, view_fade=0.05, offset=1.0)
        b.free()
    bm_all.free()
    gph = gp_object("hatch", cg)
    write_strokes(gph, "hatch", hatch, INK, 0.35 * px, 1.1 * px)
    ink_mods(gph, px, wobble=0.6, freq=0.15, smooth_steps=2, thick_var=0.3, seed=seed + 11, step=2, taper=False)
    print("hatch strokes", len(hatch))

    # --- ligand keylines + H-bond dashes
    gpl = gp_object("lig_ink", cg)
    lineart(gpl, "lig", clig, BLACK, 0.9 * px, contour=True, crease=False, intersection=True)
    ink_mods(gpl, px, "lig", wobble=0.5, freq=0.15, smooth_steps=2, thick_var=0.4, seed=seed + 3, step=2)
    gpb = gp_object("hbonds", cg)
    dense = []
    for c in pose["contacts"]:
        A, B = np.array(P(c["lig"])[:]), np.array(P(c["rec"])[:])
        t = np.linspace(0, 1, 40)[:, None]
        dense.append((A * (1 - t) + B * t, np.ones(40)))
    write_strokes(gpb, "hb", dense, CYAN, 1.4 * px, 1.4 * px)
    dm = gpb.modifiers.new("dash", "GREASE_PENCIL_DASH")
    dm.segments[0].dash, dm.segments[0].gap = 3, 3
    return dict(sc=sc, cam=cam, px=px, elems=elems, tail=tail, lig=lig_objs, cg=cg, lab=lab, gp=gp, gpt=gpt,
                gph=gph, gpl=gpl, gpb=gpb, pose=pose, P=P, ca=ca, D=D, ss=ss)


def add_labels(S, seed=7):
    sc, cam, lab, P, ca = S["sc"], S["cam"], S["lab"], S["P"], S["ca"]
    k = sc.render.resolution_x / 1920
    W, H = sc.render.resolution_x, sc.render.resolution_y
    dim = tuple(c * 0.6 for c in INK)
    from bl_liver_ink import annot_px
    cam_label(cam, "03 / TARGET", 110 * k, 128 * k, 20 * k, INK, coll=lab)
    seen = set()
    for c in S["pose"]["contacts"]:
        name = c["partner"].split()[0]
        if name in seen:
            continue
        seen.add(name)
        x, y = world_to_pix(cam, P(c["rec"]))
        cam_label(cam, name, x + 8 * k, y + 20 * k, 13 * k, CYAN, coll=lab)
    g = annot_gp(cam, lab, depth=1.0)
    # ligand tag (right, middle): leader from the right-most ligand atom
    ligpix = [world_to_pix(cam, o.location) for o in S["lig"] if o.name.startswith("Sphere")]
    x, y = max(ligpix, key=lambda q: q[0])
    lx, ly = 1380 * k, 470 * k
    annot_stroke(g, cam, [(x + 18 * k, y - 6 * k), (lx - 24 * k, ly - 24 * k), (lx + 330 * k, ly - 24 * k)],
                 CYAN, 2.0 * k, curve=-8 * k)
    cx = sum(q[0] for q in ligpix) / len(ligpix)
    cy = sum(q[1] for q in ligpix) / len(ligpix)
    rx = (max(q[0] for q in ligpix) - min(q[0] for q in ligpix)) * 0.68
    ry = (max(q[1] for q in ligpix) - min(q[1] for q in ligpix)) * 0.62
    annot_stroke(g, cam, scribble_ellipse(cx, cy, rx, ry, rot=0.5, seed=seed), CYAN, 1.8 * k)
    vina = S["pose"].get("vina")
    cam_label(cam, "048", lx - 4 * k, ly + 64 * k, 84 * k, CYAN, coll=lab, font=FONT_DISPLAY)
    cam_label(cam, f"our AutoDock Vina re-docking pose ({vina:.1f} kcal/mol)", lx, ly + 100 * k, 13 * k, CYAN,
              coll=lab)
    cam_label(cam, "a computed prediction, not an experimental structure", lx, ly + 120 * k, 13 * k, CYAN, coll=lab)
    cam_label(cam, "dashes = H-bond contacts in the pose", lx, ly + 140 * k, 13 * k, CYAN, coll=lab)
    # tail tag (right, low): leader from the right-most visible tail residue
    tx, ty = 1380 * k, 830 * k
    tail_pix = [world_to_pix(cam, P(ca[r]["xyz"])) for r in range(304, 347)]
    tail_pix = [q for q in tail_pix if 0 < q[0] < W * 0.7 and 0 < q[1] < H * 0.95]
    if tail_pix:
        x, y = max(tail_pix, key=lambda q: q[0])
        annot_stroke(g, cam, [(x + 16 * k, y + 4 * k), (tx - 24 * k, ty - 26 * k), (tx + 300 * k, ty - 26 * k)],
                     INK, 1.6 * k, curve=8 * k)
    ink_mods(g, annot_px(cam, g), wobble=0.7, freq=0.12, smooth_steps=3, thick_var=0.4, seed=seed + 21, step=2)
    cam_label(cam, "TAIL 303-346", tx, ty + 14 * k, 34 * k, INK, coll=lab, font=FONT_DISPLAY)
    cam_label(cam, "AlphaFold pLDDT ~47: low confidence, drawn shaky", tx, ty + 44 * k, 13 * k, INK, coll=lab)
    cam_label(cam, "in the model it runs through the same pocket", tx, ty + 64 * k, 13 * k, dim, coll=lab)
    cam_label(cam, "(the docking used residues 1-302 only)", tx, ty + 84 * k, 13 * k, dim, coll=lab)
    cam_label(cam, "CDK20: AlphaFold model AF-Q8IZL9 (DeepMind / EMBL-EBI, CC BY 4.0), residues 1-302 pLDDT ~92; "
              "cartoon from CA coordinates", 110 * k, 1010 * k, 12 * k, dim, coll=lab)


def render_passes(S, tmp, tag="prot"):
    os.makedirs(tmp, exist_ok=True)
    gps = list(S["cg"].objects)
    labs = list(S["lab"].objects)
    prot = S["elems"] + [S["tail"]]
    def setup(show, cam_meshes=(), hidden=(), labels=False):
        for o in labs:
            o.hide_render = not labels
        for o in gps:
            o.hide_render = o not in show
        for o in prot + S["lig"]:
            o.hide_render = o in hidden
            o.visible_camera = o in cam_meshes
    p = {}
    setup([S["gp"], S["gpt"], S["gph"]], hidden=S["lig"])
    p["prot"] = render(os.path.join(tmp, f"{tag}_prot.png"))
    setup([], hidden=prot + S["lig"], labels=True)
    p["labels"] = render(os.path.join(tmp, f"{tag}_labels.png"))
    setup([S["gpl"], S["gpb"]], hidden=prot)
    p["lig"] = render(os.path.join(tmp, f"{tag}_lig.png"))
    for o in S["lig"]:
        set_mat(o, emission_mat("m", (1, 1, 1)))
    setup([], cam_meshes=S["lig"], hidden=prot)
    p["ligmatte"] = render(os.path.join(tmp, f"{tag}_ligmatte.png"))
    return p


def composite(p, out, seed=7):
    prot = load_rgba(p["prot"])
    lig = load_rgba(p["lig"])
    labels = load_rgba(p["labels"])
    m = load_rgba(p["ligmatte"])[..., 3]
    h, w = m.shape
    k = w / 1920
    lig_rgb, lig_a = lig[..., :3], lig[..., 3]
    is_cyan = (lig_rgb[..., 2] > 0.5) & (lig_a > 0.02)
    hb = np.where(is_cyan, lig_a, 0)
    key = np.where(is_cyan, 0, lig_a)
    stack = [("rgba", prot, 0.2, 1.5),
             ("mask", halftone(shift(m, int(10 * k), int(8 * k)) * 0.75, cell=max(3, int(5 * k))), CYAN),
             ("mask", dilate(m, max(1, int(4 * k))) * 0.95, BLACK),
             ("mask", m, CYAN),
             ("mask", np.clip(key * 1.4, 0, 1) * 0.95, BLACK),
             ("mask", np.clip(hb * 1.4, 0, 1), CYAN),
             ("mask", np.clip(blur(labels[..., 3], max(2, int(8 * k))) * 40, 0, 1), BLACK),   # knock-out
             ("rgba", labels, 0.0, 1.3)]
    save_rgb(compose(stack, grain=0.03, seed=seed), out)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    OUT = os.path.abspath(argv[0])
    t0 = time.time()
    S = build(preview="--preview" in argv)
    add_labels(S)
    t1 = time.time()
    p = render_passes(S, os.path.join(os.path.dirname(OUT), "_passes"))
    composite(p, OUT)
    print(f"TIMING build {t1 - t0:.1f}s render+comp {time.time() - t1:.1f}s total {time.time() - t0:.1f}s")
