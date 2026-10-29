"""Downscale frames/ to 960x540, encode preview mp4 with the Remotion ffmpeg, build contact sheet."""
import os, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FR = os.path.join(ROOT, "frames")
FF = r"D:\。hkbu\molecular science\镜头设计_v2\tests\T4_remotion\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe"

tmp = tempfile.mkdtemp()
files = sorted(f for f in os.listdir(FR) if f.endswith(".png"))
for f in files:
    Image.open(os.path.join(FR, f)).resize((960, 540), Image.LANCZOS).save(os.path.join(tmp, f))
out = os.path.join(ROOT, "handprints_preview_960.mp4")
subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "30", "-i", os.path.join(tmp, "%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
shutil.rmtree(tmp)

keys = [2, 6, 26, 50, 70, 98, 104, 120, 140, 160, 190, 235]
tw, th = 640, 360
sheet = Image.new("RGB", (tw * 3, th * 4), (0, 0, 0))
fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
for i, k in enumerate(keys):
    im = Image.open(os.path.join(FR, f"{k:04d}.png")).resize((tw, th), Image.LANCZOS)
    ImageDraw.Draw(im).text((10, 8), f"f{k:03d}", font=fnt, fill=(41, 240, 255))
    sheet.paste(im, ((i % 3) * tw, (i // 3) * th))
sheet.save(os.path.join(ROOT, "handprints_contact.jpg"), quality=85)
print("ok", out, os.path.getsize(os.path.join(ROOT, "handprints_contact.jpg")))
