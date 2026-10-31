"""HKBU SCIE1007 coursework science video. Pigment direction, T5: the real pocket as a depth map for contour lines, plus the 048 pose as plain coordinates for the outline drawing.

Run: bash gpu_slot.sh blender -b -t 4 -P bl_pocket.py -- --out <dir> [--ppa 21] [--xc 1400] [--yc 500]
Uses the S2plus geometry unchanged (pocket048.py, our AutoDock Vina pose, never a measured structure).
Writes pocket_z.png: 16 bit, R = depth 0-1 over zlo..zhi, G = visible wall (1) or flat cut (0). And pocket.json: ligand atoms and bonds in frame px, the z range, the scale.
"""
import argparse, json, os, sys
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, "..", "..", "..", "S2plus", "code"))
sys.path.insert(0, S2)
sys.dont_write_bytecode = True
import pocket048 as G

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ppa", type=float, default=21)
ap.add_argument("--xc", type=float, default=1400)
ap.add_argument("--yc", type=float, default=500)
ap.add_argument("--roll", type=float, default=0)
A = ap.parse_args(argv)
OUT = A.out.rstrip("/\\")
os.makedirs(OUT, exist_ok=True)
SC = 0.1

S, f, lo, d, verts, quads, hidden, ppa0, cx0, cy0 = G.build()
del f, d
show = G.show_mask(quads, hidden, len(verts))
seen = verts[np.unique(quads[~hidden])]
mid = (seen[:, :2].min(0) + seen[:, :2].max(0)) / 2
zlo, zhi = float(seen[:, 2].min()), float(seen[:, 2].max())
print("pocket extent A:", seen.min(0).round(1), seen.max(0).round(1), "zlo,zhi", zlo, zhi, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples, c_.use_denoising, c_.use_adaptive_sampling = "GPU", 16, False, False
c_.max_bounces = 0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 3840, 2160, 100
sc.render.film_transparent = False
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
sc.render.dither_intensity = 0

me = bpy.data.meshes.new("pocket")
me.from_pydata((verts * SC).tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("show", "FLOAT", "POINT").data.foreach_set("value", show.tolist())
me.update()
ob = bpy.data.objects.new("pocket", me)
sc.collection.objects.link(ob)

m = bpy.data.materials.new("z")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
L = nt.links.new
geo, sep, rng, at, gt, comb, em, out = (nt.nodes.new(k) for k in ("ShaderNodeNewGeometry", "ShaderNodeSeparateXYZ", "ShaderNodeMapRange", "ShaderNodeAttribute", "ShaderNodeMath", "ShaderNodeCombineXYZ", "ShaderNodeEmission", "ShaderNodeOutputMaterial"))
at.attribute_name, at.attribute_type = "show", "GEOMETRY"
gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
L(geo.outputs["Position"], sep.inputs[0])
L(sep.outputs["Z"], rng.inputs["Value"])
rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = zlo * SC, zhi * SC
rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = 0, 1
L(rng.outputs["Result"], comb.inputs[0]); L(at.outputs["Fac"], gt.inputs[0]); L(gt.outputs[0], comb.inputs[1])
L(comb.outputs[0], em.inputs["Color"]); L(em.outputs[0], out.inputs["Surface"])
me.materials.append(m)

cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
cam_d.ortho_scale = 1080 / A.ppa * SC
cam_d.clip_start, cam_d.clip_end = 0.01, 40
cam = bpy.data.objects.new("cam", cam_d)
camx = float(mid[0]) + (960 - A.xc) / A.ppa
camy = float(mid[1]) + (A.yc - 540) / A.ppa
cam.location = (camx * SC, camy * SC, 8)
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.filepath = f"{OUT}/pocket_z.exr"
bpy.ops.render.render(write_still=True)
im = bpy.data.images.load(f"{OUT}/pocket_z.exr")
im.colorspace_settings.name = "Non-Color"
px_ = np.empty(3840 * 2160 * 4, np.float32)
im.pixels.foreach_get(px_)
np.save(f"{OUT}/pocket_z.npy", px_.reshape(2160, 3840, 4)[::-1, :, :2].copy())

lig = S["lig"]
px = lambda p: (960 + (p[0] - camx) * A.ppa, 540 - (p[1] - camy) * A.ppa)
json.dump(dict(ppa=A.ppa, zlo=zlo, zhi=zhi, atoms=[dict(el=e, x=px(p)[0], y=px(p)[1], z=float(p[2]), r=G.ATOM_R.get(e, 0.36)) for e, p in zip(S["el"], lig)],
               bonds=[dict(i=int(i), j=int(j), order=float(o)) for i, j, o in S["bonds"]], vina=str(S["vina"]), mode=str(S["mode"])), open(f"{OUT}/pocket.json", "w"))
print("DONE", flush=True)
