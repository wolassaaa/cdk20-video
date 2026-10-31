"""HKBU SCIE1007 coursework science video. manual T1: chapter one, the darkest printed page in the book. The grey paper is flooded almost to black. The real BodyParts3D liver is cut as an engraving, front view, big right lobe on the left of the frame. No dots and no runes on it: this is a real organ, not a prediction. Unread runes sit in the flood, barely there."""
from mk import *

C = CH[1]
WK = ART / "manual" / "_work"
load_ = lambda n: np.asarray(Image.open(WK / n).convert("RGBA"), np.float32) / 255
ky, lw = load_("liver_key.png"), load_("liver_low.png")
SC = 1.27
PW_, PH_ = int(ky.shape[1] * SC), int(ky.shape[0] * SC)
rs = lambda a: np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((PW_, PH_), Image.LANCZOS), np.float32) / 255
ky, lw = rs(ky), rs(lw)
OX, OY = -440, -300  # bbox lands left of centre, right lobe on the left page
place = lambda a: np.stack([(lambda c: c)(np.pad(a[..., i], ((0, 0), (0, 0))))[max(0, -OY):max(0, -OY) + SH, max(0, -OX):max(0, -OX) + SW] for i in range(a.shape[2])], -1)
KY_, LW_ = place(ky), place(lw)
m = KY_[..., 3]
key_ = KY_[..., 0] / np.maximum(m, 1e-3)
low_ = LW_[..., 0] / np.maximum(m, 1e-3)
s = np.clip(key_ * 0.92 + low_ * 0.42, 0, 1)
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)

# Flood: the chapter's grey paper under an almost black ink, the runes knocked out so faintly they are felt more than read
out = paper(C["paper"], 11)
Rb = Mask(SW, SH, 2)
Rb.runes(40, 34, SW - 80, 24, 0, 13.0, 19.0, 5.0, 39.0, 2.0)
flood = np.clip(1 - Rb.a() * 0.085, 0, 1)
out = out * (1 - flood[..., None]) + hexc("#100a0b") * flood[..., None]

# Shadow of the form on the page
sh = gauss(np.roll(np.roll(m, 40, 0), 30, 1), 26)
out *= 1 - 0.55 * sh[..., None]

# Engraving: lines that bend with the form. Oxblood plate, then cut lines in red, then the fewest bone lines
h_ = gauss(s * m, 52) + gauss(m, 80) * 0.6
v = (yy * 0.94 + xx * 0.34 + h_ * 104) / 7.5
tri = np.abs(v % 1 - 0.5) * 2
line = lambda g, sharp=3.0: np.clip((g - tri) * sharp + 0.5, 0, 1)
liver = paper("#3a0b0e", 12, mott=0.05)
liver = ink(liver, line(np.clip((s - 0.16) / 0.5, 0, 0.72)), "#7e1a1e")
liver = ink(liver, line(np.clip((s - 0.56) / 0.40, 0, 0.62) ** 1.3), C["paper"])
out = out * (1 - m[..., None]) + liver * m[..., None]
rim = np.clip(gauss((m > 0.5).astype(np.float32), 1.3) - gauss((m > 0.5).astype(np.float32), 3.2), 0, 1)
out = ink(out, np.clip(rim * 2.4, 0, 0.8), "#a32a2a")

# The figure, in the paper's own colour, knocked out of the flood
T = Mask(SW, SH, 2)
T.text((986, 800), "1,412", serif(164 * 2, 900), "ls", track=-1)
T.text((992, 880), "deaths in Hong Kong, 2022", serif(52 * 2, 700), "ls")
out = ink(out, T.a(), hexc(C["paper"]) * 1.12, 0.05, 6)

if __name__ == "__main__":
    rgb = wrap(out, 0.03, tilt=-1.4, zoom=1.0, lamp=(980, 560), fall=1250, warm=0.5, floor=0.36)
    save(rgb, ST / "T1.png")
