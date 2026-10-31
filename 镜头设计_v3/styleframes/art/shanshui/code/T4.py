"""HKBU SCIE1007 coursework science video. shanshui direction, shot T4 (W2): CDK20 seen for the first time, as a mountain. Ink only and no seal, because this is a prediction. The real low-confidence tail is the summit lost in cloud."""
import time
from sbrush import *

t0 = time.time()
S = surface2()
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
import sys
ry, pitch, D, sc, cx, cy = [float(a) for a in (sys.argv[1:7] or (205, 40, 66, 23, 960, 930))]
name = sys.argv[7] if len(sys.argv) > 7 else "T4.png"
R = rot(0, ry, 0) @ rot(0, 0, 90)
P = persp(R, pitch, D, D * sc, cx, cy, S=S)
print("persp", time.time() - t0)
m = P["mask"]
I = ink_rock(P, seed=3, density=1.25)
print("ink", time.time() - t0)
rng = np.random.default_rng(5)
n1 = fbm(SH, SW, 3.0, 11); n2 = fbm(SH, SW, 2.4, 12)
low = smooth01(.78, .60, gblur(np.where(m > .5, P["conf"], 1), 9))
top = smooth01(20, 400, yy + (n1 - .5) * 260)              # up into nothing
foot = 1 - smooth01(800, 925, yy + (n2 - .5) * 150)         # down into mist
c1 = np.exp(-((yy + (n1 - .5) * 190 - 470) / 44) ** 2) * smooth01(.25, .6, n2)  # one reserved band of cloud across the waist
# air between the ridges: real depth decides what sinks into the blank paper, and more of it sinks the higher you look
zn = (P["z"] - P["zmin"]) / (P["zmax"] - P["zmin"])
zb = gblur(P["z"] * m, 2.5) / np.maximum(gblur(m, 2.5), 1e-3)
zn = (zb - P["zmin"]) / (P["zmax"] - P["zmin"])
hgt = 1 - np.clip(yy / 900, 0, 1)
thr = .16 + .40 * hgt + (n1 - .5) * .30
air = smooth01(thr - .10, thr + .13, zn)
frame = top * foot * (1 - .92 * c1) * (.30 + .70 * air)
kw = np.clip(frame * (1 - .92 * low), 0, 1)                 # the tail keeps no wash at all
ks = dissolve(np.clip(frame * 1.25, 0, 1))        # only dry lines survive up there
base = paper(seed=2)
rgb = far_hills(base, 800, 240, .15, 41)
rgb = far_hills(rgb, 850, 150, .20, 45, 110)
hide = np.clip(gblur(m, 2) * foot * 1.2, 0, 1)[..., None]    # far hills never show through the near rock
rgb = rgb * (1 - hide) + base * hide
trees = ridge_trees([m], rng, 880, n=420, size=(7, 18))
rgb = lay(rgb, I, kw, ks)
tk = trees * ks
rgb = rgb * (1 - tk[..., None] * .95) + INK * tk[..., None] * .95
rgb = ripples(rgb, 905, 1076, rng, 90)
rgb = boat(rgb, 1500, 962, 1.0)
tag = text_mask(LABEL, vf(SERIF, 36, 600), (60, 1030), "ls", w=SW, h=SH)
rgb = over(rgb, INK, tag * .96)
save_still(rgb, name)
print("done", time.time() - t0)
