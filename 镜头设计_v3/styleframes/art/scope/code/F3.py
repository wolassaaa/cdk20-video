"""HKBU SCIE1007 coursework science video. Scope direction, frame F3 (script 3-02, 3-03): protein is the lock, molecule is the key, a good key fits its own lock and no other.
Schematic on purpose: invented flat shapes with a dashed ring, drawn with the same bright-wall look as the real models so the film stays one piece, and nothing here looks like a molecule."""
from scopelib import *


def blob(cx, cy, lobes):
    """A smooth lumpy outline, plainly a drawing."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    f = np.zeros((H, W), np.float32)
    for x, y, r in lobes:
        f += np.exp(-((xx - cx - x) ** 2 + (yy - cy - y) ** 2) / (2 * r * r))
    return np.clip((f - .6) / .06, 0, 1)


TEETH_A = [(0, 26), (40, 12), (72, 34), (112, 18), (136, 30)]        # blade profile: offset along the blade, depth
TEETH_B = [(6, 42), (68, 12), (130, 42)]        # the other lock's slot


def blade(x, y, L, profile, pad=0.0, t=22):
    """Blade pointing right from (x, y). Flat top, stepped lower edge."""
    top = y - t - pad
    base = y + 8 + pad
    pts = [(x, top), (x + L + pad, top), (x + L + pad, base)]
    for o, dp in sorted(profile, reverse=True):
        xa = x + L - 162 + o
        pts += [(xa + 26 + pad, base), (xa + 26 + pad, y + 8 + dp + pad), (xa - pad, y + 8 + dp + pad), (xa - pad, base)]
    pts += [(x, base)]
    return poly(pts)


def key(x, y, L=230):
    """x, y = where the blade meets the bow."""
    return np.maximum(disc(x - 58, y - 7, 66), blade(x, y, L, TEETH_A)) * (1 - disc(x - 66, y - 7, 26))


def lock(cx, cy, lobes, slot):
    return np.clip(blob(cx, cy, lobes) - slot, 0, 1)


def wall(rgb, m):
    """Same look as the real surface: bright wall, dark body, a couple of nested contours."""
    d = gblur(m, 20)
    con = sum(np.exp(-((d - q) / .014) ** 2) for q in (.72, .9, .985))
    d2 = gblur(m, 5)
    rim = np.exp(-((d2 - .5) / .22) ** 2) * m
    rgb = over(rgb, KLEIN, m * (.28 + .5 * np.clip(con, 0, 1)))
    return over(rgb, BLUE, np.clip(rim * 1.2 + con * .25 * m, 0, 1))


def show_key(rgb, k):
    rgb = rgb * (1 - np.clip(gblur(k, 3) * 1.6, 0, 1)[..., None] * .9)
    col, a = fluor(k, DARKRED, RED, 6, .78)
    return over(rgb, col, a)


LA, LB = (470, 440), (1450, 440)
R = 398
lobes1 = [(0, 0, 100), (130, -90, 74), (150, 80, 70), (10, 130, 62), (-40, -120, 60), (60, -170, 44), (-80, 90, 52), (210, 0, 50)]
lobes2 = [(30, -20, 96), (150, 20, 84), (70, 140, 68), (-30, -110, 56), (130, -130, 66), (-40, 110, 50), (190, 96, 46), (40, -190, 40)]

rgb = blank()
for fx, fy in (LA, LB):
    rgb = over(rgb, KLEIN, disc(fx, fy, R) * .05)

# left: the key sits in a slot cut to its own shape
x1, y1 = LA[0] - 150, LA[1] + 10
slot = blade(x1, y1, 230, TEETH_A, pad=6)
mouth = poly([(x1 - 200, y1 - 28), (x1 + 20, y1 - 28), (x1 + 20, y1 + 14), (x1 - 200, y1 + 14)])
rgb = wall(rgb, lock(LA[0] + 60, LA[1], lobes1, np.maximum(slot, mouth)))
rgb = show_key(rgb, key(x1, y1))

# right: a different lock, a slot with other teeth, the same key stopped at the door
x2, y2 = LB[0] - 250, LB[1] + 10
sx = LB[0] + 40
slot2 = blade(sx, y2, 230, TEETH_B, pad=6)
mouth2 = poly([(sx - 200, y2 - 28), (sx + 20, y2 - 28), (sx + 20, y2 + 14), (sx - 200, y2 + 14)])
rgb = wall(rgb, lock(LB[0] + 94, LB[1], lobes2, np.maximum(slot2, mouth2)))
rgb = show_key(rgb, key(x2, y2))

rgb = rgb * np.maximum(disc(LA[0], LA[1], R), disc(LB[0], LB[1], R))[..., None]
for f in LA, LB:
    rgb = ring(rgb, f[0], f[1], R, "dashed")

clean(rgb, "F3")
rgb = tick(rgb, LA[0], LA[1] + 348, 30, w=6)
rgb = cross(rgb, LB[0], LB[1] + 346, 24, w=6)

rgb = text(rgb, "candidate (a small molecule)", (LA[0], 150), 36, BONE, anchor="ms", halo=False)
rgb = line(rgb, [(LA[0] - 170, 166), (x1 - 58, y1 - 78)], BONE, 2.4)
rgb = text(rgb, "target (a protein)", (LA[0] + 40, 738), 38, BONE, anchor="ms", halo=False)
rgb = text(rgb, "selectivity", (W / 2, 985), (sans, 84, 600), BONE, anchor="ms", halo=False)
rgb = tag(rgb, 1860, 1000, "dashed", "schematic", anchor="r", size=30)
rgb = minimap(rgb, 96, 1000, 0, before=True)
purple_check(rgb)
save(rgb, "F3.png")
