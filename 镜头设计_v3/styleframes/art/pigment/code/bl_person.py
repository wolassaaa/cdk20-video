"""HKBU SCIE1007 coursework science video. Pigment direction, T2: a warm stand-in for a team member's phone clip, only to show how the torn photo holds a person.

Run: bash gpu_slot.sh blender -b -t 4 -P bl_person.py -- --out <dir>
It is a placeholder, not footage: a plain bust with no real face, in a window-side room thrown out of focus, the kind of frame a phone gives. Replaced by the real clip later.
The bust is a smooth blend of ellipsoids meshed with the same surface nets as the pocket, so there are no seams.
"""
import argparse, math, os, sys
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..", "S2plus", "code")))
sys.dont_write_bytecode = True
import pocket048 as G

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples, c_.use_denoising, c_.denoiser = "GPU", 128, True, "OPTIX"
c_.seed, c_.use_animated_seed = 0, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1500, 1600, 100
sc.view_settings.view_transform, sc.view_settings.look = "AgX", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "PNG", "RGB", "8"
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 0.86, 0.72, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
sc.world = w

# implicit bust on a grid, metres, x right, y to the back, z up
h = 0.005
lo = np.array([-0.46, -0.20, -1.00])
hi = np.array([0.46, 0.24, 0.17])
n = np.ceil((hi - lo) / h).astype(int) + 1
ax = [(lo[i] + h * np.arange(n[i])).astype(np.float32) for i in range(3)]
K = 2.6


def ell(c, r, w_=1.0, k=K):
    d2 = ((ax[0][:, None, None] - c[0]) / r[0]) ** 2 + ((ax[1][None, :, None] - c[1]) / r[1]) ** 2 + ((ax[2][None, None, :] - c[2]) / r[2]) ** 2
    return w_ * np.exp(-k * (d2 - 1))


F = ell((0, 0.008, 0.0), (0.082, 0.098, 0.112))        # skull
F += ell((0, -0.012, -0.075), (0.058, 0.066, 0.062))   # jaw
F += ell((0, 0.018, -0.135), (0.050, 0.054, 0.085))      # neck
F += ell((0, 0.03, -0.47), (0.215, 0.115, 0.30))       # chest
for s in (-1, 1):
    F += ell((s * 0.11, 0.03, -0.232), (0.12, 0.075, 0.052))   # trapezius into the shoulder
    F += ell((s * 0.21, 0.035, -0.275), (0.070, 0.075, 0.070))  # shoulder
    F += ell((s * 0.262, 0.04, -0.59), (0.062, 0.075, 0.33))   # arm
F += ell((0, 0.022, 0.030), (0.092, 0.108, 0.104), 1.0, 3.2)   # hair volume, a little over the skull
verts, quads = G.surface_nets((F - 1).astype(np.float32), lo.astype(np.float32), h, relax=4)
print(len(verts), "verts", flush=True)
x, y, z = verts.T

# colour by place: face oval and neck are skin, the rest of the head hair, below the collar shirt
sm_ = lambda a, b, t: (lambda u: u * u * (3 - 2 * u))(np.clip((t - a) / (b - a), 0, 1))
srgb = lambda hx: np.array([int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]) ** 2.2
skin, hair, shirt = srgb("C8906A"), srgb("231712"), srgb("3F5361")
hl = 0.060 - 0.85 * np.maximum(np.abs(x) - 0.035, 0)      # hairline falls at the temples
hairm = sm_(0.0, 0.010, z - hl) * (z > -0.10)
hairm = np.maximum(hairm, sm_(0.02, 0.035, y) * sm_(-0.095, -0.085, z))
collar = -0.172 - 0.05 * np.exp(-(x / 0.05) ** 2)
shirtm = sm_(-0.003, 0.003, collar - z)
col = skin[None] * (1 - shirtm[:, None]) + shirt[None] * shirtm[:, None]
col = col * (1 - hairm[:, None]) + hair[None] * hairm[:, None]

me = bpy.data.meshes.new("bust")
me.from_pydata(verts.tolist(), [], quads.tolist())
for p in me.polygons:
    p.use_smooth = True
at = me.color_attributes.new("c", "FLOAT_COLOR", "POINT")
rgba = np.ones((len(verts), 4)); rgba[:, :3] = col
at.data.foreach_set("color", rgba.ravel())
me.update()
body = bpy.data.objects.new("bust", me)
sc.collection.objects.link(body)
m = bpy.data.materials.new("skin")
m.use_nodes = True
nt = m.node_tree
pb = nt.nodes["Principled BSDF"]
ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "c"
nt.links.new(ca.outputs[0], pb.inputs["Base Color"])
pb.inputs["Roughness"].default_value = 0.52
pb.inputs["Subsurface Weight"].default_value = 0.3
pb.inputs["Subsurface Radius"].default_value = (0.05, 0.02, 0.01)
pb.inputs["Subsurface Scale"].default_value = 0.03
me.materials.append(m)
body.rotation_euler = (0, 0, math.radians(-7))


def emis(name, rgb, strength):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    t = mt.node_tree
    t.nodes.clear()
    e, o = t.nodes.new("ShaderNodeEmission"), t.nodes.new("ShaderNodeOutputMaterial")
    e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    t.links.new(e.outputs[0], o.inputs["Surface"])
    return mt


def box(loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = size
    o.data.materials.append(mat)
    return o


wallm = bpy.data.materials.new("wall")
wallm.use_nodes = True
wallm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.74, 0.60, 0.46, 1)
box((0, 3.2, 0), (6, 0.05, 4), wallm)
box((-1.55, 3.05, 0.35), (0.62, 0.05, 1.15), emis("win", (1.0, 0.95, 0.85), 5.0))   # window
shelf = bpy.data.materials.new("shelf")
shelf.use_nodes = True
shelf.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.24, 0.15, 0.09, 1)
for i in range(4):
    box((1.5, 3.0, -0.9 + i * 0.62), (0.75, 0.2, 0.03), shelf)
    for k in range(7):
        c = [(0.6, 0.2, 0.12), (0.8, 0.65, 0.35), (0.2, 0.3, 0.35), (0.7, 0.7, 0.6)][(i * 3 + k) % 4]
        bm = bpy.data.materials.new("b"); bm.use_nodes = True
        bm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c, 1)
        box((0.92 + k * 0.17, 2.95, -0.72 + i * 0.62), (0.07, 0.14, 0.15 + 0.03 * (k % 3)), bm)

ld = bpy.data.lights.new("win", "AREA")
ld.shape, ld.size, ld.size_y, ld.energy = "RECTANGLE", 1.6, 2.2, 150
ld.color = (1.0, 0.9, 0.78)
o = bpy.data.objects.new("win", ld)
o.location = (-1.4, -1.5, 0.7)
o.rotation_euler = (Vector((0, 0.1, -0.2)) - Vector(o.location)).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(o)
f = bpy.data.lights.new("fill", "AREA")
f.size, f.energy = 3, 9
f.color = (1.0, 0.75, 0.6)
o2 = bpy.data.objects.new("fill", f)
o2.location = (1.6, -1.2, 0.0)
o2.rotation_euler = (Vector((0, 0, -0.2)) - Vector(o2.location)).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(o2)

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 58
cam_d.dof.use_dof, cam_d.dof.aperture_fstop = True, 2.8
cam_d.dof.focus_distance = 1.46
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (0.04, -1.55, -0.17)
cam.rotation_euler = (Vector((0.0, 0, -0.20)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.filepath = f"{A.out}/person.png"
bpy.ops.render.render(write_still=True)
print("DONE", flush=True)
