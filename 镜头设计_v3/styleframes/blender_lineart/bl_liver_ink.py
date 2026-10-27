"""Frame 1 - the real liver (BodyParts3D FMA7197) as a hand-inked drawing on black, vessels in vermilion.

Run (from this folder):
  blender -b --factory-startup --python bl_liver_ink.py -- bl_liver_ink.png [--preview]

Pipeline
  * Line Art (GPv3 modifier) draws the visible silhouette/contour; its stroke weight follows a vertex group that
    stores how much each vertex faces away from the key light (heavier line on the shadow side, like an inker would).
  * Cross-contour hatching is made in Python: the mesh is sliced by parallel planes, the parts that face away from
    the light and are visible from the camera (BVH ray casts) become GP strokes whose width swells with darkness.
    A second plane family is added only in the deeper shadow -> crosshatch.
  * Wobble/boil: GP Simplify(sample) -> Noise (seed changes every `step` frames) -> Smooth -> Thickness taper.
  * Vessels: every STL in 镜头设计_v3/assets/anatomy/ (recursive) that is not liver/skin/gallbladder is drawn as a
    second Line Art pass rendered *without* the liver occluding it (x-ray) and composited in vermilion.
    If no vessel meshes exist, the vermilion falls back to an offset halftone block of the liver silhouette.
Scene scale: 1 mm -> 0.01 m (liver ~2 m wide) so the pixel-based ink parameters are comfortable.
"""
import bpy, sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink_common import *
from mathutils.bvhtree import BVHTree

U = 0.01
LIGHT = Vector((-0.60, 0.25, 0.75)).normalized()    # towards the key light: patient's right, behind, up


def shade_vgroup(obj, light_dir, name="shade"):
    """Vertex weights = how much each vertex faces away from the light (world space)."""
    vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
    R = obj.matrix_world.to_3x3()
    for v in obj.data.vertices:
        s = (R @ v.normal).normalized().dot(light_dir)
        vg.add([v.index], max(0.05, min(1.0, 0.5 - 0.8 * s)), "REPLACE")
    return vg


def make_hatch(S, frame, seed):
    """(Re)build the python hatch strokes for the current pose of the liver into GP keyframe `frame`."""
    sc, cam, liver, pivot, px = S["sc"], S["cam"], S["liver"], S["pivot"], S["px"]
    bpy.context.view_layer.update()
    bm = bm_world(liver)
    bvh = BVHTree.FromBMesh(bm)
    rng = np.random.default_rng(seed * 1000 + frame)
    R = pivot.matrix_world.to_3x3()
    size = S["size"]
    famA = slice_chains(bm, R @ Vector((0.20, -0.55, 0.80)), 12 * px)   # rings tilted to the camera -> curved
    famB = slice_chains(bm, R @ Vector((0.80, -0.50, -0.25)), 14 * px)  # crossing family for deep shadow
    hA = hatch_strokes(famA, LIGHT, cam.location, bvh, px, thr=0.02, jitter=0.12, rng=rng, stroke=(60, 220),
                       min_len=14, sparse=(3, 0.5))
    hB = hatch_strokes(famB, LIGHT, cam.location, bvh, px, thr=-0.30, jitter=0.14, rng=rng, stroke=(25, 90),
                       min_len=10, drop=0.1)
    bm.free()
    gph = S["gph"]
    for ln in ("hatchA", "hatchB"):          # rebuilding a pose: drop what was drawn on this keyframe before
        lay = gph.data.layers.get(ln)
        fr = lay and next((f for f in lay.frames if f.frame_number == frame), None)
        if fr and len(fr.drawing.strokes):
            fr.drawing.remove_strokes()
    write_strokes(gph, "hatchA", hA, INK, 0.45 * px, 1.5 * px, frame=frame)
    write_strokes(gph, "hatchB", hB, INK, 0.40 * px, 1.2 * px, frame=frame)
    return len(hA), len(hB)


def build(preview=False, turn=0.0, seed=3, scene=None):
    """Build the whole liver scene. `turn` (radians) spins the liver around its vertical axis (used by the turn test)."""
    sc = scene or reset_scene((960, 540) if preview else (1920, 1080))
    cl, cv, cg = collection("liver"), collection("vessels"), collection("ink")
    liver = import_stl(LIVER_STL, cl, scale=U, name="liver")
    bb = [liver.matrix_world @ Vector(c) for c in liver.bound_box]
    ctr = sum(bb, Vector()) / 8
    anat = anatomy_stls()
    vessels = [import_stl(p, cv, scale=U, name="v_" + n) for p, n in anat["vessels"]]
    pivot = empty("pivot", ctr)
    bpy.context.view_layer.update()
    for o in [liver] + vessels:
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
        hide_from_camera(o)
    pivot.rotation_euler.z = turn
    bpy.context.view_layer.update()

    # camera: anterior view, a little from the patient's right and from below so the inferior border reads;
    # liver pushed to the right of the frame for an editorial layout
    cam = camera(ctr + Vector((-0.8, -5.5, -0.5)), ctr + Vector((0, 0, -0.05)), 50, shift=(-0.13, 0.0))
    px = px_at(cam, ctr)
    size = max((b - ctr).length for b in bb)
    shade_vgroup(liver, LIGHT)

    # --- contour: Line Art, weight follows the shadow
    gp = gp_object("contour", cg)
    m, _, _ = lineart(gp, "contour", cl, INK, 2.5 * px, contour=True, crease=True, crease_deg=120, smooth=0.2)
    m.source_vertex_group = "shade"
    m.vertex_group = "shade"
    m.use_output_vertex_group_match_by_name = True
    ink_mods(gp, px, wobble=2.2, freq=0.09, smooth_steps=5, thick_var=0.7, seed=seed, step=2, overshoot=0.08,
             double=1.6, dash=(46, 1))
    t = gp.modifiers.new("weight", "GREASE_PENCIL_THICKNESS")
    t.vertex_group_name, t.use_weight_factor, t.thickness_factor = "shade", True, 2.4

    # --- hatching (python strokes, real form + light + visibility)
    gph = gp_object("hatch", cg)
    S = dict(sc=sc, cam=cam, liver=liver, vessels=vessels, gp=gp, gph=gph, gpv=None, pivot=pivot, ctr=ctr, cl=cl,
             cv=cv, cg=cg, px=px, size=size)
    n = make_hatch(S, sc.frame_start, seed)
    print("hatch strokes", n)
    ink_mods(gph, px, wobble=1.2, freq=0.15, smooth_steps=3, thick_var=0.3, seed=seed + 11, step=2, taper=False,
             resample=3.0)

    # --- vessels (vermilion Line Art, drawn x-ray: liver is hidden during this pass)
    if vessels:
        gpv = gp_object("vessels_ink", cg)
        lineart(gpv, "vessels", cv, VERMILION, 1.1 * px, contour=True, crease=False)
        ink_mods(gpv, px, wobble=1.6, freq=0.12, smooth_steps=4, thick_var=0.6, seed=seed + 5, step=2,
                 overshoot=0.02)
        S["gpv"] = gpv
    return S


VESSEL_NAMES = {"portal_vein_hepatic": "portal vein", "hepatic_veins": "hepatic veins",
                "hepatic_artery": "hepatic artery", "inferior_vena_cava": "IVC", "abdominal_aorta": "aorta",
                "celiac_trunk": "celiac trunk", "portal_tributaries_splenic_SMV": "splenic v./SMV"}


def add_labels(S, seed=3, leader=True):
    """Editorial marks: clean mono captions against the hand-drawn ink, one hand-drawn vermilion leader."""
    sc, cam = S["sc"], S["cam"]
    k = sc.render.resolution_x / 1920
    lab = collection("labels")
    S["labels"] = lab
    dim = tuple(c * 0.6 for c in INK)
    cam_label(cam, "01 / LIVER", 110 * k, 128 * k, 20 * k, INK, coll=lab)
    cam_label(cam, "LIVER: BodyParts3D FMA7197 (DBCLS, CC BY 4.0), real adult anatomy", 110 * k, 974 * k,
              12 * k, dim, coll=lab)
    if S["vessels"] and leader:
        W, H = sc.render.resolution_x, sc.render.resolution_y
        best = None   # right-most vessel point in a band near the bottom -> leader start
        for o in S["vessels"]:
            for i in range(0, len(o.data.vertices), 3):
                x, y = world_to_pix(cam, o.matrix_world @ o.data.vertices[i].co)
                if 0.80 * H < y < 0.86 * H and 0 < x < W and (best is None or x > best[0]):
                    best = (x, y)
        if best:
            tx, ty = best
            g = annot_gp(cam, lab, depth=1.0)
            lx, ly = 1480 * k, 948 * k
            annot_stroke(g, cam, [(tx + 14 * k, ty + 6 * k), (lx, ly - 26 * k)], VERMILION, 3.0 * k, curve=6 * k)
            annot_stroke(g, cam, [(lx - 6 * k, ly - 18 * k), (lx + 330 * k, ly - 22 * k)], VERMILION, 2.4 * k,
                         curve=-3 * k)
            ink_mods(g, annot_px(cam, g), wobble=0.7, freq=0.12, smooth_steps=3, thick_var=0.4, seed=seed + 21,
                     step=2, taper=True, resample=3.0)
            names = [VESSEL_NAMES.get(o.name[2:], o.name[2:]) for o in S["vessels"]]
            cam_label(cam, "BLOOD VESSELS", lx, ly + 6 * k, 18 * k, VERMILION, coll=lab)
            cam_label(cam, " / ".join(names[:4]), lx, ly + 32 * k, 12 * k, VERMILION, coll=lab)
            cam_label(cam, " / ".join(names[4:]), lx, ly + 52 * k, 12 * k, VERMILION, coll=lab)
            cam_label(cam, "BodyParts3D meshes, same body frame", lx, ly + 72 * k, 12 * k, VERMILION, coll=lab)
    return lab


def annot_px(cam, g):
    return pix_to_cam_local(cam, 1, 0, g["depth"]).x - pix_to_cam_local(cam, 0, 0, g["depth"]).x


def render_passes(S, tmpdir, tag="f", need_matte=None):
    """hatch: python hatching | line: Line Art contour + labels | ves: vessel ink with the liver hidden (x-ray) |
    vmatte: vessel silhouettes | matte: liver silhouette (only needed when there are no vessels)."""
    os.makedirs(tmpdir, exist_ok=True)
    paths = {}
    gps = list(S["cg"].objects)
    meshes = [S["liver"]] + S["vessels"]
    labs = list(S["labels"].objects) if S.get("labels") else []
    def setup(show_gp, cam_meshes=(), hidden=(), labels=False):
        for o in labs:
            o.hide_render = not labels
        for o in gps:
            o.hide_render = o not in show_gp
        for o in meshes:
            o.hide_render = o in hidden
            o.visible_camera = o in cam_meshes
    setup([S["gph"]], hidden=S["vessels"])
    paths["hatch"] = render(os.path.join(tmpdir, f"{tag}_hatch.png"))
    setup([S["gp"]], hidden=S["vessels"], labels=True)
    paths["line"] = render(os.path.join(tmpdir, f"{tag}_line.png"))
    if S["gpv"]:
        setup([S["gpv"]], hidden=[S["liver"]])
        paths["ves"] = render(os.path.join(tmpdir, f"{tag}_ves.png"))
        for o in S["vessels"]:
            set_mat(o, emission_mat("vm", (1, 1, 1)))
        setup([], cam_meshes=S["vessels"], hidden=[S["liver"]])
        paths["vmatte"] = render(os.path.join(tmpdir, f"{tag}_vmatte.png"))
    if need_matte or (need_matte is None and not S["gpv"]):
        set_mat(S["liver"], emission_mat("matte", (1, 1, 1)))
        setup([], cam_meshes=[S["liver"]], hidden=S["vessels"])
        paths["matte"] = render(os.path.join(tmpdir, f"{tag}_matte.png"))
    setup(gps, labels=True)
    return paths


def composite(paths, out, seed=0):
    hatch = load_rgba(paths["hatch"])
    line = load_rgba(paths["line"])
    h, w = hatch.shape[:2]
    k = w / 1920
    stack = []
    if "vmatte" in paths:
        vm = load_rgba(paths["vmatte"])[..., 3]
        # misregistered dot-screen echo of the vessels (print offset), then the white hatching,
        # a black trap around the vessels (knock-out like a screen print), the flat vermilion vessels,
        # and the white contour + labels on top
        stack.append(("mask", halftone(shift(vm, int(12 * k), int(9 * k)) * 0.6, cell=max(3, int(5 * k))), VERMILION))
        stack.append(("rgba", hatch, 0.2, 1.5))
        stack.append(("mask", dilate(vm, max(1, int(3 * k))) * 0.92, BLACK))
        stack.append(("mask", vm, VERMILION))
        # black keylines inside the red (vessel Line Art) so overlapping branches separate like a screen print
        stack.append(("mask", np.clip(load_rgba(paths["ves"])[..., 3] * 1.4, 0, 1) * 0.9, BLACK))
    else:
        matte = load_rgba(paths["matte"])[..., 3]
        hh, ww = np.mgrid[0:h, 0:w].astype(np.float32)
        grad = np.clip(0.15 + 0.5 * (hh / h) + 0.2 * (ww / w), 0, 1)
        m = shift(matte, int(26 * k), int(20 * k)) * grad * 0.6
        stack.append(("mask", halftone(m, cell=max(4, int(8 * k)), angle=0.26), VERMILION))
        stack.append(("rgba", hatch, 0.2, 1.5))
    stack.append(("rgba", line, 0.25, 1.5))
    save_rgb(compose(stack, grain=0.03, seed=seed), out)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    OUT = os.path.abspath(argv[0])
    PREVIEW = "--preview" in argv
    t0 = time.time()
    S = build(preview=PREVIEW)
    add_labels(S)
    tl = time.time()
    p = render_passes(S, os.path.join(os.path.dirname(OUT), "_passes"), "liver")
    composite(p, OUT)
    print(f"TIMING build {tl - t0:.1f}s render+comp {time.time() - tl:.1f}s total {time.time() - t0:.1f}s")
    print("vessels:", [o.name for o in S["vessels"]])
