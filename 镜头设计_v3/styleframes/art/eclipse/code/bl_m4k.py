"""HKBU SCIE1007 coursework science video. Eclipse direction, 4K60 delivery of the one-take: renders the real CDK20 surface passes sharp enough for 4K.
Orthographic, straight down the view used in the film, 56 px per Angstrom. Writes normal, depth and coverage as raw float arrays for numpy. Run through gpu_slot.sh."""
import time
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
OUT = ROOT / "styleframes/art/eclipse/_work/m4k"
OUT.mkdir(exist_ok=True)
MS, MW = 56.0, 5200

D = np.load(ROOT / "styleframes/S2plus/_work/cdk20_surface.npz")
v, q = D["verts"].astype(np.float64), D["quads"].astype(np.int64)
cen = (v.min(0) + v.max(0)) / 2


def base_view():
    z = np.array([0.15, -0.25, 1.0])
    z /= np.linalg.norm(z)
    x = np.cross([0, 1, 0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z])


p = (v - cen) @ base_view().T
a, b, d = p[q[:, 0]], p[q[:, 1]], p[q[:, 3]]
fn = np.cross(b - a, d - a)
if np.sum(((a + b + d) / 3) * fn) < 0:
    q = q[:, ::-1]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
me = bpy.data.meshes.new("cdk20")
me.from_pydata(p.tolist(), [], q.tolist())
me.update()
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
me.update()
ob = bpy.data.objects.new("cdk20", me)
sc = bpy.context.scene
sc.collection.objects.link(ob)
cam = bpy.data.cameras.new("c")
cam.type, cam.ortho_scale = "ORTHO", MW / MS
cam.clip_start, cam.clip_end = 1, 400
co = bpy.data.objects.new("c", cam)
co.location = (0, 0, 120)
sc.collection.objects.link(co)
sc.camera = co
sc.render.engine = "CYCLES"
pr = bpy.context.preferences.addons["cycles"].preferences
pr.compute_device_type = "OPTIX"
pr.get_devices()
for dv in pr.devices:
    dv.use = dv.type == "OPTIX"
sc.cycles.device = "GPU"
sc.cycles.samples = 16
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 0
sc.cycles.use_auto_tile = True
sc.cycles.tile_size = 2048
sc.render.resolution_x, sc.render.resolution_y = MW, MW
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"
w = bpy.data.worlds.new("w")
sc.world = w


def material(name, fn_):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    e, o = n.new("ShaderNodeEmission"), n.new("ShaderNodeOutputMaterial")
    l.new(fn_(n, l), e.inputs["Color"])
    l.new(e.outputs[0], o.inputs["Surface"])
    return m


def f_normal(n, l):
    g, a_, b_ = n.new("ShaderNodeNewGeometry"), n.new("ShaderNodeVectorMath"), n.new("ShaderNodeVectorMath")
    a_.operation, b_.operation = "MULTIPLY", "ADD"
    a_.inputs[1].default_value = (0.5, 0.5, 0.5)
    b_.inputs[1].default_value = (0.5, 0.5, 0.5)
    l.new(g.outputs["Normal"], a_.inputs[0])
    l.new(a_.outputs[0], b_.inputs[0])
    return b_.outputs[0]


def f_depth(n, l):
    g, s_, m_ = n.new("ShaderNodeNewGeometry"), n.new("ShaderNodeSeparateXYZ"), n.new("ShaderNodeMapRange")
    m_.inputs["From Min"].default_value, m_.inputs["From Max"].default_value = -45, 45
    l.new(g.outputs["Position"], s_.inputs[0])
    l.new(s_.outputs["Z"], m_.inputs["Value"])
    return m_.outputs["Result"]


me.materials.append(bpy.data.materials.new("x"))
t0 = time.time()
for name, fn_ in (("normal", f_normal), ("depth", f_depth)):
    me.materials[0] = material(name, fn_)
    sc.render.filepath = str(OUT / f"_{name}.exr")
    bpy.ops.render.render(write_still=True)
    print("rendered", name, time.time() - t0, flush=True)
    im = bpy.data.images.load(sc.render.filepath)
    px = np.empty(MW * MW * 4, np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(MW, MW, 4)[::-1]
    al = px[..., 3].copy()
    un = np.maximum(al, 1e-3)[..., None]
    if name == "normal":
        n3 = px[..., :3] / un * 2 - 1
        n3 = n3 * (al[..., None] > 0.001)
        nl = np.maximum(np.sqrt((n3 ** 2).sum(-1, keepdims=True)), 1e-5)
        np.save(OUT / "normal.npy", (n3 / nl).astype(np.float32))
        np.save(OUT / "mask.npy", al)
    else:
        np.save(OUT / "depth.npy", ((px[..., 0] / un[..., 0]) * 90 - 45) * (al > 0.001))
    bpy.data.images.remove(im)
    Path(sc.render.filepath).unlink()
print("done", time.time() - t0, flush=True)
