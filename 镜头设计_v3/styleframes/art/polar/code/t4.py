"""HKBU SCIE1007 coursework science video. polar direction, still T4: CDK20 first seen, the sheet swings open. The colour is a look; the label says predicted."""
import sys
from plib import *

views = {"a": (-90, 0, -18, 24, 960, 500), "b": (-60, 30, 10, 24, 980, 540), "c": (-110, -40, 20, 24, 960, 500), "d": (-20, 60, -30, 24, 980, 540)}
pick = sys.argv[1] if len(sys.argv) > 1 else "a"
rx, ry, rz, sc, cx, cy = views[pick]
S = surface(); R = rot(rx, ry, rz)
P = smooth_pass(render(R, sc, cx, cy, W, H, ss=2, S=S), 2.6)
T = thickness(P, R, sc, cx, cy, S)
c = limit(photo(P, T, sc, height=.042) * 1.14, .82)
t = .60
grey = plaster(P, sc, grey_world(.80))
rgb = sheet(c, grey, t)
# predicted plate: outline only, left edge parallel to the sheet edge. Paper inside so it reads over anything
y0, y1, x1 = 856, 1044, 1892
xl = lambda y: line_x(t, y) + 34
q = [(xl(y0), y0), (x1, y0), (x1, y1), (xl(y1), y1)]
rgb = over(rgb, (.86, .855, .835), poly(q))
for a_, b_ in zip(q, q[1:] + q[:1]):
    rgb = over(rgb, INK, seg(a_, b_, 4))
x = xl(y0) + 26
rgb = put(rgb, "AlphaFold DB v6 ·", (x, 918), sans(42, 600))
rgb = put(rgb, "predicted", (x - 34, 1020), sans(86, 800))
save(rgb, f"t4_{pick}_test.png" if len(sys.argv) > 2 else "T4.png")
