"""HKBU SCIE1007 coursework science video. Style scout f5: one hue, one fog. Everything is computed as luminance and pushed through a single amber ramp, so nothing but the fog gives depth."""
from fx import *

d = np.load(WORK / "world_f5.npz")
beauty, z, ids = d["beauty"], d["z"], np.round(d["id"])
L0 = beauty @ np.array([0.3, 0.6, 0.1], np.float32)
yy, xx = np.mgrid[:H, :W].astype(np.float32)
prot = gauss((ids == 2).astype(np.float32), 0.6)
sand = (ids == 1).astype(np.float32)
sky = (ids == 0).astype(np.float32)

# fog luminance: hot and pale where the sun is drowning behind the object, falling away to the edges
sx, sy = 880.0, 170.0
fogL = 0.52 + 0.34 * np.exp(-(((xx - sx) / 620) ** 2 + ((yy - sy) / 340) ** 2)) - 0.10 * (yy / H)
fogL = fogL - 0.16 * smooth(0.5, 1.15, np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)))

T = 0.8 * np.exp(-np.maximum(z - 23.5, 0) / 7.5)  # transmittance: the far lobes of the object are lost in the air
surf = np.clip(L0, 0, 2) * 0.16 + 0.015
img = fogL * sky
img = img + (surf * T + fogL * (1 - T)) * (prot + sand * 0) * (1 - sky)
# sand: dark near the lens, sinking into the same fog, its detail only a whisper
Tg = np.exp(-np.maximum(z - 3, 0) / 15.0)
sandL = (0.13 + 0.14 * np.clip(L0, 0, 1)) * Tg + fogL * (1 - Tg)
img = img * (1 - sand) + sandL * sand * (1 - prot) + img * sand * prot

# the title stands in the desert as a dead sign, each letter further into the fog than the last
f = font("bahnschrift.ttf", 300)
try:
    f.set_variation_by_name("Bold Condensed")
except Exception:
    pass
base = 618
xs = [70, 318, 560, 820, 1032]
T_ls = [0.92, 0.78, 0.64, 0.52, 0.42]
for ch, x, Tl in zip("CDK20", xs, T_ls):
    m = text_mask(ch, f, (x, base - 18 * (1 - Tl)), 0)
    m = np.minimum(m, 1 - smooth(base - 20 * (1 - Tl) - 4, base - 20 * (1 - Tl), yy) * 0.0)
    # letter is lit a little on the sun side
    letterL = 0.03 * Tl + fogL * (1 - Tl)
    img = img + gauss(m, 15) * (fogL - img) * 0.62  # fog gathers round each letter and lifts it off the object behind
    img = mix(img, letterL, m)

# one person, the only hard black in the frame, with a long soft shadow toward the lens
SS = 4
pp = Image.new("L", (W * SS, H * SS), 0)
dr = ImageDraw.Draw(pp)
px, py, ph = 698.0, 650.0, 62.0


def T_(pts):
    return [((px + a * ph) * SS, (py - b * ph) * SS) for a, b in pts]


dr.polygon(T_([(-0.06, 0.0), (-0.11, 0.0), (-0.085, 0.45), (-0.13, 0.82), (-0.09, 0.86), (0.09, 0.86), (0.13, 0.82), (0.085, 0.45), (0.11, 0.0), (0.06, 0.0), (0.0, 0.42)]), fill=255)
dr.polygon(T_([(-0.13, 0.82), (-0.17, 0.46), (-0.135, 0.45), (-0.09, 0.74)]), fill=255)
dr.polygon(T_([(0.13, 0.82), (0.17, 0.46), (0.135, 0.45), (0.09, 0.74)]), fill=255)
dr.ellipse([(px - 0.062 * ph) * SS, (py - ph * 1.0) * SS, (px + 0.062 * ph) * SS, (py - ph * 0.87) * SS], fill=255)
man = np.asarray(pp.resize((W, H), Image.LANCZOS), np.float32) / 255
# shadow: the figure smeared toward the camera
sh = np.zeros((H, W), np.float32)
for i in range(1, 60):
    s = 1 + i * 0.07
    my = (yy - py) / (-s * 0.6) + py
    mx = (xx - px + (yy - py) * 0.55) + px
    sh = np.maximum(sh, sample(man, mx, my) * (1 - i / 60) ** 1.5)
img = img * (1 - 0.5 * gauss(sh, 1.6))
img = mix(img, 0.012, man)

# air: a very wide veil over everything, lifted by the bright sun side
veil = gauss(img, 40) * 0.35
img = img * 0.8 + veil * 0.57
img = img + gauss(np.clip(img - 0.62, 0, 1), 30) * 0.6

# single ramp. Black, burnt, amber, pale. Hue never moves
stops = np.array([0.0, 0.1, 0.28, 0.5, 0.72, 1.0], np.float32)
cols = np.stack([rgb(c) for c in ("#0B0300", "#3C1200", "#9C3400", "#E8640A", "#FFA133", "#FFE2A0")])
t = np.clip(img, 0, 1)
out = np.stack([np.interp(t.ravel(), stops, cols[:, i]).reshape(t.shape) for i in range(3)], -1).astype(np.float32)

lab = font("bahnschrift.ttf", 23)
lm = text_mask(LABEL, lab, (72, 690), 2.2)
out = mix(out, rgb("#FFE9BE"), lm)
save(out, OUT / "f5_monofog.png")
print("ok")
