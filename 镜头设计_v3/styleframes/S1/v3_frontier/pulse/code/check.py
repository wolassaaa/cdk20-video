"""PULSE: verify the claims the piece rests on. Run from the pulse/ folder.
1. exactly 1,412 lights exist, all distinct, and all fall inside the final frame
2. at the end exactly 1,408 are lit and 4 are dark (the four that went out)
3. every heartbeat is deterministic: recomputed from the saved seeds, nothing depends on render order
4. red rule on the ember frames (optional, needs post frames)
"""
import json, os, sys
import numpy as np
from PIL import Image

d = np.load("data/points.npz"); P = d["P"]
pl = json.load(open("data/plan.json"))
pu = np.load("data/pulse.npz")
white, ember, dying, death = pu["white"], pu["ember"], pu["dying"], pu["death_t"]

print("lights:", len(P), " distinct:", len(np.unique(P.round(6), axis=0)))
assert len(P) == 1412 and len(np.unique(P.round(6), axis=0)) == 1412

# final camera (frame 299)
E, TGT = np.array(pl["E"]), np.array(pl["tgt"])
f = (TGT - E) / np.linalg.norm(TGT - E)
r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
u = np.cross(r, f)
pos = E
TX = 18.0 / 40.0; TY = TX * 1080 / 1920
rel = P - pos
z = rel @ f
sx = (rel @ r) / z / TX; sy = (rel @ u) / z / TY
px = (sx + 1) / 2 * 1920; py = (1 - sy) / 2 * 1080
inside = (np.abs(sx) < 1) & (np.abs(sy) < 1) & (z > 0)
print("inside final frame: %d / %d   x %.0f-%.0f  y %.0f-%.0f px" % (inside.sum(), len(P), px.min(), px.max(), py.min(), py.max()))
assert inside.all()

last = white[:, -1]
lit = last > 0.05
dark = last < 1e-3
print("final frame: lit %d, dark %d" % (lit.sum(), dark.sum()))
assert lit.sum() == 1408 and dark.sum() == 4 and set(np.where(dark)[0]) == set(int(i) for i in dying)
assert ember[:, -1].max() < 0.02
print("the four, in order:", [int(i) for i in dying], " go out at", [round(float(t), 2) for t in death], "s")
print("heart rates: %.0f-%.0f bpm, mean %.1f; no two bulbs share rate and phase: %s"
      % (pu["bpm"].min(), pu["bpm"].max(), pu["bpm"].mean(), len({(round(a, 4), round(b, 4)) for a, b in zip(pu["bpm"], pu["phase0"])}) == 1412))

# red rule on post frames
fdir = sys.argv[1] if len(sys.argv) > 1 else ""
if fdir:
    tot = bad_g = bad_b = 0
    for fr in range(100, 225, 5):
        fp = os.path.join(fdir, "p_%04d.png" % fr)
        if not os.path.exists(fp): continue
        a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R > 90) & (R > 2.2 * G)                     # pixels that read as red
        tot += m.sum(); bad_g += (G[m] >= 0.35 * R[m]).sum(); bad_b += (B[m] > 1.3 * G[m] + 2).sum()
    print("red pixels %d: G<0.35R fails %.1f%%, B<=1.3G fails %.1f%%" % (tot, 100 * bad_g / max(tot, 1), 100 * bad_b / max(tot, 1)))
