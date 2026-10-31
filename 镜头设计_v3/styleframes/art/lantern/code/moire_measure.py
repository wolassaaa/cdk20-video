"""HKBU SCIE1007 coursework science video. Lantern moire measure: encode each stripe period at the film's average bitrate, then count what survives.
Reads _work/moire/p*/. Prints bitrate and PSNR at 7.5 Mbps, frame-to-frame flicker, and how much false low-frequency pattern appears when a viewer watches at 480p. Writes a side-by-side crop."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

W_ = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/lantern/_work/moire")
FF = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
N = 45
rows = []
sheet = []
for p in ("10.5", "16", "24"):
    d = W_ / f"p{p}"
    mp4 = W_ / f"p{p}.mp4"
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "30", "-i", str(d / "%04d.png"), "-c:v", "libx264", "-preset", "medium", "-b:v", "7500k", "-maxrate", "9000k", "-bufsize", "9000k", "-pix_fmt", "yuv420p", str(mp4)], check=True)
    dec = W_ / f"dec{p}"
    dec.mkdir(exist_ok=True)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4), str(dec / "%04d.png")], check=True)
    src = [np.asarray(Image.open(d / f"{i:04d}.png").convert("L"), np.float32) for i in range(0, N, 4)]
    enc = [np.asarray(Image.open(dec / f"{i + 1:04d}.png").convert("L"), np.float32) for i in range(0, N, 4)]
    psnr = np.mean([10 * np.log10(255 ** 2 / np.mean((a - b) ** 2)) for a, b in zip(src, enc)])
    mean = [a.mean() for a in src]
    flick = np.abs(np.diff(mean)).max()
    # a viewer at 480p: plain bilinear, what a phone player does. False pattern = what it has beyond a clean area average
    lo, ideal = [], []
    for a in enc:
        im = Image.fromarray(a.astype(np.uint8))
        lo.append(np.asarray(im.resize((854, 480), Image.BILINEAR), np.float32))
        ideal.append(np.asarray(im.resize((854, 480), Image.BOX), np.float32))
    # keep only slow bands, moire shows up as broad light and dark patches
    def low(x):
        return np.asarray(Image.fromarray(x).resize((85, 48), Image.BOX), np.float32)
    moire = np.mean([np.abs(low(a) - low(b)).max() for a, b in zip(lo, ideal)])
    tmp = np.mean([np.abs(lo[i + 1] - lo[i]).mean() for i in range(len(lo) - 1)])
    kb = mp4.stat().st_size * 8 / 1000 / (N / 30)
    rows.append((p, round(kb), round(float(psnr), 1), round(float(flick), 2), round(float(moire), 2), round(float(tmp), 2)))
    sheet.append(Image.fromarray(lo[len(lo) // 2].astype(np.uint8)).crop((300, 40, 640, 340)).resize((340, 300)))
    sheet.append(Image.fromarray(enc[len(enc) // 2].astype(np.uint8)).crop((800, 200, 1140, 500)))
print("period  kbps  psnr  mean_step  lowband_err  480p_temporal")
for r in rows:
    print(r)
o = Image.new("L", (340 * 6, 300))
for i, s in enumerate(sheet):
    o.paste(s, (i * 340, 0))
o.save(W_ / "compare.png")
