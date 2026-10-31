"""HKBU SCIE1007 coursework science video. Colour script of the darkroom direction: eight sections left to right, width by real running time, each band cut from a graded frame, with its two working colours under it."""
import os, sys
sys.path.insert(0, '.')
from ink import *
from grade import *

DUR = [141, 142, 129, 213, 139, 151, 49, 99]
HEX = [("B3140C", "160403"), ("C98A4E", "1A0605"), ("4A0704", "050202"), ("1A5AA8", "06112E"), ("B3140C", "123E9A"), ("2A1530", "D9B98A"), ("2B2A3E", "E8DED0"), ("0C0C10", "F2E9D8")]
W, H = 1920, 480
IMG_H, SW_H = 340, 56
xs = np.round(np.cumsum([0] + DUR) / sum(DUR) * W).astype(int)


def still(n):
    return Image.open(os.path.join(STILLS, n + '.png')).convert('RGB')


def s7():
    # slate dusk: the unexposed end of the strip, no words
    a = np.asarray(still('T6').crop((1400, 215, 1520, 435)), float) / 255
    g = a.mean(-1, keepdims=True) ** 0.75
    out = a * 0.3 + g * np.array([0.78, 0.84, 1.08]) * 1.1
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype('uint8'))


def s8():
    a = np.load(os.path.join(WORK, 's8.npy')).astype(np.float64)
    return Image.fromarray((finish(a, 1.0, (1, 0.9, 0.75), 0.5, 0.2) * 255).astype('uint8'))


src = [
    (still('T1'), (500, 120, 1500, 980)),
    (still('T2'), (100, 80, 1600, 960)),
    (still('T3'), (560, 200, 1360, 900)),
    (still('T4'), (260, 120, 1660, 1000)),
    (still('T5'), (560, 120, 1860, 960)),
    (still('T6'), (40, 200, 1760, 880)),
    (s7(), None),
    (s8(), None),
]
sheet = Image.new('RGB', (W, H), (10, 9, 9))
for i, (im, box) in enumerate(src):
    x0, x1 = int(xs[i]), int(xs[i + 1])
    bw = x1 - x0 - 2
    if box:
        im = im.crop(box)
    # crop to the band, keeping the centre of interest
    ar = bw / IMG_H
    w, h = im.size
    if w / h > ar:
        nw = int(h * ar)
        l = (w - nw) // 2
        im = im.crop((l, 0, l + nw, h))
    else:
        nh = int(w / ar)
        t = (h - nh) // 2
        im = im.crop((0, t, w, t + nh))
    sheet.paste(im.resize((bw, IMG_H), Image.LANCZOS), (x0 + 1, 0))
    a, b = HEX[i]
    c = lambda h: tuple(int(h[j:j + 2], 16) for j in (0, 2, 4))
    sheet.paste(Image.new('RGB', (bw // 2, SW_H), c(a)), (x0 + 1, IMG_H + 2))
    sheet.paste(Image.new('RGB', (bw - bw // 2, SW_H), c(b)), (x0 + 1 + bw // 2, IMG_H + 2))
    paste(sheet, f'cs-S{i + 1}', (x0 + 8, IMG_H + SW_H + 8), height=30, color=(232, 226, 214))
    paste(sheet, f'cs-t{i + 1}', (x0 + 8, IMG_H + SW_H + 46), height=18, color=(170, 164, 154))
sheet.save(os.path.join(STILLS, 'colour_script.png'))
print('colour script ok', sheet.size)
