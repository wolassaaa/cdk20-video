"""HKBU SCIE1007 coursework science video. Arena direction: a grey clay stand-in for a member's phone footage, in an ordinary warm room, as a phone would see it.
Run through the GPU queue, writes ../_work/person.npy (linear RGB, 1000 x 1000). The real film swaps this for the member's own shot."""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector
WORK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work"))
bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "GPU", 128, True
sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
sc.view_settings.view_transform = "Standard"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGB", "32"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 0.82, 0.62, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
sc.world = w
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "S2plus", "code")))
import pocket048 as G5

H = 0.006
ax = [np.arange(-.62, .62, H), np.arange(-.34, .34, H), np.arange(.42, 1.92, H)]
X, Y, Z = np.meshgrid(*ax, indexing="ij")
F = np.zeros(X.shape, np.float32)


def E(x, y, z, sx, sy, sz, k=4.0, w=1.0):
    global F
    d2 = ((X - x) / sx) ** 2 + ((Y - y) / sy) ** 2 + ((Z - z) / sz) ** 2
    F += (w * np.exp(-k * (d2 - 1))).astype(np.float32)


E(0, 0, 1.62, .120, .142, .155, 5)               # cranium
E(0, -.02, 1.525, .092, .102, .090, 5)           # jaw
E(0, -.118, 1.655, .082, .022, .016, 7, .7)      # brow
E(0, -.150, 1.585, .017, .034, .042, 6, .9)      # nose
E(0, -.128, 1.513, .036, .014, .009, 7, .8)      # upper lip
E(0, -.122, 1.490, .030, .014, .009, 7, .8)      # lower lip
E(0, -.098, 1.452, .030, .02, .018, 6, .8)       # chin
for sx in (-1, 1):
    E(sx * .116, .0, 1.590, .012, .026, .040, 6, .9)      # ears
    E(sx * .050, -.128, 1.622, .026, .022, .013, 7, -1.5)   # eye sockets
    E(sx * .050, -.112, 1.621, .014, .012, .010, 7, .55)   # lids
E(0, .03, 1.71, .122, .135, .090, 5)             # hair
E(0, -.055, 1.745, .100, .070, .040, 5)
E(0, .08, 1.62, .115, .085, .13, 5)
E(0, .012, 1.42, .070, .074, .10, 3.5)            # neck
E(0, .03, 1.345, .155, .085, .065, 3)              # trapezius
E(0, .03, 1.18, .225, .125, .18, 2.5)             # chest
E(.245, .03, 1.245, .080, .085, .090, 3); E(-.245, .03, 1.245, .080, .085, .090, 3)
E(.285, .03, 1.02, .066, .074, .22, 3); E(-.285, .03, 1.02, .066, .074, .22, 3)
E(0, .04, .90, .215, .13, .24, 2.5)
verts, quads = G5.surface_nets(F - 1, np.array([ax[0][0], ax[1][0], ax[2][0]], np.float32), H, relax=3)
me = bpy.data.meshes.new("b")
me.from_pydata(verts.tolist(), [], quads.tolist())
# paint by position, so the stand-in has hair, a jumper, brows, eyes and a mouth. Still a stand-in, but it reads as a person on a wall
vx, vy, vz = verts[:, 0], verts[:, 1], verts[:, 2]
col = np.tile(np.array([.46, .42, .40]), (len(verts), 1))
col[vz < 1.355 + .4 * np.abs(vx)] = (.05, .058, .075)
col[vz > 1.71 - .9 * np.clip(vy + .10, 0, None)] = (.045, .04, .036)
col[(np.abs(vz - 1.502) < .007) & (np.abs(vx) < .031) & (vy < -.09)] = (.37, .29, .27)
for sx in (-1, 1):
    col[(((vx - sx * .050) / .019) ** 2 + ((vz - 1.621) / .0105) ** 2 < 1) & (vy < -.08)] = (.03, .025, .022)
    bx = np.abs(vx - sx * .052) < .037
    col[bx & (np.abs(vz - 1.657 - .12 * (np.abs(vx) - .05)) < .0065) & (vy < -.07)] = (.05, .04, .035)
for po in me.polygons:
    po.use_smooth = True
at_ = me.attributes.new("col", "FLOAT_COLOR", "POINT")
at_.data.foreach_set("color", np.c_[col, np.ones(len(col))].astype(np.float32).ravel().tolist())
me.update()
ob = bpy.data.objects.new("b", me)
sc.collection.objects.link(ob)
m = bpy.data.materials.new("clay"); m.use_nodes = True
p = m.node_tree.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = .55
an = m.node_tree.nodes.new("ShaderNodeAttribute"); an.attribute_name = "col"
m.node_tree.links.new(an.outputs["Color"], p.inputs["Base Color"])
me.materials.append(m)


def solid(col, em=0):
    q = bpy.data.materials.new("s"); q.use_nodes = True
    n = q.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = (*col, 1)
    if em:
        n.inputs["Emission Color"].default_value = (*col, 1); n.inputs["Emission Strength"].default_value = em
    return q


# an ordinary room: a wall, a shelf with books, a window, all out of focus
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 1.6, 1.3), rotation=(math.pi / 2, 0, 0))
bpy.context.object.data.materials.append(solid((.30, .23, .17)))
bpy.ops.mesh.primitive_cube_add(size=1, location=(-.95, 1.5, 1.42))
bpy.context.object.scale = (.9, .12, .05)
bpy.context.object.data.materials.append(solid((.20, .12, .07)))
for x, h, c in ((-1.25, .26, (.5, .2, .1)), (-1.08, .21, (.15, .25, .3)), (-.92, .28, (.7, .6, .4)), (-.78, .23, (.3, .15, .15))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 1.5, 1.45 + h / 2))
    bpy.context.object.scale = (.1, .1, h)
    bpy.context.object.data.materials.append(solid(c))
bpy.ops.mesh.primitive_plane_add(size=1, location=(1.75, 1.58, 1.55), rotation=(math.pi / 2, 0, 0))
bpy.context.object.scale = (.9, 1.2, 1)
bpy.context.object.data.materials.append(solid((1, .9, .75), 0.9))
# window key from camera left, warm lamp from the right
for pos, en, sz, col in (((-1.5, -2.0, 2.0), 70, 1.2, (1, .86, .70)), ((1.8, -0.6, 1.5), 16, 0.8, (1, .62, .36))):
    l = bpy.data.lights.new("a", "AREA"); l.energy, l.size, l.color = en, sz, col
    o = bpy.data.objects.new("a", l); sc.collection.objects.link(o); o.location = pos
    o.rotation_euler = (Vector((0, 0, 1.6)) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
cd = bpy.data.cameras.new("c"); cd.lens = 66; cd.sensor_width = 36
cd.dof.use_dof, cd.dof.focus_distance, cd.dof.aperture_fstop = True, 2.36, 2.8
c = bpy.data.objects.new("c", cd); sc.collection.objects.link(c)
c.location = (.0, -2.5, 1.44)
c.rotation_euler = (Vector((0, 0, 1.46)) - Vector(c.location)).to_track_quat("-Z", "Y").to_euler()
sc.camera = c
exr = os.path.join(WORK, "person.exr")
sc.render.filepath = exr
bpy.ops.render.render(write_still=True)
im = bpy.data.images.load(exr)
a = np.empty(1000 * 1000 * 4, np.float32); im.pixels.foreach_get(a)
np.save(os.path.join(WORK, "person.npy"), a.reshape(1000, 1000, 4)[::-1, :, :3].copy())
print("DONE person")
