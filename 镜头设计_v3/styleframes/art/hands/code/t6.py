"""HKBU SCIE1007 coursework science video. Hands T6: the road map as a relay across the ash, with real hands cut from our phone clip.
Stations 1 to 3 are hands. Gold runs from touch to touch and stops at the door of station 4. Stations 4 to 6 are empty dents in the shape of those same hands."""
from hk import *
from phone import hand, over

ST = np.array([(190, 560), (490, 510), (790, 565), (1120, 515), (1420, 565), (1720, 515)], np.float32)
LAB = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"]
DOOR = 1052.0     # the gold head stops here, just short of station 4
FRAMES = [690, 684, 694]     # the same clip a moment apart, so no two stations are the same picture


def pose(i):
    return hand(FRAMES[i % 3], "Left", tuple(ST[i]), 196 if i % 2 == 0 else -14, 1.14, wrist=0.5, arm_dir=(0.51, -0.86))


def spline(p, n=40):
    p = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3))
    return np.vstack(out + [p[-2:-1]])


path = spline(np.vstack([[-40, 590], ST, [1980, 480]]))
wob = vnoise(W, H, 90, 21, 3)
path[:, 1] += (np.interp(path[:, 0], np.arange(W), wob[540]) - 0.5) * 26


def line_mask(pts, wfun):
    im = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(im)
    for i in range(len(pts) - 1):
        w = wfun(pts[i])
        d.line([tuple(pts[i] * 2), tuple(pts[i + 1] * 2)], fill=255, width=max(2, int(w * 2)))
        d.ellipse((pts[i][0] * 2 - w, pts[i][1] * 2 - w, pts[i][0] * 2 + w, pts[i][1] * 2 + w), fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


wn = vnoise(W, 1, 60, 8, 3)[0]
live = path[path[:, 0] <= DOOR]
gold = line_mask(live, lambda p: 15 + 12 * wn[int(np.clip(p[0], 0, W - 1))] - 6 * max(0, (p[0] - 850) / 200))
future = line_mask(path[path[:, 0] > DOOR + 80], lambda p: 7)
pool = np.zeros((H, W), np.float32)
for i in range(3):
    pool = np.maximum(pool, poly([(ST[i][0] + 34 * math.cos(t) * (1 + 0.2 * math.sin(3 * t + i)), ST[i][1] + 24 * math.sin(t)) for t in np.linspace(0, 6.28, 48)]))
hy = float(path[np.abs(path[:, 0] - DOOR).argmin(), 1])
head = poly([(DOOR - 22 + 66 * math.cos(t) * (1 + 0.05 * math.sin(5 * t)), hy + 40 * math.sin(t) * (1 + 0.07 * math.sin(3 * t + 1))) for t in np.linspace(0, 6.28, 64)])
gold = np.clip(np.maximum.reduce([gold, pool, head]), 0, 1)
crack = np.clip((vnoise(W, H, 16, 4, 3) - 0.5) * 7 + 0.5, 0, 1)
gm = np.clip(np.clip(gblur(gold, 1.4) * (0.78 + 0.5 * crack) - 0.26, 0, 1) * 1.7, 0, 1)

# hands 4 to 6 exist only as the shape they would leave
dent_a = np.zeros((H, W), np.float32)
for i in (3, 4, 5):
    dent_a = np.maximum(dent_a, pose(i)[..., 3])

fn, fr = font(SERIF, 50), font(SERIF, 40)
txt_on, txt_off = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
POS = [(160, 400), (490, 640), (748, 410), (1092, 640), (1352, 408), (1720, 640)]
for i, t in enumerate(LAB):
    x, y = POS[i]
    if i < 3:
        txt_on = np.maximum(txt_on, layer(sprite_text(t, fn), x, y, "c"))
    else:
        txt_off = np.maximum(txt_off, layer(sprite_text(t, fn), x, y, "c"))
sub = {3: ["cells: first tests", "animals: not reported"], 4: ["not reported"], 5: ["not reported"]}
for i, rows in sub.items():
    x, y = POS[i]
    for j, t in enumerate(rows):
        txt_off = np.maximum(txt_off, layer(sprite_text(t, fr), x, y + 54 + j * 48, "c"))
tag = layer(sprite_text("048", font(BLACK, 40)), DOOR - 22, hy, "c")

relief = press(dent_a, 2.6, 3.2) + press(gold, 1.1, 2.0) + press(future, 0.34, 3.0) + press(txt_on + txt_off, 0.16, 1.2)
rgb, _ = ash(relief, tone=0.30, seed=17, light=1.0)
rgb = rgb * (1 - gblur(dent_a, 5)[..., None] * 0.38)
gy, gx = np.gradient(gblur(gold, 2.4))
sh = np.clip((gx * LX + gy * LY) * 6, -1, 1)
col = GOLD[None, None] * (0.78 + 0.32 * sh[..., None]) + GOLD_L[None, None] * np.clip(sh[..., None], 0, 1) * 0.6
rgb = comp(rgb, gm, col)
rgb = comp(rgb, gblur(txt_on, 0.5), np.array([0.92, 0.92, 0.92], np.float32))
rgb = comp(rgb, gblur(txt_off, 0.5), np.array([0.70, 0.70, 0.71], np.float32))
rgb = comp(rgb, gblur(tag, 0.4), np.array([0.07, 0.045, 0.02], np.float32))
for i, g in ((0, 1.0), (1, 0.92), (2, 1.04)):
    rgb = over(rgb, pose(i), grade_gain=g)
rgb = vignette(rgb, 0.40)
save(rgb, "T6.png")
