"""HKBU SCIE1007 coursework science video, dawn art direction. Motion test: the T3 to T4 reveal, 7 s at 1080p30. The dark mass that hid the stars takes the first blue light. Colour only: same plates, no new render.
python motion.py <ffmpeg> <out.mp4>
"""
import io, subprocess, sys
import numpy as np
from PIL import Image
from comp_lib import sm

ff, out = sys.argv[1], sys.argv[2]
FPS, N = 30, 210
a = np.asarray(Image.open("../_work/plates/T3.png").convert("RGB"), np.float32) / 255
b = np.asarray(Image.open("../_work/plates/T4.png").convert("RGB"), np.float32) / 255
la, lb = a ** 2.2, b ** 2.2
hy = 720
h, w = a.shape[:2]
# the light arrives from the right and low: every pixel has its own moment, so it sweeps across instead of cross-fading
y, x = np.mgrid[0:h, 0:w].astype(np.float32)
lead = np.clip((1920 - x) / 1920 * .55 + np.abs(y - hy) / 720 * .25, 0, 1)
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "bmp", "-framerate", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
KEEP = [20, 90, 130, 170]
sheet = Image.new("RGB", (1284, 724), (60, 60, 60))
for i in range(N):
    t = i / (N - 1)
    u = np.clip(sm(.14, .92, t) * 1.8 - lead, 0, 1)      # hold on the dark, then the sweep
    u = (u * u * (3 - 2 * u))[..., None]
    img = la * (1 - u) + lb * u
    fr = (np.clip(img, 0, 1) ** (1 / 2.2) * 255 + .5).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(fr).save(buf, "BMP"); p.stdin.write(buf.getvalue())
    if i in KEEP:
        sheet.paste(Image.fromarray(fr).resize((640, 360)), (KEEP.index(i) % 2 * 644, KEEP.index(i) // 2 * 364))
p.stdin.close(); p.wait()
sheet.save("../_work/t1test/motion_sheet.png")
print("frames", N, p.returncode)
