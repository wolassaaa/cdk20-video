"""HKBU SCIE1007 coursework science video. Blender kit for the plate direction: real objects on a seamless bone surface, shot straight down with an orthographic camera.

The floor comes out at #EDEBE4 wherever nothing shades it: world dome + sun add up to radiance 1, so a diffuse floor shows its albedo.
Orthographic means scale is exact and the label code can place leader lines from scene coordinates: px = 960 + x * PPU, py = 540 - y * PPU.
"""
import math
import sys

import bpy

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
import glass_kit as gk  # noqa: E402

PPU = 200.0  # pixels per Blender unit at 1080p, so the frame is 9.6 x 5.4 units
BONE_LIN = (0.8469, 0.8308, 0.7758)
RED, DARK = (0.8069, 0.0091, 0.0048), (0.3231, 0.0044, 0.0024)  # #E8190F, #9A0E08 in linear
KLEIN, BLUE = (0.0, 0.0284, 0.3864), (0.0137, 0.0437, 1.0)      # #002FA7, #1F3BFF in linear
SUN_DIR = (math.radians(-32), 0, math.radians(38))               # light from upper left, the textbook convention
WINDOW = (-0.33, 0.42, 0.845)                                    # direction of the soft window seen in reflections
SKY, SUN = 0.58, 1.12


def scene(samples=192, w=1920, h=1080):
    sc = gk.scene(w=w, h=h, samples=samples, look="None")
    wd = sc.world
    nt = wd.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    # bright overhead, dark at the horizon: glass and gloss get dark edges, as on a light table with black flags at the sides
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs[1].default_value, mr.inputs[2].default_value = 0.10, 0.75
    mr.inputs[3].default_value, mr.inputs[4].default_value = 0.0, SKY * 1.52
    nt.links.new(sep.outputs["Z"], mr.inputs[0])
    # reflections see a dark room with one soft window, otherwise the white sky washes blood red to pink on every gloss
    lp = nt.nodes.new("ShaderNodeLightPath")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = WINDOW
    nt.links.new(tc.outputs["Generated"], dot.inputs[0])
    win = nt.nodes.new("ShaderNodeMapRange")
    win.interpolation_type = "SMOOTHSTEP"
    win.inputs[1].default_value, win.inputs[2].default_value = 0.92, 0.975
    win.inputs[3].default_value, win.inputs[4].default_value = 0.03, 7.0
    nt.links.new(dot.outputs["Value"], win.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    # only first reflections: inside glass the rays keep seeing the bright room, so empty glass stays clear instead of going grey
    gate = nt.nodes.new("ShaderNodeMath")
    gate.operation = "LESS_THAN"
    gate.inputs[1].default_value = 0.5
    nt.links.new(lp.outputs["Transmission Depth"], gate.inputs[0])
    both = nt.nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    nt.links.new(lp.outputs["Is Glossy Ray"], both.inputs[0])
    nt.links.new(gate.outputs[0], both.inputs[1])
    nt.links.new(both.outputs[0], mix.inputs["Factor"])
    nt.links.new(mr.outputs[0], mix.inputs["A"])
    nt.links.new(win.outputs[0], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bg.inputs[1])
    bg.inputs[0].default_value = (1, 1, 1, 1)
    nt.links.new(bg.outputs[0], out.inputs[0])
    return sc


def floor(z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, z))
    o = bpy.context.object
    o.name = "floor"
    m, nt, out = gk._mat("floor")
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (*BONE_LIN, 1)
    nt.links.new(d.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)
    return o


def sun(strength=SUN, angle=9.0):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy, d.angle = strength, math.radians(angle)
    o = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = SUN_DIR
    return o


def camera(ppu=PPU, z=20.0):
    d = bpy.data.cameras.new("cam")
    d.type = "ORTHO"
    d.ortho_scale = 1920 / ppu
    d.clip_start, d.clip_end = 0.1, 100
    c = bpy.data.objects.new("cam", d)
    sc = bpy.context.scene
    sc.collection.objects.link(c)
    sc.camera = c
    c.location = (0, 0, z)
    return c


def gloss(rgb, rough=0.24, coat=0.6, spec=0.5):
    """Painted ceramic: deep saturated body with a clear coat on top."""
    m, nt, out = gk._mat("gloss")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.08
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def rx(o, deg):
    o.rotation_euler[0] = math.radians(deg)


def report(sc):
    print("PLATE_SCENE", sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples)
