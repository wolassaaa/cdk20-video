"""HKBU SCIE1007 coursework science video. Arena direction: motion test, T4, 1080p30, from the 15 fps plates in _work/motion.

The lighting cue is done here on the desk, not in Blender: the key fader rises slowly over two seconds, so no frame has to be re-rendered to change the cue. In-between frames are plain averages of
neighbouring plates in linear light; the motion is slow enough that this cannot be seen. Writes stills/motion.mp4 and prints how much the picture moves frame to frame, to check it does not flicker.
"""
import glob, os, subprocess, sys
import numpy as np
from PIL import Image
import grade as g

mdir = os.path.join(g.WORK, "motion")
frames = sorted(glob.glob(os.path.join(mdir, "f*.npy")))
tmp = os.path.join(mdir, "png")
os.makedirs(tmp, exist_ok=True)
for f in glob.glob(os.path.join(tmp, "*.png")):
    os.remove(f)
a, b, c, ex, bl = g.DESK["T4"]
overlay = g.WORK + "/text/T4over.png"
lab = np.asarray(Image.open(overlay).convert("RGBA"), np.float32) / 255
n = 2 * len(frames) - 1
step, prev = [], None


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


for i in range(n):
    t = i / 30.0
    j = i // 2
    d = np.load(frames[j]).astype(np.float32)
    if i % 2:
        d = 0.5 * (d + np.load(frames[j + 1]).astype(np.float32))
    key = 0.02 + 0.98 * ease((t - 1.0) / 2.2)
    room = 0.55 + 0.45 * ease((t - 0.2) / 2.8)
    img = g.desk(d, (a[0], a[1] * key), (b[0], b[1] * room), (c[0], c[1] * room))
    out = g.film(g.bloom(img, bl), ex)
    al = lab[..., 3:] * ease((t - 3.2) / 0.8)
    show = out * (1 - al) + lab[..., :3] * al
    Image.fromarray((np.clip(show, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(tmp, f"{i:04d}.png"), compress_level=1)
    if prev is not None:
        step.append(float(np.abs(out - prev).mean()))
    prev = out
s = np.array(step)
print("frames", n, "mean step %.5f, max step %.5f, largest jump between neighbouring steps %.5f" % (s.mean(), s.max(), np.abs(np.diff(s)).max()))
ff = sys.argv[1]
subprocess.run([ff, "-y", "-framerate", "30", "-i", os.path.join(tmp, "%04d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(g.STILLS, "motion.mp4")], check=True, capture_output=True)
print("wrote motion.mp4")
