"""HKBU SCIE1007 coursework science video. manual T5: chapter five, saffron. A keyhole cut through the page shows 048 in the pocket (our re-docking, pencil treatment, never a measured structure). The measured number is printed solid with a rubber stamp."""
from mk import *

C = CH[5]
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
out = paper(C["paper"], 51, mott=0.04)
GUT = SW / 2

# ---- right page: the keyhole, die cut through the sheet ----
kx, ky, R = 1352, 354, 262
bw0, bw1, by1 = 152, 306, 956
K = Mask(SW, SH, 2)
K.ell(kx - R, ky - R, kx + R, ky + R)
K.poly([(kx - bw0, ky + 170), (kx + bw0, ky + 170), (kx + bw1, by1), (kx - bw1, by1)])
hole = K.a()
# What is behind the hole: the page below, near black
under = paper("#100d0c", 52, mott=0.05)
# The pocket and 048, our docking. Real render, recoloured only. Same frame for both layers.
PUB = ART.parent / "S2plus" / "public"
grey = Image.open(PUB / "pose_048_grey.png").convert("RGBA")
lig = Image.open(PUB / "pose_048_lig.png").convert("RGBA").resize(grey.size, Image.LANCZOS)
PH = 900
sc = PH / 1566  # bbox height in the 1920x2160 frame
gw, gh = int(grey.width * sc), int(grey.height * sc)
g = np.asarray(grey.resize((gw, gh), Image.LANCZOS), np.float32) / 255
l = np.asarray(lig.resize((gw, gh), Image.LANCZOS), np.float32) / 255
ox, oy = kx - 596 + 18, 18


def place(a):
    o = np.zeros((SH, SW, a.shape[2]), np.float32)
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + gw, SW), min(oy + gh, SH)
    o[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return o


G, L = place(g), place(l)
ga, la = G[..., 3], L[..., 3]
gv = G[..., :3].mean(2) / np.maximum(ga, 1e-3)
gv = np.clip(gv / 0.42, 0, 1)
# pocket in pencil: graphite strokes on the dark sheet, hatched along one direction with weight from the render
hatch = np.abs(((xx * 0.86 + yy * 0.5) / 5.2) % 1 - 0.5) * 2
hb = (hatch < (gv ** 1.1) * 0.8 + 0.06).astype(np.float32)
hb = gauss(hb, 0.5)
pocket = hexc("#7fa6c0") * (0.40 + 0.75 * gv[..., None])
behind = under * (1 - (ga * hb)[..., None]) + pocket * (ga * hb)[..., None]
# wall edge in brighter pencil
ed = np.clip(gauss(ga, 1.6) - gauss(ga, 5), 0, 1) * 2.4
behind = ink(behind, np.clip(ed, 0, 1) * ga, "#cfe0ea")
# 048: warm bone with a dark keyline, the one bright warm thing in the hole
la_s = gauss(la, 3.2)
behind = ink(behind, np.clip(la_s * 2.4, 0, 1), "#100d0c")
lc = L[..., :3].mean(2) / np.maximum(la, 1e-3)
lig_col = ramp(np.clip(lc, 0, 1), [(0.3, "#e4661e"), (0.62, "#ffb732"), (0.9, "#fff6da"), (1, "#ffffff")])
behind = behind * (1 - la[..., None]) + lig_col * la[..., None]

# shadow of the page's cut edge falling into the hole
inner = np.clip(np.roll(np.roll(gauss(1 - hole, 9), 16, 0), 12, 1), 0, 1)
behind *= 1 - 0.72 * inner[..., None]
out = out * (1 - hole[..., None]) + behind * hole[..., None]
# paper thickness: a thin lit lip on the lower right of the cut
lip = np.clip(hole - np.roll(np.roll(hole, 3, 0), 3, 1), 0, 1)
out = ink(out, lip, "#ffe08a")

# Cut guide in pencil around the hole, dashed: this part is ours and tentative. Traced as rays from inside the shape.
Dd = Mask(SW, SH, 2)
far = gauss(hole, 10) > 0.03
c0x, c0y = kx, ky + 150
pts = []
for t in np.linspace(0, 2 * np.pi, 240):
    for r_ in np.arange(900, 0, -2.0):
        px_, py_ = c0x + r_ * np.cos(t), c0y + r_ * np.sin(t)
        if 0 <= px_ < SW and 0 <= py_ < SH and far[int(py_), int(px_)]:
            pts.append((px_, py_))
            break
Dd.dash(pts, 3.6, 24, 14, 0.5, 5)
out = ink(out, Dd.a(), "#1c1a22")

# ---- our re-docking tag: dashed pencil outline, plain weight, no fill ----
Tg = Mask(SW, SH, 2)
tx0, ty0, tx1, ty1 = 930, 14, 1262, 80
Tg.dash([(tx0, ty0), (tx1, ty0), (tx1, ty1), (tx0, ty1), (tx0, ty0)], 3.0, 14, 9, 0.8, 6)
Tt = Mask(SW, SH, 2)
Tt.text(((tx0 + tx1) / 2, (ty0 + ty1) / 2 + 13), "OUR RE-DOCKING", sans(36 * 2, 500), "ms", track=0)
out = ink(out, Tg.a(), "#1c1a22")
out = ink(out, Tt.a(), "#14100c")

# ---- left page ----
P = Mask(SW, SH, 2)
P.text((70, 112), "Enzyme IC50", serif(70 * 2, 900), "ls")
P.text((64, 286), "048 = 33.4", serif(138 * 2, 900), "ls", track=-1)
P.text((64, 452), "± 22.6 nM", serif(138 * 2, 900), "ls", track=-1)
sent = ["Just this much cuts the", "enzyme's activity in half."]
for i, ln in enumerate(sent):
    P.text((70, 556 + i * 62), ln, serif(50 * 2, 700), "ls")
out = ink(out, P.a(), C["ink"], 0.06, 4)

# Runes left over: what this chapter has not read yet
Rn = Mask(SW, SH, 2)
Rn.runes(72, 862, 790, 3, 212, 11.0, 16.0, 4.5, 28.0, 2.0)
out = ink(out, Rn.a() * 0.9, C["ink"])

# ---- measured: a solid rubber stamp, double rule, tilted, deep red with the words knocked out. Heavy against the pencil dash ----
st = Mask(860, 170, 3)
st.rect(4, 4, 790, 112)
st.rect(10, 10, 784, 106, 0)
st.rect(15, 15, 779, 101)
Kt = Mask(860, 170, 3)
Kt.text((397, 74), "MEASURED · Ren 2023, Fig. 9A", sans(42 * 3, 900), "ms")
sa, ka = st.a(), Kt.a()
big = Image.new("L", (SW, SH), 0)
bk = Image.new("L", (SW, SH), 0)
big.paste(Image.fromarray((sa * 255).astype(np.uint8)).rotate(2.4, Image.BICUBIC), (58, 668))
bk.paste(Image.fromarray((ka * 255).astype(np.uint8)).rotate(2.4, Image.BICUBIC), (58, 668))
smask = np.asarray(big, np.float32) / 255
kn = np.asarray(bk, np.float32) / 255
press = fbm(SH, SW, 70, 3, 8)
smask = smask * np.clip(0.82 + (press - 0.42) * 1.4, 0.62, 1)  # uneven pressure
out = ink(out, smask, "#a81a0e")
out = ink(out, kn, "#fff0c4")

rgb = wrap(out, 0.71, tilt=-1.2, zoom=1.0, lamp=(900, 140), warm=0.5, fall=2600)
save(rgb, ST / "T5.png")
