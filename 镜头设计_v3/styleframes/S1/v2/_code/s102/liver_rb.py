"""[s102 copy for 1-02: red portal/arterial vs pure-blue hepatic veins] S1 look development: real liver vascular tree (BodyParts3D, CC BY 4.0) in two looks.

Run headless:
  blender -b --factory-startup -P liver_lookdev.py -- --look glass --shot full --samples 256 --out X.png [--pct 50]
  --look glass : glossy glass tubes, red liquid in portal+arterial tree, clear teal glass in hepatic veins, ghost liver
  --look heat  : grayscale "heat" pass (emission by tube core + glossy highlights + liver volume glow), 16-bit BW PNG;
                 map it with thermal_map.py
"""
import bpy, bmesh, sys, math, argparse, time
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--look", default="glass")
ap.add_argument("--shot", default="full")
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--out", required=True)
ap.add_argument("--subdiv", type=int, default=1)
ap.add_argument("--shiftx", type=float, default=0.0)
ap.add_argument("--cam", default="", help="override: tx,ty,tz,az,el,d,lens,fstop(0=off)")
ap.add_argument("--ivc", type=int, default=0)
ap.add_argument("--heatpass", default="all", help="all | liver (volume glow only) | vessel (tubes only, RGBA alpha)")
ap.add_argument("--exposure", type=float, default=0.35)
ap.add_argument("--hero", type=int, default=0, help="1: s102 hero pass: no hepatic artery, fattened trunks, rim + one soft key")
ap.add_argument("--fatten", type=float, default=0.006, help="hero: push vessel surfaces out along normals (units; 0.01 = 1 mm)")
A = ap.parse_args(argv)

STL = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
CENTER_MM = Vector((-10.35, -122.87, 1105.54))  # liver bbox centre
S = 0.01  # 1 unit = 100 mm

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def load(name, subdiv=0, smooth=True, keep=None):
    bpy.ops.wm.stl_import(filepath=STL + name + ".stl")
    o = bpy.context.selected_objects[0]
    o.name = name
    me = o.data
    for v in me.vertices:
        v.co = (v.co - CENTER_MM) * S
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    if keep:  # keep(mm_vector) -> bool ; drop everything else (open cut ends read like cut glass)
        bad = [v for v in bm.verts if not keep(v.co / S + CENTER_MM)]
        bmesh.ops.delete(bm, geom=bad, context="VERTS")
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if subdiv:
        m = o.modifiers.new("sub", "SUBSURF"); m.levels = subdiv; m.render_levels = subdiv
    return o


# ---------------------------------------------------------------- materials
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out


def glass_liquid(name, liquid_rgb, density, surface_tint=(1, 1, 1), rough=0.03):
    """Clear glass skin + absorbing liquid inside (thickness-dependent colour, like blown-glass vessels)."""
    m, nt, out = nodes_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*surface_tint, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Coat Weight"].default_value = 0.0
    if "Dispersion" in b.inputs: b.inputs["Dispersion"].default_value = 0.25  # faint spectral fringes on rims
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*liquid_rgb, 1)
    va.inputs["Density"].default_value = density
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


def ghost_shell(name):
    """Liver as a soap-film skin (fresnel gloss, no refraction) + faint forward-scattering haze."""
    m, nt, out = nodes_mat(name)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.12
    gl.inputs["Color"].default_value = (0.9, 0.9, 0.9, 1)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Max"].default_value = 0.30
    nt.links.new(lw.outputs["Fresnel"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Color"].default_value = (0.8, 0.8, 0.82, 1)
    vs.inputs["Density"].default_value = 0.025
    vs.inputs["Anisotropy"].default_value = 0.55
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    return m


def heat_vessel(name, level, cam_obj, near, far):
    """Heat = core of tube (facing camera) * level * depth falloff, plus glossy highlight from the lights."""
    m, nt, out = nodes_mat(name)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
    nt.links.new(inv.outputs[0], pw.inputs[0])
    cd = nt.nodes.new("ShaderNodeCameraData")
    dr = nt.nodes.new("ShaderNodeMapRange")
    dr.inputs["From Min"].default_value = near; dr.inputs["From Max"].default_value = far
    dr.inputs["To Min"].default_value = 1.0; dr.inputs["To Max"].default_value = 0.45
    nt.links.new(cd.outputs["View Distance"], dr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(pw.outputs[0], mul.inputs[0]); nt.links.new(dr.outputs[0], mul.inputs[1])
    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = level
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(mul2.outputs[0], em.inputs["Strength"])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.12
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0]); nt.links.new(gl.outputs[0], add.inputs[1])
    # open cut ends: the inside of a tube seen through its cut must stay cold, not flare white
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    blk = nt.nodes.new("ShaderNodeEmission"); blk.inputs["Strength"].default_value = 0.0
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mx.inputs[0])
    nt.links.new(add.outputs[0], mx.inputs[1]); nt.links.new(blk.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def heat_liver(name, strength):
    m, nt, out = nodes_mat(name)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs[0], out.inputs["Surface"])
    ve = nt.nodes.new("ShaderNodeEmission")  # emission as volume = thickness-proportional glow
    ve.inputs["Strength"].default_value = strength
    nt.links.new(ve.outputs[0], out.inputs["Volume"])
    return m


# ---------------------------------------------------------------- geometry
t0 = time.time()
families = {
    "warm": ["portal_vein_hepatic", "portal_tributaries_splenic_SMV"] + ([] if A.hero else ["hepatic_artery"]),
    "cool": ["hepatic_veins"] + (["inferior_vena_cava"] if A.ivc else []),
}
CLIP = {
    "portal_tributaries_splenic_SMV": lambda c: c.z > 1030 and c.x < 25,   # short stub of the trunk, no splenic twig
    "inferior_vena_cava": lambda c: 1045 < c.z < 1186,
}
objs = {}
for fam, names in families.items():
    for n in names:
        objs[n] = (load(n, subdiv=A.subdiv, keep=CLIP.get(n)), fam)
        if A.hero:  # thicker trunks: every tube grows by the same amount, so thin twigs gain proportionally the most body
            d = objs[n][0].modifiers.new("fat", "DISPLACE"); d.strength = A.fatten; d.mid_level = 0.0

liver = load("liver_parenchyma_segments", subdiv=0)
gb = load("gallbladder", subdiv=0)
# fuse liver + gallbladder into one clean closed skin (voxel remesh) so the volume shader is well defined
bpy.ops.object.select_all(action="DESELECT")
liver.select_set(True); gb.select_set(True); bpy.context.view_layer.objects.active = liver
bpy.ops.object.join()
liver.data.remesh_voxel_size = 0.02  # >= segment gaps, so no fins/thorns between segments
bpy.ops.object.voxel_remesh()
lap = liver.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = 6; lap.lambda_factor = 0.8
sub = liver.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
for p in liver.data.polygons: p.use_smooth = True
print("geometry %.1fs" % (time.time() - t0))

# ---------------------------------------------------------------- camera
SHOTS = {
    # target (liver-centred units), azimuth (deg, + toward patient's right), elevation, distance, lens, fstop
    "full":  dict(t=(0.06, 0.0, 0.02), az=22, el=-10, d=4.9, lens=50, f=None),
    "mid":   dict(t=(-0.30, -0.20, -0.10), az=-10, el=-25, d=2.3, lens=60, f=2.0, fp=(0.0, -0.02, -0.33)),
    "close": dict(t=(-0.10, 0.05, -0.34), az=-120, el=-20, d=1.7, lens=55, f=4.0),
}
sh = dict(SHOTS[A.shot])
if A.cam:
    v = [float(x) for x in A.cam.split(",")]
    sh = dict(t=tuple(v[0:3]), az=v[3], el=v[4], d=v[5], lens=v[6], f=v[7] or None)
tgt = Vector(sh["t"])
az, el = math.radians(sh["az"]), math.radians(sh["el"])
pos = tgt + sh["d"] * Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
camd = bpy.data.cameras.new("cam"); camd.lens = sh["lens"]; camd.shift_x = A.shiftx
cam = bpy.data.objects.new("cam", camd); scn.collection.objects.link(cam); scn.camera = cam
cam.location = pos
cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
if sh["f"] and A.look == "glass":
    fp = Vector(sh["fp"]) if sh.get("fp") else tgt  # optional focus point other than the aim point
    camd.dof.use_dof = True; camd.dof.focus_distance = (fp - pos).dot((tgt - pos).normalized()); camd.dof.aperture_fstop = sh["f"]
fwd = (tgt - pos).normalized()
right = fwd.cross(Vector((0, 0, 1))).normalized()
up = right.cross(fwd)


# ---------------------------------------------------------------- lights (camera-relative so every framing gets the same design)
def area(name, power, size, rel, color=(1, 1, 1), shape="RECTANGLE", size_y=None, cam_vis=False):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.color = color
    ld.shape = shape; ld.size = size; ld.size_y = size_y or size
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    p = tgt + right * rel[0] + up * rel[1] + fwd * rel[2]
    o.location = p
    o.rotation_euler = (tgt - p).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = cam_vis
    return o

def softbox(name, strength, w, h, rel, color=(1, 1, 1), hard=0.0):
    """Emissive plane with elliptical smooth falloff: soft-edged studio reflections instead of hard rectangles.
    Invisible to camera, visible to glossy/transmission/diffuse."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    p = tgt + right * rel[0] + up * rel[1] + fwd * rel[2]
    o.location = p
    o.rotation_euler = (tgt - p).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = False; o.visible_shadow = False
    m, nt, out = nodes_mat(name + "_m")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; vm.inputs[1].default_value = (0, 0, 0)
    sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], sc.inputs[0]); nt.links.new(sc.outputs[0], vm.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHERSTEP"
    mr.inputs["From Min"].default_value = hard; mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
    nt.links.new(vm.outputs["Value"], mr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = strength
    nt.links.new(mr.outputs[0], mu.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1)
    nt.links.new(mu.outputs[0], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)
    return o


def point(name, power, rel, radius=0.01, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "POINT"); ld.energy = power; ld.shadow_soft_size = radius; ld.color = color
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    o.location = tgt + right * rel[0] + up * rel[1] + fwd * rel[2]
    return o


if A.hero:
    k = sh["d"] / 5.0 + 0.6
    # slow light: one long rim from behind-left, one big soft key from front-right, a faint back glow through the glass
    softbox("rim", 45.0, 0.25 * k, 5.0 * k, (-2.4 * k, 0.6 * k, 2.6 * k), (0.92, 0.95, 1.0), hard=0.4)
    softbox("key", 2.2, 3.5 * k, 2.5 * k, (2.6 * k, 1.6 * k, -2.2 * k), (1.0, 1.0, 1.0), hard=0.0)
    softbox("back", 1.6, 3.0 * k, 2.0 * k, (0.6 * k, 0.4 * k, 3.6 * k), (1.0, 1.0, 1.0), hard=0.1)
else:
    k = sh["d"] / 5.0 + 0.6  # scale rig with framing
    # big soft back panel: seen through the glass (tubes glow from within), never seen directly
    softbox("back", 6.0, 4.0 * k, 3.0 * k, (0.8 * k, 1.0 * k, 3.5 * k), (1.0, 1.0, 1.0), hard=0.1)
    # two long thin strips, high-left (cool) and low-right (warm): streak highlights + rims on the liver skin
    softbox("stripL", 30.0, 0.22 * k, 4.0 * k, (-2.8 * k, 1.2 * k, 1.0 * k), (0.92, 0.95, 1.0), hard=0.5)
    softbox("stripR", 18.0, 0.18 * k, 3.4 * k, (3.0 * k, -0.4 * k, 1.3 * k), (1.0, 0.96, 0.94), hard=0.5)
    # overhead front softbox (very weak) so front faces of tubes are not dead black
    softbox("top", 1.2, 2.5 * k, 1.2 * k, (-0.6 * k, 3.0 * k, -2.0 * k), (1.0, 0.97, 0.94), hard=0.2)
    # small sparkle sources for pin-point highlights
    point("spark1", 60 * k * k, (-1.6 * k, 2.0 * k, -1.8 * k), 0.01)
    point("spark2", 40 * k * k, (2.2 * k, 1.6 * k, 0.4 * k), 0.01, (0.9, 0.97, 1.0))

# ---------------------------------------------------------------- assign looks
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

if A.look == "glass":
    warm = glass_liquid("blood", (0.85, 0.03, 0.01), 110.0, surface_tint=(1.0, 0.97, 0.95))
    cool = glass_liquid("blue", (0.02, 0.10, 1.0), 70.0, surface_tint=(0.92, 0.95, 1.0))
    for o, fam in objs.values():
        o.data.materials.append(warm if fam == "warm" else cool)
    liver.data.materials.append(ghost_shell("ghost"))
else:
    near = sh["d"] - 1.2 * (sh["d"] / 5 + 0.3); far = sh["d"] + 1.2 * (sh["d"] / 5 + 0.3)
    lv = (0.55, 0.45)
    hw = heat_vessel("hot", lv[0], cam, near, far)
    hc = heat_vessel("hot2", lv[1], cam, near, far)
    for o, fam in objs.values():
        o.data.materials.append(hw if fam == "warm" else hc)
    liver.data.materials.append(heat_liver("warmliver", 0.18))  # constant: glow ~ tissue thickness
    for l in [o for o in scn.objects if o.type == "LIGHT"]:
        l.data.energy *= 0.35
    for o in scn.objects:
        if o.name in ("back", "top"): o.hide_render = True  # heat pass: only strip/sparkle highlights
    if A.heatpass == "liver":
        for o, fam in objs.values(): o.hide_render = True
    elif A.heatpass == "vessel":
        liver.hide_render = True

# ---------------------------------------------------------------- render settings
scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        pref.compute_device_type = dev; pref.get_devices()
        ok = False
        for d in pref.devices:
            d.use = (d.type == dev); ok |= d.use
        if ok: break
    except Exception as e:
        print("device", dev, e)
scn.cycles.device = "GPU"
scn.cycles.samples = A.samples
scn.cycles.use_denoising = True
scn.cycles.denoiser = "OPENIMAGEDENOISE"
scn.cycles.max_bounces = 24; scn.cycles.transmission_bounces = 24; scn.cycles.glossy_bounces = 8
scn.cycles.transparent_max_bounces = 32; scn.cycles.volume_bounces = 2
scn.cycles.volume_step_rate = 1.0
scn.cycles.caustics_refractive = True; scn.cycles.caustics_reflective = True
scn.cycles.blur_glossy = 0.5
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
scn.render.film_transparent = (A.look == "heat" and A.heatpass == "vessel")
vs = scn.view_settings
if A.look == "glass":
    vs.view_transform = "AgX"
    try: vs.look = "AgX - Punchy"
    except Exception as e: print("look", e)
    vs.exposure = A.exposure
    scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
    scn.render.image_settings.color_depth = "8"
else:
    vs.view_transform = "Standard"; vs.look = "None"; vs.exposure = 0.0
    scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGBA" if A.heatpass == "vessel" else "BW"
    scn.render.image_settings.color_depth = "16"
scn.render.filepath = A.out
t1 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_TIME %.1fs (total %.1fs) -> %s" % (time.time() - t1, time.time() - t0, A.out))
