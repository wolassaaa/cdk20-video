"""HKBU SCIE1007 coursework science video. Style scout b3: a wall of raw red pigment with the real CDK20 pressed in as a cavity. Its rim catches light, its centre is true zero black."""
import numpy as np

from common import *

P = load()
V = view(P, zoom=1.36, at=(640, 268), src=(950, 545), rot=-8)
y, x = grid()
m = V["mask"]
hard = (m > 0.5).astype(np.float32)

# raw pigment wall, dead matte, soft raking light from upper left
grain = noise(5, 6, slope=0.6)
drift = noise(6, 300, slope=2.2)
rake = 0.72 + 0.34 * (1 - (x / W * 0.6 + y / H * 0.4)) + 0.22 * (drift - 0.5)
wall = lin(hexc("#d80f12")) * (rake * (0.9 + 0.2 * grain))[..., None]

# the cavity: normals flipped so every bump reads as a dent, light slides in from the rim only
n = V["normal"]
ld = np.array([-0.55, 0.62, 0.56], np.float32)
ld /= np.linalg.norm(ld)
inv = n * np.array([-1, -1, 1], np.float32)
lam = np.clip((inv * ld).sum(-1), 0, 1)
wet = np.clip(lam, 0, 1) ** 1.6 * (0.3 + 0.7 * V["ao"])

# distance from the lip, measured from a blurred mask: the deep interior goes to exactly zero
lip = blur(hard, 62)
reach = 1 - sstep(0.62, 0.97, lip)
inside = (0.05 + wet * 3.0) * reach ** 1.25
cav = lin(hexc("#ff1a14"))[None, None] * inside[..., None]
cav = cav * (lip < 0.97)[..., None]

rgb = wall * (1 - m[..., None]) + cav * m[..., None]
rgb = to_srgb(rgb)

# name in the same absolute black, sunk into the bottom of the void so both are one hole
t = text("CDK20", "ariblk.ttf", 176, (640, 628), "mm", tracking=14)
rgb = rgb * (1 - t[..., None])

# the label sits at the bottom of the hole, the only light in the black
lab = text(LABEL, "bahnschrift.ttf", 21, (640, 270), "mm", tracking=2)
rgb = over(rgb, hexc("#ff5a48"), lab)
finish(rgb, "b3_absolute_black.png")
