"""SCAN checks on a rendered PNG sequence: contact sheet, flicker metric (brief), palette rule for red, WCAG flash count.
python check.py <seq_dir> <out_contact.jpg>"""
import sys, glob, numpy as np
from PIL import Image, ImageFilter

seq, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(seq + "/*.png"))
print(len(files), "frames")
step = 15
thumbs = files[::step]
cols = 5; tw, th = 384, 216
rows = int(np.ceil(len(thumbs) / cols))
sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
for i, f in enumerate(thumbs):
    sheet.paste(Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
sheet.save(out, quality=90)


def load(i):
    return np.asarray(Image.open(files[i]).convert("RGB"), dtype=np.float32)


# flicker: mean high-frequency part of consecutive-frame difference (diff minus its 3 px Gaussian blur)
def hf(a, b):
    d = np.abs(a - b).mean(2)
    bl = np.asarray(Image.fromarray(np.clip(d, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)
    return float(np.abs(d - bl).mean())


for lo, hi in ((86, 96), (118, 126), (205, 212), (280, 299)):
    v = [hf(load(i), load(i + 1)) for i in range(lo, hi)]
    print(f"flicker f{lo}-{hi}: mean {np.mean(v):.4f} max {np.max(v):.4f}")

# palette + flash over all frames
L = np.array([0.2126, 0.7152, 0.0722])
lum, redA, bad, worst = [], [], [], (0, 0)
for i, f in enumerate(files):
    a = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    lin = (a / 255.0) ** 2.2
    lum.append(float((lin * L).sum(2).mean()))
    red = (R - G > 25) & (R > 40)
    redA.append(float(red.mean()))
    viol = red & ~((G < 0.35 * R) & (B <= G * 1.3 + 2))
    bad.append(int(viol.sum()))
    if viol.sum() > worst[1]:
        worst = (i, int(viol.sum()))
print("red pixels violating G<0.35R, B<=1.3G: total", sum(bad), "worst frame", worst)
print("frames with violations", [(i, b) for i, b in enumerate(bad) if b > 0][:30])
redA = np.array(redA); lum = np.array(lum)
# WCAG: a red flash = a rise and fall of saturated red; count local maxima above 25% of the max per 1 s window
d = np.diff(redA)
peaks = [i for i in range(1, len(redA)) if redA[i] > 0.02 and redA[i - 1] <= 0.02]   # one flash = one rise through 2% of the frame
print("red flash onsets at frames", peaks, "max red area share", round(float(redA.max()), 3))
w = [sum(1 for p in peaks if s <= p < s + 30) for s in range(0, 271)]
print("max red flashes in any 1 s window:", max(w))
print("luminance min/max", round(float(lum.min()), 4), round(float(lum.max()), 4))
