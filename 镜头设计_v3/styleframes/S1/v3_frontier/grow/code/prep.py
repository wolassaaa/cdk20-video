"""GROW / prep: project BodyParts3D liver + vessel meshes (anterior view) into 1920x1080 masks.

Anterior view: viewer at -y looking +y, z up.  screen_x = +x (patient left on viewer's right), screen_y = -z.
Outputs code/../work/liver_proj.npz with
  mask    float32 HxW  anti-aliased liver silhouette (rasterised at 3x, box-downsampled)
  portal, hepv, art, gb  uint8 HxW  projected vessel / gallbladder masks
  root    (x, y)  portal vein entry point (porta hepatis) in px
  ivc     (x, y)  top of the inferior vena cava where hepatic veins drain
  px_per_mm, offset
"""
import numpy as np, json, sys, os
from PIL import Image, ImageDraw

ANAT = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
SS = 3


def load_stl(p):
    b = open(p, "rb").read()
    n = np.frombuffer(b, np.uint32, 1, 80)[0]
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.frombuffer(b, dt, n, 84)["v"].astype(np.float64)  # (n,3,3)


tri = {k: load_stl(ANAT + k + ".stl") for k in
       ["liver_parenchyma_segments", "portal_vein_hepatic", "hepatic_veins", "hepatic_artery",
        "gallbladder", "inferior_vena_cava"]}
liv = tri["liver_parenchyma_segments"]
lo, hi = liv.reshape(-1, 3).min(0), liv.reshape(-1, 3).max(0)
print("liver bbox mm", lo.round(1), hi.round(1), "size", (hi - lo).round(1))

# layout: liver width -> LW px, centred at (CX, CY)
LW = float(sys.argv[1]) if len(sys.argv) > 1 else 1180.0
CX = float(sys.argv[2]) if len(sys.argv) > 2 else 960.0
CY = float(sys.argv[3]) if len(sys.argv) > 3 else 500.0
s = LW / (hi[0] - lo[0])
mx, mz = (hi[0] + lo[0]) / 2, (hi[2] + lo[2]) / 2


def proj(v):
    return np.stack([CX + (v[..., 0] - mx) * s, CY - (v[..., 2] - mz) * s], -1)


def raster(t, ss=SS, clip=None):
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    p = proj(t) * ss
    if clip is not None:
        p = p[clip]
    for q in p:
        d.polygon([tuple(q[0]), tuple(q[1]), tuple(q[2])], fill=255)
    a = np.asarray(im, np.float32) / 255.0
    return a.reshape(H, ss, W, ss).mean((1, 3))


mask = raster(liv)
gb3 = raster(tri["gallbladder"])
mask = np.maximum(mask, gb3)          # silhouette = liver + gallbladder (the bulge under the right lobe)
print("mask px", mask.sum())
portal = raster(tri["portal_vein_hepatic"], 1)
hepv = raster(tri["hepatic_veins"], 1)
art = raster(tri["hepatic_artery"], 1)
gb = raster(tri["gallbladder"], 1)

# portal vein entry: lowest portal-vein vertex that still lies within the liver's projected mask band
pv = tri["portal_vein_hepatic"].reshape(-1, 3)
pp = proj(pv)
# trunk = vertices below liver mid; take the lowest z overall (start of hepatic portal vein)
i0 = np.argmin(pv[:, 2])
root_low = pp[i0]
# entry into the parenchyma: walk up the trunk: points with z within 25mm above the lowest, take their mean x
sel = pv[:, 2] < pv[i0, 2] + 20
root_low = proj(pv[sel].mean(0))
hv = tri["inferior_vena_cava"].reshape(-1, 3)
ivc_top = proj(hv[np.argmax(hv[:, 2])])
hvv = tri["hepatic_veins"].reshape(-1, 3)
print("portal low", root_low.round(1), "ivc top", ivc_top.round(1))
print("portal z range", pv[:, 2].min(), pv[:, 2].max(), "liver z", lo[2], hi[2])

np.savez_compressed(os.path.join(OUT, "liver_proj.npz"), mask=mask.astype(np.float32),
                    portal=(portal * 255).astype(np.uint8), hepv=(hepv * 255).astype(np.uint8),
                    art=(art * 255).astype(np.uint8), gb=(gb * 255).astype(np.uint8),
                    root=root_low, ivc=ivc_top, px_per_mm=s, center=np.array([CX, CY]))
rgb = np.zeros((H, W, 3), np.float32)
rgb[..., 0] = mask * 0.5 + portal * 0.5
rgb[..., 2] = hepv
rgb[..., 1] = art * 0.6 + gb * 0.4
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "proj_check.png"))
print("done")
