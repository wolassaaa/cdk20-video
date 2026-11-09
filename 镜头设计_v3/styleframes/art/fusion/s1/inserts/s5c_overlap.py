"""HKBU SCIE1007 coursework science video. S5 5-03 / 5-08 review cuts (copy of s6_overlap.py): do the Remotion words sit on the 3D figures? For every third frame it compares the finished frame with the
take under it (both at half size): pixels the words changed are the overlay; take pixels far from the bone table are figure (objects, cell rims, shadows' cores).
Prints the share of overlay pixels that lie on figure, in runs. The review strip along the top is left out.
Run: python s6_overlap.py <seq dir> <take.mp4> [step]"""
import subprocess
import sys

import numpy as np
from PIL import Image

seq, take = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 3
FF = "C:/Program Files/digiKam/ffmpeg.exe"
w, h = 960, 540
p = subprocess.Popen([FF, "-loglevel", "error", "-i", take, "-vf", "scale=%d:%d" % (w, h), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
BONE = np.array([237, 235, 228], float)
rows = []
f = 0
while True:
    b = p.stdout.read(w * h * 3)
    if len(b) < w * h * 3:
        break
    if f % step == 0:
        base = np.frombuffer(b, np.uint8).reshape(h, w, 3).astype(float)
        fin = np.asarray(Image.open("%s/element-%03d.png" % (seq, f)).convert("RGB").resize((w, h), Image.BILINEAR), float)
        over = np.abs(fin - base).max(2) > 40
        over[:31] = False                       # the review strip
        fig = np.abs(base - BONE).max(2) > 45
        both = over & fig
        # a pixel counts only with its four neighbours: encoding noise along a strong colour edge leaves single pixels, a word on a figure leaves patches
        both[1:-1, 1:-1] &= both[:-2, 1:-1] & both[2:, 1:-1] & both[1:-1, :-2] & both[1:-1, 2:]
        both[[0, -1], :] = False
        both[:, [0, -1]] = False
        n = over.sum()
        rows.append((f, n, both.sum() / max(n, 1)))
    f += 1
bad = [(f, n, r) for f, n, r in rows if n > 200 and r > 0.02]
print("OVERLAP frames checked: %d (every %d of %d)" % (len(rows), step, f))
print("OVERLAP frames with more than 2%% of the words on a figure: %d" % len(bad))
runs = []
for f_, n, r in bad:
    if runs and f_ - runs[-1][1] <= step:
        runs[-1][1], runs[-1][2] = f_, max(runs[-1][2], r)
    else:
        runs.append([f_, f_, r])
for a, b_, r in runs:
    print("OVERLAP  %.2f-%.2fs (frames %d-%d): up to %.0f%%" % (a / 30, b_ / 30, a, b_, 100 * r))
