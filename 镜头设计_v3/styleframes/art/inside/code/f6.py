"""HKBU SCIE1007 coursework science video. Direction inside, F6 (script 6-10): where 048 stands on the road, and what has not been done.
Station 4 is half filled on purpose: first cell tests happened, animals are not reported. Station state is told by fill, not by colour alone. The molecule is the same real 048 as F5."""
from ilib import *

sys.path.insert(0, str(ROOT / "styleframes/S2plus/code"))
import pocket048 as G

XS = [190, 490, 790, 1090, 1400, 1710]
Y = 470
rgb = crowd(seed=13)
rgb = dim(rgb, box(0, 0, W, H, 10), .55)
rgb = dim(rgb, box(0, 250, W, 800, 60), .55)
rgb = road(rgb, XS, Y, ["done", "done", "done", "half", "todo", "todo"], flow_to=1060, x_start=60, x_end=1860, wave=4)

# real 048, the same atoms as F5
S = G.load()
Lg = S["lig"][S["heavy"]].astype(np.float32)
Lg = (Lg - Lg.mean(0)) @ rotm(0, 0, 62).T
SC, MX, MY = 14.5, 800, 668
Z, N, I = spheres(Lg, np.full(len(Lg), 1.55, np.float32), SC, MX, MY)
m = I >= 0
LI = np.array([-.4, .55, .73], np.float32)
lam = np.clip(N @ LI, 0, 1)
c = RED * (.74 + .34 * lam[..., None])
e = edges(Z, I, np.ones(len(Lg) + 1, np.int32), jump=1.0, grow=3)
c = np.where(e[..., None], BONE, c)
e2 = edges(Z, I, np.arange(len(Lg) + 1, dtype=np.int32), jump=.6, grow=1)
c = np.where(e2[..., None] & ~e[..., None], DEEP, c)
a = down(m.astype(np.float32))[..., None]
rgb = rgb * (1 - a) + down(np.where(m[..., None], c, 0))
im = to_pil(rgb)

yw = lambda x: Y + 4 * np.sin((x - XS[0]) / 140)
for x, s in zip(XS[:4], ["Target", "Hit", "Improve", "Cells & animals"]):
    text(im, (x, yw(x) - 60), s, sans(42, 600), anchor="ms")
x = XS[4]
text(im, (x, yw(x) - 110), "Clinical trials", sans(42, 600), anchor="ms")
text(im, (x, yw(x) - 60), "1-2-3", sans(42, 600), anchor="ms")
text(im, (XS[5], yw(XS[5]) - 60), "Approval", sans(42, 600), anchor="ms")

for x in XS[4:]:
    text(im, (x, yw(x) + 56), "not reported", sans(38), anchor="ma")

x = XS[3]
leader(im, (x, yw(x) + 44), (x, 556), dot=False, width=4, col=RED)
text(im, (x, 640), "048", sans(128, 600), fill=RED, anchor="mm")
text(im, (x + 170, 720), "cells: first tests", sans(40, 600), anchor="ls")
text(im, (x + 170, 776), "animals: not reported", sans(40, 600), anchor="ls")
tag(im, (96, 968), "schematic", "schematic", size=30, bg=NIGHT)
save(im, "F6.png")
