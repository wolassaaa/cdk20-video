"""PULSE extra still, beat 1-04: "only about three in ten patients are alive five years on".
Ten bulbs of the same installation on their cables, three still lit, seven cold.
The cold ones show only as glass: two tall panels behind the row, invisible to the camera, give each globe a thin rim
crescent, because glass reflects strongly at grazing angles (a perfect mirror reflection, so nothing to converge).
blender -b --factory-startup -t 3 -P extra.py -- --out DIR/extra_ [--samples 2048]
"""
import bpy, bmesh, sys, math, argparse
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=2048)
A = ap.parse_args(argv)


def srgb2lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


BONE = srgb2lin("#EDEBE4")
RG, CAP_H = 0.024, 0.026

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def glass(name, glow):
    m, nt, out = nodes_mat(name)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.97, 0.97, 0.97, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.0
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
    nt.links.new(inv.outputs[0], pw.inputs[0])
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = glow
    nt.links.new(pw.outputs[0], sc.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*BONE, 1)
    nt.links.new(sc.outputs[0], em.inputs["Strength"])
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mx.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], out.inputs["Surface"])
    m.cycles.emission_sampling = "NONE"
    return m


def emit(name, strength, sampling="AUTO"):
    m, nt, out = nodes_mat(name)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*BONE, 1); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.cycles.emission_sampling = sampling
    return m


def dark(name, rough, base, spec):
    m, nt, out = nodes_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (base, base, base, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = spec
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


m_on, m_off = emit("fil_on", 8.0), dark("fil_off", 0.45, 0.05, 0.5)
g_on, g_off = glass("g_on", 0.55), glass("g_off", 0.0)
m_cap, m_cab = dark("cap", 0.32, 0.02, 0.6), dark("cable", 0.3, 0.012, 0.5)


def bulb_mesh(name, mg, mf):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=RG)
    for f in bm.faces: f.material_index = 0; f.smooth = True
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0085, radius2=0.0085, depth=CAP_H)
    for v in g["verts"]: v.co.z += RG + CAP_H / 2 - 0.004
    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = 2; f.smooth = True
    pts = []
    turns, hh, rr = 3.5, 0.020, 0.0055
    for k in range(141):
        t = k / 140; a = t * turns * 2 * math.pi
        pts.append(Vector((rr * math.cos(a), rr * math.sin(a), -hh / 2 + hh * t)))

    def tube(path, rad, segs=6):
        rings = []
        for k, p in enumerate(path):
            t = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
            n = t.cross(Vector((0, 0, 1)))
            if n.length < 1e-4: n = t.cross(Vector((1, 0, 0)))
            n.normalize(); b = t.cross(n)
            rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * s / segs) + b * math.sin(2 * math.pi * s / segs)) * rad) for s in range(segs)])
        for r0, r1 in zip(rings, rings[1:]):
            for s in range(segs):
                f = bm.faces.new((r0[s], r0[(s + 1) % segs], r1[(s + 1) % segs], r1[s])); f.material_index = 1; f.smooth = True
    tube(pts, 0.00075)
    for a_, b_ in ((Vector((rr, 0, -hh / 2)), Vector((0.0025, 0, RG - 0.006))), (pts[-1].copy(), Vector((-0.0025, 0, RG - 0.006)))):
        tube([a_.lerp(b_, t / 8) for t in range(9)], 0.00035, 5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (mg, mf, m_cap): me.materials.append(m)
    return me


me_on, me_off = bulb_mesh("on", g_on, m_on), bulb_mesh("off", g_off, m_off)

# ten in a row, all inside the frame, heights a little uneven, hand-hung
rng = np.random.default_rng(10)
LIT = {1, 4, 8}
xs = (np.arange(10) - 4.5) * 0.15
zs = 1.60 + rng.uniform(-0.035, 0.035, 10)
ys = rng.uniform(-0.03, 0.03, 10)
cv, cf = [], []
for i in range(10):
    o = bpy.data.objects.new("b%d" % i, me_on if i in LIT else me_off)
    o.location = (xs[i], ys[i], zs[i]); o.rotation_euler = (0, 0, float(rng.random() * 6.28))
    scn.collection.objects.link(o)
    z0 = zs[i] + RG + CAP_H - 0.005; base = len(cv)
    for s in range(6):
        a = 2 * math.pi * s / 6; dx, dy = 0.0018 * math.cos(a), 0.0018 * math.sin(a)
        cv.append((xs[i] + dx, ys[i] + dy, z0)); cv.append((xs[i] + dx, ys[i] + dy, 8.0))
    for s in range(6):
        a0, a1 = base + 2 * s, base + 2 * ((s + 1) % 6); cf.append((a0, a1, a1 + 1, a0 + 1))
cme = bpy.data.meshes.new("cables"); cme.from_pydata(cv, [], cf)
for p in cme.polygons: p.use_smooth = True
cme.materials.append(m_cab)
scn.collection.objects.link(bpy.data.objects.new("cables", cme))

# two tall strips behind the row, seen only in the glass, as rim crescents
for sx_ in (-1, 1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(sx_ * 2.3, 2.1, 1.6))
    pl = bpy.context.active_object; pl.scale = (0.5, 3.2, 1)
    pl.rotation_euler = (Vector((0, 0, 1.6)) - pl.location).to_track_quat("Z", "Y").to_euler()
    pl.visible_camera = False; pl.visible_diffuse = False; pl.visible_shadow = False
    pl.data.materials.append(emit("panel%d" % sx_, 2.6, "NONE"))

w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

camd = bpy.data.cameras.new("cam"); camd.lens = 50; camd.sensor_width = 36
cam = bpy.data.objects.new("cam", camd); scn.collection.objects.link(cam); scn.camera = cam
loc = Vector((0.0, -2.24, 1.34)); tgt = Vector((0.0, 0.0, 1.40))
cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
camd.dof.use_dof = True; camd.dof.focus_distance = 2.24; camd.dof.aperture_fstop = 8.0; camd.dof.aperture_blades = 0

scn.render.engine = "CYCLES"
pref = bpy.context.preferences.addons["cycles"].preferences
pref.compute_device_type = "OPTIX"; pref.get_devices()
for d in pref.devices: d.use = (d.type == "OPTIX")
scn.cycles.device = "GPU"; scn.cycles.samples = A.samples
scn.cycles.use_adaptive_sampling = True; scn.cycles.adaptive_threshold = 0.004
scn.cycles.use_denoising = True; scn.cycles.denoiser = "OPTIX"; scn.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scn.cycles.max_bounces = 8; scn.cycles.glossy_bounces = 3; scn.cycles.transparent_max_bounces = 24
scn.cycles.caustics_refractive = False; scn.cycles.caustics_reflective = False
scn.cycles.blur_glossy = 0.0; scn.cycles.sample_clamp_direct = 6.0; scn.cycles.sample_clamp_indirect = 4.0
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.view_settings.view_transform = "Standard"; scn.view_settings.look = "None"
ims = scn.render.image_settings
ims.file_format = "OPEN_EXR"; ims.color_mode = "RGB"; ims.color_depth = "16"; ims.exr_codec = "ZIP"
scn.render.filepath = A.out + "0000.exr"
bpy.ops.render.render(write_still=True)
print("extra done", scn.render.filepath)
