"""HKBU SCIE1007 课程作业的科普视频：粗剪 cut_v3.mp4 前 140 s 的帧差曲线（1080p30 → 240×135 灰度）。出 motion_S1.npy（每帧对上一帧的平均绝对差）。"""
import subprocess, numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W, H = 240, 135
p = subprocess.run([str(ROOT / "_env/ffmpeg/ffmpeg.exe"), "-v", "error", "-threads", "2", "-t", "140", "-i", str(HERE.parent / "cut_v3.mp4"),
                    "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True)
f = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W).astype(np.int16)
d = np.r_[0, np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))]
np.save(HERE / "motion_S1.npy", d)
print(len(f))
