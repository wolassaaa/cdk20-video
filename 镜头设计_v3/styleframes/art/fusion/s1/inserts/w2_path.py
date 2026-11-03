"""HKBU SCIE1007 coursework science video. The bead chain for the W2 motion test (S4 upgrade idea 1): 346 beads, one per residue of the AlphaFold DB v6 model, lie coiled in S3's empty cell, are lifted like a necklace, fold in the air and set down as the model's real shape. The path is drawn, AlphaFold does not simulate folding; only the end is real. The necklace is picked up whole, then the whole chain folds at once, so no bead has to thread into a finished shape. Every frame is relaxed so neighbours keep their spacing and no two beads overlap or sink into the table, then all frames are written to frames/w2_path.npz for bl_inserts.py shot y. Run: python w2_path.py"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
CELL = (127.0, -2.3)                    # cell 22, where S3 ends
FPS, SECONDS = 60, 25.0
LIFT = (3.0, 3.0)                       # the first bead lifts off the coil, and the spread to the last: the necklace is picked up whole
RISE = 1.2                              # how long each bead takes to rise
FOLD = (7.0, 3.0, 9.0)                  # the whole chain folds: start, spread from first bead to last, and how long each takes
LOCK = 19.5                             # the shape locks in: the first big chord, until the song is here
HIGH = 0.3                              # how high the necklace is lifted
AIR = 0.06                              # the model builds this far above the table, clear of the coil, and sets down on the lock

lines = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"]
ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in lines])
conf = np.array([float(l[60:66]) for l in lines])
n = len(ca)
ca -= ca[:302].mean(0)
s = math.sqrt(math.pi * 0.3 ** 2 / (2.3 * 0.42 * 3.8 * 3.8 * (n - 1)))      # the same scale as shot x: the whole necklace coils inside the cell
r = 3.8 * s * 0.42
bond = np.linalg.norm(np.diff(ca, axis=0), axis=1) * s
folded = ca * s + (*CELL, 0.0)
folded[:, 2] += r + 0.02 - folded[:, 2].min()
coil, th = [], 0.0
for i in range(n):
    rad = 0.05 + 2.3 * r * th / (2 * math.pi)
    coil.append((CELL[0] + rad * math.cos(th), CELL[1] + rad * math.sin(th), r))
    th += 3.8 * s / max(rad, 0.05)
coil = np.array(coil)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def lifted(t):
    return smooth((t - LIFT[0] - LIFT[1] * np.arange(n) / n) / RISE)


def folding(t):
    return smooth((t - FOLD[0] - FOLD[1] * np.arange(n) / n) / FOLD[2])


def target(t):
    up = coil + (0, 0, HIGH)
    above = folded + (0, 0, AIR * (1 - float(smooth((t - LOCK) / 0.8))))
    a, u = lifted(t)[:, None], folding(t)[:, None]
    return coil + (up - coil) * a + (above - up) * u


far = 2.1 * r                           # no two beads closer than this, centre to centre
mask = np.abs(np.subtract.outer(np.arange(n), np.arange(n))) > 1
frames, p = [], coil.copy()
for f in range(int(SECONDS * FPS) + 1):
    t = f / FPS
    free = (lifted(t) > 0).astype(float)              # beads still lying in the coil do not move
    goal = target(t)
    p = p + (goal - p) * 0.3
    fly = np.nonzero(free)[0]
    near_ok = np.abs(fly[:, None] - np.arange(n)[None, :]) > 1
    for _ in range(40):
        e = p[1:] - p[:-1]
        el = np.linalg.norm(e, axis=1)
        wa, wb = free[1:], free[:-1]
        share = np.where(wa + wb > 0, (el - bond) / el / np.maximum(wa + wb, 1e-9), 0.0)
        p[1:] -= e * (share * wa)[:, None]
        p[:-1] += e * (share * wb)[:, None]
        if len(fly):            # only beads in flight give way, so only their distances are needed
            d = p[fly, None, :] - p[None, :, :]
            dist = np.linalg.norm(d, axis=2) + 1e-9
            over = np.where(near_ok & (dist < far), far - dist, 0.0)
            over *= np.where(free[None, :] > 0, 0.5, 1.0)       # two beads in flight each go half the way
            p[fly] += (d / dist[:, :, None] * over[:, :, None]).sum(1)
        p[:, 2] = np.maximum(p[:, 2], r + 0.002)
    frames.append(p.copy())
frames = np.array(frames, np.float32)
np.savez_compressed(HERE + "frames/w2_path.npz", pos=frames, conf=conf, r=r)
near, stretch = [], []
for q in frames:                        # checked one frame at a time; all at once does not fit in memory
    dd = np.linalg.norm(q[:, None] - q[None], axis=2)
    near.append(dd[mask].min())
    stretch.append(np.abs(np.linalg.norm(np.diff(q, axis=0), axis=1) / bond - 1).max())
print("beads", n, "radius", round(r, 4), "frames", len(frames))
print("closest two beads, any frame: %.2f radii (touching is 2), at frame %d" % (min(near) / r, int(np.argmin(near))))
print("lowest bead bottom above the table: %.4f" % float((frames[:, :, 2] - r).min()))
print("bond stretch, worst: %.1f%% at frame %d" % (100 * max(stretch), int(np.argmax(stretch))))
