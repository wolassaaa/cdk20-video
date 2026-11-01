"""HKBU SCIE1007 coursework science video. Blender helpers for the specimen direction: thin non-refracting glass shells and matte coloured structure inside, so the glass never hides what it holds."""
import math
import sys

import bpy
from mathutils import Vector

ROOT = "D:/。hkbu/molecular science/镜头设计_v3/"
sys.path.insert(0, ROOT + "styleframes/art/_shared")
import glass_kit as gk  # noqa: E402

PLATES = ROOT + "styleframes/art/specimen/plates/"


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return {"samples": int(argv[0]) if argv else 128, "pct": int(argv[1]) if len(argv) > 1 else 100}


def scene(samples, pct=100, world=(0, 0, 0)):
    sc = gk.scene(samples=samples, world=world, look="None")
    sc.render.resolution_percentage = pct
    return sc


def lin(hexcol):
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


RED, DEEP, KLEIN, BLUE, BONE = lin("E8190F"), lin("9A0E08"), lin("002FA7"), lin("1F3BFF"), lin("EDEBE4")


def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def shell(blend=0.30, edge=0.34, rgb=(0.9, 0.92, 0.95), rough=0.14, haze=0.0, fill=0.0):
    """Soap-film glass: transparent face-on, glossy at the silhouette, no refraction, so what is inside stays where it really is. Same idea as ghost_shell in S1/v2/_code/s102/liver_rb.py."""
    m, nt, out = _mat("shell")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = blend
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = rough
    gl.inputs["Color"].default_value = (*rgb, 1)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Max"].default_value = edge
    nt.links.new(lw.outputs["Fresnel"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    last = mx
    if fill > 0:  # a faint emissive skin so the outline holds on black
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*rgb, 1)
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "MULTIPLY"
        fr.inputs[1].default_value = fill
        nt.links.new(lw.outputs["Facing"], fr.inputs[0])
        em2 = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(fr.outputs[0], em.inputs["Strength"])
        nt.links.new(mx.outputs[0], em2.inputs[0])
        nt.links.new(em.outputs[0], em2.inputs[1])
        last = em2
    geo = nt.nodes.new("ShaderNodeNewGeometry")     # the far wall of the shell adds glare and no information: only the near skin shows
    fm = nt.nodes.new("ShaderNodeMixShader")
    tr2 = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(geo.outputs["Backfacing"], fm.inputs[0])
    nt.links.new(last.outputs[0], fm.inputs[1])
    nt.links.new(tr2.outputs[0], fm.inputs[2])
    nt.links.new(fm.outputs[0], out.inputs["Surface"])
    if haze > 0:
        vs = nt.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Color"].default_value = (0.8, 0.8, 0.82, 1)
        vs.inputs["Density"].default_value = haze
        vs.inputs["Anisotropy"].default_value = 0.55
        nt.links.new(vs.outputs[0], out.inputs["Volume"])
    return m


def tissue(rgb, rough=0.26, coat=1.0, glow=0.0):
    """Matte body with a clear coat: reads as the true colour under any light, with one wet highlight on top."""
    m, nt, out = _mat("tissue")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.08
    if glow:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = glow
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def ortho(loc, target, width):
    """Orthographic camera. Image width is `width` units, so 1920 / width px per unit everywhere in the frame, which is what lets a scale bar be true."""
    d = bpy.data.cameras.new("cam")
    d.type, d.ortho_scale, d.clip_start, d.clip_end = "ORTHO", width, 0.01, 200
    c = bpy.data.objects.new("cam", d)
    sc = bpy.context.scene
    sc.collection.objects.link(c)
    sc.camera = c
    c.location = loc
    c.rotation_euler = (Vector(target) - c.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    return c


def softbox(name, loc, target, strength, w, h, rgb=(1, 1, 1)):
    """Emissive card, invisible to camera, seen in reflections and as light. Soft elliptical falloff so highlights have no hard rectangle edges."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name, o.scale = name, (w, h, 1)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = False
    o.visible_shadow = False
    m, nt, out = _mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sca = nt.nodes.new("ShaderNodeVectorMath")
    sca.operation, sca.inputs["Scale"].default_value = "SCALE", 2.0
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    nt.links.new(tc.outputs["Object"], sca.inputs[0])
    nt.links.new(sca.outputs[0], dist.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHERSTEP"
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(dist.outputs["Value"], mr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMath")
    mu.operation, mu.inputs[1].default_value = "MULTIPLY", strength
    nt.links.new(mr.outputs[0], mu.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(mu.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)
    return o


def backdrop(z_y=6.0, rgb=KLEIN, strength=1.0, w=12, h=7, loc=(0, 0)):
    """A soft glow behind the specimen, the back panel of a lit display case."""
    return softbox("panel", (loc[0], z_y, loc[1]), (loc[0], 0, loc[1]), strength, w, h, rgb)
