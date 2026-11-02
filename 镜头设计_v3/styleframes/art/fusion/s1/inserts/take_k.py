"""HKBU SCIE1007 coursework science video. Joins the S3 lock and key frames and the holds between them into one take that runs frame for frame from 283 s, the start of S3. k is 1 for 1080p, 2 for 4K. Run: python take_k.py <out.mp4> [k]"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
OUT = sys.argv[1]
K = int(sys.argv[2]) if len(sys.argv) > 2 else 1
LEAD = 168                               # 283.0 to 285.8 s: the empty table
MOVES = [(0, 780), (1124, 1426)]         # the rendered frames, first and last of each move
END = 1572

seq = [0] * LEAD
for i, (a, b) in enumerate(MOVES):
    seq += list(range(a, b + 1))
    seq += [b] * ((MOVES[i + 1][0] if i + 1 < len(MOVES) else END) - b - 1)
print("frames", len(seq))
p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "60", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-vf", "scale=%d:%d:flags=lanczos:out_color_matrix=bt709:out_range=tv" % (1920 * K, 1080 * K), "-threads", "4", OUT], stdin=subprocess.PIPE)
for n in seq:
    p.stdin.write(open("%s/frames/k/k_%04d.png" % (HERE, n), "rb").read())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("TAKE_OK")
