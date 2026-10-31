"""HKBU SCIE1007 coursework science video. manual T6: the road map is a fold-out sheet pulled from the booklet. Six accordion panels on the desk: printed solid up to the third, 048 clipped at the fold in front of the fourth, the last three still dashed pencil and unread runes."""
from mk import *

C = CH[6]
S = 2
OW, OH = FW * S, FH * S
Y, X = np.mgrid[0:OH, 0:OW].astype(np.float32)
LIT = ["Target", "Hit", "Improve"]
OPEN = [("Cells &", "animals"), ("Clinical trials", "1-2-3"), ("Approval", "")]
PW, PHh = 620, 1180  # flat panel at 2x of on-screen 310 x 590
FOREST, MINT, CREAM = hexc("#163c30"), hexc("#3f8a6a"), hexc("#f0ecd8")


KCY, KR, KB0, KB1, KBY = 590, 96, 40, 104, 846  # one keyhole shape for every station, same as chapter five


def keyhole_pts(n=70):
    cx = PW / 2
    th0 = np.arcsin(0.72)
    th = np.linspace(np.pi / 2 + 0.72, 2.5 * np.pi - 0.72, n)
    p = [(cx + KR * np.cos(t), KCY + KR * np.sin(t)) for t in th]
    return [(cx + KB1, KBY), (cx - KB1, KBY)] + p + [(cx + KB1, KBY)]


panels = []
for k in range(6):
    done = k < 3
    PA = "#dbe6cc" if done else "#16322c"
    FG = "#163c30" if done else "#f2f8ea"
    p = paper(PA, 60 + k, w=PW, h=PHh, mott=0.05)
    Hl = Mask(PW, PHh, 1)
    Hl.poly(keyhole_pts())
    hole = Hl.a()
    Rd = Mask(PW, PHh, 1)
    if done:
        Rd.rect(0, KCY - 17, PW, KCY + 17)
        p = ink(p, Rd.a(), FG)
        # punched clean through: the saffron sheet underneath shows, the only hot colour here
        under = paper("#f6b414", 80 + k, w=PW, h=PHh)
        shd = np.clip(np.roll(np.roll(gauss(1 - hole, 7), 10, 0), 8, 1), 0, 1)
        under *= 1 - 0.6 * shd[..., None]
        p = p * (1 - hole[..., None]) + under * hole[..., None]
        Lp = Mask(PW, PHh, 1)
        Lp.line(keyhole_pts(), 5.0)
        p = ink(p, Lp.a(), FG)
        Nm = Mask(PW, PHh, 1)
        Nm.text((PW / 2, 182), LIT[k], serif(100, 900), "ms")
        p = ink(p, Nm.a(), FG)
    else:
        Dd = Mask(PW, PHh, 1)
        Dd.dash([(0, KCY), (PW, KCY)], 6.0, 26, 22, 0.6, 30 + k)
        Dd.dash(keyhole_pts(), 5.0, 18, 13, 0.6, 40 + k)
        p = ink(p, Dd.a(), FG)
        # still uncut, so the road behind it stays a guide. Clear the middle of the dashed road inside the shape
        l1, l2 = OPEN[k - 3]
        M = Mask(PW, PHh, 1)
        fs = 80
        M.text((PW / 2, 150 if l2 else 182), l1, serif(fs, 800), "ms")
        if l2:
            M.text((PW / 2, 246), l2, serif(fs, 800), "ms")
        p = ink(p, M.a(), FG)
        Nr = Mask(PW, PHh, 1)
        fn = sans(80, 500)
        if k == 3:
            # cells: the script says the first tests were done, so a thin solid frame. animals: dashed, same as the stations ahead
            bx0, by0, bx1, by1 = 40, 300, PW - 40, 462
            Nr.line([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 4.4)
            Nr.text((PW / 2, 372), "cells:", fn, "ms")
            Nr.text((PW / 2, 444), "first tests", fn, "ms")
            bx0, by0, bx1, by1 = 40, 900, PW - 40, 1062
            Nr.dash([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 4.4, 18, 13, 0.6, 50 + k)
            Nr.text((PW / 2, 972), "animals:", fn, "ms")
            Nr.text((PW / 2, 1044), "not reported", fn, "ms")
            p = ink(p, Nr.a(), FG)
        else:
            bx0, by0, bx1, by1 = 56, 322, PW - 56, 440
            Nr.dash([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 4.4, 18, 13, 0.6, 50 + k)
            Nr.text((PW / 2, 406), "not reported", sans(82, 500), "ms")
            p = ink(p, Nr.a(), FG)
            Lb = Mask(PW, PHh, 1)
            Lb.runes(52, 900, PW - 110, 6, 150 + k * 50, 15, 22, 7, 44, 2.6)
            p = ink(p, Lb.a() * 0.8, "#9fbcae")
    panels.append(p)


def homog(src, dst):
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    h = np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64))
    return np.array([[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1]])


# Desk and the book the sheet comes out of
desk = np.ones((OH, OW, 3), np.float32) * hexc("#141216")
wood = np.asarray(Image.fromarray(fbm(OH // 2, OW // 2, 220, 3, 2)).resize((OW, OH), Image.BICUBIC), np.float32)
desk *= (0.75 + 0.6 * wood[..., None])

# The accordion: fold lines alternate near the camera and away from it
x0, x1 = 176.0, 1880.0
n = 6
xs = np.linspace(x0, x1, n + 1)
xs[1:] -= 2
top0, bot0 = 256.0, 960.0
amp = 40.0
tilt_y = np.linspace(0, -46, n + 1)  # the sheet runs slightly uphill to the right
tops = [top0 + (amp if i % 2 else -amp * 0.6) + tilt_y[i] for i in range(n + 1)]
bots = [bot0 - (amp if i % 2 else -amp * 0.6) + tilt_y[i] for i in range(n + 1)]

# shadow of the strip on the desk: a zig-zag, longer under the valley folds
Sh = Mask(FW, FH, 2)
sp_ = []
for i in range(n + 1):
    sp_.append((xs[i] + 22, bots[i] + (26 if i % 2 == 0 else 62)))
for i in range(n, -1, -1):
    sp_.append((xs[i] + 22, tops[i] + 40))
Sh.poly(sp_)
sa = gauss(Sh.a(), 16)
sa = np.asarray(Image.fromarray(sa).resize((OW, OH), Image.BICUBIC), np.float32)
desk *= 1 - 0.78 * sa[..., None]

out = desk
for k in range(6):
    dst = [(xs[k], tops[k]), (xs[k + 1], tops[k + 1]), (xs[k + 1], bots[k + 1]), (xs[k], bots[k])]
    dst2 = [(a * S, b * S) for a, b in dst]
    src = [(0, 0), (PW, 0), (PW, PHh), (0, PHh)]
    Hm = homog(dst2, src)
    w = Hm[2, 0] * X + Hm[2, 1] * Y + Hm[2, 2]
    u = (Hm[0, 0] * X + Hm[0, 1] * Y + Hm[0, 2]) / w
    v = (Hm[1, 0] * X + Hm[1, 1] * Y + Hm[1, 2]) / w
    ins = (u >= 0) & (v >= 0) & (u < PW - 1) & (v < PHh - 1)
    tex = sample(panels[k], np.clip(u, 0, PW - 2.01), np.clip(v, 0, PHh - 2.01))
    # the panels that face the lamp are bright, the others fall off into their fold
    facing = 1.0 if k % 2 == 1 else 0.80
    uu = np.clip(u / PW, 0, 1)
    grad = uu if k % 2 == 0 else (1 - uu)
    sh = facing * (1 - 0.30 * grad ** 2.2) * (1 + 0.08 * (1 - grad))
    if k < 3:
        sh = np.minimum(sh * 1.06, 1.0)
    tex = tex * sh[..., None]
    out = np.where(ins[..., None], tex, out)

# Sharp crease highlight along each fold
Cr = Mask(FW, FH, 2)
for i in range(1, 6):
    if i % 2 == 1:
        Cr.line([(xs[i], tops[i]), (xs[i], bots[i])], 1.6)
cr = np.asarray(Image.fromarray((Cr.a() * 255).astype(np.uint8)).resize((OW, OH), Image.BICUBIC), np.float32) / 255
out = out + cr[..., None] * 0.22

# Where the sheet comes from: the book itself at the left, edges showing the eight chapter papers
bx1 = xs[0] + 3
top_b, bot_b = tops[0] + 6, bots[0] - 6
for i in range(46):
    x_a = bx1 - i * 3.0
    y_a = top_b - 22 + i * 0.5
    y_b = bot_b + 34 + i * 0.5
    k = chapter_at(i / 46 + 0.01)
    col = hexc(CH[k]["paper"]) * (0.92 if i % 3 else 0.74)
    sel = (X / S > x_a - 3.0) & (X / S <= x_a) & (Y / S > y_a) & (Y / S < y_b)
    out[sel] = col
sel = (X / S <= bx1 - 46 * 3.0) & (Y / S > top_b - 2) & (Y / S < bot_b + 56)
out[sel] = hexc("#1f1a22")
# The lamp sits over the read panels; its light gives out at the door of the fourth
lx = xs[3]
fall_off = np.clip(1.14 - np.clip((X / S - lx + 60) / 240, 0, 1) * 0.30, 0, 1.2)
out *= fall_off[..., None] * hexc("#fff3dc")
out = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((FW, FH), Image.LANCZOS), np.float32) / 255

# 048: a red paper tab clipped over the top fold in front of station four, its tail reaching down to the road
fx = xs[3]
ty = tops[3]
Tb = Mask(FW, FH, 2)
Tb.poly([(fx - 92, 70), (fx + 92, 70), (fx + 92, 180), (fx + 14, 180), (fx, 260), (fx - 14, 180), (fx - 92, 180)])
ta = Tb.a()
ss = gauss(np.roll(np.roll(ta, 9, 0), 7, 1), 7)
out = out * (1 - 0.55 * ss[..., None])
out = ink(out, ta, "#d62c1a")
Tx = Mask(FW, FH, 2)
Tx.text((fx, 154), "048", serif(84 * 2, 900), "ms")
out = ink(out, Tx.a(), "#fff6e0")
# the tab sits right on the fold, the door of the fourth station
Pn = Mask(FW, FH, 2)
out = ink(out, Pn.a(), "#d62c1a")

save(out, ST / "T6.png")
