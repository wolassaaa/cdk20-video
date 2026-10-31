"""HKBU SCIE1007 coursework science video. Style scout f7: line light. One continuous tube of light is the real CA chain of CDK20, folded; contour rings show the real surface around it. Black mirror underneath.
Blue is pLDDT 0.7 and above, orange is below. Everything that glows here is real data, the only drawn lines are the title."""
from fx import *

d = np.load(WORK / "tron.npz")
shell, chain = d["shell"], d["chain"]
yy, xx = np.mgrid[:H, :W].astype(np.float32)

hdr = shell * 0.62 + chain * 1.0
# bloom in three sizes, the way a light tube blooms in fog
b1, b2, b3 = gauss(hdr, 2.0), gauss(hdr, 9), gauss(hdr, 34)
glow = hdr + b1 * 0.45 + b2 * 0.2 + b3 * 0.2
# title stands on the mirror, tubes drawn from the monoline skeletons
SS = 3
tm = Image.new("L", (W * SS, H * SS), 0)
dr = ImageDraw.Draw(tm)
LH, LW = 104, 84
gap = 40
tot = sum(LW * ADV[c] + gap for c in "CDK20") - gap
x = (W - tot) / 2
base = 648
top = base - LH
for ch in "CDK20":
    for st in STROKES[ch]:
        pts = [((x + px * LW) * SS, (top + py * LH) * SS) for px, py in st]
        dr.line(pts, fill=255, width=4 * SS, joint="curve")
    x += LW * ADV[ch] + gap
t = np.asarray(tm.resize((W, H), Image.LANCZOS), np.float32) / 255
COL = rgb("#30D4FF")
# clear the mirror under the title so it reads against black
under = np.clip(gauss(t, 16) * 4.0, 0, 1)
glow = glow * (1 - 0.7 * under)[..., None]
tg = t[..., None] * rgb("#E8FBFF") * 3.0 + gauss(t, 3)[..., None] * COL * 2.6 + gauss(t, 12)[..., None] * COL * 1.6 + gauss(t, 40)[..., None] * COL * 0.9
# its reflection in the floor
ry = np.clip(2 * (base + 7) - yy, 0, H - 1)
refl = sample(t, xx, ry)
refl = gauss(refl, 1.2) * smooth(H + 60, base, yy) * (yy > base + 6)
tg = tg + refl[..., None] * COL * 1.3
img = glow + tg

# filmic shoulder: colour stays saturated until it is very hot, then bleaches
img = 1 - np.exp(-img * 1.2)
img = np.clip(img, 0, 1) ** (1 / 1.5)
img = img * (1 - 0.35 * smooth(560, 860, np.hypot(xx - 640, yy - 330)))[..., None]

lab = font("bahnschrift.ttf", 23)
lw = text_width(LABEL, lab, 2.0)
lm = text_mask(LABEL, lab, ((W - lw) / 2, 698), 2.0)
img = img * (1 - np.clip(gauss(lm, 5) * 6, 0, 1) * 0.9)[..., None]
img = mix(img, rgb("#DDF8FF"), lm)
save(img, OUT / "f7_linelight.png")
print("ok")
