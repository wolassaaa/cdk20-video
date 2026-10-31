"""HKBU SCIE1007 coursework science video. d7 style test: drifter pixel art. 320x180, a hard palette of 24 colours, the real CDK20 surface as a dead titan half sunk in a pink valley, one tiny cloaked figure, clean colour clusters."""
from t import *

W, H = 320, 180
K = 4
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rng = np.random.default_rng(21)

# Render the protein at low res by area average so clusters stay clean
Q = view(W * 3, H * 3, zoom=1.20, rot=-14, at=(0.655, 0.40), c=(0.5, 0.50))
def down(a):
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a).resize((W, H), Image.BOX))
    return np.stack([down(a[..., i]) for i in range(a.shape[2])], -1)


m = down(Q["mask"])
mb = m > 0.5
key = down(lit(Q, (-0.55, 0.72, -0.42), 0.0))
rimL = down(lit(Q, (0.95, 0.05, -0.05), 0.0))
ao = down(Q["ao"])
conf = down(Q["conf"])
dpt = down(Q["depth"])
Nb = dict(Q)
Nb["normal"] = gauss(Q["normal"], 16)
big = down(lit(Nb, (-0.55, 0.72, -0.42), 0.0))


def idx(a, n):
    return np.clip((a * n).astype(int), 0, n - 1)


pic = np.zeros((H, W, 3), np.float32)

# Sky: hard horizontal bands, broken by steps so they never look like a gradient tool
SKY = ["#1b1548", "#2a1b6b", "#4a2388", "#7a2c9e", "#b53aa6", "#ea4f9c", "#ff7fa0", "#ffb6a8"]
bandw = (fbm(H, W, 34, 2, 4) - 0.5) * 18
t = np.clip((yy + bandw) / 118, 0, 0.999)
n = idx(t, len(SKY))
for i, c in enumerate(SKY):
    pic[n == i] = hexc(c)
# Long flat cloud banks instead of a sun: the titan is the only round thing up there
for y0, c, seed, th in [(46, "#ffb6a8", 31, 0.60), (70, "#ff7fa0", 32, 0.58), (22, "#7a2c9e", 33, 0.60)]:
    st = fbm(H, W, 90, 3, seed)
    band = np.exp(-((yy - y0 - (st - 0.5) * 34) / 9) ** 2)
    long_ = fbm(H, W, 120, 2, seed + 40)
    cl = (band * (0.5 + long_) > 0.62)
    cl &= (yy.astype(int) % 2 == 0) | (band * (0.5 + long_) > 0.72)
    pic[cl] = hexc(c)

# Far ridges, flat colour, stepped profile
def ridge(y0, amp, cell, seed):
    n = fbm(1, W, cell, 3, seed)[0]
    prof = y0 + (n - 0.5) * amp * 2
    return np.floor(prof / 3) * 3


for y0, amp, cell, c, seed in [(98, 34, 60, "#6a2a9a", 2), (112, 30, 44, "#4a2388", 3), (124, 22, 34, "#2e1f70", 4)]:
    pr = ridge(y0, amp, cell, seed)
    pic[yy > pr[xx.astype(int)]] = hexc(c)

# Titan: colour by shade, ramps hue shifted. Cold deep teal shadow, violet mid, hot pink light, cream peak.
s = np.clip((0.55 * key + 0.65 * big) * (0.45 + 0.55 * ao), 0, 1)
RAMP = ["#0e1a44", "#142c5e", "#1c4a78", "#2a6f8c", "#3aa0a0", "#6fd0b0", "#d8f7c8"]
TAIL = ["#2a123e", "#4a1a58", "#7a2178", "#c2307e", "#ff5a8a", "#ff9fa8", "#ffe7c4"]
ths = [0.10, 0.20, 0.31, 0.44, 0.58, 0.76]
lvl = np.digitize(s, ths)
# hard clusters: a tiny majority smooth
lvb = gauss(lvl.astype(np.float32), 0.75)
lvl = np.clip(np.round(lvb).astype(int), 0, 6)
far = np.clip((dpt - 0.40) / 0.2, 0, 1)
tail = conf < 0.70  # real low confidence tail goes to the hot ramp
for i in range(7):
    pic[mb & (lvl == i) & ~tail] = hexc(RAMP[i])
    pic[mb & (lvl == i) & tail] = hexc(TAIL[i])
chk = ((xx.astype(int) + yy.astype(int)) % 2 == 0)
for i in range(1, 7):  # selective dither on just one row of pixels between bands
    edge = (lvl == i) & (gauss((lvl < i).astype(np.float32), 0.6) > 0.3) & mb & chk
    pic[edge & ~tail] = hexc(RAMP[i - 1])
    pic[edge & tail] = hexc(TAIL[i - 1])
# One pixel outline up against the sky, bright only on the lit side
sil = mb & ~(np.roll(mb, 1, 0) & np.roll(mb, -1, 0) & np.roll(mb, 1, 1) & np.roll(mb, -1, 1))
pic[sil] = hexc("#0a1030")
hl = sil & (key > 0.3)
pic[hl] = hexc("#ffffff") * 0.9

# Valley: the mass is sunk in terraces, stepped cliffs in teal-black, pink canopy above them
def cliff(y0, amp, cell, seed):
    n = fbm(1, W, cell, 3, seed)[0]
    return np.floor((y0 + (n - 0.5) * amp * 2) / 2) * 2


cols = [(143, 24, 40, "#16204e", "#2f5a8a", 7), (156, 14, 30, "#0f1638", "#1c4a78", 8), (168, 8, 22, "#090c24", "#142c5e", 9)]
for y0, amp, cell, c, lip, seed in cols:
    pr = cliff(y0, amp, cell, seed)[xx.astype(int)]
    body = yy >= pr
    pic[body] = hexc(c)
    pic[body & (yy < pr + 2)] = hexc(lip)
    # cliff strata
    st = body & ((yy.astype(int) + (xx.astype(int) // 7) % 3 * 2) % 8 == 0) & (yy > pr + 4)
    pic[st] = hexc(lip) * 0.6

# Foliage: big soft blobs of pink quantised, climbing out of the valley and over the dead form
def blobs(N, y0, y1, rmin, rmax, seed):
    r_ = np.random.default_rng(seed)
    f = np.zeros((H, W), np.float32)
    for i in range(N):
        cx, cy, rr = r_.uniform(0, W), r_.uniform(y0, y1), r_.uniform(rmin, rmax)
        d2 = ((xx - cx) ** 2 + (yy - cy) ** 2 * 1.5) / rr ** 2
        f = np.maximum(f, 1 - d2)
    return f


f = blobs(46, 128, 166, 9, 24, 3) * np.clip((xx - 100) / 34, 0, 1) ** 0.7
fn = f + (fbm(H, W, 7, 2, 8) - 0.5) * 0.34
canopy = (fn > 0.18) & (f > 0.02)
pal3 = [hexc("#ffb6a8"), hexc("#ff7fa0"), hexc("#ff5a8a"), hexc("#c2307e"), hexc("#7a2178"), hexc("#4a1a58")]
lit2 = np.clip((f - 0.1) * 0.62 + (150 - yy) / 46 + 0.14, 0, 0.999)
lit2 = np.round(lit2 * 12) / 12
lv2 = idx(1 - lit2, 6)
for i, c in enumerate(pal3):
    pic[canopy & (lv2 == i)] = c

# Figure on a stepped foreground cliff, standing against the far ridge
top = 142
cl_x = 104
profile = top + np.maximum((xx - cl_x + 40) // 6, 0) * 4 + (xx.astype(int) // 13 % 2)
rock = (yy >= profile) & (xx < cl_x + 20)
pic[rock] = hexc("#0f1638")
pic[rock & (yy < profile + 2)] = hexc("#3aa0a0")
pic[rock & (yy >= profile + 2) & (yy < profile + 3)] = hexc("#1c4a78")
st = rock & (((yy.astype(int) + (xx.astype(int) // 9) % 3 * 3) % 7) == 0) & (yy > profile + 5)
pic[st] = hexc("#16204e")
gy = top
fig = [
    "...XX...",
    "..XccX..",
    "..XccX..",
    ".XrrrrX.",
    "XrrrrrrX",
    "XrrrrrrX",
    ".XrrrrX.",
    ".XrrrrX.",
    "..X..X..",
]
fx, fy = 50, gy - 10
for j, row in enumerate(fig):
    for i, ch in enumerate(row):
        if ch == "X":
            pic[fy + j, fx + i] = hexc("#0a0c24")
        elif ch == "r":
            pic[fy + j, fx + i] = hexc("#ff3a4e")
        elif ch == "c":
            pic[fy + j, fx + i] = hexc("#d8f7c8")
pic[fy + 4:fy + 5, fx + 8:fx + 16] = hexc("#7ff7e0")
pic[fy + 3:fy + 6, fx + 15:fx + 16] = hexc("#d8f7c8")

# Floating motes, hard pixels
for i in range(70):
    x, y = rng.integers(0, W), rng.integers(10, 150)
    pic[y, x] = hexc("#ffe7c4") if i % 3 else hexc("#7ff7e0")

# Giant title: drawn from a hand pixel grid. Thick chamfered blocks, two tone with a hard shadow.
G = {
    "C": ["..XXXXX.", ".XXXXXXX", "XXX...XX", "XXX.....", "XXX.....", "XXX.....", "XXX...XX", ".XXXXXXX", "..XXXXX."],
    "D": ["XXXXXX..", "XXXXXXX.", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXXXXXX.", "XXXXXX.."],
    "K": ["XXX..XXX", "XXX.XXX.", "XXXXXX..", "XXXXX...", "XXXX....", "XXXXX...", "XXXXXX..", "XXX.XXX.", "XXX..XXX"],
    "2": [".XXXXXX.", "XXXXXXXX", "XX...XXX", ".....XXX", "...XXXX.", ".XXXX...", "XXX.....", "XXXXXXXX", "XXXXXXXX"],
    "0": [".XXXXXX.", "XXXXXXXX", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXX..XXX", "XXXXXXXX", ".XXXXXX."],
}
s_ = 3
ox, oy = 8, 6
for ci, ch in enumerate("CDK20"):
    for j, row in enumerate(G[ch]):
        for i, b in enumerate(row):
            if b == "X":
                x0 = ox + ci * 28 + i * s_ + 0
                y0 = oy + j * s_
                pic[y0 + 3:y0 + 3 + s_, x0 + 3:x0 + 3 + s_] = hexc("#1b1548")
for ci, ch in enumerate("CDK20"):
    for j, row in enumerate(G[ch]):
        for i, b in enumerate(row):
            if b == "X":
                x0 = ox + ci * 28 + i * s_
                y0 = oy + j * s_
                pic[y0:y0 + s_, x0:x0 + s_] = hexc("#d8f7c8") if j < 5 else hexc("#7ff7e0")

# Label: hand 5x7 pixel face, nothing borrowed
F = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#", "F": "#####|#....|#....|####.|#....|#....|#....", "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.", "l": "##...|.#...|.#...|.#...|.#...|.#...|###..", "p": ".....|.....|####.|#...#|####.|#....|#....",
    "h": "#....|#....|####.|#...#|#...#|#...#|#...#", "a": ".....|.....|.###.|....#|.####|#...#|.####", "o": ".....|.....|.###.|#...#|#...#|#...#|.###.",
    "d": "....#|....#|.####|#...#|#...#|#...#|.####", "v": ".....|.....|#...#|#...#|#...#|.#.#.|..#..", "6": ".###.|#....|#....|####.|#...#|#...#|.###.",
    "r": ".....|.....|#.##.|##..#|#....|#....|#....", "e": ".....|.....|.###.|#...#|#####|#....|.###.", "i": ".#...|.....|##...|.#...|.#...|.#...|###..",
    "c": ".....|.....|.###.|#....|#....|#....|.###.", "t": ".#...|.#...|####.|.#...|.#...|.#...|..##.", "·": ".....|.....|.....|.##..|.##..|.....|.....",
    " ": ".....|.....|.....|.....|.....|.....|.....",
}
xp, yp = 8, 170
pad = np.zeros((H, W), bool)
pad[yp - 3:yp + 10, 5:164] = True
pic[pad] = hexc("#0a0c24")
for ch in LABEL:
    rows = F[ch].split("|")
    wd = max(max((r.rfind("#") + 1 for r in rows), default=0), 3)
    for j, row in enumerate(rows):
        for i, b in enumerate(row):
            if b == "#":
                pic[yp + j, xp + i] = hexc("#ffe7c4")
    xp += wd + 1
print("label end", xp)

out = nearest(pic, K)

# Bloom is the only soft thing allowed: wide additive glow from the sun, the rim and the title, static
Hh, Ww = out.shape[:2]
hi = np.clip(out - 0.72, 0, 1) * 3
gl = gauss(np.asarray(Image.fromarray((hi * 255).astype(np.uint8)).resize((320, 180), Image.BOX), np.float32) / 255, 3.0)
gl = np.asarray(Image.fromarray((np.clip(gl, 0, 1) * 255).astype(np.uint8)).resize((Ww, Hh), Image.BICUBIC), np.float32) / 255
out = 1 - (1 - out) * (1 - gl * 0.42)
save(out, OUT / "d7_drifter_pixel.png")
