"""HKBU SCIE1007 coursework science video. d2 style test: heavy ink with high saturation. Spotted blacks with wedge feathering, flat hot colour, the real CDK20 surface at a violent tilt."""
from t import *

W, H = 1280, 720
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
Q = view(W, H, zoom=1.42, rot=-24, at=(0.655, 0.53), c=(0.5, 0.48))
m = Q["mask"]
mb = m > 0.5

# Backdrop: flat crimson with inked flame tongues climbing from the lower left
warpx = (fbm(H, W, 170, 3, 4) - 0.5) * 240
warpy = (fbm(H, W, 170, 3, 9) - 0.5) * 240
u = (xx + warpx) / 1280
v = (yy + warpy + xx * 0.32) / 720
fl = np.sin(u * 15 + fbm(H, W, 120, 2, 2) * 7) * 0.5 + 0.5
heat = np.clip(0.80 - (1.1 - v) * 1.36 + (fl - 0.5) * 0.78, 0, 1)
rgb = ramp(heat, [(0, "#0d0309"), (0.50, "#0d0309"), (0.505, "#4a0628"), (0.70, "#4a0628"), (0.705, "#c20f3c"), (0.88, "#c20f3c"), (0.885, "#ff8a1e"), (0.97, "#ff8a1e"), (0.975, "#ffe14a")])

# Hard radial burst behind the form, gold blades on the upper right
cx, cy = 800, 330
a = np.arctan2(yy - cy, xx - cx)
r = np.hypot(xx - cx, yy - cy)
blade = (np.sin(a * 23 + 1.3 * np.sin(a * 5)) > 0.45 + (r - 200) / 900) & (r < 660) & (heat < 0.7)
rgb = np.where(blade[..., None], hexc("#7a0a33") * 0.6 + rgb * 0.4, rgb)

# Heavy contour: the silhouette grown far more on the shadow side
sil = gauss((m > 0.5).astype(np.float32), 2)
shadow = np.zeros((H, W), bool)
for k in range(0, 27, 3):
    shadow |= np.roll(np.roll(sil > 0.5, k + 2, 0), -k - 2, 1)
rgb[shadow] = hexc("#0b0408")

# Light: hot key from the upper right, a colder kicker from the lower left
key = lit(Q, (0.62, 0.70, -0.42), 0.0)
kick = lit(Q, (-0.86, -0.42, -0.16), 0.0)
ao = np.clip(Q["ao"], 0, 1)
NN = dict(Q)
NN["normal"] = gauss(Q["normal"], 16)
big = lit(NN, (0.62, 0.70, -0.42), 0.0)
s = (0.55 * key + 0.45 * big * 1.5) * (0.42 + 0.58 * ao ** 1.3) * (0.35 + 0.95 * np.clip(big * 2.0, 0, 1))

# Wedge feathering: the shadow edge is cut into ink spikes running along the light direction
t = (xx * 0.74 - yy * 0.67) + (fbm(H, W, 90, 2, 12) - 0.5) * 70
saw = np.abs(((t / 13) % 1) - 0.5) * 2
dv = fbm(H, W, 120, 3, 31)
thr = 0.26 + (saw - 0.5) * 0.26 + (dv - 0.5) * 0.15
ink = s < thr

tail = np.clip((0.72 - gauss(Q["conf"], 1.5)) / 0.08, 0, 1) * mb  # real low confidence region
base = ramp(np.clip(s, 0, 1), [(0, "#c20f3c"), (0.44, "#e8123f"), (0.70, "#ff2f3f"), (0.705, "#ffb51e"), (1, "#ffe14a")])
cold = ramp(np.clip(s, 0, 1), [(0, "#0a6a78"), (0.5, "#12b5a8"), (0.70, "#14c6b4"), (0.705, "#c8ffe0"), (1, "#e8fff0")])
col = base * (1 - tail[..., None]) + cold * tail[..., None]
col = np.where(ink[..., None], hexc("#0b0408"), col)

# Cold kicker as a flat razor band that never touches the spotted blacks
band = (kick > 0.86) & (ao > 0.30)
band &= gauss(Q["mask"], 9) < 0.93
col = np.where(band[..., None], hexc("#ff3fa0"), col)
sp = (s > 0.93)
col = np.where(sp[..., None], hexc("#fff6c8"), col)

# Lines: thick at creases, swelling with shade
e, gz, gn = edges(Q, dz=0.0028, dn=0.17)
wid = 1.7 + 3.2 * (1 - np.clip(s * 1.5, 0, 1))
line = gauss(e.astype(np.float32), 1.4) * 2.6 * wid / 2.5 > 0.42
line &= mb
col = np.where(line[..., None], hexc("#0b0408"), col)
rgb = rgb * (1 - m[..., None]) + col * m[..., None]
hard = gauss(((m > 0.35) & (m < 0.95)).astype(np.float32), 1.6) > 0.25
rgb[hard] = hexc("#0b0408")

# Embers
r0 = np.random.default_rng(5)
em = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(em)
for i in range(150):
    x, y = r0.uniform(0, W), r0.uniform(120, H)
    L = r0.uniform(5, 34)
    w = r0.uniform(2, 6)
    p = [(x, y), (x + L * 0.5 + w, y - L * 0.6), (x + L * 1.1, y - L * 1.2), (x + L * 0.5 - w, y - L * 0.5)]
    d.polygon(p, fill=255)
em = np.asarray(em, np.float32) / 255
em *= ~(sil > 0.3)
rgb = over(rgb, hexc("#ffdb4a"), em)

# Type: tall, flat, cut by one slash. No gradient: one gold, one black.
S = 2
tw = Image.new("L", (W * S, H * S), 0)
dt = ImageDraw.Draw(tw)
dt.text((34 * S, 8 * S), "CDK20", fill=255, font=font("impact.ttf", 262 * S))
tw = tw.rotate(4.5, Image.BICUBIC, center=(0, 0))
sh = 0.16
tw = tw.transform(tw.size, Image.AFFINE, (1, sh, -sh * 100 * S, 0, 1, 0), Image.BILINEAR)
tw = tw.resize((W, H), Image.LANCZOS)
T = np.asarray(tw, np.float32) / 255
slash = np.abs((yy - 150) - (xx - 300) * -0.16) < 3.5
T2 = T * ~slash
rim = np.zeros((H, W), np.float32)
for k in range(1, 24, 2):
    rim = np.maximum(rim, np.roll(np.roll(T, k, 0), -k // 2, 1))
fat = gauss(T, 2.2) > 0.05
rgb = over(rgb, hexc("#0b0408"), np.maximum(rim, fat.astype(np.float32)))
rgb = rgb * (1 - T2[..., None]) + hexc("#ffd23c") * T2[..., None]
tt = np.clip(T2 * ((yy - 118 - (xx - 300) * -0.16) > 0), 0, 1)
rgb = over(rgb, hexc("#ff2f3f"), tt * ((xx - 1.25 * yy) % 13 < 5.5) * ((yy > 200)))

# Label, flat black tag with hot edge
tag = np.zeros((H, W), bool)
tag[640:688, 40:488] = True
slant = (xx - 40 + (yy - 640) * 0.3 > 0) & (xx - 488 + (yy - 640) * 0.3 < 0)
tag &= slant
rgb[tag] = hexc("#0b0408")
rgb = over(rgb, hexc("#ffe14a"), text(W, H, LABEL, font("arialbd.ttf", 27), (66, 664), "lm"))
save(rgb, OUT / "d2_hades_ink.png")
