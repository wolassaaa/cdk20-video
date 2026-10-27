"""Render a docked pose (from export_poses.py) inside the CDK20 hologram.

Run: blender -b -P render_poses.py -- <poses.json> <outdir> <001|048>
Ligand as solid ball-and-stick (CPK-like colours), protein as dim hologram trace, Met84/Lys33/Ile10 as thin sticks,
hydrogen bonds as glowing dashes (orange for the pyrazole-Lys33 contact that 048 adds).
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
DATA, OUT, LIG = json.load(open(argv[0])), argv[1].rstrip("/\\"), argv[2]
pose = DATA["poses"][LIG]
S = 0.1  # 1 Å -> 0.1 m

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device, sc.cycles.samples = "GPU", 512
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Base Contrast"
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.002, 0.003, 0.006, 1)
sc.world = w

lig_xyz = [Vector(a[1:]) for a in pose["atoms"]]
centre = sum(lig_xyz, Vector()) / len(lig_xyz)
P = lambda xyz: (Vector(xyz) - centre) * S

def solid(name, color, rough=0.35, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.3
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m

def glow(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m

def holo(name, color, strength, edge=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = edge
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], mix.inputs["Fac"])
    nt.links.new(t.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

EL = {"C": ((0.80, 0.80, 0.78), 0.34), "N": ((0.22, 0.42, 1.0), 0.32), "O": ((1.0, 0.22, 0.15), 0.32), "H": ((0.95, 0.95, 0.95), 0.18), "S": ((1.0, 0.85, 0.2), 0.4)}
mats = {k: solid(k, c) for k, (c, _) in EL.items()}
rmats = {k: solid("r" + k, tuple(0.35 + 0.4 * v for v in c), rough=0.5) for k, (c, _) in EL.items()}

def sphere(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o

def cyl(a, b, r, mat):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=20)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o

# ligand: ball-and-stick; double bonds drawn as two thinner offset sticks
for el, *xyz in pose["atoms"]:
    sphere(P(xyz), EL.get(el, EL["C"])[1] * S, mats.get(el, mats["C"]))
for i, j, order in pose["bonds"]:
    a, b = P(pose["atoms"][i][1:]), P(pose["atoms"][j][1:])
    ei, ej = pose["atoms"][i][0], pose["atoms"][j][0]
    mid = (a + b) / 2
    r = 0.11 * S if order < 1.9 else 0.075 * S
    offs = [Vector()] if order < 1.9 else [((b - a).cross(Vector((0, 0, 1))).normalized() * 0.09 * S * k) for k in (-1, 1)]
    for off in offs:  # half-bond colouring
        cyl(a + off, mid + off, r, mats.get(ei, mats["C"]))
        cyl(mid + off, b + off, r, mats.get(ej, mats["C"]))

# key residues as thin sticks, bonds inferred by distance
for label, res in DATA["residues"].items():
    if label not in ("Met84", "Lys33", "Ile10"):
        continue
    ats = [(n, el, P(xyz)) for n, el, *xyz in res["atoms"]]
    for n, el, p in ats:
        sphere(p, 0.12 * S, rmats.get(el, rmats["C"]))
    for k in range(len(ats)):
        for m in range(k + 1, len(ats)):
            if (ats[k][2] - ats[m][2]).length < 1.9 * S:
                cyl(ats[k][2], ats[m][2], 0.06 * S, rmats["C"])

# protein backbone hologram (residues 1-302)
cd = bpy.data.curves.new("trace", "CURVE")
cd.dimensions, cd.bevel_depth, cd.bevel_resolution, cd.resolution_u = "3D", 0.12 * S, 4, 8
sp = cd.splines.new("NURBS")
pts = [P(c[1:]) for c in DATA["ca"]]
sp.points.add(len(pts) - 1)
for k, p in enumerate(pts):
    sp.points[k].co = (*p, 1)
sp.use_endpoint_u, sp.order_u = True, 4
tr = bpy.data.objects.new("trace", cd)
tr.data.materials.append(holo("holo", (0.25, 0.85, 1.0), 0.6))
sc.collection.objects.link(tr)

# hydrogen bonds as dashes
for c in pose["contacts"]:
    a, b = P(c["lig"]), P(c["rec"])
    lys = c["partner"].startswith("Lys33")
    col = (1.0, 0.30, 0.04) if lys else (1.0, 0.78, 0.15)
    m = glow("hb", col, 3.5)
    n = 7
    for k in range(n):
        t0, t1 = k / n, (k + 0.5) / n
        cyl(a.lerp(b, t0), a.lerp(b, t1), (0.09 if lys else 0.06) * S, m)

# lights + camera looking at the ligand face-on (normal of its best-fit plane)
import numpy as np
X = np.array([list(P(a[1:])) for a in pose["atoms"]])
_, _, vt = np.linalg.svd(X - X.mean(axis=0))
normal = Vector(vt[2].tolist())
if normal.z < 0:
    normal = -normal
view = (normal + Vector((0.15, -0.25, 0.35))).normalized()
extent = max((Vector(p) - Vector()).length for p in X.tolist())
for name, off, e, col in (("key", Vector((2, -2, 3)), 220, (1, 0.96, 0.92)), ("rim", Vector((-3, 2, 1)), 160, (0.6, 0.8, 1)), ("fill", Vector((-1, -3, -1)), 50, (1, 0.9, 0.8))):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.color, ld.size = e, col, 1.5
    lo = bpy.data.objects.new(name, ld)
    lo.location = view * 3 + off
    lo.rotation_euler = (-lo.location).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(lo)
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 50
dist = extent * 6.5
cam_d.dof.use_dof, cam_d.dof.aperture_fstop, cam_d.dof.focus_distance = True, 4.0, dist
# slab view: clip away the protein between the camera and the front of the pocket
cam_d.clip_start = dist - extent * 1.8
cam = bpy.data.objects.new("cam", cam_d)
cam.location = view * dist
cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.filepath = f"{OUT}/pose_{LIG}_raw.png"
import os
sys.path.append(os.environ.get("CLIP_HELPER_DIR", ""))
if os.environ.get("CLIP_SECONDS"):
    from clip_anim import render_clip  # moving version for the music test
    render_clip(sc, cam, (0, 0, 0))
else:
    bpy.ops.render.render(write_still=True)
print("DONE", LIG)
