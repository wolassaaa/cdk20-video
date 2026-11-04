"""HKBU SCIE1007 coursework science video. Paths for bl_inserts.py shot u, the motion test of the new S4 opening (W2 to 4-05: the AI guesses CDK20's shape, the tail never settles, the tail is cut off). Two things move near the model and must never pass through it:

1. The tail's wobble while it "won't hold still": the tail swings about its last kept residue (302) between the real pose and four swung poses. Each swing is tested all the way out: no tail atom from 304 on comes closer to a kept atom (1-302) than the real pose already has one.
2. The cut: the tail (now a tube along its backbone, 303-346) is drawn out of the model along its own path, the cut end first, so every part of it only passes where the tube already was; past the cut it leaves along a line that is tested clear of the model and of the rest of the tail, turns straight up, hangs from its cut end, is carried over the next cell and paid out into it, coiling from its free end (the hinge from tail_path.py, so no bond stretches).

Every frame of the cut is checked: tube to kept atoms, tube to itself, tube to the table. Lengths are in Angstrom for the model and in table units on the table. Writes frames/u_tail.npz. Run: python u_path.py"""
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
CUT = dict(snip=33.5, tight=(33.6, 0.8), draw=(34.5, 3.2), carry=(37.7, 1.6), pay=(39.3, 2.2), end=42.5)
HANG = 0.62                                  # the hanging tail's free end, this high over the table while it is carried

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


best = None
spiral = np.arange(300) + 0.5
for z_, ph in zip(1 - spiral / 300, math.pi * (1 + 5 ** 0.5) * spiral):        # nearest to straight up first
    d = np.array([math.sqrt(1 - z_ * z_) * math.cos(ph), math.sqrt(1 - z_ * z_) * math.sin(ph), z_])
    r_ = route(d, 140)
    if nearest(r_[1:], far_w).min() / A >= NEED and nearest(r_[16:], near_w).min() / A >= NEED and nearest(r_[8:], chain[3:]).min() / A >= 2 * TR:
        best = d
        break
assert best is not None, "no clear way out of the cut"
print("the cut end leaves %.0f degrees off straight up" % math.degrees(math.acos(best[2])))
way = route(best, 4000)
path = np.r_[chain[::-1], way[1:]]          # the free end's place first, back along the tail to the cut, then out
s_path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
s0 = arc[::-1] * 0 + (rod - arc)             # each bead's place on the path now: the cut end at rod, the free end at 0
s0 = rod - arc
at = lambda s: np.c_[[np.interp(s, s_path, path[:, k]) for k in range(3)]].T
top_lift = next(u for u in np.arange(0, 6, 0.001) if at(np.array([u]))[0, 2] >= HANG + rod)     # the cut end this high: the free end is at HANG
draw_end = top_lift - rod
held_xy = at(np.array([top_lift]))[0, :2]

# the coil in the next cell, laid from the free end, which lands first
coil, th = [], 0.0
back = bond[::-1]
for i in range(m):
    rad = 0.05 + 2.3 * TR * A * th / (2 * math.pi)
    coil.append((NEXT[0] + rad * math.cos(th), NEXT[1] + rad * math.sin(th), TR * A + 0.002))
    th += back[min(i, m - 2)] / max(rad, 0.05)
coil = np.array(coil)
arc_b = np.r_[0, np.cumsum(back)]


def line(paid):
    """As in tail_path.py, the free end first: the paid-out length lies in the coil, the rest hangs straight up over the bead landing now."""
    if paid < 0:
        return np.c_[np.full(m, coil[0, 0]), np.full(m, coil[0, 1]), coil[0, 2] + arc_b - paid]
    k = min(int(np.searchsorted(arc_b, paid, side="right")) - 1, m - 1)
    p = coil.copy()
    if k < m - 1:
        a_ = (1 - (paid - arc_b[k]) / back[k]) * math.pi / 2
        w = (coil[k + 1] - coil[k]) / np.linalg.norm(coil[k + 1] - coil[k])
        p[k + 1] = coil[k] + back[k] * (math.cos(a_) * w + math.sin(a_) * up)
        p[k + 2:] = p[k + 1] + np.c_[np.zeros(m - k - 2), np.zeros(m - k - 2), arc_b[k + 2:] - arc_b[k + 1]]
    return p


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def tail_at(t):
    """The tube's 44 points, cut end first, at time t on the shot's clock."""
    if t < CUT["carry"][0]:
        u = draw_end * smooth((t - CUT["draw"][0]) / CUT["draw"][1])
        return at(s0 + u)
    hang = at(s0 + draw_end)                 # straight down from the cut end, free end at HANG
    lift = HANG - coil[0, 2]
    if t < CUT["pay"][0]:
        x = smooth((t - CUT["carry"][0]) / CUT["carry"][1])
        over = line(-lift)[::-1]
        return hang + (over - hang) * x + np.array([0, 0, 0.12]) * math.sin(math.pi * x)       # over the gap in a low arc
    return line(-lift + (lift + rod) * smooth((t - CUT["pay"][0]) / CUT["pay"][1]))[::-1]


times = np.arange(CUT["snip"], CUT["end"] + 1e-9, 1 / FPS)
frames = np.array([tail_at(t) for t in times], np.float32)
# checks on every frame: the tube against the kept atoms, against itself and against the table
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
print("bond stretch, worst %.1f%%; fastest bead moves %.1f A a frame" % (100 * stretch, step))
assert gap >= NEED - 0.01 and gap_near >= own_near - 0.05 and self_ >= 2 * TR and low >= 0
np.savez_compressed(HERE + "frames/u_tail.npz", pos=frames, t0=CUT["snip"], picks=np.array(picks), pivot=pivot, tr=TR * A)
print("U_PATH_OK")
