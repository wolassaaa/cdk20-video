"""HKBU SCIE1007 coursework science video. Lantern: encode the frames into motion.mp4 and measure it. Adjacent-frame brightness, how often the whole picture changes, size, bitrate, and how the cold-ray stretch holds at the film's average bitrate."""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

L = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/lantern")
FR = L / "_work/f"
FF = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
OUT = L / "stills/motion.mp4"
N = len(list(FR.glob("*.png")))
print("frames", N)
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "30", "-i", str(FR / "%04d.png"), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(OUT)], check=True)
mb = OUT.stat().st_size / 1e6
print(f"motion.mp4 {mb:.1f} MB, {mb * 8 / (N / 30):.1f} Mbps at crf 17")
t = L / "_work/m75.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "30", "-i", str(FR / "%04d.png"), "-c:v", "libx264", "-preset", "slow", "-b:v", "7500k", "-maxrate", "12000k", "-bufsize", "15000k", "-pix_fmt", "yuv420p", "-an", str(t)], check=True)
print(f"7.5 Mbps version {t.stat().st_size / 1e6:.1f} MB")
dec = L / "_work/dec"
dec.mkdir(exist_ok=True)
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(t), str(dec / "%04d.png")], check=True)

mean, diffs, big = [], [], []
prev = None
for i in range(N):
    a = np.asarray(Image.open(FR / f"{i:04d}.png").convert("L").resize((480, 270), Image.BOX), np.float32)
    mean.append(a.mean())
    if prev is not None:
        d = np.abs(a - prev)
        diffs.append(d.mean())
        big.append((d > 25).mean())
    prev = a
mean = np.array(mean)
step = np.abs(np.diff(mean))
big = np.array(big)
print(f"mean luma step per frame: max {step.max():.2f} of 255 at frame {step.argmax()}, mean {step.mean():.3f}")
print(f"adjacent-frame abs diff: max {max(diffs):.2f} at frame {int(np.argmax(diffs))}, mean {np.mean(diffs):.2f}")
print(f"frames where over 25% of the picture jumps: {int((big > 0.25).sum())}, over 10%: {int((big > 0.10).sum())}")
# brightness reversals faster than 2 per second: count up/down swings over 3 of 255
sign, swings, last = 0, [], mean[0]
for i, m in enumerate(mean):
    if m - last > 3 and sign <= 0:
        sign, last = 1, m
        swings.append(i)
    elif last - m > 3 and sign >= 0:
        sign, last = -1, m
        swings.append(i)
    else:
        last = max(last, m) if sign > 0 else min(last, m) if sign < 0 else last
print("brightness swings over 3/255 at frames", swings)

for name, a0, b0 in (("T3 search", 0, 105), ("T4 rays", 135, 225), ("push", 225, 330), ("key", 330, 415), ("hold", 460, 540)):
    ps = []
    for i in range(a0, b0, 9):
        s = np.asarray(Image.open(FR / f"{i:04d}.png").convert("L"), np.float32)
        e = np.asarray(Image.open(dec / f"{i + 1:04d}.png").convert("L"), np.float32)
        ps.append(10 * np.log10(255 ** 2 / max(np.mean((s - e) ** 2), 1e-3)))
    print(f"PSNR at 7.5 Mbps, {name}: {np.mean(ps):.1f} dB")
