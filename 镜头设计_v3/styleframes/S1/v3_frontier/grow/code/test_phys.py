import numpy as np, os, sys, time
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from physarum import Physarum
from flicker import hf

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work")
d = np.load(os.path.join(WORK, "liver_proj.npz")); t = np.load(os.path.join(WORK, "tree.npz"))
X0, Y0, CW, CH = 300, 56, 1152, 848
mask = d["mask"][Y0:Y0 + CH, X0:X0 + CW]
P, par, leaves = t["P"] - np.array([X0, Y0]), t["parent"], t["leaves"]
im = Image.new("F", (CW, CH), 0); dr = ImageDraw.Draw(im)
for i in range(1, len(P)):
    w = 0.42 * leaves[i] ** (1 / 2.2)
    dr.line([tuple(P[par[i]]), tuple(P[i])], fill=float(min(1.0, 0.3 + w / 3)), width=max(1, int(round(w))))
food = np.asarray(im, np.float32)

N = int(float(sys.argv[1])) if len(sys.argv) > 1 else 600000
SO = float(sys.argv[2]) if len(sys.argv) > 2 else 9
DEC = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
FG = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
tag = sys.argv[5] if len(sys.argv) > 5 else "a"
ph = Physarum(mask > 0.5, SO=SO, DECAY=DEC, DIFF=float(os.environ.get("DIFF", 1.0)), SA=float(os.environ.get("SA", 22.5)), RA=float(os.environ.get("RA", 45)))
rng = np.random.default_rng(3)
ys, xs = np.nonzero(mask > 0.5)
k = rng.integers(0, len(xs), N)
ph.spawn(xs[k] + rng.random(N), ys[k] + rng.random(N))
t0 = time.time()
disp = None
frames = []
NST = int(os.environ.get("NST", 420))
for st in range(NST):
    ph.step(food, FG)
    if st % 2 == 1:
        disp = ph.T.copy() if disp is None else disp * 0.75 + ph.T * 0.25
        if st >= NST - 20:
            frames.append(disp.copy())
print(f"{(time.time()-t0)/NST*1000:.0f} ms/step  agents {N}")
T = frames[-1]
k = np.percentile(T[mask > 0.5], 90)
def tone(T):
    v = 1 - np.exp(-T / k)
    rgb = np.stack([v * 232, v * 25, v * 15], -1) * 0.8 + 6
    return np.clip(rgb, 0, 255).astype(np.uint8)
Image.fromarray(tone(T)).save(os.path.join(WORK, f"phys_{tag}.png"))
print('k', k, 'Tmax', T.max()); Image.fromarray(tone(T)[200:500, 300:750]).save(os.path.join(WORK, f"phys_{tag}_crop.png"))
vals = [hf(tone(frames[i]), tone(frames[i + 1])) for i in range(len(frames) - 1)]
print("flicker HF mean (EMA display)", np.mean(vals))
