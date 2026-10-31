"""HKBU SCIE1007 coursework science video. manual T3: chapter three, black paper. Nothing is printed on this page. A keyhole is die cut through it and the only thing the lamp finds is the cut edge. No words: the book has run out of anything it can say."""
from mk import *

C = CH[3]
KX, KY, KR = 1350, 400, 150  # same shape as chapter five and the road map, smaller


def keyhole_mask(kx=KX, ky=KY, r=KR, w=SW, h=SH):
    K = Mask(w, h, 2)
    K.ell(kx - r, ky - r, kx + r, ky + r)
    K.poly([(kx - r * 0.58, ky + r * 0.65), (kx + r * 0.58, ky + r * 0.65), (kx + r * 1.17, ky + r * 2.28), (kx - r * 1.17, ky + r * 2.28)])
    return K.a()


def black_spread():
    out = paper(C["paper"], 31, mott=0.04)
    a = keyhole_mask()
    # the hole shows nothing: only its cut edge, a thin lit lip low on the far side and a fainter one all round
    edge = np.clip(gauss(a, 1.2) - gauss(a, 4.5), 0, 1)
    lit_ = np.clip(a - np.roll(np.roll(a, -4, 0), -4, 1), 0, 1)
    out = out * (1 - a[..., None]) + hexc("#020203") * a[..., None]
    out = ink(out, np.clip(edge * 1.1, 0, 0.32), C["spot"])
    out = ink(out, np.clip(gauss(lit_, 0.7) * 1.8, 0, 1), "#d8dce4")
    return out


if __name__ == "__main__":
    Z = 1.25
    rgb = wrap(black_spread(), 0.31, tilt=-1.0, zoom=Z, lamp=(960, 540), fall=720, warm=0.2, pan=(-(KX - SW / 2) * Z, (SH / 2 - KY - 110) * Z), floor=0.28)
    # the lamp gives out before the page edge: nothing else in the book is left
    yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
    d = np.hypot(xx - 960, yy - 540)
    rgb = rgb * np.clip(1 - (d - 330) / 300, 0.05, 1)[..., None]
    save(rgb, ST / "T3.png")
