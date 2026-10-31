"""HKBU SCIE1007 coursework science video. Hands T4: the real CDK20 surface half sunk in ash, cold and black, one hand touches it, gold runs out of the touch along the real creases.
The hand and the gold are metaphor. The surface and its low-confidence tail (conf attribute, pLDDT below 0.7, left as dull ash) are real data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_kit import *

sc, ob, cam = scene(samples=192, with_protein=True)
catcher(0)
SC = 1.62
VIEW = Vector((0.15, -0.25, 1.0)).normalized()
ob.scale = (SC, SC, SC)
ob.rotation_mode = "QUATERNION"
ob.rotation_quaternion = (VIEW.rotation_difference(Vector((0, 0, 1))))
ob.rotation_quaternion = Quaternion((0, 0, 1), math.radians(164)) @ ob.rotation_quaternion
CX, CY = -1.4, 0.75
ob.location = (CX, CY, 1.0)
bpy.context.view_layer.update()
TX, TY = 2.55, -1.15
hit, tl_, _, _, _, _ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), (TX, TY, 30), (0, 0, -1))
print("touch hit", hit, tl_)
TOUCH = Vector((TX, TY, tl_.z))

m = bpy.data.materials.new("mass")
m.use_nodes = True
nt = m.node_tree
N, L = nt.nodes, nt.links
b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
b.inputs["Roughness"].default_value = 0.26
geo = N.new("ShaderNodeNewGeometry")
ao = N.new("ShaderNodeAmbientOcclusion")
ao.samples = 12
ao.inputs["Distance"].default_value = 1.1
ao.inputs["Color"].default_value = (1, 1, 1, 1)
# gold mask: crevices only, and only near the touch
ram = N.new("ShaderNodeMapRange")
ram.inputs["From Min"].default_value, ram.inputs["From Max"].default_value = 0.30, 0.47
ram.inputs["To Min"].default_value, ram.inputs["To Max"].default_value = 1.0, 0.0
L.new(ao.outputs["AO"], ram.inputs["Value"])
dist = N.new("ShaderNodeVectorMath")
dist.operation = "DISTANCE"
dist.inputs[1].default_value = tuple(TOUCH)
L.new(geo.outputs["Position"], dist.inputs[0])
fade = N.new("ShaderNodeMapRange")
fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = 4.2, 9.6
fade.inputs["To Min"].default_value, fade.inputs["To Max"].default_value = 1.0, 0.0
L.new(dist.outputs["Value"], fade.inputs["Value"])
nz = N.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 1.1, 6
L.new(geo.outputs["Position"], nz.inputs["Vector"])
wob = N.new("ShaderNodeMath")
wob.operation = "MULTIPLY"
L.new(fade.outputs[0], wob.inputs[0])
wob2 = N.new("ShaderNodeMapRange")
wob2.inputs["From Min"].default_value, wob2.inputs["From Max"].default_value = 0.32, 0.58
L.new(nz.outputs[0], wob2.inputs["Value"])
L.new(wob2.outputs[0], wob.inputs[1])
gm = N.new("ShaderNodeMath")
gm.operation = "MULTIPLY"
gm.use_clamp = True
L.new(ram.outputs[0], gm.inputs[0])
ad = N.new("ShaderNodeMath")
ad.operation = "ADD"
ad.use_clamp = True
L.new(fade.outputs[0], ad.inputs[0])
L.new(wob.outputs[0], ad.inputs[1])
sq = N.new("ShaderNodeMath")
sq.operation = "POWER"
sq.inputs[1].default_value = 2.2
L.new(ad.outputs[0], sq.inputs[0])
L.new(sq.outputs[0], gm.inputs[1])
# dull tail: real pLDDT below 0.7 stays ash, undecided
at = N.new("ShaderNodeAttribute")
at.attribute_name, at.attribute_type = "conf", "GEOMETRY"
tl = N.new("ShaderNodeMapRange")
tl.inputs["From Min"].default_value, tl.inputs["From Max"].default_value = 0.66, 0.72
tl.inputs["To Min"].default_value, tl.inputs["To Max"].default_value = 1.0, 0.0
L.new(at.outputs["Fac"], tl.inputs["Value"])
g = N.new("ShaderNodeBsdfPrincipled")
g.inputs["Base Color"].default_value = (1.0, 0.70, 0.24, 1)
g.inputs["Metallic"].default_value = 1.0
g.inputs["Roughness"].default_value = 0.30
g.inputs["Emission Color"].default_value = (1.0, 0.58, 0.14, 1)
g.inputs["Emission Strength"].default_value = 0.22
d = N.new("ShaderNodeBsdfPrincipled")
d.inputs["Base Color"].default_value = (0.20, 0.20, 0.205, 1)
d.inputs["Roughness"].default_value = 0.95
mx1 = N.new("ShaderNodeMixShader")
L.new(tl.outputs[0], mx1.inputs[0])
L.new(b.outputs[0], mx1.inputs[1])
L.new(d.outputs[0], mx1.inputs[2])
mx2 = N.new("ShaderNodeMixShader")
L.new(gm.outputs[0], mx2.inputs[0])
L.new(mx1.outputs[0], mx2.inputs[1])
L.new(g.outputs[0], mx2.inputs[2])
L.new(mx2.outputs[0], N["Material Output"].inputs["Surface"])
ob.data.materials.append(m)

NOHAND = os.environ.get("NOHAND") == "1"
h = Hand(curl=[(5, 12, 10), (34, 52, 28), (44, 62, 30), (50, 70, 30)], thumb=(-34, 26), lift=TOUCH.z + 0.62)
ANG, S = 52.0, 1.05
t0 = h.tip(0, (0, 0, 0), ANG, False, S)
loc = (TOUCH.x - t0[0], TOUCH.y - t0[1], 0)
if not NOHAND:
    h.add(loc, ANG, False, S, skin(name="s1"), name="ha")
# passes for the motion test: the same surface and camera, split so numpy can grow the gold and the light
PASS = os.environ.get("PASS", "")
if os.environ.get("RES4K") == "1":
    sc.render.resolution_percentage = 200
if PASS:
    out = N["Material Output"].inputs["Surface"]
    sc.render.film_transparent = True
    if PASS == "nogold":
        L.remove(gm.outputs[0].links[0])
        mx2.inputs[0].default_value = 0.0
    elif PASS == "allgold":
        L.remove(gm.outputs[0].links[0])
        L.new(ram.outputs[0], mx2.inputs[0])
    else:
        e = N.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.0
        if PASS == "dist":
            sc_ = N.new("ShaderNodeMath")
            sc_.operation = "DIVIDE"
            sc_.inputs[1].default_value = 14.0
            L.new(dist.outputs["Value"], sc_.inputs[0])
            L.new(sc_.outputs[0], e.inputs["Color"])
        else:
            L.new(ram.outputs[0], e.inputs["Color"])
        L.new(e.outputs[0], out)
        sc.view_settings.view_transform = "Raw"
        sc.render.image_settings.color_depth = "16"
        sc.cycles.samples = 8
        sc.cycles.use_denoising = False
        for o in list(sc.objects):
            if o.is_shadow_catcher:
                bpy.data.objects.remove(o)
sc.render.filepath = os.path.join(RAW, "t4_4k.png" if os.environ.get("RES4K") == "1" else (f"t4_{PASS}.png" if PASS else ("t4_mass.png" if NOHAND else "t4.png")))
bpy.ops.render.render(write_still=True)
print("t4 done", tuple(TOUCH), loc)
