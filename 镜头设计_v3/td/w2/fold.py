"""HKBU SCIE1007 coursework science video. W2 in TouchDesigner: the 346 beads of the CDK20 model pull together from a loose string and land exactly on the AlphaFold DB v6 coordinates. Writes pos.npy, col.npy and light.npy for TouchDesigner.

The end shape and the confidence colours are real. The folding path is a picture: AlphaFold does not simulate folding.
The music is not in the project yet, so LOCK is a guess. Set it to the first big chord of Emerald Rush when the track arrives.
Run: python fold.py
"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PDB = os.path.join(HERE, "..", "..", "assets", "alphafold", "AF-Q8IZL9-F1-model_v6.pdb")
FPS, SECONDS = 60, 25
LOCK = 18.5
FOLD = (5.0, 16.7)           # local shapes form first, the whole chain closes last
PX = 14.0                    # pixels per angstrom at 1080p
SUB = 12
DT = 0.04
LINKS = 3                    # small beads between two residues, so it reads as one string
BONE, INK = np.array([237, 235, 228]) / 255, np.array([17, 17, 19]) / 255
KLEIN, RED = np.array([0, 47, 167]) / 255, np.array([232, 25, 15]) / 255


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def kabsch(a, b):
    """The rotation r that best lays centred a onto centred b, as a @ r."""
    u, _, vt = np.linalg.svd(a.T @ b)
    d = np.sign(np.linalg.det(u @ vt))
    return u @ np.diag([1, 1, d]) @ vt


ca = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54]), float(l[60:66])] for l in open(PDB) if l.startswith("ATOM") and l[12:16].strip() == "CA"])
native, plddt = ca[:, :3] - ca[:, :3].mean(0), ca[:, 3]
N = len(native)

rng = np.random.default_rng(1007)
v = np.zeros((N, 3))
v[0] = (1, 0, 0)
for i in range(1, N):
    v[i] = 0.93 * v[i - 1] + 0.3 * rng.normal(size=3)
    v[i] /= np.linalg.norm(v[i])
x = np.cumsum(v * 3.8, axis=0)
x -= x.mean(0)

d0 = np.linalg.norm(native[:, None] - native[None], axis=2)
sep = np.abs(np.arange(N)[:, None] - np.arange(N)[None]).astype(float)
contact = ((d0 < 10) & (sep >= 3)) * 1.2
order = np.log(np.maximum(sep, 1)) / math.log(N)
bond = (sep == 1) * 8.0
near = (sep == 2) * 2.0
free = sep >= 2
total = int(LOCK * FPS)
path = np.zeros((total, N, 3))
for f in range(total):
    s = float(np.clip((f / FPS - FOLD[0]) / (FOLD[1] - FOLD[0]), 0, 1))
    w = bond + near * min(1, s * 4) + contact * ease((s - order * 0.75) / 0.25)
    pull = 0.6 * float(ease((s - 0.6) / 0.4))
    for _ in range(SUB):
        diff = x[:, None] - x[None]
        d = np.linalg.norm(diff, axis=2) + np.eye(N)
        mag = np.clip(w * (d - d0), -3, 3) - 5 * np.clip(4.2 - d, 0, None) * free
        force = -((mag / d)[..., None] * diff).sum(1)
        c = x.mean(0)
        target = native @ kabsch(native, x - c) + c
        x = x + DT * (force + pull * (target - x)) + rng.normal(0, 0.05 * (1 - s) * math.sqrt(DT), x.shape)
    path[f] = x - x.mean(0)
print("fold end, distance from the real shape %.2f A" % float(np.sqrt(((path[-1] - native @ kabsch(native, path[-1])) ** 2).sum(1).mean())))

end_rot = kabsch(native, path[-1])
_, _, axes = np.linalg.svd(native)  # long axis across the screen
if np.linalg.det(axes) < 0:
    axes[2] *= -1
view = axes.T                        # as native @ view
path = path @ end_rot.T @ view

frames = FPS * SECONDS
trace = np.zeros((frames, N, 3))
k = np.exp(-0.5 * (np.arange(-14, 15) / 4.0) ** 2)
k /= k.sum()
padded = np.concatenate([np.repeat(path[:1], 14, 0), path, np.repeat(path[-1:], 14, 0)])
smooth = sum(k[j] * padded[j:j + total] for j in range(29))
final = native @ view
blend = ease((np.arange(total) / FPS - (LOCK - 1.2)) / 1.2)[:, None, None]
trace[:total] = smooth * (1 - blend) + final * blend
trace[total:] = final

t = np.arange(frames) / FPS
rate = 11 - 9.5 * ease((t - (LOCK - 1.6)) / 1.6)
yaw = np.radians(np.cumsum(rate) / FPS)
yaw -= yaw[total]                    # the chosen view lands on the lock
c, s = np.cos(yaw), np.sin(yaw)
px = np.stack([trace[..., 0] * c[:, None] + trace[..., 2] * s[:, None], trace[..., 1], -trace[..., 0] * s[:, None] + trace[..., 2] * c[:, None]], axis=2) * PX

M = N + LINKS * (N - 1)
pos = np.zeros((frames, M, 4), np.float32)
idx = np.arange(M) / (LINKS + 1)
lo = np.minimum(idx.astype(int), N - 2)
u = (idx - lo)[None, :, None]
a, b = px[:, lo], px[:, lo + 1]
before, after = px[:, np.maximum(lo - 1, 0)], px[:, np.minimum(lo + 2, N - 1)]
pos[..., :3] = 0.5 * (2 * a + (b - before) * u + (2 * before - 5 * a + 4 * b - after) * u * u + (3 * a - 3 * b + after - before) * u ** 3)
big = np.arange(M) % (LINKS + 1) == 0
order01 = np.arange(M) / (M - 1)
appear = ease((t[:, None] - 0.3 - 3.6 * order01[None]) / 0.5)
pulse = 1 + 0.16 * np.exp(-(((t[:, None] - LOCK - 0.9 * order01[None]) / 0.22) ** 2))
pos[..., 3] = np.where(big, 1.15, 0.42) * PX * appear * pulse

edge = 280.0
radius = (1100 + edge + 40) * ease((t - (LOCK - 0.7)) / 3.4) ** 1.4
dist = np.linalg.norm(pos[..., :2], axis=2)
inside = ease((radius[:, None] - dist) / edge)[..., None]
sure = np.where(plddt[np.minimum(np.rint(idx).astype(int), N - 1)] < 70, 1.0, 0.0)[None, :, None]
conf = KLEIN + (RED - KLEIN) * sure
wave = ease((t[:, None] - LOCK - 0.1 - 0.9 * order01[None]) / 0.5)[..., None]
lit = INK + (conf - INK) * wave
col = np.ones((frames, M, 4), np.float32)
col[..., :3] = BONE + (lit - BONE) * inside

np.save(os.path.join(HERE, "pos.npy"), pos)
np.save(os.path.join(HERE, "col.npy"), col)
np.save(os.path.join(HERE, "light.npy"), radius.astype(np.float32))
print("frames", frames, "instances", M, "low-confidence residues", int((plddt < 70).sum()), "screen reach", float(np.abs(pos[total:, :, :2]).max()))
