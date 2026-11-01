"""HKBU SCIE1007 coursework science video. W3 in TouchDesigner: where each of the 8,918 dots sits and when it leaves the ring. Writes seats.npy for TouchDesigner and count.json for the number on screen.

The music is not in the project yet, so beats come from the script: Godmother, 8 bars in about 15.7 s. Replace BEATS with times measured from the track when it arrives.
Run: python seats.py
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
N = 8918                     # real: the number of designs in Ren 2023
W, H, MARGIN, STEP = 1920, 1080, 36, 13.3
BAR = 15.7 / 8
BEAT = BAR / 4
BEATS = [i * BEAT for i in range(33)]
FIRST, LAST = 4, 25          # the first dots leave on bar 2, the last so they land on bar 8
FLY = 1.4
SPREAD = 0.12

rng = np.random.default_rng(1007)
xs = np.arange(-(W / 2 - MARGIN), W / 2 - MARGIN + 0.1, STEP)
ys = np.arange(-(H / 2 - MARGIN), H / 2 - MARGIN + 0.1, STEP)
gx, gy = [a.ravel() for a in np.meshgrid(xs - xs.mean(), ys - ys.mean())]
d = np.hypot(gx, gy)
keep = np.argsort(d)[-N:]    # the hole in the middle takes up the rest, so the count is exact
gx, gy, d = gx[keep], gy[keep], d[keep]
print("dots", len(gx), "hole radius %.0f" % d.min())

order = np.argsort(d + rng.uniform(0, 120, N))  # nearest the ring leave first
totals = [round(N ** ((b - FIRST + 1) / (LAST - FIRST + 1))) for b in range(FIRST, LAST + 1)]
totals[-1] = N
leave = np.zeros(N, dtype=np.float32)
start = 0
for b, end in zip(range(FIRST, LAST + 1), totals):
    leave[order[start:end]] = BEATS[b]
    start = end
leave += rng.uniform(0, SPREAD, N).astype(np.float32)
angle = rng.uniform(0, 2 * math.pi, N)

seeds = np.stack([gx, gy, angle, leave], axis=1).astype(np.float32)[None, :, :]
np.save(os.path.join(HERE, "seats.npy"), seeds)

land = np.sort(leave + FLY)
times = np.arange(0, 15.7, 1 / 60)
counts = np.searchsorted(land, times, side="right").tolist()
json.dump(dict(fps=60, count=counts, land=float(land[-1])), open(os.path.join(HERE, "count.json"), "w"), separators=(",", ":"))
print("last lands %.2f, bar 8 starts %.2f, batches %s" % (land[-1], 7 * BAR, totals))
