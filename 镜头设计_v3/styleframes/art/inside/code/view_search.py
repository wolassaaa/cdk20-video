"""HKBU SCIE1007 coursework science video. Direction inside: picks the F4 camera so the real tail, residues 303 to 346, stands clear of the body."""
from ilib import *

xyz, name, resi = read_pdb()
ca = xyz[name == "CA"]
c = ca[:302].mean(0)
ca = ca - c
r = np.random.default_rng(3)
best = []
for k in range(6000):
    a = r.uniform(0, 360, 3)
    R = rotm(*a)
    V = ca @ R.T
    core, tail = V[:302], V[302:]
    d = np.sqrt(((tail[:, None, :2] - core[None, :, :2]) ** 2).sum(-1)).min(1)
    free = (d > 6).mean()
    side = (tail[:, 0].mean() - core[:, 0].mean())
    h = V[:, 1].max() - V[:, 1].min()
    s = free + .004 * side - .004 * h + .004 * (tail[:, 2].mean() - core[:, 2].mean())
    best.append((s, free, side, h, *a))
best.sort(reverse=True)
for b in best[:6]:
    print(["%.2f" % x for x in b])
