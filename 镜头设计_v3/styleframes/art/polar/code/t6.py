"""HKBU SCIE1007 coursework science video. polar direction, still T6: the road map as a rack of six glass panes.
The sheet edge itself is the progress marker: it stands at the door of station 4. Panes 1-3 look through the sheet, panes 4-6 are dashed empty glass."""
from plib import *

y0, y1 = 110, 690
xb0, pitch, pw = 56, 272, 240
door_x = xb0 + 3 * pitch - 14
t = (door_x - PX) / (PY - y1)
sh = (y1 - y0) * t
print("t", t)
Pf, Tf = field(seed=8)
c = limit(photo(Pf, Tf, 12, shift=.10, seed=2, height=.055) * 1.12, .84)
pal_ = plaster(Pf, 12, grey_world(.82))
grey = grey_world(.82) * .72 + pal_ * .28
black = np.zeros((H, W, 3), np.float32)


def pane(i):
    x = xb0 + i * pitch
    return [(x + sh, y0), (x + pw + sh, y0), (x + pw, y1), (x, y1)]


lit = np.zeros((H, W), np.float32)
for i in range(3):
    lit = np.maximum(lit, poly(pane(i)))
dark = black * (1 - lit[..., None]) + c * lit[..., None]
for i in range(3):
    q = pane(i)
    e = np.zeros((H, W), np.float32)
    for a, b in zip(q, q[1:] + q[:1]):
        e = np.maximum(e, seg(a, b, 2))
    dark = over(dark, (.95, .94, .9), e * .9)

plain = grey_world(.82)
for i in range(3, 6):
    m = poly(pane(i))
    plain = plain * (1 - m[..., None]) + grey * m[..., None]
rgb = sheet(dark, plain, t)
for i in range(3, 6):
    q = pane(i)
    for a, b in zip(q, q[1:] + q[:1]):
        rgb = over(rgb, INK, seg(a, b, 3.5, 17, 11))

# road: solid while lit, dashed after the door
ry = 722
rgb = over(rgb, (.95, .94, .9), seg((xb0, ry), (door_x - 10, ry), 7))
rgb = over(rgb, INK, seg((door_x + 34, ry), (W - 56, ry), 5, 18, 12))

names = [["Target"], ["Hit"], ["Improve"], ["Cells &", "animals"], ["Clinical trials", "1-2-3"], ["Approval"]]
f = sans(38, 700)
for i, n in enumerate(names):
    x = xb0 + i * pitch
    if i < 3:
        rgb = over(rgb, PAPER, poly([(x, 748), (x + pw, 748), (x + pw, 826), (x, 826)]))
        rgb = put(rgb, n[0], (x + 18, 802), f)
    else:
        x += 26 if i == 3 else 14
        for j, l in enumerate(n):
            rgb = put(rgb, l, (x, 786 + j * 48), f)
        rgb = put(rgb, "not reported", (x, 930), sans(36, 500))
        rgb = over(rgb, INK, seg((x, 946), (x + 214, 946), 2.5, 9, 7))

# 048 stands where the light stops
mx = door_x - 46
rgb = over(rgb, (.95, .94, .9), poly([(door_x - 10, ry), (door_x - 34, ry - 15), (door_x - 34, ry + 15)]))
rgb = put(rgb, "048", (line_x(t, 960) - 26, 960), serif(104, 900), (.95, .94, .9), "rs")
save(rgb, "T6.png")
