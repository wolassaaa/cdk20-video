"""HKBU SCIE1007 coursework science video. Shared Blender set pieces for the darkroom art direction: render setup, lamps, paper, and a linear float dump for the grade."""
import math, os, sys, time, argparse
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
WORK = os.path.join(ROOT, "_work")
V3 = os.path.normpath(os.path.join(ROOT, "..", "..", ".."))


def args(extra=None):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--samples", type=int, default=160)
    ap.add_argument("--out", default="")
    if extra:
        extra(ap)
    return ap.parse_args(argv)


def setup(samples=160, pct=100, bounces=6, limit=150):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.refresh_devices()
    for dv in prefs.devices:
        dv.use = dv.type == "OPTIX"
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    c = sc.cycles
    c.device, c.samples = "GPU", samples
    c.use_adaptive_sampling, c.adaptive_threshold = True, 0.015
    c.time_limit = limit
    c.use_denoising, c.denoiser = True, "OPTIX"
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = bounces, 3, 4, 6, 12
    c.caustics_reflective, c.caustics_refractive = False, False
    c.seed, c.use_animated_seed = 7, False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, pct
    sc.view_settings.view_transform, sc.view_settings.look = "Raw", "None"
    st = sc.render.image_settings
    st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGB", "32"
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = w
    return sc


def render(sc, name):
    """Render to _work/<name>.exr and dump linear float RGB to _work/<name>.npy, top row first."""
    t = time.time()
    p = os.path.join(WORK, name + ".exr")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    im.colorspace_settings.name = "Non-Color"
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1, :, :3]
    np.save(os.path.join(WORK, name + ".npy"), a)
    print(f"DONE {name} {time.time() - t:.0f}s mean {a.mean(axis=(0, 1))} max {a.max():.2f}")


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return (*np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).tolist(), 1.0)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out


def pbr(name, col, rough=0.5, spec=0.5, metal=0.0):
    m, nt, out = new_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = col if len(col) == 4 else (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Metallic"].default_value = metal
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def emit(name, col, strength=1.0):
    m, nt, out = new_mat(name)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = col if len(col) == 4 else (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box(name, lo, hi, m):
    lo, hi = np.array(lo, float), np.array(hi, float)
    v = [[(lo, hi)[i & 1][0], (lo, hi)[i >> 1 & 1][1], (lo, hi)[i >> 2 & 1][2]] for i in range(8)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def camera(loc, tgt, lens=50, fstop=0, focus=None, roll=0):
    d = bpy.data.cameras.new("cam")
    d.lens, d.sensor_width = lens, 36
    d.clip_start, d.clip_end = 0.05, 400
    o = link(bpy.data.objects.new("cam", d))
    o.location = loc
    q = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y")
    o.rotation_euler = q.to_euler()
    if roll:
        o.rotation_euler.rotate_axis("Z", math.radians(roll))
    if fstop:
        d.dof.use_dof, d.dof.aperture_fstop = True, fstop
        d.dof.focus_distance = focus or (Vector(tgt) - Vector(loc)).length
    bpy.context.scene.camera = o
    return o


def area(name, loc, tgt, w, h, col, power, spread=None, visible=False):
    d = bpy.data.lights.new(name, "AREA")
    d.shape, d.size, d.size_y = "RECTANGLE", w, h
    d.color, d.energy = col[:3], power
    if spread:
        d.spread = math.radians(spread)
    o = link(bpy.data.objects.new(name, d))
    o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(tgt)).to_track_quat("Z", "Y").to_euler()
    o.visible_camera = visible
    return o


def spot(name, loc, tgt, col, power, size=0.5, cone=40, blend=0.6):
    d = bpy.data.lights.new(name, "SPOT")
    d.color, d.energy, d.shadow_soft_size = col[:3], power, size
    d.spot_size, d.spot_blend = math.radians(cone), blend
    o = link(bpy.data.objects.new(name, d))
    o.location = loc
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def sheet(name, w, h, loc=(0, 0, 0), rot=(0, 0, 0), nx=120, ny=90, warp=None, mat=None):
    """A sheet of paper in its local XY, UV 0..1, smooth, optional warp(u,v)->z in local units so fibre paper can cockle and curl."""
    xs, ys = np.linspace(-w / 2, w / 2, nx + 1), np.linspace(-h / 2, h / 2, ny + 1)
    X, Y = np.meshgrid(xs, ys)
    U, V = (X + w / 2) / w, (Y + h / 2) / h
    Z = warp(U, V) if warp else np.zeros_like(X)
    v = np.stack([X, Y, Z], -1).reshape(-1, 3)
    ix = np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1)
    q = np.stack([ix[:-1, :-1], ix[:-1, 1:], ix[1:, 1:], ix[1:, :-1]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], q.tolist())
    uv = me.uv_layers.new(name="UVMap")
    uvs = np.stack([U, V], -1).reshape(-1, 2)
    uv.data.foreach_set("uv", uvs[q.reshape(-1)].reshape(-1).tolist())
    for p in me.polygons:
        p.use_smooth = True
    if mat:
        me.materials.append(mat)
    me.update()
    o = link(bpy.data.objects.new(name, me))
    o.location, o.rotation_euler = loc, rot
    return o


def paper_mat(name, tex, rough=0.42, spec=0.5, bump=0.12, alpha=None, trans=0.0, trans_col=None):
    """Printed paper. tex is an sRGB PNG. A fine fixed bump gives the sheet a fibre that does not move. alpha: if set, the texture alpha cuts the sheet."""
    m, nt, out = new_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(tex)
    t.interpolation = "Cubic"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value, n.inputs["Detail"].default_value = 260, 6
    nt.links.new(tc.outputs["UV"], n.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value, bu.inputs["Distance"].default_value = bump, 0.02
    nt.links.new(n.outputs[0], bu.inputs["Height"])
    nt.links.new(bu.outputs[0], b.inputs["Normal"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def liquid(name, tint=(0.25, 0.45, 1.0), density=0.2, rings=(0, 0), ring_scale=1.2, ring_amp=0.05, noise_amp=0.05, rough=0.012):
    """Tray liquid. Glass for the eye, transparent for shadow rays so the lamp still reaches what is under the surface without caustic noise. Fixed ripple from a bump, so it never crawls."""
    m, nt, out = new_mat(name)
    L = nt.links.new
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value, g.inputs["Roughness"].default_value = 1.33, rough
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    L(lp.outputs["Is Shadow Ray"], mix.inputs[0])
    L(g.outputs[0], mix.inputs[1])
    L(tr.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-rings[0], -rings[1], 0)
    L(tc.outputs["Position"], mp.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type, w.rings_direction, w.wave_profile = "RINGS", "SPHERICAL", "SIN"
    w.inputs["Scale"].default_value, w.inputs["Distortion"].default_value = ring_scale, 1.5
    w.inputs["Detail"].default_value, w.inputs["Detail Scale"].default_value = 2, 0.6
    L(mp.outputs[0], w.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 0.16, 1
    L(tc.outputs["Position"], nz.inputs["Vector"])
    a = nt.nodes.new("ShaderNodeMath")
    a.operation = "MULTIPLY"
    L(w.outputs["Fac"], a.inputs[0])
    a.inputs[1].default_value = ring_amp
    b = nt.nodes.new("ShaderNodeMath")
    b.operation = "MULTIPLY"
    L(nz.outputs[0], b.inputs[0])
    b.inputs[1].default_value = noise_amp
    s = nt.nodes.new("ShaderNodeMath")
    L(a.outputs[0], s.inputs[0])
    L(b.outputs[0], s.inputs[1])
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value, bu.inputs["Distance"].default_value = 0.5, 0.5
    L(s.outputs[0], bu.inputs["Height"])
    L(bu.outputs[0], g.inputs["Normal"])
    if density:
        v = nt.nodes.new("ShaderNodeVolumeAbsorption")
        v.inputs["Color"].default_value = (*tint, 1)
        v.inputs["Density"].default_value = density
        L(v.outputs[0], out.inputs["Volume"])
    return m


def facing(cam, px, py, dist, w_px, h_px, m, name="tag", roll=0, res=(1920, 1080)):
    """A sheet that faces the lens at a given screen position and pixel size, so label text keeps its size and stays square to the viewer."""
    k = cam.data.sensor_width / cam.data.lens * dist / res[0]
    local = Vector(((px - res[0] / 2) * k, -(py - res[1] / 2) * k, -dist))
    bpy.context.view_layer.update()
    o = sheet(name, w_px * k, h_px * k, nx=8, ny=4, mat=m)
    o.location = cam.matrix_world @ local
    o.rotation_mode = "XYZ"
    o.rotation_euler = cam.matrix_world.to_euler()
    o.rotation_euler.rotate_axis("Z", math.radians(roll))
    return o
