"""HKBU SCIE1007 coursework science video. Direction inside, shot F1: data passes of the real BodyParts3D liver and veins, seen from the front. No flip. Each part alone, as coverage plus normal and depth, so the molecular-illustration look can be painted in numpy."""
import math, os, sys
import bpy
import numpy as np
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
import glass_kit as gk

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/inside/_work/"
sc = gk.scene(1920, 1080, samples=16, look="None")
sc.render.film_transparent = True
sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = "BOX"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"


def passmat():
    m = bpy.data.materials.new("pass")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, em, geo = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeNewGeometry")
    sep_n, sep_p, com = nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(geo.outputs["Normal"], sep_n.inputs[0])
    nt.links.new(geo.outputs["Position"], sep_p.inputs[0])
    nt.links.new(sep_n.outputs[0], com.inputs[0])       # world nx
    nt.links.new(sep_n.outputs[2], com.inputs[1])       # world nz
    nt.links.new(sep_p.outputs[1], com.inputs[2])       # world y, small is near the camera on -y
    nt.links.new(com.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


M = passmat()
parts = {"liver": gk.liver_skin(M, voxel=0.02)}
for k, n in (("portal", "portal_vein_hepatic"), ("hepatic", "hepatic_veins"), ("ivc", "inferior_vena_cava")):
    parts[k] = gk.stl(n, M)
cd = bpy.data.cameras.new("cam")
cd.type, cd.ortho_scale, cd.clip_start, cd.clip_end = "ORTHO", 1920 / 520, 0.1, 40
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
cam.location = (0, -12, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam
for k in parts:
    for n, o in parts.items():
        o.hide_render = n != k
    p = OUT + f"liver_{k}.exr"
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    a = np.zeros(1920 * 1080 * 4, np.float32)
    im.pixels.foreach_get(a)
    np.save(OUT + f"liver_{k}.npy", a.reshape(1080, 1920, 4)[::-1].astype(np.float16))
    print("SAVED", k, a[3::4].mean())
