"""HKBU SCIE1007 coursework science video. manual: really run the hardest frame at 4K once, numpy path. The rising surface: mesh projection, rune lookup, four screened plates, page composite, book mapping. All sizes doubled from motion.py; nothing is reused between frames."""
import time
import sys

from mk import *

sys.path.insert(0, str(ART / "scouts/a/code"))
import kit

FW4, FH4, SW4, SH4 = 3840, 2160, 3600, 1984
t0 = time.time()
Y, X = np.mgrid[0:SH4, 0:SW4].astype(np.float32)
R = kit.rot(-12, 9, -5) @ kit.base_view()
marks = {}
t = time.time()
V = kit.view(R=R, scale=36.3, cx=1971, cy=969, w=SW4, h=SH4, ss=0.34, L=(-0.6, 0.62, 0.5))
marks["project"] = time.time() - t
t = time.time()
M = Mask(SW4 + 480, SH4 + 480, 1)
M.runes(20, 28, SW4 + 400, int((SH4 + 400) / 72), 0, 30.0, 44.0, 12.0, 72.0, 6.0)
sheet = M.a()
marks["rune sheet, once per shot"] = time.time() - t
t = time.time()
m, z, n = V["mask"], V["z"], V["normal"]
Rd = (R @ (kit.rot(0, 0, -5) @ kit.base_view()).T).astype(np.float32)
p = np.stack([(X - 1971) / 36.3, -(Y - 969) / 36.3, z], -1) @ Rd
sh_ = sample(sheet, np.clip(p[..., 0] * 36.3 + 1971 + 240, 0, SW4 + 477), np.clip(-p[..., 1] * 36.3 + 969 + 240, 0, SH4 + 477))
s = np.clip(np.clip((n @ np.array([-0.6, 0.62, 0.5], np.float32) / 1.0), 0, 1) * (0.25 + 0.75 * V["ao"]), 0, 1)
a = np.deg2rad(15)
S = 0.5 + 0.25 * (np.cos(2 * np.pi * (X * np.cos(a) + Y * np.sin(a)) / 14) + np.cos(2 * np.pi * (-X * np.sin(a) + Y * np.cos(a)) / 14))
col = np.ones((SH4, SW4, 3), np.float32) * hexc("#fbf1d4")
for g, c in ((0.66, "#f0a81e"), (0.36, "#141f66"), (0.86, "#d9361c"), (0.34, "#3a0a22")):
    col = ink(col, np.clip((np.clip((g - s) / 0.3, 0, 1) - (1 - S)) * 6 + 0.5, 0, 1), c)
col = ink(col, sh_ * 0.9, "#141f66")
pg = paper("#10195c", 41, w=SW4, h=SH4)
out = pg * (1 - m[..., None]) + col * m[..., None]
marks["print and composite"] = time.time() - t
t = time.time()
Yf, Xf = np.mgrid[0:FH4, 0:FW4].astype(np.float32)
xx, yy = Xf - 1920, Yf - 1064
vv = yy * (1 + 0.1 * np.exp(-np.abs(xx) / 132))
px = xx + 32 * np.tanh(xx / 180) * np.exp(-np.abs(xx) / 360)
fin = sample(out, np.clip(px + SW4 / 2, 0, SW4 - 2.01), np.clip(vv + SH4 / 2, 0, SH4 - 2.01))
Image.fromarray((np.clip(fin, 0, 1) * 255).astype(np.uint8)).save(ART / "manual" / "_work" / "t4k.jpg", quality=95)
marks["book mapping and save"] = time.time() - t
for k, v in marks.items():
    print("%-28s %.1f s" % (k, v))
print("total %.1f s (including setup once)" % (time.time() - t0))
