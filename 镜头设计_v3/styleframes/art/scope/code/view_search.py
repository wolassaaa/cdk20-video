"""HKBU SCIE1007 coursework science video. Scope direction: finds the rotation of the real CDK20 model where the 303-346 tail reads best, then draws a contact sheet of backbone traces. Numpy and PIL only."""
import json
import numpy as np
from PIL import Image, ImageDraw
V = json.load(open(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/code/cdk20_backbone_view.json"))
ca = np.array([r["ca"] for r in V["res"]])
ca -= ca[:302].mean(0)
def rot(rx, ry, rz=0):
    a, b, c = np.radians([rx, ry, rz])
    X = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    return X @ Y
res = []
for rx in range(-80, 81, 20):
    for ry in range(0, 360, 20):
        R = rot(rx, ry)
        P = ca @ R.T
        b, t = P[:300], P[304:346]
        d = np.sqrt(((t[:, None, :2] - b[None, :, :2]) ** 2).sum(-1)).min(1)
        # score: tail far from the body in projection, or at least in front of it
        s = np.clip(d, 0, 12).mean() + .10 * (t[:, 2].mean() - b[:, 2].mean())
        res.append((float(s), rx, ry))
res.sort(reverse=True)
top = []
for r in res:
    if all(abs(r[1] - q[1]) + min(abs(r[2] - q[2]), 360 - abs(r[2] - q[2])) > 50 for q in top):
        top.append(r)
    if len(top) == 8:
        break
print(top)
S = 360
sheet = Image.new("RGB", (S * 4, S * 2), "black")
d = ImageDraw.Draw(sheet)
for k, (s, rx, ry) in enumerate(top):
    R = rot(rx, ry)
    P = ca @ R.T
    x0, y0 = S * (k % 4) + S / 2, S * (k // 4) + S / 2
    p = [(x0 + q[0] * 4.2, y0 - q[1] * 4.2) for q in P]
    d.line(p[:303], fill=(31, 59, 255), width=2)
    d.line(p[302:], fill=(232, 25, 15), width=3)
    d.text((x0 - 170, y0 - 170), f"rx{rx} ry{ry} s{s:.1f}", fill="white")
sheet.save("../_work/view_sheet.png")
