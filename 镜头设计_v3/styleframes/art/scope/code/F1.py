"""HKBU SCIE1007 coursework science video. Scope direction, frame F1 (script 1-02): this is the liver, this many people died.
Real anatomy: BodyParts3D liver, portal vein and hepatic veins. Not flipped: seen from the front, the right lobe sits at image left.
Scale bar: the render is orthographic at PPM px per mm of the BodyParts3D model, so 5 cm is 50 x PPM px."""
from scopelib import *

D = np.load(WORK / "liver.npz")
PPM = float(D["ppm"])
cx, cy, R = 540, 540, 486
dx, dy = int(cx - W / 2), int(cy - H / 2) - 6
get = lambda k: np.roll(np.roll(D[k].astype(np.float32), dx, 1), dy, 0)
shell, ln, la, vn, vz, vv, va = map(get, ("lshell", "ln", "la", "vn", "vz", "vv", "va"))
ln = smooth_norm(ln, la)
vn = smooth_norm(vn, va)
vz = vz / np.maximum(va, 1e-3)
vv = vv / np.maximum(va, 1e-3)

# liver: a thin bone-white film, brighter where the wall turns edge-on, with a faint front-lit form so it reads as an organ
L = np.array([-.35, .5, .79], np.float32)
form = np.clip(ln @ L, 0, 1) ** 2.0 * la
s = np.clip(shell / 2.4, 0, 1) ** .9
rgb = blank()
rgb = over(rgb, BONE, np.clip(.07 * form + .8 * s, 0, 1))

# vessels: red portal vein, blue hepatic veins, each replacing what is behind it, nearer one on top
lit = np.clip(vn @ L, 0, 1)
rim = 1 - np.clip(vn[..., 2], 0, 1)
zm = vz[va > .5]
zn = np.clip((vz - np.percentile(zm, 2)) / (np.percentile(zm, 98) - np.percentile(zm, 2)), 0, 1)
lv = np.clip((.36 + .95 * lit ** 1.5) * (1 - .45 * zn), 0, 1)[..., None]
ramp = lambda lo, hi: np.where(lv < .42, lo * lv / .42, lo + (hi - lo) * np.clip((lv - .42) / .42, 0, 1))
red = (vv > .5).astype(np.float32) * va
blu = (vv <= .5).astype(np.float32) * va
rgb = rgb * (1 - np.clip(gblur(va, 2.5) * 1.1, 0, 1)[..., None] * .75)
rgb = over(rgb, ramp(KLEIN * 1.3, BLUE), blu)
lv = np.clip(lv * 1.5, 0, 1)
rgb = over(rgb, ramp(DARKRED, RED), red)
rgb = rgb * illum(cx, cy, R)[..., None]
rgb = rgb + over(blank(), KLEIN, disc(cx, cy, R) * (1 - np.clip(rgb.sum(-1) * 4, 0, 1)) * .05)
rgb = ring(rgb, cx, cy, R, "dashed")

clean(rgb, "F1")
# labels sit inside the field, the way an annotated figure does
rgb = text(rgb, "hepatic veins", (500, 196), 40, BONE, anchor="ms", halo=False)
rgb = line(rgb, [(500, 210), (500, 292)], BONE, 2.4)
rgb = text(rgb, "portal vein", (640, 712), 40, BONE, halo=False)
rgb = line(rgb, [(630, 700), (545, 668)], BONE, 2.4)
rgb = text(rgb, "liver", (800, 640), 40, BONE, halo=False)
rgb = line(rgb, [(830, 600), (800, 510)], BONE, 2.4)
rgb = ruler(rgb, 450, 900, PPM * 10, 5, "5 cm")

rgb = text(rgb, "1,412", (1096, 470), (sans, 250, 600), RED, halo=False)
rgb = text(rgb, "deaths in Hong Kong, 2022", (1106, 612), (sans, 62, 500), BONE, halo=False)
rgb = tag(rgb, 1106, 930, "dashed", "schematic", size=30)
rgb = text(rgb, "HKCaR 2022 · BodyParts3D, DBCLS, CC BY 4.0", (1106, 1000), (sans, 30, 500), BONE, halo=False)
purple_check(rgb)
save(rgb, "F1.png")
