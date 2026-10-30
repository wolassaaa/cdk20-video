"""Still 5 plate: CDK20 residues 1-302 as a matte ribbon on transparent black, in the same camera frame as still 4. AlphaFold DB AF-Q8IZL9-F1 v6 (CC BY 4.0), predicted.
bl_protein.py has no look that cuts the chain, and S1 code stays as it is, so this reuses its helpers and prot_geo with Standard view, not AgX.
Run from this folder, after make_protein_points.py, with an absolute --out:
blender -b -t 4 -P bl_ribbon302.py -- --out <S2plus>/public/ribbon302.png [--samples 256 --exp 0] (flags: bl_common.RENDER_FLAGS)
"""
import bpy, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
S1 = HERE + "../../S1/v2/_code/"
sys.path += [S1 + "s110", S1 + "w0"]
import bl_util as U
import prot_geo as G
import bl_common as C
VIEW = HERE + "cdk20_backbone_view.json"
U.CODE, U.FONTS, G.JSON = S1 + "s110/", S1 + "s110/fonts/", VIEW   # those two modules hard-code D:/

A = U.args({**C.RENDER_FLAGS, "out": "", "samples": 256, "pct": 100, "exp": 0.0, "view": "Standard"})
KEEP_TO, PX_PER_A = 302, 12.98       # 0.85 x still 4's scale, the same size as the stand-in in s05.jsx
PLATE_W, PLATE_H = 1920, 2160        # design px x 2: the left half of the frame
CENTRE = (480, 490)                  # where the body sits in the left half, design px; matches s05.jsx

scn = U.reset()
U.render_setup(scn, samples=A.samples, w=PLATE_W, h=PLATE_H, pct=A.pct, exposure=A.exp, bounces=6, view=A.view)
scn.render.film_transparent = True   # the stage black comes from the page, not from Cycles
scn.render.image_settings.color_mode = "RGBA"; scn.render.image_settings.color_depth = "8"

# the view json is x right, y up, z to the lens: stand it up in Blender's camera-on-minus-y layout
frame = json.load(open(VIEW))["frame"]
rib = G.ribbon(G.load()[:KEEP_TO], coil_r=0.6, helix_w=1.7, sheet_w=1.5, thick=0.5, arrow=1.7)
rib.rotation_euler = (math.pi / 2, 0, 0)
A2U = 0.05                           # prot_geo scale, Blender units per Angstrom
rib.location = ((-frame["body_centre"][0] + (CENTRE[0] - PLATE_W / 4) / PX_PER_A) * A2U, 0, (-frame["body_centre"][1] + (PLATE_H / 4 - CENTRE[1]) / PX_PER_A) * A2U)

# bone at 70+, blue below: the barcode's rule, a hard step on the real pLDDT attribute
m, nt, b, out = U.principled("ribbon", rough=0.5)
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "plddt"; at.attribute_type = "GEOMETRY"
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0; mr.inputs[2].default_value = 100
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
els = cr.color_ramp.elements
els[0].position = 0.0; els[0].color = U.hex2lin(U.BLUE)
els[1].position = 0.7; els[1].color = U.hex2lin(U.INK)
nt.links.new(at.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs["Base Color"])
U.assign(rib, m)

# one bone key, a low fill and a thin rim. No coloured rims: one colour per screen. Standard clips at 1.0, so the key lands just under it on a facing surface
U.light_panel("key", U.INK, 640, (-3.5, -4.5, 4.5), 3.0)
U.light_panel("fill", U.INK, 40, (3.0, -6.0, -1.0), 4.0)
U.light_panel("rim", U.INK, 300, (4.0, 4.0, 2.0), 2.0)

# same distance as still 4's camera. Sensor is fitted to width because the plate is taller than wide
dist = frame["cam"] * A2U
cam = U.camera((0, -dist, 0), (0, 0, 0), lens=PX_PER_A / A2U * 36 * dist / (PLATE_W / 2))
cam.data.sensor_fit = "HORIZONTAL"

C.apply_flags(scn, A)
print("SAVED", C.render(scn, A.out))
