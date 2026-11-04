"""HKBU SCIE1007 coursework science video. Joins the 4-01 test (shot i: from W2's last frame, the red coil and then the body turn into a chain of blocks, a light runs along it as the sequence stands up on the table, and each block takes its AlphaFold confidence colour) into one clip at 30 fps, from every second frame. Each frame is checked against the one before it, and the biggest jumps are printed. Shots i2 (4-02) and i3 (4-03) go through the same: python take_i.py <frame dir> <out.mp4> i2. Run: python take_i.py <frame dir> <out.mp4> [shot]"""
import glob
import io
import subprocess
import sys

import numpy as np
from PIL import Image

FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SRC, OUT = sys.argv[1], sys.argv[2]
SHOT = sys.argv[3] if len(sys.argv) > 3 else "i"
files = sorted(glob.glob(SRC + "/%s_*.png" % SHOT))
assert len(files) == dict(i=780, i2=510, i3=540, i4=105)[SHOT], len(files)          # 4-01 26 s, 4-02 17 s, 4-03 18 s, back after 4-05 3.5 s

p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT], stdin=subprocess.PIPE)
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
