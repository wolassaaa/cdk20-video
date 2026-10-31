"""HKBU SCIE1007 coursework science video. T3 of the darkroom direction: the safelight is out. A black card with a keyhole cut in it, and what is left of the light behind it. No lock is drawn, because no one had seen it."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="t3"))
sc = dr.setup(A.samples, A.pct, bounces=5)
SAFE = (1.0, 0.02, 0.005)

# keyhole outline: a circle over a tapered foot
n = 96
R, FOOT_T, FOOT_B, FOOT_H = 1.0, 0.46, 0.78, 2.3
ang = np.linspace(math.radians(-68), math.radians(248), n)
top = [(R * math.cos(t), R * math.sin(t)) for t in ang]
y0 = top[0][1]
outline = top + [(-FOOT_B, y0 - FOOT_H), (FOOT_B, y0 - FOOT_H)]
outline = [(x, y + 0.7) for x, y in outline]
bm_v = [(x, y, -1.0) for x, y in outline] + [(x, y, 1.0) for x, y in outline]
m = len(outline)
faces = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))] + [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
me = bpy.data.meshes.new("cutter")
me.from_pydata(bm_v, [], faces)
me.update()
cut = link(bpy.data.objects.new("cutter", me))
cut.hide_render = True
cut.hide_viewport = False

card_m = pbr("card", lin("0A0807"), rough=0.62, spec=0.35)
card = box("card", (-40, -25, -0.12), (40, 25, 0.0), card_m)
bo = card.modifiers.new("hole", "BOOLEAN")
bo.operation, bo.object, bo.solver = "DIFFERENCE", cut, "EXACT"

# the room behind the door: a red wall lit from out of sight, seen only through the hole
wall = sheet("back", 40, 30, loc=(0.6, 0.4, -6), nx=1, ny=1, mat=pbr("back", (0.8, 0.8, 0.8), rough=0.8))
spot("behind", (-3.4, 3.0, -1.0), (0.9, -0.9, -6), SAFE, 72, size=0.2, cone=60, blend=1.0)
# dashed chalk ring on the card, the schematic's own line
dash, dnt, dout = new_mat("dash")
dt = dnt.nodes.new("ShaderNodeTexImage")
dt.image = bpy.data.images.load(os.path.join(WORK, "t3_dash.png"))
de = dnt.nodes.new("ShaderNodeEmission")
de.inputs["Color"].default_value = (1.0, 0.09, 0.04, 1)
de.inputs["Strength"].default_value = 0.035
dmx = dnt.nodes.new("ShaderNodeMixShader")
dnt.links.new(dt.outputs["Alpha"], dmx.inputs[0])
dnt.links.new(dnt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], dmx.inputs[1])
dnt.links.new(de.outputs[0], dmx.inputs[2])
dnt.links.new(dmx.outputs[0], dout.inputs["Surface"])
sheet("dash", 16, 16, loc=(0, 0, 0.012), nx=1, ny=1, mat=dash)
c_ = camera((1.1, -0.5, 30), (0.0, -0.2, 0), lens=50, fstop=0)
c_.rotation_euler = (0.018, 0.04, 0.0)
dr.render(sc, A.name)
