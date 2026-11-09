# HKBU SCIE1007 coursework science video. Measures the W5 background layer: (1) brightness range of the layer where the type sits, and the contrast of the palest type colour against it;
# (2) how fast the whole screen changes. Reads W5_bg_4k60_v1.mp4 through ffmpeg (small gray frames), and 3 frames of the layer at full size.
# Run: python measure_w5.py
import subprocess, json
import numpy as np
from PIL import Image

ROOT = "D:/。hkbu/molecular science/"
FF = ROOT + "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
BG = ROOT + "镜头设计_v3/td/w5/W5_bg_4k60_v1.mp4"
FPS = 60


def lin(c):                                            # sRGB 0-255 to linear
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def Y(rgb):
    l = lin(rgb)
    return 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]


def ratio(y1, y2):
    hi, lo = max(y1, y2), min(y1, y2)
    return (hi + 0.05) / (lo + 0.05)


INK, SOFT, RED, BONE = (0x11, 0x11, 0x13), (0x54, 0x54, 0x58), (0xE8, 0x19, 0x0F), (0xED, 0xEB, 0xE4)
print("type colours (luminance Y): ink %.3f, soft grey %.3f, red rule %.3f, bone paper %.3f" % (Y(INK), Y(SOFT), Y(RED), Y(BONE)))
print("contrast of the palest type (soft grey #545458) on plain bone: %.2f : 1" % ratio(Y(SOFT), Y(BONE)))

# (1) three frames of the layer, full size; the type lives in x 420-3420, y 160-2000 (padding 210 px at 1080p, footer line at y 1990-2030)
rows = []
for t in (4.0, 14.0, 31.0):
    p = subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", BG, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    import io
    im = np.array(Image.open(io.BytesIO(p)).convert("RGB"))
    box = im[160:2040, 420:3420]
    y = Y(box)
    lo, hi, p01, p999 = y.min(), y.max(), np.percentile(y, 0.1), np.percentile(y, 99.9)
    rows.append((t, lo, hi))
    print("t=%4.1f s  layer brightness under the type: Y %.3f to %.3f (0.1-99.9%%: %.3f to %.3f); palest type (soft grey) on the darkest spot of the layer: %.2f : 1; ink on it: %.2f : 1; dark spot covers %.2f%% of the area darker than 0.9x bone"
          % (t, lo, hi, p01, p999, ratio(Y(SOFT), lo), ratio(Y(INK), lo), 100 * (y < 0.9 * Y(BONE)).mean()))

# (2) how fast the whole screen changes: 480x270 gray frames at 60 fps
w, h = 480, 270
import os, shutil, glob
TMP = ROOT + "镜头设计_v3/td/w5/_tmp/"                      # this ffmpeg has no rawvideo and only writes inside the project
os.makedirs(TMP, exist_ok=True)
subprocess.run([FF, "-y", "-v", "error", "-i", BG, "-vf", "scale=%d:%d:flags=area,format=gray" % (w, h), TMP + "g_%04d.png"], check=True)
a = np.stack([np.array(Image.open(f)) for f in sorted(glob.glob(TMP + "g_*.png"))]).astype(np.float32)
shutil.rmtree(TMP)
n = len(a)
print("frames read:", n)
mean = a.mean(axis=(1, 2))
d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
print("mean gray level of the whole screen: min %.3f, max %.3f (of 255); largest change between two frames %.4f levels" % (mean.min(), mean.max(), d.max()))
# whole-screen brightness cycles per second: spectrum of the mean level, strongest component
m0 = mean - mean.mean()
sp = np.abs(np.fft.rfft(m0 * np.hanning(n)))
fr = np.fft.rfftfreq(n, 1 / FPS)
print("whole-screen brightness: strongest cycle %.3f per second (peak-to-peak %.3f levels)" % (fr[1:][sp[1:].argmax()], mean.max() - mean.min()))
# a single spot: how many times a second does a pixel move between 'on a dot or line' and 'bare paper' (crossing the level halfway between its own min and max), worst 1% of pixels
q = a[:, ::3, ::3].reshape(n, -1)
lo, hi = q.min(0), q.max(0)
rng = hi - lo
mid = (lo + hi) / 2
mask = rng > 2.5                                           # pixels that change enough to matter (more than 2.5 of 255)
s = (q[:, mask] > mid[mask]).astype(np.int8)
cross = np.abs(np.diff(s, axis=0)).sum(0) / (n / FPS)
print("pixels that ever change by more than 2.5 levels: %.1f%%; their crossings of their own halfway level per second: mean %.3f, 99th percentile %.3f, max %.3f" % (100 * mask.mean(), cross.mean(), np.percentile(cross, 99), cross.max()))
