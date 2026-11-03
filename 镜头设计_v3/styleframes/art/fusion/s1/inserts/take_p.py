"""HKBU SCIE1007 coursework science video. Joins the frames for S3's second piece into two takes: the held full view of the lock and key shot from 310 s, and shot p from 312.0 s, where the first lock turns into the CDK20 model. Both run frame for frame on the film's clock. k is 1 for 1080p, 2 for 4K. Run: python take_p.py <lock.mp4> <cdk20.mp4> [k]"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
A, B = sys.argv[1:3]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LAST_P, END_P = 912, 1080                # the model stands still after frame 912
MIX = (156, 175)                         # the grown shape is a little fuller than the model, so the last 19 frames of growth dissolve into the model (render_pm.sh)


def take(out, files):
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "60", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-vf", "scale=%d:%d:flags=lanczos:out_color_matrix=bt709:out_range=tv" % (1920 * K, 1080 * K), "-threads", "4", out], stdin=subprocess.PIPE)
    for f in files:
        p.stdin.write(open(f, "rb").read())
    p.stdin.close()
    if p.wait():
        raise SystemExit("TAKE_FAILED")
    print("frames", len(files))


def frame(n):
    n = min(n, LAST_P)
    if not MIX[0] <= n < MIX[1]:
        return "%s/frames/p/p_%04d.png" % (HERE, n)
    out = "%s/frames/p_mix/p_%04d.png" % (HERE, n)
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        a, b = [np.asarray(Image.open("%s/frames/%s/p_%04d.png" % (HERE, d, n)).convert("RGB"), np.float32) for d in ("p", "p_model")]
        w = (n - MIX[0] + 1) / (MIX[1] - MIX[0] + 1)
        w = w * w * (3 - 2 * w)
        Image.fromarray(np.uint8(np.clip(a + (b - a) * w + 0.5, 0, 255))).save(out)
    return out


# frame 1426 is the held full view; shot p's first frame is the same view at 312.0 s
take(A, ["%s/frames/k/k_1426.png" % HERE] * 120)
take(B, ["%s/frames/p/p_0000.png" % HERE] * 120 + [frame(n) for n in range(END_P + 30)])    # the same clock as the other take
print("TAKE_OK")
