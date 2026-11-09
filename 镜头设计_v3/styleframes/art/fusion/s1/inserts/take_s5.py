# -*- coding: utf-8 -*-
"""HKBU SCIE1007 课程作业的科普视频。把 s5 的镜头帧合成一条片子，并逐帧看有没有跳。

s410 是 1500 帧（25 秒，60 帧），s504 是 1440 帧；审片版每两帧取一帧（30 帧，也可以直接按步长 2 渲），4K 版每帧都要。
用法：python take_s5.py <帧目录> <输出.mp4> s410 [30|60]
"""
import glob
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image

FF = os.environ.get("FF") or "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SRC, OUT = sys.argv[1], sys.argv[2]
SHOT = sys.argv[3] if len(sys.argv) > 3 else "s410"
RATE = sys.argv[4] if len(sys.argv) > 4 else "30"
COUNT = {"s410": 1500, "s504": 1440}[SHOT]
files = sorted(glob.glob(SRC + "/%s_*.png" % SHOT) + glob.glob(SRC + "/%s_*.jpg" % SHOT))
if RATE != "60" and len(files) == COUNT // 2:
    pass                                     # 审片版按步长 2 渲的（0, 2, 4, ...），本来就是 30 帧
else:
    assert len(files) == COUNT, (len(files), COUNT)
    if RATE != "60":
        files = files[::2]                   # 审片版 30 帧：每两帧取一帧

p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", RATE, "-i", "-",
                      "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT],
                     stdin=subprocess.PIPE)
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
print("mean frame-to-frame change %.2f; biggest: %s" % (np.mean([j[0] for j in jumps]), ", ".join("%s %.1f" % (f, d) for d, f in jumps[:8])))
print("TAKE_OK", len(files))
