"""HKBU SCIE1007 coursework science video. Lantern render bench: one real 3840x2160 frame of the hardest kind in the film (T4: cold rays on the real mesh, moving camera), numpy only, one process, while other renders share the machine."""
import time

import numpy as np

import lk
from mv import view2, S

W, H = 3840, 2160
Rm = (lk.rot(0, -6, -14) @ lk.base_view()).astype(np.float64)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
for i in range(2):
    t0 = time.time()
    V = view2(Rm, 32.0, 2260.0, 924.0, cull_back=True, w=W, h=H, ss=0.5)
    t1 = time.time()
    th = np.arctan2(yy + 1520.0, xx - 5040.0)
    phase = th * 3800.0 / 32.0 + V["z"] * 0.23 * 2
    tone = np.clip(V["key"] ** 0.75, 0, 1) * (0.25 + 0.75 * V["ao"] ** 1.2)
    width = np.clip(0.10 + 0.72 * tone, 0, 0.86)
    v = np.abs(phase - np.floor(phase) - 0.5) * 2
    lit = lk.smooth(width - (1 - v), -0.11, 0.11) * V["mask"]
    rgb = (lit[..., None] * lk.COLD + (1 - lit[..., None]) * lk.BLACK)
    img = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    lk.Image.fromarray(img).save(lk.kit.ROOT / "styleframes/art/lantern/_work/bench4k.png", compress_level=1)
    print(f"mesh passes {t1 - t0:.1f} s, whole frame {time.time() - t0:.1f} s, {len(S['v'])} points")
