"""HKBU SCIE1007 coursework science video. Pigment direction: does the test clip flicker? Compares neighbouring frames in the 3 s to 6 s stretch, where only the slow turn is left.
Two numbers matter: how much of the frame changes at all, and whether the change comes in spikes. Spikes in luminance from frame to frame are what the eye reads as flicker.
"""
import numpy as np
from pathlib import Path
from PIL import Image

D = Path(__file__).resolve().parent.parent / "_work" / "motion"
load = lambda i: np.asarray(Image.open(D / f"f_{i:04d}.png").convert("L"), np.float32)
prev = load(95)
means, diffs = [prev.mean()], []
for i in range(96, 180):
    cur = load(i)
    means.append(cur.mean())
    diffs.append(np.abs(cur - prev).mean())
    prev = cur
m = np.array(means)
d = np.array(diffs)
print("mean luma range over 3 s: %.3f .. %.3f levels" % (m.min(), m.max()))
print("largest jump in mean luma between neighbours: %.3f levels" % np.abs(np.diff(m)).max())
print("frame-to-frame abs diff: mean %.3f, max %.3f, spike ratio %.2f" % (d.mean(), d.max(), d.max() / d.mean()))
