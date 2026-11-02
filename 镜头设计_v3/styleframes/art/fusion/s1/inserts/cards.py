"""HKBU SCIE1007 coursework science video. S2 table shot: cuts the six source cards and the main paper out of the 4K film, so the 3D sheets carry the film's own type. Run: python cards.py"""
import os
import subprocess

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
ROOT = "D:/。hkbu/molecular science/"
FF = ROOT + "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
FILM = HERE + "/../../s2/S2_fusion_4k_v1.mp4"
OUT = HERE + "/frames/cards/"
os.makedirs(OUT, exist_ok=True)
subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "95", "-i", FILM, "-frames:v", "1", "-update", "1", OUT + "film.png"], check=True)
im = Image.open(OUT + "film.png").convert("RGB")
for i in range(6):
    x, y = 19960 + i % 2 * 540 - 19200, 1280 + i // 2 * 186 - 1080
    im.crop((x * 2, y * 2, (x + 520) * 2, (y + 170) * 2)).save(OUT + "card_%d.png" % i)
im.crop((192, 220, 1392, 1920)).save(OUT + "paper.png")
os.remove(OUT + "film.png")
print("CARDS_OK")
