"""HKBU SCIE1007 课程作业的科普视频：数粗剪某区域里深色（字）像素随时间的变化，用来定文字出现的时刻。
用法：python ink.py 起秒 长秒 x0 y0 x1 y1（按 480×270 坐标）[阈值]"""
import subprocess, sys, numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parents[2]
a, n, x0, y0, x1, y1 = map(float, sys.argv[1:7]); th = float(sys.argv[7]) if len(sys.argv) > 7 else 120
p = subprocess.run([str(ROOT / "_env/ffmpeg/ffmpeg.exe"), "-v", "error", "-ss", str(a), "-t", str(n), "-i", str(H.parent / "cut_v3.mp4"),
                    "-vf", "scale=480:270,format=gray", "-f", "rawvideo", "-"], capture_output=True)
f = np.frombuffer(p.stdout, np.uint8).reshape(-1, 270, 480)[:, int(y0):int(y1), int(x0):int(x1)]
ink = (f < th).sum(axis=(1, 2))
print(" ".join(f"{a + i / 30:.1f}:{ink[i]}" for i in range(0, len(ink), 3)))
