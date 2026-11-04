"""HKBU SCIE1007 coursework science video. Paths for bl_inserts.py shot u, the motion test of the new S4 opening (W2 to 4-05: the AI guesses CDK20's shape, the tail never settles, the tail is cut off). Two things move near the model and must never pass through it:

1. The tail's wobble while it "won't hold still": the tail swings about its last kept residue (302) between the real pose and four swung poses. Each swing is tested all the way out: no tail atom from 304 on comes closer to a kept atom (1-302) than the real pose already has one.
2. The cut: the tail (now a tube along its backbone, 303-346) is drawn out of the model along its own path, the cut end first, so every part of it only passes where the tube already was; past the cut it leaves along a line that is tested clear of the model and of the rest of the tail, crawls low over the model's shoulder and the gap, down into the next cell, and winds into a flat coil there, the cut end at its centre. Version 2: version 1 (u_path.py) lifted the tail straight up and hung it, which ran out of the top of the frame.

Every frame of the cut is checked: tube to kept atoms, tube to itself, tube to the table. Lengths are in Angstrom for the model and in table units on the table. Writes frames/u_tail_2.npz. Run: python u_path_2.py"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
FPS = 60
P_S, P_UP = 0.05, math.radians(16)          # as in bl_inserts.py
CELL, NEXT = (127.0, -2.3), (127.95, -2.3)   # cell 22, where the model sits, and cell 23
TR = 1.6                                      # the tube's radius, Angstrom
VDW = 1.7                                     # a kept atom's radius, Angstrom: the model's surface lies about here
# the cut, seconds on the shot's clock (shot u starts at 0 = 412 s on the film's clock)
CUT = dict(snip=33.5, tight=(33.6, 0.8), draw=(34.5, 6.0), end=42.5)
RC = 0.15                                    # the coil's outer radius, table units

pdb = [l for l in open(HERE + "../../../../../assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[76:78].strip() != "H"]
res = np.array([int(l[22:26]) for l in pdb])
xyz = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in pdb])
name = [l[12:16].strip() for l in pdb]
ca = np.array([xyz[i] for i in range(len(pdb)) if name[i] == "CA"])
keep, tail_atoms = xyz[res <= 302], xyz[res >= 304]
centre = xyz.mean(0)


def turn(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a @ b)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def axis_angle(ax, ang):
    ax = ax / np.linalg.norm(ax)
    k = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(ang) * k + (1 - math.cos(ang)) * k @ k


# the small model's place on the table, as shot q sets it
full = np.load(HERE + "frames/cdk20.npz")
R = turn(full["mouth"], np.array([0, -math.cos(P_UP), math.sin(P_UP)]))
a = -(math.pi / 2 - P_UP)
Q = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
pts = full["verts"] @ R.T * P_S @ Q.T
pk = Q @ (R @ full["pocket"]) * P_S
S = 0.31 / float(np.linalg.norm(pts[:, :2] - pk[:2], axis=1).max())
LOC = np.array([CELL[0] - pk[0] * S, CELL[1] - pk[1] * S, -float(pts[:, 2].min()) * S + 0.01])
A = P_S * S                                  # table units to the Angstrom
world = lambda x: (np.asarray(x) - centre) @ R.T * P_S @ Q.T * S + LOC
keep_w = world(keep)
print("one Angstrom is %.5f table units; model top %.3f" % (A, float(world(full["verts"] + centre)[:, 2].max())))


def nearest(p, cloud, chunk=400):
    p = np.atleast_2d(p)
    return np.concatenate([np.sqrt(((p[i:i + chunk, None] - cloud[None]) ** 2).sum(2)).min(1) for i in range(0, len(p), chunk)])


# 1. the wobble: four swings about residue 302, each clear all the way out
pivot = ca[301]
real = float(nearest(tail_atoms, keep).min())
g = np.random.default_rng(5)
picks = []
for _ in range(2000):
    ax, ang = g.normal(size=3), math.radians(g.uniform(18, 40))
    if all(float(nearest(pivot + (tail_atoms[::3] - pivot) @ axis_angle(ax, ang * s).T, keep).min()) >= real - 0.05 for s in (0.25, 0.5, 0.75, 1.0)):
        far = (ca[302:] - pivot) @ axis_angle(ax, ang).T + pivot
        if all(np.abs(far - (ca[302:] - pivot) @ p.T - pivot).max() > 6.0 for p in picks):         # the four read as four different guesses
            picks.append(axis_angle(ax, ang))
            if len(picks) == 4:
                break
assert len(picks) >= 3, "only %d clear swings" % len(picks)
print("wobble: %d swings," % len(picks) + " none closer to the kept part than the real pose's %.2f A" % real)

# 2. the cut
up = np.array([0, 0, 1.0])
chain = world(ca[302:])                      # 303-346 on the table
m = len(chain)
bond = np.linalg.norm(np.diff(chain, axis=0), axis=1)
arc = np.r_[0, np.cumsum(bond)]
rod = arc[-1]
far_w, near_w = world(xyz[res <= 300]), world(xyz[(res >= 301) & (res <= 302)])     # the two kept residues at the cut touch the cut end, as bonded atoms do
own_far = float(nearest(chain[1:], far_w).min()) / A
own_near = float(nearest(chain[:1], near_w).min()) / A
NEED = min(TR + VDW, own_far) - 0.05        # the tube may come as close as the backbone already is, never closer
print("the tail's backbone sits %.2f A from the kept atoms (%.2f A from the bonded ones at the cut); the tube keeps %.2f A" % (own_far, own_near, NEED))


def route(d, n=400, step=0.25 * A):
    """From the cut end along d, turning straight up."""
    p, out = chain[0].copy(), [chain[0].copy()]
    for i in range(n):
        L = i * step / A
        w = d + (up - d) * min(1.0, max(0.0, (L - 10.0) / 14.0))
        p = p + step * w / np.linalg.norm(w)
        out.append(p.copy())
    return np.array(out)


inner = np.array([a_ + (b_ - a_) * u for a_, b_ in zip(chain[3:-1], chain[4:]) for u in np.linspace(0, 1, 8, endpoint=False)])     # the tail's own path, between its residues too: the drawn-out tube passes along all of it
ways = []
spiral = np.arange(300) + 0.5
for z_, ph in zip(1 - spiral / 300, math.pi * (1 + 5 ** 0.5) * spiral):        # nearest to straight up first
    d = np.array([math.sqrt(1 - z_ * z_) * math.cos(ph), math.sqrt(1 - z_ * z_) * math.sin(ph), z_])
    r_ = route(d, 140)
    if nearest(r_[1:], far_w).min() / A >= NEED and nearest(r_[16:], near_w).min() / A >= NEED and nearest(r_[8:], inner).min() / A >= 2 * TR:
        ways.append(d)
        if len(ways) == 24:
            break
assert ways, "no clear way out of the cut"
STEP = 0.25 * A


def chaikin(p, n=5):
    for _ in range(n):
        q = [p[0]]
        for a_, b_ in zip(p[:-1], p[1:]):
            q += [0.75 * a_ + 0.25 * b_, 0.25 * a_ + 0.75 * b_]
        q.append(p[-1])
        p = np.array(q)
    return p


def resample(p):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    u = np.arange(0, s[-1], STEP)
    return np.c_[[np.interp(u, s, p[:, k]) for k in range(3)]].T


# the coil in the next cell: a flat spiral, wound inwards, its turns 2.6 tube radii apart; long enough for the whole tail
pitch = 2.6 * TR * A
th = np.arange(0, 40 * math.pi, 0.002)
rad = RC - pitch * th / (2 * math.pi)
th, rad = th[rad >= 0.035], rad[rad >= 0.035]
spiral = resample(np.c_[NEXT[0] + rad * np.cos(math.pi + th), NEXT[1] + rad * np.sin(math.pi + th), np.full(len(th), TR * A + 0.002)])
assert len(spiral) * STEP > rod * 1.1, "coil too short"


def snake(d, H, X1, Y1):
    """The tail crawls out low, over the model's shoulder and the gap, down into the next cell and round the spiral."""
    straight = route(d, 40)                  # 10 A out along the clear line
    P1 = straight[-1]
    ctrl = np.array([P1, P1 + d * 0.06, (X1, Y1, H), (0.5 * (X1 + NEXT[0] - RC), 0.5 * (Y1 + CELL[1]), H), (NEXT[0] - RC, CELL[1] + 0.12, 0.08), spiral[0], spiral[4]])      # it comes down outside the coil and joins it along its way round, so the joint never cuts in over the next turn
    mid = resample(chaikin(ctrl))
    return np.r_[straight, mid[1:], spiral[5:]]


best_way, closest = None, 0
for H, d, Y1, dx in [(H, d, Y1, dx) for H in (0.6, 0.7, 0.8) for d in ways for Y1 in (CELL[1] + 0.1, CELL[1] + 0.25, CELL[1] - 0.1) for dx in (0.05, 0.2)]:       # lowest first
    w = snake(d, H, chain[0][0] + dx, Y1)
    if w[:, 2].min() < TR * A or nearest(w[1:], far_w).min() / A < NEED or nearest(w[16:], near_w).min() / A < NEED:
        continue
    own = float(nearest(w[8:], inner).min()) / A
    closest = max(closest, own)
    if own >= 2 * TR:
        best_way, best = w, d
        break
print("closest the tube comes to its own path over the tries: %.2f A" % closest)
assert best_way is not None, "no low way over"
print("the cut end leaves %.0f degrees off straight up" % math.degrees(math.acos(best[2])))
print("the tail crawls over at %.2f high, %.2f behind the cell's middle (model top %.2f), then round the coil" % (H, Y1 - CELL[1], float(world(full["verts"] + centre)[:, 2].max())))
path = np.r_[chain[::-1], best_way[1:]]      # the free end's place first, back along the tail to the cut, then out
s_path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
s0 = rod - arc                               # each bead's place on the path now: the cut end at rod, the free end at 0
at = lambda s: np.c_[[np.interp(s, s_path, path[:, k]) for k in range(3)]].T
U = s_path[-1] - rod                         # the cut end ends at the centre of the coil


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def tail_at(t):
    return at(s0 + U * smooth((t - CUT["draw"][0]) / CUT["draw"][1]))


times = np.arange(CUT["snip"], CUT["end"] + 1e-9, 1 / FPS)
frames = np.array([tail_at(t) for t in times], np.float32)
mids = lambda p: np.r_[p, (p[1:] + p[:-1]) / 2]
gap = min(float(nearest(mids(f), far_w).min()) for f in frames[::2]) / A
gap_near = min(float(nearest(mids(f), near_w).min()) for f in frames[::2]) / A
far = np.abs(np.subtract.outer(np.arange(m), np.arange(m))) > 2
self_ = min(float(np.linalg.norm(f[:, None] - f[None], axis=2)[far].min()) for f in frames) / A
low = float(frames[:, :, 2].min()) - TR * A
step = np.linalg.norm(np.diff(frames, axis=0), axis=2).max() / A
stretch = max(float((np.linalg.norm(np.diff(f, axis=0), axis=1) / bond - 1).max()) for f in frames)
print("cut, %d frames: tube to the nearest kept atom %.2f A (%.2f kept), to the two at the cut %.2f A (%.2f to start with)" % (len(frames), gap, NEED, gap_near, own_near))
print("tube to itself, beads 3 or more apart: %.2f A (2 x %.1f needed); lowest tube bottom %.4f over the table" % (self_, TR, low))
print("bond stretch, worst %.1f%%; fastest bead moves %.1f A a frame; highest point %.2f" % (100 * stretch, step, float(frames[:, :, 2].max())))
assert gap >= NEED - 0.01 and gap_near >= own_near - 0.05 and self_ >= 2 * TR and low >= 0
np.savez_compressed(HERE + "frames/u_tail_2.npz", pos=frames, t0=CUT["snip"], picks=np.array(picks), pivot=pivot, tr=TR * A)
print("U_PATH_OK")
