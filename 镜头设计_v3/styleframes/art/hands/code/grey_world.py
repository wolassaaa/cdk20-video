"""HKBU SCIE1007 coursework science video. Hands: the one grade every phone clip goes through. Nothing is cut out: the whole frame stays, and only colour changes.
1 skin channel: a soft window on Cb and Cr. 2 everything outside it loses its colour. 3 the grey is pulled to the film's ash values and given a little ash grain. Inside the window the skin is left alone apart from a small lift.
Because only saturation changes, there is no matte edge to clean. grade_frame() takes any RGB frame, float 0 to 1."""
import sys

from hk import *
from phone import frame

CR = (138, 146, 168, 178)     # ramp up, ramp down, 8-bit
CB = (84, 92, 122, 130)


def ramp(x, a, b, c, d):
    return np.clip((x - a) / (b - a), 0, 1) * np.clip((d - x) / (d - c), 0, 1)


def skin_channel(rgb, soft=2.0):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cr = (0.5 * r - 0.4187 * g - 0.0813 * b) * 255 + 128
    cb = (-0.1687 * r - 0.3313 * g + 0.5 * b) * 255 + 128
    m = ramp(gblur(cr, 1.0), *CR) * ramp(gblur(cb, 1.0), *CB)
    # no very dark or blown pixels: shadow and window frames should not qualify
    l = rgb.mean(-1)
    m = m * np.clip((l - 0.16) / 0.10, 0, 1) * np.clip((0.97 - l) / 0.05, 0, 1)
    return np.clip(gblur(m, soft), 0, 1)


def grade_frame(rgb, tone=0.36, grain=True):
    m = skin_channel(rgb)[..., None]
    l = rgb.mean(-1, keepdims=True)
    lo, hi = np.percentile(l, 2), np.percentile(l, 98)
    g = np.clip((l - lo) / max(hi - lo, 1e-3), 0, 1) ** 1.25 * (tone * 1.7)
    grey = np.repeat(g, 3, -1)
    if grain and rgb.shape[0] == H and rgb.shape[1] == W:
        n, _ = ash(None, tone=1.0, seed=51)
        grey = grey * (0.86 + 0.14 * n)
    sk = l + (rgb - l) * 0.92
    sk = np.clip(sk ** 0.96, 0, 1)
    return grey * (1 - m) + sk * m, m[..., 0]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 140
    f = frame(n)
    y0 = 300
    crop = f[y0:y0 + 405]
    im = Image.fromarray((crop * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    rgb = np.asarray(im, np.float32) / 255
    out, m = grade_frame(rgb)
    panels = [rgb, np.repeat(m[..., None], 3, -1), np.repeat(rgb.mean(-1, keepdims=True), 3, -1) * (1 - m[..., None]) + rgb * m[..., None], out]
    lab = ["1 phone frame, untouched", "2 skin channel (Cb, Cr window)", "3 everything else loses colour", "4 grey pulled to ash, grain added"]
    w, h = 960, 540
    sheet = np.zeros((h * 2 + 96, W, 3), np.float32) + 0.04
    f2 = font(MONO, 24)
    for i, p in enumerate(panels):
        s = np.asarray(Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS), np.float32) / 255
        x, y = (i % 2) * w, (i // 2) * (h + 48)
        sheet[y:y + h, x:x + w] = s
        t = sprite_text(lab[i], f2, pad=2)
        a = Image.new("L", (W, sheet.shape[0]), 0)
        a.paste(t, (x + 14, y + h + 10))
        am = np.asarray(a, np.float32)[..., None] / 255
        sheet = sheet * (1 - am) + am * 0.88
    Image.fromarray((np.clip(sheet, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILL / "T2_pipeline.png")
    print("wrote T2_pipeline.png", sheet.shape)
