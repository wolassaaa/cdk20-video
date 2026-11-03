"""HKBU SCIE1007 coursework science video. Joins the frames of shot q and the holds between them into one take that runs frame for frame from 330 s. k is 1 for 1080p, 2 for 4K. Run: python take_q.py <out.mp4> [k]"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
OUT = sys.argv[1]
K = int(sys.argv[2]) if len(sys.argv) > 2 else 1
MOVES = [(0, 180), (192, 552), (1224, 1314), (1716, 1836), (1980, 2400), (2976, 3036), (3156, 3276), (3594, 3594), (3600, 3600), (4080, 4260)]
END = 4920
have = sorted(n for a, b in MOVES for n in range(a, b + 1))

p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "60", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-vf", "scale=%d:%d:flags=lanczos:out_color_matrix=bt709:out_range=tv" % (1920 * K, 1080 * K), "-threads", "4", OUT], stdin=subprocess.PIPE)
i, last, data = 0, None, None
for f in range(END):
    while i + 1 < len(have) and have[i + 1] <= f:
        i += 1
    if have[i] != last:
        last, data = have[i], open("%s/frames/q/q_%04d.png" % (HERE, have[i]), "rb").read()
    p.stdin.write(data)
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("frames", END)
print("TAKE_OK")
