"""HKBU SCIE1007 coursework science video. Direction inside: colour script, S1 to S8 left to right, width by running time.
S1 to S6 are the F frames rebuilt as packed discs, each disc taking one pixel from its frame, so the shares of colour are the real ones and stay on palette. S7 and S8 have no test frame yet: their bands are planned colours."""
from ilib import *

W_, H_, TOP = 1920, 480, 62
SECS = [("S1", 141, "2:21", "F1.png", 1330), ("S2", 142, "2:22", "F2.png", 900), ("S3", 129, "2:09", "F3.png", 470), ("S4", 213, "3:33", "F4.png", 950),
        ("S5", 139, "2:19", "F5.png", 1500), ("S6", 151, "2:31", "F6.png", 1090), ("S7", 49, "0:49", None, 0), ("S8", 99, "1:39", None, 0)]


def planned(name):
    if name == "S7":      # next steps: the bright blue, the road in bone
        rgb = crowd(seed=31, layers=((34, 62, BLUE * .8, None), (46, 84, KLEIN, BLACK)), ground=KLEIN * .7)
        rgb = dim(rgb, box(0, 470, W, 610, 12), 1, col=BONE)
    else:                  # the answer: lights on, bone ground, ink and one red
        rgb = crowd(seed=32, layers=((34, 62, BONE * .92, None), (46, 84, BONE * .84, BLACK)), ground=BONE)
        rgb = dim(rgb, disc(960, 540, 300, 3), 1, col=RED)
    return rgb


tot = sum(s[1] for s in SECS)
r = np.random.default_rng(21)
ss = 2
im = Image.new("RGB", (W_ * ss, H_ * ss), (0, 0, 0))
d = ImageDraw.Draw(im)
GAP, H2 = 21, H_ - TOP
x0 = 0
edges_ = []
for name, sec, tm, f, cx in SECS:
    x1 = W_ if name == "S8" else round(x0 + sec / tot * W_)
    edges_.append((x0, x1))
    bw = x1 - x0
    src = np.asarray(Image.open(OUT / f).convert("RGB")) if f else (planned(name) * 255).astype(np.uint8)
    k = H / H2                     # frame px per band px
    cx = cx or 960
    ox = np.clip(cx - bw * k / 2, 0, W - bw * k)
    tmp = Image.new("RGB", (bw * ss, H2 * ss), (0, 0, 0))
    t = ImageDraw.Draw(tmp)
    for j, y in enumerate(np.arange(0, H2 + GAP, GAP * .87)):
        for x in np.arange((j % 2) * GAP / 2, bw + GAP, GAP):
            sx, sy = int(np.clip(ox + x * k + r.normal(0, 3), 0, W - 1)), int(np.clip(y * k + r.normal(0, 3), 0, H - 1))
            c = tuple(int(v) for v in src[sy, sx])
            q = (GAP * .52) * ss
            t.ellipse((x * ss - q, y * ss - q, x * ss + q, y * ss + q), fill=c, outline=(0, 0, 0), width=ss)
    im.paste(tmp, (x0 * ss, TOP * ss))
    x0 = x1
im = im.resize((W_, H_), Image.LANCZOS)
d = ImageDraw.Draw(im)
for (x0, x1), (name, sec, tm, f, cx) in zip(edges_, SECS):
    d.text((x0 + 10, 8), name, fill=rgb8(BONE), font=sans(26, 600))
    d.text((x0 + 10, 33), tm, fill=rgb8(BONE), font=mono(22))
    d.line([(x0, 0), (x0, H_)], fill=(0, 0, 0), width=4)
save(im, "colour_script.png")
