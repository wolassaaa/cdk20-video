"""HKBU SCIE1007 coursework science video. Lantern moire test: the T4 stripes on the real CDK20 surface, slow rotation, at one stripe period. Usage: motion_test.py <period_px> <frames>."""
import sys
import time

from lk import *

PERIOD = float(sys.argv[1])
N = int(sys.argv[2])
out = kit.ROOT / f"styleframes/art/lantern/_work/moire/p{PERIOD:g}"
out.mkdir(parents=True, exist_ok=True)
AX, AY = 2520.0, -760.0
dx, dy = xx - AX, yy - AY
th = np.arctan2(dy, dx)
t0 = time.time()
for f in range(N):
    Rm = rot(0, -6 + 0.30 * f, -14) @ base_view()
    V = view(Rm, scale=16.0, cx=1130, cy=462, w=W, h=H, ss=0.45, L=(0.60, 0.58, 0.55), L2=(-0.7, -0.6, 0.35))
    ph = th * 1900.0 / PERIOD + V["z"] * 0.34 * 10.5 / PERIOD
    tone = np.clip(V["key"] ** 0.75, 0, 1) * (0.25 + 0.75 * V["ao"] ** 1.2)
    cf = smooth(V["conf"], 0.5, 0.86)
    wd = np.clip(0.10 + 0.72 * tone, 0, 0.86) * (0.42 + 0.58 * cf)
    aa = 0.16 * 10.5 / PERIOD
    lit = stripes(ph, wd, aa=aa) * V["mask"] * smooth(V["key"], 0.0, 0.05)
    c = blank()
    c = add(c, stripes(th * 1900.0 / PERIOD, 0.30, 0.2) * (1 - V["mask"]) * 0.30, COLD)
    c = lay(c, lit, COLD)
    Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out / f"{f:04d}.png", compress_level=1)
print(PERIOD, "sec per frame", (time.time() - t0) / N)
