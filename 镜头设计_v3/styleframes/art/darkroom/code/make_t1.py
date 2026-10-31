"""HKBU SCIE1007 coursework science video. Builds the T1 paper: the liver as a silver print, wide lower border carrying the number. Texture only."""
import sys; sys.path.insert(0, '.')
from ink import *
from grade import srgb, shoulder
a = np.load('../_work/liver_img.npy').astype(np.float64)
g = a.mean(-1)
g = srgb(shoulder(g, 1.9)) ** 1.15
W, H = 3000, 2200
M, B = 110, 410
IW, IH = W - 2 * M, H - M - B
im = Image.fromarray((np.clip(g, 0, 1) * 255).astype('uint8'))
s = max(IW / im.width, IH / im.height)
im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
l, t = (im.width - IW) // 2, (im.height - IH) // 2
im = im.crop((l, t, l + IW, t + IH))
pa = np.ones((H, W, 3)) * np.array([236, 230, 216.])
pa *= (0.97 + 0.03 * lf(W, H, 20, 11))[..., None]
im_a = np.asarray(im, float) / 255
# silver tone: black is not zero, and the paper base shows in the highlights
im_rgb = 10 + im_a[..., None] * (np.array([232, 226, 212.]) - 10)
pa[M:M + IH, M:M + IW] = im_rgb
p = Image.fromarray(np.clip(pa, 0, 255).astype('uint8'))
sz = paste(p, 't1-num', (M + 20, H - B + 70), height=232, color=(14, 12, 12))
paste(p, 't1-rest', (M + 20 + sz[0] + 60, H - B + 150), height=118, color=(14, 12, 12))
p.save('../_work/t1_print.png'); print(p.size)
