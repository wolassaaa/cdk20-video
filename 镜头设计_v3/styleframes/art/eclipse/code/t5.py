"""HKBU SCIE1007 coursework science video. Eclipse direction, T5: the key turns. A raw red wall carries the measured number in black, the real pocket sits inside the shadow, and 048 from our re-docking is the first thing in the dark that burns."""
from ec import *

y, x = grid()
S2 = ART.parent / "S2plus/public"
rng = np.random.default_rng(2)

# red wall, the same pigment as the first scout, as a band position
grain = noise(5, 8, slope=0.6)
drift = noise(6, 420, slope=2.2)
wall = 0.475 + 0.03 * (drift - 0.5) + 0.012 * (grain - 0.5) - 0.05 * (x / W)

# the shadow: the real outline at huge scale comes in from the right and swallows half the frame
cache = WORK / "t5_view.npz"
SCALE = 26.0
if cache.exists():
    V = dict(np.load(cache))
else:
    R = kit.rot(0, 0, 96) @ kit.base_view()
    V = kit.view(R=R, scale=SCALE, cx=1730, cy=540, w=W, h=H, ss=0.45)
    np.savez(cache, **{k: v for k, v in V.items() if isinstance(v, np.ndarray)})
hard = sstep(0.4, 0.6, blur(V["mask"], 3.5))
hard = np.maximum(hard, sstep(1380, 1440, x))  # no wall showing behind the pocket
lip = blur(hard, 70)
reach = 1 - sstep(0.60, 0.97, lip)
n3 = V["normal"]
ld = np.array([-0.75, 0.35, 0.56], np.float32)
ld /= np.linalg.norm(ld)
lam = np.clip((n3 * ld).sum(-1), 0, 1) ** 1.5
limb = np.clip(0.03 + 0.46 * lam * (0.3 + 0.7 * V["ao"]), 0, 0.56) * reach ** 1.1
t = wall * (1 - hard) + limb * hard
ai = hard.copy()                    # everything on the mass is on the pearl rail, the red wall stays warm

# light getting through the real valleys of the outline: pearl, the machine's colour
valley = (1 - hard) * sstep(0.56, 0.66, blur(hard, 30)) * sstep(120, 200, y) * sstep(1040, 960, y)
print("valley px", float(valley.sum()))
glow = blur(valley, 3) * 1.0 + blur(valley, 14) * 1.4 + blur(valley, 46) * 1.1
g_ = np.clip(glow * (1 - hard * 0.5), 0, 1)
t = np.clip(t + valley * 0.6 + g_ * 0.42, 0, 1)
ai = np.maximum(ai, np.clip(valley + g_ * 1.6, 0, 1))

# pocket: our surface and 048, placed at the real pocket's own position in this view, recoloured without touching the structure
RP = kit.rot(0, 0, 96)[:2, :2] @ np.array([0.73, -0.19])
px_, py_ = 1730 + RP[0] * SCALE, 540 - RP[1] * SCALE
print("pocket", px_, py_)
grey = np.asarray(Image.open(S2 / "pose_048_grey.png").convert("RGBA"), np.float32) / 255
lig = np.asarray(Image.open(S2 / "pose_048_lig.png").convert("RGBA").resize((1920, 2160), Image.LANCZOS), np.float32) / 255
PS = 0.46                     # pose frame to screen scale
sx = (x - px_) / PS + 1037    # 1037, 850 is the middle of 048 in the pose frame
sy = (y - py_) / PS + 850
ga = sample(grey[..., 3], sx, sy)
gl = sample(grey[..., 0], sx, sy)
la = sample(lig[..., 3], sx, sy)
ll = sample(lig[..., 0], sx, sy)
ga = ga * sstep(0.05, 0.5, hard)
pocket = (0.04 + 0.46 * gl ** 1.1)
tp = t * (1 - ga) + pocket * ga
hot = np.clip(blur(la, 4) * 0.6 + blur(la, 18) * 0.8 + blur(la, 55) * 0.6, 0, 1)
tp = np.clip(tp + hot * 0.30 * hard, 0, 1)
tp = put(tp, la, 0.78 + 0.22 * ll)
t = tp
ai = np.maximum(ai, la)

# type on the wall, absolute black. The measured plate is black with the wall showing through its letters
INK = 0.0
t = put(t, text("Enzyme IC50", 58, (84, 176), 700), INK)
t = put(t, text("048 =", 112, (80, 300), 900), INK)
t = put(t, text("33.4 ± 22.6 nM", 122, (78, 462), 900), INK)
t = put(t, text("Just this much cuts the enzyme's", 46, (84, 610), 500), INK)
t = put(t, text("activity in half.", 46, (84, 672), 500), INK)
t = tag(t, x, y, "measured", "MEASURED · Ren 2023, Fig. 9A", 84, 800, size=40, weight=700, ink=0.0, ground=0.47)
t = tag(t, x, y, "docked", "OUR RE-DOCKING", 1270, 980, size=40, weight=700, ink=0.93, ground=0.0)
ai = np.maximum(ai, tag_box(x, y, "OUR RE-DOCKING", 1270, 980, 40, 700))
save(t, "T5.png", ai)
