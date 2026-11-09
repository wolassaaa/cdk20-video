# HKBU SCIE1007 coursework science video. Review film: the W5 end card laid over the new background layer, multiply, at 1080p.
# The Remotion ffmpeg has no blend filter and no rawvideo, so ffmpeg only turns the two films into 1080p PNG frames (in _tmp/, inside the project because this ffmpeg only writes there) and back, and the multiply is done in numpy: out = end card x layer / bone, per colour channel (bone = #EDEBE4),
# so the bone paper stays exactly bone, and the type (dark) stays dark wherever it sits on a dot or line.
# Run: python overlay_w5.py   ->  W5_with_bg_1080p_v1.mp4 (and W5_with_bg_check_<t>.png: three frames at 4 s, 14 s, 31 s)
import io, os, shutil, subprocess
import numpy as np
from PIL import Image

ROOT = "D:/。hkbu/molecular science/"
FF = ROOT + "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
OUT = ROOT + "镜头设计_v3/td/w5/"
W5 = ROOT + "镜头设计_v3/styleframes/art/fusion/end/W5_end_4k60_1.mp4"
BG = OUT + "W5_bg_4k60_v1.mp4"
W, H = 1920, 1080
TMP = OUT + "_tmp/"
BONE = np.array([237, 235, 228], np.float32)
VF = "scale=%d:%d:flags=lanczos:in_range=tv:in_color_matrix=bt709,format=rgb24" % (W, H)


def frames(path, tag):
    subprocess.run([FF, "-y", "-v", "error", "-i", path, "-vf", VF, TMP + tag + "_%04d.png"], check=True)


os.makedirs(TMP, exist_ok=True)
frames(W5, "a")
frames(BG, "b")
enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "image2pipe", "-framerate", "60", "-c:v", "png", "-i", "-", "-an",
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT + "W5_with_bg_1080p_v1.mp4"], stdin=subprocess.PIPE)
n = 0
saved = {4 * 60, 14 * 60, 31 * 60}
while os.path.exists(TMP + "a_%04d.png" % (n + 1)) and os.path.exists(TMP + "b_%04d.png" % (n + 1)):
    A = np.array(Image.open(TMP + "a_%04d.png" % (n + 1)).convert("RGB"), np.float32)
    B = np.array(Image.open(TMP + "b_%04d.png" % (n + 1)).convert("RGB"), np.float32)
    C = Image.fromarray(np.clip(A * B / BONE + 0.5, 0, 255).astype(np.uint8))
    bio = io.BytesIO()
    C.save(bio, "PNG", compress_level=1)
    enc.stdin.write(bio.getvalue())
    if n in saved:
        C.save(OUT + "W5_with_bg_check_%02ds.png" % (n // 60))
    n += 1
enc.stdin.close()
enc.wait()
print("frames", n)
