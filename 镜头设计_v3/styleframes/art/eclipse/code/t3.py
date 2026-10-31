"""HKBU SCIE1007 coursework science video. Eclipse direction, T3: totality, the darkest moment of the film. Pure black, one empty keyhole cut from the last red of the sky. Schematic, not the real structure."""
from ec import *

y, x = grid()
cx, cy, Rr = 960, 470, 372

# the last of the light: a barely-there ring, the corona at its faintest
r = np.hypot(x - cx, y - cy)
th = np.arctan2(y - cy, x - cx)
n = 2048
s1 = noise(61, 340, (8, n), 1.4)[3]
s2 = noise(62, 90, (8, n), 1.1)[5]
idx = ((th + np.pi) / (2 * np.pi) * n).astype(np.int32) % n
st = (0.7 * s1 + 0.3 * s2)[idx]
st = sstep(0.2, 0.85, (st - st.min()) / (st.max() - st.min()))
out = np.maximum(r - Rr, 0)
L = 0.26 * np.exp(-out / 34) * (0.6 + 0.4 * st) + 0.12 * np.exp(-out / (70 + 170 * st)) * st
t = expose(L, 1.0) * (r > Rr)

# empty keyhole: the only thing in the disc. A plain drawn shape, a metaphor, hatched so it reads as schematic
head = np.hypot(x - cx, y - (cy - 72)) < 62
u = (y - (cy - 40)) / 196
stem = (u > 0) & (u < 1) & (np.abs(x - cx) < 30 + 34 * u)
hole = np.maximum(head, stem).astype(np.float32)
hole = blur(hole, 0.8)
hatch = ((np.floor((x + y) / 7) % 2) == 0)
edge = np.clip(blur(hole, 2) * (1 - blur(hole, 2)) * 4, 0, 1)
t = put(t, hole * hatch, 0.22)
t = put(t, sstep(0.72, 0.95, edge), 0.36)

t = put(t, text("no one had measured CDK20's shape", 46, (960, 934), 500, "mm"), 0.48)
tw = width("schematic", 38, 500)
x0 = 960 - (tw + 48 + 2 * 17 + 18) / 2
t = tag(t, x, y, "schematic", "schematic", x0, 1010, size=38, weight=500, ink=0.46)
(WORK / "m").mkdir(exist_ok=True)
np.save(WORK / "m/t3.npy", t.astype(np.float32))
save(t, "T3.png")
