"""HKBU SCIE1007 coursework science video. Scope direction, frame F5 (script 5-08): 048 is far stronger than 001, and that number was measured.
Bars share one linear axis, so 048's bar is true to scale. 001 only has a lower limit, so its bar has no end: it passes 6,000 and leaves the frame.
The field shows our re-docked pose of 048 in the real pocket (S2plus renders), with a double ring. No scale bar here, on purpose: nm next to nM invites a misreading."""
from scopelib import *

PUB = SCOPE.parent.parent / "S2plus/public"
X0, X6000 = 110, 1740                        # axis: 0 nM and 6,000 nM on screen
PX = (X6000 - X0) / 6000                     # px per nM
val, err = 33.4, 22.6

rgb = blank()

# pose field, top right
cx, cy, R = 1440, 318, 262
pocket = Image.open(PUB / "pose_048_blue.png").convert("RGBA")
lig = Image.open(PUB / "pose_048_lig.png").convert("RGBA").resize(pocket.size, Image.LANCZOS)
pw, ph = pocket.size
scale = 1.06 * 2 * R / ph * 1.42                     # fills the field with the pocket
crop_cx, crop_cy = 960, 900                          # centre of the pose in the source, px
size = int(2 * R / scale)
box = (crop_cx - size // 2, crop_cy - size // 2, crop_cx + size // 2, crop_cy + size // 2)
pk = np.asarray(pocket.crop(box).resize((2 * R, 2 * R), Image.LANCZOS), np.float32) / 255
lg = np.asarray(lig.crop(box).resize((2 * R, 2 * R), Image.LANCZOS), np.float32) / 255
pa = np.zeros((H, W, 3), np.float32)
pa[cy - R:cy + R, cx - R:cx + R] = pk[..., :3] * pk[..., 3:]
la = np.zeros((H, W), np.float32)
ll = np.zeros((H, W), np.float32)
la[cy - R:cy + R, cx - R:cx + R] = lg[..., 3]
ll[cy - R:cy + R, cx - R:cx + R] = lg[..., 0]
f = disc(cx, cy, R)
rgb = over(rgb, KLEIN, f * .05)
rgb = rgb * (1 - (pk_a := np.clip(pa.sum(-1) * 6, 0, 1))[..., None]) + pa
rgb = rgb * (1 - np.clip(gblur(la, 5) * 1.4, 0, 1)[..., None] * .8)
tone = np.clip((ll - .55) / .4, 0, 1)[..., None]
rgb = over(rgb, DARKRED + (RED - DARKRED) * tone, la)
rgb = rgb * illum(cx, cy, R)[..., None]
rgb = ring(rgb, cx, cy, R, "double")
clean(rgb, "F5")
rgb = tag(rgb, 1078, 640, "double", "OUR RE-DOCKING", size=30)

# heading
rgb = text(rgb, "Enzyme IC50", (X0, 170), (sans, 96, 600), BONE, halo=False)

# 001: solid to the only number we have, then keeps going off the frame, thinning into dashes. No cap
yb1, h = 716, 54
im, d = layer()
d.rectangle((X0 * SS, (yb1 - h / 2) * SS, X6000 * SS, (yb1 + h / 2) * SS), fill=255)
x = X6000 + 10
g = 40
while x < W + 20:
    d.rectangle((x * SS, (yb1 - h / 2) * SS, (x + g) * SS, (yb1 + h / 2) * SS), fill=255)
    x += g + 14
    g = max(10, g - 6)
rgb = over(rgb, BLUE, done(im))
rgb = line(rgb, [(X6000, yb1 - 64), (X6000, yb1 + 44)], BONE, 3)
rgb = text(rgb, "001 > 6,000 nM", (X0, yb1 - 44), (sans, 56, 600), BONE, halo=False)

# 048: same axis, so this is all the bar there is. Whisker is the plus-minus
yb2 = 900
im, d = layer()
d.rectangle((X0 * SS, (yb2 - h / 2) * SS, (X0 + val * PX) * SS, (yb2 + h / 2) * SS), fill=255)
rgb = over(rgb, RED, done(im))
wa, wb = X0 + (val - err) * PX, X0 + (val + err) * PX
rgb = line(rgb, [(wa, yb2), (wb, yb2)], BONE, 3)
rgb = line(rgb, [(wb, yb2 - 16), (wb, yb2 + 16)], BONE, 3)
rgb = line(rgb, [(X0, yb1 - h / 2 - 2), (X0, yb2 + h / 2 + 2)], BONE, 2, .6)
rgb = text(rgb, "048 = 33.4 ± 22.6 nM", (X0, yb2 - 44), (sans, 76, 600), RED, halo=False)
rgb = line(rgb, [(X0 + 34, yb2), (168, yb2)], BONE, 2.4)
rgb = text(rgb, "Just this much cuts the enzyme's activity in half.", (182, yb2 + 15), 44, BONE, halo=False)

rgb = tag(rgb, X0, 1030, "solid", "MEASURED · Ren 2023, Fig. 9A", size=30)
rgb = minimap(rgb, 1590, 1022, 3)
purple_check(rgb)
save(rgb, "F5.png")
