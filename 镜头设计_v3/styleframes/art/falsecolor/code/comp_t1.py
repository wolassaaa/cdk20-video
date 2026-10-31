"""HKBU SCIE1007 coursework science video. falsecolor art direction: T1 picture layer.

python comp_t1.py [--front MM] [--max MM] [--out X.png]   needs ../_work/liver_field.npz from liver_field.py

The public BodyParts3D liver seen from the front. Each pixel is the distance to the nearest vessel, in mm, averaged through the organ with the front counting most.
Vessels are the dark threads, so the organ sits low on the bar and the top of the bar stays empty on purpose: this opening is heavy, nothing in it reaches full scale.
No data outside the liver, so the field is the floor of the bar. Public anatomy model, not a patient.
"""
import argparse
import os

import numpy as np
from PIL import Image

from fc_common import PUB, WORK, apply, blur, l2s, s2l, smooth, to_u8

BAR_MAX = 66.0          # mm at the top of the bar
FRONT = 11.0            # mm of depth over which the front of the organ counts most
PPM = 6.45              # px per mm in the frame
CX, CY = 742, 548       # where the middle of the liver box lands


def field(F, front=FRONT):
    inside, dist, h = F["inside"], F["dist"], float(F["h"])
    start = inside.argmax(1)
    yy = np.arange(inside.shape[1], dtype=np.float32)[None, :, None]
    w = np.exp(-np.clip(yy - start[:, None, :], 0, None) * h / front) * inside
    d = (dist * w).sum(1) / np.maximum(w.sum(1), 1e-6)
    return d, inside.any(1), h


def frame(d, t, h, ppm=PPM, cx=CX, cy=CY, W=1920, H=1080):
    s = ppm * h
    a = d.T[::-1, :].astype(np.float32)
    b = t.T[::-1, :].astype(np.float32)
    sz = (int(a.shape[1] * s), int(a.shape[0] * s))
    sd = np.asarray(Image.fromarray(a, "F").resize(sz, Image.BICUBIC))
    sm = np.asarray(Image.fromarray(b, "F").resize(sz, Image.BILINEAR))
    x0, y0 = int(cx - sz[0] / 2), int(cy - sz[1] / 2)

    def place(p):
        c = np.zeros((H, W), np.float32)
        ya, xa, yb, xb = max(y0, 0), max(x0, 0), min(y0 + p.shape[0], H), min(x0 + p.shape[1], W)
        c[ya:yb, xa:xb] = p[ya - y0:yb - y0, xa - x0:xb - x0]
        return c

    return place(sd), place(sm)


def picture(D, M, bar_max=BAR_MAX, name="s1_ember", rim=0.22):
    D = blur(D, 1.5) / np.maximum(blur(M, 1.5), 0.2)     # keeps the voxels out of the soft field and stops the edge bleeding dark
    m = smooth(0.42, 0.58, blur(M, 3.6))
    v = np.clip(D / bar_max, 0, 1) * m
    rgb = apply(v, name)
    e = np.exp(-(((blur(M, 3.6) - 0.5) / 0.09) ** 2))[..., None]    # the mesh outline: the one sharp line in a soft picture, as the CT edge is in a PET-CT overlay
    lin = s2l(rgb) + e * s2l(np.array([0.95, 0.72, 0.58])) * rim
    return l2s(lin)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--front", type=float, default=FRONT)
    ap.add_argument("--max", type=float, default=BAR_MAX)
    ap.add_argument("--out", default=os.path.join(PUB, "t1_bg.png"))
    A = ap.parse_args()
    F = np.load(os.path.join(WORK, "liver_field.npz"))
    d, t, h = field(F, A.front)
    print("distance on screen, mm, p50 p95 p99.5 max", np.percentile(d[t], [50, 95, 99.5, 100]).round(1))
    D, M = frame(d, t, h)
    Image.fromarray(to_u8(picture(D, M, A.max))).save(A.out)
    print("wrote", A.out)
