"""HKBU SCIE1007 coursework science video. T2 papers: the warm fibre print of the person, and the question sheet."""
import sys
sys.path.insert(0, '.')
from ink import *
from grade import srgb, shoulder

a = np.load('../_work/person.npy').astype(np.float64)
c = srgb(shoulder(a, 1.5)) ** 1.5
g = c.mean(-1, keepdims=True)
# warm grade any phone clip can take: pull most of the colour out, then tone shadows brown and highlights cream, so white balance stops mattering
toned = np.array([0.20, 0.07, 0.04]) * (1 - g) ** 2 + np.array([1.0, 0.80, 0.54]) * g ** 0.92
out = toned * 0.8 + c * np.array([1.06, 0.96, 0.82]) * 0.2
W, H = 2400, 3000
M = 150
IW, IH = W - 2 * M, H - 2 * M
im = Image.fromarray((np.clip(out, 0, 1) * 255).astype('uint8'))
s = max(IW / im.width, IH / im.height)
im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
l, t = (im.width - IW) // 2, (im.height - IH) // 2
im = im.crop((l, t, l + IW, t + IH))
pa = np.ones((H, W, 3)) * np.array([240, 229, 208.])
pa *= (0.965 + 0.035 * lf(W, H, 14, 21))[..., None]
pa[M:M + IH, M:M + IW] = np.asarray(im, float)
Image.fromarray(np.clip(pa, 0, 255).astype('uint8')).save('../_work/t2_person.png')

# question sheet
W, H = 2200, 1320
pa = np.ones((H, W, 3)) * np.array([236, 230, 216.])
pa *= (0.97 + 0.03 * lf(W, H, 14, 22))[..., None]
p = Image.fromarray(np.clip(pa, 0, 255).astype('uint8'))
paste(p, 't2-q', (170, 150), width=1860, color=(16, 12, 12))
p.save('../_work/t2_q.png')
print('t2 ok')
