"""1-02 option 'fog': a fogged window pane with 1,412 tally marks and the number wiped into it by a fingertip.
Behind the glass: black, one vermilion lamp and one cobalt lamp. Fog scatters them into a soft glow; the wiped
marks are clear and show the dark room (and sharp bokeh where they cross a lamp). Focus on the glass.
Refs: writing on fogged glass (director's list); Doris Salcedo, Palimpsest (names that appear in water and fade).

blender -b --factory-startup -t 4 -P fog_glass.py -- --mask fog_mask.png --out X.png [--samples 512] [--pct 100]
"""
import bpy, sys, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--mask", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=512)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--yaw", type=float, default=16.0)
ap.add_argument("--fstop", type=float, default=1.8)
ap.add_argument("--look", default="duo", help="duo (red + blue lamps) | quiet (one deep red field from the left, blue only at the edge)")
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
PW, PH = 3.2, 1.8


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


# ---------------------------------------------------------------- the pane
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
pane = bpy.context.active_object; pane.scale = (PW, PH, 1)
bpy.ops.object.transform_apply(scale=True)
# plane rotated +90 about X faces -Y (toward the camera); UV (0,0) bottom-left as seen from the camera
m, nt, out = mat("fogpane")
N = nt.nodes; L = nt.links.new
tc = N.new("ShaderNodeTexCoord")
img = N.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(A.mask); img.image.colorspace_settings.name = "Non-Color"
img.interpolation = "Cubic"
L(tc.outputs["UV"], img.inputs["Vector"])
# fog body: frosted transmission (glows with whatever is behind) + a faint diffuse sheen on the front
# rough refraction, not Lambertian: each lamp blooms into its own halo instead of tinting the whole pane magenta
trl = N.new("ShaderNodeBsdfGlass"); trl.inputs["Color"].default_value = (0.9, 0.9, 0.92, 1)
trl.inputs["Roughness"].default_value = 0.32; trl.inputs["IOR"].default_value = 1.33
dif = N.new("ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (0.5, 0.5, 0.52, 1)
fogmix = N.new("ShaderNodeMixShader"); fogmix.inputs[0].default_value = 0.18
L(trl.outputs[0], fogmix.inputs[1]); L(dif.outputs[0], fogmix.inputs[2])
# fog is not uniform: thinner patches let some light straight through
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 6
L(tc.outputs["Object"], nz.inputs["Vector"])
cr = N.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.35; cr.inputs["From Max"].default_value = 0.75
cr.inputs["To Min"].default_value = 0.0; cr.inputs["To Max"].default_value = 0.06
L(nz.outputs["Fac"], cr.inputs["Value"])
tr = N.new("ShaderNodeBsdfTransparent")
thin = N.new("ShaderNodeMixShader"); L(cr.outputs[0], thin.inputs[0]); L(fogmix.outputs[0], thin.inputs[1]); L(tr.outputs[0], thin.inputs[2])
# clear (wiped) glass: transparent + fresnel gloss; wet edges get a little rough gloss
gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
fr = N.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.33
clear = N.new("ShaderNodeMixShader"); L(fr.outputs[0], clear.inputs[0]); L(tr.outputs[0], clear.inputs[1]); L(gl.outputs[0], clear.inputs[2])
mix = N.new("ShaderNodeMixShader"); L(img.outputs["Color"], mix.inputs[0]); L(thin.outputs[0], mix.inputs[1]); L(clear.outputs[0], mix.inputs[2])
# whole pane: a thin film of gloss on top so the room's light streaks across fog and clear alike
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.2
gl2 = N.new("ShaderNodeBsdfGlossy"); gl2.inputs["Roughness"].default_value = 0.08
top = N.new("ShaderNodeMixShader"); L(lw.outputs["Fresnel"], top.inputs[0]); L(mix.outputs[0], top.inputs[1]); L(gl2.outputs[0], top.inputs[2])
L(top.outputs[0], out.inputs["Surface"])
# condensation bumps: fine Voronoi droplets everywhere, coarser beads along the wiped edges
vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE" if False else "F1"; vo.inputs["Scale"].default_value = 900
L(tc.outputs["Object"], vo.inputs["Vector"])
inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L(vo.outputs["Distance"], inv.inputs[1])
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.6; bmp.inputs["Distance"].default_value = 0.002
L(inv.outputs[0], bmp.inputs["Height"])
for s in (trl, dif, gl, gl2): L(bmp.outputs["Normal"], s.inputs["Normal"])
pane.data.materials.append(m)

# a window frame edge: thin dark mullion at the left so it reads as a window, not a screen
bpy.ops.mesh.primitive_cube_add(size=1, location=(-PW / 2 - 0.04, 0.02, 0)); fr_o = bpy.context.active_object
fr_o.scale = (0.08, 0.06, PH + 0.4)
fm, fnt, fout = mat("frame"); p = fnt.nodes.new("ShaderNodeBsdfPrincipled")
p.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1); p.inputs["Roughness"].default_value = 0.4
fnt.links.new(p.outputs[0], fout.inputs["Surface"]); fr_o.data.materials.append(fm)


# ---------------------------------------------------------------- the room behind: black, two lamps
def lamp(name, color, strength, loc, size, shape="disc", soft=0.0):
    if shape == "disc":
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=size, fill_type="NGON", location=loc, rotation=(math.radians(90), 0, 0))
    else:
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.scale = (size[0], size[1], 1)
    o = bpy.context.active_object; o.name = name
    lm, lnt, lout = mat(name); e = lnt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    lnt.links.new(e.outputs[0], lout.inputs["Surface"]); o.data.materials.append(lm)
    if soft:   # radial falloff: a field with no edge (Turrell / Rothko), strength * (1 - r)^soft
        tc = lnt.nodes.new("ShaderNodeTexCoord"); vm = lnt.nodes.new("ShaderNodeVectorMath"); vm.operation = "MULTIPLY_ADD"
        vm.inputs[1].default_value = (2, 2, 0); vm.inputs[2].default_value = (-1, -1, 0)
        gr = lnt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
        pw = lnt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = soft
        ml = lnt.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; ml.inputs[1].default_value = strength
        lnt.links.new(tc.outputs["Generated"], vm.inputs[0]); lnt.links.new(vm.outputs[0], gr.inputs[0])
        lnt.links.new(gr.outputs["Fac"], pw.inputs[0]); lnt.links.new(pw.outputs[0], ml.inputs[0]); lnt.links.new(ml.outputs[0], e.inputs["Strength"])
    return o


if A.look == "duo":
    lamp("red_lamp", (1.0, 0.006, 0.003), 30.0, (1.3, 9.0, 0.4), 0.55)                         # vermilion, right of centre
    lamp("blue_lamp", (0.0, 0.008, 1.0), 26.0, (-3.6, 10.0, 1.0), (0.25, 3.2), shape="rect")       # tall cobalt strip, far left
    lamp("blue_low", (0.0, 0.01, 0.55), 0.6, (-0.4, 14.0, -2.6), (9.0, 1.2), shape="rect")       # faint cobalt floor bounce
    lamp("bone_dot", (0.95, 0.94, 0.9), 0.9, (3.2, 12.0, 1.6), 0.05)                             # one far white point (bokeh)
else:
    # quiet: one large, low-intensity deep-red field behind the left half (a Rothko block seen through breath on glass);
    # cobalt only as a faint bleed at the far right edge. Everything else is dark.
    lamp("red_field", (0.55, 0.004, 0.002), 2.6, (-2.4, 7.0, 0.4), (4.2, 4.2), shape="rect", soft=2.2)
    lamp("blue_edge", (0.0, 0.006, 0.6), 9.0, (5.6, 8.0, 0.0), (0.3, 3.0), shape="rect")

# front room light: a soft, very dim panel behind the camera, high left: a long sheen across the glass
bpy.ops.mesh.primitive_plane_add(size=1, location=(-2.2, -4.0, 2.2))
k = bpy.context.active_object; k.scale = (2.6, 0.5, 1)
k.rotation_euler = (Vector((0, 0, 0)) - k.location).to_track_quat("Z", "Y").to_euler(); k.visible_camera = False
km, knt, kout = mat("key"); ke = knt.nodes.new("ShaderNodeEmission"); ke.inputs["Strength"].default_value = 7.0 if A.look == "duo" else 1.2
knt.links.new(ke.outputs[0], kout.inputs["Surface"]); k.data.materials.append(km)

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

# ---------------------------------------------------------------- camera: slightly oblique, focus on the glass
cd = bpy.data.cameras.new("cam"); cd.lens = 45
cam = bpy.data.objects.new("cam", cd); scn.collection.objects.link(cam); scn.camera = cam
yaw = math.radians(A.yaw)
tgt = Vector((-0.05, 0, 0.0))
dist = 3.95
cam.location = tgt + Vector((math.sin(yaw) * dist, -math.cos(yaw) * dist, 0.12))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.dof.use_dof = True; cd.dof.focus_object = None
cd.dof.focus_distance = (Vector((-0.55, 0, -0.3)) - cam.location).length; cd.dof.aperture_fstop = A.fstop

# ---------------------------------------------------------------- render
scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        pref.compute_device_type = dev; pref.get_devices(); ok = False
        for dv in pref.devices:
            dv.use = (dv.type == dev); ok |= dv.use
        if ok: break
    except Exception as ex:
        print("device", dev, ex)
scn.cycles.device = "GPU"; scn.cycles.samples = A.samples; scn.cycles.use_denoising = True
scn.cycles.max_bounces = 12; scn.cycles.transparent_max_bounces = 16
scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = A.pct
# Standard, not AgX: AgX desaturates a hot red toward orange (banned); Standard keeps it vermilion
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"; scn.view_settings.exposure = -0.5 if A.look == "duo" else 0.0
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
