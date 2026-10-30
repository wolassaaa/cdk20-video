"""Extra still (beat 1-10): the AlphaFold CDK20 model as a radiance field, where per-residue confidence (pLDDT) IS coherence.
Confident residues are dense, fine, bone-white gaussians; the low-confidence C-terminal tail loses coherence and drifts off
into blue, the same way the four lives do in the test. Red marks the kinase G-loop / HRD / DFG motifs found by sequence.

blender -b --factory-startup -t 3 -P extra_protein.py -- --out OUT.png [--pct 100] [--samples 32]
"""
import bpy, sys, os, math, argparse
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import splatlib as sl

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--pct", type=int, default=100); ap.add_argument("--samples", type=int, default=32)
A = ap.parse_args(argv)
PDB = "D:/。hkbu/molecular science/镜头设计_v3/assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
rng = np.random.default_rng(346)

BONE = np.array([0.846, 0.831, 0.776]); RED = np.array([0.807, 0.0097, 0.0048]); BLUE = np.array([0.0137, 0.0423, 1.0]); KLEIN = np.array([0.0, 0.0284, 0.386])

# ------------------------------------------------------------------ parse
xyz, res, name, bf = [], [], [], []
for l in open(PDB):
    if l.startswith("ATOM"):
        xyz.append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
        res.append(int(l[22:26])); name.append(l[12:16].strip()); bf.append(float(l[60:66]))
xyz = np.array(xyz); res = np.array(res); bf = np.array(bf) / 100; name = np.array(name)
nres = res.max()
ca = np.zeros((nres + 1, 3)); plddt = np.zeros(nres + 1)
for r in range(1, nres + 1):
    m = (res == r) & (name == "CA")
    ca[r] = xyz[m][0]; plddt[r] = bf[m][0]

# ------------------------------------------------------------------ pose: kinase domain centred, tail thrown to screen left and up
cen = ca[1:291].mean(0)
tail = ca[305:347].mean(0) - cen
d = tail / np.linalg.norm(tail)
aim = np.array([-0.86, 0.10, 0.50]); aim /= np.linalg.norm(aim)
v = np.cross(d, aim); c = d @ aim
vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
Rm = np.eye(3) + vx + vx @ vx / (1 + c)
# a further spin about the aim axis to show the fold
ang = math.radians(35); ax = aim
K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
Rs = np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
Rm = Rs @ Rm
S = 1 / 27.0  # units per angstrom
P = ((xyz - cen) @ Rm.T) * S
CA = ((ca - cen) @ Rm.T) * S

# ------------------------------------------------------------------ coherence from confidence
conf = np.clip((plddt - 0.50) / 0.40, 0, 1)
pocket = np.zeros(nres + 1, bool)
for a, b in ((11, 16), (125, 127), (145, 147)): pocket[a:b + 1] = True


def tangent(i):
    a = max(1, i - 1); b = min(nres, i + 1)
    t = CA[b] - CA[a]; return t / (np.linalg.norm(t) + 1e-9)


T_res = np.array([np.zeros(3)] + [tangent(i) for i in range(1, nres + 1)])
pos, sz, col, al, nrm = [], [], [], [], []
Rots = []


def frame(tan):
    t = tan / (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9)
    a = np.cross(t, [0.3, 0.5, 0.8]); a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-9
    b = np.cross(t, a)
    return np.stack([t, a, b], 2)


def drift_field(p):
    return np.stack([np.sin(p[:, 2] * 2.1 + 0.3) + 0.5 * np.sin(p[:, 1] * 3.7), np.sin(p[:, 0] * 1.7 + 1.1), np.sin(p[:, 0] * 2.3 + 2.0) + 0.5 * np.sin(p[:, 1] * 2.9)], 1)


# atoms: 8 gaussians each (density), loosening with low confidence
rep = 8
A_i = np.repeat(np.arange(len(P)), rep)
ri = res[A_i]; cc = conf[ri]
loose = (1 - cc) ** 1.5
p = P[A_i] + rng.normal(size=(len(A_i), 3)) * (0.010 + 0.20 * loose)[:, None]
p += drift_field(p * 1.6) * (0.26 * loose)[:, None] + np.array([-0.26, 0, 0.20])[None] * (loose * rng.random(len(A_i)))[:, None]
tan = T_res[ri] + rng.normal(size=(len(A_i), 3)) * (0.3 + 3.0 * loose)[:, None]
Rots.append(frame(tan))
h = (0.026 + 0.075 * loose) * np.exp(rng.normal(0, 0.18, len(A_i)))
sz.append(np.stack([h * (1.25 - 0.25 * loose), h, h * (0.9 + 0.1 * loose)], 1)); pos.append(p)
c_ = BONE[None] * (0.50 + 0.30 * cc)[:, None]
blue = sl_mix = np.clip(1 - cc * 1.5, 0, 1)[:, None]
c_ = c_ * (1 - blue) + (BLUE * 0.6 * (1 - loose[:, None]) + KLEIN * 1.1 * loose[:, None]) * blue
pk = pocket[ri][:, None]
c_ = np.where(pk, RED[None] * 0.95, c_)
col.append(c_); al.append(0.085 * (0.25 + 0.75 * cc) * (1 - 0.55 * loose)); nrm.append(rng.normal(size=(len(A_i), 3)))

# backbone thread: fine anisotropic strokes along the chain (a Catmull-Rom through the CA)
per = 70
for i in range(1, nres):
    a, b = CA[max(1, i - 1)], CA[i]
    c2, d2 = CA[i + 1], CA[min(nres, i + 2)]
    t = np.linspace(0, 1, per, endpoint=False)[:, None]
    q = 0.5 * ((2 * b) + (c2 - a) * t + (2 * a - 5 * b + 4 * c2 - d2) * t ** 2 + (-a + 3 * b - 3 * c2 + d2) * t ** 3)
    tn = c2 - b
    c0 = conf[i]; lo = (1 - c0) ** 1.5
    pk0 = pocket[i]
    q = q + rng.normal(size=(per, 3)) * (0.005 + 0.18 * lo)
    q += drift_field(q * 1.6) * 0.28 * lo + np.array([-0.28, 0, 0.22])[None] * (lo * rng.random((per, 1)))
    Rots.append(frame(np.tile(tn, (per, 1)) + rng.normal(size=(per, 3)) * (0.025 + 0.6 * lo) * np.linalg.norm(tn)))
    hh = (0.0125 + 0.05 * lo) * np.exp(rng.normal(0, 0.15, per))
    sz.append(np.stack([hh * (3.2 - 2.0 * lo), hh * (0.7 + 0.3 * lo), hh * (0.7 + 0.3 * lo)], 1)); pos.append(q)
    base = RED * 1.0 if pk0 else (BONE * (0.95 + 0.4 * c0) if c0 > 0.45 else BLUE * 0.8 * (1 - lo) + KLEIN * 1.4 * lo)
    col.append(np.tile(base, (per, 1))); al.append(np.full(per, 0.30 * (0.25 + 0.75 * c0) * (1 - 0.6 * lo))); nrm.append(rng.normal(size=(per, 3)))

pos = np.concatenate(pos); sz = np.concatenate(sz); col = np.concatenate(col); al = np.concatenate(al); nrm = np.concatenate(nrm)
Rots = np.concatenate(Rots)
nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
N = len(pos); print("splats", N)
# place the fold right of frame centre, depth cue: the back recedes (fixed camera, so this can be baked)
OFF = np.array([0.72, 0.0, -0.16])
pos = pos + OFF
depth = (pos[:, 1] - pos[:, 1].min()) / (pos[:, 1].max() - pos[:, 1].min())
col = col * (1.0 - 0.72 * depth)[:, None]

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
mat = sl.splat_material()
ob = sl.splat_object("protein", N, mat)
zero = np.zeros(N, np.float32)
sl.set_attrs(ob, pos, sl.euler_from_mats(Rots), sz, col, nrm, al, zero, zero, np.ones(N, np.float32), zero)
camd = bpy.data.cameras.new("c"); camd.lens = 50; camd.sensor_width = 36; camd.sensor_fit = "HORIZONTAL"
cam = bpy.data.objects.new("c", camd); scn.collection.objects.link(cam); scn.camera = cam
pos_c = Vector((0.0, -6.0, 0.25)); cam.location = pos_c
cam.rotation_euler = (Vector((0, 0, 0.0)) - pos_c).to_track_quat("-Z", "Y").to_euler()
sl.cycles_setup(samples=A.samples, pct=A.pct, tbounces=256)
scn.render.filepath = A.out
bpy.ops.render.render(write_still=True)
print("DONE", A.out)
