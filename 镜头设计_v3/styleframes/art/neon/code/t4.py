"""HKBU SCIE1007 coursework science video. T4 of the neon street direction: the first time CDK20 is seen. The real surface is a sign over the street.
Every tube is traced from the real mesh: outline, height contours, and the low-confidence region (pLDDT below 0.7) in broken tube. Pressed steel behind carries the real relief."""
import time

from nk import *

t0 = time.time()
SW, SH = 1500, 1180
ang = [float(v) for v in (sys.argv[1:4] or (-14, 8, 0))]
cache = WORK / ("t4_%g_%g_%g.npz" % tuple(ang))
if cache.exists():
    P = dict(np.load(cache))
    P["zmin"], P["zmax"] = float(P["zmin"]), float(P["zmax"])
else:
    P = smooth_pass(render(rot(*ang), 18.5, SW / 2 - 10, SH / 2 + 4, w=SW, h=SH, ss=2, S=surface()), 2.0)
    np.savez(cache, **{k: v for k, v in P.items() if k != "res"})
m, z, nrm, conf = P["mask"], P["z"], P["n"], P["conf"]
print("render", time.time() - t0)
mS = gauss(m, 8)
ms = mS > 0.5
f = gauss(z * m, 7.0) + 40 * (1 - mS)

low = gauss((conf < 0.7).astype(np.float32) * m, 8) > 0.42


def is_low(p):
    i = np.clip(p[:, 1].astype(np.int32), 0, SH - 1)
    j = np.clip(p[:, 0].astype(np.int32), 0, SW - 1)
    return low[i, j]


# outline
out_loops = tube_loops(ms, 10)
inset = gauss(ms.astype(np.float32), 13) > 0.8
in_loops = tube_loops(inset, 10)
# height contours, like the lines on a map of a place nobody has walked
lines = []
for lv in np.arange(P["zmin"] + 7, P["zmax"], 3.3):
    lines += tube_loops((f > lv) & inset, 7, 90)

wh = (SW, SH)
sil_hi = draw_tube(wh, out_loops, 7, value=lambda p: ~is_low(p), closed=True)
sil_lo = draw_tube(wh, out_loops, 7, dash=(30, 15), value=is_low)
in_hi = draw_tube(wh, in_loops, 4, value=lambda p: ~is_low(p))
in_lo = draw_tube(wh, in_loops, 4, dash=(22, 13), value=is_low)
con_hi = draw_tube(wh, lines, 4, value=lambda p: ~is_low(p))
con_lo = draw_tube(wh, lines, 4, dash=(16, 12), value=is_low)
print("tubes", time.time() - t0)

em = neon(sil_hi, PINK, 0.72, 0.7) + neon(in_hi, CYN, 0.8, 0.6) + neon(con_hi, GRN, 0.74, 0.6)
em = em + neon(sil_lo, AMB, 0.8, 0.7) + neon(in_lo, RED, 0.8, 0.6) + neon(con_lo, RED, 0.74, 0.6)

# pressed steel: the real surface as a dim relief, lit only by its own tubes
msf = gauss(ms.astype(np.float32), 1.2)
L1 = np.array([-0.55, 0.65, 0.5])
L1 /= np.linalg.norm(L1)
sh = np.clip(nrm @ L1, 0, 1) * m
sh = np.clip(gauss(sh, 1.6), 0, 1)
glow = gauss(em, 34)
panel = (np.array([0.02, 0.014, 0.026], np.float32) + (0.06 + 2.6 * sh ** 1.5)[..., None] * (glow * 0.9 + 0.035)) * msf[..., None]
# rivet seams of the sheet metal
sm = (((np.arange(SW) % 240) < 3)[None, :] | ((np.arange(SH) % 240) < 3)[:, None]).astype(np.float32)
panel = panel * (1 - 0.5 * sm[..., None])

# ---- the street
vp = (1500, 610)
plate = street_cached(vp, seed=12, n=110, gain=1.0)
plate = building_mass(plate, vp)
# nearer signs, sharp, crowding the frame edges
near = [(1390, 30, 130, 400, "茶餐廳", GRN, 1), (1536, 8, 120, 270, "涼茶", PINK, 1), (1672, 60, 110, 110, "押", RED, 1), (1672, 186, 110, 230, "粥麵", CYN, 1),
        (1796, 20, 124, 330, "燒臘", YEL, 1), (1796, 366, 124, 230, "冰室", PINK, 1), (1536, 296, 120, 250, "配匙", AMB, 1),
        (14, 640, 120, 300, "酒家", YEL, 1), (14, 8, 96, 240, "金行", AMB, 1), (1000, 2, 180, 96, "押", RED, 1), (150, 2, 120, 96, "士多", CYN, 1)]
for x, y, ww, hh, wd, col, _ in near:
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    dr.rectangle((x, y, x + ww, y + hh), outline=255, width=5)
    dr.rectangle((x + 11, y + 11, x + ww - 11, y + hh - 11), outline=110, width=2)
    sz = int(min(ww * 0.7, hh * 0.86 / len(wd)))
    fn = nfont(sz, "Bold")
    for j, ch in enumerate(wd):
        dr.text((x + ww / 2, y + (j + 0.5) * hh / len(wd)), ch, 255, font=fn, anchor="mm")
    t = np.asarray(im, np.float32) / 255
    box = ((xx > x) & (xx < x + ww) & (yy > y) & (yy < y + hh)).astype(np.float32)
    plate = plate * (1 - box[..., None] * 0.86) + box[..., None] * col * 0.05
    plate = plate + neon(gauss(t, 0.9), col, 0.5, 0.16)

# hang the sign: looking up at it from the road, it leans over the street
q = [(-36, -60), (1336, 8), (1326, 950), (-36, 1016)]
wp, ins = warp(panel, q, SW, SH)
wem, _ = warp(em, q, SW, SH)
wms, _ = warp(msf, q, SW, SH)
wsharp = wms
img = plate * (1 - gauss(wms, 1.0)[..., None] * 0.97) + wp + wem

# steel stays to the wall
st = Image.new("L", (W, H), 0)
dr = ImageDraw.Draw(st)
for a, b in (((0, 150), (420, 210)), ((0, 640), (260, 610)), ((980, 0), (900, 120))):
    dr.line((a, b), fill=255, width=7)
st = np.asarray(st, np.float32) / 255 * (1 - gauss(wms, 1))
img = img * (1 - st[..., None] * 0.9) + st[..., None] * np.array([0.05, 0.045, 0.05], np.float32)

# the road
wy = 952
img = wet_road(img, wy, 0.95)

# the people underneath: a few, looking up, very small next to the sign
pm = Image.new("L", (W * 3, H * 3), 0)
pd = ImageDraw.Draw(pm)
for px, hh, ph, fl in ((1120, 128, True, 1), (1176, 118, False, -1), (1262, 112, False, 1), (1440, 134, True, -1), (1508, 104, False, 1), (960, 98, False, -1), (1640, 92, False, 1)):
    person(pd, px, wy + 8, hh, 3, ph, fl)
pm = np.asarray(pm.resize((W, H), Image.LANCZOS), np.float32) / 255
rimw = np.clip(pm - gauss(pm, 2.2), 0, 1) * 2.2
img = img * (1 - pm)[..., None] + pm[..., None] * np.array([0.015, 0.012, 0.016], np.float32) + rimw[..., None] * np.array([1.0, 0.35, 0.5], np.float32) * 0.9
# their shadows reach toward the lens along the wet road
sh2 = np.zeros((H, W), np.float32)
for i in range(1, 30):
    sh2 = np.maximum(sh2, sample(pm, xx, wy + 16 - (yy - wy - 16) / (0.08 * i)) * (1 - i / 30))
img = img * (1 - 0.5 * sh2 * (yy > wy))[..., None]

# the one label on this shot is made like the sign it names: line, not lightbox
tx, ty = 1160, 1040
m_lab = text(LABEL, 44, (W - 70, 1034), "Light", "rs", 1)
tw = text_w(LABEL, 44, "Light", 1)
box = Image.new("L", (W, H), 0)
ImageDraw.Draw(box).rounded_rectangle((W - 70 - tw - 36, 972, W - 34, 1058), radius=26, outline=255, width=4)
box = np.asarray(box, np.float32) / 255
back = gauss((((xx > W - 70 - tw - 36) & (xx < W - 34) & (yy > 972) & (yy < 1058))).astype(np.float32), 2)
img = img * (1 - 0.86 * back)[..., None]
img = img + neon(gauss(box, 0.7), CYN, 0.85, 0.3)
img = img * (1 - m_lab)[..., None] + m_lab[..., None] * rgb("#E8FBFF")
img = img + gauss(m_lab, 3)[..., None] * CYN * 0.6
finish(img, "T4.png")
print("done", time.time() - t0)
