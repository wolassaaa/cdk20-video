"""HKBU SCIE1007 coursework science video. T6 of the darkroom direction: the road map as one strip of film across a light box. The box stops at the door of the fourth frame, so what is lit and what is not is a physical fact of the set, not a graphic decision."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="t6"))
sc = dr.setup(A.samples, A.pct, bounces=6)
BOX = (1.0, 0.70, 0.40)
PLUM = (0.52, 0.16, 0.62)

FW, FH, GAP, MY, N = 900, 620, 70, 130, 6
TW = (FW + GAP) * N + GAP
TH = FH + 2 * MY
L = 21.0                              # strip length in scene units
k = L / TW
SW, SH = L, TH * k
x0 = -L / 2
DOOR = x0 + (GAP + 3 * (FW + GAP) + 0.045 * FW) * k     # light box edge: just inside frame 4
Z_TOP = 0.45

box("bench", (-60, -60, -0.5), (60, 60, 0), pbr("bench", lin("15101A"), rough=0.5, spec=0.5))
# the light box: opal glass top, thin dark frame
g, g_nt, g_out = new_mat("opal")
tc = g_nt.nodes.new("ShaderNodeNewGeometry")
sp = g_nt.nodes.new("ShaderNodeSeparateXYZ")
g_nt.links.new(tc.outputs["Position"], sp.inputs[0])
mr = g_nt.nodes.new("ShaderNodeMapRange")
mr.interpolation_type = "SMOOTHSTEP"
g_nt.links.new(sp.outputs["X"], mr.inputs["Value"])
mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -16, DOOR
mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.22, 0.78
e = g_nt.nodes.new("ShaderNodeEmission")
e.inputs["Color"].default_value = (*BOX, 1)
ym = g_nt.nodes.new("ShaderNodeMapRange")
ym.interpolation_type = "SMOOTHSTEP"
ab = g_nt.nodes.new("ShaderNodeMath")
ab.operation = "ABSOLUTE"
sb = g_nt.nodes.new("ShaderNodeMath")
sb.operation = "SUBTRACT"
g_nt.links.new(sp.outputs["Y"], sb.inputs[0])
sb.inputs[1].default_value = 0.1
g_nt.links.new(sb.outputs[0], ab.inputs[0])
g_nt.links.new(ab.outputs[0], ym.inputs["Value"])
ym.inputs["From Min"].default_value, ym.inputs["From Max"].default_value = 0.5, 3.0
ym.inputs["To Min"].default_value, ym.inputs["To Max"].default_value = 1.0, 0.13
mu_ = g_nt.nodes.new("ShaderNodeMath")
mu_.operation = "MULTIPLY"
g_nt.links.new(mr.outputs[0], mu_.inputs[0])
g_nt.links.new(ym.outputs[0], mu_.inputs[1])
g_nt.links.new(mu_.outputs[0], e.inputs["Strength"])
g_nt.links.new(e.outputs[0], g_out.inputs["Surface"])
YLO, YHI = -3.1, 2.75
box("glass", (-30, YLO, Z_TOP - 0.02), (DOOR, YHI, Z_TOP), g)
frame_m = pbr("frame", lin("0C0A0A"), rough=0.4)
box("hsg", (-30.2, YLO - 0.2, 0), (DOOR + 0.2, YHI + 0.2, Z_TOP - 0.02), frame_m)
box("lip", (DOOR, YLO - 0.2, 0), (DOOR + 0.2, YHI + 0.2, Z_TOP + 0.03), frame_m)


def drape(U, V):
    x = x0 + U * L
    t = np.clip((x - DOOR - 0.15) / 2.6, 0, 1)
    t = t * t * (3 - 2 * t)
    return (Z_TOP + 0.02) * (1 - t) + 0.05 * t + 0.02 * np.sin(U * 17 + 1) * t


# strip: emission is the film seen against the box; beyond the edge only a little spill reaches the frame
sm, nt, out = new_mat("strip")
Ln = nt.links.new
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(os.path.join(WORK, "t6_strip.png"))
tex.interpolation = "Cubic"
coord = nt.nodes.new("ShaderNodeTexCoord")
sx = nt.nodes.new("ShaderNodeSeparateXYZ")
Ln(coord.outputs["UV"], sx.inputs[0])
back = nt.nodes.new("ShaderNodeMapRange")
back.interpolation_type = "SMOOTHSTEP"
Ln(sx.outputs["X"], back.inputs["Value"])
ue = (DOOR - x0) / L
back.inputs["From Min"].default_value, back.inputs["From Max"].default_value = ue + 0.002, ue + 0.075
back.inputs["To Min"].default_value, back.inputs["To Max"].default_value = 1.0, 0.0
em = nt.nodes.new("ShaderNodeEmission")
Ln(tex.outputs["Color"], em.inputs["Color"])
mul = nt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
Ln(back.outputs[0], mul.inputs[0])
mul.inputs[1].default_value = 1.15
Ln(mul.outputs[0], em.inputs["Strength"])
dif = nt.nodes.new("ShaderNodeBsdfPrincipled")
Ln(tex.outputs["Color"], dif.inputs["Base Color"])
dif.inputs["Roughness"].default_value = 0.22
add = nt.nodes.new("ShaderNodeAddShader")
Ln(em.outputs[0], add.inputs[0])
Ln(dif.outputs[0], add.inputs[1])
trans = nt.nodes.new("ShaderNodeBsdfTransparent")
mix = nt.nodes.new("ShaderNodeMixShader")
Ln(tex.outputs["Alpha"], mix.inputs[0])
Ln(trans.outputs[0], mix.inputs[1])
Ln(add.outputs[0], mix.inputs[2])
Ln(mix.outputs[0], out.inputs["Surface"])
strip = sheet("strip", SW, SH, loc=(0, 0.55, 0), nx=300, ny=4, warp=drape, mat=sm)

# labels: printed dark on the glass for the lit stations, pale chalk on the bench for the dark ones
lm, lnt, lout = new_mat("labels")
ltx = lnt.nodes.new("ShaderNodeTexImage")
ltx.image = bpy.data.images.load(os.path.join(WORK, "t6_labels.png"))
ltx.interpolation = "Cubic"
lem = lnt.nodes.new("ShaderNodeEmission")
lnt.links.new(ltx.outputs["Color"], lem.inputs["Color"])
lem.inputs["Strength"].default_value = 0.8
lt = lnt.nodes.new("ShaderNodeBsdfTransparent")
lmx = lnt.nodes.new("ShaderNodeMixShader")
lnt.links.new(ltx.outputs["Alpha"], lmx.inputs[0])
lnt.links.new(lt.outputs[0], lmx.inputs[1])
lnt.links.new(lem.outputs[0], lmx.inputs[2])
lnt.links.new(lmx.outputs[0], lout.inputs["Surface"])
LB = 720 * k
yl = 0.55 - SH / 2 - LB / 2 - 0.1


def lab_z(U, V):
    x = x0 + U * L
    return np.where(x < DOOR + 0.1, Z_TOP + 0.03, 0.03)


sheet("labels", SW, LB, loc=(0, yl, 0), nx=600, ny=2, warp=lab_z, mat=lm)

# the 048 flag stands on the top edge of the strip at the door
fl, fnt, fout = new_mat("flag")
ft = fnt.nodes.new("ShaderNodeTexImage")
ft.image = bpy.data.images.load(os.path.join(WORK, "t6_flag.png"))
fe = fnt.nodes.new("ShaderNodeEmission")
fnt.links.new(ft.outputs["Color"], fe.inputs["Color"])
fe.inputs["Strength"].default_value = 0.92
fnt.links.new(fe.outputs[0], fout.inputs["Surface"])
FX = DOOR - 0.9
sheet("flag", 2.05, 1.18, loc=(FX, 0.55 + SH / 2 + 0.28, Z_TOP + 0.04), rot=(0, 0, math.radians(2)), nx=8, ny=4, mat=fl)

# far end of the room: a plum dark, just enough to find the bench and the chalk
area("plum", (10, 3, 11), (6, 0, 0), 12, 8, PLUM, 620)
camera((-4.2, -10.6, 20.0), (0.1, -0.15, 0.1), lens=34, fstop=2.2, focus=23.0, roll=3.6)
dr.render(sc, A.name)
