"""HKBU SCIE1007 coursework science video. Small textures for the darkroom stills that have no script of their own: the T4 tray floor and the T3 chalk outline. Writes into _work/. The T4 tag is built here too, from the rendered type layer."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from ink import fit, lf as ink_lf


def floor():
    W, H = 3000, 2100

    def lf(sig, seed):
        r = np.random.default_rng(seed).random((H // 8, W // 8))
        im = Image.fromarray((r * 255).astype('uint8')).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(sig))
        a = np.asarray(im, float) / 255
        return (a - a.min()) / (a.max() - a.min())

    wash = lf(60, 1) * .6 + lf(12, 2) * .3 + lf(3, 5) * .1
    deep, mid = np.array([9, 30, 74.]), np.array([22, 66, 140.])
    a = deep[None, None] + (mid - deep)[None, None] * wash[..., None]
    g = np.zeros((H, W), float)
    for x in range(0, W, 150):
        g[:, x:x + 3] = 1
    for y in range(0, H, 150):
        g[y:y + 3, :] = 1
    for x in range(0, W, 750):
        g[:, x:x + 6] = 1
    for y in range(0, H, 750):
        g[y:y + 6, :] = 1
    g = np.asarray(Image.fromarray((g * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2)), float) / 255
    g *= .35 + .65 * lf(20, 8)
    a = a + (np.array([214, 226, 240.]) - a) * (g * 0.62)[..., None]
    Image.fromarray(np.clip(a, 0, 255).astype('uint8')).save('../_work/blue_floor.png')


def dash():
    S, k = 2048, 2048 / 16
    c = lambda x, y: (S / 2 + x * k, S / 2 - y * k)
    rng = np.random.default_rng(5)
    R, FB, FH = 1.42, 1.23, 2.64
    ang = np.linspace(math.radians(-64), math.radians(244), 260)
    top = [(R * math.cos(t), R * math.sin(t) + .7) for t in ang]
    low = .7 - .93 - FH
    pts = np.array(top + list(np.linspace(top[-1], [-FB, low], 40)) + list(np.linspace([-FB, low], [FB, low], 50)) + list(np.linspace([FB, low], top[0], 40)))
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    L, pos = s[-1], 0
    im = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(im)
    while pos < L:
        e = min(pos + rng.uniform(.26, .34), L)
        t = np.linspace(pos, e, 16)
        xy = np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], -1) + rng.normal(0, .012, (16, 2)).cumsum(0) * .5
        d.line([c(*p) for p in xy], fill=255, width=int(rng.uniform(5, 7)))
        pos = e + rng.uniform(.15, .22)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(1)), float)
    gr = np.random.default_rng(9).random((S, S))
    a = a * (gr > .28) * (.7 + .3 * gr)
    a = np.asarray(Image.fromarray(a.astype('uint8')).filter(ImageFilter.GaussianBlur(.8)))
    out = np.zeros((S, S, 4), 'uint8')
    out[..., :3] = (224, 214, 204)
    out[..., 3] = a
    Image.fromarray(out).save('../_work/t3_dash.png')


def tag():
    W, H = 1920, 276
    n = ink_lf(W, H, 10, 4) * .5 + ink_lf(W, H, 2, 5) * .5
    a, b = np.array([14, 46, 104.]), np.array([26, 78, 150.])
    im = Image.fromarray(np.clip(a + (b - a) * n[..., None], 0, 255).astype('uint8'))
    ImageDraw.Draw(im).rectangle((14, 14, W - 15, H - 15), outline=(226, 234, 244), width=5)
    t = fit('t4-tag', width=1780)
    im.paste(Image.new('RGB', t.size, (240, 244, 250)), (70, (H - t.height) // 2), t.split()[3])
    im.save('../_work/t4_tag.png')


if __name__ == '__main__':
    floor()
    dash()
    tag()
    print('misc ok')
