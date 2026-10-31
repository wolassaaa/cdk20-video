"""HKBU SCIE1007 coursework science video. T5 of the darkroom direction: the work bench where red meets blue. The measured number is a print pinned down under the safelight; the AI pocket is a blueprint under the UV lamp; our re-docked 048 is pencil on tracing paper taped over it."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dr
from dr import *

A = dr.args(lambda ap: ap.add_argument("--name", default="t5"))
sc = dr.setup(A.samples, A.pct, bounces=6)
SAFE = (1.0, 0.022, 0.006)
UV = (0.16, 0.42, 1.0)
box("bench", (-60, -60, -0.6), (60, 60, 0), pbr("bench", lin("120F0E"), rough=0.42, spec=0.5))


def cockle(a, s):
    def f(U, V):
        return a * np.sin(U * 4.1 + s) * np.sin(V * 3.2 + 1.3 * s) + a * 1.6 * (np.clip(0.04 - V, 0, 1) / 0.04) ** 2
    return f


PW, PH = 10.7, 10.7 * 1600 / 2400
px, py, pr = -3.95, -0.45, math.radians(3.4)
sheet("print", PW, PH, loc=(px, py, 0.11), rot=(0, 0, pr), nx=160, ny=110, warp=cockle(0.012, 0.7), mat=dr.paper_mat("print", os.path.join(WORK, "t5_print.png"), rough=0.5, spec=0.35))
BW, BH = 7.3, 7.3 * 2600 / 2000
bx, by, br = 4.85, 0.15, math.radians(-5.2)
sheet("blue", BW, BH, loc=(bx, by, 0.04), rot=(0, 0, br), nx=100, ny=130, warp=cockle(0.015, 1.9), mat=dr.paper_mat("blue", os.path.join(WORK, "t5_blue.png"), rough=0.7, spec=0.2))
# tracing paper is registered to the blueprint: same rotation, offset by its place on the sheet, so the ligand stays in the pocket
k = BW / 2000
VW, VH = 1500 * k, 2120 * k
lx = (280 + 750 - 1000) * k
ly = -(240 + 1060 - 1300) * k
ox = bx + lx * math.cos(br) - ly * math.sin(br)
oy = by + lx * math.sin(br) + ly * math.cos(br)
vel = dr.paper_mat("vellum", os.path.join(WORK, "t5_vellum.png"), rough=0.5, spec=0.3, bump=0.03, alpha=True)
vel.blend_method = "HASHED" if hasattr(vel, "blend_method") else None
sheet("vellum", VW, VH, loc=(ox, oy, 0.075), rot=(0, 0, br), nx=8, ny=8, mat=vel)
rm, rnt, rout = new_mat("redline")
rt = rnt.nodes.new("ShaderNodeTexImage")
rt.image = bpy.data.images.load(os.path.join(WORK, "t5_redline.png"))
rt.interpolation = "Cubic"
re_ = rnt.nodes.new("ShaderNodeEmission")
rnt.links.new(rt.outputs["Color"], re_.inputs["Color"])
re_.inputs["Strength"].default_value = 1.05
rmx = rnt.nodes.new("ShaderNodeMixShader")
rnt.links.new(rt.outputs["Alpha"], rmx.inputs[0])
rnt.links.new(rnt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], rmx.inputs[1])
rnt.links.new(re_.outputs[0], rmx.inputs[2])
rnt.links.new(rmx.outputs[0], rout.inputs["Surface"])
sheet("redline", VW, VH, loc=(ox, oy, 0.09), rot=(0, 0, br), nx=8, ny=8, mat=rm)

# pins: the record is fixed to the bench, the way a result is
steel = pbr("pin", lin("B8B4AE"), rough=0.28, metal=1.0)
for ux, uy in [(-0.47, 0.455), (0.47, 0.455), (-0.47, -0.455), (0.47, -0.455)]:
    lx, ly = ux * PW, uy * PH
    x, y = px + lx * math.cos(pr) - ly * math.sin(pr), py + lx * math.sin(pr) + ly * math.cos(pr)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(x, y, 0.24), segments=32, ring_count=16)
    o = bpy.context.object
    o.scale = (1, 1, 0.55)
    o.data.materials.append(steel)
    bpy.ops.object.shade_smooth()
    box(f"pin{ux}{uy}", (x - 0.02, y - 0.02, 0.05), (x + 0.02, y + 0.02, 0.22), steel)
# masking tape holding the tracing paper
tape = pbr("tape", lin("B7A988"), rough=0.6)
for ux, uy, r in [(-0.49, 0.48, 42), (0.49, 0.48, -42)]:
    lx, ly = ux * VW, uy * VH
    x, y = ox + lx * math.cos(br) - ly * math.sin(br), oy + lx * math.sin(br) + ly * math.cos(br)
    sheet(f"tape{ux}", 1.0, 0.3, loc=(x, y, 0.085), rot=(0, 0, br + math.radians(r)), nx=4, ny=2, mat=tape)

# two lamps, two sides of the seam
spot("safe", (-8.5, -4.0, 14.5), (-3.6, -0.2, 0), SAFE, 7600, size=1.2, cone=58, blend=0.7)
spot("uv", (11.5, 2, 14), (6.6, 0.1, 0), UV, 3400, size=1.2, cone=50, blend=0.55)
fg = box("flag", (2.3, -20, 6.0), (6.1, 20, 6.1), pbr("flagm", (0, 0, 0)))
fg.visible_camera = False
camera((-0.1, -9.2, 21.6), (-0.1, 0.1, 0), lens=41, fstop=1.2, focus=23.4)
dr.render(sc, A.name)
