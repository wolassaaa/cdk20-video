"""HKBU SCIE1007 coursework science video. Style scout e8: foil balloon letters as a double sided pillow field. System Python."""
import numpy as np
from PIL import Image, ImageFilter

from common import WORK, text_mask

m = text_mask("CDK20", "ariblk.ttf", 300, pad=30)
h, w = m.shape
im = Image.fromarray((m > 0.5).astype(np.uint8) * 255)
# distance from the edge via repeated erosion, coarse is fine
hgt = np.zeros((h, w), np.float32)
cur = m > 0.5
for r in range(100):
    if not cur.any():
        break
    hgt += cur
    cur = cur & np.roll(cur, 1, 0) & np.roll(cur, -1, 0) & np.roll(cur, 1, 1) & np.roll(cur, -1, 1)
pill = np.sqrt(np.clip(hgt / 80.0, 0, 1))
yy, xx = np.mgrid[0:h, 0:w]
# radial puckers along the seam: wrinkles where the two foil sheets are welded
wr = np.sin(xx * 0.22 + np.sin(yy * 0.095) * 3) * np.sin(yy * 0.2 + np.sin(xx * 0.085) * 3)
wr = wr * np.exp(-hgt / 26) * (hgt > 0) * 0.045
z = (pill + wr) * 0.42
z = np.asarray(Image.fromarray(z.astype(np.float32), "F").resize((w // 2, h // 2), Image.BILINEAR))
ins = np.asarray(im.resize((w // 2, h // 2), Image.BILINEAR)) > 128
h2, w2 = z.shape
sc = 12.5 / w2
vid = -np.ones((h2, w2), np.int64)
idx = np.argwhere(ins)
vid[idx[:, 0], idx[:, 1]] = np.arange(len(idx))
n = len(idx)
vx = (idx[:, 1] - w2 / 2) * sc
vy = -(idx[:, 0] - h2 / 2) * sc
vz = z[idx[:, 0], idx[:, 1]]
front = np.c_[vx, vy, vz]
back = np.c_[vx, vy, -vz]
v = np.concatenate([front, back]).astype(np.float32)
a = vid[:-1, :-1]; b = vid[:-1, 1:]; c = vid[1:, 1:]; d = vid[1:, :-1]
ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
qf = np.c_[a[ok], d[ok], c[ok], b[ok]]
qb = qf[:, ::-1] + n
q = np.concatenate([qf, qb]).astype(np.int32)
np.savez(WORK / "e8_letters.npz", v=v, q=q)
print(len(v), len(q))
