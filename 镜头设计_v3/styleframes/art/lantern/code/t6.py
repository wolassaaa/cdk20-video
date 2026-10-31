"""HKBU SCIE1007 coursework science video. Lantern T6 (6-10): the road map, used twelve times. A black wall runs away into the dark with six doors on it. Doors that have been opened have solid light behind them. A spike of light on the floor stops at the fourth threshold, the person with the lamp stands there. The rest have never been lit and exist only as chalk."""
from lk import *

XS = [168, 520, 832, 1112, 1372, 1622]
DW = [236, 200, 170, 150, 134, 122]
top = lambda x: 234 + 0.042 * x
bot = lambda x: 912 - 0.156 * x
c = blank()


def door_poly(i):
    xl, xr = XS[i] - DW[i] / 2, XS[i] + DW[i] / 2
    return xl, xr, [(xl, top(xl)), (xr, top(xr)), (xr, bot(xr)), (xl, bot(xl))]


# floor: every open door lays a hard flat wedge toward the viewer, the same flat light as T2
spill = np.zeros((H, W), np.float32)
for i in range(3):
    xl, xr, _ = door_poly(i)
    p = [(xl, bot(xl)), (xr, bot(xr)), (xr + 470, H + 20), (xl + 120, H + 20)]
    spill = np.maximum(spill, Layer(W, H, 2).poly(p).a())
c = lay(c, spill, AMBER)

# the spike: from the third door along the foot of the wall, its point exactly on the fourth threshold
xl3, xr3, _ = door_poly(2)
xl4, xr4, _ = door_poly(3)
sp = Layer(W, H, 2).poly([(xr3, bot(xr3)), (xl4, bot(xl4)), (xr3 + 12, bot(xr3) + 54)]).a()
c = lay(c, sp, AMBER)

# open doors: a block of solid light, a black leaf swung inward
for i in range(3):
    xl, xr, pl = door_poly(i)
    d = Layer(W, H, 2).poly(pl).a()
    c = lay(c, d, AMBER_HI)
    w_ = xr - xl
    leaf = [(xl, top(xl)), (xl + w_ * 0.30, top(xl) + 26), (xl + w_ * 0.30, bot(xl) - 44), (xl, bot(xl))]
    c = lay(c, Layer(W, H, 2).poly(leaf).a(), BLACK)

# doors never lit: chalk only, and the chalk floor line carrying on into the dark
for i in (3, 4, 5):
    xl, xr, pl = door_poly(i)
    c = lay(c, dash([pl[3], pl[0], pl[1], pl[2]], on=20, off=13, width=3.6), CHALK)
c = lay(c, dash([(xl4, bot(xl4)), (W + 10, bot(W + 10))], on=20, off=13, width=3.6), CHALK)

# the person at the threshold
PX = xl4 - 50
PY = bot(PX) + 4
fig, (lx, ly) = walker(PX, PY, 2.8, reach=(1.2, 0.84))
ang = np.arctan2(yy - ly, xx - lx)
dist = np.hypot(xx - lx, yy - ly)
da = np.abs(np.angle(np.exp(1j * ang)))
cone = fft_blur(((da < np.radians(21)) & (xx > lx) & (dist < 130)).astype(np.float32), 0.7)
c = add(c, cone * 0.36, AMBER)
c = lay(c, fig, AMBER)
c = add(c, (dist < 8).astype(np.float32), AMBER_HI)
bw = tw("048", 48, 800)
c = lay(c, Layer(W, H, 2).rect(PX - 24 - bw / 2 - 18, PY - 248, PX - 24 + bw / 2 + 18, PY - 180).a(), AMBER)
c = lay(c, tx("048", 48, 800, PX - 24, PY - 196, anchor="ms"), BLACK)

# names in one level row. Lit ones are bright holes, the rest are chalk
names = [("Target",), ("Hit",), ("Improve",), ("Cells &", "animals"), ("Clinical trials", "1-2-3"), ("Approval",)]
for i, nm in enumerate(names):
    col = AMBER_HI if i < 3 else CHALK
    wt = 800 if i < 3 else 500
    for j, l in enumerate(reversed(nm)):
        c = lay(c, tx(l, 46, wt, XS[i], 214 - j * 58, anchor="ms"), col)
    if i >= 3:
        if i == 3:  # script 6-10: first cell tests were done. Waits on the director
            c = lay(c, tx("cells: first tests", 38, 600, 1056, 816), AMBER)
            c = lay(c, tx("animals: not reported", 38, 500, 1056, 864), CHALK)
        else:
            c = lay(c, tx("not reported", 38, 500, XS[i], bot(XS[i]) + 66, anchor="ms"), CHALK)
save(c, "T6.png")
