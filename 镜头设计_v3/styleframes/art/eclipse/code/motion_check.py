"""HKBU SCIE1007 coursework science video. Eclipse direction: flicker check. Adjacent-frame mean brightness difference over the whole take, on a 0-255 scale (Rec.709 luma)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

d = Path(sys.argv[1])
fps = float(sys.argv[2])
fs = sorted(d.glob("*.png"))
m = []
for f in fs:
    a = np.asarray(Image.open(f).convert("RGB").resize((480, 270), Image.BILINEAR), np.float32)
    m.append((a * [0.2126, 0.7152, 0.0722]).sum(-1).mean())
m = np.array(m)
dm = np.diff(m)
ab = np.abs(dm)
print("frames", len(m), "mean luma min/max", round(float(m.min()), 2), round(float(m.max()), 2))
print("adjacent mean-brightness diff per frame: max", round(float(ab.max()), 3), "at", round(float(ab.argmax() / fps), 2), "s, mean", round(float(ab.mean()), 3))
# sign changes of any swing bigger than 1 level: how often the whole screen reverses direction
ext = [0]
for i in range(1, len(m) - 1):
    if (m[i] - m[i - 1]) * (m[i + 1] - m[i]) < 0:
        ext.append(i)
ext.append(len(m) - 1)
kept = [ext[0]]
for i in ext[1:]:
    if abs(m[i] - m[kept[-1]]) >= 8:
        kept.append(i)
print("swings of 8 levels or more:", [(round(i / fps, 2), round(float(m[i]), 1)) for i in kept])
best = 0
for a, b in zip(kept[:-1], kept[1:]):
    best = max(best, 0.5 * fps / max(b - a, 1))
print("fastest whole-screen swing, equivalent cycles per second", round(best, 2))
