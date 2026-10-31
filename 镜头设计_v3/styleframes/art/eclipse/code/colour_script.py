"""HKBU SCIE1007 coursework science video. Eclipse direction, colour script, 1920x480.
Every column is one real beat of script_v3.3, at its true length and with its true kind: gold is a person on camera, pearl is the machine, red is the world and the ink. The sun across the top is the metaphor's clock."""
import re

from ec import *

SCRIPT = ART.parent.parent / "script/script_v3.3.md"
lines = SCRIPT.read_text(encoding="utf8").split("\n")


def sec(s):
    m, c = s.split(":")
    return int(m) * 60 + int(c)


beats = []
for i, ln in enumerate(lines):
    m = re.match(r"\*\*([0-9W][0-9-]*) · (\d\d:\d\d)–(\d\d:\d\d) · (.*?)\*\*", ln)
    if not m:
        continue
    vis = next((l for l in lines[i + 1:i + 8] if l.startswith("- Visual:")), "")
    a, b = sec(m.group(2)), sec(m.group(3))
    kind = "cam" if "ON-CAM" in m.group(4) else "music" if "MUSIC" in m.group(4) else "3d" if ("[3D]" in vis or "[TD]" in vis) else "flat"
    beats.append((m.group(1), a, b, kind))
beats.sort(key=lambda r: r[1])
END = max(b[2] for b in beats)
print(len(beats), "beats, ends", END, [k for k in ("cam", "music", "3d", "flat") if not any(b[3] == k for b in beats)])

SEC = [("S1", 0), ("S2", 141), ("S3", 283), ("S4", 412), ("S5", 625), ("S6", 764), ("S7", 915), ("S8", 964)]
W2, W3 = 412, 574
SW, SH = W, 480
yy, xx = grid(SW, SH)
TOP, BOT = 104, 424
t = np.zeros((SH, SW), np.float32)
ai = np.zeros((SH, SW), np.float32)
px = SW / END


def floor(s):
    """How much red the world still has: falls away through S1 to S3, then stays black, one hold of red wall at the number."""
    return float(np.interp(s, [0, 141, 283, 370, 412, 640, 660, 760, 1000, END], [0.42, 0.40, 0.30, 0.10, 0.02, 0.02, 0.40, 0.26, 0.06, 0.03]))


def pearl(s):
    """How much of the frame the machine's light takes. None before W2: the first cold thing in the film is the first look at CDK20."""
    if s < W2:
        return 0.0
    return float(np.interp(s, [412, 437, 470, 500, 545, 574, 589, 615, 640, 780, 960, 1040, END], [0.55, 0.30, 0.22, 0.26, 0.42, 0.95, 0.70, 0.38, 0.20, 0.16, 0.14, 0.10, 0.12]))


cy = (TOP + BOT) / 2
for name, a, b, k in beats:
    x0, x1 = int(a * px), max(int(b * px), int(a * px) + 1)
    s = (a + b) / 2
    col = (xx >= x0) & (xx < x1) & (yy >= TOP) & (yy < BOT)
    base = floor(s) * (0.55 + 0.45 * ((yy - TOP) / (BOT - TOP)))
    t = np.where(col, base, t)
    p = pearl(s)
    if k == "cam":                         # a person: gold blob in the middle of the warm dark
        h = 74 * (1 if s > 20 else 1)
        c = np.exp(-((yy - cy) / h) ** 4)
        t = np.where(col, np.maximum(0.10, base) * (1 - c) + 0.74 * c, t)
    elif p > 0:                            # the machine: pearl, growing out of black
        h = 12 + 150 * p
        c = np.exp(-((yy - cy) / h) ** 2) * (0.5 + 0.5 * p)
        t = np.where(col, np.maximum(base, 0.98 * c), t)
        ai = np.where(col, sstep(0.0, 0.4, c), ai)
    elif k == "flat" or k == "3d":         # the world and the ink: the red holds, a thin dark centre
        t = np.where(col, base * (1 - 0.35 * np.exp(-((yy - cy) / 60) ** 2)), t)
t = blur(t, 0.7)

# the eclipse across the top as a clock: same shadow sliding on, stopping at the cover it holds for the rest of the film
n = 20
COVER = [(0, 0.03), (141, 0.30), (283, 0.72), (412, 1.0), (625, 1.0), (640, 0.985), (END, 0.975)]
for i in range(n):
    tm = (i + 0.5) / n
    sx_ = tm * SW
    c = float(np.interp(tm * END, [p[0] for p in COVER], [p[1] for p in COVER]))
    R, cy0 = 26, 54
    disc = sstep(R + 1, R - 1, np.hypot(xx - sx_, yy - cy0))
    moon = sstep(R + 1.5, R - 0.5, np.hypot(xx - (sx_ + 2 * R * (1 - c) * 1.02), yy - cy0))
    t = put(t, disc, 0.02)
    lit = disc * (1 - moon)
    t = put(t, lit, 1.0)
    ai = np.maximum(ai, np.maximum(lit, disc))
    if c >= 0.97:
        r_ = ring(xx, yy, sx_, cy0, R, 2)
        t = put(t, r_, 0.5)
        ai = np.maximum(ai, r_)
    if tm * END > 640:                     # one bead on the limb, it barely grows: the film ends at the first thread of light
        rb = 2.5 + (tm * END - 640) / (END - 640) * 5
        bd = sstep(rb + 1, rb - 1, np.hypot(xx - (sx_ - R + 2), yy - cy0))
        t = put(t, bd, 1.0)


def lab(s_, x_, y_, size, v, weight=500, anchor="lm"):
    global t
    im = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(im).text((x_, y_), s_, 255, font=face(size, weight), anchor=anchor)
    t = put(t, np.asarray(im, np.float32) / 255, v)


for j, (name, a) in enumerate(SEC):
    b = SEC[j + 1][1] if j + 1 < len(SEC) else END
    x0 = int(a * px)
    t = put(t, box(xx, yy, x0, BOT, x0 + 2, SH), 1.0)
    d = b - a
    lab(f"{name} {d // 60}:{d % 60:02d}", x0 + 8, 452, 22, 1.0)
for s_, at in (("first cold", W2), ("8,918", W3)):
    x_ = int(at * px)
    lab(s_, x_ + 2, TOP - 14, 20, 1.0)
save(t, "colour_script.png", ai)
