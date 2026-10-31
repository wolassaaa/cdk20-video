"""HKBU SCIE1007 coursework science video. Hands T4: the real surface half sunk in ash, the prints from T3 still round it, one real hand from our phone clip touching it, gold running out of the touch. The only on-screen text is the evidence label."""
from hk import *
from phone import hand, over

TOUCH = (1215, 655)
a = np.asarray(Image.open(RAW / "t4_mass.png").convert("RGBA"), np.float32) / 255
solid = (a[..., 3] > 0.992).astype(np.float32)
ring = np.load(RAW / "ring.npz")
pm, col = ring["pm"], ring["col"]
pm = pm * (1 - gblur(solid, 8))
heap = gblur(solid, 22) * 1.3 + gblur(solid, 7) * 0.5
rgb, _ = ash(heap + press(pm, 0.5, 1.0), tone=0.34, seed=5, light=1.0)
rgb = comp(rgb, pm * 0.60, col * 0.72)
sh = (1 - solid) * a[..., 3] * 0.84
rgb = rgb * (1 - sh[..., None])
rgb = comp(rgb, solid, a[..., :3])
gold = np.clip(a[..., 0] - a[..., 2] - 0.25, 0, 1) * solid
rgb = 1 - (1 - np.clip(rgb, 0, 1)) * (1 - np.clip(gblur(gold, 9) * 0.28, 0, 1)[..., None] * GOLD)
rgb = over(rgb, hand(690, "Left", TOUCH, 132, 1.75))
rgb = vignette(rgb, 0.46)

# machine voice: mono type, hairline box, cold
f = font(MONO, 36)
spr = sprite_text("AlphaFold DB v6 · predicted", f, pad=2)
x, y = 64, 972
cold = np.array([0.90, 0.92, 0.95], np.float32)
bx = (x - 22, y - 20, x + spr.width + 22, y + spr.height + 20)
rgb = comp(rgb, gblur(layer(Image.new("L", (bx[2] - bx[0], bx[3] - bx[1]), 255), bx[0], bx[1]), 1) * 0.72, np.array([0.03, 0.03, 0.035], np.float32))
fr = strokes([(bx[0], bx[1], bx[2], bx[1]), (bx[2], bx[1], bx[2], bx[3]), (bx[2], bx[3], bx[0], bx[3]), (bx[0], bx[3], bx[0], bx[1])], 1.5)
rgb = comp(rgb, fr, cold)
rgb = comp(rgb, layer(spr, x, y), cold)
save(rgb, "T4.png")
