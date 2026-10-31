"""HKBU SCIE1007 coursework science video. Lantern T1 (1-02): the real liver (BodyParts3D) found by one small hand lamp, the figure cut through the wall. Heavy, mostly dark. The whole front of the organ is lit, so the outline closes and it reads as a liver at once. Right lobe on frame left."""
import struct

from lk import *

D_ = kit.ROOT / "assets/anatomy/bp3d_v4_groups_stl"


def sample(name, K, rng):
    """Dense points and smooth normals from one STL, so the real organ can go through kit.view."""
    b = open(D_ / name, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    tri = np.frombuffer(b[84:], np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), n)["v"].reshape(-1, 3).astype(np.float64)
    key, inv = np.unique(np.round(tri, 2), axis=0, return_inverse=True)
    faces = inv.reshape(-1, 3)
    v = key.astype(np.float32)
    fn = np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]])
    nv = np.zeros_like(v)
    for i in range(3):
        np.add.at(nv, faces[:, i], fn)
    nv /= np.maximum(np.linalg.norm(nv, axis=1, keepdims=True), 1e-6)
    bc = rng.dirichlet((1, 1, 1), (len(faces), K)).astype(np.float32)
    pts = (v[faces][:, None, :, :] * bc[..., None]).sum(2).reshape(-1, 3)
    nrm = (nv[faces][:, None, :, :] * bc[..., None]).sum(2).reshape(-1, 3)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    cen = (v.min(0) + v.max(0)) / 2
    if np.mean(np.sum((pts - cen) * nrm, 1)) < 0:
        nrm = -nrm
    return pts, nrm


rng = np.random.default_rng(1)
pl, nl = sample("liver_parenchyma_segments.stl", 9, rng)
pg, ng = sample("gallbladder.stl", 60, rng)
cen = (pl.min(0) + pl.max(0)) / 2
# front view: the patient's right lobe sits on the left of the frame, as in any anatomy plate
Rl = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], np.float32)
CX, CY, SC = 1312, 448, 4.7
PX, PY = 690.0, 1030.0
fig, (lx, ly) = walker(PX, PY, 2.0, reach=(1.0, 1.0))
dirL = np.array((-0.58, -0.40, 0.71))


def shaded(p, n_):
    kit._S = dict(v=p - cen, n=n_, c=np.ones(len(p), np.float32), cen=cen)
    V_ = view(Rl, scale=SC, cx=CX, cy=CY, w=W, h=H, ss=0.4, L=dirL)
    return V_


V = shaded(pl, nl)
Vg = shaded(pg, ng)
m = smooth(fft_blur(V["mask"], 2.0), 0.40, 0.60)
mg = smooth(fft_blur(Vg["mask"] * ((Vg["z"] > V["z"]) | (V["mask"] < 0.5)), 2.0), 0.40, 0.60)  # the gallbladder sits under the edge: only what is really in front shows
ws = fft_blur(m, 14) + 1e-3
ns = np.stack([fft_blur(V["normal"][..., i] * m, 14) / ws for i in range(3)], -1)
ns /= np.maximum(np.linalg.norm(ns, axis=2, keepdims=True), 1e-5)
t = np.clip(ns @ (dirL / np.linalg.norm(dirL)).astype(np.float32), 0, 1)
st = 0.20 + (t > 0.36) * 0.28 + (t > 0.60) * 0.26 + (t > 0.84) * 0.26
st = fft_blur(st.astype(np.float32), 0.9)
A_ = np.asarray(AMBER)
mi = A_ * np.array((0.56, 0.42, 0.30))
u = st[..., None]
col = np.where(u < 0.5, BLACK + (mi - BLACK) * u * 2, mi + (A_ - mi) * (u - 0.5) * 2)

c = blank()
ang = np.arctan2(yy - ly, xx - lx)
ax = np.radians(-47.0)
da = np.abs(np.angle(np.exp(1j * (ang - ax))))
cone = fft_blur((da < np.radians(37.0)).astype(np.float32), 0.8)
c = add(c, cone * (1 - m) * (yy < PY) * 0.075, AMBER)
c = c * (1 - m[..., None]) + col * m[..., None]
# gallbladder: its own black outline, so the small sac under the edge reads as a separate thing
c = lay(c, np.clip(fft_blur(mg, 2.6) * 2.4, 0, 1) * (1 - mg), BLACK)
c = lay(c, mg, A_ * 0.78)
c = lay(c, fig, AMBER)
c = add(c, (np.hypot(xx - lx, yy - ly) < 7).astype(np.float32), AMBER_HI)

big = stencil("1,412", 214, 900, 70, 520)
c = add(c, extrude(big, 58, 36, step=3) * (1 - big) * (1 - cone) * 0.15, AMBER)
c = lay(c, big, AMBER_HI * 0.45 + AMBER * 0.55)
c = lay(c, tx("deaths in", 62, 700, 76, 636), AMBER_HI)
c = lay(c, tx("Hong Kong, 2022", 62, 700, 76, 716), AMBER_HI)
save(c, "T1.png")
