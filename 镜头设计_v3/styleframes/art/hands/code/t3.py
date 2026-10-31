"""HKBU SCIE1007 coursework science video. Hands T3: near-black ash, a void, handprints that crowd up to its edge and stop.
The void is the same outline and position as the surface in T4, so S4 can fill the hole that S3 left. The prints are a metaphor, so the text is labelled schematic."""
from hk import *

N = 900
a = np.asarray(Image.open(RAW / "t4_mass.png").convert("RGBA"), np.float32) / 255
void = gblur((a[..., 3] > 0.992).astype(np.float32), 16) > 0.42      # closed up: the void is an outline, not a surface
vf = void.astype(np.float32)
near = gblur(vf, 90)
far = gblur(vf, 34)
gy, gx = np.gradient(gblur(vf, 44))

rng = np.random.default_rng(33)
base = [print_sil(s, 300) for s in range(6)]
pm = np.zeros((H, W), np.float32)
col = np.zeros((H, W, 3), np.float32)
ids = np.zeros((H, W), np.int16)
pts = []
tries = 0
size = 44
while len(pts) < N and tries < 200000:
    tries += 1
    x, y = rng.integers(0, W), rng.integers(0, H)
    if void[y, x] or far[y, x] > 0.18 or (x < 800 and y > 900):        # keep the whole print outside the edge
        continue
    if rng.random() > max(near[y, x], 0) ** 0.5 * 1.7:
        continue
    if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < 30 ** 2 for p in pts):
        continue
    pts.append((x, y))
for pi_, (x, y) in enumerate(pts):
    ang = math.degrees(math.atan2(-gx[y, x], -gy[y, x])) + rng.normal(0, 14)
    s = rot_sprite(base[int(rng.integers(6))], ang, size)
    h, w = s.shape
    x0, y0 = int(x - w / 2), int(y - h / 2)
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if cx0 >= cx1 or cy0 >= cy1:
        continue
    sub = s[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    sub = sub * (1 - vf[cy0:cy1, cx0:cx1])
    t = SKIN[int(rng.integers(len(SKIN)))] * rng.uniform(0.62, 0.90)
    col[cy0:cy1, cx0:cx1] = col[cy0:cy1, cx0:cx1] * (1 - sub[..., None]) + t * sub[..., None]
    pm[cy0:cy1, cx0:cx1] = np.maximum(pm[cy0:cy1, cx0:cx1], sub)
    ids[cy0:cy1, cx0:cx1][sub > 0.02] = pi_ + 1
print("prints", len(pts))
np.savez_compressed(RAW / "ring.npz", pm=pm, col=col, void=vf, pts=np.array(pts), ids=ids)

t1 = layer(sprite_text("no one had measured CDK20's shape", font(SERIF, 54)), 64, 950)
t2 = layer(sprite_text("schematic", font(SERIFI, 40)), 66, 1012)
txt = np.maximum(t1, t2)
plate = np.clip(gblur(((t1 + t2) > 0).astype(np.float32), 26) * 2.4, 0, 1)
relief = press(pm, 0.5, 1.0) + press(vf, 1.4, 2.5)
rgb, _ = ash(relief, tone=0.105, seed=47, light=1.2)
rgb = comp(rgb, pm * 0.95, col * 0.92)
rgb = comp(rgb, plate * 0.72 * (1 - pm), np.array([0.05, 0.05, 0.055], np.float32))
rgb = comp(rgb, gblur(vf, 1.2), np.array([0.0, 0.0, 0.0], np.float32))
rgb = comp(rgb, gblur(txt, 0.45), np.array([0.92, 0.92, 0.92], np.float32))
rgb = vignette(rgb, 0.40)
save(rgb, "T3.png")
