"""HKBU SCIE1007 coursework science video. polar direction, still T5: 048 in the pocket on the coloured side, the measured number on the grey side.
The pocket and pose are the existing renders, recoloured only. The colour stays on our computed picture; the measured value never sits on it."""
from plib import *

PUB = ART.parent / "S2plus/public"
t = .36
SC = .62
ox, oy = -140, -130            # where the 1920x2160 layer lands, in frame px


def layer(name, s):
    im = Image.open(PUB / name).convert("RGBA")
    w, h = round(1920 * s), round(2160 * s)
    im = im.resize((w, h), Image.LANCZOS)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.paste(im, (ox, oy))
    a = np.asarray(c, np.float32) / 255
    return a[..., :3] / np.maximum(a[..., 3:], 1e-3), a[..., 3]


rgbP, aP = layer("pose_048_grey.png", SC)
rgbL, aL = layer("pose_048_lig.png", SC)
L = rgbP.mean(-1) * aP
m = np.clip(gblur(aP, .6), 0, 1)

# height-like field from the shading, only to lay colour bands and crosses over the pocket that is already there
h_ = gblur(L, 9)
gy, gx = np.gradient(gblur(L, 7))
wob = G.fbm(H, W, beta=3.9, seed=6)
yn = (yy - 500) / 500
c = pal(2.3 * h_ + .55 * (wob - .5) + .22 * yn + .42)
th = np.arctan2(gy, gx) + .6 * (wob - .5)
ext = .16 + .84 * (np.sin(2 * th) ** 2) ** .5
shade = np.clip(L / .36, 0, 1.2) ** .6
shade = np.maximum(shade, .34)
col = limit(c * (ext * shade * m)[..., None], .82)
col = col * (1 - .55 * gblur(aL, 7) * 1.4).clip(0, 1)[..., None]        # a dark seat around the ligand so bone reads on any band

bg = grey_world(.80)
v = (.58 + .75 * L)[..., None] * np.array([1, .993, .972], np.float32)
grey = bg * (1 - m[..., None]) + np.clip(v, 0, 1) * m[..., None]

# ligand: same render, bone white, on both sides
bone = rgbL * np.array([1.0, .975, .93], np.float32) * 1.06
rgb = sheet(col, grey, t)
rgb = rgb * (1 - aL[..., None]) + np.clip(bone, 0, 1) * aL[..., None]

ink = INK
def lx(y, m=46):
    return line_x(t, y) + m

# measured value: flush to the sheet edge, row by row
rgb = put(rgb, "Enzyme IC50", (lx(330), 330), sans(56, 600))
rgb = put(rgb, "048 =", (lx(462), 462), serif(96, 900))
rgb = put(rgb, "33.4 ± 22.6 nM", (lx(620), 620), serif(112, 900))
rgb = put(rgb, "Just this much cuts the enzyme's activity in half.", (lx(712), 712), sans(38, 500))

# evidence plates: solid block = measured, dashed outline = ours
x0 = lx(860); s = "MEASURED · Ren 2023, Fig. 9A"; f = sans(38, 700)
tw = ImageDraw.Draw(Image.new("L", (8, 8))).textlength(s, font=f)
rgb = over(rgb, ink, poly([(x0 + 22, 790), (x0 + 22 + tw + 48, 790), (x0 - 2 + tw + 48, 862), (x0 - 2, 862)]))
rgb = put(rgb, s, (x0 + 34, 840), f, (.93, .925, .90))

x1, y1 = 1250, 66
f2 = sans(38, 700); s2 = "OUR RE-DOCKING"
tw2 = ImageDraw.Draw(Image.new("L", (8, 8))).textlength(s2, font=f2)
rgb = over(rgb, ink, box(x1, y1, x1 + tw2 + 52, y1 + 74, 4, 15, 10))
rgb = put(rgb, s2, (x1 + 26, y1 + 51), f2)
lig_y, lig_x = np.array(np.where(aL > .5)).mean(1)
rgb = over(rgb, (.95, .94, .90), seg((x1, y1 + 37), (lig_x + 92, lig_y - 262), 3.5, 13, 10) * np.clip(-line_d(t) / 2, 0, 1))
rgb = over(rgb, ink, seg((x1, y1 + 37), (lig_x + 92, lig_y - 262), 3.5, 13, 10) * np.clip(line_d(t) / 2, 0, 1))
save(rgb, "T5.png")
