"""Shared helpers for the hand-drawn ink look (Blender 5.1, Grease Pencil v3 Line Art, EEVEE).

Every frame is rendered in two passes and composited with numpy inside Blender:
  ink pass  : only the Grease Pencil Line Art objects (meshes are invisible to the camera but still feed Line Art)
  fill pass : flat emission mattes of selected meshes (used for accent colour blocks, offset like a misregistered print)
The composite adds the black ground, the offset accent fills, ink lines, a little ink bleed and film grain.
"""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix

INK = (0.929, 0.922, 0.894)       # #EDEBE4 off-white ink
BLACK = (0.027, 0.027, 0.027)     # #070707
VERMILION = (1.0, 0.231, 0.122)   # #FF3B1F body / blood
CYAN = (0.161, 0.941, 1.0)        # #29F0FF AI / computed

HERE = os.path.dirname(os.path.abspath(__file__))
LIVER_STL = r"D:\dsh project\cdk20-film\assets\structures\FMA7197_liver.stl"
SKIN_STL = r"D:\。hkbu\molecular science\镜头设计_v2\tests\T5_body\assets\FMA7163_skin.stl"
PDB = r"D:\dsh project\cdk20-film\assets\structures\CDK20_py.pdb"
POSES = r"D:\。hkbu\molecular science\镜头设计_v2\tests\T6_molecules\poses.json"
ANATOMY_DIR = r"D:\。hkbu\molecular science\镜头设计_v3\assets\anatomy"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_DISPLAY = r"C:\Windows\Fonts\ARIALNB.TTF"   # Arial Narrow Bold for the few big words


def srgb_to_lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ------------------------------------------------------------------ scene
def reset_scene(res=(1920, 1080)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"   # keep the accent colours exact (AgX would desaturate them)
    sc.view_settings.look = "None"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.eevee.taa_render_samples = 16
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    sc.world = w
    sc.frame_start = sc.frame_end = sc.frame_current = 1
    return sc


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def import_stl(path, coll, scale=0.001, name=None):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    o.scale = (scale,) * 3
    if name:
        o.name = name
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    move_to(o, coll)
    return o


def decimate(o, ratio):
    m = o.modifiers.new("dec", "DECIMATE")
    m.ratio = ratio
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)


def hide_from_camera(o):
    """Mesh stays in the depsgraph (Line Art sees it) but never shows in the beauty render."""
    o.visible_camera = False
    o.visible_shadow = False


def camera(loc, target, lens=50, shift=(0, 0), ortho=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.shift_x, cd.shift_y = shift
    if ortho:
        cd.type, cd.ortho_scale = "ORTHO", ortho
    cd.clip_start, cd.clip_end = 0.01, 200
    ob = bpy.data.objects.new("cam", cd)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def look_at(obj, target, up=(0, 0, 1)):
    """Orient a camera to look at `target` with `up` projected as the image's up direction."""
    f = (Vector(target) - Vector(obj.location)).normalized()
    u = Vector(up)
    u = (u - f * f.dot(u)).normalized()
    r = f.cross(u)
    m = Matrix((r, u, -f)).transposed()
    obj.rotation_euler = m.to_euler()


def empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def emission_mat(name, color, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*srgb_to_lin(color), 1)   # palette is given in display sRGB
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def set_mat(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


# ------------------------------------------------------------------ grease pencil
def gp_material(name, color, alpha=1.0):
    m = bpy.data.materials.new(name)
    bpy.data.materials.create_gpencil_data(m)
    g = m.grease_pencil
    g.color = (*srgb_to_lin(color), alpha)   # palette is given in display sRGB, GP colours are scene-linear
    g.show_stroke, g.show_fill = True, False
    return m


def gp_object(name, coll=None):
    d = bpy.data.grease_pencils.new(name)
    o = bpy.data.objects.new(name, d)
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def lineart(gp, name, source_coll, color, radius, opacity=1.0, *, contour=True, crease=False, loose=False,
            intersection=False, material_bounds=False, edge_mark=False, crease_deg=140, silhouette=None,
            light=None, shadow_filter=None, light_contour=False, smooth=0.0, chain_thresh=0.001, depth_offset=0.0,
            back_face_cull=False, level=(0, 0)):
    """Add one Line Art modifier writing into its own layer + material on GP object `gp`."""
    d = gp.data
    layer = d.layers.new(name)
    layer.use_lights = False
    layer.frames.new(bpy.context.scene.frame_start)
    mat = gp_material(name, color)
    d.materials.append(mat)
    m = gp.modifiers.new(name, "LINEART")
    m.source_type = "COLLECTION"
    m.source_collection = source_coll
    m.target_layer = name
    m.target_material = mat
    m.radius, m.opacity = radius, opacity
    m.use_contour, m.use_crease, m.use_loose = contour, crease, loose
    m.use_intersection, m.use_material, m.use_edge_mark = intersection, material_bounds, edge_mark
    m.crease_threshold = math.radians(crease_deg)
    m.use_crease_on_smooth = True
    m.smooth_tolerance = smooth
    m.chaining_image_threshold = chain_thresh
    m.use_loose_edge_chain = True
    m.stroke_depth_offset = depth_offset
    m.use_back_face_culling = back_face_cull
    m.level_start, m.level_end = level
    m.use_multiple_levels = level[1] > level[0]
    if silhouette:
        m.silhouette_filtering = silhouette
    if light is not None:
        m.light_contour_object = light
        m.use_light_contour = light_contour
        if shadow_filter:
            m.use_shadow = True
            m.shadow_region_filtering = shadow_filter
    return m, layer, mat


def _curve(mapping, pts):
    """Fill a CurveMapping with (x, y) points."""
    c = mapping.curves[0]
    while len(c.points) > 2:
        c.points.remove(c.points[1])
    c.points[0].location = pts[0]
    c.points[-1].location = pts[-1]
    for p in pts[1:-1]:
        c.points.new(*p)
    mapping.update()


def px_at(cam, point):
    """World size of one output pixel at the depth of `point` (perspective camera, horizontal sensor fit)."""
    sc = bpy.context.scene
    cd = cam.data
    if cd.type == "ORTHO":
        return cd.ortho_scale / sc.render.resolution_x
    bpy.context.view_layer.update()
    depth = -(cam.matrix_world.inverted() @ Vector(point)).z
    assert depth > 0, "point is behind the camera"
    return depth * cd.sensor_width / cd.lens / sc.render.resolution_x


NOISE_K = 0.0375   # calibrated: GP noise factor 1.0 ~ 0.0375 world units of wobble after smoothing


def ink_mods(gp, px, layer=None, *, wobble=2.0, freq=0.1, smooth_steps=6, thick_var=0.5, seed=1, step=2,
             taper=True, overshoot=0.0, resample=3.0, double=None, thick=1.0, opacity=None, dash=None):
    """Hand-drawn feel on top of Line Art / python strokes, all sizes in output pixels (px = world size of 1 px):
    resample -> (double sketch line) -> overshoot -> wobble noise (re-seeded every `step` frames = boil on twos)
    -> smooth -> pressure taper. `layer` restricts the stack to one GP layer."""
    def mod(kind, nm):
        m = gp.modifiers.new(nm, kind)
        if layer is not None:
            m.tree_node_filter = layer
        return m
    tag = layer or "all"
    if resample:
        s = mod("GREASE_PENCIL_SIMPLIFY", f"resample_{tag}")
        s.mode, s.length = "SAMPLE", resample * px
    if dash:
        # break long Line Art chains into separate pen strokes (dash, gap in resampled points); with `overshoot`
        # each piece is extended so neighbouring strokes overlap like a hand-inked contour
        dm = mod("GREASE_PENCIL_DASH", f"dash_{tag}")
        dm.segments[0].dash, dm.segments[0].gap = dash
    if double:
        mul = mod("GREASE_PENCIL_MULTIPLY", f"double_{tag}")
        mul.duplicates, mul.distance, mul.offset = 1, double * px, 0.0
        mul.use_fade, mul.fading_thickness, mul.fading_opacity, mul.fading_center = True, 0.5, 0.45, 0.5
    if overshoot:
        L = mod("GREASE_PENCIL_LENGTH", f"len_{tag}")
        L.mode = "RELATIVE"
        L.start_factor = L.end_factor = overshoot
        L.use_random, L.random_start_factor, L.random_end_factor = True, overshoot * 2, overshoot * 2
        L.seed, L.step = seed + 7, step
        L.use_curvature = False
    if wobble:
        n = mod("GREASE_PENCIL_NOISE", f"noise_{tag}")
        n.factor, n.factor_strength, n.factor_thickness, n.factor_uvs = wobble * px / NOISE_K, 0.0, thick_var, 0.0
        n.noise_scale, n.noise_offset = freq, 0.0
        n.use_random, n.seed, n.step, n.random_mode = True, seed, step, "STEP"
    if smooth_steps:
        s = mod("GREASE_PENCIL_SMOOTH", f"smooth_{tag}")
        s.factor, s.step = 1.0, smooth_steps
        s.use_edit_position, s.use_edit_thickness = True, True
    t = mod("GREASE_PENCIL_THICKNESS", f"thick_{tag}")
    t.use_uniform_thickness = False
    t.thickness_factor = thick
    if taper:
        t.use_custom_curve = True
        _curve(t.custom_curve, [(0, 0.12), (0.1, 0.8), (0.45, 1.0), (0.85, 0.85), (1, 0.08)])
    if opacity is not None:
        o = mod("GREASE_PENCIL_OPACITY", f"op_{tag}")
        o.color_mode, o.color_factor = "STROKE", opacity


# ------------------------------------------------------------------ hand-made strokes (hatching) written straight into GP
def bm_world(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.normal_update()
    return bm


def slice_chains(bm, normal, spacing, phase=0.5):
    """Cross-contour lines: cut the (world-space) bmesh with parallel planes. Returns [(P(n,3), N(n,3), t)]."""
    assert spacing > 0
    normal = Vector(normal).normalized()
    ds = [normal.dot(v.co) for v in bm.verts]
    lo, hi = min(ds), max(ds)
    out = []
    t = lo + spacing * phase
    while t < hi:
        b = bm.copy()
        res = bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=normal * t,
                                     plane_no=normal, dist=1e-7)
        b.normal_update()
        cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        adj = {}
        for e in cut:
            a, c = e.verts
            adj.setdefault(a, []).append(c)
            adj.setdefault(c, []).append(a)
        seen = set()
        for start in list(adj):
            if start in seen:
                continue
            # walk to one end (if open) then collect
            prev, cur = None, start
            for _ in range(len(adj) + 1):
                nxt = [v for v in adj[cur] if v is not prev]
                if len(adj[cur]) != 2 or not nxt or nxt[0] is start:
                    break
                prev, cur = cur, nxt[0]
            chain, prev = [cur], None
            seen.add(cur)
            while True:
                nxt = [v for v in adj[chain[-1]] if v is not prev and v not in seen]
                if not nxt:
                    break
                prev = chain[-1]
                chain.append(nxt[0])
                seen.add(nxt[0])
            if len(chain) >= 3:
                out.append((np.array([v.co[:] for v in chain]), np.array([v.normal[:] for v in chain]), t))
        b.free()
        t += spacing
    return out


def visibility(P, cam_loc, bvh, eps):
    c = Vector(cam_loc)
    vis = np.zeros(len(P), dtype=bool)
    for i, p in enumerate(P):
        p = Vector(p)
        d = p - c
        L = d.length
        hit = bvh.ray_cast(c, d / L, L)
        vis[i] = hit[0] is None or hit[3] >= L - eps
    return vis


def runs(mask):
    """Index runs where mask is True -> list of (i0, i1) inclusive."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def resample_poly(P, N, ds):
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    if L[-1] < ds * 2:
        return P, N
    t = np.arange(0, L[-1], ds)
    Pr = np.stack([np.interp(t, L, P[:, i]) for i in range(3)], 1)
    Nr = np.stack([np.interp(t, L, N[:, i]) for i in range(3)], 1)
    Nr /= np.linalg.norm(Nr, axis=1, keepdims=True) + 1e-12
    return Pr, Nr


def hatch_strokes(chains, light_dir, cam_loc, bvh, px, *, thr=0.2, jitter=0.12, offset=1.5, rng=None,
                  stroke=(40, 160), gap=(2, 6), min_len=12, drop=0.0, view_fade=0.15, every=1, sparse=None):
    """Keep the parts of each cross-contour chain that face away from the light (n.l < thr; the threshold is
    jittered per line so the hatch edge is ragged like a pen drawing), that are visible from the camera and not
    grazing; split them into pen strokes. Sizes in output pixels. Returns [(P, darkness)]."""
    rng = rng or np.random.default_rng(0)
    L = np.array(light_dir, dtype=np.float64)
    L /= np.linalg.norm(L)
    cam = np.array(cam_loc)
    out = []
    for k, (P, N, _) in enumerate(chains):
        if k % every or (drop and rng.random() < drop):
            continue
        P, N = resample_poly(P, N, 2 * px)
        s = N @ L
        base = sparse[1] if (sparse and k % sparse[0] == 0) else thr   # every n-th line reaches further into light
        t = base + rng.uniform(-jitter, jitter)
        Pw = P + N * offset * px
        V = Pw - cam
        V /= np.linalg.norm(V, axis=1, keepdims=True)
        facing = -(N * V).sum(1)
        keep = (s < t) & (facing > view_fade)
        if not keep.any():
            continue
        keep &= visibility(Pw, cam_loc, bvh, offset * px * 3)
        for i0, i1 in runs(keep):
            i = i0
            while i < i1:
                j = min(i1, i + int(rng.integers(*stroke) / 2))
                if (j - i) * 2 >= min_len:
                    out.append((Pw[i:j + 1], np.clip((t - s[i:j + 1]) / (t + 1.0), 0, 1)))
                i = j + int(rng.integers(*gap) / 2) + 1
    return out


def write_strokes(gp, layer_name, strokes, color, r_min, r_max, opacity=1.0, frame=None, use_lights=False):
    """strokes: [(P(n,3), darkness(n))] -> one GP layer; radius swells with darkness (engraving line)."""
    d = gp.data
    layer = d.layers.get(layer_name) or d.layers.new(layer_name)
    layer.use_lights = use_lights
    fn = bpy.context.scene.frame_start if frame is None else frame
    fr = next((f for f in layer.frames if f.frame_number == fn), None) or layer.frames.new(fn)
    mname = f"{gp.name}_{layer_name}"
    mat = next((m for m in d.materials if m and m.get("ink_layer") == mname), None)
    if mat is None:
        mat = gp_material(mname, color)
        mat["ink_layer"] = mname
        d.materials.append(mat)
    mi = list(d.materials).index(mat)
    strokes = [(np.asarray(P, np.float32), np.asarray(k, np.float32)) for P, k in strokes if len(P) >= 2]
    if not strokes:
        return layer
    dr = fr.drawing
    def attr(name, typ, dom):
        return dr.attributes.get(name) or dr.attributes.new(name, typ, dom)
    def get(name, typ, dom, width):
        a = attr(name, typ, dom)
        buf = np.zeros(len(a.data) * width, np.float32 if typ != "INT" else np.int32)
        if len(a.data):
            a.data.foreach_get("vector" if width == 3 else "value", buf)
        return buf
    # existing content (appending to a drawing that already has strokes)
    old = {n: get(n, t, dm, wd) for n, t, dm, wd in (("position", "FLOAT_VECTOR", "POINT", 3),
                                                      ("radius", "FLOAT", "POINT", 1),
                                                      ("opacity", "FLOAT", "POINT", 1),
                                                      ("material_index", "INT", "CURVE", 1))}
    dr.add_strokes([len(P) for P, _ in strokes])
    pos = np.concatenate([P for P, _ in strokes]).ravel()
    rad, op = [], []
    for P, k in strokes:
        n = len(P)
        u = np.linspace(0, 1, n)
        taper = np.sin(np.pi * np.clip(0.04 + 0.92 * u, 0, 1)) ** 0.6
        rad.append((r_min + (r_max - r_min) * k) * (0.2 + 0.8 * taper))
        op.append(np.full(n, opacity, np.float32))
    attr("position", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", np.concatenate([old["position"], pos]))
    attr("radius", "FLOAT", "POINT").data.foreach_set(
        "value", np.concatenate([old["radius"], np.concatenate(rad).astype(np.float32)]))
    attr("opacity", "FLOAT", "POINT").data.foreach_set(
        "value", np.concatenate([old["opacity"], np.concatenate(op).astype(np.float32)]))
    attr("material_index", "INT", "CURVE").data.foreach_set(
        "value", np.concatenate([old["material_index"], np.full(len(strokes), mi, np.int32)]))
    return layer


# ------------------------------------------------------------------ text (labels as flat emission text)
def label(text, loc, rot, size, color, coll=None, font=FONT_MONO, align="LEFT", parent=None):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = align
    if font and os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    o = bpy.data.objects.new("txt", cu)
    o.location, o.rotation_euler = loc, rot
    if parent:
        o.parent = parent
    (coll or bpy.context.scene.collection).objects.link(o)
    o.data.materials.append(emission_mat("txt_" + text[:8], color, 1.0))
    return o


def cam_label(cam, text, px, py, height_px, color, coll=None, align="LEFT", font=FONT_MONO):
    """Place a text object parented to the camera so it lands at pixel (px, py) (origin top-left) with a given
    cap height in pixels. Works for perspective cameras with sensor_fit AUTO and landscape output."""
    sc = bpy.context.scene
    W, H = sc.render.resolution_x, sc.render.resolution_y
    cd = cam.data
    depth = cd.clip_start * 5 + 0.05
    vis_w = cd.sensor_width / cd.lens * depth if cd.type == "PERSP" else cd.ortho_scale
    sx, sy = cd.shift_x * vis_w, cd.shift_y * vis_w
    x = (px / W - 0.5) * vis_w + sx
    y = (0.5 - py / H) * vis_w * H / W + sy
    size = height_px / W * vis_w / 0.72
    return label(text, (x, y, -depth), (0, 0, 0), size, color, coll=coll, align=align, parent=cam, font=font)


def pix_to_cam_local(cam, x, y, depth):
    """Pixel (x right, y down, origin top-left) -> point in camera-local space at distance `depth`."""
    sc = bpy.context.scene
    W, H = sc.render.resolution_x, sc.render.resolution_y
    cd = cam.data
    vis_w = cd.sensor_width / cd.lens * depth if cd.type == "PERSP" else cd.ortho_scale
    sx, sy = cd.shift_x * vis_w, cd.shift_y * vis_w
    return Vector(((x / W - 0.5) * vis_w + sx, (0.5 - y / H) * vis_w * H / W + sy, -depth))


def world_to_pix(cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    v = world_to_camera_view(sc, cam, Vector(p))
    return v.x * sc.render.resolution_x, (1 - v.y) * sc.render.resolution_y


def scribble_ellipse(cx, cy, rx, ry, turns=1.35, rot=-0.15, seed=0, n=160):
    """A quick hand-drawn ellipse (pixel coords): >1 turn, drifting radius, so it overshoots like a pen gesture."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi * turns, n) + rng.uniform(0, 6.28)
    drift = 1 + 0.08 * np.sin(t * 0.7 + rng.uniform(0, 6)) + np.linspace(-0.06, 0.08, n)
    x, y = rx * np.cos(t) * drift, ry * np.sin(t) * drift
    cr, sr = math.cos(rot), math.sin(rot)
    return list(zip(cx + x * cr - y * sr, cy + x * sr + y * cr))


def annot_gp(cam, coll, name="annot", depth=1.0):
    """GP object glued to the camera for hand-drawn 2D marks (leader lines, brackets). Use annot_stroke()."""
    g = gp_object(name, coll)
    g.parent = cam
    g["depth"] = depth
    return g


def annot_stroke(g, cam, pts_px, color, width_px, layer=None, frame=None, curve=0.0, seed=0):
    """Draw a hand-drawn polyline given in pixel coordinates (optionally bowed by `curve` px)."""
    depth = g["depth"]
    layer = layer or "annot_%02x%02x%02x" % tuple(int(c * 255) for c in color)   # one layer/material per colour
    pts = np.array(pts_px, dtype=np.float64)
    # densify + slight bow so it does not look ruler-straight
    dense = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / 3))
        t = np.linspace(0, 1, n, endpoint=False)
        seg = a[None] + (b - a)[None] * t[:, None]
        nrm = np.array([-(b - a)[1], (b - a)[0]]) / (np.linalg.norm(b - a) + 1e-9)
        seg += nrm[None] * (np.sin(np.pi * t) * curve)[:, None]
        dense.append(seg)
    dense.append(pts[-1:])
    dense = np.concatenate(dense)
    P = np.array([pix_to_cam_local(cam, x, y, depth)[:] for x, y in dense])
    px = pix_to_cam_local(cam, 1, 0, depth).x - pix_to_cam_local(cam, 0, 0, depth).x
    write_strokes(g, layer, [(P, np.ones(len(P)))], color, width_px * 0.5 * px, width_px * 0.5 * px, frame=frame)
    return px


# ------------------------------------------------------------------ render + composite
def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_rgba(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1].copy()   # top-down


def save_rgb(arr, path):
    h, w = arr.shape[:2]
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = np.clip(arr[..., :3], 0, 1)
    img = bpy.data.images.new("out", w, h, alpha=True)
    img.pixels.foreach_set(out[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def shift(a, dx, dy):
    """Translate an image (pixels), filling with zeros."""
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    out[yd, xd] = a[ys, xs]
    return out


def blur(a, r):
    """Cheap separable box blur (3 passes ~ gaussian)."""
    if r < 1:
        return a
    out = a.astype(np.float32)
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if i == ax else (0, 0) for i in range(out.ndim)], mode="edge"), axis=ax)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax)
            lo = np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)
            out = (hi - lo) / (2 * r + 1)
    return out


def halftone(mask, cell=7, angle=0.4, gain=1.0):
    """Dot-screen version of a 0..1 mask (used for soft accent fills)."""
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ca, sa = math.cos(angle), math.sin(angle)
    u = (xx * ca + yy * sa) / cell
    v = (-xx * sa + yy * ca) / cell
    d = np.hypot(u - np.round(u), v - np.round(v)) / 0.7071
    return np.clip((np.sqrt(np.clip(mask * gain, 0, 1)) - d) * 3.0 + 0.5, 0, 1) * (mask > 0.01)


def compose(stack, grain=0.03, seed=0, bg=BLACK):
    """Layer stack over the black ground (top of list = bottom layer). Items:
         ("mask", mask HxW, colour)          flat colour through a 0..1 mask
         ("rgba", rgba HxWx4, bleed[, gain])  a rendered ink pass (PNG = straight alpha); `bleed` adds a soft ink
                                              halo, `gain` boosts alpha so anti-aliased strokes print as solid ink
    Ends with film grain that is stronger on the light marks (like toner / riso grain)."""
    first = stack[0][1]
    h, w = first.shape[:2]
    rng = np.random.default_rng(seed)
    out = np.empty((h, w, 3), dtype=np.float32)
    out[:] = bg
    mott = blur(rng.standard_normal(((h + 7) // 8, (w + 7) // 8)).astype(np.float32), 2)
    mott = np.kron(mott, np.ones((8, 8), dtype=np.float32))[:h, :w]
    out += (mott * 0.012)[..., None]
    for kind, data, *args in stack:
        arg = args[0]
        if kind == "mask":
            m = np.clip(data, 0, 1)[..., None]
            out = out * (1 - m) + m * np.array(arg, dtype=np.float32)
        else:
            a = np.clip(data[..., 3:4] * (args[1] if len(args) > 1 else 1.0), 0, 1)
            col = data[..., :3]
            if arg:
                soft = blur(a[..., 0], 2)[..., None]
                out = out * (1 - soft * arg) + soft * arg * col
            out = out * (1 - a) + col * a
    n = rng.standard_normal((h, w)).astype(np.float32)
    out += (n * grain)[..., None] * (0.35 + 0.65 * out.mean(axis=2, keepdims=True))
    return np.clip(out, 0, 1)


def dilate(mask, r):
    return np.clip(blur(mask, r) * 3.0, 0, 1)


ORGANS = {"FMA7197": "liver", "FMA7202": "gallbladder", "FMA7163": "skin"}
# BodyParts3D v4 named groups (made by the assets agent from FJ elements, same mm frame)
V4_BLOOD = ["inferior_vena_cava", "abdominal_aorta", "portal_vein_hepatic", "hepatic_veins", "hepatic_artery",
            "celiac_trunk", "portal_tributaries_splenic_SMV"]
V4_OTHER = {"gallbladder": "gallbladder", "intrahepatic_bile_ducts": "bile", "liver_parenchyma_segments": "liver_v4"}


def anatomy_stls():
    """Hook for the BodyParts3D meshes another agent drops into 镜头设计_v3/assets/anatomy/.
    Prefers the v4 named groups (bp3d_v4_groups_stl/*.stl); otherwise every v3 FMA*.stl that is not a known organ is
    treated as a vessel. Returns {"vessels": [(path, name)], "gallbladder": path|None, "bile": path|None,
    "liver_v4": path|None}. Blood vessels are drawn in vermilion; bile ducts/gallbladder are NOT blood."""
    import glob
    out = {"vessels": [], "gallbladder": None, "bile": None, "liver_v4": None}
    if not os.path.isdir(ANATOMY_DIR):
        return out
    g4 = os.path.join(ANATOMY_DIR, "bp3d_v4_groups_stl")
    if os.path.isdir(g4):
        for n in V4_BLOOD:
            f = os.path.join(g4, n + ".stl")
            if os.path.exists(f):
                out["vessels"].append((f, n))
        for n, key in V4_OTHER.items():
            f = os.path.join(g4, n + ".stl")
            if os.path.exists(f):
                out[key] = f
        if out["vessels"]:
            return out
    for f in sorted(glob.glob(os.path.join(ANATOMY_DIR, "**", "*.stl"), recursive=True)):
        fma = os.path.splitext(os.path.basename(f))[0].split("_")[0].upper()
        kind = ORGANS.get(fma)
        if kind == "gallbladder":
            out["gallbladder"] = f
        elif kind is None and fma.startswith("FMA"):
            out["vessels"].append((f, fma))
    return out
