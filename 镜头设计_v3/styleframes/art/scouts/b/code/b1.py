"""HKBU SCIE1007 coursework science video. Style scout b1: a room of one saturated light, the real CDK20 outline is the only opening in the wall."""
import numpy as np

from common import *

P = load()
V = view(P, zoom=1.34, at=(640, 262), src=(950, 545))
y, x = grid()
m = V["mask"]

# the room: no corners, one colour, only a slow slide from blue into violet on the floor
floor = sstep(470, 640, y)
wall = ramp(np.clip(np.hypot((x - 640) / 900, (y - 268) / 520), 0, 1), [(0, "#2b18ff"), (0.55, "#1a08e8"), (1, "#0b02a8")])
fl = ramp(np.clip((y - 470) / 250, 0, 1), [(0, "#2b12f0"), (0.5, "#6a10e8"), (1, "#c410c8")])
rgb = lin(wall) * (1 - floor[..., None]) + lin(fl) * floor[..., None]

# the opening: flat burning light, the relief stays inside as a whisper of tone
edge = blur(m, 2.4)
shade = 0.5 * V["ao"] + 0.5 * np.clip(0.7 * V["key"] + 0.9 * V["rim"], 0, 1)
shade = blur(shade * m, 1.2) / np.maximum(blur(m, 1.2), 0.05)
ap = lin(ramp(np.clip(shade, 0, 1), [(0, "#e60a2c"), (0.4, "#f40e2e"), (0.75, "#ff1c30"), (1, "#ff3234")]))
tail = sstep(0.7, 0.6, blur(V["conf"], 2) / np.maximum(blur(m, 2), 0.05))  # real low confidence tail cools toward pink
ap = ap * (1 - 0.75 * tail[..., None]) + lin(hexc("#ff30a8")) * 0.75 * tail[..., None]

# light spills from the opening onto the wall and pools on the floor
red = lin(hexc("#ff2a3a"))
spill = blur(m, 70)[..., None] * 0.55 + blur(m, 22)[..., None] * 0.35
rgb = rgb + spill * red
pool = np.exp(-((x - 640) / 430) ** 2) * sstep(520, 720, y)
rgb = rgb + pool[..., None] * red * 0.42

# the name lies on the floor as light, seen in steep perspective
fx, fy = np.mgrid[0:360, 0:2600].astype(np.float32)[::-1]
tm = text("CDK20", "ariblk.ttf", 340, (1300, 180), "mm", tracking=30, shape=(360, 2600))
t = np.clip((y - 556) / 150, 0.0, 1)  # 0 at far edge, near the bottom of the frame at 1
d, d0, d1 = 1 / (t + 2.2), 1 / 2.2, 1 / 3.2
sx = 1300 + (x - 640) * d * 6.9
sy = 360 * (d0 - d) / (d0 - d1)
letters = sample(tm, sx, sy) * (y > 556) * (y < 706)
letters = np.clip(letters + 0.4 * blur(letters, 5), 0, 1)
rgb = rgb * (1 - letters[..., None]) + letters[..., None] * lin(hexc("#ff3a2c")) * 1.5
rgb = rgb + blur(letters, 24)[..., None] * red * 0.5

rgb = rgb * (1 - edge[..., None]) + ap * edge[..., None]
rgb = rgb + blur(m, 3)[..., None] * (1 - edge[..., None]) * red * 0.5


# two small people, for scale, hard black against the light
def person(cx, base, h):
    a = np.zeros((H, W), np.float32)
    r = h * 0.085
    a = np.maximum(a, sstep(r + 0.7, r - 0.7, np.hypot(x - cx, y - (base - h + r))))
    tt = np.clip((y - (base - h + 2.1 * r)) / (h - 2.1 * r), 0, 1)
    wd = (h * 0.135 * (1 - 0.55 * tt ** 1.3) * (1 - 0.5 * (1 - sstep(0, 0.1, tt))))
    body = sstep(0.7, -0.7, np.abs(x - cx) - wd) * (y > base - h + 2.1 * r) * (y < base)
    return np.maximum(a, body)


b = np.maximum(person(596, 546, 44), person(622, 549, 40))
rgb = rgb * (1 - b[..., None])
sh = b
refl = sample(sh, x, 2 * 548 - y) * sstep(600, 548, y) * 0.5
rgb = rgb * (1 - refl[..., None] * 0.8)

lab = text(LABEL, "bahnschrift.ttf", 21, (1248, 40), "rm", tracking=1)
rgb = np.clip(rgb, 0, None)
out = to_srgb(rgb)
out = over(out, hexc("#ffffff"), lab)
finish(out, "b1_light_field.png")
