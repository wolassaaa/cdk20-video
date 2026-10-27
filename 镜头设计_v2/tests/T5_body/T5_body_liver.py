"""T5 feasibility test: hologram body with the real liver mesh inside.

Body and liver share the BodyParts3D frame (mm, feet at z=0, anterior = -y, patient's right = -x), so the liver
(FMA7197) sits at its anatomical position. With a skin STL (FMA7163, BodyParts3D, CC BY-SA 2.1 JP) the real body
surface is used; without it a skin-modifier mannequin is built from a simple skeleton as a fallback.

Run: blender -b -P T5_body_liver.py -- <liver.stl> <out_png> [skin.stl]
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
LIVER, OUT = argv[0], argv[1]
SKIN = argv[2] if len(argv) > 2 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device, sc.cycles.samples = "GPU", 512
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Base Contrast"
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.002, 0.003, 0.006, 1)
sc.world = w

# ---- mannequin skeleton: (name, position, skin radius x, skin radius y)
J = {
    "pelvis": ((0, -0.10, 0.95), 0.155, 0.10), "spine": ((0, -0.11, 1.12), 0.145, 0.10),
    "chest": ((0, -0.10, 1.30), 0.165, 0.11), "neck": ((0, -0.09, 1.48), 0.055, 0.055),
    "head": ((0, -0.08, 1.60), 0.085, 0.10), "crown": ((0, -0.08, 1.69), 0.06, 0.07),
}
for s, x in (("R", -1), ("L", 1)):
    J.update({
        f"sho{s}": ((x * 0.19, -0.10, 1.40), 0.06, 0.06), f"elb{s}": ((x * 0.25, -0.09, 1.13), 0.045, 0.045),
        f"wri{s}": ((x * 0.27, -0.08, 0.89), 0.035, 0.03), f"hand{s}": ((x * 0.275, -0.08, 0.80), 0.04, 0.02),
        f"hip{s}": ((x * 0.10, -0.10, 0.90), 0.085, 0.085), f"kne{s}": ((x * 0.11, -0.11, 0.50), 0.055, 0.055),
        f"ank{s}": ((x * 0.11, -0.10, 0.09), 0.04, 0.04), f"toe{s}": ((x * 0.11, -0.20, 0.03), 0.035, 0.025),
    })
E = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("neck", "head"), ("head", "crown")]
for s in "RL":
    E += [("chest", f"sho{s}"), (f"sho{s}", f"elb{s}"), (f"elb{s}", f"wri{s}"), (f"wri{s}", f"hand{s}"),
          ("pelvis", f"hip{s}"), (f"hip{s}", f"kne{s}"), (f"kne{s}", f"ank{s}"), (f"ank{s}", f"toe{s}")]
if SKIN:
    bpy.ops.wm.stl_import(filepath=SKIN)
    body = bpy.context.selected_objects[0]
    body.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.shade_smooth()
else:
    names = list(J)
    me = bpy.data.meshes.new("body")
    me.from_pydata([J[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in E], [])
    body = bpy.data.objects.new("body", me)
    sc.collection.objects.link(body)
    body.modifiers.new("skin", "SKIN")
    for i, n in enumerate(names):
        me.skin_vertices[0].data[i].radius = (J[n][1], J[n][2])
    me.skin_vertices[0].data[names.index("pelvis")].use_root = True
    sub = body.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 3
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.shade_smooth()

def holo(name, color, strength, edge):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = edge
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    nt.links.new(pw.outputs[0], mix.inputs["Fac"])
    nt.links.new(t.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

body.data.materials.append(holo("body", (0.30, 0.82, 1.0), 1.6, 0.3))

# ---- the real liver (BodyParts3D FMA7197, mm -> m), warm and solid so it reads through the hologram skin
bpy.ops.wm.stl_import(filepath=LIVER)
liver = bpy.context.selected_objects[0]
liver.scale = (0.001, 0.001, 0.001)
bpy.ops.object.shade_smooth()
lm = bpy.data.materials.new("liver")
lm.use_nodes = True
b = lm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.42, 0.06, 0.04, 1)
b.inputs["Roughness"].default_value = 0.4
b.inputs["Subsurface Weight"].default_value = 0.25
b.inputs["Subsurface Radius"].default_value = (0.02, 0.006, 0.004)
b.inputs["Coat Weight"].default_value = 0.3
b.inputs["Emission Color"].default_value = (0.9, 0.18, 0.08, 1)
b.inputs["Emission Strength"].default_value = 0.25
liver.data.materials.append(lm)

# faint scan rings at liver height
lc = Vector((-0.018, -0.117, 1.117))
for k, (r, z) in enumerate(((0.26, 1.06), (0.28, 1.12), (0.26, 1.18))):
    bpy.ops.mesh.primitive_torus_add(location=(0, -0.10, z), major_radius=r, minor_radius=0.0012, major_segments=160, minor_segments=6)
    rm = bpy.data.materials.new(f"ring{k}")
    rm.use_nodes = True
    rm.node_tree.nodes.clear()
    e = rm.node_tree.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1.0, 0.55, 0.3, 1)
    e.inputs["Strength"].default_value = 3.0
    rm.node_tree.links.new(e.outputs[0], rm.node_tree.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    bpy.context.object.data.materials.append(rm)

for name, loc, e, col in (("key", (1.2, -2.0, 2.0), 120, (1, 0.95, 0.9)), ("rim", (-1.5, 1.2, 1.8), 120, (0.6, 0.8, 1)), ("fill", (-1.2, -1.8, 0.8), 30, (1, 0.9, 0.8))):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.color, ld.size = e, col, 1.2
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = (lc - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(lo)

cd = bpy.data.cameras.new("cam")
cd.lens = 50
cd.dof.use_dof, cd.dof.aperture_fstop = True, 2.8
cam = bpy.data.objects.new("cam", cd)
cam.location = (-0.75, -1.85, 1.30)  # front, slightly from the body's right side so the right lobe faces us
cam.rotation_euler = (Vector((0, -0.10, 1.22)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.dof.focus_distance = (cam.location - lc).length
sc.collection.objects.link(cam)
sc.camera = cam

import os
sys.path.append(os.environ.get("CLIP_HELPER_DIR", ""))
if os.environ.get("CLIP_SECONDS"):
    from clip_anim import render_clip  # moving version for the music test
    render_clip(sc, cam, (0, -0.10, 1.22))
else:
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
print("DONE")
