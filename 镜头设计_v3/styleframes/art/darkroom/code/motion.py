"""HKBU SCIE1007 coursework science video. Motion test of the darkroom direction: T4 developing in the tray.

Three plates from t4.py at 125%: m_a (the form with no lines), m_b (final), m_c (real per-vertex pLDDT as a screen pass). The lines come up in linear light, high-confidence parts first, under a slow push-in. The dither is one fixed pattern and the dye does not move, so nothing flickers.
Run from code/: python motion.py [--frames dir]
"""
import os, subprocess, sys
import numpy as np
from PIL import Image
from grade import *

FPS, SEC, HOLD = 30, 7.0, 1.0
N = int(FPS * SEC)
W, H = 1920, 1080
FF = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"


def ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


load = lambda n: np.load(os.path.join(WORK, n + ".npy")).astype(np.float32)
A, B, C = load("m_a"), load("m_b"), load("m_c")
ph, pw = B.shape[:2]
cov = np.clip(C[..., 1], 0, 1)
conf = C[..., 0] / np.maximum(C[..., 1], 1e-3)
sure = ss((conf - 0.5) / 0.4)
x = np.linspace(0, 1, pw, dtype=np.float32)[None, :]
d = (0.03 + 0.08 * x) * (1 - cov) + (0.14 + 0.52 * (1 - sure) + 0.08 * x) * cov
d = gauss(d[..., None].astype(np.float64), 4)[..., 0].astype(np.float32)
D = A * 0.20


def zoom(a, z):
    bw, bh = pw / z, ph / z
    l, t = (pw - bw) * 0.22, (ph - bh) * 0.62
    box = (l, t, l + bw, t + bh)
    return np.stack([np.asarray(Image.fromarray(a[..., c], "F").resize((W, H), Image.BICUBIC, box=box)) for c in range(3)], -1)


def frame(f):
    t = min(f / (FPS * (SEC - HOLD)), 1.0)
    r = ss((t - d) / 0.30)[..., None]
    p = f / (N - 1)
    z = 1.0 + 0.045 * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    a = zoom(D * (1 - r) + B * r, z)
    return finish(a.astype(np.float64), 1.12, (0.45, 0.65, 1.0), 0.50, 0.40)


out = os.path.join(STILLS, "motion.mp4")
fd = os.path.join(WORK, "m_frames")
os.makedirs(fd, exist_ok=True)
for f in range(N):
    b = (frame(f) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(b).save(os.path.join(fd, f"{f:04d}.png"), compress_level=1)
r = subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fd, "%04d.png"),
                    "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out])
print("motion ok", N, r.returncode)
