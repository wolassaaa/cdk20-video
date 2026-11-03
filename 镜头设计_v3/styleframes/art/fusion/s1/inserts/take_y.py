"""HKBU SCIE1007 coursework science video. Joins the W2 motion test (S4 upgrade idea 1, shot y, 412-437 s) into one 1080p clip. S3 ends with the table under a dark veil; here the light comes back from the empty cell outwards in 3.4 s, no flash. Run: python take_y.py <out.mp4>"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
N, FPS = 1501, 60
VEIL = np.array((5, 5, 6), np.float32)       # the dark S3 ends under, #050506 at 90 %
CELL = (1316, 540)                            # the empty cell on screen in the first frame


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


yy, xx = np.mgrid[0:1080, 0:1920]
reach = np.hypot(xx - CELL[0], yy - CELL[1]) / 1400.0      # 0 at the cell, about 1 at the far corner
p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", sys.argv[1]], stdin=subprocess.PIPE)
for f in range(N):
    im = np.asarray(Image.open("%s/frames/y/y_%04d.png" % (HERE, f)).convert("RGB"), np.float32)
    t = f / FPS
    if t < 3.4:
        a = 0.9 * (1 - smooth((t - 0.4 - 1.4 * reach) / 1.6))[:, :, None]
        im = im + (VEIL - im) * a
    p.stdin.write(np.clip(im + 0.5, 0, 255).astype(np.uint8).tobytes())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("TAKE_OK", N)
