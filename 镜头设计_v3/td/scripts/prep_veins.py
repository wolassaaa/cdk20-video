# 2D field for the "glowing cracks in rock" look: the real vessel tree projected onto the front view becomes the main
# crack network. Per pixel: distance to the nearest vessel centreline, that vessel's radius, its arc length from the
# root (for the flow front), and the liver silhouette mask. Rows are bottom-up (TD's numpy convention).
import numpy as np, sys, trimesh
from scipy import ndimage
from PIL import Image, ImageDraw
OUT = sys.argv[1]
X0, X1, Y0, Y1 = -52.0, 52.0, -39.0, 39.0
W, H = 4096, 3072
px = (X1 - X0) / W
P = np.load(r"D:/。hkbu/molecular science/镜头设计_v3/assets/vessel_paths/real_paths.npy")
NP, NS = P.shape[:2]
seed = np.zeros((H, W), bool); R = np.zeros((H, W), np.float32); A = np.zeros((H, W), np.float32)
for i in range(NP):
    p = P[i, :, :3]; r = P[i, :, 3]
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    s = np.arange(0, L[-1], 0.02)
    x = np.interp(s, L, p[:, 0]); y = np.interp(s, L, p[:, 1]); rr = np.interp(s, L, r)
    ix = ((x - X0) / px).astype(int); iy = ((y - Y0) / px).astype(int)
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    ix, iy, rr, s = ix[ok], iy[ok], rr[ok], s[ok]
    new = ~seed[iy, ix]                      # first path to reach a pixel keeps it (shared trunks keep root arc)
    R[iy[new], ix[new]] = rr[new]; A[iy[new], ix[new]] = s[new]; seed[iy[new], ix[new]] = True
dist, (ny, nx) = ndimage.distance_transform_edt(~seed, return_indices=True)
dist = dist * px
# liver silhouette from the mesh, same frame as the paths
src = r"D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
with open(src, "rb") as f: m = trimesh.load(f, file_type="stl")
c = m.bounds.mean(axis=0); sc = 100.0 / (m.bounds[1] - m.bounds[0]).max(); v = m.vertices
v2 = np.stack([(v[:, 0] - c[0]), (v[:, 2] - c[2])], axis=1) * sc
img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
T = ((v2[m.faces] - [X0, Y0]) / px)
for tri in T: d.polygon([tuple(q) for q in tri], fill=255)
mask = np.asarray(img, np.float32) / 255.0
mask = ndimage.gaussian_filter(mask, 1.0)
field = np.stack([dist, R[ny, nx], A[ny, nx], mask], -1).astype(np.float32)
np.save(f"{OUT}/veins_field.npy", field)
print(field.shape, "dist max", dist.max(), "arc max", A.max(), "mask frac", (mask > 0.5).mean())
Image.fromarray((np.clip(1 - dist / 3, 0, 1) * 255).astype(np.uint8)[::-1]).resize((1024, 768)).save(f"{OUT}/veins_preview.png")
