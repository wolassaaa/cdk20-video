"""HKBU SCIE1007 coursework science video. Style scout b5: strictly one bit. 346 vertical bars are the 346 real residues, the real CDK20 inverts them and a line screen carves its surface."""
import json

import numpy as np

from common import *

P = load()
V = view(P, zoom=1.2, at=(640, 268), src=(950, 545))
y, x = grid()
m = V["mask"]
hard = m > 0.5

plddt = np.array(json.load(open(PLDDT, encoding="utf8"))["score"], float) / 100
seq = json.load(open(SEQ, encoding="utf8"))["seq"]
print(len(plddt), len(seq), seq[:12])

# one bar per residue, 3 px each, so 346 bars take exactly 1038 px and the rest of the frame stays solid black
SLOT, X0 = 3, 121
i = np.clip(((x - X0) / SLOT).astype(np.int32), 0, 345)
inside = (x >= X0) & (x < X0 + 346 * SLOT)
ink = np.array([2 if (ord(c) - 65) % 3 else 1 for c in seq])
bars = inside & (((x - X0).astype(np.int32) % SLOT) < ink[i])

# low confidence residues break the bars into fine dashes, real data from pLDDT
low = plddt[i] < 0.7
dash = (y % 4) < 1
bars = np.where(low, bars & dash, bars)

# protein: horizontal line screen, line thickness tracks the light, nothing is grey
light = np.clip(0.2 + 1.0 * V["key"] + 0.75 * V["rim"], 0, 1) * (0.35 + 0.65 * V["ao"])
light = blur(light * m, 0.8) / np.maximum(blur(m, 0.8), 0.05)
PITCH = 6
phase = (y % PITCH) / PITCH
lines = phase < np.clip(light, 0.04, 0.96)

# depth-staircase: the screen shifts by a pixel per contour so the form bends the lines
contour = (V["depth"] * 26).astype(np.int32)
lines2 = ((y + contour * 2) % PITCH) / PITCH < np.clip(light, 0.04, 0.96)

img = np.where(hard, lines2, bars)

# real numbers in the margins as microtype: index, letter, pLDDT, one row per residue until the column is full
col = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(col)
f = font("consola.ttf", 10)
for k in range(69):
    d.text((8, 2 + k * 10), f"{k + 1:03d} {seq[k]} {plddt[k] * 100:5.2f}", 255, font=f)
    r = 277 + k
    d.text((1166, 2 + k * 10), f"{r + 1:03d} {seq[r]} {plddt[r] * 100:5.2f}", 255, font=f)
micro = (np.asarray(col) > 110) & (y < 688)
img = img | micro

# name: solid white slab with a black keyline, the only flat area in the frame
t = text("CDK20", "arialbd.ttf", 244, (640, 582), "mm", tracking=4) > 0.5
ring = blur(t.astype(np.float32), 2.2) > 0.1
img = np.where(ring, False, img)
img = np.where(t, True, img)

# data strip: solid black band and white band so the frame has a horizon
band = (y >= 690) & (y < 720)
img = np.where(band, False, img)
lab = text(LABEL, "arial.ttf", 19, (20, 705), "lm", tracking=1) > 0.4
num = text("346 aa", "arial.ttf", 19, (1260, 705), "rm", tracking=1) > 0.4
img = np.where(band & (lab | num), True, img)

rgb = np.repeat(img[..., None].astype(np.float32), 3, -1)
save(rgb, str(OUT / "b5_binary_data.png"))
print("saved b5")
