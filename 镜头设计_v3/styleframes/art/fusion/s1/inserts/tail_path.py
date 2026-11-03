"""HKBU SCIE1007 coursework science video. The tail cut for the S4 motion test (upgrade ideas 2 and 3, shot z), straight after W2: the folded bead model holds, the camera pushes in over the low-confidence tail (residues 303-346) lying across the pocket, the tail is snipped off at 302/303, lifted straight up out of the model, swung over the empty cell to the right so it hangs from its last bead, and paid out into the cell, where it coils up the way the chain did at the start of W2. Beads 1-302 never move. The lift direction was searched so the rigid tail stays clear of the model the whole way up; every frame after that is relaxed so tail beads keep their spacing and no two beads overlap or sink into the table. Writes frames/tail_path.npz for bl_inserts.py shot z. Run: python tail_path.py"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
FPS, SECONDS = 60, 12.0
CUT = 302                               # beads from here on are the tail, residues 303-346
SNIP = 6.0                              # the snip: B's scissor hands, until the cut is timed to the take
LIFT = (6.2, 1.8, 0.65)                 # the tail rises: start, how long, how far
UP = np.array((-0.064, 0.066, 0.996))   # straight up, tilted 5 degrees: the nearest clear way out of the model (see the check below)
CARRY = (7.7, 1.8, 0.95)                # then over to the next cell, hanging from its last bead: start, how long, how far along x
HANG = 0.55                             # the hanging tail's first bead ends the swing this high over the cell
DROP = (9.6, 1.8)                       # then it is paid out into the cell: start, how long

d = np.load(HERE + "frames/w2_path.npz")
start, conf, r = d["pos"][-1].astype(float), d["conf"], float(d["r"])
n = len(start)
tail = start[CUT:]
m = len(tail)
bond = np.linalg.norm(np.diff(tail, axis=0), axis=1)
cx, cy = 127.0 + CARRY[2], -2.3
coil, th = [], 0.0
for i in range(m):
    rad = 0.05 + 2.3 * r * th / (2 * math.pi)
    coil.append((cx + rad * math.cos(th), cy + rad * math.sin(th), r + 0.002))
    th += bond[min(i, m - 2)] / max(rad, 0.05)
coil = np.array(coil)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


arc = np.r_[0, np.cumsum(bond)]


def line(paid):
    """The tail paid out into the cell: beads within the paid-out length lie in the coil, the rest hang straight up over the bead landing now."""
    if paid < 0:
        return np.c_[np.full(m, coil[0, 0]), np.full(m, coil[0, 1]), coil[0, 2] + arc - paid]
    k = min(int(np.searchsorted(arc, paid, side="right")) - 1, m - 1)
    p = coil.copy()
    if k < m - 1:               # the next bead swings down on its bond round the bead that just landed, so the bond never stretches or folds
        a = (1 - (paid - arc[k]) / bond[k]) * math.pi / 2
        way = (coil[k + 1] - coil[k]) / np.linalg.norm(coil[k + 1] - coil[k])
        p[k + 1] = coil[k] + bond[k] * (math.cos(a) * way + math.sin(a) * np.array((0, 0, 1.0)))
        p[k + 2:] = p[k + 1] + np.c_[np.zeros(m - k - 2), np.zeros(m - k - 2), arc[k + 2:] - arc[k + 1]]
    return p


def target(t):
    gap = 0.03 * float(smooth((t - SNIP) / 0.25))                       # the cut opens a little before the tail goes
    held = tail + UP * (gap + LIFT[2] * float(smooth((t - LIFT[0]) / LIFT[1])))
    if t < DROP[0]:
        return held + (line(-HANG) - held) * float(smooth((t - CARRY[0]) / CARRY[1]))
    return line(-HANG + (HANG + arc[-1]) * float(smooth((t - DROP[0]) / DROP[1])))


far = 2.1 * r
mask = np.abs(np.subtract.outer(np.arange(m), np.arange(m))) > 1
frames, p = [], tail.copy()
for f in range(int(SECONDS * FPS) + 1):
    t = f / FPS
    goal = target(t)
    swing = CARRY[0] <= t < DROP[0]
    p = p + (goal - p) * 0.35 if swing else goal.copy()
    if swing:                           # while it swings into a hanging line, beads keep their spacing and give way to each other
        for _ in range(40):
            e = p[1:] - p[:-1]
            el = np.linalg.norm(e, axis=1)
            fix = e * ((el - bond) / el / 2)[:, None]
            p[1:] -= fix
            p[:-1] += fix
            dd = p[:, None] - p[None]
            dist = np.linalg.norm(dd, axis=2) + 1e-9
            over = np.where(mask & (dist < far), (far - dist) / 2, 0.0)
            p += (dd / dist[:, :, None] * over[:, :, None]).sum(1)
            p[:, 2] = np.maximum(p[:, 2], r + 0.002)
    q = start.copy()
    q[CUT:] = p
    frames.append(q)
frames = np.array(frames, np.float32)
np.savez_compressed(HERE + "frames/tail_path.npz", pos=frames, conf=conf, r=r)
full = np.abs(np.subtract.outer(np.arange(n), np.arange(n))) > 1
full[CUT - 1, CUT] = full[CUT, CUT - 1] = False        # the cut bond: those two only part
near, stretch = [], []
for q in frames:
    dd = np.linalg.norm(q[:, None] - q[None], axis=2)
    near.append(dd[full].min())
    stretch.append(np.abs(np.linalg.norm(np.diff(q[CUT:], axis=0), axis=1) / bond - 1).max())
print("frames", len(frames), "tail beads", m)
print("closest two beads, any frame: %.4f radii (touching is 2), at frame %d" % (min(near) / r, int(np.argmin(near))))
print("lowest bead bottom above the table: %.4f" % float((frames[:, :, 2] - r).min()))
print("tail bond stretch, worst: %.1f%% at frame %d" % (100 * max(stretch), int(np.argmax(stretch))))
