"""HKBU SCIE1007 coursework science video. Style scout a1, constructivism: the real CDK20 surface as a black mass, a red beam prints only what it hits."""
from kit import *

cream, red, blk = (235, 222, 192), (208, 30, 20), (17, 15, 14)
AP = (-70, 610)  # beam apex, off the corner


def ray(deg, x):
    return AP[1] - (x - AP[0]) * np.tan(np.radians(deg))


LOW, UP = 6.5, 39.0
beam = Layer().poly([AP, (1500, ray(LOW, 1500)), (1500, ray(UP, 1500))]).a()

R = rot(rz=-20) @ base_view()
V = view(R, scale=13.6, cx=770, cy=250, ss=0.6, L=(-0.72, -0.5, 0.48), L2=(0.6, 0.7, 0.3))
m = V["mask"]
tone = np.clip(0.04 + 1.15 * V["key"] ** 0.8 + 0.12 * V["rim"], 0, 1) * (0.35 + 0.65 * V["ao"])

c = paper(cream, 3, mott=0.012, fibre=0.016)
# red plate, printed a hair off register, ink slightly starved
ink_tex = 0.965 + 0.035 * np.clip(noise(s=1.2, seed=5), -2, 2)
hot = smooth(tone, 0.70, 0.74) * m  # brightest forms burn through to bare paper
red_cov = np.roll(np.roll(beam * (1 - hot), 2, 0), -2, 1) * ink_tex
red_cov[:3] = red_cov[3]
red_cov[:, -3:] = red_cov[:, -4:-3]
c = ink(c, np.clip(red_cov, 0, 1), red)

# black plate
dots = halftone(np.clip(1.08 - tone * 1.5, 0, 1) ** 1.05, cell=6.5, ang=45)
blk_cov = m * ((1 - beam) + beam * dots)

# lower wedge of paper stays clean so the type can climb out of the corner
clean = Layer().poly([AP, (1500, ray(LOW, 1500)), (1500, 900), AP]).a()
blk_cov = blk_cov * (1 - clean)

# type: flat baseline, top edge on the beam ray, letters grow toward the light's far end
L = Layer()
base = 706
x = 196
word = "CDK20"
ws = [128, 156, 196, 240, 280]
gap = 15
for ch, wd in zip(word, ws):
    x0, x1 = x, x + wd

    def T(u, v, x0=x0, x1=x1):
        px = x0 + (x1 - x0) * u
        top = ray(LOW, px) + 11
        return px, top + (base - top) * v

    for s, pl in glyph_pts(ch, T):
        L.poly(pl, 255 if s > 0 else 0)
    x += wd + gap
blk_cov = np.maximum(blk_cov, L.a())

# lamp in the corner, ring, rules that run on the beam axis
lamp = Layer().ell(-178, 432, 178, 788).a()
ring = Layer().ell(-104, 506, 104, 714).a()
ring2 = Layer().ell(-62, 548, 62, 672).a()
blk_cov = np.maximum(blk_cov, lamp)
blk_cov = blk_cov * (1 - ring)
c = ink(c, ring * (1 - ring2), red)
blk_cov = np.maximum(blk_cov, ring2)

# label: a black slat lying on the upper beam edge
a = np.radians(UP)
slat = Layer()
sx, sy = 150, ray(UP, 150)
ln, th = 440, 33
dx, dy = np.cos(a), -np.sin(a)
nx, ny = np.sin(a), np.cos(a)
slat.poly([(sx, sy), (sx + dx * ln, sy + dy * ln), (sx + dx * ln - nx * th, sy + dy * ln - ny * th), (sx - nx * th, sy - ny * th)])
slat_a = slat.a()
blk_cov = np.maximum(blk_cov, slat_a)
mx, my = sx + dx * ln / 2 - nx * th / 2, sy + dy * ln / 2 - ny * th / 2
txt = text_rot("AlphaFold DB v6 · predicted", "arialbd.ttf", 24, UP, mx, my, track=0.5)

c = ink(c, np.clip(blk_cov, 0, 1) * (0.985 + 0.015 * ink_tex), blk)
c = ink(c, txt, cream)
save(c, "a1_constructivism.png")
