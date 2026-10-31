"""HKBU SCIE1007 coursework science video. Eclipse direction, T6: the roadmap as the classic multiple-exposure photo of an eclipse crossing the sky. Six stations, six exposures. The real CDK20 outline takes the bite, three stations are lit, light reaches the door of the fourth and the rest is dashed."""
from ec import *

y, x = grid()

# real outline as the occluder, one flat mask reused at every station
cache = WORK / "t6_mask.npy"
if cache.exists():
    OC = np.load(cache)
else:
    Vm = kit.view(scale=9.0, cx=480, cy=480, w=960, h=960, ss=0.6)
    OC = sstep(0.4, 0.6, blur(Vm["mask"], 1.5)).astype(np.float32)
    np.save(cache, OC)

# sky: red low down, black overhead, the whole frame stays in the lower band so the suns are the only light
hz = 836
sky = 0.05 + 0.31 * sstep(120, hz, y) ** 2.2
t = sky + 0.012 * (noise(7, 500) - 0.5)

R = 112
XS = [176, 492, 808, 1124, 1440, 1756]
YS = [430, 300, 236, 236, 300, 430]
OFF = [(500, 0), (262, 26), (168, 8)]    # the shadow slides in from the right: this edge is the edge of what is known


def occ(cx, cy, dx, dy):
    """Sample the outline scaled so it just covers a sun of radius R, slid by dx, dy."""
    k = 0.62
    return sample(OC, (x - cx - dx) / k + 480, (y - cy - dy) / k + 480)


# the path: solid and lit as far as the door of station 4, dashed beyond
px, py = np.array(XS, float), np.array(YS, float)
ts = np.linspace(0, 5, 1400)
cx_ = np.interp(ts, range(6), px)
cy_ = np.polyval(np.polyfit(range(6), py, 4), ts)
door = 3 - (R + 24) / (XS[3] - XS[2])
img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(img)
pts = [(float(a), float(b)) for a, b, c in zip(cx_, cy_, ts) if c <= door]
d.line(pts, fill=255, width=8)
lit = np.asarray(img, np.float32) / 255
img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(img)
rest = [(float(a), float(b)) for a, b, c in zip(cx_, cy_, ts) if c > door]
for i in range(0, len(rest) - 16, 34):
    d.line(rest[i:i + 16], fill=255, width=4)
dash = np.asarray(img, np.float32) / 255
g0 = np.clip(blur(lit, 22) * 0.55 + blur(lit, 7) * 0.5, 0, 1)
t = t + g0 * 0.5
ai = np.clip(g0 * 1.5, 0, 1)
t = put(t, lit, 0.92)
ai = np.maximum(ai, lit)

for i, (cx, cy) in enumerate(zip(XS[:3], YS[:3])):
    dx, dy = OFF[i]
    d_ = np.hypot(x - cx, y - cy)
    disc = sstep(R + 1, R - 1, d_)
    sh = occ(cx, cy, dx, dy)
    lightm = disc * (1 - sh)
    t = put(t, disc * (1 - lightm), 0.02)                       # the shadowed part of the sun is pure dark
    glow = blur(lightm, 12) * 0.8 + blur(lightm, 40) * 1.2 + blur(lightm, 110) * 1.0
    gc = np.clip(glow, 0, 1) * (1 - disc)
    t = np.clip(t + gc * 0.40, 0, 1)
    t = put(t, lightm, 1.0)
    ai = np.maximum(ai, np.clip(np.maximum(disc, gc * 1.5), 0, 1))

# rest of the path over the glow
t = put(t, dash, 0.62)
ai = np.maximum(ai, dash)

# station 4: fully covered, thin ring, one bead on the edge that faces the light
cx4, cy4 = XS[3], YS[3]
t = put(t, sstep(R + 1, R - 1, np.hypot(x - cx4, y - cy4)), 0.0)
dr = dashed_ring(x, y, cx4, cy4, R, 4, 15)
t = put(t, dr, 0.62)
ai = np.maximum(ai, dr)
bx, by = cx4 - R + 6, cy4 + 2
bd = sstep(13, 7, np.hypot((x - bx) * 0.8, y - by))
gb = np.clip(blur(bd, 7) * 1.1 + blur(bd, 24) * 1.4 + blur(bd, 70) * 1.2, 0, 1)
t = np.clip(t + gb, 0, 1)
t = put(t, bd, 1.0)
ai = np.maximum(ai, np.clip(gb * 1.6, 0, 1))

# stations 5, 6: empty dashed rings, nothing has reached them
for cx, cy in zip(XS[4:], YS[4:]):
    t = put(t, sstep(R + 1, R - 1, np.hypot(x - cx, y - cy)), 0.03)
    dr = dashed_ring(x, y, cx, cy, R, 4, 15)
    t = put(t, dr, 0.62)
    ai = np.maximum(ai, dr)

# 048 marks how far the light has come
t = put(t, text("048", 84, (cx4 - R + 6, 74), 900, "mm"), 0.96)
t = put(t, box(x, y, cx4 - R + 5, 122, cx4 - R + 8, by - 22), 0.9)
ai = np.maximum(ai, np.maximum(text("048", 84, (cx4 - R + 6, 74), 900, "mm"), box(x, y, cx4 - R + 5, 122, cx4 - R + 8, by - 22)))

# ground and a plumb line from every sun, one person stands where the light stops, the only warm thing here
g = sstep(hz - 1, hz + 1, y)
t = t * (1 - g)
ai = ai * (1 - g)
PAPER = 1.0      # plain type, not light
LINE = 0.46
for i, (cx, cy) in enumerate(zip(XS, YS)):
    b_ = box(x, y, cx - 1, cy + R + 8, cx + 1, hz)
    if i < 3:
        t = put(t, b_, 0.84)
    else:
        b_ = b_ * ((y // 14) % 2 == 0)
        t = put(t, b_, LINE)
    ai = np.maximum(ai, b_)
pp = person(x, y, cx4 - R + 6, hz, 74)
t = put(t, pp, 0.72)
ai = ai * (1 - pp)
gl_ = blur(pp, 10) * (1 - pp)
t = np.clip(t + gl_ * 0.5, 0, 1)
b1 = box(x, y, 0, hz - 2, W, hz + 2) * (x < cx4 - R)
b2 = box(x, y, cx4 - R, hz - 1, W, hz + 1) * ((x // 26) % 2 == 0)
t = put(t, b1, 0.8)
t = put(t, b2, LINE)
ai = np.maximum(ai, np.maximum(b1, b2))

# names, 36 px or more. Under station 4 and beyond, the line itself says how far the evidence goes: solid is done, dashed is not reported. Station 4's lines wait for the director
NAMES = [["Target"], ["Hit"], ["Improve"], ["Cells & animals"], ["Clinical trials", "1-2-3"], ["Approval"]]
for i, (cx, nm) in enumerate(zip(XS, NAMES)):
    yy_ = 892
    for ln in nm:
        t = put(t, text(ln, 44 if i < 3 else 40, (cx, yy_), 700 if i < 3 else 500, "mm"), PAPER)
        yy_ += 50
    if i == 3:
        t = put(t, text("cells: first tests", 36, (cx, 946), 400, "mm"), PAPER)
        t = put(t, box(x, y, cx - 132, 968, cx + 132, 970), PAPER)
        t = put(t, text("animals: not reported", 36, (cx, 1000), 400, "mm"), 0.48)
        t = put(t, box(x, y, cx - 180, 1026, cx + 180, 1028) * ((x // 14) % 2 == 0), 0.48)
    if i > 3:
        t = put(t, text("not reported", 36, (cx, 1000), 400, "mm"), 0.48)
        t = put(t, box(x, y, cx - 104, 1026, cx + 104, 1028) * ((x // 14) % 2 == 0), 0.48)
save(t, "T6.png", ai)
