"""HKBU SCIE1007 coursework science video. Eclipse direction, T1: the real liver (BodyParts3D) stands on the horizon as a mountain, the sun behind it has just lost its first bite, and the ground holds exactly 1,412 small figures."""
import struct

from ec import *

y, x = grid()

# real liver mesh, same front view as the dawn direction: fed through the shared projector
STL = ART.parent.parent / "assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
cache = WORK / "t1_view.npz"
SC, CX, CY = 4.9, 790, 410
if cache.exists():
    V = dict(np.load(cache))
else:
    b = open(STL, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    tri = np.frombuffer(b[84:], np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), n)["v"].reshape(-1, 3).astype(np.float64)
    key, inv = np.unique(np.round(tri, 3), axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    c = (key.max(0) + key.min(0)) / 2
    # BodyParts3D frame: patient's right is -x, front is -y, up is +z. A front view keeps x, so the big right lobe lands on the left of the frame, as in _alignment_check_anterior.png
    p = key - c
    v = np.stack([p[:, 0], p[:, 2], -p[:, 1]], 1).astype(np.float32)     # screen right, up, toward camera
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    nn = np.zeros_like(v)
    for i in range(3):
        np.add.at(nn, f[:, i], fn)
    nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
    if np.mean(np.sum(v * nn, 1)) < 0:
        nn = -nn
    # the mesh is too coarse for a point splat at this size, so scatter points across every triangle
    rng0 = np.random.default_rng(0)
    w = rng0.dirichlet((1, 1, 1), (len(f), 6)).astype(np.float32)        # tris x 6 x 3
    pts = (v[f][:, None, :, :] * w[..., None]).sum(2).reshape(-1, 3)
    nrm = (nn[f][:, None, :, :] * w[..., None]).sum(2).reshape(-1, 3)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    kit._S = dict(v=np.vstack([v, pts]), n=np.vstack([nn, nrm]), c=np.ones(len(v) + len(pts), np.float32), cen=np.zeros(3))
    V = kit.view(R=np.eye(3), scale=SC, cx=CX, cy=CY, w=W, h=H, ss=0.5)
    np.savez(cache, **{k: a for k, a in V.items() if isinstance(a, np.ndarray)})
hard = sstep(0.4, 0.6, blur(V["mask"], 3))

# sun behind and above, first bite taken by the real CDK20 outline
OC = np.load(WORK / "t6_mask.npy")
SX, SY, R = 1400, 300, 226
r = np.hypot(x - SX, y - SY)
disc = sstep(R + 1.2, R - 1.2, r)
k = 0.62 * R / 112
bite = sample(OC, (x - SX - R * 2.02) / k + 480, (y - SY + R * 0.42) / k + 480)
sun = disc * (1 - bite)

# sky: the strange flat light before an eclipse, one haze, nothing but the ramp
sky = 0.33 + 0.12 * np.exp(-r / 520) + 0.05 * np.exp(-r / 260) - 0.12 * sstep(600, 0, y) * 0.5
sky = sky + 0.03 * (blur(noise(71, 600, slope=3), 30) - 0.5)
t = sky * (1 - disc) + bite * disc * 0.03 + sun * 1.0
sg = np.clip(blur(sun, 10) * 0.5 + blur(sun, 40) * 0.6, 0, 1) * (1 - disc)
t = np.clip(t + sg * 0.34, 0, 1)
ai = np.clip(sun + sg * 1.5, 0, 1)      # the sun is pearl: the only cold thing in this frame

# ground, a long dark plain
hz = 700
g = sstep(hz - 1, hz + 1, y)
t = t * (1 - g) + g * (0.20 - 0.18 * sstep(hz, 985, y))
ai = ai * (1 - g)

# liver: dark red mass, back-lit edge toward the sun, relief just visible
n3 = V["normal"]
dx, dy = (SX - x) / np.maximum(r, 1), -(SY - y) / np.maximum(r, 1)
toward = np.clip(n3[..., 0] * dx + n3[..., 1] * dy, 0, 1)
fres = (1 - np.clip(n3[..., 2], 0, 1)) ** 2.4
wt = blur(hard, 9) + 1e-3
body = blur(np.clip(0.7 * V["key"] + 0.3, 0, 1) * hard, 9) / wt       # the mesh has gaps between segments, so the relief is read soft and the specks go
near = 1 - sstep(0.62, 0.92, blur(hard, 22))                             # only the true outline takes the back light
surf = 0.03 + 0.07 * body + 0.30 * fres * toward * near
hard = hard * (1 - g)     # the liver stands behind the horizon
t = t * (1 - hard) + surf * hard
ai = ai * (1 - hard)

# exactly 1,412 figures on the plain, far rows smaller. Nothing else on the ground
rng = np.random.default_rng(1412)
N = 1412
u = rng.random(N) ** 2.1
py = hz + 5 + u * 232
sz = 4.5 + 19 * u
px = rng.uniform(-10, W + 10, N)
order = np.argsort(py)
cov = np.zeros((H, W), np.float32)
stamps = {}
for i in order:
    s = int(round(sz[i]))
    if s not in stamps:
        m_ = int(s * 1.5) | 1
        yy, xx = np.mgrid[0:s + 3, 0:m_].astype(np.float32)
        stamps[s] = person(xx, yy, m_ / 2, s + 1.5, s)
    a = stamps[s]
    x0, y0 = int(px[i] - a.shape[1] / 2), int(py[i] - a.shape[0])
    x1, y1 = min(x0 + a.shape[1], W), min(y0 + a.shape[0], H)
    ax, ay = max(x0, 0), max(y0, 0)
    if x1 <= ax or y1 <= ay:
        continue
    reg = cov[ay:y1, ax:x1]
    np.maximum(reg, a[ay - y0:y1 - y0, ax - x0:x1 - x0], out=reg)
t = put(t, cov, 0.70)
t = np.clip(t + blur(cov, 6) * 0.22 * g, 0, 1)
ai = ai * (1 - cov)

t = put(t, text("1,412 deaths in Hong Kong, 2022", 66, (960, 1010), 700, "mm"), 0.84)
save(t, "T1.png", ai)
