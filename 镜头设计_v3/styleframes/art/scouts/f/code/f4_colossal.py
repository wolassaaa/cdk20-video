"""HKBU SCIE1007 coursework science video. Style scout f4: colossal scale. The real CDK20 surface stood on end as a cliff, people at its foot about 1/200 of its height, dust at the base."""
from fx import *

d = np.load(WORK / "world_f4.npz")
beauty, z, ids = d["beauty"], d["z"], np.round(d["id"])
L0 = beauty @ np.array([0.3, 0.6, 0.1], np.float32)
yy, xx = np.mgrid[:H, :W].astype(np.float32)
prot = gauss((ids == 2).astype(np.float32), 0.5)
sand = (ids == 1).astype(np.float32)
sky = gauss((ids == 0).astype(np.float32), 0.5)
ppl = (ids == 3).astype(np.float32)

hz = 516.0  # horizon line in this render
# sky: pale bone with the sun burning just outside the frame, upper left
sun = np.exp(-(((xx + 40) / 700) ** 2 + ((yy + 60) / 520) ** 2))
skyL = 0.70 + 0.30 * sun
skyL = skyL + 0.12 * smooth(0, hz, yy)

# object: hard contrast, shadow goes nearly black, the sun side stays bone
pL = np.clip((L0 - 0.045) / 0.40, 0, 1) ** 1.05
pL = pL * 0.86 + 0.012
sharp = pL - gauss(pL, 11)
pL = np.clip(pL + 1.5 * sharp, 0, 1)
pL = pL * (0.72 + 0.28 * smooth(0.0, 0.5, pL))
# dust climbs the foot of the object, this is what makes it read as far away and vast
dust = np.exp(-np.maximum(hz + 8 - yy, 0) / 86.0) * 0.82
air = np.clip((z - 8) / 60, 0, 0.3)
fog = np.clip(dust + air, 0, 0.92)
pL = pL * (1 - fog) + (0.80 + 0.1 * sun) * fog

# sand: pale at the horizon, falling to a black foreground dune so the eye starts in the dark
sL = np.clip(L0 / 0.62, 0, 1.2) ** 1.25
depth = smooth(hz + 2, 640, yy)
ripple = (sL - gauss(sL, 10))
sL = (0.74 - 0.72 * depth ** 0.8) * (0.92 + 0.5 * ripple) + 0.015
gd = smooth(hz + 90, hz + 8, yy) * dust * 0.4
sL = sL * (1 - gd) + 0.82 * gd

img = skyL * sky + pL * prot + sL * sand * (1 - prot)
img = np.clip(img, 0, 1)
img = img * (1 - ppl * 0.97)  # figures stay as hard black specks
# long sun shadows of the figures across the sand, thrown right
sh = np.zeros((H, W), np.float32)
for i in range(1, 46):
    sh = np.maximum(sh, np.roll(np.roll(ppl, i, axis=1), int(i * 0.07), axis=0) * (1 - i / 46))
img = img * (1 - 0.34 * sh * sand)

# bone and ochre, nothing else
stops = np.array([0.0, 0.2, 0.46, 0.72, 1.0], np.float32)
cols = np.stack([rgb(c) for c in ("#0C0A08", "#3A2C1F", "#9C7A52", "#DCC49D", "#FBF1DE")])
out = np.stack([np.interp(img.ravel(), stops, cols[:, i]).reshape(img.shape) for i in range(3)], -1).astype(np.float32)
# sand gets a little more heat than the sky
out = out * (1 + (sand * (1 - prot))[..., None] * (rgb("#FFC890") / rgb("#FFE9D0") - 1) * 0.5)
out = screen(out, (sun ** 3)[..., None] * rgb("#FFF0D0") * 0.3)

f = font("GOTHIC.TTF", 112)
tr = 96
t = "CDK20"
tw = text_width(t, f, tr)
tm = text_mask(t, f, ((W - tw) / 2, 648), tr)
out = mix(out, rgb("#F4E7CF"), tm)
lab = font("GOTHIC.TTF", 21)
lw = text_width(LABEL, lab, 3.0)
lm = text_mask(LABEL, lab, ((W - lw) / 2, 696), 3.0)
out = mix(out, rgb("#E8D8BA"), lm)
save(out, OUT / "f4_colossal_scale.png")
print("ok")
