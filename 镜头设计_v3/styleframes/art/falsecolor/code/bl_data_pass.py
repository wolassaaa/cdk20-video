"""HKBU SCIE1007 coursework science video. falsecolor art direction: data passes for the CDK20 surface (T4 still).

blender -b -t 4 -P bl_data_pass.py -- --out DIR [--ppa 11.5 --xc 930 --yc 540 --rot 0 --pct 100 --tag t4]

Renders no colour at all. Writes three 16-bit grey PNGs of the same camera:
  <tag>_plddt.png   the real per-vertex pLDDT carried by make_surface.py, 0..1 on the surface, film alpha outside
  <tag>_ao.png      ambient occlusion only, the crevices that give the form
  <tag>_facing.png  how much the surface faces the camera
False colour is then a lookup in compose scripts, so the colour on screen is the number and nothing else.
"""
import argparse, math, os, sys, time
import bpy
import numpy as np
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ppa", type=float, default=11.5)
ap.add_argument("--xc", type=float, default=930)
ap.add_argument("--yc", type=float, default=540)
ap.add_argument("--rot", type=float, default=0)     # degrees about the vertical, for the motion test
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--tag", default="t4")
ap.add_argument("--seq", default="")                # "start,end,rot0,rot1,total": render frames start..end-1 of a slow turn into <out>/<tag>_NNN_<pass>.png
A = ap.parse_args(argv)

SC = 0.1
S2 = os.path.normpath(os.path.join(HERE, "..", "..", "..", "S2plus"))
D = np.load(os.path.join(S2, "_work", "cdk20_surface.npz"))
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
c_.device, c_.samples, c_.use_denoising = "GPU", A.samples, True
c_.denoiser = "OPTIX"
c_.max_bounces = 0
c_.seed, c_.use_animated_seed = 0, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, A.pct
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.view_settings.exposure, sc.view_settings.gamma = 0, 1
wd = bpy.data.worlds.new("w")
wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[1].default_value = 0
sc.world = wd
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth, st.compression = "PNG", "BW", "16", 40   # PIL reads 16-bit grey as is; it would cut 16-bit RGBA to 8
sc.display_settings.display_device = "sRGB"

me = bpy.data.meshes.new("cdk20")
me.from_pydata(verts.tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
# a mesh-smoothed copy of the same number, used only to draw clean contour lines
cs, cnt = conf.astype(np.float64).copy(), np.zeros(len(conf))
np.add.at(cnt, quads.ravel(), 2)
for _ in range(60):
    acc = np.zeros(len(conf))
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
        np.add.at(acc, quads[:, a], cs[quads[:, b]])
        np.add.at(acc, quads[:, b], cs[quads[:, a]])
    cs = 0.3 * cs + 0.7 * acc / np.maximum(cnt, 1)
me.attributes.new("conf_s", "FLOAT", "POINT").data.foreach_set("value", cs.tolist())
me.update()
ob = bpy.data.objects.new("cdk20", me)
sc.collection.objects.link(ob)
ob.rotation_euler = Euler((0, math.radians(A.rot), 0))


def mat(kind):
    m = bpy.data.materials.new(kind)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    if kind == "mask":
        em.inputs["Color"].default_value = (1, 1, 1, 1)
    elif kind in ("plddt", "smooth"):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name, at.attribute_type = "conf" if kind == "plddt" else "conf_s", "GEOMETRY"
        # the output is display-referred sRGB under Standard, so undo that here to store the number as is
        p = nt.nodes.new("ShaderNodeMath")
        p.operation = "POWER"
        p.inputs[1].default_value = 2.2
        nt.links.new(at.outputs["Fac"], p.inputs[0])
        nt.links.new(p.outputs[0], em.inputs["Color"])
    elif kind == "ao":
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 16
        ao.inputs["Distance"].default_value = 1.6
        p = nt.nodes.new("ShaderNodeMath")
        p.operation = "POWER"
        p.inputs[1].default_value = 2.2
        nt.links.new(ao.outputs["AO"], p.inputs[0])
        nt.links.new(p.outputs[0], em.inputs["Color"])
    else:
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1
        nt.links.new(lw.outputs["Facing"], inv.inputs[1])
        p = nt.nodes.new("ShaderNodeMath")
        p.operation = "POWER"
        p.inputs[1].default_value = 2.2
        nt.links.new(inv.outputs[0], p.inputs[0])
        nt.links.new(p.outputs[0], em.inputs["Color"])
    return m


cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
cam_d.ortho_scale = 1080 / A.ppa * SC
cam_d.clip_start, cam_d.clip_end = 0.01, 40
cam = bpy.data.objects.new("cam", cam_d)
cam.location = ((960 - A.xc) / A.ppa * SC, (A.yc - 540) / A.ppa * SC, 20)
sc.collection.objects.link(cam)
sc.camera = cam

t = time.time()
if A.seq:
    a0, a1, r0, r1, total = [float(x) for x in A.seq.split(",")]
    c_.use_denoising = False                         # no per-frame denoiser: nothing to shimmer. AO noise is blurred away in comp
    mats = {k: mat(k) for k in ("mask", "plddt", "smooth", "ao", "facing")}
    for fr in range(int(a0), int(a1)):
        u = fr / (total - 1)
        ob.rotation_euler = Euler((0, math.radians(r0 + (r1 - r0) * u), 0))
        for kind, mm in mats.items():
            me.materials.clear()
            me.materials.append(mm)
            c_.samples = 48 if kind == "ao" else 8
            sc.render.filepath = os.path.join(A.out, f"{A.tag}_{fr:03d}_{kind}.png")
            bpy.ops.render.render(write_still=True)
    print(f"DONE seq {time.time() - t:.1f} s")
    sys.exit(0)
for kind in ("mask", "plddt", "smooth", "ao", "facing"):
    me.materials.clear()
    me.materials.append(mat(kind))
    c_.samples = A.samples if kind == "ao" else 24
    c_.use_denoising = kind == "ao"
    sc.render.filepath = os.path.join(A.out, f"{A.tag}_{kind}.png")
    bpy.ops.render.render(write_still=True)
print(f"DONE {time.time() - t:.1f} s")
