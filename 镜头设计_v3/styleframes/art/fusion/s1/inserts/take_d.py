"""HKBU SCIE1007 coursework science video. Joins the motion test of the W2 opening with the tail shaken off (shot d: shot e's liquid settles into the real CDK20, the tail melts back into red liquid, the body shakes like a wet dog and flings it into the next cell, where it splats and draws into a line; the body floats down) into one clip at 30 fps, from every second frame. Each frame is checked against the one before it, and the biggest jumps are printed, so a pop shows up without watching. Run: python take_d.py <frame dir> <out.mp4> [fps]"""
import glob
import io
import subprocess
import sys

import numpy as np
from PIL import Image

FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SRC, OUT = sys.argv[1], sys.argv[2]
RATE = sys.argv[3] if len(sys.argv) > 3 else "30"          # 60 for the 4K pass, from every frame
files = sorted(glob.glob(SRC + "/d_*.png"))
assert len(files) in (550, 759, 1517), len(files)          # 550 for versions 1-2 (18.3 s), 759 for version 3 (25.3 s, all of W2), 1517 for the 4K pass at 60 fps

p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", RATE, "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT], stdin=subprocess.PIPE)
jumps, last = [], None
for f in files:
    im = Image.open(f).convert("RGB")
    a = np.asarray(im.resize((480, 270)), np.float32)
    if last is not None:
        jumps.append((float(np.abs(a - last).mean()), f[-8:-4]))
    last = a
    buf = io.BytesIO()
    im.save(buf, "PNG", compress_level=1)
    p.stdin.write(buf.getvalue())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
jumps.sort(reverse=True)
print("mean frame-to-frame change %.2f; biggest:" % np.mean([j[0] for j in jumps]), ", ".join("%s %.1f" % (f, d) for d, f in jumps[:8]))
print("TAKE_OK", len(files))
