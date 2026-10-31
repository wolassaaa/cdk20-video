"""HKBU SCIE1007 coursework science video. Art direction `hot`, frame T3 (3-08): the darkest moment. A lock nobody can see, only the empty keyhole.

Not required for round two; drawn with T1 to show the quiet end of the palette. Pure black, the keyhole is a stepped dashed outline, because a dashed outline is what schematic means in this film.
"""
from hot_kit import *

rgb = field(hx("#040405"))
CX, CY = 960, 470
# keyhole built on the same pixel step as every other edge in the film
s = 26
rows = [(-3, 2), (-2, 3), (-1, 4), (0, 4), (1, 4), (2, 4), (3, 3), (4, 2), (5, 2), (6, 2), (7, 3), (8, 3), (9, 4), (10, 4), (11, 4)]
ma = np.zeros((H, W), np.float32)
for r, w_ in rows:
    ma[CY + (r - 4) * s:CY + (r - 3) * s, CX - w_ * s:CX + w_ * s] = 1
er = np.zeros_like(ma)
er[4:-4, 4:-4] = ma[4:-4, 4:-4] * ma[8:, 4:-4] * ma[:-8, 4:-4] * ma[4:-4, 8:] * ma[4:-4, :-8]
line = np.clip(ma - er, 0, 1)
ang = np.arctan2(yy - CY, xx - CX)
dash = ((xx + yy).astype(np.int32) % 34 < 21).astype(np.float32)
rgb = comp(rgb, line * dash, hx("#6E6C64"))

f = mono(36, 700, 75)
rgb = comp(rgb, place(sprite("no one had measured CDK20's shape", f, pad=0), 56, 978), hx("#BDBAB0"))
t = sprite("schematic", f, pad=0)
x0 = W - 56 - t.width - 44
rgb = comp(rgb, dashed_rect(x0, 958, W - 56, 958 + 74, t=3, on=14, off=10), hx("#BDBAB0"))
rgb = comp(rgb, place(t, x0 + 22, 978), hx("#BDBAB0"))
save(rgb, "T3.png")
