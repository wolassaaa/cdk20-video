"""HKBU SCIE1007 coursework science video. Arena direction: colour script, 1920 x 480, S1 to S8, widths by real running time.

S7 and S8 have no shot of their own in this round, so they re-use the T6 and T4 plates with their own two lamp colours: that is the lighting desk at work, no new render.
"""
import os
import numpy as np
from PIL import Image
import grade as g

CUES = [
    # section, seconds, plate, R, G, B lamps, focus x in the plate (0-1)
    ("S1", 141, "T1", "T1", None, .50),
    ("S2", 142, "T2", "T2", None, .32),
    ("S3", 129, "T3", "T3", None, .565),
    ("S4", 213, "T4", "T4", None, .50),
    ("S5", 139, "T5", "T5", None, .62),
    ("S6", 151, "T6", "T6", None, .44),
    ("S7", 49, "T6", "T6", (("FFC85A", 0.9), ("FF9E3D", 0.9), ("FFC85A", 1.0), 1.0, 0.09), .50),
    ("S8", 99, "T4", "T4", (("FFE3C2", 0.42), ("FF9E3D", 1.4), ("FFC89A", 0.8), 1.0, 0.09), .50),
]
W, H, STRIP = 1920, 480, 396
total = sum(c[1] for c in CUES)


def plate(tag, desk_key, override):
    name = tag if os.path.exists(os.path.join(g.WORK, tag + ".npy")) else tag + "_p"
    d = g.load(name)
    a, b, c, ex, bl = override or g.DESK[desk_key]
    img = g.desk(d, a, b, c)
    mp = os.path.join(g.WORK, name + "_mask.npy")
    if os.path.exists(mp) and not override:
        m = np.clip(np.load(mp)[..., :1], 0, 1)
        beams = d[..., 0:1] * g.lin(a[0]) * a[1] + d[..., 1:2] * g.lin(b[0]) * b[1]
        img = img * (1 - m) + (np.load(os.path.join(g.WORK, desk_key + "led.npy")) + beams) * m
    return g.film(g.bloom(img, bl), ex)


out = np.zeros((H, W, 3), np.float32)
x = 0.0
strips = []
for sec, dur, tag, key, ov, fx in CUES:
    w = dur / total * W
    img = np.clip(plate(tag, key, ov), 0, 1)
    pil = Image.fromarray((img * 255).astype(np.uint8)).resize((int(1920 * STRIP / 1080), STRIP), Image.LANCZOS)
    a = np.asarray(pil, np.float32) / 255
    cx = int(fx * a.shape[1])
    wi = int(round(w)) + 40
    x0 = int(np.clip(cx - wi / 2, 0, a.shape[1] - wi))
    strips.append((int(round(x)), a[:, x0:x0 + wi]))
    x += w
fade = 40
for i, (px, a) in enumerate(strips):
    wi = a.shape[1]
    al = np.ones(wi, np.float32)
    if i:
        al[:fade] = np.linspace(0, 1, fade)
    px0 = max(px - fade // 2, 0)
    wi2 = min(wi, W - px0)
    out[:STRIP, px0:px0 + wi2] = out[:STRIP, px0:px0 + wi2] * (1 - al[:wi2, None]) + a[:, :wi2] * al[:wi2, None]
out = g.over(out, os.path.join(g.WORK, "text", "CS.png"))
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(g.STILLS, "colour_script.png"))
print("wrote colour script")
