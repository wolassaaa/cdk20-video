# HKBU SCIE1007 coursework science video. End card W5, test of a new background layer: drawn liver cells (many-sided, one or two round nuclei, small granules) on bone paper.
# Reads the motion from w5cells_sim.py (run that first) and draws each frame with EEVEE on the graphics card. Look: flat ink-line drawing with three flat tones and pen hatching on the shaded side, a soft shadow on the paper.
# Run: bash ../../gpu_slot.sh blender -b -t 4 --python bl_w5cells.py -- <first> <last> <step> <out dir> [scale]
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w5cells_sim as S

a = sys.argv[sys.argv.index("--") + 1:]
F0, F1, STEP, OUT = int(a[0]), int(a[1]), int(a[2]), a[3]
SCALE = float(a[4]) if len(a) > 4 else 1.0
N, M = 144, 14                                         # points round the rim, rings from centre to rim
z = np.load("C:/render_tmp/w5cells/sim.npz")
R, sim = z["R"], {k: z[k] for k in ("pos", "psi", "bulge", "cphi", "cdist")}


def lin(c):
    c = np.array(c, float) / 255
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)) + (1.0,)


BONE = (237, 235, 228)
PAL = {"n": dict(mid=(227, 223, 213), hi=(245, 243, 237), sh=(208, 204, 195)),
       "r": dict(mid=(229, 213, 204), hi=(245, 240, 234), sh=(214, 190, 181))}
NUC = dict(mid=(198, 205, 224), hi=(224, 229, 240), sh=(165, 176, 208))
LINE, NLINE, HATCH, GRAN, PSHADOW = (128, 127, 132), (104, 118, 176), (160, 158, 160), (188, 184, 176), (216, 213, 205)
LDIR = np.array([-0.55, 0.55, 0.63]); LDIR = LDIR / np.linalg.norm(LDIR)   # light from the upper left

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
try:
    sc.render.engine = "BLENDER_EEVEE"
except TypeError:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = int(1920 * SCALE), int(1080 * SCALE), 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.image_settings.compression = 15
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.film_transparent = False
sc.render.filter_size = 1.5
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1920; cam.location = (0, 0, 800); cam.data.clip_end = 2000
sc.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0; sun.data.angle = math.radians(14)
sun.rotation_mode = "QUATERNION"
import mathutils
sun.rotation_quaternion = mathutils.Vector(tuple(LDIR)).to_track_quat("Z", "Y")
sc.collection.objects.link(sun)


def emit(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs[0].default_value = lin(rgb); nt.links.new(e.outputs[0], o.inputs[0])
    return m


def toon(name, mid, hi, sh, hatch=None):
    """Three flat tones picked by how much the surface faces the light; pen hatching in the darkest tone."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"; dot.inputs[1].default_value = tuple(LDIR)
    L(geo.outputs["Normal"], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, lin(sh)
    cr.elements[1].position, cr.elements[1].color = 0.30, lin(sh)
    for pos, col in ((0.36, mid), (0.925, mid), (0.955, hi)):
        el = cr.elements.new(pos); el.color = lin(col)
    L(dot.outputs["Value"], ramp.inputs[0])
    col = ramp.outputs[0]
    if hatch:
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
        ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; L(sep.outputs[0], ad.inputs[0]); L(sep.outputs[1], ad.inputs[1])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "PINGPONG"; fr.inputs[1].default_value = 5.5; L(ad.outputs[0], fr.inputs[0])
        st = nt.nodes.new("ShaderNodeMapRange"); st.inputs[1].default_value = 3.0; st.inputs[2].default_value = 4.4; L(fr.outputs[0], st.inputs[0])
        dk = nt.nodes.new("ShaderNodeMapRange"); dk.inputs[1].default_value = 0.34; dk.inputs[2].default_value = 0.28; L(dot.outputs["Value"], dk.inputs[0])
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L(st.outputs[0], mu.inputs[0]); L(dk.outputs[0], mu.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["B"].default_value = lin(hatch)
        L(mu.outputs[0], mix.inputs["Factor"]); L(ramp.outputs[0], mix.inputs["A"])
        col = mix.outputs["Result"]
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    L(col, e.inputs[0]); L(e.outputs[0], o.inputs[0])
    return m


def paper():
    """Bone paper that only shows the cells' soft shadows; lit paper comes out as the exact bone colour."""
    m = bpy.data.materials.new("paper"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    d = nt.nodes.new("ShaderNodeBsdfDiffuse"); d.inputs[0].default_value = (1, 1, 1, 1)
    s = nt.nodes.new("ShaderNodeShaderToRGB"); L(d.outputs[0], s.inputs[0])
    lit = 3.0 * LDIR[2] / math.pi * float(os.environ.get("W5_LIT", "1.0"))
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = lit * 0.97; L(s.outputs[0], mr.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["A"].default_value = lin(PSHADOW); mix.inputs["B"].default_value = lin(BONE)
    L(mr.outputs[0], mix.inputs["Factor"])
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    L(mix.outputs["Result"], e.inputs[0]); L(e.outputs[0], o.inputs[0])
    return m


def new_obj(name, nv, faces, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(0, 0, 0)] * nv, [], faces)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def put(ob, co):
    ob.data.vertices.foreach_set("co", np.asarray(co, np.float32).ravel()); ob.data.update()


pl = new_obj("paper", 4, [(0, 1, 2, 3)], paper(), False)
put(pl, [(-1400, -900, 0), (1400, -900, 0), (1400, 900, 0), (-1400, 900, 0)])

TH = np.arange(N) * 2 * np.pi / N
RHO = 1 - (1 - np.arange(1, M + 1) / M) ** 1.8          # rings crowd towards the rim, where the surface turns over
dome_faces = [(0, 1 + j, 1 + (j + 1) % N) for j in range(N)] + [(1 + (m - 1) * N + j, 1 + m * N + j, 1 + m * N + (j + 1) % N, 1 + (m - 1) * N + (j + 1) % N) for m in range(1, M) for j in range(N)]
ring_faces = [(j, N + j, N + (j + 1) % N, (j + 1) % N) for j in range(N)]
NN, NM = 48, 8
nRHO = np.arange(1, NM + 1) / NM
ndome_faces = [(0, 1 + j, 1 + (j + 1) % NN) for j in range(NN)] + [(1 + (m - 1) * NN + j, 1 + m * NN + j, 1 + m * NN + (j + 1) % NN, 1 + (m - 1) * NN + (j + 1) % NN) for m in range(1, NM) for j in range(NN)]
nring_faces = [(j, NN + j, NN + (j + 1) % NN, (j + 1) % NN) for j in range(NN)]
nTH = np.arange(NN) * 2 * np.pi / NN
line_m, nline_m, gran_m, nuc_m = emit("line", LINE), emit("nline", NLINE), emit("gran", GRAN), toon("nuc", **NUC)
body_m = {k: toon("body_" + k, hatch=HATCH, **v) for k, v in PAL.items()}

cells = []
for i, c in enumerate(S.CAST):
    rng = np.random.default_rng(500 + i)
    d = dict(body=new_obj("body%d" % i, 1 + M * N, dome_faces, body_m[c[8]]), line=new_obj("line%d" % i, 2 * N, ring_faces, line_m, False))
    # the pen line is a little uneven round the rim, like a drawn line
    d["lw"] = 2.3 + 0.9 * np.sin(TH * 2 + rng.uniform(0, 6)) * np.sin(TH * 5 + rng.uniform(0, 6))
    k = c[9]
    base = rng.uniform(0, 6.28)
    d["nuc"] = [dict(rho=(0.10 if k == 1 else 0.30) + rng.uniform(0, 0.08), th=base + q * math.pi + rng.uniform(-0.3, 0.3), rn=R[i] * (0.25 if k == 1 else 0.21),
                     dome=new_obj("nuc%d_%d" % (i, q), 1 + NM * NN, ndome_faces, nuc_m), ring=new_obj("nl%d_%d" % (i, q), 2 * NN, nring_faces, nline_m, False),
                     dot=new_obj("no%d_%d" % (i, q), NN, [tuple(range(NN))], nline_m, False), dth=rng.uniform(0, 6.28)) for q in range(k)]
    ng = 46
    d["g"] = dict(rho=np.sqrt(rng.uniform(0.02, 0.62, ng)), th=rng.uniform(0, 6.28, ng), r=rng.uniform(1.6, 3.4, ng))
    d["gran"] = new_obj("gran%d" % i, ng * 6, [tuple(range(q * 6, q * 6 + 6)) for q in range(ng)], gran_m, False)
    cells.append(d)


def height(rho, Hc):
    return Hc * (1 - np.clip(rho, 0, 1) ** 3.2) ** 0.55


def build(f):
    for i, c in enumerate(S.CAST):
        d = cells[i]
        cx, cy = sim["pos"][f, i]
        psi = sim["psi"][f, i]
        rest = S.rest_planes(i)
        rad = lambda th: S.radius(np.atleast_1d(th), R[i], psi, sim["bulge"][f, i], rest, sim["cphi"][f, i], sim["cdist"][f, i])
        r = rad(TH)
        Hc = 0.20 * R[i]
        # local frame turned with the cell (so the hatching stays on it); screen y points down, world y up
        loc = lambda th, rr, zz: np.stack([rr * np.cos(th - psi), -rr * np.sin(th - psi), zz * np.ones_like(rr)], -1)
        for ob in [d["body"], d["line"], d["gran"]] + [x for nu in d["nuc"] for x in (nu["dome"], nu["ring"], nu["dot"])]:
            ob.location = (cx - 960, 540 - cy, 0); ob.rotation_euler = (0, 0, -psi)
        co = [np.array([[0, 0, Hc]])] + [loc(TH, rho * r, height(rho, Hc)) for rho in RHO]
        put(d["body"], np.concatenate(co))
        put(d["line"], np.concatenate([loc(TH, r - 1.5, 0.6), loc(TH, r + d["lw"], 0.6)]))
        g = d["g"]
        gth = g["th"] + psi
        gc = loc(gth, g["rho"] * rad(gth), height(g["rho"], Hc) + 0.8)
        hexa = np.stack([np.cos(np.arange(6) * math.pi / 3), np.sin(np.arange(6) * math.pi / 3), np.zeros(6)], 1)
        put(d["gran"], (gc[:, None, :] + hexa[None] * g["r"][:, None, None]).reshape(-1, 3))
        for nu in d["nuc"]:
            th0 = nu["th"] + psi
            c0 = loc(np.array([th0]), nu["rho"] * rad(th0), np.array([Hc + 1.0]))[0]
            rn = nu["rn"]
            nloc = lambda rr, zz: c0 + np.stack([rr * np.cos(nTH), rr * np.sin(nTH), zz * np.ones(NN)], 1)
            put(nu["dome"], np.concatenate([[c0 + (0, 0, 0.30 * rn)]] + [nloc(q * rn, 0.30 * rn * (1 - q ** 2.6) ** 0.6) for q in nRHO]))
            put(nu["ring"], np.concatenate([nloc(rn - 1.2, 0.3), nloc(rn + 1.6, 0.3)]))
            dc = c0 + (0.3 * rn * math.cos(nu["dth"]), 0.3 * rn * math.sin(nu["dth"]), 0.30 * rn + 1)
            put(nu["dot"], dc + np.stack([0.13 * rn * np.cos(nTH), 0.13 * rn * np.sin(nTH), np.zeros(NN)], 1))


os.makedirs(OUT, exist_ok=True)
import time
t0 = time.time()
for f in range(F0, F1 + 1, STEP):
    path = os.path.join(OUT, "c_%04d.png" % f)
    if os.path.exists(path):
        continue
    build(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
print("W5CELLS done %d frames in %.1f s" % (len(range(F0, F1 + 1, STEP)), time.time() - t0))
