"""HKBU SCIE1007 coursework science video. Hands: join the rendered parts of the motion test and measure it. python motion_join.py <parts> [preview]"""
import subprocess
import sys

from hk import *

FF = str(ROOT.parent / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe")
parts = int(sys.argv[1])
prev = len(sys.argv) > 2
tag = "p" if prev else "f"
lst = RAW / f"parts_{tag}.txt"
lst.write_text("".join(f"file 'part{tag}_{i}.mp4'\n" for i in range(parts)), encoding="utf8")
out = RAW / "motion_preview.mp4" if prev else STILL / "motion.mp4"
subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
lum = np.concatenate([np.load(RAW / f"lum{tag}_{i}.npy") for i in range(parts)])
fps = 10 if prev else 30
step = np.diff(lum)
d = np.abs(step)
# whole-screen changes faster than twice a second: count reversals of direction in the mean luminance, ignoring moves too small to see
big = step[d > 0.0015]
rev = np.flatnonzero(big[1:] * big[:-1] < 0)
win = int(fps)
worst = 0
if len(rev):
    idx = np.flatnonzero(d > 0.0015)[rev]
    worst = max(int(((idx >= i) & (idx < i + win)).sum()) for i in idx)
rep = (f"frames {len(lum)} at {fps} fps, {len(lum) / fps:.1f} s\nfile {out.stat().st_size / 1e6:.1f} MB, {out.stat().st_size * 8 / 1e6 / (len(lum) / fps):.2f} Mbit/s\n"
       f"mean luminance (0 to 1): min {lum.min():.4f}, max {lum.max():.4f}\nlargest change between neighbouring frames {d.max():.5f}, that is {d.max() * 255:.2f} of 255\nmean change {d.mean():.5f}\n"
       f"reversals of direction above 0.0015: {len(rev)}, most in any one second: {worst}\n")
print(rep)
(RAW / f"motion_metrics_{tag}.txt").write_text(rep, encoding="utf8")
