"""HKBU SCIE1007 coursework science video. Style scout c6: red and black ripped layout, the real silhouette filled with splinters, cut-out letters. Method only."""
from common import *

rng = np.random.default_rng(5)
R, K, Wt = hexrgb("#E8001E"), hexrgb("#060606"), hexrgb("#F6F4EE")
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

# torn diagonal: red field, black wedge, jagged edge
rgb = np.ones((H, W, 3), np.float32) * R


def jag(x0, y0, x1, y1, n=26, amp=30, seed=0):
    r = np.random.default_rng(seed)
    t = np.sort(r.random(n))
    pts = []
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    for i, a in enumerate(t):
        o = amp * (1 if i % 2 else -1) * r.uniform(0.2, 1)
        pts.append((x0 + dx * a + nx * o, y0 + dy * a + ny * o))
    return pts


# big black torn slab from the top left, big white splinter band across
blk = [(-20, -20)] + [(560, -20)] + jag(560, -20, 150, 740, 22, 34, 1) + [(-20, 740)]
rgb = comp(rgb, poly_mask(blk), K)
band = jag(-30, 560, 1310, 40, 30, 15, 2) + jag(1310, 150, -30, 660, 30, 15, 3)
blk2 = jag(-30, 584, 1310, 64, 26, 7, 4) + jag(1310, 120, -30, 642, 26, 7, 5)

# halftone gradient in the red corner
th = 0.5
u = xx * math.cos(th) + yy * math.sin(th)
v = -xx * math.sin(th) + yy * math.cos(th)
d = np.hypot((u / 13) % 1 - .5, (v / 13) % 1 - .5)
grad = np.clip((xx + (H - yy) - 1250) / 760, 0, 1) * 0.72
rgb = comp(rgb, np.clip((grad - d) * 12, 0, 1), K)
grad2 = np.clip(((W - xx) * 0.0 + (yy - 200) * 0 + (820 - xx) * 0 + (260 - yy)) / 260, 0, 1) * np.clip((xx - 880) / 200, 0, 1) * 0.7
rgb = comp(rgb, np.clip((grad2 - d) * 12, 0, 1), hexrgb("#FFFFFF") * 0 + K)

# real silhouette, tilted hard, drop block behind it
Q = warp(load(), zoom=0.80, cx=950, cy=525, rot=-0.34, ox=770, oy=392)
n, m, ao = Q["normal"], Q["mask"], Q["ao"]
hard = (m > 0.5).astype(np.float32)
offs = np.roll(np.roll(gblur(hard, 0.6), 20, 1), 18, 0)
rgb = comp(rgb, offs, K)
off2 = np.roll(np.roll(gblur(hard, 0.6), -14, 1), -10, 0)
rgb = comp(rgb, off2 * (1 - offs), Wt)

# splinter fill: flat black and white shards cut by the real shading, each shard leans along the surface
L = np.array([-0.5, 0.65, 0.57], np.float32)
tone = np.clip((n * L).sum(-1) * 0.55 + 0.66, 0, 1) * (0.3 + 0.7 * np.clip(ao * 1.6 - 0.35, 0, 1))
# build shards from many thin triangles laid in rays from focal points
sh = Image.new("L", (W, H), 0)
ds = ImageDraw.Draw(sh)
foci = [(660, 330), (980, 240), (470, 500), (880, 560)]
for f in foci:
    for i in range(170):
        a = rng.uniform(0, 2 * math.pi)
        r0, r1 = rng.uniform(0, 80), rng.uniform(150, 640)
        w = rng.uniform(0.012, 0.05)
        pts = [(f[0] + r0 * math.cos(a - w), f[1] + r0 * math.sin(a - w)), (f[0] + r1 * math.cos(a), f[1] + r1 * math.sin(a)), (f[0] + r0 * math.cos(a + w), f[1] + r0 * math.sin(a + w))]
        ds.polygon(pts, fill=255)
sh = np.asarray(sh, np.float32) / 255
ink = np.zeros((H, W), np.float32)
t1, t2 = [float(np.percentile(tone[m > 0.5], p)) for p in (30, 64)]
ink = np.maximum(ink, (tone < t1).astype(np.float32))               # deep shadow is solid black
ink = np.maximum(ink, sh * ((tone >= t1) & (tone < t2)))          # mid tone is splintered
fill = np.ones((H, W, 3), np.float32) * Wt
fill = comp(fill, ink, K)
# a few lobes turn red, ripped out of the white
rrim = np.clip(((n * np.array([0.8, -0.3, 0.25], np.float32)).sum(-1) - 0.42) * 20, 0, 1) * (1 - ink)
fill = comp(fill, rrim, R)
hedge = gblur(hard, 0.6)
rgb = comp(rgb, hedge, fill)
# hard outline around the cut
out = np.clip(gblur(hard, 3.2) * 3 - 0.2, 0, 1) * (1 - hedge)
edge = np.clip(out, 0, 1)

# jagged accent splinters flying out of the form
for i in range(30):
    a = rng.uniform(-0.75, 0.75) if i % 2 else rng.uniform(2.4, 3.8)
    r0 = rng.uniform(330, 520)
    r1 = r0 + rng.uniform(60, 240)
    w = rng.uniform(.02, .05)
    x, y = 770, 392
    pts = [(x + r0 * math.cos(a - w), y + r0 * math.sin(a - w) * .72), (x + r1 * math.cos(a), y + r1 * math.sin(a) * .72), (x + r0 * math.cos(a + w), y + r0 * math.sin(a + w) * .72)]
    rgb = comp(rgb, poly_mask(pts), Wt if i % 3 else K)


# ransom letters: each glyph cut from a different scrap, different face, different tilt, scraps overlap
def scrap(rgb, ch, fn, size, x, y, rot, bg, fg, pad=14, sx=1.0, invert_shadow=True):
    spr = type_sprite(ch, font(fn, size), sx=sx, pad=pad)
    w, h = spr.size
    r = np.random.default_rng(int(x * 7 + y))
    box = [(r.uniform(0, 12), r.uniform(0, 10)), (w - r.uniform(0, 12), r.uniform(0, 10)), (w - r.uniform(0, 8), h - r.uniform(0, 12)), (r.uniform(0, 12), h - r.uniform(0, 10))]
    bim = Image.new("L", (w, h), 0)
    ImageDraw.Draw(bim).polygon(box, fill=255)
    rgb = paste_sprite(rgb, bim, x + 9, y + 10, Wt if np.mean(bg) < 0.4 else K, rot=rot)    # hard shadow
    rgb = paste_sprite(rgb, bim, x, y, bg, rot=rot)
    rgb = paste_sprite(rgb, spr, x, y, fg, rot=rot)
    return rgb


rgb = scrap(rgb, "C", FX + "ArchivoBlack-Regular.ttf", 236, 150, 170, 9, Wt, K)
rgb = scrap(rgb, "D", F + "impact.ttf", 300, 322, 196, -7, K, Wt)
rgb = scrap(rgb, "K", F + "georgiab.ttf", 214, 490, 120, 12, R, K)
rgb = scrap(rgb, "2", F + "cour.ttf", 250, 672, 148, -11, Wt, R)
rgb = scrap(rgb, "0", F + "ariblk.ttf", 214, 852, 142, 6, K, R)

# label on a torn strip, slanted
lab = type_sprite(LABEL, font(F + "arialbd.ttf", 26), pad=12)
strip = Image.new("L", (lab.width + 26, lab.height + 2), 255)
rgb = paste_sprite(rgb, strip, 1022, 678, Wt, rot=4)
rgb = paste_sprite(rgb, strip, 1012, 668, K, rot=4)
rgb = paste_sprite(rgb, lab, 1012, 668, Wt, rot=4)
finish(rgb, "c6_persona5_red_black_rip.png")
