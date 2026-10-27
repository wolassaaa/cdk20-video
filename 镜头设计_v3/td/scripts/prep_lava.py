# Lava-blood data: spheres along each vessel path with flow tangent + arc length (so the shader can stretch its
# texture along the flow), and the v4 liver mesh in the same TD frame as the vessel paths.
import numpy as np, sys, trimesh
OUT = sys.argv[1]
P = np.load(r"D:/。hkbu/molecular science/镜头设计_v3/assets/vessel_paths/real_paths.npy")
NP, NS = P.shape[:2]
pos, tan, arc = [], [], []
for i in range(NP):
    p = P[i, :, :3]; r = P[i, :, 3]
    s = np.linspace(0, NS - 1, NS * 10)
    pp = np.stack([np.interp(s, np.arange(NS), p[:, c]) for c in range(3)], 1)
    rr = np.interp(s, np.arange(NS), r) * (0.93 + 0.1 * np.sin(s * 0.3 + i) ** 8)
    t = np.gradient(pp, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pp, axis=0), axis=1))]
    pos.append(np.c_[pp, rr]); tan.append(t); arc.append(L)
pos, tan, arc = map(np.concatenate, (pos, tan, arc))
_, first = np.unique(np.round(pos[:, :3] / 0.07).astype(int), axis=0, return_index=True); k = np.sort(first)
pos, tan, arc = pos[k], tan[k], arc[k]
def tex(a, w=1024):
    n = len(a); rows = (n + w - 1) // w; o = np.zeros((rows * w, 4), np.float32); o[:n] = a; return o.reshape(rows, w, 4)
np.save(f"{OUT}/lava_pos.npy", tex(pos))
np.save(f"{OUT}/lava_flow.npy", tex(np.c_[tan, arc]))
np.save(f"{OUT}/lava_rad.npy", tex(np.c_[pos[:, 3], np.zeros((len(pos), 3))]))
print("spheres", len(pos))

src = r"D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
with open(src, "rb") as f: m = trimesh.load(f, file_type="stl")
c = m.bounds.mean(axis=0); sc = 100.0 / (m.bounds[1] - m.bounds[0]).max()
v = m.vertices
m.vertices = np.stack([(v[:, 0] - c[0]), (v[:, 2] - c[2]), -(v[:, 1] - c[1])], axis=1) * sc
m.fix_normals()
if len(m.faces) > 150000:
    try: m = m.simplify_quadric_decimation(face_count=150000)
    except Exception as e: print("no decimation", e)
trimesh.smoothing.filter_taubin(m, iterations=8)
m.export(f"{OUT}/liver_td.obj")
print("liver faces", len(m.faces), m.bounds)
