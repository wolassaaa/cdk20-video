"""HKBU SCIE1007 coursework science video. Style scout c8: sacred geometry that is real data. The rose window is CDK20's own residue contact map, the ticks are real pLDDT, the protein is the relic at its centre. Method only."""
from common import *

GOLD, IV, COR = hexrgb("#E2B95E"), hexrgb("#F7F1E3"), hexrgb("#FF5A3C")
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
CX, CY, RR = 640.0, 360.0, 342.0
dist = np.hypot(xx - CX, yy - CY)
rgb = (hexrgb("#0C3A3B")[None, None] * np.clip(1.15 - dist / 760, 0, 1)[..., None]) + hexrgb("#030D10")

SS = 3
ca, conf, atoms = read_pdb()
n_ = len(ca)
th = -math.pi / 2 + np.arange(n_) * 2 * math.pi / n_
rx, ry = CX + RR * np.cos(th), CY + RR * np.sin(th)

# contact map as string art: every residue pair closer than 8 A, Calpha to Calpha, |i-j| > 3
D = np.linalg.norm(ca[:, None] - ca[None], axis=-1)
I, J = np.where(np.triu(D < 8.0, 4))
print("contacts", len(I))
acc = np.zeros((H * SS, W * SS), np.float32)
for i, j in zip(I, J):
    x0, y0, x1, y1 = rx[i], ry[i], rx[j], ry[j]
    L = int(math.hypot(x1 - x0, y1 - y0) * SS * 1.2) + 2
    t = np.linspace(0, 1, L)
    px = ((x0 + (x1 - x0) * t) * SS).astype(int)
    py = ((y0 + (y1 - y0) * t) * SS).astype(int)
    ok = (px >= 0) & (px < W * SS) & (py >= 0) & (py < H * SS)
    np.add.at(acc, (py[ok], px[ok]), 1.0)
acc = np.asarray(Image.fromarray(acc).resize((W, H), Image.BOX), np.float32)
acc = gblur(acc, 0.5)
a_ = np.clip(acc / np.percentile(acc[acc > 0], 97), 0, 1) ** 0.9
# a sun fills the ring: light at the centre, gold at the rim, the contact map drawn dark across it like leading in a window
disc = np.clip((RR - dist) * 1.0, 0, 1)
sun_col = np.zeros((H, W, 3), np.float32)
tt = np.clip(dist / RR, 0, 1) ** 1.6
for ch in range(3):
    sun_col[..., ch] = np.interp(tt, [0, 0.55, 0.85, 1.0], [hexrgb(c_)[ch] for c_ in ("#FFFDF4", "#FBEBC4", "#EDBE62", "#D38F2F")])
rgb = comp(rgb, disc, sun_col)
rgb = comp(rgb, a_ * 0.9, hexrgb("#07282C"))


# geometry: strict left-right symmetry, line only
def circle(cx, cy, r, step=1400):
    t = np.linspace(0, 2 * math.pi, step)
    x, y = cx + r * np.cos(t), cy + r * np.sin(t)
    return [(x[k], y[k], x[k + 1], y[k + 1]) for k in range(step - 1)]


def poly(pts):
    return [(pts[k][0], pts[k][1], pts[(k + 1) % len(pts)][0], pts[(k + 1) % len(pts)][1]) for k in range(len(pts))]


def ngon(n, r, rot=-math.pi / 2, cx=CX, cy=CY):
    return [(cx + r * math.cos(rot + k * 2 * math.pi / n), cy + r * math.sin(rot + k * 2 * math.pi / n)) for k in range(n)]


fine, med = [], []
for r in (RR + 12, RR + 26, RR + 92, RR + 210, RR + 440):
    fine += circle(CX, CY, r, 2400)
for r2 in (RR + 2, RR + 40):
    med += circle(CX, CY, r2, 2400)
med += poly(ngon(3, RR + 330)) + poly(ngon(3, RR + 330, math.pi / 2))
fine += poly(ngon(6, RR + 26)) + poly(ngon(6, RR + 26, 0)) + poly(ngon(12, RR + 92, -math.pi / 2))
# vesica: a giant eye across the whole frame, built from two circles
for s_ in (-1, 1):
    med += circle(CX, CY + s_ * 760, 1090, 3000)
# axis with rhombus nodes
fine += [(0, CY, CX - RR - 26, CY), (CX + RR + 26, CY, W, CY)]
fine += [(CX, 0, CX, CY - RR - 26), (CX, CY + RR + 26, CX, H)]
for dx in (440, 560):
    for s_ in (-1, 1):
        x = CX + s_ * dx
        med += poly([(x, CY - 34), (x + 15, CY), (x, CY + 34), (x - 15, CY)])
# satellite discs, mirrored, sizes from the same ratio
for dx, dy, r in [(486, -212, 56), (486, 212, 56), (360, -300, 34), (360, 300, 34)]:
    for s_ in (-1, 1):
        fine += circle(CX + s_ * dx, CY + dy, r, 600)
        fine += circle(CX + s_ * dx, CY + dy, r * 0.62, 400)
        fine += poly(ngon(3, r, -math.pi / 2 if dy < 0 else math.pi / 2, CX + s_ * dx, CY + dy))
rgb = comp(rgb, lines_mask(fine, 0.8) * 0.75, GOLD)
rgb = comp(rgb, lines_mask(med, 1.3), GOLD)

# real pLDDT ticks around the rim. Below 0.7 they turn coral.
tk_g, tk_c = [], []
for i, c in enumerate(conf):
    a = th[i]
    r0, r1 = RR + 4, RR + 4 + 7 + 12 * c
    seg = (CX + r0 * math.cos(a), CY + r0 * math.sin(a), CX + r1 * math.cos(a), CY + r1 * math.sin(a))
    (tk_c if c < 0.7 else tk_g).append(seg)
rgb = comp(rgb, lines_mask(tk_g, 1.1), IV)
rgb = comp(rgb, lines_mask(tk_c, 2.0), COR)

# relic: real surface, ivory in light, gold in the turn, teal black in shadow
Q = warp(load(), zoom=0.66, cx=955, cy=525, rot=0.0, ox=CX, oy=CY)
n, m, ao, conf_p = Q["normal"], Q["mask"], Q["ao"], Q["conf"]
hard = gblur((m > 0.5).astype(np.float32), 0.6)
halo = np.clip(gblur((m > 0.5).astype(np.float32), 9) * 1.5, 0, 1)
L = np.array([-0.2, 0.75, 0.63], np.float32)
t = np.clip((n * L).sum(-1) * 0.5 + 0.5, 0, 1)
t = t * (0.3 + 0.7 * np.clip(ao * 1.3 - 0.2, 0, 1))
pal = [(0.0, "#020B0E"), (0.30, "#062226"), (0.52, "#0F4A4C"), (0.70, "#7E5C22"), (0.84, "#E2B95E"), (1.0, "#FFF6DC")]
out = np.zeros((H, W, 3), np.float32)
for ch in range(3):
    out[..., ch] = np.interp(t, [p[0] for p in pal], [hexrgb(p[1])[ch] for p in pal])
tail = gblur(((conf_p < 0.7) & (m > 0.5)).astype(np.float32), 0.8)
out = comp(out, tail, np.clip(out * np.array([1.0, 0.42, 0.28], np.float32) * 1.25 + COR * 0.12, 0, 1))
# thin gold engraving of depth bands across the surface
depth_lines = np.abs(np.sin(Q["depth"] * 210)) < 0.05
out = comp(out, gblur(depth_lines.astype(np.float32), 0.4) * hard * 0.35, hexrgb("#05181C"))
# the sun wraps round the edge of the form, so the lobes stay readable against it
wrap = np.clip(1 - n[..., 2], 0, 1) ** 6 * np.clip((n * np.array([0.1, 0.8, 0.3], np.float32)).sum(-1) + 0.75, 0, 1)
out = out + wrap[..., None] * hexrgb("#F4C565") * 1.5
rgb = comp(rgb, hard, np.clip(out, 0, 1))

# the name stands on both sides of the relic
f = font(F + "GOTHIC.TTF", 118)
for txt, x in [("CDK", 136), ("20", 1144)]:
    spr = type_sprite(txt, f, pad=6)
    sh = np.zeros((H, W, 3), np.float32)
    lay = paste_sprite(np.zeros((H, W, 3), np.float32), spr, x, CY - 4, np.ones(3, np.float32))[..., 0]
    rgb = comp(rgb, np.clip(gblur(lay, 7) * 2.6, 0, 1), hexrgb("#041A1D"))
    rgb = paste_sprite(rgb, spr, x, CY - 4, IV)
lab = type_sprite(LABEL, font(F + "segoeuib.ttf", 23), pad=2)
rgb = paste_sprite(rgb, lab, 176, 686, IV)
lb2 = type_sprite("ring: real residue contacts", font(F + "segoeuib.ttf", 23), pad=2)
rgb = paste_sprite(rgb, lb2, 1104, 686, IV)
finish(rgb, "c8_destiny_sacred_geometry.png")
