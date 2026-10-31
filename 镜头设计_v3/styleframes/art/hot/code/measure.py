"""HKBU SCIE1007 coursework science video. Art direction `hot`: no-flash numbers for the motion test, computed from the rendered frames.

Reports adjacent-frame mean luma difference, how much of the frame changes, and how many times the whole picture changes per second.
"""
import glob
import sys

import numpy as np
from PIL import Image

fs = sorted(glob.glob(sys.argv[1] + "/f*.png"))
Y, S = [], []
prev = None
for f in fs:
    im = Image.open(f).convert("RGB").resize((480, 270), Image.BOX)
    a = np.asarray(im, np.float32) / 255
    y = a @ np.array([0.2126, 0.7152, 0.0722], np.float32) * 255          # luma, 0..255, on the display signal
    Y.append(y.mean())
    if prev is not None:
        d = np.abs(y - prev)
        S.append((d.mean(), (d > 25).mean()))
    prev = y
Y = np.array(Y)
S = np.array(S)
dy = np.abs(np.diff(Y))
print("frames", len(fs))
print("adjacent mean luma diff: mean %.3f  p99 %.2f  max %.2f of 255, at frame %d" % (dy.mean(), np.percentile(dy, 99), dy.max(), dy.argmax() + 1))
print("mean abs pixel diff: mean %.2f  max %.2f at frame %d" % (S[:, 0].mean(), S[:, 0].max(), S[:, 0].argmax() + 1))
print("share of pixels moving >25/255 per frame: median %.3f  max %.3f at frame %d" % (np.median(S[:, 1]), S[:, 1].max(), S[:, 1].argmax() + 1))
# a whole-screen change: mean luma moves by 15/255 or more within half a second. Runs of it are merged into one event.
W = 15
big = np.abs(Y[W:] - Y[:-W]) >= 15
ev = []
i = 0
while i < len(big):
    if big[i]:
        j = i
        while j + 1 < len(big) and big[j + 1]:
            j += 1
        ev.append((i, j + W))
        i = j + 1
    i += 1
print("whole-screen luma events (start,end frame):", ev)
# flash: a rise and a fall of mean luma by 10% of full scale each, in opposite directions, counted per second
ext = [0]
for k in range(1, len(Y) - 1):
    if (Y[k] - Y[ext[-1]]) * (Y[k + 1] - Y[k]) < 0 and abs(Y[k] - Y[ext[-1]]) >= 25.5:
        ext.append(k)
print("luma reversals of 10% or more:", len(ext) - 1, "at frames", ext[1:])
print("start, T4, end mean luma:", Y[0].round(1), Y[234].round(1), Y[-1].round(1))
