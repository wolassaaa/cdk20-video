"""HKBU SCIE1007 coursework science video. Arena direction: one Blender venue, six concept stills.

Run through the GPU queue:
bash ../../gpu_slot.sh D:/software/tools/blender.exe -b -t 4 -P scene.py -- --shot T4 [--pct 50 --samples 64]

The venue is the same in every shot and the scale never changes: 1 Angstrom = 1 m, so CDK20 stands about 70 m wide on a real arena floor.
Materials are neutral and the lights are pure red, green or blue, one channel per fader of a lighting desk (see DESK below). grade.py then maps each channel to the
two colours of that lighting section, so a re-light costs no GPU time. Output is <shot>.npy (linear, denoised) plus <shot>_mask.npy for the LED wall and <shot>.json for anchors.
"""
import argparse, json, math, os, sys, time
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.normpath(os.path.join(HERE, "..", ".."))
V3 = os.path.normpath(os.path.join(ART, "..", ".."))
S2 = os.path.join(V3, "styleframes", "S2plus")
WORK = os.path.normpath(os.path.join(HERE, "..", "_work"))
os.makedirs(WORK, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", required=True)
ap.add_argument("--samples", type=int, default=200)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--limit", type=float, default=140)   # seconds of sampling
ap.add_argument("--tag", default="")                  # variant name for the output files
ap.add_argument("--anim", default="")                 # "first,last": motion test frames of T4, 15 fps
ap.add_argument("--flat", action="store_true")        # homogeneous haze, cheaper
A = ap.parse_args(argv)

R, G, B = (1, 0, 0), (0, 1, 0), (0, 0, 1)   # desk faders: grade.py maps these to real colours per shot

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples = "GPU", A.samples
c_.use_adaptive_sampling, c_.adaptive_threshold = True, 0.02
c_.time_limit = A.limit
c_.use_denoising, c_.denoiser = True, "OPTIX"
c_.denoising_input_passes = "RGB_ALBEDO_NORMAL"
c_.max_bounces, c_.diffuse_bounces, c_.glossy_bounces, c_.transmission_bounces, c_.volume_bounces, c_.transparent_max_bounces = 4, 2, 2, 0, 0, 12
c_.caustics_reflective, c_.caustics_refractive = False, False
c_.sample_clamp_indirect = 20
c_.seed, c_.use_animated_seed = 3, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, A.pct
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth, st.exr_codec = "OPEN_EXR", "RGB", "32", "ZIP"
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
sc.world = w


# ---------- materials ----------
def mat(name, base=0.18, rough=0.5, spec=0.3, emit=None, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (base, base, base, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    if emit is not None:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


FLOOR = mat("floor", 0.035, 0.34, 0.5)


def floor_seams():
    """10 m panels: at this hall's scale one tile is 1 nm. A seam is a matte line, so it only shows where the floor reflects light."""
    nt = FLOOR.node_tree
    pr = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])

    def line(sock):
        dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 10.0
        nt.links.new(sock, dv.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(dv.outputs[0], fr.inputs[0])
        pp = nt.nodes.new("ShaderNodeMath"); pp.operation = "PINGPONG"; pp.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], pp.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.006
        nt.links.new(pp.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(line(sep.outputs["X"]), mx.inputs[0]); nt.links.new(line(sep.outputs["Y"]), mx.inputs[1])
    rg = nt.nodes.new("ShaderNodeMapRange")
    rg.inputs["To Min"].default_value, rg.inputs["To Max"].default_value = 0.34, 0.8
    nt.links.new(mx.outputs[0], rg.inputs["Value"])
    nt.links.new(rg.outputs[0], pr.inputs["Roughness"])
    ab = nt.nodes.new("ShaderNodeMapRange")
    ab.inputs["To Min"].default_value, ab.inputs["To Max"].default_value = 0.035, 0.0
    nt.links.new(mx.outputs[0], ab.inputs["Value"])
    cb = nt.nodes.new("ShaderNodeCombineColor")
    for k in range(3):
        nt.links.new(ab.outputs[0], cb.inputs[k])
    nt.links.new(cb.outputs[0], pr.inputs["Base Color"])


floor_seams()
SEAT = mat("seat", 0.10, 0.75, 0.2)
STEEL = mat("steel", 0.22, 0.5, 0.4)
ROOF = mat("roof", 0.03, 0.9, 0.1)
BLACK = mat("black", 0.0, 0.9, 0.0)
STONE = mat("stone", 0.50, 0.58, 0.32)


def link(ob):
    sc.collection.objects.link(ob)
    return ob


def mesh(name, V, F, material, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(V).tolist(), [], [tuple(int(i) for i in f) for f in F])
    me.materials.append(material)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.update()
    return link(bpy.data.objects.new(name, me))


class Bars:
    """Many thin boxes in one mesh: truss chords, lacing, cables, frames."""
    def __init__(self):
        self.V, self.F = [], []

    def bar(self, a, b, r):
        a, b = np.array(a, float), np.array(b, float)
        d = b - a
        L = np.linalg.norm(d)
        if L < 1e-6:
            return
        d /= L
        up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(d, up); u /= np.linalg.norm(u)
        v = np.cross(d, u)
        n = len(self.V)
        for p in (a, b):
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                self.V.append(p + u * sx * r + v * sy * r)
        for i in range(4):
            j = (i + 1) % 4
            self.F.append((n + i, n + j, n + 4 + j, n + 4 + i))
        self.F += [(n, n + 3, n + 2, n + 1), (n + 4, n + 5, n + 6, n + 7)]

    def truss(self, a, b, w=3.0, r=0.16, step=3.2):
        a, b = np.array(a, float), np.array(b, float)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        u = np.cross(d, (0, 0, 1.0)); u /= np.linalg.norm(u) + 1e-9
        v = np.cross(d, u)
        off = [(u + v) * w / 2, (u - v) * w / 2, (-u - v) * w / 2, (-u + v) * w / 2]
        for o in off:
            self.bar(a + o, b + o, r)
        n = max(int(L / step), 1)
        for k in range(n):
            p, q = a + d * L * k / n, a + d * L * (k + 1) / n
            for i in range(4):
                self.bar(p + off[i], q + off[(i + 1) % 4], r * 0.6)

    def build(self, name, material):
        return mesh(name, self.V, self.F, material)


BA, BB = 176, 160   # inner edge of the seating, metres


def bowl(z0=3.0):
    """Stepped seating with aisles, split into two tiers. Seen far off, the steps read as rows of seats."""
    V, F = [], []
    seg, every, gap = 540, 45, 3
    th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    keep = (np.arange(seg) % every) >= gap

    def tier(a0, b0, z, rows, tread, rise):
        rings = []
        for r in range(rows):
            a, b = a0 + r * tread, b0 + r * tread
            zr = z + r * rise
            rings += [(a, b, zr), (a, b, zr + rise), (a + tread, b + tread, zr + rise)]
        base = len(V)
        for a, b, zr in rings:
            V.extend(np.stack([a * np.cos(th), b * np.sin(th), np.full(seg, zr)], 1).tolist())
        for i in range(len(rings) - 1):
            for j in range(seg):
                if keep[j]:
                    k = (j + 1) % seg
                    F.append((base + i * seg + j, base + i * seg + k, base + (i + 1) * seg + k, base + (i + 1) * seg + j))

    tier(BA, BB, z0, 24, 1.45, 0.82)
    tier(BA + 46, BB + 46, z0 + 28, 18, 1.5, 1.05)
    mesh("seats", V, F, SEAT)
    # walkway ring between the two tiers and the back wall
    a0, b0 = BA + 24 * 1.45, BB + 24 * 1.45
    ring = []
    for a, b, z in ((a0, b0, z0 + 24 * 0.82), (BA + 46, BB + 46, z0 + 24 * 0.82), (BA + 46, BB + 46, z0 + 28), (BA + 73, BB + 73, z0 + 28 + 19), (BA + 73, BB + 73, 130)):
        ring.append(np.stack([a * np.cos(th), b * np.sin(th), np.full(seg, z)], 1))
    V2 = np.concatenate(ring)
    F2 = [(i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j) for i in range(4) for j in range(seg)]
    mesh("walk", V2, F2, ROOF)


def rig():
    """Roof steel: an oval ring, radial trusses, an inner ring. Returns fixture points on it."""
    t = Bars()
    a1, b1, a2, b2, z1, z2 = 150, 132, 50, 40, 92, 98
    n = 18
    pts = []
    for i in range(n):
        p, q = i / n * 2 * math.pi, (i + 1) / n * 2 * math.pi
        t.truss((a1 * math.cos(p), b1 * math.sin(p), z1), (a1 * math.cos(q), b1 * math.sin(q), z1))
        t.truss((a2 * math.cos(p), b2 * math.sin(p), z2), (a2 * math.cos(q), b2 * math.sin(q), z2))
        t.truss((a1 * math.cos(p), b1 * math.sin(p), z1), (a2 * math.cos(p), b2 * math.sin(p), z2))
        for f in np.linspace(0, 1, 7)[1:-1]:
            pts.append(((a1 * (1 - f) + a2 * f) * math.cos(p), (b1 * (1 - f) + b2 * f) * math.sin(p), z1 * (1 - f) + z2 * f - 2))
    t.build("rig", STEEL)
    return pts


def lamps(points, r=0.55, strength=60, ch=B):
    """Fixture heads on the rig. Small, bright, one fader: at this distance they are the stars of the roof."""
    V, F = [], []
    for p in points:
        n = len(V)
        for x, y, z in ((-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0), (-r, -r, -r), (r, -r, -r), (r, r, -r), (-r, r, -r)):
            V.append((p[0] + x, p[1] + y, p[2] + z))
        F += [(n, n + 1, n + 2, n + 3), (n + 4, n + 5, n + 6, n + 7), (n, n + 1, n + 5, n + 4), (n + 1, n + 2, n + 6, n + 5), (n + 2, n + 3, n + 7, n + 6), (n + 3, n, n + 4, n + 7)]
    mesh("lamps", V, F, mat("lamp", 0, 0.5, 0, ch, strength))


def venue(lamp=60):
    bpy.ops.mesh.primitive_plane_add(size=800, location=(0, 0, 0))
    bpy.context.object.data.materials.append(FLOOR)
    bpy.ops.mesh.primitive_plane_add(size=800, location=(0, 0, 118))
    bpy.context.object.data.materials.append(ROOF)
    bowl()
    pts = rig()
    if lamp:
        lamps(pts, strength=lamp)
    return pts


def haze(density=0.0035, floor_pool=2.2, height=24.0, aniso=0.45):
    """Thin haze through the room, a heavier layer on the floor. The noise is very low frequency: it is weather, it must not shimmer."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 60))
    ob = bpy.context.object
    ob.scale = (420, 420, 119.5)
    ob.name = "haze"
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, v = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeVolumeScatter")
    v.inputs["Color"].default_value = (1, 1, 1, 1)
    v.inputs["Anisotropy"].default_value = aniso
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    if A.flat:
        v.inputs["Density"].default_value = density * (1 + floor_pool * 0.25)
    else:
        tc = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Position"], sep.inputs[0])
        dz = nt.nodes.new("ShaderNodeMath"); dz.operation = "DIVIDE"; dz.inputs[1].default_value = height
        nt.links.new(sep.outputs["Z"], dz.inputs[0])
        ex = nt.nodes.new("ShaderNodeMath"); ex.operation = "POWER"; ex.inputs[0].default_value = 2.718
        neg = nt.nodes.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1
        nt.links.new(dz.outputs[0], neg.inputs[0]); nt.links.new(neg.outputs[0], ex.inputs[1])
        noi = nt.nodes.new("ShaderNodeTexNoise")
        noi.inputs["Scale"].default_value = 0.016; noi.inputs["Detail"].default_value = 3; noi.inputs["Roughness"].default_value = 0.5
        nt.links.new(tc.outputs["Position"], noi.inputs["Vector"])
        rmp = nt.nodes.new("ShaderNodeMapRange")
        rmp.inputs["From Min"].default_value, rmp.inputs["From Max"].default_value = 0.34, 0.66
        rmp.inputs["To Min"].default_value, rmp.inputs["To Max"].default_value = 0.45, 1.6
        nt.links.new(noi.outputs[0], rmp.inputs["Value"])
        add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = floor_pool; add.inputs[2].default_value = 1.0
        nt.links.new(ex.outputs[0], add.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        nt.links.new(add.outputs[0], mul.inputs[0]); nt.links.new(rmp.outputs[0], mul.inputs[1])
        mu2 = nt.nodes.new("ShaderNodeMath"); mu2.operation = "MULTIPLY"; mu2.inputs[1].default_value = density
        nt.links.new(mul.outputs[0], mu2.inputs[0])
        nt.links.new(mu2.outputs[0], v.inputs["Density"])
    ob.data.materials.append(m)
    return ob


def spot(pos, tgt, ch, power, deg, blend=0.12, r=0.25, name="spot"):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy, ld.color = power, ch
    ld.spot_size, ld.spot_blend, ld.shadow_soft_size = math.radians(deg), blend, r
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = pos
    ob.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return ob


def quiet(ob):
    ob.visible_volume_scatter = False
    return ob


def fan(pos, tgt, ch, power, n, spread, deg=1.6, axis=(1, 0, 0)):
    """One head cluster throwing n thin beams in a flat fan, as moving heads do."""
    p, t, ax = Vector(pos), Vector(tgt), Vector(axis)
    for i in range(n):
        f = (i / (n - 1) - 0.5) * 2 if n > 1 else 0
        spot(pos, t + ax * f * spread, ch, power, deg, 0.08)


SIL = [(-.10,0),(-.03,0),(-.015,.46),(.015,.46),(.03,0),(.10,0),(.115,.46),(.13,.80),(.165,.76),(.185,.80),(.205,1.14),(.185,1.34),(.155,1.42),(.075,1.455),(.05,1.50),
       (.085,1.56),(.09,1.64),(.055,1.72),(0,1.75),(-.055,1.72),(-.09,1.64),(-.085,1.56),(-.05,1.50),(-.075,1.455),(-.155,1.42),(-.185,1.34),(-.205,1.14),(-.185,.80),(-.165,.76),(-.13,.80),(-.115,.46)]


def person(x, y, h=1.75, yaw=0.0, z0=0.0):
    """A plain black figure for scale: a flat silhouette card, never lit, only ever seen against light. 1.75 tall in a room measured in Angstrom-metres."""
    k = h / 1.75
    c, s = math.cos(yaw), math.sin(yaw)
    V = [(x + c * dx * k, y + s * dx * k, z0 + dz * k) for dx, dz in SIL]
    return mesh("person", V, [tuple(range(len(V)))], BLACK)


def ruler(p, length, yaw=0.0, ticks=10, width=0.34):
    """The floor ruler, same object in every shot. Solid bar with end stops, flush with the floor. Its colour comes from the B fader."""
    m = mat("ruler", 0, 0.5, 0, B, 4)
    t = Bars()
    c, s = math.cos(yaw), math.sin(yaw)
    x0, y0 = p
    L = lambda f, o=0: (x0 + c * f * length - s * o, y0 + s * f * length + c * o, 0.05)
    t.bar(L(0), L(1), width)
    for k in range(ticks + 1):
        o = 1.8 * length / 10 if k in (0, ticks) else 0.9 * length / 10
        t.bar(L(k / ticks, -o), L(k / ticks, o), width * 0.8)
    t.build("ruler", m)


def camera(pos, tgt, lens, shift=(0, 0), level=False):
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width = lens, 36
    cd.clip_start, cd.clip_end = 0.1, 900
    cd.shift_x, cd.shift_y = shift
    ob = link(bpy.data.objects.new("cam", cd))
    ob.location = pos
    t = Vector(tgt)
    if level:   # horizontal axis, so a wall parallel to the sensor stays a true rectangle
        t.z = pos[2]
    ob.rotation_euler = (t - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = ob
    return ob


def project(ob_cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    v = world_to_camera_view(sc, ob_cam, Vector(p))
    return [v.x * 1920, (1 - v.y) * 1080]


def load_stl(path):
    raw = open(path, "rb").read()
    n = int.from_bytes(raw[80:84], "little")
    d = np.frombuffer(raw, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), count=n, offset=84)
    tri = d["v"].reshape(-1, 3)
    u, inv = np.unique(np.round(tri, 3), axis=0, return_inverse=True)
    return u, inv.reshape(-1, 3)


def relax(V, F, passes=3):
    for _ in range(passes):
        acc, cnt = np.zeros_like(V), np.zeros(len(V))
        for a, b in ((0, 1), (1, 2), (2, 0)):
            np.add.at(acc, F[:, a], V[F[:, b]]); np.add.at(cnt, F[:, a], 1)
            np.add.at(acc, F[:, b], V[F[:, a]]); np.add.at(cnt, F[:, b], 1)
        V = 0.5 * V + 0.5 * acc / np.maximum(cnt, 1)[:, None]
    return V


def cdk20(z_lift=2.0, spin=0.0):
    """The real AlphaFold surface, 1 Angstrom = 1 m. Solid stone where pLDDT >= 70. Below 70 it breaks into a dot screen: the model is less sure there, and predicted
    work in this film is always dotted. Model frame: x right, y up, z to the viewer of the M series; standing it up keeps that face to our camera."""
    D = np.load(os.path.join(S2, "_work", "cdk20_surface.npz"))
    v, q, conf = D["verts"].astype(float), D["quads"], D["conf"]
    W = np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)
    c, s = math.cos(spin), math.sin(spin)
    W = np.stack([c * W[:, 0] - s * W[:, 1], s * W[:, 0] + c * W[:, 1], W[:, 2]], 1)
    W[:, 2] += z_lift - W[:, 2].min()
    me = bpy.data.meshes.new("cdk20")
    me.from_pydata(W.tolist(), [], q.tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", conf.tolist())
    m = bpy.data.materials.new("cdk")
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
    pr.inputs["Roughness"].default_value = 0.55
    pr.inputs["Specular IOR Level"].default_value = 0.35
    at, geo = nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeNewGeometry")
    at.attribute_name, at.attribute_type = "conf", "GEOMETRY"
    sure = nt.nodes.new("ShaderNodeMath"); sure.operation = "GREATER_THAN"; sure.inputs[1].default_value = 0.70
    nt.links.new(at.outputs["Fac"], sure.inputs[0])
    tex = nt.nodes.new("ShaderNodeTexVoronoi")      # a regular dot lattice, fixed in the sculpture, so it never crawls
    tex.feature, tex.inputs["Scale"].default_value = "F1", 1 / 1.7
    tex.inputs["Randomness"].default_value = 0.0
    nt.links.new(geo.outputs["Position"], tex.inputs["Vector"])
    hole = nt.nodes.new("ShaderNodeMath"); hole.operation = "LESS_THAN"; hole.inputs[1].default_value = 0.34
    nt.links.new(tex.outputs["Distance"], hole.inputs[0])
    keep = nt.nodes.new("ShaderNodeMath"); keep.operation = "MAXIMUM"
    nt.links.new(sure.outputs[0], keep.inputs[0]); nt.links.new(hole.outputs[0], keep.inputs[1])
    # built up in lifts 1 m tall, like a very large print: one lift = 1 Angstrom, so the surface carries its own scale. Fixed in the sculpture, it cannot crawl.
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sepz.inputs[0])
    frc = nt.nodes.new("ShaderNodeMath"); frc.operation = "FRACT"
    nt.links.new(sepz.outputs["Z"], frc.inputs[0])
    tri = nt.nodes.new("ShaderNodeMath"); tri.operation = "PINGPONG"; tri.inputs[1].default_value = 0.5
    nt.links.new(frc.outputs[0], tri.inputs[0])
    gr = nt.nodes.new("ShaderNodeMapRange")
    gr.interpolation_type = "SMOOTHSTEP"
    gr.inputs["From Min"].default_value, gr.inputs["From Max"].default_value = 0.0, 0.05
    gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = 0.22, 1.0
    nt.links.new(tri.outputs[0], gr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMixRGB"); mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0
    mu.inputs[1].default_value = (0.36, 0.36, 0.36, 1)
    nt.links.new(gr.outputs[0], mu.inputs[2])
    nt.links.new(mu.outputs[0], pr.inputs["Base Color"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.8; bmp.inputs["Distance"].default_value = 0.2
    nt.links.new(gr.outputs[0], bmp.inputs["Height"])
    nt.links.new(bmp.outputs[0], pr.inputs["Normal"])
    mix, tr = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
    outn = nt.nodes["Material Output"]
    nt.links.new(keep.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(pr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outn.inputs["Surface"])
    me.materials.append(m)
    me.update()
    ob = link(bpy.data.objects.new("cdk20", me))
    return ob, W


def lifted_stone(name, base=0.36, pitch=1.0, axis=(0, 0, 1), low=0.22):
    """Sculpture stone built in lifts, the contour line every object in this hall shares."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.55
    pr.inputs["Specular IOR Level"].default_value = 0.35
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dt = nt.nodes.new("ShaderNodeVectorMath"); dt.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Position"], dt.inputs[0])
    dt.inputs[1].default_value = tuple(Vector(axis).normalized())
    dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = pitch
    nt.links.new(dt.outputs["Value"], dv.inputs[0])
    frc = nt.nodes.new("ShaderNodeMath"); frc.operation = "FRACT"
    nt.links.new(dv.outputs[0], frc.inputs[0])
    tri = nt.nodes.new("ShaderNodeMath"); tri.operation = "PINGPONG"; tri.inputs[1].default_value = 0.5
    nt.links.new(frc.outputs[0], tri.inputs[0])
    gr = nt.nodes.new("ShaderNodeMapRange")
    gr.interpolation_type = "SMOOTHSTEP"
    gr.inputs["From Min"].default_value, gr.inputs["From Max"].default_value = 0.0, 0.05 / pitch
    gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = low, 1.0
    nt.links.new(tri.outputs[0], gr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMixRGB"); mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0
    mu.inputs[1].default_value = (base, base, base, 1)
    nt.links.new(gr.outputs[0], mu.inputs[2])
    nt.links.new(mu.outputs[0], pr.inputs["Base Color"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.8; bmp.inputs["Distance"].default_value = 0.2
    nt.links.new(gr.outputs[0], bmp.inputs["Height"])
    nt.links.new(bmp.outputs[0], pr.inputs["Normal"])
    return m


META = {"shot": A.shot}
BEAMS = []


# ---------- shots ----------
def T1():
    """1-02. The real liver hung on cables over the number. The number lights it from below; one cold column lights it from above."""
    pts = venue(lamp=7)
    haze(0.0016, 0.6, 12)
    d = os.path.join(V3, "assets", "anatomy", "bp3d_v4_groups_stl")
    V, F = load_stl(os.path.join(d, "liver_parenchyma_segments.stl"))
    V = relax(V.astype(float), F, 6)
    lo, hi = V.min(0), V.max(0)
    print("liver bbox mm", lo, hi, hi - lo)
    width_mm = float((hi - lo).max())
    S = 92.0 / width_mm             # hung 92 m wide; the shape is real, the scale is printed on the floor
    mid = (lo + hi) / 2
    place = np.array([0, 10, 47.0])
    ST = lifted_stone("liverstone", 0.40, 1.4)
    W = (V - mid) * S + place
    mesh("liver", W, F, ST, True)
    for nm in ("portal_vein_hepatic", "hepatic_veins", "gallbladder"):
        vv, ff = load_stl(os.path.join(d, nm + ".stl"))
        vv = relax(vv.astype(float), ff, 2)
        mesh(nm, (vv - mid) * S + place, ff, ST, True)
    META["liver_scale_m_per_mm"] = S
    META["liver_width_mm"] = width_mm
    ten_cm = 100 * S
    rx, ry = -ten_cm / 2, 9
    ruler((rx, ry), ten_cm, 0, width=0.28)
    # cables
    t = Bars()
    for ang in (0.6, 2.5, 4.4):
        p = W[np.argmax(W[:, 2] + 22 * (np.cos(ang) * W[:, 0] + np.sin(ang) * (W[:, 1] - 8)) / 40)]
        t.bar(p, (p[0] * 1.15, p[1] * 1.15, 112), 0.07)
    t.build("cables", STEEL)
    # floor numeral: emission from the Remotion layer, B fader
    img = bpy.data.images.load(os.path.join(HERE, "..", "_work", "text", "T1floor.png"))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -22, 0.04))
    pl = bpy.context.object
    pl.scale = (100, 50, 1)
    m = bpy.data.materials.new("num")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o, e, tx, mx, tr = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
    tx.image = img
    e.inputs["Color"].default_value = (*B, 1)
    e.inputs["Strength"].default_value = 5.0
    nt.links.new(tx.outputs["Alpha"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs["Surface"])
    pl.data.materials.append(m)
    # what the number throws up at the liver: an area light lying on it, B fader
    ld = bpy.data.lights.new("up", "AREA")
    ld.shape, ld.size, ld.size_y = "RECTANGLE", 80, 40
    ld.energy, ld.color = 150000, B
    up = link(bpy.data.objects.new("up", ld))
    up.location = (0, -14, 1.0)
    up.rotation_euler = (math.radians(172), 0, 0)
    # cold top light: lands on the liver and stops there, R fader
    quiet(spot((-16, 16, 116), (-16, 16, 74), R, 4e6, 22, 0.7, 2.0))
    spot((-130, -40, 104), (-30, 4, 58), R, 7e6, 13, 0.9, 2.0)
    # thin edge beams crossing behind it, G fader, the same crimson as the numeral
    for x in (-150, -104, -60, 60, 104, 150):
        fan((x, 110, 92), (x * 0.62, -10, 0), G, 2.0e6, 3, 16, 1.4)
    person(-56, 12, 1.75); person(-52.5, 11.4, 1.75); person(55, 14, 1.75)
    cam = camera((0, -118, 62), (0, 0, 30.5), 18)
    META["ruler"] = [project(cam, (rx, ry, 0)), project(cam, (rx + ten_cm, ry, 0))]
    return cam


def wall(x0, x1, z0, z1, y, power, tex=None):
    """LED wall: an emissive panel on the B fader, spilling onto haze and floor. grade.py swaps its pixels for the real LED picture through the mask."""
    V = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    ob = mesh("wall", V, [(0, 1, 2, 3)], BLACK)
    m = bpy.data.materials.new("led")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o, e = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*B, 1)
    e.inputs["Strength"].default_value = power
    if tex:
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(tex)
        tx.image.colorspace_settings.name = "Non-Color"
        tc = nt.nodes.new("ShaderNodeTexCoord")
        uv = nt.nodes.new("ShaderNodeCombineXYZ")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        def rng(a, lo, hi):
            n = nt.nodes.new("ShaderNodeMapRange")
            n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
            nt.links.new(a, n.inputs["Value"])
            return n.outputs[0]
        nt.links.new(rng(sep.outputs["X"], x0, x1), uv.inputs[0]); nt.links.new(rng(sep.outputs["Z"], z0, z1), uv.inputs[1])
        nt.links.new(uv.outputs[0], tx.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = B
        nt.links.new(tx.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], e.inputs["Color"])
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    ob.data.materials[0] = m
    return ob


def T2():
    """2-02. The speaker on the venue's big screen: warm face, cold room."""
    pts = venue(lamp=0)
    lamps(pts, strength=26, ch=R)
    haze(0.0026, 2.8, 14)
    x0, x1, z0, z1, y = -86, 86, 5, 73, 78
    wall(x0, x1, z0, z1, y, 2.2, os.path.join(WORK, "T2wall.png") if os.path.exists(os.path.join(WORK, "T2wall.png")) else None)
    t = Bars()
    t.truss((x0 - 14, y - 2, z1 + 4), (x1 + 14, y - 2, z1 + 4), 4)
    for xx in (x0 - 6, x1 + 6):
        t.truss((xx, y, 0), (xx, y, z1 + 4), 3)
    t.build("frame", STEEL)
    # cold fans from the side rig, R and G faders, out to the sides of the wall so the screen stays clean
    for f in (-1, 1):
        fan((f * 150, 40, 92), (f * 110, -60, 0), R, 8e6, 5, 40, 1.4, axis=(0, 1, 0))
        fan((f * 124, 66, 94), (f * 100, -10, 0), G, 7e6, 5, 34, 1.4, axis=(0, 1, 0))
        spot((f * 112, 76, 3), (f * 80, -90, 1), R, 5e6, 14, 0.6, 1.5)
        spot((f * 150, 76, 3), (f * 150, -90, 1), R, 5e6, 14, 0.6, 1.5)
        spot((f * 100, 74, 2), (f * 118, 60, 90), G, 8e6, 40, 0.8, 2)
    for xx in (-110, -60, 60, 110):
        spot((xx, 40, 96), (xx * 0.9, -40, 0), G, 5e6, 2.0, 0.3)
    for x, yy in ((-30.2, -66), (-27.6, -66.6), (9, -74), (21, -58), (13.4, -60)):
        person(x, yy, 1.75)
    spot((-29, -66, 112), (-29, -66, 0), R, 5e6, 3.6, 0.6, 0.6)
    cam = camera((0, -130, 7), (0, 78, 7), 36, shift=(0, 0.135), level=True)
    META["wall"] = [project(cam, (x0, y, z1)), project(cam, (x1, y, z0))]
    return cam


def keyhole_prism(cx, cz, r, y0, y1):
    """A keyhole: circle over a flared stem. Schematic, the same flat shape from the camera."""
    pts = []
    n = 72
    a0 = math.radians(-62)
    for i in range(n + 1):
        a = a0 + (2 * math.pi - 2 * (math.radians(28))) * i / n
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    pts = [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))) for a in np.linspace(-58, 238, n)]
    pts += [(cx - r * 1.10, cz - r * 2.7), (cx + r * 1.10, cz - r * 2.7)]
    m = len(pts)
    V = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    F = [tuple(range(m))[::1], tuple(range(2 * m - 1, m - 1, -1))] + [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
    return mesh("kh", V, F, BLACK), pts


def T3():
    """3-08. House lights out. One follow spot crosses a black wall and finds nothing but a hole."""
    venue(lamp=0)
    haze(0.0034, 1.4, 26, 0.55)
    y, hx, hz, r = 60, 6.3, 34.6, 6.2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y + 8, 60))
    w_ = bpy.context.object
    w_.scale = (400, 16, 121)
    w_.data.materials.append(mat("wallblack", 0.05, 0.6, 0.3))
    kh, pts = keyhole_prism(hx, hz, r, y - 2, y + 30)
    bo = w_.modifiers.new("kh", "BOOLEAN")
    bo.operation, bo.object, bo.solver = "DIFFERENCE", kh, "EXACT"
    bpy.context.view_layer.objects.active = w_
    bpy.ops.object.modifier_apply(modifier="kh")
    kh.hide_render = True
    # dashed schematic ring: B fader, a row of lit dashes round the hole
    t = Bars()
    cent = np.array([hx, hz - r * 0.65])
    P = np.array(pts)
    closed = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    s_ = np.concatenate([[0], np.cumsum(seg)])
    L, dash, gap = s_[-1], 1.2, 1.1
    k = int(L / (dash + gap))
    pitch = L / k
    for i in range(k):
        a, b = i * pitch, i * pitch + dash
        pa = np.array([np.interp(a, s_, closed[:, 0]), np.interp(a, s_, closed[:, 1])])
        pb = np.array([np.interp(b, s_, closed[:, 0]), np.interp(b, s_, closed[:, 1])])
        off = lambda p: p + (p - cent) / np.linalg.norm(p - cent) * 0.8
        pa, pb = off(pa), off(pb)
        t.bar((pa[0], y - 0.15, pa[1]), (pb[0], y - 0.15, pb[1]), 0.09)
    t.build("dash", mat("dash", 0, 0.5, 0, B, 7))
    # the spot barely wider than the hole: nearly all its light goes in and does not come back
    spot((112, -60, 113), (hx - 1.5, y, hz - 4.0), R, 11e6, 7.2, 0.10, 0.15)
    cam = camera((0, -30, 17), (0, 60, 30), 34)
    META["hole"] = project(cam, (hx, y, hz - r * 0.6))
    return cam


def T4():
    """W2. House lights up. The real surface takes its first beam; we stand at its foot."""
    pts = venue(lamp=9)
    haze(0.0022, 3.4, 11)
    ob, W = cdk20(z_lift=0.6, spin=math.radians(4))
    pocket = np.array([9.57, -10.59, 22.7])
    # key: one big raking column from high left, nearly side-on, R fader. Half the mass stays in shadow.
    spot((-124, -66, 116), (-14, -8, 34), R, 40e6, 13, 0.5, 2.0)
    # pin into the cleft, the place the follow spot could not find in the blackout
    spot((18, -100, 6), tuple(pocket + np.array([0, -2, 0])), R, 4e6, 1.3, 0.4, 0.2)
    # thin edge on the far shoulder
    spot((190, 30, 84), (40, 0, 30), R, 2.6e6, 4.5, 0.4, 1.0)
    # low backlight across the floor haze behind the sculpture, G fader: the horizon it stands on
    for x in np.linspace(-150, 150, 9):
        spot((x, 96, 3.0), (x * 0.45, -30, 0.5), B, 0.55e6, 13, 0.6, 1.5)
    # one wide flood on the steel from the far floor, B fader: the roof must be seen for the room to have a size
    spot((0, 70, 2), (0, 40, 100), B, 1.5e6, 150, 0.8, 3)
    # thin beams from the rig behind it, G fader, uneven on purpose
    wid = (1.1, 2.2, 1.3, 3.0, 1.1, 1.8, 1.2)
    powr = (3.2e6, 6e6, 2.4e6, 8e6, 2.8e6, 5e6, 3e6)
    for i, (x, tx, ty) in enumerate(((-136, -96, -30), (-92, -70, 6), (-58, -46, 14), (-22, -44, 24), (30, 62, 20), (66, 70, 6), (108, 96, -20), (140, 128, 20),
                                     (-112, -130, 30), (84, 120, 44), (0, 6, 60), (-40, -70, 60))):
        BEAMS.append((spot((x, 44, 96), (tx, ty, 0), G, powr[i % 7], wid[i % 7], 0.15, 0.2), np.array([x, 44, 96.0]), np.array([tx, ty, 0.0])))
    person(-17, -30, 1.75, 0.0)
    person(-20.5, -30.6, 1.75, 0.0)
    person(24, -24, 1.75, 0.0)
    ruler((-14.5, -33.5), 10, 0.0, width=0.2)
    spot((-30, -70, 104), (-18, -32, 0), R, 2.4e6, 3.0, 0.5)
    cam = camera((-3, -68, 1.5), (5, 0, 29), 19)
    META["ruler"] = [project(cam, (-14.5, -33.5, 0)), project(cam, (-4.5, -33.5, 0))]
    META["pocket"] = project(cam, tuple(pocket + np.array([0, -8, 0])))
    return cam


def T5():
    """W4. The key in the lock on the stage, the number on the wall behind."""
    sys.path.insert(0, os.path.join(S2, "code"))
    import pocket048 as G5
    venue(lamp=26)
    haze(0.0026, 2.0, 18)
    S, f, lo, d, verts, quads, hidden, ppa, cx, cy = G5.build()
    del f, d
    origin = np.array([18.0, -48.0, 12.4])
    tw = lambda p: np.stack([p[..., 0] - cx, -p[..., 2], p[..., 1] - cy], -1) + origin   # our re-docking pose, unrotated, unmirrored: x right, y up, toward camera
    show = G5.show_mask(quads, hidden, len(verts))
    me = bpy.data.meshes.new("pocket")
    me.from_pydata(tw(verts).tolist(), [], quads.tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.attributes.new("show", "FLOAT", "POINT").data.foreach_set("value", show.tolist())
    m = lifted_stone("pocket", 0.075, 0.8, axis=(0.15, -0.72, 0.68), low=0.45)
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name, at.attribute_type = "show", "GEOMETRY"
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
    nt.links.new(at.outputs["Fac"], gt.inputs[0])
    mx, tr = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(pr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    me.materials.append(m)
    me.update()
    link(bpy.data.objects.new("pocket", me))
    # ligand, same ball-and-stick as render_048.py, bone white
    BONE = mat("bone", 0.92, 0.42, 0.3)
    L = tw(S["lig"])

    def sph(p, r):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=tuple(p), segments=32, ring_count=16)
        o = bpy.context.object
        o.data.materials.append(BONE)
        bpy.ops.object.shade_smooth()

    def cyl(a, b, r):
        a, b = Vector(a), Vector(b)
        dv = b - a
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=dv.length, location=(a + b) / 2, vertices=20)
        o = bpy.context.object
        o.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
        o.data.materials.append(BONE)
        bpy.ops.object.shade_smooth()

    for el, p in zip(S["el"], L):
        sph(p, G5.ATOM_R.get(el, 0.36))
    for i, j, order in S["bonds"]:
        a, b = Vector(L[i]), Vector(L[j])
        r = G5.STICK_R if order < 1.9 else 0.085
        offs = [Vector()] if order < 1.9 else [(b - a).cross(Vector((0, 1, 0))).normalized() * 0.1 * k for k in (-1, 1)]
        for off in offs:
            cyl(a + off, b + off, r)
    cut = G5.cut_z(S)
    for c in S["contacts"]:
        if c["rec"][2] >= cut or not c["partner"].startswith("Lys33"):
            continue
        rp, lp = Vector(tw(np.array(c["rec"]))), Vector(tw(np.array(c["lig"])))
        sph(rp, 0.24)
        for k in range(7):
            cyl(lp.lerp(rp, k / 7), lp.lerp(rp, (k + 0.5) / 7), 0.09)
    wx0, wx1, wz0, wz1, wy = -84, 84, 8, 74, 66
    wall(wx0, wx1, wz0, wz1, wy, 2.4, os.path.join(WORK, "T5wall.png") if os.path.exists(os.path.join(WORK, "T5wall.png")) else None)
    t = Bars()
    t.truss((wx0 - 14, wy - 2, wz1 + 4), (wx1 + 14, wy - 2, wz1 + 4), 4)
    for xx in (wx0 - 6, wx1 + 6):
        t.truss((xx, wy, 0), (xx, wy, wz1 + 4), 3)
    t.build("frame", STEEL)
    # white on the key and the pocket together, from high left, so the walls cast real shadows. No shaft: nothing may cross the number. R fader
    c0 = L.mean(0)
    quiet(spot((c0[0] - 44, -126, 86), tuple(c0 + np.array([0, 0, 1.0])), R, 9e6, 9.5, 0.5, 0.6))
    # teal rakes the pocket walls from the right, low, G fader
    quiet(spot((c0[0] + 74, c0[1] - 14, c0[2] + 8), tuple(c0), G, 3.2e6, 16, 0.5, 1.0))
    quiet(spot((c0[0] - 60, c0[1] - 20, c0[2] - 16), tuple(c0), G, 0.9e6, 14, 0.5, 1.0))
    # beams only in the margins and over the top of the wall, so the number stays clean
    for x, tx in ((-96, -92), (-101, -110), (96, 92), (101, 112)):
        spot((x, 58, 96), (tx, 30, 0), G, 7e6, 0.9, 0.2)
    spot((-150, 50, 86), (150, 50, 81), G, 16e6, 0.7, 0.2)
    spot((150, 46, 90), (-150, 46, 79), G, 12e6, 0.7, 0.2)
    # the near floor is out of frame, so the people stand further back, against the light of the wall on the floor
    person(-22, 8, 1.75)
    person(-25.4, 7.4, 1.75)
    ruler((-19, 5), 10, 0.0, width=0.1)
    quiet(spot((-20, 8, 104), (-20, 8, 0), G, 2.6e6, 5.0, 0.7, 0.6))
    cam = camera((0, -100, 12), (0, 66, 12), 31, shift=(0, 0.145), level=True)
    META["wall"] = [project(cam, (wx0, wy, wz1)), project(cam, (wx1, wy, wz0))]
    META["lig"] = project(cam, tuple(c0))
    return cam


def T6():
    """6-10. The road map laid into the arena floor. Lit to the door of station 4, dark after."""
    venue(lamp=0)
    haze(0.0028, 2.0, 16)
    P0, P1 = np.array([-170.0, -100.0]), np.array([145.0, 60.0])
    cam = camera((20, -125, 34), (30, 0, 16), 24)
    at = lambda t: P0 + (P1 - P0) * t
    tt_, xx_ = np.linspace(0, 1, 400), []
    for t in tt_:
        xx_.append(project(cam, (*at(t), 0))[0])
    ts = np.interp([165, 475, 785, 1085, 1370, 1640], xx_, tt_)
    door = np.interp(1085 - 44, xx_, tt_)
    d = (P1 - P0) / np.linalg.norm(P1 - P0)
    n = np.array([-d[1], d[0]])
    lit = Bars()
    lit.bar((*at(0.0), 0.08), (*at(door), 0.08), 0.7)
    lit.build("strip", mat("strip", 0, 0.5, 0, B, 26))
    faint = Bars()
    tt = door + 0.016
    while tt < 1.0:
        faint.bar((*at(tt), 0.06), (*at(min(tt + 0.0125, 1.0)), 0.06), 0.5)
        tt += 0.0245
    gatew, gateh = 8.0, 22.0
    glit = Bars()
    for i, t in enumerate(ts):
        c = at(t)
        a, b = c - n * gatew, c + n * gatew
        if i < 3:
            glit.bar((*a, 0), (*a, gateh), 0.34); glit.bar((*b, 0), (*b, gateh), 0.34); glit.bar((*a, gateh), (*b, gateh), 0.34)
            spot((c[0], c[1] - 10, 104), (c[0], c[1], 0), R, 16e6, 6.0, 0.35, 0.5)
            spot((c[0] - 26, c[1] + 22, 104), (c[0], c[1], 0), R, 3e6, 2.0, 0.2)
            spot((c[0] + 26, c[1] - 22, 104), (c[0], c[1], 0), G, 3e6, 2.0, 0.2)
        else:
            def dashes(p, q, k=7):
                for u in range(k):
                    faint.bar(p + (q - p) * (u / k), p + (q - p) * ((u + 0.55) / k), 0.22)
            A3, B3 = np.array([*a, 0.0]), np.array([*b, 0.0])
            dashes(A3, A3 + (0, 0, gateh)); dashes(B3, B3 + (0, 0, gateh)); dashes(A3 + (0, 0, gateh), B3 + (0, 0, gateh), 10)
    glit.build("gates", mat("gate", 0, 0.5, 0, B, 18))
    faint.build("dashed", mat("dashed", 0, 0.5, 0, B, 1.3))
    # 048: one point of light on the line, on the threshold of station 4
    c = at(door)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.9, location=(c[0], c[1], 1.9), segments=32, ring_count=16)
    bpy.context.object.data.materials.append(mat("048", 0, 0.5, 0, R, 40))
    spot((c[0] - 8, c[1] - 24, 106), (c[0], c[1], 0), R, 5.5e6, 2.6, 0.2)
    person(c[0] - 2.2, c[1] - 7.5, 1.75)
    for x, yy in ((at(ts[1])[0] + 11, at(ts[1])[1] - 7), (at(ts[2])[0] - 10, at(ts[2])[1] + 8), (at(ts[2])[0] - 13, at(ts[2])[1] + 7.2)):
        person(x, yy, 1.75)
    META["stops"] = [project(cam, (*at(t), 0)) for t in ts]
    META["stops_top"] = [project(cam, (*at(t), gateh)) for t in ts]
    META["door"] = project(cam, (*at(door), 0))
    return cam


cam = {"T1": T1, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "T6": T6}[A.shot]()
tag = A.shot + A.tag
json.dump(META, open(os.path.join(WORK, tag + ".json"), "w"))


def to_npy(exr, npy):
    im = bpy.data.images.load(exr)
    iw, ih = im.size
    a = np.empty(iw * ih * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(ih, iw, 4)[::-1, :, :3].copy()
    np.save(npy, a.astype(np.float32))
    bpy.data.images.remove(im)


if A.anim:
    # slow by construction: each beam drifts along its own sine, once in about 12 s, the camera creeps 3 m. Fixed seed, fixed samples, no time limit, so frames match.
    first, last = (int(v) for v in A.anim.split(","))
    c_.use_adaptive_sampling, c_.time_limit = False, 0
    mdir = os.path.join(WORK, "motion")
    os.makedirs(mdir, exist_ok=True)
    start = Vector(cam.location)
    for f in range(first, last + 1):
        t0 = time.time()
        u = f / 15.0
        for i, (ob, pos, tgt) in enumerate(BEAMS):
            ph = 1.7 * i
            d = np.array([26 * math.sin(2 * math.pi * u / 12 + ph), 16 * math.cos(2 * math.pi * u / 15 + 0.6 * ph), 0])
            ob.rotation_euler = Vector(tgt + d - pos).to_track_quat("-Z", "Y").to_euler()
        cam.location = start + Vector((0.12, 0.5, 0.0)) * u
        exr = os.path.join(mdir, f"f{f:04d}.exr")
        sc.render.filepath = exr
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(exr)
        iw, ih = im.size
        a = np.empty(iw * ih * 4, np.float32)
        im.pixels.foreach_get(a)
        np.save(os.path.join(mdir, f"f{f:04d}.npy"), a.reshape(ih, iw, 4)[::-1, :, :3].astype(np.float16))
        bpy.data.images.remove(im)
        os.remove(exr)
        print(f"FRAME {f} {time.time() - t0:.1f}s", flush=True)
    print("DONE anim")
    sys.exit(0)

t = time.time()
exr = os.path.join(WORK, tag + ".exr")
sc.render.filepath = exr
bpy.ops.render.render(write_still=True)
to_npy(exr, os.path.join(WORK, tag + ".npy"))
print(f"RENDER {tag} {time.time() - t:.1f}s")
if os.path.exists(exr):
    os.remove(exr)

if "wall" in bpy.data.objects:
    # visibility mask for the LED wall: everything else goes black, no haze, no lights, a few samples
    for ob in list(sc.objects):
        if ob.type == "LIGHT" or ob.name == "haze":
            ob.hide_render = True
    em = bpy.data.materials.new("white")
    em.use_nodes = True
    nt = em.node_tree
    nt.nodes.clear()
    o_, e_ = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    e_.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(e_.outputs[0], o_.inputs["Surface"])
    blk = mat("hold", 0, 1, 0)
    for ob in sc.objects:
        if ob.type == "MESH":
            ob.data.materials.clear() if False else None
            for i in range(len(ob.material_slots)):
                ob.material_slots[i].material = em if ob.name == "wall" else (ob.material_slots[i].material if ob.name == "pocket" else blk)
    if "pocket" in bpy.data.objects:   # the pocket keeps its transparent holes but must read black where it is solid
        pm = bpy.data.objects["pocket"].material_slots[0].material
        pmp = pm.node_tree.nodes["Principled BSDF"]
        for lk in list(pmp.inputs["Base Color"].links):
            pm.node_tree.links.remove(lk)
        pmp.inputs["Base Color"].default_value = (0, 0, 0, 1)
        pm.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0
    c_.samples, c_.use_denoising, c_.time_limit = 32, False, 0
    c_.use_adaptive_sampling = False
    exr = os.path.join(WORK, tag + "_mask.exr")
    sc.render.filepath = exr
    bpy.ops.render.render(write_still=True)
    to_npy(exr, os.path.join(WORK, tag + "_mask.npy"))
    if os.path.exists(exr):
        os.remove(exr)
print("DONE", tag)
