"""HKBU SCIE1007 coursework science video. T4 of the darkroom direction: the AlphaFold CDK20 surface rising out of a wash tray as a blueprint.

The white lines are planes through the model, so they are contour lines of the real surface; line strength follows the real per-vertex pLDDT carried in cdk20_surface.npz. The water line is staging only.
Cyanotype paper is washed in water and is printed under UV, so this is the one lamp in the film that is not safelight. Real light, real liquid, one frame.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *


def extra(ap):
    ap.add_argument("--water", type=float, default=0.55)  # water level in model-y units (0.1 A)
    ap.add_argument("--name", default="t4")
    ap.add_argument("--tilt", type=float, default=-26)
    ap.add_argument("--dye", type=float, default=0.0)
    ap.add_argument("--mode", default="full")  # full, nolines (the form before it develops) or conf (pLDDT pass for the reveal in motion.py)


A = dr.args(extra)
SC = 0.1
D = np.load(os.path.join(V3, "styleframes", "S2plus", "_work", "cdk20_surface.npz"))
v0, quads, conf = D["verts"] * SC, D["quads"], D["conf"]
sc = dr.setup(A.samples, A.pct, bounces=10)

# upright: model y is up, so the plane contours run level like the water line; low-confidence tail goes down and away
R = Vector((0.20, 0.96, 0.18)).normalized()
v = np.stack([v0[:, 0], -v0[:, 2], v0[:, 1]], -1)
t_ = math.radians(A.tilt)
ca, sa = math.cos(t_), math.sin(t_)
v = np.stack([v[:, 0], ca * v[:, 1] + sa * v[:, 2], -sa * v[:, 1] + ca * v[:, 2]], -1)   # lean the top toward the lens
z_shift = -A.water
v[:, 2] += z_shift
me = bpy.data.meshes.new("cdk20")
me.from_pydata(v.tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
me.update()
ob = link(bpy.data.objects.new("cdk20", me))

# blueprint skin
m, nt, out = new_mat("blueprint")
Ln = nt.links.new
geo, at = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeAttribute")
at.attribute_name, at.attribute_type = "conf", "GEOMETRY"


def op(kind, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation, n.use_clamp = kind, clamp
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            Ln(x, n.inputs[i])
    return n.outputs[0]


def ramp(a, lo, hi):
    n = nt.nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP"
    Ln(a, n.inputs["Value"])
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
    return n.outputs["Result"]


dotn = nt.nodes.new("ShaderNodeVectorMath")
dotn.operation = "DOT_PRODUCT"
Ln(geo.outputs["Position"], dotn.inputs[0])
dotn.inputs[1].default_value = tuple(Vector((0.16, 0.34, 0.93)).normalized())
PITCH = 0.05
s = op("MULTIPLY", dotn.outputs["Value"], 1 / PITCH)
tri = op("ABSOLUTE", op("SUBTRACT", op("MULTIPLY", op("FRACT", s), 2.0), 1.0))
shn = nt.nodes.new("ShaderNodeVectorMath")
shn.operation = "DOT_PRODUCT"
Ln(geo.outputs["Normal"], shn.inputs[0])
shn.inputs[1].default_value = tuple(Vector((-0.78, -0.42, 0.46)).normalized())
shade = op("MAXIMUM", shn.outputs["Value"], 0.0)
sure = ramp(at.outputs["Fac"], 0.50, 0.80)
width = op("MULTIPLY", op("ADD", 0.05, op("MULTIPLY", op("POWER", shade, 1.5), 0.30)), op("ADD", 0.22, op("MULTIPLY", sure, 0.78)))
line = op("LESS_THAN", tri, width)
cr = nt.nodes.new("ShaderNodeMix")
cr.data_type = "RGBA"
Ln(sure, cr.inputs[0])
cr.inputs["A"].default_value, cr.inputs["B"].default_value = lin("081A3C"), lin("1A5AA8")
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value, nz.inputs["Roughness"].default_value = 3.2, 8, 0.62
Ln(geo.outputs["Position"], nz.inputs["Vector"])
mt = nt.nodes.new("ShaderNodeMix")
mt.data_type, mt.blend_type = "RGBA", "MULTIPLY"
mt.inputs[0].default_value = 0.85
Ln(cr.outputs["Result"], mt.inputs["A"])
gm = nt.nodes.new("ShaderNodeMapRange")
Ln(nz.outputs[0], gm.inputs["Value"])
gm.inputs["From Min"].default_value, gm.inputs["From Max"].default_value = 0.32, 0.68
gm.inputs["To Min"].default_value, gm.inputs["To Max"].default_value = 0.45, 1.25
Ln(gm.outputs[0], mt.inputs["B"])
c2 = nt.nodes.new("ShaderNodeMix")
c2.data_type = "RGBA"
Ln(line, c2.inputs[0])
Ln(mt.outputs["Result"], c2.inputs["A"])
c2.inputs["B"].default_value = (0.92, 0.95, 1.0, 1)
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
Ln(c2.outputs["Result"], b.inputs["Base Color"])
# just above the water the skin is still wet
zp = nt.nodes.new("ShaderNodeSeparateXYZ")
Ln(geo.outputs["Position"], zp.inputs[0])
wet = nt.nodes.new("ShaderNodeMapRange")
wet.interpolation_type = "SMOOTHSTEP"
Ln(zp.outputs["Z"], wet.inputs["Value"])
wet.inputs["From Min"].default_value, wet.inputs["From Max"].default_value = 0.0, 0.85
wet.inputs["To Min"].default_value, wet.inputs["To Max"].default_value = 0.14, 0.78
Ln(wet.outputs[0], b.inputs["Roughness"])
b.inputs["Specular IOR Level"].default_value = 0.42
Ln(b.outputs[0], out.inputs["Surface"])
me.materials.append(m)

# tray with a blueprint sheet on its floor, so the blue fills the frame from below
ink = pbr("tray", lin("05070C"), rough=0.35, spec=0.5)
TX, TY, DEPTH = 11.0, 7.6, 2.6
box("wallB", (-TX, TY, -DEPTH), (TX, TY + 0.5, 0.32), ink)
box("wallL", (-TX - 0.5, -TY, -DEPTH), (-TX, TY, 0.32), ink)
box("wallR", (TX, -TY, -DEPTH), (TX + 0.5, TY, 0.32), ink)
box("wallF", (-TX, -TY - 0.5, -DEPTH), (TX, -TY, 0.32), ink)
sheet("floor", TX * 2, TY * 2, loc=(0, 0, -DEPTH), nx=1, ny=1, mat=dr.paper_mat("floor", os.path.join(WORK, "blue_floor.png"), rough=0.7, spec=0.3))
box("table", (-40, -40, -DEPTH - 0.6), (40, 40, -DEPTH - 0.05), pbr("bench", lin("030303"), rough=0.5))
lq = box("liquid", (-TX + 0.005, -TY + 0.005, -DEPTH + 0.005), (TX - 0.005, TY - 0.005, 0), dr.liquid("wash", tint=(0.10, 0.40, 0.92), density=1.25, rings=(1.0, 0.0), ring_scale=0.30, ring_amp=0.004, noise_amp=0.0))
lq.data.update()
if A.dye:
    # cyanotype bleeds a little dye when it is washed: a thin scattering cloud under the surface, fixed in place
    vm = lq.data.materials[0]
    vn = vm.node_tree
    vout = [n for n in vn.nodes if n.type == "OUTPUT_MATERIAL"][0]
    vabs = vout.inputs["Volume"].links[0].from_node
    pos = vn.nodes.new("ShaderNodeNewGeometry")
    nz_ = vn.nodes.new("ShaderNodeTexNoise")
    nz_.inputs["Scale"].default_value, nz_.inputs["Detail"].default_value, nz_.inputs["Roughness"].default_value = 0.42, 7, 0.58
    nz_.inputs["Distortion"].default_value = 1.3
    vn.links.new(pos.outputs["Position"], nz_.inputs["Vector"])
    th = vn.nodes.new("ShaderNodeMapRange")
    th.interpolation_type = "SMOOTHSTEP"
    vn.links.new(nz_.outputs[0], th.inputs["Value"])
    th.inputs["From Min"].default_value, th.inputs["From Max"].default_value = 0.47, 0.72
    th.inputs["To Min"].default_value, th.inputs["To Max"].default_value = 0.0, A.dye
    sc_ = vn.nodes.new("ShaderNodeVolumeScatter")
    sc_.inputs["Color"].default_value = (0.10, 0.34, 0.95, 1)
    vn.links.new(th.outputs[0], sc_.inputs["Density"])
    addv = vn.nodes.new("ShaderNodeAddShader")
    vn.links.new(vabs.outputs[0], addv.inputs[0])
    vn.links.new(sc_.outputs[0], addv.inputs[1])
    vn.links.new(addv.outputs[0], vout.inputs["Volume"])
    sc.cycles.volume_bounces, sc.cycles.volume_step_rate = 1, 2.0

# a raking bank from the left does the modelling and dies off to the right, so part of the form stays unseen. One thin red line stays on the far rim: the safelight is still on behind us
area("key", (-11.5, -3.5, 5.2), (1.0, 0, 1.0), 4.5, 4.5, (0.46, 0.68, 1.0), 1700)
tp = area("top", (2, -1, 12), (1, 0, 0), 22, 14, (0.22, 0.48, 1.0), 800)
tp.visible_glossy = False
spot("safe", (6, 9, 6), (6, 8.1, 0.32), (1.0, 0.05, 0.02), 90, size=0.3, cone=70)

cam = camera((-1.2, -12.2, 9.6), (0.9, 0.25, 0.4), lens=46, fstop=0.6, focus=15.2)

# the only word in the frame: a blueprint slip, white on blue, standing in the tray corner
tag = dr.paper_mat("tag", os.path.join(WORK, "t4_tag.png"), rough=0.7, spec=0.2, bump=0.05)
dr.facing(cam, 380, 958, 12.4, 640, 92, tag, roll=-1.3)

if A.mode == "nolines":
    nt.links.remove(c2.inputs[0].links[0])
    c2.inputs[0].default_value = 0.0
if A.mode == "conf":
    # R carries real pLDDT, G carries coverage; the water stays so the refraction registers with the beauty plate
    cc = nt.nodes.new("ShaderNodeCombineColor")
    Ln(at.outputs["Fac"], cc.inputs[0])
    cc.inputs[1].default_value = 1.0
    ee = nt.nodes.new("ShaderNodeEmission")
    Ln(cc.outputs[0], ee.inputs["Color"])
    Ln(ee.outputs[0], out.inputs["Surface"])
    vm_ = lq.data.materials[0]
    vo_ = [n for n in vm_.node_tree.nodes if n.type == "OUTPUT_MATERIAL"][0]
    for l_ in list(vo_.inputs["Volume"].links):
        vm_.node_tree.links.remove(l_)
    for o_ in bpy.data.objects:
        if o_.type == "LIGHT":
            o_.hide_render = True

dr.render(sc, A.name)
