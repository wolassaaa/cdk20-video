"""HKBU SCIE1007 coursework science video. Lantern render bench: the T4 cold rays as an EEVEE emission shader on the real mesh, at 3840x2160, to see what the GPU path costs against numpy.
Run: blender -b -t 4 -P bl_bench.py"""
import sys
import time

import bpy
import mathutils

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
from scene_cdk20 import build, emit_material

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/lantern/_work/bl4k_"
sc, ob, cam = build(3840, 2160, engine="BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
sc.eevee.taa_render_samples = 8
sc.render.film_transparent = False
w = bpy.data.worlds.new("w")
sc.world = w
sc.render.image_settings.file_format = "PNG"


def rays(nodes, links):
    def M(op, a, b=None, clamp=False):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                links.new(v, n.inputs[i])
        return n.outputs[0]

    tc = nodes.new("ShaderNodeTexCoord")
    sp = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Window"], sp.inputs[0])
    geo = nodes.new("ShaderNodeNewGeometry")
    x = M("SUBTRACT", M("MULTIPLY", sp.outputs[0], 3840.0), 5040.0)
    y = M("SUBTRACT", M("MULTIPLY", sp.outputs[1], 2160.0), 3680.0)
    th = M("ARCTAN2", y, x)
    dp = nodes.new("ShaderNodeVectorMath")
    dp.operation = "DOT_PRODUCT"
    links.new(geo.outputs["Position"], dp.inputs[0])
    dp.inputs[1].default_value = (0.15, -0.25, 1.0)
    phase = M("ADD", M("MULTIPLY", th, 118.75), M("MULTIPLY", dp.outputs["Value"], 2.3))
    v = M("MULTIPLY", M("ABSOLUTE", M("SUBTRACT", M("FRACT", phase), 0.5)), 2.0)
    dn = nodes.new("ShaderNodeVectorMath")
    dn.operation = "DOT_PRODUCT"
    links.new(geo.outputs["Normal"], dn.inputs[0])
    dn.inputs[1].default_value = (0.6, 0.58, 0.55)
    key = M("POWER", M("MAXIMUM", dn.outputs["Value"], 0.0), 0.75)
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "conf"
    width = M("MULTIPLY", M("ADD", 0.10, M("MULTIPLY", key, 0.72)), M("ADD", 0.42, M("MULTIPLY", attr.outputs["Fac"], 0.58)))
    d = M("ADD", M("SUBTRACT", width, 1.0), v)
    mr = nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs[1].default_value, mr.inputs[2].default_value = -0.11, 0.11
    links.new(d, mr.inputs[0])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(mr.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = (0.002, 0.002, 0.002, 1)
    mix.inputs[7].default_value = (0.67, 0.87, 1.0, 1)
    return mix.outputs[2]


ob.data.materials.append(emit_material(rays, "rays"))
c = mathutils.Vector(ob.bound_box[0]) * 0.5 + mathutils.Vector(ob.bound_box[6]) * 0.5
ob.rotation_mode = "XYZ"
for i in range(5):
    ob.rotation_euler = (0, 0, i * 0.01)
    sc.render.filepath = OUT + f"{i}.png"
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"BENCH frame {i}: {time.time() - t0:.2f} s", flush=True)
