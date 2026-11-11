# -*- coding: utf-8 -*-
"""HKBU SCIE1007 课程作业的科普视频。把 4-10 新锁版（s410k）隔一帧渲的 750 张帧压成 30 帧的底片（显卡编码），并逐帧看有没有跳。
用法：python take_s410k.py <帧目录> <输出.mp4>
"""
import glob
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image

FF = os.environ.get("FF") or "C:/Program Files/digiKam/ffmpeg.exe"
SRC, OUT = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(SRC + "/s410k_*.jpg") + glob.glob(SRC + "/s410k_*.png"))
assert len(files) == 750, len(files)
p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "30", "-i", "-",
                      "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "constqp", "-qp", "12", "-pix_fmt", "yuv420p",
                      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT], stdin=subprocess.PIPE)
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
d = np.array([j[0] for j in jumps])
print("mean frame-to-frame change %.2f; first second max %.2f, last second max %.2f; biggest: %s" % (d.mean(), d[:30].max(), d[-30:].max(), ", ".join("%s %.1f" % (f, v) for v, f in sorted(jumps, reverse=True)[:8])))
print("TAKE_OK", len(files))
