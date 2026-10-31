"""HKBU SCIE1007 coursework science video. Engraves the CDK20 surface for the W2 still.

Run from this folder, after make_surface.py:
blender -b -t 4 -P bl_lines.py -- --out <S2plus>/public/cdk20_lines.png [--ppa 11.5 --cx 1240 --cy 540 --pitch 9 --samples 128 --pct 100]

Lines are planes through the model, so they stay on the surface when it turns and do not crawl on the frame the way a screen-space line screen would.
Line width = light x confidence, using the real per-residue pLDDT carried by make_surface.py. Below pLDDT 70 the black fill drops out and only broken
rings are left: that is a picture of low confidence, not a measured motion. Emission only under the Standard view, so bone and black land on their exact hex.
"""
import argparse, math, os, sys, time
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ppa", type=float, default=11.5)     # design px per Angstrom at 1080p
ap.add_argument("--xc", type=float, default=1240)      # where the model origin lands, design px
ap.add_argument("--yc", type=float, default=540)
ap.add_argument("--pitch", type=float, default=9)      # line pitch, design px
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--pct", type=int, default=100)        # 100 = 3840x2160
ap.add_argument("--ink", default="EDEBE4")
ap.add_argument("--fill", default="060606")
A = ap.parse_args(argv)


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return (*np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).tolist(), 1.0)


SC = 0.1
D = np.load(os.path.join(HERE, "..", "_work", "cdk20_surface.npz"))
verts, quads, conf = D["verts"] * SC, D["quads"], D["conf"]

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples, c_.use_denoising = "GPU", A.samples, False
c_.use_adaptive_sampling = False
c_.max_bounces, c_.transparent_max_bounces = 0, 16
c_.seed, c_.use_animated_seed = 0, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 3840, 2160, A.pct
sc.render.film_transparent = True
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.view_settings.exposure, sc.view_settings.gamma = 0, 1
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth, st.compression = "PNG", "RGBA", "8", 60

me = bpy.data.meshes.new("cdk20")
me.from_pydata(verts.tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
me.update()
ob = bpy.data.objects.new("cdk20", me)
sc.collection.objects.link(ob)

m = bpy.data.materials.new("engrave")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
L = lambda a, b: nt.links.new(a, b)
geo, at = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeAttribute")
at.attribute_name, at.attribute_type = "conf", "GEOMETRY"


def op(kind, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation, n.use_clamp = kind, clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L(v, n.inputs[i])
    return n.outputs[0]


def dot(vec_socket, v):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = "DOT_PRODUCT"
    L(vec_socket, n.inputs[0])
    n.inputs[1].default_value = tuple(v)
    return n.outputs["Value"]


def ramp(a, lo, hi):
    """Smoothstep from lo to hi."""
    n = nt.nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP"
    L(a, n.inputs["Value"])
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
    n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = 0, 1
    return n.outputs["Result"]


# planes tilted a little off horizontal, so the lines wrap the form; lines per metre from the pitch in px
PLANE = Vector((0.20, 0.96, 0.18)).normalized()
LIGHT = Vector((-0.42, 0.62, 0.66)).normalized()
per_unit = A.ppa / SC / A.pitch
s = op("MULTIPLY", dot(geo.outputs["Position"], PLANE), per_unit)
tri = op("ABSOLUTE", op("SUBTRACT", op("MULTIPLY", op("FRACT", s), 2.0), 1.0))
shade = op("MAXIMUM", dot(geo.outputs["Normal"], LIGHT), 0.0)
sure = ramp(at.outputs["Fac"], 0.55, 0.80)
width = op("MULTIPLY", op("ADD", 0.05, op("MULTIPLY", op("POWER", shade, 1.3), 0.70)), op("ADD", 0.30, op("MULTIPLY", sure, 0.70)))
line = op("LESS_THAN", tri, width)
solid = op("GREATER_THAN", at.outputs["Fac"], 0.70)   # same split as the barcode, AlphaFold's 70

ink, fill = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeEmission")
ink.inputs["Color"].default_value, fill.inputs["Color"].default_value = lin(A.ink), lin(A.fill)
gone = nt.nodes.new("ShaderNodeBsdfTransparent")
inner, outer = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeMixShader")
L(solid, inner.inputs[0]); L(gone.outputs[0], inner.inputs[1]); L(fill.outputs[0], inner.inputs[2])
L(line, outer.inputs[0]); L(inner.outputs[0], outer.inputs[1]); L(ink.outputs[0], outer.inputs[2])
out = nt.nodes.new("ShaderNodeOutputMaterial")
L(outer.outputs[0], out.inputs["Surface"])
me.materials.append(m)

# orthographic down -Z; a model point (x, y) lands at cx + ppa x, cy - ppa y in design px
cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
cam_d.ortho_scale = 1080 / A.ppa * SC
cam_d.clip_start, cam_d.clip_end = 0.01, 40
cam = bpy.data.objects.new("cam", cam_d)
cam.location = ((960 - A.xc) / A.ppa * SC, (A.yc - 540) / A.ppa * SC, 20)
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.filepath = A.out
t = time.time()
bpy.ops.render.render(write_still=True)
print(f"wrote {A.out} in {time.time() - t:.1f} s")
