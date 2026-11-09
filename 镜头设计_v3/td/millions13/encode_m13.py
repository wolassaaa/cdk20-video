# HKBU SCIE1007 coursework science video. millions -> 13 sample: frames to millions13_1080p_v1.mp4 (1920x1080, 30 fps, no audio) and four key frames in millions13_stills.jpg (2 x 2).
# Run: python encode_m13.py    frames: C:/render_tmp/td_m13/f/m13_0000.png ... m13_0239.png (from build_m13.py)
import subprocess
from PIL import Image

ROOT = "D:/。hkbu/molecular science/"
FF = ROOT + "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
OUT = ROOT + "镜头设计_v3/td/millions13/"
F = "C:/render_tmp/td_m13/f/m13_%04d.png"
subprocess.run([FF, "-y", "-v", "error", "-framerate", "30", "-i", F, "-an", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "12",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", OUT + "millions13_1080p_v1.mp4"], check=True)
KEYS = [20, 66, 138, 239]
sheet = Image.new("RGB", (3840, 2160))
for i, n in enumerate(KEYS):
    sheet.paste(Image.open(F % n).convert("RGB"), ((i % 2) * 1920, (i // 2) * 1080))
sheet.save(OUT + "millions13_stills.jpg", quality=93)
print("key frames", KEYS)
