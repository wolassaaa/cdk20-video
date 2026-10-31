"""HKBU SCIE1007 coursework science video. T5 of the neon street direction: the key turns. The measured number is the only solid white lightbox in the film; the re-docking is a bulb sign, because it is ours.
Screen text is copied letter for letter. The pose comes from S2plus/public, recoloured only; the structure is untouched."""
import time

from nk import *

t0 = time.time()
PUB = ROOT / "styleframes/S2plus/public"
vp = (640, 560)
plate = street_cached(vp, seed=21, n=110, gain=0.95, tag="red2", pal=[RED, RED, PINK, AMB, RED, GRN])
plate = plate * [1.0, 0.72, 0.8] * 1.25

# ---- pose sign: pocket in tube, ligand in bulbs, marquee border. Same crop on both layers, they share one frame
PW, PH = 760, 880
pk = np.asarray(Image.open(PUB / "pose_048_grey.png").convert("RGBA").resize((1920, 2160), Image.LANCZOS), np.float32) / 255
lg = np.asarray(Image.open(PUB / "pose_048_lig.png").convert("RGBA").resize((1920, 2160), Image.LANCZOS), np.float32) / 255
ca = pk[..., 3] > 0.5
ys, xs = np.nonzero(ca)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
k = min((PW - 130) / (x1 - x0), (PH - 240) / (y1 - y0))
cw, ch = int((x1 - x0) * k), int((y1 - y0) * k)


def fit(a):
    c = a[y0:y1, x0:x1]
    im = np.stack([np.asarray(Image.fromarray(c[..., i]).resize((cw, ch), Image.LANCZOS)) for i in range(4)], -1)
    o = np.zeros((PH, PW, 4), np.float32)
    ox, oy = (PW - cw) // 2, (PH - 130 - ch) // 2 + 6
    o[oy:oy + ch, ox:ox + cw] = im
    return o


pk, lg = fit(pk), fit(lg)
pa = pk[..., 3]
pl = pk[..., 0]
wh = (PW, PH)
# pocket: outline tube and tone contours, the same line language as the predicted protein
loops = tube_loops(gauss(pa, 3) > 0.5, 7, 60)
sil = draw_tube(wh, loops, 4)
fl = gauss(pl * pa, 5)
inner = []
for lv in (0.22, 0.34):
    inner += tube_loops((fl > lv) & (gauss(pa, 6) > 0.8), 5, 60)
con = draw_tube(wh, inner, 2)
em = neon(sil, CYN, 0.8, 0.45) + neon(con, CYN, 0.45, 0.35)
back = np.array([0.012, 0.016, 0.03], np.float32) + (pl * pa)[..., None] * np.array([0.05, 0.10, 0.2], np.float32)
sign = back * pa[..., None]

# ligand: bulbs on wire. Recolour only. Hot where the atoms are, warm wire where the bonds are
lgm = lg[..., 3]
lgl = lg[..., 0] * lgm
core = np.clip(lgl * 1.1, 0, 1)
bulb = core[..., None] * rgb("#FFE9B8") * 1.6 + gauss(core, 2.5)[..., None] * rgb("#FFB347") * 1.1 + gauss(core, 10)[..., None] * rgb("#FF8A1E") * 0.9 + gauss(core, 34)[..., None] * rgb("#FF7A10") * 0.5
sign = sign * (1 - lgm)[..., None] + em * (1 - lgm)[..., None] + bulb

# marquee border of separate bulbs: a dotted edge, not a tube and not a box
bm = np.zeros((PH, PW), np.float32)
BY, BX = np.mgrid[:PH, :PW].astype(np.float32)
pitch = 30
m_ = 24
pts = [(x, m_) for x in np.arange(m_, PW - m_ + 1, pitch)] + [(x, PH - m_ - 110) for x in np.arange(m_, PW - m_ + 1, pitch)]
pts += [(m_, y) for y in np.arange(m_, PH - m_ - 110, pitch)] + [(PW - m_ - ((PW - 2 * m_) % pitch), y) for y in np.arange(m_, PH - m_ - 110, pitch)]
d = Image.new("L", (PW * 2, PH * 2), 0)
dr = ImageDraw.Draw(d)
for x, y in pts:
    dr.ellipse((2 * x - 11, 2 * y - 11, 2 * x + 11, 2 * y + 11), fill=255)
bm = np.asarray(d.resize((PW, PH), Image.LANCZOS), np.float32) / 255

# OUR RE-DOCKING, made of the same bulbs: heavy letters resampled onto a dot grid
tm = text("OUR RE-DOCKING", 74, (PW / 2, PH - 44), "Black", "ms", 3, wh=wh)
pitch2 = 7.0
gy = ((BY % pitch2) - pitch2 / 2)
gx = ((BX % pitch2) - pitch2 / 2)
dots = np.exp(-(gx ** 2 + gy ** 2) / (2 * 1.9 ** 2))
cell_x = np.floor(BX / pitch2) * pitch2 + pitch2 / 2
cell_y = np.floor(BY / pitch2) * pitch2 + pitch2 / 2
on = sample(tm, cell_x, cell_y) > 0.5
txb = dots * on
glowt = txb + bm
sign = sign + glowt[..., None] * rgb("#FFEFC8") * 1.4 + gauss(glowt, 3)[..., None] * rgb("#FFB347") * 1.1 + gauss(glowt, 12)[..., None] * rgb("#FF8A1E") * 0.5

# hang it, sheet behind
face = np.ones((PH, PW), np.float32)
wp, ins = warp(sign, [(50, 26), (800, 86), (800, 868), (50, 908)], PW, PH)
wf = gauss(ins, 1.0)
img = plate * (1 - 0.95 * wf)[..., None] + wp + wf[..., None] * np.array([0.006, 0.007, 0.012], np.float32)

# ---- the lightbox. Everything measured in this film looks like this: a solid white face, black letters, no tube
LW, LH = 1120, 720
Q = [(838, 92), (1902, 18), (1902, 804), (838, 754)]
yb, xb = np.mgrid[:LH, :LW].astype(np.float32)
# fluorescent tubes behind the acrylic show as soft bands, and the box ages toward its edges
bands = 0.93 + 0.07 * np.cos(yb / LH * 2 * np.pi * 3.5) ** 2
edge = smooth(0, 90, np.minimum.reduce([xb, yb, LW - xb, LH - yb]))
lum = bands * (0.84 + 0.16 * edge)
face = lum[..., None] * rgb("#FFF7E6")
# red band at the foot, printed on the same acrylic
bandt = LH - 128
ins_b = (yb > bandt).astype(np.float32)
face = face * (1 - ins_b)[..., None] + ins_b[..., None] * rgb("#D6141C") * lum[..., None]
ink = rgb("#120C0A")
t1 = text("Enzyme IC50", 68, (60, 104), "Bold", "ls", wh=(LW, LH))
t2 = text("048 =", 132, (56, 256), "Black", "ls", wh=(LW, LH))
size = 180
while text_w("33.4 ± 22.6 nM", size, "Black", -2) > LW - 92:
    size -= 2
print("number size", size)
t3 = text("33.4 ± 22.6 nM", size, (LW / 2, 476), "Black", "ms", -2, wh=(LW, LH))
t4 = text("MEASURED · Ren 2023, Fig. 9A", 64, (LW / 2, LH - 44), "Bold", "ms", 1, wh=(LW, LH))
face = face * (1 - t1)[..., None] + ink * t1[..., None]
face = face * (1 - t2)[..., None] + ink * t2[..., None]
face = face * (1 - t3)[..., None] + ink * t3[..., None]
face = face * (1 - t4)[..., None] + rgb("#FFF7E6") * t4[..., None]
face_pad = np.pad(face, ((16, 16), (16, 16), (0, 0)), mode="constant", constant_values=0.028)
fw, ins2 = warp(face_pad, Q, LW + 32, LH + 32)
boxm = gauss(ins2, 0.7)
img = img * (1 - boxm)[..., None] + fw
# spill: the box lights the street around it, all white
spill = gauss(boxm, 40)[..., None] * rgb("#FFE6C4") * 0.55 + gauss(boxm, 130)[..., None] * rgb("#FFD6B0") * 0.45
img = img + spill * (1 - boxm)[..., None]
# brackets
st = Image.new("L", (W, H), 0)
dr = ImageDraw.Draw(st)
for a, b in (((1000, 0), (1000, 84)), ((1740, 0), (1740, 44)), ((240, 0), (240, 40)), ((640, 0), (640, 74))):
    dr.line((a, b), fill=255, width=9)
st = np.asarray(st, np.float32) / 255
img = img * (1 - st * 0.92)[..., None]

wy = 932
img = wet_road(img, wy, 0.92, seed=37, fall=240)
pm = Image.new("L", (W * 3, H * 3), 0)
pd = ImageDraw.Draw(pm)
for px, hh, ph, fl in ((1006, 104, False, 1), (1060, 112, False, -1), (1290, 118, True, 1), (1356, 100, False, -1), (1604, 92, False, 1), (210, 84, False, 1)):
    person(pd, px, wy + 7, hh, 3, ph, fl)
pm = np.asarray(pm.resize((W, H), Image.LANCZOS), np.float32) / 255
rimw = np.clip(pm - gauss(pm, 2.2), 0, 1) * 2.0
img = img * (1 - pm)[..., None] + pm[..., None] * 0.012 + rimw[..., None] * rgb("#FFE0C0") * 0.8

# a person's words stay subtitles
img = subtitle(img, ["Just this much cuts the enzyme's activity in half."], 1038, 52)
finish(img, "T5.png", 0.55)
print("done", time.time() - t0)
