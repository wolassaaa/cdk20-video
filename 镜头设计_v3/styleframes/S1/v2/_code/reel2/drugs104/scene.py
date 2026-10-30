"""1-04 v2 (drugs104): two animated gallery shots, Cycles OPTIX, rendered as JPEG sequences.

  A (288 f, 0-9.6 s): two dark plinths. Left: an oversized blister pack of tablets on an acrylic easel, in a
     spotlight. Right: two IV bags on a steel stand whose lines join into one. On "from Nexavar ..." the left
     spot dies and the right spot comes up; the camera drifts right.
  B (342 f, 9.6-21 s): ten frosted glass globes on a long plinth, all lit blood red. Seven go out one by one
     (indices 6,0,9,3,7,2,5); 1,4,8 stay lit. Then a cold blue rim comes up on the seven dark ones.

blender -b --factory-startup -t 4 -P scene.py -- --shot A|B --out DIR/prefix_ [--start N --end N]
        [--samples 96] [--pct 100] [--proj file.json]
"""
import bpy, sys, math, json, argparse
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", default="A")
ap.add_argument("--out", required=True)
ap.add_argument("--start", type=int, default=1)
ap.add_argument("--end", type=int, default=0)
ap.add_argument("--samples", type=int, default=96)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--proj", default="")
A = ap.parse_args(argv)
NFR = {"A": 288, "B": 342}[A.shot]

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    scn.cycles.device = "GPU"
except Exception as e:
    print("GPU fallback", e)
scn.cycles.samples = A.samples
scn.cycles.use_denoising = True
scn.cycles.denoiser = "OPTIX"
scn.cycles.max_bounces = 10; scn.cycles.transmission_bounces = 10; scn.cycles.glossy_bounces = 4
scn.cycles.caustics_refractive = False; scn.cycles.caustics_reflective = False
scn.cycles.seed = 7
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = A.pct
scn.render.fps = 30
scn.frame_start, scn.frame_end = 1, NFR
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "Medium High Contrast"
scn.render.image_settings.file_format = "JPEG"
scn.render.image_settings.quality = 93
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

RED = (1.0, 0.0055, 0.0045, 1)          # blood red, linear: B <= G keeps hot pixels off pink
BLUE = (0.0137, 0.0423, 1.0, 1)         # #1F3BFF linear


# ---------------------------------------------------------------- helpers
def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def principled(name, color, rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0):
    m, nt, out = mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, b


def link(o):
    bpy.context.collection.objects.link(o); return o


def box(name, size, loc, m, bevel=0.0, seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = seg
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def spot(name, loc, target, energy, size_deg, blend, color=(1, 1, 1), radius=0.05):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = energy; ld.spot_size = math.radians(size_deg)
    ld.spot_blend = blend; ld.color = color; ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def area(name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    o = link(bpy.data.objects.new(name, ld)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def key(datablock, path, pts):
    for f, v in pts:
        setattr(datablock, path, v); datablock.keyframe_insert(path, frame=f)


def camera(lens):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens
    cam = link(bpy.data.objects.new("cam", cd)); scn.camera = cam
    return cam


def aim(cam, loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


# shared stage
m_floor, b_floor = principled("floor", (0.012, 0.012, 0.012, 1), rough=0.32)
m_plinth, _ = principled("plinth", (0.022, 0.022, 0.021, 1), rough=0.6)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); bpy.context.active_object.data.materials.append(m_floor)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 4.5, 0), rotation=(math.pi / 2, 0, 0))
bpy.context.active_object.data.materials.append(m_floor)

proj_pts = {}   # name -> object/point for 2D label tracking

# ================================================================ SHOT A
if A.shot == "A":
    PH = 0.95; XL, XR = -0.74, 0.74
    box("plinthL", (0.66, 0.66, PH), (XL, 0, PH / 2), m_plinth, bevel=0.004)
    box("plinthR", (0.66, 0.66, PH), (XR, 0, PH / 2), m_plinth, bevel=0.004)

    # --- blister pack on an acrylic easel (left)
    m_foil, _ = principled("foil", (0.55, 0.55, 0.57, 1), rough=0.42, metal=1.0)
    m_dome, _ = principled("dome", (0.95, 0.96, 1.0, 1), rough=0.06, trans=1.0, ior=1.5)
    m_tab, _ = principled("tablet", (0.80, 0.78, 0.73, 1), rough=0.55, coat=0.3)
    m_acr, _ = principled("acrylic", (0.97, 0.98, 1.0, 1), rough=0.02, trans=1.0, ior=1.49)
    tilt = math.radians(62)
    piv = bpy.data.objects.new("blisterPivot", None); link(piv)
    piv.location = (XL, -0.02, PH + 0.135); piv.rotation_euler = (tilt, 0, 0)
    BW, BH = 0.58, 0.29
    foil = box("foil", (BW, BH, 0.006), (0, 0, 0), m_foil, bevel=0.012, seg=4); foil.parent = piv
    gone = {(0, 0), (1, 0)}   # two tablets already taken
    for r in range(2):
        for c in range(5):
            x = (c - 2) * 0.105; y = (r - 0.5) * 0.13
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.044, location=(x, y, 0.003), segments=40, ring_count=20)
            d = bpy.context.active_object; d.scale = (1.0, 0.8, 0.42); d.data.materials.append(m_dome)
            bpy.ops.object.shade_smooth(); d.parent = piv
            d.visible_shadow = False
            if (r, c) in gone:
                d.scale = (1.0, 0.8, 0.12)   # pushed-through dome
                continue
            bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.014, location=(x, y, 0.011), vertices=48)
            t = bpy.context.active_object; t.scale = (1.0, 0.72, 1.0); t.data.materials.append(m_tab)
            bv = t.modifiers.new("bv", "BEVEL"); bv.width = 0.006; bv.segments = 4
            bpy.ops.object.shade_smooth(); t.parent = piv
    # acrylic back strut (thin, nearly invisible) so the pack leans rather than floats
    st = box("strut", (0.30, 0.012, 0.16), (XL, 0.11, PH + 0.08), m_acr, bevel=0.002)
    st.rotation_euler = (math.radians(-20), 0, 0); st.visible_shadow = False
    proj_pts["objL"] = Vector((XL, 0, PH + 0.13))

    # --- two IV bags on a steel stand, lines joining into one (right)
    m_steel, _ = principled("steel", (0.75, 0.75, 0.77, 1), rough=0.22, metal=1.0)
    m_bag, _ = principled("bag", (0.85, 0.87, 0.92, 1), rough=0.18, trans=1.0, ior=1.4)
    m_fluid, _ = principled("fluid", (0.42, 0.43, 0.45, 1), rough=0.35, trans=0.0)
    m_tube, _ = principled("tube", (0.92, 0.94, 1.0, 1), rough=0.12, trans=0.9, ior=1.4)
    TOP = PH + 0.92
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.012, location=(XR, 0.12, PH + 0.006), vertices=48)
    bpy.context.active_object.data.materials.append(m_steel)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=TOP - PH, location=(XR, 0.12, (TOP + PH) / 2), vertices=24)
    bpy.context.active_object.data.materials.append(m_steel)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.46, location=(XR, 0.12, TOP), rotation=(0, math.pi / 2, 0), vertices=24)
    bpy.context.active_object.data.materials.append(m_steel)
    joins = []
    for s in (-1, 1):
        bx = XR + s * 0.15
        bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.003, location=(bx, 0.12, TOP - 0.018), rotation=(math.pi / 2, 0, 0))
        bpy.context.active_object.data.materials.append(m_steel)
        bag = box("bag", (0.19, 0.045, 0.29), (bx, 0.12, TOP - 0.19), m_bag)
        bv = bag.modifiers.new("bv", "BEVEL"); bv.width = 0.02; bv.segments = 6
        bag.visible_shadow = False
        fl = box("fluid", (0.165, 0.028, 0.20), (bx, 0.12, TOP - 0.225), m_fluid)
        bv = fl.modifiers.new("bv", "BEVEL"); bv.width = 0.012; bv.segments = 6
        fl.visible_shadow = False
        bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=0.05, location=(bx, 0.12, TOP - 0.35), vertices=24)
        bpy.context.active_object.data.materials.append(m_tube)
        joins.append(bx)
    # tubing: each bag's line curves to a Y-joint, one line continues down to the plinth
    cu = bpy.data.curves.new("lines", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0045; cu.bevel_resolution = 4
    jz = PH + 0.32; jx = XR
    for bx in joins:
        sp = cu.splines.new("BEZIER"); sp.bezier_points.add(1)
        p0, p1 = sp.bezier_points
        p0.co = (bx, 0.12, TOP - 0.375); p0.handle_left = (bx, 0.12, TOP - 0.3); p0.handle_right = (bx, 0.12, TOP - 0.52)
        p1.co = (jx, 0.10, jz); p1.handle_left = (jx + (bx - jx) * 0.15, 0.10, jz + 0.12); p1.handle_right = (jx, 0.10, jz - 0.1)
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = (jx, 0.10, jz); p0.handle_left = (jx, 0.10, jz + 0.1); p0.handle_right = (jx, 0.10, jz - 0.12)
    p1.co = (jx - 0.12, -0.08, PH + 0.004); p1.handle_left = (jx - 0.06, -0.03, PH + 0.05); p1.handle_right = (jx - 0.2, -0.12, PH)
    tl = link(bpy.data.objects.new("lines", cu)); tl.data.materials.append(m_tube); tl.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.013, location=(jx, 0.10, jz))
    bpy.context.active_object.data.materials.append(m_tube)
    proj_pts["objR"] = Vector((XR, 0.12, PH + 0.55))

    # --- lights
    sL = spot("spotL", (XL - 0.1, -0.55, 3.3), (XL, 0, PH + 0.12), 260, 17, 0.6, radius=0.08)
    sR = spot("spotR", (XR + 0.1, -0.9, 3.2), (XR, 0.1, PH + 0.6), 0, 20, 0.6, radius=0.08)
    rimR = area("rimR", (XR + 0.3, 1.2, 2.2), (XR, 0.1, PH + 0.6), 0, 1.2)
    fill = area("fill", (0, -3.0, 2.2), (0, 0, 1.2), 2, 3.0)
    # switch: left dies 168-210, right comes up 176-222 (local frames, 30 fps; "from Nexavar" ~5.6 s)
    key(sL.data, "energy", [(1, 200), (168, 200), (210, 5)])
    key(sR.data, "energy", [(1, 0), (176, 0), (222, 70)])
    key(rimR.data, "energy", [(1, 0), (180, 0), (226, 60)])

    cam = camera(40)
    def campos(t):  # t 0..1
        x = -0.16 + 0.32 * t
        return (x, -3.05 + 0.18 * t, 1.80 - 0.04 * t), (x * 0.6, 0, 1.32)
    for f in range(1, NFR + 1, 8):
        t = (f - 1) / (NFR - 1); t = t * t * (3 - 2 * t)
        loc, tg = campos(t); aim(cam, loc, tg)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)

# ================================================================ SHOT B
else:
    PH = 0.80; N = 10; SP = 0.29; R = 0.105
    box("plinth", (N * SP + 0.3, 0.5, PH), (0, 0, PH / 2), m_plinth, bevel=0.004)
    m_shell, _ = principled("shell", (0.95, 0.96, 1.0, 1), rough=0.32, trans=1.0, ior=1.45)
    LIT = {1, 4, 8}
    OUT = [(6, 30), (0, 44), (9, 58), (3, 74), (7, 92), (2, 114), (5, 140)]   # (index, local frame it starts going out)
    outf = dict(OUT); shells = []
    for i in range(N):
        x = (i - (N - 1) / 2) * SP; z = PH + R
        bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=(x, 0, z), segments=64, ring_count=32)
        sh = bpy.context.active_object; sh.data.materials.append(m_shell); bpy.ops.object.shade_smooth()
        sh.visible_shadow = False; sh.name = f"shell{i}"; shells.append(sh.name)
        # inner core: emissive, its own material so it can be keyed
        cm, cnt, cout = mat(f"core{i}")
        em = cnt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = RED
        dk, _b = None, None
        pb = cnt.nodes.new("ShaderNodeBsdfPrincipled")
        pb.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1); pb.inputs["Roughness"].default_value = 0.4
        mx = cnt.nodes.new("ShaderNodeAddShader")
        cnt.links.new(em.outputs[0], mx.inputs[0]); cnt.links.new(pb.outputs[0], mx.inputs[1])
        cnt.links.new(mx.outputs[0], cout.inputs["Surface"])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=R * 0.55, location=(x, 0, z), segments=48, ring_count=24)
        co = bpy.context.active_object; co.data.materials.append(cm); bpy.ops.object.shade_smooth()
        co.visible_shadow = False
        # a point light inside carries the glow onto the plinth (shell ignores shadow rays)
        ld = bpy.data.lights.new(f"pt{i}", "POINT"); ld.color = RED[:3]; ld.shadow_soft_size = R * 0.5
        pl = link(bpy.data.objects.new(f"pt{i}", ld)); pl.location = (x, 0, z)
        ON_E, ON_P = 2.4, 26.0
        if i in LIT:
            em.inputs["Strength"].default_value = ON_E; ld.energy = ON_P
        else:
            f0 = outf[i]
            key(em.inputs["Strength"], "default_value", [(1, ON_E), (f0, ON_E), (f0 + 16, 0.0)])
            key(ld, "energy", [(1, ON_P), (f0, ON_P), (f0 + 16, 0.0)])
        proj_pts[f"g{i}"] = Vector((x, 0, z))

    dark = bpy.data.collections.new("darkShells")
    for i in range(N):
        if i not in LIT: dark.objects.link(bpy.data.objects[shells[i]])
    rim = area("rimBlue", (0, 1.3, 1.6), (0, 0, PH + 0.1), 0, 4.0, color=BLUE[:3])
    rim.light_linking.receiver_collection = dark
    key(rim.data, "energy", [(1, 0), (196, 0), (262, 0)])
    top = area("topBone", (0, -1.0, 3.0), (0, 0, PH), 0, 3.0)
    top.light_linking.receiver_collection = dark
    key(top.data, "energy", [(1, 0), (150, 0), (230, 22)])

    cam = camera(38)
    for f in range(1, NFR + 1, 8):
        t = (f - 1) / (NFR - 1); t = t * t * (3 - 2 * t)
        aim(cam, (0.0, -3.4 + 0.22 * t, 1.30 - 0.16 * t), (0, 0, PH + 0.04 - 0.02 * t))
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)

for o in scn.objects:
    if o.type == "LIGHT": o.visible_camera = False

# ---------------------------------------------------------------- projections (for Remotion labels)
if A.proj:
    res = {}
    for f in range(1, NFR + 1):
        scn.frame_set(f)
        row = {}
        for k, p in proj_pts.items():
            v = world_to_camera_view(scn, scn.camera, p)
            row[k] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
        res[f] = row
    json.dump(res, open(A.proj, "w"))
    print("proj written", A.proj)

end = A.end or NFR
scn.frame_start, scn.frame_end = A.start, end
scn.render.filepath = A.out
import os
if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
else: bpy.ops.render.render(animation=True)
