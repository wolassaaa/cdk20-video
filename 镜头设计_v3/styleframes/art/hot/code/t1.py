"""HKBU SCIE1007 coursework science video. Art direction `hot`, frame T1 (1-02): the real liver and the number, in the quiet register.

Not required for round two; drawn because the hot palette is only safe if it can stay silent. No fluorescent colour: one wine hue, bone type, the same stepped block and giant type as the loud frames.
Liver: BodyParts3D mesh, reprojected here with no edits.
"""
from hot_kit import *

STL = ART.parent.parent / "assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
b = open(STL, "rb").read()
n = int.from_bytes(b[80:84], "little")
dt = np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
T = np.frombuffer(b, dt, n, 84)["v"].reshape(-1, 3, 3)
c = T.mean(1)
mid = (c.min(0) + c.max(0)) / 2
c = c - mid
span = np.ptp(c, axis=0)
print("span", span, n)
# anterior view: screen x = model x, screen y = -model z, depth = -model y
sc = 1040 / max(span[0], span[2])
CX, CY = 1330, 545
sx = c[:, 0] * sc * -1 + CX
sy = -c[:, 2] * sc + CY
dep = -c[:, 1]
ss = 2
Wb, Hb = W // ss, H // ss
ix, iy = (sx / ss).astype(np.int32), (sy / ss).astype(np.int32)
ok = (ix >= 0) & (ix < Wb) & (iy >= 0) & (iy < Hb)
ix, iy, dep = ix[ok], iy[ok], dep[ok]
o = np.argsort(dep)
z = np.full((Hb, Wb), np.nan, np.float32)
z[iy[o], ix[o]] = dep[o]
m0 = ~np.isnan(z)
z0 = np.nan_to_num(z, nan=0.0)
wt = kit.fft_blur(m0.astype(np.float32), 1.4) + 1e-3
zs = kit.fft_blur(z0, 1.4) / wt
mask = (kit.fft_blur(m0.astype(np.float32), 1.8) > 0.45).astype(np.float32)
up = lambda a: np.asarray(Image.fromarray(a).resize((W, H), Image.BICUBIC))
zs, mask = up(zs.astype(np.float32)), np.clip(up(mask) * 1.0, 0, 1)
gy, gx = np.gradient(blur(zs, 7) * sc / 2)
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1)
nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
L = np.array([-0.5, -0.62, 0.6], np.float32)
tn = np.clip(nrm @ L, 0, 1) * mask

W1, W2_ = hx("#2C0519"), hx("#8E1240")
rgb = field(hx("#050507"))
# one stepped block of wine, the only colour in the frame, and it is barely on
rgb = comp(rgb, poly([(760, 0), (W, 0), (W, H), (880, H), (880, 900), (820, 900), (820, 760), (760, 760)]), W1)
# engraved lines, width from the light
pitch = 9
ph = (yy + blur(zs, 7) * sc * 0.25) / pitch
d = np.abs(ph % 1 - 0.5) * 2
wd = np.clip(tn * 0.95 + 0.04, 0.05, 0.9)
rgb = comp(rgb, mask * np.clip((wd - d + 0.1) / 0.2, 0, 1), W2_)

num = stepped(fit("1,412", 680, 300), 8)
rgb = comp(rgb, place(num, 56, 270), P)
rgb = comp(rgb, place(sprite("deaths in Hong Kong, 2022", tight(52, 700), pad=0), 58, 610), P)
save(rgb, "T1.png")
