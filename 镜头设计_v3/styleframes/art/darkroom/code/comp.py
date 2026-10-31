"""HKBU SCIE1007 coursework science video. Final grade of the six darkroom stills, plus a phone-size contact sheet for the thumbnail test. Run: python comp.py [name=file ...]. Default files are t1..t6."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from grade import *

P = {
    # name: ev, halation tint, threshold, vignette
    "T1": dict(src="t1", ev=1.9, tint=(1.0, 0.45, 0.30), thr=0.45, vig=0.34),
    "T2": dict(src="t2", ev=1.15, tint=(1.0, 0.60, 0.40), thr=0.50, vig=0.30),
    "T3": dict(src="t3", ev=1.6, tint=(1.0, 0.20, 0.10), thr=0.004, vig=0.10, boost=1.0),
    "T4": dict(src="t4", ev=1.12, tint=(0.45, 0.65, 1.0), thr=0.50, vig=0.40),
    "T5": dict(src="t5", ev=1.75, tint=(1.0, 0.45, 0.45), thr=0.50, vig=0.34),
    "T6": dict(src="t6", ev=1.05, tint=(1.0, 0.68, 0.42), thr=0.50, vig=0.26),
}
over = dict(a.split("=") for a in sys.argv[1:])
thumbs = []
for k, p in P.items():
    f = os.path.join(WORK, over.get(k, p["src"]) + ".npy")
    if not os.path.exists(f):
        print("missing", f)
        continue
    a = np.load(f).astype(np.float64)
    h, w = a.shape[:2]
    if k == "T3":
        # the only light in the frame gets a wide soft bloom, as a dark-adapted eye would see it
        hi = gauss(a, 18) * 0.55 + gauss(a, 60) * 0.5
        a = a * 1.0 + hi
    out = finish(a, p["ev"], p["tint"], p["thr"], p["vig"])
    save(out, k)
    thumbs.append(Image.fromarray((out * 255).astype(np.uint8)).resize((320, 180), Image.LANCZOS))

# phone thumbnails, in film order
if thumbs:
    S = Image.new("RGB", (3 * 320 + 40, 2 * 180 + 30), (24, 24, 24))
    for i, t in enumerate(thumbs):
        S.paste(t, (10 + (i % 3) * 330, 10 + (i // 3) * 190))
    S.save(os.path.join(WORK, "thumbs.png"))
