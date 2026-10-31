"""HKBU SCIE1007 coursework science video. Arena direction: last step of the motion test, run after motion.py. python motion_even.py <ffmpeg path>

The in-between frames are averages, so they come out slightly softer than the rendered plates, and that difference would pulse at 15 Hz. Here every plate gets the same 1-2-1 blend with its neighbours, which brings the two kinds of frame level. The clip then holds its last frame for three frames, to pass 5 s. Prints the pulse before and after, and writes stills/motion.mp4.
"""
import glob, os, subprocess, sys
import numpy as np
from PIL import Image
import grade as g

src = os.path.join(g.WORK, "motion", "png")
dst = os.path.join(g.WORK, "motion", "png2")
os.makedirs(dst, exist_ok=True)
for f in glob.glob(os.path.join(dst, "*.png")):
    os.remove(f)
fs = sorted(glob.glob(os.path.join(src, "*.png")))


def load(i):
    return np.asarray(Image.open(fs[i]).convert("RGB"), np.float32)


def detail(a):
    return float(np.abs(np.diff(a[300:800, 450:1500].mean(2), axis=1)).mean())


def pulse(v):
    v = np.array(v)
    e, o = v[0::2], v[1::2]
    n = min(len(o), len(e) - 1)
    return 100 * np.abs(o[:n] - (e[:n] + e[1:n + 1]) / 2).mean() / e.mean()


before, after = [], []
prev, cur = None, load(0)
for i in range(len(fs)):
    nxt = load(i + 1) if i + 1 < len(fs) else None
    out = cur
    if i % 2 == 0 and prev is not None and nxt is not None:
        out = 0.25 * prev + 0.5 * cur + 0.25 * nxt
    if 10 <= i < len(fs) - 10:
        before.append(detail(cur))
        after.append(detail(out))
    Image.fromarray((out + 0.5).astype(np.uint8)).save(os.path.join(dst, f"{i:04d}.png"), compress_level=1)
    prev, cur = cur, nxt
last = os.path.join(dst, f"{len(fs) - 1:04d}.png")
im = Image.open(last)
for k in range(3):
    im.save(os.path.join(dst, f"{len(fs) + k:04d}.png"), compress_level=1)
print("detail pulse before %.2f%%, after %.2f%%" % (pulse(before), pulse(after)))
subprocess.run([sys.argv[1], "-y", "-framerate", "30", "-i", os.path.join(dst, "%04d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(g.STILLS, "motion.mp4")], check=True, capture_output=True)
print("wrote motion.mp4")
