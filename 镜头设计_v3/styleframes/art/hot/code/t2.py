"""HKBU SCIE1007 coursework science video. Art direction `hot`, frame T2 (2-02): a person sits and talks, half screen. People are warm and stay in one piece.

The hand is a real phone frame from our own test clip (tests/T1_hand/hand_raw.mp4 at 2 s), cut by skin colour with nothing fixed by hand: that is the point,
it shows what ordinary phone footage looks like once it passes the sticker treatment. The talking head and body are a back-lit placeholder until the team films:
no member has been filmed yet, so the grade has not been tried on a real face.
S2 has no fluorescent yellow: yellow is held back until W2.
"""
from hot_kit import *
from PIL import ImageFilter

SRC = ART / "hot/_work/hand_phone_2s.jpg"   # frame at 2 s of tests/T1_hand/hand_raw.mp4
SS = 2


def spline(pts, n=14, closed=True):
    p = np.array(pts, np.float32)
    N = len(p)
    out = []
    for i in range(N if closed else N - 1):
        a, b, c, d = p[(i - 1) % N], p[i], p[(i + 1) % N], p[(i + 2) % N]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3))
    return [tuple(q) for q in out]


def smooth(pts, r=0):
    im = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in spline(pts)], fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


def ell(cx, cy, rx, ry, ang=0.0):
    t = np.linspace(0, 2 * np.pi, 90)
    ca, sa = np.cos(ang), np.sin(ang)
    x, y = rx * np.cos(t), ry * np.sin(t)
    im = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(im).polygon([((cx + a * ca - b * sa) * SS, (cy + a * sa + b * ca) * SS) for a, b in zip(x, y)], fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255


# ---- field: cobalt, one magenta collision. No yellow in S2.
rgb = field(B)
Q = [("How can", 1.0), ("computer-aided", 1.0), ("methods help scientists", 1.0), ("find and assess potential", 1.0), ("cancer drug candidates?", 1.0)]
TX, TW = 56, 930
y = 150
rows = []
for s, _ in Q:
    sp = sprite(s, black(300), pad=0)
    h_ = int(TW / sp.width * sp.height * 1.16)
    rows.append((s, sp, h_, y))
    y += h_ + 24

_, _, h1, y1 = rows[1]
# the magenta block runs out of the second line and steps up to the top edge, the person stands clear of it on cobalt
pts = [(0, y1 - 16), (1040, y1 - 16), (1040, y1 - 96), (1160, y1 - 96), (1160, y1 - 176), (1280, y1 - 176), (1280, 0), (1400, 0), (1400, y1 + h1 + 12), (0, y1 + h1 + 12)]
rgb = comp(rgb, poly(pts), M)
for i, (s, sp, h_, y_) in enumerate(rows):
    r = sp.resize((TW, h_), Image.LANCZOS)
    rgb = comp(rgb, place(r, TX, y_), K if i == 1 else P)

# ---- real hand: one frame of our own phone clip, cut by colour, no retouching
im = np.asarray(Image.open(SRC).convert("RGB"), np.float32) / 255
r_, g_, b_ = im[..., 0] * 255, im[..., 1] * 255, im[..., 2] * 255
mk = ((r_ - b_) > 55) & (r_ > 140) & (r_ - g_ > 28)
mk[:380] = False
mk[:, :380] = False
mk[800:] = False
from collections import deque
seen = np.zeros(mk.shape, bool)
dq = deque([(620, 620)])
seen[620, 620] = True
while dq:
    a_, b__ = dq.popleft()
    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c, d = a_ + da, b__ + db
        if 0 <= c < mk.shape[0] and 0 <= d < mk.shape[1] and mk[c, d] and not seen[c, d]:
            seen[c, d] = True
            dq.append((c, d))
HS = 0.86
crop = (380, 385, 720, 800)
hw, hh = int((crop[2] - crop[0]) * HS), int((crop[3] - crop[1]) * HS)
pil = Image.fromarray((im * 255).astype(np.uint8)).crop(crop).resize((hw, hh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(4, 80, 2))
hlum = np.asarray(pil.convert("L"), np.float32) / 255
hmask = np.asarray(Image.fromarray((seen * 255).astype(np.uint8)).crop(crop).resize((hw, hh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.4)), np.float32) / 255
hmask = np.clip((hmask - 0.45) * 8, 0, 1)
HX, HY = 1012, 512

# ---- placeholder body: a back-lit silhouette in the same warm ramp, so nobody reads it as a dummy. The team's footage replaces it, grade and sticker stay
def rimlight(mask, s=26, dirn=(-0.86, -0.3)):
    """Soft edge light from the question's side, from the silhouette alone."""
    h_ = blur(mask, s)
    gy, gx = np.gradient(h_)
    k = -(gx * dirn[0] + gy * dirn[1]) * s * 3.2
    return np.clip(k, 0, 1) ** 1.6 * mask

torso = smooth([(1400, 720), (1480, 610), (1600, 540), (1740, 530), (1880, 560), (2010, 640), (2010, 1140), (1400, 1140), (1370, 880)])
arm = smooth([(1252, 540), (1320, 530), (1420, 610), (1530, 700), (1610, 830), (1610, 960), (1530, 1020), (1420, 960), (1340, 880), (1280, 800), (1244, 680)])
# a head in profile with the mouth open, facing the question: the person is talking to it. Units are percent of head height
UX, UY, US = 1486, 142, 3.3
PROFILE = [(30, 0), (17, 5), (9, 15), (7, 26), (8, 34), (3, 42), (0, 49), (3, 52), (7, 54), (7, 57), (3, 59), (9, 62), (13, 63.5), (10, 66), (5, 69), (8, 73),
           (9, 76), (7, 82), (10, 89), (17, 93), (26, 93), (37, 90), (38, 100), (37, 112), (36, 135), (76, 135), (66, 112), (64, 88), (71, 72), (80, 54), (82, 34), (76, 14), (56, 2)]
head = np.zeros((H, W), np.float32)
im_ = Image.new("L", (W * SS, H * SS), 0)
ImageDraw.Draw(im_).polygon([((UX + a * US) * SS, (UY + b * US) * SS) for a, b in spline(PROFILE, 8)], fill=255)
head = np.asarray(im_.resize((W, H), Image.LANCZOS), np.float32) / 255
HAIR = [(14, 15), (17, 6), (30, -5), (50, -8), (70, -2), (84, 12), (91, 32), (92, 56), (88, 76), (84, 94), (77, 104), (73, 94), (68, 108), (62, 96), (58, 86), (52, 74), (49, 60),
        (44, 50), (41, 40), (34, 32), (28, 25), (22, 24), (17, 26), (13, 22)]
im_ = Image.new("L", (W * SS, H * SS), 0)
ImageDraw.Draw(im_).polygon([((UX + a * US) * SS, (UY + b * US) * SS) for a, b in spline(HAIR, 8)], fill=255)
hair = np.asarray(im_.resize((W, H), Image.LANCZOS), np.float32) / 255
body = np.clip(torso + head + hair, 0, 1)
lum = 0.06 + 0.56 * rimlight(body) + 0.24 * rimlight(body, 74) + 0.012 * kit.noise(H, W, 40, 2)
lum = lum * (1 - hair) + (0.025 + 0.5 * rimlight(hair, 12, (-0.5, -0.86))) * hair
lum_arm = 0.08 + 0.7 * rimlight(arm, 20, (-0.5, -0.86))
hand_m = np.zeros((H, W), np.float32)
x1 = min(W, HX + hw)
hand_m[HY:HY + hh, HX:x1] = hmask[:, :x1 - HX]
hl = np.zeros((H, W), np.float32)
hl[HY:HY + hh, HX:x1] = np.clip((hlum[:, :x1 - HX] - 0.42) * 1.5 + 0.60, 0, 1)
fig_m = np.clip(body + arm, 0, 1)
all_m = np.clip(fig_m + hand_m, 0, 1)
lum2 = lum * (1 - hand_m) + hl * hand_m
lum2 = lum2 * (1 - arm) + lum_arm * arm

# the one grade every member's clip goes through: luminance into a warm ramp, so any room and any phone lands on the same people
RAMP = [(0.0, hx("#26080E")), (0.3, hx("#7A1A14")), (0.55, hx("#E8541C")), (0.78, hx("#FFAA62")), (1.0, hx("#FFF3DC"))]
xs = np.array([a for a, _ in RAMP], np.float32)
cs = np.stack([c for _, c in RAMP])
g = np.stack([np.interp(np.clip(lum2, 0, 1), xs, cs[:, i]) for i in range(3)], -1).astype(np.float32)

die = grow(all_m, 9)
shadow = np.zeros_like(die)
shadow[16:, 16:] = die[:-16, :-16]
rgb = comp(rgb, shadow, K)
rgb = comp(rgb, die, P)
rgb = comp(rgb, all_m, g)

# ---- real data on the margin, in the place nothing needs reading
s = plddt()
for i, c in enumerate(s):
    x = 56 + i * 2.688
    h_ = int(8 + 36 * float(c))
    rgb[1020 - h_:1020, int(x):int(x) + 2] = P if c >= 0.7 else M
save(rgb, "T2.png")
