"""HKBU SCIE1007 coursework science video. Joins the frames for S3's second piece into two takes: the end of the lock and key shot from 310 s, and the CDK20 shot from 313.2 s. Both run frame for frame on the film's clock. k is 1 for 1080p, 2 for 4K. Run: python take_p.py <lock.mp4> <cdk20.mp4> [k]"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
A, B = sys.argv[1:3]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LAST_P, END_P = 840, 1008                # the model stands still after frame 840


def take(out, files):
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "60", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-vf", "scale=%d:%d:flags=lanczos:out_color_matrix=bt709:out_range=tv" % (1920 * K, 1080 * K), "-threads", "4", out], stdin=subprocess.PIPE)
    for f in files:
        p.stdin.write(open(f, "rb").read())
    p.stdin.close()
    if p.wait():
        raise SystemExit("TAKE_FAILED")
    print("frames", len(files))


# frame 1426 is the held full view; 1572 on is the dive
take(A, ["%s/frames/k/k_1426.png" % HERE] * 120 + ["%s/frames/k/k_%04d.png" % (HERE, min(n, 1643)) for n in range(1572, 1645)])
take(B, ["%s/frames/p/p_0000.png" % HERE] * 192 + ["%s/frames/p/p_%04d.png" % (HERE, min(n, LAST_P)) for n in range(END_P)])    # the same clock as the other take
print("TAKE_OK")
