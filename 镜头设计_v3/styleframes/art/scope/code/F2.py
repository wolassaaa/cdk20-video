"""HKBU SCIE1007 coursework science video. Scope direction, frame F2 (script 2-02): a person asks the question, and the road map shows nothing has started yet.
The person is a placeholder: a flat outline, not a fake human. Phone footage drops into the same round field, see the direction note."""
from scopelib import *

cx, cy, R = 430, 424, 372
rgb = blank()
f = disc(cx, cy, R)
rgb = over(rgb, BONE, f * .07)
# flat placeholder: head and shoulders outline, plainly not a person
im, d = layer()
k = SS
d.ellipse(((cx - 104) * k, (cy - 196) * k, (cx + 104) * k, (cy + 34) * k), fill=255)
d.rounded_rectangle(((cx - 250) * k, (cy + 76) * k, (cx + 250) * k, (cy + 520) * k), radius=150 * k, fill=255)
sil = done(im) * f
rgb = over(rgb, BONE, sil * .16)
rgb = ring(rgb, cx, cy, R, "solid", w=3)
clean(rgb, "F2")
rgb = text(rgb, "phone footage here", (cx, cy + 250), (mono, 25, 400), BONE, anchor="ms", halo=False)

q = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
for i, l in enumerate(q):
    rgb = text(rgb, l, (872, 268 + i * 92), (sans, 76, 500), BONE, halo=False)

# road map: same six stops as F6. The red flow stops just before the first one
y = 884
xs, x = [], 96
ws = [width(s, 36) for s in STATIONS]
gap = (1920 - 96 * 2 - sum(ws)) / 5
for wd in ws:
    xs.append(x + wd / 2)
    x += wd + gap
rgb = line(rgb, [(xs[0] - 60, y), (xs[-1], y)], BONE, 2.4, .5)
rgb = line(rgb, [(0, y), (xs[0] - 26, y)], RED, 6)
for xc, s in zip(xs, STATIONS):
    rgb = over(rgb, (0, 0, 0), disc(xc, y, 22))
    rgb = small_ring(rgb, xc, y, 18, "solid", BONE)
    rgb = text(rgb, s, (xc, y + 78), 36, BONE, anchor="ms", halo=False)
purple_check(rgb)
save(rgb, "F2.png")
