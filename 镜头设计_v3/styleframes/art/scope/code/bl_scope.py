"""HKBU SCIE1007 coursework science video. Scope direction: raw data passes of the real models, orthographic so the scale bars can be calculated exactly.

blender -b -t 4 -P bl_scope.py -- cdk      ribbon normal, depth, pLDDT, mask, plus an additive thin-shell pass of the surface
blender -b -t 4 -P bl_scope.py -- liver    liver shell and form, portal vein and hepatic veins (normal, depth, which vessel, mask)
Writes ../_work/<shot>.npz, float16, 1080x1920, plus the px-per-Angstrom or px-per-mm the frame was rendered at.
"""
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
ART = HERE + "../../"
sys.path.insert(0, ART + "_shared")
import glass_kit as gk

S1 = ART + "../S1/v2/_code/s110/"
sys.path.insert(0, S1)
import prot_geo as G
G.JSON = ART + "../S2plus/code/cdk20_backbone_view.json"

SHOT = sys.argv[sys.argv.index("--") + 1]
W, H = (3840, 2160) if SHOT == "bench" else (1920, 1080)   # bench: worst case, 4K with the heaviest shell, timed, nothing kept
OUT = HERE + "../_work/"


def emit(fn, name, additive=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = 1
    nt.links.new(fn(nt), e.inputs["Color"])
    if additive:
        tr, ad = nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(e.outputs[0], ad.inputs[0])
        nt.links.new(tr.outputs[0], ad.inputs[1])
        nt.links.new(ad.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def f_normal(nt):
    g, t = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeVectorTransform")
    t.vector_type, t.convert_from, t.convert_to = "NORMAL", "WORLD", "CAMERA"
    nt.links.new(g.outputs["Normal"], t.inputs[0])
    return t.outputs[0]


def f_depth(nt):
    return nt.nodes.new("ShaderNodeCameraData").outputs["View Z Depth"]


def f_attr(name):
    def f(nt):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name, a.attribute_type = name, "GEOMETRY"
        return a.outputs["Fac"]
    return f


def f_shell(power):
    """Thin shell: a wall seen edge-on is a longer path through the film, so it collects more signal, about 1 / facing. Backfaces count too."""
    def f(nt):
        g = nt.nodes.new("ShaderNodeNewGeometry")
        d = nt.nodes.new("ShaderNodeVectorMath")
        d.operation = "DOT_PRODUCT"
        nt.links.new(g.outputs["Normal"], d.inputs[0])
        nt.links.new(g.outputs["Incoming"], d.inputs[1])
        ab, sub, pw = nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeMath")
        ab.operation, sub.operation, pw.operation = "ABSOLUTE", "SUBTRACT", "POWER"
        nt.links.new(d.outputs["Value"], ab.inputs[0])
        sub.inputs[0].default_value = 1
        nt.links.new(ab.outputs[0], sub.inputs[1])
        nt.links.new(sub.outputs[0], pw.inputs[0])
        pw.inputs[1].default_value = power
        return pw.outputs[0]
    return f


def setup(ortho_scale, cam_xyz, rot, samples):
    sc = bpy.context.scene
    sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
    sc.render.film_transparent = True
    sc.cycles.samples, sc.cycles.use_denoising = samples, False
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.max_bounces, sc.cycles.transparent_max_bounces = 128, 128
    sc.cycles.filter_width = 1.2
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
    d = bpy.data.cameras.new("cam")
    d.type, d.ortho_scale, d.clip_start, d.clip_end = "ORTHO", ortho_scale, 0.01, 500
    c = bpy.data.objects.new("cam", d)
    sc.collection.objects.link(c)
    sc.camera = c
    c.location, c.rotation_euler = cam_xyz, rot
    return sc


def shoot(sc, name, ob, material, obs_visible):
    t0 = gk.time.time()
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in obs_visible
    for o in obs_visible:
        o.data.materials.clear()
        o.data.materials.append(material)
    p = OUT + "_" + name + ".exr"
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    px = np.empty(W * H * 4, np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)[::-1].copy()
    bpy.data.images.remove(im)
    os.remove(p)
    print("pass", name, float(px.min()), float(px.max()), "seconds %.1f" % (gk.time.time() - t0))
    return px


os.makedirs(OUT, exist_ok=True)
gk.scene(W, H, samples=32, look="None")
res = {}
if SHOT in ("cdk", "bench"):
    PPA = 24.0 if SHOT == "bench" else 12.0                      # px per Angstrom at 1080p; orthographic, so true everywhere in the frame
    A2U = 0.05
    frame = (6.8, -1.0)             # Angstrom, what lands on frame centre
    rib = G.ribbon(G.load(), coil_r=0.55, helix_w=1.7, sheet_w=1.5, thick=0.5, arrow=1.7)
    surf = gk.cdk20(centre=False)
    surf.scale = (0.5, 0.5, 0.5)    # glass_kit is 0.1 unit per Angstrom, the ribbon 0.05
    sc = setup(W / PPA * A2U, (frame[0] * A2U, frame[1] * A2U, 20), (0, 0, 0), 48)
    for nm, fn, c in (("n", f_normal, 3), ("z", f_depth, 1), ("p", f_attr("plddt"), 1), ("u", f_attr("u"), 1)):
        px = shoot(sc, "r" + nm, rib, emit(fn, nm), [rib])
        res["r" + nm] = px[..., :c] if c > 1 else px[..., 0]
        res["ra"] = px[..., 3]
    px = shoot(sc, "shell", surf, emit(f_shell(3.0), "shell", True), [surf])
    res["shell"] = px[..., 0]
    px = shoot(sc, "sc", surf, emit(f_attr("conf"), "sc"), [surf])
    res["sconf"], res["sa"] = px[..., 0], px[..., 3]
    res["ppa"] = np.array(PPA)
else:
    PPM = 3.6                       # px per mm at 1080p
    U = 0.01                        # 1 unit = 100 mm
    liver = gk.liver_skin()
    pv = gk.stl("portal_vein_hepatic")
    hv = gk.stl("hepatic_veins")
    for o, v in ((pv, 1.0), (hv, 0.0)):
        a = o.data.attributes.new("vid", "FLOAT", "POINT")
        a.data.foreach_set("value", [v] * len(o.data.vertices))
    for o in (liver, pv, hv):
        print("bbox", o.name, np.array(o.bound_box).min(0), np.array(o.bound_box).max(0))
    sc = setup(W / PPM * U, (0, -20, 0), (math.pi / 2, 0, 0), 48)
    px = shoot(sc, "lshell", liver, emit(f_shell(2.5), "lshell", True), [liver])
    res["lshell"] = px[..., 0]
    px = shoot(sc, "ln", liver, emit(f_normal, "ln"), [liver])
    res["ln"], res["la"] = px[..., :3], px[..., 3]
    for nm, fn, c in (("n", f_normal, 3), ("z", f_depth, 1), ("v", f_attr("vid"), 1)):
        px = shoot(sc, "v" + nm, pv, emit(fn, nm), [pv, hv])
        res["v" + nm] = px[..., :c] if c > 1 else px[..., 0]
        res["va"] = px[..., 3]
    res["ppm"] = np.array(PPM)
if SHOT != "bench":
    np.savez_compressed(OUT + SHOT + ".npz", **{k: v.astype(np.float16) if v.ndim else v for k, v in res.items()})
print("DONE", SHOT, gk.time.time() - gk._t0)
