"""1-02 v2: glass organs on one black plinth. One continuous camera move (510 frames @30fps):
  0-140   close on the glass liver (v1 hero look: red portal vein, blue hepatic veins), slow push
  140-210 pull back: glass lung (red bronchial tree) and glass colon (red lumen) fade in either side -> HK top 3
  320-380 pull back again: oesophagus, stomach, prostate fade in; lung/colon reds drain to clear -> world row
Everything at true relative scale (BodyParts3D, mm), one shared plinth.

blender -b --factory-startup -t 4 -P organs.py -- --out DIR/f_#### [--frames 0-509 | --frame 100] [--samples 48] [--pct 100]
Also writes DIR/../labels.json (projected label anchors per frame) when --labels is given.
"""
import bpy, bmesh, sys, math, argparse, time, json, os
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--frames", default="")
ap.add_argument("--stills", default="", help="comma-separated frames -> OUT_####.png")
ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--thresh", type=float, default=0.02)  # adaptive noise threshold; 0.004 for the clean pass (10-30)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--labels", default="")
ap.add_argument("--labels_only", type=int, default=0)
ap.add_argument("--exposure", type=float, default=0.35)
ap.add_argument("--haze", type=float, default=0.025)
A = ap.parse_args(argv)

ANAT = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/"
V4 = ANAT + "bp3d_v4_groups_stl/"
V3 = ANAT + "bp3d_v3_stl/"
S = 0.01  # 1 unit = 100 mm

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = 30
t0 = time.time()

# ---------------------------------------------------------------- timing (frames)
F_PULL1 = (140, 215)   # liver -> trio
F_PULL2 = (318, 385)   # trio -> six
F_END = 509


def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def ease(f, a, b):
    """smootherstep from frame a to b"""
    x = max(0.0, min(1.0, (f - a) / (b - a))); return x * x * x * (x * (x * 6 - 15) + 10)


# ---------------------------------------------------------------- mesh loading
def load(path, keep=None):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    me = o.data
    for v in me.vertices: v.co = v.co * S   # mm -> units, still in body coords
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    if keep:
        bad = [v for v in bm.verts if not keep(v.co / S)]
        bmesh.ops.delete(bm, geom=bad, context="VERTS")
    bm.to_mesh(me); bm.free()
    return o


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = objs[0]; o.name = name
    return o


def apply_mods(o):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)


def shell(o, voxel, smooth_it=6, decim=None):
    """closed clean skin (voxel remesh) + laplacian smoothing, optional decimate; smooth shading."""
    o.data.remesh_voxel_size = voxel
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.voxel_remesh()
    lap = o.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = smooth_it; lap.lambda_factor = 0.8
    if decim:
        d = o.modifiers.new("dec", "DECIMATE"); d.ratio = decim
    apply_mods(o)
    for p in o.data.polygons: p.use_smooth = True
    return o


def smooth_shade(o):
    for p in o.data.polygons: p.use_smooth = True


# ---------------------------------------------------------------- materials
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def fader(nt, shader_out, out_socket, key):
    """mix(transparent, shader, fac) with fac keyframed -> organ fades in.  key = [(frame, value), ...]"""
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(shader_out, mx.inputs[2])
    nt.links.new(mx.outputs[0], out_socket)
    for f, v in key:
        mx.inputs[0].default_value = v; mx.inputs[0].keyframe_insert("default_value", frame=f)
    return mx


def glass_liquid(name, rgb, density, tint=(1, 1, 1), fade=None, dens_key=None):
    m, nt, out = nodes_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Transmission Weight"].default_value = 1.0
    if "Dispersion" in b.inputs: b.inputs["Dispersion"].default_value = 0.25
    if fade: fader(nt, b.outputs[0], out.inputs["Surface"], fade)
    else: nt.links.new(b.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*rgb, 1)
    va.inputs["Density"].default_value = density
    if dens_key:
        for f, v in dens_key:
            va.inputs["Density"].default_value = v; va.inputs["Density"].keyframe_insert("default_value", frame=f)
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


def ghost(name, fade=None, gloss=0.30, haze=None):
    """v1 liver skin: soap-film fresnel gloss, no refraction + faint forward haze."""
    m, nt, out = nodes_mat(name)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.12
    gl.inputs["Color"].default_value = (0.9, 0.9, 0.9, 1)
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Max"].default_value = gloss
    nt.links.new(lw.outputs["Fresnel"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    if fade: fmx = fader(nt, mx.outputs[0], out.inputs["Surface"], fade)
    else: nt.links.new(mx.outputs[0], out.inputs["Surface"])
    hz = A.haze if haze is None else haze
    if hz > 0:
        vs = nt.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Color"].default_value = (0.8, 0.8, 0.82, 1)
        vs.inputs["Density"].default_value = hz
        vs.inputs["Anisotropy"].default_value = 0.55
        if fade:
            for f, v in fade:
                vs.inputs["Density"].default_value = hz * v; vs.inputs["Density"].keyframe_insert("default_value", frame=f)
        nt.links.new(vs.outputs[0], out.inputs["Volume"])
    return m


# blood red #E8190F -> linear (0.807, 0.0097, 0.0048): transmitted tint with B < G so it never drifts pink
BLOOD = (0.85, 0.010, 0.005)
BLUE = (0.02, 0.10, 1.0)

# ---------------------------------------------------------------- organs
ROW = {}   # name -> dict(parent empty, x, bottom, top, half-width)


def place(name, objs, x, rotz=0.0, lift=0.02, y=0.35):
    """Group objs (body coords) under an empty: centre in x/y, bottom on the plinth (z=lift), rotate about z."""
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.data.vertices:
            c = o.matrix_world @ v.co
            mn = Vector(map(min, mn, c)); mx = Vector(map(max, mx, c))
    c = (mn + mx) / 2
    e = bpy.data.objects.new(name, None); scn.collection.objects.link(e)
    for o in objs:
        o.data.transform(Matrix.Translation(Vector((-c.x, -c.y, -mn.z))))
        o.parent = e
    e.location = (x, y, lift); e.rotation_euler = (0, 0, math.radians(rotz))
    bpy.context.view_layer.update()
    ROW[name] = dict(objs=list(objs), x=x, y=y, w=(mx.x - mn.x) / 2, h=mx.z - mn.z, d=(mx.y - mn.y) / 2, e=e)
    print("placed %-10s w=%.2f h=%.2f d=%.2f" % (name, mx.x - mn.x, mx.z - mn.z, mx.y - mn.y))
    return e


ON = [(0, 1.0)]
IN1 = [(F_PULL1[0] + 10, 0.0), (F_PULL1[0] + 55, 1.0)]       # lung / colon materialise during pull-back 1
IN2 = [(F_PULL2[0] + 5, 0.0), (F_PULL2[0] + 50, 1.0)]        # the rest during pull-back 2
DRAIN = lambda d: [(F_PULL2[0] + 5, d), (F_PULL2[0] + 50, 0.0)]  # reds drain to clear glass for the world row

# --- liver (v1 hero recipe, v4 meshes)
CLIP = {"portal_tributaries_splenic_SMV": lambda c: c.z > 1030 and c.x < 25}
lv = []
warm = glass_liquid("blood", BLOOD, 30.0, tint=(1.0, 0.97, 0.95))
cool = glass_liquid("blue", BLUE, 21.0, tint=(0.92, 0.95, 1.0))
for n, mat in [("portal_vein_hepatic", warm), ("portal_tributaries_splenic_SMV", warm), ("hepatic_veins", cool)]:
    o = load(V4 + n + ".stl", keep=CLIP.get(n)); o.name = n; smooth_shade(o)
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = sd.render_levels = 1
    fd = o.modifiers.new("fat", "DISPLACE"); fd.strength = 0.006; fd.mid_level = 0.0
    o.data.materials.append(mat); lv.append(o)
lp = load(V4 + "liver_parenchyma_segments.stl"); gb = load(V4 + "gallbladder.stl")
liver = join([lp, gb], "liver_skin")
liver.data.remesh_voxel_size = 0.02
bpy.ops.object.select_all(action="DESELECT"); liver.select_set(True); bpy.context.view_layer.objects.active = liver
bpy.ops.object.voxel_remesh()
lap = liver.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = 6; lap.lambda_factor = 0.8
sd = liver.modifiers.new("sub", "SUBSURF"); sd.levels = sd.render_levels = 1
smooth_shade(liver)
liver.data.materials.append(ghost("liver_ghost"))
place("liver", [liver] + lv, 0.0, rotz=22, y=-0.75)

# --- lung: 5 lobes fused into one skin + trachea/bronchial tree in blood red
lobes = [load(V3 + f + ".stl") for f in ("FMA7333", "FMA7383", "FMA7337", "FMA7370", "FMA7371")]
lung = shell(join(lobes, "lung_skin"), 0.022, smooth_it=8, decim=0.5)
lung.data.materials.append(ghost("lung_ghost", fade=IN1))
br = join([load(V3 + "FMA7409.stl"), load(V3 + "FMA7394.stl")], "bronchi")
br = shell(br, 0.008, smooth_it=3, decim=0.5)
br.data.materials.append(glass_liquid("bronchi_red", BLOOD, 34.0, tint=(1.0, 0.97, 0.95), fade=IN1 + [(F_PULL2[0] + 5, 1.0), (F_PULL2[0] + 50, 0.35)], dens_key=DRAIN(34.0)))
place("lung", [lung, br], -3.05, rotz=8)

# --- colorectum: glass wall + blood-red lumen (an inset copy of the skin)
col = shell(join([load(V3 + "FMA14543nsn.stl"), load(V3 + "FMA14544.stl")], "colon_skin"), 0.012, smooth_it=6, decim=0.5)
col.data.materials.append(ghost("colon_ghost", fade=IN1))
lum = col.copy(); lum.data = col.data.copy(); lum.name = "colon_lumen"; scn.collection.objects.link(lum)
lum.data.materials.clear()
ins = lum.modifiers.new("ins", "DISPLACE"); ins.strength = -0.08; ins.mid_level = 0.0
ls_ = lum.modifiers.new("ls", "LAPLACIANSMOOTH"); ls_.iterations = 12; ls_.lambda_factor = 1.0
lum.data.materials.append(glass_liquid("lumen_red", BLOOD, 12.0, tint=(1.0, 0.97, 0.95), fade=IN1 + [(F_PULL2[0] + 5, 1.0), (F_PULL2[0] + 50, 0.0)], dens_key=DRAIN(12.0)))
place("colon", [col, lum], 2.9, rotz=10)

# --- world-row extras: plain glass
st = shell(load(V3 + "FMA7148.stl"), 0.012, smooth_it=6)
st.data.materials.append(ghost("stomach_ghost", fade=IN2))
place("stomach", [st], -5.75, rotz=12)
oe = shell(load(V3 + "FMA7131.stl"), 0.006, smooth_it=4)
oe.data.materials.append(ghost("oes_ghost", fade=IN2))
place("oesophagus", [oe], -7.35, rotz=0)
pr = shell(load(V3 + "FMA9600.stl"), 0.004, smooth_it=4)
pr.data.materials.append(ghost("prostate_ghost", fade=IN2))
place("prostate", [pr], 4.85, rotz=0, lift=0.02)
print("geometry %.1fs" % (time.time() - t0))

# ---------------------------------------------------------------- plinth: one long black slab, top at z = 0
bpy.ops.mesh.primitive_cube_add(size=1)
pl = bpy.context.active_object; pl.name = "plinth"
pl.scale = (30, 3.4, 1.0); pl.location = (-1.5, 0.0, -0.5)
m, nt, out = nodes_mat("plinth")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
b.inputs["Roughness"].default_value = 0.32
b.inputs["Specular IOR Level"].default_value = 0.22
nt.links.new(b.outputs[0], out.inputs["Surface"])
pl.data.materials.append(m)
bev = pl.modifiers.new("bev", "BEVEL"); bev.width = 0.01; bev.segments = 3

# ---------------------------------------------------------------- lights: per-organ vitrine rigs (fixed; the camera always looks +y)
def softbox(name, strength, w, h, loc, aim, color=(1, 1, 1), hard=0.0, key=None):
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    o.location = loc
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = False; o.visible_shadow = False
    m, nt, out = nodes_mat(name + "_m")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 2.0
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"
    nt.links.new(tc.outputs["Object"], sc.inputs[0]); nt.links.new(sc.outputs[0], vm.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHERSTEP"
    mr.inputs["From Min"].default_value = hard; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
    nt.links.new(vm.outputs["Value"], mr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = strength
    if key:
        for f, v in key:
            mu.inputs[1].default_value = strength * v; mu.inputs[1].keyframe_insert("default_value", frame=f)
    nt.links.new(mr.outputs[0], mu.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1)
    nt.links.new(mu.outputs[0], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)
    return o


def rig(name, gain=1.0, key=None):
    r = ROW[name]; x = r["x"]; h = r["h"]; c = Vector((x, r["y"], 0.02 + h / 2))
    k = max(r["w"], h / 2) / 1.05 * 1.25   # liver (w~1.05) -> ~1.25, like v1 hero k at d=3.2
    softbox(name + "_rim", 45.0 * gain, 0.25 * k, 5.0 * k, c + Vector((-2.4 * k, 2.6 * k, 0.6 * k)), c, (0.92, 0.95, 1.0), 0.4, key)
    softbox(name + "_key", 2.2 * gain, 3.5 * k, 2.5 * k, c + Vector((2.6 * k, -2.2 * k, 1.6 * k)), c, (1, 1, 1), 0.0, key)
    softbox(name + "_back", 1.6 * gain, 3.0 * k, 2.0 * k, c + Vector((0.6 * k, 3.6 * k, 0.4 * k)), c, (1, 1, 1), 0.1, key)


rig("liver", 1.0, [(F_PULL1[0], 1.0), (F_PULL1[1], 1.15), (F_PULL2[0], 1.15), (F_PULL2[1], 1.6)])
rig("lung", 1.1, [(F_PULL1[0], 0.0), (F_PULL1[0] + 50, 1.0), (F_PULL2[0] + 5, 1.0), (F_PULL2[0] + 50, 0.6)])
rig("colon", 0.95, [(F_PULL1[0], 0.0), (F_PULL1[0] + 50, 1.0), (F_PULL2[0] + 5, 1.0), (F_PULL2[0] + 50, 0.6)])
for n in ("stomach", "oesophagus", "prostate"):
    rig(n, 0.7, [(F_PULL2[0], 0.0), (F_PULL2[0] + 50, 1.0)])
# a long faint top strip so the plinth edge catches a line of light
PT = softbox("plinth_top", 0.6, 30, 1.5, Vector((-1.5, -3.0, 6.0)), Vector((-1.5, 0.0, 0.0)), (1, 1, 1), 0.2)

PF = softbox("plinth_front", 0.35, 30, 0.6, Vector((-1.5, -7.0, -0.2)), Vector((-1.5, -1.7, -0.5)), (1, 1, 1), 0.3)
lp_ = bpy.data.collections.new("lit_plinth"); lp_.objects.link(pl)
PT.light_linking.receiver_collection = lp_; PF.light_linking.receiver_collection = lp_
# light linking: each vitrine rig lights only its own organ; the plinth sees only its top strip
for n, r in ROW.items():
    lit = bpy.data.collections.new("lit_" + n)
    for o in r["objs"]: lit.objects.link(o)
    for suf in ("_rim", "_key", "_back"):
        scn.objects[n + suf].light_linking.receiver_collection = lit
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

# ---------------------------------------------------------------- camera: baked per frame from smooth params
camd = bpy.data.cameras.new("cam"); camd.lens = 50; camd.sensor_width = 36
cam = bpy.data.objects.new("cam", camd); scn.collection.objects.link(cam); scn.camera = cam
LZ = ROW["liver"]["h"] / 2 + 0.02
# key states: (tx, tz, d, el_deg)
S0 = (-0.70, LZ + 0.05, 6.2, -10.0)    # v1 framing: liver right, type left
S0b = (-0.62, LZ + 0.05, 5.8, -9.0)    # end of slow push
S1 = (-0.55, 1.75, 12.6, 3.0)   # trio, organs in the lower half, type above-left
S1b = (-0.60, 1.80, 13.2, 3.5)
S2 = (-1.55, 2.75, 21.5, 5.0)   # six; row low, type top-left
S2b = (-1.60, 2.80, 22.6, 5.5)


def lerp(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))


def state(f):
    if f <= F_PULL1[0]: return lerp(S0, S0b, smooth(f / F_PULL1[0]) * 0.5 + 0.5 * f / F_PULL1[0])
    if f <= F_PULL1[1]: return lerp(S0b, S1, ease(f, *F_PULL1))
    if f <= F_PULL2[0]: return lerp(S1, S1b, (f - F_PULL1[1]) / (F_PULL2[0] - F_PULL1[1]))
    if f <= F_PULL2[1]: return lerp(S1b, S2, ease(f, *F_PULL2))
    return lerp(S2, S2b, (f - F_PULL2[1]) / (F_END - F_PULL2[1]))


def cam_at(f):
    tx, tz, d, el = state(f); el = math.radians(el)
    tgt = Vector((tx, 0, tz))
    pos = tgt + d * Vector((0, -math.cos(el), math.sin(el)))
    return pos, (tgt - pos).to_track_quat("-Z", "Y").to_euler()


for f in range(0, F_END + 1):
    p, r = cam_at(f)
    cam.location = p; cam.rotation_euler = r
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# shallow DOF only on the close liver; gone once we pull back
camd.dof.use_dof = True
for f, fs, fd in [(0, 2.8, 5.45), (F_PULL1[0], 2.8, 5.05), (F_PULL1[1], 16.0, 12.6), (F_END, 22.0, 22.6)]:
    camd.dof.aperture_fstop = fs; camd.dof.focus_distance = fd
    camd.dof.keyframe_insert("aperture_fstop", frame=f); camd.dof.keyframe_insert("focus_distance", frame=f)

# ---------------------------------------------------------------- label anchors (screen px, per frame)
if A.labels:
    lab = {"fps": 30, "w": 1920, "h": 1080, "organs": {}}
    for n, r in ROW.items():
        lab["organs"][n] = {"base": [], "top": []}
    for f in range(0, F_END + 1):
        scn.frame_set(f)
        for n, r in ROW.items():
            for key, pt in (("base", Vector((r["x"], r["y"], 0.0))), ("top", Vector((r["x"], r["y"], r["h"] + 0.02)))):
                v = world_to_camera_view(scn, cam, pt)
                lab["organs"][n][key].append([round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)])
    json.dump(lab, open(A.labels, "w"))
    print("labels ->", A.labels)
    if A.labels_only: sys.exit(0)

# ---------------------------------------------------------------- render
scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
pref.compute_device_type = "OPTIX"; pref.get_devices()
for d in pref.devices: d.use = (d.type == "OPTIX")
scn.cycles.device = "GPU"
scn.cycles.samples = A.samples
scn.cycles.use_adaptive_sampling = True; scn.cycles.adaptive_threshold = A.thresh
scn.cycles.use_denoising = True; scn.cycles.denoiser = "OPTIX"
scn.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scn.cycles.max_bounces = 16; scn.cycles.transmission_bounces = 16; scn.cycles.glossy_bounces = 6
scn.cycles.transparent_max_bounces = 32; scn.cycles.volume_bounces = 1
scn.cycles.diffuse_bounces = 2
scn.cycles.caustics_refractive = True; scn.cycles.caustics_reflective = False
scn.cycles.blur_glossy = 0.5
scn.cycles.seed = 7; scn.cycles.use_animated_seed = True
scn.render.use_persistent_data = True
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
vs = scn.view_settings; vs.view_transform = "Standard"; vs.look = "None"; vs.exposure = A.exposure
for f, e in [(F_PULL1[0], A.exposure), (F_PULL1[1], A.exposure + 0.3), (F_PULL2[0], A.exposure + 0.3), (F_PULL2[1], A.exposure + 0.45)]:
    vs.exposure = e; vs.keyframe_insert("exposure", frame=f)
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"; scn.render.image_settings.color_depth = "8"

if A.stills:
    for fr in [int(x) for x in A.stills.split(",")]:
        scn.frame_set(fr); scn.render.filepath = A.out + "_%04d.png" % fr
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print("RENDER_TIME %.1fs -> %s" % (time.time() - t1, scn.render.filepath))
elif A.frames:
    a, b = [int(x) for x in A.frames.split("-")]
    step = 1
    if ":" in A.frames: pass
    scn.frame_start = a; scn.frame_end = b; scn.render.filepath = A.out
    t1 = time.time(); bpy.ops.render.render(animation=True)
    print("RENDER_TIME %.1fs (%d frames) -> %s" % (time.time() - t1, b - a + 1, A.out))
