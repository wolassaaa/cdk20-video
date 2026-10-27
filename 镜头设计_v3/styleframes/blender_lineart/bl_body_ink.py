"""Frame 2 - the body (BodyParts3D skin FMA7163) in sparse ink, the real liver inside it in vermilion.

Run (from this folder):
  blender -b --factory-startup --python bl_body_ink.py -- bl_body_ink.png [--preview]

  * skin: decimated to 8 % and stripped of its inner shell (ray test, see clean_outer_skin), cached in
    _cache/skin_dec08_outer.stl (~60 s the first time, then ~3 s). Line Art: a bold outer silhouette
    (silhouette_filtering=INDIVIDUAL) + thin broken interior contours; eyes/nose/mouth faces carry Freestyle face
    marks and are filtered out (a sparse drawing with eyelids and lips reads as a cartoon face).
    Strokes are broken into pen strokes (Dash + Length overshoot), wobbled (Noise + Smooth) - deliberately sparse.
  * one cross-section ring: the skin cut by a horizontal plane at liver height (a real body cross-section, like a
    CT slice position), front half solid, back half thin.
  * liver (FMA7197, same mm frame, so it sits exactly where it is in this body): flat vermilion, offset dot-screen
    echo, thin white keyline (rendered with the skin hidden = x-ray), its own cut at the ring height as a black
    line, and - if the anatomy hook finds them - the intrahepatic portal/hepatic vein trees as black keylines.
  * editorial marks: a loose vermilion pen circle, a long hand-drawn leader into the empty right half, type.
"""
import bpy, sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink_common import *
from mathutils.bvhtree import BVHTree

CACHE = os.path.join(HERE, "_cache")
LIGHT = Vector((-0.55, -0.45, 0.70)).normalized()


def clean_outer_skin(o):
    """The BodyParts3D skin is a shell whose inner surface is connected through the mouth/eyes/navel etc.; Line Art
    would draw those pockets (a cartoon face, nested rings in cuts). Keep only faces that can 'see' the outside:
    a face is kept if any of 10 rays (both sides, normal + tilted) escapes the mesh. Then close the holes."""
    from mathutils.bvhtree import BVHTree
    import random
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    # drop tiny floating pieces
    seen, comps = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        while stack:
            g = stack.pop()
            if g.index in seen:
                continue
            seen.add(g.index)
            comp.append(g)
            stack.extend(h for e in g.edges for h in e.link_faces if h.index not in seen)
        comps.append(comp)
    big = max(comps, key=len)
    bmesh.ops.delete(bm, geom=[f for c in comps if c is not big for f in c], context="FACES")
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    rnd = random.Random(1)
    dirs = []
    inner = []
    for f in bm.faces:
        c, n = f.calc_center_median(), f.normal
        t1 = n.orthogonal().normalized()
        t2 = n.cross(t1)
        ok = False
        for sgn in (1, -1):
            for k in range(5):
                a = rnd.random() * 6.283
                tilt = 0.0 if k == 0 else 0.9
                d = (n * sgn + (t1 * math.cos(a) + t2 * math.sin(a)) * tilt).normalized()
                if bvh.ray_cast(c + d * 1e-4, d)[0] is None:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            inner.append(f)
    print("skin clean: removed", len(inner), "inner faces of", len(bm.faces), flush=True)
    bmesh.ops.delete(bm, geom=inner, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=4000)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()


def load_skin(coll):
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, "skin_dec08_outer.stl")
    if os.path.exists(cached):
        return import_stl(cached, coll, scale=1.0, name="skin")
    o = import_stl(SKIN_STL, coll, scale=0.001, name="skin")
    decimate(o, 0.08)
    clean_outer_skin(o)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.wm.stl_export(filepath=cached, export_selected_objects=True, apply_modifiers=True)
    return o


def ring_strokes(bm, z, cam_loc, bvh, px, front_only=False, largest=False):
    """Horizontal cut of a closed mesh at height z -> [(P, vis)] split into visible / hidden runs."""
    out = []
    b = bm.copy()
    res = bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1),
                                 dist=1e-7)
    b.normal_update()
    cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in cut:
        a, c = e.verts
        adj.setdefault(a, []).append(c)
        adj.setdefault(c, []).append(a)
    seen = set()
    loops = []
    for start in list(adj):
        if start in seen:
            continue
        chain, prev = [start], None
        seen.add(start)
        while True:
            nxt = [v for v in adj[chain[-1]] if v is not prev and v not in seen]
            if not nxt:
                break
            prev = chain[-1]
            chain.append(nxt[0])
            seen.add(nxt[0])
        if len(chain) >= 8:
            loops.append(chain)
    if largest and loops:
        # the outer torso loop: biggest footprint among loops that straddle the midline (this skin mesh has
        # several nested shells, the arms give separate loops)
        def area(ch):
            xs, ys = [v.co.x for v in ch], [v.co.y for v in ch]
            return (max(xs) - min(xs)) * (max(ys) - min(ys))
        mid = [ch for ch in loops if min(v.co.x for v in ch) < 0 < max(v.co.x for v in ch)] or loops
        loops = [max(mid, key=area)]
    for chain in loops:
        P = np.array([v.co[:] for v in chain] + [chain[0].co[:]])
        N = np.array([v.normal[:] for v in chain] + [chain[0].normal[:]])
        P, N = resample_poly(P, N, 2 * px)
        toc = np.array(cam_loc)[None] - P
        toc /= np.linalg.norm(toc, axis=1, keepdims=True)
        Pw = P + toc * 2.0 * px
        vis = visibility(Pw, cam_loc, bvh, 3 * px)
        for i0, i1 in runs(vis):
            if i1 - i0 > 3:
                out.append((Pw[i0:i1 + 1], True))
        if not front_only:
            for i0, i1 in runs(~vis):
                if i1 - i0 > 3:
                    out.append((Pw[i0:i1 + 1], False))
    b.free()
    return out


def build(preview=False, seed=5):
    sc = reset_scene((960, 540) if preview else (1920, 1080))
    cs, cl, cg, lab = collection("skin"), collection("liver"), collection("ink"), collection("labels")
    skin = load_skin(cs)
    liver = import_stl(LIVER_STL, cl, scale=0.001, name="liver")
    # intrahepatic vessels (if the anatomy hook found them) -> black keylines inside the red liver
    cvs = collection("vessels")
    ves = [import_stl(f, cvs, scale=0.001, name=n) for f, n in anatomy_stls()["vessels"]
           if n in ("portal_vein_hepatic", "hepatic_veins")]
    for o in (skin, liver, *ves):
        hide_from_camera(o)
    lb = [liver.matrix_world @ Vector(c) for c in liver.bound_box]
    lctr = sum(lb, Vector()) / 8

    # editorial framing: torso cropped at the hips, on the left third, seen a little from above and from the
    # patient's right so the cross-section rings open into ellipses; the right 60 % of the frame stays empty
    tgt = Vector((0.0, -0.08, 1.30))
    cam = camera(tgt + Vector((-0.80, -2.05, 0.50)), tgt, 50, shift=(0.22, 0.0))
    px = px_at(cam, tgt)

    # --- body: bold outer silhouette + thin, broken interior contours (sparse)
    gp = gp_object("body", cg)
    # face-marked faces (eyes / nose / mouth zone) give no lines: eyelids and lips read as a cartoon face here
    me = skin.data
    fm = me.attributes.get("freestyle_face") or me.attributes.new("freestyle_face", "BOOLEAN", "FACE")
    head_y = min(v.co.y for v in me.vertices if v.co.z > 1.5)
    marks = [abs(p.center.x) < 0.062 and 1.46 < p.center.z < 1.61 and p.center.y < head_y + 0.05
             for p in me.polygons]
    fm.data.foreach_set("value", marks)
    m, _, _ = lineart(gp, "sil", cs, INK, 2.3 * px, contour=True, crease=False, smooth=0.3, silhouette="INDIVIDUAL")
    m.use_face_mark, m.use_face_mark_invert, m.use_face_mark_keep_contour = True, True, False
    ink_mods(gp, px, "sil", wobble=2.0, freq=0.08, smooth_steps=5, thick_var=0.8, seed=seed, step=2, overshoot=0.10,
             double=1.4, dash=(40, 2))
    m2, _, _ = lineart(gp, "inner", cs, INK, 0.9 * px, contour=True, crease=False, smooth=0.3)
    m2.use_face_mark, m2.use_face_mark_invert, m2.use_face_mark_keep_contour = True, True, False
    ink_mods(gp, px, "inner", wobble=1.5, freq=0.1, smooth_steps=4, thick_var=0.8, seed=seed + 1, step=2,
             overshoot=0.06, dash=(22, 4), opacity=0.8)

    # --- liver keyline (x-ray: rendered with the skin hidden)
    gpl = gp_object("liver_line", cg)
    lineart(gpl, "liverline", cl, INK, 1.0 * px, contour=True, crease=False)
    ink_mods(gpl, px, wobble=0.8, freq=0.12, smooth_steps=3, thick_var=0.5, seed=seed + 3, step=2, overshoot=0.05,
             dash=(30, 1))

    gpv = None
    if ves:
        gpv = gp_object("ves_line", cg)
        lineart(gpv, "ves", cvs, BLACK, 0.75 * px, contour=True, crease=False)
        ink_mods(gpv, px, wobble=0.5, freq=0.15, smooth_steps=2, thick_var=0.4, seed=seed + 13, step=2)

    # --- cross-section rings through skin and liver at liver height (real cuts)
    bpy.context.view_layer.update()
    bms, bml = bm_world(skin), bm_world(liver)
    bvh = BVHTree.FromBMesh(bms)
    bvl = BVHTree.FromBMesh(bml)
    gpr = gp_object("rings", cg)
    zs = [lctr.z + 0.01]
    vis_s, hid_s, liv = [], [], []
    for z in zs:
        for P, v in ring_strokes(bms, z, cam.location, bvh, px, largest=True):
            (vis_s if v else hid_s).append((P, np.full(len(P), 0.6)))
        for P, v in ring_strokes(bml, z, cam.location, bvl, px):
            liv.append((P, np.full(len(P), 0.6 if v else 0.2)))
    write_strokes(gpr, "ring_front", vis_s, INK, 1.5 * px, 1.5 * px)
    write_strokes(gpr, "ring_back", hid_s, INK, 0.6 * px, 0.6 * px, opacity=0.7)
    ink_mods(gpr, px, wobble=1.0, freq=0.1, smooth_steps=3, thick_var=0.5, seed=seed + 7, step=2, taper=True,
             dash=(50, 3))
    gplr = gp_object("liver_rings", cg)
    write_strokes(gplr, "liver_ring", liv, BLACK, 0.8 * px, 1.6 * px)   # black section cuts across the red
    ink_mods(gplr, px, wobble=0.8, freq=0.12, smooth_steps=3, thick_var=0.4, seed=seed + 9, step=2, taper=True)
    bms.free()
    bml.free()

    # --- sparse hatching on the shadow side of the body (only every other slice, long pen strokes)
    bms = bm_world(skin)
    famA = slice_chains(bms, Vector((0.15, -0.35, 1.0)), 16 * px)
    rng = np.random.default_rng(seed)
    hA = hatch_strokes(famA, LIGHT, cam.location, bvh, px, thr=0.0, jitter=0.15, rng=rng, stroke=(30, 110),
                       min_len=18, view_fade=0.25, drop=0.5)
    bms.free()
    gph = gp_object("hatch", cg)
    write_strokes(gph, "hatch", hA, INK, 0.3 * px, 0.9 * px)
    ink_mods(gph, px, wobble=1.0, freq=0.15, smooth_steps=3, thick_var=0.3, seed=seed + 11, step=2, taper=False)
    print("hatch", len(hA), "rings", len(vis_s), len(hid_s), len(liv))

    return dict(sc=sc, cam=cam, skin=skin, liver=liver, gp=gp, gpl=gpl, gpr=gpr, gplr=gplr, gph=gph, cg=cg,
                lab=lab, px=px, lctr=lctr, zs=zs, ves=ves, gpv=gpv)


def add_labels(S, seed=5):
    sc, cam, lab = S["sc"], S["cam"], S["lab"]
    k = sc.render.resolution_x / 1920
    dim = tuple(c * 0.6 for c in INK)
    cam_label(cam, "02 / WHERE", 1180 * k, 128 * k, 20 * k, INK, coll=lab)
    lx, ly = world_to_pix(cam, S["lctr"])
    g = annot_gp(cam, lab, depth=1.0)
    ax, ay = 1180 * k, 640 * k
    annot_stroke(g, cam, [(lx + 130 * k, ly + 10 * k), (ax - 30 * k, ay - 30 * k)], VERMILION, 2.6 * k, curve=-24 * k)
    annot_stroke(g, cam, [(ax - 38 * k, ay - 30 * k), (ax + 470 * k, ay - 34 * k)], VERMILION, 2.0 * k, curve=4 * k)
    from bl_liver_ink import annot_px
    ink_mods(g, annot_px(cam, g), wobble=0.8, freq=0.12, smooth_steps=3, thick_var=0.4, seed=seed + 21, step=2,
             taper=True, resample=3.0)
    cam_label(cam, "LIVER", ax - 4 * k, ay + 64 * k, 76 * k, VERMILION, coll=lab, font=FONT_DISPLAY)
    cam_label(cam, "right upper abdomen, tucked under the ribs", ax, ay + 100 * k, 13 * k, VERMILION, coll=lab)
    # a loose vermilion pen circle around the organ
    xs, ys = [], []
    for v in S["liver"].data.vertices[:]:
        if v.index % 7 == 0:
            x, y = world_to_pix(cam, S["liver"].matrix_world @ v.co)
            xs.append(x)
            ys.append(y)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    annot_stroke(g, cam, scribble_ellipse(cx, cy, (max(xs) - min(xs)) * 0.66, (max(ys) - min(ys)) * 0.68,
                                          seed=seed), VERMILION, 2.2 * k)
    cam_label(cam, "BODY + LIVER: BodyParts3D FMA7163 / FMA7197", 1180 * k, 954 * k, 12 * k, dim, coll=lab)
    cam_label(cam, "DBCLS, CC BY 4.0 - one shared mm frame", 1180 * k, 974 * k, 12 * k, dim, coll=lab)
    cam_label(cam, "ring = a real horizontal cut through skin + liver", 1180 * k, 994 * k, 12 * k, dim, coll=lab)


def render_passes(S, tmp, tag="body"):
    os.makedirs(tmp, exist_ok=True)
    gps = list(S["cg"].objects)
    labs = list(S["lab"].objects)
    def setup(show, cam_meshes=(), hidden=(), labels=False):
        for o in labs:
            o.hide_render = not labels
        for o in gps:
            o.hide_render = o not in show
        for o in (S["skin"], S["liver"], *S["ves"]):
            o.hide_render = o in hidden
            o.visible_camera = o in cam_meshes
    p = {}
    if S["gpv"]:
        setup([S["gpv"]], hidden=[S["skin"], S["liver"]])
        p["ves"] = render(os.path.join(tmp, f"{tag}_ves.png"))
    setup([S["gp"], S["gpr"], S["gph"]], hidden=[S["liver"], *S["ves"]], labels=True)
    p["body"] = render(os.path.join(tmp, f"{tag}_lines.png"))
    setup([S["gpl"], S["gplr"]], hidden=[S["skin"], *S["ves"]])
    p["liverline"] = render(os.path.join(tmp, f"{tag}_liverline.png"))
    set_mat(S["liver"], emission_mat("m", (1, 1, 1)))
    setup([], cam_meshes=[S["liver"]], hidden=[S["skin"], *S["ves"]])
    p["matte"] = render(os.path.join(tmp, f"{tag}_matte.png"))
    return p


def composite(p, out, seed=5):
    body = load_rgba(p["body"])
    ll = load_rgba(p["liverline"])
    m = load_rgba(p["matte"])[..., 3]
    h, w = m.shape
    k = w / 1920
    stack = [("mask", halftone(shift(m, int(9 * k), int(7 * k)) * 0.7, cell=max(3, int(5 * k))), VERMILION),
             ("rgba", body, 0.2, 1.5),
             ("mask", dilate(m, max(1, int(3 * k))) * 0.9, BLACK),
             ("mask", m, VERMILION)]
    if "ves" in p:   # vessel tree as black keylines, only inside the liver silhouette
        stack.append(("mask", np.clip(load_rgba(p["ves"])[..., 3] * 1.3, 0, 1) * m * 0.85, BLACK))
    stack.append(("rgba", ll, 0.1, 1.4))
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
