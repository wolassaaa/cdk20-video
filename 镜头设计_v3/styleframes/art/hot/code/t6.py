"""HKBU SCIE1007 coursework science video. Art direction `hot`, frame T6 (6-10): the road map, used 12 times in the film, as a staircase of blocks.

Six stations, six rising blocks. The first three are lit and the same real CDK20 surface runs through them; the light stops at the door of the fourth.
The last three are dashed outlines marked `not reported`. The right side stays empty on purpose: nothing has been reported there.
"""
from hot_kit import *

BAND = 930
CW = 320
TOPS = [790, 650, 510, 370, 230, 90]
NAMES = [("Target",), ("Hit",), ("Improve",), ("Cells &", "animals"), ("Clinical trials", "1-2-3"), ("Approval",)]

rgb = field(B)
rgb = comp(rgb, rect(960, 0, W, H), K)

ROT, SC, CX, CY = (0, -30, 90), 13.5, 470, 700
V = surface(ROT, SC, CX, CY, ss=1.0)
m = edge(V)
low = blur(((V["conf"] < 0.7) & (V["mask"] > 0.5)).astype(np.float32), 1.0)[..., None]
hero = r_toon(V, K, M, P, B) * (1 - low) + r_toon(V, K, B, P, M) * low
tex = [(r_half(V, P, K, pitch=11), P), (r_contour(V, M, K, width=2.2), M), (hero, Y)]

# giant number on the field, pushed against the door
sp = stepped(fit("048", 900, 400), 10)
rgb = comp(rgb, place(sp, 30, 44), Y)

for i in range(3):
    x0, x1 = i * CW, (i + 1) * CW
    p = rect(x0, TOPS[i], x1, BAND)
    rgb = comp(rgb, p, tex[i][1])
    rgb = comp(rgb, p * m, tex[i][0])
    rgb = comp(rgb, rect(x0 - 2, TOPS[i], x0 + 2, BAND), K)
    rgb = comp(rgb, rect(x0, TOPS[i], x1, TOPS[i] + 5), K)

# the light reaches the door and stops: a stepped spill on the floor of station 4
door = 960
rgb = comp(rgb, rect(door, TOPS[3], door + 14, BAND), Y)
sp_pts = [(door + 14, BAND), (door + 14, BAND - 150), (door + 64, BAND - 150), (door + 64, BAND - 100), (door + 114, BAND - 100), (door + 114, BAND - 50), (door + 164, BAND - 50), (door + 164, BAND)]
rgb = comp(rgb, poly(sp_pts), Y)

# dashed blocks: nothing reported yet
fn = mono(36, 700, 75)
for i in range(3, 6):
    x0, x1 = i * CW + (22 if i == 3 else 8), (i + 1) * CW - 8
    rgb = comp(rgb, dashed_rect(x0, TOPS[i], x1, BAND - 6, t=5), P)
    if i == 3:      # the narration at 6-10 says first cell tests were done; awaiting the director's confirmation
        for k, (ln, col) in enumerate([("cells:", Y), ("first tests", Y), ("animals:", P), ("not reported", P)]):
            rgb = comp(rgb, place(sprite(ln, fn, pad=0), x0 + 14, TOPS[i] + 30 + k * 62 + (26 if k > 1 else 0)), col)
        continue
    t = sprite("not reported", fn, pad=0)
    tx = x0 + (x1 - x0 - t.width) // 2
    ty = TOPS[i] + 30
    rgb = comp(rgb, place(t, tx, ty), P)

# the known side is dense with real data, the unknown side stays empty
s = plddt()
for i, c in enumerate(s):
    x = 30 + i * 2.6
    h_ = int(8 + 34 * float(c))
    rgb[492 - h_:492, int(x):int(x) + 2] = Y if c >= 0.7 else M
ft = mono(15, 700, 75)
for k in range(4):
    a = SEQ[k * 58:(k + 1) * 58]
    rgb = comp(rgb, place(sprite(a, ft, pad=0), 30, 506 + k * 22), P)

# bottom band: the six station names
rgb = comp(rgb, rect(0, BAND, W, H), K)
f = black(46)
fs = black(38)
for i, nm in enumerate(NAMES):
    lit = i < 3
    col = Y if lit else P
    if len(nm) == 1:
        rgb = comp(rgb, place(sprite(nm[0], f, pad=0), i * CW + 26, BAND + 46), col)
    else:
        rgb = comp(rgb, place(sprite(nm[0], fs, pad=0), i * CW + 26, BAND + 22), col)
        rgb = comp(rgb, place(sprite(nm[1], fs, pad=0), i * CW + 26, BAND + 78), col)
    if i:
        rgb = comp(rgb, rect(i * CW - 2, BAND, i * CW + 2, H), P if lit else P * 0.45)

rgb = cross(rgb, [(320, BAND), (640, BAND), (960, BAND)], P)
save(rgb, "T6.png")
