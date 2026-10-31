"""HKBU SCIE1007 coursework science video. Lantern colour script: eight segments, width set by running time, cut from the real frames of this direction."""
from lk import *

CW, CH, PH = 1920, 480, 436
SEC = [141, 142, 129, 213, 139, 151, 49, 99]
TIME = ["2:21", "2:22", "2:09", "3:33", "2:19", "2:31", "0:49", "1:39"]


def still(n):
    return Image.open(OUT / f"{n}.png").convert("RGB")


def cut(im, box, w, h):
    """Crop centred on the box, trimmed to the panel's shape, so nothing is stretched."""
    x0, y0, x1, y1 = box
    a = w / h
    bw, bh = x1 - x0, y1 - y0
    if bw / bh > a:
        nw = bh * a
        x0 += (bw - nw) / 2
        x1 = x0 + nw
    else:
        nh = bw / a
        y0 += (bh - nh) / 2
        y1 = y0 + nh
    return im.crop((int(x0), int(y0), int(x1), int(y1))).resize((w, h), Image.LANCZOS)


def s8():
    """The last segment has no still of its own: one small warm lamp left on black."""
    c = blank()
    fig, (lx, ly) = walker(900.0, 930.0, 3.2)
    dist = np.hypot(xx - lx, yy - ly)
    ang = np.arctan2(yy - ly, xx - lx)
    da = np.abs(np.angle(np.exp(1j * (ang - np.radians(-62.0)))))
    c = add(c, fft_blur(((da < np.radians(13.0)) & (dist < 330)).astype(np.float32), 0.7) * 0.34, AMBER)
    c = lay(c, fig, AMBER)
    c = add(c, (dist < 9).astype(np.float32), AMBER_HI)
    return Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8))


def s5_number():
    """Right half of S5: the number and its solid plate, in the colours of T5, without cut-off words."""
    c = blank()
    n = stencil("3", 330, 800, 760, 560)
    c = add(c, extrude(n, 62, 40) * (1 - n) * 0.16, AMBER)
    c = lay(c, n, AMBER_HI)
    c = lay(c, Layer(W, H, 2).rect(760, 640, 960, 700).a(), AMBER)
    return Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8))


def s7():
    """S7 is short and nearly all chalk: one dashed door, one small amber lamp left under it."""
    c = blank()
    c = lay(c, dash([(1094, 300), (1204, 300), (1204, 730), (1094, 730)], closed=True, width=4), CHALK)
    fig, (lx, ly) = walker(1140.0, 960.0, 2.6)
    c = lay(c, fig, AMBER)
    c = add(c, (np.hypot(xx - lx, yy - ly) < 8).astype(np.float32), AMBER_HI)
    return Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8))


t1, t2, t3, t4, t5, t6 = [still(f"T{i}") for i in range(1, 7)]
xs = [0]
for s in SEC:
    xs.append(xs[-1] + s)
xs = [round(x / xs[-1] * CW) for x in xs]
wd = [b - a for a, b in zip(xs[:-1], xs[1:])]

sheet = Image.new("RGB", (CW, CH), tuple(int(v * 255) for v in BLACK))
sheet.paste(cut(t1, (800, 60, 1440, 1040), wd[0], PH), (xs[0], 0))
sheet.paste(cut(t2, (930, 0, 1500, 970), wd[1], PH), (xs[1], 0))
sheet.paste(cut(t3, (20, 30, 650, 1020), wd[2], PH), (xs[2], 0))
sheet.paste(cut(t4, (690, 0, 1643, 1080), wd[3], PH), (xs[3], 0))
# S5 runs cold stripes, then dots, then solid amber once the number lands
a = wd[4] // 2
sheet.paste(cut(t5, (1400, 112, 1672, 940), a, PH), (xs[4], 0))
sheet.paste(cut(s5_number(), (700, 140, 1000, 900), wd[4] - a, PH), (xs[4] + a, 0))
sheet.paste(cut(t6, (760, 250, 1120, 790), wd[5], PH), (xs[5], 0))
sheet.paste(cut(s7(), (1040, 0, 1258, 1080), wd[6], PH), (xs[6], 0))
sheet.paste(cut(s8(), (690, 0, 1133, 1080), wd[7], PH), (xs[7], 0))

d = ImageDraw.Draw(sheet)
ch = tuple(int(v * 255) for v in CHALK)
f = noto(20, 600)
for i, x in enumerate(xs[:-1]):
    d.text((x + 8, PH + 13), f"S{i + 1} {TIME[i]}", font=f, fill=ch)
    if i:
        d.line([(x, PH + 8), (x, CH - 8)], fill=ch, width=2)
        d.line([(x, 0), (x, PH)], fill=(40, 40, 40), width=2)
sheet.save(OUT / "colour_script.png")
print("saved colour_script.png", sheet.size, wd)
