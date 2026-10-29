"""Option 3 · fog-glass (Blender): a real pane of glass, fogged by breath, with Hong Kong night lights behind it.
Fog and condensation come from fogmask.py (rough + milky where fogged, clear where a finger passed).
The city is real emissive geometry far behind; the camera focuses on the glass, so the city is true lens bokeh.
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
RAW = "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/raw/"
scn = reset()
world(scn, (0.0, 0.0, 0.0))

DG, LENS = 0.9, 35.0
FWm = 36.0 * DG / LENS; FHm = FWm * 9 / 16
GW, GH = FWm * 1.06, FHm * 1.06

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
glass = bpy.context.active_object; glass.scale = (GW, GH, 1)
bpy.ops.object.transform_apply(scale=True)
sol = glass.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.004; sol.offset = 1.0

m, nt, out = mat("fogglass")
tc = nt.nodes.new("ShaderNodeTexCoord")
fimg = nt.nodes.new("ShaderNodeTexImage"); fimg.image = bpy.data.images.load(RAW + f"fog_{A.shot}.png"); fimg.image.colorspace_settings.name = "Non-Color"
himg = nt.nodes.new("ShaderNodeTexImage"); himg.image = bpy.data.images.load(RAW + f"height_{A.shot}.png"); himg.image.colorspace_settings.name = "Non-Color"
for im_ in (fimg, himg):
    im_.extension = "EXTEND"; im_.interpolation = "Cubic"
    nt.links.new(tc.outputs["UV"], im_.inputs["Vector"])
gl = nt.nodes.new("ShaderNodeBsdfPrincipled")
gl.inputs["Base Color"].default_value = (1, 1, 1, 1); gl.inputs["IOR"].default_value = 1.5
gl.inputs["Transmission Weight"].default_value = 1.0
rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.0; rr.inputs["To Max"].default_value = 0.42
nt.links.new(fimg.outputs["Color"], rr.inputs["Value"]); nt.links.new(rr.outputs[0], gl.inputs["Roughness"])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 0.0012
nt.links.new(himg.outputs["Color"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], gl.inputs["Normal"])
# milky scattering of the fog: a translucent white layer weighted by fog density
trl = nt.nodes.new("ShaderNodeBsdfTranslucent"); trl.inputs["Color"].default_value = (0.9, 0.93, 1.0, 1)
dif = nt.nodes.new("ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (0.8, 0.84, 0.95, 1)
mixw = nt.nodes.new("ShaderNodeMixShader"); mixw.inputs[0].default_value = 0.3
nt.links.new(trl.outputs[0], mixw.inputs[1]); nt.links.new(dif.outputs[0], mixw.inputs[2])
fm = nt.nodes.new("ShaderNodeMath"); fm.operation = "MULTIPLY"; fm.inputs[1].default_value = 0.7
nt.links.new(fimg.outputs["Color"], fm.inputs[0])
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(fm.outputs[0], mx.inputs[0]); nt.links.new(gl.outputs[0], mx.inputs[1]); nt.links.new(mixw.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs["Surface"])
glass.data.materials.append(m)

# ---------------------------------------------------------------- the city: emissive lights far behind the glass
random.seed(5)
mats = {
    "blue": [emission("b%d" % i, (0.0, 0.05 + 0.04 * i, 1.0), s) for i, s in enumerate((3, 6, 10))],
    "red": [emission("r%d" % i, (1.0, 0.012, 0.004), s) for i, s in enumerate((4, 8))],
    "bone": [emission("w0", BONE, 3)],
}
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12)
proto = bpy.context.active_object; proto.hide_render = True; proto.hide_viewport = True
proto.data.materials.append(mats["blue"][0])
N = 55
for i in range(N):
    D = random.uniform(4, 45)
    u, v = random.uniform(-0.62, 0.62), random.uniform(-0.40, 0.42)
    p = random.random()
    kind = "red" if p < 0.15 else ("bone" if p < 0.2 else "blue")
    o = proto.copy(); o.data = proto.data; scn.collection.objects.link(o)
    o.hide_render = False; o.hide_viewport = False
    s = random.uniform(0.03, 0.12) * D / 20 * (2.5 if random.random() < 0.08 else 1.0)
    o.location = (u * D * FWm / DG, D, v * D * FWm / DG * 0.9 - 0.15 * D / 20)
    o.scale = (s, s, s)
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = random.choice(mats[kind])
    o.visible_shadow = False
if A.shot == "1-01":
    # a few red lights placed so they are seen through the four finger-lines
    for px_, py_, D_, sz in ((1225, 520, 14, 0.06), (1388, 380, 22, 0.08), (1560, 640, 10, 0.045), (1716, 470, 18, 0.07)):
        o = proto.copy(); o.data = proto.data; scn.collection.objects.link(o); o.hide_render = False
        o.location = ((px_ - 960) / 1920 * FWm * D_ / DG, D_, (540 - py_) / 1920 * FWm * D_ / DG)
        o.scale = (sz * D_ / 10,) * 3
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = mats["red"][0]
# a distant blue glow at street level (sky reflected off the harbour), very soft
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 90, 0), rotation=(math.radians(90), 0, 0))
pl = bpy.context.active_object; pl.scale = (260, 140, 1)
# the night sky over the harbour: a broad cobalt glow behind everything; through fog it becomes a luminous blue field
pm, pnt, pout = mat("sky")
pe = pnt.nodes.new("ShaderNodeEmission"); pe.inputs["Color"].default_value = (0.0, 0.045, 1.0, 1)
ptc = pnt.nodes.new("ShaderNodeTexCoord"); pg = pnt.nodes.new("ShaderNodeTexGradient"); pg.gradient_type = "SPHERICAL"
pmp = pnt.nodes.new("ShaderNodeMapping"); pmp.inputs["Scale"].default_value = (1.6, 2.4, 1); pmp.inputs["Location"].default_value = (0.0, 0.05, 0)
pnt.links.new(ptc.outputs["Object"], pmp.inputs["Vector"]); pnt.links.new(pmp.outputs[0], pg.inputs["Vector"])
pr = pnt.nodes.new("ShaderNodeMapRange"); pr.inputs["To Min"].default_value = 0.0; pr.inputs["To Max"].default_value = 0.025
pnt.links.new(pg.outputs["Fac"], pr.inputs["Value"]); pnt.links.new(pr.outputs[0], pe.inputs["Strength"])
pnt.links.new(pe.outputs[0], pout.inputs["Surface"]); pl.data.materials.append(pm)

# ---------------------------------------------------------------- room side: a dim cold lamp lights the fog from our side
for L_ in (area(scn, "room", 0.8, 1.2, (-0.6, -1.6, 0.7), (0, 0, 0), (0.85, 0.9, 1.0)),
           area(scn, "room2", 0.3, 1.5, (0.8, -1.4, -0.5), (0, 0, 0), (0.75, 0.82, 1.0))):
    L_.visible_glossy = False; L_.visible_transmission = False
# the city's glow reaching the pane from behind: lights the fog (translucent), never seen through the clear lines
bl_ = area(scn, "cityglow", 160.0, 4.0, (0.3, 1.6, -0.5), (0, 0, 0.05), (0.0, 0.06, 1.0), size_y=3.0)
bl_.visible_transmission = False; bl_.visible_glossy = False
rd_ = area(scn, "redglow", 0.0, 0.5, (0.35, 0.5, 0.2), (0.1, 0, 0.0), (1.0, 0.01, 0.004), size_y=0.5)
rd_.visible_transmission = False; rd_.visible_glossy = False
# small hard lamp up-left: the only thing the beads can sparkle with
point(scn, "spark", 6, (-0.9, -1.2, 0.9), (0.9, 0.95, 1.0), radius=0.01)

camera(scn, (0, -DG, 0), (0, 0, 0), lens=LENS, fstop=1.2, focus=DG)
gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
scn.cycles.max_bounces = 12
render(scn, A.out)
