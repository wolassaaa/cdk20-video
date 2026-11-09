"""HKBU SCIE1007 课程作业的科普视频。bl_s5b.py 只渲会变的帧（60 帧/秒的帧号）；这里按 30 帧/秒铺满整段，没渲的帧用它前面最近的一张（台面那时不动），
压成 1920x1080 的底片给 s5b.jsx 读。顺带报每帧和前一帧的平均差（0-255），看有没有跳。
用法：python take_s5b.py <帧目录> <镜头名 s501|s507|s510> <60 帧/秒的总帧数> <输出.mp4>
"""
import glob
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image

src, shot, total, dst = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
have = {int(os.path.basename(f)[len(shot) + 1:-4]): f for f in glob.glob(os.path.join(src, shot + "_*.png"))}
if 0 not in have:
    sys.exit("no frame 0")
FF = os.environ.get("FF", "C:/Program Files/digiKam/ffmpeg.exe")
p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                      "-pix_fmt", "yuv420p", "-an", dst], stdin=subprocess.PIPE)
keys = sorted(have)
last, prev, jumps = None, None, []
for k in range(total // 2):
    f = max(x for x in keys if x <= 2 * k)
    if f != last:
        data = open(have[f], "rb").read()
        a = np.asarray(Image.open(io.BytesIO(data)).convert("RGB").resize((480, 270)), np.float32)
        if prev is not None:
            jumps.append((float(np.abs(a - prev).mean()), k))
        prev, last = a, f
    p.stdin.write(data)
p.stdin.close()
p.wait()
jumps.sort(reverse=True)
print("TAKE_OK" if p.returncode == 0 else "TAKE_FAILED", shot, total // 2, "frames from", len(keys), "renders; biggest steps", [(round(j, 2), k) for j, k in jumps[:4]])
