"""HKBU SCIE1007 coursework science video. Eclipse direction: looks at a few 4K frames of the one-take, whole and at 1:1 crops."""
import os
import sys
import time

os.environ["EC4K"] = "1"
from motion import *

wd = World(2.0)
for s, crop in ((9.4, (1800, 900, 3000, 1800)), (18.7, (2900, 300, 3840, 1200)), (4.4, (1500, 500, 2500, 1300)), (14.0, (2200, 600, 3400, 1500))):
    t0 = time.time()
    a = wd.frame(s)
    print(s, "s", round(time.time() - t0, 2), flush=True)
    im = to8(a)
    im.resize((1920, 1080), Image.LANCZOS).save(WORK / f"p_{s}.png")
    im.crop(crop).save(WORK / f"p_{s}_crop.png")
