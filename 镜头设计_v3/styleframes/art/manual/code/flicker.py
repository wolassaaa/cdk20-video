"""HKBU SCIE1007 coursework science video. manual: the flicker numbers for the motion test. Mean brightness change between neighbouring frames, and how many times per second a whole-screen change happens.
Run: python flicker.py <frames_dir>"""
import glob
import os
import sys

import numpy as np
from PIL import Image

fs = sorted(glob.glob(os.path.join(sys.argv[1], "*.jpg")))
prev = None
d, big, signed = [], [], []
for f in fs:
    a = np.asarray(Image.open(f).convert("L").resize((480, 270), Image.BOX), np.float32) / 255
    if prev is not None:
        e = np.abs(a - prev)
        d.append(float(e.mean()))
        big.append(float((e > 0.1).mean()))
        signed.append(float((a - prev).mean()))
    prev = a
d, big, signed = np.array(d), np.array(big), np.array(signed)
print("frames", len(fs))
print("mean change between neighbouring frames %.4f, worst %.4f at frame %d" % (d.mean(), d.max(), d.argmax()))
print("mean brightness step, worst %.4f at frame %d" % (np.abs(signed).max(), np.abs(signed).argmax()))
# a whole-screen change: at least half the picture moves by more than 10 percent, counted once per run of frames
run = big > 0.5
starts = int(((run[1:]) & (~run[:-1])).sum() + run[0])
print("frames with over half the screen changing %d, separate events %d, in %.1f s" % (run.sum(), starts, len(fs) / 30))
# sign flips of the overall brightness faster than 2 per second would read as flicker
win = 15
worst = 0
for i in range(0, len(signed) - win):
    s = np.sign(signed[i:i + win][np.abs(signed[i:i + win]) > 0.002])
    if len(s) > 1:
        worst = max(worst, int((s[1:] != s[:-1]).sum()))
print("largest number of up/down reversals of overall brightness in any half second:", worst)
