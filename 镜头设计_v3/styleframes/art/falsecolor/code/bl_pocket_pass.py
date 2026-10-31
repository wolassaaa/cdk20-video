"""HKBU SCIE1007 coursework science video. falsecolor art direction: data passes for the pocket with 048 (T5 still). Built on S2plus/code/render_048.py and pocket048.py, which are left as they were.

blender -b -t 4 -P bl_pocket_pass.py -- --out DIR [--zoom 1.0 --px 1260 --py 540]

Writes 16-bit grey PNGs, the pocket048 camera scaled and moved, frame 1920x1080:
  t5_mask  pocket surface coverage     t5_dist  distance from each surface point to the nearest heavy atom of 048, Å / 8
  t5_ao    crevices                    t5_lig   048 coverage     t5_ligshade  048 matte shade
The pose is OUR RE-DOCKING, AutoDock Vina, never a measured structure. The on-screen plate says so.
"""
import argparse, math, os, sys, time
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
S2CODE = os.path.normpath(os.path.join(HERE, "..", "..", "..", "S2plus", "code"))
sys.path.insert(0, S2CODE)
import pocket048 as G

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--zoom", type=float, default=1.0)
ap.add_argument("--px", type=float, default=1260)   # frame x where the middle of the pocket lands
ap.add_argument("--py", type=float, default=540)
ap.add_argument("--samples", type=int, default=64)
A = ap.parse_args(argv)
SC = 0.1

S, f, lo, d, verts, quads, hidden, ppa0, cx0, cy0 = G.build()
del f, d
L = S["lig"][S["heavy"]]
dv = np.full(len(verts), 1e9, np.float32)
for p in L.astype(np.float32):
    dv = np.minimum(dv, ((verts.astype(np.float32) - p) ** 2).sum(1))
dv = np.sqrt(dv)
vis = np.unique(quads[~hidden])
print("visible surface to ligand, Å: min %.2f p5 %.2f p50 %.2f p95 %.2f" % tuple(np.percentile(dv[vis], [0, 5, 50, 95])))

ppa = ppa0 * A.zoom
seen = verts[vis]
mid = (seen[:, :2].min(0) + seen[:, :2].max(0)) / 2

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dev in prefs.devices:
    dev.use = dev.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples = "GPU", A.samples
c_.use_denoising = False
c_.max_bounces = 0
c_.seed, c_.use_animated_seed = 0, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.view_settings.exposure, sc.view_settings.gamma = 0, 1
wd = bpy.data.worlds.new("w")
wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[1].default_value = 0
sc.world = wd
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth, st.compression = "PNG", "BW", "16", 40

P = lambda xyz: Vector((float(xyz[0]) * SC, float(xyz[1]) * SC, float(xyz[2]) * SC))


def mat(kind, masked=True):
    m = bpy.data.materials.new(kind)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    pw.inputs[0].default_value = 1
    nt.links.new(pw.outputs[0], em.inputs["Color"])
    if kind == "dist":
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name, at.attribute_type = "dist", "GEOMETRY"
        nt.links.new(at.outputs["Fac"], pw.inputs[0])
    elif kind == "ao":
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 16
        ao.inputs["Distance"].default_value = 0.5
        nt.links.new(ao.outputs["AO"], pw.inputs[0])
    elif kind == "shade":
        g = nt.nodes.new("ShaderNodeNewGeometry")
        dp = nt.nodes.new("ShaderNodeVectorMath")
        dp.operation = "DOT_PRODUCT"
        nt.links.new(g.outputs["Normal"], dp.inputs[0])
        dp.inputs[1].default_value = tuple(float(x) for x in G.LIGHT)
        cl = nt.nodes.new("ShaderNodeMath")
        cl.operation, cl.use_clamp = "MULTIPLY_ADD", True
        cl.inputs[1].default_value, cl.inputs[2].default_value = 0.5, 0.5
        nt.links.new(dp.outputs["Value"], cl.inputs[0])
        nt.links.new(cl.outputs[0], pw.inputs[0])
    link = em.outputs[0]
    if masked:
        # the flat cut and the crop walls stay out of the picture, through the same show attribute render_048.py uses
        at2 = nt.nodes.new("ShaderNodeAttribute")
        at2.attribute_name, at2.attribute_type = "show", "GEOMETRY"
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(at2.outputs["Fac"], gt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(gt.outputs[0], mx.inputs[0])
        blk = nt.nodes.new("ShaderNodeEmission")
        blk.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(blk.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2])
        link = mx.outputs[0]
    nt.links.new(link, out.inputs["Surface"])
    return m


me = bpy.data.meshes.new("pocket")
me.from_pydata((verts * SC).tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("show", "FLOAT", "POINT").data.foreach_set("value", G.show_mask(quads, hidden, len(verts)).tolist())
me.attributes.new("dist", "FLOAT", "POINT").data.foreach_set("value", (dv / 8).clip(0, 1).astype(float).tolist())
me.update()
ob = bpy.data.objects.new("pocket", me)
sc.collection.objects.link(ob)


def sphere(loc, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    return o


def cyl(a, b, r):
    a, b = Vector(a), Vector(b)
    dvv = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=dvv.length, location=(a + b) / 2, vertices=32)
    o = bpy.context.object
    o.rotation_euler = dvv.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.shade_smooth()
    return o


LL = S["lig"]
lig_obs = []
for el, xyz in zip(S["el"], LL):
    lig_obs.append(sphere(P(xyz), G.ATOM_R.get(el, 0.36) * SC))
for i, j, order in S["bonds"]:
    a, b = P(LL[i]), P(LL[j])
    r = G.STICK_R * SC if order < 1.9 else 0.085 * SC
    offs = [Vector()] if order < 1.9 else [((b - a).cross(Vector((0, 0, 1))).normalized() * 0.1 * SC * k) for k in (-1, 1)]
    for off in offs:
        lig_obs.append(cyl(a + off, b + off, r))
cut = G.cut_z(S)
for c in S["contacts"]:
    if c["rec"][2] >= cut or not c["partner"].startswith("Lys33"):
        continue
    lig_obs.append(sphere(P(c["rec"]), 0.24 * SC))
    a, b = P(c["lig"]), P(c["rec"])
    for k in range(7):
        lig_obs.append(cyl(a.lerp(b, k / 7), a.lerp(b, (k + 0.5) / 7), 0.09 * SC))

cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
cam_d.ortho_scale = 1080 / ppa * SC
cam_d.clip_start, cam_d.clip_end = 0.01, 20
cam = bpy.data.objects.new("cam", cam_d)
cam.location = ((mid[0] - (A.px - 960) / ppa) * SC, (mid[1] + (A.py - 540) / ppa) * SC, 5)
sc.collection.objects.link(cam)
sc.camera = cam

t = time.time()


def shot(name):
    sc.render.filepath = os.path.join(A.out, name + ".png")
    bpy.ops.render.render(write_still=True)


for o in lig_obs:
    o.hide_render = True
me.materials.append(mat("white"))
shot("t5_mask")
me.materials[0] = mat("dist")
shot("t5_dist")
me.materials[0] = mat("ao")
shot("t5_ao")
for o in lig_obs:
    o.hide_render = False
ob.hide_render = True
w, s = mat("white", False), mat("shade", False)
for o in lig_obs:
    o.data.materials.append(w)
shot("t5_lig")
for o in lig_obs:
    o.data.materials[0] = s
shot("t5_ligshade")
print("DONE %.1fs ppa %.2f" % (time.time() - t, ppa))
