"""HKBU SCIE1007 coursework science video. Direction inside, F5 (script 5-08): 048 against 001, measured.
Bars share one true linear scale. 001 is only known as a lower bound, so its bar has no end and runs out of frame. The slice shows our re-docked 048 in the pocket of the real AlphaFold model, cut on real atoms."""
from ilib import *

sys.path.insert(0, str(ROOT / "styleframes/S2plus/code"))
import pocket048 as G

S = G.load()
Lg, heavy = S["lig"], S["heavy"]
rec, rad = S["rec"].astype(np.float32), S["rad"].astype(np.float32)
cut = G.cut_z(S)
near = np.sqrt(((rec[:, None] - Lg[heavy][None]) ** 2).sum(-1)).min(1) < 34
rec, rad = rec[near], rad[near]

CX, CY, SC, RAD = 1500, 305, 17.0, 268     # the slice sits in a round window, centre, px per Angstrom, window radius
cl = Lg[heavy].mean(0)
ox, oy = CX - cl[0] * SC, CY + cl[1] * SC

rgb = crowd(seed=11)
rgb = dim(rgb, box(0, 0, W, H, 10), .5)
rgb = dim(rgb, box(0, 560, W, H, 40), .92)
rgb = dim(rgb, disc(CX, CY, RAD + 40, 30), .8)

Z, N, I = spheres(rec, rad * 1.28, SC, ox, oy, clip=cut)   # heavy atoms only, so 1.28 x radius stands in for the missing hydrogens and closes the cut face
nr = len(rec)
Ll = Lg[heavy]
Zl, Nl, Il = spheres(Ll, np.full(len(Ll), 1.55, np.float32), SC, ox, oy)
m = I >= 0
flat = m & (Z >= cut - .01)
L = np.array([-.4, .55, .73], np.float32)
lam = np.clip(N @ L, 0, 1)
dep = np.clip((cut - Z) / 9, 0, 1)
base = np.where(flat[..., None], BONE, BONE * (.60 - .48 * dep[..., None]) + KLEIN * (.30 * dep[..., None]))
base = base * np.where(flat, 1, .80 + .30 * lam)[..., None]
e = edges(Z, I, np.arange(nr + 1, dtype=np.int32), jump=1.2, grow=1)
base = np.where(e[..., None], base * np.where(flat, .55, .45)[..., None], base)
e2 = edges(Z, I, np.ones(nr + 1, np.int32), jump=1.2, grow=2)
base = np.where(e2[..., None], BLACK, base)
ground = KLEIN * .22
c = np.where(m[..., None], base, ground)
# 048 on top of the slice, full atoms, one colour
ml = Il >= 0
lamL = np.clip(Nl @ L, 0, 1)
cL = RED * (.74 + .34 * lamL[..., None])
eL = edges(Zl, Il, np.ones(len(Ll) + 1, np.int32), jump=1.0, grow=3)
cL = np.where(eL[..., None], BONE, cL)
eL2 = edges(Zl, Il, np.arange(len(Ll) + 1, dtype=np.int32), jump=.6, grow=1)
cL = np.where(eL2[..., None] & ~eL[..., None], DEEP, cL)
c = np.where(ml[..., None], cL, c)
c = down(c)
win = disc(CX, CY, RAD, 1)
rgb = rgb * (1 - win[..., None]) + c * win[..., None]
ring = disc(CX, CY, RAD + 5, 1) - win
rgb = rgb * (1 - ring[..., None]) + BONE * ring[..., None]

# bars: one true linear scale
X0, X6K = 96, 1656
PX = (X6K - X0) / 6000
Y1, Y2, BH = 640, 760, 92
d_rgb = rgb.copy()
im = to_pil(d_rgb)
d = ImageDraw.Draw(im)
d.rectangle((X0, Y1, X6K, Y1 + BH), fill=rgb8(BONE))                 # solid up to the lower bound
d.rectangle((X6K, Y1, W + 20, Y1 + 5), fill=rgb8(BONE))              # past it only open rails, running out of frame: never capped
d.rectangle((X6K, Y1 + BH - 5, W + 20, Y1 + BH), fill=rgb8(BONE))
for k in range(3):                                                   # chevrons say it keeps going
    x = X6K + 44 + k * 70
    d.line([(x, Y1 + 20), (x + 26, Y1 + BH / 2), (x, Y1 + BH - 20)], fill=rgb8(BONE), width=9, joint="curve")
text(im, (X0 + 24, Y1 + BH / 2), "001 > 6,000 nM", sans(56, 600), fill=BLACK, anchor="lm")

w48 = 33.4 * PX
lo, hi = (33.4 - 22.6) * PX, (33.4 + 22.6) * PX
d.rectangle((X0, Y2, X0 + w48, Y2 + BH), fill=rgb8(RED))
yc = Y2 + BH / 2
d.line([(X0 + lo, yc), (X0 + hi, yc)], fill=rgb8(BONE), width=4)
for xx_ in (X0 + lo, X0 + hi):
    d.line([(xx_, yc - 22), (xx_, yc + 22)], fill=rgb8(BONE), width=4)
print("px per nM", PX, "048 bar", w48, "whisker", lo, hi)
text(im, (X0 + 52, yc), "048 = 33.4 ± 22.6 nM", sans(84, 600), fill=BONE, anchor="lm")

text(im, (X0, 556), "Enzyme IC50", sans(56, 600))
text(im, (X0, 884), "Just this much cuts the enzyme's activity in half.", sans(52, 500))
d.line([(X0 + 4, 888), (X0 + 4, Y2 + BH)], fill=rgb8(RED), width=4)
tag(im, (X0, 968), "MEASURED · Ren 2023, Fig. 9A", "measured", size=30)

# what the slice is
rx = CX - RAD - 44
text(im, (rx, 96), "CDK20", sans(60, 600), anchor="ra")
text(im, (rx, 176), "048", sans(60, 600), fill=RED, anchor="ra")
leader(im, (rx + 8, 214), (CX - 30, 300), col=BONE, case=BLACK)
tag(im, (rx, 290), "OUR RE-DOCKING", "ours", size=30, bg=NIGHT, anchor="r")
bx, by = rx - 10 * SC, 440
d.rectangle((bx, by, bx + 10 * SC, by + 8), fill=rgb8(BONE))
text(im, (bx - 20, by + 4), "1 nm", sans(36), anchor="rm")
tag(im, (96, 72), "schematic", "schematic", size=30, bg=NIGHT)
save(im, "F5.png")
