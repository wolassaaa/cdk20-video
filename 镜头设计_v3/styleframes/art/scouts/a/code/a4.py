"""HKBU SCIE1007 coursework science video. Style scout a4, op art: black and white lines fill the frame and the real CDK20 surface pushes them up from behind. No shading tool, only line position and line weight."""
import sys
from kit import *

SS = 2
w, h = W * SS, H * SS
R = rot(0, -14, 10) @ base_view()
V = view(R, scale=12.6 * SS, cx=835 * SS, cy=352 * SS, w=w, h=h, ss=0.35, L=(-0.5, 0.7, 0.5))
m = V["mask"]
zr = V["z"][m > 0.5]
zn = np.clip((V["z"] - np.percentile(zr, 1)) / (np.percentile(zr, 99) - np.percentile(zr, 1)), 0, 1) * m
hh = fft_blur(zn, 1.6 * SS)
big = fft_blur((m > 0.5).astype(np.float32), 70 * SS)
big2 = fft_blur((m > 0.5).astype(np.float32), 200 * SS)
tone = np.clip(0.12 + 1.1 * V["key"] ** 0.9, 0, 1) * (0.55 + 0.45 * V["ao"])
tone = fft_blur(tone, 1.0 * SS)
fieldmask = fft_blur((m > 0.5).astype(np.float32), 0.7 * SS)

y, x = np.mgrid[0:h, 0:w].astype(np.float32)
x /= SS
y /= SS
P = 15.0

Tx = Layer(w=W, h=H, ss=3)
block_word(Tx, "CDK20", lambda i: affine(30 + i * 92, 524, 80, 170))
letters = resize(Tx.a(), w, h)


def stripes(amp=95, amp_big=70):
    ph = (y - amp * hh - amp_big * big - 60 * big2) / P
    # weight follows light on the protein; flat bars outside
    duty = 0.5 + (0.26 - 0.56 * tone) * fieldmask
    a = ph - np.floor(ph)
    v = np.abs(a - 0.5) * 2  # 0 at bar centre, 1 at gap centre
    return smooth(duty - v, -0.06, 0.06)


def check(amp=11):
    hb = fft_blur(hh + 2.2 * big, 2.5 * SS)
    gy, gx = np.gradient(hb)
    S = (amp * SS) / max(np.abs(gx).max(), 1e-5) * 6
    u = (x - gx * S / SS) / (P * 1.4)
    v = (y - gy * S / SS) / (P * 1.4)
    return ((np.floor(u) + np.floor(v)) % 2).astype(np.float32)


def out(g):
    rgb = np.stack([g] * 3, -1)
    rgb = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS), np.float32) / 255
    return rgb


if len(sys.argv) > 1:
    s = Image.new("L", (1280, 360))
    for i, g in enumerate([1 - stripes(), check()]):
        s.paste(Image.fromarray((out(g)[..., 0] * 255).astype(np.uint8)).resize((640, 360), Image.LANCZOS), (i * 640, 0))
    s.save(OUT / "code/_a4_sheet.png")
    sys.exit()

g = 1 - stripes()
key = np.clip(resize(fft_blur(Tx.a(), 3.2), w, h) * 7, 0, 1)
g = g * (1 - key) + key  # bars stop on a white keyline, the letters are solid black
g = g * (1 - letters)
rgb = out(g)
Bx = Layer().rect(30, 476, 438, 512).a()
rgb = ink(rgb, Bx, (0, 0, 0))
rgb = ink(rgb, Layer().text((44, 502), "AlphaFold DB v6 · predicted", "arialbd.ttf", 24, track=0.4).a(), (255, 255, 255))
save(rgb, "a4_op_art.png")
