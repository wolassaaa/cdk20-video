"""HKBU SCIE1007 coursework science video. Joins the tail-cut motion test (S4 upgrade ideas 2 and 3, shot z, 437-449 s) into one 1080p clip. Frame 0 of shot z is the last frame of shot y, so the clip starts at frame 1 and plays straight on from W2_beads_test_2.mp4. Run: python take_z.py <out.mp4>"""
import io
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
N, FPS = 721, 60

# this ffmpeg has no raw video input, so frames go in as PNG; same settings as take_y.py, so the two clips join without re-encoding
p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", sys.argv[1]], stdin=subprocess.PIPE)
for f in range(1, N):
    buf = io.BytesIO()
    Image.open("%s/frames/z/z_%04d.png" % (HERE, f)).convert("RGB").save(buf, "PNG", compress_level=1)
    p.stdin.write(buf.getvalue())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("TAKE_OK", N - 1)
