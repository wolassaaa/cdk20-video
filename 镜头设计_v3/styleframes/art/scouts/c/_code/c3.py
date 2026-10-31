"""HKBU SCIE1007 coursework science video. Style scout c3: seen from straight above, a real protein as a black mass on an ash plain, handprints closing in, gold lines tie them to real residues, rain falls towards the lens. Method only."""
from common import *

rng = np.random.default_rng(23)
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
GOLD = hexrgb("#FFB63C")
INK = hexrgb("#060607")
CX, CY = 640, 356

# ash
hgt = vnoise(W, H, 170, 1, 6, 0.55) + vnoise(W, H, 14, 2, 3, 0.5) * 0.14
gy, gx = np.gradient(hgt)
ash = np.clip(0.72 + (gx * 0.7 - gy * 0.5) * 22, 0, 1)
base = (0.5 + 0.5 * ash)[..., None] * hexrgb("#E2E1DA")
dist = np.hypot((xx - CX) / 1.0, (yy - CY) / 0.72)
base *= np.clip(1.08 - (dist / 980) ** 2 * 0.65, 0, 1.1)[..., None]
rgb = base.copy()


def make_hand(seed, s=340):
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((95, 150, 245, 300), 60, fill=255)
    for x, top, wd in [(106, 62, 30), (146, 34, 31), (186, 42, 31), (224, 82, 27)]:
        d.rounded_rectangle((x - wd // 2, top, x + wd // 2, 200), wd // 2, fill=255)
    d.line([(112, 245), (44, 172)], fill=255, width=34)
    d.ellipse((27, 155, 61, 189), fill=255)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    n = vnoise(s, s, 14, seed, 4)
    a = np.clip((a + (n - 0.5) * 0.5 - 0.5) * 8 + 0.5, 0, 1)
    speck = vnoise(s, s, 4, seed + 9, 2)
    a = a * np.clip((speck - 0.20) * 12, 0.55, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


hands = [make_hand(s) for s in range(6)]
hands += [h.transpose(Image.FLIP_LEFT_RIGHT) for h in hands]

# handprints walk in on rings, fingers point at the mass
ink = Image.new("L", (W, H), 0)
hp = []
for ring, (rad, count, sz) in enumerate([(345, 26, 104), (452, 32, 96), (560, 34, 92), (680, 40, 84), (810, 40, 80)]):
    for i in range(count):
        th = 2 * math.pi * (i + rng.uniform(-.28, .28)) / count + ring * 0.4
        r = rad + rng.normal(0, 18)
        x, y = CX + r * math.cos(th), CY + r * 0.70 * math.sin(th)
        if not (-60 < x < W + 60 and -60 < y < H + 60):
            continue
        ang = math.degrees(math.atan2(x - CX, -(y - CY) / 0.70 * 0.8)) + rng.normal(180, 12)
        px = int(sz * rng.uniform(.9, 1.2))
        h = hands[int(rng.integers(len(hands)))].resize((px, px), Image.BILINEAR).rotate(-ang, Image.BILINEAR, expand=True)
        ink.paste(255, (int(x - h.width / 2), int(y - h.height / 2)), h)
        hp.append((x, y))
pr = np.asarray(ink, np.float32) / 255
rim = np.clip(gblur(pr, 3) - pr, 0, 1)
rgb *= (1 + rim * 0.4)[..., None]      # ash pushed up around each print
rgb = comp(rgb, pr, INK)

# rain seen from below the clouds: streaks run towards the point straight under the lens
rain = Image.new("L", (W * 2, H * 2), 0)
d = ImageDraw.Draw(rain)
for i in range(2100):
    th = rng.uniform(0, 2 * math.pi)
    r0 = rng.uniform(250, 980)
    L = r0 * rng.uniform(.08, .34)
    x0, y0 = CX + r0 * math.cos(th), CY + r0 * math.sin(th)
    x1, y1 = CX + (r0 + L) * math.cos(th), CY + (r0 + L) * math.sin(th)
    d.line([(x0 * 2, y0 * 2), (x1 * 2, y1 * 2)], fill=int(rng.uniform(70, 230)), width=1)
rn = np.asarray(rain.resize((W, H), Image.LANCZOS), np.float32) / 255
rgb = comp(rgb, rn * 0.8, INK)

# the mass. Real surface, oil black
Q = warp(load(), zoom=0.74, cx=955, cy=520, rot=0.0, ox=CX, oy=CY)
n, m, ao, pos = Q["normal"], Q["mask"], Q["ao"], Q["pos"]
hard = gblur((m > 0.5).astype(np.float32), 0.7)
# tar runs out from the rim along the radial direction
tar = np.zeros((H, W), np.float32)
th = np.arctan2(yy - CY, xx - CX)
ang_n = vnoise(W, H, 16, 8, 2)
for i in range(1, 9):
    s = 1 + i * 0.022
    im = Image.fromarray(hard).transform((W, H), Image.AFFINE, (1 / s, 0, CX - CX / s, 0, 1 / s, CY - CY / s), Image.BILINEAR)
    tar = np.maximum(tar, np.asarray(im) * (ang_n > 0.40 + i * 0.022))
tar = np.clip(gblur(tar, 1.6) * 1.6 - .25, 0, 1)
rgb = comp(rgb, tar, INK)

v = np.array([0, 0, 1], np.float32)
r = 2 * n[..., 2:3] * n - v
fres = np.clip(1 - n[..., 2], 0, 1) ** 3.5
top = np.clip((r * (np.array([-0.45, 0.7, 0.55], np.float32) / 0.994)).sum(-1), 0, 1)
hl = np.clip((top - 0.93) * 24, 0, 1)
soft = top ** 22 * 0.10
film = 3.0 * (1 - n[..., 2]) + 2.6 * (pos[..., 0] + pos[..., 1])
ir = np.stack([np.sin(film * 3.1) * .5 + .5, np.sin(film * 3.1 + 2.0) * .5 + .5, np.sin(film * 3.1 + 4.0) * .5 + .5], -1) * 0.25 + GOLD * 0.75
oil = np.ones((H, W, 3), np.float32) * hexrgb("#040405")
oil += (soft * 1.2 + fres * 0.85 * ao)[..., None] * np.array([.66, .70, .74], np.float32)
band = 1 - np.exp(-((yy - 375) / 72) ** 4)
oil += (hl * ao * band)[..., None] * np.array([1, .97, .9], np.float32)
# gold sits in the creases of the real surface, so the form still reads inside the black
thr = np.percentile(ao[m > 0.5], 20)
seam = np.clip((thr - ao) * 22, 0, 1) * np.clip((thr + 0.1 - ao) * 8, 0, 1)
seam = seam * hard
oil = comp(oil, seam * 0.9, GOLD * (0.62 + 0.2 * (1 - band[..., None])))
rgb = comp(rgb, hard, oil)

# gold strands: real C-alpha positions, out to the prints
ca, conf, _ = read_pdb()
xy, _z = project(ca)
pts = unwarp_pts(Q, xy)
strand = Image.new("L", (W * 3, H * 3), 0)
sd = ImageDraw.Draw(strand)
hp2 = [hp[i] for i in rng.permutation(len(hp))[:34]]
for b in hp2:
    # nearest surface residue on that side, so each line lands on real data
    dv = pts - np.array(b)
    a = pts[np.argmin((dv ** 2).sum(1) + rng.uniform(0, 60000, len(pts)))]
    nx, ny = -(b[1] - a[1]) * .18, (b[0] - a[0]) * .18
    mx, my = (a[0] + b[0]) / 2 + nx * rng.uniform(-1, 1), (a[1] + b[1]) / 2 + ny * rng.uniform(-1, 1)
    t = np.linspace(0, 1, 50)
    cx_ = (1 - t) ** 2 * a[0] + 2 * t * (1 - t) * mx + t ** 2 * b[0]
    cy_ = (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * my + t ** 2 * b[1]
    sd.line([(x * 3, y * 3) for x, y in zip(cx_, cy_)], fill=255, width=3)
    sd.ellipse((a[0] * 3 - 9, a[1] * 3 - 9, a[0] * 3 + 9, a[1] * 3 + 9), fill=255)
    sd.ellipse((b[0] * 3 - 7, b[1] * 3 - 7, b[0] * 3 + 7, b[1] * 3 + 7), fill=255)
s_ = np.asarray(strand.resize((W, H), Image.LANCZOS), np.float32) / 255
glow = gblur(s_, 4)
rgb = 1 - (1 - np.clip(rgb, 0, 1)) * (1 - np.clip(glow[..., None] * GOLD * 0.9, 0, 1))
rgb = comp(rgb, s_, GOLD * 1.05)

rgb *= np.clip(1.12 - (dist / 1000) ** 2 * 0.75, 0, 1.15)[..., None]

# type: light, wide spaced, on the black
fnt = font(F + "segoeuil.ttf", 112)
x = 330.0
for ch in "CDK20":
    spr = type_sprite(ch, fnt, pad=2)
    rgb = paste_sprite(rgb, spr, x + spr.width / 2, 346, np.array([1, 1, 1], np.float32))
    x += spr.width + 64
lab = type_sprite(LABEL, font(F + "segoeui.ttf", 23), pad=2)
rgb = paste_sprite(rgb, lab, 642, 425, np.array([1, 1, 1], np.float32))
finish(rgb, "c3_death_stranding_black_rain.png")
