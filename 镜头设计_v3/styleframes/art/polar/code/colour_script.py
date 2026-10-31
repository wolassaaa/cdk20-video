"""HKBU SCIE1007 coursework science video. polar direction, colour script: eight sections by running time, the height of the colour is how far the sheet has swung."""
import plib
from plib import *

CW, CH = 1920, 480
secs = [("S1", 141), ("S2", 142), ("S3", 129), ("S4", 213), ("S5", 139), ("S6", 151), ("S7", 49), ("S8", 99)]
times = ["2:21", "2:22", "2:09", "3:33", "2:19", "2:31", "0:49", "1:39"]
tot = sum(s for _, s in secs)
grey = [.62, .80, .15, .10, .80, .80, .80, .84]      # tone of the grey world in each section
share = [.05, .05, .012, .86, .44, .50, .50, .42]    # share of the strip the colour takes
edges = np.round(np.cumsum([0] + [s for _, s in secs]) / tot * CW).astype(int)

src = np.asarray(Image.open(STILLS / "T4.png").convert("RGB"), np.float32)[:760, 200:1500] / 255
tex = np.asarray(Image.fromarray((src * 255).astype(np.uint8)).resize((CW, CH), Image.LANCZOS), np.float32) / 255
c2 = np.asarray(Image.fromarray((src[::-1] * 255).astype(np.uint8)).resize((CW, CH), Image.LANCZOS), np.float32) / 255

X = np.arange(CW)
h = np.zeros(CW); g = np.zeros(CW)
for i in range(8):
    h[edges[i]:edges[i + 1]] = share[i]; g[edges[i]:edges[i + 1]] = grey[i]
# the swing in S4 lands a third of the way in, not on the section line
s4 = edges[3]; turn = s4 + int((edges[4] - s4) * .3)
h[s4:turn] = share[2]; g[s4:turn] = .10
s5 = edges[4]; h[s5 + int((edges[5] - s5) * .55):edges[5]] = .68   # second turn: the key
w = 46
h = np.convolve(np.pad(h, w, mode="edge"), np.ones(2 * w + 1) / (2 * w + 1), "same")[w:-w]
g = np.convolve(np.pad(g, 22, mode="edge"), np.ones(45) / 45, "same")[22:-22]

yy2, xx2 = np.mgrid[0:CH, 0:CW].astype(np.float32)
col_h = 400
edge_y = h[None, :] * col_h
a = np.clip((edge_y - yy2) / 1.5 + .5, 0, 1)[..., None]
warm = np.clip((X - edges[7]) / 60, 0, 1)[None, :, None] * np.array([0, -.012, -.05], np.float32)
base = g[None, :, None] * (np.array([1, .995, .975], np.float32) + warm) * np.ones((CH, CW, 3), np.float32)
rgb = base * (1 - a) + tex * a
rgb = rgb + (np.exp(-((yy2 - edge_y) / 1.4) ** 2) * (edge_y > 1))[..., None] * .8

im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)); d = ImageDraw.Draw(im)
d.rectangle([0, 408, CW, CH], fill=(204, 203, 198))
f = sans(30, 700); f2 = sans(24, 500)
for i, (n, _) in enumerate(secs):
    x = int(edges[i]); d.line([x, 0, x, CH], fill=(20, 20, 22), width=2)
    d.text((x + 12, 412), n, (19, 19, 20), font=f)
    d.text((x + 12, 446), times[i], (19, 19, 20), font=f2)
im.save(STILLS / "colour_script.png")
